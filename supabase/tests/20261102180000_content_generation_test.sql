-- ============================================================================
-- PLATAFORMA DE MICROAPRENDIZAJE ADAPTATIVO
-- PRUEBAS DE SEGURIDAD MULTITENANT Y CONTROL DE ACCESO RLS (ADR-0004 / M1)
-- Suite pgTAP: Generación Asistida, Borradores, Notificaciones y Storage
-- File: supabase/tests/20261102180000_content_generation_test.sql
-- ============================================================================

BEGIN;

CREATE EXTENSION IF NOT EXISTS pgtap;

CREATE SCHEMA IF NOT EXISTS tests;
GRANT USAGE ON SCHEMA tests TO authenticated, anon, public;

-- Planificamos 30 pruebas formales que cubren exhaustivamente las 10 verificaciones obligatorias y vectores de ataque
SELECT plan(30);

-- ============================================================================
-- 0. CONFIGURACIÓN DE ACTORES FICTICIOS Y DATOS BASE
-- ============================================================================

-- Helper para suplantación de identidad en pruebas RLS
CREATE OR REPLACE FUNCTION tests.authenticate_as(p_user_id UUID, p_role TEXT DEFAULT 'authenticated')
RETURNS void LANGUAGE plpgsql AS $$
BEGIN
    PERFORM set_config('request.jwt.claim.sub', COALESCE(p_user_id::text, ''), true);
    PERFORM set_config('request.jwt.claim.role', p_role, true);
END;
$$;
GRANT EXECUTE ON FUNCTION tests.authenticate_as(UUID, TEXT) TO authenticated, anon, public;

DO $$
DECLARE
    tenant_a UUID := '11111111-1111-1111-1111-111111111111';
    tenant_b UUID := '22222222-2222-2222-2222-222222222222';
    teacher_a1 UUID := '11111111-1111-1111-1111-aaaaaaaaaaaa';
    student_a1 UUID := '11111111-1111-1111-1111-bbbbbbbbbbbb';
    teacher_b1 UUID := '22222222-2222-2222-2222-aaaaaaaaaaaa';
    student_b1 UUID := '22222222-2222-2222-2222-bbbbbbbbbbbb';
    admin_a UUID := '99999999-9999-9999-9999-aaaaaaaaaaaa';
    admin_b UUID := '99999999-9999-9999-9999-bbbbbbbbbbbb';
    course_a1 UUID := '11111111-1111-1111-1111-cccccccccccc';
    course_a2 UUID := '11111111-1111-1111-1111-cccccccccccd';
    course_b1 UUID := '22222222-2222-2222-2222-cccccccccccc';
    sec_a1 UUID := '11111111-1111-1111-1111-dddddddddddd';
    sec_b1 UUID := '22222222-2222-2222-2222-dddddddddddd';
