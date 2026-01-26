"""
Blueprint Validator - Validate blueprint structure.

Laravel Equivalent: app/Services/Blueprints/BlueprintValidator.php

Validates that a blueprint YAML structure matches expected format
and contains required fields.
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class BlueprintValidator:
    """
    Validates blueprint structure.

    Laravel Equivalent:
    class BlueprintValidator
    {
        public function validate(array $blueprint): array
        {
            $errors = [];
            // Validate structure...
            return $errors;
        }
    }
    """

    def validate(self, blueprint: Dict[str, Any]) -> List[str]:
        """
        Validate blueprint structure and return list of errors.

        Args:
            blueprint: Parsed blueprint dictionary

        Returns:
            List of error messages (empty if valid)
        """
        errors: List[str] = []

        # Validate carrier section
        if "carrier" not in blueprint:
            errors.append("Missing required 'carrier' section")
        else:
            carrier = blueprint["carrier"]
            if not isinstance(carrier, dict):
                errors.append("'carrier' must be a dictionary")
            else:
                # Validate required carrier fields
                if "name" not in carrier or not carrier["name"]:
                    errors.append("'carrier.name' is required and cannot be empty")
                if "base_url" not in carrier or not carrier["base_url"]:
                    errors.append("'carrier.base_url' is required and cannot be empty")
                else:
                    # Basic URL validation
                    base_url = str(carrier["base_url"])
                    if not (
                        base_url.startswith("http://")
                        or base_url.startswith("https://")
                    ):
                        errors.append(
                            "'carrier.base_url' must be a valid URL (start with http:// or https://)"
                        )

        # Validate endpoints section
        if "endpoints" not in blueprint:
            errors.append("Missing required 'endpoints' section")
        else:
            endpoints = blueprint["endpoints"]
            if not isinstance(endpoints, list):
                errors.append("'endpoints' must be a list")
            elif len(endpoints) == 0:
                errors.append("'endpoints' must contain at least one endpoint")
            else:
                # Validate each endpoint
                for i, endpoint in enumerate(endpoints):
                    if not isinstance(endpoint, dict):
                        errors.append(f"endpoints[{i}] must be a dictionary")
                        continue

                    # Required endpoint fields
                    if "path" not in endpoint or not endpoint["path"]:
                        errors.append(f"endpoints[{i}].path is required")
                    elif not str(endpoint["path"]).startswith("/"):
                        errors.append(
                            f"endpoints[{i}].path must start with '/' (got: {endpoint['path']})"
                        )

                    if "method" not in endpoint or not endpoint["method"]:
                        errors.append(f"endpoints[{i}].method is required")
                    else:
                        valid_methods = [
                            "GET",
                            "POST",
                            "PUT",
                            "DELETE",
                            "PATCH",
                            "HEAD",
                            "OPTIONS",
                        ]
                        if endpoint["method"] not in valid_methods:
                            errors.append(
                                f"endpoints[{i}].method must be one of {valid_methods} (got: {endpoint['method']})"
                            )

                    if "summary" not in endpoint or not endpoint["summary"]:
                        errors.append(f"endpoints[{i}].summary is required")

                    # Validate request parameters if present
                    if "request" in endpoint and endpoint["request"]:
                        request = endpoint["request"]
                        if isinstance(request, dict) and "parameters" in request:
                            params = request["parameters"]
                            if isinstance(params, list):
                                for j, param in enumerate(params):
                                    if not isinstance(param, dict):
                                        errors.append(
                                            f"endpoints[{i}].request.parameters[{j}] must be a dictionary"
                                        )
                                        continue

                                    if "name" not in param or not param["name"]:
                                        errors.append(
                                            f"endpoints[{i}].request.parameters[{j}].name is required"
                                        )
                                    if "type" not in param:
                                        errors.append(
                                            f"endpoints[{i}].request.parameters[{j}].type is required"
                                        )
                                    if "location" not in param:
                                        errors.append(
                                            f"endpoints[{i}].request.parameters[{j}].location is required"
                                        )

                    # Validate responses if present
                    if "responses" in endpoint and endpoint["responses"]:
                        responses = endpoint["responses"]
                        if isinstance(responses, list):
                            for j, response in enumerate(responses):
                                if not isinstance(response, dict):
                                    errors.append(
                                        f"endpoints[{i}].responses[{j}] must be a dictionary"
                                    )
                                    continue
                                if "status_code" not in response:
                                    errors.append(
                                        f"endpoints[{i}].responses[{j}].status_code is required"
                                    )
                                else:
                                    status_code = response["status_code"]
                                    if not isinstance(status_code, int):
                                        errors.append(
                                            f"endpoints[{i}].responses[{j}].status_code must be an integer"
                                        )
                                    elif not (100 <= status_code <= 599):
                                        errors.append(
                                            f"endpoints[{i}].responses[{j}].status_code must be between 100 and 599"
                                        )

        # Validate authentication if present
        if "authentication" in blueprint:
            auth = blueprint["authentication"]
            # Can be single object or list
            auth_list = auth if isinstance(auth, list) else [auth]
            for i, auth_method in enumerate(auth_list):
                if not isinstance(auth_method, dict):
                    errors.append(f"authentication[{i}] must be a dictionary")
                    continue

                if "type" not in auth_method:
                    errors.append(f"authentication[{i}].type is required")
                else:
                    valid_types = ["api_key", "bearer", "basic", "oauth2", "custom"]
                    if auth_method["type"] not in valid_types:
                        errors.append(
                            f"authentication[{i}].type must be one of {valid_types}"
                        )

                # Name is optional in blueprint (will be generated if missing)
                # if "name" not in auth_method or not auth_method["name"]:
                #     errors.append(f"authentication[{i}].name is required")

        # Validate rate_limits if present
        if "rate_limits" in blueprint:
            rate_limits = blueprint["rate_limits"]
            if not isinstance(rate_limits, list):
                errors.append("'rate_limits' must be a list")
            else:
                for i, limit in enumerate(rate_limits):
                    if not isinstance(limit, dict):
                        errors.append(f"rate_limits[{i}] must be a dictionary")
                        continue

                    if "requests" not in limit:
                        errors.append(f"rate_limits[{i}].requests is required")
                    elif not isinstance(limit["requests"], int) or limit["requests"] <= 0:
                        errors.append(
                            f"rate_limits[{i}].requests must be a positive integer"
                        )

                    if "period" not in limit or not limit["period"]:
                        errors.append(f"rate_limits[{i}].period is required")

        # Validate documentation_url if present
        if "documentation_url" in blueprint and blueprint["documentation_url"]:
            doc_url = str(blueprint["documentation_url"])
            if not (
                doc_url.startswith("http://") or doc_url.startswith("https://")
            ):
                errors.append(
                    "'documentation_url' must be a valid URL (start with http:// or https://)"
                )

        return errors

    def is_valid(self, blueprint: Dict[str, Any]) -> bool:
        """
        Check if blueprint is valid.

        Args:
            blueprint: Parsed blueprint dictionary

        Returns:
            True if valid, False otherwise
        """
        return len(self.validate(blueprint)) == 0
