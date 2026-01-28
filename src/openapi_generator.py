"""
OpenAPI / Swagger generator from Universal Carrier Format schema.

Generates openapi.yaml or swagger.json from the Python Pydantic models
(UniversalCarrierFormat, Endpoint, RequestSchema, ResponseSchema, etc.)
so the code is the source of truth for documentation.

Usage:
    from src.openapi_generator import generate_openapi, write_openapi_yaml

    schema = UniversalCarrierFormat.model_validate(...)
    spec = generate_openapi(schema)
    write_openapi_yaml(spec, "output/openapi.yaml")

CLI:
    python -m src.openapi_generator output/schema.json -o output/openapi.yaml
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Union

import click

from .core.schema import UniversalCarrierFormat

OPENAPI_VERSION = "3.0.3"


def _sanitize_operation_id(summary: str, path: str, method: str) -> str:
    """Turn summary/path/method into a valid operationId (alphanumeric + underscore)."""
    base = summary or f"{path}_{method}".strip("/").replace("/", "_")
    safe = re.sub(r"[^a-zA-Z0-9_]", "_", base)
    return (safe or "operation").strip("_")[:64]


def _parameter_to_openapi(param: Union[Any, Dict[str, Any]]) -> Dict[str, Any]:
    """Convert Parameter (or dict) to OpenAPI parameter spec."""
    if isinstance(param, dict):
        p = param
        loc = (p.get("location") or "query").lower()
        if loc == "body":
            return {}  # OpenAPI 3 uses requestBody, not body param
    else:
        p = param.model_dump() if hasattr(param, "model_dump") else param
        loc = getattr(param, "location", None) or p.get("location", "query")
        if hasattr(loc, "value"):
            loc = loc.value
        loc = str(loc).lower()

    if loc == "body":
        return {}

    openapi_param: Dict[str, Any] = {
        "name": p.get("name", "param"),
        "in": "query" if loc == "form_data" else loc,
        "description": p.get("description"),
        "required": p.get("required", False),
        "schema": {
            "type": (
                (p.get("type") or "string").lower()
                if isinstance(p.get("type"), str)
                else getattr(p.get("type"), "value", "string")
            )
        },
        "style": "form" if loc == "query" else "simple",
    }
    if p.get("enum_values") is not None:
        openapi_param["schema"]["enum"] = p["enum_values"]
    if p.get("example") is not None:
        openapi_param["example"] = p["example"]
    if p.get("default_value") is not None:
        openapi_param["schema"]["default"] = p["default_value"]
    return openapi_param


def _request_to_openapi(request: Union[Any, Dict[str, Any], None]) -> Dict[str, Any]:
    """Convert RequestSchema to OpenAPI requestBody."""
    if request is None:
        return {}
    r = (
        request
        if isinstance(request, dict)
        else getattr(request, "model_dump", lambda: request)()
    )
    if callable(r):
        r = r()
    body_schema = r.get("body_schema")
    content_type = r.get("content_type") or "application/json"
    if not body_schema:
        return {}
    return {
        "description": "Request body",
        "required": True,
        "content": {
            content_type: {
                "schema": (
                    body_schema if isinstance(body_schema, dict) else {"type": "object"}
                )
            }
        },
    }


def _responses_to_openapi(
    responses: List[Union[Any, Dict[str, Any]]],
) -> Dict[str, Any]:
    """Convert ResponseSchema list to OpenAPI responses map."""
    out: Dict[str, Any] = {}
    for r in responses or []:
        item = (
            r
            if isinstance(r, dict)
            else (r.model_dump() if hasattr(r, "model_dump") else r)
        )
        if callable(item):
            continue
        code = item.get("status_code") or item.get("status", 200)
        code_str = str(int(code))
        desc = item.get("description") or f"HTTP {code}"
        ct = item.get("content_type") or "application/json"
        body = item.get("body_schema")
        out[code_str] = {
            "description": desc,
            "content": (
                {ct: {"schema": body if isinstance(body, dict) else {"type": "object"}}}
                if body is not None
                else {ct: {"schema": {"type": "object"}}}
            ),
        }
        if not out[code_str]["content"]:
            out[code_str]["content"] = {ct: {"schema": {"type": "object"}}}
    return out


def generate_openapi(
    schema: Union[UniversalCarrierFormat, Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Build an OpenAPI 3.x document from Universal Carrier Format (or its dict).

    Uses the Pydantic-backed schema as the source of truth. Output can be
    serialized to openapi.yaml or swagger.json.

    Args:
        schema: UniversalCarrierFormat instance or dict (e.g. from schema.json).
                If dict and has key "schema", that nested object is used.

    Returns:
        OpenAPI 3.0.3 document as a dict.
    """
    if isinstance(schema, dict) and "schema" in schema:
        schema = schema["schema"]
    if isinstance(schema, dict):
        data = schema
    else:
        data = schema.model_dump() if hasattr(schema, "model_dump") else schema

    base_url = str(data.get("base_url", "https://api.example.com")).rstrip("/")
    name = data.get("name", "Carrier API")
    version = data.get("version") or "1.0.0"
    description = data.get("description") or ""

    paths: Dict[str, Any] = {}
    for ep in data.get("endpoints", []):
        path = ep.get("path", "/")
        method = ep.get("method", "GET")
        if isinstance(method, dict) and "value" in method:
            method = method.get("value", "GET")
        # Normalize: "POST", "HttpMethod.POST" -> "post"
        method_str = str(method).upper()
        if "." in method_str:
            method_str = method_str.split(".")[-1]
        method_key = method_str.lower() if method_str else "get"

        if path not in paths:
            paths[path] = {}

        op_id = _sanitize_operation_id(ep.get("summary"), path, method_key)
        operation: Dict[str, Any] = {
            "operationId": op_id,
            "summary": ep.get("summary") or op_id,
            "description": ep.get("description") or "",
            "tags": ep.get("tags") or [],
        }

        # Parameters (query, path, header)
        request = ep.get("request")
        params: List[Dict[str, Any]] = []
        if request:
            for p in request.get("parameters") or []:
                po = _parameter_to_openapi(p)
                if po:
                    params.append(po)
        if params:
            operation["parameters"] = params

        # Request body
        req_body = _request_to_openapi(request)
        if req_body:
            operation["requestBody"] = req_body

        # Responses
        operation["responses"] = _responses_to_openapi(ep.get("responses") or [])
        if not operation["responses"]:
            operation["responses"] = {"200": {"description": "Default success"}}

        if ep.get("authentication_required"):
            operation["security"] = [{"carrierAuth": []}]

        paths[path][method_key] = operation

    # Security schemes from authentication
    auth_list = data.get("authentication") or []
    security_schemes: Dict[str, Any] = {}
    for i, a in enumerate(auth_list):
        auth = (
            a
            if isinstance(a, dict)
            else (a.model_dump() if hasattr(a, "model_dump") else a)
        )
        if callable(auth):
            continue
        scheme_name = "carrierAuth" if len(auth_list) == 1 else f"carrierAuth{i}"
        auth_type = (auth.get("type") or "custom").lower()
        if auth_type == "api_key":
            security_schemes[scheme_name] = {
                "type": "apiKey",
                "in": (auth.get("location") or "header").lower(),
                "name": auth.get("parameter_name") or "X-API-Key",
                "description": auth.get("description") or auth.get("name"),
            }
        elif auth_type == "bearer":
            security_schemes[scheme_name] = {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": auth.get("description") or auth.get("name"),
            }
        elif auth_type == "basic":
            security_schemes[scheme_name] = {
                "type": "http",
                "scheme": "basic",
                "description": auth.get("description") or auth.get("name"),
            }
        else:
            security_schemes[scheme_name] = {
                "type": "apiKey",
                "in": "header",
                "name": auth.get("parameter_name") or "Authorization",
                "description": auth.get("description") or auth.get("name"),
            }

    spec: Dict[str, Any] = {
        "openapi": OPENAPI_VERSION,
        "info": {
            "title": name,
            "version": version,
            "description": description or f"API for {name}",
        },
        "servers": [{"url": base_url, "description": name}],
        "paths": paths,
        "components": {"securitySchemes": security_schemes},
    }
    return spec