BEGIN
    -- Limpieza previa de posibles ejecuciones manuales previas
    PERFORM set_config('storage.allow_delete_query', 'true', true);
    DELETE FROM storage.objects WHERE bucket_id = 'teacher-materials';
    DELETE FROM notifications WHERE id IN ('ffffffff-1111-1111-1111-111111111111', 'ffffffff-2222-2222-2222-222222222222');
    DELETE FROM question_drafts WHERE id = 'dddddddd-1111-1111-1111-111111111111';
    DELETE FROM content_generation_jobs WHERE id IN ('aaaaaaaa-1111-1111-1111-111111111111', 'bbbbbbbb-2222-2222-2222-222222222222');
    -- Tenants
    INSERT INTO tenants (id, name, slug) VALUES 
        (tenant_a, 'Colegio A', 'colegio-a-test'),
        (tenant_b, 'Colegio B', 'colegio-b-test')
    ON CONFLICT (id) DO NOTHING;

    -- Usuarios en auth.users
    INSERT INTO auth.users (id, email) VALUES
        (teacher_a1, 'teacher_a1@test.edu'),
        (student_a1, 'student_a1@test.edu'),
        (teacher_b1, 'teacher_b1@test.edu'),
        (student_b1, 'student_b1@test.edu'),
        (admin_a, 'admin_a@test.edu'),
        (admin_b, 'admin_b@test.edu')
    ON CONFLICT (id) DO NOTHING;

    -- Perfiles
    INSERT INTO profiles (id, tenant_id, full_name, role) VALUES
        (teacher_a1, tenant_a, 'Docente A1', 'teacher'),
        (student_a1, tenant_a, 'Estudiante A1', 'student'),
        (teacher_b1, tenant_b, 'Docente B1', 'teacher'),
        (student_b1, tenant_b, 'Estudiante B1', 'student'),
        (admin_a, tenant_a, 'Administrador A', 'admin'),
        (admin_b, tenant_b, 'Administrador B', 'admin')
    ON CONFLICT (id) DO UPDATE SET role = EXCLUDED.role, tenant_id = EXCLUDED.tenant_id;

    -- Cursos
    INSERT INTO courses (id, tenant_id, code, name) VALUES
        (course_a1, tenant_a, 'CIEN-A1', 'Ciencias A1'),
        (course_a2, tenant_a, 'LETR-A2', 'Letras A2 (No asignado a A1)'),
        (course_b1, tenant_b, 'CIEN-B1', 'Ciencias B1')
    ON CONFLICT (id) DO NOTHING;

    -- Secciones y Asignación Docente
    INSERT INTO sections (id, tenant_id, course_id, teacher_id, name) VALUES
        (sec_a1, tenant_a, course_a1, teacher_a1, '5to A'),
        (sec_b1, tenant_b, course_b1, teacher_b1, '5to B')
    ON CONFLICT (id) DO NOTHING;

    -- Matrículas
    INSERT INTO enrollments (id, tenant_id, section_id, student_id) VALUES
        ('11111111-1111-1111-1111-eeeeeeeeeeee', tenant_a, sec_a1, student_a1),
        ('22222222-2222-2222-2222-eeeeeeeeeeee', tenant_b, sec_b1, student_b1)
    ON CONFLICT (id) DO NOTHING;

    -- Trabajos y borradores base preexistentes (creados como superuser para pruebas de lectura)
    INSERT INTO content_generation_jobs (
        id, tenant_id, course_id, created_by, storage_bucket, storage_path,
        original_filename, mime_type, file_size_bytes, file_checksum, provider, model_id, status
    ) VALUES 
    (
        'aaaaaaaa-0000-0000-0000-111111111111',
        tenant_a, course_a1, teacher_a1,
        'teacher-materials', '11111111-1111-1111-1111-111111111111/doc_base_a.pdf',
        'doc_base_a.pdf', 'application/pdf', 1024, 'sha-a0', 'google_vertex', 'gemini-1.5', 'queued'
    ),
    (
        'bbbbbbbb-2222-2222-2222-222222222222',
        tenant_b, course_b1, teacher_b1,
        'teacher-materials', '22222222-2222-2222-2222-222222222222/doc_b.pdf',
        'doc_b.pdf', 'application/pdf', 1024, 'sha-b1', 'google_vertex', 'gemini-1.5', 'queued'
    ) ON CONFLICT (id) DO NOTHING;

    INSERT INTO question_drafts (
        id, tenant_id, generation_job_id, suggested_kc_name, question_text, explanation, options, status
    ) VALUES (
        'dddddddd-1111-1111-1111-111111111111',
        tenant_a, 'aaaaaaaa-0000-0000-0000-111111111111',
        'Fotosíntesis', '¿En qué organelo ocurre la fotosíntesis?', 'En el cloroplasto',
        '[{"text": "Cloroplasto", "is_correct": true}, {"text": "Mitocondria", "is_correct": false}]'::jsonb,
        'draft'
    ) ON CONFLICT (id) DO NOTHING;

    -- Notificaciones base preexistentes
    INSERT INTO notifications (
        id, tenant_id, student_id, notification_type, title, body, target_path, deduplication_key
    ) VALUES
        ('ffffffff-1111-1111-1111-111111111111', tenant_a, student_a1, 'review_reminder', 'Aviso A1', 'Cuerpo A1', '/learn/1', 'key:notif:a1'),
        ('ffffffff-2222-2222-2222-222222222222', tenant_b, student_b1, 'review_reminder', 'Aviso B1', 'Cuerpo B1', '/learn/2', 'key:notif:b1')
    ON CONFLICT (id) DO NOTHING;

    -- Objeto de storage en Tenant A para pruebas de acceso
    INSERT INTO storage.objects (id, bucket_id, name, owner)
    VALUES (
        '10000000-0000-0000-0000-000000000001',
        'teacher-materials',
        '11111111-1111-1111-1111-111111111111/material_docente.pdf',
        teacher_a1
    ) ON CONFLICT (id) DO NOTHING;
