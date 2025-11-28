# Final Format Summary - CURRENT VERSION

## Format Evolution

### ✅ Change 1: Bluebook Court Abbreviations
- **Source:** `/sample_files/all_court_abbreviations.md`
- **Implementation:** Using official Bluebook abbreviations with dots/spaces removed
- **Mapping file:** `bluebook_courts_mapping.json`

### ✅ Change 2: Reporter Citations Include Volume & Page
- **New format:** `volume_reporter_page` (e.g., `743_FSupp2d_762`)
- **Previous format:** Just reporter (e.g., `FSupp2d`)

### ✅ Change 3: Double Underscores Between Major Elements
- **New format:** `c.court__year__case__reporter.pdf`
- **Previous format:** `cs_court-year-case-reporter.pdf`
- **Reason:** Improved readability

### ✅ Change 4: Underscores Within Court Codes
- **Examples:** `Ga_Ct_App`, `Ga_St_Ct_Fulton`
- **Previous format:** `GaCtApp`, `GaStCtFulton`

### ✅ Change 5: Federal Court Format Changes
- **Circuit Courts:** `Cir_1`, `Cir_2`, etc. (reversed from `1st_Cir`)
- **District Courts:** `VA_ED`, `ILL_ND`, etc. (format: `STATE_DIRECTION`, state in ALL CAPS)
- **Previous format:** `1st_Cir`, `ND_Ill`, `ED_Va`

### ✅ Change 6: Case Name Formatting
- **Words per party:** 1 (changed from 2)
- **Smart selection:** Surname for persons (3+ words), first word for companies
- **Examples:** "JOHN H. ALDEN" → "ALDEN", "Abbott Labs" → "Abbott"

---

## Final Filename Format

```
c.[court]__[year]__[case-name]__[volume_reporter_page].pdf
```

**Components:**
1. **Prefix:** `c.` (single-character caselaw prefix for brevity)
2. **Court:** Bluebook abbreviation with underscores (federal courts use STATE_DIRECTION or Cir_NUMBER format)
3. **Year:** 4-digit decision year
4. **Case Name:** 1 word per party, smart selection (surname/first word), hyphenated
5. **Reporter:** `volume_reporter_page` format, dots removed

---

## Updated Sample Filenames

### File 1: Abbott Labs v. Sandoz
```
BEFORE: Abbott Labs. v. Sandoz, Inc (ND Ill 2010).pdf

AFTER:  c.ILL_ND__2010__Abbott-v-Sandoz__743_FSupp2d_762.pdf
```

**Extracted:**
- Court: Northern District of Illinois → `ILL_ND` (STATE_DIRECTION format, state in caps)
- Year: 2010
- Case: Abbott-v-Sandoz (smart selection: "Abbott Labs" → "Abbott", "Sandoz, Inc" → "Sandoz")
- Reporter: 743 F. Supp. 2d 762 → `743_FSupp2d_762`

**Notes:**
- Timestamp fragment "AM Z" from download date filtered out
- Company name handling: first word, not surname logic

---

### File 2: Alden v. Maine
```
BEFORE: Alden v. Me._Attachment1 (1st Cir 1999).pdf

AFTER:  c.US__1999__ALDEN-v-MAINE__527_US_706.pdf
```

**Extracted:**
- Court: United States Supreme Court → `US`
- Year: 1999
- Case: ALDEN-v-MAINE (surname extraction: "JOHN H. ALDEN" → "ALDEN", "Me." expanded to "MAINE")
- Reporter: 527 U.S. 706 → `527_US_706`

**Notes:**
- Filename said "1st Cir" but PDF shows SCOTUS - corrected!
- Multi-line case caption: "v" on separate line between parties
- "_Attachment1" artifact removed

---

### File 3: Allan v. United States
```
BEFORE: Allan v. United States_ 2019 U.S. Dist. LEXIS 123570.pdf

AFTER:  c.VA_ED__2019__Allan-v-United-States__USDistLEXIS_123570.pdf
```

**Extracted:**
- Court: Eastern District of Virginia → `VA_ED` (STATE_DIRECTION format)
- Year: 2019
- Case: Allan-v-United-States (geographic name preserved: both words kept)
- Reporter: U.S. Dist. LEXIS 123570 → `USDistLEXIS_123570` (no volume number)

---

### File 4: Landrum v. Verg Enterprises
```
BEFORE: Landrum v. Verg Enters., LLC (State Ct Fulton County 2024).pdf

AFTER:  c.Ga_St_Ct_Fulton__2024__Landrum-v-Verg__2024_GaStateLEXIS_4558.pdf
```

**Extracted:**
- Court: State Court of Georgia, Fulton County → `Ga_St_Ct_Fulton` (custom format for trial courts)
- Year: 2024
- Case: Landrum-v-Verg (1 word per party)
- Reporter: 2024 Ga. State LEXIS 4558 → `2024_GaStateLEXIS_4558`

---

