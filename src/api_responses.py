"""Standard error envelope and response helpers for the API."""

from typing import Any, Dict, Optional

from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field


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


def error_response(
    status_code: int, code: str, message: str, details: Optional[Dict[str, Any]] = None
) -> JSONResponse:
    """Return a JSONResponse with the standard error envelope."""
    body = ErrorEnvelope(error=ErrorDetail(code=code, message=message, details=details))
    return JSONResponse(status_code=status_code, content=body.model_dump())
