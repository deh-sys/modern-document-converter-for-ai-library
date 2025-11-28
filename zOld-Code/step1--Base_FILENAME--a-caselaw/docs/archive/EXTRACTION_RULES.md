# Caselaw Filename Extraction Rules

**Target Format:** `cs_[jurisdiction/court]-[year]-[shortened case name]-[main reporter citation]`

## Sample Analysis Summary

### Key Findings

1. **Filenames are often incomplete** - Reporter citations frequently missing from filenames but present in PDFs
2. **Filename court info can be misleading** - e.g., "Alden" shows "(1st Cir 1999)" but is actually a Supreme Court case
3. **PDF extraction is reliable** - All PDFs contained accurate court, date, and case name information
4. **Reporter citations are critical** - 4 out of 6 files had reporter citations in PDF but not in filename
5. **Prefixes need stripping** - "law - " prefix in some files
6. **Artifacts need cleaning** - "_Attachment1" and similar suffixes

### Sample File Details

| Original Filename | Court (PDF) | Year | Reporter (PDF) | Notes |
|-------------------|-------------|------|----------------|-------|
| Abbott Labs. v. Sandoz, Inc (ND Ill 2010) | ND Ill | 2010 | 743 F. Supp. 2d 762 | Reporter in PDF only |
| Alden v. Me._Attachment1 (1st Cir 1999) | **SCOTUS** | 1999 | 527 US 706 | Filename says 1st Cir but is SCOTUS! |
| Allan v. United States_ 2019 U.S. Dist. LEXIS 123570 | ED Va | 2019 | U.S. Dist. LEXIS 123570 | LEXIS citation |
| Landrum v. Verg Enters., LLC (State Ct Fulton County 2024) | State Ct GA, Fulton | 2024 | (none) | Unreported case |
| law - GA COA - Adams v. State (Ga App 2000) | GA COA | 2000 | 534 S.E.2d 538 | Has prefix |
| law - GA SC - Agee v. State (Ga 2003) | GA SC | 2003 | 579 S.E.2d 730 | Has prefix |

---

## Extraction Rules by Element

### 1. JURISDICTION/COURT

**Priority Order:**
1. Extract from PDF court name (most reliable)
2. Fall back to filename parenthetical if PDF fails
3. Fall back to filename prefix hint (e.g., "GA COA")

**Standardization Mappings:**

#### Federal Courts
- Supreme Court → `SCOTUS`
- Circuit Courts → `1st-Cir`, `2d-Cir`, `3d-Cir`, `4th-Cir`, ..., `11th-Cir`, `DC-Cir`, `Fed-Cir`
- District Courts → `[District]-[State]` format:
  - Northern District of Illinois → `ND-Ill`
  - Eastern District of Virginia → `ED-Va`
  - Southern District of New York → `SD-NY`
  - District of [State] (single district) → `D-[State]` (e.g., `D-Conn`, `D-Mass`)

#### State Courts
- Format: `[State]-[Court Level]-[Optional County]`
- Georgia Supreme Court → `GA-SC`
- Georgia Court of Appeals → `GA-COA`
- State Court of Georgia, Fulton County → `GA-State-Fulton`
- New York Court of Appeals → `NY-CA` (highest court)
- New York Supreme Court → `NY-Sup-[County]` (trial court)

**Recognition Patterns:**

Federal:
- `UNITED STATES DISTRICT COURT` → extract district and state
- `COURT OF APPEALS` → extract circuit number
- `SUPREME COURT OF THE UNITED STATES` / `U.S. SUPREME COURT` → `SCOTUS`

State (Georgia examples):
- `Supreme Court of Georgia` → `GA-SC`
- `Court of Appeals of Georgia` → `GA-COA`
- `State Court of Georgia, [County] County` → `GA-State-[County]`
- `Superior Court of [County] County, Georgia` → `GA-Super-[County]`

**Special Cases:**
- If court cannot be determined → use `UNKNOWN`
- Multi-jurisdictional cases → use primary court listed

---

### 2. YEAR OF DECISION

**Priority Order:**
1. Extract from PDF "Decided:" date (most reliable)
2. Extract from PDF "Filed:" date if no "Decided:" date
3. Fall back to year in filename parenthetical
4. Fall back to year in LEXIS/WL citation

**Extraction Strategy:**
- Look for: `Decided: [Month] [Day], [YEAR]` or `Filed: [Month] [Day], [YEAR]`
- Parse month-day-year format and extract 4-digit year
- **IMPORTANT:** Ignore dates in margins/headers that appear alone without context words
- Validate: Year must be between 1700-2025

**Edge Cases:**
- Multiple dates → prefer "Decided" over "Filed"
- Year in filename conflicts with PDF → **trust PDF**

---

### 3. SHORTENED CASE NAME

**Priority Order:**
1. Extract from PDF case caption (most accurate formatting)
2. Fall back to filename case name

