"""Comprehensive test suite for Milestone M2.2: LLM Provider Agnostic Adapter,

Draft Generation, Schema Validation, Provenance Verification, and Draft Quarantine.
"""

from typing import Any

import pytest
from pydantic import ValidationError

from app.content_generation.exceptions import (
    DraftAlreadyReviewedError,
    DuplicateOptionsError,
    EmptyDraftsError,
    EmptyExplanationError,
    EmptyOptionTextError,
    EmptyQuestionTextError,
    GenerationProviderError,
    InvalidCorrectOptionsCountError,
    InvalidDifficultyError,
    InvalidJobStateTransitionError,
    InvalidOptionsCountError,
    InvalidSourceReferenceError,
    SnippetNotFoundError,
    UnauthorizedFieldsError,
    UnprocessedHtmlError,
    UnsupportedProviderError,
)
from app.content_generation.providers.factory import get_llm_provider
from app.content_generation.providers.mock_provider import (
    MockBehaviorMode,
    MockQuestionGenerationProvider,
)
from app.content_generation.repositories.draft_repository import (
    InMemoryDraftRepository,
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
    DocumentUnitType,
    ExtractedDocument,
    ExtractedUnit,
)
from app.content_generation.schemas.generated_questions import (
    BloomTaxonomy,
    GeneratedQuestionDraft,
    GenerationContext,
    QuestionDraftRecord,
    QuestionOptionDraft,
    QuestionSourceReference,
    QuestionType,
)
from app.content_generation.services.draft_validation_service import (
    DraftValidationService,
)
from app.content_generation.services.extraction_service import (
    DocumentExtractionService,
)
from app.content_generation.services.generation_orchestrator import (
    GenerationOrchestrator,
)
from app.content_generation.services.question_generation_service import (
    QuestionGenerationService,
)
from tests.content_generation.test_fixtures import (
    build_valid_pdf,
    build_valid_pptx,
)


@pytest.fixture
def sample_extracted_document() -> ExtractedDocument:
    """Fixture providing a synthetic ExtractedDocument with realistic educational content."""
    unit1 = ExtractedUnit(
        type=DocumentUnitType.PAGE,
        index=1,
        text=(
            "Capitulo 1: Fundamentos de la Fotosintesis Celular.\n"
            "La fase luminosa de la fotosintesis ocurre en las membranas de los tilacoides. "
            "Durante este proceso, la energia solar se convierte en ATP y NADPH, liberando oxigeno molecular."
        ),
    )
    unit2 = ExtractedUnit(
        type=DocumentUnitType.PAGE,
        index=2,
        text=(
            "Capitulo 2: El Ciclo de Calvin y Fijacion de Carbono.\n"
            "En el estroma del cloroplasto, el dioxido de carbono se fija enzimaticamente mediante la Rubisco "
            "para sintetizar moleculas precursoras de glucosa."
        ),
    )
    return ExtractedDocument(
        document_id="doc-fotosintesis-101",
        document_type=DocumentType.PDF,
        original_filename="fotosintesis_secundaria.pdf",
        total_units=2,
        units=[unit1, unit2],
    )


@pytest.fixture
def generation_fixtures() -> tuple[
    InMemoryJobRepository,
    InMemoryStorageClient,
    InMemoryDraftRepository,
    DocumentExtractionService,
    DraftValidationService,
    QuestionGenerationService,
    GenerationOrchestrator,
]:
    """Assemble isolated in-memory test harness for content generation orchestrator."""
    job_repo = InMemoryJobRepository()
    storage_client = InMemoryStorageClient()
    draft_repo = InMemoryDraftRepository()

    extraction_service = DocumentExtractionService(
        job_repository=job_repo,
        storage_client=storage_client,
    )
    validation_service = DraftValidationService()
    generation_service = QuestionGenerationService(
        validation_service=validation_service,
    )
    orchestrator = GenerationOrchestrator(
        job_repository=job_repo,
        extraction_service=extraction_service,
        generation_service=generation_service,
        draft_repository=draft_repo,
    )
    return (
        job_repo,
        storage_client,
        draft_repo,
        extraction_service,
        validation_service,
        generation_service,
        orchestrator,
    )


# ==============================================================================
# 1. Carga del proveedor simulado mediante la factoría
# ==============================================================================


def test_factory_load_mock_provider() -> None:
    """Verify loading MockQuestionGenerationProvider via factory with default and custom settings."""
    provider = get_llm_provider()
    assert isinstance(provider, MockQuestionGenerationProvider)
    assert provider.provider_name == "mock"
    assert provider.model_id == "mock-v1"

    custom_provider = get_llm_provider(
        provider_name="mock",
        model_id="custom-model-2026",
        behavior_mode=MockBehaviorMode.VALID,
    )
    assert custom_provider.model_id == "custom-model-2026"


# ==============================================================================
# 2. Configuración de proveedor no soportado
# ==============================================================================


def test_factory_unsupported_provider_raises_error() -> None:
    """Verify factory rejects unsupported providers safely without revealing credentials or internal paths."""
    with pytest.raises(UnsupportedProviderError) as exc_info:
        get_llm_provider(provider_name="unsupported_cloud_ai", model_id="gpt-5")

    err = exc_info.value
    assert err.code == "UNSUPPORTED_LLM_PROVIDER"
    assert "no está implementado" in err.message_safe


# ==============================================================================
# 3. Generación válida de preguntas
# ==============================================================================


@pytest.mark.asyncio
async def test_valid_question_generation(
    sample_extracted_document: ExtractedDocument,
) -> None:
    """Verify deterministic valid question generation and provenance validation."""
    provider = MockQuestionGenerationProvider(behavior_mode=MockBehaviorMode.VALID)
    validation_service = DraftValidationService()
    generation_service = QuestionGenerationService(
        provider=provider,
        validation_service=validation_service,
    )

    context = GenerationContext(
        job_id="job-uuid-1",
        tenant_id="tenant-uuid-1",
        target_num_questions=2,
    )

    drafts = await generation_service.generate_and_validate(
        document=sample_extracted_document,
        context=context,
    )

    assert len(drafts) == 2
    for draft in drafts:
        assert len(draft.question_text) > 0
        assert len(draft.options) >= 2
        assert sum(1 for opt in draft.options if opt.is_correct) == 1
        assert len(draft.source_references) >= 1
        assert draft.numeric_difficulty in (0.3, 0.5, 0.8)


