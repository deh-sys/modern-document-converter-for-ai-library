# Architecture Map

## Target Directory Structure

```
document-processor/
├── 1-Context-Documentation/          # Project documentation (this folder)
│   ├── 1-Master-Plan.md
│   ├── 2-Task-Board.md
│   ├── 3-Architecture-Map.md         # You are here
│   ├── 4-Logbook.md
│   └── README.md
│
├── src/
│   ├── core/                         # Core orchestration (workflow only)
│   │   ├── __init__.py
│   │   ├── orchestrator.py           # Pipeline manager - coordinates services
│   │   ├── factory.py                # Plugin loader (Phase 4)
│   │   └── models.py                 # Pydantic data models
│   │
│   ├── services/                     # ⭐ Business logic layer (pure, stateless)
│   │   ├── __init__.py
│   │   ├── text_extractor.py         # PDF/DOCX → text (pdfplumber + python-docx)
│   │   ├── registrar.py              # SQLite operations (CRUD, tracking)
│   │   ├── classifier.py             # Document type detection
│   │   └── code_generator.py         # Base-25 unique code generation
│   │
│   ├── plugins/                      # Document type handlers (Phase 4)
│   │   ├── __init__.py
│   │   ├── base.py                   # BasePlugin abstract interface
│   │   ├── caselaw.py                # Legal case documents
│   │   ├── statutes.py               # Legislation & regulations
│   │   ├── articles.py               # Academic journal articles
│   │   ├── briefs.py                 # Legal briefs & pleadings
│   │   └── books.py                  # Monographs & long-form works
│   │
│   ├── extractors/                   # Metadata extraction (reused from step1)
│   │   ├── __init__.py
│   │   ├── court_extractor.py        # From step1a (court identification)
│   │   ├── reporter_extractor.py     # From step1a (citation extraction)
│   │   ├── date_extractor.py         # From step1a/step1b (year extraction)
│   │   ├── case_name_formatter.py    # From step1a (case name parsing)
│   │   ├── author_extractor.py       # From step1b (author identification)
│   │   ├── title_extractor.py        # From step1b (article title extraction)
│   │   └── journal_extractor.py      # From step1b (journal metadata)
│   │
│   ├── steps/                        # Pipeline step implementations
│   │   ├── __init__.py
│   │   ├── base_step.py              # Abstract step interface
│   │   ├── rename_step.py            # Step 1: Filename normalization
│   │   ├── code_step.py              # Step 2: Unique code assignment
│   │   ├── convert_step.py           # Step 3: Format conversion to TXT
│   │   └── clean_step.py             # Step 4: Content cleaning & heading detection
│   │
│   ├── cleaners/                     # Text cleaning utilities
│   │   ├── __init__.py
│   │   ├── markdown_cleaner.py       # From step3a (RAG optimization)
│   │   └── ocr_cleaner.py            # From step3a/clean_txt.py
│   │
│   └── utils/                        # Shared utilities
│       ├── __init__.py
│       ├── file_utils.py             # Filename sanitization, validation
│       ├── logging_config.py         # Logging setup
│       └── validators.py             # Data validation helpers
│
├── config/                           # User-editable configurations
│   ├── pipeline.yaml                 # Pipeline settings & step enablement (Phase 3)
│   ├── settings.yaml                 # Global preferences (Phase 3)
│   └── document_types/               # ✅ Document classification patterns (IMPLEMENTED)
│       ├── caselaw.yaml              # ✅ Court patterns, reporter citations (122 lines)
│       ├── statutes.yaml             # ✅ Statute patterns with Trump Card weights (167 lines)
│       └── article.yaml              # Placeholder (disabled, Phase 4)
│
├── data/                             # Reference databases
│   ├── bluebook_courts_mapping.json  # From step1a (200+ courts)
│   └── reporters_database.json       # From step1a (100+ reporters)
│
├── registry/                         # Centralized tracking
│   └── master.db                     # SQLite registry (replaces all JSON registries)
│
├── tests/                            # Test suite
│   ├── test_services/
│   ├── test_extractors/
│   ├── test_steps/
│   └── fixtures/                     # Sample files for testing
│
├── logs/                             # Application logs
│   └── processor.log
│
├── main.py                           # CLI entry point
├── requirements.txt                  # Python dependencies
├── .gitignore
└── README.md                         # Quick start guide
```

---

