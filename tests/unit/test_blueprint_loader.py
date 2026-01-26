"""
Tests for Blueprint Loader.

Laravel Equivalent: tests/Unit/BlueprintLoaderTest.php
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from src.blueprints.loader import BlueprintLoader


@pytest.mark.unit
class TestBlueprintLoader:
    """Test BlueprintLoader."""

    @pytest.fixture
    def loader(self):
        """Create loader instance."""
        return BlueprintLoader()

    def test_load_valid_blueprint(self, loader, tmp_path):
        """Test loading a valid blueprint file."""
        blueprint_data = {
            "carrier": {"name": "Test Carrier", "base_url": "https://api.test.com"},
            "endpoints": [
                {"path": "/test", "method": "GET", "summary": "Test endpoint"}
            ],
        }

        blueprint_file = tmp_path / "test_blueprint.yaml"
        with open(blueprint_file, "w") as f:
            yaml.dump(blueprint_data, f)

        result = loader.load(blueprint_file)

        assert result == blueprint_data
        assert result["carrier"]["name"] == "Test Carrier"

    def test_load_relative_path(self, loader, tmp_path, monkeypatch):
        """Test loading blueprint with relative path."""
        blueprint_data = {
            "carrier": {"name": "Test", "base_url": "https://api.test.com"},
            "endpoints": [{"path": "/test", "method": "GET", "summary": "Test"}],
        }

        # Create blueprints directory
        blueprints_dir = tmp_path / "blueprints"
        blueprints_dir.mkdir()
        blueprint_file = blueprints_dir / "test.yaml"
        with open(blueprint_file, "w") as f:
            yaml.dump(blueprint_data, f)

        # Change to tmp_path
        monkeypatch.chdir(tmp_path)

        result = loader.load("test.yaml")

        assert result["carrier"]["name"] == "Test"

    def test_load_file_not_found(self, loader):
        """Test loading non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            loader.load("nonexistent.yaml")

    def test_load_empty_file(self, loader, tmp_path):
        """Test loading empty file raises ValueError."""
        empty_file = tmp_path / "empty.yaml"
        empty_file.write_text("")

        with pytest.raises(ValueError, match="empty"):
            loader.load(empty_file)

    def test_load_invalid_yaml(self, loader, tmp_path):
        """Test loading invalid YAML raises ValueError."""
        invalid_file = tmp_path / "invalid.yaml"
        invalid_file.write_text("invalid: yaml: content: [unclosed")

        with pytest.raises(ValueError, match="Invalid YAML"):
            loader.load(invalid_file)

    def test_load_from_string(self, loader):
        """Test loading blueprint from YAML string."""
        yaml_content = """
carrier:
  name: "Test Carrier"
  base_url: "https://api.test.com"
endpoints:
  - path: "/test"
    method: "GET"
    summary: "Test endpoint"
"""
        result = loader.load_from_string(yaml_content)

        assert result["carrier"]["name"] == "Test Carrier"
        assert len(result["endpoints"]) == 1

    def test_load_from_string_empty(self, loader):
        """Test loading empty string raises ValueError."""
        with pytest.raises(ValueError, match="empty"):
            loader.load_from_string("")

    def test_load_from_string_invalid(self, loader):
        """Test loading invalid YAML string raises ValueError."""
        with pytest.raises(ValueError, match="Invalid YAML"):
            loader.load_from_string("invalid: yaml: [unclosed")