# ==============================================================================
# 4. Pregunta sin alternativa correcta
# ==============================================================================


def test_question_without_correct_option_rejected() -> None:
    """Verify validation rejection when all options have is_correct=False."""
    with pytest.raises(InvalidCorrectOptionsCountError) as exc_info:
        GeneratedQuestionDraft(
            suggested_kc_name="Fotosíntesis",
            question_text="¿Dónde ocurre la fase luminosa?",
            question_type=QuestionType.SINGLE_CHOICE,
            options=[
                QuestionOptionDraft(text="En el estroma", is_correct=False),
                QuestionOptionDraft(text="En el citoplasma", is_correct=False),
                QuestionOptionDraft(text="En la mitocondria", is_correct=False),
                QuestionOptionDraft(text="En el núcleo", is_correct=False),
            ],
            explanation="Ocurre en la membrana tilacoidal.",
            source_references=[
                QuestionSourceReference(
                    type=DocumentUnitType.PAGE,
                    index=1,
                    snippet="membranas de los tilacoides",
                )
            ],
        )

    assert exc_info.value.code == "INVALID_CORRECT_OPTIONS_COUNT"


# ==============================================================================
# 5. Pregunta con más de una alternativa correcta
# ==============================================================================


def test_question_with_multiple_correct_options_rejected() -> None:
    """Verify single_choice question rejects multiple options marked is_correct=True."""
    with pytest.raises(InvalidCorrectOptionsCountError) as exc_info:
        GeneratedQuestionDraft(
            suggested_kc_name="Fotosíntesis",
            question_text="¿Dónde ocurre la fase luminosa?",
            question_type=QuestionType.SINGLE_CHOICE,
            options=[
                QuestionOptionDraft(text="En los tilacoides", is_correct=True),
                QuestionOptionDraft(text="En la membrana tilacoidal", is_correct=True),
                QuestionOptionDraft(text="En la mitocondria", is_correct=False),
                QuestionOptionDraft(text="En el núcleo", is_correct=False),
            ],
            explanation="La fase luminosa ocurre en los tilacoides.",
            source_references=[
                QuestionSourceReference(
                    type=DocumentUnitType.PAGE,
                    index=1,
                    snippet="membranas de los tilacoides",
                )
            ],
        )

    assert exc_info.value.code == "INVALID_CORRECT_OPTIONS_COUNT"


# ==============================================================================
# 6. Alternativas duplicadas tras normalización
# ==============================================================================


def test_duplicate_options_rejected() -> None:
    """Verify duplicate options after whitespace and case normalization are rejected."""
    with pytest.raises(DuplicateOptionsError) as exc_info:
        GeneratedQuestionDraft(
            suggested_kc_name="Fotosíntesis",
            question_text="¿Dónde ocurre la fase luminosa?",
            question_type=QuestionType.SINGLE_CHOICE,
            options=[
                QuestionOptionDraft(text="En los tilacoides", is_correct=True),
                QuestionOptionDraft(
                    text=" en  los  tilacoides ", is_correct=False
                ),  # Duplicate normalized!
                QuestionOptionDraft(text="En el estroma", is_correct=False),
                QuestionOptionDraft(text="En la mitocondria", is_correct=False),
            ],
            explanation="Ocurre en los tilacoides.",
            source_references=[
                QuestionSourceReference(
                    type=DocumentUnitType.PAGE,
                    index=1,
                    snippet="membranas de los tilacoides",
                )
            ],
        )

    assert exc_info.value.code == "DUPLICATE_OPTIONS"


# ==============================================================================
# 7. Referencias a páginas inexistentes
# ==============================================================================


def test_nonexistent_page_reference_rejected(
    sample_extracted_document: ExtractedDocument,
) -> None:
    """Verify rejection when question references a page/slide index not in the document."""
    validation_service = DraftValidationService()

    invalid_draft = GeneratedQuestionDraft(
        suggested_kc_name="Fotosíntesis",
        question_text="¿Dónde ocurre la fase luminosa?",
        question_type=QuestionType.SINGLE_CHOICE,
        options=[
            QuestionOptionDraft(text="En los tilacoides", is_correct=True),
            QuestionOptionDraft(text="En el estroma", is_correct=False),
        ],
        explanation="Ocurre en los tilacoides.",
        source_references=[
            QuestionSourceReference(
                type=DocumentUnitType.PAGE,
                index=99,  # Document only has 2 pages!
                snippet="membranas de los tilacoides",
            )
        ],
    )

    with pytest.raises(InvalidSourceReferenceError) as exc_info:
        validation_service.validate_drafts([invalid_draft], sample_extracted_document)

    assert exc_info.value.code == "INVALID_SOURCE_REFERENCE"


# ==============================================================================
# 8. Fragmentos que no pertenecen al documento (Alucinación)
# ==============================================================================


def test_hallucinated_snippet_rejected(
    sample_extracted_document: ExtractedDocument,
) -> None:
    """Verify rejection when cited snippet is not present in the referenced page."""
    validation_service = DraftValidationService()

    hallucinated_draft = GeneratedQuestionDraft(
        suggested_kc_name="Fotosíntesis",
        question_text="¿Dónde ocurre la fase luminosa?",
        question_type=QuestionType.SINGLE_CHOICE,
        options=[
            QuestionOptionDraft(text="En los tilacoides", is_correct=True),
            QuestionOptionDraft(text="En el estroma", is_correct=False),
        ],
        explanation="Ocurre en los tilacoides.",
        source_references=[
            QuestionSourceReference(
                type=DocumentUnitType.PAGE,
                index=1,
                snippet="Este texto nunca existio en el documento original sobre fotosintesis celular.",
            )
        ],
    )

    with pytest.raises(SnippetNotFoundError) as exc_info:
        validation_service.validate_drafts(
            [hallucinated_draft], sample_extracted_document
        )

    assert exc_info.value.code == "SNIPPET_NOT_FOUND"


