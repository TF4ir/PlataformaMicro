"""Bayesian Knowledge Tracing (BKT) Baseline Models.

Implements two distinct models as required by Section 6 of TASK M5.1:
1. StandardBKTModel:
   Classic Corbett & Anderson (1995) 4-parameter HMM.
   Explicitly does NOT model time decay (supports_time_decay = False).

2. BKTDecayModel:
   Independent variant extending BKT with continuous exponential forgetting decay
   (Qiu et al., 2011; Yudelson et al., 2014).
   Supports time decay (supports_time_decay = True).
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from datetime import datetime

from ml.src.contracts.exposure_contract import StudentInteractionEvent
from ml.src.models.base import TemporalRetentionModel


class StandardBKTModel(TemporalRetentionModel):
    """Classic Bayesian Knowledge Tracing without temporal decay.

    Parameters per KC:
        - L0: Prior probability of knowing the KC before any practice
        - T: Probability of learning the KC between practice opportunities
        - G: Probability of guessing correctly without knowing the KC
        - S: Probability of slipping (making a mistake despite knowing the KC)
    """

    def __init__(
        self,
        default_l0: float = 0.20,
        default_t: float = 0.15,
        default_g: float = 0.25,
        default_s: float = 0.10,
        version: str = "1.0.0",
    ) -> None:
        super().__init__(name="BKT-Standard", version=version)
        self.default_l0 = default_l0
        self.default_t = default_t
        self.default_g = default_g
        self.default_s = default_s

        # Parameters per KC: {kc_id: (l0, t, g, s)}
        self.kc_params: dict[str, tuple[float, float, float, float]] = {}

    @property
    def supports_time_decay(self) -> bool:
        """Standard BKT does NOT model temporal decay."""
        return False

    def fit(self, interactions: Sequence[StudentInteractionEvent]) -> StandardBKTModel:
        """Estimate BKT parameters per KC.

        In production or research pipelines, uses grid search or Expectation-Maximization (EM).
        Initializes with standard educational priors if data is sparse.
        """
        # For small/sparse datasets, use domain-calibrated priors with empirical adjustment
        kcs = {ev.kc_id for ev in interactions}
        for kc_id in kcs:
            kc_events = [ev for ev in interactions if ev.kc_id == kc_id]
            if len(kc_events) >= 10:
                acc = sum(ev.is_correct for ev in kc_events) / len(kc_events)
                l0 = min(0.60, max(0.10, acc * 0.5))
                self.kc_params[kc_id] = (l0, self.default_t, self.default_g, self.default_s)
            else:
                self.kc_params[kc_id] = (
                    self.default_l0,
                    self.default_t,
                    self.default_g,
                    self.default_s,
                )
        return self

    def _compute_current_knowledge(
        self,
        kc_id: str,
        kc_history: list[StudentInteractionEvent],
    ) -> float:
        """Forward-propagate BKT observation updates across chronological events."""
        l0, t, g, s = self.kc_params.get(
            kc_id, (self.default_l0, self.default_t, self.default_g, self.default_s)
        )

        p_l = l0
        for ev in kc_history:
            # Bayes update based on observed correct (1) or incorrect (0)
            if ev.is_correct == 1:
                denom = p_l * (1.0 - s) + (1.0 - p_l) * g
                if denom > 1e-9:
                    p_l_given_obs = (p_l * (1.0 - s)) / denom
                else:
                    p_l_given_obs = p_l
            else:
                denom = p_l * s + (1.0 - p_l) * (1.0 - g)
                if denom > 1e-9:
                    p_l_given_obs = (p_l * s) / denom
                else:
                    p_l_given_obs = p_l

            # Transition step: probability of learning between opportunities
            p_l = p_l_given_obs + (1.0 - p_l_given_obs) * t
            p_l = min(0.999, max(0.001, p_l))

        return p_l

    def predict_retention(
        self,
        student_id: str,
        kc_id: str,
        delta_seconds: float,
        history: Sequence[StudentInteractionEvent],
        reference_time: datetime | None = None,
    ) -> float:
        """Estimate P(R=1).

        NOTE: In standard BKT, delta_seconds has NO effect on the probability.
        """
        if reference_time is not None:
            relevant = [
                ev for ev in history if ev.kc_id == kc_id and ev.event_timestamp < reference_time
            ]
        else:
            relevant = [ev for ev in history if ev.kc_id == kc_id]

        relevant.sort(key=lambda e: e.event_timestamp)
        p_l = self._compute_current_knowledge(kc_id, relevant)

        _, _, g, s = self.kc_params.get(
            kc_id, (self.default_l0, self.default_t, self.default_g, self.default_s)
        )

        p_recall = p_l * (1.0 - s) + (1.0 - p_l) * g
        return min(0.999, max(0.001, p_recall))


class BKTDecayModel(TemporalRetentionModel):
    """BKT variant incorporating continuous exponential forgetting decay.

    Formulation:
        P(L(t + delta)) = P(L(t)) * exp(-lambda_k * delta)
        P(R=1 | delta) = P(L(t + delta)) * (1 - S) + (1 - P(L(t + delta))) * G
    """

    def __init__(
        self,
        default_l0: float = 0.20,
        default_t: float = 0.15,
        default_g: float = 0.25,
        default_s: float = 0.10,
        default_half_life_days: float = 5.0,  # Half-life of mastery in days
        version: str = "1.0.0",
    ) -> None:
        super().__init__(name="BKT-Decay", version=version)
        self.default_l0 = default_l0
        self.default_t = default_t
        self.default_g = default_g
        self.default_s = default_s

        # Decay rate lambda = ln(2) / half_life_seconds
        self.default_lambda = math.log(2.0) / (default_half_life_days * 86400.0)

        # Parameters per KC: {kc_id: (l0, t, g, s, lambda_decay)}
        self.kc_params: dict[str, tuple[float, float, float, float, float]] = {}

    @property
    def supports_time_decay(self) -> bool:
        """BKT-Decay supports continuous temporal decay."""
        return True

    def fit(self, interactions: Sequence[StudentInteractionEvent]) -> BKTDecayModel:
        """Fit parameters per KC."""
        kcs = {ev.kc_id for ev in interactions}
        for kc_id in kcs:
            kc_events = [ev for ev in interactions if ev.kc_id == kc_id]
            if len(kc_events) >= 10:
                acc = sum(ev.is_correct for ev in kc_events) / len(kc_events)
                l0 = min(0.60, max(0.10, acc * 0.5))
                self.kc_params[kc_id] = (
                    l0,
                    self.default_t,
                    self.default_g,
                    self.default_s,
                    self.default_lambda,
                )
            else:
                self.kc_params[kc_id] = (
                    self.default_l0,
                    self.default_t,
                    self.default_g,
                    self.default_s,
                    self.default_lambda,
                )
        return self

    def _forward_with_decay(
        self,
        kc_id: str,
        kc_history: list[StudentInteractionEvent],
        reference_time: datetime | None,
    ) -> float:
        """Propagate BKT updates including inter-event temporal decay."""
        l0, t, g, s, decay_lambda = self.kc_params.get(
            kc_id,
            (
                self.default_l0,
                self.default_t,
                self.default_g,
                self.default_s,
                self.default_lambda,
            ),
        )

        p_l = l0
        prev_time: datetime | None = None

        for ev in kc_history:
            # Apply decay from previous event if elapsed
            if prev_time is not None:
                elapsed_sec = max(0.0, (ev.event_timestamp - prev_time).total_seconds())
                p_l = p_l * math.exp(-decay_lambda * elapsed_sec)

            # Observation Bayes update
            if ev.is_correct == 1:
                denom = p_l * (1.0 - s) + (1.0 - p_l) * g
                p_l_given_obs = (p_l * (1.0 - s)) / denom if denom > 1e-9 else p_l
            else:
                denom = p_l * s + (1.0 - p_l) * (1.0 - g)
                p_l_given_obs = (p_l * s) / denom if denom > 1e-9 else p_l

            # Learning transition
            p_l = p_l_given_obs + (1.0 - p_l_given_obs) * t
            p_l = min(0.999, max(0.001, p_l))
            prev_time = ev.event_timestamp

        # Apply decay from last event to reference_time
        if prev_time is not None and reference_time is not None:
            elapsed_to_ref = max(0.0, (reference_time - prev_time).total_seconds())
            p_l = p_l * math.exp(-decay_lambda * elapsed_to_ref)

        return min(0.999, max(0.001, p_l))

    def predict_retention(
        self,
        student_id: str,
        kc_id: str,
        delta_seconds: float,
        history: Sequence[StudentInteractionEvent],
        reference_time: datetime | None = None,
    ) -> float:
        """Estimate P_recall(s, k, t + delta | history).

        Applies exponential decay exp(-lambda * delta_seconds) to the latent knowledge state.
        """
        if reference_time is not None:
            relevant = [
                ev for ev in history if ev.kc_id == kc_id and ev.event_timestamp < reference_time
            ]
        else:
            relevant = [ev for ev in history if ev.kc_id == kc_id]

        relevant.sort(key=lambda e: e.event_timestamp)
        p_l_at_ref = self._forward_with_decay(kc_id, relevant, reference_time)

        _, _, g, s, decay_lambda = self.kc_params.get(
            kc_id,
            (
                self.default_l0,
                self.default_t,
                self.default_g,
                self.default_s,
                self.default_lambda,
            ),
        )

        # Decay knowledge over future delta
        p_l_future = p_l_at_ref * math.exp(-decay_lambda * max(0.0, delta_seconds))

        p_recall = p_l_future * (1.0 - s) + (1.0 - p_l_future) * g
        return min(0.999, max(0.001, p_recall))
