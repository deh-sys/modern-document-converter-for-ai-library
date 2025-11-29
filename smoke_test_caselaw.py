#!/usr/bin/env python3
"""
Smoke Test - Caselaw Metadata Extractor

Test metadata extraction from legal case documents.

Usage:
    python smoke_test_caselaw.py
    python smoke_test_caselaw.py --verbose
    python smoke_test_caselaw.py --file path/to/case.pdf

Features:
    - Extract text from PDF
    - Run CaselawProcessor
    - Display extracted metadata
    - Validate extraction quality

Test File:
    Default: z-test-files--caselaw/2014-None-915_Indian_Trail.pdf

Expected Extractions:
    - Case name: "915 Indian Trail, LLC v. State Bank and Trust Company"
    - Year: "2014"
    - Court: "Ga. Ct. App." (Court of Appeals of Georgia)
    - Citation: "328 Ga. App. 524" or "759 S.E.2d 654"
"""

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax

from src.services.text_extractor import extract_text
from src.plugins.caselaw import CaselawProcessor

console = Console()


# ============================================================================
# VALIDATION
# ============================================================================

def validate_extraction(metadata, verbose: bool = False) -> dict[str, bool]:
    """
    Validate extracted metadata against expected values.

    Args:
        metadata: DocumentMetadata from CaselawProcessor
        verbose: Show detailed validation output

    Returns:
        Dictionary of validation results {field: passed}
    """
    results = {}

    # Validate case name
    case_name = metadata.fields.get("case_name")
    if case_name:
        case_name_value = case_name.value.lower()
        has_plaintiff = "915 indian trail" in case_name_value or "indian trail" in case_name_value
        has_defendant = "state bank" in case_name_value

        results["case_name"] = has_plaintiff and has_defendant

        if verbose:
            console.print(f"\n[bold]Case Name Validation:[/bold]")
            console.print(f"  Expected: '915 Indian Trail' and 'State Bank'")
            console.print(f"  Found: {case_name.value}")
            console.print(f"  Status: {'✓ PASS' if results['case_name'] else '✗ FAIL'}")
    else:
        results["case_name"] = False
        if verbose:
            console.print(f"\n[red]✗ Case name not extracted[/red]")

    # Validate year
    year = metadata.fields.get("year")
    if year:
        results["year"] = year.value == "2014"

        if verbose:
            console.print(f"\n[bold]Year Validation:[/bold]")
            console.print(f"  Expected: '2014'")
            console.print(f"  Found: {year.value}")
            console.print(f"  Status: {'✓ PASS' if results['year'] else '✗ FAIL'}")
    else:
        results["year"] = False
        if verbose:
            console.print(f"\n[red]✗ Year not extracted[/red]")

    # Validate court
    court = metadata.fields.get("court")
    if court:
        court_value = court.value.lower()
        has_georgia = "ga" in court_value or "georgia" in court_value

        results["court"] = has_georgia

        if verbose:
            console.print(f"\n[bold]Court Validation:[/bold]")
            console.print(f"  Expected: Contains 'Ga' (Georgia)")
            console.print(f"  Found: {court.value}")
            console.print(f"  Status: {'✓ PASS' if results['court'] else '✗ FAIL'}")
    else:
        results["court"] = False
        if verbose:
            console.print(f"\n[red]✗ Court not extracted[/red]")

    # Validate citation
    citation = metadata.fields.get("citation")
    if citation:
        citation_value = citation.value
        has_ga_app = "328" in citation_value and "Ga. App." in citation_value
        has_se2d = "759" in citation_value and "S.E.2d" in citation_value

        results["citation"] = has_ga_app or has_se2d

        if verbose:
            console.print(f"\n[bold]Citation Validation:[/bold]")
            console.print(f"  Expected: '328 Ga. App.' or '759 S.E.2d'")
            console.print(f"  Found: {citation.value}")
            console.print(f"  Status: {'✓ PASS' if results['citation'] else '✗ FAIL'}")
    else:
        results["citation"] = False
        if verbose:
            console.print(f"\n[red]✗ Citation not extracted[/red]")

    return results


# ============================================================================
# CLI
# ============================================================================

@click.command()
@click.option(
    "--file",
    type=click.Path(exists=True, path_type=Path),
    default=Path("z-test-files--caselaw/2014-None-915_Indian_Trail.pdf"),
    help="PDF file to test (default: Indian_Trail.pdf)",
)
@click.option(
    "--verbose",
    is_flag=True,
    help="Show detailed extraction and validation output",
)
@click.option(
    "--max-pages",
    type=int,
    default=3,
    help="Maximum pages to extract (default: 3)",
)
def main(file: Path, verbose: bool, max_pages: int):
    """
    Smoke test for caselaw metadata extraction.

    Tests CaselawProcessor against a known case document.
    """
    console.print("\n[bold]Smoke Test - Caselaw Metadata Extractor[/bold]\n")

    # ========================================================================
    # STEP 1: Extract Text
    # ========================================================================

    console.print("[bold cyan]Step 1: Extracting text from PDF...[/bold cyan]")

    if verbose:
        console.print(f"  File: {file}")
        console.print(f"  Max pages: {max_pages}")

    result = extract_text(file, max_pages=max_pages)

    if not result.success:
        console.print(f"[red]✗ Text extraction failed: {result.error_message}[/red]\n")
        sys.exit(1)

    text = result.text
    char_count = len(text)

    console.print(f"[green]✓[/green] Extracted {char_count:,} characters from {file.name}")

    if verbose:
        console.print(f"\n[dim]First 500 characters:[/dim]")
        console.print(Panel(text[:500], border_style="dim"))

    # ========================================================================
    # STEP 2: Extract Metadata
    # ========================================================================

    console.print("\n[bold cyan]Step 2: Extracting metadata...[/bold cyan]")

    processor = CaselawProcessor()
    metadata = processor.extract_metadata(text)

    field_count = len(metadata.fields)
    console.print(f"[green]✓[/green] Extracted {field_count} metadata fields")

    # Display metadata
    console.print("\n[bold]Extracted Metadata:[/bold]\n")

    if metadata.fields:
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="green")
        table.add_column("Confidence", justify="center")
        table.add_column("Method", style="dim")

        for field_name, field_data in metadata.fields.items():
            table.add_row(
                field_name,
                field_data.value,
                field_data.confidence.value if hasattr(field_data.confidence, 'value') else str(field_data.confidence),
                field_data.extractor_name or "N/A"
            )

        console.print(table)
    else:
        console.print("[red]No metadata extracted[/red]")

    # ========================================================================
    # STEP 3: Validate Extraction
    # ========================================================================

    console.print("\n[bold cyan]Step 3: Validating extraction...[/bold cyan]")

    validation = validate_extraction(metadata, verbose=verbose)

    # Summary table
    console.print("\n[bold]Validation Summary:[/bold]\n")

    summary_table = Table(show_header=True, header_style="bold cyan")
    summary_table.add_column("Field", style="cyan")
    summary_table.add_column("Status", justify="center")

    for field, passed in validation.items():
        status = "[green]✓ PASS[/green]" if passed else "[red]✗ FAIL[/red]"
        summary_table.add_row(field, status)

    console.print(summary_table)

    # Overall result
    passed_count = sum(validation.values())
    total_count = len(validation)

    console.print(f"\n[bold]Results:[/bold] {passed_count}/{total_count} validations passed")

    if passed_count == total_count:
        console.print("\n[green]✓ All validations passed![/green]\n")
        sys.exit(0)
    else:
        console.print(f"\n[red]✗ {total_count - passed_count} validation(s) failed[/red]\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
