#!/usr/bin/env python3
"""
Document Processor - Main Entry Point

Unified document processing pipeline:
1. Rename - Extract metadata and normalize filenames
2. Code - Add unique 5-letter identifiers
3. Convert - Transform to plain text
4. Clean - Optimize for AI/RAG consumption

Usage:
    python main.py process /path/to/files --type caselaw
    python main.py process /path/to/files --dry-run
    python main.py status
    python main.py export registry.csv

Current Status: Phase 1 - Stub only (CLI implementation in Phase 2)
"""

import sys


def main():
    """Main entry point (stub for Phase 2)."""
    print("Document Processor v0.1.0")
    print("=" * 60)
    print()
    print("Status: Phase 1 - Building services layer")
    print()
    print("The CLI will be implemented in Phase 2.")
    print("Current focus: Building core services:")
    print("  - services/text_extractor.py")
    print("  - services/registrar.py")
    print("  - services/classifier.py")
    print("  - services/code_generator.py")
    print()
    print("See 1-Context-Documentation/ for project details.")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
