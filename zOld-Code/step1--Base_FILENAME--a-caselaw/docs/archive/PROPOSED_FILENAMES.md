# Proposed Filename Transformations

**Target Format:** `cs_[jurisdiction/court]-[year]-[shortened case name]-[main reporter citation].pdf`

---

## Sample Files - Before & After

### File 1: Abbott Labs v. Sandoz

**Current Filename:**
```
Abbott Labs. v. Sandoz, Inc (ND Ill 2010).pdf
```

**Extracted Elements:**
- **Court:** ND-Ill (Northern District of Illinois)
  - Source: PDF text - "United States District Court for the Northern District of Illinois, Eastern Division"
- **Year:** 2010
  - Source: PDF text - "May 24, 2010, Decided"
- **Case Name:** Abbott-Labs-v-Sandoz-Inc
  - Source: Filename + PDF validation
- **Reporter:** F.Supp.2d
  - Source: PDF text - "743 F. Supp. 2d 762"
  - Note: Reporter NOT in original filename

**Proposed New Filename:**
```
cs_ND-Ill-2010-Abbott-Labs-v-Sandoz-Inc-F.Supp.2d.pdf
```

---

### File 2: Alden v. Maine

**Current Filename:**
```
Alden v. Me._Attachment1 (1st Cir 1999).pdf
```

**Extracted Elements:**
- **Court:** SCOTUS (Supreme Court of the United States)
  - Source: PDF text - "U.S. SUPREME COURT REPORTS"
  - ⚠️ **Important:** Filename says "1st Cir" but PDF shows it's actually a Supreme Court case!
- **Year:** 1999
  - Source: PDF text - "June 23, 1999"
- **Case Name:** Alden-v-Maine
  - Source: Filename (corrected "Me." to full state name "Maine")
- **Reporter:** U.S.
  - Source: PDF text - "527 US 706"
  - Note: Official U.S. Reports citation

**Proposed New Filename:**
```
cs_SCOTUS-1999-Alden-v-Maine-U.S.pdf
```

**Notes:**
- Removed "_Attachment1" artifact
- Corrected misleading court information from filename

---

### File 3: Allan v. United States

**Current Filename:**
```
Allan v. United States_ 2019 U.S. Dist. LEXIS 123570.pdf
```

**Extracted Elements:**
- **Court:** ED-Va (Eastern District of Virginia)
  - Source: PDF text - "United States District Court for the Eastern District of Virginia, Alexandria Division"
  - Note: Filename doesn't show court, only reporter
- **Year:** 2019
  - Source: PDF text - "July 23, 2019, Decided" (also in filename)
- **Case Name:** Allan-v-US
  - Source: Filename (shortened "United States" to "US")
- **Reporter:** U.S.Dist.LEXIS
  - Source: Filename + PDF confirmation

**Proposed New Filename:**
```
cs_ED-Va-2019-Allan-v-US-U.S.Dist.LEXIS.pdf
```

**Notes:**
- Removed trailing underscore
- Added court identifier from PDF

---

### File 4: Landrum v. Verg Enterprises

**Current Filename:**
```
Landrum v. Verg Enters., LLC (State Ct Fulton County 2024).pdf
```

**Extracted Elements:**
- **Court:** GA-State-Fulton (State Court of Georgia, Fulton County)
  - Source: PDF text - "State Court of Georgia, Fulton County"
- **Year:** 2024
  - Source: PDF text - "September 24, 2024, Decided"
- **Case Name:** Landrum-v-Verg-Enters-LLC
  - Source: Filename (kept LLC designation)
- **Reporter:** Unpub
  - Source: None found - case is unreported
  - Note: Recent state court trial case, likely not published in reporters

**Proposed New Filename:**
```
cs_GA-State-Fulton-2024-Landrum-v-Verg-Enters-LLC-Unpub.pdf
```

**Notes:**
- Standardized court abbreviation
- Used "Unpub" for unreported case

---

### File 5: Adams v. State

**Current Filename:**
```
law - GA COA - Adams v. State (Ga App 2000).pdf
```

**Extracted Elements:**
- **Court:** GA-COA (Georgia Court of Appeals)
  - Source: PDF text - "Court of Appeals of Georgia"
  - Note: Filename prefix "GA COA" was helpful hint
- **Year:** 2000
  - Source: PDF text - "May 10, 2000, Decided"
- **Case Name:** Adams-v-State
  - Source: Filename
- **Reporter:** S.E.2d
  - Source: PDF text - "534 S.E.2d 538"
  - Note: Regional reporter for Georgia

**Proposed New Filename:**
```
cs_GA-COA-2000-Adams-v-State-S.E.2d.pdf
```

**Notes:**
- Removed "law - " prefix
- Added reporter from PDF

