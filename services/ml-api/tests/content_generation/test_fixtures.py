"""Programmatic fixture builders for educational document extraction tests.

Generates strictly synthetic educational materials in-memory:
- Fictional Science curriculum (Fotosíntesis celular, Ecosistemas, Mitocondrias)
- Clean, corrupt, encrypted, empty, and malicious/suspicious files.
"""

import io
import zipfile

from pptx import Presentation
from pptx.util import Inches
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject


def build_valid_pdf(pages_content: list[str]) -> bytes:
    """Build a multi-page valid PDF containing fictional educational text."""
    writer = PdfWriter()
    for text in pages_content:
        page = writer.add_blank_page(width=400, height=500)
        # Standard PDF content stream with text operators
        escaped_text = text.replace("(", "\\(").replace(")", "\\)")
        stream_data = f"BT /F1 12 Tf 40 450 Td ({escaped_text}) Tj ET".encode("latin-1")
        stream_obj = DecodedStreamObject()
        stream_obj.set_data(stream_data)
        page[NameObject("/Contents")] = writer._add_object(stream_obj)

        # Attach Helvetica font dictionary
        f1_dict = DictionaryObject(
            {
                NameObject("/Type"): NameObject("/Font"),
                NameObject("/Subtype"): NameObject("/Type1"),
                NameObject("/BaseFont"): NameObject("/Helvetica"),
            }
        )
        font_dict = DictionaryObject({NameObject("/F1"): f1_dict})
        page[NameObject("/Resources")] = DictionaryObject(
            {NameObject("/Font"): font_dict}
        )

    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


def build_blank_pdf(num_pages: int = 2) -> bytes:
    """Build a PDF with pages but zero extractable text (e.g. scanned image placeholder)."""
    writer = PdfWriter()
    for _ in range(num_pages):
        writer.add_blank_page(width=300, height=400)
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


def build_encrypted_pdf(password: str = "docente_pass_2026") -> bytes:
    """Build an encrypted/password-protected PDF."""
    writer = PdfWriter()
    writer.add_blank_page(width=300, height=400)
    writer.encrypt(password)
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


def build_valid_pptx(slides_content: list[str], include_table: bool = False) -> bytes:
    """Build a multi-slide PPTX with educational curriculum text and optional table."""
    prs = Presentation()

    for idx, text in enumerate(slides_content, start=1):
        # Layout 5: Title only, or Layout 0: Title and Subtitle
        layout = prs.slide_layouts[0] if idx == 1 else prs.slide_layouts[5]
        slide = prs.slides.add_slide(layout)
        if slide.shapes.title:
            slide.shapes.title.text = f"Unidad {idx}: {text[:30]}"

        # Add content text frame
        txBox = slide.shapes.add_textbox(Inches(1), Inches(2), Inches(6), Inches(2))
        tf = txBox.text_frame
        tf.text = text

    if include_table:
        # Add a slide with a structured table
        table_slide = prs.slides.add_slide(prs.slide_layouts[5])
        if table_slide.shapes.title:
            table_slide.shapes.title.text = "Comparativa de Fases de la Fotosíntesis"

        table_shape = table_slide.shapes.add_table(
            3, 2, Inches(1), Inches(2), Inches(6), Inches(2)
        )
        tbl = table_shape.table
        tbl.cell(0, 0).text = "Fase de Reacción"
        tbl.cell(0, 1).text = "Ubicación en Cloroplasto"
        tbl.cell(1, 0).text = "Fase Luminosa"
        tbl.cell(1, 1).text = "Membrana Tilacoidal"
        tbl.cell(2, 0).text = "Ciclo de Calvin"
        tbl.cell(2, 1).text = "Estroma"

    buf = io.BytesIO()
    prs.save(buf)
    return buf.getvalue()


def build_empty_pptx() -> bytes:
    """Build an empty PPTX presentation with 0 slides."""
    prs = Presentation()
    buf = io.BytesIO()
    prs.save(buf)
    return buf.getvalue()


def build_zip_bomb_pptx() -> bytes:
    """Build a suspicious PPTX with an extreme uncompressed-to-compressed ratio."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", b"<Types/>")
        zf.writestr("ppt/presentation.xml", b"<p:presentation/>")
        # Write large repeating zeros to trigger high compression ratio (> 30x)
        zf.writestr("ppt/slides/suspicious_data.bin", b"0" * (10 * 1024 * 1024))
    return buf.getvalue()


def build_traversal_pptx() -> bytes:
    """Build a PPTX archive containing path traversal entries."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("[Content_Types].xml", b"<Types/>")
        zf.writestr("ppt/presentation.xml", b"<p:presentation/>")
        zf.writestr("../../../etc/passwd", b"malicious content")
    return buf.getvalue()


def build_macro_pptx() -> bytes:
    """Build a PPTX containing a VBA macro (vbaProject.bin)."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("[Content_Types].xml", b"<Types/>")
        zf.writestr("ppt/presentation.xml", b"<p:presentation/>")
        zf.writestr("ppt/vbaProject.bin", b"VBA_MACRO_PAYLOAD_BINARY")
    return buf.getvalue()


def build_script_pptx() -> bytes:
    """Build a PPTX containing an embedded executable script (.vbs)."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("[Content_Types].xml", b"<Types/>")
        zf.writestr("ppt/presentation.xml", b"<p:presentation/>")
        zf.writestr("ppt/embeddings/exploit.vbs", b"WScript.Echo 'Injected'")
    return buf.getvalue()


def build_multiline_table_pptx() -> bytes:
    """Build a PPTX with a table containing multiline cell values and pipe symbols."""
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[5])
    table_shape = slide.shapes.add_table(
        2, 2, Inches(1), Inches(2), Inches(6), Inches(2)
    )
    tbl = table_shape.table
    tbl.cell(0, 0).text = "Concepto\nPrincipal"
    tbl.cell(0, 1).text = "Definición | Descripción"
    tbl.cell(1, 0).text = "Mitocondria\n(Organelo)"
    tbl.cell(1, 1).text = "Generación de ATP\nmediante fosforilación"
    buf = io.BytesIO()
    prs.save(buf)
    return buf.getvalue()


def build_spanish_accented_pdf() -> bytes:
    """Build a valid PDF containing Spanish accented educational text and special characters."""
    pages = [
        "Capítulo 1: La fotosíntesis celular, energía solar y fijación del CO2.",
        "Capítulo 2: Respiración celular en la mitocondria y síntesis del ATP.",
    ]
    return build_valid_pdf(pages)
