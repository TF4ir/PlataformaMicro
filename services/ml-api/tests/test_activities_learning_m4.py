"""Comprehensive Integration Tests for Milestone M4: Learning Flow, Activities, and Immutable Answer Events.

Covers all 24 mandatory integration requirements:
1. Crear actividad.
2. Asociar preguntas aprobadas.
3. Rechazar preguntas no aprobadas / inactivas.
4. Publicar actividad (validando requisitos de sección y preguntas).
5. Consultar actividad desde docente autorizado.
6. Consultar actividad desde estudiante asignado.
7. Bloquear estudiante de otra sección.
8. Bloquear actividades no publicadas para estudiantes.
9. Iniciar intento (start attempt).
10. Evitar intentos duplicados / idempotencia.
11. Registrar respuesta correcta.
12. Registrar respuesta incorrecta.
13. Verificar cálculo de correctitud estrictamente en backend.
14. Comprobar idempotencia ante reintentos de envío de respuesta.
15. Verificar secuencia temporal y orden de answer_events.
16. Impedir UPDATE de answer_events (a nivel de trigger y permisos).
17. Impedir DELETE de answer_events (a nivel de trigger y permisos).
18. Impedir acceso cruzado entre tenants.
19. Impedir modificación o envío de respuestas a intentos de otros estudiantes.
20. Finalizar intento correctamente (submit attempt y cálculo de puntaje).
21. Impedir doble finalización (idempotencia en submit).
22. Validar resultados agrupados por Knowledge Component.
23. Verificar que las respuestas correctas y explicaciones no se filtren prematuramente.
24. Verificar la persistencia después de reiniciar conexiones y pool de base de datos.
"""

import logging
from datetime import UTC, datetime
from uuid import UUID, uuid4

import asyncpg
import httpx
import pytest

from app.content_generation.infrastructure.database import close_db_pool, get_db_pool
from app.main import app

logger = logging.getLogger(__name__)

TEST_DB_URL = "postgresql://postgres:postgres@127.0.0.1:5432/plataformamicro_test"

# Fixed UUIDs for multi-tenant integration fixtures
TENANT_A = "11111111-1111-1111-1111-111111111111"
TENANT_B = "22222222-2222-2222-2222-222222222222"

TEACHER_A = "11111111-1111-1111-1111-aaaaaaaaaaaa"
STUDENT_A1 = "11111111-1111-1111-1111-bbbbbbbbbbbb"
STUDENT_A2 = "11111111-1111-1111-1111-bbbbbbbbbbbc"  # Enrolled in different section

TEACHER_B = "22222222-2222-2222-2222-aaaaaaaaaaaa"
STUDENT_B = "22222222-2222-2222-2222-bbbbbbbbbbbb"

COURSE_A1 = "11111111-1111-1111-1111-cccccccccccc"
SECTION_A1 = "11111111-1111-1111-1111-dddddddddddd"
SECTION_A2 = "11111111-1111-1111-1111-ddddddddddde"

ENROLLMENT_A1 = "11111111-1111-1111-1111-999999999991"
ENROLLMENT_A2 = "11111111-1111-1111-1111-999999999992"


@pytest.fixture(autouse=True)
async def setup_test_db():
    """Ensure database connection pool is active and test fixtures are seeded."""
    import app.content_generation.infrastructure.database as db_mod

    pool = await asyncpg.create_pool(dsn=TEST_DB_URL, min_size=1, max_size=5)
    db_mod._POOL = pool

    async with pool.acquire() as conn:
        # 1. Base Tenants
        await conn.execute(
            """
            INSERT INTO tenants (id, name, slug) VALUES 
                ($1, 'Colegio Piloto A', 'colegio-a-m4'),
                ($2, 'Colegio Piloto B', 'colegio-b-m4')
            ON CONFLICT (id) DO NOTHING;
            """,
            UUID(TENANT_A),
            UUID(TENANT_B),
        )

        # 2. Auth Users
        await conn.execute(
            """
            INSERT INTO auth.users (id, email) VALUES
                ($1, 'teacher_a@test.edu'),
                ($2, 'student_a1@test.edu'),
                ($3, 'student_a2@test.edu'),
                ($4, 'teacher_b@test.edu'),
                ($5, 'student_b@test.edu')
            ON CONFLICT (id) DO NOTHING;
            """,
            UUID(TEACHER_A),
            UUID(STUDENT_A1),
            UUID(STUDENT_A2),
            UUID(TEACHER_B),
            UUID(STUDENT_B),
        )

        # 3. Profiles
        await conn.execute(
            """
            INSERT INTO profiles (id, tenant_id, full_name, role, student_code) VALUES 
                ($1, $2, 'Prof. Ana García', 'teacher', 'DOC-A1'),
                ($3, $2, 'Lucía Mendoza (Sec A)', 'student', 'EST-A1'),
                ($4, $2, 'Carlos Ruiz (Sec B)', 'student', 'EST-A2'),
                ($5, $6, 'Prof. Beto B', 'teacher', 'DOC-B1'),
                ($7, $6, 'David B', 'student', 'EST-B1')
            ON CONFLICT (id) DO UPDATE SET role = EXCLUDED.role;
            """,
            UUID(TEACHER_A), UUID(TENANT_A),
            UUID(STUDENT_A1),
            UUID(STUDENT_A2),
            UUID(TEACHER_B), UUID(TENANT_B),
            UUID(STUDENT_B),
        )

        # 3. Courses
        await conn.execute(
            """
            INSERT INTO courses (id, tenant_id, code, name, is_active) VALUES 
                ($1, $2, 'CIEN-5SEC', 'Ciencias 5.°', true)
            ON CONFLICT (id) DO NOTHING;
            """,
            UUID(COURSE_A1),
            UUID(TENANT_A),
        )

        # 4. Sections & Enrollments
        await conn.execute(
            """
            INSERT INTO sections (id, tenant_id, course_id, teacher_id, name) VALUES 
                ($1, $2, $3, $4, '5to A - Mañana'),
                ($5, $2, $3, $4, '5to B - Tarde')
            ON CONFLICT (id) DO NOTHING;
            """,
            UUID(SECTION_A1), UUID(TENANT_A), UUID(COURSE_A1), UUID(TEACHER_A),
            UUID(SECTION_A2),
        )

        await conn.execute(
            """
            INSERT INTO enrollments (id, tenant_id, section_id, student_id) VALUES 
                ($1, $2, $3, $4),
                ($5, $2, $6, $7)
            ON CONFLICT (section_id, student_id) DO NOTHING;
            """,
            UUID(ENROLLMENT_A1), UUID(TENANT_A), UUID(SECTION_A1), UUID(STUDENT_A1),
            UUID(ENROLLMENT_A2), UUID(SECTION_A2), UUID(STUDENT_A2),
        )

    yield pool
    await pool.close()


