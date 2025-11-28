# Law Journal Article File Renamer

Automatically rename PDF and Word document law journal articles using a standardized format and extract comprehensive metadata into structured files.

## Filename Format

```
[year]_[author_last_name]_[short_title].pdf
```

**Examples:**
```
1974_Arnold_Law_Fact_Medieval_Jury.pdf
2013_Lerner_Rise_Directed_Verdict_Jury_Power.pdf
2009_Appleman_Lost_Meaning_Jury_Trial_Right.pdf
```

## Features

### Intelligent Extraction

- **Multi-format support**: Works with both PDF and Word (.docx) documents
- **Document-first approach**: Prioritizes document text over filename hints
- **Smart author detection**: Extracts author names from document headers and footnotes
- **Title extraction**: Identifies article titles from first page
- **Publication date**: Finds year from headers, copyright notices, or journal citations
- **Journal metadata**: Extracts journal name, volume, issue, and page numbers

### Comprehensive Metadata Extraction

Extracts rich metadata including:
- **Core fields**: Authors, title, journal name, volume, issue, year, page ranges
- **Extended fields**: Abstract, keywords, DOI
- **Institutional fields**: Author affiliations and institutions
- **Citation fields**: Recommended citation format

### Output Files

**Renamed files:**
```
1974_Arnold_Law_Fact_Medieval_Jury.pdf
```

**Sidecar metadata** (optional, with `--extract-metadata`):
```
1974_Arnold_Law_Fact_Medieval_Jury.pdf.metadata.json
```

**Central registry** (optional, with `--extract-metadata --registry-path`):
```
metadata_registry.json  # Machine-readable
metadata_registry.csv   # Spreadsheet-compatible
```

## Quick Start

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

**For Word document support:**
```bash
pip install python-docx
```

### Basic Usage

**1. Preview Mode** (see what would be renamed):
```bash
python3 src/cli.py preview z_sample_articles/
```

**2. Rename Files:**
```bash
python3 src/cli.py rename z_sample_articles/
```

**3. Interactive Mode** (confirm each file):
```bash
python3 src/cli.py rename z_sample_articles/ --interactive
```

**4. With Metadata Extraction:**
```bash
python3 src/cli.py rename z_sample_articles/ --extract-metadata --registry-path ./article_registry
```

## How It Works

### Extraction Process

The tool extracts 3 core elements from each article:

1. **Author(s)** - From document headers, "By [NAME]" patterns, or footnote markers
2. **Title** - From first page, identified by position and formatting
3. **Year** - From publication date, copyright notice, or journal citation

Each extraction is tracked with a confidence score:
- **HIGH**: All 3 elements extracted from document text
- **MEDIUM**: 2 elements from document text
- **LOW**: Mostly from filename fallback

### Metadata Extraction

**Multi-zone reading:**
- Reads first 3 pages (title page, headers, abstract)
- Identifies patterns for abstract, keywords, DOI
- Extracts author affiliations from footnotes

