# Quick Start Guide

## Key Commands

### Test on Sample Articles

**Preview mode** (shows what would happen, doesn't rename):
```bash
python3 src/cli.py preview z_sample_articles/
```

### Rename Your Articles

**Rename all articles in a directory:**
```bash
python3 src/cli.py rename /path/to/your/articles/
```

**Rename with confirmation for each file:**
```bash
python3 src/cli.py rename /path/to/your/articles/ --interactive
```

### Extract Metadata

**Save metadata to JSON files alongside each article:**
```bash
python3 src/cli.py rename /path/to/your/articles/ --extract-metadata --registry-path ./my_registry
```

This creates:
- `[article].pdf.metadata.json` next to each file
- `my_registry.json` and `my_registry.csv` with all metadata

## Installation

1. **Install pdftotext** (required for PDF processing):
```bash
# macOS
brew install poppler

# Linux
sudo apt-get install poppler-utils
```

2. **Install Python dependencies** (optional, for Word documents):
```bash
pip install python-docx pydantic
```

## Understanding the Output

### Filename Format

```
[year]_[author_last]_[short_title].pdf
```

Examples:
- `1974_Arnold_Law_Fact_Medieval_Jury.pdf`
- `2013_Lerner_Rise_Directed_Verdict.pdf`

### Confidence Levels

- **HIGH**: All fields extracted from document text (most reliable)
- **MEDIUM**: Some fields from document, some from filename
- **LOW**: Mostly from filename (may need manual review)

### Smart Replacement Decisions

**The tool protects your manual work!**

Each file shows a replacement decision:
- **REPLACE ✓**: File will be renamed
- **SKIP ✗**: Original filename will be kept

The decision considers:
1. **Your filename quality**: Is it good manual work or a garbage download?
2. **Extraction confidence**: How reliable is the extracted data?

**You'll see output like:**
```
Arnold_Law_Fact_Medieval_Jury_Trial_1974.pdf
      ↓
      1974_Arnold_Law_Fact_Medieval_Jury_Trial_Out.pdf

      Original filename quality: HIGH
      Extraction confidence: HIGH
      Decision: REPLACE ✓
        Reason: Both high quality - extracted version likely better
```

**What gets protected (SKIP):**
- Good manual filenames when extraction is uncertain
- Files where extraction failed completely
- Cases where extraction looks wrong (e.g., wrong year detected)

**What gets improved (REPLACE):**
- Garbage downloads: `download(1).pdf`, `ssrn-12345.pdf`
- Generic names: `article.pdf`, `document.pdf`
- Any file when extraction confidence is HIGH

## Common Issues

### "pdftotext not found"

Install poppler:
```bash
brew install poppler  # macOS
sudo apt-get install poppler-utils  # Linux
```

### Poor extraction quality

The system works best with:
- Standard academic article formatting
- Clean PDFs (not scanned)
- Articles with clear title/author sections

If extraction is poor:
1. Check the PDF opens normally
2. Try preview mode first to see what's extracted
3. Use interactive mode to review each file
4. The patterns can be refined in the extractor files

### Missing fields

If author, title, or year is missing:
- The file won't be renamed (shown as FAILED)
- Check the extraction output to see what was found
- Fields may be extracted from filename as fallback

## Tips

1. **Start with preview mode** to see what will happen
2. **The tool protects manual work** - Good filenames won't be replaced unless extraction is HIGH confidence
3. **Garbage downloads get fixed** - Files like `download(1).pdf` will be improved even with MEDIUM confidence
4. **Use interactive mode** for important files or to verify decisions
5. **Check a few files** before batch processing
6. **Keep backups** of your original files (though the tool is conservative)
7. **Review SKIP decisions** - If a file shows "SKIP ✗", check why in the reason field

## Getting Help

Run with `--help` to see all options:
```bash
python3 src/cli.py --help
python3 src/cli.py preview --help
python3 src/cli.py rename --help
```
