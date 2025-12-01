#!/usr/bin/env python3
"""
Orchestrator - Pipeline Manager

Coordinates services to process batches of documents.

This is currently a stub implementation. The real orchestrator will be
implemented in Phase 2 after all pipeline steps are complete.

Architecture:
    - Receives folder path and strategy parameter
    - Scans for supported documents (.pdf, .docx)
    - Coordinates pipeline steps: extract → classify → metadata → code → format → rename
    - Tracks progress in registry
    - Returns batch results

Future Implementation (Phase 2):
    - Sequential pipeline execution
    - Dry-run mode support
    - Error handling and rollback
    - Progress tracking with rich
    - Batch statistics and reporting

Usage:
    from src.core.orchestrator import process_batch

    process_batch(Path("/documents"), strategy="fast")
"""

from pathlib import Path


def process_batch(folder_path: Path, strategy: str) -> None:
    """
    Process a batch of documents with specified extraction strategy.

    This is a STUB implementation. It will be replaced with real orchestration
    logic in Phase 2 after pipeline steps are complete.

    Args:
        folder_path: Path to folder containing documents to process
        strategy: Extraction strategy to use:
            - 'fast': Use pdfplumber for PDFs (default, works for most layouts)
            - 'deep': Use marker-pdf AI for complex multi-column PDFs (requires marker-pdf)

    Returns:
        None (stub prints status message)

    Future Returns:
        BatchResult model with:
            - success_count: Number of documents processed successfully
            - failure_count: Number of documents that failed
            - results: List of individual DocumentResult models
            - processing_time: Total time taken

    Example:
        >>> process_batch(Path("/path/to/pdfs"), strategy="fast")
        Fake Orchestrator: Processing /path/to/pdfs using fast strategy...

    Note:
        The real implementation will:
        - Scan folder recursively for .pdf and .docx files
        - Process each file through pipeline steps
        - Track progress in registry
        - Handle errors gracefully
        - Return comprehensive BatchResult
    """
    # STUB: Just print status message
    print(f"Fake Orchestrator: Processing {folder_path} using {strategy} strategy...")