**Pattern-based extraction:**
- Regex patterns for each metadata field
- Context-aware matching (abstract after title, keywords labeled, etc.)
- Defensive programming (one field failure doesn't break others)

### Smart Replacement Protection

**The system protects your manual work while improving garbage downloads.**

When deciding whether to rename a file, the system evaluates both:
1. **Existing filename quality** (is it good manual work or garbage?)
2. **Extraction confidence** (how reliable is the extracted data?)

#### Filename Quality Levels

**HIGH Quality** (good manual work):
- Contains author name (capitalized words)
- Has 4-digit year
- Uses underscores or hyphens
- Has 3+ meaningful words
- Reasonable length (15-80 characters)

**LOW Quality** (garbage downloads):
- Generic names: `download.pdf`, `document.pdf`, `untitled.pdf`
- Numbers in parentheses: `download(1).pdf`, `article(final).pdf`
- Source prefixes: `ssrn-12345.pdf`, `jstor-article.pdf`
- Very short (<10 chars) or very long (>100 chars)
- Random strings or hex patterns

#### Replacement Decision Matrix

| Extraction Confidence | Existing Filename | Action | Why |
|-----------------------|-------------------|--------|-----|
| HIGH | HIGH | ✓ Replace | Extracted version likely better |
| HIGH | MEDIUM/LOW | ✓ Replace | High confidence extraction |
| MEDIUM | **HIGH** | **✗ Skip** | **Protects your manual work** |
| MEDIUM | MEDIUM/LOW | ✓ Replace | Probable improvement |
| LOW | **HIGH/MEDIUM** | **✗ Skip** | **Too risky** |
| LOW | LOW | ✓ Replace | Can't be worse than garbage |
| UNKNOWN | ANY | ✗ Skip | Extraction failed |

#### Real Examples

**Protected (manual work preserved):**
```bash
# Good manual filename + uncertain extraction = SKIP
Lerner_Rise_of_Directed_Verdict_2013.pdf
  Quality: HIGH | Confidence: MEDIUM → SKIP ✗
  Reason: Keeping good manual filename
  (Extraction got wrong year: 1938 vs 2013)
```

**Improved (garbage downloads fixed):**
```bash
# Garbage filename + any confidence = REPLACE
download(1).pdf → 1974_Arnold_Law_Fact_Medieval_Jury.pdf
  Quality: LOW | Confidence: HIGH → REPLACE ✓
  Reason: Existing filename is garbage

ssrn-12345.pdf → 2009_Appleman_Lost_Meaning_Jury_Trial.pdf
  Quality: LOW | Confidence: MEDIUM → REPLACE ✓
  Reason: Any improvement over garbage filename
```

**Best case (both high quality):**
```bash
# Good filename + perfect extraction = REPLACE
Arnold_Law_Fact_Medieval_Jury_Trial_1974.pdf
  Quality: HIGH | Confidence: HIGH → REPLACE ✓
  Reason: Both high quality - extracted version likely better
```

## Project Structure

```
article-renamer/
├── src/
│   ├── cli.py                      # Command-line interface
│   ├── renamer.py                  # Main coordination engine
│   ├── config_manager.py           # Configuration persistence
│   ├── registry_manager.py         # Central registry manager
│   ├── extractors/
│   │   ├── pdf_extractor.py        # PDF text extraction
│   │   ├── docx_extractor.py       # Word text extraction
│   │   ├── author_extractor.py     # Author name extraction
│   │   ├── title_extractor.py      # Title extraction
│   │   ├── journal_extractor.py    # Journal metadata
│   │   ├── date_extractor.py       # Publication year
│   │   └── metadata_extractor.py   # Comprehensive metadata
│   ├── formatters/
│   │   └── title_formatter.py      # Title formatting for filenames
│   └── file_renamer/
│       └── models.py                # Data models
├── z_sample_articles/              # Sample PDFs for testing
└── README.md                       # This file
```

## Command-Line Options

```
python3 src/cli.py {preview|rename} PATH [OPTIONS]

Modes:
  preview           Show what would be renamed (dry run)
  rename            Actually rename the files

Arguments:
  PATH              File or directory to process

Options:
  --interactive, -i         Confirm each rename interactively
  --extract-metadata, -m    Extract comprehensive metadata
  --registry-path PATH, -r  Path for central metadata registry
  --output DIR, -o          Output directory (default: same as input)
```

## Examples

**Preview a single file:**
```bash
python3 src/cli.py preview "Arnold_Law_Fact_Medieval_Jury_Trial_1974.pdf"
```

**Rename all articles in a directory:**
```bash
python3 src/cli.py rename z_sample_articles/
```

**Interactive rename with metadata:**
```bash
python3 src/cli.py rename z_sample_articles/ --interactive --extract-metadata --registry-path ./registry
```

## Limitations & Notes

- **Extraction accuracy**: Depends on article formatting and PDF quality
- **Author detection**: Works best with standard academic article formats
- **Year extraction**: May pick up dates from article content (e.g., case years) instead of publication year
- **Title extraction**: May struggle with non-standard layouts or repository headers

## Future Improvements

- Improved pattern matching for author names
- Better handling of digital repository headers
- Support for multi-author formatting options
- Enhanced year detection (prioritize publication over content dates)
- Machine learning-based extraction for difficult cases

## Requirements

- Python 3.6+
- `pdftotext` command-line tool (part of poppler-utils)
- `python-docx` library for Word document support
- `pydantic` for data validation

## License

Open source - free to use and modify.
