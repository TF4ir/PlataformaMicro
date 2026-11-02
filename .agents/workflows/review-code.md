# Workflow: Review Code

## 1. Objective & Scope
Peer review and quality assurance protocol for verifying changes across architecture, security, data integrity, and educational research validity before integration.

## 2. Review Checklists

### 1. Architectural & Subsystem Boundaries
- [ ] Frontend (`apps/web/`) contains zero ML imports (`scikit-learn`, `numpy`, `.pkl`).
- [ ] No direct database access or service role key usage in browser code.
- [ ] In Phase 0: strictly NO UI wireframes or interactive React components in `apps/web/`.
- [ ] FastAPI service treats Supabase as sole source of truth (no local DDL ownership).

### 2. Database & Row Level Security (RLS)
- [ ] 100% of newly introduced tables have RLS enabled (`ALTER TABLE ... ENABLE ROW LEVEL SECURITY`).
- [ ] Granular policies exist for `anon`, `authenticated`, and service roles.
- [ ] Table `answer_events` has strictly revoked `UPDATE` and `DELETE` permissions.
- [ ] All primary keys are UUIDs generated via `gen_random_uuid()`.

### 3. Contract & Type Consistency
- [ ] Data entity attributes match identically across PostgreSQL DDL, OpenAPI JSON, Pydantic schemas, and TypeScript interfaces.
- [ ] All timestamps use `timestamptz` / ISO-8601 UTC strings.
- [ ] Mutation endpoints require `X-Idempotency-Key` header.

### 4. Scientific Rigor & Ethics (Ley N° 29733)
- [ ] Complete absence of student personally identifiable information (PII).
- [ ] Student Group-K-Fold validation applied without data leakage.
- [ ] Quarantined 7-day delayed post-test questions are strictly excluded from practice pools.
- [ ] Model metrics and predictions are genuinely computed (no hardcoded outputs).

## 3. Verdict
- **APPROVED**: All checklist criteria satisfied; code passes tests and type checks.
- **CHANGES_REQUESTED**: Specific line items identified with remediation guidance.
- **REJECTED**: Architectural boundary violation, security vulnerability, or integrity breach detected.
