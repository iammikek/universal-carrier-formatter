"""
Tests for DPD Mapper.

Laravel Equivalent: tests/Unit/Mappers/DpdMapperTest.php

These tests validate that the DPD mapper correctly transforms messy DPD responses
to universal format.
"""

import pytest

from src.mappers.dpd_mapper import DpdMapper


@pytest.mark.unit
class TestDpdMapper:
    """Test DPD mapper transformations."""

    def test_maps_tracking_number(self):
        """Test mapping tracking number field."""
        mapper = DpdMapper()
        messy_response = {"trk_num": "1234567890"}

        result = mapper.map_tracking_response(messy_response)

        assert result["tracking_number"] == "1234567890"
        assert "trk_num" not in result

    def test_maps_and_normalizes_status(self):
        """Test mapping and normalizing status values."""
        mapper = DpdMapper()

        test_cases = [
            ("IN_TRANSIT", "in_transit"),
            ("DELIVERED", "delivered"),
            ("EXCEPTION", "exception"),
            ("PENDING", "pending"),
        ]

        for dpd_status, expected_status in test_cases:
            messy_response = {"stat": dpd_status}
            result = mapper.map_tracking_response(messy_response)
            assert result["status"] == expected_status

    def test_maps_location(self):
        """Test mapping location structure."""
        mapper = DpdMapper()
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
        mapper = DpdMapper()

        # UK postcode
        result = mapper._derive_country_from_postcode("SW1A 1AA")
        assert result == "GB"

        # US ZIP code
        result = mapper._derive_country_from_postcode("10001")
        assert result == "US"

    def test_maps_estimated_delivery(self):
        """Test mapping estimated delivery date."""
        mapper = DpdMapper()
        messy_response = {"est_del": "2026-01-30"}

        result = mapper.map_tracking_response(messy_response)

        assert "estimated_delivery" in result
        assert result["estimated_delivery"].startswith("2026-01-30")

    def test_complete_transformation(self):
        """Test complete transformation of messy DPD response."""
        mapper = DpdMapper()
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
        mapper = DpdMapper()
        messy_response = {"trk_num": "1234567890"}

        result = mapper.map_tracking_response(messy_response)

        assert result["tracking_number"] == "1234567890"
        # Other fields should not be present if not in input
        assert "status" not in result or result.get("status") is None

    def test_handles_empty_location(self):
        """Test handling of empty location."""
        mapper = DpdMapper()
        messy_response = {"loc": {}}

        result = mapper.map_tracking_response(messy_response)

        # Should not create current_location if empty
        assert "current_location" not in result or not result.get("current_location")