# ==============================================================================
# 9. Respuestas con campos no autorizados (extra='forbid')
# ==============================================================================


def test_extra_unauthorized_fields_rejected() -> None:
    """Verify that extra forbidden fields in generated questions are strictly rejected by Pydantic."""
    raw_question_dict = {
        "suggested_kc_name": "Fotosíntesis",
        "question_text": "¿Dónde ocurre la fase luminosa?",
        "question_type": "single_choice",
        "options": [
            {"text": "En los tilacoides", "is_correct": True},
            {"text": "En el estroma", "is_correct": False},
        ],
        "explanation": "Ocurre en los tilacoides.",
        "source_references": [
            {"type": "page", "index": 1, "snippet": "membranas de los tilacoides"}
        ],
        "injected_unauthorized_payload": "SELECT * FROM passwords;",  # Forbidden field!
    }

    with pytest.raises(ValidationError):
        GeneratedQuestionDraft.model_validate(raw_question_dict)


# ==============================================================================
# 10. Persistencia de borradores válidos
# ==============================================================================


@pytest.mark.asyncio
async def test_persistence_of_valid_drafts(
    sample_extracted_document: ExtractedDocument,
) -> None:
    """Verify valid drafts are safely quarantined in InMemoryDraftRepository with all metadata."""
    draft_repo = InMemoryDraftRepository()
    tenant_id = "tenant-1111-1111-1111"
    job_id = "job-1111-1111-1111"

    draft = GeneratedQuestionDraft(
        suggested_kc_name="Fase luminosa",
        question_text="¿Dónde ocurre la fase luminosa?",
        question_type=QuestionType.SINGLE_CHOICE,
        difficulty=0.500,
        bloom_taxonomy=BloomTaxonomy.UNDERSTAND,
        options=[
            QuestionOptionDraft(text="En los tilacoides", is_correct=True),
            QuestionOptionDraft(text="En el estroma", is_correct=False),
        ],
        explanation="Ocurre en los tilacoides.",
        source_references=[
            QuestionSourceReference(
                type=DocumentUnitType.PAGE,
                index=1,
                snippet="membranas de los tilacoides",
            )
        ],
    )

    records = await draft_repo.save_drafts(
        job_id=job_id, tenant_id=tenant_id, drafts=[draft]
    )

    assert len(records) == 1
    record = records[0]
    assert record.generation_job_id == job_id
    assert record.tenant_id == tenant_id
    assert record.status == "draft"
    assert record.suggested_kc_name == "Fase luminosa"
    assert record.suggested_difficulty == 0.500
    assert record.suggested_bloom_level == "understand"
    assert len(record.options) == 2
    assert record.options[0]["is_correct"] is True
    assert record.approved_question_id is None


# ==============================================================================
# 11. Rechazo de borradores inválidos en orquestador
# ==============================================================================


@pytest.mark.asyncio
async def test_orchestrator_rejects_invalid_drafts_and_marks_failed(
    generation_fixtures: tuple[
        InMemoryJobRepository,
        InMemoryStorageClient,
        InMemoryDraftRepository,
        DocumentExtractionService,
        DraftValidationService,
        QuestionGenerationService,
        GenerationOrchestrator,
    ],
) -> None:
    """Verify that when generated draft fails validation, job transitions to failed and repository has 0 drafts."""
    job_repo, storage_client, draft_repo, _, _, _, orchestrator = generation_fixtures

    tenant_id = "550e8400-e29b-41d4-a716-446655440000"
    job_id = "job-fail-validation-1"
    storage_path = f"{tenant_id}/materials/ciencias.pdf"

    pdf_bytes = build_valid_pdf(["Texto de prueba sobre bioelementos y carbohidratos."])
    storage_client.upload_file("teacher-materials", storage_path, pdf_bytes)

    job_repo.add_job(
        ContentGenerationJobRecord(
            id=job_id,
            tenant_id=tenant_id,
            created_by="teacher-1",
            storage_bucket="teacher-materials",
            storage_path=storage_path,
            original_filename="ciencias.pdf",
            mime_type="application/pdf",
            file_size_bytes=len(pdf_bytes),
            file_checksum="checksum-1",
            status="queued",
            provider="mock",
            model_id="mock-v1",
        )
    )

    # Inject mock provider with fabricated snippet mode
    mock_provider = MockQuestionGenerationProvider(
        behavior_mode=MockBehaviorMode.FABRICATED_SNIPPET
    )
    orchestrator._provider = mock_provider

    with pytest.raises(SnippetNotFoundError):
        await orchestrator.execute_job(job_id=job_id, tenant_id=tenant_id)

    # Job must be in 'failed' status, NOT 'review_required'
    job = await job_repo.get_job(job_id, tenant_id)
    assert job is not None
    assert job.status == "failed"
    assert job.error_code == "SNIPPET_NOT_FOUND"

    # Draft repository must be empty
    drafts = await draft_repo.get_drafts_by_job(job_id, tenant_id)
    assert len(drafts) == 0


# ==============================================================================
# 12. Aislamiento entre trabajos y tenants
# ==============================================================================