**Extraction Rules:**
1. Get text before " v. " or " vs. " (case insensitive)
2. Get text after " v. " / " vs. " up to next comma or end
3. Clean up:
   - Remove "et al."
   - Keep corporate designators but standardize: "Inc.", "LLC", "Corp.", "Ltd."
   - Replace "United States" with "US"
   - Remove trailing descriptors after commas (unless part of party name)

**Shortening Rules:**
1. First party: Keep up to first 3 words (or until comma/designation)
2. Keep " v " (single space, no periods)
3. Second party: Keep up to first 3 words (or until comma/designation)
4. Replace spaces with hyphens
5. Remove periods EXCEPT in designators (Inc., LLC, etc.)
6. Remove apostrophes or replace with hyphens

**Examples:**
- `Abbott Labs. v. Sandoz, Inc` → `Abbott-Labs-v-Sandoz-Inc`
- `Alden v. Maine` (not "Me.") → `Alden-v-Maine`
- `Allan v. United States` → `Allan-v-US`
- `Landrum v. Verg Enters., LLC` → `Landrum-v-Verg-Enters-LLC`
- `Adams v. State` → `Adams-v-State`

---

### 4. MAIN REPORTER CITATION

**Priority Order:**
1. Extract from PDF text (most reliable)
2. Fall back to filename if contains reporter pattern
3. If no reporter found → use court abbreviation or "Unpub"

**Reporter Database (by preference):**

#### U.S. Supreme Court
1. `U.S.` - United States Reports (official)
2. `S.Ct.` - Supreme Court Reporter
3. `L.Ed.` or `L.Ed.2d` - Lawyers' Edition

#### Federal Courts of Appeal
1. `F.` / `F.2d` / `F.3d` / `F.4th` - Federal Reporter
2. `Fed.Appx.` - Federal Appendix (unpublished)

#### Federal District Courts
1. `F.Supp.` / `F.Supp.2d` / `F.Supp.3d` - Federal Supplement
2. `F.R.D.` - Federal Rules Decisions

#### Regional Reporters (state cases)
1. `S.E.` / `S.E.2d` - South Eastern Reporter (GA, NC, SC, VA, WV)
2. `N.E.` / `N.E.2d` / `N.E.3d` - North Eastern Reporter
3. `P.` / `P.2d` / `P.3d` - Pacific Reporter
4. `A.` / `A.2d` / `A.3d` - Atlantic Reporter
5. `S.W.` / `S.W.2d` / `S.W.3d` - South Western Reporter
6. `N.W.` / `N.W.2d` - North Western Reporter
7. `So.` / `So.2d` / `So.3d` - Southern Reporter

#### State-Specific Reporters
- `Ga.` - Georgia Reports (Supreme Court)
- `Ga.App.` - Georgia Appeals Reports
- `N.Y.S.` / `N.Y.S.2d` / `N.Y.S.3d` - New York Supplement
- `Cal.Rptr.` / `Cal.Rptr.2d` / `Cal.Rptr.3d` - California Reporter

#### Online Databases
1. `LEXIS` - LexisNexis (format: "U.S. Dist. LEXIS" or just "LEXIS")
2. `WL` - Westlaw
3. `Unpub` - Unpublished/unreported

**Extraction Patterns:**
- `\d+\s+F\.\s*Supp\.\s*\d*d?\s+\d+` → extract "F.Supp.2d" or "F.Supp.3d"
- `\d+\s+F\.\s*\d*d\s+\d+` → extract "F.3d" or "F.4th"
- `\d+\s+S\.E\.\s*\d*d\s+\d+` → extract "S.E.2d"
- `U\.S\.\s+Dist\.\s+LEXIS` → extract "US-Dist-LEXIS"
- If volume + reporter + page found → keep only reporter abbreviation

**Standardization for Filename:**
- Replace periods with nothing EXCEPT maintain clarity: `F.Supp.2d` → `FSupp2d`
- Or keep periods: `F.Supp.2d` (may be clearer)
- **Recommendation:** Keep dots but no spaces: `F.Supp.2d`, `S.E.2d`, `U.S.Dist.LEXIS`

**If No Reporter Found:**
- Check if case is recent (2020+) → likely `Unpub`
- State court trial level → likely `Unpub`
- Otherwise → use court abbreviation as proxy

---

## Extraction Algorithm

### Step-by-Step Process

```
1. PREPROCESS
   - Strip prefix ("law - ", etc.)
   - Strip artifacts ("_Attachment1", etc.)
   - Extract filename components as hints

2. EXTRACT FROM PDF (first 2 pages, avoid margins)
   - Find court name (look for official court name patterns)
   - Find decision/filed date (look for labeled dates)
   - Find case caption (look for "v." pattern)
   - Find reporter citation (look for reporter patterns)

3. NORMALIZE EACH ELEMENT
   - Court → standardized abbreviation (use mapping)
   - Year → 4-digit year from decision date
   - Case name → shortened format with hyphens
   - Reporter → standardized abbreviation (use database)

4. CONSTRUCT FILENAME
   - Format: cs_[court]-[year]-[case_name]-[reporter].pdf
   - Example: cs_ND-Ill-2010-Abbott-Labs-v-Sandoz-Inc-F.Supp.2d.pdf

5. VALIDATE
   - Check all required elements present
   - Flag any extractions with low confidence
   - Provide alternative suggestions if ambiguous
```

