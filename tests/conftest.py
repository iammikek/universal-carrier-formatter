"""
Shared test fixtures and configuration.

Laravel Equivalent: TestCase base class with setUp() methods.

Fixtures defined here are automatically available to all tests.
"""

from pathlib import Path

import pytest

from src.models import (Endpoint, HttpMethod, Parameter, ParameterLocation,
                        ParameterType, UniversalCarrierFormat)


@pytest.fixture
def sample_parameter():
    """
    Sample parameter fixture.

    Laravel Equivalent:
    protected function setUp(): void
    {
        $this->parameter = Parameter::create([...]);
    }
    """
    return Parameter(
        name="tracking_number",
        type=ParameterType.STRING,
        location=ParameterLocation.PATH,
        required=True,
    )


@pytest.fixture
def sample_endpoint():
    """
    Sample endpoint fixture.

    Laravel Equivalent:
    protected function setUp(): void
    {
        $this->endpoint = Endpoint::create([...]);
    }
    """
    return Endpoint(
        path="/api/v1/track", method=HttpMethod.GET, summary="Track shipment"
    )


@pytest.fixture
def sample_carrier():
    """
    Sample carrier format fixture.

    Laravel Equivalent:
    protected function setUp(): void
    {
        $this->carrier = CarrierSchema::create([...]);
    }
    """
    return UniversalCarrierFormat(
        name="Test Carrier",
        base_url="https://api.test.com",
        endpoints=[
            Endpoint(path="/api/track", method=HttpMethod.GET, summary="Track shipment")
        ],
    )


@pytest.fixture
def temp_output_dir(tmp_path):
    """
    Temporary directory for test output files.

    Laravel Equivalent:
    protected function setUp(): void
    {
        $this->outputDir = storage_path('tests/temp');
    }
    """
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir
