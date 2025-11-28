# Caselaw File Renamer - Complete Implementation Plan

## Project Overview

**Goal:** Create an application to rename PDF and MS Word documents of caselaw using a standardized format.

**Target Format:** `cs_[court]-[year]-[case-name]-[reporter].pdf`

**Example:** `cs_ND-Ill-2010-Abbott-Labs-v-Sandoz-Inc-FSupp2d.pdf`

---

## Project Deliverables Completed

### ✅ Analysis & Documentation

1. **sample_analysis.json** - Raw data from analyzing 6 sample files
2. **EXTRACTION_RULES.md** - Comprehensive extraction logic and rules
3. **FORMATTING_RULES.md** - Finalized formatting decisions
4. **courts_mapping.json** - Court identification database (100+ courts)
5. **reporters_database.json** - Reporter citation database (100+ reporters)
6. **PROPOSED_FILENAMES.md** - Before/after examples with explanations

### 📊 Test Results

- **Sample Size:** 6 PDF files with varying formats
- **Success Rate:** 100% (all elements successfully extracted)
- **Key Finding:** PDF text extraction is essential (filenames alone are incomplete/incorrect)

---

## Extraction Logic - Fixed Rules

### 1. Court/Jurisdiction Extraction

**Sources (in priority order):**
1. PDF text (primary) - search for official court name
2. Filename parenthetical - e.g., "(ND Ill 2010)"
3. Filename prefix - e.g., "law - GA COA -"

**Recognition Patterns:**
- Federal: Match patterns like "United States District Court for the Northern District of Illinois"
- State: Match patterns like "Supreme Court of Georgia"
- Use regex patterns from `courts_mapping.json`

**Standardization:**
- Federal District: `[Direction]-[State]` → `ND-Ill`, `ED-Va`, `SD-NY`
- Federal Circuit: `[Number]-Cir` → `1st-Cir`, `2d-Cir`, `11th-Cir`
- Supreme Court: `SCOTUS`
- State format: `[State]-[Court]` → `GA-SC`, `GA-COA`, `CA-SC`
- State trial courts: `[State]-[Court]-[County]` → `GA-State-Fulton`

**Key Insight:** Filename can be wrong (see Alden case - filename said "1st Cir" but was actually SCOTUS)

### 2. Year Extraction

**Sources (in priority order):**
1. PDF "Decided:" date (most reliable)
2. PDF "Filed:" date (if no decided date)
3. Filename parenthetical year
4. Filename LEXIS/WL citation year

**Extraction Strategy:**
- Look for: `Decided: [Month] [Day], [YEAR]` in PDF text
- Avoid: Dates in margins/headers (download dates)
- Validate: Year must be 1700-2025
- Extract: 4-digit year only

**Key Insight:** Watch for download dates in margins - focus on labeled dates in case caption

### 3. Case Name Extraction & Formatting

**Sources (in priority order):**
1. PDF case caption (most accurate)
2. Filename case name

**Extraction:**
- Identify case caption by finding " v. " or " vs. " pattern
- Extract text before and after the "v"

**Formatting Rules (user-finalized):**
1. Split at "v" → left party, right party
2. Take only FIRST party on each side (split at comma if multiple parties)
3. Remove ALL special characters: `.` `,` `'` `&` `"` `(` `)` `:` `;`
4. Tokenize into words (split on spaces)
5. Take first 2 WORDS from each side
6. Join with hyphens between words
7. Join parties with " v " in middle

**Examples:**
- "Abbott Labs. v. Sandoz, Inc" → `Abbott-Labs-v-Sandoz-Inc`
- "O'Brien v. State" → `OBrien-v-State`
- "Smith, Jones & Co. v. Brown" → `Smith-Jones-v-Brown`
- "A, B, C v. X, Y, Z" → `A-v-X` (single word each side)

### 4. Reporter Citation Extraction

**Sources (in priority order):**
1. PDF text (most reliable)
2. Filename citation

**Recognition Patterns:**
- Federal: `\d+ F\.3d \d+` → `F3d`
- Federal District: `\d+ F\. Supp\. 2d \d+` → `FSupp2d`
- Regional: `\d+ S\.E\.2d \d+` → `SE2d`
- State: `\d+ Ga\. \d+` → `Ga`
- Online: `U.S. Dist. LEXIS \d+` → `USDistLEXIS`

**Priority Selection (if multiple found):**
1. Official state reporter (e.g., Ga., Cal.)
2. Regional reporter (e.g., S.E.2d, P.3d)
3. Federal print reporter (e.g., F.3d, F.Supp.2d)
4. Online database (e.g., LEXIS, WL)

**Formatting (user-finalized):**
- Remove ALL dots from reporter abbreviations
- `F.Supp.2d` → `FSupp2d`
- `S.E.2d` → `SE2d`
- `U.S.` → `US`
- `Ga.App.` → `GaApp`

**Fallback:**
- If no reporter found → use `Unpub` (unpublished/unreported)

---

## Complete Extraction Algorithm

