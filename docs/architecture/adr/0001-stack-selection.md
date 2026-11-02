# ADR-0001: Monorepo + Microfrontend Architecture vs Monolith & Technology Stack Selection

- **Status:** ACCEPTED
- **Date:** 2026-11-01
- **Deciders:** Lead Architect, Antigravity AI Orchestrator
- **Technical Domain:** Monorepo Topology, Web Presentation, Persistence, Predictive Engine
- **Consulted:** Frontend Specialist, Backend Specialist, Machine Learning Specialist, Security Specialist

---

## 1. Context and Problem Statement

The platform is designed as an adaptive microlearning web system targeted at 5th-year secondary school students in Peru (16–17 years old), piloting in Science with an agnostic architecture applicable to any secondary curriculum. The platform has two fundamentally distinct architectural drivers:

1. **Interactive Educational Experience:** A highly responsive, accessible web experience optimized for mobile and desktop classroom devices, requiring microlearning card rendering (3–5 minute chunks), interactive multiple-choice quiz flows, and real-time student telemetry with minimal cognitive load and empathetic feedback.
2. **Probabilistic Cognitive Modeling:** A specialized scientific inference engine modeling memory retention and forgetting dynamics across temporal horizons ($h \in \{24, 72, 168\}$ hours) via Knowledge Components (KCs), demanding high-performance scientific libraries (NumPy, pandas, scikit-learn), temporal windowing feature extractors, and calibrated predictive inference.

### Evaluated Architectural Alternatives

- **Alternative A: Monolithic Python Framework (Django or FastAPI Fullstack with SSR/Jinja2):**
  - *Advantages:* Single language runtime; straightforward sharing of data science classes; single deployment unit.
  - *Deficiencies:* Rigid and outdated UI capabilities for rich, reactive microlearning interactions; high latency for dynamic client-side state manipulation; poor separation between fast-evolving UI components and scientific modeling algorithms; lack of modern component ecosystems (e.g., shadcn/ui, Tailwind CSS).
- **Alternative B: Monolithic Node.js / TypeScript Application (Next.js with embedded ML):**
  - *Advantages:* Single TypeScript codebase; unified developer experience; excellent SSR/RSC capabilities on Vercel.
  - *Deficiencies:* The Node.js scientific computing ecosystem is severely deficient compared to Python; training and inference of advanced memory retention models (DAS3H, BKT, PFA) require native Python C-extensions (NumPy, SciPy, scikit-learn); calling Python scripts via child processes in Node.js introduces unpredictable latency, memory overhead, and severe debugging complexity.
- **Alternative C: Independent Multi-Repository Architecture:**
  - *Advantages:* Total physical isolation between frontend, database, and backend services.
  - *Deficiencies:* High coordination overhead across multiple repositories; schema drift and contract desynchronization between database migrations, API schemas, and client types; difficult end-to-end integration testing and unified agent governance.
- **Alternative D: Decoupled Polyglot Monorepo Topology (Next.js + Supabase + FastAPI):**
  - *Advantages:* Unifies governance and contracts in a single git repository while leveraging the best-in-class toolchain for each specific concern: Next.js App Router for reactive presentation, Supabase PostgreSQL with native Row Level Security (RLS) for data persistence and authentication, and FastAPI with Python 3.11+ for predictive machine learning and adaptation policies.

---

## 2. Decision Outcome

We decided to adopt **Alternative D: Decoupled Polyglot Monorepo Topology** structured as follows:

```text
adaptive-microlearning-platform/
├── apps/web/               # Presentation Layer (Next.js 14+ App Router, React, TypeScript, Tailwind, shadcn/ui)
├── supabase/               # Persistence & Auth Layer (PostgreSQL 15+, Native RLS, Supabase Auth, Migrations)
├── services/ml-api/        # Predictive & Adaptive Microservice (Python 3.11+, FastAPI, Pydantic v2, asyncpg, Docker)
├── ml/                     # Scientific Research & Experimentation (Datasets, EDA, Feature Engineering, Training)
├── packages/contracts/     # Shared Type & Schema Contracts (OpenAPI 3.1 JSON, TypeScript types)
├── docs/                   # System Architecture, ADRs, Research Protocols, IEEE 830 SRS
└── .agents/                # Antigravity Multi-Agent Governance (Rules, Skills, Workflows)
```

### Detailed Component Selections

1. **Presentation Layer (`apps/web/`):**
   - **Framework:** Next.js (App Router), React 18+, TypeScript.
   - **Styling & Components:** Tailwind CSS, shadcn/ui (Radix UI primitives).
   - **Form Validation & State:** React Hook Form, Zod.
   - **Data Visualization:** Recharts for student retention progress and teacher section telemetry.
   - **Hosting:** Vercel (Edge Network and Serverless Functions).
   - **Constraint:** Strictly decoupled from ML logic; zero `.pkl` artifact access; interacts with persistence via typed Supabase Client and with predictive capabilities via typed OpenAPI HTTP requests.

