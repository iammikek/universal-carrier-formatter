"""
DPD Carrier Mapper

Laravel Equivalent: app/Services/Mappers/DpdMapper.php

Maps DPD's carrier-specific API responses to the Universal Carrier Format.
This handles the transformation from DPD's messy JSON structure to our clean schema.

Example messy DPD response:
{
  "trk_num": "1234567890",
  "stat": "IN_TRANSIT",
  "loc": {"city": "London", "postcode": "SW1A 1AA"},
  "est_del": "2026-01-30"
}

Transforms to Universal Carrier Format tracking response.

In Laravel, you'd have:
- A mapper service class
- Transformation methods
- Data mapping logic
"""

from datetime import datetime
from typing import Any, Dict

from core.schema import (
    Endpoint,
    HttpMethod,
    Parameter,
    ParameterLocation,
    ParameterType,
    UniversalCarrierFormat,
)


class DpdMapper:
    """
    Maps DPD API responses to Universal Carrier Format.

    Laravel Equivalent: app/Services/Mappers/DpdMapper.php

    Usage:
        mapper = DpdMapper()
        universal_format = mapper.map_tracking_response(dpd_response)
    """

    # Field name mappings: DPD field → Universal field
    FIELD_MAPPING = {
        "trk_num": "tracking_number",
        "stat": "status",
        "loc": "current_location",
        "est_del": "estimated_delivery",
        "postcode": "postal_code",
    }

    # Status value mappings: DPD status → Universal status
    STATUS_MAPPING = {
        "IN_TRANSIT": "in_transit",
        "DELIVERED": "delivered",
        "EXCEPTION": "exception",
        "PENDING": "pending",
        "OUT_FOR_DELIVERY": "out_for_delivery",
    }

    def map_tracking_response(
        self, dpd_response: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Transform messy DPD tracking response to universal format.

        Args:
            dpd_response: Raw DPD API tracking response

        Returns:
            Dict: Universal format tracking response

        Example:
            Input: {"trk_num": "1234567890", "stat": "IN_TRANSIT", ...}
            Output: {"tracking_number": "1234567890", "status": "in_transit", ...}
        """
        universal_response = {}

        # Map tracking number
        if "trk_num" in dpd_response:
            universal_response["tracking_number"] = dpd_response["trk_num"]

        # Map and normalize status
        if "stat" in dpd_response:
            dpd_status = dpd_response["stat"]
            universal_response["status"] = self.STATUS_MAPPING.get(
                dpd_status, dpd_status.lower()
            )

        # Map location
        if "loc" in dpd_response:
            location = dpd_response["loc"]
            universal_location = {}

            if "city" in location:
                universal_location["city"] = location["city"]

            if "postcode" in location:
                universal_location["postal_code"] = location["postcode"]

            # Derive country from postcode if missing
            if "country" not in location and "postcode" in location:
                universal_location["country"] = self._derive_country_from_postcode(
                    location["postcode"]
                )

            if universal_location:
                universal_response["current_location"] = universal_location

        # Map estimated delivery
        if "est_del" in dpd_response:
            # Normalize date format (DPD uses YYYY-MM-DD, we want ISO 8601)
            est_del = dpd_response["est_del"]
            try:
                # Try to parse and format as ISO 8601
                dt = datetime.strptime(est_del, "%Y-%m-%d")
                universal_response["estimated_delivery"] = dt.isoformat() + "Z"
            except ValueError:
                # If parsing fails, use as-is
                universal_response["estimated_delivery"] = est_del

        return universal_response

    def _derive_country_from_postcode(self, postcode: str) -> str:
        """
        Derive country code from postcode format.

        This is a simple heuristic - in production, you'd use a proper
        postcode validation library.

        Args:
            postcode: Postcode string

        Returns:
            str: ISO country code (e.g., "GB", "US")
        """
        # UK postcodes: alphanumeric pattern like SW1A 1AA, M1 1AA
        if len(postcode) >= 5 and postcode[0].isalpha():
            return "GB"

        # US ZIP codes: 5 digits or 5+4 format
        if postcode.replace("-", "").isdigit() and len(postcode.replace("-", "")) in [
            5,
            9,
        ]:
            return "US"

        # Default to GB for UK-style postcodes
        return "GB"

    def map_carrier_schema(
        self, dpd_schema: Dict[str, Any]
    ) -> UniversalCarrierFormat:
        """
        Transform DPD carrier schema to Universal Carrier Format.

        This maps the carrier's API documentation structure to our universal schema.

        Args:
            dpd_schema: DPD API schema/documentation structure

        Returns:
            UniversalCarrierFormat: Standardized carrier format
        """
        return UniversalCarrierFormat(
            name=dpd_schema.get("carrier", "DPD"),
            base_url=dpd_schema.get("api_url", "https://api.dpd.com"),
            version=dpd_schema.get("api_ver", "v1"),
            description=dpd_schema.get("description", "DPD API"),
            endpoints=self._map_endpoints(dpd_schema.get("endpoints", [])),
            authentication=self._map_authentication(
                dpd_schema.get("auth", {})
            ),
            rate_limits=self._map_rate_limits(
                dpd_schema.get("rate_limits", [])
            ),
            documentation_url=dpd_schema.get("docs_url"),
        )

    def _map_endpoints(self, dpd_endpoints: list) -> list:
        """Map DPD endpoints to universal format."""
        universal_endpoints = []

        for endpoint in dpd_endpoints:
            # Map HTTP method
            method_str = endpoint.get("method", "GET").upper()
            try:
                method = HttpMethod[method_str]
            except KeyError:
                method = HttpMethod.GET

            # Map path
            path = endpoint.get("path", "")
            if not path.startswith("/"):
                path = f"/{path}"

            # Map parameters
            parameters = []
            for param in endpoint.get("params", []):
                param_type_str = param.get("type", "string").lower()
                param_type = ParameterType.STRING
                if param_type_str == "integer":
                    param_type = ParameterType.INTEGER
                elif param_type_str == "number":
                    param_type = ParameterType.NUMBER
                elif param_type_str == "boolean":
                    param_type = ParameterType.BOOLEAN

                parameters.append(
                    Parameter(
                        name=param.get("name", ""),
                        type=param_type,
                        location=ParameterLocation.QUERY,
                        required=param.get("required", False),
                        description=param.get("description"),
                    )
                )

            universal_endpoints.append(
                Endpoint(
                    path=path,
                    method=method,
                    summary=endpoint.get("summary", ""),
                    description=endpoint.get("description", ""),
                    authentication_required=endpoint.get("auth_required", False),
                    request={"parameters": parameters} if parameters else None,
                )
            )

        return universal_endpoints

    def _map_authentication(self, dpd_auth: Dict[str, Any]) -> list:
        """Map DPD authentication to universal format."""
        # DPD typically uses API key authentication
        if dpd_auth.get("type") == "api_key":
            return [
                {
                    "type": "api_key",
                    "name": "API Key Authentication",
                    "description": dpd_auth.get("description", "DPD API Key"),
                    "location": dpd_auth.get("location", "header"),
                    "parameter_name": dpd_auth.get("param_name", "X-API-Key"),
                }
            ]
        return []

    def _map_rate_limits(self, dpd_limits: list) -> list:
        """Map DPD rate limits to universal format."""
        universal_limits = []

        for limit in dpd_limits:
            universal_limits.append(
                {
                    "requests": limit.get("requests", 100),
                    "period": limit.get("period", "1 minute"),
                    "description": limit.get(
                        "description", "Rate limit per API key"
                    ),
                }
            )

        return universal_limits
