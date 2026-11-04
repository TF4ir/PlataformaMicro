"""PostgreSQL Repository for Activity and Questionnaire Management (Milestone M4)."""

import logging
from decimal import Decimal
from typing import Any
from uuid import UUID

import asyncpg

from app.schemas.activities import (
    ActivityCreateRequest,
    ActivityDetailResponse,
    ActivityListItem,
    ActivityQuestionDetail,
    ActivityResultsResponse,
    ActivitySectionDetail,
    ActivityStatus,
    ActivityType,
    ActivityUpdateRequest,
    AttemptStatus,
    CourseSectionItem,
    FeedbackPolicy,
    KCResultMetric,
    QuestionOptionDetail,
    QuestionResultMetric,
    SectionResultMetric,
    StudentAttemptSummary,
)

logger = logging.getLogger(__name__)


class ActivityRepository:
    """Handles persistence and transactional operations for Activities and Questionnaires."""

    def __init__(self, pool: asyncpg.Pool) -> None:
        self.pool = pool

    async def is_teacher_authorized_for_course(
        self,
        tenant_id: UUID,
        teacher_id: UUID,
        course_id: UUID,
    ) -> bool:
        """Verify if teacher is assigned to at least one section of the course."""
        async with self.pool.acquire() as conn:
            val = await conn.fetchval(
                """
                SELECT EXISTS (
                    SELECT 1 FROM sections s
                    WHERE s.course_id = $1 AND s.teacher_id = $2 AND s.tenant_id = $3
                );
                """,
                course_id,
                teacher_id,
                tenant_id,
            )
            return bool(val)

    async def _verify_teacher_course_access(
        self,
        tenant_id: UUID,
        course_id: UUID,
        user_id: UUID | None,
        role: str,
        authorized_course_ids: set[str] | None = None,
        created_by: UUID | None = None,
    ) -> None:
        if role in ("admin", "super_admin"):
            return
        if not user_id:
            return
        if created_by and str(created_by) == str(user_id):
            return
        if authorized_course_ids and (str(course_id) in authorized_course_ids):
            return
        is_auth = await self.is_teacher_authorized_for_course(tenant_id, user_id, course_id)
        if not is_auth:
            raise PermissionError(f"Teacher {user_id} is not authorized for course {course_id}.")

    async def list_course_sections(
        self,
        tenant_id: UUID,
        course_id: UUID,
        teacher_id: UUID | None = None,
        role: str = "teacher",
    ) -> list[CourseSectionItem]:
        """List sections for a course in the tenant."""
        async with self.pool.acquire() as conn:
            if role in ("admin", "super_admin"):
                rows = await conn.fetch(
                    "SELECT id, course_id, name, teacher_id, created_at FROM sections WHERE course_id = $1 AND tenant_id = $2 ORDER BY name ASC;",
                    course_id,
                    tenant_id,
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT id, course_id, name, teacher_id, created_at FROM sections 
                    WHERE course_id = $1 AND tenant_id = $2
                      AND (teacher_id = $3 OR NOT EXISTS (SELECT 1 FROM sections WHERE course_id = $1 AND teacher_id = $3))
                    ORDER BY name ASC;
                    """,
                    course_id,
                    tenant_id,
                    teacher_id,
                )
            return [
                CourseSectionItem(
                    id=r["id"],
                    course_id=r["course_id"],
                    name=r["name"],
                    teacher_id=r["teacher_id"],
                    created_at=r["created_at"],
                )
                for r in rows
            ]

    async def create_activity(
        self,
        tenant_id: UUID,
        created_by: UUID,
        payload: ActivityCreateRequest,
        role: str = "teacher",
        authorized_course_ids: set[str] | None = None,
    ) -> ActivityDetailResponse:
        """Create a new activity in draft status with sections and questions in a single transaction."""
        await self._verify_teacher_course_access(
            tenant_id=tenant_id,
            course_id=payload.course_id,
            user_id=created_by,
            role=role,
            authorized_course_ids=authorized_course_ids,
        )

        async with self.pool.acquire() as conn, conn.transaction():
            # 1. Validate course belongs to tenant
            course_row = await conn.fetchrow(
                "SELECT id, name FROM courses WHERE id = $1 AND tenant_id = $2 AND is_active = true;",
                payload.course_id,
                tenant_id,
            )
            if not course_row:
                raise ValueError(f"Course {payload.course_id} not found or inactive for tenant {tenant_id}.")

            # 2. Validate all section_ids belong to this course and tenant
            valid_sections = await conn.fetch(
                "SELECT id, name FROM sections WHERE id = ANY($1::uuid[]) AND course_id = $2 AND tenant_id = $3;",
                payload.section_ids,
                payload.course_id,
                tenant_id,
            )
            if len(valid_sections) != len(payload.section_ids):
                valid_ids = {r["id"] for r in valid_sections}
                missing = set(payload.section_ids) - valid_ids
                raise ValueError(f"Sections {missing} are invalid or do not belong to course {payload.course_id}.")

            # 3. Validate all question_ids exist, belong to tenant, are active and have options
            valid_questions = await conn.fetch(
                """
                SELECT q.id, q.question_text, q.question_type, q.difficulty,
                       q.knowledge_component_id, kc.name AS kc_name
                FROM questions q
                JOIN knowledge_components kc ON kc.id = q.knowledge_component_id
                WHERE q.id = ANY($1::uuid[])
                  AND q.tenant_id = $2
                  AND q.is_active = true;
                """,
                payload.question_ids,
                tenant_id,
            )
            if len(valid_questions) != len(payload.question_ids):
                found_ids = {r["id"] for r in valid_questions}
                missing = set(payload.question_ids) - found_ids
                raise ValueError(f"Questions {missing} are unapproved, inactive, or not in the canonical bank.")

            # 4. Insert into activities
            activity_row = await conn.fetchrow(
                """
                INSERT INTO activities (
                    tenant_id, course_id, created_by, title, description,
                    activity_type, status, feedback_policy, max_attempts,
                    time_limit_minutes, available_from, available_until, is_active
                ) VALUES (
                    $1, $2, $3, $4, $5,
                    $6::activity_type_enum, 'draft'::activity_status_enum,
                    $7::feedback_policy_enum, $8,
                    $9, $10, $11, true
                )
                RETURNING id, created_at, updated_at;
                """,
                tenant_id,
                payload.course_id,
                created_by,
                payload.title,
                payload.description,
                payload.activity_type.value,
                payload.feedback_policy.value,
                payload.max_attempts,
                payload.time_limit_minutes,
                payload.available_from,
                payload.available_until,
            )
            activity_id = activity_row["id"]

            # 5. Insert activity_sections
            section_records = [
                (tenant_id, activity_id, sec_id) for sec_id in payload.section_ids
            ]
            await conn.executemany(
                """
                INSERT INTO activity_sections (tenant_id, activity_id, section_id)
                VALUES ($1, $2, $3)
                ON CONFLICT (activity_id, section_id) DO NOTHING;
                """,
                section_records,
            )

            # 6. Insert activity_questions preserving ordering
            question_records = [
                (activity_id, q_id, idx + 1)
                for idx, q_id in enumerate(payload.question_ids)
            ]
            await conn.executemany(
                """
                INSERT INTO activity_questions (activity_id, question_id, order_index)
                VALUES ($1, $2, $3)
                ON CONFLICT (activity_id, question_id) DO UPDATE SET order_index = EXCLUDED.order_index;
                """,
                question_records,
            )

        return await self.get_activity_by_id(tenant_id, activity_id)

    async def update_activity(
        self,
        tenant_id: UUID,
        activity_id: UUID,
        payload: ActivityUpdateRequest,
        user_id: UUID | None = None,
        role: str = "teacher",
        authorized_course_ids: set[str] | None = None,
    ) -> ActivityDetailResponse:
        """Update activity metadata or question associations (only if allowed)."""
        async with self.pool.acquire() as conn, conn.transaction():
            # Check activity existence
            current = await conn.fetchrow(
                "SELECT id, course_id, status, created_by FROM activities WHERE id = $1 AND tenant_id = $2;",
                activity_id,
                tenant_id,
            )
            if not current:
                raise KeyError(f"Activity {activity_id} not found.")

            await self._verify_teacher_course_access(
                tenant_id=tenant_id,
                course_id=current["course_id"],
                user_id=user_id,
                role=role,
                authorized_course_ids=authorized_course_ids,
                created_by=current["created_by"],
            )


            if current["status"] == "closed":
                raise ValueError("Cannot modify a closed activity.")

            # If modifying questions, check if any attempts exist
            if payload.question_ids is not None:
                attempts_count = await conn.fetchval(
                    "SELECT COUNT(*) FROM quiz_attempts WHERE activity_id = $1;",
                    activity_id,
                )
                if attempts_count > 0:
                    raise ValueError("Cannot alter questions for an activity that already has registered student attempts.")

                # Validate new questions
                valid_questions = await conn.fetch(
                    "SELECT id FROM questions WHERE id = ANY($1::uuid[]) AND tenant_id = $2 AND is_active = true;",
                    payload.question_ids,
                    tenant_id,
                )
                if len(valid_questions) != len(payload.question_ids):
                    raise ValueError("Some questions are invalid or inactive.")

                # Replace activity_questions
                await conn.execute("DELETE FROM activity_questions WHERE activity_id = $1;", activity_id)
                question_records = [
                    (activity_id, q_id, idx + 1)
                    for idx, q_id in enumerate(payload.question_ids)
                ]
                await conn.executemany(
                    "INSERT INTO activity_questions (activity_id, question_id, order_index) VALUES ($1, $2, $3);",
                    question_records,
                )

            # If modifying sections
            if payload.section_ids is not None:
                valid_sections = await conn.fetch(
                    "SELECT id FROM sections WHERE id = ANY($1::uuid[]) AND course_id = $2 AND tenant_id = $3;",
                    payload.section_ids,
                    current["course_id"],
                    tenant_id,
                )
                if len(valid_sections) != len(payload.section_ids):
                    raise ValueError("Some sections are invalid.")

                await conn.execute("DELETE FROM activity_sections WHERE activity_id = $1;", activity_id)
                section_records = [
                    (tenant_id, activity_id, sec_id) for sec_id in payload.section_ids
                ]
                await conn.executemany(
                    "INSERT INTO activity_sections (tenant_id, activity_id, section_id) VALUES ($1, $2, $3);",
                    section_records,
                )

            # Update core fields if provided
            updates = []
            params: list[Any] = [activity_id, tenant_id]

            def add_update(col: str, val: Any) -> None:
                nonlocal params
                if val is not None:
                    params.append(val)
                    updates.append(f"{col} = ${len(params)}")

            add_update("title", payload.title)
            add_update("description", payload.description)
            if payload.activity_type:
                add_update("activity_type", payload.activity_type.value)
            if payload.feedback_policy:
                add_update("feedback_policy", payload.feedback_policy.value)
            add_update("max_attempts", payload.max_attempts)
            add_update("time_limit_minutes", payload.time_limit_minutes)
            add_update("available_from", payload.available_from)
            add_update("available_until", payload.available_until)

            if updates:
                query = f"""
                UPDATE activities
                SET {', '.join(updates)}, updated_at = now()
                WHERE id = $1 AND tenant_id = $2;
                """
                await conn.execute(query, *params)

        return await self.get_activity_by_id(tenant_id, activity_id)

    async def publish_activity(
        self,
        tenant_id: UUID,
        activity_id: UUID,
        user_id: UUID | None = None,
        role: str = "teacher",
        authorized_course_ids: set[str] | None = None,
    ) -> ActivityDetailResponse:
        """Atomically transition activity to published status."""
        async with self.pool.acquire() as conn, conn.transaction():
            activity = await conn.fetchrow(
                "SELECT id, course_id, status, created_by FROM activities WHERE id = $1 AND tenant_id = $2;",
                activity_id,
                tenant_id,
            )
            if not activity:
                raise KeyError(f"Activity {activity_id} not found.")

            await self._verify_teacher_course_access(
                tenant_id=tenant_id,
                course_id=activity["course_id"],
                user_id=user_id,
                role=role,
                authorized_course_ids=authorized_course_ids,
                created_by=activity["created_by"],
            )


            # Check question count >= 1
            q_count = await conn.fetchval(
                "SELECT COUNT(*) FROM activity_questions WHERE activity_id = $1;",
                activity_id,
            )
            if q_count == 0:
                raise ValueError("Cannot publish an activity with zero questions.")

            # Check section count >= 1
            s_count = await conn.fetchval(
                "SELECT COUNT(*) FROM activity_sections WHERE activity_id = $1;",
                activity_id,
            )
            if s_count == 0:
                raise ValueError("Cannot publish an activity with zero target sections.")

            await conn.execute(
                """
                UPDATE activities
                SET status = 'published'::activity_status_enum,
                    published_at = COALESCE(published_at, now()),
                    updated_at = now()
                WHERE id = $1 AND tenant_id = $2;
                """,
                activity_id,
                tenant_id,
            )

        return await self.get_activity_by_id(tenant_id, activity_id)

    async def list_teacher_activities(
        self,
        tenant_id: UUID,
        teacher_id: UUID,
        role: str,
        course_id: UUID | None = None,
        status: ActivityStatus | None = None,
    ) -> list[ActivityListItem]:
        """List activities for teacher's courses with metrics."""
        async with self.pool.acquire() as conn:
            where_clauses = ["a.tenant_id = $1"]
            params: list[Any] = [tenant_id]

            if role != "admin" and role != "super_admin":
                # Only courses where teacher is assigned to at least one section OR created the activity
                params.append(teacher_id)
                where_clauses.append(
                    f"""(
                        a.created_by = ${len(params)} OR
                        EXISTS (
                            SELECT 1 FROM sections s 
                            WHERE s.course_id = a.course_id AND s.teacher_id = ${len(params)}
                        )
                    )"""
                )

            if course_id:
                params.append(course_id)
                where_clauses.append(f"a.course_id = ${len(params)}")

            if status:
                params.append(status.value)
                where_clauses.append(f"a.status = ${len(params)}::activity_status_enum")

            where_sql = " AND ".join(where_clauses)
            query = f"""
            SELECT a.id, a.tenant_id, a.course_id, c.name AS course_name,
                   a.title, a.description, a.activity_type::text, a.status::text,
                   a.feedback_policy::text, a.max_attempts, a.time_limit_minutes,
                   a.available_from, a.available_until, a.published_at,
                   a.created_by, a.created_at, a.updated_at,
                   (SELECT COUNT(*) FROM activity_questions aq WHERE aq.activity_id = a.id) AS questions_count,
                   (SELECT COUNT(*) FROM activity_sections acts WHERE acts.activity_id = a.id) AS sections_count,
                   (SELECT COUNT(*) FROM quiz_attempts qa WHERE qa.activity_id = a.id) AS attempts_count
            FROM activities a
            JOIN courses c ON c.id = a.course_id
            WHERE {where_sql}
            ORDER BY a.created_at DESC;
            """
            rows = await conn.fetch(query, *params)

            # Also fetch sections for each activity
            results: list[ActivityListItem] = []
            for row in rows:
                act_id = row["id"]
                sec_rows = await conn.fetch(
                    """
                    SELECT s.id AS section_id, s.name AS section_name
                    FROM activity_sections acts
                    JOIN sections s ON s.id = acts.section_id
                    WHERE acts.activity_id = $1;
                    """,
                    act_id,
                )
                sections = [
                    ActivitySectionDetail(section_id=sr["section_id"], section_name=sr["section_name"])
                    for sr in sec_rows
                ]

                results.append(
                    ActivityListItem(
                        id=row["id"],
                        tenant_id=row["tenant_id"],
                        course_id=row["course_id"],
                        course_name=row["course_name"],
                        title=row["title"],
                        description=row["description"],
                        activity_type=ActivityType(row["activity_type"]),
                        status=ActivityStatus(row["status"]),
                        feedback_policy=FeedbackPolicy(row["feedback_policy"]),
                        max_attempts=row["max_attempts"],
                        time_limit_minutes=row["time_limit_minutes"],
                        available_from=row["available_from"],
                        available_until=row["available_until"],
                        published_at=row["published_at"],
                        created_by=row["created_by"],
                        created_at=row["created_at"],
                        updated_at=row["updated_at"],
                        questions_count=row["questions_count"],
                        sections_count=row["sections_count"],
                        attempts_count=row["attempts_count"],
                        sections=sections,
                    )
                )

            return results

    async def get_activity_by_id(
        self,
        tenant_id: UUID,
        activity_id: UUID,
        user_id: UUID | None = None,
        role: str = "teacher",
        authorized_course_ids: set[str] | None = None,
    ) -> ActivityDetailResponse:
        """Fetch full activity details including questions and options."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT a.id, a.tenant_id, a.course_id, c.name AS course_name,
                       a.title, a.description, a.activity_type::text, a.status::text,
                       a.feedback_policy::text, a.max_attempts, a.time_limit_minutes,
                       a.available_from, a.available_until, a.published_at,
                       a.created_by, a.created_at, a.updated_at,
                       (SELECT COUNT(*) FROM activity_questions aq WHERE aq.activity_id = a.id) AS questions_count,
                       (SELECT COUNT(*) FROM activity_sections acts WHERE acts.activity_id = a.id) AS sections_count,
                       (SELECT COUNT(*) FROM quiz_attempts qa WHERE qa.activity_id = a.id) AS attempts_count
                FROM activities a
                JOIN courses c ON c.id = a.course_id
                WHERE a.id = $1 AND a.tenant_id = $2;
                """,
                activity_id,
                tenant_id,
            )
            if not row:
                raise KeyError(f"Activity {activity_id} not found.")

            await self._verify_teacher_course_access(
                tenant_id=tenant_id,
                course_id=row["course_id"],
                user_id=user_id,
                role=role,
                authorized_course_ids=authorized_course_ids,
                created_by=row["created_by"],
            )


            # Sections
            sec_rows = await conn.fetch(
                """
                SELECT s.id AS section_id, s.name AS section_name
                FROM activity_sections acts
                JOIN sections s ON s.id = acts.section_id
                WHERE acts.activity_id = $1;
                """,
                activity_id,
            )
            sections = [
                ActivitySectionDetail(section_id=sr["section_id"], section_name=sr["section_name"])
                for sr in sec_rows
            ]

            # Questions with KCs and options
            q_rows = await conn.fetch(
                """
                SELECT aq.order_index, q.id AS question_id, q.question_text,
                       q.question_type, q.difficulty, q.knowledge_component_id,
                       kc.name AS kc_name
                FROM activity_questions aq
                JOIN questions q ON q.id = aq.question_id
                JOIN knowledge_components kc ON kc.id = q.knowledge_component_id
                WHERE aq.activity_id = $1
                ORDER BY aq.order_index ASC;
                """,
                activity_id,
            )

            questions: list[ActivityQuestionDetail] = []
            for qr in q_rows:
                q_id = qr["question_id"]
                opt_rows = await conn.fetch(
                    """
                    SELECT id, option_text, is_correct, order_index
                    FROM question_options
                    WHERE question_id = $1
                    ORDER BY order_index ASC;
                    """,
                    q_id,
                )
                options = [
                    QuestionOptionDetail(
                        id=opt["id"],
                        option_text=opt["option_text"],
                        is_correct=opt["is_correct"],
                        order_index=opt["order_index"],
                    )
                    for opt in opt_rows
                ]

                diff = qr["difficulty"]
                diff_val = float(diff) if isinstance(diff, (Decimal, int, float)) else 0.5

                questions.append(
                    ActivityQuestionDetail(
                        question_id=qr["question_id"],
                        question_text=qr["question_text"],
                        question_type=qr["question_type"],
                        knowledge_component_id=qr["knowledge_component_id"],
                        knowledge_component_name=qr["kc_name"],
                        difficulty=diff_val,
                        order_index=qr["order_index"],
                        options=options,
                    )
                )

            return ActivityDetailResponse(
                id=row["id"],
                tenant_id=row["tenant_id"],
                course_id=row["course_id"],
                course_name=row["course_name"],
                title=row["title"],
                description=row["description"],
                activity_type=ActivityType(row["activity_type"]),
                status=ActivityStatus(row["status"]),
                feedback_policy=FeedbackPolicy(row["feedback_policy"]),
                max_attempts=row["max_attempts"],
                time_limit_minutes=row["time_limit_minutes"],
                available_from=row["available_from"],
                available_until=row["available_until"],
                published_at=row["published_at"],
                created_by=row["created_by"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                questions_count=row["questions_count"],
                sections_count=row["sections_count"],
                attempts_count=row["attempts_count"],
                sections=sections,
                questions=questions,
            )

    async def get_activity_results(
        self,
        tenant_id: UUID,
        activity_id: UUID,
        user_id: UUID | None = None,
        role: str = "teacher",
        authorized_course_ids: set[str] | None = None,
    ) -> ActivityResultsResponse:
        """Calculate aggregated results and student attempts breakdown for teacher analytics."""
        async with self.pool.acquire() as conn:
            act_row = await conn.fetchrow(
                """
                SELECT a.id, a.title, a.course_id, a.created_by, c.name AS course_name
                FROM activities a
                JOIN courses c ON c.id = a.course_id
                WHERE a.id = $1 AND a.tenant_id = $2;
                """,
                activity_id,
                tenant_id,
            )
            if not act_row:
                raise KeyError(f"Activity {activity_id} not found.")

            await self._verify_teacher_course_access(
                tenant_id=tenant_id,
                course_id=act_row["course_id"],
                user_id=user_id,
                role=role,
                authorized_course_ids=authorized_course_ids,
                created_by=act_row["created_by"],
            )


            # Total enrolled students across all assigned sections
            total_enrolled = await conn.fetchval(
                """
                SELECT COUNT(DISTINCT e.student_id)
                FROM activity_sections acts
                JOIN enrollments e ON e.section_id = acts.section_id
                WHERE acts.activity_id = $1;
                """,
                activity_id,
            ) or 0

            # Attempts metrics
            attempt_stats = await conn.fetchrow(
                """
                SELECT COUNT(*) AS total_attempts,
                       COUNT(*) FILTER (WHERE status = 'completed') AS completed_attempts,
                       COUNT(DISTINCT student_id) AS participating_students,
                       COALESCE(AVG(score) FILTER (WHERE status = 'completed'), 0.0) AS avg_score
                FROM quiz_attempts
                WHERE activity_id = $1;
                """,
                activity_id,
            )
            total_attempts = attempt_stats["total_attempts"]
            completed_attempts = attempt_stats["completed_attempts"]
            participating_students = attempt_stats["participating_students"]
            avg_score = float(attempt_stats["avg_score"] or 0.0)
            part_rate = (
                round((participating_students / total_enrolled) * 100.0, 1)
                if total_enrolled > 0
                else 0.0
            )

            # Breakdown per section
            sec_breakdown_rows = await conn.fetch(
                """
                SELECT s.id AS section_id, s.name AS section_name,
                       COUNT(DISTINCT e.student_id) AS enrolled_count,
                       COUNT(DISTINCT qa.student_id) AS participating_students,
                       COUNT(qa.id) FILTER (WHERE qa.status = 'completed') AS completed_attempts,
                       COALESCE(AVG(qa.score) FILTER (WHERE qa.status = 'completed'), 0.0) AS average_score
                FROM activity_sections acts
                JOIN sections s ON s.id = acts.section_id
                LEFT JOIN enrollments e ON e.section_id = s.id
                LEFT JOIN quiz_attempts qa ON qa.enrollment_id = e.id AND qa.activity_id = acts.activity_id
                WHERE acts.activity_id = $1
                GROUP BY s.id, s.name
                ORDER BY s.name ASC;
                """,
                activity_id,
            )
            sections_breakdown = [
                SectionResultMetric(
                    section_id=sb["section_id"],
                    section_name=sb["section_name"],
                    enrolled_count=sb["enrolled_count"],
                    participating_students=sb["participating_students"],
                    completed_attempts=sb["completed_attempts"],
                    average_score=round(float(sb["average_score"]), 2),
                )
                for sb in sec_breakdown_rows
            ]

            # Breakdown per question (using latest answer per attempt to avoid interaction skew)
            q_breakdown_rows = await conn.fetch(
                """
                WITH latest_events AS (
                    SELECT DISTINCT ON (ae.attempt_id, ae.question_id)
                           ae.question_id, ae.is_correct
                    FROM answer_events ae
                    WHERE ae.activity_id = $1
                    ORDER BY ae.attempt_id, ae.question_id, ae.event_timestamp DESC, ae.question_sequence DESC
                )
                SELECT aq.order_index, q.id AS question_id, q.question_text,
                       q.knowledge_component_id, kc.name AS kc_name,
                       COUNT(le.question_id) AS total_answers,
                       COUNT(le.question_id) FILTER (WHERE le.is_correct = true) AS correct_answers
                FROM activity_questions aq
                JOIN questions q ON q.id = aq.question_id
                JOIN knowledge_components kc ON kc.id = q.knowledge_component_id
                LEFT JOIN latest_events le ON le.question_id = q.id
                WHERE aq.activity_id = $1
                GROUP BY aq.order_index, q.id, q.question_text, q.knowledge_component_id, kc.name
                ORDER BY aq.order_index ASC;
                """,
                activity_id,
            )
            questions_breakdown = [
                QuestionResultMetric(
                    question_id=qb["question_id"],
                    question_text=qb["question_text"],
                    knowledge_component_id=qb["knowledge_component_id"],
                    knowledge_component_name=qb["kc_name"],
                    total_answers=qb["total_answers"],
                    correct_answers=qb["correct_answers"],
                    accuracy_rate=(
                        round((qb["correct_answers"] / qb["total_answers"]) * 100.0, 1)
                        if qb["total_answers"] > 0
                        else 0.0
                    ),
                    order_index=qb["order_index"],
                )
                for qb in q_breakdown_rows
            ]

            # Breakdown per Knowledge Component (using latest answer per attempt)
            kc_breakdown_rows = await conn.fetch(
                """
                WITH latest_events AS (
                    SELECT DISTINCT ON (ae.attempt_id, ae.question_id)
                           ae.knowledge_component_id, ae.is_correct
                    FROM answer_events ae
                    WHERE ae.activity_id = $1
                    ORDER BY ae.attempt_id, ae.question_id, ae.event_timestamp DESC, ae.question_sequence DESC
                )
                SELECT kc.id AS kc_id, kc.name AS kc_name,
                       COUNT(le.knowledge_component_id) AS total_answers,
                       COUNT(le.knowledge_component_id) FILTER (WHERE le.is_correct = true) AS correct_answers
                FROM activity_questions aq
                JOIN questions q ON q.id = aq.question_id
                JOIN knowledge_components kc ON kc.id = q.knowledge_component_id
                LEFT JOIN latest_events le ON le.knowledge_component_id = kc.id
                WHERE aq.activity_id = $1
                GROUP BY kc.id, kc.name
                ORDER BY kc.name ASC;
                """,
                activity_id,
            )
            kc_breakdown = [
                KCResultMetric(
                    knowledge_component_id=kcb["kc_id"],
                    knowledge_component_name=kcb["kc_name"],
                    total_answers=kcb["total_answers"],
                    correct_answers=kcb["correct_answers"],
                    mastery_rate=(
                        round((kcb["correct_answers"] / kcb["total_answers"]) * 100.0, 1)
                        if kcb["total_answers"] > 0
                        else 0.0
                    ),
                )
                for kcb in kc_breakdown_rows
            ]

            # Student attempts list
            attempts_rows = await conn.fetch(
                """
                SELECT qa.id AS attempt_id, qa.student_id, p.full_name AS student_name,
                       p.student_code, s.name AS section_name, qa.attempt_number,
                       qa.status::text, qa.score, qa.started_at, qa.completed_at,
                       qa.total_questions, qa.correct_answers
                FROM quiz_attempts qa
                JOIN profiles p ON p.id = qa.student_id
                JOIN enrollments e ON e.id = qa.enrollment_id
                JOIN sections s ON s.id = e.section_id
                WHERE qa.activity_id = $1
                ORDER BY qa.started_at DESC;
                """,
                activity_id,
            )
            student_attempts = [
                StudentAttemptSummary(
                    attempt_id=ar["attempt_id"],
                    student_id=ar["student_id"],
                    student_name=ar["student_name"],
                    student_code=ar["student_code"],
                    section_name=ar["section_name"],
                    attempt_number=ar["attempt_number"],
                    status=AttemptStatus(ar["status"]),
                    score=float(ar["score"]) if ar["score"] is not None else None,
                    started_at=ar["started_at"],
                    completed_at=ar["completed_at"],
                    total_questions=ar["total_questions"],
                    correct_answers=ar["correct_answers"],
                )
                for ar in attempts_rows
            ]

            return ActivityResultsResponse(
                activity_id=act_row["id"],
                activity_title=act_row["title"],
                course_id=act_row["course_id"],
                course_name=act_row["course_name"],
                total_enrolled=total_enrolled,
                total_attempts=total_attempts,
                completed_attempts=completed_attempts,
                participation_rate=part_rate,
                average_score=round(avg_score, 2),
                sections_breakdown=sections_breakdown,
                questions_breakdown=questions_breakdown,
                kc_breakdown=kc_breakdown,
                student_attempts=student_attempts,
            )
