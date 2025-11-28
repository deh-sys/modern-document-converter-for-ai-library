"""Filename templates."""

from __future__ import annotations

from enum import Enum
from typing import Callable

from .models import DocumentMetadata

Sanitizer = Callable[[str], str]


class TemplateError(RuntimeError):
    """Raised when template rendering fails due to missing fields."""


class FilenameTemplate(str, Enum):
    """Enumerate supported filename templates."""

    CS_COURT_YEAR_SHORTCASE_REPORTER = "cs_[court]-[year]-[short_case]-[reporter]"

    def render(self, metadata: DocumentMetadata, sanitizer: Sanitizer) -> str:
        """Render template using metadata."""

        if self is FilenameTemplate.CS_COURT_YEAR_SHORTCASE_REPORTER:
            return _render_cs(metadata, sanitizer)
        raise TemplateError(f"Unsupported template: {self.value}")


def _render_cs(metadata: DocumentMetadata, sanitizer: Sanitizer) -> str:
    """Implementation for cs_[court]-[year]-[short_case]-[reporter]."""

    missing = [
        label
        for label, value in (
            ("court", metadata.jurisdiction),
            ("year", metadata.decision_year),
            ("short_case", metadata.short_case_name),
            ("reporter", metadata.reporter_citation),
        )
        if not value
    ]
    if missing:
        raise TemplateError(f"Missing metadata fields: {', '.join(missing)}")

    components = [
        "cs",
        sanitizer(metadata.jurisdiction or ""),
        str(metadata.decision_year),
        sanitizer(metadata.short_case_name or ""),
        sanitizer(metadata.reporter_citation or ""),
    ]
    return "-".join(filter(None, components))
