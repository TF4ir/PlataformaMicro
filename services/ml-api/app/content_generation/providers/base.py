"""Abstract provider protocol for assisted question generation.

Defines the decoupled QuestionGenerationProvider interface in strict adherence
to ADR-0004 (Aislamiento del Módulo de Generación Asistida de Contenido).
"""

from typing import Any, Protocol, runtime_checkable

from app.content_generation.schemas.generated_questions import (
    GenerationContext,
    LLMGenerationOutput,
)


@runtime_checkable
class QuestionGenerationProvider(Protocol):
    """Protocol defining the asynchronous contract for question generation providers.

    All LLM providers (mock, OpenAI, Vertex AI, Anthropic, vLLM) must satisfy this interface.
    """

    provider_name: str
    model_id: str

    async def generate_drafts(
        self,
        extracted_text: str,
        schema: dict[str, Any] | None,
        context: GenerationContext,
    ) -> LLMGenerationOutput:
        """Asynchronously generate structured question drafts from extracted curriculum text.

        Args:
            extracted_text: Cleaned, extracted textual content of the curriculum material.
            schema: Optional JSON schema or constraints dictionary for structured generation.
            context: Contextual execution parameters (job_id, tenant_id, units provenance, etc.).

        Returns:
            LLMGenerationOutput containing validated question drafts and execution metadata.
        """
        ...
