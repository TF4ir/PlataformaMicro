"""Deterministic in-memory mock provider for assisted question generation.

Produces controlled generation outputs from extracted documents without any network requests,
supporting exhaustive verification of validation pipelines and failure scenarios.
"""

import asyncio
from enum import StrEnum
from typing import Any

from app.content_generation.exceptions import (
    GenerationProviderError,
    UnauthorizedFieldsError,
)
from app.content_generation.schemas.extracted_document import (
    DocumentUnitType,
    ExtractedUnit,
)
from app.content_generation.schemas.generated_questions import (
    BloomTaxonomy,
    GeneratedQuestionDraft,
    GenerationContext,
    LLMGenerationOutput,
    QuestionOptionDraft,
    QuestionSourceReference,
    QuestionType,
)


class MockBehaviorMode(StrEnum):
    """Controlled behavioral modes to verify domain validations and error handling."""

    VALID = "valid"
    NO_CORRECT_OPTION = "no_correct_option"
    MULTIPLE_CORRECT_OPTIONS = "multiple_correct_options"
    DUPLICATE_OPTIONS = "duplicate_options"
    EMPTY_QUESTION_TEXT = "empty_question_text"
    EMPTY_OPTION_TEXT = "empty_option_text"
    EMPTY_EXPLANATION = "empty_explanation"
    INVALID_PAGE_INDEX = "invalid_page_index"
    FABRICATED_SNIPPET = "fabricated_snippet"
    EXTRA_FORBIDDEN_FIELDS = "extra_forbidden_fields"
    PROVIDER_ERROR = "provider_error"


