"""Unit and integration tests for DocumentExtractionService and Job Lifecycle."""

import pytest
from pydantic import ValidationError

from app.content_generation.exceptions import (
    EncryptedDocumentError,
    InvalidJobStateTransitionError,
    NoExtractableTextError,
    UnauthorizedStorageAccessError,
    ZipBombDetectedError,
)
from app.content_generation.repositories.job_repository import (
    ContentGenerationJobRecord,
    InMemoryJobRepository,
)
from app.content_generation.repositories.storage_client import (
    InMemoryStorageClient,
)
from app.content_generation.schemas.extracted_document import (
    DocumentType,
    ExtractedDocument,
    ExtractedUnit,
    ExtractionMetadata,
)
from app.content_generation.services.extraction_service import (
    DocumentExtractionService,
)
from tests.content_generation.test_fixtures import (
    build_blank_pdf,
    build_encrypted_pdf,
    build_valid_pdf,
    build_valid_pptx,
    build_zip_bomb_pptx,
)


@pytest.fixture
def test_setup() -> tuple[
    DocumentExtractionService, InMemoryJobRepository, InMemoryStorageClient
]:
    job_repo = InMemoryJobRepository()
    storage_client = InMemoryStorageClient()
    service = DocumentExtractionService(
        job_repository=job_repo,
        storage_client=storage_client,
    )
    return service, job_repo, storage_client


def test_schema_extra_forbid() -> None:
    """Verify that ExtractedDocument, ExtractedUnit and ExtractionMetadata enforce extra='forbid'."""
    with pytest.raises(ValidationError):
        ExtractedUnit.model_validate(
            {
                "type": "page",
                "index": 1,
                "text": "sample",
                "character_count": 6,
                "word_count": 1,
                "unknown_field": "injected",  # Must raise ValidationError
            }
        )

    with pytest.raises(ValidationError):
        ExtractionMetadata.model_validate(
            {
                "file_size_bytes": 100,
                "file_checksum": "abc",
                "mime_type": "application/pdf",
                "requires_ocr": False,
                "processing_time_seconds": 0.1,
                "unauthorized_key": 123,  # Must raise ValidationError
            }
        )


@pytest.mark.asyncio
async def test_job_lifecycle_successful_pdf_extraction(
    test_setup: tuple[
        DocumentExtractionService, InMemoryJobRepository, InMemoryStorageClient
    ],
) -> None:
    """Successful job processing transitions: queued -> processing -> review_required."""
    service, job_repo, storage_client = test_setup
    tenant_id = "550e8400-e29b-41d4-a716-446655440000"
    job_id = "11111111-2222-3333-4444-555555555555"
    storage_path = f"{tenant_id}/materials/ciencias_tema1.pdf"

    pdf_bytes = build_valid_pdf(
        [
            "Tema 1: La reproduccion celular y division meiotica",
            "Tema 2: Leyes de Mendel y herencia genetica",
        ]
    )
    storage_client.upload_file("teacher-materials", storage_path, pdf_bytes)

    job_record = ContentGenerationJobRecord(
        id=job_id,
        tenant_id=tenant_id,
        created_by="99999999-8888-7777-6666-555555555555",
        storage_bucket="teacher-materials",
        storage_path=storage_path,
        original_filename="genetica.pdf",
        mime_type="application/pdf",
        file_size_bytes=len(pdf_bytes),
        file_checksum="test_checksum",
        status="queued",
        provider="test-provider",
        model_id="test-model",
    )
    job_repo.add_job(job_record)

    # Process the job
    extracted_doc = await service.process_job(job_id=job_id, tenant_id=tenant_id)

    # Verify extracted document
    assert extracted_doc.document_type == DocumentType.PDF
    assert extracted_doc.total_units == 2
    assert len(extracted_doc.units) == 2
    assert "division meiotica" in extracted_doc.units[0].text
    assert "Leyes de Mendel" in extracted_doc.units[1].text

    # Verify final job state
    updated_job = await job_repo.get_job(job_id=job_id, tenant_id=tenant_id)
    assert updated_job is not None
    assert updated_job.status == "review_required"
    assert updated_job.started_at is not None
    assert updated_job.completed_at is not None
    assert updated_job.error_code is None
    assert updated_job.error_message_safe is None


