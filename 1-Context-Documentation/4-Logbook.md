# Development Logbook

Track design decisions, issues encountered, and lessons learned during development.

---

## 2025-11-28 - Project Kickoff & Architectural Design

### Context
Reviewed existing codebase consisting of four separate applications:
- `step1a--Base_FILENAME--a-caselaw/` - Caselaw file renaming
- `step1b--Base_FILENAME--b-articles/` - Academic article renaming
- `step2--FILE_CODE_NAME---All Files/` - Unique code assignment
- `step3a--NORMALIZE-TXT--MODERN--convert_to_txt--clean--add_headings/` - Document conversion & cleaning

**Goal:** Consolidate into single unified application with modular architecture.

### Major Decisions Made

#### 1. Services Layer Architecture ✅
**Decision:** Add dedicated `services/` layer between orchestrator and implementation.

**Rationale:**
- Keeps orchestrator clean (workflow logic only, ~200 lines)
- Services are pure business logic, stateless, easily testable
- Easy to swap implementations (e.g., PostgreSQL instead of SQLite)
- Clear separation of concerns

**Influenced by:** Architectural feedback emphasizing that dynamic plugin loading is the hardest part and orchestrator should be kept simple.

**Services identified:**
- `text_extractor.py` - PDF/DOCX → text
- `registrar.py` - SQLite operations
- `classifier.py` - Document type detection
- `code_generator.py` - Unique code generation

---

#### 2. Caselaw-First Development ✅
**Decision:** Build complete working implementation for caselaw before abstracting to plugin system.

**Rationale:**
- Avoid over-engineering before understanding the patterns
- Get working end-to-end pipeline quickly
- See what's truly shared vs. document-type-specific
- Only abstract after having 2+ working examples

**Timeline:**
- Phase 1: Core services foundation
- Phase 2: Caselaw end-to-end (hardcoded)
- Phase 3: Extract patterns to YAML configs
- Phase 4: Abstract to plugin system when patterns are clear

---

#### 3. Configuration Strategy ✅
**Decision:** YAML configs for patterns only, NOT for dynamic class loading.

**What goes in YAML:**
- Regex patterns for extraction
- Filename templates
- Court mappings and abbreviations
- Pipeline step enablement

**What stays in Python:**
- Class structures
- Plugin loading logic
- Core orchestration

**Rejected approach:** Dynamic imports like `importlib.import_module("extractors.JurisdictionExtractor")`

**Rationale:**
- Dynamic string-to-class loading is hard to debug
- Type safety and IDE support are valuable
- Can still make patterns user-editable without full dynamic loading
- Simpler is better for initial implementation

---

#### 4. Technology Stack Decisions ✅

**PDF Extraction: pdfplumber (not pdftotext)**
- Python-native (no subprocess calls)
- Better table and layout handling
- Already familiar from other projects
- Replaces: step1a/step1b subprocess calls to pdftotext

**Word Extraction: python-docx**
- Keep existing approach (working well)

**Registry: SQLite (not multiple JSON files)**
- Consolidates:
  - step1a: `metadata_registry.json` + CSV
  - step1b: `metadata_registry.json` + CSV
  - step2: `filename-indexing-registry.json`
  - step3a: `doc_to_markdown_history.db`
- Single source of truth
- Atomic transactions (WAL mode)
- Better query capabilities
- Export to JSON/CSV still supported for analysis

---

#### 5. Deferred Features ✅
**Decision:** Defer these to later phases:

**Deferred to Phase 3:**
- Interactive CLI wizard
- Drag-drop macOS wrapper
- YAML configuration system

**Deferred to Phase 4:**
- Plugin abstraction (BasePlugin interface)
- Additional document types (statutes, briefs, books)
- Modern pipeline architecture from step1a/file_renamer/

**Deferred indefinitely:**
- Web interface
- Parallel batch processing
- Advanced metadata exports (BibTeX, Zotero)

**Rationale:** Start simple, add complexity only when needed.

---

### Code Migration Plan

#### Reuse As-Is
From step1a:
- `extractors/court_extractor.py`
- `extractors/reporter_extractor.py`
- `extractors/date_extractor.py`
- `formatters/case_name_formatter.py`
- `data/bluebook_courts_mapping.json`
- `data/reporters_database.json`

