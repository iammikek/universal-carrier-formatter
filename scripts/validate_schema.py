#!/usr/bin/env python3
"""
Validate schema.json against the Universal Carrier Format contract (imp-23).

With no arguments: quick self-test (import models, create minimal UCF, load example).
With a path: load that schema.json and validate required top-level keys and the
schema object against UCF — no LLM call. Useful for CI or hand-crafted schemas.

    uv run python scripts/validate_schema.py
    uv run python scripts/validate_schema.py output/schema.json

In Docker:
    docker compose exec app python scripts/validate_schema.py path/to/schema.json
"""

import argparse
import json
import sys
from pathlib import Path

# Add project root to path
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

try:
    from src.core.config import (
        KEY_CONSTRAINTS,
        KEY_EDGE_CASES,
        KEY_FIELD_MAPPINGS,
        KEY_GENERATOR_VERSION,
        KEY_SCHEMA,
        KEY_SCHEMA_VERSION,
    )
    from src.core.schema import Endpoint, HttpMethod, UniversalCarrierFormat
    from src.core.validator import CarrierValidator
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("\nPlease install dependencies (from pyproject.toml):")
    print('  uv sync --extra dev   # or: pip install -e ".[dev]"')
    sys.exit(1)

REQUIRED_TOP_LEVEL = {
    KEY_SCHEMA,
    KEY_FIELD_MAPPINGS,
    KEY_CONSTRAINTS,
    KEY_EDGE_CASES,
    KEY_SCHEMA_VERSION,
    KEY_GENERATOR_VERSION,
}


def _self_test() -> int:
    """Quick self-test: import models, create minimal UCF, optional example load."""
    print("✅ Successfully imported all models")

    carrier = UniversalCarrierFormat(
        name="Test Carrier",
        base_url="https://api.test.com",
        endpoints=[
            Endpoint(
                path="/api/track",
                method=HttpMethod.GET,
                summary="Track shipment",
            )
        ],
    )
    print("✅ Successfully created UniversalCarrierFormat")
    print(f"   Carrier: {carrier.name}")
    print(f"   Base URL: {carrier.base_url}")
    print(f"   Endpoints: {len(carrier.endpoints)}")

    _ = carrier.model_dump()
    print("✅ Successfully serialized to dict")

    example_file = _ROOT / "examples" / "expected_output.json"
    if example_file.exists():
        with open(example_file, encoding="utf-8") as f:
            data = json.load(f)
        schema_data = data.get(KEY_SCHEMA, data)
        UniversalCarrierFormat.model_validate(schema_data)
        print(f"✅ Successfully validated example file: {example_file.name}")
    else:
        print("⚠️  Example file not found (this is okay)")

    print("\n🎉 All validations passed!")
    return 0


def _validate_schema_file(path: Path) -> int:
    """Load schema.json and validate against contract (required keys + UCF schema)."""
    if not path.exists():
        print(f"❌ File not found: {path}", file=sys.stderr)
        return 1

    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}", file=sys.stderr)
        return 1

    for key in REQUIRED_TOP_LEVEL:
        if key not in data:
            print(f"❌ Missing required top-level key: {key}", file=sys.stderr)
            return 1

    validator = CarrierValidator()
    try:
        validated = validator.validate(data[KEY_SCHEMA])
        print(f"✅ Valid: {path}")
        print(f"   Carrier: {validated.name}")
        print(f"   Endpoints: {len(validated.endpoints)}")
        return 0
    except Exception as e:
        print(f"❌ Validation failed: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc(file=sys.stderr)
        return 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate schema.json against Universal Carrier Format (or run self-test)."
    )
    parser.add_argument(
        "schema_path",
        type=Path,
        nargs="?",
        default=None,
        help="Path to schema.json to validate; if omitted, run self-test only.",
    )
    args = parser.parse_args()

    if args.schema_path is None:
        return _self_test()
    return _validate_schema_file(args.schema_path.resolve())


if __name__ == "__main__":
    sys.exit(main())
