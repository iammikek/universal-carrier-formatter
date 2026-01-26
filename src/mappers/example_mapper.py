"""
Example Carrier Mapper

Laravel Equivalent: app/Services/Mappers/ExampleMapper.php

This is an EXAMPLE/REFERENCE mapper showing the pattern for creating carrier mappers.
It demonstrates how to map carrier-specific API responses to the Universal Carrier Format.

Example messy carrier response (DPD-style):
{
  "trk_num": "1234567890",
  "stat": "IN_TRANSIT",
  "loc": {"city": "London", "postcode": "SW1A 1AA"},
  "est_del": "2026-01-30"
}

Transforms to Universal Carrier Format tracking response.

NOTE: This is a reference example - not a production mapper for a specific carrier.
Use this as a template when creating new mappers or as a reference for the mapper generator.

In Laravel, you'd have:
- A mapper service class
- Transformation methods
- Data mapping logic
"""

from datetime import datetime
from typing import Any, Dict

from ..core.schema import (
    Endpoint,
    HttpMethod,
    Parameter,
    ParameterLocation,
    ParameterType,
    UniversalCarrierFormat,
)


class ExampleMapper:
    """
    Example mapper for carrier API responses to Universal Carrier Format.

    This is a reference example showing the mapper pattern. Use this as a template
    when creating new mappers or as a reference for the mapper generator.

    Laravel Equivalent: app/Services/Mappers/ExampleMapper.php

    Usage:
        mapper = ExampleMapper()
        universal_format = mapper.map_tracking_response(carrier_response)
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
        self, carrier_response: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Transform messy carrier tracking response to universal format.

        Args:
            carrier_response: Raw carrier API tracking response (DPD-style format)

        Returns:
            Dict: Universal format tracking response

        Example:
            Input: {"trk_num": "1234567890", "stat": "IN_TRANSIT", ...}
            Output: {"tracking_number": "1234567890", "status": "in_transit", ...}
        """
        universal_response = {}

        # Map tracking number
        if "trk_num" in carrier_response:
            universal_response["tracking_number"] = carrier_response["trk_num"]

        # Map and normalize status
        if "stat" in carrier_response:
            carrier_status = carrier_response["stat"]
            universal_response["status"] = self.STATUS_MAPPING.get(
                carrier_status, carrier_status.lower()
            )

        # Map location
        if "loc" in carrier_response:
            location = carrier_response["loc"]
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
        if "est_del" in carrier_response:
            # Normalize date format (carrier uses YYYY-MM-DD, we want ISO 8601)
            est_del = carrier_response["est_del"]
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
        self, carrier_schema: Dict[str, Any]
    ) -> UniversalCarrierFormat:
        """
        Transform carrier schema to Universal Carrier Format.

        This maps the carrier's API documentation structure to our universal schema.

        Args:
            carrier_schema: Carrier API schema/documentation structure

        Returns:
            UniversalCarrierFormat: Standardized carrier format
        """
        return UniversalCarrierFormat(
            name=carrier_schema.get("carrier", "Example Carrier"),
            base_url=carrier_schema.get("api_url", "https://api.example.com"),
            version=carrier_schema.get("api_ver", "v1"),
            description=carrier_schema.get("description", "Example Carrier API"),
            endpoints=self._map_endpoints(carrier_schema.get("endpoints", [])),
            authentication=self._map_authentication(
                carrier_schema.get("auth", {})
            ),
            rate_limits=self._map_rate_limits(
                carrier_schema.get("rate_limits", [])
            ),
            documentation_url=carrier_schema.get("docs_url"),
        )

    def _map_endpoints(self, carrier_endpoints: list) -> list:
        """Map carrier endpoints to universal format."""
        universal_endpoints = []

        for endpoint in carrier_endpoints:
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

    def _map_authentication(self, carrier_auth: Dict[str, Any]) -> list:
        """Map carrier authentication to universal format."""
        # Example: API key authentication
        if carrier_auth.get("type") == "api_key":
            return [
                {
                    "type": "api_key",
                    "name": "API Key Authentication",
                    "description": carrier_auth.get("description", "API Key"),
                    "location": carrier_auth.get("location", "header"),
                    "parameter_name": carrier_auth.get("param_name", "X-API-Key"),
                }
            ]
        return []

    def _map_rate_limits(self, carrier_limits: list) -> list:
        """Map carrier rate limits to universal format."""
        universal_limits = []

        for limit in carrier_limits:
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
