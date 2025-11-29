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

#### Registrar Service ✅ COMPLETED
- [x] Create `services/registrar.py`
- [x] Design SQLite schema (5 tables)
  - [x] Documents table (file paths, names, types, unique codes)
  - [x] Processing_steps table (step execution history with timestamps)
  - [x] Codes table (code allocation tracking with status)
  - [x] Metadata table (flexible key-value with provenance)
  - [x] Registry_state table (system state: next_code_index)
- [x] Implement CRUD operations
  - [x] `register_document()` - Add new document with optional code
  - [x] `update_document_name()` / `update_document_type()` - Modify documents
  - [x] `get_document_by_path()` / `get_document_by_code()` / `get_document_by_id()` - Queries
  - [x] `list_documents()` - List with optional filtering and limit
- [x] Implement code management
  - [x] `get_next_code_index()` - Query current index
  - [x] `increment_code_index()` - Atomic increment and return
  - [x] `allocate_code()` - Reserve code in codes table
  - [x] `commit_code_to_document()` - Link code to document, mark in_use
  - [x] `rollback_code()` - Delete uncommitted allocations
  - [x] `code_exists()` - Check if code already allocated
- [x] Add metadata tracking
  - [x] `add_metadata()` - Store extracted fields with provenance
  - [x] `get_metadata()` - Retrieve all metadata for document
- [x] Add processing step tracking
  - [x] `record_processing_step()` - Log step execution with timestamps
  - [x] `get_processing_steps()` - Retrieve step history
- [x] Add atomic operations (WAL mode + transactions)
  - [x] Enable WAL mode for concurrent access
  - [x] Transaction context manager for batch operations
  - [x] Foreign keys enabled for referential integrity
- [x] Add export functionality
  - [x] `get_statistics()` - Registry stats (counts, next_index)
  - [x] `export_to_json()` - Export documents and stats to JSON
- [x] Write smoke tests for registry operations
  - [x] Test document registration
  - [x] Test code allocation and linking
  - [x] Test rollback functionality
  - [x] Test database persistence and queries

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

#### Code Generator Service ✅ COMPLETED
- [x] Create `services/code_generator.py`
- [x] Port base-25 encoding logic from step2/filename_indexer.py
  - [x] `index_to_code()` function (exact port from legacy)
  - [x] `code_to_index()` function (reverse conversion for validation)
- [x] Implement code allocation with discovery logic
  - [x] Get next available code from registrar
  - [x] Extract existing codes from filenames (regex pattern)
  - [x] Preserve legacy codes (Scenario A)
  - [x] Generate new codes for files without valid codes (Scenario B)
  - [x] Rollback code on failure (atomic operations)
- [x] Add filename utilities
  - [x] `has_code_suffix()` - Check for existing code
  - [x] `extract_code_from_filename()` - Regex extraction with validation
  - [x] `append_code_to_filename()` - Add ----CODE separator
  - [x] `is_valid_code()` - Validate format (5 chars, uppercase, no W)
- [x] Write smoke tests for code generation
  - [x] Test base-25 encoding/decoding (index 0→AAAAA, 1→AAAAB, etc.)
  - [x] Test legacy code preservation (old_statute----ABXCD.pdf keeps ABXCD)
  - [x] Test invalid code replacement (bad_file----WWWWW.pdf gets new code)
  - [x] Test rollback logic (allocate, rollback, verify)
  - [x] Test utility functions (extract, append, validate)

---

## Phase 2 Tasks (In Progress)

### Caselaw Metadata Extraction ✅ COMPLETED
- [x] Create `config/document_types/caselaw.yaml` with extraction_rules
  - [x] Case name patterns (v. pattern with cleanup)
  - [x] Date patterns (Decided, Filed, Argued, fallback)
  - [x] Court patterns (state, federal district, circuit)
  - [x] Citation patterns (Ga., S.E.2d, F.2d, F.3d, F.Supp, U.S.)
