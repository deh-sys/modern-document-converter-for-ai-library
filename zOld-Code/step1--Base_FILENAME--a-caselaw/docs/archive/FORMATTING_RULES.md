# Final Formatting Rules for Caselaw Filenames

**Target Format:** `cs_[jurisdiction/court]-[year]-[shortened case name]-[main reporter citation].pdf`

---

## Finalized Rules (User Decisions)

### 1. Reporter Citation Format
**Decision:** Remove all dots from reporter citations

**Examples:**
- `F.Supp.2d` → `FSupp2d`
- `S.E.2d` → `SE2d`
- `U.S.` → `US`
- `F.3d` → `F3d`
- `U.S.Dist.LEXIS` → `USDistLEXIS`
- `Ga.App.` → `GaApp`

### 2. Case Name Length Limit
**Decision:** Maximum 2 full words per side of "v"

**Examples:**
- "Abbott Laboratories v. Sandoz Incorporated" → `Abbott-Laboratories-v-Sandoz-Incorporated`
- "John Jacob Smith v. State" → `John-Jacob-v-State`
- "Microsoft Corporation v. United States" → `Microsoft-Corporation-v-United-States`

**Edge Cases:**
- If party name is only 1 word, use just that word
- "Smith v. Jones" → `Smith-v-Jones`
- Count real words, not designators (Inc, LLC, Corp count as words)

### 3. Special Characters
**Decision:** Eliminate all special characters

**Characters to Remove:**
- Periods: `.`
- Commas: `,`
- Apostrophes: `'`
- Ampersands: `&`
- Quotation marks: `"` `'`
- Parentheses: `(` `)`
- Colons, semicolons: `:` `;`

**Examples:**
- `O'Brien` → `OBrien`
- `AT&T` → `ATT`
- `Smith, Jr.` → `Smith Jr`
- `"Big Apple" Store` → `Big Apple Store`

### 4. Multiple Parties
**Decision:** Use only the first party on each side of "v"

**Examples:**
- "Smith, Jones, and Brown v. State" → `Smith` (only) `v State`
- "United States ex rel. Smith v. Johnson" → `United States ex rel Smith` (first 2 words) `v Johnson`
- "A, B, C, and D v. X, Y, and Z" → `A` `v X`

**Implementation:**
- Split case caption at " v. " or " vs. " or " v "
- On each side, take text up to first comma (if present) to isolate first party
- Then apply 2-word limit
- Remove "et al." if present

---

## Complete Formatting Algorithm

### Step-by-Step Process

```
INPUT: Full case name from PDF or filename
EXAMPLE: "Abbott Laboratories, Inc. v. Sandoz, Inc., Johnson & Johnson"

1. SPLIT AT "v"
   - Before v: "Abbott Laboratories, Inc."
   - After v: "Sandoz, Inc., Johnson & Johnson"

2. ISOLATE FIRST PARTY (remove at first comma)
   - Before v: "Abbott Laboratories, Inc."
   - After v: "Sandoz, Inc."

3. REMOVE SPECIAL CHARACTERS
   - Before v: "Abbott Laboratories Inc"
   - After v: "Sandoz Inc"

4. TOKENIZE AND LIMIT TO 2 WORDS
   - Before v: ["Abbott", "Laboratories"] (stop at 2 words)
   - After v: ["Sandoz", "Inc"] (only 2 words available)

5. JOIN WITH HYPHENS
   - Result: "Abbott-Laboratories-v-Sandoz-Inc"

OUTPUT: Abbott-Laboratories-v-Sandoz-Inc
```

---

## Updated Sample Transformations

### File 1: Abbott Labs v. Sandoz
- **Original:** `Abbott Labs. v. Sandoz, Inc (ND Ill 2010).pdf`
- **Case Name Processing:**
  - Raw: "Abbott Labs. v. Sandoz, Inc"
  - First party each side: "Abbott Labs." / "Sandoz, Inc"
  - Remove special chars: "Abbott Labs" / "Sandoz Inc"
  - Take 2 words: "Abbott Labs" / "Sandoz Inc"
  - Result: `Abbott-Labs-v-Sandoz-Inc`
- **Reporter:** `FSupp2d` (removed dots from F.Supp.2d)
- **New Filename:** `cs_ND-Ill-2010-Abbott-Labs-v-Sandoz-Inc-FSupp2d.pdf`

### File 2: Alden v. Maine
- **Original:** `Alden v. Me._Attachment1 (1st Cir 1999).pdf`
- **Case Name Processing:**
  - Raw: "Alden v. Maine" (corrected from Me.)
  - First party each side: "Alden" / "Maine"
  - Remove special chars: "Alden" / "Maine"
  - Take 2 words: "Alden" (only 1) / "Maine" (only 1)
  - Result: `Alden-v-Maine`
- **Reporter:** `US` (removed dots from U.S.)
- **New Filename:** `cs_SCOTUS-1999-Alden-v-Maine-US.pdf`

### File 3: Allan v. United States
- **Original:** `Allan v. United States_ 2019 U.S. Dist. LEXIS 123570.pdf`
- **Case Name Processing:**
  - Raw: "Allan v. United States"
  - First party each side: "Allan" / "United States"
  - Remove special chars: "Allan" / "United States"
  - Take 2 words: "Allan" (only 1) / "United States" (2 words)
  - Result: `Allan-v-United-States`
- **Reporter:** `USDistLEXIS` (removed dots)
- **New Filename:** `cs_ED-Va-2019-Allan-v-United-States-USDistLEXIS.pdf`

