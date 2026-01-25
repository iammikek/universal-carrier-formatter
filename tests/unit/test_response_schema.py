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
        with pytest.raises(ValidationError):
            ResponseSchema(status_code=999)
        
        # Invalid status code (too low)
        with pytest.raises(ValidationError):
            ResponseSchema(status_code=50)
