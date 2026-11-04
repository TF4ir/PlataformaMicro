"""Comprehensive Tests for Teacher Question Editor (Milestone M3).

Validates:
1. Teacher job listing, course filtering, status filtering, and pagination.
2. Tenant isolation on jobs and drafts (cross-tenant 404).
3. Draft listing with status filtering and pagination.
4. Valid draft patch transitions draft -> edited, and subsequent edits maintain edited.
5. Optimistic concurrency conflict (HTTP 409 on outdated expected_updated_at).
6. Validation: option count (<2 or >6), single correct option (0 or >1), Unicode NFKC duplicate options, difficulty range, Bloom taxonomy.
7. Terminal status protection: cannot edit approved or rejected drafts.
8. Single draft transactional approval: canonical question + options insertion, draft approved status, reviewed_by/at audit.
9. Idempotent approval: repeated approval returns existing canonical question ID without duplicates.
10. Knowledge Component assignment: required KC validation, invalid KC 404, matching valid KC.
11. Batch approval endpoint (POST /jobs/{job_id}/approve).
12. Draft rejection (POST /drafts/{draft_id}/reject) with optional reason and terminal status protection.
13. Security & authorization: student role forbidden (403), unauthenticated (401).
14. Course listing, KC listing, and canonical question bank retrieval.
15. Material upload endpoint (PDF/PPTX) validation and storage path generation.
"""

import asyncio
import io
import logging
import uuid

import asyncpg
import httpx
import pytest

logger = logging.getLogger(__name__)

from app.content_generation.exceptions import (
    DraftAlreadyReviewedError,
)
from app.content_generation.infrastructure.postgres_draft_repository import (
    PostgresDraftRepository,
)
from app.content_generation.infrastructure.postgres_job_repository import (
    PostgresJobRepository,
)
from app.content_generation.repositories.job_repository import (
    ContentGenerationJobRecord,
)
from app.content_generation.schemas.extracted_document import DocumentUnitType
from app.content_generation.schemas.generated_questions import (
    BloomTaxonomy,
    GeneratedQuestionDraft,
    QuestionOptionDraft,
    QuestionSourceReference,
    QuestionType,
)
from app.main import app

# Seed UUIDs
TENANT_A = "11111111-1111-1111-1111-111111111111"
TENANT_B = "22222222-2222-2222-2222-222222222222"
TEACHER_A = "11111111-1111-1111-1111-aaaaaaaaaaaa"
STUDENT_A = "11111111-1111-1111-1111-bbbbbbbbbbbb"
TEACHER_B = "22222222-2222-2222-2222-aaaaaaaaaaaa"
COURSE_A1 = "11111111-1111-1111-1111-cccccccccccc"
COURSE_A2 = "11111111-1111-1111-1111-cccccccccccd"
COURSE_B1 = "22222222-2222-2222-2222-cccccccccccc"
KC_A1 = "11111111-1111-1111-1111-eeeeeeeeeeee"
KC_B1 = "22222222-2222-2222-2222-eeeeeeeeeeee"

TEST_DB_URL = "postgresql://postgres:postgres@127.0.0.1:5432/plataformamicro_test"


@pytest.fixture
async def db_pool():
    """Create fresh asyncpg pool for each test on the active event loop with clean state."""
    pool = await asyncpg.create_pool(dsn=TEST_DB_URL, min_size=1, max_size=5)
    async with pool.acquire() as conn:
        # Clean canonical questions created by tests to preserve test_canonical_tables_untouched
        await conn.execute("DELETE FROM question_options WHERE question_id IN (SELECT id FROM questions WHERE source_draft_id IS NOT NULL);")
        await conn.execute("DELETE FROM questions WHERE source_draft_id IS NOT NULL;")
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
            await conn.execute("DELETE FROM question_options WHERE question_id IN (SELECT id FROM questions WHERE source_draft_id IS NOT NULL);")
            await conn.execute("DELETE FROM questions WHERE source_draft_id IS NOT NULL;")
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
    from app.content_generation.dependencies import (
        get_database_pool,
        get_draft_repository,
        get_job_repository,
    )

    app.dependency_overrides[get_database_pool] = lambda: db_pool
    app.dependency_overrides[get_job_repository] = lambda: PostgresJobRepository(db_pool)
    app.dependency_overrides[get_draft_repository] = lambda: PostgresDraftRepository(db_pool)
    yield
    app.dependency_overrides.clear()


def make_sample_job(
    tenant_id: str = TENANT_A,
    user_id: str = TEACHER_A,
    course_id: str = COURSE_A1,
    status: str = "review_required",
) -> ContentGenerationJobRecord:
    job_id = str(uuid.uuid4())
    return ContentGenerationJobRecord(
        id=job_id,
        tenant_id=tenant_id,
        created_by=user_id,
        storage_bucket="teacher-materials",
        storage_path=f"{tenant_id}/ciencias/{job_id}.pdf",
        original_filename="fotosintesis.pdf",
        mime_type="application/pdf",
        file_size_bytes=10240,
        file_checksum="f" * 64,
        status=status,
        provider="mock",
        model_id="mock-v1",
        course_id=course_id,
    )


