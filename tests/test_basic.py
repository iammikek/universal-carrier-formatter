"""
Example test file to demonstrate testing structure.

- Use assert for assertions
- Use pytest.raises() for expected exceptions
- Test methods start with 'test_' (or use @pytest.mark)
- Can use classes OR standalone functions
"""

import pytest

from src import __version__


@pytest.mark.unit
class TestBasicFunctionality:
    """Test class for basic functionality."""

    def test_version_exists(self):
        """Test that version is defined."""
        assert __version__ is not None
        assert isinstance(__version__, str)

    def test_version_format(self):
        """Test version format (x.y.z)."""
        # Version should be in format x.y.z
        parts = __version__.split(".")
        assert len(parts) == 3
        assert all(part.isdigit() for part in parts)


# Standalone test function (pytest allows both classes and functions)
def test_simple_assertion():
    """Simple test function."""
    assert 1 + 1 == 2
