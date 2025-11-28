"""
Markdown cleaning and normalization for RAG system compatibility.

This module provides conservative cleaning functions to ensure markdown files
are optimized for RAG (Retrieval-Augmented Generation) systems with:
- Consistent line endings (Unix-style \n)
- UTF-8 encoding without BOM
- No hidden control characters
- Stable heading syntax (ATX-style)
- Reproducible spacing

All cleaning is conservative - only formatting is normalized, content and
markdown semantics are preserved.
"""

import re
import unicodedata
from typing import Pattern


def normalize_line_endings(text: str) -> str:
    """
    Normalize all line endings to Unix-style (\\n).

    Converts Windows (\\r\\n) and old Mac (\\r) line endings to \\n.

    Args:
        text: Input markdown text

    Returns:
        Text with normalized line endings

    Example:
        >>> normalize_line_endings("line1\\r\\nline2\\rline3\\n")
        'line1\\nline2\\nline3\\n'
    """
    # Replace Windows line endings
    text = text.replace('\r\n', '\n')
    # Replace old Mac line endings
    text = text.replace('\r', '\n')
    return text


def ensure_utf8(text: str) -> str:
    """
    Ensure clean UTF-8 encoding by removing BOM and fixing common issues.

    Removes UTF-8 BOM and replaces problematic Unicode characters with
    ASCII equivalents where appropriate.

    Args:
        text: Input markdown text

    Returns:
        Text with clean UTF-8 encoding

    Example:
        >>> ensure_utf8("\\ufeffHello") # BOM removed
        'Hello'
    """
    # Remove UTF-8 BOM if present
    if text.startswith('\ufeff'):
        text = text[1:]

    # Replace common smart quotes with standard quotes
    replacements = {
        '\u2018': "'",  # Left single quotation mark
        '\u2019': "'",  # Right single quotation mark
        '\u201c': '"',  # Left double quotation mark
        '\u201d': '"',  # Right double quotation mark
        '\u2013': '-',  # En dash
        '\u2014': '--',  # Em dash
        '\u2026': '...',  # Horizontal ellipsis
        '\xa0': ' ',  # Non-breaking space
    }

    for unicode_char, ascii_char in replacements.items():
        text = text.replace(unicode_char, ascii_char)

    return text


def remove_control_characters(text: str) -> str:
    """
    Remove non-printable control characters except standard whitespace.

    Removes control characters (0x00-0x1F) except:
    - \\t (tab, 0x09)
    - \\n (newline, 0x0A)

    Also removes zero-width spaces and soft hyphens.

    Args:
        text: Input markdown text

    Returns:
        Text without control characters

    Example:
        >>> remove_control_characters("Hello\\x00World")
        'HelloWorld'
    """
    # Remove control characters except tab and newline
    # Pattern matches: 0x00-0x08, 0x0B-0x0C, 0x0E-0x1F
    text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f]', '', text)

    # Remove zero-width characters
    text = text.replace('\u200b', '')  # Zero-width space
    text = text.replace('\u200c', '')  # Zero-width non-joiner
    text = text.replace('\u200d', '')  # Zero-width joiner
    text = text.replace('\ufeff', '')  # Zero-width no-break space (BOM)

    # Remove soft hyphens
    text = text.replace('\xad', '')

    return text


def normalize_headings(text: str) -> str:
    """
    Normalize heading syntax to ATX-style with consistent spacing.

    Ensures:
    - Space after hash marks: ##Heading -> ## Heading
    - No trailing hashes: ## Heading ## -> ## Heading
    - Consistent blank line before headings (except at document start)

    Args:
        text: Input markdown text

    Returns:
        Text with normalized heading syntax

    Example:
        >>> normalize_headings("##No Space\\n###  Too Many Spaces  ###")
        '## No Space\\n### Too Many Spaces'
    """
    lines = text.split('\n')
    normalized_lines = []

    for i, line in enumerate(lines):
        # Check if line is a heading (starts with 1-6 # characters)
        # Use .*? (non-greedy) to capture content, allowing empty headings
        # The (?:\s*#+\s*)? at the end optionally matches trailing hashes with spaces
        heading_match = re.match(r'^(#{1,6})\s*(.*?)(?:\s*#+\s*)?$', line)

        if heading_match:
            hashes, content = heading_match.groups()

            # Skip if heading has no actual content after stripping
            if not content.strip():
                normalized_lines.append(line)
                continue

            # Normalize: single space after hashes, remove trailing hashes
            normalized_heading = f"{hashes} {content.strip()}"

            # Ensure blank line before heading (except at start or after blank line)
            if i > 0 and normalized_lines and normalized_lines[-1].strip():
                normalized_lines.append('')

            normalized_lines.append(normalized_heading)
        else:
            normalized_lines.append(line)

    return '\n'.join(normalized_lines)


