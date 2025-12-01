"""
Core Data Models - Document Processor

Pydantic models providing type safety and validation throughout the application.
These models are used by services, steps, and the orchestrator.

Usage:
    from src.core.models import Document, ExtractionResult, DocumentType

Design:
    - Immutable where appropriate (frozen=True)
    - Validation on construction
    - JSON serialization support
    - Clear documentation for all fields
"""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator, ConfigDict


# ============================================================================
# ENUMS
# ============================================================================

class DocumentType(str, Enum):
    """Document type classification."""
    CASELAW = "caselaw"
    ARTICLE = "article"
    STATUTE = "statute"
    BRIEF = "brief"
    BOOK = "book"
    UNKNOWN = "unknown"


class ProcessingStatus(str, Enum):
    """Processing step status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class ConfidenceLevel(str, Enum):
    """Confidence level for extracted data."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ExtractionSource(str, Enum):
    """Source of extracted metadata."""
    DOCUMENT = "document"      # Extracted from document text
    FILENAME = "filename"      # Extracted from filename
    FALLBACK = "fallback"      # Default/unknown value


# ============================================================================
# SERVICE RESULT MODELS
# ============================================================================

class ExtractionResult(BaseModel):
    """
    Result from text extraction service.

    Returned by: services/text_extractor.py

    Example:
        result = extract_text(Path("document.pdf"))
        if result.success:
            print(result.text)
        else:
            print(result.error_message)
    """
    text: str = Field(default="", description="Extracted text content")
    success: bool = Field(description="Whether extraction succeeded")
    page_count: Optional[int] = Field(
        default=None,
        description="Number of pages in document"
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Error message if extraction failed"
    )

    model_config = ConfigDict(frozen=True)


class ConvertResult(BaseModel):
    """
    Result from document conversion to AI-ready text.

    Returned by: steps/convert_step.py

    Contains information about the conversion process including:
        - Success status
        - Source and output file paths
        - Document type and metadata
        - Cleaning statistics (lines removed, headings added)
        - Processing time

    Example:
        result = convert_step.process_file(Path("case.pdf"))
        if result.success:
            print(f"Converted to: {result.output_file}")
            print(f"Removed {result.lines_removed} noise lines")
            print(f"Added {result.headings_added} markdown headings")
        else:
            print(result.error_message)
    """
    success: bool = Field(
        description="Whether conversion succeeded"
    )
    source_file: str = Field(
        description="Original source file path"
    )
    output_file: Optional[str] = Field(
        default=None,
        description="Output .txt file path (if successful)"
    )
    document_type: Optional[DocumentType] = Field(
        default=None,
        description="Classified document type"
    )
    character_count: int = Field(
        default=0,
        description="Number of characters in final cleaned text"
    )
    lines_removed: int = Field(
        default=0,
        description="Number of noise lines removed during cleaning"
    )
    headings_added: int = Field(
        default=0,
        description="Number of markdown headings added"
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Error message if conversion failed"
    )
    processing_time: Optional[float] = Field(
        default=None,
        description="Time taken for conversion in seconds"
    )

    model_config = ConfigDict(frozen=True)


class Classification(BaseModel):
    """
    Result from document type classification.

    Returned by: services/classifier.py

    Example:
        classification = classify(text)
        if classification.confidence > 0.8:
            print(f"Document is {classification.document_type}")
    """
    document_type: DocumentType = Field(
        description="Classified document type"
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence score (0.0 to 1.0)"
    )
    indicators: List[str] = Field(
        default_factory=list,
        description="Patterns/features that indicated this type"
    )

    model_config = ConfigDict(frozen=True)


# ============================================================================
# METADATA MODELS
# ============================================================================

class MetadataField(BaseModel):
    """
    Individual metadata field with provenance tracking.

    Tracks not just the value, but where it came from and how confident we are.

    Example:
        field = MetadataField(
            key="court",
            value="ILL_ND",
            source=ExtractionSource.DOCUMENT,
            confidence=ConfidenceLevel.HIGH,
            extractor_name="CourtExtractor"
        )
    """
    key: str = Field(description="Metadata field name (e.g., 'court', 'year')")
    value: str = Field(description="Extracted value")
    source: ExtractionSource = Field(
        description="Where this value was extracted from"
    )
    confidence: ConfidenceLevel = Field(
        description="Confidence in this extraction"
    )
    extractor_name: Optional[str] = Field(
        default=None,
        description="Name of extractor that produced this value"
    )
    extracted_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When this field was extracted"
    )

    model_config = ConfigDict(frozen=True)


