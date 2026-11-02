---
name: model-training
description: Training, cross-validation, and artifact serialization for DAS3H and baseline models (PFA, BKT) using Student Group-K-Fold and frozen metadata packaging.
---
# Model Training Skill

## 1. Overview & Purpose
Train, regularize, cross-validate, and package candidate educational retention models under strict scientific rigor. Ensures reproducible training and frozen artifact packaging with full lineage.

## 2. Model Family Specifications
1. **Baseline 1 — Performance Factor Analysis (PFA)**:
   $$\text{logit}(P(R=1)) = \beta_k + \gamma_k S_{s,k} + \rho_k F_{s,k}$$
2. **Baseline 2 — Bayesian Knowledge Tracing with Decay (BKT-Decay)**:
   $$P(L_t) = P(L_{t-1}) e^{-\lambda \Delta t} + (1 - P(L_{t-1}) e^{-\lambda \Delta t}) T$$
3. **Champion Candidate — DAS3H**:
   $$\text{logit}(P(R=1)) = \theta_s - \beta_k + \sum_{w=1}^5 (\alpha_{k,w} S_{s,k,w} + \beta_{k,w} F_{s,k,w})$$

## 3. Cross-Validation Protocol
- **Grouping**: Stratified `GroupKFold(n_splits=5)` partitioned strictly by `student_id_pseudo`.
- **Generalization Target**: Ensures model evaluates out-of-sample student generalization; no student appears in both train and test splits.
- **Test Quarantine**: Evaluation items from the 7-day delayed post-test remain quarantined from training.

## 4. Optimization & Regularization
- **L2 Regularization (Ridge)** on time-window weights $\alpha_{k,w}, \beta_{k,w}$ to dampen noise in sparse historical windows.
- **Optimizer**: L-BFGS or SGD with early stopping keyed on validation Brier score.

## 5. Artifact Packaging Specification
Frozen models must be saved in `ml/artifacts/<model_name>_v<semver>/`:
- `model.pkl` / `weights.json`: Serialized parameters and intercept values.
- `feature_config.json`: Feature window parameters and scaling factors.
- `metadata.json`:
  ```json
  {
    "model_name": "das3h",
    "version": "1.0.0",
    "trained_at_utc": "2026-11-01T00:00:00Z",
    "git_commit": "abcdef123456",
    "dependencies": {
      "scikit-learn": "1.4.0",
      "numpy": "1.26.4",
      "pandas": "2.2.0"
    },
    "hyperparameters": {
      "l2_penalty": 0.01,
      "windows": 5,
      "max_iter": 500
    },
    "metrics_summary": {
      "auc_roc": 0.782,
      "brier_score": 0.154,
      "ece": 0.048
    }
  }
  ```
