"""
Core Validator

Laravel Equivalent: app/Services/ValidationService.php or FormRequest classes

Validates carrier responses against the Universal Carrier Format schema.
This ensures all carrier responses conform to the universal standard.

In Laravel, you'd have:
- FormRequest classes with validation rules
- Validator::make() calls
- Custom validation rules
"""

from typing import Any, Dict, List, Optional

from pydantic import ValidationError

from .schema import UniversalCarrierFormat


class CarrierValidator:
    """
    Validates carrier responses against the Universal Carrier Format.

    Laravel Equivalent: FormRequest class or Validator::make()

    Usage:
        validator = CarrierValidator()
        try:
            validated = validator.validate(carrier_response_data)
        except ValidationError as e:
            # Handle validation errors
    """

    def validate(
        self, data: Dict[str, Any]
    ) -> UniversalCarrierFormat:
        """
        Validate carrier response data against Universal Carrier Format.

        Args:
            data: Dictionary containing carrier response data

        Returns:
            UniversalCarrierFormat: Validated and parsed carrier format

        Raises:
            ValidationError: If data doesn't match the schema

        Laravel Equivalent:
            $request->validate([
                'name' => 'required|string',
                'base_url' => 'required|url',
                // ...
            ]);
        """
        try:
            return UniversalCarrierFormat(**data)
        except ValidationError as e:
            # Re-raise with more context
            raise ValidationError.from_exception_data(
                "UniversalCarrierFormat", e.errors()
            ) from e

    def validate_endpoint(self, endpoint_data: Dict[str, Any]) -> bool:
        """
        Validate a single endpoint against the schema.

        Args:
            endpoint_data: Dictionary containing endpoint data

        Returns:
            bool: True if valid

        Raises:
            ValidationError: If endpoint doesn't match the schema
        """
        from .schema import Endpoint

        try:
            Endpoint(**endpoint_data)
            return True
        except ValidationError as e:
            raise ValidationError.from_exception_data("Endpoint", e.errors()) from e

    def validate_batch(
        self, carrier_responses: List[Dict[str, Any]]
    ) -> List[UniversalCarrierFormat]:
        """
        Validate multiple carrier responses in batch.

        Args:
            carrier_responses: List of carrier response dictionaries

        Returns:
            List[UniversalCarrierFormat]: List of validated carrier formats

        Raises:
            ValidationError: If any response doesn't match the schema
        """
        validated = []
        errors = []

        for idx, response in enumerate(carrier_responses):
            try:
                validated.append(self.validate(response))
            except ValidationError as e:
                errors.append(f"Response {idx}: {e.errors()}")

        if errors:
            # Raise a ValueError with all error messages
            # (Simpler than trying to combine ValidationErrors)
            error_message = "Batch validation failed:\n" + "\n".join(errors)
            raise ValueError(error_message)

        return validated
