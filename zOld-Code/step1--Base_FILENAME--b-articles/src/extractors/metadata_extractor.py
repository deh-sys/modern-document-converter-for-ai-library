"""
Metadata extraction module for law journal articles.
Extracts comprehensive metadata including abstract, keywords, DOI, and more.
"""

import re
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ===== REGEX PATTERNS AS CONSTANTS =====

# Abstract patterns
ABSTRACT_PATTERNS = [
    # Standard "ABSTRACT" heading
    r'ABSTRACT\s*\n((?:.+\n){1,50}?)(?:\n\n|TABLE OF CONTENTS|INTRODUCTION|I\.|[A-Z\s]+\n\n)',

    # Alternative headers
    r'Abstract\s*\n((?:.+\n){1,50}?)(?:\n\n|TABLE OF CONTENTS|INTRODUCTION)',

    # No header but starts after title/author
    # (harder to detect reliably)
]

# Keywords patterns
KEYWORDS_PATTERNS = [
    # "Keywords:" followed by comma-separated list
    r'Keywords?:\s*(.+?)(?:\n\n|\n[A-Z])',

    # Common alternative format
    r'Key [Ww]ords?[:\-]\s*(.+?)(?:\n\n|\n[A-Z])',
]

# DOI patterns
DOI_PATTERNS = [
    # Standard DOI format
    r'DOI:\s*(10\.\d{4,}/[^\s]+)',
    r'doi:\s*(10\.\d{4,}/[^\s]+)',

    # URL format
    r'https?://doi\.org/(10\.\d{4,}/[^\s]+)',

    # Just the DOI number
    r'\b(10\.\d{4,}/[^\s]+)\b',
]

# Citation recommendation patterns
CITATION_PATTERNS = [
    # "Recommended Citation"
    r'Recommended Citation[:\n]\s*(.+?)(?:\n\n|This Article)',

    # "Please cite as:"
    r'(?:Please\s+)?[Cc]ite\s+as:?\s*(.+?)(?:\n\n|$)',
]


