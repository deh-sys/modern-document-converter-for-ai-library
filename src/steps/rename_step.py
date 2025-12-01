#!/usr/bin/env python3
"""
Rename Step - Atomic File Renaming with Metadata Extraction

Orchestrates the complete rename workflow:
    1. Extract text from document
    2. Classify document type
    3. Extract metadata (case name, year, court, citation)
    4. Allocate unique code (or preserve existing code)
    5. Format standardized filename
    6. Rename file atomically
    7. Record processing history

Critical: This step is ATOMIC. The unique code is allocated BEFORE renaming
to prevent filename collisions (e.g., two "Smith v. Jones" cases).

Legacy Format (Caselaw):
    c.{COURT}__{YEAR}__{CASE_NAME}__{CITATION}----{CODE}.ext

Example Workflow:
    Input:  "Abbott Labs. v. Sandoz, Inc (ND Ill 2010).pdf"
    Steps:
        1. Extract text → "Abbott Laboratories v. Sandoz..."
        2. Classify → CASELAW (HIGH confidence)
        3. Extract metadata → {court: "ND Ill.", year: "2010", ...}
        4. Allocate code → "ABCDE" (from registrar)
        5. Format filename → "c.ND_Ill__2010__Abbott-v-Sandoz__743_FSupp2d_762----ABCDE.pdf"
        6. Rename file (atomic operation)
        7. Record in registry
    Output: "c.ND_Ill__2010__Abbott-v-Sandoz__743_FSupp2d_762----ABCDE.pdf"

Architecture:
    - Services Layer: text_extractor, classifier, CaselawProcessor, code_generator, registrar
    - Formatters Layer: filename_formatter
    - This Step: Orchestration only (no business logic)

Usage:
    step = RenameStep(dry_run=True)
    result = step.process_file(Path("case.pdf"))
    if result.success:
        print(f"Renamed: {result.old_name} → {result.new_name}")
"""

from pathlib import Path
from typing import Optional
from dataclasses import dataclass

from src.services.text_extractor import extract_text
from src.services.classifier import classify
from src.services.code_generator import CodeGenerator
from src.services.registrar import Registrar
from src.plugins.caselaw import CaselawProcessor
from src.formatters.filename_formatter import FilenameFormatter
from src.core.models import DocumentType, ProcessingStatus


# ============================================================================
# RESULT MODELS
# ============================================================================

@dataclass
class RenameResult:
    """Result of rename operation."""
    success: bool
    old_path: Path
    new_path: Optional[Path]
    old_name: str
    new_name: Optional[str]
    document_type: Optional[DocumentType]
    unique_code: Optional[str]
    confidence: Optional[str]
    error_message: Optional[str] = None
    notes: list[str] = None

    def __post_init__(self):
        if self.notes is None:
            self.notes = []


# ============================================================================
# RENAME STEP
# ============================================================================

