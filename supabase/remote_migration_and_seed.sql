-- ============================================================================
-- PLATAFORMA DE MICROAPRENDIZAJE ADAPTATIVO (NEXO) — MIGRACIÓN Y SEED REMOTO
-- ============================================================================
-- Ejecutar en Supabase Dashboard: SQL Editor -> New Query -> Run
-- O ejecutar via script: python scripts/migrate_remote.py
--
-- Contenido:
--  0. Reparación de auth.users (elimina NULLs que provocan 500 en GoTrue)
--  1. Migración 2: Generación de contenido, question_drafts y notificaciones
--  2. Migración 3: Leases e idempotencia
--  3. Migración 4: Hardening de estados
--  4. Migración 5: Editor de preguntas docente
--  5. Migración 6: Flujo de aprendizaje y answer_events inmutables (activity_sections)
--  6. Migración 7: Eventos de exposición de contenido (content_exposure_events)
--  7. Migración 8: Recomendaciones y predicciones
--  8. Seed base: Tenant San Agustín, docente Ana, estudiante Lucía
--  9. Seed demo: 10 estudiantes seudonimizados, 5 KCs, 15 preguntas,
--                 120 intentos, 360 respuestas, 60 exposiciones, 30 recomendaciones
-- ============================================================================

-- ============================================================================
-- 0. REPARACIÓN DE SUPABASE AUTH (Eliminar valores NULL en auth.users)
--    Resuelve el error HTTP 500: Database error querying schema (GoTrue v2.197+)
-- ============================================================================
DO $$ BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.schemata WHERE schema_name = 'auth') THEN
        UPDATE auth.users
        SET confirmation_token = COALESCE(confirmation_token, ''),
            recovery_token = COALESCE(recovery_token, ''),
            email_change = COALESCE(email_change, ''),
            email_change_token_new = COALESCE(email_change_token_new, ''),
            email_change_token_current = COALESCE(email_change_token_current, ''),
            phone_change = COALESCE(phone_change, ''),
            phone_change_token = COALESCE(phone_change_token, ''),
            reauthentication_token = COALESCE(reauthentication_token, '')
        WHERE confirmation_token IS NULL
           OR recovery_token IS NULL
           OR email_change IS NULL
           OR email_change_token_new IS NULL
           OR email_change_token_current IS NULL
           OR phone_change IS NULL
           OR phone_change_token IS NULL
           OR reauthentication_token IS NULL;
    END IF;
END $$;

-- >>> MIGRACIÓN: 20261102180000_content_generation_quizzes_notifications.sql >>>
-- ============================================================================
-- PLATAFORMA DE MICROAPRENDIZAJE ADAPTATIVO
-- MIGRACIÓN INCREMENTAL: Persistencia Segura para ADR-0004
-- Ingesta Documental, Borradores, Notificaciones In-App y Storage Privado
-- Version: 20261102180000
-- ============================================================================

-- 1. Nuevos Tipos Enumerados (ENUMs)
DO $$ BEGIN
    CREATE TYPE generation_job_status_enum AS ENUM (
        'queued',
        'processing',
        'review_required',
        'approved',
        'rejected',
        'failed'
    );
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE draft_status_enum AS ENUM (
        'draft',
        'edited',
        'approved',
        'rejected'
    );
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE notification_type_enum AS ENUM (
        'review_reminder',
        'new_assignment',
        'system_notice'
    );
EXCEPTION WHEN duplicate_object THEN null;
END $$;

-- 2. Funciones de Autorización y Triggers
CREATE OR REPLACE FUNCTION is_teacher_of_course(p_course_id UUID)
RETURNS BOOLEAN LANGUAGE sql STABLE SECURITY DEFINER SET search_path = '' AS $$
    SELECT EXISTS (
        SELECT 1 
        FROM public.sections s
        WHERE s.course_id = p_course_id
          AND s.teacher_id = (SELECT auth.uid())
          AND s.tenant_id = (SELECT public.current_user_tenant_id())
    );
$$;

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$;

-- 3. Tabla: content_generation_jobs
CREATE TABLE IF NOT EXISTS content_generation_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL DEFAULT current_user_tenant_id() REFERENCES tenants(id) ON DELETE CASCADE,
    course_id UUID REFERENCES courses(id) ON DELETE RESTRICT,
    unit_id UUID REFERENCES units(id) ON DELETE SET NULL,
    created_by UUID NOT NULL DEFAULT auth.uid() REFERENCES profiles(id) ON DELETE RESTRICT,
    storage_bucket TEXT NOT NULL DEFAULT 'teacher-materials' CHECK (storage_bucket = 'teacher-materials'),
    storage_path TEXT NOT NULL,
    original_filename TEXT NOT NULL,
    mime_type TEXT NOT NULL CHECK (mime_type IN ('application/pdf', 'application/vnd.openxmlformats-officedocument.presentationml.presentation')),
    file_size_bytes INTEGER NOT NULL CHECK (file_size_bytes > 0 AND file_size_bytes <= 31457280), -- Máximo 30 MB
    file_checksum TEXT NOT NULL,
    status generation_job_status_enum NOT NULL DEFAULT 'queued',
    provider TEXT NOT NULL CHECK (char_length(provider) > 0),
    model_id TEXT NOT NULL CHECK (char_length(model_id) > 0),
    prompt_version TEXT NOT NULL DEFAULT 'v1',
    error_code TEXT,
    error_message_safe TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_content_gen_jobs_storage_path_tenant CHECK (split_part(storage_path, '/', 1) = tenant_id::text)
);

DO $$ BEGIN
    ALTER TABLE content_generation_jobs
        ADD CONSTRAINT chk_content_gen_jobs_storage_path_tenant
        CHECK (split_part(storage_path, '/', 1) = tenant_id::text);
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    ALTER TABLE content_generation_jobs
        ADD CONSTRAINT chk_content_gen_jobs_storage_bucket
        CHECK (storage_bucket = 'teacher-materials');
EXCEPTION WHEN duplicate_object THEN null;
END $$;

-- 4. Tabla: question_drafts (Cuarentena de Borradores de Preguntas)
CREATE TABLE IF NOT EXISTS question_drafts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL DEFAULT current_user_tenant_id() REFERENCES tenants(id) ON DELETE CASCADE,
    generation_job_id UUID NOT NULL REFERENCES content_generation_jobs(id) ON DELETE CASCADE,
    knowledge_component_id UUID REFERENCES knowledge_components(id) ON DELETE SET NULL,
    suggested_kc_name TEXT NOT NULL,
    question_text TEXT NOT NULL,
    explanation TEXT NOT NULL,
    options JSONB NOT NULL,
    suggested_difficulty NUMERIC(4,3) DEFAULT 0.500 CHECK (suggested_difficulty >= 0.0 AND suggested_difficulty <= 1.0),
    suggested_bloom_level TEXT DEFAULT 'understand',
    source_references JSONB NOT NULL DEFAULT '[]'::jsonb CHECK (jsonb_typeof(source_references) = 'array'),
    status draft_status_enum NOT NULL DEFAULT 'draft',
    approved_question_id UUID REFERENCES questions(id) ON DELETE SET NULL,
    reviewed_by UUID REFERENCES profiles(id) ON DELETE SET NULL,
    reviewed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_question_drafts_options_array CHECK (jsonb_typeof(options) = 'array'),
    CONSTRAINT uq_question_drafts_approved_question UNIQUE (approved_question_id)
);

-- 5. Tabla: notifications (Avisos In-App Deduplicados)
CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    review_assignment_id UUID REFERENCES review_assignments(id) ON DELETE SET NULL,
    notification_type notification_type_enum NOT NULL DEFAULT 'review_reminder',
    title TEXT NOT NULL CHECK (char_length(title) > 0),
    body TEXT NOT NULL CHECK (char_length(body) > 0),
    target_path TEXT NOT NULL CHECK (char_length(target_path) > 0),
    deduplication_key TEXT NOT NULL,
    read_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(tenant_id, deduplication_key)
);

-- 6. Configuración de Storage Privado (Bucket: teacher-materials)
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
    'teacher-materials',
    'teacher-materials',
    false,
    31457280, -- 30MB
    ARRAY['application/pdf', 'application/vnd.openxmlformats-officedocument.presentationml.presentation']
)
ON CONFLICT (id) DO UPDATE SET 
    public = false,
    file_size_limit = EXCLUDED.file_size_limit,
    allowed_mime_types = EXCLUDED.allowed_mime_types;

-- 7. Índices de Alto Rendimiento
CREATE INDEX IF NOT EXISTS idx_content_gen_jobs_tenant_status ON content_generation_jobs(tenant_id, status);
CREATE INDEX IF NOT EXISTS idx_content_gen_jobs_creator ON content_generation_jobs(created_by);
CREATE INDEX IF NOT EXISTS idx_content_gen_jobs_course ON content_generation_jobs(course_id);
CREATE INDEX IF NOT EXISTS idx_question_drafts_job ON question_drafts(generation_job_id);
CREATE INDEX IF NOT EXISTS idx_question_drafts_tenant_status ON question_drafts(tenant_id, status);
CREATE INDEX IF NOT EXISTS idx_question_drafts_kc ON question_drafts(knowledge_component_id);
CREATE INDEX IF NOT EXISTS idx_notifications_student_unread ON notifications(student_id) WHERE read_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_notifications_tenant_student ON notifications(tenant_id, student_id);

-- 8. Triggers de Mantenimiento de updated_at
DROP TRIGGER IF EXISTS trg_content_gen_jobs_updated_at ON content_generation_jobs;
CREATE TRIGGER trg_content_gen_jobs_updated_at
    BEFORE UPDATE ON content_generation_jobs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS trg_question_drafts_updated_at ON question_drafts;
CREATE TRIGGER trg_question_drafts_updated_at
    BEFORE UPDATE ON question_drafts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 9. Triggers de Salvaguarda de Estados y Transiciones Sensibles
CREATE OR REPLACE FUNCTION enforce_content_generation_jobs_status_guard()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
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

DROP TRIGGER IF EXISTS trg_content_gen_jobs_status_guard ON content_generation_jobs;
CREATE TRIGGER trg_content_gen_jobs_status_guard
    BEFORE INSERT OR UPDATE OR DELETE ON content_generation_jobs
    FOR EACH ROW
    EXECUTE FUNCTION enforce_content_generation_jobs_status_guard();

CREATE OR REPLACE FUNCTION enforce_question_drafts_status_guard()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    IF (TG_OP = 'INSERT') THEN
        IF (NEW.status = 'approved' OR NEW.approved_question_id IS NOT NULL) THEN
            IF (SELECT current_user_role()) IN ('teacher', 'student', 'admin') THEN
                RAISE EXCEPTION 'Direct approval of question drafts via SQL is prohibited. Approval is reserved for the transactional publication service.';
            END IF;
        END IF;
        RETURN NEW;
    ELSIF (TG_OP = 'UPDATE') THEN
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

DROP TRIGGER IF EXISTS trg_question_drafts_status_guard ON question_drafts;
CREATE TRIGGER trg_question_drafts_status_guard
    BEFORE INSERT OR UPDATE OR DELETE ON question_drafts
    FOR EACH ROW
    EXECUTE FUNCTION enforce_question_drafts_status_guard();

CREATE OR REPLACE FUNCTION enforce_notifications_student_update_guard()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
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

DROP TRIGGER IF EXISTS trg_notifications_student_update ON notifications;
CREATE TRIGGER trg_notifications_student_update
    BEFORE UPDATE ON notifications
    FOR EACH ROW
    EXECUTE FUNCTION enforce_notifications_student_update_guard();

