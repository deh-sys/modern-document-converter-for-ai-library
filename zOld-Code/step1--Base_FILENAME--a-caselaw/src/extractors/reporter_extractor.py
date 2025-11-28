"""
Reporter citation extraction module.
Extracts volume, reporter, and page number from PDF text.
Formats as: volume_reporter_page (e.g., 743_FSupp2d_762)
"""

import re


class ReporterExtractor:
    """Extract reporter citations with volume and page numbers."""

    def __init__(self):
        """Initialize reporter extractor with patterns."""
        self.patterns = self._build_patterns()

    def _build_patterns(self):
        """
        Build regex patterns for all reporter citations.

        Returns:
            list: List of (pattern, reporter_name, has_volume) tuples
        """
        patterns = []

        # Federal Supreme Court
        # Note: Match both "U.S." and "US" (with and without periods)
        patterns.extend([
            (r'(\d+)\s+U\.?S\.?\s+(\d+)', 'U.S.', True),  # Matches both "U.S." and "US"
            (r'(\d+)\s+S\.\s*Ct\.\s+(\d+)', 'S.Ct.', True),
            (r'(\d+)\s+L\.\s*Ed\.\s*2d\s+(\d+)', 'L.Ed.2d', True),
            (r'(\d+)\s+L\.\s*Ed\.\s+(\d+)', 'L.Ed.', True),
        ])

        # Federal Courts of Appeals
        patterns.extend([
            (r'(\d+)\s+F\.\s*4th\s+(\d+)', 'F.4th', True),
            (r'(\d+)\s+F\.\s*3d\s+(\d+)', 'F.3d', True),
            (r'(\d+)\s+F\.\s*2d\s+(\d+)', 'F.2d', True),
            (r'(\d+)\s+F\.\s+(\d+)', 'F.', True),
            (r'(\d+)\s+Fed\.\s*Appx\.\s+(\d+)', 'Fed.Appx.', True),
        ])

        # Federal District Courts
        patterns.extend([
            (r'(\d+)\s+F\.\s*Supp\.\s*3d\s+(\d+)', 'F.Supp.3d', True),
            (r'(\d+)\s+F\.\s*Supp\.\s*2d\s+(\d+)', 'F.Supp.2d', True),
            (r'(\d+)\s+F\.\s*Supp\.\s+(\d+)', 'F.Supp.', True),
            (r'(\d+)\s+F\.\s*R\.\s*D\.\s+(\d+)', 'F.R.D.', True),
        ])

        # Regional Reporters - South Eastern
        patterns.extend([
            (r'(\d+)\s+S\.E\.\s*2d\s+(\d+)', 'S.E.2d', True),
            (r'(\d+)\s+S\.E\.\s+(\d+)', 'S.E.', True),
        ])

        # Regional Reporters - North Eastern
        patterns.extend([
            (r'(\d+)\s+N\.E\.\s*3d\s+(\d+)', 'N.E.3d', True),
            (r'(\d+)\s+N\.E\.\s*2d\s+(\d+)', 'N.E.2d', True),
            (r'(\d+)\s+N\.E\.\s+(\d+)', 'N.E.', True),
        ])

        # Regional Reporters - Pacific
        patterns.extend([
            (r'(\d+)\s+P\.\s*3d\s+(\d+)', 'P.3d', True),
            (r'(\d+)\s+P\.\s*2d\s+(\d+)', 'P.2d', True),
            (r'(\d+)\s+P\.\s+(\d+)', 'P.', True),
        ])

        # Regional Reporters - Atlantic
        patterns.extend([
            (r'(\d+)\s+A\.\s*3d\s+(\d+)', 'A.3d', True),
            (r'(\d+)\s+A\.\s*2d\s+(\d+)', 'A.2d', True),
            (r'(\d+)\s+A\.\s+(\d+)', 'A.', True),
        ])

        # Regional Reporters - South Western
        patterns.extend([
            (r'(\d+)\s+S\.W\.\s*3d\s+(\d+)', 'S.W.3d', True),
            (r'(\d+)\s+S\.W\.\s*2d\s+(\d+)', 'S.W.2d', True),
            (r'(\d+)\s+S\.W\.\s+(\d+)', 'S.W.', True),
        ])

        # Regional Reporters - North Western
        patterns.extend([
            (r'(\d+)\s+N\.W\.\s*2d\s+(\d+)', 'N.W.2d', True),
            (r'(\d+)\s+N\.W\.\s+(\d+)', 'N.W.', True),
        ])

        # Regional Reporters - Southern
        patterns.extend([
            (r'(\d+)\s+So\.\s*3d\s+(\d+)', 'So.3d', True),
            (r'(\d+)\s+So\.\s*2d\s+(\d+)', 'So.2d', True),
            (r'(\d+)\s+So\.\s+(\d+)', 'So.', True),
        ])

        # State Specific - Georgia
        patterns.extend([
            (r'(\d+)\s+Ga\.\s*App\.\s+(\d+)', 'Ga.App.', True),
            (r'(\d+)\s+Ga\.\s+(\d+)', 'Ga.', True),
        ])

        # State Specific - California
        patterns.extend([
            (r'(\d+)\s+Cal\.\s*Rptr\.\s*3d\s+(\d+)', 'Cal.Rptr.3d', True),
            (r'(\d+)\s+Cal\.\s*Rptr\.\s*2d\s+(\d+)', 'Cal.Rptr.2d', True),
            (r'(\d+)\s+Cal\.\s*Rptr\.\s+(\d+)', 'Cal.Rptr.', True),
            (r'(\d+)\s+Cal\.\s*App\.\s+(\d+)', 'Cal.App.', True),
            (r'(\d+)\s+Cal\.\s+(\d+)', 'Cal.', True),
        ])

        # State Specific - New York
        patterns.extend([
            (r'(\d+)\s+N\.Y\.S\.\s*3d\s+(\d+)', 'N.Y.S.3d', True),
            (r'(\d+)\s+N\.Y\.S\.\s*2d\s+(\d+)', 'N.Y.S.2d', True),
            (r'(\d+)\s+N\.Y\.S\.\s+(\d+)', 'N.Y.S.', True),
            (r'(\d+)\s+N\.Y\.\s+(\d+)', 'N.Y.', True),
        ])

        # Online Databases - LEXIS (no volume)
        patterns.extend([
            (r'(\d{4})\s+Ga\.\s*State\s+LEXIS\s+(\d+)', 'Ga.State.LEXIS', True),  # State-specific LEXIS
            (r'U\.S\.\s*Dist\.\s*LEXIS\s+(\d+)', 'U.S.Dist.LEXIS', False),
            (r'U\.S\.\s*App\.\s*LEXIS\s+(\d+)', 'U.S.App.LEXIS', False),
            (r'LEXIS\s+(\d+)', 'LEXIS', False),
        ])

        # Online Databases - Westlaw
        patterns.extend([
            (r'(\d{4})\s+WL\s+(\d+)', 'WL', True),
        ])

        return patterns

    def extract_from_pdf(self, pdf_text):
        """
        Extract reporter citation from PDF text.
        Prioritizes citations in the first ~1000 characters (case header).

        Args:
            pdf_text: Extracted PDF text

        Returns:
            tuple: (volume, reporter, page) or None
        """
        if not pdf_text:
            return None

        # First, try to find reporter in the header/beginning (first 1000 chars)
        # This avoids picking up case citations from the body
        header_text = pdf_text[:1000]

        for pattern, reporter_name, has_volume in self.patterns:
            match = re.search(pattern, header_text)
            if match:
                if has_volume:
                    volume = match.group(1)
                    page = match.group(2)
                    return (volume, reporter_name, page)
                else:
                    # LEXIS citations - no volume
                    page = match.group(1)
                    return (None, reporter_name, page)

        # If not found in header, search full text
        for pattern, reporter_name, has_volume in self.patterns:
            match = re.search(pattern, pdf_text)
            if match:
                if has_volume:
                    volume = match.group(1)
                    page = match.group(2)
                    return (volume, reporter_name, page)
                else:
                    # LEXIS citations - no volume
                    page = match.group(1)
                    return (None, reporter_name, page)

        return None

    def extract_from_filename(self, filename):
        """
        Extract reporter citation from filename.

        Args:
            filename: Original filename

        Returns:
            tuple: (volume, reporter, page) or None
        """
        # Try to find LEXIS citation
        lexis_match = re.search(
            r'(\d{4})\s+U\.S\.\s*Dist\.\s*LEXIS\s+(\d+)',
            filename
        )
        if lexis_match:
            year = lexis_match.group(1)
            number = lexis_match.group(2)
            return (None, 'U.S.Dist.LEXIS', number)

        # Try Westlaw
        wl_match = re.search(r'(\d{4})\s+WL\s+(\d+)', filename)
        if wl_match:
            year = wl_match.group(1)
            number = wl_match.group(2)
            return (year, 'WL', number)

        return None

    def format_citation(self, volume, reporter, page):
        """
        Format citation as: volume_reporter_page

        Args:
            volume: Volume number (or None for LEXIS)
            reporter: Reporter abbreviation (e.g., "F.Supp.2d")
            page: Page number

        Returns:
            str: Formatted citation (e.g., "743_FSupp2d_762")
        """
        if not reporter or not page:
            return "Unpub"

        # Remove dots and spaces from reporter
        reporter_clean = reporter.replace('.', '').replace(' ', '')

        if volume:
            return f"{volume}_{reporter_clean}_{page}"
        else:
            # LEXIS citations without volume
            return f"{reporter_clean}_{page}"
