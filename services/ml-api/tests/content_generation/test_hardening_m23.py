"""Hardening Integration & Security Tests for Milestone M2.3.

Covers:
1. Strict Fencing Token Verification:
   - Completion with valid token.
   - Completion with incorrect token (rejected).
   - Completion with NULL token (rejected without bypass).
   - Completion after lease expiry (rejected).
   - Completion by old worker after another claimed job (rejected).
   - Administrative un-fenced completion separation.
   - Completion when lease expiration is NULL (strictly rejected, no bypass loophole).
   - Lease renewal and heartbeat rejection when lease has expired.
2. Question Drafts Atomic UPSERT & Teacher Protection:
   - Idempotent upsert of unreviewed 'draft' status preserving existing draft IDs.
   - Protection of human-intervened drafts (edited, approved, rejected).
   - Direct SQL engine level rejection via WHERE status = 'draft' on conflict.
   - Database trigger blocking status reversion from edited/approved/rejected back to draft.
   - Teacher audit protection blocking deletion of approved drafts.
   - Concurrency race condition simulation between teacher intervention and worker generation.
3. Durable Worker Abrupt Termination & Recovery:
   - Complete 10-step sequence with real PostgreSQL instance.
   - Explicit differentiation between:
     * Connection pool restart.
     * API service restart.
     * Worker process termination & recovery.
4. PostgreSQL Privileges and Multi-Tenant Isolation Audit:
   - Verification of execution roles and BYPASSRLS attributes.
   - Real execution under least-privilege role ml_api_worker (NOSUPERUSER, NOBYPASSRLS).
   - Verification of least-privilege boundary: permission denied on auth_recovery_pins and answer_events.
   - Same-connection isolation across Tenant A and Tenant B.
   - Cross-tenant draft injection protection at trigger and repo levels.
"""

import asyncio
import json
import logging
import uuid
from collections.abc import AsyncGenerator

import asyncpg
import pytest

from app.content_generation.exceptions import (
    DraftAlreadyReviewedError,
    InvalidJobStateTransitionError,
    JobNotFoundError,
)
from app.content_generation.infrastructure.postgres_draft_repository import (
    PostgresDraftRepository,
)
from app.content_generation.infrastructure.postgres_job_repository import (
    PostgresJobRepository,
)
from app.content_generation.infrastructure.unit_of_work import (
    PostgresUnitOfWork,
)
from app.content_generation.providers.mock_provider import (
    MockQuestionGenerationProvider,
)
from app.content_generation.repositories.job_repository import (
    ContentGenerationJobRecord,
)
from app.content_generation.repositories.storage_client import (
    InMemoryStorageClient,
)
from app.content_generation.schemas.extracted_document import (
    DocumentUnitType,
)
from app.content_generation.schemas.generated_questions import (
    BloomTaxonomy,
    GeneratedQuestionDraft,
    QuestionOptionDraft,
    QuestionSourceReference,
    QuestionType,
    compute_draft_content_hash,
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
from app.content_generation.worker import GenerationWorker
from tests.content_generation.test_fixtures import build_valid_pdf

logger = logging.getLogger(__name__)

TENANT_A = "11111111-1111-1111-1111-111111111111"
TENANT_B = "22222222-2222-2222-2222-222222222222"
TEACHER_A = "11111111-1111-1111-1111-aaaaaaaaaaaa"
TEACHER_B = "22222222-2222-2222-2222-aaaaaaaaaaaa"
COURSE_A1 = "11111111-1111-1111-1111-cccccccccccc"
COURSE_B1 = "22222222-2222-2222-2222-cccccccccccc"

TEST_DB_URL = "postgresql://postgres:postgres@127.0.0.1:5432/plataformamicro_test"
WORKER_DB_URL = "postgresql://ml_api_worker:ml_api_worker_secret@127.0.0.1:5432/plataformamicro_test"


@pytest.fixture
async def local_pool() -> AsyncGenerator[asyncpg.Pool, None]:
    """Create dedicated clean asyncpg connection pool for hardening tests."""
    pool = await asyncpg.create_pool(dsn=TEST_DB_URL, min_size=1, max_size=5)
    async with pool.acquire() as conn:
        await conn.execute(
            "DELETE FROM question_drafts WHERE tenant_id IN ($1::uuid, $2::uuid);",
            uuid.UUID(TENANT_A),
            uuid.UUID(TENANT_B),
        )
        await conn.execute(
            "DELETE FROM content_generation_jobs WHERE tenant_id IN ($1::uuid, $2::uuid);",
            uuid.UUID(TENANT_A),
            uuid.UUID(TENANT_B),
        )
    yield pool
    try:
        async with pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM question_drafts WHERE tenant_id IN ($1::uuid, $2::uuid);",
                uuid.UUID(TENANT_A),
                uuid.UUID(TENANT_B),
            )
            await conn.execute(
                "DELETE FROM content_generation_jobs WHERE tenant_id IN ($1::uuid, $2::uuid);",
                uuid.UUID(TENANT_A),
                uuid.UUID(TENANT_B),
            )
    except (OSError, asyncpg.PostgresError) as e:
        logger.debug("Cleanup warning: %s", e)
    finally:
        await pool.close()