### File 4: Landrum v. Verg Enterprises
- **Original:** `Landrum v. Verg Enters., LLC (State Ct Fulton County 2024).pdf`
- **Case Name Processing:**
  - Raw: "Landrum v. Verg Enters., LLC"
  - First party each side: "Landrum" / "Verg Enters., LLC"
  - Remove special chars: "Landrum" / "Verg Enters LLC"
  - Take 2 words: "Landrum" (only 1) / "Verg Enters" (2 words)
  - Result: `Landrum-v-Verg-Enters`
- **Reporter:** `Unpub`
- **New Filename:** `cs_GA-State-Fulton-2024-Landrum-v-Verg-Enters-Unpub.pdf`

### File 5: Adams v. State
- **Original:** `law - GA COA - Adams v. State (Ga App 2000).pdf`
- **Case Name Processing:**
  - Raw: "Adams v. State"
  - First party each side: "Adams" / "State"
  - Remove special chars: "Adams" / "State"
  - Take 2 words: "Adams" (only 1) / "State" (only 1)
  - Result: `Adams-v-State`
- **Reporter:** `SE2d` (removed dots from S.E.2d)
- **New Filename:** `cs_GA-COA-2000-Adams-v-State-SE2d.pdf`

### File 6: Agee v. State
- **Original:** `law - GA SC - Agee v. State (Ga 2003).pdf`
- **Case Name Processing:**
  - Raw: "Agee v. State"
  - First party each side: "Agee" / "State"
  - Remove special chars: "Agee" / "State"
  - Take 2 words: "Agee" (only 1) / "State" (only 1)
  - Result: `Agee-v-State`
- **Reporter:** `SE2d` (removed dots from S.E.2d)
- **New Filename:** `cs_GA-SC-2003-Agee-v-State-SE2d.pdf`

---

## Final Summary Table

| Original Filename | Final Proposed Filename |
|-------------------|-------------------------|
| Abbott Labs. v. Sandoz, Inc (ND Ill 2010).pdf | `cs_ND-Ill-2010-Abbott-Labs-v-Sandoz-Inc-FSupp2d.pdf` |
| Alden v. Me._Attachment1 (1st Cir 1999).pdf | `cs_SCOTUS-1999-Alden-v-Maine-US.pdf` |
| Allan v. United States_ 2019 U.S. Dist. LEXIS 123570.pdf | `cs_ED-Va-2019-Allan-v-United-States-USDistLEXIS.pdf` |
| Landrum v. Verg Enters., LLC (State Ct Fulton County 2024).pdf | `cs_GA-State-Fulton-2024-Landrum-v-Verg-Enters-Unpub.pdf` |
| law - GA COA - Adams v. State (Ga App 2000).pdf | `cs_GA-COA-2000-Adams-v-State-SE2d.pdf` |
| law - GA SC - Agee v. State (Ga 2003).pdf | `cs_GA-SC-2003-Agee-v-State-SE2d.pdf` |

---

## Special Cases & Edge Cases

### Complex Party Names

**Example 1: Multiple entities**
- Input: "Smith, Jones & Associates, LLC v. Brown Corporation, Inc., Johnson"
- Split at v: "Smith, Jones & Associates, LLC" / "Brown Corporation, Inc., Johnson"
- First party (at comma): "Smith, Jones & Associates, LLC" / "Brown Corporation, Inc."
- Remove special chars: "Smith Jones Associates LLC" / "Brown Corporation Inc"
- Take 2 words: "Smith Jones" / "Brown Corporation"
- Result: `Smith-Jones-v-Brown-Corporation`

**Example 2: "et al."**
- Input: "Smith, et al. v. State"
- Split at v: "Smith, et al." / "State"
- First party: "Smith, et al." / "State"
- Remove special chars and "et al": "Smith" / "State"
- Result: `Smith-v-State`

**Example 3: "Ex rel" (on behalf of)**
- Input: "United States ex rel. Johnson v. Big Corp"
- Split at v: "United States ex rel. Johnson" / "Big Corp"
- First party (before comma, or if no comma, take 2 words): "United States" / "Big Corp"
- Take 2 words: "United States" / "Big Corp"
- Result: `United-States-v-Big-Corp`

### Numbers in Names
**Example:** "123 Corporation v. Smith"
- Keep numbers: "123 Corporation v Smith"
- Result: `123-Corporation-v-Smith`

### Abbreviations in Names
**Example:** "Dr. Smith v. ABC Hospital"
- Remove periods: "Dr Smith v ABC Hospital"
- Result: `Dr-Smith-v-ABC-Hospital`

### Hyphenated Names (input already has hyphens)
**Example:** "Coca-Cola v. Pepsi-Co"
- Input already has internal hyphens
- Keep them: "Coca-Cola" / "Pepsi-Co"
- Result: `Coca-Cola-v-Pepsi-Co`
- Note: This means some party names will have internal hyphens, which is fine for readability

---

## Implementation Notes

### Word Counting Logic
- Split on spaces after removing special characters
- Filter out empty strings
- Take first N words (N=2 for this project)
- Common small words like "the", "a", "an" still count as words

### State Name Expansions
When extracting from PDF or filename:
- "Me." → "Maine"
- "Me" → "Maine" (if in state context)
- "U.S." → "United States" (as party name)
- "US" → "United States" (as party name)

### Preservation of Meaning
- Try to keep abbreviations that are part of proper names: "ABC Corp" stays as "ABC Corp"
- Don't expand well-known acronyms: "IBM" stays as "IBM", not "International Business Machines"

---

## Ready for Implementation

All formatting rules are now finalized and documented. The extraction engine can be built using:
1. `courts_mapping.json` - for court standardization
2. `reporters_database.json` - for reporter identification (with dots removed in output)
3. These formatting rules - for case name processing

Next step: Build the Python extraction engine and file renaming application.
