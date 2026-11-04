"""Comprehensive PostgreSQL Integration Tests for Milestone M2.3.

Validates against real local PostgreSQL instance (plataformamicro_test):
1. Create and retrieve a job from PostgreSQL.
2. Persist drafts to PostgreSQL.
3. Retrieve drafts after simulated service restart (new pool).
4. Multi-tenant isolation (Tenant B cannot see Tenant A's jobs/drafts; 403/404).
5. Transactional Unit of Work atomicity (drafts + review_required in 1 transaction).
6. Simulated persistence failure and atomic rollback.
7. Real draft idempotency on retry without duplicates.
8. Partial unique index on active jobs (active conflict, allowed after completion).
9. Lease recovery for abandoned jobs with expired lease.
10. Concurrency fencing: prevent duplicate simultaneous processing.
11. Fencing token protection: zombie worker cannot update stolen job.
12. Protection of human-reviewed drafts (edited, approved, rejected).
13. HTTP REST endpoints real flow (POST /jobs -> 202, GET /jobs/{id} -> 200).
14. Authorization enforcement (student -> 403, missing auth -> 401).
15. Canonical tables quarantine check (questions and question_options untouched).
16. Durable worker execution flow.
"""

import asyncio
import logging
import uuid

import asyncpg
import httpx
import pytest

logger = logging.getLogger(__name__)

from app.content_generation.exceptions import (
    DraftAlreadyReviewedError,
    InvalidJobStateTransitionError,
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
    DocumentType,
    DocumentUnitType,
    ExtractedDocument,
    ExtractedUnit,
)
from app.content_generation.schemas.generated_questions import (
    BloomTaxonomy,
    GeneratedQuestionDraft,
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
from app.content_generation.worker import GenerationWorker
from app.main import app

# Known seed IDs from 20261102180000_content_generation_test.sql
TENANT_A = "11111111-1111-1111-1111-111111111111"
TENANT_B = "22222222-2222-2222-2222-222222222222"
TEACHER_A = "11111111-1111-1111-1111-aaaaaaaaaaaa"
STUDENT_A = "11111111-1111-1111-1111-bbbbbbbbbbbb"
TEACHER_B = "22222222-2222-2222-2222-aaaaaaaaaaaa"
COURSE_A1 = "11111111-1111-1111-1111-cccccccccccc"
COURSE_B1 = "22222222-2222-2222-2222-cccccccccccc"

TEST_DB_URL = "postgresql://postgres:postgres@127.0.0.1:5432/plataformamicro_test"


@pytest.fixture
async def db_pool():
    """Create fresh asyncpg pool for each test on the active event loop with clean state."""
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
        logger.debug("Database cleanup warning: %s", e)
    finally:
        await pool.close()


@pytest.fixture(autouse=True)
def override_database_dependency(db_pool):
    """Override get_database_pool with test db_pool on the test's active loop."""
    from app.content_generation.dependencies import get_database_pool
    app.dependency_overrides[get_database_pool] = lambda: db_pool
    yield
    app.dependency_overrides.clear()




def make_sample_drafts(count: int = 2) -> list[GeneratedQuestionDraft]:
    """Factory helper generating validated GeneratedQuestionDraft objects."""
    drafts: list[GeneratedQuestionDraft] = []
    for i in range(1, count + 1):
        drafts.append(
            GeneratedQuestionDraft(
                suggested_kc_name=f"Fotosintesis Fase Luminosa {i}",
                question_text=f"¿En que estructura celular se realiza la fase luminosa de la fotosintesis? ({i})",
                question_type=QuestionType.SINGLE_CHOICE,
                difficulty=0.500,
                bloom_taxonomy=BloomTaxonomy.UNDERSTAND,
                options=[
                    QuestionOptionDraft(text="En las membranas de los tilacoides", is_correct=True),
                    QuestionOptionDraft(text="En el estroma del cloroplasto", is_correct=False, misconception_explanation="El estroma es el sitio de la fase oscura."),
                    QuestionOptionDraft(text="En la matriz mitocondrial", is_correct=False),
                    QuestionOptionDraft(text="En el reticulo endoplasmatico", is_correct=False),
                ],
                explanation="La fotofosforilacion y fotolisis del agua ocurren en los tilacoides.",
                source_references=[
                    QuestionSourceReference(type=DocumentUnitType.PAGE, index=1, snippet="membranas de los tilacoides")
                ],
            )
        )
    return drafts


# ==============================================================================
# 1. Crear y Recuperar un Job en PostgreSQL
# ==============================================================================


@pytest.mark.asyncio
async def test_create_and_get_job_postgres(db_pool):
    """Verify persisting and querying a content generation job in local PostgreSQL."""
    job_repo = PostgresJobRepository(db_pool)
    job_id = str(uuid.uuid4())

    job = ContentGenerationJobRecord(
        id=job_id,
        tenant_id=TENANT_A,
        created_by=TEACHER_A,
        storage_bucket="teacher-materials",
        storage_path=f"{TENANT_A}/ciencias/guia1.pdf",
        original_filename="guia1.pdf",
        mime_type="application/pdf",
        file_size_bytes=1048576,
        file_checksum="a" * 64,
        status="queued",
        provider="mock",
        model_id="mock-v1",
        course_id=COURSE_A1,
    )

    created = await job_repo.create_job(job)
    assert created.id == job_id
    assert created.status == "queued"
    assert created.attempt_count == 0

    fetched = await job_repo.get_job(job_id=job_id, tenant_id=TENANT_A)
    assert fetched is not None
    assert fetched.id == job_id
    assert fetched.original_filename == "guia1.pdf"
    assert fetched.storage_path == f"{TENANT_A}/ciencias/guia1.pdf"


# ==============================================================================
# 2. Persistir Borradores en PostgreSQL
# ==============================================================================


@pytest.mark.asyncio
async def test_persist_drafts_postgres(db_pool):
    """Verify persisting validated question drafts with JSONB and content hashes."""
    job_repo = PostgresJobRepository(db_pool)
    draft_repo = PostgresDraftRepository(db_pool)

    job_id = str(uuid.uuid4())
    await job_repo.create_job(
        ContentGenerationJobRecord(
            id=job_id,
            tenant_id=TENANT_A,
            created_by=TEACHER_A,
            storage_bucket="teacher-materials",
            storage_path=f"{TENANT_A}/ciencias/doc.pdf",
            original_filename="doc.pdf",
            mime_type="application/pdf",
            file_size_bytes=1000,
            file_checksum="b" * 64,
            status="queued",
            provider="mock",
            model_id="mock-v1",
        )
    )

    sample_drafts = make_sample_drafts(2)
    saved_records = await draft_repo.save_drafts(
        job_id=job_id,
        tenant_id=TENANT_A,
        drafts=sample_drafts,
    )

    assert len(saved_records) == 2
    for record in saved_records:
        assert record.generation_job_id == job_id
        assert record.tenant_id == TENANT_A
        assert record.status == "draft"
        assert len(record.options) == 4
        assert record.content_hash is not None


# ==============================================================================
# 3. Recuperar Borradores tras Reinicio del Servicio (Nuevo Pool)
# ==============================================================================


@pytest.mark.asyncio
async def test_retrieve_drafts_after_service_restart(db_pool):
    """Verify drafts survive container restart by creating a completely separate connection."""
    job_repo = PostgresJobRepository(db_pool)
    draft_repo = PostgresDraftRepository(db_pool)

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
            file_checksum="c" * 64,
            status="queued",
            provider="mock",
            model_id="mock-v1",
        )
    )

    await draft_repo.save_drafts(job_id=job_id, tenant_id=TENANT_A, drafts=make_sample_drafts(2))

    # Simulate cold restart: open brand new independent pool
    fresh_pool = await asyncpg.create_pool(dsn=TEST_DB_URL, min_size=1, max_size=2)
    try:
        fresh_draft_repo = PostgresDraftRepository(fresh_pool)
        retrieved = await fresh_draft_repo.get_drafts_by_job(job_id=job_id, tenant_id=TENANT_A)
        assert len(retrieved) == 2
        assert retrieved[0].suggested_kc_name.startswith("Fotosintesis")
    finally:
        await fresh_pool.close()


