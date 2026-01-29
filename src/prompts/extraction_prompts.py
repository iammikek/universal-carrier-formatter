"""
Extraction prompts for LLM schema, field mappings, constraints, and edge cases.

These prompts are used by llm_extractor to produce structured JSON from
carrier documentation. Variable placeholders: {pdf_text}, {carrier_name}.

Bump PROMPT_VERSION_* when prompt content or structure changes (for reproducibility).
"""

from typing import Dict

from langchain_core.prompts import ChatPromptTemplate

from ..core.config import (
    KEY_CONSTRAINTS,
    KEY_EDGE_CASES,
    KEY_FIELD_MAPPINGS,
    KEY_SCHEMA,
)

# Prompt version per group (bump when prompt content/structure changes)
PROMPT_VERSION_SCHEMA = "1.0"
PROMPT_VERSION_FIELD_MAPPINGS = "1.0"
PROMPT_VERSION_CONSTRAINTS = "1.0"
PROMPT_VERSION_EDGE_CASES = "1.0"


def get_prompt_versions() -> Dict[str, str]:
    """Return version for each prompt group (for extraction_metadata)."""
    return {
        KEY_SCHEMA: PROMPT_VERSION_SCHEMA,
        KEY_FIELD_MAPPINGS: PROMPT_VERSION_FIELD_MAPPINGS,
        KEY_CONSTRAINTS: PROMPT_VERSION_CONSTRAINTS,
        KEY_EDGE_CASES: PROMPT_VERSION_EDGE_CASES,
    }


# --- Schema extraction ---

SCHEMA_SYSTEM = """You are an expert API documentation parser. Your job is to extract structured API information from carrier documentation and convert it to a standardized Universal Carrier Format JSON schema.

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

SCHEMA_USER = """Extract the API schema from this carrier documentation:

{pdf_text}

Return a JSON object matching the Universal Carrier Format schema with:
- name: Carrier name
- base_url: Base API URL
- version: API version
- description: Brief description
- endpoints: Array of endpoint objects with path, method, request, responses
- authentication: Array of authentication methods
- rate_limits: Array of rate limit objects

RATE LIMITS REQUIREMENTS:
- Each rate limit object MUST have a "requests" field (number of requests allowed)
- Do NOT use "limit" - use "requests" instead
- Example: {{"requests": 100, "period": "1 minute", "description": "100 requests per minute"}}
- Common fields: "requests" (required), "period" (required), "description" (optional)

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


def get_schema_extraction_prompt() -> ChatPromptTemplate:
    """Return the ChatPromptTemplate for full schema extraction."""
    return ChatPromptTemplate.from_messages(
        [
            ("system", SCHEMA_SYSTEM),
            ("user", SCHEMA_USER),
        ]
    )


# --- Field mappings ---

FIELD_MAPPINGS_SYSTEM = "You are an expert at identifying field name mappings and validation rules in API documentation."

FIELD_MAPPINGS_USER = """From this {carrier_name} API documentation, extract field name mappings with validation metadata.

Look for:
- Response field names (e.g., "trk_num", "stat", "loc", "s_addr_1")
- Map them to universal field names (e.g., "tracking_number", "status", "current_location", "sender_address_line_1")
- Extract validation rules: required/optional, max/min length, data type, patterns, enum values

Return ONLY a JSON array at the top level (start with [ and end with ]). Do not wrap in an object with a key like "field_mappings".
Include ALL available validation metadata:
[
  {{
    "carrier_field": "s_addr_1",
    "universal_field": "sender_address_line_1",
    "description": "Sender Address Line 1",
    "required": true,
    "max_length": 50,
    "type": "string"
  }},
  {{
    "carrier_field": "trk_num",
    "universal_field": "tracking_number",
    "description": "Tracking number",
    "required": true,
    "min_length": 10,
    "max_length": 20,
    "type": "string",
    "pattern": "^[A-Z0-9]{{10,20}}$"
  }},
  {{
    "carrier_field": "stat",
    "universal_field": "status",
    "description": "Shipment status",
    "required": true,
    "type": "string",
    "enum_values": ["IN_TRANSIT", "DELIVERED", "PENDING"]
  }}
]

Fields to extract (include only if mentioned in documentation):
- carrier_field: REQUIRED - The carrier's field name
- universal_field: REQUIRED - The universal field name
- description: REQUIRED - Description of the field
- required: OPTIONAL - boolean, true if field is required
- max_length: OPTIONAL - integer, maximum character length
- min_length: OPTIONAL - integer, minimum character length
- type: OPTIONAL - string (string, integer, number, boolean, date, datetime, array, object)
- pattern: OPTIONAL - string, regex pattern for validation
- enum_values: OPTIONAL - array of strings, allowed values for the field

Documentation:
{pdf_text}"""


