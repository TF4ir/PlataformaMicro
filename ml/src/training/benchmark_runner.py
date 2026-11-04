"""Benchmark execution runner for retention prediction models.

Addresses Section 4 and 5 of TASK M5.2-A:
Evaluates 6 models across synthetic scenarios:
- Canonical DAS3H (Choffin et al., 2019)
- Extended DAS3H (PlataformaMicro)
- Half-Life Regression (Settles & Meeder, 2016)
- BKT-Decay (Qiu / Yudelson)
- Standard PFA (Pavlik et al., 2009)
- Standard BKT (Corbett & Anderson, 1995)

Computes out-of-sample Brier Score, Log Loss, AUC-ROC, ECE, and MAE of critical forgetting time.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from ml.src.baselines.bkt_model import BKTDecayModel, StandardBKTModel
from ml.src.baselines.hlr_model import HalfLifeRegressionModel
from ml.src.baselines.pfa_model import StandardPFAModel
from ml.src.das3h.model import CanonicalDAS3HModel, ExtendedDAS3HModel
from ml.src.evaluation.retention_metrics import (
    auc_roc,
    brier_score,
    expected_calibration_error,
    log_loss,
)
from ml.src.models.base import TemporalRetentionModel
from ml.src.training.synthetic_generator import (
    SyntheticDataset,
    SyntheticMemoryGenerator,
    SyntheticScenario,
)


@dataclass
class ModelScenarioResult:
    """Evaluation summary of one model on one scenario."""

    model_name: str
    scenario: str
    supports_time_decay: bool
    brier_score: float
    log_loss: float
    auc_roc: float
    ece: float
    mae_critical_time_days: float | None
    n_queries: int
    n_positive_obs: int
    notes: str = ""


@dataclass
class BenchmarkReport:
    """Complete experimental benchmark summary across scenarios and models."""

    results: list[ModelScenarioResult] = field(default_factory=list)
    generator_version: str = "1.0.0"
    random_seeds: list[int] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class RetentionBenchmarkRunner:
    """Executes controlled multi-scenario retention model comparisons."""

    def __init__(self, random_seeds: Sequence[int] = (42, 101)) -> None:
        self.random_seeds = list(random_seeds)

    def _instantiate_models(self) -> list[TemporalRetentionModel]:
        """Instantiate the 6 candidate and baseline models with fresh parameters."""
        return [
            CanonicalDAS3HModel(),
            ExtendedDAS3HModel(),
            HalfLifeRegressionModel(),
            BKTDecayModel(),
            StandardPFAModel(),
            StandardBKTModel(),
        ]

    def run_benchmark(
        self,
        scenarios: Sequence[SyntheticScenario] | None = None,
        n_students: int = 15,
        n_kcs: int = 4,
        events_per_pair: int = 4,
        tau: float = 0.65,
    ) -> BenchmarkReport:
        """Run the comprehensive benchmark across all specified scenarios and seeds."""
        if scenarios is None:
            scenarios = list(SyntheticScenario)

        all_results: list[ModelScenarioResult] = []

        for scenario in scenarios:
            scenario_seed_results: dict[str, list[ModelScenarioResult]] = {}

            for seed in self.random_seeds:
                gen = SyntheticMemoryGenerator(random_seed=seed)
                dataset: SyntheticDataset = gen.generate(
                    scenario=scenario,
                    n_students=n_students,
                    n_kcs=n_kcs,
                    events_per_pair=events_per_pair,
                    tau=tau,
                )

                models = self._instantiate_models()
                for model in models:
                    # Fit on train events
                    model.fit(dataset.train_events)

                    # Predict out-of-sample test queries
                    y_true_list: list[int] = []
                    p_pred_list: list[float] = []
                    pred_crit_times: list[float] = []
                    true_crit_times: list[float] = []

                    # Group history by student to avoid re-filtering
                    student_histories: dict[str, list[Any]] = {}
                    for ev in dataset.train_events:
                        student_histories.setdefault(ev.student_id_pseudo, []).append(ev)

                    for q in dataset.test_queries:
                        s_hist = student_histories.get(q.student_id_pseudo, [])
                        p_hat = model.predict_retention(
                            student_id=q.student_id_pseudo,
                            kc_id=q.kc_id,
                            delta_seconds=q.delta_seconds,
                            history=s_hist,
                            reference_time=q.reference_time,
                        )
                        # Clip prediction to [0.001, 0.999] for numerical stability
                        p_hat = float(np.clip(p_hat, 0.001, 0.999))
                        y_true_list.append(q.y_obs)
                        p_pred_list.append(p_hat)

                        # Evaluate critical time estimation once per unique reference state
                        if q.delta_seconds == dataset.test_queries[0].delta_seconds and q.true_forgetting_time_seconds is not None:
                            t_hat = model.predict_forgetting_time(
                                student_id=q.student_id_pseudo,
                                kc_id=q.kc_id,
                                tau=q.tau,
                                history=s_hist,
                                reference_time=q.reference_time,
                            )
                            if t_hat is not None:
                                pred_crit_times.append(t_hat)
                                true_crit_times.append(q.true_forgetting_time_seconds)

                    # Calculate metrics
                    bs = brier_score(y_true_list, p_pred_list)
                    ll = log_loss(y_true_list, p_pred_list)

                    n_pos = sum(y_true_list)
                    if n_pos > 0 and n_pos < len(y_true_list):
                        auc = auc_roc(y_true_list, p_pred_list)
                    else:
                        auc = 0.50

                    ece = expected_calibration_error(y_true_list, p_pred_list, n_bins=10)

                    mae_crit: float | None = None
                    if pred_crit_times and len(pred_crit_times) >= 5:
                        p_days = np.array(pred_crit_times) / 86400.0
                        t_days = np.array(true_crit_times) / 86400.0
                        mae_crit = float(np.mean(np.abs(p_days - t_days)))

                    res = ModelScenarioResult(
                        model_name=model.name,
                        scenario=scenario.value,
                        supports_time_decay=model.supports_time_decay,
                        brier_score=round(bs, 4),
                        log_loss=round(ll, 4),
                        auc_roc=round(auc, 4),
                        ece=round(ece, 4),
                        mae_critical_time_days=round(mae_crit, 2) if mae_crit is not None else None,
                        n_queries=len(y_true_list),
                        n_positive_obs=n_pos,
                    )
                    scenario_seed_results.setdefault(model.name, []).append(res)

            # Average results across seeds for this scenario
            for m_name, seed_res_list in scenario_seed_results.items():
                avg_bs = float(np.mean([r.brier_score for r in seed_res_list]))
                avg_ll = float(np.mean([r.log_loss for r in seed_res_list]))
                avg_auc = float(np.mean([r.auc_roc for r in seed_res_list]))
                avg_ece = float(np.mean([r.ece for r in seed_res_list]))

                valid_maes = [r.mae_critical_time_days for r in seed_res_list if r.mae_critical_time_days is not None]
                avg_mae: float | None = float(np.mean(valid_maes)) if valid_maes else None

                all_results.append(
                    ModelScenarioResult(
                        model_name=m_name,
                        scenario=scenario.value,
                        supports_time_decay=seed_res_list[0].supports_time_decay,
                        brier_score=round(avg_bs, 4),
                        log_loss=round(avg_ll, 4),
                        auc_roc=round(avg_auc, 4),
                        ece=round(avg_ece, 4),
                        mae_critical_time_days=round(avg_mae, 2) if avg_mae is not None else None,
                        n_queries=seed_res_list[0].n_queries,
                        n_positive_obs=seed_res_list[0].n_positive_obs,
                        notes=f"Aggregated over {len(self.random_seeds)} seeds.",
                    )
                )

        return BenchmarkReport(
            results=all_results,
            generator_version="1.0.0",
            random_seeds=self.random_seeds,
            metadata={"tau": tau, "scenarios": [s.value for s in scenarios]},
        )
