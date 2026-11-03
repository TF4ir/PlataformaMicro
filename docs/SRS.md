# System Requirements Specification (SRS)
## Plataforma de Microaprendizaje Adaptativo para 5to Año de Secundaria

**Standard:** IEEE 830-1998 / ISO/IEC/IEEE 29148:2018 Compliant  
**Project:** Plataforma de Microaprendizaje Adaptativo  
**Target Population:** 5th Year Secondary Students (16–17 years old) in Peru  
**Initial Pilot Subject:** Ciencias (Science) — Subject-Agnostic Architecture  
**Status:** Approved / Base Architecture Document  
**Date:** 2026-11-01  
**Version:** 1.0.0  

---

## 1. Introduction

### 1.1 Purpose
This document specifies the software requirements for the **Plataforma de Microaprendizaje Adaptativo**, an educational web platform engineered to model memory retention and forgetting dynamics at the Knowledge Component (KC) level. By deploying predictive cognitive models and spaced repetition algorithms, the system delivers timely micro-reviews to secondary school students, optimizing long-term retention while safeguarding experimental research validity.

### 1.2 Scope and Product Overview
The platform provides a subject-agnostic microlearning environment. While the initial empirical pilot investigates 5th-year secondary Science (*Ciencias*), the underlying database schemas, API contracts, and predictive inference engines are entirely domain-neutral. The platform encompasses:
- Responsive, low-cognitive-load web interfaces for students and teachers.
- High-integrity, append-only interaction logging with cryptographic student pseudonymization under Peruvian Law N° 29733.
- Predictive inference microservice modeling retention probability vectors $P(R=1 \mid h)$ over temporal horizons $h \in \{24, 72, 168\}$ hours.
- Spaced review recommendation engine with anti-fatigue frequency capping and deterministic cold-start fallback.
- Quasi-experimental 7-day post-test quarantine ensuring rigorous scientific hypothesis testing.

### 1.3 Definitions, Acronyms, and Abbreviations
- **ADR:** Architectural Decision Record.
- **BKT:** Bayesian Knowledge Tracing.
- **DAS3H:** Difficulty, Ability, Student, Student-Skill, Recency/Frequency across log-spaced windows.
- **ECE:** Expected Calibration Error.
- **FR:** Functional Requirement.
- **KC (Knowledge Component):** An atomic, distinct unit of knowledge or skill within a subject domain (e.g., *Estequiometría: Balance de Materia*).
- **Ley N° 29733:** Peruvian Personal Data Protection Law (*Ley de Protección de Datos Personales*).
- **Microcontent:** A concise educational learning unit designed for 3–5 minute student consumption.
- **NFR:** Non-Functional Requirement.
- **PFA:** Performance Factor Analysis.
- **RLS:** Row Level Security (PostgreSQL).
- **SRS:** System Requirements Specification.

### 1.4 References
1. IEEE Std 830-1998: *IEEE Recommended Practice for Software Requirements Specifications*.
2. ISO/IEC/IEEE 29148:2018: *Systems and software engineering — Life cycle processes — Requirements engineering*.
3. ADR-0001: Monorepo + Microfrontend Architecture vs Monolith & Technology Stack Selection (`docs/architecture/adr/0001-stack-selection.md`).
4. ADR-0002: Service Separation, Cold-Start Mitigation & ML Model Selection (`docs/architecture/adr/0002-service-separation-and-inference-hosting.md`).
5. ADR-0003: Supabase PostgreSQL with Native RLS vs Managed Multitenant DB & Probabilistic Adaptation Boundary (`docs/architecture/adr/0003-probabilistic-adaptation-boundary.md`).
6. Master Plan: `plan_detallado_de_implementaci_n_para_agentes_ia.md`.
7. Architectural Specifications: `docs/architecture/overview.md`, `database-schema.md`, `api-contracts.md`, `model-contract.md`, `security.md`.

---

## 2. Overall Description

### 2.1 Product Perspective
The platform is structured as a decoupled polyglot monorepo comprising four synchronized tiers:
1. **Presentation Tier (`apps/web/`):** Next.js App Router (React, TypeScript, Tailwind CSS, shadcn/ui) deployed on Vercel.
2. **Persistence & Identity Tier (`supabase/`):** Supabase PostgreSQL 15+ with native Row Level Security (RLS) and Supabase Auth.
3. **Predictive & Adaptive Tier (`services/ml-api/`):** Python 3.11+ FastAPI microservice running in a Docker container on blitz.cloud.
4. **Research & Experimentation Tier (`ml/`):** Offline feature extraction, model training, cross-validation, and artifact serialization.

