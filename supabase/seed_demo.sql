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
