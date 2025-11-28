"""Metadata extraction for different document types."""

from .word import WordMetadataExtractor
from .ebook import EbookMetadataExtractor
from .pdf import PDFMetadataExtractor

__all__ = [
    'WordMetadataExtractor',
    'EbookMetadataExtractor',
    'PDFMetadataExtractor',
]