@pytest.mark.asyncio
async def test_multi_tenant_and_job_draft_isolation() -> None:
    """Verify drafts are strictly isolated across tenants and generation jobs."""
    draft_repo = InMemoryDraftRepository()
    tenant_a = "tenant-aaaa"
    tenant_b = "tenant-bbbb"
    job_a = "job-a1"
    job_b = "job-b1"

    draft_a = GeneratedQuestionDraft(
        suggested_kc_name="KC-A",
        question_text="Pregunta Tenant A",
        options=[
            QuestionOptionDraft(text="Correcta A", is_correct=True),
            QuestionOptionDraft(text="Incorrecta A", is_correct=False),
        ],
        explanation="Explicación A",
        source_references=[
            QuestionSourceReference(
                type=DocumentUnitType.PAGE, index=1, snippet="texto A"
            )
        ],
    )

    draft_b = GeneratedQuestionDraft(
        suggested_kc_name="KC-B",
        question_text="Pregunta Tenant B",
        options=[
            QuestionOptionDraft(text="Correcta B", is_correct=True),
            QuestionOptionDraft(text="Incorrecta B", is_correct=False),
        ],
        explanation="Explicación B",
        source_references=[
            QuestionSourceReference(
                type=DocumentUnitType.SLIDE, index=1, snippet="texto B"
            )
        ],
    )

    await draft_repo.save_drafts(job_a, tenant_a, [draft_a])
    await draft_repo.save_drafts(job_b, tenant_b, [draft_b])

    # Tenant A querying its drafts
    drafts_a = await draft_repo.get_drafts_by_job(job_a, tenant_a)
    assert len(drafts_a) == 1
    assert drafts_a[0].suggested_kc_name == "KC-A"

    # Tenant B querying Job A should return nothing
    drafts_b_queried_a = await draft_repo.get_drafts_by_job(job_a, tenant_b)
    assert len(drafts_b_queried_a) == 0

    # Cross-tenant direct draft ID query must return None
    draft_a_id = drafts_a[0].id
    cross_access = await draft_repo.get_draft_by_id(draft_a_id, tenant_id=tenant_b)
    assert cross_access is None


# ==============================================================================
# 13. Idempotencia ante reintentos
# ==============================================================================


@pytest.mark.asyncio
async def test_retry_idempotency_does_not_duplicate_drafts() -> None:
    """Verify retrying a job with unreviewed drafts replaces them cleanly without duplication."""
    draft_repo = InMemoryDraftRepository()
    tenant_id = "tenant-test"
    job_id = "job-retry-1"

    draft1 = GeneratedQuestionDraft(
        suggested_kc_name="KC-1",
        question_text="Pregunta intento 1",
        options=[
            QuestionOptionDraft(text="Correcta 1", is_correct=True),
            QuestionOptionDraft(text="Incorrecta 1", is_correct=False),
        ],
        explanation="Explicación 1",
        source_references=[
            QuestionSourceReference(
                type=DocumentUnitType.PAGE, index=1, snippet="texto 1"
            )
        ],
    )

    # First attempt persists 1 draft
    records1 = await draft_repo.save_drafts(job_id, tenant_id, [draft1])
    assert len(records1) == 1
    assert len(await draft_repo.get_drafts_by_job(job_id, tenant_id)) == 1

    # Retry with 2 new drafts replaces previous unreviewed drafts
    draft2_a = GeneratedQuestionDraft(
        suggested_kc_name="KC-2A",
        question_text="Pregunta intento 2A",
        options=[
            QuestionOptionDraft(text="Correcta 2A", is_correct=True),
            QuestionOptionDraft(text="Incorrecta 2A", is_correct=False),
        ],
        explanation="Explicación 2A",
        source_references=[
            QuestionSourceReference(
                type=DocumentUnitType.PAGE, index=1, snippet="texto 2A"
            )
        ],
    )
    draft2_b = GeneratedQuestionDraft(
        suggested_kc_name="KC-2B",
        question_text="Pregunta intento 2B",
        options=[
            QuestionOptionDraft(text="Correcta 2B", is_correct=True),
            QuestionOptionDraft(text="Incorrecta 2B", is_correct=False),
        ],
        explanation="Explicación 2B",
        source_references=[
            QuestionSourceReference(
                type=DocumentUnitType.PAGE, index=1, snippet="texto 2B"
            )
        ],
    )

    records2 = await draft_repo.save_drafts(job_id, tenant_id, [draft2_a, draft2_b])
    assert len(records2) == 2

    # Verify no duplicates accumulated: exactly 2 drafts exist for job
    stored = await draft_repo.get_drafts_by_job(job_id, tenant_id)
    assert len(stored) == 2
    assert {d.suggested_kc_name for d in stored} == {"KC-2A", "KC-2B"}


# ==============================================================================
# 14. Protección de borradores editados o aprobados
# ==============================================================================


@pytest.mark.asyncio
async def test_protection_of_reviewed_drafts_blocks_overwrite() -> None:
    """Verify that if a draft has been edited, approved, or rejected, retrying raises DraftAlreadyReviewedError."""
    draft_repo = InMemoryDraftRepository()
    tenant_id = "tenant-test"
    job_id = "job-reviewed-1"

    draft = GeneratedQuestionDraft(
        suggested_kc_name="KC-Docente",
        question_text="Pregunta inicial",
        options=[
            QuestionOptionDraft(text="Correcta", is_correct=True),
            QuestionOptionDraft(text="Incorrecta", is_correct=False),
        ],
        explanation="Explicación",
        source_references=[
            QuestionSourceReference(
                type=DocumentUnitType.PAGE, index=1, snippet="texto"
            )
        ],
    )

    records = await draft_repo.save_drafts(job_id, tenant_id, [draft])
    draft_id = records[0].id

    # Simulate teacher review: status -> edited
    draft_repo.mark_draft_status_for_testing(draft_id, status="edited")

    # Attempt to overwrite must be rejected
    with pytest.raises(DraftAlreadyReviewedError) as exc_info:
        await draft_repo.save_drafts(job_id, tenant_id, [draft])

    assert exc_info.value.code == "DRAFT_ALREADY_REVIEWED"


# ==============================================================================
# 15. Fallo de persistencia sin transición incorrecta del trabajo
# ==============================================================================


