"""Unit tests for PdfDocumentExtractor."""

import pytest

from app.content_generation.exceptions import (
    CorruptDocumentError,
    EmptyDocumentError,
    EncryptedDocumentError,
    ExtractionLimitExceededError,
    NoExtractableTextError,
)
from app.content_generation.extractors.pdf_extractor import (
    MAX_PDF_PAGES,
    PdfDocumentExtractor,
)
from app.content_generation.schemas.extracted_document import (
    DocumentType,
    DocumentUnitType,
)
from tests.content_generation.test_fixtures import (
    build_blank_pdf,
    build_encrypted_pdf,
    build_spanish_accented_pdf,
    build_valid_pdf,
)


def test_pdf_extractor_can_handle() -> None:
    extractor = PdfDocumentExtractor()
    assert extractor.can_handle("application/pdf", "biologia_celular.pdf") is True
    assert extractor.can_handle("application/pdf", "MATERIAL.PDF") is True
    assert extractor.can_handle("text/plain", "notas.pdf") is True
    assert extractor.can_handle("text/plain", "notas.txt") is False


def test_pdf_extractor_valid_multipage() -> None:
    """1. Valid PDF with multiple pages."""
    pages = [
        "Capitulo 1: La celula vegetal y su estructura de membrana",
        "Capitulo 2: Cloroplastos y conversion de energia solar",
        "Capitulo 3: Ciclo de Krebs y fosforilacion oxidativa",
    ]
    pdf_bytes = build_valid_pdf(pages)
    extractor = PdfDocumentExtractor()

    doc = extractor.extract(
        file_bytes=pdf_bytes,
        original_filename="ciencias_5to_celula.pdf",
        file_checksum="dummy_checksum_123",
        mime_type="application/pdf",
    )

    # 10. Preservación del número de página
    assert doc.document_type == DocumentType.PDF
    assert doc.original_filename == "ciencias_5to_celula.pdf"
    assert doc.total_units == 3
    assert len(doc.units) == 3

    for idx, unit in enumerate(doc.units, start=1):
        assert unit.type == DocumentUnitType.PAGE
        assert unit.index == idx
        assert unit.character_count > 0
        assert unit.word_count > 0

    assert "celula vegetal" in doc.units[0].text
    assert "Cloroplastos" in doc.units[1].text
    assert "Ciclo de Krebs" in doc.units[2].text
    assert doc.extraction_metadata is not None
    assert doc.extraction_metadata.requires_ocr is False
    assert doc.extractor_version == "1.0"


def test_pdf_extractor_no_extractable_text_detects_ocr() -> None:
    """3. PDF sin texto extraíble informa requerimiento de OCR."""
    pdf_bytes = build_blank_pdf(num_pages=3)
    extractor = PdfDocumentExtractor()

    with pytest.raises(NoExtractableTextError) as exc_info:
        extractor.extract(
            file_bytes=pdf_bytes,
            original_filename="escaneo_ciencias.pdf",
            file_checksum="dummy_checksum_ocr",
            mime_type="application/pdf",
        )

    err = exc_info.value
    assert err.code == "NO_EXTRACTABLE_TEXT"
    assert err.details.get("requires_ocr") is True
    assert err.details.get("total_pages") == 3
    assert "OCR" in err.message_safe


def test_pdf_extractor_encrypted_document() -> None:
    """6. PDF cifrado genera error controlado sin HTTP 500."""
    pdf_bytes = build_encrypted_pdf(password="secret_school_key")
    extractor = PdfDocumentExtractor()

    with pytest.raises(EncryptedDocumentError) as exc_info:
        extractor.extract(
            file_bytes=pdf_bytes,
            original_filename="evaluacion_protegida.pdf",
            file_checksum="dummy_checksum_enc",
            mime_type="application/pdf",
        )

    err = exc_info.value
    assert err.code == "ENCRYPTED_DOCUMENT"
    assert (
        "cifrado" in err.message_safe.lower() or "protegido" in err.message_safe.lower()
    )


