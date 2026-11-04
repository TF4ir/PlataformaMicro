"""PostgreSQL Repository for Student Learning Flow, Attempts, and Immutable Answer Events (Milestone M4)."""

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

import asyncpg

from app.schemas.activities import (
    ActivityType,
    AttemptStatus,
    FeedbackPolicy,
    QuestionOptionPublic,
)
from app.schemas.learning import (
    AnswerFeedback,
    AttemptQuestionReview,
    AttemptResultsResponse,
    KCResultSummary,
    StartAttemptResponse,
    StudentActivityDetail,
    StudentActivityListItem,
    StudentCourseItem,
    StudentQuestionItem,
    SubmitAnswerRequest,
    SubmitAnswerResponse,
    SubmitAttemptResponse,
)

logger = logging.getLogger(__name__)


class LearningRepository:
    """Handles persistence and transactions for Student Learning sessions and immutable answer_events."""

    def __init__(self, pool: asyncpg.Pool) -> None:
        self.pool = pool

    async def list_student_courses(
        self,
        tenant_id: UUID,
        student_id: UUID,
    ) -> list[StudentCourseItem]:
        """Fetch courses and assigned sections for the authenticated student."""
        async with self.pool.acquire() as conn:
            query = """
            SELECT DISTINCT c.id AS course_id, c.code AS course_code,
                   c.name AS course_name, c.description,
                   s.id AS section_id, s.name AS section_name
            FROM enrollments e
            JOIN sections s ON s.id = e.section_id
            JOIN courses c ON c.id = s.course_id
            WHERE e.tenant_id = $1 AND e.student_id = $2 AND c.is_active = true
            ORDER BY c.name ASC;
            """
            rows = await conn.fetch(query, tenant_id, student_id)
            return [
                StudentCourseItem(
                    course_id=r["course_id"],
                    course_code=r["course_code"],
                    course_name=r["course_name"],
                    description=r["description"],
                    section_id=r["section_id"],
                    section_name=r["section_name"],
                )
                for r in rows
            ]

    async def list_student_activities(
        self,
        tenant_id: UUID,
        student_id: UUID,
    ) -> list[StudentActivityListItem]:
        """List published activities for the student's enrolled sections."""
        async with self.pool.acquire() as conn:
            query = """
            SELECT a.id AS activity_id, a.title, a.description, a.course_id,
                   c.name AS course_name, s.id AS section_id, s.name AS section_name,
                   a.activity_type::text, a.feedback_policy::text,
                   a.max_attempts, a.time_limit_minutes, a.available_from,
                   a.available_until, a.published_at,
                   COUNT(qa.id) AS attempts_count,
                   (
                       SELECT qa2.id FROM quiz_attempts qa2
                       WHERE qa2.activity_id = a.id AND qa2.student_id = $2
                       ORDER BY qa2.started_at DESC LIMIT 1
                   ) AS latest_attempt_id,
                   (
                       SELECT qa2.status::text FROM quiz_attempts qa2
                       WHERE qa2.activity_id = a.id AND qa2.student_id = $2
                       ORDER BY qa2.started_at DESC LIMIT 1
                   ) AS latest_attempt_status,
                   (
                       SELECT qa2.score FROM quiz_attempts qa2
                       WHERE qa2.activity_id = a.id AND qa2.student_id = $2
                       ORDER BY qa2.started_at DESC LIMIT 1
                   ) AS latest_score
            FROM activities a
            JOIN courses c ON c.id = a.course_id
            JOIN activity_sections acts ON acts.activity_id = a.id
            JOIN sections s ON s.id = acts.section_id
            JOIN enrollments e ON e.section_id = s.id AND e.student_id = $2
            LEFT JOIN quiz_attempts qa ON qa.activity_id = a.id AND qa.student_id = $2
            WHERE a.tenant_id = $1
              AND a.status = 'published'
              AND a.is_active = true
            GROUP BY a.id, c.name, s.id, s.name
            ORDER BY a.published_at DESC NULLS LAST, a.created_at DESC;
            """
            rows = await conn.fetch(query, tenant_id, student_id)

            now = datetime.now(UTC)
            results: list[StudentActivityListItem] = []
            for r in rows:
                attempts_count = r["attempts_count"]
                max_attempts = r["max_attempts"]

                # Availability check
                is_available = True
                if r["available_from"] and now < r["available_from"]:
                    is_available = False
                if r["available_until"] and now > r["available_until"]:
                    is_available = False

                can_attempt = is_available and (attempts_count < max_attempts)

                latest_score = float(r["latest_score"]) if r["latest_score"] is not None else None
                latest_status = AttemptStatus(r["latest_attempt_status"]) if r["latest_attempt_status"] else None

                results.append(
                    StudentActivityListItem(
                        activity_id=r["activity_id"],
                        title=r["title"],
                        description=r["description"],
                        course_id=r["course_id"],
                        course_name=r["course_name"],
                        section_id=r["section_id"],
                        section_name=r["section_name"],
                        activity_type=ActivityType(r["activity_type"]),
                        feedback_policy=FeedbackPolicy(r["feedback_policy"]),
                        max_attempts=max_attempts,
                        time_limit_minutes=r["time_limit_minutes"],
                        available_from=r["available_from"],
                        available_until=r["available_until"],
                        published_at=r["published_at"],
                        attempts_count=attempts_count,
                        can_attempt=can_attempt,
                        latest_attempt_id=r["latest_attempt_id"],
                        latest_attempt_status=latest_status,
                        latest_score=latest_score,
                    )
                )

            return results

    async def get_student_activity_detail(
        self,
        tenant_id: UUID,
        student_id: UUID,
        activity_id: UUID,
    ) -> StudentActivityDetail:
        """Fetch sanitized activity detail and questions for student (no answers or explanations)."""
        async with self.pool.acquire() as conn:
            # Verify enrollment in an assigned section
            act_row = await conn.fetchrow(
                """
                SELECT a.id, a.title, a.description, a.course_id, c.name AS course_name,
                       a.activity_type::text, a.feedback_policy::text,
                       a.time_limit_minutes, a.max_attempts, a.status, a.is_active
                FROM activities a
                JOIN courses c ON c.id = a.course_id
                JOIN activity_sections acts ON acts.activity_id = a.id
                JOIN enrollments e ON e.section_id = acts.section_id AND e.student_id = $2
                WHERE a.id = $1 AND a.tenant_id = $3;
                """,
                activity_id,
                student_id,
                tenant_id,
            )
            if not act_row:
                raise KeyError(f"Activity {activity_id} not accessible for student.")

            if act_row["status"] != "published" or not act_row["is_active"]:
                raise PermissionError(f"Activity {activity_id} is not currently published.")

            # Check for active in_progress attempt
            active_attempt = await conn.fetchval(
                """
                SELECT id FROM quiz_attempts
                WHERE activity_id = $1 AND student_id = $2 AND status = 'in_progress'
                ORDER BY started_at DESC LIMIT 1;
                """,
                activity_id,
                student_id,
            )

            # Fetch sanitized questions
            q_rows = await conn.fetch(
                """
                SELECT aq.order_index, q.id, q.question_text, q.question_type
                FROM activity_questions aq
                JOIN questions q ON q.id = aq.question_id
                WHERE aq.activity_id = $1 AND q.is_active = true
                ORDER BY aq.order_index ASC;
                """,
                activity_id,
            )

            questions: list[StudentQuestionItem] = []
            for qr in q_rows:
                q_id = qr["id"]
                # Options: id, option_text, order_index ONLY
                opt_rows = await conn.fetch(
                    """
                    SELECT id, option_text, order_index
                    FROM question_options
                    WHERE question_id = $1
                    ORDER BY order_index ASC;
                    """,
                    q_id,
                )
                options = [
                    QuestionOptionPublic(
                        id=opt["id"],
                        option_text=opt["option_text"],
                        order_index=opt["order_index"],
                    )
                    for opt in opt_rows
                ]

                questions.append(
                    StudentQuestionItem(
                        id=qr["id"],
                        question_text=qr["question_text"],
                        question_type=qr["question_type"],
                        order_index=qr["order_index"],
                        options=options,
                    )
                )

            return StudentActivityDetail(
                activity_id=act_row["id"],
                title=act_row["title"],
                description=act_row["description"],
                course_id=act_row["course_id"],
                course_name=act_row["course_name"],
                activity_type=ActivityType(act_row["activity_type"]),
                feedback_policy=FeedbackPolicy(act_row["feedback_policy"]),
                time_limit_minutes=act_row["time_limit_minutes"],
                max_attempts=act_row["max_attempts"],
                questions=questions,
                active_attempt_id=active_attempt,
            )

    async def start_attempt(
        self,
        tenant_id: UUID,
        student_id: UUID,
        activity_id: UUID,
        idempotency_key: UUID | None = None,
    ) -> StartAttemptResponse:
        """Safely initialize or retrieve an in-progress quiz attempt."""
        async with self.pool.acquire() as conn, conn.transaction():
            # 1. Idempotency check if idempotency_key provided
            if idempotency_key:
                existing_by_key = await conn.fetchrow(
                    """
                    SELECT id, attempt_number, status::text, started_at
                    FROM quiz_attempts
                    WHERE idempotency_key = $1;
                    """,
                    idempotency_key,
                )
                if existing_by_key:
                    questions = (await self.get_student_activity_detail(tenant_id, student_id, activity_id)).questions
                    return StartAttemptResponse(
                        attempt_id=existing_by_key["id"],
                        activity_id=activity_id,
                        attempt_number=existing_by_key["attempt_number"],
                        status=AttemptStatus(existing_by_key["status"]),
                        started_at=existing_by_key["started_at"],
                        questions=questions,
                    )

            # 2. Check student's enrollment in a section assigned to this activity
            enrollment_row = await conn.fetchrow(
                """
                SELECT e.id AS enrollment_id, a.status, a.is_active,
                       a.available_from, a.available_until, a.max_attempts
                FROM activities a
                JOIN activity_sections acts ON acts.activity_id = a.id
                JOIN enrollments e ON e.section_id = acts.section_id AND e.student_id = $2
                WHERE a.id = $1 AND a.tenant_id = $3;
                """,
                activity_id,
                student_id,
                tenant_id,
            )
            if not enrollment_row:
                raise PermissionError(f"Student {student_id} is not enrolled in any section assigned to activity {activity_id}.")

            if enrollment_row["status"] != "published" or not enrollment_row["is_active"]:
                raise PermissionError(f"Activity {activity_id} is not currently open.")

            now = datetime.now(UTC)
            if enrollment_row["available_from"] and now < enrollment_row["available_from"]:
                raise ValueError("La actividad aún no está disponible según el calendario programado.")
            if enrollment_row["available_until"] and now > enrollment_row["available_until"]:
                raise ValueError("El periodo de disponibilidad para esta actividad ha concluido.")

            # 3. Check for existing in_progress attempt
            existing_active = await conn.fetchrow(
                """
                SELECT id, attempt_number, status::text, started_at
                FROM quiz_attempts
                WHERE activity_id = $1 AND student_id = $2 AND status = 'in_progress'
                ORDER BY started_at DESC LIMIT 1;
                """,
                activity_id,
                student_id,
            )
            if existing_active:
                questions = (await self.get_student_activity_detail(tenant_id, student_id, activity_id)).questions
                return StartAttemptResponse(
                    attempt_id=existing_active["id"],
                    activity_id=activity_id,
                    attempt_number=existing_active["attempt_number"],
                    status=AttemptStatus(existing_active["status"]),
                    started_at=existing_active["started_at"],
                    questions=questions,
                )

            # 4. Check max_attempts limit
            total_attempts = await conn.fetchval(
                "SELECT COUNT(*) FROM quiz_attempts WHERE activity_id = $1 AND student_id = $2;",
                activity_id,
                student_id,
            ) or 0
            max_allowed = enrollment_row["max_attempts"]
            if total_attempts >= max_allowed:
                raise PermissionError(f"Se ha alcanzado el límite máximo de intentos permitidos ({max_allowed}).")

            # 5. Insert new attempt
            attempt_number = total_attempts + 1
            key_to_use = idempotency_key or uuid4()

            try:
                attempt_row = await conn.fetchrow(
                    """
                    INSERT INTO quiz_attempts (
                        tenant_id, enrollment_id, activity_id, student_id,
                        attempt_number, status, idempotency_key, started_at
                    ) VALUES (
                        $1, $2, $3, $4, $5, 'in_progress'::attempt_status_enum, $6, now()
                    )
                    RETURNING id, started_at;
                    """,
                    tenant_id,
                    enrollment_row["enrollment_id"],
                    activity_id,
                    student_id,
                    attempt_number,
                    key_to_use,
                )
                attempt_id_ret = attempt_row["id"]
                started_at_ret = attempt_row["started_at"]
                ret_status = AttemptStatus.IN_PROGRESS
            except asyncpg.UniqueViolationError:
                existing_attempt = await conn.fetchrow(
                    """
                    SELECT id, attempt_number, status::text, started_at
                    FROM quiz_attempts
                    WHERE idempotency_key = $1
                       OR (activity_id = $2 AND student_id = $3 AND status = 'in_progress');
                    """,
                    key_to_use,
                    activity_id,
                    student_id,
                )
                if existing_attempt:
                    attempt_id_ret = existing_attempt["id"]
                    started_at_ret = existing_attempt["started_at"]
                    attempt_number = existing_attempt["attempt_number"]
                    ret_status = AttemptStatus(existing_attempt["status"])
                else:
                    raise

            questions = (await self.get_student_activity_detail(tenant_id, student_id, activity_id)).questions
            return StartAttemptResponse(
                attempt_id=attempt_id_ret,
                activity_id=activity_id,
                attempt_number=attempt_number,
                status=ret_status,
                started_at=started_at_ret,
                questions=questions,
            )


    async def record_answer(
        self,
        tenant_id: UUID,
        student_id: UUID,
        attempt_id: UUID,
        payload: SubmitAnswerRequest,
    ) -> SubmitAnswerResponse:
        """Evaluate and persist answer into immutable answer_events table with strict idempotency."""
        effective_key = payload.idempotency_key or uuid4()

        async with self.pool.acquire() as conn, conn.transaction():
            # 1. Idempotency check: did we already record an event with this key?
            existing_event = await conn.fetchrow(
                """
                SELECT ae.id, ae.attempt_id, ae.question_id, ae.is_correct,
                       a.feedback_policy::text, q.explanation, aq.order_index
                FROM answer_events ae
                JOIN activities a ON a.id = ae.activity_id
                JOIN questions q ON q.id = ae.question_id
                LEFT JOIN activity_questions aq ON aq.activity_id = ae.activity_id AND aq.question_id = ae.question_id
                WHERE ae.idempotency_key = $1;
                """,
                effective_key,
            )
            if existing_event:
                is_corr = existing_event["is_correct"]
                policy = FeedbackPolicy(existing_event["feedback_policy"])
                feedback = None
                revealed_corr = None

                if policy == FeedbackPolicy.IMMEDIATE_WITH_EXPLANATION:
                    revealed_corr = is_corr
                    feedback = AnswerFeedback(
                        title="¡Respuesta correcta!" if is_corr else "Respuesta incorrecta",
                        explanation=existing_event["explanation"],
                    )

                next_idx = (
                    (existing_event["order_index"] + 1)
                    if existing_event["order_index"] is not None
                    else None
                )

                return SubmitAnswerResponse(
                    event_id=existing_event["id"],
                    attempt_id=existing_event["attempt_id"],
                    question_id=existing_event["question_id"],
                    is_correct=revealed_corr,
                    feedback=feedback,
                    attempt_completed=False,
                    next_question_index=next_idx,
                )

            # 2. Verify attempt exists, belongs to student, and is in_progress
            attempt = await conn.fetchrow(
                """
                SELECT qa.id, qa.activity_id, qa.attempt_number, qa.status::text,
                       a.course_id, a.feedback_policy::text
                FROM quiz_attempts qa
                JOIN activities a ON a.id = qa.activity_id
                WHERE qa.id = $1 AND qa.student_id = $2 AND qa.tenant_id = $3;
                """,
                attempt_id,
                student_id,
                tenant_id,
            )
            if not attempt:
                raise KeyError(f"Attempt {attempt_id} not found or not owned by student.")

            if attempt["status"] != "in_progress":
                raise ValueError("Cannot submit answers to an already completed or abandoned attempt.")

            activity_id = attempt["activity_id"]
            course_id = attempt["course_id"]
            attempt_number = attempt["attempt_number"]
            feedback_policy = FeedbackPolicy(attempt["feedback_policy"])

            # 3. Validate question is part of this activity
            aq_row = await conn.fetchrow(
                """
                SELECT aq.order_index, q.knowledge_component_id, q.explanation
                FROM activity_questions aq
                JOIN questions q ON q.id = aq.question_id
                WHERE aq.activity_id = $1 AND aq.question_id = $2;
                """,
                activity_id,
                payload.question_id,
            )
            if not aq_row:
                raise ValueError(f"Question {payload.question_id} is not part of activity {activity_id}.")

            kc_id = aq_row["knowledge_component_id"]
            explanation = aq_row["explanation"]
            q_order = aq_row["order_index"]

            # 4. Validate selected_option_id belongs to question and fetch canonical correctness
            opt_row = await conn.fetchrow(
                """
                SELECT id, is_correct
                FROM question_options
                WHERE id = $1 AND question_id = $2;
                """,
                payload.selected_option_id,
                payload.question_id,
            )
            if not opt_row:
                raise ValueError(f"Option {payload.selected_option_id} is not a valid option for question {payload.question_id}.")

            is_correct = bool(opt_row["is_correct"])

            # 5. Insert into immutable answer_events table (Append-Only)
            response_ms = max(1, int(payload.response_time_seconds * 1000))

            # Compute next chronological sequence number in this attempt
            seq_val = await conn.fetchval(
                "SELECT COALESCE(MAX(question_sequence), 0) + 1 FROM answer_events WHERE attempt_id = $1;",
                attempt_id,
            )

            try:
                event_row = await conn.fetchrow(
                    """
                    INSERT INTO answer_events (
                        tenant_id, attempt_id, student_id, question_id,
                        knowledge_component_id, selected_option_id, is_correct,
                        attempt_number, response_time_seconds, response_time_ms,
                        idempotency_key, activity_id, course_id, question_sequence,
                        event_timestamp
                    ) VALUES (
                        $1, $2, $3, $4,
                        $5, $6, $7,
                        $8, $9, $10,
                        $11, $12, $13, $14,
                        now()
                    )
                    RETURNING id;
                    """,
                    tenant_id,
                    attempt_id,
                    student_id,
                    payload.question_id,
                    kc_id,
                    payload.selected_option_id,
                    is_correct,
                    attempt_number,
                    payload.response_time_seconds,
                    response_ms,
                    effective_key,
                    activity_id,
                    course_id,
                    seq_val,
                )
                event_id = event_row["id"]
            except asyncpg.UniqueViolationError:
                existing = await conn.fetchrow(
                    "SELECT id, is_correct FROM answer_events WHERE idempotency_key = $1;",
                    effective_key,
                )
                if existing:
                    event_id = existing["id"]
                    is_correct = bool(existing["is_correct"])
                else:
                    raise


            # 6. Check feedback policy
            revealed_is_correct: bool | None = None
            feedback_obj: AnswerFeedback | None = None

            if feedback_policy == FeedbackPolicy.IMMEDIATE_WITH_EXPLANATION:
                revealed_is_correct = is_correct
                feedback_obj = AnswerFeedback(
                    title="¡Respuesta correcta!" if is_correct else "Respuesta incorrecta",
                    explanation=explanation,
                )

            # Next question index
            next_index = q_order + 1

            return SubmitAnswerResponse(
                event_id=event_id,
                attempt_id=attempt_id,
                question_id=payload.question_id,
                is_correct=revealed_is_correct,
                feedback=feedback_obj,
                attempt_completed=False,
                next_question_index=next_index,
            )

    async def submit_attempt(
        self,
        tenant_id: UUID,
        student_id: UUID,
        attempt_id: UUID,
    ) -> SubmitAttemptResponse:
        """Finalize the attempt, evaluate total score, and seal the session."""
        async with self.pool.acquire() as conn, conn.transaction():
            # 1. Fetch attempt and lock row with FOR UPDATE
            attempt = await conn.fetchrow(
                """
                SELECT id, activity_id, status::text, score, total_questions,
                       correct_answers, completed_at
                FROM quiz_attempts
                WHERE id = $1 AND student_id = $2 AND tenant_id = $3
                FOR UPDATE;
                """,
                attempt_id,
                student_id,
                tenant_id,
            )
            if not attempt:
                raise KeyError(f"Attempt {attempt_id} not found or not owned by student.")

            # If already completed, return idempotent response
            if attempt["status"] == "completed":
                return SubmitAttemptResponse(
                    attempt_id=attempt["id"],
                    activity_id=attempt["activity_id"],
                    status=AttemptStatus.COMPLETED,
                    score=float(attempt["score"] or 0.0),
                    total_questions=attempt["total_questions"] or 0,
                    correct_answers=attempt["correct_answers"] or 0,
                    completed_at=attempt["completed_at"],
                )

            activity_id = attempt["activity_id"]

            # 2. Fetch all questions in the activity
            act_questions = await conn.fetch(
                "SELECT question_id FROM activity_questions WHERE activity_id = $1 ORDER BY order_index ASC;",
                activity_id,
            )
            total_q = len(act_questions)
            if total_q == 0:
                total_q = 1  # prevent div by zero

            # 3. For each question, get the latest answer_event in this attempt
            answered_rows = await conn.fetch(
                """
                SELECT DISTINCT ON (question_id) question_id, is_correct
                FROM answer_events
                WHERE attempt_id = $1
                ORDER BY question_id, event_timestamp DESC, question_sequence DESC;
                """,
                attempt_id,
            )
            correct_count = sum(1 for r in answered_rows if r["is_correct"] is True)

            # Score on scale 0.0 - 100.0
            score = round((correct_count / total_q) * 100.0, 2)

            # 4. Seal attempt
            completed_at = datetime.now(UTC)
            await conn.execute(
                """
                UPDATE quiz_attempts
                SET status = 'completed'::attempt_status_enum,
                    completed_at = $1,
                    submitted_at = $1,
                    score = $2,
                    total_questions = $3,
                    correct_answers = $4
                WHERE id = $5;
                """,
                completed_at,
                score,
                total_q,
                correct_count,
                attempt_id,
            )

            return SubmitAttemptResponse(
                attempt_id=attempt_id,
                activity_id=activity_id,
                status=AttemptStatus.COMPLETED,
                score=score,
                total_questions=total_q,
                correct_answers=correct_count,
                completed_at=completed_at,
            )

    async def get_attempt_results(
        self,
        tenant_id: UUID,
        user_id: UUID,
        role: str,
        attempt_id: UUID,
    ) -> AttemptResultsResponse:
        """Retrieve complete results, question feedback review, and Knowledge Component breakdown."""
        async with self.pool.acquire() as conn:
            # Fetch attempt
            attempt = await conn.fetchrow(
                """
                SELECT qa.id, qa.activity_id, qa.student_id, qa.started_at,
                       qa.completed_at, qa.score, qa.total_questions,
                       qa.correct_answers, qa.status::text,
                       a.title AS activity_title, c.name AS course_name,
                       p.full_name AS student_name,
                       a.feedback_policy::text, a.available_until
                FROM quiz_attempts qa
                JOIN activities a ON a.id = qa.activity_id
                JOIN courses c ON c.id = a.course_id
                JOIN profiles p ON p.id = qa.student_id
                WHERE qa.id = $1 AND qa.tenant_id = $2;
                """,
                attempt_id,
                tenant_id,
            )
            if not attempt:
                raise KeyError(f"Attempt {attempt_id} not found.")

            # Access check: student can only view own; attempt must be completed for students
            if role == "student":
                if str(attempt["student_id"]) != str(user_id):
                    raise PermissionError("Access forbidden to attempt results.")
                if attempt["status"] != "completed":
                    raise PermissionError("Cannot view results of an in-progress attempt. Finalize the attempt first.")

            # Check feedback policy for solutions visibility
            can_reveal_solutions = True
            if role == "student":
                policy = FeedbackPolicy(attempt["feedback_policy"])
                if policy == FeedbackPolicy.AFTER_DEADLINE and attempt["available_until"]:
                    now = datetime.now(UTC)
                    if now < attempt["available_until"]:
                        can_reveal_solutions = False

            # Fetch questions with answers
            q_rows = await conn.fetch(
                """
                SELECT aq.order_index, q.id AS question_id, q.question_text,
                       q.explanation, q.knowledge_component_id, kc.name AS kc_name,
                       (
                           SELECT ae.selected_option_id FROM answer_events ae
                           WHERE ae.attempt_id = $1 AND ae.question_id = q.id
                           ORDER BY ae.event_timestamp DESC, ae.question_sequence DESC LIMIT 1
                       ) AS selected_option_id,
                       (
                           SELECT ae.is_correct FROM answer_events ae
                           WHERE ae.attempt_id = $1 AND ae.question_id = q.id
                           ORDER BY ae.event_timestamp DESC, ae.question_sequence DESC LIMIT 1
                       ) AS is_correct,
                       (
                           SELECT qo.id FROM question_options qo
                           WHERE qo.question_id = q.id AND qo.is_correct = true
                           LIMIT 1
                       ) AS correct_option_id,
                       (
                           SELECT qo.option_text FROM question_options qo
                           WHERE qo.question_id = q.id AND qo.is_correct = true
                           LIMIT 1
                       ) AS correct_option_text
                FROM activity_questions aq
                JOIN questions q ON q.id = aq.question_id
                JOIN knowledge_components kc ON kc.id = q.knowledge_component_id
                WHERE aq.activity_id = $2
                ORDER BY aq.order_index ASC;
                """,
                attempt_id,
                attempt["activity_id"],
            )

            questions: list[AttemptQuestionReview] = []
            kc_counts: dict[str, dict[str, Any]] = {}

            for qr in q_rows:
                sel_opt_id = qr["selected_option_id"]
                sel_opt_text = "No respondida"
                if sel_opt_id:
                    sel_text_row = await conn.fetchval(
                        "SELECT option_text FROM question_options WHERE id = $1;",
                        sel_opt_id,
                    )
                    if sel_text_row:
                        sel_opt_text = sel_text_row

                is_corr = bool(qr["is_correct"]) if qr["is_correct"] is not None else False

                kc_id_str = str(qr["knowledge_component_id"])
                if kc_id_str not in kc_counts:
                    kc_counts[kc_id_str] = {
                        "kc_id": qr["knowledge_component_id"],
                        "kc_name": qr["kc_name"],
                        "total": 0,
                        "correct": 0,
                    }
                kc_counts[kc_id_str]["total"] += 1
                if is_corr:
                    kc_counts[kc_id_str]["correct"] += 1

                correct_opt_id = qr["correct_option_id"] if can_reveal_solutions else None
                correct_opt_text = qr["correct_option_text"] if can_reveal_solutions else None
                explanation = qr["explanation"] if can_reveal_solutions else "La retroalimentación y respuestas correctas estarán disponibles una vez concluido el plazo de entrega."

                questions.append(
                    AttemptQuestionReview(
                        question_id=qr["question_id"],
                        question_text=qr["question_text"],
                        knowledge_component_id=qr["knowledge_component_id"],
                        knowledge_component_name=qr["kc_name"],
                        selected_option_id=sel_opt_id,
                        selected_option_text=sel_opt_text,
                        is_correct=is_corr,
                        correct_option_id=correct_opt_id,
                        correct_option_text=correct_opt_text,
                        explanation=explanation,
                    )
                )

            kc_summaries = [
                KCResultSummary(
                    knowledge_component_id=kc["kc_id"],
                    knowledge_component_name=kc["kc_name"],
                    total_questions=kc["total"],
                    correct_answers=kc["correct"],
                    mastery_rate=round((kc["correct"] / kc["total"]) * 100.0, 1) if kc["total"] > 0 else 0.0,
                )
                for kc in kc_counts.values()
            ]

            return AttemptResultsResponse(
                attempt_id=attempt["id"],
                activity_id=attempt["activity_id"],
                activity_title=attempt["activity_title"],
                course_name=attempt["course_name"],
                student_id=attempt["student_id"],
                student_name=attempt["student_name"],
                started_at=attempt["started_at"],
                completed_at=attempt["completed_at"],
                score=float(attempt["score"] or 0.0),
                total_questions=attempt["total_questions"] or len(questions),
                correct_answers=attempt["correct_answers"] or sum(1 for q in questions if q.is_correct),
                questions=questions,
                kc_summaries=kc_summaries,
            )
