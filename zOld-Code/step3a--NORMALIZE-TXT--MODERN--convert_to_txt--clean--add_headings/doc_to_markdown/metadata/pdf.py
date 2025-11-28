"""Extract metadata from PDF files."""

from pathlib import Path
from typing import Optional

try:
    from PyPDF2 import PdfReader
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False


class PDFMetadataExtractor:
    """Extract metadata from PDF files."""

    @staticmethod
    def extract(file_path: Path) -> dict[str, Optional[str]]:
        """Extract metadata from a PDF file.

        Args:
            file_path: Path to the PDF file

        Returns:
            Dictionary containing metadata fields
        """
        metadata = {
            'title': None,
            'author': None,
            'subject': None,
            'creator': None,
            'producer': None,
            'date': None,
        }

        if not PYPDF2_AVAILABLE:
            metadata['title'] = file_path.stem
            return metadata

        try:
            reader = PdfReader(file_path)
            pdf_metadata = reader.metadata

            if pdf_metadata:
                # Extract standard PDF metadata
                metadata['title'] = pdf_metadata.get('/Title')
                metadata['author'] = pdf_metadata.get('/Author')
                metadata['subject'] = pdf_metadata.get('/Subject')
                metadata['creator'] = pdf_metadata.get('/Creator')
                metadata['producer'] = pdf_metadata.get('/Producer')

                # Handle creation/modification date
                creation_date = pdf_metadata.get('/CreationDate')
                mod_date = pdf_metadata.get('/ModDate')

                if creation_date:
                    metadata['date'] = PDFMetadataExtractor._parse_pdf_date(creation_date)
                elif mod_date:
                    metadata['date'] = PDFMetadataExtractor._parse_pdf_date(mod_date)

        except Exception as e:
            # Fallback to filename
            pass

        # Clean up empty values
        metadata = {k: v for k, v in metadata.items() if v}

        # Ensure title exists
        if 'title' not in metadata:
            metadata['title'] = file_path.stem

        return metadata

    @staticmethod
    def _parse_pdf_date(pdf_date: str) -> Optional[str]:
        """Parse PDF date format to YYYY-MM-DD.

        PDF dates are in format: D:YYYYMMDDHHmmSSOHH'mm'
        Example: D:20231215103045+05'30'

        Args:
            pdf_date: PDF date string

        Returns:
            Date in YYYY-MM-DD format, or None if parsing fails
        """
        try:
            # Remove D: prefix if present
            if pdf_date.startswith('D:'):
                pdf_date = pdf_date[2:]

            # Extract YYYYMMDD
            if len(pdf_date) >= 8:
                year = pdf_date[0:4]
                month = pdf_date[4:6]
                day = pdf_date[6:8]
                return f"{year}-{month}-{day}"

        except Exception:
            pass

        return None