@pytest.mark.asyncio
async def test_persistence_failure_leaves_job_failed(
    generation_fixtures: tuple[
        InMemoryJobRepository,
        InMemoryStorageClient,
        InMemoryDraftRepository,
        DocumentExtractionService,
        DraftValidationService,
        QuestionGenerationService,
        GenerationOrchestrator,
    ],
) -> None:
    """Verify that if draft persistence fails, the job transitions to 'failed' and NOT 'review_required'."""
    job_repo, storage_client, draft_repo, _, _, _, orchestrator = generation_fixtures

    tenant_id = "550e8400-e29b-41d4-a716-446655440000"
    job_id = "job-fail-persistence-1"
    storage_path = f"{tenant_id}/materials/ciencias.pdf"

    pdf_bytes = build_valid_pdf(["Texto de prueba sobre bioelementos y carbohidratos."])
    storage_client.upload_file("teacher-materials", storage_path, pdf_bytes)

    job_repo.add_job(
        ContentGenerationJobRecord(
            id=job_id,
            tenant_id=tenant_id,
            created_by="teacher-1",
            storage_bucket="teacher-materials",
            storage_path=storage_path,
            original_filename="ciencias.pdf",
            mime_type="application/pdf",
            file_size_bytes=len(pdf_bytes),
            file_checksum="checksum-1",
            status="queued",
            provider="mock",
            model_id="mock-v1",
        )
    )

    # Force draft_repository.save_drafts to fail
    async def failing_save_drafts(
        *args: Any, **kwargs: Any
    ) -> list[QuestionDraftRecord]:
        raise DraftAlreadyReviewedError(
            "Fallo simulado de base de datos en inserción de drafts."
        )

    draft_repo.save_drafts = failing_save_drafts  # type: ignore[method-assign]

    with pytest.raises(DraftAlreadyReviewedError):
        await orchestrator.execute_job(job_id=job_id, tenant_id=tenant_id)

    # Verify job status is 'failed', NOT 'review_required'
    job = await job_repo.get_job(job_id, tenant_id)
    assert job is not None
    assert job.status == "failed"
    assert job.status != "review_required"


# ==============================================================================
# 16. Transición a review_required únicamente después de completar la persistencia
# ==============================================================================


@pytest.mark.asyncio
async def test_transition_to_review_required_after_persistence(
    generation_fixtures: tuple[
        InMemoryJobRepository,
        InMemoryStorageClient,
        InMemoryDraftRepository,
        DocumentExtractionService,
        DraftValidationService,
        QuestionGenerationService,
        GenerationOrchestrator,
    ],
) -> None:
    """Verify end-to-end happy path: extraction -> generation -> persistence -> review_required."""
    job_repo, storage_client, draft_repo, _, _, _, orchestrator = generation_fixtures

    tenant_id = "550e8400-e29b-41d4-a716-446655440000"
    job_id = "job-success-e2e-1"
    storage_path = f"{tenant_id}/materials/fotosintesis.pptx"

    pptx_bytes = build_valid_pptx(
        [
            "Diapositiva 1: La fase luminosa convierte luz solar en ATP en la membrana tilacoidal.",
            "Diapositiva 2: El ciclo de Calvin fija dioxido de carbono en el estroma con Rubisco.",
        ]
    )
    storage_client.upload_file("teacher-materials", storage_path, pptx_bytes)

    job_repo.add_job(
        ContentGenerationJobRecord(
            id=job_id,
            tenant_id=tenant_id,
            created_by="teacher-1",
            storage_bucket="teacher-materials",
            storage_path=storage_path,
            original_filename="fotosintesis.pptx",
            mime_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            file_size_bytes=len(pptx_bytes),
            file_checksum="checksum-pptx-1",
            status="queued",
            provider="mock",
            model_id="mock-v1",
        )
    )

    # Execute orchestrator
    records = await orchestrator.execute_job(
        job_id=job_id,
        tenant_id=tenant_id,
        target_num_questions=2,
    )

    # 1. Borradores persistidos correctamente
    assert len(records) == 2
    for r in records:
        assert r.status == "draft"
        assert r.generation_job_id == job_id
        assert r.tenant_id == tenant_id
        assert len(r.options) >= 2
        assert any(opt["is_correct"] for opt in r.options)

    stored_drafts = await draft_repo.get_drafts_by_job(job_id, tenant_id)
    assert len(stored_drafts) == 2

    # 2. Trabajo transicionó a review_required
    updated_job = await job_repo.get_job(job_id, tenant_id)
    assert updated_job is not None
    assert updated_job.status == "review_required"
    assert updated_job.completed_at is not None
    assert updated_job.error_code is None


# ==============================================================================
# 17. Validaciones adicionales de integridad y límites
# ==============================================================================


def test_empty_question_text_rejected() -> None:
    """Verify empty or whitespace-only question text is rejected."""
    with pytest.raises(EmptyQuestionTextError):
        GeneratedQuestionDraft(
            suggested_kc_name="Fotosíntesis",
            question_text="   \n   ",  # Blank
            options=[
                QuestionOptionDraft(text="A", is_correct=True),
                QuestionOptionDraft(text="B", is_correct=False),
            ],
            explanation="Explicación",
            source_references=[
                QuestionSourceReference(
                    type=DocumentUnitType.PAGE, index=1, snippet="texto"
                )
            ],
        )


def test_empty_explanation_rejected() -> None:
    """Verify empty or whitespace-only explanation is rejected."""
    with pytest.raises(EmptyExplanationError):
        GeneratedQuestionDraft(
            suggested_kc_name="Fotosíntesis",
            question_text="¿Pregunta válida?",
            options=[
                QuestionOptionDraft(text="A", is_correct=True),
                QuestionOptionDraft(text="B", is_correct=False),
            ],
            explanation="   ",  # Blank
            source_references=[
                QuestionSourceReference(
                    type=DocumentUnitType.PAGE, index=1, snippet="texto"
                )
            ],
        )


def test_empty_option_text_rejected() -> None:
    """Verify option with blank text is rejected."""
    with pytest.raises(EmptyOptionTextError):
        GeneratedQuestionDraft(
            suggested_kc_name="Fotosíntesis",
            question_text="¿Pregunta válida?",
            options=[
                QuestionOptionDraft(text="A", is_correct=True),
                QuestionOptionDraft(text="   ", is_correct=False),  # Blank distractor
            ],
            explanation="Explicación",
            source_references=[
                QuestionSourceReference(
                    type=DocumentUnitType.PAGE, index=1, snippet="texto"
                )
            ],
        )


