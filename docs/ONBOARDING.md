# Onboarding New Carriers

This guide explains how to onboard a new carrier into the Universal Carrier Formatter system.

## Overview

Onboarding a new carrier involves three main steps:

1. **Parse Carrier Documentation** - Extract API schema from PDF
2. **Create Mapper** - Transform carrier-specific responses to universal format
3. **Create Blueprint** - Define carrier configuration and integration logic

## Step-by-Step Process

### Step 1: Parse Carrier Documentation

If you have a PDF with the carrier's API documentation:

```bash
# Parse the PDF to extract structured schema
python -m src.formatter --input examples/new_carrier.pdf --output blueprints/new_carrier_schema.json
```

This generates a Universal Carrier Format JSON schema that describes the carrier's API.

### Step 2: Create Mapper

Create a mapper file in `mappers/` that transforms the carrier's messy response format to universal format.

**Example: `mappers/new_carrier.py`**

```python
"""
New Carrier Mapper

Maps New Carrier's API responses to Universal Carrier Format.
"""

from typing import Any, Dict

from core.schema import UniversalCarrierFormat


class NewCarrierMapper:
    """
    Maps New Carrier API responses to Universal Carrier Format.
    """

    def map(self, carrier_response: Dict[str, Any]) -> UniversalCarrierFormat:
        """
        Transform carrier response to Universal Carrier Format.

        Args:
            carrier_response: Raw carrier API response dictionary

        Returns:
            UniversalCarrierFormat: Standardized carrier format
        """
        return UniversalCarrierFormat(
            name="New Carrier",
            base_url=carrier_response.get("api_url", "https://api.newcarrier.com"),
            version=carrier_response.get("version", "v1"),
            description=carrier_response.get("description", "New Carrier API"),
            endpoints=self._map_endpoints(carrier_response.get("endpoints", [])),
            authentication=self._map_authentication(carrier_response.get("auth", {})),
            rate_limits=self._map_rate_limits(carrier_response.get("rate_limits", [])),
            documentation_url=carrier_response.get("docs_url"),
        )

    def _map_endpoints(self, carrier_endpoints: list) -> list:
        """Map carrier endpoints to universal format."""
        # Transform carrier-specific endpoint structure
        # to Universal Carrier Format endpoint structure
        universal_endpoints = []
        
        for endpoint in carrier_endpoints:
            # Example transformation:
            # carrier: {"path": "/track", "method": "GET", "tracking_param": "id"}
            # universal: {"path": "/api/v1/track/{tracking_number}", "method": "GET", ...}
            universal_endpoints.append({
                "path": f"/api/v1{endpoint.get('path', '')}",
                "method": endpoint.get("method", "GET"),
                "summary": endpoint.get("summary", ""),
                # ... map other fields
            })
        
        return universal_endpoints

    def _map_authentication(self, carrier_auth: Dict[str, Any]) -> list:
        """Map carrier authentication to universal format."""
        # Transform carrier auth structure to universal format
        return []

    def _map_rate_limits(self, carrier_limits: list) -> list:
        """Map carrier rate limits to universal format."""
        # Transform carrier rate limit structure to universal format
        return []
```

**Key Mapping Tasks:**

1. **Field Name Mapping**
   - Map carrier field names to universal field names
   - Example: `trk_num` → `tracking_number`, `stat` → `status`

2. **Data Format Normalization**
   - Normalize status values (`IN_TRANSIT` → `in_transit`)
   - Standardize date formats
   - Convert units (grams ↔ kilograms)

3. **Structure Transformation**
   - Flatten or restructure nested objects
   - Add missing required fields
   - Handle optional fields

### Step 3: Create Blueprint

Create a YAML blueprint file in `blueprints/` that defines the carrier's configuration.

**Example: `blueprints/new_carrier.yaml`**

```yaml
# New Carrier Blueprint
# YAML configuration for New Carrier integration

carrier:
  name: "New Carrier"
  code: "new_carrier"
  base_url: "https://api.newcarrier.com"
  version: "v1"
  description: "New Carrier API integration blueprint"

authentication:
  type: "api_key"
  location: "header"
  parameter_name: "X-API-Key"
  required: true

endpoints:
  - path: "/api/v1/track"
    method: "GET"
    summary: "Track shipment"
    description: "Track a shipment by tracking number"
    authentication_required: true
    tags: ["tracking"]
    
    request:
      content_type: "application/json"
      parameters:
        - name: "tracking_number"
          type: "string"
          location: "query"
          required: true
          description: "Tracking number"
    
    responses:
      - status_code: 200
        content_type: "application/json"
        description: "Successful tracking response"

rate_limits:
  - requests: 100
    period: "1 minute"
    description: "100 requests per minute per API key"

documentation_url: "https://docs.newcarrier.com/api"
```

