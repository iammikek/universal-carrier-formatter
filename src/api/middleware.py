"""Request-ID and body-size middleware; shared request_id context and API logger."""

import json
import logging
import uuid
from contextvars import ContextVar
from typing import Any, Dict, Optional

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from src.core.config import MAX_CONVERT_BODY_BYTES, MAX_UPLOAD_BYTES

from .api_responses import error_response

# Request ID for structured logging (set by middleware)
request_id_ctx: ContextVar[Optional[str]] = ContextVar("request_id", default=None)


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
            return error_response(
                413,
                "payload_too_large",
                f"Request body must be at most {MAX_UPLOAD_BYTES} bytes.",
            )
        if path == "/convert" and cl > MAX_CONVERT_BODY_BYTES:
            return error_response(
                413,
                "payload_too_large",
                f"Request body must be at most {MAX_CONVERT_BODY_BYTES} bytes.",
            )
        return await call_next(request)
