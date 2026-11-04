"""Comprehensive test suite for temporal retention modeling and baselines.

Certifies all requirements of TASK M5.1 (CORRECCIÓN DE ENFOQUE):
1. Retention probability decay over elapsed future horizon delta.
2. Forgetting risk definition (1 - P_recall).
3. Estimation of critical forgetting time (predicted_forgetting_time <= tau).
4. Strict anti-leakage causality (events at t >= t_ref are ignored).
5. Baseline differentiation (PFA & BKT-Standard static vs BKT-Decay, HLR, DAS3H decaying).
6. Content exposure contract validation.
7. Calibration and metric computation accuracy (AUC, Brier, ECE, Log Loss).
"""

from __future__ import annotations

import math
import uuid
from datetime import UTC, datetime, timedelta

import pytest

from ml.src.baselines.bkt_model import BKTDecayModel, StandardBKTModel
from ml.src.baselines.hlr_model import HalfLifeRegressionModel
from ml.src.baselines.pfa_model import StandardPFAModel
from ml.src.contracts.exposure_contract import (
    ContentExposureEvent,
    ExposureCompletionStatus,
    ExposureType,
    StudentInteractionEvent,
)
from ml.src.das3h.model import DAS3HRetentionModel
from ml.src.evaluation.retention_metrics import (
    auc_roc,
    brier_score,
    expected_calibration_error,
    log_loss,
    review_interval_mae_days,
)


@pytest.fixture
def base_timestamp() -> datetime:
    return datetime(2026, 11, 1, 12, 0, 0, tzinfo=UTC)


@pytest.fixture
def synthetic_student_history(base_timestamp: datetime) -> list[StudentInteractionEvent]:
    """Generates a realistic chronological interaction history for student 'std-01' on KC 'kc-cell'."""
    s_id = "std-01"
    kc_id = "kc-cell"
    q_id = "q-01"

    # 4 interactions spaced over 3 days
    return [
        StudentInteractionEvent(
            event_id=uuid.uuid4(),
            student_id_pseudo=s_id,
            kc_id=kc_id,
            question_id=q_id,
            event_timestamp=base_timestamp,
            is_correct=1,
            response_time_seconds=12.5,
        ),
        StudentInteractionEvent(
            event_id=uuid.uuid4(),
            student_id_pseudo=s_id,
            kc_id=kc_id,
            question_id=q_id,
            event_timestamp=base_timestamp + timedelta(hours=4),
            is_correct=1,
            response_time_seconds=10.2,
        ),
        StudentInteractionEvent(
            event_id=uuid.uuid4(),
            student_id_pseudo=s_id,
            kc_id=kc_id,
            question_id=q_id,
            event_timestamp=base_timestamp + timedelta(days=1),
            is_correct=0,  # Retrieval failure
            response_time_seconds=25.0,
        ),
        StudentInteractionEvent(
            event_id=uuid.uuid4(),
            student_id_pseudo=s_id,
            kc_id=kc_id,
            question_id=q_id,
            event_timestamp=base_timestamp + timedelta(days=2),
            is_correct=1,  # Successful review
            response_time_seconds=14.0,
        ),
    ]


