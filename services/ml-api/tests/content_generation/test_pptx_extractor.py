"""Unit tests for PptxDocumentExtractor."""

import io

import pytest
from pptx import Presentation

from app.content_generation.exceptions import (
    CorruptDocumentError,
    EmptyDocumentError,
    ExtractionLimitExceededError,
    NoExtractableTextError,
)
from app.content_generation.extractors.pptx_extractor import (
    MAX_PPTX_SLIDES,
    PptxDocumentExtractor,
)
from app.content_generation.schemas.extracted_document import (
    DocumentType,
    DocumentUnitType,
)
from tests.content_generation.test_fixtures import (
    build_empty_pptx,
    build_multiline_table_pptx,
    build_valid_pptx,
)


def test_pptx_extractor_can_handle() -> None:
    extractor = PptxDocumentExtractor()
    mime = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    assert extractor.can_handle(mime, "fotosintesis.pptx") is True
    assert extractor.can_handle(mime, "CLASE.PPTX") is True
    assert extractor.can_handle("text/plain", "diapositivas.pptx") is True
    assert extractor.can_handle("text/plain", "diapositivas.pdf") is False


def test_pptx_extractor_valid_multislide() -> None:
    """2 & 10. PPTX válido con varias diapositivas y preservación del índice."""
    slides = [
        "Fase luminosa de la fotosintesis: fotolisis del agua y liberacion de O2.",
        "Fase oscura o Ciclo de Calvin: fijacion del CO2 en moleculas de glucosa.",
        "Factores limitantes: intensidad luminosa, concentracion de CO2 y temperatura.",
    ]
    pptx_bytes = build_valid_pptx(slides, include_table=False)
    extractor = PptxDocumentExtractor()

    doc = extractor.extract(
        file_bytes=pptx_bytes,
        original_filename="ciencias_5to_fotosintesis.pptx",
        file_checksum="dummy_checksum_pptx",
    )

    assert doc.document_type == DocumentType.PPTX
    assert doc.original_filename == "ciencias_5to_fotosintesis.pptx"
    assert doc.total_units == 3
    assert len(doc.units) == 3

    for idx, unit in enumerate(doc.units, start=1):
        assert unit.type == DocumentUnitType.SLIDE
        assert unit.index == idx
        assert unit.character_count > 0
        assert unit.word_count > 0

    assert "fotolisis del agua" in doc.units[0].text
    assert "Ciclo de Calvin" in doc.units[1].text
    assert "Factores limitantes" in doc.units[2].text
    assert doc.extractor_version == "1.0"


def test_pptx_extractor_with_tables() -> None:
    """11. Extracción de tablas compatibles."""
    slides = ["Diapositiva introductoria"]
    pptx_bytes = build_valid_pptx(slides, include_table=True)
    extractor = PptxDocumentExtractor()

    doc = extractor.extract(
        file_bytes=pptx_bytes,
        original_filename="tabla_comparativa.pptx",
        file_checksum="dummy_table_checksum",
    )

    assert doc.total_units == 2
    table_unit = doc.units[1]
    assert table_unit.index == 2
    assert table_unit.has_tables is True
    assert "Membrana Tilacoidal" in table_unit.text
    assert "Ciclo de Calvin" in table_unit.text
    assert "Estroma" in table_unit.text
    assert "|" in table_unit.text  # Pipe-delimited structured representation


def test_pptx_extractor_empty_presentation() -> None:
    """4. PPTX vacío (0 diapositivas) genera EmptyDocumentError."""
    empty_bytes = build_empty_pptx()
    extractor = PptxDocumentExtractor()

    with pytest.raises(EmptyDocumentError) as exc_info:
        extractor.extract(
            file_bytes=empty_bytes,
            original_filename="presentacion_vacia.pptx",
            file_checksum="dummy_empty_pptx",
        )

    assert exc_info.value.code == "EMPTY_DOCUMENT"


def test_pptx_extractor_corrupt_file() -> None:
    """5. Archivo PPTX corrupto genera CorruptDocumentError."""
    corrupt_bytes = b"PK\x03\x04\x14\x00\x00\x00RandomBrokenZipData\xff\xfe"
    extractor = PptxDocumentExtractor()

    with pytest.raises(CorruptDocumentError) as exc_info:
        extractor.extract(
            file_bytes=corrupt_bytes,
            original_filename="corrupt.pptx",
            file_checksum="dummy_corrupt_pptx",
        )

    assert exc_info.value.code == "CORRUPT_DOCUMENT"


