"""History builder for longitudinal student retention modeling.

Queries content_exposure_events and answer_events to reconstruct a deterministic,
strictly causal chronological sequence of learning interactions per student and KC.
"""

from __future__ import annotations

import json
import sys
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import asyncpg

# Ensure monorepo root is on sys.path for ml.* package discovery
_curr = Path(__file__).resolve().parent
_repo_root = next((p for p in [_curr, *_curr.parents] if (p / "ml").is_dir()), None)
if _repo_root is not None and str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from ml.src.contracts.exposure_contract import StudentInteractionEvent


def _parse_metadata(val: Any) -> dict[str, Any]:
    if isinstance(val, dict):
        return val
    if isinstance(val, str) and val.strip():
        try:
            parsed = json.loads(val)
            if isinstance(parsed, dict):
                return parsed
        except (json.JSONDecodeError, TypeError, ValueError):
            return {}
    return {}


@dataclass
class UnifiedInteractionRecord:
    """Raw unified interaction event from PostgreSQL."""

    id: uuid.UUID
    event_timestamp: datetime
    created_at: datetime
    event_category: str  # 'exposure' or 'retrieval'
    event_subtype: str   # 'initial_study', 'review_study', 'question_answer', etc.
    knowledge_component_id: uuid.UUID
    is_correct: bool | None
    duration_seconds: float
    question_difficulty: float
    is_delayed_assessment: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class StudentKCHistorySummary:
    """Aggregated timeline summary for a specific (student, KC) pair."""

    knowledge_component_id: uuid.UUID
    knowledge_component_name: str
    kc_difficulty_prior: float
    total_exposures: int
    total_retrieval_attempts: int
    total_successes: int
    total_failures: int
    first_exposure_at: datetime | None
    last_exposure_at: datetime | None
    last_retrieval_at: datetime | None
    last_interaction_at: datetime | None
    interaction_events: list[StudentInteractionEvent] = field(default_factory=list)


