#!/usr/bin/env python3
"""
Command-line interface for law journal article file renamer.
"""

import argparse
import sys
from pathlib import Path
from renamer import ArticleRenamer
from config_manager import ConfigManager
from extractors.pdf_extractor import PDFExtractor


def check_dependencies():
    """
    Check if required external dependencies are available.

    Returns:
        tuple: (success: bool, error_message: str or None)
    """
    available, error_msg = PDFExtractor.check_pdftotext_available()
    if not available:
        return (False, error_msg)
    return (True, None)


def print_result(result, index=None, total=None):
    """Print extraction result in formatted way."""
    if index and total:
        print(f"\n[{index}/{total}] {result['original_filename']}")
    else:
        print(f"\n{result['original_filename']}")

    print("      ↓")
    if result['new_filename']:
        print(f"      {result['new_filename']}")
    else:
        print("      [FAILED - Could not generate filename]")

    print("\n      Extracted:")
    authors_str = ', '.join(result.get('authors', [])) if result.get('authors') else 'N/A'
    print(f"        Authors:  {authors_str} (from {result['authors_source'] or 'N/A'})")
    print(f"        Title:    {result['title'] or 'N/A'} (from {result['title_source'] or 'N/A'})")
    print(f"        Year:     {result['year'] or 'N/A'} (from {result['year_source'] or 'N/A'})")
    print(f"        Journal:  {result['journal_name'] or 'N/A'}")
    if result.get('volume'):
        print(f"        Volume:   {result['volume']}")

    # Show quality assessment and decision
    print(f"\n      Original filename quality: {result.get('original_filename_quality', 'N/A')}")
    print(f"      Extraction confidence: {result['confidence']}")

    # Show replacement decision
    should_rename = result.get('should_rename', False)
    decision_icon = "✓" if should_rename else "✗"
    decision_text = "REPLACE" if should_rename else "SKIP"
    print(f"      Decision: {decision_text} {decision_icon}")

    if result.get('rename_decision_reason'):
        print(f"        Reason: {result['rename_decision_reason']}")

    if result['notes']:
        print(f"      Notes:")
        for note in result['notes']:
            print(f"        - {note}")


def prompt_registry_path():
    """
    Interactively prompt user for registry path.

    Returns:
        tuple: (registry_path, save_as_default) or (None, False) if cancelled
    """
    config_manager = ConfigManager()
    default_path = config_manager.get_default_registry_path()

    print("\n" + "=" * 80)
    print("Metadata Registry Configuration")
    print("=" * 80)

    if default_path:
        print(f"\nCurrent default: {default_path}")
        print("\nPress Enter to use this location, or type a new path:")
    else:
        print("\nNo default registry path configured.")
        print("Enter path for metadata registry (e.g., ./metadata_registry):")

    user_input = input("> ").strip()

    # Use default if Enter pressed and default exists
    if not user_input and default_path:
        registry_path = default_path
        save_default = False
    elif not user_input and not default_path:
        print("ERROR: Registry path required.")
        return (None, False)
    else:
        registry_path = user_input
        save_default = False

        # Ask if they want to save as default
        if registry_path != default_path:
            response = input("\nSave this as default registry location? [Y/n]: ").strip().lower()
            save_default = response in ('', 'y', 'yes')

    # Save as default if requested
    if save_default:
        if config_manager.set_default_registry_path(registry_path):
            print(f"✓ Saved as default registry path")
        else:
            print("Warning: Could not save default path to config")

    print("=" * 80 + "\n")

    return (registry_path, save_default)


