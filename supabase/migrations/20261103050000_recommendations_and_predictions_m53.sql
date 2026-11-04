-- ====================================================================
-- Migration: 20261103050000_recommendations_and_predictions_m53.sql
-- Description: M5.3 Spaced Repetition Recommendations & Retention Predictions
-- 
-- Extends recommendations and predictions tables for temporal retention inference,
-- 24h anti-fatigue frequency capping, decision audit trails, and student completion.
-- ====================================================================

-- 1. Extend recommendation_status_enum with 'expired'
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_enum 
        WHERE enumtypid = 'recommendation_status_enum'::regtype 
        AND enumlabel = 'expired'
    ) THEN
        ALTER TYPE recommendation_status_enum ADD VALUE 'expired';
    END IF;
END $$;

-- 2. Extend predictions table with critical forgetting time and tau threshold
ALTER TABLE predictions 
    ADD COLUMN IF NOT EXISTS predicted_forgetting_time_seconds NUMERIC(12, 2),
    ADD COLUMN IF NOT EXISTS tau_threshold NUMERIC(4, 3) NOT NULL DEFAULT 0.650;

-- 3. Extend recommendations table with policy metadata, scheduling, cooldown, and idempotency
ALTER TABLE recommendations
    ADD COLUMN IF NOT EXISTS policy_name TEXT NOT NULL DEFAULT 'preventive_spaced_repetition',
    ADD COLUMN IF NOT EXISTS policy_version TEXT NOT NULL DEFAULT '1.0.0',
    ADD COLUMN IF NOT EXISTS scheduled_for TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS cooldown_until TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS completed_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS expires_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS idempotency_key UUID UNIQUE;

-- 4. Performance Indexes for 24h Anti-Fatigue Moving Window and Student Lookups
CREATE INDEX IF NOT EXISTS idx_recommendations_student_kc_created 
    ON recommendations (student_id, knowledge_component_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_recommendations_student_status_pending 
    ON recommendations (student_id, status) WHERE status = 'pending';

CREATE INDEX IF NOT EXISTS idx_recommendations_idempotency 
    ON recommendations (idempotency_key) WHERE idempotency_key IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_predictions_student_kc_created 
    ON predictions (student_id, knowledge_component_id, created_at DESC);

-- 5. RLS Policies and Privilege Hardening
ALTER TABLE recommendations ENABLE ROW LEVEL SECURITY;
ALTER TABLE predictions ENABLE ROW LEVEL SECURITY;
ALTER TABLE model_versions ENABLE ROW LEVEL SECURITY;

-- Recommendations: Student can insert own or update status to 'completed'
DROP POLICY IF EXISTS "recommendations_insert" ON recommendations;
CREATE POLICY "recommendations_insert" ON recommendations
    FOR INSERT
    WITH CHECK (
        student_id = (SELECT auth.uid())
        OR (SELECT current_user_role() = ANY (ARRAY['super_admin'::user_role, 'admin'::user_role]))
    );

DROP POLICY IF EXISTS "recommendations_update" ON recommendations;
CREATE POLICY "recommendations_update" ON recommendations
    FOR UPDATE
    USING (
        student_id = (SELECT auth.uid())
        OR (SELECT is_teacher_of_student(recommendations.student_id))
        OR (SELECT current_user_role() = ANY (ARRAY['super_admin'::user_role, 'admin'::user_role]))
    );

-- Predictions: Insert policy
DROP POLICY IF EXISTS "predictions_insert" ON predictions;
CREATE POLICY "predictions_insert" ON predictions
    FOR INSERT
    WITH CHECK (
        student_id = (SELECT auth.uid())
        OR (SELECT current_user_role() = ANY (ARRAY['super_admin'::user_role, 'admin'::user_role]))
    );

-- Model Versions: Read for all authenticated, write for admins
DROP POLICY IF EXISTS "model_versions_select" ON model_versions;
CREATE POLICY "model_versions_select" ON model_versions
    FOR SELECT
    USING (true);

-- Privileges
GRANT SELECT, INSERT, UPDATE ON recommendations TO authenticated;
GRANT SELECT, INSERT ON predictions TO authenticated;
GRANT SELECT ON model_versions TO authenticated;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'ml_api_worker') THEN
        GRANT SELECT, INSERT, UPDATE ON recommendations TO ml_api_worker;
        GRANT SELECT, INSERT ON predictions TO ml_api_worker;
        GRANT SELECT ON model_versions TO ml_api_worker;
    END IF;
END $$;
