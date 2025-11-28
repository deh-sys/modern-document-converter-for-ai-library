# Document Processor - Project Documentation

Welcome to the unified document processing system documentation. This folder contains all planning, architecture, and progress tracking documents.

---

## What This Project Does

**Unified Document Processing Pipeline** for legal and academic documents:

1. **Rename** - Extract metadata and normalize filenames
   - Legal cases: `c.ILL_ND__2010__Abbott-v-Sandoz__743_FSupp2d_762.pdf`
   - Articles: `1974_Arnold_Law_Fact_Medieval_Jury.pdf`
   - Statutes: `s.USC__2010__Title_42_Section_1983.pdf`

2. **Code** - Add unique 5-letter identifiers
   - `c.ILL_ND__2010__Abbott-v-Sandoz__743_FSupp2d_762----ABCDE.pdf`

3. **Convert** - Transform to plain text
   - PDF/DOCX → clean TXT using pdfplumber and python-docx

4. **Clean** - Optimize for AI/RAG consumption
   - Normalize formatting, detect headings, prepare for embeddings

---

## Current Status

**Phase:** Planning Complete, Implementation Starting
**Last Updated:** 2025-11-28

### Completed
- ✅ Codebase analysis and review
- ✅ Architectural design with services layer
- ✅ Phased implementation plan
- ✅ Project documentation structure

### In Progress
- ⏳ Setting up project structure
- ⏳ Building core services layer (Phase 1)

### Next Up
- Phase 1: Core services foundation (text extraction, registry, classification)
- Phase 2: Caselaw end-to-end implementation

---

## Documentation Files

### 📋 [1-Master-Plan.md](1-Master-Plan.md)
**The complete project strategy and roadmap**

Read this to understand:
- Overall project goals and vision
- Phased implementation strategy (4 phases)
- Technology stack decisions and rationale
- Design principles (services layer, caselaw-first, config-driven)
- Migration plan from existing code
- Success metrics and risk mitigation

**Start here** if you're new to the project or need the big picture.

---

### ✅ [2-Task-Board.md](2-Task-Board.md)
**Detailed task tracking and progress management**

Read this to understand:
- Phase 1 tasks with checkboxes (services layer development)
- Phase 2-4 task lists (pending completion of earlier phases)
- Deferred features and why they're deferred
- Current sprint status and blockers
- Open questions and decisions needed

**Update this** as tasks are completed and new work is identified.

---

### 🏗️ [3-Architecture-Map.md](3-Architecture-Map.md)
**Complete system architecture and design**

Read this to understand:
- Target directory structure with detailed annotations
- Module responsibilities and interfaces
- Data flow diagrams (overall pipeline, rename step details)
- Services layer design (text_extractor, registrar, classifier, code_generator)
- Plugin system architecture (Phase 4)
- SQLite schema design
- Current codebase migration analysis
- Technology dependencies and design patterns

**Reference this** when implementing any module or understanding how components interact.

---

### 📝 [4-Logbook.md](4-Logbook.md)
**Development journal and decision log**

Read this to understand:
- Why specific design decisions were made
- Issues encountered and solutions applied
- Lessons learned during development
- Open questions and risks identified

**Update this** after significant work sessions, decisions, or when encountering issues.

---

## Quick Start Guide

### Prerequisites
```bash
# Required Python version
python >= 3.9

# Install dependencies
pip install -r requirements.txt

# External tools (optional)
# - LibreOffice (for legacy .doc conversion)
```

### Installation
```bash
# Clone or navigate to project
cd MODERN-DOCS

# Set up virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Usage (Coming in Phase 2)
```bash
# Basic usage (planned)
python main.py process /path/to/files --type caselaw

# Dry-run mode (preview changes)
python main.py process /path/to/files --type caselaw --dry-run

# Verbose output
python main.py process /path/to/files --type caselaw --verbose

# Check registry status
python main.py status

