"""Request/response schemas for extract endpoints."""

from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from src.core.config import MAX_EXTRACTED_TEXT_CHARS


@dataclass
class ExtractInput:
    """Parsed input for extract: either PDF bytes or extracted text, plus async flag."""

    pdf_content: Optional[bytes]
    extracted_text: Optional[str]
    pdf_filename: Optional[str]
    async_mode: bool


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


class JobAcceptedResponse(BaseModel):
    """Response when POST /extract is called with ?async=1 (202 Accepted)."""

    job_id: str = Field(
        ..., description="Unique job ID; poll GET /extract/jobs/{job_id} for result."
    )
    status: str = Field(..., description="Job status (pending until complete).")
    status_url: str = Field(..., description="URL to poll for status and result.")


# ----- GET /extract/jobs/{job_id} response shapes -----


class ExtractJobPendingResponse(BaseModel):
    """Response when job is still running (202)."""

    job_id: str = Field(..., description="Unique job ID.")
    status: Literal["pending"] = Field("pending", description="Job still running.")


class ExtractJobFailedResponse(BaseModel):
    """Response when job failed (200 with status and error)."""

    job_id: str = Field(..., description="Unique job ID.")
    status: Literal["failed"] = Field("failed", description="Job failed.")
    error: str = Field(..., description="Error message.")