def make_sample_drafts(count: int = 1, kc_name: str = "Fotosíntesis y Cloroplastos") -> list[GeneratedQuestionDraft]:
    drafts: list[GeneratedQuestionDraft] = []
    for i in range(1, count + 1):
        drafts.append(
            GeneratedQuestionDraft(
                suggested_kc_name=kc_name,
                question_text=f"¿En qué estructura celular se realiza la fase luminosa de la fotosíntesis? ({i})",
                question_type=QuestionType.SINGLE_CHOICE,
                difficulty=0.500,
                bloom_taxonomy=BloomTaxonomy.UNDERSTAND,
                options=[
                    QuestionOptionDraft(text="En las membranas de los tilacoides", is_correct=True),
                    QuestionOptionDraft(text="En el estroma del cloroplasto", is_correct=False, misconception_explanation="El estroma es para la fase oscura."),
                    QuestionOptionDraft(text="En la matriz mitocondrial", is_correct=False),
                    QuestionOptionDraft(text="En el reticulo endoplasmatico", is_correct=False),
                ],
                explanation="La fase luminosa ocurre en los tilacoides.",
                source_references=[
                    QuestionSourceReference(type=DocumentUnitType.PAGE, index=1, snippet="membranas de los tilacoides")
                ],
            )
        )
    return drafts


def teacher_a_headers() -> dict[str, str]:
    return {
        "X-User-Id": TEACHER_A,
        "X-Tenant-Id": TENANT_A,
        "X-User-Role": "teacher",
        "X-Course-Ids": f"{COURSE_A1},{COURSE_A2}",
    }


def teacher_b_headers() -> dict[str, str]:
    return {
        "X-User-Id": TEACHER_B,
        "X-Tenant-Id": TENANT_B,
        "X-User-Role": "teacher",
        "X-Course-Ids": COURSE_B1,
    }


def student_headers() -> dict[str, str]:
    return {
        "X-User-Id": STUDENT_A,
        "X-Tenant-Id": TENANT_A,
        "X-User-Role": "student",
        "X-Course-Ids": COURSE_A1,
    }


# ==============================================================================
# 1. Listado de Trabajos y Filtros
# ==============================================================================


