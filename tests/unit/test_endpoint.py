"""
Tests for Endpoint model.

Laravel Equivalent: tests/Unit/EndpointTest.php

These tests validate that the Endpoint model works correctly,
similar to how Laravel tests validate Eloquent models and validation rules.
"""

import pytest
from pydantic import ValidationError

from core import (Endpoint, HttpMethod, Parameter, ParameterLocation,
                  ParameterType, RequestSchema, ResponseSchema)


@pytest.mark.unit
class TestEndpoint:
    """
    Test Endpoint model.

    Laravel Equivalent: tests/Unit/EndpointTest.php
    """

    def test_creates_endpoint_with_required_fields(self):
        """Test creating an endpoint"""
        endpoint = Endpoint(
            path="/api/v1/track", method=HttpMethod.GET, summary="Track shipment"
        )

        assert endpoint.path == "/api/v1/track"
        assert endpoint.method == HttpMethod.GET
        assert endpoint.summary == "Track shipment"
        assert endpoint.authentication_required is False  # Default

    def test_endpoint_path_must_start_with_slash(self):
        """
        Test validation: path must start with /.

        Laravel Equivalent:
        public function test_path_validation()
        {
            $this->expectException(ValidationException::class);
            Endpoint::create(['path' => 'api/v1/track']);
        }
        """
        with pytest.raises(ValidationError) as exc_info:
            Endpoint(
                path="api/v1/track",  # Missing leading slash
                method=HttpMethod.GET,
                summary="Test",
            )

        assert "path" in str(exc_info.value).lower()

    def test_endpoint_with_request_and_responses(self):
        """Test endpoint with request and response schemas"""
        request = RequestSchema(
            content_type="application/json",
            parameters=[
                Parameter(
                    name="tracking_number",
                    type=ParameterType.STRING,
                    location=ParameterLocation.PATH,
                    required=True,
                )
            ],
        )

        response = ResponseSchema(
            status_code=200, content_type="application/json", description="Success"
        )

        endpoint = Endpoint(
            path="/api/v1/track/{tracking_number}",
            method=HttpMethod.GET,
            summary="Track shipment",
            request=request,
            responses=[response],
        )

        assert endpoint.request is not None
        assert len(endpoint.responses) == 1
        assert endpoint.responses[0].status_code == 200
