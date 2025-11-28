# Changelog

All notable changes to the Caselaw PDF Renamer project.

## [0.2.0] - 2025-11-06

### Added

**Comprehensive Metadata Extraction**
- Extracts 7+ metadata fields from each case:
  - Disposition (affirmed, reversed, etc.)
  - Opinion author
  - Opinion type (majority, per curiam, etc.)
  - Lower court judge
  - Panel members (appellate courts)
  - Concurring/dissenting judges
  - Attorneys/counsel (best effort)
- Per-field confidence scoring (HIGH/MEDIUM/LOW)
- Multizone PDF reading (first 5 + last 2 pages)
- Pattern-based extraction with defensive error handling

**Central Registry System**
- JSON format for machine-readable data
- CSV format for spreadsheet analysis
- Automatic deduplication by source filename
- Timestamp tracking (extraction + processing)
- Incremental updates (no reprocessing needed)
- Atomic writes with automatic backups

**Configuration Management**
- Interactive registry path configuration on first use
- Persistent config file (`.caselaw_config.json`)
- Remembers preferences across sessions
- Easy reconfiguration workflow

**12 Safety & Reliability Improvements**

*File Operation Safety:*
1. Duplicate filename detection (auto-appends `_1`, `_2`, etc.)
2. Filename validation (length limits, illegal characters)
3. Automatic sanitization of problematic characters
4. Clear permission error handling

*Data Protection:*
5. Atomic file operations (write to temp, then rename)
6. Automatic backups before overwriting registry
7. Error recovery with temp file cleanup
8. Cross-platform filesystem compatibility

*User Experience:*
9. Dependency checking with helpful installation instructions
10. Detailed error messages with specific causes
11. File-by-file progress feedback and summary statistics
12. Configuration persistence with easy updates

**Enhanced Error Handling**
- Specific error messages for each failure type
- Context-aware error reporting (includes filename, field name)
- Graceful degradation when metadata extraction fails
- Division by zero protection when no files found

**Documentation**
- `INSTRUCTIONS_FOR_USE.md` - Complete step-by-step guide with exact commands
- `CHANGELOG.md` - This file
- `TROUBLESHOOTING.md` - Common issues and solutions
- Updated `README.md` with comprehensive feature documentation

### Changed

- **Filename prefix**: Changed from `cl.` to `c.` for brevity
  - Old: `cl.ILL_ND__2010__Abbott-v-Sandoz__743_FSupp2d_762.pdf`
  - New: `c.ILL_ND__2010__Abbott-v-Sandoz__743_FSupp2d_762.pdf`
- PDF timeout increased from 10s to 30s (45s for multizone extraction)
- `rename_file()` now returns tuple: `(success, actual_filename, error_msg)`
- Enhanced confidence calculation to account for metadata quality
- Improved case name extraction to better handle edge cases

### Fixed

- Division by zero error when processing empty directories
- Metadata extraction after file rename (file path bug)
- Silent failures now report specific error messages
- Filename length validation prevents OS errors
- Better handling of scanned/encrypted PDFs

### Technical Details

**New Modules:**
- `src/config_manager.py` - Configuration persistence
- `src/registry_manager.py` - Central registry management
- `src/extractors/metadata_extractor.py` - Comprehensive metadata extraction

**Enhanced Modules:**
- `src/cli.py` - Interactive prompts, dependency checking, better error handling
- `src/renamer.py` - Filename validation, sanitization, duplicate detection
- `src/extractors/pdf_extractor.py` - Multizone reading, configurable timeout

---

## [0.1.0] - 2025-10-XX

### Initial Release

**Core Functionality**
- PDF text extraction using `pdftotext`
- Bluebook court abbreviation mapping (200+ courts)
- Reporter citation formatting (100+ reporters)
- Intelligent extraction from PDF content
- Fallback extraction from filenames
- Confidence scoring (HIGH/MEDIUM/LOW)

**Format Specification**
- Standardized filename format: `cl.[court]__[year]__[case]__[reporter].pdf`
- Double underscores separate major components
- Script-safe (no spaces, all underscores)
- Bluebook-compliant court abbreviations

**Extraction Logic**
- Multi-line case caption handling
- Smart party name selection (surname vs. company name)
- Date filtering (ignores download timestamps)
- Header prioritization for reporter extraction
- Corporate vs. person name detection

**CLI Interface**
- Preview mode (dry run)
- Rename mode (actual renaming)
- Interactive mode (confirm each file)
- Single file and directory batch processing

**Sample Files**
- 6 diverse test cases covering:
  - Federal Supreme Court
  - Federal District Courts
  - State Supreme Courts
  - State Appeals Courts
  - State Trial Courts
  - Different reporter types (bound, LEXIS)

---

## Future Enhancements

Planned features for future releases:

- MS Word document support (.doc/.docx)
- Additional state trial court mappings
- GUI interface
- Multiple output format templates
- Undo/rollback functionality
- Batch edit capability
- Search/query interface for registry
- Export to additional formats (SQLite, XML)
- Parallel processing for large batches
- PDF OCR support for scanned documents
- Machine learning for improved extraction

---

## Version Numbering

This project uses [Semantic Versioning](https://semver.org/):
- **MAJOR**: Breaking changes to file format or API
- **MINOR**: New features, backward compatible
- **PATCH**: Bug fixes, backward compatible

---

## Links

- [README](./README.md) - Project overview and quick start
- [INSTRUCTIONS_FOR_USE](./INSTRUCTIONS_FOR_USE.md) - Step-by-step user guide
- [TROUBLESHOOTING](./TROUBLESHOOTING.md) - Common issues and solutions
- [TEST_RESULTS](./TEST_RESULTS.md) - Detailed test results