class DocumentMetadata(BaseModel):
    """
    Complete metadata for a document (flexible schema).

    Different document types have different fields:
    - Caselaw: court, year, case_name, reporter
    - Article: authors, year, title, journal
    - Statute: jurisdiction, year, code_section

    Example:
        metadata = DocumentMetadata(
            fields={
                "court": MetadataField(key="court", value="ILL_ND", ...),
                "year": MetadataField(key="year", value="2010", ...),
            },
            document_type=DocumentType.CASELAW
        )
    """
    fields: Dict[str, MetadataField] = Field(
        default_factory=dict,
        description="Extracted metadata fields"
    )
    document_type: DocumentType = Field(
        description="Type of document this metadata is for"
    )

    def get_value(self, key: str, default: str = "") -> str:
        """Get metadata value by key, or default if not found."""
        field = self.fields.get(key)
        return field.value if field else default

    def get_confidence(self, key: str) -> Optional[ConfidenceLevel]:
        """Get confidence level for a field."""
        field = self.fields.get(key)
        return field.confidence if field else None


# ============================================================================
# DOCUMENT MODELS
# ============================================================================

class Document(BaseModel):
    """
    Main document representation.

    Tracks a document through the entire pipeline:
    - File identification (paths, filenames)
    - Content (extracted text)
    - Classification (document type)
    - Metadata (extracted fields)
    - Processing (unique code, status)

    Example:
        doc = Document(
            file_path=Path("/files/case.pdf"),
            original_filename="case.pdf",
            current_filename="case.pdf"
        )
        doc.text = extractor.extract_text(doc.file_path).text
        doc.document_type = classifier.classify(doc.text).document_type
    """
    # File identification
    file_path: Path = Field(description="Current absolute path to file")
    original_filename: str = Field(
        description="Original filename when first processed"
    )
    current_filename: str = Field(
        description="Current filename (may be renamed)"
    )
    file_hash: Optional[str] = Field(
        default=None,
        description="SHA-256 hash for change detection"
    )

    # Content
    text: Optional[str] = Field(
        default=None,
        description="Extracted text content"
    )

    # Classification
    document_type: Optional[DocumentType] = Field(
        default=None,
        description="Classified document type"
    )
    classification_confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Classification confidence score"
    )

    # Metadata
    metadata: Optional[DocumentMetadata] = Field(
        default=None,
        description="Extracted metadata fields"
    )

    # Processing
    unique_code: Optional[str] = Field(
        default=None,
        description="Unique 5-letter identifier code"
    )
    processing_status: ProcessingStatus = Field(
        default=ProcessingStatus.PENDING,
        description="Overall processing status"
    )

    # Timestamps
    first_seen: datetime = Field(
        default_factory=datetime.utcnow,
        description="When document was first added to system"
    )
    last_modified: datetime = Field(
        default_factory=datetime.utcnow,
        description="When document file was last modified"
    )
    last_processed: Optional[datetime] = Field(
        default=None,
        description="When document was last processed"
    )

    @field_validator('file_path')
    @classmethod
    def validate_file_path(cls, v: Path) -> Path:
        """Ensure file path is absolute."""
        if not v.is_absolute():
            raise ValueError(f"file_path must be absolute, got: {v}")
        return v

    model_config = ConfigDict(
        arbitrary_types_allowed=True  # Allow Path objects
    )


# ============================================================================
# PROCESSING TRACKING MODELS
# ============================================================================

class ProcessingStep(BaseModel):
    """
    Record of a single processing step execution.

    Tracks:
    - What step ran (rename, code, convert, clean)
    - When it ran (started/completed)
    - What happened (success/failure)
    - Any errors or outputs

    Used by: services/registrar.py to track step completion

    Example:
        step = ProcessingStep(
            step_name="rename",
            step_order=1,
            status=ProcessingStatus.SUCCESS,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow()
        )
    """
    step_name: str = Field(
        description="Step identifier (rename, code, convert, clean)"
    )
    step_order: int = Field(
        ge=1,
        le=4,
        description="Step order in pipeline (1-4)"
    )
    status: ProcessingStatus = Field(
        description="Current status of this step"
    )
    started_at: Optional[datetime] = Field(
        default=None,
        description="When step started"
    )
    completed_at: Optional[datetime] = Field(
        default=None,
        description="When step completed"
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Error message if step failed"
    )
    warning_message: Optional[str] = Field(
        default=None,
        description="Warning message (step succeeded but with issues)"
    )
    output_path: Optional[Path] = Field(
        default=None,
        description="Output file path (for convert/clean steps)"
    )
    config_snapshot: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Configuration used for this step (for reproducibility)"
    )

    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate step duration if both timestamps available."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    model_config = ConfigDict(
        arbitrary_types_allowed=True  # Allow Path objects
    )


