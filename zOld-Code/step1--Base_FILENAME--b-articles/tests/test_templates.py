from pathlib import Path

import pytest

from file_renamer.models import DocumentMetadata, DocumentType
from file_renamer.templates import FilenameTemplate, TemplateError


def test_template_requires_fields() -> None:
    metadata = DocumentMetadata(
        source_path=Path("example.pdf"), document_type=DocumentType.PDF
    )
    template = FilenameTemplate.CS_COURT_YEAR_SHORTCASE_REPORTER
    with pytest.raises(TemplateError):
        template.render(metadata, lambda value: value)


def test_template_renders_expected_format() -> None:
    metadata = DocumentMetadata(
        source_path=Path("example.pdf"),
        jurisdiction="Supreme Court of Canada",
        decision_year=2024,
        short_case_name="R. v. Smith",
        reporter_citation="2024 SCC 12",
        document_type=DocumentType.PDF,
    )
    template = FilenameTemplate.CS_COURT_YEAR_SHORTCASE_REPORTER
    result = template.render(metadata, lambda value: value.replace(" ", "-").lower())
    assert result == "cs_supreme-court-of-canada-2024_r.-v.-smith_2024-scc-12".replace("_", "-")