def preview_mode(file_or_dir, extract_metadata=False, registry_path=None):
    """Preview mode - show what would be renamed."""
    # Check dependencies
    deps_ok, deps_error = check_dependencies()
    if not deps_ok:
        print("ERROR: Missing required dependencies")
        print(deps_error)
        return 1

    # Handle registry path
    if extract_metadata and not registry_path:
        # Try to use default registry path
        config_manager = ConfigManager()
        default_path = config_manager.get_default_registry_path()

        if default_path:
            # Use default automatically
            registry_path = default_path
            print(f"Using default registry: {registry_path}")
        elif sys.stdin.isatty():
            # No default - prompt user interactively
            registry_path, _ = prompt_registry_path()
            if not registry_path:
                print("ERROR: Registry path required for metadata extraction.")
                return 1
        else:
            # Non-interactive mode with no default - require explicit path
            print("ERROR: --registry-path required for metadata extraction in non-interactive mode.")
            print("Either provide --registry-path or run interactively to configure default.")
            return 1

    renamer = ArticleRenamer()
    path = Path(file_or_dir)

    print("=" * 80)
    print("PREVIEW: Proposed Filename Changes")
    print("=" * 80)

    # Process file(s)
    if path.is_file():
        results = [renamer.process_file(path)]
    elif path.is_dir():
        results = renamer.process_directory(path)
    else:
        print(f"Error: {file_or_dir} is not a valid file or directory")
        return 1

    # Display results
    for i, result in enumerate(results, 1):
        print_result(result, i, len(results))

        # Extract metadata if requested
        if extract_metadata:
            try:
                metadata = renamer.extract_metadata(result)
                paths = renamer.save_metadata_json(result, metadata, registry_path=registry_path)

                if paths['sidecar']:
                    print(f"      Metadata saved: {paths['sidecar'].name}")
                    print(f"        Abstract: {metadata.get('abstract', 'N/A')[:100]}..." if metadata.get('abstract') else "        Abstract: N/A")
                    keywords_str = ', '.join(metadata.get('keywords', [])) if metadata.get('keywords') else 'N/A'
                    print(f"        Keywords: {keywords_str}")
                    print(f"        DOI: {metadata.get('doi', 'N/A')}")
                    affiliations = metadata.get('author_affiliations', [])
                    if affiliations:
                        print(f"        Affiliations: {len(affiliations)} author(s) with institution data")

                if paths['registry_json']:
                    print(f"      Registry updated: {paths['registry_json'].name}, {paths['registry_csv'].name}")

            except Exception as e:
                print(f"      Metadata extraction failed: {e}")

    # Summary
    print("\n" + "=" * 80)
    print("Summary:")
    print("-" * 80)
    print(f"Total files: {len(results)}")

    if len(results) > 0:
        successful = sum(1 for r in results if r['new_filename'])
        high_conf = sum(1 for r in results if r['confidence'] == 'HIGH')
        medium_conf = sum(1 for r in results if r['confidence'] == 'MEDIUM')
        low_conf = sum(1 for r in results if r['confidence'] == 'LOW')

        print(f"Successfully extracted: {successful} ({successful/len(results)*100:.0f}%)")
        print(f"High confidence: {high_conf}")
        print(f"Medium confidence: {medium_conf}")
        print(f"Low confidence: {low_conf}")
    print("=" * 80)

    return 0


