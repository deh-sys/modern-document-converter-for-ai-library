# Task Board

## Current Phase: Phase 1 - Core Services Foundation

**Target:** Build shared infrastructure for all document types
**Timeline:** Week 1

---

## Phase 1 Tasks

### Setup & Infrastructure
- [x] Create project directory structure
  - [x] `src/core/`
  - [x] `src/services/`
  - [x] `src/extractors/`
  - [x] `src/steps/`
  - [x] `src/plugins/`
  - [x] `config/`
  - [x] `data/`
  - [x] `registry/`
- [x] Create `requirements.txt` with dependencies
- [ ] Initialize git repository (if not already done)
- [ ] Set up basic logging configuration

### Service Layer Development

#### Text Extractor Service ✅ COMPLETED
- [x] Create `services/text_extractor.py`
- [x] Implement PDF extraction using pdfplumber
  - [x] Extract full document text
  - [x] Extract first N pages (configurable via max_pages)
  - [ ] Extract multi-zone (first + last pages) - DEFERRED
  - [x] Handle extraction errors gracefully (returns ExtractionResult with success=False)
- [x] Implement DOCX extraction using python-docx
  - [x] Extract full document text
  - [x] Preserve paragraph structure
  - [x] Handle extraction errors gracefully
- [x] Add file type detection (PDF vs DOCX vs legacy .doc)
- [x] Create text normalizer with clean-text library
  - [x] Custom hyphen fixing for legal documents
  - [x] Unicode normalization
  - [x] Whitespace cleanup
- [x] Write smoke test for text extraction
  - [x] Test with sample PDF (Indian_Trail.pdf - 43K chars, 13 pages)
  - [x] CLI tool: `smoke_test_extractor.py`
  - [x] Rich output formatting
- [ ] Write unit tests for text extraction (DEFERRED to Phase 2)

#### Registrar Service
- [ ] Create `services/registrar.py`
- [ ] Design SQLite schema
  - [ ] Documents table (file paths, types, metadata)
  - [ ] Processing history table (step completion status)
  - [ ] Codes table (unique 5-letter codes)
  - [ ] Metadata table (extracted fields)
- [ ] Implement CRUD operations
  - [ ] Add new document
  - [ ] Update document status
  - [ ] Get document by path/code
  - [ ] List documents by status/type
- [ ] Add atomic operations (WAL mode)
- [ ] Add export functionality (JSON, CSV)
- [ ] Write unit tests for registry operations

#### Classifier Service ✅ COMPLETED
- [x] Create `services/classifier.py`
- [x] Implement YAML-driven pattern matching system
  - [x] Load classification rules from `config/document_types/*.yaml`
  - [x] Score documents against all enabled types
  - [x] Return highest scoring type with confidence level
  - [x] Pattern-based scoring with positive and negative weights
- [x] Create `config/document_types/caselaw.yaml`
  - [x] Court name patterns (Supreme Court, Court of Appeals, etc.)
  - [x] Reporter citations (regex for F.2d, F.3d, etc.)
  - [x] Case caption format (v., versus)
  - [x] Party designations (Plaintiff, Defendant, etc.)
  - [x] Negative patterns (statutory citations reduce score)
  - [x] Confidence thresholds (HIGH ≥60, MEDIUM ≥30, LOW ≥10)
- [x] Create `config/document_types/statutes.yaml`
  - [x] Trump Card indicators: "Official Code of" (+100), "TITLE \d+" (+50)
  - [x] Section symbols (§) and code citations
  - [x] Spaced acronyms (O.C.G.A., U.S.C., C.F.R.)
  - [x] Light negative patterns for annotated codes (-5 each)
  - [x] Successfully handles annotated statutes (statute wins 205 vs caselaw 130)
- [x] Create placeholder `config/document_types/article.yaml` (disabled, Phase 4)
- [x] Return confidence scores (0.0-1.0, capped at 1.0)
- [x] Write smoke test with known samples
  - [x] CLI tool: `smoke_test_classifier.py`
  - [x] Options: --show-scores, --json-output, --max-pages
  - [x] Tested on caselaw (140 points, HIGH confidence)
  - [x] Tested on statutes (205 points, HIGH confidence)

#### Code Generator Service
- [ ] Create `services/code_generator.py`
- [ ] Port base-25 encoding logic from step2/filename_indexer.py
  - [ ] `index_to_code()` function
  - [ ] `code_to_index()` function (for verification)
- [ ] Implement code allocation
  - [ ] Get next available code
  - [ ] Mark code as used
  - [ ] Rollback code on failure
- [ ] Add suffix detection (`has_registry_suffix()`)
- [ ] Write unit tests for code generation
  - [ ] Test base-25 encoding/decoding
  - [ ] Test collision detection
  - [ ] Test rollback logic

---

## Phase 2 Tasks (Pending Phase 1 Completion)

### Extractor Porting
- [ ] Port `step1a/extractors/court_extractor.py`
- [ ] Port `step1a/extractors/reporter_extractor.py`
- [ ] Port `step1a/extractors/date_extractor.py`
- [ ] Port `step1a/formatters/case_name_formatter.py`
- [ ] Copy `data/bluebook_courts_mapping.json`
- [ ] Copy `data/reporters_database.json`

### Pipeline Steps
- [ ] Create `steps/base_step.py` (abstract interface)
- [ ] Create `steps/rename_step.py`
- [ ] Create `steps/code_step.py`
- [ ] Create `steps/convert_step.py`
- [ ] Create `steps/clean_step.py`

