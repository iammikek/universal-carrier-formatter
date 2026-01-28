"""
Schema.json contract: versioning and stability guarantees.

The extraction pipeline writes schema.json; mappers/validators are generated from it.
This module defines the public contract version and helpers for migration and validation.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

# Semantic version of the schema.json *format* (top-level keys and semantics).
# Bump when the contract changes in a breaking way (e.g. new required field, renamed key).
SCHEMA_VERSION = "1.0.0"


def get_generator_version() -> str:
    """
    Return the version of the tool that generated the schema (package version or fallback).
    Used as generator_version in schema.json for traceability.
    """
    try:
        from importlib.metadata import version

        return version("universal-carrier-formatter")
    except Exception:
        pass
    return "0.1.0"


class SchemaContractOutput(BaseModel):
    """
    Formal model for the schema.json file (extraction pipeline output).

    Used to generate the JSON Schema meta-schema and to validate the output.
    """

    model_config = {"populate_by_name": True}
    schema_version: str = Field(
        ...,
        description="Semantic version of this schema format (contract version).",
    )
    generator_version: str = Field(
        ...,
        description="Version of the tool that generated this file (e.g. package version or git SHA).",
    )
    schema_: Dict[str, Any] = Field(
        ...,
        alias="schema",
        description="Universal Carrier Format schema (name, base_url, endpoints, etc.).",
    )
    field_mappings: List[Any] = Field(
        default_factory=list,
        description="Field name mappings from carrier to universal.",
    )
    constraints: List[Any] = Field(
        default_factory=list,
        description="Business rules and constraints.",
    )
    edge_cases: List[Any] = Field(
        default_factory=list,
        description="Route-specific edge cases.",
    )


def check_schema_version(data: Dict[str, Any]) -> Optional[tuple[str, str]]:
    """
    Compare schema_version in data to current SCHEMA_VERSION.

    Returns:
        (file_version, current_version) if they differ (migration may be required), else None.
    """
    file_version = (data or {}).get("schema_version")
    if file_version is None:
        return None  # Legacy file without version; don't force migration
    file_version = str(file_version).strip()
    current = SCHEMA_VERSION.strip()
    if file_version != current:
        return (file_version, current)
    return None


def check_schema_version_and_warn(
    data: Dict[str, Any],
    *,
    source: str = "schema.json",
    log: Optional[logging.Logger] = None,
) -> None:
    """
    If schema_version in data differs from current, log a migration warning.

    Use after loading a schema.json file (e.g. in mapper_generator_cli).
    """
    mismatch = check_schema_version(data)
    if mismatch is None:
        return
    file_ver, current_ver = mismatch
    msg = (
        f"Schema version mismatch: file has schema_version={file_ver!r}, "
        f"current contract is {current_ver!r}. Migration may be required (schema v{file_ver} -> v{current_ver})."
    )
    if log:
        log.warning(msg)
    else:
        import sys

        print(msg, file=sys.stderr)


def export_meta_schema_json() -> str:
    """
    Return the JSON Schema (meta-schema) for schema.json as a JSON string.

    Use to validate generated schema.json files formally (e.g. jsonschema.validate).
    """
    return json.dumps(SchemaContractOutput.model_json_schema(by_alias=True), indent=2)
