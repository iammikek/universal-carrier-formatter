"""
FastAPI dependency injection for the API.

Provides get_settings and get_controller so route handlers can use Depends()
and tests can override via app.dependency_overrides.
"""

from typing import Optional

from src.controller import ApiController
from src.core.settings import Settings, get_settings as get_core_settings


def get_settings() -> Settings:
    """Return application settings (cached). Override in tests if needed."""
    return get_core_settings()


_controller: Optional[ApiController] = None


def get_controller() -> ApiController:
    """Return the API controller singleton. Override in tests via dependency_overrides."""
    global _controller
    if _controller is None:
        _controller = ApiController()
    return _controller