-- 10. Permisos y Restricciones a Nivel de Columna (Defense-in-Depth)
GRANT SELECT, INSERT, UPDATE, DELETE ON content_generation_jobs TO authenticated, service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON question_drafts TO authenticated, service_role;
GRANT SELECT, INSERT, DELETE ON notifications TO authenticated, service_role;

REVOKE UPDATE ON notifications FROM authenticated;
GRANT UPDATE (read_at) ON notifications TO authenticated;
GRANT UPDATE ON notifications TO service_role;

-- 11. Habilitación de Row Level Security (RLS)
ALTER TABLE content_generation_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE question_drafts ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;
DO $$ BEGIN
    ALTER TABLE storage.objects ENABLE ROW LEVEL SECURITY;
EXCEPTION WHEN insufficient_privilege THEN
    -- In official Supabase, storage.objects is owned by supabase_storage_admin and already has RLS enabled.
    NULL;
END $$;

-- 12. Políticas RLS para content_generation_jobs
DO $$ BEGIN
    DROP POLICY IF EXISTS "content_gen_jobs_select" ON content_generation_jobs;
    CREATE POLICY "content_gen_jobs_select" ON content_generation_jobs
        FOR SELECT USING (
            (SELECT current_user_role()) = 'super_admin'
            OR (
                tenant_id = (SELECT current_user_tenant_id())
                AND (
                    (SELECT current_user_role()) = 'admin'
                    OR (
                        created_by = (SELECT auth.uid())
                        AND (course_id IS NULL OR is_teacher_of_course(course_id))
                    )
                )
            )
        );
END $$;

DO $$ BEGIN
    DROP POLICY IF EXISTS "content_gen_jobs_insert" ON content_generation_jobs;
    CREATE POLICY "content_gen_jobs_insert" ON content_generation_jobs
        FOR INSERT WITH CHECK (
            status = 'queued'
            AND tenant_id = (SELECT current_user_tenant_id())
            AND created_by = (SELECT auth.uid())
            AND (SELECT current_user_role()) IN ('teacher', 'admin', 'super_admin')
            AND (
                (SELECT current_user_role()) IN ('super_admin', 'admin')
                OR course_id IS NULL
                OR is_teacher_of_course(course_id)
            )
            AND split_part(storage_path, '/', 1) = (SELECT current_user_tenant_id())::text
            AND storage_bucket = 'teacher-materials'
        );
END $$;

DO $$ BEGIN
    DROP POLICY IF EXISTS "content_gen_jobs_update" ON content_generation_jobs;
    CREATE POLICY "content_gen_jobs_update" ON content_generation_jobs
        FOR UPDATE USING (
            (SELECT current_user_role()) = 'super_admin'
            OR (
                tenant_id = (SELECT current_user_tenant_id())
                AND (
                    (SELECT current_user_role()) = 'admin'
                    OR (
                        created_by = (SELECT auth.uid())
                        AND (course_id IS NULL OR is_teacher_of_course(course_id))
                    )
                )
            )
        )
        WITH CHECK (
            (SELECT current_user_role()) = 'super_admin'
            OR (
                tenant_id = (SELECT current_user_tenant_id())
                AND (SELECT current_user_role()) = 'admin'
            )
        );
END $$;

DO $$ BEGIN
    DROP POLICY IF EXISTS "content_gen_jobs_delete" ON content_generation_jobs;
    CREATE POLICY "content_gen_jobs_delete" ON content_generation_jobs
        FOR DELETE USING (
            (SELECT current_user_role()) = 'super_admin'
            OR (
                tenant_id = (SELECT current_user_tenant_id())
                AND (
                    (SELECT current_user_role()) = 'admin'
                    OR (
                        created_by = (SELECT auth.uid())
                        AND (course_id IS NULL OR is_teacher_of_course(course_id))
                    )
                )
            )
        );
END $$;

-- 13. Políticas RLS para question_drafts
DO $$ BEGIN
    DROP POLICY IF EXISTS "question_drafts_select" ON question_drafts;
    CREATE POLICY "question_drafts_select" ON question_drafts
        FOR SELECT USING (
            (SELECT current_user_role()) = 'super_admin'
            OR (
                tenant_id = (SELECT current_user_tenant_id())
                AND (
                    (SELECT current_user_role()) = 'admin'
                    OR EXISTS (
                        SELECT 1 FROM public.content_generation_jobs j
                        WHERE j.id = question_drafts.generation_job_id
                          AND j.created_by = (SELECT auth.uid())
                          AND (j.course_id IS NULL OR is_teacher_of_course(j.course_id))
                    )
                )
            )
        );
END $$;

DO $$ BEGIN
    DROP POLICY IF EXISTS "question_drafts_insert" ON question_drafts;
    CREATE POLICY "question_drafts_insert" ON question_drafts
        FOR INSERT WITH CHECK (
            status = 'draft'
            AND approved_question_id IS NULL
            AND (
                (SELECT current_user_role()) = 'super_admin'
                OR (
                    tenant_id = (SELECT current_user_tenant_id())
                    AND (SELECT current_user_role()) IN ('teacher', 'admin')
                    AND EXISTS (
                        SELECT 1 FROM public.content_generation_jobs j
                        WHERE j.id = question_drafts.generation_job_id
                          AND j.tenant_id = (SELECT current_user_tenant_id())
                          AND (
                              (SELECT current_user_role()) = 'admin'
                              OR (
                                  j.created_by = (SELECT auth.uid())
                                  AND (j.course_id IS NULL OR is_teacher_of_course(j.course_id))
                              )
                          )
                    )
                )
            )
        );
END $$;

DO $$ BEGIN
    DROP POLICY IF EXISTS "question_drafts_update" ON question_drafts;
    CREATE POLICY "question_drafts_update" ON question_drafts
        FOR UPDATE USING (
            (SELECT current_user_role()) = 'super_admin'
            OR (
                tenant_id = (SELECT current_user_tenant_id())
                AND (
                    (SELECT current_user_role()) = 'admin'
                    OR EXISTS (
                        SELECT 1 FROM public.content_generation_jobs j
                        WHERE j.id = question_drafts.generation_job_id
                          AND j.created_by = (SELECT auth.uid())
                          AND (j.course_id IS NULL OR is_teacher_of_course(j.course_id))
                    )
                )
            )
        )
        WITH CHECK (
            (SELECT current_user_role()) = 'super_admin'
            OR (
                tenant_id = (SELECT current_user_tenant_id())
                AND status != 'approved'
                AND approved_question_id IS NULL
            )
        );
END $$;

DO $$ BEGIN
    DROP POLICY IF EXISTS "question_drafts_delete" ON question_drafts;
    CREATE POLICY "question_drafts_delete" ON question_drafts
        FOR DELETE USING (
            (SELECT current_user_role()) = 'super_admin'
            OR (
                tenant_id = (SELECT current_user_tenant_id())
                AND (
                    (SELECT current_user_role()) = 'admin'
                    OR EXISTS (
                        SELECT 1 FROM public.content_generation_jobs j
                        WHERE j.id = question_drafts.generation_job_id
                          AND j.created_by = (SELECT auth.uid())
                          AND (j.course_id IS NULL OR is_teacher_of_course(j.course_id))
                    )
                )
            )
        );
END $$;

-- 14. Políticas RLS para notifications
DO $$ BEGIN
    DROP POLICY IF EXISTS "notifications_select" ON notifications;
    CREATE POLICY "notifications_select" ON notifications
        FOR SELECT USING (
            (SELECT current_user_role()) = 'super_admin'
            OR (
                tenant_id = (SELECT current_user_tenant_id())
                AND (
                    student_id = (SELECT auth.uid())
                    OR (SELECT is_teacher_of_student(student_id))
                    OR (SELECT current_user_role()) = 'admin'
                )
            )
        );
END $$;

DO $$ BEGIN
    DROP POLICY IF EXISTS "notifications_insert" ON notifications;
    CREATE POLICY "notifications_insert" ON notifications
        FOR INSERT WITH CHECK (
            (SELECT current_user_role()) = 'super_admin'
            OR (
                tenant_id = (SELECT current_user_tenant_id())
                AND (
                    (SELECT current_user_role()) = 'admin'
                    OR (SELECT is_teacher_of_student(student_id))
                )
            )
        );
END $$;

DO $$ BEGIN
    DROP POLICY IF EXISTS "notifications_update" ON notifications;
    CREATE POLICY "notifications_update" ON notifications
        FOR UPDATE USING (
            (SELECT current_user_role()) = 'super_admin'
            OR (
                tenant_id = (SELECT current_user_tenant_id())
                AND (
                    student_id = (SELECT auth.uid())
                    OR (SELECT current_user_role()) = 'admin'
                )
            )
        )
        WITH CHECK (
            (SELECT current_user_role()) = 'super_admin'
            OR (
                tenant_id = (SELECT current_user_tenant_id())
                AND (
                    student_id = (SELECT auth.uid())
                    OR (SELECT current_user_role()) = 'admin'
                )
            )
        );
END $$;

DO $$ BEGIN
    DROP POLICY IF EXISTS "notifications_delete" ON notifications;
    CREATE POLICY "notifications_delete" ON notifications
        FOR DELETE USING (
            (SELECT current_user_role()) = 'super_admin'
            OR (
                tenant_id = (SELECT current_user_tenant_id())
                AND (SELECT current_user_role()) = 'admin'
            )
        );
END $$;

-- 15. Políticas RLS para storage.objects (Bucket teacher-materials)
DO $$ BEGIN
    DROP POLICY IF EXISTS "storage_teacher_materials_select" ON storage.objects;
    CREATE POLICY "storage_teacher_materials_select" ON storage.objects
        FOR SELECT USING (
            bucket_id = 'teacher-materials'
            AND (
                (SELECT current_user_role()) = 'super_admin'
                OR (
                    split_part(name, '/', 1) = (SELECT current_user_tenant_id())::text
                    AND (
                        (SELECT current_user_role()) = 'admin'
                        OR (
                            (SELECT current_user_role()) = 'teacher'
                            AND auth.uid() = owner
                        )
                    )
                )
            )
        );
END $$;

DO $$ BEGIN
    DROP POLICY IF EXISTS "storage_teacher_materials_insert" ON storage.objects;
    CREATE POLICY "storage_teacher_materials_insert" ON storage.objects
        FOR INSERT WITH CHECK (
            bucket_id = 'teacher-materials'
            AND auth.uid() = owner
            AND (
                (SELECT current_user_role()) = 'super_admin'
                OR (
                    (SELECT current_user_role()) IN ('teacher', 'admin')
                    AND split_part(name, '/', 1) = (SELECT current_user_tenant_id())::text
                )
            )
        );
END $$;

DO $$ BEGIN
    DROP POLICY IF EXISTS "storage_teacher_materials_update" ON storage.objects;
    CREATE POLICY "storage_teacher_materials_update" ON storage.objects
        FOR UPDATE USING (
            bucket_id = 'teacher-materials'
            AND (
                (SELECT current_user_role()) = 'super_admin'
                OR (
                    split_part(name, '/', 1) = (SELECT current_user_tenant_id())::text
                    AND (
                        (SELECT current_user_role()) = 'admin'
                        OR (
                            (SELECT current_user_role()) = 'teacher'
                            AND auth.uid() = owner
                        )
                    )
                )
            )
        )
        WITH CHECK (
            bucket_id = 'teacher-materials'
            AND (
                (SELECT current_user_role()) = 'super_admin'
                OR (
                    split_part(name, '/', 1) = (SELECT current_user_tenant_id())::text
                    AND (
                        (SELECT current_user_role()) = 'admin'
                        OR (
                            (SELECT current_user_role()) = 'teacher'
                            AND auth.uid() = owner
                        )
                    )
                )
            )
        );
