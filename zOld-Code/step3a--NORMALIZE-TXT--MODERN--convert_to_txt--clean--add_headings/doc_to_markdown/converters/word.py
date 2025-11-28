"""Word document to Markdown converter using pandoc."""

import logging
import shutil
import subprocess
from pathlib import Path
from typing import Optional

from .base import BaseConverter
from ..metadata.word import WordMetadataExtractor
from ..frontmatter import FrontmatterGenerator
from ..markdown_cleaner import clean_markdown

logger = logging.getLogger(__name__)


class WordConverter(BaseConverter):
    """Convert Word documents to Markdown using pandoc."""

    def _convert_doc_to_docx(self, doc_file: Path) -> Path:
        """Convert legacy .doc file to .docx using LibreOffice.

        Args:
            doc_file: Path to .doc file

        Returns:
            Path to converted .docx file

        Raises:
            RuntimeError: If LibreOffice is not found or conversion fails
        """
        # Check if LibreOffice is available
        libreoffice_cmd = None
        for cmd in ['libreoffice', 'soffice']:
            if shutil.which(cmd):
                libreoffice_cmd = cmd
                break

        if not libreoffice_cmd:
            raise RuntimeError(
                f"Cannot convert {doc_file.name}: LibreOffice is required for .doc files. "
                "Install it with: brew install --cask libreoffice (macOS) or "
                "sudo apt-get install libreoffice (Linux)"
            )

        docx_file = doc_file.with_suffix('.docx')

        # Run LibreOffice headless conversion
        cmd = [
            libreoffice_cmd,
            '--headless',
            '--convert-to', 'docx',
            '--outdir', str(doc_file.parent),
            str(doc_file)
        ]

        try:
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True,
                timeout=60  # 60 second timeout
            )

            if not docx_file.exists():
                raise RuntimeError(f"LibreOffice conversion failed: output file not created")

            logger.info(f"Converted {doc_file.name} to {docx_file.name}")
            return docx_file

        except subprocess.TimeoutExpired:
            raise RuntimeError(f"LibreOffice conversion timed out after 60 seconds")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"LibreOffice conversion failed: {e.stderr}")

    def _validate_heading_extraction(self, markdown_content: str, source_file: Path) -> None:
        """Log warning if no headings found in converted markdown.

        Args:
            markdown_content: The converted markdown content
            source_file: Original source file path
        """
        lines = markdown_content.split('\n')
        has_headings = any(line.strip().startswith('#') for line in lines)

        if not has_headings:
            logger.warning(
                f"No headings detected in {source_file.name}. "
                f"Ensure the source document uses Word's built-in heading styles "
                f"(Heading 1, Heading 2, etc.) instead of manual bold formatting. "
                f"In Word: Select text → Home tab → Styles → Choose 'Heading 1', 'Heading 2', etc."
            )

    def convert(
        self,
        input_file: Path,
        output_file: Optional[Path] = None,
        extract_images: bool = True
    ) -> Path:
        """Convert a Word document to Markdown.

        Args:
            input_file: Path to the Word document (.docx or .doc)
            output_file: Path to output markdown file (defaults to same dir as input)
            extract_images: Whether to extract and link images

        Returns:
            Path to the created markdown file

        Raises:
            FileNotFoundError: If input file doesn't exist
            RuntimeError: If pandoc conversion fails
        """
        self._check_input_file(input_file)

        # Convert .doc to .docx if needed
        original_file = input_file
        if input_file.suffix.lower() == '.doc':
            logger.warning(
                f"Legacy .doc format detected: {input_file.name}. "
                "Converting to .docx first..."
            )
            input_file = self._convert_doc_to_docx(input_file)

        # Determine output path
        markdown_file = self._get_output_path(original_file, output_file)

        # Extract metadata
        metadata = WordMetadataExtractor.extract(input_file)

        # Build pandoc command with improved heading detection
        cmd = [
            'pandoc',
            '-f', 'docx+styles',  # Enable custom style preservation
            str(input_file),
            '-t', 'markdown',  # Explicit output format
            '-o', str(markdown_file)
        ]

        # Add options
        cmd.extend(['--markdown-headings=atx'])  # Use ATX-style headers (###)
        cmd.extend(['--wrap=none'])  # Don't wrap lines
        cmd.extend(['--track-changes=accept'])  # Handle tracked changes consistently

        # Extract images if requested
        if extract_images:
            images_dir = self._get_images_dir(markdown_file)
            cmd.extend(['--extract-media', str(images_dir.parent)])

        try:
            # Run pandoc
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True
            )

            # Read the generated markdown
            with open(markdown_file, 'r', encoding='utf-8') as f:
                markdown_content = f.read()

            # Clean markdown for RAG compatibility
            markdown_content = clean_markdown(markdown_content)

            # Validate heading extraction
            self._validate_heading_extraction(markdown_content, original_file)

            # Generate and prepend frontmatter
            frontmatter = FrontmatterGenerator.generate(metadata, input_file)
            final_content = FrontmatterGenerator.prepend_to_markdown(
                frontmatter,
                markdown_content
            )

            # Write final markdown with frontmatter
            with open(markdown_file, 'w', encoding='utf-8') as f:
                f.write(final_content)

            return markdown_file

        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"Pandoc conversion failed: {e.stderr}"
            ) from e
        except FileNotFoundError:
            raise RuntimeError(
                "Pandoc not found. Please install pandoc: https://pandoc.org/installing.html"
            )
