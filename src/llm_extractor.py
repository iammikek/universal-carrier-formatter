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
        model: str = "gpt-4",
        temperature: float = 0.0,
        api_key: Optional[str] = None,
    ):
        """
        Initialize LLM extractor service.

        Args:
            model: LLM model to use (default: "gpt-4")
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

Output ONLY valid JSON matching the Universal Carrier Format schema. Do not include any explanatory text, only the JSON object."""

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

Return ONLY the JSON, no markdown formatting or explanations."""

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

        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from LLM response: {e}")
            logger.debug(f"Response content: {content[:500]}")
            raise ValueError(f"LLM response is not valid JSON: {e}") from e

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
  {{"carrier_field": "trk_num", "universal_field": "tracking_number", "description": "Tracking number"}},
  {{"carrier_field": "stat", "universal_field": "status", "description": "Shipment status"}}
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