## Module Responsibilities

### Core Layer (`src/core/`)

#### `orchestrator.py` - The Manager
**Role:** Coordinates the entire pipeline workflow (NO implementation details)

**Responsibilities:**
- Load configuration and determine which steps to run
- Call services in correct sequence: classify → extract → rename → code → convert → clean
- Handle dry-run mode (preview without executing)
- Manage rollback on errors
- Report progress and statistics

**Does NOT:**
- Extract text directly
- Write to database directly
- Implement extraction logic
- Parse documents

**Example Logic:**
```python
def process_batch(files):
    for file in files:
        # Use services for all actual work
        doc_type = classifier.classify(file)
        metadata = extract_metadata(file, doc_type)
        new_name = generate_filename(metadata, doc_type)
        registrar.add_document(file, metadata)
        ...
```

**Size Target:** ~200 lines

---

#### `models.py` - Data Structures
**Role:** Pydantic models for type safety and validation

**Models:**
- `DocumentMetadata` - Extracted fields (court, year, authors, etc.)
- `ProcessingStatus` - Step completion tracking
- `RenameResult` - Before/after filename with confidence
- `DocumentType` - Enum (CASELAW, STATUTE, ARTICLE, etc.)
- `PipelineConfig` - Configuration data structure

---

#### `factory.py` - Plugin Loader (Phase 4)
**Role:** Dynamic loading of document type plugins

**Responsibilities:**
- Load plugin classes from `src/plugins/`
- Register plugins with orchestrator
- Validate plugin interface compliance

---

### Services Layer (`src/services/`) ⭐

#### `text_extractor.py` - Document Text Extraction ✅ IMPLEMENTED
**Role:** Pure function: File path → Plain text string

**Status:** COMPLETE (335 lines)

**Responsibilities:**
- Detect file type (PDF, DOCX, DOC)
- Extract full text using pdfplumber (PDF) or python-docx (DOCX)
- Extract partial text (first N pages via max_pages parameter)
- Normalize text using clean-text library + custom legal hyphen fixing
- Handle corrupt/empty files gracefully (returns ExtractionResult with success=False)
- Return structured result with success/failure status

**Implementation Highlights:**
- **Strategy Pattern:** Internal `_extract_pdf()` and `_extract_docx()` handlers
- **pdfplumber Settings:** Uses `layout=True` to preserve spacing for better pattern matching
- **Text Normalization:** Optional normalization (default=True) using `cleaners/text_normalizer.py`
  - clean-text library for unicode, ASCII conversion, whitespace cleanup
  - Custom `fix_hyphens()` for legal documents ("defend-\nant" → "defendant")
- **Error Handling:** Returns `ExtractionResult(success=False, error_message="...")` instead of raising

**Interface:**
```python
def extract_text(file_path: Path, max_pages: Optional[int] = None,
                normalize: bool = True) -> ExtractionResult
    # Returns: ExtractionResult(text, success, page_count, error_message)

# Note: extract_multizone deferred to Phase 2
```

**Test Results:**
- Indian_Trail.pdf: 43,124 characters, 13 pages - SUCCESS
- OCGA statute: 126,148 characters, 35 pages - SUCCESS
- Clean extraction with hyphen fixing working correctly

**No State:** Stateless service - doesn't save files, doesn't track history, just extracts text

---

#### `registrar.py` - SQLite Registry Manager
**Role:** Single source of truth for all document tracking

**Responsibilities:**
- Manage SQLite database connection (WAL mode for safety)
- CRUD operations on documents
- Track processing status for each step
- Generate and allocate unique codes
- Export registry to JSON/CSV for analysis
- Atomic transactions for batch operations

**Schema:**
```sql
-- Documents table
CREATE TABLE documents (
    id INTEGER PRIMARY KEY,
    file_path TEXT UNIQUE NOT NULL,
    original_name TEXT NOT NULL,
    current_name TEXT NOT NULL,
    document_type TEXT,
    unique_code TEXT UNIQUE,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Metadata table (flexible key-value for extracted fields)
CREATE TABLE metadata (
    document_id INTEGER,
    key TEXT NOT NULL,
    value TEXT,
    source TEXT,  -- 'document' or 'filename' or 'fallback'
    confidence TEXT,  -- 'HIGH', 'MEDIUM', 'LOW'
    FOREIGN KEY (document_id) REFERENCES documents(id)
);

-- Processing history
CREATE TABLE processing_steps (
    id INTEGER PRIMARY KEY,
    document_id INTEGER,
    step_name TEXT,  -- 'rename', 'code', 'convert', 'clean'
    status TEXT,  -- 'pending', 'success', 'failed', 'skipped'
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    FOREIGN KEY (document_id) REFERENCES documents(id)
);

-- Unique codes tracking
CREATE TABLE codes (
    code TEXT PRIMARY KEY,
    document_id INTEGER,
    allocated_at TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(id)
);
```

