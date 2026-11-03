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
