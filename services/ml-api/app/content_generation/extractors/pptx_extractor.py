"""PPTX curriculum document extractor using python-pptx.

Extracts slide text, shapes, and tables while preserving slide sequence.
Explicitly documents limitations: speaker notes, animations, media, and images
are omitted in this phase.
"""

import io
import time

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE

from app.content_generation.exceptions import (
    CorruptDocumentError,
    EmptyDocumentError,
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

MAX_PPTX_SLIDES: int = 500


class PptxDocumentExtractor(BaseDocumentExtractor):
    """Secure PPTX presentation extractor.

    Architecture and Limitations:
    - Extracts ordered slide content from shapes and tabular structures.
    - Preserves exact 1-indexed slide numbering.
    - Ignored by design in this version: speaker notes, animations, embedded audio/video,
      and graphic raster images without text.
    """

    EXTRACTOR_VERSION: str = "1.0"

    def can_handle(self, mime_type: str, filename: str) -> bool:
        """Check if this extractor handles the file based on MIME or extension."""
        return (
            mime_type
            == "application/vnd.openxmlformats-officedocument.presentationml.presentation"
            or filename.lower().endswith(".pptx")
        )

    def extract(
        self,
        file_bytes: bytes,
        original_filename: str,
        file_checksum: str | None = None,
        mime_type: str | None = None,
        document_id: str | None = None,
    ) -> ExtractedDocument:
        """Extract ordered slide text and tables from PPTX presentation."""
        start_time = time.perf_counter()

        if not file_bytes:
            raise EmptyDocumentError(
                "La presentación PPTX no contiene bytes.",
                details={"original_filename": original_filename},
            )

        effective_mime = (
            mime_type
            or "application/vnd.openxmlformats-officedocument.presentationml.presentation"
        )
        effective_checksum = file_checksum or compute_sha256(file_bytes)

        stream = io.BytesIO(file_bytes)

        try:
            presentation = Presentation(stream)
        except Exception as e:  # noqa: BLE001
            raise CorruptDocumentError(
                "La presentación PPTX se encuentra dañada o no pudo ser interpretada por el motor OpenXML.",
                details={"original_filename": original_filename, "error": str(e)},
            )

        try:
            slides = list(presentation.slides)
            total_slides = len(slides)
        except Exception as e:  # noqa: BLE001
            raise CorruptDocumentError(
                "No se pudo acceder a las diapositivas de la presentación PPTX.",
                details={"original_filename": original_filename, "error": str(e)},
            )

        if total_slides == 0:
            raise EmptyDocumentError(
                "La presentación PPTX no contiene diapositivas.",
                details={"original_filename": original_filename},
            )

        if total_slides > MAX_PPTX_SLIDES:
            raise ExtractionLimitExceededError(
                f"La presentación PPTX contiene {total_slides} diapositivas, superando el límite permitido de {MAX_PPTX_SLIDES}.",
                details={"total_slides": total_slides, "limit": MAX_PPTX_SLIDES},
            )

        units: list[ExtractedUnit] = []
        total_text_length = 0
        warnings: list[str] = []

        for slide_idx, slide in enumerate(slides, start=1):
            slide_fragments: list[str] = []
            has_tables_on_slide = False

            # Isolate shape extraction errors so one corrupted shape does not drop the rest of the slide
            for shape in slide.shapes:
                try:
                    if self._extract_shape_text(shape, slide_fragments):
                        has_tables_on_slide = True
                except Exception as e:  # noqa: BLE001
                    warnings.append(
                        f"Error parcial al extraer forma en la diapositiva {slide_idx}: {e!s}"
                    )

            slide_text = "\n\n".join(slide_fragments).strip()
            char_count = len(slide_text)
            word_count = len(slide_text.split()) if slide_text else 0
            total_text_length += char_count

            units.append(
                ExtractedUnit(
                    type=DocumentUnitType.SLIDE,
                    index=slide_idx,
                    text=slide_text,
                    character_count=char_count,
                    word_count=word_count,
                    has_tables=has_tables_on_slide,
                )
            )

        elapsed_time = round(time.perf_counter() - start_time, 4)

        if total_text_length == 0:
            raise NoExtractableTextError(
                "No se encontró texto digital extraíble en la presentación PPTX. "
                "Todas las diapositivas se encuentran vacías o contienen únicamente imágenes no textuales.",
                details={
                    "original_filename": original_filename,
                    "total_slides": total_slides,
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
                document_type=DocumentType.PPTX,
                original_filename=original_filename,
                total_units=total_slides,
                units=units,
                extraction_metadata=metadata,
                extractor_version=self.EXTRACTOR_VERSION,
            )

        return ExtractedDocument(
            document_type=DocumentType.PPTX,
            original_filename=original_filename,
            total_units=total_slides,
            units=units,
            extraction_metadata=metadata,
            extractor_version=self.EXTRACTOR_VERSION,
        )

    def _extract_shape_text(self, shape: object, fragments: list[str]) -> bool:
        """Extract text from shapes and tables recursively.

        Returns True if tabular content was detected.
        """
        has_table = False

        # 1. Standard text frame (titles, subtitles, body shapes)
        if getattr(shape, "has_text_frame", False):
            text_frame = getattr(shape, "text_frame", None)
            if text_frame and text_frame.text:
                cleaned = text_frame.text.strip()
                if cleaned:
                    fragments.append(cleaned)

        # 2. Tabular shapes
        if getattr(shape, "has_table", False):
            table = getattr(shape, "table", None)
            if table:
                has_table = True
                for row in table.rows:
                    row_cells: list[str] = []
                    for cell in row.cells:
                        raw_cell = cell.text if cell and cell.text else ""
                        cell_val = " ".join(raw_cell.split()).replace("|", "\\|")
                        row_cells.append(cell_val)
                    row_line = " | ".join(row_cells)
                    if row_line.replace("|", "").replace("\\", "").strip():
                        fragments.append(f"| {row_line} |")

        # 3. Recursive extraction for grouped shapes
        shape_type = getattr(shape, "shape_type", None)
        if shape_type == MSO_SHAPE_TYPE.GROUP or hasattr(shape, "shapes"):
            child_shapes = getattr(shape, "shapes", [])
            for child in child_shapes:
                if self._extract_shape_text(child, fragments):
                    has_table = True

        return has_table
