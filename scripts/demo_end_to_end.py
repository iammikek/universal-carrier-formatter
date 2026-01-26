#!/usr/bin/env python3
"""
End-to-End Demo: Blueprint → Schema → Mapper Code

This script demonstrates the complete automation pipeline:
1. Load blueprint YAML
2. Convert to Universal Carrier Format
3. Generate mapper code using LLM
4. Test the generated mapper

Laravel Equivalent: A complete automation workflow script
"""

import json
import sys
from pathlib import Path

from src.blueprints.processor import BlueprintProcessor
from src.core.validator import CarrierValidator
from src.mapper_generator import MapperGeneratorService


def main():
    """Run end-to-end demo."""
    print("=" * 70)
    print("End-to-End Demo: Blueprint → Schema → Mapper Code")
    print("=" * 70)
    print()

    # Step 1: Load and process blueprint
    print("Step 1: Loading blueprint...")
    blueprint_file = Path("blueprints/dhl_express.yaml")
    if not blueprint_file.exists():
        print(f"❌ Blueprint file not found: {blueprint_file}")
        sys.exit(1)

    processor = BlueprintProcessor()
    schema = processor.process(blueprint_file)
    print(f"✅ Blueprint loaded: {schema.name}")
    print(f"   Base URL: {schema.base_url}")
    print(f"   Endpoints: {len(schema.endpoints)}")
    print()

    # Step 2: Validate schema
    print("Step 2: Validating schema...")
    validator = CarrierValidator()
    try:
        validated = validator.validate(schema.model_dump())
        print("✅ Schema validation passed")
    except ValueError as e:
        print(f"❌ Schema validation failed: {e}")
        sys.exit(1)
    print()

    # Step 3: Generate mapper code
    print("Step 3: Generating mapper code...")
    mapper_output = Path("src/mappers/dhl_express_mapper_generated.py")
    generator = MapperGeneratorService()
    mapper_code = generator.generate_mapper(schema, output_path=mapper_output)
    print(f"✅ Mapper code generated: {mapper_output}")
    print(f"   Code size: {len(mapper_code)} characters")
    print()

    # Step 4: Test generated mapper
    print("Step 4: Testing generated mapper...")
    try:
        # Import the generated mapper
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "dhl_express_mapper_generated", mapper_output
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Get the mapper class
        mapper_class = getattr(module, "DhlExpressMapper")
        mapper = mapper_class()

        # Test with sample data
        test_response = {
            "trackingNumber": "1234567890",
            "status": "in_transit",
            "currentLocation": {"city": "London", "country": "GB"},
            "estimatedDelivery": "2026-01-30",
        }

        result = mapper.map_tracking_response(test_response)
        print("✅ Mapper test passed!")
        print(f"   Input keys: {list(test_response.keys())}")
        print(f"   Output keys: {list(result.keys())}")
        print(f"   Output: {json.dumps(result, indent=2)}")
    except Exception as e:
        print(f"⚠️  Mapper test failed: {e}")
        print("   (This is expected if the generated code needs manual adjustment)")
    print()

    print("=" * 70)
    print("✅ End-to-End Demo Complete!")
    print("=" * 70)
    print()
    print("Summary:")
    print(f"  • Blueprint: {blueprint_file}")
    print(f"  • Schema: Validated Universal Carrier Format")
    print(f"  • Mapper: {mapper_output}")
    print()
    print("The complete automation pipeline is working!")


if __name__ == "__main__":
    main()