def test_options_count_limits_rejected() -> None:
    """Verify option counts < 2 or > 5 are rejected."""
    # Only 1 option
    with pytest.raises(InvalidOptionsCountError):
        GeneratedQuestionDraft(
            suggested_kc_name="Fotosíntesis",
            question_text="¿Pregunta?",
            options=[QuestionOptionDraft(text="Solo una opción", is_correct=True)],
            explanation="Explicación",
            source_references=[
                QuestionSourceReference(
                    type=DocumentUnitType.PAGE, index=1, snippet="texto"
                )
            ],
        )

    # 6 options (exceeds max 5)
    with pytest.raises(InvalidOptionsCountError):
        GeneratedQuestionDraft(
            suggested_kc_name="Fotosíntesis",
            question_text="¿Pregunta?",
            options=[
                QuestionOptionDraft(text="Opción 1", is_correct=True),
                QuestionOptionDraft(text="Opción 2", is_correct=False),
                QuestionOptionDraft(text="Opción 3", is_correct=False),
                QuestionOptionDraft(text="Opción 4", is_correct=False),
                QuestionOptionDraft(text="Opción 5", is_correct=False),
                QuestionOptionDraft(text="Opción 6", is_correct=False),
            ],
            explanation="Explicación",
            source_references=[
                QuestionSourceReference(
                    type=DocumentUnitType.PAGE, index=1, snippet="texto"
                )
            ],
        )


def test_true_false_question_validation() -> None:
    """Verify true_false questions must have exactly 2 options."""
    # Valid true_false
    q = GeneratedQuestionDraft(
        suggested_kc_name="Fotosíntesis",
        question_text="¿La fase luminosa produce ATP?",
        question_type=QuestionType.TRUE_FALSE,
        options=[
            QuestionOptionDraft(text="Verdadero", is_correct=True),
            QuestionOptionDraft(text="Falso", is_correct=False),
        ],
        explanation="Produce ATP y NADPH.",
        source_references=[
            QuestionSourceReference(
                type=DocumentUnitType.PAGE, index=1, snippet="ATP y NADPH"
            )
        ],
    )
    assert q.question_type == QuestionType.TRUE_FALSE

    # Invalid true_false with 3 options
    with pytest.raises(InvalidOptionsCountError):
        GeneratedQuestionDraft(
            suggested_kc_name="Fotosíntesis",
            question_text="¿La fase luminosa produce ATP?",
            question_type=QuestionType.TRUE_FALSE,
            options=[
                QuestionOptionDraft(text="Verdadero", is_correct=True),
                QuestionOptionDraft(text="Falso", is_correct=False),
                QuestionOptionDraft(text="No determinado", is_correct=False),
            ],
            explanation="Explicación",
            source_references=[
                QuestionSourceReference(
                    type=DocumentUnitType.PAGE, index=1, snippet="ATP"
                )
            ],
        )


@pytest.mark.asyncio
async def test_concurrent_execution_guard(
    generation_fixtures: tuple[
        InMemoryJobRepository,
        InMemoryStorageClient,
        InMemoryDraftRepository,
        DocumentExtractionService,
        DraftValidationService,
        QuestionGenerationService,
        GenerationOrchestrator,
    ],
) -> None:
    """Verify that an active 'processing' job rejects concurrent re-execution."""
    job_repo, _, _, _, _, _, orchestrator = generation_fixtures

    tenant_id = "550e8400-e29b-41d4-a716-446655440000"
    job_id = "job-concurrent-1"

    job_repo.add_job(
        ContentGenerationJobRecord(
            id=job_id,
            tenant_id=tenant_id,
            created_by="teacher-1",
            storage_bucket="teacher-materials",
            storage_path=f"{tenant_id}/mat.pdf",
            original_filename="mat.pdf",
            mime_type="application/pdf",
            file_size_bytes=100,
            file_checksum="chk",
            status="processing",  # Already processing!
            provider="mock",
            model_id="mock-v1",
        )
    )

    with pytest.raises(InvalidJobStateTransitionError) as exc_info:
        await orchestrator.execute_job(job_id=job_id, tenant_id=tenant_id)

    assert "procesamiento activo" in exc_info.value.message_safe


@pytest.mark.asyncio
async def test_terminal_state_job_guard(
    generation_fixtures: tuple[
        InMemoryJobRepository,
        InMemoryStorageClient,
        InMemoryDraftRepository,
        DocumentExtractionService,
        DraftValidationService,
        QuestionGenerationService,
        GenerationOrchestrator,
    ],
) -> None:
    """Verify that jobs in terminal states (approved, rejected) cannot be re-executed."""
    job_repo, _, _, _, _, _, orchestrator = generation_fixtures

    tenant_id = "550e8400-e29b-41d4-a716-446655440000"
    job_id = "job-terminal-approved"

    job_record = ContentGenerationJobRecord(
        id=job_id,
        tenant_id=tenant_id,
        created_by="teacher-1",
        storage_bucket="teacher-materials",
        storage_path=f"{tenant_id}/mat.pdf",
        original_filename="mat.pdf",
        mime_type="application/pdf",
        file_size_bytes=100,
        file_checksum="chk",
        status="queued",
        provider="mock",
        model_id="mock-v1",
    )
    job_repo.add_job(job_record)
    # Manually transition to approved (terminal)
    job_record.status = "approved"

    with pytest.raises(InvalidJobStateTransitionError) as exc_info:
        await orchestrator.execute_job(job_id=job_id, tenant_id=tenant_id)

    assert "estado terminal" in exc_info.value.message_safe