# ==============================================================================
# 4. Verificar Aislamiento Multitenant
# ==============================================================================


@pytest.mark.asyncio
async def test_multitenant_isolation(db_pool):
    """Verify Tenant B cannot access jobs or drafts created by Tenant A."""
    job_repo = PostgresJobRepository(db_pool)
    draft_repo = PostgresDraftRepository(db_pool)

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
            file_checksum="d" * 64,
            status="queued",
            provider="mock",
            model_id="mock-v1",
        )
    )
    await draft_repo.save_drafts(job_id=job_id, tenant_id=TENANT_A, drafts=make_sample_drafts(2))

    # Tenant B tries to fetch Job A -> Must return None
    cross_job = await job_repo.get_job(job_id=job_id, tenant_id=TENANT_B)
    assert cross_job is None

    # Tenant B tries to fetch Drafts A -> Must return empty list
    cross_drafts = await draft_repo.get_drafts_by_job(job_id=job_id, tenant_id=TENANT_B)
    assert len(cross_drafts) == 0


# ==============================================================================
# 5. Comprobar Atomicidad de Borradores y Transición de Estado (Unit of Work)
# ==============================================================================


@pytest.mark.asyncio
async def test_uow_atomicity(db_pool):
    """Verify drafts are inserted and job transitions to review_required in a single transaction."""
    job_repo = PostgresJobRepository(db_pool)
    draft_repo = PostgresDraftRepository(db_pool)
    uow = PostgresUnitOfWork(db_pool, draft_repository=draft_repo)

    job_id = str(uuid.uuid4())
    token = str(uuid.uuid4())

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
            file_checksum="e" * 64,
            status="queued",
            provider="mock",
            model_id="mock-v1",
        )
    )
    # Transition to processing with lease token
    await job_repo.mark_processing(job_id=job_id, tenant_id=TENANT_A, lease_token=token)

    sample_drafts = make_sample_drafts(3)
    updated_job, saved_drafts = await uow.commit_generation_results(
        job_id=job_id,
        tenant_id=TENANT_A,
        drafts=sample_drafts,
        lease_token=token,
    )

    assert updated_job.status == "review_required"
    assert updated_job.completed_at is not None
    assert len(saved_drafts) == 3

    # Direct database verification
    persisted_drafts = await draft_repo.get_drafts_by_job(job_id=job_id, tenant_id=TENANT_A)
    assert len(persisted_drafts) == 3


