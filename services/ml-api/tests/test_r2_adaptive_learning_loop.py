"""End-to-End Integration Tests for R2: Closed-Loop Adaptive Microlearning & Assessment Integrity.

Validates the full cycle:
1. Student access to authorized, published activity with questions sanitized.
2. Attempt start with idempotency key.
3. Server-side answer evaluation and append-only answer_events persistence.
4. Attempt completion triggering:
   - Score calculation on server.
   - Predictive retention state update (predictions & student_knowledge_states tables).
   - Adaptive recommendation scheduling (recommendations table).
5. Student dashboard (/dashboard) reflecting the new personalized upcoming reviews.
6. Student recommendations endpoint (/recommendations) retrieving the persisted plan.
7. Query idempotency: reloading dashboard/recommendations does not duplicate recommendations.
8. Microcontent exposure completion: reading microcontent marks recommendation as completed.
9. Student isolation: another student in another section cannot access or manipulate attempts/recommendations.
"""

from __future__ import annotations

import asyncio
import os
import uuid
from datetime import UTC, datetime, timedelta

import asyncpg
import httpx
import jwt
import pytest

from app.core.config import settings
from app.main import app

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/plataformamicro_test",
)


def create_student_token(student_id: uuid.UUID, tenant_id: uuid.UUID) -> str:
    now = datetime.now(UTC)
    payload = {
        "iss": "http://127.0.0.1:54321/auth/v1",
        "sub": str(student_id),
        "email": f"student-{student_id.hex[:6]}@pilot.edu.pe",
        "role": "authenticated",
        "app_metadata": {
            "provider": "email",
            "role": "student",
            "tenant_id": str(tenant_id),
        },
        "user_metadata": {
            "role": "student",
            "tenant_id": str(tenant_id),
        },
        "aud": "authenticated",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=2)).timestamp()),
    }
    return jwt.encode(payload, settings.SUPABASE_JWT_SECRET, algorithm="HS256")