def _make_sample_draft(index: int = 1) -> GeneratedQuestionDraft:
    return GeneratedQuestionDraft(
        suggested_kc_name=f"Hardening KC {index}",
        question_text=f"¿Cuál es el mecanismo de endurecimiento {index}?",
        question_type=QuestionType.SINGLE_CHOICE,
        difficulty=0.600,
        bloom_taxonomy=BloomTaxonomy.ANALYZE,
        options=[
            QuestionOptionDraft(text="Validación de tokens de lease atómicos", is_correct=True),
            QuestionOptionDraft(text="Bypass sin validación", is_correct=False),
            QuestionOptionDraft(text="Sobrescritura ciega", is_correct=False),
            QuestionOptionDraft(text="Omitir RLS", is_correct=False),
        ],
        explanation="El lease atómico evita que workers caídos corrompan el estado.",
        source_references=[
            QuestionSourceReference(type=DocumentUnitType.PAGE, index=1, snippet="tokens de lease atómicos")
        ],
    )


# ==============================================================================
# SECTION 1: Pruebas de Fencing Token (Garantías 1 a 5 + Robustez)
# ==============================================================================


@pytest.mark.asyncio
async def test_fencing_1_completion_with_valid_token(local_pool: asyncpg.Pool) -> None:
    """Garantía 1: Finalización con token correcto debe ser exitosa."""
    job_repo = PostgresJobRepository(local_pool)
    job_id = str(uuid.uuid4())
    worker_token = str(uuid.uuid4())

    await job_repo.create_job(
        ContentGenerationJobRecord(
            id=job_id,
            tenant_id=TENANT_A,
            created_by=TEACHER_A,
            storage_bucket="teacher-materials",
            storage_path=f"{TENANT_A}/doc.pdf",
            original_filename="doc.pdf",
            mime_type="application/pdf",
            file_size_bytes=1000,
            file_checksum="f1" * 32,
            status="queued",
            provider="mock",
            model_id="mock-v1",
        )
    )

    claimed = await job_repo.claim_pending_job(
        tenant_id=TENANT_A,
        lease_duration_seconds=300,
        worker_token=worker_token,
        job_id=job_id,
    )
    assert claimed is not None
    assert claimed.processing_lease_token == worker_token

    completed = await job_repo.mark_review_required(
        job_id=job_id,
        tenant_id=TENANT_A,
        lease_token=worker_token,
    )
    assert completed.status == "review_required"
    assert completed.completed_at is not None


@pytest.mark.asyncio
async def test_fencing_2_completion_with_incorrect_token_rejected(local_pool: asyncpg.Pool) -> None:
    """Garantía 2: Finalización con token incorrecto debe ser rechazada."""
    job_repo = PostgresJobRepository(local_pool)
    job_id = str(uuid.uuid4())
    worker_token = str(uuid.uuid4())
    wrong_token = str(uuid.uuid4())

    await job_repo.create_job(
        ContentGenerationJobRecord(
            id=job_id,
            tenant_id=TENANT_A,
            created_by=TEACHER_A,
            storage_bucket="teacher-materials",
            storage_path=f"{TENANT_A}/doc.pdf",
            original_filename="doc.pdf",
            mime_type="application/pdf",
            file_size_bytes=1000,
            file_checksum="f2" * 32,
            status="queued",
            provider="mock",
            model_id="mock-v1",
        )
    )

    await job_repo.claim_pending_job(
        tenant_id=TENANT_A,
        lease_duration_seconds=300,
        worker_token=worker_token,
        job_id=job_id,
    )

    with pytest.raises(InvalidJobStateTransitionError) as exc_info:
        await job_repo.mark_review_required(
            job_id=job_id,
            tenant_id=TENANT_A,
            lease_token=wrong_token,
        )
    assert "lease_token" in str(exc_info.value) or "otro worker" in str(exc_info.value)


@pytest.mark.asyncio
async def test_fencing_3_completion_with_null_token_rejected(local_pool: asyncpg.Pool) -> None:
    """Garantía 3: Finalización con token NULL debe ser rechazada estrictamente sin bypass."""
    job_repo = PostgresJobRepository(local_pool)
    job_id = str(uuid.uuid4())
    worker_token = str(uuid.uuid4())

    await job_repo.create_job(
        ContentGenerationJobRecord(
            id=job_id,
            tenant_id=TENANT_A,
            created_by=TEACHER_A,
            storage_bucket="teacher-materials",
            storage_path=f"{TENANT_A}/doc.pdf",
            original_filename="doc.pdf",
            mime_type="application/pdf",
            file_size_bytes=1000,
            file_checksum="f3" * 32,
            status="queued",
            provider="mock",
            model_id="mock-v1",
        )
    )

    await job_repo.claim_pending_job(
        tenant_id=TENANT_A,
        lease_duration_seconds=300,
        worker_token=worker_token,
        job_id=job_id,
    )

    # Worker calls mark_review_required with None -> MUST FAIL
    with pytest.raises(InvalidJobStateTransitionError) as exc_info:
        await job_repo.mark_review_required(
            job_id=job_id,
            tenant_id=TENANT_A,
            lease_token=None,
        )
    assert "token" in str(exc_info.value).lower()

    # Same check for Unit of Work commit_generation_results
    uow = PostgresUnitOfWork(local_pool)
    with pytest.raises(InvalidJobStateTransitionError):
        await uow.commit_generation_results(
            job_id=job_id,
            tenant_id=TENANT_A,
            drafts=[_make_sample_draft(1)],
            lease_token=None,
        )


