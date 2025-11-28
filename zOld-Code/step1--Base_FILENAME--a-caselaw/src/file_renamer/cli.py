"""Command-line entry point for caselaw file renaming."""

from pathlib import Path
from typing import Optional

import typer

from .models import DocumentMetadata
from .pipeline import build_pipeline
from .templates import FilenameTemplate

app = typer.Typer(help="Batch rename caselaw documents with deterministic logic.")


@app.command()
def preview(
    source: Path = typer.Argument(..., exists=True, readable=True, file_okay=False),
    template: FilenameTemplate = typer.Option(
        FilenameTemplate.CS_COURT_YEAR_SHORTCASE_REPORTER,
        "--template",
        case_sensitive=False,
        help="Filename template to apply.",
    ),
    limit: Optional[int] = typer.Option(None, help="Limit number of files processed."),
) -> None:
    """Preview renaming plan without touching the filesystem."""

    pipeline = build_pipeline(template)
    results = pipeline.generate_preview(source, limit=limit)

    if not results:
        typer.echo("No documents found.")
        raise typer.Exit()

    for result in results:
        typer.echo(f"{result.original_name} -> {result.new_name}")


@app.command()
def rename(
    source: Path = typer.Argument(..., exists=True, readable=True, file_okay=False),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Simulate the renaming process without modifying files."
    ),
    template: FilenameTemplate = typer.Option(
        FilenameTemplate.CS_COURT_YEAR_SHORTCASE_REPORTER,
        "--template",
        case_sensitive=False,
        help="Filename template to apply.",
    ),
) -> None:
    """Rename files according to the chosen template."""

    pipeline = build_pipeline(template)
    rename_plan = pipeline.generate_preview(source)

    if not rename_plan:
        typer.echo("No documents found.")
        raise typer.Exit()

    if dry_run:
        for result in rename_plan:
            typer.echo(f"[DRY RUN] {result.original_name} -> {result.new_name}")
        raise typer.Exit()

    pipeline.execute(rename_plan)
    typer.echo(f"Renamed {len(rename_plan)} files.")


def main() -> None:
    """Typer expects a callable main for console entry points."""

    app()


if __name__ == "__main__":
    main()
