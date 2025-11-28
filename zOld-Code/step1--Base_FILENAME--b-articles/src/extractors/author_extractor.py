"""
Author extraction module for law journal articles.
Extracts author names and affiliations from PDF/Word documents.
"""

import re
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Author name patterns (in order of preference)
AUTHOR_PATTERNS = [
    # Pattern 1: All-caps name with footnote marker (most reliable)
    # "LAURA I APPLEMAN*" or "MORRIS S. ARNOLD**"
    r'^([A-Z][A-Z\s\.]{5,50}?)\s*[\*†‡§¶]+\s*$',

    # Pattern 2: "By [NAME]" format (common in older articles)
    # "By MORRIS S. ARNOLD**"
    r'By\s+([A-Z][A-Za-z\s\.]+?)(?:\s*[\*†‡§¶]+)?(?:\n|$)',

    # Pattern 3: Title case name with footnote marker
    # "Morris S. Arnold*"
    r'^([A-Z][a-z]+(?:\s+[A-Z]\.)?(?:\s+[A-Z][a-z]+)+)\s*[\*†‡§¶]+\s*$',

    # Pattern 4: "Author:" or "Authors:" label
    r'(?:Author|Authors?):\s*([A-Z][A-Za-z\s,\.&]+?)(?:\n|$)',

    # Pattern 5: All-caps name (without footnote, less reliable)
    r'^([A-Z][A-Z\s\.]{8,40})$',
]

# Affiliation patterns (footnotes at bottom of first page)
AFFILIATION_PATTERNS = [
    # Pattern 1: "* Professor of Law, University Name"
    r'[\*†‡§¶]\s*(.{5,100}?,\s+[A-Z][A-Za-z\s,\.]+(?:University|College|School|Institute))',

    # Pattern 2: "* Associate Professor, Institution. J.D., School"
    r'[\*†‡§¶]\s*(.{5,200}?(?:Professor|Scholar|Fellow|Attorney|Counsel).+?\.)',

    # Pattern 3: Generic footnote with institutional info
    r'[\*†‡§¶]\s*([A-Z].{10,150}?(?:University|College|Law School))',
]

# Patterns to filter out (not author names)
FALSE_POSITIVE_PATTERNS = [
    r'^TABLE OF CONTENTS',
    r'^ABSTRACT',
    r'^INTRODUCTION',
    r'^CONCLUSION',
    r'^\d+',  # Page numbers
    r'^VOL\.',
    r'^[A-Z\s]+LAW\s+(?:REVIEW|JOURNAL)',

    # False author patterns
    r'^ABOUT THE AUTHORS?',
    r'^THE AUTHORS?$',
    r'^AUTHORS?$',
    r'FACULTY SCHOLARSHIP',
    r'DIGITAL REPOSITORY',
    r'ARTICLES BY',
    r'MAURER SCHOOL',
]


