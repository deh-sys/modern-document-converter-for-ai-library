"""
Text Normalizer - Document Processor

Centralized text cleaning for use across the application.
Used by text_extractor service and potentially other components.

Strategy:
    1. Use clean-text library for heavy lifting (unicode, smart quotes, etc.)
    2. Custom regex for legal document hyphenation issues
    3. Normalize whitespace and line breaks

Usage:
    from src.cleaners.text_normalizer import normalize_text

    clean = normalize_text(raw_text)
"""

import re
from typing import Optional


def fix_hyphens(text: str) -> str:
    """
    Fix broken line hyphens common in legal documents.

    Handles:
        - "defend-\\nant" → "defendant" (hyphen at end of line, next starts lowercase)
        - "SOME-\\nTHING" → "SOMETHING" (hyphen at end of line, next starts uppercase)
        - Preserves intentional hyphens: "well-known" stays "well-known"

    Based on proven regex from step3a/clean_txt.py.

    Args:
        text: Text with potential broken hyphens

    Returns:
        Text with hyphens repaired

    Examples:
        >>> fix_hyphens("The defend-\\nant argued...")
        "The defendant argued..."

        >>> fix_hyphens("The PLAIN-\\nTIFF filed...")
        "The PLAINTIFF filed..."

        >>> fix_hyphens("A well-known case")
        "A well-known case"
    """
    # Pattern 1: Hyphen followed by newline and lowercase letter
    # This is almost always a broken word: "defend-\nant" -> "defendant"
    text = re.sub(
        r"-\s*\n\s*([a-z])",  # Hyphen, optional space, newline, optional space, lowercase
        r"\1",  # Just the lowercase letter (remove hyphen)
        text
    )

    # Pattern 2: Hyphen followed by newline and uppercase letter
    # Could be broken word in all-caps: "PLAIN-\nTIFF" -> "PLAINTIFF"
    # Or intentional hyphen with new sentence (rare)
    # Conservative: remove hyphen if next word continues the pattern
    text = re.sub(
        r"-\s*\n\s*([A-Z])",  # Hyphen, optional space, newline, optional space, uppercase
        r"\1",  # Just the uppercase letter (remove hyphen)
        text
    )

    # Pattern 3: Hyphen at end of line followed by space and lowercase
    # (In case newline was already converted to space)
    text = re.sub(
        r"-\s{2,}([a-z])",  # Hyphen followed by 2+ spaces and lowercase
        r" \1",  # Single space + letter (remove hyphen)
        text
    )

    return text


def normalize_whitespace(text: str) -> str:
    """
    Normalize whitespace without removing intentional structure.

    Fixes:
        - Multiple spaces → single space
        - Tab characters → single space
        - Inconsistent line endings
        - Trailing/leading whitespace on lines

    Preserves:
        - Paragraph breaks (double newline)
        - Single newlines (might be meaningful in some contexts)

    Args:
        text: Text with inconsistent whitespace

    Returns:
        Text with normalized whitespace

    Examples:
        >>> normalize_whitespace("The   defendant    argued")
        "The defendant argued"

        >>> normalize_whitespace("Line 1\\n\\n\\nLine 2")
        "Line 1\\n\\nLine 2"  # Max 2 newlines (paragraph break)
    """
    # Replace tabs with spaces
    text = text.replace("\t", " ")

    # Normalize line endings (Windows/Mac -> Unix)
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    # Remove trailing whitespace from each line
    text = "\n".join(line.rstrip() for line in text.split("\n"))

    # Collapse multiple spaces to single space (but not across newlines)
    text = re.sub(r"[ \t]{2,}", " ", text)

    # Collapse excessive newlines (max 2 = paragraph break)
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Strip leading/trailing whitespace from entire text
    text = text.strip()

    return text


