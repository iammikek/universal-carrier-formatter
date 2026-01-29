"""
End-to-end parser test: run formatter on a small real PDF with LLM mocked.

Demonstrates "run parser on PDF → get UCF JSON" in CI. Uses a real PDF (created
via pymupdf in fixture) and real PdfParserService; LLM is mocked so the test
does not call the API. Asserts output JSON has expected top-level keys and
valid schema shape.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.core.config import (
    KEY_CONSTRAINTS,
    KEY_EDGE_CASES,
    KEY_EXTRACTION_METADATA,
    KEY_FIELD_MAPPINGS,
    KEY_GENERATOR_VERSION,
    KEY_SCHEMA,
    KEY_SCHEMA_VERSION,
)
from src.core.schema import Endpoint, HttpMethod, UniversalCarrierFormat
from src.extraction_pipeline import ExtractionPipeline


def _make_small_pdf(path: Path) -> None:
    """Write a minimal one-page PDF with extractable text (requires pymupdf)."""
    try:
        import fitz  # pymupdf
    except ImportError:
        pytest.skip("pymupdf required for e2e PDF fixture")
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text(
        (72, 72),
        "API Documentation\n\nGET /api/v1/track - Track shipment.",
        fontsize=12,
    )
    doc.save(str(path))
    doc.close()


def _mock_llm_extractor():
    """Return a mock LLM extractor with fixed UCF-shaped responses."""
    mock = MagicMock()
    mock.extract_schema.return_value = UniversalCarrierFormat(
        name="E2E Test Carrier",
        base_url="https://api.e2e.test",
        endpoints=[
            Endpoint(
                path="/api/v1/track",
                method=HttpMethod.GET,
                summary="Track shipment",
            ),
        ],
    )
    mock.extract_field_mappings.return_value = [
        {
            "carrier_field": "trk_num",
            "universal_field": "tracking_number",
            "description": "Tracking number",
            "required": True,
            "type": "string",
        }
    ]
    mock.extract_constraints.return_value = []
    mock.extract_edge_cases.return_value = []
    mock.get_config.return_value = {
        "model": "gpt-4.1-mini",
        "temperature": 0.0,
    }
    return mock


@pytest.mark.integration
class TestParserE2E:
    """End-to-end: real PDF + mocked LLM → UCF JSON with expected shape."""

    @patch("src.extraction_pipeline.LlmExtractorService")
    def test_run_parser_on_real_pdf_produces_ucf_json(self, mock_llm_class, tmp_path):
        """
        Run extraction pipeline on a small real PDF with LLM mocked.
        Assert output JSON has expected top-level keys and valid schema shape.
        """
        # Real PDF (small, created in tmp_path)
        pdf_path = tmp_path / "sample.pdf"
        _make_small_pdf(pdf_path)
        assert pdf_path.exists()

        mock_llm_class.return_value = _mock_llm_extractor()
        pipeline = ExtractionPipeline(llm_api_key="test-key")
        output_path = tmp_path / "output_schema.json"

        schema = pipeline.process(str(pdf_path), output_path=str(output_path))

        assert schema.name == "E2E Test Carrier"
        assert output_path.exists()

        data = json.loads(output_path.read_text())

        # Expected top-level keys (contract)
        required_top_level = {
            KEY_SCHEMA_VERSION,
            KEY_GENERATOR_VERSION,
            KEY_SCHEMA,
            KEY_FIELD_MAPPINGS,
            KEY_CONSTRAINTS,
            KEY_EDGE_CASES,
        }
        for key in required_top_level:
            assert key in data, f"Missing top-level key: {key}"

        # Valid schema shape
        schema_obj = data[KEY_SCHEMA]
        assert isinstance(schema_obj, dict)
        assert schema_obj.get("name") == "E2E Test Carrier"
        assert "base_url" in schema_obj
        assert "endpoints" in schema_obj
        assert isinstance(schema_obj["endpoints"], list)
        assert len(schema_obj["endpoints"]) == 1
        assert schema_obj["endpoints"][0].get("path") == "/api/v1/track"

        assert isinstance(data[KEY_FIELD_MAPPINGS], list)
        assert len(data[KEY_FIELD_MAPPINGS]) == 1
        assert data[KEY_FIELD_MAPPINGS][0]["universal_field"] == "tracking_number"
        assert isinstance(data[KEY_CONSTRAINTS], list)
        assert isinstance(data[KEY_EDGE_CASES], list)

        # Reproducibility metadata when pipeline runs to completion
        assert KEY_EXTRACTION_METADATA in data
        meta = data[KEY_EXTRACTION_METADATA]
        assert "llm_config" in meta
        assert "prompt_versions" in meta
