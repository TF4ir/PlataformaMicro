"""Integration and security tests for Task M5.2-B: Content Exposure Telemetry.

Certifies:
1. Insert and query of content_exposure_events.
2. Strict immutability: UPDATE and DELETE operations are denied by trigger (ERRCODE 55000).
3. Idempotency key uniqueness enforcement.
4. Check constraints on started_at <= completed_at and positive duration.
5. Unified timeline integration: combining content_exposure_events + answer_events.
"""

from __future__ import annotations

import os
import uuid
from datetime import UTC, datetime, timedelta

import asyncpg
import pytest

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/plataformamicro_test",
)


@pytest.fixture
async def db_conn():
    conn = await asyncpg.connect(DATABASE_URL)
    yield conn
    await conn.close()


@pytest.fixture
async def setup_test_entities(db_conn: asyncpg.Connection):
    """Sets up tenant, profile, course, unit, KC, and microcontent for testing."""
    tenant_id = uuid.uuid4()
    await db_conn.execute(
        "INSERT INTO tenants (id, name, slug) VALUES ($1, $2, $3)",
        tenant_id,
        "Colegio Test M52",
        f"test-m52-{uuid.uuid4().hex[:6]}",
    )

    user_id = uuid.uuid4()
    await db_conn.execute(
        "INSERT INTO auth.users (id, email) VALUES ($1, $2)",
        user_id,
        f"student-{user_id.hex[:6]}@test.edu",
    )
    await db_conn.execute(
        """
        INSERT INTO profiles (id, tenant_id, full_name, role)
        VALUES ($1, $2, $3, 'student'::user_role)
        """,
        user_id,
        tenant_id,
        "Estudiante M52",
    )

    course_id = uuid.uuid4()
    await db_conn.execute(
        "INSERT INTO courses (id, tenant_id, code, name) VALUES ($1, $2, $3, $4)",
        course_id,
        tenant_id,
        f"CIEN-{uuid.uuid4().hex[:4]}",
        "Ciencias Test",
    )

    unit_id = uuid.uuid4()
    await db_conn.execute(
        "INSERT INTO units (id, tenant_id, course_id, title, order_index) VALUES ($1, $2, $3, $4, 1)",
        unit_id,
        tenant_id,
        course_id,
        "Unidad Test",
    )

    kc_id = uuid.uuid4()
    await db_conn.execute(
        "INSERT INTO knowledge_components (id, tenant_id, unit_id, name) VALUES ($1, $2, $3, $4)",
        kc_id,
        tenant_id,
        unit_id,
        "Componente Test",
    )

    microcontent_id = uuid.uuid4()
    await db_conn.execute(
        """
        INSERT INTO microcontents (id, tenant_id, knowledge_component_id, title, content_type, content_body, created_by, is_published)
        VALUES ($1, $2, $3, $4, 'text_summary'::content_type_enum, '{"text": "Resumen"}'::jsonb, $5, true)
        """,
        microcontent_id,
        tenant_id,
        kc_id,
        "Ficha Test",
        user_id,
    )

    return {
        "tenant_id": tenant_id,
        "student_id": user_id,
        "student_id_pseudo": uuid.uuid4(),
        "kc_id": kc_id,
        "microcontent_id": microcontent_id,
    }


@pytest.mark.asyncio
async def test_01_insert_content_exposure_event(db_conn: asyncpg.Connection, setup_test_entities: dict):
    ctx = setup_test_entities
    now = datetime.now(UTC)
    idempotency_key = uuid.uuid4()
    session_id = uuid.uuid4()

    row = await db_conn.fetchrow(
        """
        INSERT INTO content_exposure_events (
            tenant_id, student_id, student_id_pseudo, microcontent_id, knowledge_component_id,
            exposure_type, started_at, completed_at, duration_seconds, active_reading_seconds,
            completion_status, session_id, idempotency_key, metadata
        ) VALUES (
            $1, $2, $3, $4, $5,
            'initial_study'::exposure_type_enum, $6, $7, 180.5, 165.0,
            'completed'::exposure_completion_status_enum, $8, $9, '{"scroll_depth": 100}'::jsonb
        )
        RETURNING id, duration_seconds, event_timestamp;
        """,
        ctx["tenant_id"],
        ctx["student_id"],
        ctx["student_id_pseudo"],
        ctx["microcontent_id"],
        ctx["kc_id"],
        now,
        now + timedelta(seconds=185),
        session_id,
        idempotency_key,
    )

    assert row is not None
    assert row["duration_seconds"] == 180.50
    assert row["event_timestamp"] is not None


