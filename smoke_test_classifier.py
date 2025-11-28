#!/usr/bin/env python3
"""
Smoke Test - Document Classifier

Manual testing script for document classification service.
Extracts text from a file and classifies its document type.

Usage:
    python smoke_test_classifier.py /path/to/file.pdf
    python smoke_test_classifier.py /path/to/file.pdf --show-scores
    python smoke_test_classifier.py /path/to/file.pdf --json-output

Features:
    - Extracts text using text_extractor service
    - Classifies using classifier service
    - Shows matched patterns and confidence
    - Optional: Show scores for all document types

Examples:
    # Basic classification
    python smoke_test_classifier.py z-test-files--caselaw/Indian_Trail.pdf

    # Show all type scores (debugging)
    python smoke_test_classifier.py z-test-files--caselaw/Indian_Trail.pdf --show-scores

    # JSON output (for scripting)
    python smoke_test_classifier.py file.pdf --json-output
"""

import json
import sys
from pathlib import Path

import click
from rich import print as rprint
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax

from src.services.text_extractor import extract_text
from src.services.classifier import classify, get_all_scores
from src.core.models import Classification, ConfidenceLevel


console = Console()


@click.command()
@click.argument(
    "file_path",
    type=click.Path(exists=True, path_type=Path),
    required=True,
)
@click.option(
    "--show-scores",
    is_flag=True,
    help="Show scores for all document types (debugging)",
)
@click.option(
    "--json-output",
    is_flag=True,
    help="Output raw JSON instead of pretty-printed",
)
@click.option(
    "--max-pages",
    type=int,
    default=None,
    help="Maximum pages to extract for classification (faster)",
)
def main(
    file_path: Path,
    show_scores: bool,
    json_output: bool,
    max_pages: int,
):
    """
    Smoke test for document classifier.

    Extracts text from FILE_PATH and classifies document type.
    """
    console.print(f"\n[bold cyan]Extracting text from:[/bold cyan] {file_path}")

    # Step 1: Extract text
    extraction_result = extract_text(file_path, max_pages=max_pages)

    if not extraction_result.success:
        console.print(f"\n[bold red]✗ Extraction failed:[/bold red] {extraction_result.error_message}")
        sys.exit(1)

    console.print(f"[dim]Extracted {len(extraction_result.text)} characters from {extraction_result.page_count} pages[/dim]\n")

    # Step 2: Classify document
    console.print("[bold cyan]Classifying document...[/bold cyan]\n")

    classification: Classification = classify(extraction_result.text)

    # Output mode: JSON or pretty-printed
    if json_output:
        _output_json(classification, extraction_result, file_path)
    else:
        _display_pretty_result(classification, extraction_result, file_path, show_scores)

    # Exit code: 0 if classified (even if UNKNOWN), 1 if error
    sys.exit(0)


def _output_json(classification: Classification, extraction_result, file_path: Path):
    """Output classification result as JSON."""
    result = {
        "file_path": str(file_path),
        "extraction": {
            "success": extraction_result.success,
            "page_count": extraction_result.page_count,
            "text_length": len(extraction_result.text),
        },
        "classification": {
            "document_type": classification.document_type.value,
            "confidence": classification.confidence,
            "confidence_percent": f"{classification.confidence * 100:.1f}",
            "indicators": classification.indicators,
        },
    }

    print(json.dumps(result, indent=2))


def _display_pretty_result(
    classification: Classification,
    extraction_result,
    file_path: Path,
    show_all_scores: bool,
):
    """Display classification result with rich formatting."""

    # Classification result panel
    doc_type = classification.document_type.value.upper()
    confidence_pct = classification.confidence * 100

    # Determine confidence level color
    if confidence_pct >= 60:
        confidence_color = "green"
        confidence_text = "HIGH"
    elif confidence_pct >= 30:
        confidence_color = "yellow"
        confidence_text = "MEDIUM"
    elif confidence_pct >= 10:
        confidence_color = "blue"
        confidence_text = "LOW"
    else:
        confidence_color = "red"
        confidence_text = "VERY LOW"

    result_text = f"""[bold]Document Type:[/bold] {doc_type}
[bold]Confidence:[/bold] [{confidence_color}]{confidence_text}[/{confidence_color}] ({confidence_pct:.1f}/100)
[bold]Score:[/bold] {confidence_pct:.1f} points"""

    console.print(Panel(result_text, title="Classification Result", border_style=confidence_color))

    # Matched patterns
    if classification.indicators:
        console.print("\n[bold]Matched Patterns:[/bold]")
        for indicator in classification.indicators:
            console.print(f"  [green]✓[/green] {indicator}")
    else:
        console.print("\n[bold yellow]No patterns matched[/bold yellow]")

    # Show all scores (debugging mode)
    if show_all_scores:
        console.print("\n[bold]All Document Type Scores:[/bold]")

        scores = get_all_scores(extraction_result.text)

        if scores:
            table = Table(show_header=True, header_style="bold cyan")
            table.add_column("Document Type", style="cyan")
            table.add_column("Score", justify="right")
            table.add_column("Matched Patterns", style="dim")

            for type_name, (score, indicators) in sorted(
                scores.items(), key=lambda x: x[1][0], reverse=True
            ):
                indicators_str = f"{len(indicators)} patterns" if indicators else "none"
                table.add_row(
                    type_name.upper(),
                    f"{score:.1f}",
                    indicators_str,
                )

            console.print(table)

            # Detailed indicators for each type
            console.print("\n[bold]Detailed Pattern Matches:[/bold]")
            for type_name, (score, indicators) in sorted(
                scores.items(), key=lambda x: x[1][0], reverse=True
            ):
                if indicators:
                    console.print(f"\n[cyan]{type_name.upper()}[/cyan] ({score:.1f} points):")
                    for indicator in indicators:
                        console.print(f"  • {indicator}")
        else:
            console.print("[dim]No scores available[/dim]")

    # Summary
    console.print("\n[bold]Summary:[/bold]")
    console.print(f"  File: {file_path.name}")
    console.print(f"  Size: {len(extraction_result.text):,} characters")
    console.print(f"  Type: [cyan]{doc_type}[/cyan]")
    console.print(f"  Confidence: [{confidence_color}]{confidence_pct:.1f}%[/{confidence_color}]")

    # Recommendation based on confidence
    if classification.document_type.value == "unknown":
        console.print("\n[yellow]⚠ Document type could not be determined[/yellow]")
        console.print("[dim]This file might be a type not yet configured (statute, brief, book, etc.)[/dim]")
    elif confidence_pct < 30:
        console.print(f"\n[yellow]⚠ Low confidence classification[/yellow]")
        console.print(f"[dim]Manual review recommended[/dim]")
    elif confidence_pct >= 60:
        console.print(f"\n[green]✓ High confidence - document is likely {doc_type}[/green]")


if __name__ == "__main__":
    main()
