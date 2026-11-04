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
