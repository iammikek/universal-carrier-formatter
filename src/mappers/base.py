"""
Base class for carrier mappers (Registry / Plugin architecture).

All carrier-specific mappers inherit from CarrierMapperBase (CarrierAbstract)
and register themselves with CarrierRegistry. This keeps the core uniform:
contributors add new carriers by adding a single mapping file that inherits
and registers; no changes to core or API.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict

from ..core.schema import UniversalCarrierFormat


class CarrierMapperBase(ABC):
    """
    Abstract base for carrier API → Universal Carrier Format mappers.

    Each carrier (DHL, DPD, Royal Mail, etc.) is a concrete mapper that:
    1. Inherits from this class (or CarrierAbstract, same type)
    2. Implements map_tracking_response (required) and optionally map_carrier_schema
    3. Registers with CarrierRegistry under a slug via @register_carrier("slug")

    Usage:
        @register_carrier("my_carrier")
        class MyCarrierMapper(CarrierMapperBase):
            FIELD_MAPPING = {...}
            def map_tracking_response(self, carrier_response): ...
    """

    # Subclasses may define for documentation / codegen; not required by base.
    FIELD_MAPPING: Dict[str, Any] = {}
    STATUS_MAPPING: Dict[str, str] = {}

    @abstractmethod
    def map_tracking_response(self, carrier_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map carrier-specific tracking response to Universal Carrier Format.

        Args:
            carrier_response: Raw API response from the carrier.

        Returns:
            Dict with universal field names (e.g. tracking_number, status).
        """
        ...

    def map_carrier_schema(
        self, carrier_schema: Dict[str, Any]
    ) -> UniversalCarrierFormat:
        """
        Map carrier-specific schema/documentation to UniversalCarrierFormat.

        Optional. Default raises NotImplementedError. Override in mappers
        that support schema mapping.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} does not implement map_carrier_schema"
        )


# Plugin architecture: each carrier is "just a mapping" that inherits this.
CarrierAbstract = CarrierMapperBase