From step1b:
- `extractors/author_extractor.py`
- `extractors/title_extractor.py`
- `extractors/journal_extractor.py`

From step3a:
- `markdown_cleaner.py`
- `clean_txt.py` (OCR cleaning)

#### Refactor & Consolidate
**Text extraction:**
- step1a/pdf_extractor.py + step1b/pdf_extractor.py → `services/text_extractor.py` (pdfplumber)
- step1a/docx_extractor.py + step1b/docx_extractor.py → `services/text_extractor.py`

**Registry management:**
- step1a/registry_manager.py + step2/JSON registry + step3a/tracking.py → `services/registrar.py` (SQLite)

**Renaming logic:**
- step1a/renamer.py + step1b/renamer.py → `steps/rename_step.py` + `plugins/caselaw.py`

**Code generation:**
- step2/filename_indexer.py → `services/code_generator.py`

#### Eliminate Duplication
**Identical files to consolidate:**
- pdf_extractor.py (appears in step1a and step1b)
- docx_extractor.py (appears in step1a and step1b)
- date_extractor.py (appears in step1a and step1b)
- config_manager.py (appears in step1a and step1b)

---

### Open Questions & Decisions Needed

#### Q1: File handling strategy
**Question:** Should we rename files in place or create copies?

**Options:**
- A) Rename in place (current step1 behavior)
- B) Copy to new location with new name
- C) Configurable via settings

**Current thinking:** Rename in place (option A) for Phase 1, make configurable later.

---

#### Q2: Duplicate filename handling
**Question:** How to handle filename collisions across different document types?

**Scenario:**
- Caselaw: `c.ILL_ND__2010__Abbott-v-Sandoz.pdf`
- Articles: Could also generate similar name by coincidence

**Options:**
- A) Document type prefix prevents collisions (`c.` vs `a.`)
- B) Additional hash in filename
- C) Subdirectories by type

**Current thinking:** Type prefix (option A) should be sufficient.

---

#### Q3: Registry tracking of external changes
**Question:** Should registry track files that are moved/renamed outside the app?

**Options:**
- A) Registry is source of truth, warn if files don't match
- B) Registry auto-updates when files are found at new locations
- C) Provide "sync" command to reconcile registry with filesystem

**Current thinking:** Defer to Phase 2, implement option C (sync command).

---

### Risks Identified

#### Risk: Over-engineering
**Mitigation:** Caselaw-first approach, only abstract after seeing patterns.
**Status:** Mitigated through phased development plan.

#### Risk: SQLite corruption
**Mitigation:** WAL mode, backups before batch operations, CSV export.
**Status:** Will test thoroughly in Phase 1.

#### Risk: pdfplumber performance
**Concern:** Slower than pdftotext for large PDFs?
**Mitigation:** Benchmark with real files, can fall back to pdftotext if needed.
**Status:** To be tested in Phase 1.

#### Risk: Regex pattern complexity
**Concern:** Patterns may become hard to maintain.
**Mitigation:** Unit tests for each pattern, config validation, graceful fallbacks.
**Status:** Existing patterns in step1a/step1b work well, should be fine.

---

### Next Actions
1. ✅ Create documentation folder structure
2. ✅ Write 1-Master-Plan.md
3. ✅ Write 2-Task-Board.md
4. ✅ Write 3-Architecture-Map.md
5. ✅ Write 4-Logbook.md (this file)
6. ✅ Write README.md
7. ⏳ Set up project directory structure
8. ⏳ Create requirements.txt
9. ⏳ Begin Phase 1: Build services/text_extractor.py

---

### Lessons Learned
- Services layer architecture proved valuable - orchestrator stays clean, services are easily testable
- Caselaw-first approach prevented over-engineering - built real working code before abstracting
- YAML-driven patterns work well for configuration without dynamic class loading complexity

---

## 2025-11-28 (Afternoon) - Text Extractor & Classifier Services Implementation

### Context
Building Phase 1 core services: text extraction and document classification.

**Goal:** Extract text from PDF/DOCX files and classify document type using YAML-driven pattern matching.

### Decisions Made

#### 1. Text Normalization Strategy ✅
**Decision:** Use clean-text library + custom legal-specific cleaning

**Implementation:**
- Created `src/cleaners/text_normalizer.py` (310 lines)
- clean-text library handles: unicode, ASCII conversion, extra whitespace, broken encoding
- Custom `fix_hyphens()` function for legal documents:
  - Fixes broken line hyphens: "defend-\nant" → "defendant"
  - Handles both lowercase and uppercase continuation
