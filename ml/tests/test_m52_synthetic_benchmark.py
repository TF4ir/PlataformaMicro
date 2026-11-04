"""Unit and integration tests for Task M5.2-A: Synthetic generator and model benchmark.

Certifies:
1. Canonical DAS3H vs Extended DAS3H differentiation.
2. All 7 synthetic scenarios produce deterministic, valid datasets.
3. Benchmark runner executes all 6 models and computes Brier, AUC, ECE, LogLoss, and MAE.
"""

from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta

import pytest

from ml.src.contracts.exposure_contract import StudentInteractionEvent
from ml.src.das3h.model import CanonicalDAS3HModel, ExtendedDAS3HModel
from ml.src.training.benchmark_runner import RetentionBenchmarkRunner
from ml.src.training.synthetic_generator import (
    SyntheticMemoryGenerator,
    SyntheticScenario,
)


class TestDAS3HVariantsDifferentiation:
    """Certifies Section 2 of M5.2-A: Canonical vs Extended DAS3H."""

    def test_canonical_vs_extended_das3h_formulation(self) -> None:
        t0 = datetime(2026, 11, 1, 12, 0, 0, tzinfo=UTC)
        ev = StudentInteractionEvent(
            event_id=pytest.importorskip("uuid").uuid4(),
            student_id_pseudo="s1",
            kc_id="k1",
            question_id="q1",
            event_timestamp=t0,
            is_correct=1,
            response_time_seconds=10.0,
        )

        canonical = CanonicalDAS3HModel()
        extended = ExtendedDAS3HModel(decay_gamma=0.20)

        canonical.fit([ev])
        extended.fit([ev])

        ref_time = t0 + timedelta(hours=2)  # Event is in W2: [1h, 1d)

        # Within the same window (e.g. 2h vs 10h), canonical remains constant
        p_canon_2h = canonical.predict_retention("s1", "k1", 0.0, [ev], ref_time)
        p_canon_10h = canonical.predict_retention("s1", "k1", 8 * 3600.0, [ev], ref_time)

        # In canonical, since 2h and 10h are both inside W2, the logit is identical!
        assert math.isclose(p_canon_2h, p_canon_10h, rel_tol=1e-5), (
            "Canonical DAS3H must have step-constant retention within the same window."
        )

        # In extended DAS3H, the continuous penalty -gamma * ln(1 + delta_t) makes 10h lower than 2h!
        p_ext_2h = extended.predict_retention("s1", "k1", 0.0, [ev], ref_time)
        p_ext_10h = extended.predict_retention("s1", "k1", 8 * 3600.0, [ev], ref_time)

        assert p_ext_2h > p_ext_10h, (
            "Extended DAS3H must produce smooth continuous intra-window decay."
        )


class TestSyntheticScenariosGeneration:
    """Certifies Section 3 of M5.2-A: Independent synthetic generator across 7 scenarios."""

    @pytest.mark.parametrize("scenario", list(SyntheticScenario))
    def test_scenario_generation_integrity(self, scenario: SyntheticScenario) -> None:
        gen = SyntheticMemoryGenerator(random_seed=42)
        dataset = gen.generate(
            scenario=scenario,
            n_students=4,
            n_kcs=2,
            events_per_pair=3,
            tau=0.65,
        )

        assert dataset.scenario == scenario
        assert dataset.random_seed == 42
        assert dataset.data_origin == "synthetic"
        assert dataset.total_events == 4 * 2 * 3
        assert dataset.total_queries > 0

        # Verify query fields
        q0 = dataset.test_queries[0]
        assert 0.0 <= q0.p_true <= 1.0
        assert q0.y_obs in (0, 1)
        assert q0.tau == 0.65

    def test_deterministic_reproducibility(self) -> None:
        gen1 = SyntheticMemoryGenerator(random_seed=123)
        gen2 = SyntheticMemoryGenerator(random_seed=123)

        ds1 = gen1.generate(SyntheticScenario.EXPONENTIAL_DECAY, n_students=3, n_kcs=2)
        ds2 = gen2.generate(SyntheticScenario.EXPONENTIAL_DECAY, n_students=3, n_kcs=2)

        assert len(ds1.train_events) == len(ds2.train_events)
        assert ds1.train_events[0].is_correct == ds2.train_events[0].is_correct
        assert ds1.test_queries[0].p_true == ds2.test_queries[0].p_true


class TestBenchmarkExecution:
    """Certifies Section 4 and 5 of M5.2-A: Benchmark comparison across all models."""

    def test_benchmark_runs_across_scenarios(self) -> None:
        runner = RetentionBenchmarkRunner(random_seeds=[42])
        # Test on a representative subset of scenarios for fast CI verification
        test_scenarios = [
            SyntheticScenario.EXPONENTIAL_DECAY,
            SyntheticScenario.POWER_LAW_DECAY,
            SyntheticScenario.NOISY_SLIP_GUESS,
        ]

        report = runner.run_benchmark(
            scenarios=test_scenarios,
            n_students=6,
            n_kcs=2,
            events_per_pair=3,
            tau=0.65,
        )

        assert len(report.results) == len(test_scenarios) * 6  # 6 models per scenario
        model_names = {r.model_name for r in report.results}
        assert "DAS3H-Canonical" in model_names
        assert "DAS3H-Extended" in model_names
        assert "Half-Life-Regression" in model_names
        assert "BKT-Decay" in model_names
        assert "PFA-Standard" in model_names
        assert "BKT-Standard" in model_names

        for r in report.results:
            assert 0.0 <= r.brier_score <= 1.0
            assert r.log_loss >= 0.0
            assert 0.0 <= r.auc_roc <= 1.0
            assert 0.0 <= r.ece <= 1.0
