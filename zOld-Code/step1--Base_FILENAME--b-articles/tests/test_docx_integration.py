"""Integration tests for Word document support."""

from pathlib import Path
from unittest.mock import Mock, patch
import sys

import pytest

# Add src to path for legacy system imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from file_renamer.parsers.docx_parser import DocxParser
from file_renamer.models import DocumentType
from extractors.docx_extractor import DocxExtractor
from renamer import CaselawRenamer


class TestDocxIntegration:
    """Integration tests for Word document processing."""

    def test_docx_parser_in_pipeline(self):
        """Test that DocxParser integrates correctly with pipeline."""
        from file_renamer.pipeline import build_pipeline
        from file_renamer.templates import FilenameTemplate

        pipeline = build_pipeline(FilenameTemplate.CS_COURT_YEAR_SHORTCASE_REPORTER)

        # Verify DocxParser is registered
        parser = pipeline.registry.get_parser(Path("test.docx"))
        assert parser is not None
        assert isinstance(parser, DocxParser)
        assert parser.document_type == DocumentType.DOCX

    def test_renamer_processes_docx_files(self):
        """Test that CaselawRenamer can process DOCX files."""
        renamer = CaselawRenamer()

        # Verify docx_extractor is initialized
        assert renamer.docx_extractor is not None
        assert isinstance(renamer.docx_extractor, DocxExtractor)

    @patch.object(DocxExtractor, 'extract_text')
    def test_renamer_process_file_docx(self, mock_extract_text):
        """Test complete file processing workflow for DOCX."""
        mock_extract_text.return_value = "Smith v. Jones\n123 F.3d 456\nUnited States District Court\nDecided: January 15, 2024"

        renamer = CaselawRenamer()

        # Create a mock file path
        test_path = Path("test.docx")

        with patch.object(Path, 'exists', return_value=True):
            result = renamer.process_file(test_path)

        # Verify result structure
        assert result is not None
        assert 'original_filename' in result
        assert 'document_text' in result
        assert 'new_filename' in result
        assert result['original_filename'] == 'test.docx'

    def test_renamer_rejects_unsupported_files(self):
        """Test that unsupported file types are rejected."""
        renamer = CaselawRenamer()

        test_path = Path("test.rtf")

        with patch.object(Path, 'exists', return_value=True):
            result = renamer.process_file(test_path)

        # Should return error for unsupported type
        assert 'error' in result
        assert 'Unsupported file type' in result['error']

    @patch.object(DocxExtractor, 'extract_text')
    def test_confidence_calculation_for_docx(self, mock_extract_text):
        """Test confidence score calculation for DOCX extraction."""
        # Mock a document with all required fields
        mock_extract_text.return_value = (
            "Abbott Labs v. Sandoz\n"
            "United States District Court for the Northern District of Illinois\n"
            "723 F. Supp. 2d 922\n"
            "Decided: January 15, 2010"
        )

        renamer = CaselawRenamer()

        with patch.object(Path, 'exists', return_value=True):
            result = renamer.process_file(Path("test.docx"))

        # If extraction succeeds from document, should have high confidence
        assert 'confidence' in result

    @patch('extractors.docx_extractor.DOCX_AVAILABLE', True)
    @patch('extractors.docx_extractor.Document')
    def test_multizone_extraction_integration(self, mock_document_class):
        """Test multizone extraction in metadata workflow."""
        # Create a long document with substantial content
        mock_paras = []
        for i in range(100):
            para = Mock()
            para.text = f"This is paragraph number {i+1} with substantial content for testing"
            mock_paras.append(para)

        mock_doc = Mock()
        mock_doc.paragraphs = mock_paras
        mock_doc.tables = []

        mock_document_class.return_value = mock_doc

        extractor = DocxExtractor()

        with patch.object(Path, 'exists', return_value=True):
            text = extractor.extract_text_multizone(Path("test.docx"))

        # Verify both zones are extracted
        assert text is not None
        assert "paragraph number 1" in text.lower()
        assert "[LAST_SECTION]" in text

    def test_process_directory_finds_docx_files(self):
        """Test that process_directory finds both PDF and DOCX files."""
        renamer = CaselawRenamer()

        mock_files = [
            Path("file1.pdf"),
            Path("file2.docx"),
            Path("file3.pdf"),
            Path("file4.docx"),
        ]

        def mock_glob(pattern):
            if '*.pdf' in str(pattern):
                return [f for f in mock_files if f.suffix == '.pdf']
            elif '*.docx' in str(pattern):
                return [f for f in mock_files if f.suffix == '.docx']
            return []

        with patch.object(Path, 'glob', side_effect=mock_glob):
            with patch.object(renamer, 'process_file', return_value={'test': 'result'}):
                results = renamer.process_directory(Path("test_dir"))

        # Should process all 4 files
        assert len(results) == 4

    @patch.object(DocxExtractor, 'extract_text')
    @patch.object(DocxExtractor, 'extract_text_multizone')
    def test_extract_metadata_uses_docx_extractor(self, mock_multizone, mock_extract):
        """Test that extract_metadata uses DocxExtractor for DOCX files."""
        mock_extract.return_value = "Test content"
        mock_multizone.return_value = "Multizone content"

        renamer = CaselawRenamer()

        # Create a result dict with docx file
        result = {
            'file_path': 'test.docx',
            'document_text': 'Basic text',
            'court': 'test_court',
            'year': '2024',
            'case_name': 'Test Case',
            'reporter': 'Unpub'
        }

        with patch.object(Path, 'exists', return_value=True):
            metadata = renamer.extract_metadata(result)

        # Verify multizone extraction was called for DOCX
        mock_multizone.assert_called_once_with('test.docx')

    def test_docx_and_pdf_coexist(self):
        """Test that DOCX support doesn't break PDF processing."""
        renamer = CaselawRenamer()

        # Verify both extractors exist
        assert renamer.pdf_extractor is not None
        assert renamer.docx_extractor is not None

        # Both should be initialized
        from extractors.pdf_extractor import PDFExtractor
        from extractors.docx_extractor import DocxExtractor

        assert isinstance(renamer.pdf_extractor, PDFExtractor)
        assert isinstance(renamer.docx_extractor, DocxExtractor)
