"""Domain models for caselaw renaming."""

from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field, validator


class DocumentType(str, Enum):
    """Supported document types."""

    PDF = "pdf"
    DOCX = "docx"


class DocumentMetadata(BaseModel):
    """Parsed metadata required for filename generation."""

    source_path: Path
    jurisdiction: Optional[str] = Field(default=None, description="Normalized court identifier.")
    decision_year: Optional[int] = Field(default=None, ge=1600, le=2100)
    short_case_name: Optional[str] = Field(default=None, description="Concise case name.")
    reporter_citation: Optional[str] = Field(default=None, description="Primary reporter citation.")
    document_type: DocumentType

    @validator("source_path", pre=True)
    def _ensure_path(cls, value: Path) -> Path:
        return Path(value)


class RenameResult(BaseModel):
    """Represents a proposed or executed rename operation."""

    original_path: Path
    new_path: Path
    original_name: str
    new_name: str
    metadata: DocumentMetadata
