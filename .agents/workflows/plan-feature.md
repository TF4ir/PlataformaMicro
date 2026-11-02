# Workflow: Plan Feature

## 1. Objective & Scope
Deconstruct, specify, and validate requirements for any new capability across the Plataforma de Microaprendizaje Adaptativo monorepo prior to authoring code.

## 2. Execution Phases

### Phase 1: Requirements Ingestion & Tracing
- Map the incoming user story or objective directly to the System Requirements Specification (`docs/SRS.md`, FR-01 through FR-16).
- Identify target user role (Student, Teacher, or Admin).
- Confirm pedagogical alignment (microlearning chunking of 3–5 min, empathetic language, Ley N° 29733 compliance).

### Phase 2: Architectural Boundary Verification
- Check proposed changes against root `AGENTS.md` and `.agents/rules/architecture.md`:
  - Does this touch presentation? (`apps/web/`)
  - Does this touch inference or adaptation logic? (`services/ml-api/`)
  - Does this alter relational schemas or security policies? (`supabase/`)
  - Does this impact ML training or evaluation? (`ml/`)
- Enforce strict boundaries: ensure no ML computation or direct Supabase administrative mutations are introduced in `apps/web/`.

### Phase 3: Contract-First Schema Design
- If endpoints or payloads are added or modified:
  - Draft changes in `packages/contracts/openapi/openapi.json`.
  - Validate field types and UUID identifiers.
  - Scribe corresponding Pydantic schema changes for `services/ml-api/app/schemas/`.

### Phase 4: Risk & Edge Case Assessment
- Assess cold-start implications on blitz.cloud free tier (10–25s delay on idle containers).
- Verify student data pseudonymization (`student_id_pseudo`).
- Check that delayed evaluation items (7-day retention post-test) remain strictly quarantined.

### Phase 5: Acceptance Criteria & Test Plan Definition
- Define explicit Given-When-Then criteria.
- Specify required unit and integration tests (`pytest`, TypeScript compiler).

## 3. Definition of Done
- Feature plan documented with affected paths and interface diffs.
- Architectural boundary checklist verified.
- Test plan established with zero regressions on existing contracts.
