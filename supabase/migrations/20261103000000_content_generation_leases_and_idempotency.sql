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
