# Model Selection & Comparative Architecture Analysis

**Project:** Plataforma de Microaprendizaje Adaptativo (5to Secundaria)  
**Target Domain:** Probabilistic Knowledge Tracing & Memory Retention Modeling  
**Date:** 2026-11-01  
**Status:** Approved Reference Specification  

---

## 1. Overview and Problem Statement

Predicting student recall probability $P(R=1 \mid h)$ over multi-day horizons ($h \in \{24, 72, 168\}$ hours) requires balancing mathematical expressiveness against statistical parameter estimation constraints. In a pilot study with $N \approx 66$ secondary school students, model complexity must be managed rigorously to prevent catastrophic overfitting.

This document presents the theoretical foundations, mathematical formulations, and comparative trade-off matrix for the candidate models:
1. **DAS3H** (Difficulty, Ability, Student, Student-Skill, Recency/Frequency across Log-Windows) — Primary Target Candidate.
2. **PFA (Performance Factor Analysis) / Temporal Logistic Regression** — Baseline 1.
3. **BKT (Bayesian Knowledge Tracing with Forgetting)** — Baseline 2.
4. **CatBoost (Gradient Boosted Decision Trees)** — Baseline 3.
5. **DKT (Deep Knowledge Tracing / RNN)** — Reference Evaluated Architecture.

---

## 2. Mathematical Formulations

### 2.1 DAS3H (Difficulty, Ability, Student, Student-Skill, Recency/Frequency across Log-Windows)

DAS3H extends Item Response Theory (IRT) and Performance Factor Analysis by incorporating power-law forgetting curves across multiple log-spaced time windows:

$$\text{logit}\left( P(Y_{u,i,t} = 1) \right) = \alpha_u - \beta_i + \sum_{k \in KC(i)} \left( \gamma_k + \sum_{w=1}^{W} \left( \theta_{k,w} s_{u,k,w} + \tau_{k,w} f_{u,k,w} \right) \right)$$

Where:
- $\alpha_u \in \mathbb{R}$: Latent mastery/ability parameter for student $u$.
- $\beta_i \in \mathbb{R}$: Calibrated difficulty parameter for question item $i$.
- $\gamma_k \in \mathbb{R}$: Base difficulty/mastery offset for Knowledge Component $k$.
- $W$: Number of log-spaced time windows ($W = 5$).
- $s_{u,k,w} = \log(1 + C_{u,k,w}^{\text{success}})$: Log-transformed count of past successful interactions of student $u$ on KC $k$ within time window $w$.
- $f_{u,k,w} = \log(1 + C_{u,k,w}^{\text{failure}})$: Log-transformed count of past failed interactions of student $u$ on KC $k$ within time window $w$.
- $\theta_{k,w}, \tau_{k,w}$: Learned coefficients representing the decay weights of successes and failures within window $w$.

#### Time Windows Definition:
- $W_1$: Interactions within the last 1 hour: $[0, 3600)$ seconds.
- $W_2$: Interactions within 1 hour to 1 day: $[3600, 86400)$ seconds.
- $W_3$: Interactions within 1 day to 7 days: $[86400, 604800)$ seconds.
- $W_4$: Interactions within 7 days to 30 days: $[604800, 2592000)$ seconds.
- $W_5$: Interactions older than 30 days: $[2592000, \infty)$ seconds.

---

### 2.2 Baseline 1: Temporal Logistic Regression / Extended PFA

An interpretable logistic formulation tracking cumulative successes ($S_{u,k}$), failures ($F_{u,k}$), and log-recency ($\Delta t$):

$$\text{logit}\left( P(Y_{u,i,t} = 1) \right) = \alpha_u - \beta_i + \gamma_k + \theta_k S_{u,k} + \tau_k F_{u,k} - \lambda_k \log(1 + \Delta t)$$

Where:
- $\Delta t$: Elapsed time (in hours) since the student's most recent interaction on KC $k$.
- $\lambda_k \ge 0$: Knowledge decay rate (forgetting parameter) for KC $k$.
- Requires estimating only 3 parameters per KC ($\theta_k, \tau_k, \lambda_k$), ensuring convergence even with very small student cohorts ($N \approx 66$).

---

### 2.3 Baseline 2: Modified Bayesian Knowledge Tracing (BKT with Decay)

A two-state Hidden Markov Model tracking whether student $u$ is in the learned state ($L_t = 1$) or unlearned state ($L_t = 0$) for KC $k$:

- Initial knowledge prior: $P(L_0) = p_{\text{init}}$
- Transition (learning rate): $P(L_t = 1 \mid L_{t-1} = 0) = p_T$
- Forgetting rate (decay over interval $\Delta t$):
  $$P(L_t = 0 \mid L_{t-1} = 1) = 1 - e^{-\delta \cdot \Delta t}$$
