"""Tests for DocxExtractor."""

import re
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from extractors.docx_extractor import DocxExtractor


class TestDocxExtractor:
    """Test suite for DocxExtractor."""

    def test_initialization(self):
        """Test extractor initialization."""
        extractor = DocxExtractor()
        assert extractor.max_paragraphs is None

        extractor_limited = DocxExtractor(max_paragraphs=10)
        assert extractor_limited.max_paragraphs == 10

    def test_check_docx_available_when_present(self):
        """Test availability check when python-docx is present."""
        with patch('extractors.docx_extractor.DOCX_AVAILABLE', True):
            available, error = DocxExtractor.check_docx_available()
            assert available is True
            assert error is None

    def test_check_docx_available_when_missing(self):
        """Test availability check when python-docx is missing."""
        with patch('extractors.docx_extractor.DOCX_AVAILABLE', False):
            available, error = DocxExtractor.check_docx_available()
            assert available is False
            assert "python-docx not found" in error

    def test_extract_text_file_not_found(self):
        """Test extraction returns None for non-existent file."""
        extractor = DocxExtractor()
        text = extractor.extract_text(Path("/nonexistent/file.docx"))
        assert text is None

    @patch('extractors.docx_extractor.Document')
    def test_extract_text_success(self, mock_document_class):
        """Test successful text extraction."""
        extractor = DocxExtractor()

        # Mock document
        mock_para1 = Mock()
        mock_para1.text = "Plaintiff v. Defendant"
        mock_para2 = Mock()
        mock_para2.text = "Supreme Court Decision"

        mock_doc = Mock()
        mock_doc.paragraphs = [mock_para1, mock_para2]
        mock_doc.tables = []

        mock_document_class.return_value = mock_doc

        # Create a temporary file path
        with patch.object(Path, 'exists', return_value=True):
            text = extractor.extract_text(Path("test.docx"))

        assert text == "Plaintiff v. Defendant\nSupreme Court Decision"

    @patch('extractors.docx_extractor.Document')
    def test_extract_text_respects_max_paragraphs(self, mock_document_class):
        """Test that max_paragraphs limit is respected."""
        extractor = DocxExtractor(max_paragraphs=2)

        # Mock document with 3 paragraphs
        mock_paras = [Mock() for _ in range(3)]
        for i, para in enumerate(mock_paras):
            para.text = f"Paragraph {i+1}"

        mock_doc = Mock()
        mock_doc.paragraphs = mock_paras
        mock_doc.tables = []

        mock_document_class.return_value = mock_doc

        with patch.object(Path, 'exists', return_value=True):
            text = extractor.extract_text(Path("test.docx"))

        # Should only extract first 2 paragraphs
        assert "Paragraph 1" in text
        assert "Paragraph 2" in text
        assert "Paragraph 3" not in text

    @patch('extractors.docx_extractor.Document')
    def test_extract_text_from_tables(self, mock_document_class):
        """Test text extraction includes table content."""
        extractor = DocxExtractor()

        mock_para = Mock()
        mock_para.text = "Before table"

        mock_cell = Mock()
        mock_cell.text = "Table cell"
        mock_row = Mock()
        mock_row.cells = [mock_cell]
        mock_table = Mock()
        mock_table.rows = [mock_row]

        mock_doc = Mock()
        mock_doc.paragraphs = [mock_para]
        mock_doc.tables = [mock_table]

        mock_document_class.return_value = mock_doc

        with patch.object(Path, 'exists', return_value=True):
            text = extractor.extract_text(Path("test.docx"))

        assert "Before table" in text
        assert "Table cell" in text

    def test_get_main_content_filters_short_lines(self):
        """Test that short lines without keywords are filtered."""
        extractor = DocxExtractor()

        text = "Header\nThis is a substantial line with enough content\nFooter"
        filtered = extractor.get_main_content(text)

        assert "substantial line" in filtered
        assert "Header" not in filtered  # Too short
        assert "Footer" not in filtered  # Too short

    def test_get_main_content_keeps_keyword_lines(self):
        """Test that lines with keywords are kept even if short."""
        extractor = DocxExtractor()

        text = "Short\nDecided: 2024\nv. Defendant\nSupreme Court"
        filtered = extractor.get_main_content(text)

        # These should be kept due to keywords
        assert "Decided" in filtered
        assert "v. Defendant" in filtered
        assert "Supreme Court" in filtered

    def test_get_main_content_empty_text(self):
        """Test handling of empty text."""
        extractor = DocxExtractor()
        assert extractor.get_main_content(None) == ""
        assert extractor.get_main_content("") == ""

    def test_extract_text_multizone_file_not_found(self):
        """Test multizone extraction returns None for non-existent file."""
        extractor = DocxExtractor()
        text = extractor.extract_text_multizone(Path("/nonexistent/file.docx"))
        assert text is None

    @patch('extractors.docx_extractor.DOCX_AVAILABLE', True)
    @patch('extractors.docx_extractor.Document')
    def test_extract_text_multizone(self, mock_document_class):
        """Test multizone extraction."""
        extractor = DocxExtractor()

        # Create many paragraphs with substantial content
        mock_paras = [Mock() for _ in range(100)]
        for i, para in enumerate(mock_paras):
            para.text = f"This is paragraph number {i+1} with substantial content"

        mock_doc = Mock()
        mock_doc.paragraphs = mock_paras
        mock_doc.tables = []

        mock_document_class.return_value = mock_doc

        # Mock Path.exists to return True
        with patch.object(Path, 'exists', return_value=True):
            text = extractor.extract_text_multizone(Path("test.docx"))

        # Verify text was extracted
        assert text is not None
        assert "paragraph number 1" in text.lower()
        # Last paragraph should be in last section
        assert "paragraph number 100" in text.lower()

    @patch('extractors.docx_extractor.DOCX_AVAILABLE', True)
    @patch('extractors.docx_extractor.Document')
    def test_extract_text_multizone_short_document(self, mock_document_class):
        """Test multizone extraction on short document."""
        extractor = DocxExtractor()

        # Create document shorter than first_paragraphs setting
        mock_paras = [Mock() for _ in range(10)]
        for i, para in enumerate(mock_paras):
            para.text = f"This is paragraph number {i+1} with substantial content"

        mock_doc = Mock()
        mock_doc.paragraphs = mock_paras
        mock_doc.tables = []

        mock_document_class.return_value = mock_doc

        with patch.object(Path, 'exists', return_value=True):
            text = extractor.extract_text_multizone(Path("test.docx"))

        # Should not have LAST_SECTION marker for short docs
        assert text is not None
        assert "paragraph number 1" in text.lower()
        assert "paragraph number 10" in text.lower()

    def test_find_case_caption_finds_v_pattern(self):
        """Test case caption extraction with 'v.' pattern."""
        extractor = DocxExtractor()

        text = "Line 1\nLine 2\nSmith v. Jones\nSome other content"
        caption = extractor.find_case_caption(text)

        assert caption is not None
        assert "Smith" in caption
        assert "Jones" in caption
        assert "v." in caption

    def test_find_case_caption_handles_multiline(self):
        """Test case caption extraction with context lines."""
        extractor = DocxExtractor()

        # Test with case name on single line in context
        text = "SUPREME COURT\n\nSmith v. Jones\n\nNo. 12-345\nDecided January 15, 2024"
        caption = extractor.find_case_caption(text)

        # This should work since v. and parties are on same line
        assert caption is not None
        assert "Smith" in caption
        assert "Jones" in caption

    def test_find_case_caption_returns_none_if_not_found(self):
        """Test that None is returned when no caption found."""
        extractor = DocxExtractor()

        text = "Some document\nWithout case names\nNo versus pattern"
        caption = extractor.find_case_caption(text)

        assert caption is None

    def test_find_case_caption_empty_text(self):
        """Test caption extraction with empty text."""
        extractor = DocxExtractor()

        assert extractor.find_case_caption(None) is None
        assert extractor.find_case_caption("") is None

    @patch('extractors.docx_extractor.Document')
    def test_extract_text_handles_exception(self, mock_document_class):
        """Test that extraction errors return None."""
        extractor = DocxExtractor()

        mock_document_class.side_effect = Exception("Corrupted document")

        with patch.object(Path, 'exists', return_value=True):
            text = extractor.extract_text(Path("test.docx"))

        assert text is None
