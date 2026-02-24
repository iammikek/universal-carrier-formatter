"""Carriers listing and carrier OpenAPI spec endpoints."""

from typing import List

from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse

from src.api.dependencies import get_controller
from src.api.controller import ApiController

router = APIRouter(prefix="/carriers", tags=["carriers"])


@router.get(
    "",
    response_model=List[str],
    summary="List registered carriers",
    description="Return slugs of registered carrier mappers (e.g. example, dhl, royal_mail). Use in POST /convert as the carrier parameter.",
)
def list_carriers(
    controller: ApiController = Depends(get_controller),
) -> List[str]:
    """List carrier slugs available for conversion."""
    return controller.list_carriers()


@router.get(
    "/{name}/openapi.yaml",
    response_class=PlainTextResponse,
    summary="OpenAPI spec for a carrier schema",
    description="Generate and return OpenAPI 3 (YAML) for a carrier's schema by name.",
)
def carrier_openapi_yaml(
    name: str,
    controller: ApiController = Depends(get_controller),
) -> str:
    """
    Return openapi.yaml for the given carrier schema.

    Loads schema from examples/expected_output.json if name is 'expected',
    or from output/{name}_schema.json if present.
    """
    return controller.carrier_openapi_yaml(name)