```python
def extract_filename_elements(pdf_path, original_filename):
    """
    Extract all 4 elements needed for standardized filename.
    Returns: (court_code, year, case_name, reporter_code)
    """

    # Step 1: Extract text from first 2 pages of PDF
    pdf_text = extract_pdf_text(pdf_path, max_pages=2)

    # Step 2: Parse original filename for hints
    filename_hints = parse_filename(original_filename)

    # Step 3: Extract court
    court_from_pdf = find_court_in_text(pdf_text)  # Primary source
    court_from_filename = filename_hints.get('court')  # Fallback
    court_code = standardize_court(court_from_pdf or court_from_filename)

    # Step 4: Extract year
    year_from_pdf = find_decision_date(pdf_text)  # Primary source
    year_from_filename = filename_hints.get('year')  # Fallback
    year = year_from_pdf or year_from_filename

    # Step 5: Extract case name
    case_name_from_pdf = find_case_caption(pdf_text)  # Primary source
    case_name_from_filename = filename_hints.get('case_name')  # Fallback
    raw_case_name = case_name_from_pdf or case_name_from_filename
    case_name = format_case_name(raw_case_name)

    # Step 6: Extract reporter
    reporter_from_pdf = find_reporter_citation(pdf_text)  # Primary source
    reporter_from_filename = filename_hints.get('reporter')  # Fallback
    reporter = reporter_from_pdf or reporter_from_filename or "Unpub"
    reporter_code = format_reporter(reporter)  # Remove dots

    # Step 7: Construct new filename
    new_filename = f"cs_{court_code}-{year}-{case_name}-{reporter_code}.pdf"

    return new_filename
```

### Helper Function: format_case_name()

```python
def format_case_name(raw_case_name):
    """
    Format case name according to finalized rules.
    Input: "Abbott Labs. v. Sandoz, Inc., Johnson"
    Output: "Abbott-Labs-v-Sandoz-Inc"
    """

    # Step 1: Split at "v." or "v" (case insensitive)
    parts = re.split(r'\s+v\.?\s+', raw_case_name, flags=re.IGNORECASE, maxsplit=1)
    if len(parts) != 2:
        return sanitize(raw_case_name)  # Fallback if no "v" found

    left_party, right_party = parts

    # Step 2: Take only first party on each side (before first comma)
    left_party = left_party.split(',')[0].strip()
    right_party = right_party.split(',')[0].strip()

    # Step 3: Remove special characters
    special_chars = r'[.,\'\"&();:]'
    left_party = re.sub(special_chars, '', left_party)
    right_party = re.sub(special_chars, '', right_party)

    # Step 4: Remove "et al" if present
    left_party = re.sub(r'\s*et\s+al\.?\s*', '', left_party, flags=re.IGNORECASE)
    right_party = re.sub(r'\s*et\s+al\.?\s*', '', right_party, flags=re.IGNORECASE)

    # Step 5: Tokenize and take first 2 words
    left_words = left_party.split()[:2]  # First 2 words
    right_words = right_party.split()[:2]  # First 2 words

    # Step 6: Join with hyphens
    left_formatted = '-'.join(left_words)
    right_formatted = '-'.join(right_words)

    # Step 7: Combine with "v"
    return f"{left_formatted}-v-{right_formatted}"
```

### Helper Function: format_reporter()

```python
def format_reporter(reporter_text):
    """
    Remove dots from reporter citation.
    Input: "F.Supp.2d" or "743 F. Supp. 2d 762"
    Output: "FSupp2d"
    """

    # Extract just the reporter abbreviation (no volume/page numbers)
    # Match patterns from reporters_database.json
    for pattern in reporter_patterns:
        match = re.search(pattern, reporter_text)
        if match:
            reporter_abbrev = extract_reporter_abbrev(match.group(0))
            # Remove all dots and spaces from abbreviation
            return reporter_abbrev.replace('.', '').replace(' ', '')

    return "Unpub"  # Fallback
```

---

## Implementation Architecture

### Core Modules

```
file-renamer-caselaw/
├── src/
│   ├── extractors/
│   │   ├── pdf_extractor.py      # PDF text extraction (pdftotext wrapper)
│   │   ├── court_extractor.py    # Court identification
│   │   ├── date_extractor.py     # Year extraction
│   │   ├── case_name_extractor.py # Case name extraction & formatting
│   │   └── reporter_extractor.py # Reporter citation extraction
│   ├── formatters/
│   │   ├── case_name_formatter.py # Case name formatting logic
│   │   └── reporter_formatter.py  # Reporter formatting (remove dots)
│   ├── data/
│   │   ├── courts_mapping.json    # Court database
│   │   └── reporters_database.json # Reporter database
│   ├── renamer.py                 # Main file renaming engine
│   └── cli.py                     # Command-line interface
├── tests/
│   ├── test_extractors.py
│   ├── test_formatters.py
│   └── fixtures/                  # Sample test files
├── sample_files/                  # Original sample files (6 PDFs)
├── analyze_samples.py             # Analysis script (already created)
├── requirements.txt               # Python dependencies
└── README.md
```

