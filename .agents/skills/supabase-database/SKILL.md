---
name: supabase-database
description: PostgreSQL 15+ schema design, idempotent migrations, Row Level Security (RLS) policies, and append-only event stores in Supabase.
---
# Supabase Database Skill

## 1. Overview & Role
Governs the persistence layer (`supabase/`), including PostgreSQL 15+ database design, Supabase Auth integration, and declarative Row Level Security (RLS) enforcement.

## 2. Key Standards
- **UUID Primary Keys**: Every table uses `id UUID DEFAULT gen_random_uuid() PRIMARY KEY`.
- **100% RLS Enforcement**: Every table must execute `ALTER TABLE <name> ENABLE ROW LEVEL SECURITY;`.
- **Granular Least Privilege**: Student queries constrained by `auth.uid() = student_id`; teachers constrained to their assigned sections.
- **Append-Only Event Store**: `answer_events` is immutable. Explicitly revoke `UPDATE` and `DELETE` privileges for authenticated and anon roles.
- **Minor Protection**: Personal identifiable information in `profiles` is strictly decoupled from research events via `student_id_pseudo`.

## 3. Cross-References
- `supabase/AGENTS.md`
- `.agents/rules/database.md`
- `.agents/skills/supabase/`
- `.agents/skills/supabase-postgres-best-practices/`
