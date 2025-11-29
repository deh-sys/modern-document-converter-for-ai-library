#!/usr/bin/env python3
"""
Caselaw Metadata Extractor

Extracts structured metadata from legal case documents using YAML-driven regex patterns.

Features:
    - Case name extraction (plaintiff v. defendant)
    - Date extraction (decision, filing, argument dates)
    - Court identification (state, federal, circuit, district)
    - Citation extraction (reporter volume and page numbers)
    - Graceful fallback for missing data

Architecture:
    - YAML-driven patterns (no hardcoded regex)
    - Priority-based pattern matching (try highest priority first)
    - Reference database lookups for court abbreviations
    - Provenance tracking for all extracted fields

Usage:
    processor = CaselawProcessor()
    metadata = processor.extract_metadata(document_text)
"""

import re
import json
from pathlib import Path
from typing import Optional

import yaml

from src.core.models import (
    DocumentMetadata,
    DocumentType,
    MetadataField,
    ExtractionSource,
    ConfidenceLevel,
)


# ============================================================================
# CASELAW PROCESSOR
# ============================================================================

class CaselawProcessor:
    """
    Extract structured metadata from caselaw documents.

    Uses YAML-driven extraction rules to identify:
        - Case names (parties)
        - Decision dates
        - Court information
        - Reporter citations

    All patterns loaded from config/document_types/caselaw.yaml.
    Reference data loaded from data/ directory (courts, reporters).
    """

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize caselaw processor.

        Args:
            config_path: Optional path to caselaw.yaml config file.
                        Defaults to config/document_types/caselaw.yaml
        """
        if config_path is None:
            config_path = Path("config/document_types/caselaw.yaml")

        self.config_path = config_path
        self.config = self._load_yaml_config()
        self.extraction_rules = self.config.get("extraction_rules", {})

        # Load reference databases
        self.courts_db = self._load_courts_database()
        self.reporters_db = self._load_reporters_database()


    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def _map_confidence(self, conf_str: str) -> ConfidenceLevel:
        """
        Map string confidence to ConfidenceLevel enum.

        Args:
            conf_str: "HIGH", "MEDIUM", or "LOW"

        Returns:
            ConfidenceLevel enum value
        """
        mapping = {
            "HIGH": ConfidenceLevel.HIGH,
            "MEDIUM": ConfidenceLevel.MEDIUM,
            "LOW": ConfidenceLevel.LOW,
        }
        return mapping.get(conf_str.upper(), ConfidenceLevel.MEDIUM)


    # ========================================================================
    # PUBLIC API
    # ========================================================================

    def extract_metadata(self, text: str) -> DocumentMetadata:
        """
        Extract all metadata from document text.

        Args:
            text: Full document text (typically first few pages)

        Returns:
            DocumentMetadata with extracted fields and provenance tracking

        Extracts:
            - case_name: Full caption (e.g., "Smith v. Jones")
            - year: Decision year
            - court: Court name or abbreviation
            - citation: Primary reporter citation
        """
        fields: dict[str, MetadataField] = {}

        # Extract case name
        case_name = self._extract_case_name(text)
        if case_name:
            fields["case_name"] = case_name

        # Extract date
        date_field = self._extract_date(text)
        if date_field:
            fields["year"] = date_field

        # Extract court
        court = self._extract_court(text)
        if court:
            fields["court"] = court

        # Extract citation
        citation = self._extract_citation(text)
        if citation:
            fields["citation"] = citation

        return DocumentMetadata(
            fields=fields,
            document_type=DocumentType.CASELAW
        )


    # ========================================================================
    # CASE NAME EXTRACTION
    # ========================================================================

    def _extract_case_name(self, text: str) -> Optional[MetadataField]:
        """
        Extract case caption (party names).

        Pattern: "Plaintiff v. Defendant"

        Returns:
            MetadataField with cleaned case name, or None if not found
        """
        rules = self.extraction_rules.get("case_name", [])
        if not rules:
            return None

        # Sort by priority (lowest number = highest priority, try first)
        rules = sorted(rules, key=lambda r: r.get("priority", 999), reverse=False)

        for rule in rules:
            pattern = rule.get("pattern")
            if not pattern:
                continue

            match = re.search(pattern, text, re.MULTILINE)
            if match:
                # Extract plaintiff and defendant
                plaintiff_raw = match.group(1) if match.lastindex >= 1 else ""
                defendant_raw = match.group(2) if match.lastindex >= 2 else ""

                # Clean up parties
                captures = rule.get("captures", {})
                plaintiff = self._cleanup_party(
                    plaintiff_raw,
                    captures.get("plaintiff", {}).get("cleanup_patterns", [])
                )
                defendant = self._cleanup_party(
                    defendant_raw,
                    captures.get("defendant", {}).get("cleanup_patterns", [])
                )

                if plaintiff and defendant:
                    case_name = f"{plaintiff} v. {defendant}"

                    return MetadataField(
                        key="case_name",
                        value=case_name,
                        source=ExtractionSource.DOCUMENT,
                        confidence=self._map_confidence(rule.get("confidence", "HIGH")),
                        extractor_name=f"CaselawProcessor: {rule.get('description', 'case_name')}"
                    )

        return None


    def _cleanup_party(self, party: str, cleanup_patterns: list[str]) -> str:
        """
        Clean up party name by removing procedural designations.

        Args:
            party: Raw party name (e.g., "Smith, Plaintiff")
            cleanup_patterns: List of regex patterns to remove

        Returns:
            Cleaned party name (e.g., "Smith")
        """
        party = party.strip()

        for pattern in cleanup_patterns:
            party = re.sub(pattern, "", party, flags=re.IGNORECASE)

        # Final cleanup
        party = party.strip().strip(",").strip()

        return party


    # ========================================================================
    # DATE EXTRACTION
    # ========================================================================

    def _extract_date(self, text: str) -> Optional[MetadataField]:
        """
        Extract decision date (prefer Decided > Filed > Argued).

        Pattern: "Decided: July 3, 2014"

        Returns:
            MetadataField with year as value, or None if not found
        """
        rules = self.extraction_rules.get("date", [])
        if not rules:
            return None

        # Sort by priority (lowest number = highest priority, try first)
        rules = sorted(rules, key=lambda r: r.get("priority", 999), reverse=False)

        for rule in rules:
            pattern = rule.get("pattern")
            if not pattern:
                continue

            match = re.search(pattern, text)
            if match:
                # Extract year (typically capture group 2)
                captures = rule.get("captures", {})
                year_group = captures.get("year", {}).get("group", 2)

                # Check if group exists (use len(groups()) not lastindex for nested groups)
                if len(match.groups()) >= year_group:
                    year = match.group(year_group)

                    return MetadataField(
                        key="year",
                        value=year,
                        source=ExtractionSource.DOCUMENT,
                        confidence=self._map_confidence(rule.get("confidence", "HIGH")),
                        extractor_name=f"CaselawProcessor: {rule.get('description', 'date')}"
                    )

        return None


    # ========================================================================
    # COURT EXTRACTION
    # ========================================================================

    def _extract_court(self, text: str) -> Optional[MetadataField]:
        """
        Extract court name.

        Patterns:
            - "Court of Appeals of Georgia"
            - "United States District Court for the Northern District of Illinois"

        Returns:
            MetadataField with court abbreviation, or None if not found
        """
        rules = self.extraction_rules.get("court", [])
        if not rules:
            return None

        # Sort by priority (lowest number = highest priority, try first)
        rules = sorted(rules, key=lambda r: r.get("priority", 999), reverse=False)

        for rule in rules:
            pattern = rule.get("pattern")
            if not pattern:
                continue

            match = re.search(pattern, text)
            if match:
                # Build court name from captures
                court_name = self._build_court_name(match, rule)

                if court_name:
                    return MetadataField(
                        key="court",
                        value=court_name,
                        source=ExtractionSource.DOCUMENT,
                        confidence=self._map_confidence(rule.get("confidence", "HIGH")),
                        extractor_name=f"CaselawProcessor: {rule.get('description', 'court')}"
                    )

        return None


    def _build_court_name(self, match: re.Match, rule: dict) -> str:
        """
        Build court name from regex match and rule configuration.

        Args:
            match: Regex match object
            rule: Extraction rule with capture group definitions

        Returns:
            Court name or abbreviation
        """
        captures = rule.get("captures", {})
        description = rule.get("description", "")

        # State Court of Appeals
        if "state" in captures and match.lastindex >= 1:
            state = match.group(captures["state"]["group"]).strip()

            # Look up state abbreviation
            state_abbrev = self._get_state_abbreviation(state)

            if "Appeals" in description:
                return f"{state_abbrev} Ct. App."
            elif "Supreme" in description:
                return f"{state_abbrev} Sup. Ct."

        # Federal Circuit
        if "circuit" in captures and match.lastindex >= 1:
            circuit = match.group(captures["circuit"]["group"]).strip()
            return circuit

        # Federal District Court
        if "district" in captures and "state" in captures and match.lastindex >= 2:
            district = match.group(captures["district"]["group"]).strip()
            state = match.group(captures["state"]["group"]).strip()
            state_abbrev = self._get_state_abbreviation(state)

            # Format: "ND Ill." for Northern District of Illinois
            district_abbrev = self._abbreviate_district(district)
            return f"{district_abbrev} {state_abbrev}"

        # Fallback: return full match
        return match.group(0)


    def _get_state_abbreviation(self, state_name: str) -> str:
        """
        Get standard abbreviation for state name.

        Args:
            state_name: Full state name (e.g., "Georgia", "Illinois")

        Returns:
            State abbreviation (e.g., "Ga.", "Ill.")
        """
        # Use courts database if available
        if self.courts_db:
            for court_id, court_data in self.courts_db.items():
                if state_name.lower() in court_data.get("name", "").lower():
                    # Extract state abbreviation from court ID
                    # Format: "GA_APP" -> "Ga."
                    state_code = court_id.split("_")[0]
                    return f"{state_code.capitalize()}."

        # Fallback: common state abbreviations
        state_abbrevs = {
            "georgia": "Ga.",
            "illinois": "Ill.",
            "california": "Cal.",
            "new york": "N.Y.",
            "texas": "Tex.",
            "florida": "Fla.",
        }

        return state_abbrevs.get(state_name.lower(), state_name)


    def _abbreviate_district(self, district: str) -> str:
        """
        Abbreviate federal district designation.

        Args:
            district: District name (e.g., "Northern District of")

        Returns:
            Abbreviated form (e.g., "ND")
        """
        abbrevs = {
            "northern": "ND",
            "southern": "SD",
            "eastern": "ED",
            "western": "WD",
        }

        for full, abbrev in abbrevs.items():
            if full.lower() in district.lower():
                return abbrev

        return district


    # ========================================================================
    # CITATION EXTRACTION
    # ========================================================================

    def _extract_citation(self, text: str) -> Optional[MetadataField]:
        """
        Extract primary reporter citation.

        Pattern: "328 Ga. App. 524"

        Returns:
            MetadataField with formatted citation, or None if not found
        """
        rules = self.extraction_rules.get("citation", [])
        if not rules:
            return None

        # Sort by priority (lowest number = highest priority, try first)
        rules = sorted(rules, key=lambda r: r.get("priority", 999), reverse=False)

        for rule in rules:
            pattern = rule.get("pattern")
            if not pattern:
                continue

            match = re.search(pattern, text)
            if match:
                # Extract volume and page
                captures = rule.get("captures", {})
                volume_group = captures.get("volume", {}).get("group", 1)
                page_group = captures.get("page", {}).get("group", 2)

                # Check if groups exist (use len(groups()) not lastindex)
                if len(match.groups()) >= max(volume_group, page_group):
                    volume = match.group(volume_group)
                    page = match.group(page_group)
                    reporter = rule.get("reporter", "")

                    citation = f"{volume} {reporter} {page}"

                    return MetadataField(
                        key="citation",
                        value=citation,
                        source=ExtractionSource.DOCUMENT,
                        confidence=self._map_confidence(rule.get("confidence", "HIGH")),
                        extractor_name=f"CaselawProcessor: {rule.get('description', 'citation')}"
                    )

        return None


    # ========================================================================
    # CONFIGURATION LOADING
    # ========================================================================

    def _load_yaml_config(self) -> dict:
        """
        Load extraction rules from YAML config.

        Returns:
            Parsed YAML configuration dictionary

        Raises:
            FileNotFoundError: If config file doesn't exist
            yaml.YAMLError: If config file is invalid
        """
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(self.config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)


    def _load_courts_database(self) -> Optional[dict]:
        """
        Load courts reference database.

        Returns:
            Courts database dictionary, or None if file doesn't exist
        """
        db_path = Path("data/bluebook_courts_mapping.json")

        if not db_path.exists():
            return None

        try:
            with open(db_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None


    def _load_reporters_database(self) -> Optional[dict]:
        """
        Load reporters reference database.

        Returns:
            Reporters database dictionary, or None if file doesn't exist
        """
        db_path = Path("data/reporters_database.json")

        if not db_path.exists():
            return None

        try:
            with open(db_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None
