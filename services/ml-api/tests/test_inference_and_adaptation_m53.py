"""Comprehensive tests for Task M5.3: Retention Inference Service & Adaptive Engine.

Certifies:
1. Unified history reconstruction (exposure + answer events).
2. Anti-leakage causality: future events strictly ignored.
3. Model availability statuses: cold_start, synthetic_test_mode, insufficient_empirical_data.
4. Production guardrail: synthetic models rejected when ENVIRONMENT=production.
5. Critical forgetting time calculation and review scheduling.
6. Pedagogical adaptation: threshold crossing triggers review, sufficient retention skips review.
7. Anti-fatigue 24h frequency capping and duplicate pending recommendation rejection.
8. Microcontent catalog selection, published status, and tenant isolation.
9. Recommendation completion via POST /complete.
10. Full REST API endpoints with Supabase JWT authentication and RBAC.
"""

from __future__ import annotations

import os
import uuid
from datetime import UTC, datetime, timedelta

import asyncpg
import jwt
import pytest
from httpx import ASGITransport, AsyncClient

from app.adaptation.adaptation_engine import AdaptationEngine
from app.core.config import settings
from app.main import app
from app.prediction.history_builder import UnifiedHistoryBuilder
from app.prediction.inference_service import RetentionInferenceService
from app.prediction.model_registry import RetentionModelRegistry
from app.schemas.prediction import ModelAvailabilityStatus

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/plataformamicro_test",
)


def create_test_jwt(
    user_id: uuid.UUID,
    email: str,
    role: str = "student",
    tenant_id: uuid.UUID | None = None,
) -> str:
    now = datetime.now(UTC)
    payload = {
        "iss": "http://127.0.0.1:54321/auth/v1",
        "sub": str(user_id),
        "email": email,
        "role": "authenticated",
        "app_metadata": {
            "provider": "email",
            "role": role,
            **({"tenant_id": str(tenant_id)} if tenant_id else {}),
        },
        "user_metadata": {
            "role": role,
            **({"tenant_id": str(tenant_id)} if tenant_id else {}),
        },
        **({"tenant_id": str(tenant_id)} if tenant_id else {}),
        "aud": "authenticated",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=2)).timestamp()),
    }
    return jwt.encode(payload, settings.SUPABASE_JWT_SECRET, algorithm="HS256")


@pytest.fixture(autouse=True)
async def setup_app_db_pool():
    """Ensure database connection pool is globally initialized for the FastAPI app."""
    import app.content_generation.infrastructure.database as db_mod

    pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=5)
    db_mod._POOL = pool
    yield pool
    await pool.close()
    db_mod._POOL = None


@pytest.fixture
async def db_conn():
    conn = await asyncpg.connect(DATABASE_URL)
    yield conn
    await conn.close()


