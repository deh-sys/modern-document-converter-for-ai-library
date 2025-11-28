"""Extract metadata from Word documents."""

from datetime import datetime
from pathlib import Path
from typing import Optional

from docx import Document


class WordMetadataExtractor:
    """Extract metadata from Word documents (.docx, .doc)."""

    @staticmethod
    def extract(file_path: Path) -> dict[str, Optional[str]]:
        """Extract metadata from a Word document.

        Args:
            file_path: Path to the Word document

        Returns:
            Dictionary containing metadata fields
        """
        metadata = {
            'title': None,
            'author': None,
            'date': None,
            'subject': None,
            'keywords': None,
        }

        try:
            # Only works with .docx files (not .doc)
            if file_path.suffix.lower() == '.docx':
                doc = Document(file_path)
                core_props = doc.core_properties

                # Extract core properties
                metadata['title'] = core_props.title or file_path.stem
                metadata['author'] = core_props.author
                metadata['subject'] = core_props.subject
                metadata['keywords'] = core_props.keywords

                # Handle date
                if core_props.created:
                    metadata['date'] = core_props.created.strftime('%Y-%m-%d')
                elif core_props.modified:
                    metadata['date'] = core_props.modified.strftime('%Y-%m-%d')
            else:
                # For .doc files, use filename as title
                metadata['title'] = file_path.stem

        except Exception as e:
            # Fallback to filename if extraction fails
            metadata['title'] = file_path.stem

        # Clean up empty values
        metadata = {k: v for k, v in metadata.items() if v}

        return metadata