### Step 4: Test the Integration

Create tests to verify the mapper works correctly:

**Example: `tests/unit/test_new_carrier_mapper.py`**

```python
"""
Tests for New Carrier Mapper.
"""

import pytest

from mappers.new_carrier import NewCarrierMapper


@pytest.mark.unit
class TestNewCarrierMapper:
    """Test New Carrier mapper."""

    def test_maps_tracking_response(self):
        """Test mapping tracking response."""
        mapper = NewCarrierMapper()
        
        messy_response = {
            "trk_num": "1234567890",
            "stat": "IN_TRANSIT",
            "loc": {"city": "London", "postcode": "SW1A 1AA"},
        }
        
        result = mapper.map(messy_response)
        
        assert result.name == "New Carrier"
        # Add more assertions...

    def test_handles_missing_fields(self):
        """Test handling missing fields."""
        mapper = NewCarrierMapper()
        
        incomplete_response = {"trk_num": "1234567890"}
        
        result = mapper.map(incomplete_response)
        # Should handle gracefully
```

### Step 5: Validate Output

Use the validator to ensure the mapped output conforms to Universal Carrier Format:

```python
from core.validator import CarrierValidator
from mappers.new_carrier import NewCarrierMapper

# Get messy carrier response
messy_response = get_carrier_response()

# Map to universal format
mapper = NewCarrierMapper()
mapped_data = mapper.map(messy_response)

# Validate
validator = CarrierValidator()
validated = validator.validate(mapped_data.dict())

# Output is now perfect universal JSON ready for e-commerce checkout
print(validated.json())
```

## Complete Onboarding Example

Here's a complete example of onboarding a new carrier:

```python
# 1. Parse PDF (if available)
# python -m src.formatter --input new_carrier.pdf --output schema.json

# 2. Create mapper
from mappers.new_carrier import NewCarrierMapper
mapper = NewCarrierMapper()

# 3. Transform messy response
messy_response = {
    "trk_num": "1234567890",
    "stat": "IN_TRANSIT",
    "loc": {"city": "London", "postcode": "SW1A 1AA"},
    "est_del": "2026-01-30"
}

universal_format = mapper.map(messy_response)

# 4. Validate
from core.validator import CarrierValidator
validator = CarrierValidator()
validated = validator.validate(universal_format.dict())

# 5. Use in e-commerce checkout
# validated is now perfect universal JSON
```

## Best Practices

1. **Start with Examples** - Look at existing mappers (`dpd_mapper.py`, `royal_mail.py`) for patterns
2. **Test Edge Cases** - Handle missing fields, null values, unexpected formats
3. **Document Mapping Rules** - Add comments explaining why certain transformations are needed
4. **Validate Early** - Use the validator to catch issues early
5. **Update Blueprint** - Keep blueprint YAML in sync with actual API behavior

## Common Mapping Challenges

### Challenge 1: Inconsistent Field Names
**Solution:** Create a field mapping dictionary:
```python
FIELD_MAPPING = {
    "trk_num": "tracking_number",
    "stat": "status",
    "loc": "current_location",
    "est_del": "estimated_delivery"
}
```

### Challenge 2: Different Status Values
**Solution:** Create a status mapping:
```python
STATUS_MAPPING = {
    "IN_TRANSIT": "in_transit",
    "DELIVERED": "delivered",
    "EXCEPTION": "exception"
}
```

### Challenge 3: Missing Required Fields
**Solution:** Add defaults or derive from other fields:
```python
if "country" not in location:
    location["country"] = derive_country_from_postcode(location.get("postcode"))
```

## Next Steps After Onboarding

1. **Add Integration Tests** - Test with real API responses
2. **Document Edge Cases** - Note any carrier-specific quirks
3. **Update Documentation** - Add carrier to supported carriers list
4. **Monitor Usage** - Track how the mapper performs in production