---

## Example Transformations

### File 1: Abbott Labs
- **Original:** `Abbott Labs. v. Sandoz, Inc (ND Ill 2010).pdf`
- **Extracted:**
  - Court: ND-Ill (from PDF: "United States District Court for the Northern District of Illinois")
  - Year: 2010 (from PDF: "May 24, 2010, Decided")
  - Case: Abbott-Labs-v-Sandoz-Inc
  - Reporter: F.Supp.2d (from PDF: "743 F. Supp. 2d 762")
- **Result:** `cs_ND-Ill-2010-Abbott-Labs-v-Sandoz-Inc-F.Supp.2d.pdf`

### File 2: Alden
- **Original:** `Alden v. Me._Attachment1 (1st Cir 1999).pdf`
- **Extracted:**
  - Court: SCOTUS (from PDF: "U.S. SUPREME COURT REPORTS", **NOT** "1st Cir" from filename!)
  - Year: 1999 (from PDF: "June 23, 1999")
  - Case: Alden-v-Maine (correct "Me." to "Maine")
  - Reporter: U.S. (from PDF: "527 US 706")
- **Result:** `cs_SCOTUS-1999-Alden-v-Maine-U.S.pdf`

### File 3: Allan
- **Original:** `Allan v. United States_ 2019 U.S. Dist. LEXIS 123570.pdf`
- **Extracted:**
  - Court: ED-Va (from PDF: "Eastern District of Virginia")
  - Year: 2019 (from PDF: "July 23, 2019, Decided")
  - Case: Allan-v-US
  - Reporter: U.S.Dist.LEXIS (from filename and confirmed in PDF)
- **Result:** `cs_ED-Va-2019-Allan-v-US-U.S.Dist.LEXIS.pdf`

### File 4: Landrum
- **Original:** `Landrum v. Verg Enters., LLC (State Ct Fulton County 2024).pdf`
- **Extracted:**
  - Court: GA-State-Fulton (from PDF: "State Court of Georgia, Fulton County")
  - Year: 2024 (from PDF: "September 24, 2024, Decided")
  - Case: Landrum-v-Verg-Enters-LLC
  - Reporter: Unpub (no reporter found)
- **Result:** `cs_GA-State-Fulton-2024-Landrum-v-Verg-Enters-LLC-Unpub.pdf`

### File 5: Adams
- **Original:** `law - GA COA - Adams v. State (Ga App 2000).pdf`
- **Extracted:**
  - Court: GA-COA (from PDF: "Court of Appeals of Georgia")
  - Year: 2000 (from PDF: "May 10, 2000, Decided")
  - Case: Adams-v-State
  - Reporter: S.E.2d (from PDF: "534 S.E.2d 538")
- **Result:** `cs_GA-COA-2000-Adams-v-State-S.E.2d.pdf`

### File 6: Agee
- **Original:** `law - GA SC - Agee v. State (Ga 2003).pdf`
- **Extracted:**
  - Court: GA-SC (from PDF: "Supreme Court of Georgia")
  - Year: 2003 (from PDF: "April 29, 2003, Decided")
  - Case: Agee-v-State
  - Reporter: S.E.2d (from PDF: "579 S.E.2d 730")
- **Result:** `cs_GA-SC-2003-Agee-v-State-S.E.2d.pdf`

---

## Edge Cases & Decisions Needed

### Questions for User:

1. **Reporter citation format in filename:**
   - Option A: Keep dots: `F.Supp.2d`, `S.E.2d`
   - Option B: Remove dots: `FSupp2d`, `SE2d`
   - Option C: Use hyphens: `F-Supp-2d`, `S-E-2d`
   - **Recommendation:** Keep dots (most recognizable)

2. **Case name length limit:**
   - Current rule: First 3 words per party
   - Should we limit total length? (e.g., max 40 characters)
   - How to handle very long party names?

3. **Missing reporter handling:**
   - Option A: Use `Unpub` for unreported cases
   - Option B: Use court abbreviation as proxy (e.g., `ND-Ill`)
   - Option C: Leave empty or use placeholder
   - **Recommendation:** Use `Unpub`

4. **Multiple parties handling:**
   - "A v. B, C, and D" → `A-v-B-et-al`?
   - Or keep first two: `A-v-B-C`?

5. **Special characters:**
   - Apostrophes: `O'Brien` → `OBrien` or `O-Brien`?
   - Ampersands: `AT&T` → `AT-T` or `ATT`?
   - Numbers: `123 Corp.` → keep as is?

6. **Court abbreviation conflicts:**
   - Some courts have common abbreviations (e.g., "ED-NY" could be Eastern District New York or...)
   - Do we need more specific codes?

---

## Next Steps

1. Build comprehensive court mapping database (JSON)
2. Build reporter database (JSON)
3. Implement PDF text extraction with margin avoidance
4. Implement extraction functions for each element
5. Test on sample files and validate results
6. Build user interface for batch renaming with preview
