# Caselaw File Renamer

Automatically rename PDF and Word caselaw files using standardized Bluebook format and extract comprehensive metadata into a searchable registry.

## Format

```
c.[court]__[year]__[case-name]__[volume_reporter_page].pdf
```

**Example:**
```
c.ILL_ND__2010__Abbott-v-Sandoz__743_FSupp2d_762.pdf
```

### Format Components

**Prefix:**
- `c.` - Single-character prefix for brevity

**Court Abbreviations:**
- Federal Supreme Court: `US`
- Federal Circuit Courts: `Cir_1`, `Cir_2`, `Cir_3`, etc.
- Federal District Courts: `VA_ED`, `ILL_ND`, `CA_CD`, etc. (STATE_DIRECTION format, state in ALL CAPS)
- State Supreme/Appeals: `Ga`, `Ga_Ct_App`, etc. (Bluebook abbreviations with underscores)
- State Trial Courts: `Ga_St_Ct_Fulton` (custom format)

**Case Names:**
- 1 word per party (smart selection: surname for persons, first word for companies)
- Special characters removed
- Hyphen-separated (e.g., `Abbott-v-Sandoz`, `ALDEN-v-MAINE`)

**Reporter Citations:**
- Format: `volume_reporter_page` (e.g., `743_FSupp2d_762`)
- No dots or spaces in reporter abbreviation
- LEXIS without volume: `USDistLEXIS_123570`

---

## Quick Start

📖 **New to this app?** See **[INSTRUCTIONS_FOR_USE.md](./INSTRUCTIONS_FOR_USE.md)** for detailed step-by-step instructions with exact commands to copy-paste.

### Prerequisites

**For PDF support:**
Install `pdftotext` (required for PDF text extraction):

**macOS:**
```bash
brew install poppler
```

**Ubuntu/Debian:**
```bash
sudo apt-get install poppler-utils
```

**Windows:**
Download from https://blog.alivate.com.au/poppler-windows/

**For Word document support:**
Install python-docx:
```bash
pip install -e .
```
(This is installed automatically when you install the package)

### 1. Preview Mode (Recommended First Step)

See what the tool would do without actually renaming files:

```bash
python3 src/cli.py preview sample_files/
```

### 2. Rename Files

**Interactive Mode** (confirm each file):
```bash
python3 src/cli.py rename sample_files/ --interactive
```

**Batch Mode** (rename all at once):
```bash
python3 src/cli.py rename sample_files/
```

**Single File:**
```bash
python3 src/cli.py preview "Abbott Labs. v. Sandoz, Inc (ND Ill 2010).pdf"
```

### 3. Extract Metadata (NEW!)

Extract comprehensive metadata and build a central registry:

```bash
python3 src/cli.py rename sample_files/ --extract-metadata
```

On first run, you'll be prompted to configure registry location. The app saves your preference for future use.

---

## Features

### Core Capabilities

**Intelligent Extraction:**
- **Multi-format support**: Works with both PDF and Word (.docx) documents
- **Document-first approach**: Prioritizes document text over filename hints
- **Multi-line case captions**: Handles "v" on separate line between parties
- **Smart name selection**: Surname for persons (3+ words), first word for companies
- **Date filtering**: Ignores download dates in margins, finds decision dates
- **Header prioritization**: Extracts reporter from case header, avoiding body citations

**Format Standards:**
- **Bluebook compliance**: Uses official Bluebook court abbreviations
- **Script-safe**: All underscores, no spaces
- **Readable**: Double underscores (`__`) separate major elements
- **Consistent**: Volume_Reporter_Page format for all citations

### NEW: Comprehensive Metadata Extraction

Extracts 7+ metadata fields per case:
- **Disposition**: Affirmed, Reversed, Vacated, Dismissed, etc.
- **Opinion Author**: Judge who wrote the opinion
- **Opinion Type**: Majority, Per Curiam, Plurality
- **Lower Court Judge**: Trial court judge (appellate cases)
- **Panel Members**: Judges on the panel (appellate cases)
- **Concurring/Dissenting**: Separate/concurring opinions
- **Attorneys**: Counsel for parties (best effort)

**Per-field confidence scoring:**
- HIGH: Strong pattern match
- MEDIUM: Likely correct
- LOW: Uncertain extraction

### NEW: Central Registry System

**Creates two registry formats:**
1. **JSON** (`metadata_registry.json`) - Machine-readable, preserves structure
2. **CSV** (`metadata_registry.csv`) - Open in Excel/Sheets for analysis

