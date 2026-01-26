from typing import Any, Dict, Optional
from datetime import datetime
from ..core.schema import UniversalCarrierFormat


class DhlExpressMapper:
    """
    Mapper class to convert DHL Express API responses into the Universal Carrier Format.
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

        # Map tracking number
        tracking_number = carrier_response.get("trackingNumber")
        if tracking_number:
            universal_response["tracking_number"] = str(tracking_number)
        else:
            universal_response["tracking_number"] = None

        # Map status with fallback to None if unknown
        raw_status = carrier_response.get("status")
        universal_response["status"] = self.STATUS_MAPPING.get(raw_status, None)

        # Map current location (city and country)
        current_location = carrier_response.get("currentLocation", {})
        city = current_location.get("city")
        country = current_location.get("country")

        universal_response["current_location"] = {
            "city": city if city else None,
            "country": country if country else None,
        }

        # Map estimated delivery date with parsing and fallback
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
            # The format is expected to be ISO date (YYYY-MM-DD)
            parsed_date = datetime.strptime(date_str, "%Y-%m-%d")
            return parsed_date.strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            return None

    def map_carrier_schema(self) -> UniversalCarrierFormat:
        """
        Maps the DHL Express carrier schema to the UniversalCarrierFormat schema object.

        Returns:
            UniversalCarrierFormat: The mapped schema object.
        """
        # Construct the UniversalCarrierFormat object based on the provided schema
        # This is a simplified example assuming UniversalCarrierFormat accepts these fields.
        # Adjust according to actual UniversalCarrierFormat implementation.

        schema = UniversalCarrierFormat(
            name="DHL Express",
            base_url="https://api.dhl.com/",
            version="v1",
            description="DHL Express API integration blueprint",
            endpoints=[
                {
                    "path": "/tracking/v1/track",
                    "method": "GET",
                    "summary": "Track shipment",
                    "description": "Track a DHL Express shipment by tracking number",
                    "request": {
                        "content_type": "application/json",
                        "body_schema": None,
                        "parameters": [
                            {
                                "name": "trackingNumber",
                                "type": "string",
                                "location": "query",
                                "required": True,
                                "description": "DHL Express tracking number",
                                "default_value": None,
                                "example": "1234567890",
                                "enum_values": None,
                            }
                        ],
                    },
                    "responses": [
                        {
                            "status_code": 200,
                            "content_type": "application/json",
                            "body_schema": {
                                "type": "object",
                                "properties": {
                                    "trackingNumber": {"type": "string"},
                                    "status": {
                                        "type": "string",
                                        "enum": ["in_transit", "delivered", "exception"],
                                    },
                                    "currentLocation": {
                                        "type": "object",
                                        "properties": {
                                            "city": {"type": "string"},
                                            "country": {"type": "string"},
                                        },
                                    },
                                    "estimatedDelivery": {"type": "string", "format": "date"},
                                },
                            },
                            "description": "Successful tracking response",
                        }
                    ],
                    "authentication_required": True,
                    "tags": ["tracking"],
                }
            ],
            authentication=[
                {
                    "type": "api_key",
                    "name": "Api_Key Authentication",
                    "description": None,
                    "location": "header",
                    "scheme": None,
                    "parameter_name": "DHL-API-Key",
                }
            ],
            rate_limits=[
                {
                    "requests": 100,
                    "period": "1 minute",
                    "description": "100 requests per minute per API key",
                },
                {
                    "requests": 10000,
                    "period": "1 day",
                    "description": "10,000 requests per day per API key",
                },
            ],
            documentation_url="https://developer.dhl.com/api-reference/express",
            extracted_at="2026-01-26T17:15:39.961354",
        )
        return schema