### Dependencies

```
# requirements.txt
pypdf2          # PDF handling (backup to pdftotext)
python-dateutil # Date parsing
argparse        # CLI arguments
tabulate        # Pretty table output for preview
colorama        # Colored terminal output
```

### External Tools
- `pdftotext` (already available via Homebrew)
- Future: `docx` or `python-docx` for MS Word support

---

## User Interface Design

### CLI Interface

```bash
# Preview mode (dry run - show what would be renamed)
$ python renamer.py preview sample_files/

# Batch rename
$ python renamer.py rename sample_files/ --output renamed_files/

# Interactive mode (confirm each file)
$ python renamer.py rename sample_files/ --interactive

# Single file
$ python renamer.py preview "Abbott Labs. v. Sandoz, Inc (ND Ill 2010).pdf"

# Generate report
$ python renamer.py report sample_files/ --output report.html
```

### Preview Output Format

```
PREVIEW: Proposed Filename Changes
================================================================================

[1/6] Abbott Labs. v. Sandoz, Inc (ND Ill 2010).pdf
      ↓
      cs_ND-Ill-2010-Abbott-Labs-v-Sandoz-Inc-FSupp2d.pdf

      Extracted:
        Court:    ND-Ill (from PDF ✓)
        Year:     2010 (from PDF ✓)
        Case:     Abbott-Labs-v-Sandoz-Inc (from PDF ✓)
        Reporter: FSupp2d (from PDF ✓)
      Confidence: HIGH

[2/6] Alden v. Me._Attachment1 (1st Cir 1999).pdf
      ↓
      cs_SCOTUS-1999-Alden-v-Maine-US.pdf

      Extracted:
        Court:    SCOTUS (from PDF ✓) [filename said "1st Cir" - CORRECTED]
        Year:     1999 (from PDF ✓)
        Case:     Alden-v-Maine (from PDF ✓)
        Reporter: US (from PDF ✓)
      Confidence: HIGH

...

Summary:
--------
Total files: 6
Successfully extracted: 6 (100%)
High confidence: 6
Medium confidence: 0
Low confidence: 0

Ready to proceed with rename? [y/N]:
```

---

## Testing Strategy

### Unit Tests

1. **Court Extraction Tests**
   - Test each court pattern in courts_mapping.json
   - Test fallback to filename when PDF fails
   - Test edge cases (multi-district courts, county courts)

2. **Year Extraction Tests**
   - Test "Decided:" date parsing
   - Test "Filed:" date parsing
   - Test avoiding margin dates
   - Test fallback to filename year

3. **Case Name Formatting Tests**
   - Test 2-word limit
   - Test special character removal
   - Test first party extraction (multiple parties)
   - Test edge cases: "et al.", "ex rel.", hyphenated names

4. **Reporter Extraction Tests**
   - Test each reporter pattern
   - Test dot removal
   - Test priority selection (multiple reporters)
   - Test fallback to "Unpub"

### Integration Tests

- Run on all 6 sample files
- Verify 100% success rate
- Compare output to expected filenames in FORMATTING_RULES.md

### Edge Case Tests

- Files with no parenthetical
- Files with multiple years
- Very long case names
- Special characters in party names
- Missing reporters
- Ambiguous court names

---

## Future Enhancements

### Phase 2 Features

1. **MS Word Document Support**
   - Extract text from .doc/.docx files
   - Apply same extraction logic

2. **Multiple Output Formats**
   - Allow user to choose from template formats
   - Format A: `cs_[court]-[year]-[case]-[reporter]` (current)
   - Format B: `[year]-[court]-[case]-[reporter]`
   - Format C: Custom template with variables

3. **GUI Application**
   - Drag-and-drop file interface
   - Visual preview with side-by-side comparison
   - Edit/override extracted elements before renaming
   - Progress bar for batch operations

4. **Enhanced Court Database**
   - Add more states beyond GA, NY, CA, TX, FL
   - Add specialized courts (Tax Court, Bankruptcy, etc.)
   - User-editable court mappings

5. **Confidence Scoring**
   - Calculate confidence score per extraction
   - Flag low-confidence extractions for manual review
   - Machine learning to improve extraction over time

6. **Export/Import**
   - Export extraction results to CSV/JSON
   - Import corrections to improve future extractions
   - Batch edit in spreadsheet, re-import

---

## Next Steps - Ready to Build

All planning and analysis is complete. Ready to proceed with implementation:

1. ✅ Requirements gathered
2. ✅ Sample files analyzed
3. ✅ Extraction rules defined
4. ✅ Formatting rules finalized
5. ✅ Court database built
6. ✅ Reporter database built
7. ✅ Algorithm documented
8. ⏭️ **Next: Implement extraction engine**
9. ⏭️ Build CLI interface
10. ⏭️ Write tests
11. ⏭️ Test on sample files
12. ⏭️ Deploy and iterate

**Implementation can begin immediately with all specifications finalized.**
