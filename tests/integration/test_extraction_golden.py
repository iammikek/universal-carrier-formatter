"""
Golden tests for LLM extraction: fixed input + fixed LLM responses → assert output invariants.

Given a fixed extracted-text fixture and mocked LLM responses, the pipeline output
must match expected schema shape and include extraction_metadata (llm_config, prompt_versions)
for reproducibility.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.extraction_pipeline import ExtractionPipeline

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"
GOLDEN_EXTRACTED_TEXT = FIXTURES_DIR / "golden_extracted_text.txt"
GOLDEN_EXPECTED_JSON = FIXTURES_DIR / "golden_expected_schema.json"


def _mock_llm_extractor():
    """Return a mock LLM extractor with fixed responses and get_config()."""
    from src.core.schema import Endpoint, HttpMethod, UniversalCarrierFormat

    mock = MagicMock()
    mock.extract_schema.return_value = UniversalCarrierFormat(
        name="Test Carrier",
        base_url="https://api.test.com",
        endpoints=[
            Endpoint(
                path="/api/v1/track", method=HttpMethod.GET, summary="Track shipment"
            ),
            Endpoint(
                path="/api/v1/shipments",
                method=HttpMethod.POST,
                summary="Create shipment",
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
    mock.extract_edge_cases.return_value = [
        {
            "type": "rate_limit",
            "route": None,
            "requirement": "100 requests per minute",
            "documentation": None,
        }
    ]
    mock.get_config.return_value = {
        "model": "gpt-4.1-mini",
        "temperature": 0.0,
        "response_format": {"type": "json_object"},
    }
    return mock


@pytest.mark.integration
class TestExtractionGolden:
    """Golden tests: fixed text fixture → assert output shape and extraction_metadata."""

    @patch("src.extraction_pipeline.LlmExtractorService")
    def test_golden_extraction_invariants(self, mock_llm_class, tmp_path):
        """
        Given fixed extracted text and mocked LLM, output has extraction_metadata and key invariants.
        """
        mock_llm_class.return_value = _mock_llm_extractor()
        pipeline = ExtractionPipeline(llm_api_key="test-key")

        output_path = tmp_path / "golden_output.json"
        pipeline.process(
            "/tmp/dummy.pdf",
            output_path=str(output_path),
            extracted_text_path=str(GOLDEN_EXTRACTED_TEXT),
        )

        assert output_path.exists()
        data = json.loads(output_path.read_text())

        # Contract fields
        assert data.get("schema_version") == "1.0.0"
        assert "generator_version" in data

        # Reproducibility: LLM config and prompt versions in output
        assert (
            "extraction_metadata" in data
        ), "extraction_metadata required for reproducibility"
        meta = data["extraction_metadata"]
        assert "llm_config" in meta
        assert meta["llm_config"].get("model") == "gpt-4.1-mini"
        assert meta["llm_config"].get("temperature") == 0.0
        assert "prompt_versions" in meta
        assert meta["prompt_versions"].get("schema") == "1.0"
        assert meta["prompt_versions"].get("field_mappings") == "1.0"
        assert meta["prompt_versions"].get("constraints") == "1.0"
        assert meta["prompt_versions"].get("edge_cases") == "1.0"

        # Schema invariants (base_url may have trailing slash from Pydantic HttpUrl)
        schema = data["schema"]
        assert schema["name"] == "Test Carrier"
        assert schema["base_url"].rstrip("/") == "https://api.test.com"
        assert len(schema["endpoints"]) == 2
        paths = {e["path"] for e in schema["endpoints"]}
        assert "/api/v1/track" in paths
        assert "/api/v1/shipments" in paths

        assert len(data["field_mappings"]) == 1
        assert data["field_mappings"][0]["universal_field"] == "tracking_number"
        assert len(data["edge_cases"]) == 1
        assert data["edge_cases"][0]["type"] == "rate_limit"

    @patch("src.extraction_pipeline.LlmExtractorService")
    def test_golden_extraction_matches_expected_json(self, mock_llm_class, tmp_path):
        """
        Given fixed text and mocked LLM, output matches golden expected JSON (key fields).
        """
        if not GOLDEN_EXPECTED_JSON.exists():
            pytest.skip("Golden expected file not found; run once to generate")

        mock_llm_class.return_value = _mock_llm_extractor()
        pipeline = ExtractionPipeline(llm_api_key="test-key")
        output_path = tmp_path / "golden_output.json"
        pipeline.process(
            "/tmp/dummy.pdf",
            output_path=str(output_path),
            extracted_text_path=str(GOLDEN_EXTRACTED_TEXT),
        )

        with open(GOLDEN_EXPECTED_JSON, encoding="utf-8") as f:
            expected = json.load(f)

        data = json.loads(output_path.read_text())

        # Compare key invariants (ignore generator_version / dynamic fields; base_url may have trailing slash)
        assert data["schema_version"] == expected["schema_version"]
        assert data["schema"]["name"] == expected["schema"]["name"]
        assert data["schema"]["base_url"].rstrip("/") == expected["schema"][
            "base_url"
        ].rstrip("/")
        assert len(data["schema"]["endpoints"]) == len(expected["schema"]["endpoints"])
        assert (
            data["extraction_metadata"]["llm_config"]["model"]
            == expected["extraction_metadata"]["llm_config"]["model"]
        )
        assert (
            data["extraction_metadata"]["prompt_versions"]
            == expected["extraction_metadata"]["prompt_versions"]
        )


def _key_fields_for_regression(data: dict) -> dict:
    """
    Extract key fields for golden snapshot regression (imp-14).
    Normalizes so we can diff pipeline output against committed baseline.
    """
    schema = data.get("schema") or {}
    base_url = (schema.get("base_url") or "").rstrip("/")
    endpoints = schema.get("endpoints") or []
    endpoint_paths = sorted(e.get("path", "") for e in endpoints)
    meta = data.get("extraction_metadata") or {}
    prompt_versions = meta.get("prompt_versions") or {}
    return {
        "schema_version": data.get("schema_version"),
        "schema_name": schema.get("name"),
        "schema_base_url": base_url,
        "endpoint_paths": endpoint_paths,
        "num_field_mappings": len(data.get("field_mappings") or []),
        "num_constraints": len(data.get("constraints") or []),
        "num_edge_cases": len(data.get("edge_cases") or []),
        "prompt_versions": prompt_versions,
    }


@pytest.mark.integration
class TestGoldenSnapshotRegression:
    """Golden snapshot regression: diff key fields against committed baseline (imp-14)."""

    @patch("src.extraction_pipeline.LlmExtractorService")
    def test_golden_snapshot_key_fields_match_baseline(self, mock_llm_class, tmp_path):
        """
        Run pipeline with fixed mock; diff key fields of output against
        golden_expected_schema.json. Fails with clear diff if schema or
        normalization regresses.
        """
        if not GOLDEN_EXPECTED_JSON.exists():
            pytest.skip("Golden baseline not found")

        mock_llm_class.return_value = _mock_llm_extractor()
        pipeline = ExtractionPipeline(llm_api_key="test-key")
        output_path = tmp_path / "snapshot_output.json"
        pipeline.process(
            "/tmp/dummy.pdf",
            output_path=str(output_path),
            extracted_text_path=str(GOLDEN_EXTRACTED_TEXT),
        )

        with open(GOLDEN_EXPECTED_JSON, encoding="utf-8") as f:
            baseline = json.load(f)

        actual_data = json.loads(output_path.read_text())
        expected_key_fields = _key_fields_for_regression(baseline)
        actual_key_fields = _key_fields_for_regression(actual_data)

        diff_parts = []
        for key in expected_key_fields:
            exp = expected_key_fields[key]
            act = actual_key_fields.get(key)
            if exp != act:
                diff_parts.append(f"  {key}: expected {exp!r}, got {act!r}")
        if diff_parts:
            raise AssertionError(
                "Golden snapshot key fields differ from baseline:\n"
                + "\n".join(diff_parts)
            )