# ==============================================================================
# 6. Simular Fallos de Persistencia y Rollback Atómico
# ==============================================================================


@pytest.mark.asyncio
async def test_uow_rollback_on_failure(db_pool):
    """Verify rollback leaves 0 drafts and job NOT in review_required if error occurs."""
    job_repo = PostgresJobRepository(db_pool)
    draft_repo = PostgresDraftRepository(db_pool)
    uow = PostgresUnitOfWork(db_pool, draft_repository=draft_repo)

    job_id = str(uuid.uuid4())
    token = str(uuid.uuid4())
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
            file_checksum="f" * 64,
            status="queued",
            provider="mock",
            model_id="mock-v1",
        )
    )
    # Job is marked processing with token
    await job_repo.mark_processing(job_id=job_id, tenant_id=TENANT_A, lease_token=token)

    # Unit of work with WRONG lease token -> must fail on job status update and rollback drafts!
    with pytest.raises(InvalidJobStateTransitionError):
        await uow.commit_generation_results(
            job_id=job_id,
            tenant_id=TENANT_A,
            drafts=make_sample_drafts(2),
            lease_token=wrong_token,
        )

    # Verify rollback: ZERO drafts must exist, and job must still be in 'processing'
    drafts_in_db = await draft_repo.get_drafts_by_job(job_id=job_id, tenant_id=TENANT_A)
    assert len(drafts_in_db) == 0

    job_in_db = await job_repo.get_job(job_id=job_id, tenant_id=TENANT_A)
    assert job_in_db is not None
    assert job_in_db.status == "processing"


# ==============================================================================
# 7. Comprobar Idempotencia Real de Borradores
# ==============================================================================


@pytest.mark.asyncio
async def test_draft_idempotency_on_retry(db_pool):
    """Verify re-executing draft persistence replaces unreviewed drafts without duplication."""
    job_repo = PostgresJobRepository(db_pool)
    draft_repo = PostgresDraftRepository(db_pool)

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
            file_checksum="1" * 64,
            status="queued",
            provider="mock",
            model_id="mock-v1",
        )
    )

    # First attempt: 2 drafts
    await draft_repo.save_drafts(job_id=job_id, tenant_id=TENANT_A, drafts=make_sample_drafts(2))
    assert len(await draft_repo.get_drafts_by_job(job_id, TENANT_A)) == 2

    # Second attempt: retry with 2 drafts -> must replace unreviewed drafts, count remains 2
    await draft_repo.save_drafts(job_id=job_id, tenant_id=TENANT_A, drafts=make_sample_drafts(2))
    assert len(await draft_repo.get_drafts_by_job(job_id, TENANT_A)) == 2


# ==============================================================================
# 8. Comprobar Restricción de Unicidad Parcial (Trabajos Activos)
# ==============================================================================


@pytest.mark.asyncio
async def test_partial_unique_index_active_jobs(db_pool):
    """Verify uq_content_gen_jobs_active_file blocks duplicate active jobs, but allows new jobs after completion."""
    job_repo = PostgresJobRepository(db_pool)
    checksum = "checksum_unique_123"

    job1_id = str(uuid.uuid4())
    await job_repo.create_job(
        ContentGenerationJobRecord(
            id=job1_id,
            tenant_id=TENANT_A,
            created_by=TEACHER_A,
            storage_bucket="teacher-materials",
            storage_path=f"{TENANT_A}/doc.pdf",
            original_filename="doc.pdf",
            mime_type="application/pdf",
            file_size_bytes=1000,
            file_checksum=checksum,
            status="queued",
            provider="mock",
            model_id="mock-v1",
            course_id=COURSE_A1,
        )
    )

    # Concurrent attempt to create active job with same checksum and course -> Must fail
    job2_id = str(uuid.uuid4())
    with pytest.raises(InvalidJobStateTransitionError):
        await job_repo.create_job(
            ContentGenerationJobRecord(
                id=job2_id,
                tenant_id=TENANT_A,
                created_by=TEACHER_A,
                storage_bucket="teacher-materials",
                storage_path=f"{TENANT_A}/doc.pdf",
                original_filename="doc.pdf",
                mime_type="application/pdf",
                file_size_bytes=1000,
                file_checksum=checksum,
                status="queued",
                provider="mock",
                model_id="mock-v1",
                course_id=COURSE_A1,
            )
        )

    # Complete job1 (transition to review_required)
    p_job1 = await job_repo.mark_processing(job_id=job1_id, tenant_id=TENANT_A)
    await job_repo.mark_review_required(job_id=job1_id, tenant_id=TENANT_A, lease_token=p_job1.processing_lease_token)

    # Now creating job3 with the same checksum and course MUST succeed
    job3_id = str(uuid.uuid4())
    job3 = await job_repo.create_job(
        ContentGenerationJobRecord(
            id=job3_id,
            tenant_id=TENANT_A,
            created_by=TEACHER_A,
            storage_bucket="teacher-materials",
            storage_path=f"{TENANT_A}/doc.pdf",
            original_filename="doc.pdf",
            mime_type="application/pdf",
            file_size_bytes=1000,
            file_checksum=checksum,
            status="queued",
            provider="mock",
            model_id="mock-v1",
            course_id=COURSE_A1,
        )
    )
    assert job3.id == job3_id