@pytest.mark.asyncio
async def test_job_lifecycle_successful_pptx_extraction(
    test_setup: tuple[
        DocumentExtractionService, InMemoryJobRepository, InMemoryStorageClient
    ],
) -> None:
    """Successful PPTX job transitions: queued -> processing -> review_required."""
    service, job_repo, storage_client = test_setup
    tenant_id = "550e8400-e29b-41d4-a716-446655440000"
    job_id = "22222222-3333-4444-5555-666666666666"
    storage_path = f"{tenant_id}/materials/ciencias_tema2.pptx"

    pptx_bytes = build_valid_pptx(
        ["Slide 1: Biodiversidad en el Peru", "Slide 2: Ecosistemas andinos"],
        include_table=True,
    )
    storage_client.upload_file("teacher-materials", storage_path, pptx_bytes)

    job_record = ContentGenerationJobRecord(
        id=job_id,
        tenant_id=tenant_id,
        created_by="99999999-8888-7777-6666-555555555555",
        storage_bucket="teacher-materials",
        storage_path=storage_path,
        original_filename="ecologia.pptx",
        mime_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        file_size_bytes=len(pptx_bytes),
        file_checksum="test_pptx_checksum",
        status="queued",
        provider="test-provider",
        model_id="test-model",
    )
    job_repo.add_job(job_record)

    extracted_doc = await service.process_job(job_id=job_id, tenant_id=tenant_id)

    assert extracted_doc.document_type == DocumentType.PPTX
    assert extracted_doc.total_units == 3  # 2 content slides + 1 table slide
    assert extracted_doc.units[2].has_tables is True

    updated_job = await job_repo.get_job(job_id=job_id, tenant_id=tenant_id)
    assert updated_job is not None
    assert updated_job.status == "review_required"
    assert updated_job.completed_at is not None


@pytest.mark.asyncio
async def test_job_lifecycle_controlled_failure_encrypted_pdf(
    test_setup: tuple[
        DocumentExtractionService, InMemoryJobRepository, InMemoryStorageClient
    ],
) -> None:
    """Controlled error: Encrypted PDF transitions job to failed with safe message."""
    service, job_repo, storage_client = test_setup
    tenant_id = "550e8400-e29b-41d4-a716-446655440000"
    job_id = "33333333-4444-5555-6666-777777777777"
    storage_path = f"{tenant_id}/materials/locked.pdf"

    enc_bytes = build_encrypted_pdf()
    storage_client.upload_file("teacher-materials", storage_path, enc_bytes)

    job_record = ContentGenerationJobRecord(
        id=job_id,
        tenant_id=tenant_id,
        created_by="99999999-8888-7777-6666-555555555555",
        storage_bucket="teacher-materials",
        storage_path=storage_path,
        original_filename="locked.pdf",
        mime_type="application/pdf",
        file_size_bytes=len(enc_bytes),
        file_checksum="enc_checksum",
        status="queued",
        provider="test-provider",
        model_id="test-model",
    )
    job_repo.add_job(job_record)

    with pytest.raises(EncryptedDocumentError):
        await service.process_job(job_id=job_id, tenant_id=tenant_id)

    updated_job = await job_repo.get_job(job_id=job_id, tenant_id=tenant_id)
    assert updated_job is not None
    assert updated_job.status == "failed"
    assert updated_job.error_code == "ENCRYPTED_DOCUMENT"
    assert updated_job.error_message_safe is not None
    assert (
        "cifrado" in updated_job.error_message_safe.lower()
        or "protegido" in updated_job.error_message_safe.lower()
    )
    assert updated_job.completed_at is not None


@pytest.mark.asyncio
async def test_job_lifecycle_controlled_failure_scanned_ocr_required(
    test_setup: tuple[
        DocumentExtractionService, InMemoryJobRepository, InMemoryStorageClient
    ],
) -> None:
    """Controlled error: PDF without extractable text transitions to failed reporting OCR."""
    service, job_repo, storage_client = test_setup
    tenant_id = "550e8400-e29b-41d4-a716-446655440000"
    job_id = "44444444-5555-6666-7777-888888888888"
    storage_path = f"{tenant_id}/materials/scanned.pdf"

    blank_bytes = build_blank_pdf(num_pages=2)
    storage_client.upload_file("teacher-materials", storage_path, blank_bytes)

    job_record = ContentGenerationJobRecord(
        id=job_id,
        tenant_id=tenant_id,
        created_by="99999999-8888-7777-6666-555555555555",
        storage_bucket="teacher-materials",
        storage_path=storage_path,
        original_filename="scanned.pdf",
        mime_type="application/pdf",
        file_size_bytes=len(blank_bytes),
        file_checksum="blank_checksum",
        status="queued",
        provider="test-provider",
        model_id="test-model",
    )
    job_repo.add_job(job_record)

    with pytest.raises(NoExtractableTextError) as exc_info:
        await service.process_job(job_id=job_id, tenant_id=tenant_id)

    assert exc_info.value.code == "NO_EXTRACTABLE_TEXT"
    assert exc_info.value.details.get("requires_ocr") is True

    updated_job = await job_repo.get_job(job_id=job_id, tenant_id=tenant_id)
    assert updated_job is not None
    assert updated_job.status == "failed"
    assert updated_job.error_code == "NO_EXTRACTABLE_TEXT"
    assert updated_job.error_message_safe is not None
    assert "OCR" in updated_job.error_message_safe