- [x] Create `src/plugins/caselaw.py` (510 lines)
  - [x] CaselawProcessor class with YAML-driven extraction
  - [x] Priority-based pattern matching
  - [x] Reference database integration
  - [x] Graceful fallback handling
- [x] Copy `data/bluebook_courts_mapping.json` from legacy
- [x] Copy `data/reporters_database.json` from legacy
- [x] Create `smoke_test_caselaw.py` (259 lines)
  - [x] Validation: case name, year, court, citation
  - [x] 4/4 tests passing on Indian_Trail.pdf

### Rename Workflow ✅ COMPLETED
- [x] Create `config/filename_templates/caselaw.yaml` (122 lines)
  - [x] Legacy format template: c.{COURT}__{YEAR}__{CASE_NAME}__{CITATION}----{CODE}
  - [x] Field formatting rules (hyphens, underscores, sanitization)
  - [x] Length limits and fallback handling
- [x] Create `src/formatters/filename_formatter.py` (402 lines)
  - [x] format_court() - spaces→underscores, remove periods
  - [x] format_year() - as-is validation
  - [x] format_case_name() - spaces→hyphens, &→and, cleanup
  - [x] format_citation() - spaces→underscores, remove periods
  - [x] sanitize_filename() - remove OS-illegal characters only
  - [x] truncate_if_needed() - enforce 255 char limit
- [x] Create `src/steps/rename_step.py` (369 lines)
  - [x] Atomic workflow: extract → classify → metadata → code → format → rename
  - [x] RenameStep class with dry-run mode
  - [x] Registry integration (register before rename)
  - [x] Code allocation BEFORE filename generation (prevents collisions)
  - [x] Error handling with rollback support
- [x] Create `smoke_test_rename.py` (270 lines)
  - [x] End-to-end validation
  - [x] 4/4 tests passing on Indian_Trail.pdf
  - [x] Expected output: c.Ga_Ct_App__2014__Indian-Trail-LLC-v-State-Bank-and-Trust-Co__328_Ga_App_524----AAAAA.pdf

### Pipeline Steps (Remaining)
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

## Current Sprint - Phase 1 Foundation (Nov 28, 2025) ✅ COMPLETED

**Sprint Goal:** Build core services foundation for text extraction and document classification

**Status:** ✅ ALL PHASE 1 SERVICES COMPLETE (4/4)

**Completed Services:**
- [x] Text Extractor Service (335 lines) - PDF/DOCX extraction with normalization
- [x] Classifier Service (405 lines) - YAML-driven pattern matching
- [x] Code Generator Service (546 lines) - Base-25 encoding with legacy compatibility
- [x] Registrar Service (653 lines) - SQLite persistence with WAL mode

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
- [x] Code generator service (`src/services/code_generator.py` - 546 lines)
  - Base-25 encoding algorithm (A-Z excluding W)
  - Discovery logic: preserves legacy codes, generates new for files without codes
  - Validation: `is_valid_code()` ensures 5 chars, uppercase, no W
  - Filename utilities: extract, append, validate codes
  - Tested with 249,025 code compatibility
- [x] Registrar service (`src/services/registrar.py` - 653 lines)
  - SQLite database: registry/master.db with 5 tables
  - Code management: allocate, commit, rollback (atomic operations)
  - Document tracking: register, query, update (by path/code/id)
  - Metadata storage: flexible key-value with provenance
  - Processing steps: pipeline execution history
  - WAL mode for concurrent access, transaction support
- [x] Smoke test tools
  - `smoke_test_extractor.py` - 224 lines (CLI for testing extraction)
  - `smoke_test_classifier.py` - 224 lines (CLI for testing classification)
  - `smoke_test_registry.py` - 489 lines (CLI for testing registry & codes)
  - Rich formatted output with tables and panels
  - All tests passing (6/6 registry tests, 100% success rate)
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
**Current Phase:** Phase 1 - Core Services Foundation ✅ COMPLETE
**Progress:** Text Extractor ✅ | Classifier ✅ | Registrar ✅ | Code Generator ✅
**Next Phase:** Phase 2 - Caselaw End-to-End Pipeline
