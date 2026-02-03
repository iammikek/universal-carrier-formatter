"""
Tests for Extraction Pipeline.

These tests validate the complete extraction pipeline:
PDF → Parser → LLM → Validator → Output
"""

import json
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
        from src.core.schema import Endpoint, HttpMethod, UniversalCarrierFormat

        mock_schema = UniversalCarrierFormat(
            name="Test Carrier",
            base_url="https://api.test.com",
            endpoints=[
                Endpoint(
                    path="/api/v1/track",
                    method=HttpMethod.GET,
                    summary="Track shipment",
                )
            ],
        )
        mock_extractor.extract_schema.return_value = mock_schema
        # Mock field mappings with validation metadata
        mock_extractor.extract_field_mappings.return_value = [
            {
                "carrier_field": "s_addr_1",
                "universal_field": "sender_address_line_1",
                "description": "Sender Address Line 1",
                "required": True,
                "max_length": 50,
                "type": "string",
            }
        ]
        mock_extractor.extract_constraints.return_value = []
        mock_extractor.extract_edge_cases.return_value = [
            {
                "type": "customs_requirement",
                "route": "EU → UK",
                "requirement": "Customs declaration required",
                "documentation": "Section 4.2",
            }
        ]
        mock_extractor.get_config.return_value = {
            "model": "gpt-4.1-mini",
            "temperature": 0.0,
        }
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

        # Verify field_mappings structure
        assert "field_mappings" in output_data
        assert len(output_data["field_mappings"]) == 1
        mapping = output_data["field_mappings"][0]
        assert mapping["carrier_field"] == "s_addr_1"
        assert mapping["universal_field"] == "sender_address_line_1"
        assert mapping["required"] is True
        assert mapping["max_length"] == 50
        assert mapping["type"] == "string"

        # Verify edge_cases (Scenario 3)
        assert "edge_cases" in output_data
        assert len(output_data["edge_cases"]) == 1
        assert output_data["edge_cases"][0]["type"] == "customs_requirement"
        assert output_data["edge_cases"][0]["route"] == "EU → UK"

        # Verify extracted text was saved (always saved when parsing from PDF)
        extracted_text_path = tmp_path / "test_extracted_text.txt"
        assert extracted_text_path.exists()
        assert extracted_text_path.read_text() == "Test PDF text content"

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
        from src.core.schema import Endpoint, HttpMethod, UniversalCarrierFormat

        mock_schema = UniversalCarrierFormat(
            name="Test",
            base_url="https://api.test.com",
            endpoints=[
                Endpoint(path="/api/track", method=HttpMethod.GET, summary="Track")
            ],
        )
        mock_extractor.extract_schema.return_value = mock_schema
        # Mock field mappings with validation metadata
        mock_extractor.extract_field_mappings.return_value = [
            {
                "carrier_field": "trk_num",
                "universal_field": "tracking_number",
                "description": "Tracking number",
                "required": True,
                "min_length": 10,
                "max_length": 20,
                "type": "string",
                "pattern": "^[A-Z0-9]{10,20}$",
            }
        ]
        mock_extractor.extract_constraints.return_value = []
        mock_extractor.extract_edge_cases.return_value = []
        mock_extractor.get_config.return_value = {
            "model": "gpt-4.1-mini",
            "temperature": 0.0,
        }
        mock_llm_extractor_class.return_value = mock_extractor

        pipeline = ExtractionPipeline(llm_api_key="test-key")
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4\n")

        schema = pipeline.process(str(pdf_path))

        assert schema.name == "Test"
        # Should not save file if output_path not provided


@pytest.mark.integration
class TestExtractionPipelineLLMFailures:
    """
    LLM failure behaviour: pipeline fails clearly and does not leave partial output.

    Tests for timeout, malformed JSON response, and API errors.
    """

    @patch("src.extraction_pipeline.LlmExtractorService")
    @patch("src.extraction_pipeline.PdfParserService")
    def test_llm_timeout_raises_no_partial_output(
        self, mock_pdf_parser_class, mock_llm_extractor_class, tmp_path
    ):
        """When LLM times out, pipeline raises and does not write output file."""
        mock_parser = MagicMock()
        mock_parser.extract_text.return_value = "PDF text"
        mock_parser.extract_metadata.return_value = {"page_count": 1}
        mock_pdf_parser_class.return_value = mock_parser

        mock_extractor = MagicMock()
        mock_extractor.extract_schema.side_effect = TimeoutError(
            "LLM request timed out"
        )
        mock_llm_extractor_class.return_value = mock_extractor

        pipeline = ExtractionPipeline(llm_api_key="test-key")
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4\n")
        output_path = tmp_path / "output.json"

        with pytest.raises((ValueError, TimeoutError)):
            pipeline.process(str(pdf_path), output_path=str(output_path))

        assert (
            not output_path.exists()
        ), "Pipeline must not leave partial output on timeout"

    @patch("src.extraction_pipeline.LlmExtractorService")
    @patch("src.extraction_pipeline.PdfParserService")
    def test_llm_malformed_json_raises_no_partial_output(
        self, mock_pdf_parser_class, mock_llm_extractor_class, tmp_path
    ):
        """When LLM returns malformed JSON, pipeline raises and does not write output file."""
        mock_parser = MagicMock()
        mock_parser.extract_text.return_value = "PDF text"
        mock_parser.extract_metadata.return_value = {"page_count": 1}
        mock_pdf_parser_class.return_value = mock_parser

        mock_extractor = MagicMock()
        mock_extractor.extract_schema.side_effect = ValueError(
            "Failed to extract schema from PDF text: Expecting value: line 1 column 1"
        )
        mock_llm_extractor_class.return_value = mock_extractor

        pipeline = ExtractionPipeline(llm_api_key="test-key")
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4\n")
        output_path = tmp_path / "output.json"

        with pytest.raises(ValueError):
            pipeline.process(str(pdf_path), output_path=str(output_path))

        assert (
            not output_path.exists()
        ), "Pipeline must not leave partial output on malformed JSON"

    @patch("src.extraction_pipeline.LlmExtractorService")
    @patch("src.extraction_pipeline.PdfParserService")
    def test_llm_api_error_raises_no_partial_output(
        self, mock_pdf_parser_class, mock_llm_extractor_class, tmp_path
    ):
        """When LLM API errors (e.g. rate limit, 5xx), pipeline raises and does not write output."""
        mock_parser = MagicMock()
        mock_parser.extract_text.return_value = "PDF text"
        mock_parser.extract_metadata.return_value = {"page_count": 1}
        mock_pdf_parser_class.return_value = mock_parser

        mock_extractor = MagicMock()
        mock_extractor.extract_schema.side_effect = Exception(
            "OpenAI API rate limit exceeded"
        )
        mock_llm_extractor_class.return_value = mock_extractor

        pipeline = ExtractionPipeline(llm_api_key="test-key")
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4\n")
        output_path = tmp_path / "output.json"

        with pytest.raises(Exception, match="rate limit|API"):
            pipeline.process(str(pdf_path), output_path=str(output_path))

        assert (
            not output_path.exists()
        ), "Pipeline must not leave partial output on API error"
