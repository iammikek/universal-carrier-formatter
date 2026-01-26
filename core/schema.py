"""
Core Universal Carrier Format Schema

Laravel Equivalent: app/Models/CarrierSchema.php, app/Models/Endpoint.php, etc.

This is the "Universal" part - the core schema that all carriers map to.
All carrier-specific responses are transformed to match this schema.

In Laravel, you'd have:
- CarrierSchema model (extends Model)
- Endpoint model (relationship to CarrierSchema)
- Request/Response models
- Validation rules in FormRequest classes

Here we use Pydantic models which combine:
- Model definition (like Eloquent models)
- Validation (like FormRequest validation)
- Type safety (like PHP type hints)
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, HttpUrl, validator


class HttpMethod(str, Enum):
    """
    HTTP Method enumeration.

    Laravel Equivalent:
    enum HttpMethod: string
    {
        case GET = 'GET';
        case POST = 'POST';
        case PUT = 'PUT';
        case DELETE = 'DELETE';
        case PATCH = 'PATCH';
    }
    """

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


class ParameterLocation(str, Enum):
    """
    Parameter location in request.

    Laravel Equivalent: enum ParameterLocation
    """

    QUERY = "query"  # Query string parameters
    PATH = "path"  # URL path parameters
    HEADER = "header"  # HTTP headers
    BODY = "body"  # Request body
    FORM_DATA = "form_data"  # Form data


class ParameterType(str, Enum):
    """
    Parameter data type.

    Laravel Equivalent: enum ParameterType
    """

    STRING = "string"
    INTEGER = "integer"
    NUMBER = "number"  # Float/decimal
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"
    DATE = "date"
    DATETIME = "datetime"


class Parameter(BaseModel):
    """
    API Parameter definition.

    Laravel Equivalent:
    class Parameter extends Model
    {
        protected $fillable = ['name', 'type', 'required', 'description'];

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

    @validator("name")
    def name_must_not_be_empty(cls, v):
        """
        Custom validator (like Laravel's validation rules).

        Laravel Equivalent:
        'name' => 'required|string|min:1'
        """
        if not v or not v.strip():
            raise ValueError("Parameter name cannot be empty")
        return v.strip()

    class Config:
        """Pydantic config (like Laravel model $casts, $fillable, etc.)"""

        allow_population_by_field_name = (
            True  # Allow both 'default' and 'default_value'
        )
        json_schema_extra = {
            "example": {
                "name": "tracking_number",
                "type": "string",
                "location": "path",
                "required": True,
                "description": "Carrier tracking number",
                "example": "1Z999AA10123456784",
            }
        }


class RequestSchema(BaseModel):
    """
    Request schema definition.

    Laravel Equivalent:
    class RequestSchema extends Model
    {
        protected $fillable = ['content_type', 'body_schema', 'parameters'];

        // In Laravel, you'd use FormRequest for validation
        // Here Pydantic handles both model and validation
    }
    """

    content_type: str = Field(
        default="application/json", description="Request content type"
    )
    body_schema: Optional[Dict[str, Any]] = Field(
        None, description="JSON schema for request body"
    )
    parameters: List[Parameter] = Field(
        default_factory=list, description="Request parameters"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "content_type": "application/json",
                "body_schema": {
                    "type": "object",
                    "properties": {"tracking_number": {"type": "string"}},
                },
                "parameters": [],
            }
        }


class ResponseSchema(BaseModel):
    """
    Response schema definition.

    Laravel Equivalent:
    class ResponseSchema extends Model
    {
        protected $fillable = ['status_code', 'content_type', 'body_schema'];
    }
    """

    status_code: int = Field(..., ge=100, le=599, description="HTTP status code")
    content_type: str = Field(
        default="application/json", description="Response content type"
    )
    body_schema: Optional[Dict[str, Any]] = Field(
        None, description="JSON schema for response body"
    )
    description: Optional[str] = Field(None, description="Response description")

    @validator("status_code")
    def validate_status_code(cls, v):
        """
        Validate status code is valid HTTP status.

        Laravel Equivalent:
        'status_code' => 'required|integer|between:100,599'
        """
        if not (100 <= v <= 599):
            raise ValueError("Status code must be between 100 and 599")
        return v

    class Config:
        json_schema_extra = {
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
        }