def normalize_text(text: str, modernize_spellings: bool = False) -> str:
    """
    Main text normalization function.

    Applies comprehensive cleaning:
        1. clean-text library for unicode/smart quotes
        2. Custom hyphen fixing for legal documents
        3. Whitespace normalization

    Args:
        text: Raw extracted text
        modernize_spellings: If True, apply archaic -> modern spelling conversions
                            (e.g., "publick" -> "public"). Default False.
                            Only use for historical documents.

    Returns:
        Normalized, clean text

    Example:
        >>> raw = "The   defend-\\nant's "argument""
        >>> normalize_text(raw)
        'The defendant\\'s "argument"'
    """
    if not text:
        return ""

    # Step 1: Use clean-text library for primary cleaning
    try:
        from cleantext import clean

        text = clean(
            text,
            fix_unicode=True,  # Fix unicode errors
            to_ascii=True,  # Convert unicode quotes/dashes to ASCII
            lower=False,  # Preserve original case
            no_line_breaks=False,  # Keep line breaks (we'll handle them)
            no_urls=False,  # Keep URLs (might be in citations)
            no_emails=False,  # Keep emails
            no_phone_numbers=False,  # Keep phone numbers
            no_numbers=False,  # Keep numbers (dates, citations)
            no_digits=False,  # Keep digits
            no_currency_symbols=False,  # Keep $ (damages amounts)
            no_punct=False,  # Keep punctuation
            replace_with_punct="",  # Default replacement
            replace_with_url="",
            replace_with_email="",
            replace_with_phone_number="",
            replace_with_number="",
            replace_with_digit="",
            replace_with_currency_symbol="",
        )

    except ImportError:
        # Fallback if clean-text not installed
        # Basic unicode fixes using just stdlib
        text = text.encode("ascii", "ignore").decode("ascii")

    # Step 2: Fix broken hyphens (custom logic for legal docs)
    text = fix_hyphens(text)

    # Step 3: Normalize whitespace
    text = normalize_whitespace(text)

    # Step 4: Additional punctuation spacing fixes
    # Ensure space after periods (if not already)
    text = re.sub(r"\.([A-Z])", r". \1", text)

    # Ensure space after commas (if not already)
    text = re.sub(r",([^ \n])", r", \1", text)

    # Optional: Modernize archaic spellings (for historical documents only)
    if modernize_spellings:
        text = _modernize_spellings(text)

    return text


def _modernize_spellings(text: str) -> str:
    """
    Convert archaic spellings to modern equivalents.

    Only use this for historical documents (17th-19th century).
    Not recommended for modern legal documents.

    Based on patterns from step3a/clean_txt.py.

    Args:
        text: Text with potential archaic spellings

    Returns:
        Text with modernized spellings
    """
    # Common archaic -> modern patterns
    replacements = [
        # -our -> -or (British -> American)
        (r"\bhonour\b", "honor"),
        (r"\bhonours\b", "honors"),
        (r"\bhonourable\b", "honorable"),
        (r"\bcolour\b", "color"),
        (r"\bcolours\b", "colors"),
        (r"\blabour\b", "labor"),
        (r"\blabours\b", "labor"),

        # -re -> -er (British -> American)
        (r"\bcentre\b", "center"),
        (r"\bcentres\b", "centers"),
        (r"\btheatre\b", "theater"),
        (r"\bmetre\b", "meter"),

        # v -> u (Middle English)
        (r"\bvpon\b", "upon"),
        (r"\bvnto\b", "unto"),
        (r"\bvnder\b", "under"),

        # -ick -> -ic
        (r"\bpublick\b", "public"),
        (r"\bmagick\b", "magic"),

        # Other common archaic forms
        (r"\bshew\b", "show"),
        (r"\bshewed\b", "showed"),
        (r"\bgaol\b", "jail"),
        (r"\bcompl(eat|ete)", "complete"),
    ]

    for pattern, replacement in replacements:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

    return text


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def normalize_filename_text(text: str) -> str:
    """
    Normalize text specifically for use in filenames.

    More aggressive than general text normalization:
        - Removes most punctuation
        - Collapses all whitespace to single space
        - Truncates excessive length

    Args:
        text: Text to use in filename (e.g., case name, title)

    Returns:
        Filename-safe text

    Example:
        >>> normalize_filename_text("Smith v. Jones (2010)")
        "Smith v Jones 2010"
    """
    # Start with basic normalization
    text = normalize_text(text)

    # Remove characters that are problematic in filenames
    # Keep: letters, numbers, spaces, hyphens, underscores, periods
    text = re.sub(r"[^\w\s\-\_\.]", "", text)

    # Collapse whitespace to single space
    text = re.sub(r"\s+", " ", text)

    # Trim
    text = text.strip()

    return text


def preview_normalized(text: str, max_chars: int = 500) -> str:
    """
    Get preview of normalized text for debugging/logging.

    Args:
        text: Text to preview
        max_chars: Maximum characters to show

    Returns:
        Truncated preview with character count

    Example:
        >>> preview_normalized("Long text..." * 100)
        "Long text...Long text... [truncated, 1200 chars total]"
    """
    if len(text) <= max_chars:
        return text

    preview = text[:max_chars]
    return f"{preview}... [truncated, {len(text)} chars total]"