**No Business Logic:** Doesn't decide what to extract or how to rename, just stores/retrieves data

---

#### `classifier.py` - Document Type Detection ✅ IMPLEMENTED
**Role:** Pure function: Text → DocumentType + confidence score

**Status:** COMPLETE (405 lines)

**Responsibilities:**
- Load YAML classification rules from `config/document_types/*.yaml` (cached at module level)
- Score text against all enabled document types using weighted pattern matching
- Return highest scoring type with confidence level and matched indicators
- Support positive and negative patterns for sophisticated classification

**YAML Pattern Structure:**
```yaml
document_type: caselaw
enabled: true
patterns:
  - pattern: '\b\w+\s+v\.\s+\w+'  # Regex
    description: "Case caption with 'v.'"
    weight: 40  # Positive or negative score
    case_sensitive: false
    notes: "Nearly universal in US case law"
confidence_thresholds:
  high: 60    # Score >= 60 → HIGH
  medium: 30  # Score >= 30 → MEDIUM
  low: 10     # Score >= 10 → LOW
```

**Implementation Highlights:**
- **Trump Card Philosophy:** Definitive indicators (e.g., "Official Code of" +100) overwhelm ambiguous signals
- **Negative Patterns:** Light penalties (-5) for hybrid documents like annotated statutes
- **Transparent Scoring:** Returns all matched pattern descriptions for debugging
- **Confidence Capping:** Scores normalized to 0.0-1.0 range (capped at 1.0)

**Interface:**
```python
def classify(text: str, min_confidence: Optional[ConfidenceLevel] = None) -> Classification:
    # Returns: Classification(document_type, confidence, indicators)

def get_all_scores(text: str) -> Dict[str, Tuple[float, List[str]]]:
    # Returns scores for all types (debugging)

def reload_rules():
    # Force reload YAML files (development)
```

**Test Results:**
- Caselaw: 140 points, HIGH confidence (Indian_Trail.pdf)
- Statute: 205 points, HIGH confidence (OCGA annotated code)
- Correctly handles annotated statutes (statute wins 205 vs caselaw 130)

---

#### `code_generator.py` - Unique Code Generation
**Role:** Generate and track 5-letter unique codes

**Responsibilities:**
- Base-25 encoding (A-Z except W)
- Allocate next available code
- Check if file already has code suffix
- Rollback code if rename fails
- Coordinate with registrar for persistence

**Interface:**
```python
def generate_next_code() -> str  # Returns "AAAAB", "AAAAC", etc.
def has_code_suffix(filename: str) -> bool  # Checks for "----CODE"
def rollback_code(code: str) -> None  # Returns code to pool
```

**Ported from:** `step2/filename_indexer.py`

---

### Plugins Layer (`src/plugins/`) - Phase 4

#### `base.py` - Abstract Interface
**Role:** Define contract all document type plugins must implement

**Required Methods:**
```python
class BasePlugin(ABC):
    @abstractmethod
    def extract_metadata(self, text: str, filename: str) -> DocumentMetadata:
        """Extract all relevant fields for this document type"""

    @abstractmethod
    def generate_filename(self, metadata: DocumentMetadata) -> str:
        """Build standardized filename from metadata"""

    @abstractmethod
    def identify_headings(self, text: str) -> List[Heading]:
        """Detect structural headings for this document type"""
```

---

#### `caselaw.py` - Legal Case Document Plugin
**Role:** Implement caselaw-specific extraction and formatting

**Metadata Fields:** court, year, case_name, reporter_citation
**Filename Template:** `c.{court}__{year}__{case_name}__{reporter}.{ext}`
**Heading Patterns:** Roman numerals, all-caps sections, numbered points

**Uses:**
- `extractors/court_extractor.py`
- `extractors/reporter_extractor.py`
- `extractors/case_name_formatter.py`
- `extractors/date_extractor.py`

