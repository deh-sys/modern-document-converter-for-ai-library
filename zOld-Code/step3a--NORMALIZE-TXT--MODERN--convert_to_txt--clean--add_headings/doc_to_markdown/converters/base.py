"""Base converter class for all document converters."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional


class BaseConverter(ABC):
    """Base class for document converters."""

    @abstractmethod
    def convert(
        self,
        input_file: Path,
        output_file: Optional[Path] = None,
        extract_images: bool = True
    ) -> Path:
        """Convert a document to Markdown.

        Args:
            input_file: Path to the input document
            output_file: Path to output markdown file (defaults to same dir as input)
            extract_images: Whether to extract and link images

        Returns:
            Path to the created markdown file

        Raises:
            FileNotFoundError: If input file doesn't exist
            RuntimeError: If conversion fails
        """
        pass

    @staticmethod
    def _get_output_path(input_file: Path, output_file: Optional[Path] = None) -> Path:
        """Determine the output markdown file path.

        Args:
            input_file: Path to the input document
            output_file: Optional explicit output path

        Returns:
            Path where markdown should be written
        """
        if output_file:
            return output_file
        else:
            # Same directory and name as input, but with .md extension
            return input_file.with_suffix('.md')

    @staticmethod
    def _get_images_dir(markdown_file: Path) -> Path:
        """Get the images directory for extracted images.

        Args:
            markdown_file: Path to the markdown file

        Returns:
            Path to images directory (relative to markdown file)
        """
        return markdown_file.parent / 'images'

    @staticmethod
    def _check_input_file(input_file: Path) -> None:
        """Validate that input file exists.

        Args:
            input_file: Path to check

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        if not input_file.exists():
            raise FileNotFoundError(f"Input file not found: {input_file}")
        if not input_file.is_file():
            raise ValueError(f"Input path is not a file: {input_file}")
