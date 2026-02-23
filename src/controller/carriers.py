"""
Carriers domain: list registered carriers and serve carrier OpenAPI YAML.

Encapsulates CarrierRegistry listing and schema file + OpenAPI generation.
"""

import io
import json
from pathlib import Path
from typing import List

import yaml
from fastapi import HTTPException

from ..core.config import KEY_SCHEMA
from ..core.schema import UniversalCarrierFormat
from ..mappers import CarrierRegistry
from ..openapi_generator import generate_openapi


class CarrierController:
    """Controller for carrier catalog and schema OpenAPI docs."""

    def list_carriers(self) -> List[str]:
        """List carrier slugs available for conversion."""
        return CarrierRegistry.list_names()

    def carrier_openapi_yaml(self, name: str) -> str:
        """Return OpenAPI YAML for the given carrier schema."""
        if name == "expected":
            path = Path(__file__).parent.parent.parent / "examples" / "expected_output.json"
        else:
            path = Path(__file__).parent.parent.parent / "output" / f"{name}_schema.json"
        if not path.exists():
            raise HTTPException(404, f"Schema not found for carrier: {name}")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        schema_data = data.get(KEY_SCHEMA, data)
        schema = UniversalCarrierFormat.model_validate(schema_data)
        spec = generate_openapi(schema)
        buf = io.StringIO()
        yaml.dump(spec, buf, default_flow_style=False, allow_unicode=True, sort_keys=False)
        return buf.getvalue()
