# Workflow: Implement Feature

## 1. Objective & Scope
Standard execution protocol for implementing code changes across frontend (`apps/web/`), backend microservices (`services/ml-api/`), or database layers (`supabase/`).

## 2. Execution Phases

### Phase 1: Pre-flight Verification
- Review relevant subsystem `AGENTS.md` and associated rules in `.agents/rules/`.
- Ensure clean workspace state and sync against base branch.
- Confirm contract changes have been recorded in `packages/contracts/openapi/openapi.json`.

### Phase 2: Contracts and Schema Updates
- For database updates: author idempotent migration script in `supabase/migrations/`.
- For backend updates: implement Pydantic v2 schemas in `services/ml-api/app/schemas/`.
- For frontend updates: generate or update TypeScript types from contracts.

### Phase 3: Core Implementation (Hexagonal Architecture)
- Apply minimal-change edits.
- Implement domain models and interfaces in `services/ml-api/app/prediction/` or `app/adaptation/`.
- Implement use-case services in `services/ml-api/app/services/`.
- Implement repository data access in `services/ml-api/app/repositories/`.
- Wire HTTP routes in `services/ml-api/app/api/v1/` with mandatory idempotency key validation on mutation routes.

### Phase 4: Automated Testing
- Write behavior-driven tests under `services/ml-api/tests/` or `supabase/tests/`.
- Run tests (`pytest -v`) to ensure 100% pass rate.
- Validate error paths (`insufficient_history` fallback, duplicate idempotency keys).

### Phase 5: Static Analysis & Type Checking
- Run `mypy --strict` on Python packages.
- Run `tsc --noEmit` on TypeScript packages.
- Format code according to project style standards.

## 3. Definition of Done
- All new and existing automated tests pass.
- Type check clean with zero errors.
- No violation of subsystem boundaries or Phase 0 UI exclusions.
