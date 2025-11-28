# AI Assistant Onboarding - Document Processor

**Comprehensive context for AI assistants new to this project**

Read this document once when starting a new session or when you need deep context. For quick reference during coding, use `llm.md`.

---

## Table of Contents

1. [Project Story](#project-story)
2. [The Problem We're Solving](#the-problem-were-solving)
3. [Architecture Philosophy](#architecture-philosophy)
4. [Existing Codebase Tour](#existing-codebase-tour)
5. [Migration Strategy](#migration-strategy)
6. [Technology Decisions](#technology-decisions)
7. [Design Patterns](#design-patterns)
8. [Common Scenarios](#common-scenarios)
9. [Pitfalls to Avoid](#pitfalls-to-avoid)
10. [SQLite Schema Deep Dive](#sqlite-schema-deep-dive)

---

## Project Story

### Where We Started

This project consolidates **four separate applications** that were built independently:

1. **step1a-caselaw** - Renames legal case PDFs using court, year, case name, reporter citation
2. **step1b-articles** - Renames academic articles using author, year, title
3. **step2-codes** - Adds unique 5-letter identifiers to any file
4. **step3a-convert** - Converts documents to clean text/markdown for AI consumption

Each application works well but:
- Has duplicated code (3 different PDF extractors, 3 registry systems)
- Can't share improvements across document types
- Forces users to run 4 separate tools in sequence
- Makes adding new document types (statutes, briefs, books) require copying entire app structure

### Where We're Going

**One unified application** with:
- Modular architecture that handles multiple document types
- Single SQLite registry replacing multiple JSON files
- Shared services layer (no duplicate extraction code)
- Plugin system for document types (caselaw, articles, statutes, briefs, books)
- Sequential pipeline: Rename → Code → Convert → Clean

### How We're Getting There

**Phased approach:**
- **Phase 1 (Current):** Build shared services layer
- **Phase 2:** Get caselaw working end-to-end (hardcoded, no plugins)
- **Phase 3:** Extract patterns to YAML configs
- **Phase 4:** Abstract to plugin system, add more document types

**Why this order?** We learned from architectural review that building the perfect plugin system upfront is the hardest part. Better to build one complete implementation, understand the patterns, THEN abstract.

---

## The Problem We're Solving

### User Workflow (Current Pain Points)

**Before (4 separate tools):**
```bash
# Step 1: Rename caselaw files
cd step1a--Base_FILENAME--a-caselaw
python src/cli.py process /path/to/cases

# Step 2: Add unique codes
cd ../step2--FILE_CODE_NAME---All Files
python filename_indexer.py /path/to/cases

# Step 3: Convert to text
cd ../step3a--NORMALIZE-TXT--MODERN--convert_to_txt--clean--add_headings
python -m doc_to_markdown.cli convert /path/to/cases

# For articles, repeat with step1b...
```

**After (unified tool):**
```bash
# One command, all steps
python main.py process /path/to/mixed_documents
# → Automatically detects types, processes each appropriately
```

### Document Type Challenges

Different document types need different handling:

**Caselaw:**
- Extract: Court, Year, Case Name, Reporter Citation
- Format: `c.ILL_ND__2010__Abbott-v-Sandoz__743_FSupp2d_762.pdf`
- Headings: Roman numerals, numbered sections, opinion structure

**Academic Articles:**
- Extract: Authors, Year, Title, Journal
- Format: `1974_Arnold_Law_Fact_Medieval_Jury.pdf`
- Headings: Abstract, sections, footnotes
- Challenge: Evaluate existing filename quality (don't replace good manual work)

**Statutes (Future):**
- Extract: Jurisdiction, Year, Code Section
- Format: `s.USC__2010__Title_42_Section_1983.pdf`
- Headings: Section numbers, subsections

**The Challenge:** Same pipeline (rename/code/convert/clean) but completely different regex patterns, extraction logic, and quality rules.

---

## Architecture Philosophy

### The Services Layer Insight

**Key architectural decision** (from expert review):

> "Your structure is 95% perfect. I would only add a `services` layer to keep the 'Orchestrator' clean."

This insight shaped our entire architecture:

```
BEFORE (common anti-pattern):
┌─────────────────────────────────────┐
│ orchestrator.py                     │
│                                     │
│ def process_file(path):             │
│   # Opens PDF directly              │
│   import pdfplumber                 │
│   with pdfplumber.open(path) as pdf:│
│     text = extract_text(pdf)        │  ❌ Implementation details
│   # Writes to database directly     │
│   conn = sqlite3.connect(...)       │  ❌ in orchestrator
│   conn.execute("INSERT ...")        │
│   # Implements extraction logic     │
│   if "United States" in text:       │  ❌ Business logic
│     court = parse_court(text)       │  ❌ here too
└─────────────────────────────────────┘
```

```
AFTER (services layer pattern):
┌─────────────────────────────────────┐
│ orchestrator.py                     │  ✅ Workflow only
│                                     │
│ def process_file(path):             │
│   text = text_extractor.extract()  │  ✅ Delegate to services
│   doc_type = classifier.classify() │
│   metadata = extract_metadata()    │
│   registrar.save(metadata)          │
└─────────────────────────────────────┘
        ↓ calls ↓
┌─────────────────────────────────────┐
│ services/                           │  ✅ Pure business logic
│   text_extractor.py                 │  ✅ Stateless
│   classifier.py                     │  ✅ Testable
│   registrar.py                      │  ✅ Swappable
└─────────────────────────────────────┘
```

**Benefits:**
- **Orchestrator:** ~200 lines, easy to understand workflow
- **Services:** Independently testable, reusable, no state
- **Debugging:** Clear responsibility boundaries
- **Swapping:** Can replace SQLite with PostgreSQL by changing only registrar.py

### Caselaw-First Development

**Why not build the perfect plugin system first?**

From architectural review:
> "The hardest part of this to build is the 'Plugin System' where a string in YAML (`extractors.JurisdictionExtractor`) becomes a running Python class."

**Our approach:**
1. Build complete caselaw processing (hardcoded)
2. See what patterns emerge
3. Extract common code
4. Build plugin abstraction based on real needs (not speculation)

**Example of what we'll learn:**

After implementing caselaw AND articles, we might discover:
- Both need "extract_metadata()" but signatures differ
- Both need filename templates but structure differs
- Both need heading detection but patterns completely differ

Only THEN can we design the right `BasePlugin` interface. Building it now = guessing.

---

## Existing Codebase Tour

### step1a: Caselaw Renamer (Most Mature)

**Purpose:** Extract metadata from legal case PDFs and generate standardized filenames.

**Key Components:**

#### Extractors (src/extractors/)
```python
# court_extractor.py
# - 200+ court patterns in bluebook_courts_mapping.json
# - Federal: SCOTUS, 13 Circuits, 94 District Courts
# - State: All 50 states (supreme, appeals, trial courts)
# - Pattern: "United States District Court for the Northern District of Illinois"
# - Output: "ILL_ND" (filename-safe Bluebook code)

# reporter_extractor.py
# - Citation patterns: "743 F. Supp. 2d 762"
# - 100+ reporters in reporters_database.json
# - Output: "743_FSupp2d_762" (filename-safe)

# date_extractor.py
# - Multiple strategies: PDF metadata, text patterns
# - Handles various formats: "2010", "December 15, 2010", "Dec. 15, 2010"
# - Output: "2010" (year only)

# case_name_formatter.py
# - Multi-line format: "Party Name\nv\nOther Party"
# - Single-line format: "Party v. Other Party"
# - Extracts first party vs second party
# - Smart surname selection for people vs company names
# - Output: "Abbott-v-Sandoz"
```

**Reference Data:**
```json
// bluebook_courts_mapping.json
{
  "federal": {
    "district_courts": {
      "pattern": "United States District Court.*for the\\s+(Northern|...)\\s+District\\s+of\\s+([A-Za-z\\s]+)",
      "northern_illinois": {
        "bluebook": "N.D. Ill.",
        "filename_code": "ILL_ND"
      }
    }
  }
}
```

**What to Reuse:**
- ✅ All extractors - they work well, comprehensive patterns
- ✅ Reference data - critical, don't modify
- ✅ Confidence scoring pattern (HIGH/MEDIUM/LOW)
- 🔄 PDF extraction - refactor to use pdfplumber in services/

**What NOT to Port:**
- ❌ Modern file_renamer/ system - too complex for Phase 1
- ❌ Registry manager - replaced by SQLite in services/registrar.py

---

### step1b: Articles Renamer (Quality-Aware)

**Purpose:** Extract author, title, year from academic articles.

**Key Components:**

#### Extractors (src/extractors/)
```python
# author_extractor.py
# - Multiple pattern strategies:
#   1. All-caps with footnote: "LAURA I APPLEMAN*"
#   2. "By [NAME]" format
#   3. Title case with footnote: "Morris S. Arnold*"
# - Affiliation detection: "* Professor of Law, Yale"
# - False positive filters: "TABLE OF CONTENTS", "ABSTRACT", etc.
# - Output: ['Morris S. Arnold', 'Laura I Appleman']
# - Filename: First author's last name → "Arnold"

# title_extractor.py
# - Position-based: Title appears BEFORE author line
# - Pattern matching: Title case, colon for subtitles
# - Filters repository headers: "Digital Repository", "Faculty Scholarship"
# - Multi-line title combining
# - Output: "Law, Fact, and the Medieval Jury Trial"

# journal_extractor.py
# - Journal name detection
# - Volume/issue extraction
# - Publication metadata
```

**Unique Feature: Filename Quality Evaluation**
```python
# filename_evaluator.py
# Decision matrix:
# - HIGH extraction confidence + ANY quality → REPLACE
# - MEDIUM confidence + LOW quality → REPLACE
# - MEDIUM confidence + HIGH quality → SKIP (protect manual work!)
# - LOW confidence + not LOW quality → SKIP (too risky)

# Quality indicators:
# - Has year, author, underscores/hyphens
# - Not "download.pdf", "ssrn-123.pdf", "untitled.pdf"
# - 15-80 characters, 3+ words
```

**What to Reuse:**
- ✅ Author/title/journal extractors
- ✅ Filename quality evaluation logic (article-specific)
- ✅ Pattern: Extract → Evaluate → Decide

**What to Adapt:**
- 🔄 Quality evaluation - make it plugin-specific (not all types need this)

---

### step2: Unique Code Generator (Simple but Clever)

**Purpose:** Append unique 5-letter codes to filenames/folders.

**Key Logic:**
```python
# Base-25 alphabet (A-Z except W) = 25^5 = 9,765,625 codes
ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVXYZ"  # No W

def index_to_code(idx: int) -> str:
    """0 → AAAAA, 1 → AAAAB, 25 → AAAAZ, 26 → AAAAC, etc."""
    code = []
    for _ in range(5):
        code.append(ALPHABET[idx % 25])
        idx //= 25
    return ''.join(reversed(code))

# Output format: "filename----CODE.ext"
# Or for folders: "foldername----CODE"
```

**Registry Management:**
```json
// filename-indexing-registry.json
{
  "next_index": 1234,
  "used_codes": ["AAAAB", "AAAAC", "AAAAD", ...]
}
```

**Atomic Operations:**
- Write to temp file
- Rename to registry.json (atomic on most filesystems)
- Rollback code if rename fails

**What to Reuse:**
- ✅ Base-25 encoding logic → `services/code_generator.py`
- ✅ Suffix pattern: `----CODE`
- ✅ Rollback logic

**What to Replace:**
- 🔄 JSON registry → SQLite codes table
- 🔄 Standalone script → service called by pipeline

---

### step3a: Document Converter (AI-Ready Output)

**Purpose:** Convert PDF/DOCX/EPUB to clean markdown/text optimized for RAG.

**Key Components:**

#### Converters (doc_to_markdown/converters/)
```python
# pdf.py - Uses marker-pdf (AI-powered structure detection)
# word.py - Uses Pandoc with custom options
# ebook.py - Uses Calibre → Pandoc chain

# Each converter:
# - Extracts images to ./images/
# - Adds YAML frontmatter with metadata
# - Returns markdown with preserved structure
```

#### Markdown Cleaner (RAG-Optimized)
```python
# markdown_cleaner.py
# Why needed: Embedding models require consistent formatting

def clean_markdown(text):
    # 1. Normalize line endings (Windows/Mac → Unix)
    # 2. UTF-8 fixes (smart quotes → ASCII, remove BOM)
    # 3. Remove control characters
    # 4. Normalize headings (##Heading → ## Heading)
    # 5. Normalize spacing (max 2 blank lines, no trailing)
    # 6. Clean frontmatter spacing

# Result: Stable embeddings, reproducible chunking
```

#### OCR Text Cleaner (Historical Documents)
```python
# clean_txt.py - Regex-only, no APIs/AI
# - Preserves: ---[PDF Page 42]--- markers
# - Removes: Repeated headers/footers (frequency ≥ 3)
# - Marks headings: All-caps → # Heading
# - Repairs: Hyphenation "bro-\nken" → "broken"
# - Modernizes: "publick" → "public", "honour" → "honor"
```

#### Tracking System
```python
# tracking.py - SQLite database
# Tracks: file hash, conversion date, output path
# Prevents: Re-processing unchanged files
# Categorizes: NEW, MODIFIED, UNCHANGED
```

**What to Reuse:**
- ✅ markdown_cleaner.py (RAG optimization is valuable)
- ✅ clean_txt.py patterns (OCR cleaning)
- ✅ Tracking concept → merge into services/registrar.py

**What to Adapt:**
- 🔄 SQLite schema → integrate into unified registry
- 🔄 Converters → may simplify (use pdfplumber directly for Phase 1)

---

## Migration Strategy

### Code Consolidation Plan

#### Duplicated Code to Merge

**Three PDF Extractors → One Service:**
```python
# Current:
step1a/src/extractors/pdf_extractor.py  # Uses pdftotext subprocess
step1b/src/extractors/pdf_extractor.py  # Uses pdftotext subprocess
step3a/doc_to_markdown/converters/pdf.py # Uses marker-pdf (ML models)

# After migration:
src/services/text_extractor.py
  - extract_text(path, format='plain') → pdfplumber extraction
  - extract_text(path, format='markdown') → Could add marker-pdf later
  - Unified interface, one implementation
```

**Three Registry Systems → One SQLite Database:**
```python
# Current:
step1a/src/registry_manager.py           # JSON + CSV export
step1b/src/registry_manager.py           # JSON + CSV export
step2/filename-indexing-registry.json    # Standalone JSON
step3a/doc_to_markdown/tracking.py       # SQLite

# After migration:
src/services/registrar.py
  - Single SQLite database in registry/master.db
  - Combines all tracking needs
  - Export to JSON/CSV still supported
```

#### Extraction Code: Reuse As-Is

**No changes needed:**
```python
# Court patterns work great, comprehensive coverage
src/extractors/court_extractor.py       # ← From step1a
src/extractors/reporter_extractor.py    # ← From step1a
src/extractors/case_name_formatter.py   # ← From step1a

# Article extraction well-developed
src/extractors/author_extractor.py      # ← From step1b
src/extractors/title_extractor.py       # ← From step1b
src/extractors/journal_extractor.py     # ← From step1b

# Both use same date logic
src/extractors/date_extractor.py        # ← From step1a or step1b (identical)
```

**Reference data:**
```python
data/bluebook_courts_mapping.json  # ← From step1a (don't modify)
data/reporters_database.json       # ← From step1a (don't modify)
```

#### Renaming Logic: Refactor Structure

**Current:**
```python
# step1a/src/renamer.py - Hardcoded caselaw logic
def process_file(path):
    court = court_extractor.extract(text)
    year = date_extractor.extract(text)
    case_name = case_name_formatter.extract(text)
    reporter = reporter_extractor.extract(text)
    new_name = f"c.{court}__{year}__{case_name}__{reporter}.pdf"
```

**After Phase 2:**
```python
# src/steps/rename_step.py - Generic step
def execute(document):
    doc_type = classifier.classify(document.text)
    # Hardcoded switch for Phase 2:
    if doc_type == DocumentType.CASELAW:
        metadata = extract_caselaw_metadata(document)
        new_name = format_caselaw_filename(metadata)
```

**After Phase 4:**
```python
# src/steps/rename_step.py - Plugin-based
def execute(document):
    doc_type = classifier.classify(document.text)
    plugin = factory.get_plugin(doc_type)
    metadata = plugin.extract_metadata(document)
    new_name = plugin.format_filename(metadata)
```

---

## Technology Decisions

### PDF Extraction: pdfplumber (Not pdftotext)

**Current approach (step1a/step1b):**
```python
# subprocess call to external tool
subprocess.run(['pdftotext', '-layout', '-f', '1', '-l', '2', path, '-'])
```

**Problems:**
- Requires external installation (poppler-utils)
- Subprocess overhead
- Platform-specific paths
- Harder to debug
- No Python-level error handling

**New approach:**
```python
import pdfplumber

with pdfplumber.open(path) as pdf:
    text = "\n".join(page.extract_text() or "" for page in pdf.pages[:2])
```

**Benefits:**
- Pure Python (pip install)
- Better table extraction
- Layout analysis capabilities
- Image extraction built-in
- Consistent error handling
- Works same on all platforms

### Registry: SQLite (Not Multiple JSON Files)

**Current fragmentation:**
```
step1a: ~/.caselaw_config.json + metadata_registry.json + metadata_registry.csv
step1b: ~/.articles_config.json + metadata_registry.json + metadata_registry.csv
step2: /LIBRARY_SYSTEM_REGISTRIES/filename-indexing-registry.json
step3a: doc_to_markdown_history.db (SQLite)
```

**Problems:**
- No referential integrity
- Concurrent access issues
- Manual JSON merging
- CSV export duplication
- No query capabilities

**New approach:**
```sql
-- Single database: registry/master.db
-- Referential integrity with foreign keys
-- WAL mode for concurrent access
-- SQL queries for complex operations
-- Still export JSON/CSV for analysis
```

**Benefits:**
- Single source of truth
- ACID transactions
- Better query performance
- Export capabilities maintained
- Already have schema from step3a to build on

### Configuration: YAML Patterns (Not Dynamic Loading)

**Rejected approach:**
```yaml
# config/caselaw.yaml
extractors:
  court: "extractors.court_extractor.CourtExtractor"  # ❌ String → class

# Python code:
import importlib
module_name, class_name = config['extractors']['court'].rsplit('.', 1)
module = importlib.import_module(module_name)  # ❌ Hard to debug
ExtractorClass = getattr(module, class_name)
```

**Problems:**
- Hard to debug (string typos = runtime errors)
- No IDE support (autocomplete, go-to-definition)
- Type safety lost
- Testing harder
- Over-engineering for uncertain future needs

**Accepted approach (Phase 3):**
```yaml
# config/caselaw_patterns.yaml
court_patterns:
  federal_district:
    regex: "United States District Court.*for the\\s+(Northern|Southern|...)\\s+District\\s+of\\s+([A-Za-z\\s]+)"
    weight: 0.8

filename_template: "c.{court}__{year}__{case_name}__{reporter}.{ext}"
```

```python
# Python code: Classes hardcoded, patterns from YAML
from extractors.court_extractor import CourtExtractor  # ✅ Direct import
patterns = yaml.load('config/caselaw_patterns.yaml')
extractor = CourtExtractor(patterns=patterns['court_patterns'])
```

**Benefits:**
- Patterns editable without code changes
- Still get type safety and IDE support
- Easy to debug
- Simpler implementation
- Can always add dynamic loading later if truly needed

---

## Design Patterns

### 1. Services Pattern (Core Architecture)

**Definition:** Separate business logic from orchestration.

**Structure:**
```python
# Service interface
class TextExtractor:
    @staticmethod
    def extract_text(path: Path) -> ExtractionResult:
        """Pure function: no state, no side effects (except reading file)"""

# Orchestrator uses service
class Orchestrator:
    def __init__(self, text_extractor: TextExtractor):
        self.text_extractor = text_extractor  # Dependency injection

    def process(self, path: Path):
        result = self.text_extractor.extract_text(path)  # Delegate
```

**Benefits:**
- Services are testable in isolation
- Easy to mock for testing
- Can swap implementations (e.g., different PDF libraries)

### 2. Repository Pattern (Registrar)

**Definition:** Abstract data persistence behind an interface.

**Structure:**
```python
class Registrar:
    def add_document(self, path: Path, metadata: dict) -> None:
        """Interface doesn't specify SQLite"""

    def get_document(self, path: Path) -> Optional[Document]:
        """Could be SQLite, PostgreSQL, MongoDB..."""

# Implementation detail hidden:
class SQLiteRegistrar(Registrar):
    def add_document(self, path, metadata):
        conn = sqlite3.connect(self.db_path)
        # ... SQLite-specific code
```

**Benefits:**
- Can replace SQLite with PostgreSQL later
- Tests can use in-memory database
- Business logic doesn't know about SQL

### 3. Strategy Pattern (Future Plugin System)

**Definition:** Define family of algorithms (document type handling), make them interchangeable.

**Structure (Phase 4):**
```python
class BasePlugin(ABC):
    @abstractmethod
    def extract_metadata(self, text: str) -> dict:
        pass

class CaselawPlugin(BasePlugin):
    def extract_metadata(self, text):
        return {
            'court': self.court_extractor.extract(text),
            'year': self.date_extractor.extract(text),
            # ... caselaw-specific
        }

class ArticlePlugin(BasePlugin):
    def extract_metadata(self, text):
        return {
            'authors': self.author_extractor.extract(text),
            'title': self.title_extractor.extract(text),
            # ... article-specific
        }
```

**Benefits:**
- Add new document types without changing orchestrator
- Each type encapsulates its own logic
- Easy to test individual types

### 4. Template Method Pattern (Pipeline Steps)

**Definition:** Define algorithm skeleton, let subclasses override specific steps.

**Structure:**
```python
class BaseStep(ABC):
    def execute(self, document: Document) -> StepResult:
        """Template method - defines workflow"""
        if not self.should_process(document):
            return StepResult(status='skipped')

        try:
            result = self.do_process(document)  # ← Subclass implements
            self.update_registry(document, result)
            return StepResult(status='success', data=result)
        except Exception as e:
            return StepResult(status='failed', error=str(e))

    @abstractmethod
    def do_process(self, document: Document):
        """Subclass implements specific processing"""
        pass

class RenameStep(BaseStep):
    def do_process(self, document):
        # Specific rename logic here
        pass
```

---

## Common Scenarios

### Scenario 1: Adding a New Extractor

**Situation:** You need to extract "Disposition" from case documents (Affirmed, Reversed, etc.)

**Steps:**
```python
# 1. Create new extractor in src/extractors/
# File: src/extractors/disposition_extractor.py

from typing import Optional
import re

class DispositionExtractor:
    """Extracts case disposition from legal opinions."""

    DISPOSITION_PATTERNS = [
        r'\b(AFFIRMED|REVERSED|REMANDED|VACATED|DISMISSED)\b',
        r'[Tt]he judgment.*is (affirmed|reversed|remanded)',
    ]

    def extract_from_text(self, text: str) -> Optional[str]:
        """
        Extract disposition from document text.

        Returns:
            'Affirmed', 'Reversed', etc., or None if not found
        """
        # Look in last 20% of document (dispositions usually at end)
        end_portion = text[-len(text)//5:]

        for pattern in self.DISPOSITION_PATTERNS:
            match = re.search(pattern, end_portion, re.IGNORECASE)
            if match:
                return match.group(1).title()

        return None

# 2. Write tests
# File: tests/test_extractors/test_disposition_extractor.py

def test_extract_affirmed():
    text = "...For the foregoing reasons, AFFIRMED."
    result = DispositionExtractor().extract_from_text(text)
    assert result == "Affirmed"

def test_extract_not_found():
    text = "...This is a motion for summary judgment."
    result = DispositionExtractor().extract_from_text(text)
    assert result is None

# 3. Integrate into metadata extraction (Phase 2)
# File: src/plugins/caselaw.py (or wherever caselaw logic lives in current phase)

from extractors.disposition_extractor import DispositionExtractor

def extract_caselaw_metadata(text: str, filename: str) -> dict:
    # ... existing extractors
    disposition = DispositionExtractor().extract_from_text(text)

    return {
        # ... existing fields
        'disposition': disposition,
        'disposition_source': 'document' if disposition else 'not_found',
    }

# 4. Update schema to store it (if needed)
# File: src/services/registrar.py

# Add to metadata table (already flexible key-value, so might not need schema change)
# But document it:
# metadata.key = 'disposition'
# metadata.value = 'Affirmed'

# 5. Log the addition
# File: 1-Context-Documentation/4-Logbook.md

## 2025-XX-XX - Added Disposition Extraction

### Context
User requested tracking case dispositions (Affirmed, Reversed, etc.) for outcome analysis.

### Implementation
- Created `extractors/disposition_extractor.py`
- Searches last 20% of document (dispositions typically at end)
- Pattern matching for common disposition language
- Returns None if not found (not all documents have explicit dispositions)

### Testing
- Unit tests with sample opinions
- Tested with step1a sample files: 8/10 had extractable dispositions

### Next Steps
- Consider adding to filename template (TBD - might make names too long)
```

### Scenario 2: Debugging Failed PDF Extraction

**Situation:** PDF extraction returns empty text for a specific file.

**Debugging steps:**
```python
# 1. Test extraction directly
from pathlib import Path
from services.text_extractor import extract_text

result = extract_text(Path("problem_file.pdf"))
print(f"Success: {result.success}")
print(f"Text length: {len(result.text)}")
print(f"Error: {result.error_message}")
print(f"First 500 chars: {result.text[:500]}")

# 2. Check if PDF is actually text-based (vs scanned image)
import pdfplumber
with pdfplumber.open("problem_file.pdf") as pdf:
    page = pdf.pages[0]
    text = page.extract_text()
    print(f"Page 1 text: {text}")

    # Check if it's an image-based PDF
    if not text or len(text.strip()) < 50:
        print("WARNING: PDF appears to be scanned image (OCR needed)")
        print(f"Page has {len(page.images)} images")

# 3. Try extracting tables (might be tabular layout)
    tables = page.extract_tables()
    if tables:
        print(f"Found {len(tables)} tables")
        print(tables[0])  # First table

# 4. Check PDF metadata
import PyPDF2
with open("problem_file.pdf", "rb") as f:
    pdf = PyPDF2.PdfReader(f)
    info = pdf.metadata
    print(f"Creator: {info.get('/Creator')}")
    print(f"Producer: {info.get('/Producer')}")
    print(f"Pages: {len(pdf.pages)}")

# 5. If image-based PDF, note in logbook
# File: 1-Context-Documentation/4-Logbook.md

## Issue: Image-Based PDFs Not Extracting

### Problem
File "Abbott_v_Sandoz_scan.pdf" returns empty text extraction.

### Root Cause
PDF is scanned image, not text-based. pdfplumber can't extract text from images.

### Solutions
A. Short-term: Skip and log warning
B. Long-term: Add OCR support (tesseract) in Phase 3+

### Implementation (Short-term)
- Modified text_extractor.py to detect image-based PDFs
- Returns ExtractionResult with warning flag
- Classifier skips files without extractable text
```

### Scenario 3: Adding Support for a New Court

**Situation:** Extractor doesn't recognize "Arizona Court of Appeals, Division 1"

**Steps:**
```json
// 1. Add to bluebook_courts_mapping.json
// File: data/bluebook_courts_mapping.json

{
  "state": {
    "arizona": {
      "supreme": {
        "bluebook": "Ariz.",
        "filename_code": "Ariz",
        "patterns": ["Arizona Supreme Court"]
      },
      "appeals": {
        "bluebook": "Ariz. Ct. App.",
        "filename_code": "Ariz_Ct_App",
        "patterns": [
          "Arizona Court of Appeals",
          "Court of Appeals of Arizona"
        ]
      }
    }
  }
}
```

```python
# 2. Test that court_extractor now recognizes it
# File: tests/test_extractors/test_court_extractor.py

def test_arizona_court_of_appeals():
    text = "Arizona Court of Appeals, Division 1"
    result = CourtExtractor().extract_from_text(text)
    assert result == "Ariz_Ct_App"

# 3. No code changes needed - extractor loads patterns from JSON
# 4. Document in logbook if significant
```

---

## Pitfalls to Avoid

### 1. Premature Abstraction

**Pitfall:**
```python
# Building generic plugin system before understanding needs
class BasePlugin(ABC):
    @abstractmethod
    def extract_field_1(self): pass  # What is field_1?
    @abstractmethod
    def extract_field_2(self): pass  # Guessing at interface
```

**Why it's wrong:**
- Don't know what methods all document types actually need
- Interface will be wrong, require refactoring anyway
- Wastes time building unused abstractions

**Right approach:**
```python
# Phase 2: Hardcode caselaw
def extract_caselaw_metadata(text):
    return {'court': ..., 'year': ..., 'case_name': ..., 'reporter': ...}

# Later, add articles (also hardcoded)
def extract_article_metadata(text):
    return {'authors': ..., 'year': ..., 'title': ...}

# Phase 4: NOW abstract (you know what's common)
class BasePlugin(ABC):
    @abstractmethod
    def extract_metadata(self, text) -> dict:  # ← Simple, clear interface
        pass
```

### 2. Mixing Concerns

**Pitfall:**
```python
# Putting database writes in extraction functions
def extract_court(text):
    court = parse_court_name(text)

    # ❌ Don't do this
    conn = sqlite3.connect('registry.db')
    conn.execute("INSERT INTO extractions ...")

    return court
```

**Why it's wrong:**
- Can't test extraction without database
- Can't reuse extraction in different contexts
- Violates single responsibility principle

**Right approach:**
```python
# Extractor: pure function
def extract_court(text) -> str:
    return parse_court_name(text)  # Just return the value

# Orchestrator: coordinates saving
def process_file(path):
    text = text_extractor.extract_text(path)
    court = court_extractor.extract_court(text)
    registrar.save_metadata(path, {'court': court})  # ← Save here
```

### 3. Recreating Existing Code

**Pitfall:**
```python
# Writing new court extraction when it already exists
def extract_court_new(text):
    if "Supreme Court" in text:
        return "SCOTUS"
    # ... incomplete patterns
```

**Why it's wrong:**
- step1a has 200+ court patterns (years of refinement)
- Your new code will miss edge cases
- Duplicates maintenance burden

**Right approach:**
```python
# Reuse existing extractor
from extractors.court_extractor import CourtExtractor

court = CourtExtractor().extract_from_pdf(text)
```

### 4. Subprocess Over-Use

**Pitfall:**
```python
# Using shell commands for what Python libraries can do
import subprocess

def extract_pdf_text(path):
    result = subprocess.run(['pdftotext', path, '-'], capture_output=True)
    return result.stdout.decode()
```

**Why it's wrong:**
- Platform-dependent (pdftotext path varies)
- Requires external installation
- Harder to debug
- Security risks with path injection

**Right approach:**
```python
import pdfplumber

def extract_pdf_text(path):
    with pdfplumber.open(path) as pdf:
        return "\n".join(p.extract_text() or "" for p in pdf.pages)
```

### 5. Monolithic Functions

**Pitfall:**
```python
# 500-line function that does everything
def process_document(path):
    # Extract text
    if path.endswith('.pdf'):
        # ... 50 lines of PDF extraction
    else:
        # ... 50 lines of DOCX extraction

    # Classify document type
    # ... 100 lines of classification logic

    # Extract metadata
    # ... 100 lines of extraction

    # Generate filename
    # ... 50 lines of formatting

    # Rename file
    # ... 50 lines of file operations

    # Update registry
    # ... 50 lines of database code
```

**Why it's wrong:**
- Impossible to test individual parts
- Hard to debug
- Can't reuse components
- Violates single responsibility

**Right approach:**
```python
# Services layer - each does one thing
def process_document(path):
    text = text_extractor.extract_text(path)           # ← Service
    doc_type = classifier.classify(text.text)          # ← Service
    metadata = extract_metadata(text.text, doc_type)   # ← Uses extractors
    new_name = generate_filename(metadata, doc_type)   # ← Formatter
    rename_file(path, new_name)                        # ← File operation
    registrar.update(path, metadata)                   # ← Service
```

---

## SQLite Schema Deep Dive

### Complete Schema

```sql
-- Main documents table
CREATE TABLE documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- File identification
    file_path TEXT UNIQUE NOT NULL,
    original_filename TEXT NOT NULL,
    current_filename TEXT NOT NULL,
    file_hash TEXT,  -- SHA-256 for change detection

    -- Classification
    document_type TEXT,  -- 'caselaw', 'article', 'statute', etc.
    classification_confidence REAL,  -- 0.0 to 1.0

    -- Unique code
    unique_code TEXT UNIQUE,  -- 5-letter code (AAAAA, AAAAB, etc.)

    -- Timestamps
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_processed TIMESTAMP,

    -- Status
    processing_status TEXT DEFAULT 'pending',  -- 'pending', 'complete', 'failed'

    -- Foreign key constraints
    CONSTRAINT fk_code FOREIGN KEY (unique_code)
        REFERENCES codes(code) ON DELETE SET NULL
);

-- Flexible metadata storage (key-value pairs)
CREATE TABLE metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,

    -- Metadata field
    key TEXT NOT NULL,  -- 'court', 'year', 'author', etc.
    value TEXT,

    -- Extraction tracking
    source TEXT,  -- 'document', 'filename', 'fallback'
    confidence TEXT,  -- 'HIGH', 'MEDIUM', 'LOW'
    extractor TEXT,  -- 'CourtExtractor', 'AuthorExtractor', etc.
    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
    UNIQUE(document_id, key)  -- One value per key per document
);

-- Processing step history
CREATE TABLE processing_steps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,

    -- Step identification
    step_name TEXT NOT NULL,  -- 'rename', 'code', 'convert', 'clean'
    step_order INTEGER,  -- 1, 2, 3, 4

    -- Execution
    status TEXT NOT NULL,  -- 'pending', 'success', 'failed', 'skipped'
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    duration_seconds REAL,

    -- Results
    error_message TEXT,
    warning_message TEXT,
    output_path TEXT,  -- For convert/clean steps

    -- Debugging
    config_snapshot TEXT,  -- JSON of configuration used

    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
);

-- Unique code allocation
CREATE TABLE codes (
    code TEXT PRIMARY KEY,  -- 'AAAAA', 'AAAAB', etc.

    -- Allocation
    allocated_at TIMESTAMP,
    allocated_to_document INTEGER,  -- NULL if rolled back

    -- Status
    status TEXT DEFAULT 'allocated',  -- 'allocated', 'in_use', 'rolled_back'

    FOREIGN KEY (allocated_to_document)
        REFERENCES documents(id) ON DELETE SET NULL
);

-- Code allocation sequence (for base-25 counter)
CREATE TABLE code_sequence (
    id INTEGER PRIMARY KEY CHECK (id = 1),  -- Only one row
    next_index INTEGER NOT NULL DEFAULT 0  -- Current counter
);

-- Initial sequence value
INSERT INTO code_sequence (id, next_index) VALUES (1, 0);

-- Indices for performance
CREATE INDEX idx_documents_type ON documents(document_type);
CREATE INDEX idx_documents_status ON documents(processing_status);
CREATE INDEX idx_documents_code ON documents(unique_code);
CREATE INDEX idx_metadata_document ON metadata(document_id);
CREATE INDEX idx_metadata_key ON metadata(key);
CREATE INDEX idx_steps_document ON processing_steps(document_id);
CREATE INDEX idx_steps_status ON processing_steps(status);
CREATE INDEX idx_codes_status ON codes(status);
```

### Why This Schema?

**documents table:**
- Tracks file identity and current state
- Foreign key to codes for referential integrity
- file_hash enables change detection (re-process if modified)

**metadata table (flexible key-value):**
- Different document types have different fields
- Caselaw: court, year, case_name, reporter
- Articles: authors, year, title, journal
- Statutes: jurisdiction, year, code_section
- Storing as key-value allows schema-less flexibility
- source/confidence tracking for quality assessment

**processing_steps table:**
- Audit trail of what happened
- Can resume failed batches
- Duration tracking for performance analysis
- config_snapshot enables reproducing results

**codes table:**
- Separate allocation from usage
- Can rollback codes if rename fails
- Status tracking prevents reuse

**code_sequence table:**
- Single-row table for atomic counter
- Base-25 index increments here

### Common Queries

```sql
-- Get document with all metadata
SELECT d.*,
       GROUP_CONCAT(m.key || '=' || m.value) as metadata
FROM documents d
LEFT JOIN metadata m ON d.id = m.document_id
WHERE d.file_path = ?
GROUP BY d.id;

-- Find all documents missing step 3 (convert)
SELECT d.*
FROM documents d
WHERE NOT EXISTS (
    SELECT 1 FROM processing_steps ps
    WHERE ps.document_id = d.id
    AND ps.step_name = 'convert'
    AND ps.status = 'success'
);

-- Get next available code
BEGIN TRANSACTION;
UPDATE code_sequence SET next_index = next_index + 1 WHERE id = 1;
SELECT next_index FROM code_sequence WHERE id = 1;
COMMIT;

-- Statistics by document type
SELECT
    document_type,
    COUNT(*) as total,
    SUM(CASE WHEN processing_status = 'complete' THEN 1 ELSE 0 END) as completed,
    SUM(CASE WHEN processing_status = 'failed' THEN 1 ELSE 0 END) as failed
FROM documents
GROUP BY document_type;
```

---

## Final Checklist for Starting Work

Before you begin coding:

- [ ] Read `llm.md` for quick rules
- [ ] Read this document for deep context
- [ ] Check `1-Context-Documentation/2-Task-Board.md` for current phase tasks
- [ ] Verify you understand services layer pattern
- [ ] Confirm you know what code to reuse vs. create
- [ ] Check `1-Context-Documentation/3-Architecture-Map.md` for module you're building

During work:

- [ ] Write pure functions in services/ (no state)
- [ ] Use existing extractors from step1/step2/step3a when possible
- [ ] Write unit tests with real sample files
- [ ] Update task board as you complete items

After work:

- [ ] Update `1-Context-Documentation/2-Task-Board.md` (check off tasks)
- [ ] Add entry to `1-Context-Documentation/4-Logbook.md` (if significant decisions made)
- [ ] Ensure tests pass
- [ ] Update `llm.md` if you discovered new patterns/constraints

---

**Welcome to the project! When in doubt, ask questions and document your decisions.**

**Last Updated:** 2025-11-28
**Document Version:** 1.0