### 2.2 User Characteristics and Roles
The system defines four authoritative user roles:
- **Student (`student`):** 5th-year secondary school adolescent (16–17 years old). Interacts with microcontents, completes diagnostic assessments and practice quizzes, receives empathetic feedback, and executes assigned spaced reviews.
- **Teacher (`teacher`):** Secondary school educator. Manages courses and sections, monitors real-time section mastery via KC retention heatmaps, reviews student progress, schedules activities, and triggers classroom warmup pings.
- **Researcher (`researcher`):** Academic investigator. Accesses pseudonymized dataset exports (`student_id_pseudo`), inspects model calibration metrics, and analyzes experimental retention curves without accessing personally identifiable information.
- **System Worker (`system_worker`):** Automated background actor executing pre-session warmup pings, asynchronous model evaluations, database cleanups, and export generation.

### 2.3 General Constraints
1. **Subject-Agnostic Design:** Course titles, subject areas, and pedagogical taxonomies are database entities. Code logic and API routes shall never contain hardcoded references to "Ciencias" or specific secondary subjects.
2. **Minor Protection Mandate:** Under Peruvian Law N° 29733, real student names, emails, and identifiers must never be merged with ML training sets, exported files, or research publications.
3. **Phase 0 UX/UI Boundary:** No interactive React components, visual UI wireframes, or student/teacher user flows are permitted in `apps/web/src/components/ui/` or `app/` during Phase 0.
4. **Append-Only Immutability:** Interaction logs (`answer_events`) are strictly insert-only; `UPDATE` and `DELETE` operations are revoked at the database layer.

---

## 3. Specific Requirements

### 3.1 External Interface Requirements

#### 3.1.1 User Interfaces
- Mobile-first responsive web design supporting viewports from 360px (mobile) to 1920px (desktop monitors).
- UI typography and color palettes adhering to WCAG 2.1 AA accessibility guidelines.
- Student interface uses empathetic pedagogical phrasing (e.g., *"Concepto por consolidar"*, *"Momento ideal para repasar"*), strictly avoiding punitive or deficit-based terminology.

#### 3.1.2 Hardware Interfaces
- Operates on standard school computer laboratory equipment (desktop PCs with modern browsers: Chrome, Firefox, Edge, Safari) and student mobile devices over 3G/4G/Wi-Fi connections.

#### 3.1.3 Software Interfaces
- **Supabase Auth & PostgreSQL:** Secure connection pooling via asyncpg and RESTful queries via `@supabase/supabase-js`.
- **FastAPI Microservice:** JSON-over-HTTP API compliant with OpenAPI 3.1 specification (`packages/contracts/openapi/openapi.json`).

#### 3.1.4 Communications Interfaces
- All network traffic encrypted via TLS 1.3 over HTTPS.
- Authentication credentials transmitted as Bearer Tokens (JWT signed with RS256/ES256).

---

### 3.2 Functional Requirements

#### FR-01: Authentication & Profile Management
- **Description:** The system shall authenticate users via Supabase Auth and associate each user account with a record in `profiles`.
- **Inputs:** User credentials (email, password) or session JWT.
- **Processing:** Validates credentials; checks session claims; retrieves role (`student`, `teacher`, `researcher`, `system_worker`).
- **Outputs:** Authenticated user session with role-scoped authorization context.
- **Acceptance Criteria:** Unauthenticated requests are rejected with HTTP 401; users can only read and update their own profile data under RLS policies.

#### FR-02: Course & Section Hierarchical Structure
- **Description:** The system shall maintain an agnostic hierarchical curriculum structure: `courses` $\rightarrow$ `sections` $\rightarrow$ `units` $\rightarrow$ `knowledge_components` (KCs).
- **Inputs:** Course metadata, section identifiers, academic units, atomic Knowledge Component descriptors.
- **Processing:** Enforces foreign key constraints; establishes curriculum graphs without subject-specific hardcoding.
- **Outputs:** Structured curriculum tree accessible to authorized teachers and enrolled students.
- **Acceptance Criteria:** A single course can support multiple independent sections; each KC maps to a single parent unit with unique UUID.

