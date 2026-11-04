-- ============================================================================
-- PLATAFORMA DE MICROAPRENDIZAJE ADAPTATIVO
-- MIGRACIÓN INCREMENTAL: Flujo de Aprendizaje, Cuestionarios y answer_events (Hito M4)
-- Version: 20261103030000
-- ============================================================================

-- 1. Tipos Enumerados (ENUMs)
DO $$ BEGIN
    ALTER TYPE activity_type_enum ADD VALUE IF NOT EXISTS 'formative';
    ALTER TYPE activity_type_enum ADD VALUE IF NOT EXISTS 'summative';
    ALTER TYPE activity_type_enum ADD VALUE IF NOT EXISTS 'remediation';
    ALTER TYPE activity_type_enum ADD VALUE IF NOT EXISTS 'retention_check';
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE activity_status_enum AS ENUM (
        'draft',
        'published',
        'closed'
    );
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE feedback_policy_enum AS ENUM (
        'immediate_with_explanation',
        'upon_completion',
        'after_deadline'
    );
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE attempt_status_enum AS ENUM (
        'in_progress',
        'completed',
        'abandoned'
    );
EXCEPTION WHEN duplicate_object THEN null;
END $$;

-- 2. Modificaciones a la tabla: activities
ALTER TABLE activities
    ADD COLUMN IF NOT EXISTS created_by UUID REFERENCES profiles(id) ON DELETE RESTRICT,
    ADD COLUMN IF NOT EXISTS status activity_status_enum NOT NULL DEFAULT 'draft',
    ADD COLUMN IF NOT EXISTS feedback_policy feedback_policy_enum NOT NULL DEFAULT 'immediate_with_explanation',
    ADD COLUMN IF NOT EXISTS published_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS available_from TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS available_until TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS max_attempts INTEGER NOT NULL DEFAULT 1 CHECK (max_attempts >= 1),
    ADD COLUMN IF NOT EXISTS time_limit_minutes INTEGER CHECK (time_limit_minutes IS NULL OR time_limit_minutes > 0),
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now();

CREATE INDEX IF NOT EXISTS idx_activities_course_status ON activities(course_id, status);
CREATE INDEX IF NOT EXISTS idx_activities_tenant_status ON activities(tenant_id, status);

-- 3. Tabla: activity_sections (Secciones Destinatarias de Actividades)
CREATE TABLE IF NOT EXISTS activity_sections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    activity_id UUID NOT NULL REFERENCES activities(id) ON DELETE CASCADE,
    section_id UUID NOT NULL REFERENCES sections(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(activity_id, section_id)
);

CREATE INDEX IF NOT EXISTS idx_activity_sections_activity ON activity_sections(activity_id);
CREATE INDEX IF NOT EXISTS idx_activity_sections_section ON activity_sections(section_id);

-- 4. Modificaciones a la tabla: quiz_attempts
ALTER TABLE quiz_attempts
    ADD COLUMN IF NOT EXISTS student_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
    ADD COLUMN IF NOT EXISTS attempt_number INTEGER NOT NULL DEFAULT 1 CHECK (attempt_number >= 1),
    ADD COLUMN IF NOT EXISTS status attempt_status_enum NOT NULL DEFAULT 'in_progress',
    ADD COLUMN IF NOT EXISTS total_questions INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS correct_answers INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS idempotency_key UUID UNIQUE,
    ADD COLUMN IF NOT EXISTS submitted_at TIMESTAMPTZ;

-- Backfill student_id en quiz_attempts existentes desde enrollments
UPDATE quiz_attempts qa
SET student_id = e.student_id
FROM enrollments e
WHERE qa.enrollment_id = e.id
  AND qa.student_id IS NULL;