### Orchestration
- [ ] Create `core/orchestrator.py`
- [ ] Implement sequential pipeline execution
- [ ] Add dry-run mode
- [ ] Add rollback capability
- [ ] Add progress tracking/reporting

### CLI
- [ ] Create `cli.py` using Click framework
- [ ] Add `process` command
- [ ] Add `--type` flag (caselaw, articles, etc.)
- [ ] Add `--dry-run` flag
- [ ] Add `--verbose` flag
- [ ] Add status/reporting commands

### Testing
- [ ] End-to-end test with step1a sample files
- [ ] Verify filename accuracy
- [ ] Verify registry tracking
- [ ] Verify code assignment

---

## Phase 3 Tasks (Deferred)

### Configuration System
- [ ] Create YAML schema for patterns
- [ ] Port caselaw patterns to `config/caselaw_patterns.yaml`
- [ ] Port caselaw template to `config/caselaw_template.yaml`
- [ ] Add config validation
- [ ] Update extractors to load from YAML
- [ ] Add helpful error messages for invalid configs

---

## Phase 4 Tasks (Deferred)

### Plugin System
- [ ] Design `plugins/base.py` interface
- [ ] Refactor caselaw → `plugins/caselaw.py`
- [ ] Implement articles plugin
- [ ] Implement statutes plugin
- [ ] Implement briefs plugin
- [ ] Implement books plugin
- [ ] Update classifier for multi-type detection

---

## Deferred Features

### Interactive Experience
- [ ] Interactive CLI wizard
- [ ] Drag-drop macOS .command script
- [ ] Windows batch file wrapper
- [ ] Progress bars with `rich` library

### Advanced Features
- [ ] Parallel processing for large batches
- [ ] Resume interrupted batches
- [ ] Batch rollback
- [ ] Metadata export formats (BibTeX, Zotero)
- [ ] Web interface (optional, far future)

### Quality Enhancements
- [ ] Filename quality evaluation (from step1b)
- [ ] OCR text cleaning integration
- [ ] Image extraction from PDFs
- [ ] Table extraction and formatting

---

## Current Sprint - Phase 1 Foundation (Nov 28, 2025)

**Sprint Goal:** Build core services foundation for text extraction and document classification

**Active Tasks:**
- [ ] Registrar Service (SQLite operations) - NEXT UP
- [ ] Code Generator Service (base-25 encoding) - PENDING

**Blocked:**
- None

**Completed This Sprint:**
- [x] Project structure created (`src/`, `config/`, `data/`, `registry/`)
- [x] Core models implemented (`src/core/models.py` - 454 lines)
  - DocumentType enum, ExtractionResult, Classification, MetadataField
  - Pydantic validation with provenance tracking
- [x] Text normalizer service (`src/cleaners/text_normalizer.py` - 310 lines)
  - clean-text library integration
  - Custom hyphen fixing for legal documents
  - Unicode and whitespace normalization
- [x] Text extractor service (`src/services/text_extractor.py` - 335 lines)
  - pdfplumber PDF extraction with layout preservation
  - python-docx DOCX extraction
  - Strategy pattern for internal implementations
  - Error handling with ExtractionResult model
- [x] Classifier service (`src/services/classifier.py` - 405 lines)
  - YAML-driven pattern matching (no hardcoded keywords)
  - Weighted scoring system with positive and negative patterns
  - Confidence thresholds (HIGH/MEDIUM/LOW)
  - Module-level caching for performance
- [x] YAML classification rules
  - `config/document_types/caselaw.yaml` - 122 lines
  - `config/document_types/statutes.yaml` - 167 lines (with Trump Card weights)
  - `config/document_types/article.yaml` - 62 lines (placeholder, disabled)
- [x] Smoke test tools
  - `smoke_test_extractor.py` - 224 lines (CLI for testing extraction)
  - `smoke_test_classifier.py` - 224 lines (CLI for testing classification)
  - Rich formatted output with tables and panels
- [x] Requirements file (`requirements.txt`)
  - Added unidecode>=1.3.0 to fix unicode warnings
- [x] Critical bug fixes
  - Fixed confidence validation error (capped at 1.0)
  - Fixed smoke test display bug (variable collision)
  - Implemented Trump Card philosophy for annotated statutes

---

## Notes & Decisions

### Decisions Made
- Using pdfplumber instead of pdftotext for better Python integration
- SQLite instead of multiple JSON files for centralized tracking
- Hardcode first implementation before building plugin abstraction
- YAML configs for patterns only, not for dynamic class loading
- **Trump Card Philosophy (Nov 28, 2025):** Definitive indicators get massive weights to override ambiguous signals
  - Example: "Official Code of" (+100 points) definitively marks statutes, even if annotated with many case citations
  - Negative patterns use light penalties (-5) for annotated documents that naturally contain both statute and case text
  - Result: Annotated statutes correctly classified (STATUTE: 205 vs CASELAW: 130)

### Open Questions
- [ ] Should we preserve original files or rename in place?
- [ ] How to handle duplicate filenames across different document types?
- [ ] Should registry track file moves/renames outside the app?

---

**Last Updated:** 2025-11-28
**Current Phase:** Phase 1 - Core Services Foundation (In Progress)
**Progress:** Text Extractor ✅ | Classifier ✅ | Registrar (Next) | Code Generator (Pending)
