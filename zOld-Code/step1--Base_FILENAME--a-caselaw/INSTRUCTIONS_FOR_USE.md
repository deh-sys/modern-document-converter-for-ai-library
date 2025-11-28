# Instructions for Using the Caselaw PDF Renamer

Complete step-by-step guide with exact commands to copy and paste into your terminal.



## Quick Reference

### Most Common Commands

**Preview files before renaming:**

```bash
python3 src/cli.py preview sample_files/
```

**Rename files with metadata extraction:**

```bash
python3 src/cli.py rename sample_files/ --extract-metadata
```

**Interactive rename (confirm each):**

```bash
python3 src/cli.py rename sample_files/ --extract-metadata --interactive
```

**View registry in Excel/Sheets:**

```bash
open /Users/dan/LIBRARY_SYSTEM_REGISTRIES/metadata_registry.csv
```

**Reset configuration:**

```bash
rm .caselaw_config.json
```

---

## 

---

## Table of Contents

1. [Prerequisites & Installation](#prerequisites--installation)
2. [First-Time Setup](#first-time-setup)
3. [Basic Operations](#basic-operations)
4. [Metadata & Registry](#metadata--registry)
5. [Advanced Usage](#advanced-usage)
6. [Understanding Output](#understanding-output)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites & Installation

### Step 1: Check if pdftotext is installed

Copy and paste this command into your terminal:

```bash
pdftotext -v
```

**If you see version information**, you're good! Skip to [First-Time Setup](#first-time-setup).

**If you see "command not found"**, continue to Step 2.

### Step 2: Install pdftotext

**On macOS** (using Homebrew):
```bash
brew install poppler
```

**On Ubuntu/Debian Linux**:
```bash
sudo apt-get update
sudo apt-get install poppler-utils
```

**On Windows**:
Download from: https://blog.alivate.com.au/poppler-windows/
Extract and add to your PATH.

### Step 3: Navigate to the project directory

```bash
cd /Users/dan/Projects/file-renamer-caselaw
```

*(Replace with your actual project path if different)*

---

## First-Time Setup

### Understanding the App

This app does two main things:
1. **Renames** your PDF files using a standardized format
2. **Extracts metadata** (case info, judges, disposition, etc.) into a searchable registry

The format for renamed files is:
```
c.COURT__YEAR__Case-Name__Citation.pdf
```

Example:
```
c.US__1999__ALDEN-v-MAINE__527_US_706.pdf
```

### No Setup Required!

The app works immediately. On first use with metadata extraction, it will prompt you to configure where to store your registry files.

---

## Basic Operations

### Preview Mode (See What Would Change - Doesn't Actually Rename)

**Preview a single PDF file:**

```bash
python3 src/cli.py preview "path/to/your/file.pdf"
```

**Example with an actual file:**
```bash
python3 src/cli.py preview "sample_files/Abbott Labs. v. Sandoz, Inc (ND Ill 2010).pdf"
```

**Preview all PDFs in a directory:**

```bash
python3 src/cli.py preview sample_files/
```

**What you'll see:**
- Original filename
- Proposed new filename
- Extracted court, year, case name, reporter
- Confidence level (HIGH/MEDIUM/LOW)
- Any notes or warnings

### Rename Mode (Actually Renames Files)

**⚠️ WARNING:** This ACTUALLY renames your files. Use preview mode first!

**Rename a single file:**

```bash
python3 src/cli.py rename "path/to/your/file.pdf"
```

**Rename all PDFs in a directory:**

```bash
python3 src/cli.py rename sample_files/
```

**Interactive mode (confirm each rename):**

```bash
python3 src/cli.py rename sample_files/ --interactive
```

*For each file, you'll be asked:*
```
Proceed with rename? [y/N]:
```

Type `y` and press Enter to rename, or just press Enter to skip.

---

## Metadata & Registry

### What is the Registry?

The registry is a central database (JSON + CSV files) that stores detailed metadata about all your processed cases:
- Case name, court, year, citation
- Disposition (affirmed, reversed, etc.)
- Opinion author
- Panel members
- Concurring/dissenting judges
- Date decided
- And more...

### First-Time Registry Setup

**Run rename OR preview with metadata extraction:**

```bash
python3 src/cli.py preview sample_files/ --extract-metadata
```

**You'll see this prompt:**
```
================================================================================
Metadata Registry Configuration
================================================================================

No default registry path configured.
Enter path for metadata registry (e.g., ./metadata_registry):
>
```

**Type your desired path** (example):
```
/Users/dan/LIBRARY_SYSTEM_REGISTRIES/metadata_registry
```

**Then it asks:**
```
Save this as default registry location? [Y/n]:
```

Press Enter (or type `y`) to save this as your default.

### Using the Registry After Setup

**Preview with metadata extraction (uses your saved default):**

```bash
python3 src/cli.py preview sample_files/ --extract-metadata
```

It will use your saved registry path automatically!

**Rename with metadata extraction:**

```bash
python3 src/cli.py rename sample_files/ --extract-metadata
```

**Specify a different registry path (one-time override):**

```bash
python3 src/cli.py preview sample_files/ --extract-metadata --registry-path /path/to/other/registry
```

### What Files Are Created?

After running with `--extract-metadata`, you'll have:

**1. Sidecar JSON files** (next to each PDF):
```
Abbott Labs. v. Sandoz, Inc (ND Ill 2010).pdf
Abbott Labs. v. Sandoz, Inc (ND Ill 2010).pdf.metadata.json  ← New!
```

**2. Central registry files** (at your registry path):
```
/Users/dan/LIBRARY_SYSTEM_REGISTRIES/
  metadata_registry.json      ← Machine-readable
  metadata_registry.csv       ← Spreadsheet-compatible
  metadata_registry.json.backup  ← Auto-backup
  metadata_registry.csv.backup   ← Auto-backup
```

### Viewing Registry Data

**Open CSV in Excel/Numbers/Sheets:**

```bash
open /Users/dan/LIBRARY_SYSTEM_REGISTRIES/metadata_registry.csv
```

*(Or double-click the file)*

**View JSON in terminal:**

```bash
cat /Users/dan/LIBRARY_SYSTEM_REGISTRIES/metadata_registry.json | python3 -m json.tool | less
```

Press `q` to quit.

### Changing Your Default Registry Path

**Option 1: Delete config and start over**

```bash
rm .caselaw_config.json
```

Next time you run with `--extract-metadata`, you'll be prompted again.

**Option 2: Edit config file directly**

```bash
open .caselaw_config.json
```

Change the `default_registry_path` value, save, and close.

---

## Advanced Usage

### Batch Processing Large Directories

**Process all PDFs in a directory tree recursively:**

The app doesn't support recursion currently, but you can process subdirectories:

```bash
python3 src/cli.py rename legal_cases/2023/
python3 src/cli.py rename legal_cases/2024/
python3 src/cli.py rename legal_cases/2025/
```

Or use a shell loop:

```bash
for dir in legal_cases/*/; do
    python3 src/cli.py rename "$dir" --extract-metadata
done
```

### Handling Duplicate Filenames

**The app automatically handles duplicates!**

If two cases would generate the same filename, the second one gets `_1` appended:

```
c.US__1999__Smith-v-Jones__123_US_456.pdf
c.US__1999__Smith-v-Jones__123_US_456_1.pdf  ← Auto-renamed
```

You'll see a note:
```
Note: Renamed to avoid duplicate (added _1)
```

### Preview Without Installing Dependencies

The app checks for `pdftotext` on startup. If it's missing, you'll see:

```
ERROR: Missing required dependencies
pdftotext not found. Please install poppler-utils:
  macOS:   brew install poppler
  Ubuntu:  sudo apt-get install poppler-utils
  Windows: Download from https://blog.alivate.com.au/poppler-windows/
```

### Testing on Sample Files

**Try the app on included sample files:**

```bash
# Preview only (safe)
python3 src/cli.py preview sample_files/

# With metadata extraction
python3 src/cli.py preview sample_files/ --extract-metadata --registry-path ./test_registry

# Check the registry
open test_registry.csv
```

---

## Understanding Output

### Console Output Explained

When you run preview or rename, you'll see:

```
[1/6] Abbott Labs. v. Sandoz, Inc (ND Ill 2010).pdf
      ↓
      c.ILL_ND__2010__Abbott-v-Sandoz__743_FSupp2d_762.pdf

      Extracted:
        Court:    ILL_ND (from PDF)
        Year:     2010 (from PDF)
        Case:     Abbott-v-Sandoz (from PDF)
        Reporter: 743_FSupp2d_762 (from PDF)
      Confidence: HIGH
```

**Breaking it down:**

- `[1/6]` - File 1 of 6 being processed
- Original filename shown first
- `↓` arrow
- New filename shown below
- **Extracted** section shows what was found and where (PDF or filename)
- **Confidence** indicates how certain the extraction is:
  - `HIGH`: 3+ fields extracted from PDF
  - `MEDIUM`: 2 fields from PDF
  - `LOW`: Mostly from filename

### Confidence Scores

**HIGH confidence** - Most reliable
- 3 or 4 fields extracted directly from PDF text
- Court, year, case name all found in PDF
- Safe to rename automatically

**MEDIUM confidence** - Generally reliable
- 2 fields from PDF, others from filename
- Review recommended but usually correct

**LOW confidence** - Review carefully
- Mostly extracted from filename
- PDF may be scanned/OCR issues
- Double-check before renaming

### Notes and Warnings

You may see notes like:

```
Notes:
  - Court from filename (PDF extraction failed)
  - Filename truncated from 300 to 255 characters
  - Renamed to avoid duplicate (added _1)
```

These are informational and help you understand what happened.

### Summary Statistics

At the end, you'll see:

```
Summary:
--------------------------------------------------------------------------------
Total files: 6
Successfully extracted: 6 (100%)
High confidence: 5
Medium confidence: 1
Low confidence: 0
```

This helps you assess the overall quality of the batch.

---

## Troubleshooting

### "pdftotext not found"

**Problem:** The app can't find the pdftotext tool.

**Solution:** Install poppler-utils (see [Prerequisites](#prerequisites--installation))

### "Permission denied"

**Problem:** You don't have permission to rename files in that directory.

**Solution:**
```bash
# Check file permissions
ls -la path/to/directory/

# If needed, change ownership
sudo chown -R $USER path/to/directory/
```

### "No files found" or "Total files: 0"

**Problem:** No PDFs in the specified directory.

**Solution:** Check the path:
```bash
# List PDFs in directory
ls -la path/to/directory/*.pdf

# Verify you're in the right place
pwd
```

### "Registry path required"

**Problem:** You used `--extract-metadata` but didn't provide a registry path and the app couldn't prompt you.

**Solution:** Either:
1. Run interactively (in a terminal where you can type)
2. Provide `--registry-path` explicitly:
```bash
python3 src/cli.py preview sample_files/ --extract-metadata --registry-path ./my_registry
```

### "Metadata extraction failed"

**Problem:** PDF is scanned/encrypted/corrupted.

**What happens:**
- File will still be renamed based on filename
- Metadata fields will be empty
- You'll see a warning message

**Solution:**
- Check if PDF opens normally
- Try re-downloading the PDF
- File will still be processed, just without metadata

### Very Long Filenames

**Problem:** Generated filename exceeds 255 characters.

**What happens:**
- App automatically truncates filename
- Extension is preserved
- You'll see: "Filename truncated from 300 to 255 characters"

**Solution:** This is handled automatically. The file works fine.

### Duplicate Filenames

**Problem:** Two PDFs would generate identical filenames.

**What happens:**
- Second file gets `_1` appended
- Third file gets `_2`, etc.
- You'll see: "Renamed to avoid duplicate (added _1)"

**Solution:** This is handled automatically. If you want different names, rename one manually.

### Config File Issues

**Problem:** Config file corrupted or wrong path saved.

**Solution:**
```bash
# View current config
cat .caselaw_config.json

# Delete and reconfigure
rm .caselaw_config.json

# Next run will prompt you again
python3 src/cli.py preview sample_files/ --extract-metadata
```

---

## Getting Help

**View command-line help:**
```bash
python3 src/cli.py --help
```

**View mode-specific help:**
```bash
python3 src/cli.py preview --help
python3 src/cli.py rename --help
```

**Test on sample files:**
```bash
python3 src/cli.py preview sample_files/
```

---

## Next Steps

1. **Start with preview mode** on a few test files
2. **Check the output** to verify it's what you expect
3. **Use `--extract-metadata`** to build your registry
4. **Review the CSV** in Excel/Sheets periodically
5. **Use interactive mode** when processing important files

The app includes safety features:
- Duplicate detection (never overwrites)
- Automatic backups (for registry)
- Validation (checks filename length, illegal characters)
- Atomic operations (safe file renames)

Happy renaming!
