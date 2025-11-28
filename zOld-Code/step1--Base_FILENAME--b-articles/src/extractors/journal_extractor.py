"""
Journal metadata extraction module for law journal articles.
Extracts journal name, volume, issue, and page information.
"""

import re
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Journal name patterns
JOURNAL_PATTERNS = [
    # Pattern: "INDIANA LAW JOURNAL"
    r'([A-Z][A-Z\s&]+(?:LAW\s+)?(?:REVIEW|JOURNAL))',

    # Pattern: "The American Journal of Legal History"
    r'(The\s+[A-Z][A-Za-z\s]+\s+(?:Law\s+)?(?:Review|Journal))',

    # Pattern: "Georgetown Law Journal" or similar
    r'([A-Z][A-Za-z]+\s+Law\s+(?:Review|Journal))',
]

# Volume/Issue patterns
VOLUME_PATTERNS = [
    # Pattern: "Vol. 84" or "Volume 84"
    r'Vol(?:ume|\.)?\s+(\d+)',

    # Pattern: "[Vol. 84:397" (with bracket)
    r'\[Vol\.\s+(\d+)',

    # Pattern: "XVIII" (Roman numerals) - less common
    r'Vol\.\s+([IVXLCDM]+)',
]

ISSUE_PATTERNS = [
    # Pattern: "No. 2"
    r'No\.\s+(\d+)',

    # Pattern: "Issue 2"
    r'Issue\s+(\d+)',
]

# Page number patterns (from headers/footers)
PAGE_PATTERNS = [
    # Pattern: "[Vol. 84:397" (vol:page format)
    r'Vol\.\s+\d+:(\d+)',

    # Pattern: "397" in header/footer (page number alone)
    r'^(\d{1,4})$',  # Used in context with other matches
]


class JournalExtractor:
    """Extract journal metadata from law journal articles."""

    def __init__(self):
        """Initialize journal extractor."""
        pass

    def extract_from_document(self, document_text):
        """
        Extract journal metadata from document text.

        Args:
            document_text: Full extracted text from PDF or Word document

        Returns:
            dict: {'journal_name': str,
                   'volume': int or None,
                   'issue': int or None,
                   'page_start': int or None,
                   'page_end': int or None}
        """
        if not document_text:
            logger.warning("No document text provided for journal extraction")
            return self._empty_result()

        # Headers/footers typically repeat, so look in first few pages
        header_text = self._get_header_footer_text(document_text)

        result = {
            'journal_name': self._extract_journal_name(header_text),
            'volume': self._extract_volume(header_text),
            'issue': self._extract_issue(header_text),
            'page_start': self._extract_page_start(header_text),
            'page_end': None,  # Hard to determine without full document
        }

        return result

    def extract_from_filename(self, filename):
        """
        Extract journal info from filename (limited fallback).

        Args:
            filename: Original filename

        Returns:
            dict: Partial journal metadata
        """
        # Filenames rarely contain journal info, but try to extract year
        year_match = re.search(r'(\d{4})', filename)

        return {
            'journal_name': None,
            'volume': None,
            'issue': None,
            'page_start': None,
            'page_end': None,
            'year': int(year_match.group(1)) if year_match else None,
        }

    # ===== HELPER METHODS =====

    def _empty_result(self):
        """Return empty result structure."""
        return {
            'journal_name': None,
            'volume': None,
            'issue': None,
            'page_start': None,
            'page_end': None,
        }

    def _get_header_footer_text(self, text, max_chars=2000):
        """
        Extract text that's likely from headers/footers.
        Headers repeat, so we look at first few pages.
        """
        # Take first 2000 chars (roughly first 2 pages)
        return text[:max_chars]

    def _extract_journal_name(self, text):
        """
        Extract journal name.

        Returns:
            str: Journal name or None
        """
        for pattern in JOURNAL_PATTERNS:
            match = re.search(pattern, text)
            if match:
                journal_name = match.group(1).strip()
                # Clean up extra whitespace
                journal_name = re.sub(r'\s+', ' ', journal_name)
                return journal_name

        return None

    def _extract_volume(self, text):
        """
        Extract volume number.

        Returns:
            int: Volume number or None
        """
        for pattern in VOLUME_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                volume_str = match.group(1)

                # Handle Roman numerals
                if re.match(r'^[IVXLCDM]+$', volume_str):
                    volume = self._roman_to_int(volume_str)
                else:
                    try:
                        volume = int(volume_str)
                    except ValueError:
                        continue

                # Sanity check (volumes are typically 1-999)
                if 1 <= volume <= 999:
                    return volume

        return None

    def _extract_issue(self, text):
        """
        Extract issue number.

        Returns:
            int: Issue number or None
        """
        for pattern in ISSUE_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    issue = int(match.group(1))
                    # Sanity check (issues are typically 1-12)
                    if 1 <= issue <= 12:
                        return issue
                except ValueError:
                    continue

        return None

    def _extract_page_start(self, text):
        """
        Extract starting page number.

        Returns:
            int: Page number or None
        """
        # Look for Vol:Page format first (most reliable)
        match = re.search(r'Vol\.\s+\d+:(\d+)', text)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                pass

        # Look for standalone page numbers in likely header positions
        lines = text.split('\n')[:20]  # First 20 lines
        for line in lines:
            line = line.strip()
            # Look for 2-4 digit numbers (likely page numbers)
            if re.match(r'^\d{2,4}$', line):
                try:
                    page = int(line)
                    # Sanity check (pages typically 1-9999)
                    if 1 <= page <= 9999:
                        return page
                except ValueError:
                    continue

        return None

    def _roman_to_int(self, roman):
        """Convert Roman numeral to integer."""
        roman_values = {
            'I': 1, 'V': 5, 'X': 10, 'L': 50,
            'C': 100, 'D': 500, 'M': 1000
        }

        total = 0
        prev_value = 0

        for char in reversed(roman.upper()):
            value = roman_values.get(char, 0)
            if value < prev_value:
                total -= value
            else:
                total += value
            prev_value = value

        return total
