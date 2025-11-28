# UPDATED Formatting Rules for Caselaw Filenames

**Target Format:** `cs_[bluebook-court]-[year]-[case-name]-[volume_reporter_page].pdf`

---

## UPDATED: Key Changes from Previous Version

### Change 1: Bluebook Court Abbreviations
Now using official Bluebook abbreviations (with dots removed for filenames)

**Examples:**
- Northern District of Illinois: `NDIll` (Bluebook: "N.D. Ill." → dots removed)
- Eastern District of Virginia: `EDVa` (Bluebook: "E.D. Va." → dots removed)
- Supreme Court of Georgia: `Ga` (Bluebook: "Ga." → dot removed)
- Georgia Court of Appeals: `GaCtApp` (Bluebook: "Ga. Ct. App." → dots/spaces removed)
- Supreme Court of the United States: `US` (Bluebook: no abbreviation needed, use "U.S.")

### Change 2: Reporter Citation Format - NOW INCLUDES VOLUME AND PAGE
**New Format:** `volume_reporter_page`

**Examples:**
- `743 F. Supp. 2d 762` → `743_FSupp2d_762`
- `534 S.E.2d 538` → `534_SE2d_538`
- `527 U.S. 706` → `527_US_706`
- `U.S. Dist. LEXIS 123570` → `USDistLEXIS_123570` (LEXIS number becomes "page")

---

## Updated Bluebook Court Abbreviations (Dots Removed for Filenames)

### Federal Courts

#### Supreme Court
- **Bluebook:** (no abbreviation) or "U.S."
- **Filename:** `US`

#### Courts of Appeals
- **Bluebook:** "1st Cir.", "2d Cir.", "3d Cir.", etc.
- **Filename:** `1stCir`, `2dCir`, `3dCir`, `4thCir`, ..., `11thCir`, `DCCir`, `FedCir`

#### District Courts
Format: `[Direction][State]` (removing dots and spaces)

Examples:
- **Bluebook:** "N.D. Ill."
- **Filename:** `NDIll`

- **Bluebook:** "E.D. Va."
- **Filename:** `EDVa`

- **Bluebook:** "S.D.N.Y."
- **Filename:** `SDNY`

- **Bluebook:** "D. Mass." (single district)
- **Filename:** `DMass`

Full mapping:
- N.D. = `ND`
- S.D. = `SD`
- E.D. = `ED`
- W.D. = `WD`
- M.D. = `MD` (Middle District)
- C.D. = `CD` (Central District)
- D. = `D` (single district states)

### State Courts

#### Format Rules
State court abbreviations follow Bluebook, with dots and spaces removed:

**Supreme Courts:**
- **Bluebook:** "Ga.", "Cal.", "Tex.", "Fla.", etc.
- **Filename:** `Ga`, `Cal`, `Tex`, `Fla`

**Appellate Courts:**
- **Bluebook:** "Ga. Ct. App."
- **Filename:** `GaCtApp`

- **Bluebook:** "Cal. Ct. App."
- **Filename:** `CalCtApp`