def test_pdf_extractor_corrupt_file() -> None:
    """5. Archivo corrupto genera CorruptDocumentError."""
    corrupt_bytes = b"%PDF-1.4\nGarbage binary data corrupted stream\x00\xff\xfe"
    extractor = PdfDocumentExtractor()

    with pytest.raises(CorruptDocumentError) as exc_info:
        extractor.extract(
            file_bytes=corrupt_bytes,
            original_filename="corrupt_ciencias.pdf",
            file_checksum="dummy_checksum_corrupt",
            mime_type="application/pdf",
        )

    assert exc_info.value.code == "CORRUPT_DOCUMENT"


def test_pdf_extractor_empty_pages() -> None:
    """PDF con 0 páginas genera EmptyDocumentError."""
    import io

    from pypdf import PdfWriter

    writer = PdfWriter()
    buf = io.BytesIO()
    writer.write(buf)

    extractor = PdfDocumentExtractor()
    with pytest.raises(EmptyDocumentError) as exc_info:
        extractor.extract(
            file_bytes=buf.getvalue(),
            original_filename="empty.pdf",
            file_checksum="dummy_empty",
        )

    assert exc_info.value.code == "EMPTY_DOCUMENT"


def test_pdf_extractor_page_limit_defense() -> None:
    """Defensa ante PDFs excesivamente grandes que superan el límite de páginas."""
    import io

    from pypdf import PdfWriter

    writer = PdfWriter()
    for _ in range(MAX_PDF_PAGES + 5):
        writer.add_blank_page(width=100, height=100)
    buf = io.BytesIO()
    writer.write(buf)

    extractor = PdfDocumentExtractor()
    with pytest.raises(ExtractionLimitExceededError) as exc_info:
        extractor.extract(
            file_bytes=buf.getvalue(),
            original_filename="huge_book.pdf",
            file_checksum="dummy_huge",
        )

    assert exc_info.value.code == "EXTRACTION_LIMIT_EXCEEDED"


def test_pdf_extractor_empty_bytes() -> None:
    """Extracción directa con 0 bytes genera EmptyDocumentError."""
    extractor = PdfDocumentExtractor()
    with pytest.raises(EmptyDocumentError) as exc_info:
        extractor.extract(file_bytes=b"", original_filename="vacio.pdf")
    assert exc_info.value.code == "EMPTY_DOCUMENT"


def test_pdf_extractor_auto_checksum() -> None:
    """Calcula automáticamente el hash SHA-256 si no es provisto."""
    pdf_bytes = build_valid_pdf(["Prueba de checksum automático"])
    extractor = PdfDocumentExtractor()

    doc = extractor.extract(file_bytes=pdf_bytes, original_filename="ciencias.pdf")
    assert doc.extraction_metadata is not None
    assert len(doc.extraction_metadata.file_checksum) == 64


def test_pdf_extractor_file_not_decrypted_maps_to_encrypted_error() -> None:
    """Verifica que FileNotDecryptedError se mapee a EncryptedDocumentError en lugar de CorruptDocumentError."""
    from unittest.mock import MagicMock, PropertyMock, patch

    from pypdf.errors import FileNotDecryptedError

    extractor = PdfDocumentExtractor()

    mock_reader = MagicMock()
    mock_reader.is_encrypted = False  # Did not report is_encrypted at top level
    type(mock_reader).pages = PropertyMock(
        side_effect=FileNotDecryptedError("File not decrypted")
    )

    with (
        patch(
            "app.content_generation.extractors.pdf_extractor.PdfReader",
            return_value=mock_reader,
        ),
        pytest.raises(EncryptedDocumentError) as exc_info,
    ):
        extractor.extract(
            file_bytes=b"%PDF-1.4 mock",
            original_filename="cifrado_oculto.pdf",
        )

    assert exc_info.value.code == "ENCRYPTED_DOCUMENT"


def test_pdf_extractor_spanish_accents() -> None:
    """Verifica la correcta extracción de caracteres con tilde y terminología científica en español."""
    pdf_bytes = build_spanish_accented_pdf()
    extractor = PdfDocumentExtractor()

    doc = extractor.extract(
        file_bytes=pdf_bytes, original_filename="fotosintesis_espanol.pdf"
    )
    assert doc.total_units == 2
    assert "fotosíntesis" in doc.units[0].text
    assert "energía" in doc.units[0].text
    assert "fijación" in doc.units[0].text
    assert "Respiración" in doc.units[1].text
    assert "síntesis" in doc.units[1].text