- Normalize function is optional parameter in `extract_text()`

**Rationale:** Legal documents have specific formatting quirks (hyphenated line breaks) that generic cleaners miss.

**Result:** Clean, normalized text ready for classification and metadata extraction.

---

#### 2. Text Extraction Architecture ✅
**Decision:** Strategy pattern with internal PDF/DOCX handlers

**Implementation:**
- Created `src/services/text_extractor.py` (335 lines)
- `extract_text()` public API dispatches to:
  - `_extract_pdf()` - pdfplumber with layout=True
  - `_extract_docx()` - python-docx paragraph extraction
- Returns `ExtractionResult` model (success, text, page_count, error_message)
- Error handling: Returns failure result instead of raising exceptions

**Rationale:**
- pdfplumber is Python-native (no subprocess calls like pdftotext)
- layout=True preserves spacing for better pattern matching
- Strategy pattern allows easy addition of new formats later
- ExtractionResult provides type-safe, consistent error handling

**Test Results:**
- Indian_Trail.pdf: 43,124 characters, 13 pages - SUCCESS
- Clean extraction with preserved layout
- Smoke test tool created: `smoke_test_extractor.py`

---

#### 3. YAML-Driven Classification System ✅
**Decision:** Pattern matching with weighted scoring, NO hardcoded keywords

**Implementation:**
- Created `src/services/classifier.py` (405 lines)
- Classification rules in `config/document_types/*.yaml`
- Each pattern has:
  - `pattern`: Regex to match
  - `description`: Human-readable explanation
  - `weight`: Positive or negative score contribution
  - `case_sensitive`: Boolean flag
  - `notes`: Optional implementation notes

**Architecture:**
```python
def classify(text: str) -> Classification:
    1. Load all enabled YAML rule files (cached)
    2. Score text against each document type
    3. Sum weights for matched patterns
    4. Map score to confidence level (HIGH/MEDIUM/LOW)
    5. Return highest scoring type
```

**Confidence Thresholds:**
- HIGH: ≥60 points
- MEDIUM: ≥30 points
- LOW: ≥10 points
- Below 10: Return UNKNOWN

**Rationale:**
- User-editable patterns without touching Python code
- Transparent scoring (can see which patterns matched)
- Flexible weighting allows tuning
- Negative patterns prevent false positives

---

#### 4. Caselaw Classification Rules ✅
**Created:** `config/document_types/caselaw.yaml` (122 lines)

**Strong Indicators (75 points total):**
- Case caption with "v." or "versus": +40
- Reporter citation (e.g., "328 Ga. App. 524"): +35

**Medium Indicators (55 points combined):**
- Court name (Supreme Court, Court of Appeals, etc.): +20
- Legal database citation (LEXIS, Westlaw): +15
- Party designation (Plaintiff, Defendant, Appellant): +10
- Decision date notation: +10

**Weak Indicators (5 points each):**
- Legal procedural terms (Opinion, Judgment, ORDER)
- Judicial action verbs (affirm, reverse, remand)
- Case/docket number
- Judge attribution ("Smith, J., concurring")

**Negative Indicators:**
- Statutory citation (§, U.S.C.): -10 (suggests statute, not case)

**Test Results:**
- Indian_Trail.pdf: 140 points (capped at 100% confidence)
- Classification: CASELAW with HIGH confidence
- Matched 9 patterns successfully

---

### Issues Encountered

#### Issue 1: Confidence Validation Error ❌
**Problem:**
```
pydantic_core._pydantic_core.ValidationError:
confidence Input should be less than or equal to 1
[input_value=1.4]
```

**Cause:** Caselaw scored 140 points, normalized to 1.4, exceeding Pydantic's 0.0-1.0 constraint

**Solution:** Added `min()` cap in three places in `classifier.py`:
```python
confidence=min(best_score / 100.0, 1.0)  # Normalize to 0-1, cap at 1.0
```

**Learning:** Pydantic validation constraints must be enforced before creating model instances.

---

#### Issue 2: Smoke Test Display Bug ❌
**Problem:** Summary section showed wrong document type (displayed loop variable instead of classification result)