- **Bluebook:** "N.Y. App. Div." (New York's intermediate court)
- **Filename:** `NYAppDiv`

**Trial Courts (when needed):**
- State trial courts are generally NOT listed in Bluebook abbreviations
- For trial courts like "State Court of Georgia, Fulton County":
  - Create descriptive abbreviation: `GaStateFulton` or `GaStCtFulton`
  - Prioritize clarity and consistency

---

## Reporter Citation Extraction & Formatting

### Extraction Pattern

**Goal:** Extract volume, reporter, and page from PDF text

**Common Citation Formats:**
1. `743 F. Supp. 2d 762` → Volume: 743, Reporter: F. Supp. 2d, Page: 762
2. `534 S.E.2d 538` → Volume: 534, Reporter: S.E.2d, Page: 538
3. `527 U.S. 706` → Volume: 527, Reporter: U.S., Page: 706
4. `U.S. Dist. LEXIS 123570` → Volume: (none), Reporter: U.S. Dist. LEXIS, Page: 123570

**Regex Pattern:**
```regex
(?:(\d+)\s+)?                           # Optional volume number
((?:F\.|U\.S\.|S\.E\.|N\.E\.|etc)\S*)  # Reporter abbreviation
\s+(\d+)                                # Page number
```

### Formatting Rules

1. **Extract volume, reporter abbreviation, and page number**
2. **Remove all dots and spaces from reporter**
3. **Join with underscores:** `volume_reporter_page`

**Examples:**

| PDF Text | Volume | Reporter | Page | Filename Format |
|----------|--------|----------|------|-----------------|
| 743 F. Supp. 2d 762 | 743 | F. Supp. 2d | 762 | `743_FSupp2d_762` |
| 534 S.E.2d 538 | 534 | S.E.2d | 538 | `534_SE2d_538` |
| 527 U.S. 706 | 527 | U.S. | 706 | `527_US_706` |
| 579 S.E.2d 730 | 579 | S.E.2d | 730 | `579_SE2d_730` |
| U.S. Dist. LEXIS 123570 | - | U.S. Dist. LEXIS | 123570 | `USDistLEXIS_123570` |

**Special Cases:**

- **LEXIS citations:** No volume number, so format is `USDistLEXIS_123570`
- **Westlaw citations:** `2019 WL 3426891` → `2019_WL_3426891`
- **Slip opinions (no reporter):** Use `Unpub` → no volume/page, so just `Unpub`

---

## Updated Sample Transformations

### File 1: Abbott Labs v. Sandoz

**Original:** `Abbott Labs. v. Sandoz, Inc (ND Ill 2010).pdf`

**Extracted Elements:**
- **Court:** Northern District of Illinois
  - Bluebook: "N.D. Ill."
  - Filename: `NDIll`
- **Year:** 2010
- **Case Name:** Abbott-Labs-v-Sandoz-Inc
- **Reporter from PDF:** "743 F. Supp. 2d 762"
  - Volume: 743
  - Reporter: F. Supp. 2d → `FSupp2d`
  - Page: 762
  - Format: `743_FSupp2d_762`

**NEW PROPOSED FILENAME:**
```
cs_NDIll-2010-Abbott-Labs-v-Sandoz-Inc-743_FSupp2d_762.pdf
```

---

### File 2: Alden v. Maine

**Original:** `Alden v. Me._Attachment1 (1st Cir 1999).pdf`

**Extracted Elements:**
- **Court:** Supreme Court of the United States
  - Bluebook: (no abbrev) → use "U.S."
  - Filename: `US`
- **Year:** 1999
- **Case Name:** Alden-v-Maine
- **Reporter from PDF:** "527 US 706" (from "527 US 706")
  - Volume: 527
  - Reporter: U.S. → `US`
  - Page: 706
  - Format: `527_US_706`

**NEW PROPOSED FILENAME:**
```
cs_US-1999-Alden-v-Maine-527_US_706.pdf
```

---

### File 3: Allan v. United States

**Original:** `Allan v. United States_ 2019 U.S. Dist. LEXIS 123570.pdf`

**Extracted Elements:**
- **Court:** Eastern District of Virginia
  - Bluebook: "E.D. Va."
  - Filename: `EDVa`
- **Year:** 2019
- **Case Name:** Allan-v-United-States
- **Reporter from PDF:** "U.S. Dist. LEXIS 123570"
  - Volume: (none)
  - Reporter: U.S. Dist. LEXIS → `USDistLEXIS`
  - Page: 123570
  - Format: `USDistLEXIS_123570`

**NEW PROPOSED FILENAME:**
```
cs_EDVa-2019-Allan-v-United-States-USDistLEXIS_123570.pdf
```

---

### File 4: Landrum v. Verg Enterprises

**Original:** `Landrum v. Verg Enters., LLC (State Ct Fulton County 2024).pdf`

**Extracted Elements:**
- **Court:** State Court of Georgia, Fulton County
  - No Bluebook abbreviation (trial court)
  - Filename: `GaStCtFulton` (descriptive)
- **Year:** 2024
- **Case Name:** Landrum-v-Verg-Enters
- **Reporter:** None found (unreported)
  - Format: `Unpub`

**NEW PROPOSED FILENAME:**
```
cs_GaStCtFulton-2024-Landrum-v-Verg-Enters-Unpub.pdf
```

---

### File 5: Adams v. State

**Original:** `law - GA COA - Adams v. State (Ga App 2000).pdf`

**Extracted Elements:**
- **Court:** Court of Appeals of Georgia
  - Bluebook: "Ga. Ct. App."
  - Filename: `GaCtApp`
- **Year:** 2000
- **Case Name:** Adams-v-State
- **Reporter from PDF:** "534 S.E.2d 538"
  - Volume: 534
  - Reporter: S.E.2d → `SE2d`
  - Page: 538
  - Format: `534_SE2d_538`

**NEW PROPOSED FILENAME:**
```
cs_GaCtApp-2000-Adams-v-State-534_SE2d_538.pdf
```

---

### File 6: Agee v. State

**Original:** `law - GA SC - Agee v. State (Ga 2003).pdf`

**Extracted Elements:**
- **Court:** Supreme Court of Georgia
  - Bluebook: "Ga."
  - Filename: `Ga`
- **Year:** 2003
- **Case Name:** Agee-v-State
- **Reporter from PDF:** "579 S.E.2d 730"
  - Volume: 579
  - Reporter: S.E.2d → `SE2d`
  - Page: 730
  - Format: `579_SE2d_730`

**NEW PROPOSED FILENAME:**
```
cs_Ga-2003-Agee-v-State-579_SE2d_730.pdf
```

---

## Updated Summary Table

| Original Filename | NEW Proposed Filename |
|-------------------|----------------------|
| Abbott Labs. v. Sandoz, Inc (ND Ill 2010).pdf | `cs_NDIll-2010-Abbott-Labs-v-Sandoz-Inc-743_FSupp2d_762.pdf` |
| Alden v. Me._Attachment1 (1st Cir 1999).pdf | `cs_US-1999-Alden-v-Maine-527_US_706.pdf` |
| Allan v. United States_ 2019 U.S. Dist. LEXIS 123570.pdf | `cs_EDVa-2019-Allan-v-United-States-USDistLEXIS_123570.pdf` |
| Landrum v. Verg Enters., LLC (State Ct Fulton County 2024).pdf | `cs_GaStCtFulton-2024-Landrum-v-Verg-Enters-Unpub.pdf` |
| law - GA COA - Adams v. State (Ga App 2000).pdf | `cs_GaCtApp-2000-Adams-v-State-534_SE2d_538.pdf` |
| law - GA SC - Agee v. State (Ga 2003).pdf | `cs_Ga-2003-Agee-v-State-579_SE2d_730.pdf` |

---

## Court Abbreviation Conversion Algorithm

```python
def bluebook_to_filename(bluebook_abbrev):
    """
    Convert Bluebook abbreviation to filename-safe format.
    Input: "N.D. Ill." or "Ga. Ct. App."
    Output: "NDIll" or "GaCtApp"
    """
    # Remove all dots
    result = bluebook_abbrev.replace('.', '')
    # Remove spaces
    result = result.replace(' ', '')
    return result

# Examples:
# "N.D. Ill." → "NDIll"
# "E.D. Va." → "EDVa"
# "S.D.N.Y." → "SDNY"
# "Ga." → "Ga"
# "Ga. Ct. App." → "GaCtApp"
# "1st Cir." → "1stCir"
```

---

## Reporter Citation Extraction Algorithm

```python
def extract_reporter_citation(pdf_text):
    """
    Extract volume, reporter, and page from PDF text.
    Returns: (volume, reporter_abbrev, page) or None
    """

    # Define reporter patterns (in priority order)
    patterns = [
        # Federal reporters
        r'(\d+)\s+F\.\s*Supp\.\s*(\d*)d?\s+(\d+)',  # F.Supp.2d, F.Supp.3d
        r'(\d+)\s+F\.\s*(\d*)(?:th|d)?\s+(\d+)',    # F.3d, F.4th
        r'(\d+)\s+S\.\s*Ct\.\s+(\d+)',               # S.Ct.
        r'(\d+)\s+U\.S\.\s+(\d+)',                   # U.S.

        # Regional reporters
        r'(\d+)\s+S\.E\.\s*(\d*)d?\s+(\d+)',         # S.E.2d
        r'(\d+)\s+N\.E\.\s*(\d*)d?\s+(\d+)',         # N.E.2d, N.E.3d
        r'(\d+)\s+P\.\s*(\d*)d?\s+(\d+)',            # P.2d, P.3d
        r'(\d+)\s+A\.\s*(\d*)d?\s+(\d+)',            # A.2d, A.3d
        r'(\d+)\s+S\.W\.\s*(\d*)d?\s+(\d+)',         # S.W.2d, S.W.3d
        r'(\d+)\s+N\.W\.\s*(\d*)d?\s+(\d+)',         # N.W.2d
        r'(\d+)\s+So\.\s*(\d*)d?\s+(\d+)',           # So.2d, So.3d

        # State reporters
        r'(\d+)\s+Ga\.\s*App\.\s+(\d+)',             # Ga.App.
        r'(\d+)\s+Ga\.\s+(\d+)',                     # Ga.
        r'(\d+)\s+Cal\.\s*(?:App\.)?\s*(\d+)',       # Cal., Cal.App.

        # Online databases
        r'U\.S\.\s*Dist\.\s*LEXIS\s+(\d+)',          # U.S. Dist. LEXIS
        r'U\.S\.\s*App\.\s*LEXIS\s+(\d+)',           # U.S. App. LEXIS
        r'(\d{4})\s+WL\s+(\d+)',                     # Westlaw
    ]

    for pattern in patterns:
        match = re.search(pattern, pdf_text)
        if match:
            return parse_citation(match)

    return None  # No reporter found

def format_reporter_citation(volume, reporter, page):
    """
    Format as: volume_reporter_page
    Reporter: remove dots and spaces
    """
    reporter_clean = reporter.replace('.', '').replace(' ', '')

    if volume:
        return f"{volume}_{reporter_clean}_{page}"
    else:
        # LEXIS/WL without volume
        return f"{reporter_clean}_{page}"
```

---

## Complete Bluebook Court Mapping

### Federal District Courts (All 94 Districts)

Conversion formula: Remove dots and spaces from Bluebook abbreviation

**Examples:**
- N.D. Ala. → `NDAla`
- D. Alaska → `DAlaska`
- E.D. Ark. → `EDArk`
- C.D. Cal. → `CDCal`
- D.D.C. → `DDC`
- N.D.N.Y. → `NDNY`
- S.D.W. Va. → `SDWVa`

**Full list available in:** `courts_mapping.json` (to be updated with Bluebook format)

### State Courts (All 50 States)

**Supreme Courts:**
- Alabama: Ala. → `Ala`
- Alaska: Alaska → `Alaska`
- Arizona: Ariz. → `Ariz`
- California: Cal. → `Cal`
- Georgia: Ga. → `Ga`
- New York: N.Y. → `NY` (Court of Appeals is highest court)
- Texas: Tex. → `Tex`
- [etc. for all 50 states]

**Appellate Courts:**
- Alabama Civil: Ala. Civ. App. → `AlaCivApp`
- Georgia: Ga. Ct. App. → `GaCtApp`
- California: Cal. Ct. App. → `CalCtApp`
- New York: N.Y. App. Div. → `NYAppDiv`
- [etc.]

**Full list available in:** `courts_mapping.json` (to be updated)

---

## Next Steps

1. ✅ Updated formatting rules documented
2. ✅ Bluebook abbreviations incorporated
3. ✅ Reporter citation format updated to include volume and page
4. ⏭️ Update `courts_mapping.json` with Bluebook abbreviations
5. ⏭️ Update `reporters_database.json` with volume/page extraction patterns
6. ⏭️ Implement extraction engine with new format
7. ⏭️ Test on sample files

---

## Summary of All Formatting Rules

**Final Format:** `cs_[bluebook-court]-[year]-[case-name]-[volume_reporter_page].pdf`

**Element Rules:**
1. **Court:** Bluebook abbreviation with dots/spaces removed
2. **Year:** 4-digit year from decision date
3. **Case Name:** First 2 words per party, special chars removed, hyphen-separated
4. **Reporter:** `volume_reporter_page` format, dots removed from reporter

**Example:**
```
cs_NDIll-2010-Abbott-Labs-v-Sandoz-Inc-743_FSupp2d_762.pdf
```
