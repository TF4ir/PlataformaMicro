# Workflow: Database Migration

## 1. Objective & Scope
Standard protocol for authoring, validating, and applying idempotent PostgreSQL migrations within Supabase (`supabase/migrations/`).

## 2. Migration Protocol

### Step 1: Migration Naming Convention
- File name must follow timestamp pattern: `supabase/migrations/<YYYYMMDDHHMMSS>_<descriptive_slug>.sql`.

### Step 2: Idempotent DDL Authoring
- Ensure all extension creations use `CREATE EXTENSION IF NOT EXISTS "uuid-ossp";` or `pgcrypto`.
- All table primary keys must use `id UUID DEFAULT gen_random_uuid() PRIMARY KEY`.
- Every table must include audit timestamps:
  ```sql
  created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
  ```
- Declare explicit foreign key constraints with `ON DELETE RESTRICT` (for critical learning history) or `CASCADE` (for child entities).

### Step 3: Security & RLS Declarations
- Explicitly enable RLS on every table:
  ```sql
  ALTER TABLE <table_name> ENABLE ROW LEVEL SECURITY;
  ```
- Author distinct policies for student access (`auth.uid() = student_id`) and teacher access (via section enrollments).
- For `answer_events`, ensure append-only immutability:
  ```sql
  REVOKE UPDATE, DELETE ON answer_events FROM anon, authenticated;
  ```

### Step 4: Indexing & Performance
- Index foreign key columns to avoid seq scans during joins.
- Create composite indexes on time-series lookup queries (e.g., `(student_id, knowledge_component_id, event_timestamp DESC)`).

### Step 5: Verification & Contract Generation
- Test migration locally via Supabase CLI (`supabase db reset` or `supabase migration up`).
- Regenerate TypeScript types to maintain contract synchronization (`supabase gen types typescript`).

## 3. Definition of Done
- Migration executes cleanly forward and rollback scripts tested.
- RLS verified with positive and negative permission assertions.
