# AI Assistant Guide - Document Processor

**Quick reference for AI coding assistants working on this project**

---

## Project Identity

**What:** Unified document processing system for legal and academic documents (rename → code → convert → clean)

**Current Phase:** Phase 1 - Building services layer foundation

**Architecture:** Services layer pattern with caselaw-first development (defer plugin abstraction until Phase 4)

---

## Critical Constraints

### ❌ NEVER Do This

- **Don't create plugin abstractions yet** - We're Phase 1, caselaw-first. No `BasePlugin` until Phase 4 when patterns are clear
- **Don't use dynamic class loading** - No `importlib.import_module("extractors.Something")` from YAML configs
- **Don't add features beyond current phase** - Stick to Phase 1 tasks (see Task Board)
- **Don't duplicate existing code** - Reuse extractors from step1a/step1b, don't recreate
- **Don't use subprocess PDF extraction** - Use `pdfplumber` library, not `pdftotext` command
- **Don't create JSON registries** - Use SQLite via `services/registrar.py` only
- **Don't put implementation logic in orchestrator** - That belongs in services/

### ✅ ALWAYS Do This

- **Put business logic in `src/services/`** - Pure, stateless functions (no state management in services)
- **Put workflow logic in `core/orchestrator.py`** - Coordinates services, doesn't implement
- **Use pdfplumber for PDFs** - `import pdfplumber`, not subprocess calls
- **Use python-docx for Word** - Direct text extraction
- **Update documentation** - Check off `2-Task-Board.md` tasks as you complete them
- **Log decisions** - Add entries to `4-Logbook.md` for significant changes
- **Write unit tests** - All services/ functions need tests with real sample files
- **Use Pydantic models** - Import from `core/models.py` for type safety
- **Check existing code first** - step1a/step1b/step2/step3a have working extractors to reuse

---

## File Organization Quick Reference

```
WHERE THINGS GO:

Business logic (pure functions)     → src/services/
Workflow coordination only          → src/core/orchestrator.py
Data models & validation            → src/core/models.py
Metadata extraction (reuse!)        → src/extractors/ (from step1a/step1b)
Pipeline step implementations       → src/steps/
Text cleaning utilities             → src/cleaners/
Reference data (courts, reporters)  → data/*.json
Document tracking database          → registry/master.db (SQLite)
Configuration (Phase 3+)            → config/*.yaml
Tests                               → tests/
Project documentation               → 1-Context-Documentation/
```

---

## Current Phase: Phase 1 (Services Layer)

**Building ONLY these four services:**

1. **`services/text_extractor.py`**
   - Pure function: `Path → ExtractionResult`
   - PDF extraction with pdfplumber
   - DOCX extraction with python-docx
   - No state, no database writes, just extract text

2. **`services/registrar.py`**
   - SQLite operations (CRUD)
   - Document tracking, metadata storage
   - Unique code allocation
   - Export to JSON/CSV

3. **`services/classifier.py`**
   - Pure function: `str → Classification`
   - Detect document type from text
   - Return confidence scores
   - Start with caselaw detection only

4. **`services/code_generator.py`**
   - Base-25 unique code generation
   - Port logic from `step2/filename_indexer.py`
   - Check for existing codes, rollback on failure

**DO NOT BUILD YET:**
- ❌ Plugin system (Phase 4)
- ❌ YAML config loader (Phase 3)
- ❌ Interactive CLI wizard (Phase 3)
- ❌ Orchestrator (Phase 2)
- ❌ Pipeline steps (Phase 2)

---

## Code Patterns & Examples

### Services Layer Pattern

**GOOD - Pure function, no state:**
```python
# services/text_extractor.py
from pathlib import Path
from dataclasses import dataclass

@dataclass
class ExtractionResult:
    text: str
    success: bool
    error_message: Optional[str] = None

def extract_text(file_path: Path, max_pages: int = None) -> ExtractionResult:
    """Pure function: Path → Text. No side effects except reading file."""
    try:
        import pdfplumber
        with pdfplumber.open(file_path) as pdf:
            pages = pdf.pages[:max_pages] if max_pages else pdf.pages
            text = "\n".join(page.extract_text() or "" for page in pages)
        return ExtractionResult(text=text, success=True)
    except Exception as e:
        return ExtractionResult(text="", success=False, error_message=str(e))
```

**BAD - State management in services:**
```python
# DON'T DO THIS
class TextExtractor:
    def __init__(self):
        self.registry = Registry()  # ❌ Services shouldn't manage state
        self.cache = {}             # ❌ No caching in services

    def extract_and_save(self, path):  # ❌ Services do ONE thing
        text = self._extract(path)
        self.registry.save(text)    # ❌ That's registrar's job
```

### Orchestrator Pattern