def get_field_mappings_prompt() -> ChatPromptTemplate:
    """Return the ChatPromptTemplate for field mappings extraction."""
    return ChatPromptTemplate.from_messages(
        [
            ("system", FIELD_MAPPINGS_SYSTEM),
            ("user", FIELD_MAPPINGS_USER),
        ]
    )


# --- Constraints ---

CONSTRAINTS_SYSTEM = "You are an expert at identifying business rules and constraints in API documentation."

CONSTRAINTS_USER = """Extract business rules and constraints from this API documentation.

Look for:
- Field validation rules (format, length, required/optional)
- Conditional rules (e.g., "if shipping to X, then Y")
- Unit conversions (grams vs kilograms)
- Format requirements (date formats, phone number formats)

Return a JSON array. Include optional allowed_values, max_length, min_length, or pattern when the docs specify them (so we can emit real validation code):
[
  {{"field": "weight", "rule": "Must be in grams if shipping to Germany", "type": "unit_conversion", "condition": "destination_country == 'DE'"}},
  {{"field": "LanguageCode", "rule": "Optional; supported codes include eng, dan, ita; default eng", "type": "enum", "allowed_values": ["eng", "dan", "ita"]}},
  {{"field": "MessageReference", "rule": "Length between 28 and 36 characters", "min_length": 28, "max_length": 36}}
]

Optional keys (use when documented): allowed_values (list of strings), max_length, min_length, pattern (regex string).

Documentation:
{pdf_text}"""


def get_constraints_prompt() -> ChatPromptTemplate:
    """Return the ChatPromptTemplate for constraints extraction."""
    return ChatPromptTemplate.from_messages(
        [
            ("system", CONSTRAINTS_SYSTEM),
            ("user", CONSTRAINTS_USER),
        ]
    )


# --- Edge cases ---

EDGE_CASES_SYSTEM = (
    "You are an expert at finding route-specific and conditional "
    "requirements in shipping and carrier API documentation."
)

EDGE_CASES_USER = """Scan this documentation and extract edge cases: route-specific
requirements, surcharges, restrictions, and special rules that apply only in
certain conditions or to certain routes.

Look for:
- Customs requirements (e.g. declarations, particular routes like EU → Canary Islands)
- Surcharges (remote area, fuel, peak season) with conditions and amounts
- Restrictions (hazardous goods, prohibited items, weight/size limits)
- Route-specific rules (country pairs, regions, postcode prefixes)
- Documentation references (section numbers, page numbers) when mentioned

Return a JSON array. Each object should have:
- type: string (e.g. "customs_requirement", "surcharge", "restriction")
- route: string or null (e.g. "EU → Canary Islands")
- requirement: string (what is required or restricted)
- documentation: string or null (e.g. "Section 4.2.3, page 87")
- condition: string or null (e.g. "remote_area")
- applies_to: array of strings or null (e.g. ["postcodes starting with 'IV', 'KW', 'PA'"])
- surcharge_amount: string or null (e.g. "£2.50") when type is surcharge

Example:
[
  {{"type": "customs_requirement", "route": "EU → Canary Islands", "requirement": "Customs declaration required", "documentation": "Section 4.2.3, page 87", "condition": null, "applies_to": null, "surcharge_amount": null}},
  {{"type": "surcharge", "route": null, "requirement": "Remote area surcharge", "documentation": null, "condition": "remote_area", "applies_to": ["postcodes starting with 'IV', 'KW', 'PA'"], "surcharge_amount": "£2.50"}}
]

Documentation:
{pdf_text}"""


def get_edge_cases_prompt() -> ChatPromptTemplate:
    """Return the ChatPromptTemplate for edge cases extraction."""
    return ChatPromptTemplate.from_messages(
        [
            ("system", EDGE_CASES_SYSTEM),
            ("user", EDGE_CASES_USER),
        ]
    )