END $$;

-- Activamos el rol authenticated para que PostgreSQL evalúe estrictamente las políticas RLS
SET LOCAL ROLE authenticated;

-- ============================================================================
-- VERIFICACIÓN 1: A1 puede crear y consultar sus trabajos autorizados
-- ============================================================================
SELECT tests.authenticate_as('11111111-1111-1111-1111-aaaaaaaaaaaa'::uuid);

SELECT lives_ok(
    $$
    INSERT INTO content_generation_jobs (
        id, tenant_id, course_id, created_by, storage_bucket, storage_path,
        original_filename, mime_type, file_size_bytes, file_checksum, provider, model_id
    ) VALUES (
        'aaaaaaaa-1111-1111-1111-111111111111',
        '11111111-1111-1111-1111-111111111111',
        '11111111-1111-1111-1111-cccccccccccc',
        '11111111-1111-1111-1111-aaaaaaaaaaaa',
        'teacher-materials',
        '11111111-1111-1111-1111-111111111111/ciencias.pdf',
        'ciencias.pdf',
        'application/pdf',
        2048,
        'sha256-a1',
        'google_vertex',
        'gemini-1.5'
    )
    $$,
    '1.1 Docente A1 puede crear trabajo en curso asignado con su tenant propio'
);

SELECT results_eq(
    $$ SELECT count(*)::integer FROM content_generation_jobs WHERE id = 'aaaaaaaa-1111-1111-1111-111111111111' $$,
    ARRAY[1],
    '1.2 Docente A1 puede consultar su trabajo autorizado creado'
);

-- ============================================================================
-- VERIFICACIÓN 2: A1 no puede crear trabajos con el tenant de B ni paths cruzados
-- ============================================================================
SELECT tests.authenticate_as('11111111-1111-1111-1111-aaaaaaaaaaaa'::uuid);

SELECT throws_ok(
    $$
    INSERT INTO content_generation_jobs (
        id, tenant_id, course_id, created_by, storage_bucket, storage_path,
        original_filename, mime_type, file_size_bytes, file_checksum, provider, model_id
    ) VALUES (
        'aaaaaaaa-2222-2222-2222-111111111111',
        '22222222-2222-2222-2222-222222222222', -- Tenant B (Violación cross-tenant)
        NULL,
        '11111111-1111-1111-1111-aaaaaaaaaaaa',
        'teacher-materials',
        '22222222-2222-2222-2222-222222222222/ciencias.pdf',
        'ciencias.pdf',
        'application/pdf',
        2048,
        'sha256-cross',
        'google_vertex',
        'gemini-1.5'
    )
    $$,
    '42501', -- Insufficient privilege / RLS check violation
    NULL,
    '2.1 A1 no puede crear trabajos con el tenant de B (Rechazado por RLS WITH CHECK)'
);

