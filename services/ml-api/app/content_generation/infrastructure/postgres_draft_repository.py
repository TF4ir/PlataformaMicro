"""PostgreSQL adapter for Question Drafts repository in quarantine.

Enforces:
- Multi-tenant boundary isolation.
- Idempotency on retry with content hashing and clean unreviewed draft replacement.
- Protection against overwriting teacher-reviewed drafts (edited, approved, rejected).
"""

import json
import logging
import uuid
from decimal import Decimal
from typing import Any

import asyncpg

from app.content_generation.exceptions import (
    DraftAlreadyReviewedError,
    EmptyDraftsError,
    JobNotFoundError,
)
from app.content_generation.repositories.draft_repository import (
    DraftRepositoryProtocol,
)
from app.content_generation.schemas.generated_questions import (
    GeneratedQuestionDraft,
    QuestionDraftRecord,
    compute_draft_content_hash,
)

logger = logging.getLogger(__name__)


def _deserialize_json(val: Any) -> Any:
    """Deserialize JSON data if returned as string by asyncpg."""
    if isinstance(val, str):
        try:
            return json.loads(val)
        except json.JSONDecodeError:
            return val
    return val


def _row_to_draft(row: asyncpg.Record) -> QuestionDraftRecord:
    """Map asyncpg Record to QuestionDraftRecord domain model."""
    raw_diff = row["suggested_difficulty"]
    diff_float = float(raw_diff) if isinstance(raw_diff, (Decimal, int, float)) else 0.500

    return QuestionDraftRecord(
        id=str(row["id"]),
        tenant_id=str(row["tenant_id"]),
        generation_job_id=str(row["generation_job_id"]),
        suggested_kc_name=str(row["suggested_kc_name"]),
        question_text=str(row["question_text"]),
        explanation=str(row["explanation"]),
        options=_deserialize_json(row["options"]),
        suggested_difficulty=diff_float,
        suggested_bloom_level=str(row["suggested_bloom_level"]),
        source_references=_deserialize_json(row["source_references"]),
        status=str(row["status"]),
        question_type="single_choice",
        knowledge_component_id=str(row["knowledge_component_id"]) if row["knowledge_component_id"] is not None else None,
        approved_question_id=str(row["approved_question_id"]) if row["approved_question_id"] is not None else None,
        reviewed_by=str(row["reviewed_by"]) if row["reviewed_by"] is not None else None,
        reviewed_at=row["reviewed_at"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        content_hash=dict(row).get("content_hash"),
    )


class PostgresDraftRepository(DraftRepositoryProtocol):
    """PostgreSQL implementation of DraftRepositoryProtocol using asyncpg."""

    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def get_draft_by_id(
        self,
        draft_id: str,
        tenant_id: str,
    ) -> QuestionDraftRecord | None:
        """Retrieve a specific draft by ID ensuring tenant isolation."""
        try:
            did = uuid.UUID(draft_id)
            tid = uuid.UUID(tenant_id)
        except ValueError:
            return None

        query = """
        SELECT * FROM question_drafts
        WHERE id = $1::uuid AND tenant_id = $2::uuid;
        """
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(query, did, tid)

        if not row:
            return None
        return _row_to_draft(row)

    async def get_drafts_by_job(
        self,
        job_id: str,
        tenant_id: str,
    ) -> list[QuestionDraftRecord]:
        """Retrieve all drafts for a given job and tenant ordered chronologically."""
        try:
            jid = uuid.UUID(job_id)
            tid = uuid.UUID(tenant_id)
        except ValueError:
            return []

        query = """
        SELECT * FROM question_drafts
        WHERE generation_job_id = $1::uuid AND tenant_id = $2::uuid
        ORDER BY created_at ASC;
        """
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(query, jid, tid)

        return [_row_to_draft(r) for r in rows]

    async def delete_unreviewed_drafts_for_job(
        self,
        job_id: str,
        tenant_id: str,
    ) -> int:
        """Delete only drafts in 'draft' status; protects reviewed drafts."""
        jid = uuid.UUID(job_id)
        tid = uuid.UUID(tenant_id)

        async with self._pool.acquire() as conn, conn.transaction():
            # Check for reviewed drafts
                reviewed_query = """
                SELECT id, status FROM question_drafts
                WHERE generation_job_id = $1::uuid
                  AND tenant_id = $2::uuid
                  AND status != 'draft'
                LIMIT 1;
                """
                reviewed_row = await conn.fetchrow(reviewed_query, jid, tid)
                if reviewed_row:
                    raise DraftAlreadyReviewedError(
                        f"No se puede eliminar el borrador {reviewed_row['id']} "
                        f"porque ya tiene estado '{reviewed_row['status']}'.",
                        details={"draft_id": str(reviewed_row["id"]), "status": reviewed_row["status"]},
                    )

                delete_query = """
                DELETE FROM question_drafts
                WHERE generation_job_id = $1::uuid
                  AND tenant_id = $2::uuid
                  AND status = 'draft';
                """
                result = await conn.execute(delete_query, jid, tid)
                # result format is "DELETE <count>"
                parts = result.split()
                return int(parts[1]) if len(parts) > 1 else 0

    async def save_drafts(
        self,
        job_id: str,
        tenant_id: str,
        drafts: list[GeneratedQuestionDraft],
    ) -> list[QuestionDraftRecord]:
        """Atomically persist generated drafts for a job with idempotency and review guards."""
        if not drafts:
            raise EmptyDraftsError(
                "No se pueden persistir cero borradores para el trabajo de generación.",
                details={"job_id": job_id},
            )

        jid = uuid.UUID(job_id)
        tid = uuid.UUID(tenant_id)

        async with self._pool.acquire() as conn, conn.transaction():
            return await self._save_drafts_in_connection(conn, jid, tid, drafts)

    async def _save_drafts_in_connection(
        self,
        conn: asyncpg.Connection,
        jid: uuid.UUID,
        tid: uuid.UUID,
        drafts: list[GeneratedQuestionDraft],
    ) -> list[QuestionDraftRecord]:
        """Internal worker method to persist drafts within an existing connection/transaction."""
        # 0. Verify parent job exists and belongs to the specified tenant
        job_check_query = """
        SELECT id FROM content_generation_jobs
        WHERE id = $1::uuid AND tenant_id = $2::uuid;
        """
        job_exists = await conn.fetchrow(job_check_query, jid, tid)
        if not job_exists:
            raise JobNotFoundError(f"Trabajo con ID {jid} no pertenece al tenant {tid} o no existe.")

        # 1. Safeguard human-in-the-loop review work
        reviewed_query = """
        SELECT id, status FROM question_drafts
        WHERE generation_job_id = $1::uuid
          AND tenant_id = $2::uuid
          AND status != 'draft'
        LIMIT 1;
        """
        reviewed = await conn.fetchrow(reviewed_query, jid, tid)
        if reviewed:
            raise DraftAlreadyReviewedError(
                f"No se pueden sobreescribir los borradores del trabajo {jid} "
                f"porque el borrador {reviewed['id']} ya se encuentra en estado '{reviewed['status']}'.",
                details={
                    "job_id": str(jid),
                    "draft_id": str(reviewed["id"]),
                    "status": reviewed["status"],
                },
            )

        # 2. Deduplicate drafts within the batch by content hash
        seen_hashes: set[str] = set()
        deduped_drafts: list[GeneratedQuestionDraft] = []
        for item in drafts:
            ch = compute_draft_content_hash(
                item.question_text, item.suggested_kc_name, item.options
            )
            if ch in seen_hashes:
                logger.warning(
                    "Skipping duplicate draft with identical content hash within batch: %s",
                    ch,
                )
                continue
            seen_hashes.add(ch)
            deduped_drafts.append(item)

        # 3. Prune unreviewed drafts for this job whose content_hash is not in the incoming batch
        # Preserves matching 'draft' rows for atomic in-place UPSERT without touching status != 'draft'
        delete_pruned_query = """
        DELETE FROM question_drafts
        WHERE generation_job_id = $1::uuid
          AND tenant_id = $2::uuid
          AND status = 'draft'
          AND content_hash != ALL($3::text[]);
        """
        await conn.execute(delete_pruned_query, jid, tid, list(seen_hashes))

        # 4. Insert or update draft records with idempotency upsert protection and status='draft' condition
        insert_query = """
        INSERT INTO question_drafts (
            id, tenant_id, generation_job_id,
            suggested_kc_name, question_text, explanation,
            options, suggested_difficulty, suggested_bloom_level,
            source_references, status, content_hash
        ) VALUES (
            $1::uuid, $2::uuid, $3::uuid,
            $4, $5, $6,
            $7::jsonb, $8, $9,
            $10::jsonb, 'draft'::draft_status_enum, $11
        )
        ON CONFLICT (generation_job_id, content_hash) WHERE content_hash IS NOT NULL
        DO UPDATE SET
            suggested_kc_name = EXCLUDED.suggested_kc_name,
            question_text = EXCLUDED.question_text,
            explanation = EXCLUDED.explanation,
            options = EXCLUDED.options,
            suggested_difficulty = EXCLUDED.suggested_difficulty,
            suggested_bloom_level = EXCLUDED.suggested_bloom_level,
            source_references = EXCLUDED.source_references,
            updated_at = now()
        WHERE question_drafts.status = 'draft'
        RETURNING *;
        """
        records: list[QuestionDraftRecord] = []
        for item in deduped_drafts:
            draft_id = uuid.uuid4()
            options_data = [
                {
                    "text": opt.text,
                    "is_correct": opt.is_correct,
                    **(
                        {"misconception_explanation": opt.misconception_explanation}
                        if opt.misconception_explanation
                        else {}
                    ),
                }
                for opt in item.options
            ]
            source_refs_data = [
                {
                    "type": ref.type.value,
                    "index": ref.index,
                    "snippet": ref.snippet,
                }
                for ref in item.source_references
            ]
            content_hash = compute_draft_content_hash(
                item.question_text, item.suggested_kc_name, item.options
            )

            row = await conn.fetchrow(
                insert_query,
                draft_id,
                tid,
                jid,
                item.suggested_kc_name,
                item.question_text,
                item.explanation,
                json.dumps(options_data),
                item.numeric_difficulty,
                item.bloom_taxonomy.value,
                json.dumps(source_refs_data),
                content_hash,
            )
            if row:
                records.append(_row_to_draft(row))
            else:
                # Concurrency / race condition protection:
                # A row with this (generation_job_id, content_hash) exists, but its status != 'draft'.
                # The WHERE question_drafts.status = 'draft' prevented update, returning 0 rows.
                existing_row = await conn.fetchrow(
                    """
                    SELECT id, status FROM question_drafts
                    WHERE generation_job_id = $1::uuid AND content_hash = $2;
                    """,
                    jid,
                    content_hash,
                )
                status_str = existing_row["status"] if existing_row else "reviewed"
                draft_id_str = str(existing_row["id"]) if existing_row else "unknown"
                raise DraftAlreadyReviewedError(
                    f"No se pueden sobreescribir los borradores del trabajo {jid} "
                    f"porque el borrador {draft_id_str} ya se encuentra en estado '{status_str}'.",
                    details={
                        "job_id": str(jid),
                        "draft_id": draft_id_str,
                        "status": status_str,
                    },
                )

        return records
