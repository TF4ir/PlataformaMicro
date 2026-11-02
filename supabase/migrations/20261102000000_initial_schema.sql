-- ============================================================================
-- PLATAFORMA DE MICROAPRENDIZAJE ADAPTATIVO (NEXO) - ESQUEMA DE BASE DE DATOS DDL
-- Multi-Tenancy nativo, Row Level Security (RLS) e Inmutabilidad de Auditoría
-- ============================================================================

-- 0. Extensiones Requeridas
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================================
-- 1. Tipos Enumerados (ENUMs)
-- ============================================================================
DO $$ BEGIN
    CREATE TYPE user_role AS ENUM (
        'super_admin',
        'admin',
        'teacher',
        'student',
        'researcher'
    );
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE activity_type_enum AS ENUM (
        'diagnostic',
        'practice',
        'immediate_assessment',
        'delayed_assessment'
    );
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE content_type_enum AS ENUM (
        'text_summary',
        'infographic_card',
        'concept_map'
    );
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE risk_level_enum AS ENUM (
        'low',
        'medium',
        'high',
        'critical'
    );
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE prediction_status_enum AS ENUM (
        'valid',
        'insufficient_history',
        'degraded_fallback'
    );
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE recommendation_method_enum AS ENUM (
        'predictive_model',
        'rule_based_fallback',
        'teacher_assigned'
    );
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE recommendation_status_enum AS ENUM (
        'pending',
        'delivered',
        'completed',
        'dismissed'
    );
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE assignment_status_enum AS ENUM (
        'assigned',
        'in_progress',
        'completed',
        'expired'
    );
EXCEPTION WHEN duplicate_object THEN null;
END $$;

-- ============================================================================
-- 2. Entidades de Tenencia, Identidad y Usuarios
-- ============================================================================

CREATE TABLE IF NOT EXISTS tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    domain TEXT,
    is_active BOOLEAN NOT NULL DEFAULT true,
    settings JSONB NOT NULL DEFAULT '{"risk_threshold": 0.65, "cold_start_kcs": 3}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    student_code TEXT UNIQUE, -- Código institucional opcional para login (ej. EST-501)
    full_name TEXT NOT NULL,
    role user_role NOT NULL DEFAULT 'student',
    avatar_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Tabla para recuperación de contraseñas de menores sin correo real (Asistido por docente / PIN temporal)
CREATE TABLE IF NOT EXISTS auth_recovery_pins (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    pin_hash TEXT NOT NULL,
    created_by UUID NOT NULL REFERENCES profiles(id),
    expires_at TIMESTAMPTZ NOT NULL DEFAULT (now() + interval '30 minutes'),
    used_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================================
-- 3. Estructura Pedagógica Agnóstica
-- ============================================================================

CREATE TABLE IF NOT EXISTS courses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    code TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(tenant_id, code)
);

CREATE TABLE IF NOT EXISTS sections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE RESTRICT,
    teacher_id UUID NOT NULL REFERENCES profiles(id) ON DELETE RESTRICT,
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS enrollments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    section_id UUID NOT NULL REFERENCES sections(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    student_id_pseudo UUID NOT NULL DEFAULT gen_random_uuid(),
    enrolled_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(section_id, student_id),
    UNIQUE(tenant_id, student_id_pseudo)
);

