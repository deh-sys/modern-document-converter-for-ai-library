"""Pipeline coordinating parsing and renaming."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Set

from .formatter import FilenameFormatter
from .models import DocumentMetadata, DocumentType, RenameResult
from .parsers import DocxParser, PDFParser
from .parsers.base import DocumentParser
from .templates import FilenameTemplate, TemplateError

LOGGER = logging.getLogger(__name__)


@dataclass
class ParserRegistry:
    """Registry for document parsers keyed by file extension."""

    parsers: Sequence[DocumentParser]

    def get_parser(self, path: Path) -> Optional[DocumentParser]:
        for parser in self.parsers:
            try:
                if parser.supports(path):
                    return parser
            except Exception:
                LOGGER.exception("Parser %s failed supports check for %s", parser, path)
        LOGGER.debug("No parser available for %s", path)
        return None


class RenamePipeline:
    """Main orchestration for previewing and executing rename operations."""

    def __init__(self, registry: ParserRegistry, formatter: FilenameFormatter) -> None:
        self.registry = registry
        self.formatter = formatter

    def generate_preview(self, source_dir: Path, limit: Optional[int] = None) -> List[RenameResult]:
        """Return planned rename operations."""

        results: List[RenameResult] = []
        seen_paths: Set[Path] = set()
        for document in self._discover_documents(source_dir):
            parser = self.registry.get_parser(document)
            if not parser:
                LOGGER.info("Skipping unsupported file: %s", document.name)
                continue
            try:
                metadata = parser.parse(document)
            except Exception as exc:  # pragma: no cover - defensive logging
                LOGGER.exception("Failed to parse %s: %s", document, exc)
                continue
            try:
                destination = self._build_unique_destination(metadata, seen_paths)
            except TemplateError as exc:
                LOGGER.warning("Template requirements not satisfied for %s: %s", document, exc)
                continue

            result = RenameResult(
                original_path=document,
                new_path=destination,
                original_name=document.name,
                new_name=destination.name,
                metadata=metadata,
            )
            results.append(result)
            seen_paths.add(destination)

            if limit is not None and len(results) >= limit:
                break

        return results

    def execute(self, plan: Iterable[RenameResult]) -> None:
        """Perform the rename operations on disk."""

        for result in plan:
            destination_parent = result.new_path.parent
            destination_parent.mkdir(parents=True, exist_ok=True)
            if result.original_path == result.new_path:
                LOGGER.debug("Skipping rename for %s (no change)", result.original_path)
                continue
            LOGGER.info("Renaming %s -> %s", result.original_path.name, result.new_name)
            result.original_path.rename(result.new_path)

    def _discover_documents(self, source_dir: Path) -> Iterable[Path]:
        """Yield supported documents from the source directory."""

        # Collect all matching files (case-insensitive)
        matching_files = []
        for path in source_dir.iterdir():
            if not path.is_file():
                continue
            suffix = path.suffix.lower()
            if suffix in {".pdf", ".docx"}:
                matching_files.append(path)

        # Sort and yield
        for path in sorted(matching_files):
            yield path

    def _build_unique_destination(self, metadata: DocumentMetadata, seen_paths: Set[Path]) -> Path:
        """Compute a unique destination path avoiding collisions."""

        base_path = self.formatter.build_full_path(metadata, metadata.source_path.parent)
        candidate = base_path
        counter = 1
        while candidate in seen_paths or candidate.exists():
            candidate = candidate.with_stem(f"{base_path.stem}-{counter}")
            counter += 1
        return candidate


def build_pipeline(template: FilenameTemplate) -> RenamePipeline:
    """Factory for creating a ready-to-use pipeline."""

    registry = ParserRegistry(parsers=[PDFParser(), DocxParser()])
    formatter = FilenameFormatter(template)
    return RenamePipeline(registry, formatter)
