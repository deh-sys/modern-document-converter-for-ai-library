# Troubleshooting Guide

Common issues and solutions for the Caselaw PDF Renamer.

---

## Installation Issues

### "pdftotext not found" or "command not found: pdftotext"

**Problem:** The `pdftotext` command-line tool is not installed on your system.

**Solution:**

**macOS** (using Homebrew):
```bash
# Install Homebrew if you don't have it
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install poppler (includes pdftotext)
brew install poppler

# Verify installation
pdftotext -v
```

**Ubuntu/Debian Linux**:
```bash
sudo apt-get update
sudo apt-get install poppler-utils

# Verify installation
pdftotext -v
```

**Fedora/RedHat/CentOS**:
```bash
sudo yum install poppler-utils

# Verify installation
pdftotext -v
```

**Windows**:
1. Download poppler from: https://blog.alivate.com.au/poppler-windows/
2. Extract the ZIP file
3. Add the `bin` folder to your PATH environment variable
4. Restart your terminal
5. Verify: `pdftotext -v`

---

## Permission Issues

### "Permission denied" when renaming files

**Problem:** You don't have write permission for the directory or files.

**Diagnosis:**
```bash
# Check file and directory permissions
ls -la /path/to/files/

# Check who owns the files
ls -l /path/to/files/*.pdf
```

**Solution 1:** Change ownership to your user
```bash
# For a single directory
sudo chown -R $USER /path/to/files/

# Verify
ls -la /path/to/files/
```

**Solution 2:** Run with appropriate permissions
```bash
# Make files writable
chmod +w /path/to/files/*.pdf
```

**Solution 3:** Use sudo (last resort, be careful)
```bash
sudo python3 src/cli.py rename /path/to/files/
```

### "Permission denied" when creating registry

**Problem:** No write permission for registry directory.

**Solution:**
```bash
# Check directory permissions
ls -la /path/to/LIBRARY_SYSTEM_REGISTRIES/

# Create directory with correct permissions
mkdir -p /path/to/LIBRARY_SYSTEM_REGISTRIES/
chmod 755 /path/to/LIBRARY_SYSTEM_REGISTRIES/

# Or use a different location you own
python3 src/cli.py preview sample_files/ --extract-metadata --registry-path ~/Documents/caselaw_registry
```

---

## File Processing Issues

### "No files found" or "Total files: 0"

**Problem:** The app isn't finding any PDF files in the specified directory.

**Diagnosis:**
```bash
# List PDF files in the directory
ls -la /path/to/directory/*.pdf

# Check if you're in the right directory
pwd

# Verify the path exists
ls -la /path/to/directory/
```

**Common Causes:**
1. Wrong path specified
2. No `.pdf` files in directory
3. Files have different extensions (`.PDF`, `.Pdf`)
4. Hidden files (starting with `.`)

**Solutions:**
```bash
# Check for case-sensitive extensions
ls -la /path/to/directory/*.{pdf,PDF,Pdf}

# Use absolute path
python3 src/cli.py preview /full/path/to/directory/

# Process specific file
python3 src/cli.py preview "/path/to/specific file.pdf"
```

### "Could not generate filename - missing: court, year"

**Problem:** The app couldn't extract required fields from the PDF or filename.

**What this means:**
- PDF might be scanned (no extractable text)
- PDF might be encrypted
- Filename doesn't contain hints
- PDF formatting is non-standard

**Diagnosis:**
```bash
# Test if PDF has extractable text
pdftotext "/path/to/file.pdf" - | head -50

# If empty or gibberish, PDF is likely scanned/encrypted
```

**Solutions:**
1. **Check PDF opens normally:**
   ```bash
   open "/path/to/file.pdf"
   ```

2. **Try renaming with better filename hints:**
   ```bash
   # Original: document.pdf (no hints)
   # Better: Smith v Jones 2023 US.pdf (has hints)
   ```

3. **Check preview output for clues:**
   ```bash
   python3 src/cli.py preview "/path/to/file.pdf"
   # Look at the "Extracted" section to see what was found
   ```

4. **Manual rename if necessary:**
   If the PDF is scanned or corrupted, you may need to manually rename it based on the content you can see.

---

## Registry Issues

### "Registry path required for metadata extraction"

**Problem:** You're using `--extract-metadata` but haven't configured a registry path.