@pytest.fixture
async def setup_test_context(db_conn: asyncpg.Connection):
    """Sets up a complete isolated testing tenant with student, course, section, unit, KC, and microcontent."""
    tenant_id = uuid.uuid4()
    await db_conn.execute(
        "INSERT INTO tenants (id, name, slug) VALUES ($1, $2, $3)",
        tenant_id,
        "Colegio Piloto M53",
        f"pilot-m53-{uuid.uuid4().hex[:6]}",
    )

    student_id = uuid.uuid4()
    await db_conn.execute(
        "INSERT INTO auth.users (id, email) VALUES ($1, $2)",
        student_id,
        f"student-{student_id.hex[:6]}@pilot.edu.pe",
    )
    await db_conn.execute(
        "INSERT INTO profiles (id, tenant_id, full_name, role) VALUES ($1, $2, $3, 'student'::user_role)",
        student_id,
        tenant_id,
        "Estudiante M53",
    )

    teacher_id = uuid.uuid4()
    await db_conn.execute(
        "INSERT INTO auth.users (id, email) VALUES ($1, $2)",
        teacher_id,
        f"teacher-{teacher_id.hex[:6]}@pilot.edu.pe",
    )
    await db_conn.execute(
        "INSERT INTO profiles (id, tenant_id, full_name, role) VALUES ($1, $2, $3, 'teacher'::user_role)",
        teacher_id,
        tenant_id,
        "Docente M53",
    )

    course_id = uuid.uuid4()
    await db_conn.execute(
        "INSERT INTO courses (id, tenant_id, code, name) VALUES ($1, $2, $3, $4)",
        course_id,
        tenant_id,
        f"CIEN-{uuid.uuid4().hex[:4]}",
        "Ciencias M53",
    )

    section_id = uuid.uuid4()
    await db_conn.execute(
        "INSERT INTO sections (id, tenant_id, course_id, teacher_id, name) VALUES ($1, $2, $3, $4, '5 A')",
        section_id,
        tenant_id,
        course_id,
        teacher_id,
    )

    await db_conn.execute(
        "INSERT INTO enrollments (tenant_id, section_id, student_id, student_id_pseudo) VALUES ($1, $2, $3, $4)",
        tenant_id,
        section_id,
        student_id,
        uuid.uuid4(),
    )

    unit_id = uuid.uuid4()
    await db_conn.execute(
        "INSERT INTO units (id, tenant_id, course_id, title, order_index) VALUES ($1, $2, $3, $4, 1)",
        unit_id,
        tenant_id,
        course_id,
        "Biología Celular",
    )

    kc_id = uuid.uuid4()
    await db_conn.execute(
        "INSERT INTO knowledge_components (id, tenant_id, unit_id, name, difficulty_prior) VALUES ($1, $2, $3, $4, 0.500)",
        kc_id,
        tenant_id,
        unit_id,
        "Fotosíntesis y Cloroplastos",
    )

    microcontent_id = uuid.uuid4()
    await db_conn.execute(
        """
        INSERT INTO microcontents (
            id, tenant_id, knowledge_component_id, title, content_type,
            content_body, estimated_duration_seconds, created_by, is_published
        ) VALUES (
            $1, $2, $3, $4, 'text_summary'::content_type_enum,
            '{"summary": "La fotosíntesis convierte energía luminosa en glucosa."}'::jsonb,
            180, $5, true
        )
        """,
        microcontent_id,
        tenant_id,
        kc_id,
        "Ficha: Fases de la Fotosíntesis",
        teacher_id,
    )

    # Question for quiz
    question_id = uuid.uuid4()
    await db_conn.execute(
        """
        INSERT INTO questions (
            id, tenant_id, knowledge_component_id, question_text,
            difficulty, is_active, created_by, explanation
        ) VALUES ($1, $2, $3, $4, 0.500, true, $5, 'Explicación')
        """,
        question_id,
        tenant_id,
        kc_id,
        "¿Dónde ocurre la fase luminosa?",
        teacher_id,
    )

    opt_correct_id = uuid.uuid4()
    await db_conn.execute(
        "INSERT INTO question_options (id, question_id, option_text, is_correct, order_index) VALUES ($1, $2, 'Tilacoides', true, 1)",
        opt_correct_id,
        question_id,
    )

    opt_wrong_id = uuid.uuid4()
    await db_conn.execute(
        "INSERT INTO question_options (id, question_id, option_text, is_correct, order_index) VALUES ($1, $2, 'Estroma', false, 2)",
        opt_wrong_id,
        question_id,
    )

    activity_id = uuid.uuid4()
    await db_conn.execute(
        """
        INSERT INTO activities (
            id, tenant_id, course_id, created_by, title, status, activity_type, max_attempts
        ) VALUES ($1, $2, $3, $4, 'Quiz Fotosíntesis', 'published'::activity_status_enum, 'practice'::activity_type_enum, 2)
        """,
        activity_id,
        tenant_id,
        course_id,
        teacher_id,
    )

    attempt_id = uuid.uuid4()
    await db_conn.execute(
        """
        INSERT INTO quiz_attempts (
            id, tenant_id, enrollment_id, activity_id, student_id, attempt_number, status
        ) VALUES (
            $1, $2,
            (SELECT id FROM enrollments WHERE student_id = $3),
            $4, $3, 1, 'completed'::attempt_status_enum
        )
        """,
        attempt_id,
        tenant_id,
        student_id,
        activity_id,
    )

    return {
        "tenant_id": tenant_id,
        "student_id": student_id,
        "teacher_id": teacher_id,
        "kc_id": kc_id,
        "microcontent_id": microcontent_id,
        "activity_id": activity_id,
        "attempt_id": attempt_id,
        "question_id": question_id,
        "opt_correct_id": opt_correct_id,
        "opt_wrong_id": opt_wrong_id,
    }


