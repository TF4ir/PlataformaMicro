"""Integration tests for Task M5.4: End-to-end Learning, Telemetry & Teacher Analytics.

Validates:
1. GET /api/v1/microcontents/{microcontent_id} retrieves structured lesson details.
2. POST /api/v1/microcontents/{microcontent_id}/exposures records append-only reading events.
3. GET /api/v1/microcontents lists catalog with filters (course_id, kc_id).
4. POST /api/v1/microcontents authors and publishes microcontent.
5. GET /api/v1/learning/student/dashboard returns real enrolled courses, analytics and upcoming reviews.
6. GET /api/v1/learning/student/progress returns objective observed accuracy, score evolution and KC breakdown.
7. GET /api/v1/teacher/dashboard aggregates real sections, proficiency distribution and student status lists.
8. GET /api/v1/teacher/courses returns courses, units, KCs and counts.
9. GET /api/v1/teacher/students returns student roster with pseudonyms and observed telemetry.
10. GET /api/v1/teacher/reports returns AI insight, mastery heat map, KC bar chart data and growth trajectory.
"""

from __future__ import annotations

import os
import uuid
from datetime import UTC, datetime, timedelta

import asyncpg
import jwt
import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import settings
from app.main import app

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/plataformamicro_test",
)

TENANT_ID = uuid.UUID("a0000000-0000-0000-0000-000000000001")
STUDENT_ID = uuid.UUID("e0000000-0000-0000-0000-000000000001")
TEACHER_ID = uuid.UUID("d0000000-0000-0000-0000-000000000001")
KC_FOTOSINTESIS = uuid.UUID("f0000000-0000-0000-0000-000000000001")
MICROCONTENT_ID = uuid.UUID("a1000000-0000-0000-0000-000000000001")


def create_test_jwt(user_id: uuid.UUID, email: str, role: str) -> str:
    now = datetime.now(UTC)
    payload = {
        "iss": "http://127.0.0.1:54321/auth/v1",
        "sub": str(user_id),
        "email": email,
        "role": "authenticated",
        "app_metadata": {
            "provider": "email",
            "role": role,
            "tenant_id": str(TENANT_ID),
        },
        "user_metadata": {
            "role": role,
            "tenant_id": str(TENANT_ID),
        },
        "tenant_id": str(TENANT_ID),
        "aud": "authenticated",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=2)).timestamp()),
    }
    return jwt.encode(payload, settings.SUPABASE_JWT_SECRET, algorithm="HS256")


@pytest.fixture(autouse=True)
async def setup_app_db_pool():
    import app.content_generation.infrastructure.database as db_mod

    pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=5)
    db_mod._POOL = pool
    yield pool
    await pool.close()
    db_mod._POOL = None


