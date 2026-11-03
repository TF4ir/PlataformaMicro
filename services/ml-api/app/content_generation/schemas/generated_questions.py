"""Pydantic v2 schemas for assisted question generation and draft quarantine.

All models strictly enforce extra='forbid' in adherence to ADR-0004 and project contracts.
"""

import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from app.content_generation.exceptions import (
    DuplicateOptionsError,
    EmptyExplanationError,
    EmptyOptionTextError,
    EmptyQuestionTextError,
    InvalidCorrectOptionsCountError,
    InvalidDifficultyError,
    InvalidOptionsCountError,
    InvalidSourceReferenceError,
    SnippetNotFoundError,
    UnprocessedHtmlError,
)
from app.content_generation.schemas.extracted_document import (
    DocumentUnitType,
    ExtractedUnit,
)

HTML_TAG_PATTERN = re.compile(
    r"<\s*/?\s*(?:script|iframe|style|object|embed|svg|applet|meta|link|form|input|button|a|img|div|span|p|body|html)[^>]*>",
    re.IGNORECASE,
)


class QuestionType(StrEnum):
    """Supported question types for curriculum assessment generation."""

    SINGLE_CHOICE = "single_choice"
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"


class BloomTaxonomy(StrEnum):
    """Cognitive levels according to Bloom's Revised Taxonomy."""

    REMEMBER = "remember"
    UNDERSTAND = "understand"
    APPLY = "apply"
    ANALYZE = "analyze"
    EVALUATE = "evaluate"
    CREATE = "create"


class DifficultyLevel(StrEnum):
    """Qualitative difficulty level descriptors."""

    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


DIFFICULTY_NUMERIC_MAP: dict[DifficultyLevel, float] = {
    DifficultyLevel.EASY: 0.300,
    DifficultyLevel.MEDIUM: 0.500,
    DifficultyLevel.HARD: 0.800,
}


class DraftStatus(StrEnum):
    """Lifecycle statuses of question drafts in human-in-the-loop workflow."""

    DRAFT = "draft"
    EDITED = "edited"
    APPROVED = "approved"
    REJECTED = "rejected"


class QuestionOptionDraft(BaseModel):
    """A single option or distractor within a generated question draft."""

    model_config = ConfigDict(extra="forbid")

    text: str = Field(
        ...,
        min_length=1,
        description="Enunciado de la opción o distractor",
    )
    is_correct: bool = Field(
        ...,
        description="Indica si la alternativa representa la respuesta correcta",
    )
    misconception_explanation: str | None = Field(
        default=None,
        description="Explicación del error conceptual que representa el distractor (opcional)",
    )

    @field_validator("text")
    @classmethod
    def validate_text_not_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise EmptyOptionTextError(
                "El texto de la alternativa no puede estar vacío."
            )
        if HTML_TAG_PATTERN.search(stripped):
            raise UnprocessedHtmlError(
                "El texto de la alternativa no puede contener etiquetas HTML sin procesar."
            )
        return stripped

    @model_validator(mode="after")
    def validate_option_semantics(self) -> "QuestionOptionDraft":
        if (
            self.is_correct
            and self.misconception_explanation is not None
            and self.misconception_explanation.strip()
        ):
            raise ValueError(
                "La alternativa correcta no puede incluir una explicación de error conceptual (solo los distractores)."
            )
        if self.misconception_explanation and HTML_TAG_PATTERN.search(
            self.misconception_explanation
        ):
            raise UnprocessedHtmlError(
                "La explicación de error conceptual no puede contener etiquetas HTML sin procesar."
            )
        return self


class QuestionSourceReference(BaseModel):
    """Traceable provenance link to the source document page or slide."""

    model_config = ConfigDict(extra="forbid")

    type: DocumentUnitType = Field(
        ...,
        description="Tipo de unidad documental de procedencia (page para PDF, slide para PPTX)",
    )
    index: int = Field(
        ...,
        ge=1,
        description="Índice 1-indexado de la página o diapositiva",
    )
    snippet: str = Field(
        ...,
        min_length=1,
        description="Fragmento textual citado del documento que fundamenta el reactivo",
    )

    @field_validator("snippet")
    @classmethod
    def validate_snippet_not_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise SnippetNotFoundError(
                "El fragmento citado en la referencia no puede estar vacío."
            )
        return stripped


# Aliases for cross-contract naming alignment with openapi.json and api-contracts.md
QuestionDraftOption = QuestionOptionDraft
QuestionDraftSourceReference = QuestionSourceReference


