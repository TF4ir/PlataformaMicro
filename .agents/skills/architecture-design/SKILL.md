---
name: architecture-design
description: Architecture design, monorepo cohesion, C4 model diagrams, ADR governance, and schema/contract synchronization.
---
# Architecture Design Skill

## 1. Overview & Role
Guides architectural design, monorepo cohesion, and contract synchronization across presentation (`apps/web`), persistence (`supabase`), inference (`services/ml-api`), and experimentation (`ml`).

## 2. Responsibilities
- Maintain C4 architecture diagrams and component interactions.
- Manage Architectural Decision Records (ADRs) under `docs/architecture/adr/`.
- Validate zero coupling between presentation and ML binaries.
- Ensure OpenAPI schemas in `packages/contracts/openapi/` mirror PostgreSQL DDL and Pydantic models without drift.

## 3. Cross-References & Tools
- `docs/architecture/overview.md`
- `docs/architecture/api-contracts.md`
- `packages/contracts/openapi/openapi.json`
- ADR-0001, ADR-0002, ADR-0003
