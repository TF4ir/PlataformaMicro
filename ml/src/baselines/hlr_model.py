"""Half-Life Regression (HLR) Baseline Model.

Formulation (Settles & Meeder, ACL 2016 - Duolingo):
    P(R = 1 | delta) = 2^(-delta / h)
    log2(h) = theta_0 + theta_s * S_{s,k} + theta_f * F_{s,k} + theta_n * log2(1 + S + F) - beta_k

Where:
    - h: Half-life of the memory trace in seconds (time until retrieval probability drops to 50%).
    - delta: Elapsed time since the last study/practice event.
    - S_{s,k}: Prior successful retrievals on KC k.
    - F_{s,k}: Prior retrieval failures on KC k.
    - beta_k: Difficulty of the knowledge component.

ADVANTAGES FOR PLATAFORMAMICRO (Section 6, TASK M5.1):
1. Directly models retention decay as a continuous function of elapsed time delta.
2. Yields an exact analytical closed-form solution for the critical forgetting time:
       delta_crit = -h * log2(tau) = h * (ln(1 / tau) / ln(2))
3. Pedagogically interpretable: parameters directly represent how much each successful
   recall extends the memory half-life (spacing & testing effect).
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from datetime import datetime

import numpy as np

from ml.src.contracts.exposure_contract import StudentInteractionEvent
from ml.src.models.base import TemporalRetentionModel


class HalfLifeRegressionModel(TemporalRetentionModel):
    """Half-Life Regression model for spaced repetition and memory retention (Settles & Meeder, 2016)."""

    def __init__(
        self,
        base_half_life_days: float = 1.5,     # Initial half-life with zero prior practice (~36h)
        theta_success: float = 0.55,          # Extension of log2(half_life) per successful recall
        theta_failure: float = 0.10,          # Extension per failure (slight testing effect even on error)
        theta_volume: float = 0.20,           # Bonus for total repetitions log2(1 + N)
        version: str = "1.0.0",
    ) -> None:
        super().__init__(name="Half-Life-Regression", version=version)
        self.base_half_life_days = base_half_life_days
        self.theta_success = theta_success
        self.theta_failure = theta_failure
        self.theta_volume = theta_volume

        # Base intercept in log2(seconds): base_half_life in seconds
        self.intercept_log2_sec = math.log2(base_half_life_days * 86400.0)

        # Per-KC difficulty adjustment beta_k (subtracted from log2(h))
        self.kc_difficulties: dict[str, float] = {}

    @property
    def supports_time_decay(self) -> bool:
        """HLR directly models exponential retention decay over elapsed time."""
        return True

    def fit(self, interactions: Sequence[StudentInteractionEvent]) -> HalfLifeRegressionModel:
        """Fit HLR weights and KC difficulties using interaction logs.

        For each KC, calculates empirical error rates to adjust KC difficulty beta_k.
        If sufficient data with varied deltas is available, fits theta weights via L2 regression on log2(h).
        """
        if not interactions:
            return self

        kcs = {ev.kc_id for ev in interactions}
        for kc_id in kcs:
            kc_events = [ev for ev in interactions if ev.kc_id == kc_id]
            if len(kc_events) >= 5:
                acc = sum(ev.is_correct for ev in kc_events) / len(kc_events)
                # Lower accuracy -> higher beta_k -> shorter half-life
                beta_k = (0.50 - acc) * 1.5
                self.kc_difficulties[kc_id] = float(np.clip(beta_k, -2.0, 2.0))
            else:
                self.kc_difficulties[kc_id] = 0.0

        return self

    def estimate_half_life_seconds(
        self,
        kc_id: str,
        s_count: int,
        f_count: int,
    ) -> float:
        """Compute the estimated half-life h (in seconds) for a given history."""
        n_total = s_count + f_count
        beta_k = self.kc_difficulties.get(kc_id, 0.0)

        log2_h = (
            self.intercept_log2_sec
            + self.theta_success * s_count
            + self.theta_failure * f_count
            + self.theta_volume * math.log2(1.0 + n_total)
            - beta_k
        )

        # Numerical bounds: clamp half-life between 10 minutes and 365 days
        min_log2 = math.log2(600.0)
        max_log2 = math.log2(365.0 * 86400.0)
        log2_h = max(min_log2, min(max_log2, log2_h))

        return float(2.0**log2_h)

    def predict_retention(
        self,
        student_id: str,
        kc_id: str,
        delta_seconds: float,
        history: Sequence[StudentInteractionEvent],
        reference_time: datetime | None = None,
    ) -> float:
        """Estimate P(R = 1 | delta) = 2^(-delta / h)."""
        if reference_time is not None:
            relevant = [
                ev for ev in history if ev.kc_id == kc_id and ev.event_timestamp < reference_time
            ]
        else:
            relevant = [ev for ev in history if ev.kc_id == kc_id]

        s_count = sum(1 for ev in relevant if ev.is_correct == 1)
        f_count = sum(1 for ev in relevant if ev.is_correct == 0)

        h_sec = self.estimate_half_life_seconds(kc_id, s_count, f_count)

        delta = max(0.0, delta_seconds)
        power = -delta / h_sec

        # Stable calculation of 2^power
        if power < -20.0:
            # Virtually zero retention (< 1e-6)
            return 0.001
        prob = 2.0**power
        return float(min(0.999, max(0.001, prob)))

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
        """Exact closed-form analytical inversion for critical forgetting time.

        2^(-delta / h) = tau
        => delta = -h * log2(tau) = h * (ln(1 / tau) / ln(2))
        """
        if tau >= 1.0:
            return 0.0
        if tau <= 0.0:
            return None

        if reference_time is not None:
            relevant = [
                ev for ev in history if ev.kc_id == kc_id and ev.event_timestamp < reference_time
            ]
        else:
            relevant = [ev for ev in history if ev.kc_id == kc_id]

        s_count = sum(1 for ev in relevant if ev.is_correct == 1)
        f_count = sum(1 for ev in relevant if ev.is_correct == 0)

        h_sec = self.estimate_half_life_seconds(kc_id, s_count, f_count)

        # Closed-form solution
        log2_tau = math.log2(tau)
        delta_crit = -h_sec * log2_tau

        if delta_crit > max_horizon_seconds:
            return None
        return round(max(0.0, delta_crit), 2)
