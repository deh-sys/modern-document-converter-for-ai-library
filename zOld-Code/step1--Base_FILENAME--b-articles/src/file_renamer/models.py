"""Domain models for article renaming."""

from enum import Enum
from pathlib import Path
from typing import Optional, List

from pydantic import BaseModel, Field, validator


class DocumentType(str, Enum):
    """Supported document types."""

    PDF = "pdf"
    DOCX = "docx"


class ArticleMetadata(BaseModel):
    """Parsed metadata for law journal articles."""

    source_path: Path
    authors: List[str] = Field(default_factory=list, description="List of author names")
    title: Optional[str] = Field(default=None, description="Article title")
    publication_year: Optional[int] = Field(default=None, ge=1600, le=2100)
    journal_name: Optional[str] = Field(default=None, description="Journal name")
    volume: Optional[int] = Field(default=None, description="Volume number")
    issue: Optional[int] = Field(default=None, description="Issue number")
    page_start: Optional[int] = Field(default=None, description="Starting page")
    page_end: Optional[int] = Field(default=None, description="Ending page")
    document_type: DocumentType

    # Extended metadata fields
    abstract: Optional[str] = Field(default=None, description="Article abstract")
    keywords: List[str] = Field(default_factory=list, description="Keywords")
    doi: Optional[str] = Field(default=None, description="Digital Object Identifier")
    author_affiliations: List[dict] = Field(default_factory=list, description="Author institutions")

    @validator("source_path", pre=True)
    def _ensure_path(cls, value: Path) -> Path:
        return Path(value)


class RenameResult(BaseModel):
    """Represents a proposed or executed rename operation."""

    original_path: Path
    new_path: Path
    original_name: str
    new_name: str
    metadata: ArticleMetadata