**Solution - Interactive (Recommended):**
```bash
# Run without --registry-path, answer the prompts
python3 src/cli.py preview sample_files/ --extract-metadata

# Follow the prompt:
# > Enter path: /Users/dan/LIBRARY_SYSTEM_REGISTRIES/metadata_registry
# > Save as default? Y
```

**Solution - Specify explicitly:**
```bash
python3 src/cli.py preview sample_files/ --extract-metadata --registry-path ./my_registry
```

**Solution - Non-interactive scripts:**
If running in a script/automated environment:
```bash
# Always provide --registry-path explicitly
python3 src/cli.py rename /path/to/files/ --extract-metadata --registry-path /path/to/registry
```

### "Error updating registry" or corrupted registry files

**Problem:** Registry JSON is malformed or write failed mid-operation.

**Recovery Steps:**

1. **Check if backup exists:**
```bash
ls -la /path/to/registry.json.backup
```

2. **Restore from backup:**
```bash
cp /path/to/registry.json.backup /path/to/registry.json
```

3. **Delete and start fresh:**
```bash
# This will lose your registry data!
rm /path/to/registry.json
rm /path/to/registry.csv

# Next run will create new registry
python3 src/cli.py preview sample_files/ --extract-metadata
```

4. **Verify JSON is valid:**
```bash
python3 -m json.tool /path/to/registry.json > /dev/null
# If no error, JSON is valid
```

### Can't find where registry files are saved

**Check your config:**
```bash
cat .caselaw_config.json
```

This shows your default registry path.

**Common locations:**
- `/Users/dan/LIBRARY_SYSTEM_REGISTRIES/metadata_registry.json`
- `./metadata_registry.json` (in current directory)
- `~/Documents/caselaw_registry.json`

**Search for them:**
```bash
# macOS/Linux
find ~ -name "metadata_registry.json" 2>/dev/null

# Or search by recent modification
find ~ -name "*.json" -mtime -1 2>/dev/null | grep registry
```

---

## Configuration Issues

### Config file corrupted or has wrong path

**Problem:** `.caselaw_config.json` has incorrect or corrupted data.

**Solution 1:** View and edit
```bash
# View current config
cat .caselaw_config.json

# Edit directly
nano .caselaw_config.json
# or
open .caselaw_config.json
```

**Solution 2:** Delete and reconfigure
```bash
# Delete config
rm .caselaw_config.json

# Next run with --extract-metadata will prompt you again
python3 src/cli.py preview sample_files/ --extract-metadata
```

**Solution 3:** Create config manually
```bash
# Create correct config
cat > .caselaw_config.json << 'EOF'
{
  "default_registry_path": "/Users/dan/LIBRARY_SYSTEM_REGISTRIES/metadata_registry"
}
EOF
```

---

## Filename Issues

### "Filename truncated from X to 255 characters"

**Problem:** Generated filename exceeds OS limits (255 characters max).

**What happens:**
- App automatically truncates the filename
- Extension is preserved
- File still works normally

**This is handled automatically** - no action needed!

**If you want shorter names:**
- Case names are already limited to 1 word per party
- Reporter citations are abbreviated
- No further shortening possible without losing information

### Duplicate filenames or "_1" appended

**Problem:** Two PDFs generate identical filenames.

**What happens:**
- First file gets the standard name
- Second file gets `_1` appended
- Third gets `_2`, etc.

**Example:**
```
c.US__1999__Smith-v-Jones__123_US_456.pdf
c.US__1999__Smith-v-Jones__123_US_456_1.pdf
```

**This is handled automatically** to prevent overwrites!

**If you don't want this:**
The files are likely different cases that happened to generate the same name. You'll need to manually distinguish them (add court location, docket number, etc.).

### Special characters or weird formatting

**Problem:** Filename contains unexpected characters or formatting.

**The app automatically sanitizes:**
- Removes: `< > : " / \ | ? *`
- Removes: Control characters
- Keeps: Letters, numbers, underscores, hyphens, dots

**If you see odd formatting:**
It likely came from the PDF text itself. Check the PDF's case caption.

---

## Metadata Extraction Issues

### "Metadata extraction failed"

**Problem:** Comprehensive metadata couldn't be extracted.

**What happens:**
- File will still be renamed (uses basic extraction)
- Metadata fields will be empty in registry
- Warning message displayed

**Common Causes:**
1. PDF is scanned (no text layer)
2. PDF is encrypted
3. Non-standard formatting
4. Very old case (pre-computer typesetting)