class MetadataExtractor:
    """Extract comprehensive metadata from law journal articles."""

    def __init__(self, date_extractor=None, author_extractor=None):
        """
        Initialize metadata extractor.

        Args:
            date_extractor: Optional DateExtractor instance
            author_extractor: Optional AuthorExtractor instance
        """
        self.date_extractor = date_extractor
        self.author_extractor = author_extractor

    def extract_metadata(self, renamer_result, document_text):
        """
        Extract comprehensive metadata from document text.

        Args:
            renamer_result: Dictionary from ArticleRenamer.process_file()
            document_text: Full extracted text from PDF or Word

        Returns:
            dict: Complete metadata with all fields
        """
        if not document_text:
            logger.warning("No document text provided for metadata extraction")
            document_text = ""

        # Initialize metadata dict with renamer's values
        metadata = {
            'authors': renamer_result.get('authors', []),
            'title': renamer_result.get('title', ''),
            'journal_name': renamer_result.get('journal_name', ''),
            'volume': renamer_result.get('volume'),
            'issue': renamer_result.get('issue'),
            'year': renamer_result.get('year'),
            'page_start': renamer_result.get('page_start'),
            'page_end': renamer_result.get('page_end'),
            'extraction_timestamp': datetime.now().isoformat(),
            'source_file': renamer_result.get('original_filename', ''),
        }

        # Extract additional fields
        # Focus on first few pages where this info typically appears
        first_pages = document_text[:8000]

        # 1. Abstract
        try:
            abstract = self._extract_abstract(first_pages)
            metadata['abstract'] = abstract
        except Exception as e:
            logger.debug(f"Abstract extraction error: {e}")
            metadata['abstract'] = ''

        # 2. Keywords
        try:
            keywords = self._extract_keywords(first_pages)
            metadata['keywords'] = keywords
        except Exception as e:
            logger.debug(f"Keywords extraction error: {e}")
            metadata['keywords'] = []

        # 3. DOI
        try:
            doi = self._extract_doi(first_pages)
            metadata['doi'] = doi
        except Exception as e:
            logger.debug(f"DOI extraction error: {e}")
            metadata['doi'] = ''

        # 4. Recommended citation
        try:
            citation = self._extract_recommended_citation(first_pages)
            metadata['recommended_citation'] = citation
        except Exception as e:
            logger.debug(f"Citation extraction error: {e}")
            metadata['recommended_citation'] = ''

        # 5. Author affiliations (if author_extractor provided)
        if self.author_extractor:
            try:
                author_data = self.author_extractor.extract_from_document(first_pages)
                metadata['author_affiliations'] = author_data.get('author_affiliations', [])
                metadata['affiliations'] = author_data.get('affiliations', [])
            except Exception as e:
                logger.debug(f"Author affiliation extraction error: {e}")
                metadata['author_affiliations'] = []
                metadata['affiliations'] = []
        else:
            metadata['author_affiliations'] = []
            metadata['affiliations'] = []

        return metadata

    # ===== EXTRACTION METHODS =====

    def _extract_abstract(self, text):
        """
        Extract article abstract.

        Returns:
            str: Abstract text or empty string
        """
        for pattern in ABSTRACT_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
            if match:
                abstract = match.group(1).strip()

                # Clean up the abstract
                abstract = re.sub(r'\s+', ' ', abstract)  # Normalize whitespace

                # Must be at least 50 characters to be a real abstract
                if len(abstract) >= 50:
                    return abstract

        return ''

    def _extract_keywords(self, text):
        """
        Extract keywords.

        Returns:
            list: Keywords or empty list
        """
        for pattern in KEYWORDS_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                keywords_str = match.group(1).strip()

                # Split by comma or semicolon
                keywords = re.split(r'[,;]\s*', keywords_str)

                # Clean up each keyword
                keywords = [kw.strip() for kw in keywords if kw.strip()]

                # Filter out very long "keywords" (likely not real keywords)
                keywords = [kw for kw in keywords if len(kw) < 50]

                if keywords:
                    return keywords

        return []

    def _extract_doi(self, text):
        """
        Extract Digital Object Identifier (DOI).

        Returns:
            str: DOI or empty string
        """
        for pattern in DOI_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                doi = match.group(1).strip()

                # Clean up DOI
                doi = doi.rstrip('.,;)')  # Remove trailing punctuation

                # Validate format (should start with 10.)
                if doi.startswith('10.'):
                    return doi

        return ''

    def _extract_recommended_citation(self, text):
        """
        Extract recommended citation.

        Returns:
            str: Citation or empty string
        """
        for pattern in CITATION_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
            if match:
                citation = match.group(1).strip()

                # Clean up citation
                citation = re.sub(r'\s+', ' ', citation)  # Normalize whitespace

                # Must be at least 20 characters
                if len(citation) >= 20:
                    return citation

        return ''

    def _calculate_confidence(self, metadata):
        """
        Calculate overall confidence score based on extracted fields.

        Returns:
            str: HIGH, MEDIUM, or LOW
        """
        score = 0

        # Core bibliographic fields (heavy weight)
        if metadata.get('authors') and len(metadata['authors']) > 0:
            score += 3
        if metadata.get('title'):
            score += 3
        if metadata.get('year'):
            score += 3
        if metadata.get('journal_name'):
            score += 3

        # Important fields (medium weight)
        if metadata.get('volume'):
            score += 2
        if metadata.get('abstract'):
            score += 2

        # Optional fields (light weight)
        if metadata.get('keywords'):
            score += 1
        if metadata.get('doi'):
            score += 1
        if metadata.get('page_start'):
            score += 1

        # Max possible: 19
        if score >= 15:
            return 'HIGH'
        elif score >= 10:
            return 'MEDIUM'
        else:
            return 'LOW'
