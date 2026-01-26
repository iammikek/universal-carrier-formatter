"""
LLM Extractor Service

Laravel Equivalent: app/Services/LlmExtractorService.php

This service uses LLMs (via LangChain) to extract structured API schema
from unstructured PDF text. It's the "intelligence" that bridges messy
documentation to structured Universal Carrier Format.

In Laravel, you'd have:
class LlmExtractorService
{
    public function __construct(
        private HttpClient $http,
        private Config $config
    ) {}

    public function extractSchema(string $pdfText): CarrierSchema
    {
        $response = Http::withHeaders([
            'Authorization' => 'Bearer ' . config('services.openai.key'),
        ])->post('https://api.openai.com/v1/chat/completions', [
            'model' => 'gpt-4',
            'messages' => [
                ['role' => 'system', 'content' => $this->getSystemPrompt()],
                ['role' => 'user', 'content' => $pdfText],
            ],
        ]);

        return CarrierSchema::fromArray($response->json());
    }
}
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import ValidationError

from .core.schema import UniversalCarrierFormat
from .core.validator import CarrierValidator

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)


class LlmExtractorService:
    """
    LLM service for extracting structured API schema from PDF text.

    Laravel Equivalent: app/Services/LlmExtractorService.php

    This service uses LangChain to:
    1. Send PDF text to LLM
    2. Extract structured schema using prompts
    3. Parse and validate the response
    4. Return Universal Carrier Format JSON

    Usage:
        extractor = LlmExtractorService()
        schema = extractor.extract_schema(pdf_text)
    """

    def __init__(
        self,
        model: str = "gpt-4.1-mini",
        temperature: float = 0.0,
        api_key: Optional[str] = None,
    ):
        """
        Initialize LLM extractor service.

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

        # Use response_format="json_object" if available (OpenAI models)
        # This forces the model to return valid JSON
        # Note: response_format goes in model_kwargs for LangChain
        model_kwargs = {}
        if "gpt" in model.lower() or "o1" in model.lower():
            # Enable JSON mode for OpenAI models to ensure valid JSON output
            model_kwargs["response_format"] = {"type": "json_object"}
        
        self.llm = ChatOpenAI(
            model=model,
            temperature=temperature,
            api_key=api_key,
            model_kwargs=model_kwargs if model_kwargs else None,
        )
        self.validator = CarrierValidator()

    def extract_schema(self, pdf_text: str) -> UniversalCarrierFormat:
        """
        Extract Universal Carrier Format schema from PDF text.

        Laravel Equivalent:
        public function extractSchema(string $pdfText): CarrierSchema

        Args:
            pdf_text: Extracted text from PDF (from PdfParserService)

        Returns:
            UniversalCarrierFormat: Extracted and validated schema

        Raises:
            ValidationError: If LLM response doesn't match schema
            ValueError: If extraction fails
        """
        logger.info("Starting LLM schema extraction")

        # Create prompt
        prompt = self._create_extraction_prompt()
        chain = prompt | self.llm

        try:
            # Send to LLM
            logger.debug(f"Sending {len(pdf_text)} characters to LLM")
            response = chain.invoke({"pdf_text": pdf_text})

            # Parse response
            content = response.content
            logger.debug(f"Received LLM response: {len(content)} characters")

            # Extract JSON from response (LLM might wrap it in markdown code blocks)
            json_data = self._extract_json_from_response(content)

            # Validate against schema
            validated_schema = self.validator.validate(json_data)

            logger.info(
                "Successfully extracted schema",
                extra={
                    "carrier_name": validated_schema.name,
                    "endpoints_count": len(validated_schema.endpoints),
                },
            )

            return validated_schema

        except ValidationError as e:
            logger.error(f"Schema validation failed: {e.errors()}")
            raise ValueError(f"LLM response doesn't match Universal Carrier Format: {e}") from e
        except Exception as e:
            logger.error(f"LLM extraction failed: {e}", exc_info=True)
            raise ValueError(f"Failed to extract schema from PDF text: {e}") from e

    def _create_extraction_prompt(self) -> ChatPromptTemplate:
        """
        Create prompt template for schema extraction.

        Returns:
            ChatPromptTemplate: Configured prompt template
        """
        system_prompt = """You are an expert API documentation parser. Your job is to extract structured API information from carrier documentation and convert it to a standardized Universal Carrier Format JSON schema.

Your task:
1. Identify all API endpoints (paths, HTTP methods)
2. Extract request parameters (query, path, headers, body)
3. Extract response schemas (status codes, body structure)
4. Identify authentication methods
5. Extract rate limits
6. Extract field mappings (carrier field names → universal field names)
7. Identify business rules and constraints

Output ONLY valid JSON matching the Universal Carrier Format schema. 

CRITICAL: 
- Return ONLY valid JSON (you are in JSON mode, so return pure JSON)
- No markdown code blocks (just the JSON object)
- No trailing commas in arrays or objects
- No comments (// or /* */)
- All strings must be properly escaped
- Ensure all brackets and braces are properly closed
- Do not include any explanatory text before or after the JSON

Start your response with {{ and end with }}"""

        user_prompt = """Extract the API schema from this carrier documentation:

{pdf_text}

Return a JSON object matching the Universal Carrier Format schema with:
- name: Carrier name
- base_url: Base API URL
- version: API version
- description: Brief description
- endpoints: Array of endpoint objects with path, method, request, responses
- authentication: Array of authentication methods
- rate_limits: Array of rate limit objects

For each endpoint, extract:
- path: API path (e.g., "/api/v1/track")
- method: HTTP method (GET, POST, etc.)
- summary: Brief description
- request: Parameters and body schema
- responses: Array of possible responses with status codes

Return ONLY valid JSON. 

CRITICAL REQUIREMENTS:
- Valid JSON syntax only (no markdown code blocks)
- No trailing commas in arrays or objects
- No comments (// or /* */)
- All strings properly escaped
- All brackets and braces properly closed
- No text before or after the JSON"""

        return ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                ("user", user_prompt),
            ]
        )

    def _extract_json_from_response(self, response_content: str) -> Dict[str, Any]:
        """
        Extract JSON from LLM response.

        LLMs often wrap JSON in markdown code blocks like:
        ```json
        {...}
        ```

        Args:
            response_content: Raw LLM response

        Returns:
            Dict: Parsed JSON data

        Raises:
            ValueError: If JSON cannot be extracted or parsed
        """
        content = response_content.strip()

        # Try to find JSON in markdown code blocks
        if "```json" in content:
            # Extract content between ```json and ```
            start = content.find("```json") + 7
            end = content.find("```", start)
            if end != -1:
                content = content[start:end].strip()
        elif "```" in content:
            # Generic code block
            start = content.find("```") + 3
            end = content.find("```", start)
            if end != -1:
                content = content[start:end].strip()
                # Remove language identifier if present
                if content.startswith("json"):
                    content = content[4:].strip()

        # Try to find JSON object boundaries
        if "{" in content and "}" in content:
            start = content.find("{")
            end = content.rfind("}") + 1
            content = content[start:end]

        # Clean up common JSON issues
        content = self._clean_json_string(content)

        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from LLM response: {e}")
            # Log more context around the error
            error_pos = e.pos if hasattr(e, "pos") else None
            if error_pos:
                start = max(0, error_pos - 500)
                end = min(len(content), error_pos + 500)
                error_context = content[start:end]
                logger.error(
                    f"JSON error at position {error_pos} (line {e.lineno if hasattr(e, 'lineno') else 'unknown'}, col {e.colno if hasattr(e, 'colno') else 'unknown'})"
                )
                logger.error(f"Error context (500 chars before/after):\n{error_context}")
            else:
                logger.debug(f"Response content (first 1000 chars): {content[:1000]}")
            
            # Save problematic JSON to file for debugging
            try:
                import tempfile
                with tempfile.NamedTemporaryFile(
                    mode="w", suffix=".json", delete=False, dir="/tmp"
                ) as f:
                    f.write(content)
                    logger.error(f"Saved problematic JSON to: {f.name}")
                    logger.error(
                        "You can inspect this file to see what the LLM returned. "
                        "Consider using a different model or breaking the PDF into smaller chunks."
                    )
            except Exception as save_error:
                logger.debug(f"Could not save problematic JSON: {save_error}")
            
            raise ValueError(
                f"LLM response is not valid JSON: {e}. "
                f"Error at position {error_pos if error_pos else 'unknown'}. "
                "The LLM may have generated invalid JSON. Try using a different model or "
                "breaking the PDF into smaller sections."
            ) from e

    def _clean_json_string(self, json_str: str) -> str:
        """
        Clean JSON string to fix common LLM-generated issues.

        Args:
            json_str: Raw JSON string from LLM

        Returns:
            str: Cleaned JSON string
        """
        import re

        # Remove comments (JSON doesn't support comments)
        lines = json_str.split("\n")
        cleaned_lines = []
        for line in lines:
            # Remove single-line comments (// style) but preserve // inside strings
            if "//" in line:
                comment_pos = line.find("//")
                # Check if // is inside a string
                in_string = False
                escape_next = False
                for i, char in enumerate(line):
                    if escape_next:
                        escape_next = False
                        continue
                    if char == "\\":
                        escape_next = True
                        continue
                    if char == '"' and not escape_next:
                        in_string = not in_string
                    if i == comment_pos and not in_string:
                        line = line[:comment_pos].rstrip()
                        break
            cleaned_lines.append(line)
        json_str = "\n".join(cleaned_lines)

        # Try to fix trailing commas (common LLM mistake)
        # Fix trailing commas before closing braces/brackets
        # Use word boundaries to avoid matching commas inside strings
        json_str = re.sub(r",(\s*[}\]])", r"\1", json_str)

        # Remove any remaining comments that might have slipped through
        json_str = re.sub(r"//.*$", "", json_str, flags=re.MULTILINE)
        json_str = re.sub(r"/\*.*?\*/", "", json_str, flags=re.DOTALL)

        # Remove any leading/trailing whitespace
        json_str = json_str.strip()

        return json_str

    def extract_field_mappings(
        self, pdf_text: str, carrier_name: str
    ) -> List[Dict[str, str]]:
        """
        Extract field name mappings from PDF documentation.

        Example: "trk_num" → "tracking_number"

        Args:
            pdf_text: Extracted PDF text
            carrier_name: Name of the carrier

        Returns:
            List of mapping dictionaries with 'carrier_field' and 'universal_field'
        """
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are an expert at identifying field name mappings in API documentation.",
                ),
                (
                    "user",
                    f"""From this {carrier_name} API documentation, extract field name mappings.

Look for:
- Response field names (e.g., "trk_num", "stat", "loc")
- Map them to universal field names (e.g., "tracking_number", "status", "current_location")

Return a JSON array of mappings:
[
  {{{{"carrier_field": "trk_num", "universal_field": "tracking_number", "description": "Tracking number"}}}},
  {{{{"carrier_field": "stat", "universal_field": "status", "description": "Shipment status"}}}}
]

Documentation:
{pdf_text}""",
                ),
            ]
        )

        chain = prompt | self.llm
        response = chain.invoke({"pdf_text": pdf_text, "carrier_name": carrier_name})

        try:
            json_data = self._extract_json_from_response(response.content)
            if isinstance(json_data, list):
                return json_data
            return []
        except Exception as e:
            logger.warning(f"Failed to extract field mappings: {e}")
            return []

    def extract_constraints(self, pdf_text: str) -> List[Dict[str, Any]]:
        """
        Extract business rules and constraints from PDF documentation.

        Examples:
        - "Weight must be in grams for Germany"
        - "Phone numbers must not include + prefix"

        Args:
            pdf_text: Extracted PDF text

        Returns:
            List of constraint dictionaries
        """
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are an expert at identifying business rules and constraints in API documentation.",
                ),
                (
                    "user",
                    """Extract business rules and constraints from this API documentation.

Look for:
- Field validation rules (format, length, required/optional)
- Conditional rules (e.g., "if shipping to X, then Y")
- Unit conversions (grams vs kilograms)
- Format requirements (date formats, phone number formats)

Return a JSON array:
[
  {{
    "field": "weight",
    "rule": "Must be in grams if shipping to Germany, kilograms for UK",
    "type": "unit_conversion",
    "condition": "destination_country == 'DE'"
  }}
]

Documentation:
{pdf_text}""",
                ),
            ]
        )

        chain = prompt | self.llm
        response = chain.invoke({"pdf_text": pdf_text})

        try:
            json_data = self._extract_json_from_response(response.content)
            if isinstance(json_data, list):
                return json_data
            return []
        except Exception as e:
            logger.warning(f"Failed to extract constraints: {e}")
            return []
