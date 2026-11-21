-- Pre-create roles needed by schema and tests
DO $$ BEGIN
    CREATE ROLE anon NOLOGIN;
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE ROLE authenticated NOLOGIN;
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE ROLE service_role NOLOGIN;
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE ROLE ml_api_worker WITH LOGIN PASSWORD 'ml_api_worker_secret';
EXCEPTION WHEN duplicate_object THEN
    ALTER ROLE ml_api_worker WITH LOGIN PASSWORD 'ml_api_worker_secret';
END $$;

--
-- PostgreSQL database dump
--

\restrict BJHHdFsjcRRncAbU1Q3Ao5xRJTZR3oK8NtXBwVOf1bAjimlh0U3642WvA84cvNj

-- Dumped from database version 16.15 (Ubuntu 16.15-0ubuntu0.24.04.1)
-- Dumped by pg_dump version 16.15 (Ubuntu 16.15-0ubuntu0.24.04.1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: auth; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA auth;


ALTER SCHEMA auth OWNER TO postgres;

--
-- Name: storage; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA storage;


ALTER SCHEMA storage OWNER TO postgres;

--
-- Name: pgcrypto; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA public;


--
-- Name: EXTENSION pgcrypto; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION pgcrypto IS 'cryptographic functions';


--
-- Name: pgtap; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pgtap WITH SCHEMA public;


--
-- Name: EXTENSION pgtap; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION pgtap IS 'Unit testing for PostgreSQL';


--
-- Name: uuid-ossp; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA public;


--
-- Name: EXTENSION "uuid-ossp"; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION "uuid-ossp" IS 'generate universally unique identifiers (UUIDs)';


--
-- Name: activity_status_enum; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.activity_status_enum AS ENUM (
    'draft',
    'published',
    'closed'
);


ALTER TYPE public.activity_status_enum OWNER TO postgres;

--
-- Name: activity_type_enum; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.activity_type_enum AS ENUM (
    'diagnostic',
    'practice',
    'immediate_assessment',
    'delayed_assessment',
    'formative',
    'summative',
    'remediation',
    'retention_check'
);


ALTER TYPE public.activity_type_enum OWNER TO postgres;

--
-- Name: assignment_status_enum; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.assignment_status_enum AS ENUM (
    'assigned',
    'in_progress',
    'completed',
    'expired'
);


ALTER TYPE public.assignment_status_enum OWNER TO postgres;

--
-- Name: attempt_status_enum; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.attempt_status_enum AS ENUM (
    'in_progress',
    'completed',
    'abandoned'
);


ALTER TYPE public.attempt_status_enum OWNER TO postgres;

--
-- Name: content_type_enum; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.content_type_enum AS ENUM (
    'text_summary',
    'infographic_card',
    'concept_map'
);


ALTER TYPE public.content_type_enum OWNER TO postgres;

--
-- Name: draft_status_enum; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.draft_status_enum AS ENUM (
    'draft',
    'edited',
    'approved',
    'rejected'
);


ALTER TYPE public.draft_status_enum OWNER TO postgres;

--
-- Name: exposure_completion_status_enum; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.exposure_completion_status_enum AS ENUM (
    'completed',
    'partial',
    'abandoned'
);


ALTER TYPE public.exposure_completion_status_enum OWNER TO postgres;

--
-- Name: exposure_type_enum; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.exposure_type_enum AS ENUM (
    'initial_study',
    'review_study',
    'remedial_reading',
    'diagnostic_exposure'
);


ALTER TYPE public.exposure_type_enum OWNER TO postgres;

--
-- Name: feedback_policy_enum; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.feedback_policy_enum AS ENUM (
    'immediate_with_explanation',
    'upon_completion',
    'after_deadline'
);


ALTER TYPE public.feedback_policy_enum OWNER TO postgres;

--
-- Name: generation_job_status_enum; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.generation_job_status_enum AS ENUM (
    'queued',
    'processing',
    'review_required',
    'approved',
    'rejected',
    'failed'
);


ALTER TYPE public.generation_job_status_enum OWNER TO postgres;

--
-- Name: notification_type_enum; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.notification_type_enum AS ENUM (
    'review_reminder',
    'new_assignment',
    'system_notice'
);


ALTER TYPE public.notification_type_enum OWNER TO postgres;

--
-- Name: prediction_status_enum; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.prediction_status_enum AS ENUM (
    'valid',
    'insufficient_history',
    'degraded_fallback'
);


ALTER TYPE public.prediction_status_enum OWNER TO postgres;

--
-- Name: recommendation_method_enum; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.recommendation_method_enum AS ENUM (
    'predictive_model',
    'rule_based_fallback',
    'teacher_assigned'
);


ALTER TYPE public.recommendation_method_enum OWNER TO postgres;

--
-- Name: recommendation_status_enum; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.recommendation_status_enum AS ENUM (
    'pending',
    'delivered',
    'completed',
    'dismissed',
    'expired'
);


ALTER TYPE public.recommendation_status_enum OWNER TO postgres;

--
-- Name: risk_level_enum; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.risk_level_enum AS ENUM (
    'low',
    'medium',
    'high',
    'critical'
);


ALTER TYPE public.risk_level_enum OWNER TO postgres;

--
-- Name: user_role; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.user_role AS ENUM (
    'super_admin',
    'admin',
    'teacher',
    'student',
    'researcher'
);


ALTER TYPE public.user_role OWNER TO postgres;

--
-- Name: role(); Type: FUNCTION; Schema: auth; Owner: postgres
--

CREATE FUNCTION auth.role() RETURNS text
    LANGUAGE sql STABLE
    AS $$
    SELECT COALESCE(NULLIF(current_setting('request.jwt.claim.role', true), ''), 'anon');
$$;


ALTER FUNCTION auth.role() OWNER TO postgres;

--
-- Name: uid(); Type: FUNCTION; Schema: auth; Owner: postgres
--

CREATE FUNCTION auth.uid() RETURNS uuid
    LANGUAGE sql STABLE
    AS $$
    SELECT NULLIF(current_setting('request.jwt.claim.sub', true), '')::uuid;
$$;


ALTER FUNCTION auth.uid() OWNER TO postgres;

--
-- Name: current_user_role(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.current_user_role() RETURNS public.user_role
    LANGUAGE sql STABLE SECURITY DEFINER
    SET search_path TO ''
    AS $$
    SELECT role FROM public.profiles WHERE id = (SELECT auth.uid());
$$;


ALTER FUNCTION public.current_user_role() OWNER TO postgres;

--
-- Name: current_user_tenant_id(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.current_user_tenant_id() RETURNS uuid
    LANGUAGE sql STABLE SECURITY DEFINER
    SET search_path TO ''
    AS $$
    SELECT tenant_id FROM public.profiles WHERE id = (SELECT auth.uid());
$$;


ALTER FUNCTION public.current_user_tenant_id() OWNER TO postgres;

--
-- Name: enforce_content_generation_jobs_status_guard(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.enforce_content_generation_jobs_status_guard() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    IF (TG_OP = 'INSERT') THEN
        IF (NEW.status != 'queued') THEN
            IF (SELECT current_user_role()) IN ('teacher', 'student', 'admin') THEN
                RAISE EXCEPTION 'Initial status for content_generation_jobs must be queued.';
            END IF;
        END IF;
        RETURN NEW;
    ELSIF (TG_OP = 'UPDATE') THEN
        IF (SELECT current_user_role()) IN ('teacher', 'student') THEN
            RAISE EXCEPTION 'Direct update on content_generation_jobs is prohibited. Transitions must be executed by authorized backend processes.';
        END IF;
        IF (OLD.status IS DISTINCT FROM NEW.status) THEN
            IF (SELECT current_user_role()) = 'admin' THEN
                RAISE EXCEPTION 'Direct status update on content_generation_jobs is prohibited. Transitions must be executed by authorized backend processes.';
            END IF;
        END IF;
        RETURN NEW;
    ELSIF (TG_OP = 'DELETE') THEN
        IF (SELECT current_user_role()) IN ('teacher', 'student') THEN
            RAISE EXCEPTION 'Direct deletion of content_generation_jobs is prohibited for teachers and students.';
        END IF;
        RETURN OLD;
    END IF;
END;
$$;


ALTER FUNCTION public.enforce_content_generation_jobs_status_guard() OWNER TO postgres;

--
-- Name: enforce_notifications_student_update_guard(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.enforce_notifications_student_update_guard() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    IF (SELECT current_user_role()) = 'student' THEN
        IF (OLD.id IS DISTINCT FROM NEW.id OR
            OLD.tenant_id IS DISTINCT FROM NEW.tenant_id OR
            OLD.student_id IS DISTINCT FROM NEW.student_id OR
            OLD.review_assignment_id IS DISTINCT FROM NEW.review_assignment_id OR
            OLD.notification_type IS DISTINCT FROM NEW.notification_type OR
            OLD.title IS DISTINCT FROM NEW.title OR
            OLD.body IS DISTINCT FROM NEW.body OR
            OLD.target_path IS DISTINCT FROM NEW.target_path OR
            OLD.deduplication_key IS DISTINCT FROM NEW.deduplication_key OR
            OLD.created_at IS DISTINCT FROM NEW.created_at) THEN
            RAISE EXCEPTION 'Students can only modify read_at on their notifications.';
        END IF;
    END IF;
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.enforce_notifications_student_update_guard() OWNER TO postgres;

--
-- Name: enforce_question_drafts_status_guard(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.enforce_question_drafts_status_guard() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_job_tenant_id UUID;
    v_job_status generation_job_status_enum;
BEGIN
    IF (TG_OP = 'INSERT') THEN
        -- Verificar que el tenant del borrador coincida con el tenant del trabajo padre
        SELECT tenant_id, status INTO v_job_tenant_id, v_job_status
        FROM content_generation_jobs
        WHERE id = NEW.generation_job_id;

        IF v_job_tenant_id IS NULL THEN
            RAISE EXCEPTION 'El trabajo de generación con ID % no existe.', NEW.generation_job_id;
        END IF;

        IF v_job_tenant_id IS DISTINCT FROM NEW.tenant_id THEN
            RAISE EXCEPTION 'Violación multi-tenant: el borrador (tenant: %) no coincide con el trabajo asociado (tenant: %).',
                NEW.tenant_id, v_job_tenant_id;
        END IF;

        -- No permitir crear borradores en estado approved directamente
        IF (NEW.status = 'approved' OR NEW.approved_question_id IS NOT NULL) THEN
            IF (SELECT current_user_role()) IN ('teacher', 'student', 'admin') THEN
                RAISE EXCEPTION 'Direct approval of question drafts via SQL is prohibited. Approval is reserved for the transactional publication service.';
            END IF;
        END IF;
        RETURN NEW;

    ELSIF (TG_OP = 'UPDATE') THEN
        -- Bloquear explícitamente reversión de borradores intervenidos (edited, approved, rejected) a draft
        IF (OLD.status != 'draft' AND NEW.status = 'draft') THEN
            RAISE EXCEPTION 'Cannot revert question draft % from status "%" back to "draft".', OLD.id, OLD.status;
        END IF;

        -- Protección de inmutabilidad de campos críticos y aprobación directa
        IF (NEW.status = 'approved' OR NEW.approved_question_id IS NOT NULL) THEN
            IF (SELECT current_user_role()) IN ('teacher', 'student', 'admin') THEN
                RAISE EXCEPTION 'Direct approval of question drafts via SQL is prohibited. Approval is reserved for the transactional publication service.';
            END IF;
        END IF;

        IF (OLD.id IS DISTINCT FROM NEW.id OR
            OLD.tenant_id IS DISTINCT FROM NEW.tenant_id OR
            OLD.generation_job_id IS DISTINCT FROM NEW.generation_job_id OR
            OLD.created_at IS DISTINCT FROM NEW.created_at) THEN
            IF (SELECT current_user_role()) IN ('teacher', 'student') THEN
                RAISE EXCEPTION 'Immutable fields of question_drafts cannot be modified.';
            END IF;
        END IF;
        RETURN NEW;

    ELSIF (TG_OP = 'DELETE') THEN
        IF (OLD.status = 'approved' OR OLD.approved_question_id IS NOT NULL) THEN
            IF (SELECT current_user_role()) IN ('teacher', 'student', 'admin') THEN
                RAISE EXCEPTION 'Approved question drafts cannot be deleted as they represent audit records.';
            END IF;
        END IF;
        RETURN OLD;
    END IF;
END;
$$;


ALTER FUNCTION public.enforce_question_drafts_status_guard() OWNER TO postgres;

--
-- Name: is_student_enrolled_in_activity(uuid, uuid); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.is_student_enrolled_in_activity(p_student_id uuid, p_activity_id uuid) RETURNS boolean
    LANGUAGE sql STABLE SECURITY DEFINER
    SET search_path TO ''
    AS $$
    SELECT EXISTS (
        SELECT 1
        FROM public.activity_sections acts
        JOIN public.enrollments e ON e.section_id = acts.section_id
        WHERE acts.activity_id = p_activity_id
          AND e.student_id = p_student_id
    );
$$;


ALTER FUNCTION public.is_student_enrolled_in_activity(p_student_id uuid, p_activity_id uuid) OWNER TO postgres;

--
-- Name: is_teacher_of_course(uuid); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.is_teacher_of_course(p_course_id uuid) RETURNS boolean
    LANGUAGE sql STABLE SECURITY DEFINER
    SET search_path TO ''
    AS $$
    SELECT EXISTS (
        SELECT 1 
        FROM public.sections s
        WHERE s.course_id = p_course_id
          AND s.teacher_id = (SELECT auth.uid())
          AND s.tenant_id = (SELECT public.current_user_tenant_id())
    );
$$;


ALTER FUNCTION public.is_teacher_of_course(p_course_id uuid) OWNER TO postgres;

--
-- Name: is_teacher_of_student(uuid); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.is_teacher_of_student(p_student_id uuid) RETURNS boolean
    LANGUAGE sql STABLE SECURITY DEFINER
    SET search_path TO ''
    AS $$
    SELECT EXISTS (
        SELECT 1 
        FROM public.sections s
        JOIN public.enrollments e ON e.section_id = s.id
        WHERE s.teacher_id = (SELECT auth.uid())
          AND e.student_id = p_student_id
    );
$$;


ALTER FUNCTION public.is_teacher_of_student(p_student_id uuid) OWNER TO postgres;

--
-- Name: prevent_answer_events_mutation(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.prevent_answer_events_mutation() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
        BEGIN
            RAISE EXCEPTION 'answer_events is strictly append-only. Operations of type % are permanently denied.', TG_OP
                USING ERRCODE = '55000';
            RETURN NULL;
        END;
        $$;


ALTER FUNCTION public.prevent_answer_events_mutation() OWNER TO postgres;

--
-- Name: prevent_content_exposure_mutation(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.prevent_content_exposure_mutation() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    RAISE EXCEPTION 'content_exposure_events table is strictly append-only. Operations of type % are permanently forbidden.', TG_OP
        USING ERRCODE = '55000';
    RETURN NULL;
END;
$$;


ALTER FUNCTION public.prevent_content_exposure_mutation() OWNER TO postgres;

--
-- Name: update_updated_at_column(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.update_updated_at_column() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.update_updated_at_column() OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: users; Type: TABLE; Schema: auth; Owner: postgres
--

CREATE TABLE auth.users (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    instance_id uuid,
    email text,
    encrypted_password text,
    email_confirmed_at timestamp with time zone,
    raw_app_meta_data jsonb DEFAULT '{}'::jsonb,
    raw_user_meta_data jsonb DEFAULT '{}'::jsonb,
    role text DEFAULT 'authenticated'::text,
    aud text DEFAULT 'authenticated'::text,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE auth.users OWNER TO postgres;

--
-- Name: activities; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.activities (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    tenant_id uuid NOT NULL,
    course_id uuid NOT NULL,
    title text NOT NULL,
    description text,
    activity_type public.activity_type_enum NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    created_by uuid,
    status public.activity_status_enum DEFAULT 'draft'::public.activity_status_enum NOT NULL,
    feedback_policy public.feedback_policy_enum DEFAULT 'immediate_with_explanation'::public.feedback_policy_enum NOT NULL,
    published_at timestamp with time zone,
    available_from timestamp with time zone,
    available_until timestamp with time zone,
    max_attempts integer DEFAULT 1 NOT NULL,
    time_limit_minutes integer,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT activities_max_attempts_check CHECK ((max_attempts >= 1)),
    CONSTRAINT activities_time_limit_minutes_check CHECK (((time_limit_minutes IS NULL) OR (time_limit_minutes > 0)))
);


ALTER TABLE public.activities OWNER TO postgres;

--
-- Name: activity_questions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.activity_questions (
    activity_id uuid NOT NULL,
    question_id uuid NOT NULL,
    order_index integer NOT NULL
);


ALTER TABLE public.activity_questions OWNER TO postgres;

--
-- Name: activity_sections; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.activity_sections (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    tenant_id uuid NOT NULL,
    activity_id uuid NOT NULL,
    section_id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.activity_sections OWNER TO postgres;

--
-- Name: answer_events; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.answer_events (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    tenant_id uuid NOT NULL,
    attempt_id uuid NOT NULL,
    student_id uuid NOT NULL,
    question_id uuid NOT NULL,
    knowledge_component_id uuid NOT NULL,
    selected_option_id uuid NOT NULL,
    is_correct boolean NOT NULL,
    attempt_number integer DEFAULT 1 NOT NULL,
    response_time_seconds numeric(6,2) NOT NULL,
    idempotency_key uuid NOT NULL,
    event_timestamp timestamp with time zone DEFAULT now() NOT NULL,
    activity_id uuid,
    course_id uuid,
    question_sequence integer DEFAULT 1 NOT NULL,
    response_time_ms integer,
    CONSTRAINT answer_events_attempt_number_check CHECK ((attempt_number >= 1)),
    CONSTRAINT answer_events_response_time_ms_check CHECK (((response_time_ms IS NULL) OR (response_time_ms > 0))),
    CONSTRAINT answer_events_response_time_seconds_check CHECK ((response_time_seconds > (0)::numeric))
);


ALTER TABLE public.answer_events OWNER TO postgres;

--
-- Name: auth_recovery_pins; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.auth_recovery_pins (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    tenant_id uuid NOT NULL,
    student_id uuid NOT NULL,
    pin_hash text NOT NULL,
    created_by uuid NOT NULL,
    expires_at timestamp with time zone DEFAULT (now() + '00:30:00'::interval) NOT NULL,
    used_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.auth_recovery_pins OWNER TO postgres;

--
-- Name: content_exposure_events; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.content_exposure_events (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    tenant_id uuid NOT NULL,
    student_id uuid NOT NULL,
    student_id_pseudo uuid NOT NULL,
    microcontent_id uuid NOT NULL,
    knowledge_component_id uuid NOT NULL,
    exposure_type public.exposure_type_enum DEFAULT 'initial_study'::public.exposure_type_enum NOT NULL,
    started_at timestamp with time zone NOT NULL,
    completed_at timestamp with time zone,
    duration_seconds numeric(8,2) DEFAULT 0.0 NOT NULL,
    active_reading_seconds numeric(8,2),
    completion_status public.exposure_completion_status_enum DEFAULT 'completed'::public.exposure_completion_status_enum NOT NULL,
    session_id uuid NOT NULL,
    idempotency_key uuid NOT NULL,
    metadata jsonb DEFAULT '{}'::jsonb NOT NULL,
    event_timestamp timestamp with time zone DEFAULT now() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT chk_exposure_completed_at CHECK (((completed_at IS NULL) OR (completed_at >= started_at))),
    CONSTRAINT content_exposure_events_active_reading_seconds_check CHECK (((active_reading_seconds IS NULL) OR (active_reading_seconds >= 0.0))),
    CONSTRAINT content_exposure_events_duration_seconds_check CHECK ((duration_seconds >= 0.0))
);


ALTER TABLE public.content_exposure_events OWNER TO postgres;

--
-- Name: content_generation_jobs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.content_generation_jobs (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    tenant_id uuid NOT NULL,
    course_id uuid,
    unit_id uuid,
    created_by uuid NOT NULL,
    storage_bucket text DEFAULT 'teacher-materials'::text NOT NULL,
    storage_path text NOT NULL,
    original_filename text NOT NULL,
    mime_type text NOT NULL,
    file_size_bytes integer NOT NULL,
    file_checksum text NOT NULL,
    status public.generation_job_status_enum DEFAULT 'queued'::public.generation_job_status_enum NOT NULL,
    provider text NOT NULL,
    model_id text NOT NULL,
    prompt_version text DEFAULT 'v1'::text NOT NULL,
    error_code text,
    error_message_safe text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    started_at timestamp with time zone,
    completed_at timestamp with time zone,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    processing_started_at timestamp with time zone,
    processing_lease_expires_at timestamp with time zone,
    processing_lease_token uuid,
    attempt_count integer DEFAULT 0 NOT NULL,
    max_attempts integer DEFAULT 3 NOT NULL,
    last_heartbeat_at timestamp with time zone,
    CONSTRAINT chk_content_gen_jobs_storage_bucket CHECK ((storage_bucket = 'teacher-materials'::text)),
    CONSTRAINT chk_content_gen_jobs_storage_path_tenant CHECK ((split_part(storage_path, '/'::text, 1) = (tenant_id)::text)),
    CONSTRAINT content_generation_jobs_file_size_bytes_check CHECK (((file_size_bytes > 0) AND (file_size_bytes <= 31457280))),
    CONSTRAINT content_generation_jobs_mime_type_check CHECK ((mime_type = ANY (ARRAY['application/pdf'::text, 'application/vnd.openxmlformats-officedocument.presentationml.presentation'::text])))
);


ALTER TABLE public.content_generation_jobs OWNER TO postgres;

--
-- Name: courses; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.courses (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    tenant_id uuid NOT NULL,
    code text NOT NULL,
    name text NOT NULL,
    description text,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.courses OWNER TO postgres;

--
-- Name: enrollments; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.enrollments (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    tenant_id uuid NOT NULL,
    section_id uuid NOT NULL,
    student_id uuid NOT NULL,
    student_id_pseudo uuid DEFAULT gen_random_uuid() NOT NULL,
    enrolled_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.enrollments OWNER TO postgres;

--
-- Name: knowledge_components; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.knowledge_components (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    tenant_id uuid NOT NULL,
    unit_id uuid NOT NULL,
    name text NOT NULL,
    description text,
    difficulty_prior numeric(4,3) DEFAULT 0.500 NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT knowledge_components_difficulty_prior_check CHECK (((difficulty_prior >= 0.0) AND (difficulty_prior <= 1.0)))
);


ALTER TABLE public.knowledge_components OWNER TO postgres;

--
-- Name: microcontents; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.microcontents (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    tenant_id uuid NOT NULL,
    knowledge_component_id uuid NOT NULL,
    title text NOT NULL,
    content_type public.content_type_enum NOT NULL,
    content_body jsonb NOT NULL,
    estimated_duration_seconds integer DEFAULT 180 NOT NULL,
    created_by uuid NOT NULL,
    is_published boolean DEFAULT false NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT microcontents_estimated_duration_seconds_check CHECK ((estimated_duration_seconds > 0))
);


ALTER TABLE public.microcontents OWNER TO postgres;

--
-- Name: model_versions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.model_versions (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    model_name text NOT NULL,
    version text NOT NULL,
    artifact_uri text NOT NULL,
    metrics jsonb NOT NULL,
    is_active boolean DEFAULT false NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.model_versions OWNER TO postgres;

--
-- Name: notifications; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.notifications (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    tenant_id uuid NOT NULL,
    student_id uuid NOT NULL,
    review_assignment_id uuid,
    notification_type public.notification_type_enum DEFAULT 'review_reminder'::public.notification_type_enum NOT NULL,
    title text NOT NULL,
    body text NOT NULL,
    target_path text NOT NULL,
    deduplication_key text NOT NULL,
    read_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT notifications_body_check CHECK ((char_length(body) > 0)),
    CONSTRAINT notifications_target_path_check CHECK ((char_length(target_path) > 0)),
    CONSTRAINT notifications_title_check CHECK ((char_length(title) > 0))
);


ALTER TABLE public.notifications OWNER TO postgres;

--
-- Name: predictions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.predictions (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    tenant_id uuid NOT NULL,
    student_id uuid NOT NULL,
    knowledge_component_id uuid NOT NULL,
    model_version_id uuid,
    prediction_horizon_hours integer NOT NULL,
    predicted_recall_probability numeric(4,3) NOT NULL,
    estimated_risk numeric(4,3) NOT NULL,
    risk_level public.risk_level_enum DEFAULT 'low'::public.risk_level_enum NOT NULL,
    feature_importance jsonb,
    input_event_cutoff timestamp with time zone NOT NULL,
    prediction_status public.prediction_status_enum NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    predicted_forgetting_time_seconds numeric(12,2),
    tau_threshold numeric(4,3) DEFAULT 0.650 NOT NULL,
    CONSTRAINT predictions_estimated_risk_check CHECK (((estimated_risk >= 0.0) AND (estimated_risk <= 1.0))),
    CONSTRAINT predictions_predicted_recall_probability_check CHECK (((predicted_recall_probability >= 0.0) AND (predicted_recall_probability <= 1.0))),
    CONSTRAINT predictions_prediction_horizon_hours_check CHECK ((prediction_horizon_hours > 0))
);


ALTER TABLE public.predictions OWNER TO postgres;

--
-- Name: profiles; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.profiles (
    id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    student_code text,
    full_name text NOT NULL,
    role public.user_role DEFAULT 'student'::public.user_role NOT NULL,
    avatar_url text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.profiles OWNER TO postgres;

--
-- Name: question_drafts; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.question_drafts (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    tenant_id uuid NOT NULL,
    generation_job_id uuid NOT NULL,
    knowledge_component_id uuid,
    suggested_kc_name text NOT NULL,
    question_text text NOT NULL,
    explanation text NOT NULL,
    options jsonb NOT NULL,
    suggested_difficulty numeric(4,3) DEFAULT 0.500,
    suggested_bloom_level text DEFAULT 'understand'::text,
    source_references jsonb DEFAULT '[]'::jsonb NOT NULL,
    status public.draft_status_enum DEFAULT 'draft'::public.draft_status_enum NOT NULL,
    approved_question_id uuid,
    reviewed_by uuid,
    reviewed_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    content_hash text,
    rejection_reason text,
    CONSTRAINT chk_question_drafts_options_array CHECK ((jsonb_typeof(options) = 'array'::text)),
    CONSTRAINT question_drafts_source_references_check CHECK ((jsonb_typeof(source_references) = 'array'::text)),
    CONSTRAINT question_drafts_suggested_difficulty_check CHECK (((suggested_difficulty >= 0.0) AND (suggested_difficulty <= 1.0)))
);


ALTER TABLE public.question_drafts OWNER TO postgres;

--
-- Name: question_options; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.question_options (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    question_id uuid NOT NULL,
    option_text text NOT NULL,
    is_correct boolean NOT NULL,
    order_index integer DEFAULT 1 NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.question_options OWNER TO postgres;

--
-- Name: questions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.questions (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    tenant_id uuid NOT NULL,
    knowledge_component_id uuid NOT NULL,
    question_text text NOT NULL,
    question_type text DEFAULT 'multiple_choice'::text NOT NULL,
    explanation text NOT NULL,
    difficulty numeric(4,3) DEFAULT 0.500 NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    created_by uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    source_draft_id uuid,
    CONSTRAINT questions_difficulty_check CHECK (((difficulty >= 0.0) AND (difficulty <= 1.0)))
);


ALTER TABLE public.questions OWNER TO postgres;

--
-- Name: quiz_attempts; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.quiz_attempts (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    tenant_id uuid NOT NULL,
    enrollment_id uuid NOT NULL,
    activity_id uuid NOT NULL,
    started_at timestamp with time zone DEFAULT now() NOT NULL,
    completed_at timestamp with time zone,
    score numeric(5,2),
    student_id uuid,
    attempt_number integer DEFAULT 1 NOT NULL,
    status public.attempt_status_enum DEFAULT 'in_progress'::public.attempt_status_enum NOT NULL,
    total_questions integer DEFAULT 0 NOT NULL,
    correct_answers integer DEFAULT 0 NOT NULL,
    idempotency_key uuid,
    submitted_at timestamp with time zone,
    CONSTRAINT quiz_attempts_attempt_number_check CHECK ((attempt_number >= 1)),
    CONSTRAINT quiz_attempts_score_check CHECK (((score IS NULL) OR ((score >= 0.0) AND (score <= 100.0))))
);


ALTER TABLE public.quiz_attempts OWNER TO postgres;

--
-- Name: recommendations; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.recommendations (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    tenant_id uuid NOT NULL,
    prediction_id uuid,
    student_id uuid NOT NULL,
    knowledge_component_id uuid NOT NULL,
    microcontent_id uuid NOT NULL,
    selection_method public.recommendation_method_enum NOT NULL,
    decision_reason text NOT NULL,
    status public.recommendation_status_enum DEFAULT 'pending'::public.recommendation_status_enum NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    policy_name text DEFAULT 'preventive_spaced_repetition'::text NOT NULL,
    policy_version text DEFAULT '1.0.0'::text NOT NULL,
    scheduled_for timestamp with time zone,
    cooldown_until timestamp with time zone,
    completed_at timestamp with time zone,
    expires_at timestamp with time zone,
    idempotency_key uuid
);


ALTER TABLE public.recommendations OWNER TO postgres;

--
-- Name: review_assignments; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.review_assignments (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    tenant_id uuid NOT NULL,
    student_id uuid NOT NULL,
    recommendation_id uuid,
    activity_id uuid NOT NULL,
    due_date timestamp with time zone,
    status public.assignment_status_enum DEFAULT 'assigned'::public.assignment_status_enum NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.review_assignments OWNER TO postgres;

--
-- Name: sections; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.sections (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    tenant_id uuid NOT NULL,
    course_id uuid NOT NULL,
    teacher_id uuid NOT NULL,
    name text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.sections OWNER TO postgres;

--
-- Name: student_knowledge_states; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.student_knowledge_states (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    tenant_id uuid NOT NULL,
    student_id uuid NOT NULL,
    knowledge_component_id uuid NOT NULL,
    p_mastery numeric(4,3) NOT NULL,
    confidence numeric(4,3),
    total_interactions integer DEFAULT 0 NOT NULL,
    last_updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT student_knowledge_states_confidence_check CHECK (((confidence >= 0.0) AND (confidence <= 1.0))),
    CONSTRAINT student_knowledge_states_p_mastery_check CHECK (((p_mastery >= 0.0) AND (p_mastery <= 1.0)))
);


ALTER TABLE public.student_knowledge_states OWNER TO postgres;

--
-- Name: student_metrics; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.student_metrics (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    tenant_id uuid NOT NULL,
    student_id uuid NOT NULL,
    total_attempts integer DEFAULT 0 NOT NULL,
    correct_attempts integer DEFAULT 0 NOT NULL,
    avg_response_time_seconds numeric(6,2) DEFAULT 0.0 NOT NULL,
    retention_rate numeric(4,3) DEFAULT 0.000 NOT NULL,
    streak_days integer DEFAULT 0 NOT NULL,
    last_active_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.student_metrics OWNER TO postgres;

--
-- Name: tenants; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.tenants (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    name text NOT NULL,
    slug text NOT NULL,
    domain text,
    is_active boolean DEFAULT true NOT NULL,
    settings jsonb DEFAULT '{"cold_start_kcs": 3, "risk_threshold": 0.65}'::jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.tenants OWNER TO postgres;

--
-- Name: units; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.units (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    tenant_id uuid NOT NULL,
    course_id uuid NOT NULL,
    title text NOT NULL,
    order_index integer NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.units OWNER TO postgres;

--
-- Name: buckets; Type: TABLE; Schema: storage; Owner: postgres
--

CREATE TABLE storage.buckets (
    id text NOT NULL,
    name text NOT NULL,
    owner uuid,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    public boolean DEFAULT false,
    avif_autodetection boolean DEFAULT false,
    file_size_limit bigint,
    allowed_mime_types text[],
    owner_id text
);


ALTER TABLE storage.buckets OWNER TO postgres;

--
-- Name: objects; Type: TABLE; Schema: storage; Owner: postgres
--

CREATE TABLE storage.objects (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    bucket_id text,
    name text,
    owner uuid,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    last_accessed_at timestamp with time zone DEFAULT now(),
    metadata jsonb,
    path_tokens text[] GENERATED ALWAYS AS (string_to_array(name, '/'::text)) STORED,
    version text,
    owner_id text
);


ALTER TABLE storage.objects OWNER TO postgres;

--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: auth; Owner: postgres
--

ALTER TABLE ONLY auth.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: auth; Owner: postgres
--

ALTER TABLE ONLY auth.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: activities activities_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.activities
    ADD CONSTRAINT activities_pkey PRIMARY KEY (id);


--
-- Name: activity_questions activity_questions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.activity_questions
    ADD CONSTRAINT activity_questions_pkey PRIMARY KEY (activity_id, question_id);


--
-- Name: activity_sections activity_sections_activity_id_section_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.activity_sections
    ADD CONSTRAINT activity_sections_activity_id_section_id_key UNIQUE (activity_id, section_id);


--
-- Name: activity_sections activity_sections_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.activity_sections
    ADD CONSTRAINT activity_sections_pkey PRIMARY KEY (id);


--
-- Name: answer_events answer_events_idempotency_key_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.answer_events
    ADD CONSTRAINT answer_events_idempotency_key_key UNIQUE (idempotency_key);


--
-- Name: answer_events answer_events_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.answer_events
    ADD CONSTRAINT answer_events_pkey PRIMARY KEY (id);


--
-- Name: auth_recovery_pins auth_recovery_pins_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_recovery_pins
    ADD CONSTRAINT auth_recovery_pins_pkey PRIMARY KEY (id);


--
-- Name: content_exposure_events content_exposure_events_idempotency_key_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.content_exposure_events
    ADD CONSTRAINT content_exposure_events_idempotency_key_key UNIQUE (idempotency_key);


--
-- Name: content_exposure_events content_exposure_events_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.content_exposure_events
    ADD CONSTRAINT content_exposure_events_pkey PRIMARY KEY (id);


--
-- Name: content_generation_jobs content_generation_jobs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.content_generation_jobs
    ADD CONSTRAINT content_generation_jobs_pkey PRIMARY KEY (id);


--
-- Name: courses courses_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.courses
    ADD CONSTRAINT courses_pkey PRIMARY KEY (id);


--
-- Name: courses courses_tenant_id_code_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.courses
    ADD CONSTRAINT courses_tenant_id_code_key UNIQUE (tenant_id, code);


--
-- Name: enrollments enrollments_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.enrollments
    ADD CONSTRAINT enrollments_pkey PRIMARY KEY (id);


--
-- Name: enrollments enrollments_section_id_student_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.enrollments
    ADD CONSTRAINT enrollments_section_id_student_id_key UNIQUE (section_id, student_id);


--
-- Name: enrollments enrollments_tenant_id_student_id_pseudo_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.enrollments
    ADD CONSTRAINT enrollments_tenant_id_student_id_pseudo_key UNIQUE (tenant_id, student_id_pseudo);


--
-- Name: knowledge_components knowledge_components_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.knowledge_components
    ADD CONSTRAINT knowledge_components_pkey PRIMARY KEY (id);


--
-- Name: microcontents microcontents_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.microcontents
    ADD CONSTRAINT microcontents_pkey PRIMARY KEY (id);


--
-- Name: model_versions model_versions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.model_versions
    ADD CONSTRAINT model_versions_pkey PRIMARY KEY (id);


--
-- Name: model_versions model_versions_version_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.model_versions
    ADD CONSTRAINT model_versions_version_key UNIQUE (version);


--
-- Name: notifications notifications_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.notifications
    ADD CONSTRAINT notifications_pkey PRIMARY KEY (id);


--
-- Name: notifications notifications_tenant_id_deduplication_key_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.notifications
    ADD CONSTRAINT notifications_tenant_id_deduplication_key_key UNIQUE (tenant_id, deduplication_key);


--
-- Name: predictions predictions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.predictions
    ADD CONSTRAINT predictions_pkey PRIMARY KEY (id);


--
-- Name: profiles profiles_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.profiles
    ADD CONSTRAINT profiles_pkey PRIMARY KEY (id);


--
-- Name: profiles profiles_student_code_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.profiles
    ADD CONSTRAINT profiles_student_code_key UNIQUE (student_code);


--
-- Name: question_drafts question_drafts_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.question_drafts
    ADD CONSTRAINT question_drafts_pkey PRIMARY KEY (id);


--
-- Name: question_options question_options_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.question_options
    ADD CONSTRAINT question_options_pkey PRIMARY KEY (id);


--
-- Name: questions questions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.questions
    ADD CONSTRAINT questions_pkey PRIMARY KEY (id);


--
-- Name: quiz_attempts quiz_attempts_idempotency_key_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.quiz_attempts
    ADD CONSTRAINT quiz_attempts_idempotency_key_key UNIQUE (idempotency_key);


--
-- Name: quiz_attempts quiz_attempts_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.quiz_attempts
    ADD CONSTRAINT quiz_attempts_pkey PRIMARY KEY (id);


--
-- Name: recommendations recommendations_idempotency_key_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.recommendations
    ADD CONSTRAINT recommendations_idempotency_key_key UNIQUE (idempotency_key);


--
-- Name: recommendations recommendations_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.recommendations
    ADD CONSTRAINT recommendations_pkey PRIMARY KEY (id);


--
-- Name: review_assignments review_assignments_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.review_assignments
    ADD CONSTRAINT review_assignments_pkey PRIMARY KEY (id);


--
-- Name: sections sections_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sections
    ADD CONSTRAINT sections_pkey PRIMARY KEY (id);


--
-- Name: student_knowledge_states student_knowledge_states_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.student_knowledge_states
    ADD CONSTRAINT student_knowledge_states_pkey PRIMARY KEY (id);


--
-- Name: student_knowledge_states student_knowledge_states_student_id_knowledge_component_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.student_knowledge_states
    ADD CONSTRAINT student_knowledge_states_student_id_knowledge_component_id_key UNIQUE (student_id, knowledge_component_id);


--
-- Name: student_metrics student_metrics_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.student_metrics
    ADD CONSTRAINT student_metrics_pkey PRIMARY KEY (id);


--
-- Name: student_metrics student_metrics_tenant_id_student_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.student_metrics
    ADD CONSTRAINT student_metrics_tenant_id_student_id_key UNIQUE (tenant_id, student_id);


--
-- Name: tenants tenants_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tenants
    ADD CONSTRAINT tenants_pkey PRIMARY KEY (id);


--
-- Name: tenants tenants_slug_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tenants
    ADD CONSTRAINT tenants_slug_key UNIQUE (slug);


--
-- Name: units units_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.units
    ADD CONSTRAINT units_pkey PRIMARY KEY (id);


--
-- Name: question_drafts uq_question_drafts_approved_question; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.question_drafts
    ADD CONSTRAINT uq_question_drafts_approved_question UNIQUE (approved_question_id);


--
-- Name: buckets buckets_pkey; Type: CONSTRAINT; Schema: storage; Owner: postgres
--

ALTER TABLE ONLY storage.buckets
    ADD CONSTRAINT buckets_pkey PRIMARY KEY (id);


--
-- Name: objects objects_pkey; Type: CONSTRAINT; Schema: storage; Owner: postgres
--

ALTER TABLE ONLY storage.objects
    ADD CONSTRAINT objects_pkey PRIMARY KEY (id);


--
-- Name: idx_activities_course_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_activities_course_status ON public.activities USING btree (course_id, status);


--
-- Name: idx_activities_tenant_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_activities_tenant_status ON public.activities USING btree (tenant_id, status);


--
-- Name: idx_activity_sections_activity; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_activity_sections_activity ON public.activity_sections USING btree (activity_id);


--
-- Name: idx_activity_sections_section; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_activity_sections_section ON public.activity_sections USING btree (section_id);


--
-- Name: idx_answer_events_activity; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_answer_events_activity ON public.answer_events USING btree (activity_id);


--
-- Name: idx_answer_events_attempt; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_answer_events_attempt ON public.answer_events USING btree (attempt_id);


--
-- Name: idx_answer_events_course; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_answer_events_course ON public.answer_events USING btree (course_id);


--
-- Name: idx_answer_events_student_kc; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_answer_events_student_kc ON public.answer_events USING btree (student_id, knowledge_component_id, event_timestamp);


--
-- Name: idx_answer_events_tenant; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_answer_events_tenant ON public.answer_events USING btree (tenant_id);


--
-- Name: idx_content_gen_jobs_course; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_content_gen_jobs_course ON public.content_generation_jobs USING btree (course_id);


--
-- Name: idx_content_gen_jobs_creator; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_content_gen_jobs_creator ON public.content_generation_jobs USING btree (created_by);


--
-- Name: idx_content_gen_jobs_lease_claim; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_content_gen_jobs_lease_claim ON public.content_generation_jobs USING btree (status, processing_lease_expires_at, attempt_count) WHERE (status = ANY (ARRAY['queued'::public.generation_job_status_enum, 'processing'::public.generation_job_status_enum]));


--
-- Name: idx_content_gen_jobs_tenant_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_content_gen_jobs_tenant_status ON public.content_generation_jobs USING btree (tenant_id, status);


--
-- Name: idx_enrollments_section; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_enrollments_section ON public.enrollments USING btree (section_id);


--
-- Name: idx_enrollments_student; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_enrollments_student ON public.enrollments USING btree (student_id);


--
-- Name: idx_exposure_microcontent; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_exposure_microcontent ON public.content_exposure_events USING btree (microcontent_id);


--
-- Name: idx_exposure_pseudo; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_exposure_pseudo ON public.content_exposure_events USING btree (student_id_pseudo);


--
-- Name: idx_exposure_session; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_exposure_session ON public.content_exposure_events USING btree (session_id);


--
-- Name: idx_exposure_student_kc; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_exposure_student_kc ON public.content_exposure_events USING btree (student_id, knowledge_component_id, event_timestamp);


--
-- Name: idx_exposure_tenant; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_exposure_tenant ON public.content_exposure_events USING btree (tenant_id);


--
-- Name: idx_notifications_student_unread; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_notifications_student_unread ON public.notifications USING btree (student_id) WHERE (read_at IS NULL);


--
-- Name: idx_notifications_tenant_student; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_notifications_tenant_student ON public.notifications USING btree (tenant_id, student_id);


--
-- Name: idx_predictions_student_kc; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_predictions_student_kc ON public.predictions USING btree (student_id, knowledge_component_id, created_at DESC);


--
-- Name: idx_predictions_student_kc_created; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_predictions_student_kc_created ON public.predictions USING btree (student_id, knowledge_component_id, created_at DESC);


--
-- Name: idx_predictions_tenant; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_predictions_tenant ON public.predictions USING btree (tenant_id);


--
-- Name: idx_profiles_tenant; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_profiles_tenant ON public.profiles USING btree (tenant_id);


--
-- Name: idx_question_drafts_job; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_question_drafts_job ON public.question_drafts USING btree (generation_job_id);


--
-- Name: idx_question_drafts_kc; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_question_drafts_kc ON public.question_drafts USING btree (knowledge_component_id);


--
-- Name: idx_question_drafts_tenant_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_question_drafts_tenant_status ON public.question_drafts USING btree (tenant_id, status);


--
-- Name: idx_quiz_attempts_active_unique; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX idx_quiz_attempts_active_unique ON public.quiz_attempts USING btree (activity_id, student_id) WHERE (status = 'in_progress'::public.attempt_status_enum);


--
-- Name: idx_quiz_attempts_activity_student; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_quiz_attempts_activity_student ON public.quiz_attempts USING btree (activity_id, student_id);


--
-- Name: idx_quiz_attempts_student; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_quiz_attempts_student ON public.quiz_attempts USING btree (student_id);


--
-- Name: idx_recommendations_idempotency; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_recommendations_idempotency ON public.recommendations USING btree (idempotency_key) WHERE (idempotency_key IS NOT NULL);


--
-- Name: idx_recommendations_student_kc_created; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_recommendations_student_kc_created ON public.recommendations USING btree (student_id, knowledge_component_id, created_at DESC);


--
-- Name: idx_recommendations_student_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_recommendations_student_status ON public.recommendations USING btree (student_id, status);


--
-- Name: idx_recommendations_student_status_pending; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_recommendations_student_status_pending ON public.recommendations USING btree (student_id, status) WHERE (status = 'pending'::public.recommendation_status_enum);


--
-- Name: idx_review_assignments_student_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_review_assignments_student_status ON public.review_assignments USING btree (student_id, status);


--
-- Name: idx_sections_course; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_sections_course ON public.sections USING btree (course_id);


--
-- Name: idx_sections_teacher; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_sections_teacher ON public.sections USING btree (teacher_id);


--
-- Name: uq_content_gen_jobs_active_file; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX uq_content_gen_jobs_active_file ON public.content_generation_jobs USING btree (tenant_id, course_id, file_checksum) NULLS NOT DISTINCT WHERE (status = ANY (ARRAY['queued'::public.generation_job_status_enum, 'processing'::public.generation_job_status_enum]));


--
-- Name: uq_content_gen_jobs_id_tenant; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX uq_content_gen_jobs_id_tenant ON public.content_generation_jobs USING btree (id, tenant_id);


--
-- Name: uq_question_drafts_job_content_hash; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX uq_question_drafts_job_content_hash ON public.question_drafts USING btree (generation_job_id, content_hash) WHERE (content_hash IS NOT NULL);


--
-- Name: uq_questions_source_draft; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX uq_questions_source_draft ON public.questions USING btree (source_draft_id) WHERE (source_draft_id IS NOT NULL);


--
-- Name: content_generation_jobs trg_content_gen_jobs_status_guard; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_content_gen_jobs_status_guard BEFORE INSERT OR DELETE OR UPDATE ON public.content_generation_jobs FOR EACH ROW EXECUTE FUNCTION public.enforce_content_generation_jobs_status_guard();


--
-- Name: content_generation_jobs trg_content_gen_jobs_updated_at; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_content_gen_jobs_updated_at BEFORE UPDATE ON public.content_generation_jobs FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: notifications trg_notifications_student_update; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_notifications_student_update BEFORE UPDATE ON public.notifications FOR EACH ROW EXECUTE FUNCTION public.enforce_notifications_student_update_guard();


--
-- Name: answer_events trg_prevent_answer_events_mutation; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_prevent_answer_events_mutation BEFORE DELETE OR UPDATE ON public.answer_events FOR EACH ROW EXECUTE FUNCTION public.prevent_answer_events_mutation();


--
-- Name: answer_events trg_prevent_answer_events_truncate; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_prevent_answer_events_truncate BEFORE TRUNCATE ON public.answer_events FOR EACH STATEMENT EXECUTE FUNCTION public.prevent_answer_events_mutation();


--
-- Name: content_exposure_events trg_prevent_content_exposure_mutation; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_prevent_content_exposure_mutation BEFORE DELETE OR UPDATE ON public.content_exposure_events FOR EACH ROW EXECUTE FUNCTION public.prevent_content_exposure_mutation();


--
-- Name: content_exposure_events trg_prevent_content_exposure_truncate; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_prevent_content_exposure_truncate BEFORE TRUNCATE ON public.content_exposure_events FOR EACH STATEMENT EXECUTE FUNCTION public.prevent_content_exposure_mutation();


--
-- Name: question_drafts trg_question_drafts_status_guard; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_question_drafts_status_guard BEFORE INSERT OR DELETE OR UPDATE ON public.question_drafts FOR EACH ROW EXECUTE FUNCTION public.enforce_question_drafts_status_guard();


--
-- Name: question_drafts trg_question_drafts_updated_at; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_question_drafts_updated_at BEFORE UPDATE ON public.question_drafts FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: activities activities_course_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.activities
    ADD CONSTRAINT activities_course_id_fkey FOREIGN KEY (course_id) REFERENCES public.courses(id) ON DELETE CASCADE;


--
-- Name: activities activities_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.activities
    ADD CONSTRAINT activities_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.profiles(id) ON DELETE RESTRICT;


--
-- Name: activities activities_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.activities
    ADD CONSTRAINT activities_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.tenants(id) ON DELETE CASCADE;


--
-- Name: activity_questions activity_questions_activity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.activity_questions
    ADD CONSTRAINT activity_questions_activity_id_fkey FOREIGN KEY (activity_id) REFERENCES public.activities(id) ON DELETE CASCADE;


--
-- Name: activity_questions activity_questions_question_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.activity_questions
    ADD CONSTRAINT activity_questions_question_id_fkey FOREIGN KEY (question_id) REFERENCES public.questions(id) ON DELETE CASCADE;


--
-- Name: activity_sections activity_sections_activity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.activity_sections
    ADD CONSTRAINT activity_sections_activity_id_fkey FOREIGN KEY (activity_id) REFERENCES public.activities(id) ON DELETE CASCADE;


--
-- Name: activity_sections activity_sections_section_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.activity_sections
    ADD CONSTRAINT activity_sections_section_id_fkey FOREIGN KEY (section_id) REFERENCES public.sections(id) ON DELETE CASCADE;


--
-- Name: activity_sections activity_sections_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.activity_sections
    ADD CONSTRAINT activity_sections_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.tenants(id) ON DELETE CASCADE;


--
-- Name: answer_events answer_events_activity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.answer_events
    ADD CONSTRAINT answer_events_activity_id_fkey FOREIGN KEY (activity_id) REFERENCES public.activities(id) ON DELETE RESTRICT;


--
-- Name: answer_events answer_events_attempt_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.answer_events
    ADD CONSTRAINT answer_events_attempt_id_fkey FOREIGN KEY (attempt_id) REFERENCES public.quiz_attempts(id) ON DELETE CASCADE;


--
-- Name: answer_events answer_events_course_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.answer_events
    ADD CONSTRAINT answer_events_course_id_fkey FOREIGN KEY (course_id) REFERENCES public.courses(id) ON DELETE RESTRICT;


--
-- Name: answer_events answer_events_knowledge_component_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.answer_events
    ADD CONSTRAINT answer_events_knowledge_component_id_fkey FOREIGN KEY (knowledge_component_id) REFERENCES public.knowledge_components(id) ON DELETE RESTRICT;


--
-- Name: answer_events answer_events_question_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.answer_events
    ADD CONSTRAINT answer_events_question_id_fkey FOREIGN KEY (question_id) REFERENCES public.questions(id) ON DELETE RESTRICT;


--
-- Name: answer_events answer_events_selected_option_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.answer_events
    ADD CONSTRAINT answer_events_selected_option_id_fkey FOREIGN KEY (selected_option_id) REFERENCES public.question_options(id) ON DELETE RESTRICT;


--
-- Name: answer_events answer_events_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.answer_events
    ADD CONSTRAINT answer_events_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.profiles(id) ON DELETE RESTRICT;


--
-- Name: answer_events answer_events_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.answer_events
    ADD CONSTRAINT answer_events_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.tenants(id) ON DELETE CASCADE;


--
-- Name: auth_recovery_pins auth_recovery_pins_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_recovery_pins
    ADD CONSTRAINT auth_recovery_pins_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.profiles(id);


--
-- Name: auth_recovery_pins auth_recovery_pins_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_recovery_pins
    ADD CONSTRAINT auth_recovery_pins_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.profiles(id) ON DELETE CASCADE;


--
-- Name: auth_recovery_pins auth_recovery_pins_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_recovery_pins
    ADD CONSTRAINT auth_recovery_pins_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.tenants(id) ON DELETE CASCADE;


--
-- Name: content_exposure_events content_exposure_events_knowledge_component_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.content_exposure_events
    ADD CONSTRAINT content_exposure_events_knowledge_component_id_fkey FOREIGN KEY (knowledge_component_id) REFERENCES public.knowledge_components(id) ON DELETE RESTRICT;


--
-- Name: content_exposure_events content_exposure_events_microcontent_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.content_exposure_events
    ADD CONSTRAINT content_exposure_events_microcontent_id_fkey FOREIGN KEY (microcontent_id) REFERENCES public.microcontents(id) ON DELETE RESTRICT;


--
-- Name: content_exposure_events content_exposure_events_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.content_exposure_events
    ADD CONSTRAINT content_exposure_events_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.profiles(id) ON DELETE RESTRICT;


--
-- Name: content_exposure_events content_exposure_events_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.content_exposure_events
    ADD CONSTRAINT content_exposure_events_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.tenants(id) ON DELETE CASCADE;


--
-- Name: content_generation_jobs content_generation_jobs_course_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.content_generation_jobs
    ADD CONSTRAINT content_generation_jobs_course_id_fkey FOREIGN KEY (course_id) REFERENCES public.courses(id) ON DELETE RESTRICT;


--
-- Name: content_generation_jobs content_generation_jobs_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.content_generation_jobs
    ADD CONSTRAINT content_generation_jobs_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.profiles(id) ON DELETE RESTRICT;


--
-- Name: content_generation_jobs content_generation_jobs_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.content_generation_jobs
    ADD CONSTRAINT content_generation_jobs_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.tenants(id) ON DELETE CASCADE;


--
-- Name: content_generation_jobs content_generation_jobs_unit_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.content_generation_jobs
    ADD CONSTRAINT content_generation_jobs_unit_id_fkey FOREIGN KEY (unit_id) REFERENCES public.units(id) ON DELETE SET NULL;


--
-- Name: courses courses_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.courses
    ADD CONSTRAINT courses_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.tenants(id) ON DELETE CASCADE;


--
-- Name: enrollments enrollments_section_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.enrollments
    ADD CONSTRAINT enrollments_section_id_fkey FOREIGN KEY (section_id) REFERENCES public.sections(id) ON DELETE CASCADE;


--
-- Name: enrollments enrollments_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.enrollments
    ADD CONSTRAINT enrollments_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.profiles(id) ON DELETE CASCADE;


--
-- Name: enrollments enrollments_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.enrollments
    ADD CONSTRAINT enrollments_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.tenants(id) ON DELETE CASCADE;


--
-- Name: knowledge_components knowledge_components_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.knowledge_components
    ADD CONSTRAINT knowledge_components_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.tenants(id) ON DELETE CASCADE;


--
-- Name: knowledge_components knowledge_components_unit_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.knowledge_components
    ADD CONSTRAINT knowledge_components_unit_id_fkey FOREIGN KEY (unit_id) REFERENCES public.units(id) ON DELETE CASCADE;


--
-- Name: microcontents microcontents_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.microcontents
    ADD CONSTRAINT microcontents_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.profiles(id);


--
-- Name: microcontents microcontents_knowledge_component_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.microcontents
    ADD CONSTRAINT microcontents_knowledge_component_id_fkey FOREIGN KEY (knowledge_component_id) REFERENCES public.knowledge_components(id) ON DELETE RESTRICT;


--
-- Name: microcontents microcontents_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.microcontents
    ADD CONSTRAINT microcontents_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.tenants(id) ON DELETE CASCADE;


--
-- Name: notifications notifications_review_assignment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.notifications
    ADD CONSTRAINT notifications_review_assignment_id_fkey FOREIGN KEY (review_assignment_id) REFERENCES public.review_assignments(id) ON DELETE SET NULL;


--
-- Name: notifications notifications_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.notifications
    ADD CONSTRAINT notifications_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.profiles(id) ON DELETE CASCADE;


--
-- Name: notifications notifications_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.notifications
    ADD CONSTRAINT notifications_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.tenants(id) ON DELETE CASCADE;


--
-- Name: predictions predictions_knowledge_component_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.predictions
    ADD CONSTRAINT predictions_knowledge_component_id_fkey FOREIGN KEY (knowledge_component_id) REFERENCES public.knowledge_components(id) ON DELETE RESTRICT;


--
-- Name: predictions predictions_model_version_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.predictions
    ADD CONSTRAINT predictions_model_version_id_fkey FOREIGN KEY (model_version_id) REFERENCES public.model_versions(id) ON DELETE SET NULL;


--
-- Name: predictions predictions_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.predictions
    ADD CONSTRAINT predictions_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.profiles(id) ON DELETE CASCADE;


--
-- Name: predictions predictions_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.predictions
    ADD CONSTRAINT predictions_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.tenants(id) ON DELETE CASCADE;


--
-- Name: profiles profiles_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.profiles
    ADD CONSTRAINT profiles_id_fkey FOREIGN KEY (id) REFERENCES auth.users(id) ON DELETE CASCADE;


--
-- Name: profiles profiles_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.profiles
    ADD CONSTRAINT profiles_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.tenants(id) ON DELETE CASCADE;


--
-- Name: question_drafts question_drafts_approved_question_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.question_drafts
    ADD CONSTRAINT question_drafts_approved_question_id_fkey FOREIGN KEY (approved_question_id) REFERENCES public.questions(id) ON DELETE SET NULL;


--
-- Name: question_drafts question_drafts_generation_job_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.question_drafts
    ADD CONSTRAINT question_drafts_generation_job_id_fkey FOREIGN KEY (generation_job_id) REFERENCES public.content_generation_jobs(id) ON DELETE CASCADE;


--
-- Name: question_drafts question_drafts_knowledge_component_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.question_drafts
    ADD CONSTRAINT question_drafts_knowledge_component_id_fkey FOREIGN KEY (knowledge_component_id) REFERENCES public.knowledge_components(id) ON DELETE SET NULL;


--
-- Name: question_drafts question_drafts_reviewed_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.question_drafts
    ADD CONSTRAINT question_drafts_reviewed_by_fkey FOREIGN KEY (reviewed_by) REFERENCES public.profiles(id) ON DELETE SET NULL;


--
-- Name: question_drafts question_drafts_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.question_drafts
    ADD CONSTRAINT question_drafts_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.tenants(id) ON DELETE CASCADE;


--
-- Name: question_options question_options_question_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.question_options
    ADD CONSTRAINT question_options_question_id_fkey FOREIGN KEY (question_id) REFERENCES public.questions(id) ON DELETE CASCADE;


--
-- Name: questions questions_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.questions
    ADD CONSTRAINT questions_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.profiles(id);


--
-- Name: questions questions_knowledge_component_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.questions
    ADD CONSTRAINT questions_knowledge_component_id_fkey FOREIGN KEY (knowledge_component_id) REFERENCES public.knowledge_components(id) ON DELETE RESTRICT;


--
-- Name: questions questions_source_draft_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.questions
    ADD CONSTRAINT questions_source_draft_id_fkey FOREIGN KEY (source_draft_id) REFERENCES public.question_drafts(id) ON DELETE SET NULL;


--
-- Name: questions questions_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.questions
    ADD CONSTRAINT questions_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.tenants(id) ON DELETE CASCADE;


--
-- Name: quiz_attempts quiz_attempts_activity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.quiz_attempts
    ADD CONSTRAINT quiz_attempts_activity_id_fkey FOREIGN KEY (activity_id) REFERENCES public.activities(id) ON DELETE RESTRICT;


--
-- Name: quiz_attempts quiz_attempts_enrollment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.quiz_attempts
    ADD CONSTRAINT quiz_attempts_enrollment_id_fkey FOREIGN KEY (enrollment_id) REFERENCES public.enrollments(id) ON DELETE CASCADE;


--
-- Name: quiz_attempts quiz_attempts_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.quiz_attempts
    ADD CONSTRAINT quiz_attempts_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.profiles(id) ON DELETE CASCADE;


--
-- Name: quiz_attempts quiz_attempts_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.quiz_attempts
    ADD CONSTRAINT quiz_attempts_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.tenants(id) ON DELETE CASCADE;


--
-- Name: recommendations recommendations_knowledge_component_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.recommendations
    ADD CONSTRAINT recommendations_knowledge_component_id_fkey FOREIGN KEY (knowledge_component_id) REFERENCES public.knowledge_components(id) ON DELETE RESTRICT;


--
-- Name: recommendations recommendations_microcontent_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.recommendations
    ADD CONSTRAINT recommendations_microcontent_id_fkey FOREIGN KEY (microcontent_id) REFERENCES public.microcontents(id) ON DELETE RESTRICT;


--
-- Name: recommendations recommendations_prediction_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.recommendations
    ADD CONSTRAINT recommendations_prediction_id_fkey FOREIGN KEY (prediction_id) REFERENCES public.predictions(id) ON DELETE SET NULL;


--
-- Name: recommendations recommendations_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.recommendations
    ADD CONSTRAINT recommendations_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.profiles(id) ON DELETE CASCADE;


--
-- Name: recommendations recommendations_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.recommendations
    ADD CONSTRAINT recommendations_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.tenants(id) ON DELETE CASCADE;


--
-- Name: review_assignments review_assignments_activity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.review_assignments
    ADD CONSTRAINT review_assignments_activity_id_fkey FOREIGN KEY (activity_id) REFERENCES public.activities(id) ON DELETE CASCADE;


--
-- Name: review_assignments review_assignments_recommendation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.review_assignments
    ADD CONSTRAINT review_assignments_recommendation_id_fkey FOREIGN KEY (recommendation_id) REFERENCES public.recommendations(id) ON DELETE SET NULL;


--
-- Name: review_assignments review_assignments_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.review_assignments
    ADD CONSTRAINT review_assignments_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.profiles(id) ON DELETE CASCADE;


--
-- Name: review_assignments review_assignments_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.review_assignments
    ADD CONSTRAINT review_assignments_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.tenants(id) ON DELETE CASCADE;


--
-- Name: sections sections_course_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sections
    ADD CONSTRAINT sections_course_id_fkey FOREIGN KEY (course_id) REFERENCES public.courses(id) ON DELETE RESTRICT;


--
-- Name: sections sections_teacher_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sections
    ADD CONSTRAINT sections_teacher_id_fkey FOREIGN KEY (teacher_id) REFERENCES public.profiles(id) ON DELETE RESTRICT;


--
-- Name: sections sections_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sections
    ADD CONSTRAINT sections_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.tenants(id) ON DELETE CASCADE;


--
-- Name: student_knowledge_states student_knowledge_states_knowledge_component_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.student_knowledge_states
    ADD CONSTRAINT student_knowledge_states_knowledge_component_id_fkey FOREIGN KEY (knowledge_component_id) REFERENCES public.knowledge_components(id) ON DELETE CASCADE;


--
-- Name: student_knowledge_states student_knowledge_states_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.student_knowledge_states
    ADD CONSTRAINT student_knowledge_states_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.profiles(id) ON DELETE CASCADE;


--
-- Name: student_knowledge_states student_knowledge_states_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.student_knowledge_states
    ADD CONSTRAINT student_knowledge_states_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.tenants(id) ON DELETE CASCADE;


--
-- Name: student_metrics student_metrics_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.student_metrics
    ADD CONSTRAINT student_metrics_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.profiles(id) ON DELETE CASCADE;


--
-- Name: student_metrics student_metrics_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.student_metrics
    ADD CONSTRAINT student_metrics_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.tenants(id) ON DELETE CASCADE;


--
-- Name: units units_course_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.units
    ADD CONSTRAINT units_course_id_fkey FOREIGN KEY (course_id) REFERENCES public.courses(id) ON DELETE CASCADE;


--
-- Name: units units_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.units
    ADD CONSTRAINT units_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.tenants(id) ON DELETE CASCADE;


--
-- Name: buckets buckets_owner_fkey; Type: FK CONSTRAINT; Schema: storage; Owner: postgres
--

ALTER TABLE ONLY storage.buckets
    ADD CONSTRAINT buckets_owner_fkey FOREIGN KEY (owner) REFERENCES auth.users(id);


--
-- Name: objects objects_bucket_id_fkey; Type: FK CONSTRAINT; Schema: storage; Owner: postgres
--

ALTER TABLE ONLY storage.objects
    ADD CONSTRAINT objects_bucket_id_fkey FOREIGN KEY (bucket_id) REFERENCES storage.buckets(id);


--
-- Name: objects objects_owner_fkey; Type: FK CONSTRAINT; Schema: storage; Owner: postgres
--

ALTER TABLE ONLY storage.objects
    ADD CONSTRAINT objects_owner_fkey FOREIGN KEY (owner) REFERENCES auth.users(id);


--
-- Name: activities; Type: ROW SECURITY; Schema: public; Owner: postgres
--

ALTER TABLE public.activities ENABLE ROW LEVEL SECURITY;

--
-- Name: activities activities_delete_teacher; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY activities_delete_teacher ON public.activities FOR DELETE USING (((status = 'draft'::public.activity_status_enum) AND (public.is_teacher_of_course(course_id) OR (( SELECT public.current_user_role() AS current_user_role) = ANY (ARRAY['super_admin'::public.user_role, 'admin'::public.user_role])))));


--
-- Name: activities activities_insert_teacher; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY activities_insert_teacher ON public.activities FOR INSERT WITH CHECK ((public.is_teacher_of_course(course_id) OR (( SELECT public.current_user_role() AS current_user_role) = ANY (ARRAY['super_admin'::public.user_role, 'admin'::public.user_role]))));


--
-- Name: activities activities_select_policy; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY activities_select_policy ON public.activities FOR SELECT USING ((public.is_teacher_of_course(course_id) OR (( SELECT public.current_user_role() AS current_user_role) = ANY (ARRAY['super_admin'::public.user_role, 'admin'::public.user_role])) OR ((status = 'published'::public.activity_status_enum) AND (is_active = true) AND public.is_student_enrolled_in_activity(( SELECT auth.uid() AS uid), id))));


--
-- Name: activities activities_update_teacher; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY activities_update_teacher ON public.activities FOR UPDATE USING ((public.is_teacher_of_course(course_id) OR (( SELECT public.current_user_role() AS current_user_role) = ANY (ARRAY['super_admin'::public.user_role, 'admin'::public.user_role]))));


--
-- Name: activity_questions; Type: ROW SECURITY; Schema: public; Owner: postgres
--

ALTER TABLE public.activity_questions ENABLE ROW LEVEL SECURITY;

--
-- Name: activity_questions activity_questions_manage_teacher; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY activity_questions_manage_teacher ON public.activity_questions USING ((EXISTS ( SELECT 1
   FROM public.activities a
  WHERE ((a.id = activity_questions.activity_id) AND (public.is_teacher_of_course(a.course_id) OR (( SELECT public.current_user_role() AS current_user_role) = ANY (ARRAY['super_admin'::public.user_role, 'admin'::public.user_role])))))));


--
-- Name: activity_questions activity_questions_select; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY activity_questions_select ON public.activity_questions FOR SELECT USING ((EXISTS ( SELECT 1
   FROM public.activities a
  WHERE ((a.id = activity_questions.activity_id) AND (public.is_teacher_of_course(a.course_id) OR (( SELECT public.current_user_role() AS current_user_role) = ANY (ARRAY['super_admin'::public.user_role, 'admin'::public.user_role])) OR ((a.status = 'published'::public.activity_status_enum) AND (a.is_active = true) AND public.is_student_enrolled_in_activity(( SELECT auth.uid() AS uid), a.id)))))));


--
-- Name: activity_sections; Type: ROW SECURITY; Schema: public; Owner: postgres
--

ALTER TABLE public.activity_sections ENABLE ROW LEVEL SECURITY;

--
-- Name: activity_sections activity_sections_manage_teacher; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY activity_sections_manage_teacher ON public.activity_sections USING ((EXISTS ( SELECT 1
   FROM public.activities a
  WHERE ((a.id = activity_sections.activity_id) AND (public.is_teacher_of_course(a.course_id) OR (( SELECT public.current_user_role() AS current_user_role) = ANY (ARRAY['super_admin'::public.user_role, 'admin'::public.user_role])))))));


--
-- Name: activity_sections activity_sections_select; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY activity_sections_select ON public.activity_sections FOR SELECT USING (((EXISTS ( SELECT 1
   FROM public.activities a
  WHERE ((a.id = activity_sections.activity_id) AND (public.is_teacher_of_course(a.course_id) OR (( SELECT public.current_user_role() AS current_user_role) = ANY (ARRAY['super_admin'::public.user_role, 'admin'::public.user_role])))))) OR (EXISTS ( SELECT 1
   FROM public.enrollments e
  WHERE ((e.section_id = activity_sections.section_id) AND (e.student_id = ( SELECT auth.uid() AS uid)))))));


--
-- Name: answer_events; Type: ROW SECURITY; Schema: public; Owner: postgres
--

ALTER TABLE public.answer_events ENABLE ROW LEVEL SECURITY;

--
-- Name: answer_events answer_events_insert; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY answer_events_insert ON public.answer_events FOR INSERT WITH CHECK ((student_id = ( SELECT auth.uid() AS uid)));


--
-- Name: answer_events answer_events_select; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY answer_events_select ON public.answer_events FOR SELECT USING (((student_id = ( SELECT auth.uid() AS uid)) OR ( SELECT public.is_teacher_of_student(answer_events.student_id) AS is_teacher_of_student) OR (( SELECT public.current_user_role() AS current_user_role) = ANY (ARRAY['super_admin'::public.user_role, 'admin'::public.user_role]))));


--
-- Name: quiz_attempts attempts_insert_student; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY attempts_insert_student ON public.quiz_attempts FOR INSERT WITH CHECK (((student_id = ( SELECT auth.uid() AS uid)) OR (EXISTS ( SELECT 1
   FROM public.enrollments e
  WHERE ((e.id = quiz_attempts.enrollment_id) AND (e.student_id = ( SELECT auth.uid() AS uid)))))));


--
-- Name: quiz_attempts attempts_student_access; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY attempts_student_access ON public.quiz_attempts FOR SELECT USING (((student_id = ( SELECT auth.uid() AS uid)) OR (EXISTS ( SELECT 1
   FROM public.enrollments e
  WHERE ((e.id = quiz_attempts.enrollment_id) AND (e.student_id = ( SELECT auth.uid() AS uid))))) OR (( SELECT public.current_user_role() AS current_user_role) = ANY (ARRAY['super_admin'::public.user_role, 'admin'::public.user_role])) OR (EXISTS ( SELECT 1
   FROM (public.enrollments e
     JOIN public.sections s ON ((s.id = e.section_id)))
  WHERE ((e.id = quiz_attempts.enrollment_id) AND (s.teacher_id = ( SELECT auth.uid() AS uid)))))));


--
-- Name: quiz_attempts attempts_update_student; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY attempts_update_student ON public.quiz_attempts FOR UPDATE USING (((student_id = ( SELECT auth.uid() AS uid)) OR (EXISTS ( SELECT 1
   FROM public.enrollments e
  WHERE ((e.id = quiz_attempts.enrollment_id) AND (e.student_id = ( SELECT auth.uid() AS uid))))) OR (( SELECT public.current_user_role() AS current_user_role) = ANY (ARRAY['super_admin'::public.user_role, 'admin'::public.user_role]))));


--
-- Name: auth_recovery_pins; Type: ROW SECURITY; Schema: public; Owner: postgres
--

ALTER TABLE public.auth_recovery_pins ENABLE ROW LEVEL SECURITY;

--
-- Name: content_exposure_events; Type: ROW SECURITY; Schema: public; Owner: postgres
--

ALTER TABLE public.content_exposure_events ENABLE ROW LEVEL SECURITY;

--
-- Name: content_exposure_events content_exposure_events_insert; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY content_exposure_events_insert ON public.content_exposure_events FOR INSERT WITH CHECK ((student_id = ( SELECT auth.uid() AS uid)));


--
-- Name: content_exposure_events content_exposure_events_select; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY content_exposure_events_select ON public.content_exposure_events FOR SELECT USING (((student_id = ( SELECT auth.uid() AS uid)) OR ( SELECT public.is_teacher_of_student(content_exposure_events.student_id) AS is_teacher_of_student) OR (( SELECT public.current_user_role() AS current_user_role) = ANY (ARRAY['super_admin'::public.user_role, 'admin'::public.user_role]))));


--
-- Name: content_generation_jobs content_gen_jobs_delete; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY content_gen_jobs_delete ON public.content_generation_jobs FOR DELETE USING (((( SELECT public.current_user_role() AS current_user_role) = 'super_admin'::public.user_role) OR ((tenant_id = ( SELECT public.current_user_tenant_id() AS current_user_tenant_id)) AND ((( SELECT public.current_user_role() AS current_user_role) = 'admin'::public.user_role) OR ((created_by = ( SELECT auth.uid() AS uid)) AND ((course_id IS NULL) OR public.is_teacher_of_course(course_id)))))));


--
-- Name: content_generation_jobs content_gen_jobs_insert; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY content_gen_jobs_insert ON public.content_generation_jobs FOR INSERT WITH CHECK (((status = 'queued'::public.generation_job_status_enum) AND (tenant_id = ( SELECT public.current_user_tenant_id() AS current_user_tenant_id)) AND (created_by = ( SELECT auth.uid() AS uid)) AND (( SELECT public.current_user_role() AS current_user_role) = ANY (ARRAY['teacher'::public.user_role, 'admin'::public.user_role, 'super_admin'::public.user_role])) AND ((( SELECT public.current_user_role() AS current_user_role) = ANY (ARRAY['super_admin'::public.user_role, 'admin'::public.user_role])) OR (course_id IS NULL) OR public.is_teacher_of_course(course_id)) AND (split_part(storage_path, '/'::text, 1) = (( SELECT public.current_user_tenant_id() AS current_user_tenant_id))::text) AND (storage_bucket = 'teacher-materials'::text)));


--
-- Name: content_generation_jobs content_gen_jobs_select; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY content_gen_jobs_select ON public.content_generation_jobs FOR SELECT USING (((( SELECT public.current_user_role() AS current_user_role) = 'super_admin'::public.user_role) OR ((tenant_id = ( SELECT public.current_user_tenant_id() AS current_user_tenant_id)) AND ((( SELECT public.current_user_role() AS current_user_role) = 'admin'::public.user_role) OR ((created_by = ( SELECT auth.uid() AS uid)) AND ((course_id IS NULL) OR public.is_teacher_of_course(course_id)))))));


--
-- Name: content_generation_jobs content_gen_jobs_update; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY content_gen_jobs_update ON public.content_generation_jobs FOR UPDATE USING (((( SELECT public.current_user_role() AS current_user_role) = 'super_admin'::public.user_role) OR ((tenant_id = ( SELECT public.current_user_tenant_id() AS current_user_tenant_id)) AND ((( SELECT public.current_user_role() AS current_user_role) = 'admin'::public.user_role) OR ((created_by = ( SELECT auth.uid() AS uid)) AND ((course_id IS NULL) OR public.is_teacher_of_course(course_id))))))) WITH CHECK (((( SELECT public.current_user_role() AS current_user_role) = 'super_admin'::public.user_role) OR ((tenant_id = ( SELECT public.current_user_tenant_id() AS current_user_tenant_id)) AND (( SELECT public.current_user_role() AS current_user_role) = 'admin'::public.user_role))));


--
-- Name: content_generation_jobs; Type: ROW SECURITY; Schema: public; Owner: postgres
--

ALTER TABLE public.content_generation_jobs ENABLE ROW LEVEL SECURITY;

--
-- Name: courses; Type: ROW SECURITY; Schema: public; Owner: postgres
--

ALTER TABLE public.courses ENABLE ROW LEVEL SECURITY;

--
-- Name: courses courses_select_tenant; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY courses_select_tenant ON public.courses FOR SELECT USING ((tenant_id = ( SELECT public.current_user_tenant_id() AS current_user_tenant_id)));


--
-- Name: enrollments; Type: ROW SECURITY; Schema: public; Owner: postgres
--

ALTER TABLE public.enrollments ENABLE ROW LEVEL SECURITY;

--
-- Name: enrollments enrollments_select_policy; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY enrollments_select_policy ON public.enrollments FOR SELECT USING (((student_id = ( SELECT auth.uid() AS uid)) OR (( SELECT public.current_user_role() AS current_user_role) = ANY (ARRAY['super_admin'::public.user_role, 'admin'::public.user_role])) OR (EXISTS ( SELECT 1
   FROM public.sections s
  WHERE ((s.id = enrollments.section_id) AND (s.teacher_id = ( SELECT auth.uid() AS uid)))))));


--
-- Name: knowledge_components kc_select_tenant; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY kc_select_tenant ON public.knowledge_components FOR SELECT USING ((tenant_id = ( SELECT public.current_user_tenant_id() AS current_user_tenant_id)));


--
-- Name: knowledge_components; Type: ROW SECURITY; Schema: public; Owner: postgres
--

ALTER TABLE public.knowledge_components ENABLE ROW LEVEL SECURITY;

--
-- Name: microcontents; Type: ROW SECURITY; Schema: public; Owner: postgres
--

ALTER TABLE public.microcontents ENABLE ROW LEVEL SECURITY;

--
-- Name: microcontents microcontents_select_tenant; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY microcontents_select_tenant ON public.microcontents FOR SELECT USING (((tenant_id = ( SELECT public.current_user_tenant_id() AS current_user_tenant_id)) AND ((is_published = true) OR (created_by = ( SELECT auth.uid() AS uid)))));


--
-- Name: activities ml_worker_activities_policy; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY ml_worker_activities_policy ON public.activities TO ml_api_worker USING (true) WITH CHECK (true);


--
-- Name: activity_questions ml_worker_activity_questions_policy; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY ml_worker_activity_questions_policy ON public.activity_questions TO ml_api_worker USING (true) WITH CHECK (true);


--
-- Name: activity_sections ml_worker_activity_sections_policy; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY ml_worker_activity_sections_policy ON public.activity_sections TO ml_api_worker USING (true) WITH CHECK (true);


--
-- Name: answer_events ml_worker_answer_events_policy; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY ml_worker_answer_events_policy ON public.answer_events TO ml_api_worker USING (true) WITH CHECK (true);


--
-- Name: question_drafts ml_worker_drafts_policy; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY ml_worker_drafts_policy ON public.question_drafts TO ml_api_worker USING (true) WITH CHECK (true);


--
-- Name: content_generation_jobs ml_worker_jobs_policy; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY ml_worker_jobs_policy ON public.content_generation_jobs TO ml_api_worker USING (true) WITH CHECK (true);


--
-- Name: question_options ml_worker_question_options_policy; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY ml_worker_question_options_policy ON public.question_options TO ml_api_worker USING (true) WITH CHECK (true);


--
-- Name: questions ml_worker_questions_policy; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY ml_worker_questions_policy ON public.questions TO ml_api_worker USING (true) WITH CHECK (true);


--
-- Name: quiz_attempts ml_worker_quiz_attempts_policy; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY ml_worker_quiz_attempts_policy ON public.quiz_attempts TO ml_api_worker USING (true) WITH CHECK (true);


--
-- Name: model_versions; Type: ROW SECURITY; Schema: public; Owner: postgres
--

ALTER TABLE public.model_versions ENABLE ROW LEVEL SECURITY;

--
-- Name: model_versions model_versions_select; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY model_versions_select ON public.model_versions FOR SELECT USING (true);


--
-- Name: notifications; Type: ROW SECURITY; Schema: public; Owner: postgres
--

ALTER TABLE public.notifications ENABLE ROW LEVEL SECURITY;

--
-- Name: notifications notifications_delete; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY notifications_delete ON public.notifications FOR DELETE USING (((( SELECT public.current_user_role() AS current_user_role) = 'super_admin'::public.user_role) OR ((tenant_id = ( SELECT public.current_user_tenant_id() AS current_user_tenant_id)) AND (( SELECT public.current_user_role() AS current_user_role) = 'admin'::public.user_role))));


--
-- Name: notifications notifications_insert; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY notifications_insert ON public.notifications FOR INSERT WITH CHECK (((( SELECT public.current_user_role() AS current_user_role) = 'super_admin'::public.user_role) OR ((tenant_id = ( SELECT public.current_user_tenant_id() AS current_user_tenant_id)) AND ((( SELECT public.current_user_role() AS current_user_role) = 'admin'::public.user_role) OR ( SELECT public.is_teacher_of_student(notifications.student_id) AS is_teacher_of_student)))));


--
-- Name: notifications notifications_select; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY notifications_select ON public.notifications FOR SELECT USING (((( SELECT public.current_user_role() AS current_user_role) = 'super_admin'::public.user_role) OR ((tenant_id = ( SELECT public.current_user_tenant_id() AS current_user_tenant_id)) AND ((student_id = ( SELECT auth.uid() AS uid)) OR ( SELECT public.is_teacher_of_student(notifications.student_id) AS is_teacher_of_student) OR (( SELECT public.current_user_role() AS current_user_role) = 'admin'::public.user_role)))));


--
-- Name: notifications notifications_update; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY notifications_update ON public.notifications FOR UPDATE USING (((( SELECT public.current_user_role() AS current_user_role) = 'super_admin'::public.user_role) OR ((tenant_id = ( SELECT public.current_user_tenant_id() AS current_user_tenant_id)) AND ((student_id = ( SELECT auth.uid() AS uid)) OR (( SELECT public.current_user_role() AS current_user_role) = 'admin'::public.user_role))))) WITH CHECK (((( SELECT public.current_user_role() AS current_user_role) = 'super_admin'::public.user_role) OR ((tenant_id = ( SELECT public.current_user_tenant_id() AS current_user_tenant_id)) AND ((student_id = ( SELECT auth.uid() AS uid)) OR (( SELECT public.current_user_role() AS current_user_role) = 'admin'::public.user_role)))));


--
-- Name: question_options options_select_all; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY options_select_all ON public.question_options FOR SELECT USING ((EXISTS ( SELECT 1
   FROM public.questions q
  WHERE ((q.id = question_options.question_id) AND (q.tenant_id = ( SELECT public.current_user_tenant_id() AS current_user_tenant_id))))));


--
-- Name: predictions; Type: ROW SECURITY; Schema: public; Owner: postgres
--

ALTER TABLE public.predictions ENABLE ROW LEVEL SECURITY;

--
-- Name: predictions predictions_insert; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY predictions_insert ON public.predictions FOR INSERT WITH CHECK (((student_id = ( SELECT auth.uid() AS uid)) OR ( SELECT (public.current_user_role() = ANY (ARRAY['super_admin'::public.user_role, 'admin'::public.user_role])))));


--
-- Name: predictions predictions_select; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY predictions_select ON public.predictions FOR SELECT USING (((student_id = ( SELECT auth.uid() AS uid)) OR ( SELECT public.is_teacher_of_student(predictions.student_id) AS is_teacher_of_student) OR (( SELECT public.current_user_role() AS current_user_role) = ANY (ARRAY['super_admin'::public.user_role, 'admin'::public.user_role]))));


--
-- Name: profiles; Type: ROW SECURITY; Schema: public; Owner: postgres
--

ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

--
-- Name: profiles profiles_select_own_or_same_tenant; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY profiles_select_own_or_same_tenant ON public.profiles FOR SELECT USING (((id = ( SELECT auth.uid() AS uid)) OR (tenant_id = ( SELECT public.current_user_tenant_id() AS current_user_tenant_id))));


--
-- Name: profiles profiles_update_own; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY profiles_update_own ON public.profiles FOR UPDATE USING ((id = ( SELECT auth.uid() AS uid)));


--
-- Name: question_drafts; Type: ROW SECURITY; Schema: public; Owner: postgres
--

ALTER TABLE public.question_drafts ENABLE ROW LEVEL SECURITY;

--
-- Name: question_drafts question_drafts_delete; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY question_drafts_delete ON public.question_drafts FOR DELETE USING (((( SELECT public.current_user_role() AS current_user_role) = 'super_admin'::public.user_role) OR ((tenant_id = ( SELECT public.current_user_tenant_id() AS current_user_tenant_id)) AND ((( SELECT public.current_user_role() AS current_user_role) = 'admin'::public.user_role) OR (EXISTS ( SELECT 1
   FROM public.content_generation_jobs j
  WHERE ((j.id = question_drafts.generation_job_id) AND (j.created_by = ( SELECT auth.uid() AS uid)) AND ((j.course_id IS NULL) OR public.is_teacher_of_course(j.course_id)))))))));


--
-- Name: question_drafts question_drafts_insert; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY question_drafts_insert ON public.question_drafts FOR INSERT WITH CHECK (((status = 'draft'::public.draft_status_enum) AND (approved_question_id IS NULL) AND ((( SELECT public.current_user_role() AS current_user_role) = 'super_admin'::public.user_role) OR ((tenant_id = ( SELECT public.current_user_tenant_id() AS current_user_tenant_id)) AND (( SELECT public.current_user_role() AS current_user_role) = ANY (ARRAY['teacher'::public.user_role, 'admin'::public.user_role])) AND (EXISTS ( SELECT 1
   FROM public.content_generation_jobs j
  WHERE ((j.id = question_drafts.generation_job_id) AND (j.tenant_id = ( SELECT public.current_user_tenant_id() AS current_user_tenant_id)) AND ((( SELECT public.current_user_role() AS current_user_role) = 'admin'::public.user_role) OR ((j.created_by = ( SELECT auth.uid() AS uid)) AND ((j.course_id IS NULL) OR public.is_teacher_of_course(j.course_id)))))))))));


--
-- Name: question_drafts question_drafts_select; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY question_drafts_select ON public.question_drafts FOR SELECT USING (((( SELECT public.current_user_role() AS current_user_role) = 'super_admin'::public.user_role) OR ((tenant_id = ( SELECT public.current_user_tenant_id() AS current_user_tenant_id)) AND ((( SELECT public.current_user_role() AS current_user_role) = 'admin'::public.user_role) OR (EXISTS ( SELECT 1
   FROM public.content_generation_jobs j
  WHERE ((j.id = question_drafts.generation_job_id) AND (j.created_by = ( SELECT auth.uid() AS uid)) AND ((j.course_id IS NULL) OR public.is_teacher_of_course(j.course_id)))))))));


--
-- Name: question_drafts question_drafts_update; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY question_drafts_update ON public.question_drafts FOR UPDATE USING (((( SELECT public.current_user_role() AS current_user_role) = 'super_admin'::public.user_role) OR ((tenant_id = ( SELECT public.current_user_tenant_id() AS current_user_tenant_id)) AND ((( SELECT public.current_user_role() AS current_user_role) = 'admin'::public.user_role) OR (EXISTS ( SELECT 1
   FROM public.content_generation_jobs j
  WHERE ((j.id = question_drafts.generation_job_id) AND (j.created_by = ( SELECT auth.uid() AS uid)) AND ((j.course_id IS NULL) OR public.is_teacher_of_course(j.course_id))))))))) WITH CHECK (((( SELECT public.current_user_role() AS current_user_role) = 'super_admin'::public.user_role) OR ((tenant_id = ( SELECT public.current_user_tenant_id() AS current_user_tenant_id)) AND (status <> 'approved'::public.draft_status_enum) AND (approved_question_id IS NULL))));


--
-- Name: question_options; Type: ROW SECURITY; Schema: public; Owner: postgres
--

ALTER TABLE public.question_options ENABLE ROW LEVEL SECURITY;

--
-- Name: questions; Type: ROW SECURITY; Schema: public; Owner: postgres
--

ALTER TABLE public.questions ENABLE ROW LEVEL SECURITY;

--
-- Name: questions questions_select_tenant; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY questions_select_tenant ON public.questions FOR SELECT USING ((tenant_id = ( SELECT public.current_user_tenant_id() AS current_user_tenant_id)));


--
-- Name: quiz_attempts; Type: ROW SECURITY; Schema: public; Owner: postgres
--

ALTER TABLE public.quiz_attempts ENABLE ROW LEVEL SECURITY;

--
-- Name: recommendations; Type: ROW SECURITY; Schema: public; Owner: postgres
--

ALTER TABLE public.recommendations ENABLE ROW LEVEL SECURITY;

--
-- Name: recommendations recommendations_insert; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY recommendations_insert ON public.recommendations FOR INSERT WITH CHECK (((student_id = ( SELECT auth.uid() AS uid)) OR ( SELECT (public.current_user_role() = ANY (ARRAY['super_admin'::public.user_role, 'admin'::public.user_role])))));


--
-- Name: recommendations recommendations_select; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY recommendations_select ON public.recommendations FOR SELECT USING (((student_id = ( SELECT auth.uid() AS uid)) OR ( SELECT public.is_teacher_of_student(recommendations.student_id) AS is_teacher_of_student) OR (( SELECT public.current_user_role() AS current_user_role) = ANY (ARRAY['super_admin'::public.user_role, 'admin'::public.user_role]))));


--
-- Name: recommendations recommendations_update; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY recommendations_update ON public.recommendations FOR UPDATE USING (((student_id = ( SELECT auth.uid() AS uid)) OR ( SELECT public.is_teacher_of_student(recommendations.student_id) AS is_teacher_of_student) OR ( SELECT (public.current_user_role() = ANY (ARRAY['super_admin'::public.user_role, 'admin'::public.user_role])))));


--
-- Name: auth_recovery_pins recovery_pins_policy; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY recovery_pins_policy ON public.auth_recovery_pins USING (((( SELECT auth.uid() AS uid) = created_by) OR (( SELECT auth.uid() AS uid) = student_id) OR (( SELECT public.current_user_role() AS current_user_role) = ANY (ARRAY['super_admin'::public.user_role, 'admin'::public.user_role]))));


--
-- Name: review_assignments; Type: ROW SECURITY; Schema: public; Owner: postgres
--

ALTER TABLE public.review_assignments ENABLE ROW LEVEL SECURITY;

--
-- Name: sections; Type: ROW SECURITY; Schema: public; Owner: postgres
--

ALTER TABLE public.sections ENABLE ROW LEVEL SECURITY;

--
-- Name: student_knowledge_states; Type: ROW SECURITY; Schema: public; Owner: postgres
--

ALTER TABLE public.student_knowledge_states ENABLE ROW LEVEL SECURITY;

--
-- Name: student_metrics; Type: ROW SECURITY; Schema: public; Owner: postgres
--

ALTER TABLE public.student_metrics ENABLE ROW LEVEL SECURITY;

--
-- Name: tenants; Type: ROW SECURITY; Schema: public; Owner: postgres
--

ALTER TABLE public.tenants ENABLE ROW LEVEL SECURITY;

--
-- Name: units; Type: ROW SECURITY; Schema: public; Owner: postgres
--

ALTER TABLE public.units ENABLE ROW LEVEL SECURITY;

--
-- Name: units units_select_tenant; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY units_select_tenant ON public.units FOR SELECT USING ((tenant_id = ( SELECT public.current_user_tenant_id() AS current_user_tenant_id)));


--
-- Name: objects; Type: ROW SECURITY; Schema: storage; Owner: postgres
--

ALTER TABLE storage.objects ENABLE ROW LEVEL SECURITY;

--
-- Name: objects storage_teacher_materials_delete; Type: POLICY; Schema: storage; Owner: postgres
--

CREATE POLICY storage_teacher_materials_delete ON storage.objects FOR DELETE USING (((bucket_id = 'teacher-materials'::text) AND ((( SELECT public.current_user_role() AS current_user_role) = 'super_admin'::public.user_role) OR ((split_part(name, '/'::text, 1) = (( SELECT public.current_user_tenant_id() AS current_user_tenant_id))::text) AND ((( SELECT public.current_user_role() AS current_user_role) = 'admin'::public.user_role) OR ((( SELECT public.current_user_role() AS current_user_role) = 'teacher'::public.user_role) AND (auth.uid() = owner)))))));


--
-- Name: objects storage_teacher_materials_insert; Type: POLICY; Schema: storage; Owner: postgres
--

CREATE POLICY storage_teacher_materials_insert ON storage.objects FOR INSERT WITH CHECK (((bucket_id = 'teacher-materials'::text) AND (auth.uid() = owner) AND ((( SELECT public.current_user_role() AS current_user_role) = 'super_admin'::public.user_role) OR ((( SELECT public.current_user_role() AS current_user_role) = ANY (ARRAY['teacher'::public.user_role, 'admin'::public.user_role])) AND (split_part(name, '/'::text, 1) = (( SELECT public.current_user_tenant_id() AS current_user_tenant_id))::text)))));


--
-- Name: objects storage_teacher_materials_select; Type: POLICY; Schema: storage; Owner: postgres
--

CREATE POLICY storage_teacher_materials_select ON storage.objects FOR SELECT USING (((bucket_id = 'teacher-materials'::text) AND ((( SELECT public.current_user_role() AS current_user_role) = 'super_admin'::public.user_role) OR ((split_part(name, '/'::text, 1) = (( SELECT public.current_user_tenant_id() AS current_user_tenant_id))::text) AND ((( SELECT public.current_user_role() AS current_user_role) = 'admin'::public.user_role) OR ((( SELECT public.current_user_role() AS current_user_role) = 'teacher'::public.user_role) AND (auth.uid() = owner)))))));


--
-- Name: objects storage_teacher_materials_update; Type: POLICY; Schema: storage; Owner: postgres
--

CREATE POLICY storage_teacher_materials_update ON storage.objects FOR UPDATE USING (((bucket_id = 'teacher-materials'::text) AND ((( SELECT public.current_user_role() AS current_user_role) = 'super_admin'::public.user_role) OR ((split_part(name, '/'::text, 1) = (( SELECT public.current_user_tenant_id() AS current_user_tenant_id))::text) AND ((( SELECT public.current_user_role() AS current_user_role) = 'admin'::public.user_role) OR ((( SELECT public.current_user_role() AS current_user_role) = 'teacher'::public.user_role) AND (auth.uid() = owner))))))) WITH CHECK (((bucket_id = 'teacher-materials'::text) AND ((( SELECT public.current_user_role() AS current_user_role) = 'super_admin'::public.user_role) OR ((split_part(name, '/'::text, 1) = (( SELECT public.current_user_tenant_id() AS current_user_tenant_id))::text) AND ((( SELECT public.current_user_role() AS current_user_role) = 'admin'::public.user_role) OR ((( SELECT public.current_user_role() AS current_user_role) = 'teacher'::public.user_role) AND (auth.uid() = owner)))))));


--
-- Name: SCHEMA auth; Type: ACL; Schema: -; Owner: postgres
--

GRANT USAGE ON SCHEMA auth TO anon;
GRANT USAGE ON SCHEMA auth TO authenticated;
GRANT USAGE ON SCHEMA auth TO service_role;


--
-- Name: SCHEMA public; Type: ACL; Schema: -; Owner: pg_database_owner
--

GRANT USAGE ON SCHEMA public TO anon;
GRANT USAGE ON SCHEMA public TO authenticated;
GRANT USAGE ON SCHEMA public TO service_role;
GRANT USAGE ON SCHEMA public TO ml_api_worker;


--
-- Name: SCHEMA storage; Type: ACL; Schema: -; Owner: postgres
--

GRANT USAGE ON SCHEMA storage TO anon;
GRANT USAGE ON SCHEMA storage TO authenticated;
GRANT USAGE ON SCHEMA storage TO service_role;


--
-- Name: FUNCTION role(); Type: ACL; Schema: auth; Owner: postgres
--

GRANT ALL ON FUNCTION auth.role() TO anon;
GRANT ALL ON FUNCTION auth.role() TO authenticated;
GRANT ALL ON FUNCTION auth.role() TO service_role;


--
-- Name: FUNCTION uid(); Type: ACL; Schema: auth; Owner: postgres
--

GRANT ALL ON FUNCTION auth.uid() TO anon;
GRANT ALL ON FUNCTION auth.uid() TO authenticated;
GRANT ALL ON FUNCTION auth.uid() TO service_role;


--
-- Name: FUNCTION _add(text, integer); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._add(text, integer) TO anon;
GRANT ALL ON FUNCTION public._add(text, integer) TO authenticated;
GRANT ALL ON FUNCTION public._add(text, integer) TO service_role;


--
-- Name: FUNCTION _add(text, integer, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._add(text, integer, text) TO anon;
GRANT ALL ON FUNCTION public._add(text, integer, text) TO authenticated;
GRANT ALL ON FUNCTION public._add(text, integer, text) TO service_role;


--
-- Name: FUNCTION _alike(boolean, anyelement, text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._alike(boolean, anyelement, text, text) TO anon;
GRANT ALL ON FUNCTION public._alike(boolean, anyelement, text, text) TO authenticated;
GRANT ALL ON FUNCTION public._alike(boolean, anyelement, text, text) TO service_role;


--
-- Name: FUNCTION _ancestor_of(name, name, integer); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._ancestor_of(name, name, integer) TO anon;
GRANT ALL ON FUNCTION public._ancestor_of(name, name, integer) TO authenticated;
GRANT ALL ON FUNCTION public._ancestor_of(name, name, integer) TO service_role;


--
-- Name: FUNCTION _ancestor_of(name, name, name, name, integer); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._ancestor_of(name, name, name, name, integer) TO anon;
GRANT ALL ON FUNCTION public._ancestor_of(name, name, name, name, integer) TO authenticated;
GRANT ALL ON FUNCTION public._ancestor_of(name, name, name, name, integer) TO service_role;


--
-- Name: FUNCTION _are(text, name[], name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._are(text, name[], name[], text) TO anon;
GRANT ALL ON FUNCTION public._are(text, name[], name[], text) TO authenticated;
GRANT ALL ON FUNCTION public._are(text, name[], name[], text) TO service_role;


--
-- Name: FUNCTION _areni(text, text[], text[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._areni(text, text[], text[], text) TO anon;
GRANT ALL ON FUNCTION public._areni(text, text[], text[], text) TO authenticated;
GRANT ALL ON FUNCTION public._areni(text, text[], text[], text) TO service_role;


--
-- Name: FUNCTION _array_to_sorted_string(name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._array_to_sorted_string(name[], text) TO anon;
GRANT ALL ON FUNCTION public._array_to_sorted_string(name[], text) TO authenticated;
GRANT ALL ON FUNCTION public._array_to_sorted_string(name[], text) TO service_role;


--
-- Name: FUNCTION _assets_are(text, text[], text[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._assets_are(text, text[], text[], text) TO anon;
GRANT ALL ON FUNCTION public._assets_are(text, text[], text[], text) TO authenticated;
GRANT ALL ON FUNCTION public._assets_are(text, text[], text[], text) TO service_role;


--
-- Name: FUNCTION _cast_exists(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._cast_exists(name, name) TO anon;
GRANT ALL ON FUNCTION public._cast_exists(name, name) TO authenticated;
GRANT ALL ON FUNCTION public._cast_exists(name, name) TO service_role;


--
-- Name: FUNCTION _cast_exists(name, name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._cast_exists(name, name, name) TO anon;
GRANT ALL ON FUNCTION public._cast_exists(name, name, name) TO authenticated;
GRANT ALL ON FUNCTION public._cast_exists(name, name, name) TO service_role;


--
-- Name: FUNCTION _cast_exists(name, name, name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._cast_exists(name, name, name, name) TO anon;
GRANT ALL ON FUNCTION public._cast_exists(name, name, name, name) TO authenticated;
GRANT ALL ON FUNCTION public._cast_exists(name, name, name, name) TO service_role;


--
-- Name: FUNCTION _cdi(name, name, anyelement); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._cdi(name, name, anyelement) TO anon;
GRANT ALL ON FUNCTION public._cdi(name, name, anyelement) TO authenticated;
GRANT ALL ON FUNCTION public._cdi(name, name, anyelement) TO service_role;


--
-- Name: FUNCTION _cdi(name, name, anyelement, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._cdi(name, name, anyelement, text) TO anon;
GRANT ALL ON FUNCTION public._cdi(name, name, anyelement, text) TO authenticated;
GRANT ALL ON FUNCTION public._cdi(name, name, anyelement, text) TO service_role;


--
-- Name: FUNCTION _cdi(name, name, name, anyelement, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._cdi(name, name, name, anyelement, text) TO anon;
GRANT ALL ON FUNCTION public._cdi(name, name, name, anyelement, text) TO authenticated;
GRANT ALL ON FUNCTION public._cdi(name, name, name, anyelement, text) TO service_role;


--
-- Name: FUNCTION _cexists(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._cexists(name, name) TO anon;
GRANT ALL ON FUNCTION public._cexists(name, name) TO authenticated;
GRANT ALL ON FUNCTION public._cexists(name, name) TO service_role;


--
-- Name: FUNCTION _cexists(name, name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._cexists(name, name, name) TO anon;
GRANT ALL ON FUNCTION public._cexists(name, name, name) TO authenticated;
GRANT ALL ON FUNCTION public._cexists(name, name, name) TO service_role;


--
-- Name: FUNCTION _ckeys(name, character); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._ckeys(name, character) TO anon;
GRANT ALL ON FUNCTION public._ckeys(name, character) TO authenticated;
GRANT ALL ON FUNCTION public._ckeys(name, character) TO service_role;


--
-- Name: FUNCTION _ckeys(name, name, character); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._ckeys(name, name, character) TO anon;
GRANT ALL ON FUNCTION public._ckeys(name, name, character) TO authenticated;
GRANT ALL ON FUNCTION public._ckeys(name, name, character) TO service_role;


--
-- Name: FUNCTION _cleanup(); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._cleanup() TO anon;
GRANT ALL ON FUNCTION public._cleanup() TO authenticated;
GRANT ALL ON FUNCTION public._cleanup() TO service_role;


--
-- Name: FUNCTION _cmp_types(oid, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._cmp_types(oid, name) TO anon;
GRANT ALL ON FUNCTION public._cmp_types(oid, name) TO authenticated;
GRANT ALL ON FUNCTION public._cmp_types(oid, name) TO service_role;


--
-- Name: FUNCTION _col_is_null(name, name, text, boolean); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._col_is_null(name, name, text, boolean) TO anon;
GRANT ALL ON FUNCTION public._col_is_null(name, name, text, boolean) TO authenticated;
GRANT ALL ON FUNCTION public._col_is_null(name, name, text, boolean) TO service_role;


--
-- Name: FUNCTION _col_is_null(name, name, name, text, boolean); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._col_is_null(name, name, name, text, boolean) TO anon;
GRANT ALL ON FUNCTION public._col_is_null(name, name, name, text, boolean) TO authenticated;
GRANT ALL ON FUNCTION public._col_is_null(name, name, name, text, boolean) TO service_role;


--
-- Name: FUNCTION _constraint(name, character, name[], text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._constraint(name, character, name[], text, text) TO anon;
GRANT ALL ON FUNCTION public._constraint(name, character, name[], text, text) TO authenticated;
GRANT ALL ON FUNCTION public._constraint(name, character, name[], text, text) TO service_role;


--
-- Name: FUNCTION _constraint(name, name, character, name[], text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._constraint(name, name, character, name[], text, text) TO anon;
GRANT ALL ON FUNCTION public._constraint(name, name, character, name[], text, text) TO authenticated;
GRANT ALL ON FUNCTION public._constraint(name, name, character, name[], text, text) TO service_role;


--
-- Name: FUNCTION _contract_on(text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._contract_on(text) TO anon;
GRANT ALL ON FUNCTION public._contract_on(text) TO authenticated;
GRANT ALL ON FUNCTION public._contract_on(text) TO service_role;


--
-- Name: FUNCTION _currtest(); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._currtest() TO anon;
GRANT ALL ON FUNCTION public._currtest() TO authenticated;
GRANT ALL ON FUNCTION public._currtest() TO service_role;


--
-- Name: FUNCTION _db_privs(); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._db_privs() TO anon;
GRANT ALL ON FUNCTION public._db_privs() TO authenticated;
GRANT ALL ON FUNCTION public._db_privs() TO service_role;


--
-- Name: FUNCTION _def_is(text, text, anyelement, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._def_is(text, text, anyelement, text) TO anon;
GRANT ALL ON FUNCTION public._def_is(text, text, anyelement, text) TO authenticated;
GRANT ALL ON FUNCTION public._def_is(text, text, anyelement, text) TO service_role;


--
-- Name: FUNCTION _definer(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._definer(name) TO anon;
GRANT ALL ON FUNCTION public._definer(name) TO authenticated;
GRANT ALL ON FUNCTION public._definer(name) TO service_role;


--
-- Name: FUNCTION _definer(name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._definer(name, name[]) TO anon;
GRANT ALL ON FUNCTION public._definer(name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public._definer(name, name[]) TO service_role;


--
-- Name: FUNCTION _definer(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._definer(name, name) TO anon;
GRANT ALL ON FUNCTION public._definer(name, name) TO authenticated;
GRANT ALL ON FUNCTION public._definer(name, name) TO service_role;


--
-- Name: FUNCTION _definer(name, name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._definer(name, name, name[]) TO anon;
GRANT ALL ON FUNCTION public._definer(name, name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public._definer(name, name, name[]) TO service_role;


--
-- Name: FUNCTION _dexists(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._dexists(name) TO anon;
GRANT ALL ON FUNCTION public._dexists(name) TO authenticated;
GRANT ALL ON FUNCTION public._dexists(name) TO service_role;


--
-- Name: FUNCTION _dexists(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._dexists(name, name) TO anon;
GRANT ALL ON FUNCTION public._dexists(name, name) TO authenticated;
GRANT ALL ON FUNCTION public._dexists(name, name) TO service_role;


--
-- Name: FUNCTION _do_ne(text, text, text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._do_ne(text, text, text, text) TO anon;
GRANT ALL ON FUNCTION public._do_ne(text, text, text, text) TO authenticated;
GRANT ALL ON FUNCTION public._do_ne(text, text, text, text) TO service_role;


--
-- Name: FUNCTION _docomp(text, text, text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._docomp(text, text, text, text) TO anon;
GRANT ALL ON FUNCTION public._docomp(text, text, text, text) TO authenticated;
GRANT ALL ON FUNCTION public._docomp(text, text, text, text) TO service_role;


--
-- Name: FUNCTION _error_diag(text, text, text, text, text, text, text, text, text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._error_diag(text, text, text, text, text, text, text, text, text, text) TO anon;
GRANT ALL ON FUNCTION public._error_diag(text, text, text, text, text, text, text, text, text, text) TO authenticated;
GRANT ALL ON FUNCTION public._error_diag(text, text, text, text, text, text, text, text, text, text) TO service_role;


--
-- Name: FUNCTION _expand_context(character); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._expand_context(character) TO anon;
GRANT ALL ON FUNCTION public._expand_context(character) TO authenticated;
GRANT ALL ON FUNCTION public._expand_context(character) TO service_role;


--
-- Name: FUNCTION _expand_on(character); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._expand_on(character) TO anon;
GRANT ALL ON FUNCTION public._expand_on(character) TO authenticated;
GRANT ALL ON FUNCTION public._expand_on(character) TO service_role;


--
-- Name: FUNCTION _expand_vol(character); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._expand_vol(character) TO anon;
GRANT ALL ON FUNCTION public._expand_vol(character) TO authenticated;
GRANT ALL ON FUNCTION public._expand_vol(character) TO service_role;


--
-- Name: FUNCTION _ext_exists(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._ext_exists(name) TO anon;
GRANT ALL ON FUNCTION public._ext_exists(name) TO authenticated;
GRANT ALL ON FUNCTION public._ext_exists(name) TO service_role;


--
-- Name: FUNCTION _ext_exists(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._ext_exists(name, name) TO anon;
GRANT ALL ON FUNCTION public._ext_exists(name, name) TO authenticated;
GRANT ALL ON FUNCTION public._ext_exists(name, name) TO service_role;


--
-- Name: FUNCTION _extensions(); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._extensions() TO anon;
GRANT ALL ON FUNCTION public._extensions() TO authenticated;
GRANT ALL ON FUNCTION public._extensions() TO service_role;


--
-- Name: FUNCTION _extensions(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._extensions(name) TO anon;
GRANT ALL ON FUNCTION public._extensions(name) TO authenticated;
GRANT ALL ON FUNCTION public._extensions(name) TO service_role;


--
-- Name: FUNCTION _extras(character[], name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._extras(character[], name[]) TO anon;
GRANT ALL ON FUNCTION public._extras(character[], name[]) TO authenticated;
GRANT ALL ON FUNCTION public._extras(character[], name[]) TO service_role;


--
-- Name: FUNCTION _extras(character, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._extras(character, name[]) TO anon;
GRANT ALL ON FUNCTION public._extras(character, name[]) TO authenticated;
GRANT ALL ON FUNCTION public._extras(character, name[]) TO service_role;


--
-- Name: FUNCTION _extras(character[], name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._extras(character[], name, name[]) TO anon;
GRANT ALL ON FUNCTION public._extras(character[], name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public._extras(character[], name, name[]) TO service_role;


--
-- Name: FUNCTION _extras(character, name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._extras(character, name, name[]) TO anon;
GRANT ALL ON FUNCTION public._extras(character, name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public._extras(character, name, name[]) TO service_role;


--
-- Name: FUNCTION _finish(integer, integer, integer, boolean); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._finish(integer, integer, integer, boolean) TO anon;
GRANT ALL ON FUNCTION public._finish(integer, integer, integer, boolean) TO authenticated;
GRANT ALL ON FUNCTION public._finish(integer, integer, integer, boolean) TO service_role;


--
-- Name: FUNCTION _fkexists(name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._fkexists(name, name[]) TO anon;
GRANT ALL ON FUNCTION public._fkexists(name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public._fkexists(name, name[]) TO service_role;


--
-- Name: FUNCTION _fkexists(name, name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._fkexists(name, name, name[]) TO anon;
GRANT ALL ON FUNCTION public._fkexists(name, name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public._fkexists(name, name, name[]) TO service_role;


--
-- Name: FUNCTION _fprivs_are(text, name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._fprivs_are(text, name, name[], text) TO anon;
GRANT ALL ON FUNCTION public._fprivs_are(text, name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public._fprivs_are(text, name, name[], text) TO service_role;


--
-- Name: FUNCTION _func_compare(name, name, boolean, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._func_compare(name, name, boolean, text) TO anon;
GRANT ALL ON FUNCTION public._func_compare(name, name, boolean, text) TO authenticated;
GRANT ALL ON FUNCTION public._func_compare(name, name, boolean, text) TO service_role;


--
-- Name: FUNCTION _func_compare(name, name, name[], boolean, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._func_compare(name, name, name[], boolean, text) TO anon;
GRANT ALL ON FUNCTION public._func_compare(name, name, name[], boolean, text) TO authenticated;
GRANT ALL ON FUNCTION public._func_compare(name, name, name[], boolean, text) TO service_role;


--
-- Name: FUNCTION _func_compare(name, name, anyelement, anyelement, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._func_compare(name, name, anyelement, anyelement, text) TO anon;
GRANT ALL ON FUNCTION public._func_compare(name, name, anyelement, anyelement, text) TO authenticated;
GRANT ALL ON FUNCTION public._func_compare(name, name, anyelement, anyelement, text) TO service_role;


--
-- Name: FUNCTION _func_compare(name, name, name[], anyelement, anyelement, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._func_compare(name, name, name[], anyelement, anyelement, text) TO anon;
GRANT ALL ON FUNCTION public._func_compare(name, name, name[], anyelement, anyelement, text) TO authenticated;
GRANT ALL ON FUNCTION public._func_compare(name, name, name[], anyelement, anyelement, text) TO service_role;


--
-- Name: FUNCTION _funkargs(name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._funkargs(name[]) TO anon;
GRANT ALL ON FUNCTION public._funkargs(name[]) TO authenticated;
GRANT ALL ON FUNCTION public._funkargs(name[]) TO service_role;


--
-- Name: FUNCTION _get(text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._get(text) TO anon;
GRANT ALL ON FUNCTION public._get(text) TO authenticated;
GRANT ALL ON FUNCTION public._get(text) TO service_role;


--
-- Name: FUNCTION _get_ac_privs(name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._get_ac_privs(name, text) TO anon;
GRANT ALL ON FUNCTION public._get_ac_privs(name, text) TO authenticated;
GRANT ALL ON FUNCTION public._get_ac_privs(name, text) TO service_role;


--
-- Name: FUNCTION _get_col_ns_type(name, name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._get_col_ns_type(name, name, name) TO anon;
GRANT ALL ON FUNCTION public._get_col_ns_type(name, name, name) TO authenticated;
GRANT ALL ON FUNCTION public._get_col_ns_type(name, name, name) TO service_role;


--
-- Name: FUNCTION _get_col_privs(name, text, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._get_col_privs(name, text, name) TO anon;
GRANT ALL ON FUNCTION public._get_col_privs(name, text, name) TO authenticated;
GRANT ALL ON FUNCTION public._get_col_privs(name, text, name) TO service_role;


--
-- Name: FUNCTION _get_col_type(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._get_col_type(name, name) TO anon;
GRANT ALL ON FUNCTION public._get_col_type(name, name) TO authenticated;
GRANT ALL ON FUNCTION public._get_col_type(name, name) TO service_role;


--
-- Name: FUNCTION _get_col_type(name, name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._get_col_type(name, name, name) TO anon;
GRANT ALL ON FUNCTION public._get_col_type(name, name, name) TO authenticated;
GRANT ALL ON FUNCTION public._get_col_type(name, name, name) TO service_role;


--
-- Name: FUNCTION _get_context(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._get_context(name, name) TO anon;
GRANT ALL ON FUNCTION public._get_context(name, name) TO authenticated;
GRANT ALL ON FUNCTION public._get_context(name, name) TO service_role;


--
-- Name: FUNCTION _get_db_owner(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._get_db_owner(name) TO anon;
GRANT ALL ON FUNCTION public._get_db_owner(name) TO authenticated;
GRANT ALL ON FUNCTION public._get_db_owner(name) TO service_role;


--
-- Name: FUNCTION _get_db_privs(name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._get_db_privs(name, text) TO anon;
GRANT ALL ON FUNCTION public._get_db_privs(name, text) TO authenticated;
GRANT ALL ON FUNCTION public._get_db_privs(name, text) TO service_role;


--
-- Name: FUNCTION _get_dtype(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._get_dtype(name) TO anon;
GRANT ALL ON FUNCTION public._get_dtype(name) TO authenticated;
GRANT ALL ON FUNCTION public._get_dtype(name) TO service_role;


--
-- Name: FUNCTION _get_dtype(name, text, boolean); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._get_dtype(name, text, boolean) TO anon;
GRANT ALL ON FUNCTION public._get_dtype(name, text, boolean) TO authenticated;
GRANT ALL ON FUNCTION public._get_dtype(name, text, boolean) TO service_role;


--
-- Name: FUNCTION _get_fdw_privs(name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._get_fdw_privs(name, text) TO anon;
GRANT ALL ON FUNCTION public._get_fdw_privs(name, text) TO authenticated;
GRANT ALL ON FUNCTION public._get_fdw_privs(name, text) TO service_role;


--
-- Name: FUNCTION _get_func_owner(name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._get_func_owner(name, name[]) TO anon;
GRANT ALL ON FUNCTION public._get_func_owner(name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public._get_func_owner(name, name[]) TO service_role;


--
-- Name: FUNCTION _get_func_owner(name, name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._get_func_owner(name, name, name[]) TO anon;
GRANT ALL ON FUNCTION public._get_func_owner(name, name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public._get_func_owner(name, name, name[]) TO service_role;


--
-- Name: FUNCTION _get_func_privs(text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._get_func_privs(text, text) TO anon;
GRANT ALL ON FUNCTION public._get_func_privs(text, text) TO authenticated;
GRANT ALL ON FUNCTION public._get_func_privs(text, text) TO service_role;


--
-- Name: FUNCTION _get_index_owner(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._get_index_owner(name, name) TO anon;
GRANT ALL ON FUNCTION public._get_index_owner(name, name) TO authenticated;
GRANT ALL ON FUNCTION public._get_index_owner(name, name) TO service_role;


--
-- Name: FUNCTION _get_index_owner(name, name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._get_index_owner(name, name, name) TO anon;
GRANT ALL ON FUNCTION public._get_index_owner(name, name, name) TO authenticated;
GRANT ALL ON FUNCTION public._get_index_owner(name, name, name) TO service_role;


--
-- Name: FUNCTION _get_lang_privs(name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._get_lang_privs(name, text) TO anon;
GRANT ALL ON FUNCTION public._get_lang_privs(name, text) TO authenticated;
GRANT ALL ON FUNCTION public._get_lang_privs(name, text) TO service_role;


--
-- Name: FUNCTION _get_language_owner(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._get_language_owner(name) TO anon;
GRANT ALL ON FUNCTION public._get_language_owner(name) TO authenticated;
GRANT ALL ON FUNCTION public._get_language_owner(name) TO service_role;


--
-- Name: FUNCTION _get_latest(text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._get_latest(text) TO anon;
GRANT ALL ON FUNCTION public._get_latest(text) TO authenticated;
GRANT ALL ON FUNCTION public._get_latest(text) TO service_role;


--
-- Name: FUNCTION _get_latest(text, integer); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._get_latest(text, integer) TO anon;
GRANT ALL ON FUNCTION public._get_latest(text, integer) TO authenticated;
GRANT ALL ON FUNCTION public._get_latest(text, integer) TO service_role;


--
-- Name: FUNCTION _get_note(integer); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._get_note(integer) TO anon;
GRANT ALL ON FUNCTION public._get_note(integer) TO authenticated;
GRANT ALL ON FUNCTION public._get_note(integer) TO service_role;


--
-- Name: FUNCTION _get_note(text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._get_note(text) TO anon;
GRANT ALL ON FUNCTION public._get_note(text) TO authenticated;
GRANT ALL ON FUNCTION public._get_note(text) TO service_role;


--
-- Name: FUNCTION _get_opclass_owner(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._get_opclass_owner(name) TO anon;
GRANT ALL ON FUNCTION public._get_opclass_owner(name) TO authenticated;
GRANT ALL ON FUNCTION public._get_opclass_owner(name) TO service_role;


--
-- Name: FUNCTION _get_opclass_owner(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._get_opclass_owner(name, name) TO anon;
GRANT ALL ON FUNCTION public._get_opclass_owner(name, name) TO authenticated;
GRANT ALL ON FUNCTION public._get_opclass_owner(name, name) TO service_role;


--
-- Name: FUNCTION _get_rel_owner(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._get_rel_owner(name) TO anon;
GRANT ALL ON FUNCTION public._get_rel_owner(name) TO authenticated;
GRANT ALL ON FUNCTION public._get_rel_owner(name) TO service_role;


--
-- Name: FUNCTION _get_rel_owner(character[], name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._get_rel_owner(character[], name) TO anon;
GRANT ALL ON FUNCTION public._get_rel_owner(character[], name) TO authenticated;
GRANT ALL ON FUNCTION public._get_rel_owner(character[], name) TO service_role;


--
-- Name: FUNCTION _get_rel_owner(character, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._get_rel_owner(character, name) TO anon;
GRANT ALL ON FUNCTION public._get_rel_owner(character, name) TO authenticated;
GRANT ALL ON FUNCTION public._get_rel_owner(character, name) TO service_role;


--
-- Name: FUNCTION _get_rel_owner(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._get_rel_owner(name, name) TO anon;
GRANT ALL ON FUNCTION public._get_rel_owner(name, name) TO authenticated;
GRANT ALL ON FUNCTION public._get_rel_owner(name, name) TO service_role;


--
-- Name: FUNCTION _get_rel_owner(character[], name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._get_rel_owner(character[], name, name) TO anon;
GRANT ALL ON FUNCTION public._get_rel_owner(character[], name, name) TO authenticated;
GRANT ALL ON FUNCTION public._get_rel_owner(character[], name, name) TO service_role;


--
-- Name: FUNCTION _get_rel_owner(character, name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._get_rel_owner(character, name, name) TO anon;
GRANT ALL ON FUNCTION public._get_rel_owner(character, name, name) TO authenticated;
GRANT ALL ON FUNCTION public._get_rel_owner(character, name, name) TO service_role;


--
-- Name: FUNCTION _get_schema_owner(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._get_schema_owner(name) TO anon;
GRANT ALL ON FUNCTION public._get_schema_owner(name) TO authenticated;
GRANT ALL ON FUNCTION public._get_schema_owner(name) TO service_role;


--
-- Name: FUNCTION _get_schema_privs(name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._get_schema_privs(name, text) TO anon;
GRANT ALL ON FUNCTION public._get_schema_privs(name, text) TO authenticated;
GRANT ALL ON FUNCTION public._get_schema_privs(name, text) TO service_role;


--
-- Name: FUNCTION _get_sequence_privs(name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._get_sequence_privs(name, text) TO anon;
GRANT ALL ON FUNCTION public._get_sequence_privs(name, text) TO authenticated;
GRANT ALL ON FUNCTION public._get_sequence_privs(name, text) TO service_role;


--
-- Name: FUNCTION _get_server_privs(name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._get_server_privs(name, text) TO anon;
GRANT ALL ON FUNCTION public._get_server_privs(name, text) TO authenticated;
GRANT ALL ON FUNCTION public._get_server_privs(name, text) TO service_role;


--
-- Name: FUNCTION _get_table_privs(name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._get_table_privs(name, text) TO anon;
GRANT ALL ON FUNCTION public._get_table_privs(name, text) TO authenticated;
GRANT ALL ON FUNCTION public._get_table_privs(name, text) TO service_role;


--
-- Name: FUNCTION _get_tablespace_owner(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._get_tablespace_owner(name) TO anon;
GRANT ALL ON FUNCTION public._get_tablespace_owner(name) TO authenticated;
GRANT ALL ON FUNCTION public._get_tablespace_owner(name) TO service_role;


--
-- Name: FUNCTION _get_tablespaceprivs(name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._get_tablespaceprivs(name, text) TO anon;
GRANT ALL ON FUNCTION public._get_tablespaceprivs(name, text) TO authenticated;
GRANT ALL ON FUNCTION public._get_tablespaceprivs(name, text) TO service_role;


--
-- Name: FUNCTION _get_type_owner(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._get_type_owner(name) TO anon;
GRANT ALL ON FUNCTION public._get_type_owner(name) TO authenticated;
GRANT ALL ON FUNCTION public._get_type_owner(name) TO service_role;


--
-- Name: FUNCTION _get_type_owner(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._get_type_owner(name, name) TO anon;
GRANT ALL ON FUNCTION public._get_type_owner(name, name) TO authenticated;
GRANT ALL ON FUNCTION public._get_type_owner(name, name) TO service_role;


--
-- Name: FUNCTION _got_func(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._got_func(name) TO anon;
GRANT ALL ON FUNCTION public._got_func(name) TO authenticated;
GRANT ALL ON FUNCTION public._got_func(name) TO service_role;


--
-- Name: FUNCTION _got_func(name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._got_func(name, name[]) TO anon;
GRANT ALL ON FUNCTION public._got_func(name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public._got_func(name, name[]) TO service_role;


--
-- Name: FUNCTION _got_func(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._got_func(name, name) TO anon;
GRANT ALL ON FUNCTION public._got_func(name, name) TO authenticated;
GRANT ALL ON FUNCTION public._got_func(name, name) TO service_role;


--
-- Name: FUNCTION _got_func(name, name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._got_func(name, name, name[]) TO anon;
GRANT ALL ON FUNCTION public._got_func(name, name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public._got_func(name, name, name[]) TO service_role;


--
-- Name: FUNCTION _grolist(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._grolist(name) TO anon;
GRANT ALL ON FUNCTION public._grolist(name) TO authenticated;
GRANT ALL ON FUNCTION public._grolist(name) TO service_role;


--
-- Name: FUNCTION _has_def(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._has_def(name, name) TO anon;
GRANT ALL ON FUNCTION public._has_def(name, name) TO authenticated;
GRANT ALL ON FUNCTION public._has_def(name, name) TO service_role;


--
-- Name: FUNCTION _has_def(name, name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._has_def(name, name, name) TO anon;
GRANT ALL ON FUNCTION public._has_def(name, name, name) TO authenticated;
GRANT ALL ON FUNCTION public._has_def(name, name, name) TO service_role;


--
-- Name: FUNCTION _has_group(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._has_group(name) TO anon;
GRANT ALL ON FUNCTION public._has_group(name) TO authenticated;
GRANT ALL ON FUNCTION public._has_group(name) TO service_role;


--
-- Name: FUNCTION _has_role(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._has_role(name) TO anon;
GRANT ALL ON FUNCTION public._has_role(name) TO authenticated;
GRANT ALL ON FUNCTION public._has_role(name) TO service_role;


--
-- Name: FUNCTION _has_type(name, character[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._has_type(name, character[]) TO anon;
GRANT ALL ON FUNCTION public._has_type(name, character[]) TO authenticated;
GRANT ALL ON FUNCTION public._has_type(name, character[]) TO service_role;


--
-- Name: FUNCTION _has_type(name, name, character[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._has_type(name, name, character[]) TO anon;
GRANT ALL ON FUNCTION public._has_type(name, name, character[]) TO authenticated;
GRANT ALL ON FUNCTION public._has_type(name, name, character[]) TO service_role;


--
-- Name: FUNCTION _has_user(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._has_user(name) TO anon;
GRANT ALL ON FUNCTION public._has_user(name) TO authenticated;
GRANT ALL ON FUNCTION public._has_user(name) TO service_role;


--
-- Name: FUNCTION _hasc(name, character); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._hasc(name, character) TO anon;
GRANT ALL ON FUNCTION public._hasc(name, character) TO authenticated;
GRANT ALL ON FUNCTION public._hasc(name, character) TO service_role;


--
-- Name: FUNCTION _hasc(name, name, character); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._hasc(name, name, character) TO anon;
GRANT ALL ON FUNCTION public._hasc(name, name, character) TO authenticated;
GRANT ALL ON FUNCTION public._hasc(name, name, character) TO service_role;


--
-- Name: FUNCTION _have_index(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._have_index(name, name) TO anon;
GRANT ALL ON FUNCTION public._have_index(name, name) TO authenticated;
GRANT ALL ON FUNCTION public._have_index(name, name) TO service_role;


--
-- Name: FUNCTION _have_index(name, name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._have_index(name, name, name) TO anon;
GRANT ALL ON FUNCTION public._have_index(name, name, name) TO authenticated;
GRANT ALL ON FUNCTION public._have_index(name, name, name) TO service_role;


--
-- Name: FUNCTION _ident_array_to_sorted_string(name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._ident_array_to_sorted_string(name[], text) TO anon;
GRANT ALL ON FUNCTION public._ident_array_to_sorted_string(name[], text) TO authenticated;
GRANT ALL ON FUNCTION public._ident_array_to_sorted_string(name[], text) TO service_role;


--
-- Name: FUNCTION _ident_array_to_string(name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._ident_array_to_string(name[], text) TO anon;
GRANT ALL ON FUNCTION public._ident_array_to_string(name[], text) TO authenticated;
GRANT ALL ON FUNCTION public._ident_array_to_string(name[], text) TO service_role;


--
-- Name: FUNCTION _ikeys(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._ikeys(name, name) TO anon;
GRANT ALL ON FUNCTION public._ikeys(name, name) TO authenticated;
GRANT ALL ON FUNCTION public._ikeys(name, name) TO service_role;


--
-- Name: FUNCTION _ikeys(name, name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._ikeys(name, name, name) TO anon;
GRANT ALL ON FUNCTION public._ikeys(name, name, name) TO authenticated;
GRANT ALL ON FUNCTION public._ikeys(name, name, name) TO service_role;


--
-- Name: FUNCTION _inherited(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._inherited(name) TO anon;
GRANT ALL ON FUNCTION public._inherited(name) TO authenticated;
GRANT ALL ON FUNCTION public._inherited(name) TO service_role;


--
-- Name: FUNCTION _inherited(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._inherited(name, name) TO anon;
GRANT ALL ON FUNCTION public._inherited(name, name) TO authenticated;
GRANT ALL ON FUNCTION public._inherited(name, name) TO service_role;


--
-- Name: FUNCTION _is_indexed(name, name, text[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._is_indexed(name, name, text[]) TO anon;
GRANT ALL ON FUNCTION public._is_indexed(name, name, text[]) TO authenticated;
GRANT ALL ON FUNCTION public._is_indexed(name, name, text[]) TO service_role;


--
-- Name: FUNCTION _is_instead(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._is_instead(name, name) TO anon;
GRANT ALL ON FUNCTION public._is_instead(name, name) TO authenticated;
GRANT ALL ON FUNCTION public._is_instead(name, name) TO service_role;


--
-- Name: FUNCTION _is_instead(name, name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._is_instead(name, name, name) TO anon;
GRANT ALL ON FUNCTION public._is_instead(name, name, name) TO authenticated;
GRANT ALL ON FUNCTION public._is_instead(name, name, name) TO service_role;


--
-- Name: FUNCTION _is_schema(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._is_schema(name) TO anon;
GRANT ALL ON FUNCTION public._is_schema(name) TO authenticated;
GRANT ALL ON FUNCTION public._is_schema(name) TO service_role;


--
-- Name: FUNCTION _is_super(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._is_super(name) TO anon;
GRANT ALL ON FUNCTION public._is_super(name) TO authenticated;
GRANT ALL ON FUNCTION public._is_super(name) TO service_role;


--
-- Name: FUNCTION _is_trusted(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._is_trusted(name) TO anon;
GRANT ALL ON FUNCTION public._is_trusted(name) TO authenticated;
GRANT ALL ON FUNCTION public._is_trusted(name) TO service_role;


--
-- Name: FUNCTION _is_verbose(); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._is_verbose() TO anon;
GRANT ALL ON FUNCTION public._is_verbose() TO authenticated;
GRANT ALL ON FUNCTION public._is_verbose() TO service_role;


--
-- Name: FUNCTION _keys(name, character); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._keys(name, character) TO anon;
GRANT ALL ON FUNCTION public._keys(name, character) TO authenticated;
GRANT ALL ON FUNCTION public._keys(name, character) TO service_role;


--
-- Name: FUNCTION _keys(name, name, character); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._keys(name, name, character) TO anon;
GRANT ALL ON FUNCTION public._keys(name, name, character) TO authenticated;
GRANT ALL ON FUNCTION public._keys(name, name, character) TO service_role;


--
-- Name: FUNCTION _lang(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._lang(name) TO anon;
GRANT ALL ON FUNCTION public._lang(name) TO authenticated;
GRANT ALL ON FUNCTION public._lang(name) TO service_role;


--
-- Name: FUNCTION _lang(name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._lang(name, name[]) TO anon;
GRANT ALL ON FUNCTION public._lang(name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public._lang(name, name[]) TO service_role;


--
-- Name: FUNCTION _lang(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._lang(name, name) TO anon;
GRANT ALL ON FUNCTION public._lang(name, name) TO authenticated;
GRANT ALL ON FUNCTION public._lang(name, name) TO service_role;


--
-- Name: FUNCTION _lang(name, name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._lang(name, name, name[]) TO anon;
GRANT ALL ON FUNCTION public._lang(name, name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public._lang(name, name, name[]) TO service_role;


--
-- Name: FUNCTION _missing(character[], name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._missing(character[], name[]) TO anon;
GRANT ALL ON FUNCTION public._missing(character[], name[]) TO authenticated;
GRANT ALL ON FUNCTION public._missing(character[], name[]) TO service_role;


--
-- Name: FUNCTION _missing(character, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._missing(character, name[]) TO anon;
GRANT ALL ON FUNCTION public._missing(character, name[]) TO authenticated;
GRANT ALL ON FUNCTION public._missing(character, name[]) TO service_role;


--
-- Name: FUNCTION _missing(character[], name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._missing(character[], name, name[]) TO anon;
GRANT ALL ON FUNCTION public._missing(character[], name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public._missing(character[], name, name[]) TO service_role;


--
-- Name: FUNCTION _missing(character, name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._missing(character, name, name[]) TO anon;
GRANT ALL ON FUNCTION public._missing(character, name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public._missing(character, name, name[]) TO service_role;


--
-- Name: FUNCTION _nosuch(name, name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._nosuch(name, name, name[]) TO anon;
GRANT ALL ON FUNCTION public._nosuch(name, name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public._nosuch(name, name, name[]) TO service_role;


--
-- Name: FUNCTION _op_exists(name, name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._op_exists(name, name, name) TO anon;
GRANT ALL ON FUNCTION public._op_exists(name, name, name) TO authenticated;
GRANT ALL ON FUNCTION public._op_exists(name, name, name) TO service_role;


--
-- Name: FUNCTION _op_exists(name, name, name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._op_exists(name, name, name, name) TO anon;
GRANT ALL ON FUNCTION public._op_exists(name, name, name, name) TO authenticated;
GRANT ALL ON FUNCTION public._op_exists(name, name, name, name) TO service_role;


--
-- Name: FUNCTION _op_exists(name, name, name, name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._op_exists(name, name, name, name, name) TO anon;
GRANT ALL ON FUNCTION public._op_exists(name, name, name, name, name) TO authenticated;
GRANT ALL ON FUNCTION public._op_exists(name, name, name, name, name) TO service_role;


--
-- Name: FUNCTION _opc_exists(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._opc_exists(name) TO anon;
GRANT ALL ON FUNCTION public._opc_exists(name) TO authenticated;
GRANT ALL ON FUNCTION public._opc_exists(name) TO service_role;


--
-- Name: FUNCTION _opc_exists(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._opc_exists(name, name) TO anon;
GRANT ALL ON FUNCTION public._opc_exists(name, name) TO authenticated;
GRANT ALL ON FUNCTION public._opc_exists(name, name) TO service_role;


--
-- Name: FUNCTION _partof(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._partof(name, name) TO anon;
GRANT ALL ON FUNCTION public._partof(name, name) TO authenticated;
GRANT ALL ON FUNCTION public._partof(name, name) TO service_role;


--
-- Name: FUNCTION _partof(name, name, name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._partof(name, name, name, name) TO anon;
GRANT ALL ON FUNCTION public._partof(name, name, name, name) TO authenticated;
GRANT ALL ON FUNCTION public._partof(name, name, name, name) TO service_role;


--
-- Name: FUNCTION _parts(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._parts(name) TO anon;
GRANT ALL ON FUNCTION public._parts(name) TO authenticated;
GRANT ALL ON FUNCTION public._parts(name) TO service_role;


--
-- Name: FUNCTION _parts(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._parts(name, name) TO anon;
GRANT ALL ON FUNCTION public._parts(name, name) TO authenticated;
GRANT ALL ON FUNCTION public._parts(name, name) TO service_role;


--
-- Name: FUNCTION _pg_sv_column_array(oid, smallint[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._pg_sv_column_array(oid, smallint[]) TO anon;
GRANT ALL ON FUNCTION public._pg_sv_column_array(oid, smallint[]) TO authenticated;
GRANT ALL ON FUNCTION public._pg_sv_column_array(oid, smallint[]) TO service_role;


--
-- Name: FUNCTION _pg_sv_table_accessible(oid, oid); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._pg_sv_table_accessible(oid, oid) TO anon;
GRANT ALL ON FUNCTION public._pg_sv_table_accessible(oid, oid) TO authenticated;
GRANT ALL ON FUNCTION public._pg_sv_table_accessible(oid, oid) TO service_role;


--
-- Name: FUNCTION _pg_sv_type_array(oid[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._pg_sv_type_array(oid[]) TO anon;
GRANT ALL ON FUNCTION public._pg_sv_type_array(oid[]) TO authenticated;
GRANT ALL ON FUNCTION public._pg_sv_type_array(oid[]) TO service_role;


--
-- Name: FUNCTION _prokind(p_oid oid); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._prokind(p_oid oid) TO anon;
GRANT ALL ON FUNCTION public._prokind(p_oid oid) TO authenticated;
GRANT ALL ON FUNCTION public._prokind(p_oid oid) TO service_role;


--
-- Name: FUNCTION _query(text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._query(text) TO anon;
GRANT ALL ON FUNCTION public._query(text) TO authenticated;
GRANT ALL ON FUNCTION public._query(text) TO service_role;


--
-- Name: FUNCTION _refine_vol(text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._refine_vol(text) TO anon;
GRANT ALL ON FUNCTION public._refine_vol(text) TO authenticated;
GRANT ALL ON FUNCTION public._refine_vol(text) TO service_role;


--
-- Name: FUNCTION _relcomp(text, anyarray, text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._relcomp(text, anyarray, text, text) TO anon;
GRANT ALL ON FUNCTION public._relcomp(text, anyarray, text, text) TO authenticated;
GRANT ALL ON FUNCTION public._relcomp(text, anyarray, text, text) TO service_role;


--
-- Name: FUNCTION _relcomp(text, text, text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._relcomp(text, text, text, text) TO anon;
GRANT ALL ON FUNCTION public._relcomp(text, text, text, text) TO authenticated;
GRANT ALL ON FUNCTION public._relcomp(text, text, text, text) TO service_role;


--
-- Name: FUNCTION _relcomp(text, text, text, text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._relcomp(text, text, text, text, text) TO anon;
GRANT ALL ON FUNCTION public._relcomp(text, text, text, text, text) TO authenticated;
GRANT ALL ON FUNCTION public._relcomp(text, text, text, text, text) TO service_role;


--
-- Name: FUNCTION _relexists(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._relexists(name) TO anon;
GRANT ALL ON FUNCTION public._relexists(name) TO authenticated;
GRANT ALL ON FUNCTION public._relexists(name) TO service_role;


--
-- Name: FUNCTION _relexists(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._relexists(name, name) TO anon;
GRANT ALL ON FUNCTION public._relexists(name, name) TO authenticated;
GRANT ALL ON FUNCTION public._relexists(name, name) TO service_role;


--
-- Name: FUNCTION _relne(text, anyarray, text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._relne(text, anyarray, text, text) TO anon;
GRANT ALL ON FUNCTION public._relne(text, anyarray, text, text) TO authenticated;
GRANT ALL ON FUNCTION public._relne(text, anyarray, text, text) TO service_role;


--
-- Name: FUNCTION _relne(text, text, text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._relne(text, text, text, text) TO anon;
GRANT ALL ON FUNCTION public._relne(text, text, text, text) TO authenticated;
GRANT ALL ON FUNCTION public._relne(text, text, text, text) TO service_role;


--
-- Name: FUNCTION _returns(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._returns(name) TO anon;
GRANT ALL ON FUNCTION public._returns(name) TO authenticated;
GRANT ALL ON FUNCTION public._returns(name) TO service_role;


--
-- Name: FUNCTION _returns(name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._returns(name, name[]) TO anon;
GRANT ALL ON FUNCTION public._returns(name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public._returns(name, name[]) TO service_role;


--
-- Name: FUNCTION _returns(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._returns(name, name) TO anon;
GRANT ALL ON FUNCTION public._returns(name, name) TO authenticated;
GRANT ALL ON FUNCTION public._returns(name, name) TO service_role;


--
-- Name: FUNCTION _returns(name, name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._returns(name, name, name[]) TO anon;
GRANT ALL ON FUNCTION public._returns(name, name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public._returns(name, name, name[]) TO service_role;


--
-- Name: FUNCTION _retval(text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._retval(text) TO anon;
GRANT ALL ON FUNCTION public._retval(text) TO authenticated;
GRANT ALL ON FUNCTION public._retval(text) TO service_role;


--
-- Name: FUNCTION _rexists(character[], name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._rexists(character[], name) TO anon;
GRANT ALL ON FUNCTION public._rexists(character[], name) TO authenticated;
GRANT ALL ON FUNCTION public._rexists(character[], name) TO service_role;


--
-- Name: FUNCTION _rexists(character, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._rexists(character, name) TO anon;
GRANT ALL ON FUNCTION public._rexists(character, name) TO authenticated;
GRANT ALL ON FUNCTION public._rexists(character, name) TO service_role;


--
-- Name: FUNCTION _rexists(character[], name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._rexists(character[], name, name) TO anon;
GRANT ALL ON FUNCTION public._rexists(character[], name, name) TO authenticated;
GRANT ALL ON FUNCTION public._rexists(character[], name, name) TO service_role;


--
-- Name: FUNCTION _rexists(character, name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._rexists(character, name, name) TO anon;
GRANT ALL ON FUNCTION public._rexists(character, name, name) TO authenticated;
GRANT ALL ON FUNCTION public._rexists(character, name, name) TO service_role;


--
-- Name: FUNCTION _rule_on(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._rule_on(name, name) TO anon;
GRANT ALL ON FUNCTION public._rule_on(name, name) TO authenticated;
GRANT ALL ON FUNCTION public._rule_on(name, name) TO service_role;


--
-- Name: FUNCTION _rule_on(name, name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._rule_on(name, name, name) TO anon;
GRANT ALL ON FUNCTION public._rule_on(name, name, name) TO authenticated;
GRANT ALL ON FUNCTION public._rule_on(name, name, name) TO service_role;


--
-- Name: FUNCTION _runem(text[], boolean); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._runem(text[], boolean) TO anon;
GRANT ALL ON FUNCTION public._runem(text[], boolean) TO authenticated;
GRANT ALL ON FUNCTION public._runem(text[], boolean) TO service_role;


--
-- Name: FUNCTION _runner(text[], text[], text[], text[], text[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._runner(text[], text[], text[], text[], text[]) TO anon;
GRANT ALL ON FUNCTION public._runner(text[], text[], text[], text[], text[]) TO authenticated;
GRANT ALL ON FUNCTION public._runner(text[], text[], text[], text[], text[]) TO service_role;


--
-- Name: FUNCTION _set(integer, integer); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._set(integer, integer) TO anon;
GRANT ALL ON FUNCTION public._set(integer, integer) TO authenticated;
GRANT ALL ON FUNCTION public._set(integer, integer) TO service_role;


--
-- Name: FUNCTION _set(text, integer); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._set(text, integer) TO anon;
GRANT ALL ON FUNCTION public._set(text, integer) TO authenticated;
GRANT ALL ON FUNCTION public._set(text, integer) TO service_role;


--
-- Name: FUNCTION _set(text, integer, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._set(text, integer, text) TO anon;
GRANT ALL ON FUNCTION public._set(text, integer, text) TO authenticated;
GRANT ALL ON FUNCTION public._set(text, integer, text) TO service_role;


--
-- Name: FUNCTION _strict(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._strict(name) TO anon;
GRANT ALL ON FUNCTION public._strict(name) TO authenticated;
GRANT ALL ON FUNCTION public._strict(name) TO service_role;


--
-- Name: FUNCTION _strict(name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._strict(name, name[]) TO anon;
GRANT ALL ON FUNCTION public._strict(name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public._strict(name, name[]) TO service_role;


--
-- Name: FUNCTION _strict(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._strict(name, name) TO anon;
GRANT ALL ON FUNCTION public._strict(name, name) TO authenticated;
GRANT ALL ON FUNCTION public._strict(name, name) TO service_role;


--
-- Name: FUNCTION _strict(name, name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._strict(name, name, name[]) TO anon;
GRANT ALL ON FUNCTION public._strict(name, name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public._strict(name, name, name[]) TO service_role;


--
-- Name: FUNCTION _table_privs(); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._table_privs() TO anon;
GRANT ALL ON FUNCTION public._table_privs() TO authenticated;
GRANT ALL ON FUNCTION public._table_privs() TO service_role;


--
-- Name: FUNCTION _temptable(anyarray, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._temptable(anyarray, text) TO anon;
GRANT ALL ON FUNCTION public._temptable(anyarray, text) TO authenticated;
GRANT ALL ON FUNCTION public._temptable(anyarray, text) TO service_role;


--
-- Name: FUNCTION _temptable(text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._temptable(text, text) TO anon;
GRANT ALL ON FUNCTION public._temptable(text, text) TO authenticated;
GRANT ALL ON FUNCTION public._temptable(text, text) TO service_role;


--
-- Name: FUNCTION _temptypes(text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._temptypes(text) TO anon;
GRANT ALL ON FUNCTION public._temptypes(text) TO authenticated;
GRANT ALL ON FUNCTION public._temptypes(text) TO service_role;


--
-- Name: FUNCTION _time_trials(text, integer, numeric); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._time_trials(text, integer, numeric) TO anon;
GRANT ALL ON FUNCTION public._time_trials(text, integer, numeric) TO authenticated;
GRANT ALL ON FUNCTION public._time_trials(text, integer, numeric) TO service_role;


--
-- Name: FUNCTION _tlike(boolean, text, text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._tlike(boolean, text, text, text) TO anon;
GRANT ALL ON FUNCTION public._tlike(boolean, text, text, text) TO authenticated;
GRANT ALL ON FUNCTION public._tlike(boolean, text, text, text) TO service_role;


--
-- Name: FUNCTION _todo(); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._todo() TO anon;
GRANT ALL ON FUNCTION public._todo() TO authenticated;
GRANT ALL ON FUNCTION public._todo() TO service_role;


--
-- Name: FUNCTION _trig(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._trig(name, name) TO anon;
GRANT ALL ON FUNCTION public._trig(name, name) TO authenticated;
GRANT ALL ON FUNCTION public._trig(name, name) TO service_role;


--
-- Name: FUNCTION _trig(name, name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._trig(name, name, name) TO anon;
GRANT ALL ON FUNCTION public._trig(name, name, name) TO authenticated;
GRANT ALL ON FUNCTION public._trig(name, name, name) TO service_role;


--
-- Name: FUNCTION _type_func("char", name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._type_func("char", name) TO anon;
GRANT ALL ON FUNCTION public._type_func("char", name) TO authenticated;
GRANT ALL ON FUNCTION public._type_func("char", name) TO service_role;


--
-- Name: FUNCTION _type_func("char", name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._type_func("char", name, name[]) TO anon;
GRANT ALL ON FUNCTION public._type_func("char", name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public._type_func("char", name, name[]) TO service_role;


--
-- Name: FUNCTION _type_func("char", name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._type_func("char", name, name) TO anon;
GRANT ALL ON FUNCTION public._type_func("char", name, name) TO authenticated;
GRANT ALL ON FUNCTION public._type_func("char", name, name) TO service_role;


--
-- Name: FUNCTION _type_func("char", name, name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._type_func("char", name, name, name[]) TO anon;
GRANT ALL ON FUNCTION public._type_func("char", name, name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public._type_func("char", name, name, name[]) TO service_role;


--
-- Name: FUNCTION _typename(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._typename(name) TO anon;
GRANT ALL ON FUNCTION public._typename(name) TO authenticated;
GRANT ALL ON FUNCTION public._typename(name) TO service_role;


--
-- Name: FUNCTION _types_are(name[], text, character[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._types_are(name[], text, character[]) TO anon;
GRANT ALL ON FUNCTION public._types_are(name[], text, character[]) TO authenticated;
GRANT ALL ON FUNCTION public._types_are(name[], text, character[]) TO service_role;


--
-- Name: FUNCTION _types_are(name, name[], text, character[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._types_are(name, name[], text, character[]) TO anon;
GRANT ALL ON FUNCTION public._types_are(name, name[], text, character[]) TO authenticated;
GRANT ALL ON FUNCTION public._types_are(name, name[], text, character[]) TO service_role;


--
-- Name: FUNCTION _unalike(boolean, anyelement, text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._unalike(boolean, anyelement, text, text) TO anon;
GRANT ALL ON FUNCTION public._unalike(boolean, anyelement, text, text) TO authenticated;
GRANT ALL ON FUNCTION public._unalike(boolean, anyelement, text, text) TO service_role;


--
-- Name: FUNCTION _vol(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._vol(name) TO anon;
GRANT ALL ON FUNCTION public._vol(name) TO authenticated;
GRANT ALL ON FUNCTION public._vol(name) TO service_role;


--
-- Name: FUNCTION _vol(name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._vol(name, name[]) TO anon;
GRANT ALL ON FUNCTION public._vol(name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public._vol(name, name[]) TO service_role;


--
-- Name: FUNCTION _vol(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._vol(name, name) TO anon;
GRANT ALL ON FUNCTION public._vol(name, name) TO authenticated;
GRANT ALL ON FUNCTION public._vol(name, name) TO service_role;


--
-- Name: FUNCTION _vol(name, name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public._vol(name, name, name[]) TO anon;
GRANT ALL ON FUNCTION public._vol(name, name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public._vol(name, name, name[]) TO service_role;


--
-- Name: FUNCTION add_result(boolean, boolean, text, text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.add_result(boolean, boolean, text, text, text) TO anon;
GRANT ALL ON FUNCTION public.add_result(boolean, boolean, text, text, text) TO authenticated;
GRANT ALL ON FUNCTION public.add_result(boolean, boolean, text, text, text) TO service_role;


--
-- Name: FUNCTION alike(anyelement, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.alike(anyelement, text) TO anon;
GRANT ALL ON FUNCTION public.alike(anyelement, text) TO authenticated;
GRANT ALL ON FUNCTION public.alike(anyelement, text) TO service_role;


--
-- Name: FUNCTION alike(anyelement, text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.alike(anyelement, text, text) TO anon;
GRANT ALL ON FUNCTION public.alike(anyelement, text, text) TO authenticated;
GRANT ALL ON FUNCTION public.alike(anyelement, text, text) TO service_role;


--
-- Name: FUNCTION any_column_privs_are(name, name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.any_column_privs_are(name, name, name[]) TO anon;
GRANT ALL ON FUNCTION public.any_column_privs_are(name, name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public.any_column_privs_are(name, name, name[]) TO service_role;


--
-- Name: FUNCTION any_column_privs_are(name, name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.any_column_privs_are(name, name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.any_column_privs_are(name, name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.any_column_privs_are(name, name, name[], text) TO service_role;


--
-- Name: FUNCTION any_column_privs_are(name, name, name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.any_column_privs_are(name, name, name, name[]) TO anon;
GRANT ALL ON FUNCTION public.any_column_privs_are(name, name, name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public.any_column_privs_are(name, name, name, name[]) TO service_role;


--
-- Name: FUNCTION any_column_privs_are(name, name, name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.any_column_privs_are(name, name, name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.any_column_privs_are(name, name, name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.any_column_privs_are(name, name, name, name[], text) TO service_role;


--
-- Name: FUNCTION armor(bytea); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.armor(bytea) TO anon;
GRANT ALL ON FUNCTION public.armor(bytea) TO authenticated;
GRANT ALL ON FUNCTION public.armor(bytea) TO service_role;


--
-- Name: FUNCTION armor(bytea, text[], text[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.armor(bytea, text[], text[]) TO anon;
GRANT ALL ON FUNCTION public.armor(bytea, text[], text[]) TO authenticated;
GRANT ALL ON FUNCTION public.armor(bytea, text[], text[]) TO service_role;


--
-- Name: FUNCTION bag_eq(text, anyarray); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.bag_eq(text, anyarray) TO anon;
GRANT ALL ON FUNCTION public.bag_eq(text, anyarray) TO authenticated;
GRANT ALL ON FUNCTION public.bag_eq(text, anyarray) TO service_role;


--
-- Name: FUNCTION bag_eq(text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.bag_eq(text, text) TO anon;
GRANT ALL ON FUNCTION public.bag_eq(text, text) TO authenticated;
GRANT ALL ON FUNCTION public.bag_eq(text, text) TO service_role;


--
-- Name: FUNCTION bag_eq(text, anyarray, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.bag_eq(text, anyarray, text) TO anon;
GRANT ALL ON FUNCTION public.bag_eq(text, anyarray, text) TO authenticated;
GRANT ALL ON FUNCTION public.bag_eq(text, anyarray, text) TO service_role;


--
-- Name: FUNCTION bag_eq(text, text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.bag_eq(text, text, text) TO anon;
GRANT ALL ON FUNCTION public.bag_eq(text, text, text) TO authenticated;
GRANT ALL ON FUNCTION public.bag_eq(text, text, text) TO service_role;


--
-- Name: FUNCTION bag_has(text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.bag_has(text, text) TO anon;
GRANT ALL ON FUNCTION public.bag_has(text, text) TO authenticated;
GRANT ALL ON FUNCTION public.bag_has(text, text) TO service_role;


--
-- Name: FUNCTION bag_has(text, text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.bag_has(text, text, text) TO anon;
GRANT ALL ON FUNCTION public.bag_has(text, text, text) TO authenticated;
GRANT ALL ON FUNCTION public.bag_has(text, text, text) TO service_role;


--
-- Name: FUNCTION bag_hasnt(text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.bag_hasnt(text, text) TO anon;
GRANT ALL ON FUNCTION public.bag_hasnt(text, text) TO authenticated;
GRANT ALL ON FUNCTION public.bag_hasnt(text, text) TO service_role;


--
-- Name: FUNCTION bag_hasnt(text, text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.bag_hasnt(text, text, text) TO anon;
GRANT ALL ON FUNCTION public.bag_hasnt(text, text, text) TO authenticated;
GRANT ALL ON FUNCTION public.bag_hasnt(text, text, text) TO service_role;


--
-- Name: FUNCTION bag_ne(text, anyarray); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.bag_ne(text, anyarray) TO anon;
GRANT ALL ON FUNCTION public.bag_ne(text, anyarray) TO authenticated;
GRANT ALL ON FUNCTION public.bag_ne(text, anyarray) TO service_role;


--
-- Name: FUNCTION bag_ne(text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.bag_ne(text, text) TO anon;
GRANT ALL ON FUNCTION public.bag_ne(text, text) TO authenticated;
GRANT ALL ON FUNCTION public.bag_ne(text, text) TO service_role;


--
-- Name: FUNCTION bag_ne(text, anyarray, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.bag_ne(text, anyarray, text) TO anon;
GRANT ALL ON FUNCTION public.bag_ne(text, anyarray, text) TO authenticated;
GRANT ALL ON FUNCTION public.bag_ne(text, anyarray, text) TO service_role;


--
-- Name: FUNCTION bag_ne(text, text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.bag_ne(text, text, text) TO anon;
GRANT ALL ON FUNCTION public.bag_ne(text, text, text) TO authenticated;
GRANT ALL ON FUNCTION public.bag_ne(text, text, text) TO service_role;


--
-- Name: FUNCTION can(name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.can(name[]) TO anon;
GRANT ALL ON FUNCTION public.can(name[]) TO authenticated;
GRANT ALL ON FUNCTION public.can(name[]) TO service_role;


--
-- Name: FUNCTION can(name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.can(name[], text) TO anon;
GRANT ALL ON FUNCTION public.can(name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.can(name[], text) TO service_role;


--
-- Name: FUNCTION can(name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.can(name, name[]) TO anon;
GRANT ALL ON FUNCTION public.can(name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public.can(name, name[]) TO service_role;


--
-- Name: FUNCTION can(name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.can(name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.can(name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.can(name, name[], text) TO service_role;


--
-- Name: FUNCTION cast_context_is(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.cast_context_is(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.cast_context_is(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.cast_context_is(name, name, text) TO service_role;


--
-- Name: FUNCTION cast_context_is(name, name, text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.cast_context_is(name, name, text, text) TO anon;
GRANT ALL ON FUNCTION public.cast_context_is(name, name, text, text) TO authenticated;
GRANT ALL ON FUNCTION public.cast_context_is(name, name, text, text) TO service_role;


--
-- Name: FUNCTION casts_are(text[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.casts_are(text[]) TO anon;
GRANT ALL ON FUNCTION public.casts_are(text[]) TO authenticated;
GRANT ALL ON FUNCTION public.casts_are(text[]) TO service_role;


--
-- Name: FUNCTION casts_are(text[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.casts_are(text[], text) TO anon;
GRANT ALL ON FUNCTION public.casts_are(text[], text) TO authenticated;
GRANT ALL ON FUNCTION public.casts_are(text[], text) TO service_role;


--
-- Name: FUNCTION check_test(text, boolean); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.check_test(text, boolean) TO anon;
GRANT ALL ON FUNCTION public.check_test(text, boolean) TO authenticated;
GRANT ALL ON FUNCTION public.check_test(text, boolean) TO service_role;


--
-- Name: FUNCTION check_test(text, boolean, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.check_test(text, boolean, text) TO anon;
GRANT ALL ON FUNCTION public.check_test(text, boolean, text) TO authenticated;
GRANT ALL ON FUNCTION public.check_test(text, boolean, text) TO service_role;


--
-- Name: FUNCTION check_test(text, boolean, text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.check_test(text, boolean, text, text) TO anon;
GRANT ALL ON FUNCTION public.check_test(text, boolean, text, text) TO authenticated;
GRANT ALL ON FUNCTION public.check_test(text, boolean, text, text) TO service_role;


--
-- Name: FUNCTION check_test(text, boolean, text, text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.check_test(text, boolean, text, text, text) TO anon;
GRANT ALL ON FUNCTION public.check_test(text, boolean, text, text, text) TO authenticated;
GRANT ALL ON FUNCTION public.check_test(text, boolean, text, text, text) TO service_role;


--
-- Name: FUNCTION check_test(text, boolean, text, text, text, boolean); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.check_test(text, boolean, text, text, text, boolean) TO anon;
GRANT ALL ON FUNCTION public.check_test(text, boolean, text, text, text, boolean) TO authenticated;
GRANT ALL ON FUNCTION public.check_test(text, boolean, text, text, text, boolean) TO service_role;


--
-- Name: FUNCTION cmp_ok(anyelement, text, anyelement); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.cmp_ok(anyelement, text, anyelement) TO anon;
GRANT ALL ON FUNCTION public.cmp_ok(anyelement, text, anyelement) TO authenticated;
GRANT ALL ON FUNCTION public.cmp_ok(anyelement, text, anyelement) TO service_role;


--
-- Name: FUNCTION cmp_ok(anyelement, text, anyelement, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.cmp_ok(anyelement, text, anyelement, text) TO anon;
GRANT ALL ON FUNCTION public.cmp_ok(anyelement, text, anyelement, text) TO authenticated;
GRANT ALL ON FUNCTION public.cmp_ok(anyelement, text, anyelement, text) TO service_role;


--
-- Name: FUNCTION col_default_is(name, name, anyelement); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.col_default_is(name, name, anyelement) TO anon;
GRANT ALL ON FUNCTION public.col_default_is(name, name, anyelement) TO authenticated;
GRANT ALL ON FUNCTION public.col_default_is(name, name, anyelement) TO service_role;


--
-- Name: FUNCTION col_default_is(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.col_default_is(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.col_default_is(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.col_default_is(name, name, text) TO service_role;


--
-- Name: FUNCTION col_default_is(name, name, anyelement, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.col_default_is(name, name, anyelement, text) TO anon;
GRANT ALL ON FUNCTION public.col_default_is(name, name, anyelement, text) TO authenticated;
GRANT ALL ON FUNCTION public.col_default_is(name, name, anyelement, text) TO service_role;


--
-- Name: FUNCTION col_default_is(name, name, text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.col_default_is(name, name, text, text) TO anon;
GRANT ALL ON FUNCTION public.col_default_is(name, name, text, text) TO authenticated;
GRANT ALL ON FUNCTION public.col_default_is(name, name, text, text) TO service_role;


--
-- Name: FUNCTION col_default_is(name, name, name, anyelement, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.col_default_is(name, name, name, anyelement, text) TO anon;
GRANT ALL ON FUNCTION public.col_default_is(name, name, name, anyelement, text) TO authenticated;
GRANT ALL ON FUNCTION public.col_default_is(name, name, name, anyelement, text) TO service_role;


--
-- Name: FUNCTION col_default_is(name, name, name, text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.col_default_is(name, name, name, text, text) TO anon;
GRANT ALL ON FUNCTION public.col_default_is(name, name, name, text, text) TO authenticated;
GRANT ALL ON FUNCTION public.col_default_is(name, name, name, text, text) TO service_role;


--
-- Name: FUNCTION col_has_check(name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.col_has_check(name, name[]) TO anon;
GRANT ALL ON FUNCTION public.col_has_check(name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public.col_has_check(name, name[]) TO service_role;


--
-- Name: FUNCTION col_has_check(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.col_has_check(name, name) TO anon;
GRANT ALL ON FUNCTION public.col_has_check(name, name) TO authenticated;
GRANT ALL ON FUNCTION public.col_has_check(name, name) TO service_role;


--
-- Name: FUNCTION col_has_check(name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.col_has_check(name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.col_has_check(name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.col_has_check(name, name[], text) TO service_role;


--
-- Name: FUNCTION col_has_check(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.col_has_check(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.col_has_check(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.col_has_check(name, name, text) TO service_role;


--
-- Name: FUNCTION col_has_check(name, name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.col_has_check(name, name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.col_has_check(name, name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.col_has_check(name, name, name[], text) TO service_role;


--
-- Name: FUNCTION col_has_check(name, name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.col_has_check(name, name, name, text) TO anon;
GRANT ALL ON FUNCTION public.col_has_check(name, name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.col_has_check(name, name, name, text) TO service_role;


--
-- Name: FUNCTION col_has_default(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.col_has_default(name, name) TO anon;
GRANT ALL ON FUNCTION public.col_has_default(name, name) TO authenticated;
GRANT ALL ON FUNCTION public.col_has_default(name, name) TO service_role;


--
-- Name: FUNCTION col_has_default(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.col_has_default(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.col_has_default(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.col_has_default(name, name, text) TO service_role;


--
-- Name: FUNCTION col_has_default(name, name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.col_has_default(name, name, name, text) TO anon;
GRANT ALL ON FUNCTION public.col_has_default(name, name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.col_has_default(name, name, name, text) TO service_role;


--
-- Name: FUNCTION col_hasnt_default(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.col_hasnt_default(name, name) TO anon;
GRANT ALL ON FUNCTION public.col_hasnt_default(name, name) TO authenticated;
GRANT ALL ON FUNCTION public.col_hasnt_default(name, name) TO service_role;


--
-- Name: FUNCTION col_hasnt_default(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.col_hasnt_default(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.col_hasnt_default(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.col_hasnt_default(name, name, text) TO service_role;


--
-- Name: FUNCTION col_hasnt_default(name, name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.col_hasnt_default(name, name, name, text) TO anon;
GRANT ALL ON FUNCTION public.col_hasnt_default(name, name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.col_hasnt_default(name, name, name, text) TO service_role;


--
-- Name: FUNCTION col_is_fk(name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.col_is_fk(name, name[]) TO anon;
GRANT ALL ON FUNCTION public.col_is_fk(name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public.col_is_fk(name, name[]) TO service_role;


--
-- Name: FUNCTION col_is_fk(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.col_is_fk(name, name) TO anon;
GRANT ALL ON FUNCTION public.col_is_fk(name, name) TO authenticated;
GRANT ALL ON FUNCTION public.col_is_fk(name, name) TO service_role;


--
-- Name: FUNCTION col_is_fk(name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.col_is_fk(name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.col_is_fk(name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.col_is_fk(name, name[], text) TO service_role;


--
-- Name: FUNCTION col_is_fk(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.col_is_fk(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.col_is_fk(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.col_is_fk(name, name, text) TO service_role;


--
-- Name: FUNCTION col_is_fk(name, name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.col_is_fk(name, name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.col_is_fk(name, name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.col_is_fk(name, name, name[], text) TO service_role;


--
-- Name: FUNCTION col_is_fk(name, name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.col_is_fk(name, name, name, text) TO anon;
GRANT ALL ON FUNCTION public.col_is_fk(name, name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.col_is_fk(name, name, name, text) TO service_role;


--
-- Name: FUNCTION col_is_null(table_name name, column_name name, description text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.col_is_null(table_name name, column_name name, description text) TO anon;
GRANT ALL ON FUNCTION public.col_is_null(table_name name, column_name name, description text) TO authenticated;
GRANT ALL ON FUNCTION public.col_is_null(table_name name, column_name name, description text) TO service_role;


--
-- Name: FUNCTION col_is_null(schema_name name, table_name name, column_name name, description text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.col_is_null(schema_name name, table_name name, column_name name, description text) TO anon;
GRANT ALL ON FUNCTION public.col_is_null(schema_name name, table_name name, column_name name, description text) TO authenticated;
GRANT ALL ON FUNCTION public.col_is_null(schema_name name, table_name name, column_name name, description text) TO service_role;


--
-- Name: FUNCTION col_is_pk(name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.col_is_pk(name, name[]) TO anon;
GRANT ALL ON FUNCTION public.col_is_pk(name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public.col_is_pk(name, name[]) TO service_role;


--
-- Name: FUNCTION col_is_pk(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.col_is_pk(name, name) TO anon;
GRANT ALL ON FUNCTION public.col_is_pk(name, name) TO authenticated;
GRANT ALL ON FUNCTION public.col_is_pk(name, name) TO service_role;


--
-- Name: FUNCTION col_is_pk(name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.col_is_pk(name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.col_is_pk(name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.col_is_pk(name, name[], text) TO service_role;


--
-- Name: FUNCTION col_is_pk(name, name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.col_is_pk(name, name, name[]) TO anon;
GRANT ALL ON FUNCTION public.col_is_pk(name, name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public.col_is_pk(name, name, name[]) TO service_role;


--
-- Name: FUNCTION col_is_pk(name, name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.col_is_pk(name, name, name) TO anon;
GRANT ALL ON FUNCTION public.col_is_pk(name, name, name) TO authenticated;
GRANT ALL ON FUNCTION public.col_is_pk(name, name, name) TO service_role;


--
-- Name: FUNCTION col_is_pk(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.col_is_pk(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.col_is_pk(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.col_is_pk(name, name, text) TO service_role;


--
-- Name: FUNCTION col_is_pk(name, name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.col_is_pk(name, name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.col_is_pk(name, name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.col_is_pk(name, name, name[], text) TO service_role;


--
-- Name: FUNCTION col_is_pk(name, name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.col_is_pk(name, name, name, text) TO anon;
GRANT ALL ON FUNCTION public.col_is_pk(name, name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.col_is_pk(name, name, name, text) TO service_role;


--
-- Name: FUNCTION col_is_unique(name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.col_is_unique(name, name[]) TO anon;
GRANT ALL ON FUNCTION public.col_is_unique(name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public.col_is_unique(name, name[]) TO service_role;


--
-- Name: FUNCTION col_is_unique(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.col_is_unique(name, name) TO anon;
GRANT ALL ON FUNCTION public.col_is_unique(name, name) TO authenticated;
GRANT ALL ON FUNCTION public.col_is_unique(name, name) TO service_role;


--
-- Name: FUNCTION col_is_unique(name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.col_is_unique(name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.col_is_unique(name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.col_is_unique(name, name[], text) TO service_role;


--
-- Name: FUNCTION col_is_unique(name, name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.col_is_unique(name, name, name[]) TO anon;
GRANT ALL ON FUNCTION public.col_is_unique(name, name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public.col_is_unique(name, name, name[]) TO service_role;


--
-- Name: FUNCTION col_is_unique(name, name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.col_is_unique(name, name, name) TO anon;
GRANT ALL ON FUNCTION public.col_is_unique(name, name, name) TO authenticated;
GRANT ALL ON FUNCTION public.col_is_unique(name, name, name) TO service_role;


--
-- Name: FUNCTION col_is_unique(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.col_is_unique(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.col_is_unique(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.col_is_unique(name, name, text) TO service_role;


--
-- Name: FUNCTION col_is_unique(name, name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.col_is_unique(name, name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.col_is_unique(name, name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.col_is_unique(name, name, name[], text) TO service_role;


--
-- Name: FUNCTION col_is_unique(name, name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.col_is_unique(name, name, name, text) TO anon;
GRANT ALL ON FUNCTION public.col_is_unique(name, name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.col_is_unique(name, name, name, text) TO service_role;


--
-- Name: FUNCTION col_isnt_fk(name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.col_isnt_fk(name, name[]) TO anon;
GRANT ALL ON FUNCTION public.col_isnt_fk(name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public.col_isnt_fk(name, name[]) TO service_role;


--
-- Name: FUNCTION col_isnt_fk(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.col_isnt_fk(name, name) TO anon;
GRANT ALL ON FUNCTION public.col_isnt_fk(name, name) TO authenticated;
GRANT ALL ON FUNCTION public.col_isnt_fk(name, name) TO service_role;


--
-- Name: FUNCTION col_isnt_fk(name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.col_isnt_fk(name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.col_isnt_fk(name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.col_isnt_fk(name, name[], text) TO service_role;


--
-- Name: FUNCTION col_isnt_fk(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.col_isnt_fk(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.col_isnt_fk(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.col_isnt_fk(name, name, text) TO service_role;


--
-- Name: FUNCTION col_isnt_fk(name, name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.col_isnt_fk(name, name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.col_isnt_fk(name, name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.col_isnt_fk(name, name, name[], text) TO service_role;


--
-- Name: FUNCTION col_isnt_fk(name, name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.col_isnt_fk(name, name, name, text) TO anon;
GRANT ALL ON FUNCTION public.col_isnt_fk(name, name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.col_isnt_fk(name, name, name, text) TO service_role;


--
-- Name: FUNCTION col_isnt_pk(name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.col_isnt_pk(name, name[]) TO anon;
GRANT ALL ON FUNCTION public.col_isnt_pk(name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public.col_isnt_pk(name, name[]) TO service_role;


--
-- Name: FUNCTION col_isnt_pk(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.col_isnt_pk(name, name) TO anon;
GRANT ALL ON FUNCTION public.col_isnt_pk(name, name) TO authenticated;
GRANT ALL ON FUNCTION public.col_isnt_pk(name, name) TO service_role;


--
-- Name: FUNCTION col_isnt_pk(name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.col_isnt_pk(name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.col_isnt_pk(name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.col_isnt_pk(name, name[], text) TO service_role;


--
-- Name: FUNCTION col_isnt_pk(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.col_isnt_pk(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.col_isnt_pk(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.col_isnt_pk(name, name, text) TO service_role;


--
-- Name: FUNCTION col_isnt_pk(name, name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.col_isnt_pk(name, name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.col_isnt_pk(name, name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.col_isnt_pk(name, name, name[], text) TO service_role;


--
-- Name: FUNCTION col_isnt_pk(name, name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.col_isnt_pk(name, name, name, text) TO anon;
GRANT ALL ON FUNCTION public.col_isnt_pk(name, name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.col_isnt_pk(name, name, name, text) TO service_role;


--
-- Name: FUNCTION col_not_null(table_name name, column_name name, description text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.col_not_null(table_name name, column_name name, description text) TO anon;
GRANT ALL ON FUNCTION public.col_not_null(table_name name, column_name name, description text) TO authenticated;
GRANT ALL ON FUNCTION public.col_not_null(table_name name, column_name name, description text) TO service_role;


--
-- Name: FUNCTION col_not_null(schema_name name, table_name name, column_name name, description text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.col_not_null(schema_name name, table_name name, column_name name, description text) TO anon;
GRANT ALL ON FUNCTION public.col_not_null(schema_name name, table_name name, column_name name, description text) TO authenticated;
GRANT ALL ON FUNCTION public.col_not_null(schema_name name, table_name name, column_name name, description text) TO service_role;


--
-- Name: FUNCTION col_type_is(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.col_type_is(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.col_type_is(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.col_type_is(name, name, text) TO service_role;


--
-- Name: FUNCTION col_type_is(name, name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.col_type_is(name, name, name, text) TO anon;
GRANT ALL ON FUNCTION public.col_type_is(name, name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.col_type_is(name, name, name, text) TO service_role;


--
-- Name: FUNCTION col_type_is(name, name, text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.col_type_is(name, name, text, text) TO anon;
GRANT ALL ON FUNCTION public.col_type_is(name, name, text, text) TO authenticated;
GRANT ALL ON FUNCTION public.col_type_is(name, name, text, text) TO service_role;


--
-- Name: FUNCTION col_type_is(name, name, name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.col_type_is(name, name, name, name, text) TO anon;
GRANT ALL ON FUNCTION public.col_type_is(name, name, name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.col_type_is(name, name, name, name, text) TO service_role;


--
-- Name: FUNCTION col_type_is(name, name, name, text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.col_type_is(name, name, name, text, text) TO anon;
GRANT ALL ON FUNCTION public.col_type_is(name, name, name, text, text) TO authenticated;
GRANT ALL ON FUNCTION public.col_type_is(name, name, name, text, text) TO service_role;


--
-- Name: FUNCTION col_type_is(name, name, name, name, text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.col_type_is(name, name, name, name, text, text) TO anon;
GRANT ALL ON FUNCTION public.col_type_is(name, name, name, name, text, text) TO authenticated;
GRANT ALL ON FUNCTION public.col_type_is(name, name, name, name, text, text) TO service_role;


--
-- Name: FUNCTION collect_tap(VARIADIC text[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.collect_tap(VARIADIC text[]) TO anon;
GRANT ALL ON FUNCTION public.collect_tap(VARIADIC text[]) TO authenticated;
GRANT ALL ON FUNCTION public.collect_tap(VARIADIC text[]) TO service_role;


--
-- Name: FUNCTION collect_tap(character varying[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.collect_tap(character varying[]) TO anon;
GRANT ALL ON FUNCTION public.collect_tap(character varying[]) TO authenticated;
GRANT ALL ON FUNCTION public.collect_tap(character varying[]) TO service_role;


--
-- Name: FUNCTION column_privs_are(name, name, name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.column_privs_are(name, name, name, name[]) TO anon;
GRANT ALL ON FUNCTION public.column_privs_are(name, name, name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public.column_privs_are(name, name, name, name[]) TO service_role;


--
-- Name: FUNCTION column_privs_are(name, name, name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.column_privs_are(name, name, name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.column_privs_are(name, name, name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.column_privs_are(name, name, name, name[], text) TO service_role;


--
-- Name: FUNCTION column_privs_are(name, name, name, name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.column_privs_are(name, name, name, name, name[]) TO anon;
GRANT ALL ON FUNCTION public.column_privs_are(name, name, name, name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public.column_privs_are(name, name, name, name, name[]) TO service_role;


--
-- Name: FUNCTION column_privs_are(name, name, name, name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.column_privs_are(name, name, name, name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.column_privs_are(name, name, name, name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.column_privs_are(name, name, name, name, name[], text) TO service_role;


--
-- Name: FUNCTION columns_are(name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.columns_are(name, name[]) TO anon;
GRANT ALL ON FUNCTION public.columns_are(name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public.columns_are(name, name[]) TO service_role;


--
-- Name: FUNCTION columns_are(name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.columns_are(name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.columns_are(name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.columns_are(name, name[], text) TO service_role;


--
-- Name: FUNCTION columns_are(name, name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.columns_are(name, name, name[]) TO anon;
GRANT ALL ON FUNCTION public.columns_are(name, name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public.columns_are(name, name, name[]) TO service_role;


--
-- Name: FUNCTION columns_are(name, name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.columns_are(name, name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.columns_are(name, name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.columns_are(name, name, name[], text) TO service_role;


--
-- Name: FUNCTION composite_owner_is(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.composite_owner_is(name, name) TO anon;
GRANT ALL ON FUNCTION public.composite_owner_is(name, name) TO authenticated;
GRANT ALL ON FUNCTION public.composite_owner_is(name, name) TO service_role;


--
-- Name: FUNCTION composite_owner_is(name, name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.composite_owner_is(name, name, name) TO anon;
GRANT ALL ON FUNCTION public.composite_owner_is(name, name, name) TO authenticated;
GRANT ALL ON FUNCTION public.composite_owner_is(name, name, name) TO service_role;


--
-- Name: FUNCTION composite_owner_is(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.composite_owner_is(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.composite_owner_is(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.composite_owner_is(name, name, text) TO service_role;


--
-- Name: FUNCTION composite_owner_is(name, name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.composite_owner_is(name, name, name, text) TO anon;
GRANT ALL ON FUNCTION public.composite_owner_is(name, name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.composite_owner_is(name, name, name, text) TO service_role;


--
-- Name: FUNCTION crypt(text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.crypt(text, text) TO anon;
GRANT ALL ON FUNCTION public.crypt(text, text) TO authenticated;
GRANT ALL ON FUNCTION public.crypt(text, text) TO service_role;


--
-- Name: FUNCTION current_user_role(); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.current_user_role() TO anon;
GRANT ALL ON FUNCTION public.current_user_role() TO authenticated;
GRANT ALL ON FUNCTION public.current_user_role() TO service_role;


--
-- Name: FUNCTION current_user_tenant_id(); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.current_user_tenant_id() TO anon;
GRANT ALL ON FUNCTION public.current_user_tenant_id() TO authenticated;
GRANT ALL ON FUNCTION public.current_user_tenant_id() TO service_role;


--
-- Name: FUNCTION database_privs_are(name, name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.database_privs_are(name, name, name[]) TO anon;
GRANT ALL ON FUNCTION public.database_privs_are(name, name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public.database_privs_are(name, name, name[]) TO service_role;


--
-- Name: FUNCTION database_privs_are(name, name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.database_privs_are(name, name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.database_privs_are(name, name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.database_privs_are(name, name, name[], text) TO service_role;


--
-- Name: FUNCTION db_owner_is(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.db_owner_is(name, name) TO anon;
GRANT ALL ON FUNCTION public.db_owner_is(name, name) TO authenticated;
GRANT ALL ON FUNCTION public.db_owner_is(name, name) TO service_role;


--
-- Name: FUNCTION db_owner_is(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.db_owner_is(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.db_owner_is(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.db_owner_is(name, name, text) TO service_role;


--
-- Name: FUNCTION dearmor(text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.dearmor(text) TO anon;
GRANT ALL ON FUNCTION public.dearmor(text) TO authenticated;
GRANT ALL ON FUNCTION public.dearmor(text) TO service_role;


--
-- Name: FUNCTION decrypt(bytea, bytea, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.decrypt(bytea, bytea, text) TO anon;
GRANT ALL ON FUNCTION public.decrypt(bytea, bytea, text) TO authenticated;
GRANT ALL ON FUNCTION public.decrypt(bytea, bytea, text) TO service_role;


--
-- Name: FUNCTION decrypt_iv(bytea, bytea, bytea, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.decrypt_iv(bytea, bytea, bytea, text) TO anon;
GRANT ALL ON FUNCTION public.decrypt_iv(bytea, bytea, bytea, text) TO authenticated;
GRANT ALL ON FUNCTION public.decrypt_iv(bytea, bytea, bytea, text) TO service_role;


--
-- Name: FUNCTION diag(VARIADIC text[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.diag(VARIADIC text[]) TO anon;
GRANT ALL ON FUNCTION public.diag(VARIADIC text[]) TO authenticated;
GRANT ALL ON FUNCTION public.diag(VARIADIC text[]) TO service_role;


--
-- Name: FUNCTION diag(VARIADIC anyarray); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.diag(VARIADIC anyarray) TO anon;
GRANT ALL ON FUNCTION public.diag(VARIADIC anyarray) TO authenticated;
GRANT ALL ON FUNCTION public.diag(VARIADIC anyarray) TO service_role;


--
-- Name: FUNCTION diag(msg anyelement); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.diag(msg anyelement) TO anon;
GRANT ALL ON FUNCTION public.diag(msg anyelement) TO authenticated;
GRANT ALL ON FUNCTION public.diag(msg anyelement) TO service_role;


--
-- Name: FUNCTION diag(msg text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.diag(msg text) TO anon;
GRANT ALL ON FUNCTION public.diag(msg text) TO authenticated;
GRANT ALL ON FUNCTION public.diag(msg text) TO service_role;


--
-- Name: FUNCTION diag_test_name(text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.diag_test_name(text) TO anon;
GRANT ALL ON FUNCTION public.diag_test_name(text) TO authenticated;
GRANT ALL ON FUNCTION public.diag_test_name(text) TO service_role;


--
-- Name: FUNCTION digest(bytea, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.digest(bytea, text) TO anon;
GRANT ALL ON FUNCTION public.digest(bytea, text) TO authenticated;
GRANT ALL ON FUNCTION public.digest(bytea, text) TO service_role;


--
-- Name: FUNCTION digest(text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.digest(text, text) TO anon;
GRANT ALL ON FUNCTION public.digest(text, text) TO authenticated;
GRANT ALL ON FUNCTION public.digest(text, text) TO service_role;


--
-- Name: FUNCTION display_oper(name, oid); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.display_oper(name, oid) TO anon;
GRANT ALL ON FUNCTION public.display_oper(name, oid) TO authenticated;
GRANT ALL ON FUNCTION public.display_oper(name, oid) TO service_role;


--
-- Name: FUNCTION do_tap(); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.do_tap() TO anon;
GRANT ALL ON FUNCTION public.do_tap() TO authenticated;
GRANT ALL ON FUNCTION public.do_tap() TO service_role;


--
-- Name: FUNCTION do_tap(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.do_tap(name) TO anon;
GRANT ALL ON FUNCTION public.do_tap(name) TO authenticated;
GRANT ALL ON FUNCTION public.do_tap(name) TO service_role;


--
-- Name: FUNCTION do_tap(text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.do_tap(text) TO anon;
GRANT ALL ON FUNCTION public.do_tap(text) TO authenticated;
GRANT ALL ON FUNCTION public.do_tap(text) TO service_role;


--
-- Name: FUNCTION do_tap(name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.do_tap(name, text) TO anon;
GRANT ALL ON FUNCTION public.do_tap(name, text) TO authenticated;
GRANT ALL ON FUNCTION public.do_tap(name, text) TO service_role;


--
-- Name: FUNCTION doesnt_imatch(anyelement, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.doesnt_imatch(anyelement, text) TO anon;
GRANT ALL ON FUNCTION public.doesnt_imatch(anyelement, text) TO authenticated;
GRANT ALL ON FUNCTION public.doesnt_imatch(anyelement, text) TO service_role;


--
-- Name: FUNCTION doesnt_imatch(anyelement, text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.doesnt_imatch(anyelement, text, text) TO anon;
GRANT ALL ON FUNCTION public.doesnt_imatch(anyelement, text, text) TO authenticated;
GRANT ALL ON FUNCTION public.doesnt_imatch(anyelement, text, text) TO service_role;


--
-- Name: FUNCTION doesnt_match(anyelement, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.doesnt_match(anyelement, text) TO anon;
GRANT ALL ON FUNCTION public.doesnt_match(anyelement, text) TO authenticated;
GRANT ALL ON FUNCTION public.doesnt_match(anyelement, text) TO service_role;


--
-- Name: FUNCTION doesnt_match(anyelement, text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.doesnt_match(anyelement, text, text) TO anon;
GRANT ALL ON FUNCTION public.doesnt_match(anyelement, text, text) TO authenticated;
GRANT ALL ON FUNCTION public.doesnt_match(anyelement, text, text) TO service_role;


--
-- Name: FUNCTION domain_type_is(text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.domain_type_is(text, text) TO anon;
GRANT ALL ON FUNCTION public.domain_type_is(text, text) TO authenticated;
GRANT ALL ON FUNCTION public.domain_type_is(text, text) TO service_role;


--
-- Name: FUNCTION domain_type_is(name, text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.domain_type_is(name, text, text) TO anon;
GRANT ALL ON FUNCTION public.domain_type_is(name, text, text) TO authenticated;
GRANT ALL ON FUNCTION public.domain_type_is(name, text, text) TO service_role;


--
-- Name: FUNCTION domain_type_is(text, text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.domain_type_is(text, text, text) TO anon;
GRANT ALL ON FUNCTION public.domain_type_is(text, text, text) TO authenticated;
GRANT ALL ON FUNCTION public.domain_type_is(text, text, text) TO service_role;


--
-- Name: FUNCTION domain_type_is(name, text, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.domain_type_is(name, text, name, text) TO anon;
GRANT ALL ON FUNCTION public.domain_type_is(name, text, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.domain_type_is(name, text, name, text) TO service_role;


--
-- Name: FUNCTION domain_type_is(name, text, text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.domain_type_is(name, text, text, text) TO anon;
GRANT ALL ON FUNCTION public.domain_type_is(name, text, text, text) TO authenticated;
GRANT ALL ON FUNCTION public.domain_type_is(name, text, text, text) TO service_role;


--
-- Name: FUNCTION domain_type_is(name, text, name, text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.domain_type_is(name, text, name, text, text) TO anon;
GRANT ALL ON FUNCTION public.domain_type_is(name, text, name, text, text) TO authenticated;
GRANT ALL ON FUNCTION public.domain_type_is(name, text, name, text, text) TO service_role;


--
-- Name: FUNCTION domain_type_isnt(text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.domain_type_isnt(text, text) TO anon;
GRANT ALL ON FUNCTION public.domain_type_isnt(text, text) TO authenticated;
GRANT ALL ON FUNCTION public.domain_type_isnt(text, text) TO service_role;


--
-- Name: FUNCTION domain_type_isnt(name, text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.domain_type_isnt(name, text, text) TO anon;
GRANT ALL ON FUNCTION public.domain_type_isnt(name, text, text) TO authenticated;
GRANT ALL ON FUNCTION public.domain_type_isnt(name, text, text) TO service_role;


--
-- Name: FUNCTION domain_type_isnt(text, text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.domain_type_isnt(text, text, text) TO anon;
GRANT ALL ON FUNCTION public.domain_type_isnt(text, text, text) TO authenticated;
GRANT ALL ON FUNCTION public.domain_type_isnt(text, text, text) TO service_role;


--
-- Name: FUNCTION domain_type_isnt(name, text, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.domain_type_isnt(name, text, name, text) TO anon;
GRANT ALL ON FUNCTION public.domain_type_isnt(name, text, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.domain_type_isnt(name, text, name, text) TO service_role;


--
-- Name: FUNCTION domain_type_isnt(name, text, text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.domain_type_isnt(name, text, text, text) TO anon;
GRANT ALL ON FUNCTION public.domain_type_isnt(name, text, text, text) TO authenticated;
GRANT ALL ON FUNCTION public.domain_type_isnt(name, text, text, text) TO service_role;


--
-- Name: FUNCTION domain_type_isnt(name, text, name, text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.domain_type_isnt(name, text, name, text, text) TO anon;
GRANT ALL ON FUNCTION public.domain_type_isnt(name, text, name, text, text) TO authenticated;
GRANT ALL ON FUNCTION public.domain_type_isnt(name, text, name, text, text) TO service_role;


--
-- Name: FUNCTION domains_are(name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.domains_are(name[]) TO anon;
GRANT ALL ON FUNCTION public.domains_are(name[]) TO authenticated;
GRANT ALL ON FUNCTION public.domains_are(name[]) TO service_role;


--
-- Name: FUNCTION domains_are(name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.domains_are(name[], text) TO anon;
GRANT ALL ON FUNCTION public.domains_are(name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.domains_are(name[], text) TO service_role;


--
-- Name: FUNCTION domains_are(name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.domains_are(name, name[]) TO anon;
GRANT ALL ON FUNCTION public.domains_are(name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public.domains_are(name, name[]) TO service_role;


--
-- Name: FUNCTION domains_are(name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.domains_are(name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.domains_are(name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.domains_are(name, name[], text) TO service_role;


--
-- Name: FUNCTION encrypt(bytea, bytea, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.encrypt(bytea, bytea, text) TO anon;
GRANT ALL ON FUNCTION public.encrypt(bytea, bytea, text) TO authenticated;
GRANT ALL ON FUNCTION public.encrypt(bytea, bytea, text) TO service_role;


--
-- Name: FUNCTION encrypt_iv(bytea, bytea, bytea, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.encrypt_iv(bytea, bytea, bytea, text) TO anon;
GRANT ALL ON FUNCTION public.encrypt_iv(bytea, bytea, bytea, text) TO authenticated;
GRANT ALL ON FUNCTION public.encrypt_iv(bytea, bytea, bytea, text) TO service_role;


--
-- Name: FUNCTION enforce_content_generation_jobs_status_guard(); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.enforce_content_generation_jobs_status_guard() TO anon;
GRANT ALL ON FUNCTION public.enforce_content_generation_jobs_status_guard() TO authenticated;
GRANT ALL ON FUNCTION public.enforce_content_generation_jobs_status_guard() TO service_role;


--
-- Name: FUNCTION enforce_notifications_student_update_guard(); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.enforce_notifications_student_update_guard() TO anon;
GRANT ALL ON FUNCTION public.enforce_notifications_student_update_guard() TO authenticated;
GRANT ALL ON FUNCTION public.enforce_notifications_student_update_guard() TO service_role;


--
-- Name: FUNCTION enforce_question_drafts_status_guard(); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.enforce_question_drafts_status_guard() TO anon;
GRANT ALL ON FUNCTION public.enforce_question_drafts_status_guard() TO authenticated;
GRANT ALL ON FUNCTION public.enforce_question_drafts_status_guard() TO service_role;


--
-- Name: FUNCTION enum_has_labels(name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.enum_has_labels(name, name[]) TO anon;
GRANT ALL ON FUNCTION public.enum_has_labels(name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public.enum_has_labels(name, name[]) TO service_role;


--
-- Name: FUNCTION enum_has_labels(name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.enum_has_labels(name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.enum_has_labels(name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.enum_has_labels(name, name[], text) TO service_role;


--
-- Name: FUNCTION enum_has_labels(name, name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.enum_has_labels(name, name, name[]) TO anon;
GRANT ALL ON FUNCTION public.enum_has_labels(name, name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public.enum_has_labels(name, name, name[]) TO service_role;


--
-- Name: FUNCTION enum_has_labels(name, name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.enum_has_labels(name, name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.enum_has_labels(name, name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.enum_has_labels(name, name, name[], text) TO service_role;


--
-- Name: FUNCTION enums_are(name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.enums_are(name[]) TO anon;
GRANT ALL ON FUNCTION public.enums_are(name[]) TO authenticated;
GRANT ALL ON FUNCTION public.enums_are(name[]) TO service_role;


--
-- Name: FUNCTION enums_are(name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.enums_are(name[], text) TO anon;
GRANT ALL ON FUNCTION public.enums_are(name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.enums_are(name[], text) TO service_role;


--
-- Name: FUNCTION enums_are(name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.enums_are(name, name[]) TO anon;
GRANT ALL ON FUNCTION public.enums_are(name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public.enums_are(name, name[]) TO service_role;


--
-- Name: FUNCTION enums_are(name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.enums_are(name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.enums_are(name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.enums_are(name, name[], text) TO service_role;


--
-- Name: FUNCTION extensions_are(name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.extensions_are(name[]) TO anon;
GRANT ALL ON FUNCTION public.extensions_are(name[]) TO authenticated;
GRANT ALL ON FUNCTION public.extensions_are(name[]) TO service_role;


--
-- Name: FUNCTION extensions_are(name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.extensions_are(name[], text) TO anon;
GRANT ALL ON FUNCTION public.extensions_are(name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.extensions_are(name[], text) TO service_role;


--
-- Name: FUNCTION extensions_are(name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.extensions_are(name, name[]) TO anon;
GRANT ALL ON FUNCTION public.extensions_are(name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public.extensions_are(name, name[]) TO service_role;


--
-- Name: FUNCTION extensions_are(name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.extensions_are(name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.extensions_are(name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.extensions_are(name, name[], text) TO service_role;


--
-- Name: FUNCTION fail(); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.fail() TO anon;
GRANT ALL ON FUNCTION public.fail() TO authenticated;
GRANT ALL ON FUNCTION public.fail() TO service_role;


--
-- Name: FUNCTION fail(text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.fail(text) TO anon;
GRANT ALL ON FUNCTION public.fail(text) TO authenticated;
GRANT ALL ON FUNCTION public.fail(text) TO service_role;


--
-- Name: FUNCTION fdw_privs_are(name, name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.fdw_privs_are(name, name, name[]) TO anon;
GRANT ALL ON FUNCTION public.fdw_privs_are(name, name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public.fdw_privs_are(name, name, name[]) TO service_role;


--
-- Name: FUNCTION fdw_privs_are(name, name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.fdw_privs_are(name, name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.fdw_privs_are(name, name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.fdw_privs_are(name, name, name[], text) TO service_role;


--
-- Name: FUNCTION findfuncs(text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.findfuncs(text) TO anon;
GRANT ALL ON FUNCTION public.findfuncs(text) TO authenticated;
GRANT ALL ON FUNCTION public.findfuncs(text) TO service_role;


--
-- Name: FUNCTION findfuncs(name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.findfuncs(name, text) TO anon;
GRANT ALL ON FUNCTION public.findfuncs(name, text) TO authenticated;
GRANT ALL ON FUNCTION public.findfuncs(name, text) TO service_role;


--
-- Name: FUNCTION findfuncs(text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.findfuncs(text, text) TO anon;
GRANT ALL ON FUNCTION public.findfuncs(text, text) TO authenticated;
GRANT ALL ON FUNCTION public.findfuncs(text, text) TO service_role;


--
-- Name: FUNCTION findfuncs(name, text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.findfuncs(name, text, text) TO anon;
GRANT ALL ON FUNCTION public.findfuncs(name, text, text) TO authenticated;
GRANT ALL ON FUNCTION public.findfuncs(name, text, text) TO service_role;


--
-- Name: FUNCTION finish(exception_on_failure boolean); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.finish(exception_on_failure boolean) TO anon;
GRANT ALL ON FUNCTION public.finish(exception_on_failure boolean) TO authenticated;
GRANT ALL ON FUNCTION public.finish(exception_on_failure boolean) TO service_role;


--
-- Name: FUNCTION fk_ok(name, name[], name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.fk_ok(name, name[], name, name[]) TO anon;
GRANT ALL ON FUNCTION public.fk_ok(name, name[], name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public.fk_ok(name, name[], name, name[]) TO service_role;


--
-- Name: FUNCTION fk_ok(name, name, name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.fk_ok(name, name, name, name) TO anon;
GRANT ALL ON FUNCTION public.fk_ok(name, name, name, name) TO authenticated;
GRANT ALL ON FUNCTION public.fk_ok(name, name, name, name) TO service_role;


--
-- Name: FUNCTION fk_ok(name, name[], name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.fk_ok(name, name[], name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.fk_ok(name, name[], name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.fk_ok(name, name[], name, name[], text) TO service_role;


--
-- Name: FUNCTION fk_ok(name, name, name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.fk_ok(name, name, name, name, text) TO anon;
GRANT ALL ON FUNCTION public.fk_ok(name, name, name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.fk_ok(name, name, name, name, text) TO service_role;


--
-- Name: FUNCTION fk_ok(name, name, name[], name, name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.fk_ok(name, name, name[], name, name, name[]) TO anon;
GRANT ALL ON FUNCTION public.fk_ok(name, name, name[], name, name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public.fk_ok(name, name, name[], name, name, name[]) TO service_role;


--
-- Name: FUNCTION fk_ok(name, name, name, name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.fk_ok(name, name, name, name, name, text) TO anon;
GRANT ALL ON FUNCTION public.fk_ok(name, name, name, name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.fk_ok(name, name, name, name, name, text) TO service_role;


--
-- Name: FUNCTION fk_ok(name, name, name[], name, name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.fk_ok(name, name, name[], name, name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.fk_ok(name, name, name[], name, name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.fk_ok(name, name, name[], name, name, name[], text) TO service_role;


--
-- Name: FUNCTION fk_ok(name, name, name, name, name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.fk_ok(name, name, name, name, name, name, text) TO anon;
GRANT ALL ON FUNCTION public.fk_ok(name, name, name, name, name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.fk_ok(name, name, name, name, name, name, text) TO service_role;


--
-- Name: FUNCTION foreign_table_owner_is(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.foreign_table_owner_is(name, name) TO anon;
GRANT ALL ON FUNCTION public.foreign_table_owner_is(name, name) TO authenticated;
GRANT ALL ON FUNCTION public.foreign_table_owner_is(name, name) TO service_role;


--
-- Name: FUNCTION foreign_table_owner_is(name, name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.foreign_table_owner_is(name, name, name) TO anon;
GRANT ALL ON FUNCTION public.foreign_table_owner_is(name, name, name) TO authenticated;
GRANT ALL ON FUNCTION public.foreign_table_owner_is(name, name, name) TO service_role;


--
-- Name: FUNCTION foreign_table_owner_is(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.foreign_table_owner_is(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.foreign_table_owner_is(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.foreign_table_owner_is(name, name, text) TO service_role;


--
-- Name: FUNCTION foreign_table_owner_is(name, name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.foreign_table_owner_is(name, name, name, text) TO anon;
GRANT ALL ON FUNCTION public.foreign_table_owner_is(name, name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.foreign_table_owner_is(name, name, name, text) TO service_role;


--
-- Name: FUNCTION foreign_tables_are(name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.foreign_tables_are(name[]) TO anon;
GRANT ALL ON FUNCTION public.foreign_tables_are(name[]) TO authenticated;
GRANT ALL ON FUNCTION public.foreign_tables_are(name[]) TO service_role;


--
-- Name: FUNCTION foreign_tables_are(name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.foreign_tables_are(name[], text) TO anon;
GRANT ALL ON FUNCTION public.foreign_tables_are(name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.foreign_tables_are(name[], text) TO service_role;


--
-- Name: FUNCTION foreign_tables_are(name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.foreign_tables_are(name, name[]) TO anon;
GRANT ALL ON FUNCTION public.foreign_tables_are(name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public.foreign_tables_are(name, name[]) TO service_role;


--
-- Name: FUNCTION foreign_tables_are(name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.foreign_tables_are(name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.foreign_tables_are(name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.foreign_tables_are(name, name[], text) TO service_role;


--
-- Name: FUNCTION format_type_string(text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.format_type_string(text) TO anon;
GRANT ALL ON FUNCTION public.format_type_string(text) TO authenticated;
GRANT ALL ON FUNCTION public.format_type_string(text) TO service_role;


--
-- Name: FUNCTION function_lang_is(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.function_lang_is(name, name) TO anon;
GRANT ALL ON FUNCTION public.function_lang_is(name, name) TO authenticated;
GRANT ALL ON FUNCTION public.function_lang_is(name, name) TO service_role;


--
-- Name: FUNCTION function_lang_is(name, name[], name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.function_lang_is(name, name[], name) TO anon;
GRANT ALL ON FUNCTION public.function_lang_is(name, name[], name) TO authenticated;
GRANT ALL ON FUNCTION public.function_lang_is(name, name[], name) TO service_role;


--
-- Name: FUNCTION function_lang_is(name, name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.function_lang_is(name, name, name) TO anon;
GRANT ALL ON FUNCTION public.function_lang_is(name, name, name) TO authenticated;
GRANT ALL ON FUNCTION public.function_lang_is(name, name, name) TO service_role;


--
-- Name: FUNCTION function_lang_is(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.function_lang_is(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.function_lang_is(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.function_lang_is(name, name, text) TO service_role;


--
-- Name: FUNCTION function_lang_is(name, name[], name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.function_lang_is(name, name[], name, text) TO anon;
GRANT ALL ON FUNCTION public.function_lang_is(name, name[], name, text) TO authenticated;
GRANT ALL ON FUNCTION public.function_lang_is(name, name[], name, text) TO service_role;


--
-- Name: FUNCTION function_lang_is(name, name, name[], name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.function_lang_is(name, name, name[], name) TO anon;
GRANT ALL ON FUNCTION public.function_lang_is(name, name, name[], name) TO authenticated;
GRANT ALL ON FUNCTION public.function_lang_is(name, name, name[], name) TO service_role;


--
-- Name: FUNCTION function_lang_is(name, name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.function_lang_is(name, name, name, text) TO anon;
GRANT ALL ON FUNCTION public.function_lang_is(name, name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.function_lang_is(name, name, name, text) TO service_role;


--
-- Name: FUNCTION function_lang_is(name, name, name[], name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.function_lang_is(name, name, name[], name, text) TO anon;
GRANT ALL ON FUNCTION public.function_lang_is(name, name, name[], name, text) TO authenticated;
GRANT ALL ON FUNCTION public.function_lang_is(name, name, name[], name, text) TO service_role;


--
-- Name: FUNCTION function_owner_is(name, name[], name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.function_owner_is(name, name[], name) TO anon;
GRANT ALL ON FUNCTION public.function_owner_is(name, name[], name) TO authenticated;
GRANT ALL ON FUNCTION public.function_owner_is(name, name[], name) TO service_role;


--
-- Name: FUNCTION function_owner_is(name, name[], name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.function_owner_is(name, name[], name, text) TO anon;
GRANT ALL ON FUNCTION public.function_owner_is(name, name[], name, text) TO authenticated;
GRANT ALL ON FUNCTION public.function_owner_is(name, name[], name, text) TO service_role;


--
-- Name: FUNCTION function_owner_is(name, name, name[], name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.function_owner_is(name, name, name[], name) TO anon;
GRANT ALL ON FUNCTION public.function_owner_is(name, name, name[], name) TO authenticated;
GRANT ALL ON FUNCTION public.function_owner_is(name, name, name[], name) TO service_role;


--
-- Name: FUNCTION function_owner_is(name, name, name[], name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.function_owner_is(name, name, name[], name, text) TO anon;
GRANT ALL ON FUNCTION public.function_owner_is(name, name, name[], name, text) TO authenticated;
GRANT ALL ON FUNCTION public.function_owner_is(name, name, name[], name, text) TO service_role;


--
-- Name: FUNCTION function_privs_are(name, name[], name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.function_privs_are(name, name[], name, name[]) TO anon;
GRANT ALL ON FUNCTION public.function_privs_are(name, name[], name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public.function_privs_are(name, name[], name, name[]) TO service_role;


--
-- Name: FUNCTION function_privs_are(name, name[], name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.function_privs_are(name, name[], name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.function_privs_are(name, name[], name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.function_privs_are(name, name[], name, name[], text) TO service_role;


--
-- Name: FUNCTION function_privs_are(name, name, name[], name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.function_privs_are(name, name, name[], name, name[]) TO anon;
GRANT ALL ON FUNCTION public.function_privs_are(name, name, name[], name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public.function_privs_are(name, name, name[], name, name[]) TO service_role;


--
-- Name: FUNCTION function_privs_are(name, name, name[], name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.function_privs_are(name, name, name[], name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.function_privs_are(name, name, name[], name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.function_privs_are(name, name, name[], name, name[], text) TO service_role;


--
-- Name: FUNCTION function_returns(name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.function_returns(name, text) TO anon;
GRANT ALL ON FUNCTION public.function_returns(name, text) TO authenticated;
GRANT ALL ON FUNCTION public.function_returns(name, text) TO service_role;


--
-- Name: FUNCTION function_returns(name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.function_returns(name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.function_returns(name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.function_returns(name, name[], text) TO service_role;


--
-- Name: FUNCTION function_returns(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.function_returns(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.function_returns(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.function_returns(name, name, text) TO service_role;


--
-- Name: FUNCTION function_returns(name, text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.function_returns(name, text, text) TO anon;
GRANT ALL ON FUNCTION public.function_returns(name, text, text) TO authenticated;
GRANT ALL ON FUNCTION public.function_returns(name, text, text) TO service_role;


--
-- Name: FUNCTION function_returns(name, name[], text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.function_returns(name, name[], text, text) TO anon;
GRANT ALL ON FUNCTION public.function_returns(name, name[], text, text) TO authenticated;
GRANT ALL ON FUNCTION public.function_returns(name, name[], text, text) TO service_role;


--
-- Name: FUNCTION function_returns(name, name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.function_returns(name, name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.function_returns(name, name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.function_returns(name, name, name[], text) TO service_role;


--
-- Name: FUNCTION function_returns(name, name, text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.function_returns(name, name, text, text) TO anon;
GRANT ALL ON FUNCTION public.function_returns(name, name, text, text) TO authenticated;
GRANT ALL ON FUNCTION public.function_returns(name, name, text, text) TO service_role;


--
-- Name: FUNCTION function_returns(name, name, name[], text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.function_returns(name, name, name[], text, text) TO anon;
GRANT ALL ON FUNCTION public.function_returns(name, name, name[], text, text) TO authenticated;
GRANT ALL ON FUNCTION public.function_returns(name, name, name[], text, text) TO service_role;


--
-- Name: FUNCTION functions_are(name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.functions_are(name[]) TO anon;
GRANT ALL ON FUNCTION public.functions_are(name[]) TO authenticated;
GRANT ALL ON FUNCTION public.functions_are(name[]) TO service_role;


--
-- Name: FUNCTION functions_are(name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.functions_are(name[], text) TO anon;
GRANT ALL ON FUNCTION public.functions_are(name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.functions_are(name[], text) TO service_role;


--
-- Name: FUNCTION functions_are(name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.functions_are(name, name[]) TO anon;
GRANT ALL ON FUNCTION public.functions_are(name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public.functions_are(name, name[]) TO service_role;


--
-- Name: FUNCTION functions_are(name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.functions_are(name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.functions_are(name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.functions_are(name, name[], text) TO service_role;


--
-- Name: FUNCTION gen_random_bytes(integer); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.gen_random_bytes(integer) TO anon;
GRANT ALL ON FUNCTION public.gen_random_bytes(integer) TO authenticated;
GRANT ALL ON FUNCTION public.gen_random_bytes(integer) TO service_role;


--
-- Name: FUNCTION gen_random_uuid(); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.gen_random_uuid() TO anon;
GRANT ALL ON FUNCTION public.gen_random_uuid() TO authenticated;
GRANT ALL ON FUNCTION public.gen_random_uuid() TO service_role;


--
-- Name: FUNCTION gen_salt(text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.gen_salt(text) TO anon;
GRANT ALL ON FUNCTION public.gen_salt(text) TO authenticated;
GRANT ALL ON FUNCTION public.gen_salt(text) TO service_role;


--
-- Name: FUNCTION gen_salt(text, integer); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.gen_salt(text, integer) TO anon;
GRANT ALL ON FUNCTION public.gen_salt(text, integer) TO authenticated;
GRANT ALL ON FUNCTION public.gen_salt(text, integer) TO service_role;


--
-- Name: FUNCTION groups_are(name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.groups_are(name[]) TO anon;
GRANT ALL ON FUNCTION public.groups_are(name[]) TO authenticated;
GRANT ALL ON FUNCTION public.groups_are(name[]) TO service_role;


--
-- Name: FUNCTION groups_are(name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.groups_are(name[], text) TO anon;
GRANT ALL ON FUNCTION public.groups_are(name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.groups_are(name[], text) TO service_role;


--
-- Name: FUNCTION has_cast(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_cast(name, name) TO anon;
GRANT ALL ON FUNCTION public.has_cast(name, name) TO authenticated;
GRANT ALL ON FUNCTION public.has_cast(name, name) TO service_role;


--
-- Name: FUNCTION has_cast(name, name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_cast(name, name, name) TO anon;
GRANT ALL ON FUNCTION public.has_cast(name, name, name) TO authenticated;
GRANT ALL ON FUNCTION public.has_cast(name, name, name) TO service_role;


--
-- Name: FUNCTION has_cast(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_cast(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.has_cast(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.has_cast(name, name, text) TO service_role;


--
-- Name: FUNCTION has_cast(name, name, name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_cast(name, name, name, name) TO anon;
GRANT ALL ON FUNCTION public.has_cast(name, name, name, name) TO authenticated;
GRANT ALL ON FUNCTION public.has_cast(name, name, name, name) TO service_role;


--
-- Name: FUNCTION has_cast(name, name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_cast(name, name, name, text) TO anon;
GRANT ALL ON FUNCTION public.has_cast(name, name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.has_cast(name, name, name, text) TO service_role;


--
-- Name: FUNCTION has_cast(name, name, name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_cast(name, name, name, name, text) TO anon;
GRANT ALL ON FUNCTION public.has_cast(name, name, name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.has_cast(name, name, name, name, text) TO service_role;


--
-- Name: FUNCTION has_check(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_check(name) TO anon;
GRANT ALL ON FUNCTION public.has_check(name) TO authenticated;
GRANT ALL ON FUNCTION public.has_check(name) TO service_role;


--
-- Name: FUNCTION has_check(name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_check(name, text) TO anon;
GRANT ALL ON FUNCTION public.has_check(name, text) TO authenticated;
GRANT ALL ON FUNCTION public.has_check(name, text) TO service_role;


--
-- Name: FUNCTION has_check(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_check(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.has_check(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.has_check(name, name, text) TO service_role;


--
-- Name: FUNCTION has_column(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_column(name, name) TO anon;
GRANT ALL ON FUNCTION public.has_column(name, name) TO authenticated;
GRANT ALL ON FUNCTION public.has_column(name, name) TO service_role;


--
-- Name: FUNCTION has_column(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_column(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.has_column(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.has_column(name, name, text) TO service_role;


--
-- Name: FUNCTION has_column(name, name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_column(name, name, name, text) TO anon;
GRANT ALL ON FUNCTION public.has_column(name, name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.has_column(name, name, name, text) TO service_role;


--
-- Name: FUNCTION has_composite(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_composite(name) TO anon;
GRANT ALL ON FUNCTION public.has_composite(name) TO authenticated;
GRANT ALL ON FUNCTION public.has_composite(name) TO service_role;


--
-- Name: FUNCTION has_composite(name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_composite(name, text) TO anon;
GRANT ALL ON FUNCTION public.has_composite(name, text) TO authenticated;
GRANT ALL ON FUNCTION public.has_composite(name, text) TO service_role;


--
-- Name: FUNCTION has_composite(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_composite(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.has_composite(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.has_composite(name, name, text) TO service_role;


--
-- Name: FUNCTION has_domain(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_domain(name) TO anon;
GRANT ALL ON FUNCTION public.has_domain(name) TO authenticated;
GRANT ALL ON FUNCTION public.has_domain(name) TO service_role;


--
-- Name: FUNCTION has_domain(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_domain(name, name) TO anon;
GRANT ALL ON FUNCTION public.has_domain(name, name) TO authenticated;
GRANT ALL ON FUNCTION public.has_domain(name, name) TO service_role;


--
-- Name: FUNCTION has_domain(name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_domain(name, text) TO anon;
GRANT ALL ON FUNCTION public.has_domain(name, text) TO authenticated;
GRANT ALL ON FUNCTION public.has_domain(name, text) TO service_role;


--
-- Name: FUNCTION has_domain(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_domain(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.has_domain(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.has_domain(name, name, text) TO service_role;


--
-- Name: FUNCTION has_enum(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_enum(name) TO anon;
GRANT ALL ON FUNCTION public.has_enum(name) TO authenticated;
GRANT ALL ON FUNCTION public.has_enum(name) TO service_role;


--
-- Name: FUNCTION has_enum(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_enum(name, name) TO anon;
GRANT ALL ON FUNCTION public.has_enum(name, name) TO authenticated;
GRANT ALL ON FUNCTION public.has_enum(name, name) TO service_role;


--
-- Name: FUNCTION has_enum(name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_enum(name, text) TO anon;
GRANT ALL ON FUNCTION public.has_enum(name, text) TO authenticated;
GRANT ALL ON FUNCTION public.has_enum(name, text) TO service_role;


--
-- Name: FUNCTION has_enum(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_enum(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.has_enum(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.has_enum(name, name, text) TO service_role;


--
-- Name: FUNCTION has_extension(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_extension(name) TO anon;
GRANT ALL ON FUNCTION public.has_extension(name) TO authenticated;
GRANT ALL ON FUNCTION public.has_extension(name) TO service_role;


--
-- Name: FUNCTION has_extension(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_extension(name, name) TO anon;
GRANT ALL ON FUNCTION public.has_extension(name, name) TO authenticated;
GRANT ALL ON FUNCTION public.has_extension(name, name) TO service_role;


--
-- Name: FUNCTION has_extension(name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_extension(name, text) TO anon;
GRANT ALL ON FUNCTION public.has_extension(name, text) TO authenticated;
GRANT ALL ON FUNCTION public.has_extension(name, text) TO service_role;


--
-- Name: FUNCTION has_extension(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_extension(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.has_extension(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.has_extension(name, name, text) TO service_role;


--
-- Name: FUNCTION has_fk(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_fk(name) TO anon;
GRANT ALL ON FUNCTION public.has_fk(name) TO authenticated;
GRANT ALL ON FUNCTION public.has_fk(name) TO service_role;


--
-- Name: FUNCTION has_fk(name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_fk(name, text) TO anon;
GRANT ALL ON FUNCTION public.has_fk(name, text) TO authenticated;
GRANT ALL ON FUNCTION public.has_fk(name, text) TO service_role;


--
-- Name: FUNCTION has_fk(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_fk(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.has_fk(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.has_fk(name, name, text) TO service_role;


--
-- Name: FUNCTION has_foreign_table(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_foreign_table(name) TO anon;
GRANT ALL ON FUNCTION public.has_foreign_table(name) TO authenticated;
GRANT ALL ON FUNCTION public.has_foreign_table(name) TO service_role;


--
-- Name: FUNCTION has_foreign_table(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_foreign_table(name, name) TO anon;
GRANT ALL ON FUNCTION public.has_foreign_table(name, name) TO authenticated;
GRANT ALL ON FUNCTION public.has_foreign_table(name, name) TO service_role;


--
-- Name: FUNCTION has_foreign_table(name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_foreign_table(name, text) TO anon;
GRANT ALL ON FUNCTION public.has_foreign_table(name, text) TO authenticated;
GRANT ALL ON FUNCTION public.has_foreign_table(name, text) TO service_role;


--
-- Name: FUNCTION has_foreign_table(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_foreign_table(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.has_foreign_table(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.has_foreign_table(name, name, text) TO service_role;


--
-- Name: FUNCTION has_function(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_function(name) TO anon;
GRANT ALL ON FUNCTION public.has_function(name) TO authenticated;
GRANT ALL ON FUNCTION public.has_function(name) TO service_role;


--
-- Name: FUNCTION has_function(name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_function(name, name[]) TO anon;
GRANT ALL ON FUNCTION public.has_function(name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public.has_function(name, name[]) TO service_role;


--
-- Name: FUNCTION has_function(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_function(name, name) TO anon;
GRANT ALL ON FUNCTION public.has_function(name, name) TO authenticated;
GRANT ALL ON FUNCTION public.has_function(name, name) TO service_role;


--
-- Name: FUNCTION has_function(name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_function(name, text) TO anon;
GRANT ALL ON FUNCTION public.has_function(name, text) TO authenticated;
GRANT ALL ON FUNCTION public.has_function(name, text) TO service_role;


--
-- Name: FUNCTION has_function(name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_function(name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.has_function(name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.has_function(name, name[], text) TO service_role;


--
-- Name: FUNCTION has_function(name, name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_function(name, name, name[]) TO anon;
GRANT ALL ON FUNCTION public.has_function(name, name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public.has_function(name, name, name[]) TO service_role;


--
-- Name: FUNCTION has_function(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_function(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.has_function(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.has_function(name, name, text) TO service_role;


--
-- Name: FUNCTION has_function(name, name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_function(name, name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.has_function(name, name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.has_function(name, name, name[], text) TO service_role;


--
-- Name: FUNCTION has_group(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_group(name) TO anon;
GRANT ALL ON FUNCTION public.has_group(name) TO authenticated;
GRANT ALL ON FUNCTION public.has_group(name) TO service_role;


--
-- Name: FUNCTION has_group(name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_group(name, text) TO anon;
GRANT ALL ON FUNCTION public.has_group(name, text) TO authenticated;
GRANT ALL ON FUNCTION public.has_group(name, text) TO service_role;


--
-- Name: FUNCTION has_index(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_index(name, name) TO anon;
GRANT ALL ON FUNCTION public.has_index(name, name) TO authenticated;
GRANT ALL ON FUNCTION public.has_index(name, name) TO service_role;


--
-- Name: FUNCTION has_index(name, name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_index(name, name, name[]) TO anon;
GRANT ALL ON FUNCTION public.has_index(name, name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public.has_index(name, name, name[]) TO service_role;


--
-- Name: FUNCTION has_index(name, name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_index(name, name, name) TO anon;
GRANT ALL ON FUNCTION public.has_index(name, name, name) TO authenticated;
GRANT ALL ON FUNCTION public.has_index(name, name, name) TO service_role;


--
-- Name: FUNCTION has_index(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_index(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.has_index(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.has_index(name, name, text) TO service_role;


--
-- Name: FUNCTION has_index(name, name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_index(name, name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.has_index(name, name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.has_index(name, name, name[], text) TO service_role;


--
-- Name: FUNCTION has_index(name, name, name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_index(name, name, name, name[]) TO anon;
GRANT ALL ON FUNCTION public.has_index(name, name, name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public.has_index(name, name, name, name[]) TO service_role;


--
-- Name: FUNCTION has_index(name, name, name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_index(name, name, name, name) TO anon;
GRANT ALL ON FUNCTION public.has_index(name, name, name, name) TO authenticated;
GRANT ALL ON FUNCTION public.has_index(name, name, name, name) TO service_role;


--
-- Name: FUNCTION has_index(name, name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_index(name, name, name, text) TO anon;
GRANT ALL ON FUNCTION public.has_index(name, name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.has_index(name, name, name, text) TO service_role;


--
-- Name: FUNCTION has_index(name, name, name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_index(name, name, name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.has_index(name, name, name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.has_index(name, name, name, name[], text) TO service_role;


--
-- Name: FUNCTION has_index(name, name, name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_index(name, name, name, name, text) TO anon;
GRANT ALL ON FUNCTION public.has_index(name, name, name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.has_index(name, name, name, name, text) TO service_role;


--
-- Name: FUNCTION has_inherited_tables(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_inherited_tables(name) TO anon;
GRANT ALL ON FUNCTION public.has_inherited_tables(name) TO authenticated;
GRANT ALL ON FUNCTION public.has_inherited_tables(name) TO service_role;


--
-- Name: FUNCTION has_inherited_tables(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_inherited_tables(name, name) TO anon;
GRANT ALL ON FUNCTION public.has_inherited_tables(name, name) TO authenticated;
GRANT ALL ON FUNCTION public.has_inherited_tables(name, name) TO service_role;


--
-- Name: FUNCTION has_inherited_tables(name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_inherited_tables(name, text) TO anon;
GRANT ALL ON FUNCTION public.has_inherited_tables(name, text) TO authenticated;
GRANT ALL ON FUNCTION public.has_inherited_tables(name, text) TO service_role;


--
-- Name: FUNCTION has_inherited_tables(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_inherited_tables(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.has_inherited_tables(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.has_inherited_tables(name, name, text) TO service_role;


--
-- Name: FUNCTION has_language(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_language(name) TO anon;
GRANT ALL ON FUNCTION public.has_language(name) TO authenticated;
GRANT ALL ON FUNCTION public.has_language(name) TO service_role;


--
-- Name: FUNCTION has_language(name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_language(name, text) TO anon;
GRANT ALL ON FUNCTION public.has_language(name, text) TO authenticated;
GRANT ALL ON FUNCTION public.has_language(name, text) TO service_role;


--
-- Name: FUNCTION has_leftop(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_leftop(name, name) TO anon;
GRANT ALL ON FUNCTION public.has_leftop(name, name) TO authenticated;
GRANT ALL ON FUNCTION public.has_leftop(name, name) TO service_role;


--
-- Name: FUNCTION has_leftop(name, name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_leftop(name, name, name) TO anon;
GRANT ALL ON FUNCTION public.has_leftop(name, name, name) TO authenticated;
GRANT ALL ON FUNCTION public.has_leftop(name, name, name) TO service_role;


--
-- Name: FUNCTION has_leftop(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_leftop(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.has_leftop(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.has_leftop(name, name, text) TO service_role;


--
-- Name: FUNCTION has_leftop(name, name, name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_leftop(name, name, name, name) TO anon;
GRANT ALL ON FUNCTION public.has_leftop(name, name, name, name) TO authenticated;
GRANT ALL ON FUNCTION public.has_leftop(name, name, name, name) TO service_role;


--
-- Name: FUNCTION has_leftop(name, name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_leftop(name, name, name, text) TO anon;
GRANT ALL ON FUNCTION public.has_leftop(name, name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.has_leftop(name, name, name, text) TO service_role;


--
-- Name: FUNCTION has_leftop(name, name, name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_leftop(name, name, name, name, text) TO anon;
GRANT ALL ON FUNCTION public.has_leftop(name, name, name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.has_leftop(name, name, name, name, text) TO service_role;


--
-- Name: FUNCTION has_materialized_view(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_materialized_view(name) TO anon;
GRANT ALL ON FUNCTION public.has_materialized_view(name) TO authenticated;
GRANT ALL ON FUNCTION public.has_materialized_view(name) TO service_role;


--
-- Name: FUNCTION has_materialized_view(name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_materialized_view(name, text) TO anon;
GRANT ALL ON FUNCTION public.has_materialized_view(name, text) TO authenticated;
GRANT ALL ON FUNCTION public.has_materialized_view(name, text) TO service_role;


--
-- Name: FUNCTION has_materialized_view(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_materialized_view(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.has_materialized_view(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.has_materialized_view(name, name, text) TO service_role;


--
-- Name: FUNCTION has_opclass(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_opclass(name) TO anon;
GRANT ALL ON FUNCTION public.has_opclass(name) TO authenticated;
GRANT ALL ON FUNCTION public.has_opclass(name) TO service_role;


--
-- Name: FUNCTION has_opclass(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_opclass(name, name) TO anon;
GRANT ALL ON FUNCTION public.has_opclass(name, name) TO authenticated;
GRANT ALL ON FUNCTION public.has_opclass(name, name) TO service_role;


--
-- Name: FUNCTION has_opclass(name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_opclass(name, text) TO anon;
GRANT ALL ON FUNCTION public.has_opclass(name, text) TO authenticated;
GRANT ALL ON FUNCTION public.has_opclass(name, text) TO service_role;


--
-- Name: FUNCTION has_opclass(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_opclass(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.has_opclass(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.has_opclass(name, name, text) TO service_role;


--
-- Name: FUNCTION has_operator(name, name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_operator(name, name, name) TO anon;
GRANT ALL ON FUNCTION public.has_operator(name, name, name) TO authenticated;
GRANT ALL ON FUNCTION public.has_operator(name, name, name) TO service_role;


--
-- Name: FUNCTION has_operator(name, name, name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_operator(name, name, name, name) TO anon;
GRANT ALL ON FUNCTION public.has_operator(name, name, name, name) TO authenticated;
GRANT ALL ON FUNCTION public.has_operator(name, name, name, name) TO service_role;


--
-- Name: FUNCTION has_operator(name, name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_operator(name, name, name, text) TO anon;
GRANT ALL ON FUNCTION public.has_operator(name, name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.has_operator(name, name, name, text) TO service_role;


--
-- Name: FUNCTION has_operator(name, name, name, name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_operator(name, name, name, name, name) TO anon;
GRANT ALL ON FUNCTION public.has_operator(name, name, name, name, name) TO authenticated;
GRANT ALL ON FUNCTION public.has_operator(name, name, name, name, name) TO service_role;


--
-- Name: FUNCTION has_operator(name, name, name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_operator(name, name, name, name, text) TO anon;
GRANT ALL ON FUNCTION public.has_operator(name, name, name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.has_operator(name, name, name, name, text) TO service_role;


--
-- Name: FUNCTION has_operator(name, name, name, name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_operator(name, name, name, name, name, text) TO anon;
GRANT ALL ON FUNCTION public.has_operator(name, name, name, name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.has_operator(name, name, name, name, name, text) TO service_role;


--
-- Name: FUNCTION has_pk(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_pk(name) TO anon;
GRANT ALL ON FUNCTION public.has_pk(name) TO authenticated;
GRANT ALL ON FUNCTION public.has_pk(name) TO service_role;


--
-- Name: FUNCTION has_pk(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_pk(name, name) TO anon;
GRANT ALL ON FUNCTION public.has_pk(name, name) TO authenticated;
GRANT ALL ON FUNCTION public.has_pk(name, name) TO service_role;


--
-- Name: FUNCTION has_pk(name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_pk(name, text) TO anon;
GRANT ALL ON FUNCTION public.has_pk(name, text) TO authenticated;
GRANT ALL ON FUNCTION public.has_pk(name, text) TO service_role;


--
-- Name: FUNCTION has_pk(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_pk(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.has_pk(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.has_pk(name, name, text) TO service_role;


--
-- Name: FUNCTION has_relation(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_relation(name) TO anon;
GRANT ALL ON FUNCTION public.has_relation(name) TO authenticated;
GRANT ALL ON FUNCTION public.has_relation(name) TO service_role;


--
-- Name: FUNCTION has_relation(name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_relation(name, text) TO anon;
GRANT ALL ON FUNCTION public.has_relation(name, text) TO authenticated;
GRANT ALL ON FUNCTION public.has_relation(name, text) TO service_role;


--
-- Name: FUNCTION has_relation(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_relation(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.has_relation(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.has_relation(name, name, text) TO service_role;


--
-- Name: FUNCTION has_rightop(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_rightop(name, name) TO anon;
GRANT ALL ON FUNCTION public.has_rightop(name, name) TO authenticated;
GRANT ALL ON FUNCTION public.has_rightop(name, name) TO service_role;


--
-- Name: FUNCTION has_rightop(name, name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_rightop(name, name, name) TO anon;
GRANT ALL ON FUNCTION public.has_rightop(name, name, name) TO authenticated;
GRANT ALL ON FUNCTION public.has_rightop(name, name, name) TO service_role;


--
-- Name: FUNCTION has_rightop(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_rightop(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.has_rightop(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.has_rightop(name, name, text) TO service_role;


--
-- Name: FUNCTION has_rightop(name, name, name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_rightop(name, name, name, name) TO anon;
GRANT ALL ON FUNCTION public.has_rightop(name, name, name, name) TO authenticated;
GRANT ALL ON FUNCTION public.has_rightop(name, name, name, name) TO service_role;


--
-- Name: FUNCTION has_rightop(name, name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_rightop(name, name, name, text) TO anon;
GRANT ALL ON FUNCTION public.has_rightop(name, name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.has_rightop(name, name, name, text) TO service_role;


--
-- Name: FUNCTION has_rightop(name, name, name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_rightop(name, name, name, name, text) TO anon;
GRANT ALL ON FUNCTION public.has_rightop(name, name, name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.has_rightop(name, name, name, name, text) TO service_role;


--
-- Name: FUNCTION has_role(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_role(name) TO anon;
GRANT ALL ON FUNCTION public.has_role(name) TO authenticated;
GRANT ALL ON FUNCTION public.has_role(name) TO service_role;


--
-- Name: FUNCTION has_role(name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_role(name, text) TO anon;
GRANT ALL ON FUNCTION public.has_role(name, text) TO authenticated;
GRANT ALL ON FUNCTION public.has_role(name, text) TO service_role;


--
-- Name: FUNCTION has_rule(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_rule(name, name) TO anon;
GRANT ALL ON FUNCTION public.has_rule(name, name) TO authenticated;
GRANT ALL ON FUNCTION public.has_rule(name, name) TO service_role;


--
-- Name: FUNCTION has_rule(name, name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_rule(name, name, name) TO anon;
GRANT ALL ON FUNCTION public.has_rule(name, name, name) TO authenticated;
GRANT ALL ON FUNCTION public.has_rule(name, name, name) TO service_role;


--
-- Name: FUNCTION has_rule(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_rule(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.has_rule(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.has_rule(name, name, text) TO service_role;


--
-- Name: FUNCTION has_rule(name, name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_rule(name, name, name, text) TO anon;
GRANT ALL ON FUNCTION public.has_rule(name, name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.has_rule(name, name, name, text) TO service_role;


--
-- Name: FUNCTION has_schema(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_schema(name) TO anon;
GRANT ALL ON FUNCTION public.has_schema(name) TO authenticated;
GRANT ALL ON FUNCTION public.has_schema(name) TO service_role;


--
-- Name: FUNCTION has_schema(name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_schema(name, text) TO anon;
GRANT ALL ON FUNCTION public.has_schema(name, text) TO authenticated;
GRANT ALL ON FUNCTION public.has_schema(name, text) TO service_role;


--
-- Name: FUNCTION has_sequence(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_sequence(name) TO anon;
GRANT ALL ON FUNCTION public.has_sequence(name) TO authenticated;
GRANT ALL ON FUNCTION public.has_sequence(name) TO service_role;


--
-- Name: FUNCTION has_sequence(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_sequence(name, name) TO anon;
GRANT ALL ON FUNCTION public.has_sequence(name, name) TO authenticated;
GRANT ALL ON FUNCTION public.has_sequence(name, name) TO service_role;


--
-- Name: FUNCTION has_sequence(name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_sequence(name, text) TO anon;
GRANT ALL ON FUNCTION public.has_sequence(name, text) TO authenticated;
GRANT ALL ON FUNCTION public.has_sequence(name, text) TO service_role;


--
-- Name: FUNCTION has_sequence(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_sequence(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.has_sequence(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.has_sequence(name, name, text) TO service_role;


--
-- Name: FUNCTION has_table(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_table(name) TO anon;
GRANT ALL ON FUNCTION public.has_table(name) TO authenticated;
GRANT ALL ON FUNCTION public.has_table(name) TO service_role;


--
-- Name: FUNCTION has_table(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_table(name, name) TO anon;
GRANT ALL ON FUNCTION public.has_table(name, name) TO authenticated;
GRANT ALL ON FUNCTION public.has_table(name, name) TO service_role;


--
-- Name: FUNCTION has_table(name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_table(name, text) TO anon;
GRANT ALL ON FUNCTION public.has_table(name, text) TO authenticated;
GRANT ALL ON FUNCTION public.has_table(name, text) TO service_role;


--
-- Name: FUNCTION has_table(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_table(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.has_table(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.has_table(name, name, text) TO service_role;


--
-- Name: FUNCTION has_tablespace(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_tablespace(name) TO anon;
GRANT ALL ON FUNCTION public.has_tablespace(name) TO authenticated;
GRANT ALL ON FUNCTION public.has_tablespace(name) TO service_role;


--
-- Name: FUNCTION has_tablespace(name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_tablespace(name, text) TO anon;
GRANT ALL ON FUNCTION public.has_tablespace(name, text) TO authenticated;
GRANT ALL ON FUNCTION public.has_tablespace(name, text) TO service_role;


--
-- Name: FUNCTION has_tablespace(name, text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_tablespace(name, text, text) TO anon;
GRANT ALL ON FUNCTION public.has_tablespace(name, text, text) TO authenticated;
GRANT ALL ON FUNCTION public.has_tablespace(name, text, text) TO service_role;


--
-- Name: FUNCTION has_trigger(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_trigger(name, name) TO anon;
GRANT ALL ON FUNCTION public.has_trigger(name, name) TO authenticated;
GRANT ALL ON FUNCTION public.has_trigger(name, name) TO service_role;


--
-- Name: FUNCTION has_trigger(name, name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_trigger(name, name, name) TO anon;
GRANT ALL ON FUNCTION public.has_trigger(name, name, name) TO authenticated;
GRANT ALL ON FUNCTION public.has_trigger(name, name, name) TO service_role;


--
-- Name: FUNCTION has_trigger(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_trigger(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.has_trigger(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.has_trigger(name, name, text) TO service_role;


--
-- Name: FUNCTION has_trigger(name, name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_trigger(name, name, name, text) TO anon;
GRANT ALL ON FUNCTION public.has_trigger(name, name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.has_trigger(name, name, name, text) TO service_role;


--
-- Name: FUNCTION has_type(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_type(name) TO anon;
GRANT ALL ON FUNCTION public.has_type(name) TO authenticated;
GRANT ALL ON FUNCTION public.has_type(name) TO service_role;


--
-- Name: FUNCTION has_type(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_type(name, name) TO anon;
GRANT ALL ON FUNCTION public.has_type(name, name) TO authenticated;
GRANT ALL ON FUNCTION public.has_type(name, name) TO service_role;


--
-- Name: FUNCTION has_type(name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_type(name, text) TO anon;
GRANT ALL ON FUNCTION public.has_type(name, text) TO authenticated;
GRANT ALL ON FUNCTION public.has_type(name, text) TO service_role;


--
-- Name: FUNCTION has_type(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_type(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.has_type(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.has_type(name, name, text) TO service_role;


--
-- Name: FUNCTION has_unique(text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_unique(text) TO anon;
GRANT ALL ON FUNCTION public.has_unique(text) TO authenticated;
GRANT ALL ON FUNCTION public.has_unique(text) TO service_role;


--
-- Name: FUNCTION has_unique(text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_unique(text, text) TO anon;
GRANT ALL ON FUNCTION public.has_unique(text, text) TO authenticated;
GRANT ALL ON FUNCTION public.has_unique(text, text) TO service_role;


--
-- Name: FUNCTION has_unique(text, text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_unique(text, text, text) TO anon;
GRANT ALL ON FUNCTION public.has_unique(text, text, text) TO authenticated;
GRANT ALL ON FUNCTION public.has_unique(text, text, text) TO service_role;


--
-- Name: FUNCTION has_user(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_user(name) TO anon;
GRANT ALL ON FUNCTION public.has_user(name) TO authenticated;
GRANT ALL ON FUNCTION public.has_user(name) TO service_role;


--
-- Name: FUNCTION has_user(name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_user(name, text) TO anon;
GRANT ALL ON FUNCTION public.has_user(name, text) TO authenticated;
GRANT ALL ON FUNCTION public.has_user(name, text) TO service_role;


--
-- Name: FUNCTION has_view(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_view(name) TO anon;
GRANT ALL ON FUNCTION public.has_view(name) TO authenticated;
GRANT ALL ON FUNCTION public.has_view(name) TO service_role;


--
-- Name: FUNCTION has_view(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_view(name, name) TO anon;
GRANT ALL ON FUNCTION public.has_view(name, name) TO authenticated;
GRANT ALL ON FUNCTION public.has_view(name, name) TO service_role;


--
-- Name: FUNCTION has_view(name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_view(name, text) TO anon;
GRANT ALL ON FUNCTION public.has_view(name, text) TO authenticated;
GRANT ALL ON FUNCTION public.has_view(name, text) TO service_role;


--
-- Name: FUNCTION has_view(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.has_view(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.has_view(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.has_view(name, name, text) TO service_role;


--
-- Name: FUNCTION hasnt_cast(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_cast(name, name) TO anon;
GRANT ALL ON FUNCTION public.hasnt_cast(name, name) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_cast(name, name) TO service_role;


--
-- Name: FUNCTION hasnt_cast(name, name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_cast(name, name, name) TO anon;
GRANT ALL ON FUNCTION public.hasnt_cast(name, name, name) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_cast(name, name, name) TO service_role;


--
-- Name: FUNCTION hasnt_cast(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_cast(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.hasnt_cast(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_cast(name, name, text) TO service_role;


--
-- Name: FUNCTION hasnt_cast(name, name, name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_cast(name, name, name, name) TO anon;
GRANT ALL ON FUNCTION public.hasnt_cast(name, name, name, name) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_cast(name, name, name, name) TO service_role;


--
-- Name: FUNCTION hasnt_cast(name, name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_cast(name, name, name, text) TO anon;
GRANT ALL ON FUNCTION public.hasnt_cast(name, name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_cast(name, name, name, text) TO service_role;


--
-- Name: FUNCTION hasnt_cast(name, name, name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_cast(name, name, name, name, text) TO anon;
GRANT ALL ON FUNCTION public.hasnt_cast(name, name, name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_cast(name, name, name, name, text) TO service_role;


--
-- Name: FUNCTION hasnt_column(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_column(name, name) TO anon;
GRANT ALL ON FUNCTION public.hasnt_column(name, name) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_column(name, name) TO service_role;


--
-- Name: FUNCTION hasnt_column(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_column(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.hasnt_column(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_column(name, name, text) TO service_role;


--
-- Name: FUNCTION hasnt_column(name, name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_column(name, name, name, text) TO anon;
GRANT ALL ON FUNCTION public.hasnt_column(name, name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_column(name, name, name, text) TO service_role;


--
-- Name: FUNCTION hasnt_composite(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_composite(name) TO anon;
GRANT ALL ON FUNCTION public.hasnt_composite(name) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_composite(name) TO service_role;


--
-- Name: FUNCTION hasnt_composite(name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_composite(name, text) TO anon;
GRANT ALL ON FUNCTION public.hasnt_composite(name, text) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_composite(name, text) TO service_role;


--
-- Name: FUNCTION hasnt_composite(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_composite(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.hasnt_composite(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_composite(name, name, text) TO service_role;


--
-- Name: FUNCTION hasnt_domain(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_domain(name) TO anon;
GRANT ALL ON FUNCTION public.hasnt_domain(name) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_domain(name) TO service_role;


--
-- Name: FUNCTION hasnt_domain(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_domain(name, name) TO anon;
GRANT ALL ON FUNCTION public.hasnt_domain(name, name) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_domain(name, name) TO service_role;


--
-- Name: FUNCTION hasnt_domain(name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_domain(name, text) TO anon;
GRANT ALL ON FUNCTION public.hasnt_domain(name, text) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_domain(name, text) TO service_role;


--
-- Name: FUNCTION hasnt_domain(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_domain(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.hasnt_domain(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_domain(name, name, text) TO service_role;


--
-- Name: FUNCTION hasnt_enum(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_enum(name) TO anon;
GRANT ALL ON FUNCTION public.hasnt_enum(name) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_enum(name) TO service_role;


--
-- Name: FUNCTION hasnt_enum(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_enum(name, name) TO anon;
GRANT ALL ON FUNCTION public.hasnt_enum(name, name) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_enum(name, name) TO service_role;


--
-- Name: FUNCTION hasnt_enum(name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_enum(name, text) TO anon;
GRANT ALL ON FUNCTION public.hasnt_enum(name, text) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_enum(name, text) TO service_role;


--
-- Name: FUNCTION hasnt_enum(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_enum(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.hasnt_enum(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_enum(name, name, text) TO service_role;


--
-- Name: FUNCTION hasnt_extension(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_extension(name) TO anon;
GRANT ALL ON FUNCTION public.hasnt_extension(name) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_extension(name) TO service_role;


--
-- Name: FUNCTION hasnt_extension(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_extension(name, name) TO anon;
GRANT ALL ON FUNCTION public.hasnt_extension(name, name) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_extension(name, name) TO service_role;


--
-- Name: FUNCTION hasnt_extension(name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_extension(name, text) TO anon;
GRANT ALL ON FUNCTION public.hasnt_extension(name, text) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_extension(name, text) TO service_role;


--
-- Name: FUNCTION hasnt_extension(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_extension(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.hasnt_extension(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_extension(name, name, text) TO service_role;


--
-- Name: FUNCTION hasnt_fk(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_fk(name) TO anon;
GRANT ALL ON FUNCTION public.hasnt_fk(name) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_fk(name) TO service_role;


--
-- Name: FUNCTION hasnt_fk(name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_fk(name, text) TO anon;
GRANT ALL ON FUNCTION public.hasnt_fk(name, text) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_fk(name, text) TO service_role;


--
-- Name: FUNCTION hasnt_fk(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_fk(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.hasnt_fk(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_fk(name, name, text) TO service_role;


--
-- Name: FUNCTION hasnt_foreign_table(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_foreign_table(name) TO anon;
GRANT ALL ON FUNCTION public.hasnt_foreign_table(name) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_foreign_table(name) TO service_role;


--
-- Name: FUNCTION hasnt_foreign_table(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_foreign_table(name, name) TO anon;
GRANT ALL ON FUNCTION public.hasnt_foreign_table(name, name) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_foreign_table(name, name) TO service_role;


--
-- Name: FUNCTION hasnt_foreign_table(name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_foreign_table(name, text) TO anon;
GRANT ALL ON FUNCTION public.hasnt_foreign_table(name, text) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_foreign_table(name, text) TO service_role;


--
-- Name: FUNCTION hasnt_foreign_table(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_foreign_table(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.hasnt_foreign_table(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_foreign_table(name, name, text) TO service_role;


--
-- Name: FUNCTION hasnt_function(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_function(name) TO anon;
GRANT ALL ON FUNCTION public.hasnt_function(name) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_function(name) TO service_role;


--
-- Name: FUNCTION hasnt_function(name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_function(name, name[]) TO anon;
GRANT ALL ON FUNCTION public.hasnt_function(name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_function(name, name[]) TO service_role;


--
-- Name: FUNCTION hasnt_function(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_function(name, name) TO anon;
GRANT ALL ON FUNCTION public.hasnt_function(name, name) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_function(name, name) TO service_role;


--
-- Name: FUNCTION hasnt_function(name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_function(name, text) TO anon;
GRANT ALL ON FUNCTION public.hasnt_function(name, text) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_function(name, text) TO service_role;


--
-- Name: FUNCTION hasnt_function(name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_function(name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.hasnt_function(name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_function(name, name[], text) TO service_role;


--
-- Name: FUNCTION hasnt_function(name, name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_function(name, name, name[]) TO anon;
GRANT ALL ON FUNCTION public.hasnt_function(name, name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_function(name, name, name[]) TO service_role;


--
-- Name: FUNCTION hasnt_function(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_function(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.hasnt_function(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_function(name, name, text) TO service_role;


--
-- Name: FUNCTION hasnt_function(name, name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_function(name, name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.hasnt_function(name, name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_function(name, name, name[], text) TO service_role;


--
-- Name: FUNCTION hasnt_group(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_group(name) TO anon;
GRANT ALL ON FUNCTION public.hasnt_group(name) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_group(name) TO service_role;


--
-- Name: FUNCTION hasnt_group(name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_group(name, text) TO anon;
GRANT ALL ON FUNCTION public.hasnt_group(name, text) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_group(name, text) TO service_role;


--
-- Name: FUNCTION hasnt_index(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_index(name, name) TO anon;
GRANT ALL ON FUNCTION public.hasnt_index(name, name) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_index(name, name) TO service_role;


--
-- Name: FUNCTION hasnt_index(name, name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_index(name, name, name) TO anon;
GRANT ALL ON FUNCTION public.hasnt_index(name, name, name) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_index(name, name, name) TO service_role;


--
-- Name: FUNCTION hasnt_index(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_index(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.hasnt_index(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_index(name, name, text) TO service_role;


--
-- Name: FUNCTION hasnt_index(name, name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_index(name, name, name, text) TO anon;
GRANT ALL ON FUNCTION public.hasnt_index(name, name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_index(name, name, name, text) TO service_role;


--
-- Name: FUNCTION hasnt_inherited_tables(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_inherited_tables(name) TO anon;
GRANT ALL ON FUNCTION public.hasnt_inherited_tables(name) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_inherited_tables(name) TO service_role;


--
-- Name: FUNCTION hasnt_inherited_tables(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_inherited_tables(name, name) TO anon;
GRANT ALL ON FUNCTION public.hasnt_inherited_tables(name, name) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_inherited_tables(name, name) TO service_role;


--
-- Name: FUNCTION hasnt_inherited_tables(name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_inherited_tables(name, text) TO anon;
GRANT ALL ON FUNCTION public.hasnt_inherited_tables(name, text) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_inherited_tables(name, text) TO service_role;


--
-- Name: FUNCTION hasnt_inherited_tables(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_inherited_tables(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.hasnt_inherited_tables(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_inherited_tables(name, name, text) TO service_role;


--
-- Name: FUNCTION hasnt_language(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_language(name) TO anon;
GRANT ALL ON FUNCTION public.hasnt_language(name) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_language(name) TO service_role;


--
-- Name: FUNCTION hasnt_language(name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_language(name, text) TO anon;
GRANT ALL ON FUNCTION public.hasnt_language(name, text) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_language(name, text) TO service_role;


--
-- Name: FUNCTION hasnt_leftop(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_leftop(name, name) TO anon;
GRANT ALL ON FUNCTION public.hasnt_leftop(name, name) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_leftop(name, name) TO service_role;


--
-- Name: FUNCTION hasnt_leftop(name, name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_leftop(name, name, name) TO anon;
GRANT ALL ON FUNCTION public.hasnt_leftop(name, name, name) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_leftop(name, name, name) TO service_role;


--
-- Name: FUNCTION hasnt_leftop(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_leftop(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.hasnt_leftop(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_leftop(name, name, text) TO service_role;


--
-- Name: FUNCTION hasnt_leftop(name, name, name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_leftop(name, name, name, name) TO anon;
GRANT ALL ON FUNCTION public.hasnt_leftop(name, name, name, name) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_leftop(name, name, name, name) TO service_role;


--
-- Name: FUNCTION hasnt_leftop(name, name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_leftop(name, name, name, text) TO anon;
GRANT ALL ON FUNCTION public.hasnt_leftop(name, name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_leftop(name, name, name, text) TO service_role;


--
-- Name: FUNCTION hasnt_leftop(name, name, name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_leftop(name, name, name, name, text) TO anon;
GRANT ALL ON FUNCTION public.hasnt_leftop(name, name, name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_leftop(name, name, name, name, text) TO service_role;


--
-- Name: FUNCTION hasnt_materialized_view(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_materialized_view(name) TO anon;
GRANT ALL ON FUNCTION public.hasnt_materialized_view(name) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_materialized_view(name) TO service_role;


--
-- Name: FUNCTION hasnt_materialized_view(name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_materialized_view(name, text) TO anon;
GRANT ALL ON FUNCTION public.hasnt_materialized_view(name, text) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_materialized_view(name, text) TO service_role;


--
-- Name: FUNCTION hasnt_materialized_view(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_materialized_view(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.hasnt_materialized_view(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_materialized_view(name, name, text) TO service_role;


--
-- Name: FUNCTION hasnt_opclass(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_opclass(name) TO anon;
GRANT ALL ON FUNCTION public.hasnt_opclass(name) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_opclass(name) TO service_role;


--
-- Name: FUNCTION hasnt_opclass(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_opclass(name, name) TO anon;
GRANT ALL ON FUNCTION public.hasnt_opclass(name, name) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_opclass(name, name) TO service_role;


--
-- Name: FUNCTION hasnt_opclass(name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_opclass(name, text) TO anon;
GRANT ALL ON FUNCTION public.hasnt_opclass(name, text) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_opclass(name, text) TO service_role;


--
-- Name: FUNCTION hasnt_opclass(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_opclass(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.hasnt_opclass(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_opclass(name, name, text) TO service_role;


--
-- Name: FUNCTION hasnt_operator(name, name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_operator(name, name, name) TO anon;
GRANT ALL ON FUNCTION public.hasnt_operator(name, name, name) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_operator(name, name, name) TO service_role;


--
-- Name: FUNCTION hasnt_operator(name, name, name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_operator(name, name, name, name) TO anon;
GRANT ALL ON FUNCTION public.hasnt_operator(name, name, name, name) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_operator(name, name, name, name) TO service_role;


--
-- Name: FUNCTION hasnt_operator(name, name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_operator(name, name, name, text) TO anon;
GRANT ALL ON FUNCTION public.hasnt_operator(name, name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_operator(name, name, name, text) TO service_role;


--
-- Name: FUNCTION hasnt_operator(name, name, name, name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_operator(name, name, name, name, name) TO anon;
GRANT ALL ON FUNCTION public.hasnt_operator(name, name, name, name, name) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_operator(name, name, name, name, name) TO service_role;


--
-- Name: FUNCTION hasnt_operator(name, name, name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_operator(name, name, name, name, text) TO anon;
GRANT ALL ON FUNCTION public.hasnt_operator(name, name, name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_operator(name, name, name, name, text) TO service_role;


--
-- Name: FUNCTION hasnt_operator(name, name, name, name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_operator(name, name, name, name, name, text) TO anon;
GRANT ALL ON FUNCTION public.hasnt_operator(name, name, name, name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_operator(name, name, name, name, name, text) TO service_role;


--
-- Name: FUNCTION hasnt_pk(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_pk(name) TO anon;
GRANT ALL ON FUNCTION public.hasnt_pk(name) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_pk(name) TO service_role;


--
-- Name: FUNCTION hasnt_pk(name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_pk(name, text) TO anon;
GRANT ALL ON FUNCTION public.hasnt_pk(name, text) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_pk(name, text) TO service_role;


--
-- Name: FUNCTION hasnt_pk(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_pk(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.hasnt_pk(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_pk(name, name, text) TO service_role;


--
-- Name: FUNCTION hasnt_relation(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_relation(name) TO anon;
GRANT ALL ON FUNCTION public.hasnt_relation(name) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_relation(name) TO service_role;


--
-- Name: FUNCTION hasnt_relation(name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_relation(name, text) TO anon;
GRANT ALL ON FUNCTION public.hasnt_relation(name, text) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_relation(name, text) TO service_role;


--
-- Name: FUNCTION hasnt_relation(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_relation(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.hasnt_relation(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_relation(name, name, text) TO service_role;


--
-- Name: FUNCTION hasnt_rightop(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_rightop(name, name) TO anon;
GRANT ALL ON FUNCTION public.hasnt_rightop(name, name) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_rightop(name, name) TO service_role;


--
-- Name: FUNCTION hasnt_rightop(name, name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_rightop(name, name, name) TO anon;
GRANT ALL ON FUNCTION public.hasnt_rightop(name, name, name) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_rightop(name, name, name) TO service_role;


--
-- Name: FUNCTION hasnt_rightop(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_rightop(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.hasnt_rightop(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_rightop(name, name, text) TO service_role;


--
-- Name: FUNCTION hasnt_rightop(name, name, name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_rightop(name, name, name, name) TO anon;
GRANT ALL ON FUNCTION public.hasnt_rightop(name, name, name, name) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_rightop(name, name, name, name) TO service_role;


--
-- Name: FUNCTION hasnt_rightop(name, name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_rightop(name, name, name, text) TO anon;
GRANT ALL ON FUNCTION public.hasnt_rightop(name, name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_rightop(name, name, name, text) TO service_role;


--
-- Name: FUNCTION hasnt_rightop(name, name, name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_rightop(name, name, name, name, text) TO anon;
GRANT ALL ON FUNCTION public.hasnt_rightop(name, name, name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_rightop(name, name, name, name, text) TO service_role;


--
-- Name: FUNCTION hasnt_role(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_role(name) TO anon;
GRANT ALL ON FUNCTION public.hasnt_role(name) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_role(name) TO service_role;


--
-- Name: FUNCTION hasnt_role(name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_role(name, text) TO anon;
GRANT ALL ON FUNCTION public.hasnt_role(name, text) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_role(name, text) TO service_role;


--
-- Name: FUNCTION hasnt_rule(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_rule(name, name) TO anon;
GRANT ALL ON FUNCTION public.hasnt_rule(name, name) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_rule(name, name) TO service_role;


--
-- Name: FUNCTION hasnt_rule(name, name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_rule(name, name, name) TO anon;
GRANT ALL ON FUNCTION public.hasnt_rule(name, name, name) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_rule(name, name, name) TO service_role;


--
-- Name: FUNCTION hasnt_rule(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_rule(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.hasnt_rule(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_rule(name, name, text) TO service_role;


--
-- Name: FUNCTION hasnt_rule(name, name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_rule(name, name, name, text) TO anon;
GRANT ALL ON FUNCTION public.hasnt_rule(name, name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_rule(name, name, name, text) TO service_role;


--
-- Name: FUNCTION hasnt_schema(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_schema(name) TO anon;
GRANT ALL ON FUNCTION public.hasnt_schema(name) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_schema(name) TO service_role;


--
-- Name: FUNCTION hasnt_schema(name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_schema(name, text) TO anon;
GRANT ALL ON FUNCTION public.hasnt_schema(name, text) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_schema(name, text) TO service_role;


--
-- Name: FUNCTION hasnt_sequence(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_sequence(name) TO anon;
GRANT ALL ON FUNCTION public.hasnt_sequence(name) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_sequence(name) TO service_role;


--
-- Name: FUNCTION hasnt_sequence(name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_sequence(name, text) TO anon;
GRANT ALL ON FUNCTION public.hasnt_sequence(name, text) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_sequence(name, text) TO service_role;


--
-- Name: FUNCTION hasnt_sequence(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_sequence(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.hasnt_sequence(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_sequence(name, name, text) TO service_role;


--
-- Name: FUNCTION hasnt_table(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_table(name) TO anon;
GRANT ALL ON FUNCTION public.hasnt_table(name) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_table(name) TO service_role;


--
-- Name: FUNCTION hasnt_table(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_table(name, name) TO anon;
GRANT ALL ON FUNCTION public.hasnt_table(name, name) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_table(name, name) TO service_role;


--
-- Name: FUNCTION hasnt_table(name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_table(name, text) TO anon;
GRANT ALL ON FUNCTION public.hasnt_table(name, text) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_table(name, text) TO service_role;


--
-- Name: FUNCTION hasnt_table(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_table(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.hasnt_table(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_table(name, name, text) TO service_role;


--
-- Name: FUNCTION hasnt_tablespace(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_tablespace(name) TO anon;
GRANT ALL ON FUNCTION public.hasnt_tablespace(name) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_tablespace(name) TO service_role;


--
-- Name: FUNCTION hasnt_tablespace(name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_tablespace(name, text) TO anon;
GRANT ALL ON FUNCTION public.hasnt_tablespace(name, text) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_tablespace(name, text) TO service_role;


--
-- Name: FUNCTION hasnt_trigger(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_trigger(name, name) TO anon;
GRANT ALL ON FUNCTION public.hasnt_trigger(name, name) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_trigger(name, name) TO service_role;


--
-- Name: FUNCTION hasnt_trigger(name, name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_trigger(name, name, name) TO anon;
GRANT ALL ON FUNCTION public.hasnt_trigger(name, name, name) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_trigger(name, name, name) TO service_role;


--
-- Name: FUNCTION hasnt_trigger(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_trigger(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.hasnt_trigger(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_trigger(name, name, text) TO service_role;


--
-- Name: FUNCTION hasnt_trigger(name, name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_trigger(name, name, name, text) TO anon;
GRANT ALL ON FUNCTION public.hasnt_trigger(name, name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_trigger(name, name, name, text) TO service_role;


--
-- Name: FUNCTION hasnt_type(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_type(name) TO anon;
GRANT ALL ON FUNCTION public.hasnt_type(name) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_type(name) TO service_role;


--
-- Name: FUNCTION hasnt_type(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_type(name, name) TO anon;
GRANT ALL ON FUNCTION public.hasnt_type(name, name) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_type(name, name) TO service_role;


--
-- Name: FUNCTION hasnt_type(name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_type(name, text) TO anon;
GRANT ALL ON FUNCTION public.hasnt_type(name, text) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_type(name, text) TO service_role;


--
-- Name: FUNCTION hasnt_type(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_type(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.hasnt_type(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_type(name, name, text) TO service_role;


--
-- Name: FUNCTION hasnt_user(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_user(name) TO anon;
GRANT ALL ON FUNCTION public.hasnt_user(name) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_user(name) TO service_role;


--
-- Name: FUNCTION hasnt_user(name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_user(name, text) TO anon;
GRANT ALL ON FUNCTION public.hasnt_user(name, text) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_user(name, text) TO service_role;


--
-- Name: FUNCTION hasnt_view(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_view(name) TO anon;
GRANT ALL ON FUNCTION public.hasnt_view(name) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_view(name) TO service_role;


--
-- Name: FUNCTION hasnt_view(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_view(name, name) TO anon;
GRANT ALL ON FUNCTION public.hasnt_view(name, name) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_view(name, name) TO service_role;


--
-- Name: FUNCTION hasnt_view(name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_view(name, text) TO anon;
GRANT ALL ON FUNCTION public.hasnt_view(name, text) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_view(name, text) TO service_role;


--
-- Name: FUNCTION hasnt_view(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hasnt_view(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.hasnt_view(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.hasnt_view(name, name, text) TO service_role;


--
-- Name: FUNCTION hmac(bytea, bytea, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hmac(bytea, bytea, text) TO anon;
GRANT ALL ON FUNCTION public.hmac(bytea, bytea, text) TO authenticated;
GRANT ALL ON FUNCTION public.hmac(bytea, bytea, text) TO service_role;


--
-- Name: FUNCTION hmac(text, text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.hmac(text, text, text) TO anon;
GRANT ALL ON FUNCTION public.hmac(text, text, text) TO authenticated;
GRANT ALL ON FUNCTION public.hmac(text, text, text) TO service_role;


--
-- Name: FUNCTION ialike(anyelement, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.ialike(anyelement, text) TO anon;
GRANT ALL ON FUNCTION public.ialike(anyelement, text) TO authenticated;
GRANT ALL ON FUNCTION public.ialike(anyelement, text) TO service_role;


--
-- Name: FUNCTION ialike(anyelement, text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.ialike(anyelement, text, text) TO anon;
GRANT ALL ON FUNCTION public.ialike(anyelement, text, text) TO authenticated;
GRANT ALL ON FUNCTION public.ialike(anyelement, text, text) TO service_role;


--
-- Name: FUNCTION imatches(anyelement, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.imatches(anyelement, text) TO anon;
GRANT ALL ON FUNCTION public.imatches(anyelement, text) TO authenticated;
GRANT ALL ON FUNCTION public.imatches(anyelement, text) TO service_role;


--
-- Name: FUNCTION imatches(anyelement, text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.imatches(anyelement, text, text) TO anon;
GRANT ALL ON FUNCTION public.imatches(anyelement, text, text) TO authenticated;
GRANT ALL ON FUNCTION public.imatches(anyelement, text, text) TO service_role;


--
-- Name: FUNCTION in_todo(); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.in_todo() TO anon;
GRANT ALL ON FUNCTION public.in_todo() TO authenticated;
GRANT ALL ON FUNCTION public.in_todo() TO service_role;


--
-- Name: FUNCTION index_is_primary(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.index_is_primary(name) TO anon;
GRANT ALL ON FUNCTION public.index_is_primary(name) TO authenticated;
GRANT ALL ON FUNCTION public.index_is_primary(name) TO service_role;


--
-- Name: FUNCTION index_is_primary(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.index_is_primary(name, name) TO anon;
GRANT ALL ON FUNCTION public.index_is_primary(name, name) TO authenticated;
GRANT ALL ON FUNCTION public.index_is_primary(name, name) TO service_role;


--
-- Name: FUNCTION index_is_primary(name, name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.index_is_primary(name, name, name) TO anon;
GRANT ALL ON FUNCTION public.index_is_primary(name, name, name) TO authenticated;
GRANT ALL ON FUNCTION public.index_is_primary(name, name, name) TO service_role;


--
-- Name: FUNCTION index_is_primary(name, name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.index_is_primary(name, name, name, text) TO anon;
GRANT ALL ON FUNCTION public.index_is_primary(name, name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.index_is_primary(name, name, name, text) TO service_role;


--
-- Name: FUNCTION index_is_type(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.index_is_type(name, name) TO anon;
GRANT ALL ON FUNCTION public.index_is_type(name, name) TO authenticated;
GRANT ALL ON FUNCTION public.index_is_type(name, name) TO service_role;


--
-- Name: FUNCTION index_is_type(name, name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.index_is_type(name, name, name) TO anon;
GRANT ALL ON FUNCTION public.index_is_type(name, name, name) TO authenticated;
GRANT ALL ON FUNCTION public.index_is_type(name, name, name) TO service_role;


--
-- Name: FUNCTION index_is_type(name, name, name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.index_is_type(name, name, name, name) TO anon;
GRANT ALL ON FUNCTION public.index_is_type(name, name, name, name) TO authenticated;
GRANT ALL ON FUNCTION public.index_is_type(name, name, name, name) TO service_role;


--
-- Name: FUNCTION index_is_type(name, name, name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.index_is_type(name, name, name, name, text) TO anon;
GRANT ALL ON FUNCTION public.index_is_type(name, name, name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.index_is_type(name, name, name, name, text) TO service_role;


--
-- Name: FUNCTION index_is_unique(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.index_is_unique(name) TO anon;
GRANT ALL ON FUNCTION public.index_is_unique(name) TO authenticated;
GRANT ALL ON FUNCTION public.index_is_unique(name) TO service_role;


--
-- Name: FUNCTION index_is_unique(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.index_is_unique(name, name) TO anon;
GRANT ALL ON FUNCTION public.index_is_unique(name, name) TO authenticated;
GRANT ALL ON FUNCTION public.index_is_unique(name, name) TO service_role;


--
-- Name: FUNCTION index_is_unique(name, name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.index_is_unique(name, name, name) TO anon;
GRANT ALL ON FUNCTION public.index_is_unique(name, name, name) TO authenticated;
GRANT ALL ON FUNCTION public.index_is_unique(name, name, name) TO service_role;


--
-- Name: FUNCTION index_is_unique(name, name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.index_is_unique(name, name, name, text) TO anon;
GRANT ALL ON FUNCTION public.index_is_unique(name, name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.index_is_unique(name, name, name, text) TO service_role;


--
-- Name: FUNCTION index_owner_is(name, name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.index_owner_is(name, name, name) TO anon;
GRANT ALL ON FUNCTION public.index_owner_is(name, name, name) TO authenticated;
GRANT ALL ON FUNCTION public.index_owner_is(name, name, name) TO service_role;


--
-- Name: FUNCTION index_owner_is(name, name, name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.index_owner_is(name, name, name, name) TO anon;
GRANT ALL ON FUNCTION public.index_owner_is(name, name, name, name) TO authenticated;
GRANT ALL ON FUNCTION public.index_owner_is(name, name, name, name) TO service_role;


--
-- Name: FUNCTION index_owner_is(name, name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.index_owner_is(name, name, name, text) TO anon;
GRANT ALL ON FUNCTION public.index_owner_is(name, name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.index_owner_is(name, name, name, text) TO service_role;


--
-- Name: FUNCTION index_owner_is(name, name, name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.index_owner_is(name, name, name, name, text) TO anon;
GRANT ALL ON FUNCTION public.index_owner_is(name, name, name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.index_owner_is(name, name, name, name, text) TO service_role;


--
-- Name: FUNCTION indexes_are(name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.indexes_are(name, name[]) TO anon;
GRANT ALL ON FUNCTION public.indexes_are(name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public.indexes_are(name, name[]) TO service_role;


--
-- Name: FUNCTION indexes_are(name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.indexes_are(name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.indexes_are(name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.indexes_are(name, name[], text) TO service_role;


--
-- Name: FUNCTION indexes_are(name, name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.indexes_are(name, name, name[]) TO anon;
GRANT ALL ON FUNCTION public.indexes_are(name, name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public.indexes_are(name, name, name[]) TO service_role;


--
-- Name: FUNCTION indexes_are(name, name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.indexes_are(name, name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.indexes_are(name, name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.indexes_are(name, name, name[], text) TO service_role;


--
-- Name: FUNCTION "is"(anyelement, anyelement); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public."is"(anyelement, anyelement) TO anon;
GRANT ALL ON FUNCTION public."is"(anyelement, anyelement) TO authenticated;
GRANT ALL ON FUNCTION public."is"(anyelement, anyelement) TO service_role;


--
-- Name: FUNCTION "is"(anyelement, anyelement, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public."is"(anyelement, anyelement, text) TO anon;
GRANT ALL ON FUNCTION public."is"(anyelement, anyelement, text) TO authenticated;
GRANT ALL ON FUNCTION public."is"(anyelement, anyelement, text) TO service_role;


--
-- Name: FUNCTION is_aggregate(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_aggregate(name) TO anon;
GRANT ALL ON FUNCTION public.is_aggregate(name) TO authenticated;
GRANT ALL ON FUNCTION public.is_aggregate(name) TO service_role;


--
-- Name: FUNCTION is_aggregate(name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_aggregate(name, name[]) TO anon;
GRANT ALL ON FUNCTION public.is_aggregate(name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public.is_aggregate(name, name[]) TO service_role;


--
-- Name: FUNCTION is_aggregate(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_aggregate(name, name) TO anon;
GRANT ALL ON FUNCTION public.is_aggregate(name, name) TO authenticated;
GRANT ALL ON FUNCTION public.is_aggregate(name, name) TO service_role;


--
-- Name: FUNCTION is_aggregate(name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_aggregate(name, text) TO anon;
GRANT ALL ON FUNCTION public.is_aggregate(name, text) TO authenticated;
GRANT ALL ON FUNCTION public.is_aggregate(name, text) TO service_role;


--
-- Name: FUNCTION is_aggregate(name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_aggregate(name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.is_aggregate(name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.is_aggregate(name, name[], text) TO service_role;


--
-- Name: FUNCTION is_aggregate(name, name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_aggregate(name, name, name[]) TO anon;
GRANT ALL ON FUNCTION public.is_aggregate(name, name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public.is_aggregate(name, name, name[]) TO service_role;


--
-- Name: FUNCTION is_aggregate(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_aggregate(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.is_aggregate(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.is_aggregate(name, name, text) TO service_role;


--
-- Name: FUNCTION is_aggregate(name, name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_aggregate(name, name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.is_aggregate(name, name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.is_aggregate(name, name, name[], text) TO service_role;


--
-- Name: FUNCTION is_ancestor_of(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_ancestor_of(name, name) TO anon;
GRANT ALL ON FUNCTION public.is_ancestor_of(name, name) TO authenticated;
GRANT ALL ON FUNCTION public.is_ancestor_of(name, name) TO service_role;


--
-- Name: FUNCTION is_ancestor_of(name, name, integer); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_ancestor_of(name, name, integer) TO anon;
GRANT ALL ON FUNCTION public.is_ancestor_of(name, name, integer) TO authenticated;
GRANT ALL ON FUNCTION public.is_ancestor_of(name, name, integer) TO service_role;


--
-- Name: FUNCTION is_ancestor_of(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_ancestor_of(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.is_ancestor_of(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.is_ancestor_of(name, name, text) TO service_role;


--
-- Name: FUNCTION is_ancestor_of(name, name, integer, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_ancestor_of(name, name, integer, text) TO anon;
GRANT ALL ON FUNCTION public.is_ancestor_of(name, name, integer, text) TO authenticated;
GRANT ALL ON FUNCTION public.is_ancestor_of(name, name, integer, text) TO service_role;


--
-- Name: FUNCTION is_ancestor_of(name, name, name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_ancestor_of(name, name, name, name) TO anon;
GRANT ALL ON FUNCTION public.is_ancestor_of(name, name, name, name) TO authenticated;
GRANT ALL ON FUNCTION public.is_ancestor_of(name, name, name, name) TO service_role;


--
-- Name: FUNCTION is_ancestor_of(name, name, name, name, integer); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_ancestor_of(name, name, name, name, integer) TO anon;
GRANT ALL ON FUNCTION public.is_ancestor_of(name, name, name, name, integer) TO authenticated;
GRANT ALL ON FUNCTION public.is_ancestor_of(name, name, name, name, integer) TO service_role;


--
-- Name: FUNCTION is_ancestor_of(name, name, name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_ancestor_of(name, name, name, name, text) TO anon;
GRANT ALL ON FUNCTION public.is_ancestor_of(name, name, name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.is_ancestor_of(name, name, name, name, text) TO service_role;


--
-- Name: FUNCTION is_ancestor_of(name, name, name, name, integer, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_ancestor_of(name, name, name, name, integer, text) TO anon;
GRANT ALL ON FUNCTION public.is_ancestor_of(name, name, name, name, integer, text) TO authenticated;
GRANT ALL ON FUNCTION public.is_ancestor_of(name, name, name, name, integer, text) TO service_role;


--
-- Name: FUNCTION is_clustered(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_clustered(name) TO anon;
GRANT ALL ON FUNCTION public.is_clustered(name) TO authenticated;
GRANT ALL ON FUNCTION public.is_clustered(name) TO service_role;


--
-- Name: FUNCTION is_clustered(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_clustered(name, name) TO anon;
GRANT ALL ON FUNCTION public.is_clustered(name, name) TO authenticated;
GRANT ALL ON FUNCTION public.is_clustered(name, name) TO service_role;


--
-- Name: FUNCTION is_clustered(name, name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_clustered(name, name, name) TO anon;
GRANT ALL ON FUNCTION public.is_clustered(name, name, name) TO authenticated;
GRANT ALL ON FUNCTION public.is_clustered(name, name, name) TO service_role;


--
-- Name: FUNCTION is_clustered(name, name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_clustered(name, name, name, text) TO anon;
GRANT ALL ON FUNCTION public.is_clustered(name, name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.is_clustered(name, name, name, text) TO service_role;


--
-- Name: FUNCTION is_definer(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_definer(name) TO anon;
GRANT ALL ON FUNCTION public.is_definer(name) TO authenticated;
GRANT ALL ON FUNCTION public.is_definer(name) TO service_role;


--
-- Name: FUNCTION is_definer(name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_definer(name, name[]) TO anon;
GRANT ALL ON FUNCTION public.is_definer(name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public.is_definer(name, name[]) TO service_role;


--
-- Name: FUNCTION is_definer(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_definer(name, name) TO anon;
GRANT ALL ON FUNCTION public.is_definer(name, name) TO authenticated;
GRANT ALL ON FUNCTION public.is_definer(name, name) TO service_role;


--
-- Name: FUNCTION is_definer(name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_definer(name, text) TO anon;
GRANT ALL ON FUNCTION public.is_definer(name, text) TO authenticated;
GRANT ALL ON FUNCTION public.is_definer(name, text) TO service_role;


--
-- Name: FUNCTION is_definer(name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_definer(name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.is_definer(name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.is_definer(name, name[], text) TO service_role;


--
-- Name: FUNCTION is_definer(name, name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_definer(name, name, name[]) TO anon;
GRANT ALL ON FUNCTION public.is_definer(name, name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public.is_definer(name, name, name[]) TO service_role;


--
-- Name: FUNCTION is_definer(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_definer(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.is_definer(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.is_definer(name, name, text) TO service_role;


--
-- Name: FUNCTION is_definer(name, name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_definer(name, name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.is_definer(name, name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.is_definer(name, name, name[], text) TO service_role;


--
-- Name: FUNCTION is_descendent_of(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_descendent_of(name, name) TO anon;
GRANT ALL ON FUNCTION public.is_descendent_of(name, name) TO authenticated;
GRANT ALL ON FUNCTION public.is_descendent_of(name, name) TO service_role;


--
-- Name: FUNCTION is_descendent_of(name, name, integer); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_descendent_of(name, name, integer) TO anon;
GRANT ALL ON FUNCTION public.is_descendent_of(name, name, integer) TO authenticated;
GRANT ALL ON FUNCTION public.is_descendent_of(name, name, integer) TO service_role;


--
-- Name: FUNCTION is_descendent_of(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_descendent_of(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.is_descendent_of(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.is_descendent_of(name, name, text) TO service_role;


--
-- Name: FUNCTION is_descendent_of(name, name, integer, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_descendent_of(name, name, integer, text) TO anon;
GRANT ALL ON FUNCTION public.is_descendent_of(name, name, integer, text) TO authenticated;
GRANT ALL ON FUNCTION public.is_descendent_of(name, name, integer, text) TO service_role;


--
-- Name: FUNCTION is_descendent_of(name, name, name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_descendent_of(name, name, name, name) TO anon;
GRANT ALL ON FUNCTION public.is_descendent_of(name, name, name, name) TO authenticated;
GRANT ALL ON FUNCTION public.is_descendent_of(name, name, name, name) TO service_role;


--
-- Name: FUNCTION is_descendent_of(name, name, name, name, integer); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_descendent_of(name, name, name, name, integer) TO anon;
GRANT ALL ON FUNCTION public.is_descendent_of(name, name, name, name, integer) TO authenticated;
GRANT ALL ON FUNCTION public.is_descendent_of(name, name, name, name, integer) TO service_role;


--
-- Name: FUNCTION is_descendent_of(name, name, name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_descendent_of(name, name, name, name, text) TO anon;
GRANT ALL ON FUNCTION public.is_descendent_of(name, name, name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.is_descendent_of(name, name, name, name, text) TO service_role;


--
-- Name: FUNCTION is_descendent_of(name, name, name, name, integer, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_descendent_of(name, name, name, name, integer, text) TO anon;
GRANT ALL ON FUNCTION public.is_descendent_of(name, name, name, name, integer, text) TO authenticated;
GRANT ALL ON FUNCTION public.is_descendent_of(name, name, name, name, integer, text) TO service_role;


--
-- Name: FUNCTION is_empty(text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_empty(text) TO anon;
GRANT ALL ON FUNCTION public.is_empty(text) TO authenticated;
GRANT ALL ON FUNCTION public.is_empty(text) TO service_role;


--
-- Name: FUNCTION is_empty(text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_empty(text, text) TO anon;
GRANT ALL ON FUNCTION public.is_empty(text, text) TO authenticated;
GRANT ALL ON FUNCTION public.is_empty(text, text) TO service_role;


--
-- Name: FUNCTION is_indexed(name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_indexed(name, name[]) TO anon;
GRANT ALL ON FUNCTION public.is_indexed(name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public.is_indexed(name, name[]) TO service_role;


--
-- Name: FUNCTION is_indexed(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_indexed(name, name) TO anon;
GRANT ALL ON FUNCTION public.is_indexed(name, name) TO authenticated;
GRANT ALL ON FUNCTION public.is_indexed(name, name) TO service_role;


--
-- Name: FUNCTION is_indexed(name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_indexed(name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.is_indexed(name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.is_indexed(name, name[], text) TO service_role;


--
-- Name: FUNCTION is_indexed(name, name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_indexed(name, name, name[]) TO anon;
GRANT ALL ON FUNCTION public.is_indexed(name, name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public.is_indexed(name, name, name[]) TO service_role;


--
-- Name: FUNCTION is_indexed(name, name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_indexed(name, name, name) TO anon;
GRANT ALL ON FUNCTION public.is_indexed(name, name, name) TO authenticated;
GRANT ALL ON FUNCTION public.is_indexed(name, name, name) TO service_role;


--
-- Name: FUNCTION is_indexed(name, name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_indexed(name, name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.is_indexed(name, name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.is_indexed(name, name, name[], text) TO service_role;


--
-- Name: FUNCTION is_indexed(name, name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_indexed(name, name, name, text) TO anon;
GRANT ALL ON FUNCTION public.is_indexed(name, name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.is_indexed(name, name, name, text) TO service_role;


--
-- Name: FUNCTION is_member_of(name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_member_of(name, name[]) TO anon;
GRANT ALL ON FUNCTION public.is_member_of(name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public.is_member_of(name, name[]) TO service_role;


--
-- Name: FUNCTION is_member_of(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_member_of(name, name) TO anon;
GRANT ALL ON FUNCTION public.is_member_of(name, name) TO authenticated;
GRANT ALL ON FUNCTION public.is_member_of(name, name) TO service_role;


--
-- Name: FUNCTION is_member_of(name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_member_of(name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.is_member_of(name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.is_member_of(name, name[], text) TO service_role;


--
-- Name: FUNCTION is_member_of(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_member_of(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.is_member_of(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.is_member_of(name, name, text) TO service_role;


--
-- Name: FUNCTION is_normal_function(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_normal_function(name) TO anon;
GRANT ALL ON FUNCTION public.is_normal_function(name) TO authenticated;
GRANT ALL ON FUNCTION public.is_normal_function(name) TO service_role;


--
-- Name: FUNCTION is_normal_function(name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_normal_function(name, name[]) TO anon;
GRANT ALL ON FUNCTION public.is_normal_function(name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public.is_normal_function(name, name[]) TO service_role;


--
-- Name: FUNCTION is_normal_function(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_normal_function(name, name) TO anon;
GRANT ALL ON FUNCTION public.is_normal_function(name, name) TO authenticated;
GRANT ALL ON FUNCTION public.is_normal_function(name, name) TO service_role;


--
-- Name: FUNCTION is_normal_function(name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_normal_function(name, text) TO anon;
GRANT ALL ON FUNCTION public.is_normal_function(name, text) TO authenticated;
GRANT ALL ON FUNCTION public.is_normal_function(name, text) TO service_role;


--
-- Name: FUNCTION is_normal_function(name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_normal_function(name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.is_normal_function(name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.is_normal_function(name, name[], text) TO service_role;


--
-- Name: FUNCTION is_normal_function(name, name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_normal_function(name, name, name[]) TO anon;
GRANT ALL ON FUNCTION public.is_normal_function(name, name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public.is_normal_function(name, name, name[]) TO service_role;


--
-- Name: FUNCTION is_normal_function(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_normal_function(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.is_normal_function(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.is_normal_function(name, name, text) TO service_role;


--
-- Name: FUNCTION is_normal_function(name, name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_normal_function(name, name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.is_normal_function(name, name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.is_normal_function(name, name, name[], text) TO service_role;


--
-- Name: FUNCTION is_partition_of(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_partition_of(name, name) TO anon;
GRANT ALL ON FUNCTION public.is_partition_of(name, name) TO authenticated;
GRANT ALL ON FUNCTION public.is_partition_of(name, name) TO service_role;


--
-- Name: FUNCTION is_partition_of(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_partition_of(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.is_partition_of(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.is_partition_of(name, name, text) TO service_role;


--
-- Name: FUNCTION is_partition_of(name, name, name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_partition_of(name, name, name, name) TO anon;
GRANT ALL ON FUNCTION public.is_partition_of(name, name, name, name) TO authenticated;
GRANT ALL ON FUNCTION public.is_partition_of(name, name, name, name) TO service_role;


--
-- Name: FUNCTION is_partition_of(name, name, name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_partition_of(name, name, name, name, text) TO anon;
GRANT ALL ON FUNCTION public.is_partition_of(name, name, name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.is_partition_of(name, name, name, name, text) TO service_role;


--
-- Name: FUNCTION is_partitioned(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_partitioned(name) TO anon;
GRANT ALL ON FUNCTION public.is_partitioned(name) TO authenticated;
GRANT ALL ON FUNCTION public.is_partitioned(name) TO service_role;


--
-- Name: FUNCTION is_partitioned(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_partitioned(name, name) TO anon;
GRANT ALL ON FUNCTION public.is_partitioned(name, name) TO authenticated;
GRANT ALL ON FUNCTION public.is_partitioned(name, name) TO service_role;


--
-- Name: FUNCTION is_partitioned(name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_partitioned(name, text) TO anon;
GRANT ALL ON FUNCTION public.is_partitioned(name, text) TO authenticated;
GRANT ALL ON FUNCTION public.is_partitioned(name, text) TO service_role;


--
-- Name: FUNCTION is_partitioned(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_partitioned(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.is_partitioned(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.is_partitioned(name, name, text) TO service_role;


--
-- Name: FUNCTION is_procedure(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_procedure(name) TO anon;
GRANT ALL ON FUNCTION public.is_procedure(name) TO authenticated;
GRANT ALL ON FUNCTION public.is_procedure(name) TO service_role;


--
-- Name: FUNCTION is_procedure(name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_procedure(name, name[]) TO anon;
GRANT ALL ON FUNCTION public.is_procedure(name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public.is_procedure(name, name[]) TO service_role;


--
-- Name: FUNCTION is_procedure(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_procedure(name, name) TO anon;
GRANT ALL ON FUNCTION public.is_procedure(name, name) TO authenticated;
GRANT ALL ON FUNCTION public.is_procedure(name, name) TO service_role;


--
-- Name: FUNCTION is_procedure(name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_procedure(name, text) TO anon;
GRANT ALL ON FUNCTION public.is_procedure(name, text) TO authenticated;
GRANT ALL ON FUNCTION public.is_procedure(name, text) TO service_role;


--
-- Name: FUNCTION is_procedure(name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_procedure(name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.is_procedure(name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.is_procedure(name, name[], text) TO service_role;


--
-- Name: FUNCTION is_procedure(name, name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_procedure(name, name, name[]) TO anon;
GRANT ALL ON FUNCTION public.is_procedure(name, name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public.is_procedure(name, name, name[]) TO service_role;


--
-- Name: FUNCTION is_procedure(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_procedure(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.is_procedure(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.is_procedure(name, name, text) TO service_role;


--
-- Name: FUNCTION is_procedure(name, name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_procedure(name, name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.is_procedure(name, name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.is_procedure(name, name, name[], text) TO service_role;


--
-- Name: FUNCTION is_strict(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_strict(name) TO anon;
GRANT ALL ON FUNCTION public.is_strict(name) TO authenticated;
GRANT ALL ON FUNCTION public.is_strict(name) TO service_role;


--
-- Name: FUNCTION is_strict(name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_strict(name, name[]) TO anon;
GRANT ALL ON FUNCTION public.is_strict(name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public.is_strict(name, name[]) TO service_role;


--
-- Name: FUNCTION is_strict(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_strict(name, name) TO anon;
GRANT ALL ON FUNCTION public.is_strict(name, name) TO authenticated;
GRANT ALL ON FUNCTION public.is_strict(name, name) TO service_role;


--
-- Name: FUNCTION is_strict(name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_strict(name, text) TO anon;
GRANT ALL ON FUNCTION public.is_strict(name, text) TO authenticated;
GRANT ALL ON FUNCTION public.is_strict(name, text) TO service_role;


--
-- Name: FUNCTION is_strict(name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_strict(name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.is_strict(name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.is_strict(name, name[], text) TO service_role;


--
-- Name: FUNCTION is_strict(name, name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_strict(name, name, name[]) TO anon;
GRANT ALL ON FUNCTION public.is_strict(name, name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public.is_strict(name, name, name[]) TO service_role;


--
-- Name: FUNCTION is_strict(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_strict(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.is_strict(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.is_strict(name, name, text) TO service_role;


--
-- Name: FUNCTION is_strict(name, name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_strict(name, name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.is_strict(name, name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.is_strict(name, name, name[], text) TO service_role;


--
-- Name: FUNCTION is_superuser(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_superuser(name) TO anon;
GRANT ALL ON FUNCTION public.is_superuser(name) TO authenticated;
GRANT ALL ON FUNCTION public.is_superuser(name) TO service_role;


--
-- Name: FUNCTION is_superuser(name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_superuser(name, text) TO anon;
GRANT ALL ON FUNCTION public.is_superuser(name, text) TO authenticated;
GRANT ALL ON FUNCTION public.is_superuser(name, text) TO service_role;


--
-- Name: FUNCTION is_teacher_of_course(p_course_id uuid); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_teacher_of_course(p_course_id uuid) TO anon;
GRANT ALL ON FUNCTION public.is_teacher_of_course(p_course_id uuid) TO authenticated;
GRANT ALL ON FUNCTION public.is_teacher_of_course(p_course_id uuid) TO service_role;


--
-- Name: FUNCTION is_teacher_of_student(p_student_id uuid); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_teacher_of_student(p_student_id uuid) TO anon;
GRANT ALL ON FUNCTION public.is_teacher_of_student(p_student_id uuid) TO authenticated;
GRANT ALL ON FUNCTION public.is_teacher_of_student(p_student_id uuid) TO service_role;


--
-- Name: FUNCTION is_window(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_window(name) TO anon;
GRANT ALL ON FUNCTION public.is_window(name) TO authenticated;
GRANT ALL ON FUNCTION public.is_window(name) TO service_role;


--
-- Name: FUNCTION is_window(name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_window(name, name[]) TO anon;
GRANT ALL ON FUNCTION public.is_window(name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public.is_window(name, name[]) TO service_role;


--
-- Name: FUNCTION is_window(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_window(name, name) TO anon;
GRANT ALL ON FUNCTION public.is_window(name, name) TO authenticated;
GRANT ALL ON FUNCTION public.is_window(name, name) TO service_role;


--
-- Name: FUNCTION is_window(name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_window(name, text) TO anon;
GRANT ALL ON FUNCTION public.is_window(name, text) TO authenticated;
GRANT ALL ON FUNCTION public.is_window(name, text) TO service_role;


--
-- Name: FUNCTION is_window(name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_window(name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.is_window(name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.is_window(name, name[], text) TO service_role;


--
-- Name: FUNCTION is_window(name, name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_window(name, name, name[]) TO anon;
GRANT ALL ON FUNCTION public.is_window(name, name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public.is_window(name, name, name[]) TO service_role;


--
-- Name: FUNCTION is_window(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_window(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.is_window(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.is_window(name, name, text) TO service_role;


--
-- Name: FUNCTION is_window(name, name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.is_window(name, name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.is_window(name, name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.is_window(name, name, name[], text) TO service_role;


--
-- Name: FUNCTION isa_ok(anyelement, regtype); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.isa_ok(anyelement, regtype) TO anon;
GRANT ALL ON FUNCTION public.isa_ok(anyelement, regtype) TO authenticated;
GRANT ALL ON FUNCTION public.isa_ok(anyelement, regtype) TO service_role;


--
-- Name: FUNCTION isa_ok(anyelement, regtype, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.isa_ok(anyelement, regtype, text) TO anon;
GRANT ALL ON FUNCTION public.isa_ok(anyelement, regtype, text) TO authenticated;
GRANT ALL ON FUNCTION public.isa_ok(anyelement, regtype, text) TO service_role;


--
-- Name: FUNCTION isnt(anyelement, anyelement); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.isnt(anyelement, anyelement) TO anon;
GRANT ALL ON FUNCTION public.isnt(anyelement, anyelement) TO authenticated;
GRANT ALL ON FUNCTION public.isnt(anyelement, anyelement) TO service_role;


--
-- Name: FUNCTION isnt(anyelement, anyelement, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.isnt(anyelement, anyelement, text) TO anon;
GRANT ALL ON FUNCTION public.isnt(anyelement, anyelement, text) TO authenticated;
GRANT ALL ON FUNCTION public.isnt(anyelement, anyelement, text) TO service_role;


--
-- Name: FUNCTION isnt_aggregate(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.isnt_aggregate(name) TO anon;
GRANT ALL ON FUNCTION public.isnt_aggregate(name) TO authenticated;
GRANT ALL ON FUNCTION public.isnt_aggregate(name) TO service_role;


--
-- Name: FUNCTION isnt_aggregate(name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.isnt_aggregate(name, name[]) TO anon;
GRANT ALL ON FUNCTION public.isnt_aggregate(name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public.isnt_aggregate(name, name[]) TO service_role;


--
-- Name: FUNCTION isnt_aggregate(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.isnt_aggregate(name, name) TO anon;
GRANT ALL ON FUNCTION public.isnt_aggregate(name, name) TO authenticated;
GRANT ALL ON FUNCTION public.isnt_aggregate(name, name) TO service_role;


--
-- Name: FUNCTION isnt_aggregate(name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.isnt_aggregate(name, text) TO anon;
GRANT ALL ON FUNCTION public.isnt_aggregate(name, text) TO authenticated;
GRANT ALL ON FUNCTION public.isnt_aggregate(name, text) TO service_role;


--
-- Name: FUNCTION isnt_aggregate(name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.isnt_aggregate(name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.isnt_aggregate(name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.isnt_aggregate(name, name[], text) TO service_role;


--
-- Name: FUNCTION isnt_aggregate(name, name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.isnt_aggregate(name, name, name[]) TO anon;
GRANT ALL ON FUNCTION public.isnt_aggregate(name, name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public.isnt_aggregate(name, name, name[]) TO service_role;


--
-- Name: FUNCTION isnt_aggregate(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.isnt_aggregate(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.isnt_aggregate(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.isnt_aggregate(name, name, text) TO service_role;


--
-- Name: FUNCTION isnt_aggregate(name, name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.isnt_aggregate(name, name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.isnt_aggregate(name, name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.isnt_aggregate(name, name, name[], text) TO service_role;


--
-- Name: FUNCTION isnt_ancestor_of(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.isnt_ancestor_of(name, name) TO anon;
GRANT ALL ON FUNCTION public.isnt_ancestor_of(name, name) TO authenticated;
GRANT ALL ON FUNCTION public.isnt_ancestor_of(name, name) TO service_role;


--
-- Name: FUNCTION isnt_ancestor_of(name, name, integer); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.isnt_ancestor_of(name, name, integer) TO anon;
GRANT ALL ON FUNCTION public.isnt_ancestor_of(name, name, integer) TO authenticated;
GRANT ALL ON FUNCTION public.isnt_ancestor_of(name, name, integer) TO service_role;


--
-- Name: FUNCTION isnt_ancestor_of(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.isnt_ancestor_of(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.isnt_ancestor_of(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.isnt_ancestor_of(name, name, text) TO service_role;


--
-- Name: FUNCTION isnt_ancestor_of(name, name, integer, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.isnt_ancestor_of(name, name, integer, text) TO anon;
GRANT ALL ON FUNCTION public.isnt_ancestor_of(name, name, integer, text) TO authenticated;
GRANT ALL ON FUNCTION public.isnt_ancestor_of(name, name, integer, text) TO service_role;


--
-- Name: FUNCTION isnt_ancestor_of(name, name, name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.isnt_ancestor_of(name, name, name, name) TO anon;
GRANT ALL ON FUNCTION public.isnt_ancestor_of(name, name, name, name) TO authenticated;
GRANT ALL ON FUNCTION public.isnt_ancestor_of(name, name, name, name) TO service_role;


--
-- Name: FUNCTION isnt_ancestor_of(name, name, name, name, integer); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.isnt_ancestor_of(name, name, name, name, integer) TO anon;
GRANT ALL ON FUNCTION public.isnt_ancestor_of(name, name, name, name, integer) TO authenticated;
GRANT ALL ON FUNCTION public.isnt_ancestor_of(name, name, name, name, integer) TO service_role;


--
-- Name: FUNCTION isnt_ancestor_of(name, name, name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.isnt_ancestor_of(name, name, name, name, text) TO anon;
GRANT ALL ON FUNCTION public.isnt_ancestor_of(name, name, name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.isnt_ancestor_of(name, name, name, name, text) TO service_role;


--
-- Name: FUNCTION isnt_ancestor_of(name, name, name, name, integer, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.isnt_ancestor_of(name, name, name, name, integer, text) TO anon;
GRANT ALL ON FUNCTION public.isnt_ancestor_of(name, name, name, name, integer, text) TO authenticated;
GRANT ALL ON FUNCTION public.isnt_ancestor_of(name, name, name, name, integer, text) TO service_role;


--
-- Name: FUNCTION isnt_definer(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.isnt_definer(name) TO anon;
GRANT ALL ON FUNCTION public.isnt_definer(name) TO authenticated;
GRANT ALL ON FUNCTION public.isnt_definer(name) TO service_role;


--
-- Name: FUNCTION isnt_definer(name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.isnt_definer(name, name[]) TO anon;
GRANT ALL ON FUNCTION public.isnt_definer(name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public.isnt_definer(name, name[]) TO service_role;


--
-- Name: FUNCTION isnt_definer(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.isnt_definer(name, name) TO anon;
GRANT ALL ON FUNCTION public.isnt_definer(name, name) TO authenticated;
GRANT ALL ON FUNCTION public.isnt_definer(name, name) TO service_role;


--
-- Name: FUNCTION isnt_definer(name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.isnt_definer(name, text) TO anon;
GRANT ALL ON FUNCTION public.isnt_definer(name, text) TO authenticated;
GRANT ALL ON FUNCTION public.isnt_definer(name, text) TO service_role;


--
-- Name: FUNCTION isnt_definer(name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.isnt_definer(name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.isnt_definer(name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.isnt_definer(name, name[], text) TO service_role;


--
-- Name: FUNCTION isnt_definer(name, name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.isnt_definer(name, name, name[]) TO anon;
GRANT ALL ON FUNCTION public.isnt_definer(name, name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public.isnt_definer(name, name, name[]) TO service_role;


--
-- Name: FUNCTION isnt_definer(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.isnt_definer(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.isnt_definer(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.isnt_definer(name, name, text) TO service_role;


--
-- Name: FUNCTION isnt_definer(name, name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.isnt_definer(name, name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.isnt_definer(name, name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.isnt_definer(name, name, name[], text) TO service_role;


--
-- Name: FUNCTION isnt_descendent_of(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.isnt_descendent_of(name, name) TO anon;
GRANT ALL ON FUNCTION public.isnt_descendent_of(name, name) TO authenticated;
GRANT ALL ON FUNCTION public.isnt_descendent_of(name, name) TO service_role;


--
-- Name: FUNCTION isnt_descendent_of(name, name, integer); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.isnt_descendent_of(name, name, integer) TO anon;
GRANT ALL ON FUNCTION public.isnt_descendent_of(name, name, integer) TO authenticated;
GRANT ALL ON FUNCTION public.isnt_descendent_of(name, name, integer) TO service_role;


--
-- Name: FUNCTION isnt_descendent_of(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.isnt_descendent_of(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.isnt_descendent_of(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.isnt_descendent_of(name, name, text) TO service_role;


--
-- Name: FUNCTION isnt_descendent_of(name, name, integer, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.isnt_descendent_of(name, name, integer, text) TO anon;
GRANT ALL ON FUNCTION public.isnt_descendent_of(name, name, integer, text) TO authenticated;
GRANT ALL ON FUNCTION public.isnt_descendent_of(name, name, integer, text) TO service_role;


--
-- Name: FUNCTION isnt_descendent_of(name, name, name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.isnt_descendent_of(name, name, name, name) TO anon;
GRANT ALL ON FUNCTION public.isnt_descendent_of(name, name, name, name) TO authenticated;
GRANT ALL ON FUNCTION public.isnt_descendent_of(name, name, name, name) TO service_role;


--
-- Name: FUNCTION isnt_descendent_of(name, name, name, name, integer); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.isnt_descendent_of(name, name, name, name, integer) TO anon;
GRANT ALL ON FUNCTION public.isnt_descendent_of(name, name, name, name, integer) TO authenticated;
GRANT ALL ON FUNCTION public.isnt_descendent_of(name, name, name, name, integer) TO service_role;


--
-- Name: FUNCTION isnt_descendent_of(name, name, name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.isnt_descendent_of(name, name, name, name, text) TO anon;
GRANT ALL ON FUNCTION public.isnt_descendent_of(name, name, name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.isnt_descendent_of(name, name, name, name, text) TO service_role;


--
-- Name: FUNCTION isnt_descendent_of(name, name, name, name, integer, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.isnt_descendent_of(name, name, name, name, integer, text) TO anon;
GRANT ALL ON FUNCTION public.isnt_descendent_of(name, name, name, name, integer, text) TO authenticated;
GRANT ALL ON FUNCTION public.isnt_descendent_of(name, name, name, name, integer, text) TO service_role;


--
-- Name: FUNCTION isnt_empty(text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.isnt_empty(text) TO anon;
GRANT ALL ON FUNCTION public.isnt_empty(text) TO authenticated;
GRANT ALL ON FUNCTION public.isnt_empty(text) TO service_role;


--
-- Name: FUNCTION isnt_empty(text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.isnt_empty(text, text) TO anon;
GRANT ALL ON FUNCTION public.isnt_empty(text, text) TO authenticated;
GRANT ALL ON FUNCTION public.isnt_empty(text, text) TO service_role;


--
-- Name: FUNCTION isnt_member_of(name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.isnt_member_of(name, name[]) TO anon;
GRANT ALL ON FUNCTION public.isnt_member_of(name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public.isnt_member_of(name, name[]) TO service_role;


--
-- Name: FUNCTION isnt_member_of(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.isnt_member_of(name, name) TO anon;
GRANT ALL ON FUNCTION public.isnt_member_of(name, name) TO authenticated;
GRANT ALL ON FUNCTION public.isnt_member_of(name, name) TO service_role;


--
-- Name: FUNCTION isnt_member_of(name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.isnt_member_of(name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.isnt_member_of(name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.isnt_member_of(name, name[], text) TO service_role;


--
-- Name: FUNCTION isnt_member_of(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.isnt_member_of(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.isnt_member_of(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.isnt_member_of(name, name, text) TO service_role;


--
-- Name: FUNCTION isnt_normal_function(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.isnt_normal_function(name) TO anon;
GRANT ALL ON FUNCTION public.isnt_normal_function(name) TO authenticated;
GRANT ALL ON FUNCTION public.isnt_normal_function(name) TO service_role;


--
-- Name: FUNCTION isnt_normal_function(name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.isnt_normal_function(name, name[]) TO anon;
GRANT ALL ON FUNCTION public.isnt_normal_function(name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public.isnt_normal_function(name, name[]) TO service_role;


--
-- Name: FUNCTION isnt_normal_function(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.isnt_normal_function(name, name) TO anon;
GRANT ALL ON FUNCTION public.isnt_normal_function(name, name) TO authenticated;
GRANT ALL ON FUNCTION public.isnt_normal_function(name, name) TO service_role;


--
-- Name: FUNCTION isnt_normal_function(name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.isnt_normal_function(name, text) TO anon;
GRANT ALL ON FUNCTION public.isnt_normal_function(name, text) TO authenticated;
GRANT ALL ON FUNCTION public.isnt_normal_function(name, text) TO service_role;


--
-- Name: FUNCTION isnt_normal_function(name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.isnt_normal_function(name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.isnt_normal_function(name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.isnt_normal_function(name, name[], text) TO service_role;


--
-- Name: FUNCTION isnt_normal_function(name, name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.isnt_normal_function(name, name, name[]) TO anon;
GRANT ALL ON FUNCTION public.isnt_normal_function(name, name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public.isnt_normal_function(name, name, name[]) TO service_role;


--
-- Name: FUNCTION isnt_normal_function(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.isnt_normal_function(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.isnt_normal_function(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.isnt_normal_function(name, name, text) TO service_role;


--
-- Name: FUNCTION isnt_normal_function(name, name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.isnt_normal_function(name, name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.isnt_normal_function(name, name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.isnt_normal_function(name, name, name[], text) TO service_role;


--
-- Name: FUNCTION isnt_partitioned(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.isnt_partitioned(name) TO anon;
GRANT ALL ON FUNCTION public.isnt_partitioned(name) TO authenticated;
GRANT ALL ON FUNCTION public.isnt_partitioned(name) TO service_role;


--
-- Name: FUNCTION isnt_partitioned(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.isnt_partitioned(name, name) TO anon;
GRANT ALL ON FUNCTION public.isnt_partitioned(name, name) TO authenticated;
GRANT ALL ON FUNCTION public.isnt_partitioned(name, name) TO service_role;


--
-- Name: FUNCTION isnt_partitioned(name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.isnt_partitioned(name, text) TO anon;
GRANT ALL ON FUNCTION public.isnt_partitioned(name, text) TO authenticated;
GRANT ALL ON FUNCTION public.isnt_partitioned(name, text) TO service_role;


--
-- Name: FUNCTION isnt_partitioned(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.isnt_partitioned(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.isnt_partitioned(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.isnt_partitioned(name, name, text) TO service_role;


--
-- Name: FUNCTION isnt_procedure(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.isnt_procedure(name) TO anon;
GRANT ALL ON FUNCTION public.isnt_procedure(name) TO authenticated;
GRANT ALL ON FUNCTION public.isnt_procedure(name) TO service_role;


--
-- Name: FUNCTION isnt_procedure(name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.isnt_procedure(name, name[]) TO anon;
GRANT ALL ON FUNCTION public.isnt_procedure(name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public.isnt_procedure(name, name[]) TO service_role;


--
-- Name: FUNCTION isnt_procedure(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.isnt_procedure(name, name) TO anon;
GRANT ALL ON FUNCTION public.isnt_procedure(name, name) TO authenticated;
GRANT ALL ON FUNCTION public.isnt_procedure(name, name) TO service_role;


--
-- Name: FUNCTION isnt_procedure(name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.isnt_procedure(name, text) TO anon;
GRANT ALL ON FUNCTION public.isnt_procedure(name, text) TO authenticated;
GRANT ALL ON FUNCTION public.isnt_procedure(name, text) TO service_role;


--
-- Name: FUNCTION isnt_procedure(name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.isnt_procedure(name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.isnt_procedure(name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.isnt_procedure(name, name[], text) TO service_role;


--
-- Name: FUNCTION isnt_procedure(name, name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.isnt_procedure(name, name, name[]) TO anon;
GRANT ALL ON FUNCTION public.isnt_procedure(name, name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public.isnt_procedure(name, name, name[]) TO service_role;


--
-- Name: FUNCTION isnt_procedure(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.isnt_procedure(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.isnt_procedure(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.isnt_procedure(name, name, text) TO service_role;


--
-- Name: FUNCTION isnt_procedure(name, name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.isnt_procedure(name, name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.isnt_procedure(name, name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.isnt_procedure(name, name, name[], text) TO service_role;


--
-- Name: FUNCTION isnt_strict(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.isnt_strict(name) TO anon;
GRANT ALL ON FUNCTION public.isnt_strict(name) TO authenticated;
GRANT ALL ON FUNCTION public.isnt_strict(name) TO service_role;


--
-- Name: FUNCTION isnt_strict(name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.isnt_strict(name, name[]) TO anon;
GRANT ALL ON FUNCTION public.isnt_strict(name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public.isnt_strict(name, name[]) TO service_role;


--
-- Name: FUNCTION isnt_strict(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.isnt_strict(name, name) TO anon;
GRANT ALL ON FUNCTION public.isnt_strict(name, name) TO authenticated;
GRANT ALL ON FUNCTION public.isnt_strict(name, name) TO service_role;


--
-- Name: FUNCTION isnt_strict(name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.isnt_strict(name, text) TO anon;
GRANT ALL ON FUNCTION public.isnt_strict(name, text) TO authenticated;
GRANT ALL ON FUNCTION public.isnt_strict(name, text) TO service_role;


--
-- Name: FUNCTION isnt_strict(name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.isnt_strict(name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.isnt_strict(name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.isnt_strict(name, name[], text) TO service_role;


--
-- Name: FUNCTION isnt_strict(name, name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.isnt_strict(name, name, name[]) TO anon;
GRANT ALL ON FUNCTION public.isnt_strict(name, name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public.isnt_strict(name, name, name[]) TO service_role;


--
-- Name: FUNCTION isnt_strict(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.isnt_strict(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.isnt_strict(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.isnt_strict(name, name, text) TO service_role;


--
-- Name: FUNCTION isnt_strict(name, name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.isnt_strict(name, name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.isnt_strict(name, name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.isnt_strict(name, name, name[], text) TO service_role;


--
-- Name: FUNCTION isnt_superuser(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.isnt_superuser(name) TO anon;
GRANT ALL ON FUNCTION public.isnt_superuser(name) TO authenticated;
GRANT ALL ON FUNCTION public.isnt_superuser(name) TO service_role;


--
-- Name: FUNCTION isnt_superuser(name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.isnt_superuser(name, text) TO anon;
GRANT ALL ON FUNCTION public.isnt_superuser(name, text) TO authenticated;
GRANT ALL ON FUNCTION public.isnt_superuser(name, text) TO service_role;


--
-- Name: FUNCTION isnt_window(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.isnt_window(name) TO anon;
GRANT ALL ON FUNCTION public.isnt_window(name) TO authenticated;
GRANT ALL ON FUNCTION public.isnt_window(name) TO service_role;


--
-- Name: FUNCTION isnt_window(name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.isnt_window(name, name[]) TO anon;
GRANT ALL ON FUNCTION public.isnt_window(name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public.isnt_window(name, name[]) TO service_role;


--
-- Name: FUNCTION isnt_window(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.isnt_window(name, name) TO anon;
GRANT ALL ON FUNCTION public.isnt_window(name, name) TO authenticated;
GRANT ALL ON FUNCTION public.isnt_window(name, name) TO service_role;


--
-- Name: FUNCTION isnt_window(name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.isnt_window(name, text) TO anon;
GRANT ALL ON FUNCTION public.isnt_window(name, text) TO authenticated;
GRANT ALL ON FUNCTION public.isnt_window(name, text) TO service_role;


--
-- Name: FUNCTION isnt_window(name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.isnt_window(name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.isnt_window(name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.isnt_window(name, name[], text) TO service_role;


--
-- Name: FUNCTION isnt_window(name, name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.isnt_window(name, name, name[]) TO anon;
GRANT ALL ON FUNCTION public.isnt_window(name, name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public.isnt_window(name, name, name[]) TO service_role;


--
-- Name: FUNCTION isnt_window(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.isnt_window(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.isnt_window(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.isnt_window(name, name, text) TO service_role;


--
-- Name: FUNCTION isnt_window(name, name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.isnt_window(name, name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.isnt_window(name, name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.isnt_window(name, name, name[], text) TO service_role;


--
-- Name: FUNCTION language_is_trusted(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.language_is_trusted(name) TO anon;
GRANT ALL ON FUNCTION public.language_is_trusted(name) TO authenticated;
GRANT ALL ON FUNCTION public.language_is_trusted(name) TO service_role;


--
-- Name: FUNCTION language_is_trusted(name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.language_is_trusted(name, text) TO anon;
GRANT ALL ON FUNCTION public.language_is_trusted(name, text) TO authenticated;
GRANT ALL ON FUNCTION public.language_is_trusted(name, text) TO service_role;


--
-- Name: FUNCTION language_owner_is(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.language_owner_is(name, name) TO anon;
GRANT ALL ON FUNCTION public.language_owner_is(name, name) TO authenticated;
GRANT ALL ON FUNCTION public.language_owner_is(name, name) TO service_role;


--
-- Name: FUNCTION language_owner_is(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.language_owner_is(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.language_owner_is(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.language_owner_is(name, name, text) TO service_role;


--
-- Name: FUNCTION language_privs_are(name, name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.language_privs_are(name, name, name[]) TO anon;
GRANT ALL ON FUNCTION public.language_privs_are(name, name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public.language_privs_are(name, name, name[]) TO service_role;


--
-- Name: FUNCTION language_privs_are(name, name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.language_privs_are(name, name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.language_privs_are(name, name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.language_privs_are(name, name, name[], text) TO service_role;


--
-- Name: FUNCTION languages_are(name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.languages_are(name[]) TO anon;
GRANT ALL ON FUNCTION public.languages_are(name[]) TO authenticated;
GRANT ALL ON FUNCTION public.languages_are(name[]) TO service_role;


--
-- Name: FUNCTION languages_are(name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.languages_are(name[], text) TO anon;
GRANT ALL ON FUNCTION public.languages_are(name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.languages_are(name[], text) TO service_role;


--
-- Name: FUNCTION lives_ok(text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.lives_ok(text) TO anon;
GRANT ALL ON FUNCTION public.lives_ok(text) TO authenticated;
GRANT ALL ON FUNCTION public.lives_ok(text) TO service_role;


--
-- Name: FUNCTION lives_ok(text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.lives_ok(text, text) TO anon;
GRANT ALL ON FUNCTION public.lives_ok(text, text) TO authenticated;
GRANT ALL ON FUNCTION public.lives_ok(text, text) TO service_role;


--
-- Name: FUNCTION matches(anyelement, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.matches(anyelement, text) TO anon;
GRANT ALL ON FUNCTION public.matches(anyelement, text) TO authenticated;
GRANT ALL ON FUNCTION public.matches(anyelement, text) TO service_role;


--
-- Name: FUNCTION matches(anyelement, text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.matches(anyelement, text, text) TO anon;
GRANT ALL ON FUNCTION public.matches(anyelement, text, text) TO authenticated;
GRANT ALL ON FUNCTION public.matches(anyelement, text, text) TO service_role;


--
-- Name: FUNCTION materialized_view_owner_is(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.materialized_view_owner_is(name, name) TO anon;
GRANT ALL ON FUNCTION public.materialized_view_owner_is(name, name) TO authenticated;
GRANT ALL ON FUNCTION public.materialized_view_owner_is(name, name) TO service_role;


--
-- Name: FUNCTION materialized_view_owner_is(name, name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.materialized_view_owner_is(name, name, name) TO anon;
GRANT ALL ON FUNCTION public.materialized_view_owner_is(name, name, name) TO authenticated;
GRANT ALL ON FUNCTION public.materialized_view_owner_is(name, name, name) TO service_role;


--
-- Name: FUNCTION materialized_view_owner_is(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.materialized_view_owner_is(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.materialized_view_owner_is(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.materialized_view_owner_is(name, name, text) TO service_role;


--
-- Name: FUNCTION materialized_view_owner_is(name, name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.materialized_view_owner_is(name, name, name, text) TO anon;
GRANT ALL ON FUNCTION public.materialized_view_owner_is(name, name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.materialized_view_owner_is(name, name, name, text) TO service_role;


--
-- Name: FUNCTION materialized_views_are(name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.materialized_views_are(name[]) TO anon;
GRANT ALL ON FUNCTION public.materialized_views_are(name[]) TO authenticated;
GRANT ALL ON FUNCTION public.materialized_views_are(name[]) TO service_role;


--
-- Name: FUNCTION materialized_views_are(name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.materialized_views_are(name[], text) TO anon;
GRANT ALL ON FUNCTION public.materialized_views_are(name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.materialized_views_are(name[], text) TO service_role;


--
-- Name: FUNCTION materialized_views_are(name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.materialized_views_are(name, name[]) TO anon;
GRANT ALL ON FUNCTION public.materialized_views_are(name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public.materialized_views_are(name, name[]) TO service_role;


--
-- Name: FUNCTION materialized_views_are(name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.materialized_views_are(name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.materialized_views_are(name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.materialized_views_are(name, name[], text) TO service_role;


--
-- Name: FUNCTION no_plan(); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.no_plan() TO anon;
GRANT ALL ON FUNCTION public.no_plan() TO authenticated;
GRANT ALL ON FUNCTION public.no_plan() TO service_role;


--
-- Name: FUNCTION num_failed(); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.num_failed() TO anon;
GRANT ALL ON FUNCTION public.num_failed() TO authenticated;
GRANT ALL ON FUNCTION public.num_failed() TO service_role;


--
-- Name: FUNCTION ok(boolean); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.ok(boolean) TO anon;
GRANT ALL ON FUNCTION public.ok(boolean) TO authenticated;
GRANT ALL ON FUNCTION public.ok(boolean) TO service_role;


--
-- Name: FUNCTION ok(boolean, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.ok(boolean, text) TO anon;
GRANT ALL ON FUNCTION public.ok(boolean, text) TO authenticated;
GRANT ALL ON FUNCTION public.ok(boolean, text) TO service_role;


--
-- Name: FUNCTION opclass_owner_is(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.opclass_owner_is(name, name) TO anon;
GRANT ALL ON FUNCTION public.opclass_owner_is(name, name) TO authenticated;
GRANT ALL ON FUNCTION public.opclass_owner_is(name, name) TO service_role;


--
-- Name: FUNCTION opclass_owner_is(name, name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.opclass_owner_is(name, name, name) TO anon;
GRANT ALL ON FUNCTION public.opclass_owner_is(name, name, name) TO authenticated;
GRANT ALL ON FUNCTION public.opclass_owner_is(name, name, name) TO service_role;


--
-- Name: FUNCTION opclass_owner_is(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.opclass_owner_is(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.opclass_owner_is(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.opclass_owner_is(name, name, text) TO service_role;


--
-- Name: FUNCTION opclass_owner_is(name, name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.opclass_owner_is(name, name, name, text) TO anon;
GRANT ALL ON FUNCTION public.opclass_owner_is(name, name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.opclass_owner_is(name, name, name, text) TO service_role;


--
-- Name: FUNCTION opclasses_are(name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.opclasses_are(name[]) TO anon;
GRANT ALL ON FUNCTION public.opclasses_are(name[]) TO authenticated;
GRANT ALL ON FUNCTION public.opclasses_are(name[]) TO service_role;


--
-- Name: FUNCTION opclasses_are(name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.opclasses_are(name[], text) TO anon;
GRANT ALL ON FUNCTION public.opclasses_are(name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.opclasses_are(name[], text) TO service_role;


--
-- Name: FUNCTION opclasses_are(name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.opclasses_are(name, name[]) TO anon;
GRANT ALL ON FUNCTION public.opclasses_are(name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public.opclasses_are(name, name[]) TO service_role;


--
-- Name: FUNCTION opclasses_are(name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.opclasses_are(name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.opclasses_are(name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.opclasses_are(name, name[], text) TO service_role;


--
-- Name: FUNCTION operators_are(text[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.operators_are(text[]) TO anon;
GRANT ALL ON FUNCTION public.operators_are(text[]) TO authenticated;
GRANT ALL ON FUNCTION public.operators_are(text[]) TO service_role;


--
-- Name: FUNCTION operators_are(text[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.operators_are(text[], text) TO anon;
GRANT ALL ON FUNCTION public.operators_are(text[], text) TO authenticated;
GRANT ALL ON FUNCTION public.operators_are(text[], text) TO service_role;


--
-- Name: FUNCTION operators_are(name, text[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.operators_are(name, text[]) TO anon;
GRANT ALL ON FUNCTION public.operators_are(name, text[]) TO authenticated;
GRANT ALL ON FUNCTION public.operators_are(name, text[]) TO service_role;


--
-- Name: FUNCTION operators_are(name, text[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.operators_are(name, text[], text) TO anon;
GRANT ALL ON FUNCTION public.operators_are(name, text[], text) TO authenticated;
GRANT ALL ON FUNCTION public.operators_are(name, text[], text) TO service_role;


--
-- Name: FUNCTION os_name(); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.os_name() TO anon;
GRANT ALL ON FUNCTION public.os_name() TO authenticated;
GRANT ALL ON FUNCTION public.os_name() TO service_role;


--
-- Name: FUNCTION partitions_are(name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.partitions_are(name, name[]) TO anon;
GRANT ALL ON FUNCTION public.partitions_are(name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public.partitions_are(name, name[]) TO service_role;


--
-- Name: FUNCTION partitions_are(name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.partitions_are(name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.partitions_are(name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.partitions_are(name, name[], text) TO service_role;


--
-- Name: FUNCTION partitions_are(name, name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.partitions_are(name, name, name[]) TO anon;
GRANT ALL ON FUNCTION public.partitions_are(name, name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public.partitions_are(name, name, name[]) TO service_role;


--
-- Name: FUNCTION partitions_are(name, name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.partitions_are(name, name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.partitions_are(name, name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.partitions_are(name, name, name[], text) TO service_role;


--
-- Name: FUNCTION pass(); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.pass() TO anon;
GRANT ALL ON FUNCTION public.pass() TO authenticated;
GRANT ALL ON FUNCTION public.pass() TO service_role;


--
-- Name: FUNCTION pass(text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.pass(text) TO anon;
GRANT ALL ON FUNCTION public.pass(text) TO authenticated;
GRANT ALL ON FUNCTION public.pass(text) TO service_role;


--
-- Name: FUNCTION performs_ok(text, numeric); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.performs_ok(text, numeric) TO anon;
GRANT ALL ON FUNCTION public.performs_ok(text, numeric) TO authenticated;
GRANT ALL ON FUNCTION public.performs_ok(text, numeric) TO service_role;


--
-- Name: FUNCTION performs_ok(text, numeric, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.performs_ok(text, numeric, text) TO anon;
GRANT ALL ON FUNCTION public.performs_ok(text, numeric, text) TO authenticated;
GRANT ALL ON FUNCTION public.performs_ok(text, numeric, text) TO service_role;


--
-- Name: FUNCTION performs_within(text, numeric, numeric); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.performs_within(text, numeric, numeric) TO anon;
GRANT ALL ON FUNCTION public.performs_within(text, numeric, numeric) TO authenticated;
GRANT ALL ON FUNCTION public.performs_within(text, numeric, numeric) TO service_role;


--
-- Name: FUNCTION performs_within(text, numeric, numeric, integer); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.performs_within(text, numeric, numeric, integer) TO anon;
GRANT ALL ON FUNCTION public.performs_within(text, numeric, numeric, integer) TO authenticated;
GRANT ALL ON FUNCTION public.performs_within(text, numeric, numeric, integer) TO service_role;


--
-- Name: FUNCTION performs_within(text, numeric, numeric, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.performs_within(text, numeric, numeric, text) TO anon;
GRANT ALL ON FUNCTION public.performs_within(text, numeric, numeric, text) TO authenticated;
GRANT ALL ON FUNCTION public.performs_within(text, numeric, numeric, text) TO service_role;


--
-- Name: FUNCTION performs_within(text, numeric, numeric, integer, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.performs_within(text, numeric, numeric, integer, text) TO anon;
GRANT ALL ON FUNCTION public.performs_within(text, numeric, numeric, integer, text) TO authenticated;
GRANT ALL ON FUNCTION public.performs_within(text, numeric, numeric, integer, text) TO service_role;


--
-- Name: FUNCTION pg_version(); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.pg_version() TO anon;
GRANT ALL ON FUNCTION public.pg_version() TO authenticated;
GRANT ALL ON FUNCTION public.pg_version() TO service_role;


--
-- Name: FUNCTION pg_version_num(); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.pg_version_num() TO anon;
GRANT ALL ON FUNCTION public.pg_version_num() TO authenticated;
GRANT ALL ON FUNCTION public.pg_version_num() TO service_role;


--
-- Name: FUNCTION pgp_armor_headers(text, OUT key text, OUT value text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.pgp_armor_headers(text, OUT key text, OUT value text) TO anon;
GRANT ALL ON FUNCTION public.pgp_armor_headers(text, OUT key text, OUT value text) TO authenticated;
GRANT ALL ON FUNCTION public.pgp_armor_headers(text, OUT key text, OUT value text) TO service_role;


--
-- Name: FUNCTION pgp_key_id(bytea); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.pgp_key_id(bytea) TO anon;
GRANT ALL ON FUNCTION public.pgp_key_id(bytea) TO authenticated;
GRANT ALL ON FUNCTION public.pgp_key_id(bytea) TO service_role;


--
-- Name: FUNCTION pgp_pub_decrypt(bytea, bytea); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.pgp_pub_decrypt(bytea, bytea) TO anon;
GRANT ALL ON FUNCTION public.pgp_pub_decrypt(bytea, bytea) TO authenticated;
GRANT ALL ON FUNCTION public.pgp_pub_decrypt(bytea, bytea) TO service_role;


--
-- Name: FUNCTION pgp_pub_decrypt(bytea, bytea, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.pgp_pub_decrypt(bytea, bytea, text) TO anon;
GRANT ALL ON FUNCTION public.pgp_pub_decrypt(bytea, bytea, text) TO authenticated;
GRANT ALL ON FUNCTION public.pgp_pub_decrypt(bytea, bytea, text) TO service_role;


--
-- Name: FUNCTION pgp_pub_decrypt(bytea, bytea, text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.pgp_pub_decrypt(bytea, bytea, text, text) TO anon;
GRANT ALL ON FUNCTION public.pgp_pub_decrypt(bytea, bytea, text, text) TO authenticated;
GRANT ALL ON FUNCTION public.pgp_pub_decrypt(bytea, bytea, text, text) TO service_role;


--
-- Name: FUNCTION pgp_pub_decrypt_bytea(bytea, bytea); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.pgp_pub_decrypt_bytea(bytea, bytea) TO anon;
GRANT ALL ON FUNCTION public.pgp_pub_decrypt_bytea(bytea, bytea) TO authenticated;
GRANT ALL ON FUNCTION public.pgp_pub_decrypt_bytea(bytea, bytea) TO service_role;


--
-- Name: FUNCTION pgp_pub_decrypt_bytea(bytea, bytea, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.pgp_pub_decrypt_bytea(bytea, bytea, text) TO anon;
GRANT ALL ON FUNCTION public.pgp_pub_decrypt_bytea(bytea, bytea, text) TO authenticated;
GRANT ALL ON FUNCTION public.pgp_pub_decrypt_bytea(bytea, bytea, text) TO service_role;


--
-- Name: FUNCTION pgp_pub_decrypt_bytea(bytea, bytea, text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.pgp_pub_decrypt_bytea(bytea, bytea, text, text) TO anon;
GRANT ALL ON FUNCTION public.pgp_pub_decrypt_bytea(bytea, bytea, text, text) TO authenticated;
GRANT ALL ON FUNCTION public.pgp_pub_decrypt_bytea(bytea, bytea, text, text) TO service_role;


--
-- Name: FUNCTION pgp_pub_encrypt(text, bytea); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.pgp_pub_encrypt(text, bytea) TO anon;
GRANT ALL ON FUNCTION public.pgp_pub_encrypt(text, bytea) TO authenticated;
GRANT ALL ON FUNCTION public.pgp_pub_encrypt(text, bytea) TO service_role;


--
-- Name: FUNCTION pgp_pub_encrypt(text, bytea, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.pgp_pub_encrypt(text, bytea, text) TO anon;
GRANT ALL ON FUNCTION public.pgp_pub_encrypt(text, bytea, text) TO authenticated;
GRANT ALL ON FUNCTION public.pgp_pub_encrypt(text, bytea, text) TO service_role;


--
-- Name: FUNCTION pgp_pub_encrypt_bytea(bytea, bytea); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.pgp_pub_encrypt_bytea(bytea, bytea) TO anon;
GRANT ALL ON FUNCTION public.pgp_pub_encrypt_bytea(bytea, bytea) TO authenticated;
GRANT ALL ON FUNCTION public.pgp_pub_encrypt_bytea(bytea, bytea) TO service_role;


--
-- Name: FUNCTION pgp_pub_encrypt_bytea(bytea, bytea, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.pgp_pub_encrypt_bytea(bytea, bytea, text) TO anon;
GRANT ALL ON FUNCTION public.pgp_pub_encrypt_bytea(bytea, bytea, text) TO authenticated;
GRANT ALL ON FUNCTION public.pgp_pub_encrypt_bytea(bytea, bytea, text) TO service_role;


--
-- Name: FUNCTION pgp_sym_decrypt(bytea, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.pgp_sym_decrypt(bytea, text) TO anon;
GRANT ALL ON FUNCTION public.pgp_sym_decrypt(bytea, text) TO authenticated;
GRANT ALL ON FUNCTION public.pgp_sym_decrypt(bytea, text) TO service_role;


--
-- Name: FUNCTION pgp_sym_decrypt(bytea, text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.pgp_sym_decrypt(bytea, text, text) TO anon;
GRANT ALL ON FUNCTION public.pgp_sym_decrypt(bytea, text, text) TO authenticated;
GRANT ALL ON FUNCTION public.pgp_sym_decrypt(bytea, text, text) TO service_role;


--
-- Name: FUNCTION pgp_sym_decrypt_bytea(bytea, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.pgp_sym_decrypt_bytea(bytea, text) TO anon;
GRANT ALL ON FUNCTION public.pgp_sym_decrypt_bytea(bytea, text) TO authenticated;
GRANT ALL ON FUNCTION public.pgp_sym_decrypt_bytea(bytea, text) TO service_role;


--
-- Name: FUNCTION pgp_sym_decrypt_bytea(bytea, text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.pgp_sym_decrypt_bytea(bytea, text, text) TO anon;
GRANT ALL ON FUNCTION public.pgp_sym_decrypt_bytea(bytea, text, text) TO authenticated;
GRANT ALL ON FUNCTION public.pgp_sym_decrypt_bytea(bytea, text, text) TO service_role;


--
-- Name: FUNCTION pgp_sym_encrypt(text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.pgp_sym_encrypt(text, text) TO anon;
GRANT ALL ON FUNCTION public.pgp_sym_encrypt(text, text) TO authenticated;
GRANT ALL ON FUNCTION public.pgp_sym_encrypt(text, text) TO service_role;


--
-- Name: FUNCTION pgp_sym_encrypt(text, text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.pgp_sym_encrypt(text, text, text) TO anon;
GRANT ALL ON FUNCTION public.pgp_sym_encrypt(text, text, text) TO authenticated;
GRANT ALL ON FUNCTION public.pgp_sym_encrypt(text, text, text) TO service_role;


--
-- Name: FUNCTION pgp_sym_encrypt_bytea(bytea, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.pgp_sym_encrypt_bytea(bytea, text) TO anon;
GRANT ALL ON FUNCTION public.pgp_sym_encrypt_bytea(bytea, text) TO authenticated;
GRANT ALL ON FUNCTION public.pgp_sym_encrypt_bytea(bytea, text) TO service_role;


--
-- Name: FUNCTION pgp_sym_encrypt_bytea(bytea, text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.pgp_sym_encrypt_bytea(bytea, text, text) TO anon;
GRANT ALL ON FUNCTION public.pgp_sym_encrypt_bytea(bytea, text, text) TO authenticated;
GRANT ALL ON FUNCTION public.pgp_sym_encrypt_bytea(bytea, text, text) TO service_role;


--
-- Name: FUNCTION pgtap_version(); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.pgtap_version() TO anon;
GRANT ALL ON FUNCTION public.pgtap_version() TO authenticated;
GRANT ALL ON FUNCTION public.pgtap_version() TO service_role;


--
-- Name: FUNCTION plan(integer); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.plan(integer) TO anon;
GRANT ALL ON FUNCTION public.plan(integer) TO authenticated;
GRANT ALL ON FUNCTION public.plan(integer) TO service_role;


--
-- Name: FUNCTION policies_are(name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.policies_are(name, name[]) TO anon;
GRANT ALL ON FUNCTION public.policies_are(name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public.policies_are(name, name[]) TO service_role;


--
-- Name: FUNCTION policies_are(name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.policies_are(name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.policies_are(name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.policies_are(name, name[], text) TO service_role;


--
-- Name: FUNCTION policies_are(name, name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.policies_are(name, name, name[]) TO anon;
GRANT ALL ON FUNCTION public.policies_are(name, name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public.policies_are(name, name, name[]) TO service_role;


--
-- Name: FUNCTION policies_are(name, name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.policies_are(name, name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.policies_are(name, name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.policies_are(name, name, name[], text) TO service_role;


--
-- Name: FUNCTION policy_cmd_is(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.policy_cmd_is(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.policy_cmd_is(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.policy_cmd_is(name, name, text) TO service_role;


--
-- Name: FUNCTION policy_cmd_is(name, name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.policy_cmd_is(name, name, name, text) TO anon;
GRANT ALL ON FUNCTION public.policy_cmd_is(name, name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.policy_cmd_is(name, name, name, text) TO service_role;


--
-- Name: FUNCTION policy_cmd_is(name, name, text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.policy_cmd_is(name, name, text, text) TO anon;
GRANT ALL ON FUNCTION public.policy_cmd_is(name, name, text, text) TO authenticated;
GRANT ALL ON FUNCTION public.policy_cmd_is(name, name, text, text) TO service_role;


--
-- Name: FUNCTION policy_cmd_is(name, name, name, text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.policy_cmd_is(name, name, name, text, text) TO anon;
GRANT ALL ON FUNCTION public.policy_cmd_is(name, name, name, text, text) TO authenticated;
GRANT ALL ON FUNCTION public.policy_cmd_is(name, name, name, text, text) TO service_role;


--
-- Name: FUNCTION policy_roles_are(name, name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.policy_roles_are(name, name, name[]) TO anon;
GRANT ALL ON FUNCTION public.policy_roles_are(name, name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public.policy_roles_are(name, name, name[]) TO service_role;


--
-- Name: FUNCTION policy_roles_are(name, name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.policy_roles_are(name, name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.policy_roles_are(name, name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.policy_roles_are(name, name, name[], text) TO service_role;


--
-- Name: FUNCTION policy_roles_are(name, name, name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.policy_roles_are(name, name, name, name[]) TO anon;
GRANT ALL ON FUNCTION public.policy_roles_are(name, name, name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public.policy_roles_are(name, name, name, name[]) TO service_role;


--
-- Name: FUNCTION policy_roles_are(name, name, name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.policy_roles_are(name, name, name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.policy_roles_are(name, name, name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.policy_roles_are(name, name, name, name[], text) TO service_role;


--
-- Name: FUNCTION relation_owner_is(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.relation_owner_is(name, name) TO anon;
GRANT ALL ON FUNCTION public.relation_owner_is(name, name) TO authenticated;
GRANT ALL ON FUNCTION public.relation_owner_is(name, name) TO service_role;


--
-- Name: FUNCTION relation_owner_is(name, name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.relation_owner_is(name, name, name) TO anon;
GRANT ALL ON FUNCTION public.relation_owner_is(name, name, name) TO authenticated;
GRANT ALL ON FUNCTION public.relation_owner_is(name, name, name) TO service_role;


--
-- Name: FUNCTION relation_owner_is(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.relation_owner_is(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.relation_owner_is(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.relation_owner_is(name, name, text) TO service_role;


--
-- Name: FUNCTION relation_owner_is(name, name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.relation_owner_is(name, name, name, text) TO anon;
GRANT ALL ON FUNCTION public.relation_owner_is(name, name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.relation_owner_is(name, name, name, text) TO service_role;


--
-- Name: FUNCTION results_eq(refcursor, anyarray); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.results_eq(refcursor, anyarray) TO anon;
GRANT ALL ON FUNCTION public.results_eq(refcursor, anyarray) TO authenticated;
GRANT ALL ON FUNCTION public.results_eq(refcursor, anyarray) TO service_role;


--
-- Name: FUNCTION results_eq(refcursor, refcursor); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.results_eq(refcursor, refcursor) TO anon;
GRANT ALL ON FUNCTION public.results_eq(refcursor, refcursor) TO authenticated;
GRANT ALL ON FUNCTION public.results_eq(refcursor, refcursor) TO service_role;


--
-- Name: FUNCTION results_eq(refcursor, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.results_eq(refcursor, text) TO anon;
GRANT ALL ON FUNCTION public.results_eq(refcursor, text) TO authenticated;
GRANT ALL ON FUNCTION public.results_eq(refcursor, text) TO service_role;


--
-- Name: FUNCTION results_eq(text, anyarray); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.results_eq(text, anyarray) TO anon;
GRANT ALL ON FUNCTION public.results_eq(text, anyarray) TO authenticated;
GRANT ALL ON FUNCTION public.results_eq(text, anyarray) TO service_role;


--
-- Name: FUNCTION results_eq(text, refcursor); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.results_eq(text, refcursor) TO anon;
GRANT ALL ON FUNCTION public.results_eq(text, refcursor) TO authenticated;
GRANT ALL ON FUNCTION public.results_eq(text, refcursor) TO service_role;


--
-- Name: FUNCTION results_eq(text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.results_eq(text, text) TO anon;
GRANT ALL ON FUNCTION public.results_eq(text, text) TO authenticated;
GRANT ALL ON FUNCTION public.results_eq(text, text) TO service_role;


--
-- Name: FUNCTION results_eq(refcursor, anyarray, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.results_eq(refcursor, anyarray, text) TO anon;
GRANT ALL ON FUNCTION public.results_eq(refcursor, anyarray, text) TO authenticated;
GRANT ALL ON FUNCTION public.results_eq(refcursor, anyarray, text) TO service_role;


--
-- Name: FUNCTION results_eq(refcursor, refcursor, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.results_eq(refcursor, refcursor, text) TO anon;
GRANT ALL ON FUNCTION public.results_eq(refcursor, refcursor, text) TO authenticated;
GRANT ALL ON FUNCTION public.results_eq(refcursor, refcursor, text) TO service_role;


--
-- Name: FUNCTION results_eq(refcursor, text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.results_eq(refcursor, text, text) TO anon;
GRANT ALL ON FUNCTION public.results_eq(refcursor, text, text) TO authenticated;
GRANT ALL ON FUNCTION public.results_eq(refcursor, text, text) TO service_role;


--
-- Name: FUNCTION results_eq(text, anyarray, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.results_eq(text, anyarray, text) TO anon;
GRANT ALL ON FUNCTION public.results_eq(text, anyarray, text) TO authenticated;
GRANT ALL ON FUNCTION public.results_eq(text, anyarray, text) TO service_role;


--
-- Name: FUNCTION results_eq(text, refcursor, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.results_eq(text, refcursor, text) TO anon;
GRANT ALL ON FUNCTION public.results_eq(text, refcursor, text) TO authenticated;
GRANT ALL ON FUNCTION public.results_eq(text, refcursor, text) TO service_role;


--
-- Name: FUNCTION results_eq(text, text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.results_eq(text, text, text) TO anon;
GRANT ALL ON FUNCTION public.results_eq(text, text, text) TO authenticated;
GRANT ALL ON FUNCTION public.results_eq(text, text, text) TO service_role;


--
-- Name: FUNCTION results_ne(refcursor, anyarray); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.results_ne(refcursor, anyarray) TO anon;
GRANT ALL ON FUNCTION public.results_ne(refcursor, anyarray) TO authenticated;
GRANT ALL ON FUNCTION public.results_ne(refcursor, anyarray) TO service_role;


--
-- Name: FUNCTION results_ne(refcursor, refcursor); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.results_ne(refcursor, refcursor) TO anon;
GRANT ALL ON FUNCTION public.results_ne(refcursor, refcursor) TO authenticated;
GRANT ALL ON FUNCTION public.results_ne(refcursor, refcursor) TO service_role;


--
-- Name: FUNCTION results_ne(refcursor, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.results_ne(refcursor, text) TO anon;
GRANT ALL ON FUNCTION public.results_ne(refcursor, text) TO authenticated;
GRANT ALL ON FUNCTION public.results_ne(refcursor, text) TO service_role;


--
-- Name: FUNCTION results_ne(text, anyarray); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.results_ne(text, anyarray) TO anon;
GRANT ALL ON FUNCTION public.results_ne(text, anyarray) TO authenticated;
GRANT ALL ON FUNCTION public.results_ne(text, anyarray) TO service_role;


--
-- Name: FUNCTION results_ne(text, refcursor); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.results_ne(text, refcursor) TO anon;
GRANT ALL ON FUNCTION public.results_ne(text, refcursor) TO authenticated;
GRANT ALL ON FUNCTION public.results_ne(text, refcursor) TO service_role;


--
-- Name: FUNCTION results_ne(text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.results_ne(text, text) TO anon;
GRANT ALL ON FUNCTION public.results_ne(text, text) TO authenticated;
GRANT ALL ON FUNCTION public.results_ne(text, text) TO service_role;


--
-- Name: FUNCTION results_ne(refcursor, anyarray, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.results_ne(refcursor, anyarray, text) TO anon;
GRANT ALL ON FUNCTION public.results_ne(refcursor, anyarray, text) TO authenticated;
GRANT ALL ON FUNCTION public.results_ne(refcursor, anyarray, text) TO service_role;


--
-- Name: FUNCTION results_ne(refcursor, refcursor, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.results_ne(refcursor, refcursor, text) TO anon;
GRANT ALL ON FUNCTION public.results_ne(refcursor, refcursor, text) TO authenticated;
GRANT ALL ON FUNCTION public.results_ne(refcursor, refcursor, text) TO service_role;


--
-- Name: FUNCTION results_ne(refcursor, text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.results_ne(refcursor, text, text) TO anon;
GRANT ALL ON FUNCTION public.results_ne(refcursor, text, text) TO authenticated;
GRANT ALL ON FUNCTION public.results_ne(refcursor, text, text) TO service_role;


--
-- Name: FUNCTION results_ne(text, anyarray, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.results_ne(text, anyarray, text) TO anon;
GRANT ALL ON FUNCTION public.results_ne(text, anyarray, text) TO authenticated;
GRANT ALL ON FUNCTION public.results_ne(text, anyarray, text) TO service_role;


--
-- Name: FUNCTION results_ne(text, refcursor, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.results_ne(text, refcursor, text) TO anon;
GRANT ALL ON FUNCTION public.results_ne(text, refcursor, text) TO authenticated;
GRANT ALL ON FUNCTION public.results_ne(text, refcursor, text) TO service_role;


--
-- Name: FUNCTION results_ne(text, text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.results_ne(text, text, text) TO anon;
GRANT ALL ON FUNCTION public.results_ne(text, text, text) TO authenticated;
GRANT ALL ON FUNCTION public.results_ne(text, text, text) TO service_role;


--
-- Name: FUNCTION roles_are(name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.roles_are(name[]) TO anon;
GRANT ALL ON FUNCTION public.roles_are(name[]) TO authenticated;
GRANT ALL ON FUNCTION public.roles_are(name[]) TO service_role;


--
-- Name: FUNCTION roles_are(name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.roles_are(name[], text) TO anon;
GRANT ALL ON FUNCTION public.roles_are(name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.roles_are(name[], text) TO service_role;


--
-- Name: FUNCTION row_eq(text, anyelement); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.row_eq(text, anyelement) TO anon;
GRANT ALL ON FUNCTION public.row_eq(text, anyelement) TO authenticated;
GRANT ALL ON FUNCTION public.row_eq(text, anyelement) TO service_role;


--
-- Name: FUNCTION row_eq(text, anyelement, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.row_eq(text, anyelement, text) TO anon;
GRANT ALL ON FUNCTION public.row_eq(text, anyelement, text) TO authenticated;
GRANT ALL ON FUNCTION public.row_eq(text, anyelement, text) TO service_role;


--
-- Name: FUNCTION rule_is_instead(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.rule_is_instead(name, name) TO anon;
GRANT ALL ON FUNCTION public.rule_is_instead(name, name) TO authenticated;
GRANT ALL ON FUNCTION public.rule_is_instead(name, name) TO service_role;


--
-- Name: FUNCTION rule_is_instead(name, name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.rule_is_instead(name, name, name) TO anon;
GRANT ALL ON FUNCTION public.rule_is_instead(name, name, name) TO authenticated;
GRANT ALL ON FUNCTION public.rule_is_instead(name, name, name) TO service_role;


--
-- Name: FUNCTION rule_is_instead(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.rule_is_instead(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.rule_is_instead(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.rule_is_instead(name, name, text) TO service_role;


--
-- Name: FUNCTION rule_is_instead(name, name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.rule_is_instead(name, name, name, text) TO anon;
GRANT ALL ON FUNCTION public.rule_is_instead(name, name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.rule_is_instead(name, name, name, text) TO service_role;


--
-- Name: FUNCTION rule_is_on(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.rule_is_on(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.rule_is_on(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.rule_is_on(name, name, text) TO service_role;


--
-- Name: FUNCTION rule_is_on(name, name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.rule_is_on(name, name, name, text) TO anon;
GRANT ALL ON FUNCTION public.rule_is_on(name, name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.rule_is_on(name, name, name, text) TO service_role;


--
-- Name: FUNCTION rule_is_on(name, name, text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.rule_is_on(name, name, text, text) TO anon;
GRANT ALL ON FUNCTION public.rule_is_on(name, name, text, text) TO authenticated;
GRANT ALL ON FUNCTION public.rule_is_on(name, name, text, text) TO service_role;


--
-- Name: FUNCTION rule_is_on(name, name, name, text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.rule_is_on(name, name, name, text, text) TO anon;
GRANT ALL ON FUNCTION public.rule_is_on(name, name, name, text, text) TO authenticated;
GRANT ALL ON FUNCTION public.rule_is_on(name, name, name, text, text) TO service_role;


--
-- Name: FUNCTION rules_are(name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.rules_are(name, name[]) TO anon;
GRANT ALL ON FUNCTION public.rules_are(name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public.rules_are(name, name[]) TO service_role;


--
-- Name: FUNCTION rules_are(name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.rules_are(name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.rules_are(name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.rules_are(name, name[], text) TO service_role;


--
-- Name: FUNCTION rules_are(name, name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.rules_are(name, name, name[]) TO anon;
GRANT ALL ON FUNCTION public.rules_are(name, name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public.rules_are(name, name, name[]) TO service_role;


--
-- Name: FUNCTION rules_are(name, name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.rules_are(name, name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.rules_are(name, name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.rules_are(name, name, name[], text) TO service_role;


--
-- Name: FUNCTION runtests(); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.runtests() TO anon;
GRANT ALL ON FUNCTION public.runtests() TO authenticated;
GRANT ALL ON FUNCTION public.runtests() TO service_role;


--
-- Name: FUNCTION runtests(name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.runtests(name) TO anon;
GRANT ALL ON FUNCTION public.runtests(name) TO authenticated;
GRANT ALL ON FUNCTION public.runtests(name) TO service_role;


--
-- Name: FUNCTION runtests(text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.runtests(text) TO anon;
GRANT ALL ON FUNCTION public.runtests(text) TO authenticated;
GRANT ALL ON FUNCTION public.runtests(text) TO service_role;


--
-- Name: FUNCTION runtests(name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.runtests(name, text) TO anon;
GRANT ALL ON FUNCTION public.runtests(name, text) TO authenticated;
GRANT ALL ON FUNCTION public.runtests(name, text) TO service_role;


--
-- Name: FUNCTION schema_owner_is(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.schema_owner_is(name, name) TO anon;
GRANT ALL ON FUNCTION public.schema_owner_is(name, name) TO authenticated;
GRANT ALL ON FUNCTION public.schema_owner_is(name, name) TO service_role;


--
-- Name: FUNCTION schema_owner_is(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.schema_owner_is(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.schema_owner_is(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.schema_owner_is(name, name, text) TO service_role;


--
-- Name: FUNCTION schema_privs_are(name, name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.schema_privs_are(name, name, name[]) TO anon;
GRANT ALL ON FUNCTION public.schema_privs_are(name, name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public.schema_privs_are(name, name, name[]) TO service_role;


--
-- Name: FUNCTION schema_privs_are(name, name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.schema_privs_are(name, name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.schema_privs_are(name, name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.schema_privs_are(name, name, name[], text) TO service_role;


--
-- Name: FUNCTION schemas_are(name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.schemas_are(name[]) TO anon;
GRANT ALL ON FUNCTION public.schemas_are(name[]) TO authenticated;
GRANT ALL ON FUNCTION public.schemas_are(name[]) TO service_role;


--
-- Name: FUNCTION schemas_are(name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.schemas_are(name[], text) TO anon;
GRANT ALL ON FUNCTION public.schemas_are(name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.schemas_are(name[], text) TO service_role;


--
-- Name: FUNCTION sequence_owner_is(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.sequence_owner_is(name, name) TO anon;
GRANT ALL ON FUNCTION public.sequence_owner_is(name, name) TO authenticated;
GRANT ALL ON FUNCTION public.sequence_owner_is(name, name) TO service_role;


--
-- Name: FUNCTION sequence_owner_is(name, name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.sequence_owner_is(name, name, name) TO anon;
GRANT ALL ON FUNCTION public.sequence_owner_is(name, name, name) TO authenticated;
GRANT ALL ON FUNCTION public.sequence_owner_is(name, name, name) TO service_role;


--
-- Name: FUNCTION sequence_owner_is(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.sequence_owner_is(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.sequence_owner_is(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.sequence_owner_is(name, name, text) TO service_role;


--
-- Name: FUNCTION sequence_owner_is(name, name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.sequence_owner_is(name, name, name, text) TO anon;
GRANT ALL ON FUNCTION public.sequence_owner_is(name, name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.sequence_owner_is(name, name, name, text) TO service_role;


--
-- Name: FUNCTION sequence_privs_are(name, name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.sequence_privs_are(name, name, name[]) TO anon;
GRANT ALL ON FUNCTION public.sequence_privs_are(name, name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public.sequence_privs_are(name, name, name[]) TO service_role;


--
-- Name: FUNCTION sequence_privs_are(name, name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.sequence_privs_are(name, name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.sequence_privs_are(name, name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.sequence_privs_are(name, name, name[], text) TO service_role;


--
-- Name: FUNCTION sequence_privs_are(name, name, name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.sequence_privs_are(name, name, name, name[]) TO anon;
GRANT ALL ON FUNCTION public.sequence_privs_are(name, name, name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public.sequence_privs_are(name, name, name, name[]) TO service_role;


--
-- Name: FUNCTION sequence_privs_are(name, name, name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.sequence_privs_are(name, name, name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.sequence_privs_are(name, name, name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.sequence_privs_are(name, name, name, name[], text) TO service_role;


--
-- Name: FUNCTION sequences_are(name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.sequences_are(name[]) TO anon;
GRANT ALL ON FUNCTION public.sequences_are(name[]) TO authenticated;
GRANT ALL ON FUNCTION public.sequences_are(name[]) TO service_role;


--
-- Name: FUNCTION sequences_are(name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.sequences_are(name[], text) TO anon;
GRANT ALL ON FUNCTION public.sequences_are(name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.sequences_are(name[], text) TO service_role;


--
-- Name: FUNCTION sequences_are(name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.sequences_are(name, name[]) TO anon;
GRANT ALL ON FUNCTION public.sequences_are(name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public.sequences_are(name, name[]) TO service_role;


--
-- Name: FUNCTION sequences_are(name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.sequences_are(name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.sequences_are(name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.sequences_are(name, name[], text) TO service_role;


--
-- Name: FUNCTION server_privs_are(name, name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.server_privs_are(name, name, name[]) TO anon;
GRANT ALL ON FUNCTION public.server_privs_are(name, name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public.server_privs_are(name, name, name[]) TO service_role;


--
-- Name: FUNCTION server_privs_are(name, name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.server_privs_are(name, name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.server_privs_are(name, name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.server_privs_are(name, name, name[], text) TO service_role;


--
-- Name: FUNCTION set_eq(text, anyarray); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.set_eq(text, anyarray) TO anon;
GRANT ALL ON FUNCTION public.set_eq(text, anyarray) TO authenticated;
GRANT ALL ON FUNCTION public.set_eq(text, anyarray) TO service_role;


--
-- Name: FUNCTION set_eq(text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.set_eq(text, text) TO anon;
GRANT ALL ON FUNCTION public.set_eq(text, text) TO authenticated;
GRANT ALL ON FUNCTION public.set_eq(text, text) TO service_role;


--
-- Name: FUNCTION set_eq(text, anyarray, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.set_eq(text, anyarray, text) TO anon;
GRANT ALL ON FUNCTION public.set_eq(text, anyarray, text) TO authenticated;
GRANT ALL ON FUNCTION public.set_eq(text, anyarray, text) TO service_role;


--
-- Name: FUNCTION set_eq(text, text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.set_eq(text, text, text) TO anon;
GRANT ALL ON FUNCTION public.set_eq(text, text, text) TO authenticated;
GRANT ALL ON FUNCTION public.set_eq(text, text, text) TO service_role;


--
-- Name: FUNCTION set_has(text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.set_has(text, text) TO anon;
GRANT ALL ON FUNCTION public.set_has(text, text) TO authenticated;
GRANT ALL ON FUNCTION public.set_has(text, text) TO service_role;


--
-- Name: FUNCTION set_has(text, text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.set_has(text, text, text) TO anon;
GRANT ALL ON FUNCTION public.set_has(text, text, text) TO authenticated;
GRANT ALL ON FUNCTION public.set_has(text, text, text) TO service_role;


--
-- Name: FUNCTION set_hasnt(text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.set_hasnt(text, text) TO anon;
GRANT ALL ON FUNCTION public.set_hasnt(text, text) TO authenticated;
GRANT ALL ON FUNCTION public.set_hasnt(text, text) TO service_role;


--
-- Name: FUNCTION set_hasnt(text, text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.set_hasnt(text, text, text) TO anon;
GRANT ALL ON FUNCTION public.set_hasnt(text, text, text) TO authenticated;
GRANT ALL ON FUNCTION public.set_hasnt(text, text, text) TO service_role;


--
-- Name: FUNCTION set_ne(text, anyarray); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.set_ne(text, anyarray) TO anon;
GRANT ALL ON FUNCTION public.set_ne(text, anyarray) TO authenticated;
GRANT ALL ON FUNCTION public.set_ne(text, anyarray) TO service_role;


--
-- Name: FUNCTION set_ne(text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.set_ne(text, text) TO anon;
GRANT ALL ON FUNCTION public.set_ne(text, text) TO authenticated;
GRANT ALL ON FUNCTION public.set_ne(text, text) TO service_role;


--
-- Name: FUNCTION set_ne(text, anyarray, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.set_ne(text, anyarray, text) TO anon;
GRANT ALL ON FUNCTION public.set_ne(text, anyarray, text) TO authenticated;
GRANT ALL ON FUNCTION public.set_ne(text, anyarray, text) TO service_role;


--
-- Name: FUNCTION set_ne(text, text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.set_ne(text, text, text) TO anon;
GRANT ALL ON FUNCTION public.set_ne(text, text, text) TO authenticated;
GRANT ALL ON FUNCTION public.set_ne(text, text, text) TO service_role;


--
-- Name: FUNCTION skip(integer); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.skip(integer) TO anon;
GRANT ALL ON FUNCTION public.skip(integer) TO authenticated;
GRANT ALL ON FUNCTION public.skip(integer) TO service_role;


--
-- Name: FUNCTION skip(text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.skip(text) TO anon;
GRANT ALL ON FUNCTION public.skip(text) TO authenticated;
GRANT ALL ON FUNCTION public.skip(text) TO service_role;


--
-- Name: FUNCTION skip(integer, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.skip(integer, text) TO anon;
GRANT ALL ON FUNCTION public.skip(integer, text) TO authenticated;
GRANT ALL ON FUNCTION public.skip(integer, text) TO service_role;


--
-- Name: FUNCTION skip(why text, how_many integer); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.skip(why text, how_many integer) TO anon;
GRANT ALL ON FUNCTION public.skip(why text, how_many integer) TO authenticated;
GRANT ALL ON FUNCTION public.skip(why text, how_many integer) TO service_role;


--
-- Name: FUNCTION table_owner_is(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.table_owner_is(name, name) TO anon;
GRANT ALL ON FUNCTION public.table_owner_is(name, name) TO authenticated;
GRANT ALL ON FUNCTION public.table_owner_is(name, name) TO service_role;


--
-- Name: FUNCTION table_owner_is(name, name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.table_owner_is(name, name, name) TO anon;
GRANT ALL ON FUNCTION public.table_owner_is(name, name, name) TO authenticated;
GRANT ALL ON FUNCTION public.table_owner_is(name, name, name) TO service_role;


--
-- Name: FUNCTION table_owner_is(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.table_owner_is(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.table_owner_is(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.table_owner_is(name, name, text) TO service_role;


--
-- Name: FUNCTION table_owner_is(name, name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.table_owner_is(name, name, name, text) TO anon;
GRANT ALL ON FUNCTION public.table_owner_is(name, name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.table_owner_is(name, name, name, text) TO service_role;


--
-- Name: FUNCTION table_privs_are(name, name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.table_privs_are(name, name, name[]) TO anon;
GRANT ALL ON FUNCTION public.table_privs_are(name, name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public.table_privs_are(name, name, name[]) TO service_role;


--
-- Name: FUNCTION table_privs_are(name, name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.table_privs_are(name, name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.table_privs_are(name, name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.table_privs_are(name, name, name[], text) TO service_role;


--
-- Name: FUNCTION table_privs_are(name, name, name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.table_privs_are(name, name, name, name[]) TO anon;
GRANT ALL ON FUNCTION public.table_privs_are(name, name, name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public.table_privs_are(name, name, name, name[]) TO service_role;


--
-- Name: FUNCTION table_privs_are(name, name, name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.table_privs_are(name, name, name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.table_privs_are(name, name, name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.table_privs_are(name, name, name, name[], text) TO service_role;


--
-- Name: FUNCTION tables_are(name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.tables_are(name[]) TO anon;
GRANT ALL ON FUNCTION public.tables_are(name[]) TO authenticated;
GRANT ALL ON FUNCTION public.tables_are(name[]) TO service_role;


--
-- Name: FUNCTION tables_are(name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.tables_are(name[], text) TO anon;
GRANT ALL ON FUNCTION public.tables_are(name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.tables_are(name[], text) TO service_role;


--
-- Name: FUNCTION tables_are(name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.tables_are(name, name[]) TO anon;
GRANT ALL ON FUNCTION public.tables_are(name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public.tables_are(name, name[]) TO service_role;


--
-- Name: FUNCTION tables_are(name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.tables_are(name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.tables_are(name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.tables_are(name, name[], text) TO service_role;


--
-- Name: FUNCTION tablespace_owner_is(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.tablespace_owner_is(name, name) TO anon;
GRANT ALL ON FUNCTION public.tablespace_owner_is(name, name) TO authenticated;
GRANT ALL ON FUNCTION public.tablespace_owner_is(name, name) TO service_role;


--
-- Name: FUNCTION tablespace_owner_is(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.tablespace_owner_is(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.tablespace_owner_is(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.tablespace_owner_is(name, name, text) TO service_role;


--
-- Name: FUNCTION tablespace_privs_are(name, name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.tablespace_privs_are(name, name, name[]) TO anon;
GRANT ALL ON FUNCTION public.tablespace_privs_are(name, name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public.tablespace_privs_are(name, name, name[]) TO service_role;


--
-- Name: FUNCTION tablespace_privs_are(name, name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.tablespace_privs_are(name, name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.tablespace_privs_are(name, name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.tablespace_privs_are(name, name, name[], text) TO service_role;


--
-- Name: FUNCTION tablespaces_are(name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.tablespaces_are(name[]) TO anon;
GRANT ALL ON FUNCTION public.tablespaces_are(name[]) TO authenticated;
GRANT ALL ON FUNCTION public.tablespaces_are(name[]) TO service_role;


--
-- Name: FUNCTION tablespaces_are(name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.tablespaces_are(name[], text) TO anon;
GRANT ALL ON FUNCTION public.tablespaces_are(name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.tablespaces_are(name[], text) TO service_role;


--
-- Name: FUNCTION throws_ilike(text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.throws_ilike(text, text) TO anon;
GRANT ALL ON FUNCTION public.throws_ilike(text, text) TO authenticated;
GRANT ALL ON FUNCTION public.throws_ilike(text, text) TO service_role;


--
-- Name: FUNCTION throws_ilike(text, text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.throws_ilike(text, text, text) TO anon;
GRANT ALL ON FUNCTION public.throws_ilike(text, text, text) TO authenticated;
GRANT ALL ON FUNCTION public.throws_ilike(text, text, text) TO service_role;


--
-- Name: FUNCTION throws_imatching(text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.throws_imatching(text, text) TO anon;
GRANT ALL ON FUNCTION public.throws_imatching(text, text) TO authenticated;
GRANT ALL ON FUNCTION public.throws_imatching(text, text) TO service_role;


--
-- Name: FUNCTION throws_imatching(text, text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.throws_imatching(text, text, text) TO anon;
GRANT ALL ON FUNCTION public.throws_imatching(text, text, text) TO authenticated;
GRANT ALL ON FUNCTION public.throws_imatching(text, text, text) TO service_role;


--
-- Name: FUNCTION throws_like(text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.throws_like(text, text) TO anon;
GRANT ALL ON FUNCTION public.throws_like(text, text) TO authenticated;
GRANT ALL ON FUNCTION public.throws_like(text, text) TO service_role;


--
-- Name: FUNCTION throws_like(text, text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.throws_like(text, text, text) TO anon;
GRANT ALL ON FUNCTION public.throws_like(text, text, text) TO authenticated;
GRANT ALL ON FUNCTION public.throws_like(text, text, text) TO service_role;


--
-- Name: FUNCTION throws_matching(text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.throws_matching(text, text) TO anon;
GRANT ALL ON FUNCTION public.throws_matching(text, text) TO authenticated;
GRANT ALL ON FUNCTION public.throws_matching(text, text) TO service_role;


--
-- Name: FUNCTION throws_matching(text, text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.throws_matching(text, text, text) TO anon;
GRANT ALL ON FUNCTION public.throws_matching(text, text, text) TO authenticated;
GRANT ALL ON FUNCTION public.throws_matching(text, text, text) TO service_role;


--
-- Name: FUNCTION throws_ok(text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.throws_ok(text) TO anon;
GRANT ALL ON FUNCTION public.throws_ok(text) TO authenticated;
GRANT ALL ON FUNCTION public.throws_ok(text) TO service_role;


--
-- Name: FUNCTION throws_ok(text, integer); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.throws_ok(text, integer) TO anon;
GRANT ALL ON FUNCTION public.throws_ok(text, integer) TO authenticated;
GRANT ALL ON FUNCTION public.throws_ok(text, integer) TO service_role;


--
-- Name: FUNCTION throws_ok(text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.throws_ok(text, text) TO anon;
GRANT ALL ON FUNCTION public.throws_ok(text, text) TO authenticated;
GRANT ALL ON FUNCTION public.throws_ok(text, text) TO service_role;


--
-- Name: FUNCTION throws_ok(text, integer, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.throws_ok(text, integer, text) TO anon;
GRANT ALL ON FUNCTION public.throws_ok(text, integer, text) TO authenticated;
GRANT ALL ON FUNCTION public.throws_ok(text, integer, text) TO service_role;


--
-- Name: FUNCTION throws_ok(text, text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.throws_ok(text, text, text) TO anon;
GRANT ALL ON FUNCTION public.throws_ok(text, text, text) TO authenticated;
GRANT ALL ON FUNCTION public.throws_ok(text, text, text) TO service_role;


--
-- Name: FUNCTION throws_ok(text, character, text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.throws_ok(text, character, text, text) TO anon;
GRANT ALL ON FUNCTION public.throws_ok(text, character, text, text) TO authenticated;
GRANT ALL ON FUNCTION public.throws_ok(text, character, text, text) TO service_role;


--
-- Name: FUNCTION throws_ok(text, integer, text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.throws_ok(text, integer, text, text) TO anon;
GRANT ALL ON FUNCTION public.throws_ok(text, integer, text, text) TO authenticated;
GRANT ALL ON FUNCTION public.throws_ok(text, integer, text, text) TO service_role;


--
-- Name: FUNCTION todo(how_many integer); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.todo(how_many integer) TO anon;
GRANT ALL ON FUNCTION public.todo(how_many integer) TO authenticated;
GRANT ALL ON FUNCTION public.todo(how_many integer) TO service_role;


--
-- Name: FUNCTION todo(why text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.todo(why text) TO anon;
GRANT ALL ON FUNCTION public.todo(why text) TO authenticated;
GRANT ALL ON FUNCTION public.todo(why text) TO service_role;


--
-- Name: FUNCTION todo(how_many integer, why text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.todo(how_many integer, why text) TO anon;
GRANT ALL ON FUNCTION public.todo(how_many integer, why text) TO authenticated;
GRANT ALL ON FUNCTION public.todo(how_many integer, why text) TO service_role;


--
-- Name: FUNCTION todo(why text, how_many integer); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.todo(why text, how_many integer) TO anon;
GRANT ALL ON FUNCTION public.todo(why text, how_many integer) TO authenticated;
GRANT ALL ON FUNCTION public.todo(why text, how_many integer) TO service_role;


--
-- Name: FUNCTION todo_end(); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.todo_end() TO anon;
GRANT ALL ON FUNCTION public.todo_end() TO authenticated;
GRANT ALL ON FUNCTION public.todo_end() TO service_role;


--
-- Name: FUNCTION todo_start(); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.todo_start() TO anon;
GRANT ALL ON FUNCTION public.todo_start() TO authenticated;
GRANT ALL ON FUNCTION public.todo_start() TO service_role;


--
-- Name: FUNCTION todo_start(text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.todo_start(text) TO anon;
GRANT ALL ON FUNCTION public.todo_start(text) TO authenticated;
GRANT ALL ON FUNCTION public.todo_start(text) TO service_role;


--
-- Name: FUNCTION trigger_is(name, name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.trigger_is(name, name, name) TO anon;
GRANT ALL ON FUNCTION public.trigger_is(name, name, name) TO authenticated;
GRANT ALL ON FUNCTION public.trigger_is(name, name, name) TO service_role;


--
-- Name: FUNCTION trigger_is(name, name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.trigger_is(name, name, name, text) TO anon;
GRANT ALL ON FUNCTION public.trigger_is(name, name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.trigger_is(name, name, name, text) TO service_role;


--
-- Name: FUNCTION trigger_is(name, name, name, name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.trigger_is(name, name, name, name, name) TO anon;
GRANT ALL ON FUNCTION public.trigger_is(name, name, name, name, name) TO authenticated;
GRANT ALL ON FUNCTION public.trigger_is(name, name, name, name, name) TO service_role;


--
-- Name: FUNCTION trigger_is(name, name, name, name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.trigger_is(name, name, name, name, name, text) TO anon;
GRANT ALL ON FUNCTION public.trigger_is(name, name, name, name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.trigger_is(name, name, name, name, name, text) TO service_role;


--
-- Name: FUNCTION triggers_are(name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.triggers_are(name, name[]) TO anon;
GRANT ALL ON FUNCTION public.triggers_are(name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public.triggers_are(name, name[]) TO service_role;


--
-- Name: FUNCTION triggers_are(name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.triggers_are(name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.triggers_are(name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.triggers_are(name, name[], text) TO service_role;


--
-- Name: FUNCTION triggers_are(name, name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.triggers_are(name, name, name[]) TO anon;
GRANT ALL ON FUNCTION public.triggers_are(name, name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public.triggers_are(name, name, name[]) TO service_role;


--
-- Name: FUNCTION triggers_are(name, name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.triggers_are(name, name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.triggers_are(name, name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.triggers_are(name, name, name[], text) TO service_role;


--
-- Name: FUNCTION type_owner_is(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.type_owner_is(name, name) TO anon;
GRANT ALL ON FUNCTION public.type_owner_is(name, name) TO authenticated;
GRANT ALL ON FUNCTION public.type_owner_is(name, name) TO service_role;


--
-- Name: FUNCTION type_owner_is(name, name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.type_owner_is(name, name, name) TO anon;
GRANT ALL ON FUNCTION public.type_owner_is(name, name, name) TO authenticated;
GRANT ALL ON FUNCTION public.type_owner_is(name, name, name) TO service_role;


--
-- Name: FUNCTION type_owner_is(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.type_owner_is(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.type_owner_is(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.type_owner_is(name, name, text) TO service_role;


--
-- Name: FUNCTION type_owner_is(name, name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.type_owner_is(name, name, name, text) TO anon;
GRANT ALL ON FUNCTION public.type_owner_is(name, name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.type_owner_is(name, name, name, text) TO service_role;


--
-- Name: FUNCTION types_are(name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.types_are(name[]) TO anon;
GRANT ALL ON FUNCTION public.types_are(name[]) TO authenticated;
GRANT ALL ON FUNCTION public.types_are(name[]) TO service_role;


--
-- Name: FUNCTION types_are(name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.types_are(name[], text) TO anon;
GRANT ALL ON FUNCTION public.types_are(name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.types_are(name[], text) TO service_role;


--
-- Name: FUNCTION types_are(name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.types_are(name, name[]) TO anon;
GRANT ALL ON FUNCTION public.types_are(name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public.types_are(name, name[]) TO service_role;


--
-- Name: FUNCTION types_are(name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.types_are(name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.types_are(name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.types_are(name, name[], text) TO service_role;


--
-- Name: FUNCTION unalike(anyelement, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.unalike(anyelement, text) TO anon;
GRANT ALL ON FUNCTION public.unalike(anyelement, text) TO authenticated;
GRANT ALL ON FUNCTION public.unalike(anyelement, text) TO service_role;


--
-- Name: FUNCTION unalike(anyelement, text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.unalike(anyelement, text, text) TO anon;
GRANT ALL ON FUNCTION public.unalike(anyelement, text, text) TO authenticated;
GRANT ALL ON FUNCTION public.unalike(anyelement, text, text) TO service_role;


--
-- Name: FUNCTION unialike(anyelement, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.unialike(anyelement, text) TO anon;
GRANT ALL ON FUNCTION public.unialike(anyelement, text) TO authenticated;
GRANT ALL ON FUNCTION public.unialike(anyelement, text) TO service_role;


--
-- Name: FUNCTION unialike(anyelement, text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.unialike(anyelement, text, text) TO anon;
GRANT ALL ON FUNCTION public.unialike(anyelement, text, text) TO authenticated;
GRANT ALL ON FUNCTION public.unialike(anyelement, text, text) TO service_role;


--
-- Name: FUNCTION update_updated_at_column(); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.update_updated_at_column() TO anon;
GRANT ALL ON FUNCTION public.update_updated_at_column() TO authenticated;
GRANT ALL ON FUNCTION public.update_updated_at_column() TO service_role;


--
-- Name: FUNCTION users_are(name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.users_are(name[]) TO anon;
GRANT ALL ON FUNCTION public.users_are(name[]) TO authenticated;
GRANT ALL ON FUNCTION public.users_are(name[]) TO service_role;


--
-- Name: FUNCTION users_are(name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.users_are(name[], text) TO anon;
GRANT ALL ON FUNCTION public.users_are(name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.users_are(name[], text) TO service_role;


--
-- Name: FUNCTION uuid_generate_v1(); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.uuid_generate_v1() TO anon;
GRANT ALL ON FUNCTION public.uuid_generate_v1() TO authenticated;
GRANT ALL ON FUNCTION public.uuid_generate_v1() TO service_role;


--
-- Name: FUNCTION uuid_generate_v1mc(); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.uuid_generate_v1mc() TO anon;
GRANT ALL ON FUNCTION public.uuid_generate_v1mc() TO authenticated;
GRANT ALL ON FUNCTION public.uuid_generate_v1mc() TO service_role;


--
-- Name: FUNCTION uuid_generate_v3(namespace uuid, name text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.uuid_generate_v3(namespace uuid, name text) TO anon;
GRANT ALL ON FUNCTION public.uuid_generate_v3(namespace uuid, name text) TO authenticated;
GRANT ALL ON FUNCTION public.uuid_generate_v3(namespace uuid, name text) TO service_role;


--
-- Name: FUNCTION uuid_generate_v4(); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.uuid_generate_v4() TO anon;
GRANT ALL ON FUNCTION public.uuid_generate_v4() TO authenticated;
GRANT ALL ON FUNCTION public.uuid_generate_v4() TO service_role;


--
-- Name: FUNCTION uuid_generate_v5(namespace uuid, name text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.uuid_generate_v5(namespace uuid, name text) TO anon;
GRANT ALL ON FUNCTION public.uuid_generate_v5(namespace uuid, name text) TO authenticated;
GRANT ALL ON FUNCTION public.uuid_generate_v5(namespace uuid, name text) TO service_role;


--
-- Name: FUNCTION uuid_nil(); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.uuid_nil() TO anon;
GRANT ALL ON FUNCTION public.uuid_nil() TO authenticated;
GRANT ALL ON FUNCTION public.uuid_nil() TO service_role;


--
-- Name: FUNCTION uuid_ns_dns(); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.uuid_ns_dns() TO anon;
GRANT ALL ON FUNCTION public.uuid_ns_dns() TO authenticated;
GRANT ALL ON FUNCTION public.uuid_ns_dns() TO service_role;


--
-- Name: FUNCTION uuid_ns_oid(); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.uuid_ns_oid() TO anon;
GRANT ALL ON FUNCTION public.uuid_ns_oid() TO authenticated;
GRANT ALL ON FUNCTION public.uuid_ns_oid() TO service_role;


--
-- Name: FUNCTION uuid_ns_url(); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.uuid_ns_url() TO anon;
GRANT ALL ON FUNCTION public.uuid_ns_url() TO authenticated;
GRANT ALL ON FUNCTION public.uuid_ns_url() TO service_role;


--
-- Name: FUNCTION uuid_ns_x500(); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.uuid_ns_x500() TO anon;
GRANT ALL ON FUNCTION public.uuid_ns_x500() TO authenticated;
GRANT ALL ON FUNCTION public.uuid_ns_x500() TO service_role;


--
-- Name: FUNCTION view_owner_is(name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.view_owner_is(name, name) TO anon;
GRANT ALL ON FUNCTION public.view_owner_is(name, name) TO authenticated;
GRANT ALL ON FUNCTION public.view_owner_is(name, name) TO service_role;


--
-- Name: FUNCTION view_owner_is(name, name, name); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.view_owner_is(name, name, name) TO anon;
GRANT ALL ON FUNCTION public.view_owner_is(name, name, name) TO authenticated;
GRANT ALL ON FUNCTION public.view_owner_is(name, name, name) TO service_role;


--
-- Name: FUNCTION view_owner_is(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.view_owner_is(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.view_owner_is(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.view_owner_is(name, name, text) TO service_role;


--
-- Name: FUNCTION view_owner_is(name, name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.view_owner_is(name, name, name, text) TO anon;
GRANT ALL ON FUNCTION public.view_owner_is(name, name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.view_owner_is(name, name, name, text) TO service_role;


--
-- Name: FUNCTION views_are(name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.views_are(name[]) TO anon;
GRANT ALL ON FUNCTION public.views_are(name[]) TO authenticated;
GRANT ALL ON FUNCTION public.views_are(name[]) TO service_role;


--
-- Name: FUNCTION views_are(name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.views_are(name[], text) TO anon;
GRANT ALL ON FUNCTION public.views_are(name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.views_are(name[], text) TO service_role;


--
-- Name: FUNCTION views_are(name, name[]); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.views_are(name, name[]) TO anon;
GRANT ALL ON FUNCTION public.views_are(name, name[]) TO authenticated;
GRANT ALL ON FUNCTION public.views_are(name, name[]) TO service_role;


--
-- Name: FUNCTION views_are(name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.views_are(name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.views_are(name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.views_are(name, name[], text) TO service_role;


--
-- Name: FUNCTION volatility_is(name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.volatility_is(name, text) TO anon;
GRANT ALL ON FUNCTION public.volatility_is(name, text) TO authenticated;
GRANT ALL ON FUNCTION public.volatility_is(name, text) TO service_role;


--
-- Name: FUNCTION volatility_is(name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.volatility_is(name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.volatility_is(name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.volatility_is(name, name[], text) TO service_role;


--
-- Name: FUNCTION volatility_is(name, name, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.volatility_is(name, name, text) TO anon;
GRANT ALL ON FUNCTION public.volatility_is(name, name, text) TO authenticated;
GRANT ALL ON FUNCTION public.volatility_is(name, name, text) TO service_role;


--
-- Name: FUNCTION volatility_is(name, text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.volatility_is(name, text, text) TO anon;
GRANT ALL ON FUNCTION public.volatility_is(name, text, text) TO authenticated;
GRANT ALL ON FUNCTION public.volatility_is(name, text, text) TO service_role;


--
-- Name: FUNCTION volatility_is(name, name[], text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.volatility_is(name, name[], text, text) TO anon;
GRANT ALL ON FUNCTION public.volatility_is(name, name[], text, text) TO authenticated;
GRANT ALL ON FUNCTION public.volatility_is(name, name[], text, text) TO service_role;


--
-- Name: FUNCTION volatility_is(name, name, name[], text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.volatility_is(name, name, name[], text) TO anon;
GRANT ALL ON FUNCTION public.volatility_is(name, name, name[], text) TO authenticated;
GRANT ALL ON FUNCTION public.volatility_is(name, name, name[], text) TO service_role;


--
-- Name: FUNCTION volatility_is(name, name, text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.volatility_is(name, name, text, text) TO anon;
GRANT ALL ON FUNCTION public.volatility_is(name, name, text, text) TO authenticated;
GRANT ALL ON FUNCTION public.volatility_is(name, name, text, text) TO service_role;


--
-- Name: FUNCTION volatility_is(name, name, name[], text, text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.volatility_is(name, name, name[], text, text) TO anon;
GRANT ALL ON FUNCTION public.volatility_is(name, name, name[], text, text) TO authenticated;
GRANT ALL ON FUNCTION public.volatility_is(name, name, name[], text, text) TO service_role;


--
-- Name: TABLE users; Type: ACL; Schema: auth; Owner: postgres
--

GRANT ALL ON TABLE auth.users TO authenticated;
GRANT ALL ON TABLE auth.users TO anon;
GRANT ALL ON TABLE auth.users TO service_role;


--
-- Name: TABLE activities; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.activities TO anon;
GRANT ALL ON TABLE public.activities TO authenticated;
GRANT ALL ON TABLE public.activities TO service_role;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.activities TO ml_api_worker;


--
-- Name: TABLE activity_questions; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.activity_questions TO anon;
GRANT ALL ON TABLE public.activity_questions TO authenticated;
GRANT ALL ON TABLE public.activity_questions TO service_role;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.activity_questions TO ml_api_worker;


--
-- Name: TABLE activity_sections; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.activity_sections TO ml_api_worker;


--
-- Name: TABLE answer_events; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT,REFERENCES,TRIGGER,TRUNCATE ON TABLE public.answer_events TO anon;
GRANT SELECT,INSERT,REFERENCES,TRIGGER,TRUNCATE ON TABLE public.answer_events TO authenticated;
GRANT ALL ON TABLE public.answer_events TO service_role;
GRANT SELECT,INSERT ON TABLE public.answer_events TO ml_api_worker;


--
-- Name: TABLE auth_recovery_pins; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.auth_recovery_pins TO anon;
GRANT ALL ON TABLE public.auth_recovery_pins TO authenticated;
GRANT ALL ON TABLE public.auth_recovery_pins TO service_role;


--
-- Name: TABLE content_exposure_events; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT ON TABLE public.content_exposure_events TO authenticated;
GRANT SELECT,INSERT ON TABLE public.content_exposure_events TO ml_api_worker;


--
-- Name: TABLE content_generation_jobs; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.content_generation_jobs TO authenticated;
GRANT ALL ON TABLE public.content_generation_jobs TO service_role;
GRANT ALL ON TABLE public.content_generation_jobs TO anon;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.content_generation_jobs TO ml_api_worker;


--
-- Name: TABLE courses; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.courses TO anon;
GRANT ALL ON TABLE public.courses TO authenticated;
GRANT ALL ON TABLE public.courses TO service_role;
GRANT SELECT ON TABLE public.courses TO ml_api_worker;


--
-- Name: TABLE enrollments; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.enrollments TO anon;
GRANT ALL ON TABLE public.enrollments TO authenticated;
GRANT ALL ON TABLE public.enrollments TO service_role;
GRANT SELECT ON TABLE public.enrollments TO ml_api_worker;


--
-- Name: TABLE knowledge_components; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.knowledge_components TO anon;
GRANT ALL ON TABLE public.knowledge_components TO authenticated;
GRANT ALL ON TABLE public.knowledge_components TO service_role;
GRANT SELECT ON TABLE public.knowledge_components TO ml_api_worker;


--
-- Name: TABLE microcontents; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.microcontents TO anon;
GRANT ALL ON TABLE public.microcontents TO authenticated;
GRANT ALL ON TABLE public.microcontents TO service_role;


--
-- Name: TABLE model_versions; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.model_versions TO anon;
GRANT ALL ON TABLE public.model_versions TO authenticated;
GRANT ALL ON TABLE public.model_versions TO service_role;
GRANT SELECT ON TABLE public.model_versions TO ml_api_worker;


--
-- Name: TABLE notifications; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE ON TABLE public.notifications TO authenticated;
GRANT ALL ON TABLE public.notifications TO service_role;
GRANT ALL ON TABLE public.notifications TO anon;


--
-- Name: COLUMN notifications.read_at; Type: ACL; Schema: public; Owner: postgres
--

GRANT UPDATE(read_at) ON TABLE public.notifications TO authenticated;


--
-- Name: TABLE pg_all_foreign_keys; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.pg_all_foreign_keys TO authenticated;
GRANT ALL ON TABLE public.pg_all_foreign_keys TO anon;
GRANT ALL ON TABLE public.pg_all_foreign_keys TO service_role;


--
-- Name: TABLE predictions; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.predictions TO anon;
GRANT ALL ON TABLE public.predictions TO authenticated;
GRANT ALL ON TABLE public.predictions TO service_role;
GRANT SELECT,INSERT ON TABLE public.predictions TO ml_api_worker;


--
-- Name: TABLE profiles; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.profiles TO anon;
GRANT ALL ON TABLE public.profiles TO authenticated;
GRANT ALL ON TABLE public.profiles TO service_role;
GRANT SELECT ON TABLE public.profiles TO ml_api_worker;


--
-- Name: TABLE question_drafts; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.question_drafts TO authenticated;
GRANT ALL ON TABLE public.question_drafts TO service_role;
GRANT ALL ON TABLE public.question_drafts TO anon;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.question_drafts TO ml_api_worker;


--
-- Name: TABLE question_options; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.question_options TO anon;
GRANT ALL ON TABLE public.question_options TO authenticated;
GRANT ALL ON TABLE public.question_options TO service_role;
GRANT SELECT,INSERT,UPDATE ON TABLE public.question_options TO ml_api_worker;


--
-- Name: TABLE questions; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.questions TO anon;
GRANT ALL ON TABLE public.questions TO authenticated;
GRANT ALL ON TABLE public.questions TO service_role;
GRANT SELECT,INSERT,UPDATE ON TABLE public.questions TO ml_api_worker;


--
-- Name: TABLE quiz_attempts; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.quiz_attempts TO anon;
GRANT ALL ON TABLE public.quiz_attempts TO authenticated;
GRANT ALL ON TABLE public.quiz_attempts TO service_role;
GRANT SELECT,INSERT,UPDATE ON TABLE public.quiz_attempts TO ml_api_worker;


--
-- Name: TABLE recommendations; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.recommendations TO anon;
GRANT ALL ON TABLE public.recommendations TO authenticated;
GRANT ALL ON TABLE public.recommendations TO service_role;
GRANT SELECT,INSERT,UPDATE ON TABLE public.recommendations TO ml_api_worker;


--
-- Name: TABLE review_assignments; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.review_assignments TO anon;
GRANT ALL ON TABLE public.review_assignments TO authenticated;
GRANT ALL ON TABLE public.review_assignments TO service_role;


--
-- Name: TABLE sections; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.sections TO anon;
GRANT ALL ON TABLE public.sections TO authenticated;
GRANT ALL ON TABLE public.sections TO service_role;
GRANT SELECT ON TABLE public.sections TO ml_api_worker;


--
-- Name: TABLE student_knowledge_states; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.student_knowledge_states TO anon;
GRANT ALL ON TABLE public.student_knowledge_states TO authenticated;
GRANT ALL ON TABLE public.student_knowledge_states TO service_role;


--
-- Name: TABLE student_metrics; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.student_metrics TO anon;
GRANT ALL ON TABLE public.student_metrics TO authenticated;
GRANT ALL ON TABLE public.student_metrics TO service_role;


--
-- Name: TABLE tap_funky; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.tap_funky TO authenticated;
GRANT ALL ON TABLE public.tap_funky TO anon;
GRANT ALL ON TABLE public.tap_funky TO service_role;


--
-- Name: TABLE tenants; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.tenants TO anon;
GRANT ALL ON TABLE public.tenants TO authenticated;
GRANT ALL ON TABLE public.tenants TO service_role;
GRANT SELECT ON TABLE public.tenants TO ml_api_worker;


--
-- Name: TABLE units; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.units TO anon;
GRANT ALL ON TABLE public.units TO authenticated;
GRANT ALL ON TABLE public.units TO service_role;
GRANT SELECT ON TABLE public.units TO ml_api_worker;


--
-- Name: TABLE buckets; Type: ACL; Schema: storage; Owner: postgres
--

GRANT ALL ON TABLE storage.buckets TO authenticated;
GRANT ALL ON TABLE storage.buckets TO anon;
GRANT ALL ON TABLE storage.buckets TO service_role;


--
-- Name: TABLE objects; Type: ACL; Schema: storage; Owner: postgres
--

GRANT ALL ON TABLE storage.objects TO authenticated;
GRANT ALL ON TABLE storage.objects TO anon;
GRANT ALL ON TABLE storage.objects TO service_role;


--
-- PostgreSQL database dump complete
--

\unrestrict BJHHdFsjcRRncAbU1Q3Ao5xRJTZR3oK8NtXBwVOf1bAjimlh0U3642WvA84cvNj

