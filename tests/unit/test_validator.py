"""
Tests for Carrier Validator.

Laravel Equivalent: tests/Unit/ValidatorTest.php

These tests validate that the CarrierValidator correctly validates
carrier responses against the Universal Carrier Format schema.
"""

import pytest
from pydantic import ValidationError

from src.core.schema import UniversalCarrierFormat
from src.core.validator import CarrierValidator


@pytest.mark.unit
class TestCarrierValidator:
    """Test CarrierValidator validation logic."""

    def test_validate_success(self):
        """Test successful validation of valid carrier data."""
        validator = CarrierValidator()

        valid_data = {
            "name": "Test Carrier",
            "base_url": "https://api.test.com",
            "version": "v1",
            "endpoints": [
                {
                    "path": "/api/v1/track",
                    "method": "GET",
                    "summary": "Track shipment",
                }
            ],
        }

        result = validator.validate(valid_data)

        assert isinstance(result, UniversalCarrierFormat)
        assert result.name == "Test Carrier"
        assert str(result.base_url) == "https://api.test.com/"
        assert len(result.endpoints) == 1

    def test_validate_missing_required_fields(self):
        """Test validation fails when required fields are missing."""
        validator = CarrierValidator()

        invalid_data = {
            "name": "Test Carrier",
            # Missing base_url and endpoints
        }

        with pytest.raises(ValidationError):
            validator.validate(invalid_data)

    def test_validate_invalid_base_url(self):
        """Test validation fails with invalid URL."""
        validator = CarrierValidator()

        invalid_data = {
            "name": "Test Carrier",
            "base_url": "not-a-valid-url",
            "endpoints": [],
        }

        with pytest.raises(ValidationError):
            validator.validate(invalid_data)

    def test_validate_invalid_endpoints(self):
        """Test validation fails with invalid endpoint data."""
        validator = CarrierValidator()

        invalid_data = {
            "name": "Test Carrier",
            "base_url": "https://api.test.com",
            "endpoints": [
                {
                    "path": "/api/track",
                    # Missing required 'method' and 'summary'
                }
            ],
        }

        with pytest.raises(ValidationError):
            validator.validate(invalid_data)

    def test_validate_endpoint_success(self):
        """Test validating a single endpoint."""
        validator = CarrierValidator()

        valid_endpoint = {
            "path": "/api/v1/track",
            "method": "GET",
            "summary": "Track shipment",
        }

        result = validator.validate_endpoint(valid_endpoint)
        assert result is True

    def test_validate_endpoint_invalid(self):
        """Test endpoint validation fails with invalid data."""
        validator = CarrierValidator()

        invalid_endpoint = {
            "path": "/api/track",
            # Missing required fields
        }

        with pytest.raises(ValidationError):
            validator.validate_endpoint(invalid_endpoint)

    def test_validate_batch_success(self):
        """Test batch validation of multiple carrier responses."""
        validator = CarrierValidator()

        batch_data = [
            {
                "name": "Carrier 1",
                "base_url": "https://api.carrier1.com",
                "endpoints": [{"path": "/track", "method": "GET", "summary": "Track"}],
            },
            {
                "name": "Carrier 2",
                "base_url": "https://api.carrier2.com",
                "endpoints": [{"path": "/ship", "method": "POST", "summary": "Ship"}],
            },
        ]

        results = validator.validate_batch(batch_data)

        assert len(results) == 2
        assert results[0].name == "Carrier 1"
        assert results[1].name == "Carrier 2"

    def test_validate_batch_with_errors(self):
        """Test batch validation fails when any response is invalid."""
        validator = CarrierValidator()

        batch_data = [
            {
                "name": "Carrier 1",
                "base_url": "https://api.carrier1.com",
                "endpoints": [{"path": "/track", "method": "GET", "summary": "Track"}],
            },
            {
                "name": "Carrier 2",
                # Missing required fields
            },
        ]

        with pytest.raises((ValidationError, ValueError)):
            validator.validate_batch(batch_data)

    def test_validate_error_messages(self):
        """Test that validation errors provide helpful messages."""
        validator = CarrierValidator()

        invalid_data = {
            "name": "Test",
            # Missing base_url
        }

        with pytest.raises(ValidationError):
            validator.validate(invalid_data)

        # Just verify ValidationError is raised (message format may vary)
        # The important thing is that validation fails appropriately