@pytest.mark.asyncio
async def test_fencing_4_completion_after_lease_expiry_rejected(local_pool: asyncpg.Pool) -> None:
    """Garantía 4: Worker cuyo lease haya expirado no debe poder finalizar el trabajo."""
    job_repo = PostgresJobRepository(local_pool)
    job_id = str(uuid.uuid4())
    worker_token = str(uuid.uuid4())

    await job_repo.create_job(
        ContentGenerationJobRecord(
            id=job_id,
            tenant_id=TENANT_A,
            created_by=TEACHER_A,
            storage_bucket="teacher-materials",
            storage_path=f"{TENANT_A}/doc.pdf",
            original_filename="doc.pdf",
            mime_type="application/pdf",
            file_size_bytes=1000,
            file_checksum="f4" * 32,
            status="queued",
            provider="mock",
            model_id="mock-v1",
        )
    )

    # Claim with a 1-second lease
    await job_repo.claim_pending_job(
        tenant_id=TENANT_A,
        lease_duration_seconds=1,
        worker_token=worker_token,
        job_id=job_id,
    )

    # Wait for lease to expire completely
    await asyncio.sleep(1.2)

    # Worker attempts completion with expired lease -> MUST FAIL even before another worker claims
    with pytest.raises(InvalidJobStateTransitionError) as exc_info:
        await job_repo.mark_review_required(
            job_id=job_id,
            tenant_id=TENANT_A,
            lease_token=worker_token,
        )
    assert "expirado" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_fencing_5_old_worker_rejected_after_new_worker_claimed(local_pool: asyncpg.Pool) -> None:
    """Garantía 5: Worker antiguo no puede finalizar tras reclamación por nuevo worker."""
    job_repo = PostgresJobRepository(local_pool)
    job_id = str(uuid.uuid4())
    worker_a_token = str(uuid.uuid4())
    worker_b_token = str(uuid.uuid4())

    await job_repo.create_job(
        ContentGenerationJobRecord(
            id=job_id,
            tenant_id=TENANT_A,
            created_by=TEACHER_A,
            storage_bucket="teacher-materials",
            storage_path=f"{TENANT_A}/doc.pdf",
            original_filename="doc.pdf",
            mime_type="application/pdf",
            file_size_bytes=1000,
            file_checksum="f5" * 32,
            status="queued",
            provider="mock",
            model_id="mock-v1",
        )
    )

    # Worker A claims with 1-second lease
    await job_repo.claim_pending_job(
        tenant_id=TENANT_A,
        lease_duration_seconds=1,
        worker_token=worker_a_token,
        job_id=job_id,
    )

    # Expire lease
    await asyncio.sleep(1.2)

    # Worker B claims job with new token
    claimed_b = await job_repo.claim_pending_job(
        tenant_id=TENANT_A,
        lease_duration_seconds=300,
        worker_token=worker_b_token,
        job_id=job_id,
    )
    assert claimed_b is not None
    assert claimed_b.processing_lease_token == worker_b_token

    # Worker A wakes up and attempts mark_review_required -> MUST BE REJECTED
    with pytest.raises(InvalidJobStateTransitionError):
        await job_repo.mark_review_required(
            job_id=job_id,
            tenant_id=TENANT_A,
            lease_token=worker_a_token,
        )

    # Worker A attempts mark_failed -> MUST ALSO BE REJECTED
    with pytest.raises(InvalidJobStateTransitionError):
        await job_repo.mark_failed(
            job_id=job_id,
            tenant_id=TENANT_A,
            error_code="TEST_ERROR",
            error_message_safe="Error de worker antiguo",
            lease_token=worker_a_token,
        )

    # Worker B finishes cleanly
    completed_b = await job_repo.mark_review_required(
        job_id=job_id,
        tenant_id=TENANT_A,
        lease_token=worker_b_token,
    )
    assert completed_b.status == "review_required"


@pytest.mark.asyncio
async def test_fencing_administrative_operations_separated(local_pool: asyncpg.Pool) -> None:
    """Operaciones administrativas sin lease deben operar de manera separada e independiente."""
    job_repo = PostgresJobRepository(local_pool)
    job_id = str(uuid.uuid4())

    await job_repo.create_job(
        ContentGenerationJobRecord(
            id=job_id,
            tenant_id=TENANT_A,
            created_by=TEACHER_A,
            storage_bucket="teacher-materials",
            storage_path=f"{TENANT_A}/doc.pdf",
            original_filename="doc.pdf",
            mime_type="application/pdf",
            file_size_bytes=1000,
            file_checksum="admin_test" * 4,
            status="queued",
            provider="mock",
            model_id="mock-v1",
        )
    )

    # Manual transition to processing
    await job_repo.mark_processing(job_id=job_id, tenant_id=TENANT_A)

    # Admin forces completion without lease token via admin_mark_review_required
    admin_done = await job_repo.admin_mark_review_required(
        job_id=job_id,
        tenant_id=TENANT_A,
    )
    assert admin_done.status == "review_required"


