# Esquema de Base de Datos PostgreSQL (DDL Formal)

## 1. Visión General del Modelo Relacional

El modelo de datos de la **Plataforma de Microaprendizaje Adaptativo** está diseñado para ejecutarse en **PostgreSQL 15+** dentro del entorno de **Supabase**. Implementa:

- **Multi-Tenancy Nativo:** Aislamiento total de instituciones educativas mediante la tabla `tenants` y la propagación de claves foráneas `tenant_id` en todas las entidades de dominio.
- **Seguridad Declarativa Estricta (RLS):** Row Level Security habilitado en el 100% de las tablas con políticas optimizadas que evalúan la sesión del usuario mediante subconsultas escalares `(SELECT auth.uid())`.
- **Inmutabilidad y Auditoría Pedagógica:** El registro de respuestas en `answer_events` opera como un almacén de eventos de solo inserción (*Append-Only*). Las operaciones `UPDATE` y `DELETE` quedan revocadas explícitamente a nivel de permisos SQL para roles anónimos y autenticados.
- **Indexación Temporal Estratégica:** Índices compuestos de alta selectividad para la extracción rápida de ventanas temporales de práctica requeridas por los modelos de Knowledge Tracing y retención (DAS3H, BKT).

---

## 2. Definición DDL Exhaustiva