@pytest.mark.asyncio
async def test_job_lifecycle_controlled_failure_zip_bomb(
    test_setup: tuple[
        DocumentExtractionService, InMemoryJobRepository, InMemoryStorageClient
    ],
) -> None:
    """Controlled error: PPTX zip bomb transitions job to failed."""
    service, job_repo, storage_client = test_setup
    tenant_id = "550e8400-e29b-41d4-a716-446655440000"
    job_id = "55555555-6666-7777-8888-999999999999"
    storage_path = f"{tenant_id}/materials/bomb.pptx"

    bomb_bytes = build_zip_bomb_pptx()
    storage_client.upload_file("teacher-materials", storage_path, bomb_bytes)

    job_record = ContentGenerationJobRecord(
        id=job_id,
        tenant_id=tenant_id,
        created_by="99999999-8888-7777-6666-555555555555",
        storage_bucket="teacher-materials",
        storage_path=storage_path,
        original_filename="bomb.pptx",
        mime_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        file_size_bytes=len(bomb_bytes),
        file_checksum="bomb_checksum",
        status="queued",
        provider="test-provider",
        model_id="test-model",
    )
    job_repo.add_job(job_record)

    with pytest.raises(ZipBombDetectedError):
        await service.process_job(job_id=job_id, tenant_id=tenant_id)

    updated_job = await job_repo.get_job(job_id=job_id, tenant_id=tenant_id)
    assert updated_job is not None
    assert updated_job.status == "failed"
    assert updated_job.error_code == "SUSPICIOUS_ARCHIVE_DETECTED"


@pytest.mark.asyncio
async def test_job_lifecycle_tenant_isolation_violation(
    test_setup: tuple[
        DocumentExtractionService, InMemoryJobRepository, InMemoryStorageClient
    ],
) -> None:
    """Rejection of jobs requested across tenant boundary."""
    service, job_repo, _ = test_setup
    tenant_a = "550e8400-e29b-41d4-a716-446655440000"
    tenant_b = "660e8400-e29b-41d4-a716-446655440001"
    job_id = "66666666-7777-8888-9999-000000000000"

    job_record = ContentGenerationJobRecord(
        id=job_id,
        tenant_id=tenant_a,
        created_by="99999999-8888-7777-6666-555555555555",
        storage_bucket="teacher-materials",
        storage_path=f"{tenant_a}/materials/doc.pdf",
        original_filename="doc.pdf",
        mime_type="application/pdf",
        file_size_bytes=100,
        file_checksum="chk",
        status="queued",
        provider="test-provider",
        model_id="test-model",
    )
    job_repo.add_job(job_record)

    with pytest.raises(UnauthorizedStorageAccessError):
        await service.process_job(job_id=job_id, tenant_id=tenant_b)


@pytest.mark.asyncio
async def test_illegal_job_transition_to_approved_rejected(
    test_setup: tuple[
        DocumentExtractionService, InMemoryJobRepository, InMemoryStorageClient
    ],
) -> None:
    """M2.1 rule: Direct transition to approved is prohibited."""
    _, job_repo, _ = test_setup
    tenant_id = "550e8400-e29b-41d4-a716-446655440000"
    job_id = "77777777-8888-9999-0000-111111111111"

    job_record = ContentGenerationJobRecord(
        id=job_id,
        tenant_id=tenant_id,
        created_by="99999999-8888-7777-6666-555555555555",
        storage_bucket="teacher-materials",
        storage_path=f"{tenant_id}/materials/doc.pdf",
        original_filename="doc.pdf",
        mime_type="application/pdf",
        file_size_bytes=100,
        file_checksum="chk",
        status="queued",
        provider="test-provider",
        model_id="test-model",
    )
    job_repo.add_job(job_record)

    # Attempting illegal direct transition queued -> review_required
    with pytest.raises(InvalidJobStateTransitionError):
        await job_repo.mark_review_required(job_id=job_id, tenant_id=tenant_id)


