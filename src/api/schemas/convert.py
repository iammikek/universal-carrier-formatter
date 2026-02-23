"""Request/response schemas for convert endpoint."""

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class ConvertRequest(BaseModel):
    """Request body for converting a carrier response to universal JSON."""

    carrier_response: Dict[str, Any] = Field(
        ...,
        description="Messy carrier API response (e.g. trk_num, stat, loc, est_del).",
    )
    carrier: Optional[str] = Field(
        default="example",
        description="Carrier slug for mapper selection (e.g. example, dhl, royal_mail). Use GET /carriers for list.",
    )
