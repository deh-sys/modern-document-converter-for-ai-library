"""File type detection for document conversion."""

from enum import Enum
from pathlib import Path
from typing import Optional


class DocumentType(Enum):
    """Supported document types."""
    WORD = "word"
    EPUB = "epub"
    MOBI = "mobi"
    PDF = "pdf"
    UNKNOWN = "unknown"


class FileTypeDetector:
    """Detect document type based on file extension."""

    # Extension mappings
    WORD_EXTENSIONS = {'.docx', '.doc'}
    EPUB_EXTENSIONS = {'.epub'}
    MOBI_EXTENSIONS = {'.mobi', '.azw', '.azw3'}
    PDF_EXTENSIONS = {'.pdf'}

    @classmethod
    def detect(cls, file_path: Path) -> DocumentType:
        """Detect document type from file extension.

        Args:
            file_path: Path to the document file

        Returns:
            DocumentType enum value
        """
        if not isinstance(file_path, Path):
            file_path = Path(file_path)

        extension = file_path.suffix.lower()

        if extension in cls.WORD_EXTENSIONS:
            return DocumentType.WORD
        elif extension in cls.EPUB_EXTENSIONS:
            return DocumentType.EPUB
        elif extension in cls.MOBI_EXTENSIONS:
            return DocumentType.MOBI
        elif extension in cls.PDF_EXTENSIONS:
            return DocumentType.PDF
        else:
            return DocumentType.UNKNOWN

    @classmethod
    def is_supported(cls, file_path: Path) -> bool:
        """Check if file type is supported.

        Args:
            file_path: Path to the document file

        Returns:
            True if file type is supported, False otherwise
        """
        return cls.detect(file_path) != DocumentType.UNKNOWN

    @classmethod
    def get_supported_extensions(cls) -> set[str]:
        """Get all supported file extensions.

        Returns:
            Set of supported extensions
        """
        return (
            cls.WORD_EXTENSIONS |
            cls.EPUB_EXTENSIONS |
            cls.MOBI_EXTENSIONS |
            cls.PDF_EXTENSIONS
        )
