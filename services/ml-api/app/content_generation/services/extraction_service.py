"""Curriculum document extraction orchestration service.

Coordinates storage retrieval, security and integrity validation, format-specific
extractor delegation (PDF/PPTX), and job lifecycle state updates.
"""

from app.content_generation.exceptions import (
    ContentGenerationError,
    CorruptDocumentError,
    UnsupportedMimeTypeError,
)
from app.content_generation.extractors.base import BaseDocumentExtractor
from app.content_generation.extractors.pdf_extractor import PdfDocumentExtractor
from app.content_generation.extractors.pptx_extractor import PptxDocumentExtractor
from app.content_generation.repositories.job_repository import (
    JobRepositoryProtocol,
)
from app.content_generation.repositories.storage_client import (
    StorageClientProtocol,
)
from app.content_generation.schemas.extracted_document import (
    ExtractedDocument,
)
from app.content_generation.services.document_validation import (
    compute_sha256,
    validate_file_signature_and_mime,
    validate_storage_authorization,
    validate_teacher_job_access,
)


class DocumentExtractionService:
    """Service orchestrating end-to-end document extraction for teacher materials."""

    def __init__(
        self,
        job_repository: JobRepositoryProtocol | None = None,
        storage_client: StorageClientProtocol | None = None,
        extractors: list[BaseDocumentExtractor] | None = None,
    ) -> None:
        self._job_repository = job_repository
        self._storage_client = storage_client
        self._extractors: list[BaseDocumentExtractor] = extractors or [
            PdfDocumentExtractor(),
            PptxDocumentExtractor(),
        ]

    def _select_extractor(self, mime_type: str, filename: str) -> BaseDocumentExtractor:
        """Find the matching extractor for the validated MIME type and filename."""
        for extractor in self._extractors:
            if extractor.can_handle(mime_type, filename):
                return extractor
        raise UnsupportedMimeTypeError(
            f"No existe un extractor registrado para el tipo de archivo '{mime_type}'.",
            details={"mime_type": mime_type, "filename": filename},
        )

    def extract_from_bytes(
        self,
        file_bytes: bytes,
        original_filename: str,
        declared_mime: str,
        document_id: str | None = None,
    ) -> ExtractedDocument:
        """Validate and extract textual units directly from raw binary bytes.

        1. Performs security inspections (size, MIME, magic signature, zip defense).
        2. Computes SHA-256 checksum.
        3. Selects the appropriate extractor.
        4. Extracts ordered textual units with provenance (pages/slides).
        """
        # Validate binary structure and MIME
        validate_file_signature_and_mime(
            file_bytes=file_bytes,
            original_filename=original_filename,
            declared_mime=declared_mime,
        )

        checksum = compute_sha256(file_bytes)
        extractor = self._select_extractor(declared_mime, original_filename)

        return extractor.extract(
            file_bytes=file_bytes,
            original_filename=original_filename,
            file_checksum=checksum,
            mime_type=declared_mime,
            document_id=document_id,
        )

    async def process_job(
        self,
        job_id: str,
        tenant_id: str,
        requesting_user_id: str | None = None,
        user_role: str | None = None,
        authorized_course_ids: set[str] | list[str] | None = None,
        auto_complete_job: bool = True,
    ) -> ExtractedDocument:
        """Process a content generation job through document extraction.

        Transitions:
        queued -> processing -> (if auto_complete_job) review_required
                             -> (failure) failed
        """
        if not self._job_repository:
            raise CorruptDocumentError(
                "Repositorio de trabajos no configurado en el servicio."
            )
        if not self._storage_client:
            raise CorruptDocumentError(
                "Cliente de almacenamiento no configurado en el servicio."
            )

        # 1. Fetch job ensuring tenant isolation and teacher permissions
        job = await self._job_repository.get_job(
            job_id=job_id,
            tenant_id=tenant_id,
            requesting_user_id=requesting_user_id,
            user_role=user_role,
            authorized_course_ids=authorized_course_ids,
        )
        if not job:
            raise CorruptDocumentError(
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

        # 2. Validate storage path against tenant boundary
        validate_storage_authorization(
            storage_path=job.storage_path,
            tenant_id=tenant_id,
            storage_bucket=job.storage_bucket,
        )

        # 3. Transition to 'processing' if currently queued
        processing_token = job.processing_lease_token
        if job.status == "queued" or not processing_token:
            updated_job = await self._job_repository.mark_processing(
                job_id=job_id, tenant_id=tenant_id
            )
            processing_token = updated_job.processing_lease_token

        try:
            # 4. Download file from private storage
            file_bytes = await self._storage_client.download_file(
                storage_bucket=job.storage_bucket,
                storage_path=job.storage_path,
                tenant_id=tenant_id,
            )

            # 5. Extract document units
            extracted_doc = self.extract_from_bytes(
                file_bytes=file_bytes,
                original_filename=job.original_filename,
                declared_mime=job.mime_type,
                document_id=job_id,
            )

            # 6. Mark review_required only if standalone auto_complete_job is explicitly requested
            if auto_complete_job:
                await self._job_repository.mark_review_required(
                    job_id=job_id, tenant_id=tenant_id, lease_token=processing_token
                )

            return extracted_doc

        except ContentGenerationError as e:
            # Controlled domain failure -> update job to failed
            await self._job_repository.mark_failed(
                job_id=job_id,
                tenant_id=tenant_id,
                error_code=e.code,
                error_message_safe=e.message_safe,
                lease_token=processing_token,
            )
            raise

        except Exception as e:
            # Unhandled unexpected error -> safe failure without leaking internals
            safe_message = (
                "Ocurrió un error inesperado al procesar el material educativo."
            )
            await self._job_repository.mark_failed(
                job_id=job_id,
                tenant_id=tenant_id,
                error_code="UNEXPECTED_EXTRACTION_FAILURE",
                error_message_safe=safe_message,
                lease_token=processing_token,
            )
            raise ContentGenerationError(
                message_safe=safe_message,
                code="UNEXPECTED_EXTRACTION_FAILURE",
                status_code=500,
            ) from e

    async def extract_document_for_job(
        self,
        job_id: str,
        tenant_id: str,
        requesting_user_id: str | None = None,
        user_role: str | None = None,
        authorized_course_ids: set[str] | list[str] | None = None,
    ) -> ExtractedDocument:
        """Extract curriculum document for a job without transitioning to review_required.

        Leaves final lifecycle completion to the question generation orchestrator.
        """
        return await self.process_job(
            job_id=job_id,
            tenant_id=tenant_id,
            requesting_user_id=requesting_user_id,
            user_role=user_role,
            authorized_course_ids=authorized_course_ids,
            auto_complete_job=False,
        )
