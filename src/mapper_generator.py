"""
Mapper Generator Service.

Uses LLMs to generate mapper code from Universal Carrier Format schemas.
Completes the flow: PDF/Blueprint → Schema → Mapper Code.
"""

import logging
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from .core.schema import UniversalCarrierFormat

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class MapperGeneratorService:
    """
    LLM service for generating mapper code from Universal Carrier Format schemas.

    Uses LLMs to:
    1. Analyze Universal Carrier Format schema
    2. Generate Python mapper class code
    3. Include field mappings, status mappings, and transformation logic
    4. Return ready-to-use mapper code

    Usage:
        generator = MapperGeneratorService()
        mapper_code = generator.generate_mapper(universal_format)
    """

    def __init__(
        self,
        model: str = "gpt-4.1-mini",
        temperature: float = 0.0,
        api_key: Optional[str] = None,
    ):
        """
        Initialize mapper generator service.

        Args:
            model: LLM model to use (default: "gpt-4.1-mini" - under $2.5/1M tokens)
            temperature: Temperature for LLM (default: 0.0 for deterministic output)
            api_key: OpenAI API key (default: from OPENAI_API_KEY env var)
        """
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable not set. "
                "Please set it in your .env file or pass api_key parameter."
            )

        self.llm = ChatOpenAI(
            model=model,
            temperature=temperature,
            api_key=api_key,
        )

    def generate_mapper(
        self,
        schema: UniversalCarrierFormat,
        output_path: Optional[Path] = None,
    ) -> str:
        """
        Generate mapper code from Universal Carrier Format schema.

        Args:
            schema: UniversalCarrierFormat instance
            output_path: Optional path to save generated mapper file

        Returns:
            str: Generated mapper code as string

        Raises:
            ValueError: If generation fails
        """
        logger.info(f"Generating mapper for carrier: {schema.name}")

        # Convert schema to JSON for LLM
        schema_json = schema.model_dump_json(indent=2)

        # Create prompt
        prompt = self._create_mapper_prompt(schema.name, schema_json)

        # Generate code with LLM
        try:
            response = self.llm.invoke(prompt)
            mapper_code = self._extract_code_from_response(response.content)

            # Validate and clean up code
            mapper_code = self._clean_generated_code(mapper_code, schema.name)

            # Save to file if path provided
            if output_path:
                output_path = Path(output_path)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(mapper_code, encoding="utf-8")
                logger.info(f"Mapper code saved to: {output_path}")

            return mapper_code

        except (KeyError, TypeError, ValueError, OSError) as e:
            logger.error(f"Failed to generate mapper: {e}")
            raise ValueError(f"Failed to generate mapper: {e}") from e
        except Exception as e:
            logger.error(f"Failed to generate mapper: {e}")
            raise ValueError(f"Failed to generate mapper: {e}") from e

    def _create_mapper_prompt(self, carrier_name: str, schema_json: str) -> str:
        """
        Create prompt for mapper code generation.

        Args:
            carrier_name: Name of the carrier
            schema_json: JSON representation of Universal Carrier Format schema

        Returns:
            str: Formatted prompt
        """
        # Generate a Python-friendly class name
        class_name = self._carrier_name_to_class_name(carrier_name)

        prompt_template = """You are a Python code generator. Generate a complete mapper class for a carrier API.

CARRIER: {carrier_name}
CLASS NAME: {class_name}

SCHEMA (Universal Carrier Format JSON):
{schema_json}

REQUIREMENTS:
1. Generate a complete Python mapper class named `{class_name}Mapper` that INHERITS from CarrierMapperBase.
2. Add these imports: `from .base import CarrierMapperBase` and `from .registry import register_carrier`.
3. Decorate the class with @register_carrier("carrier_slug") where carrier_slug is snake_case from the carrier name (e.g. "dhl_express", "mydhl").
4. The class should map carrier-specific API responses to Universal Carrier Format.
5. Include:
   - FIELD_MAPPING dictionary (carrier field → universal field using UniversalFieldNames constants)
     **IMPORTANT: Each carrier field key must be UNIQUE - no duplicate keys allowed!**
   - STATUS_MAPPING dictionary (carrier status → universal status string)
   - map_tracking_response() method (main mapping method)
   - Helper methods for transformations (date formatting, country derivation, etc.)
   - map_carrier_schema() method (maps carrier schema to UniversalCarrierFormat)
   - Proper imports from ..core.schema and ..core
   - Comprehensive docstrings
4. Follow the pattern of ExampleMapper (see example structure below)
5. Handle edge cases (missing fields, null values, date parsing errors)
6. Use type hints and proper error handling
7. ONLY use standard library and datetime module - do NOT import external libraries like dateutil, pandas, etc.
8. For date parsing, use datetime.strptime() from datetime module

CRITICAL:
- Use UniversalFieldNames constants for all universal field names, NOT string literals!
- FIELD_MAPPING must have UNIQUE keys only - each carrier field name must appear exactly once. If the same carrier field appears in multiple places (e.g. nested paths like ShipmentInfo.X and top-level X), pick one canonical mapping per logical field and do not repeat the key. Duplicate keys in generated code will be removed automatically (first occurrence kept).

EXAMPLE STRUCTURE (from ExampleMapper; use CarrierMapperBase and register_carrier):
```python
from typing import Any, Dict
from datetime import datetime
from ..core.schema import UniversalCarrierFormat
from ..core import UniversalFieldNames
from .base import CarrierMapperBase
from .registry import register_carrier

@register_carrier("example")
class ExampleMapper(CarrierMapperBase):
    # Use UniversalFieldNames constants, NOT string literals
    FIELD_MAPPING = {{
        "trk_num": UniversalFieldNames.TRACKING_NUMBER,
        "stat": UniversalFieldNames.STATUS,
        "loc": UniversalFieldNames.CURRENT_LOCATION,
        "est_del": UniversalFieldNames.ESTIMATED_DELIVERY,
        "postcode": UniversalFieldNames.POSTAL_CODE,
    }}

    # Status values are strings (not constants)
    STATUS_MAPPING = {{
        "IN_TRANSIT": "in_transit",
        "DELIVERED": "delivered",
        "EXCEPTION": "exception",
        "PENDING": "pending",
    }}

    def map_tracking_response(self, carrier_response: Dict[str, Any]) -> Dict[str, Any]:
        universal_response = {{}}

        # Use constants when accessing dictionary keys
        if "trk_num" in carrier_response:
            universal_response[UniversalFieldNames.TRACKING_NUMBER] = carrier_response["trk_num"]

        if "stat" in carrier_response:
            carrier_status = carrier_response["stat"]
            universal_response[UniversalFieldNames.STATUS] = self.STATUS_MAPPING.get(
                carrier_status, carrier_status.lower()
            )
        return universal_response

    def _derive_country_from_postcode(self, postcode: str) -> str:
        # Helper method
        ...
```

IMPORTANT:
- ALWAYS import: `from ..core import UniversalFieldNames`
- ALWAYS use `UniversalFieldNames.TRACKING_NUMBER` instead of `"tracking_number"`
- ALWAYS use `UniversalFieldNames.STATUS` instead of `"status"`
- Use constants in FIELD_MAPPING values
- Use constants when setting dictionary keys: `universal[UniversalFieldNames.TRACKING_NUMBER]`
- Do NOT use string literals for universal field names
- Do NOT import TrackingStatus or TrackingEvent (they don't exist)

AVAILABLE UniversalFieldNames CONSTANTS (use ONLY these):
- UniversalFieldNames.TRACKING_NUMBER
- UniversalFieldNames.STATUS
- UniversalFieldNames.LAST_UPDATE
- UniversalFieldNames.CURRENT_LOCATION
- UniversalFieldNames.ESTIMATED_DELIVERY
- UniversalFieldNames.CITY
- UniversalFieldNames.POSTAL_CODE
- UniversalFieldNames.COUNTRY
- UniversalFieldNames.ADDRESS_LINE_1
- UniversalFieldNames.ADDRESS_LINE_2
- UniversalFieldNames.STATE
- UniversalFieldNames.ORIGIN_COUNTRY
- UniversalFieldNames.DESTINATION_COUNTRY
- UniversalFieldNames.EVENTS
- UniversalFieldNames.EVENT_TYPE
- UniversalFieldNames.EVENT_DATETIME
- UniversalFieldNames.EVENT_DESCRIPTION
- UniversalFieldNames.EVENT_LOCATION
- UniversalFieldNames.PROOF_OF_DELIVERY
- UniversalFieldNames.DELIVERED_AT
- UniversalFieldNames.SIGNED_BY
- UniversalFieldNames.WEIGHT
- UniversalFieldNames.DIMENSIONS
- UniversalFieldNames.LABEL_BASE64
- UniversalFieldNames.LABEL
- UniversalFieldNames.MANIFEST_ID
- UniversalFieldNames.MANIFEST_NUMBER
- UniversalFieldNames.MANIFEST_LABEL
- UniversalFieldNames.SERVICE_NAME
- UniversalFieldNames.SHIPMENT_NUMBER
- UniversalFieldNames.HISTORY
- UniversalFieldNames.CREATED_AT
- UniversalFieldNames.UPDATED_AT
- UniversalFieldNames.CARRIER
- UniversalFieldNames.CARRIER_SERVICE
- UniversalFieldNames.COST
- UniversalFieldNames.CURRENCY

If a field doesn't match any constant above, use the closest match or create a descriptive snake_case string (but prefer constants when possible).

Generate ONLY the Python code, no markdown formatting, no explanations. Start with the imports and class definition.
"""

        return prompt_template.format(
            carrier_name=carrier_name,
            class_name=class_name,
            schema_json=schema_json,
        )

    def _carrier_name_to_class_name(self, carrier_name: str) -> str:
        """
        Convert carrier name to Python class name.

        Args:
            carrier_name: Carrier name (e.g., "DHL Express", "FedEx")

        Returns:
            str: Class name (e.g., "DhlExpress", "Fedex")
        """
        # Remove special characters, split by spaces/underscores
        parts = carrier_name.replace("-", " ").replace("_", " ").split()
        # Capitalize each part and join
        return "".join(word.capitalize() for word in parts)

    def _carrier_name_to_slug(self, carrier_name: str) -> str:
        """
        Convert carrier name to registry slug (snake_case).

        Args:
            carrier_name: Carrier name (e.g., "DHL Express", "MYDHL API")

        Returns:
            str: Slug for @register_carrier (e.g., "dhl_express", "mydhl_api")
        """
        slug = carrier_name.replace("-", "_").replace(" ", "_").lower()
        # Collapse multiple underscores
        while "__" in slug:
            slug = slug.replace("__", "_")
        return slug.strip("_") or "carrier"

    def _extract_code_from_response(self, response_content: str) -> str:
        """
        Extract Python code from LLM response.

        Handles responses that may be wrapped in markdown code blocks.

        Args:
            response_content: Raw LLM response

        Returns:
            str: Extracted Python code
        """
        content = response_content.strip()

        # Remove markdown code blocks if present
        if content.startswith("```python"):
            content = content[9:]  # Remove ```python
        elif content.startswith("```"):
            content = content[3:]  # Remove ```

        if content.endswith("```"):
            content = content[:-3]  # Remove closing ```

        return content.strip()

    def _clean_generated_code(self, code: str, carrier_name: str) -> str:
        """
        Clean and validate generated code.

        Args:
            code: Generated mapper code
            carrier_name: Carrier name for validation

        Returns:
            str: Cleaned code
        """
        lines = code.split("\n")

        # Ensure proper imports
        has_core_schema_import = (
            "from ..core.schema import" in code or "from ..core.schema import" in code
        )
        has_universal_field_names = (
            "from ..core import UniversalFieldNames" in code
            or "UniversalFieldNames" in code
        )

        if not has_core_schema_import:
            logger.warning("Generated code missing core.schema imports, adding...")
            import_line = "from ..core.schema import UniversalCarrierFormat"
            if import_line not in code:
                # Find first non-comment line and insert after imports
                for i, line in enumerate(lines):
                    if line.startswith("from") or line.startswith("import"):
                        continue
                    if line.strip() and not line.strip().startswith("#"):
                        lines.insert(i, import_line)
                        break

        # Ensure registry pattern: CarrierMapperBase and register_carrier
        slug = self._carrier_name_to_slug(carrier_name)
        expected_class = f"{self._carrier_name_to_class_name(carrier_name)}Mapper"
        has_base_import = "from .base import CarrierMapperBase" in code
        has_registry_import = "from .registry import register_carrier" in code
        has_register_decorator = "@register_carrier" in code
        has_base_class = "(CarrierMapperBase)" in code or "CarrierMapperBase" in code

        if not has_base_import:
            # Insert after last ..core import (prefer after UniversalFieldNames)
            inserted = False
            for i, line in enumerate(lines):
                if "from ..core import UniversalFieldNames" in line:
                    lines.insert(i + 1, "from .base import CarrierMapperBase")
                    inserted = True
                    break
            if not inserted:
                for i, line in enumerate(lines):
                    if "from ..core.schema import" in line:
                        lines.insert(i + 1, "from .base import CarrierMapperBase")
                        break
                else:
                    for i, line in enumerate(lines):
                        if line.startswith("from") or line.startswith("import"):
                            continue
                        if line.strip() and not line.strip().startswith("#"):
                            lines.insert(i, "from .base import CarrierMapperBase")
                            break
        if not has_registry_import:
            for i, line in enumerate(lines):
                if "from .base import CarrierMapperBase" in line:
                    lines.insert(i + 1, "from .registry import register_carrier")
                    break

        code = "\n".join(lines)

        # Ensure class inherits CarrierMapperBase
        if not has_base_class and f"class {expected_class}" in code:
            code = code.replace(
                f"class {expected_class}:",
                f"class {expected_class}(CarrierMapperBase):",
                1,
            )
            code = code.replace(
                f"class {expected_class} ",
                f"class {expected_class}(CarrierMapperBase) ",
                1,
            )

        # Ensure @register_carrier(slug) decorator before class
        if not has_register_decorator and f"class {expected_class}" in code:
            # Insert line before "class XxxMapper"
            code = code.replace(
                f"class {expected_class}",
                f'@register_carrier("{slug}")\nclass {expected_class}',
                1,
            )

        lines = code.split("\n")

        # Ensure UniversalFieldNames import
        if not has_universal_field_names:
            logger.warning(
                "Generated code missing UniversalFieldNames import, adding..."
            )
            import_line = "from ..core import UniversalFieldNames"
            if import_line not in code:
                # Find line with core.schema import and add after it
                for i, line in enumerate(lines):
                    if "from ..core.schema import" in line:
                        lines.insert(i + 1, import_line)
                        break
                    elif i > 0 and (
                        "from ..core.schema" in lines[i - 1]
                        or "from ..core import" in lines[i - 1]
                    ):
                        lines.insert(i, import_line)
                        break
                else:
                    # If no core import found, add at top after other imports
                    for i, line in enumerate(lines):
                        if line.startswith("from") or line.startswith("import"):
                            continue
                        if line.strip() and not line.strip().startswith("#"):
                            lines.insert(i, import_line)
                            break

        # Ensure class name matches pattern
        class_name = self._carrier_name_to_class_name(carrier_name)
        expected_class = f"{class_name}Mapper"
        if expected_class not in code:
            logger.warning(
                f"Generated code class name doesn't match expected '{expected_class}'"
            )

        # Fix common issues: replace string literals with UniversalFieldNames constants
        # This is a safety net - the prompt should handle this, but we fix it here too
        code = "\n".join(lines)

        # Replace common string literals in FIELD_MAPPING with constants
        # Note: This is a basic fix - the LLM should generate this correctly from the prompt
        field_replacements = {
            '"tracking_number"': "UniversalFieldNames.TRACKING_NUMBER",
            '"status"': "UniversalFieldNames.STATUS",
            '"last_update"': "UniversalFieldNames.LAST_UPDATE",
            '"current_location"': "UniversalFieldNames.CURRENT_LOCATION",
            '"estimated_delivery"': "UniversalFieldNames.ESTIMATED_DELIVERY",
            '"postal_code"': "UniversalFieldNames.POSTAL_CODE",
            '"city"': "UniversalFieldNames.CITY",
            '"country"': "UniversalFieldNames.COUNTRY",
            '"origin_country"': "UniversalFieldNames.ORIGIN_COUNTRY",
            '"destination_country"': "UniversalFieldNames.DESTINATION_COUNTRY",
            '"events"': "UniversalFieldNames.EVENTS",
            '"proof_of_delivery"': "UniversalFieldNames.PROOF_OF_DELIVERY",
            '"label_base64"': "UniversalFieldNames.LABEL_BASE64",
            '"manifest_id"': "UniversalFieldNames.MANIFEST_ID",
        }

        # Only replace in FIELD_MAPPING context (between FIELD_MAPPING = { and })
        import re

        field_mapping_pattern = r'(FIELD_MAPPING\s*=\s*\{[^}]*)"(tracking_number|status|last_update|current_location|estimated_delivery|postal_code|city|country|origin_country|destination_country|events|proof_of_delivery|label_base64|manifest_id)"'

        def replace_in_field_mapping(match):
            field_name = match.group(2)
            replacement = field_replacements.get(f'"{field_name}"', f'"{field_name}"')
            return match.group(1) + replacement

        code = re.sub(field_mapping_pattern, replace_in_field_mapping, code)

        # Remove duplicate keys in FIELD_MAPPING (keep first occurrence of each key)
        field_mapping_match = re.search(
            r"(FIELD_MAPPING\s*=\s*\{)([^}]+)(\})", code, re.DOTALL
        )
        if field_mapping_match:
            prefix, field_mapping_content, suffix = field_mapping_match.groups()
            seen_keys = set()
            kept_lines = []
            for line in field_mapping_content.split("\n"):
                key_match = re.match(r'^\s*"([^"]+)"\s*:', line)
                if key_match:
                    key = key_match.group(1)
                    if key in seen_keys:
                        logger.warning(
                            f"Removing duplicate FIELD_MAPPING key: {key!r} (keeping first occurrence)"
                        )
                        continue
                    seen_keys.add(key)
                kept_lines.append(line)
            deduped_content = "\n".join(kept_lines)
            code = (
                code[: field_mapping_match.start()]
                + prefix
                + deduped_content
                + suffix
                + code[field_mapping_match.end() :]
            )

        # Also replace in dictionary key access patterns: universal["field_name"]
        # This is more complex, so we'll rely on the prompt to get it right
        # But we can add a comment to guide developers

        return code
