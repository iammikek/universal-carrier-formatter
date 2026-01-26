from typing import Any, Dict, Optional
from datetime import datetime
from ..core.schema import UniversalCarrierFormat


class DhlExpressMapper:
    """
    Mapper class to transform DHL Express API responses into the Universal Carrier Format.
    """

    FIELD_MAPPING = {
        "trackingNumber": "tracking_number",
        "status": "status",
        "currentLocation.city": "current_location.city",
        "currentLocation.country": "current_location.country",
        "estimatedDelivery": "estimated_delivery",
    }

    STATUS_MAPPING = {
        "in_transit": "in_transit",
        "delivered": "delivered",
        "exception": "exception",
    }

    def map_tracking_response(self, carrier_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Maps the DHL Express tracking API response to the Universal Carrier Format.

        Args:
            carrier_response (Dict[str, Any]): The raw response from DHL Express API.

        Returns:
            Dict[str, Any]: The mapped response in Universal Carrier Format.
        """
        universal_response: Dict[str, Any] = {}

        # Extract tracking number
        tracking_number = carrier_response.get("trackingNumber")
        if tracking_number:
            universal_response["tracking_number"] = tracking_number
        else:
            universal_response["tracking_number"] = None

        # Map status with fallback to None if unknown
        raw_status = carrier_response.get("status")
        universal_response["status"] = self.STATUS_MAPPING.get(raw_status, None)

        # Map current location
        current_location = carrier_response.get("currentLocation", {})
        city = current_location.get("city")
        country = current_location.get("country")

        universal_response["current_location"] = {
            "city": city if city else None,
            "country": country if country else None,
        }

        # Parse estimated delivery date safely
        estimated_delivery_raw = carrier_response.get("estimatedDelivery")
        universal_response["estimated_delivery"] = self._parse_date(estimated_delivery_raw)

        return universal_response

    def _parse_date(self, date_str: Optional[str]) -> Optional[str]:
        """
        Parses a date string in ISO format and returns it in YYYY-MM-DD format.
        Returns None if parsing fails or input is None.

        Args:
            date_str (Optional[str]): Date string to parse.

        Returns:
            Optional[str]: Formatted date string or None.
        """
        if not date_str:
            return None
        try:
            dt = datetime.fromisoformat(date_str)
            return dt.date().isoformat()
        except (ValueError, TypeError):
            return None

    def map_carrier_schema(self, carrier_schema: Dict[str, Any]) -> UniversalCarrierFormat:
        """
        Maps the DHL Express carrier schema to the UniversalCarrierFormat schema.

        Args:
            carrier_schema (Dict[str, Any]): The carrier-specific schema.

        Returns:
            UniversalCarrierFormat: The mapped universal carrier format schema.
        """
        # This is a stub implementation assuming UniversalCarrierFormat can be constructed from dict
        # Adjust according to actual UniversalCarrierFormat implementation
        try:
            return UniversalCarrierFormat(**carrier_schema)
        except Exception as e:
            raise ValueError(f"Failed to map carrier schema: {e}") from e