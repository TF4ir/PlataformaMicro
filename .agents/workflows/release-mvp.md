# Workflow: Release MVP

## 1. Objective & Scope
Pre-release quality audit, boundary verification, and tagging protocol for shipping Phase 0 and subsequent releases of the Plataforma de Microaprendizaje Adaptativo.

## 2. Release Gating Protocol

### Gate 1: Automated Verification Suite
- Execute the master verification suite:
  ```bash
  python3 scripts/verify-phase0.py
  ```
- Confirm execution completes with exit code 0 and zero errors or warnings.

### Gate 2: Phase 0 Boundary Compliance Audit
- Execute strict absence check for UI wireframes or interactive React components:
  ```bash
  find apps/web/src/components/ui/ -type f ! -name ".gitkeep" | wc -l
  # Must return 0
  ```
- Confirm `apps/web/` contains only scaffolding configuration and typed interfaces.

### Gate 3: Schema and Contract Synchronization
- Confirm consistency across PostgreSQL DDL, OpenAPI JSON (`packages/contracts/openapi/openapi.json`), Pydantic schemas, and TypeScript interfaces.
- Verify zero field name or type discrepancies.

### Gate 4: Security and Secrets Hygiene
- Audit git status to ensure zero `.env` files or credentials are tracked.
- Confirm only `.env.example` is committed with placeholder values.
- Verify that `REVOKE UPDATE, DELETE ON answer_events` is intact in migrations.

### Gate 5: Container Build & Health Probe
- Build Docker container for `services/ml-api`:
  ```bash
  docker build -f services/ml-api/Dockerfile -t ml-api:local .
  ```
- Verify `/api/v1/health` and `/api/v1/health/warmup` respond with HTTP 200.

### Gate 6: Git Tagging & Release Documentation
- Create signed Git release tag:
  ```bash
  git tag -a v0.1.0-phase0 -m "Release v0.1.0-phase0: Monorepo scaffolding, agent governance, and formal contracts"
  ```
- Document release notes with verified test logs and audit attestation.

## 3. Definition of Done
- All 6 quality gates pass with zero exceptions.
- Release tag applied and audit report published.
