"""
Centralized constants for LLM defaults and extraction/schema JSON keys.

Reduces drift and typos when the same keys or default values are used
across llm_extractor, extraction_pipeline, formatter, mapper_generator, and API.
"""

# ----- LLM defaults -----
DEFAULT_LLM_MODEL = "gpt-4.1-mini"
OPENAI_API_KEY_ENV = "OPENAI_API_KEY"
# Multi-provider: openai | anthropic (LangChain or similar)
LLM_PROVIDER_ENV = "LLM_PROVIDER"
DEFAULT_LLM_PROVIDER = "openai"
ANTHROPIC_API_KEY_ENV = "ANTHROPIC_API_KEY"
DEFAULT_ANTHROPIC_MODEL = "claude-3-5-haiku-20241022"

# ----- Extraction output (schema.json top-level keys) -----
KEY_SCHEMA = "schema"
KEY_FIELD_MAPPINGS = "field_mappings"
KEY_CONSTRAINTS = "constraints"
KEY_EDGE_CASES = "edge_cases"
KEY_EXTRACTION_METADATA = "extraction_metadata"
KEY_SCHEMA_VERSION = "schema_version"
KEY_GENERATOR_VERSION = "generator_version"

# ----- Universal Carrier Format / LLM response structure keys -----
KEY_AUTHENTICATION = "authentication"
KEY_RATE_LIMITS = "rate_limits"
KEY_ENDPOINTS = "endpoints"
KEY_RESPONSES = "responses"
KEY_STATUS_CODE = "status_code"
KEY_STATUS = "status"
KEY_REQUESTS = "requests"
KEY_LIMIT = "limit"
KEY_NAME = "name"

# ----- LLM unwrap: alternate keys the model might return -----
FIELD_MAPPINGS_ALT_KEYS = ("field_mappings", "fieldMappings", "mappings")
CONSTRAINTS_ALT_KEYS = ("constraints", "constraint", "rules")
EDGE_CASES_ALT_KEYS = ("edge_cases", "edgeCases")

# ----- Field mapping single-object keys -----
KEY_CARRIER_FIELD = "carrier_field"
KEY_UNIVERSAL_FIELD = "universal_field"

# ----- Chunking for very large PDFs (imp-4) -----
# When extracted text exceeds this length, split into chunks before sending to LLM.
# Typical model context ~128k tokens; ~4 chars/token → ~100k chars leaves room for prompt + response.
DEFAULT_MAX_CHARS_PER_LLM_CHUNK = 100_000
LLM_MAX_CHARS_PER_CHUNK_ENV = "LLM_MAX_CHARS_PER_CHUNK"
DEFAULT_LLM_CHUNK_OVERLAP_CHARS = (
    500  # Overlap between chunks to avoid cutting mid-sentence
)

# ----- Pipeline progress step names (used by extraction_pipeline + formatter CLI) -----
STEP_PARSE = "parse"
STEP_EXTRACT = "extract"
STEP_VALIDATE = "validate"
STEP_SAVE = "save"
