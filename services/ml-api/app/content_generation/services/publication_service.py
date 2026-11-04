"""Transactional Publication Service for AI-generated Question Drafts.

Implements ADR-0004 & Milestone M3:
- Human-in-the-loop approval: Promotes question drafts in quarantine to canonical questions and options.
- Atomicity: Insertion of canonical question, its options, and draft status update execute in a single ACID transaction.
- Idempotency: Multiple approval calls on the same draft return the previous publication result without duplicating records.
- Concurrency protection: SELECT FOR UPDATE guarantees strict serialization.
- Knowledge Component governance: Requires explicit assignment of an institutional KC; rejects unregistered KCs.
"""

import logging
import re
import unicodedata
import uuid
from datetime import UTC, datetime
from typing import Any

import asyncpg

from app.content_generation.exceptions import (
    ContentGenerationError,
    DraftNotFoundError,
    DuplicateOptionsError,
    EmptyExplanationError,
    EmptyOptionTextError,
    EmptyQuestionTextError,
    InvalidCorrectOptionsCountError,
    InvalidDifficultyError,
    InvalidJobStateTransitionError,
    InvalidOptionsCountError,
    KcAssignmentRequiredError,
    KnowledgeComponentNotFoundError,
    UnprocessedHtmlError,
)
from app.content_generation.infrastructure.postgres_draft_repository import (
    _deserialize_json,
    _row_to_draft,
)
from app.content_generation.repositories.draft_repository import (
    DraftRepositoryProtocol,
    InMemoryDraftRepository,
)
from app.content_generation.repositories.job_repository import (
    JobRepositoryProtocol,
)
from app.content_generation.schemas.generated_questions import (
    HTML_TAG_PATTERN,
    QuestionDraftRecord,
)

logger = logging.getLogger(__name__)


def _validate_draft_content_for_approval(
    question_text: str,
    explanation: str,
    options: list[dict[str, Any]],
    difficulty: float,
) -> None:
    """Validate question structural integrity before promoting to canonical tables."""
    # 1. Enunciado no vacío y sin HTML malicioso
    stripped_text = question_text.strip()
    if not stripped_text:
        raise EmptyQuestionTextError("El enunciado de la pregunta no puede estar vacío.")
    if HTML_TAG_PATTERN.search(stripped_text):
        raise UnprocessedHtmlError("El enunciado contiene etiquetas HTML sin procesar.")

    # 2. Explicación no vacía y sin HTML malicioso
    stripped_explanation = explanation.strip()
    if not stripped_explanation:
        raise EmptyExplanationError("La explicación formativa no puede estar vacía.")
    if HTML_TAG_PATTERN.search(stripped_explanation):
        raise UnprocessedHtmlError("La explicación contiene etiquetas HTML sin procesar.")

    # 3. Dificultad numérica en [0.0, 1.0]
    if not (0.0 <= difficulty <= 1.0):
        raise InvalidDifficultyError(
            f"La dificultad numérica debe estar entre 0.0 y 1.0 (recibido: {difficulty}).",
            details={"difficulty": difficulty},
        )

    # 4. Conteo de alternativas (entre 2 y 6)
    options_count = len(options)
    if not (2 <= options_count <= 6):
        raise InvalidOptionsCountError(
            f"La pregunta debe tener entre 2 y 6 alternativas (recibidas: {options_count}).",
            details={"options_count": options_count},
        )

    # 5. Exactamente una alternativa correcta
    correct_count = sum(1 for opt in options if opt.get("is_correct") is True)
    if correct_count != 1:
        raise InvalidCorrectOptionsCountError(
            f"La pregunta debe tener exactamente 1 respuesta correcta (recibidas: {correct_count}).",
            details={"correct_count": correct_count, "options_count": options_count},
        )

    # 6. Sin alternativas duplicadas tras normalización Unicode NFKC y minúsculas
    seen_normalized: set[str] = set()
    for opt in options:
        raw_text = str(opt.get("text", "")).strip()
        if not raw_text:
            raise EmptyOptionTextError("El texto de la alternativa no puede estar vacío.")
        if HTML_TAG_PATTERN.search(raw_text):
            raise UnprocessedHtmlError("El texto de la alternativa contiene etiquetas HTML sin procesar.")

        normalized = re.sub(
            r"\s+", " ", unicodedata.normalize("NFKC", raw_text).strip().lower()
        )
        if normalized in seen_normalized:
            raise DuplicateOptionsError(
                f"Alternativa duplicada detectada: '{raw_text}'.",
                details={"duplicate_text": raw_text},
            )
        seen_normalized.add(normalized)


