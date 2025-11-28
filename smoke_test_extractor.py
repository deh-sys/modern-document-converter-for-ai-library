#!/usr/bin/env python3
"""
Smoke Test - Text Extractor

Manual testing script for text extraction service.
Provides immediate feedback during development.

Usage:
    python smoke_test_extractor.py /path/to/file.pdf
    python smoke_test_extractor.py /path/to/file.pdf --max-pages 2
    python smoke_test_extractor.py /path/to/file.docx --no-normalize

Features:
    - Pretty-printed JSON output (rich formatting)
    - Shows complete ExtractionResult model
    - Handles errors gracefully
    - Quick iteration during development

Examples:
    # Test PDF extraction
    python smoke_test_extractor.py step1a/sample_files/sample.pdf

    # Test DOCX extraction
    python smoke_test_extractor.py step1b/z_sample_articles/article.pdf

    # Limit pages
    python smoke_test_extractor.py large_file.pdf --max-pages 3

    # Skip normalization (see raw text)
    python smoke_test_extractor.py file.pdf --no-normalize
"""

import json
import sys
from pathlib import Path
from typing import Optional

import click
from rich import print as rprint
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from src.services.text_extractor import extract_text
from src.core.models import ExtractionResult


console = Console()


@click.command()
@click.argument(
    "file_path",
    type=click.Path(exists=True, path_type=Path),
    required=True,
)
@click.option(
    "--max-pages",
    type=int,
    default=None,
    help="Maximum number of pages to extract (PDF only)",
)
@click.option(
    "--normalize/--no-normalize",
    default=True,
    help="Whether to normalize extracted text (default: yes)",
)
@click.option(
    "--preview-length",
    type=int,
    default=500,
    help="Max characters of text to show in preview (default: 500)",
)
@click.option(
    "--json-output",
    is_flag=True,
    help="Output raw JSON instead of pretty-printed",
)
def main(
    file_path: Path,
    max_pages: Optional[int],
    normalize: bool,
    preview_length: int,
    json_output: bool,
):
    """
    Smoke test for text extraction service.

    Extracts text from FILE_PATH and displays the ExtractionResult as JSON.
    """
    console.print(f"\n[bold cyan]Extracting text from:[/bold cyan] {file_path}")

    if max_pages:
        console.print(f"[dim]Max pages: {max_pages}[/dim]")

    console.print(f"[dim]Normalize: {normalize}[/dim]\n")

    # Extract text
    result: ExtractionResult = extract_text(
        file_path=file_path,
        max_pages=max_pages,
        normalize=normalize,
    )

    # Convert to dict for JSON output
    result_dict = result.model_dump()

    # Truncate text for display (full text in JSON)
    if result.success and len(result.text) > preview_length:
        preview_text = result.text[:preview_length] + f"... [truncated, {len(result.text)} chars total]"
        result_dict["text_preview"] = preview_text
        result_dict["text_length"] = len(result.text)
    elif result.success:
        result_dict["text_preview"] = result.text
        result_dict["text_length"] = len(result.text)

    # Output mode: JSON or pretty-printed
    if json_output:
        # Raw JSON output (for scripting)
        print(json.dumps(result_dict, indent=2))
    else:
        # Pretty-printed with rich
        _display_pretty_result(result, result_dict, preview_length)

    # Exit code: 0 if success, 1 if failed
    sys.exit(0 if result.success else 1)


def _display_pretty_result(
    result: ExtractionResult,
    result_dict: dict,
    preview_length: int,
):
    """Display extraction result with rich formatting."""

    # Status panel
    if result.success:
        status_text = "[bold green]✓ SUCCESS[/bold green]"
        status_color = "green"
    else:
        status_text = "[bold red]✗ FAILED[/bold red]"
        status_color = "red"

    console.print(Panel(status_text, border_style=status_color))

    # Metadata
    console.print("\n[bold]Extraction Metadata:[/bold]")
    console.print(f"  Success: [{'green' if result.success else 'red'}]{result.success}[/]")
    console.print(f"  Page Count: {result.page_count or 'N/A'}")

    if result.error_message:
        console.print(f"  Error: [red]{result.error_message}[/red]")

    # Text preview
    if result.success and result.text:
        console.print("\n[bold]Text Preview:[/bold]")
        preview = result.text[:preview_length]

        if len(result.text) > preview_length:
            preview += f"\n\n... [dim][truncated, {len(result.text)} total characters][/dim]"

        console.print(Panel(preview, border_style="blue"))

        # Character count
        console.print(f"\n[dim]Total characters extracted: {len(result.text)}[/dim]")
        console.print(f"[dim]Total words (approx): {len(result.text.split())}[/dim]")

    # Full JSON
    console.print("\n[bold]Full ExtractionResult (JSON):[/bold]")

    # Create JSON with syntax highlighting
    json_str = json.dumps(result_dict, indent=2)
    syntax = Syntax(json_str, "json", theme="monokai", line_numbers=False)
    console.print(syntax)


if __name__ == "__main__":
    main()