**Solution:**
This is expected for some PDFs. The basic renaming still works! Metadata is "best effort."

### Incorrect metadata extracted

**Problem:** Disposition, judges, etc. are wrong.

**Why this happens:**
- Pattern-based extraction isn't perfect
- Non-standard case formatting
- Multiple opinions in one PDF
- Unusual judicial language

**Solution:**
1. **Check confidence level:**
   - LOW confidence = likely needs review
   - MEDIUM = usually okay
   - HIGH = generally reliable

2. **Edit CSV manually:**
   ```bash
   open /path/to/metadata_registry.csv
   # Edit in Excel/Numbers/Sheets
   ```

3. **Report patterns:**
   If you see systematic errors, this helps improve the extraction patterns!

---

## Command-Line Issues

### Line breaks in commands causing errors

**Problem:**
```bash
python3 src/cli.py preview sample_files/ --extract-metadata
  --registry-path ./metadata_registry
```
Doesn't work! Shell executes as two separate commands.

**Solution:**

**Option 1:** Write on one line
```bash
python3 src/cli.py preview sample_files/ --extract-metadata --registry-path ./metadata_registry
```

**Option 2:** Use backslash for continuation
```bash
python3 src/cli.py preview sample_files/ \
  --extract-metadata \
  --registry-path ./metadata_registry
```

The backslash (`\`) tells the shell "more coming on next line."

### Spaces in filenames/paths

**Problem:**
```bash
python3 src/cli.py preview My Documents/Cases/
```
Fails because space breaks the path.

**Solution:** Quote paths with spaces
```bash
python3 src/cli.py preview "My Documents/Cases/"

# Or escape spaces
python3 src/cli.py preview My\ Documents/Cases/
```

---

## Performance Issues

### Processing is very slow

**Problem:** Large PDFs or many files taking a long time.

**Expected speeds:**
- ~2-5 seconds per file (depends on PDF size)
- First 5 pages + last 2 pages are read for metadata

**Solutions:**

1. **Process without metadata:**
   ```bash
   # Just rename, no metadata extraction
   python3 src/cli.py rename sample_files/
   ```

2. **Process in smaller batches:**
   ```bash
   python3 src/cli.py rename cases_2023/
   python3 src/cli.py rename cases_2024/
   python3 src/cli.py rename cases_2025/
   ```

3. **Check for stuck processes:**
   ```bash
   ps aux | grep pdftotext
   # Kill if stuck
   killall pdftotext
   ```

### Timeout errors

**Problem:** "TimeoutExpired" error during PDF extraction.

**What happens:**
- PDF extraction aborted after 30-45 seconds
- Falls back to filename extraction

**Solution:**
These timeouts protect against hang. If it happens frequently:

1. **Check PDF file size:**
   ```bash
   ls -lh problem_file.pdf
   ```

2. **Test pdftotext directly:**
   ```bash
   time pdftotext "problem_file.pdf" -
   ```

3. **Process that file separately:**
   Skip it in batch, handle manually

---

## Getting More Help

### Enable verbose output (if needed)

Currently the app shows file-by-file progress. For debugging:

```bash
# Preview with detailed output
python3 src/cli.py preview sample_files/ 2>&1 | tee output.log
```

### Check Python version

```bash
python3 --version
# Should be 3.6 or higher
```

### Verify file integrity

```bash
# Check if PDF opens
open "problem_file.pdf"

# Check if PDF has text
pdftotext "problem_file.pdf" - | wc -l
# If 0 or very few lines, PDF might be scanned
```

### Still having issues?

1. Check [README.md](./README.md) for overview
2. Check [INSTRUCTIONS_FOR_USE.md](./INSTRUCTIONS_FOR_USE.md) for step-by-step guide
3. Try on the included `sample_files/` first
4. Report issues with:
   - Command you ran
   - Error message (full text)
   - PDF characteristics (size, scanned/digital, court)
   - OS and Python version

---

## Quick Reference

**Reset everything:**
```bash
rm .caselaw_config.json
```

**Test on samples:**
```bash
python3 src/cli.py preview sample_files/
```

**Check dependencies:**
```bash
pdftotext -v
python3 --version
```

**View config:**
```bash
cat .caselaw_config.json
```

**Find registry files:**
```bash
find ~ -name "metadata_registry.json"
```

**View CLI help:**
```bash
python3 src/cli.py --help
python3 src/cli.py preview --help
python3 src/cli.py rename --help
```