**Registry features:**
- Searchable database of all processed cases
- Automatic deduplication (by source filename)
- Timestamp tracking (extraction + processing time)
- Incremental updates (add new cases without reprocessing)

### Safety & Reliability (NEW: 12 Improvements)

**File Operation Safety:**
1. **Duplicate detection** - Automatically appends `_1`, `_2` if filename exists
2. **Validation** - Checks for illegal characters, filename length limits
3. **Sanitization** - Removes/replaces problematic characters automatically
4. **Permission handling** - Clear error messages for access issues

**Data Protection:**
5. **Atomic operations** - Writes to temp file, then renames (prevents corruption)
6. **Automatic backups** - Creates `.backup` files before updating registry
7. **Error recovery** - Cleans up temp files on failure
8. **Filesystem compatibility** - Works across macOS/Linux/Windows

**User Experience:**
9. **Dependency checking** - Validates `pdftotext` is installed with helpful errors
10. **Detailed error messages** - Shows specific cause (permissions, missing fields, etc.)
11. **Progress feedback** - File-by-file status and summary statistics
12. **Configuration management** - Remembers registry location across sessions

### Edge Cases Handled

- State trial courts not in standard Bluebook
- Timestamp fragments from download dates
- Multiple parties (takes first party only)
- Corporate vs. person name detection
- LEXIS citations with/without volume numbers
- Filename artifacts and prefixes
- Very long case names (auto-truncation with warning)
- Duplicate filenames (auto-numbering)
- Scanned PDFs with OCR issues (graceful fallback)

---

## Configuration

### Registry Configuration

**On first use with `--extract-metadata`:**
```
================================================================================
Metadata Registry Configuration
================================================================================

No default registry path configured.
Enter path for metadata registry (e.g., ./metadata_registry):
> /Users/dan/LIBRARY_SYSTEM_REGISTRIES/metadata_registry

Save this as default registry location? [Y/n]: y
✓ Saved as default registry path
```

**Configuration stored in:**
```
.caselaw_config.json
```

**To change registry location:**
```bash
# Option 1: Delete config and reconfigure
rm .caselaw_config.json

# Option 2: Edit directly
open .caselaw_config.json
```

---

## Output Files

### Renamed PDFs
```
c.ILL_ND__2010__Abbott-v-Sandoz__743_FSupp2d_762.pdf
```

### Sidecar Metadata (per PDF)
```
c.ILL_ND__2010__Abbott-v-Sandoz__743_FSupp2d_762.pdf.metadata.json
```

Contains full metadata for that specific case.

### Central Registry (all cases)
```
/Users/dan/LIBRARY_SYSTEM_REGISTRIES/
  metadata_registry.json      # Machine-readable
  metadata_registry.csv       # Spreadsheet-compatible
  metadata_registry.json.backup
  metadata_registry.csv.backup
```

---

## Test Results

**6 sample files processed:**
- ✅ 100% success rate
- ✅ 100% high confidence
- ✅ All elements extracted from PDF text
- ✅ Metadata extraction working for all cases
- ✅ Registry generated successfully

See [TEST_RESULTS.md](./docs/TEST_RESULTS.md) for detailed results.

---

## How It Works

### File Renaming

The tool extracts 4 key elements from each PDF:

1. **Court** - Using Bluebook abbreviations from 200+ court database
2. **Year** - From decision date (labeled "Decided:", "Filed:", etc.)
3. **Case Name** - From case caption, formatted to 1 word per party
4. **Reporter** - Citation with volume, reporter, and page number

Each extraction is tracked with a confidence score:
- **HIGH**: 3+ elements from PDF text
- **MEDIUM**: 2 elements from PDF text
- **LOW**: Mostly from filename fallback

### Metadata Extraction

**Multizone reading:**
- Reads first 5 pages (header, caption, opinion start)
- Reads last 2 pages (signatures, concurrences/dissents)
- Combines for comprehensive coverage