def test_pptx_extractor_no_extractable_text() -> None:
    """PPTX con diapositivas en blanco sin texto genera NoExtractableTextError."""
    prs = Presentation()
    # Add blank slide without any shapes
    blank_layout = prs.slide_layouts[6]  # Blank
    prs.slides.add_slide(blank_layout)
    buf = io.BytesIO()
    prs.save(buf)

    extractor = PptxDocumentExtractor()
    with pytest.raises(NoExtractableTextError) as exc_info:
        extractor.extract(
            file_bytes=buf.getvalue(),
            original_filename="blanco.pptx",
            file_checksum="dummy_blank_pptx",
        )

    assert exc_info.value.code == "NO_EXTRACTABLE_TEXT"


def test_pptx_extractor_slide_limit_exceeded() -> None:
    """Defensa ante presentaciones que superan el límite de diapositivas."""
    prs = Presentation()
    blank_layout = prs.slide_layouts[6]
    for _ in range(MAX_PPTX_SLIDES + 2):
        prs.slides.add_slide(blank_layout)
    buf = io.BytesIO()
    prs.save(buf)

    extractor = PptxDocumentExtractor()
    with pytest.raises(ExtractionLimitExceededError) as exc_info:
        extractor.extract(
            file_bytes=buf.getvalue(),
            original_filename="too_many_slides.pptx",
            file_checksum="dummy_limit_pptx",
        )

    assert exc_info.value.code == "EXTRACTION_LIMIT_EXCEEDED"


def test_pptx_extractor_empty_bytes() -> None:
    """Extracción directa con 0 bytes genera EmptyDocumentError."""
    extractor = PptxDocumentExtractor()
    with pytest.raises(EmptyDocumentError) as exc_info:
        extractor.extract(file_bytes=b"", original_filename="vacio.pptx")
    assert exc_info.value.code == "EMPTY_DOCUMENT"


def test_pptx_extractor_auto_checksum() -> None:
    """Calcula automáticamente el checksum SHA-256 si no es provisto."""
    slides = ["Diapositiva para prueba de checksum automatico"]
    pptx_bytes = build_valid_pptx(slides)
    extractor = PptxDocumentExtractor()

    doc = extractor.extract(file_bytes=pptx_bytes, original_filename="slides.pptx")
    assert doc.extraction_metadata is not None
    assert len(doc.extraction_metadata.file_checksum) == 64


def test_pptx_extractor_multiline_table_cells() -> None:
    """Verifica que celdas de tabla con saltos de línea se normalicen a filas Markdown limpias."""
    pptx_bytes = build_multiline_table_pptx()
    extractor = PptxDocumentExtractor()

    doc = extractor.extract(
        file_bytes=pptx_bytes, original_filename="tabla_multilinea.pptx"
    )
    assert doc.total_units == 1
    unit = doc.units[0]
    assert unit.has_tables is True

    # Check that each table row in unit.text is on a single line (no raw newlines within a pipe row)
    lines = [line.strip() for line in unit.text.split("\n") if line.strip()]
    table_lines = [l for l in lines if l.startswith("|") and l.endswith("|")]
    assert len(table_lines) == 2
    # Verify content was preserved and normalized
    assert "Concepto Principal" in table_lines[0]
    assert "Mitocondria (Organelo)" in table_lines[1]
    assert "Generación de ATP mediante fosforilación" in table_lines[1]


def test_pptx_extractor_shape_error_isolation() -> None:
    """Verifica que un error en una forma no aborte la extracción de las demás formas en la misma diapositiva."""
    from unittest.mock import MagicMock

    extractor = PptxDocumentExtractor()

    # Create mock slide with 2 shapes: first raises exception on text_frame, second has valid text
    mock_slide = MagicMock()

    shape_bad = MagicMock()
    # Property that raises when accessed
    type(shape_bad).has_text_frame = property(
        lambda self: (_ for _ in ()).throw(ValueError("Corrupt shape XML"))
    )
    shape_bad.has_table = False

    shape_good = MagicMock()
    shape_good.has_text_frame = True
    shape_good.text_frame.text = "Texto valido de forma sobreviviente"
    shape_good.has_table = False

    mock_slide.shapes = [shape_bad, shape_good]

    mock_prs = MagicMock()
    mock_prs.slides = [mock_slide]

    from unittest.mock import patch

    with patch(
        "app.content_generation.extractors.pptx_extractor.Presentation",
        return_value=mock_prs,
    ):
        doc = extractor.extract(
            file_bytes=b"dummy_bytes_for_mock",
            original_filename="resilience.pptx",
        )

    assert doc.total_units == 1
    assert "Texto valido de forma sobreviviente" in doc.units[0].text
    assert doc.extraction_metadata is not None
    assert len(doc.extraction_metadata.warnings) >= 1
    assert "Corrupt shape XML" in doc.extraction_metadata.warnings[0]