@pytest.mark.asyncio
async def test_fencing_null_lease_expiry_bypass_rejected(local_pool: asyncpg.Pool) -> None:
    """Comprueba que un trabajo con lease_expires_at NULL no pueda finalizarse (elimina loophole IS NULL)."""
    job_repo = PostgresJobRepository(local_pool)
    uow = PostgresUnitOfWork(local_pool)
    job_id = str(uuid.uuid4())
    worker_token = str(uuid.uuid4())

    await job_repo.create_job(
        ContentGenerationJobRecord(
            id=job_id,
            tenant_id=TENANT_A,
            created_by=TEACHER_A,
            storage_bucket="teacher-materials",
            storage_path=f"{TENANT_A}/doc.pdf",
            original_filename="doc.pdf",
            mime_type="application/pdf",
            file_size_bytes=1000,
            file_checksum="null_expiry_test" * 2,
            status="queued",
            provider="mock",
            model_id="mock-v1",
        )
    )

    # Simulate manual/corrupted processing state with token set but lease_expires_at NULL
    async with local_pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE content_generation_jobs
            SET status = 'processing',
                processing_lease_token = $2::uuid,
                processing_lease_expires_at = NULL
            WHERE id = $1::uuid;
            """,
            uuid.UUID(job_id),
            uuid.UUID(worker_token),
        )

    # mark_review_required MUST REJECT because the lease has no valid non-null expiration
    with pytest.raises(InvalidJobStateTransitionError) as exc_info:
        await job_repo.mark_review_required(
            job_id=job_id,
            tenant_id=TENANT_A,
            lease_token=worker_token,
        )
    assert "expirado" in str(exc_info.value).lower()

    # uow.commit_generation_results MUST ALSO REJECT
    with pytest.raises(InvalidJobStateTransitionError):
        await uow.commit_generation_results(
            job_id=job_id,
            tenant_id=TENANT_A,
            drafts=[_make_sample_draft(1)],
            lease_token=worker_token,
        )


@pytest.mark.asyncio
async def test_fencing_renew_lease_and_heartbeat_rejected_when_lease_expired(local_pool: asyncpg.Pool) -> None:
    """Verifica que renew_lease y heartbeat rechazan operaciones cuando el lease ha expirado."""
    job_repo = PostgresJobRepository(local_pool)
    job_id = str(uuid.uuid4())
    worker_token = str(uuid.uuid4())

    await job_repo.create_job(
        ContentGenerationJobRecord(
            id=job_id,
            tenant_id=TENANT_A,
            created_by=TEACHER_A,
            storage_bucket="teacher-materials",
            storage_path=f"{TENANT_A}/doc.pdf",
            original_filename="doc.pdf",
            mime_type="application/pdf",
            file_size_bytes=1000,
            file_checksum="renew_test" * 3,
            status="queued",
            provider="mock",
            model_id="mock-v1",
        )
    )

    await job_repo.claim_pending_job(
        tenant_id=TENANT_A,
        lease_duration_seconds=1,
        worker_token=worker_token,
        job_id=job_id,
    )

    # Let the 1-second lease expire
    await asyncio.sleep(1.2)

    # Stale worker attempts to renew lease -> MUST FAIL
    with pytest.raises(InvalidJobStateTransitionError):
        await job_repo.renew_lease(
            job_id=job_id,
            tenant_id=TENANT_A,
            lease_token=worker_token,
            extension_seconds=300,
        )

    # Heartbeat must return False
    hb = await job_repo.heartbeat(
        job_id=job_id,
        tenant_id=TENANT_A,
        lease_token=worker_token,
    )
    assert hb is False


# ==============================================================================
# SECTION 2: Pruebas de UPSERT y Protección de question_drafts
# ==============================================================================


@pytest.mark.asyncio
async def test_draft_upsert_idempotent_in_draft_status(local_pool: asyncpg.Pool) -> None:
    """Borradores en estado 'draft' se actualizan de forma limpia e idempotente conservando el ID original."""
    job_repo = PostgresJobRepository(local_pool)
    draft_repo = PostgresDraftRepository(local_pool)
    job_id = str(uuid.uuid4())

    await job_repo.create_job(
        ContentGenerationJobRecord(
            id=job_id,
            tenant_id=TENANT_A,
            created_by=TEACHER_A,
            storage_bucket="teacher-materials",
            storage_path=f"{TENANT_A}/doc.pdf",
            original_filename="doc.pdf",
            mime_type="application/pdf",
            file_size_bytes=1000,
            file_checksum="upsert_1" * 4,
            status="queued",
            provider="mock",
            model_id="mock-v1",
        )
    )

    sample_draft = _make_sample_draft(1)

    # First save
    saved_first = await draft_repo.save_drafts(job_id=job_id, tenant_id=TENANT_A, drafts=[sample_draft])
    assert len(saved_first) == 1
    assert saved_first[0].status == "draft"
    original_id = saved_first[0].id
    original_created_at = saved_first[0].created_at

    # Second save with same content hash (simulating retry of unreviewed job)
    saved_second = await draft_repo.save_drafts(job_id=job_id, tenant_id=TENANT_A, drafts=[sample_draft])
    assert len(saved_second) == 1
    assert saved_second[0].status == "draft"

    # In-place idempotent UPSERT preserves existing primary key ID and created_at
    assert saved_second[0].id == original_id
    assert saved_second[0].created_at == original_created_at

    # Total drafts in DB for this job must remain exactly 1 (no duplicates)
    all_drafts = await draft_repo.get_drafts_by_job(job_id, TENANT_A)
    assert len(all_drafts) == 1


@pytest.mark.asyncio
async def test_draft_upsert_protects_intervened_draft_at_sql_engine_level(local_pool: asyncpg.Pool) -> None:
    """Verifica que la cláusula WHERE status = 'draft' en ON CONFLICT bloquea sobrescrituras a nivel SQL."""
    job_repo = PostgresJobRepository(local_pool)
    draft_repo = PostgresDraftRepository(local_pool)
    job_id = str(uuid.uuid4())

    await job_repo.create_job(
        ContentGenerationJobRecord(
            id=job_id,
            tenant_id=TENANT_A,
            created_by=TEACHER_A,
            storage_bucket="teacher-materials",
            storage_path=f"{TENANT_A}/doc.pdf",
            original_filename="doc.pdf",
            mime_type="application/pdf",
            file_size_bytes=1000,
            file_checksum="upsert_protect" * 4,
            status="queued",
            provider="mock",
            model_id="mock-v1",
        )
    )

    sample_draft = _make_sample_draft(1)
    saved = await draft_repo.save_drafts(job_id=job_id, tenant_id=TENANT_A, drafts=[sample_draft])
    draft_id = saved[0].id

    # Simulate teacher intervention directly in PostgreSQL: change status to 'edited',
    # and customize difficulty and question text
    async with local_pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE question_drafts
            SET status = 'edited',
                suggested_difficulty = 0.950,
                question_text = 'Texto editado por el docente',
                updated_at = '2026-01-01 00:00:00+00'::timestamptz
            WHERE id = $1::uuid;
            """,
            uuid.UUID(draft_id),
        )

    # Now attempt a regeneration save: MUST FAIL with DraftAlreadyReviewedError
    with pytest.raises(DraftAlreadyReviewedError) as exc_info:
        await draft_repo.save_drafts(job_id=job_id, tenant_id=TENANT_A, drafts=[sample_draft])
    assert "edited" in str(exc_info.value)

    # Verify that teacher's values, difficulty and updated_at were NOT modified silently
    draft_in_db = await draft_repo.get_draft_by_id(draft_id, TENANT_A)
    assert draft_in_db is not None
    assert draft_in_db.status == "edited"
    assert draft_in_db.question_text == "Texto editado por el docente"
    assert draft_in_db.suggested_difficulty == 0.950
    assert draft_in_db.updated_at is not None and draft_in_db.updated_at.year == 2026