---

### Steps Layer (`src/steps/`)

#### `base_step.py` - Abstract Step Interface
**Required Methods:**
```python
class BaseStep(ABC):
    @abstractmethod
    def execute(self, document: Document, dry_run: bool = False) -> StepResult:
        """Perform this step's processing"""

    @abstractmethod
    def rollback(self, document: Document) -> None:
        """Undo this step if possible"""
```

---

#### `rename_step.py` - Filename Normalization
**Responsibilities:**
1. Use classifier to detect document type
2. Delegate to appropriate plugin for metadata extraction
3. Generate new filename from metadata
4. Validate and sanitize filename (length, illegal chars)
5. Check for collisions, append -1, -2 if needed
6. Perform rename (if not dry-run)
7. Update registry with new name and metadata

---

#### `code_step.py` - Unique Code Assignment
**Responsibilities:**
1. Check if file already has code suffix (`----CODE`)
2. If not, generate new code via `code_generator`
3. Append code to filename: `original----ABCDE.ext`
4. Perform rename
5. Update registry with code assignment
6. Rollback code if rename fails

---

#### `convert_step.py` - Format Conversion
**Responsibilities:**
1. Use `text_extractor` to extract full text
2. Save as `.txt` file (same directory, same base name)
3. Preserve page markers if present (for PDFs)
4. Update registry with conversion status

---

#### `clean_step.py` - Content Cleaning
**Responsibilities:**
1. Load `.txt` file created by convert_step
2. Apply document-type-specific heading detection
3. Clean formatting (normalize whitespace, remove artifacts)
4. Apply markdown_cleaner for RAG optimization
5. Save cleaned version
6. Update registry

---

## Data Flow Diagrams

### Overall Pipeline Flow

```
┌─────────────┐
│ Input Files │
│ (PDF/DOCX)  │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│ ORCHESTRATOR                                                │
│ (Coordinates services, no implementation logic)             │
└─────────────────────────────────────────────────────────────┘
       │
       ├──────────────────────────────────────────────┐
       ▼                                              ▼
┌─────────────────┐                          ┌─────────────────┐
│ TEXT EXTRACTOR  │                          │   REGISTRAR     │
│   (Service)     │                          │   (Service)     │
│                 │                          │                 │
│ PDF→Text        │                          │ SQLite tracking │
│ DOCX→Text       │                          │ CRUD operations │
└────────┬────────┘                          └────────┬────────┘
         │                                            │
         │ Plain text                                 │ Status updates
         ▼                                            │
┌─────────────────┐                                   │
│  CLASSIFIER     │                                   │
│   (Service)     │                                   │
│                 │                                   │
│ Detect doc type │                                   │
└────────┬────────┘                                   │
         │                                            │
         │ DocumentType                               │
         ▼                                            │
┌─────────────────┐                                   │
│ PLUGIN FACTORY  │                                   │
│   (Core)        │                                   │
│                 │                                   │
│ Load caselaw.py │                                   │
└────────┬────────┘                                   │
         │                                            │
         │ Plugin instance                            │
         ▼                                            │
┌─────────────────┐                                   │
│ RENAME STEP     │                                   │
│   (Step)        │                                   │
│                 │                                   │
│ plugin.extract()├───────────────────────────────────┤
│ plugin.format() │        Update metadata            │
│ Sanitize        │                                   │
│ Rename file     │                                   │
└────────┬────────┘                                   │
         │                                            │
         ▼                                            │
┌─────────────────┐                                   │
│  CODE STEP      │                                   │
│   (Step)        │                                   │
│                 │                                   │
│ Generate code   ├───────────────────────────────────┤
│ Append suffix   │        Allocate code              │
│ Rename file     │                                   │
└────────┬────────┘                                   │
         │                                            │
         ▼                                            │
┌─────────────────┐                                   │
│ CONVERT STEP    │                                   │
│   (Step)        │                                   │
│                 │                                   │
│ Extract text    ├───────────────────────────────────┤
│ Save as .txt    │        Mark converted             │
└────────┬────────┘                                   │
         │                                            │
         ▼                                            │
┌─────────────────┐                                   │
│  CLEAN STEP     │                                   │
│   (Step)        │                                   │
│                 │                                   │
│ Detect headings ├───────────────────────────────────┤
│ Clean text      │        Mark complete              │
│ RAG optimize    │                                   │
└────────┬────────┘                                   │
         │                                            ▼
         ▼                                   ┌─────────────────┐
┌─────────────────┐                         │ master.db       │
│ Output Files    │                         │                 │
│ Clean TXT       │                         │ All metadata    │
│ + Registry      │                         │ All statuses    │
│ + Metadata      │                         │ All codes       │
└─────────────────┘                         └─────────────────┘
```