class RenameResult(BaseModel):
    """
    Result from rename step.

    Tracks:
    - Original and new paths
    - Extracted metadata used for renaming
    - Overall confidence in the rename
    - Any warnings (e.g., filename truncated)

    Used by: steps/rename_step.py

    Example:
        result = RenameResult(
            original_path=Path("/files/case.pdf"),
            new_path=Path("/files/c.ILL_ND__2010__Abbott-v-Sandoz.pdf"),
            metadata=metadata,
            confidence=ConfidenceLevel.HIGH
        )
    """
    original_path: Path = Field(description="Original file path")
    new_path: Path = Field(description="New file path after rename")
    metadata: DocumentMetadata = Field(
        description="Metadata used to generate new filename"
    )
    confidence: ConfidenceLevel = Field(
        description="Overall confidence in this rename"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Warnings (e.g., 'filename truncated', 'fallback used')"
    )
    dry_run: bool = Field(
        default=False,
        description="Whether this was a dry-run (no actual rename)"
    )

    @property
    def original_filename(self) -> str:
        """Get original filename."""
        return self.original_path.name

    @property
    def new_filename(self) -> str:
        """Get new filename."""
        return self.new_path.name

    model_config = ConfigDict(
        frozen=True,
        arbitrary_types_allowed=True
    )


class CodeAllocation(BaseModel):
    """
    Unique code assignment record.

    Tracks:
    - What code was allocated
    - When it was allocated
    - Current status (allocated, in_use, rolled_back)

    Used by: services/code_generator.py

    Example:
        allocation = CodeAllocation(
            code="ABCDE",
            allocated_at=datetime.utcnow(),
            status="in_use"
        )
    """
    code: str = Field(
        min_length=5,
        max_length=5,
        description="5-letter unique code"
    )
    allocated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When code was allocated"
    )
    status: str = Field(
        default="allocated",
        description="Code status: allocated, in_use, rolled_back"
    )

    @field_validator('code')
    @classmethod
    def validate_code_format(cls, v: str) -> str:
        """Ensure code is uppercase letters only (A-Z except W)."""
        if not v.isupper():
            raise ValueError(f"Code must be uppercase: {v}")
        if not all(c in "ABCDEFGHIJKLMNOPQRSTUVXYZ" for c in v):
            raise ValueError(f"Code contains invalid characters: {v}")
        return v

    model_config = ConfigDict(frozen=True)


# ============================================================================
# BATCH PROCESSING MODELS
# ============================================================================

class BatchResult(BaseModel):
    """
    Result from batch processing operation.

    Summary statistics for processing multiple documents.

    Example:
        result = BatchResult(
            total=100,
            successful=95,
            failed=3,
            skipped=2
        )
        print(f"Success rate: {result.success_rate:.1%}")
    """
    total: int = Field(ge=0, description="Total documents processed")
    successful: int = Field(ge=0, description="Successfully processed")
    failed: int = Field(ge=0, description="Failed to process")
    skipped: int = Field(ge=0, description="Skipped (already processed, etc.)")
    warnings: List[str] = Field(
        default_factory=list,
        description="Batch-level warnings"
    )
    failure_details: List[tuple[str, str]] = Field(
        default_factory=list,
        description="Failed files: [(filename, error_message), ...]"
    )
    started_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Batch start time"
    )
    completed_at: Optional[datetime] = Field(
        default=None,
        description="Batch completion time"
    )

    @property
    def success_rate(self) -> float:
        """Calculate success rate (0.0 to 1.0)."""
        if self.total == 0:
            return 0.0
        return self.successful / self.total

    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate batch duration."""
        if self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    model_config = ConfigDict(frozen=True)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def create_metadata_field(
    key: str,
    value: str,
    source: ExtractionSource,
    confidence: ConfidenceLevel,
    extractor_name: Optional[str] = None
) -> MetadataField:
    """
    Helper to create MetadataField with less boilerplate.

    Example:
        field = create_metadata_field(
            "court", "ILL_ND",
            ExtractionSource.DOCUMENT,
            ConfidenceLevel.HIGH,
            "CourtExtractor"
        )
    """
    return MetadataField(
        key=key,
        value=value,
        source=source,
        confidence=confidence,
        extractor_name=extractor_name
    )