---

### File 6: Agee v. State

**Current Filename:**
```
law - GA SC - Agee v. State (Ga 2003).pdf
```

**Extracted Elements:**
- **Court:** GA-SC (Supreme Court of Georgia)
  - Source: PDF text - "Supreme Court of Georgia"
  - Note: Filename prefix "GA SC" was helpful hint
- **Year:** 2003
  - Source: PDF text - "April 29, 2003, Decided"
- **Case Name:** Agee-v-State
  - Source: Filename
- **Reporter:** S.E.2d
  - Source: PDF text - "579 S.E.2d 730"
  - Note: Regional reporter for Georgia

**Proposed New Filename:**
```
cs_GA-SC-2003-Agee-v-State-S.E.2d.pdf
```

**Notes:**
- Removed "law - " prefix
- Added reporter from PDF

---

## Summary Table

| Original Filename | Proposed Filename | Changes Made |
|-------------------|-------------------|--------------|
| Abbott Labs. v. Sandoz, Inc (ND Ill 2010).pdf | cs_ND-Ill-2010-Abbott-Labs-v-Sandoz-Inc-F.Supp.2d.pdf | Added prefix, reporter; standardized format |
| Alden v. Me._Attachment1 (1st Cir 1999).pdf | cs_SCOTUS-1999-Alden-v-Maine-U.S.pdf | **Corrected court**, removed artifact, added reporter |
| Allan v. United States_ 2019 U.S. Dist. LEXIS 123570.pdf | cs_ED-Va-2019-Allan-v-US-U.S.Dist.LEXIS.pdf | Added court, cleaned up reporter format |
| Landrum v. Verg Enters., LLC (State Ct Fulton County 2024).pdf | cs_GA-State-Fulton-2024-Landrum-v-Verg-Enters-LLC-Unpub.pdf | Standardized court code, added reporter (Unpub) |
| law - GA COA - Adams v. State (Ga App 2000).pdf | cs_GA-COA-2000-Adams-v-State-S.E.2d.pdf | Removed prefix, added reporter |
| law - GA SC - Agee v. State (Ga 2003).pdf | cs_GA-SC-2003-Agee-v-State-S.E.2d.pdf | Removed prefix, added reporter |

---

## Key Observations

### Critical Findings

1. **PDF extraction is essential** - 5 out of 6 files required PDF text to get complete information
2. **Filenames can be misleading** - The Alden file showed wrong court in filename
3. **Reporter citations often missing** - 4 out of 6 files lacked reporter in filename but had it in PDF
4. **Artifacts need cleaning** - "_Attachment1", "law - " prefix must be removed

### Extraction Success Rate (from sample)

- **Court identification:** 6/6 (100%) - all correctly identified from PDF
- **Year extraction:** 6/6 (100%) - all correctly identified from PDF
- **Case name:** 6/6 (100%) - all correctly extracted
- **Reporter citation:** 6/6 (100%) - 5 from PDF, 1 marked as Unpub

### Confidence Level

**HIGH CONFIDENCE** - The extraction logic successfully identified all elements for all sample files, with PDF text providing reliable ground truth.

---

## Recommended Next Steps

1. **Implement extraction engine** - Build Python module with extraction functions
2. **Handle edge cases:**
   - Very long case names (truncation rules)
   - Multiple reporters (priority selection)
   - Missing elements (fallback strategies)
   - Special characters in case names
3. **Build user interface:**
   - Preview mode (show proposed renames before executing)
   - Batch processing
   - Confidence scoring per file
   - Manual override options
4. **Testing:**
   - Validate on larger sample set
   - Test MS Word document handling
   - Test various file naming patterns

---

## Questions for User Decision

Before implementing the extraction engine, please decide:

1. **Reporter format in filename:**
   - Current proposal: Keep dots (e.g., `F.Supp.2d`, `S.E.2d`)
   - Alternative A: Remove dots (e.g., `FSupp2d`, `SE2d`)
   - Alternative B: Replace dots with hyphens (e.g., `F-Supp-2d`)

2. **Case name length limits:**
   - Should there be a maximum length?
   - How to handle very long party names?

3. **Multiple party handling:**
   - "A v. B, C, and D" → keep as `A-v-B-C-and-D` or simplify to `A-v-B-et-al`?

4. **Special characters:**
   - Apostrophes: `O'Brien` → `O-Brien` or `OBrien`?
   - Ampersands: `AT&T` → `AT-T`, `ATT`, or `AT-and-T`?
   - Periods in abbreviations: Keep or remove?

5. **Missing reporter fallback:**
   - Current proposal: Use "Unpub" for unreported cases
   - Alternative: Use court code as reporter (e.g., use `GA-State-Fulton` as reporter too)
