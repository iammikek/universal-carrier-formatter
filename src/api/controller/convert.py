"""
Convert domain: carrier-specific response → Universal Carrier Format JSON.

Uses CarrierRegistry to resolve mapper and map_tracking_response.
"""

from typing import Any, Dict, Optional

from fastapi import HTTPException

from ...mappers import CarrierRegistry


class ConvertController:
    """Controller for carrier response → universal format conversion."""

    def convert(
        self, carrier_response: Dict[str, Any], carrier: Optional[str]
    ) -> Dict[str, Any]:
        """Convert a non-standard carrier response to Universal Carrier Format JSON."""
        try:
            mapper = CarrierRegistry.get(carrier or "example")
            universal = mapper.map_tracking_response(carrier_response)
            return universal
        except KeyError as e:
            raise HTTPException(404, str(e)) from e
        except (ValueError, KeyError, TypeError) as e:
            raise HTTPException(400, f"Conversion failed: {e}") from e
        except Exception as e:
            raise HTTPException(400, f"Conversion failed: {e}") from e