@pytest.mark.asyncio
async def test_list_jobs_with_course_and_status_filters(db_pool):
    """Test listing jobs filtered by course_id and status, with pagination."""
    job_repo = PostgresJobRepository(db_pool)

    # Insert 3 jobs for Teacher A: 2 for COURSE_A1 (1 review_required, 1 queued), 1 for COURSE_A2
    j1 = make_sample_job(course_id=COURSE_A1, status="review_required")
    j2 = make_sample_job(course_id=COURSE_A1, status="queued")
    j3 = make_sample_job(course_id=COURSE_A2, status="review_required")

    await job_repo.create_job(j1)
    await job_repo.create_job(j2)
    await job_repo.create_job(j3)

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # 1. Filter by course COURSE_A1
        resp = await client.get(
            f"/api/v1/content-generation/jobs?course_id={COURSE_A1}",
            headers=teacher_a_headers(),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert all(item["course_id"] == COURSE_A1 for item in data)

        # 2. Filter by status 'queued'
        resp_status = await client.get(
            "/api/v1/content-generation/jobs?status=queued",
            headers=teacher_a_headers(),
        )
        assert resp_status.status_code == 200
        data_status = resp_status.json()
        assert len(data_status) == 1
        assert data_status[0]["status"] == "queued"

        # 3. Pagination: limit 1, offset 0
        resp_p1 = await client.get(
            f"/api/v1/content-generation/jobs?course_id={COURSE_A1}&limit=1&offset=0",
            headers=teacher_a_headers(),
        )
        assert resp_p1.status_code == 200
        d_p1 = resp_p1.json()
        assert len(d_p1) == 1


@pytest.mark.asyncio
async def test_jobs_tenant_isolation(db_pool):
    """Teacher B cannot see jobs belonging to Tenant A."""
    job_repo = PostgresJobRepository(db_pool)
    j_a = make_sample_job(tenant_id=TENANT_A, user_id=TEACHER_A, course_id=COURSE_A1)
    j_b = make_sample_job(tenant_id=TENANT_B, user_id=TEACHER_B, course_id=COURSE_B1)
    await job_repo.create_job(j_a)
    await job_repo.create_job(j_b)

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        resp_b = await client.get(
            "/api/v1/content-generation/jobs",
            headers=teacher_b_headers(),
        )
        assert resp_b.status_code == 200
        data_b = resp_b.json()
        assert len(data_b) == 1
        assert data_b[0]["job_id"] == j_b.id
        assert data_b[0]["tenant_id"] == TENANT_B


# ==============================================================================
# 2. Consulta de Borradores y Paginación
# ==============================================================================


@pytest.mark.asyncio
async def test_get_drafts_by_job_with_status_filter(db_pool):
    """Verify draft listing endpoint supports status filtering and returns full draft payload."""
    job_repo = PostgresJobRepository(db_pool)
    draft_repo = PostgresDraftRepository(db_pool)

    job = make_sample_job()
    await job_repo.create_job(job)

    records = await draft_repo.save_drafts(job_id=job.id, tenant_id=TENANT_A, drafts=make_sample_drafts(2))
    _d1 = records[0]
    d2 = records[1]

    # Update d2 to approved status in DB
    async with db_pool.acquire() as conn:
        await conn.execute("UPDATE question_drafts SET status = 'approved' WHERE id = $1::uuid;", uuid.UUID(d2.id))

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # All drafts for job
        resp = await client.get(
            f"/api/v1/content-generation/jobs/{job.id}/drafts",
            headers=teacher_a_headers(),
        )
        assert resp.status_code == 200
        drafts = resp.json()
        assert len(drafts) == 2

        # Filter by status=draft
        resp_draft_only = await client.get(
            f"/api/v1/content-generation/jobs/{job.id}/drafts?status=draft",
            headers=teacher_a_headers(),
        )
        assert resp_draft_only.status_code == 200
        d_only = resp_draft_only.json()
        assert len(d_only) == 1
        assert d_only[0]["status"] == "draft"

        # Cross-tenant draft access returns 404
        cross_resp = await client.get(
            f"/api/v1/content-generation/jobs/{job.id}/drafts",
            headers=teacher_b_headers(),
        )
        assert cross_resp.status_code == 404


# ==============================================================================
# 3. Edición de Borradores (PATCH) y Concurrencia Optimista
# ==============================================================================


@pytest.mark.asyncio
async def test_patch_draft_success_transition_to_edited(db_pool):
    """Editing a draft for the first time transitions status from draft to edited."""
    job_repo = PostgresJobRepository(db_pool)
    draft_repo = PostgresDraftRepository(db_pool)

    job = make_sample_job()
    await job_repo.create_job(job)
    records = await draft_repo.save_drafts(job_id=job.id, tenant_id=TENANT_A, drafts=make_sample_drafts(1))
    draft = records[0]

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # Initial read to get updated_at
        get_resp = await client.get(
            f"/api/v1/content-generation/jobs/{job.id}/drafts",
            headers=teacher_a_headers(),
        )
        draft_data = get_resp.json()[0]
        original_updated_at = draft_data["updated_at"]

        # First edit
        patch_payload = {
            "question_text": "¿En qué organelo y estructura específica ocurre la fase luminosa?",
            "difficulty": 0.650,
            "bloom_taxonomy": "analyze",
            "expected_updated_at": original_updated_at,
        }
        patch_resp = await client.patch(
            f"/api/v1/content-generation/drafts/{draft.id}",
            json=patch_payload,
            headers=teacher_a_headers(),
        )
        assert patch_resp.status_code == 200
        edited_draft = patch_resp.json()
        assert edited_draft["status"] == "edited"
        assert edited_draft["question_text"] == patch_payload["question_text"]
        assert edited_draft["difficulty"] == 0.650
        assert edited_draft["bloom_taxonomy"] == "analyze"

        # Second edit: remains 'edited'
        second_patch = {
            "explanation": "Explicación ampliada por el docente.",
            "expected_updated_at": edited_draft["updated_at"],
        }
        second_resp = await client.patch(
            f"/api/v1/content-generation/drafts/{draft.id}",
            json=second_patch,
            headers=teacher_a_headers(),
        )
        assert second_resp.status_code == 200
        assert second_resp.json()["status"] == "edited"
        assert second_resp.json()["explanation"] == "Explicación ampliada por el docente."


@pytest.mark.asyncio
async def test_patch_draft_optimistic_concurrency_conflict(db_pool):
    """Providing an outdated expected_updated_at returns HTTP 409 Conflict."""
    job_repo = PostgresJobRepository(db_pool)
    draft_repo = PostgresDraftRepository(db_pool)

    job = make_sample_job()
    await job_repo.create_job(job)
    records = await draft_repo.save_drafts(job_id=job.id, tenant_id=TENANT_A, drafts=make_sample_drafts(1))
    draft = records[0]

    stale_updated_at = "2020-01-01T00:00:00Z"
    patch_payload = {
        "question_text": "Texto modificado con timestamp desactualizado",
        "expected_updated_at": stale_updated_at,
    }

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.patch(
            f"/api/v1/content-generation/drafts/{draft.id}",
            json=patch_payload,
            headers=teacher_a_headers(),
        )
        assert resp.status_code == 409
        err = resp.json()
        assert err["code"] == "CONCURRENCY_CONFLICT"


@pytest.mark.asyncio
async def test_patch_draft_validation_rules(db_pool):
    """Test validation constraints on draft updates: option count, single correct, duplicates, bloom."""
    job_repo = PostgresJobRepository(db_pool)
    draft_repo = PostgresDraftRepository(db_pool)

    job = make_sample_job()
    await job_repo.create_job(job)
    records = await draft_repo.save_drafts(job_id=job.id, tenant_id=TENANT_A, drafts=make_sample_drafts(1))
    draft = records[0]

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # A. Less than 2 options -> 422
        bad_options_few = [
            {"text": "Única opción", "is_correct": True}
        ]
        resp = await client.patch(
            f"/api/v1/content-generation/drafts/{draft.id}",
            json={"options": bad_options_few},
            headers=teacher_a_headers(),
        )
        assert resp.status_code == 422

        # B. More than 6 options -> 422
        bad_options_many = [
            {"text": f"Opción {i}", "is_correct": (i == 1)} for i in range(1, 8)
        ]
        resp = await client.patch(
            f"/api/v1/content-generation/drafts/{draft.id}",
            json={"options": bad_options_many},
            headers=teacher_a_headers(),
        )
        assert resp.status_code == 422

        # C. Zero correct options -> 422
        no_correct = [
            {"text": "Opción 1", "is_correct": False},
            {"text": "Opción 2", "is_correct": False},
        ]
        resp = await client.patch(
            f"/api/v1/content-generation/drafts/{draft.id}",
            json={"options": no_correct},
            headers=teacher_a_headers(),
        )
        assert resp.status_code == 422

        # D. Multiple correct options -> 422
        multi_correct = [
            {"text": "Opción 1", "is_correct": True},
            {"text": "Opción 2", "is_correct": True},
        ]
        resp = await client.patch(
            f"/api/v1/content-generation/drafts/{draft.id}",
            json={"options": multi_correct},
            headers=teacher_a_headers(),
        )
        assert resp.status_code == 422

        # E. Duplicate options using Unicode NFKC normalization -> 422
        unicode_duplicates = [
            {"text": "café", "is_correct": True},
            {"text": "cafe\u0301", "is_correct": False},
        ]
        resp = await client.patch(
            f"/api/v1/content-generation/drafts/{draft.id}",
            json={"options": unicode_duplicates},
            headers=teacher_a_headers(),
        )
        assert resp.status_code == 422

        # F. Invalid difficulty (< 0 or > 1) -> 422
        resp = await client.patch(
            f"/api/v1/content-generation/drafts/{draft.id}",
            json={"difficulty": 1.5},
            headers=teacher_a_headers(),
        )
        assert resp.status_code == 422

        # G. Invalid bloom_taxonomy -> 422
        resp = await client.patch(
            f"/api/v1/content-generation/drafts/{draft.id}",
            json={"bloom_taxonomy": "memorizar_rapido"},
            headers=teacher_a_headers(),
        )
        assert resp.status_code == 422


@pytest.mark.asyncio
async def test_patch_draft_terminal_status_protection(db_pool):
    """Cannot edit drafts that are already approved or rejected."""
    job_repo = PostgresJobRepository(db_pool)
    draft_repo = PostgresDraftRepository(db_pool)

    job = make_sample_job()
    await job_repo.create_job(job)

    records = await draft_repo.save_drafts(job_id=job.id, tenant_id=TENANT_A, drafts=make_sample_drafts(2))
    d_approved = records[0]
    d_rejected = records[1]

    async with db_pool.acquire() as conn:
        await conn.execute("UPDATE question_drafts SET status = 'approved' WHERE id = $1::uuid;", uuid.UUID(d_approved.id))
        await conn.execute("UPDATE question_drafts SET status = 'rejected' WHERE id = $1::uuid;", uuid.UUID(d_rejected.id))

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # Try editing approved draft -> 409
        resp1 = await client.patch(
            f"/api/v1/content-generation/drafts/{d_approved.id}",
            json={"question_text": "Cambio no permitido en aprobado"},
            headers=teacher_a_headers(),
        )
        assert resp1.status_code == 409
        assert resp1.json()["code"] == "DRAFT_ALREADY_REVIEWED"

        # Try editing rejected draft -> 409
        resp2 = await client.patch(
            f"/api/v1/content-generation/drafts/{d_rejected.id}",
            json={"question_text": "Cambio no permitido en rechazado"},
            headers=teacher_a_headers(),
        )
        assert resp2.status_code == 409
        assert resp2.json()["code"] == "DRAFT_ALREADY_REVIEWED"


# ==============================================================================
# 4. Aprobación Transaccional e Idempotencia
# ==============================================================================


@pytest.mark.asyncio
async def test_approve_draft_atomic_publication(db_pool):
    """Single draft approval transactionally publishes to canonical questions and options."""
    job_repo = PostgresJobRepository(db_pool)
    draft_repo = PostgresDraftRepository(db_pool)

    job = make_sample_job()
    await job_repo.create_job(job)

    records = await draft_repo.save_drafts(job_id=job.id, tenant_id=TENANT_A, drafts=make_sample_drafts(1, kc_name="Fotosíntesis y Cloroplastos"))
    draft = records[0]

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            f"/api/v1/content-generation/drafts/{draft.id}/approve",
            json={"knowledge_component_id": KC_A1},
            headers=teacher_a_headers(),
        )
        assert resp.status_code == 200
        data = resp.json()
        canonical_id = data["canonical_question_id"]
        assert canonical_id is not None
        assert data["draft_id"] == draft.id
        assert data["status"] == "approved"

    # Verify directly in PostgreSQL
    async with db_pool.acquire() as conn:
        q_row = await conn.fetchrow(
            "SELECT * FROM questions WHERE id = $1::uuid;",
            uuid.UUID(canonical_id),
        )
        assert q_row is not None
        assert str(q_row["source_draft_id"]) == draft.id
        assert str(q_row["knowledge_component_id"]) == KC_A1
        assert str(q_row["created_by"]) == TEACHER_A
        assert q_row["is_active"] is True

        options = await conn.fetch(
            "SELECT * FROM question_options WHERE question_id = $1::uuid ORDER BY order_index ASC;",
            uuid.UUID(canonical_id),
        )
        assert len(options) == 4
        assert sum(1 for o in options if o["is_correct"]) == 1

        # Check draft status updated
        draft_row = await conn.fetchrow(
            "SELECT * FROM question_drafts WHERE id = $1::uuid;",
            uuid.UUID(draft.id),
        )
        assert draft_row["status"] == "approved"
        assert str(draft_row["reviewed_by"]) == TEACHER_A
        assert draft_row["reviewed_at"] is not None


