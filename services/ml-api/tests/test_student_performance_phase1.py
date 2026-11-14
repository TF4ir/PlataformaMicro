"""Phase 1 Backend Performance and Connection Pool Hardening Tests.

Validates all 6 mandatory requirements from the performance audit:
1. get_student_dashboard() operates reliably with pool max_size=1 (no deadlocks).
2. Zero nested connection acquisitions when conn is passed/reused.
3. get_student_progress() executes decoupled from get_student_dashboard().
4. Both endpoints maintain 100% response schema and contract fidelity.
5. Strict multi-tenant and student isolation is preserved.
6. Proper exception handling and connection release under query failures.
"""

import asyncio
import os
import time
from collections.abc import AsyncIterator
from datetime import datetime, timedelta, timezone
from typing import Any
from unittest.mock import AsyncMock, patch
from urllib.parse import urlparse
from uuid import UUID, uuid4

import asyncpg
import httpx
import pytest

import app.content_generation.infrastructure.database as db_mod
from app.api.v1.learning import get_learning_repo
from app.main import app
from app.repositories.learning_repository import LearningRepository
from app.schemas.activities import AttemptStatus
from app.schemas.learning import (
    StudentAnalyticsSummary,
    StudentDashboardResponse,
    StudentProgressDetailResponse,
)

TEST_DB_URL = os.getenv("TEST_DATABASE_URL", "postgresql://postgres:postgres@127.0.0.1:5432/plataformamicro_test")

# Isolated test environment validation (prevents execution against non-local databases)
_parsed_test_db = urlparse(TEST_DB_URL)
assert _parsed_test_db.hostname in ("127.0.0.1", "localhost", "::1"), (
    f"Security check failed: Tests must execute strictly against an isolated local database, got hostname {_parsed_test_db.hostname}"
)

TENANT_A = "11111111-1111-1111-1111-111111111111"
TENANT_B = "22222222-2222-2222-2222-222222222222"

TEACHER_A = "11111111-1111-1111-1111-aaaaaaaaaaaa"
STUDENT_A1 = "11111111-1111-1111-1111-bbbbbbbbbbbb"
STUDENT_A2 = "11111111-1111-1111-1111-bbbbbbbbbbbc"
STUDENT_NO_ENR = "11111111-1111-1111-1111-bbbbbbbbbbbd"

TEACHER_B = "22222222-2222-2222-2222-aaaaaaaaaaaa"
STUDENT_B = "22222222-2222-2222-2222-bbbbbbbbbbbb"

COURSE_A1 = "11111111-1111-1111-1111-cccccccccccc"
SECTION_A1 = "11111111-1111-1111-1111-dddddddddddd"
SECTION_A2 = "11111111-1111-1111-1111-ddddddddddde"

ENROLLMENT_A1 = "11111111-1111-1111-1111-999999999991"
ENROLLMENT_A2 = "11111111-1111-1111-1111-999999999992"

UNIT_A1 = "11111111-1111-1111-1111-eeeeeeeeee01"
KC1_A1 = "11111111-1111-1111-1111-ffffffffff01"
ACT_A1 = "11111111-1111-1111-1111-aaaaaaaaaa01"
ACT_SEC_A1 = "11111111-1111-1111-1111-aaaaaaaaaa02"
ATTEMPT_A1 = "11111111-1111-1111-1111-bbbbbbbbbb01"
Q_A1 = "11111111-1111-1111-1111-cccccccccc01"
OPT_A1 = "11111111-1111-1111-1111-dddddddddd01"
ANSWER_A1 = "11111111-1111-1111-1111-eeeeeeeeee02"
ANSWER_KEY_A1 = "11111111-1111-1111-1111-eeeeeeeeee03"


def make_headers(user_id: str, tenant_id: str, role: str) -> dict[str, str]:
    return {
        "X-User-Id": user_id,
        "X-Tenant-Id": tenant_id,
        "X-User-Role": role,
    }


