"""Unit of Work pattern for atomic content generation persistence.

Guarantees strict atomicity:
Drafts are inserted and job transitions to 'review_required' in a SINGLE PostgreSQL transaction.
Any intermediate failure executes full rollback, ensuring no orphan drafts or prematurely completed jobs.
"""

import logging
import uuid
from typing import Protocol

import asyncpg

from app.content_generation.exceptions import (
    EmptyDraftsError,
    InvalidJobStateTransitionError,
    JobNotFoundError,
)
from app.content_generation.infrastructure.postgres_draft_repository import (
    PostgresDraftRepository,
)
from app.content_generation.infrastructure.postgres_job_repository import (
    _row_to_job,
)
from app.content_generation.repositories.draft_repository import (
    InMemoryDraftRepository,
)
from app.content_generation.repositories.job_repository import (
    ContentGenerationJobRecord,
    InMemoryJobRepository,
)
from app.content_generation.schemas.generated_questions import (
    GeneratedQuestionDraft,
    QuestionDraftRecord,
)

logger = logging.getLogger(__name__)


class GenerationUnitOfWorkProtocol(Protocol):
    """Protocol defining the transactional Unit of Work boundary."""

    async def commit_generation_results(
        self,
        job_id: str,
        tenant_id: str,
        drafts: list[GeneratedQuestionDraft],
        lease_token: str | None = None,
    ) -> tuple[ContentGenerationJobRecord, list[QuestionDraftRecord]]:
        """Atomically persist question drafts and mark job as review_required."""
        ...


class PostgresUnitOfWork(GenerationUnitOfWorkProtocol):
    """PostgreSQL implementation of GenerationUnitOfWorkProtocol using asyncpg transactions."""

    def __init__(
        self,
        pool: asyncpg.Pool,
        draft_repository: PostgresDraftRepository | None = None,
    ) -> None:
        self._pool = pool
        self._draft_repo = draft_repository or PostgresDraftRepository(pool)

    async def commit_generation_results(
        self,
        job_id: str,
        tenant_id: str,
        drafts: list[GeneratedQuestionDraft],
        lease_token: str | None = None,
    ) -> tuple[ContentGenerationJobRecord, list[QuestionDraftRecord]]:
        """Atomically persist drafts and transition job to review_required within a single transaction."""
        if not drafts:
            raise EmptyDraftsError(
                "No se pueden persistir cero borradores para el trabajo de generación.",
                details={"job_id": job_id},
            )

        if lease_token is None:
            raise InvalidJobStateTransitionError(
                "Se requiere un lease_token UUID válido y no nulo para persistir los resultados de generación.",
                details={"job_id": job_id, "token_provided": False},
            )
        try:
            token_uuid = uuid.UUID(str(lease_token))
        except (ValueError, AttributeError) as e:
            raise InvalidJobStateTransitionError(
                f"El lease_token suministrado '{lease_token}' no es un UUID válido.",
                details={"job_id": job_id, "lease_token": str(lease_token)},
            ) from e

        jid = uuid.UUID(job_id)
        tid = uuid.UUID(tenant_id)

        async with self._pool.acquire() as conn, conn.transaction():
            # 1. Persist validated drafts in quarantine
            persisted_drafts = await self._draft_repo._save_drafts_in_connection(
                conn, jid, tid, drafts
            )

            # 2. Transition job to 'review_required' verifying lease fencing token
            update_query = """
            UPDATE content_generation_jobs
            SET status = 'review_required',
                completed_at = now(),
                updated_at = now()
            WHERE id = $1::uuid
              AND tenant_id = $2::uuid
              AND status = 'processing'
              AND processing_lease_token = $3::uuid
              AND processing_lease_expires_at >= now()
            RETURNING *;
            """
            job_row = await conn.fetchrow(update_query, jid, tid, token_uuid)

            if not job_row:
                check_query = """
                SELECT status, processing_lease_token, processing_lease_expires_at
                FROM content_generation_jobs
                WHERE id = $1::uuid AND tenant_id = $2::uuid;
                """
                chk = await conn.fetchrow(check_query, jid, tid)
                if not chk:
                    raise JobNotFoundError(f"Trabajo de generación {job_id} no encontrado.")
                if chk["status"] != "processing":
                    raise InvalidJobStateTransitionError(
                        f"No se pudo completar el trabajo {job_id}: estado '{chk['status']}' no permite "
                        "transición a 'review_required'.",
                        details={"job_id": job_id, "status": chk["status"]},
                    )
                if chk["processing_lease_token"] != token_uuid:
                    raise InvalidJobStateTransitionError(
                        f"No se pudo completar el trabajo {job_id}: el lease pertenece a otro worker.",
                        details={
                            "job_id": job_id,
                            "expected_token": str(chk["processing_lease_token"]),
                            "provided_token": str(token_uuid),
                        },
                    )
                raise InvalidJobStateTransitionError(
                    f"No se pudo completar el trabajo {job_id}: el lease de procesamiento ha expirado.",
                    details={"job_id": job_id, "lease_expires_at": str(chk["processing_lease_expires_at"])},
                )

            job_record = _row_to_job(job_row)
            logger.info(
                "Atomically committed %d drafts for job %s with review_required status.",
                len(persisted_drafts),
                job_id,
            )
            return job_record, persisted_drafts


class InMemoryUnitOfWork(GenerationUnitOfWorkProtocol):
    """In-memory Unit of Work for fast, isolated unit testing."""

    def __init__(
        self,
        job_repository: InMemoryJobRepository,
        draft_repository: InMemoryDraftRepository,
    ) -> None:
        self._job_repo = job_repository
        self._draft_repo = draft_repository

    async def commit_generation_results(
        self,
        job_id: str,
        tenant_id: str,
        drafts: list[GeneratedQuestionDraft],
        lease_token: str | None = None,
    ) -> tuple[ContentGenerationJobRecord, list[QuestionDraftRecord]]:
        """Atomically persist drafts and transition job in memory."""
        draft_records = await self._draft_repo.save_drafts(job_id, tenant_id, drafts)
        job_record = await self._job_repo.mark_review_required(
            job_id, tenant_id, lease_token=lease_token
        )
        return job_record, draft_records