END $$;

DO $$ BEGIN
    DROP POLICY IF EXISTS "storage_teacher_materials_delete" ON storage.objects;
    CREATE POLICY "storage_teacher_materials_delete" ON storage.objects
        FOR DELETE USING (
            bucket_id = 'teacher-materials'
            AND (
                (SELECT current_user_role()) = 'super_admin'
                OR (
                    split_part(name, '/', 1) = (SELECT current_user_tenant_id())::text
                    AND (
                        (SELECT current_user_role()) = 'admin'
                        OR (
                            (SELECT current_user_role()) = 'teacher'
                            AND auth.uid() = owner
                        )
                    )
                )
            )
        );
END $$;


-- >>> MIGRACIÓN: 20261103000000_content_generation_leases_and_idempotency.sql >>>
-- ============================================================================
-- PLATAFORMA DE MICROAPRENDIZAJE ADAPTATIVO
-- MIGRACIÓN INCREMENTAL: Leases de Procesamiento, Recuperación e Idempotencia
-- Tarea M2.3: Persistencia PostgreSQL, Consistencia Transaccional y API REST
-- Version: 20261103000000
-- ============================================================================

-- 1. Incorporar campos para modelo de Leases y Recuperación en content_generation_jobs
ALTER TABLE content_generation_jobs
    ADD COLUMN IF NOT EXISTS processing_started_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS processing_lease_expires_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS processing_lease_token UUID,
    ADD COLUMN IF NOT EXISTS attempt_count INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS max_attempts INTEGER NOT NULL DEFAULT 3,
    ADD COLUMN IF NOT EXISTS last_heartbeat_at TIMESTAMPTZ;

-- 2. Restricción de Idempotencia Parcial para Trabajos Activos
-- Evita trabajos redundantes simultáneos para el mismo archivo y curso en el mismo tenant,
-- permitiendo nuevos trabajos tras culminación o fallo del trabajo anterior.
CREATE UNIQUE INDEX IF NOT EXISTS uq_content_gen_jobs_active_file
    ON content_generation_jobs (tenant_id, course_id, file_checksum)
    NULLS NOT DISTINCT
    WHERE status IN ('queued', 'processing');

-- 3. Índice para Selección Rápida y Fencing de Trabajos Reclamables
CREATE INDEX IF NOT EXISTS idx_content_gen_jobs_lease_claim
    ON content_generation_jobs (status, processing_lease_expires_at, attempt_count)
    WHERE status IN ('queued', 'processing');

-- 4. Clave de Idempotencia para Borradores de Preguntas en question_drafts
ALTER TABLE question_drafts
    ADD COLUMN IF NOT EXISTS content_hash TEXT;

-- Evita la duplicación idéntica de reactivos dentro de un mismo trabajo en reintentos
CREATE UNIQUE INDEX IF NOT EXISTS uq_question_drafts_job_content_hash
    ON question_drafts (generation_job_id, content_hash)
    WHERE content_hash IS NOT NULL;


-- >>> MIGRACIÓN: 20261103010000_content_generation_hardening.sql >>>
-- ============================================================================
-- PLATAFORMA DE MICROAPRENDIZAJE ADAPTATIVO
-- MIGRACIÓN INCREMENTAL: Endurecimiento de Seguridad, Integridad Tenant y Fencing
-- Tarea M2.3-HARDENING: Auditoría de Concurrencia, Idempotencia y RLS
-- Version: 20261103010000
-- ============================================================================

-- 1. Clave Única Compuesta (id, tenant_id) en content_generation_jobs
-- Permite validación estricta de pertenencia multi-tenant y claves foráneas compuestas.
CREATE UNIQUE INDEX IF NOT EXISTS uq_content_gen_jobs_id_tenant
    ON content_generation_jobs (id, tenant_id);

-- 2. Actualización de Trigger de Seguridad en question_drafts
-- Previene activamente a nivel motor de base de datos la inyección cruzada de borradores
-- entre distintos tenants (Cross-Tenant Draft Poisoning), y la reversión de borradores
-- intervenidos (edited, approved, rejected) hacia estado 'draft'.
CREATE OR REPLACE FUNCTION enforce_question_drafts_status_guard()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
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

DROP TRIGGER IF EXISTS trg_question_drafts_status_guard ON question_drafts;
CREATE TRIGGER trg_question_drafts_status_guard
    BEFORE INSERT OR UPDATE OR DELETE ON question_drafts
    FOR EACH ROW
    EXECUTE FUNCTION enforce_question_drafts_status_guard();

-- 3. Rol de Ejecución con Privilegios Mínimos (Least Privilege) para el Microservicio FastAPI / Worker
-- No cuenta con atributo SUPERUSER ni BYPASSRLS.
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'ml_api_worker') THEN
        CREATE ROLE ml_api_worker WITH LOGIN PASSWORD 'ml_api_worker_secret' NOINHERIT;
    END IF;
END
$$;

-- Otorgar exclusivamente permisos sobre las tablas del pipeline de generación y lectura curricular
GRANT USAGE ON SCHEMA public TO ml_api_worker;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.content_generation_jobs TO ml_api_worker;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.question_drafts TO ml_api_worker;
GRANT SELECT ON public.tenants, public.profiles, public.courses, public.sections, public.enrollments, public.units, public.knowledge_components TO ml_api_worker;

-- 4. Políticas RLS para el Rol ml_api_worker
-- Permite al worker consultar y procesar trabajos y borradores de manera segura manteniendo RLS habilitado
DO $$ BEGIN
    DROP POLICY IF EXISTS "ml_worker_jobs_policy" ON content_generation_jobs;
    CREATE POLICY "ml_worker_jobs_policy" ON content_generation_jobs
        FOR ALL TO ml_api_worker
        USING (true) WITH CHECK (true);
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    DROP POLICY IF EXISTS "ml_worker_drafts_policy" ON question_drafts;
    CREATE POLICY "ml_worker_drafts_policy" ON question_drafts
        FOR ALL TO ml_api_worker
        USING (true) WITH CHECK (true);
EXCEPTION WHEN duplicate_object THEN null;
END $$;


-- >>> MIGRACIÓN: 20261103020000_teacher_question_editor_m3.sql >>>
-- ============================================================================
-- PLATAFORMA DE MICROAPRENDIZAJE ADAPTATIVO
-- MIGRACIÓN INCREMENTAL: Trazabilidad Canónica, Motivo de Rechazo y Permisos M3
-- Version: 20261103020000
-- ============================================================================

-- 1. Columna de motivo de rechazo en question_drafts
ALTER TABLE question_drafts
    ADD COLUMN IF NOT EXISTS rejection_reason TEXT;

-- 2. Trazabilidad bidireccional: referencia al borrador de origen en questions
ALTER TABLE questions
    ADD COLUMN IF NOT EXISTS source_draft_id UUID REFERENCES question_drafts(id) ON DELETE SET NULL;

DROP INDEX IF EXISTS idx_questions_source_draft;
CREATE UNIQUE INDEX IF NOT EXISTS uq_questions_source_draft ON questions(source_draft_id) WHERE source_draft_id IS NOT NULL;

-- 3. Permisos para ml_api_worker en preguntas y opciones canónicas
GRANT SELECT, INSERT, UPDATE ON public.questions TO ml_api_worker;
GRANT SELECT, INSERT, UPDATE ON public.question_options TO ml_api_worker;

-- 4. Política RLS para ml_api_worker sobre questions y question_options
DO $$ BEGIN
    DROP POLICY IF EXISTS "ml_worker_questions_policy" ON questions;
    CREATE POLICY "ml_worker_questions_policy" ON questions
        FOR ALL TO ml_api_worker
        USING (true) WITH CHECK (true);
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    DROP POLICY IF EXISTS "ml_worker_question_options_policy" ON question_options;
    CREATE POLICY "ml_worker_question_options_policy" ON question_options
        FOR ALL TO ml_api_worker
        USING (true) WITH CHECK (true);
EXCEPTION WHEN duplicate_object THEN null;
END $$;


-- >>> MIGRACIÓN: 20261103030000_learning_flow_and_answer_events_m4.sql >>>
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


-- >>> MIGRACIÓN: 20261103040000_content_exposure_events_m52.sql >>>
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


-- >>> MIGRACIÓN: 20261103050000_recommendations_and_predictions_m53.sql >>>
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


-- >>> SEED BASE: seed.sql >>>
-- ============================================================================
-- SEED DATA — PLATAFORMA DE MICROAPRENDIZAJE ADAPTATIVO (NEXO)
-- Cuentas pre-provisionadas, curso piloto de Ciencias y reactivos de prueba
-- ============================================================================

-- 1. Tenant Institucional
INSERT INTO tenants (id, name, slug, domain, is_active, settings)
VALUES (
    'a0000000-0000-0000-0000-000000000001',
    'Colegio Piloto San Agustín',
    'san-agustin',
    'sanagustin.edu.pe',
    true,
    '{"risk_threshold": 0.65, "cold_start_kcs": 3}'::jsonb
) ON CONFLICT (id) DO NOTHING;

-- 2. Cuentas de Auth y Profiles (Docente y Estudiante)
-- Nota: En Supabase Auth, los usuarios se insertan en auth.users con contraseñas encriptadas bcrypt.
-- Contraseña por defecto para desarrollo: "Nexo2026!"
-- hash pgcrypto: crypt('Nexo2026!', gen_salt('bf'))
DO $$
DECLARE
    teacher_user_id UUID := 'd0000000-0000-0000-0000-000000000001';
    student_user_id UUID := 'e0000000-0000-0000-0000-000000000001';
    tenant_uuid UUID := 'a0000000-0000-0000-0000-000000000001';
BEGIN
    -- Usuario Docente en auth.users (si existe esquema auth)
    IF EXISTS (SELECT 1 FROM information_schema.schemata WHERE schema_name = 'auth') THEN
        INSERT INTO auth.users (
            id, instance_id, email, encrypted_password, email_confirmed_at,
            raw_app_meta_data, raw_user_meta_data, role, aud, created_at, updated_at,
            confirmation_token, recovery_token, email_change_token_new, email_change,
            email_change_token_current, phone_change, phone_change_token, reauthentication_token
        ) VALUES (
            teacher_user_id,
            '00000000-0000-0000-0000-000000000000',
            'ana.garcia@nexo.edu.pe',
            crypt('Nexo2026!', gen_salt('bf')),
            now(),
            '{"provider":"email","providers":["email"]}',
            '{"full_name":"Ana García","role":"teacher"}',
            'authenticated',
            'authenticated',
            now(),
            now(),
            '', '', '', '', '', '', '', ''
        ) ON CONFLICT (id) DO NOTHING;

        -- Usuario Estudiante en auth.users
        INSERT INTO auth.users (
            id, instance_id, email, encrypted_password, email_confirmed_at,
            raw_app_meta_data, raw_user_meta_data, role, aud, created_at, updated_at,
            confirmation_token, recovery_token, email_change_token_new, email_change,
            email_change_token_current, phone_change, phone_change_token, reauthentication_token
        ) VALUES (
            student_user_id,
            '00000000-0000-0000-0000-000000000000',
            'lucia.mendoza@nexo.edu.pe',
            crypt('Nexo2026!', gen_salt('bf')),
            now(),
            '{"provider":"email","providers":["email"]}',
            '{"full_name":"Lucía Mendoza","role":"student","student_code":"EST-501"}',
            'authenticated',
            'authenticated',
            now(),
            now(),
            '', '', '', '', '', '', '', ''
        ) ON CONFLICT (id) DO NOTHING;
    END IF;

    -- Profiles asociados
    INSERT INTO profiles (id, tenant_id, student_code, full_name, role)
    VALUES 
        (teacher_user_id, tenant_uuid, 'DOC-101', 'Ana García', 'teacher'),
        (student_user_id, tenant_uuid, 'EST-501', 'Lucía Mendoza', 'student')
    ON CONFLICT (id) DO UPDATE SET full_name = EXCLUDED.full_name;