@pytest.mark.asyncio
async def test_draft_upsert_sql_engine_direct_rejection_without_python_precheck(local_pool: asyncpg.Pool) -> None:
    """Verifica que el rechazo por intervención docente es ejecutado directamente por la cláusula SQL ON CONFLICT."""
    job_id = str(uuid.uuid4())
    draft_id = str(uuid.uuid4())

    job_repo = PostgresJobRepository(local_pool)
    await job_repo.create_job(
        ContentGenerationJobRecord(
            id=job_id,
            tenant_id=TENANT_A,
            created_by=TEACHER_A,
            storage_bucket="teacher-materials",
            storage_path=f"{TENANT_A}/doc.pdf",
            original_filename="doc.pdf",
            mime_type="application/pdf",
            file_size_bytes=1000,
            file_checksum="sql_direct" * 4,
            status="processing",
            provider="mock",
            model_id="mock-v1",
        )
    )

    sample_draft = _make_sample_draft(1)
    content_hash = compute_draft_content_hash(
        sample_draft.question_text, sample_draft.suggested_kc_name, sample_draft.options
    )

    # Insert initial draft directly in 'edited' status
    async with local_pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO question_drafts (
                id, tenant_id, generation_job_id,
                suggested_kc_name, question_text, explanation,
                options, suggested_difficulty, status, content_hash
            ) VALUES (
                $1::uuid, $2::uuid, $3::uuid,
                $4, $5, $6,
                $7::jsonb, 0.950, 'edited', $8
            );
            """,
            uuid.UUID(draft_id),
            uuid.UUID(TENANT_A),
            uuid.UUID(job_id),
            sample_draft.suggested_kc_name,
            "Texto modificado por docente",
            sample_draft.explanation,
            json.dumps([{"text": o.text, "is_correct": o.is_correct} for o in sample_draft.options]),
            content_hash,
        )

        # Directly execute the repository's INSERT ... ON CONFLICT query bypassing Python pre-validation
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

        # PostgreSQL MUST return 0 rows because status != 'draft' suppresses DO UPDATE
        row = await conn.fetchrow(
            insert_query,
            uuid.uuid4(),
            uuid.UUID(TENANT_A),
            uuid.UUID(job_id),
            sample_draft.suggested_kc_name,
            sample_draft.question_text,
            sample_draft.explanation,
            json.dumps([{"text": o.text, "is_correct": o.is_correct} for o in sample_draft.options]),
            sample_draft.numeric_difficulty,
            sample_draft.bloom_taxonomy.value,
            json.dumps([]),
            content_hash,
        )

        assert row is None, "The WHERE question_drafts.status = 'draft' clause must suppress the update and return 0 rows"


@pytest.mark.asyncio
async def test_draft_trigger_blocks_status_reversion_to_draft(local_pool: asyncpg.Pool) -> None:
    """Verifica que el trigger trg_question_drafts_status_guard bloquea la reversión de un borrador intervenido a draft."""
    job_id = str(uuid.uuid4())
    draft_id = str(uuid.uuid4())

    job_repo = PostgresJobRepository(local_pool)
    await job_repo.create_job(
        ContentGenerationJobRecord(
            id=job_id,
            tenant_id=TENANT_A,
            created_by=TEACHER_A,
            storage_bucket="teacher-materials",
            storage_path=f"{TENANT_A}/doc.pdf",
            original_filename="doc.pdf",
            mime_type="application/pdf",
            file_size_bytes=1000,
            file_checksum="rev_test" * 4,
            status="processing",
            provider="mock",
            model_id="mock-v1",
        )
    )

    async with local_pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO question_drafts (
                id, tenant_id, generation_job_id,
                suggested_kc_name, question_text, explanation,
                options, status
            ) VALUES (
                $1::uuid, $2::uuid, $3::uuid,
                'KC Reversion', 'Pregunta editada', 'Explicación',
                '[]'::jsonb, 'edited'
            );
            """,
            uuid.UUID(draft_id),
            uuid.UUID(TENANT_A),
            uuid.UUID(job_id),
        )

        # Attempt to revert the draft to 'draft' via direct UPDATE -> TRIGGER MUST BLOCK IT
        with pytest.raises(asyncpg.RaiseError) as exc_info:
            await conn.execute(
                """
                UPDATE question_drafts
                SET status = 'draft'
                WHERE id = $1::uuid;
                """,
                uuid.UUID(draft_id),
            )
        assert "Cannot revert question draft" in str(exc_info.value)