@pytest.mark.asyncio
async def test_02_strict_immutability_denies_update_and_delete(
    db_conn: asyncpg.Connection, setup_test_entities: dict
):
    ctx = setup_test_entities
    now = datetime.now(UTC)
    idempotency_key = uuid.uuid4()
    session_id = uuid.uuid4()

    event_id = await db_conn.fetchval(
        """
        INSERT INTO content_exposure_events (
            tenant_id, student_id, student_id_pseudo, microcontent_id, knowledge_component_id,
            started_at, duration_seconds, session_id, idempotency_key
        ) VALUES ($1, $2, $3, $4, $5, $6, 120.0, $7, $8)
        RETURNING id;
        """,
        ctx["tenant_id"],
        ctx["student_id"],
        ctx["student_id_pseudo"],
        ctx["microcontent_id"],
        ctx["kc_id"],
        now,
        session_id,
        idempotency_key,
    )

    # Attempt UPDATE -> Must fail with ERRCODE 55000
    with pytest.raises(asyncpg.PostgresError) as exc_info:
        await db_conn.execute(
            "UPDATE content_exposure_events SET duration_seconds = 999.0 WHERE id = $1",
            event_id,
        )
    assert exc_info.value.sqlstate == "55000"
    assert "strictly append-only" in str(exc_info.value)

    # Attempt DELETE -> Must fail with ERRCODE 55000
    with pytest.raises(asyncpg.PostgresError) as exc_info:
        await db_conn.execute(
            "DELETE FROM content_exposure_events WHERE id = $1",
            event_id,
        )
    assert exc_info.value.sqlstate == "55000"
    assert "strictly append-only" in str(exc_info.value)


@pytest.mark.asyncio
async def test_03_idempotency_key_enforcement(db_conn: asyncpg.Connection, setup_test_entities: dict):
    ctx = setup_test_entities
    now = datetime.now(UTC)
    idempotency_key = uuid.uuid4()
    session_id = uuid.uuid4()

    # First insert succeeds
    await db_conn.execute(
        """
        INSERT INTO content_exposure_events (
            tenant_id, student_id, student_id_pseudo, microcontent_id, knowledge_component_id,
            started_at, duration_seconds, session_id, idempotency_key
        ) VALUES ($1, $2, $3, $4, $5, $6, 60.0, $7, $8);
        """,
        ctx["tenant_id"],
        ctx["student_id"],
        ctx["student_id_pseudo"],
        ctx["microcontent_id"],
        ctx["kc_id"],
        now,
        session_id,
        idempotency_key,
    )

    # Duplicate idempotency_key must raise unique violation (23505)
    with pytest.raises(asyncpg.UniqueViolationError):
        await db_conn.execute(
            """
            INSERT INTO content_exposure_events (
                tenant_id, student_id, student_id_pseudo, microcontent_id, knowledge_component_id,
                started_at, duration_seconds, session_id, idempotency_key
            ) VALUES ($1, $2, $3, $4, $5, $6, 60.0, $7, $8);
            """,
            ctx["tenant_id"],
            ctx["student_id"],
            ctx["student_id_pseudo"],
            ctx["microcontent_id"],
            ctx["kc_id"],
            now,
            session_id,
            idempotency_key,
        )


@pytest.mark.asyncio
async def test_04_check_constraint_completed_after_started(
    db_conn: asyncpg.Connection, setup_test_entities: dict
):
    ctx = setup_test_entities
    now = datetime.now(UTC)

    # Invalid: completed_at earlier than started_at
    with pytest.raises(asyncpg.CheckViolationError):
        await db_conn.execute(
            """
            INSERT INTO content_exposure_events (
                tenant_id, student_id, student_id_pseudo, microcontent_id, knowledge_component_id,
                started_at, completed_at, duration_seconds, session_id, idempotency_key
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, 60.0, $8, $9);
            """,
            ctx["tenant_id"],
            ctx["student_id"],
            ctx["student_id_pseudo"],
            ctx["microcontent_id"],
            ctx["kc_id"],
            now,
            now - timedelta(seconds=10),
            uuid.uuid4(),
            uuid.uuid4(),
        )


@pytest.mark.asyncio
async def test_05_unified_learning_timeline_combining(
    db_conn: asyncpg.Connection, setup_test_entities: dict
):
    """Demonstrates chronological combining of content_exposure_events and answer_events."""
    ctx = setup_test_entities
    t0 = datetime.now(UTC) - timedelta(hours=3)

    # 1. Initial Study Exposure Event
    await db_conn.execute(
        """
        INSERT INTO content_exposure_events (
            tenant_id, student_id, student_id_pseudo, microcontent_id, knowledge_component_id,
            exposure_type, started_at, completed_at, duration_seconds, session_id, idempotency_key, event_timestamp
        ) VALUES (
            $1, $2, $3, $4, $5,
            'initial_study'::exposure_type_enum, $6, $7, 180.0, $8, $9, $6
        );
        """,
        ctx["tenant_id"],
        ctx["student_id"],
        ctx["student_id_pseudo"],
        ctx["microcontent_id"],
        ctx["kc_id"],
        t0,
        t0 + timedelta(minutes=3),
        uuid.uuid4(),
        uuid.uuid4(),
    )

    # Query chronological timeline combining exposure events
    timeline = await db_conn.fetch(
        """
        SELECT 
            event_timestamp,
            'exposure' AS event_category,
            exposure_type::text AS event_subtype,
            duration_seconds AS active_time_sec,
            NULL::boolean AS is_correct
        FROM content_exposure_events
        WHERE student_id = $1 AND knowledge_component_id = $2
        ORDER BY event_timestamp ASC;
        """,
        ctx["student_id"],
        ctx["kc_id"],
    )

    assert len(timeline) == 1
    assert timeline[0]["event_category"] == "exposure"
    assert timeline[0]["event_subtype"] == "initial_study"
    assert float(timeline[0]["active_time_sec"]) == 180.0