**Pattern-based extraction:**
- Regex patterns for each metadata field
- Context-aware matching (disposition at end, author at top, etc.)
- Defensive programming (one field failure doesn't break others)

**Registry management:**
- Loads existing registry (or creates new)
- Updates entry for each processed file
- Atomic write with backup before overwrite
- Exports to both JSON and CSV simultaneously

---

## Example Transformations

```
Abbott Labs. v. Sandoz, Inc (ND Ill 2010).pdf
→ c.ILL_ND__2010__Abbott-v-Sandoz__743_FSupp2d_762.pdf

Alden v. Me._Attachment1 (1st Cir 1999).pdf
→ c.US__1999__ALDEN-v-MAINE__527_US_706.pdf

law - GA COA - Adams v. State (Ga App 2000).pdf
→ c.Ga_Ct_App__2000__Adams-v-State__534_SE2d_538.pdf

Landrum v. Verg Enters., LLC (State Ct Fulton County 2024).pdf
→ c.Ga_St_Ct_Fulton__2024__Landrum-v-Verg__2024_GaStateLEXIS_4558.pdf
```

---

## Project Structure

```
file-renamer-caselaw/
├── src/
│   ├── cli.py                          # Command-line interface
│   ├── renamer.py                      # Main coordination engine
│   ├── config_manager.py               # Configuration persistence
│   ├── registry_manager.py             # Central registry manager
│   ├── file_renamer/                   # Modern system (pipeline-based)
│   │   ├── cli.py                      # Modern CLI
│   │   ├── pipeline.py                 # Renaming pipeline
│   │   ├── parsers/
│   │   │   ├── pdf_parser.py           # PDF parser
│   │   │   └── docx_parser.py          # Word parser (NEW)
│   │   └── models.py                   # Data models
│   ├── extractors/
│   │   ├── pdf_extractor.py            # PDF text extraction
│   │   ├── docx_extractor.py           # Word text extraction (NEW)
│   │   ├── court_extractor.py          # Court identification
│   │   ├── date_extractor.py           # Year extraction
│   │   ├── reporter_extractor.py       # Citation extraction
│   │   └── metadata_extractor.py       # Comprehensive metadata
│   ├── formatters/
│   │   └── case_name_formatter.py      # Case name parsing & formatting
│   └── data/
│       └── bluebook_courts_mapping.json
├── sample_files/                       # Test PDFs
├── .caselaw_config.json                # User configuration (generated)
├── bluebook_courts_mapping.json        # 200+ courts
├── reporters_database.json             # 100+ reporters
├── INSTRUCTIONS_FOR_USE.md             # Step-by-step guide (NEW)
├── TEST_RESULTS.md                     # Detailed test results
├── CHANGELOG.md                        # Version history (NEW)
├── TROUBLESHOOTING.md                  # Common issues (NEW)
└── README.md                           # This file
```

---

## Requirements

- Python 3.6+
- `pdftotext` command-line tool (part of poppler-utils) - for PDF support
- `python-docx` library - for Word document support (installed automatically)

**Supported file formats:**
- PDF (.pdf)
- Microsoft Word (.docx)

---

## Documentation

- **[INSTRUCTIONS_FOR_USE.md](./INSTRUCTIONS_FOR_USE.md)** - Complete step-by-step guide with exact commands
- **[CHANGELOG.md](./CHANGELOG.md)** - Version history and changes
- **[TROUBLESHOOTING.md](./TROUBLESHOOTING.md)** - Common issues and solutions
- **[TEST_RESULTS.md](./docs/TEST_RESULTS.md)** - Detailed test results
- **[FINAL_FORMAT_SUMMARY.md](./docs/FINAL_FORMAT_SUMMARY.md)** - Complete format specification

---

## Troubleshooting

### Common Issues

**"pdftotext not found"**
```bash
# macOS
brew install poppler

# Linux
sudo apt-get install poppler-utils
```

**"Permission denied"**
```bash
# Check permissions
ls -la /path/to/files/

# Fix ownership if needed
sudo chown -R $USER /path/to/files/
```

**"Registry path required"**
```bash
# Provide path explicitly
python3 src/cli.py preview sample_files/ --extract-metadata --registry-path ./my_registry
```

See [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) for more solutions.

---

## Version History

**v0.2.1** (Current)
- Added Microsoft Word (.docx) support
- Created comprehensive test suite (37 new tests)
- Updated both modern and legacy systems
- No breaking changes to PDF processing

**v0.2.0**
- Added comprehensive metadata extraction (7 fields)
- Added central registry system (JSON + CSV)
- Added interactive configuration with persistence
- Added 12 safety improvements (duplicates, validation, backups, etc.)
- Changed prefix from `cl.` to `c.`
- Enhanced error messages and user feedback

**v0.1.0**
- Initial release with core renaming functionality
- PDF text extraction
- Bluebook court abbreviations
- Reporter citation formatting

See [CHANGELOG.md](./CHANGELOG.md) for complete history.

---

## Future Enhancements

- RTF document support
- Legacy Word format (.doc) support
- Additional state trial court mappings
- GUI interface
- Multiple output format templates
- Undo/rollback functionality
- Batch edit capability
- Search/query interface for registry
- Export registry to other formats (SQLite, XML)

---

## License

Open source - free to use and modify.
