#!/usr/bin/env python3
"""
Smoke Test - Document Conversion

Test the convert_step pipeline end-to-end.

Features:
    - Tests extraction → normalization → cleaning → frontmatter → save
    - Validates YAML frontmatter format
    - Validates noise pattern removal
    - Validates markdown heading detection
    - Shows cleaning statistics
    - Supports both fast and deep strategies

Usage:
    python smoke_test_convert.py /path/to/document.pdf
    python smoke_test_convert.py /path/to/document.pdf --strategy deep
    python smoke_test_convert.py /path/to/document.pdf --dry-run
    python smoke_test_convert.py /path/to/document.pdf --cleanup

Expected Output:
    - Creates document.txt in same directory as source
    - Contains YAML frontmatter with metadata
    - Removes Lexis noise (As of:, Page X of Y, etc.)
    - Adds markdown headings (##, ###)

Example:
    python smoke_test_convert.py z-test-files--caselaw/2014-None-915_Indian_Trail.pdf
"""

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.steps.convert_step import ConvertStep
from src.services.registrar import Registrar


console = Console()


# ============================================================================
# VALIDATION
# ============================================================================

def validate_conversion_result(result, verbose: bool = False) -> dict[str, bool]:
    """
    Validate conversion result against expected criteria.

    Args:
        result: ConvertResult from convert_step
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

    if not result.success:
        return checks

    # Check 2: Output file created
    if result.output_file:
        output_path = Path(result.output_file)
        checks["output_exists"] = output_path.exists()
    else:
        checks["output_exists"] = False

    if verbose:
        console.print(f"\n[bold]Output File Validation:[/bold]")
        console.print(f"  File: {result.output_file or 'N/A'}")
        console.print(f"  Exists: {'✓ PASS' if checks['output_exists'] else '✗ FAIL'}")

    # Check 3: Validate frontmatter (if output exists)
    if checks["output_exists"]:
        output_path = Path(result.output_file)
        content = output_path.read_text(encoding='utf-8')

        # Check for YAML delimiters
        has_frontmatter = content.startswith('---\n') and '\n---\n' in content

        # Check for required fields
        has_type = 'type:' in content.split('---')[1]
        has_source = 'source_file:' in content.split('---')[1]

        checks["frontmatter"] = has_frontmatter and has_type and has_source

        if verbose:
            console.print(f"\n[bold]Frontmatter Validation:[/bold]")
            console.print(f"  Has YAML delimiters (---): {has_frontmatter}")
            console.print(f"  Has 'type' field: {has_type}")
            console.print(f"  Has 'source_file' field: {has_source}")
            console.print(f"  Status: {'✓ PASS' if checks['frontmatter'] else '✗ FAIL'}")

        # Check 4: Validate noise removal
        # These patterns should NOT appear in cleaned text
        noise_indicators = ['As of:', 'Page ', ' of ', 'Load Date:', 'End of Document']
        has_noise = any(indicator in content for indicator in noise_indicators)
        checks["noise_removed"] = not has_noise

        if verbose:
            console.print(f"\n[bold]Noise Removal Validation:[/bold]")
            console.print(f"  Noise patterns found: {has_noise}")
            console.print(f"  Status: {'✓ PASS' if checks['noise_removed'] else '✗ FAIL'}")

    return checks


# ============================================================================
# CLI
# ============================================================================

@click.command()
@click.argument(
    "file_path",
    type=click.Path(exists=True, path_type=Path),
)
@click.option(
    "--strategy",
    type=click.Choice(['fast', 'deep'], case_sensitive=False),
    default='fast',
    help="Extraction strategy (default: fast)",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Don't write output files or update registry",
)
@click.option(
    "--cleanup",
    is_flag=True,
    help="Delete test database and output .txt file after run",
)
@click.option(
    "--verbose",
    is_flag=True,
    help="Show detailed validation output",
)
def main(
    file_path: Path,
    strategy: str,
    dry_run: bool,
    cleanup: bool,
    verbose: bool,
):
    """
    Smoke test for document conversion pipeline.

    Tests: extract → classify → normalize → clean → frontmatter → save
    """
    console.print("\n[bold]Smoke Test - Document Conversion[/bold]\n")

    # Setup test registry
    test_db = Path("registry/test_convert.db")
    if test_db.exists():
        test_db.unlink()
        for suffix in ["-wal", "-shm"]:
            wal_file = Path(str(test_db) + suffix)
            if wal_file.exists():
                wal_file.unlink()

    registrar = Registrar(test_db)

    # Create convert step
    step = ConvertStep(
        registrar=registrar,
        strategy=strategy,
        dry_run=dry_run,
    )

    # Display input file and settings
    console.print(f"[bold cyan]Input File:[/bold cyan] {file_path.name}")
    console.print(f"[dim]Full path: {file_path}[/dim]")
    console.print(f"[dim]Strategy: {strategy}[/dim]")
    console.print(f"[dim]Dry-run: {dry_run}[/dim]\n")

    # Process file
    console.print("[bold cyan]Processing...[/bold cyan]\n")

    result = step.process_file(file_path)

    # Display results
    console.print("[bold]Results:[/bold]\n")

    if result.success:
        # Success table
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Source File", result.source_file)
        table.add_row("Output File", result.output_file or "N/A (dry-run)")
        table.add_row("Document Type", result.document_type.value if result.document_type else "N/A")
        table.add_row("Character Count", str(result.character_count))
        table.add_row("Lines Removed", str(result.lines_removed))
        table.add_row("Headings Added", str(result.headings_added))
        table.add_row("Processing Time", f"{result.processing_time:.2f}s" if result.processing_time else "N/A")

        console.print(table)

        # Preview output file content (if exists)
        if result.output_file and Path(result.output_file).exists():
            console.print(f"\n[bold]Output Preview:[/bold]\n")

            content = Path(result.output_file).read_text(encoding='utf-8')
            preview_lines = content.split('\n')[:25]  # First 25 lines
            preview = '\n'.join(preview_lines)

            if len(content.split('\n')) > 25:
                preview += f"\n\n... [dim][{len(content.split('\n')) - 25} more lines][/dim]"

            console.print(Panel(preview, border_style="blue"))

    else:
        console.print(f"[red]✗ Processing failed: {result.error_message}[/red]")

    # Validation
    if result.success and result.output_file:
        console.print(f"\n[bold cyan]Validation:[/bold cyan]\n")

        checks = validate_conversion_result(result, verbose=verbose)

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
        console.print(f"\n[bold cyan]Cleaning up...[/bold cyan]")

        # Delete test database
        if test_db.exists():
            test_db.unlink()
        for suffix in ["-wal", "-shm"]:
            wal_file = Path(str(test_db) + suffix)
            if wal_file.exists():
                wal_file.unlink()

        # Delete output .txt file
        if result.output_file and Path(result.output_file).exists():
            Path(result.output_file).unlink()
            console.print(f"[green]Deleted output file: {result.output_file}[/green]")

        console.print("[green]Test database deleted[/green]")

    # Exit code
    if result.success:
        console.print("\n[green]✓ Conversion successful![/green]\n")
        sys.exit(0)
    else:
        console.print(f"\n[red]✗ Conversion failed[/red]\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
