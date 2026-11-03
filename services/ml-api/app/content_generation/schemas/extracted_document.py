"""Pydantic v2 schemas for extracted document representations.

All models strictly enforce extra='forbid' to satisfy architectural contracts.
"""

import uuid
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class DocumentType(StrEnum):
    """Supported document types for curriculum content extraction."""

    PDF = "pdf"
    PPTX = "pptx"


class DocumentUnitType(StrEnum):
    """Unit of provenance for extracted document fragments."""

    PAGE = "page"
    SLIDE = "slide"


class ExtractedUnit(BaseModel):
    """A single page or slide of extracted curriculum content."""

    model_config = ConfigDict(extra="forbid")

    type: DocumentUnitType = Field(
        description="Type of source unit: page for PDF, slide for PPTX"
    )
    index: int = Field(
        ge=1, description="1-indexed sequence number of the original page or slide"
    )
    text: str = Field(description="Extracted clean text content from the page or slide")
    character_count: int = Field(
        default=0, ge=0, description="Total character count in the unit text"
    )
    word_count: int = Field(
        default=0, ge=0, description="Total word count in the unit text"
    )
    has_tables: bool = Field(
        default=False,
        description="Flag indicating whether tabular data was detected and extracted",
    )

    @model_validator(mode="before")
    @classmethod
    def populate_counts(cls, data: Any) -> Any:
        """Automatically derive character and word counts from text if omitted."""
        if isinstance(data, dict):
            text = data.get("text", "")
            if isinstance(text, str):
                if "character_count" not in data:
                    data["character_count"] = len(text)
                if "word_count" not in data:
                    data["word_count"] = len(text.split())
        return data


class ExtractionMetadata(BaseModel):
    """Technical and diagnostic metadata about the extraction execution."""

    model_config = ConfigDict(extra="forbid")

    file_size_bytes: int = Field(
        ge=1,
        le=31457280,
        description="Size of the raw document file in bytes (up to 30 MB)",
    )
    file_checksum: str = Field(
        description="SHA-256 cryptographic digest of the source file bytes"
    )
    mime_type: str = Field(description="Verified MIME type of the document")
    requires_ocr: bool = Field(
        default=False,
        description="Diagnostic flag indicating if digital text was absent and OCR is required",
    )
    processing_time_seconds: float = Field(
        ge=0.0, description="Wall-clock time taken for validation and extraction"
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Diagnostic warnings encountered during extraction without failing",
    )
    extracted_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="UTC timestamp of extraction completion",
    )


class ExtractedDocument(BaseModel):
    """Normalized structured output of the document extraction engine."""

    model_config = ConfigDict(extra="forbid")

    document_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique identifier for the extracted document instance",
    )
    document_type: DocumentType = Field(
        description="Document format type (pdf or pptx)"
    )
    original_filename: str = Field(
        default="document",
        min_length=1,
        max_length=255,
        description="Original name of the uploaded material file",
    )
    total_units: int = Field(
        ge=0, description="Total count of pages (PDF) or slides (PPTX) processed"
    )
    units: list[ExtractedUnit] = Field(
        default_factory=list,
        description="Ordered list of extracted content units preserving original sequence",
    )
    extraction_metadata: ExtractionMetadata | None = Field(
        default=None,
        description="Technical provenance and telemetry of the extraction process",
    )
    extractor_version: str = Field(
        default="1.0", description="Semantic version of the document extraction engine"
    )