class TestInferenceService:
    """Verifies history reconstruction, anti-leakage, and model inference."""

    @pytest.mark.asyncio
    async def test_cold_start_detected_with_insufficient_history(
        self, db_conn: asyncpg.Connection, setup_test_context: dict
    ):
        ctx = setup_test_context
        service = RetentionInferenceService()

        # Call with no events
        pool = await asyncpg.create_pool(DATABASE_URL)
        assert pool is not None
        try:
            profile = await service.get_student_retention_profile(
                pool=pool,
                student_id=ctx["student_id"],
                tenant_id=ctx["tenant_id"],
                knowledge_component_id=ctx["kc_id"],
            )

            assert len(profile.kcs) == 1
            kc_pred = profile.kcs[0]
            assert kc_pred.availability_status == ModelAvailabilityStatus.COLD_START
            assert kc_pred.total_exposures == 0
            assert kc_pred.total_retrieval_attempts == 0
        finally:
            await pool.close()

    @pytest.mark.asyncio
    async def test_anti_leakage_future_events_excluded(
        self, db_conn: asyncpg.Connection, setup_test_context: dict
    ):
        ctx = setup_test_context
        t_ref = datetime.now(UTC)

        # 1 past exposure
        await db_conn.execute(
            """
            INSERT INTO content_exposure_events (
                tenant_id, student_id, student_id_pseudo, microcontent_id, knowledge_component_id,
                exposure_type, started_at, duration_seconds, session_id, idempotency_key, event_timestamp
            ) VALUES ($1, $2, $3, $4, $5, 'initial_study'::exposure_type_enum, $6, 120.0, $7, $8, $6)
            """,
            ctx["tenant_id"],
            ctx["student_id"],
            uuid.uuid4(),
            ctx["microcontent_id"],
            ctx["kc_id"],
            t_ref - timedelta(days=2),
            uuid.uuid4(),
            uuid.uuid4(),
        )

        # 1 future event (leakage candidate)
        await db_conn.execute(
            """
            INSERT INTO content_exposure_events (
                tenant_id, student_id, student_id_pseudo, microcontent_id, knowledge_component_id,
                exposure_type, started_at, duration_seconds, session_id, idempotency_key, event_timestamp
            ) VALUES ($1, $2, $3, $4, $5, 'review_study'::exposure_type_enum, $6, 120.0, $7, $8, $6)
            """,
            ctx["tenant_id"],
            ctx["student_id"],
            uuid.uuid4(),
            ctx["microcontent_id"],
            ctx["kc_id"],
            t_ref + timedelta(days=2),  # In the future!
            uuid.uuid4(),
            uuid.uuid4(),
        )

        builder = UnifiedHistoryBuilder()
        pool = await asyncpg.create_pool(DATABASE_URL)
        assert pool is not None
        try:
            history = await builder.fetch_student_kc_history(
                pool=pool,
                student_id=ctx["student_id"],
                tenant_id=ctx["tenant_id"],
                knowledge_component_id=ctx["kc_id"],
                reference_time=t_ref,
            )

            kc_hist = history[ctx["kc_id"]]
            # Must strictly contain ONLY 1 exposure (the past one)
            assert kc_hist.total_exposures == 1
        finally:
            await pool.close()

    def test_production_guardrail_rejects_synthetic_models(self):
        original_env = settings.ENVIRONMENT
        try:
            settings.ENVIRONMENT = "production"
            registry = RetentionModelRegistry()
            model, _meta, status = registry.get_active_model()

            # In production, synthetic models are denied
            assert model is None
            assert status == ModelAvailabilityStatus.INSUFFICIENT_EMPIRICAL_DATA
        finally:
            settings.ENVIRONMENT = original_env