class Endpoint(BaseModel):
    """
    API Endpoint definition.

    Laravel Equivalent:
    class Endpoint extends Model
    {
        protected $fillable = [
            'path', 'method', 'summary', 'description',
            'request', 'responses', 'authentication_required'
        ];

        // Relationships
        public function carrierSchema()
        {
            return $this->belongsTo(CarrierSchema::class);
        }

        public function parameters()
        {
            return $this->hasMany(Parameter::class);
        }
    }
    """

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

    @validator("path")
    def path_must_start_with_slash(cls, v):
        """
        Validate path format.

        Laravel Equivalent:
        'path' => 'required|string|regex:/^\\/.+/'
        """
        if not v.startswith("/"):
            raise ValueError("Path must start with /")
        return v

    class Config:
        json_schema_extra = {
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
        }


class AuthenticationMethod(BaseModel):
    """
    Authentication method definition.

    Laravel Equivalent:
    class AuthenticationMethod extends Model
    {
        protected $fillable = ['type', 'name', 'description', 'location', 'scheme'];
    }
    """

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

    class Config:
        json_schema_extra = {
            "example": {
                "type": "api_key",
                "name": "API Key Authentication",
                "description": "Include API key in X-API-Key header",
                "location": "header",
                "parameter_name": "X-API-Key",
            }
        }


class RateLimit(BaseModel):
    """
    Rate limiting information.

    Laravel Equivalent:
    class RateLimit extends Model
    {
        protected $fillable = ['requests', 'period', 'description'];
    }
    """

    requests: int = Field(..., gt=0, description="Number of requests allowed")
    period: str = Field(
        ..., description="Time period (e.g., '1 minute', '1 hour', '1 day')"
    )
    description: Optional[str] = Field(None, description="Rate limit description")

    class Config:
        json_schema_extra = {
            "example": {
                "requests": 100,
                "period": "1 minute",
                "description": "100 requests per minute",
            }
        }


class UniversalCarrierFormat(BaseModel):
    """
    Universal Carrier Format - Main schema.

    This is the standardized format that all carrier API documentation
    will be converted into.

    Laravel Equivalent:
    class CarrierSchema extends Model
    {
        protected $fillable = [
            'name', 'base_url', 'version', 'description',
            'endpoints', 'authentication', 'rate_limits'
        ];

        // Relationships
        public function endpoints()
        {
            return $this->hasMany(Endpoint::class);
        }

        public function authenticationMethods()
        {
            return $this->hasMany(AuthenticationMethod::class);
        }

        // Validation
        public static function rules(): array
        {
            return [
                'name' => 'required|string|min:1',
                'base_url' => 'required|url',
                'version' => 'nullable|string',
                'endpoints' => 'required|array|min:1',
                'endpoints.*' => 'required|array',
            ];
        }
    }
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

    @validator("name")
    def name_must_not_be_empty(cls, v):
        """
        Validate carrier name.

        Laravel Equivalent:
        'name' => 'required|string|min:1'
        """
        if not v or not v.strip():
            raise ValueError("Carrier name cannot be empty")
        return v.strip()

    @validator("endpoints")
    def must_have_at_least_one_endpoint(cls, v):
        """
        Validate at least one endpoint exists.

        Laravel Equivalent:
        'endpoints' => 'required|array|min:1'
        """
        if not v or len(v) == 0:
            raise ValueError("Must have at least one endpoint")
        return v

    class Config:
        """Pydantic configuration (like Laravel model config)"""

        json_encoders = {
            datetime: lambda v: v.isoformat()  # Serialize datetime to ISO format
        }
        json_schema_extra = {
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
        }

    def to_json_file(self, filepath: str, indent: int = 2) -> None:
        """
        Save schema to JSON file.

        Laravel Equivalent:
        public function toJsonFile(string $filepath): void
        {
            file_put_contents($filepath, json_encode($this->toArray(), JSON_PRETTY_PRINT));
        }
        """
        import json

        with open(filepath, "w") as f:
            json.dump(self.dict(by_alias=True), f, indent=indent, default=str)

    @classmethod
    def from_json_file(cls, filepath: str) -> "UniversalCarrierFormat":
        """
        Load schema from JSON file.

        Laravel Equivalent:
        public static function fromJsonFile(string $filepath): self
        {
            $data = json_decode(file_get_contents($filepath), true);
            return self::create($data);
        }
        """
        import json

        with open(filepath, "r") as f:
            data = json.load(f)
        return cls(**data)