def rename_mode(file_or_dir, output_dir=None, interactive=False, extract_metadata=False, registry_path=None):
    """Rename mode - actually rename files."""
    # Check dependencies
    deps_ok, deps_error = check_dependencies()
    if not deps_ok:
        print("ERROR: Missing required dependencies")
        print(deps_error)
        return 1

    # Handle registry path
    if extract_metadata and not registry_path:
        # Try to use default registry path
        config_manager = ConfigManager()
        default_path = config_manager.get_default_registry_path()

        if default_path:
            # Use default automatically
            registry_path = default_path
            print(f"Using default registry: {registry_path}")
        elif sys.stdin.isatty():
            # No default - prompt user interactively
            registry_path, _ = prompt_registry_path()
            if not registry_path:
                print("ERROR: Registry path required for metadata extraction.")
                return 1
        else:
            # Non-interactive mode with no default - require explicit path
            print("ERROR: --registry-path required for metadata extraction in non-interactive mode.")
            print("Either provide --registry-path or run interactively to configure default.")
            return 1

    renamer = ArticleRenamer()
    path = Path(file_or_dir)

    print("=" * 80)
    print("RENAME MODE: Processing files...")
    print("=" * 80)

    # Process file(s)
    if path.is_file():
        results = [renamer.process_file(path)]
    elif path.is_dir():
        results = renamer.process_directory(path)
    else:
        print(f"Error: {file_or_dir} is not a valid file or directory")
        return 1

    # Rename files
    renamed_count = 0
    failed_count = 0

    for i, result in enumerate(results, 1):
        print_result(result, i, len(results))

        if not result['new_filename']:
            print("      STATUS: SKIPPED (could not generate filename)\n")
            failed_count += 1
            continue

        # Interactive mode - ask for confirmation
        if interactive:
            response = input("\n      Proceed with rename? [y/N]: ").strip().lower()
            if response != 'y':
                print("      STATUS: SKIPPED (user declined)\n")
                continue

        # Perform rename
        original_path = Path(result['file_path'])

        rename_result = renamer.rename_file(original_path, dry_run=False)

        if rename_result['success']:
            print("      STATUS: RENAMED ✓")
            if rename_result['result'].get('notes'):
                for note in rename_result['result']['notes']:
                    print(f"      Note: {note}")
            renamed_count += 1

            # Extract metadata if requested
            if extract_metadata:
                try:
                    # Update file_path to point to renamed file
                    new_path = rename_result['new_path']
                    result['file_path'] = str(new_path)

                    metadata = renamer.extract_metadata(result)
                    paths = renamer.save_metadata_json(result, metadata, registry_path=registry_path)
                    if paths['sidecar']:
                        print(f"      Metadata saved: {paths['sidecar'].name}")
                    if paths['registry_json']:
                        print(f"      Registry updated: {paths['registry_json'].name}")
                except Exception as e:
                    print(f"      ERROR: Metadata extraction failed for {result['original_filename']}: {e}")

            print()  # Blank line
        else:
            error_msg = rename_result.get('error', 'Unknown error')
            print(f"      STATUS: FAILED - {error_msg}\n")
            failed_count += 1

    # Summary
    print("\n" + "=" * 80)
    print("Summary:")
    print("-" * 80)
    print(f"Total files: {len(results)}")
    print(f"Successfully renamed: {renamed_count}")
    print(f"Failed: {failed_count}")
    print("=" * 80)

    return 0


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Rename law journal article files (PDF, Word) using standardized format: [year]_[author]_[title].pdf',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Preview mode (show what would be renamed)
  python cli.py preview z_sample_articles/

  # Rename files
  python cli.py rename z_sample_articles/

  # Interactive rename (confirm each file)
  python cli.py rename z_sample_articles/ --interactive

  # With metadata extraction
  python cli.py rename z_sample_articles/ --extract-metadata

  # Single file
  python cli.py preview "Arnold_Law_Fact_Medieval_Jury_Trial_1974.pdf"
        """
    )

    parser.add_argument(
        'mode',
        choices=['preview', 'rename'],
        help='Mode: preview (dry run) or rename (actually rename files)'
    )

    parser.add_argument(
        'path',
        help='File or directory to process'
    )

    parser.add_argument(
        '--output',
        '-o',
        help='Output directory (default: same as input)'
    )

    parser.add_argument(
        '--interactive',
        '-i',
        action='store_true',
        help='Interactive mode - confirm each rename'
    )

    parser.add_argument(
        '--extract-metadata',
        '-m',
        action='store_true',
        help='Extract and save comprehensive metadata to JSON sidecar files'
    )

    parser.add_argument(
        '--registry-path',
        '-r',
        help='Path prefix for central metadata registry (creates .json and .csv files). '
             'If omitted when using --extract-metadata, will prompt interactively for path. '
             'Example: --registry-path ./metadata_registry'
    )

    args = parser.parse_args()

    # Execute
    if args.mode == 'preview':
        return preview_mode(args.path, extract_metadata=args.extract_metadata, registry_path=args.registry_path)
    elif args.mode == 'rename':
        return rename_mode(args.path, args.output, args.interactive,
                          extract_metadata=args.extract_metadata, registry_path=args.registry_path)
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())