**Cause:** Variable name collision on line 194:
```python
for doc_type, (score, indicators) in sorted(...)  # Overwrites doc_type from line 137
```

**Solution:** Renamed loop variable:
```python
for type_name, (score, indicators) in sorted(...)  # No collision
```

**Learning:** Be careful with variable scope in Python, especially when reusing common names.

---

### Code Changes

**New Files:**
- `src/core/models.py` (454 lines) - Pydantic data models
- `src/cleaners/text_normalizer.py` (310 lines) - Text cleaning with clean-text + custom hyphen fixing
- `src/services/text_extractor.py` (335 lines) - PDF/DOCX extraction with pdfplumber/python-docx
- `src/services/classifier.py` (405 lines) - YAML-driven classification
- `config/document_types/caselaw.yaml` (122 lines) - Caselaw patterns
- `config/document_types/article.yaml` (62 lines) - Placeholder (disabled)
- `smoke_test_extractor.py` (224 lines) - CLI testing tool for extraction
- `smoke_test_classifier.py` (224 lines) - CLI testing tool for classification

**Updated Files:**
- `requirements.txt` - Added unidecode>=1.3.0 to fix unicode warnings

---

### Testing Notes

**Text Extraction:**
- Tested with Indian_Trail.pdf (legal case, 13 pages)
- Success: 43,124 characters extracted
- pdfplumber layout preservation works well
- Hyphen fixing successfully merged line-broken words

**Caselaw Classification:**
- Tested with Indian_Trail.pdf
- Score: 140 points (HIGH confidence)
- Matched patterns:
  - Case caption with 'v.' ✓
  - Reporter citation format ✓
  - Court name ✓
  - Legal database citation ✓
  - Party designation ✓
  - Decision date notation ✓
  - Legal procedural terms ✓
  - Judicial action verbs ✓
  - Statutory citation (negative) ✓

**Smoke Test Tools:**
- Both tools use rich library for formatted output
- Tables, panels, and color-coded confidence levels
- `--show-scores` flag shows all document types with detailed pattern matches
- `--json-output` for programmatic use
- `--max-pages` for faster testing on large files

---

### Next Steps
- [x] Text Extractor Service - COMPLETE
- [x] Classifier Service - COMPLETE
- [ ] Create statute classification rules
- [ ] Test statute classification
- [ ] Build Registrar Service (SQLite)
- [ ] Build Code Generator Service (base-25)

---

## 2025-11-28 (Evening) - Statute Classification & Trump Card Philosophy

### Context
User tested classifier on OCGA (Official Code of Georgia Annotated) statute file.

**Problem Discovered:** Annotated statute misclassified as CASELAW
- STATUTE score: 60 points
- CASELAW score: 130 points (WRONG WINNER)

**Root Cause:** Annotated codes contain both:
1. Statute text with "Official Code of...", "TITLE", "§" symbols
2. Case annotations with "v.", court names, case citations

Original negative patterns too aggressive (-30, -20, -15, -10) penalized statute score heavily.

### Major Decision: Trump Card Philosophy ✅

**User Guidance:**
> "This 'Annotated Code' issue is a critical edge case in legal tech. We need a Hybrid Solution with a 'Trump Card' philosophy."

**Principle:** Definitive indicators should overwhelm ambiguous signals

**Rationale:**
> "An Annotated Statute (Statute + Case Notes) IS a Statute. The presence of 'Official Code of...' is a definitive marker that overrides any amount of 'v.' or 'Court' mentions found in the annotations."

### Decisions Made

#### 1. Trump Card Weights for Statutes ✅
**Decision:** Boost definitive statute indicators to massive weights

**Changes to `config/document_types/statutes.yaml`:**

**Trump Card Indicators:**
- "Official Code of": 40 → **100 points** (DEFINITIVE)
  - Notes: "TRUMP CARD - Definitive statute marker. If this exists, document IS a statute (even if annotated with cases)"
- "TITLE \d+": 20 → **50 points** (DEFINITIVE)
  - Notes: "TRUMP CARD - Strong structural indicator of codified statute"

**High Weight Indicators (unchanged):**
- § symbol: +35
- O.C.G.A. spaced acronym: +30
- U.S.C.: +30
- C.F.R.: +30

**Rationale:** These two patterns ("Official Code of" and "TITLE") are unambiguous proof that a document is a statute, regardless of any case annotations present.

---

