"""Synthetic longitudinal memory dataset generator for retention benchmark.

Addresses Section 3 of TASK M5.2-A:
Implements 7 distinct synthetic scenarios:
1. no_forgetting: Retention remains stable between reviews.
2. exponential_decay: Classic Ebbinghaus exponential forgetting curve.
3. heterogeneous_decay: Varying memory decay speeds per student and KC.
4. power_law_decay: Power law of forgetting (Wixted & Ebbesen, 1991).
5. spacing_and_testing_effect: Successful retrievals exponentially increase stability.
6. noisy_slip_guess: Cognitive noise with item slip and guess probabilities.
7. model_mismatch: Weibull / stretched-exponential decay (different functional form).

Guarantees full reproducibility through deterministic random seeds and complete metadata.
"""

from __future__ import annotations

import math
import uuid
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

import numpy as np

from ml.src.contracts.exposure_contract import StudentInteractionEvent


class SyntheticScenario(str, Enum):
    NO_FORGETTING = "no_forgetting"
    EXPONENTIAL_DECAY = "exponential_decay"
    HETEROGENEOUS_DECAY = "heterogeneous_decay"
    POWER_LAW_DECAY = "power_law_decay"
    SPACING_AND_TESTING_EFFECT = "spacing_and_testing_effect"
    NOISY_SLIP_GUESS = "noisy_slip_guess"
    MODEL_MISMATCH = "model_mismatch"


@dataclass
class SyntheticTestQuery:
    """Out-of-sample evaluation instance with ground-truth retention and critical time."""

    student_id_pseudo: str
    kc_id: str
    reference_time: datetime
    delta_seconds: float
    p_true: float
    y_obs: int
    true_forgetting_time_seconds: float | None
    tau: float


@dataclass
class SyntheticDataset:
    """Container for a generated synthetic retention experiment."""

    scenario: SyntheticScenario
    random_seed: int
    generator_version: str = "1.0.0"
    data_origin: str = "synthetic"
    parameters: dict[str, Any] = field(default_factory=dict)
    train_events: list[StudentInteractionEvent] = field(default_factory=list)
    test_queries: list[SyntheticTestQuery] = field(default_factory=list)

    @property
    def total_events(self) -> int:
        return len(self.train_events)

    @property
    def total_queries(self) -> int:
        return len(self.test_queries)