#### FR-03: Student Enrollment & Pseudonymization
- **Description:** The system shall enroll students into sections and automatically generate an immutable pseudonymized UUID (`student_id_pseudo`) for each enrollment.
- **Inputs:** `student_id` (linking to `profiles.id`), `section_id`.
- **Processing:** Inserts enrollment record; generates `student_id_pseudo = gen_random_uuid()`; enforces unique constraint on `(section_id, student_id)`.
- **Outputs:** Active enrollment with pseudonymized research identifier.
- **Acceptance Criteria:** `student_id_pseudo` cannot be altered once created; analytical export queries exclusively expose `student_id_pseudo` to researchers.

#### FR-04: Microcontent Management
- **Description:** The system shall store, organize, and retrieve modular microcontent cards designed for 3–5 minute learning chunks with immutable versioning and strict JSON structure validation.
- **Inputs:** Microcontent title, content type (`text_summary`, `infographic_card`, `concept_map`, `youtube_video`), content body (structured JSON payload adhering to `content_schema_version`), estimated read time, source metadata (author, license, attribution), and associated `knowledge_component_id`.
- **Processing:** Validates content structure against strict JSON schema (prohibiting raw/unfiltered HTML generated by LLMs); links microcontent to the targeted KC; maintains version history (`version_group_id`, `version_number`) ensuring published microcontents referenced by historical reviews are never destructively overwritten.
- **Outputs:** Versioned microcontent records available for practice sessions and adaptive recommendations.
- **Acceptance Criteria:** Every microcontent is linked to exactly one KC; content types are strictly constrained by database enum; video content is restricted to official YouTube player embeds without downloading media; raw HTML injection is strictly rejected.

#### FR-05: Question Bank & Calibration
- **Description:** The system shall maintain a calibrated multiple-choice question bank categorized by Knowledge Component.
- **Inputs:** Question text, associated KC, difficulty parameter prior ($0.000$ to $1.000$), discrimination parameter, explanatory feedback, and four multiple-choice options (`question_options`) with exactly one correct option.
- **Processing:** Validates that each question has at least two options and exactly one designated correct option (`is_correct = true`).
- **Outputs:** Calibrated question item ready for presentation in assessments and practice quizzes.
- **Acceptance Criteria:** Question difficulty is stored as a numerical prior; explanatory feedback is available for immediate formative remediation.

#### FR-06: Activity Lifecycle & Typology
- **Description:** The system shall manage structured educational activities categorized into distinct operational types: `diagnostic`, `practice`, `immediate_assessment`, and `delayed_assessment`.
- **Inputs:** Activity title, section, activity type, start timestamp, due timestamp, and ordered list of questions (`activity_questions`).
- **Processing:** Transitions activity states (`draft`, `published`, `in_progress`, `completed`); enforces time windows.
- **Outputs:** Active activity sessions delivered to enrolled students.
- **Acceptance Criteria:** Activities marked as `delayed_assessment` are quarantined from adaptive recommendation logic.

#### FR-07: Quiz Attempt Execution
- **Description:** The system shall track student quiz attempts from initiation to completion.
- **Inputs:** `activity_id`, `student_id`.
- **Processing:** Creates `quiz_attempts` record; tracks `started_at`, `completed_at`, `score`, and `attempt_number`.
- **Outputs:** Unique `attempt_id` governing the submission of individual answer events.
- **Acceptance Criteria:** Multiple attempts are tracked sequentially by `attempt_number`; attempt status transitions to completed upon final answer submission.

#### FR-08: Immutable Answer Event Logging
- **Description:** The system shall record student responses in an append-only `answer_events` table with strict idempotency and cryptographic immutability.
- **Inputs:** `attempt_id`, `question_id`, `selected_option_id`, `response_time_seconds`, `idempotency_key`.
- **Processing:** Checks `idempotency_key` uniqueness; verifies selected option correctness; calculates `is_correct`; records timestamp `now()`.
- **Outputs:** Created `answer_events` record with HTTP 201 response.
- **Acceptance Criteria:** Duplicate requests with identical `idempotency_key` return existing record without duplicate insertion; database permissions explicitly deny `UPDATE` and `DELETE`.

#### FR-09: Feature Extraction & Temporal Windowing
- **Description:** The predictive microservice shall extract on-the-fly temporal features from the student's historical interaction logs for a targeted KC.
- **Inputs:** Sequence of historical `answer_events` for student $u$ and KC $k$.
- **Processing:** Computes cumulative successes ($s_{u,k,w}$) and cumulative failures ($f_{u,k,w}$) across log-spaced time windows:
  $$W \in \{[0, 1\text{h}], [1\text{h}, 1\text{d}], [1\text{d}, 7\text{d}], [7\text{d}, 30\text{d}], [30\text{d}, \infty)\}$$
  and calculates inter-practice intervals $\Delta t$.
