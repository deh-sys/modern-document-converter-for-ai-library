"""
Main file renaming engine for law journal articles.
Coordinates all extractors to generate standardized filenames.
"""

import json
import re
from pathlib import Path
from extractors.pdf_extractor import PDFExtractor
from extractors.docx_extractor import DocxExtractor
from extractors.author_extractor import AuthorExtractor
from extractors.title_extractor import TitleExtractor
from extractors.journal_extractor import JournalExtractor
from extractors.date_extractor import DateExtractor
from extractors.metadata_extractor import MetadataExtractor
from formatters.title_formatter import TitleFormatter
from registry_manager import RegistryManager
from filename_evaluator import FilenameEvaluator

# Constants for filename validation
MAX_FILENAME_LENGTH = 255  # Maximum filename length for most filesystems
ILLEGAL_FILENAME_CHARS = r'[<>:"/\\|?*\x00-\x1f]'  # Characters not allowed in filenames


class ArticleRenamer:
    """Main renaming engine for law journal article files."""

    def __init__(self):
        """Initialize renamer with all extractors."""
        self.pdf_extractor = PDFExtractor(max_pages=3)  # First 3 pages for articles
        self.docx_extractor = DocxExtractor()
        self.author_extractor = AuthorExtractor()
        self.title_extractor = TitleExtractor()
        self.journal_extractor = JournalExtractor()
        self.date_extractor = DateExtractor()
        self.title_formatter = TitleFormatter(max_words=6)
        self.metadata_extractor = MetadataExtractor(
            date_extractor=self.date_extractor,
            author_extractor=self.author_extractor
        )
        self.filename_evaluator = FilenameEvaluator()

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
            'authors': [],
            'authors_source': None,
            'title': None,
            'title_source': None,
            'year': None,
            'year_source': None,
            'journal_name': None,
            'volume': None,
            'issue': None,
            'page_start': None,
            'new_filename': None,
            'confidence': 'UNKNOWN',
            'notes': []
        }

        # 1. Extract Authors
        author_data = self.author_extractor.extract_from_document(document_text)
        if author_data['authors']:
            result['authors'] = author_data['authors']
            result['authors_source'] = 'document'
        else:
            # Fallback to filename
            author = self.author_extractor.extract_from_filename(original_filename)
            if author:
                result['authors'] = [author]
                result['authors_source'] = 'filename'
                result['notes'].append('Author from filename (document extraction failed)')

        # 2. Extract Title
        title = self.title_extractor.extract_from_document(document_text)
        if title:
            result['title'] = title
            result['title_source'] = 'document'
        else:
            title = self.title_extractor.extract_from_filename(original_filename)
            if title:
                result['title'] = title
                result['title_source'] = 'filename'
                result['notes'].append('Title from filename (document extraction failed)')

        # 3. Extract Year
        year = self.date_extractor.extract_from_document(document_text)
        if year:
            result['year'] = year
            result['year_source'] = 'document'
        else:
            year = self.date_extractor.extract_from_filename(original_filename)
            if year:
                result['year'] = year
                result['year_source'] = 'filename'
                result['notes'].append('Year from filename (document extraction failed)')

        # 4. Extract Journal metadata
        journal_data = self.journal_extractor.extract_from_document(document_text)
        result['journal_name'] = journal_data.get('journal_name')
        result['volume'] = journal_data.get('volume')
        result['issue'] = journal_data.get('issue')
        result['page_start'] = journal_data.get('page_start')

        # Generate filename if we have minimum required fields
        if result['authors'] and result['year'] and result['title']:
            # Format: [year]_[author_last]_[short_title].pdf
            author_formatted = self.author_extractor.format_author_for_filename(result['authors'])
            title_formatted = self.title_formatter.format_for_filename(result['title'])

            # Build filename
            new_filename = f"{result['year']}_{author_formatted}_{title_formatted}{extension}"

            # Sanitize and validate
            new_filename = self.sanitize_filename(new_filename)
            new_filename, was_truncated, warning = self.validate_and_truncate_filename(new_filename)

            if was_truncated:
                result['notes'].append(warning)

            result['new_filename'] = new_filename

            # Calculate confidence
            result['confidence'] = self._calculate_confidence(result)
        else:
            # Missing required fields
            result['error'] = 'Missing required fields for filename generation'
            result['notes'].append(f"Missing: {', '.join([f for f in ['authors', 'year', 'title'] if not result.get(f)])}")

        # Evaluate original filename quality
        filename_quality, quality_score, quality_reasons = self.filename_evaluator.evaluate_quality(file_path.name)
        result['original_filename_quality'] = filename_quality
        result['filename_quality_score'] = quality_score
        result['filename_quality_reasons'] = quality_reasons

        # Determine if we should replace the filename
        should_replace, replace_reason = self.filename_evaluator.should_replace(
            result['confidence'],
            filename_quality
        )
        result['should_rename'] = should_replace
        result['rename_decision_reason'] = replace_reason

        return result

    def _calculate_confidence(self, result):
        """
        Calculate extraction confidence based on sources.

        Args:
            result: Extraction result dictionary

        Returns:
            str: HIGH, MEDIUM, or LOW
        """
        doc_count = 0

        # Count fields extracted from document
        if result.get('authors_source') == 'document':
            doc_count += 1
        if result.get('title_source') == 'document':
            doc_count += 1
        if result.get('year_source') == 'document':
            doc_count += 1

        # HIGH: All 3 core fields from document
        if doc_count >= 3:
            return 'HIGH'
        # MEDIUM: 2 fields from document
        elif doc_count >= 2:
            return 'MEDIUM'
        # LOW: Mostly from filename
        else:
            return 'LOW'

    def rename_file(self, file_path, dry_run=False):
        """
        Rename a file based on extracted metadata.

        Args:
            file_path: Path to file
            dry_run: If True, don't actually rename (default: False)

        Returns:
            dict: Result with success status and paths
        """
        result = self.process_file(file_path)

        if not result.get('new_filename'):
            return {
                'success': False,
                'original_path': str(file_path),
                'error': result.get('error', 'Could not generate filename'),
                'result': result
            }

        file_path = Path(file_path)
        new_path = file_path.parent / result['new_filename']

        # Check if file already exists
        if new_path.exists() and new_path != file_path:
            # Handle duplicate by adding _1, _2, etc.
            counter = 1
            stem = new_path.stem
            suffix = new_path.suffix

            while new_path.exists():
                new_filename = f"{stem}_{counter}{suffix}"
                new_path = file_path.parent / new_filename
                counter += 1

            result['notes'].append(f"Renamed to avoid duplicate (added _{counter-1})")
            result['new_filename'] = new_path.name

        if not dry_run:
            # Actually rename the file
            try:
                file_path.rename(new_path)
                return {
                    'success': True,
                    'original_path': str(file_path),
                    'new_path': str(new_path),
                    'result': result
                }
            except Exception as e:
                return {
                    'success': False,
                    'original_path': str(file_path),
                    'error': f"Rename failed: {str(e)}",
                    'result': result
                }
        else:
            # Dry run - just return what would happen
            return {
                'success': True,
                'dry_run': True,
                'original_path': str(file_path),
                'new_path': str(new_path),
                'result': result
            }

    def process_directory(self, directory_path):
        """
        Process all PDF and DOCX files in a directory.

        Args:
            directory_path: Path to directory

        Returns:
            list: Results for all processed files
        """
        directory_path = Path(directory_path)
        results = []

        # Find all PDF and DOCX files
        for ext in ['*.pdf', '*.docx']:
            for file_path in directory_path.glob(ext):
                result = self.process_file(file_path)
                results.append(result)

        return results

    def extract_metadata(self, result):
        """
        Extract comprehensive metadata from a processed file result.

        Args:
            result: Result dictionary from process_file()

        Returns:
            dict: Comprehensive metadata
        """
        document_text = result.get('document_text', '')
        metadata = self.metadata_extractor.extract_metadata(result, document_text)
        return metadata

    def save_metadata_json(self, result, metadata, registry_path=None):
        """
        Save metadata to JSON sidecar file and optionally to central registry.

        Args:
            result: Result dictionary from process_file()
            metadata: Metadata dictionary
            registry_path: Optional path for central registry

        Returns:
            dict: Paths to created files {'sidecar': Path, 'registry_json': Path, 'registry_csv': Path}
        """
        import json
        from pathlib import Path

        file_path = Path(result['file_path'])
        sidecar_path = file_path.with_suffix(file_path.suffix + '.metadata.json')

        # Save sidecar JSON
        with open(sidecar_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        paths = {'sidecar': sidecar_path, 'registry_json': None, 'registry_csv': None}

        # Save to central registry if requested
        if registry_path:
            registry_manager = RegistryManager(registry_path)
            registry_manager.add_entry(metadata)
            registry_manager.save()

            paths['registry_json'] = Path(f"{registry_path}.json")
            paths['registry_csv'] = Path(f"{registry_path}.csv")

        return paths
