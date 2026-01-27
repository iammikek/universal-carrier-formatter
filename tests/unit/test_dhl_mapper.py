"""
Tests for DHL Mapper.

Laravel Equivalent: tests/Unit/DhlMapperTest.php
"""

import pytest

from src.mappers.dhl_mapper import MydhlApiMapper


@pytest.mark.unit
class TestMydhlApiMapper:
    """Test MydhlApiMapper."""

    @pytest.fixture
    def mapper(self):
        """Create mapper instance."""
        return MydhlApiMapper()

    def test_mapper_has_field_mapping(self, mapper):
        """Test mapper has FIELD_MAPPING."""
        assert hasattr(mapper, "FIELD_MAPPING")
        assert isinstance(mapper.FIELD_MAPPING, dict)
        assert len(mapper.FIELD_MAPPING) > 0

    def test_mapper_has_status_mapping(self, mapper):
        """Test mapper has STATUS_MAPPING."""
        assert hasattr(mapper, "STATUS_MAPPING")
        assert isinstance(mapper.STATUS_MAPPING, dict)
        assert len(mapper.STATUS_MAPPING) > 0

    def test_field_mapping_no_duplicates(self, mapper):
        """Test FIELD_MAPPING has no duplicate keys."""
        keys = list(mapper.FIELD_MAPPING.keys())
        unique_keys = set(keys)
        assert len(keys) == len(
            unique_keys
        ), f"Found duplicate keys: {[k for k in keys if keys.count(k) > 1]}"

    def test_map_tracking_response_basic(self, mapper):
        """Test basic tracking response mapping."""
        carrier_response = {
            "TrackingResponse": {
                "AWBInfo": {
                    "ArrayOfAWBInfoItem": [
                        {
                            "AWBNumber": "1234567890",
                            "Status": {"ActionStatus": "DELIVERED"},
                        }
                    ]
                }
            }
        }

        result = mapper.map_tracking_response(carrier_response)

        assert "tracking_number" in result
        assert result["tracking_number"] == "1234567890"
        assert "status" in result
        assert result["status"] == "delivered"

    def test_map_tracking_response_with_events(self, mapper):
        """Test tracking response with shipment events."""
        carrier_response = {
            "TrackingResponse": {
                "AWBInfo": {
                    "ArrayOfAWBInfoItem": [
                        {
                            "AWBNumber": "1234567890",
                            "Status": {"ActionStatus": "IN_TRANSIT"},
                            "ShipmentInfo": {
                                "ShipmentEvent": {
                                    "ArrayOfShipmentEventItem": [
                                        {
                                            "Date": "2026-01-25",
                                            "Time": "14:30:00",
                                            "GMTOffset": "+00:00",
                                            "ServiceEvent": {
                                                "Description": "In transit",
                                                "EventCode": "IT",
                                            },
                                            "ServiceArea": {"Description": "London"},
                                        }
                                    ]
                                }
                            },
                        }
                    ]
                }
            }
        }

        result = mapper.map_tracking_response(carrier_response)

        assert "tracking_number" in result
        assert "status" in result
        assert result["status"] == "in_transit"
        assert "last_update" in result
        assert "events" in result
        assert len(result["events"]) == 1
        assert result["events"][0]["event_description"] == "In transit"

    def test_map_tracking_response_empty(self, mapper):
        """Test mapping empty response."""
        result = mapper.map_tracking_response({})
        assert isinstance(result, dict)

    def test_map_tracking_response_missing_awb_info(self, mapper):
        """Test mapping response with missing AWBInfo."""
        carrier_response = {"TrackingResponse": {"AWBInfo": {"ArrayOfAWBInfoItem": []}}}

        result = mapper.map_tracking_response(carrier_response)
        assert isinstance(result, dict)

    def test_status_mapping(self, mapper):
        """Test status mapping converts correctly."""
        assert mapper.STATUS_MAPPING["DELIVERED"] == "delivered"
        assert mapper.STATUS_MAPPING["IN_TRANSIT"] == "in_transit"
        assert mapper.STATUS_MAPPING["EXCEPTION"] == "exception"
        assert mapper.STATUS_MAPPING["PENDING"] == "pending"

    def test_status_mapping_unknown_status(self, mapper):
        """Test unknown status is lowercased."""
        carrier_response = {
            "TrackingResponse": {
                "AWBInfo": {
                    "ArrayOfAWBInfoItem": [
                        {
                            "AWBNumber": "1234567890",
                            "Status": {"ActionStatus": "UNKNOWN_STATUS"},
                        }
                    ]
                }
            }
        }

        result = mapper.map_tracking_response(carrier_response)
        assert result["status"] == "unknown_status"

    def test_parse_event_datetime_with_offset(self, mapper):
        """Test parsing event datetime with GMT offset."""
        result = mapper._parse_event_datetime("2026-01-25", "14:30:00", "+00:00")
        assert result == "2026-01-25T14:30:00+00:00"

    def test_parse_event_datetime_without_time(self, mapper):
        """Test parsing event datetime without time."""
        result = mapper._parse_event_datetime("2026-01-25", None, None)
        assert result == "2026-01-25T00:00:00"

    def test_parse_event_datetime_invalid(self, mapper):
        """Test parsing invalid datetime returns None."""
        result = mapper._parse_event_datetime("invalid", "14:30:00", "+00:00")
        assert result is None

    def test_parse_date(self, mapper):
        """Test parsing date string."""
        result = mapper._parse_date("2026-01-25")
        assert result == "2026-01-25"

    def test_parse_date_invalid(self, mapper):
        """Test parsing invalid date returns None."""
        result = mapper._parse_date("invalid-date")
        assert result is None

    def test_get_latest_event(self, mapper):
        """Test getting latest event from list."""
        events = [
            {"Date": "2026-01-24", "Time": "10:00:00", "GMTOffset": "+00:00"},
            {"Date": "2026-01-25", "Time": "14:30:00", "GMTOffset": "+00:00"},
            {"Date": "2026-01-25", "Time": "12:00:00", "GMTOffset": "+00:00"},
        ]

        latest = mapper._get_latest_event(events)
        assert latest["Date"] == "2026-01-25"
        assert latest["Time"] == "14:30:00"

    def test_get_latest_event_empty(self, mapper):
        """Test getting latest event from empty list."""
        result = mapper._get_latest_event([])
        assert result is None
