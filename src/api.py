"""
HTTP API for the Universal Carrier Formatter service.

Exposes the formatter as a REST API so consumers can:
- Extract schema from PDF or extracted text (POST /extract)
- Convert messy carrier response to universal JSON (POST /convert)
- Read the service's OpenAPI spec (GET /openapi.json, GET /docs)

Production-ish guardrails: explicit request/response models, error envelope,
size limits, timeouts, request-id middleware, and JSON structured logging.
"""

import asyncio
import json
import logging
import tempfile
import uuid
from contextvars import ContextVar
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel, Field, ValidationError
from starlette.middleware.base import BaseHTTPMiddleware

from .core.config import (
    KEY_CONSTRAINTS,
    KEY_EDGE_CASES,
    KEY_EXTRACTION_METADATA,
    KEY_FIELD_MAPPINGS,
    KEY_GENERATOR_VERSION,
    KEY_SCHEMA,
    KEY_SCHEMA_VERSION,
)
from .core.schema import UniversalCarrierFormat
from .extraction_pipeline import ExtractionPipeline
from .mappers import CarrierRegistry
from .openapi_generator import generate_openapi

# ----- Limits (reject early: 413 payload too large, 422 validation) -----
MAX_UPLOAD_BYTES = 50 * 1024 * 1024  # 50 MB for PDF or form
MAX_EXTRACTED_TEXT_CHARS = 2_000_000  # 2M chars for extracted_text (JSON mode)
MAX_CONVERT_BODY_BYTES = 1 * 1024 * 1024  # 1 MB for /convert JSON
EXTRACT_TIMEOUT_SECONDS = 300  # 5 min for LLM extraction

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


# ----- Error envelope (standardized JSON) -----
class ErrorDetail(BaseModel):
    """Standard error payload for API responses."""

    code: str = Field(
        ..., description="Machine-readable error code (e.g. bad_request, not_found)."
    )
    message: str = Field(..., description="Human-readable error message.")
    details: Optional[Dict[str, Any]] = Field(
        default=None, description="Optional extra context."
    )


class ErrorEnvelope(BaseModel):
    """Top-level error response: {"error": {...}}."""

    error: ErrorDetail


def _error_response(
    status_code: int, code: str, message: str, details: Optional[Dict[str, Any]] = None
) -> JSONResponse:
    """Return a JSONResponse with the standard error envelope."""
    body = ErrorEnvelope(error=ErrorDetail(code=code, message=message, details=details))
    return JSONResponse(status_code=status_code, content=body.model_dump())


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
    return _error_response(exc.status_code, code, exc.detail or "Request failed")


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


# Convert response: universal JSON shape varies; keep Dict[str, Any] for OpenAPI flexibility.


# ----- Endpoints -----


@app.get("/")
def root() -> Dict[str, str]:
    """Service info and links to docs."""
    return {
        "service": "Universal Carrier Formatter API",
        "docs": "/docs",
        "openapi": "/openapi.json",
        "carriers": "GET /carriers (list registered carrier slugs)",
        "extract": "POST /extract (PDF file or JSON with extracted_text)",
        "convert": "POST /convert (carrier response → universal JSON)",
        "carrier_openapi": "GET /carriers/{name}/openapi.yaml (OpenAPI for a carrier schema)",
    }


@app.get(
    "/carriers",
    response_model=List[str],
    summary="List registered carriers",
    description="Return slugs of registered carrier mappers (e.g. example, dhl, royal_mail). Use in POST /convert as the carrier parameter.",
)
def list_carriers() -> List[str]:
    """List carrier slugs available for conversion."""
    return CarrierRegistry.list_names()