# ==============================================================================
# 9. Recuperar Trabajos con Leases Expirados
# ==============================================================================


@pytest.mark.asyncio
async def test_reclaim_abandoned_job_with_expired_lease(db_pool):
    """Verify an abandoned processing job whose lease expired is reclaimed by another worker."""
    job_repo = PostgresJobRepository(db_pool)
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
            file_checksum="2" * 64,
            status="queued",
            provider="mock",
            model_id="mock-v1",
        )
    )

    # Worker 1 claims job with 1 second lease
    worker1_token = str(uuid.uuid4())
    claimed_by_w1 = await job_repo.claim_pending_job(
        tenant_id=TENANT_A,
        lease_duration_seconds=1,
        worker_token=worker1_token,
        job_id=job_id,
    )
    assert claimed_by_w1 is not None
    assert claimed_by_w1.attempt_count == 1
    assert claimed_by_w1.processing_lease_token == worker1_token

    # Wait for lease to expire
    await asyncio.sleep(2.0)

    # Worker 2 attempts to claim -> must succeed and reclaim the abandoned job
    worker2_token = str(uuid.uuid4())
    claimed_by_w2 = await job_repo.claim_pending_job(
        tenant_id=TENANT_A,
        lease_duration_seconds=300,
        worker_token=worker2_token,
        job_id=job_id,
    )
    assert claimed_by_w2 is not None
    assert claimed_by_w2.id == job_id
    assert claimed_by_w2.attempt_count == 2
    assert claimed_by_w2.processing_lease_token == worker2_token


# ==============================================================================
# 10. Impedir Procesamiento Concurrente Duplicado (SELECT FOR UPDATE SKIP LOCKED)
# ==============================================================================


@pytest.mark.asyncio
async def test_prevent_concurrent_duplicate_processing(db_pool):
    """Verify two concurrent claim requests only allow one worker to acquire the job."""
    job_repo = PostgresJobRepository(db_pool)
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
            file_checksum="3" * 64,
            status="queued",
            provider="mock",
            model_id="mock-v1",
        )
    )

    # Run two claims concurrently
    res1, res2 = await asyncio.gather(
        job_repo.claim_pending_job(tenant_id=TENANT_A, job_id=job_id),
        job_repo.claim_pending_job(tenant_id=TENANT_A, job_id=job_id),
    )

    # Exactly one worker gets the job; the other gets None
    claimed_count = sum(1 for r in (res1, res2) if r is not None)
    assert claimed_count == 1


# ==============================================================================
# 11. Protección de Fencing: Worker Antiguo no puede actualizar Job Reclamado
# ==============================================================================


@pytest.mark.asyncio
async def test_zombie_worker_fence_token_protection(db_pool):
    """Verify zombie worker holding expired lease token is blocked from updating after another worker claimed job."""
    job_repo = PostgresJobRepository(db_pool)
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
            file_checksum="4" * 64,
            status="queued",
            provider="mock",
            model_id="mock-v1",
        )
    )

    old_worker_token = str(uuid.uuid4())
    await job_repo.claim_pending_job(tenant_id=TENANT_A, lease_duration_seconds=1, worker_token=old_worker_token, job_id=job_id)

    # Expire lease
    await asyncio.sleep(2.0)

    # New worker claims with new token
    new_worker_token = str(uuid.uuid4())
    await job_repo.claim_pending_job(tenant_id=TENANT_A, lease_duration_seconds=300, worker_token=new_worker_token, job_id=job_id)

    # Zombie worker attempts to mark review_required with old token -> MUST BE BLOCKED
    with pytest.raises(InvalidJobStateTransitionError):
        await job_repo.mark_review_required(job_id=job_id, tenant_id=TENANT_A, lease_token=old_worker_token)

    # Zombie worker attempts to renew lease -> MUST BE BLOCKED
    with pytest.raises(InvalidJobStateTransitionError):
        await job_repo.renew_lease(job_id=job_id, tenant_id=TENANT_A, lease_token=old_worker_token)


# ==============================================================================
# 12. Proteger Borradores Editados o Aprobados
# ==============================================================================