---

### Rename Step Detail Flow

```
Input: "Abbott Labs. v. Sandoz, Inc (ND Ill 2010).pdf"
  │
  ├─► text_extractor.extract_text()
  │   └─► "United States District Court... Abbott... v. Sandoz..."
  │
  ├─► classifier.classify(text)
  │   └─► DocumentType.CASELAW (confidence: 0.85)
  │
  ├─► factory.get_plugin("caselaw")
  │   └─► CaselawPlugin instance
  │
  ├─► plugin.extract_metadata(text, filename)
  │   ├─► court_extractor.extract() → "ILL_ND"
  │   ├─► date_extractor.extract() → "2010"
  │   ├─► case_name_formatter.extract() → "Abbott-v-Sandoz"
  │   └─► reporter_extractor.extract() → "743_FSupp2d_762"
  │
  ├─► plugin.generate_filename(metadata)
  │   └─► "c.ILL_ND__2010__Abbott-v-Sandoz__743_FSupp2d_762.pdf"
  │
  ├─► sanitize_filename() - validate length, illegal chars
  │   └─► (unchanged, valid)
  │
  ├─► check_collision() - does new filename already exist?
  │   └─► No collision
  │
  ├─► os.rename(old, new) [if not dry_run]
  │   └─► Success
  │
  └─► registrar.update_document(metadata, status='renamed')
      └─► SQLite updated

Output: "c.ILL_ND__2010__Abbott-v-Sandoz__743_FSupp2d_762.pdf"
```

---

## Current Codebase Analysis Summary

### Existing Code to Migrate

**From step1a (Caselaw):**
- ✅ Reuse: `court_extractor.py`, `reporter_extractor.py`, `date_extractor.py`, `case_name_formatter.py`
- ✅ Reuse: `bluebook_courts_mapping.json`, `reporters_database.json`
- 🔄 Refactor: `pdf_extractor.py` → `services/text_extractor.py` (use pdfplumber)
- 🔄 Refactor: `renamer.py` → `steps/rename_step.py` + `plugins/caselaw.py`
- 🔄 Refactor: `registry_manager.py` → `services/registrar.py` (SQLite)

**From step1b (Articles):**
- ✅ Reuse: `author_extractor.py`, `title_extractor.py`, `journal_extractor.py`
- 🔄 Refactor: `filename_evaluator.py` → plugin-specific logic in Phase 4
- 🔄 Refactor: `renamer.py` → `plugins/articles.py`

**From step2 (Codes):**
- ✅ Reuse: Base-25 encoding logic → `services/code_generator.py`
- 🔄 Refactor: Registry JSON → SQLite in `services/registrar.py`

**From step3a (Conversion):**
- ✅ Reuse: `markdown_cleaner.py` → `cleaners/markdown_cleaner.py`
- ✅ Reuse: `clean_txt.py` → `cleaners/ocr_cleaner.py`
- 🔄 Refactor: `tracking.py` → merged into `services/registrar.py`

### Code Duplication to Eliminate

**Identical across step1a and step1b:**
- `pdf_extractor.py` - consolidate to `services/text_extractor.py`
- `docx_extractor.py` - consolidate to `services/text_extractor.py`
- `date_extractor.py` - move to shared `extractors/`
- `config_manager.py` - replace with YAML-based config system

**Similar patterns to unify:**
- Filename sanitization (appears in both step1a and step1b)
- Confidence scoring (appears in both step1a and step1b)
- Registry management (JSON in step1/step2, SQLite in step3a)

---

## Dependency Graph

```
orchestrator.py
    ├── services/text_extractor.py
    ├── services/classifier.py
    │       └── (regex patterns)
    ├── services/registrar.py
    │       └── sqlite3
    ├── services/code_generator.py
    │       └── services/registrar.py
    ├── core/factory.py
    │       └── plugins/*.py
    │               ├── extractors/*.py
    │               │       └── data/*.json
    │               └── core/models.py
    └── steps/*.py
            ├── services/*
            ├── plugins/*
            └── cleaners/*
```