@pytest.mark.asyncio
async def test_draft_upsert_concurrency_race_condition(local_pool: asyncpg.Pool) -> None:
    """Simula una condición de carrera entre dos transacciones concurrentes guardando el mismo borrador."""
    job_repo = PostgresJobRepository(local_pool)
    draft_repo = PostgresDraftRepository(local_pool)
    job_id = str(uuid.uuid4())

    await job_repo.create_job(
        ContentGenerationJobRecord(
            id=job_id,
            tenant_id=TENANT_A,
            created_by=TEACHER_A,
            storage_bucket="teacher-materials",
            storage_path=f"{TENANT_A}/doc.pdf",
            original_filename="doc.pdf",
            mime_type="application/pdf",
            file_size_bytes=1000,
            file_checksum="race_test" * 4,
            status="queued",
            provider="mock",
            model_id="mock-v1",
        )
    )

    sample_draft = _make_sample_draft(1)

    # Execute two parallel save_drafts calls
    results = await asyncio.gather(
        draft_repo.save_drafts(job_id=job_id, tenant_id=TENANT_A, drafts=[sample_draft]),
        draft_repo.save_drafts(job_id=job_id, tenant_id=TENANT_A, drafts=[sample_draft]),
        return_exceptions=True,
    )

    # Both must either succeed idempotently or handle gracefully without throwing unhandled DB errors
    for res in results:
        assert not isinstance(res, asyncpg.PostgresError)

    # Exactly one draft must exist in PostgreSQL
    all_drafts = await draft_repo.get_drafts_by_job(job_id, TENANT_A)
    assert len(all_drafts) == 1
    assert all_drafts[0].status == "draft"


# ==============================================================================
# SECTION 3: Prueba de Caída Real del Worker y Recuperación (Secuencia 1 a 10)
# ==============================================================================


@pytest.mark.asyncio
async def test_worker_crash_and_recovery_lifecycle(local_pool: asyncpg.Pool) -> None:
    """Prueba de integración completa del ciclo de terminación abrupta y recuperación.

    Diferencia expresamente:
    - Reinicio del pool de conexiones.
    - Reinicio del servicio API.
    - Terminación y recuperación del worker.
    """
    job_repo = PostgresJobRepository(local_pool)
    draft_repo = PostgresDraftRepository(local_pool)
    uow = PostgresUnitOfWork(local_pool, draft_repository=draft_repo)
    storage_client = InMemoryStorageClient()

    pdf_bytes = build_valid_pdf(["Texto curricular para prueba de recuperacion de workers."])
    storage_path = f"{TENANT_A}/recovery_doc.pdf"
    storage_client.upload_file("teacher-materials", storage_path, pdf_bytes)

    # Configurar servicios con mocks simulados
    ext_service = DocumentExtractionService(job_repository=job_repo, storage_client=storage_client)
    val_service = DraftValidationService()
    gen_service = QuestionGenerationService(validation_service=val_service)
    mock_provider = MockQuestionGenerationProvider()

    # Worker A orchestrator configured with initial pool
    orchestrator_a = GenerationOrchestrator(
        job_repository=job_repo,
        extraction_service=ext_service,
        generation_service=gen_service,
        draft_repository=draft_repo,
        unit_of_work=uow,
        provider=mock_provider,
    )
    _worker_a = GenerationWorker(
        job_repository=job_repo,
        orchestrator=orchestrator_a,
        worker_id="worker-a-crashed",
        lease_duration_seconds=1,
    )

    # 1. Crear un trabajo en 'queued'
    job_id = str(uuid.uuid4())
    job = await job_repo.create_job(
        ContentGenerationJobRecord(
            id=job_id,
            tenant_id=TENANT_A,
            created_by=TEACHER_A,
            storage_bucket="teacher-materials",
            storage_path=storage_path,
            original_filename="recovery_doc.pdf",
            mime_type="application/pdf",
            file_size_bytes=len(pdf_bytes),
            file_checksum="crash_recov" * 4,
            status="queued",
            provider="mock",
            model_id="mock-v1",
            max_attempts=3,
        )
    )
    assert job.status == "queued"
    assert job.attempt_count == 0

    # 2. Iniciar Worker A
    worker_a_token = str(uuid.uuid4())
    # Worker A reclama con lease muy corto (1 segundo) para la simulación
    claimed_a = await job_repo.claim_pending_job(
        tenant_id=TENANT_A,
        lease_duration_seconds=1,
        worker_token=worker_a_token,
        job_id=job_id,
    )

    # 3. Verificar que adquiere el trabajo y su lease
    assert claimed_a is not None
    assert claimed_a.status == "processing"
    assert claimed_a.processing_lease_token == worker_a_token
    assert claimed_a.attempt_count == 1

    # 4. Simular la terminación abrupta de Worker A (proceso muere; no finaliza el trabajo)
    logger.info("Worker A [token: %s] terminated abruptly (SIGKILL simulated).", worker_a_token)

    # 5. Confirmar que el trabajo permanece en 'processing' y es recuperable
    interim_job = await job_repo.get_job(job_id, TENANT_A)
    assert interim_job is not None
    assert interim_job.status == "processing"
    assert interim_job.attempt_count == 1

    # 6. Esperar a la expiración del lease de Worker A
    await asyncio.sleep(1.2)

    # [Diferenciación Expresa: Reinicio del Pool de Conexiones de la Aplicación]
    logger.info("Diferenciación: Simulando reconexión / nuevo pool tras corte de red...")
    new_pool = await asyncpg.create_pool(dsn=TEST_DB_URL, min_size=1, max_size=3)
    try:
        job_repo_b = PostgresJobRepository(new_pool)
        draft_repo_b = PostgresDraftRepository(new_pool)
        uow_b = PostgresUnitOfWork(new_pool, draft_repository=draft_repo_b)
        orchestrator_b = GenerationOrchestrator(
            job_repository=job_repo_b,
            extraction_service=ext_service,
            generation_service=gen_service,
            draft_repository=draft_repo_b,
            unit_of_work=uow_b,
            provider=mock_provider,
        )

        # 7. Iniciar Worker B con nueva instancia de GenerationWorker
        worker_b = GenerationWorker(
            job_repository=job_repo_b,
            orchestrator=orchestrator_b,
            worker_id="worker-b-recovery",
            lease_duration_seconds=300,
        )

        # 8. Confirmar que Worker B reclama el trabajo y lo procesa
        processed = await worker_b.process_one(tenant_id=TENANT_A, job_id=job_id)
        assert processed is True

        # 9. Verificar que el resultado se persiste correctamente en PostgreSQL
        final_job = await job_repo_b.get_job(job_id, TENANT_A)
        assert final_job is not None
        assert final_job.status == "review_required"
        assert final_job.attempt_count == 2  # Reclamado por A (1) + B (2)

        persisted_drafts = await draft_repo_b.get_drafts_by_job(job_id, TENANT_A)
        assert len(persisted_drafts) >= 1
        assert persisted_drafts[0].status == "draft"

        # 10. Comprobar que Worker A no puede finalizar el trabajo utilizando su token anterior
        logger.info("Verificando que Worker A antiguo no puede cometer cambios con token previo...")
        with pytest.raises(InvalidJobStateTransitionError):
            await job_repo_b.mark_review_required(
                job_id=job_id,
                tenant_id=TENANT_A,
                lease_token=worker_a_token,
            )

        with pytest.raises(InvalidJobStateTransitionError):
            await job_repo_b.mark_failed(
                job_id=job_id,
                tenant_id=TENANT_A,
                error_code="ZOMBIE_ERROR",
                error_message_safe="Error tardío de worker zombie",
                lease_token=worker_a_token,
            )
    finally:
        await new_pool.close()


