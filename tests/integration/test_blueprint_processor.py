"""
Integration tests for Blueprint Processor.

Laravel Equivalent: tests/Integration/BlueprintProcessorTest.php
"""

import tempfile
from pathlib import Path

import pytest
import yaml

from src.blueprints.processor import BlueprintProcessor
from src.core.schema import UniversalCarrierFormat


@pytest.mark.integration
class TestBlueprintProcessor:
    """Integration tests for BlueprintProcessor."""

    @pytest.fixture
    def processor(self):
        """Create processor instance."""
        return BlueprintProcessor()

    @pytest.fixture
    def valid_blueprint_file(self, tmp_path):
        """Create a valid blueprint file for testing."""
        blueprint_data = {
            "carrier": {
                "name": "Test Carrier",
                "base_url": "https://api.test.com",
                "version": "v1",
            },
            "endpoints": [
                {
                    "path": "/test",
                    "method": "GET",
                    "summary": "Test endpoint",
                }
            ],
        }

        blueprint_file = tmp_path / "test_blueprint.yaml"
        with open(blueprint_file, "w") as f:
            yaml.dump(blueprint_data, f)

        return blueprint_file

    def test_process_valid_blueprint(self, processor, valid_blueprint_file):
        """Test processing a valid blueprint file."""
        result = processor.process(valid_blueprint_file)

        assert isinstance(result, UniversalCarrierFormat)
        assert result.name == "Test Carrier"
        assert len(result.endpoints) == 1

    def test_process_file_not_found(self, processor):
        """Test processing non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            processor.process("nonexistent.yaml")

    def test_process_invalid_blueprint(self, processor, tmp_path):
        """Test processing invalid blueprint raises ValueError."""
        invalid_blueprint = {
            "carrier": {"name": "Test"},  # Missing base_url and endpoints
        }

        invalid_file = tmp_path / "invalid.yaml"
        with open(invalid_file, "w") as f:
            yaml.dump(invalid_blueprint, f)

        with pytest.raises(ValueError, match="validation failed"):
            processor.process(invalid_file)

    def test_process_from_string(self, processor):
        """Test processing blueprint from YAML string."""
        yaml_content = """
carrier:
  name: "String Carrier"
  base_url: "https://api.string.com"
endpoints:
  - path: "/test"
    method: "GET"
    summary: "Test endpoint"
"""
        result = processor.process_from_string(yaml_content)

        assert isinstance(result, UniversalCarrierFormat)
        assert result.name == "String Carrier"

    def test_process_complete_blueprint(self, processor, tmp_path):
        """Test processing a complete blueprint with all fields."""
        blueprint_data = {
            "carrier": {
                "name": "Complete Carrier",
                "base_url": "https://api.complete.com",
                "version": "v2",
                "description": "Complete test carrier",
            },
            "authentication": {
                "type": "api_key",
                "parameter_name": "X-API-Key",
            },
            "endpoints": [
                {
                    "path": "/track",
                    "method": "GET",
                    "summary": "Track shipment",
                    "authentication_required": True,
                    "request": {
                        "parameters": [
                            {
                                "name": "tracking_id",
                                "type": "string",
                                "location": "query",
                                "required": True,
                            }
                        ]
                    },
                    "responses": [{"status_code": 200, "description": "Success"}],
                }
            ],
            "rate_limits": [{"requests": 100, "period": "1 minute"}],
            "documentation_url": "https://docs.complete.com",
        }

        blueprint_file = tmp_path / "complete.yaml"
        with open(blueprint_file, "w") as f:
            yaml.dump(blueprint_data, f)

        result = processor.process(blueprint_file)

        assert result.name == "Complete Carrier"
        assert result.version == "v2"
        assert len(result.authentication) == 1
        assert len(result.endpoints) == 1
        assert len(result.rate_limits) == 1
        assert result.documentation_url is not None
