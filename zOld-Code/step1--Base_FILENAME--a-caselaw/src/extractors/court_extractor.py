"""
Court identification and Bluebook abbreviation extraction module.
"""

import re
import json
from pathlib import Path


class CourtExtractor:
    """Extract and standardize court names using Bluebook abbreviations."""

    def __init__(self, mapping_file=None):
        """
        Initialize court extractor.

        Args:
            mapping_file: Path to Bluebook courts mapping JSON file
        """
        if mapping_file is None:
            # Default to bluebook_courts_mapping.json in src/data
            mapping_file = Path(__file__).parent.parent / "data" / "bluebook_courts_mapping.json"
            # Fallback to project root if not in src/data
            if not mapping_file.exists():
                project_root = Path(__file__).parent.parent.parent
                mapping_file = project_root / "bluebook_courts_mapping.json"

        self.mapping = self._load_mapping(mapping_file)

    def _load_mapping(self, mapping_file):
        """Load Bluebook court mappings from JSON file."""
        try:
            with open(mapping_file, 'r') as f:
                mapping = json.load(f)
                # Convert all filename_code values to use underscores
                self._add_underscores_to_codes(mapping)
                return mapping
        except Exception:
            return {"federal": {}, "state": {}}

    def _add_underscores_to_codes(self, mapping):
        """Recursively update filename_code from bluebook format with underscores."""
        if isinstance(mapping, dict):
            # If this dict has both 'bluebook' and 'filename_code', regenerate filename_code from bluebook
            if 'bluebook' in mapping and 'filename_code' in mapping:
                bluebook = mapping['bluebook']
                # Convert: remove dots, replace spaces with underscores
                mapping['filename_code'] = bluebook.replace('.', '').replace(' ', '_')

            # Recurse into all values
            for value in mapping.values():
                self._add_underscores_to_codes(value)
        elif isinstance(mapping, list):
            for item in mapping:
                self._add_underscores_to_codes(item)

    def extract_from_pdf(self, pdf_text):
        """
        Extract court name from PDF text.

        Args:
            pdf_text: Extracted PDF text

        Returns:
            str: Bluebook filename code or None
        """
        if not pdf_text:
            return None

        # Try federal courts first
        court_code = self._match_federal_court(pdf_text)
        if court_code:
            return court_code

        # Try state courts
        court_code = self._match_state_court(pdf_text)
        if court_code:
            return court_code

        return None

    def _match_federal_court(self, text):
        """Match federal court patterns in text."""

        # Check Supreme Court
        scotus_patterns = self.mapping['federal']['supreme_court']['patterns']
        for pattern in scotus_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return self.mapping['federal']['supreme_court']['filename_code']

        # Check Courts of Appeals
        for circuit_id, circuit_info in self.mapping['federal']['courts_of_appeals'].items():
            for pattern in circuit_info['patterns']:
                if re.search(pattern, text, re.IGNORECASE):
                    # Convert from mapping format to new format: "1st_Cir" -> "Cir_1"
                    code = circuit_info['filename_code']
                    if '_Cir' in code:
                        # Extract circuit number/name and reverse: "1st_Cir" -> "Cir_1"
                        parts = code.split('_')
                        circuit_num = parts[0].replace('st', '').replace('nd', '').replace('rd', '').replace('th', '')
                        return f"Cir_{circuit_num}"
                    return code

        # Check District Courts
        district_pattern = r'United States District Court.*?for the\s+((?:Northern|Southern|Eastern|Western|Middle|Central)\s+District\s+of|District\s+of)\s+([A-Za-z\s]+?)(?:\n|,|;)'
        match = re.search(district_pattern, text, re.IGNORECASE)

        if match:
            district_type = match.group(1).strip()
            state_name = match.group(2).strip()

            # Determine if it's a multi-district state or single district
            # Check if direction word is at the start
            direction_map = {
                'Northern': 'ND',
                'Southern': 'SD',
                'Eastern': 'ED',
                'Western': 'WD',
                'Middle': 'MD',
                'Central': 'CD'
            }

            direction_abbrev = 'D'  # default for single district
            for direction_word, abbrev in direction_map.items():
                if direction_word in district_type:
                    direction_abbrev = abbrev
                    break

            # Look up state abbreviation and convert to ALL CAPS
            state_code = self._get_state_abbreviation(state_name)
            if state_code:
                state_code_upper = state_code.upper()
                # New format: STATE_DIRECTION (e.g., "VA_ED" not "ED_Va")
                return f"{state_code_upper}_{direction_abbrev}"

        return None

    def _match_state_court(self, text):
        """Match state court patterns in text."""

        # Special case: State Court of Georgia, Fulton County
        state_court_match = re.search(
            r'State Court of (Georgia|[A-Z][a-z]+),\s+([A-Z][a-z]+)\s+County',
            text
        )
        if state_court_match:
            state = state_court_match.group(1)
            county = state_court_match.group(2)
            if state == 'Georgia':
                return f"Ga_St_Ct_{county}"
            # Add other states as needed

        # Iterate through each state in the mapping
        for state_name, courts in self.mapping['state'].items():
            for court_type, court_info in courts.items():
                bluebook = court_info['bluebook']

                # Create search pattern from Bluebook abbreviation
                # e.g., "Ga. Ct. App." -> "Court of Appeals of Georgia"
                if court_type == 'supreme':
                    patterns = [
                        f"Supreme Court of {state_name}",
                        f"{state_name} Supreme Court"
                    ]
                elif court_type == 'appeals' or 'appeal' in court_type:
                    patterns = [
                        f"Court of Appeals of {state_name}",
                        f"{state_name} Court of Appeals"
                    ]
                elif 'appellate' in court_type or 'app' in court_type:
                    patterns = [
                        f"Appellate.*?{state_name}",
                        f"{state_name}.*?Appellate"
                    ]
                else:
                    # Generic pattern based on court type
                    patterns = [f"{state_name}.*?{court_type}"]

                # Check all patterns
                for pattern in patterns:
                    if re.search(pattern, text, re.IGNORECASE):
                        return court_info['filename_code']

        return None

    def _get_state_abbreviation(self, state_name):
        """
        Get state abbreviation for filename from full state name.

        Args:
            state_name: Full state name (e.g., "Illinois")

        Returns:
            str: State abbreviation (e.g., "Ill")
        """
        state_abbrev_map = {
            'Alabama': 'Ala',
            'Alaska': 'Alaska',
            'Arizona': 'Ariz',
            'Arkansas': 'Ark',
            'California': 'Cal',
            'Colorado': 'Colo',
            'Connecticut': 'Conn',
            'Delaware': 'Del',
            'District of Columbia': 'DC',
            'Florida': 'Fla',
            'Georgia': 'Ga',
            'Hawaii': 'Haw',
            'Idaho': 'Idaho',
            'Illinois': 'Ill',
            'Indiana': 'Ind',
            'Iowa': 'Iowa',
            'Kansas': 'Kan',
            'Kentucky': 'Ky',
            'Louisiana': 'La',
            'Maine': 'Me',
            'Maryland': 'Md',
            'Massachusetts': 'Mass',
            'Michigan': 'Mich',
            'Minnesota': 'Minn',
            'Mississippi': 'Miss',
            'Missouri': 'Mo',
            'Montana': 'Mont',
            'Nebraska': 'Neb',
            'Nevada': 'Nev',
            'New Hampshire': 'NH',
            'New Jersey': 'NJ',
            'New Mexico': 'NM',
            'New York': 'NY',
            'North Carolina': 'NC',
            'North Dakota': 'ND',
            'Ohio': 'Ohio',
            'Oklahoma': 'Okla',
            'Oregon': 'Or',
            'Pennsylvania': 'Pa',
            'Puerto Rico': 'PR',
            'Rhode Island': 'RI',
            'South Carolina': 'SC',
            'South Dakota': 'SD',
            'Tennessee': 'Tenn',
            'Texas': 'Tex',
            'Utah': 'Utah',
            'Vermont': 'Vt',
            'Virginia': 'Va',
            'Washington': 'Wash',
            'West Virginia': 'WVa',
            'Wisconsin': 'Wis',
            'Wyoming': 'Wyo'
        }

        return state_abbrev_map.get(state_name.strip())

    def extract_from_filename(self, filename):
        """
        Extract court hint from filename.

        Args:
            filename: Original filename

        Returns:
            str: Court code hint or None
        """
        # Look for parenthetical pattern: (ND Ill 2010)
        paren_match = re.search(r'\(([A-Z][A-Za-z\s\.]+?)\s+(\d{4})\)', filename)
        if paren_match:
            court_hint = paren_match.group(1).strip()
            # Try to standardize common abbreviations
            return self._standardize_filename_hint(court_hint)

        # Look for prefix pattern: law - GA COA -
        prefix_match = re.match(r'law\s*-\s*([A-Z\s]+)\s*-', filename)
        if prefix_match:
            court_hint = prefix_match.group(1).strip()
            return self._standardize_filename_hint(court_hint)

        return None

    def _standardize_filename_hint(self, hint):
        """Convert common filename court hints to new format."""
        hint_map = {
            'ND Ill': 'IL_ND',
            'N.D. Ill': 'IL_ND',
            'ED Va': 'VA_ED',
            'E.D. Va': 'VA_ED',
            'SD NY': 'NY_SD',
            'S.D.N.Y': 'NY_SD',
            '1st Cir': 'Cir_1',
            '2d Cir': 'Cir_2',
            '3d Cir': 'Cir_3',
            '4th Cir': 'Cir_4',
            '5th Cir': 'Cir_5',
            '6th Cir': 'Cir_6',
            '7th Cir': 'Cir_7',
            '8th Cir': 'Cir_8',
            '9th Cir': 'Cir_9',
            '10th Cir': 'Cir_10',
            '11th Cir': 'Cir_11',
            'DC Cir': 'Cir_DC',
            'GA SC': 'Ga',
            'GA COA': 'Ga_Ct_App',
            'Ga App': 'Ga_Ct_App',
            'Ga': 'Ga'
        }

        return hint_map.get(hint)
