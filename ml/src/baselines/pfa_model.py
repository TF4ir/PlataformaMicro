"""Performance Factor Analysis (PFA) Baseline Model.

Formulation (Pavlik et al., 2009):
    logit(P(R=1)) = beta_k + gamma_k * S_{s,k} + rho_k * F_{s,k}

CRITICAL ARCHITECTURAL NOTE (Section 6, TASK M5.1):
Classic PFA does NOT model temporal retention decay (supports_time_decay = False).
The predicted probability of correct retrieval depends only on the cumulative count
of prior successes (S) and failures (F). It remains invariant across future elapsed
time intervals delta. PFA is included strictly as a comparative baseline to quantify
the empirical advantage of models that incorporate temporal forgetting dynamics (DAS3H, HLR, BKT-Decay).
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from datetime import datetime

import numpy as np

from ml.src.contracts.exposure_contract import StudentInteractionEvent
from ml.src.models.base import TemporalRetentionModel


def _sigmoid(x: float) -> float:
    # Stable numerical sigmoid
    if x >= 0:
        z = math.exp(-x)
        return 1.0 / (1.0 + z)
    z = math.exp(x)
    return z / (1.0 + z)


class StandardPFAModel(TemporalRetentionModel):
    """Performance Factor Analysis baseline (Pavlik et al., 2009).

    Models retrieval probability as a function of cumulative successes and failures.
    Does NOT model decay over elapsed time.
    """

    def __init__(
        self,
        default_beta: float = 0.0,
        default_gamma: float = 0.30,
        default_rho: float = 0.10,
        version: str = "1.0.0",
    ) -> None:
        super().__init__(name="PFA-Standard", version=version)
        self.default_beta = default_beta
        self.default_gamma = default_gamma
        self.default_rho = default_rho

        # Parameters per KC: {kc_id: (beta_k, gamma_k, rho_k)}
        self.kc_params: dict[str, tuple[float, float, float]] = {}

    @property
    def supports_time_decay(self) -> bool:
        """Standard PFA does NOT model temporal decay."""
        return False

    def fit(self, interactions: Sequence[StudentInteractionEvent]) -> StandardPFAModel:
        """Fit PFA parameters per Knowledge Component using historical interaction logs.

        Extracts causal cumulative features (S, F) for each event, then estimates
        (beta_k, gamma_k, rho_k) for each KC using logistic regression.
        """
        if not interactions:
            return self

        # Sort chronologically to preserve causality
        sorted_events = sorted(interactions, key=lambda e: e.event_timestamp)

        # Track causal cumulative S and F per (student, kc)
        running_s: dict[tuple[str, str], int] = {}
        running_f: dict[tuple[str, str], int] = {}

        kc_data: dict[str, list[tuple[int, int, int]]] = {}

        for ev in sorted_events:
            pair = (ev.student_id_pseudo, ev.kc_id)
            s_prior = running_s.get(pair, 0)
            f_prior = running_f.get(pair, 0)

            if ev.kc_id not in kc_data:
                kc_data[ev.kc_id] = []
            kc_data[ev.kc_id].append((s_prior, f_prior, ev.is_correct))

            # Update running counts for future events
            if ev.is_correct == 1:
                running_s[pair] = s_prior + 1
            else:
                running_f[pair] = f_prior + 1

        # Fit per-KC parameters
        for kc_id, records in kc_data.items():
            if len(records) < 5:
                # Insufficient observations for stable logistic fit; use defaults
                self.kc_params[kc_id] = (self.default_beta, self.default_gamma, self.default_rho)
                continue

            try:
                from sklearn.linear_model import LogisticRegression

                x_mat = np.array([[r[0], r[1]] for r in records], dtype=np.float64)
                y_vec = np.array([r[2] for r in records], dtype=np.int32)

                # Check if classes are balanced enough
                unique_classes = np.unique(y_vec)
                if len(unique_classes) < 2:
                    self.kc_params[kc_id] = (
                        self.default_beta + (1.0 if unique_classes[0] == 1 else -1.0),
                        self.default_gamma,
                        self.default_rho,
                    )
                    continue

                clf = LogisticRegression(C=1.0, solver="lbfgs", max_iter=200)
                clf.fit(x_mat, y_vec)

                beta = float(clf.intercept_[0])
                gamma = float(clf.coef_[0][0])
                rho = float(clf.coef_[0][1])

                self.kc_params[kc_id] = (beta, gamma, rho)
            except (ValueError, TypeError, RuntimeError):
                self.kc_params[kc_id] = (self.default_beta, self.default_gamma, self.default_rho)

        return self

    def predict_retention(
        self,
        student_id: str,
        kc_id: str,
        delta_seconds: float,
        history: Sequence[StudentInteractionEvent],
        reference_time: datetime | None = None,
    ) -> float:
        """Estimate P(R=1).

        NOTE: In standard PFA, delta_seconds has NO effect on the probability.
        """
        # Filter history strictly prior to reference_time
        if reference_time is not None:
            relevant = [ev for ev in history if ev.kc_id == kc_id and ev.event_timestamp < reference_time]
        else:
            relevant = [ev for ev in history if ev.kc_id == kc_id]

        s_count = sum(1 for ev in relevant if ev.is_correct == 1)
        f_count = sum(1 for ev in relevant if ev.is_correct == 0)

        beta, gamma, rho = self.kc_params.get(
            kc_id, (self.default_beta, self.default_gamma, self.default_rho)
        )

        logit = beta + gamma * s_count + rho * f_count
        return _sigmoid(logit)