SELECT throws_ok(
    $$
    INSERT INTO content_generation_jobs (
        id, tenant_id, course_id, created_by, storage_bucket, storage_path,
        original_filename, mime_type, file_size_bytes, file_checksum, provider, model_id
    ) VALUES (
        'aaaaaaaa-beef-beef-1111-111111111111',
        '11111111-1111-1111-1111-111111111111',
        '11111111-1111-1111-1111-cccccccccccc',
        '11111111-1111-1111-1111-aaaaaaaaaaaa',
        'teacher-materials',
        '22222222-2222-2222-2222-222222222222/stolen_b.pdf', -- Inyección de path de Tenant B
        'stolen.pdf', 'application/pdf', 2048, 'sha256-cross-path', 'google_vertex', 'gemini-1.5'
    )
    $$,
    NULL,
    NULL,
    '2.2 A1 no puede crear trabajo con storage_path de otro tenant (Aislamiento de almacenamiento)'
);

-- ============================================================================
-- VERIFICACIÓN 3: A1 no puede consultar ni modificar trabajos no autorizados
-- ============================================================================
SELECT tests.authenticate_as('11111111-1111-1111-1111-aaaaaaaaaaaa'::uuid);

-- A1 no puede ver trabajos de Institución B
SELECT is_empty(
    $$ SELECT * FROM content_generation_jobs WHERE id = 'bbbbbbbb-2222-2222-2222-222222222222' $$,
    '3.1 A1 no puede consultar trabajos de otra institución (Tenant B)'
);

-- A1 no puede crear trabajos para cursos de su mismo tenant donde NO es docente titular
SELECT throws_ok(
    $$
    INSERT INTO content_generation_jobs (
        id, tenant_id, course_id, created_by, storage_bucket, storage_path,
        original_filename, mime_type, file_size_bytes, file_checksum, provider, model_id
    ) VALUES (
        'aaaaaaaa-9999-9999-9999-111111111111',
        '11111111-1111-1111-1111-111111111111',
        '11111111-1111-1111-1111-cccccccccccd', -- Curso A2 (Letras, no asignado a A1)
        '11111111-1111-1111-1111-aaaaaaaaaaaa',
        'teacher-materials',
        '11111111-1111-1111-1111-111111111111/letras.pdf',
        'letras.pdf',
        'application/pdf',
        2048,
        'sha256-letras',
        'google_vertex',
        'gemini-1.5'
    )
    $$,
    '42501',
    NULL,
    '3.2 A1 no puede crear trabajos para cursos donde no es docente autorizado'
);

-- ============================================================================
-- VERIFICACIÓN 4: B1 no puede consultar borradores de A
-- ============================================================================
SELECT tests.authenticate_as('22222222-2222-2222-2222-aaaaaaaaaaaa'::uuid); -- Docente B1

SELECT is_empty(
    $$ SELECT * FROM question_drafts WHERE id = 'dddddddd-1111-1111-1111-111111111111' $$,
    '4. Docente B1 no puede consultar borradores generados para la Institución A'
);

-- ============================================================================
-- VERIFICACIÓN 5: Ningún estudiante puede crear trabajos o borradores
-- ============================================================================
SELECT tests.authenticate_as('11111111-1111-1111-1111-bbbbbbbbbbbb'::uuid); -- Estudiante A1

SELECT throws_ok(
    $$
    INSERT INTO content_generation_jobs (
        id, tenant_id, course_id, created_by, storage_bucket, storage_path,
        original_filename, mime_type, file_size_bytes, file_checksum, provider, model_id
    ) VALUES (
        'cccccccc-1111-1111-1111-111111111111',
        '11111111-1111-1111-1111-111111111111',
        '11111111-1111-1111-1111-cccccccccccc',
        '11111111-1111-1111-1111-bbbbbbbbbbbb',
        'teacher-materials', 'estudiante.pdf', 'estudiante.pdf', 'application/pdf', 1024, 'sha-e', 'test', 'test'
    )
    $$,
    '42501',
    NULL,
    '5.1 Estudiante no puede crear trabajos de generación'
);

SELECT throws_ok(
    $$
    INSERT INTO question_drafts (
        id, tenant_id, generation_job_id, suggested_kc_name, question_text, explanation, options
    ) VALUES (
        'dddddddd-3333-3333-3333-111111111111',
        '11111111-1111-1111-1111-111111111111',
        'aaaaaaaa-1111-1111-1111-111111111111',
        'Genética', 'Pregunta est', 'Expl', '[]'::jsonb
    )
    $$,
    '42501',
    NULL,
    '5.2 Estudiante no puede crear borradores de preguntas'
);

