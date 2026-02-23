"""
Extract domain: PDF/text → Universal Carrier Format schema, async job handling.

Encapsulates extraction pipeline usage, in-memory job store, and sync/async execution.
"""

import asyncio
import json
import logging
import tempfile
import uuid
from pathlib import Path
from typing import Any, Dict, Optional, Union

from fastapi import HTTPException
from fastapi.responses import JSONResponse

from ..core.config import (
    KEY_CONSTRAINTS,
    KEY_EDGE_CASES,
    KEY_EXTRACTION_METADATA,
    KEY_FIELD_MAPPINGS,
    KEY_GENERATOR_VERSION,
    KEY_SCHEMA,
    KEY_SCHEMA_VERSION,
)
from ..extraction_pipeline import ExtractionPipeline

# In-memory async extract jobs (lost on restart); cap to prevent unbounded growth
MAX_EXTRACT_JOBS = 1_000
_extract_jobs: Dict[str, Dict[str, Any]] = {}


def _extract_timeout_seconds() -> int:
    """Extraction timeout in seconds (env EXTRACT_TIMEOUT_SECONDS, default 300)."""
    from ..core.settings import get_settings

    return get_settings().extract_timeout_seconds


def _api_logger() -> logging.Logger:
    logger = logging.getLogger("universal_carrier_formatter.api")
    if not logger.handlers:
        handler = logging.StreamHandler()
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def _run_extract_job_sync(
    job_id: str,
    pdf_path: str,
    output_path: str,
    extracted_text_path: Optional[str],
    temp_pdf_path: Optional[str],
) -> None:
    """Run extraction (sync); update job store and cleanup temp files when done."""
    log = _api_logger()
    pipeline = ExtractionPipeline()
    try:
        pipeline.process(
            pdf_path,
            output_path=output_path,
            generate_validators=False,
            extracted_text_path=extracted_text_path,
        )
        with open(output_path, "r", encoding="utf-8") as f:
            result = json.load(f)
        from ..core.contract import SCHEMA_VERSION, get_generator_version

        _extract_jobs[job_id]["status"] = "completed"
        _extract_jobs[job_id]["result"] = {
            "schema_version": result.get(KEY_SCHEMA_VERSION, SCHEMA_VERSION),
            "generator_version": result.get(
                KEY_GENERATOR_VERSION, get_generator_version()
            ),
            "schema": result.get(KEY_SCHEMA, {}),
            "field_mappings": result.get(KEY_FIELD_MAPPINGS, []),
            "constraints": result.get(KEY_CONSTRAINTS, []),
            "edge_cases": result.get(KEY_EDGE_CASES, []),
            "extraction_metadata": result.get(KEY_EXTRACTION_METADATA),
        }
    except Exception as e:
        log.exception("extract job %s failed: %s", job_id, e)
        _extract_jobs[job_id]["status"] = "failed"
        _extract_jobs[job_id]["error"] = str(e)
    finally:
        Path(output_path).unlink(missing_ok=True)
        if extracted_text_path:
            Path(extracted_text_path).unlink(missing_ok=True)
        if temp_pdf_path:
            Path(temp_pdf_path).unlink(missing_ok=True)


async def _run_extract_job_async(
    job_id: str,
    pdf_path: str,
    output_path: str,
    extracted_text_path: Optional[str],
    temp_pdf_path: Optional[str],
) -> None:
    """Run extraction in thread pool with timeout; then update job store."""
    timeout_secs = _extract_timeout_seconds()
    try:
        await asyncio.wait_for(
            asyncio.to_thread(
                _run_extract_job_sync,
                job_id,
                pdf_path,
                output_path,
                extracted_text_path,
                temp_pdf_path,
            ),
            timeout=timeout_secs,
        )
    except asyncio.TimeoutError:
        _extract_jobs[job_id]["status"] = "failed"
        _extract_jobs[job_id][
            "error"
        ] = f"Extraction timed out after {timeout_secs} seconds."
        Path(output_path).unlink(missing_ok=True)
        if extracted_text_path:
            Path(extracted_text_path).unlink(missing_ok=True)
        if temp_pdf_path:
            Path(temp_pdf_path).unlink(missing_ok=True)


