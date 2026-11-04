import logging
import time
from typing import Any

from app.content_generation.exceptions import (
    ContentGenerationError,
    GenerationProviderError,
    NoExtractableTextError,
)
from app.content_generation.providers.base import QuestionGenerationProvider
from app.content_generation.providers.cost_calculator import (
    GenerationTelemetry,
    calculate_cost,
)
from app.content_generation.providers.factory import get_llm_provider
from app.content_generation.providers.prompts import PROMPT_VERSION
from app.content_generation.schemas.extracted_document import ExtractedDocument
from app.content_generation.schemas.generated_questions import (
    GeneratedQuestionDraft,
    GenerationContext,
)
from app.content_generation.services.draft_validation_service import (
    DraftValidationService,
)

logger = logging.getLogger(__name__)


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

        start_time = time.monotonic()

        # 1. Generate via provider
        try:
            output = await selected_provider.generate_drafts(
                extracted_text=extracted_text,
                schema=schema,
                context=context,
            )
        except ContentGenerationError:
            latency_ms = (time.monotonic() - start_time) * 1000.0
            telemetry_err = GenerationTelemetry(
                provider=getattr(selected_provider, "provider_name", "unknown"),
                model_id=getattr(selected_provider, "model_id", "unknown"),
                prompt_version=context.prompt_version or PROMPT_VERSION,
                request_id=None,
                input_tokens=None,
                output_tokens=None,
                latency_ms=latency_ms,
                retry_count=0,
                generated_questions=0,
                valid_questions=0,
                failed_validations=0,
                estimated_cost=None,
                generation_status="provider_error",
            )
            logger.error("Content generation provider error: %s", telemetry_err.to_dict())
            raise
        except Exception as e:
            latency_ms = (time.monotonic() - start_time) * 1000.0
            telemetry_err = GenerationTelemetry(
                provider=getattr(selected_provider, "provider_name", "unknown"),
                model_id=getattr(selected_provider, "model_id", "unknown"),
                prompt_version=context.prompt_version or PROMPT_VERSION,
                request_id=None,
                input_tokens=None,
                output_tokens=None,
                latency_ms=latency_ms,
                retry_count=0,
                generated_questions=0,
                valid_questions=0,
                failed_validations=0,
                estimated_cost=None,
                generation_status="provider_error",
            )
            logger.error("Content generation provider error: %s", telemetry_err.to_dict())
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

        # 2. Extract token counts if reported
        in_tokens = None
        out_tokens = None
        cached_tokens = 0
        reasoning_tokens = 0
        if output.token_usage:
            in_tokens = output.token_usage.get("prompt_tokens")
            out_tokens = output.token_usage.get("completion_tokens")
            cached_tokens = output.token_usage.get("cached_tokens", 0)
            reasoning_tokens = output.token_usage.get("reasoning_tokens", 0)

        # 3. Strictly validate against source document
        try:
            validated_drafts = self._validation_service.validate_drafts(
                drafts=output.questions,
                document=document,
            )
        except ContentGenerationError as val_err:
            cost_on_failure = calculate_cost(
                provider=output.provider,
                model_id=output.model_id,
                input_tokens=in_tokens,
                output_tokens=out_tokens,
                generated_questions=len(output.questions),
                valid_questions=0,
                cached_input_tokens=cached_tokens,
                reasoning_tokens=reasoning_tokens,
            )
            telemetry_failure = GenerationTelemetry(
                provider=output.provider,
                model_id=output.model_id,
                prompt_version=output.prompt_version,
                request_id=output.request_id,
                input_tokens=in_tokens,
                output_tokens=out_tokens,
                latency_ms=output.latency_ms or (time.monotonic() - start_time) * 1000.0,
                retry_count=output.retry_count,
                generated_questions=len(output.questions),
                valid_questions=0,
                failed_validations=len(output.questions),
                estimated_cost=cost_on_failure.total_cost_usd,
                generation_status="validation_failed",
            )
            logger.warning("Content generation validation failed: %s (error: %s)", telemetry_failure.to_dict(), val_err.message_safe)
            raise

        cost_breakdown = calculate_cost(
            provider=output.provider,
            model_id=output.model_id,
            input_tokens=in_tokens,
            output_tokens=out_tokens,
            generated_questions=len(output.questions),
            valid_questions=len(validated_drafts),
            cached_input_tokens=cached_tokens,
            reasoning_tokens=reasoning_tokens,
        )
        telemetry_success = GenerationTelemetry(
            provider=output.provider,
            model_id=output.model_id,
            prompt_version=output.prompt_version,
            request_id=output.request_id,
            input_tokens=in_tokens,
            output_tokens=out_tokens,
            latency_ms=output.latency_ms or (time.monotonic() - start_time) * 1000.0,
            retry_count=output.retry_count,
            generated_questions=len(output.questions),
            valid_questions=len(validated_drafts),
            failed_validations=len(output.questions) - len(validated_drafts),
            estimated_cost=cost_breakdown.total_cost_usd,
            generation_status="success",
        )
        logger.info("Content generation validated: %s", telemetry_success.to_dict())

        return validated_drafts