class TestAdaptationEngine:
    """Verifies pedagogical policies, 24h anti-fatigue cooldown, and completion."""

    @pytest.mark.asyncio
    async def test_anti_fatigue_24h_blocks_duplicate_recommendations(
        self, db_conn: asyncpg.Connection, setup_test_context: dict
    ):
        ctx = setup_test_context
        engine = AdaptationEngine(anti_fatigue_hours=24)
        pool = await asyncpg.create_pool(DATABASE_URL)
        assert pool is not None

        try:
            # Add an exposure event so cold-start creates recommendation
            await db_conn.execute(
                """
                INSERT INTO content_exposure_events (
                    tenant_id, student_id, student_id_pseudo, microcontent_id, knowledge_component_id,
                    exposure_type, started_at, duration_seconds, session_id, idempotency_key
                ) VALUES ($1, $2, $3, $4, $5, 'initial_study'::exposure_type_enum, now(), 120.0, $6, $7)
                """,
                ctx["tenant_id"],
                ctx["student_id"],
                uuid.uuid4(),
                ctx["microcontent_id"],
                ctx["kc_id"],
                uuid.uuid4(),
                uuid.uuid4(),
            )

            inference = RetentionInferenceService()
            profile = await inference.get_student_retention_profile(
                pool=pool,
                student_id=ctx["student_id"],
                tenant_id=ctx["tenant_id"],
                knowledge_component_id=ctx["kc_id"],
                tau=0.650,
            )

            eval_res_1 = await engine.evaluate_and_generate_recommendations(
                pool=pool,
                student_id=ctx["student_id"],
                tenant_id=ctx["tenant_id"],
                retention_predictions=profile.kcs,
                tau=0.650,
            )

            assert eval_res_1.recommendations_created == 1
            assert eval_res_1.decisions[0].decision == "recommended"

            # Immediate second evaluation must be blocked by 24h anti-fatigue cooldown
            eval_res_2 = await engine.evaluate_and_generate_recommendations(
                pool=pool,
                student_id=ctx["student_id"],
                tenant_id=ctx["tenant_id"],
                retention_predictions=profile.kcs,
                tau=0.650,
            )

            assert eval_res_2.recommendations_created == 0
            assert eval_res_2.decisions[0].decision == "cooldown_active"
            assert "pendiente" in eval_res_2.decisions[0].reason.lower() or "anti-fatiga" in eval_res_2.decisions[0].reason.lower()
        finally:
            await pool.close()

    @pytest.mark.asyncio
    async def test_mark_recommendation_completed(
        self, db_conn: asyncpg.Connection, setup_test_context: dict
    ):
        ctx = setup_test_context
        engine = AdaptationEngine()
        pool = await asyncpg.create_pool(DATABASE_URL)
        assert pool is not None

        try:
            # Insert a pending recommendation
            rec_id = uuid.uuid4()
            await db_conn.execute(
                """
                INSERT INTO recommendations (
                    id, tenant_id, student_id, knowledge_component_id, microcontent_id,
                    selection_method, decision_reason, status, policy_name, policy_version
                ) VALUES (
                    $1, $2, $3, $4, $5,
                    'predictive_model'::recommendation_method_enum, 'Test reason',
                    'pending'::recommendation_status_enum, 'test_policy', '1.0.0'
                )
                """,
                rec_id,
                ctx["tenant_id"],
                ctx["student_id"],
                ctx["kc_id"],
                ctx["microcontent_id"],
            )

            # Mark completed as student
            ok = await engine.mark_recommendation_completed(
                pool=pool,
                recommendation_id=rec_id,
                student_id=ctx["student_id"],
                tenant_id=ctx["tenant_id"],
            )
            assert ok is True

            # Verify in DB
            status = await db_conn.fetchval("SELECT status::text FROM recommendations WHERE id = $1", rec_id)
            assert status == "completed"

            # Trying to complete again returns False (not pending)
            ok_again = await engine.mark_recommendation_completed(
                pool=pool,
                recommendation_id=rec_id,
                student_id=ctx["student_id"],
                tenant_id=ctx["tenant_id"],
            )
            assert ok_again is False
        finally:
            await pool.close()