**GOOD - Coordinates services:**
```python
# core/orchestrator.py (Phase 2)
def process_file(file_path: Path) -> ProcessingResult:
    # Use services, don't implement
    text = text_extractor.extract_text(file_path)
    doc_type = classifier.classify(text.text)
    metadata = extract_metadata(text.text, doc_type)
    registrar.add_document(file_path, metadata)
    # ... coordinate next steps
```

**BAD - Implements logic:**
```python
# DON'T DO THIS
def process_file(file_path: Path):
    # ❌ Don't implement extraction in orchestrator
    import pdfplumber
    with pdfplumber.open(file_path) as pdf:
        text = pdf.pages[0].extract_text()
    # ... more implementation details
```

---

## Reusing Existing Code

### From step1a (Caselaw) - Reuse As-Is
```python
# These work well, don't recreate:
from extractors.court_extractor import CourtExtractor       # 200+ court patterns
from extractors.reporter_extractor import ReporterExtractor # Citation extraction
from extractors.date_extractor import DateExtractor         # Year extraction
from formatters.case_name_formatter import CaseNameFormatter

# Reference data:
data/bluebook_courts_mapping.json  # Critical - don't modify
data/reporters_database.json       # 100+ reporters
```

### From step1b (Articles) - Reuse As-Is
```python
from extractors.author_extractor import AuthorExtractor
from extractors.title_extractor import TitleExtractor
from extractors.journal_extractor import JournalExtractor
```

### From step2 (Codes) - Port to Service
```python
# Port this logic to services/code_generator.py:
step2/filename_indexer.py:
  - index_to_code() → base-25 encoding
  - has_registry_suffix() → check for ----CODE pattern
```

### From step3a (Conversion) - Reuse As-Is
```python
from cleaners.markdown_cleaner import clean_markdown  # RAG optimization
from cleaners.ocr_cleaner import clean_ocr_text       # Historical text cleanup
```

---

## Testing Requirements

### All Services Need Tests
```python
# tests/test_services/test_text_extractor.py
def test_extract_pdf():
    # Use actual sample files
    result = extract_text(Path("step1a/sample_files/sample.pdf"))
    assert result.success
    assert len(result.text) > 0

def test_extract_corrupt_pdf():
    # Test error handling
    result = extract_text(Path("tests/fixtures/corrupt.pdf"))
    assert not result.success
    assert result.error_message is not None
```

### Test with Real Sample Files
- Use PDFs from `step1a/sample_files/`
- Use articles from `step1b/z_sample_articles/`
- Create `tests/fixtures/` for edge cases (empty, corrupt, etc.)

---

## SQLite Schema (Quick Reference)

```sql
-- Core tables (services/registrar.py)
documents           -- file paths, types, unique codes
metadata            -- extracted fields (key-value, flexible)
processing_steps    -- step completion tracking
codes               -- unique code allocation

-- See 3-Architecture-Map.md for full schema
```

---

## Documentation Quick Links

**Full details in:**
- **Master plan:** `1-Context-Documentation/1-Master-Plan.md`
- **Task tracking:** `1-Context-Documentation/2-Task-Board.md`
- **Architecture:** `1-Context-Documentation/3-Architecture-Map.md`
- **Decision log:** `1-Context-Documentation/4-Logbook.md`
- **Overview:** `1-Context-Documentation/README.md`

**For deep context, read:** `AI-ONBOARDING.md`

---

## Before Starting Work

1. **Check current phase** - Are we still in Phase 1? (Task Board)
2. **Read relevant docs** - Architecture Map for module you're building
3. **Check for existing code** - Can you reuse from step1/step2/step3a?
4. **Plan tests** - What sample files will you test with?

## After Completing Work

1. **Update Task Board** - Check off completed items in `2-Task-Board.md`
2. **Log decisions** - Add entry to `4-Logbook.md` if you made choices or solved issues
3. **Write/update tests** - Ensure test coverage for new code
4. **Update this file** - If you discover new patterns or constraints

---

## Common Pitfalls

### Over-Engineering
- **Problem:** Building plugin system before understanding patterns
- **Solution:** Caselaw-first. Build complete implementation, THEN abstract

### Mixing Concerns
- **Problem:** Putting database writes in text extraction functions
- **Solution:** Services do ONE thing. Orchestrator coordinates.

### Recreating Existing Code
- **Problem:** Rewriting court extraction when it exists in step1a
- **Solution:** Check step1/step2/step3a first. Reuse, don't recreate.

### Subprocess Over-Use
- **Problem:** Using `subprocess.run(['pdftotext', ...])`
- **Solution:** Use Python libraries (pdfplumber, python-docx)

---

**Last Updated:** 2025-11-28
**Current Phase:** Phase 1 - Services Layer
**Status:** Ready for Implementation
