# ADR-0003: Supabase PostgreSQL with Native RLS vs Managed Multitenant DB & Probabilistic Adaptation Boundary

- **Status:** ACCEPTED
- **Date:** 2026-11-01
- **Deciders:** Lead Architect, Data Protection Officer, Antigravity AI Orchestrator
- **Technical Domain:** Database Multitenancy, Row Level Security, Pedagogical Adaptation Boundary, Research Ethics, Minor Data Privacy
- **Consulted:** Database Specialist, Adaptive Learning Specialist, Security Auditor, Research Ethics Committee

---

## 1. Context and Problem Statement

The platform is deployed in secondary educational institutions serving adolescent students aged 16–17 years old. Two critical systemic challenges must be resolved at the fundamental architectural level:

### 1.1 Multitenancy and Minor Data Governance under Peruvian Law N° 29733
The platform handles personal, academic, and behavioral interaction data of minors under the jurisdiction of Peru's Personal Data Protection Law (Ley N° 29733) and its Regulation (D.S. 003-2013-JUS):
- Strict multitenant isolation must be maintained across different educational institutions, courses, sections, and roles (`student`, `teacher`, `researcher`, `system_worker`).
- Student interaction logs (`answer_events`) constitute the empirical foundation of the scientific thesis. Any accidental or malicious modification, deletion, or tampering would invalidate the research findings.
- Analytical research exports and thesis publications must guarantee absolute anonymity without exposing real student names, national identity documents (DNI), or school identifiers.

### 1.2 Conflation of Predictive Inference and Pedagogical Decision-Making
In educational technology, a frequent design anti-pattern is directly coupling machine learning model outputs to user actions:
- A raw prediction $P(R=1 \mid h = 168) = 0.52$ is purely an estimated statistical probability of memory recall after 7 days; it is **not** an educational mandate.
- Prescriptive educational actions require pedagogical domain policies: anti-fatigue frequency capping (preventing student cognitive overload), minimum inter-practice rest intervals, content chunking, and deterministic fallbacks.
- If pedagogical logic is embedded inside ML inference code, adjusting educational thresholds requires retraining or redeploying models. Conversely, if ML inference is scattered in UI code, scientific reproducibility is lost.

### 1.3 Threat of Experimental Contamination (Quasi-Experimental 7-Day Assessment)
The scientific thesis investigates memory retention via a quasi-experimental design with a 7-day delayed post-test ($h = 168$ hours):
- If the adaptive recommendation engine selects questions reserved for the 7-day post-test during intermediate formative practice on days 3 or 5, students encounter the exact test items beforehand (practice effect / test leakage), destroying experimental validity.

---

## 2. Decision Outcome

We decided to adopt **Supabase PostgreSQL with Native Row Level Security (RLS)** as the authoritative single source of persistence and enforce a **strict boundary between the Prediction Engine and the Adaptation Policy**:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        SUPABASE POSTGRESQL 15+                         │
│  - Native Row Level Security (RLS) on 100% of tables                   │
│  - Append-Only answer_events (REVOKE UPDATE, DELETE)                   │
│  - Immutable student_id_pseudo for research exports                    │
└────────────────────────────────────────────────────────────────────────┘
                               ▲
                               │
            ┌──────────────────┴──────────────────┐
            │                                     │
