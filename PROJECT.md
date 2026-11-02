# Project: Plataforma de Microaprendizaje Adaptativo (Fase 0: Arquitectura, Gobernanza y Contratos)

## Architecture
- **Presentation Layer**: `apps/web/` (Next.js App Router, React, Tailwind CSS, shadcn/ui). *Strictly scaffolding in Phase 0: No wireframes, visual components, or user flows.*
- **Persistence & Identity Layer**: `supabase/` (Supabase PostgreSQL 15+, Supabase Auth, Row Level Security, Append-only event store).
- **Predictive & Adaptive Service**: `services/ml-api/` (Python 3.11+, FastAPI, Pydantic v2, DAS3H, BKT/DKT, rule-based fallback for blitz.cloud cold start).
- **Scientific Research & Experimentation**: `ml/` (Datasets, EDA, feature engineering, offline model training & calibration, frozen artifacts).
- **Shared Contracts**: `packages/contracts/` (OpenAPI 3.1 JSON schema, TypeScript definitions).
- **Agent Governance & Workflows**: `.agents/` (AGENTS.md, rules/, skills/, workflows/).
- **Technical Documentation & Specifications**: `docs/` (architecture/, adr/, research/, SRS.md).

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Monorepo Directory Scaffold | Complete directory tree for apps, docs, ml, packages, services, supabase, .agents | M1 (DONE) | Survey 1 (Plan Sec 1.1) |
| 2 | Root AGENTS.md | Central technical governance constitution with rules, boundaries, and tech stack | M1 (DONE) | Survey 1 (Plan Sec 2.1) |
| 3 | Subsystem AGENTS.md | Specialized governance for apps/web/, services/ml-api/, ml/, and supabase/ | M1 (DONE) | Survey 1 (Plan Sec 1.1) |
| 4 | Agent Rules (.agents/rules/) | 6 rules: architecture, frontend, backend, database, machine-learning, research-integrity | M1 (DONE) | Survey 1 (Plan Sec 2.2) |
| 5 | Agent Skills (.agents/skills/) | 8 skills: fastapi-templates, supabase, supabase-postgres-best-practices, improve-animations, eda-pipeline, feature-engineering, model-training, model-evaluation (and Plan Sec 2.3 mappings) | M1 (DONE) | Survey 1 (Plan Sec 2.3) |
| 6 | Agent Workflows (.agents/workflows/) | 6 workflows: plan-feature, implement-feature, review-code, database-migration, integrate-model, release-mvp | M1 (DONE) | Survey 1 (Plan Sec 1.1) |
| 7 | Root Configuration Files | .gitignore, .env.example, docker-compose.yml, README.md, CONTRIBUTING.md | M1 (DONE) | Survey 1 (Plan Sec 1.1) |
| 8 | UX/UI Exclusion Guardrail | Enforce zero visual components, wireframes, and user flows in apps/web/ | M1 (DONE) | ORIGINAL_REQUEST R3 |
| 9 | Architecture Overview (overview.md) | Distributed decoupled topology, 8-step end-to-end adaptive execution flow | M2 (DONE) | Survey 2 (Plan Sec 3.1) |
| 10 | PostgreSQL DDL & RLS (database-schema.md) | Complete DDL for 17+ tables, UUIDs, indexes, RLS policies, append-only answer_events | M2 (DONE) | Survey 2 (Plan Sec 3.2) |
| 11 | API Contracts (api-contracts.md & openapi.json) | OpenAPI 3.1 JSON schemas for /answers, /predictions, /recommendations | M2 (DONE) | Survey 2 (Plan Sec 3.3) |
| 12 | Model Contract (model-contract.md) | Python BaseRetentionModel ABC, Pydantic v2 schemas, BKT protocol, artifact metadata | M2 (DONE) | Survey 2 (Plan Sec 3.4) |
| 13 | Security Architecture (security.md) | RBAC/ABAC matrix, Supabase JWT validation, Ley N° 29733 minor data privacy | M2 (DONE) | Survey 2 (Plan Sec 3.5) |
| 14 | Cross-Contract Type Consistency | 100% strict matching of fields, types, and constraints across SQL, OpenAPI, and Python | M2 (DONE) | Survey 2 (Checklist Sec 7) |
| 15 | ADR-0001: Stack Selection / Monorepo vs Monolith | Decoupled Next.js + Supabase + FastAPI topology | M3 (DONE) | Survey 3 (Plan Sec 4.2) |
| 16 | ADR-0002: Service Separation, Cold-Start & Model Selection | DAS3H vs PFA/BKT baselines, blitz.cloud cold start mitigation, rule-based fallback | M3 (DONE) | Survey 3 (Plan Sec 4.2) |
| 17 | ADR-0003: Supabase RLS & Adaptation Boundary | Native RLS multi-tenancy, immutable events, prediction vs pedagogy boundary | M3 (DONE) | Survey 3 (Plan Sec 4.2) |
| 18 | System Requirements Specification (SRS.md) | IEEE 830 / ISO 29148 specification, user roles, FR-01 to FR-16, NFRs | M3 (DONE) | Survey 3 (Plan Sec 4.1) |
| 19 | Research & Evaluation Protocol (evaluation-protocol.md) | Quasi-experimental 7-day retention protocol, metrics, Student Group-K-Fold, 5-item risk matrix | M3 (DONE) | Survey 3 (Plan Sec 5) |
| 20 | Automated Verification Script (verify-phase0.py) | Standalone Python script validating file presence, DDL syntax, OpenAPI validity, contract AST | M4 | Survey 3 (Plan Sec 7) |
| 21 | Forensic Audit & Checklist Verification | Systematic audit of Section 7 checklist items and anti-cheating verification | M4 | Survey 3 (Plan Sec 7) |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Monorepo Structure & Agent Governance | Features 1-8: Directory tree, AGENTS.md, rules, skills, workflows, root configs, apps/web scaffolding (no UI) | None | DONE |
| M2 | Technical Architecture & Formal Contracts | Features 9-14: docs/architecture/ (overview, database-schema, api-contracts, model-contract, security), openapi.json, type consistency | M1 | DONE |
| M3 | ADRs, SRS & Research Evaluation Protocol | Features 15-19: docs/architecture/adr/ (0001, 0002, 0003), docs/SRS.md, docs/research/evaluation-protocol.md | M1, M2 | DONE |
| M4 | Automated Verification & Integrity Audit | Features 20-21: scripts/verify-phase0.py, execution with exit code 0, Section 7 checklist audit | M1, M2, M3 | DONE |
| M5 | Phase 1 UI/UX Implementation (Nexo Platform) | Implementation of 10 screens from Capturas/ in apps/web/ (Student Dashboard, Courses, Pre-activity, Microlesson, Quiz, Feedback, Analytics, Teacher Portal, System Telemetry) | M1, M2, M4 | DONE |