class MockQuestionGenerationProvider:
    """Deterministic mock implementation of QuestionGenerationProvider."""

    provider_name: str = "mock"

    def __init__(
        self,
        model_id: str = "mock-v1",
        behavior_mode: MockBehaviorMode = MockBehaviorMode.VALID,
        custom_questions: list[GeneratedQuestionDraft] | None = None,
        token_usage: dict[str, int] | None = None,
        simulated_latency_seconds: float = 0.0,
    ) -> None:
        self.model_id = model_id
        self.behavior_mode = behavior_mode
        self._custom_questions = custom_questions
        self._token_usage = token_usage
        self._simulated_latency_seconds = simulated_latency_seconds

    def _extract_snippets_from_unit(self, unit: ExtractedUnit) -> str:
        """Extract a deterministic clean substring from unit text to use as proven snippet."""
        text = unit.text.strip()
        if not text:
            return "Texto de referencia no disponible."

        # Find first sentence or line with at least 15 characters
        lines = [line.strip() for line in text.splitlines() if len(line.strip()) >= 15]
        if lines:
            first_line = lines[0]
            # Take up to 80 chars
            return first_line[:80].strip()

        # Fallback to chunk of text
        return text[: min(len(text), 80)].strip()

    def _generate_valid_drafts(
        self,
        context: GenerationContext,
    ) -> list[GeneratedQuestionDraft]:
        """Generate deterministically valid question drafts backed by real document units."""
        units = context.document_units
        if not units:
            # Fallback synthetic unit
            units = [
                ExtractedUnit(
                    type=DocumentUnitType.PAGE
                    if context.document_type == "pdf"
                    else DocumentUnitType.SLIDE,
                    index=1,
                    text="Fundamento curricular básico para generación de reactivos adaptativos.",
                )
            ]

        num_questions = min(context.target_num_questions, max(len(units), 1))
        drafts: list[GeneratedQuestionDraft] = []

        for i in range(num_questions):
            unit = units[i % len(units)]
            snippet = self._extract_snippets_from_unit(unit)
            unit_label = (
                "Página" if unit.type == DocumentUnitType.PAGE else "Diapositiva"
            )

            q = GeneratedQuestionDraft(
                suggested_kc_name=f"Componente Clave {unit.index}: {unit_label} {unit.index}",
                question_text=f"¿Cuál es el postulado principal abordado en la {unit_label.lower()} {unit.index} respecto a '{snippet[:40]}'?",
                question_type=QuestionType.SINGLE_CHOICE,
                difficulty=0.500,
                bloom_taxonomy=BloomTaxonomy.UNDERSTAND,
                options=[
                    QuestionOptionDraft(
                        text=f"Afirmación correcta respaldada por la fuente: {snippet[:50]}",
                        is_correct=True,
                    ),
                    QuestionOptionDraft(
                        text=f"Distractor plausivo A para {unit_label.lower()} {unit.index} sin sustento en el texto",
                        is_correct=False,
                        misconception_explanation="Confusión común entre el postulado principal y una hipótesis descartada.",
                    ),
                    QuestionOptionDraft(
                        text=f"Distractor plausivo B para {unit_label.lower()} {unit.index} basado en interpretación errónea",
                        is_correct=False,
                        misconception_explanation="Error de generalización indebida de los datos presentados.",
                    ),
                    QuestionOptionDraft(
                        text=f"Distractor plausivo C para {unit_label.lower()} {unit.index} con premisa opuesta",
                        is_correct=False,
                        misconception_explanation="Inversión lógica del concepto clave.",
                    ),
                ],
                explanation=f"La respuesta correcta se fundamenta directamente en la {unit_label.lower()} {unit.index}, donde se señala que '{snippet}'.",
                source_references=[
                    QuestionSourceReference(
                        type=unit.type,
                        index=unit.index,
                        snippet=snippet,
                    )
                ],
            )
            drafts.append(q)

        return drafts

    async def generate_drafts(
        self,
        extracted_text: str,
        schema: dict[str, Any] | None,
        context: GenerationContext,
    ) -> LLMGenerationOutput:
        """Asynchronously return deterministic generation output according to configured mode."""
        if self.behavior_mode == MockBehaviorMode.PROVIDER_ERROR:
            raise GenerationProviderError(
                message_safe="El proveedor de generación LLM simulado falló intencionalmente.",
                details={"mode": self.behavior_mode.value},
            )

        if self._custom_questions is not None:
            return LLMGenerationOutput(
                provider=self.provider_name,
                model_id=self.model_id,
                prompt_version=context.prompt_version,
                questions=self._custom_questions,
                finish_reason="stop",
            )

        # Handle adversarial behavior modes for validation testing
        unit_type = (
            DocumentUnitType.PAGE
            if context.document_type == "pdf"
            else DocumentUnitType.SLIDE
        )
        real_index = (
            context.document_units[0].index if context.document_units else 1
        )
        real_snippet = (
            self._extract_snippets_from_unit(context.document_units[0])
            if context.document_units
            else "Texto base de prueba"
        )

        if self.behavior_mode == MockBehaviorMode.NO_CORRECT_OPTION:
            # Model output with zero correct options
            q = GeneratedQuestionDraft.model_construct(
                suggested_kc_name="Concepto sin respuesta correcta",
                question_text="¿Pregunta donde todas las opciones son incorrectas?",
                question_type=QuestionType.SINGLE_CHOICE,
                difficulty=0.500,
                bloom_taxonomy=BloomTaxonomy.UNDERSTAND,
                options=[
                    QuestionOptionDraft.model_construct(
                        text="Distractor 1 sin respuesta correcta",
                        is_correct=False,
                        misconception_explanation="Error conceptual 1",
                    ),
                    QuestionOptionDraft.model_construct(
                        text="Distractor 2 sin respuesta correcta",
                        is_correct=False,
                        misconception_explanation="Error conceptual 2",
                    ),
                ],
                explanation="Explicación pedagógica.",
                source_references=[
                    QuestionSourceReference(
                        type=unit_type,
                        index=real_index,
                        snippet=real_snippet,
                    )
                ],
            )
            return LLMGenerationOutput(
                provider=self.provider_name,
                model_id=self.model_id,
                prompt_version=context.prompt_version,
                questions=[q],
            )

        if self.behavior_mode == MockBehaviorMode.MULTIPLE_CORRECT_OPTIONS:
            # Single-choice question with more than 1 correct option
            q = GeneratedQuestionDraft.model_construct(
                suggested_kc_name="Concepto con múltiples correctas",
                question_text="¿Pregunta de opción única con más de una opción correcta?",
                question_type=QuestionType.SINGLE_CHOICE,
                difficulty=0.500,
                bloom_taxonomy=BloomTaxonomy.UNDERSTAND,
                options=[
                    QuestionOptionDraft.model_construct(
                        text="Respuesta correcta A",
                        is_correct=True,
                    ),
                    QuestionOptionDraft.model_construct(
                        text="Respuesta correcta B duplicada",
                        is_correct=True,
                    ),
                    QuestionOptionDraft.model_construct(
                        text="Distractor regular",
                        is_correct=False,
                        misconception_explanation="Error conceptual",
                    ),
                ],
                explanation="Explicación pedagógica.",
                source_references=[
                    QuestionSourceReference(
                        type=unit_type,
                        index=real_index,
                        snippet=real_snippet,
                    )
                ],
            )
            return LLMGenerationOutput(
                provider=self.provider_name,
                model_id=self.model_id,
                prompt_version=context.prompt_version,
                questions=[q],
            )

        if self.behavior_mode == MockBehaviorMode.DUPLICATE_OPTIONS:
            # Question with duplicate options after normalization
            q = GeneratedQuestionDraft.model_construct(
                suggested_kc_name="Concepto con alternativas duplicadas",
                question_text="¿Pregunta con opciones repetidas tras normalización?",
                question_type=QuestionType.SINGLE_CHOICE,
                difficulty=0.500,
                bloom_taxonomy=BloomTaxonomy.UNDERSTAND,
                options=[
                    QuestionOptionDraft.model_construct(
                        text="Opción duplicada idéntica",
                        is_correct=True,
                    ),
                    QuestionOptionDraft.model_construct(
                        text="  opción   duplicada   idéntica  ",
                        is_correct=False,
                        misconception_explanation="Distractor duplicado",
                    ),
                ],
                explanation="Explicación pedagógica.",
                source_references=[
                    QuestionSourceReference(
                        type=unit_type,
                        index=real_index,
                        snippet=real_snippet,
                    )
                ],
            )
            return LLMGenerationOutput(
                provider=self.provider_name,
                model_id=self.model_id,
                prompt_version=context.prompt_version,
                questions=[q],
            )

        if self.behavior_mode == MockBehaviorMode.EMPTY_QUESTION_TEXT:
            q = GeneratedQuestionDraft.model_construct(
                suggested_kc_name="Concepto con enunciado vacío",
                question_text="   \n   ",
                question_type=QuestionType.SINGLE_CHOICE,
                difficulty=0.500,
                bloom_taxonomy=BloomTaxonomy.UNDERSTAND,
                options=[
                    QuestionOptionDraft.model_construct(
                        text="Opción A",
                        is_correct=True,
                    ),
                    QuestionOptionDraft.model_construct(
                        text="Opción B",
                        is_correct=False,
                    ),
                ],
                explanation="Explicación.",
                source_references=[
                    QuestionSourceReference(
                        type=unit_type,
                        index=real_index,
                        snippet=real_snippet,
                    )
                ],
            )
            return LLMGenerationOutput(
                provider=self.provider_name,
                model_id=self.model_id,
                prompt_version=context.prompt_version,
                questions=[q],
            )

        if self.behavior_mode == MockBehaviorMode.EMPTY_OPTION_TEXT:
            q = GeneratedQuestionDraft.model_construct(
                suggested_kc_name="Concepto con distractor vacío",
                question_text="¿Pregunta con distractor en blanco?",
                question_type=QuestionType.SINGLE_CHOICE,
                difficulty=0.500,
                bloom_taxonomy=BloomTaxonomy.UNDERSTAND,
                options=[
                    QuestionOptionDraft.model_construct(
                        text="Opción correcta",
                        is_correct=True,
                    ),
                    QuestionOptionDraft.model_construct(
                        text="   ",
                        is_correct=False,
                    ),
                ],
                explanation="Explicación.",
                source_references=[
                    QuestionSourceReference(
                        type=unit_type,
                        index=real_index,
                        snippet=real_snippet,
                    )
                ],
            )
            return LLMGenerationOutput(
                provider=self.provider_name,
                model_id=self.model_id,
                prompt_version=context.prompt_version,
                questions=[q],
            )

        if self.behavior_mode == MockBehaviorMode.EMPTY_EXPLANATION:
            q = GeneratedQuestionDraft.model_construct(
                suggested_kc_name="Concepto con explicación vacía",
                question_text="¿Pregunta con explicación en blanco?",
                question_type=QuestionType.SINGLE_CHOICE,
                difficulty=0.500,
                bloom_taxonomy=BloomTaxonomy.UNDERSTAND,
                options=[
                    QuestionOptionDraft.model_construct(
                        text="Opción correcta",
                        is_correct=True,
                    ),
                    QuestionOptionDraft.model_construct(
                        text="Opción incorrecta",
                        is_correct=False,
                    ),
                ],
                explanation="   ",
                source_references=[
                    QuestionSourceReference(
                        type=unit_type,
                        index=real_index,
                        snippet=real_snippet,
                    )
                ],
            )
            return LLMGenerationOutput(
                provider=self.provider_name,
                model_id=self.model_id,
                prompt_version=context.prompt_version,
                questions=[q],
            )

        if self.behavior_mode == MockBehaviorMode.EXTRA_FORBIDDEN_FIELDS:
            # Pydantic extra='forbid' validation test
            raw_payload = {
                "suggested_kc_name": "Concepto Prohibido",
                "question_text": "¿Pregunta con payload contaminado?",
                "question_type": "single_choice",
                "difficulty": 0.5,
                "bloom_taxonomy": "understand",
                "options": [
                    {"text": "Opción A", "is_correct": True},
                    {"text": "Opción B", "is_correct": False},
                ],
                "explanation": "Explicación con campo prohibido.",
                "source_references": [
                    {"type": "page", "index": 1, "snippet": "texto base"}
                ],
                "unauthorized_field": "INJECTED_METADATA_ATTACK",  # Prohibited
            }
            # This should raise validation error when parsed into GeneratedQuestionDraft
            try:
                GeneratedQuestionDraft.model_validate(raw_payload)
            except Exception as e:
                raise UnauthorizedFieldsError(
                    f"El proveedor devolvió campos no autorizados en el JSON: {e}",
                    details={"unauthorized_fields": ["unauthorized_field"]},
                ) from e

        if self.behavior_mode == MockBehaviorMode.INVALID_PAGE_INDEX:
            # Valid question draft but references non-existent page index (e.g. 9999)
            q = GeneratedQuestionDraft(
                suggested_kc_name="Concepto con página inválida",
                question_text="¿Pregunta con índice de procedencia fuera de rango?",
                question_type=QuestionType.SINGLE_CHOICE,
                difficulty=0.500,
                bloom_taxonomy=BloomTaxonomy.UNDERSTAND,
                options=[
                    QuestionOptionDraft(text="Respuesta correcta", is_correct=True),
                    QuestionOptionDraft(text="Distractor A", is_correct=False),
                ],
                explanation="Explicación con referencia fuera de rango.",
                source_references=[
                    QuestionSourceReference(
                        type=unit_type,
                        index=9999,  # Out of bounds!
                        snippet="Fragmento fantasma",
                    )
                ],
            )
            return LLMGenerationOutput(
                provider=self.provider_name,
                model_id=self.model_id,
                prompt_version=context.prompt_version,
                questions=[q],
            )

        if self.behavior_mode == MockBehaviorMode.FABRICATED_SNIPPET:
            # Valid question draft but snippet does not exist anywhere in document
            q = GeneratedQuestionDraft(
                suggested_kc_name="Concepto con fragmento inventado",
                question_text="¿Pregunta cuyo fragmento citado fue alucinado por el modelo?",
                question_type=QuestionType.SINGLE_CHOICE,
                difficulty=0.500,
                bloom_taxonomy=BloomTaxonomy.UNDERSTAND,
                options=[
                    QuestionOptionDraft(text="Respuesta correcta", is_correct=True),
                    QuestionOptionDraft(text="Distractor A", is_correct=False),
                ],
                explanation="Explicación con fragmento inventado.",
                source_references=[
                    QuestionSourceReference(
                        type=unit_type,
                        index=real_index,
                        snippet="ESTE_TEXTO_ES_UNA_ALUCINACION_TOTALMENTE_FANTASMA_QUE_NO_EXISTE_EN_EL_DOCUMENTO",
                    )
                ],
            )
            return LLMGenerationOutput(
                provider=self.provider_name,
                model_id=self.model_id,
                prompt_version=context.prompt_version,
                questions=[q],
            )

        if self._simulated_latency_seconds > 0:
            await asyncio.sleep(self._simulated_latency_seconds)

        # Standard valid generation
        questions = self._generate_valid_drafts(context)
        return LLMGenerationOutput(
            provider=self.provider_name,
            model_id=self.model_id,
            prompt_version=context.prompt_version,
            questions=questions,
            token_usage=self._token_usage,
            finish_reason="stop",
        )

