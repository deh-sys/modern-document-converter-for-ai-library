"""
Title extraction module for law journal articles.
Extracts article titles from PDF/Word documents.
"""

import re
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Patterns to identify likely titles
TITLE_INDICATORS = [
    # Titles often appear before these markers
    'ABSTRACT',
    'TABLE OF CONTENTS',
    'INTRODUCTION',
    r'By\s+[A-Z]',  # "By [Author]"
    r'[A-Z][A-Z\s\.]+\*',  # Author with footnote marker
]

# Patterns to filter out (not titles)
FALSE_POSITIVE_PATTERNS = [
    r'^\d+$',  # Just numbers
    r'^Page\s+\d+',
    r'^\w{1,2}$',  # Single or two letters
    r'^Vol\.',
    r'^No\.',
    r'^\d{4}$',  # Just year
    r'^[A-Z]{1,3}\s+LAW\s+(?:REVIEW|JOURNAL)',  # Journal name

    # Repository headers
    r'Digital Repository',
    r'Follow this',
    r'Recommended Citation',
    r'This Article',
    r'Maurer School of Law',
    r'Part of the.*Commons',  # "Part of the Courts Commons, European Law Commons..."
    r'Faculty Scholarship',
    r'Articles by.*Faculty',
    r'brought to you',

    # Table of contents and section markers
    r'^(?:TABLE OF )?CONTENTS?',
    r'^INTRODUCTION\s*\.{3,}',  # "INTRODUCTION....397"
    r'^CONCLUSION\s*\.{3,}',
    r'^[IVX]+\.',  # Roman numerals: I., II., III., IV.
    r'^[A-D]\.',  # Section markers: A., B., C., D.
    r'^\d+\.',  # Numbered sections: 1., 2., 3.

    r'^\s*$',  # Empty
]


