"""
Canonical physical units for logistics.

Data integrity starts with physical constants: "10" means nothing without a unit.
All weight and dimension values are normalized to canonical units on ingestion:
- Weight → grams (int)
- Length → centimetres (int)

Use these types in universal payloads and mappers so downstream code never sees
bare floats or ambiguous units. Normalize at the boundary (API/mapper input), store
canonically.
"""

from typing import Annotated, Any, Union

from pydantic import BeforeValidator

# --- Weight: canonical unit = grams (int) ---

_GRAMS_PER_KG = 1000
_GRAMS_PER_LB = 453.59237


def _normalize_weight_to_grams(v: Any) -> int:
    """Normalize weight input to grams (int). Accepts int, float, or dict with value+unit."""
    if isinstance(v, int):
        if v < 0:
            raise ValueError("weight_grams must be non-negative")
        return v
    if isinstance(v, float):
        if v < 0:
            raise ValueError("weight must be non-negative")
        return int(round(v))  # assume already in grams if float (backward compat)
    if isinstance(v, dict):
        val = v.get("value") if "value" in v else v.get("weight")
        if val is None:
            raise ValueError("weight dict must have 'value' or 'weight'")
        unit = (v.get("unit") or "g").lower().strip()
        num = float(val)
        if num < 0:
            raise ValueError("weight value must be non-negative")
        if unit in ("g", "grams", "gram"):
            return int(round(num))
        if unit in ("kg", "kilograms", "kilogram"):
            return int(round(num * _GRAMS_PER_KG))
        if unit in ("lb", "lbs", "pounds", "pound"):
            return int(round(num * _GRAMS_PER_LB))
        raise ValueError(f"Unknown weight unit: {unit!r}. Use g, kg, or lb.")
    raise ValueError(
        "weight must be int (grams), float (grams), or dict with 'value' and 'unit' (g/kg/lb)"
    )


# Use in Pydantic models: weight_grams: WeightGrams
WeightGrams = Annotated[int, BeforeValidator(_normalize_weight_to_grams)]


# --- Length: canonical unit = centimetres (int) ---

_CM_PER_M = 100
_CM_PER_IN = 2.54
_CM_PER_FT = 30.48


def _normalize_length_to_cm(v: Any) -> int:
    """Normalize length input to centimetres (int). Accepts int, float, or dict with value+unit."""
    if isinstance(v, int):
        if v < 0:
            raise ValueError("length_cm must be non-negative")
        return v
    if isinstance(v, float):
        if v < 0:
            raise ValueError("length must be non-negative")
        return int(round(v))  # assume already cm if float
    if isinstance(v, dict):
        val = v.get("value") if "value" in v else v.get("length")
        if val is None:
            raise ValueError("length dict must have 'value' or 'length'")
        unit = (v.get("unit") or "cm").lower().strip()
        num = float(val)
        if num < 0:
            raise ValueError("length value must be non-negative")
        if unit in ("cm", "centimetres", "centimeters", "centimetre", "centimeter"):
            return int(round(num))
        if unit in ("m", "metres", "meters", "metre", "meter"):
            return int(round(num * _CM_PER_M))
        if unit in ("in", "inch", "inches"):
            return int(round(num * _CM_PER_IN))
        if unit in ("ft", "feet", "foot"):
            return int(round(num * _CM_PER_FT))
        raise ValueError(f"Unknown length unit: {unit!r}. Use cm, m, in, or ft.")
    raise ValueError(
        "length must be int (cm), float (cm), or dict with 'value' and 'unit' (cm/m/in/ft)"
    )


# Use in Pydantic models: length_cm: LengthCm
LengthCm = Annotated[int, BeforeValidator(_normalize_length_to_cm)]


def parse_weight_to_grams(value: Union[int, float], unit: str = "g") -> int:
    """
    Parse a weight value and unit into grams (int). Use when mapping carrier payloads.

    Args:
        value: Numeric weight.
        unit: One of 'g', 'kg', 'lb'.

    Returns:
        Weight in grams (int).
    """
    return _normalize_weight_to_grams({"value": value, "unit": unit})


def parse_length_to_cm(value: Union[int, float], unit: str = "cm") -> int:
    """
    Parse a length value and unit into centimetres (int). Use when mapping carrier payloads.

    Args:
        value: Numeric length.
        unit: One of 'cm', 'm', 'in', 'ft'.

    Returns:
        Length in cm (int).
    """
    return _normalize_length_to_cm({"value": value, "unit": unit})