END $$;

-- 3. Curso Piloto "Ciencias" (Agnóstico)
INSERT INTO courses (id, tenant_id, code, name, description, is_active)
VALUES (
    'c0000000-0000-0000-0000-000000000001',
    'a0000000-0000-0000-0000-000000000001',
    'CIEN-5SEC',
    'Ciencias',
    'Biología, química y ambiente para 5.° de secundaria',
    true
) ON CONFLICT (id) DO NOTHING;

-- 4. Sección y Matrícula
INSERT INTO sections (id, tenant_id, course_id, teacher_id, name)
VALUES (
    '5ec00000-0000-0000-0000-000000000001',
    'a0000000-0000-0000-0000-000000000001',
    'c0000000-0000-0000-0000-000000000001',
    'd0000000-0000-0000-0000-000000000001',
    '5.° A - Ciencias'
) ON CONFLICT (id) DO NOTHING;

INSERT INTO enrollments (id, tenant_id, section_id, student_id, student_id_pseudo)
VALUES (
    'e0000000-0000-0000-0000-000000000002',
    'a0000000-0000-0000-0000-000000000001',
    '5ec00000-0000-0000-0000-000000000001',
    'e0000000-0000-0000-0000-000000000001',
    'f0000000-0000-0000-0000-000000000001'
) ON CONFLICT (id) DO NOTHING;

-- 5. Unidades Temáticas
INSERT INTO units (id, tenant_id, course_id, title, order_index)
VALUES 
    ('b0000000-0000-0000-0000-000000000001', 'a0000000-0000-0000-0000-000000000001', 'c0000000-0000-0000-0000-000000000001', 'Estructura celular', 1),
    ('b0000000-0000-0000-0000-000000000002', 'a0000000-0000-0000-0000-000000000001', 'c0000000-0000-0000-0000-000000000001', 'Nutrición y metabolismo', 2),
    ('b0000000-0000-0000-0000-000000000003', 'a0000000-0000-0000-0000-000000000001', 'c0000000-0000-0000-0000-000000000001', 'Genética y herencia', 3),
    ('b0000000-0000-0000-0000-000000000004', 'a0000000-0000-0000-0000-000000000001', 'c0000000-0000-0000-0000-000000000001', 'Ecología y sostenibilidad', 4)
ON CONFLICT (id) DO NOTHING;

-- 6. Componente de Conocimiento (KC) - Fotosíntesis
INSERT INTO knowledge_components (id, tenant_id, unit_id, name, description, difficulty_prior)
VALUES (
    'f0000000-0000-0000-0000-000000000001',
    'a0000000-0000-0000-0000-000000000001',
    'b0000000-0000-0000-0000-000000000002',
    'Fotosíntesis',
    'Conversión de energía solar en energía química celular',
    0.480
) ON CONFLICT (id) DO NOTHING;

-- 7. Pregunta y Opciones de Fotosíntesis (Exactas de la interfaz)
INSERT INTO questions (id, tenant_id, knowledge_component_id, question_text, question_type, explanation, difficulty, created_by)
VALUES (
    '00000000-0000-0000-0000-000000000001',
    'a0000000-0000-0000-0000-000000000001',
    'f0000000-0000-0000-0000-000000000001',
    '¿Cuál es la función principal de la luz solar durante la fotosíntesis?',
    'multiple_choice',
    'La energía luminosa es capturada por la clorofila y transformada en energía química. Esa energía permite sintetizar glucosa, que la planta utiliza y almacena como alimento.',
    0.450,
    'd0000000-0000-0000-0000-000000000001'
) ON CONFLICT (id) DO NOTHING;

INSERT INTO question_options (id, question_id, option_text, is_correct, order_index)
VALUES
    ('00000000-0000-0000-0000-000000000011', '00000000-0000-0000-0000-000000000001', 'Calentar las hojas para que absorban más agua.', false, 1),
    ('00000000-0000-0000-0000-000000000012', '00000000-0000-0000-0000-000000000001', 'Proporcionar la energía necesaria para producir glucosa.', true, 2),
    ('00000000-0000-0000-0000-000000000013', '00000000-0000-0000-0000-000000000001', 'Convertir directamente el oxígeno en dióxido de carbono.', false, 3),
    ('00000000-0000-0000-0000-000000000014', '00000000-0000-0000-0000-000000000001', 'Transportar minerales desde las raíces hasta las hojas.', false, 4)
ON CONFLICT (id) DO NOTHING;

-- 8. Microcontenido Canónico de Fotosíntesis (M5.4)
INSERT INTO microcontents (
    id, tenant_id, knowledge_component_id, title, content_type,
    content_body, estimated_duration_seconds, created_by, is_published, created_at
) VALUES (
    'a1000000-0000-0000-0000-000000000001',
    'a0000000-0000-0000-0000-000000000001',
    'f0000000-0000-0000-0000-000000000001',
    'Fotosíntesis: Transformación de Energía Solar en Glucosa',
    'text_summary'::content_type_enum,
    '{
        "summary": "Comprensión integral de cómo las células vegetales convierten compuestos inorgánicos en energía química.",
        "sections": [
            {
                "id": 1,
                "navTitle": "Idea principal",
                "heading": "La fotosíntesis como base de la vida",
                "tag": "FOTOSÍNTESIS",
                "lead": "Las células vegetales convierten compuestos inorgánicos simples en moléculas energéticas ricas en enlaces de carbono.",
                "durationMinutes": 2
            },
            {
                "id": 2,
                "navTitle": "El proceso",
                "heading": "La luz se transforma en alimento",
                "tag": "FOTOSÍNTESIS",
                "lead": "Las plantas capturan energía del sol y la usan para producir glucosa a partir de agua y dióxido de carbono.",
                "durationMinutes": 4,
                "formula": "6CO₂  +  6H₂O  —luz→  C₆H₁₂O₆  +  6O₂",
                "analogy": {
                    "title": "Piensa en un panel solar natural",
                    "body": "Así como un panel captura luz para producir electricidad, la clorofila de las hojas captura luz para producir energía química almacenada en la glucosa."
                },
                "keyTakeaways": [
                    {"number": "01", "text": "Ocurre principalmente en las hojas, dentro de los cloroplastos."},
                    {"number": "02", "text": "Necesita luz, agua y dióxido de carbono."},
                    {"number": "03", "text": "Produce glucosa y libera oxígeno a la atmósfera."}
                ]
            },
            {
                "id": 3,
                "navTitle": "Estructura celular",
                "heading": "La hoja bajo el microscopio",
                "tag": "ESTOMAS Y CLOROPLASTOS",
                "lead": "A través de los estomas entra el dióxido de carbono y sale el oxígeno liberado a la atmósfera.",
                "durationMinutes": 2
            },
            {
                "id": 4,
                "navTitle": "Ideas clave",
                "heading": "Síntesis para retención a largo plazo",
                "tag": "CONSOLIDACIÓN",
                "lead": "Comprender la diferencia entre fuente de materia y fuente de energía es la clave para dominar este concepto.",
                "durationMinutes": 2
            }
        ]
    }'::jsonb,
    240,
    'd0000000-0000-0000-0000-000000000001',
    true,
    now()
) ON CONFLICT (id) DO NOTHING;

-- 9. Actividad Canónica Publicada (M5.4)
INSERT INTO activities (
    id, tenant_id, course_id, created_by, title, description,
    status, activity_type, feedback_policy, max_attempts, time_limit_minutes, published_at
) VALUES (
    'ac700000-0000-0000-0000-000000000001',
    'a0000000-0000-0000-0000-000000000001',
    'c0000000-0000-0000-0000-000000000001',
    'd0000000-0000-0000-0000-000000000001',
    'Comprobación Activa: Fundamentos de Fotosíntesis',
    'Cuestionario breve formativo para comprobar la asimilación conceptual de la fotosíntesis y reactivos lumínicos.',
    'published'::activity_status_enum,
    'practice'::activity_type_enum,
    'immediate_with_explanation'::feedback_policy_enum,
    3,
    10,
    now()
) ON CONFLICT (id) DO NOTHING;

-- Vincular pregunta a la actividad
INSERT INTO activity_questions (activity_id, question_id, order_index)
VALUES ('ac700000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000001', 1)
ON CONFLICT (activity_id, question_id) DO NOTHING;

-- Vincular sección a la actividad
INSERT INTO activity_sections (tenant_id, activity_id, section_id)
VALUES ('a0000000-0000-0000-0000-000000000001', 'ac700000-0000-0000-0000-000000000001', '5ec00000-0000-0000-0000-000000000001')
ON CONFLICT (activity_id, section_id) DO NOTHING;



-- >>> SEED DEMO: seed_demo.sql >>>
-- ============================================================================
-- DEMO SEED — PLATAFORMA DE MICROAPRENDIZAJE ADAPTATIVO (NEXO)
-- ============================================================================
-- Requisito previo: haber ejecutado `supabase/seed.sql` (tenant, docente,
-- estudiante Lucía Mendoza, curso, sección, unidades y contenido canónico).
--
-- Este archivo es ADITIVO e IDEMPOTENTE:
--   * Contenido con UUID fijos + ON CONFLICT DO NOTHING.
--   * Historial con UUID deterministas derivados de uuid_generate_v5.
--   * Se puede ejecutar N veces sin duplicar estudiantes, intentos ni eventos.
--
-- Datos: 10 estudiantes seudonimizados, 5 componentes de conocimiento,
-- 5 microcontenidos, 15 preguntas, 5 actividades y 6 semanas de historial.
--
-- NO se insertan predicciones ni métricas de modelo: el MVP no cuenta aún con
-- un artefacto predictivo validado. Las recomendaciones usan la etiqueta
-- honesta `rule_based_fallback` y su motivo lo declara explícitamente.
-- ============================================================================

BEGIN;