class TitleExtractor:
    """Extract article titles from law journal articles."""

    def __init__(self):
        """Initialize title extractor."""
        pass

    def extract_from_document(self, document_text):
        """
        Extract article title from document text.

        Args:
            document_text: Full extracted text from PDF or Word document

        Returns:
            str: Article title or None
        """
        if not document_text:
            logger.warning("No document text provided for title extraction")
            return None

        # Extract from first page only (where title always appears)
        first_page = self._get_first_page(document_text, max_chars=3000)

        # Try multiple strategies
        title = self._extract_title_by_position(first_page)

        if not title:
            title = self._extract_title_by_pattern(first_page)

        if not title:
            title = self._extract_title_aggressive(first_page)

        return title

    def extract_from_filename(self, filename):
        """
        Extract title from filename (fallback method).

        Args:
            filename: Original filename

        Returns:
            str: Title or None
        """
        # Remove extension
        name_stem = re.sub(r'\.(pdf|docx?)$', '', filename, flags=re.IGNORECASE)

        # Common patterns:
        # "Author_Title_Words_Year.pdf"
        # Remove author name (first word or two)
        # Remove year (last 4 digits)

        # Remove year if present
        name_stem = re.sub(r'_\d{4}$', '', name_stem)

        # Split by underscore
        parts = name_stem.split('_')

        # Assume first 1-2 parts are author name, rest is title
        if len(parts) > 2:
            # Skip first part (author), take rest as title
            title_parts = parts[1:]
            title = ' '.join(title_parts)
            return title
        elif len(parts) == 2:
            # Just author and one word
            return parts[1]

        return None

    # ===== HELPER METHODS =====

    def _get_first_page(self, text, max_chars=3000):
        """Extract first N characters (approximately first page)."""
        return text[:max_chars]

    def _extract_title_by_position(self, text):
        """
        Extract title by looking at lines near top of document.
        Title is often one of the first substantive lines.
        """
        lines = text.split('\n')

        # Strategy 1: Look for title line BEFORE author name line
        # This is very reliable
        for i, line in enumerate(lines[:50]):
            line_stripped = line.strip()

            # Check if this line looks like an author name
            # Patterns: "MORRIS S. ARNOLD**", "By MORRIS S. ARNOLD**", "LAURA I APPLEMAN*"
            is_author_line = (
                re.match(r'^([A-Z][A-Z\s\.]+)\s*[\*†‡§¶]+\s*$', line_stripped) or
                re.match(r'^By\s+([A-Z][A-Za-z\s\.]+)', line_stripped, re.IGNORECASE)
            )

            if is_author_line:
                # Found author line! Look backward for title
                # Check up to 10 lines back to handle repository headers
                for j in range(i-1, max(0, i-10), -1):
                    prev_line = lines[j].strip()

                    # Skip empty lines
                    if not prev_line:
                        continue

                    # Skip false positives
                    if any(re.search(pat, prev_line, re.IGNORECASE) for pat in FALSE_POSITIVE_PATTERNS):
                        continue

                    # Skip lines with email addresses or URLs (repository info)
                    if re.search(r'[@\.](?:edu|com|org)', prev_line, re.IGNORECASE):
                        continue

                    # Check if this could be the title
                    # Allow footnote markers at end (title often has footnote)
                    if (10 <= len(prev_line) <= 200 and
                        len(prev_line.split()) >= 3 and
                        re.match(r'[A-Z]', prev_line)):
                        # Check if it's a partial title (e.g., "Trial: Out of Sight, Out of Mind. *")
                        # Look for previous line to combine
                        if j > 0:
                            prev_prev_line = lines[j-1].strip()
                            # If previous line also looks like title text, combine them
                            if (prev_prev_line and
                                len(prev_prev_line.split()) >= 2 and
                                re.match(r'[A-Z]', prev_prev_line) and
                                not any(re.search(pat, prev_prev_line, re.IGNORECASE) for pat in FALSE_POSITIVE_PATTERNS)):
                                combined = prev_prev_line + ' ' + prev_line
                                return self._clean_title(combined)

                        return self._clean_title(prev_line)

        # Strategy 2: Look through first 40 lines for candidate titles
        candidate_titles = []

        for i, line in enumerate(lines[:40]):
            line = line.strip()

            # Skip empty lines
            if not line:
                continue

            # Skip obvious non-titles
            if any(re.search(pat, line, re.IGNORECASE) for pat in FALSE_POSITIVE_PATTERNS):
                continue

            # Title characteristics:
            # 1. Between 10 and 200 characters
            # 2. Contains at least 2 words
            # 3. Starts with capital letter
            # 4. Doesn't have footnote markers (*, †, etc.)

            if (10 <= len(line) <= 200 and
                len(line.split()) >= 2 and
                re.match(r'[A-Z]', line) and
                not re.search(r'[\*†‡§¶]', line)):

                # Check if line appears before author or abstract
                remaining_text = '\n'.join(lines[i+1:i+10])
                if any(re.search(indicator, remaining_text, re.IGNORECASE)
                       for indicator in TITLE_INDICATORS):
                    # This is likely the title
                    return self._clean_title(line)

                # Store as candidate
                candidate_titles.append((i, line))

        # If we found candidates, take the first substantial one
        for i, title in candidate_titles:
            # Prefer titles with at least 3 words
            if len(title.split()) >= 3:
                return self._clean_title(title)

        # Fall back to first candidate
        if candidate_titles:
            return self._clean_title(candidate_titles[0][1])

        return None

    def _extract_title_by_pattern(self, text):
        """
        Extract title using specific patterns.
        """
        # Pattern: Line in title case with colon (common for subtitled articles)
        # "The Rise of Directed Verdict: Jury Power in Civil Cases"
        match = re.search(
            r'([A-Z][A-Za-z\s,:\-\'\"]+(?::\s+[A-Z][A-Za-z\s,\-\'\"]+)?)\n',
            text
        )
        if match:
            title = match.group(1).strip()
            if len(title.split()) >= 3 and len(title) >= 15:
                # Make sure it's not a false positive
                if not any(re.search(pat, title, re.IGNORECASE) for pat in FALSE_POSITIVE_PATTERNS):
                    return self._clean_title(title)

        return None

    def _extract_title_aggressive(self, text):
        """
        Aggressive title extraction for difficult cases.
        Looks for any substantial text block in upper section.
        """
        lines = text.split('\n')[:30]

        for line in lines:
            line = line.strip()

            # Look for lines that are:
            # - Substantial length (20+ chars)
            # - Multiple words
            # - Not in the false positive list

            if len(line) >= 20 and len(line.split()) >= 3:
                if not any(re.search(pat, line, re.IGNORECASE) for pat in FALSE_POSITIVE_PATTERNS):
                    # Check if it looks like a title (has proper capitalization)
                    if re.match(r'[A-Z]', line):
                        return self._clean_title(line)

        return None

    def _clean_title(self, title):
        """
        Clean up extracted title.
        Remove extra whitespace, trailing punctuation, etc.
        """
        if not title:
            return None

        # Remove footnote markers
        title = re.sub(r'[\*†‡§¶\d]+$', '', title)

        # Remove trailing punctuation (except periods that are part of abbreviations)
        title = title.rstrip('.,;:')

        # Normalize whitespace
        title = re.sub(r'\s+', ' ', title)

        title = title.strip()

        return title if title else None