def write_openapi_yaml(spec: Dict[str, Any], path: Union[str, Path]) -> None:
    """Write OpenAPI spec to a YAML file."""
    import yaml

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(
            spec, f, default_flow_style=False, allow_unicode=True, sort_keys=False
        )


def write_openapi_json(spec: Dict[str, Any], path: Union[str, Path]) -> None:
    """Write OpenAPI spec to a JSON file (e.g. swagger.json)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(spec, f, indent=2, default=str)


def _cli_main(
    schema_file: Path,
    output: Path,
    fmt: str,
) -> None:
    """Load schema, generate OpenAPI, write to file."""
    with open(schema_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    raw = data.get("schema", data) if isinstance(data, dict) else data
    schema = UniversalCarrierFormat.model_validate(raw)
    spec = generate_openapi(schema)
    if output is None:
        output = schema_file.parent / "openapi.yaml"
    if fmt is None:
        fmt = "json" if str(output).lower().endswith(".json") else "yaml"
    if fmt == "yaml":
        write_openapi_yaml(spec, output)
    else:
        write_openapi_json(spec, output)
    click.echo(f"Wrote {fmt.upper()} to {output}")


if __name__ == "__main__":

    @click.command()
    @click.argument(
        "schema_file",
        type=click.Path(exists=True, path_type=Path),
        required=True,
    )
    @click.option(
        "-o",
        "output",
        type=click.Path(path_type=Path),
        default=None,
        help="Output path (default: schema dir / openapi.yaml)",
    )
    @click.option(
        "--format",
        "fmt",
        type=click.Choice(["yaml", "json"]),
        default=None,
        help="Output format (default: from -o extension, else yaml)",
    )
    def main(schema_file: Path, output: Path, fmt: str) -> None:
        """Generate openapi.yaml or swagger.json from Universal Carrier Format schema."""
        _cli_main(schema_file, output, fmt)

    main()