```sql
-- ============================================================================
-- PLATAFORMA DE MICROAPRENDIZAJE ADAPTATIVO - ESQUEMA DE BASE DE DATOS DDL
-- Multi-Tenancy nativo, Row Level Security (RLS) e Inmutabilidad de Auditoría
-- ============================================================================

-- 0. Extensiones Requeridas
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================================
-- 1. Tipos Enumerados (ENUMs)
-- ============================================================================
CREATE TYPE user_role AS ENUM (
    'super_admin',
    'admin',
    'teacher',
    'student',
    'researcher'
);

CREATE TYPE activity_type_enum AS ENUM (
    'diagnostic',
    'practice',
    'immediate_assessment',
    'delayed_assessment'
);

CREATE TYPE content_type_enum AS ENUM (
    'text_summary',
    'infographic_card',
    'concept_map'
);

CREATE TYPE risk_level_enum AS ENUM (
    'low',
    'medium',
    'high',
    'critical'
);

CREATE TYPE prediction_status_enum AS ENUM (
    'valid',
    'insufficient_history',
    'degraded_fallback'
);

CREATE TYPE recommendation_method_enum AS ENUM (
    'predictive_model',
    'rule_based_fallback',
    'teacher_assigned'
);

CREATE TYPE recommendation_status_enum AS ENUM (
    'pending',
    'delivered',
    'completed',
    'dismissed'
);

CREATE TYPE assignment_status_enum AS ENUM (
    'assigned',
    'in_progress',
    'completed',
    'expired'
);

-- ============================================================================
-- 2. Entidades de Tenencia, Identidad y Usuarios
-- ============================================================================

CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    domain TEXT,
    is_active BOOLEAN NOT NULL DEFAULT true,
    settings JSONB NOT NULL DEFAULT '{"risk_threshold": 0.65, "cold_start_kcs": 3}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    full_name TEXT NOT NULL,
    role user_role NOT NULL DEFAULT 'student',
    avatar_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================================
-- 3. Estructura Pedagógica Agnóstica
-- ============================================================================

CREATE TABLE courses (
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

CREATE TABLE sections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE RESTRICT,
    teacher_id UUID NOT NULL REFERENCES profiles(id) ON DELETE RESTRICT,
    name TEXT NOT NULL, -- ej. "5to A - Ciencias"
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE enrollments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    section_id UUID NOT NULL REFERENCES sections(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    student_id_pseudo UUID NOT NULL DEFAULT gen_random_uuid(), -- Token disociado para investigación y ML
    enrolled_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(section_id, student_id),
    UNIQUE(tenant_id, student_id_pseudo)
);

CREATE TABLE units (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    order_index INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE knowledge_components (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    unit_id UUID NOT NULL REFERENCES units(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    difficulty_prior NUMERIC(4,3) NOT NULL DEFAULT 0.500 CHECK (difficulty_prior >= 0.0 AND difficulty_prior <= 1.0),
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE microcontents (
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
-- 4. Banco de Preguntas y Actividades de Evaluación
-- ============================================================================

CREATE TABLE questions (
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

CREATE TABLE question_options (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question_id UUID NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    option_text TEXT NOT NULL,
    is_correct BOOLEAN NOT NULL,
    order_index INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE activities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT,
    activity_type activity_type_enum NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Alias conceptual: diagnostic_tests mapea a activities con activity_type = 'diagnostic'
CREATE VIEW diagnostic_tests AS
SELECT * FROM activities WHERE activity_type = 'diagnostic';

CREATE TABLE activity_questions (
    activity_id UUID NOT NULL REFERENCES activities(id) ON DELETE CASCADE,
    question_id UUID NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    order_index INTEGER NOT NULL,
    PRIMARY KEY (activity_id, question_id)
);

-- ============================================================================
-- 5. Registro Inmutable de Interacciones y Respuestas
-- ============================================================================

CREATE TABLE quiz_attempts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    enrollment_id UUID NOT NULL REFERENCES enrollments(id) ON DELETE CASCADE,
    activity_id UUID NOT NULL REFERENCES activities(id) ON DELETE RESTRICT,
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ,
    score NUMERIC(5,2) CHECK (score IS NULL OR (score >= 0.0 AND score <= 100.0))
);

CREATE TABLE answer_events (
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

-- Alias conceptual: student_responses mapea a answer_events
CREATE VIEW student_responses AS
SELECT * FROM answer_events;

-- ============================================================================
-- 6. Estados de Conocimiento y Métricas Agregadas
-- ============================================================================

CREATE TABLE student_knowledge_states (
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

CREATE TABLE student_metrics (
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
-- 7. Registro de Versiones de Modelo, Predicciones y Recomendaciones
-- ============================================================================

CREATE TABLE model_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_name TEXT NOT NULL,
    version TEXT NOT NULL UNIQUE,
    artifact_uri TEXT NOT NULL,
    metrics JSONB NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE predictions (
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

-- Alias conceptual: risk_predictions mapea a predictions
CREATE VIEW risk_predictions AS
SELECT * FROM predictions;

CREATE TABLE recommendations (
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

-- Alias conceptual: learning_recommendations mapea a recommendations
CREATE VIEW learning_recommendations AS
SELECT * FROM recommendations;

CREATE TABLE review_assignments (
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
-- 8. Índices Estratégicos de Alto Rendimiento
-- ============================================================================

-- Extracción de ventanas temporales para inferencia DAS3H / BKT
CREATE INDEX idx_answer_events_student_kc ON answer_events(student_id, knowledge_component_id, event_timestamp ASC);
CREATE INDEX idx_answer_events_attempt ON answer_events(attempt_id);
CREATE INDEX idx_answer_events_tenant ON answer_events(tenant_id);

-- Consultas de inferencia y predicción
CREATE INDEX idx_predictions_student_kc ON predictions(student_id, knowledge_component_id, created_at DESC);
CREATE INDEX idx_predictions_tenant ON predictions(tenant_id);

-- Recomendaciones y repasos pendientes
CREATE INDEX idx_recommendations_student_status ON recommendations(student_id, status);
CREATE INDEX idx_review_assignments_student_status ON review_assignments(student_id, status);

-- Claves foráneas y filtrado por tenant
CREATE INDEX idx_profiles_tenant ON profiles(tenant_id);
CREATE INDEX idx_sections_teacher ON sections(teacher_id);
CREATE INDEX idx_sections_course ON sections(course_id);
CREATE INDEX idx_enrollments_student ON enrollments(student_id);
CREATE INDEX idx_enrollments_section ON enrollments(section_id);
CREATE INDEX idx_questions_kc ON questions(knowledge_component_id);
CREATE INDEX idx_microcontents_kc ON microcontents(knowledge_component_id);
CREATE INDEX idx_student_ks_student ON student_knowledge_states(student_id);

-- ============================================================================
-- 9. Políticas de Seguridad por Fila (Row Level Security - RLS)
-- ============================================================================

-- Habilitar RLS en el 100% de las tablas
ALTER TABLE tenants ENABLE ROW LEVEL SECURITY;
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
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

-- Funciones de Seguridad Auxiliares (SECURITY DEFINER optimizadas)
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

-- Políticas para Profiles
CREATE POLICY "profiles_select_own_or_same_tenant" ON profiles
    FOR SELECT USING (
        id = (SELECT auth.uid()) 
        OR tenant_id = (SELECT current_user_tenant_id())
    );

CREATE POLICY "profiles_update_own" ON profiles
    FOR UPDATE USING (id = (SELECT auth.uid()));

-- Políticas para Courses, Units, Knowledge Components y Microcontents
CREATE POLICY "courses_select_tenant" ON courses
    FOR SELECT USING (tenant_id = (SELECT current_user_tenant_id()));

CREATE POLICY "units_select_tenant" ON units
    FOR SELECT USING (tenant_id = (SELECT current_user_tenant_id()));

CREATE POLICY "kc_select_tenant" ON knowledge_components
    FOR SELECT USING (tenant_id = (SELECT current_user_tenant_id()));

CREATE POLICY "microcontents_select_tenant" ON microcontents
    FOR SELECT USING (
        tenant_id = (SELECT current_user_tenant_id()) 
        AND (is_published = true OR created_by = (SELECT auth.uid()))
    );

-- Políticas para Enrollments
CREATE POLICY "enrollments_select_policy" ON enrollments
    FOR SELECT USING (
        student_id = (SELECT auth.uid())
        OR (SELECT current_user_role()) IN ('super_admin', 'admin')
        OR EXISTS (
            SELECT 1 FROM public.sections s 
            WHERE s.id = enrollments.section_id AND s.teacher_id = (SELECT auth.uid())
        )
    );

-- Políticas para Questions & Options
CREATE POLICY "questions_select_tenant" ON questions
    FOR SELECT USING (tenant_id = (SELECT current_user_tenant_id()));

CREATE POLICY "options_select_all" ON question_options
    FOR SELECT USING (EXISTS (
        SELECT 1 FROM public.questions q 
        WHERE q.id = question_options.question_id 
          AND q.tenant_id = (SELECT current_user_tenant_id())
    ));

-- Políticas para Quiz Attempts
CREATE POLICY "attempts_student_access" ON quiz_attempts
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.enrollments e 
            WHERE e.id = quiz_attempts.enrollment_id AND e.student_id = (SELECT auth.uid())
        )
        OR (SELECT current_user_role()) IN ('super_admin', 'admin')
        OR EXISTS (
            SELECT 1 FROM public.enrollments e
            JOIN public.sections s ON s.id = e.section_id
            WHERE e.id = quiz_attempts.enrollment_id AND s.teacher_id = (SELECT auth.uid())
        )
    );

CREATE POLICY "attempts_insert_student" ON quiz_attempts
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.enrollments e 
            WHERE e.id = enrollment_id AND e.student_id = (SELECT auth.uid())
        )
    );

-- Políticas para Answer Events (Inmutabilidad Estricta: Solo SELECT e INSERT)
CREATE POLICY "answer_events_select" ON answer_events
    FOR SELECT USING (
        student_id = (SELECT auth.uid())
        OR (SELECT is_teacher_of_student(student_id))
        OR (SELECT current_user_role()) IN ('super_admin', 'admin')
    );

CREATE POLICY "answer_events_insert" ON answer_events
    FOR INSERT WITH CHECK (
        student_id = (SELECT auth.uid())
    );

-- INMUTABILIDAD ESTRICTA: Denegar UPDATE y DELETE en answer_events
REVOKE UPDATE, DELETE ON answer_events FROM anon, authenticated;

-- Políticas para Predictions
CREATE POLICY "predictions_select" ON predictions
    FOR SELECT USING (
        student_id = (SELECT auth.uid())
        OR (SELECT is_teacher_of_student(student_id))
        OR (SELECT current_user_role()) IN ('super_admin', 'admin')
    );

-- Políticas para Recommendations
CREATE POLICY "recommendations_select" ON recommendations
    FOR SELECT USING (
        student_id = (SELECT auth.uid())
        OR (SELECT is_teacher_of_student(student_id))
        OR (SELECT current_user_role()) IN ('super_admin', 'admin')
    );

-- Políticas para Student Knowledge States
CREATE POLICY "knowledge_states_select" ON student_knowledge_states
    FOR SELECT USING (
        student_id = (SELECT auth.uid())
        OR (SELECT is_teacher_of_student(student_id))
        OR (SELECT current_user_role()) IN ('super_admin', 'admin')
    );

-- Políticas para Student Metrics
CREATE POLICY "student_metrics_select" ON student_metrics
    FOR SELECT USING (
        student_id = (SELECT auth.uid())
        OR (SELECT is_teacher_of_student(student_id))
        OR (SELECT current_user_role()) IN ('super_admin', 'admin')
    );

-- Políticas para Review Assignments
CREATE POLICY "review_assignments_select" ON review_assignments
    FOR SELECT USING (
        student_id = (SELECT auth.uid())
        OR (SELECT is_teacher_of_student(student_id))
        OR (SELECT current_user_role()) IN ('super_admin', 'admin')
    );
```