-- ============================================================================
-- VERIFICACIÓN 6: Un estudiante solo puede leer sus notificaciones y aislamiento
-- ============================================================================
SELECT tests.authenticate_as('11111111-1111-1111-1111-bbbbbbbbbbbb'::uuid); -- Estudiante A1

SELECT results_eq(
    $$ SELECT id FROM notifications $$,
    ARRAY['ffffffff-1111-1111-1111-111111111111'::uuid],
    '6.1 Estudiante A1 solo puede ver sus propias notificaciones'
);

SELECT is_empty(
    $$ SELECT * FROM notifications WHERE id = 'ffffffff-2222-2222-2222-222222222222' $$,
    '6.2 Estudiante A1 no puede ver notificaciones del Estudiante B1'
);

-- Admin B no puede consultar notificaciones de Tenant A
SELECT tests.authenticate_as('99999999-9999-9999-9999-bbbbbbbbbbbb'::uuid); -- Admin B
SELECT is_empty(
    $$ SELECT * FROM notifications WHERE tenant_id = '11111111-1111-1111-1111-111111111111' $$,
    '6.3 Administrador de Institución B no puede consultar notificaciones de Institución A'
);

-- Admin B no puede eliminar notificaciones de Tenant A
DELETE FROM notifications WHERE id = 'ffffffff-1111-1111-1111-111111111111';
SELECT tests.authenticate_as('99999999-9999-9999-9999-aaaaaaaaaaaa'::uuid); -- Admin A
SELECT results_eq(
    $$ SELECT count(*)::integer FROM notifications WHERE id = 'ffffffff-1111-1111-1111-111111111111' $$,
    ARRAY[1],
    '6.4 Administrador de Institución B no puede eliminar notificaciones de Institución A'
);

-- ============================================================================
-- VERIFICACIÓN 7: Estudiante solo modifica estado de lectura de sus avisos
-- ============================================================================
SELECT tests.authenticate_as('11111111-1111-1111-1111-bbbbbbbbbbbb'::uuid); -- Estudiante A1

SELECT lives_ok(
    $$ UPDATE notifications SET read_at = now() WHERE id = 'ffffffff-1111-1111-1111-111111111111' $$,
    '7.1 Estudiante puede marcar su notificación como leída (read_at)'
);

SELECT throws_ok(
    $$ UPDATE notifications SET title = 'Aviso falsificado' WHERE id = 'ffffffff-1111-1111-1111-111111111111' $$,
    NULL, -- Error de disparador o permiso de columna
    NULL,
    '7.2 Estudiante no puede alterar el título o contenido de su notificación'
);

SELECT throws_ok(
    $$ UPDATE notifications SET student_id = '11111111-1111-1111-1111-aaaaaaaaaaaa'::uuid WHERE id = 'ffffffff-1111-1111-1111-111111111111' $$,
    NULL,
    NULL,
    '7.3 Estudiante no puede alterar el destinatario o deduplication_key de su notificación'
);

-- ============================================================================
-- VERIFICACIÓN 8: Ningún estudiante puede insertar notificaciones propias
-- ============================================================================
SELECT tests.authenticate_as('11111111-1111-1111-1111-bbbbbbbbbbbb'::uuid); -- Estudiante A1

SELECT throws_ok(
    $$
    INSERT INTO notifications (
        id, tenant_id, student_id, notification_type, title, body, target_path, deduplication_key
    ) VALUES (
        'ffffffff-9999-9999-9999-111111111111',
        '11111111-1111-1111-1111-111111111111',
        '11111111-1111-1111-1111-bbbbbbbbbbbb',
        'review_reminder', 'Spam', 'Spam body', '/spam', 'fake:key:2'
    )
    $$,
    '42501',
    NULL,
    '8. Ningún estudiante puede insertar notificaciones propias ni para terceros'
);

