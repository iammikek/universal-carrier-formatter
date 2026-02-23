"""
Unit tests for extract request parsing (ExtractInput, parse_extract_request).
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock

from fastapi import HTTPException
from fastapi.responses import JSONResponse

from src.api.extract_parsing import parse_extract_request
from src.api.schemas import ExtractInput


def _run(coro):
    """Run async coroutine from sync test."""
    return asyncio.run(coro)


def _make_request(
    content_type: str = "application/json",
    json_body: dict | None = None,
    async_param: str = "",
):
    """Build a mock Request for parse_extract_request."""
    request = MagicMock()
    request.headers = {"content-type": content_type}
    request.query_params = MagicMock()
    request.query_params.get = MagicMock(return_value=async_param)
    if json_body is not None:
        request.json = AsyncMock(return_value=json_body)
    return request


@pytest.mark.unit
class TestParseExtractRequest:
    """Test parse_extract_request with mocked Request."""

    def test_json_valid_returns_extract_input(self):
        request = _make_request(
            content_type="application/json",
            json_body={"extracted_text": "Sample carrier API doc."},
        )
        result = _run(parse_extract_request(request))
        assert isinstance(result, ExtractInput)
        assert result.extracted_text == "Sample carrier API doc."
        assert result.pdf_content is None
        assert result.pdf_filename is None
        assert result.async_mode is False

    def test_json_with_async_param(self):
        request = _make_request(
            content_type="application/json",
            json_body={"extracted_text": "x"},
            async_param="1",
        )
        result = _run(parse_extract_request(request))
        assert isinstance(result, ExtractInput)
        assert result.async_mode is True

    def test_json_empty_extracted_text_returns_422_response(self):
        request = _make_request(
            content_type="application/json",
            json_body={"extracted_text": ""},
        )
        result = _run(parse_extract_request(request))
        assert isinstance(result, JSONResponse)
        assert result.status_code == 422

    def test_json_missing_extracted_text_returns_422_response(self):
        request = _make_request(
            content_type="application/json",
            json_body={},
        )
        result = _run(parse_extract_request(request))
        assert isinstance(result, JSONResponse)
        assert result.status_code == 422

    def test_bad_content_type_raises_400(self):
        request = _make_request(content_type="text/plain")
        with pytest.raises(HTTPException) as exc_info:
            _run(parse_extract_request(request))
        assert exc_info.value.status_code == 400

    def test_json_invalid_type_returns_422_response(self):
        request = _make_request(content_type="application/json", json_body=None)
        request.json = AsyncMock(return_value="not a dict")
        result = _run(parse_extract_request(request))
        assert isinstance(result, JSONResponse)
        assert result.status_code == 422