class AuthorExtractor:
    """Extract author names and affiliations from law journal articles."""

    def __init__(self):
        """Initialize author extractor."""
        pass

    def extract_from_document(self, document_text):
        """
        Extract author names and affiliations from document text.

        Args:
            document_text: Full extracted text from PDF or Word document

        Returns:
            dict: {'authors': [list of author names],
                   'affiliations': [list of affiliation strings],
                   'author_affiliations': [list of dicts with author+institution]}
        """
        if not document_text:
            logger.warning("No document text provided for author extraction")
            return {'authors': [], 'affiliations': [], 'author_affiliations': []}

        # Extract from first 2 pages only (where author info typically appears)
        first_pages = self._get_first_pages(document_text, max_chars=5000)

        # Extract author names
        authors = self._extract_author_names(first_pages)

        # Extract affiliations
        affiliations = self._extract_affiliations(first_pages)

        # Try to match authors with affiliations
        author_affiliations = self._match_authors_to_affiliations(authors, affiliations)

        return {
            'authors': authors,
            'affiliations': affiliations,
            'author_affiliations': author_affiliations
        }

    def extract_from_filename(self, filename):
        """
        Extract author name from filename (fallback method).

        Args:
            filename: Original filename

        Returns:
            str: Author name or None
        """
        # Common patterns in article filenames:
        # "Arnold_Law_and_Fact_1974.pdf"
        # "Lerner_Rise_of_Directed_Verdict_2013.pdf"
        # "B_Lerner_Remittitur_1976.pdf"

        # Remove extension
        name_stem = re.sub(r'\.(pdf|docx?)$', '', filename, flags=re.IGNORECASE)

        # Pattern: Author name at beginning before underscore or first capital word
        match = re.match(r'^([A-Z][A-Za-z]+(?:_[A-Z][A-Za-z]+)?)', name_stem)
        if match:
            author = match.group(1).replace('_', ' ')
            return author

        return None

    def format_author_for_filename(self, authors):
        """
        Format author name(s) for use in filename.
        Uses first author's last name only.

        Args:
            authors: List of author names

        Returns:
            str: Formatted author name for filename (e.g., "Arnold")
        """
        if not authors:
            return "Unknown"

        first_author = authors[0]

        # Extract last name (last word in the name)
        # "Morris S. Arnold" -> "Arnold"
        # "LAURA I APPLEMAN" -> "APPLEMAN"
        # "Renée Lettow Lerner" -> "Lerner"

        # Clean up the name first
        name = first_author.strip()

        # Remove footnote markers
        name = re.sub(r'[\*†‡§¶\d]+', '', name)

        # Split into words
        words = name.split()

        if not words:
            return "Unknown"

        # Take last word (surname)
        last_name = words[-1]

        # Remove any remaining special characters
        last_name = re.sub(r'[^\w]', '', last_name)

        # Title case (handle all-caps names)
        if last_name.isupper():
            last_name = last_name.title()

        return last_name

    # ===== HELPER METHODS =====

    def _get_first_pages(self, text, max_chars=5000):
        """Extract first N characters (approximately first 2 pages)."""
        return text[:max_chars]

    def _extract_author_names(self, text):
        """
        Extract author names using multiple patterns.

        Returns:
            list: Author names (strings)
        """
        authors = []

        # Split into lines for line-by-line matching
        lines = text.split('\n')[:50]  # First 50 lines only

        for line in lines:
            line_stripped = line.strip()

            # Try each pattern
            for pattern in AUTHOR_PATTERNS:
                match = re.match(pattern, line_stripped)
                if match:
                    author = match.group(1).strip()

                    # Filter out false positives
                    if self._is_valid_author_name(author) and author not in authors:
                        authors.append(author)
                        break  # Found author on this line, move to next line

        # If no authors found, try more aggressive pattern
        if not authors:
            authors = self._extract_authors_aggressive(text)

        return authors

    def _extract_authors_aggressive(self, text):
        """
        More aggressive author extraction for cases where standard patterns fail.
        Looks for all-caps names near the top of the document.
        """
        lines = text.split('\n')[:50]  # First 50 lines

        authors = []
        for line in lines:
            line = line.strip()

            # Look for all-caps names (likely author)
            # Must be 2-4 words, all capitals
            if re.match(r'^[A-Z][A-Z\s\.]{5,40}$', line):
                # Check it's not a section header
                if not any(re.search(pat, line) for pat in FALSE_POSITIVE_PATTERNS):
                    if line not in authors:
                        authors.append(line)
                        if len(authors) >= 3:  # Limit to 3 authors max in aggressive mode
                            break

        return authors

    def _is_valid_author_name(self, name):
        """Check if extracted name is likely a valid author name."""
        # Filter out false positives
        for pattern in FALSE_POSITIVE_PATTERNS:
            if re.search(pattern, name):
                return False

        # Must have at least one letter
        if not re.search(r'[A-Za-z]', name):
            return False

        # Must not be too short or too long
        if len(name) < 3 or len(name) > 50:
            return False

        # Must have at least one uppercase letter
        if not re.search(r'[A-Z]', name):
            return False

        return True

    def _extract_affiliations(self, text):
        """
        Extract author affiliations from footnotes.

        Returns:
            list: Affiliation strings
        """
        affiliations = []

        for pattern in AFFILIATION_PATTERNS:
            matches = re.finditer(pattern, text, re.MULTILINE)
            for match in matches:
                affiliation = match.group(1).strip()
                if affiliation and affiliation not in affiliations:
                    affiliations.append(affiliation)

        return affiliations

    def _match_authors_to_affiliations(self, authors, affiliations):
        """
        Attempt to match authors with their affiliations.

        Returns:
            list: Dicts with {'author': name, 'institution': affiliation}
        """
        matched = []

        for i, author in enumerate(authors):
            # Try to find affiliation for this author
            institution = None

            if i < len(affiliations):
                institution = affiliations[i]

            matched.append({
                'author': author,
                'institution': institution
            })

        return matched
