"""YAML frontmatter generator for markdown files."""

from datetime import datetime
from pathlib import Path
from typing import Optional
import yaml


class FrontmatterGenerator:
    """Generate YAML frontmatter for markdown files."""

    @staticmethod
    def generate(
        metadata: dict,
        source_file: Path,
        conversion_date: Optional[str] = None
    ) -> str:
        """Generate YAML frontmatter from metadata.

        Args:
            metadata: Dictionary of metadata fields
            source_file: Path to the source document
            conversion_date: Date of conversion (defaults to today)

        Returns:
            YAML frontmatter string with delimiters
        """
        if conversion_date is None:
            conversion_date = datetime.now().strftime('%Y-%m-%d')

        # Build frontmatter dict
        frontmatter = {}

        # Add metadata fields
        if 'title' in metadata:
            frontmatter['title'] = metadata['title']
        if 'author' in metadata:
            frontmatter['author'] = metadata['author']
        if 'date' in metadata:
            frontmatter['date'] = metadata['date']
        if 'subject' in metadata:
            frontmatter['subject'] = metadata['subject']
        if 'keywords' in metadata:
            frontmatter['keywords'] = metadata['keywords']
        if 'publisher' in metadata:
            frontmatter['publisher'] = metadata['publisher']
        if 'language' in metadata:
            frontmatter['language'] = metadata['language']

        # Add conversion metadata
        frontmatter['source_file'] = source_file.name
        frontmatter['conversion_date'] = conversion_date

        # Convert to YAML
        yaml_str = yaml.dump(
            frontmatter,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False
        )

        # Add delimiters
        return f"---\n{yaml_str}---\n\n"

    @staticmethod
    def prepend_to_markdown(frontmatter: str, markdown_content: str) -> str:
        """Prepend frontmatter to markdown content.

        Args:
            frontmatter: YAML frontmatter string (with delimiters)
            markdown_content: Markdown content

        Returns:
            Combined string with frontmatter and content
        """
        # Remove existing frontmatter if present
        if markdown_content.startswith('---\n'):
            # Find the end of existing frontmatter
            end_index = markdown_content.find('\n---\n', 4)
            if end_index != -1:
                # Remove existing frontmatter
                markdown_content = markdown_content[end_index + 5:]

        return frontmatter + markdown_content