- Slip probability: $P(Y_t = 0 \mid L_t = 1) = s$
- Guess probability: $P(Y_t = 1 \mid L_t = 0) = g$

Probability of recall at time $t$:
$$P(Y_t = 1) = P(L_t) \cdot (1 - s) + (1 - P(L_t)) \cdot g$$

---

### 2.4 Baseline 3: CatBoost Gradient Boosted Decision Trees

A tree-based approach operating on tabular engineered summary features:
- Input vector $\vec{x}_{u,k,t}$: student historical accuracy rate, total attempts on KC, average response time, inter-practice interval, item difficulty prior, and current section average.
- Objective: Logloss on binary outcome $y \in \{0, 1\}$.
- Advantages: Automatically captures non-linear feature interactions without manual scaling; highly robust to outliers in response time.

---

### 2.5 Evaluated Architecture: Deep Knowledge Tracing (DKT)

Recurrent Neural Network (LSTM / GRU) encoding student interaction sequences:
- Input: One-hot vector $\vec{x}_t \in \{0, 1\}^{2|E|}$ encoding the tuple $(\text{KC}_t, y_t)$.
- Hidden state update: $\vec{h}_t = \tanh(W_{hx} \vec{x}_t + W_{hh} \vec{h}_{t-1} + \vec{b}_h)$.
- Prediction: $\vec{y}_t = \sigma(W_{yh} \vec{h}_t + \vec{b}_y)$.
- **Assessment for Pilot:** DKT contains tens of thousands of trainable weights. On $N \approx 66$ students, empirical studies show severe overfitting and unstable probability calibration. Therefore, DKT is excluded from production inference and retained strictly as an academic research comparison in offline experiments.

---

## 3. Comparative Trade-Off Matrix

| Dimension | DAS3H | Extended PFA | Modified BKT | CatBoost | DKT (LSTM) |
|---|---|---|---|---|---|
| **Sample Size Sensitivity ($N \approx 66$)** | Moderate (benefits from shrinkage / prior transfer) | Very Low (readily converges on small samples) | Low (4 parameters per KC) | Low to Moderate | Severe Overfitting Risk |
| **Temporal Granularity** | High (5 log-spaced windows) | Moderate (cumulative counts + single $\Delta t$) | Discrete (transition per opportunity) | Low to Moderate (aggregated summary) | High (sequential RNN) |
| **Probability Calibration** | High (calibrated via logistic link) | High (calibrated via logistic link) | Moderate (bounded by guess/slip) | Moderate (requires Platt scaling) | Low (tends to overconfident extremes) |
| **Inference Latency** | $\le 200$ ms | $\le 50$ ms | $\le 80$ ms | $\le 100$ ms | $\ge 400$ ms |
| **Interpretability** | High (additive weights per window) | Very High (linear coefficients) | High (belief state) | Moderate (SHAP values) | Black Box |
| **Production Readiness** | Candidate 1 | Production Baseline | Benchmark Baseline | Tabular Baseline | Research Only |

---

## 4. Formal Model Promotion Workflow

```text
[Training Dataset: ml/datasets/]
               │
               ▼
[Student-Stratified Group-K-Fold (K=5)]
               │
      ┌────────┴────────┐
      ▼                 ▼
[Baseline 1: PFA]   [Candidate: DAS3H]
      │                 │
      ├─────────────────┤
      ▼                 ▼
[Evaluation: AUC-ROC, Brier Score, ECE]
               │
    Is DAS3H AUC >= Baseline AUC + 0.02
    AND DAS3H Brier < Baseline Brier?
         /           \
       YES            NO
        │              │
        ▼              ▼
[Promote DAS3H]   [Retain PFA Baseline]
(Pack artifact)   (Log in research docs)
```

1. **Pre-Training Gate:** Initialize item difficulty priors ($\beta_i$) using historical pilot diagnostic data or public educational benchmarks.
2. **Cross-Validation Execution:** Run 5-fold Student-Stratified Group-K-Fold cross-validation via `ml/src/training/train_das3h.py`.
3. **Threshold Gate:** Candidate DAS3H is approved for deployment in `services/ml-api/` if and only if:
   - $\text{AUC-ROC}_{\text{DAS3H}} \ge \text{AUC-ROC}_{\text{Baseline}} + 0.02$
   - $\text{Brier}_{\text{DAS3H}} < \text{Brier}_{\text{Baseline}}$
   - $\text{ECE}_{\text{DAS3H}} \le 0.08$
4. **Artifact Freezing:** Export artifact with `metadata.json` including git commit SHA, training timestamp, and library versions.