CREATE TABLE IF NOT EXISTS units (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    order_index INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS knowledge_components (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    unit_id UUID NOT NULL REFERENCES units(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    difficulty_prior NUMERIC(4,3) NOT NULL DEFAULT 0.500 CHECK (difficulty_prior >= 0.0 AND difficulty_prior <= 1.0),
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS microcontents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    knowledge_component_id UUID NOT NULL REFERENCES knowledge_components(id) ON DELETE RESTRICT,
    title TEXT NOT NULL,
    content_type content_type_enum NOT NULL,
    content_body JSONB NOT NULL,
    estimated_duration_seconds INTEGER NOT NULL DEFAULT 180 CHECK (estimated_duration_seconds > 0),
    created_by UUID NOT NULL REFERENCES profiles(id),
    is_published BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================================
-- 4. Banco de Preguntas y Actividades
-- ============================================================================

CREATE TABLE IF NOT EXISTS questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    knowledge_component_id UUID NOT NULL REFERENCES knowledge_components(id) ON DELETE RESTRICT,
    question_text TEXT NOT NULL,
    question_type TEXT NOT NULL DEFAULT 'multiple_choice',
    explanation TEXT NOT NULL,
    difficulty NUMERIC(4,3) NOT NULL DEFAULT 0.500 CHECK (difficulty >= 0.0 AND difficulty <= 1.0),
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_by UUID NOT NULL REFERENCES profiles(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS question_options (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question_id UUID NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    option_text TEXT NOT NULL,
    is_correct BOOLEAN NOT NULL,
    order_index INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS activities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT,
    activity_type activity_type_enum NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS activity_questions (
    activity_id UUID NOT NULL REFERENCES activities(id) ON DELETE CASCADE,
    question_id UUID NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    order_index INTEGER NOT NULL,
    PRIMARY KEY (activity_id, question_id)
);

-- ============================================================================
-- 5. Registro Inmutable de Respuestas (Append-Only)
-- ============================================================================

CREATE TABLE IF NOT EXISTS quiz_attempts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    enrollment_id UUID NOT NULL REFERENCES enrollments(id) ON DELETE CASCADE,
    activity_id UUID NOT NULL REFERENCES activities(id) ON DELETE RESTRICT,
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ,
    score NUMERIC(5,2) CHECK (score IS NULL OR (score >= 0.0 AND score <= 100.0))
);

CREATE TABLE IF NOT EXISTS answer_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    attempt_id UUID NOT NULL REFERENCES quiz_attempts(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES profiles(id) ON DELETE RESTRICT,
    question_id UUID NOT NULL REFERENCES questions(id) ON DELETE RESTRICT,
    knowledge_component_id UUID NOT NULL REFERENCES knowledge_components(id) ON DELETE RESTRICT,
    selected_option_id UUID NOT NULL REFERENCES question_options(id) ON DELETE RESTRICT,
    is_correct BOOLEAN NOT NULL,
    attempt_number INTEGER NOT NULL DEFAULT 1 CHECK (attempt_number >= 1),
    response_time_seconds NUMERIC(6,2) NOT NULL CHECK (response_time_seconds > 0),
    idempotency_key UUID UNIQUE NOT NULL,
    event_timestamp TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================================
-- 6. Estados de Conocimiento y Métricas
-- ============================================================================

CREATE TABLE IF NOT EXISTS student_knowledge_states (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    knowledge_component_id UUID NOT NULL REFERENCES knowledge_components(id) ON DELETE CASCADE,
    p_mastery NUMERIC(4,3) NOT NULL CHECK (p_mastery >= 0.0 AND p_mastery <= 1.0),
    confidence NUMERIC(4,3) CHECK (confidence >= 0.0 AND confidence <= 1.0),
    total_interactions INTEGER NOT NULL DEFAULT 0,
    last_updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(student_id, knowledge_component_id)
);

CREATE TABLE IF NOT EXISTS student_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    total_attempts INTEGER NOT NULL DEFAULT 0,
    correct_attempts INTEGER NOT NULL DEFAULT 0,
    avg_response_time_seconds NUMERIC(6,2) NOT NULL DEFAULT 0.0,
    retention_rate NUMERIC(4,3) NOT NULL DEFAULT 0.000,
    streak_days INTEGER NOT NULL DEFAULT 0,
    last_active_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(tenant_id, student_id)
);

-- ============================================================================
-- 7. Modelos, Predicciones y Recomendaciones
-- ============================================================================

CREATE TABLE IF NOT EXISTS model_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_name TEXT NOT NULL,
    version TEXT NOT NULL UNIQUE,
    artifact_uri TEXT NOT NULL,
    metrics JSONB NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS predictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    knowledge_component_id UUID NOT NULL REFERENCES knowledge_components(id) ON DELETE RESTRICT,
    model_version_id UUID REFERENCES model_versions(id) ON DELETE SET NULL,
    prediction_horizon_hours INTEGER NOT NULL CHECK (prediction_horizon_hours > 0),
    predicted_recall_probability NUMERIC(4,3) NOT NULL CHECK (predicted_recall_probability >= 0.0 AND predicted_recall_probability <= 1.0),
    estimated_risk NUMERIC(4,3) NOT NULL CHECK (estimated_risk >= 0.0 AND estimated_risk <= 1.0),
    risk_level risk_level_enum NOT NULL DEFAULT 'low',
    feature_importance JSONB,
    input_event_cutoff TIMESTAMPTZ NOT NULL,
    prediction_status prediction_status_enum NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS recommendations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    prediction_id UUID REFERENCES predictions(id) ON DELETE SET NULL,
    student_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    knowledge_component_id UUID NOT NULL REFERENCES knowledge_components(id) ON DELETE RESTRICT,
    microcontent_id UUID NOT NULL REFERENCES microcontents(id) ON DELETE RESTRICT,
    selection_method recommendation_method_enum NOT NULL,
    decision_reason TEXT NOT NULL,
    status recommendation_status_enum NOT NULL DEFAULT 'pending',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS review_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    recommendation_id UUID REFERENCES recommendations(id) ON DELETE SET NULL,
    activity_id UUID NOT NULL REFERENCES activities(id) ON DELETE CASCADE,
    due_date TIMESTAMPTZ,
    status assignment_status_enum NOT NULL DEFAULT 'assigned',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================================
-- 8. Índices de Rendimiento
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_answer_events_student_kc ON answer_events(student_id, knowledge_component_id, event_timestamp ASC);
CREATE INDEX IF NOT EXISTS idx_answer_events_attempt ON answer_events(attempt_id);
CREATE INDEX IF NOT EXISTS idx_answer_events_tenant ON answer_events(tenant_id);
CREATE INDEX IF NOT EXISTS idx_predictions_student_kc ON predictions(student_id, knowledge_component_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_predictions_tenant ON predictions(tenant_id);
CREATE INDEX IF NOT EXISTS idx_recommendations_student_status ON recommendations(student_id, status);
CREATE INDEX IF NOT EXISTS idx_review_assignments_student_status ON review_assignments(student_id, status);
CREATE INDEX IF NOT EXISTS idx_profiles_tenant ON profiles(tenant_id);
CREATE INDEX IF NOT EXISTS idx_sections_teacher ON sections(teacher_id);
CREATE INDEX IF NOT EXISTS idx_sections_course ON sections(course_id);
CREATE INDEX IF NOT EXISTS idx_enrollments_student ON enrollments(student_id);
CREATE INDEX IF NOT EXISTS idx_enrollments_section ON enrollments(section_id);

-- ============================================================================
-- 9. Row Level Security (RLS)
-- ============================================================================
ALTER TABLE tenants ENABLE ROW LEVEL SECURITY;
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE auth_recovery_pins ENABLE ROW LEVEL SECURITY;
ALTER TABLE courses ENABLE ROW LEVEL SECURITY;
ALTER TABLE sections ENABLE ROW LEVEL SECURITY;
ALTER TABLE enrollments ENABLE ROW LEVEL SECURITY;
ALTER TABLE units ENABLE ROW LEVEL SECURITY;
ALTER TABLE knowledge_components ENABLE ROW LEVEL SECURITY;
ALTER TABLE microcontents ENABLE ROW LEVEL SECURITY;
ALTER TABLE questions ENABLE ROW LEVEL SECURITY;
ALTER TABLE question_options ENABLE ROW LEVEL SECURITY;
ALTER TABLE activities ENABLE ROW LEVEL SECURITY;
ALTER TABLE activity_questions ENABLE ROW LEVEL SECURITY;
ALTER TABLE quiz_attempts ENABLE ROW LEVEL SECURITY;
ALTER TABLE answer_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE student_knowledge_states ENABLE ROW LEVEL SECURITY;
ALTER TABLE student_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE model_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE predictions ENABLE ROW LEVEL SECURITY;
ALTER TABLE recommendations ENABLE ROW LEVEL SECURITY;
ALTER TABLE review_assignments ENABLE ROW LEVEL SECURITY;

-- Funciones Auxiliares de RLS
CREATE OR REPLACE FUNCTION current_user_tenant_id()
RETURNS UUID LANGUAGE sql STABLE SECURITY DEFINER SET search_path = '' AS $$
    SELECT tenant_id FROM public.profiles WHERE id = (SELECT auth.uid());
$$;

CREATE OR REPLACE FUNCTION current_user_role()
RETURNS public.user_role LANGUAGE sql STABLE SECURITY DEFINER SET search_path = '' AS $$
    SELECT role FROM public.profiles WHERE id = (SELECT auth.uid());
$$;

CREATE OR REPLACE FUNCTION is_teacher_of_student(p_student_id UUID)
RETURNS BOOLEAN LANGUAGE sql STABLE SECURITY DEFINER SET search_path = '' AS $$
    SELECT EXISTS (
        SELECT 1 
        FROM public.sections s
        JOIN public.enrollments e ON e.section_id = s.id
        WHERE s.teacher_id = (SELECT auth.uid())
          AND e.student_id = p_student_id
    );
$$;

-- Políticas Profiles
DO $$ BEGIN
    CREATE POLICY "profiles_select_own_or_same_tenant" ON profiles
        FOR SELECT USING (id = (SELECT auth.uid()) OR tenant_id = (SELECT current_user_tenant_id()));
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE POLICY "profiles_update_own" ON profiles
        FOR UPDATE USING (id = (SELECT auth.uid()));
EXCEPTION WHEN duplicate_object THEN null;
END $$;

-- Políticas Cursos y Contenido
DO $$ BEGIN
    CREATE POLICY "courses_select_tenant" ON courses
        FOR SELECT USING (tenant_id = (SELECT current_user_tenant_id()));
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE POLICY "units_select_tenant" ON units
        FOR SELECT USING (tenant_id = (SELECT current_user_tenant_id()));
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE POLICY "kc_select_tenant" ON knowledge_components
        FOR SELECT USING (tenant_id = (SELECT current_user_tenant_id()));
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE POLICY "microcontents_select_tenant" ON microcontents
        FOR SELECT USING (tenant_id = (SELECT current_user_tenant_id()) AND (is_published = true OR created_by = (SELECT auth.uid())));
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE POLICY "enrollments_select_policy" ON enrollments
        FOR SELECT USING (student_id = (SELECT auth.uid()) OR (SELECT current_user_role()) IN ('super_admin', 'admin') OR EXISTS (SELECT 1 FROM public.sections s WHERE s.id = enrollments.section_id AND s.teacher_id = (SELECT auth.uid())));
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE POLICY "questions_select_tenant" ON questions
        FOR SELECT USING (tenant_id = (SELECT current_user_tenant_id()));
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE POLICY "options_select_all" ON question_options
        FOR SELECT USING (EXISTS (SELECT 1 FROM public.questions q WHERE q.id = question_options.question_id AND q.tenant_id = (SELECT current_user_tenant_id())));
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE POLICY "attempts_student_access" ON quiz_attempts
        FOR SELECT USING (EXISTS (SELECT 1 FROM public.enrollments e WHERE e.id = quiz_attempts.enrollment_id AND e.student_id = (SELECT auth.uid())) OR (SELECT current_user_role()) IN ('super_admin', 'admin') OR EXISTS (SELECT 1 FROM public.enrollments e JOIN public.sections s ON s.id = e.section_id WHERE e.id = quiz_attempts.enrollment_id AND s.teacher_id = (SELECT auth.uid())));
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE POLICY "attempts_insert_student" ON quiz_attempts
        FOR INSERT WITH CHECK (EXISTS (SELECT 1 FROM public.enrollments e WHERE e.id = enrollment_id AND e.student_id = (SELECT auth.uid())));
EXCEPTION WHEN duplicate_object THEN null;
END $$;

-- Inmutabilidad Answer Events: Solo SELECT e INSERT
DO $$ BEGIN
    CREATE POLICY "answer_events_select" ON answer_events
        FOR SELECT USING (student_id = (SELECT auth.uid()) OR (SELECT is_teacher_of_student(student_id)) OR (SELECT current_user_role()) IN ('super_admin', 'admin'));
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE POLICY "answer_events_insert" ON answer_events
        FOR INSERT WITH CHECK (student_id = (SELECT auth.uid()));
EXCEPTION WHEN duplicate_object THEN null;
END $$;

REVOKE UPDATE, DELETE ON answer_events FROM anon, authenticated;

-- Políticas de Predicciones y Recomendaciones
DO $$ BEGIN
    CREATE POLICY "predictions_select" ON predictions
        FOR SELECT USING (student_id = (SELECT auth.uid()) OR (SELECT is_teacher_of_student(student_id)) OR (SELECT current_user_role()) IN ('super_admin', 'admin'));
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE POLICY "recommendations_select" ON recommendations
        FOR SELECT USING (student_id = (SELECT auth.uid()) OR (SELECT is_teacher_of_student(student_id)) OR (SELECT current_user_role()) IN ('super_admin', 'admin'));
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE POLICY "recovery_pins_policy" ON auth_recovery_pins
        FOR ALL USING ((SELECT auth.uid()) = created_by OR (SELECT auth.uid()) = student_id OR (SELECT current_user_role()) IN ('super_admin', 'admin'));
EXCEPTION WHEN duplicate_object THEN null;
END $$;
