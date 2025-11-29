#!/usr/bin/env python3
"""
Smoke Test - Rename Workflow

Test the atomic rename operation end-to-end.

Workflow tested:
    1. Extract text from PDF
    2. Classify document type (caselaw)
    3. Extract metadata (case_name, year, court, citation)
    4. Allocate unique code
    5. Format filename
    6. Rename file (dry-run mode)
    7. Record in registry

Usage:
    python smoke_test_rename.py
    python smoke_test_rename.py --verbose
    python smoke_test_rename.py --file path/to/case.pdf

Expected Output (Indian_Trail.pdf):
    Old:  2014-None-915_Indian_Trail.pdf
    New:  c.Ga_Ct_App__2014__Indian-Trail-v-State-Bank__328_GaApp_524----AAAAA.pdf
    Code: AAAAA
    Type: CASELAW
"""

import sys
from pathlib import Path
import shutil

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.steps.rename_step import RenameStep
from src.services.registrar import Registrar

console = Console()


# ============================================================================
# VALIDATION
# ============================================================================

def validate_rename_result(result, verbose: bool = False) -> dict[str, bool]:
    """
    Validate rename result against expected values.

    Args:
        result: RenameResult from rename_step
        verbose: Show detailed validation output

    Returns:
        Dictionary of validation results {check: passed}
    """
    checks = {}

    # Check 1: Success status
    checks["success"] = result.success

    if verbose:
        console.print(f"\n[bold]Success Validation:[/bold]")
        console.print(f"  Status: {'✓ PASS' if checks['success'] else '✗ FAIL'}")
        if not checks["success"]:
            console.print(f"  Error: {result.error_message}")

    # Check 2: Document type
    checks["document_type"] = (result.document_type is not None and
                                result.document_type.value == "caselaw")

    if verbose:
        console.print(f"\n[bold]Document Type Validation:[/bold]")
        console.print(f"  Expected: CASELAW")
        console.print(f"  Found: {result.document_type.value if result.document_type else 'None'}")
        console.print(f"  Status: {'✓ PASS' if checks['document_type'] else '✗ FAIL'}")

    # Check 3: Unique code allocated
    checks["unique_code"] = (result.unique_code is not None and
                             len(result.unique_code) == 5 and
                             'W' not in result.unique_code)

    if verbose:
        console.print(f"\n[bold]Unique Code Validation:[/bold]")
        console.print(f"  Expected: 5 uppercase letters (no 'W')")
        console.print(f"  Found: {result.unique_code}")
        console.print(f"  Status: {'✓ PASS' if checks['unique_code'] else '✗ FAIL'}")

    # Check 4: Filename format
    if result.new_name:
        # Check prefix
        has_prefix = result.new_name.startswith("c.")

        # Check components (split by __)
        parts = result.new_name.replace("c.", "").split("__")
        has_4_parts = len(parts) == 4  # court, year, case_name, citation----CODE.ext

        # Check code separator (----)
        has_code_sep = "----" in result.new_name

        # Check court contains expected value
        has_ga = "Ga" in result.new_name or "Georgia" in result.new_name

        # Check year
        has_2014 = "2014" in result.new_name

        # Check case name components
        has_indian_trail = "Indian" in result.new_name and "Trail" in result.new_name
        has_state_bank = "State" in result.new_name and "Bank" in result.new_name

        # Check citation (formatted with underscores: 328_Ga_App_524)
        has_citation = "328" in result.new_name and ("Ga_App" in result.new_name or "GaApp" in result.new_name)

        checks["filename_format"] = all([
            has_prefix, has_4_parts, has_code_sep, has_ga, has_2014,
            has_indian_trail, has_state_bank, has_citation
        ])

        if verbose:
            console.print(f"\n[bold]Filename Format Validation:[/bold]")
            console.print(f"  Filename: {result.new_name}")
            console.print(f"  ✓ Prefix 'c.': {has_prefix}")
            console.print(f"  ✓ 4 components: {has_4_parts}")
            console.print(f"  ✓ Code separator '----': {has_code_sep}")
            console.print(f"  ✓ Court (Ga): {has_ga}")
            console.print(f"  ✓ Year (2014): {has_2014}")
            console.print(f"  ✓ Case name (Indian Trail): {has_indian_trail}")
            console.print(f"  ✓ Case name (State Bank): {has_state_bank}")
            console.print(f"  ✓ Citation (328 GaApp): {has_citation}")
            console.print(f"  Status: {'✓ PASS' if checks['filename_format'] else '✗ FAIL'}")
    else:
        checks["filename_format"] = False

        if verbose:
            console.print(f"\n[red]✗ Filename not generated[/red]")

    return checks


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
    help="Show detailed validation output",
)
@click.option(
    "--cleanup",
    is_flag=True,
    help="Delete test database after run",
)
def main(file: Path, verbose: bool, cleanup: bool):
    """
    Smoke test for rename workflow.

    Tests atomic rename operation: extract → classify → metadata → code → format → rename.
    """
    console.print("\n[bold]Smoke Test - Rename Workflow[/bold]\n")

    # Setup test registry
    test_db = Path("registry/test_rename.db")
    if test_db.exists():
        test_db.unlink()
        for suffix in ["-wal", "-shm"]:
            wal_file = Path(str(test_db) + suffix)
            if wal_file.exists():
                wal_file.unlink()

    registrar = Registrar(test_db)

    # Create rename step (dry-run mode)
    step = RenameStep(registrar=registrar, dry_run=True, max_pages=3)

    # Display input file
    console.print(f"[bold cyan]Input File:[/bold cyan] {file.name}")
    console.print(f"[dim]Full path: {file}[/dim]\n")

    # Process file
    console.print("[bold cyan]Processing...[/bold cyan]\n")

    result = step.process_file(file)

    # Display results
    console.print("[bold]Results:[/bold]\n")

    if result.success:
        # Success table
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Old Name", result.old_name)
        table.add_row("New Name", result.new_name or "N/A")
        table.add_row("Document Type", result.document_type.value if result.document_type else "N/A")
        table.add_row("Unique Code", result.unique_code or "N/A")
        table.add_row("Confidence", result.confidence or "N/A")

        console.print(table)

        # Notes
        if verbose and result.notes:
            console.print(f"\n[bold]Processing Notes:[/bold]")
            for note in result.notes:
                console.print(f"  • {note}")

    else:
        console.print(f"[red]✗ Processing failed: {result.error_message}[/red]")

        if verbose and result.notes:
            console.print(f"\n[bold]Processing Notes:[/bold]")
            for note in result.notes:
                console.print(f"  • {note}")

    # Validation
    console.print(f"\n[bold cyan]Validation:[/bold cyan]\n")

    checks = validate_rename_result(result, verbose=verbose)

    # Summary table
    summary_table = Table(show_header=True, header_style="bold cyan")
    summary_table.add_column("Check", style="cyan")
    summary_table.add_column("Status", justify="center")

    for check_name, passed in checks.items():
        status = "[green]✓ PASS[/green]" if passed else "[red]✗ FAIL[/red]"
        summary_table.add_row(check_name.replace("_", " ").title(), status)

    console.print(summary_table)

    # Overall result
    passed_count = sum(checks.values())
    total_count = len(checks)

    console.print(f"\n[bold]Results:[/bold] {passed_count}/{total_count} checks passed")

    # Cleanup
    step.close()
    registrar.close()

    if cleanup:
        console.print(f"\n[bold cyan]Cleaning up test database...[/bold cyan]")
        if test_db.exists():
            test_db.unlink()
        for suffix in ["-wal", "-shm"]:
            wal_file = Path(str(test_db) + suffix)
            if wal_file.exists():
                wal_file.unlink()
        console.print("[green]Test database deleted[/green]")

    # Exit code
    if passed_count == total_count:
        console.print("\n[green]✓ All checks passed![/green]\n")
        sys.exit(0)
    else:
        console.print(f"\n[red]✗ {total_count - passed_count} check(s) failed[/red]\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
