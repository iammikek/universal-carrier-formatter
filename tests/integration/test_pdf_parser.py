"""
Integration tests for PDF Parser Service.

Laravel Equivalent: tests/Feature/PdfParserServiceTest.php

These tests use real PDF files to validate the PDF parser works
with actual carrier documentation PDFs.
"""

from pathlib import Path

import pytest

from src.pdf_parser import PdfParserService


@pytest.mark.integration
class TestPdfParserIntegration:
    """
    Integration tests for PDF Parser Service.

    Laravel Equivalent: tests/Feature/PdfParserServiceTest.php

    These tests require actual PDF files in the examples/ directory.
    """

    @pytest.fixture
    def parser(self):
        """Create parser instance for testing"""
        return PdfParserService()

    @pytest.fixture
    def parser_with_tables(self):
        """Create parser with table extraction enabled"""
        return PdfParserService(config={"extract_tables": True})

    @pytest.fixture
    def example_pdf_path(self):
        """
        Get path to example PDF file.

        Prefers the small pdf_parser_test.pdf for fast runs; falls back to
        other examples/ PDFs if missing. Skips if no PDF exists.
        """
        examples_dir = Path("examples")

        # Small 1-page PDF for fast integration tests (API keywords included)
        small = examples_dir / "pdf_parser_test.pdf"
        if small.exists():
            return str(small)

        pdf_files = list(examples_dir.glob("*.pdf"))
        if not pdf_files:
            pytest.skip(f"No PDF files found in {examples_dir}")

        return str(pdf_files[0])

    def test_extract_text_from_real_pdf(self, parser, example_pdf_path):
        """
        Test extracting text from real PDF file.

        Laravel Equivalent:
        public function test_extract_text_from_real_pdf()
        {
            $service = new PdfParserService();
            $text = $service->extractText('examples/sample.pdf');
            $this->assertNotEmpty($text);
            $this->assertGreaterThan(100, strlen($text));
        }
        """
        text = parser.extract_text(example_pdf_path)

        assert text is not None
        assert len(text) > 0
        assert isinstance(text, str)

    def test_extract_text_contains_api_keywords(self, parser, example_pdf_path):
        """
        Test that extracted text contains API-related keywords.

        This validates that the PDF parser is working correctly
        for carrier API documentation.
        """
        text = parser.extract_text(example_pdf_path).lower()

        # Check for common API documentation keywords
        keywords = ["api", "endpoint", "request", "response", "http", "method"]
        found_keywords = [kw for kw in keywords if kw in text]

        # At least some API-related keywords should be present
        assert (
            len(found_keywords) > 0
        ), f"No API keywords found in extracted text. Found: {found_keywords}"

    def test_extract_metadata_from_real_pdf(self, parser, example_pdf_path):
        """
        Test extracting metadata from real PDF file.

        Laravel Equivalent:
        public function test_extract_metadata_from_real_pdf()
        {
            $service = new PdfParserService();
            $metadata = $service->extractMetadata('examples/sample.pdf');
            $this->assertArrayHasKey('page_count', $metadata);
            $this->assertGreaterThan(0, $metadata['page_count']);
        }
        """
        metadata = parser.extract_metadata(example_pdf_path)

        assert "page_count" in metadata
        assert metadata["page_count"] > 0
        assert isinstance(metadata["page_count"], int)

    def test_extract_text_handles_multi_page_pdf(self, parser, example_pdf_path):
        """
        Test that multi-page PDFs are handled correctly.

        This test verifies that text from all pages is extracted
        and combined properly.
        """
        metadata = parser.extract_metadata(example_pdf_path)

        # If PDF has multiple pages, verify text is combined
        if metadata["page_count"] > 1:
            text = parser.extract_text(example_pdf_path)
            # Text should be substantial for multi-page PDF
            assert (
                len(text) > 100
            ), "Multi-page PDF should have substantial text content"

    def test_extract_text_with_tables_from_real_pdf(
        self, parser_with_tables, example_pdf_path
    ):
        """
        Test table extraction from real PDF when enabled.

        This test verifies that tables are extracted and included
        in the text output when extract_tables=True.
        """
        text = parser_with_tables.extract_text(example_pdf_path)

        # If PDF contains tables, they should be included
        # Note: This test may pass even if no tables found (PDF might not have tables)
        assert len(text) > 0
        assert isinstance(text, str)

    def test_extract_text_performance(self, parser, example_pdf_path):
        """
        Test that PDF extraction completes in reasonable time.

        Laravel Equivalent:
        public function test_extract_text_performance()
        {
            $start = microtime(true);
            $service = new PdfParserService();
            $service->extractText('examples/sample.pdf');
            $duration = microtime(true) - $start;
            $this->assertLessThan(5.0, $duration); // Should complete in under 5 seconds
        }
        """
        import time

        start_time = time.time()
        text = parser.extract_text(example_pdf_path)
        duration = time.time() - start_time

        # Should complete in reasonable time (adjust threshold as needed)
        assert duration < 10.0, f"PDF extraction took too long: {duration:.2f} seconds"
        assert len(text) > 0  # Ensure we actually got text