def normalize_spacing(text: str) -> str:
    """
    Normalize spacing for consistent, reproducible formatting.

    Ensures:
    - Maximum 2 consecutive blank lines
    - No trailing whitespace on lines
    - File ends with single newline
    - Consistent paragraph spacing

    Args:
        text: Input markdown text

    Returns:
        Text with normalized spacing

    Example:
        >>> normalize_spacing("line1  \\n\\n\\n\\n\\nline2")
        'line1\\n\\n\\nline2\\n'
    """
    # Remove trailing whitespace from each line
    lines = [line.rstrip() for line in text.split('\n')]

    # Collapse excessive blank lines (3+ consecutive -> 2)
    normalized_lines = []
    blank_count = 0

    for line in lines:
        if not line:  # Blank line
            blank_count += 1
            if blank_count <= 2:
                normalized_lines.append(line)
        else:
            blank_count = 0
            normalized_lines.append(line)

    # Join lines and ensure file ends with single newline
    result = '\n'.join(normalized_lines)

    # Ensure exactly one trailing newline
    result = result.rstrip('\n') + '\n'

    return result


def clean_frontmatter_spacing(text: str) -> str:
    """
    Ensure consistent spacing around YAML frontmatter.

    Ensures exactly one blank line after the closing --- of frontmatter.

    Args:
        text: Input markdown text with frontmatter

    Returns:
        Text with normalized frontmatter spacing

    Example:
        >>> clean_frontmatter_spacing("---\\ntitle: Test\\n---\\n\\n\\n# Heading")
        '---\\ntitle: Test\\n---\\n\\n# Heading'
    """
    # Match frontmatter: ---\n...content...\n---
    frontmatter_pattern = re.compile(
        r'^(---\n.*?\n---)\n+',
        re.DOTALL | re.MULTILINE
    )

    # Replace with frontmatter followed by exactly one blank line
    text = frontmatter_pattern.sub(r'\1\n\n', text)

    return text


def clean_markdown(text: str) -> str:
    """
    Apply all markdown cleaning operations in the correct order.

    This is the main entry point for markdown cleaning. It applies all
    conservative normalization steps to ensure RAG-compatible output:

    1. Normalize line endings (\\n)
    2. Ensure UTF-8 encoding
    3. Remove control characters
    4. Normalize heading syntax
    5. Normalize spacing
    6. Clean frontmatter spacing

    Args:
        text: Raw markdown text

    Returns:
        Cleaned and normalized markdown text

    Example:
        >>> clean_markdown("\\ufeff##Heading\\r\\nContent\\x00")
        '## Heading\\nContent\\n'
    """
    # Step 1: Normalize line endings (must be first)
    text = normalize_line_endings(text)

    # Step 2: Ensure UTF-8 encoding
    text = ensure_utf8(text)

    # Step 3: Remove control characters
    text = remove_control_characters(text)

    # Step 4: Normalize heading syntax
    text = normalize_headings(text)

    # Step 5: Normalize spacing
    text = normalize_spacing(text)

    # Step 6: Clean frontmatter spacing (if present)
    text = clean_frontmatter_spacing(text)

    return text


def clean_markdown_file(input_path: str, output_path: str = None) -> None:
    """
    Clean a markdown file in place or write to a new file.

    Args:
        input_path: Path to input markdown file
        output_path: Path to output file (if None, overwrites input)

    Example:
        >>> clean_markdown_file("input.md", "output.md")
    """
    with open(input_path, 'r', encoding='utf-8') as f:
        text = f.read()

    cleaned_text = clean_markdown(text)

    output = output_path or input_path
    with open(output, 'w', encoding='utf-8', newline='\n') as f:
        f.write(cleaned_text)