class ExtractController:
    """Controller for document extraction and async extract jobs."""

    async def extract(
        self,
        *,
        pdf_content: Optional[bytes] = None,
        extracted_text: Optional[str] = None,
        pdf_filename: Optional[str] = None,
        async_mode: bool = False,
    ) -> Union[Dict[str, Any], JSONResponse]:
        """
        Extract Universal Carrier Format schema from a PDF or from extracted text.
        Caller must pass either pdf_content or extracted_text (validated in extract router).
        Returns a dict for 200 (build ExtractResponse in router), or JSONResponse for 202.
        """
        log = _api_logger()
        pipeline = ExtractionPipeline()
        pdf_path: Optional[str] = None
        extracted_text_path: Optional[str] = None
        temp_pdf_path: Optional[str] = None

        if pdf_content is not None:
            suffix = Path(pdf_filename or "upload.pdf").suffix if pdf_filename else ".pdf"
            if not suffix:
                suffix = ".pdf"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as f:
                f.write(pdf_content)
                temp_pdf_path = f.name
                pdf_path = temp_pdf_path
            log.info("extract: processing uploaded PDF, size=%s", len(pdf_content))
        else:
            assert extracted_text is not None
            with tempfile.NamedTemporaryFile(
                mode="w", delete=False, suffix=".txt", encoding="utf-8"
            ) as f:
                f.write(extracted_text)
                extracted_text_path = f.name
            pdf_path = "/tmp/input.pdf"
            log.info("extract: processing extracted_text, len=%s", len(extracted_text))

        if async_mode:
            if len(_extract_jobs) >= MAX_EXTRACT_JOBS:
                raise HTTPException(
                    503,
                    f"Too many pending jobs (max {MAX_EXTRACT_JOBS}). Retry after existing jobs complete.",
                )
            with tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode="w") as out:
                output_path = out.name
            job_id = str(uuid.uuid4())
            _extract_jobs[job_id] = {"status": "pending", "result": None, "error": None}
            asyncio.create_task(
                _run_extract_job_async(
                    job_id, pdf_path, output_path, extracted_text_path, temp_pdf_path
                )
            )
            return JSONResponse(
                status_code=202,
                content={
                    "job_id": job_id,
                    "status": "pending",
                    "status_url": f"/extract/jobs/{job_id}",
                },
            )

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
                timeout_secs = _extract_timeout_seconds()
                await asyncio.wait_for(
                    asyncio.to_thread(run_extraction), timeout=timeout_secs
                )
            except asyncio.TimeoutError:
                log.warning("extract: timeout after %s seconds", timeout_secs)
                raise HTTPException(
                    504,
                    f"Extraction timed out after {timeout_secs} seconds. Try a smaller document or use POST /extract?async=1 and poll GET /extract/jobs/<job_id> for result.",
                ) from None

            with open(output_path, "r", encoding="utf-8") as f:
                result = json.load(f)
            Path(output_path).unlink(missing_ok=True)

            from ..core.contract import SCHEMA_VERSION, get_generator_version

            return {
                "schema_version": result.get(KEY_SCHEMA_VERSION, SCHEMA_VERSION),
                "generator_version": result.get(
                    KEY_GENERATOR_VERSION, get_generator_version()
                ),
                "schema": result.get(KEY_SCHEMA, {}),
                "field_mappings": result.get(KEY_FIELD_MAPPINGS, []),
                "constraints": result.get(KEY_CONSTRAINTS, []),
                "edge_cases": result.get(KEY_EDGE_CASES, []),
                "extraction_metadata": result.get(KEY_EXTRACTION_METADATA),
            }
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

    def get_extract_job(self, job_id: str) -> Union[Dict[str, Any], JSONResponse]:
        """
        Get status or result of an async extract job.
        Returns dict for 200 result, JSONResponse for 200 failed / 202 pending.
        """
        if job_id not in _extract_jobs:
            raise HTTPException(404, f"Job not found: {job_id}")
        job = _extract_jobs[job_id]
        status = job.get("status", "pending")
        if status == "completed":
            return job.get("result", {})
        if status == "failed":
            return JSONResponse(
                status_code=200,
                content={
                    "job_id": job_id,
                    "status": "failed",
                    "error": job.get("error", "Unknown error"),
                },
            )
        return JSONResponse(
            status_code=202,
            content={"job_id": job_id, "status": "pending"},
        )