### File 5: Adams v. State
```
BEFORE: law - GA COA - Adams v. State (Ga App 2000).pdf

AFTER:  c.Ga_Ct_App__2000__Adams-v-State__534_SE2d_538.pdf
```

**Extracted:**
- Court: Georgia Court of Appeals → `Ga_Ct_App`
- Year: 2000
- Case: Adams-v-State
- Reporter: 534 S.E.2d 538 → `534_SE2d_538`

**Notes:**
- "law - GA COA -" prefix removed

---

### File 6: Agee v. State
```
BEFORE: law - GA SC - Agee v. State (Ga 2003).pdf

AFTER:  c.Ga__2003__Agee-v-State__579_SE2d_730.pdf
```

**Extracted:**
- Court: Georgia Supreme Court → `Ga`
- Year: 2003
- Case: Agee-v-State
- Reporter: 579 S.E.2d 730 → `579_SE2d_730`

**Notes:**
- "law - GA SC -" prefix removed

---

## Complete Summary Table

| # | Original Filename | Final Filename |
|---|-------------------|----------------|
| 1 | Abbott Labs. v. Sandoz, Inc (ND Ill 2010).pdf | c.ILL_ND__2010__Abbott-v-Sandoz__743_FSupp2d_762.pdf |
| 2 | Alden v. Me._Attachment1 (1st Cir 1999).pdf | c.US__1999__ALDEN-v-MAINE__527_US_706.pdf |
| 3 | Allan v. United States_ 2019 U.S. Dist. LEXIS 123570.pdf | c.VA_ED__2019__Allan-v-United-States__USDistLEXIS_123570.pdf |
| 4 | Landrum v. Verg Enters., LLC (State Ct Fulton County 2024).pdf | c.Ga_St_Ct_Fulton__2024__Landrum-v-Verg__2024_GaStateLEXIS_4558.pdf |
| 5 | law - GA COA - Adams v. State (Ga App 2000).pdf | c.Ga_Ct_App__2000__Adams-v-State__534_SE2d_538.pdf |
| 6 | law - GA SC - Agee v. State (Ga 2003).pdf | c.Ga__2003__Agee-v-State__579_SE2d_730.pdf |

---

## Bluebook Court Code Examples

### Federal Supreme Court
- U.S. → `US` or `SCOTUS`

### Federal Circuit Courts
- 1st Cir. → `Cir_1`
- 2d Cir. → `Cir_2`
- 3d Cir. → `Cir_3`
- 4th Cir. → `Cir_4`
- 5th Cir. → `Cir_5`
- 6th Cir. → `Cir_6`
- 7th Cir. → `Cir_7`
- 8th Cir. → `Cir_8`
- 9th Cir. → `Cir_9`
- 10th Cir. → `Cir_10`
- 11th Cir. → `Cir_11`
- D.C. Cir. → `Cir_DC`
- Fed. Cir. → `Cir_Fed`

### Federal District Courts (STATE_DIRECTION format, state in ALL CAPS)
- N.D. Ill. → `ILL_ND`
- E.D. Va. → `VA_ED`
- S.D.N.Y. → `NY_SD`
- D. Mass. → `MASS_D`
- C.D. Cal. → `CAL_CD`
- W.D. Tex. → `TEX_WD`

### State Supreme Courts
- Ga. → `Ga`
- Cal. → `Cal`
- Tex. → `Tex`
- N.Y. → `NY` (Court of Appeals - highest court in NY)

### State Appellate Courts
- Ga. Ct. App. → `Ga_Ct_App`
- Cal. Ct. App. → `Cal_Ct_App`
- N.Y. App. Div. → `NY_App_Div`
- Tex. App. → `Tex_App`

### State Trial Courts
- State Court of Georgia, Fulton County → `Ga_St_Ct_Fulton`

---

## Reporter Citation Format Examples

### Federal Reporters
| PDF Citation | Filename Format |
|--------------|-----------------|
| 743 F. Supp. 2d 762 | 743_FSupp2d_762 |
| 456 F.3d 789 | 456_F3d_789 |
| 123 F.4th 456 | 123_F4th_456 |
| 78 S. Ct. 901 | 78_SCt_901 |
| 527 U.S. 706 | 527_US_706 |
| 527 US 706 (no periods) | 527_US_706 |

### Regional Reporters
| PDF Citation | Filename Format |
|--------------|-----------------|
| 534 S.E.2d 538 | 534_SE2d_538 |
| 789 N.E.3d 123 | 789_NE3d_123 |
| 456 P.3d 789 | 456_P3d_789 |
| 234 S.W.3d 567 | 234_SW3d_567 |

### State Reporters
| PDF Citation | Filename Format |
|--------------|-----------------|
| 345 Ga. 678 | 345_Ga_678 |
| 234 Ga. App. 456 | 234_GaApp_456 |
| 567 Cal. 890 | 567_Cal_890 |
| 123 N.Y.S.3d 456 | 123_NYS3d_456 |