class TestTemporalDecayBehavior:
    """Verifies that models supporting decay show strictly declining retention curves over time."""

    def test_das3h_shows_retention_decay(
        self,
        synthetic_student_history: list[StudentInteractionEvent],
        base_timestamp: datetime,
    ) -> None:
        model = DAS3HRetentionModel()
        model.fit(synthetic_student_history)

        ref_time = base_timestamp + timedelta(days=2, hours=1)
        history = synthetic_student_history

        # Predict across increasing horizons: 0h, 1d, 7d, 30d
        p_now = model.predict_retention("std-01", "kc-cell", 0.0, history, ref_time)
        p_1d = model.predict_retention("std-01", "kc-cell", 86400.0, history, ref_time)
        p_7d = model.predict_retention("std-01", "kc-cell", 7 * 86400.0, history, ref_time)
        p_30d = model.predict_retention("std-01", "kc-cell", 30 * 86400.0, history, ref_time)

        # Retention must strictly decrease over time
        assert p_now > p_1d, f"Expected p_now ({p_now}) > p_1d ({p_1d})"
        assert p_1d > p_7d, f"Expected p_1d ({p_1d}) > p_7d ({p_7d})"
        assert p_7d > p_30d, f"Expected p_7d ({p_7d}) > p_30d ({p_30d})"
        assert model.supports_time_decay is True

    def test_hlr_shows_exponential_decay_and_analytical_inversion(
        self,
        synthetic_student_history: list[StudentInteractionEvent],
        base_timestamp: datetime,
    ) -> None:
        model = HalfLifeRegressionModel()
        model.fit(synthetic_student_history)

        ref_time = base_timestamp + timedelta(days=2, hours=1)
        history = synthetic_student_history

        p_0 = model.predict_retention("std-01", "kc-cell", 0.0, history, ref_time)
        p_3d = model.predict_retention("std-01", "kc-cell", 3 * 86400.0, history, ref_time)
        p_14d = model.predict_retention("std-01", "kc-cell", 14 * 86400.0, history, ref_time)

        assert p_0 > p_3d > p_14d
        assert model.supports_time_decay is True

        # Test analytical closed-form inversion for critical forgetting time (tau = 0.65)
        tau = 0.65
        t_crit = model.predict_forgetting_time("std-01", "kc-cell", tau, history, ref_time)
        assert t_crit is not None
        assert t_crit > 0.0

        # At delta = t_crit, predicted probability should equal tau within numerical tolerance
        p_at_crit = model.predict_retention("std-01", "kc-cell", t_crit, history, ref_time)
        assert math.isclose(p_at_crit, tau, rel_tol=1e-2), (
            f"Expected P(t_crit)={p_at_crit} to be close to tau={tau}"
        )

    def test_bkt_decay_shows_decay_vs_standard_bkt_static(
        self,
        synthetic_student_history: list[StudentInteractionEvent],
        base_timestamp: datetime,
    ) -> None:
        bkt_standard = StandardBKTModel()
        bkt_decay = BKTDecayModel()

        ref_time = base_timestamp + timedelta(days=2, hours=1)
        history = synthetic_student_history

        # Standard BKT: delta has NO effect
        std_p0 = bkt_standard.predict_retention("std-01", "kc-cell", 0.0, history, ref_time)
        std_p7d = bkt_standard.predict_retention("std-01", "kc-cell", 7 * 86400.0, history, ref_time)
        assert std_p0 == std_p7d
        assert bkt_standard.supports_time_decay is False

        # BKT-Decay: delta reduces probability
        decay_p0 = bkt_decay.predict_retention("std-01", "kc-cell", 0.0, history, ref_time)
        decay_p7d = bkt_decay.predict_retention("std-01", "kc-cell", 7 * 86400.0, history, ref_time)
        assert decay_p0 > decay_p7d
        assert bkt_decay.supports_time_decay is True

    def test_pfa_is_static_over_delta(
        self,
        synthetic_student_history: list[StudentInteractionEvent],
        base_timestamp: datetime,
    ) -> None:
        pfa = StandardPFAModel()
        ref_time = base_timestamp + timedelta(days=2, hours=1)

        p0 = pfa.predict_retention("std-01", "kc-cell", 0.0, synthetic_student_history, ref_time)
        p30d = pfa.predict_retention("std-01", "kc-cell", 30 * 86400.0, synthetic_student_history, ref_time)

        assert p0 == p30d
        assert pfa.supports_time_decay is False


class TestAntiLeakageAndCausality:
    """Verifies that future events (t >= reference_time) are strictly ignored during prediction."""

    def test_future_events_do_not_leak_into_prediction(
        self,
        base_timestamp: datetime,
    ) -> None:
        s_id = "std-leakage"
        kc_id = "kc-leakage"

        past_event = StudentInteractionEvent(
            event_id=uuid.uuid4(),
            student_id_pseudo=s_id,
            kc_id=kc_id,
            question_id="q-1",
            event_timestamp=base_timestamp,
            is_correct=1,
            response_time_seconds=10.0,
        )

        future_delayed_assessment = StudentInteractionEvent(
            event_id=uuid.uuid4(),
            student_id_pseudo=s_id,
            kc_id=kc_id,
            question_id="q-delayed",
            event_timestamp=base_timestamp + timedelta(days=7),
            is_correct=0,  # Failed in the future
            response_time_seconds=30.0,
            activity_type="delayed_assessment",
        )

        model = DAS3HRetentionModel()

        # Reference time at Day 1 (before the 7-day delayed assessment)
        ref_time = base_timestamp + timedelta(days=1)

        # History containing BOTH past and future events
        full_history = [past_event, future_delayed_assessment]

        # Prediction with full history vs prediction with only past event
        p_with_future = model.predict_retention(s_id, kc_id, 0.0, full_history, ref_time)
        p_without_future = model.predict_retention(s_id, kc_id, 0.0, [past_event], ref_time)

        # Causality test: they must be EXACTLY identical because future event is ignored!
        assert p_with_future == p_without_future


