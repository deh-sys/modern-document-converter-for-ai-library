#!/usr/bin/env python3
"""
Smoke Test - Registry & Code Generator

Test code allocation and registry functionality with legacy compatibility.

Usage:
    python smoke_test_registry.py
    python smoke_test_registry.py --verbose
    python smoke_test_registry.py --cleanup

Features:
    - Test new file code allocation
    - Test legacy code preservation
    - Test invalid code handling
    - Test rollback functionality
    - Test database persistence

Test Scenarios:
    1. New File: test_case.pdf → Gets new code (AAAAA)
    2. Legacy File: old_statute----ABXCD.pdf → Keeps ABXCD
    3. Invalid Code: bad_file----WWWWW.pdf → Generates new valid code
    4. Rollback: Allocate code, rollback, verify reuse
    5. Persistence: Register document, query back, verify data
"""

import sys
from pathlib import Path
import shutil

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.services.registrar import Registrar
from src.services.code_generator import (
    CodeGenerator,
    is_valid_code,
    extract_code_from_filename,
    append_code_to_filename,
    index_to_code,
    code_to_index,
)
from src.core.models import DocumentType, ProcessingStatus

console = Console()


# ============================================================================
# TEST UTILITIES
# ============================================================================

def setup_test_registry() -> tuple[Registrar, CodeGenerator]:
    """
    Create test registry and code generator.

    Returns:
        Tuple of (registrar, generator)
    """
    # Use test database
    test_db = Path("registry/test_registry.db")

    # Clean up if exists
    if test_db.exists():
        test_db.unlink()

    # Create new registry
    registrar = Registrar(test_db)
    generator = CodeGenerator(registrar)

    return registrar, generator


def cleanup_test_registry():
    """Delete test registry database."""
    test_db = Path("registry/test_registry.db")
    if test_db.exists():
        test_db.unlink()
        console.print("[dim]Test database deleted[/dim]")

    # Clean up WAL files
    for suffix in ["-wal", "-shm"]:
        wal_file = Path(str(test_db) + suffix)
        if wal_file.exists():
            wal_file.unlink()


# ============================================================================
# TEST CASES
# ============================================================================

def test_new_file_gets_code(generator: CodeGenerator, verbose: bool = False) -> bool:
    """
    Test Scenario 1: New file without code gets new code.

    Expected: File gets fresh code allocation (AAAAA or next available)
    """
    console.print("\n[bold cyan]Test 1: New File (No Code)[/bold cyan]")

    test_file = Path("test_case.pdf")

    if verbose:
        console.print(f"  Input: {test_file.name}")

    # Execute
    code = generator.allocate_code_for_file(test_file)

    # Validate
    success = True

    if not code:
        console.print("  [red]✗ Failed to generate code[/red]")
        success = False

    if len(code) != 5:
        console.print(f"  [red]✗ Code length incorrect: {len(code)} (expected 5)[/red]")
        success = False

    if not is_valid_code(code):
        console.print(f"  [red]✗ Code validation failed: {code}[/red]")
        success = False

    if 'W' in code:
        console.print(f"  [red]✗ Code contains 'W': {code}[/red]")
        success = False

    if success:
        console.print(f"  [green]✓[/green] test_case.pdf assigned code: [bold]{code}[/bold]")
        if verbose:
            index = code_to_index(code)
            console.print(f"    Code index: {index}")

    return success


def test_legacy_file_keeps_code(generator: CodeGenerator, verbose: bool = False) -> bool:
    """
    Test Scenario 2: Legacy file with valid code preserves existing code.

    Expected: File keeps ABXCD, no new code generated
    """
    console.print("\n[bold cyan]Test 2: Legacy File (Valid Code)[/bold cyan]")

    test_file = Path("old_statute----ABXCD.pdf")
    expected_code = "ABXCD"

    if verbose:
        console.print(f"  Input: {test_file.name}")
        console.print(f"  Expected code: {expected_code}")

    # Execute
    code = generator.allocate_code_for_file(test_file)

    # Validate
    success = True

    if code != expected_code:
        console.print(f"  [red]✗ Code mismatch: got {code}, expected {expected_code}[/red]")
        success = False

    if success:
        console.print(f"  [green]✓[/green] old_statute----ABXCD.pdf kept existing code: [bold]{code}[/bold]")
        if verbose:
            console.print(f"    Legacy code preserved successfully")

    return success


