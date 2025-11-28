"""PDF to Markdown converter using marker-pdf."""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

from .base import BaseConverter
from ..metadata.pdf import PDFMetadataExtractor
from ..frontmatter import FrontmatterGenerator
from ..markdown_cleaner import clean_markdown


class PDFConverter(BaseConverter):
    """Convert PDFs to Markdown using marker-pdf."""

    _marker_checked = False

    @classmethod
    def _ensure_marker_available(cls) -> bool:
        """
        Attempt to locate an existing marker installation outside this venv.

        Returns:
            True if we were able to discover and add paths for marker.
        """
        if cls._marker_checked:
            return False

        cls._marker_checked = True

        python_candidates = []
        marker_python = os.environ.get("MARKER_PYTHON")
        if marker_python:
            python_candidates.append(marker_python)

        # Fallbacks: whatever python binaries are on PATH
        for name in ("python3", "python"):
            bin_path = shutil.which(name)
            if bin_path and bin_path not in python_candidates:
                python_candidates.append(bin_path)

        # Well-known system interpreters that frequently contain marker installs
        common_paths = [
            "/usr/local/bin/python3",
            "/opt/homebrew/bin/python3",
            "/usr/bin/python3",
            "/Library/Frameworks/Python.framework/Versions/3.11/bin/python3",
            "/Library/Frameworks/Python.framework/Versions/3.12/bin/python3",
            "/Library/Frameworks/Python.framework/Versions/3.13/bin/python3",
        ]
        for path in common_paths:
            if os.path.exists(path) and path not in python_candidates:
                python_candidates.append(path)

        if not python_candidates:
            return False

        discovery_code = (
            "import json, pathlib, marker;"
            "paths = [str(pathlib.Path(p).parent) for p in marker.__path__];"
            "print(json.dumps(paths))"
        )

        for executable in python_candidates:
            try:
                result = subprocess.run(
                    [executable, "-c", discovery_code],
                    capture_output=True,
                    text=True,
                    check=True
                )
            except Exception:
                continue

            try:
                site_dirs = json.loads(result.stdout.strip())
            except json.JSONDecodeError:
                continue

            added = False
            for site_dir in site_dirs:
                if site_dir and site_dir not in sys.path:
                    sys.path.append(site_dir)
                    added = True

            if added:
                return True

        return False

    def _run_marker_conversion(
        self,
        PdfConverter,
        create_model_dict,
        text_from_rendered,
        input_file: Path,
        markdown_file: Path,
        metadata: dict,
        extract_images: bool
    ) -> Path:
        """Execute marker conversion and post-process the output."""
        # Create converter with models
        converter = PdfConverter(artifact_dict=create_model_dict())

        # Convert PDF (converter is callable)
        rendered = converter(str(input_file))

        # Extract markdown text and images
        full_text, _, images = text_from_rendered(rendered)

        # Handle images if requested and available
        if extract_images and images:
            images_dir = self._get_images_dir(markdown_file)
            images_dir.mkdir(parents=True, exist_ok=True)

            for img_name, img_pil in images.items():
                img_path = images_dir / img_name
                # Save PIL Image object
                img_pil.save(img_path)

                # Update image links in markdown to use relative paths
                full_text = full_text.replace(
                    f"]({img_name})",
                    f"](images/{img_name})"
                )

        # Clean markdown for RAG compatibility
        full_text = clean_markdown(full_text)

        # Generate and prepend frontmatter
        frontmatter = FrontmatterGenerator.generate(metadata, input_file)
        final_content = FrontmatterGenerator.prepend_to_markdown(
            frontmatter,
            full_text
        )

        # Write markdown file
        with open(markdown_file, 'w', encoding='utf-8') as f:
            f.write(final_content)

        return markdown_file

    def convert(
        self,
        input_file: Path,
        output_file: Optional[Path] = None,
        extract_images: bool = True
    ) -> Path:
        """Convert a PDF to Markdown.

        Args:
            input_file: Path to the PDF file
            output_file: Path to output markdown file (defaults to same dir as input)
            extract_images: Whether to extract and link images

        Returns:
            Path to the created markdown file

        Raises:
            FileNotFoundError: If input file doesn't exist
            RuntimeError: If marker-pdf conversion fails
        """
        self._check_input_file(input_file)

        # Determine output path
        markdown_file = self._get_output_path(input_file, output_file)

        # Extract metadata
        metadata = PDFMetadataExtractor.extract(input_file)

        try:
            from marker.converters.pdf import PdfConverter
            from marker.models import create_model_dict
            from marker.output import text_from_rendered
        except ImportError:
            if not self._ensure_marker_available():
                raise RuntimeError(
                    "marker-pdf not found in this environment. Install it with "
                    "`pip install marker-pdf` or point to an existing installation "
                    "by setting MARKER_PYTHON=/path/to/python that already has marker."
                )
            try:
                from marker.converters.pdf import PdfConverter
                from marker.models import create_model_dict
                from marker.output import text_from_rendered
            except ImportError as exc:
                raise RuntimeError(
                    "marker-pdf could not be imported even after searching your "
                    "system installation. Set MARKER_PYTHON to the Python that "
                    "already has marker installed."
                ) from exc

        try:
            return self._run_marker_conversion(
                PdfConverter,
                create_model_dict,
                text_from_rendered,
                input_file,
                markdown_file,
                metadata,
                extract_images
            )
        except Exception as e:
            raise RuntimeError(f"PDF conversion failed: {str(e)}") from e