2. **Persistence and Identity Layer (`supabase/`):**
   - **Database:** PostgreSQL 15+ hosted on Supabase.
   - **Security:** Native Row Level Security (RLS) enabled on 100% of tables with scalar subqueries `(SELECT auth.uid())`.
   - **Authentication:** Supabase Auth (JWT with RS256/ES256 asymmetric cryptographic signing).
   - **Immutability:** Strictly append-only interaction store (`answer_events`) with explicit `REVOKE UPDATE, DELETE FROM anon, authenticated`.
   - **Role Segregation:** RBAC enforced in PostgreSQL via `profiles.role` (`student`, `teacher`, `researcher`, `system_worker`).

3. **Predictive & Adaptive Service (`services/ml-api/`):**
   - **Runtime:** Python 3.11+, FastAPI, Pydantic v2.
   - **Database Access:** asyncpg / SQLAlchemy Core for high-throughput asynchronous reading of student interaction logs.
   - **Containerization:** Docker (`linux/amd64`), deployed on blitz.cloud container hosting.
   - **Responsibilities:** On-the-fly temporal window feature extraction, probabilistic recall inference $P(R=1 \mid h)$, and pedagogical recommendation policy generation.

4. **Shared Contracts Layer (`packages/contracts/`):**
   - **OpenAPI Specification:** `packages/contracts/openapi/openapi.json` (OpenAPI 3.1.0) serving as the single contract truth between `services/ml-api/` and `apps/web/`.
   - **TypeScript Definitions:** Automated type generation from Supabase PostgreSQL schema and OpenAPI JSON ensuring compile-time safety across the frontend.

---

## 3. Architectural Boundaries and Non-Negotiable Rules

1. **Frontend Isolation:** The web client shall never directly compute memory retention decay curves or make autonomous pedagogical sequencing decisions. All recommendations originate from the `/api/v1/recommendations/generate` backend endpoint or its explicit deterministic rule fallback.
2. **Single Persistence Truth:** Supabase PostgreSQL is the sole source of truth for the platform. FastAPI does not own database DDL migrations; all schema changes originate exclusively from `supabase/migrations/`.
3. **Investigation vs Production Segregation:** The `ml/` directory contains exploration notebooks, training pipelines, and dataset fixtures. The production service `services/ml-api/` only consumes frozen, versioned model artifacts packaged with explicit `metadata.json`.
4. **Phase 0 Strict Scope Boundary:** During Phase 0, no interactive React components, visual UI wireframes, or student/teacher user flows may be introduced in `apps/web/src/components/ui/` or `app/`. Only structural scaffolding and configuration files are materialized.

---

## 4. Consequences and Trade-offs

### Positive Consequences

- **Best-of-Breed Tooling:** Maximizes developer efficiency by using TypeScript/React for UI and Python for scientific computation without compromising either domain.
- **Auditable Security:** Native RLS ensures multitenant data isolation at the database layer; even if an API route suffers an authorization defect, PostgreSQL denies unauthorized row access.
- **Contract-Driven Cohesion:** Monorepo co-location enables continuous integration to detect contract drift immediately across SQL DDL, OpenAPI JSON, and Python Pydantic models.
- **Fast Startup & SSR:** Next.js App Router provides instant initial page loads and search engine optimization, crucial for low-bandwidth school networks.

### Negative Consequences and Mitigations

- **Multi-Runtime Orchestration:** Developers must manage both Node.js and Python toolchains locally.
  - *Mitigation:* Comprehensive `docker-compose.yml` orchestrating local Supabase (PostgreSQL, Auth), FastAPI microservice, and Next.js frontend with unified environment variables in `.env.example`.
- **Cross-Language Type Synchronization:** Changes to API payloads in FastAPI require re-generating OpenAPI contracts and updating TypeScript definitions.
  - *Mitigation:* CI automated verification script (`scripts/verify-phase0.py` and `scripts/verify-m2.py`) validating 100% field alignment between SQL schemas, OpenAPI specifications, and Pydantic models.

---

## 5. Compliance Notes

- **Peruvian Law N° 29733 (Ley de Protección de Datos Personales):** The architecture strictly disassociates personal identifiers from scientific logs using persistent pseudonyms (`student_id_pseudo`).
- **OpenAPI 3.1.0:** Contract compliance is verified using Python `json` and `jsonschema` validation against `packages/contracts/openapi/openapi.json`.
