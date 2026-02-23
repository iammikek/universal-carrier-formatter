"""
Unit tests for API request/response schemas (Pydantic models).
"""

import pytest
from pydantic import ValidationError

from src.api import ConvertRequest, ExtractFromTextRequest, ExtractResponse


@pytest.mark.unit
class TestConvertRequest:
    """Test ConvertRequest schema."""

    def test_valid_minimal(self):
        req = ConvertRequest.model_validate({"carrier_response": {"trk_num": "123"}})
        assert req.carrier_response == {"trk_num": "123"}
        assert req.carrier == "example"

    def test_carrier_optional_default(self):
        req = ConvertRequest.model_validate({"carrier_response": {}})
        assert req.carrier == "example"

    def test_carrier_explicit(self):
        req = ConvertRequest.model_validate(
            {"carrier_response": {}, "carrier": "dhl"}
        )
        assert req.carrier == "dhl"

    def test_missing_carrier_response_raises(self):
        with pytest.raises(ValidationError):
            ConvertRequest.model_validate({})

    def test_carrier_response_must_be_dict(self):
        with pytest.raises(ValidationError):
            ConvertRequest.model_validate({"carrier_response": "not a dict"})
        with pytest.raises(ValidationError):
            ConvertRequest.model_validate({"carrier_response": None})


@pytest.mark.unit
class TestExtractFromTextRequest:
    """Test ExtractFromTextRequest schema."""

    def test_valid(self):
        req = ExtractFromTextRequest.model_validate(
            {"extracted_text": "Sample PDF text content."}
        )
        assert req.extracted_text == "Sample PDF text content."

    def test_empty_text_raises(self):
        with pytest.raises(ValidationError):
            ExtractFromTextRequest.model_validate({"extracted_text": ""})

    def test_missing_extracted_text_raises(self):
        with pytest.raises(ValidationError):
            ExtractFromTextRequest.model_validate({})

    def test_text_too_long_raises(self):
        with pytest.raises(ValidationError):
            ExtractFromTextRequest.model_validate(
                {"extracted_text": "x" * (2_000_001)}
            )


@pytest.mark.unit
class TestExtractResponse:
    """Test ExtractResponse schema."""

    def test_minimal_valid(self):
        resp = ExtractResponse.model_validate(
            {
                "schema_version": "1.0",
                "generator_version": "0.1.0",
                "schema": {"name": "Test", "endpoints": []},
            }
        )
        assert resp.schema_version == "1.0"
        assert resp.generator_version == "0.1.0"
        assert resp.schema_["name"] == "Test"
        assert resp.field_mappings == []
        assert resp.constraints == []
        assert resp.edge_cases == []
        assert resp.extraction_metadata is None

    def test_serialization_uses_schema_alias(self):
        resp = ExtractResponse(
            schema_version="1.0",
            generator_version="0.1.0",
            schema_={"name": "Test", "endpoints": []},
        )
        d = resp.model_dump(by_alias=True)
        assert "schema" in d
        assert d["schema"]["name"] == "Test"
