#!/usr/bin/env python3
"""
Orchestrator - Pipeline Manager

Coordinates services to process batches of documents through the complete pipeline.

Pipeline Flow:
    1. Scan folder recursively for PDF/DOCX files
    2. Sort files alphabetically (deterministic processing)
    3. For each file:
       a. RenameStep: Extract metadata, assign code, rename file
       b. ConvertStep: Extract text, clean, add frontmatter, save .txt (only if rename succeeded)
    4. Track statistics and errors
    5. Return comprehensive BatchResult

Features:
    - Atomic pipeline: if rename fails, conversion is skipped
    - Shared registrar instance across both steps
    - Progress tracking with rich progress bars
    - Comprehensive error handling (individual file failures don't crash batch)
    - Detailed failure reporting (filename + error message for each failure)
    - Dry-run mode support

Usage:
    from src.core.orchestrator import process_batch

    result = process_batch(Path("/documents"), strategy="fast")
    print(f"Processed {result.successful}/{result.total} files")

    # Dry-run mode (simulation)
    result = process_batch(Path("/documents"), strategy="fast", dry_run=True)
"""

from pathlib import Path
from datetime import datetime

from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.console import Console

from src.core.models import BatchResult
from src.steps.rename_step import RenameStep
from src.steps.convert_step import ConvertStep
from src.services.registrar import Registrar


console = Console()


def process_batch(
    folder_path: Path,
    strategy: str = 'fast',
    dry_run: bool = False,
) -> BatchResult:
    """
    Process a batch of documents through the complete pipeline.

    Pipeline for each file:
        1. RenameStep: Extract metadata → Assign unique code → Rename file
        2. ConvertStep: Extract text → Clean → Add frontmatter → Save .txt

    Args:
        folder_path: Path to folder containing documents to process
        strategy: Extraction strategy for PDFs:
            - 'fast': pdfplumber (default, works for most layouts)
            - 'deep': marker-pdf AI (slow, complex multi-column layouts)
        dry_run: If True, simulate processing without modifying files (default: False)

    Returns:
        BatchResult with statistics:
            - total: Total files found
            - successful: Files processed through both steps successfully
            - failed: Files that failed rename or convert
            - failure_details: List of (filename, error_message) tuples
            - duration_seconds: Total processing time

    Example:
        >>> result = process_batch(Path("/documents"), strategy="fast")
        >>> print(f"Success rate: {result.success_rate:.1%}")
        >>> for filename, error in result.failure_details:
        ...     print(f"Failed: {filename} - {error}")

    Processing Rules:
        - Files processed in alphabetical order (deterministic)
        - If RenameStep fails, ConvertStep is skipped (atomic pipeline)
        - Individual file failures don't crash the entire batch
        - All errors are collected in failure_details for reporting
    """
    start_time = datetime.utcnow()

    # Step 1: Scan folder for PDF and DOCX files
    pdf_files = list(folder_path.rglob("*.pdf"))
    docx_files = list(folder_path.rglob("*.docx"))
    all_files = pdf_files + docx_files

    # Sort alphabetically for deterministic processing
    all_files.sort()

    # Handle empty folder
    if len(all_files) == 0:
        return BatchResult(
            total=0,
            successful=0,
            failed=0,
            skipped=0,
            warnings=["No PDF or DOCX files found in folder"],
            completed_at=datetime.utcnow(),
        )

    # Step 2: Initialize registrar and pipeline steps
    try:
        registrar = Registrar(Path("registry/master.db"))
    except Exception as e:
        # Failed to initialize registrar - can't process anything
        return BatchResult(
            total=len(all_files),
            successful=0,
            failed=len(all_files),
            skipped=0,
            warnings=[f"Failed to initialize registrar: {str(e)}"],
            failure_details=[(f.name, "Registrar initialization failed") for f in all_files],
            started_at=start_time,
            completed_at=datetime.utcnow(),
        )

    try:
        # Create pipeline steps with shared registrar
        rename_step = RenameStep(registrar=registrar, dry_run=dry_run, max_pages=3)
        convert_step = ConvertStep(registrar=registrar, strategy=strategy, dry_run=dry_run)

        # Step 3: Process files with progress tracking
        successful = 0
        failed = 0
        failure_details = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
        ) as progress:
            task = progress.add_task("Processing documents...", total=len(all_files))

            for file_path in all_files:
                # Update progress bar with current file
                progress.update(task, description=f"Processing {file_path.name}...")

                # Step 3a: Rename (extract metadata, assign code, rename file)
                rename_result = rename_step.process_file(file_path)

                if not rename_result.success:
                    # ATOMIC RULE: If rename fails, skip conversion
                    # We can't create proper .txt file without unique code and metadata
                    failed += 1
                    error_msg = rename_result.error_message or "Unknown error"
                    failure_details.append((file_path.name, f"Rename failed: {error_msg}"))
                    progress.advance(task)
                    continue

                # Step 3b: Convert (only if rename succeeded)
                # Use new_path from rename result (file has been renamed)
                new_path = rename_result.new_path if not dry_run else file_path
                convert_result = convert_step.process_file(new_path)

                if not convert_result.success:
                    # Rename succeeded but conversion failed (partial success)
                    failed += 1
                    error_msg = convert_result.error_message or "Unknown error"
                    # Use renamed filename for error reporting
                    failed_name = rename_result.new_name or file_path.name
                    failure_details.append((failed_name, f"Convert failed: {error_msg}"))
                else:
                    # Both steps succeeded!
                    successful += 1

                progress.advance(task)

    finally:
        # Always close registrar connection (even if errors occur)
        registrar.close()

    # Step 4: Construct and return batch result
    batch_result = BatchResult(
        total=len(all_files),
        successful=successful,
        failed=failed,
        skipped=0,  # Can add skip logic later (e.g., already processed files)
        warnings=[],
        failure_details=failure_details,
        started_at=start_time,
        completed_at=datetime.utcnow(),
    )

    return batch_result