- **Outputs:** Engineered feature vector matching the input contract of `BaseRetentionModel`.
- **Acceptance Criteria:** Temporal leakage is strictly prevented ($event\_timestamp < t$); execution completes in $\le 200$ ms.

#### FR-10: Retention Probability Inference
- **Description:** The predictive microservice shall estimate the vector of memory recall probabilities over multiple time horizons using calibrated cognitive models.
- **Inputs:** Extracted student temporal feature vector and target horizons $h \in \{24, 72, 168\}$ hours.
- **Processing:** Executes `predict_recall()` on the active `BaseRetentionModel` artifact; computes $\vec{P} = [P(R=1 \mid 24), P(R=1 \mid 72), P(R=1 \mid 168)]$; classifies risk level.
- **Outputs:** `ModelInferenceResult` containing prediction vector, risk level (`low`, `medium`, `high`, `critical`), and model metadata.
- **Acceptance Criteria:** Returns `insufficient_history` if student has $< 3$ prior interactions; probabilities are bounded in $[0.0000, 1.0000]$.

#### FR-11: Adaptive Recommendation Generation
- **Description:** The adaptation policy engine shall evaluate memory recall probability $P(R=1 \mid h)$ against a configurable threshold $\tau_{\text{recall}}$ to schedule timely spaced reviews.
- **Inputs:** Predicted retention probability vector $\vec{P}$, configurable threshold $\tau_{\text{recall}}$ (environment/tenant setting, default: 0.65 provisional), KC catalog, student recent review history.
- **Processing:** Evaluates whether $P(R=1 \mid h) < \tau_{\text{recall}}$ (distinguishing memory recall probability $p_{\text{recall}}$ from forgetting risk $p_{\text{forgetting}} = 1 - p_{\text{recall}}$); enforces anti-fatigue frequency caps; selects suitable microcontent; records decision reason in `recommendations`.
- **Outputs:** Persisted recommendation record with `selection_method = 'predictive_model'` or `'rule_based_fallback'`.
- **Acceptance Criteria:** Recommendations are auditable; each record references the specific model version, probability, and threshold used; threshold 0.65 is treated as a configurable parameter, not a validated universal constant.

#### FR-12: Review Assignment Scheduling
- **Description:** The system shall convert approved recommendations into student review tasks (`review_assignments`) with due dates and anti-fatigue constraints.
- **Inputs:** `recommendation_id`, `student_id`, target KC, recommended microcontent.
- **Processing:** Enforces anti-fatigue frequency cap (maximum 3 review assignments per student per day); calculates spaced due date ($t + h$); creates `review_assignments` record.
- **Outputs:** Active review assignment presented on the student's learning dashboard.
- **Acceptance Criteria:** Students cannot be flooded with excessive reviews; review tasks are completed when student views microcontent and answers a check question.

#### FR-13: Degraded Fallback & Cold-Start Resilience
- **Description:** The system shall provide deterministic rule-based recommendations when the ML predictive service experiences cold starts, timeouts, or insufficient interaction history.
- **Inputs:** Student attempt history, service timeout flag ($> 5.0$ seconds), or `insufficient_history` status.
- **Processing:** Triggers `rule_based_fallback`: evaluates recent accuracy ($< 60\%$) and days since last practice ($> 5$ days); selects foundational microcontent card.
- **Outputs:** Fallback recommendation with `selection_method = 'rule_based_fallback'`.
- **Acceptance Criteria:** The student experience never deadlocks or halts due to backend container cold starts; fallback execution completes in $< 100$ ms.

#### FR-14: Teacher Analytics & Section Monitoring
- **Description:** The system shall provide teachers with real-time aggregated dashboards visualizing KC retention risk and section completion telemetry.
- **Inputs:** `section_id`, teacher authorization token.
- **Processing:** Aggregates section interactions; computes average recall probability and risk distribution per KC; tracks completion rates.
- **Outputs:** Section telemetry dashboard displaying KC risk distribution without revealing raw minor PII.
- **Acceptance Criteria:** Teachers can identify struggling KCs across their section at a glance; RLS enforces that teachers can only view sections assigned to them.

