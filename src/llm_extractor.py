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

            # Normalize authentication types before validation
            json_data = self._normalize_authentication(json_data)

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

AUTHENTICATION REQUIREMENTS:
- Authentication type MUST be one of: "api_key", "bearer", "basic", "oauth2", or "custom"
- If you encounter non-standard auth types (like "ws-security", "soap", "username_token", etc.), use "custom"
- Each authentication object MUST include a "name" field (e.g., "API Key Authentication", "WS-Security Authentication")
- Common mappings:
  * API keys, X-API-Key → "api_key"
  * Bearer tokens, JWT → "bearer"
  * Basic auth, Digest → "basic"
  * OAuth, OAuth2 → "oauth2"
  * WS-Security, SOAP headers, custom protocols → "custom"

Return ONLY valid JSON. 

CRITICAL REQUIREMENTS:
- Valid JSON syntax only (no markdown code blocks)
- No trailing commas in arrays or objects
- No comments (// or /* */)
- All strings properly escaped
- All brackets and braces properly closed
- No text before or after the JSON
- Every authentication object MUST have both "type" and "name" fields"""

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
            # If error is about control characters, try to fix them
            error_msg = str(e).lower()
            if "control character" in error_msg:
                logger.warning(
                    "Detected control character in JSON, attempting to fix..."
                )
                try:
                    content = self._fix_control_characters(content)
                    parsed = json.loads(content)
                    logger.info("✅ Successfully fixed control character issue")
                    return parsed
                except json.JSONDecodeError as fix_error:
                    logger.warning(
                        f"Control character fix attempted but failed: {fix_error}"
                    )
                    # Fall through to original error handling
                except Exception as fix_error:
                    logger.debug(f"Unexpected error during control character fix: {fix_error}")
                    # Fall through to original error handling
            
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
        # Process character by character to properly handle strings
        result = []
        i = 0
        in_string = False
        escape_next = False
        in_single_line_comment = False
        in_multi_line_comment = False

        while i < len(json_str):
            char = json_str[i]

            if escape_next:
                # We're processing an escape sequence, preserve it
                result.append(char)
                escape_next = False
                i += 1
                continue

            if char == "\\":
                # Start of escape sequence
                result.append(char)
                escape_next = True
                i += 1
                continue

            if in_multi_line_comment:
                # We're in a multi-line comment, skip until */
                if char == "*" and i + 1 < len(json_str) and json_str[i + 1] == "/":
                    in_multi_line_comment = False
                    i += 2  # Skip */
                    continue
                i += 1
                continue

            if in_single_line_comment:
                # We're in a single-line comment, skip until newline
                if char == "\n":
                    in_single_line_comment = False
                    result.append(char)  # Preserve newline
                i += 1
                continue

            if char == '"':
                # Toggle string state
                in_string = not in_string
                result.append(char)
                i += 1
                continue

            if not in_string:
                # We're outside a string, check for comments
                if char == "/" and i + 1 < len(json_str):
                    next_char = json_str[i + 1]
                    if next_char == "/":
                        # Single-line comment
                        in_single_line_comment = True
                        i += 2
                        continue
                    elif next_char == "*":
                        # Multi-line comment
                        in_multi_line_comment = True
                        i += 2
                        continue

            # Regular character, preserve it
            result.append(char)
            i += 1

        json_str = "".join(result)

        # Try to fix trailing commas (common LLM mistake)
        # Fix trailing commas before closing braces/brackets
        # This regex is safe because we're only matching outside strings
        json_str = re.sub(r",(\s*[}\]])", r"\1", json_str)

        # Remove any leading/trailing whitespace
        json_str = json_str.strip()

        return json_str

    def _normalize_authentication(self, json_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize authentication methods in JSON data before validation.
        
        Ensures:
        - All auth types are valid (maps non-standard to 'custom')
        - All auth objects have a 'name' field
        
        Args:
            json_data: Raw JSON data from LLM
            
        Returns:
            Dict: Normalized JSON data
        """
        if "authentication" not in json_data:
            return json_data
        
        normalized_auth = []
        for auth in json_data["authentication"]:
            if not isinstance(auth, dict):
                continue
            
            # Normalize type
            auth_type = auth.get("type", "custom")
            auth_type_lower = str(auth_type).lower().strip()
            
            # Map non-standard types to 'custom'
            allowed_types = ["api_key", "bearer", "basic", "oauth2", "custom"]
            if auth_type_lower not in allowed_types:
                # Common mappings
                type_mappings = {
                    "ws-security": "custom",
                    "ws_security": "custom",
                    "soap": "custom",
                    "soap_header": "custom",
                    "username_token": "custom",
                    "digest": "basic",
                    "token": "bearer",
                    "jwt": "bearer",
                    "apikey": "api_key",
                    "api-key": "api_key",
                }
                
                if auth_type_lower in type_mappings:
                    auth["type"] = type_mappings[auth_type_lower]
                elif "bearer" in auth_type_lower or "token" in auth_type_lower:
                    auth["type"] = "bearer"
                elif "basic" in auth_type_lower or "digest" in auth_type_lower:
                    auth["type"] = "basic"
                elif "oauth" in auth_type_lower:
                    auth["type"] = "oauth2"
                elif "api" in auth_type_lower and "key" in auth_type_lower:
                    auth["type"] = "api_key"
                else:
                    auth["type"] = "custom"
            else:
                auth["type"] = auth_type_lower
            
            # Ensure name field exists
            if "name" not in auth or not auth.get("name"):
                type_names = {
                    "api_key": "API Key Authentication",
                    "bearer": "Bearer Token Authentication",
                    "basic": "Basic Authentication",
                    "oauth2": "OAuth 2.0 Authentication",
                    "custom": "Custom Authentication",
                }
                auth["name"] = type_names.get(auth["type"], f"{auth['type'].title()} Authentication")
            
            normalized_auth.append(auth)
        
        json_data["authentication"] = normalized_auth
        return json_data

    def _fix_control_characters(self, json_str: str) -> str:
        """
        Fix invalid control characters in JSON strings by properly escaping them.

        JSON doesn't allow unescaped control characters (except in specific cases).
        This function escapes control characters within string values.

        Args:
            json_str: JSON string that may contain invalid control characters

        Returns:
            str: JSON string with properly escaped control characters
        """
        import re

        # Control characters that need to be escaped in JSON strings
        # (0x00-0x1F except for \n, \r, \t which are already handled)
        result = []
        i = 0
        in_string = False
        escape_next = False
        string_start = None

        while i < len(json_str):
            char = json_str[i]

            if escape_next:
                # We're processing an escape sequence, just copy it
                result.append(char)
                escape_next = False
                i += 1
                continue

            if char == "\\":
                # Start of escape sequence
                result.append(char)
                escape_next = True
                i += 1
                continue

            if char == '"':
                # Toggle string state
                in_string = not in_string
                result.append(char)
                i += 1
                continue

            if in_string:
                # We're inside a string value
                # Check if this is a control character that needs escaping
                char_code = ord(char)
                # Control characters are 0x00-0x1F
                # But \n (0x0A), \r (0x0D), \t (0x09) are allowed if escaped
                if char_code < 0x20:
                    # This is a control character - escape it
                    if char == "\n":
                        result.append("\\n")
                    elif char == "\r":
                        result.append("\\r")
                    elif char == "\t":
                        result.append("\\t")
                    elif char == "\b":
                        result.append("\\b")
                    elif char == "\f":
                        result.append("\\f")
                    else:
                        # Other control characters - use Unicode escape
                        result.append(f"\\u{char_code:04x}")
                else:
                    # Regular character, just append
                    result.append(char)
            else:
                # Outside string, just copy
                result.append(char)

            i += 1

        return "".join(result)

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
                    """From this {carrier_name} API documentation, extract field name mappings.

Look for:
- Response field names (e.g., "trk_num", "stat", "loc")
- Map them to universal field names (e.g., "tracking_number", "status", "current_location")

Return a JSON array of mappings:
[
  {{"carrier_field": "trk_num", "universal_field": "tracking_number", "description": "Tracking number"}},
  {{"carrier_field": "stat", "universal_field": "status", "description": "Shipment status"}}
]

Documentation:
{pdf_text}""".format(carrier_name=carrier_name, pdf_text=pdf_text),
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
  {{"field": "weight", "rule": "Must be in grams if shipping to Germany, kilograms for UK", "type": "unit_conversion", "condition": "destination_country == 'DE'"}}
]

Documentation:
{pdf_text}""".format(pdf_text=pdf_text),
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
