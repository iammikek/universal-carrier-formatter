"""
Tests for Parameter model.

Laravel Equivalent: tests/Unit/ParameterTest.php

These tests validate that the Parameter model works correctly,
similar to how Laravel tests validate Eloquent models and validation rules.
"""

import pytest
from pydantic import ValidationError

from src.core import Parameter, ParameterLocation, ParameterType


@pytest.mark.unit
class TestParameter:
    """
    Test Parameter model.

    Laravel Equivalent:
    class ParameterTest extends TestCase
    {
        public function test_creates_parameter_with_required_fields()
        {
            $param = Parameter::create([
                'name' => 'tracking_number',
                'type' => 'string',
                'location' => 'path',
                'required' => true,
            ]);

            $this->assertEquals('tracking_number', $param->name);
        }
    }
    """

    def test_creates_parameter_with_required_fields(self):
        """Test creating a parameter with required fields"""
        param = Parameter(
            name="tracking_number",
            type=ParameterType.STRING,
            location=ParameterLocation.PATH,
            required=True,
        )

        assert param.name == "tracking_number"
        assert param.type == ParameterType.STRING
        assert param.location == ParameterLocation.PATH
        assert param.required is True

    def test_parameter_name_cannot_be_empty(self):
        """
        Test validation: parameter name cannot be empty.

        Laravel Equivalent:
        public function test_parameter_name_validation()
        {
            $this->expectException(ValidationException::class);
            Parameter::create(['name' => '']);
        }
        """
        with pytest.raises(ValidationError) as exc_info:
            Parameter(
                name="",  # Empty name should fail
                type=ParameterType.STRING,
                location=ParameterLocation.PATH,
            )

        assert "name" in str(exc_info.value)

    def test_parameter_name_cannot_be_whitespace_only(self):
        """
        Test validation: parameter name cannot be whitespace only.

        This tests the validator that raises ValueError on line 118.
        """
        with pytest.raises(ValidationError) as exc_info:
            Parameter(
                name="   ",  # Whitespace only should fail
                type=ParameterType.STRING,
                location=ParameterLocation.PATH,
            )

        assert "name" in str(exc_info.value)

    def test_parameter_with_optional_fields(self):
        """
        Test parameter with optional fields.

        Note: We use 'default' (the alias) instead of 'default_value' when creating,
        or we can use the field name directly. Pydantic's alias is mainly for JSON serialization.
        """
        # Use the alias 'default' when creating from dict-like data
        param = Parameter(
            name="api_key",
            type=ParameterType.STRING,
            location=ParameterLocation.HEADER,
            required=True,
            description="API key for authentication",
            default="test-key",  # Use alias name
            example="abc123xyz",
        )

        assert param.description == "API key for authentication"
        # Access via field name
        assert param.default_value == "test-key"
        assert param.example == "abc123xyz"
