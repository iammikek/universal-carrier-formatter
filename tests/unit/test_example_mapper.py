"""
Tests for Example Mapper.

Laravel Equivalent: tests/Unit/Mappers/ExampleMapperTest.php

These tests validate that the Example mapper correctly transforms messy carrier responses
to universal format.
"""

import pytest

from src.core.schema import Endpoint, HttpMethod, Parameter, ParameterLocation, ParameterType
from src.mappers.example_mapper import ExampleMapper


@pytest.mark.unit
class TestExampleMapper:
    """Test Example mapper transformations."""

    def test_maps_tracking_number(self):
        """Test mapping tracking number field."""
        mapper = ExampleMapper()
        messy_response = {"trk_num": "1234567890"}

        result = mapper.map_tracking_response(messy_response)

        assert result["tracking_number"] == "1234567890"
        assert "trk_num" not in result

    def test_maps_and_normalizes_status(self):
        """Test mapping and normalizing status values."""
        mapper = ExampleMapper()

        test_cases = [
            ("IN_TRANSIT", "in_transit"),
            ("DELIVERED", "delivered"),
            ("EXCEPTION", "exception"),
            ("PENDING", "pending"),
        ]

        for carrier_status, expected_status in test_cases:
            messy_response = {"stat": carrier_status}
            result = mapper.map_tracking_response(messy_response)
            assert result["status"] == expected_status

    def test_maps_location(self):
        """Test mapping location structure."""
        mapper = ExampleMapper()
        messy_response = {
            "loc": {
                "city": "London",
                "postcode": "SW1A 1AA",
            }
        }

        result = mapper.map_tracking_response(messy_response)

        assert "current_location" in result
        assert result["current_location"]["city"] == "London"
        assert result["current_location"]["postal_code"] == "SW1A 1AA"
        assert result["current_location"]["country"] == "GB"  # Derived from postcode

    def test_derives_country_from_postcode(self):
        """Test country derivation from postcode."""
        mapper = ExampleMapper()

        # UK postcode
        result = mapper._derive_country_from_postcode("SW1A 1AA")
        assert result == "GB"

        # US ZIP code
        result = mapper._derive_country_from_postcode("10001")
        assert result == "US"

    def test_maps_estimated_delivery(self):
        """Test mapping estimated delivery date."""
        mapper = ExampleMapper()
        messy_response = {"est_del": "2026-01-30"}

        result = mapper.map_tracking_response(messy_response)

        assert "estimated_delivery" in result
        assert result["estimated_delivery"].startswith("2026-01-30")

    def test_complete_transformation(self):
        """Test complete transformation of messy carrier response."""
        mapper = ExampleMapper()
        messy_response = {
            "trk_num": "1234567890",
            "stat": "IN_TRANSIT",
            "loc": {
                "city": "London",
                "postcode": "SW1A 1AA",
            },
            "est_del": "2026-01-30",
        }

        result = mapper.map_tracking_response(messy_response)

        # Verify all fields are mapped
        assert result["tracking_number"] == "1234567890"
        assert result["status"] == "in_transit"
        assert result["current_location"]["city"] == "London"
        assert result["current_location"]["postal_code"] == "SW1A 1AA"
        assert result["current_location"]["country"] == "GB"
        assert "estimated_delivery" in result

        # Verify no messy fields remain
        assert "trk_num" not in result
        assert "stat" not in result
        assert "loc" not in result
        assert "est_del" not in result

    def test_handles_missing_fields(self):
        """Test handling of missing optional fields."""
        mapper = ExampleMapper()
        messy_response = {"trk_num": "1234567890"}

        result = mapper.map_tracking_response(messy_response)

        assert result["tracking_number"] == "1234567890"
        # Other fields should not be present if not in input
        assert "status" not in result or result.get("status") is None

    def test_handles_empty_location(self):
        """Test handling of empty location."""
        mapper = ExampleMapper()
        messy_response = {"loc": {}}

        result = mapper.map_tracking_response(messy_response)

        # Should not create current_location if empty
        assert "current_location" not in result or not result.get("current_location")

    def test_map_carrier_schema(self):
        """Test mapping complete carrier schema."""
        mapper = ExampleMapper()
        carrier_schema = {
            "carrier": "Example Carrier",
            "api_url": "https://api.example.com",
            "api_ver": "v2",
            "description": "Example Carrier API v2",
            "endpoints": [
                {
                    "path": "/track",
                    "method": "GET",
                    "summary": "Track shipment",
                    "params": [
                        {"name": "tracking_number", "type": "string", "required": True}
                    ],
                }
            ],
            "auth": {"type": "api_key", "location": "header", "param_name": "X-API-Key"},
            "rate_limits": [{"requests": 100, "period": "1 minute"}],
            "docs_url": "https://docs.example.com",
        }

        result = mapper.map_carrier_schema(carrier_schema)

        assert result.name == "Example Carrier"
        assert str(result.base_url) == "https://api.example.com/"
        assert result.version == "v2"
        assert len(result.endpoints) == 1
        assert result.endpoints[0].path == "/track"
        assert result.endpoints[0].method == HttpMethod.GET

    def test_map_endpoints(self):
        """Test endpoint mapping."""
        mapper = ExampleMapper()
        carrier_endpoints = [
            {
                "path": "track",
                "method": "POST",
                "summary": "Track shipment",
                "params": [
                    {"name": "id", "type": "integer", "required": True},
                    {"name": "format", "type": "string", "required": False},
                ],
            }
        ]

        result = mapper._map_endpoints(carrier_endpoints)

        assert len(result) == 1
        assert isinstance(result[0], Endpoint)
        assert result[0].path == "/track"  # Should add leading slash
        assert result[0].method == HttpMethod.POST
        assert len(result[0].request.parameters) == 2
        assert result[0].request.parameters[0].type == ParameterType.INTEGER

    def test_map_endpoints_invalid_method(self):
        """Test endpoint mapping with invalid HTTP method."""
        mapper = ExampleMapper()
        carrier_endpoints = [{"path": "/track", "method": "INVALID", "summary": "Track"}]

        result = mapper._map_endpoints(carrier_endpoints)

        assert len(result) == 1
        # Should default to GET for invalid method
        assert result[0].method == HttpMethod.GET

    def test_map_authentication(self):
        """Test authentication mapping."""
        mapper = ExampleMapper()
        carrier_auth = {
            "type": "api_key",
            "location": "header",
            "param_name": "X-API-Key",
            "description": "Example Carrier API Key",
        }

        result = mapper._map_authentication(carrier_auth)

        assert len(result) == 1
        assert result[0]["type"] == "api_key"
        assert result[0]["location"] == "header"
        assert result[0]["parameter_name"] == "X-API-Key"

    def test_map_authentication_unknown_type(self):
        """Test authentication mapping with unknown type."""
        mapper = ExampleMapper()
        carrier_auth = {"type": "unknown"}

        result = mapper._map_authentication(carrier_auth)

        assert result == []

    def test_map_rate_limits(self):
        """Test rate limit mapping."""
        mapper = ExampleMapper()
        carrier_limits = [
            {"requests": 100, "period": "1 minute", "description": "Per minute limit"},
            {"requests": 10000, "period": "1 day"},
        ]

        result = mapper._map_rate_limits(carrier_limits)

        assert len(result) == 2
        assert result[0]["requests"] == 100
        assert result[0]["period"] == "1 minute"
        assert result[1]["requests"] == 10000

    def test_date_parsing_error_handling(self):
        """Test handling of invalid date formats."""
        mapper = ExampleMapper()
        messy_response = {"est_del": "invalid-date-format"}

        result = mapper.map_tracking_response(messy_response)

        # Should use date as-is if parsing fails
        assert result["estimated_delivery"] == "invalid-date-format"

    def test_derive_country_unknown_format(self):
        """Test country derivation for unknown postcode format."""
        mapper = ExampleMapper()

        # "12345" matches US ZIP pattern (5 digits), so returns US
        result = mapper._derive_country_from_postcode("12345")
        assert result == "US"
        
        # Test with truly unknown format (non-numeric, non-UK pattern)
        result = mapper._derive_country_from_postcode("XYZ123")
        assert result == "GB"  # Default
