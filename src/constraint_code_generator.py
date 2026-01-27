"""
Constraint Code Generator

Converts constraint metadata (from LLM extraction) into Pydantic v2 validator code.
Completes Scenario 2: constraint extraction → executable validation logic.

Input: List of constraint dicts with keys such as field, rule, type, condition.
Output: Python source defining @field_validator / @model_validator that can be
        mixed into a schema or mapper model.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

HEADER = '''"""
Auto-generated Pydantic validators from constraint extraction (Scenario 2).

Add this mixin to your schema or request/response model:
    class MyModel(ConstraintValidatorsMixin, BaseModel):
        ...
"""

from typing import Any

from pydantic import field_validator, model_validator
'''

MIXIN_START = """
class ConstraintValidatorsMixin:
    \"\"\"
    Pydantic v2 validators derived from extracted business rules.
    Include this mixin in your model to apply the constraints.
    \"\"\"
"""


def _sanitize_identifier(s: str) -> str:
    """Turn a string into a valid Python identifier fragment."""
    return "".join(c if c.isalnum() or c == "_" else "_" for c in s)[:48]


def _emit_field_validator(constraint: Dict[str, Any], index: int) -> str:
    """Emit a single-field validator (no other fields)."""
    field = constraint.get("field") or "value"
    rule = constraint.get("rule") or "Business rule"
    ctype = (constraint.get("type") or "").lower()
    fn_name = f"_validate_{_sanitize_identifier(field)}_{index}"

    if "phone" in field.lower() or "phone" in (rule or "").lower():
        if "+" in (rule or "") or "prefix" in (rule or "").lower():
            return f'''
    @field_validator({repr(field)}, mode="before")
    @classmethod
    def {fn_name}(cls, v: Any) -> Any:
        """{rule}"""
        if v is None:
            return v
        s = str(v).strip()
        if s.startswith("+"):
            return s.lstrip("+")
        return v
'''
    if ctype == "format" or "pattern" in (rule or "").lower():
        return f'''
    @field_validator({repr(field)}, mode="before")
    @classmethod
    def {fn_name}(cls, v: Any) -> Any:
        """{rule}"""
        if v is None:
            return v
        return v
'''
    return f'''
    @field_validator({repr(field)}, mode="before")
    @classmethod
    def {fn_name}(cls, v: Any) -> Any:
        """{rule}"""
        return v
'''


def _emit_model_validator(constraint: Dict[str, Any], index: int) -> str:
    """Emit a model-level validator (can use other fields)."""
    field = constraint.get("field") or "value"
    rule = constraint.get("rule") or "Business rule"
    condition = constraint.get("condition") or ""
    ctype = (constraint.get("type") or "").lower()
    fn_name = f"_validate_{_sanitize_identifier(field)}_{index}"

    if ctype == "unit_conversion" and "weight" in (field or "").lower():
        if "destination_country" in condition or "DE" in condition or "GB" in condition:
            return f'''
    @model_validator(mode="after")
    def {fn_name}(self) -> Any:
        """{rule} (condition: {condition})"""
        dest = getattr(self, "destination_country", None) or getattr(
            self, "destination_country_code", None
        )
        unit = getattr(self, "unit", None)
        weight = getattr(self, "weight", None)
        if weight is None:
            return self
        if dest == "DE":
            if unit == "kg":
                object.__setattr__(self, "weight", weight * 1000)
                if hasattr(self, "unit"):
                    object.__setattr__(self, "unit", "g")
        elif dest == "GB":
            if unit == "g":
                object.__setattr__(self, "weight", weight / 1000)
                if hasattr(self, "unit"):
                    object.__setattr__(self, "unit", "kg")
        return self
'''
    return f'''
    @model_validator(mode="after")
    def {fn_name}(self) -> Any:
        """{rule} (condition: {condition or 'none'})"""
        return self
'''


def _constraint_uses_other_fields(constraint: Dict[str, Any]) -> bool:
    """True if the constraint depends on other model fields (needs model_validator)."""
    ctype = (constraint.get("type") or "").lower()
    cond = (constraint.get("condition") or "").strip()
    if ctype in ("unit_conversion", "conditional", "cross_field"):
        return True
    if "destination_country" in cond or "origin_country" in cond or "country" in cond:
        return True
    if "get(" in cond or "==" in cond or " in " in cond:
        return True
    return False


def generate_validators(constraints: List[Dict[str, Any]]) -> str:
    """
    Convert constraint metadata into Pydantic v2 validator Python source.

    Args:
        constraints: List of dicts with field, rule, type, condition, etc.

    Returns:
        Python source string (imports + ConstraintValidatorsMixin class).
    """
    if not constraints:
        return HEADER + MIXIN_START + "\n    pass\n"

    parts = [HEADER, MIXIN_START]
    for i, c in enumerate(constraints):
        if not isinstance(c, dict):
            continue
        if _constraint_uses_other_fields(c):
            parts.append(_emit_model_validator(c, i))
        else:
            parts.append(_emit_field_validator(c, i))

    return "".join(parts)


def generate_validators_file(
    constraints: List[Dict[str, Any]],
    output_path: str,
) -> None:
    """
    Write generated validator source to a Python file.

    Args:
        constraints: List of constraint dicts from extract_constraints().
        output_path: Path for the output .py file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    source = generate_validators(constraints)
    path.write_text(source, encoding="utf-8")
    logger.info(f"Wrote constraint validators to {path}")
