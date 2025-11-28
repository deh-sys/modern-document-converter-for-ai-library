"""
Metadata extraction module for legal case PDFs.
Extracts comprehensive metadata including disposition, judges, attorneys, and more.
"""

import re
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ===== REGEX PATTERNS AS CONSTANTS =====

# Disposition patterns
DISPOSITION_PATTERNS = [
    # All-caps outcomes
    r'(?:judgment|decision|order)\s+(?:is\s+)?(AFFIRMED|REVERSED|VACATED|REMANDED|DISMISSED)',
    # Regular case outcomes
    r'(?:AFFIRM|REVERSE|VACATE|REMAND|DISMISS)(?:ED|ING)?(?:\s+in\s+part)?(?:\s+and\s+\w+ed)?',
    # With label
    r'Disposition:\s*(.+?)(?:\n|\.)',
]

# Opinion author patterns
OPINION_AUTHOR_PATTERNS = [
    # "Kennedy, J., delivered the opinion"
    r'([A-Z][A-Za-z]+),\s+(?:C\.)?J\.,\s+delivered the opinion',
    # "Justice Kennedy delivered the opinion"
    r'(?:Justice|Judge)\s+([A-Z][A-Za-z]+)\s+delivered the opinion',
    # "OPINION BY JUSTICE KENNEDY"
    r'OPINION BY (?:JUSTICE|JUDGE)\s+([A-Z][A-Z]+)',
    # "[Name], J., delivered the opinion of the Court"
    r'([A-Z][A-Za-z]+),\s+J\.,\s+delivered',
]

# Opinion type patterns
OPINION_TYPE_PATTERNS = [
    r'(MAJORITY|PLURALITY|PER CURIAM) OPINION',
    r'OPINION (?:OF|BY) THE COURT',
    r'\bPER CURIAM\b',
]

# Lower court judge patterns
LOWER_COURT_JUDGE_PATTERNS = [
    # "District Judge Smith"
    r'District Judge\s+([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)?)',
    # "Judge Smith presiding"
    r'Judge\s+([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)?)\s+presiding',
    # In procedural history
    r'before\s+(?:District\s+)?Judge\s+([A-Z][A-Za-z]+)',
]

# Panel members pattern (appellate courts)
PANEL_PATTERNS = [
    # "Before Smith, Jones, and Brown, Circuit Judges"
    r'Before\s+((?:[A-Z][A-Za-z]+(?:,\s+)?(?:and\s+)?)+),\s+(?:Circuit|District)?\s*Judges',
    # "Panel: Smith, Jones, Brown"
    r'Panel:\s+((?:[A-Z][A-Za-z]+(?:,\s+)?(?:and\s+)?)+)',
]

# Concurring/dissenting patterns
CONCUR_DISSENT_PATTERNS = [
    # "Justice Smith, concurring"
    r'(?:Justice|Judge)\s+([A-Z][A-Za-z]+)(?:,|\s+)(?:with whom[^,]+,\s+)?concurring(?:\s+in\s+part)?',
    # "Smith, J., concurring"
    r'([A-Z][A-Za-z]+),\s+J\.,\s+concurring(?:\s+in\s+part)?',
    # "Justice Smith, dissenting"
    r'(?:Justice|Judge)\s+([A-Z][A-Za-z]+)(?:,|\s+)(?:with whom[^,]+,\s+)?dissenting(?:\s+in\s+part)?',
    # "Smith, J., dissenting"
    r'([A-Z][A-Za-z]+),\s+J\.,\s+dissenting(?:\s+in\s+part)?',
    # Section headers
    r'([A-Z][A-Za-z]+),.*?(?:CONCURRING|DISSENTING)',
]

# Attorney patterns (simple, best effort)
ATTORNEY_PATTERNS = [
    # "[Name] argued the cause for [party]"
    r'([A-Z][a-z]+(?:\s+[A-Z]\.)?(?:\s+[A-Z][a-z]+)+)\s+argued the cause for\s+(petitioner|respondent|appellant|appellee)',
    # "Attorney for [party]: [Name]"
    r'Attorney for\s+(petitioner|respondent|appellant|appellee):\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
    # "[Name], [City], [State], for [party]"
    r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+),\s+\w+,\s+\w+,\s+for\s+(petitioner|respondent|appellant|appellee)',
]