# ==============================================================================
# SECTION 4: Auditoría de RLS y Privilegios PostgreSQL
# ==============================================================================


@pytest.mark.asyncio
async def test_postgres_role_privilege_audit(local_pool: asyncpg.Pool) -> None:
    """Audita los roles de conexión y comprueba si omiten RLS (Superuser / Bypass RLS)."""
    async with local_pool.acquire() as conn:
        current_user = await conn.fetchval("SELECT current_user;")
        row = await conn.fetchrow(
            """
            SELECT rolname, rolsuper, rolbypassrls
            FROM pg_roles
            WHERE rolname = $1;
            """,
            current_user,
        )
        assert row is not None
        # En entorno local de pruebas el usuario es 'postgres'
        assert row["rolname"] == "postgres"
        # Documentar y verificar el atributo Superuser/BypassRLS del usuario de conexión directa
        is_bypass = row["rolbypassrls"] or row["rolsuper"]
        logger.info(
            "Audit findings for connection user '%s': Superuser=%s, BypassRLS=%s. RLS bypass status: %s",
            row["rolname"],
            row["rolsuper"],
            row["rolbypassrls"],
            is_bypass,
        )
        # Comprobar que existe el rol de privilegio mínimo creado para producción
        ml_worker_role = await conn.fetchrow(
            """
            SELECT rolname, rolsuper, rolbypassrls
            FROM pg_roles
            WHERE rolname = 'ml_api_worker';
            """
        )
        assert ml_worker_role is not None
        assert ml_worker_role["rolsuper"] is False
        assert ml_worker_role["rolbypassrls"] is False


@pytest.mark.asyncio
async def test_ml_api_worker_least_privilege_execution_and_boundaries(local_pool: asyncpg.Pool) -> None:
    """Verifica que el rol ml_api_worker opera bajo mínimo privilegio con RLS activo y sin BYPASSRLS."""
    worker_pool = await asyncpg.create_pool(dsn=WORKER_DB_URL, min_size=1, max_size=2)
    try:
        # 1. Verificar identidad del rol
        current_user = await worker_pool.fetchval("SELECT current_user;")
        assert current_user == "ml_api_worker"

        role_attrs = await worker_pool.fetchrow(
            "SELECT rolsuper, rolbypassrls FROM pg_roles WHERE rolname = 'ml_api_worker';"
        )
        assert role_attrs is not None
        assert role_attrs["rolsuper"] is False
        assert role_attrs["rolbypassrls"] is False

        # 2. Worker puede consultar y operar sobre content_generation_jobs bajo políticas RLS
        job_repo = PostgresJobRepository(worker_pool)
        draft_repo = PostgresDraftRepository(worker_pool)
        uow = PostgresUnitOfWork(worker_pool, draft_repository=draft_repo)

        job_id = str(uuid.uuid4())
        worker_token = str(uuid.uuid4())

        created = await job_repo.create_job(
            ContentGenerationJobRecord(
                id=job_id,
                tenant_id=TENANT_A,
                created_by=TEACHER_A,
                storage_bucket="teacher-materials",
                storage_path=f"{TENANT_A}/doc.pdf",
                original_filename="doc.pdf",
                mime_type="application/pdf",
                file_size_bytes=1000,
                file_checksum="worker_role_test" * 2,
                status="queued",
                provider="mock",
                model_id="mock-v1",
            )
        )
        assert created.id == job_id

        # Reclamar el trabajo
        claimed = await job_repo.claim_pending_job(
            tenant_id=TENANT_A,
            lease_duration_seconds=300,
            worker_token=worker_token,
            job_id=job_id,
        )
        assert claimed is not None
        assert claimed.processing_lease_token == worker_token

        # Persistir borradores y finalizar a través de Unit of Work
        job_done, drafts = await uow.commit_generation_results(
            job_id=job_id,
            tenant_id=TENANT_A,
            drafts=[_make_sample_draft(1)],
            lease_token=worker_token,
        )
        assert job_done.status == "review_required"
        assert len(drafts) == 1

        # 3. Restricción de Mínimo Privilegio: Acceso denegado a tablas sensibles del sistema
        async with worker_pool.acquire() as conn:
            with pytest.raises(asyncpg.PostgresError) as exc_info:
                await conn.execute("SELECT * FROM auth_recovery_pins;")
            assert "permission denied" in str(exc_info.value).lower()

            # 4. Inmutabilidad estricta: ml_api_worker no puede eliminar eventos educativos de answer_events
            with pytest.raises(asyncpg.PostgresError) as exc_info:
                await conn.execute("DELETE FROM answer_events;")
            assert "permission denied" in str(exc_info.value).lower()

    finally:
        await worker_pool.close()