@pytest.mark.asyncio
async def test_protect_reviewed_drafts(db_pool):
    """Verify drafts in status != 'draft' (e.g. edited, approved) reject overwrites and deletions."""
    job_repo = PostgresJobRepository(db_pool)
    draft_repo = PostgresDraftRepository(db_pool)

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
            file_checksum="5" * 64,
            status="queued",
            provider="mock",
            model_id="mock-v1",
        )
    )

    records = await draft_repo.save_drafts(job_id=job_id, tenant_id=TENANT_A, drafts=make_sample_drafts(2))

    # Teacher reviews one draft: simulate status update to 'edited'
    async with db_pool.acquire() as conn:
        await conn.execute(
            "UPDATE question_drafts SET status = 'edited' WHERE id = $1::uuid;",
            uuid.UUID(records[0].id),
        )

    # Subsequent attempt to save new drafts on this job must fail with DraftAlreadyReviewedError
    with pytest.raises(DraftAlreadyReviewedError):
        await draft_repo.save_drafts(job_id=job_id, tenant_id=TENANT_A, drafts=make_sample_drafts(2))

    # Deletion of unreviewed drafts must also fail with DraftAlreadyReviewedError
    with pytest.raises(DraftAlreadyReviewedError):
        await draft_repo.delete_unreviewed_drafts_for_job(job_id=job_id, tenant_id=TENANT_A)


# ==============================================================================
# 13. Validar Endpoints HTTP Reales (POST /jobs, GET /jobs/{id}, GET /drafts)
# ==============================================================================


@pytest.mark.asyncio
async def test_http_endpoints_real_flow(db_pool):
    """Verify HTTP REST flow against running FastAPI application and local PostgreSQL."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. POST /api/v1/content-generation/jobs
        payload = {
            "storage_path": f"{TENANT_A}/ciencias/resumen.pdf",
            "original_filename": "resumen.pdf",
            "mime_type": "application/pdf",
            "file_size_bytes": 204800,
            "file_checksum": "sha256_http_test_flow_0123456789012345",
            "course_id": COURSE_A1,
            "storage_bucket": "teacher-materials",
            "target_num_questions": 5,
        }
        headers = {
            "X-User-Id": TEACHER_A,
            "X-Tenant-Id": TENANT_A,
            "X-User-Role": "teacher",
            "X-Course-Ids": COURSE_A1,
        }

        resp = await client.post("/api/v1/content-generation/jobs", json=payload, headers=headers)
        assert resp.status_code == 202
        body = resp.json()
        job_id = body["job_id"]
        assert body["status"] == "queued"
        assert body["tenant_id"] == TENANT_A

        # 2. GET /api/v1/content-generation/jobs/{job_id}
        get_resp = await client.get(f"/api/v1/content-generation/jobs/{job_id}", headers=headers)
        assert get_resp.status_code == 200
        assert get_resp.json()["job_id"] == job_id
        assert get_resp.json()["status"] == "queued"

        # 3. Insert some drafts and check GET /drafts
        draft_repo = PostgresDraftRepository(db_pool)
        await draft_repo.save_drafts(job_id=job_id, tenant_id=TENANT_A, drafts=make_sample_drafts(2))

        drafts_resp = await client.get(f"/api/v1/content-generation/jobs/{job_id}/drafts", headers=headers)
        assert drafts_resp.status_code == 200
        drafts_list = drafts_resp.json()
        assert len(drafts_list) == 2
        assert drafts_list[0]["generation_job_id"] == job_id
        assert drafts_list[0]["status"] == "draft"


# ==============================================================================
# 14. Verificar Respuestas 401/403/404 según Modelo de Autorización
# ==============================================================================


@pytest.mark.asyncio
async def test_http_authorization_and_cross_tenant_errors(db_pool):
    """Verify 401 for missing auth, 403 for students, and 404 for cross-tenant job queries."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # A. Missing credentials -> 401
        resp_401 = await client.post(
            "/api/v1/content-generation/jobs",
            json={
                "storage_path": f"{TENANT_A}/doc.pdf",
                "original_filename": "doc.pdf",
                "mime_type": "application/pdf",
                "file_size_bytes": 100,
                "file_checksum": "a" * 32,
            },
        )
        assert resp_401.status_code == 401
        assert resp_401.json()["code"] == "MISSING_CREDENTIALS"

        # B. Student role -> 403
        student_headers = {
            "X-User-Id": STUDENT_A,
            "X-Tenant-Id": TENANT_A,
            "X-User-Role": "student",
        }
        resp_403 = await client.post(
            "/api/v1/content-generation/jobs",
            json={
                "storage_path": f"{TENANT_A}/doc.pdf",
                "original_filename": "doc.pdf",
                "mime_type": "application/pdf",
                "file_size_bytes": 100,
                "file_checksum": "b" * 32,
            },
            headers=student_headers,
        )
        assert resp_403.status_code == 403
        assert resp_403.json()["code"] == "INSUFFICIENT_PERMISSIONS"

        # C. Storage path from another tenant -> 403
        teacher_headers = {
            "X-User-Id": TEACHER_A,
            "X-Tenant-Id": TENANT_A,
            "X-User-Role": "teacher",
        }
        resp_path_403 = await client.post(
            "/api/v1/content-generation/jobs",
            json={
                "storage_path": f"{TENANT_B}/stolen_doc.pdf",  # Tenant B path!
                "original_filename": "stolen_doc.pdf",
                "mime_type": "application/pdf",
                "file_size_bytes": 100,
                "file_checksum": "c" * 32,
            },
            headers=teacher_headers,
        )
        assert resp_path_403.status_code == 403
        assert resp_path_403.json()["code"] == "UNAUTHORIZED_STORAGE_ACCESS"

        # D. Cross-tenant access to Job -> 404
        # First create a job for Tenant A
        job_repo = PostgresJobRepository(db_pool)
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
                file_checksum="d" * 32,
                status="queued",
                provider="mock",
                model_id="mock-v1",
            )
        )

        teacher_b_headers = {
            "X-User-Id": TEACHER_B,
            "X-Tenant-Id": TENANT_B,
            "X-User-Role": "teacher",
        }
        cross_resp = await client.get(
            f"/api/v1/content-generation/jobs/{job_id}",
            headers=teacher_b_headers,
        )
        assert cross_resp.status_code == 404
        assert cross_resp.json()["code"] == "JOB_NOT_FOUND"


