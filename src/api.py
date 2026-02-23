"""
HTTP API for the Universal Carrier Formatter service.

Exposes the formatter as a REST API so consumers can:
- Extract schema from PDF or extracted text (POST /extract)
- Convert messy carrier response to universal JSON (POST /convert)
- Read the service's OpenAPI spec (GET /openapi.json, GET /docs)

Production-ish guardrails: explicit request/response models, error envelope,
size limits, timeouts, request-id middleware, and JSON structured logging.
"""

import json
import logging
import uuid
from contextvars import ContextVar
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel, Field, ValidationError
from starlette.middleware.base import BaseHTTPMiddleware

from .api_responses import error_response as _error_response
from .controller import ApiController
from .core.settings import get_settings

# ----- Limits (reject early: 413 payload too large, 422 validation) -----
MAX_UPLOAD_BYTES = 50 * 1024 * 1024  # 50 MB for PDF or form
MAX_EXTRACTED_TEXT_CHARS = 2_000_000  # 2M chars for extracted_text (JSON mode)
MAX_CONVERT_BODY_BYTES = 1 * 1024 * 1024  # 1 MB for /convert JSON


# Request ID for structured logging (set by middleware)
request_id_ctx: ContextVar[Optional[str]] = ContextVar("request_id", default=None)