CREATE INDEX IF NOT EXISTS idx_quiz_attempts_student ON quiz_attempts(student_id);
CREATE INDEX IF NOT EXISTS idx_quiz_attempts_activity_student ON quiz_attempts(activity_id, student_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_quiz_attempts_active_unique ON quiz_attempts(activity_id, student_id) WHERE status = 'in_progress';

-- 5. Modificaciones a la tabla: answer_events
ALTER TABLE answer_events
    ADD COLUMN IF NOT EXISTS activity_id UUID REFERENCES activities(id) ON DELETE RESTRICT,
    ADD COLUMN IF NOT EXISTS course_id UUID REFERENCES courses(id) ON DELETE RESTRICT,
    ADD COLUMN IF NOT EXISTS question_sequence INTEGER NOT NULL DEFAULT 1,
    ADD COLUMN IF NOT EXISTS response_time_ms INTEGER CHECK (response_time_ms IS NULL OR response_time_ms > 0);

-- Backfill activity_id y course_id en answer_events existentes
UPDATE answer_events ae
SET activity_id = qa.activity_id,
    course_id = a.course_id
FROM quiz_attempts qa
JOIN activities a ON a.id = qa.activity_id
WHERE ae.attempt_id = qa.id
  AND ae.activity_id IS NULL;

CREATE INDEX IF NOT EXISTS idx_answer_events_activity ON answer_events(activity_id);
CREATE INDEX IF NOT EXISTS idx_answer_events_course ON answer_events(course_id);

-- 6. Inmutabilidad Estricta a Nivel de Trigger (Append-Only Guard)
CREATE OR REPLACE FUNCTION prevent_answer_events_mutation()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'answer_events table is strictly append-only; UPDATE and DELETE operations are forbidden.'
        USING ERRCODE = '55000';
END;
$$;

DROP TRIGGER IF EXISTS trg_prevent_answer_events_mutation ON answer_events;
CREATE TRIGGER trg_prevent_answer_events_mutation
    BEFORE UPDATE OR DELETE ON answer_events
    FOR EACH ROW
    EXECUTE FUNCTION prevent_answer_events_mutation();

DROP TRIGGER IF EXISTS trg_prevent_answer_events_truncate ON answer_events;
CREATE TRIGGER trg_prevent_answer_events_truncate
    BEFORE TRUNCATE ON answer_events
    FOR EACH STATEMENT
    EXECUTE FUNCTION prevent_answer_events_mutation();

-- Revocar explícitamente UPDATE, DELETE y TRUNCATE en answer_events
REVOKE UPDATE, DELETE, TRUNCATE ON answer_events FROM anon, authenticated;

-- 7. Funciones Auxiliares de RLS
CREATE OR REPLACE FUNCTION is_student_enrolled_in_activity(p_student_id UUID, p_activity_id UUID)
RETURNS BOOLEAN LANGUAGE sql STABLE SECURITY DEFINER SET search_path = '' AS $$
    SELECT EXISTS (
        SELECT 1
        FROM public.activity_sections acts
        JOIN public.enrollments e ON e.section_id = acts.section_id
        WHERE acts.activity_id = p_activity_id
          AND e.student_id = p_student_id
    );
$$;

-- 8. Políticas Row Level Security (RLS)

-- Habilitar RLS en tablas relevantes
ALTER TABLE activities ENABLE ROW LEVEL SECURITY;
ALTER TABLE activity_sections ENABLE ROW LEVEL SECURITY;
ALTER TABLE activity_questions ENABLE ROW LEVEL SECURITY;
ALTER TABLE quiz_attempts ENABLE ROW LEVEL SECURITY;
ALTER TABLE answer_events ENABLE ROW LEVEL SECURITY;

-- Políticas para activities
DO $$ BEGIN
    DROP POLICY IF EXISTS "activities_select_policy" ON activities;
    CREATE POLICY "activities_select_policy" ON activities
        FOR SELECT USING (
            is_teacher_of_course(course_id)
            OR (SELECT current_user_role()) IN ('super_admin', 'admin')
            OR (
                status = 'published'
                AND is_active = true
                AND is_student_enrolled_in_activity((SELECT auth.uid()), id)
            )
        );
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    DROP POLICY IF EXISTS "activities_insert_teacher" ON activities;
    CREATE POLICY "activities_insert_teacher" ON activities
        FOR INSERT WITH CHECK (
            is_teacher_of_course(course_id)
            OR (SELECT current_user_role()) IN ('super_admin', 'admin')
        );
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    DROP POLICY IF EXISTS "activities_update_teacher" ON activities;
    CREATE POLICY "activities_update_teacher" ON activities
        FOR UPDATE USING (
            is_teacher_of_course(course_id)
            OR (SELECT current_user_role()) IN ('super_admin', 'admin')
        );
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    DROP POLICY IF EXISTS "activities_delete_teacher" ON activities;
    CREATE POLICY "activities_delete_teacher" ON activities
        FOR DELETE USING (
            status = 'draft'
            AND (
                is_teacher_of_course(course_id)
                OR (SELECT current_user_role()) IN ('super_admin', 'admin')
            )
        );
EXCEPTION WHEN duplicate_object THEN null;
END $$;

-- Políticas para activity_sections
DO $$ BEGIN
    DROP POLICY IF EXISTS "activity_sections_select" ON activity_sections;
    CREATE POLICY "activity_sections_select" ON activity_sections
        FOR SELECT USING (
            EXISTS (
                SELECT 1 FROM public.activities a 
                WHERE a.id = activity_sections.activity_id 
                  AND (is_teacher_of_course(a.course_id) OR (SELECT current_user_role()) IN ('super_admin', 'admin'))
            )
            OR EXISTS (
                SELECT 1 FROM public.enrollments e 
                WHERE e.section_id = activity_sections.section_id 
                  AND e.student_id = (SELECT auth.uid())
            )
        );
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    DROP POLICY IF EXISTS "activity_sections_manage_teacher" ON activity_sections;
    CREATE POLICY "activity_sections_manage_teacher" ON activity_sections
        FOR ALL USING (
            EXISTS (
                SELECT 1 FROM public.activities a 
                WHERE a.id = activity_sections.activity_id 
                  AND (is_teacher_of_course(a.course_id) OR (SELECT current_user_role()) IN ('super_admin', 'admin'))
            )
        );
EXCEPTION WHEN duplicate_object THEN null;
END $$;

-- Políticas para activity_questions
DO $$ BEGIN
    DROP POLICY IF EXISTS "activity_questions_select" ON activity_questions;
    CREATE POLICY "activity_questions_select" ON activity_questions
        FOR SELECT USING (
            EXISTS (
                SELECT 1 FROM public.activities a 
                WHERE a.id = activity_questions.activity_id 
                  AND (
                      is_teacher_of_course(a.course_id)
                      OR (SELECT current_user_role()) IN ('super_admin', 'admin')
                      OR (a.status = 'published' AND a.is_active = true AND is_student_enrolled_in_activity((SELECT auth.uid()), a.id))
                  )
            )
        );
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    DROP POLICY IF EXISTS "activity_questions_manage_teacher" ON activity_questions;
    CREATE POLICY "activity_questions_manage_teacher" ON activity_questions
        FOR ALL USING (
            EXISTS (
                SELECT 1 FROM public.activities a 
                WHERE a.id = activity_questions.activity_id 
                  AND (is_teacher_of_course(a.course_id) OR (SELECT current_user_role()) IN ('super_admin', 'admin'))
            )
        );
EXCEPTION WHEN duplicate_object THEN null;
END $$;

-- Políticas para quiz_attempts
DO $$ BEGIN
    DROP POLICY IF EXISTS "attempts_student_access" ON quiz_attempts;
    CREATE POLICY "attempts_student_access" ON quiz_attempts
        FOR SELECT USING (
            student_id = (SELECT auth.uid())
            OR EXISTS (
                SELECT 1 FROM public.enrollments e 
                WHERE e.id = quiz_attempts.enrollment_id 
                  AND e.student_id = (SELECT auth.uid())
            )
            OR (SELECT current_user_role()) IN ('super_admin', 'admin')
            OR EXISTS (
                SELECT 1 FROM public.enrollments e 
                JOIN public.sections s ON s.id = e.section_id 
                WHERE e.id = quiz_attempts.enrollment_id 
                  AND s.teacher_id = (SELECT auth.uid())
            )
        );
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    DROP POLICY IF EXISTS "attempts_insert_student" ON quiz_attempts;
    CREATE POLICY "attempts_insert_student" ON quiz_attempts
        FOR INSERT WITH CHECK (
            student_id = (SELECT auth.uid())
            OR EXISTS (
                SELECT 1 FROM public.enrollments e 
                WHERE e.id = enrollment_id 
                  AND e.student_id = (SELECT auth.uid())
            )
        );
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    DROP POLICY IF EXISTS "attempts_update_student" ON quiz_attempts;
    CREATE POLICY "attempts_update_student" ON quiz_attempts
        FOR UPDATE USING (
            student_id = (SELECT auth.uid())
            OR EXISTS (
                SELECT 1 FROM public.enrollments e 
                WHERE e.id = enrollment_id 
                  AND e.student_id = (SELECT auth.uid())
            )
            OR (SELECT current_user_role()) IN ('super_admin', 'admin')
        );
EXCEPTION WHEN duplicate_object THEN null;
END $$;

-- Permisos y Políticas para rol ml_api_worker (si existe)
DO $$ BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'ml_api_worker') THEN
        GRANT SELECT, INSERT, UPDATE, DELETE ON public.activities TO ml_api_worker;
        GRANT SELECT, INSERT, UPDATE, DELETE ON public.activity_sections TO ml_api_worker;
        GRANT SELECT, INSERT, UPDATE, DELETE ON public.activity_questions TO ml_api_worker;
        GRANT SELECT, INSERT, UPDATE ON public.quiz_attempts TO ml_api_worker;
        GRANT SELECT, INSERT ON public.answer_events TO ml_api_worker;

        DROP POLICY IF EXISTS "ml_worker_activities_policy" ON activities;
        CREATE POLICY "ml_worker_activities_policy" ON activities
            FOR ALL TO ml_api_worker USING (true) WITH CHECK (true);

        DROP POLICY IF EXISTS "ml_worker_activity_sections_policy" ON activity_sections;
        CREATE POLICY "ml_worker_activity_sections_policy" ON activity_sections
            FOR ALL TO ml_api_worker USING (true) WITH CHECK (true);

        DROP POLICY IF EXISTS "ml_worker_activity_questions_policy" ON activity_questions;
        CREATE POLICY "ml_worker_activity_questions_policy" ON activity_questions
            FOR ALL TO ml_api_worker USING (true) WITH CHECK (true);

        DROP POLICY IF EXISTS "ml_worker_quiz_attempts_policy" ON quiz_attempts;
        CREATE POLICY "ml_worker_quiz_attempts_policy" ON quiz_attempts
            FOR ALL TO ml_api_worker USING (true) WITH CHECK (true);

        DROP POLICY IF EXISTS "ml_worker_answer_events_policy" ON answer_events;
        CREATE POLICY "ml_worker_answer_events_policy" ON answer_events
            FOR ALL TO ml_api_worker USING (true) WITH CHECK (true);
    END IF;
END $$;