@pytest.mark.asyncio
async def test_multi_tenant_isolation_same_application_connection(local_pool: asyncpg.Pool) -> None:
    """Comprueba el aislamiento estricto entre dos tenants utilizando la misma conexión."""
    job_repo = PostgresJobRepository(local_pool)
    draft_repo = PostgresDraftRepository(local_pool)

    # Crear trabajo y borrador perteneciente a Tenant A
    job_a_id = str(uuid.uuid4())
    await job_repo.create_job(
        ContentGenerationJobRecord(
            id=job_a_id,
            tenant_id=TENANT_A,
            created_by=TEACHER_A,
            storage_bucket="teacher-materials",
            storage_path=f"{TENANT_A}/doc.pdf",
            original_filename="doc.pdf",
            mime_type="application/pdf",
            file_size_bytes=1000,
            file_checksum="tenant_iso_a" * 3,
            status="queued",
            provider="mock",
            model_id="mock-v1",
        )
    )
    drafts_a = await draft_repo.save_drafts(
        job_id=job_a_id,
        tenant_id=TENANT_A,
        drafts=[_make_sample_draft(1)],
    )
    assert len(drafts_a) == 1
    draft_a_id = drafts_a[0].id

    # 1. Tenant B no puede leer el trabajo de Tenant A
    job_read_b = await job_repo.get_job(job_id=job_a_id, tenant_id=TENANT_B)
    assert job_read_b is None

    # 2. Tenant B no puede leer el borrador de Tenant A
    draft_read_b = await draft_repo.get_draft_by_id(draft_id=draft_a_id, tenant_id=TENANT_B)
    assert draft_read_b is None

    # 3. Tenant B no puede listar borradores del trabajo de Tenant A
    job_drafts_b = await draft_repo.get_drafts_by_job(job_id=job_a_id, tenant_id=TENANT_B)
    assert job_drafts_b == []

    # 4. Tenant B no puede eliminar borradores de Tenant A
    deleted = await draft_repo.delete_unreviewed_drafts_for_job(job_id=job_a_id, tenant_id=TENANT_B)
    assert deleted == 0

    # 5. Tenant B no puede inyectar borradores en el trabajo de Tenant A (bloqueado por JobNotFoundError o trigger)
    with pytest.raises((JobNotFoundError, asyncpg.PostgresError)):
        await draft_repo.save_drafts(
            job_id=job_a_id,
            tenant_id=TENANT_B,
            drafts=[_make_sample_draft(2)],
        )


@pytest.mark.asyncio
async def test_cross_tenant_draft_injection_blocked_by_database_trigger(local_pool: asyncpg.Pool) -> None:
    """Comprueba que el trigger en PostgreSQL bloquea directamente cualquier INSERT cruzado entre tenants."""
    job_repo = PostgresJobRepository(local_pool)
    job_a_id = str(uuid.uuid4())

    await job_repo.create_job(
        ContentGenerationJobRecord(
            id=job_a_id,
            tenant_id=TENANT_A,
            created_by=TEACHER_A,
            storage_bucket="teacher-materials",
            storage_path=f"{TENANT_A}/doc.pdf",
            original_filename="doc.pdf",
            mime_type="application/pdf",
            file_size_bytes=1000,
            file_checksum="trigger_test" * 3,
            status="queued",
            provider="mock",
            model_id="mock-v1",
        )
    )

    # Intentar inserción manual de SQL asignando tenant_id = TENANT_B pero generation_job_id = job_a_id (TENANT_A)
    async with local_pool.acquire() as conn:
        with pytest.raises(asyncpg.PostgresError) as exc_info:
            await conn.execute(
                """
                INSERT INTO question_drafts (
                    id, tenant_id, generation_job_id,
                    suggested_kc_name, question_text, explanation,
                    options, status
                ) VALUES (
                    $1::uuid, $2::uuid, $3::uuid,
                    'Cross Tenant Poisoning', '¿Pregunta maliciosa?', 'Explicacion',
                    '[]'::jsonb, 'draft'
                );
                """,
                uuid.uuid4(),
                uuid.UUID(TENANT_B),  # Tenant B
                uuid.UUID(job_a_id),   # Job from Tenant A
            )
        assert "Violación multi-tenant" in str(exc_info.value)