# ==============================================================================
# 18. Cobertura exhaustiva de modos de comportamiento del proveedor simulado
# ==============================================================================


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("behavior_mode", "expected_exception"),
    [
        (MockBehaviorMode.NO_CORRECT_OPTION, InvalidCorrectOptionsCountError),
        (MockBehaviorMode.MULTIPLE_CORRECT_OPTIONS, InvalidCorrectOptionsCountError),
        (MockBehaviorMode.DUPLICATE_OPTIONS, DuplicateOptionsError),
        (MockBehaviorMode.EMPTY_QUESTION_TEXT, EmptyQuestionTextError),
        (MockBehaviorMode.EMPTY_OPTION_TEXT, EmptyOptionTextError),
        (MockBehaviorMode.EMPTY_EXPLANATION, EmptyExplanationError),
        (MockBehaviorMode.INVALID_PAGE_INDEX, InvalidSourceReferenceError),
        (MockBehaviorMode.FABRICATED_SNIPPET, SnippetNotFoundError),
        (MockBehaviorMode.EXTRA_FORBIDDEN_FIELDS, UnauthorizedFieldsError),
        (MockBehaviorMode.PROVIDER_ERROR, GenerationProviderError),
    ],
)
async def test_mock_behavior_modes_comprehensive(
    sample_extracted_document: ExtractedDocument,
    behavior_mode: MockBehaviorMode,
    expected_exception: type[Exception],
) -> None:
    """Verify that every single adversarial mode in MockQuestionGenerationProvider triggers the expected domain exception."""
    provider = MockQuestionGenerationProvider(behavior_mode=behavior_mode)
    validation_service = DraftValidationService()
    generation_service = QuestionGenerationService(
        provider=provider,
        validation_service=validation_service,
    )
    context = GenerationContext(
        job_id="test-job-mode",
        tenant_id="test-tenant-mode",
    )

    with pytest.raises(expected_exception):
        await generation_service.generate_and_validate(
            document=sample_extracted_document,
            context=context,
        )


# ==============================================================================
# 19. Reintento de trabajo fallido transiciona correctamente a través del repositorio
# ==============================================================================


@pytest.mark.asyncio
async def test_failed_job_retry_transitions_processing_via_repository(
    generation_fixtures: tuple[
        InMemoryJobRepository,
        InMemoryStorageClient,
        InMemoryDraftRepository,
        DocumentExtractionService,
        DraftValidationService,
        QuestionGenerationService,
        GenerationOrchestrator,
    ],
) -> None:
    """Verify that retrying a job currently in 'failed' status properly calls repository.mark_processing and succeeds."""
    job_repo, storage_client, draft_repo, _, _, _, orchestrator = generation_fixtures

    tenant_id = "550e8400-e29b-41d4-a716-446655440000"
    job_id = "job-retry-from-failed-1"
    storage_path = f"{tenant_id}/materials/ciencias.pdf"

    pdf_bytes = build_valid_pdf(["Texto de ciencias para reintento de trabajo."])
    storage_client.upload_file("teacher-materials", storage_path, pdf_bytes)

    job_record = ContentGenerationJobRecord(
        id=job_id,
        tenant_id=tenant_id,
        created_by="teacher-1",
        storage_bucket="teacher-materials",
        storage_path=storage_path,
        original_filename="ciencias.pdf",
        mime_type="application/pdf",
        file_size_bytes=len(pdf_bytes),
        file_checksum="chk",
        status="failed",  # Job previously failed!
        error_code="PREVIOUS_ERROR",
        error_message_safe="Error previo",
        provider="mock",
        model_id="mock-v1",
    )
    job_repo.add_job(job_record)

    # Re-executing orchestrator should transition failed -> processing -> review_required
    records = await orchestrator.execute_job(job_id=job_id, tenant_id=tenant_id)
    assert len(records) >= 1

    updated_job = await job_repo.get_job(job_id, tenant_id)
    assert updated_job is not None
    assert updated_job.status == "review_required"
    assert updated_job.started_at is not None
    assert updated_job.completed_at is not None

    stored_drafts = await draft_repo.get_drafts_by_job(job_id, tenant_id)
    assert len(stored_drafts) == len(records)


# ==============================================================================
# 20. Seguridad: Detección y rechazo de HTML no procesado (XSS defense)
# ==============================================================================


def test_unprocessed_html_rejected() -> None:
    """Verify that raw, unprocessed HTML in question_text, explanation, or options is strictly rejected."""
    # HTML in question text
    with pytest.raises(UnprocessedHtmlError):
        GeneratedQuestionDraft(
            suggested_kc_name="Fotosíntesis",
            question_text="¿Dónde ocurre la fase luminosa? <script>alert('xss')</script>",
            options=[
                QuestionOptionDraft(text="En los tilacoides", is_correct=True),
                QuestionOptionDraft(text="En el estroma", is_correct=False),
            ],
            explanation="Explicación normal.",
            source_references=[
                QuestionSourceReference(type=DocumentUnitType.PAGE, index=1, snippet="texto")
            ],
        )

    # HTML in option text
    with pytest.raises(UnprocessedHtmlError):
        GeneratedQuestionDraft(
            suggested_kc_name="Fotosíntesis",
            question_text="¿Pregunta válida sin html?",
            options=[
                QuestionOptionDraft(text="Opción <img src=x onerror=alert(1)>", is_correct=True),
                QuestionOptionDraft(text="Opción normal", is_correct=False),
            ],
            explanation="Explicación normal.",
            source_references=[
                QuestionSourceReference(type=DocumentUnitType.PAGE, index=1, snippet="texto")
            ],
        )

    # HTML in explanation
    with pytest.raises(UnprocessedHtmlError):
        GeneratedQuestionDraft(
            suggested_kc_name="Fotosíntesis",
            question_text="¿Pregunta válida sin html?",
            options=[
                QuestionOptionDraft(text="Opción A", is_correct=True),
                QuestionOptionDraft(text="Opción B", is_correct=False),
            ],
            explanation="Explicación con <iframe src='http://evil.com'></iframe> malicioso.",
            source_references=[
                QuestionSourceReference(type=DocumentUnitType.PAGE, index=1, snippet="texto")
            ],
        )


# ==============================================================================
# 21. Reglas pedagógicas de opción múltiple y distractores
# ==============================================================================