@pytest.fixture(autouse=True)
async def setup_app_db_pool():
    """Ensure database connection pool is globally initialized for FastAPI."""
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
async def r2_test_environment(db_conn: asyncpg.Connection):
    """Sets up a complete isolated learning environment for R2 testing."""
    tenant_id = uuid.uuid4()
    await db_conn.execute(
        "INSERT INTO tenants (id, name, slug) VALUES ($1, $2, $3)",
        tenant_id,
        "Colegio Piloto R2",
        f"pilot-r2-{uuid.uuid4().hex[:6]}",
    )

    # Teacher
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
        "Profesor de Ciencias R2",
    )

    # Student 1 (Enrolled in Section 1)
    student1_id = uuid.uuid4()
    await db_conn.execute(
        "INSERT INTO auth.users (id, email) VALUES ($1, $2)",
        student1_id,
        f"student1-{student1_id.hex[:6]}@pilot.edu.pe",
    )
    await db_conn.execute(
        "INSERT INTO profiles (id, tenant_id, full_name, role, student_code) VALUES ($1, $2, $3, 'student'::user_role, $4)",
        student1_id,
        tenant_id,
        "Estudiante Uno R2",
        f"EST-R2-{uuid.uuid4().hex[:6]}",
    )

    # Student 2 (Enrolled in Section 2 - for isolation tests)
    student2_id = uuid.uuid4()
    await db_conn.execute(
        "INSERT INTO auth.users (id, email) VALUES ($1, $2)",
        student2_id,
        f"student2-{student2_id.hex[:6]}@pilot.edu.pe",
    )
    await db_conn.execute(
        "INSERT INTO profiles (id, tenant_id, full_name, role, student_code) VALUES ($1, $2, $3, 'student'::user_role, $4)",
        student2_id,
        tenant_id,
        "Estudiante Dos R2",
        f"EST-R2-{uuid.uuid4().hex[:6]}",
    )

    # Course, Sections, Unit, KC
    course_id = uuid.uuid4()
    await db_conn.execute(
        "INSERT INTO courses (id, tenant_id, code, name, description, is_active) VALUES ($1, $2, $3, $4, $5, true)",
        course_id,
        tenant_id,
        "BIO-501",
        "Biología Celular",
        "Curso de 5to de Secundaria",
    )

    section1_id = uuid.uuid4()
    await db_conn.execute(
        "INSERT INTO sections (id, tenant_id, course_id, teacher_id, name) VALUES ($1, $2, $3, $4, '5to A')",
        section1_id,
        tenant_id,
        course_id,
        teacher_id,
    )

    section2_id = uuid.uuid4()
    await db_conn.execute(
        "INSERT INTO sections (id, tenant_id, course_id, teacher_id, name) VALUES ($1, $2, $3, $4, '5to B')",
        section2_id,
        tenant_id,
        course_id,
        teacher_id,
    )

    # Enrollments
    enr1_id = uuid.uuid4()
    await db_conn.execute(
        "INSERT INTO enrollments (id, tenant_id, student_id, section_id, student_id_pseudo) VALUES ($1, $2, $3, $4, $5)",
        enr1_id,
        tenant_id,
        student1_id,
        section1_id,
        uuid.uuid4(),
    )

    enr2_id = uuid.uuid4()
    await db_conn.execute(
        "INSERT INTO enrollments (id, tenant_id, student_id, section_id, student_id_pseudo) VALUES ($1, $2, $3, $4, $5)",
        enr2_id,
        tenant_id,
        student2_id,
        section2_id,
        uuid.uuid4(),
    )

    unit_id = uuid.uuid4()
    await db_conn.execute(
        "INSERT INTO units (id, tenant_id, course_id, title, order_index) VALUES ($1, $2, $3, 'Metabolismo Celular', 1)",
        unit_id,
        tenant_id,
        course_id,
    )

    kc_id = uuid.uuid4()
    await db_conn.execute(
        "INSERT INTO knowledge_components (id, tenant_id, unit_id, name, description, difficulty_prior) VALUES ($1, $2, $3, $4, $5, 0.450)",
        kc_id,
        tenant_id,
        unit_id,
        "Fase Luminosa y Transporte de Electrones",
        "Reacciones dependientes de la luz en la membrana tilacoidal",
    )

    # Published Microcontent for this KC
    microcontent_id = uuid.uuid4()
    content_body = {
        "summary": "Resumen de la fase luminosa",
        "sections": [
            {"id": 1, "navTitle": "Conceptos", "heading": "Tilacoides", "lead": "Fotólisis del agua", "durationMinutes": 3}
        ],
    }
    import json
    await db_conn.execute(
        """
        INSERT INTO microcontents (
            id, tenant_id, knowledge_component_id, title,
            content_type, content_body, is_published, estimated_duration_seconds, created_by
        ) VALUES ($1, $2, $3, $4, 'text_summary'::content_type_enum, $5::jsonb, true, 180, $6)
        """,
        microcontent_id,
        tenant_id,
        kc_id,
        "Microlección: Fase Luminosa",
        json.dumps(content_body),
        teacher_id,
    )

    # Question with 2 options
    q_id = uuid.uuid4()
    await db_conn.execute(
        """
        INSERT INTO questions (
            id, tenant_id, knowledge_component_id, question_text, explanation, difficulty, created_by, is_active
        ) VALUES ($1, $2, $3, '¿Cuál es el aceptor terminal de electrones en la fase luminosa?', 'El NADP+ se reduce a NADPH.', 0.500, $4, true)
        """,
        q_id,
        tenant_id,
        kc_id,
        teacher_id,
    )

    opt_correct_id = uuid.uuid4()
    opt_incorrect_id = uuid.uuid4()
    await db_conn.execute(
        """
        INSERT INTO question_options (id, question_id, option_text, is_correct, order_index) VALUES
            ($1, $2, 'NADP+', true, 1),
            ($3, $2, 'Oxígeno', false, 2)
        """,
        opt_correct_id,
        q_id,
        opt_incorrect_id,
    )

    # Activity published for Section 1
    activity_id = uuid.uuid4()
    await db_conn.execute(
        """
        INSERT INTO activities (
            id, tenant_id, course_id, title, activity_type,
            feedback_policy, max_attempts, is_active, status, created_by
        ) VALUES ($1, $2, $3, 'Cuestionario: Fotosíntesis Luminosa', 'formative'::activity_type_enum, 'immediate_with_explanation'::feedback_policy_enum, 3, true, 'published', $4)
        """,
        activity_id,
        tenant_id,
        course_id,
        teacher_id,
    )

    await db_conn.execute(
        "INSERT INTO activity_questions (activity_id, question_id, order_index) VALUES ($1, $2, 1)",
        activity_id,
        q_id,
    )

    await db_conn.execute(
        "INSERT INTO activity_sections (activity_id, section_id, tenant_id) VALUES ($1, $2, $3)",
        activity_id,
        section1_id,
        tenant_id,
    )

    return {
        "tenant_id": tenant_id,
        "teacher_id": teacher_id,
        "student1_id": student1_id,
        "student2_id": student2_id,
        "course_id": course_id,
        "section1_id": section1_id,
        "section2_id": section2_id,
        "kc_id": kc_id,
        "microcontent_id": microcontent_id,
        "activity_id": activity_id,
        "q_id": q_id,
        "opt_correct_id": opt_correct_id,
        "opt_incorrect_id": opt_incorrect_id,
    }