-- ----------------------------------------------------------------------------
-- 1. Estudiantes demo adicionales (9) + perfiles + matrícula
--    Lucía Mendoza (EST-501) ya viene en seed.sql.
-- ----------------------------------------------------------------------------
DO $$
DECLARE
    r RECORD;
    tenant_uuid UUID := 'a0000000-0000-0000-0000-000000000001';
    section_uuid UUID := '5ec00000-0000-0000-0000-000000000001';
    enrollment_uuid UUID;
    pseudo_uuid UUID;
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.schemata WHERE schema_name = 'auth') THEN
        FOR r IN
            SELECT *
            FROM (VALUES
                ('e0000000-0000-0000-0000-000000000002'::uuid, 'estudiante.502@nexo.edu.pe', 'Estudiante 502', 'EST-502'),
                ('e0000000-0000-0000-0000-000000000003'::uuid, 'estudiante.503@nexo.edu.pe', 'Estudiante 503', 'EST-503'),
                ('e0000000-0000-0000-0000-000000000004'::uuid, 'estudiante.504@nexo.edu.pe', 'Estudiante 504', 'EST-504'),
                ('e0000000-0000-0000-0000-000000000005'::uuid, 'estudiante.505@nexo.edu.pe', 'Estudiante 505', 'EST-505'),
                ('e0000000-0000-0000-0000-000000000006'::uuid, 'estudiante.506@nexo.edu.pe', 'Estudiante 506', 'EST-506'),
                ('e0000000-0000-0000-0000-000000000007'::uuid, 'estudiante.507@nexo.edu.pe', 'Estudiante 507', 'EST-507'),
                ('e0000000-0000-0000-0000-000000000008'::uuid, 'estudiante.508@nexo.edu.pe', 'Estudiante 508', 'EST-508'),
                ('e0000000-0000-0000-0000-000000000009'::uuid, 'estudiante.509@nexo.edu.pe', 'Estudiante 509', 'EST-509'),
                ('e0000000-0000-0000-0000-000000000010'::uuid, 'estudiante.510@nexo.edu.pe', 'Estudiante 510', 'EST-510')
            ) AS t(id, email, full_name, code)
        LOOP
            INSERT INTO auth.users (
                id, instance_id, email, encrypted_password, email_confirmed_at,
                raw_app_meta_data, raw_user_meta_data, role, aud, created_at, updated_at,
                confirmation_token, recovery_token, email_change_token_new, email_change,
                email_change_token_current, phone_change, phone_change_token, reauthentication_token
            ) VALUES (
                r.id,
                '00000000-0000-0000-0000-000000000000',
                r.email,
                crypt('Nexo2026!', gen_salt('bf')),
                now(),
                '{"provider":"email","providers":["email"]}',
                jsonb_build_object('full_name', r.full_name, 'role', 'student', 'student_code', r.code),
                'authenticated',
                'authenticated',
                now(),
                now(),
                '', '', '', '', '', '', '', ''
            ) ON CONFLICT (id) DO NOTHING;

            INSERT INTO profiles (id, tenant_id, student_code, full_name, role)
            VALUES (r.id, tenant_uuid, r.code, r.full_name, 'student')
            ON CONFLICT (id) DO UPDATE SET full_name = EXCLUDED.full_name;

            enrollment_uuid := uuid_generate_v5(uuid_ns_url(), 'nexo:demo:enrollment:' || r.code);
            pseudo_uuid := uuid_generate_v5(uuid_ns_url(), 'nexo:demo:pseudo:' || r.code);

            INSERT INTO enrollments (id, tenant_id, section_id, student_id, student_id_pseudo)
            VALUES (enrollment_uuid, tenant_uuid, section_uuid, r.id, pseudo_uuid)
            ON CONFLICT (section_id, student_id) DO NOTHING;
        END LOOP;
    END IF;
END $$;

-- ----------------------------------------------------------------------------
-- 2. Componentes de Conocimiento (4 nuevos; Fotosíntesis ya existe)
-- ----------------------------------------------------------------------------
INSERT INTO knowledge_components (id, tenant_id, unit_id, name, description, difficulty_prior)
VALUES
    ('f0000000-0000-0000-0000-000000000002', 'a0000000-0000-0000-0000-000000000001', 'b0000000-0000-0000-0000-000000000002',
     'Respiración celular', 'Obtención de energía a partir de la glucosa en las mitocondrias', 0.520),
    ('f0000000-0000-0000-0000-000000000003', 'a0000000-0000-0000-0000-000000000001', 'b0000000-0000-0000-0000-000000000001',
     'Estructura y función celular', 'Organelos, membrana y núcleo como sistemas integrados', 0.450),
    ('f0000000-0000-0000-0000-000000000004', 'a0000000-0000-0000-0000-000000000001', 'b0000000-0000-0000-0000-000000000003',
     'Herencia mendeliana', 'Transmisión de rasgos mediante alelos dominantes y recesivos', 0.580),
    ('f0000000-0000-0000-0000-000000000005', 'a0000000-0000-0000-0000-000000000001', 'b0000000-0000-0000-0000-000000000004',
     'Ciclos biogeoquímicos', 'Circulación de carbono, nitrógeno y agua en los ecosistemas', 0.600)
ON CONFLICT (id) DO NOTHING;

-- ----------------------------------------------------------------------------
-- 3. Microcontenidos (4 nuevos; el de Fotosíntesis ya existe)
-- ----------------------------------------------------------------------------
INSERT INTO microcontents (
    id, tenant_id, knowledge_component_id, title, content_type,
    content_body, estimated_duration_seconds, created_by, is_published, created_at
) VALUES
    ('a1000000-0000-0000-0000-000000000002', 'a0000000-0000-0000-0000-000000000001', 'f0000000-0000-0000-0000-000000000002',
     'Respiración celular: la energía que sostiene la vida', 'text_summary'::content_type_enum,
     '{
        "summary": "La respiración celular transforma la glucosa en energía utilizable (ATP).",
        "sections": [
          {"id": 1, "navTitle": "Idea principal", "heading": "Liberar energía química", "tag": "RESPIRACIÓN CELULAR", "lead": "Las células degradan la glucosa para obtener ATP, la moneda energética de la célula.", "durationMinutes": 2},
          {"id": 2, "navTitle": "El proceso", "heading": "De glucosa a ATP", "tag": "MITOCONDRIAS", "lead": "En presencia de oxígeno, la glucosa se oxida y se liberan dióxido de carbono, agua y energía.", "durationMinutes": 3, "formula": "C6H12O6 + 6O2 -> 6CO2 + 6H2O + ATP", "keyTakeaways": [{"number": "01", "text": "Ocurre principalmente en las mitocondrias."}, {"number": "02", "text": "Requiere glucosa y oxígeno en la respiración aerobia."}, {"number": "03", "text": "Genera ATP, la energía que la célula utiliza."}]},
          {"id": 3, "navTitle": "Ideas clave", "heading": "Fotosíntesis y respiración", "tag": "CONSOLIDACIÓN", "lead": "La fotosíntesis almacena energía y la respiración la libera: son procesos complementarios.", "durationMinutes": 2}
        ]
     }'::jsonb,
     200, 'd0000000-0000-0000-0000-000000000001', true, now()),

    ('a1000000-0000-0000-0000-000000000003', 'a0000000-0000-0000-0000-000000000001', 'f0000000-0000-0000-0000-000000000003',
     'La célula: estructura y funciones', 'text_summary'::content_type_enum,
     '{
        "summary": "Cada organelo cumple una función específica dentro de la célula.",
        "sections": [
          {"id": 1, "navTitle": "Idea principal", "heading": "Una unidad con muchos sistemas", "tag": "CÉLULA", "lead": "La célula organiza sus funciones en organelos especializados.", "durationMinutes": 2},
          {"id": 2, "navTitle": "Organelos", "heading": "Membrana, núcleo y mitocondrias", "tag": "ESTRUCTURA", "lead": "La membrana regula el intercambio, el núcleo guarda el material genético y las mitocondrias producen energía.", "durationMinutes": 3, "keyTakeaways": [{"number": "01", "text": "La membrana plasmática controla el paso de sustancias."}, {"number": "02", "text": "El núcleo contiene el ADN."}, {"number": "03", "text": "Las células vegetales poseen pared celular y cloroplastos."}]},
          {"id": 3, "navTitle": "Ideas clave", "heading": "Estructura y función", "tag": "CONSOLIDACIÓN", "lead": "La forma de cada organelo está relacionada con la función que realiza.", "durationMinutes": 2}
        ]
     }'::jsonb,
     210, 'd0000000-0000-0000-0000-000000000001', true, now()),

    ('a1000000-0000-0000-0000-000000000004', 'a0000000-0000-0000-0000-000000000001', 'f0000000-0000-0000-0000-000000000004',
     'Herencia mendeliana: cómo se transmiten los rasgos', 'text_summary'::content_type_enum,
     '{
        "summary": "Los alelos dominantes y recesivos explican la transmisión de caracteres.",
        "sections": [
          {"id": 1, "navTitle": "Idea principal", "heading": "Genes que se heredan", "tag": "GENÉTICA", "lead": "Cada progenitor aporta un alelo para cada carácter.", "durationMinutes": 2},
          {"id": 2, "navTitle": "Cruces", "heading": "Dominante y recesivo", "tag": "LEYES DE MENDEL", "lead": "El alelo dominante se manifiesta aunque haya uno recesivo; el recesivo necesita dos copias.", "durationMinutes": 3, "keyTakeaways": [{"number": "01", "text": "Aa es heterocigoto; AA y aa son homocigotos."}, {"number": "02", "text": "El cruce Aa x Aa produce una proporción fenotípica 3:1."}, {"number": "03", "text": "El alelo recesivo solo se expresa cuando no está el dominante."}]},
          {"id": 3, "navTitle": "Ideas clave", "heading": "Genotipo y fenotipo", "tag": "CONSOLIDACIÓN", "lead": "El genotipo es la combinación de alelos; el fenotipo es el rasgo observable.", "durationMinutes": 2}
        ]
     }'::jsonb,
     220, 'd0000000-0000-0000-0000-000000000001', true, now()),

    ('a1000000-0000-0000-0000-000000000005', 'a0000000-0000-0000-0000-000000000001', 'f0000000-0000-0000-0000-000000000005',
     'Ciclos biogeoquímicos: la materia en movimiento', 'text_summary'::content_type_enum,
     '{
        "summary": "El carbono, el nitrógeno y el agua circulan entre seres vivos y ambiente.",
        "sections": [
          {"id": 1, "navTitle": "Idea principal", "heading": "La materia se recicla", "tag": "CICLOS", "lead": "Los elementos químicos pasan del ambiente a los organismos y regresan al ambiente.", "durationMinutes": 2},
          {"id": 2, "navTitle": "Ciclo del carbono", "heading": "Fotosíntesis y respiración", "tag": "CARBONO", "lead": "La fotosíntesis retira carbono de la atmósfera y la respiración y la combustión lo devuelven.", "durationMinutes": 3, "keyTakeaways": [{"number": "01", "text": "Las bacterias fijadoras capturan nitrógeno atmosférico."}, {"number": "02", "text": "La respiración y la combustión liberan CO2."}, {"number": "03", "text": "El ciclo del agua distribuye agua dulce y regula el clima."}]},
          {"id": 3, "navTitle": "Ideas clave", "heading": "Equilibrio de los ecosistemas", "tag": "CONSOLIDACIÓN", "lead": "Alterar un ciclo puede afectar la disponibilidad de nutrientes y el clima.", "durationMinutes": 2}
        ]
     }'::jsonb,
     230, 'd0000000-0000-0000-0000-000000000001', true, now())
ON CONFLICT (id) DO NOTHING;

