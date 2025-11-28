# Master Plan: Unified Document Processing System

## Project Overview

**Goal:** Build a single, modular application that processes legal and academic documents through a sequential pipeline:
1. **Rename** - Normalize filenames with metadata extraction
2. **Code** - Add unique 5-letter identifiers
3. **Convert** - Transform to plain text format
4. **Clean** - Optimize for AI/RAG consumption with structured headings

**Current State:** Four separate applications (step1a-caselaw, step1b-articles, step2-codes, step3a-convert) that work independently.

**Target State:** One unified application with document-type plugins, editable configurations, and centralized tracking.

---

## Design Principles

### 1. Services Layer Architecture ⭐
**Rationale:** Keep orchestrator clean by separating workflow logic from implementation details.

```
orchestrator.py  → "First classify, then extract, then rename" (workflow)
classifier.py    → "Look for court patterns vs. author patterns" (logic)
registrar.py     → "Save this to SQLite with atomic transactions" (implementation)
```

**Benefits:**
- Easy to test in isolation
- Easy to swap implementations (e.g., PostgreSQL instead of SQLite)
- Orchestrator stays ~200 lines of pure coordination

### 2. Caselaw-First Development
**Rationale:** Get one document type fully working end-to-end before abstracting.

**Avoid:** Building a perfect plugin system before understanding the patterns.

**Approach:**
- Phase 1-2: Hardcode caselaw processing
- Phase 3: Extract common patterns
- Phase 4: Abstract to plugin system after seeing what's truly shared

### 3. Configuration-Driven (Patterns Only)
**Editable in YAML:**
- Regex patterns for extraction
- Filename templates
- Court mappings and abbreviations

**Hardcoded in Python:**
- Class structures
- Plugin loading logic
- Core orchestration

**Avoid:** Dynamic string-to-class loading (`importlib.import_module("extractors.court_extractor.CourtExtractor")`) - it's hard to debug and adds unnecessary complexity early on.

### 4. Sequential Pipeline with Optional Steps
**Pipeline:** Rename → Code → Convert → Clean

Each step:
- Can be optionally skipped
- Has rollback support
- Tracks status in central registry
- Operates in dry-run mode for safety

---

## Technology Stack

### Text Extraction
- **PDFs:** `pdfplumber` (Python-native, better table/layout handling than pdftotext)
- **Word Docs:** `python-docx` (already in use)
- **Legacy .doc:** LibreOffice headless conversion (keep existing approach)

### Format Conversion
- **PDF → TXT:** pdfplumber (replaces marker-pdf for simplicity in Phase 1)
- **DOCX → TXT:** python-docx direct text extraction
- **Markdown cleaning:** Existing markdown_cleaner.py logic (RAG-optimized)

### Storage & Tracking
- **Registry:** SQLite database (replaces multiple JSON files)
- **Schema:** Extends doc_to_markdown_history.db from step3a
- **Atomic operations:** Temp file writes + renames for safety

### CLI
- **Framework:** `click` (already used in step3a)
- **Features:** Dry-run mode, verbose logging, status reporting
- **Future:** Interactive wizard and drag-drop wrapper (deferred to later phase)

---

## Phased Implementation Strategy

### Phase 1: Core Services Foundation (Week 1) - IN PROGRESS ⚙️
**Goal:** Build the shared infrastructure that all document types will use.

**Deliverables:**
1. ✅ `services/text_extractor.py` - PDF/DOCX → plain text using pdfplumber/python-docx
   - COMPLETE: Strategy pattern with pdfplumber (layout=True) and python-docx
   - COMPLETE: Text normalizer with clean-text + custom hyphen fixing for legal docs
   - COMPLETE: ExtractionResult model for type-safe error handling
   - COMPLETE: Smoke test tool (`smoke_test_extractor.py`)

2. ⏳ `services/registrar.py` - SQLite operations (schema design, CRUD operations)
   - PENDING: Next task to implement

3. ✅ `services/classifier.py` - Document type detection (YAML-driven pattern matching)
   - COMPLETE: YAML-driven classification system (no hardcoded keywords)
   - COMPLETE: Weighted scoring with positive and negative patterns
   - COMPLETE: Confidence levels (HIGH/MEDIUM/LOW) with configurable thresholds
   - COMPLETE: Module-level caching for performance
   - COMPLETE: Caselaw detection (140 points, HIGH confidence)
   - COMPLETE: Statute detection with Trump Card philosophy (205 points, handles annotated codes)
   - COMPLETE: Smoke test tool with `--show-scores` flag (`smoke_test_classifier.py`)

4. ⏳ `services/code_generator.py` - Base-25 unique code logic (port from step2)
   - PENDING: After registrar service

**Success Criteria:**
- ✅ Can extract text from any PDF/DOCX file (tested with 43K char, 13 page PDF)
- ✅ Can classify document type with confidence scores (caselaw and statutes working)
- ⏳ Can save metadata to SQLite registry (pending)
- ⏳ Can generate and track unique codes (pending)

**Status:** 2 of 4 services complete (50%)

### Phase 2: Caselaw End-to-End (Week 2)
**Goal:** Complete working pipeline for one document type (caselaw).

**Deliverables:**
1. Port existing extractors from step1a:
   - `extractors/court_extractor.py` (use bluebook_courts.json)
   - `extractors/reporter_extractor.py` (use reporters.json)
   - `extractors/date_extractor.py`
   - `extractors/case_name_formatter.py`