#### 2. Light Negative Patterns for Annotated Codes ✅
**Decision:** Reduce negative penalties from aggressive to light touch

**Changes:**
- "v." case caption: -30 → **-5**
- Court names: -20 → **-5**
- Party designations: -15 → **-5**
- Decision dates: -10 → **-5**
- Judicial language (Opinion, affirm, etc.): -10 → **-5**

**Notes added to YAML:**
```yaml
notes: "Light negative - annotated codes cite many cases. Only slight penalty to distinguish from pure caselaw"
```

**Rationale:** Annotated codes naturally contain case references in their annotations. Heavy penalties would incorrectly penalize all annotated statutes. Light penalties (-5) acknowledge the presence of case content without overwhelming the definitive statute markers.

---

### Code Changes

**Modified Files:**
- `config/document_types/statutes.yaml` (167 lines)
  - Trump Card weights: "Official Code of" (+100), "TITLE \d+" (+50)
  - Light negative patterns: All reduced to -5
  - Added detailed notes explaining Trump Card philosophy

---

### Testing Notes

**Before Trump Card (FAILED):**
- STATUTE: 60 points
- CASELAW: 130 points ← WRONG WINNER
- Result: Annotated statute misclassified as case

**After Trump Card (SUCCESS):**
- **STATUTE: 205 points** ← CORRECT WINNER
- CASELAW: 130 points
- Result: Annotated statute correctly classified

**Score Breakdown:**
```
STATUTE (205 points):
  Official Code designation         +100  (TRUMP CARD)
  Title number (TITLE \d+)          +50   (TRUMP CARD)
  O.C.G.A. spaced acronym           +30
  Chapter number                    +15
  Code reference                    +10
  Section number notation           +10
  Legislative action verbs          +5
  Statutory subdivision notation    +5

  Case caption 'v.' (negative)      -5
  Court name (negative)             -5
  Party designation (negative)      -5
  Decision date (negative)          -5
  ──────────────────────────────────────
  TOTAL                             205

CASELAW (130 points):
  Case caption 'v.'                 +40
  Reporter citation                 +35
  Court name                        +20
  Legal database citation           +15
  Party designation                 +10
  Decision date                     +10
  Legal procedural terms            +5
  Judicial action verbs             +5
  Statutory citation (negative)     -10
  ──────────────────────────────────────
  TOTAL                             130
```

**Margin of Victory:** 75 points (205 vs 130)

---

### Lessons Learned

**Critical Legal Tech Edge Case:**
- Annotated legal codes are hybrid documents (primary law + case commentary)
- Classification must recognize document's PRIMARY nature (statute) despite secondary content (cases)
- Definitive markers ("Official Code of") are more reliable than frequency-based patterns

**Trump Card Pattern Design:**
- Not all patterns are equal - some are definitive, some are suggestive
- Definitive patterns should have weights that overcome cumulative ambiguous patterns
- Negative patterns should acknowledge legitimate hybrid content

**Scoring System Flexibility:**
- Weighted scoring allows sophisticated distinctions impossible with boolean matching
- Ability to tune weights makes system adaptable to edge cases
- Transparent scoring (show all matched patterns) enables debugging and confidence

**YAML Configuration Power:**
- Changed classification behavior without touching Python code
- Added explanatory notes directly in config for future maintainers
- User can tune weights based on their specific corpus

---

### Next Steps
- [x] Statute classification - COMPLETE
- [x] Trump Card implementation - COMPLETE
- [x] Test annotated statute - SUCCESS
- [ ] Build Registrar Service (SQLite)
- [ ] Build Code Generator Service (base-25)
- [ ] Move to Phase 2 (end-to-end caselaw pipeline)

---

## Template for Future Entries

```markdown
## YYYY-MM-DD - [Title]

### Context
[What were you working on? What problem were you solving?]

### Decisions Made
[What choices did you make? Why?]

### Issues Encountered
[Problems, bugs, unexpected behavior]

### Solutions Applied
[How did you resolve the issues?]

### Code Changes
[Key files modified, functions added/removed]

### Testing Notes
[What did you test? Results?]

### Next Steps
[What needs to be done next?]

### Open Questions
[Unresolved issues or decisions needed]
```

---

**Logbook started:** 2025-11-28
**Last updated:** 2025-11-28 (Evening - Trump Card implementation complete)