@pytest.fixture(autouse=True)
async def seed_data() -> None:
    """Ensure baseline schema data is seeded idempotently and pool max_size=1 is enforced."""
    init_pool = await asyncpg.create_pool(dsn=TEST_DB_URL, min_size=1, max_size=2)
    async with init_pool.acquire() as conn:
        # 1. Tenants
        await conn.execute(
            """
            INSERT INTO tenants (id, name, slug) VALUES
                ($1, 'Colegio Piloto A', 'colegio-a-perf'),
                ($2, 'Colegio Piloto B', 'colegio-b-perf')
            ON CONFLICT (id) DO NOTHING;
            """,
            UUID(TENANT_A),
            UUID(TENANT_B),
        )

        # 2. Users & Profiles
        await conn.execute(
            """
            INSERT INTO auth.users (id, email) VALUES
                ($1, 'teacher_a@perf.edu'),
                ($2, 'student_a1@perf.edu'),
                ($3, 'student_a2@perf.edu'),
                ($4, 'teacher_b@perf.edu'),
                ($5, 'student_b@perf.edu'),
                ($6, 'student_no_enr@perf.edu')
            ON CONFLICT (id) DO NOTHING;
            """,
            UUID(TEACHER_A),
            UUID(STUDENT_A1),
            UUID(STUDENT_A2),
            UUID(TEACHER_B),
            UUID(STUDENT_B),
            UUID(STUDENT_NO_ENR),
        )
        await conn.execute(
            """
            INSERT INTO profiles (id, tenant_id, full_name, role, student_code) VALUES
                ($1, $2, 'Prof. Ada A', 'teacher', 'DOC-A1'),
                ($3, $2, 'Carlos Estudiante A1', 'student', 'EST-A1'),
                ($4, $2, 'Diana Estudiante A2', 'student', 'EST-A2'),
                ($5, $6, 'Prof. Beto B', 'teacher', 'DOC-B1'),
                ($7, $6, 'David Estudiante B', 'student', 'EST-B1'),
                ($8, $2, 'Elena Sin Matricula', 'student', 'EST-NO-ENR')
            ON CONFLICT (id) DO UPDATE SET full_name = EXCLUDED.full_name, role = EXCLUDED.role, student_code = EXCLUDED.student_code;
            """,
            UUID(TEACHER_A), UUID(TENANT_A),
            UUID(STUDENT_A1),
            UUID(STUDENT_A2),
            UUID(TEACHER_B), UUID(TENANT_B),
            UUID(STUDENT_B),
            UUID(STUDENT_NO_ENR),
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

        # 5. Units & Knowledge Components (Deterministic IDs to prevent table bloat)
        await conn.execute(
            """
            INSERT INTO units (id, tenant_id, course_id, title, order_index)
            VALUES ($1, $2, $3, 'Biología Celular', 1)
            ON CONFLICT (id) DO NOTHING;
            """,
            UUID(UNIT_A1), UUID(TENANT_A), UUID(COURSE_A1)
        )
        await conn.execute(
            """
            INSERT INTO knowledge_components (id, tenant_id, unit_id, name, difficulty_prior)
            VALUES ($1, $2, $3, 'Estructura Celular', 0.5)
            ON CONFLICT (id) DO NOTHING;
            """,
            UUID(KC1_A1), UUID(TENANT_A), UUID(UNIT_A1)
        )

        # 6. Published Activity
        await conn.execute(
            """
            INSERT INTO activities (
                id, tenant_id, course_id, created_by, title, description,
                activity_type, feedback_policy, status, is_active, published_at
            ) VALUES (
                $1, $2, $3, $4, 'Práctica de Células', 'Evaluación rápida',
                'formative', 'immediate_with_explanation', 'published', true, now()
            )
            ON CONFLICT (id) DO NOTHING;
            """,
            UUID(ACT_A1), UUID(TENANT_A), UUID(COURSE_A1), UUID(TEACHER_A)
        )
        await conn.execute(
            """
            INSERT INTO activity_sections (id, tenant_id, activity_id, section_id)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (id) DO NOTHING;
            """,
            UUID(ACT_SEC_A1), UUID(TENANT_A), UUID(ACT_A1), UUID(SECTION_A1)
        )

        # 7. Completed Attempt and Answer Event for student A1
        actual_enr_a1 = await conn.fetchval(
            "SELECT id FROM enrollments WHERE section_id = $1 AND student_id = $2;",
            UUID(SECTION_A1),
            UUID(STUDENT_A1),
        )
        await conn.execute(
            """
            INSERT INTO quiz_attempts (
                id, tenant_id, enrollment_id, activity_id, student_id,
                attempt_number, status, score, total_questions, correct_answers,
                started_at, completed_at
            ) VALUES (
                $1, $2, $3, $4, $5, 1, 'completed', 100.0, 1, 1, now(), now()
            )
            ON CONFLICT (id) DO NOTHING;
            """,
            UUID(ATTEMPT_A1), UUID(TENANT_A), actual_enr_a1, UUID(ACT_A1), UUID(STUDENT_A1)
        )

        await conn.execute(
            """
            INSERT INTO questions (id, tenant_id, knowledge_component_id, question_text, explanation, difficulty, created_by, is_active)
            VALUES ($1, $2, $3, '¿Tiene la célula eucariota núcleo?', 'Las células eucariotas tienen núcleo definido.', 0.5, $4, true)
            ON CONFLICT (id) DO NOTHING;
            """,
            UUID(Q_A1), UUID(TENANT_A), UUID(KC1_A1), UUID(TEACHER_A)
        )

        await conn.execute(
            """
            INSERT INTO question_options (id, question_id, option_text, is_correct, order_index)
            VALUES ($1, $2, 'Sí, contiene núcleo', true, 1)
            ON CONFLICT (id) DO NOTHING;
            """,
            UUID(OPT_A1), UUID(Q_A1)
        )

        await conn.execute(
            """
            INSERT INTO answer_events (
                id, tenant_id, attempt_id, student_id, question_id,
                knowledge_component_id, selected_option_id, is_correct,
                attempt_number, response_time_seconds, idempotency_key,
                activity_id, course_id, event_timestamp
            ) VALUES (
                $1, $2, $3, $4, $5,
                $6, $7, true,
                1, 5.0, $8,
                $9, $10, now()
            )
            ON CONFLICT (id) DO NOTHING;
            """,
            UUID(ANSWER_A1), UUID(TENANT_A), UUID(ATTEMPT_A1), UUID(STUDENT_A1), UUID(Q_A1),
            UUID(KC1_A1), UUID(OPT_A1), UUID(ANSWER_KEY_A1),
            UUID(ACT_A1), UUID(COURSE_A1)
        )

    await init_pool.close()


@pytest.fixture
async def pool_size_1() -> AsyncIterator[asyncpg.Pool]:
    """AsyncPG connection pool strictly configured with min_size=1, max_size=1."""
    pool = await asyncpg.create_pool(
        dsn=TEST_DB_URL,
        min_size=1,
        max_size=1,
        command_timeout=5,
    )
    db_mod._POOL = pool
    yield pool
    await pool.close()
    db_mod._POOL = None


# ============================================================================
# 1. get_student_dashboard() funciona con un pool cuyo max_size=1
# ============================================================================

@pytest.mark.asyncio
async def test_01_dashboard_succeeds_with_pool_max_size_1(pool_size_1: asyncpg.Pool) -> None:
    """Demuestra que get_student_dashboard() finaliza con éxito sin deadlock en un pool max_size=1."""
    repo = LearningRepository(pool=pool_size_1)

    # Debe completarse rápidamente en < 2 segundos sin entrar en contención de conexiones
    start_t = time.perf_counter()
    dashboard = await asyncio.wait_for(
        repo.get_student_dashboard(tenant_id=UUID(TENANT_A), student_id=UUID(STUDENT_A1)),
        timeout=3.0,
    )
    duration = time.perf_counter() - start_t

    assert isinstance(dashboard, StudentDashboardResponse)
    assert dashboard.student_name == "Carlos Estudiante A1"
    assert dashboard.student_code == "EST-A1"
    assert len(dashboard.enrolled_courses) >= 1
    assert dashboard.analytics.total_answers >= 1
    assert dashboard.analytics.completed_activities_count >= 1
    assert duration < 2.0, f"Dashboard took too long: {duration:.3f}s"


@pytest.mark.asyncio
async def test_01b_sequential_dashboard_calls_on_max_size_1(pool_size_1: asyncpg.Pool) -> None:
    """Verifica que múltiples ejecuciones sucesivas con pool max_size=1 no acumulan fugas."""
    repo = LearningRepository(pool=pool_size_1)
    for _ in range(5):
        dashboard = await repo.get_student_dashboard(tenant_id=UUID(TENANT_A), student_id=UUID(STUDENT_A1))
        assert dashboard is not None


# ============================================================================
# 2. No se produce una segunda adquisición de conexión cuando se reutiliza conn
# ============================================================================

class SpyPool:
    """Wrapper around asyncpg.Pool to monitor pool acquisition calls."""

    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool
        self.acquire_count = 0

    def acquire(self, *args: Any, **kwargs: Any) -> Any:
        self.acquire_count += 1
        return self._pool.acquire(*args, **kwargs)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._pool, name)


@pytest.mark.asyncio
async def test_02a_list_student_activities_reuses_passed_connection(pool_size_1: asyncpg.Pool) -> None:
    """Demuestra que list_student_activities() no invoca pool.acquire() cuando recibe conn."""
    spy_pool = SpyPool(pool_size_1)
    repo = LearningRepository(pool=spy_pool)

    async with pool_size_1.acquire() as active_conn:
        activities = await repo.list_student_activities(
            tenant_id=UUID(TENANT_A),
            student_id=UUID(STUDENT_A1),
            conn=active_conn,
        )
        assert spy_pool.acquire_count == 0, "No debe adquirirse ninguna conexión del pool cuando se pasa conn"
        assert isinstance(activities, list)


