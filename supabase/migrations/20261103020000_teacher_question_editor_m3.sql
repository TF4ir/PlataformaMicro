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
