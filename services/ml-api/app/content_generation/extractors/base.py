"""Base class and interface for format-specific curriculum extractors."""

from abc import ABC, abstractmethod

from app.content_generation.schemas.extracted_document import ExtractedDocument


class BaseDocumentExtractor(ABC):
    """Abstract base class for format-specific document text extractors."""

    EXTRACTOR_VERSION: str = "1.0"

    @abstractmethod
    def can_handle(self, mime_type: str, filename: str) -> bool:
        """Determine whether this extractor can process the given MIME type or filename."""

    @abstractmethod
    def extract(
        self,
        file_bytes: bytes,
        original_filename: str,
        file_checksum: str | None = None,
        mime_type: str | None = None,
        document_id: str | None = None,
    ) -> ExtractedDocument:
        """Extract textual units and metadata from file bytes without leaking secrets or failing unsafely."""
