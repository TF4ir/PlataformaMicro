# Research Data Dictionary & Variable Specifications

**Project:** Plataforma de Microaprendizaje Adaptativo (5to Secundaria)  
**Legal Framework:** Ley N° 29733 (Ley de Protección de Datos Personales - Perú)  
**Target Domain:** Quasi-Experimental Evaluation & Knowledge Tracing Datasets  
**Date:** 2026-11-01  
**Status:** Approved Reference Specification  

---

## 1. Overview & Data Privacy Architecture

This dictionary documents all variables, feature representations, and database schemas utilized in the educational research and evaluation pipeline. To comply strictly with **Peruvian Law N° 29733 (Ley de Protección de Datos Personales)** and ethical standards for minors (aged 16–17 years):

1. **Personally Identifiable Information (PII) Isolation:**
   - Real names, email addresses, phone numbers, and national identity numbers (DNI) are stored exclusively in `profiles` and are **never** exported into data science or evaluation datasets.
2. **Persistent Analytical Pseudonymization:**
   - Every student enrollment in a section is assigned an immutable, cryptographically generated UUID: `student_id_pseudo = gen_random_uuid()`.
   - All research analyses, machine learning training sets, cross-validation scripts, and thesis publication tables reference `student_id_pseudo` exclusively.

---

## 2. Core Interaction Entities

### 2.1 `answer_events` (Append-Only Interaction Log)

The immutable primary event store capturing student responses.

| Variable Name | SQL Data Type | Python / OpenAPI Type | Constraints & Range | Description |
|---|---|---|---|---|
| `id` | `uuid` | `UUID` | Primary Key, `gen_random_uuid()` | Unique identifier of the answer event record. |
| `attempt_id` | `uuid` | `UUID` | Foreign Key $\rightarrow$ `quiz_attempts.id` | Session identifier for the quiz attempt. |
| `question_id` | `uuid` | `UUID` | Foreign Key $\rightarrow$ `questions.id` | Target question item answered. |
| `selected_option_id` | `uuid` | `UUID` | Foreign Key $\rightarrow$ `question_options.id` | Option selected by the student. |
| `is_correct` | `boolean` | `bool` | `{true, false}`, NOT NULL | Evaluated correctness of the answer. |
| `response_time_seconds` | `numeric(6,2)` | `float` | $[0.00, 9999.99]$, NOT NULL | Time elapsed between question presentation and answer submission. |
| `attempt_number` | `integer` | `int` | $\ge 1$, DEFAULT 1 | Sequential attempt count for this question within the activity. |
| `idempotency_key` | `uuid` | `UUID` | UNIQUE, NOT NULL | Client-generated UUID preventing duplicate insertions. |
| `event_timestamp` | `timestamptz` | `datetime` | DEFAULT `now()`, NOT NULL | Exact UTC timestamp of answer submission. Used for temporal ordering. |

---

### 2.2 `predictions` (Retention Probability Logs)

Stores the output of probabilistic cognitive modeling across horizons.

| Variable Name | SQL Data Type | Python / OpenAPI Type | Constraints & Range | Description |
|---|---|---|---|---|
| `id` | `uuid` | `UUID` | Primary Key, `gen_random_uuid()` | Unique identifier of the prediction record. |
| `student_id` | `uuid` | `UUID` | Foreign Key $\rightarrow$ `profiles.id` | Student for whom prediction was computed. |
| `knowledge_component_id` | `uuid` | `UUID` | Foreign Key $\rightarrow$ `knowledge_components.id` | Knowledge Component evaluated. |
| `model_version_id` | `uuid` | `UUID` | Foreign Key $\rightarrow$ `model_versions.id` | Serialized model artifact version used for inference. |
| `prediction_horizon_hours` | `integer` | `int` | $\{24, 72, 168\}$ | Horizon $h$ for which recall probability is forecast. |
| `predicted_recall_probability` | `numeric(5,4)` | `float` | $[0.0000, 1.0000]$ | Inferred probability $P(R=1 \mid h)$. |
| `estimated_risk` | `numeric(5,4)` | `float` | $[0.0000, 1.0000]$ | Complementary forgetting risk ($1.0 - P(R=1)$). |
| `risk_level` | `risk_level_enum` | `str` | `{'low', 'medium', 'high', 'critical'}` | Categorical risk bucket based on probability thresholds. |
| `prediction_status` | `prediction_status_enum`| `str` | `{'valid', 'insufficient_history', 'degraded_fallback'}` | Inference execution quality status. |
| `created_at` | `timestamptz` | `datetime` | DEFAULT `now()` | UTC generation timestamp. |

---

### 2.3 `recommendations` (Pedagogical Decisions Audit Log)

Persists pedagogical decisions and algorithmic reasons for accountability.