class GeneratedQuestionDraft(BaseModel):
    """Strictly validated draft question produced by the LLM generation provider."""

    model_config = ConfigDict(extra="forbid")

    suggested_kc_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Nombre sugerido del Knowledge Component",
    )
    question_text: str = Field(
        ...,
        min_length=1,
        description="Enunciado de la pregunta de evaluación",
    )
    question_type: QuestionType = Field(
        default=QuestionType.SINGLE_CHOICE,
        description="Tipo de pregunta (single_choice, multiple_choice, true_false)",
    )
    difficulty: float | DifficultyLevel = Field(
        default=0.500,
        description="Dificultad psicométrica prior (0.0 a 1.0) o nivel cualitativo (easy, medium, hard)",
    )
    bloom_taxonomy: BloomTaxonomy = Field(
        default=BloomTaxonomy.UNDERSTAND,
        description="Nivel cognitivo según taxonomía de Bloom",
    )
    options: list[QuestionOptionDraft] = Field(
        ...,
        description="Lista de alternativas de respuesta",
    )
    explanation: str = Field(
        ...,
        min_length=1,
        description="Fundamentación formativa respaldada por el documento fuente",
    )
    source_references: list[QuestionSourceReference] = Field(
        ...,
        min_length=1,
        description="Referencias documentales con número de página/diapositiva y texto de respaldo",
    )

    @property
    def numeric_difficulty(self) -> float:
        """Derive validated numeric difficulty in [0.0, 1.0] for database persistence."""
        if isinstance(self.difficulty, DifficultyLevel):
            return DIFFICULTY_NUMERIC_MAP[self.difficulty]
        return round(float(self.difficulty), 3)

    def validate_structural_integrity(self) -> "GeneratedQuestionDraft":
        """Strictly validate question schema, distractors, options count, and HTML injection."""
        # 1. Enunciado no vacío tras strip y sin HTML no procesado
        stripped_text = self.question_text.strip()
        if not stripped_text:
            raise EmptyQuestionTextError(
                "El enunciado de la pregunta no puede estar vacío."
            )
        if HTML_TAG_PATTERN.search(stripped_text):
            raise UnprocessedHtmlError(
                "El enunciado de la pregunta no puede contener etiquetas HTML sin procesar."
            )

        # 2. Explicación no vacía tras strip y sin HTML no procesado
        stripped_explanation = self.explanation.strip()
        if not stripped_explanation:
            raise EmptyExplanationError(
                "La explicación formativa no puede estar vacía."
            )
        if HTML_TAG_PATTERN.search(stripped_explanation):
            raise UnprocessedHtmlError(
                "La explicación de la pregunta no puede contener etiquetas HTML sin procesar."
            )

        # 3. KC sugerido no vacío tras strip
        if not self.suggested_kc_name.strip():
            raise EmptyQuestionTextError(
                "El nombre del componente de conocimiento sugerido no puede estar vacío."
            )

        # 4. Validar dificultad numérica si es float
        if isinstance(self.difficulty, (int, float)):
            val = float(self.difficulty)
            if not (0.0 <= val <= 1.0):
                raise InvalidDifficultyError(
                    f"La dificultad numérica debe estar entre 0.0 y 1.0 (recibido: {val}).",
                    details={"difficulty": val},
                )

        # 5. Número de alternativas según el tipo de pregunta
        options_count = len(self.options)
        if self.question_type == QuestionType.SINGLE_CHOICE:
            if not (2 <= options_count <= 5):
                raise InvalidOptionsCountError(
                    f"Las preguntas de opción única deben tener entre 2 y 5 alternativas (recibidas: {options_count}).",
                    details={
                        "options_count": options_count,
                        "question_type": self.question_type.value,
                    },
                )
        elif self.question_type == QuestionType.TRUE_FALSE and options_count != 2:
            raise InvalidOptionsCountError(
                f"Las preguntas de verdadero/falso deben tener exactamente 2 alternativas (recibidas: {options_count}).",
                details={
                    "options_count": options_count,
                    "question_type": self.question_type.value,
                },
            )
        elif self.question_type == QuestionType.MULTIPLE_CHOICE and not (
            2 <= options_count <= 5
        ):
            raise InvalidOptionsCountError(
                f"Las preguntas de opción múltiple deben tener entre 2 y 5 alternativas (recibidas: {options_count}).",
                details={
                    "options_count": options_count,
                    "question_type": self.question_type.value,
                },
            )

        # 6. Número de respuestas correctas y presencia de distractores
        correct_count = sum(1 for opt in self.options if opt.is_correct)
        if self.question_type in (QuestionType.SINGLE_CHOICE, QuestionType.TRUE_FALSE):
            if correct_count != 1:
                raise InvalidCorrectOptionsCountError(
                    f"Las preguntas de tipo '{self.question_type.value}' deben tener exactamente 1 respuesta correcta "
                    f"(recibidas: {correct_count}).",
                    details={
                        "correct_count": correct_count,
                        "question_type": self.question_type.value,
                    },
                )
        elif self.question_type == QuestionType.MULTIPLE_CHOICE:
            if correct_count < 1:
                raise InvalidCorrectOptionsCountError(
                    "Las preguntas de opción múltiple deben tener al menos una alternativa correcta.",
                    details={
                        "correct_count": correct_count,
                        "question_type": self.question_type.value,
                    },
                )
            if correct_count >= options_count:
                raise InvalidCorrectOptionsCountError(
                    "Las preguntas de opción múltiple deben tener al menos un distractor (alternativa incorrecta).",
                    details={
                        "correct_count": correct_count,
                        "options_count": options_count,
                        "question_type": self.question_type.value,
                    },
                )

        # 7. No alternativas duplicadas tras normalización de Unicode NFKC, espacios y mayúsculas
        seen_normalized: set[str] = set()
        for opt in self.options:
            normalized = re.sub(
                r"\s+", " ", unicodedata.normalize("NFKC", opt.text).strip().lower()
            )
            if normalized in seen_normalized:
                raise DuplicateOptionsError(
                    f"Alternativa duplicada detectada: '{opt.text}'.",
                    details={"duplicate_text": opt.text},
                )
            seen_normalized.add(normalized)

        # 8. Validar que los distractores tengan texto
        for opt in self.options:
            if not opt.text.strip():
                raise EmptyOptionTextError(
                    "El texto de la alternativa no puede estar vacío."
                )

        # 9. Al menos una referencia documental
        if not self.source_references:
            raise InvalidSourceReferenceError(
                "La pregunta debe incluir al menos una referencia documental a la fuente."
            )

        return self

    @model_validator(mode="after")
    def _run_pydantic_validators(self) -> "GeneratedQuestionDraft":
        return self.validate_structural_integrity()

    validate_question_integrity = validate_structural_integrity