#### FR-15: Quasi-Experimental 7-Day Assessment Isolation
- **Description:** The system shall enforce cryptographic and logical quarantine of questions designated for the 7-day delayed post-test.
- **Inputs:** Question bank, activity configuration, recommendation candidate pool.
- **Processing:** Filters out all questions associated with `delayed_assessment` activities from practice quiz pools and adaptive recommendation candidate sets.
- **Outputs:** Quarantined assessment items presented exclusively during the scheduled 7-day post-test window.
- **Acceptance Criteria:** Zero leakage of delayed assessment questions into formative practice; verified via automated query assertions.

#### FR-16: Audit Trail & Research Export
- **Description:** The system shall export anonymized research datasets and algorithmic decision trails for thesis verification and empirical reproducibility.
- **Inputs:** Researcher credentials, course/section filter, date range.
- **Processing:** Queries interaction logs, predictions, and recommendations; joins with `student_id_pseudo`; strips all profile PII (names, emails, user IDs).
- **Outputs:** Structured CSV/JSON export containing pseudonymized interactions, timestamps, features, predictions, and algorithmic justifications.
- **Acceptance Criteria:** Exports contain zero personal identifiable information; every exported prediction includes model version and hyperparameter metadata.

#### FR-17: Teacher Document Ingestion & Assisted Question Draft Generation
- **Description:** The system shall ingest teacher-provided documents (PDF and PPTX) from private storage and generate preliminary question drafts via a configurable, provider-agnostic LLM adapter.
- **Inputs:** Internal document reference (`storage_path`) located in the private `teacher-materials` bucket, verified MIME type (`application/pdf`, PPTX), file checksum, course ID, and teacher authorization context.
- **Processing:** Validates document metadata, file size ($\le 30$ MB), and ownership; extracts page/slide-indexed clean text treated as untrusted data; invokes configured `QuestionGenerationProvider` with bounded structural schemas; validates candidate items with Pydantic; persists candidate items in `question_drafts` with initial status `'draft'`.
- **Outputs:** Persisted `content_generation_jobs` record and associated `question_drafts` with page/slide source citations.
- **Acceptance Criteria:** AI-generated drafts are strictly quarantined from student activities and knowledge tracing; zero student PII is transmitted to external model providers; no vendor/model string is hardcoded.

#### FR-18: Human-in-the-Loop Question Draft Curation & Canonical Publication
- **Description:** The system shall provide an authoritative teacher curation workflow allowing educators to inspect, modify, assign KCs, and approve or reject AI-generated question drafts prior to canonical publication.
- **Inputs:** Draft identifier, edited question text, options, verified single correct answer, pedagogical explanation, and associated `knowledge_component_id`.
- **Processing:** Verifies teacher ownership/section assignment; validates that each approved draft has at least two options and exactly one designated correct option; executes transactional insertion into canonical `questions` and `question_options`; transitions draft status to `'approved'` or `'rejected'`.
- **Outputs:** Published canonical questions ready for inclusion in activities; audit record linking original draft to published item.
- **Acceptance Criteria:** No AI-generated question is ever published automatically; every published question requires explicit teacher approval and an assigned KC.

#### FR-19: In-App Deduplicated Notifications & Review Reminders
- **Description:** The system shall deliver non-intrusive, deduplicated in-app notifications informing students of scheduled adaptive reviews without relying on browser push channels.
- **Inputs:** Scheduled `review_assignments`, target KC, student session context.
- **Processing:** Constructs empathetic notification item with unique deduplication key (`student_id:kc_id:horizon:date`); persists into `notifications` table; resolves student notifications exclusively through authenticated session token (`auth.uid()`).
- **Outputs:** Real-time in-app notification badges and review direct links on the student dashboard.
- **Acceptance Criteria:** Students never receive duplicate notification entries for the same review window upon dashboard refreshes; student operations never accept browser-supplied `student_id`; student UI phrasing strictly adheres to empathetic feedback guidelines.

---

### 3.3 Non-Functional Requirements (NFRs)

#### NFR-01: Latency & Performance
- **Interactive Answer Submission:** The endpoint `POST /api/v1/learning/attempts/{attempt_id}/answers` shall respond within $\le 300$ ms under normal network conditions.
- **Predictive Inference:** The endpoint `POST /api/v1/predictions/retention` shall execute feature extraction and probabilistic inference within $\le 1500$ ms.
- **Circuit Breaker Timeout:** If inference takes $\ge 5000$ ms (e.g. during a blitz.cloud container cold start), the caller shall automatically trigger the deterministic fallback policy (`rule_based_fallback`).

