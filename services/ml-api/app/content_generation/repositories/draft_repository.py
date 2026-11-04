"""Repository abstractions and implementations for question draft quarantine.

Provides draft quarantine persistence adhering to ADR-0004 and the PostgreSQL schema:
- Multi-tenant boundary isolation.
- Idempotency on retry (replaces unreviewed drafts).
- Protection against overwriting teacher-reviewed drafts (edited/approved/rejected).
"""

import uuid
from datetime import UTC, datetime
from typing import Any, Protocol

from app.content_generation.exceptions import (
    ConcurrencyConflictError,
    DraftAlreadyReviewedError,
    DraftNotFoundError,
    EmptyDraftsError,
    InvalidJobStateTransitionError,
)
from app.content_generation.schemas.generated_questions import (
    GeneratedQuestionDraft,
    QuestionDraftRecord,
    compute_draft_content_hash,
)


class DraftRepositoryProtocol(Protocol):
    """Protocol for persisting and retrieving question drafts in quarantine."""

    async def save_drafts(
        self,
        job_id: str,
        tenant_id: str,
        drafts: list[GeneratedQuestionDraft],
    ) -> list[QuestionDraftRecord]:
        """Atomically persist generated drafts for a content generation job."""
        ...

    async def get_drafts_by_job(
        self,
        job_id: str,
        tenant_id: str,
        status: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[QuestionDraftRecord]:
        """Retrieve drafts associated with a specific generation job for a tenant."""
        ...

    async def get_draft_by_id(
        self,
        draft_id: str,
        tenant_id: str,
    ) -> QuestionDraftRecord | None:
        """Retrieve a specific draft by its ID ensuring tenant isolation."""
        ...

    async def update_draft(
        self,
        draft_id: str,
        tenant_id: str,
        reviewed_by: str,
        question_text: str | None = None,
        options: list[dict[str, Any]] | None = None,
        explanation: str | None = None,
        difficulty: float | None = None,
        bloom_taxonomy: str | None = None,
        knowledge_component_id: str | None = None,
        expected_updated_at: datetime | None = None,
    ) -> QuestionDraftRecord:
        """Update an existing draft in 'draft' or 'edited' status, transitioning it to 'edited'."""
        ...

    async def reject_draft(
        self,
        draft_id: str,
        tenant_id: str,
        reviewed_by: str,
        rejection_reason: str | None = None,
    ) -> QuestionDraftRecord:
        """Reject a draft, setting status to 'rejected' and recording audit metadata."""
        ...

    async def delete_unreviewed_drafts_for_job(
        self,
        job_id: str,
        tenant_id: str,
    ) -> int:
        """Delete only unreviewed ('draft') records for a job upon retry."""
        ...


class InMemoryDraftRepository:
    """In-memory draft repository implementation for unit testing and offline execution."""

    def __init__(self) -> None:
        # Key: draft_id (str) -> QuestionDraftRecord
        self._drafts: dict[str, QuestionDraftRecord] = {}

    async def get_draft_by_id(
        self,
        draft_id: str,
        tenant_id: str,
    ) -> QuestionDraftRecord | None:
        """Retrieve draft by ID ensuring tenant isolation."""
        record = self._drafts.get(draft_id)
        if not record or record.tenant_id != tenant_id:
            return None
        return record

    async def get_drafts_by_job(
        self,
        job_id: str,
        tenant_id: str,
        status: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[QuestionDraftRecord]:
        """Retrieve drafts for a given job and tenant, sorted by creation time."""
        results = [
            draft
            for draft in self._drafts.values()
            if draft.generation_job_id == job_id
            and draft.tenant_id == tenant_id
            and (status is None or draft.status == status)
        ]
        results.sort(key=lambda d: d.created_at or datetime.min.replace(tzinfo=UTC))
        start = offset or 0
        if limit is not None:
            return results[start : start + limit]
        return results[start:]

    async def update_draft(
        self,
        draft_id: str,
        tenant_id: str,
        reviewed_by: str,
        question_text: str | None = None,
        options: list[dict[str, Any]] | None = None,
        explanation: str | None = None,
        difficulty: float | None = None,
        bloom_taxonomy: str | None = None,
        knowledge_component_id: str | None = None,
        expected_updated_at: datetime | None = None,
    ) -> QuestionDraftRecord:
        """Update an existing draft in 'draft' or 'edited' status in memory."""
        draft = await self.get_draft_by_id(draft_id, tenant_id)
        if not draft:
            raise DraftNotFoundError(f"El borrador con ID {draft_id} no fue encontrado.")

        if draft.status in ("approved", "rejected"):
            raise InvalidJobStateTransitionError(
                f"No se pueden modificar borradores en estado '{draft.status}'."
            )

        if (
            expected_updated_at
            and draft.updated_at
            and abs((draft.updated_at - expected_updated_at).total_seconds()) > 1.0
        ):
            raise ConcurrencyConflictError(
                "El borrador fue modificado por otro usuario desde su última lectura."
            )

        if question_text is not None:
            draft.question_text = question_text
        if options is not None:
            draft.options = options
        if explanation is not None:
            draft.explanation = explanation
        if difficulty is not None:
            draft.suggested_difficulty = difficulty
        if bloom_taxonomy is not None:
            draft.suggested_bloom_level = bloom_taxonomy
        if knowledge_component_id is not None:
            draft.knowledge_component_id = knowledge_component_id

        draft.status = "edited"
        draft.reviewed_by = reviewed_by
        draft.updated_at = datetime.now(UTC)
        return draft

    async def reject_draft(
        self,
        draft_id: str,
        tenant_id: str,
        reviewed_by: str,
        rejection_reason: str | None = None,
    ) -> QuestionDraftRecord:
        """Reject a draft in memory."""
        draft = await self.get_draft_by_id(draft_id, tenant_id)
        if not draft:
            raise DraftNotFoundError(f"El borrador con ID {draft_id} no fue encontrado.")

        if draft.status == "approved":
            raise InvalidJobStateTransitionError(
                "No se puede descartar un borrador que ya fue aprobado y publicado."
            )

        if draft.status == "rejected":
            return draft

        draft.status = "rejected"
        draft.reviewed_by = reviewed_by
        draft.reviewed_at = datetime.now(UTC)
        draft.rejection_reason = rejection_reason
        draft.updated_at = datetime.now(UTC)
        return draft

    async def delete_unreviewed_drafts_for_job(
        self,
        job_id: str,
        tenant_id: str,
    ) -> int:
        """Delete only drafts in 'draft' status for a job; protects reviewed drafts."""
        existing = await self.get_drafts_by_job(job_id, tenant_id)
        deleted_count = 0
        for draft in existing:
            if draft.status == "draft":
                del self._drafts[draft.id]
                deleted_count += 1
            else:
                raise DraftAlreadyReviewedError(
                    f"No se puede eliminar el borrador {draft.id} porque ya tiene estado '{draft.status}'.",
                    details={"draft_id": draft.id, "status": draft.status},
                )
        return deleted_count

    async def save_drafts(
        self,
        job_id: str,
        tenant_id: str,
        drafts: list[GeneratedQuestionDraft],
    ) -> list[QuestionDraftRecord]:
        """Persist drafts atomically for a job.

        Guarantees:
        - If any draft for this job has been reviewed (status != 'draft'), rejects the operation.
        - Idempotent on retry: if only 'draft' items exist, removes them before inserting new ones.
        - Converts Pydantic models to JSONB-compliant dictionary records.
        """
        if not drafts:
            raise EmptyDraftsError(
                "No se pueden persistir cero borradores para el trabajo de generación.",
                details={"job_id": job_id},
            )

        existing = await self.get_drafts_by_job(job_id, tenant_id)

        # 1. Safeguard human-in-the-loop review work
        for draft in existing:
            if draft.status != "draft":
                raise DraftAlreadyReviewedError(
                    f"No se pueden sobreescribir los borradores del trabajo {job_id} "
                    f"porque el borrador {draft.id} ya se encuentra en estado '{draft.status}'.",
                    details={
                        "job_id": job_id,
                        "draft_id": draft.id,
                        "status": draft.status,
                    },
                )

        # 2. Idempotency cleanup: purge existing unreviewed drafts for this job
        for draft in existing:
            if draft.id in self._drafts:
                del self._drafts[draft.id]

        # 3. Create and store new draft records with batch deduplication
        now = datetime.now(UTC)
        records: list[QuestionDraftRecord] = []
        seen_hashes: set[str] = set()

        for item in drafts:
            c_hash = compute_draft_content_hash(
                item.question_text, item.suggested_kc_name, item.options
            )
            if c_hash in seen_hashes:
                continue
            seen_hashes.add(c_hash)
            draft_id = str(uuid.uuid4())
            record = QuestionDraftRecord(
                id=draft_id,
                tenant_id=tenant_id,
                generation_job_id=job_id,
                suggested_kc_name=item.suggested_kc_name,
                question_text=item.question_text,
                explanation=item.explanation,
                options=[
                    {
                        "text": opt.text,
                        "is_correct": opt.is_correct,
                        **(
                            {"misconception_explanation": opt.misconception_explanation}
                            if opt.misconception_explanation
                            else {}
                        ),
                    }
                    for opt in item.options
                ],
                suggested_difficulty=item.numeric_difficulty,
                suggested_bloom_level=item.bloom_taxonomy.value,
                source_references=[
                    {
                        "type": ref.type.value,
                        "index": ref.index,
                        "snippet": ref.snippet,
                    }
                    for ref in item.source_references
                ],
                status="draft",
                question_type=item.question_type.value,
                knowledge_component_id=None,
                approved_question_id=None,
                reviewed_by=None,
                reviewed_at=None,
                created_at=now,
                updated_at=now,
                content_hash=compute_draft_content_hash(
                    item.question_text, item.suggested_kc_name, item.options
                ),
            )
            self._drafts[draft_id] = record
            records.append(record)

        return records

    def mark_draft_status_for_testing(
        self,
        draft_id: str,
        status: str,
        reviewed_by: str | None = None,
    ) -> None:
        """Helper to simulate teacher review status (edited, approved, rejected) in tests."""
        if draft_id in self._drafts:
            draft = self._drafts[draft_id]
            draft.status = status
            draft.reviewed_by = reviewed_by or "teacher-uuid"
            draft.reviewed_at = datetime.now(UTC)
            draft.updated_at = datetime.now(UTC)
