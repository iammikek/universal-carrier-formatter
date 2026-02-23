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
        # Request/response schemas should be in components
        assert "components" in spec
        assert "schemas" in spec["components"]
        assert "ConvertRequest" in spec["components"]["schemas"]
        assert "ExtractJobPendingResponse" in spec["components"]["schemas"]
        assert "ExtractJobFailedResponse" in spec["components"]["schemas"]

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
        """POST /convert with missing carrier_response returns 422 and error envelope."""
        response = client.post("/convert", json={})
        _assert_error_envelope(response, "validation_error", 422)
        data = response.json()
        assert "details" in data["error"]
        assert "errors" in data["error"]["details"]

    def test_convert_carrier_response_wrong_type_string(self, client):
        """POST /convert with carrier_response as string returns 422, not 500."""
        response = client.post(
            "/convert",
            json={"carrier_response": "not a dict"},
        )
        _assert_error_envelope(response, "validation_error", 422)

    def test_convert_carrier_response_wrong_type_list(self, client):
        """POST /convert with carrier_response as list returns 422, not 500."""
        response = client.post(
            "/convert",
            json={"carrier_response": ["a", "b"]},
        )
        _assert_error_envelope(response, "validation_error", 422)

    def test_convert_carrier_response_null(self, client):
        """POST /convert with carrier_response null returns 422."""
        response = client.post(
            "/convert",
            json={"carrier_response": None},
        )
        _assert_error_envelope(response, "validation_error", 422)

    def test_convert_unknown_carrier_returns_404(self, client):
        """POST /convert with unknown carrier slug returns 404 and error envelope."""
        response = client.post(
            "/convert",
            json={
                "carrier_response": {"trk_num": "123"},
                "carrier": "nonexistent_carrier_slug",
            },
        )
        _assert_error_envelope(response, "not_found", 404)

    def test_convert_bad_nested_structure_no_500(self, client):
        """POST /convert with valid dict but weird nested types returns 4xx with envelope, not 500."""
        # Example mapper may still succeed with extra keys; use a payload that can trigger mapper errors
        # (e.g. loc as string when mapper expects dict). Example mapper treats loc as dict for current_location.
        response = client.post(
            "/convert",
            json={
                "carrier_response": {
                    "trk_num": "123",
                    "stat": "IN_TRANSIT",
                    "loc": "string_instead_of_object",  # unexpected type for nested field
                    "est_del": "2026-01-30",
                },
            },
        )
        # Either 200 (mapper tolerates) or 400 (mapper fails); must not 500
        assert response.status_code in (200, 400)
        if response.status_code == 400:
            _assert_error_envelope(response, "bad_request", 400)
        else:
            data = response.json()
            assert "tracking_number" in data

    def test_extract_job_not_found_returns_404(self, client):
        """GET /extract/jobs/{job_id} with unknown job_id returns 404 and error envelope."""
        response = client.get("/extract/jobs/nonexistent-job-id")
        _assert_error_envelope(response, "not_found", 404)

    def test_extract_validation_no_input(self, client):
        """POST /extract with neither file nor body returns 400."""
        response = client.post("/extract")
        assert response.status_code == 400

    def test_extract_with_text_mocked(self, client):
        """POST /extract with extracted_text returns schema when pipeline is mocked (imp-13)."""
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
            "extraction_metadata": {"llm_config": {"model": "gpt-4.1-mini"}},
        }

        def write_minimal_output(pdf_path, output_path=None, **kwargs):
            if output_path:
                with open(output_path, "w") as f:
                    json.dump(minimal_output, f)

        with patch("src.controller.extract.ExtractionPipeline") as mock_pipeline_class:
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
            assert data.get("extraction_metadata") is not None
            assert data["extraction_metadata"].get("llm_config", {}).get("model")

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

    def test_openapi_extract_documents_202_response(self, client):
        """OpenAPI spec for POST /extract should document the 202 async response."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        spec = response.json()
        extract_post = spec["paths"]["/extract"]["post"]
        responses = extract_post.get("responses", {})
        assert "202" in responses, "POST /extract must document 202 Accepted for async mode"
        resp_202 = responses["202"]
        assert "description" in resp_202
        assert "job" in resp_202["description"].lower() or "accept" in resp_202["description"].lower()

    def test_async_extract_job_store_limit(self, client):
        """POST /extract?async=1 returns 503 when _extract_jobs is at max capacity."""
        from src.controller import _extract_jobs

        original = dict(_extract_jobs)
        try:
            with patch("src.controller.MAX_EXTRACT_JOBS", 2):
                _extract_jobs["job-1"] = {"status": "pending", "result": None, "error": None}
                _extract_jobs["job-2"] = {"status": "pending", "result": None, "error": None}
                response = client.post(
                    "/extract?async=1",
                    json={"extracted_text": "some text"},
                )
            assert response.status_code == 503
            data = response.json()
            assert "error" in data
            assert "Too many pending jobs" in data["error"]["message"]
        finally:
            _extract_jobs.clear()
            _extract_jobs.update(original)

    def test_request_id_in_response(self, client):
        """Response includes X-Request-ID header (from middleware)."""
        response = client.get("/health")
        assert response.status_code == 200
        assert "X-Request-ID" in response.headers
        assert len(response.headers["X-Request-ID"]) > 0

    def test_request_id_from_client_preserved(self, client):
        """When client sends X-Request-ID, response echoes it."""
        response = client.get(
            "/health",
            headers={"X-Request-ID": "test-id-123"},
        )
        assert response.status_code == 200
        assert response.headers.get("X-Request-ID") == "test-id-123"

    def test_payload_too_large_extract_returns_413(self, client):
        """POST /extract with Content-Length over limit returns 413 and error envelope."""
        # Middleware checks Content-Length header; body can be minimal
        response = client.post(
            "/extract",
            headers={"Content-Length": "60000000"},  # 60 MB > 50 MB limit
            content=b"x",
        )
        _assert_error_envelope(response, "payload_too_large", 413)

    def test_payload_too_large_convert_returns_413(self, client):
        """POST /convert with Content-Length over 1MB returns 413 and error envelope."""
        response = client.post(
            "/convert",
            headers={"Content-Length": "2000000"},  # 2 MB > 1 MB limit
            content=b'{"carrier_response":{}}',
        )
        _assert_error_envelope(response, "payload_too_large", 413)
