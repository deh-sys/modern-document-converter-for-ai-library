"""Utilities for turning metadata into filenames."""

import re
from pathlib import Path

from .models import DocumentMetadata
from .templates import FilenameTemplate

SAFE_SEPARATOR = "-"


def sanitize_component(value: str) -> str:
    """Normalize a metadata component into a filesystem friendly token."""

    normalized = value.strip().lower()
    normalized = re.sub(r"['’]", "", normalized)
    normalized = re.sub(r"[^a-z0-9]+", SAFE_SEPARATOR, normalized)
    normalized = re.sub(rf"{SAFE_SEPARATOR}+", SAFE_SEPARATOR, normalized)
    return normalized.strip(SAFE_SEPARATOR)


class FilenameFormatter:
    """Build filenames based on configurable templates."""

    def __init__(self, template: FilenameTemplate) -> None:
        self.template = template

    def build_filename(self, metadata: DocumentMetadata) -> str:
        """Compose the filename (without extension)."""

        return self.template.render(metadata, sanitize_component)

    def build_full_path(self, metadata: DocumentMetadata, destination_dir: Path) -> Path:
        """Return full path including original extension."""

        filename = self.build_filename(metadata)
        extension = metadata.source_path.suffix.lower()
        return destination_dir / f"{filename}{extension}"
