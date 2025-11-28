"""
Date/year extraction module.
Extracts publication year from law journal articles.
"""

import re
from datetime import datetime


class DateExtractor:
    """Extract publication year from law journal articles."""

    def __init__(self):
        """Initialize date extractor."""
        self.min_year = 1700
        self.max_year = 2025

    def extract_from_document(self, document_text):
        """
        Extract publication year from document text.

        Args:
            document_text: Extracted PDF or Word text

        Returns:
            int: 4-digit year or None
        """
        if not document_text:
            return None

        # Look in first page (where publication info typically appears)
        first_page = document_text[:2000]

        # Priority 1: Look for copyright year (most reliable for publication year)
        # e.g., "© 2008" or "Copyright © 2008"
        year = self._find_copyright_year(first_page)
        if year:
            return year

        # Priority 2: Look for year in journal citation format
        # e.g., "[2013]" or "Vol. 81...2013" in brackets/footer
        year = self._find_year_in_citation_format(first_page)
        if year:
            return year

        # Priority 3: Look for year in journal citation
        # e.g., "Vol. 81 No. 2" near "2013"
        year = self._find_year_near_volume(first_page)
        if year:
            return year

        # Priority 4: Look for year with month/date context
        # e.g., "February 2013", "January 15, 2024"
        year = self._find_publication_date(first_page)
        if year:
            return year

        # Priority 5: Find year in header area only (first 500 chars)
        # Avoid years from article content
        year = self._find_any_year(first_page[:500])
        if year:
            return year

        return None

    # Maintain old method name for compatibility
    def extract_from_pdf(self, pdf_text):
        """Alias for extract_from_document for backward compatibility."""
        return self.extract_from_document(pdf_text)

    def _find_publication_date(self, text):
        """
        Find publication date with month context.

        Returns:
            int: Year or None
        """
        # Pattern: "February 2013", "January 2024", etc.
        months = ['January', 'February', 'March', 'April', 'May', 'June',
                  'July', 'August', 'September', 'October', 'November', 'December']

        for month in months:
            # Month followed by year
            pattern = rf'{month}\s+(\d{{4}})'
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                year = match.group(1)
                if self._validate_year(year):
                    return int(year)

            # Month day, year
            pattern = rf'{month}\s+\d{{1,2}},\s+(\d{{4}})'
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                year = match.group(1)
                if self._validate_year(year):
                    return int(year)

        return None

    def _find_copyright_year(self, text):
        """
        Find copyright year.

        Returns:
            int: Year or None
        """
        # Pattern: "© 2008", "Copyright © 2008", "Copyright 2008"
        patterns = [
            r'©\s*(\d{4})',
            r'Copyright\s+©\s*(\d{4})',
            r'Copyright\s+(\d{4})',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                year = match.group(1)
                if self._validate_year(year):
                    return int(year)

        return None

    def _find_year_in_citation_format(self, text):
        """
        Find year in specific journal citation formats.
        These are highly reliable as they're publication metadata.

        Returns:
            int: Year or None
        """
        # Pattern 1: Year in brackets "[2013]" (common in law reviews)
        match = re.search(r'\[(\d{4})\]', text)
        if match:
            year = match.group(1)
            if self._validate_year(year):
                return int(year)

        # Pattern 2: "Vol. 84:397" format at bottom of page
        # Look for this in last 500 chars (footer area)
        footer = text[-500:]
        match = re.search(r'\[?Vol\.\s+\d+:(\d+)', footer, re.IGNORECASE)
        if match:
            # Extract the year from nearby text
            # Usually appears as "[Vol. 84:397" followed by year
            context = text[max(0, len(text)-800):]
            year_match = re.search(r'\[?Vol\.\s+\d+:\d+.*?(\d{4})', context, re.IGNORECASE)
            if year_match:
                year = year_match.group(1)
                if self._validate_year(year):
                    return int(year)

        # Pattern 3: Year in parentheses at end of line (publication info)
        # "(2013)" or "(2008)"
        match = re.search(r'\((\d{4})\)', text[:500])  # Header area only
        if match:
            year = match.group(1)
            if self._validate_year(year):
                return int(year)

        return None

    def _find_year_near_volume(self, text):
        """
        Find year near volume information.

        Returns:
            int: Year or None
        """
        # Look for pattern like "Vol. 81 No. 2" near a year
        # Extract context around "Vol."
        match = re.search(r'Vol\.\s+\d+.{0,50}?(\d{4})', text, re.IGNORECASE)
        if match:
            year = match.group(1)
            if self._validate_year(year):
                return int(year)

        return None

    def _find_any_year(self, text):
        """
        Find any valid 4-digit year in text.
        Returns most recent valid year found.

        Returns:
            int: Year or None
        """
        # Find all 4-digit numbers that could be years
        matches = re.finditer(r'\b(\d{4})\b', text)

        valid_years = []
        for match in matches:
            year = match.group(1)
            if self._validate_year(year):
                valid_years.append(int(year))

        # Return the most recent year (likely publication year)
        if valid_years:
            return max(valid_years)

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
            int: 4-digit year or None
        """
        # Article filenames often have year at end: "Arnold_Law_Fact_1974.pdf"
        # Or: "Lerner_Rise_of_Directed_Verdict_2013.pdf"

        # Look for year at end of filename (most common for articles)
        end_year_match = re.search(r'_(\d{4})(?:\.|$)', filename)
        if end_year_match:
            year = end_year_match.group(1)
            if self._validate_year(year):
                return int(year)

        # Generic 4-digit year search
        year_match = re.search(r'(\d{4})', filename)
        if year_match:
            year = year_match.group(1)
            if self._validate_year(year):
                return int(year)

        return None