-- ----------------------------------------------------------------------------
-- 4. Preguntas (14 nuevas; Fotosíntesis ya tiene 1)
-- ----------------------------------------------------------------------------
INSERT INTO questions (id, tenant_id, knowledge_component_id, question_text, question_type, explanation, difficulty, created_by)
VALUES
    -- KC 1: Fotosíntesis
    ('00100000-0000-0000-0000-000000000002', 'a0000000-0000-0000-0000-000000000001', 'f0000000-0000-0000-0000-000000000001',
     '¿Qué gases intercambia la planta durante la fotosíntesis?', 'multiple_choice',
     'La planta absorbe dióxido de carbono y libera oxígeno como producto de la fotosíntesis.', 0.400, 'd0000000-0000-0000-0000-000000000001'),
    ('00100000-0000-0000-0000-000000000003', 'a0000000-0000-0000-0000-000000000001', 'f0000000-0000-0000-0000-000000000001',
     '¿Dónde ocurre principalmente la fotosíntesis en la célula vegetal?', 'multiple_choice',
     'La fotosíntesis ocurre en los cloroplastos, donde se encuentra la clorofila.', 0.380, 'd0000000-0000-0000-0000-000000000001'),

    -- KC 2: Respiración celular
    ('00200000-0000-0000-0000-000000000001', 'a0000000-0000-0000-0000-000000000001', 'f0000000-0000-0000-0000-000000000002',
     '¿Cuál es el objetivo principal de la respiración celular?', 'multiple_choice',
     'La respiración celular libera la energía almacenada en la glucosa y la convierte en ATP.', 0.500, 'd0000000-0000-0000-0000-000000000001'),
    ('00200000-0000-0000-0000-000000000002', 'a0000000-0000-0000-0000-000000000001', 'f0000000-0000-0000-0000-000000000002',
     '¿En qué organelo ocurre principalmente la respiración celular?', 'multiple_choice',
     'Las mitocondrias son el organelo donde se realiza la respiración celular aerobia.', 0.420, 'd0000000-0000-0000-0000-000000000001'),
    ('00200000-0000-0000-0000-000000000003', 'a0000000-0000-0000-0000-000000000001', 'f0000000-0000-0000-0000-000000000002',
     '¿Qué productos se generan en la respiración celular aerobia?', 'multiple_choice',
     'La oxidación de la glucosa produce dióxido de carbono, agua y energía en forma de ATP.', 0.550, 'd0000000-0000-0000-0000-000000000001'),

    -- KC 3: Estructura y función celular
    ('00300000-0000-0000-0000-000000000001', 'a0000000-0000-0000-0000-000000000001', 'f0000000-0000-0000-0000-000000000003',
     '¿Qué estructura controla el paso de sustancias hacia el interior de la célula?', 'multiple_choice',
     'La membrana plasmática es selectivamente permeable y regula el intercambio con el medio.', 0.440, 'd0000000-0000-0000-0000-000000000001'),
    ('00300000-0000-0000-0000-000000000002', 'a0000000-0000-0000-0000-000000000001', 'f0000000-0000-0000-0000-000000000003',
     '¿Qué función cumple el núcleo celular?', 'multiple_choice',
     'El núcleo almacena el material genético y dirige las actividades de la célula.', 0.410, 'd0000000-0000-0000-0000-000000000001'),
    ('00300000-0000-0000-0000-000000000003', 'a0000000-0000-0000-0000-000000000001', 'f0000000-0000-0000-0000-000000000003',
     '¿Qué estructura diferencia a una célula vegetal de una célula animal?', 'multiple_choice',
     'Las células vegetales poseen pared celular y cloroplastos, ausentes en las células animales.', 0.460, 'd0000000-0000-0000-0000-000000000001'),

    -- KC 4: Herencia mendeliana
    ('00400000-0000-0000-0000-000000000001', 'a0000000-0000-0000-0000-000000000001', 'f0000000-0000-0000-0000-000000000004',
     'Si un individuo tiene genotipo Aa, ¿cómo se describe?', 'multiple_choice',
     'Aa es heterocigoto porque presenta dos alelos diferentes para el mismo gen.', 0.480, 'd0000000-0000-0000-0000-000000000001'),
    ('00400000-0000-0000-0000-000000000002', 'a0000000-0000-0000-0000-000000000001', 'f0000000-0000-0000-0000-000000000004',
     '¿Qué proporción fenotípica se espera del cruce Aa x Aa?', 'multiple_choice',
     'El cruce Aa x Aa produce 3 individuos con el rasgo dominante por cada 1 con el recesivo.', 0.620, 'd0000000-0000-0000-0000-000000000001'),
    ('00400000-0000-0000-0000-000000000003', 'a0000000-0000-0000-0000-000000000001', 'f0000000-0000-0000-0000-000000000004',
     '¿Qué caracteriza a un alelo recesivo?', 'multiple_choice',
     'El alelo recesivo solo se manifiesta cuando no está presente el alelo dominante.', 0.520, 'd0000000-0000-0000-0000-000000000001'),

    -- KC 5: Ciclos biogeoquímicos
    ('00500000-0000-0000-0000-000000000001', 'a0000000-0000-0000-0000-000000000001', 'f0000000-0000-0000-0000-000000000005',
     '¿Qué procesos devuelven carbono a la atmósfera?', 'multiple_choice',
     'La respiración de los seres vivos y la combustión liberan dióxido de carbono.', 0.560, 'd0000000-0000-0000-0000-000000000001'),
    ('00500000-0000-0000-0000-000000000002', 'a0000000-0000-0000-0000-000000000001', 'f0000000-0000-0000-0000-000000000005',
     '¿Qué organismos fijan el nitrógeno atmosférico?', 'multiple_choice',
     'Las bacterias fijadoras transforman el nitrógeno atmosférico en compuestos utilizables por las plantas.', 0.640, 'd0000000-0000-0000-0000-000000000001'),
    ('00500000-0000-0000-0000-000000000003', 'a0000000-0000-0000-0000-000000000001', 'f0000000-0000-0000-0000-000000000005',
     '¿Por qué es importante el ciclo del agua?', 'multiple_choice',
     'El ciclo del agua distribuye agua dulce y contribuye a regular el clima.', 0.500, 'd0000000-0000-0000-0000-000000000001')
ON CONFLICT (id) DO NOTHING;

-- Opciones de respuesta (4 por pregunta, una sola correcta)
INSERT INTO question_options (id, question_id, option_text, is_correct, order_index)
VALUES
    -- KC1 / Q2
    ('11200000-0000-0000-0000-000000000001', '00100000-0000-0000-0000-000000000002', 'Absorbe dióxido de carbono y libera oxígeno.', true, 1),
    ('11200000-0000-0000-0000-000000000002', '00100000-0000-0000-0000-000000000002', 'Absorbe oxígeno y libera dióxido de carbono.', false, 2),
    ('11200000-0000-0000-0000-000000000003', '00100000-0000-0000-0000-000000000002', 'Absorbe nitrógeno y libera oxígeno.', false, 3),
    ('11200000-0000-0000-0000-000000000004', '00100000-0000-0000-0000-000000000002', 'No intercambia gases con el ambiente.', false, 4),
    -- KC1 / Q3
    ('11300000-0000-0000-0000-000000000001', '00100000-0000-0000-0000-000000000003', 'En los cloroplastos.', true, 1),
    ('11300000-0000-0000-0000-000000000002', '00100000-0000-0000-0000-000000000003', 'En las mitocondrias.', false, 2),
    ('11300000-0000-0000-0000-000000000003', '00100000-0000-0000-0000-000000000003', 'En el núcleo.', false, 3),
    ('11300000-0000-0000-0000-000000000004', '00100000-0000-0000-0000-000000000003', 'En los ribosomas.', false, 4),

    -- KC2 / Q1
    ('12100000-0000-0000-0000-000000000001', '00200000-0000-0000-0000-000000000001', 'Producir glucosa a partir de la luz.', false, 1),
    ('12100000-0000-0000-0000-000000000002', '00200000-0000-0000-0000-000000000001', 'Liberar la energía de la glucosa en forma de ATP.', true, 2),
    ('12100000-0000-0000-0000-000000000003', '00200000-0000-0000-0000-000000000001', 'Almacenar agua en las vacuolas.', false, 3),
    ('12100000-0000-0000-0000-000000000004', '00200000-0000-0000-0000-000000000001', 'Transportar minerales por el tallo.', false, 4),
    -- KC2 / Q2
    ('12200000-0000-0000-0000-000000000001', '00200000-0000-0000-0000-000000000002', 'En los cloroplastos.', false, 1),
    ('12200000-0000-0000-0000-000000000002', '00200000-0000-0000-0000-000000000002', 'En las mitocondrias.', true, 2),
    ('12200000-0000-0000-0000-000000000003', '00200000-0000-0000-0000-000000000002', 'En los lisosomas.', false, 3),
    ('12200000-0000-0000-0000-000000000004', '00200000-0000-0000-0000-000000000002', 'En las vacuolas.', false, 4),
    -- KC2 / Q3
    ('12300000-0000-0000-0000-000000000001', '00200000-0000-0000-0000-000000000003', 'Glucosa y oxígeno.', false, 1),
    ('12300000-0000-0000-0000-000000000002', '00200000-0000-0000-0000-000000000003', 'Solo oxígeno.', false, 2),
    ('12300000-0000-0000-0000-000000000003', '00200000-0000-0000-0000-000000000003', 'Dióxido de carbono, agua y ATP.', true, 3),
    ('12300000-0000-0000-0000-000000000004', '00200000-0000-0000-0000-000000000003', 'Proteínas y lípidos.', false, 4),

    -- KC3 / Q1
    ('13100000-0000-0000-0000-000000000001', '00300000-0000-0000-0000-000000000001', 'La pared celular.', false, 1),
    ('13100000-0000-0000-0000-000000000002', '00300000-0000-0000-0000-000000000001', 'La membrana plasmática.', true, 2),
    ('13100000-0000-0000-0000-000000000003', '00300000-0000-0000-0000-000000000001', 'El núcleo.', false, 3),
    ('13100000-0000-0000-0000-000000000004', '00300000-0000-0000-0000-000000000001', 'El citoplasma.', false, 4),
    -- KC3 / Q2
    ('13200000-0000-0000-0000-000000000001', '00300000-0000-0000-0000-000000000002', 'Producir ATP.', false, 1),
    ('13200000-0000-0000-0000-000000000002', '00300000-0000-0000-0000-000000000002', 'Almacenar el material genético.', true, 2),
    ('13200000-0000-0000-0000-000000000003', '00300000-0000-0000-0000-000000000002', 'Digerir desechos celulares.', false, 3),
    ('13200000-0000-0000-0000-000000000004', '00300000-0000-0000-0000-000000000002', 'Sintetizar lípidos.', false, 4),
    -- KC3 / Q3
    ('13300000-0000-0000-0000-000000000001', '00300000-0000-0000-0000-000000000003', 'La presencia de núcleo.', false, 1),
    ('13300000-0000-0000-0000-000000000002', '00300000-0000-0000-0000-000000000003', 'La presencia de mitocondrias.', false, 2),
    ('13300000-0000-0000-0000-000000000003', '00300000-0000-0000-0000-000000000003', 'La pared celular y los cloroplastos.', true, 3),
    ('13300000-0000-0000-0000-000000000004', '00300000-0000-0000-0000-000000000003', 'La membrana plasmática.', false, 4),

    -- KC4 / Q1
    ('14100000-0000-0000-0000-000000000001', '00400000-0000-0000-0000-000000000001', 'Heterocigoto.', true, 1),
    ('14100000-0000-0000-0000-000000000002', '00400000-0000-0000-0000-000000000001', 'Homocigoto dominante.', false, 2),
    ('14100000-0000-0000-0000-000000000003', '00400000-0000-0000-0000-000000000001', 'Homocigoto recesivo.', false, 3),
    ('14100000-0000-0000-0000-000000000004', '00400000-0000-0000-0000-000000000001', 'Haploide.', false, 4),
    -- KC4 / Q2
    ('14200000-0000-0000-0000-000000000001', '00400000-0000-0000-0000-000000000002', '1:1.', false, 1),
    ('14200000-0000-0000-0000-000000000002', '00400000-0000-0000-0000-000000000002', '3:1.', true, 2),
    ('14200000-0000-0000-0000-000000000003', '00400000-0000-0000-0000-000000000002', '9:3:3:1.', false, 3),
    ('14200000-0000-0000-0000-000000000004', '00400000-0000-0000-0000-000000000002', '1:2:1.', false, 4),
    -- KC4 / Q3
    ('14300000-0000-0000-0000-000000000001', '00400000-0000-0000-0000-000000000003', 'Se manifiesta siempre.', false, 1),
    ('14300000-0000-0000-0000-000000000002', '00400000-0000-0000-0000-000000000003', 'Solo se manifiesta si no está el alelo dominante.', true, 2),
    ('14300000-0000-0000-0000-000000000003', '00400000-0000-0000-0000-000000000003', 'No se hereda.', false, 3),
    ('14300000-0000-0000-0000-000000000004', '00400000-0000-0000-0000-000000000003', 'Solo existe en plantas.', false, 4),

    -- KC5 / Q1
    ('15100000-0000-0000-0000-000000000001', '00500000-0000-0000-0000-000000000001', 'La fotosíntesis.', false, 1),
    ('15100000-0000-0000-0000-000000000002', '00500000-0000-0000-0000-000000000001', 'La respiración y la combustión.', true, 2),
    ('15100000-0000-0000-0000-000000000003', '00500000-0000-0000-0000-000000000001', 'La evaporación.', false, 3),
    ('15100000-0000-0000-0000-000000000004', '00500000-0000-0000-0000-000000000001', 'La precipitación.', false, 4),
    -- KC5 / Q2
    ('15200000-0000-0000-0000-000000000001', '00500000-0000-0000-0000-000000000002', 'Las bacterias fijadoras.', true, 1),
    ('15200000-0000-0000-0000-000000000002', '00500000-0000-0000-0000-000000000002', 'Los hongos.', false, 2),
    ('15200000-0000-0000-0000-000000000003', '00500000-0000-0000-0000-000000000002', 'Las plantas carnívoras.', false, 3),
    ('15200000-0000-0000-0000-000000000004', '00500000-0000-0000-0000-000000000002', 'Las algas verdes.', false, 4),
    -- KC5 / Q3
    ('15300000-0000-0000-0000-000000000001', '00500000-0000-0000-0000-000000000003', 'Produce oxígeno.', false, 1),
    ('15300000-0000-0000-0000-000000000002', '00500000-0000-0000-0000-000000000003', 'Elimina los suelos.', false, 2),
    ('15300000-0000-0000-0000-000000000003', '00500000-0000-0000-0000-000000000003', 'Distribuye agua dulce y regula el clima.', true, 3),
    ('15300000-0000-0000-0000-000000000004', '00500000-0000-0000-0000-000000000003', 'Crea minerales nuevos.', false, 4)
