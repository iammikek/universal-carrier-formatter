"""
Example test file to demonstrate testing structure

Laravel Equivalent: tests/Feature/BasicTest.php or tests/Unit/BasicTest.php

Key differences from Laravel/PHPUnit:
- Use 'assert' instead of '$this->assert*()'
- Use 'pytest.raises()' instead of 'expectException()'
- Test methods start with 'test_' (or use @pytest.mark)
- Can use classes OR standalone functions
"""

import pytest
from src import __version__


@pytest.mark.unit
class TestBasicFunctionality:
    """
    Test class (like Laravel's TestCase class)
    
    In Laravel:
    class BasicTest extends TestCase {
        public function test_version_exists() { ... }
    }
    """
    
    def test_version_exists(self):
        """
        Test that version is defined.
        
        Laravel equivalent:
        public function test_version_exists()
        {
            $this->assertNotNull(__VERSION__);
            $this->assertIsString(__VERSION__);
        }
        """
        assert __version__ is not None
        assert isinstance(__version__, str)
    
    def test_version_format(self):
        """
        Test version format.
        
        Laravel equivalent:
        public function test_version_format()
        {
            $parts = explode('.', __VERSION__);
            $this->assertCount(3, $parts);
            $this->assertTrue(all(is_numeric($part) for $part in $parts));
        }
        """
        # Version should be in format x.y.z
        parts = __version__.split('.')
        assert len(parts) == 3
        assert all(part.isdigit() for part in parts)


# Standalone test function (also valid in pytest)
# In Laravel, you'd typically put this in a class, but pytest allows both
def test_simple_assertion():
    """
    Simple test function.
    
    Laravel equivalent would be:
    public function test_simple_assertion()
    {
        $this->assertEquals(2, 1 + 1);
    }
    """
    assert 1 + 1 == 2
