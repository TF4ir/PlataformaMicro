"""Orchestrator for end-to-end curriculum content generation workflow.

Coordinates:
1. Authorized job retrieval and teacher permission verification.
2. Controlled transition to 'processing'.
3. Ingestion and extraction of structured document units (pages/slides).
4. LLM provider selection via decoupled factory.
5. Assisted question draft generation and provenance validation.
6. Quarantine persistence into question_drafts with idempotency and teacher review protection.
7. Atomic lifecycle transition to 'review_required' only after persistence succeeds.
"""

import logging
from typing import Any

from app.content_generation.exceptions import (
    ContentGenerationError,
    DraftAlreadyReviewedError,
    InvalidJobStateTransitionError,
    JobNotFoundError,
)
from app.content_generation.infrastructure.unit_of_work import (
    GenerationUnitOfWorkProtocol,
)
from app.content_generation.providers.base import QuestionGenerationProvider
from app.content_generation.providers.factory import get_llm_provider
from app.content_generation.repositories.draft_repository import (
    DraftRepositoryProtocol,
)
from app.content_generation.repositories.job_repository import (
    JobRepositoryProtocol,
)
from app.content_generation.schemas.generated_questions import (
    GenerationContext,
    QuestionDraftRecord,
)
from app.content_generation.services.document_validation import (
    validate_teacher_job_access,
)
from app.content_generation.services.extraction_service import (
    DocumentExtractionService,
)
from app.content_generation.services.question_generation_service import (
    QuestionGenerationService,
)

logger = logging.getLogger(__name__)