@pytest.mark.asyncio
async def test_02b_fetch_student_analytics_reuses_passed_connection(pool_size_1: asyncpg.Pool) -> None:
    """Demuestra que _fetch_student_analytics() no invoca pool.acquire() cuando recibe conn."""
    spy_pool = SpyPool(pool_size_1)
    repo = LearningRepository(pool=spy_pool)

    async with pool_size_1.acquire() as active_conn:
        analytics = await repo._fetch_student_analytics(
            tenant_id=UUID(TENANT_A),
            student_id=UUID(STUDENT_A1),
            conn=active_conn,
        )
        assert spy_pool.acquire_count == 0, "No debe adquirirse ninguna conexión del pool cuando se pasa conn"
        assert isinstance(analytics, StudentAnalyticsSummary)


@pytest.mark.asyncio
async def test_02c_dashboard_performs_exactly_one_pool_acquisition(pool_size_1: asyncpg.Pool) -> None:
    """Demuestra que get_student_dashboard() adquiere la conexión del pool exactamente 1 vez."""
    spy_pool = SpyPool(pool_size_1)
    repo = LearningRepository(pool=spy_pool)

    dashboard = await repo.get_student_dashboard(
        tenant_id=UUID(TENANT_A),
        student_id=UUID(STUDENT_A1),
    )
    assert spy_pool.acquire_count == 1, (
        f"El dashboard completo debe realizar exactamente 1 adquisición de conexión, pero realizó {spy_pool.acquire_count}"
    )
    assert isinstance(dashboard, StudentDashboardResponse)


@pytest.mark.asyncio
async def test_02d_dashboard_with_passed_conn_performs_zero_acquisitions(pool_size_1: asyncpg.Pool) -> None:
    """Demuestra que si get_student_dashboard() recibe conn, adquiere 0 conexiones del pool."""
    spy_pool = SpyPool(pool_size_1)
    repo = LearningRepository(pool=spy_pool)

    async with pool_size_1.acquire() as active_conn:
        dashboard = await repo.get_student_dashboard(
            tenant_id=UUID(TENANT_A),
            student_id=UUID(STUDENT_A1),
            conn=active_conn,
        )
        assert spy_pool.acquire_count == 0
        assert isinstance(dashboard, StudentDashboardResponse)


@pytest.mark.asyncio
async def test_02e_proves_old_behavior_would_timeout_without_conn_reuse(pool_size_1: asyncpg.Pool) -> None:
    """Demuestra que intentar una adquisición anidada sin pasar conn causaría bloqueo en max_size=1."""
    repo = LearningRepository(pool=pool_size_1)

    async with pool_size_1.acquire():
        # La única conexión del pool está ocupada.
        # Si invocamos list_student_activities sin pasar conn, debe intentar adquirir del pool y bloquearse.
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(
                repo.list_student_activities(
                    tenant_id=UUID(TENANT_A),
                    student_id=UUID(STUDENT_A1),
                    conn=None,  # omite conn deliberadamente para demostrar el bloqueo
                ),
                timeout=0.3,
            )


@pytest.mark.asyncio
async def test_02f_start_attempt_succeeds_and_reuses_connection_on_max_size_1(pool_size_1: asyncpg.Pool) -> None:
    """Demuestra que start_attempt() opera en un pool max_size=1 reutilizando la conexión en su flujo transaccional.

    Evita deadlocks al delegar en get_student_activity_detail pasando conn=conn dentro
    del bloque transaccional, requiriendo exactamente 1 adquisición del pool.
    """
    spy_pool = SpyPool(pool_size_1)
    repo = LearningRepository(pool=spy_pool)

    act_id = uuid4()
    sec_id = UUID(SECTION_A1)
    tenant_id = UUID(TENANT_A)
    teacher_id = UUID(TEACHER_A)
    course_id = UUID(COURSE_A1)
    student_id = UUID(STUDENT_A1)
    q_id = UUID(Q_A1)

    async with pool_size_1.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO activities (
                id, tenant_id, course_id, created_by, title, description,
                activity_type, feedback_policy, status, is_active, max_attempts, published_at
            ) VALUES (
                $1, $2, $3, $4, 'Actividad Verificación Transaccional', 'Validación pool 1',
                'formative', 'immediate_with_explanation', 'published', true, 5, now()
            );
            """,
            act_id, tenant_id, course_id, teacher_id,
        )
        await conn.execute(
            """
            INSERT INTO activity_sections (id, tenant_id, activity_id, section_id)
            VALUES ($1, $2, $3, $4);
            """,
            uuid4(), tenant_id, act_id, sec_id,
        )
        await conn.execute(
            """
            INSERT INTO activity_questions (activity_id, question_id, order_index)
            VALUES ($1, $2, 1);
            """,
            act_id, q_id,
        )

    # Reiniciar contador del spy pool tras la preparación
    spy_pool.acquire_count = 0

    idem_key = uuid4()
    # 1. Iniciar intento: debe completarse sin bloqueo en < 2 segundos
    start_t = time.perf_counter()
    attempt = await asyncio.wait_for(
        repo.start_attempt(
            tenant_id=tenant_id,
            student_id=student_id,
            activity_id=act_id,
            idempotency_key=idem_key,
        ),
        timeout=3.0,
    )
    duration = time.perf_counter() - start_t

    # Verificaciones
    assert duration < 2.0, f"start_attempt tardó demasiado en pool max_size=1: {duration:.3f}s"
    assert spy_pool.acquire_count == 1, (
        f"start_attempt debe reutilizar conn internamente con exactamente 1 adquisición del pool, pero realizó {spy_pool.acquire_count}"
    )
    assert attempt.attempt_id is not None
    assert attempt.activity_id == act_id
    assert attempt.status == AttemptStatus.IN_PROGRESS
    assert len(attempt.questions) >= 1

    # 2. Re-invocación idempotente: debe reutilizar la conexión y devolver el mismo intento sin deadlock
    attempt_idem = await asyncio.wait_for(
        repo.start_attempt(
            tenant_id=tenant_id,
            student_id=student_id,
            activity_id=act_id,
            idempotency_key=idem_key,
        ),
        timeout=3.0,
    )
    assert spy_pool.acquire_count == 2, (
        f"La llamada idempotente debe requerir exactamente 1 adquisición adicional (total 2), pero obtuvo {spy_pool.acquire_count}"
    )
    assert attempt_idem.attempt_id == attempt.attempt_id
    assert attempt_idem.status == AttemptStatus.IN_PROGRESS

    # Limpieza de entidades de prueba transaccionales
    async with pool_size_1.acquire() as conn:
        await conn.execute("DELETE FROM quiz_attempts WHERE activity_id = $1;", act_id)
        await conn.execute("DELETE FROM activity_questions WHERE activity_id = $1;", act_id)
        await conn.execute("DELETE FROM activity_sections WHERE activity_id = $1;", act_id)
        await conn.execute("DELETE FROM activities WHERE id = $1;", act_id)


@pytest.mark.asyncio
async def test_02g_start_attempt_concurrent_race_condition_handled_cleanly() -> None:
    """Verifica que carreras concurrentes con la misma clave de idempotencia no aborten la transacción.

    Demuestra la efectividad del SAVEPOINT interno (`async with conn.transaction():`)
    permitiendo que la excepción UniqueViolationError no contamine la conexión con
    InFailedSQLTransactionError y recupere el intento existente limpiamente.
    """
    concurrent_pool = await asyncpg.create_pool(dsn=TEST_DB_URL, min_size=2, max_size=2)
    repo = LearningRepository(pool=concurrent_pool)

    act_id = uuid4()
    sec_id = UUID(SECTION_A1)
    tenant_id = UUID(TENANT_A)
    teacher_id = UUID(TEACHER_A)
    course_id = UUID(COURSE_A1)
    student_id = UUID(STUDENT_A1)
    q_id = UUID(Q_A1)

    async with concurrent_pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO activities (
                id, tenant_id, course_id, created_by, title, description,
                activity_type, feedback_policy, status, is_active, max_attempts, published_at
            ) VALUES (
                $1, $2, $3, $4, 'Actividad Concurrente Savepoint', 'Validación SAVEPOINT',
                'formative', 'immediate_with_explanation', 'published', true, 5, now()
            );
            """,
            act_id, tenant_id, course_id, teacher_id,
        )
        await conn.execute(
            "INSERT INTO activity_sections (id, tenant_id, activity_id, section_id) VALUES ($1, $2, $3, $4);",
            uuid4(), tenant_id, act_id, sec_id,
        )
        await conn.execute(
            "INSERT INTO activity_questions (activity_id, question_id, order_index) VALUES ($1, $2, 1);",
            act_id, q_id,
        )

    idem_key = uuid4()
    try:
        t1 = asyncio.create_task(
            repo.start_attempt(
                tenant_id=tenant_id,
                student_id=student_id,
                activity_id=act_id,
                idempotency_key=idem_key,
            )
        )
        t2 = asyncio.create_task(
            repo.start_attempt(
                tenant_id=tenant_id,
                student_id=student_id,
                activity_id=act_id,
                idempotency_key=idem_key,
            )
        )
        res1, res2 = await asyncio.gather(t1, t2)
        assert res1.attempt_id == res2.attempt_id
        assert res1.status == AttemptStatus.IN_PROGRESS
        assert len(res1.questions) >= 1
    finally:
        async with concurrent_pool.acquire() as conn:
            await conn.execute("DELETE FROM quiz_attempts WHERE activity_id = $1;", act_id)
            await conn.execute("DELETE FROM activity_questions WHERE activity_id = $1;", act_id)
            await conn.execute("DELETE FROM activity_sections WHERE activity_id = $1;", act_id)
            await conn.execute("DELETE FROM activities WHERE id = $1;", act_id)
        await concurrent_pool.close()