class RenameStep:
    """
    Atomic rename operation for document files.

    Extracts metadata, allocates unique code, formats filename, and renames file
    in one atomic operation to prevent collisions.
    """

    def __init__(
        self,
        registrar: Optional[Registrar] = None,
        dry_run: bool = True,
        max_pages: int = 3,
    ):
        """
        Initialize rename step.

        Args:
            registrar: Registrar instance (creates default if None)
            dry_run: If True, don't actually rename files (default: True)
            max_pages: Max pages to extract for metadata (default: 3)
        """
        self.dry_run = dry_run
        self.max_pages = max_pages

        # Initialize services
        if registrar is None:
            registrar = Registrar(Path("registry/master.db"))
        self.registrar = registrar
        self.code_generator = CodeGenerator(registrar)

        # Initialize processors (lazy load by document type)
        self._processors = {}


    # ========================================================================
    # PUBLIC API
    # ========================================================================

    def process_file(self, file_path: Path) -> RenameResult:
        """
        Process single file: extract metadata, allocate code, rename.

        This is the main entry point for the rename step. All operations are
        atomic - either everything succeeds or nothing changes.

        Args:
            file_path: Path to document file (.pdf, .docx)

        Returns:
            RenameResult with success status and details

        Example:
            >>> step = RenameStep(dry_run=True)
            >>> result = step.process_file(Path("case.pdf"))
            >>> print(result.new_name)
            'c.Ga_Ct_App__2014__Smith-v-Jones__328_GaApp_524----ABCDE.pdf'
        """
        file_path = file_path.resolve()
        original_name = file_path.name

        # Validate file exists
        if not file_path.exists():
            return RenameResult(
                success=False,
                old_path=file_path,
                new_path=None,
                old_name=original_name,
                new_name=None,
                document_type=None,
                unique_code=None,
                confidence=None,
                error_message=f"File not found: {file_path}",
            )

        # STEP 1: Extract text
        extraction_result = extract_text(file_path, max_pages=self.max_pages)
        if not extraction_result.success:
            return RenameResult(
                success=False,
                old_path=file_path,
                new_path=None,
                old_name=original_name,
                new_name=None,
                document_type=None,
                unique_code=None,
                confidence=None,
                error_message=f"Text extraction failed: {extraction_result.error_message}",
            )

        text = extraction_result.text
        notes = [f"Extracted {len(text)} characters from document"]

        # STEP 2: Classify document type
        classification = classify(text)
        document_type = classification.document_type
        notes.append(f"Classified as {document_type.value} (confidence: {classification.confidence:.2f})")

        # STEP 3: Extract metadata (document-type specific)
        metadata = self._extract_metadata(document_type, text)
        if not metadata or not metadata.fields:
            return RenameResult(
                success=False,
                old_path=file_path,
                new_path=None,
                old_name=original_name,
                new_name=None,
                document_type=document_type,
                unique_code=None,
                confidence=None,
                error_message="Metadata extraction failed - no fields extracted",
                notes=notes,
            )

        # Extract metadata values
        metadata_dict = {key: field.value for key, field in metadata.fields.items()}
        notes.append(f"Extracted metadata: {list(metadata_dict.keys())}")

        # STEP 4: Allocate unique code (ATOMIC - prevents collisions)
        unique_code = self.code_generator.allocate_code_for_file(file_path)
        notes.append(f"Allocated unique code: {unique_code}")

        # STEP 5: Register document in registry (before rename)
        try:
            doc_id = self.registrar.register_document(
                file_path,
                document_type=document_type,
            )

            # Link code to document
            self.registrar.commit_code_to_document(unique_code, doc_id)

            # Store metadata
            for key, field in metadata.fields.items():
                self.registrar.add_metadata(
                    doc_id,
                    key=key,
                    value=field.value,
                    source=field.source,  # Pass enum directly, not .value
                    confidence=field.confidence,  # Pass enum directly, not .value
                    extractor_name=field.extractor_name,
                )

            notes.append(f"Registered document (ID: {doc_id})")

        except Exception as e:
            # Rollback code allocation on registration failure
            self.code_generator.rollback_code(unique_code)
            return RenameResult(
                success=False,
                old_path=file_path,
                new_path=None,
                old_name=original_name,
                new_name=None,
                document_type=document_type,
                unique_code=None,
                confidence=None,
                error_message=f"Document registration failed: {e}",
                notes=notes,
            )

        # STEP 6: Format filename (with code)
        formatter = self._get_formatter(document_type)
        new_filename = formatter.format_filename(
            metadata_fields=metadata_dict,
            code=unique_code,
            extension=file_path.suffix,
        )

        if not new_filename:
            return RenameResult(
                success=False,
                old_path=file_path,
                new_path=None,
                old_name=original_name,
                new_name=None,
                document_type=document_type,
                unique_code=unique_code,
                confidence=None,
                error_message="Filename formatting failed - required fields missing",
                notes=notes,
            )

        notes.append(f"Formatted filename: {new_filename}")

        # STEP 7: Rename file (atomic operation)
        new_path = file_path.parent / new_filename

        # Check for collision (shouldn't happen with unique codes, but safety check)
        if new_path.exists() and new_path != file_path:
            return RenameResult(
                success=False,
                old_path=file_path,
                new_path=None,
                old_name=original_name,
                new_name=new_filename,
                document_type=document_type,
                unique_code=unique_code,
                confidence=f"{classification.confidence:.2f}",
                error_message=f"Filename collision: {new_filename} already exists",
                notes=notes,
            )

        # Perform rename (or skip if dry-run)
        if self.dry_run:
            notes.append("[DRY-RUN] Would rename file (no changes made)")
        else:
            try:
                file_path.rename(new_path)
                notes.append("File renamed successfully")

                # Update registry with new path
                self.registrar.update_document_name(doc_id, new_filename)

            except Exception as e:
                return RenameResult(
                    success=False,
                    old_path=file_path,
                    new_path=None,
                    old_name=original_name,
                    new_name=new_filename,
                    document_type=document_type,
                    unique_code=unique_code,
                    confidence=f"{classification.confidence:.2f}",
                    error_message=f"Rename operation failed: {e}",
                    notes=notes,
                )

        # STEP 8: Record processing step
        if not self.dry_run:
            self.registrar.record_processing_step(
                doc_id,
                step_name="rename",
                step_order=1,
                status=ProcessingStatus.SUCCESS,
            )

        # Success!
        return RenameResult(
            success=True,
            old_path=file_path,
            new_path=new_path,
            old_name=original_name,
            new_name=new_filename,
            document_type=document_type,
            unique_code=unique_code,
            confidence=f"{classification.confidence:.2f}",
            notes=notes,
        )


    # ========================================================================
    # INTERNAL HELPERS
    # ========================================================================

    def _extract_metadata(self, document_type: DocumentType, text: str):
        """
        Extract metadata using document-type specific processor.

        Args:
            document_type: Classified document type
            text: Extracted document text

        Returns:
            DocumentMetadata or None
        """
        if document_type == DocumentType.CASELAW:
            processor = self._get_caselaw_processor()
            return processor.extract_metadata(text)

        # Future: Add other document types (articles, statutes, briefs, books)
        return None


    def _get_caselaw_processor(self) -> CaselawProcessor:
        """Get or create caselaw processor (cached)."""
        if "caselaw" not in self._processors:
            self._processors["caselaw"] = CaselawProcessor()
        return self._processors["caselaw"]


    def _get_formatter(self, document_type: DocumentType) -> FilenameFormatter:
        """
        Get filename formatter for document type.

        Args:
            document_type: Document type

        Returns:
            FilenameFormatter instance
        """
        # Map DocumentType enum to template name
        template_name = document_type.value.lower()
        return FilenameFormatter(document_type=template_name)


    def close(self):
        """Clean up resources (close registrar connection)."""
        self.registrar.close()
