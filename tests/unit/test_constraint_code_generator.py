"""
Tests for Constraint Code Generator (Scenario 2).

Validates that constraint metadata is turned into valid Pydantic v2 validator code.
"""

import pytest

from src.constraint_code_generator import generate_validators, generate_validators_file


@pytest.mark.unit
class TestConstraintCodeGenerator:
    """Test constraint → Pydantic validator code generation."""

    def test_generate_validators_empty(self):
        """Empty constraints produce a mixin with no logic."""
        out = generate_validators([])
        assert "ConstraintValidatorsMixin" in out
        assert "field_validator" in out or "pass" in out
        assert "from pydantic import" in out

    def test_generate_validators_unit_conversion(self):
        """Unit-conversion constraints produce model_validator with weight logic."""
        constraints = [
            {
                "field": "weight",
                "rule": "Must be in grams if shipping to Germany, kilograms for UK",
                "type": "unit_conversion",
                "condition": "destination_country == 'DE'",
            }
        ]
        out = generate_validators(constraints)
        assert "model_validator" in out
        assert "weight" in out
        assert "destination_country" in out
        assert "DE" in out
        assert "GB" in out
        assert "ConstraintValidatorsMixin" in out

    def test_generate_validators_phone_format(self):
        """Phone/no-plus-prefix rules produce field_validator."""
        constraints = [
            {
                "field": "phone_number",
                "rule": "Telephone numbers must not include the + prefix",
                "type": "format",
            }
        ]
        out = generate_validators(constraints)
        assert "field_validator" in out
        assert "phone_number" in out
        assert "lstrip" in out or "+" in out

    def test_generate_validators_generic_field(self):
        """Generic field-only constraints produce field_validator."""
        constraints = [
            {
                "field": "postcode",
                "rule": "Must match format for region",
                "type": "format",
            }
        ]
        out = generate_validators(constraints)
        assert "field_validator" in out
        assert "postcode" in out

    def test_generate_validators_possible_values_from_rule(self):
        """Optional; possible values: X, Y, Z in rule emits validation when set."""
        constraints = [
            {
                "field": "ShipmentReferences_ShipmentReferenc",
                "rule": "Optional; possible values: AAO, CU, FF, FN, IBC, LLR, OBC, PRN",
                "type": "enum",
            }
        ]
        out = generate_validators(constraints)
        assert "field_validator" in out
        assert "AAO" in out and "CU" in out
        assert "not in allowed" in out
        assert "raise ValueError" in out
        assert 's == ""' in out or "s == ''" in out
        assert "return v" in out

    def test_generate_validators_file_writes(self, tmp_path):
        """generate_validators_file writes a .py file."""
        constraints = [
            {
                "field": "weight",
                "rule": "Grams for DE",
                "type": "unit_conversion",
                "condition": "destination_country == 'DE'",
            }
        ]
        path = tmp_path / "validators.py"
        generate_validators_file(constraints, str(path))
        assert path.exists()
        content = path.read_text()
        assert "ConstraintValidatorsMixin" in content
        assert "weight" in content
