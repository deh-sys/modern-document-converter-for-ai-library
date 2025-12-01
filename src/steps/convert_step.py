#!/usr/bin/env python3
"""
Convert Step - Document to AI-Ready Text Conversion

Converts PDF/DOCX documents to clean, AI-ready .txt files with YAML frontmatter.

Pipeline (all in memory, no intermediate files):
    1. Extract text (using text_extractor with strategy parameter)
    2. Normalize text (basic cleaning: unicode, hyphens, whitespace)
    3. Apply YAML cleaning rules (noise removal + heading detection)
    4. Generate YAML frontmatter (from metadata)
    5. Combine frontmatter + cleaned text
    6. Save final .txt file (same directory as source)
    7. Record conversion in registry

Features:
    - Strategy-based extraction (fast/deep)
    - YAML-driven cleaning rules (document-type specific)
    - Markdown heading detection and formatting
    - Noise pattern removal (Lexis headers, page numbers, etc.)
    - YAML frontmatter generation
    - Dry-run mode for testing
    - Processing statistics tracking

Usage:
    from src.steps.convert_step import ConvertStep

    step = ConvertStep(registrar, strategy='fast')
    result = step.process_file(Path("case.pdf"))

    if result.success:
        print(f"Converted to: {result.output_file}")
        print(f"Removed {result.lines_removed} noise lines")
    else:
        print(result.error_message)
"""

import re
import time
from pathlib import Path
from typing import Optional, Dict, List

import yaml

from src.core.models import ConvertResult, DocumentType, ProcessingStatus
from src.services.text_extractor import extract_text
from src.services.classifier import classify
from src.cleaners.text_normalizer import normalize_text
from src.services.registrar import Registrar


# ============================================================================
# CONVERT STEP
# ============================================================================

