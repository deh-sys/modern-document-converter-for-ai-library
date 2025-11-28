"""
Main file renaming engine.
Coordinates all extractors to generate standardized filenames.
"""

import json
import re
from pathlib import Path
from extractors.pdf_extractor import PDFExtractor
from extractors.docx_extractor import DocxExtractor
from extractors.court_extractor import CourtExtractor
from extractors.date_extractor import DateExtractor
from extractors.reporter_extractor import ReporterExtractor
from extractors.metadata_extractor import MetadataExtractor
from formatters.case_name_formatter import CaseNameFormatter
from registry_manager import RegistryManager

# Constants for filename validation
MAX_FILENAME_LENGTH = 255  # Maximum filename length for most filesystems
ILLEGAL_FILENAME_CHARS = r'[<>:"/\\|?*\x00-\x1f]'  # Characters not allowed in filenames


class CaselawRenamer:
    """Main renaming engine for caselaw files."""

    def __init__(self):
        """Initialize renamer with all extractors."""
        self.pdf_extractor = PDFExtractor(max_pages=2)
        self.docx_extractor = DocxExtractor()
        self.court_extractor = CourtExtractor()
        self.date_extractor = DateExtractor()
        self.reporter_extractor = ReporterExtractor()
        self.case_formatter = CaseNameFormatter(max_words_per_party=1)
        self.metadata_extractor = MetadataExtractor(date_extractor=self.date_extractor)

    @staticmethod
    def sanitize_filename(filename):
        """
        Remove illegal characters from filename.

        Args:
            filename: Filename to sanitize

        Returns:
            str: Sanitized filename
        """
        # Remove illegal characters
        sanitized = re.sub(ILLEGAL_FILENAME_CHARS, '', filename)
        # Remove any remaining control characters
        sanitized = ''.join(char for char in sanitized if ord(char) >= 32)
        # Remove leading/trailing spaces and dots
        sanitized = sanitized.strip('. ')
        return sanitized

    @staticmethod
    def validate_and_truncate_filename(filename, max_length=MAX_FILENAME_LENGTH):
        """
        Validate filename length and truncate if needed.

        Args:
            filename: Full filename including extension
            max_length: Maximum allowed length (default: 255)

        Returns:
            tuple: (truncated_filename, was_truncated: bool, warning_message or None)
        """
        if len(filename) <= max_length:
            return (filename, False, None)

        # Split into stem and extension
        parts = filename.rsplit('.', 1)
        if len(parts) == 2:
            stem, ext = parts
            # Reserve space for extension + dot
            max_stem_length = max_length - len(ext) - 1
            if max_stem_length > 0:
                truncated_stem = stem[:max_stem_length]
                truncated = f"{truncated_stem}.{ext}"
                warning = f"Filename truncated from {len(filename)} to {len(truncated)} characters"
                return (truncated, True, warning)

        # Fallback: just truncate the whole thing
        truncated = filename[:max_length]
        warning = f"Filename truncated from {len(filename)} to {max_length} characters"
        return (truncated, True, warning)

    def process_file(self, file_path):
        """
        Process a single file and generate new filename.

        Args:
            file_path: Path to PDF or DOCX file

        Returns:
            dict: Extraction results with new filename and confidence
        """
        file_path = Path(file_path)
        original_filename = file_path.stem
        extension = file_path.suffix.lower()

        # Extract text based on file type
        if extension == '.pdf':
            document_text = self.pdf_extractor.extract_text(file_path)
        elif extension == '.docx':
            document_text = self.docx_extractor.extract_text(file_path)
        else:
            # Unsupported file type
            return {
                'original_filename': file_path.name,
                'file_path': str(file_path),
                'error': f'Unsupported file type: {extension}',
                'new_filename': None
            }

        # Extract all elements
        result = {
            'original_filename': file_path.name,
            'file_path': str(file_path),
            'document_text': document_text,  # Store for metadata extraction
            'court': None,
            'court_source': None,
            'year': None,
            'year_source': None,
            'case_name': None,
            'case_name_source': None,
            'reporter': None,
            'reporter_source': None,
            'new_filename': None,
            'confidence': 'UNKNOWN',
            'notes': []
        }

        # 1. Extract Court
        court = self.court_extractor.extract_from_pdf(document_text)
        if court:
            result['court'] = court
            result['court_source'] = 'document'
        else:
            court = self.court_extractor.extract_from_filename(original_filename)
            if court:
                result['court'] = court
                result['court_source'] = 'filename'
                result['notes'].append('Court from filename (document extraction failed)')

        # 2. Extract Year
        year = self.date_extractor.extract_from_pdf(document_text)
        if year:
            result['year'] = year
            result['year_source'] = 'document'
        else:
            year = self.date_extractor.extract_from_filename(original_filename)
            if year:
                result['year'] = year
                result['year_source'] = 'filename'
                result['notes'].append('Year from filename (document extraction failed)')

        # 3. Extract Case Name
        raw_case_name = self.case_formatter.extract_from_pdf(document_text)
        if raw_case_name:
            result['case_name_source'] = 'document'
        else:
            raw_case_name = self.case_formatter.extract_from_filename(original_filename)
            result['case_name_source'] = 'filename'

        # Expand abbreviations and format
        if raw_case_name:
            raw_case_name = self.case_formatter.expand_abbreviations(raw_case_name)
            case_name = self.case_formatter.format_case_name(raw_case_name)
            result['case_name'] = case_name
        else:
            result['case_name'] = 'Unknown'
            result['notes'].append('Case name could not be extracted')

        # 4. Extract Reporter Citation
        citation = self.reporter_extractor.extract_from_pdf(document_text)
        if citation:
            volume, reporter, page = citation
            reporter_formatted = self.reporter_extractor.format_citation(volume, reporter, page)
            result['reporter'] = reporter_formatted
            result['reporter_source'] = 'document'
        else:
            citation = self.reporter_extractor.extract_from_filename(original_filename)
            if citation:
                volume, reporter, page = citation
                reporter_formatted = self.reporter_extractor.format_citation(volume, reporter, page)
                result['reporter'] = reporter_formatted
                result['reporter_source'] = 'filename'
            else:
                result['reporter'] = 'Unpub'
                result['reporter_source'] = 'fallback'
                result['notes'].append('No reporter citation found - marked as Unpub')

        # 5. Calculate Confidence
        result['confidence'] = self._calculate_confidence(result)

        # 6. Build New Filename
        if result['court'] and result['year'] and result['case_name'] and result['reporter']:
            # Build initial filename
            new_filename = f"c.{result['court']}__{result['year']}__{result['case_name']}__{result['reporter']}{extension}"

            # Sanitize to remove illegal characters
            new_filename = self.sanitize_filename(new_filename)

            # Validate length and truncate if needed
            new_filename, was_truncated, truncate_warning = self.validate_and_truncate_filename(new_filename)

            if was_truncated:
                result['notes'].append(truncate_warning)

            result['new_filename'] = new_filename
        else:
            result['new_filename'] = None
            # More specific error message about what's missing
            missing = []
            if not result['court']:
                missing.append('court')
            if not result['year']:
                missing.append('year')
            if not result['case_name']:
                missing.append('case name')
            if not result['reporter']:
                missing.append('reporter')
            result['notes'].append(f'Could not generate filename - missing: {", ".join(missing)}')

        return result

    def _calculate_confidence(self, result):
        """
        Calculate confidence score for extraction.

        Args:
            result: Extraction result dict

        Returns:
            str: Confidence level (HIGH, MEDIUM, LOW)
        """
        document_sources = sum([
            1 for key in ['court_source', 'year_source', 'case_name_source', 'reporter_source']
            if result.get(key) == 'document'
        ])

        if document_sources >= 3:
            return 'HIGH'
        elif document_sources >= 2:
            return 'MEDIUM'
        else:
            return 'LOW'

    def process_directory(self, directory_path, recursive=False):
        """
        Process all PDF and DOCX files in a directory.

        Args:
            directory_path: Path to directory
            recursive: Whether to search recursively

        Returns:
            list: List of extraction results
        """
        directory_path = Path(directory_path)
        results = []

        # Find all PDF and DOCX files (case-insensitive)
        all_files = []
        if recursive:
            # Case-insensitive search for PDF files
            for pattern in ['*.pdf', '*.PDF', '*.Pdf']:
                all_files.extend(directory_path.rglob(pattern))
            # Case-insensitive search for DOCX files
            for pattern in ['*.docx', '*.DOCX', '*.Docx']:
                all_files.extend(directory_path.rglob(pattern))
        else:
            # Case-insensitive search for PDF files
            for pattern in ['*.pdf', '*.PDF', '*.Pdf']:
                all_files.extend(directory_path.glob(pattern))
            # Case-insensitive search for DOCX files
            for pattern in ['*.docx', '*.DOCX', '*.Docx']:
                all_files.extend(directory_path.glob(pattern))

        # Remove duplicates and sort
        all_files = sorted(set(all_files))

        for file_path in all_files:
            result = self.process_file(file_path)
            results.append(result)

        return results

    def rename_file(self, file_path, new_filename, dry_run=True):
        """
        Rename a file to new filename with duplicate detection.

        Args:
            file_path: Original file path
            new_filename: New filename
            dry_run: If True, don't actually rename (default: True)

        Returns:
            tuple: (success: bool, actual_filename: str, error_message: str or None)
        """
        file_path = Path(file_path)
        new_path = file_path.parent / new_filename

        if dry_run:
            return (True, new_filename, None)

        # Check for duplicates and add counter if needed
        final_path = new_path
        counter = 1
        while final_path.exists() and final_path != file_path:
            # Add counter before extension
            stem = new_path.stem
            suffix = new_path.suffix
            final_path = new_path.parent / f"{stem}_{counter}{suffix}"
            counter += 1

        try:
            file_path.rename(final_path)
            actual_filename = final_path.name
            if counter > 1:
                return (True, actual_filename, f"Renamed to avoid duplicate (added _{counter-1})")
            return (True, actual_filename, None)
        except PermissionError as e:
            return (False, new_filename, f"Permission denied: {e}")
        except OSError as e:
            return (False, new_filename, f"OS error: {e}")
        except Exception as e:
            return (False, new_filename, f"Unexpected error: {e}")

    def extract_metadata(self, result):
        """
        Extract comprehensive metadata from processing result.

        Args:
            result: Dictionary from process_file()

        Returns:
            dict: Metadata dictionary with all extracted fields
        """
        # Use multizone text for comprehensive metadata extraction
        file_path = result.get('file_path', '')
        if file_path:
            path = Path(file_path)
            extension = path.suffix.lower()

            # Extract multizone text based on file type
            if extension == '.pdf':
                multizone_text = self.pdf_extractor.extract_text_multizone(file_path)
            elif extension == '.docx':
                multizone_text = self.docx_extractor.extract_text_multizone(file_path)
            else:
                multizone_text = result.get('document_text', '')
        else:
            multizone_text = result.get('document_text', '')

        return self.metadata_extractor.extract_metadata(result, multizone_text)

    def save_metadata_json(self, result, metadata, output_dir=None, registry_path=None):
        """
        Save metadata to JSON sidecar file and optionally update central registry.

        Args:
            result: Processing result dict
            metadata: Metadata dict from extract_metadata()
            output_dir: Optional output directory (default: same as PDF)
            registry_path: Optional path prefix for central registry (creates .json and .csv)

        Returns:
            dict: Paths to created files {'sidecar': Path, 'registry_json': Path, 'registry_csv': Path}
        """
        paths = {
            'sidecar': None,
            'registry_json': None,
            'registry_csv': None
        }

        try:
            file_path = Path(result.get('file_path', ''))

            if not file_path.exists():
                return paths

            # 1. Save sidecar JSON
            if output_dir:
                output_dir = Path(output_dir)
                output_dir.mkdir(parents=True, exist_ok=True)
                json_path = output_dir / f"{file_path.name}.metadata.json"
            else:
                # Save in same directory as PDF
                json_path = file_path.parent / f"{file_path.name}.metadata.json"

            # Write sidecar JSON with pretty formatting
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)

            paths['sidecar'] = json_path

            # 2. Update central registry if path provided
            if registry_path:
                try:
                    registry_manager = RegistryManager(registry_path)
                    reg_json, reg_csv = registry_manager.update_registry(metadata)
                    paths['registry_json'] = reg_json
                    paths['registry_csv'] = reg_csv
                except Exception as e:
                    print(f"Error updating central registry: {e}")

            return paths

        except Exception as e:
            print(f"Error saving metadata: {e}")
            return paths
