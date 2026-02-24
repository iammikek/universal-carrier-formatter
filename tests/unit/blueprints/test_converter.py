"""
Tests for Blueprint Converter.

"""

import pytest

from src.blueprints.converter import BlueprintConverter
from src.core.schema import UniversalCarrierFormat


@pytest.mark.unit
class TestBlueprintConverter:
    """Test BlueprintConverter."""

    @pytest.fixture
    def converter(self):
        """Create converter instance."""
        return BlueprintConverter()

    @pytest.fixture
    def valid_blueprint(self):
        """Create a valid blueprint for testing."""
        return {
            "carrier": {
                "name": "Test Carrier",
                "base_url": "https://api.test.com",
                "version": "v1",
                "description": "Test carrier API",
            },
            "authentication": {
                "type": "api_key",
                "location": "header",
                "parameter_name": "X-API-Key",
            },
            "endpoints": [
                {
                    "path": "/test",
                    "method": "GET",
                    "summary": "Test endpoint",
                    "description": "Test endpoint description",
                    "authentication_required": True,
                    "tags": ["test"],
                    "request": {
                        "content_type": "application/json",
                        "parameters": [
                            {
                                "name": "param1",
                                "type": "string",
                                "location": "query",
                                "required": True,
                                "description": "Test parameter",
                            }
                        ],
                    },
                    "responses": [
                        {
                            "status_code": 200,
                            "content_type": "application/json",
                            "description": "Success",
                        }
                    ],
                }
            ],
            "rate_limits": [
                {"requests": 100, "period": "1 minute", "description": "Rate limit"}
            ],
            "documentation_url": "https://docs.test.com",
        }

    def test_convert_valid_blueprint(self, converter, valid_blueprint):
        """Test converting a valid blueprint."""
        result = converter.convert(valid_blueprint)

        assert isinstance(result, UniversalCarrierFormat)
        assert result.name == "Test Carrier"
        assert str(result.base_url) == "https://api.test.com/"
        assert result.version == "v1"
        assert len(result.endpoints) == 1
        assert len(result.authentication) == 1
        assert len(result.rate_limits) == 1

    def test_convert_missing_carrier(self, converter):
        """Test conversion fails when carrier is missing."""
        blueprint = {"endpoints": []}
        with pytest.raises(ValueError, match="carrier"):
            converter.convert(blueprint)

    def test_convert_authentication_single_object(self, converter):
        """Test converting authentication as single object."""
        blueprint = {
            "carrier": {"name": "Test", "base_url": "https://api.test.com"},
            "endpoints": [{"path": "/test", "method": "GET", "summary": "Test"}],
            "authentication": {
                "type": "bearer",
                "scheme": "Bearer",
                "location": "header",
            },
        }
        result = converter.convert(blueprint)

        assert len(result.authentication) == 1
        assert result.authentication[0].type == "bearer"
        assert result.authentication[0].scheme == "Bearer"

    def test_convert_authentication_list(self, converter):
        """Test converting authentication as list."""
        blueprint = {
            "carrier": {"name": "Test", "base_url": "https://api.test.com"},
            "endpoints": [{"path": "/test", "method": "GET", "summary": "Test"}],
            "authentication": [
                {"type": "api_key", "parameter_name": "X-API-Key"},
                {"type": "bearer", "scheme": "Bearer"},
            ],
        }
        result = converter.convert(blueprint)

        assert len(result.authentication) == 2

    def test_convert_endpoints(self, converter):
        """Test converting endpoints."""
        blueprint = {
            "carrier": {"name": "Test", "base_url": "https://api.test.com"},
            "endpoints": [
                {
                    "path": "/test1",
                    "method": "GET",
                    "summary": "Test 1",
                },
                {
                    "path": "/test2",
                    "method": "POST",
                    "summary": "Test 2",
                },
            ],
        }
        result = converter.convert(blueprint)

        assert len(result.endpoints) == 2
        assert result.endpoints[0].path == "/test1"
        assert result.endpoints[0].method.value == "GET"
        assert result.endpoints[1].path == "/test2"
        assert result.endpoints[1].method.value == "POST"

    def test_convert_parameters(self, converter):
        """Test converting request parameters."""
        blueprint = {
            "carrier": {"name": "Test", "base_url": "https://api.test.com"},
            "endpoints": [
                {
                    "path": "/test",
                    "method": "GET",
                    "summary": "Test",
                    "request": {
                        "parameters": [
                            {
                                "name": "param1",
                                "type": "string",
                                "location": "query",
                                "required": True,
                                "example": "test",
                            }
                        ]
                    },
                }
            ],
        }
        result = converter.convert(blueprint)

        assert len(result.endpoints[0].request.parameters) == 1
        param = result.endpoints[0].request.parameters[0]
        assert param.name == "param1"
        assert param.type.value == "string"
        assert param.location.value == "query"
        assert param.required is True
        assert param.example == "test"

    def test_convert_responses(self, converter):
        """Test converting responses."""
        blueprint = {
            "carrier": {"name": "Test", "base_url": "https://api.test.com"},
            "endpoints": [
                {
                    "path": "/test",
                    "method": "GET",
                    "summary": "Test",
                    "responses": [
                        {"status_code": 200, "description": "Success"},
                        {"status_code": 404, "description": "Not found"},
                    ],
                }
            ],
        }
        result = converter.convert(blueprint)

        assert len(result.endpoints[0].responses) == 2
        assert result.endpoints[0].responses[0].status_code == 200
        assert result.endpoints[0].responses[1].status_code == 404

    def test_convert_rate_limits(self, converter):
        """Test converting rate limits."""
        blueprint = {
            "carrier": {"name": "Test", "base_url": "https://api.test.com"},
            "endpoints": [{"path": "/test", "method": "GET", "summary": "Test"}],
            "rate_limits": [
                {"requests": 100, "period": "1 minute"},
                {"requests": 1000, "period": "1 hour", "description": "Hourly limit"},
            ],
        }
        result = converter.convert(blueprint)

        assert len(result.rate_limits) == 2
        assert result.rate_limits[0].requests == 100
        assert result.rate_limits[0].period == "1 minute"
        assert result.rate_limits[1].requests == 1000
        assert result.rate_limits[1].description == "Hourly limit"
