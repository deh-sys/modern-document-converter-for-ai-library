"""Placeholder PDF parser."""

from pathlib import Path

from ..models import DocumentMetadata, DocumentType
from .base import DocumentParser


class PDFParser(DocumentParser):
    """Stub parser until deterministic extraction rules are implemented."""

    document_type = DocumentType.PDF

    def parse(self, path: Path) -> DocumentMetadata:
        return DocumentMetadata(
            source_path=path,
            document_type=self.document_type,
        )

    def supports(self, path: Path) -> bool:
        return path.suffix.lower() == ".pdf"
