"""Ebook to Markdown converter using pandoc and Calibre."""

import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from .base import BaseConverter
from ..metadata.ebook import EbookMetadataExtractor
from ..frontmatter import FrontmatterGenerator
from ..markdown_cleaner import clean_markdown


class EbookConverter(BaseConverter):
    """Convert ebooks to Markdown using pandoc and Calibre.

    Conversion workflows:
    - EPUB: EPUB → DOCX → MD
    - MOBI/AZW: MOBI → EPUB → DOCX → MD

    The intermediate DOCX step produces better heading structure.
    """

    def convert(
        self,
        input_file: Path,
        output_file: Optional[Path] = None,
        extract_images: bool = True
    ) -> Path:
        """Convert an ebook to Markdown.

        Args:
            input_file: Path to the ebook (.epub, .mobi, .azw, .azw3)
            output_file: Path to output markdown file (defaults to same dir as input)
            extract_images: Whether to extract and link images

        Returns:
            Path to the created markdown file

        Raises:
            FileNotFoundError: If input file doesn't exist
            RuntimeError: If conversion fails
        """
        self._check_input_file(input_file)

        # Determine output path
        markdown_file = self._get_output_path(input_file, output_file)

        # Extract metadata
        metadata = EbookMetadataExtractor.extract(input_file)

        extension = input_file.suffix.lower()

        if extension == '.epub':
            # Convert EPUB via DOCX intermediate
            self._convert_epub(input_file, markdown_file, extract_images)
        elif extension in {'.mobi', '.azw', '.azw3'}:
            # Convert MOBI/AZW via EPUB and DOCX intermediates
            self._convert_mobi(input_file, markdown_file, extract_images)
        else:
            raise ValueError(f"Unsupported ebook format: {extension}")

        # Read the generated markdown
        with open(markdown_file, 'r', encoding='utf-8') as f:
            markdown_content = f.read()

        # Clean markdown for RAG compatibility
        markdown_content = clean_markdown(markdown_content)

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

    def _convert_epub(
        self,
        input_file: Path,
        markdown_file: Path,
        extract_images: bool
    ) -> None:
        """Convert EPUB to Markdown via DOCX intermediate.

        Uses two-step conversion: EPUB → DOCX → MD
        This produces better heading structure than direct EPUB → MD conversion.

        Args:
            input_file: Path to EPUB file
            markdown_file: Path to output markdown file
            extract_images: Whether to extract images

        Raises:
            RuntimeError: If conversion fails
        """
        # Create temporary DOCX file
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as tmp_docx:
            tmp_docx_path = Path(tmp_docx.name)

        try:
            # Step 1: Convert EPUB to DOCX using pandoc
            cmd = ['pandoc', str(input_file), '-o', str(tmp_docx_path)]

            try:
                subprocess.run(cmd, check=True, capture_output=True, text=True)
            except subprocess.CalledProcessError as e:
                raise RuntimeError(f"Pandoc EPUB→DOCX conversion failed: {e.stderr}") from e
            except FileNotFoundError:
                raise RuntimeError(
                    "Pandoc not found. Please install pandoc: https://pandoc.org/installing.html"
                )

            # Step 2: Convert DOCX to Markdown using pandoc
            self._convert_docx_to_md(tmp_docx_path, markdown_file, extract_images)

        finally:
            # Clean up temporary DOCX file
            if tmp_docx_path.exists():
                tmp_docx_path.unlink()

    def _convert_docx_to_md(
        self,
        docx_file: Path,
        markdown_file: Path,
        extract_images: bool
    ) -> None:
        """Convert DOCX to Markdown using pandoc.

        Args:
            docx_file: Path to DOCX file
            markdown_file: Path to output markdown file
            extract_images: Whether to extract images

        Raises:
            RuntimeError: If conversion fails
        """
        # Build pandoc command
        cmd = ['pandoc', str(docx_file), '-o', str(markdown_file)]

        # Add options
        cmd.extend(['--markdown-headings=atx'])
        cmd.extend(['--wrap=none'])

        # Extract images if requested
        if extract_images:
            images_dir = self._get_images_dir(markdown_file)
            cmd.extend(['--extract-media', str(images_dir.parent)])

        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Pandoc DOCX→MD conversion failed: {e.stderr}") from e
        except FileNotFoundError:
            raise RuntimeError(
                "Pandoc not found. Please install pandoc: https://pandoc.org/installing.html"
            )

    def _convert_mobi(
        self,
        input_file: Path,
        markdown_file: Path,
        extract_images: bool
    ) -> None:
        """Convert MOBI/AZW to Markdown via EPUB and DOCX intermediates.

        Uses three-step conversion: MOBI → EPUB → DOCX → MD

        Args:
            input_file: Path to MOBI/AZW file
            markdown_file: Path to output markdown file
            extract_images: Whether to extract images

        Raises:
            RuntimeError: If conversion fails
        """
        # Create temporary EPUB file
        with tempfile.NamedTemporaryFile(suffix='.epub', delete=False) as tmp_epub:
            tmp_epub_path = Path(tmp_epub.name)

        try:
            # Convert MOBI to EPUB using Calibre's ebook-convert
            cmd = ['ebook-convert', str(input_file), str(tmp_epub_path)]

            try:
                subprocess.run(cmd, check=True, capture_output=True, text=True)
            except subprocess.CalledProcessError as e:
                raise RuntimeError(
                    f"Calibre MOBI->EPUB conversion failed: {e.stderr}"
                ) from e
            except FileNotFoundError:
                raise RuntimeError(
                    "Calibre not found. Please install Calibre: https://calibre-ebook.com/download"
                )

            # Now convert EPUB to Markdown
            self._convert_epub(tmp_epub_path, markdown_file, extract_images)

        finally:
            # Clean up temporary EPUB file
            if tmp_epub_path.exists():
                tmp_epub_path.unlink()
