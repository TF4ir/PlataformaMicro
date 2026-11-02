---
name: testing-security
description: Security verification, Row Level Security penetration testing, JWT cryptographic validation, and automated contract AST verification.
---
# Testing & Security Skill

## 1. Overview & Role
Governs automated verification, security audits, penetration testing of RLS policies, and contract schema consistency checks across the monorepo.

## 2. Testing Protocols
- **RLS Boundary Penetration Testing**: Test that anonymous and cross-student tokens cannot read or mutate foreign records in Supabase.
- **Answer Events Immutability Tests**: Execute negative assertions ensuring `UPDATE` and `DELETE` on `answer_events` raise Postgres permission errors.
- **JWT Cryptographic Verification**: Verify Supabase JWT signatures, claims, and `aud` field in FastAPI middleware.
- **Contract Schema Consistency**: Validate that field names, types, and nullability match identically between SQL DDL, OpenAPI JSON, Pydantic schemas, and TypeScript interfaces.
- **Phase 0 Negative Testing**: Verify absence of UI wireframes, components, or user flows in `apps/web/`.

## 3. Cross-References
- `scripts/verify-phase0.py`
- `supabase/tests/`
- `services/ml-api/tests/`
- `docs/architecture/security.md`
