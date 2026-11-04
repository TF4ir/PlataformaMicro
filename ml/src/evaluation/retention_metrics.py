"""Evaluation metrics for retention prediction, calibration, and review time estimation.

Addresses Section 7 of TASK M5.1:
Implements:
- Brier Score (mean squared error of probabilistic predictions)
- Log Loss / Binary Cross-Entropy
- AUC-ROC (ranking/discrimination capacity)
- Expected Calibration Error (ECE - 10 uniform bins)
- Reliability Diagram bin statistics
- Mean Absolute Error in Review Interval Estimation (MAE_delta)
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np


def brier_score(y_true: Sequence[int], y_prob: Sequence[float]) -> float:
    """Compute the Brier Score: (1/N) * sum((p_i - y_i)^2).

    Measures probabilistic calibration and accuracy. Acceptance threshold: <= 0.18.
    """
    if not y_true or len(y_true) != len(y_prob):
        raise ValueError("y_true and y_prob must be non-empty and of equal length.")

    y_t = np.asarray(y_true, dtype=np.float64)
    y_p = np.asarray(y_prob, dtype=np.float64)
    return float(np.mean((y_p - y_t) ** 2))


def log_loss(y_true: Sequence[int], y_prob: Sequence[float], eps: float = 1e-15) -> float:
    """Compute the Binary Cross-Entropy / Log Loss: -(1/N) * sum(y*ln(p) + (1-y)*ln(1-p))."""
    if not y_true or len(y_true) != len(y_prob):
        raise ValueError("y_true and y_prob must be non-empty and of equal length.")

    y_t = np.asarray(y_true, dtype=np.float64)
    y_p = np.clip(np.asarray(y_prob, dtype=np.float64), eps, 1.0 - eps)
    loss = -(y_t * np.log(y_p) + (1.0 - y_t) * np.log(1.0 - y_p))
    return float(np.mean(loss))


def auc_roc(y_true: Sequence[int], y_prob: Sequence[float]) -> float:
    """Compute Area Under the Receiver Operating Characteristic Curve (AUC-ROC).

    Uses the Mann-Whitney U statistic formulation for exact, dependency-free calculation.
    """
    if not y_true or len(y_true) != len(y_prob):
        raise ValueError("y_true and y_prob must be non-empty and of equal length.")

    y_t = np.asarray(y_true, dtype=np.int32)
    y_p = np.asarray(y_prob, dtype=np.float64)

    pos = y_p[y_t == 1]
    neg = y_p[y_t == 0]

    n_pos = len(pos)
    n_neg = len(neg)

    if n_pos == 0 or n_neg == 0:
        # Cannot calculate AUC if only one class exists
        return 0.50

    # Mann-Whitney U calculation
    # For each pair (p, n), count 1 if p > n, 0.5 if p == n
    # Vectorized computation:
    diff = pos[:, None] - neg[None, :]
    u_stat = np.sum(diff > 0) + 0.5 * np.sum(diff == 0)
    return float(u_stat / (n_pos * n_neg))


def expected_calibration_error(
    y_true: Sequence[int],
    y_prob: Sequence[float],
    n_bins: int = 10,
) -> float:
    """Compute Expected Calibration Error (ECE) across n equal-width bins.

    Formula:
        ECE = sum_{m=1}^{M} (|B_m| / N) * |accuracy(B_m) - confidence(B_m)|

    Acceptance threshold for retention forecasting: ECE <= 0.08.
    """
    if not y_true or len(y_true) != len(y_prob):
        raise ValueError("y_true and y_prob must be non-empty and of equal length.")

    y_t = np.asarray(y_true, dtype=np.float64)
    y_p = np.asarray(y_prob, dtype=np.float64)
    n = len(y_t)

    bin_boundaries = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0

    for i in range(n_bins):
        bin_lower = bin_boundaries[i]
        bin_upper = bin_boundaries[i + 1]

        if i == n_bins - 1:
            in_bin = (y_p >= bin_lower) & (y_p <= bin_upper)
        else:
            in_bin = (y_p >= bin_lower) & (y_p < bin_upper)

        bin_size = np.sum(in_bin)
        if bin_size > 0:
            bin_acc = np.mean(y_t[in_bin])
            bin_conf = np.mean(y_p[in_bin])
            ece += (bin_size / n) * abs(bin_acc - bin_conf)

    return float(ece)


def review_interval_mae_days(
    predicted_forgetting_times_sec: Sequence[float],
    observed_failure_times_sec: Sequence[float],
) -> float:
    """Compute Mean Absolute Error (MAE) in review interval estimation (in days).

    Compares the predicted critical threshold crossing time against the actual
    timestamp when retrieval failure was first observed during deferred evaluation.
    """
    if not predicted_forgetting_times_sec or len(predicted_forgetting_times_sec) != len(
        observed_failure_times_sec
    ):
        raise ValueError("Inputs must be non-empty and of equal length.")

    p_arr = np.asarray(predicted_forgetting_times_sec, dtype=np.float64) / 86400.0
    o_arr = np.asarray(observed_failure_times_sec, dtype=np.float64) / 86400.0
    return float(np.mean(np.abs(p_arr - o_arr)))
