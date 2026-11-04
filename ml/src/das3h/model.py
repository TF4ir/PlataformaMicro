"""DAS3H Retention Models — Canonical and Extended Variants.

Distinguishes between:
1. CanonicalDAS3HModel:
   Exact adaptation of Choffin et al. (2019) with embedding dimension d=0 and L2 regularization.
   Models practice and forgetting strictly via expansively shifting temporal windows (W1..W5).
   logit(P(R = 1 | delta)) = theta_s - beta_k + sum_{w=1}^5 (alpha_{k,w} * S_{s,k,w}(delta) + beta_{k,w} * F_{s,k,w}(delta))
   Does NOT include additional continuous intra-window penalties.

2. ExtendedDAS3HModel (PlataformaMicro Variant):
   Includes the canonical window terms PLUS an empirical continuous decay penalty on elapsed time
   since the last practice interaction: -gamma * ln(1 + delta_t_last / 86400).
   This provides smooth intra-window monotonic decline rather than step-function drops at window boundaries.

Addresses Section 2 of TASK M5.2-A.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from datetime import datetime

import numpy as np

from ml.src.contracts.exposure_contract import StudentInteractionEvent
from ml.src.features.temporal_retention_extractor import extract_das3h_window_features
from ml.src.models.base import TemporalRetentionModel


def _sigmoid(x: float) -> float:
    # Stable numerical sigmoid
    if x >= 0:
        z = math.exp(-x)
        return 1.0 / (1.0 + z)
    z = math.exp(x)
    return z / (1.0 + z)


class CanonicalDAS3HModel(TemporalRetentionModel):
    """Canonical DAS3H model based strictly on Choffin et al. (2019) (d=0).

    Formulation:
        logit(P(R = 1 | delta)) = theta_s - beta_k
                                 + sum_{w=1}^5 (alpha_{w} * S_{w}(delta) + beta_{w} * F_{w}(delta))

    Temporal decay occurs solely through the transition of historical events across the 5
    logarithmically spaced windows:
        W1: [0, 1h), W2: [1h, 1d), W3: [1d, 7d), W4: [7d, 30d), W5: [30d, inf)
    """

    def __init__(
        self,
        default_alpha_weights: Sequence[float] | None = None,
        default_beta_weights: Sequence[float] | None = None,
        default_theta: float = 0.0,
        default_beta_kc: float = 0.0,
        l2_penalty: float = 1.0,
        version: str = "1.0.0",
    ) -> None:
        super().__init__(name="DAS3H-Canonical", version=version)

        # Canonical weights: strictly positive benefits that decrease across receding time windows
        if default_alpha_weights is None:
            self.alpha_weights = [0.55, 0.38, 0.24, 0.14, 0.06]
        else:
            self.alpha_weights = list(default_alpha_weights)

        if default_beta_weights is None:
            self.beta_weights = [0.15, 0.10, 0.06, 0.03, 0.01]
        else:
            self.beta_weights = list(default_beta_weights)

        self.default_theta = default_theta
        self.default_beta_kc = default_beta_kc
        self.l2_penalty = l2_penalty

        self.student_abilities: dict[str, float] = {}
        self.kc_difficulties: dict[str, float] = {}

    @property
    def supports_time_decay(self) -> bool:
        """Canonical DAS3H supports decay via window shifts."""
        return True

    def fit(self, interactions: Sequence[StudentInteractionEvent]) -> CanonicalDAS3HModel:
        """Fit theta_s and beta_k with empirical Bayes L2 shrinkage."""
        if not interactions:
            return self

        sorted_events = sorted(interactions, key=lambda e: e.event_timestamp)
        student_records: dict[str, list[int]] = {}
        kc_records: dict[str, list[int]] = {}

        for ev in sorted_events:
            student_records.setdefault(ev.student_id_pseudo, []).append(ev.is_correct)
            kc_records.setdefault(ev.kc_id, []).append(ev.is_correct)

        for s_id, outcomes in student_records.items():
            acc = sum(outcomes) / len(outcomes)
            shrinkage = len(outcomes) / (len(outcomes) + self.l2_penalty * 2.0)
            logit_approx = math.log((acc + 0.05) / (1.05 - acc))
            self.student_abilities[s_id] = float(np.clip(logit_approx * shrinkage, -2.5, 2.5))

        for k_id, outcomes in kc_records.items():
            acc = sum(outcomes) / len(outcomes)
            shrinkage = len(outcomes) / (len(outcomes) + self.l2_penalty * 2.0)
            diff_approx = math.log((1.05 - acc) / (acc + 0.05))
            self.kc_difficulties[k_id] = float(np.clip(diff_approx * shrinkage, -2.5, 2.5))

        return self

    def predict_retention(
        self,
        student_id: str,
        kc_id: str,
        delta_seconds: float,
        history: Sequence[StudentInteractionEvent],
        reference_time: datetime | None = None,
    ) -> float:
        """Estimate P_recall(s, k, t + delta | history) using pure window shifts."""
        if reference_time is None:
            if history:
                reference_time = max(ev.event_timestamp for ev in history)
            else:
                reference_time = datetime.now()

        kc_history = [ev for ev in history if ev.kc_id == kc_id]
        counts = extract_das3h_window_features(kc_history, reference_time, delta_seconds)

        theta = self.student_abilities.get(student_id, self.default_theta)
        beta = self.kc_difficulties.get(kc_id, self.default_beta_kc)

        logit = theta - beta

        # Add window effects (decay occurs as delta increases and events shift into W2..W5)
        for w_idx in range(5):
            logit += self.alpha_weights[w_idx] * counts.successes[w_idx]
            logit += self.beta_weights[w_idx] * counts.failures[w_idx]

        logit = float(np.clip(logit, -8.0, 8.0))
        return _sigmoid(logit)


class ExtendedDAS3HModel(CanonicalDAS3HModel):
    """Extended DAS3H model with PlataformaMicro continuous intra-window decay penalty.

    Formulation:
        logit(P(R = 1 | delta)) = theta_s - beta_k
                                 + sum_{w=1}^5 (alpha_{w} * S_{w}(delta) + beta_{w} * F_{w}(delta))
                                 - gamma * ln(1 + delta_t_last / 86400)

    Justification:
    Windows W1..W5 produce discrete step-changes at 1h, 1d, 7d, 30d. The continuous term
    provides smooth monotonic decay within each multi-day window (e.g. between day 1 and day 6).
    """

    def __init__(
        self,
        default_alpha_weights: Sequence[float] | None = None,
        default_beta_weights: Sequence[float] | None = None,
        decay_gamma: float = 0.15,
        default_theta: float = 0.0,
        default_beta_kc: float = 0.0,
        l2_penalty: float = 1.0,
        version: str = "1.1.0-extended",
    ) -> None:
        super().__init__(
            default_alpha_weights=default_alpha_weights,
            default_beta_weights=default_beta_weights,
            default_theta=default_theta,
            default_beta_kc=default_beta_kc,
            l2_penalty=l2_penalty,
            version=version,
        )
        self.name = "DAS3H-Extended"
        self.decay_gamma = decay_gamma

    def predict_retention(
        self,
        student_id: str,
        kc_id: str,
        delta_seconds: float,
        history: Sequence[StudentInteractionEvent],
        reference_time: datetime | None = None,
    ) -> float:
        """Estimate P_recall with discrete window shifts PLUS continuous elapsed-time penalty."""
        if reference_time is None:
            if history:
                reference_time = max(ev.event_timestamp for ev in history)
            else:
                reference_time = datetime.now()

        kc_history = [ev for ev in history if ev.kc_id == kc_id]
        counts = extract_das3h_window_features(kc_history, reference_time, delta_seconds)

        theta = self.student_abilities.get(student_id, self.default_theta)
        beta = self.kc_difficulties.get(kc_id, self.default_beta_kc)

        logit = theta - beta

        for w_idx in range(5):
            logit += self.alpha_weights[w_idx] * counts.successes[w_idx]
            logit += self.beta_weights[w_idx] * counts.failures[w_idx]

        # Continuous intra-window decay penalty
        if counts.last_elapsed_seconds is not None:
            elapsed_days = counts.last_elapsed_seconds / 86400.0
            logit -= self.decay_gamma * math.log(1.0 + elapsed_days)

        logit = float(np.clip(logit, -8.0, 8.0))
        return _sigmoid(logit)


# Backward compatibility alias
DAS3HRetentionModel = ExtendedDAS3HModel
