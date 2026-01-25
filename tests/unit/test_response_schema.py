"""
Tests for ResponseSchema model.

Laravel Equivalent: tests/Unit/ResponseSchemaTest.php

These tests validate that the ResponseSchema model works correctly,
similar to how Laravel tests validate Eloquent models and validation rules.
"""

import pytest
from src.models import ResponseSchema
from pydantic import ValidationError


@pytest.mark.unit
class TestResponseSchema:
    """
    Test ResponseSchema model.

    Laravel Equivalent: tests/Unit/ResponseSchemaTest.php
    """

    def test_response_status_code_validation(self):
        """
        Test status code validation.

        Laravel Equivalent:
        public function test_status_code_validation()
        {
            $this->expectException(ValidationException::class);
            ResponseSchema::create(['status_code' => 999]);
        }
        """
        # Valid status code
        response = ResponseSchema(status_code=200)
        assert response.status_code == 200

        # Invalid status code (too high)
        with pytest.raises(ValidationError) as exc_info:
            ResponseSchema(status_code=999)
        assert (
            "status_code" in str(exc_info.value).lower()
            or "between" in str(exc_info.value).lower()
        )

        # Invalid status code (too low)
        with pytest.raises(ValidationError) as exc_info:
            ResponseSchema(status_code=50)
        assert (
            "status_code" in str(exc_info.value).lower()
            or "between" in str(exc_info.value).lower()
        )

    def test_response_status_code_boundary_values(self):
        """
        Test status code boundary values.

        Tests the validator that raises ValueError on line 192.
        """
        # Test boundary values (100 and 599 should be valid)
        response_min = ResponseSchema(status_code=100)
        assert response_min.status_code == 100

        response_max = ResponseSchema(status_code=599)
        assert response_max.status_code == 599

        # Test just outside boundaries
        with pytest.raises(ValidationError):
            ResponseSchema(status_code=99)  # Too low

        with pytest.raises(ValidationError):
            ResponseSchema(status_code=600)  # Too high