ON CONFLICT (id) DO NOTHING;

-- ----------------------------------------------------------------------------
-- 5. Actividades (4 nuevas) + vinculación de preguntas y sección
-- ----------------------------------------------------------------------------
INSERT INTO activities (
    id, tenant_id, course_id, created_by, title, description,
    status, activity_type, feedback_policy, max_attempts, time_limit_minutes, published_at
) VALUES
    ('ac700000-0000-0000-0000-000000000002', 'a0000000-0000-0000-0000-000000000001', 'c0000000-0000-0000-0000-000000000001',
     'd0000000-0000-0000-0000-000000000001',
     'Respiración celular: energía para la vida',
     'Práctica formativa sobre la obtención de energía en las mitocondrias.',
     'published'::activity_status_enum, 'practice'::activity_type_enum, 'immediate_with_explanation'::feedback_policy_enum,
     20, 10, now() - interval '35 days'),
    ('ac700000-0000-0000-0000-000000000003', 'a0000000-0000-0000-0000-000000000001', 'c0000000-0000-0000-0000-000000000001',
     'd0000000-0000-0000-0000-000000000001',
     'La célula: estructura y funciones',
     'Práctica formativa sobre organelos y funciones celulares.',
     'published'::activity_status_enum, 'practice'::activity_type_enum, 'immediate_with_explanation'::feedback_policy_enum,
     20, 10, now() - interval '28 days'),
    ('ac700000-0000-0000-0000-000000000004', 'a0000000-0000-0000-0000-000000000001', 'c0000000-0000-0000-0000-000000000001',
     'd0000000-0000-0000-0000-000000000001',
     'Herencia mendeliana: transmitir rasgos',
     'Práctica formativa sobre alelos, genotipo y proporciones mendelianas.',
     'published'::activity_status_enum, 'practice'::activity_type_enum, 'immediate_with_explanation'::feedback_policy_enum,
     20, 10, now() - interval '21 days'),
    ('ac700000-0000-0000-0000-000000000005', 'a0000000-0000-0000-0000-000000000001', 'c0000000-0000-0000-0000-000000000001',
     'd0000000-0000-0000-0000-000000000001',
     'Ciclos biogeoquímicos: materia en movimiento',
     'Práctica formativa sobre los ciclos del carbono, nitrógeno y agua.',
     'published'::activity_status_enum, 'practice'::activity_type_enum, 'immediate_with_explanation'::feedback_policy_enum,
     20, 10, now() - interval '14 days')
ON CONFLICT (id) DO NOTHING;

-- La actividad canónica de Fotosíntesis permite intentos suficientes para la demo.
UPDATE activities
SET max_attempts = 20,
    published_at = COALESCE(published_at, now() - interval '42 days')
WHERE id = 'ac700000-0000-0000-0000-000000000001';

-- Preguntas por actividad
INSERT INTO activity_questions (activity_id, question_id, order_index)
VALUES
    ('ac700000-0000-0000-0000-000000000001', '00100000-0000-0000-0000-000000000002', 2),
    ('ac700000-0000-0000-0000-000000000001', '00100000-0000-0000-0000-000000000003', 3),
    ('ac700000-0000-0000-0000-000000000002', '00200000-0000-0000-0000-000000000001', 1),
    ('ac700000-0000-0000-0000-000000000002', '00200000-0000-0000-0000-000000000002', 2),
    ('ac700000-0000-0000-0000-000000000002', '00200000-0000-0000-0000-000000000003', 3),
    ('ac700000-0000-0000-0000-000000000003', '00300000-0000-0000-0000-000000000001', 1),
    ('ac700000-0000-0000-0000-000000000003', '00300000-0000-0000-0000-000000000002', 2),
    ('ac700000-0000-0000-0000-000000000003', '00300000-0000-0000-0000-000000000003', 3),
    ('ac700000-0000-0000-0000-000000000004', '00400000-0000-0000-0000-000000000001', 1),
    ('ac700000-0000-0000-0000-000000000004', '00400000-0000-0000-0000-000000000002', 2),
    ('ac700000-0000-0000-0000-000000000004', '00400000-0000-0000-0000-000000000003', 3),
    ('ac700000-0000-0000-0000-000000000005', '00500000-0000-0000-0000-000000000001', 1),
    ('ac700000-0000-0000-0000-000000000005', '00500000-0000-0000-0000-000000000002', 2),
    ('ac700000-0000-0000-0000-000000000005', '00500000-0000-0000-0000-000000000003', 3)
ON CONFLICT (activity_id, question_id) DO NOTHING;

-- Sección destinataria
INSERT INTO activity_sections (tenant_id, activity_id, section_id)
VALUES
    ('a0000000-0000-0000-0000-000000000001', 'ac700000-0000-0000-0000-000000000002', '5ec00000-0000-0000-0000-000000000001'),
    ('a0000000-0000-0000-0000-000000000001', 'ac700000-0000-0000-0000-000000000003', '5ec00000-0000-0000-0000-000000000001'),
    ('a0000000-0000-0000-0000-000000000001', 'ac700000-0000-0000-0000-000000000004', '5ec00000-0000-0000-0000-000000000001'),
    ('a0000000-0000-0000-0000-000000000001', 'ac700000-0000-0000-0000-000000000005', '5ec00000-0000-0000-0000-000000000001')
ON CONFLICT (activity_id, section_id) DO NOTHING;

-- ----------------------------------------------------------------------------
-- 6. Historial observado: 6 semanas x 2 actividades/semana por estudiante
--    Cada actividad aporta 3 respuestas -> 360 eventos.
--    La precisión depende de la habilidad del estudiante, la dificultad del KC
--    y la recencia. Todo es determinista (md5 + uuid_v5).
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS pg_temp._demo_answers;
CREATE TEMP TABLE _demo_answers AS
WITH acts(idx, activity_id, kc_id, course_id) AS (
    VALUES
        (0, 'ac700000-0000-0000-0000-000000000001'::uuid, 'f0000000-0000-0000-0000-000000000001'::uuid, 'c0000000-0000-0000-0000-000000000001'::uuid),
        (1, 'ac700000-0000-0000-0000-000000000002'::uuid, 'f0000000-0000-0000-0000-000000000002'::uuid, 'c0000000-0000-0000-0000-000000000001'::uuid),
        (2, 'ac700000-0000-0000-0000-000000000003'::uuid, 'f0000000-0000-0000-0000-000000000003'::uuid, 'c0000000-0000-0000-0000-000000000001'::uuid),
        (3, 'ac700000-0000-0000-0000-000000000004'::uuid, 'f0000000-0000-0000-0000-000000000004'::uuid, 'c0000000-0000-0000-0000-000000000001'::uuid),
        (4, 'ac700000-0000-0000-0000-000000000005'::uuid, 'f0000000-0000-0000-0000-000000000005'::uuid, 'c0000000-0000-0000-0000-000000000001'::uuid)
),
students AS (
    SELECT
        e.student_id,
        e.student_id_pseudo,
        e.id AS enrollment_id,
        row_number() OVER (ORDER BY e.student_id) AS s_idx
    FROM enrollments e
    WHERE e.section_id = '5ec00000-0000-0000-0000-000000000001'
      AND e.tenant_id = 'a0000000-0000-0000-0000-000000000001'
),
plan AS (
    SELECT
        st.student_id,
        st.student_id_pseudo,
        st.enrollment_id,
        st.s_idx,
        w.week_offset,
        act.idx AS a_idx,
        act.activity_id,
        act.kc_id,
        act.course_id,
        date_trunc('hour', now())
            - (w.week_offset * interval '7 days')
            - ((st.s_idx % 6) * interval '1 day')
            - interval '3 hours' AS started_at
    FROM students st
    CROSS JOIN generate_series(0, 5) AS w(week_offset)
    CROSS JOIN LATERAL (
        VALUES ((st.s_idx + w.week_offset) % 5), ((st.s_idx + w.week_offset + 2) % 5)
    ) AS sel(idx)
    JOIN acts act ON act.idx = sel.idx
)
SELECT
    uuid_generate_v5(uuid_ns_url(), 'nexo:demo:attempt:' || p.student_id::text || ':' || p.week_offset::text || ':' || p.activity_id::text) AS attempt_id,
    uuid_generate_v5(uuid_ns_url(), 'nexo:demo:attempt-key:' || p.student_id::text || ':' || p.week_offset::text || ':' || p.activity_id::text) AS attempt_key,
    'a0000000-0000-0000-0000-000000000001'::uuid AS tenant_id,
    p.enrollment_id,
    p.student_id,
    p.student_id_pseudo,
    p.activity_id,
    p.course_id,
    p.kc_id,
    p.s_idx,
    p.week_offset,
    aq.question_id,
    aq.order_index AS question_sequence,
    p.started_at,
    p.started_at + (aq.order_index * interval '2 minutes') AS event_ts,
    (r.u < r.pr) AS is_correct,
    CASE WHEN r.u < r.pr THEN co.id ELSE wo.id END AS selected_option_id,
    (30 + r.u * 55)::numeric(6,2) AS response_time_seconds,
    uuid_generate_v5(uuid_ns_url(), 'nexo:demo:event:' || p.student_id::text || ':' || p.week_offset::text || ':' || p.activity_id::text || ':' || aq.question_id::text) AS event_key
