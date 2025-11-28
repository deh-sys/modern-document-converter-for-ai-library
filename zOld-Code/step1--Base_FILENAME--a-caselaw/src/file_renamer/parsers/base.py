"""Parser interfaces for extracting metadata from documents."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from ..models import DocumentMetadata, DocumentType


class DocumentParser(Protocol):
    """Interface for document parsers."""

    document_type: DocumentType

    def parse(self, path: Path) -> DocumentMetadata:
        """Extract metadata from the given path."""

    def supports(self, path: Path) -> bool:
        """Return True if this parser can handle the given file."""
