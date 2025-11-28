"""Batch processor for converting multiple documents."""

from pathlib import Path
from typing import List, Optional, Dict
import logging

from .converter_factory import ConverterFactory
from .file_detector import FileTypeDetector
from .tracking import ConversionTracker
from .file_status import FileStatusDetector, FileStatus


logger = logging.getLogger(__name__)


class BatchProcessor:
    """Process multiple documents in batch."""

    def __init__(
        self,
        extract_images: bool = True,
        verbose: bool = False,
        tracker: Optional[ConversionTracker] = None
    ):
        """Initialize batch processor.

        Args:
            extract_images: Whether to extract and link images
            verbose: Whether to show detailed processing information
            tracker: ConversionTracker instance (creates new one if not provided)
        """
        self.extract_images = extract_images
        self.verbose = verbose
        self.tracker = tracker or ConversionTracker()
        self.status_detector = FileStatusDetector(self.tracker)

        # Setup logging
        log_level = logging.DEBUG if verbose else logging.INFO
        logging.basicConfig(
            level=log_level,
            format='%(levelname)s: %(message)s'
        )

    def categorize_files(self, path: Path, recursive: bool = False) -> Dict[FileStatus, List[Path]]:
        """Categorize files by their conversion status.

        Args:
            path: Path to file or directory
            recursive: Whether to process directories recursively

        Returns:
            Dictionary mapping FileStatus to lists of file paths
        """
        if not path.exists():
            raise FileNotFoundError(f"Path not found: {path}")

        # Get all supported files
        if path.is_file():
            files = [path] if FileTypeDetector.is_supported(path) else []
        elif path.is_dir():
            files = self._get_supported_files(path, recursive)
        else:
            raise ValueError(f"Invalid path: {path}")

        # Categorize files using status detector
        return self.status_detector.categorize_files(
            files,
            get_output_path_func=lambda p: p.with_suffix('.md')
        )

    def process_path(self, path: Path, recursive: bool = False) -> dict:
        """Process a file or directory.

        Args:
            path: Path to file or directory
            recursive: Whether to process directories recursively

        Returns:
            Dictionary with processing statistics
        """
        if not path.exists():
            raise FileNotFoundError(f"Path not found: {path}")

        if path.is_file():
            # Process single file
            return self._process_file(path)
        elif path.is_dir():
            # Process directory
            return self._process_directory(path, recursive)
        else:
            raise ValueError(f"Invalid path: {path}")

    def _process_file(self, file_path: Path, force: bool = False) -> dict:
        """Process a single file.

        Args:
            file_path: Path to the file
            force: Whether to process even if file is unchanged (for internal use)

        Returns:
            Dictionary with processing statistics
        """
        stats = {'total': 1, 'converted': 0, 'skipped': 0, 'failed': 0}

        # Check if file type is supported
        if not FileTypeDetector.is_supported(file_path):
            logger.warning(f"Skipping unsupported file type: {file_path}")
            stats['skipped'] += 1
            return stats

        output_file = file_path.with_suffix('.md')

        # Convert file
        try:
            logger.info(f"Converting: {file_path.name}")
            ConverterFactory.convert_file(
                file_path,
                extract_images=self.extract_images
            )
            logger.info(f"✓ Converted: {output_file.name}")

            # Update tracking database on success
            self.tracker.add_conversion_record(
                source_path=file_path,
                output_path=output_file,
                status='success'
            )

            stats['converted'] += 1
        except Exception as e:
            logger.error(f"✗ Failed to convert {file_path.name}: {str(e)}")
            if self.verbose:
                logger.exception(e)

            # Record failure in tracking database
            self.tracker.add_conversion_record(
                source_path=file_path,
                output_path=output_file,
                status='failed'
            )

            stats['failed'] += 1

        return stats

    def process_files(self, files: List[Path]) -> dict:
        """Process a specific list of files.

        Args:
            files: List of file paths to process

        Returns:
            Dictionary with processing statistics
        """
        stats = {'total': 0, 'converted': 0, 'skipped': 0, 'failed': 0}

        for file_path in files:
            file_stats = self._process_file(file_path, force=True)
            stats['total'] += file_stats['total']
            stats['converted'] += file_stats['converted']
            stats['skipped'] += file_stats['skipped']
            stats['failed'] += file_stats['failed']

        return stats

    def _process_directory(self, dir_path: Path, recursive: bool) -> dict:
        """Process all supported files in a directory.

        Args:
            dir_path: Path to directory
            recursive: Whether to process subdirectories

        Returns:
            Dictionary with processing statistics
        """
        stats = {'total': 0, 'converted': 0, 'skipped': 0, 'failed': 0}

        # Get all supported files
        files = self._get_supported_files(dir_path, recursive)

        if not files:
            logger.warning(f"No supported files found in: {dir_path}")
            return stats

        logger.info(f"Found {len(files)} supported file(s)")

        # Process each file
        for file_path in files:
            file_stats = self._process_file(file_path)
            stats['total'] += file_stats['total']
            stats['converted'] += file_stats['converted']
            stats['skipped'] += file_stats['skipped']
            stats['failed'] += file_stats['failed']

        return stats

    def _get_supported_files(self, dir_path: Path, recursive: bool) -> List[Path]:
        """Get all supported files in a directory.

        Args:
            dir_path: Path to directory
            recursive: Whether to search subdirectories

        Returns:
            List of supported file paths
        """
        supported_files = []
        pattern = '**/*' if recursive else '*'

        for file_path in dir_path.glob(pattern):
            if file_path.is_file() and FileTypeDetector.is_supported(file_path):
                supported_files.append(file_path)

        return sorted(supported_files)
