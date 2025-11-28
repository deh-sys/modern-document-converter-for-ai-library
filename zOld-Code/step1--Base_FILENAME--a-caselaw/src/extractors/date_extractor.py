"""
Date/year extraction module.
Extracts decision year from PDF text, avoiding margin dates.
"""

import re
from datetime import datetime


class DateExtractor:
    """Extract decision year from PDF text."""

    def __init__(self):
        """Initialize date extractor."""
        self.min_year = 1700
        self.max_year = 2025

    def extract_from_pdf(self, pdf_text):
        """
        Extract decision year from PDF text.

        Args:
            pdf_text: Extracted PDF text

        Returns:
            str: 4-digit year or None
        """
        if not pdf_text:
            return None

        # Priority 1: Look for "Decided:" date
        year = self._find_labeled_date(pdf_text, 'Decided')
        if year:
            return year

        # Priority 2: Look for "Filed:" date
        year = self._find_labeled_date(pdf_text, 'Filed')
        if year:
            return year

        # Priority 3: Look for "Dated:" date
        year = self._find_labeled_date(pdf_text, 'Dated')
        if year:
            return year

        return None

    def _find_labeled_date(self, text, label):
        """
        Find date with specific label (e.g., "Decided:", "Filed:").

        Args:
            text: PDF text
            label: Label to search for (e.g., "Decided", "Filed")

        Returns:
            str: 4-digit year or None
        """
        # Pattern: "Decided: Month Day, Year" or "Decided Month Day, Year"
        # Also: "Month Day, Year, Decided" (date before label)
        patterns = [
            rf'{label}:\s*([A-Z][a-z]+\s+\d{{1,2}},\s+(\d{{4}}))',
            rf'{label}\s+([A-Z][a-z]+\s+\d{{1,2}},\s+(\d{{4}}))',
            rf'([A-Z][a-z]+\s+\d{{1,2}},\s+(\d{{4}})),?\s+{label}',  # Date before label
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                year = match.group(2)
                if self._validate_year(year):
                    return year

        return None

    def _validate_year(self, year_str):
        """
        Validate that year is reasonable.

        Args:
            year_str: Year string

        Returns:
            bool: True if valid
        """
        try:
            year = int(year_str)
            return self.min_year <= year <= self.max_year
        except (ValueError, TypeError):
            return False

    def extract_from_filename(self, filename):
        """
        Extract year from filename as fallback.

        Args:
            filename: Original filename

        Returns:
            str: 4-digit year or None
        """
        # Look for year in parenthetical: (ND Ill 2010)
        paren_match = re.search(r'\(.*?(\d{4})\)', filename)
        if paren_match:
            year = paren_match.group(1)
            if self._validate_year(year):
                return year

        # Look for year in LEXIS citation: 2019 U.S. Dist. LEXIS
        lexis_match = re.search(r'(\d{4})\s+U\.S\.\s+Dist\.\s+LEXIS', filename)
        if lexis_match:
            year = lexis_match.group(1)
            if self._validate_year(year):
                return year

        # Look for year in Westlaw citation: 2019 WL
        wl_match = re.search(r'(\d{4})\s+WL', filename)
        if wl_match:
            year = wl_match.group(1)
            if self._validate_year(year):
                return year

        # Generic 4-digit year search
        year_match = re.search(r'(\d{4})', filename)
        if year_match:
            year = year_match.group(1)
            if self._validate_year(year):
                return year

        return None