## Interface Contracts
### Database DDL <-> OpenAPI Contracts <-> Python Model Contracts
- Entity `answer_events` / `AnswerEventSubmitRequest`:
  - `attempt_id`: UUID (PostgreSQL UUID, OpenAPI string uuid, Python UUID)
  - `question_id`: UUID (PostgreSQL UUID, OpenAPI string uuid, Python UUID)
  - `selected_option_id`: UUID (PostgreSQL UUID, OpenAPI string uuid, Python UUID)
  - `response_time_seconds`: NUMERIC(6,2) / float (PostgreSQL NUMERIC, OpenAPI number, Python float)
  - `idempotency_key`: UUID (PostgreSQL UUID, OpenAPI string uuid, Python UUID)
- Entity `predictions` / `PredictionOutput`:
  - `student_id`: UUID
  - `knowledge_component_id`: UUID
  - `recall_probability_24h`: NUMERIC(5,4) / float in [0.0, 1.0]
  - `recall_probability_72h`: NUMERIC(5,4) / float in [0.0, 1.0]
  - `recall_probability_168h`: NUMERIC(5,4) / float in [0.0, 1.0]
  - `risk_level`: enum ('low', 'medium', 'high', 'critical')
  - `prediction_status`: enum ('valid', 'insufficient_history', 'degraded_fallback')
- Entity `recommendations` / `RecommendationResponse`:
  - `recommendation_id`: UUID
  - `student_id`: UUID
  - `knowledge_component_id`: UUID
  - `microcontent_id`: UUID
  - `selection_method`: enum ('predictive_model', 'rule_based_fallback', 'teacher_assigned')
  - `decision_reason`: string

## Code Layout
- `/root/PlataformaMicro/`
  - `.agents/rules/` (.md rule files with trigger: always_on)
  - `.agents/skills/` (<skill_name>/SKILL.md)
  - `.agents/workflows/` (<workflow_name>.md)
  - `apps/web/` (Next.js web app scaffolding, package.json, tsconfig.json, tailwind.config.ts - NO UI components)
  - `docs/architecture/` (Technical documentation, DDL, contracts, security)
  - `docs/architecture/adr/` (ADR-0001, ADR-0002, ADR-0003)
  - `docs/research/` (evaluation-protocol.md, model-selection.md, data-dictionary.md)
  - `docs/SRS.md` (System requirements specification)
  - `ml/` (experimentation codebase and configs)
  - `packages/contracts/` (OpenAPI and shared TypeScript types)
  - `services/ml-api/` (FastAPI microservice codebase)
  - `supabase/` (migrations, seed.sql, config.toml)
  - `scripts/` (verify-m1.py, verify-m2.py, verify-m3.py, verify-phase0.py)