### Online Databases
| PDF Citation | Filename Format |
|--------------|-----------------|
| U.S. Dist. LEXIS 123570 | USDistLEXIS_123570 |
| 2019 WL 3426891 | 2019_WL_3426891 |
| 2024 Ga. State LEXIS 4558 | 2024_GaStateLEXIS_4558 |

### Unreported Cases
| Status | Filename Format |
|--------|-----------------|
| No reporter citation | Unpub |

---

## Extraction Rules Summary

### 1. Court Extraction
- **Primary source:** PDF text (official court name)
- **Lookup:** Match to Bluebook abbreviation in `bluebook_courts_mapping.json`
- **Format:**
  - Federal circuits: `Cir_NUMBER` (e.g., `Cir_1`)
  - Federal districts: `STATE_DIRECTION` with state in ALL CAPS (e.g., `VA_ED`)
  - State courts: Bluebook with underscores (e.g., `Ga_Ct_App`)
- **Fallback:** Parse filename hints if PDF fails

### 2. Year Extraction
- **Primary source:** PDF "Decided:" date
- **Fallback:** PDF "Filed:" date, then filename
- **Avoid:** Margin dates (download dates)
- **Pattern matching:** Handles both "Decided: Date" and "Date, Decided" formats

### 3. Case Name Formatting
- **Extract:** From PDF case caption or filename
- **Multi-line handling:** Detects "v" on separate line between parties
- **Party selection:** First party only (before comma)
- **Word selection:** 1 word per party with smart selection:
  - Person names (3+ words): Take surname (e.g., "JOHN H. ALDEN" → "ALDEN")
  - Company names (2 words): Take first word (e.g., "Abbott Labs" → "Abbott")
  - Geographic names (2 words starting with direction): Keep both (e.g., "United States")
  - Single names: Use as-is
- **Clean:** Remove special characters (.,'"&();:), "et al."
- **Filter:** Remove timestamp fragments ("AM Z", "PM Z" from download dates)
- **Join:** Hyphenate words

### 4. Reporter Citation Extraction
- **Primary source:** PDF text (prioritizes first 1000 chars to avoid body citations)
- **Extract:** Volume number, reporter abbreviation, page number
- **Format:** `volume_reporter_page`
- **Clean:** Remove dots and spaces from reporter
- **Pattern support:** Matches both "U.S." and "US" (with/without periods)
- **LEXIS handling:** Citations without volume numbers (e.g., `USDistLEXIS_123570`)
- **Fallback:** `Unpub` if no citation found

---

## Key References

### Data Files
1. ✅ `bluebook_courts_mapping.json` - 200+ courts with Bluebook codes
2. ✅ `reporters_database.json` - 100+ reporter patterns
3. ✅ `TEST_RESULTS.md` - Complete test results with all 6 files
4. ✅ `FINAL_FORMAT_SUMMARY.md` - This document
5. ✅ `README.md` - User guide and quick start

### Implementation Modules
1. ✅ `src/extractors/pdf_extractor.py` - PDF text extraction
2. ✅ `src/extractors/court_extractor.py` - Court identification
3. ✅ `src/extractors/date_extractor.py` - Year extraction
4. ✅ `src/extractors/reporter_extractor.py` - Reporter citation extraction
5. ✅ `src/formatters/case_name_formatter.py` - Case name parsing & formatting
6. ✅ `src/renamer.py` - Main coordination engine
7. ✅ `src/cli.py` - Command-line interface

### Original Source Files
- `/sample_files/all_court_abbreviations.md` - Bluebook court abbreviations
- `/sample_files/*.pdf` - 6 sample files for testing

---

## Test Results Summary

### All 6 Files Successfully Processed
- ✅ 100% success rate
- ✅ 100% HIGH confidence
- ✅ 100% elements extracted from PDF text (not filename fallback)

### Edge Cases Successfully Handled
1. ✅ Multi-line case captions (Alden)
2. ✅ Surname extraction for person names (Alden)
3. ✅ Company name handling (Abbott Labs)
4. ✅ Geographic name preservation (United States)
5. ✅ Timestamp fragment filtering (Abbott Labs)
6. ✅ Header-first reporter extraction (Alden)
7. ✅ State trial court identification (Landrum)
8. ✅ LEXIS citations with/without volume
9. ✅ Filename artifact removal
10. ✅ Court misidentification correction (Alden filename vs PDF)

---

## Production Ready

The tool is fully functional and production-ready:

```bash
# Preview mode (dry run)
python3 src/cli.py preview sample_files/

# Interactive rename
python3 src/cli.py rename sample_files/ --interactive

# Batch rename
python3 src/cli.py rename sample_files/
```

All specifications finalized and tested:
- ✅ Court abbreviations (Bluebook with underscores)
- ✅ Federal court formats (Cir_NUMBER, STATE_DIRECTION)
- ✅ Reporter citations (volume_reporter_page)
- ✅ Case name formatting (1 word per party, smart selection)
- ✅ Double underscores between major elements
- ✅ All extraction priorities and fallbacks
- ✅ All 6 sample files successfully processed
