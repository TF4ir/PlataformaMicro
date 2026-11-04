"""Abstract base class and contract for temporal retention and forgetting models.

Defines the unified interface for:
- DAS3H (Champion candidate with logarithmic time windows)
- Performance Factor Analysis (PFA - Baseline, static in delta)
- Bayesian Knowledge Tracing (BKT - Baseline, static in delta)
- BKT-Decay (Independent variant with exponential decay)
- Half-Life Regression (HLR - Settles & Meeder 2016, direct half-life modeling)
"""

from __future__ import annotations

import abc
from collections.abc import Sequence
from datetime import UTC, datetime

from ml.src.contracts.exposure_contract import (
    RetentionPredictionOutput,
    RetentionProjectionPoint,
    StudentInteractionEvent,
)


class TemporalRetentionModel(abc.ABC):
    """Abstract base class for all retention and forgetting prediction models."""

    def __init__(self, name: str, version: str = "1.0.0") -> None:
        self.name = name
        self.version = version

    @property
    @abc.abstractmethod
    def supports_time_decay(self) -> bool:
        """Indicates whether the model mathematically represents retention decay over elapsed time."""

    @abc.abstractmethod
    def fit(self, interactions: Sequence[StudentInteractionEvent]) -> TemporalRetentionModel:
        """Fit model parameters on historical interaction events."""

    @abc.abstractmethod
    def predict_retention(
        self,
        student_id: str,
        kc_id: str,
        delta_seconds: float,
        history: Sequence[StudentInteractionEvent],
        reference_time: datetime | None = None,
    ) -> float:
        """Estimate P_recall(s, k, t + delta | history).

        Args:
            student_id: Pseudonymized student ID
            kc_id: Knowledge component identifier
            delta_seconds: Elapsed time past reference_time in seconds (>= 0)
            history: Filtered historical interaction events strictly strictly prior to reference_time
            reference_time: The anchor moment t from which delta_seconds begins (defaults to max timestamp in history or now)

        Returns:
            Probability of successful retrieval in [0.0, 1.0].
        """

    def predict_forgetting_time(
        self,
        student_id: str,
        kc_id: str,
        tau: float,
        history: Sequence[StudentInteractionEvent],
        reference_time: datetime | None = None,
        max_horizon_seconds: float = 30 * 86400,
        tolerance_seconds: float = 60.0,
    ) -> float | None:
        """Find the earliest future elapsed time delta (in seconds) where P_recall <= tau.

        If the model does not support time decay (e.g. standard PFA, standard BKT),
        the probability never decays:
        - If current P_recall <= tau, returns 0.0 (already below threshold).
        - If current P_recall > tau, returns None (will never cross threshold due to lack of decay).

        For models with decay, uses a robust root-finding bisection solver unless
        a closed-form analytical solution is available (e.g. HLR).
        """
        if not self.supports_time_decay:
            p_initial = self.predict_retention(student_id, kc_id, 0.0, history, reference_time)
            if p_initial <= tau:
                return 0.0
            return None

        # Check at delta = 0
        p_0 = self.predict_retention(student_id, kc_id, 0.0, history, reference_time)
        if p_0 <= tau:
            return 0.0

        # Check at max horizon
        p_max = self.predict_retention(student_id, kc_id, max_horizon_seconds, history, reference_time)
        if p_max > tau:
            # Does not cross threshold within the search window (e.g. strongly consolidated knowledge)
            return None

        # Bisection solver over [0, max_horizon_seconds]
        low = 0.0
        high = max_horizon_seconds
        while (high - low) > tolerance_seconds:
            mid = (low + high) / 2.0
            p_mid = self.predict_retention(student_id, kc_id, mid, history, reference_time)
            if p_mid <= tau:
                high = mid
            else:
                low = mid

        return round(high, 2)

    def predict_trajectory(
        self,
        student_id: str,
        kc_id: str,
        horizons_seconds: Sequence[float],
        history: Sequence[StudentInteractionEvent],
        reference_time: datetime | None = None,
    ) -> list[RetentionProjectionPoint]:
        """Sample the retention curve across multiple elapsed future horizons."""
        points: list[RetentionProjectionPoint] = []
        for delta in sorted(horizons_seconds):
            if delta < 0:
                continue
            prob = self.predict_retention(student_id, kc_id, delta, history, reference_time)
            # Clip probability to [0.001, 0.999] for numerical stability
            prob = max(0.001, min(0.999, prob))
            points.append(
                RetentionProjectionPoint(
                    delta_seconds=round(delta, 1),
                    delta_hours=round(delta / 3600.0, 2),
                    delta_days=round(delta / 86400.0, 3),
                    recall_probability=round(prob, 4),
                    forgetting_risk=round(1.0 - prob, 4),
                )
            )
        return points

    def predict(
        self,
        student_id: str,
        kc_id: str,
        history: Sequence[StudentInteractionEvent],
        tau: float = 0.65,
        horizons_days: Sequence[float] | None = None,
        reference_time: datetime | None = None,
    ) -> RetentionPredictionOutput:
        """Produce the complete predictive report for a (student, KC) pair."""
        if reference_time is None:
            if history:
                reference_time = max(ev.event_timestamp for ev in history)
            else:
                reference_time = datetime.now(UTC)

        # Default horizons: 0h (now), 1h, 6h, 12h, 1d, 2d, 3d, 5d, 7d, 14d, 30d
        if horizons_days is None:
            horizons_days = [0.0, 1 / 24, 6 / 24, 0.5, 1.0, 2.0, 3.0, 5.0, 7.0, 14.0, 30.0]

        horizons_seconds = [d * 86400.0 for d in horizons_days]
        trajectory = self.predict_trajectory(student_id, kc_id, horizons_seconds, history, reference_time)

        p_current = self.predict_retention(student_id, kc_id, 0.0, history, reference_time)
        t_forgetting_sec = self.predict_forgetting_time(student_id, kc_id, tau, history, reference_time)
        t_forgetting_days = (t_forgetting_sec / 86400.0) if t_forgetting_sec is not None else None

        # Preventive review recommendation: 85% of critical forgetting time (safety margin)
        review_start_days: float | None = None
        if t_forgetting_days is not None:
            review_start_days = round(max(0.0, t_forgetting_days * 0.85), 2)

        kc_history = [ev for ev in history if ev.kc_id == kc_id]
        is_cold_start = len(kc_history) < 3

        audit_msg = (
            f"Evaluated with {self.name} v{self.version}. "
            f"Supports temporal decay: {self.supports_time_decay}. "
            f"Observations for KC: {len(kc_history)}."
        )
        if not self.supports_time_decay:
            audit_msg += " WARNING: Model does not model elapsed time decay (probability remains static across delta)."

        return RetentionPredictionOutput(
            student_id_pseudo=student_id,
            kc_id=kc_id,
            reference_time=reference_time,
            tau_threshold=tau,
            current_recall_probability=round(p_current, 4),
            current_forgetting_risk=round(1.0 - p_current, 4),
            predicted_forgetting_time_seconds=t_forgetting_sec,
            predicted_forgetting_time_days=round(t_forgetting_days, 2) if t_forgetting_days is not None else None,
            recommended_review_window_start_days=review_start_days,
            projections=trajectory,
            model_name=self.name,
            model_version=self.version,
            supports_time_decay=self.supports_time_decay,
            is_cold_start=is_cold_start,
            audit_notes=audit_msg,
        )