2. Build `orchestrator.py` - coordinates all steps
3. Build `steps/rename_step.py` - filename normalization
4. Build `steps/code_step.py` - unique code assignment
5. Build `steps/convert_step.py` - PDF/DOCX to TXT
6. Build `steps/clean_step.py` - heading detection for caselaw
7. Build `cli.py` - basic command: `process /path/to/files --type caselaw`

**Success Criteria:**
- Input: `Abbott Labs. v. Sandoz, Inc (ND Ill 2010).pdf`
- Output: `c.ILL_ND__2010__Abbott-v-Sandoz__743_FSupp2d_762----ABCDE.txt`
- Registry: Tracks processing status, metadata, unique code
- Can run in dry-run mode to preview changes

### Phase 3: Extract to YAML Configs (Week 3)
**Goal:** Make regex patterns and templates user-editable.

**Deliverables:**
1. `config/caselaw_patterns.yaml` - court patterns, reporter patterns, date formats
2. `config/caselaw_template.yaml` - filename template, heading patterns
3. Update extractors to load patterns from YAML
4. Add config validation (invalid regex detection)

**Success Criteria:**
- User can add new court patterns without touching Python code
- User can customize filename template
- Invalid configs show helpful error messages

### Phase 4: Add More Document Types (Week 4+)
**Goal:** Extend to statutes, articles, briefs, books.

**Approach:**
1. Build second document type (statutes or articles)
2. Identify truly common patterns between caselaw + new type
3. Create `plugins/base.py` interface based on observed commonalities
4. Refactor caselaw → `plugins/caselaw.py` implementing BasePlugin
5. Implement new type as plugin
6. Repeat for remaining document types

**Success Criteria:**
- Can process multiple document types in single batch
- Classifier automatically detects document type
- Each type has its own config YAML
- Shared code is in services/, type-specific code in plugins/

---

## Migration Strategy from Existing Code

### What to Reuse As-Is
1. **Extraction Logic:**
   - step1a: court_extractor, reporter_extractor, case_name_formatter
   - step1b: author_extractor, title_extractor, journal_extractor
   - Both: date_extractor (identical code)

2. **Reference Data:**
   - bluebook_courts_mapping.json (200+ courts)
   - reporters_database.json (100+ reporters)

3. **Conversion Logic:**
   - step3a: markdown_cleaner.py (RAG optimization)
   - clean_txt.py: OCR cleaning patterns

### What to Refactor
1. **Consolidate Text Extraction:**
   - step1a/pdf_extractor.py + step1b/pdf_extractor.py → services/text_extractor.py
   - Use pdfplumber instead of subprocess pdftotext calls

2. **Unify Registry Management:**
   - step1a/registry_manager.py + step2/registry JSON + step3a/tracking.py → services/registrar.py
   - Single SQLite database instead of multiple JSON files

3. **Merge Renaming Logic:**
   - step1a/renamer.py + step1b/renamer.py → steps/rename_step.py
   - Generic interface with document-type-specific implementations

### What to Defer
1. **Modern Pipeline Architecture:** step1a/file_renamer/ (pipeline.py, models.py)
   - Good ideas but adds complexity
   - Revisit in Phase 4 when patterns are clear

2. **Filename Quality Evaluation:** step1b/filename_evaluator.py
   - Useful for articles, maybe not for other types
   - Add as article-specific plugin logic

3. **Interactive Wizard:** Build basic CLI first
4. **Drag-Drop Interface:** macOS .command script for later

---

## Success Metrics

### Phase 1 Success
- [x] Can extract text from sample PDFs without errors (tested: Indian_Trail.pdf, OCGA statute)
- [x] Document classification works for caselaw and statutes with HIGH confidence
- [x] YAML-driven patterns allow tuning without code changes (Trump Card implementation proved this)
- [ ] SQLite registry tracks all files and operations
- [ ] Unique codes generate without collisions

### Phase 2 Success
- [ ] Process step1a sample_files/ folder end-to-end
- [ ] All files renamed correctly with metadata in registry
- [ ] Dry-run mode shows accurate preview
- [ ] Can rollback failed operations

### Phase 3 Success
- [ ] Non-technical user can add new court pattern via YAML edit
- [ ] Config validation catches and explains errors

### Phase 4 Success
- [ ] Process mixed folder (caselaw + articles + statutes) automatically
- [ ] Each document type has distinct filename format
- [ ] Shared code is truly shared (no duplication)

---

## Risk Mitigation

### Risk: Over-Engineering Too Early
**Mitigation:** Caselaw-first approach. Only abstract when we have 2+ working examples.

### Risk: Data Loss During Processing
**Mitigation:**
- All operations in dry-run mode by default
- Atomic file operations (temp write + rename)
- SQLite registry tracks before/after states
- Rollback capability for failed batches

### Risk: Regex Pattern Complexity
**Mitigation:**
- Unit tests for each pattern with sample inputs
- Config validation catches invalid regex
- Fallback to filename extraction when document parsing fails

### Risk: SQLite Registry Corruption
**Mitigation:**
- WAL mode for concurrent access
- Backups before batch operations
- Export to CSV for manual inspection

---

## Next Steps

1. Review and approve this plan
2. Set up project structure (directories, requirements.txt)
3. Begin Phase 1: Build services/text_extractor.py
4. Track progress in 2-Task-Board.md
5. Log decisions and issues in 4-Logbook.md

---

**Document Version:** 1.1
**Last Updated:** 2025-11-28
**Status:** Phase 1 In Progress (2 of 4 services complete)