FROM plan p
JOIN activity_questions aq ON aq.activity_id = p.activity_id
JOIN questions q ON q.id = aq.question_id
CROSS JOIN LATERAL (
    SELECT
        (
            (('x' || substr(md5(
                'nexo:demo:ans:' || p.student_id::text || ':' || p.week_offset::text || ':' ||
                p.activity_id::text || ':' || aq.question_id::text
            ), 1, 8))::bit(32)::bigint)::numeric / 4294967295.0
        ) AS u,
        GREATEST(0.08, LEAST(0.92,
            0.48
            + 0.06 * (p.s_idx % 5)
            + 0.025 * (5 - p.week_offset)
            + (CASE p.a_idx
                   WHEN 0 THEN 0.15
                   WHEN 1 THEN 0.02
                   WHEN 2 THEN 0.10
                   WHEN 3 THEN -0.03
                   ELSE -0.06
               END)
        )) AS pr
) r
JOIN LATERAL (
    SELECT qo.id FROM question_options qo
    WHERE qo.question_id = q.id AND qo.is_correct
    ORDER BY qo.id LIMIT 1
) co ON true
JOIN LATERAL (
    SELECT qo.id FROM question_options qo
    WHERE qo.question_id = q.id AND NOT qo.is_correct
    ORDER BY qo.id LIMIT 1
) wo ON true;

-- Intentos completados (la nota refleja las respuestas registradas)
INSERT INTO quiz_attempts (
    id, tenant_id, enrollment_id, activity_id, started_at, completed_at, score,
    student_id, attempt_number, status, total_questions, correct_answers,
    idempotency_key, submitted_at
)
SELECT
    attempt_id,
    tenant_id,
    enrollment_id,
    activity_id,
    min(event_ts) - interval '2 minutes',
    max(event_ts) + interval '1 minute',
    round(100.0 * count(*) FILTER (WHERE is_correct) / count(*), 2),
    student_id,
    1,
    'completed'::attempt_status_enum,
    count(*)::int,
    count(*) FILTER (WHERE is_correct)::int,
    attempt_key,
    max(event_ts) + interval '1 minute'
FROM _demo_answers
GROUP BY attempt_id, tenant_id, enrollment_id, activity_id, student_id, attempt_key
ON CONFLICT DO NOTHING;

-- Eventos de respuesta (append-only)
INSERT INTO answer_events (
    id, tenant_id, attempt_id, student_id, question_id, knowledge_component_id,
    selected_option_id, is_correct, attempt_number, response_time_seconds,
    idempotency_key, event_timestamp, activity_id, course_id,
    question_sequence, response_time_ms
)
SELECT
    uuid_generate_v5(uuid_ns_url(), 'nexo:demo:event-id:' || event_key::text),
    tenant_id,
    attempt_id,
    student_id,
    question_id,
    kc_id,
    selected_option_id,
    is_correct,
    1,
    response_time_seconds,
    event_key,
    event_ts,
    activity_id,
    course_id,
    question_sequence,
    (response_time_seconds * 1000)::int
FROM _demo_answers
ON CONFLICT DO NOTHING;

-- ----------------------------------------------------------------------------
-- 7. Exposiciones a microcontenidos (telemetría de estudio semanal)
-- ----------------------------------------------------------------------------
INSERT INTO content_exposure_events (
    id, tenant_id, student_id, student_id_pseudo, microcontent_id,
    knowledge_component_id, exposure_type, started_at, completed_at,
    duration_seconds, active_reading_seconds, completion_status, session_id,
    idempotency_key, event_timestamp
)
SELECT
    uuid_generate_v5(uuid_ns_url(), 'nexo:demo:exposure-id:' || d.student_id::text || ':' || d.week_offset::text || ':' || d.kc_id::text),
    d.tenant_id,
    d.student_id,
    d.student_id_pseudo,
    mc.id,
    d.kc_id,
    'review_study'::exposure_type_enum,
    d.started_at - interval '20 minutes',
    d.started_at - interval '17 minutes',
    (150 + (abs(hashtext(d.student_id::text || ':' || d.week_offset::text)) % 120))::numeric(8,2),
    (150 + (abs(hashtext(d.student_id::text || ':' || d.week_offset::text)) % 120))::numeric(8,2),
    'completed'::exposure_completion_status_enum,
    uuid_generate_v5(uuid_ns_url(), 'nexo:demo:session:' || d.student_id::text || ':' || d.week_offset::text),
    uuid_generate_v5(uuid_ns_url(), 'nexo:demo:exposure-key:' || d.student_id::text || ':' || d.week_offset::text || ':' || d.kc_id::text),
    d.started_at - interval '20 minutes'
FROM (
    SELECT DISTINCT ON (student_id, week_offset)
        student_id, student_id_pseudo, tenant_id, kc_id, started_at, week_offset
    FROM _demo_answers
    ORDER BY student_id, week_offset, activity_id
) d
JOIN microcontents mc
  ON mc.knowledge_component_id = d.kc_id
 AND mc.is_published = true
ON CONFLICT DO NOTHING;

-- ----------------------------------------------------------------------------
-- 8. Recomendaciones de repaso (política de reglas, sin predicciones)
--    2 pendientes por estudiante (sus 2 KC con menor precisión observada)
--    1 completada por estudiante (KC con mayor precisión)
-- ----------------------------------------------------------------------------
WITH kc_acc AS (
    SELECT
        ae.student_id,
        ae.knowledge_component_id,
        count(*)::int AS total,
        count(*) FILTER (WHERE ae.is_correct)::int AS correct
    FROM answer_events ae
    JOIN enrollments e
      ON e.student_id = ae.student_id
     AND e.tenant_id = ae.tenant_id
    WHERE e.section_id = '5ec00000-0000-0000-0000-000000000001'
    GROUP BY ae.student_id, ae.knowledge_component_id
),
ranked AS (
    SELECT
        *,
        row_number() OVER (
            PARTITION BY student_id
            ORDER BY (correct::numeric / NULLIF(total, 0)) ASC, total DESC, knowledge_component_id
        ) AS rn_low
    FROM kc_acc
)
INSERT INTO recommendations (
    id, tenant_id, prediction_id, student_id, knowledge_component_id,
    microcontent_id, selection_method, decision_reason, status, created_at,
    policy_name, policy_version, scheduled_for, cooldown_until,
    completed_at, expires_at, idempotency_key
)
SELECT
    uuid_generate_v5(uuid_ns_url(), 'nexo:demo:rec:pending:' || r.student_id::text || ':' || r.knowledge_component_id::text),
    'a0000000-0000-0000-0000-000000000001',
    NULL,
    r.student_id,
    r.knowledge_component_id,
    mc.id,
    'rule_based_fallback'::recommendation_method_enum,
    'Repaso preventivo programado por regla de precisión observada; el MVP aún no cuenta con un artefacto predictivo validado.',
    'pending'::recommendation_status_enum,
    now() - interval '1 day',
    'preventive_spaced_repetition',
    '1.0.0',
    now() + ((r.rn_low - 1) * interval '1 day') - interval '2 hours',
    now() - interval '1 day',
    NULL,
    now() + interval '7 days',
    uuid_generate_v5(uuid_ns_url(), 'nexo:demo:rec-key:pending:' || r.student_id::text || ':' || r.knowledge_component_id::text)
FROM ranked r
JOIN LATERAL (
    SELECT id FROM microcontents
    WHERE knowledge_component_id = r.knowledge_component_id AND is_published
    ORDER BY id LIMIT 1
) mc ON true
WHERE r.rn_low <= 2
ON CONFLICT DO NOTHING;

WITH kc_acc AS (
    SELECT
        ae.student_id,
        ae.knowledge_component_id,
        count(*)::int AS total,
        count(*) FILTER (WHERE ae.is_correct)::int AS correct
    FROM answer_events ae
    JOIN enrollments e
      ON e.student_id = ae.student_id
     AND e.tenant_id = ae.tenant_id
    WHERE e.section_id = '5ec00000-0000-0000-0000-000000000001'
    GROUP BY ae.student_id, ae.knowledge_component_id
),
ranked AS (
    SELECT
        *,
        row_number() OVER (
            PARTITION BY student_id
            ORDER BY (correct::numeric / NULLIF(total, 0)) DESC, total DESC, knowledge_component_id
        ) AS rn_high
    FROM kc_acc
)
INSERT INTO recommendations (
    id, tenant_id, prediction_id, student_id, knowledge_component_id,
    microcontent_id, selection_method, decision_reason, status, created_at,
    policy_name, policy_version, scheduled_for, cooldown_until,
    completed_at, expires_at, idempotency_key
)
SELECT
    uuid_generate_v5(uuid_ns_url(), 'nexo:demo:rec:completed:' || r.student_id::text || ':' || r.knowledge_component_id::text),
    'a0000000-0000-0000-0000-000000000001',
    NULL,
    r.student_id,
    r.knowledge_component_id,
    mc.id,
    'rule_based_fallback'::recommendation_method_enum,
    'Repaso completado dentro de la política de reglas; sin inferencia predictiva.',
    'completed'::recommendation_status_enum,
    now() - interval '4 days',
    'preventive_spaced_repetition',
    '1.0.0',
    now() - interval '3 days',
    now() - interval '4 days',
    now() - interval '2 days',
    now() + interval '3 days',
    uuid_generate_v5(uuid_ns_url(), 'nexo:demo:rec-key:completed:' || r.student_id::text || ':' || r.knowledge_component_id::text)
FROM ranked r
JOIN LATERAL (
    SELECT id FROM microcontents
    WHERE knowledge_component_id = r.knowledge_component_id AND is_published
    ORDER BY id LIMIT 1
) mc ON true
WHERE r.rn_high = 1
ON CONFLICT DO NOTHING;

DROP TABLE IF EXISTS pg_temp._demo_answers;

COMMIT;

-- ----------------------------------------------------------------------------
-- 9. Resumen de verificación (se muestra al ejecutar el script)
-- ----------------------------------------------------------------------------
SELECT 'estudiantes' AS entidad, count(*)::text AS total FROM profiles WHERE role = 'student'
UNION ALL SELECT 'matriculas', count(*)::text FROM enrollments
UNION ALL SELECT 'componentes_kc', count(*)::text FROM knowledge_components
UNION ALL SELECT 'microcontenidos', count(*)::text FROM microcontents
UNION ALL SELECT 'preguntas', count(*)::text FROM questions
UNION ALL SELECT 'actividades', count(*)::text FROM activities
UNION ALL SELECT 'intentos', count(*)::text FROM quiz_attempts
UNION ALL SELECT 'respuestas', count(*)::text FROM answer_events
UNION ALL SELECT 'exposiciones', count(*)::text FROM content_exposure_events
UNION ALL SELECT 'recomendaciones', count(*)::text FROM recommendations;


-- ============================================================================
-- VERIFICACIÓN FINAL: TABLAS Y CONTEO DE DATOS SEMILLA
-- ============================================================================
SELECT 'estudiantes' AS entidad, count(*)::text AS total FROM profiles WHERE role = 'student'
UNION ALL SELECT 'docentes', count(*)::text FROM profiles WHERE role = 'teacher'
UNION ALL SELECT 'matriculas', count(*)::text FROM enrollments
UNION ALL SELECT 'componentes_kc', count(*)::text FROM knowledge_components
UNION ALL SELECT 'microcontenidos', count(*)::text FROM microcontents
UNION ALL SELECT 'preguntas', count(*)::text FROM questions
UNION ALL SELECT 'actividades', count(*)::text FROM activities
UNION ALL SELECT 'intentos', count(*)::text FROM quiz_attempts
UNION ALL SELECT 'respuestas (inmutables)', count(*)::text FROM answer_events
UNION ALL SELECT 'exposiciones (inmutables)', count(*)::text FROM content_exposure_events
UNION ALL SELECT 'recomendaciones', count(*)::text FROM recommendations;
