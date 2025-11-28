"""Tests for DocxParser."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from file_renamer.models import DocumentMetadata, DocumentType
from file_renamer.parsers.docx_parser import DocxParser


class TestDocxParser:
    """Test suite for DocxParser."""

    def test_document_type(self):
        """Test that parser has correct document type."""
        parser = DocxParser()
        assert parser.document_type == DocumentType.DOCX

    def test_supports_docx_file(self):
        """Test that parser supports .docx files."""
        parser = DocxParser()
        assert parser.supports(Path("test.docx"))
        assert parser.supports(Path("test.DOCX"))
        assert parser.supports(Path("/path/to/file.docx"))

    def test_does_not_support_other_files(self):
        """Test that parser rejects non-docx files."""
        parser = DocxParser()
        assert not parser.supports(Path("test.pdf"))
        assert not parser.supports(Path("test.txt"))
        assert not parser.supports(Path("test.doc"))
        assert not parser.supports(Path("test.rtf"))

    def test_parse_returns_metadata(self):
        """Test that parse returns DocumentMetadata."""
        parser = DocxParser()
        test_path = Path("test.docx")

        with patch.object(parser, '_extract_text', return_value="Test content"):
            metadata = parser.parse(test_path)

        assert isinstance(metadata, DocumentMetadata)
        assert metadata.source_path == test_path
        assert metadata.document_type == DocumentType.DOCX

    def test_parse_without_docx_library(self):
        """Test graceful handling when python-docx is not available."""
        parser = DocxParser()
        test_path = Path("test.docx")

        with patch('file_renamer.parsers.docx_parser.DOCX_AVAILABLE', False):
            metadata = parser.parse(test_path)

        assert isinstance(metadata, DocumentMetadata)
        assert metadata.source_path == test_path
        assert metadata.document_type == DocumentType.DOCX

    @patch('file_renamer.parsers.docx_parser.Document')
    def test_extract_text_from_paragraphs(self, mock_document_class):
        """Test text extraction from document paragraphs."""
        parser = DocxParser()

        # Mock document with paragraphs
        mock_para1 = Mock()
        mock_para1.text = "First paragraph"
        mock_para2 = Mock()
        mock_para2.text = "Second paragraph"

        mock_doc = Mock()
        mock_doc.paragraphs = [mock_para1, mock_para2]
        mock_doc.tables = []

        mock_document_class.return_value = mock_doc

        text = parser._extract_text(Path("test.docx"))

        assert text == "First paragraph\nSecond paragraph"
        mock_document_class.assert_called_once()

    @patch('file_renamer.parsers.docx_parser.Document')
    def test_extract_text_from_tables(self, mock_document_class):
        """Test text extraction from document tables."""
        parser = DocxParser()

        # Mock document with table
        mock_cell = Mock()
        mock_cell.text = "Cell content"

        mock_row = Mock()
        mock_row.cells = [mock_cell]

        mock_table = Mock()
        mock_table.rows = [mock_row]

        mock_doc = Mock()
        mock_doc.paragraphs = []
        mock_doc.tables = [mock_table]

        mock_document_class.return_value = mock_doc

        text = parser._extract_text(Path("test.docx"))

        assert text == "Cell content"

    @patch('file_renamer.parsers.docx_parser.Document')
    def test_extract_text_skips_empty_paragraphs(self, mock_document_class):
        """Test that empty paragraphs are skipped."""
        parser = DocxParser()

        mock_para1 = Mock()
        mock_para1.text = "Content"
        mock_para2 = Mock()
        mock_para2.text = "   "  # Whitespace only
        mock_para3 = Mock()
        mock_para3.text = ""

        mock_doc = Mock()
        mock_doc.paragraphs = [mock_para1, mock_para2, mock_para3]
        mock_doc.tables = []

        mock_document_class.return_value = mock_doc

        text = parser._extract_text(Path("test.docx"))

        assert text == "Content"

    @patch('file_renamer.parsers.docx_parser.Document')
    def test_extract_text_handles_exceptions(self, mock_document_class):
        """Test that extraction errors are handled gracefully."""
        parser = DocxParser()

        mock_document_class.side_effect = Exception("Corrupted file")

        text = parser._extract_text(Path("test.docx"))

        assert text is None

    def test_extract_text_without_docx_library(self):
        """Test extraction returns None when python-docx unavailable."""
        parser = DocxParser()

        with patch('file_renamer.parsers.docx_parser.DOCX_AVAILABLE', False):
            text = parser._extract_text(Path("test.docx"))

        assert text is None
