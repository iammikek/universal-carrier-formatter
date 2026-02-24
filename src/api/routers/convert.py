"""Convert carrier response to universal JSON."""

from typing import Any, Dict

from fastapi import APIRouter, Depends

from src.api.dependencies import get_controller
from src.api.schemas import ConvertRequest
from src.api.controller import ApiController

router = APIRouter(prefix="/convert", tags=["convert"])


@router.post(
    "",
    response_model=Dict[str, Any],
    summary="Convert carrier response to universal JSON",
    description=(
        "Send a messy carrier API response; returns universal JSON. "
        "Uses the example mapper by default (trk_num → tracking_number, etc.)."
    ),
)
async def convert(
    req: ConvertRequest,
    controller: ApiController = Depends(get_controller),
) -> Dict[str, Any]:
    """
    Convert a non-standard carrier response to Universal Carrier Format JSON.

    Uses the mapper registered for the given carrier slug (default: example).
    """
    return controller.convert(req.carrier_response, req.carrier)