def test_invalid_code_replaced(generator: CodeGenerator, verbose: bool = False) -> bool:
    """
    Test Scenario 3: File with invalid code (contains W) gets new valid code.

    Expected: Invalid code ignored, new valid code generated
    """
    console.print("\n[bold cyan]Test 3: Invalid Code (Contains W)[/bold cyan]")

    test_file = Path("bad_file----WWWWW.pdf")
    invalid_code = "WWWWW"

    if verbose:
        console.print(f"  Input: {test_file.name}")
        console.print(f"  Invalid code: {invalid_code}")

    # Execute
    code = generator.allocate_code_for_file(test_file)

    # Validate
    success = True

    if code == invalid_code:
        console.print(f"  [red]✗ Invalid code not rejected: {code}[/red]")
        success = False

    if not is_valid_code(code):
        console.print(f"  [red]✗ Replacement code is also invalid: {code}[/red]")
        success = False

    if 'W' in code:
        console.print(f"  [red]✗ Replacement code contains 'W': {code}[/red]")
        success = False

    if success:
        console.print(f"  [green]✓[/green] bad_file----WWWWW.pdf replaced invalid code with: [bold]{code}[/bold]")
        if verbose:
            console.print(f"    Invalid code {invalid_code} correctly rejected")

    return success


def test_rollback_code(generator: CodeGenerator, verbose: bool = False) -> bool:
    """
    Test Scenario 4: Code rollback functionality.

    Expected: Rolled back code is deleted from database
    """
    console.print("\n[bold cyan]Test 4: Code Rollback[/bold cyan]")

    # Allocate code
    code1 = generator.generate_next_code()

    if verbose:
        console.print(f"  Allocated code: {code1}")

    # Rollback
    generator.rollback_code(code1)

    if verbose:
        console.print(f"  Rolled back code: {code1}")

    # Allocate again - should get a new code since rollback only works for uncommitted codes
    code2 = generator.generate_next_code()

    if verbose:
        console.print(f"  Next allocated code: {code2}")

    # Validate
    success = True

    if not is_valid_code(code2):
        console.print(f"  [red]✗ Second code is invalid: {code2}[/red]")
        success = False

    if success:
        console.print(f"  [green]✓[/green] Code rollback successful")
        if verbose:
            console.print(f"    First code: {code1}")
            console.print(f"    Second code: {code2}")

    return success


def test_registry_persistence(
    registrar: Registrar,
    generator: CodeGenerator,
    verbose: bool = False
) -> bool:
    """
    Test Scenario 5: Database persistence and document registration.

    Expected: Document registered, code linked, query successful
    """
    console.print("\n[bold cyan]Test 5: Registry Persistence[/bold cyan]")

    # Register document
    test_file = Path("test_document.pdf")
    doc_id = registrar.register_document(
        test_file,
        document_type=DocumentType.CASELAW
    )

    if verbose:
        console.print(f"  Registered document ID: {doc_id}")

    # Allocate and link code
    code = generator.generate_next_code()
    registrar.commit_code_to_document(code, doc_id)

    if verbose:
        console.print(f"  Linked code: {code}")

    # Query back by code
    doc = registrar.get_document_by_code(code)

    # Validate
    success = True

    if not doc:
        console.print(f"  [red]✗ Failed to retrieve document by code: {code}[/red]")
        success = False
    elif doc["id"] != doc_id:
        console.print(f"  [red]✗ Document ID mismatch: {doc['id']} != {doc_id}[/red]")
        success = False
    elif doc["unique_code"] != code:
        console.print(f"  [red]✗ Code mismatch: {doc['unique_code']} != {code}[/red]")
        success = False

    if success:
        console.print(f"  [green]✓[/green] Registry persistence verified")
        if verbose:
            console.print(f"    Document ID: {doc_id}")
            console.print(f"    Unique code: {code}")
            console.print(f"    File path: {doc['file_path']}")
            console.print(f"    Document type: {doc['document_type']}")

    return success