class GenerationOrchestrator:
    """Coordinates the end-to-end question generation lifecycle for curriculum documents."""

    def __init__(
        self,
        job_repository: JobRepositoryProtocol,
        extraction_service: DocumentExtractionService,
        generation_service: QuestionGenerationService,
        draft_repository: DraftRepositoryProtocol,
        provider: QuestionGenerationProvider | None = None,
        unit_of_work: GenerationUnitOfWorkProtocol | None = None,
    ) -> None:
        self._job_repository = job_repository
        self._extraction_service = extraction_service
        self._generation_service = generation_service
        self._draft_repository = draft_repository
        self._provider = provider
        self._unit_of_work = unit_of_work

    async def execute_job(
        self,
        job_id: str,
        tenant_id: str,
        requesting_user_id: str | None = None,
        user_role: str | None = None,
        authorized_course_ids: set[str] | list[str] | None = None,
        target_num_questions: int = 5,
        generation_schema: dict[str, Any] | None = None,
        lease_token: str | None = None,
    ) -> list[QuestionDraftRecord]:
        """Execute the full question generation workflow for an authorized job.

        Lifecycle:
        queued -> processing -> (generation + validation + persistence) -> review_required
                             -> (failure in any phase) -> failed

        Args:
            job_id: ID of the generation job.
            tenant_id: Tenant institution ID.
            requesting_user_id: ID of the requesting teacher/admin.
            user_role: Role of the requesting user.
            authorized_course_ids: Course IDs assigned to the teacher.
            target_num_questions: Target number of questions to generate.
            generation_schema: Optional JSON schema for structured generation.

        Returns:
            List of QuestionDraftRecord objects safely quarantined in question_drafts.

        Raises:
            ContentGenerationError: On any controlled domain error, ensuring the job transitions to 'failed'.
        """
        # 1. Fetch job ensuring tenant isolation and teacher permissions
        job = await self._job_repository.get_job(
            job_id=job_id,
            tenant_id=tenant_id,
            requesting_user_id=requesting_user_id,
            user_role=user_role,
            authorized_course_ids=authorized_course_ids,
        )
        if not job:
            raise JobNotFoundError(
                f"El trabajo de generación {job_id} no existe o no pertenece al tenant.",
                details={"job_id": job_id},
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

        # 2. Concurrency and Idempotency Guard
        if job.status == "processing" and (
            lease_token is None or job.processing_lease_token != lease_token
        ):
            raise InvalidJobStateTransitionError(
                f"El trabajo {job_id} ya se encuentra en procesamiento activo. No se permiten ejecuciones concurrentes.",
                details={"job_id": job_id, "status": job.status},
            )
        if job.status in ("approved", "rejected"):
            raise InvalidJobStateTransitionError(
                f"El trabajo {job_id} ya alcanzó un estado terminal '{job.status}' y no puede reejecutarse.",
                details={"job_id": job_id, "status": job.status},
            )

        # 3. Check for existing teacher-reviewed drafts
        existing_drafts = await self._draft_repository.get_drafts_by_job(
            job_id, tenant_id
        )
        for existing in existing_drafts:
            if existing.status != "draft":
                raise DraftAlreadyReviewedError(
                    f"No se puede reiniciar el trabajo {job_id} porque contiene borradores que ya han sido "
                    f"revisados o aprobados por un docente (borrador: {existing.id}, estado: {existing.status}).",
                    details={
                        "job_id": job_id,
                        "draft_id": existing.id,
                        "status": existing.status,
                    },
                )

        # 4. Transition to 'processing' via repository if not already in processing
        if job.status != "processing" or (lease_token and job.processing_lease_token != lease_token):
            updated_job = await self._job_repository.mark_processing(
                job_id=job_id, tenant_id=tenant_id, lease_token=lease_token
            )
            if lease_token is None and updated_job.processing_lease_token:
                lease_token = updated_job.processing_lease_token
        elif lease_token is None:
            lease_token = job.processing_lease_token

        if lease_token is None:
            updated_job = await self._job_repository.mark_processing(
                job_id=job_id, tenant_id=tenant_id, lease_token=None
            )
            lease_token = updated_job.processing_lease_token

        try:
            # 5. Extract document units (without marking job as review_required)
            extracted_doc = await self._extraction_service.extract_document_for_job(
                job_id=job_id,
                tenant_id=tenant_id,
                requesting_user_id=requesting_user_id,
                user_role=user_role,
                authorized_course_ids=authorized_course_ids,
            )

            # 6. Resolve LLM provider via factory
            provider = self._provider or get_llm_provider(
                provider_name=job.provider,
                model_id=job.model_id,
            )

            # 7. Build generation context
            context = GenerationContext(
                job_id=job.id,
                tenant_id=job.tenant_id,
                course_id=job.course_id,
                unit_id=job.unit_id,
                language="es",
                target_num_questions=target_num_questions,
                prompt_version=job.prompt_version,
                document_units=extracted_doc.units,
                original_filename=job.original_filename,
                document_type=extracted_doc.document_type.value,
            )

            # 8. Generate drafts and strictly validate against source document
            validated_drafts = await self._generation_service.generate_and_validate(
                document=extracted_doc,
                context=context,
                provider=provider,
                schema=generation_schema,
            )

            # 9 & 10. Atomically persist drafts and mark review_required
            if self._unit_of_work is not None:
                _, persisted_records = await self._unit_of_work.commit_generation_results(
                    job_id=job.id,
                    tenant_id=job.tenant_id,
                    drafts=validated_drafts,
                    lease_token=lease_token,
                )
            else:
                persisted_records = await self._draft_repository.save_drafts(
                    job_id=job.id,
                    tenant_id=job.tenant_id,
                    drafts=validated_drafts,
                )
                await self._job_repository.mark_review_required(
                    job_id=job.id, tenant_id=tenant_id, lease_token=lease_token
                )

            return persisted_records

        except ContentGenerationError as e:
            # Controlled domain failure -> mark job as failed with safe message
            logger.warning(
                "Controlled failure during question generation for job %s: [%s] %s",
                job_id,
                e.code,
                e.message_safe,
            )
            await self._job_repository.mark_failed(
                job_id=job_id,
                tenant_id=tenant_id,
                error_code=e.code,
                error_message_safe=e.message_safe,
                lease_token=lease_token,
            )
            raise

        except Exception as e:
            # Unexpected system error -> mark job as failed with safe sanitized message
            logger.exception(
                "Unexpected failure during generation orchestration for job %s", job_id
            )
            safe_message = "Ocurrió un error inesperado al generar las preguntas a partir del material educativo."
            await self._job_repository.mark_failed(
                job_id=job_id,
                tenant_id=tenant_id,
                error_code="UNEXPECTED_GENERATION_FAILURE",
                error_message_safe=safe_message,
                lease_token=lease_token,
            )
            raise ContentGenerationError(
                message_safe=safe_message,
                code="UNEXPECTED_GENERATION_FAILURE",
                status_code=500,
            ) from e
