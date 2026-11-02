---
name: model-evaluation
description: Rigorous evaluation of educational predictive models using discrimination (AUC-ROC), calibration (Brier score, ECE), reliability diagrams, and decision curve analysis.
---
# Model Evaluation Skill

## 1. Overview & Purpose
Formally evaluate model candidates across discrimination capacity and probabilistic calibration prior to production promotion. Assesses whether predicted probabilities reflect true empirical recovery rates.

## 2. Evaluation Metrics & Acceptable Thresholds
1. **Discrimination — AUC-ROC**:
   - Evaluates ability to rank recall events above forgotten events.
   - Acceptance threshold: $\text{AUC-ROC} \ge 0.75$.
2. **Probabilistic Calibration — Brier Score**:
   $$\text{BS} = \frac{1}{N} \sum_{i=1}^N (\hat{p}_i - y_i)^2$$
   - Acceptance threshold: $\text{BS} \le 0.18$.
3. **Expected Calibration Error (ECE)**:
   $$\text{ECE} = \sum_{m=1}^{10} \frac{|B_m|}{N} \left| \text{acc}(B_m) - \text{conf}(B_m) \right|$$
   - Acceptance threshold: $\text{ECE} \le 0.08$.
4. **Baseline Superiority**:
   - Candidate model (DAS3H) must statistically outperform PFA and BKT in AUC-ROC with $p < 0.05$ (Wilcoxon signed-rank test across 5 folds).

## 3. Reliability Curves & Post-Processing
- Generate 10-bin reliability diagrams (Mean Predicted Probability vs Observed Accuracy).
- In case of miscalibration ($\text{ECE} > 0.08$), assess post-hoc calibration methods (Platt Scaling or Isotonic Regression) on held-out validation data.

## 4. Automated Evaluation Report
- Generate `ml/artifacts/<model_name>_v<semver>/evaluation_report.json` logging cross-validation fold metrics, confidence intervals, and baseline comparison tables.