#### NFR-02: Availability & Reliability
- **Uptime:** The web presentation tier (`apps/web/` on Vercel) and database tier (Supabase) shall maintain 99.9% availability during school hours (07:00–18:00 UTC-5).
- **Cold-Start Resilience:** The system shall mitigate container sleeping on blitz.cloud through pre-session warmup pings (`POST /api/v1/health/warmup`) and deterministic fallbacks, ensuring zero user-facing service failure.
- **Data Durability:** Interaction logs in `answer_events` are append-only and backed up continuously via Supabase automated point-in-time recovery (PITR).

#### NFR-03: Security & Regulatory Compliance
- **Database Security:** 100% of PostgreSQL tables shall have Row Level Security (RLS) enabled. Policies shall use scalar subqueries `(SELECT auth.uid())` for optimization.
- **Token Verification:** All API endpoints in FastAPI shall cryptographically validate Supabase RS256/ES256 asymmetric JWTs, verifying `aud = 'authenticated'`, issuer, and token expiration.
- **Minor Data Protection:** The system shall comply with Peru's Personal Data Protection Law (Ley N° 29733) and D.S. 003-2013-JUS:
  - Personal identifiers (`profiles.id`, names, emails) are disassociated from research data via `student_id_pseudo`.
  - Service-role secret keys are restricted to trusted backend worker environments and never exposed to client browsers.
  - Institutional informed consent is gathered from legal guardians prior to platform onboarding.

#### NFR-04: Scalability & Classroom Concurrency
- **Concurrent Classroom Spike:** The platform shall support at least 30 concurrent students submitting answers within a 5-minute laboratory session without error or request dropping.
- **Connection Management:** Backend services shall utilize asynchronous connection pooling (asyncpg) with pre-allocated connection pools to prevent database exhaustion during classroom spikes.

---

## 4. Verification Matrix and Traceability

| Req ID | Requirement Name | Architectural Tier | Verification Method |
|---|---|---|---|
| **FR-01** | Authentication & Profile Management | Supabase Auth / Next.js | Automated integration test with Supabase Auth mock |
| **FR-02** | Course & Section Hierarchy | Supabase PostgreSQL DDL | Schema constraint verification in `database-schema.md` |
| **FR-03** | Student Enrollment & Pseudonymization | Supabase PostgreSQL / RLS | SQL trigger and UUID format validation test |
| **FR-04** | Microcontent Management | Next.js / Supabase | Content schema validation in TypeScript / Zod |
| **FR-05** | Question Bank & Calibration | Supabase PostgreSQL / Web | Option count and difficulty prior constraint test |
| **FR-06** | Activity Lifecycle & Typology | Supabase PostgreSQL / API | State transition unit tests on activity status enum |
| **FR-07** | Quiz Attempt Execution | Next.js / Supabase | Session tracking integration test |
| **FR-08** | Immutable Answer Event Logging | Supabase PostgreSQL DDL | Permission revocation audit (`REVOKE UPDATE, DELETE`) |
| **FR-09** | Feature Extraction & Windowing | Python FastAPI (`services/ml-api`) | Windowing temporal boundary tests without data leakage |
| **FR-10** | Retention Probability Inference | Python FastAPI (`BaseRetentionModel`) | AST validation of `BaseRetentionModel` and inference tests |
| **FR-11** | Adaptive Recommendation Generation | Python FastAPI (`AdaptationPolicy`) | Threshold $\tau$ decision logic unit tests |
| **FR-12** | Review Assignment Scheduling | Next.js / Supabase | Anti-fatigue daily cap (max 3) constraint test |
| **FR-13** | Degraded Fallback & Cold Start | Python FastAPI / Next.js | 5.0s timeout circuit breaker simulation test |
| **FR-14** | Teacher Analytics & Monitoring | Next.js / Supabase RLS | RLS multi-tenant section isolation penetration test |
| **FR-15** | 7-Day Assessment Quarantine | Supabase PostgreSQL / API | Query assertion ensuring delayed items excluded from practice |
| **FR-16** | Audit Trail & Research Export | Supabase Views / Python API | Data export schema audit verifying zero PII exposure |
| **NFR-01** | Latency & Performance | Infrastructure / API | Automated latency benchmark script ($p_{95} \le 1500$ ms) |
| **NFR-02** | Availability & Reliability | blitz.cloud / Vercel / Supabase | Warmup ping endpoint and uptime health-check tests |
| **NFR-03** | Security & Compliance | Supabase RLS / FastAPI JWT | Automated JWT verification and Ley N° 29733 audit |
| **NFR-04** | Scalability & Concurrency | FastAPI asyncpg / PostgreSQL | Concurrent session load test (30 simultaneous clients) |
