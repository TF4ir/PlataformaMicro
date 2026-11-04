"""Repository for microcontents and content exposure telemetry."""

from __future__ import annotations

import json
import logging
import uuid
from datetime import UTC, datetime
from typing import Any

import asyncpg

from app.schemas.microcontents import (
    MicrocontentCreateRequest,
    MicrocontentDetailResponse,
    MicrocontentListItem,
    MicrocontentUpdateRequest,
    RecordExposureRequest,
    RecordExposureResponse,
)

logger = logging.getLogger(__name__)


class MicrocontentRepository:
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def get_microcontent_by_id(
        self,
        tenant_id: uuid.UUID,
        microcontent_id: uuid.UUID,
        user_role: str,
        user_id: uuid.UUID,
    ) -> MicrocontentDetailResponse:
        """Fetch microcontent detail with KC and curricular hierarchy."""
        async with self.pool.acquire() as conn:
            query = """
                SELECT 
                    m.id,
                    m.tenant_id,
                    m.knowledge_component_id,
                    kc.name AS kc_name,
                    u.id AS unit_id,
                    u.title AS unit_title,
                    c.id AS course_id,
                    c.name AS course_name,
                    m.title,
                    m.content_type::text AS content_type,
                    m.content_body,
                    m.estimated_duration_seconds,
                    m.is_published,
                    m.created_at
                FROM microcontents m
                JOIN knowledge_components kc ON m.knowledge_component_id = kc.id
                LEFT JOIN units u ON kc.unit_id = u.id
                LEFT JOIN courses c ON u.course_id = c.id
                WHERE m.id = $1 AND m.tenant_id = $2
            """
            row = await conn.fetchrow(query, microcontent_id, tenant_id)
            if not row:
                raise KeyError(f"Microcontent {microcontent_id} not found in tenant.")

            # Visibility check
            if user_role == "student" and not row["is_published"]:
                raise PermissionError("This microcontent has not yet been published.")

            body_val = row["content_body"]
            if isinstance(body_val, str):
                try:
                    body_val = json.loads(body_val)
                except (json.JSONDecodeError, TypeError, ValueError):
                    body_val = {"raw": body_val}
            elif not isinstance(body_val, dict):
                body_val = {}

            return MicrocontentDetailResponse(
                id=row["id"],
                tenant_id=row["tenant_id"],
                knowledge_component_id=row["knowledge_component_id"],
                knowledge_component_name=row["kc_name"],
                unit_id=row["unit_id"],
                unit_title=row["unit_title"],
                course_id=row["course_id"],
                course_name=row["course_name"],
                title=row["title"],
                content_type=row["content_type"],
                content_body=body_val,
                estimated_duration_seconds=row["estimated_duration_seconds"],
                is_published=row["is_published"],
                created_at=row["created_at"],
            )

    async def record_exposure(
        self,
        tenant_id: uuid.UUID,
        student_id: uuid.UUID,
        microcontent_id: uuid.UUID,
        payload: RecordExposureRequest,
    ) -> RecordExposureResponse:
        """Persist exposure event to content_exposure_events (append-only) and complete recommendation if linked."""
        async with self.pool.acquire() as conn:
            # 1. Resolve student pseudonym
            pseudo = await conn.fetchval(
                "SELECT student_id_pseudo FROM enrollments WHERE student_id = $1 AND tenant_id = $2 LIMIT 1",
                student_id,
                tenant_id,
            )
            if not pseudo:
                pseudo = uuid.uuid4()

            # 2. Resolve KC ID from microcontent
            kc_id = await conn.fetchval(
                "SELECT knowledge_component_id FROM microcontents WHERE id = $1 AND tenant_id = $2",
                microcontent_id,
                tenant_id,
            )
            if not kc_id:
                raise KeyError(f"Microcontent {microcontent_id} does not exist in tenant.")

            # 3. Check idempotency on content_exposure_events
            existing_event = await conn.fetchrow(
                "SELECT id, event_timestamp FROM content_exposure_events WHERE idempotency_key = $1",
                payload.idempotency_key,
            )
            if existing_event:
                return RecordExposureResponse(
                    event_id=existing_event["id"],
                    microcontent_id=microcontent_id,
                    knowledge_component_id=kc_id,
                    exposure_type=payload.exposure_type,
                    recorded_at=existing_event["event_timestamp"],
                    recommendation_completed=False,
                )

            # 4. Insert into content_exposure_events
            event_id = uuid.uuid4()
            now = datetime.now(UTC)
            meta_json = json.dumps(payload.metadata or {})

            await conn.execute(
                """
                INSERT INTO content_exposure_events (
                    id, tenant_id, student_id, student_id_pseudo, microcontent_id,
                    knowledge_component_id, exposure_type, started_at, completed_at,
                    duration_seconds, active_reading_seconds, completion_status,
                    session_id, idempotency_key, metadata, event_timestamp, created_at
                ) VALUES (
                    $1, $2, $3, $4, $5,
                    $6, $7::exposure_type_enum, $8, $9,
                    $10, $11, $12::exposure_completion_status_enum,
                    $13, $14, $15::jsonb, $16, $16
                )
                """,
                event_id,
                tenant_id,
                student_id,
                pseudo,
                microcontent_id,
                kc_id,
                payload.exposure_type,
                payload.started_at,
                payload.completed_at or now,
                payload.duration_seconds,
                payload.active_reading_seconds or payload.duration_seconds,
                payload.completion_status,
                payload.session_id,
                payload.idempotency_key,
                meta_json,
                now,
            )

            # 5. Atomically complete recommendation if provided
            rec_completed = False
            if payload.recommendation_id:
                upd = await conn.execute(
                    """
                    UPDATE recommendations
                    SET status = 'completed'::recommendation_status_enum,
                        completed_at = $1
                    WHERE id = $2 AND student_id = $3 AND tenant_id = $4 AND status = 'pending'
                    """,
                    now,
                    payload.recommendation_id,
                    student_id,
                    tenant_id,
                )
                rec_completed = upd == "UPDATE 1"

            return RecordExposureResponse(
                event_id=event_id,
                microcontent_id=microcontent_id,
                knowledge_component_id=kc_id,
                exposure_type=payload.exposure_type,
                recorded_at=now,
                recommendation_completed=rec_completed,
            )

    async def list_microcontents(
        self,
        tenant_id: uuid.UUID,
        course_id: uuid.UUID | None = None,
        unit_id: uuid.UUID | None = None,
        kc_id: uuid.UUID | None = None,
    ) -> list[MicrocontentListItem]:
        """List microcontents matching tenant and optional curricular filters."""
        async with self.pool.acquire() as conn:
            query = """
                SELECT 
                    m.id,
                    m.tenant_id,
                    m.knowledge_component_id,
                    kc.name AS kc_name,
                    u.title AS unit_title,
                    c.name AS course_name,
                    m.title,
                    m.content_type::text AS content_type,
                    m.estimated_duration_seconds,
                    m.is_published,
                    m.created_by,
                    m.created_at
                FROM microcontents m
                JOIN knowledge_components kc ON m.knowledge_component_id = kc.id
                LEFT JOIN units u ON kc.unit_id = u.id
                LEFT JOIN courses c ON u.course_id = c.id
                WHERE m.tenant_id = $1
            """
            params: list[Any] = [tenant_id]
            idx = 2

            if course_id:
                query += f" AND c.id = ${idx}"
                params.append(course_id)
                idx += 1

            if unit_id:
                query += f" AND u.id = ${idx}"
                params.append(unit_id)
                idx += 1

            if kc_id:
                query += f" AND m.knowledge_component_id = ${idx}"
                params.append(kc_id)
                idx += 1

            query += " ORDER BY m.created_at DESC"
            rows = await conn.fetch(query, *params)

            return [
                MicrocontentListItem(
                    id=r["id"],
                    tenant_id=r["tenant_id"],
                    knowledge_component_id=r["knowledge_component_id"],
                    knowledge_component_name=r["kc_name"],
                    unit_title=r["unit_title"],
                    course_name=r["course_name"],
                    title=r["title"],
                    content_type=r["content_type"],
                    estimated_duration_seconds=r["estimated_duration_seconds"],
                    is_published=r["is_published"],
                    created_by=r["created_by"],
                    created_at=r["created_at"],
                )
                for r in rows
            ]

    async def create_microcontent(
        self,
        tenant_id: uuid.UUID,
        creator_id: uuid.UUID,
        payload: MicrocontentCreateRequest,
    ) -> MicrocontentDetailResponse:
        """Create draft microcontent."""
        async with self.pool.acquire() as conn:
            kc_row = await conn.fetchrow(
                """
                SELECT kc.name AS kc_name, u.id AS unit_id, u.title AS unit_title, c.id AS course_id, c.name AS course_name
                FROM knowledge_components kc
                LEFT JOIN units u ON kc.unit_id = u.id
                LEFT JOIN courses c ON u.course_id = c.id
                WHERE kc.id = $1 AND kc.tenant_id = $2
                """,
                payload.knowledge_component_id,
                tenant_id,
            )
            if not kc_row:
                raise KeyError(f"Knowledge Component {payload.knowledge_component_id} not found in tenant.")

            new_id = uuid.uuid4()
            now = datetime.now(UTC)
            body_json = json.dumps(payload.content_body)

            await conn.execute(
                """
                INSERT INTO microcontents (
                    id, tenant_id, knowledge_component_id, title, content_type,
                    content_body, estimated_duration_seconds, created_by, is_published, created_at
                ) VALUES (
                    $1, $2, $3, $4, $5::content_type_enum,
                    $6::jsonb, $7, $8, $9, $10
                )
                """,
                new_id,
                tenant_id,
                payload.knowledge_component_id,
                payload.title,
                payload.content_type,
                body_json,
                payload.estimated_duration_seconds,
                creator_id,
                payload.is_published,
                now,
            )

            return MicrocontentDetailResponse(
                id=new_id,
                tenant_id=tenant_id,
                knowledge_component_id=payload.knowledge_component_id,
                knowledge_component_name=kc_row["kc_name"],
                unit_id=kc_row["unit_id"],
                unit_title=kc_row["unit_title"],
                course_id=kc_row["course_id"],
                course_name=kc_row["course_name"],
                title=payload.title,
                content_type=payload.content_type,
                content_body=payload.content_body,
                estimated_duration_seconds=payload.estimated_duration_seconds,
                is_published=payload.is_published,
                created_at=now,
            )

    async def update_microcontent(
        self,
        tenant_id: uuid.UUID,
        microcontent_id: uuid.UUID,
        payload: MicrocontentUpdateRequest,
    ) -> MicrocontentDetailResponse:
        """Update draft microcontent."""
        async with self.pool.acquire() as conn:
            existing = await conn.fetchrow(
                "SELECT * FROM microcontents WHERE id = $1 AND tenant_id = $2",
                microcontent_id,
                tenant_id,
            )
            if not existing:
                raise KeyError(f"Microcontent {microcontent_id} not found.")

            title = payload.title if payload.title is not None else existing["title"]
            ctype = payload.content_type if payload.content_type is not None else existing["content_type"]
            body_val = payload.content_body if payload.content_body is not None else existing["content_body"]
            body_json = json.dumps(body_val) if isinstance(body_val, dict) else body_val
            duration = payload.estimated_duration_seconds if payload.estimated_duration_seconds is not None else existing["estimated_duration_seconds"]

            await conn.execute(
                """
                UPDATE microcontents
                SET title = $1,
                    content_type = $2::content_type_enum,
                    content_body = $3::jsonb,
                    estimated_duration_seconds = $4
                WHERE id = $5 AND tenant_id = $6
                """,
                title,
                ctype,
                body_json,
                duration,
                microcontent_id,
                tenant_id,
            )

            return await self.get_microcontent_by_id(
                tenant_id=tenant_id,
                microcontent_id=microcontent_id,
                user_role="teacher",
                user_id=existing["created_by"],
            )

    async def publish_microcontent(
        self,
        tenant_id: uuid.UUID,
        microcontent_id: uuid.UUID,
    ) -> MicrocontentDetailResponse:
        """Publish microcontent making it available to enrolled students."""
        async with self.pool.acquire() as conn:
            res = await conn.execute(
                "UPDATE microcontents SET is_published = true WHERE id = $1 AND tenant_id = $2",
                microcontent_id,
                tenant_id,
            )
            if res != "UPDATE 1":
                raise KeyError(f"Microcontent {microcontent_id} not found.")

            return await self.get_microcontent_by_id(
                tenant_id=tenant_id,
                microcontent_id=microcontent_id,
                user_role="teacher",
                user_id=uuid.uuid4(),
            )