-- ============================================================================
-- VERIFICACIÓN 9: El acceso al bucket respeta tenant y propietario
-- ============================================================================
-- Docente A1 sube archivo en carpeta de su institución
SELECT tests.authenticate_as('11111111-1111-1111-1111-aaaaaaaaaaaa'::uuid);

SELECT lives_ok(
    $$
    INSERT INTO storage.objects (id, bucket_id, name, owner)
    VALUES (
        '10000000-0000-0000-0000-000000000002',
        'teacher-materials',
        '11111111-1111-1111-1111-111111111111/archivo_docente_a1.pdf',
        '11111111-1111-1111-1111-aaaaaaaaaaaa'
    )
    $$,
    '9.1 Docente A1 puede subir archivos a su carpeta de tenant en bucket privado'
);

-- Docente A1 no puede subir en carpeta de Institución B
SELECT throws_ok(
    $$
    INSERT INTO storage.objects (id, bucket_id, name, owner)
    VALUES (
        '10000000-0000-0000-0000-000000000003',
        'teacher-materials',
        '22222222-2222-2222-2222-222222222222/inyeccion_b.pdf',
        '11111111-1111-1111-1111-aaaaaaaaaaaa'
    )
    $$,
    '42501',
    NULL,
    '9.2 Docente A1 no puede subir archivos en la carpeta de Tenant B'
);

-- Estudiante A1 no puede subir a teacher-materials
SELECT tests.authenticate_as('11111111-1111-1111-1111-bbbbbbbbbbbb'::uuid);
SELECT throws_ok(
    $$
    INSERT INTO storage.objects (id, bucket_id, name, owner)
    VALUES (
        '10000000-0000-0000-0000-000000000004',
        'teacher-materials',
        '11111111-1111-1111-1111-111111111111/estudiante_hack.pdf',
        '11111111-1111-1111-1111-bbbbbbbbbbbb'
    )
    $$,
    '42501',
    NULL,
    '9.3 Estudiante A1 no puede subir archivos al bucket teacher-materials'
);

-- Docente B1 no puede ver archivos de Tenant A
SELECT tests.authenticate_as('22222222-2222-2222-2222-aaaaaaaaaaaa'::uuid);
SELECT is_empty(
    $$ SELECT * FROM storage.objects WHERE id = '10000000-0000-0000-0000-000000000001' $$,
    '9.4 Docente B1 no puede consultar archivos de almacenamiento de Institución A'
);

-- Administrador A puede ver archivos de su tenant
SELECT tests.authenticate_as('99999999-9999-9999-9999-aaaaaaaaaaaa'::uuid);
SELECT results_eq(
    $$ SELECT count(*)::integer FROM storage.objects WHERE id = '10000000-0000-0000-0000-000000000001' $$,
    ARRAY[1],
    '9.5 Administrador de Institución A puede auditar archivos de su tenant'
);

-- ============================================================================
-- VERIFICACIÓN 10: Bloqueo de alteración directa de estados sensibles
-- ============================================================================
SELECT tests.authenticate_as('11111111-1111-1111-1111-aaaaaaaaaaaa'::uuid); -- Docente A1

-- Docente no puede marcar un borrador como 'approved' mediante UPDATE directo
SELECT throws_ok(
    $$ UPDATE question_drafts SET status = 'approved' WHERE id = 'dddddddd-1111-1111-1111-111111111111' $$,
    NULL,
    NULL,
    '10.1 Docente no puede aprobar directamente un borrador vía SQL (Requiere HITL transaccional)'
);

-- Docente no puede asignar approved_question_id directamente
SELECT throws_ok(
    $$ UPDATE question_drafts SET approved_question_id = gen_random_uuid() WHERE id = 'dddddddd-1111-1111-1111-111111111111' $$,
    NULL,
    NULL,
    '10.2 Docente no puede asignar approved_question_id de forma directa vía SQL'
);

