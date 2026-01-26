# How to Create a Blueprint

## What is a Blueprint?

A **blueprint** is a **YAML configuration file** for this Python project (NOT for Laravel). It defines a carrier's API structure in a human-readable format.

**Think of it like:**
- **Laravel equivalent:** A config file like `config/carriers.php` that defines carrier settings
- **Purpose:** Store carrier API configuration that can be loaded and used by the system

## What is a Blueprint Useful For?

### 1. **Manual Carrier Configuration**
When you don't have a PDF or the LLM extraction isn't reliable, you can manually write a blueprint based on carrier documentation.

### 2. **Reference Documentation**
A human-readable way to document a carrier's API structure that developers can easily read and understand.

### 3. **Mapper Generation** (Future)
Once we build mapper generation, blueprints can be used to auto-generate mapper code.

### 4. **Validation & Testing**
Can be used to validate that extracted schemas from PDFs are correct.

### 5. **Integration Initialization**
Can be loaded to initialize carrier integrations with the correct API structure.

## How to Create a Blueprint

### Step 1: Create a YAML File

Create a new file in `blueprints/` directory:

```bash
# Example: blueprints/fedex.yaml
touch blueprints/fedex.yaml
```

### Step 2: Fill in the Structure

Use the `dhl_express.yaml` as a template and fill in your carrier's information:

```yaml
# FedEx Blueprint
# YAML configuration for FedEx carrier integration

carrier:
  name: "FedEx"
  code: "fedex"
  base_url: "https://api.fedex.com"
  version: "v1"
  description: "FedEx API integration blueprint"

authentication:
  type: "bearer"
  location: "header"
  scheme: "Bearer"
  name: "OAuth 2.0 Bearer Token"
  description: "Include Bearer token in Authorization header"

endpoints:
  - path: "/track/v1/trackingnumbers"
    method: "GET"
    summary: "Track shipment"
    description: "Track a FedEx shipment by tracking number"
    authentication_required: true
    tags: ["tracking"]
    
    request:
      content_type: "application/json"
      parameters:
        - name: "trackingNumber"
          type: "string"
          location: "query"
          required: true
          description: "FedEx tracking number"
          example: "1234567890"
    
    responses:
      - status_code: 200
        content_type: "application/json"
        description: "Successful tracking response"
        body_schema:
          type: "object"
          properties:
            trackingNumber:
              type: "string"
            status:
              type: "string"
              enum: ["in_transit", "delivered", "exception"]

rate_limits:
  - requests: 50
    period: "1 minute"
    description: "50 requests per minute per API key"

documentation_url: "https://developer.fedex.com/api-reference"
```

### Step 3: Required Fields

At minimum, you need:

```yaml
carrier:
  name: "Carrier Name"      # Required
  base_url: "https://..."    # Required (valid URL)

endpoints:                   # Required (at least 1)
  - path: "/api/..."         # Required (must start with /)
    method: "GET"            # Required (GET, POST, etc.)
    summary: "Short desc"    # Required
```

### Step 4: Optional Fields

You can also include:

- `carrier.code` - Internal identifier (e.g., "fedex", "ups")
- `carrier.version` - API version
- `carrier.description` - Description
- `authentication` - Auth methods
- `rate_limits` - Rate limiting info
- `documentation_url` - Link to docs

## Example: Creating a Blueprint from Carrier Docs

Let's say you want to create a blueprint for "FastShip Courier":

### 1. Read Carrier Documentation

From their docs, you learn:
- Base URL: `https://api.fastship.com`
- Uses API key in header: `X-API-Key`
- Has tracking endpoint: `GET /v1/track?tracking_id={id}`
- Returns JSON with `tracking_id`, `status`, `location`

### 2. Create the Blueprint

```yaml
# FastShip Courier Blueprint
carrier:
  name: "FastShip Courier"
  code: "fastship"
  base_url: "https://api.fastship.com"
  version: "v1"
  description: "FastShip Courier API integration"

authentication:
  type: "api_key"
  location: "header"
  parameter_name: "X-API-Key"
  name: "API Key Authentication"

endpoints:
  - path: "/v1/track"
    method: "GET"
    summary: "Track shipment"
    description: "Track a FastShip shipment by tracking ID"
    authentication_required: true
    tags: ["tracking"]
    
    request:
      parameters:
        - name: "tracking_id"
          type: "string"
          location: "query"
          required: true
          description: "FastShip tracking ID"
    
    responses:
      - status_code: 200
        description: "Successful tracking response"
        body_schema:
          type: "object"
          properties:
            tracking_id:
              type: "string"
            status:
              type: "string"
            location:
              type: "string"

documentation_url: "https://docs.fastship.com/api"
```

## Is This Blueprint for Laravel?

**No!** This blueprint is for **this Python project** (Universal Carrier Formatter).

### Comparison:

| Aspect | Laravel | This Project |
|--------|---------|--------------|
| **Language** | PHP | Python |
| **Config Format** | PHP arrays or YAML | YAML |
| **Purpose** | Laravel app config | Carrier API structure |
| **Usage** | `config('carriers.fedex')` | Load → Convert to `UniversalCarrierFormat` |

### In Laravel, you might have:

```php
// config/carriers.php
return [
    'fedex' => [
        'api_key' => env('FEDEX_API_KEY'),
        'base_url' => 'https://api.fedex.com',
        'endpoints' => [...],
    ],
];
```

### In This Project:

```yaml
# blueprints/fedex.yaml
carrier:
  name: "FedEx"
  base_url: "https://api.fedex.com"
  # ... full API structure
```

The blueprint defines the **API structure**, not runtime configuration (like API keys).

## How Blueprints Are Used (Once We Build the Loader)

```python
# Future usage (not built yet):
from src.blueprints.loader import BlueprintLoader

# Load blueprint
loader = BlueprintLoader()
blueprint = loader.load("blueprints/fedex.yaml")

# Convert to Universal Carrier Format
universal_format = blueprint.to_universal_format()

# Use in system
# - Generate mapper code
# - Validate extracted schemas
# - Initialize carrier integration
```

## Summary

1. **What:** YAML file defining carrier API structure
2. **Why:** Manual configuration, documentation, future mapper generation
3. **How:** Create YAML file in `blueprints/` following the structure
4. **For:** This Python project (NOT Laravel)
5. **Template:** Use `blueprints/dhl_express.yaml` as a starting point