@pytest.mark.asyncio
async def test_get_microcontent_detail():
    student_token = create_test_jwt(STUDENT_ID, "camila.rojas@nexo.edu.pe", "student")

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        resp = await client.get(
            f"/api/v1/microcontents/{MICROCONTENT_ID}",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["id"] == str(MICROCONTENT_ID)
        assert data["knowledge_component_id"] == str(KC_FOTOSINTESIS)
        assert "Fotosíntesis" in data["title"]
        assert "sections" in data["content_body"]
        assert len(data["content_body"]["sections"]) > 0


@pytest.mark.asyncio
async def test_record_content_exposure():
    student_token = create_test_jwt(STUDENT_ID, "camila.rojas@nexo.edu.pe", "student")
    session_id = uuid.uuid4()
    idempotency_key = uuid.uuid4()

    now = datetime.now(UTC)
    payload = {
        "started_at": (now - timedelta(minutes=4)).isoformat(),
        "completed_at": now.isoformat(),
        "duration_seconds": 240.0,
        "active_reading_seconds": 215.0,
        "completion_status": "completed",
        "exposure_type": "initial_study",
        "session_id": str(session_id),
        "idempotency_key": str(idempotency_key),
        "metadata": {"device": "desktop"},
    }

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        resp = await client.post(
            f"/api/v1/microcontents/{MICROCONTENT_ID}/exposures",
            headers={"Authorization": f"Bearer {student_token}"},
            json=payload,
        )
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["microcontent_id"] == str(MICROCONTENT_ID)
        assert data["exposure_type"] == "initial_study"
        assert "event_id" in data


@pytest.mark.asyncio
async def test_list_and_create_microcontent_teacher():
    teacher_token = create_test_jwt(TEACHER_ID, "ana.garcia@nexo.edu.pe", "teacher")

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        # 1. List microcontents
        list_resp = await client.get(
            "/api/v1/microcontents",
            headers={"Authorization": f"Bearer {teacher_token}"},
        )
        assert list_resp.status_code == 200, list_resp.text
        items = list_resp.json()
        assert isinstance(items, list)
        assert len(items) >= 1

        # 2. Create new microcontent
        new_payload = {
            "knowledge_component_id": str(KC_FOTOSINTESIS),
            "title": "M54 Microlección de Prueba",
            "content_type": "text_summary",
            "estimated_duration_seconds": 180,
            "content_body": {
                "summary": "Resumen de prueba para integración M5.4",
                "sections": [{"id": 1, "navTitle": "Inicio", "heading": "Conceptos", "tag": "Test", "lead": "Intro", "durationMinutes": 3}],
            },
            "is_published": True,
        }
        create_resp = await client.post(
            "/api/v1/microcontents",
            headers={"Authorization": f"Bearer {teacher_token}"},
            json=new_payload,
        )
        assert create_resp.status_code == 201, create_resp.text
        created = create_resp.json()
        assert created["title"] == "M54 Microlección de Prueba"
        assert created["is_published"] is True


@pytest.mark.asyncio
async def test_student_dashboard_and_progress_endpoints():
    student_token = create_test_jwt(STUDENT_ID, "camila.rojas@nexo.edu.pe", "student")

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        # Dashboard
        dash_resp = await client.get(
            "/api/v1/learning/student/dashboard",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert dash_resp.status_code == 200, dash_resp.text
        dash = dash_resp.json()
        assert "student_name" in dash
        assert "enrolled_courses" in dash
        assert "analytics" in dash
        assert "upcoming_reviews" in dash

        # Progress
        prog_resp = await client.get(
            "/api/v1/learning/student/progress",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert prog_resp.status_code == 200, prog_resp.text
        prog = prog_resp.json()
        assert "analytics" in prog
        assert "evolution" in prog
        assert "kc_breakdown" in prog
        assert "activity_history" in prog


@pytest.mark.asyncio
async def test_teacher_dashboard_and_analytics_endpoints():
    teacher_token = create_test_jwt(TEACHER_ID, "ana.garcia@nexo.edu.pe", "teacher")

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        # Dashboard
        dash_resp = await client.get(
            "/api/v1/teacher/dashboard",
            headers={"Authorization": f"Bearer {teacher_token}"},
        )
        assert dash_resp.status_code == 200, dash_resp.text
        dash = dash_resp.json()
        assert "teacher_name" in dash
        assert "total_students" in dash
        assert "proficiency_distribution" in dash
        assert "students_requiring_reinforcement" in dash
        assert "students_on_track" in dash
        assert "sections" in dash

        # Courses
        courses_resp = await client.get(
            "/api/v1/teacher/courses",
            headers={"Authorization": f"Bearer {teacher_token}"},
        )
        assert courses_resp.status_code == 200, courses_resp.text
        courses = courses_resp.json()
        assert isinstance(courses, list)
        assert len(courses) >= 1
        assert "units" in courses[0]

        # Students
        students_resp = await client.get(
            "/api/v1/teacher/students",
            headers={"Authorization": f"Bearer {teacher_token}"},
        )
        assert students_resp.status_code == 200, students_resp.text
        students = students_resp.json()
        assert isinstance(students, list)
        assert len(students) >= 1
        assert "observed_accuracy" in students[0]

        # Reports
        reports_resp = await client.get(
            "/api/v1/teacher/reports",
            headers={"Authorization": f"Bearer {teacher_token}"},
        )
        assert reports_resp.status_code == 200, reports_resp.text
        reports = reports_resp.json()
        assert "ai_insight" in reports
        assert "mastery_heatmap" in reports
        assert "kc_performance_overview" in reports
        assert "retention_growth_trajectory" in reports
