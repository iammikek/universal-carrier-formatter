"""Extract schema from PDF/text and poll async extract jobs."""

from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from src.api.dependencies import get_controller, get_settings
from src.api.extract_parsing import parse_extract_request
from src.api.schemas.extract import (
    ExtractJobFailedResponse,
    ExtractJobPendingResponse,
    ExtractResponse,
)
from src.controller import ApiController
from src.core.config import (
    MAX_EXTRACTED_TEXT_CHARS,
    MAX_UPLOAD_BYTES,
)

router = APIRouter(prefix="/extract", tags=["extract"])


@router.post(
    "",
    response_model=ExtractResponse,
    summary="Extract schema from PDF or text",
    description=(
        "Submit a PDF file (multipart) or pre-extracted text (JSON). "
        "Returns schema, field_mappings, constraints, and edge_cases. "
        "Uses the LLM extraction pipeline; may take a few minutes for large docs. "
        "Add ?async=1 to get 202 Accepted with job_id; poll GET /extract/jobs/{job_id} for result (avoids client timeout). "
        f"Max upload: {MAX_UPLOAD_BYTES} bytes; max extracted_text length: {MAX_EXTRACTED_TEXT_CHARS} chars; timeout: {get_settings().extract_timeout_seconds}s."
    ),
)
async def extract(
    request: Request,
    controller: ApiController = Depends(get_controller),
) -> ExtractResponse | JSONResponse:
    """
    Extract Universal Carrier Format schema from a PDF or from extracted text.

    - **multipart/form-data** with a **file** field: PDF file (max 50 MB).
    - **application/json** with **extracted_text**: pre-extracted text (max 2M chars).
    """
    parsed = await parse_extract_request(request)
    if isinstance(parsed, JSONResponse):
        return parsed
    result = await controller.extract(
        pdf_content=parsed.pdf_content,
        extracted_text=parsed.extracted_text,
        pdf_filename=parsed.pdf_filename,
        async_mode=parsed.async_mode,
    )
    if isinstance(result, JSONResponse):
        return result
    return ExtractResponse(**result)


@router.get(
    "/jobs/{job_id}",
    summary="Get async extract job status or result",
    description=(
        "Poll for the result of an async extraction (POST /extract?async=1). "
        "Returns 200 with full result when completed, 202 with status when still pending, "
        "200 with status and error when failed. Jobs are in-memory and lost on server restart."
    ),
    responses={
        200: {
            "description": "Job completed (ExtractResponse: schema_version, schema, field_mappings, etc.) or job failed (job_id, status: 'failed', error).",
            "model": ExtractJobFailedResponse,
        },
        202: {
            "description": "Job still pending.",
            "model": ExtractJobPendingResponse,
        },
        404: {
            "description": "Job not found (unknown job_id). Standard error envelope: { \"error\": { \"code\", \"message\", \"details\"? } }.",
        },
    },
)
async def get_extract_job(
    job_id: str,
    controller: ApiController = Depends(get_controller),
) -> Any:
    """
    Get status or result of an async extract job.

    - **200** and full ExtractResponse when completed
    - **202** and {job_id, status: "pending"} when still running
    - **200** and {job_id, status: "failed", error: "..."} when failed
    - **404** when job_id is unknown
    """
    return controller.get_extract_job(job_id)
