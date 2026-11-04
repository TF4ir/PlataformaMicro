"""Job repository abstractions and lifecycle transition enforcement.

Strictly enforces job state transitions:
queued -> processing -> review_required (success) or failed (controlled error).
Explicitly rejects direct approval or invalid jumps.
Includes lease tracking and concurrency recovery mechanisms.
"""

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Protocol

from app.content_generation.exceptions import (
    InvalidJobStateTransitionError,
    JobNotFoundError,
)


@dataclass
class ContentGenerationJobRecord:
    """Domain model of a content generation job in PostgreSQL."""

    id: str
    tenant_id: str
    created_by: str
    storage_bucket: str
    storage_path: str
    original_filename: str
    mime_type: str
    file_size_bytes: int
    file_checksum: str
    status: str
    provider: str
    model_id: str
    prompt_version: str = "v1"
    course_id: str | None = None
    unit_id: str | None = None
    error_code: str | None = None
    error_message_safe: str | None = None
    created_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    updated_at: datetime | None = None
    processing_started_at: datetime | None = None
    processing_lease_expires_at: datetime | None = None
    processing_lease_token: str | None = None
    attempt_count: int = 0
    max_attempts: int = 3
    last_heartbeat_at: datetime | None = None


class JobRepositoryProtocol(Protocol):
    """Protocol for persisting and transitioning content generation jobs."""

    async def create_job(
        self,
        job: ContentGenerationJobRecord,
    ) -> ContentGenerationJobRecord:
        """Insert a newly queued content generation job."""
        ...

    async def get_job(
        self,
        job_id: str,
        tenant_id: str,
        requesting_user_id: str | None = None,
        user_role: str | None = None,
        authorized_course_ids: set[str] | list[str] | None = None,
    ) -> ContentGenerationJobRecord | None:
        """Fetch job record by ID ensuring tenant isolation and user permissions."""
        ...

    async def list_jobs(
        self,
        tenant_id: str,
        requesting_user_id: str,
        user_role: str,
        authorized_course_ids: set[str] | list[str] | None = None,
        course_id: str | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[ContentGenerationJobRecord], int]:
        """List content generation jobs for the requesting user/tenant with optional filters and pagination."""
        ...

    async def mark_processing(
        self,
        job_id: str,
        tenant_id: str,
        lease_token: str | None = None,
        lease_duration_seconds: int = 300,
    ) -> ContentGenerationJobRecord:
        """Transition job from 'queued' to 'processing'."""
        ...

    async def mark_review_required(
        self,
        job_id: str,
        tenant_id: str,
        lease_token: str | None = None,
    ) -> ContentGenerationJobRecord:
        """Transition job from 'processing' to 'review_required' enforcing lease fencing."""
        ...

    async def admin_mark_review_required(
        self,
        job_id: str,
        tenant_id: str,
    ) -> ContentGenerationJobRecord:
        """Administrative transition from 'processing' to 'review_required' without lease fencing."""
        ...

    async def mark_failed(
        self,
        job_id: str,
        tenant_id: str,
        error_code: str,
        error_message_safe: str,
        lease_token: str | None = None,
    ) -> ContentGenerationJobRecord:
        """Transition job to 'failed' recording safe error details with lease fencing."""
        ...

    async def admin_mark_failed(
        self,
        job_id: str,
        tenant_id: str,
        error_code: str,
        error_message_safe: str,
    ) -> ContentGenerationJobRecord:
        """Administrative transition to 'failed' without lease fencing."""
        ...

    async def claim_pending_job(
        self,
        tenant_id: str | None = None,
        lease_duration_seconds: int = 300,
        worker_token: str | None = None,
        job_id: str | None = None,
    ) -> ContentGenerationJobRecord | None:
        """Atomically claim a queued or lease-expired job for processing."""
        ...

    async def renew_lease(
        self,
        job_id: str,
        tenant_id: str,
        lease_token: str,
        extension_seconds: int = 300,
    ) -> ContentGenerationJobRecord:
        """Extend lease expiration if caller holds active lease token."""
        ...

    async def heartbeat(
        self,
        job_id: str,
        tenant_id: str,
        lease_token: str,
    ) -> bool:
        """Update last heartbeat timestamp verifying lease ownership."""
        ...

    async def recover_abandoned_jobs(
        self,
        tenant_id: str | None = None,
        job_id: str | None = None,
    ) -> int:
        """Transition abandoned processing jobs whose lease expired and reached max attempts to 'failed'."""
        ...