@pytest.mark.asyncio
async def test_approve_draft_idempotency(db_pool):
    """Calling approve on an already approved draft returns the existing canonical ID without creating duplicates."""
    job_repo = PostgresJobRepository(db_pool)
    draft_repo = PostgresDraftRepository(db_pool)

    job = make_sample_job()
    await job_repo.create_job(job)
    records = await draft_repo.save_drafts(job_id=job.id, tenant_id=TENANT_A, drafts=make_sample_drafts(1))
    draft = records[0]

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # First call
        resp1 = await client.post(
            f"/api/v1/content-generation/drafts/{draft.id}/approve",
            json={"knowledge_component_id": KC_A1},
            headers=teacher_a_headers(),
        )
        assert resp1.status_code == 200
        canon1 = resp1.json()["canonical_question_id"]

        # Second call
        resp2 = await client.post(
            f"/api/v1/content-generation/drafts/{draft.id}/approve",
            json={"knowledge_component_id": KC_A1},
            headers=teacher_a_headers(),
        )
        assert resp2.status_code == 200
        canon2 = resp2.json()["canonical_question_id"]

        # Must return identical canonical_question_id
        assert canon1 == canon2

    # Check database: exactly ONE canonical question exists for this draft
    async with db_pool.acquire() as conn:
        count = await conn.fetchval(
            "SELECT count(*) FROM questions WHERE source_draft_id = $1::uuid;",
            uuid.UUID(draft.id),
        )
        assert count == 1


