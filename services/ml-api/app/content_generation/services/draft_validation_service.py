"""Domain service for validating question drafts and verifying source provenance against documents.

Enforces structural question constraints, distractor quality, and documentary provenance
in compliance with Milestone M2.2 requirements and ADR-0004.
"""

import re
import unicodedata

from app.content_generation.exceptions import (
    InvalidSourceReferenceError,
    NoExtractableTextError,
    SnippetNotFoundError,
)
from app.content_generation.schemas.extracted_document import (
    DocumentType,
    DocumentUnitType,
    ExtractedDocument,
    ExtractedUnit,
)
from app.content_generation.schemas.generated_questions import (
    GeneratedQuestionDraft,
    QuestionSourceReference,
)


def normalize_snippet_text(text: str) -> str:
    """Apply controlled text normalization for faithful snippet matching.

    - Decomposes and recomposes Unicode via NFKC (normalizing quotes, dashes, spaces).
    - Removes invisible zero-width characters and soft hyphens (\xad, \u200b-\u200d, \ufeff).
    - Collapses all whitespace sequences (newlines, tabs, multiple spaces) into a single space.
    - Converts to lower-case for case-insensitive provenance verification.
    """
    if not text:
        return ""
    # Unicode canonical normalization
    norm = unicodedata.normalize("NFKC", text)
    # Remove soft hyphens and invisible zero-width formatting characters
    norm = re.sub(r"[\xad\u200b\u200c\u200d\ufeff]", "", norm)
    # Collapse all whitespace characters to a single space
    norm = re.sub(r"\s+", " ", norm)
    return norm.strip().lower()


class DraftValidationService:
    """Service validating question drafts against the actual extracted curriculum document."""

    def validate_reference_against_document(
        self,
        reference: QuestionSourceReference,
        document: ExtractedDocument,
        unit_map: dict[int, ExtractedUnit],
    ) -> None:
        """Validate that a single source reference belongs to the document and its snippet exists.

        Args:
            reference: The source reference to check.
            document: The extracted document instance.
            unit_map: Mapping of 1-indexed unit sequence numbers to ExtractedUnit objects.

        Raises:
            InvalidSourceReferenceError: If reference type does not match or index is out of bounds.
            SnippetNotFoundError: If the cited snippet does not exist in the source unit text.
        """
        # 1. Verify unit type alignment (PDF -> page, PPTX -> slide)
        expected_unit_type = (
            DocumentUnitType.PAGE
            if document.document_type == DocumentType.PDF
            else DocumentUnitType.SLIDE
        )
        if reference.type != expected_unit_type:
            raise InvalidSourceReferenceError(
                f"El tipo de referencia '{reference.type.value}' no coincide con el tipo de documento "
                f"'{document.document_type.value}' (se esperaba '{expected_unit_type.value}').",
                details={
                    "reference_type": reference.type.value,
                    "expected_type": expected_unit_type.value,
                    "document_type": document.document_type.value,
                },
            )

        # 2. Verify reference index exists in the document
        if reference.index not in unit_map:
            raise InvalidSourceReferenceError(
                f"La referencia señala a la unidad con índice {reference.index}, "
                f"pero el documento solo contiene {document.total_units} {expected_unit_type.value}s.",
                details={
                    "reference_index": reference.index,
                    "total_units": document.total_units,
                    "unit_type": expected_unit_type.value,
                },
            )

        unit = unit_map[reference.index]

        # 3. Controlled normalization and substring verification of the snippet
        normalized_snippet = normalize_snippet_text(reference.snippet)
        normalized_unit_text = normalize_snippet_text(unit.text)

        if not normalized_snippet:
            raise SnippetNotFoundError(
                "El fragmento citado en la referencia está vacío o contiene solo espacios.",
                details={"reference_index": reference.index},
            )

        if normalized_snippet not in normalized_unit_text:
            raise SnippetNotFoundError(
                f"El fragmento citado en la {reference.type.value} {reference.index} no fue encontrado "
                "en el texto original del documento tras normalización controlada.",
                details={
                    "unit_index": reference.index,
                    "unit_type": reference.type.value,
                    "snippet_sample": reference.snippet[:80],
                },
            )

    def validate_draft(
        self,
        draft: GeneratedQuestionDraft,
        document: ExtractedDocument,
        unit_map: dict[int, ExtractedUnit],
    ) -> GeneratedQuestionDraft:
        """Validate an individual question draft against document provenance and schema rules.

        Args:
            draft: The generated question draft.
            document: Extracted document used as input.
            unit_map: Mapping of unit index to ExtractedUnit.

        Returns:
            The validated GeneratedQuestionDraft.
        """
        # Strictly enforce structural question rules (enunciado, options count, exactly 1 correct,
        # unique options, distractor content, explanation, HTML sanitization, extra='forbid')
        draft.validate_structural_integrity()

        # Validate each documentary source reference
        for ref in draft.source_references:
            self.validate_reference_against_document(ref, document, unit_map)

        return draft

    def validate_drafts(
        self,
        drafts: list[GeneratedQuestionDraft],
        document: ExtractedDocument,
    ) -> list[GeneratedQuestionDraft]:
        """Validate a collection of question drafts against the extracted document.

        Args:
            drafts: List of generated question drafts.
            document: Extracted document representing source of truth.

        Returns:
            The list of validated drafts.

        Raises:
            NoExtractableTextError: If document contains no units.
            DraftValidationError: If any draft fails structural or reference checks.
        """
        if not document.units or document.total_units == 0:
            raise NoExtractableTextError(
                "No se pueden validar borradores contra un documento sin unidades de texto extraídas."
            )

        unit_map = {unit.index: unit for unit in document.units}

        validated_list: list[GeneratedQuestionDraft] = []
        for draft in drafts:
            validated = self.validate_draft(draft, document, unit_map)
            validated_list.append(validated)

        return validated_list