@pytest.fixture
async def seed_canonical_questions(setup_test_db):
    """Seed canonical Knowledge Components and approved questions."""
    pool = setup_test_db
    kc1_id = uuid4()
    kc2_id = uuid4()
    q1_id = uuid4()
    q2_id = uuid4()
    q3_id = uuid4()
    unapproved_q_id = uuid4()

    q1_opt1_id = uuid4()
    q1_opt2_id = uuid4()
    q2_opt1_id = uuid4()
    q2_opt2_id = uuid4()
    q3_opt1_id = uuid4()
    q3_opt2_id = uuid4()

    unit_id = uuid4()

    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO units (id, tenant_id, course_id, title, order_index)
            VALUES ($1, $2, $3, 'Metabolismo Celular', 1)
            ON CONFLICT (id) DO NOTHING;
            """,
            unit_id, UUID(TENANT_A), UUID(COURSE_A1)
        )

        await conn.execute(
            """
            INSERT INTO knowledge_components (id, tenant_id, unit_id, name, difficulty_prior) VALUES
                ($1, $2, $3, 'Fotosíntesis y Cloroplastos', 0.450),
                ($4, $2, $3, 'Respiración Celular y Mitocondrias', 0.520)
            ON CONFLICT (id) DO NOTHING;
            """,
            kc1_id, UUID(TENANT_A), unit_id,
            kc2_id,
        )

        # Question 1 (KC1) - Opt2 is correct
        await conn.execute(
            """
            INSERT INTO questions (id, tenant_id, knowledge_component_id, question_text, explanation, difficulty, created_by, is_active)
            VALUES ($1, $2, $3, '¿En qué orgánulo ocurre la fotosíntesis?', 'Ocurre en los cloroplastos que contienen clorofila.', 0.400, $4, true)
            ON CONFLICT (id) DO NOTHING;
            """,
            q1_id, UUID(TENANT_A), kc1_id, UUID(TEACHER_A)
        )
        await conn.execute(
            """
            INSERT INTO question_options (id, question_id, option_text, is_correct, order_index) VALUES
                ($1, $2, 'Mitocondria', false, 1),
                ($3, $2, 'Cloroplasto', true, 2)
            ON CONFLICT (id) DO NOTHING;
            """,
            q1_opt1_id, q1_id,
            q1_opt2_id,
        )

        # Question 2 (KC1) - Opt1 is correct
        await conn.execute(
            """
            INSERT INTO questions (id, tenant_id, knowledge_component_id, question_text, explanation, difficulty, created_by, is_active)
            VALUES ($1, $2, $3, '¿Cuál es el gas fijado durante el Ciclo de Calvin?', 'El dióxido de carbono (CO2) es fijado por la enzima RuBisCO.', 0.500, $4, true)
            ON CONFLICT (id) DO NOTHING;
            """,
            q2_id, UUID(TENANT_A), kc1_id, UUID(TEACHER_A)
        )
        await conn.execute(
            """
            INSERT INTO question_options (id, question_id, option_text, is_correct, order_index) VALUES
                ($1, $2, 'Dióxido de carbono (CO2)', true, 1),
                ($3, $2, 'Oxígeno molecular (O2)', false, 2)
            ON CONFLICT (id) DO NOTHING;
            """,
            q2_opt1_id, q2_id,
            q2_opt2_id,
        )

        # Question 3 (KC2) - Opt1 is correct
        await conn.execute(
            """
            INSERT INTO questions (id, tenant_id, knowledge_component_id, question_text, explanation, difficulty, created_by, is_active)
            VALUES ($1, $2, $3, '¿Dónde se produce la mayor cantidad de ATP celular?', 'En la membrana interna mitocondrial por fosforilación oxidativa.', 0.550, $4, true)
            ON CONFLICT (id) DO NOTHING;
            """,
            q3_id, UUID(TENANT_A), kc2_id, UUID(TEACHER_A)
        )
        await conn.execute(
            """
            INSERT INTO question_options (id, question_id, option_text, is_correct, order_index) VALUES
                ($1, $2, 'Crestas mitocondriales', true, 1),
                ($3, $2, 'Aparato de Golgi', false, 2)
            ON CONFLICT (id) DO NOTHING;
            """,
            q3_opt1_id, q3_id,
            q3_opt2_id,
        )

        # Unapproved / Inactive Question (is_active = false)
        await conn.execute(
            """
            INSERT INTO questions (id, tenant_id, knowledge_component_id, question_text, explanation, difficulty, created_by, is_active)
            VALUES ($1, $2, $3, 'Pregunta borrador no aprobada', 'Sin explicación', 0.500, $4, false)
            ON CONFLICT (id) DO NOTHING;
            """,
            unapproved_q_id, UUID(TENANT_A), kc1_id, UUID(TEACHER_A)
        )

    yield {
        "kc1_id": kc1_id,
        "kc2_id": kc2_id,
        "q1": {"id": q1_id, "opt_incorrect": q1_opt1_id, "opt_correct": q1_opt2_id},
        "q2": {"id": q2_id, "opt_correct": q2_opt1_id, "opt_incorrect": q2_opt2_id},
        "q3": {"id": q3_id, "opt_correct": q3_opt1_id, "opt_incorrect": q3_opt2_id},
        "unapproved_q_id": unapproved_q_id,
    }

    try:
        conn = await asyncpg.connect(TEST_DB_URL)
        try:
            await conn.execute("ALTER TABLE answer_events DISABLE TRIGGER trg_prevent_answer_events_mutation;")
            await conn.execute("DELETE FROM answer_events WHERE tenant_id IN ($1::uuid, $2::uuid);", UUID(TENANT_A), UUID(TENANT_B))
            await conn.execute("DELETE FROM quiz_attempts WHERE tenant_id IN ($1::uuid, $2::uuid);", UUID(TENANT_A), UUID(TENANT_B))
            await conn.execute("DELETE FROM activity_questions WHERE activity_id IN (SELECT id FROM activities WHERE tenant_id IN ($1::uuid, $2::uuid));", UUID(TENANT_A), UUID(TENANT_B))
            await conn.execute("DELETE FROM activity_sections WHERE tenant_id IN ($1::uuid, $2::uuid);", UUID(TENANT_A), UUID(TENANT_B))
            await conn.execute("DELETE FROM activities WHERE tenant_id IN ($1::uuid, $2::uuid);", UUID(TENANT_A), UUID(TENANT_B))
            await conn.execute("DELETE FROM question_options WHERE question_id IN (SELECT id FROM questions WHERE tenant_id IN ($1::uuid, $2::uuid));", UUID(TENANT_A), UUID(TENANT_B))
            await conn.execute("DELETE FROM questions WHERE tenant_id IN ($1::uuid, $2::uuid);", UUID(TENANT_A), UUID(TENANT_B))
            await conn.execute("ALTER TABLE answer_events ENABLE TRIGGER trg_prevent_answer_events_mutation;")
        finally:
            await conn.close()
    except (asyncpg.PostgresError, OSError) as e:
        logger.warning("Teardown clean error: %s", e)


def make_headers(user_id: str, tenant_id: str, role: str) -> dict[str, str]:
    return {
        "X-User-Id": user_id,
        "X-Tenant-Id": tenant_id,
        "X-User-Role": role,
    }


# ============================================================================
# 1, 2, 3: CREAR ACTIVIDAD, ASOCIAR PREGUNTAS APROBADAS, RECHAZAR NO APROBADAS
# ============================================================================

@pytest.mark.asyncio
async def test_01_02_03_create_activity_and_question_validation(seed_canonical_questions):
    data = seed_canonical_questions
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        teacher_headers = make_headers(TEACHER_A, TENANT_A, "teacher")

        # 3. Rechazar si contiene pregunta no aprobada o inactiva
        res_invalid = await client.post(
            "/api/v1/activities",
            headers=teacher_headers,
            json={
                "title": "Actividad con pregunta no aprobada",
                "course_id": COURSE_A1,
                "section_ids": [SECTION_A1],
                "question_ids": [str(data["unapproved_q_id"])],
                "activity_type": "formative",
                "feedback_policy": "immediate_with_explanation",
            },
        )
        assert res_invalid.status_code == 422
        assert "unapproved" in res_invalid.json()["detail"].lower()

        # 1 & 2. Crear actividad con preguntas aprobadas en estado borrador (draft)
        res_create = await client.post(
            "/api/v1/activities",
            headers=teacher_headers,
            json={
                "title": "Cuestionario Formativo de Metabolismo Celular",
                "description": "Evaluación rápida sobre fotosíntesis y respiración.",
                "course_id": COURSE_A1,
                "section_ids": [SECTION_A1],
                "question_ids": [str(data["q1"]["id"]), str(data["q2"]["id"]), str(data["q3"]["id"])],
                "activity_type": "formative",
                "feedback_policy": "immediate_with_explanation",
                "max_attempts": 2,
            },
        )
        assert res_create.status_code == 201
        created = res_create.json()
        assert created["status"] == "draft"
        assert created["title"] == "Cuestionario Formativo de Metabolismo Celular"
        assert len(created["questions"]) == 3
        assert created["questions"][0]["question_id"] == str(data["q1"]["id"])
        assert created["questions"][0]["order_index"] == 1
        assert created["questions"][0]["knowledge_component_name"] == "Fotosíntesis y Cloroplastos"


# ============================================================================
# 4, 5: PUBLICAR ACTIVIDAD Y CONSULTA DOCENTE
# ============================================================================

@pytest.mark.asyncio
async def test_04_05_publish_activity_and_teacher_query(seed_canonical_questions):
    data = seed_canonical_questions
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        teacher_headers = make_headers(TEACHER_A, TENANT_A, "teacher")

        # Create draft
        res_create = await client.post(
            "/api/v1/activities",
            headers=teacher_headers,
            json={
                "title": "Cuestionario para Publicar",
                "course_id": COURSE_A1,
                "section_ids": [SECTION_A1],
                "question_ids": [str(data["q1"]["id"])],
                "activity_type": "formative",
            },
        )
        act_id = res_create.json()["id"]

        # 4. Publicar
        res_pub = await client.post(
            f"/api/v1/activities/{act_id}/publish",
            headers=teacher_headers,
        )
        assert res_pub.status_code == 200
        assert res_pub.json()["status"] == "published"
        assert res_pub.json()["published_at"] is not None

        # 5. Consultar actividad desde docente autorizado
        res_list = await client.get("/api/v1/activities", headers=teacher_headers)
        assert res_list.status_code == 200
        ids = [a["id"] for a in res_list.json()]
        assert act_id in ids


# ============================================================================
# 6, 7, 8: CONSULTA ESTUDIANTE, BLOQUEO OTRA SECCIÓN, BLOQUEO NO PUBLICADA
# ============================================================================

@pytest.mark.asyncio
async def test_06_07_08_student_access_and_section_isolation(seed_canonical_questions):
    data = seed_canonical_questions
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        teacher_headers = make_headers(TEACHER_A, TENANT_A, "teacher")
        student_a1_headers = make_headers(STUDENT_A1, TENANT_A, "student")
        student_a2_headers = make_headers(STUDENT_A2, TENANT_A, "student")

        # Create activity targeted ONLY to SECTION_A1 (Student A1 is in A1, Student A2 is in A2)
        res_create = await client.post(
            "/api/v1/activities",
            headers=teacher_headers,
            json={
                "title": "Actividad Exclusiva Sección A1",
                "course_id": COURSE_A1,
                "section_ids": [SECTION_A1],
                "question_ids": [str(data["q1"]["id"])],
            },
        )
        act_id = res_create.json()["id"]

        # 8. Bloquear actividad no publicada para estudiantes
        res_unpub = await client.get(
            f"/api/v1/students/me/activities/{act_id}",
            headers=student_a1_headers,
        )
        assert res_unpub.status_code in (403, 404)

        # Publish activity
        await client.post(f"/api/v1/activities/{act_id}/publish", headers=teacher_headers)

        # 6. Consultar actividad desde estudiante asignado (A1)
        res_assigned = await client.get(
            f"/api/v1/students/me/activities/{act_id}",
            headers=student_a1_headers,
        )
        assert res_assigned.status_code == 200
        assert res_assigned.json()["title"] == "Actividad Exclusiva Sección A1"

        # 7. Bloquear estudiante de otra sección (A2)
        res_other_section = await client.get(
            f"/api/v1/students/me/activities/{act_id}",
            headers=student_a2_headers,
        )
        assert res_other_section.status_code in (403, 404)


# ============================================================================
# 9, 10: INICIAR INTENTO Y EVITAR DUPLICADOS
# ============================================================================

@pytest.mark.asyncio
async def test_09_10_start_attempt_and_idempotency(seed_canonical_questions):
    data = seed_canonical_questions
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        teacher_headers = make_headers(TEACHER_A, TENANT_A, "teacher")
        student_headers = make_headers(STUDENT_A1, TENANT_A, "student")

        # Create and publish activity
        res_create = await client.post(
            "/api/v1/activities",
            headers=teacher_headers,
            json={
                "title": "Actividad para Intentos",
                "course_id": COURSE_A1,
                "section_ids": [SECTION_A1],
                "question_ids": [str(data["q1"]["id"]), str(data["q2"]["id"])],
                "max_attempts": 2,
            },
        )
        act_id = res_create.json()["id"]
        await client.post(f"/api/v1/activities/{act_id}/publish", headers=teacher_headers)

        # 9. Iniciar intento
        idempotency_key = str(uuid4())
        res_attempt1 = await client.post(
            f"/api/v1/students/me/activities/{act_id}/attempts",
            headers={**student_headers, "X-Idempotency-Key": idempotency_key},
            json={},
        )
        assert res_attempt1.status_code == 201
        attempt1 = res_attempt1.json()
        assert attempt1["status"] == "in_progress"
        assert attempt1["attempt_number"] == 1

        # 10. Evitar duplicados: reintento con misma clave devuelve el mismo intento
        res_attempt_retry = await client.post(
            f"/api/v1/students/me/activities/{act_id}/attempts",
            headers={**student_headers, "X-Idempotency-Key": idempotency_key},
            json={},
        )
        assert res_attempt_retry.status_code in (200, 201)
        assert res_attempt_retry.json()["attempt_id"] == attempt1["attempt_id"]


# ============================================================================
# 11, 12, 13, 14, 15: REGISTRO DE RESPUESTAS, CORRECTITUD BACKEND, IDEMPOTENCIA, SECUENCIA
# ============================================================================

@pytest.mark.asyncio
async def test_11_to_15_answer_recording_correctness_idempotency(seed_canonical_questions):
    data = seed_canonical_questions
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        teacher_headers = make_headers(TEACHER_A, TENANT_A, "teacher")
        student_headers = make_headers(STUDENT_A1, TENANT_A, "student")

        res_create = await client.post(
            "/api/v1/activities",
            headers=teacher_headers,
            json={
                "title": "Evaluación Formativa Fotosíntesis",
                "course_id": COURSE_A1,
                "section_ids": [SECTION_A1],
                "question_ids": [str(data["q1"]["id"]), str(data["q2"]["id"])],
                "feedback_policy": "immediate_with_explanation",
            },
        )
        act_id = res_create.json()["id"]
        await client.post(f"/api/v1/activities/{act_id}/publish", headers=teacher_headers)

        res_attempt = await client.post(
            f"/api/v1/students/me/activities/{act_id}/attempts",
            headers=student_headers,
            json={},
        )
        attempt_id = res_attempt.json()["attempt_id"]

        # 11. Registrar respuesta correcta a pregunta 1 (opt_correct)
        ans1_key = str(uuid4())
        res_ans1 = await client.post(
            f"/api/v1/students/me/attempts/{attempt_id}/answers",
            headers={**student_headers, "X-Idempotency-Key": ans1_key},
            json={
                "question_id": str(data["q1"]["id"]),
                "selected_option_id": str(data["q1"]["opt_correct"]),
                "response_time_seconds": 4.5,
            },
        )
        assert res_ans1.status_code == 201
        ans1_data = res_ans1.json()

        # 13. Verificar cálculo de correctitud en backend
        assert ans1_data["is_correct"] is True
        assert "cloroplasto" in ans1_data["feedback"]["explanation"].lower()

        # 14. Idempotencia ante reintentos de red
        res_ans1_retry = await client.post(
            f"/api/v1/students/me/attempts/{attempt_id}/answers",
            headers={**student_headers, "X-Idempotency-Key": ans1_key},
            json={
                "question_id": str(data["q1"]["id"]),
                "selected_option_id": str(data["q1"]["opt_correct"]),
                "response_time_seconds": 4.5,
            },
        )
        assert res_ans1_retry.status_code in (200, 201)
        assert res_ans1_retry.json()["event_id"] == ans1_data["event_id"]

        # 12. Registrar respuesta incorrecta a pregunta 2 (opt_incorrect)
        ans2_key = str(uuid4())
        res_ans2 = await client.post(
            f"/api/v1/students/me/attempts/{attempt_id}/answers",
            headers={**student_headers, "X-Idempotency-Key": ans2_key},
            json={
                "question_id": str(data["q2"]["id"]),
                "selected_option_id": str(data["q2"]["opt_incorrect"]),
                "response_time_seconds": 6.2,
            },
        )
        assert res_ans2.status_code == 201
        ans2_data = res_ans2.json()
        assert ans2_data["is_correct"] is False

        # 15. Verificar secuencia temporal de answer_events
        pool = await get_db_pool(dsn=TEST_DB_URL)
        async with pool.acquire() as conn:
            events = await conn.fetch(
                """
                SELECT question_id, is_correct, event_timestamp, question_sequence
                FROM answer_events
                WHERE attempt_id = $1
                ORDER BY event_timestamp ASC;
                """,
                UUID(attempt_id),
            )
            assert len(events) == 2
            assert events[0]["question_id"] == data["q1"]["id"]
            assert events[0]["is_correct"] is True
            assert events[1]["question_id"] == data["q2"]["id"]
            assert events[1]["is_correct"] is False
            assert events[0]["event_timestamp"] <= events[1]["event_timestamp"]


# ============================================================================
# 16, 17: IMPEDIR UPDATE Y DELETE DE answer_events
# ============================================================================

@pytest.mark.asyncio
async def test_16_17_answer_events_strict_immutability(seed_canonical_questions):
    data = seed_canonical_questions
    pool = await get_db_pool(dsn=TEST_DB_URL)

    # Insert test answer event
    event_id = uuid4()
    attempt_id = uuid4()
    activity_id = uuid4()

    async with pool.acquire() as conn:
        # Create minimal activity & attempt
        await conn.execute(
            """
            INSERT INTO activities (id, tenant_id, course_id, title, activity_type, created_by)
            VALUES ($1, $2, $3, 'Test Inmutabilidad', 'formative', $4);
            """,
            activity_id, UUID(TENANT_A), UUID(COURSE_A1), UUID(TEACHER_A)
        )
        enr_id = await conn.fetchval(
            "SELECT id FROM enrollments WHERE student_id = $1 AND section_id = $2;",
            UUID(STUDENT_A1),
            UUID(SECTION_A1),
        )
        await conn.execute(
            """
            INSERT INTO quiz_attempts (id, tenant_id, enrollment_id, activity_id, student_id)
            VALUES ($1, $2, $3, $4, $5);
            """,
            attempt_id, UUID(TENANT_A), enr_id, activity_id, UUID(STUDENT_A1)
        )
        await conn.execute(
            """
            INSERT INTO answer_events (
                id, tenant_id, attempt_id, student_id, question_id,
                knowledge_component_id, selected_option_id, is_correct,
                attempt_number, response_time_seconds, idempotency_key,
                activity_id, course_id
            ) VALUES (
                $1, $2, $3, $4, $5,
                $6, $7, true,
                1, 5.0, $8,
                $9, $10
            );
            """,
            event_id, UUID(TENANT_A), attempt_id, UUID(STUDENT_A1),
            data["q1"]["id"], data["kc1_id"], data["q1"]["opt_correct"],
            uuid4(), activity_id, UUID(COURSE_A1)
        )

        # 16. Impedir UPDATE: Trigger lanza excepción 55000
        with pytest.raises(asyncpg.PostgresError) as exc_upd:
            await conn.execute("UPDATE answer_events SET is_correct = false WHERE id = $1;", event_id)
        assert "55000" in str(exc_upd.value) or "immutable" in str(exc_upd.value).lower() or "strictly append-only" in str(exc_upd.value).lower()

        # 17. Impedir DELETE: Trigger lanza excepción 55000
        with pytest.raises(asyncpg.PostgresError) as exc_del:
            await conn.execute("DELETE FROM answer_events WHERE id = $1;", event_id)
        assert "55000" in str(exc_del.value) or "immutable" in str(exc_del.value).lower() or "strictly append-only" in str(exc_del.value).lower()

        # Teardown test row
        await conn.execute("ALTER TABLE answer_events DISABLE TRIGGER trg_prevent_answer_events_mutation;")
        await conn.execute("DELETE FROM answer_events WHERE id = $1;", event_id)
        await conn.execute("DELETE FROM quiz_attempts WHERE id = $1;", attempt_id)
        await conn.execute("DELETE FROM activities WHERE id = $1;", activity_id)
        await conn.execute("ALTER TABLE answer_events ENABLE TRIGGER trg_prevent_answer_events_mutation;")


# ============================================================================
# 18, 19: IMPEDIR ACCESO MULTITENANT CRUZADO Y MANIPULACIÓN DE OTROS ESTUDIANTES
# ============================================================================

@pytest.mark.asyncio
async def test_18_19_cross_tenant_and_cross_student_isolation(seed_canonical_questions):
    data = seed_canonical_questions
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        teacher_headers = make_headers(TEACHER_A, TENANT_A, "teacher")
        student_a_headers = make_headers(STUDENT_A1, TENANT_A, "student")
        student_b_headers = make_headers(STUDENT_B, TENANT_B, "student")

        # Create activity in Tenant A
        res_create = await client.post(
            "/api/v1/activities",
            headers=teacher_headers,
            json={
                "title": "Actividad Tenant A",
                "course_id": COURSE_A1,
                "section_ids": [SECTION_A1],
                "question_ids": [str(data["q1"]["id"])],
            },
        )
        act_id = res_create.json()["id"]
        await client.post(f"/api/v1/activities/{act_id}/publish", headers=teacher_headers)

        # Student A starts attempt
        res_attempt = await client.post(
            f"/api/v1/students/me/activities/{act_id}/attempts",
            headers=student_a_headers,
            json={},
        )
        attempt_id = res_attempt.json()["attempt_id"]

        # 18. Impedir que Student B (Tenant B) consulte o intente actividad de Tenant A
        res_tenant_b = await client.get(
            f"/api/v1/students/me/activities/{act_id}",
            headers=student_b_headers,
        )
        assert res_tenant_b.status_code in (403, 404)

        # 19. Impedir que Student B modifique o envíe respuestas al intento de Student A
        res_tamper = await client.post(
            f"/api/v1/students/me/attempts/{attempt_id}/answers",
            headers=student_b_headers,
            json={
                "question_id": str(data["q1"]["id"]),
                "selected_option_id": str(data["q1"]["opt_correct"]),
                "response_time_seconds": 3.0,
            },
        )
        assert res_tamper.status_code in (403, 404)


# ============================================================================
# 20, 21, 22: FINALIZAR INTENTO, IMPEDIR DOBLE FINALIZACIÓN, RESULTADOS POR KC
# ============================================================================

@pytest.mark.asyncio
async def test_20_21_22_submit_attempt_idempotency_and_kc_breakdown(seed_canonical_questions):
    data = seed_canonical_questions
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        teacher_headers = make_headers(TEACHER_A, TENANT_A, "teacher")
        student_headers = make_headers(STUDENT_A1, TENANT_A, "student")

        res_create = await client.post(
            "/api/v1/activities",
            headers=teacher_headers,
            json={
                "title": "Evaluación con 2 Preguntas de Fotosíntesis y 1 de Respiración",
                "course_id": COURSE_A1,
                "section_ids": [SECTION_A1],
                "question_ids": [str(data["q1"]["id"]), str(data["q2"]["id"]), str(data["q3"]["id"])],
            },
        )
        act_id = res_create.json()["id"]
        await client.post(f"/api/v1/activities/{act_id}/publish", headers=teacher_headers)

        res_attempt = await client.post(
            f"/api/v1/students/me/activities/{act_id}/attempts",
            headers=student_headers,
            json={},
        )
        attempt_id = res_attempt.json()["attempt_id"]

        # Student answers Q1 correctly (KC1)
        await client.post(
            f"/api/v1/students/me/attempts/{attempt_id}/answers",
            headers=student_headers,
            json={
                "question_id": str(data["q1"]["id"]),
                "selected_option_id": str(data["q1"]["opt_correct"]),
                "response_time_seconds": 5.0,
            },
        )

        # Student answers Q2 incorrectly (KC1)
        await client.post(
            f"/api/v1/students/me/attempts/{attempt_id}/answers",
            headers=student_headers,
            json={
                "question_id": str(data["q2"]["id"]),
                "selected_option_id": str(data["q2"]["opt_incorrect"]),
                "response_time_seconds": 4.0,
            },
        )

        # Student answers Q3 correctly (KC2)
        await client.post(
            f"/api/v1/students/me/attempts/{attempt_id}/answers",
            headers=student_headers,
            json={
                "question_id": str(data["q3"]["id"]),
                "selected_option_id": str(data["q3"]["opt_correct"]),
                "response_time_seconds": 7.0,
            },
        )

        # 20. Finalizar intento correctamente (2 de 3 correctas = 66.67%)
        res_submit = await client.post(
            f"/api/v1/students/me/attempts/{attempt_id}/submit",
            headers=student_headers,
        )
        assert res_submit.status_code == 200
        submit_data = res_submit.json()
        assert submit_data["status"] == "completed"
        assert submit_data["total_questions"] == 3
        assert submit_data["correct_answers"] == 2
        assert submit_data["score"] == pytest.approx(66.67, abs=0.1)

        # 21. Impedir doble finalización (idempotente)
        res_submit2 = await client.post(
            f"/api/v1/students/me/attempts/{attempt_id}/submit",
            headers=student_headers,
        )
        assert res_submit2.status_code == 200
        assert res_submit2.json()["score"] == submit_data["score"]

        # 22. Validar resultados por Knowledge Component
        res_results = await client.get(
            f"/api/v1/students/me/attempts/{attempt_id}/results",
            headers=student_headers,
        )
        assert res_results.status_code == 200
        results = res_results.json()
        assert len(results["kc_summaries"]) == 2

        kc_map = {k["knowledge_component_name"]: k for k in results["kc_summaries"]}
        assert "Fotosíntesis y Cloroplastos" in kc_map
        assert kc_map["Fotosíntesis y Cloroplastos"]["total_questions"] == 2
        assert kc_map["Fotosíntesis y Cloroplastos"]["correct_answers"] == 1
        assert kc_map["Fotosíntesis y Cloroplastos"]["mastery_rate"] == 50.0

        assert "Respiración Celular y Mitocondrias" in kc_map
        assert kc_map["Respiración Celular y Mitocondrias"]["total_questions"] == 1
        assert kc_map["Respiración Celular y Mitocondrias"]["correct_answers"] == 1
        assert kc_map["Respiración Celular y Mitocondrias"]["mastery_rate"] == 100.0


# ============================================================================
# 23: VERIFICAR QUE RESPUESTAS CORRECTAS NO SE FILTREN PREMATURAMENTE
# ============================================================================

@pytest.mark.asyncio
async def test_23_prevent_premature_answer_leakage(seed_canonical_questions):
    data = seed_canonical_questions
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        teacher_headers = make_headers(TEACHER_A, TENANT_A, "teacher")
        student_headers = make_headers(STUDENT_A1, TENANT_A, "student")

        # Create activity with policy = upon_completion
        res_create = await client.post(
            "/api/v1/activities",
            headers=teacher_headers,
            json={
                "title": "Evaluación Sumativa con Feedback al Final",
                "course_id": COURSE_A1,
                "section_ids": [SECTION_A1],
                "question_ids": [str(data["q1"]["id"])],
                "feedback_policy": "upon_completion",
            },
        )
        act_id = res_create.json()["id"]
        await client.post(f"/api/v1/activities/{act_id}/publish", headers=teacher_headers)

        # Student inspects questionnaire before answering
        res_detail = await client.get(
            f"/api/v1/students/me/activities/{act_id}",
            headers=student_headers,
        )
        assert res_detail.status_code == 200
        q_data = res_detail.json()["questions"][0]

        # Verify neither options have is_correct, nor question has explanation
        assert "explanation" not in q_data
        for opt in q_data["options"]:
            assert "is_correct" not in opt

        # Start attempt
        res_attempt = await client.post(
            f"/api/v1/students/me/activities/{act_id}/attempts",
            headers=student_headers,
            json={},
        )
        attempt_id = res_attempt.json()["attempt_id"]

        # Submit answer with upon_completion policy
        res_ans = await client.post(
            f"/api/v1/students/me/attempts/{attempt_id}/answers",
            headers=student_headers,
            json={
                "question_id": str(data["q1"]["id"]),
                "selected_option_id": str(data["q1"]["opt_correct"]),
                "response_time_seconds": 3.0,
            },
        )
        assert res_ans.status_code == 201
        ans_payload = res_ans.json()

        # Under upon_completion, neither is_correct nor feedback is revealed!
        assert ans_payload["is_correct"] is None
        assert ans_payload["feedback"] is None


# ============================================================================
# 24: VERIFICAR PERSISTENCIA TRAS REINICIO DE CONEXIONES Y POOL
# ============================================================================

@pytest.mark.asyncio
async def test_24_persistence_after_connection_restart(seed_canonical_questions):
    data = seed_canonical_questions
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        teacher_headers = make_headers(TEACHER_A, TENANT_A, "teacher")
        student_headers = make_headers(STUDENT_A1, TENANT_A, "student")

        res_create = await client.post(
            "/api/v1/activities",
            headers=teacher_headers,
            json={
                "title": "Actividad Persistencia Post-Reinicio",
                "course_id": COURSE_A1,
                "section_ids": [SECTION_A1],
                "question_ids": [str(data["q1"]["id"])],
            },
        )
        act_id = res_create.json()["id"]
        await client.post(f"/api/v1/activities/{act_id}/publish", headers=teacher_headers)

        res_att = await client.post(
            f"/api/v1/students/me/activities/{act_id}/attempts",
            headers=student_headers,
            json={},
        )
        attempt_id = res_att.json()["attempt_id"]

        await client.post(
            f"/api/v1/students/me/attempts/{attempt_id}/answers",
            headers=student_headers,
            json={
                "question_id": str(data["q1"]["id"]),
                "selected_option_id": str(data["q1"]["opt_correct"]),
                "response_time_seconds": 4.0,
            },
        )

        await client.post(
            f"/api/v1/students/me/attempts/{attempt_id}/submit",
            headers=student_headers,
        )

    # 24. Simulate full service restart: close pool and reopen a completely new connection
    await close_db_pool()

    new_pool = await get_db_pool(dsn=TEST_DB_URL)
    async with new_pool.acquire() as conn:
        attempt_persisted = await conn.fetchrow(
            "SELECT status, score, completed_at FROM quiz_attempts WHERE id = $1;",
            UUID(attempt_id),
        )
        assert attempt_persisted is not None
        assert attempt_persisted["status"] == "completed"
        assert float(attempt_persisted["score"]) == 100.0

        events_persisted = await conn.fetch(
            "SELECT id, is_correct, response_time_seconds FROM answer_events WHERE attempt_id = $1;",
            UUID(attempt_id),
        )
        assert len(events_persisted) == 1
        assert events_persisted[0]["is_correct"] is True
        assert float(events_persisted[0]["response_time_seconds"]) == 4.0


# ============================================================================
# 25: BLOQUEAR ACCESO ESTUDIANTE A /activities/{id} Y A RESULTADOS IN_PROGRESS
# ============================================================================

@pytest.mark.asyncio
async def test_25_security_endpoints_role_checks_and_premature_results(seed_canonical_questions):
    data = seed_canonical_questions
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        teacher_headers = make_headers(TEACHER_A, TENANT_A, "teacher")
        student_headers = make_headers(STUDENT_A1, TENANT_A, "student")

        res_create = await client.post(
            "/api/v1/activities",
            headers=teacher_headers,
            json={
                "title": "Actividad Seguridad 25",
                "course_id": COURSE_A1,
                "section_ids": [SECTION_A1],
                "question_ids": [str(data["q1"]["id"])],
            },
        )
        act_id = res_create.json()["id"]
        await client.post(f"/api/v1/activities/{act_id}/publish", headers=teacher_headers)

        # 1. Student must NOT access teacher endpoint GET /activities/{activity_id} (which contains is_correct)
        res_teacher_endpoint = await client.get(
            f"/api/v1/activities/{act_id}",
            headers=student_headers,
        )
        assert res_teacher_endpoint.status_code == 403

        # 2. Student starts attempt
        res_att = await client.post(
            f"/api/v1/students/me/activities/{act_id}/attempts",
            headers=student_headers,
            json={},
        )
        attempt_id = res_att.json()["attempt_id"]

        # 3. Student must NOT access results while attempt is still in_progress
        res_premature_results = await client.get(
            f"/api/v1/students/me/attempts/{attempt_id}/results",
            headers=student_headers,
        )
        assert res_premature_results.status_code == 403
        assert "in-progress" in res_premature_results.json()["detail"].lower() or "finalizado" in res_premature_results.json()["detail"].lower()


# ============================================================================
# 26: ENMASCARAMIENTO DE SOLUCIONES PARA AFTER_DEADLINE ANTES DEL VENCIMIENTO
# ============================================================================

@pytest.mark.asyncio
async def test_26_after_deadline_solution_masking(seed_canonical_questions):
    from datetime import timedelta
    data = seed_canonical_questions
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        teacher_headers = make_headers(TEACHER_A, TENANT_A, "teacher")
        student_headers = make_headers(STUDENT_A1, TENANT_A, "student")

        future_deadline = (datetime.now(UTC) + timedelta(days=2)).isoformat()

        res_create = await client.post(
            "/api/v1/activities",
            headers=teacher_headers,
            json={
                "title": "Actividad con Plazo Futuro",
                "course_id": COURSE_A1,
                "section_ids": [SECTION_A1],
                "question_ids": [str(data["q1"]["id"])],
                "feedback_policy": "after_deadline",
                "available_until": future_deadline,
            },
        )
        act_id = res_create.json()["id"]
        await client.post(f"/api/v1/activities/{act_id}/publish", headers=teacher_headers)

        res_att = await client.post(
            f"/api/v1/students/me/activities/{act_id}/attempts",
            headers=student_headers,
            json={},
        )
        attempt_id = res_att.json()["attempt_id"]

        await client.post(
            f"/api/v1/students/me/attempts/{attempt_id}/answers",
            headers=student_headers,
            json={
                "question_id": str(data["q1"]["id"]),
                "selected_option_id": str(data["q1"]["opt_incorrect"]),
                "response_time_seconds": 2.5,
            },
        )

        res_sub = await client.post(
            f"/api/v1/students/me/attempts/{attempt_id}/submit",
            headers=student_headers,
        )
        assert res_sub.status_code == 200

        # Now get results: since deadline is in future, correct answers & explanation must be masked
        res_res = await client.get(
            f"/api/v1/students/me/attempts/{attempt_id}/results",
            headers=student_headers,
        )
        assert res_res.status_code == 200
        res_data = res_res.json()
        q_rev = res_data["questions"][0]

        assert q_rev["correct_option_id"] is None
        assert q_rev["correct_option_text"] is None
        assert q_rev["explanation"] is not None
        assert "una vez concluido el plazo" in q_rev["explanation"]


# ============================================================================
# 27: PREGUNTAS OMITIDAS MANTIENEN SELECTED_OPTION_ID NULO EN RESULTADOS
# ============================================================================

@pytest.mark.asyncio
async def test_27_unanswered_question_selected_option_is_none(seed_canonical_questions):
    data = seed_canonical_questions
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        teacher_headers = make_headers(TEACHER_A, TENANT_A, "teacher")
        student_headers = make_headers(STUDENT_A1, TENANT_A, "student")

        res_create = await client.post(
            "/api/v1/activities",
            headers=teacher_headers,
            json={
                "title": "Actividad con Pregunta Omitida",
                "course_id": COURSE_A1,
                "section_ids": [SECTION_A1],
                "question_ids": [str(data["q1"]["id"]), str(data["q2"]["id"])],
                "feedback_policy": "upon_completion",
            },
        )
        act_id = res_create.json()["id"]
        await client.post(f"/api/v1/activities/{act_id}/publish", headers=teacher_headers)

        res_att = await client.post(
            f"/api/v1/students/me/activities/{act_id}/attempts",
            headers=student_headers,
            json={},
        )
        attempt_id = res_att.json()["attempt_id"]

        # Only answer question 1, omit question 2
        await client.post(
            f"/api/v1/students/me/attempts/{attempt_id}/answers",
            headers=student_headers,
            json={
                "question_id": str(data["q1"]["id"]),
                "selected_option_id": str(data["q1"]["opt_correct"]),
                "response_time_seconds": 2.0,
            },
        )

        res_sub = await client.post(
            f"/api/v1/students/me/attempts/{attempt_id}/submit",
            headers=student_headers,
        )
        assert res_sub.status_code == 200

        res_res = await client.get(
            f"/api/v1/students/me/attempts/{attempt_id}/results",
            headers=student_headers,
        )
        assert res_res.status_code == 200
        res_data = res_res.json()

        q1_rev = next(q for q in res_data["questions"] if q["question_id"] == str(data["q1"]["id"]))
        q2_rev = next(q for q in res_data["questions"] if q["question_id"] == str(data["q2"]["id"]))

        assert q1_rev["selected_option_id"] == str(data["q1"]["opt_correct"])
        assert q1_rev["is_correct"] is True

        assert q2_rev["selected_option_id"] is None
        assert q2_rev["selected_option_text"] == "No respondida"
        assert q2_rev["is_correct"] is False


# ============================================================================
# 28: SECUENCIA DINÁMICA MONÓTONAMENTE CRECIENTE EN answer_events
# ============================================================================

@pytest.mark.asyncio
async def test_28_dynamic_chronological_sequence_calculation(seed_canonical_questions):
    data = seed_canonical_questions
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        teacher_headers = make_headers(TEACHER_A, TENANT_A, "teacher")
        student_headers = make_headers(STUDENT_A1, TENANT_A, "student")

        res_create = await client.post(
            "/api/v1/activities",
            headers=teacher_headers,
            json={
                "title": "Actividad Secuencia Cronológica",
                "course_id": COURSE_A1,
                "section_ids": [SECTION_A1],
                "question_ids": [str(data["q1"]["id"]), str(data["q2"]["id"])],
            },
        )
        act_id = res_create.json()["id"]
        await client.post(f"/api/v1/activities/{act_id}/publish", headers=teacher_headers)

        res_att = await client.post(
            f"/api/v1/students/me/activities/{act_id}/attempts",
            headers=student_headers,
            json={},
        )
        attempt_id = res_att.json()["attempt_id"]

        # First answer question 2, then answer question 1
        await client.post(
            f"/api/v1/students/me/attempts/{attempt_id}/answers",
            headers=student_headers,
            json={
                "question_id": str(data["q2"]["id"]),
                "selected_option_id": str(data["q2"]["opt_correct"]),
                "response_time_seconds": 1.0,
            },
        )

        await client.post(
            f"/api/v1/students/me/attempts/{attempt_id}/answers",
            headers=student_headers,
            json={
                "question_id": str(data["q1"]["id"]),
                "selected_option_id": str(data["q1"]["opt_correct"]),
                "response_time_seconds": 2.0,
            },
        )

        # Inspect database question_sequence values
        pool = await get_db_pool(dsn=TEST_DB_URL)
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT question_sequence, question_id FROM answer_events WHERE attempt_id = $1 ORDER BY question_sequence ASC;",
                UUID(attempt_id),
            )
            assert len(rows) == 2
            assert rows[0]["question_sequence"] == 1
            assert rows[0]["question_id"] == data["q2"]["id"]
            assert rows[1]["question_sequence"] == 2
            assert rows[1]["question_id"] == data["q1"]["id"]


# ============================================================================
# 29: AUTORIZACIÓN DOCENTE POR CURSO
# ============================================================================

@pytest.mark.asyncio
async def test_29_teacher_course_authorization(seed_canonical_questions):
    data = seed_canonical_questions
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # TEACHER_B from TENANT_B tries to create activity in COURSE_A1
        teacher_b_headers = make_headers(TEACHER_B, TENANT_B, "teacher")

        res_unauthorized = await client.post(
            "/api/v1/activities",
            headers=teacher_b_headers,
            json={
                "title": "Actividad Ilegítima Docente B",
                "course_id": COURSE_A1,
                "section_ids": [SECTION_A1],
                "question_ids": [str(data["q1"]["id"])],
            },
        )
        assert res_unauthorized.status_code == 403


# ============================================================================
# 30: ENDPOINTS DE SECCIONES DE CURSO Y CURSOS DE ESTUDIANTE
# ============================================================================

@pytest.mark.asyncio
async def test_30_course_sections_and_student_courses():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        teacher_headers = make_headers(TEACHER_A, TENANT_A, "teacher")
        student_headers = make_headers(STUDENT_A1, TENANT_A, "student")

        # 1. Course sections
        res_sec = await client.get(
            f"/api/v1/courses/{COURSE_A1}/sections",
            headers=teacher_headers,
        )
        assert res_sec.status_code == 200
        sections = res_sec.json()
        assert len(sections) >= 2
        sec_ids = [s["id"] for s in sections]
        assert SECTION_A1 in sec_ids
        assert SECTION_A2 in sec_ids

        # 2. Student courses
        res_crs = await client.get(
            "/api/v1/students/me/courses",
            headers=student_headers,
        )
        assert res_crs.status_code == 200
        courses = res_crs.json()
        assert len(courses) >= 1
        assert courses[0]["course_id"] == COURSE_A1
        assert courses[0]["section_id"] == SECTION_A1


# ============================================================================
# 31: BLOQUEO ESTRICTO DE TRUNCATE EN answer_events (SQLSTATE 55000)
# ============================================================================

@pytest.mark.asyncio
async def test_31_truncate_answer_events_blocked():
    pool = await get_db_pool(dsn=TEST_DB_URL)
    async with pool.acquire() as conn:
        with pytest.raises(asyncpg.PostgresError) as exc_info:
            await conn.execute("TRUNCATE TABLE answer_events;")
        err_msg = str(exc_info.value).lower()
        assert "55000" in str(exc_info.value) or "truncate" in err_msg or "immutable" in err_msg


# ============================================================================
# 32: ANALÍTICA DOCENTE DE RESULTADOS DE ACTIVIDAD (GET /activities/{id}/results)
# ============================================================================

@pytest.mark.asyncio
async def test_32_teacher_activity_results_analytics(seed_canonical_questions):
    data = seed_canonical_questions
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        teacher_headers = make_headers(TEACHER_A, TENANT_A, "teacher")
        student_headers = make_headers(STUDENT_A1, TENANT_A, "student")
        teacher_b_headers = make_headers(TEACHER_B, TENANT_B, "teacher")

        # 1. Create and publish activity with 2 questions from 2 distinct KCs (q1 from KC1, q3 from KC2)
        res_create = await client.post(
            "/api/v1/activities",
            headers=teacher_headers,
            json={
                "title": "Actividad Analítica 32",
                "course_id": COURSE_A1,
                "section_ids": [SECTION_A1],
                "question_ids": [str(data["q1"]["id"]), str(data["q3"]["id"])],
            },
        )
        assert res_create.status_code == 201
        act_id = res_create.json()["id"]
        await client.post(f"/api/v1/activities/{act_id}/publish", headers=teacher_headers)

        # 2. Student starts attempt, answers Q1 correctly, Q3 incorrectly, and submits
        res_att = await client.post(
            f"/api/v1/students/me/activities/{act_id}/attempts",
            headers=student_headers,
            json={},
        )
        assert res_att.status_code == 201
        attempt_id = res_att.json()["attempt_id"]

        await client.post(
            f"/api/v1/students/me/attempts/{attempt_id}/answers",
            headers=student_headers,
            json={
                "question_id": str(data["q1"]["id"]),
                "selected_option_id": str(data["q1"]["opt_correct"]),
                "response_time_seconds": 3.0,
            },
        )
        await client.post(
            f"/api/v1/students/me/attempts/{attempt_id}/answers",
            headers=student_headers,
            json={
                "question_id": str(data["q3"]["id"]),
                "selected_option_id": str(data["q3"]["opt_incorrect"]),
                "response_time_seconds": 4.0,
            },
        )
        res_submit = await client.post(
            f"/api/v1/students/me/attempts/{attempt_id}/submit",
            headers=student_headers,
        )
        assert res_submit.status_code == 200
        assert res_submit.json()["score"] == 50.0

        # 3. Teacher queries results
        res_results = await client.get(
            f"/api/v1/activities/{act_id}/results",
            headers=teacher_headers,
        )
        assert res_results.status_code == 200
        rdata = res_results.json()
        assert rdata["activity_id"] == act_id
        assert rdata["total_enrolled"] >= 1
        assert rdata["total_attempts"] >= 1
        assert rdata["completed_attempts"] >= 1
        assert rdata["average_score"] == 50.0

        # Check sections breakdown
        sec_names = [s["section_name"] for s in rdata["sections_breakdown"]]
        assert any("5to A" in s for s in sec_names)

        # Check questions breakdown
        assert len(rdata["questions_breakdown"]) == 2
        q_map = {q["question_id"]: q for q in rdata["questions_breakdown"]}
        assert q_map[str(data["q1"]["id"])]["accuracy_rate"] == 100.0
        assert q_map[str(data["q3"]["id"])]["accuracy_rate"] == 0.0

        # Check KC breakdown
        assert len(rdata["kc_breakdown"]) == 2

        # Check student attempts
        assert len(rdata["student_attempts"]) >= 1
        st_att = rdata["student_attempts"][0]
        assert st_att["attempt_id"] == attempt_id
        assert st_att["score"] == 50.0
        assert st_att["status"] == "completed"

        # 4. Student must be forbidden from accessing teacher results
        res_stud_forbidden = await client.get(
            f"/api/v1/activities/{act_id}/results",
            headers=student_headers,
        )
        assert res_stud_forbidden.status_code == 403

        # 5. Teacher from Tenant B must get 404 (isolated tenant)
        res_tenant_b = await client.get(
            f"/api/v1/activities/{act_id}/results",
            headers=teacher_b_headers,
        )
        assert res_tenant_b.status_code in (403, 404)


# ============================================================================
# 33: MODIFICACIÓN DE RESPUESTA DENTRO DEL INTENTO Y CONTROL DE CONCURRENCIA
# ============================================================================

@pytest.mark.asyncio
async def test_33_student_answer_modification_and_in_progress_guard(seed_canonical_questions):
    data = seed_canonical_questions
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        teacher_headers = make_headers(TEACHER_A, TENANT_A, "teacher")
        student_headers = make_headers(STUDENT_A1, TENANT_A, "student")

        res_create = await client.post(
            "/api/v1/activities",
            headers=teacher_headers,
            json={
                "title": "Actividad Modificación Respuestas 33",
                "course_id": COURSE_A1,
                "section_ids": [SECTION_A1],
                "question_ids": [str(data["q1"]["id"])],
            },
        )
        act_id = res_create.json()["id"]
        await client.post(f"/api/v1/activities/{act_id}/publish", headers=teacher_headers)

        # Start attempt
        res_att = await client.post(
            f"/api/v1/students/me/activities/{act_id}/attempts",
            headers=student_headers,
            json={},
        )
        attempt_id = res_att.json()["attempt_id"]

        # Student first selects INCORRECT option
        ans1_key = str(uuid4())
        res_ans1 = await client.post(
            f"/api/v1/students/me/attempts/{attempt_id}/answers",
            headers={**student_headers, "X-Idempotency-Key": ans1_key},
            json={
                "question_id": str(data["q1"]["id"]),
                "selected_option_id": str(data["q1"]["opt_incorrect"]),
                "response_time_seconds": 5.0,
            },
        )
        assert res_ans1.status_code == 201

        # Student then changes answer to CORRECT option (new interaction event)
        ans2_key = str(uuid4())
        res_ans2 = await client.post(
            f"/api/v1/students/me/attempts/{attempt_id}/answers",
            headers={**student_headers, "X-Idempotency-Key": ans2_key},
            json={
                "question_id": str(data["q1"]["id"]),
                "selected_option_id": str(data["q1"]["opt_correct"]),
                "response_time_seconds": 3.0,
            },
        )
        assert res_ans2.status_code == 201

        # Verify answer_events contains both events with sequential order
        pool = await get_db_pool(dsn=TEST_DB_URL)
        async with pool.acquire() as conn:
            events = await conn.fetch(
                """
                SELECT id, question_sequence, selected_option_id, is_correct
                FROM answer_events
                WHERE attempt_id = $1
                ORDER BY question_sequence ASC;
                """,
                UUID(attempt_id),
            )
            assert len(events) == 2
            assert events[0]["question_sequence"] == 1
            assert events[0]["is_correct"] is False
            assert events[1]["question_sequence"] == 2
            assert events[1]["is_correct"] is True

        # Final score should use latest answer (100%)
        res_submit = await client.post(
            f"/api/v1/students/me/attempts/{attempt_id}/submit",
            headers=student_headers,
        )
        assert res_submit.status_code == 200
        assert res_submit.json()["score"] == 100.0

        # Teacher results: Question accuracy should not count 2 answers for 1 student attempt
        res_results = await client.get(
            f"/api/v1/activities/{act_id}/results",
            headers=teacher_headers,
        )
        assert res_results.status_code == 200
        q_stat = res_results.json()["questions_breakdown"][0]
        assert q_stat["total_answers"] == 1
        assert q_stat["correct_answers"] == 1
        assert q_stat["accuracy_rate"] == 100.0

