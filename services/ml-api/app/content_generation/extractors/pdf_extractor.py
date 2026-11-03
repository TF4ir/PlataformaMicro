"""PDF curriculum document extractor using pypdf.

Extracts text preserving page numbers, detects encrypted and corrupt PDFs,
identifies scanned documents that require OCR, and prevents unhandled HTTP 500 errors.
"""

import io
import time

from pypdf import PdfReader
from pypdf.errors import EmptyFileError, FileNotDecryptedError, PdfReadError

from app.content_generation.exceptions import (
    CorruptDocumentError,
    EmptyDocumentError,
    EncryptedDocumentError,
    ExtractionLimitExceededError,
    NoExtractableTextError,
)
from app.content_generation.extractors.base import BaseDocumentExtractor
from app.content_generation.schemas.extracted_document import (
    DocumentType,
    DocumentUnitType,
    ExtractedDocument,
    ExtractedUnit,
    ExtractionMetadata,
)
from app.content_generation.services.document_validation import compute_sha256

MAX_PDF_PAGES: int = 500


class PdfDocumentExtractor(BaseDocumentExtractor):
    """Secure PDF extractor using pypdf."""

    EXTRACTOR_VERSION: str = "1.0"

    def can_handle(self, mime_type: str, filename: str) -> bool:
        """Check if this extractor handles the file based on MIME or extension."""
        return mime_type == "application/pdf" or filename.lower().endswith(".pdf")

    def extract(
        self,
        file_bytes: bytes,
        original_filename: str,
        file_checksum: str | None = None,
        mime_type: str | None = None,
        document_id: str | None = None,
    ) -> ExtractedDocument:
        """Extract text from PDF pages while preserving page indices."""
        start_time = time.perf_counter()

        if not file_bytes:
            raise EmptyDocumentError(
                "El documento PDF no contiene bytes.",
                details={"original_filename": original_filename},
            )

        effective_mime = mime_type or "application/pdf"
        effective_checksum = file_checksum or compute_sha256(file_bytes)

        stream = io.BytesIO(file_bytes)

        try:
            reader = PdfReader(stream)
        except (PdfReadError, EmptyFileError, ValueError, KeyError) as e:
            raise CorruptDocumentError(
                "El documento PDF se encuentra dañado o no pudo ser interpretado.",
                details={"original_filename": original_filename, "error": str(e)},
            )
        except Exception as e:  # noqa: BLE001
            raise CorruptDocumentError(
                "Error de lectura al procesar la estructura del documento PDF.",
                details={
                    "original_filename": original_filename,
                    "error_type": type(e).__name__,
                },
            )

        # Handle encryption
        if reader.is_encrypted:
            try:
                # Attempt empty password decryption in case of default user encryption
                decryption_result = reader.decrypt("")
                if decryption_result == 0:
                    raise EncryptedDocumentError(
                        "El documento PDF está protegido con contraseña o cifrado.",
                        details={"original_filename": original_filename},
                    )
            except EncryptedDocumentError:
                raise
            except Exception as e:  # noqa: BLE001
                raise EncryptedDocumentError(
                    "El documento PDF está cifrado y no pudo ser desbloqueado.",
                    details={"original_filename": original_filename, "error": str(e)},
                )

        try:
            total_pages = len(reader.pages)
        except FileNotDecryptedError:
            raise EncryptedDocumentError(
                "El documento PDF está protegido con contraseña o cifrado.",
                details={"original_filename": original_filename},
            )
        except Exception as e:  # noqa: BLE001
            raise CorruptDocumentError(
                "No se pudo determinar el número de páginas del documento PDF.",
                details={"original_filename": original_filename, "error": str(e)},
            )

        if total_pages == 0:
            raise EmptyDocumentError(
                "El documento PDF no contiene páginas.",
                details={"original_filename": original_filename},
            )

        if total_pages > MAX_PDF_PAGES:
            raise ExtractionLimitExceededError(
                f"El documento PDF contiene {total_pages} páginas, superando el límite permitido de {MAX_PDF_PAGES}.",
                details={"total_pages": total_pages, "limit": MAX_PDF_PAGES},
            )

        units: list[ExtractedUnit] = []
        total_text_length = 0
        warnings: list[str] = []

        for page_idx, page in enumerate(reader.pages, start=1):
            try:
                page_raw_text = page.extract_text() or ""
            except FileNotDecryptedError:
                raise EncryptedDocumentError(
                    "El contenido de la página PDF está protegido con contraseña o cifrado.",
                    details={"original_filename": original_filename, "page": page_idx},
                )
            except Exception as e:  # noqa: BLE001
                warnings.append(
                    f"No se pudo extraer texto de la página {page_idx}: {e!s}"
                )
                page_raw_text = ""

            cleaned_text = page_raw_text.strip()
            if not cleaned_text:
                warnings.append(
                    f"La página {page_idx} no contiene texto extraíble (posible imagen escaneada)."
                )
            char_count = len(cleaned_text)
            word_count = len(cleaned_text.split()) if cleaned_text else 0
            total_text_length += char_count

            # Simple heuristic for tabular content (tabs or multiple column spacing)
            has_tables = "\t" in page_raw_text or (
                "  " in page_raw_text and "\n" in page_raw_text
            )

            units.append(
                ExtractedUnit(
                    type=DocumentUnitType.PAGE,
                    index=page_idx,
                    text=cleaned_text,
                    character_count=char_count,
                    word_count=word_count,
                    has_tables=has_tables,
                )
            )

        elapsed_time = round(time.perf_counter() - start_time, 4)

        # Detect scanned documents without digital text
        if total_text_length == 0:
            raise NoExtractableTextError(
                "No se encontró texto digital extraíble en el documento PDF. "
                "El documento aparenta ser una imagen escaneada que requiere OCR (no disponible en esta fase).",
                details={
                    "original_filename": original_filename,
                    "total_pages": total_pages,
                    "requires_ocr": True,
                },
            )

        metadata = ExtractionMetadata(
            file_size_bytes=len(file_bytes),
            file_checksum=effective_checksum,
            mime_type=effective_mime,
            requires_ocr=False,
            processing_time_seconds=elapsed_time,
            warnings=warnings,
        )

        if document_id:
            return ExtractedDocument(
                document_id=document_id,
                document_type=DocumentType.PDF,
                original_filename=original_filename,
                total_units=total_pages,
                units=units,
                extraction_metadata=metadata,
                extractor_version=self.EXTRACTOR_VERSION,
            )

        return ExtractedDocument(
            document_type=DocumentType.PDF,
            original_filename=original_filename,
            total_units=total_pages,
            units=units,
            extraction_metadata=metadata,
            extractor_version=self.EXTRACTOR_VERSION,
        )
