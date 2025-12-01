#!/usr/bin/env python3
"""
Document Processor - Interactive CLI

Unified document processing pipeline with intelligent auto-detection.

Features:
    - Auto-scans folder for PDFs and DOCX files (recursive)
    - DOCX files: Run immediately (always safe)
    - PDF files: Interactive prompt for layout strategy
    - Educational warnings for optimal usage

Usage:
    python main.py /path/to/documents

Interactive Flow:
    1. Scans folder recursively for supported files
    2. If only DOCX: Runs immediately with fast strategy
    3. If PDFs present: Prompts user for layout type
       - Single column (fast): Uses pdfplumber
       - Double column (deep): Uses marker-pdf AI (slow)
    4. Processes all files with selected strategy

Example:
    python main.py ~/Downloads/lexis-cases
    python main.py /path/to/mixed-documents
"""

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel

from src.core.orchestrator import process_batch


# ============================================================================
# RICH CONSOLE SETUP
# ============================================================================

console = Console()


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def scan_folder(folder_path: Path) -> dict:
    """
    Scan folder recursively for supported document files.

    Args:
        folder_path: Path to folder to scan

    Returns:
        Dictionary with:
            - pdf_count: Number of PDF files found
            - docx_count: Number of DOCX files found
            - pdf_files: List of Path objects for PDFs
            - docx_files: List of Path objects for DOCX files
            - total_count: Total files found

    Example:
        >>> result = scan_folder(Path("/documents"))
        >>> print(f"Found {result['pdf_count']} PDFs, {result['docx_count']} DOCX")
    """
    # Scan recursively using rglob (recursive glob)
    pdf_files = list(folder_path.rglob("*.pdf"))
    docx_files = list(folder_path.rglob("*.docx"))

    return {
        "pdf_count": len(pdf_files),
        "docx_count": len(docx_files),
        "pdf_files": pdf_files,
        "docx_files": docx_files,
        "total_count": len(pdf_files) + len(docx_files),
    }


def prompt_pdf_strategy() -> str:
    """
    Prompt user to select PDF layout strategy.

    Interactive prompt with two options:
        [1] Single Column - Fast extraction with pdfplumber
        [2] Double Column - Slow AI extraction with marker-pdf

    Returns:
        Strategy string: 'fast' or 'deep'

    Example:
        >>> strategy = prompt_pdf_strategy()
        >>> # User sees prompt and types '1' or '2'
        >>> print(strategy)  # 'fast' or 'deep'
    """
    console.print("\n[bold cyan]I found PDFs in this folder. How are they formatted?[/bold cyan]\n")

    # Display options with emoji indicators
    console.print("  [1] Single Column (Standard Lexis/Modern) - FAST ⚡️")
    console.print("  [2] Double Column (Old Lexis/Medical) - SLOW (Uses AI) 🐢\n")

    # Prompt with validation (only accept '1' or '2')
    while True:
        choice = click.prompt(
            "Your choice",
            type=click.Choice(["1", "2"], case_sensitive=False),
            show_choices=False,  # We already showed choices above
        )

        # Map choice to strategy
        if choice == "1":
            return "fast"
        elif choice == "2":
            return "deep"
        else:
            # This shouldn't happen due to click.Choice validation, but just in case
            console.print("[red]Invalid choice. Please enter 1 or 2.[/red]")


def show_educational_warning():
    """
    Display educational warning about double-column PDF processing.

    Shows a rich Panel with yellow border explaining:
        - Double-column processing is slow (uses AI)
        - Pro tip: Download single-column or Word format from Lexis next time

    This helps users make better choices in future downloads.
    """
    warning_text = (
        "Double-column processing uses complex AI and will take longer.\n\n"
        "[bold]PRO TIP:[/bold] Next time you download from Lexis, choose "
        "'Microsoft Word' or 'Single Column PDF' for instant processing."
    )

    console.print()  # Blank line for spacing
    console.print(
        Panel(
            warning_text,
            title="⚠️  Important Note",
            border_style="yellow",
            padding=(1, 2),  # (vertical, horizontal) padding
        )
    )
    console.print()  # Blank line after warning


# ============================================================================
# MAIN CLI COMMAND
# ============================================================================

@click.command()
@click.argument(
    "folder_path",
    type=click.Path(exists=True, path_type=Path),
)
def main(folder_path: Path):
    """
    Interactive document processor.

    Scans FOLDER_PATH for PDF and DOCX files, then processes them with
    the appropriate extraction strategy.

    \b
    Decision Tree:
        - Only DOCX files: Run immediately with fast strategy (no prompt)
        - PDFs present: Prompt user to select layout type
            - Single column → fast strategy (pdfplumber)
            - Double column → deep strategy (marker-pdf AI)

    \b
    Examples:
        python main.py ~/Downloads/lexis-cases
        python main.py /path/to/documents

    \b
    Supported File Types:
        - PDF (.pdf)
        - Microsoft Word (.docx)

    Note: Scans recursively through all subdirectories.
    """
    # Header
    console.print("\n[bold]Document Processor - Interactive Mode[/bold]\n")

    # Step 1: Scan folder
    console.print(f"[bold cyan]Scanning folder:[/bold cyan] {folder_path}")
    console.print(f"[dim](scanning recursively...)[/dim]\n")

    scan_result = scan_folder(folder_path)

    # Display scan results
    console.print(
        f"Found [bold]{scan_result['pdf_count']}[/bold] PDF files, "
        f"[bold]{scan_result['docx_count']}[/bold] DOCX files\n"
    )

    # Step 2: Decision Tree - Handle different scenarios

    # Scenario A: No supported files found
    if scan_result["total_count"] == 0:
        console.print("[red]✗ No supported files found in folder.[/red]")
        console.print("[dim]Supported formats: .pdf, .docx[/dim]\n")
        sys.exit(1)

    # Scenario B: Only DOCX files (no PDFs)
    if scan_result["pdf_count"] == 0 and scan_result["docx_count"] > 0:
        console.print("[green]✓[/green] Only DOCX files detected. Running with fast strategy...\n")
        strategy = "fast"

    # Scenario C: PDFs present (with or without DOCX)
    elif scan_result["pdf_count"] > 0:
        # Prompt user for PDF layout strategy
        strategy = prompt_pdf_strategy()

        # If user chose deep mode, show educational warning
        if strategy == "deep":
            show_educational_warning()

    else:
        # This shouldn't happen, but handle gracefully
        console.print("[red]✗ Unexpected error during file scan.[/red]\n")
        sys.exit(1)

    # Step 3: Process batch with selected strategy
    console.print(f"[bold cyan]Processing documents with '{strategy}' strategy...[/bold cyan]\n")

    process_batch(folder_path, strategy)

    # Success
    console.print("\n[green]✓ Processing complete![/green]\n")
    sys.exit(0)


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    main()
