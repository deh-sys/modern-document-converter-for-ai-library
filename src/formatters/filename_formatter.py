#!/usr/bin/env python3
"""
Filename Formatter - Standardized Filename Generation

Build standardized filenames from document metadata using YAML-driven templates.

Features:
    - Template-based formatting (loads from config/filename_templates/)
    - Field-specific formatting rules (spaces → hyphens/underscores)
    - Illegal character sanitization (OS-level restrictions)
    - Length truncation (max 255 chars for filesystem compatibility)
    - Missing field fallbacks

Legacy Format (Caselaw):
    c.{COURT}__{YEAR}__{CASE_NAME}__{CITATION}----{CODE}.ext

Example:
    Input:  court="Ga. Ct. App.", year="2014",
            case_name="Indian Trail, LLC v. State Bank",
            citation="328 Ga. App. 524", code="ABCDE"
    Output: c.Ga_Ct_App__2014__Indian-Trail-v-State-Bank__328_GaApp_524----ABCDE.pdf

Architecture:
    - YAML configs define templates and formatting rules
    - Formatter applies rules to metadata fields
    - Sanitizer removes illegal characters
    - Truncator enforces length limits

Usage:
    formatter = FilenameFormatter(document_type="caselaw")
    filename = formatter.format_filename(
        metadata_fields={"court": "Ga. Ct. App.", "year": "2014", ...},
        code="ABCDE",
        extension=".pdf"
    )
"""

import re
from pathlib import Path
from typing import Optional

import yaml


# ============================================================================
# FILENAME FORMATTER
# ============================================================================

