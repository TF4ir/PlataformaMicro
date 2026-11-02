---
name: predictive-modeling
description: End-to-end ML lifecycle coordinator for student memory retention modeling (DAS3H, PFA, BKT) aggregating EDA, features, training, and evaluation.
---
# Predictive Modeling Skill

## 1. Overview & Role
Coordinates the machine learning research lifecycle within `ml/`, orchestrating data preparation, temporal lag features, cross-validation, and artifact freezing.

## 2. Core Methodologies
- Coordinates `eda-pipeline`, `feature-engineering`, `model-training`, and `model-evaluation`.
- Validates model superiority: Candidate DAS3H must statistically surpass PFA and BKT in AUC-ROC and calibration.
- Enforces Student Group-K-Fold to prevent data leakage across train and test partitions.
- Maintains strict quarantine over delayed-retention evaluation items (7-day post-test).
- Freezes approved models in `ml/artifacts/<name>_v<semver>/` with complete `metadata.json`.

## 3. Cross-References
- `ml/AGENTS.md`
- `.agents/rules/machine-learning.md`
- `.agents/skills/eda-pipeline/`
- `.agents/skills/feature-engineering/`
- `.agents/skills/model-training/`
- `.agents/skills/model-evaluation/`
