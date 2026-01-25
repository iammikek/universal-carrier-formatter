#!/usr/bin/env python3
"""
Quick validation script to test schema models.

Run this after installing dependencies:
    pip install -r requirements-dev.txt
    python scripts/validate_schema.py

Or in Docker:
    docker-compose exec app python scripts/validate_schema.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from src.models import (
        UniversalCarrierFormat,
        Endpoint,
        Parameter,
        HttpMethod,
        ParameterType,
        ParameterLocation,
    )

    print("✅ Successfully imported all models")

    # Test creating a minimal carrier format
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

    # Test JSON serialization
    carrier_dict = carrier.dict()
    print("✅ Successfully serialized to dict")

    # Test loading example file
    example_file = Path(__file__).parent.parent / "examples" / "expected_output.json"
    if example_file.exists():
        loaded = UniversalCarrierFormat.from_json_file(str(example_file))
        print(f"✅ Successfully loaded example file: {loaded.name}")
    else:
        print("⚠️  Example file not found (this is okay)")

    print("\n🎉 All validations passed!")
    sys.exit(0)

except ImportError as e:
    print(f"❌ Import error: {e}")
    print("\nPlease install dependencies:")
    print("  pip install -r requirements-dev.txt")
    sys.exit(1)
except Exception as e:
    print(f"❌ Validation error: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)
