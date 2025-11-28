"""
File status detection for intelligent processing decisions.

This module categorizes files based on their conversion history and modification status.
"""

from enum import Enum
from pathlib import Path
from typing import Dict, List
import logging

from .tracking import ConversionTracker

logger = logging.getLogger(__name__)


class FileStatus(Enum):
    """Status of a file relative to its conversion state."""
    NEW = "new"  # Never been converted
    MODIFIED = "modified"  # Converted before, but source file has changed
    UNCHANGED = "unchanged"  # Converted before and source file hasn't changed


class FileStatusDetector:
    """Detects and categorizes files based on their conversion status."""

    def __init__(self, tracker: ConversionTracker):
        """
        Initialize the file status detector.

        Args:
            tracker: ConversionTracker instance for querying conversion history
        """
        self.tracker = tracker

    def get_file_status(self, source_path: Path, output_path: Path) -> FileStatus:
        """
        Determine the status of a single file.

        Args:
            source_path: Path to the source document
            output_path: Path where the markdown file would be/is located

        Returns:
            FileStatus enum value
        """
        source_path = Path(source_path).resolve()
        output_path = Path(output_path).resolve()

        # Check if output file exists
        output_exists = output_path.exists()

        # Check tracking database
        record = self.tracker.get_conversion_record(source_path)

        # Case 1: No output file and no record = NEW
        if not output_exists and not record:
            return FileStatus.NEW

        # Case 2: Output exists but no record = NEW (might be manually created)
        # We'll treat it as NEW to ensure it gets tracked
        if output_exists and not record:
            return FileStatus.NEW

        # Case 3: Record exists, check if file was modified
        if record:
            # Check both file modification time and output file existence
            is_modified = self.tracker.is_file_modified(source_path)

            # If source was modified OR output no longer exists, mark as MODIFIED
            if is_modified or not output_exists:
                return FileStatus.MODIFIED

            # Otherwise, file is unchanged
            return FileStatus.UNCHANGED

        # Default to NEW for safety
        return FileStatus.NEW

    def categorize_files(
        self,
        files: List[Path],
        get_output_path_func
    ) -> Dict[FileStatus, List[Path]]:
        """
        Categorize a list of files by their conversion status.

        Args:
            files: List of source file paths to categorize
            get_output_path_func: Function that takes a source path and returns
                                  the expected output path

        Returns:
            Dictionary mapping FileStatus to lists of file paths
        """
        categorized: Dict[FileStatus, List[Path]] = {
            FileStatus.NEW: [],
            FileStatus.MODIFIED: [],
            FileStatus.UNCHANGED: []
        }

        for source_path in files:
            try:
                output_path = get_output_path_func(source_path)
                status = self.get_file_status(source_path, output_path)
                categorized[status].append(source_path)

                logger.debug(f"{source_path.name}: {status.value}")
            except Exception as e:
                logger.error(f"Error categorizing {source_path}: {e}")
                # Default to NEW on error to ensure file gets processed
                categorized[FileStatus.NEW].append(source_path)

        return categorized

    def get_summary(self, categorized_files: Dict[FileStatus, List[Path]]) -> Dict[str, int]:
        """
        Get a summary of file counts by status.

        Args:
            categorized_files: Dictionary from categorize_files()

        Returns:
            Dictionary with counts: {new: X, modified: Y, unchanged: Z, total: N}
        """
        return {
            'new': len(categorized_files[FileStatus.NEW]),
            'modified': len(categorized_files[FileStatus.MODIFIED]),
            'unchanged': len(categorized_files[FileStatus.UNCHANGED]),
            'total': sum(len(files) for files in categorized_files.values())
        }

    def filter_by_status(
        self,
        categorized_files: Dict[FileStatus, List[Path]],
        include_statuses: List[FileStatus]
    ) -> List[Path]:
        """
        Filter categorized files to include only certain statuses.

        Args:
            categorized_files: Dictionary from categorize_files()
            include_statuses: List of FileStatus values to include

        Returns:
            Flat list of file paths matching the specified statuses
        """
        result = []
        for status in include_statuses:
            result.extend(categorized_files.get(status, []))
        return result
