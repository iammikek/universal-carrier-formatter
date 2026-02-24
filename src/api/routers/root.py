"""Root and health endpoints."""

from typing import Dict

from fastapi import APIRouter, Depends

from src.api.dependencies import get_controller
from src.api.controller import ApiController

router = APIRouter(tags=["root"])


@router.get("/")
def root(
    controller: ApiController = Depends(get_controller),
) -> Dict[str, str]:
    """Service info and links to docs."""
    return controller.root()


@router.get("/health")
def health(
    controller: ApiController = Depends(get_controller),
) -> Dict[str, str]:
    """Health check for load balancers and orchestration."""
    return controller.health()
