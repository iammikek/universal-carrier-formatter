"""
Mapper Generator Service

Laravel Equivalent: app/Services/MapperGeneratorService.php

This service uses LLMs to automatically generate mapper code from
Universal Carrier Format schemas. It completes the end-to-end automation:
PDF/Blueprint → Schema → Mapper Code.

In Laravel, you'd have:
class MapperGeneratorService
{
    public function generateMapper(CarrierSchema $schema): string
    {
        // Use LLM to generate mapper code
        return $this->llm->generate($schema);
    }
}
"""

import json
import logging
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from .core.schema import UniversalCarrierFormat

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class MapperGeneratorService:
    """
    LLM service for generating mapper code from Universal Carrier Format schemas.

    Laravel Equivalent: app/Services/MapperGeneratorService.php

    This service uses LLMs to:
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
1. Generate a complete Python mapper class named `{class_name}Mapper`
2. The class should map carrier-specific API responses to Universal Carrier Format
3. Include:
   - FIELD_MAPPING dictionary (carrier field → universal field)
   - STATUS_MAPPING dictionary (if applicable)
   - map_tracking_response() method (main mapping method)
   - Helper methods for transformations (date formatting, country derivation, etc.)
   - map_carrier_schema() method (maps carrier schema to UniversalCarrierFormat)
   - Proper imports from ..core.schema
   - Comprehensive docstrings
4. Follow the pattern of ExampleMapper (see example structure below)
5. Handle edge cases (missing fields, null values, date parsing errors)
6. Use type hints and proper error handling

EXAMPLE STRUCTURE (from ExampleMapper):
```python
from typing import Any, Dict
from datetime import datetime
from ..core.schema import UniversalCarrierFormat, ...

class ExampleMapper:
    FIELD_MAPPING = {{"trk_num": "tracking_number", ...}}
    STATUS_MAPPING = {{"IN_TRANSIT": "in_transit", ...}}
    
    def map_tracking_response(self, carrier_response: Dict[str, Any]) -> Dict[str, Any]:
        # Transform messy response to universal format
        ...
    
    def _derive_country_from_postcode(self, postcode: str) -> str:
        # Helper method
        ...
```

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
        if "from ..core.schema import" not in code:
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

        # Ensure class name matches pattern
        class_name = self._carrier_name_to_class_name(carrier_name)
        expected_class = f"{class_name}Mapper"
        if expected_class not in code:
            logger.warning(
                f"Generated code class name doesn't match expected '{expected_class}'"
            )

        return "\n".join(lines)