---

## Technology Dependencies

### Required Python Packages
```txt
# Text extraction
pdfplumber>=0.10.0        # PDF text extraction
python-docx>=1.0.0         # Word document parsing

# CLI & UI
click>=8.1.0               # CLI framework
rich>=13.0.0               # Terminal formatting & progress bars

# Data validation
pydantic>=2.0.0            # Data models with validation

# Configuration
pyyaml>=6.0                # YAML config parsing

# Database
# sqlite3 (built-in)       # No additional package needed

# Development
pytest>=7.0.0              # Testing framework
black>=23.0.0              # Code formatting
ruff>=0.1.0                # Linting
```

### External Tools (Optional)
- LibreOffice (for legacy .doc conversion)
- Pandoc (if we add markdown output in future)

---

## Design Patterns Used

1. **Services Pattern** - Business logic separated from orchestration
2. **Strategy Pattern** - Different plugins for different document types
3. **Factory Pattern** - Dynamic plugin loading
4. **Template Method** - BaseStep defines workflow, subclasses implement details
5. **Repository Pattern** - Registrar abstracts data persistence

---

## Implemented YAML Configuration Files

### `config/document_types/caselaw.yaml` (122 lines) ✅
**Purpose:** Classify legal case documents (judicial opinions, court decisions)

**Pattern Categories:**
- **Strong Indicators (75 points):**
  - Case caption with "v." or "versus": +40
  - Reporter citation format (e.g., "328 Ga. App. 524"): +35
- **Medium Indicators (55 points):**
  - Court name (Supreme Court, etc.): +20
  - Legal database citation (LEXIS, Westlaw): +15
  - Party designation (Plaintiff, Defendant): +10
  - Decision date notation: +10
- **Weak Indicators (3-5 points each):**
  - Legal procedural terms, judicial verbs, case numbers, judge attribution
- **Negative Indicators:**
  - Statutory citation (§, U.S.C.): -10 (suggests statute, not case)

**Thresholds:** HIGH ≥60, MEDIUM ≥30, LOW ≥10

**Test Performance:** 140 points on Indian_Trail.pdf (HIGH confidence)

---

### `config/document_types/statutes.yaml` (167 lines) ✅
**Purpose:** Classify statutory documents (legislation, codes) including annotated codes

**Pattern Categories:**
- **Trump Card Indicators (definitive markers):**
  - "Official Code of": +100 (DEFINITIVE - if present, document IS a statute)
  - "TITLE \d+": +50 (DEFINITIVE - strong structural indicator)
- **High Weight Indicators (30-35 points):**
  - § symbol: +35
  - Spaced acronyms (O.C.G.A., U.S.C., C.F.R.): +30 each
- **Medium Indicators (10-15 points):**
  - Chapter number, Code reference, Section notation
- **Weak Indicators (5 points):**
  - Legislative verbs (enacted, codified), Public Law citations
- **Light Negative Patterns (for annotated codes):**
  - Case caption "v.": -5 (was -30, reduced for Trump Card)
  - Court names: -5 (was -20)
  - Party designations: -5 (was -15)
  - Decision dates: -5 (was -10)
  - Judicial language: -5 (was -10)

**Rationale for Light Negatives:**
> "Annotated codes naturally contain case references in their annotations. Light penalties (-5) acknowledge the presence of case content without overwhelming the definitive statute markers."

**Thresholds:** HIGH ≥60, MEDIUM ≥30, LOW ≥10

**Test Performance:** 205 points on OCGA annotated statute (HIGH confidence)
- Correctly wins over caselaw (205 vs 130) despite extensive case annotations
- Trump Card philosophy successfully handles hybrid documents

---

### `config/document_types/article.yaml` (62 lines) - PLACEHOLDER
**Purpose:** Classify academic journal articles (Phase 4)

**Status:** Disabled (enabled: false)

**Placeholder Patterns (not yet tuned):**
- Abstract section, author credentials, journal volume numbers
- Article structure markers (Introduction, Conclusion, References)
- Negative patterns for case indicators

**Note:** Patterns need tuning based on real journal article corpus. Will be activated in Phase 4.

---

**Document Version:** 1.1
**Last Updated:** 2025-11-28
**Status:** Phase 1 In Progress - Services Layer Implementation Complete