class UnifiedHistoryBuilder:
    """Reconstructs causal chronological histories from PostgreSQL."""

    async def fetch_student_kc_history(
        self,
        pool: asyncpg.Pool,
        student_id: uuid.UUID,
        tenant_id: uuid.UUID,
        knowledge_component_id: uuid.UUID | None = None,
        reference_time: datetime | None = None,
    ) -> dict[uuid.UUID, StudentKCHistorySummary]:
        """Fetch and assemble unified learning histories grouped by Knowledge Component.

        Enforces:
        1. Strict Anti-Leakage: event_timestamp < reference_time.
        2. Deterministic Tie-Breaking: ORDER BY event_timestamp ASC, created_at ASC, id ASC.
        3. Excludes future delayed assessments.
        """
        if reference_time is None:
            reference_time = datetime.now(UTC)

        async with pool.acquire() as conn:
            # 1. Fetch accessible KCs for the student's enrolled courses
            kc_query = """
                SELECT DISTINCT 
                    kc.id AS kc_id,
                    kc.name AS kc_name,
                    kc.difficulty_prior
                FROM enrollments e
                JOIN sections s ON e.section_id = s.id
                JOIN units u ON s.course_id = u.course_id
                JOIN knowledge_components kc ON u.id = kc.unit_id
                WHERE e.student_id = $1 AND e.tenant_id = $2
            """
            params: list[Any] = [student_id, tenant_id]
            if knowledge_component_id is not None:
                kc_query += " AND kc.id = $3"
                params.append(knowledge_component_id)

            kc_rows = await conn.fetch(kc_query, *params)
            kc_map: dict[uuid.UUID, tuple[str, float]] = {
                r["kc_id"]: (r["kc_name"], float(r["difficulty_prior"])) for r in kc_rows
            }

            if not kc_map:
                return {}

            # 2. Query content_exposure_events (strictly causal: event_timestamp < reference_time)
            exposure_sql = """
                SELECT 
                    id,
                    event_timestamp,
                    created_at,
                    'exposure' AS event_category,
                    exposure_type::text AS event_subtype,
                    knowledge_component_id,
                    NULL::boolean AS is_correct,
                    duration_seconds,
                    0.50::float AS question_difficulty,
                    false AS is_delayed_assessment,
                    metadata
                FROM content_exposure_events
                WHERE student_id = $1 AND tenant_id = $2 AND event_timestamp < $3
            """
            exp_params: list[Any] = [student_id, tenant_id, reference_time]
            if knowledge_component_id is not None:
                exposure_sql += " AND knowledge_component_id = $4"
                exp_params.append(knowledge_component_id)

            exposure_rows = await conn.fetch(exposure_sql, *exp_params)

            # 3. Query answer_events (strictly causal: event_timestamp < reference_time)
            answer_sql = """
                SELECT 
                    ae.id,
                    ae.event_timestamp,
                    ae.event_timestamp AS created_at,
                    'retrieval' AS event_category,
                    'question_answer' AS event_subtype,
                    ae.knowledge_component_id,
                    ae.is_correct,
                    ae.response_time_seconds::float AS duration_seconds,
                    COALESCE(q.difficulty, 0.50)::float AS question_difficulty,
                    COALESCE(act.activity_type = 'delayed_assessment', false) AS is_delayed_assessment,
                    '{}'::jsonb AS metadata
                FROM answer_events ae
                LEFT JOIN questions q ON ae.question_id = q.id
                LEFT JOIN activities act ON ae.activity_id = act.id
                WHERE ae.student_id = $1 AND ae.tenant_id = $2 AND ae.event_timestamp < $3
            """
            ans_params: list[Any] = [student_id, tenant_id, reference_time]
            if knowledge_component_id is not None:
                answer_sql += " AND ae.knowledge_component_id = $4"
                ans_params.append(knowledge_component_id)

            answer_rows = await conn.fetch(answer_sql, *ans_params)

        # 4. Merge and sort deterministically
        all_records: list[UnifiedInteractionRecord] = []
        for r in exposure_rows:
            all_records.append(
                UnifiedInteractionRecord(
                    id=r["id"],
                    event_timestamp=r["event_timestamp"],
                    created_at=r["created_at"],
                    event_category=r["event_category"],
                    event_subtype=r["event_subtype"],
                    knowledge_component_id=r["knowledge_component_id"],
                    is_correct=r["is_correct"],
                    duration_seconds=float(r["duration_seconds"] or 0.0),
                    question_difficulty=float(r["question_difficulty"] or 0.50),
                    is_delayed_assessment=r["is_delayed_assessment"],
                    metadata=_parse_metadata(r["metadata"]),
                )
            )

        for r in answer_rows:
            all_records.append(
                UnifiedInteractionRecord(
                    id=r["id"],
                    event_timestamp=r["event_timestamp"],
                    created_at=r["created_at"],
                    event_category=r["event_category"],
                    event_subtype=r["event_subtype"],
                    knowledge_component_id=r["knowledge_component_id"],
                    is_correct=r["is_correct"],
                    duration_seconds=float(r["duration_seconds"] or 0.0),
                    question_difficulty=float(r["question_difficulty"] or 0.50),
                    is_delayed_assessment=r["is_delayed_assessment"],
                    metadata=_parse_metadata(r["metadata"]),
                )
            )

        # Deterministic sorting: timestamp ASC, created_at ASC, id ASC
        all_records.sort(key=lambda x: (x.event_timestamp, x.created_at, x.id))

        # 5. Group by KC and compute metrics
        summaries: dict[uuid.UUID, StudentKCHistorySummary] = {}
        for kc_id, (kc_name, diff_prior) in kc_map.items():
            kc_records = [rec for rec in all_records if rec.knowledge_component_id == kc_id]

            exp_count = sum(1 for r in kc_records if r.event_category == "exposure")
            ret_count = sum(1 for r in kc_records if r.event_category == "retrieval")
            succ_count = sum(1 for r in kc_records if r.event_category == "retrieval" and r.is_correct is True)
            fail_count = sum(1 for r in kc_records if r.event_category == "retrieval" and r.is_correct is False)

            exp_times = [r.event_timestamp for r in kc_records if r.event_category == "exposure"]
            ret_times = [r.event_timestamp for r in kc_records if r.event_category == "retrieval"]

            first_exp = min(exp_times) if exp_times else None
            last_exp = max(exp_times) if exp_times else None
            last_ret = max(ret_times) if ret_times else None
            last_any = max([r.event_timestamp for r in kc_records]) if kc_records else None

            # Convert retrieval events into StudentInteractionEvent for ML models
            interaction_events: list[StudentInteractionEvent] = []
            for rec in kc_records:
                if rec.event_category == "retrieval" and rec.is_correct is not None:
                    interaction_events.append(
                        StudentInteractionEvent(
                            event_id=rec.id,
                            student_id_pseudo=str(student_id),
                            kc_id=str(kc_id),
                            question_id=str(rec.id),
                            event_timestamp=rec.event_timestamp,
                            is_correct=1 if rec.is_correct else 0,
                            response_time_seconds=max(0.1, rec.duration_seconds),
                            activity_type="delayed_assessment" if rec.is_delayed_assessment else "practice",
                            question_difficulty=rec.question_difficulty,
                        )
                    )

            summaries[kc_id] = StudentKCHistorySummary(
                knowledge_component_id=kc_id,
                knowledge_component_name=kc_name,
                kc_difficulty_prior=diff_prior,
                total_exposures=exp_count,
                total_retrieval_attempts=ret_count,
                total_successes=succ_count,
                total_failures=fail_count,
                first_exposure_at=first_exp,
                last_exposure_at=last_exp,
                last_retrieval_at=last_ret,
                last_interaction_at=last_any,
                interaction_events=interaction_events,
            )

        return summaries
