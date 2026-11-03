"""Question generation service delegating to provider and enforcing validation.

Bridges the LLM generation provider and the domain validation service, ensuring
no invalid or hallucinated questions proceed toward persistence.
"""

from typing import Any

from app.content_generation.exceptions import (
    ContentGenerationError,
    GenerationProviderError,
    NoExtractableTextError,
)
from app.content_generation.providers.base import QuestionGenerationProvider
from app.content_generation.providers.factory import get_llm_provider
from app.content_generation.schemas.extracted_document import ExtractedDocument
from app.content_generation.schemas.generated_questions import (
    GeneratedQuestionDraft,
    GenerationContext,
)
from app.content_generation.services.draft_validation_service import (
    DraftValidationService,
)


class QuestionGenerationService:
    """Service coordinating question draft generation from extracted documents."""

    def __init__(
        self,
        provider: QuestionGenerationProvider | None = None,
        validation_service: DraftValidationService | None = None,
    ) -> None:
        self._provider = provider
        self._validation_service = validation_service or DraftValidationService()

    def _prepare_extracted_text(self, document: ExtractedDocument) -> str:
        """Combine and label document unit texts for provider context."""
        parts: list[str] = []
        for unit in document.units:
            unit_name = "Página" if unit.type.value == "page" else "Diapositiva"
            header = f"--- [{unit_name} {unit.index}] ---"
            parts.append(f"{header}\n{unit.text.strip()}")
        return "\n\n".join(parts)

    async def generate_and_validate(
        self,
        document: ExtractedDocument,
        context: GenerationContext,
        provider: QuestionGenerationProvider | None = None,
        schema: dict[str, Any] | None = None,
    ) -> list[GeneratedQuestionDraft]:
        """Generate question drafts via provider and strictly validate structural and provenance rules.

        Args:
            document: Extracted curriculum document with structured units.
            context: Contextual parameters (job_id, tenant_id, target count, etc.).
            provider: Optional explicit provider. If None, uses configured default or factory.
            schema: Optional schema or output specification for the LLM.

        Returns:
            List of strictly validated GeneratedQuestionDraft objects.

        Raises:
            NoExtractableTextError: If the document has zero units.
            GenerationProviderError: If the provider fails.
            DraftValidationError: If any draft violates schema or document provenance.
        """
        if not document.units or document.total_units == 0:
            raise NoExtractableTextError(
                "El documento no contiene texto ni unidades para generar preguntas."
            )

        # Ensure context carries document units and document type
        context.document_units = document.units
        context.document_type = document.document_type.value

        selected_provider = provider or self._provider or get_llm_provider()

        extracted_text = self._prepare_extracted_text(document)

        # 1. Generate via provider
        try:
            output = await selected_provider.generate_drafts(
                extracted_text=extracted_text,
                schema=schema,
                context=context,
            )
        except ContentGenerationError:
            raise
        except Exception as e:
            raise GenerationProviderError(
                message_safe="Error en la comunicación o procesamiento de respuesta del proveedor de generación.",
                code="GENERATION_PROVIDER_ERROR",
                details={"job_id": context.job_id, "error_type": type(e).__name__},
            ) from e

        if not output.questions:
            raise GenerationProviderError(
                "El proveedor no generó ninguna pregunta de evaluación para el material proporcionado.",
                details={"job_id": context.job_id},
            )

        # 2. Strictly validate against source document
        validated_drafts = self._validation_service.validate_drafts(
            drafts=output.questions,
            document=document,
        )

        return validated_drafts