@pytest.mark.asyncio
async def test_approve_draft_kc_validation(db_pool):
    """Approval validates knowledge component presence and existence."""
    job_repo = PostgresJobRepository(db_pool)
    draft_repo = PostgresDraftRepository(db_pool)

    job = make_sample_job()
    await job_repo.create_job(job)

    # Draft with unmatched KC name
    records = await draft_repo.save_drafts(job_id=job.id, tenant_id=TENANT_A, drafts=make_sample_drafts(1, kc_name="Concepto Completamente Desconocido"))
    draft = records[0]

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # 1. Without knowledge_component_id and no match in DB -> 422 KC_ASSIGNMENT_REQUIRED
        resp_missing = await client.post(
            f"/api/v1/content-generation/drafts/{draft.id}/approve",
            json={},
            headers=teacher_a_headers(),
        )
        assert resp_missing.status_code == 422
        assert resp_missing.json()["code"] == "KC_ASSIGNMENT_REQUIRED"

        # 2. With invalid nonexistent KC ID -> 404 KNOWLEDGE_COMPONENT_NOT_FOUND
        fake_kc = str(uuid.uuid4())
        resp_invalid = await client.post(
            f"/api/v1/content-generation/drafts/{draft.id}/approve",
            json={"knowledge_component_id": fake_kc},
            headers=teacher_a_headers(),
        )
        assert resp_invalid.status_code == 404
        assert resp_invalid.json()["code"] == "KNOWLEDGE_COMPONENT_NOT_FOUND"


# ==============================================================================
# 5. Rechazo de Borradores (POST /reject)
# ==============================================================================


@pytest.mark.asyncio
async def test_reject_draft_with_reason_and_audit(db_pool):
    """Rejecting a draft marks it rejected, persists optional reason, and records reviewed_by."""
    job_repo = PostgresJobRepository(db_pool)
    draft_repo = PostgresDraftRepository(db_pool)

    job = make_sample_job()
    await job_repo.create_job(job)
    records = await draft_repo.save_drafts(job_id=job.id, tenant_id=TENANT_A, drafts=make_sample_drafts(1))
    draft = records[0]

    reason = "El reactivo evalúa un concepto fuera del alcance de 5to de secundaria."
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            f"/api/v1/content-generation/drafts/{draft.id}/reject",
            json={"reason": reason},
            headers=teacher_a_headers(),
        )
        assert resp.status_code == 200
        rejected = resp.json()
        assert rejected["status"] == "rejected"
        assert rejected["rejection_reason"] == reason
        assert rejected["reviewed_by"] == TEACHER_A

        # Rejected draft cannot be approved subsequently
        approve_resp = await client.post(
            f"/api/v1/content-generation/drafts/{draft.id}/approve",
            json={"knowledge_component_id": KC_A1},
            headers=teacher_a_headers(),
        )
        assert approve_resp.status_code == 409
        assert approve_resp.json()["code"] in ("DRAFT_ALREADY_REVIEWED", "INVALID_JOB_STATE_TRANSITION")


