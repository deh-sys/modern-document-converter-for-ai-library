# Filename Indexer

## Key Commands
- `python3 filename_indexer.py` — launch interactive mode (prompts for recursion and targets).
- `python3 filename_indexer.py --paths /path/a /path/b` — run non-interactively using specific targets.
- `python3 filename_indexer.py --non-recursive` — limit processing to the immediate children of each provided folder (you'll still be asked to confirm).
- `python3 filename_indexer.py --help` — show the CLI usage summary.

## Overview
This utility renames selected files or folders by appending four dashes plus a unique five-letter code (letters A-Z except W). It uses a **single fixed registry file** to ensure codes are never duplicated across all uses. The tool only touches PDFs, Word docs, Markdown files (excluding README-style documentation), and directory names.

## Fixed Registry Location
**IMPORTANT:** This tool uses a single, hardcoded registry file to prevent duplicate codes:

**Registry path:** `/Users/dan/LIBRARY_SYSTEM_REGISTRIES/filename-indexing-registry.json`

The registry is automatically created if it doesn't exist. On startup, the tool displays the registry path and verifies it's accessible. This ensures all users reference the same registry, preventing duplicate filename codes.

## Workflow
1. Run the script (with or without arguments).
2. The tool displays the registry path and verifies it exists (creating it if needed).
3. Press Enter to confirm and continue.
4. Choose whether to traverse subfolders recursively.
5. Provide one or more target files/folders.
6. The tool scans the allowed items, assigns new codes, renames them, and prints a summary that includes skipped items and conflicts.

## Notes
- The registry file is plain JSON with `next_index` and `used_codes` keys, making it easy to inspect or back up.
- The rename convention is `original----CODE.ext` for files and `folder----CODE` for directories.
- Conflicts are avoided by skipping when the destination name already exists; the corresponding code is rolled back so it can be reused on the next eligible item.
- **Never use multiple registry files** - this defeats the purpose and will create duplicate codes.
