"""
Tests for canonical physical units (core.units).

Ensures weight and length normalize to grams and cm on ingestion;
no bare floats without units.
"""

import pytest
from pydantic import BaseModel

from src.core.units import (
    LengthCm,
    WeightGrams,
    parse_length_to_cm,
    parse_weight_to_grams,
)


@pytest.mark.unit
class TestWeightGrams:
    """Weight normalization to grams (int)."""

    def test_int_as_grams(self):
        assert parse_weight_to_grams(1000, "g") == 1000
        assert parse_weight_to_grams(0, "g") == 0

    def test_kg_to_grams(self):
        assert parse_weight_to_grams(1, "kg") == 1000
        assert parse_weight_to_grams(10, "kg") == 10_000
        assert parse_weight_to_grams(0.5, "kg") == 500

    def test_lb_to_grams(self):
        assert parse_weight_to_grams(1, "lb") == 454  # 453.59237 rounded
        assert parse_weight_to_grams(2.2, "lb") == 998  # ~1 kg

    def test_pydantic_weight_grams_int(self):
        class M(BaseModel):
            weight_grams: WeightGrams

        m = M(weight_grams=5000)
        assert m.weight_grams == 5000

    def test_pydantic_weight_grams_from_dict(self):
        class M(BaseModel):
            weight_grams: WeightGrams

        m = M(weight_grams={"value": 2, "unit": "kg"})
        assert m.weight_grams == 2000

    def test_pydantic_weight_grams_from_dict_lb(self):
        class M(BaseModel):
            weight_grams: WeightGrams

        m = M(weight_grams={"value": 1, "unit": "lb"})
        assert m.weight_grams == 454

    def test_negative_weight_rejected(self):
        with pytest.raises(ValueError, match="non-negative"):
            parse_weight_to_grams(-1, "g")
        with pytest.raises(ValueError, match="non-negative"):
            parse_weight_to_grams(-10, "kg")

    def test_unknown_unit_rejected(self):
        with pytest.raises(ValueError, match="Unknown weight unit"):
            parse_weight_to_grams(10, "oz")


@pytest.mark.unit
class TestLengthCm:
    """Length normalization to centimetres (int)."""

    def test_int_as_cm(self):
        assert parse_length_to_cm(100, "cm") == 100
        assert parse_length_to_cm(0, "cm") == 0

    def test_m_to_cm(self):
        assert parse_length_to_cm(1, "m") == 100
        assert parse_length_to_cm(0.5, "m") == 50

    def test_in_to_cm(self):
        assert parse_length_to_cm(1, "in") == 3  # 2.54 rounded
        assert parse_length_to_cm(10, "in") == 25

    def test_ft_to_cm(self):
        assert parse_length_to_cm(1, "ft") == 30  # 30.48 rounded

    def test_pydantic_length_cm_int(self):
        class M(BaseModel):
            length_cm: LengthCm

        m = M(length_cm=50)
        assert m.length_cm == 50

    def test_pydantic_length_cm_from_dict(self):
        class M(BaseModel):
            length_cm: LengthCm

        m = M(length_cm={"value": 1, "unit": "m"})
        assert m.length_cm == 100

    def test_negative_length_rejected(self):
        with pytest.raises(ValueError, match="non-negative"):
            parse_length_to_cm(-1, "cm")

    def test_unknown_unit_rejected(self):
        with pytest.raises(ValueError, match="Unknown length unit"):
            parse_length_to_cm(10, "yd")
