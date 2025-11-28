"""
Case name extraction and formatting module.
Formats case names according to user specifications:
- First 2 words per party
- Remove special characters
- Hyphenate words
"""

import re


class CaseNameFormatter:
    """Extract and format case names for filenames."""

    def __init__(self, max_words_per_party=1):
        """
        Initialize case name formatter.

        Args:
            max_words_per_party: Maximum words to keep per party (default: 1)
        """
        self.max_words = max_words_per_party

    def extract_from_pdf(self, pdf_text):
        """
        Extract case name from PDF text.

        Args:
            pdf_text: Extracted PDF text

        Returns:
            str: Raw case name or None
        """
        if not pdf_text:
            return None

        lines = pdf_text.split('\n')
        lines = [l.strip() for l in lines if l.strip()]  # Remove empty lines

        # Filter out timestamp fragments (e.g., "AM Z", "PM Z" from download dates)
        # These can interfere with case name extraction
        lines = [l for l in lines if not re.match(r'^(AM|PM)\s+Z$', l, re.IGNORECASE)]

        # Strategy 1: Look for "v" on its own line (multi-line caption format)
        for i, line in enumerate(lines[:40]):
            if line.lower() in ['v', 'v.', 'vs', 'vs.']:
                # Found "v" on its own line
                if i > 0 and i < len(lines) - 1:
                    left_party = lines[i-1].strip()
                    right_party = lines[i+1].strip()

                    # Clean up common suffixes on first line
                    left_party = re.sub(r',?\s*Petitioners?$', '', left_party, flags=re.IGNORECASE)
                    left_party = re.sub(r',?\s*Plaintiffs?$', '', left_party, flags=re.IGNORECASE)
                    left_party = re.sub(r',?\s*Appellants?$', '', left_party, flags=re.IGNORECASE)
                    left_party = re.sub(r',?\s*et al\.?$', '', left_party, flags=re.IGNORECASE)

                    # Clean up common suffixes on second line
                    right_party = re.sub(r',?\s*Respondents?$', '', right_party, flags=re.IGNORECASE)
                    right_party = re.sub(r',?\s*Defendants?$', '', right_party, flags=re.IGNORECASE)
                    right_party = re.sub(r',?\s*Appellees?$', '', right_party, flags=re.IGNORECASE)

                    if left_party and right_party:
                        return f"{left_party} v. {right_party}"

        # Strategy 2: Look for case caption with "v." on same line
        for i, line in enumerate(lines[:40]):
            # Check if line contains " v. " or " vs. "
            if re.search(r'\s+v\.?\s+|\s+vs\.?\s+', line, re.IGNORECASE):
                # Found potential case name
                # Get surrounding lines for context
                start = max(0, i - 2)
                end = min(len(lines), i + 3)
                context = '\n'.join(lines[start:end])

                # Try to extract case name
                match = re.search(
                    r'([A-Z][A-Za-z\s,\.&\'\-\(\)]+?)\s+v\.?\s+([A-Za-z\s,\.&\'\-\(\)]+?)(?:\n|$)',
                    context,
                    re.IGNORECASE
                )

                if match:
                    left_party = match.group(1).strip()
                    right_party = match.group(2).strip()
                    return f"{left_party} v. {right_party}"

        return None

    def extract_from_filename(self, filename):
        """
        Extract case name from filename.

        Args:
            filename: Original filename

        Returns:
            str: Raw case name or None
        """
        # Remove common prefixes
        filename = re.sub(r'^law\s*-\s*[A-Z\s]+-\s*', '', filename, flags=re.IGNORECASE)

        # Remove artifacts
        filename = re.sub(r'_Attachment\d*', '', filename)

        # Look for case name before parenthetical
        # Pattern: "Case Name (Court Year)"
        match = re.search(r'^(.+?)\s*\(', filename)
        if match:
            return match.group(1).strip()

        # Look for case name before year/citation
        # Pattern: "Case Name_ 2019 U.S. Dist. LEXIS"
        match = re.search(r'^(.+?)_\s*\d{4}\s+', filename)
        if match:
            return match.group(1).strip()

        # No clear pattern, return everything before extension
        match = re.search(r'^(.+?)\.(?:pdf|docx?)$', filename, re.IGNORECASE)
        if match:
            return match.group(1).strip()

        return None

    def format_case_name(self, raw_case_name):
        """
        Format case name according to rules:
        1. Split at "v" into left and right parties
        2. Take only first party on each side (before comma)
        3. Remove special characters
        4. Take first N words per party
        5. Join with hyphens

        Args:
            raw_case_name: Raw case name (e.g., "Abbott Labs. v. Sandoz, Inc.")

        Returns:
            str: Formatted case name (e.g., "Abbott-Labs-v-Sandoz-Inc")
        """
        if not raw_case_name:
            return "Unknown"

        # Split at "v." or "v" or "vs."
        parts = re.split(r'\s+v\.?\s+|\s+vs\.?\s+', raw_case_name, maxsplit=1, flags=re.IGNORECASE)

        if len(parts) != 2:
            # No "v" found, sanitize whole thing
            return self._sanitize_party_name(raw_case_name)

        left_party, right_party = parts

        # Take only first party (before comma)
        left_party = left_party.split(',')[0].strip()
        right_party = right_party.split(',')[0].strip()

        # Format each party
        left_formatted = self._format_party_name(left_party)
        right_formatted = self._format_party_name(right_party)

        # Combine with "v"
        return f"{left_formatted}-v-{right_formatted}"

    def _format_party_name(self, party_name):
        """
        Format a single party name:
        1. Remove "et al."
        2. Remove special characters
        3. Intelligently select words (prefer surname for people)
        4. Join with hyphens

        Args:
            party_name: Single party name

        Returns:
            str: Formatted party name
        """
        # Remove timestamp fragments from download dates (e.g., "AM Z" or "PM Z")
        party_name = re.sub(r'\b(AM|PM)\s+Z\s*', '', party_name, flags=re.IGNORECASE)

        # Remove "et al."
        party_name = re.sub(r'\s*et\s+al\.?\s*', '', party_name, flags=re.IGNORECASE)

        # Remove special characters: . , ' " & ( ) : ;
        party_name = re.sub(r'[.,\'"&();:]', '', party_name)

        # Split into words
        words = party_name.split()

        if not words:
            return 'Unknown'

        # Smart word selection based on max_words
        if self.max_words == 1:
            # For 1 word, intelligently select

            # Check if this looks like a person's full name (3+ words, likely "First Middle Last")
            is_persons_name = len(words) >= 3 and words[-1] not in ['States', 'America', 'LLC', 'Inc', 'Corp', 'Ltd']

            if is_persons_name:
                # Person's name - take last word (surname)
                # e.g., "JOHN H ALDEN" -> "ALDEN"
                selected_words = [words[-1]]
            elif len(words) == 2 and words[0] in ['United', 'New', 'North', 'South', 'East', 'West']:
                # Geographic names - keep both words
                # e.g., "United States" -> "United-States"
                selected_words = words
            else:
                # Company names, single names, or other - take first word
                # e.g., "Abbott Labs" -> "Abbott", "State" -> "State"
                selected_words = words[:1]
        else:
            # Take first N words
            selected_words = words[:self.max_words]

        # Join with hyphens
        return '-'.join(selected_words) if selected_words else 'Unknown'

    def _sanitize_party_name(self, name):
        """Sanitize a name that doesn't have proper "v" format."""
        # Remove special characters
        name = re.sub(r'[.,\'"&();:]', '', name)

        # Take first N words
        words = name.split()
        words = words[:self.max_words * 2]  # Allow more words if no "v"

        return '-'.join(words) if words else 'Unknown'

    def expand_abbreviations(self, case_name):
        """
        Expand common abbreviations in case names.

        Args:
            case_name: Case name with abbreviations

        Returns:
            str: Case name with expansions
        """
        expansions = {
            r'\bU\.?S\.?\b': 'United States',
            r'\bMe\.?\b': 'Maine',  # State names
            r'\bMd\.?\b': 'Maryland',
            r'\bMass\.?\b': 'Massachusetts',
            r'\bCal\.?\b': 'California',
            r'\bFla\.?\b': 'Florida',
        }

        for pattern, replacement in expansions.items():
            case_name = re.sub(pattern, replacement, case_name, flags=re.IGNORECASE)

        return case_name
