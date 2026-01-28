"""
Shared test fixtures and configuration.

Fixtures defined here are automatically available to all tests.
"""

import pytest

from src.core import (
    Endpoint,
    HttpMethod,
    Parameter,
    ParameterLocation,
    ParameterType,
    UniversalCarrierFormat,
)


@pytest.fixture
def sample_parameter():
    """
    Sample parameter fixture.
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
    """
    return Endpoint(
        path="/api/v1/track", method=HttpMethod.GET, summary="Track shipment"
    )


@pytest.fixture
def sample_carrier():
    """
    Sample carrier format fixture.
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
    """
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir
