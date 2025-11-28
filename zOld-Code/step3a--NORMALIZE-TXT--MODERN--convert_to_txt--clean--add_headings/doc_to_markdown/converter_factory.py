"""Factory for creating appropriate converters based on file type."""

from pathlib import Path
from typing import Optional

from .file_detector import FileTypeDetector, DocumentType
from .converters import WordConverter, EbookConverter, PDFConverter
from .converters.base import BaseConverter


class ConverterFactory:
    """Factory to create appropriate converter based on file type."""

    @staticmethod
    def get_converter(file_path: Path) -> BaseConverter:
        """Get appropriate converter for the given file.

        Args:
            file_path: Path to the document file

        Returns:
            Appropriate converter instance

        Raises:
            ValueError: If file type is not supported
        """
        doc_type = FileTypeDetector.detect(file_path)

        if doc_type == DocumentType.WORD:
            return WordConverter()
        elif doc_type == DocumentType.EPUB:
            return EbookConverter()
        elif doc_type == DocumentType.MOBI:
            return EbookConverter()
        elif doc_type == DocumentType.PDF:
            return PDFConverter()
        else:
            raise ValueError(
                f"Unsupported file type: {file_path.suffix}. "
                f"Supported extensions: {FileTypeDetector.get_supported_extensions()}"
            )

    @staticmethod
    def convert_file(
        input_file: Path,
        output_file: Optional[Path] = None,
        extract_images: bool = True
    ) -> Path:
        """Convert a file to Markdown using the appropriate converter.

        Args:
            input_file: Path to the input document
            output_file: Optional path to output markdown file
            extract_images: Whether to extract and link images

        Returns:
            Path to the created markdown file

        Raises:
            ValueError: If file type is not supported
            FileNotFoundError: If input file doesn't exist
            RuntimeError: If conversion fails
        """
        converter = ConverterFactory.get_converter(input_file)
        return converter.convert(input_file, output_file, extract_images)