# ==============================================================================
# 15. Verificar Tablas Canónicas No Tocadas
# ==============================================================================


@pytest.mark.asyncio
async def test_canonical_tables_untouched(db_pool):
    """Verify that generation pipeline does not touch canonical questions or question_options tables."""
    async with db_pool.acquire() as conn:
        q_count_before = await conn.fetchval("SELECT count(*) FROM questions;")
        opt_count_before = await conn.fetchval("SELECT count(*) FROM question_options;")

    # Run full generation flow
    job_repo = PostgresJobRepository(db_pool)
    draft_repo = PostgresDraftRepository(db_pool)
    uow = PostgresUnitOfWork(db_pool, draft_repository=draft_repo)

    job_id = str(uuid.uuid4())
    token = str(uuid.uuid4())

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
            file_checksum="canonical_check_12345",
            status="queued",
            provider="mock",
            model_id="mock-v1",
        )
    )
    await job_repo.mark_processing(job_id=job_id, tenant_id=TENANT_A, lease_token=token)
    await uow.commit_generation_results(job_id=job_id, tenant_id=TENANT_A, drafts=make_sample_drafts(3), lease_token=token)

    async with db_pool.acquire() as conn:
        q_count_after = await conn.fetchval("SELECT count(*) FROM questions;")
        opt_count_after = await conn.fetchval("SELECT count(*) FROM question_options;")

    assert q_count_after == q_count_before
    assert opt_count_after == opt_count_before


# ==============================================================================
# 16. Worker de Procesamiento Durable en PostgreSQL
# ==============================================================================


@pytest.mark.asyncio
async def test_durable_worker_execution(db_pool):
    """Verify GenerationWorker claims queued job, executes generation pipeline, and persists drafts."""
    job_repo = PostgresJobRepository(db_pool)
    draft_repo = PostgresDraftRepository(db_pool)
    uow = PostgresUnitOfWork(db_pool, draft_repository=draft_repo)

    storage_client = InMemoryStorageClient()
    file_bytes = b"%PDF-1.4 simulated pdf data"
    storage_path = f"{TENANT_A}/ciencias/celula.pdf"
    storage_client.upload_file("teacher-materials", storage_path, file_bytes)

    # Fake extractor returning valid extracted doc
    class FakeExtractorService(DocumentExtractionService):
        async def extract_document_for_job(self, *args, **kwargs) -> ExtractedDocument:
            return ExtractedDocument(
                document_id="doc-fake-1",
                document_type=DocumentType.PDF,
                total_units=1,
                units=[
                    ExtractedUnit(
                        type=DocumentUnitType.PAGE,
                        index=1,
                        text="Capitulo 1: membranas de los tilacoides y fase luminosa.",
                    )
                ],
            )

    extraction_service = FakeExtractorService(job_repository=job_repo, storage_client=storage_client)
    validation_service = DraftValidationService()
    mock_provider = MockQuestionGenerationProvider()
    generation_service = QuestionGenerationService(validation_service=validation_service)

    orchestrator = GenerationOrchestrator(
        job_repository=job_repo,
        extraction_service=extraction_service,
        generation_service=generation_service,
        draft_repository=draft_repo,
        provider=mock_provider,
        unit_of_work=uow,
    )

    worker = GenerationWorker(
        job_repository=job_repo,
        orchestrator=orchestrator,
        lease_duration_seconds=300,
        heartbeat_interval_seconds=1,
    )

    # Create job in 'queued' state
    job_id = str(uuid.uuid4())
    await job_repo.create_job(
        ContentGenerationJobRecord(
            id=job_id,
            tenant_id=TENANT_A,
            created_by=TEACHER_A,
            storage_bucket="teacher-materials",
            storage_path=storage_path,
            original_filename="celula.pdf",
            mime_type="application/pdf",
            file_size_bytes=len(file_bytes),
            file_checksum="worker_test_checksum_9999",
            status="queued",
            provider="mock",
            model_id="mock-v1",
        )
    )

    # Run worker on one job
    processed = await worker.process_one(tenant_id=TENANT_A, job_id=job_id)
    assert processed is True

    # Verify job is now review_required
    completed_job = await job_repo.get_job(job_id=job_id, tenant_id=TENANT_A)
    assert completed_job is not None
    assert completed_job.status == "review_required"
    assert completed_job.completed_at is not None

    # Verify drafts persisted into PostgreSQL
    drafts = await draft_repo.get_drafts_by_job(job_id=job_id, tenant_id=TENANT_A)
    assert len(drafts) > 0
    assert drafts[0].status == "draft"


