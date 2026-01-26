"""
Tests for Extraction Pipeline.

Laravel Equivalent: tests/Integration/ExtractionPipelineTest.php

These tests validate the complete extraction pipeline:
PDF → Parser → LLM → Validator → Output
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.extraction_pipeline import ExtractionPipeline


@pytest.mark.integration
class TestExtractionPipeline:
    """Test complete extraction pipeline."""

    @patch("src.extraction_pipeline.LlmExtractorService")
    @patch("src.extraction_pipeline.PdfParserService")
    def test_process_pdf_success(
        self, mock_pdf_parser_class, mock_llm_extractor_class, tmp_path
    ):
        """Test successful PDF processing."""
        # Mock PDF parser
        mock_parser = MagicMock()
        mock_parser.extract_text.return_value = "Test PDF text content"
        mock_parser.extract_metadata.return_value = {"page_count": 10}
        mock_pdf_parser_class.return_value = mock_parser

        # Mock LLM extractor
        mock_extractor = MagicMock()
        from core.schema import UniversalCarrierFormat, Endpoint, HttpMethod

        mock_schema = UniversalCarrierFormat(
            name="Test Carrier",
            base_url="https://api.test.com",
            endpoints=[
                Endpoint(
                    path="/api/v1/track", method=HttpMethod.GET, summary="Track shipment"
                )
            ],
        )
        mock_extractor.extract_schema.return_value = mock_schema
        mock_extractor.extract_field_mappings.return_value = []
        mock_extractor.extract_constraints.return_value = []
        mock_llm_extractor_class.return_value = mock_extractor

        # Create pipeline
        pipeline = ExtractionPipeline(llm_api_key="test-key")

        # Process PDF
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4\n")

        output_path = tmp_path / "output.json"
        schema = pipeline.process(str(pdf_path), str(output_path))

        # Verify results
        assert schema.name == "Test Carrier"
        assert output_path.exists()

        # Verify output file content
        output_data = json.loads(output_path.read_text())
        assert "schema" in output_data
        assert output_data["schema"]["name"] == "Test Carrier"

    @patch("src.extraction_pipeline.LlmExtractorService")
    @patch("src.extraction_pipeline.PdfParserService")
    def test_process_without_output_path(
        self, mock_pdf_parser_class, mock_llm_extractor_class, tmp_path
    ):
        """Test processing without output path."""
        # Mock services
        mock_parser = MagicMock()
        mock_parser.extract_text.return_value = "Test text"
        mock_parser.extract_metadata.return_value = {"page_count": 5}
        mock_pdf_parser_class.return_value = mock_parser

        mock_extractor = MagicMock()
        from core.schema import UniversalCarrierFormat, Endpoint, HttpMethod

        mock_schema = UniversalCarrierFormat(
            name="Test",
            base_url="https://api.test.com",
            endpoints=[
                Endpoint(path="/api/track", method=HttpMethod.GET, summary="Track")
            ],
        )
        mock_extractor.extract_schema.return_value = mock_schema
        mock_extractor.extract_field_mappings.return_value = []
        mock_extractor.extract_constraints.return_value = []
        mock_llm_extractor_class.return_value = mock_extractor

        pipeline = ExtractionPipeline(llm_api_key="test-key")
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4\n")

        schema = pipeline.process(str(pdf_path))

        assert schema.name == "Test"
        # Should not save file if output_path not provided