-- Docente no puede alterar el estado de un trabajo de generación directamente vía SQL
SELECT throws_ok(
    $$ UPDATE content_generation_jobs SET status = 'approved' WHERE id = 'aaaaaaaa-1111-1111-1111-111111111111' $$,
    NULL,
    NULL,
    '10.3 Docente no puede alterar el status de content_generation_jobs (Reservado a backend)'
);

-- Docente no puede insertar trabajo con status != 'queued' directamente vía INSERT
SELECT throws_ok(
    $$
    INSERT INTO content_generation_jobs (
        id, tenant_id, course_id, created_by, storage_bucket, storage_path,
        original_filename, mime_type, file_size_bytes, file_checksum, provider, model_id, status
    ) VALUES (
        'aaaaaaaa-dead-0001-1111-111111111111',
        '11111111-1111-1111-1111-111111111111',
        '11111111-1111-1111-1111-cccccccccccc',
        '11111111-1111-1111-1111-aaaaaaaaaaaa',
        'teacher-materials',
        '11111111-1111-1111-1111-111111111111/hack_status.pdf',
        'hack_status.pdf', 'application/pdf', 1024, 'sha-hack', 'google_vertex', 'gemini-1.5', 'approved'
    )
    $$,
    NULL,
    NULL,
    '10.4 Docente no puede crear trabajo con status distinto de queued'
);

-- Docente no puede insertar un borrador con status = 'approved'
SELECT throws_ok(
    $$
    INSERT INTO question_drafts (
        id, tenant_id, generation_job_id, suggested_kc_name, question_text, explanation, options, status
    ) VALUES (
        'dddddddd-dead-0002-1111-111111111111',
        '11111111-1111-1111-1111-111111111111',
        'aaaaaaaa-1111-1111-1111-111111111111',
        'Genética', 'Pregunta hack', 'Expl', '[]'::jsonb, 'approved'
    )
    $$,
    NULL,
    NULL,
    '10.5 Docente no puede insertar un borrador con status approved (Reservado a HITL transaccional)'
);

-- Docente no puede alterar metadatos (file_checksum, provider) de content_generation_jobs
SELECT throws_ok(
    $$ UPDATE content_generation_jobs SET file_checksum = 'tampered-sha' WHERE id = 'aaaaaaaa-1111-1111-1111-111111111111' $$,
    NULL,
    NULL,
    '10.6 Docente no puede alterar metadatos ni archivo de content_generation_jobs (Inmutable)'
);

-- Docente no puede eliminar content_generation_jobs
SELECT throws_ok(
    $$ DELETE FROM content_generation_jobs WHERE id = 'aaaaaaaa-1111-1111-1111-111111111111' $$,
    NULL,
    NULL,
    '10.7 Docente no puede eliminar content_generation_jobs vía DELETE directo'
);

-- Docente no puede eliminar un borrador ya aprobado (Preservación de auditoría)
SELECT tests.authenticate_as(NULL, 'service_role');
SET LOCAL ROLE postgres;
INSERT INTO question_drafts (
    id, tenant_id, generation_job_id, suggested_kc_name, question_text, explanation, options, status
) VALUES (
    'dddddddd-9999-9999-9999-111111111111',
    '11111111-1111-1111-1111-111111111111',
    'aaaaaaaa-1111-1111-1111-111111111111',
    'Auditoría', 'Pregunta auditada', 'Expl', '[]'::jsonb, 'approved'
);
SET LOCAL ROLE authenticated;
SELECT tests.authenticate_as('11111111-1111-1111-1111-aaaaaaaaaaaa'::uuid);

SELECT throws_ok(
    $$ DELETE FROM question_drafts WHERE id = 'dddddddd-9999-9999-9999-111111111111' $$,
    NULL,
    NULL,
    '10.8 Docente no puede eliminar un borrador aprobado (Preservación de auditoría)'
);

-- ============================================================================
-- FINALIZACIÓN Y ROLLBACK DE PRUEBAS
-- ============================================================================
SELECT * FROM finish();
ROLLBACK;
