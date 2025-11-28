"""Extract metadata from ebooks (EPUB, MOBI, AZW)."""

from pathlib import Path
from typing import Optional
import subprocess
import json

try:
    from ebooklib import epub
    EBOOKLIB_AVAILABLE = True
except ImportError:
    EBOOKLIB_AVAILABLE = False


class EbookMetadataExtractor:
    """Extract metadata from ebook files."""

    @staticmethod
    def extract(file_path: Path) -> dict[str, Optional[str]]:
        """Extract metadata from an ebook file.

        Args:
            file_path: Path to the ebook file

        Returns:
            Dictionary containing metadata fields
        """
        extension = file_path.suffix.lower()

        if extension == '.epub':
            return EbookMetadataExtractor._extract_epub(file_path)
        elif extension in {'.mobi', '.azw', '.azw3'}:
            return EbookMetadataExtractor._extract_mobi(file_path)
        else:
            return {'title': file_path.stem}

    @staticmethod
    def _extract_epub(file_path: Path) -> dict[str, Optional[str]]:
        """Extract metadata from EPUB file.

        Args:
            file_path: Path to EPUB file

        Returns:
            Dictionary containing metadata
        """
        metadata = {
            'title': None,
            'author': None,
            'date': None,
            'publisher': None,
            'language': None,
        }

        if not EBOOKLIB_AVAILABLE:
            metadata['title'] = file_path.stem
            return metadata

        try:
            book = epub.read_epub(file_path)

            # Extract Dublin Core metadata
            metadata['title'] = book.get_metadata('DC', 'title')
            if metadata['title']:
                metadata['title'] = metadata['title'][0][0] if metadata['title'] else None

            metadata['author'] = book.get_metadata('DC', 'creator')
            if metadata['author']:
                metadata['author'] = metadata['author'][0][0] if metadata['author'] else None

            metadata['date'] = book.get_metadata('DC', 'date')
            if metadata['date']:
                metadata['date'] = metadata['date'][0][0] if metadata['date'] else None

            metadata['publisher'] = book.get_metadata('DC', 'publisher')
            if metadata['publisher']:
                metadata['publisher'] = metadata['publisher'][0][0] if metadata['publisher'] else None

            metadata['language'] = book.get_metadata('DC', 'language')
            if metadata['language']:
                metadata['language'] = metadata['language'][0][0] if metadata['language'] else None

        except Exception as e:
            # Fallback to filename
            metadata['title'] = file_path.stem

        # Clean up empty values
        metadata = {k: v for k, v in metadata.items() if v}

        # Ensure title exists
        if 'title' not in metadata:
            metadata['title'] = file_path.stem

        return metadata

    @staticmethod
    def _extract_mobi(file_path: Path) -> dict[str, Optional[str]]:
        """Extract metadata from MOBI/AZW file using Calibre.

        Args:
            file_path: Path to MOBI/AZW file

        Returns:
            Dictionary containing metadata
        """
        metadata = {
            'title': file_path.stem,
            'author': None,
            'date': None,
        }

        try:
            # Try using Calibre's ebook-meta command
            result = subprocess.run(
                ['ebook-meta', str(file_path)],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                # Parse the output
                for line in result.stdout.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        key = key.strip().lower()
                        value = value.strip()

                        if key == 'title' and value:
                            metadata['title'] = value
                        elif key in ['author(s)', 'author'] and value:
                            metadata['author'] = value
                        elif key in ['published', 'date'] and value:
                            metadata['date'] = value

        except (subprocess.SubprocessError, FileNotFoundError):
            # Calibre not available or command failed
            pass

        # Clean up empty values
        metadata = {k: v for k, v in metadata.items() if v}

        return metadata
