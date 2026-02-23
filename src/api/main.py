"""
FastAPI app: exception handlers, middleware, and router registration.

Single entry point for the Universal Carrier Formatter HTTP API.
"""

from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.api.api_responses import error_response
from src.api.middleware import (
    BodySizeLimitMiddleware,
    RequestIdMiddleware,
    _api_logger,
)
from src.api.routers import (
    carriers_router,
    convert_router,
    extract_router,
    root_router,
)


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
    return error_response(exc.status_code, code, message, details=details)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return error_response(
        422,
        "validation_error",
        "Request validation failed.",
        details={"errors": exc.errors()},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    _api_logger().exception("Unhandled exception")
    return error_response(
        500,
        "internal_error",
        "An unexpected error occurred.",
        details={"type": type(exc).__name__},
    )


app.add_middleware(BodySizeLimitMiddleware)
app.add_middleware(RequestIdMiddleware)

app.include_router(root_router)
app.include_router(carriers_router)
app.include_router(extract_router)
app.include_router(convert_router)
