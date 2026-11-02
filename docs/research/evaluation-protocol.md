# Research & Evaluation Protocol
## Protocolo Experimental de Validación Pedagógica y Evaluación de Modelos Cognitivos

**Project:** Plataforma de Microaprendizaje Adaptativo (5to Secundaria)  
**Study Design:** Quasi-Experimental Pretest-Posttest Design with Control and Experimental Groups  
**Primary Endpoint:** 7-Day Delayed Retention Post-Test ($h = 168$ hours)  
**Legal Framework:** Ley N° 29733 (Ley de Protección de Datos Personales - Perú)  
**Status:** Approved / Base Research Protocol  
**Date:** 2026-11-01  
**Version:** 1.0.0  

---

## 1. Scientific Study Design & Experimental Methodology

### 1.1 Research Objective and Hypotheses
The primary objective of this empirical study is to evaluate whether an adaptive microlearning platform that models forgetting dynamics and schedules spaced Knowledge Component (KC) micro-reviews significantly improves long-term memory retention in 5th-year secondary school students compared to traditional non-adaptive review practices.

- **Null Hypothesis ($H_0$):** There is no statistically significant difference in 7-day delayed post-test scores between students receiving model-driven adaptive microlearning reviews and students receiving standard non-adaptive review materials ($p \ge 0.05$).
- **Alternative Hypothesis ($H_1$):** Students receiving model-driven adaptive microlearning reviews achieve statistically significantly higher 7-day delayed post-test scores than students in the control group ($p < 0.05$), with a standardized effect size (Cohen's $d$) $\ge 0.40$.

### 1.2 Study Design: Quasi-Experimental Control vs. Experimental Group
Because secondary school students are assigned to pre-existing academic sections within the educational institution, random individual assignment is impossible without disrupting school operations. Therefore, the research adopts a **Quasi-Experimental Design with Nonequivalent Groups**:
- **Target Population:** Secondary school students in 5th year of secondary education (aged 16–17 years) at the pilot school in Peru.
- **Sample Distribution ($N \approx 66$ students):**
  - **Experimental Group ($n_e \approx 33$ students):** Utilizes the adaptive microlearning platform. Formative interactions trigger predictive retention modeling ($P(R=1 \mid h)$), and when risk exceeds threshold $\tau$, the system automatically schedules spaced microcontent reviews and targeted exercises.
  - **Control Group ($n_c \approx 33$ students):** Utilizes the same digital curriculum and question bank on the platform, but receives static, massed, or linear review assignments scheduled on fixed calendar intervals without probabilistic adaptation.

### 1.3 Experimental Timeline and Intervention Protocol
The experimental intervention follows a structured 4-phase timeline:

```text
Day 1: Pre-Test / Diagnostic Assessment (All Students, N ≈ 66)
       │
       ▼
Days 2–4: Formative Microlearning Intervention
       ├─ Experimental Group: Adaptive Spaced Reviews (DAS3H / PFA triggered)
       └─ Control Group: Static Linear Review Materials
       │
Day 5: Immediate Post-Test (h = 0 hours post-intervention)
       │
Days 5–11: Quarantine Period (7 days = 168 hours)
       │  (Strict quarantine: zero review exercises on delayed post-test items)
       ▼
Day 12: Delayed Post-Test (h = 168 hours / 7 days post-intervention)
```

1. **Pre-Test / Diagnostic Assessment (Day 1):** Establishes baseline knowledge mastery across all designated Knowledge Components (KCs) for both groups.
2. **Formative Learning & Review Phase (Days 2–4):** Both groups engage with microcontents. The experimental group receives adaptive review assignments triggered by the `AdaptationPolicy`.
3. **Immediate Post-Test (Day 5):** Measures short-term acquisition immediately following content completion.
4. **Quarantine Interval (Days 5–11 / $h = 168$ hours):** A strict 7-day latency window where no reviews or exercises containing delayed post-test items are administered to either group.
5. **Delayed Post-Test (Day 12):** Measures long-term memory retention. This serves as the primary scientific endpoint for testing $H_1$.

---

## 2. Evaluation Metrics and Statistical Formulation

Model evaluation requires assessing two distinct statistical qualities: **discrimination** (can the model distinguish between recall and forgetting?) and **calibration** (does the predicted probability match the observed empirical frequency?).

### 2.1 Discrimination Metrics

1. **Area Under the Receiver Operating Characteristic Curve (AUC-ROC):**
   Measures the ranking capability of the model across all classification thresholds:
   $$\text{AUC-ROC} = \int_{0}^{1} \text{TPR}(\text{FPR}^{-1}(t)) \, dt$$
   - *Target Benchmark:* $\text{AUC-ROC} \ge 0.72$ on unseen student folds.
   - *Interpretation:* An AUC of 0.50 denotes random guessing; values above 0.70 demonstrate acceptable educational discrimination.

2. **Precision, Recall, and F1-Score:**
   Evaluated at the calibrated operational threshold $\tau$:
   $$\text{Precision} = \frac{\text{TP}}{\text{TP} + \text{FP}}, \quad \text{Recall} = \frac{\text{TP}}{\text{TP} + \text{FN}}, \quad F_1 = 2 \cdot \frac{\text{Precision} \cdot \text{Recall}}{\text{Precision} + \text{Recall}}$$
   - High recall ensures students at risk of forgetting are rarely missed (minimizing false negatives).

### 2.2 Calibration Metrics

Probabilistic memory models must be well-calibrated because predicted probabilities $P(R=1)$ directly govern the timing of spaced reviews.

1. **Brier Score:**
   The mean squared error of probabilistic forecasts:
   $$\text{Brier} = \frac{1}{N} \sum_{i=1}^{N} (p_i - y_i)^2$$
   where $p_i \in [0, 1]$ is the predicted recall probability and $y_i \in \{0, 1\}$ is the observed outcome.
   - *Target Benchmark:* $\text{Brier} \le 0.18$. A lower score indicates superior probabilistic accuracy.

2. **Expected Calibration Error (ECE):**
   Groups predictions into $M = 10$ equally spaced confidence bins $B_m \subset (0, 1]$ and computes the weighted absolute difference between average confidence and empirical accuracy:
   $$\text{ECE} = \sum_{m=1}^{M} \frac{|B_m|}{N} \left| \text{acc}(B_m) - \text{conf}(B_m) \right|$$
   where:
   $$\text{acc}(B_m) = \frac{1}{|B_m|} \sum_{i \in B_m} y_i, \quad \text{conf}(B_m) = \frac{1}{|B_m|} \sum_{i \in B_m} p_i$$
   - *Target Benchmark:* $\text{ECE} \le 0.08$. Values above $0.15$ indicate severe over- or under-confidence.

3. **Reliability Diagrams:**
   Visual plot of $\text{conf}(B_m)$ vs $\text{acc}(B_m)$ against the ideal $45^\circ$ diagonal. Plotted using `ml/src/evaluation/calibration.py`.

### 2.3 Operational Latency Metrics
- Ingestion Latency ($p_{50} \le 100$ ms, $p_{95} \le 300$ ms) for answer event recording.
- Inference Latency ($p_{50} \le 500$ ms, $p_{95} \le 1500$ ms) for probability estimation.
- Fallback Trigger Rate ($< 1\%$ of requests under normal operation; triggers at $\ge 5000$ ms).

---

## 3. Data Splitting & Cross-Validation Methodology

To guarantee scientific reproducibility and prevent data leakage, model validation strictly adheres to two structural constraints:

```text
Fold 1: [Students 1-13: Validation] | [Students 14-66: Training]
Fold 2: [Students 14-26: Validation] | [Students 1-13, 27-66: Training]
Fold 3: [Students 27-39: Validation] | [Students 1-26, 40-66: Training]
Fold 4: [Students 40-52: Validation] | [Students 1-39, 53-66: Training]
Fold 5: [Students 53-66: Validation] | [Students 1-52: Training]

* Within every fold, for each event at timestamp t:
  Training features extracted ONLY from interactions with event_timestamp < t.
```

### 3.1 Student-Stratified Group-K-Fold ($K = 5$)
- **Zero Student Leakage:** In educational knowledge tracing, random row splitting causes severe data leakage because interactions from the same student appear in both training and test sets.
- **Grouping Rule:** Splitting is strictly grouped by `student_id_pseudo`. All interactions belonging to student $u$ are exclusively assigned to either the training split or the validation split in each fold.
- **Stratification:** Folds are stratified by the student's baseline performance on the pre-test (categorized into low, medium, and high baseline mastery tiers), ensuring balanced ability distributions across all 5 folds.

### 3.2 Strict Temporal Cutoff Filtering (No Lookahead Leakage)
- For every prediction target at timestamp $t_{\text{target}}$, the feature extraction pipeline strictly queries:
  ```sql
  WHERE event_timestamp < t_target
  ```
- Any interaction occurring at $t \ge t_{\text{target}}$ is cryptographically masked from the feature extractor, preventing future information from leaking into the input vector.

---

## 4. Baseline Models & Model Evaluation Hierarchy

Every complex predictive model candidate must compete against established baselines before promotion to production inference:

| Model Tier | Architecture | Strengths | Weaknesses | Promotion Condition |
|---|---|---|---|---|
| **Baseline 1** | Temporal Logistic Regression / Extended PFA | Simple, highly interpretable, convex optimization, zero overfitting risk on $N \approx 66$. | Linear assumption; cannot capture complex multi-window non-linear decay interactions. | Production default for cold start. |
| **Baseline 2** | Modified Bayesian Knowledge Tracing (BKT) | Formal Hidden Markov Model; models latent knowledge state $P(L_t)$, slip, guess, and transition. | Binary latent state; treats forgetting as fixed exponential decay without item-specific spacing. | Evaluated as classical cognitive benchmark. |
| **Baseline 3** | CatBoost GBDT | Robust on tabular summary features; handles non-linear interactions and categorical student features. | Does not natively model temporal sequencing or continuous forgetting curves. | Evaluated for static risk classification. |
| **Target Candidate** | DAS3H | Models item difficulty ($\beta_i$), student ability ($\alpha_u$), skill mastery ($\gamma_k$), and power-law recency across log windows. | Requires sufficient interactions per parameter to avoid overfitting on small samples. | **Must beat Baseline 1 & 2** in both AUC ($\Delta \ge +0.02$) and Brier score. |

---

## 5. The 5 Critical Issues & Risk Matrix (Master Plan Section 5)

The table below synthesizes the 5 critical structural risks identified in Section 5 of the Master Plan, detailing technical impacts, empirical mitigations, and formal resolutions:

| # | Critical Issue | Category | Technical / Methodological Impact | Action & Mitigation Protocol |
|---|---|---|---|---|
| **1** | **Sample Size vs. ML Complexity** | Methodological / ML | The pilot sample size ($N \approx 66$ students) is limited. Advanced models like DAS3H or neural DKT risk severe overfitting or non-convergence when trained from scratch on local data. | **Transfer Learning & Baseline Prioritization:** Pre-train feature extractors and item difficulty priors on open benchmark datasets (e.g., ASSISTments, Duolingo SLAM). Deploy the calibrated temporal logistic baseline (PFA) during initial diagnostic and learning phases. Promote DAS3H only when local interaction volume satisfies convergence criteria. |
| **2** | **Contradiction: Adaptation Policy vs. Experimental Protocol** | Methodological / Validity | The adaptation policy seeks to schedule reviews whenever retention risk is high. If the recommendation engine selects questions reserved for the 7-day delayed post-test during intermediate days, it contaminates the dependent variable of the thesis. | **Delayed Assessment Item Quarantine:** Strict database and query isolation. All questions tagged with `activity_type_enum = 'delayed_assessment'` are quarantined from formative practice pools, diagnostic assessments, and adaptive recommendation engines. Zero overlap between practice items and post-test items. |
| **3** | **Cold Start of blitz.cloud vs. Classroom Concurrency** | Infrastructure / Operations | blitz.cloud free-tier instances sleep after 15 min of inactivity. In a school lab, 30 students log in simultaneously at the bell, causing 10–25s cold starts, request collisions, and gateway timeouts. | **Warmup Ping & Circuit Breaker Fallback:** Scheduled warmup ping (`POST /api/v1/health/warmup`) triggered 10 minutes prior to classes. Next.js frontend implements optimistic loading states. Circuit breaker at 5.0 seconds automatically routes to deterministic rule-based fallback (`rule_based_fallback`), guaranteeing zero classroom stalls. |
| **4** | **Uncalibrated Review Trigger Thresholds ($\tau$)** | Pedagogical / Incomplete Req | The SRS specifies an adaptive review trigger threshold $\tau$, but an arbitrary hardcoded threshold risks review fatigue (if too high) or under-intervention (if too low). | **Configurable Parameterization & ROC Calibration:** Parameterize $\tau$ as an environment variable and database setting (`DEFAULT_RISK_THRESHOLD = 0.65`). Calibrate $\tau$ empirically by optimizing Youden's $J$ statistic ($J = \text{Sensitivity} + \text{Specificity} - 1$) on the validation ROC curve from cross-validation. |
| **5** | **Data Privacy & Minor Protection (Ley N° 29733)** | Ethical / Legal | The platform serves minors (16–17 years old) in Peru. Processing student data without legal guardian consent or exposing PII in research datasets violates Peruvian Law N° 29733, risking legal nullity of the study. | **Persistent Pseudonymization & Informed Consent:** Disassociate personal identifiers (`profiles.id`, real names, emails) from research logs using immutable `student_id_pseudo`. Gather institutional parental informed consent forms. Research exports expose only anonymized tokens. |

---

## 6. Ethical AI, Informed Consent & Pedagogical Interaction Standards

### 6.1 Regulatory Compliance under Peruvian Law N° 29733
In accordance with Peru's Personal Data Protection Law (Ley N° 29733) and its regulatory decree (Decreto Supremo N° 003-2013-JUS):
1. **Consent Protocol:** Prior to onboarding, school authorities and legal guardians (parents/tutors) sign physical or digitally verified informed consent agreements detailing:
   - Educational purpose of the platform.
   - Types of interaction logs recorded (answer correctness, response timestamps).
   - Voluntary participation and right to revoke consent without academic penalty.
2. **Right to Revocation & Erasure:** In the event of consent revocation, the student's personal profile is permanently severed from analytical interaction logs.

### 6.2 Empathetic Feedback Standards
Adolescent students in secondary education (16–17 years old) are highly sensitive to negative educational framing, which can induce math/science anxiety or disengagement:
- **Prohibited Terminology:** The student UI shall never display negative, deficit-based, or anxiety-inducing messages such as:
  - *"Estás a punto de fallar este tema"* (You are about to fail this topic).
  - *"Alto riesgo de olvido detectado"* (High forgetting risk detected).
  - *"Tu retención es deficiente"* (Your retention is deficient).
- **Approved Pedagogical Phrasing:** The UI shall exclusively employ growth-mindset, constructive messaging:
  - *"Momento ideal para repasar este concepto"* (Ideal moment to review this concept).
  - *"Refuerzo sugerido para consolidar tu aprendizaje"* (Suggested reinforcement to consolidate your learning).
  - *"¡Gran progreso! Consolidemos lo aprendido con un microrepaso de 3 minutos"* (Great progress! Let's consolidate what you've learned with a 3-minute micro-review).

### 6.3 Algorithmic Transparency and Audit Trail
To protect scientific integrity:
- Every adaptive recommendation generated by the system persists its full algorithmic provenance in the `recommendations` table:
  - `model_version`: Exact semantic version and git commit hash of the model artifact.
  - `selection_method`: Identifies whether recommendation was generated by `'predictive_model'` or `'rule_based_fallback'`.
  - `recall_probability`: The exact calculated probability vector.
  - `threshold_used`: Numerical value of $\tau$ at execution time.
  - `decision_reason`: Detailed textual explanation of why the recommendation was generated.
- This ensures that researchers can reconstruct, audit, and explain any pedagogical decision rendered by the platform.