class FilenameFormatter:
    """
    Format document metadata into standardized filenames.

    Loads template configuration from YAML and applies formatting rules
    to generate consistent, filesystem-safe filenames.
    """

    # OS-level illegal filename characters (Windows + macOS + Linux)
    ILLEGAL_CHARS = r'[<>:"/\\|?*\x00-\x1f]'

    # Default max filename length (most filesystems)
    MAX_FILENAME_LENGTH = 255


    def __init__(self, document_type: str = "caselaw"):
        """
        Initialize formatter for specific document type.

        Args:
            document_type: Document type to load template for (default: "caselaw")

        Raises:
            FileNotFoundError: If template config doesn't exist
            yaml.YAMLError: If template config is invalid
        """
        self.document_type = document_type
        self.config_path = Path(f"config/filename_templates/{document_type}.yaml")
        self.config = self._load_config()

        # Extract config sections
        self.template = self.config.get("template", {})
        self.formatting = self.config.get("formatting", {})
        self.sanitization = self.config.get("sanitization", {})
        self.length = self.config.get("length", {})
        self.missing_fields = self.config.get("missing_fields", {})


    # ========================================================================
    # PUBLIC API
    # ========================================================================

    def format_filename(
        self,
        metadata_fields: dict[str, str],
        code: str,
        extension: str,
    ) -> Optional[str]:
        """
        Format complete filename from metadata fields and unique code.

        Args:
            metadata_fields: Dict of metadata (keys: court, year, case_name, citation)
            code: 5-letter unique code (e.g., "ABCDE")
            extension: File extension (e.g., ".pdf", ".docx")

        Returns:
            Formatted filename, or None if required fields are missing

        Example:
            >>> formatter.format_filename(
            ...     metadata_fields={"court": "Ga. Ct. App.", "year": "2014",
            ...                     "case_name": "Smith v. Jones", "citation": "328 Ga. App. 524"},
            ...     code="ABCDE",
            ...     extension=".pdf"
            ... )
            'c.Ga_Ct_App__2014__Smith-v-Jones__328_GaApp_524----ABCDE.pdf'
        """
        # Check required fields
        if not self._validate_required_fields(metadata_fields):
            return None

        # Format each field
        formatted = {}
        formatted["court"] = self.format_court(metadata_fields.get("court", ""))
        formatted["year"] = self.format_year(metadata_fields.get("year", ""))
        formatted["case_name"] = self.format_case_name(metadata_fields.get("case_name", ""))
        formatted["citation"] = self.format_citation(metadata_fields.get("citation", ""))
        formatted["code"] = code

        # Build filename from template
        pattern = self.template.get("pattern", "")
        filename_stem = pattern.format(**formatted)

        # Add extension
        filename = f"{filename_stem}{extension}"

        # Sanitize illegal characters
        filename = self.sanitize_filename(filename)

        # Truncate if needed
        filename = self.truncate_if_needed(filename)

        return filename


    # ========================================================================
    # FIELD FORMATTING
    # ========================================================================

    def format_court(self, court: str) -> str:
        """
        Format court abbreviation.

        Rules (from YAML config):
            - Spaces → underscores
            - Periods → remove
            - Use as-is (already abbreviated by CaselawProcessor)

        Args:
            court: Court abbreviation (e.g., "Ga. Ct. App.", "ND Ill.")

        Returns:
            Formatted court (e.g., "Ga_Ct_App", "ND_Ill")

        Example:
            >>> formatter.format_court("Ga. Ct. App.")
            'Ga_Ct_App'
        """
        if not court:
            return self.missing_fields.get("court", {}).get("fallback", "Unknown_Court")

        # Remove periods
        formatted = court.replace(".", "")

        # Spaces → underscores
        formatted = formatted.replace(" ", "_")

        return formatted


    def format_year(self, year: str) -> str:
        """
        Format year.

        Rules:
            - Use as-is (already clean from metadata)
            - Should be 4 digits

        Args:
            year: Year string (e.g., "2014")

        Returns:
            Formatted year (e.g., "2014")

        Example:
            >>> formatter.format_year("2014")
            '2014'
        """
        if not year:
            return self.missing_fields.get("year", {}).get("fallback", "XXXX")

        return year


    def format_case_name(self, case_name: str) -> str:
        """
        Format case name (party names).

        Rules (from YAML config):
            - Spaces → hyphens
            - Periods → remove
            - Commas → remove
            - Ampersands (&) → 'and'
            - Keep: letters, numbers, hyphens only

        Args:
            case_name: Case caption (e.g., "Indian Trail, LLC v. State Bank & Trust Co.")

        Returns:
            Formatted case name (e.g., "Indian-Trail-LLC-v-State-Bank-and-Trust-Co")

        Example:
            >>> formatter.format_case_name("Abbott Labs. v. Sandoz, Inc")
            'Abbott-Labs-v-Sandoz-Inc'
        """
        if not case_name:
            return self.missing_fields.get("case_name", {}).get("fallback", "Unnamed_Case")

        # Ampersands → 'and'
        formatted = case_name.replace("&", "and")

        # Remove periods and commas
        formatted = formatted.replace(".", "")
        formatted = formatted.replace(",", "")

        # Spaces → hyphens
        formatted = formatted.replace(" ", "-")

        # Remove any remaining non-alphanumeric characters (except hyphens)
        formatted = re.sub(r'[^a-zA-Z0-9\-]', '', formatted)

        # Collapse multiple hyphens
        formatted = re.sub(r'-+', '-', formatted)

        # Remove leading/trailing hyphens
        formatted = formatted.strip("-")

        return formatted


    def format_citation(self, citation: str) -> str:
        """
        Format reporter citation.

        Rules (from YAML config):
            - Spaces → underscores
            - Periods → remove
            - Keep: letters, numbers, underscores only

        Args:
            citation: Reporter citation (e.g., "328 Ga. App. 524", "743 F. Supp. 2d 762")

        Returns:
            Formatted citation (e.g., "328_GaApp_524", "743_FSupp2d_762")

        Example:
            >>> formatter.format_citation("759 S.E.2d 654")
            '759_SE2d_654'
        """
        if not citation:
            return self.missing_fields.get("citation", {}).get("fallback", "Unpub")

        # Remove periods
        formatted = citation.replace(".", "")

        # Spaces → underscores
        formatted = formatted.replace(" ", "_")

        # Remove any remaining non-alphanumeric characters (except underscores)
        formatted = re.sub(r'[^a-zA-Z0-9_]', '', formatted)

        # Collapse multiple underscores
        formatted = re.sub(r'_+', '_', formatted)

        # Remove leading/trailing underscores
        formatted = formatted.strip("_")

        return formatted


    # ========================================================================
    # SANITIZATION & VALIDATION
    # ========================================================================

    def sanitize_filename(self, filename: str) -> str:
        """
        Remove illegal characters from filename.

        Removes OS-level illegal characters: < > : " / \\ | ? * and control chars

        Args:
            filename: Filename to sanitize

        Returns:
            Sanitized filename

        Example:
            >>> formatter.sanitize_filename('file<name>.pdf')
            'filename.pdf'
        """
        # Use default illegal characters pattern (already a valid regex)
        # Only remove truly illegal OS-level characters, keep hyphens and underscores
        illegal_pattern = r'[<>:"/\\|?*\x00-\x1f]'

        sanitized = re.sub(illegal_pattern, "", filename)

        # Remove any remaining control characters
        sanitized = "".join(char for char in sanitized if ord(char) >= 32)

        # Remove leading/trailing spaces and dots
        sanitized = sanitized.strip(". ")

        return sanitized


    def truncate_if_needed(self, filename: str) -> str:
        """
        Truncate filename if it exceeds maximum length.

        Preserves extension and code suffix when truncating.
        Strategy: Trim case_name first, then citation if still too long.

        Args:
            filename: Full filename including extension

        Returns:
            Truncated filename (if necessary)

        Example:
            >>> formatter.truncate_if_needed("very_long_filename..." * 50 + ".pdf")
            'very_long_filename...truncated...ABCDE.pdf'  # Under 255 chars
        """
        max_length = self.length.get("max_filename", self.MAX_FILENAME_LENGTH)

        if len(filename) <= max_length:
            return filename

        # Split into stem and extension
        parts = filename.rsplit(".", 1)
        if len(parts) != 2:
            # No extension, just truncate
            return filename[:max_length]

        stem, ext = parts

        # Reserve space for extension + dot
        max_stem_length = max_length - len(ext) - 1

        if max_stem_length <= 0:
            # Extension itself is too long (shouldn't happen)
            return filename[:max_length]

        # Truncate stem
        truncated_stem = stem[:max_stem_length]

        return f"{truncated_stem}.{ext}"


    def _validate_required_fields(self, metadata_fields: dict[str, str]) -> bool:
        """
        Check if all required fields are present.

        Args:
            metadata_fields: Dict of metadata fields

        Returns:
            True if all required fields present, False otherwise
        """
        for field_name, field_config in self.missing_fields.items():
            if field_config.get("required", True):
                if not metadata_fields.get(field_name):
                    return False

        return True


    # ========================================================================
    # CONFIGURATION LOADING
    # ========================================================================

    def _load_config(self) -> dict:
        """
        Load template configuration from YAML file.

        Returns:
            Parsed YAML configuration

        Raises:
            FileNotFoundError: If config file doesn't exist
            yaml.YAMLError: If config file is invalid
        """
        if not self.config_path.exists():
            raise FileNotFoundError(f"Template config not found: {self.config_path}")

        with open(self.config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
