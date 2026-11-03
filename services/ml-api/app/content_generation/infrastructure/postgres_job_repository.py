"""PostgreSQL adapter for Content Generation Jobs repository.

Provides ACID-compliant persistence, atomic lease acquisition via SELECT FOR UPDATE SKIP LOCKED,
and fence-token validation to prevent zombie worker split-brain updates.
"""

import logging
import uuid

import asyncpg

from app.content_generation.exceptions import (
    InvalidJobStateTransitionError,
    JobNotFoundError,
)
from app.content_generation.repositories.job_repository import (
    ContentGenerationJobRecord,
    JobRepositoryProtocol,
)
from app.content_generation.services.document_validation import (
    validate_teacher_job_access,
)

logger = logging.getLogger(__name__)


def _row_to_job(row: asyncpg.Record) -> ContentGenerationJobRecord:
    """Map asyncpg Record to ContentGenerationJobRecord domain model."""
    return ContentGenerationJobRecord(
        id=str(row["id"]),
        tenant_id=str(row["tenant_id"]),
        created_by=str(row["created_by"]),
        storage_bucket=str(row["storage_bucket"]),
        storage_path=str(row["storage_path"]),
        original_filename=str(row["original_filename"]),
        mime_type=str(row["mime_type"]),
        file_size_bytes=int(row["file_size_bytes"]),
        file_checksum=str(row["file_checksum"]),
        status=str(row["status"]),
        provider=str(row["provider"]),
        model_id=str(row["model_id"]),
        prompt_version=str(row["prompt_version"]),
        course_id=str(row["course_id"]) if row["course_id"] is not None else None,
        unit_id=str(row["unit_id"]) if row["unit_id"] is not None else None,
        error_code=row["error_code"],
        error_message_safe=row["error_message_safe"],
        created_at=row["created_at"],
        started_at=row["started_at"],
        completed_at=row["completed_at"],
        updated_at=row["updated_at"],
        processing_started_at=dict(row).get("processing_started_at"),
        processing_lease_expires_at=dict(row).get("processing_lease_expires_at"),
        processing_lease_token=str(row["processing_lease_token"]) if dict(row).get("processing_lease_token") is not None else None,
        attempt_count=int(row["attempt_count"]) if dict(row).get("attempt_count") is not None else 0,
        max_attempts=int(row["max_attempts"]) if dict(row).get("max_attempts") is not None else 3,
        last_heartbeat_at=dict(row).get("last_heartbeat_at"),
    )