# Docket number patterns
DOCKET_PATTERNS = [
    # Federal format: "No. 1:19-cv-12345"
    r'(?:Case|Civil\s+Action)?\s*No\.\s+(\d+:\d{2}-[a-z]{2,3}-\d+)',
    # Simple format: "No. 19-1234"
    r'(?:Case|Docket|Civil\s+Action)?\s*No\.\s+(\d{2,4}-\d{3,5})',
    # Supreme Court format: "No. 98-436"
    r'No\.\s+(\d{2,3}-\d{3,4})',
]

# Date patterns
FULL_DATE_PATTERNS = [
    # With label: "Decided: January 15, 2024"
    r'(?:Decided|Filed|Argued|Submitted):\s*([A-Z][a-z]+\s+\d{1,2},\s+\d{4})',
    # Without label but specific format
    r'([A-Z][a-z]+\s+\d{1,2},\s+\d{4})',
]


class MetadataExtractor:
    """Extract comprehensive metadata from legal case PDFs."""

    def __init__(self, date_extractor=None):
        """
        Initialize metadata extractor.

        Args:
            date_extractor: Optional DateExtractor instance for date extraction
        """
        self.date_extractor = date_extractor

    def extract_metadata(self, renamer_result, pdf_text):
        """
        Extract comprehensive metadata from PDF text.

        Args:
            renamer_result: Dictionary from CaselawRenamer.process_file()
            pdf_text: Full extracted PDF text (multizone)

        Returns:
            dict: Complete metadata with all fields and per-field confidence
        """
        if not pdf_text:
            logger.warning("No PDF text provided for metadata extraction")
            pdf_text = ""

        # Initialize metadata dict with renamer's values
        metadata = {
            'case_name': renamer_result.get('case_name', ''),
            'court': renamer_result.get('court', ''),
            'year': renamer_result.get('year', ''),
            'citation': '',
            'date_decided': '',
            'docket_number': '',
            'extraction_timestamp': datetime.now().isoformat(),
            'source_file': renamer_result.get('original_filename', ''),
        }

        # Convert renamer's reporter to legal citation format
        try:
            metadata['citation'] = self._format_legal_citation(renamer_result)
        except Exception as e:
            logger.debug(f"Citation formatting error: {e}")
            metadata['citation'] = ''

        # Extract NEW fields with per-field confidence
        # 1. Disposition
        try:
            result = self._extract_disposition(pdf_text)
            metadata['disposition'] = result['value']
            if result['value']:
                metadata['disposition_confidence'] = result['confidence']
        except Exception as e:
            logger.debug(f"Disposition extraction error: {e}")
            metadata['disposition'] = ''

        # 2. Opinion author
        try:
            result = self._extract_opinion_author(pdf_text)
            metadata['opinion_author'] = result['value']
            if result['value']:
                metadata['opinion_author_confidence'] = result['confidence']
        except Exception as e:
            logger.debug(f"Opinion author extraction error: {e}")
            metadata['opinion_author'] = ''

        # 3. Opinion type
        try:
            result = self._extract_opinion_type(pdf_text)
            metadata['opinion_type'] = result['value']
            if result['value']:
                metadata['opinion_type_confidence'] = result['confidence']
        except Exception as e:
            logger.debug(f"Opinion type extraction error: {e}")
            metadata['opinion_type'] = ''

        # 4. Lower court judge
        try:
            result = self._extract_lower_court_judge(pdf_text)
            metadata['lower_court_judge'] = result['value']
            if result['value']:
                metadata['lower_court_judge_confidence'] = result['confidence']
        except Exception as e:
            logger.debug(f"Lower court judge extraction error: {e}")
            metadata['lower_court_judge'] = ''

        # 5. Panel members
        try:
            result = self._extract_panel_members(pdf_text)
            metadata['panel_members'] = result['value']
            if result['value']:
                metadata['panel_members_confidence'] = result['confidence']
        except Exception as e:
            logger.debug(f"Panel members extraction error: {e}")
            metadata['panel_members'] = []

        # 6. Concurring/dissenting
        try:
            result = self._extract_concurring_dissenting(pdf_text)
            metadata['concurring_dissenting'] = result['value']
            if result['value'] and (result['value'].get('concurring') or result['value'].get('dissenting')):
                metadata['concurring_dissenting_confidence'] = result['confidence']
        except Exception as e:
            logger.debug(f"Concurring/dissenting extraction error: {e}")
            metadata['concurring_dissenting'] = {'concurring': [], 'dissenting': [], 'concurring_in_part': []}

        # 7. Attorneys
        try:
            result = self._extract_attorneys(pdf_text)
            metadata['attorneys'] = result['value']
            if result['value'] and any(result['value'].values()):
                metadata['attorneys_confidence'] = result['confidence']
        except Exception as e:
            logger.debug(f"Attorneys extraction error: {e}")
            metadata['attorneys'] = {'petitioner': [], 'respondent': [], 'appellant': [], 'appellee': []}

        # Extract docket number and date
        try:
            result = self._extract_docket_number(pdf_text)
            metadata['docket_number'] = result['value']
            if result['value']:
                metadata['docket_number_confidence'] = result['confidence']
        except Exception as e:
            logger.debug(f"Docket number extraction error: {e}")
            metadata['docket_number'] = ''

        try:
            result = self._extract_full_date(pdf_text)
            metadata['date_decided'] = result['value']
            if result['value']:
                metadata['date_decided_confidence'] = result['confidence']
        except Exception as e:
            logger.debug(f"Date extraction error: {e}")
            metadata['date_decided'] = ''

        # Calculate overall confidence
        metadata['extraction_confidence'] = self._calculate_confidence(metadata)

        return metadata

    # ===== EXTRACTION METHODS =====

    def _extract_disposition(self, text):
        """Extract judgment disposition (affirmed/reversed/etc.)."""
        if not text:
            return {'value': '', 'confidence': ''}

        # Search in first 2000 chars (case summary) and last 2000 chars (conclusion)
        header = text[:2000]
        # Extract last pages section if present
        if '[LAST_PAGES_SECTION]' in text:
            footer = text.split('[LAST_PAGES_SECTION]')[1][:2000]
        else:
            footer = text[-2000:]

        search_text = header + '\n' + footer

        for pattern in DISPOSITION_PATTERNS:
            match = re.search(pattern, search_text, re.IGNORECASE)
            if match:
                disposition = match.group(1) if match.lastindex else match.group(0)
                disposition = disposition.strip().capitalize()

                # HIGH confidence if explicit label or clear context
                if 'judgment' in match.group(0).lower() or 'Disposition:' in match.group(0):
                    return {'value': disposition, 'confidence': 'HIGH'}
                else:
                    return {'value': disposition, 'confidence': 'MEDIUM'}

        return {'value': '', 'confidence': ''}

    def _extract_opinion_author(self, text):
        """Extract judge who wrote the opinion."""
        if not text:
            return {'value': '', 'confidence': ''}

        # Check for Per Curiam first
        if re.search(r'\bPER CURIAM\b', text[:3000], re.IGNORECASE):
            return {'value': 'Per Curiam', 'confidence': 'HIGH'}

        # Search in first 3 pages
        header = text[:5000]

        for pattern in OPINION_AUTHOR_PATTERNS:
            match = re.search(pattern, header, re.IGNORECASE)
            if match:
                author = match.group(1).strip().title()
                return {'value': author, 'confidence': 'HIGH'}

        return {'value': '', 'confidence': ''}

    def _extract_opinion_type(self, text):
        """Extract opinion type (majority/per curiam/plurality)."""
        if not text:
            return {'value': '', 'confidence': ''}

        for pattern in OPINION_TYPE_PATTERNS:
            match = re.search(pattern, text[:3000], re.IGNORECASE)
            if match:
                if 'PER CURIAM' in match.group(0).upper():
                    return {'value': 'Per Curiam', 'confidence': 'HIGH'}
                elif match.lastindex:
                    opinion_type = match.group(1).strip().title()
                    return {'value': opinion_type, 'confidence': 'HIGH'}
                else:
                    return {'value': 'Majority', 'confidence': 'MEDIUM'}

        return {'value': '', 'confidence': ''}

    def _extract_lower_court_judge(self, text):
        """Extract judge from lower court."""
        if not text:
            return {'value': '', 'confidence': ''}

        # Search in first 5 pages
        header = text[:8000]

        for pattern in LOWER_COURT_JUDGE_PATTERNS:
            match = re.search(pattern, header, re.IGNORECASE)
            if match:
                judge = match.group(1).strip().title()
                return {'value': judge, 'confidence': 'MEDIUM'}

        return {'value': '', 'confidence': ''}

    def _extract_panel_members(self, text):
        """Extract all judges on appellate panel."""
        if not text:
            return {'value': [], 'confidence': ''}

        # Search in first 3 pages
        header = text[:5000]

        for pattern in PANEL_PATTERNS:
            match = re.search(pattern, header, re.IGNORECASE)
            if match:
                judges_str = match.group(1)
                # Parse the list: "Smith, Jones, and Brown"
                judges = re.split(r',\s+(?:and\s+)?', judges_str)
                judges = [j.strip().title() for j in judges if j.strip()]

                if judges:
                    return {'value': judges, 'confidence': 'HIGH'}

        return {'value': [], 'confidence': ''}

    def _extract_concurring_dissenting(self, text):
        """Extract judges who concurred or dissented."""
        if not text:
            return {'value': {'concurring': [], 'dissenting': [], 'concurring_in_part': []}, 'confidence': ''}

        result = {
            'concurring': [],
            'dissenting': [],
            'concurring_in_part': []
        }

        # Search in last pages if available
        if '[LAST_PAGES_SECTION]' in text:
            search_text = text.split('[LAST_PAGES_SECTION]')[1]
        else:
            search_text = text

        for pattern in CONCUR_DISSENT_PATTERNS:
            matches = re.finditer(pattern, search_text, re.IGNORECASE)
            for match in matches:
                judge = match.group(1).strip().title()
                full_text = match.group(0).lower()

                if 'concurring in part' in full_text:
                    if judge not in result['concurring_in_part']:
                        result['concurring_in_part'].append(judge)
                elif 'concurring' in full_text:
                    if judge not in result['concurring']:
                        result['concurring'].append(judge)
                elif 'dissenting' in full_text:
                    if judge not in result['dissenting']:
                        result['dissenting'].append(judge)

        if result['concurring'] or result['dissenting'] or result['concurring_in_part']:
            return {'value': result, 'confidence': 'MEDIUM'}
        else:
            return {'value': result, 'confidence': ''}

    def _extract_attorneys(self, text):
        """Extract attorneys/counsel (best effort, simple patterns)."""
        if not text:
            return {'value': {'petitioner': [], 'respondent': [], 'appellant': [], 'appellee': []}, 'confidence': ''}

        result = {
            'petitioner': [],
            'respondent': [],
            'appellant': [],
            'appellee': []
        }

        # Search in first 3 pages only
        header = text[:5000]

        for pattern in ATTORNEY_PATTERNS:
            matches = re.finditer(pattern, header, re.IGNORECASE)
            for match in matches:
                # Pattern order varies, check which group is name vs party
                groups = match.groups()

                # Find which group contains party designation
                party = None
                name = None
                for g in groups:
                    if g and g.lower() in ['petitioner', 'respondent', 'appellant', 'appellee']:
                        party = g.lower()
                    elif g and len(g) > 3:  # Likely a name
                        name = g.strip().title()

                if party and name and name not in result[party]:
                    result[party].append(name)

        if any(result.values()):
            return {'value': result, 'confidence': 'LOW'}  # Always LOW for attorneys (difficult field)
        else:
            return {'value': result, 'confidence': ''}

    def _extract_docket_number(self, text):
        """Extract docket/case number."""
        if not text:
            return {'value': '', 'confidence': ''}

        # Search in first 2000 chars
        header = text[:2000]

        for pattern in DOCKET_PATTERNS:
            match = re.search(pattern, header, re.IGNORECASE)
            if match:
                docket = match.group(1).strip()
                return {'value': docket, 'confidence': 'HIGH'}

        return {'value': '', 'confidence': ''}

    def _extract_full_date(self, text):
        """Extract full decision date."""
        if not text:
            return {'value': '', 'confidence': ''}

        # Search in first 2000 chars
        header = text[:2000]

        for pattern in FULL_DATE_PATTERNS:
            match = re.search(pattern, header)
            if match:
                date_str = match.group(1).strip()

                # HIGH confidence if labeled, MEDIUM if just date format
                if 'Decided:' in match.group(0) or 'Filed:' in match.group(0):
                    return {'value': date_str, 'confidence': 'HIGH'}
                else:
                    return {'value': date_str, 'confidence': 'MEDIUM'}

        return {'value': '', 'confidence': ''}

    # ===== UTILITY METHODS =====

    def _format_legal_citation(self, renamer_result):
        """Convert renamer's reporter format to legal citation format."""
        reporter = renamer_result.get('reporter', '')
        if not reporter or reporter == 'Unpub':
            return ''

        # Parse renamer format: "743_FSupp2d_762"
        parts = reporter.split('_')

        if len(parts) == 3:
            volume, reporter_abbr, page = parts
            legal_reporter = self._convert_reporter_to_legal_format(reporter_abbr)
            return f"{volume} {legal_reporter} {page}"
        elif len(parts) == 2:
            reporter_abbr, number = parts
            legal_reporter = self._convert_reporter_to_legal_format(reporter_abbr)
            return f"{legal_reporter} {number}"

        return reporter

    def _convert_reporter_to_legal_format(self, reporter_abbr):
        """Convert compact reporter abbreviation to legal format with dots and spaces."""
        conversions = {
            'US': 'U.S.',
            'SCt': 'S. Ct.',
            'LEd2d': 'L. Ed. 2d',
            'FSupp3d': 'F. Supp. 3d',
            'FSupp2d': 'F. Supp. 2d',
            'FSupp': 'F. Supp.',
            'F4th': 'F.4th',
            'F3d': 'F.3d',
            'F2d': 'F.2d',
            'SE2d': 'S.E.2d',
            'NE3d': 'N.E.3d',
            'P3d': 'P.3d',
            'A3d': 'A.3d',
            'SW3d': 'S.W.3d',
            'NW2d': 'N.W.2d',
            'So3d': 'So.3d',
            'GaApp': 'Ga. App.',
            'Ga': 'Ga.',
            'USDistLEXIS': 'U.S. Dist. LEXIS',
            'GaStateLEXIS': 'Ga. State LEXIS',
            'WL': 'WL',
        }
        return conversions.get(reporter_abbr, reporter_abbr)

    def _calculate_confidence(self, metadata):
        """Calculate overall confidence score based on extracted fields."""
        score = 0

        # Core fields from renamer (heavy weight)
        if metadata.get('court'):
            score += 3
        if metadata.get('year'):
            score += 3
        if metadata.get('case_name'):
            score += 3
        if metadata.get('citation'):
            score += 3

        # Important new fields (medium weight)
        if metadata.get('date_decided'):
            score += 2
        if metadata.get('docket_number'):
            score += 2
        if metadata.get('disposition'):
            score += 2

        # Optional fields (light weight)
        if metadata.get('opinion_author'):
            score += 1
        if metadata.get('panel_members'):
            score += 1

        # Max possible: 20
        if score >= 16:
            return 'HIGH'
        elif score >= 10:
            return 'MEDIUM'
        else:
            return 'LOW'