class GenerationContext(BaseModel):
    """Contextual metadata provided to the question generation provider."""

    model_config = ConfigDict(extra="forbid")

    job_id: str = Field(description="Identificador único del trabajo de generación")
    tenant_id: str = Field(description="Identificador del tenant institucional")
    course_id: str | None = Field(
        default=None, description="ID del curso asociado si aplica"
    )
    unit_id: str | None = Field(
        default=None, description="ID de la unidad curricular si aplica"
    )
    language: str = Field(
        default="es", description="Idioma de generación (por defecto español)"
    )
    target_num_questions: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Número objetivo de preguntas a generar",
    )
    prompt_version: str = Field(default="v1", description="Versión del prompt")
    document_units: list[ExtractedUnit] = Field(
        default_factory=list,
        description="Unidades documentales extraídas (páginas/diapositivas)",
    )
    original_filename: str = Field(
        default="", description="Nombre original del archivo"
    )
    document_type: str = Field(
        default="pdf", description="Tipo de documento (pdf o pptx)"
    )


class LLMGenerationOutput(BaseModel):
    """Structured response returned by a QuestionGenerationProvider."""

    model_config = ConfigDict(extra="forbid")

    provider: str = Field(description="Nombre o identificador del proveedor LLM")
    model_id: str = Field(description="Identificador del modelo utilizado")
    prompt_version: str = Field(default="v1", description="Versión del prompt aplicado")
    questions: list[GeneratedQuestionDraft] = Field(
        description="Lista de borradores de preguntas generados",
    )
    raw_response: str | None = Field(
        default=None,
        description="Respuesta textual cruda del modelo (opcional, para auditoría)",
    )
    token_usage: dict[str, int] | None = Field(
        default=None,
        description="Metadatos de consumo de tokens (opcional)",
    )
    finish_reason: str = Field(
        default="stop",
        description="Motivo de finalización del modelo",
    )


@dataclass
class QuestionDraftRecord:
    """Domain model representing a persisted question draft in PostgreSQL."""

    id: str
    tenant_id: str
    generation_job_id: str
    suggested_kc_name: str
    question_text: str
    explanation: str
    options: list[dict[str, Any]]
    suggested_difficulty: float
    suggested_bloom_level: str
    source_references: list[dict[str, Any]]
    status: str = "draft"
    question_type: str = "single_choice"
    knowledge_component_id: str | None = None
    approved_question_id: str | None = None
    reviewed_by: str | None = None
    reviewed_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    content_hash: str | None = None


def compute_draft_content_hash(
    question_text: str,
    suggested_kc_name: str,
    options: list[dict[str, Any]] | list[QuestionOptionDraft],
) -> str:
    """Calculate deterministic SHA-256 hash for draft idempotency."""
    import hashlib
    import json

    norm_text = question_text.strip().lower()
    norm_kc = suggested_kc_name.strip().lower()
    norm_options: list[dict[str, Any]] = []
    for opt in options:
        if isinstance(opt, QuestionOptionDraft):
            norm_options.append({
                "text": opt.text.strip().lower(),
                "is_correct": opt.is_correct,
            })
        else:
            norm_options.append({
                "text": str(opt.get("text", "")).strip().lower(),
                "is_correct": bool(opt.get("is_correct", False)),
            })
    norm_options.sort(key=lambda o: (o["text"], o["is_correct"]))
    payload = f"{norm_kc}|{norm_text}|{json.dumps(norm_options, sort_keys=True)}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