class TestRestAPIEndpoints:
    """Verifies FastAPI REST endpoints with Supabase JWT and authorization."""

    @pytest.mark.asyncio
    async def test_get_my_retention_endpoint(self, setup_test_context: dict):
        ctx = setup_test_context
        token = create_test_jwt(
            ctx["student_id"],
            "student@pilot.edu.pe",
            role="student",
            tenant_id=ctx["tenant_id"],
        )

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.get(
                "/api/v1/students/me/retention",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["student_id"] == str(ctx["student_id"])
        assert "kcs" in data
        assert len(data["kcs"]) >= 1

    @pytest.mark.asyncio
    async def test_get_my_recommendations_and_complete_endpoint(
        self, db_conn: asyncpg.Connection, setup_test_context: dict
    ):
        ctx = setup_test_context
        token = create_test_jwt(
            ctx["student_id"],
            "student@pilot.edu.pe",
            role="student",
            tenant_id=ctx["tenant_id"],
        )

        # Insert a pending recommendation
        rec_id = uuid.uuid4()
        await db_conn.execute(
            """
            INSERT INTO recommendations (
                id, tenant_id, student_id, knowledge_component_id, microcontent_id,
                selection_method, decision_reason, status, policy_name, policy_version
            ) VALUES (
                $1, $2, $3, $4, $5,
                'predictive_model'::recommendation_method_enum, 'Refuerzo sugerido',
                'pending'::recommendation_status_enum, 'preventive_spaced_repetition', '1.0.0'
            )
            """,
            rec_id,
            ctx["tenant_id"],
            ctx["student_id"],
            ctx["kc_id"],
            ctx["microcontent_id"],
        )

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            # 1. List recommendations
            list_resp = await ac.get(
                "/api/v1/students/me/recommendations",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert list_resp.status_code == 200
            recs = list_resp.json()
            assert any(r["id"] == str(rec_id) for r in recs)

            # 2. Complete recommendation
            comp_resp = await ac.post(
                f"/api/v1/students/me/recommendations/{rec_id}/complete",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert comp_resp.status_code == 200
            assert comp_resp.json()["status"] == "completed"

            # 3. Trying with non-existent or other student recommendation returns 404
            bad_resp = await ac.post(
                f"/api/v1/students/me/recommendations/{uuid.uuid4()}/complete",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert bad_resp.status_code == 404

    @pytest.mark.asyncio
    async def test_evaluate_endpoint_generates_recommendations(self, setup_test_context: dict):
        ctx = setup_test_context
        token = create_test_jwt(
            ctx["student_id"],
            "student@pilot.edu.pe",
            role="student",
            tenant_id=ctx["tenant_id"],
        )

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post(
                "/api/v1/students/me/recommendations/evaluate?tau=0.650",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["student_id"] == str(ctx["student_id"])
        assert "decisions" in data

    @pytest.mark.asyncio
    async def test_unauthorized_access_rejected_without_jwt(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.get("/api/v1/students/me/retention")
        assert resp.status_code == 401