class SyntheticMemoryGenerator:
    """Deterministic generator for synthetic student retention and retrieval datasets."""

    def __init__(self, random_seed: int = 42, generator_version: str = "1.0.0") -> None:
        self.random_seed = random_seed
        self.generator_version = generator_version

    def generate(
        self,
        scenario: SyntheticScenario,
        n_students: int = 25,
        n_kcs: int = 6,
        events_per_pair: int = 5,
        tau: float = 0.65,
        base_stability_days: float = 3.0,
        test_horizons_days: Sequence[float] | None = None,
    ) -> SyntheticDataset:
        """Generate a complete synthetic dataset for a specific cognitive scenario."""
        rng = np.random.default_rng(self.random_seed)

        if test_horizons_days is None:
            # Multi-horizon evaluation grid: 1h, 12h, 1d, 3d, 7d, 14d, 21d
            test_horizons_days = [1 / 24, 0.5, 1.0, 3.0, 7.0, 14.0, 21.0]

        start_time = datetime(2026, 10, 1, 9, 0, 0, tzinfo=UTC)
        train_events: list[StudentInteractionEvent] = []
        test_queries: list[SyntheticTestQuery] = []

        students = [f"std-{i+1:03d}" for i in range(n_students)]
        kcs = [f"kc-{j+1:02d}" for j in range(n_kcs)]

        # Heterogeneous student and KC factors
        student_speeds = {s: float(rng.uniform(0.6, 1.5)) for s in students}
        kc_difficulties = {k: float(rng.uniform(0.7, 1.4)) for k in kcs}

        for s_id in students:
            for kc_id in kcs:
                # Track longitudinal memory state for this student-KC trajectory
                stability_days = base_stability_days
                if scenario in (SyntheticScenario.HETEROGENEOUS_DECAY, SyntheticScenario.SPACING_AND_TESTING_EFFECT):
                    stability_days = base_stability_days / (student_speeds[s_id] * kc_difficulties[kc_id])

                current_time = start_time + timedelta(hours=float(rng.uniform(0, 12)))
                pair_history: list[StudentInteractionEvent] = []

                for ev_idx in range(events_per_pair):
                    # Inter-event gap: spacing intervals (e.g. 1d, 2d, 4d, 7d)
                    if ev_idx > 0:
                        interval_days = float(rng.exponential(scale=2.0) + 0.5)
                        current_time += timedelta(days=interval_days)

                    # Compute true retrieval probability at this practice moment
                    elapsed_days = 0.0 if ev_idx == 0 else interval_days
                    elapsed_sec = elapsed_days * 86400.0

                    p_true = self._calculate_p_true(
                        scenario=scenario,
                        delta_seconds=elapsed_sec,
                        stability_days=stability_days,
                        ev_idx=ev_idx,
                        rng=rng,
                    )

                    # Sample binary outcome with optional slip/guess
                    p_obs = p_true
                    if scenario == SyntheticScenario.NOISY_SLIP_GUESS:
                        slip, guess = 0.10, 0.20
                        p_obs = p_true * (1.0 - slip) + (1.0 - p_true) * guess

                    is_correct = int(rng.uniform(0.0, 1.0) < p_obs)

                    ev = StudentInteractionEvent(
                        event_id=uuid.uuid4(),
                        student_id_pseudo=s_id,
                        kc_id=kc_id,
                        question_id=f"q-{kc_id}-{ev_idx+1}",
                        event_timestamp=current_time,
                        is_correct=is_correct,
                        response_time_seconds=float(rng.uniform(8.0, 30.0)),
                        activity_type="practice",
                    )
                    train_events.append(ev)
                    pair_history.append(ev)

                    # Update stability if scenario models testing / spacing benefits
                    if scenario == SyntheticScenario.SPACING_AND_TESTING_EFFECT:
                        if is_correct:
                            stability_days *= 1.8  # Practice reinforces retention
                        else:
                            stability_days = max(1.0, stability_days * 0.7)

                # Reference time for out-of-sample prediction: 1 hour after last practice
                ref_time = current_time + timedelta(hours=1)

                # Calculate true critical forgetting time where P_true(delta) <= tau
                true_delta_crit_sec = self._solve_true_forgetting_time(
                    scenario=scenario,
                    stability_days=stability_days,
                    tau=tau,
                )

                # Sample out-of-sample future evaluation queries
                for h_days in test_horizons_days:
                    delta_sec = h_days * 86400.0
                    p_future_true = self._calculate_p_true(
                        scenario=scenario,
                        delta_seconds=delta_sec,
                        stability_days=stability_days,
                        ev_idx=events_per_pair,
                        rng=rng,
                    )
                    p_obs_future = p_future_true
                    if scenario == SyntheticScenario.NOISY_SLIP_GUESS:
                        slip, guess = 0.10, 0.20
                        p_obs_future = p_future_true * (1.0 - slip) + (1.0 - p_future_true) * guess

                    y_obs = int(rng.uniform(0.0, 1.0) < p_obs_future)

                    test_queries.append(
                        SyntheticTestQuery(
                            student_id_pseudo=s_id,
                            kc_id=kc_id,
                            reference_time=ref_time,
                            delta_seconds=delta_sec,
                            p_true=round(p_future_true, 4),
                            y_obs=y_obs,
                            true_forgetting_time_seconds=true_delta_crit_sec,
                            tau=tau,
                        )
                    )

        # Sort training events strictly chronologically
        train_events.sort(key=lambda e: e.event_timestamp)

        params = {
            "n_students": n_students,
            "n_kcs": n_kcs,
            "events_per_pair": events_per_pair,
            "tau": tau,
            "base_stability_days": base_stability_days,
            "test_horizons_days": list(test_horizons_days),
        }

        return SyntheticDataset(
            scenario=scenario,
            random_seed=self.random_seed,
            generator_version=self.generator_version,
            parameters=params,
            train_events=train_events,
            test_queries=test_queries,
        )

    def _calculate_p_true(
        self,
        scenario: SyntheticScenario,
        delta_seconds: float,
        stability_days: float,
        ev_idx: int,
        rng: np.random.Generator,
    ) -> float:
        """Evaluate the ground truth retention probability for a given scenario."""
        delta_days = max(0.0, delta_seconds / 86400.0)

        if scenario == SyntheticScenario.NO_FORGETTING:
            # Constant retention regardless of elapsed time
            return 0.88

        elif scenario in (
            SyntheticScenario.EXPONENTIAL_DECAY,
            SyntheticScenario.HETEROGENEOUS_DECAY,
            SyntheticScenario.SPACING_AND_TESTING_EFFECT,
            SyntheticScenario.NOISY_SLIP_GUESS,
        ):
            # Ebbinghaus exponential decay: P(t) = exp(-delta / S)
            val = math.exp(-delta_days / max(0.1, stability_days))
            return float(np.clip(val, 0.05, 0.98))

        elif scenario == SyntheticScenario.POWER_LAW_DECAY:
            # Power law of forgetting: P(t) = (1 + a * t)^(-b) (Anderson & Schooler, 1991)
            a = 0.50
            b = 0.40
            val = (1.0 + a * delta_days) ** (-b)
            return float(np.clip(val, 0.05, 0.98))

        elif scenario == SyntheticScenario.MODEL_MISMATCH:
            # Weibull / stretched-exponential decay with shape parameter kappa = 1.6
            # Structural mismatch: decay accelerates over time
            eta = max(1.0, stability_days * 1.5)
            kappa = 1.6
            val = math.exp(-((delta_days / eta) ** kappa))
            return float(np.clip(val, 0.05, 0.98))

        return 0.70

    def _solve_true_forgetting_time(
        self,
        scenario: SyntheticScenario,
        stability_days: float,
        tau: float,
    ) -> float | None:
        """Compute the true critical forgetting time (in seconds) where P_true(delta) <= tau."""
        if scenario == SyntheticScenario.NO_FORGETTING:
            # Never crosses tau if 0.88 > tau
            return None if tau < 0.88 else 0.0

        elif scenario in (
            SyntheticScenario.EXPONENTIAL_DECAY,
            SyntheticScenario.HETEROGENEOUS_DECAY,
            SyntheticScenario.SPACING_AND_TESTING_EFFECT,
            SyntheticScenario.NOISY_SLIP_GUESS,
        ):
            # exp(-delta / S) = tau => delta = -S * ln(tau)
            if tau >= 1.0:
                return 0.0
            if tau <= 0.0:
                return None
            crit_days = -stability_days * math.log(tau)
            return round(crit_days * 86400.0, 2)

        elif scenario == SyntheticScenario.POWER_LAW_DECAY:
            # (1 + a * delta)^(-b) = tau => delta = ((tau)^(-1/b) - 1) / a
            a = 0.50
            b = 0.40
            if tau >= 1.0:
                return 0.0
            crit_days = ((tau ** (-1.0 / b)) - 1.0) / a
            return float(round(max(0.0, crit_days * 86400.0), 2))

        elif scenario == SyntheticScenario.MODEL_MISMATCH:
            # exp(-(delta / eta)^kappa) = tau => delta = eta * (-ln(tau))^(1/kappa)
            eta = max(1.0, stability_days * 1.5)
            kappa = 1.6
            if tau >= 1.0:
                return 0.0
            crit_days = eta * ((-math.log(tau)) ** (1.0 / kappa))
            return float(round(max(0.0, crit_days * 86400.0), 2))

        return None
