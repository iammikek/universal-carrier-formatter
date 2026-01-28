"""
Core Universal Carrier Format Schema

This is the "Universal" part - the core schema that all carriers map to.
All carrier-specific responses are transformed to match this schema.

Uses Pydantic models for:
- Model definition
- Validation
- Type safety
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    field_validator,
    model_validator,
)


class HttpMethod(str, Enum):
    """HTTP Method enumeration."""

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


class ParameterLocation(str, Enum):
    """Parameter location in request."""

    QUERY = "query"  # Query string parameters
    PATH = "path"  # URL path parameters
    HEADER = "header"  # HTTP headers
    BODY = "body"  # Request body
    FORM_DATA = "form_data"  # Form data


class ParameterType(str, Enum):
    """Parameter data type."""

    STRING = "string"
    INTEGER = "integer"
    NUMBER = "number"  # Float/decimal
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"
    DATE = "date"
    DATETIME = "datetime"


class UniversalFieldNames:
    """
    Constants for universal field names.

    Use these in FIELD_MAPPING instead of strings to ensure consistency
    and prevent typos.

    Usage in mapper:
        FIELD_MAPPING = {
            "mailPieceId": UniversalFieldNames.TRACKING_NUMBER,
            "stat": UniversalFieldNames.STATUS,
        }
    """

    # Tracking fields
    TRACKING_NUMBER = "tracking_number"
    STATUS = "status"
    LAST_UPDATE = "last_update"
    CURRENT_LOCATION = "current_location"
    ESTIMATED_DELIVERY = "estimated_delivery"

    # Location fields
    CITY = "city"
    POSTAL_CODE = "postal_code"
    COUNTRY = "country"
    ADDRESS_LINE_1 = "address_line_1"
    ADDRESS_LINE_2 = "address_line_2"
    STATE = "state"

    # Origin/Destination
    ORIGIN_COUNTRY = "origin_country"
    DESTINATION_COUNTRY = "destination_country"

    # Events and history
    EVENTS = "events"
    EVENT_TYPE = "event_type"
    EVENT_DATETIME = "event_datetime"
    EVENT_DESCRIPTION = "event_description"
    EVENT_LOCATION = "event_location"

    # Delivery
    PROOF_OF_DELIVERY = "proof_of_delivery"
    DELIVERED_AT = "delivered_at"
    SIGNED_BY = "signed_by"

    # Shipment details
    WEIGHT = "weight"
    DIMENSIONS = "dimensions"
    LABEL_BASE64 = "label_base64"
    LABEL = "label"  # Alias for label_base64
    MANIFEST_ID = "manifest_id"
    MANIFEST_NUMBER = "manifest_number"  # Alias for manifest_id
    MANIFEST_LABEL = "manifest_label"
    SERVICE_NAME = "service_name"
    SHIPMENT_NUMBER = "shipment_number"

    # History and tracking
    HISTORY = "history"

    # Timestamps
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"

    # Additional fields
    CARRIER = "carrier"
    CARRIER_SERVICE = "carrier_service"
    COST = "cost"
    CURRENCY = "currency"


class Parameter(BaseModel):
    """
    API Parameter definition.

        public static function rules(): array
        {
            return [
                'name' => 'required|string',
                'type' => 'required|in:string,integer,number,boolean,array,object',
                'required' => 'boolean',
                'description' => 'nullable|string',
            ];
        }
    }
    """

    name: str = Field(..., description="Parameter name", min_length=1)
    type: ParameterType = Field(..., description="Parameter data type")
    location: ParameterLocation = Field(..., description="Where parameter appears")
    required: bool = Field(default=False, description="Is parameter required")
    description: Optional[str] = Field(None, description="Parameter description")
    default_value: Optional[Any] = Field(
        None, alias="default", description="Default value"
    )
    example: Optional[Any] = Field(None, description="Example value")
    enum_values: Optional[List[Any]] = Field(
        None, alias="enum", description="Allowed enum values"
    )

    @field_validator("name", mode="before")
    @classmethod
    def name_must_not_be_empty(cls, v):
        """Validate parameter name is not empty."""
        if not v or not v.strip():
            raise ValueError("Parameter name cannot be empty")
        return v.strip()

    model_config = ConfigDict(
        extra="allow",  # Preserve any extra keys from LLM extraction
        populate_by_name=True,  # Allow both 'default' and 'default_value'
        json_schema_extra={
            "example": {
                "name": "tracking_number",
                "type": "string",
                "location": "path",
                "required": True,
                "description": "Carrier tracking number",
                "example": "1Z999AA10123456784",
            }
        },
    )


class RequestSchema(BaseModel):
    """Request schema definition. Extra keys from LLM are preserved (extra='allow')."""

    content_type: str = Field(
        default="application/json", description="Request content type"
    )
    body_schema: Optional[Dict[str, Any]] = Field(
        None, description="JSON schema for request body"
    )
    parameters: List[Parameter] = Field(
        default_factory=list, description="Request parameters"
    )

    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={
            "example": {
                "content_type": "application/json",
                "body_schema": {
                    "type": "object",
                    "properties": {"tracking_number": {"type": "string"}},
                },
                "parameters": [],
            }
        },
    )


class ResponseSchema(BaseModel):
    """Response schema definition. Extra keys from LLM are preserved (extra='allow')."""

    status_code: int = Field(..., ge=100, le=599, description="HTTP status code")
    content_type: str = Field(
        default="application/json", description="Response content type"
    )
    body_schema: Optional[Dict[str, Any]] = Field(
        None, description="JSON schema for response body"
    )
    description: Optional[str] = Field(None, description="Response description")

    @field_validator("status_code", mode="before")
    @classmethod
    def validate_status_code(cls, v):
        """Validate status code is valid HTTP status (100-599)."""
        if not (100 <= v <= 599):
            raise ValueError("Status code must be between 100 and 599")
        return v

    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={
            "example": {
                "status_code": 200,
                "content_type": "application/json",
                "body_schema": {
                    "type": "object",
                    "properties": {
                        "tracking_number": {"type": "string"},
                        "status": {"type": "string"},
                    },
                },
                "description": "Successful tracking response",
            }
        },
    )


class Endpoint(BaseModel):
    """API Endpoint definition. Extra keys from LLM are preserved (extra='allow')."""

    path: str = Field(
        ..., description="API endpoint path (e.g., /api/v1/track)", min_length=1
    )
    method: HttpMethod = Field(..., description="HTTP method")
    summary: str = Field(..., description="Short endpoint summary", min_length=1)
    description: Optional[str] = Field(
        None, description="Detailed endpoint description"
    )
    request: Optional[RequestSchema] = Field(None, description="Request schema")
    responses: List[ResponseSchema] = Field(
        default_factory=list, description="Possible responses"
    )
    authentication_required: bool = Field(
        default=False, description="Does endpoint require auth"
    )
    tags: List[str] = Field(
        default_factory=list, description="Endpoint tags/categories"
    )

    @field_validator("path", mode="before")
    @classmethod
    def path_must_start_with_slash(cls, v):
        """Validate path format - must start with '/'."""
        if not v.startswith("/"):
            raise ValueError("Path must start with /")
        return v

    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={
            "example": {
                "path": "/api/v1/track",
                "method": "GET",
                "summary": "Track a shipment",
                "description": "Retrieve tracking information for a shipment",
                "authentication_required": True,
                "request": {
                    "parameters": [
                        {
                            "name": "tracking_number",
                            "type": "string",
                            "location": "path",
                            "required": True,
                        }
                    ]
                },
                "responses": [
                    {"status_code": 200, "description": "Successful tracking response"}
                ],
            }
        },
    )


class AuthenticationMethod(BaseModel):
    """Authentication method definition."""

    type: Literal["api_key", "bearer", "basic", "oauth2", "custom"] = Field(
        ..., description="Authentication type"
    )
    name: str = Field(..., description="Authentication method name")
    description: Optional[str] = Field(None, description="How to authenticate")
    location: Literal["header", "query", "cookie"] = Field(
        default="header", description="Where auth credential is sent"
    )
    scheme: Optional[str] = Field(None, description="Auth scheme (e.g., 'Bearer')")
    parameter_name: Optional[str] = Field(
        None, description="Parameter name (e.g., 'X-API-Key')"
    )

    @model_validator(mode="before")
    @classmethod
    def normalize_and_set_defaults(cls, data):
        """Normalize authentication data before validation."""
        if isinstance(data, dict):
            # Normalize type first
            auth_type = data.get("type", "custom")
            if auth_type:
                data["type"] = cls._normalize_auth_type(auth_type)

            # Generate name if missing
            if "name" not in data or not data.get("name"):
                auth_type = data.get("type", "custom")
                type_names = {
                    "api_key": "API Key Authentication",
                    "bearer": "Bearer Token Authentication",
                    "basic": "Basic Authentication",
                    "oauth2": "OAuth 2.0 Authentication",
                    "custom": "Custom Authentication",
                }
                data["name"] = type_names.get(
                    auth_type, f"{auth_type.title()} Authentication"
                )

        return data

    @classmethod
    def _normalize_auth_type(cls, v):
        """
        Normalize authentication types to allowed values.

        Maps non-standard types (like 'ws-security', 'soap', etc.) to 'custom'.
        """
        if not v:
            return "custom"

        v_lower = str(v).lower().strip()

        # Direct matches
        allowed_types = ["api_key", "bearer", "basic", "oauth2", "custom"]
        if v_lower in allowed_types:
            return v_lower

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

        # Check mappings
        if v_lower in type_mappings:
            return type_mappings[v_lower]

        # Check if it contains keywords
        if "bearer" in v_lower or "token" in v_lower:
            return "bearer"
        if "basic" in v_lower or "digest" in v_lower:
            return "basic"
        if "oauth" in v_lower or "oauth2" in v_lower:
            return "oauth2"
        if "api" in v_lower and "key" in v_lower:
            return "api_key"

        # Default to custom for unknown types
        return "custom"

    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={
            "example": {
                "type": "api_key",
                "name": "API Key Authentication",
                "description": "Include API key in X-API-Key header",
                "location": "header",
                "parameter_name": "X-API-Key",
            }
        },
    )


class RateLimit(BaseModel):
    """Rate limiting information."""

    requests: int = Field(..., gt=0, description="Number of requests allowed")
    period: str = Field(
        ..., description="Time period (e.g., '1 minute', '1 hour', '1 day')"
    )
    description: Optional[str] = Field(None, description="Rate limit description")

    @model_validator(mode="before")
    @classmethod
    def normalize_rate_limit(cls, data):
        """
        Normalize rate limit data before validation.

        Maps 'limit' field to 'requests' if present.
        """
        if isinstance(data, dict):
            # Map 'limit' to 'requests' if 'limit' exists but 'requests' doesn't
            if "limit" in data and "requests" not in data:
                data["requests"] = data.pop("limit")

        return data

    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={
            "example": {
                "requests": 100,
                "period": "1 minute",
                "description": "100 requests per minute",
            }
        },
    )


class UniversalCarrierFormat(BaseModel):
    """
    Universal Carrier Format - Main schema.

    This is the standardized format that all carrier API documentation
    will be converted into. extra='allow' so all LLM-extracted keys are preserved.
    """

    # Metadata
    name: str = Field(..., description="Carrier name", min_length=1)
    base_url: HttpUrl = Field(..., description="Base API URL")
    version: Optional[str] = Field(None, description="API version")
    description: Optional[str] = Field(None, description="Carrier API description")

    # API Definition
    endpoints: List[Endpoint] = Field(..., min_length=1, description="API endpoints")
    authentication: List[AuthenticationMethod] = Field(
        default_factory=list, description="Authentication methods"
    )
    rate_limits: List[RateLimit] = Field(
        default_factory=list, description="Rate limiting information"
    )

    # Metadata
    documentation_url: Optional[HttpUrl] = Field(
        None, description="Link to original documentation"
    )
    extracted_at: Optional[datetime] = Field(
        default_factory=datetime.now, description="When this was extracted"
    )

    @field_validator("name", mode="before")
    @classmethod
    def name_must_not_be_empty(cls, v):
        """Validate carrier name is not empty."""
        if not v or not v.strip():
            raise ValueError("Carrier name cannot be empty")
        return v.strip()

    @field_validator("endpoints", mode="before")
    @classmethod
    def must_have_at_least_one_endpoint(cls, v):
        """Validate at least one endpoint exists."""
        if not v or len(v) == 0:
            raise ValueError("Must have at least one endpoint")
        return v

    model_config = ConfigDict(
        extra="allow",
        # datetime serialization handled automatically by Pydantic v2
        json_schema_extra={
            "example": {
                "name": "Example Carrier",
                "base_url": "https://api.example.com",
                "version": "v1",
                "description": "Example carrier API",
                "endpoints": [
                    {
                        "path": "/api/v1/track",
                        "method": "GET",
                        "summary": "Track shipment",
                        "authentication_required": True,
                    }
                ],
                "authentication": [
                    {
                        "type": "api_key",
                        "name": "API Key",
                        "location": "header",
                        "parameter_name": "X-API-Key",
                    }
                ],
            }
        },
    )

    def to_openapi(self) -> Dict[str, Any]:
        """
        Generate OpenAPI 3.x (swagger) spec from this schema.

        The Python models are the source of truth; this returns a dict that can
        be written as openapi.yaml or swagger.json.

        Returns:
            OpenAPI 3.0.3 document as a dict.
        """
        from ..openapi_generator import generate_openapi

        return generate_openapi(self)

    def to_json_file(self, filepath: str, indent: int = 2) -> None:
        """Save schema to JSON file."""
        import json

        with open(filepath, "w") as f:
            json.dump(self.model_dump(by_alias=True), f, indent=indent, default=str)

    @classmethod
    def from_json_file(cls, filepath: str) -> "UniversalCarrierFormat":
        """Load schema from JSON file."""
        import json
        from pathlib import Path

        file_path = Path(filepath)
        if not file_path.exists():
            raise FileNotFoundError(f"Schema file not found: {filepath}")

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Handle wrapped format from extraction pipeline (has 'schema' key)
        if isinstance(data, dict) and "schema" in data:
            data = data["schema"]

        return cls(**data)