# ==============================================================================
# 17. Recuperación de Trabajos Excediendo Límite de Intentos (Max Attempts)
# ==============================================================================


@pytest.mark.asyncio
async def test_expired_lease_max_attempts_transition_to_failed_and_unblock_new_jobs(db_pool):
    """Verify jobs with expired leases exceeding max_attempts are failed and allow new job submissions."""
    job_repo = PostgresJobRepository(db_pool)
    jid = str(uuid.uuid4())
    checksum = f"chk_max_attempts_{uuid.uuid4().hex[:12]}"

    job = ContentGenerationJobRecord(
        id=jid,
        tenant_id=TENANT_A,
        created_by=TEACHER_A,
        storage_bucket="teacher-materials",
        storage_path=f"{TENANT_A}/doc_fail.pdf",
        original_filename="doc_fail.pdf",
        mime_type="application/pdf",
        file_size_bytes=1000,
        file_checksum=checksum,
        status="queued",
        provider="mock",
        model_id="mock-v1",
        course_id=COURSE_A1,
        max_attempts=1,
    )
    await job_repo.create_job(job)

    # First claim (attempt_count reaches 1 == max_attempts)
    c1 = await job_repo.claim_pending_job(
        tenant_id=TENANT_A, lease_duration_seconds=1, job_id=jid
    )
    assert c1 is not None
    assert c1.attempt_count == 1

    # Simulate worker crash: wait for lease to expire
    await asyncio.sleep(2.0)

    # Next claim call triggers auto-recovery: job must be transitioned to failed
    claimed = await job_repo.claim_pending_job(tenant_id=TENANT_A, job_id=jid)
    assert claimed is None

    # Verify status in database is now 'failed' with MAX_ATTEMPTS_EXCEEDED
    failed_job = await job_repo.get_job(jid, TENANT_A)
    assert failed_job is not None
    assert failed_job.status == "failed"
    assert failed_job.error_code == "MAX_ATTEMPTS_EXCEEDED"

    # Crucial acceptance test: partial unique index MUST allow creating a new job for same file & course
    new_jid = str(uuid.uuid4())
    new_job = ContentGenerationJobRecord(
        id=new_jid,
        tenant_id=TENANT_A,
        created_by=TEACHER_A,
        storage_bucket="teacher-materials",
        storage_path=f"{TENANT_A}/doc_fail.pdf",
        original_filename="doc_fail.pdf",
        mime_type="application/pdf",
        file_size_bytes=1000,
        file_checksum=checksum,
        status="queued",
        provider="mock",
        model_id="mock-v1",
        course_id=COURSE_A1,
    )
    created_new = await job_repo.create_job(new_job)
    assert created_new.id == new_jid
    assert created_new.status == "queued"


# ==============================================================================
# 18. Deduplicación por Content Hash en Lote de Borradores
# ==============================================================================


@pytest.mark.asyncio
async def test_batch_draft_deduplication(db_pool):
    """Verify batch containing duplicate questions with the same content hash is cleanly deduplicated."""
    job_repo = PostgresJobRepository(db_pool)
    draft_repo = PostgresDraftRepository(db_pool)
    jid = str(uuid.uuid4())

    await job_repo.create_job(
        ContentGenerationJobRecord(
            id=jid,
            tenant_id=TENANT_A,
            created_by=TEACHER_A,
            storage_bucket="teacher-materials",
            storage_path=f"{TENANT_A}/dup_batch.pdf",
            original_filename="dup_batch.pdf",
            mime_type="application/pdf",
            file_size_bytes=1000,
            file_checksum=f"chk_dup_{uuid.uuid4().hex[:12]}",
            status="queued",
            provider="mock",
            model_id="mock-v1",
        )
    )

    base_drafts = make_sample_drafts(2)
    # Intentionally duplicate draft 0 so the batch contains [draft0, draft1, draft0]
    duplicate_batch = [base_drafts[0], base_drafts[1], base_drafts[0]]

    saved = await draft_repo.save_drafts(jid, TENANT_A, duplicate_batch)
    assert len(saved) == 2  # Deduplicated from 3 to 2

    # Query from database to verify only 2 drafts exist
    persisted = await draft_repo.get_drafts_by_job(jid, TENANT_A)
    assert len(persisted) == 2


# ==============================================================================
# 19. Docente sin Cursos Asignados es Bloqueado (403)
# ==============================================================================


