# ADR-0002: Service Separation, Cold-Start Mitigation & ML Model Selection (DAS3H / CatBoost / BKT / DKT)

- **Status:** ACCEPTED
- **Date:** 2026-11-01
- **Deciders:** Lead Architect, Machine Learning Specialist, Antigravity AI Orchestrator
- **Technical Domain:** Container Hosting, Cold-Start Resilience, Machine Learning Architecture, Knowledge Tracing
- **Consulted:** Backend Specialist, Adaptive Learning Specialist, Research Auditor

---

## 1. Context and Problem Statement

The platform requires real-time probabilistic inference of student memory retention and forgetting dynamics across multiple temporal horizons ($h \in \{24, 72, 168\}$ hours). Implementing this capability presents three acute structural tensions:

### 1.1 Infrastructure & Hosting Constraints (blitz.cloud Cold Start)
The predictive microservice (`services/ml-api/`) is hosted as a Docker container (`linux/amd64`) on blitz.cloud container infrastructure. Under cost-constrained or free-tier resource allocations:
- Containers are suspended into an idle sleep state after 15 minutes of zero inbound traffic.
- Initial container re-activation (cold start) requires between 10 and 25 seconds to provision resources, load the Python 3.11 runtime, initialize FastAPI, load ML model artifacts into memory, and establish database connection pools via asyncpg.

### 1.2 School Classroom Concurrency Dynamics
In real secondary school environments in Peru, class sessions operate in discrete synchronous blocks:
- A cohort of approximately 30 students in a classroom laboratory enters the platform simultaneously at the beginning of a 45-to-90 minute class session, following hours or days of platform inactivity.
- If 30 concurrent HTTP requests hit a sleeping blitz.cloud instance simultaneously, connection queues overflow, resulting in cascading gateway timeouts (HTTP 504), stalled classroom activities, and severe disruption to pedagogical momentum.

### 1.3 Sample Size vs. Model Complexity ($N \approx 66$ Students)
The pilot educational quasi-experimental study involves approximately 66 students (distributed across two sections of 5th-year secondary students: one control group and one experimental group).
- Deep Knowledge Tracing (DKT / RNN / Transformer-based architectures) typically require tens of thousands of student interactions across hundreds of learners to avoid catastrophic overfitting and parameter divergence.
- Training complex models purely on local cold-start interactions risks uncalibrated, erratic probabilities that would compromise both student learning outcomes and scientific thesis validity.

---

## 2. Decision Outcome

We decided to adopt a three-pillar architecture addressing service separation, cold-start resilience, and model selection governance:

### Pillar 1: Multi-Layered Cold-Start Mitigation Architecture

1. **Pre-Session Warmup Ping (`POST /api/v1/health/warmup`):**
   - An automated background cron job or a teacher pre-flight trigger executes an authenticated warmup ping 10 minutes prior to scheduled school class hours.
   - The warmup endpoint pre-loads serialized model artifacts into Python memory, initializes the asyncpg connection pool, executes a dummy feature extraction pass, and confirms readiness with status code 200.

2. **Progressive Non-Blocking UI Loading States:**
   - The Next.js frontend (`apps/web/`) implements non-blocking optimistic UI flows.
   - When communicating with the predictive service during a cold start, the UI informs the student with empathetic, transparent feedback: *"Inicializando motor pedagógico..."* while preserving interactive local state.

3. **Circuit Breaker with Deterministic Rule-Based Fallback (`rule_based_fallback`):**
   - A strict 5.0-second timeout threshold is enforced on all predictive API calls from the web client and server actions.
   - If the predictive API exceeds 5.0 seconds, returns an HTTP error, or indicates `insufficient_history` (e.g., student has fewer than 3 interactions on the target KC), the system gracefully degrades to a deterministic rule-based policy:
     - Fallback Rule 1: Accuracy on last 3 KC attempts $< 60\%$ $\rightarrow$ schedule review within 24 hours.
     - Fallback Rule 2: Elapsed time since last KC practice $> 5$ days $\rightarrow$ schedule review within 72 hours.
     - Fallback Rule 3: Diagnostic attempt with incorrect answer $\rightarrow$ immediate reinforcement recommendation.
   - The `recommendations` table explicitly records `selection_method = 'rule_based_fallback'` and logs `decision_reason` for complete auditability.

```text
[Student Interaction]
         │
         ▼
[Next.js Server Action / Client]
         │
         ├─── (Timeout <= 5.0s) ───► [FastAPI /predictions/retention]
         │                                    │
         │                         (Status: valid)
         │                                    ▼
         │                         [DAS3H Predictive Inference]
         │                                    │
         └─── (Timeout > 5.0s / Error / ────► [Deterministic Rule-Based Fallback]
               insufficient_history)          (Accuracy < 60% / Time > 5 days)
```

### Pillar 2: Hierarchical Model Selection & Rigorous Promotion Protocol

We establish a formal model evaluation hierarchy based on the abstract contract `BaseRetentionModel(ABC)`:

1. **Baseline 1 — Temporal Logistic Regression / Extended Performance Factor Analysis (PFA):**
   - Models recall probability as a function of cumulative successes ($S$), cumulative failures ($F$), and log-transformed recency intervals ($R$).
   - Extremely robust against small sample sizes ($N \approx 66$); acts as the primary operational baseline during the initial diagnostic and learning phase.

2. **Baseline 2 — Modified Bayesian Knowledge Tracing (BKT):**
   - Discrete two-state Hidden Markov Model estimating mastery probability $P(L_t)$ with slip ($s$) and guess ($g$) parameters, augmented with an exponential forgetting decay parameter between sessions.

3. **Baseline 3 — Gradient Boosted Decision Trees (CatBoost):**
   - Utilized for tabular student risk classification using aggregate feature representations (average response time, global error rates, interaction frequency).

4. **Target Model — DAS3H (Difficulty, Ability, Student, Student-Skill, Recency/Frequency across Log-Windows):**
   - Primary candidate for production memory modeling.
   - Formulation:
     $$\text{logit}(P(R=1)) = \alpha_u - \beta_i + \sum_{k \in KC(i)} \left( \gamma_k + \sum_{w=1}^W \left( \theta_{k,w} s_{u,k,w} + \tau_{k,w} f_{u,k,w} \right) \right)$$
   - Captures power-law forgetting dynamics across log-spaced time windows:
     $$W_1 \in [0, 1\text{h}], \quad W_2 \in [1\text{h}, 1\text{d}], \quad W_3 \in [1\text{d}, 7\text{d}], \quad W_4 \in [7\text{d}, 30\text{d}], \quad W_5 \in [30\text{d}, \infty)$$

5. **Promotion Criterion (Non-Negotiable):**
   - The target model (DAS3H or any subsequent architecture) is promoted to production **only** if it demonstrates statistically superior performance over the temporal logistic baseline (PFA) and BKT across **both**:
     - **Discrimination:** Area Under the ROC Curve ($\Delta\text{AUC-ROC} \ge +0.02$).
     - **Calibration:** Lower Brier Score ($Brier < Brier_{\text{baseline}}$) and Expected Calibration Error ($\text{ECE} \le 0.08$).
   - If DAS3H fails to beat the baseline under the pilot sample size, the platform remains on the calibrated temporal logistic baseline without interruption.

6. **Pre-Training & Transfer Learning Strategy:**
   - To mitigate cold start on $N \approx 66$ local students, feature extractors and initial item difficulties are pre-trained or initialized using benchmark open educational datasets (e.g., ASSISTments, Duolingo SLAM), fine-tuning local student parameters ($\alpha_u$) via Bayesian ridge shrinkage.

### Pillar 3: Frozen Artifact Packaging and Versioning

1. **Physical Isolation:** Mass model training, cross-validation, and dataset curation reside exclusively in `ml/`. Mass training never executes within the FastAPI web process.
2. **Metadata Contract (`metadata.json`):** Every serialized artifact in `ml/artifacts/<model_name>/<version>/` must include a strict `metadata.json`:
   - `model_name`: String identifier (e.g. `das3h_sci_pilot`).
   - `model_version`: Semantic version (e.g. `1.0.0`).
   - `training_timestamp`: ISO 8601 UTC timestamp.
   - `git_commit_sha`: Git commit hash of training source code.
   - `hyperparameters`: Complete dictionary of tuned parameters.
   - `metrics`: Cross-validation scores (AUC-ROC, Brier score, ECE).
   - `dependency_versions`: Exact pinned versions of `scikit-learn`, `numpy`, and `pandas`.
3. **Runtime Ingestion:** FastAPI loads the frozen artifact at container startup and validates dependency hash compatibility before accepting inference traffic.

---

## 3. Consequences and Trade-offs

### Positive Consequences

- **Classroom Reliability:** The 5.0s circuit breaker and rule-based fallback guarantee that secondary school students never experience stalled classroom sessions due to blitz.cloud cold starts.
- **Scientific Defense Against Overfitting:** The baseline promotion gate prevents uncalibrated deep models from distorting student review recommendations.
- **Reproducibility:** Versioned artifacts with immutable `metadata.json` ensure that every prediction stored in `predictions` can be traced to the exact model version and commit.

### Negative Consequences and Mitigations

- **Dual Policy Maintenance:** Engineering teams must maintain both the ML inference code and the deterministic rule-based fallback logic.
  - *Mitigation:* The `BaseRetentionModel` abstraction and `AdaptationPolicy` encapsulate fallback triggers cleanly, sharing the same response schemas.
- **Warmup Schedule Dependency:** Automated warmup requires a cron trigger or teacher action before class.
  - *Mitigation:* The teacher dashboard includes a 1-click session pre-flight check that triggers `POST /api/v1/health/warmup` upon teacher login.

---

## 4. Compliance Notes

- **Audit Trail Traceability:** In compliance with the Master Plan Section 5 (Critical Issue 3), all recommendations produced during cold starts or fallback states are explicitly tagged with `selection_method = 'rule_based_fallback'`.
- **Integrity Mandate:** Simulated or hardcoded ML metrics are strictly prohibited. Model performance must be computed via real cross-validation scripts in `ml/src/evaluation/`.
