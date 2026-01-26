"""
Tests for LLM Extractor Service.

Laravel Equivalent: tests/Unit/LlmExtractorTest.php

These tests validate that the LLM extractor correctly processes PDF text
and extracts Universal Carrier Format schema.
"""

import json
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from src.llm_extractor import LlmExtractorService


@pytest.mark.unit
class TestLlmExtractorService:
    """Test LLM extractor service."""

    @patch("src.llm_extractor.ChatOpenAI")
    def test_extract_schema_success(self, mock_chat_openai_class):
        """Test successful schema extraction."""
        # Mock LLM response
        mock_llm_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.content = json.dumps(
            {
                "name": "Test Carrier",
                "base_url": "https://api.test.com",
                "version": "v1",
                "endpoints": [
                    {
                        "path": "/api/v1/track",
                        "method": "GET",
                        "summary": "Track shipment",
                    }
                ],
            }
        )
        mock_llm_instance.invoke.return_value = mock_response
        mock_chat_openai_class.return_value = mock_llm_instance

        extractor = LlmExtractorService(api_key="test-key")
        pdf_text = "GET /api/v1/track - Track a shipment"

        schema = extractor.extract_schema(pdf_text)

        assert schema.name == "Test Carrier"
        assert schema.base_url == "https://api.test.com/"
        assert len(schema.endpoints) == 1

    @patch("src.llm_extractor.ChatOpenAI")
    def test_extract_json_from_markdown_code_block(self, mock_chat_openai_class):
        """Test extracting JSON from markdown code block."""
        mock_llm_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.content = """```json
{
  "name": "Test Carrier",
  "base_url": "https://api.test.com"
}
```"""
        mock_llm_instance.invoke.return_value = mock_response
        mock_chat_openai_class.return_value = mock_llm_instance

        extractor = LlmExtractorService(api_key="test-key")
        pdf_text = "Test documentation"

        # This should extract JSON from markdown code block
        result = extractor._extract_json_from_response(mock_response.content)
        assert result["name"] == "Test Carrier"

    @patch("src.llm_extractor.ChatOpenAI")
    def test_extract_json_from_plain_json(self, mock_chat_openai_class):
        """Test extracting JSON from plain JSON response."""
        mock_llm_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.content = '{"name": "Test Carrier", "base_url": "https://api.test.com"}'
        mock_llm_instance.invoke.return_value = mock_response
        mock_chat_openai_class.return_value = mock_llm_instance

        extractor = LlmExtractorService(api_key="test-key")
        result = extractor._extract_json_from_response(mock_response.content)
        assert result["name"] == "Test Carrier"

    def test_requires_api_key(self):
        """Test that API key is required."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="OPENAI_API_KEY"):
                LlmExtractorService()

    @patch("src.llm_extractor.ChatOpenAI")
    def test_extract_field_mappings(self, mock_chat_openai_class):
        """Test extracting field mappings."""
        mock_llm_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.content = json.dumps(
            [
                {
                    "carrier_field": "trk_num",
                    "universal_field": "tracking_number",
                    "description": "Tracking number",
                }
            ]
        )
        mock_llm_instance.invoke.return_value = mock_response
        mock_chat_openai_class.return_value = mock_llm_instance

        extractor = LlmExtractorService(api_key="test-key")
        mappings = extractor.extract_field_mappings("Test docs", "Test Carrier")

        assert len(mappings) == 1
        assert mappings[0]["carrier_field"] == "trk_num"
        assert mappings[0]["universal_field"] == "tracking_number"

    @patch("src.llm_extractor.ChatOpenAI")
    def test_extract_constraints(self, mock_chat_openai_class):
        """Test extracting constraints."""
        mock_llm_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.content = json.dumps(
            [
                {
                    "field": "weight",
                    "rule": "Must be in grams for Germany",
                    "type": "unit_conversion",
                }
            ]
        )
        mock_llm_instance.invoke.return_value = mock_response
        mock_chat_openai_class.return_value = mock_llm_instance

        extractor = LlmExtractorService(api_key="test-key")
        constraints = extractor.extract_constraints("Test docs")

        assert len(constraints) == 1
        assert constraints[0]["field"] == "weight"
