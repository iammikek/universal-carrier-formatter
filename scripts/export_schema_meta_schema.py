#!/usr/bin/env python3
"""
Export the JSON Schema (meta-schema) for schema.json to docs/schema_contract_meta_schema.json.

Use this to validate generated schema.json files formally, e.g.:
  jsonschema -i output/schema.json docs/schema_contract_meta_schema.json

Run from repo root:
  python scripts/export_schema_meta_schema.py
  # or: python -m scripts.export_schema_meta_schema
"""

import sys
from pathlib import Path

# Add repo root so src is importable
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root))

from src.core.contract import export_meta_schema_json  # noqa: E402

OUTPUT_PATH = repo_root / "docs" / "schema_contract_meta_schema.json"


def main() -> None:
    json_schema = export_meta_schema_json()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json_schema, encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
