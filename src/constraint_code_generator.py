"""
Constraint Code Generator

Converts constraint metadata (from LLM extraction) into Pydantic v2 validator code.
Completes Scenario 2: constraint extraction → executable validation logic.

Input: List of constraint dicts with keys such as field, rule, type, condition.
Output: Python source defining @field_validator / @model_validator that can be
        mixed into a schema or mapper model.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

HEADER = '''"""
Auto-generated Pydantic validators from constraint extraction (Scenario 2).

How to use:
  1. Import this mixin and add it to your Pydantic model (mixin first so its validators run):
       from output.dhl_express_api_schema_validators import ConstraintValidatorsMixin
       from pydantic import BaseModel

       class MyRequest(ConstraintValidatorsMixin, BaseModel):
           ShipmentInfo_DHLCustomsInvoiceLanguageCode: str | None = None
           ...

  2. Your model field names must match the validator names. Validators use the exact
     field name from the docs (e.g. ShipmentInfo/DHLCustomsInvoiceLanguageCode becomes
     a validator for that key). Use the same name or alias in your model.

  3. Many validators are currently documentation-only (they return the value unchanged).
     Real validation is emitted when constraints include allowed_values, max_length,
     min_length, or pattern. Edit this file to add logic, or re-run extraction with
     constraints that have those keys.
"""

import re
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


def _parse_possible_values_from_rule(rule: str) -> List[str] | None:
    """
    Parse 'possible values: X, Y, Z' or 'values: X, Y, Z' from rule text.
    Returns list of stripped tokens, or None if not found.
    """
    if not rule or not isinstance(rule, str):
        return None
    rule_lower = rule.lower()
    for prefix in (
        "possible values:",
        "values:",
        "include ",
        "supported codes include ",
        "supported values include ",
    ):
        if prefix in rule_lower:
            idx = rule_lower.find(prefix)
            rest = rule[idx + len(prefix) :].strip()
            # Take up to next sentence or end
            for sep in (".", ";", "\n"):
                if sep in rest:
                    rest = rest.split(sep)[0].strip()
            # Split by comma and clean
            tokens = [t.strip() for t in rest.split(",") if t.strip()]
            if len(tokens) >= 2:
                return tokens
            if len(tokens) == 1 and " " in tokens[0]:
                # e.g. "SI (KG, CM)" -> take "SI"
                tokens = [tokens[0].split()[0]]
                return tokens if tokens else None
            return tokens if tokens else None
    return None


def _emit_field_validator(constraint: Dict[str, Any], index: int) -> str:
    """Emit a single-field validator (no other fields)."""
    field = constraint.get("field") or "value"
    rule = constraint.get("rule") or "Business rule"
    ctype = (constraint.get("type") or "").lower()
    fn_name = f"_validate_{_sanitize_identifier(field)}_{index}"
    allowed = constraint.get("allowed_values") or constraint.get("enum_values")
    max_len = constraint.get("max_length")
    min_len = constraint.get("min_length")
    pattern = constraint.get("pattern")

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
    # Structured constraint or "possible values: X, Y, Z" in rule: emit real validation
    if allowed is None or not isinstance(allowed, list) or len(allowed) == 0:
        allowed = _parse_possible_values_from_rule(rule)
    if allowed is not None and len(allowed) > 0:
        allowed_str = repr([str(x) for x in allowed])
        return f'''
    @field_validator({repr(field)}, mode="before")
    @classmethod
    def {fn_name}(cls, v: Any) -> Any:
        """{rule}"""
        if v is None:
            return v
        s = str(v).strip() if v != "" else ""
        if s == "":
            return v
        allowed = {allowed_str}
        if v not in allowed and s not in allowed:
            raise ValueError(f"{repr(field)} must be one of {{allowed}}; got {{v!r}}")
        return v
'''
    if pattern is not None and isinstance(pattern, str) and pattern:
        return f'''
    @field_validator({repr(field)}, mode="before")
    @classmethod
    def {fn_name}(cls, v: Any) -> Any:
        """{rule}"""
        if v is None:
            return v
        if not re.fullmatch({repr(pattern)}, str(v)):
            raise ValueError(f"{{field!r}} must match pattern {{repr(pattern)}}; got {{v!r}}")
        return v
'''
    if max_len is not None or min_len is not None:
        max_c = int(max_len) if max_len is not None else None
        min_c = int(min_len) if min_len is not None else None
        checks = []
        if min_c is not None:
            checks.append(f"len(s) < {min_c}")
        if max_c is not None:
            checks.append(f"len(s) > {max_c}")
        cond = " or ".join(checks)
        if min_c is not None and max_c is not None:
            msg_suffix = f"between {min_c} and {max_c}"
        elif min_c is not None:
            msg_suffix = f">= {min_c}"
        else:
            msg_suffix = f"<= {max_c}"
        return f'''
    @field_validator({repr(field)}, mode="before")
    @classmethod
    def {fn_name}(cls, v: Any) -> Any:
        """{rule}"""
        if v is None:
            return v
        s = str(v)
        if {cond}:
            raise ValueError(f"{repr(field)} length must be {msg_suffix}; got len={{len(s)}}")
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
