"""Extractors package for curriculum document processing."""

from app.content_generation.extractors.base import BaseDocumentExtractor
from app.content_generation.extractors.pdf_extractor import PdfDocumentExtractor
from app.content_generation.extractors.pptx_extractor import PptxDocumentExtractor

__all__ = [
    "BaseDocumentExtractor",
    "PdfDocumentExtractor",
    "PptxDocumentExtractor",
]
