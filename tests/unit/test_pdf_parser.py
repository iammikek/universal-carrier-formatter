"""
Tests for PDF Parser Service.

Laravel Equivalent: tests/Unit/PdfParserServiceTest.php

These tests validate that the PdfParserService works correctly,
similar to how Laravel tests validate service classes.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import logging
from src.pdf_parser import PdfParserService


@pytest.mark.unit
class TestPdfParserService:
    """
    Test PDF Parser Service.
    
    Laravel Equivalent: tests/Unit/PdfParserServiceTest.php
    """
    
    @pytest.fixture
    def parser(self):
        """Create parser instance for testing"""
        return PdfParserService()
    
    @pytest.fixture
    def parser_with_tables(self):
        """Create parser with table extraction enabled"""
        return PdfParserService(config={'extract_tables': True})
    
    @pytest.fixture
    def parser_without_combine(self):
        """Create parser with page separation enabled"""
        return PdfParserService(config={'combine_pages': False})
    
    @pytest.fixture
    def mock_pdf_with_text(self):
        """Reusable fixture for PDF with text content"""
        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Sample PDF text content"
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=None)
        return mock_pdf
    
    @pytest.fixture
    def mock_pdf_multiple_pages(self):
        """Reusable fixture for multi-page PDF"""
        mock_pdf = MagicMock()
        mock_page1 = MagicMock()
        mock_page1.extract_text.return_value = "Page 1 content"
        mock_page2 = MagicMock()
        mock_page2.extract_text.return_value = "Page 2 content"
        mock_pdf.pages = [mock_page1, mock_page2]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=None)
        return mock_pdf
    
    @pytest.fixture
    def mock_pdf_with_tables(self):
        """Reusable fixture for PDF with tables"""
        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Page text content"
        mock_page.extract_tables.return_value = [
            [['Header1', 'Header2'], ['Value1', 'Value2']]
        ]
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=None)
        return mock_pdf
    
    def test_initializes_with_default_config(self, parser):
        """
        Test service initialization with default config.
        
        Laravel Equivalent:
        public function test_initializes_with_default_config()
        {
            $service = new PdfParserService();
            $this->assertNotNull($service);
        }
        """
        assert parser is not None
        assert parser.extract_tables is False
        assert parser.combine_pages is True
    
    def test_initializes_with_custom_config(self):
        """
        Test service initialization with custom config.
        
        Laravel Equivalent:
        public function test_initializes_with_custom_config()
        {
            $config = ['extract_tables' => true];
            $service = new PdfParserService($config);
            $this->assertTrue($service->extractTables);
        }
        """
        config = {
            'extract_tables': True,
            'combine_pages': False
        }
        service = PdfParserService(config=config)
        assert service.extract_tables is True
        assert service.combine_pages is False
    
    def test_validate_pdf_path_raises_error_for_missing_file(self, parser):
        """
        Test validation fails for missing file.
        
        Laravel Equivalent:
        public function test_validate_raises_error_for_missing_file()
        {
            $this->expectException(FileNotFoundException::class);
            $service = new PdfParserService();
            $service->extractText('nonexistent.pdf');
        }
        """
        with pytest.raises(FileNotFoundError) as exc_info:
            parser._validate_pdf_path('nonexistent.pdf')
        
        assert 'not found' in str(exc_info.value).lower()
    
    def test_validate_pdf_path_raises_error_for_directory(self, parser, tmp_path):
        """
        Test validation fails for directory path.
        
        Laravel Equivalent:
        public function test_validate_raises_error_for_directory()
        {
            $this->expectException(InvalidArgumentException::class);
            $service = new PdfParserService();
            $service->extractText('/tmp');
        }
        """
        # Create a temporary directory
        tmpdir = tmp_path / "test_dir"
        tmpdir.mkdir()
        
        with pytest.raises(ValueError) as exc_info:
            parser._validate_pdf_path(str(tmpdir))
        
        assert 'not a file' in str(exc_info.value).lower()
    
    def test_validate_pdf_path_raises_error_for_empty_file(self, parser, tmp_path):
        """
        Test validation fails for empty file.
        
        Laravel Equivalent:
        public function test_validate_raises_error_for_empty_file()
        {
            $this->expectException(InvalidArgumentException::class);
            $service = new PdfParserService();
            $service->extractText('empty.pdf');
        }
        """
        # Create an empty file
        empty_file = tmp_path / "empty.pdf"
        empty_file.write_bytes(b'')
        
        with pytest.raises(ValueError) as exc_info:
            parser._validate_pdf_path(str(empty_file))
        
        assert 'empty' in str(exc_info.value).lower()
    
    @patch('src.pdf_parser.pdfplumber')
    def test_extract_text_success(self, mock_pdfplumber, parser, mock_pdf_with_text, tmp_path):
        """
        Test successful text extraction.
        
        Laravel Equivalent:
        public function test_extract_text_success()
        {
            $service = new PdfParserService();
            $text = $service->extractText('test.pdf');
            $this->assertNotEmpty($text);
        }
        """
        mock_pdfplumber.open.return_value = mock_pdf_with_text
        
        # Create a temporary file path
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b'%PDF-1.4\n')  # Minimal valid PDF header
        
        text = parser.extract_text(str(pdf_file))
        
        assert text == "Sample PDF text content"
        mock_pdfplumber.open.assert_called_once_with(str(pdf_file))
    
    @patch('src.pdf_parser.pdfplumber')
    def test_extract_text_handles_multiple_pages(self, mock_pdfplumber, parser, mock_pdf_multiple_pages, tmp_path):
        """
        Test text extraction from multiple pages.
        
        Laravel Equivalent:
        public function test_extract_text_multiple_pages()
        {
            $service = new PdfParserService();
            $text = $service->extractText('multi-page.pdf');
            $this->assertStringContainsString('Page 1', $text);
            $this->assertStringContainsString('Page 2', $text);
        }
        """
        mock_pdfplumber.open.return_value = mock_pdf_multiple_pages
        
        pdf_file = tmp_path / "multi-page.pdf"
        pdf_file.write_bytes(b'%PDF-1.4\n')
        
        text = parser.extract_text(str(pdf_file))
        
        assert "Page 1 content" in text
        assert "Page 2 content" in text
    
    @patch('src.pdf_parser.pdfplumber')
    def test_extract_text_with_page_separators(self, mock_pdfplumber, parser_without_combine, mock_pdf_multiple_pages, tmp_path):
        """
        Test text extraction with page separators when combine_pages=False.
        
        Laravel Equivalent:
        public function test_extract_text_with_page_separators()
        {
            $config = ['combine_pages' => false];
            $service = new PdfParserService($config);
            $text = $service->extractText('multi-page.pdf');
            $this->assertStringContainsString('--- Page 1 ---', $text);
        }
        """
        mock_pdfplumber.open.return_value = mock_pdf_multiple_pages
        
        pdf_file = tmp_path / "multi-page.pdf"
        pdf_file.write_bytes(b'%PDF-1.4\n')
        
        text = parser_without_combine.extract_text(str(pdf_file))
        
        assert "--- Page 1 ---" in text
        assert "--- Page 2 ---" in text
        assert "Page 1 content" in text
        assert "Page 2 content" in text
    
    @patch('src.pdf_parser.pdfplumber')
    def test_extract_text_with_tables_enabled(self, mock_pdfplumber, parser_with_tables, mock_pdf_with_tables, tmp_path):
        """
        Test text extraction with table extraction enabled.
        
        Laravel Equivalent:
        public function test_extract_text_with_tables_enabled()
        {
            $config = ['extract_tables' => true];
            $service = new PdfParserService($config);
            $text = $service->extractText('with-tables.pdf');
            $this->assertStringContainsString('[Table', $text);
        }
        """
        mock_pdfplumber.open.return_value = mock_pdf_with_tables
        
        pdf_file = tmp_path / "with-tables.pdf"
        pdf_file.write_bytes(b'%PDF-1.4\n')
        
        text = parser_with_tables.extract_text(str(pdf_file))
        
        assert "Page text content" in text
        assert "[Table on page 1]" in text
        assert "Header1" in text
        assert "Header2" in text
        assert "Value1" in text
        assert "Value2" in text
    
    @patch('src.pdf_parser.pdfplumber')
    def test_extract_text_with_tables_disabled(self, mock_pdfplumber, parser, mock_pdf_with_tables, tmp_path):
        """
        Test that tables are not extracted when extract_tables=False.
        
        Laravel Equivalent:
        public function test_extract_text_without_tables()
        {
            $service = new PdfParserService();
            $text = $service->extractText('with-tables.pdf');
            $this->assertStringNotContainsString('[Table', $text);
        }
        """
        mock_pdfplumber.open.return_value = mock_pdf_with_tables
        
        pdf_file = tmp_path / "with-tables.pdf"
        pdf_file.write_bytes(b'%PDF-1.4\n')
        
        text = parser.extract_text(str(pdf_file))
        
        assert "Page text content" in text
        assert "[Table" not in text  # Tables should not be included
    
    @patch('src.pdf_parser.pdfplumber')
    def test_extract_text_logs_progress(self, mock_pdfplumber, parser, mock_pdf_with_text, tmp_path, caplog):
        """
        Test that text extraction is logged.
        
        Laravel Equivalent:
        public function test_extract_text_logs_progress()
        {
            Log::shouldReceive('info')->once();
            $service = new PdfParserService();
            $service->extractText('test.pdf');
        }
        """
        mock_pdfplumber.open.return_value = mock_pdf_with_text
        
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b'%PDF-1.4\n')
        
        with caplog.at_level(logging.INFO):
            parser.extract_text(str(pdf_file))
        
        # Verify logging occurred
        log_messages = [record.message for record in caplog.records]
        assert any("Starting PDF text extraction" in msg for msg in log_messages)
        assert any("Successfully extracted text" in msg for msg in log_messages)
    
    @patch('src.pdf_parser.pdfplumber')
    def test_extract_text_raises_error_for_empty_pdf(self, mock_pdfplumber, parser, tmp_path):
        """
        Test error handling for PDF with no text content.
        
        Laravel Equivalent:
        public function test_extract_text_raises_error_for_empty_pdf()
        {
            $this->expectException(ValueError::class);
            $service = new PdfParserService();
            $service->extractText('empty.pdf');
        }
        """
        # Mock pdfplumber with empty pages
        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = None  # No text
        
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=None)
        mock_pdfplumber.open.return_value = mock_pdf
        
        pdf_file = tmp_path / "empty.pdf"
        pdf_file.write_bytes(b'%PDF-1.4\n')
        
        with pytest.raises(ValueError) as exc_info:
            parser.extract_text(str(pdf_file))
        
        assert 'empty' in str(exc_info.value).lower() or 'images' in str(exc_info.value).lower()
    
    @patch('src.pdf_parser.pdfplumber')
    def test_extract_text_handles_corrupted_pdf(self, mock_pdfplumber, parser, tmp_path):
        """
        Test error handling for corrupted PDF.
        
        Laravel Equivalent:
        public function test_extract_text_handles_corrupted_pdf()
        {
            $this->expectException(ValueError::class);
            $service = new PdfParserService();
            $service->extractText('corrupted.pdf');
        }
        """
        # Mock pdfplumber to raise PDFSyntaxError
        from pdfplumber import PDFSyntaxError
        mock_pdfplumber.open.side_effect = PDFSyntaxError("Invalid PDF")
        
        pdf_file = tmp_path / "corrupted.pdf"
        pdf_file.write_bytes(b'invalid content')
        
        with pytest.raises(ValueError) as exc_info:
            parser.extract_text(str(pdf_file))
        
        assert 'invalid' in str(exc_info.value).lower() or 'corrupted' in str(exc_info.value).lower()
    
    @patch('src.pdf_parser.pdfplumber')
    def test_extract_text_handles_empty_pages_in_multi_page_pdf(self, mock_pdfplumber, parser, tmp_path):
        """
        Test handling of empty pages in multi-page PDF.
        
        Laravel Equivalent:
        public function test_extract_text_handles_empty_pages()
        {
            $service = new PdfParserService();
            $text = $service->extractText('mixed-pages.pdf');
            // Should handle empty pages gracefully
        }
        """
        # Mock PDF with one page with text, one empty
        mock_pdf = MagicMock()
        mock_page1 = MagicMock()
        mock_page1.extract_text.return_value = "Page 1 has content"
        mock_page2 = MagicMock()
        mock_page2.extract_text.return_value = None  # Empty page
        
        mock_pdf.pages = [mock_page1, mock_page2]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=None)
        mock_pdfplumber.open.return_value = mock_pdf
        
        pdf_file = tmp_path / "mixed-pages.pdf"
        pdf_file.write_bytes(b'%PDF-1.4\n')
        
        text = parser.extract_text(str(pdf_file))
        
        assert "Page 1 has content" in text
    
    @patch('src.pdf_parser.pdfplumber')
    def test_extract_metadata(self, mock_pdfplumber, parser, tmp_path):
        """
        Test metadata extraction.
        
        Laravel Equivalent:
        public function test_extract_metadata()
        {
            $service = new PdfParserService();
            $metadata = $service->extractMetadata('test.pdf');
            $this->assertArrayHasKey('page_count', $metadata);
        }
        """
        # Mock pdfplumber with metadata
        mock_pdf = MagicMock()
        mock_pdf.pages = [MagicMock(), MagicMock()]  # 2 pages
        mock_pdf.metadata = {
            'Title': 'Test PDF',
            'Author': 'Test Author',
            'CreationDate': '2026-01-25'
        }
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=None)
        
        mock_pdfplumber.open.return_value = mock_pdf
        
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b'%PDF-1.4\n')
        
        metadata = parser.extract_metadata(str(pdf_file))
        
        assert metadata['page_count'] == 2
        assert metadata['title'] == 'Test PDF'
        assert metadata['author'] == 'Test Author'
    
    def test_table_to_text_conversion(self, parser):
        """
        Test table to text conversion.
        
        Laravel Equivalent:
        public function test_table_to_text_conversion()
        {
            $service = new PdfParserService();
            $table = [['Header1', 'Header2'], ['Value1', 'Value2']];
            $text = $service->tableToText($table);
            $this->assertStringContainsString('Header1', $text);
        }
        """
        table = [
            ['Header1', 'Header2'],
            ['Value1', 'Value2'],
            [None, 'Value3']  # Test None handling
        ]
        
        text = parser._table_to_text(table)
        
        assert 'Header1' in text
        assert 'Header2' in text
        assert 'Value1' in text
        assert 'Value2' in text
        assert 'Value3' in text
        assert ' | ' in text  # Check separator
    
    def test_table_to_text_handles_empty_table(self, parser):
        """Test table conversion with empty table"""
        text = parser._table_to_text([])
        assert text == ""
    
    def test_table_to_text_handles_none_values(self, parser):
        """Test table conversion handles None values correctly"""
        table = [
            ['Col1', None, 'Col3'],
            [None, 'Value2', None]
        ]
        
        text = parser._table_to_text(table)
        
        # None values should be converted to empty strings
        assert 'Col1' in text
        assert 'Col3' in text
        assert 'Value2' in text
        # Should not contain 'None' as string
        assert 'None' not in text