| Variable Name | SQL Data Type | Python / OpenAPI Type | Constraints & Range | Description |
|---|---|---|---|---|
| `id` | `uuid` | `UUID` | Primary Key, `gen_random_uuid()` | Unique identifier of recommendation. |
| `student_id` | `uuid` | `UUID` | Foreign Key $\rightarrow$ `profiles.id` | Recipient student. |
| `knowledge_component_id` | `uuid` | `UUID` | Foreign Key $\rightarrow$ `knowledge_components.id` | Targeted KC. |
| `microcontent_id` | `uuid` | `UUID` | Foreign Key $\rightarrow$ `microcontents.id` | Recommended microcontent learning unit. |
| `selection_method` | `selection_method_enum` | `str` | `{'predictive_model', 'rule_based_fallback', 'teacher_assigned'}` | Mechanism that triggered the recommendation. |
| `recall_probability` | `numeric(5,4)` | `float` | $[0.0000, 1.0000]$, NULLABLE | Inferred recall probability used for triggering. |
| `threshold_used` | `numeric(5,4)` | `float` | $[0.0000, 1.0000]$ | Active decision threshold $\tau$ at execution time. |
| `decision_reason` | `text` | `str` | NOT NULL | Human-readable explanation of why recommendation was issued. |
| `status` | `varchar(30)` | `str` | `{'pending', 'assigned', 'dismissed', 'completed'}` | Recommendation lifecycle status. |
| `created_at` | `timestamptz` | `datetime` | DEFAULT `now()` | Timestamp of recommendation generation. |

---

## 3. Engineered Features for Cognitive Modeling (DAS3H & Baselines)

The following feature variables are dynamically extracted by the feature engineering pipeline (`ml/src/features/window_extractor.py` and `services/ml-api/prediction/features.py`):

| Feature Symbol | Feature Name | Computation Formula | Domain | Description |
|---|---|---|---|---|
| $s_{u,k,1}$ | `success_count_w1` | $\log(1 + \sum_{i \in W_1} \mathbb{I}(y_i = 1))$ | $[0, \infty)$ | Log-success count within last 1 hour ($[0, 3600)$ s). |
| $f_{u,k,1}$ | `failure_count_w1` | $\log(1 + \sum_{i \in W_1} \mathbb{I}(y_i = 0))$ | $[0, \infty)$ | Log-failure count within last 1 hour ($[0, 3600)$ s). |
| $s_{u,k,2}$ | `success_count_w2` | $\log(1 + \sum_{i \in W_2} \mathbb{I}(y_i = 1))$ | $[0, \infty)$ | Log-success count between 1 hour and 1 day ($[3600, 86400)$ s). |
| $f_{u,k,2}$ | `failure_count_w2` | $\log(1 + \sum_{i \in W_2} \mathbb{I}(y_i = 0))$ | $[0, \infty)$ | Log-failure count between 1 hour and 1 day ($[3600, 86400)$ s). |
| $s_{u,k,3}$ | `success_count_w3` | $\log(1 + \sum_{i \in W_3} \mathbb{I}(y_i = 1))$ | $[0, \infty)$ | Log-success count between 1 day and 7 days ($[86400, 604800)$ s). |
| $f_{u,k,3}$ | `failure_count_w3` | $\log(1 + \sum_{i \in W_3} \mathbb{I}(y_i = 0))$ | $[0, \infty)$ | Log-failure count between 1 day and 7 days ($[86400, 604800)$ s). |
| $s_{u,k,4}$ | `success_count_w4` | $\log(1 + \sum_{i \in W_4} \mathbb{I}(y_i = 1))$ | $[0, \infty)$ | Log-success count between 7 days and 30 days ($[604800, 2592000)$ s). |
| $f_{u,k,4}$ | `failure_count_w4` | $\log(1 + \sum_{i \in W_4} \mathbb{I}(y_i = 0))$ | $[0, \infty)$ | Log-failure count between 7 days and 30 days ($[604800, 2592000)$ s). |
| $s_{u,k,5}$ | `success_count_w5` | $\log(1 + \sum_{i \in W_5} \mathbb{I}(y_i = 1))$ | $[0, \infty)$ | Log-success count older than 30 days ($[2592000, \infty)$ s). |
| $f_{u,k,5}$ | `failure_count_w5` | $\log(1 + \sum_{i \in W_5} \mathbb{I}(y_i = 0))$ | $[0, \infty)$ | Log-failure count older than 30 days ($[2592000, \infty)$ s). |
| $\Delta t$ | `inter_practice_interval_hours` | $(t_{\text{current}} - t_{\text{last\_interaction}}) / 3600.0$ | $[0, \infty)$ | Elapsed hours since student's prior interaction on target KC. |
| $\beta_i$ | `item_difficulty_prior` | Stored in `questions.difficulty` | $[0.0, 1.0]$ | Calibrated prior item difficulty from pilot bank. |
| $\bar{T}_{u,k}$ | `avg_response_time_kc` | Mean response time on KC $k$ | $[0.0, 9999.0]$ | Indicator of student automaticity or hesitation. |

---

## 4. Research Export View Schema (`view_research_interaction_logs`)

The formal SQL view definition exposing completely pseudonymized datasets for thesis validation:

```sql
CREATE OR REPLACE VIEW public.view_research_interaction_logs AS
SELECT
    e.student_id_pseudo,
    e.section_id,
    c.id AS course_id,
    q.knowledge_component_id,
    q.id AS question_id,
    q.difficulty AS question_difficulty_prior,
    act.activity_type,
    ae.is_correct,
    ae.response_time_seconds,
    ae.attempt_number,
    ae.event_timestamp
FROM public.answer_events ae
JOIN public.quiz_attempts qa ON ae.attempt_id = qa.id
JOIN public.activities act ON qa.activity_id = act.id
JOIN public.sections s ON act.section_id = s.id
JOIN public.courses c ON s.course_id = c.id
JOIN public.enrollments e ON e.student_id = qa.student_id AND e.section_id = s.id
JOIN public.questions q ON ae.question_id = q.id;
```

This view strips all references to `profiles.id`, real names, emails, and student identity, enabling lawful processing under Peru's Ley N° 29733.