@app.post(
    "/extract",
    response_model=ExtractResponse,
    summary="Extract schema from PDF or text",
    description=(
        "Submit a PDF file (multipart) or pre-extracted text (JSON). "
        "Returns schema, field_mappings, constraints, and edge_cases. "
        "Uses the LLM extraction pipeline; may take a few minutes for large docs. "
        f"Max upload: {MAX_UPLOAD_BYTES} bytes; max extracted_text length: {MAX_EXTRACTED_TEXT_CHARS} chars; timeout: {EXTRACT_TIMEOUT_SECONDS}s."
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
        if isinstance(file, UploadFile) and file.filename:
            pass
        else:
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

    pipeline = ExtractionPipeline()
    pdf_path: Optional[str] = None
    extracted_text_path: Optional[str] = None
    temp_pdf_path: Optional[str] = None

    if file is not None:
        pdf_content = await file.read()
        if not pdf_content:
            raise HTTPException(400, "Uploaded file is empty.")
        if len(pdf_content) > MAX_UPLOAD_BYTES:
            raise HTTPException(
                413,
                f"Uploaded file exceeds maximum size of {MAX_UPLOAD_BYTES} bytes.",
            )
        suffix = Path(file.filename or "upload.pdf").suffix or ".pdf"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as f:
            f.write(pdf_content)
            temp_pdf_path = f.name
            pdf_path = temp_pdf_path
        log.info("extract: processing uploaded PDF, size=%s", len(pdf_content))
    else:
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".txt", encoding="utf-8"
        ) as f:
            f.write(body.extracted_text)
            extracted_text_path = f.name
        pdf_path = "/tmp/input.pdf"
        log.info("extract: processing extracted_text, len=%s", len(body.extracted_text))

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode="w") as out:
            output_path = out.name

        def run_extraction() -> None:
            pipeline.process(
                pdf_path,
                output_path=output_path,
                generate_validators=False,
                extracted_text_path=extracted_text_path,
            )

        try:
            await asyncio.wait_for(
                asyncio.to_thread(run_extraction), timeout=EXTRACT_TIMEOUT_SECONDS
            )
        except asyncio.TimeoutError:
            log.warning("extract: timeout after %s seconds", EXTRACT_TIMEOUT_SECONDS)
            raise HTTPException(
                504,
                f"Extraction timed out after {EXTRACT_TIMEOUT_SECONDS} seconds. Try a smaller document or use async job (future).",
            ) from None

        with open(output_path, "r", encoding="utf-8") as f:
            result = json.load(f)
        Path(output_path).unlink(missing_ok=True)

        from .core.contract import SCHEMA_VERSION, get_generator_version

        return ExtractResponse(
            schema_version=result.get(KEY_SCHEMA_VERSION, SCHEMA_VERSION),
            generator_version=result.get(
                KEY_GENERATOR_VERSION, get_generator_version()
            ),
            schema=result.get(KEY_SCHEMA, {}),
            field_mappings=result.get(KEY_FIELD_MAPPINGS, []),
            constraints=result.get(KEY_CONSTRAINTS, []),
            edge_cases=result.get(KEY_EDGE_CASES, []),
            extraction_metadata=result.get(KEY_EXTRACTION_METADATA),
        )
    except HTTPException:
        raise
    except (OSError, ValueError) as e:
        log.exception("extract failed: %s", e)
        raise HTTPException(500, f"Extraction failed: {e}") from e
    except Exception as e:
        log.exception("extract failed: %s", e)
        raise HTTPException(500, f"Extraction failed: {e}") from e
    finally:
        if extracted_text_path:
            Path(extracted_text_path).unlink(missing_ok=True)
        if temp_pdf_path:
            Path(temp_pdf_path).unlink(missing_ok=True)


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
    try:
        mapper = CarrierRegistry.get(req.carrier or "example")
        universal = mapper.map_tracking_response(req.carrier_response)
        return universal
    except KeyError as e:
        raise HTTPException(404, str(e)) from e
    except (ValueError, KeyError, TypeError) as e:
        raise HTTPException(400, f"Conversion failed: {e}") from e
    except Exception as e:
        raise HTTPException(400, f"Conversion failed: {e}") from e


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
    if name == "expected":
        path = Path(__file__).parent.parent / "examples" / "expected_output.json"
    else:
        path = Path(__file__).parent.parent / "output" / f"{name}_schema.json"
    if not path.exists():
        raise HTTPException(404, f"Schema not found for carrier: {name}")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    schema_data = data.get(KEY_SCHEMA, data)
    schema = UniversalCarrierFormat.model_validate(schema_data)
    spec = generate_openapi(schema)
    import io

    import yaml

    buf = io.StringIO()
    yaml.dump(spec, buf, default_flow_style=False, allow_unicode=True, sort_keys=False)
    return buf.getvalue()


@app.get("/health")
def health() -> Dict[str, str]:
    """Health check for load balancers and orchestration."""
    return {"status": "ok", "service": "universal-carrier-formatter"}
