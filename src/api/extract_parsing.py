"""
Parse POST /extract request (JSON or multipart) into ExtractInput.

Single place for content-type branching and validation; keeps the route thin.
"""

import json
from typing import Union

from fastapi import HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from src.api.api_responses import error_response
from src.api.middleware import _api_logger
from src.api.schemas.extract import ExtractFromTextRequest, ExtractInput
from src.core.config import MAX_EXTRACTED_TEXT_CHARS, MAX_UPLOAD_BYTES


async def parse_extract_request(request: Request) -> Union[ExtractInput, JSONResponse]:
    """
    Parse request body (JSON with extracted_text or multipart with file) and query params.

    Returns ExtractInput for success, or JSONResponse for validation error (422).
    Raises HTTPException for bad content-type, empty body, or size limit.
    """
    log = _api_logger()
    content_type = request.headers.get("content-type", "")
    file: Union[UploadFile, None] = None
    body: Union[ExtractFromTextRequest, None] = None

    if "application/json" in content_type:
        try:
            raw = await request.json()
            body = ExtractFromTextRequest.model_validate(raw)
        except json.JSONDecodeError as e:
            log.warning("extract json decode failed: %s", e)
            raise HTTPException(400, "Invalid JSON body.") from e
        except ValidationError as e:
            log.warning("extract body validation failed: %s", e)
            return error_response(
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

    pdf_content: Union[bytes, None] = None
    extracted_text: Union[str, None] = None
    pdf_filename: Union[str, None] = None

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
    return ExtractInput(
        pdf_content=pdf_content,
        extracted_text=extracted_text,
        pdf_filename=pdf_filename,
        async_mode=async_mode,
    )