class PostgresJobRepository(JobRepositoryProtocol):
    """PostgreSQL implementation of JobRepositoryProtocol using asyncpg."""

    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def create_job(
        self,
        job: ContentGenerationJobRecord,
    ) -> ContentGenerationJobRecord:
        """Insert a newly queued job into PostgreSQL with active uniqueness enforcement."""
        query = """
        INSERT INTO content_generation_jobs (
            id, tenant_id, course_id, unit_id, created_by,
            storage_bucket, storage_path, original_filename,
            mime_type, file_size_bytes, file_checksum,
            status, provider, model_id, prompt_version,
            attempt_count, max_attempts
        ) VALUES (
            $1::uuid, $2::uuid, $3::uuid, $4::uuid, $5::uuid,
            $6, $7, $8,
            $9, $10, $11,
            $12::generation_job_status_enum, $13, $14, $15,
            $16, $17
        )
        RETURNING *;
        """
        job_id = uuid.UUID(job.id) if isinstance(job.id, str) else job.id
        tenant_id = uuid.UUID(job.tenant_id) if isinstance(job.tenant_id, str) else job.tenant_id
        course_id = uuid.UUID(job.course_id) if job.course_id else None
        unit_id = uuid.UUID(job.unit_id) if job.unit_id else None
        created_by = uuid.UUID(job.created_by) if isinstance(job.created_by, str) else job.created_by

        async with self._pool.acquire() as conn:
            try:
                row = await conn.fetchrow(
                    query,
                    job_id,
                    tenant_id,
                    course_id,
                    unit_id,
                    created_by,
                    job.storage_bucket,
                    job.storage_path,
                    job.original_filename,
                    job.mime_type,
                    job.file_size_bytes,
                    job.file_checksum,
                    job.status,
                    job.provider,
                    job.model_id,
                    job.prompt_version,
                    job.attempt_count,
                    job.max_attempts,
                )
            except asyncpg.exceptions.UniqueViolationError as e:
                logger.warning(
                    "Duplicate active job blocked by partial unique index: %s", e
                )
                raise InvalidJobStateTransitionError(
                    "Ya existe un trabajo activo en curso para este archivo y curso.",
                    details={"file_checksum": job.file_checksum},
                ) from e

        if not row:
            raise InvalidJobStateTransitionError("No se pudo persistir el trabajo en PostgreSQL.")
        return _row_to_job(row)

    async def get_job(
        self,
        job_id: str,
        tenant_id: str,
        requesting_user_id: str | None = None,
        user_role: str | None = None,
        authorized_course_ids: set[str] | list[str] | None = None,
    ) -> ContentGenerationJobRecord | None:
        """Fetch job verifying tenant isolation and teacher permissions."""
        query = """
        SELECT * FROM content_generation_jobs
        WHERE id = $1::uuid AND tenant_id = $2::uuid;
        """
        try:
            jid = uuid.UUID(job_id)
            tid = uuid.UUID(tenant_id)
        except ValueError:
            return None

        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(query, jid, tid)

        if not row:
            return None

        job = _row_to_job(row)

        validate_teacher_job_access(
            job_tenant_id=job.tenant_id,
            job_created_by=job.created_by,
            job_course_id=job.course_id,
            tenant_id=tenant_id,
            requesting_user_id=requesting_user_id,
            user_role=user_role,
            authorized_course_ids=authorized_course_ids,
        )
        return job

    async def mark_processing(
        self,
        job_id: str,
        tenant_id: str,
        lease_token: str | None = None,
        lease_duration_seconds: int = 300,
    ) -> ContentGenerationJobRecord:
        """Transition queued/failed/review_required -> processing with lease assignment."""
        token_uuid = uuid.UUID(lease_token) if lease_token else uuid.uuid4()
        jid = uuid.UUID(job_id)
        tid = uuid.UUID(tenant_id)

        query = """
        UPDATE content_generation_jobs
        SET status = 'processing',
            processing_started_at = now(),
            processing_lease_expires_at = now() + make_interval(secs => $3),
            processing_lease_token = $4::uuid,
            last_heartbeat_at = now(),
            started_at = COALESCE(started_at, now()),
            attempt_count = attempt_count + 1,
            updated_at = now()
        WHERE id = $1::uuid
          AND tenant_id = $2::uuid
          AND status IN ('queued', 'failed', 'review_required', 'processing')
          AND (processing_lease_token IS NULL OR processing_lease_token = $4::uuid OR processing_lease_expires_at < now())
        RETURNING *;
        """
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                query,
                jid,
                tid,
                lease_duration_seconds,
                token_uuid,
            )

        if not row:
            existing = await self.get_job(job_id, tenant_id)
            if not existing:
                raise JobNotFoundError(f"Trabajo con ID {job_id} no encontrado.")
            raise InvalidJobStateTransitionError(
                f"No se puede iniciar procesamiento desde el estado '{existing.status}' "
                "o el lease pertenece a otro worker.",
                details={"job_id": job_id, "status": existing.status},
            )

        return _row_to_job(row)

    async def mark_review_required(
        self,
        job_id: str,
        tenant_id: str,
        lease_token: str | None = None,
    ) -> ContentGenerationJobRecord:
        """Transition processing -> review_required strictly validating lease fence token."""
        if lease_token is None:
            raise InvalidJobStateTransitionError(
                "Se requiere un lease_token UUID válido y no nulo para finalizar el trabajo por un worker.",
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

        query = """
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
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(query, jid, tid, token_uuid)

        if not row:
            existing = await self.get_job(job_id, tenant_id)
            if not existing:
                raise JobNotFoundError(f"Trabajo con ID {job_id} no encontrado.")
            if existing.status != "processing":
                raise InvalidJobStateTransitionError(
                    f"Transición a 'review_required' no permitida desde el estado '{existing.status}'.",
                    details={"job_id": job_id, "status": existing.status},
                )
            if existing.processing_lease_token != str(token_uuid):
                raise InvalidJobStateTransitionError(
                    "El lease_token no coincide con el worker actual o pertenece a otro worker.",
                    details={
                        "job_id": job_id,
                        "expected_token": existing.processing_lease_token,
                        "provided_token": str(token_uuid),
                    },
                )
            raise InvalidJobStateTransitionError(
                "El lease de procesamiento ha expirado. No se puede finalizar el trabajo.",
                details={
                    "job_id": job_id,
                    "lease_expires_at": str(existing.processing_lease_expires_at),
                },
            )

        return _row_to_job(row)

    async def admin_mark_review_required(
        self,
        job_id: str,
        tenant_id: str,
    ) -> ContentGenerationJobRecord:
        """Administrative transition from 'processing' to 'review_required' without lease fencing."""
        jid = uuid.UUID(job_id)
        tid = uuid.UUID(tenant_id)

        query = """
        UPDATE content_generation_jobs
        SET status = 'review_required',
            completed_at = now(),
            updated_at = now()
        WHERE id = $1::uuid
          AND tenant_id = $2::uuid
          AND status = 'processing'
        RETURNING *;
        """
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(query, jid, tid)

        if not row:
            existing = await self.get_job(job_id, tenant_id)
            if not existing:
                raise JobNotFoundError(f"Trabajo con ID {job_id} no encontrado.")
            raise InvalidJobStateTransitionError(
                f"Transición administrativa a 'review_required' no permitida desde el estado '{existing.status}'.",
                details={"job_id": job_id, "status": existing.status},
            )

        return _row_to_job(row)

    async def mark_failed(
        self,
        job_id: str,
        tenant_id: str,
        error_code: str,
        error_message_safe: str,
        lease_token: str | None = None,
    ) -> ContentGenerationJobRecord:
        """Transition job to 'failed' from any active state validating lease fence token."""
        if lease_token is None:
            raise InvalidJobStateTransitionError(
                "Se requiere un lease_token UUID válido y no nulo para marcar el trabajo como fallido por un worker.",
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

        query = """
        UPDATE content_generation_jobs
        SET status = 'failed',
            error_code = $3,
            error_message_safe = $4,
            completed_at = now(),
            updated_at = now()
        WHERE id = $1::uuid
          AND tenant_id = $2::uuid
          AND status NOT IN ('approved', 'rejected')
          AND processing_lease_token = $5::uuid
          AND processing_lease_expires_at >= now()
        RETURNING *;
        """
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                query,
                jid,
                tid,
                error_code,
                error_message_safe,
                token_uuid,
            )

        if not row:
            existing = await self.get_job(job_id, tenant_id)
            if not existing:
                raise JobNotFoundError(f"Trabajo con ID {job_id} no encontrado.")
            if existing.status in ("approved", "rejected"):
                raise InvalidJobStateTransitionError(
                    f"No se puede marcar como fallido un trabajo en estado terminal '{existing.status}'.",
                    details={"job_id": job_id, "status": existing.status},
                )
            if existing.processing_lease_token != str(token_uuid):
                raise InvalidJobStateTransitionError(
                    "El lease_token no coincide con el worker actual o pertenece a otro worker.",
                    details={
                        "job_id": job_id,
                        "expected_token": existing.processing_lease_token,
                        "provided_token": str(token_uuid),
                    },
                )
            raise InvalidJobStateTransitionError(
                "El lease de procesamiento ha expirado. No se puede finalizar el trabajo.",
                details={
                    "job_id": job_id,
                    "lease_expires_at": str(existing.processing_lease_expires_at),
                },
            )

        return _row_to_job(row)

    async def admin_mark_failed(
        self,
        job_id: str,
        tenant_id: str,
        error_code: str,
        error_message_safe: str,
    ) -> ContentGenerationJobRecord:
        """Administrative transition to 'failed' without lease fencing."""
        jid = uuid.UUID(job_id)
        tid = uuid.UUID(tenant_id)

        query = """
        UPDATE content_generation_jobs
        SET status = 'failed',
            error_code = $3,
            error_message_safe = $4,
            completed_at = now(),
            updated_at = now()
        WHERE id = $1::uuid
          AND tenant_id = $2::uuid
          AND status NOT IN ('approved', 'rejected')
        RETURNING *;
        """
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                query,
                jid,
                tid,
                error_code,
                error_message_safe,
            )

        if not row:
            existing = await self.get_job(job_id, tenant_id)
            if not existing:
                raise JobNotFoundError(f"Trabajo con ID {job_id} no encontrado.")
            raise InvalidJobStateTransitionError(
                f"No se puede marcar como fallido un trabajo en estado terminal '{existing.status}'.",
                details={"job_id": job_id, "status": existing.status},
            )

        return _row_to_job(row)

    async def recover_abandoned_jobs(
        self,
        tenant_id: str | None = None,
        job_id: str | None = None,
    ) -> int:
        """Atomically transition abandoned processing jobs with expired leases exceeding max attempts to 'failed'."""
        tid = uuid.UUID(tenant_id) if tenant_id else None
        jid = uuid.UUID(job_id) if job_id else None

        query = """
        UPDATE content_generation_jobs
        SET status = 'failed',
            error_code = 'MAX_ATTEMPTS_EXCEEDED',
            error_message_safe = 'El trabajo superó el límite máximo de reintentos permitidos tras expirar el lease.',
            completed_at = now(),
            updated_at = now()
        WHERE ($1::uuid IS NULL OR tenant_id = $1::uuid)
          AND ($2::uuid IS NULL OR id = $2::uuid)
          AND (
              (status = 'processing' AND processing_lease_expires_at < now() AND attempt_count >= max_attempts)
              OR (status = 'queued' AND attempt_count >= max_attempts)
          );
        """
        async with self._pool.acquire() as conn:
            result = await conn.execute(query, tid, jid)
            parts = str(result).split()
            return int(parts[1]) if len(parts) > 1 else 0

    async def claim_pending_job(
        self,
        tenant_id: str | None = None,
        lease_duration_seconds: int = 300,
        worker_token: str | None = None,
        job_id: str | None = None,
    ) -> ContentGenerationJobRecord | None:
        """Atomically claim the next queued or lease-expired job via SELECT FOR UPDATE SKIP LOCKED."""
        # 1. Recover and transition any expired abandoned jobs that exceeded max_attempts
        await self.recover_abandoned_jobs(tenant_id=tenant_id, job_id=job_id)

        token = uuid.UUID(worker_token) if worker_token else uuid.uuid4()
        tid = uuid.UUID(tenant_id) if tenant_id else None
        jid = uuid.UUID(job_id) if job_id else None

        query = """
        WITH candidate AS (
            SELECT id
            FROM content_generation_jobs
            WHERE ($1::uuid IS NULL OR tenant_id = $1::uuid)
              AND ($2::uuid IS NULL OR id = $2::uuid)
              AND (
                  (status = 'queued' AND attempt_count < max_attempts)
                  OR (status = 'processing' AND processing_lease_expires_at < now() AND attempt_count < max_attempts)
              )
            ORDER BY created_at ASC
            LIMIT 1
            FOR UPDATE SKIP LOCKED
        )
        UPDATE content_generation_jobs j
        SET status = 'processing',
            processing_started_at = now(),
            processing_lease_expires_at = now() + make_interval(secs => $3),
            processing_lease_token = $4::uuid,
            attempt_count = attempt_count + 1,
            last_heartbeat_at = now(),
            started_at = COALESCE(started_at, now()),
            updated_at = now()
        FROM candidate
        WHERE j.id = candidate.id
        RETURNING j.*;
        """
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(query, tid, jid, lease_duration_seconds, token)

        if not row:
            return None
        return _row_to_job(row)

    async def renew_lease(
        self,
        job_id: str,
        tenant_id: str,
        lease_token: str,
        extension_seconds: int = 300,
    ) -> ContentGenerationJobRecord:
        """Extend lease duration if current worker still holds the lease."""
        jid = uuid.UUID(job_id)
        tid = uuid.UUID(tenant_id)
        token_uuid = uuid.UUID(lease_token)

        query = """
        UPDATE content_generation_jobs
        SET processing_lease_expires_at = now() + make_interval(secs => $3),
            last_heartbeat_at = now(),
            updated_at = now()
        WHERE id = $1::uuid
          AND tenant_id = $2::uuid
          AND status = 'processing'
          AND processing_lease_token = $4::uuid
          AND processing_lease_expires_at >= now()
        RETURNING *;
        """
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(query, jid, tid, extension_seconds, token_uuid)

        if not row:
            existing = await self.get_job(job_id, tenant_id)
            if not existing:
                raise JobNotFoundError(f"Trabajo con ID {job_id} no encontrado.")
            raise InvalidJobStateTransitionError(
                "No se pudo renovar el lease: el trabajo ya no está en procesamiento "
                "o fue reclamado por otro worker.",
                details={"job_id": job_id, "status": existing.status},
            )

        return _row_to_job(row)

    async def heartbeat(
        self,
        job_id: str,
        tenant_id: str,
        lease_token: str,
    ) -> bool:
        """Update last heartbeat timestamp verifying lease ownership."""
        try:
            jid = uuid.UUID(job_id)
            tid = uuid.UUID(tenant_id)
            token_uuid = uuid.UUID(lease_token)
        except ValueError:
            return False

        query = """
        UPDATE content_generation_jobs
        SET last_heartbeat_at = now()
        WHERE id = $1::uuid
          AND tenant_id = $2::uuid
          AND status = 'processing'
          AND processing_lease_token = $3::uuid
          AND processing_lease_expires_at >= now();
        """
        async with self._pool.acquire() as conn:
            status = await conn.execute(query, jid, tid, token_uuid)
            return str(status) != "UPDATE 0"