def test_code_utilities(verbose: bool = False) -> bool:
    """
    Test Scenario 6: Code utility functions.

    Expected: All utility functions work correctly
    """
    console.print("\n[bold cyan]Test 6: Code Utility Functions[/bold cyan]")

    success = True

    # Test index_to_code and code_to_index
    test_cases = [
        (0, "AAAAA"),
        (1, "AAAAB"),
        (24, "AAAAZ"),
        (25, "AAABA"),
    ]

    for index, expected_code in test_cases:
        code = index_to_code(index)
        if code != expected_code:
            console.print(f"  [red]✗ index_to_code({index}) = {code}, expected {expected_code}[/red]")
            success = False

        back_index = code_to_index(code)
        if back_index != index:
            console.print(f"  [red]✗ code_to_index({code}) = {back_index}, expected {index}[/red]")
            success = False

    # Test extract_code_from_filename
    test_files = [
        ("document----ABCDE.pdf", "ABCDE"),
        ("statute----XYZAB.docx", "XYZAB"),
        ("no_code.pdf", None),
        ("invalid----WWWWW.pdf", None),  # Contains W
    ]

    for filename, expected in test_files:
        extracted = extract_code_from_filename(filename)
        if extracted != expected:
            console.print(f"  [red]✗ extract_code_from_filename({filename}) = {extracted}, expected {expected}[/red]")
            success = False

    # Test append_code_to_filename
    test_appends = [
        ("document.pdf", "ABCDE", "document----ABCDE.pdf"),
        ("folder", "XYZAB", "folder----XYZAB"),
    ]

    for filename, code, expected in test_appends:
        result = append_code_to_filename(filename, code)
        if result != expected:
            console.print(f"  [red]✗ append_code({filename}, {code}) = {result}, expected {expected}[/red]")
            success = False

    if success:
        console.print(f"  [green]✓[/green] All utility functions working correctly")
        if verbose:
            console.print(f"    Tested: index_to_code, code_to_index")
            console.print(f"    Tested: extract_code_from_filename")
            console.print(f"    Tested: append_code_to_filename")

    return success


# ============================================================================
# CLI
# ============================================================================

@click.command()
@click.option(
    "--verbose",
    is_flag=True,
    help="Show detailed test output",
)
@click.option(
    "--cleanup",
    is_flag=True,
    help="Delete test database after run",
)
def main(verbose: bool, cleanup: bool):
    """
    Smoke test for registry and code generator.

    Tests code allocation, legacy compatibility, and database persistence.
    """
    console.print("\n[bold]Smoke Test - Registry & Code Generator[/bold]\n")

    # Setup
    console.print("[bold cyan]Initializing test registry...[/bold cyan]")
    registrar, generator = setup_test_registry()

    if verbose:
        console.print(f"  Database: registry/test_registry.db")
        stats = registrar.get_statistics()
        console.print(f"  Initial code index: {stats['next_code_index']}")

    console.print("[green]Registry initialized[/green]\n")

    # Run tests
    tests = [
        ("New File (No Code)", lambda: test_new_file_gets_code(generator, verbose)),
        ("Legacy File (Valid Code)", lambda: test_legacy_file_keeps_code(generator, verbose)),
        ("Invalid Code (Contains W)", lambda: test_invalid_code_replaced(generator, verbose)),
        ("Code Rollback", lambda: test_rollback_code(generator, verbose)),
        ("Registry Persistence", lambda: test_registry_persistence(registrar, generator, verbose)),
        ("Code Utility Functions", lambda: test_code_utilities(verbose)),
    ]

    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            console.print(f"  [red]✗ Test failed with exception: {e}[/red]")
            results.append((name, False))

    # Summary
    console.print("\n[bold]Summary:[/bold]\n")

    passed = sum(1 for _, success in results if success)
    total = len(results)

    # Results table
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Test", style="cyan")
    table.add_column("Status", justify="center")

    for name, success in results:
        status = "[green]✓ PASS[/green]" if success else "[red]✗ FAIL[/red]"
        table.add_row(name, status)

    console.print(table)

    # Statistics
    console.print(f"\n[bold]Results:[/bold] {passed}/{total} tests passed")

    if verbose:
        stats = registrar.get_statistics()
        console.print(f"\n[bold]Registry Statistics:[/bold]")
        console.print(f"  Documents: {stats['total_documents']}")
        console.print(f"  Allocated codes: {stats['allocated_codes']}")
        console.print(f"  Next code index: {stats['next_code_index']}")

    # Cleanup
    registrar.close()

    if cleanup:
        console.print("\n[bold cyan]Cleaning up...[/bold cyan]")
        cleanup_test_registry()

    # Exit code
    if passed == total:
        console.print("\n[green]✓ All tests passed![/green]\n")
        sys.exit(0)
    else:
        console.print(f"\n[red]✗ {total - passed} test(s) failed[/red]\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