@pytest.mark.asyncio
async def test_teacher_with_empty_authorized_courses_blocked(db_pool):
    """Verify teacher with 0 assigned courses is blocked with 403 COURSE_NOT_ASSIGNED."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # Teacher has empty X-Course-Ids
        headers = {
            "X-User-Id": TEACHER_A,
            "X-Tenant-Id": TENANT_A,
            "X-User-Role": "teacher",
            "X-Course-Ids": "",  # Empty assigned courses!
        }
        payload = {
            "storage_path": f"{TENANT_A}/ciencias/doc.pdf",
            "original_filename": "doc.pdf",
            "mime_type": "application/pdf",
            "file_size_bytes": 1024,
            "file_checksum": uuid.uuid4().hex + uuid.uuid4().hex,
            "course_id": COURSE_A1,
        }
        resp = await client.post("/api/v1/content-generation/jobs", json=payload, headers=headers)
        assert resp.status_code == 403
        assert resp.json()["code"] == "COURSE_NOT_ASSIGNED"


# ==============================================================================
# 20. Rechazo de Path Traversal en Storage Path
# ==============================================================================


@pytest.mark.asyncio
async def test_path_traversal_storage_path_rejected(db_pool):
    """Verify storage paths containing path traversal (..) are rejected at REST boundary."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        headers = {
            "X-User-Id": TEACHER_A,
            "X-Tenant-Id": TENANT_A,
            "X-User-Role": "teacher",
            "X-Course-Ids": COURSE_A1,
        }
        payload = {
            "storage_path": f"{TENANT_A}/../../etc/passwd",
            "original_filename": "doc.pdf",
            "mime_type": "application/pdf",
            "file_size_bytes": 1024,
            "file_checksum": uuid.uuid4().hex + uuid.uuid4().hex,
            "course_id": COURSE_A1,
        }
        resp = await client.post("/api/v1/content-generation/jobs", json=payload, headers=headers)
        assert resp.status_code in (400, 403)
        assert resp.json()["code"] == "INVALID_STORAGE_PATH"


# ==============================================================================
# 21. GET /jobs/{id}/drafts con Cross-Tenant Retorna 404
# ==============================================================================


@pytest.mark.asyncio
async def test_cross_tenant_drafts_endpoint_returns_404(db_pool):
    """Verify Tenant B calling GET /jobs/{id}/drafts for Tenant A's job returns 404 JOB_NOT_FOUND."""
    job_repo = PostgresJobRepository(db_pool)
    draft_repo = PostgresDraftRepository(db_pool)
    jid = str(uuid.uuid4())

    await job_repo.create_job(
        ContentGenerationJobRecord(
            id=jid,
            tenant_id=TENANT_A,
            created_by=TEACHER_A,
            storage_bucket="teacher-materials",
            storage_path=f"{TENANT_A}/doc.pdf",
            original_filename="doc.pdf",
            mime_type="application/pdf",
            file_size_bytes=1000,
            file_checksum=f"chk_cross_{uuid.uuid4().hex[:12]}",
            status="queued",
            provider="mock",
            model_id="mock-v1",
        )
    )
    await draft_repo.save_drafts(jid, TENANT_A, make_sample_drafts(2))

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        headers_tenant_b = {
            "X-User-Id": TEACHER_B,
            "X-Tenant-Id": TENANT_B,
            "X-User-Role": "teacher",
        }
        resp = await client.get(f"/api/v1/content-generation/jobs/{jid}/drafts", headers=headers_tenant_b)
        assert resp.status_code == 404
        assert resp.json()["code"] == "JOB_NOT_FOUND"


# ==============================================================================
# 22. Selección de Repositorios en Tiempo de Ejecución (Dependency Injection)
# ==============================================================================


@pytest.mark.asyncio
async def test_in_memory_repository_di_selection(monkeypatch):
    """Verify setting REPOSITORY_BACKEND='memory' resolves to InMemory repositories without DB pool."""
    from app.content_generation.dependencies import (
        get_database_pool,
        get_draft_repository,
        get_job_repository,
        get_storage_client,
        get_unit_of_work,
    )
    from app.content_generation.infrastructure.unit_of_work import InMemoryUnitOfWork
    from app.content_generation.repositories.draft_repository import (
        InMemoryDraftRepository,
    )
    from app.content_generation.repositories.job_repository import InMemoryJobRepository
    from app.content_generation.repositories.storage_client import InMemoryStorageClient
    from app.core.config import settings

    monkeypatch.setattr(settings, "REPOSITORY_BACKEND", "memory")

    pool = await get_database_pool()
    assert pool is None

    job_repo = await get_job_repository(pool=pool)
    assert isinstance(job_repo, InMemoryJobRepository)

    draft_repo = await get_draft_repository(pool=pool)
    assert isinstance(draft_repo, InMemoryDraftRepository)

    uow = await get_unit_of_work(pool=pool, job_repo=job_repo, draft_repo=draft_repo)
    assert isinstance(uow, InMemoryUnitOfWork)

    storage = get_storage_client()
    assert isinstance(storage, InMemoryStorageClient)