class TestR2AdaptiveLearningLoop:
    """Verifies the complete closed loop: quiz -> answer_events -> prediction -> adaptation -> recommendations."""

    @pytest.mark.asyncio
    async def test_full_closed_loop_execution(
        self,
        db_conn: asyncpg.Connection,
        r2_test_environment: dict,
    ):
        ctx = r2_test_environment
        student1_token = create_student_token(ctx["student1_id"], ctx["tenant_id"])
        auth_headers = {"Authorization": f"Bearer {student1_token}"}

        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            # 1. Access published activity: questions must be sanitized
            res_act = await client.get(
                f"/api/v1/students/me/activities/{ctx['activity_id']}",
                headers=auth_headers,
            )
            assert res_act.status_code == 200
            act_data = res_act.json()
            assert act_data["title"] == "Cuestionario: Fotosíntesis Luminosa"
            assert len(act_data["questions"]) == 1
            # Invariant: is_correct and teacher explanation are not leaked
            assert "explanation" not in act_data["questions"][0]
            for opt in act_data["questions"][0]["options"]:
                assert "is_correct" not in opt

            # 2. Start attempt with idempotency key
            start_idem_key = str(uuid.uuid4())
            res_start = await client.post(
                f"/api/v1/students/me/activities/{ctx['activity_id']}/attempts",
                headers={**auth_headers, "X-Idempotency-Key": start_idem_key},
                json={},
            )
            assert res_start.status_code == 201
            attempt_data = res_start.json()
            attempt_id = attempt_data["attempt_id"]
            assert attempt_data["status"] == "in_progress"

            # 3. Submit an incorrect answer to trigger reinforcement need
            ans_idem_key = str(uuid.uuid4())
            res_ans = await client.post(
                f"/api/v1/students/me/attempts/{attempt_id}/answers",
                headers={**auth_headers, "X-Idempotency-Key": ans_idem_key},
                json={
                    "question_id": str(ctx["q_id"]),
                    "selected_option_id": str(ctx["opt_incorrect_id"]),
                    "response_time_seconds": 5.2,
                },
            )
            assert res_ans.status_code == 201
            ans_res = res_ans.json()
            assert ans_res["is_correct"] is False  # Server calculated

            # Verify answer_events is appended
            event_row = await db_conn.fetchrow(
                "SELECT id, is_correct, response_time_seconds FROM answer_events WHERE attempt_id = $1",
                uuid.UUID(attempt_id),
            )
            assert event_row is not None
            assert event_row["is_correct"] is False

            # 4. Finalize attempt: this triggers predictive update and adaptation
            res_submit = await client.post(
                f"/api/v1/students/me/attempts/{attempt_id}/submit",
                headers=auth_headers,
            )
            assert res_submit.status_code == 200
            submit_data = res_submit.json()
            assert submit_data["status"] == "completed"
            assert submit_data["score"] == 0.0
            assert submit_data["total_questions"] == 1
            assert submit_data["correct_answers"] == 0

            # 5. Verify predictive state persistence:
            # Table student_knowledge_states must now exist with updated mastery
            state_row = await db_conn.fetchrow(
                """
                SELECT p_mastery, confidence, total_interactions, last_updated_at
                FROM student_knowledge_states
                WHERE student_id = $1 AND knowledge_component_id = $2
                """,
                ctx["student1_id"],
                ctx["kc_id"],
            )
            assert state_row is not None, "student_knowledge_states was not updated on submit_attempt!"
            assert state_row["total_interactions"] >= 1
            assert float(state_row["p_mastery"]) <= 1.0

            # Table predictions must have recorded an entry
            pred_row = await db_conn.fetchrow(
                """
                SELECT predicted_recall_probability, estimated_risk, tau_threshold
                FROM predictions
                WHERE student_id = $1 AND knowledge_component_id = $2
                ORDER BY created_at DESC LIMIT 1
                """,
                ctx["student1_id"],
                ctx["kc_id"],
            )
            assert pred_row is not None, "predictions was not persisted on submit_attempt!"
            assert float(pred_row["tau_threshold"]) == 0.650

            # 6. Verify adaptive recommendation persistence:
            # Table recommendations must have a pending recommendation for the student's weak KC
            rec_row = await db_conn.fetchrow(
                """
                SELECT id, microcontent_id, selection_method, status, decision_reason, cooldown_until
                FROM recommendations
                WHERE student_id = $1 AND knowledge_component_id = $2
                ORDER BY created_at DESC LIMIT 1
                """,
                ctx["student1_id"],
                ctx["kc_id"],
            )
            assert rec_row is not None, "Adaptation engine did not generate a recommendation!"
            assert rec_row["status"] == "pending"
            assert rec_row["microcontent_id"] == ctx["microcontent_id"]
            recommendation_id = rec_row["id"]

            # 7. Student dashboard reflects upcoming review
            res_dash = await client.get(
                "/api/v1/students/me/dashboard",
                headers=auth_headers,
            )
            assert res_dash.status_code == 200
            dash_data = res_dash.json()
            assert len(dash_data["upcoming_reviews"]) >= 1
            up_rev = dash_data["upcoming_reviews"][0]
            assert up_rev["knowledge_component_id"] == str(ctx["kc_id"])
            assert up_rev["recommendation_id"] == str(recommendation_id)

            # 8. Student recommendations endpoint retrieves the persisted plan
            res_recs = await client.get(
                "/api/v1/students/me/recommendations",
                headers=auth_headers,
            )
            assert res_recs.status_code == 200
            recs_list = res_recs.json()
            assert len(recs_list) >= 1
            assert recs_list[0]["id"] == str(recommendation_id)
            assert recs_list[0]["microcontent"]["id"] == str(ctx["microcontent_id"])

            # 9. Query idempotency: reloading dashboard does not create new duplicate recommendations
            recs_count_before = await db_conn.fetchval(
                "SELECT COUNT(*) FROM recommendations WHERE student_id = $1",
                ctx["student1_id"],
            )
            await client.get("/api/v1/students/me/dashboard", headers=auth_headers)
            await client.get("/api/v1/students/me/recommendations", headers=auth_headers)
            recs_count_after = await db_conn.fetchval(
                "SELECT COUNT(*) FROM recommendations WHERE student_id = $1",
                ctx["student1_id"],
            )
            assert recs_count_before == recs_count_after, "Duplicate recommendations created upon query!"

            # 10. Study microcontent and record exposure event with recommendation_id
            exposure_idem_key = str(uuid.uuid4())
            started_time = (datetime.now(UTC) - timedelta(minutes=2)).isoformat()
            res_exp = await client.post(
                f"/api/v1/students/me/microcontents/{ctx['microcontent_id']}/exposures",
                headers=auth_headers,
                json={
                    "started_at": started_time,
                    "exposure_type": "review_study",
                    "duration_seconds": 120.0,
                    "active_reading_seconds": 110.0,
                    "completion_status": "completed",
                    "session_id": str(uuid.uuid4()),
                    "idempotency_key": exposure_idem_key,
                    "recommendation_id": str(recommendation_id),
                },
            )
            assert res_exp.status_code == 201
            assert res_exp.json()["recommendation_completed"] is True

            # Verify recommendation status transitioned to completed
            rec_completed = await db_conn.fetchval(
                "SELECT status FROM recommendations WHERE id = $1",
                recommendation_id,
            )
            assert rec_completed == "completed"

            # 11. Student isolation: Student 2 in Section 2 cannot view or submit to Student 1's attempt
            student2_token = create_student_token(ctx["student2_id"], ctx["tenant_id"])
            student2_headers = {"Authorization": f"Bearer {student2_token}"}

            # Student 2 blocked from viewing Student 1's attempt results
            res_iso = await client.get(
                f"/api/v1/students/me/attempts/{attempt_id}/results",
                headers=student2_headers,
            )
            assert res_iso.status_code in (403, 404)

            # Student 2 blocked from completing Student 1's recommendation
            res_rec_iso = await client.post(
                f"/api/v1/students/me/recommendations/{recommendation_id}/complete",
                headers=student2_headers,
            )
            assert res_rec_iso.status_code in (403, 404)

    @pytest.mark.asyncio
    async def test_attempt_completed_blocks_subsequent_answers(
        self,
        db_conn: asyncpg.Connection,
        r2_test_environment: dict,
    ):
        """Verifies that an attempt once sealed rejects subsequent answers with HTTP 409."""
        ctx = r2_test_environment
        student_token = create_student_token(ctx["student1_id"], ctx["tenant_id"])
        headers = {"Authorization": f"Bearer {student_token}"}

        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            # Start attempt
            res_start = await client.post(
                f"/api/v1/students/me/activities/{ctx['activity_id']}/attempts",
                headers=headers,
                json={},
            )
            att_id = res_start.json()["attempt_id"]

            # Submit attempt immediately
            res_sub = await client.post(
                f"/api/v1/students/me/attempts/{att_id}/submit",
                headers=headers,
            )
            assert res_sub.status_code == 200

            # Subsequent answer submission must be rejected with 409 Conflict
            res_ans = await client.post(
                f"/api/v1/students/me/attempts/{att_id}/answers",
                headers=headers,
                json={
                    "question_id": str(ctx["q_id"]),
                    "selected_option_id": str(ctx["opt_correct_id"]),
                    "response_time_seconds": 2.0,
                },
            )
            assert res_ans.status_code == 409

    @pytest.mark.asyncio
    async def test_no_published_content_available_fallback(
        self,
        db_conn: asyncpg.Connection,
        r2_test_environment: dict,
    ):
        """Verifies graceful adaptation fallback when KC has no published microcontent."""
        ctx = r2_test_environment
        # Unpublish all microcontents for this tenant
        await db_conn.execute(
            "UPDATE microcontents SET is_published = false WHERE tenant_id = $1",
            ctx["tenant_id"],
        )

        # Record 1 interaction so student has prior activity and triggers review need
        enr_id = await db_conn.fetchval(
            "SELECT id FROM enrollments WHERE student_id = $1 AND tenant_id = $2",
            ctx["student1_id"],
            ctx["tenant_id"],
        )
        att_id = uuid.uuid4()
        await db_conn.execute(
            "INSERT INTO quiz_attempts (id, tenant_id, enrollment_id, activity_id, student_id, status) VALUES ($1, $2, $3, $4, $5, 'completed'::attempt_status_enum)",
            att_id,
            ctx["tenant_id"],
            enr_id,
            ctx["activity_id"],
            ctx["student1_id"],
        )
        await db_conn.execute(
            """
            INSERT INTO answer_events (
                id, tenant_id, attempt_id, student_id, question_id,
                knowledge_component_id, selected_option_id, is_correct,
                attempt_number, response_time_seconds, idempotency_key, activity_id
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, false, 1, 4.0, $8, $9)
            """,
            uuid.uuid4(),
            ctx["tenant_id"],
            att_id,
            ctx["student1_id"],
            ctx["q_id"],
            ctx["kc_id"],
            ctx["opt_incorrect_id"],
            uuid.uuid4(),
            ctx["activity_id"],
        )

        student_token = create_student_token(ctx["student1_id"], ctx["tenant_id"])
        headers = {"Authorization": f"Bearer {student_token}"}

        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            # Call evaluate recommendations
            res_eval = await client.post(
                "/api/v1/students/me/recommendations/evaluate",
                headers=headers,
            )
            assert res_eval.status_code == 200
            eval_data = res_eval.json()
            # Must record no_content_available decision without hallucinating contents or crashing
            no_content_decisions = [
                d for d in eval_data["decisions"] if d["decision"] == "no_content_available"
            ]
            assert len(no_content_decisions) >= 1
            assert eval_data["recommendations_created"] == 0

    @pytest.mark.asyncio
    async def test_concurrent_attempt_submissions_no_deadlock_or_duplicate_recommendations(
        self,
        db_conn: asyncpg.Connection,
        r2_test_environment: dict,
    ):
        """Verifies concurrent attempt finalization on different activities/KCs
        completes safely without database deadlocks and produces zero duplicate recommendations."""
        ctx = r2_test_environment
        student_token = create_student_token(ctx["student1_id"], ctx["tenant_id"])
        headers = {"Authorization": f"Bearer {student_token}"}

        # Create a second KC, question, microcontent, and activity for Section 1
        kc2_id = uuid.uuid4()
        await db_conn.execute(
            """
            INSERT INTO knowledge_components (id, tenant_id, unit_id, name, description, difficulty_prior)
            VALUES ($1, $2, (SELECT id FROM units WHERE course_id = $3 LIMIT 1), 'Ciclo de Calvin', 'Fase oscura de la fotosíntesis', 0.60)
            """,
            kc2_id,
            ctx["tenant_id"],
            ctx["course_id"],
        )
        import json
        micro2_id = uuid.uuid4()
        await db_conn.execute(
            """
            INSERT INTO microcontents (
                id, tenant_id, knowledge_component_id, title,
                content_type, content_body, is_published, estimated_duration_seconds, created_by
            ) VALUES ($1, $2, $3, 'Microlección: Ciclo de Calvin', 'text_summary'::content_type_enum, $4::jsonb, true, 200, $5)
            """,
            micro2_id,
            ctx["tenant_id"],
            kc2_id,
            json.dumps({"summary": "Fase oscura fijación de carbono"}),
            ctx["teacher_id"],
        )
        q2_id = uuid.uuid4()
        await db_conn.execute(
            """
            INSERT INTO questions (id, tenant_id, knowledge_component_id, question_text, explanation, difficulty, created_by, is_active)
            VALUES ($1, $2, $3, '¿Dónde ocurre el ciclo de Calvin?', 'En el estroma del cloroplasto.', 0.55, $4, true)
            """,
            q2_id,
            ctx["tenant_id"],
            kc2_id,
            ctx["teacher_id"],
        )
        opt2_c_id = uuid.uuid4()
        opt2_i_id = uuid.uuid4()
        await db_conn.execute(
            """
            INSERT INTO question_options (id, question_id, option_text, is_correct, order_index) VALUES
                ($1, $2, 'Estroma', true, 1),
                ($3, $2, 'Tilacoide', false, 2)
            """,
            opt2_c_id,
            q2_id,
            opt2_i_id,
        )
        act2_id = uuid.uuid4()
        await db_conn.execute(
            """
            INSERT INTO activities (
                id, tenant_id, course_id, title, activity_type,
                feedback_policy, max_attempts, is_active, status, created_by
            ) VALUES ($1, $2, $3, 'Cuestionario: Ciclo de Calvin', 'formative'::activity_type_enum, 'upon_completion'::feedback_policy_enum, 3, true, 'published', $4)
            """,
            act2_id,
            ctx["tenant_id"],
            ctx["course_id"],
            ctx["teacher_id"],
        )
        await db_conn.execute(
            "INSERT INTO activity_questions (activity_id, question_id, order_index) VALUES ($1, $2, 1)",
            act2_id,
            q2_id,
        )
        await db_conn.execute(
            "INSERT INTO activity_sections (activity_id, section_id, tenant_id) VALUES ($1, $2, $3)",
            act2_id,
            ctx["section1_id"],
            ctx["tenant_id"],
        )

        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            # Start attempt 1 on Activity 1
            res_start1 = await client.post(
                f"/api/v1/students/me/activities/{ctx['activity_id']}/attempts",
                headers=headers,
                json={},
            )
            assert res_start1.status_code == 201
            att1_id = res_start1.json()["attempt_id"]

            # Start attempt 2 on Activity 2
            res_start2 = await client.post(
                f"/api/v1/students/me/activities/{act2_id}/attempts",
                headers=headers,
                json={},
            )
            assert res_start2.status_code == 201
            att2_id = res_start2.json()["attempt_id"]

            # Submit answers for both
            res_ans1 = await client.post(
                f"/api/v1/students/me/attempts/{att1_id}/answers",
                headers=headers,
                json={
                    "question_id": str(ctx["q_id"]),
                    "selected_option_id": str(ctx["opt_incorrect_id"]),
                    "response_time_seconds": 3.0,
                },
            )
            assert res_ans1.status_code == 201

            res_ans2 = await client.post(
                f"/api/v1/students/me/attempts/{att2_id}/answers",
                headers=headers,
                json={
                    "question_id": str(q2_id),
                    "selected_option_id": str(opt2_i_id),
                    "response_time_seconds": 3.5,
                },
            )
            assert res_ans2.status_code == 201

            # Submit both attempts concurrently with asyncio.gather
            sub1_task = client.post(f"/api/v1/students/me/attempts/{att1_id}/submit", headers=headers)
            sub2_task = client.post(f"/api/v1/students/me/attempts/{att2_id}/submit", headers=headers)

            res_sub1, res_sub2 = await asyncio.gather(sub1_task, sub2_task)
            assert res_sub1.status_code == 200
            assert res_sub2.status_code == 200

            # Verify both student_knowledge_states are upserted without deadlock
            states = await db_conn.fetch(
                """
                SELECT knowledge_component_id, p_mastery, total_interactions
                FROM student_knowledge_states
                WHERE student_id = $1 AND knowledge_component_id IN ($2, $3)
                """,
                ctx["student1_id"],
                ctx["kc_id"],
                kc2_id,
            )
            assert len(states) == 2

            # Verify no duplicate recommendations were generated per KC
            for kc in (ctx["kc_id"], kc2_id):
                pending_count = await db_conn.fetchval(
                    "SELECT COUNT(*) FROM recommendations WHERE student_id = $1 AND knowledge_component_id = $2 AND status = 'pending'",
                    ctx["student1_id"],
                    kc,
                )
                assert pending_count == 1, f"Expected exactly 1 pending recommendation for KC {kc}, got {pending_count}"

    @pytest.mark.asyncio
    async def test_cold_start_initial_practice_and_anti_fatigue_cooldown(
        self,
        db_conn: asyncpg.Connection,
        r2_test_environment: dict,
    ):
        """Verifies cold-start transition: 0 prior interactions -> initial practice triggers
        rule-based consolidation recommendation, while immediate subsequent practice respects
        24h anti-fatigue cooldown and rejects duplication."""
        ctx = r2_test_environment
        student_token = create_student_token(ctx["student1_id"], ctx["tenant_id"])
        headers = {"Authorization": f"Bearer {student_token}"}

        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            # First attempt: cold start with 0 prior interactions
            res_start1 = await client.post(
                f"/api/v1/students/me/activities/{ctx['activity_id']}/attempts",
                headers=headers,
                json={},
            )
            att1_id = res_start1.json()["attempt_id"]

            await client.post(
                f"/api/v1/students/me/attempts/{att1_id}/answers",
                headers=headers,
                json={
                    "question_id": str(ctx["q_id"]),
                    "selected_option_id": str(ctx["opt_incorrect_id"]),
                    "response_time_seconds": 4.0,
                },
            )

            res_sub1 = await client.post(
                f"/api/v1/students/me/attempts/{att1_id}/submit",
                headers=headers,
            )
            assert res_sub1.status_code == 200

            # Verify initial recommendation was created under rule_based_fallback / cold-start
            rec1 = await db_conn.fetchrow(
                """
                SELECT id, selection_method::text, status::text, decision_reason
                FROM recommendations
                WHERE student_id = $1 AND knowledge_component_id = $2
                ORDER BY created_at DESC LIMIT 1
                """,
                ctx["student1_id"],
                ctx["kc_id"],
            )
            assert rec1 is not None
            assert rec1["status"] == "pending"
            assert "cold-start" in rec1["decision_reason"] or "Consolidación" in rec1["decision_reason"]

            # Second attempt immediately after on the same KC
            res_start2 = await client.post(
                f"/api/v1/students/me/activities/{ctx['activity_id']}/attempts",
                headers=headers,
                json={},
            )
            att2_id = res_start2.json()["attempt_id"]

            await client.post(
                f"/api/v1/students/me/attempts/{att2_id}/answers",
                headers=headers,
                json={
                    "question_id": str(ctx["q_id"]),
                    "selected_option_id": str(ctx["opt_incorrect_id"]),
                    "response_time_seconds": 3.0,
                },
            )

            res_sub2 = await client.post(
                f"/api/v1/students/me/attempts/{att2_id}/submit",
                headers=headers,
            )
            assert res_sub2.status_code == 200

            # Total recommendations count must still be strictly 1 (no duplication under cooldown)
            total_recs = await db_conn.fetchval(
                "SELECT COUNT(*) FROM recommendations WHERE student_id = $1 AND knowledge_component_id = $2",
                ctx["student1_id"],
                ctx["kc_id"],
            )
            assert total_recs == 1
