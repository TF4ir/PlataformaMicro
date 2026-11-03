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
