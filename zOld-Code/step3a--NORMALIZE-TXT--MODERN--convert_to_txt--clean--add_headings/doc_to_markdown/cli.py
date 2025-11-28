"""Command-line interface for document to markdown converter."""

from pathlib import Path
import sys

import click
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt

from .processor import BatchProcessor
from .file_detector import FileTypeDetector
from .file_status import FileStatus


console = Console()


def _prompt_id_code_verification():
    """Prompt user to verify if files have corrected names with ID codes."""
    console.print("[bold]Do these files have corrected names with ID codes?[/bold]\n")
    console.print("  1) Yes")
    console.print("  2) No, but convert to MD anyway")
    console.print()

    choice = Prompt.ask(
        "Enter your choice",
        choices=["1", "2"],
        default="1",
        show_default=True
    )

    if choice == "1":
        console.print("[green]✓ Files have corrected names with ID codes[/green]\n")
    else:
        console.print("[yellow]⚠ Proceeding without corrected names and ID codes[/yellow]\n")


@click.command()
@click.argument(
    'path',
    type=click.Path(exists=True, path_type=Path),
    required=True
)
@click.option(
    '--recursive', '-r',
    is_flag=True,
    help='Process directories recursively'
)
@click.option(
    '--yes', '-y',
    is_flag=True,
    help='Auto-confirm prompts (process new and modified files)'
)
@click.option(
    '--no-images',
    is_flag=True,
    help='Do not extract images (text only)'
)
@click.option(
    '--verbose', '-v',
    is_flag=True,
    help='Show detailed processing information'
)
def main(
    path: Path,
    recursive: bool,
    yes: bool,
    no_images: bool,
    verbose: bool
):
    """Convert documents to Markdown with smart tracking.

    Supports Word documents (.docx, .doc), ebooks (.epub, .mobi, .azw, .azw3),
    and PDFs with native text or OCR.

    The app tracks conversions and detects file changes to prevent unnecessary
    re-processing. You'll be prompted to choose which files to process.

    \b
    Examples:
        convert-docs document.docx
        convert-docs documents/ --recursive
        convert-docs papers/ -r -v
        convert-docs ebooks/ --yes  # Auto-process new and modified files
    """
    console.print("\n[bold cyan]Document to Markdown Converter[/bold cyan]\n")

    # Ask about corrected names with ID codes (unless --yes flag is used)
    if not yes:
        _prompt_id_code_verification()

    # Show supported file types
    if verbose:
        supported = FileTypeDetector.get_supported_extensions()
        console.print(f"Supported extensions: {', '.join(sorted(supported))}\n")

    # Create processor
    processor = BatchProcessor(
        extract_images=not no_images,
        verbose=verbose
    )

    try:
        # Categorize files by status
        console.print("[cyan]Scanning files...[/cyan]")
        categorized = processor.categorize_files(path, recursive=recursive)
        summary = processor.status_detector.get_summary(categorized)

        # Check if any files were found
        if summary['total'] == 0:
            console.print("[yellow]No supported files found.[/yellow]\n")
            sys.exit(0)

        # Display categorization
        _display_categorization(categorized, summary)

        # Prompt user for action (unless --yes flag is used)
        if yes:
            # Auto-process new and modified files
            files_to_process = processor.status_detector.filter_by_status(
                categorized,
                [FileStatus.NEW, FileStatus.MODIFIED]
            )
            if not files_to_process:
                console.print("[yellow]No new or modified files to process.[/yellow]\n")
                sys.exit(0)
        else:
            files_to_process = _prompt_user_selection(categorized, summary)
            if not files_to_process:
                console.print("[yellow]No files selected for processing.[/yellow]\n")
                sys.exit(0)

        # Process selected files
        console.print(f"\n[cyan]Processing {len(files_to_process)} file(s)...[/cyan]\n")
        stats = processor.process_files(files_to_process)

        # Display summary
        _display_summary(stats)

        # Exit with appropriate code
        if stats['failed'] > 0:
            sys.exit(1)
        else:
            sys.exit(0)

    except KeyboardInterrupt:
        console.print("\n[yellow]Conversion interrupted by user[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"\n[red]Error: {str(e)}[/red]")
        if verbose:
            console.print_exception()
        sys.exit(1)


def _display_categorization(categorized: dict, summary: dict):
    """Display file categorization table.

    Args:
        categorized: Dictionary mapping FileStatus to file lists
        summary: Dictionary with file counts
    """
    console.print("\n[bold]File Status[/bold]")

    table = Table(show_header=True, header_style="bold")
    table.add_column("Category", style="cyan")
    table.add_column("Count", justify="right")
    table.add_column("Description")

    table.add_row(
        "New",
        f"[green]{summary['new']}[/green]",
        "Never been converted"
    )
    table.add_row(
        "Modified",
        f"[yellow]{summary['modified']}[/yellow]",
        "Source file changed since last conversion"
    )
    table.add_row(
        "Unchanged",
        f"[blue]{summary['unchanged']}[/blue]",
        "Already converted and unchanged"
    )
    table.add_row(
        "[bold]Total[/bold]",
        f"[bold]{summary['total']}[/bold]",
        ""
    )

    console.print(table)


def _prompt_user_selection(categorized: dict, summary: dict) -> list:
    """Prompt user to select which files to process.

    Args:
        categorized: Dictionary mapping FileStatus to file lists
        summary: Dictionary with file counts

    Returns:
        List of file paths to process
    """
    console.print("\n[bold]What would you like to do?[/bold]\n")

    # Build options dynamically based on what files exist
    options = []
    if summary['new'] > 0 and summary['modified'] > 0:
        options.append("1) Process new and modified files (recommended)")
        options.append("2) Process all files (including unchanged)")
        options.append("3) Process new files only")
        options.append("4) Process modified files only")
        options.append("5) Cancel")
        default = "1"
    elif summary['new'] > 0:
        options.append("1) Process new files")
        options.append("2) Process all files")
        options.append("3) Cancel")
        default = "1"
    elif summary['modified'] > 0:
        options.append("1) Process modified files")
        options.append("2) Process all files")
        options.append("3) Cancel")
        default = "1"
    else:
        # Only unchanged files
        options.append("1) Process all files (re-convert unchanged)")
        options.append("2) Cancel")
        default = "2"

    for option in options:
        console.print(f"  {option}")

    console.print()
    choice = Prompt.ask(
        "Enter your choice",
        default=default,
        show_default=True
    )

    # Map choice to file statuses
    processor = BatchProcessor()  # Temporary instance for status detector
    status_detector = processor.status_detector

    # Parse the choice based on what options were shown
    if summary['new'] > 0 and summary['modified'] > 0:
        if choice == "1":
            return status_detector.filter_by_status(
                categorized,
                [FileStatus.NEW, FileStatus.MODIFIED]
            )
        elif choice == "2":
            return status_detector.filter_by_status(
                categorized,
                [FileStatus.NEW, FileStatus.MODIFIED, FileStatus.UNCHANGED]
            )
        elif choice == "3":
            return status_detector.filter_by_status(
                categorized,
                [FileStatus.NEW]
            )
        elif choice == "4":
            return status_detector.filter_by_status(
                categorized,
                [FileStatus.MODIFIED]
            )
        else:
            return []
    elif summary['new'] > 0:
        if choice == "1":
            return status_detector.filter_by_status(
                categorized,
                [FileStatus.NEW]
            )
        elif choice == "2":
            return status_detector.filter_by_status(
                categorized,
                [FileStatus.NEW, FileStatus.MODIFIED, FileStatus.UNCHANGED]
            )
        else:
            return []
    elif summary['modified'] > 0:
        if choice == "1":
            return status_detector.filter_by_status(
                categorized,
                [FileStatus.MODIFIED]
            )
        elif choice == "2":
            return status_detector.filter_by_status(
                categorized,
                [FileStatus.NEW, FileStatus.MODIFIED, FileStatus.UNCHANGED]
            )
        else:
            return []
    else:
        # Only unchanged files
        if choice == "1":
            return status_detector.filter_by_status(
                categorized,
                [FileStatus.UNCHANGED]
            )
        else:
            return []


def _display_summary(stats: dict):
    """Display conversion summary.

    Args:
        stats: Dictionary with conversion statistics
    """
    console.print("\n[bold]Conversion Summary[/bold]")

    table = Table(show_header=True, header_style="bold")
    table.add_column("Status", style="cyan")
    table.add_column("Count", justify="right")

    table.add_row("Total files", str(stats['total']))
    table.add_row("✓ Converted", f"[green]{stats['converted']}[/green]")
    table.add_row("⊘ Skipped", f"[yellow]{stats['skipped']}[/yellow]")
    table.add_row("✗ Failed", f"[red]{stats['failed']}[/red]")

    console.print(table)
    console.print()


if __name__ == '__main__':
    main()