┌───────────────────────┐             ┌───────────────────────┐
│   PREDICTION ENGINE   │             │   ADAPTATION POLICY   │
│  (services/ml-api)    │             │  (services/ml-api)    │
│                       │             │                       │
│ - Pure Math / Stats   │   Recall    │ - Pedagogical Domain  │
│ - Feature Extraction  ├────────────►│ - Threshold tau = 0.65│
│ - P(R=1 | h) Vector   │ Probability │ - Anti-fatigue Capping│
│ - Risk Classification │             │ - Spaced Scheduling   │
│ - Status: valid /     │             │ - Delayed Quarantine  │
│   insufficient_history│             │ - Fallback Execution  │
└───────────────────────┘             └───────────────────────┘
```

### Pillar 1: Native Row Level Security (RLS) & Append-Only Event Store

1. **Native PostgreSQL RLS vs Managed Application-Layer Filtering:**
   - Instead of relying on application-level `WHERE school_id = ...` clauses (which are vulnerable to developer oversight), PostgreSQL enforces data isolation at the engine level for every query.
   - All RLS policies utilize optimized scalar subqueries `(SELECT auth.uid())` to enable PostgreSQL query planner caching, avoiding per-row function re-execution.

2. **Strict Immutability on Interaction Logs (`answer_events`):**
   - The `answer_events` table is append-only.
   - Database migrations explicitly execute:
     ```sql
     REVOKE UPDATE, DELETE ON TABLE public.answer_events FROM anon, authenticated;
     ```
   - No user (student, teacher, or researcher) possesses privileges to modify historical marks, response times, or correctness indicators.

3. **Persistent Anonymization via `student_id_pseudo`:**
   - In `enrollments`, each student enrollment automatically generates an immutable pseudo-random UUID:
     ```sql
     student_id_pseudo uuid DEFAULT gen_random_uuid() NOT NULL
     ```
   - Direct linkages between personal identity (`profiles.id`, real names, emails) and learning interactions are decoupled in research export views. Data science exports exclusively expose `student_id_pseudo`.

### Pillar 2: Strict Boundary between Prediction Engine and Adaptation Policy

1. **Decoupled Architecture:**
   - **`PredictionEngine` (Inference Domain):**
     - Consumes historical interaction vectors for a given student and Knowledge Component.
     - Computes the estimated retention probability vector:
       $$\vec{P} = [P(R=1 \mid h=24), P(R=1 \mid h=72), P(R=1 \mid h=168)]$$
     - Categorizes statistical risk: `low` ($\ge 0.75$), `medium` ($[0.60, 0.75)$), `high` ($[0.45, 0.60)$), `critical` ($< 0.45$).
     - Does not make pedagogical sequencing or content delivery decisions.
   - **`AdaptationPolicy` (Pedagogical Decision Domain):**
     - Evaluates predicted probabilities against the parameterized review threshold $\tau$ (default: `DEFAULT_RISK_THRESHOLD = 0.65`).
     - Applies cognitive load and anti-fatigue rules:
       - **Anti-Fatigue Frequency Cap:** Maximum of 3 adaptive review assignments per student per calendar day.
       - **Spacing Window:** Minimum inter-review interval of 4 hours for the same KC to prevent massed cramming.
       - **Microcontent Matcher:** Selects appropriate microcontent type (`text_summary`, `infographic_card`, `concept_map`) according to error pattern and cognitive complexity.
     - Dispatches review tasks to `review_assignments` with explicit completion due dates.

2. **Algorithmic Audit Trail:**
   - Every entry in `recommendations` and `predictions` records complete algorithmic provenance:
     - `model_version`: Identifier of model artifact used.
     - `selection_method`: `'predictive_model'` vs `'rule_based_fallback'`.
     - `threshold_used`: Numerical value of $\tau$ at the moment of decision.
     - `decision_reason`: Human-readable and auditable explanation (e.g., *"Recall probability at 72h (0.54) fell below threshold tau (0.65)"*).

### Pillar 3: Experimental Quarantine Protocol for Delayed Assessment Items

1. **Item Quarantine in Database:**
   - Questions associated with `activity_type_enum = 'delayed_assessment'` are formally quarantined.
   - Database queries in `AdaptationPolicy` and microcontent recommendation generators strictly filter:
     ```sql
     WHERE activity_type != 'delayed_assessment'
     ```
   - This cryptographic and query-level isolation guarantees that students never encounter delayed post-test questions during formative practice, preserving the scientific integrity of the 7-day quasi-experimental evaluation.

---

## 3. Consequences and Trade-offs

### Positive Consequences

- **Legal Compliance:** Complies fully with Peruvian Law N° 29733 regarding protection of minors' personal data and parental informed consent mandates.
- **Scientific Auditability:** Researchers can reproduce every recommendation by inspecting `predictions`, `recommendations`, and `model_versions` without ambiguity.
- **Architectural Flexibility:** Pedagogical adaptation rules (thresholds, frequency caps, spacing intervals) can be refined without retraining or modifying machine learning models.
- **Zero Experimental Leakage:** Strict quarantine of delayed assessment items protects the thesis endpoint from internal validity threats.

### Negative Consequences and Mitigations

- **Query Complexity in RLS:** Complex subqueries in RLS policies can introduce latency if unindexed.
  - *Mitigation:* Composite indexes created on all tenant, section, and enrollment lookup columns (`idx_enrollments_student_section`, `idx_answer_events_student_kc`).
- **Data Synchronization in Exports:** Maintaining pseudo-random UUIDs requires consistent analytical view pipelines.
  - *Mitigation:* Predefined database views (`view_research_interaction_logs`) expose strictly pseudonymized columns.

---

## 4. Compliance Notes

- **Peruvian Law N° 29733 (Ley de Protección de Datos Personales):** Enforced via `student_id_pseudo` disassociation, database role isolation, and parental consent audit trails.
- **PostgreSQL 15+ Security Best Practices:** Enforced via scalar subquery RLS, explicit permission revocations, and append-only constraints.
