---
name: feature-engineering
description: Feature extraction and representation pipeline for DAS3H (log-time windows, past successes/failures) and baseline knowledge tracing models without temporal data leakage.
---
# Feature Engineering Skill

## 1. Overview & Purpose
Transform raw `answer_events` time series into lag-aware feature matrices for temporal memory modeling (DAS3H, PFA, BKT). Guarantees mathematically sound decay window representations without temporal data leakage.

## 2. DAS3H Temporal Window Architecture
Implement 5 logarithmically spaced historical time windows to capture memory decay dynamics:
- $W_1 = [0, 1\text{ hour})$
- $W_2 = [1\text{ hour}, 1\text{ day})$
- $W_3 = [1\text{ day}, 7\text{ days})$
- $W_4 = [7\text{ days}, 30\text{ days})$
- $W_5 = [30\text{ days}, \infty)$

For each student $s$, knowledge component $k$, and window $w$, calculate:
- $S_{s,k,w}$: Cumulative count of correct attempts in window $w$.
- $F_{s,k,w}$: Cumulative count of incorrect attempts in window $w$.

## 3. Additional Temporal Features
- **Log Elapsed Time**: $\ln(1 + \Delta t)$, where $\Delta t$ is the elapsed seconds since the previous attempt on the same KC.
- **Cumulative Volume**: $N_{s,k} = \sum_{w=1}^5 (S_{s,k,w} + F_{s,k,w})$.
- **Standardized Response Time**: $z$-score normalized response time within item / KC.

## 4. Strict Anti-Leakage Guardrails
1. **Causality Enforcement**: When computing feature vectors for an event at timestamp $t_i$, features may ONLY use interactions where $t < t_i$.
2. **Quarantine Horizon**: Responses from future delayed evaluations ($h \in \{24, 72, 168\}\text{h}$) must NEVER appear in the predictor matrix.
3. **Fold Isolation**: Feature scaling, mean imputations, and encodings must be fitted strictly on the training fold and applied to validation/test folds without re-fitting.

## 5. Data Output Contract
- Matrix storage: Parquet / NumPy array format with explicit column definitions.
- Configuration metadata: `feature_config.json` documenting window bounds and feature mapping.