class DraftPublicationService:
    """Domain service managing the transactional publication of approved drafts into canonical tables."""

    def __init__(
        self,
        pool: asyncpg.Pool | None,
        job_repository: JobRepositoryProtocol,
        draft_repository: DraftRepositoryProtocol,
    ) -> None:
        self._pool = pool
        self._job_repo = job_repository
        self._draft_repo = draft_repository
        # In-memory canonical store for testing
        self._in_memory_questions: dict[str, dict[str, Any]] = {}
        self._in_memory_options: dict[str, list[dict[str, Any]]] = {}
        self._in_memory_kcs: set[tuple[str, str]] = set()

    def register_in_memory_kc(self, tenant_id: str, kc_id: str) -> None:
        """Register valid KC for in-memory unit tests."""
        self._in_memory_kcs.add((tenant_id, kc_id))

    async def approve_draft(
        self,
        draft_id: str,
        tenant_id: str,
        user_id: str,
        knowledge_component_id: str | None = None,
    ) -> tuple[QuestionDraftRecord, str]:
        """Atomically approve a single draft and publish to canonical questions and options."""
        if self._pool is not None:
            try:
                return await self._approve_draft_postgres(
                    draft_id=draft_id,
                    tenant_id=tenant_id,
                    user_id=user_id,
                    knowledge_component_id=knowledge_component_id,
                )
            except asyncpg.PostgresError as e:
                logger.error("Database transaction error during draft approval: %s", e)
                raise ContentGenerationError(
                    "Error interno en la persistencia durante la aprobación de la pregunta.",
                    code="DATABASE_TRANSACTION_ERROR",
                    status_code=500,
                ) from e
        return await self._approve_draft_in_memory(
            draft_id=draft_id,
            tenant_id=tenant_id,
            user_id=user_id,
            knowledge_component_id=knowledge_component_id,
        )

    async def _approve_draft_postgres(
        self,
        draft_id: str,
        tenant_id: str,
        user_id: str,
        knowledge_component_id: str | None = None,
    ) -> tuple[QuestionDraftRecord, str]:
        """PostgreSQL ACID implementation with SELECT FOR UPDATE row-level locking."""
        assert self._pool is not None
        try:
            did = uuid.UUID(draft_id)
            tid = uuid.UUID(tenant_id)
            uid = uuid.UUID(user_id)
        except ValueError as e:
            raise DraftNotFoundError(f"Identificador inválido: {e}") from e

        async with self._pool.acquire() as conn, conn.transaction():
            # 1. Lock the draft row with SELECT FOR UPDATE to prevent race conditions
            fetch_query = """
            SELECT * FROM question_drafts
            WHERE id = $1::uuid AND tenant_id = $2::uuid
            FOR UPDATE;
            """
            row = await conn.fetchrow(fetch_query, did, tid)
            if not row:
                raise DraftNotFoundError(f"El borrador con ID {draft_id} no fue encontrado.")

            curr_status = row["status"]

            # 2. Idempotency Check: if already approved, return previously published question
            if curr_status == "approved":
                canonical_id = str(row["approved_question_id"])
                logger.info(
                    "Idempotent approval request: draft %s is already approved (canonical question: %s).",
                    draft_id,
                    canonical_id,
                )
                return _row_to_draft(row), canonical_id

            # 3. Guard against approving rejected drafts
            if curr_status == "rejected":
                raise InvalidJobStateTransitionError(
                    "No se puede aprobar un borrador que ya fue descartado.",
                    details={"draft_id": draft_id, "status": curr_status},
                )

            # 4. Resolve and validate Knowledge Component
            resolved_kc_id = knowledge_component_id or (
                str(row["knowledge_component_id"]) if row["knowledge_component_id"] else None
            )
            if not resolved_kc_id:
                raise KcAssignmentRequiredError(
                    "El borrador no tiene un Componente de Conocimiento asignado. "
                    "Por favor asigne un Knowledge Component institucional antes de aprobar.",
                    details={"draft_id": draft_id},
                )

            try:
                kcid = uuid.UUID(resolved_kc_id)
            except ValueError as e:
                raise KnowledgeComponentNotFoundError(
                    f"El formato del Knowledge Component ID '{resolved_kc_id}' es inválido.",
                    details={"knowledge_component_id": resolved_kc_id},
                ) from e

            # Verify KC exists in the same tenant and is active
            kc_check_query = """
            SELECT id, name FROM knowledge_components
            WHERE id = $1::uuid AND tenant_id = $2::uuid AND is_active = true;
            """
            kc_row = await conn.fetchrow(kc_check_query, kcid, tid)
            if not kc_row:
                raise KnowledgeComponentNotFoundError(
                    f"El Componente de Conocimiento {resolved_kc_id} no existe en su institución.",
                    details={"knowledge_component_id": resolved_kc_id, "tenant_id": tenant_id},
                )

            # 5. Extract and validate question content
            q_text = row["question_text"]
            explanation = row["explanation"]
            options_data = _deserialize_json(row["options"])
            diff = float(row["suggested_difficulty"]) if row["suggested_difficulty"] is not None else 0.500

            _validate_draft_content_for_approval(
                question_text=q_text,
                explanation=explanation,
                options=options_data,
                difficulty=diff,
            )

            # 6. Insert canonical question record into `questions`
            canonical_question_id = uuid.uuid4()
            insert_question_query = """
            INSERT INTO questions (
                id, tenant_id, knowledge_component_id, question_text,
                question_type, explanation, difficulty, is_active,
                created_by, source_draft_id
            ) VALUES (
                $1::uuid, $2::uuid, $3::uuid, $4,
                'multiple_choice', $5, $6, true,
                $7::uuid, $8::uuid
            ) RETURNING id;
            """
            await conn.fetchrow(
                insert_question_query,
                canonical_question_id,
                tid,
                kcid,
                q_text,
                explanation,
                diff,
                uid,
                did,
            )

            # 7. Insert options into `question_options`
            insert_option_query = """
            INSERT INTO question_options (
                id, question_id, option_text, is_correct, order_index
            ) VALUES (
                $1::uuid, $2::uuid, $3, $4, $5
            );
            """
            for order_idx, opt in enumerate(options_data, start=1):
                opt_id = uuid.uuid4()
                raw_opt_text = opt.get("text")
                clean_opt_text = str(raw_opt_text).strip() if raw_opt_text is not None else None
                await conn.execute(
                    insert_option_query,
                    opt_id,
                    canonical_question_id,
                    clean_opt_text,
                    bool(opt.get("is_correct", False)),
                    order_idx,
                )

            # 8. Update draft in `question_drafts` to status = 'approved'
            update_draft_query = """
            UPDATE question_drafts
            SET status = 'approved'::draft_status_enum,
                approved_question_id = $3::uuid,
                knowledge_component_id = $4::uuid,
                reviewed_by = $5::uuid,
                reviewed_at = now(),
                updated_at = now()
            WHERE id = $1::uuid AND tenant_id = $2::uuid
            RETURNING *;
            """
            updated_draft_row = await conn.fetchrow(
                update_draft_query,
                did,
                tid,
                canonical_question_id,
                kcid,
                uid,
            )

            if not updated_draft_row:
                raise DraftNotFoundError(f"Error al actualizar el borrador {draft_id}.")

            logger.info(
                "Successfully approved draft %s -> published canonical question %s.",
                draft_id,
                str(canonical_question_id),
            )
            return _row_to_draft(updated_draft_row), str(canonical_question_id)

    async def _approve_draft_in_memory(
        self,
        draft_id: str,
        tenant_id: str,
        user_id: str,
        knowledge_component_id: str | None = None,
    ) -> tuple[QuestionDraftRecord, str]:
        """In-memory implementation for unit testing."""
        if not isinstance(self._draft_repo, InMemoryDraftRepository):
            draft = await self._draft_repo.get_draft_by_id(draft_id, tenant_id)
        else:
            draft = await self._draft_repo.get_draft_by_id(draft_id, tenant_id)

        if not draft:
            raise DraftNotFoundError(f"El borrador con ID {draft_id} no fue encontrado.")

        # Idempotency check
        if draft.status == "approved" and draft.approved_question_id:
            return draft, draft.approved_question_id

        if draft.status == "rejected":
            raise InvalidJobStateTransitionError(
                "No se puede aprobar un borrador que ya fue descartado.",
                details={"draft_id": draft_id, "status": draft.status},
            )

        resolved_kc = knowledge_component_id or draft.knowledge_component_id
        if not resolved_kc:
            raise KcAssignmentRequiredError(
                "El borrador no tiene un Componente de Conocimiento asignado. "
                "Por favor asigne un Knowledge Component institucional antes de aprobar.",
                details={"draft_id": draft_id},
            )

        # Check in-memory KC registration if any KCs are registered
        if self._in_memory_kcs and (tenant_id, resolved_kc) not in self._in_memory_kcs:
            raise KnowledgeComponentNotFoundError(
                f"El Componente de Conocimiento {resolved_kc} no existe en su institución.",
                details={"knowledge_component_id": resolved_kc, "tenant_id": tenant_id},
            )

        _validate_draft_content_for_approval(
            question_text=draft.question_text,
            explanation=draft.explanation,
            options=draft.options,
            difficulty=draft.suggested_difficulty,
        )

        canonical_id = str(uuid.uuid4())
        draft.status = "approved"
        draft.approved_question_id = canonical_id
        draft.knowledge_component_id = resolved_kc
        draft.reviewed_by = user_id
        now = datetime.now(UTC)
        draft.reviewed_at = now
        draft.updated_at = now

        self._in_memory_questions[canonical_id] = {
            "id": canonical_id,
            "tenant_id": tenant_id,
            "knowledge_component_id": resolved_kc,
            "question_text": draft.question_text,
            "explanation": draft.explanation,
            "difficulty": draft.suggested_difficulty,
            "created_by": user_id,
            "source_draft_id": draft_id,
        }
        self._in_memory_options[canonical_id] = [
            {
                "id": str(uuid.uuid4()),
                "question_id": canonical_id,
                "text": opt["text"],
                "is_correct": opt["is_correct"],
                "order_index": i,
            }
            for i, opt in enumerate(draft.options, start=1)
        ]

        return draft, canonical_id

    async def approve_drafts_batch(
        self,
        job_id: str,
        draft_ids: list[str],
        tenant_id: str,
        user_id: str,
        default_kc_id: str | None = None,
    ) -> tuple[int, list[str]]:
        """Batch approve multiple drafts for a given job and tenant."""
        published_ids: list[str] = []
        for did in draft_ids:
            _, pub_id = await self.approve_draft(
                draft_id=did,
                tenant_id=tenant_id,
                user_id=user_id,
                knowledge_component_id=default_kc_id,
            )
            published_ids.append(pub_id)
        return len(published_ids), published_ids