class ConvertStep:
    """
    Convert documents to AI-ready text with YAML frontmatter.

    This step orchestrates the complete conversion pipeline:
    - Extracts text using strategy-based extraction
    - Classifies document type
    - Applies document-specific cleaning rules
    - Generates YAML frontmatter
    - Saves clean .txt files

    All processing happens in memory - no intermediate files written.
    """

    def __init__(
        self,
        registrar: Registrar,
        strategy: str = 'fast',
        dry_run: bool = False,
    ):
        """
        Initialize convert step.

        Args:
            registrar: Registrar instance for tracking conversions
            strategy: Extraction strategy ('fast' or 'deep')
            dry_run: If True, don't write files or update registry
        """
        self.registrar = registrar
        self.strategy = strategy
        self.dry_run = dry_run


    # ========================================================================
    # PUBLIC API
    # ========================================================================

    def process_file(self, file_path: Path) -> ConvertResult:
        """
        Convert a single file to AI-ready text.

        Pipeline:
            1. Extract text (strategy-based)
            2. Classify document type
            3. Normalize text
            4. Load cleaning rules for document type
            5. Apply noise removal
            6. Apply heading detection
            7. Generate frontmatter
            8. Save .txt file
            9. Record in registry

        Args:
            file_path: Path to PDF or DOCX file

        Returns:
            ConvertResult with success status and statistics
        """
        start_time = time.time()

        try:
            # Step 1: Extract text
            extraction = extract_text(
                file_path,
                normalize=False,  # We'll normalize manually after extraction
                strategy=self.strategy,
            )

            if not extraction.success:
                return ConvertResult(
                    success=False,
                    source_file=str(file_path),
                    error_message=f"Extraction failed: {extraction.error_message}",
                )

            raw_text = extraction.text

            # Step 2: Classify document type
            classification = classify(raw_text)
            doc_type = classification.document_type

            # Step 3: Normalize text (unicode, hyphens, whitespace)
            normalized_text = normalize_text(raw_text)

            # Step 4: Load cleaning rules for this document type
            cleaning_rules = self._load_cleaning_rules(doc_type.value)

            # Step 5-6: Apply cleaning rules (noise removal + heading detection)
            cleaned_text, stats = self._apply_cleaning_rules(
                normalized_text,
                cleaning_rules,
            )

            # Step 7: Generate YAML frontmatter
            # For now, use basic metadata from classification
            # In full pipeline, this would come from metadata extraction step
            frontmatter = self._generate_frontmatter(
                doc_type=doc_type.value,
                source_file=file_path.name,
                code=None,  # Will be populated by orchestrator
                metadata={},  # Will be populated by orchestrator
            )

            # Combine frontmatter + cleaned text
            final_content = f"{frontmatter}\n\n{cleaned_text}"

            # Step 8: Save .txt file
            output_path = self._save_txt_file(file_path, final_content)

            # Step 9: Record in registry (if not dry-run)
            if not self.dry_run:
                # Get document_id from registry (if already registered)
                doc = self.registrar.get_document_by_path(str(file_path))
                if doc:
                    self.registrar.record_processing_step(
                        document_id=doc['id'],
                        step_name='convert',
                        step_order=2,
                        status=ProcessingStatus.SUCCESS,
                    )

            # Success!
            processing_time = time.time() - start_time

            return ConvertResult(
                success=True,
                source_file=str(file_path),
                output_file=str(output_path),
                document_type=doc_type,
                character_count=len(final_content),
                lines_removed=stats['lines_removed'],
                headings_added=stats['headings_added'],
                processing_time=processing_time,
            )

        except Exception as e:
            processing_time = time.time() - start_time
            error_type = type(e).__name__

            return ConvertResult(
                success=False,
                source_file=str(file_path),
                error_message=f"{error_type}: {str(e)}",
                processing_time=processing_time,
            )


    def close(self):
        """Close registrar connection."""
        if self.registrar:
            self.registrar.close()


    # ========================================================================
    # CLEANING RULES
    # ========================================================================

    def _load_cleaning_rules(self, document_type: str) -> Dict:
        """
        Load cleaning rules from YAML config for document type.

        Args:
            document_type: Document type (e.g., 'caselaw', 'statutes')

        Returns:
            Dictionary with cleaning_rules section from YAML

        Raises:
            FileNotFoundError: If config file doesn't exist
            KeyError: If cleaning_rules section missing
        """
        config_path = Path(f"config/document_types/{document_type}.yaml")

        if not config_path.exists():
            # Return empty rules if config doesn't exist
            return {'noise_patterns': [], 'heading_patterns': []}

        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        # Get cleaning_rules section (may not exist for all document types)
        cleaning_rules = config.get('cleaning_rules', {})

        return cleaning_rules


    def _apply_cleaning_rules(
        self,
        text: str,
        rules: Dict,
    ) -> tuple[str, Dict]:
        """
        Apply YAML-defined cleaning rules to text.

        Applies patterns in this order:
            1. noise_patterns (delete matching lines)
            2. heading_patterns (prepend markdown to matching lines)

        Args:
            text: Input text to clean
            rules: Cleaning rules dictionary from YAML

        Returns:
            Tuple of (cleaned_text, statistics_dict)
            statistics_dict contains:
                - lines_removed: Number of noise lines removed
                - headings_added: Number of markdown headings added
        """
        lines = text.split('\n')
        stats = {'lines_removed': 0, 'headings_added': 0}

        # Step 1: Remove noise patterns
        noise_patterns = rules.get('noise_patterns', [])
        cleaned_lines = []

        for line in lines:
            # Check if line matches any noise pattern
            is_noise = False
            for pattern_config in noise_patterns:
                pattern = pattern_config.get('pattern', '')
                if re.match(pattern, line):
                    is_noise = True
                    stats['lines_removed'] += 1
                    break

            # Keep line if not noise
            if not is_noise:
                cleaned_lines.append(line)

        # Step 2: Add markdown headings
        heading_patterns = rules.get('heading_patterns', [])
        final_lines = []

        for line in cleaned_lines:
            # Check if line matches any heading pattern
            heading_added = False
            for pattern_config in heading_patterns:
                pattern = pattern_config.get('pattern', '')
                markdown_prefix = pattern_config.get('markdown_prefix', '## ')

                match = re.match(pattern, line)
                if match:
                    # Prepend markdown prefix
                    final_lines.append(f"{markdown_prefix}{line}")
                    stats['headings_added'] += 1
                    heading_added = True
                    break

            # Keep line as-is if no heading pattern matched
            if not heading_added:
                final_lines.append(line)

        cleaned_text = '\n'.join(final_lines)
        return cleaned_text, stats


    # ========================================================================
    # FRONTMATTER GENERATION
    # ========================================================================

    def _generate_frontmatter(
        self,
        doc_type: str,
        source_file: str,
        code: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> str:
        """
        Generate YAML frontmatter for document.

        Args:
            doc_type: Document type (e.g., 'caselaw')
            source_file: Original source file name
            code: Unique 5-letter code (if assigned)
            metadata: Extracted metadata fields (case_name, citation, etc.)

        Returns:
            YAML frontmatter string (with --- delimiters)

        Example Output:
            ---
            type: caselaw
            case_name: Indian Trail v. State Bank
            citation: 328 Ga. App. 524
            court: Ga. Ct. App.
            date: 2014-07-03
            code: AAAAA
            source_file: c.Ga_Ct_App__2014__Indian-Trail...----AAAAA.pdf
            ---
        """
        if metadata is None:
            metadata = {}

        # Build frontmatter dictionary
        frontmatter_data = {
            'type': doc_type,
            'source_file': source_file,
        }

        # Add code if available
        if code:
            frontmatter_data['code'] = code

        # Add document-specific metadata fields
        if doc_type == 'caselaw':
            if 'case_name' in metadata:
                frontmatter_data['case_name'] = metadata['case_name']
            if 'citation' in metadata:
                frontmatter_data['citation'] = metadata['citation']
            if 'court' in metadata:
                frontmatter_data['court'] = metadata['court']
            if 'date' in metadata:
                frontmatter_data['date'] = metadata['date']

        # Convert to YAML string
        yaml_content = yaml.dump(
            frontmatter_data,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,  # Preserve order
        )

        # Add YAML delimiters
        frontmatter = f"---\n{yaml_content}---"

        return frontmatter


    # ========================================================================
    # FILE OPERATIONS
    # ========================================================================

    def _save_txt_file(self, source_path: Path, content: str) -> Path:
        """
        Save cleaned text to .txt file.

        Output location: Same directory as source file
        Output name: source_filename.txt (replaces .pdf/.docx extension)

        Args:
            source_path: Original source file path
            content: Final content (frontmatter + cleaned text)

        Returns:
            Path to output .txt file

        Example:
            Input:  /docs/case.pdf
            Output: /docs/case.txt
        """
        # Generate output path (same directory, .txt extension)
        output_path = source_path.with_suffix('.txt')

        # Write file (unless dry-run mode)
        if not self.dry_run:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)

        return output_path
