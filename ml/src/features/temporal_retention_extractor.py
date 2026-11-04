"""Temporal feature extractor for DAS3H and longitudinal memory modeling.

Computes causal time-window features (W1..W5) for student interaction histories,
supporting projection into future elapsed horizons (delta_seconds >= 0)
without temporal data leakage.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

from ml.src.contracts.exposure_contract import StudentInteractionEvent

# 5 logarithmic time windows defined in seconds:
# W1: [0, 1h)
# W2: [1h, 1d)
# W3: [1d, 7d)
# W4: [7d, 30d)
# W5: [30d, inf)
WINDOW_BOUNDS_SECONDS: list[tuple[float, float]] = [
    (0.0, 3600.0),                     # W1: [0, 1h)
    (3600.0, 86400.0),                 # W2: [1h, 1d)
    (86400.0, 7.0 * 86400.0),          # W3: [1d, 7d)
    (7.0 * 86400.0, 30.0 * 86400.0),   # W4: [7d, 30d)
    (30.0 * 86400.0, float("inf")),    # W5: [30d, inf)
]


class TemporalWindowCounts:
    """Historical successes and failures distributed across 5 logarithmic windows."""

    def __init__(self) -> None:
        self.successes: list[int] = [0, 0, 0, 0, 0]  # s_w1 .. s_w5
        self.failures: list[int] = [0, 0, 0, 0, 0]   # f_w1 .. f_w5
        self.last_elapsed_seconds: float | None = None
        self.total_interactions: int = 0

    @property
    def total_successes(self) -> int:
        return sum(self.successes)

    @property
    def total_failures(self) -> int:
        return sum(self.failures)


def extract_das3h_window_features(
    kc_history: Sequence[StudentInteractionEvent],
    reference_time: datetime,
    delta_seconds: float = 0.0,
) -> TemporalWindowCounts:
    """Extract causal DAS3H window features projected to future horizon (reference_time + delta_seconds).

    ANTI-LEAKAGE ENFORCEMENT:
    Only events with event_timestamp < reference_time are considered.
    For each past event, its effective elapsed time at the future horizon is:
        delta_effective = (reference_time + delta_seconds) - event.event_timestamp

    As delta_seconds increases, past events naturally shift from shorter windows
    (e.g. W1, W2) into longer windows (e.g. W4, W5), modeling memory decay.
    """
    counts = TemporalWindowCounts()

    # Filter strictly prior to reference_time
    prior_events = [ev for ev in kc_history if ev.event_timestamp < reference_time]
    if not prior_events:
        return counts

    prior_events.sort(key=lambda e: e.event_timestamp)
    counts.total_interactions = len(prior_events)

    most_recent_timestamp = prior_events[-1].event_timestamp
    base_last_elapsed = max(0.0, (reference_time - most_recent_timestamp).total_seconds())
    counts.last_elapsed_seconds = base_last_elapsed + max(0.0, delta_seconds)

    for ev in prior_events:
        base_elapsed = max(0.0, (reference_time - ev.event_timestamp).total_seconds())
        effective_elapsed = base_elapsed + max(0.0, delta_seconds)

        # Place event into the appropriate window
        for w_idx, (w_low, w_high) in enumerate(WINDOW_BOUNDS_SECONDS):
            if w_low <= effective_elapsed < w_high:
                if ev.is_correct == 1:
                    counts.successes[w_idx] += 1
                else:
                    counts.failures[w_idx] += 1
                break

    return counts
