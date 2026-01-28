"""
Blueprint Converter - Convert blueprint YAML to Universal Carrier Format.

Laravel Equivalent: app/Services/Blueprints/BlueprintConverter.php

Converts validated blueprint YAML structure to UniversalCarrierFormat
Pydantic model, handling differences between blueprint format and
Universal Carrier Format.
"""

import logging
from typing import Any, Dict, List

from pydantic import ValidationError

from ..core.schema import (
    AuthenticationMethod,
    Endpoint,
    HttpMethod,
    Parameter,
    ParameterLocation,
    ParameterType,
    RateLimit,
    RequestSchema,
    ResponseSchema,
    UniversalCarrierFormat,
)

logger = logging.getLogger(__name__)


class BlueprintConverter:
    """
    Converts blueprint YAML to Universal Carrier Format.

    Laravel Equivalent:
    class BlueprintConverter
    {
        public function convert(array $blueprint): UniversalCarrierFormat
        {
            // Convert blueprint structure to UniversalCarrierFormat
        }
    }
    """

    def convert(self, blueprint: Dict[str, Any]) -> UniversalCarrierFormat:
        """
        Convert blueprint dictionary to UniversalCarrierFormat.

        Args:
            blueprint: Validated blueprint dictionary

        Returns:
            UniversalCarrierFormat instance

        Raises:
            ValueError: If conversion fails
        """
        # Extract carrier info (flatten carrier: wrapper)
        carrier = blueprint.get("carrier", {})
        if not carrier:
            raise ValueError("Blueprint must contain 'carrier' section")

        # Convert authentication (handle single object or list)
        authentication = self._convert_authentication(
            blueprint.get("authentication", [])
        )

        # Convert endpoints
        endpoints = self._convert_endpoints(blueprint.get("endpoints", []))

        # Convert rate limits
        rate_limits = self._convert_rate_limits(blueprint.get("rate_limits", []))

        # Build UniversalCarrierFormat
        try:
            return UniversalCarrierFormat(
                name=carrier["name"],
                base_url=carrier["base_url"],
                version=carrier.get("version"),
                description=carrier.get("description"),
                endpoints=endpoints,
                authentication=authentication,
                rate_limits=rate_limits,
                documentation_url=blueprint.get("documentation_url"),
            )
        except (ValidationError, KeyError, TypeError) as e:
            logger.error(f"Failed to create UniversalCarrierFormat: {e}")
            raise ValueError(f"Failed to convert blueprint: {e}") from e
        except Exception as e:
            logger.error(f"Failed to create UniversalCarrierFormat: {e}")
            raise ValueError(f"Failed to convert blueprint: {e}") from e

    def _convert_authentication(self, auth_data: Any) -> List[AuthenticationMethod]:
        """
        Convert authentication data to list of AuthenticationMethod.

        Handles both single object and list formats.
        """
        if not auth_data:
            return []

        # Normalize to list
        auth_list = auth_data if isinstance(auth_data, list) else [auth_data]

        auth_methods = []
        for auth in auth_list:
            if not isinstance(auth, dict):
                continue

            # Extract fields (ignore 'required' as it's not in AuthenticationMethod)
            auth_method = AuthenticationMethod(
                type=auth["type"],
                name=auth.get("name", f"{auth['type'].title()} Authentication"),
                description=auth.get("description"),
                location=auth.get("location", "header"),
                scheme=auth.get("scheme"),
                parameter_name=auth.get("parameter_name"),
            )
            auth_methods.append(auth_method)

        return auth_methods

    def _convert_endpoints(
        self, endpoints_data: List[Dict[str, Any]]
    ) -> List[Endpoint]:
        """Convert endpoints data to list of Endpoint."""
        endpoints = []

        for endpoint_data in endpoints_data:
            if not isinstance(endpoint_data, dict):
                continue

            # Convert request if present
            request = None
            if "request" in endpoint_data and endpoint_data["request"]:
                request = self._convert_request(endpoint_data["request"])

            # Convert responses
            responses = self._convert_responses(endpoint_data.get("responses", []))

            # Convert HTTP method string to enum
            method_str = endpoint_data["method"].upper()
            try:
                method = HttpMethod(method_str)
            except ValueError:
                logger.warning(f"Invalid HTTP method: {method_str}, defaulting to GET")
                method = HttpMethod.GET

            endpoint = Endpoint(
                path=endpoint_data["path"],
                method=method,
                summary=endpoint_data["summary"],
                description=endpoint_data.get("description"),
                request=request,
                responses=responses,
                authentication_required=endpoint_data.get(
                    "authentication_required", False
                ),
                tags=endpoint_data.get("tags", []),
            )
            endpoints.append(endpoint)

        return endpoints

    def _convert_request(self, request_data: Dict[str, Any]) -> RequestSchema:
        """Convert request data to RequestSchema."""
        # Convert parameters
        parameters = []
        if "parameters" in request_data and request_data["parameters"]:
            for param_data in request_data["parameters"]:
                if not isinstance(param_data, dict):
                    continue

                # Convert parameter type string to enum
                type_str = param_data["type"].lower()
                try:
                    param_type = ParameterType(type_str)
                except ValueError:
                    logger.warning(
                        f"Invalid parameter type: {type_str}, defaulting to string"
                    )
                    param_type = ParameterType.STRING

                # Convert location string to enum
                location_str = param_data["location"].lower()
                try:
                    location = ParameterLocation(location_str)
                except ValueError:
                    logger.warning(
                        f"Invalid parameter location: {location_str}, defaulting to query"
                    )
                    location = ParameterLocation.QUERY

                parameter = Parameter(
                    name=param_data["name"],
                    type=param_type,
                    location=location,
                    required=param_data.get("required", False),
                    description=param_data.get("description"),
                    default_value=param_data.get("default"),
                    example=param_data.get("example"),
                    enum_values=param_data.get("enum"),
                )
                parameters.append(parameter)

        return RequestSchema(
            content_type=request_data.get("content_type", "application/json"),
            body_schema=request_data.get("body_schema"),
            parameters=parameters,
        )

    def _convert_responses(
        self, responses_data: List[Dict[str, Any]]
    ) -> List[ResponseSchema]:
        """Convert responses data to list of ResponseSchema."""
        responses = []

        for response_data in responses_data:
            if not isinstance(response_data, dict):
                continue

            response = ResponseSchema(
                status_code=response_data["status_code"],
                content_type=response_data.get("content_type", "application/json"),
                body_schema=response_data.get("body_schema"),
                description=response_data.get("description"),
            )
            responses.append(response)

        return responses

    def _convert_rate_limits(
        self, rate_limits_data: List[Dict[str, Any]]
    ) -> List[RateLimit]:
        """Convert rate limits data to list of RateLimit."""
        rate_limits = []

        for limit_data in rate_limits_data:
            if not isinstance(limit_data, dict):
                continue

            rate_limit = RateLimit(
                requests=limit_data["requests"],
                period=limit_data["period"],
                description=limit_data.get("description"),
            )
            rate_limits.append(rate_limit)

        return rate_limits