# ============================================================================
# 3. get_student_progress() funciona sin ejecutar el dashboard completo
# ============================================================================

@pytest.mark.asyncio
async def test_03a_progress_does_not_call_get_student_dashboard(pool_size_1: asyncpg.Pool) -> None:
    """Demuestra que get_student_progress() no ejecuta get_student_dashboard()."""
    repo = LearningRepository(pool=pool_size_1)

    with patch.object(repo, "get_student_dashboard", wraps=repo.get_student_dashboard) as mock_dash:
        progress = await repo.get_student_progress(
            tenant_id=UUID(TENANT_A),
            student_id=UUID(STUDENT_A1),
        )
        mock_dash.assert_not_called()
        assert isinstance(progress, StudentProgressDetailResponse)


@pytest.mark.asyncio
async def test_03b_progress_does_not_call_list_student_activities(pool_size_1: asyncpg.Pool) -> None:
    """Demuestra que get_student_progress() no recupera la lista completa de actividades del dashboard."""
    repo = LearningRepository(pool=pool_size_1)

    with patch.object(repo, "list_student_activities", wraps=repo.list_student_activities) as mock_acts:
        progress = await repo.get_student_progress(
            tenant_id=UUID(TENANT_A),
            student_id=UUID(STUDENT_A1),
        )
        mock_acts.assert_not_called()
        assert isinstance(progress, StudentProgressDetailResponse)


@pytest.mark.asyncio
async def test_03c_analytics_parity_between_dashboard_and_progress(pool_size_1: asyncpg.Pool) -> None:
    """Demuestra que las métricas de analítica compartida son idénticas en dashboard y progreso."""
    repo = LearningRepository(pool=pool_size_1)

    dashboard = await repo.get_student_dashboard(tenant_id=UUID(TENANT_A), student_id=UUID(STUDENT_A1))
    progress = await repo.get_student_progress(tenant_id=UUID(TENANT_A), student_id=UUID(STUDENT_A1))

    dash_ana = dashboard.analytics
    prog_ana = progress.analytics

    assert dash_ana.total_answers == prog_ana.total_answers
    assert dash_ana.observed_accuracy_percentage == prog_ana.observed_accuracy_percentage
    assert dash_ana.completed_activities_count == prog_ana.completed_activities_count
    assert dash_ana.reviewed_concepts_count == prog_ana.reviewed_concepts_count
    assert dash_ana.consolidated_concepts_count == prog_ana.consolidated_concepts_count
    assert dash_ana.total_concepts_count == prog_ana.total_concepts_count
    assert dash_ana.weekly_learning_minutes == prog_ana.weekly_learning_minutes