class InMemoryJobRepository:
    """In-memory job repository implementation for testing and development."""

    def __init__(self) -> None:
        self._jobs: dict[str, ContentGenerationJobRecord] = {}

    def add_job(self, job: ContentGenerationJobRecord) -> None:
        """Register a job in the test memory store."""
        if job.status not in ("queued", "processing", "review_required", "failed"):
            raise InvalidJobStateTransitionError(
                f"Estado inicial '{job.status}' no válido para creación de trabajo."
            )
        self._jobs[job.id] = job

    async def create_job(
        self,
        job: ContentGenerationJobRecord,
    ) -> ContentGenerationJobRecord:
        """Create a job validating partial active uniqueness."""
        if job.status not in ("queued", "processing", "review_required", "failed"):
            raise InvalidJobStateTransitionError(
                f"Estado inicial '{job.status}' no válido para creación de trabajo."
            )
        # Check active uniqueness
        if job.status in ("queued", "processing"):
            for existing in self._jobs.values():
                if (
                    existing.tenant_id == job.tenant_id
                    and existing.course_id == job.course_id
                    and existing.file_checksum == job.file_checksum
                    and existing.status in ("queued", "processing")
                    and existing.id != job.id
                ):
                    raise InvalidJobStateTransitionError(
                        "Ya existe un trabajo activo en curso para este archivo y curso."
                    )
        now = datetime.now(UTC)
        if not job.created_at:
            job.created_at = now
        job.updated_at = now
        self._jobs[job.id] = job
        return job

    async def get_job(
        self,
        job_id: str,
        tenant_id: str,
        requesting_user_id: str | None = None,
        user_role: str | None = None,
        authorized_course_ids: set[str] | list[str] | None = None,
    ) -> ContentGenerationJobRecord | None:
        """Fetch job checking tenant boundary and teacher permissions."""
        job = self._jobs.get(job_id)
        if not job:
            return None

        from app.content_generation.services.document_validation import (
            validate_teacher_job_access,
        )

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

    async def list_jobs(
        self,
        tenant_id: str,
        requesting_user_id: str,
        user_role: str,
        authorized_course_ids: set[str] | list[str] | None = None,
        course_id: str | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[ContentGenerationJobRecord], int]:
        """List content generation jobs for the requesting user/tenant."""
        auth_courses = set(authorized_course_ids or [])
        candidates: list[ContentGenerationJobRecord] = []
        for j in self._jobs.values():
            if j.tenant_id != tenant_id:
                continue
            if course_id and j.course_id != course_id:
                continue
            if status and j.status != status:
                continue
            if user_role == "teacher":
                if course_id:
                    if course_id not in auth_courses:
                        continue
                else:
                    if j.created_by != requesting_user_id and (not j.course_id or j.course_id not in auth_courses):
                        continue
            candidates.append(j)

        now = datetime.now(UTC)
        candidates.sort(key=lambda x: x.created_at or now, reverse=True)
        total = len(candidates)
        return candidates[offset : offset + limit], total

    async def mark_processing(
        self,
        job_id: str,
        tenant_id: str,
        lease_token: str | None = None,
        lease_duration_seconds: int = 300,
    ) -> ContentGenerationJobRecord:
        """Transition queued/failed/review_required -> processing."""
        job = await self.get_job(job_id, tenant_id)
        if not job:
            raise JobNotFoundError(f"Trabajo con ID {job_id} no encontrado.")

        # Guard against zombie workers
        if (
            lease_token is not None
            and job.processing_lease_token is not None
            and job.processing_lease_token != lease_token
        ):
            raise InvalidJobStateTransitionError(
                "El lease del trabajo ya pertenece a otro worker o ha expirado."
            )

        if job.status not in ("queued", "failed", "review_required"):
            raise InvalidJobStateTransitionError(
                f"No se puede iniciar procesamiento desde el estado '{job.status}'. Se requiere 'queued', 'failed' o 'review_required'."
            )

        now = datetime.now(UTC)
        job.status = "processing"
        job.started_at = job.started_at or now
        job.processing_lease_token = lease_token or job.processing_lease_token or str(uuid.uuid4())
        job.processing_lease_expires_at = now + timedelta(seconds=lease_duration_seconds)
        job.last_heartbeat_at = now
        job.attempt_count += 1
        job.updated_at = now
        return job

    async def mark_review_required(
        self,
        job_id: str,
        tenant_id: str,
        lease_token: str | None = None,
    ) -> ContentGenerationJobRecord:
        """Transition processing -> review_required enforcing fencing token."""
        if lease_token is None:
            raise InvalidJobStateTransitionError(
                "Se requiere un lease_token UUID válido y no nulo para finalizar el trabajo por un worker.",
                details={"job_id": job_id, "token_provided": False},
            )
        try:
            uuid.UUID(str(lease_token))
        except (ValueError, AttributeError) as e:
            raise InvalidJobStateTransitionError(
                f"El lease_token suministrado '{lease_token}' no es un UUID válido.",
                details={"job_id": job_id, "lease_token": str(lease_token)},
            ) from e

        job = await self.get_job(job_id, tenant_id)
        if not job:
            raise JobNotFoundError(f"Trabajo con ID {job_id} no encontrado.")

        if job.status != "processing":
            raise InvalidJobStateTransitionError(
                f"Transición a 'review_required' no permitida desde el estado '{job.status}'. Se requiere 'processing'.",
                details={"job_id": job_id, "status": job.status},
            )

        if job.processing_lease_token is None or job.processing_lease_token != str(lease_token):
            raise InvalidJobStateTransitionError(
                "El lease_token no coincide con el worker actual o pertenece a otro worker.",
                details={
                    "job_id": job_id,
                    "expected_token": job.processing_lease_token,
                    "provided_token": str(lease_token),
                },
            )

        now = datetime.now(UTC)
        if job.processing_lease_expires_at is None or job.processing_lease_expires_at < now:
            raise InvalidJobStateTransitionError(
                "El lease de procesamiento ha expirado. No se puede finalizar el trabajo.",
                details={"job_id": job_id, "lease_expires_at": str(job.processing_lease_expires_at)},
            )

        job.status = "review_required"
        job.completed_at = now
        job.updated_at = now
        return job

    async def admin_mark_review_required(
        self,
        job_id: str,
        tenant_id: str,
    ) -> ContentGenerationJobRecord:
        """Administrative transition from 'processing' to 'review_required' without lease fencing."""
        job = await self.get_job(job_id, tenant_id)
        if not job:
            raise JobNotFoundError(f"Trabajo con ID {job_id} no encontrado.")

        if job.status != "processing":
            raise InvalidJobStateTransitionError(
                f"Transición administrativa a 'review_required' no permitida desde el estado '{job.status}'.",
                details={"job_id": job_id, "status": job.status},
            )

        now = datetime.now(UTC)
        job.status = "review_required"
        job.completed_at = now
        job.updated_at = now
        return job

    async def mark_failed(
        self,
        job_id: str,
        tenant_id: str,
        error_code: str,
        error_message_safe: str,
        lease_token: str | None = None,
    ) -> ContentGenerationJobRecord:
        """Transition to failed from any active state enforcing fencing token."""
        if lease_token is None:
            raise InvalidJobStateTransitionError(
                "Se requiere un lease_token UUID válido y no nulo para marcar el trabajo como fallido por un worker.",
                details={"job_id": job_id, "token_provided": False},
            )
        try:
            uuid.UUID(str(lease_token))
        except (ValueError, AttributeError) as e:
            raise InvalidJobStateTransitionError(
                f"El lease_token suministrado '{lease_token}' no es un UUID válido.",
                details={"job_id": job_id, "lease_token": str(lease_token)},
            ) from e

        job = await self.get_job(job_id, tenant_id)
        if not job:
            raise JobNotFoundError(f"Trabajo con ID {job_id} no encontrado.")

        if job.status in ("approved", "rejected"):
            raise InvalidJobStateTransitionError(
                f"No se puede fallar un trabajo que ya concluyó en '{job.status}'.",
                details={"job_id": job_id, "status": job.status},
            )

        if job.processing_lease_token is None or job.processing_lease_token != str(lease_token):
            raise InvalidJobStateTransitionError(
                "El lease_token no coincide con el worker actual o pertenece a otro worker.",
                details={
                    "job_id": job_id,
                    "expected_token": job.processing_lease_token,
                    "provided_token": str(lease_token),
                },
            )

        now = datetime.now(UTC)
        if job.processing_lease_expires_at is None or job.processing_lease_expires_at < now:
            raise InvalidJobStateTransitionError(
                "El lease de procesamiento ha expirado. No se puede finalizar el trabajo.",
                details={"job_id": job_id, "lease_expires_at": str(job.processing_lease_expires_at)},
            )

        job.status = "failed"
        job.error_code = error_code
        job.error_message_safe = error_message_safe
        job.completed_at = now
        job.updated_at = now
        return job

    async def admin_mark_failed(
        self,
        job_id: str,
        tenant_id: str,
        error_code: str,
        error_message_safe: str,
    ) -> ContentGenerationJobRecord:
        """Administrative transition to 'failed' without lease fencing."""
        job = await self.get_job(job_id, tenant_id)
        if not job:
            raise JobNotFoundError(f"Trabajo con ID {job_id} no encontrado.")

        if job.status in ("approved", "rejected"):
            raise InvalidJobStateTransitionError(
                f"No se puede fallar un trabajo que ya concluyó en '{job.status}'.",
                details={"job_id": job_id, "status": job.status},
            )

        now = datetime.now(UTC)
        job.status = "failed"
        job.error_code = error_code
        job.error_message_safe = error_message_safe
        job.completed_at = now
        job.updated_at = now
        return job

    async def recover_abandoned_jobs(
        self,
        tenant_id: str | None = None,
        job_id: str | None = None,
    ) -> int:
        """Mark abandoned processing jobs whose lease expired and reached max attempts as failed."""
        now = datetime.now(UTC)
        failed_count = 0
        for j in self._jobs.values():
            if (tenant_id is None or j.tenant_id == tenant_id) and (job_id is None or j.id == job_id):
                is_expired_max = (
                    j.status == "processing"
                    and j.processing_lease_expires_at is not None
                    and j.processing_lease_expires_at < now
                    and j.attempt_count >= j.max_attempts
                )
                is_queued_max = (
                    j.status == "queued"
                    and j.attempt_count >= j.max_attempts
                )
                if is_expired_max or is_queued_max:
                    j.status = "failed"
                    j.error_code = "MAX_ATTEMPTS_EXCEEDED"
                    j.error_message_safe = "El trabajo superó el límite máximo de reintentos permitidos tras expirar el lease."
                    j.completed_at = now
                    j.updated_at = now
                    failed_count += 1
        return failed_count

    async def claim_pending_job(
        self,
        tenant_id: str | None = None,
        lease_duration_seconds: int = 300,
        worker_token: str | None = None,
        job_id: str | None = None,
    ) -> ContentGenerationJobRecord | None:
        """Claim next queued or lease-expired job, auto-failing expired jobs with max attempts exceeded."""
        await self.recover_abandoned_jobs(tenant_id=tenant_id, job_id=job_id)
        now = datetime.now(UTC)
        candidates = [
            j for j in self._jobs.values()
            if (tenant_id is None or j.tenant_id == tenant_id)
            and (job_id is None or j.id == job_id)
        ]
        candidates.sort(key=lambda j: j.created_at or now)

        for job in candidates:
            is_queued = job.status == "queued" and job.attempt_count < job.max_attempts
            is_expired = (
                job.status == "processing"
                and job.processing_lease_expires_at is not None
                and job.processing_lease_expires_at < now
                and job.attempt_count < job.max_attempts
            )
            if is_queued or is_expired:
                token = worker_token or str(uuid.uuid4())
                job.status = "processing"
                job.started_at = job.started_at or now
                job.processing_started_at = now
                job.processing_lease_token = token
                job.processing_lease_expires_at = now + timedelta(seconds=lease_duration_seconds)
                job.attempt_count += 1
                job.last_heartbeat_at = now
                job.updated_at = now
                return job
        return None

    async def renew_lease(
        self,
        job_id: str,
        tenant_id: str,
        lease_token: str,
        extension_seconds: int = 300,
    ) -> ContentGenerationJobRecord:
        """Renew active lease."""
        job = await self.get_job(job_id, tenant_id)
        if not job:
            raise JobNotFoundError(f"Trabajo con ID {job_id} no encontrado.")
        now = datetime.now(UTC)
        if (
            job.status != "processing"
            or job.processing_lease_token != lease_token
            or job.processing_lease_expires_at is None
            or job.processing_lease_expires_at < now
        ):
            raise InvalidJobStateTransitionError(
                "No se puede renovar el lease: token inválido o trabajo fuera de procesamiento."
            )
        job.processing_lease_expires_at = now + timedelta(seconds=extension_seconds)
        job.last_heartbeat_at = now
        job.updated_at = now
        return job

    async def heartbeat(
        self,
        job_id: str,
        tenant_id: str,
        lease_token: str,
    ) -> bool:
        """Record heartbeat."""
        job = self._jobs.get(job_id)
        if not job or job.tenant_id != tenant_id:
            return False
        now = datetime.now(UTC)
        if (
            job.status != "processing"
            or job.processing_lease_token != lease_token
            or job.processing_lease_expires_at is None
            or job.processing_lease_expires_at < now
        ):
            return False
        job.last_heartbeat_at = now
        return True
