# Blueprint Structure and Purpose

## What is a Blueprint?

A **blueprint** is a **human-readable YAML configuration file** that defines a carrier's API structure. It serves as:

1. **Manual Configuration** - When PDF extraction isn't available or reliable
2. **Reference Documentation** - Human-readable carrier API specification
3. **Source of Truth** - Can be used to validate/extend LLM-extracted schemas
4. **Mapper Generation Input** - Can be used to auto-generate mapper code

## Blueprint vs Extracted Schema vs Universal Carrier Format

| Type | Format | Source | Purpose |
|------|-------|--------|---------|
| **Blueprint** | YAML | Manual (human-written) | Human-readable carrier config |
| **Extracted Schema** | JSON | LLM (from PDF) | Machine-extracted API schema |
| **Universal Carrier Format** | JSON | Both (validated) | Standardized format (Pydantic model) |

**Flow:**
```
Blueprint (YAML) ──┐
                   ├──→ Universal Carrier Format (JSON) ──→ Mapper ──→ Validated Output
Extracted Schema ──┘     (via loader/processor)
```

## Blueprint Structure

A blueprint should map 1:1 to the `UniversalCarrierFormat` Pydantic model, with minor differences:

### Required Fields (matches UniversalCarrierFormat)

```yaml
carrier:
  name: string              # Required - Carrier name
  base_url: string          # Required - Base API URL (must be valid URL)
  version: string           # Optional - API version
  description: string       # Optional - Description
  code: string              # Optional - Carrier code (blueprint-specific, not in UniversalCarrierFormat)

authentication:             # List of authentication methods (can be single object or list)
  - type: string            # Required - "api_key" | "bearer" | "basic" | "oauth2" | "custom"
    name: string            # Required - Method name
    description: string     # Optional - How to authenticate
    location: string        # Optional - "header" | "query" | "cookie" (default: "header")
    scheme: string          # Optional - Auth scheme (e.g., "Bearer")
    parameter_name: string  # Optional - Parameter name (e.g., "X-API-Key")

endpoints:                  # List of endpoints (at least 1 required)
  - path: string            # Required - Endpoint path (must start with /)
    method: string          # Required - HTTP method (GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS)
    summary: string         # Required - Short summary
    description: string     # Optional - Detailed description
    authentication_required: boolean  # Optional - Default: false
    tags: [string]          # Optional - List of tags
    
    request:                # Optional - Request schema
      content_type: string  # Optional - Default: "application/json"
      parameters:           # Optional - List of parameters
        - name: string      # Required - Parameter name
          type: string      # Required - "string" | "integer" | "number" | "boolean" | "array" | "object" | "date" | "datetime"
          location: string  # Required - "query" | "path" | "header" | "body" | "form_data"
          required: boolean # Optional - Default: false
          description: string  # Optional
          default: any       # Optional - Default value
          example: any       # Optional - Example value
          enum: [any]        # Optional - Allowed enum values
      body_schema: object   # Optional - JSON schema for request body
    
    responses:              # Optional - List of response schemas
      - status_code: int    # Required - HTTP status code (100-599)
        content_type: string # Optional - Default: "application/json"
        description: string # Optional - Response description
        body_schema: object # Optional - JSON schema for response body

rate_limits:                # Optional - List of rate limits
  - requests: int           # Required - Number of requests (must be > 0)
    period: string          # Required - Time period (e.g., "1 minute", "1 hour", "1 day")
    description: string     # Optional - Rate limit description

documentation_url: string   # Optional - Link to original documentation (must be valid URL)
```

### Differences from UniversalCarrierFormat

1. **`carrier.code`** - Blueprint-specific field (not in UniversalCarrierFormat)
   - Used for internal identification
   - Example: `"dhl_express"`, `"fedex"`

2. **Nested structure** - Blueprint uses `carrier:` wrapper
   - UniversalCarrierFormat has fields at top level
   - Loader will flatten this during conversion

3. **YAML vs JSON** - Blueprint is YAML for readability
   - UniversalCarrierFormat is JSON (Pydantic model)

4. **Authentication format** - Blueprint can have single object or list
   - Current `dhl_express.yaml` has single object: `authentication: { type: "api_key", ... }`
   - UniversalCarrierFormat expects: `authentication: List[AuthenticationMethod]`
   - Loader should normalize: convert single object to list `[{ type: "api_key", ... }]`

5. **Authentication `required` field** - Blueprint has `required: true` (not in AuthenticationMethod)
   - This is blueprint-specific metadata
   - Can be ignored during conversion or stored separately

## Example Blueprint

See `blueprints/dhl_express.yaml` for a complete example.

## Blueprint Validation Rules

When loading a blueprint, it should be validated against these rules:

1. **Required fields:**
   - `carrier.name` (non-empty string)
   - `carrier.base_url` (valid URL)
   - `endpoints` (at least 1 endpoint)

2. **Endpoint validation:**
   - `path` must start with `/`
   - `method` must be valid HTTP method
   - `summary` must be non-empty

3. **Parameter validation:**
   - `name` must be non-empty
   - `type` must be valid ParameterType
   - `location` must be valid ParameterLocation

4. **Response validation:**
   - `status_code` must be between 100-599

5. **Rate limit validation:**
   - `requests` must be > 0
   - `period` must be non-empty string

6. **URL validation:**
   - `base_url` and `documentation_url` must be valid URLs

## How Blueprints Are Used

1. **Manual Creation** - Developer writes YAML file based on carrier docs
2. **Loading** - `BlueprintLoader` reads and parses YAML
3. **Validation** - Validates structure and required fields
4. **Conversion** - Converts to `UniversalCarrierFormat` Pydantic model
5. **Usage** - Can be used to:
   - Generate mapper code
   - Validate extracted schemas
   - Serve as reference documentation
   - Initialize carrier integrations

## Next Steps

To build the blueprint system, we need:

1. **`src/blueprints/loader.py`** - Load YAML files
2. **`src/blueprints/validator.py`** - Validate blueprint structure
3. **`src/blueprints/converter.py`** - Convert blueprint → UniversalCarrierFormat
4. **`src/blueprints/processor.py`** - Main processor (orchestrates load → validate → convert)
5. **Tests** - Unit and integration tests for blueprint loading/processing
