"""
Tests for Blueprint Validator.

Laravel Equivalent: tests/Unit/BlueprintValidatorTest.php
"""

import pytest

from src.blueprints.validator import BlueprintValidator


@pytest.mark.unit
class TestBlueprintValidator:
    """Test BlueprintValidator."""

    @pytest.fixture
    def validator(self):
        """Create validator instance."""
        return BlueprintValidator()

    @pytest.fixture
    def valid_blueprint(self):
        """Create a valid blueprint for testing."""
        return {
            "carrier": {
                "name": "Test Carrier",
                "base_url": "https://api.test.com",
            },
            "endpoints": [
                {
                    "path": "/test",
                    "method": "GET",
                    "summary": "Test endpoint",
                }
            ],
        }

    def test_validate_valid_blueprint(self, validator, valid_blueprint):
        """Test validating a valid blueprint."""
        errors = validator.validate(valid_blueprint)
        assert len(errors) == 0

    def test_validate_missing_carrier(self, validator):
        """Test validation fails when carrier section is missing."""
        blueprint = {"endpoints": []}
        errors = validator.validate(blueprint)
        assert "Missing required 'carrier' section" in errors

    def test_validate_missing_carrier_name(self, validator):
        """Test validation fails when carrier.name is missing."""
        blueprint = {
            "carrier": {"base_url": "https://api.test.com"},
            "endpoints": [{"path": "/test", "method": "GET", "summary": "Test"}],
        }
        errors = validator.validate(blueprint)
        assert any("carrier.name" in error for error in errors)

    def test_validate_invalid_base_url(self, validator):
        """Test validation fails with invalid base_url."""
        blueprint = {
            "carrier": {"name": "Test", "base_url": "not-a-url"},
            "endpoints": [{"path": "/test", "method": "GET", "summary": "Test"}],
        }
        errors = validator.validate(blueprint)
        assert any("base_url" in error and "URL" in error for error in errors)

    def test_validate_missing_endpoints(self, validator):
        """Test validation fails when endpoints are missing."""
        blueprint = {"carrier": {"name": "Test", "base_url": "https://api.test.com"}}
        errors = validator.validate(blueprint)
        assert "Missing required 'endpoints' section" in errors

    def test_validate_empty_endpoints(self, validator):
        """Test validation fails when endpoints list is empty."""
        blueprint = {
            "carrier": {"name": "Test", "base_url": "https://api.test.com"},
            "endpoints": [],
        }
        errors = validator.validate(blueprint)
        assert any("at least one endpoint" in error for error in errors)

    def test_validate_endpoint_missing_path(self, validator):
        """Test validation fails when endpoint path is missing."""
        blueprint = {
            "carrier": {"name": "Test", "base_url": "https://api.test.com"},
            "endpoints": [{"method": "GET", "summary": "Test"}],
        }
        errors = validator.validate(blueprint)
        assert any("path" in error for error in errors)

    def test_validate_endpoint_path_not_starting_with_slash(self, validator):
        """Test validation fails when path doesn't start with /."""
        blueprint = {
            "carrier": {"name": "Test", "base_url": "https://api.test.com"},
            "endpoints": [{"path": "test", "method": "GET", "summary": "Test"}],
        }
        errors = validator.validate(blueprint)
        assert any("must start with '/'" in error for error in errors)

    def test_validate_endpoint_invalid_method(self, validator):
        """Test validation fails with invalid HTTP method."""
        blueprint = {
            "carrier": {"name": "Test", "base_url": "https://api.test.com"},
            "endpoints": [{"path": "/test", "method": "INVALID", "summary": "Test"}],
        }
        errors = validator.validate(blueprint)
        assert any("method" in error and "must be one of" in error for error in errors)

    def test_validate_endpoint_missing_summary(self, validator):
        """Test validation fails when endpoint summary is missing."""
        blueprint = {
            "carrier": {"name": "Test", "base_url": "https://api.test.com"},
            "endpoints": [{"path": "/test", "method": "GET"}],
        }
        errors = validator.validate(blueprint)
        assert any("summary" in error for error in errors)

    def test_validate_parameter_missing_name(self, validator):
        """Test validation fails when parameter name is missing."""
        blueprint = {
            "carrier": {"name": "Test", "base_url": "https://api.test.com"},
            "endpoints": [
                {
                    "path": "/test",
                    "method": "GET",
                    "summary": "Test",
                    "request": {
                        "parameters": [{"type": "string", "location": "query"}]
                    },
                }
            ],
        }
        errors = validator.validate(blueprint)
        assert any("parameters" in error and "name" in error for error in errors)

    def test_validate_response_invalid_status_code(self, validator):
        """Test validation fails with invalid status code."""
        blueprint = {
            "carrier": {"name": "Test", "base_url": "https://api.test.com"},
            "endpoints": [
                {
                    "path": "/test",
                    "method": "GET",
                    "summary": "Test",
                    "responses": [{"status_code": 999}],
                }
            ],
        }
        errors = validator.validate(blueprint)
        assert any("status_code" in error and "between 100 and 599" in error for error in errors)

    def test_validate_authentication_invalid_type(self, validator):
        """Test validation fails with invalid authentication type."""
        blueprint = {
            "carrier": {"name": "Test", "base_url": "https://api.test.com"},
            "endpoints": [{"path": "/test", "method": "GET", "summary": "Test"}],
            "authentication": {"type": "invalid_type"},
        }
        errors = validator.validate(blueprint)
        assert any("authentication" in error and "type" in error for error in errors)

    def test_validate_rate_limit_invalid_requests(self, validator):
        """Test validation fails with invalid rate limit requests."""
        blueprint = {
            "carrier": {"name": "Test", "base_url": "https://api.test.com"},
            "endpoints": [{"path": "/test", "method": "GET", "summary": "Test"}],
            "rate_limits": [{"requests": -1, "period": "1 minute"}],
        }
        errors = validator.validate(blueprint)
        assert any("rate_limits" in error and "positive integer" in error for error in errors)

    def test_is_valid(self, validator, valid_blueprint):
        """Test is_valid returns True for valid blueprint."""
        assert validator.is_valid(valid_blueprint) is True

    def test_is_valid_returns_false(self, validator):
        """Test is_valid returns False for invalid blueprint."""
        blueprint = {"carrier": {"name": "Test"}}  # Missing base_url and endpoints
        assert validator.is_valid(blueprint) is False