def test_multiple_choice_requires_at_least_one_distractor() -> None:
    """Verify multiple_choice rejects cases where all options are correct (zero distractors)."""
    with pytest.raises(InvalidCorrectOptionsCountError) as exc_info:
        GeneratedQuestionDraft(
            suggested_kc_name="Fotosíntesis",
            question_text="¿Cuáles son productos de la fase luminosa?",
            question_type=QuestionType.MULTIPLE_CHOICE,
            options=[
                QuestionOptionDraft(text="ATP", is_correct=True),
                QuestionOptionDraft(text="NADPH", is_correct=True),
                QuestionOptionDraft(text="Oxígeno molecular", is_correct=True),
            ],
            explanation="Todos los anteriores son productos.",
            source_references=[
                QuestionSourceReference(type=DocumentUnitType.PAGE, index=1, snippet="texto")
            ],
        )

    assert "distractor" in exc_info.value.message_safe


def test_misconception_explanation_prohibited_on_correct_option() -> None:
    """Verify that setting misconception_explanation on a correct option is rejected."""
    with pytest.raises(ValidationError):
        QuestionOptionDraft(
            text="Respuesta correcta",
            is_correct=True,
            misconception_explanation="No puede haber error conceptual en la respuesta correcta.",
        )


# ==============================================================================
# 22. Normalización de Unicode NFKC y caracteres no imprimibles
# ==============================================================================


def test_unicode_nfkc_duplicate_options_detected() -> None:
    """Verify that composed and decomposed Unicode representations are detected as duplicates."""
    with pytest.raises(DuplicateOptionsError):
        GeneratedQuestionDraft(
            suggested_kc_name="Fotosíntesis",
            question_text="¿Dónde ocurre?",
            options=[
                QuestionOptionDraft(text="Opción con tilde", is_correct=True),  # Composed ó
                QuestionOptionDraft(text="Opcio\u0301n con tilde", is_correct=False),  # Decomposed o + combining acute
            ],
            explanation="Explicación.",
            source_references=[
                QuestionSourceReference(type=DocumentUnitType.PAGE, index=1, snippet="texto")
            ],
        )


def test_snippet_normalization_soft_hyphens(sample_extracted_document: ExtractedDocument) -> None:
    """Verify that soft hyphens (\\xad) and zero-width spaces in document text do not break snippet matching."""
    validation_service = DraftValidationService()

    # Modify unit text to contain soft hyphen in 'tilacoides' -> 'tila\xadcoides'
    doc = ExtractedDocument(
        document_id="doc-hyphen",
        document_type=DocumentType.PDF,
        original_filename="doc.pdf",
        total_units=1,
        units=[
            ExtractedUnit(
                type=DocumentUnitType.PAGE,
                index=1,
                text="La fase luminosa ocurre en las membranas de los tila\xadcoides celulares.",
            )
        ],
    )

    draft = GeneratedQuestionDraft(
        suggested_kc_name="Fotosíntesis",
        question_text="¿Dónde ocurre la fase luminosa?",
        options=[
            QuestionOptionDraft(text="En los tilacoides", is_correct=True),
            QuestionOptionDraft(text="En el estroma", is_correct=False),
        ],
        explanation="Explicación.",
        source_references=[
            QuestionSourceReference(
                type=DocumentUnitType.PAGE,
                index=1,
                snippet="membranas de los tilacoides celulares",  # No soft hyphen in snippet
            )
        ],
    )

    validated = validation_service.validate_drafts([draft], doc)
    assert len(validated) == 1


# ==============================================================================
# 23. Persistencia de lista vacía de borradores rechazada
# ==============================================================================


@pytest.mark.asyncio
async def test_empty_drafts_persistence_rejected() -> None:
    """Verify that InMemoryDraftRepository.save_drafts rejects an empty drafts list."""
    draft_repo = InMemoryDraftRepository()
    with pytest.raises(EmptyDraftsError):
        await draft_repo.save_drafts(job_id="job-1", tenant_id="tenant-1", drafts=[])


# ==============================================================================
# 24. Validación de dificultad fuera de rango [0.0, 1.0]
# ==============================================================================


def test_invalid_difficulty_range_raises_domain_error() -> None:
    """Verify that difficulty outside [0.0, 1.0] raises InvalidDifficultyError."""
    with pytest.raises(InvalidDifficultyError) as exc_info:
        GeneratedQuestionDraft(
            suggested_kc_name="Fotosíntesis",
            question_text="¿Pregunta con dificultad fuera de rango?",
            difficulty=1.5,
            options=[
                QuestionOptionDraft(text="Opción A", is_correct=True),
                QuestionOptionDraft(text="Opción B", is_correct=False),
            ],
            explanation="Explicación.",
            source_references=[
                QuestionSourceReference(type=DocumentUnitType.PAGE, index=1, snippet="texto")
            ],
        )

    assert exc_info.value.code == "INVALID_DIFFICULTY"


# ==============================================================================
# 25. DraftValidationService valida borradores no validados directamente
# ==============================================================================


def test_draft_validation_service_validates_unvalidated_drafts(
    sample_extracted_document: ExtractedDocument,
) -> None:
    """Verify that DraftValidationService.validate_draft strictly verifies structural rules even on unvalidated draft objects."""
    validation_service = DraftValidationService()
    unit_map = {u.index: u for u in sample_extracted_document.units}

    unvalidated_draft = GeneratedQuestionDraft.model_construct(
        suggested_kc_name="Fotosíntesis",
        question_text="",  # Empty!
        question_type=QuestionType.SINGLE_CHOICE,
        difficulty=0.5,
        options=[
            QuestionOptionDraft.model_construct(text="Opción A", is_correct=True),
            QuestionOptionDraft.model_construct(text="Opción B", is_correct=False),
        ],
        explanation="Explicación.",
        source_references=[
            QuestionSourceReference(
                type=DocumentUnitType.PAGE, index=1, snippet="membranas de los tilacoides"
            )
        ],
    )

    with pytest.raises(EmptyQuestionTextError):
        validation_service.validate_draft(unvalidated_draft, sample_extracted_document, unit_map)