# Export registry to CSV
python main.py export registry.csv
```

---

## Project Structure Overview

```
MODERN-DOCS/
├── 1-Context-Documentation/     # You are here
│   ├── README.md                # This file
│   ├── 1-Master-Plan.md         # Strategy & roadmap
│   ├── 2-Task-Board.md          # Task tracking
│   ├── 3-Architecture-Map.md    # System design
│   └── 4-Logbook.md             # Development journal
│
├── step1--Base_FILENAME--a-caselaw/      # Existing caselaw renamer
├── step1--Base_FILENAME--b-articles/     # Existing articles renamer
├── step2--FILE_CODE_NAME---All Files/    # Existing code generator
├── step3a--NORMALIZE-TXT--MODERN.../     # Existing converter
│
└── src/                         # New unified application (to be built)
    ├── core/                    # Orchestration
    ├── services/                # Business logic layer
    ├── plugins/                 # Document type handlers
    ├── extractors/              # Metadata extraction
    ├── steps/                   # Pipeline steps
    ├── cleaners/                # Text cleaning
    └── utils/                   # Shared utilities
```

---

## Existing Code (Legacy Applications)

The four existing applications that will be unified:

### step1a - Caselaw Renamer
- Extracts court, year, case name, reporter from legal case PDFs
- Uses Bluebook citation format
- 200+ court mappings, 100+ reporter citations
- Output: `c.COURT__YEAR__CASE-NAME__REPORTER.pdf`

### step1b - Articles Renamer
- Extracts authors, title, year from academic PDFs
- Evaluates filename quality before renaming
- Output: `YEAR_AUTHOR_TITLE.pdf`

### step2 - Code Generator
- Adds unique 5-letter codes to any file/folder
- Base-25 encoding (9.7M unique codes)
- Centralized registry prevents collisions
- Output: `original-filename----ABCDE.ext`

### step3a - Document Converter
- PDF/DOCX/EPUB → clean Markdown or TXT
- AI-powered structure detection (marker-pdf)
- RAG-optimized cleaning for embeddings
- SQLite tracking to avoid re-processing

**These will be migrated incrementally** starting with caselaw (Phase 2).

---

## Key Design Decisions

### 1. Services Layer Architecture
Separates workflow (orchestrator) from implementation (services):
- `orchestrator.py` - Coordinates pipeline (~200 lines)
- `services/` - Pure business logic, stateless, testable

### 2. Caselaw-First Development
Build complete working pipeline for one document type before abstracting to plugins.

### 3. SQLite Registry
Single source of truth replacing multiple JSON files from separate apps.

### 4. Configuration-Driven
Regex patterns and templates in YAML (Phase 3), not dynamic class loading.

### 5. Phased Implementation
- Phase 1: Services foundation
- Phase 2: Caselaw end-to-end
- Phase 3: YAML configs
- Phase 4: Plugin system + more document types

See [1-Master-Plan.md](1-Master-Plan.md) for full rationale.

---

## Technology Stack

**Core Libraries:**
- `pdfplumber` - PDF text extraction (Python-native)
- `python-docx` - Word document parsing
- `sqlite3` - Document registry and tracking
- `click` - CLI framework
- `pydantic` - Data validation and models
- `pyyaml` - Configuration files

**Development Tools:**
- `pytest` - Testing framework
- `black` - Code formatting
- `ruff` - Linting

---

## Contributing Guidelines

### Before Making Changes
1. Read [1-Master-Plan.md](1-Master-Plan.md) to understand the vision
2. Check [2-Task-Board.md](2-Task-Board.md) for current priorities
3. Review [3-Architecture-Map.md](3-Architecture-Map.md) for module responsibilities

### During Development
1. Update [2-Task-Board.md](2-Task-Board.md) as you complete tasks
2. Log significant decisions in [4-Logbook.md](4-Logbook.md)
3. Write unit tests for new functionality
4. Follow existing code patterns and conventions

### After Completing Work
1. Mark tasks as complete in task board
2. Add logbook entry with context and decisions
3. Update architecture map if design changed
4. Update this README if user-facing changes

---

## Contact & Support

**Issues & Questions:**
- Check [4-Logbook.md](4-Logbook.md) for known issues
- Review [2-Task-Board.md](2-Task-Board.md) open questions section

**External Dependencies:**
- pdfplumber docs: https://github.com/jsvine/pdfplumber
- python-docx docs: https://python-docx.readthedocs.io/
- Click docs: https://click.palletsprojects.com/

---

## License & Credits

**Existing Code:**
- step1a, step1b, step2, step3a: Original implementations to be unified
- Bluebook courts mapping: Legal citation database
- Reporters database: Legal citation database

**New Unified System:**
- Built on architectural patterns from existing code
- Refactored for modularity, testability, and extensibility

---

**Documentation Version:** 1.0
**Last Updated:** 2025-11-28
**Status:** Planning Complete, Ready for Phase 1 Implementation