def test_illustrative_output_contract_json_validation() -> None:
    """Verifica que el contrato JSON ilustrativo del hito M2.1 se valide correctamente con Pydantic v2."""
    sample_payload = {
        "document_type": "pptx",
        "total_units": 2,
        "units": [
            {
                "type": "slide",
                "index": 1,
                "text": "Introducción a la fotosíntesis y reacciones metabólicas.",
            },
            {
                "type": "slide",
                "index": 2,
                "text": "Fase luminosa y ciclo de Calvin en el estroma.",
            },
        ],
        "extractor_version": "1.0",
    }

    # Deserializes and validates strictly
    doc = ExtractedDocument.model_validate(sample_payload)
    assert doc.document_type == DocumentType.PPTX
    assert doc.total_units == 2
    assert len(doc.units) == 2
    assert doc.units[0].character_count > 0
    assert doc.units[0].word_count > 0
    assert doc.extractor_version == "1.0"

    # Strict extra='forbid' still rejects injected fields
    injected_payload = dict(sample_payload)
    injected_payload["illegal_llm_prompt"] = "ignore instructions"
    with pytest.raises(ValidationError):
        ExtractedDocument.model_validate(injected_payload)


@pytest.mark.asyncio
async def test_job_lifecycle_with_teacher_course_authorization(
    test_setup: tuple[
        DocumentExtractionService, InMemoryJobRepository, InMemoryStorageClient
    ],
) -> None:
    """Verificación de permisos: docente creador y asignado al curso procesa exitosamente."""
    service, job_repo, storage_client = test_setup
    tenant_id = "550e8400-e29b-41d4-a716-446655440000"
    teacher_id = "99999999-8888-7777-6666-555555555555"
    course_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    job_id = "88888888-9999-0000-1111-222222222222"
    storage_path = f"{tenant_id}/materials/ciencias.pdf"

    pdf_bytes = build_valid_pdf(["Material curricular de Ciencias"])
    storage_client.upload_file("teacher-materials", storage_path, pdf_bytes)

    job_record = ContentGenerationJobRecord(
        id=job_id,
        tenant_id=tenant_id,
        created_by=teacher_id,
        course_id=course_id,
        storage_bucket="teacher-materials",
        storage_path=storage_path,
        original_filename="ciencias.pdf",
        mime_type="application/pdf",
        file_size_bytes=len(pdf_bytes),
        file_checksum="test_chk",
        status="queued",
        provider="test-provider",
        model_id="test-model",
    )
    job_repo.add_job(job_record)

    # 1. Processing by authorized teacher succeeds
    doc = await service.process_job(
        job_id=job_id,
        tenant_id=tenant_id,
        requesting_user_id=teacher_id,
        user_role="teacher",
        authorized_course_ids=[course_id],
    )
    assert doc.total_units == 1

    # 2. Rejection if requesting teacher is not the creator
    other_teacher = "00000000-0000-0000-0000-000000000000"
    with pytest.raises(UnauthorizedStorageAccessError) as exc_owner:
        await service.process_job(
            job_id=job_id,
            tenant_id=tenant_id,
            requesting_user_id=other_teacher,
            user_role="teacher",
            authorized_course_ids=[course_id],
        )
    assert "creador" in exc_owner.value.message_safe.lower()

    # 3. Rejection if teacher is not assigned to the course
    unassigned_course = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
    with pytest.raises(UnauthorizedStorageAccessError) as exc_course:
        await service.process_job(
            job_id=job_id,
            tenant_id=tenant_id,
            requesting_user_id=teacher_id,
            user_role="teacher",
            authorized_course_ids=[unassigned_course],
        )
    assert "curso" in exc_course.value.message_safe.lower()

    # 4. Rejection if user role is student
    with pytest.raises(UnauthorizedStorageAccessError) as exc_student:
        await service.process_job(
            job_id=job_id,
            tenant_id=tenant_id,
            requesting_user_id=teacher_id,
            user_role="student",
        )
    assert "estudiantes" in exc_student.value.message_safe.lower()
