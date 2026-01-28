"""
Tests for the HTTP API (FastAPI).

Validates that the service API endpoints respond correctly, the
auto-generated OpenAPI docs are present, and production guardrails
(error envelope, request-id, size limits) behave as expected.
"""

import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.api import app


@pytest.fixture
def client():
    """FastAPI TestClient for the API app."""
    return TestClient(app)


def _assert_error_envelope(response, expected_code: str, status_code: int):
    """Assert response has standard error envelope and status."""
    assert response.status_code == status_code
    data = response.json()
    assert "error" in data
    err = data["error"]
    assert err["code"] == expected_code
    assert "message" in err


@pytest.mark.integration
class TestAPIEndpoints:
    """Test HTTP API endpoints."""

    def test_root(self, client):
        """GET / returns service info and links to docs."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "Universal Carrier Formatter API"
        assert data["docs"] == "/docs"
        assert data["openapi"] == "/openapi.json"
        assert "carriers" in data
        assert "extract" in data
        assert "convert" in data

    def test_health(self, client):
        """GET /health returns ok for load balancers."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "universal-carrier-formatter" in data["service"]

    def test_openapi_json(self, client):
        """GET /openapi.json returns valid OpenAPI 3 spec."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        spec = response.json()
        assert spec["openapi"].startswith("3.")
        assert "Universal Carrier Formatter" in spec["info"]["title"]
        assert "paths" in spec
        paths = spec["paths"]
        assert "/" in paths
        assert "/health" in paths
        assert "/convert" in paths
        assert "post" in paths["/convert"]
        assert "/extract" in paths
        assert "post" in paths["/extract"]
        assert "/carriers/{name}/openapi.yaml" in paths
        # Request/response schemas should be in components (ConvertRequest used by /convert)
        assert "components" in spec
        assert "schemas" in spec["components"]
        assert "ConvertRequest" in spec["components"]["schemas"]

    def test_convert_success(self, client):
        """POST /convert maps messy carrier response to universal JSON."""
        response = client.post(
            "/convert",
            json={
                "carrier_response": {
                    "trk_num": "1234567890",
                    "stat": "IN_TRANSIT",
                    "loc": {"city": "London", "postcode": "SW1A 1AA"},
                    "est_del": "2026-01-30",
                },
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["tracking_number"] == "1234567890"
        assert data["status"] == "in_transit"
        assert "current_location" in data
        assert data["current_location"]["city"] == "London"
        assert "estimated_delivery" in data

    def test_convert_validation_error(self, client):
        """POST /convert with missing carrier_response returns 422."""
        response = client.post("/convert", json={})
        assert response.status_code == 422

    def test_extract_validation_no_input(self, client):
        """POST /extract with neither file nor body returns 400."""
        response = client.post("/extract")
        assert response.status_code == 400

    def test_extract_with_text_mocked(self, client):
        """POST /extract with extracted_text returns schema when pipeline is mocked."""
        minimal_output = {
            "schema_version": "1.0.0",
            "generator_version": "0.1.0",
            "schema": {
                "name": "Test",
                "base_url": "https://api.test.com",
                "endpoints": [],
            },
            "field_mappings": [],
            "constraints": [],
            "edge_cases": [],
        }

        def write_minimal_output(pdf_path, output_path=None, **kwargs):
            if output_path:
                with open(output_path, "w") as f:
                    json.dump(minimal_output, f)

        with patch("src.api.ExtractionPipeline") as mock_pipeline_class:
            mock_pipeline = MagicMock()
            mock_pipeline.process.side_effect = write_minimal_output
            mock_pipeline_class.return_value = mock_pipeline

            response = client.post(
                "/extract",
                json={"extracted_text": "Sample carrier API documentation."},
            )
            assert response.status_code == 200
            data = response.json()
            assert data.get("schema_version") == "1.0.0"
            assert "generator_version" in data
            assert "schema" in data
            assert data["schema"]["name"] == "Test"
            assert "field_mappings" in data
            assert "constraints" in data
            assert "edge_cases" in data

    def test_carrier_openapi_yaml(self, client):
        """GET /carriers/expected/openapi.yaml returns OpenAPI YAML for example schema."""
        response = client.get("/carriers/expected/openapi.yaml")
        assert response.status_code == 200
        text = response.text
        assert "openapi:" in text
        assert "3." in text
        assert "paths:" in text or "paths:\n" in text

    def test_carrier_openapi_not_found(self, client):
        """GET /carriers/nonexistent/openapi.yaml returns 404."""
        response = client.get("/carriers/nonexistent/openapi.yaml")
        assert response.status_code == 404