# ----- Structured logging (JSON with request_id) -----
class JsonRequestIdFormatter(logging.Formatter):
    """Format log records as JSON with request_id when present."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj: Dict[str, Any] = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        rid = request_id_ctx.get()
        if rid:
            log_obj["request_id"] = rid
        if record.exc_info:
            log_obj["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)


def _api_logger() -> logging.Logger:
    logger = logging.getLogger("universal_carrier_formatter.api")
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JsonRequestIdFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


# ----- App -----
app = FastAPI(
    title="Universal Carrier Formatter API",
    description=(
        "Extract carrier API schemas from PDFs, convert messy carrier responses "
        "to universal JSON, and generate OpenAPI/Swagger docs. The Python models "
        "are the source of truth; this API exposes the service over HTTP."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


# ----- Exception handlers (emit error envelope) -----
def _normalize_http_exception_detail(exc: HTTPException) -> tuple[str, Optional[Dict[str, Any]]]:
    """Ensure error envelope message is always a string; put non-string detail in details."""
    detail = exc.detail
    if isinstance(detail, str) and detail:
        return detail, None
    if isinstance(detail, dict):
        return "Request failed", detail
    if detail is not None:
        return "Request failed", {"detail": detail}
    return "Request failed", None


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    code = "error"
    if exc.status_code == 400:
        code = "bad_request"
    elif exc.status_code == 404:
        code = "not_found"
    elif exc.status_code == 413:
        code = "payload_too_large"
    elif exc.status_code == 422:
        code = "validation_error"
    elif exc.status_code >= 500:
        code = "internal_error"
    message, details = _normalize_http_exception_detail(exc)
    return _error_response(exc.status_code, code, message, details=details)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return _error_response(
        422,
        "validation_error",
        "Request validation failed.",
        details={"errors": exc.errors()},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    _api_logger().exception("Unhandled exception")
    return _error_response(
        500,
        "internal_error",
        "An unexpected error occurred.",
        details={"type": type(exc).__name__},
    )


# ----- Request-ID middleware -----
class RequestIdMiddleware(BaseHTTPMiddleware):
    """Set X-Request-ID on request/response and in context for logging."""

    async def dispatch(self, request: Request, call_next):
        rid = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        token = request_id_ctx.set(rid)
        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = rid
            return response
        finally:
            request_id_ctx.reset(token)


# ----- Body size limit middleware -----
class BodySizeLimitMiddleware(BaseHTTPMiddleware):
    """Reject requests with Content-Length over limit for /extract and /convert (413)."""

    async def dispatch(self, request: Request, call_next):
        if request.method != "POST":
            return await call_next(request)
        path = request.url.path.rstrip("/")
        content_length = request.headers.get("content-length")
        if not content_length:
            return await call_next(request)
        try:
            cl = int(content_length)
        except ValueError:
            return await call_next(request)
        if path == "/extract" and cl > MAX_UPLOAD_BYTES:
            return _error_response(
                413,
                "payload_too_large",
                f"Request body must be at most {MAX_UPLOAD_BYTES} bytes.",
            )
        if path == "/convert" and cl > MAX_CONVERT_BODY_BYTES:
            return _error_response(
                413,
                "payload_too_large",
                f"Request body must be at most {MAX_CONVERT_BODY_BYTES} bytes.",
            )
        return await call_next(request)


app.add_middleware(BodySizeLimitMiddleware)
app.add_middleware(RequestIdMiddleware)


# ----- Request/response models (documented in OpenAPI) -----


class ExtractFromTextRequest(BaseModel):
    """Request body when submitting pre-extracted PDF text (no file upload)."""

    extracted_text: str = Field(
        ...,
        description="Raw text extracted from the carrier PDF (same as sent to the LLM).",
        min_length=1,
        max_length=MAX_EXTRACTED_TEXT_CHARS,
    )


class ExtractResponse(BaseModel):
    """Response from POST /extract: schema_version, generator_version, schema, field_mappings, constraints, edge_cases."""

    model_config = {"populate_by_name": True}
    schema_version: str = Field(
        ..., description="Contract version of the schema format (semantic version)."
    )
    generator_version: str = Field(
        ...,
        description="Version of the tool that generated this (e.g. package version).",
    )
    schema_: Dict[str, Any] = Field(
        ...,
        alias="schema",
        description="Universal Carrier Format schema (name, endpoints, etc.).",
    )
    field_mappings: List[Any] = Field(
        default_factory=list, description="Field name mappings."
    )
    constraints: List[Any] = Field(
        default_factory=list, description="Business rules and constraints."
    )
    edge_cases: List[Any] = Field(
        default_factory=list, description="Route-specific edge cases."
    )
    extraction_metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="LLM config (model, temperature, top_p) and prompt_versions for reproducibility.",
    )


class ConvertRequest(BaseModel):
    """Request body for converting a carrier response to universal JSON."""

    carrier_response: Dict[str, Any] = Field(
        ...,
        description="Messy carrier API response (e.g. trk_num, stat, loc, est_del).",
    )
    carrier: Optional[str] = Field(
        default="example",
        description="Carrier slug for mapper selection (e.g. example, dhl, royal_mail). Use GET /carriers for list.",
    )


class JobAcceptedResponse(BaseModel):
    """Response when POST /extract is called with ?async=1 (202 Accepted)."""

    job_id: str = Field(
        ..., description="Unique job ID; poll GET /extract/jobs/{job_id} for result."
    )
    status: str = Field(..., description="Job status (pending until complete).")
    status_url: str = Field(..., description="URL to poll for status and result.")


# Convert response: universal JSON shape varies; keep Dict[str, Any] for OpenAPI flexibility.

# ----- Controller (endpoint logic) -----
_controller = ApiController()


# ----- Endpoints -----


@app.get("/")
def root() -> Dict[str, str]:
    """Service info and links to docs."""
    return _controller.root()


@app.get(
    "/carriers",
    response_model=List[str],
    summary="List registered carriers",
    description="Return slugs of registered carrier mappers (e.g. example, dhl, royal_mail). Use in POST /convert as the carrier parameter.",
)
def list_carriers() -> List[str]:
    """List carrier slugs available for conversion."""
    return _controller.list_carriers()


@app.post(
    "/extract",
    response_model=ExtractResponse,
    responses={
        202: {
            "model": JobAcceptedResponse,
            "description": "Accepted: extraction job queued (use ?async=1). Poll GET /extract/jobs/{job_id} for result.",
        }
    },
    summary="Extract schema from PDF or text",
    description=(
        "Submit a PDF file (multipart) or pre-extracted text (JSON). "
        "Returns schema, field_mappings, constraints, and edge_cases. "
        "Uses the LLM extraction pipeline; may take a few minutes for large docs. "
        "Add ?async=1 to get 202 Accepted with job_id; poll GET /extract/jobs/{job_id} for result (avoids client timeout). "
        f"Max upload: {MAX_UPLOAD_BYTES} bytes; max extracted_text length: {MAX_EXTRACTED_TEXT_CHARS} chars; timeout: {get_settings().extract_timeout_seconds}s."
    ),
)
async def extract(request: Request) -> ExtractResponse:
    """
    Extract Universal Carrier Format schema from a PDF or from extracted text.

    - **multipart/form-data** with a **file** field: PDF file (max 50 MB).
    - **application/json** with **extracted_text**: pre-extracted text (max 2M chars).
    """
    log = _api_logger()
    content_type = request.headers.get("content-type", "")
    file: Optional[UploadFile] = None
    body: Optional[ExtractFromTextRequest] = None

    if "application/json" in content_type:
        try:
            raw = await request.json()
            body = ExtractFromTextRequest.model_validate(raw)
        except json.JSONDecodeError as e:
            log.warning("extract json decode failed: %s", e)
            raise HTTPException(400, "Invalid JSON body.") from e
        except ValidationError as e:
            log.warning("extract body validation failed: %s", e)
            return _error_response(
                422,
                "validation_error",
                "Invalid or oversized extracted_text (max %s chars)."
                % MAX_EXTRACTED_TEXT_CHARS,
                details={"errors": e.errors()},
            )
        except ValueError as e:
            log.warning("extract body validation failed: %s", e)
            raise HTTPException(400, str(e)) from e
    elif "multipart/form-data" in content_type:
        form = await request.form()
        file = form.get("file")
        if not isinstance(file, UploadFile) or not file.filename:
            file = None
    else:
        raise HTTPException(
            400,
            "Send either a PDF file (multipart/form-data with 'file') or JSON body with extracted_text.",
        )

    if file is None and (body is None or not body.extracted_text):
        raise HTTPException(
            400,
            "Send either a PDF file (multipart) or JSON body with extracted_text.",
        )

    pdf_content: Optional[bytes] = None
    extracted_text: Optional[str] = None
    pdf_filename: Optional[str] = None

    if file is not None:
        pdf_content = await file.read()
        if not pdf_content:
            raise HTTPException(400, "Uploaded file is empty.")
        if len(pdf_content) > MAX_UPLOAD_BYTES:
            raise HTTPException(
                413,
                f"Uploaded file exceeds maximum size of {MAX_UPLOAD_BYTES} bytes.",
            )
        pdf_filename = file.filename
    else:
        extracted_text = body.extracted_text

    async_mode = request.query_params.get("async", "").lower() in ("1", "true", "yes")
    result = await _controller.extract(
        pdf_content=pdf_content,
        extracted_text=extracted_text,
        pdf_filename=pdf_filename,
        async_mode=async_mode,
    )

    if isinstance(result, JSONResponse):
        return result
    return ExtractResponse(**result)


@app.get(
    "/extract/jobs/{job_id}",
    summary="Get async extract job status or result",
    description=(
        "Poll for the result of an async extraction (POST /extract?async=1). "
        "Returns 200 with full result when completed, 202 with status when still pending, "
        "200 with status and error when failed. Jobs are in-memory and lost on server restart."
    ),
)
async def get_extract_job(job_id: str):
    """
    Get status or result of an async extract job.

    - **200** and full ExtractResponse when completed
    - **202** and {job_id, status: "pending"} when still running
    - **200** and {job_id, status: "failed", error: "..."} when failed
    - **404** when job_id is unknown
    """
    return _controller.get_extract_job(job_id)


@app.post(
    "/convert",
    response_model=Dict[str, Any],
    summary="Convert carrier response to universal JSON",
    description=(
        "Send a messy carrier API response; returns universal JSON. "
        "Uses the example mapper by default (trk_num → tracking_number, etc.)."
    ),
)
async def convert(req: ConvertRequest) -> Dict[str, Any]:
    """
    Convert a non-standard carrier response to Universal Carrier Format JSON.

    Uses the mapper registered for the given carrier slug (default: example).
    """
    return _controller.convert(req.carrier_response, req.carrier)


@app.get(
    "/carriers/{name}/openapi.yaml",
    response_class=PlainTextResponse,
    summary="OpenAPI spec for a carrier schema",
    description="Generate and return OpenAPI 3 (YAML) for a carrier's schema by name.",
)
async def carrier_openapi_yaml(name: str) -> str:
    """
    Return openapi.yaml for the given carrier schema.

    Loads schema from examples/expected_output.json if name is 'expected',
    or from output/{name}_schema.json if present.
    """
    return _controller.carrier_openapi_yaml(name)


@app.get("/health")
def health() -> Dict[str, str]:
    """Health check for load balancers and orchestration."""
    return _controller.health()