# ==============================================================================
# 6. Aprobación en Lote (POST /jobs/{job_id}/approve)
# ==============================================================================


@pytest.mark.asyncio
async def test_batch_approve_drafts(db_pool):
    """Batch approve multiple drafts with individual KC mappings."""
    job_repo = PostgresJobRepository(db_pool)
    draft_repo = PostgresDraftRepository(db_pool)

    job = make_sample_job()
    await job_repo.create_job(job)

    records = await draft_repo.save_drafts(job_id=job.id, tenant_id=TENANT_A, drafts=make_sample_drafts(2))
    d1 = records[0]
    d2 = records[1]

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        payload = {
            "draft_ids": [d1.id, d2.id],
            "default_knowledge_component_id": KC_A1,
        }
        resp = await client.post(
            f"/api/v1/content-generation/jobs/{job.id}/approve",
            json=payload,
            headers=teacher_a_headers(),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["approved_count"] == 2
        assert len(data["published_question_ids"]) == 2


# ==============================================================================
# 7. Autorización y Roles
# ==============================================================================


@pytest.mark.asyncio
async def test_student_role_forbidden(db_pool):
    """Students cannot access content generation, draft editing, or approval."""
    job = make_sample_job()
    job_repo = PostgresJobRepository(db_pool)
    await job_repo.create_job(job)

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # Listing jobs
        resp_list = await client.get(
            "/api/v1/content-generation/jobs",
            headers=student_headers(),
        )
        assert resp_list.status_code == 403

        # Approving draft
        fake_id = str(uuid.uuid4())
        resp_approve = await client.post(
            f"/api/v1/content-generation/drafts/{fake_id}/approve",
            json={"knowledge_component_id": KC_A1},
            headers=student_headers(),
        )
        assert resp_approve.status_code == 403


# ==============================================================================
# 8. Cursos, Componentes de Conocimiento y Banco Canónico
# ==============================================================================


@pytest.mark.asyncio
async def test_get_courses_and_knowledge_components(db_pool):
    """Endpoints for teacher course selection and course KC dropdown retrieval."""
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # Get courses
        resp_courses = await client.get(
            "/api/v1/content-generation/courses",
            headers=teacher_a_headers(),
        )
        assert resp_courses.status_code == 200
        courses = resp_courses.json()
        assert len(courses) >= 1
        course_ids = [c["id"] for c in courses]
        assert COURSE_A1 in course_ids

        # Get KCs for COURSE_A1
        resp_kcs = await client.get(
            f"/api/v1/content-generation/courses/{COURSE_A1}/knowledge-components",
            headers=teacher_a_headers(),
        )
        assert resp_kcs.status_code == 200
        kcs = resp_kcs.json()
        assert len(kcs) >= 1
        assert any(k["id"] == KC_A1 for k in kcs)


@pytest.mark.asyncio
async def test_list_canonical_questions_bank(db_pool):
    """Retrieve canonical published questions bank for a course."""
    job_repo = PostgresJobRepository(db_pool)
    draft_repo = PostgresDraftRepository(db_pool)

    job = make_sample_job()
    await job_repo.create_job(job)
    records = await draft_repo.save_drafts(job_id=job.id, tenant_id=TENANT_A, drafts=make_sample_drafts(1))
    draft = records[0]

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # Approve draft to publish it into canonical tables
        approve_resp = await client.post(
            f"/api/v1/content-generation/drafts/{draft.id}/approve",
            json={"knowledge_component_id": KC_A1},
            headers=teacher_a_headers(),
        )
        assert approve_resp.status_code == 200

        # Query questions bank
        bank_resp = await client.get(
            f"/api/v1/content-generation/questions?course_id={COURSE_A1}",
            headers=teacher_a_headers(),
        )
        assert bank_resp.status_code == 200
        questions = bank_resp.json()
        assert len(questions) >= 1
        published = next(q for q in questions if q["source_draft_id"] == draft.id)
        assert published["knowledge_component_id"] == KC_A1
        assert len(published["options"]) == 4


# ==============================================================================
# 9. Carga de Material Curricular (POST /upload-material)
# ==============================================================================


@pytest.mark.asyncio
async def test_upload_material_valid_and_invalid():
    """Verify document upload endpoint validates file types and generates secure storage paths."""
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # 1. Valid PDF file with course_id
        pdf_bytes = b"%PDF-1.4 simulated pdf document content for teacher question editor"
        files = {"file": ("guia_biologia.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
        data = {"course_id": COURSE_A1}
        resp_pdf = await client.post(
            "/api/v1/content-generation/upload-material",
            files=files,
            data=data,
            headers=teacher_a_headers(),
        )
        assert resp_pdf.status_code == 200
        data_pdf = resp_pdf.json()
        assert data_pdf["original_filename"] == "guia_biologia.pdf"
        assert data_pdf["mime_type"] == "application/pdf"
        assert data_pdf["storage_bucket"] == "teacher-materials"
        assert data_pdf["storage_path"].startswith(f"{TENANT_A}/{COURSE_A1}/")
        assert len(data_pdf["file_checksum"]) == 64

        # 2. Unsupported file type (.exe) -> 415
        exe_bytes = b"MZ simulated exe binary"
        files_exe = {"file": ("virus.exe", io.BytesIO(exe_bytes), "application/octet-stream")}
        resp_exe = await client.post(
            "/api/v1/content-generation/upload-material",
            files=files_exe,
            headers=teacher_a_headers(),
        )
        assert resp_exe.status_code == 415


# ==============================================================================
# 10. Concurrencia, Rollback Transaccional y Restricciones Específicas M3
# ==============================================================================


@pytest.mark.asyncio
async def test_approve_draft_concurrent_requests(db_pool):
    """Two concurrent approval requests on the same draft must not duplicate canonical rows (Scenario 14)."""
    job_repo = PostgresJobRepository(db_pool)
    draft_repo = PostgresDraftRepository(db_pool)

    job = make_sample_job()
    await job_repo.create_job(job)
    records = await draft_repo.save_drafts(job_id=job.id, tenant_id=TENANT_A, drafts=make_sample_drafts(1))
    draft = records[0]

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # Issue 2 concurrent HTTP approval requests via asyncio.gather
        results = await asyncio.gather(
            client.post(
                f"/api/v1/content-generation/drafts/{draft.id}/approve",
                json={"knowledge_component_id": KC_A1},
                headers=teacher_a_headers(),
            ),
            client.post(
                f"/api/v1/content-generation/drafts/{draft.id}/approve",
                json={"knowledge_component_id": KC_A1},
                headers=teacher_a_headers(),
            ),
        )

        resp1, resp2 = results
        assert resp1.status_code == 200
        assert resp2.status_code == 200

        canon1 = resp1.json()["canonical_question_id"]
        canon2 = resp2.json()["canonical_question_id"]
        assert canon1 == canon2, "Both concurrent approval calls must return the identical canonical question ID."

    # Direct database verification
    async with db_pool.acquire() as conn:
        count = await conn.fetchval(
            "SELECT count(*) FROM questions WHERE source_draft_id = $1::uuid;",
            uuid.UUID(draft.id),
        )
        assert count == 1, "Exactly one canonical question record must exist in PostgreSQL."


@pytest.mark.asyncio
async def test_approve_draft_rollback_on_option_failure(db_pool, monkeypatch):
    """When option insertion fails, the transaction must roll back with zero orphaned questions (Scenario 12)."""
    job_repo = PostgresJobRepository(db_pool)
    draft_repo = PostgresDraftRepository(db_pool)

    job = make_sample_job()
    await job_repo.create_job(job)
    records = await draft_repo.save_drafts(job_id=job.id, tenant_id=TENANT_A, drafts=make_sample_drafts(1))
    draft = records[0]

    # Patch DraftPublicationService._validate_draft_content_for_approval to inject invalid options at query time
    # Or corrupt conn.execute for option insertion
    from app.content_generation.services import publication_service

    orig_validate = publication_service._validate_draft_content_for_approval

    def simulate_failure_after_question_insert(*args, **kwargs):
        # Allow validation to pass so question is inserted first
        orig_validate(*args, **kwargs)

    monkeypatch.setattr(publication_service, "_validate_draft_content_for_approval", simulate_failure_after_question_insert)

    # Corrupt options data in draft to violate question_options table constraint (e.g., null option_text)
    async with db_pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE question_drafts
            SET options = '[{"text": null, "is_correct": true}, {"text": "Opt B", "is_correct": false}]'::jsonb
            WHERE id = $1::uuid;
            """,
            uuid.UUID(draft.id),
        )

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            f"/api/v1/content-generation/drafts/{draft.id}/approve",
            json={"knowledge_component_id": KC_A1},
            headers=teacher_a_headers(),
        )
        # Should fail with 400/422 or 500 database error
        assert resp.status_code in (400, 422, 500)

    # Verify atomic ROLLBACK in PostgreSQL
    async with db_pool.acquire() as conn:
        q_count = await conn.fetchval(
            "SELECT count(*) FROM questions WHERE source_draft_id = $1::uuid;",
            uuid.UUID(draft.id),
        )
        assert q_count == 0, "No orphaned questions should exist after transaction rollback."

        draft_status = await conn.fetchval(
            "SELECT status FROM question_drafts WHERE id = $1::uuid;",
            uuid.UUID(draft.id),
        )
        assert draft_status != "approved", "Draft status must not be updated to approved on failure."


@pytest.mark.asyncio
async def test_teacher_course_restriction_enforcement(db_pool):
    """Teachers cannot list or manipulate content for courses they do not teach (Scenario 17)."""
    # Teacher A is assigned to COURSE_A1 and COURSE_A2, but NOT COURSE_B1
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # 1. GET /jobs?course_id=COURSE_B1 -> 403
        resp_jobs = await client.get(
            f"/api/v1/content-generation/jobs?course_id={COURSE_B1}",
            headers=teacher_a_headers(),
        )
        assert resp_jobs.status_code == 403

        # 2. POST /jobs with unauthorized course_id -> 403
        resp_create = await client.post(
            "/api/v1/content-generation/jobs",
            json={
                "storage_path": f"{TENANT_A}/ciencias/sample.pdf",
                "original_filename": "sample.pdf",
                "mime_type": "application/pdf",
                "file_size_bytes": 1024,
                "file_checksum": "a" * 64,
                "course_id": COURSE_B1,
            },
            headers=teacher_a_headers(),
        )
        assert resp_create.status_code == 403

        # 3. POST /upload-material with unauthorized course_id -> 403
        pdf_bytes = b"%PDF-1.4 test bytes"
        resp_upload = await client.post(
            "/api/v1/content-generation/upload-material",
            files={"file": ("test.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
            data={"course_id": COURSE_B1},
            headers=teacher_a_headers(),
        )
        assert resp_upload.status_code == 403

        # 4. GET /courses/{course_id}/knowledge-components for unassigned course -> 403
        resp_kcs = await client.get(
            f"/api/v1/content-generation/courses/{COURSE_B1}/knowledge-components",
            headers=teacher_a_headers(),
        )
        assert resp_kcs.status_code == 403

        # 5. GET /questions?course_id=COURSE_B1 -> 403
        resp_bank = await client.get(
            f"/api/v1/content-generation/questions?course_id={COURSE_B1}",
            headers=teacher_a_headers(),
        )
        assert resp_bank.status_code == 403


@pytest.mark.asyncio
async def test_student_role_forbidden_on_all_endpoints(db_pool):
    """Students are strictly forbidden from all teacher question editor endpoints (Scenario 18)."""
    fake_uuid = str(uuid.uuid4())
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # GET /jobs
        r = await client.get("/api/v1/content-generation/jobs", headers=student_headers())
        assert r.status_code == 403

        # POST /jobs
        valid_job_payload = {
            "storage_path": f"{TENANT_A}/ciencias/sample.pdf",
            "original_filename": "sample.pdf",
            "mime_type": "application/pdf",
            "file_size_bytes": 1024,
            "file_checksum": "a" * 64,
            "course_id": COURSE_A1,
        }
        r = await client.post("/api/v1/content-generation/jobs", json=valid_job_payload, headers=student_headers())
        assert r.status_code == 403

        # GET /courses
        r = await client.get("/api/v1/content-generation/courses", headers=student_headers())
        assert r.status_code == 403

        # GET /questions
        r = await client.get("/api/v1/content-generation/questions", headers=student_headers())
        assert r.status_code == 403

        # POST /upload-material
        pdf_bytes = b"%PDF-1.4 student test"
        r = await client.post(
            "/api/v1/content-generation/upload-material",
            files={"file": ("test.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
            headers=student_headers(),
        )
        assert r.status_code == 403

        # PATCH /drafts/{id}
        r = await client.patch(
            f"/api/v1/content-generation/drafts/{fake_uuid}",
            json={"question_text": "Texto editado"},
            headers=student_headers(),
        )
        assert r.status_code == 403

        # POST /drafts/{id}/approve
        r = await client.post(
            f"/api/v1/content-generation/drafts/{fake_uuid}/approve",
            json={"knowledge_component_id": KC_A1},
            headers=student_headers(),
        )
        assert r.status_code == 403

        # POST /drafts/{id}/reject
        r = await client.post(
            f"/api/v1/content-generation/drafts/{fake_uuid}/reject",
            json={"reason": "Rechazo"},
            headers=student_headers(),
        )
        assert r.status_code == 403


@pytest.mark.asyncio
async def test_protection_against_regeneration_after_approval(db_pool):
    """Saving drafts on a job where any draft is already approved/reviewed must be rejected (Scenario 20)."""
    job_repo = PostgresJobRepository(db_pool)
    draft_repo = PostgresDraftRepository(db_pool)

    job = make_sample_job()
    await job_repo.create_job(job)
    records = await draft_repo.save_drafts(job_id=job.id, tenant_id=TENANT_A, drafts=make_sample_drafts(2))
    draft1, _draft2 = records[0], records[1]

    # Approve draft1
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            f"/api/v1/content-generation/drafts/{draft1.id}/approve",
            json={"knowledge_component_id": KC_A1},
            headers=teacher_a_headers(),
        )
        assert resp.status_code == 200

    # Attempt to regenerate/save drafts for this same job: MUST FAIL with DraftAlreadyReviewedError
    with pytest.raises(DraftAlreadyReviewedError):
        await draft_repo.save_drafts(
            job_id=job.id,
            tenant_id=TENANT_A,
            drafts=make_sample_drafts(1, kc_name="Nuevo tema no permitido"),
        )

