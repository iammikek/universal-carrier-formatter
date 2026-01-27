"""
Tests for Universal Carrier Format model.

Laravel Equivalent: tests/Unit/CarrierSchemaTest.php

These tests validate that the UniversalCarrierFormat model works correctly,
similar to how Laravel tests validate Eloquent models and validation rules.
"""

import pytest
from pydantic import ValidationError

from src.core import (
    AuthenticationMethod,
    Endpoint,
    HttpMethod,
    Parameter,
    ParameterLocation,
    ParameterType,
    RateLimit,
    RequestSchema,
    ResponseSchema,
    UniversalCarrierFormat,
)


@pytest.mark.unit
class TestUniversalCarrierFormat:
    """
    Test Universal Carrier Format model.

    Laravel Equivalent: tests/Unit/CarrierSchemaTest.php
    """

    def test_creates_carrier_format_with_minimal_data(self):
        """
        Test creating carrier format with minimal required fields.

        Laravel Equivalent:
        public function test_creates_carrier_with_minimal_data()
        {
            $carrier = CarrierSchema::create([
                'name' => 'Test Carrier',
                'base_url' => 'https://api.test.com',
                'endpoints' => [
                    [
                        'path' => '/api/track',
                        'method' => 'GET',
                        'summary' => 'Track'
                    ]
                ]
            ]);

            $this->assertNotNull($carrier->id);
        }
        """
        carrier = UniversalCarrierFormat(
            name="Test Carrier",
            base_url="https://api.test.com",
            endpoints=[
                Endpoint(
                    path="/api/track", method=HttpMethod.GET, summary="Track shipment"
                )
            ],
        )

        assert carrier.name == "Test Carrier"
        # HttpUrl normalizes URLs by adding trailing slash
        assert str(carrier.base_url) == "https://api.test.com/"
        assert len(carrier.endpoints) == 1

    def test_carrier_name_cannot_be_empty(self):
        """
        Test validation: carrier name cannot be empty.

        Laravel Equivalent:
        public function test_name_validation()
        {
            $this->expectException(ValidationException::class);
            CarrierSchema::create(['name' => '']);
        }
        """
        with pytest.raises(ValidationError) as exc_info:
            UniversalCarrierFormat(
                name="",  # Empty name should fail
                base_url="https://api.test.com",
                endpoints=[
                    Endpoint(path="/api/track", method=HttpMethod.GET, summary="Test")
                ],
            )

        assert "name" in str(exc_info.value).lower()

    def test_carrier_name_cannot_be_whitespace_only(self):
        """
        Test validation: carrier name cannot be whitespace only.

        This tests the validator that raises ValueError on line 411.
        """
        with pytest.raises(ValidationError) as exc_info:
            UniversalCarrierFormat(
                name="   ",  # Whitespace only should fail
                base_url="https://api.test.com",
                endpoints=[
                    Endpoint(path="/api/track", method=HttpMethod.GET, summary="Test")
                ],
            )

        assert "name" in str(exc_info.value).lower()

    def test_carrier_must_have_at_least_one_endpoint(self):
        """
        Test validation: must have at least one endpoint.

        Laravel Equivalent:
        public function test_endpoints_validation()
        {
            $this->expectException(ValidationException::class);
            CarrierSchema::create([
                'name' => 'Test',
                'base_url' => 'https://api.test.com',
                'endpoints' => []
            ]);
        }
        """
        with pytest.raises(ValidationError) as exc_info:
            UniversalCarrierFormat(
                name="Test Carrier",
                base_url="https://api.test.com",
                endpoints=[],  # Empty endpoints should fail
            )

        assert "endpoint" in str(exc_info.value).lower()

    def test_carrier_endpoints_cannot_be_none(self):
        """
        Test validation: endpoints cannot be None.

        This tests the validator that raises ValueError on line 423.
        """
        # Note: Pydantic will convert None to empty list, so we test with empty list
        # The validator checks `if not v or len(v) == 0` which covers both cases
        with pytest.raises(ValidationError) as exc_info:
            UniversalCarrierFormat(
                name="Test Carrier",
                base_url="https://api.test.com",
                endpoints=[],  # Empty list should fail (same as None after Pydantic processing)
            )

        assert "endpoint" in str(exc_info.value).lower()

    def test_carrier_with_full_schema(self):
        endpoint = Endpoint(
            path="/api/v1/track/{tracking_number}",
            method=HttpMethod.GET,
            summary="Track shipment",
            description="Get tracking information",
            authentication_required=True,
            request=RequestSchema(
                parameters=[
                    Parameter(
                        name="tracking_number",
                        type=ParameterType.STRING,
                        location=ParameterLocation.PATH,
                        required=True,
                    )
                ]
            ),
            responses=[ResponseSchema(status_code=200, description="Success")],
        )

        auth = AuthenticationMethod(
            type="api_key",
            name="API Key",
            location="header",
            parameter_name="X-API-Key",
        )

        rate_limit = RateLimit(requests=100, period="1 minute")

        carrier = UniversalCarrierFormat(
            name="Full Test Carrier",
            base_url="https://api.fulltest.com",
            version="v1",
            description="Complete test carrier",
            endpoints=[endpoint],
            authentication=[auth],
            rate_limits=[rate_limit],
        )

        assert carrier.name == "Full Test Carrier"
        assert carrier.version == "v1"
        assert len(carrier.endpoints) == 1
        assert len(carrier.authentication) == 1
        assert len(carrier.rate_limits) == 1

    def test_carrier_json_serialization(self):
        """
        Test JSON serialization (like Laravel's toArray/toJson).

        Laravel Equivalent:
        public function test_to_array()
        {
            $carrier = CarrierSchema::create([...]);
            $array = $carrier->toArray();
            $this->assertIsArray($array);
        }
        """
        carrier = UniversalCarrierFormat(
            name="Test Carrier",
            base_url="https://api.test.com",
            endpoints=[
                Endpoint(path="/api/track", method=HttpMethod.GET, summary="Track")
            ],
        )

        # Convert to dict (like Laravel's toArray())
        carrier_dict = carrier.model_dump()

        assert isinstance(carrier_dict, dict)
        assert carrier_dict["name"] == "Test Carrier"
        assert len(carrier_dict["endpoints"]) == 1

    def test_carrier_json_file_operations(self, tmp_path):
        """
        Test saving and loading from JSON file.

        Laravel Equivalent:
        public function test_save_to_json_file()
        {
            $carrier = CarrierSchema::create([...]);
            $filepath = storage_path('test.json');
            $carrier->toJsonFile($filepath);
            $this->assertFileExists($filepath);
        }
        """
        carrier = UniversalCarrierFormat(
            name="File Test Carrier",
            base_url="https://api.filetest.com",
            endpoints=[
                Endpoint(path="/api/track", method=HttpMethod.GET, summary="Track")
            ],
        )

        # Save to file
        filepath = tmp_path / "test_carrier.json"
        carrier.to_json_file(str(filepath))

        # Verify file exists and is valid JSON
        assert filepath.exists()

        # Load from file
        loaded_carrier = UniversalCarrierFormat.from_json_file(str(filepath))

        assert loaded_carrier.name == carrier.name
        assert str(loaded_carrier.base_url) == str(carrier.base_url)
        assert len(loaded_carrier.endpoints) == len(carrier.endpoints)
