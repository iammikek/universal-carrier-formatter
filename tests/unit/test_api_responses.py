"""
Unit tests for API error envelope and response helpers.
"""

import pytest

from src.api_responses import ErrorDetail, ErrorEnvelope, error_response


@pytest.mark.unit
class TestErrorDetail:
    """Test ErrorDetail model."""

    def test_required_code_and_message(self):
        detail = ErrorDetail(code="bad_request", message="Invalid input")
        assert detail.code == "bad_request"
        assert detail.message == "Invalid input"
        assert detail.details is None

    def test_details_optional(self):
        detail = ErrorDetail(
            code="validation_error",
            message="Validation failed",
            details={"errors": [{"loc": ["body"], "msg": "field required"}]},
        )
        assert detail.details is not None
        assert "errors" in detail.details


@pytest.mark.unit
class TestErrorEnvelope:
    """Test ErrorEnvelope model."""

    def test_envelope_contains_error_detail(self):
        detail = ErrorDetail(code="not_found", message="Resource not found")
        envelope = ErrorEnvelope(error=detail)
        assert envelope.error.code == "not_found"
        assert envelope.error.message == "Resource not found"


@pytest.mark.unit
class TestErrorResponse:
    """Test error_response() helper."""

    def test_returns_json_response_with_status(self):
        resp = error_response(400, "bad_request", "Invalid JSON body.")
        assert resp.status_code == 400
        assert resp.media_type == "application/json"

    def test_body_has_error_envelope_shape(self):
        resp = error_response(422, "validation_error", "Request validation failed.")
        body = resp.body.decode("utf-8")
        import json
        data = json.loads(body)
        assert "error" in data
        assert data["error"]["code"] == "validation_error"
        assert data["error"]["message"] == "Request validation failed."
        assert "details" in data["error"]

    def test_details_included_when_provided(self):
        resp = error_response(
            422,
            "validation_error",
            "Request validation failed.",
            details={"errors": [{"loc": ["body", "x"], "msg": "required"}]},
        )
        import json
        data = json.loads(resp.body.decode("utf-8"))
        assert data["error"]["details"] is not None
        assert data["error"]["details"]["errors"] is not None
        assert len(data["error"]["details"]["errors"]) == 1
