"""
PDF text extraction module.
Extracts text from first N pages of a PDF file, avoiding margin content.
"""

import subprocess
import re
from pathlib import Path

# Constants
DEFAULT_PDF_TIMEOUT = 30  # seconds - increased from 10 to handle larger PDFs
MULTIZONE_PDF_TIMEOUT = 45  # seconds - for multizone extraction


class PDFExtractor:
    """Extract text from PDF files using pdftotext."""

    def __init__(self, max_pages=2, timeout=DEFAULT_PDF_TIMEOUT):
        """
        Initialize PDF extractor.

        Args:
            max_pages: Maximum number of pages to extract (default: 2)
            timeout: Timeout in seconds for PDF extraction (default: 30)
        """
        self.max_pages = max_pages
        self.timeout = timeout

    @staticmethod
    def check_pdftotext_available():
        """
        Check if pdftotext command is available.

        Returns:
            tuple: (available: bool, error_message: str or None)
        """
        try:
            result = subprocess.run(
                ['pdftotext', '-v'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return (True, None)
        except FileNotFoundError:
            error_msg = (
                "pdftotext not found. Please install poppler-utils:\n"
                "  macOS:   brew install poppler\n"
                "  Ubuntu:  sudo apt-get install poppler-utils\n"
                "  Windows: Download from https://blog.alivate.com.au/poppler-windows/"
            )
            return (False, error_msg)
        except Exception as e:
            return (False, f"Error checking pdftotext: {e}")

    def extract_text(self, pdf_path):
        """
        Extract text from PDF file.

        Args:
            pdf_path: Path to PDF file

        Returns:
            str: Extracted text or None if extraction fails
        """
        pdf_path = Path(pdf_path)

        if not pdf_path.exists():
            return None

        try:
            result = subprocess.run(
                [
                    'pdftotext',
                    '-f', '1',
                    '-l', str(self.max_pages),
                    '-layout',
                    str(pdf_path),
                    '-'
                ],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )

            if result.returncode == 0:
                return result.stdout
            else:
                return None

        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            return None

    def get_main_content(self, text):
        """
        Filter out margin content and focus on main body text.

        Args:
            text: Raw PDF text

        Returns:
            str: Filtered text with reduced margin content
        """
        if not text:
            return ""

        lines = text.split('\n')

        # Filter out very short lines that are likely headers/footers
        # But keep lines with key context words
        important_words = [
            'decided', 'filed', 'dated', 'court', 'circuit', 'district',
            'supreme', 'appeals', 'opinion', 'v.', 'vs.'
        ]

        filtered_lines = []
        for line in lines:
            line_stripped = line.strip()

            # Keep line if:
            # - It's substantial (>20 chars)
            # - OR it contains important context words
            if len(line_stripped) > 20 or any(
                word in line_stripped.lower()
                for word in important_words
            ):
                filtered_lines.append(line)

        return '\n'.join(filtered_lines)

    def extract_text_multizone(self, pdf_path, first_pages=5, last_pages=2):
        """
        Extract text from multiple zones of PDF for comprehensive metadata extraction.
        Reads first N pages + last M pages to capture headers and conclusions.

        Args:
            pdf_path: Path to PDF file
            first_pages: Number of pages to read from beginning (default: 5)
            last_pages: Number of pages to read from end (default: 2)

        Returns:
            str: Combined extracted text from both zones, or None if extraction fails
        """
        pdf_path = Path(pdf_path)

        if not pdf_path.exists():
            return None

        try:
            # First, get total page count using pdfinfo
            info_result = subprocess.run(
                ['pdfinfo', str(pdf_path)],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )

            total_pages = None
            if info_result.returncode == 0:
                for line in info_result.stdout.split('\n'):
                    if line.startswith('Pages:'):
                        total_pages = int(line.split(':')[1].strip())
                        break

            # Extract first pages
            first_result = subprocess.run(
                [
                    'pdftotext',
                    '-f', '1',
                    '-l', str(first_pages),
                    '-layout',
                    str(pdf_path),
                    '-'
                ],
                capture_output=True,
                text=True,
                timeout=MULTIZONE_PDF_TIMEOUT
            )

            first_text = ''
            if first_result.returncode == 0:
                first_text = self.get_main_content(first_result.stdout)

            # Extract last pages if we know total page count
            last_text = ''
            if total_pages and total_pages > first_pages:
                start_page = max(first_pages + 1, total_pages - last_pages + 1)
                last_result = subprocess.run(
                    [
                        'pdftotext',
                        '-f', str(start_page),
                        '-l', str(total_pages),
                        '-layout',
                        str(pdf_path),
                        '-'
                    ],
                    capture_output=True,
                    text=True,
                    timeout=MULTIZONE_PDF_TIMEOUT
                )

                if last_result.returncode == 0:
                    last_text = self.get_main_content(last_result.stdout)

            # Combine both zones with a marker
            combined = first_text
            if last_text:
                combined += '\n\n[LAST_PAGES_SECTION]\n\n' + last_text

            return combined if combined else None

        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            # Fallback to regular extraction if multizone fails
            return self.extract_text(pdf_path)

    def find_case_caption(self, text):
        """
        Find the case caption (case name) in PDF text.

        Args:
            text: PDF text

        Returns:
            str: Case caption or None
        """
        if not text:
            return None

        lines = text.split('\n')

        # Look for "v." or "vs." pattern which indicates case name
        # Check first 40 lines
        for i, line in enumerate(lines[:40]):
            if re.search(r'\s+v\.?\s+', line, re.IGNORECASE):
                # Found a "v" - get context around it
                # Look at surrounding lines for full case name
                start = max(0, i - 2)
                end = min(len(lines), i + 3)
                context = '\n'.join(lines[start:end])

                # Try to extract the case name from this context
                # Look for pattern: "Party v. Party"
                match = re.search(
                    r'([A-Z][A-Za-z\s,\.&\'\-]+?)\s+v\.?\s+([A-Za-z\s,\.&\'\-]+?)(?:\n|$)',
                    context,
                    re.IGNORECASE
                )

                if match:
                    return f"{match.group(1).strip()} v. {match.group(2).strip()}"

        return None