class TestForgettingRiskAndThresholds:
    """Verifies the operational definition of forgetting_risk and review window calculation."""

    def test_forgetting_risk_definition(
        self,
        synthetic_student_history: list[StudentInteractionEvent],
        base_timestamp: datetime,
    ) -> None:
        model = DAS3HRetentionModel()
        ref_time = base_timestamp + timedelta(days=3)

        out = model.predict("std-01", "kc-cell", synthetic_student_history, tau=0.65, reference_time=ref_time)

        # Operational definition: forgetting_risk = 1 - predicted_retention_probability
        assert math.isclose(out.current_forgetting_risk, 1.0 - out.current_recall_probability, abs_tol=1e-4)

        for pt in out.projections:
            assert math.isclose(pt.forgetting_risk, 1.0 - pt.recall_probability, abs_tol=1e-4)

    def test_preventive_review_window_calculation(
        self,
        synthetic_student_history: list[StudentInteractionEvent],
        base_timestamp: datetime,
    ) -> None:
        model = HalfLifeRegressionModel()
        ref_time = base_timestamp + timedelta(days=3)

        out = model.predict("std-01", "kc-cell", synthetic_student_history, tau=0.70, reference_time=ref_time)

        assert out.predicted_forgetting_time_days is not None
        assert out.recommended_review_window_start_days is not None

        # Recommended window start must precede the critical threshold (85% of critical time)
        expected_window = round(out.predicted_forgetting_time_days * 0.85, 2)
        assert out.recommended_review_window_start_days == expected_window
        assert out.recommended_review_window_start_days < out.predicted_forgetting_time_days


class TestExposureEventContract:
    """Certifies the schema and validation for microcontent study exposure events (Section 5)."""

    def test_content_exposure_event_creation(self) -> None:
        now = datetime.now(UTC)
        event = ContentExposureEvent(
            tenant_id=uuid.uuid4(),
            student_id_pseudo=uuid.uuid4(),
            microcontent_id=uuid.uuid4(),
            knowledge_component_id=uuid.uuid4(),
            exposure_type=ExposureType.INITIAL_STUDY,
            started_at=now,
            completed_at=now + timedelta(minutes=4),
            duration_seconds=240.0,
            completion_status=ExposureCompletionStatus.COMPLETED,
            metadata={"cards_viewed": 3, "reading_speed_wpm": 180},
        )

        assert event.exposure_type == ExposureType.INITIAL_STUDY
        assert event.duration_seconds == 240.0
        assert event.completion_status == ExposureCompletionStatus.COMPLETED


class TestEvaluationMetrics:
    """Verifies that all specified evaluation metrics compute correctly without errors."""

    def test_metrics_calculation(self) -> None:
        y_true = [1, 1, 0, 1, 0, 0, 1, 0]
        y_prob = [0.90, 0.80, 0.35, 0.70, 0.20, 0.40, 0.65, 0.15]

        # AUC should be high for this well-ordered toy prediction
        auc = auc_roc(y_true, y_prob)
        assert auc >= 0.85

        # Brier Score should be small (well-calibrated)
        bs = brier_score(y_true, y_prob)
        assert bs < 0.15

        # Log Loss should be positive and small
        ll = log_loss(y_true, y_prob)
        assert 0.0 < ll < 0.60

        # ECE should be bounded (finite-sample toy test)
        ece = expected_calibration_error(y_true, y_prob, n_bins=5)
        assert 0.0 <= ece < 0.30

        # MAE of review interval
        pred_times = [86400.0, 172800.0]  # 1 day, 2 days
        actual_times = [86400.0 * 1.2, 172800.0 * 0.9]
        mae = review_interval_mae_days(pred_times, actual_times)
        assert mae > 0.0
