---
name: eda-pipeline
description: Exploratory Data Analysis pipeline for adaptive microlearning interaction logs, student behavior temporal sparsity, knowledge component coverage, and response time distributions.
---
# EDA Pipeline Skill

## 1. Overview & Purpose
Pre-modeling exploratory data analysis and sanity checks on educational interaction logs. Ensures data satisfies assumptions of knowledge tracing models (DAS3H, PFA, BKT) and detects distribution anomalies prior to training and feature engineering.

## 2. Data Ingestion Schema
Interaction logs must adhere to the immutable `answer_events` schema:
- `attempt_id` (UUID): Unique attempt session identifier.
- `student_id_pseudo` (UUID): Disassociated student pseudonym.
- `question_id` (UUID): Item evaluated.
- `knowledge_component_id` (UUID): Knowledge component associated with question.
- `is_correct` (boolean): Observed binary answer outcome ($y_i \in \{0, 1\}$).
- `response_time_seconds` (numeric): Latency from item presentation to answer submission.
- `event_timestamp` (timestamptz): Monotonic timestamp of event occurrence.

## 3. Analysis Protocols
1. **Interaction Sparsity & Density Analysis**:
   - Compute mean, standard deviation, and median attempts per student and per Knowledge Component.
   - Detect cold-start proportion (students with fewer than 5 recorded attempts).
2. **Temporal Dynamics**:
   - Measure inter-attempt intervals ($\Delta t$) and retention delay distributions.
   - Cluster session inactivity gaps ($> 24\text{h}$ intervals) to define review opportunities.
3. **Response Time Anomaly Detection**:
   - Flag speed-guessing anomalies ($t < 2.0\text{s}$).
   - Flag timeout/abandonment outliers ($t > 300\text{s}$).
4. **Psychometric Baseline**:
   - Calculate item difficulty $P(\text{correct})$ per question.
   - Calculate point-biserial discrimination index ($r_{pbis}$) between item success and student total score.

## 4. Privacy & Integrity Checks
- **PII Quarantine**: Validate complete absence of real names, emails, and school identification numbers (only `student_id_pseudo` allowed).
- **Temporal Monotonicity**: Enforce strict chronological ordering within each student trajectory (`event_timestamp`).

## 5. Outputs & Artifacts
- JSON Summary Report: `ml/datasets/eda_summary.json` containing summary statistics.
- Visualization plots: sparsity heatmap, log response time distribution, empirical retention decay curve.
