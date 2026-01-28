"""
HTTP API for the Universal Carrier Formatter service.

Exposes the formatter as a REST API so consumers can:
- Extract schema from PDF or extracted text (POST /extract)
- Convert messy carrier response to universal JSON (POST /convert)
- Read the service's OpenAPI spec (GET /openapi.json, GET /docs)

FastAPI auto-generates OpenAPI 3 and Swagger UI from the Python models and routes,
so the code is the source of truth for the API documentation.
"""

import json
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, Request, UploadFile
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

from .core.schema import UniversalCarrierFormat
from .extraction_pipeline import ExtractionPipeline
from .mappers.example_mapper import ExampleMapper
from .openapi_generator import generate_openapi

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


# ----- Request/response models (documented in OpenAPI) -----


class ExtractFromTextRequest(BaseModel):
    """Request body when submitting pre-extracted PDF text (no file upload)."""

    extracted_text: str = Field(
        ...,
        description="Raw text extracted from the carrier PDF (same as sent to the LLM).",
        min_length=1,
    )


class ConvertRequest(BaseModel):
    """Request body for converting a carrier response to universal JSON."""

    carrier_response: Dict[str, Any] = Field(
        ...,
        description="Messy carrier API response (e.g. trk_num, stat, loc, est_del).",
    )
    carrier: Optional[str] = Field(
        default="example",
        description="Carrier identifier for mapper selection (default: example mapper).",
    )


# ----- Endpoints -----


@app.get("/")
def root() -> Dict[str, str]:
    """Service info and links to docs."""
    return {
        "service": "Universal Carrier Formatter API",
        "docs": "/docs",
        "openapi": "/openapi.json",
        "extract": "POST /extract (PDF file or JSON with extracted_text)",
        "convert": "POST /convert (carrier response → universal JSON)",
        "carrier_openapi": "GET /carriers/{name}/openapi.yaml (OpenAPI for a carrier schema)",
    }


@app.post(
    "/extract",
    response_model=Dict[str, Any],
    summary="Extract schema from PDF or text",
    description=(
        "Submit a PDF file (multipart) or pre-extracted text (JSON). "
        "Returns schema, field_mappings, constraints, and edge_cases. "
        "Uses the LLM extraction pipeline; may take a minute for large docs."
    ),
)
async def extract(request: Request) -> Dict[str, Any]:
    """
    Extract Universal Carrier Format schema from a PDF or from extracted text.

    - **multipart/form-data** with a **file** field: PDF file.
    - **application/json** with **extracted_text**: pre-extracted text (no PDF).
    """
    content_type = request.headers.get("content-type", "")
    file: Optional[UploadFile] = None
    body: Optional[ExtractFromTextRequest] = None

    if "application/json" in content_type:
        try:
            raw = await request.json()
            body = ExtractFromTextRequest.model_validate(raw)
        except Exception:
            raise HTTPException(400, "Invalid JSON or missing extracted_text.")
    elif "multipart/form-data" in content_type:
        form = await request.form()
        file = form.get("file")
        if isinstance(file, UploadFile) and file.filename:
            pass  # use file
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
        suffix = Path(file.filename or "upload.pdf").suffix or ".pdf"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as f:
            f.write(pdf_content)
            temp_pdf_path = f.name
            pdf_path = temp_pdf_path
    else:
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".txt", encoding="utf-8"
        ) as f:
            f.write(body.extracted_text)
            extracted_text_path = f.name
        pdf_path = (
            "/tmp/input.pdf"  # dummy; pipeline uses extracted_text_path for content
        )

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode="w") as out:
            output_path = out.name
        pipeline.process(
            pdf_path,
            output_path=output_path,
            generate_validators=False,
            extracted_text_path=extracted_text_path,
        )
        with open(output_path, "r", encoding="utf-8") as f:
            result = json.load(f)
        Path(output_path).unlink(missing_ok=True)
        return result
    except Exception as e:
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

    Uses the mapper built from the carrier schema (default: example mapper).
    """
    mapper = ExampleMapper()
    try:
        universal = mapper.map_tracking_response(req.carrier_response)
        return universal
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
    or from output/{name}_schema.json if present. The Python models generate the spec.
    """
    if name == "expected":
        path = Path(__file__).parent.parent / "examples" / "expected_output.json"
    else:
        path = Path(__file__).parent.parent / "output" / f"{name}_schema.json"
    if not path.exists():
        raise HTTPException(404, f"Schema not found for carrier: {name}")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    schema_data = data.get("schema", data)
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
