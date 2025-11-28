#!/usr/bin/env python3
"""Test script to verify setup and dependencies."""

import sys
import subprocess
from pathlib import Path


def check_python_imports():
    """Check if all Python packages can be imported."""
    print("Checking Python package imports...")

    required_packages = [
        ('click', 'click'),
        ('rich', 'rich'),
        ('python-docx', 'docx'),
        ('ebooklib', 'ebooklib'),
        ('PyPDF2', 'PyPDF2'),
        ('pyyaml', 'yaml'),
    ]

    optional_packages = [
        ('marker-pdf', 'marker'),
    ]

    errors = []

    for package_name, import_name in required_packages:
        try:
            __import__(import_name)
            print(f"  ✓ {package_name}")
        except ImportError:
            print(f"  ✗ {package_name} - MISSING")
            errors.append(package_name)

    for package_name, import_name in optional_packages:
        try:
            __import__(import_name)
            print(f"  ✓ {package_name} (optional)")
        except ImportError:
            print(f"  ⊘ {package_name} (optional) - not installed")

    if errors:
        print(f"\nError: Missing required packages: {', '.join(errors)}")
        print("Run: pip install -r requirements.txt")
        return False

    return True


def check_external_tools():
    """Check if external tools are available."""
    print("\nChecking external tools...")

    tools = [
        ('pandoc', 'pandoc --version', True),
        ('ebook-convert (Calibre)', 'ebook-convert --version', True),
    ]

    errors = []

    for tool_name, command, required in tools:
        try:
            result = subprocess.run(
                command.split(),
                capture_output=True,
                timeout=5
            )
            if result.returncode == 0:
                print(f"  ✓ {tool_name}")
            else:
                if required:
                    print(f"  ✗ {tool_name} - MISSING")
                    errors.append(tool_name)
                else:
                    print(f"  ⊘ {tool_name} - not available")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            if required:
                print(f"  ✗ {tool_name} - MISSING")
                errors.append(tool_name)
            else:
                print(f"  ⊘ {tool_name} - not available")

    if errors:
        print(f"\nError: Missing required tools: {', '.join(errors)}")
        print("\nInstallation instructions:")
        print("  macOS: brew install pandoc && brew install --cask calibre")
        print("  Linux: sudo apt-get install pandoc calibre")
        return False

    return True


def check_module_structure():
    """Check if all module files are present."""
    print("\nChecking module structure...")

    required_files = [
        'doc_to_markdown/__init__.py',
        'doc_to_markdown/cli.py',
        'doc_to_markdown/file_detector.py',
        'doc_to_markdown/converter_factory.py',
        'doc_to_markdown/processor.py',
        'doc_to_markdown/frontmatter.py',
        'doc_to_markdown/metadata/__init__.py',
        'doc_to_markdown/metadata/word.py',
        'doc_to_markdown/metadata/ebook.py',
        'doc_to_markdown/metadata/pdf.py',
        'doc_to_markdown/converters/__init__.py',
        'doc_to_markdown/converters/base.py',
        'doc_to_markdown/converters/word.py',
        'doc_to_markdown/converters/ebook.py',
        'doc_to_markdown/converters/pdf.py',
    ]

    errors = []

    for file_path in required_files:
        full_path = Path(__file__).parent / file_path
        if full_path.exists():
            print(f"  ✓ {file_path}")
        else:
            print(f"  ✗ {file_path} - MISSING")
            errors.append(file_path)

    if errors:
        print(f"\nError: Missing module files")
        return False

    return True


def test_imports():
    """Test importing main modules."""
    print("\nTesting module imports...")

    try:
        from doc_to_markdown.file_detector import FileTypeDetector
        print("  ✓ FileTypeDetector")

        from doc_to_markdown.converter_factory import ConverterFactory
        print("  ✓ ConverterFactory")

        from doc_to_markdown.processor import BatchProcessor
        print("  ✓ BatchProcessor")

        from doc_to_markdown.frontmatter import FrontmatterGenerator
        print("  ✓ FrontmatterGenerator")

        return True
    except ImportError as e:
        print(f"  ✗ Import failed: {e}")
        return False


def main():
    """Run all checks."""
    print("=" * 60)
    print("Document to Markdown Converter - Setup Test")
    print("=" * 60)

    results = []

    results.append(check_module_structure())
    results.append(check_python_imports())
    results.append(check_external_tools())
    results.append(test_imports())

    print("\n" + "=" * 60)
    if all(results):
        print("✓ All checks passed! Setup is complete.")
        print("\nYou can now use: convert-docs <file-or-directory>")
        print("=" * 60)
        return 0
    else:
        print("✗ Some checks failed. Please fix the issues above.")
        print("=" * 60)
        return 1


if __name__ == '__main__':
    sys.exit(main())
