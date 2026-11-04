-- ====================================================================
-- Migration: 20261103040000_content_exposure_events_m52.sql
-- Description: M5.2-B Content Exposure and Study Telemetry
-- 
-- Persists student initial study and review exposures on microcontents,
-- complementing answer_events (retrieval practice) to enable complete
-- longitudinal knowledge tracing and memory retention modeling.
-- ====================================================================

-- 1. Create Enums for Exposure Type and Completion Status
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'exposure_type_enum') THEN
        CREATE TYPE exposure_type_enum AS ENUM (
            'initial_study',
            'review_study',
            'remedial_reading',
            'diagnostic_exposure'
        );
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'exposure_completion_status_enum') THEN
        CREATE TYPE exposure_completion_status_enum AS ENUM (
            'completed',
            'partial',
            'abandoned'
        );
    END IF;
END $$;

-- 2. Create Table: content_exposure_events
CREATE TABLE IF NOT EXISTS content_exposure_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES profiles(id) ON DELETE RESTRICT,
    student_id_pseudo UUID NOT NULL,
    microcontent_id UUID NOT NULL REFERENCES microcontents(id) ON DELETE RESTRICT,
    knowledge_component_id UUID NOT NULL REFERENCES knowledge_components(id) ON DELETE RESTRICT,
    exposure_type exposure_type_enum NOT NULL DEFAULT 'initial_study',
    started_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ,
    duration_seconds NUMERIC(8, 2) NOT NULL DEFAULT 0.0 CHECK (duration_seconds >= 0.0),
    active_reading_seconds NUMERIC(8, 2) CHECK (active_reading_seconds IS NULL OR active_reading_seconds >= 0.0),
    completion_status exposure_completion_status_enum NOT NULL DEFAULT 'completed',
    session_id UUID NOT NULL,
    idempotency_key UUID UNIQUE NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    event_timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_exposure_completed_at CHECK (completed_at IS NULL OR completed_at >= started_at)
);

-- 3. Create Performance Indexes for KT Pipeline and Multitenant Queries
CREATE INDEX IF NOT EXISTS idx_exposure_student_kc 
    ON content_exposure_events (student_id, knowledge_component_id, event_timestamp ASC);

CREATE INDEX IF NOT EXISTS idx_exposure_microcontent 
    ON content_exposure_events (microcontent_id);

CREATE INDEX IF NOT EXISTS idx_exposure_session 
    ON content_exposure_events (session_id);

CREATE INDEX IF NOT EXISTS idx_exposure_tenant 
    ON content_exposure_events (tenant_id);

CREATE INDEX IF NOT EXISTS idx_exposure_pseudo 
    ON content_exposure_events (student_id_pseudo);

-- 4. Strict Immutability and Append-Only Protection (Defense in Depth)
CREATE OR REPLACE FUNCTION prevent_content_exposure_mutation()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'content_exposure_events table is strictly append-only. Operations of type % are permanently forbidden.', TG_OP
        USING ERRCODE = '55000';
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_prevent_content_exposure_mutation ON content_exposure_events;
CREATE TRIGGER trg_prevent_content_exposure_mutation
    BEFORE DELETE OR UPDATE ON content_exposure_events
    FOR EACH ROW
    EXECUTE FUNCTION prevent_content_exposure_mutation();

DROP TRIGGER IF EXISTS trg_prevent_content_exposure_truncate ON content_exposure_events;
CREATE TRIGGER trg_prevent_content_exposure_truncate
    BEFORE TRUNCATE ON content_exposure_events
    FOR EACH STATEMENT
    EXECUTE FUNCTION prevent_content_exposure_mutation();

-- 5. Privilege Hardening
REVOKE UPDATE, DELETE, TRUNCATE ON content_exposure_events FROM anon, authenticated;
GRANT SELECT, INSERT ON content_exposure_events TO authenticated;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'ml_api_worker') THEN
        GRANT SELECT, INSERT ON content_exposure_events TO ml_api_worker;
    END IF;
END $$;

-- 6. Row Level Security (RLS) Configuration
ALTER TABLE content_exposure_events ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "content_exposure_events_select" ON content_exposure_events;
CREATE POLICY "content_exposure_events_select" ON content_exposure_events
    FOR SELECT
    USING (
        student_id = (SELECT auth.uid())
        OR (SELECT is_teacher_of_student(content_exposure_events.student_id))
        OR ((SELECT current_user_role()) = ANY (ARRAY['super_admin'::user_role, 'admin'::user_role]))
    );

DROP POLICY IF EXISTS "content_exposure_events_insert" ON content_exposure_events;
CREATE POLICY "content_exposure_events_insert" ON content_exposure_events
    FOR INSERT
    WITH CHECK (
        student_id = (SELECT auth.uid())
    );
