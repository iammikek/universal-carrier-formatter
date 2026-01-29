"""
LLM Extractor Service.

Uses LLMs (via LangChain) to extract structured API schema from unstructured
PDF text. Bridges messy documentation to structured Universal Carrier Format.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from pydantic import ValidationError

from .core.config import (
    CONSTRAINTS_ALT_KEYS,
    DEFAULT_LLM_PROVIDER,
    EDGE_CASES_ALT_KEYS,
    FIELD_MAPPINGS_ALT_KEYS,
    KEY_AUTHENTICATION,
    KEY_CARRIER_FIELD,
    KEY_ENDPOINTS,
    KEY_LIMIT,
    KEY_NAME,
    KEY_RATE_LIMITS,
    KEY_REQUESTS,
    KEY_RESPONSES,
    KEY_STATUS,
    KEY_STATUS_CODE,
    KEY_UNIVERSAL_FIELD,
    LLM_PROVIDER_ENV,
)
from .core.llm_factory import get_chat_model, get_default_model_for_provider
from .core.schema import UniversalCarrierFormat
from .core.validator import CarrierValidator
from .prompts import (
    get_constraints_prompt,
    get_edge_cases_prompt,
    get_field_mappings_prompt,
    get_schema_extraction_prompt,
)

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)


class LlmExtractorService:
    """
    LLM service for extracting structured API schema from PDF text.

    Uses LangChain to:
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
        model: Optional[str] = None,
        temperature: float = 0.0,
        api_key: Optional[str] = None,
        provider: Optional[str] = None,
    ):
        """
        Initialize LLM extractor service.

        Args:
            model: LLM model name (default: provider-specific, e.g. gpt-4.1-mini or claude-3-5-haiku)
            temperature: Temperature for LLM (default: 0.0 for deterministic output)
            api_key: API key (default: from OPENAI_API_KEY or ANTHROPIC_API_KEY per provider)
            provider: "openai" or "anthropic" (default: from LLM_PROVIDER env or "openai")
        """
        provider = (
            (provider or os.getenv(LLM_PROVIDER_ENV) or DEFAULT_LLM_PROVIDER)
            .strip()
            .lower()
        )
        model = model or get_default_model_for_provider(provider)
        self._provider = provider
        self.llm = get_chat_model(
            provider=provider,
            model=model,
            temperature=temperature,
            api_key=api_key,
        )
        self.validator = CarrierValidator()
        self._model = model
        self._temperature = temperature
        self._model_kwargs = {}
        if provider == "openai" and ("gpt" in model.lower() or "o1" in model.lower()):
            self._model_kwargs["response_format"] = {"type": "json_object"}

    def get_config(self) -> Dict[str, Any]:
        """
        Return LLM config used for extraction (for reproducibility metadata).

        Includes model, temperature, top_p (if set), and response_format hint.
        """
        config: Dict[str, Any] = {
            "model": self._model,
            "temperature": self._temperature,
        }
        if self._model_kwargs.get("top_p") is not None:
            config["top_p"] = self._model_kwargs["top_p"]
        if self._model_kwargs.get("response_format"):
            config["response_format"] = self._model_kwargs["response_format"]
        return config

    def extract_schema(self, pdf_text: str) -> UniversalCarrierFormat:
        """
        Extract Universal Carrier Format schema from PDF text.

        Args:
            pdf_text: Extracted text from PDF (from PdfParserService)

        Returns:
            UniversalCarrierFormat: Extracted and validated schema

        Raises:
            ValidationError: If LLM response doesn't match schema
            ValueError: If extraction fails
        """
        logger.info("Starting LLM schema extraction")

        prompt = get_schema_extraction_prompt()
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

            # Normalize rate limits before validation
            json_data = self._normalize_rate_limits(json_data)

            # Normalize response objects: LLMs often return "status" instead of "status_code"
            json_data = self._normalize_response_status_codes(json_data)

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
            raise ValueError(
                f"LLM response doesn't match Universal Carrier Format: {e}"
            ) from e
        except (KeyError, TypeError, json.JSONDecodeError) as e:
            logger.error(f"LLM response parse error: {e}", exc_info=True)
            raise ValueError(f"Failed to extract schema from PDF text: {e}") from e
        except Exception as e:
            logger.error(f"LLM extraction failed: {e}", exc_info=True)
            raise ValueError(f"Failed to extract schema from PDF text: {e}") from e

    def _unwrap_json_content(self, response_content: str) -> str:
        """
        Unwrap raw JSON string from markdown code blocks or find object/array boundaries.

        LLMs often wrap JSON in ```json ... ``` or ``` ... ```. Falls back to
        finding the outermost { } or [ ].
        """
        content = response_content.strip()

        if "```json" in content:
            start = content.find("```json") + 7
            end = content.find("```", start)
            if end != -1:
                content = content[start:end].strip()
        elif "```" in content:
            start = content.find("```") + 3
            end = content.find("```", start)
            if end != -1:
                content = content[start:end].strip()
                if content.startswith("json"):
                    content = content[4:].strip()

        stripped = content.strip()
        if stripped.startswith("["):
            start = content.find("[")
            end = content.rfind("]") + 1
            if start >= 0 and end > start:
                content = content[start:end]
        elif "{" in content and "}" in content:
            start = content.find("{")
            end = content.rfind("}") + 1
            content = content[start:end]

        return content

    def _log_json_parse_error_and_raise(
        self, content: str, e: json.JSONDecodeError
    ) -> None:
        """Log context and temp file path, then raise ValueError."""
        error_pos = e.pos if hasattr(e, "pos") else None
        if error_pos is not None:
            start = max(0, error_pos - 500)
            end = min(len(content), error_pos + 500)
            logger.error(
                "JSON error at position %s (line %s, col %s)",
                error_pos,
                getattr(e, "lineno", "unknown"),
                getattr(e, "colno", "unknown"),
            )
            logger.error(
                "Error context (500 chars before/after):\n%s",
                content[start:end],
            )
        else:
            logger.debug("Response content (first 1000 chars): %s", content[:1000])

        try:
            import tempfile

            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False, dir="/tmp"
            ) as f:
                f.write(content)
                logger.error("Saved problematic JSON to: %s", f.name)
                logger.error(
                    "You can inspect this file to see what the LLM returned. "
                    "Consider using a different model or breaking the PDF into smaller chunks."
                )
        except Exception as save_error:
            logger.debug("Could not save problematic JSON: %s", save_error)

        raise ValueError(
            f"LLM response is not valid JSON: {e}. "
            f"Error at position {error_pos if error_pos else 'unknown'}. "
            "The LLM may have generated invalid JSON. Try using a different model or "
            "breaking the PDF into smaller sections."
        ) from e

    def _parse_json_string(self, content: str) -> Dict[str, Any]:
        """
        Clean JSON string, parse it, and optionally try control-character fix on failure.

        Raises:
            ValueError: If JSON cannot be parsed (after logging context).
        """
        content = self._clean_json_string(content)
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            error_msg = str(e).lower()
            if "control character" in error_msg:
                logger.warning(
                    "Detected control character in JSON, attempting to fix..."
                )
                try:
                    content = self._fix_control_characters(content)
                    parsed = json.loads(content)
                    logger.info("Successfully fixed control character issue")
                    return parsed
                except json.JSONDecodeError as fix_error:
                    logger.warning(
                        "Control character fix attempted but failed: %s",
                        fix_error,
                    )
                except Exception as fix_error:
                    logger.debug(
                        "Unexpected error during control character fix: %s",
                        fix_error,
                    )
            self._log_json_parse_error_and_raise(content, e)

    def _extract_json_from_response(self, response_content: str) -> Dict[str, Any]:
        """
        Extract JSON from LLM response.

        LLMs often wrap JSON in markdown code blocks. Unwraps content, cleans
        (comments, trailing commas), and parses. On control-character errors,
        attempts to fix and re-parse.

        Args:
            response_content: Raw LLM response

        Returns:
            Dict: Parsed JSON data

        Raises:
            ValueError: If JSON cannot be extracted or parsed
        """
        content = self._unwrap_json_content(response_content)
        return self._parse_json_string(content)

    def _strip_json_comments(self, json_str: str) -> str:
        """
        Remove // and /* */ comments from a JSON-like string.

        Processes character-by-character so string contents are not altered.
        JSON does not support comments; LLMs sometimes emit them.
        """
        result = []
        i = 0
        in_string = False
        escape_next = False
        in_single_line_comment = False
        in_multi_line_comment = False

        while i < len(json_str):
            char = json_str[i]

            if escape_next:
                result.append(char)
                escape_next = False
                i += 1
                continue

            if char == "\\":
                result.append(char)
                escape_next = True
                i += 1
                continue

            if in_multi_line_comment:
                if char == "*" and i + 1 < len(json_str) and json_str[i + 1] == "/":
                    in_multi_line_comment = False
                    i += 2
                    continue
                i += 1
                continue

            if in_single_line_comment:
                if char == "\n":
                    in_single_line_comment = False
                    result.append(char)
                i += 1
                continue

            if char == '"':
                in_string = not in_string
                result.append(char)
                i += 1
                continue

            if not in_string and char == "/" and i + 1 < len(json_str):
                next_char = json_str[i + 1]
                if next_char == "/":
                    in_single_line_comment = True
                    i += 2
                    continue
                if next_char == "*":
                    in_multi_line_comment = True
                    i += 2
                    continue

            result.append(char)
            i += 1

        return "".join(result)

    def _clean_json_string(self, json_str: str) -> str:
        """
        Clean JSON string to fix common LLM-generated issues.

        Removes comments, fixes trailing commas before ]/}, and strips whitespace.
        """
        import re

        json_str = self._strip_json_comments(json_str)
        json_str = re.sub(r",(\s*[}\]])", r"\1", json_str)
        return json_str.strip()

    def _normalize_single_auth(self, auth: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize one authentication object: type (map to allowed) and name."""
        if not isinstance(auth, dict):
            return auth

        auth_type = auth.get("type", "custom")
        auth_type_lower = str(auth_type).lower().strip()
        allowed_types = ["api_key", "bearer", "basic", "oauth2", "custom"]

        if auth_type_lower not in allowed_types:
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

        if KEY_NAME not in auth or not auth.get(KEY_NAME):
            type_names = {
                "api_key": "API Key Authentication",
                "bearer": "Bearer Token Authentication",
                "basic": "Basic Authentication",
                "oauth2": "OAuth 2.0 Authentication",
                "custom": "Custom Authentication",
            }
            auth[KEY_NAME] = type_names.get(
                auth["type"], f"{auth['type'].title()} Authentication"
            )

        return auth

    def _normalize_authentication(self, json_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize authentication methods in JSON data before validation.

        Ensures all auth types are valid (maps non-standard to 'custom') and
        all auth objects have a 'name' field.
        """
        if KEY_AUTHENTICATION not in json_data:
            return json_data

        normalized_auth = []
        for auth in json_data[KEY_AUTHENTICATION]:
            if isinstance(auth, dict):
                normalized_auth.append(self._normalize_single_auth(auth))
        json_data[KEY_AUTHENTICATION] = normalized_auth
        return json_data

    def _normalize_rate_limits(self, json_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize rate limits in JSON data before validation.

        Ensures:
        - 'limit' field is mapped to 'requests' if present
        - All rate limit objects have required 'requests' field

        Args:
            json_data: Raw JSON data from LLM

        Returns:
            Dict: Normalized JSON data
        """
        if KEY_RATE_LIMITS not in json_data:
            return json_data

        normalized_limits = []
        for limit in json_data[KEY_RATE_LIMITS]:
            if not isinstance(limit, dict):
                continue

            if KEY_LIMIT in limit and KEY_REQUESTS not in limit:
                limit[KEY_REQUESTS] = limit.pop(KEY_LIMIT)

            if KEY_REQUESTS in limit:
                try:
                    limit[KEY_REQUESTS] = int(limit[KEY_REQUESTS])
                except (ValueError, TypeError):
                    limit[KEY_REQUESTS] = 1
            else:
                limit[KEY_REQUESTS] = 1

            normalized_limits.append(limit)

        json_data[KEY_RATE_LIMITS] = normalized_limits
        return json_data

    def _normalize_response_status_codes(
        self, json_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Normalize endpoint response objects: map LLM "status" to "status_code".

        Our schema expects responses[].status_code (int). LLMs often return "status"
        (e.g. from HTTP/API docs). This ensures status_code is set before validation.

        Args:
            json_data: Raw JSON data from LLM

        Returns:
            Dict: JSON with response objects using status_code
        """
        for endpoint in json_data.get(KEY_ENDPOINTS, []):
            if not isinstance(endpoint, dict):
                continue
            for resp in endpoint.get(KEY_RESPONSES, []):
                if not isinstance(resp, dict):
                    continue
                if KEY_STATUS_CODE not in resp and KEY_STATUS in resp:
                    try:
                        resp[KEY_STATUS_CODE] = int(resp[KEY_STATUS])
                    except (ValueError, TypeError):
                        pass
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
        # Control characters that need to be escaped in JSON strings
        # (0x00-0x1F except for \n, \r, \t which are already handled)
        result = []
        i = 0
        in_string = False
        escape_next = False

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
    ) -> List[Dict[str, Any]]:
        """
        Extract field name mappings from PDF documentation with validation metadata.

        Example: "trk_num" → "tracking_number" with required=true, max_length=50, type="string"

        Args:
            pdf_text: Extracted PDF text
            carrier_name: Name of the carrier

        Returns:
            List of mapping dictionaries with:
            - carrier_field: Carrier's field name
            - universal_field: Universal field name
            - description: Field description
            - required: boolean (if specified in docs)
            - max_length: integer (if specified)
            - min_length: integer (if specified)
            - type: string (string, integer, number, boolean, date, etc.)
            - pattern: regex pattern (if specified)
            - enum_values: list of allowed values (if specified)
        """
        prompt = get_field_mappings_prompt()
        chain = prompt | self.llm
        response = chain.invoke({"pdf_text": pdf_text, "carrier_name": carrier_name})

        try:
            json_data = self._extract_json_from_response(response.content)
            if isinstance(json_data, list):
                return json_data
            if isinstance(json_data, dict):
                for key in FIELD_MAPPINGS_ALT_KEYS:
                    if key in json_data and isinstance(json_data[key], list):
                        logger.debug(
                            "Unwrapped field_mappings from LLM object key '%s'", key
                        )
                        return json_data[key]
                if KEY_CARRIER_FIELD in json_data and KEY_UNIVERSAL_FIELD in json_data:
                    logger.debug(
                        "Field mappings: LLM returned a single mapping object; wrapping in list"
                    )
                    return [json_data]
                logger.warning(
                    "Field mappings: LLM returned a dict but no %s list "
                    "and not a single mapping (carrier_field+universal_field); keys seen: %s",
                    FIELD_MAPPINGS_ALT_KEYS,
                    list(json_data.keys())[:15],
                )
            return []
        except (json.JSONDecodeError, KeyError, TypeError, ValidationError) as e:
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
        prompt = get_constraints_prompt()
        chain = prompt | self.llm
        response = chain.invoke({"pdf_text": pdf_text})

        try:
            json_data = self._extract_json_from_response(response.content)
            if isinstance(json_data, list):
                return json_data
            if isinstance(json_data, dict):
                for key in CONSTRAINTS_ALT_KEYS:
                    if key in json_data and isinstance(json_data[key], list):
                        logger.debug(
                            "Unwrapped constraints from LLM object key '%s'", key
                        )
                        return json_data[key]
                logger.warning(
                    "Constraints: LLM returned a dict but no %s list; "
                    "keys seen: %s. Unwrapping is supported for those keys.",
                    CONSTRAINTS_ALT_KEYS,
                    list(json_data.keys())[:15],
                )
            return []
        except (json.JSONDecodeError, KeyError, TypeError, ValidationError) as e:
            logger.warning(f"Failed to extract constraints: {e}")
            return []

    def extract_edge_cases(self, pdf_text: str) -> List[Dict[str, Any]]:
        """
        Extract route-specific edge cases from shipping/API documentation (Scenario 3).

        Examples: customs requirements, remote-area surcharges, hazardous-goods
        restrictions, route-specific rules that engineers often miss.

        Args:
            pdf_text: Extracted PDF text

        Returns:
            List of edge-case dictionaries with type, route, requirement,
            documentation, condition, applies_to, surcharge_amount, etc.
        """
        prompt = get_edge_cases_prompt()
        chain = prompt | self.llm
        response = chain.invoke({"pdf_text": pdf_text})

        try:
            json_data = self._extract_json_from_response(response.content)
            if isinstance(json_data, list):
                return json_data
            if isinstance(json_data, dict):
                for key in EDGE_CASES_ALT_KEYS:
                    if key in json_data and isinstance(json_data[key], list):
                        logger.debug(
                            "Unwrapped edge_cases from LLM object key '%s'", key
                        )
                        return json_data[key]
                logger.debug(
                    "Edge cases: LLM returned dict but no %s list; keys seen: %s",
                    EDGE_CASES_ALT_KEYS,
                    list(json_data.keys())[:10],
                )
            return []
        except (json.JSONDecodeError, KeyError, TypeError, ValidationError) as e:
            logger.warning(f"Failed to extract edge cases: {e}")
            return []
