---
name: fastapi-development
description: Hexagonal FastAPI microservice development, Pydantic v2 validation, asyncpg integration, blitz.cloud cold-start mitigation, and idempotency handling.
---
# FastAPI Development Skill

## 1. Overview & Role
Guides development of `services/ml-api/` for asynchronous probabilistic inference and pedagogical recommendation services.

## 2. Architectural Guidelines
- **Clean / Hexagonal Structure**: Clear separation across `core/`, `api/v1/`, `schemas/`, `services/`, `repositories/`, `prediction/`, and `adaptation/`.
- **Idempotency Enforcement**: Validate `X-Idempotency-Key` on `/api/v1/learning/attempts/{id}/answers` to eliminate duplicate response recordings.
- **Insufficient History Graceful Degradation**: When a student has fewer attempts than required for inference, return `prediction_status: "insufficient_history"` and transition cleanly to `rule_based_fallback`.
- **Cold-Start Resilience**: Provide `POST /api/v1/health/warmup` endpoint to prime containers before classroom sessions on blitz.cloud free tier.
- **Strict Typing**: 100% type annotations validated by MyPy in strict mode and Pydantic v2 schemas.

## 3. Cross-References
- `services/ml-api/AGENTS.md`
- `.agents/rules/backend.md`
- `.agents/skills/fastapi-templates/`