@pytest.mark.asyncio
async def test_03d_fetch_student_analytics_independent_oracle_validation(pool_size_1: asyncpg.Pool) -> None:
    """Valida _fetch_student_analytics() con un oráculo independiente de registros conocidos.

    Verifica de manera determinista cada métrica principal calculada por la consulta SQL CTE:
    - total_answers: conteo exacto de respuestas del estudiante.
    - observed_accuracy_percentage: tasa calculada (respuestas_correctas / total * 100).
    - weekly_learning_minutes: suma de duration_seconds // 60 con exclusión de eventos > 7 días.
    - consolidated_concepts_count: componentes con precisión >= 80%.
    - reviewed_concepts_count: unión de KCs con actividad en los últimos 7 días.
    - total_concepts_count y completed_activities_count: agregación de cursos activos vía CTE.
    """
    tenant_id = UUID(TENANT_A)
    student_id = uuid4()
    teacher_id = UUID(TEACHER_A)
    course_id = uuid4()
    unit_id = uuid4()
    kc1_id = uuid4()
    kc2_id = uuid4()
    micro1_id = uuid4()
    micro2_id = uuid4()
    sec_id = uuid4()
    enr_id = uuid4()
    act1_id = uuid4()
    act2_id = uuid4()
    qa1_id = uuid4()
    qa2_id = uuid4()
    q1_id = uuid4()
    q2_id = uuid4()
    opt1_id = uuid4()
    opt2_id = uuid4()

    now = datetime.now(timezone.utc)

    async with pool_size_1.acquire() as conn:
        # 1. Estudiante aislado
        await conn.execute(
            "INSERT INTO auth.users (id, email) VALUES ($1, $2);",
            student_id, f"oracle_{student_id}@perf.edu",
        )
        await conn.execute(
            """
            INSERT INTO profiles (id, tenant_id, full_name, role, student_code)
            VALUES ($1, $2, $3, $4, $5);
            """,
            student_id, tenant_id, "Estudiante Oráculo", "student", f"ORC-{str(student_id)[:6]}",
        )

        # 2. Curso, Unidad y 2 Knowledge Components (total_concepts_count = 2)
        await conn.execute(
            "INSERT INTO courses (id, tenant_id, code, name, is_active) VALUES ($1, $2, $3, $4, true);",
            course_id, tenant_id, f"ORC-{str(course_id)[:4]}", "Curso Oráculo",
        )
        await conn.execute(
            "INSERT INTO units (id, tenant_id, course_id, title, order_index) VALUES ($1, $2, $3, $4, 1);",
            unit_id, tenant_id, course_id, "Unidad Oráculo",
        )
        await conn.execute(
            "INSERT INTO knowledge_components (id, tenant_id, unit_id, name, difficulty_prior) VALUES ($1, $2, $3, $4, 0.5);",
            kc1_id, tenant_id, unit_id, "KC Oráculo Consolidado",
        )
        await conn.execute(
            "INSERT INTO knowledge_components (id, tenant_id, unit_id, name, difficulty_prior) VALUES ($1, $2, $3, $4, 0.5);",
            kc2_id, tenant_id, unit_id, "KC Oráculo No Consolidado",
        )

        # 3. Microcontenidos requeridos para exposures
        await conn.execute(
            """
            INSERT INTO microcontents (id, tenant_id, knowledge_component_id, title, content_type, content_body, created_by, is_published)
            VALUES ($1, $2, $3, $4, 'text_summary'::content_type_enum, '{"text": "Resumen"}'::jsonb, $5, true);
            """,
            micro1_id, tenant_id, kc1_id, "Ficha Oráculo 1", teacher_id,
        )
        await conn.execute(
            """
            INSERT INTO microcontents (id, tenant_id, knowledge_component_id, title, content_type, content_body, created_by, is_published)
            VALUES ($1, $2, $3, $4, 'text_summary'::content_type_enum, '{"text": "Resumen"}'::jsonb, $5, true);
            """,
            micro2_id, tenant_id, kc2_id, "Ficha Oráculo 2", teacher_id,
        )

        # 4. Sección y Matrícula
        await conn.execute(
            "INSERT INTO sections (id, tenant_id, course_id, teacher_id, name) VALUES ($1, $2, $3, $4, $5);",
            sec_id, tenant_id, course_id, teacher_id, "Sección Oráculo",
        )
        await conn.execute(
            "INSERT INTO enrollments (id, tenant_id, section_id, student_id) VALUES ($1, $2, $3, $4);",
            enr_id, tenant_id, sec_id, student_id,
        )

        # 5. 2 Actividades y 2 Intentos completados (completed_activities_count = 2)
        await conn.execute(
            """
            INSERT INTO activities (id, tenant_id, course_id, created_by, title, activity_type, status, is_active, max_attempts)
            VALUES ($1, $2, $3, $4, $5, 'formative', 'published', true, 10);
            """,
            act1_id, tenant_id, course_id, teacher_id, "Actividad Oráculo 1",
        )
        await conn.execute(
            """
            INSERT INTO activities (id, tenant_id, course_id, created_by, title, activity_type, status, is_active, max_attempts)
            VALUES ($1, $2, $3, $4, $5, 'formative', 'published', true, 10);
            """,
            act2_id, tenant_id, course_id, teacher_id, "Actividad Oráculo 2",
        )
        await conn.execute(
            """
            INSERT INTO quiz_attempts (
                id, tenant_id, enrollment_id, activity_id, student_id,
                attempt_number, status, score, total_questions, correct_answers, started_at, completed_at
            ) VALUES ($1, $2, $3, $4, $5, 1, 'completed', 100.0, 1, 1, now(), now());
            """,
            qa1_id, tenant_id, enr_id, act1_id, student_id,
        )
        await conn.execute(
            """
            INSERT INTO quiz_attempts (
                id, tenant_id, enrollment_id, activity_id, student_id,
                attempt_number, status, score, total_questions, correct_answers, started_at, completed_at
            ) VALUES ($1, $2, $3, $4, $5, 1, 'completed', 100.0, 1, 1, now(), now());
            """,
            qa2_id, tenant_id, enr_id, act2_id, student_id,
        )

        # 6. Preguntas y Opciones
        await conn.execute(
            "INSERT INTO questions (id, tenant_id, knowledge_component_id, question_text, explanation, difficulty, created_by) VALUES ($1, $2, $3, 'Q1', 'Exp1', 0.5, $4);",
            q1_id, tenant_id, kc1_id, teacher_id,
        )
        await conn.execute(
            "INSERT INTO questions (id, tenant_id, knowledge_component_id, question_text, explanation, difficulty, created_by) VALUES ($1, $2, $3, 'Q2', 'Exp2', 0.5, $4);",
            q2_id, tenant_id, kc2_id, teacher_id,
        )
        await conn.execute(
            "INSERT INTO question_options (id, question_id, option_text, is_correct, order_index) VALUES ($1, $2, 'Opt1', true, 1);",
            opt1_id, q1_id,
        )
        await conn.execute(
            "INSERT INTO question_options (id, question_id, option_text, is_correct, order_index) VALUES ($1, $2, 'Opt2', true, 1);",
            opt2_id, q2_id,
        )

        # 7. 8 Answer Events conocidos:
        # KC1: 4 respuestas, 4 correctas (4/4 = 100% >= 80% => Consolidado)
        for i in range(4):
            await conn.execute(
                """
                INSERT INTO answer_events (
                    id, tenant_id, attempt_id, student_id, question_id, knowledge_component_id,
                    selected_option_id, is_correct, attempt_number, response_time_seconds,
                    idempotency_key, activity_id, course_id, event_timestamp
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, true, 1, 5.0, $8, $9, $10, $11);
                """,
                uuid4(), tenant_id, qa1_id, student_id, q1_id, kc1_id, opt1_id,
                uuid4(), act1_id, course_id, now - timedelta(days=1, hours=i),
            )

        # KC2: 4 respuestas, 2 correctas y 2 incorrectas (2/4 = 50% < 80% => No consolidado)
        for i in range(4):
            is_corr = (i < 2)
            await conn.execute(
                """
                INSERT INTO answer_events (
                    id, tenant_id, attempt_id, student_id, question_id, knowledge_component_id,
                    selected_option_id, is_correct, attempt_number, response_time_seconds,
                    idempotency_key, activity_id, course_id, event_timestamp
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, 1, 5.0, $9, $10, $11, $12);
                """,
                uuid4(), tenant_id, qa2_id, student_id, q2_id, kc2_id, opt2_id,
                is_corr, uuid4(), act2_id, course_id, now - timedelta(days=2, hours=i),
            )

        # 8. 3 Content Exposure Events conocidos:
        # Evento 1: 185 segundos en KC1 (hace 1 día -> dentro de 7 días)
        t1 = now - timedelta(days=1)
        await conn.execute(
            """
            INSERT INTO content_exposure_events (
                id, tenant_id, student_id, student_id_pseudo, microcontent_id, knowledge_component_id,
                exposure_type, started_at, completed_at, duration_seconds, active_reading_seconds,
                completion_status, session_id, idempotency_key, metadata, event_timestamp
            ) VALUES (
                $1, $2, $3, $4, $5, $6,
                'initial_study'::exposure_type_enum, $7, $8, 185.0, 160.0,
                'completed'::exposure_completion_status_enum, $9, $10, '{}'::jsonb, $11
            );
            """,
            uuid4(), tenant_id, student_id, uuid4(), micro1_id, kc1_id,
            t1, t1 + timedelta(seconds=185), uuid4(), uuid4(), t1,
        )

        # Evento 2: 125 segundos en KC2 (hace 3 días -> dentro de 7 días)
        t2 = now - timedelta(days=3)
        await conn.execute(
            """
            INSERT INTO content_exposure_events (
                id, tenant_id, student_id, student_id_pseudo, microcontent_id, knowledge_component_id,
                exposure_type, started_at, completed_at, duration_seconds, active_reading_seconds,
                completion_status, session_id, idempotency_key, metadata, event_timestamp
            ) VALUES (
                $1, $2, $3, $4, $5, $6,
                'initial_study'::exposure_type_enum, $7, $8, 125.0, 100.0,
                'completed'::exposure_completion_status_enum, $9, $10, '{}'::jsonb, $11
            );
            """,
            uuid4(), tenant_id, student_id, uuid4(), micro2_id, kc2_id,
            t2, t2 + timedelta(seconds=125), uuid4(), uuid4(), t2,
        )

        # Evento 3: 600 segundos en KC1 (hace 12 días -> fuera de 7 días, DEBE ser filtrado)
        t3 = now - timedelta(days=12)
        await conn.execute(
            """
            INSERT INTO content_exposure_events (
                id, tenant_id, student_id, student_id_pseudo, microcontent_id, knowledge_component_id,
                exposure_type, started_at, completed_at, duration_seconds, active_reading_seconds,
                completion_status, session_id, idempotency_key, metadata, event_timestamp
            ) VALUES (
                $1, $2, $3, $4, $5, $6,
                'initial_study'::exposure_type_enum, $7, $8, 600.0, 500.0,
                'completed'::exposure_completion_status_enum, $9, $10, '{}'::jsonb, $11
            );
            """,
            uuid4(), tenant_id, student_id, uuid4(), micro1_id, kc1_id,
            t3, t3 + timedelta(seconds=600), uuid4(), uuid4(), t3,
        )

    repo = LearningRepository(pool=pool_size_1)

    # -------------------------------------------------------------------------
    # Oráculo Independiente: Valores esperados calculados matemáticamente
    # -------------------------------------------------------------------------
    ORACLE_TOTAL_ANSWERS = 8
    ORACLE_CORRECT_ANSWERS = 6
    ORACLE_OBSERVED_ACCURACY = round((ORACLE_CORRECT_ANSWERS / ORACLE_TOTAL_ANSWERS) * 100.0, 1)  # 75.0%
    ORACLE_RECENT_EXPOSURE_SECONDS = 185.0 + 125.0  # 310.0 segundos (600s excluido por filtro 7d)
    ORACLE_WEEKLY_LEARNING_MINUTES = int(ORACLE_RECENT_EXPOSURE_SECONDS // 60)  # 5 minutos
    ORACLE_CONSOLIDATED_KCS = 1  # KC1 (100% >= 80%), KC2 (50% < 80%)
    ORACLE_REVIEWED_KCS = 2  # {KC1, KC2} tocados en los últimos 7 días
    ORACLE_TOTAL_CONCEPTS = 2  # 2 KCs en el curso activo matriculado
    ORACLE_COMPLETED_ACTIVITIES = 2  # 2 actividades con intento 'completed'

    # 1. Validación en modo Standalone (CTE unificada calcula course_s en BD)
    analytics_standalone = await repo._fetch_student_analytics(
        tenant_id=tenant_id,
        student_id=student_id,
    )
    assert analytics_standalone.total_answers == ORACLE_TOTAL_ANSWERS
    assert analytics_standalone.observed_accuracy_percentage == ORACLE_OBSERVED_ACCURACY
    assert analytics_standalone.weekly_learning_minutes == ORACLE_WEEKLY_LEARNING_MINUTES
    assert analytics_standalone.consolidated_concepts_count == ORACLE_CONSOLIDATED_KCS
    assert analytics_standalone.reviewed_concepts_count == ORACLE_REVIEWED_KCS
    assert analytics_standalone.total_concepts_count == ORACLE_TOTAL_CONCEPTS
    assert analytics_standalone.completed_activities_count == ORACLE_COMPLETED_ACTIVITIES

    # 2. Validación en modo Precomputed (métricas de curso precalculadas)
    analytics_precomputed = await repo._fetch_student_analytics(
        tenant_id=tenant_id,
        student_id=student_id,
        total_concepts_count=ORACLE_TOTAL_CONCEPTS,
        completed_activities_count=ORACLE_COMPLETED_ACTIVITIES,
    )
    assert analytics_precomputed.total_answers == ORACLE_TOTAL_ANSWERS
    assert analytics_precomputed.observed_accuracy_percentage == ORACLE_OBSERVED_ACCURACY
    assert analytics_precomputed.weekly_learning_minutes == ORACLE_WEEKLY_LEARNING_MINUTES
    assert analytics_precomputed.consolidated_concepts_count == ORACLE_CONSOLIDATED_KCS
    assert analytics_precomputed.reviewed_concepts_count == ORACLE_REVIEWED_KCS
    assert analytics_precomputed.total_concepts_count == ORACLE_TOTAL_CONCEPTS
    assert analytics_precomputed.completed_activities_count == ORACLE_COMPLETED_ACTIVITIES


# ============================================================================
# 4. Ambos endpoints mantienen sus estructuras de respuesta (Contratos)
# ============================================================================

@pytest.mark.asyncio
async def test_04a_dashboard_endpoint_contract_fidelity(pool_size_1: asyncpg.Pool) -> None:
    """Verifica contrato HTTP y serialización completa de /students/me/dashboard."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        headers = make_headers(STUDENT_A1, TENANT_A, "student")

        for path in ("/api/v1/students/me/dashboard", "/api/v1/learning/student/dashboard"):
            resp = await client.get(path, headers=headers)
            assert resp.status_code == 200
            data = resp.json()

            # Validación estricta con Pydantic
            parsed = StudentDashboardResponse.model_validate(data)
            assert parsed.student_name == "Carlos Estudiante A1"
            assert isinstance(parsed.enrolled_courses, list)
            assert isinstance(parsed.analytics, StudentAnalyticsSummary)
            assert isinstance(parsed.upcoming_reviews, list)
            assert isinstance(parsed.recent_activities, list)


@pytest.mark.asyncio
async def test_04b_progress_endpoint_contract_fidelity(pool_size_1: asyncpg.Pool) -> None:
    """Verifica contrato HTTP y serialización completa de /students/me/progress."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        headers = make_headers(STUDENT_A1, TENANT_A, "student")

        for path in ("/api/v1/students/me/progress", "/api/v1/learning/student/progress"):
            resp = await client.get(path, headers=headers)
            assert resp.status_code == 200
            data = resp.json()

            # Validación estricta con Pydantic
            parsed = StudentProgressDetailResponse.model_validate(data)
            assert isinstance(parsed.analytics, StudentAnalyticsSummary)
            assert isinstance(parsed.evolution, list)
            assert isinstance(parsed.kc_breakdown, list)
            assert isinstance(parsed.activity_history, list)


# ============================================================================
# 5. Se conserva el aislamiento entre estudiantes y tenants
# ============================================================================

@pytest.mark.asyncio
async def test_05a_student_isolation_in_same_tenant(pool_size_1: asyncpg.Pool) -> None:
    """Estudiante A2 no ve las respuestas ni intentos del Estudiante A1."""
    repo = LearningRepository(pool=pool_size_1)

    dash_a1 = await repo.get_student_dashboard(tenant_id=UUID(TENANT_A), student_id=UUID(STUDENT_A1))
    dash_a2 = await repo.get_student_dashboard(tenant_id=UUID(TENANT_A), student_id=UUID(STUDENT_A2))

    assert dash_a1.analytics.total_answers >= 1
    assert dash_a2.analytics.total_answers == 0
    assert dash_a1.student_name == "Carlos Estudiante A1"
    assert dash_a2.student_name == "Diana Estudiante A2"


@pytest.mark.asyncio
async def test_05b_multi_tenant_isolation(pool_size_1: asyncpg.Pool) -> None:
    """Estudiante de Tenant B no tiene acceso a cursos ni datos de Tenant A."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        headers_b = make_headers(STUDENT_B, TENANT_B, "student")
        resp = await client.get("/api/v1/students/me/dashboard", headers=headers_b)
        assert resp.status_code == 200
        data = resp.json()

        # Estudiante B no debe ver cursos ni datos de Tenant A
        course_ids = [c["course_id"] for c in data["enrolled_courses"]]
        assert COURSE_A1 not in course_ids
        for c in data["enrolled_courses"]:
            assert c["course_id"] != COURSE_A1


# ============================================================================
# 6. Manejo correcto de errores de consulta y liberación de conexiones
# ============================================================================

@pytest.mark.asyncio
async def test_06a_dashboard_exception_releases_connection_to_pool(pool_size_1: asyncpg.Pool) -> None:
    """Si ocurre un error en get_student_dashboard, la conexión se libera inmediatamente al pool."""
    repo = LearningRepository(pool=pool_size_1)

    # Forzar fallo simulando error en consulta SQL interna
    with patch.object(asyncpg.Connection, "fetchrow", side_effect=asyncpg.PostgresError("Simulated SQL Error")):
        with pytest.raises(asyncpg.PostgresError):
            await repo.get_student_dashboard(tenant_id=UUID(TENANT_A), student_id=UUID(STUDENT_A1))

    # Verificar que el pool max_size=1 sigue operativo inmediatamente sin quedar trabado
    async with pool_size_1.acquire() as conn:
        val = await conn.fetchval("SELECT 1;")
        assert val == 1


@pytest.mark.asyncio
async def test_06b_progress_exception_releases_connection_to_pool(pool_size_1: asyncpg.Pool) -> None:
    """Si ocurre un error en get_student_progress, la conexión se libera inmediatamente al pool."""
    repo = LearningRepository(pool=pool_size_1)

    with patch.object(repo, "_fetch_student_analytics", side_effect=RuntimeError("Simulated Analytics Failure")):
        with pytest.raises(RuntimeError):
            await repo.get_student_progress(tenant_id=UUID(TENANT_A), student_id=UUID(STUDENT_A1))

    # El pool con tamaño 1 debe poder atender una consulta inmediatamente
    async with pool_size_1.acquire() as conn:
        val = await conn.fetchval("SELECT 42;")
        assert val == 42


# ============================================================================
# Comparación de Rendimiento (Benchmark de desacoplamiento y reducción de queries)
# ============================================================================

class CountingConnection:
    """Proxy around asyncpg.Connection to count query execution invocations."""

    def __init__(self, conn: asyncpg.Connection) -> None:
        self._conn = conn
        self.query_count = 0

    async def fetch(self, query: str, *args: Any, **kwargs: Any) -> Any:
        self.query_count += 1
        return await self._conn.fetch(query, *args, **kwargs)

    async def fetchrow(self, query: str, *args: Any, **kwargs: Any) -> Any:
        self.query_count += 1
        return await self._conn.fetchrow(query, *args, **kwargs)

    async def fetchval(self, query: str, *args: Any, **kwargs: Any) -> Any:
        self.query_count += 1
        return await self._conn.fetchval(query, *args, **kwargs)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._conn, name)


@pytest.mark.asyncio
async def test_07_performance_benchmark_decoupled_vs_legacy(pool_size_1: asyncpg.Pool) -> None:
    """Mide la reducción de consultas y latencia al evitar ejecutar el dashboard completo para Mi Progreso."""
    repo = LearningRepository(pool=pool_size_1)

    # 1. Verificación determinista de reducción de consultas a PostgreSQL
    async with pool_size_1.acquire() as raw_conn:
        # Flujo desacoplado: mide consultas ejecutadas por get_student_progress()
        c_decoupled = CountingConnection(raw_conn)
        await repo.get_student_progress(tenant_id=UUID(TENANT_A), student_id=UUID(STUDENT_A1), conn=c_decoupled)

        # Flujo legacy: simula el comportamiento previo exacto (get_student_dashboard + progreso)
        c_legacy = CountingConnection(raw_conn)
        await repo.get_student_dashboard(tenant_id=UUID(TENANT_A), student_id=UUID(STUDENT_A1), conn=c_legacy)
        # Consultas de evolución, desglose de KCs e historial de actividades del progreso
        await c_legacy.fetch(
            """
            SELECT to_char(qa.completed_at, 'DD Mon') AS date_label, qa.score, a.title AS activity_title
            FROM quiz_attempts qa
            JOIN activities a ON qa.activity_id = a.id
            JOIN enrollments e ON qa.enrollment_id = e.id
            WHERE e.student_id = $1 AND e.tenant_id = $2 AND qa.status = 'completed'
            ORDER BY qa.completed_at ASC LIMIT 20
            """,
            UUID(STUDENT_A1), UUID(TENANT_A)
        )
        await c_legacy.fetch(
            """
            SELECT kc.id AS kc_id, kc.name AS kc_name, u.title AS unit_title,
                   COUNT(ae.id)::int AS total_ans,
                   COUNT(ae.id) FILTER (WHERE ae.is_correct = true)::int AS correct_ans
            FROM knowledge_components kc
            JOIN units u ON kc.unit_id = u.id
            JOIN sections s ON u.course_id = s.course_id
            JOIN enrollments e ON s.id = e.section_id
            LEFT JOIN answer_events ae ON ae.knowledge_component_id = kc.id AND ae.student_id = $1 AND ae.tenant_id = $2
            WHERE e.student_id = $1 AND e.tenant_id = $2
            GROUP BY kc.id, kc.name, u.title
            """,
            UUID(STUDENT_A1), UUID(TENANT_A)
        )
        await c_legacy.fetch(
            """
            SELECT qa.id AS attempt_id, a.id AS activity_id, a.title AS activity_title,
                   c.name AS course_name, qa.completed_at, qa.score, qa.status::text AS status
            FROM quiz_attempts qa
            JOIN activities a ON qa.activity_id = a.id
            JOIN courses c ON a.course_id = c.id
            JOIN enrollments e ON qa.enrollment_id = e.id
            WHERE e.student_id = $1 AND e.tenant_id = $2 AND qa.status = 'completed'
            ORDER BY qa.completed_at DESC LIMIT 15
            """,
            UUID(STUDENT_A1), UUID(TENANT_A)
        )

    print(f"\n[QUERY COUNT] Legacy acoplado: {c_legacy.query_count} queries | Desacoplado: {c_decoupled.query_count} queries")
    assert c_decoupled.query_count == 4, (
        f"El flujo desacoplado con CTE debe ejecutar exactamente 4 consultas, pero ejecutó {c_decoupled.query_count}"
    )
    assert c_legacy.query_count >= 8, (
        f"El flujo legacy debe haber ejecutado al menos 8 consultas, pero ejecutó {c_legacy.query_count}"
    )
    assert c_decoupled.query_count < c_legacy.query_count

    # 2. Medición de latencia de ejecución
    # Calentamiento
    await repo.get_student_progress(tenant_id=UUID(TENANT_A), student_id=UUID(STUDENT_A1))

    times_decoupled = []
    for _ in range(15):
        t0 = time.perf_counter()
        await repo.get_student_progress(tenant_id=UUID(TENANT_A), student_id=UUID(STUDENT_A1))
        times_decoupled.append(time.perf_counter() - t0)

    avg_decoupled = sum(times_decoupled) / len(times_decoupled) * 1000
    print(f"[BENCHMARK] Latencia promedio get_student_progress(): {avg_decoupled:.2f} ms")
    assert avg_decoupled < 100.0, f"Latencia excesiva en progreso: {avg_decoupled:.2f} ms"


# ============================================================================
# Edge Cases & Robustness
# ============================================================================

@pytest.mark.asyncio
async def test_08_student_with_zero_enrollments_dashboard_and_progress_succeeds(pool_size_1: asyncpg.Pool) -> None:
    """Verifica que un estudiante sin matrículas ni actividades no arroje errores 500 en dashboard ni en progreso."""
    repo = LearningRepository(pool=pool_size_1)

    # 1. Dashboard
    dashboard = await repo.get_student_dashboard(
        tenant_id=UUID(TENANT_A),
        student_id=UUID(STUDENT_NO_ENR),
    )
    assert isinstance(dashboard, StudentDashboardResponse)
    assert dashboard.student_name == "Elena Sin Matricula"
    assert dashboard.student_code == "EST-NO-ENR"
    assert dashboard.enrolled_courses == []
    assert dashboard.upcoming_reviews == []
    assert dashboard.recent_activities == []
    assert dashboard.analytics.total_answers == 0
    assert dashboard.analytics.total_concepts_count == 0
    assert dashboard.analytics.completed_activities_count == 0
    assert dashboard.analytics.observed_accuracy_percentage == 0.0

    # 2. Progreso
    progress = await repo.get_student_progress(
        tenant_id=UUID(TENANT_A),
        student_id=UUID(STUDENT_NO_ENR),
    )
    assert isinstance(progress, StudentProgressDetailResponse)
    assert progress.analytics.total_answers == 0
    assert progress.analytics.total_concepts_count == 0
    assert progress.analytics.completed_activities_count == 0
    assert progress.evolution == []
    assert progress.kc_breakdown == []
    assert progress.activity_history == []


@pytest.mark.asyncio
async def test_09_student_with_enrollment_but_zero_attempts(pool_size_1: asyncpg.Pool) -> None:
    """Verifica estudiante matriculado pero sin intentos previos (cold start en KC breakdown)."""
    repo = LearningRepository(pool=pool_size_1)

    progress = await repo.get_student_progress(
        tenant_id=UUID(TENANT_A),
        student_id=UUID(STUDENT_A2),
    )
    assert isinstance(progress, StudentProgressDetailResponse)
    assert progress.analytics.total_answers == 0
    assert progress.analytics.completed_activities_count == 0
    assert progress.evolution == []
    assert progress.activity_history == []

    # Si hay KCs asignados a su curso, deben marcarse como cold start
    for kc in progress.kc_breakdown:
        assert kc.total_answers == 0
        assert kc.observed_accuracy == 0.0
        assert kc.status == "Sin evaluar"
        assert kc.is_cold_start is True


@pytest.mark.asyncio
async def test_10_progress_with_explicit_conn_zero_acquisitions(pool_size_1: asyncpg.Pool) -> None:
    """Demuestra que get_student_progress(conn=active_conn) realiza 0 adquisiciones del pool."""
    spy_pool = SpyPool(pool_size_1)
    repo = LearningRepository(pool=spy_pool)

    async with pool_size_1.acquire() as active_conn:
        progress = await repo.get_student_progress(
            tenant_id=UUID(TENANT_A),
            student_id=UUID(STUDENT_A1),
            conn=active_conn,
        )
        assert spy_pool.acquire_count == 0
        assert isinstance(progress, StudentProgressDetailResponse)


@pytest.mark.asyncio
async def test_11_dashboard_with_zero_enrollments_contract_fidelity(pool_size_1: asyncpg.Pool) -> None:
    """Verifica que los endpoints HTTP serialicen correctamente para un estudiante sin matrícula."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        headers = make_headers(STUDENT_NO_ENR, TENANT_A, "student")

        # Dashboard HTTP
        resp_dash = await client.get("/api/v1/students/me/dashboard", headers=headers)
        assert resp_dash.status_code == 200
        parsed_dash = StudentDashboardResponse.model_validate(resp_dash.json())
        assert parsed_dash.enrolled_courses == []

        # Progress HTTP
        resp_prog = await client.get("/api/v1/students/me/progress", headers=headers)
        assert resp_prog.status_code == 200
        parsed_prog = StudentProgressDetailResponse.model_validate(resp_prog.json())
        assert parsed_prog.evolution == []
        assert parsed_prog.activity_history == []
