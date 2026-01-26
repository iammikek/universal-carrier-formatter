from typing import Any, Dict, Optional
from datetime import datetime
from ..core.schema import UniversalCarrierFormat
from ..core import UniversalFieldNames


class RoyalMailRestApiMapper:
    """
    Mapper class for Royal Mail Rest API responses to Universal Carrier Format.
    """

    FIELD_MAPPING = {
        "shipmentNumber": UniversalFieldNames.SHIPMENT_NUMBER,
        "trackingNumber": UniversalFieldNames.TRACKING_NUMBER,
        UniversalFieldNames.STATUS: UniversalFieldNames.STATUS,
        "currentLocation": UniversalFieldNames.CURRENT_LOCATION,
        "estimatedDeliveryDate": UniversalFieldNames.ESTIMATED_DELIVERY,
        "postalCode": UniversalFieldNames.POSTAL_CODE,
        "countryCode": UniversalFieldNames.COUNTRY,
        "manifestNumber": UniversalFieldNames.MANIFEST_NUMBER,
        "label": UniversalFieldNames.LABEL,
        "proofOfDelivery": UniversalFieldNames.PROOF_OF_DELIVERY,
        "history": UniversalFieldNames.HISTORY,
        "manifestLabel": UniversalFieldNames.MANIFEST_LABEL,
        "createdAt": UniversalFieldNames.CREATED_AT,
        "updatedAt": UniversalFieldNames.UPDATED_AT,
    }

    STATUS_MAPPING = {
        "DELIVERED": "delivered",
        "IN_TRANSIT": "in_transit",
        "EXCEPTION": "exception",
        "PENDING": "pending",
        "CANCELLED": "cancelled",
        "FAILED": "failed",
        "OUT_FOR_DELIVERY": "out_for_delivery",
        "INFO_RECEIVED": "info_received",
    }

    def map_tracking_response(self, carrier_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Maps a Royal Mail tracking API response to the Universal Carrier Format dictionary.

        Args:
            carrier_response (Dict[str, Any]): The raw response from Royal Mail API.

        Returns:
            Dict[str, Any]: Mapped dictionary using UniversalFieldNames constants.
        """
        universal: Dict[str, Any] = {}

        # Map known fields using FIELD_MAPPING
        for carrier_field, universal_field in self.FIELD_MAPPING.items():
            value = carrier_response.get(carrier_field)
            if value is not None:
                if universal_field in (
                    UniversalFieldNames.ESTIMATED_DELIVERY,
                    UniversalFieldNames.CREATED_AT,
                    UniversalFieldNames.UPDATED_AT,
                ):
                    parsed_date = self._parse_date(value)
                    if parsed_date:
                        universal[universal_field] = parsed_date
                elif universal_field == UniversalFieldNames.COUNTRY:
                    country = self._derive_country(value)
                    if country:
                        universal[universal_field] = country
                else:
                    universal[universal_field] = value

        # Map status with fallback to lowercase string if unknown
        carrier_status = carrier_response.get("status")
        if carrier_status:
            universal[UniversalFieldNames.STATUS] = self.STATUS_MAPPING.get(
                carrier_status.upper(), carrier_status.lower()
            )

        # Handle nested or complex fields if present
        if "history" in carrier_response and isinstance(carrier_response["history"], list):
            universal[UniversalFieldNames.HISTORY] = self._map_history(carrier_response["history"])

        if "proofOfDelivery" in carrier_response:
            pod = carrier_response.get("proofOfDelivery")
            if pod:
                universal[UniversalFieldNames.PROOF_OF_DELIVERY] = pod

        if "label" in carrier_response:
            label = carrier_response.get("label")
            if label:
                universal[UniversalFieldNames.LABEL] = label

        if "manifestLabel" in carrier_response:
            manifest_label = carrier_response.get("manifestLabel")
            if manifest_label:
                universal[UniversalFieldNames.MANIFEST_LABEL] = manifest_label

        return universal

    def _parse_date(self, date_str: Optional[str]) -> Optional[str]:
        """
        Parses a date string into ISO 8601 format.

        Args:
            date_str (Optional[str]): Date string to parse.

        Returns:
            Optional[str]: ISO 8601 formatted date string or None if parsing fails.
        """
        if not date_str:
            return None
        try:
            # Attempt to parse common ISO formats or fallback to datetime.fromisoformat
            dt = datetime.fromisoformat(date_str.rstrip("Z"))
            return dt.isoformat() + "Z"
        except (ValueError, TypeError):
            # Could add more parsing logic here if needed
            return None

    def _derive_country(self, country_code: Optional[str]) -> Optional[str]:
        """
        Derives a normalized country code from the carrier's country code.

        Args:
            country_code (Optional[str]): Country code from carrier.

        Returns:
            Optional[str]: Uppercase ISO country code or None.
        """
        if not country_code:
            return None
        return country_code.strip().upper()

    def _map_history(self, history_list: Any) -> Any:
        """
        Maps tracking history entries to universal format.

        Args:
            history_list (Any): List of history entries from carrier.

        Returns:
            Any: Mapped history list or empty list if invalid.
        """
        if not isinstance(history_list, list):
            return []

        mapped_history = []
        for event in history_list:
            if not isinstance(event, dict):
                continue
            mapped_event = {}
            # Map known fields in history event if present
            timestamp = event.get("timestamp") or event.get("date")
            if timestamp:
                parsed_timestamp = self._parse_date(timestamp)
                if parsed_timestamp:
                    mapped_event[UniversalFieldNames.EVENT_TIMESTAMP] = parsed_timestamp

            status = event.get("status")
            if status:
                mapped_event[UniversalFieldNames.STATUS] = self.STATUS_MAPPING.get(
                    status.upper(), status.lower()
                )

            location = event.get("location")
            if location:
                mapped_event[UniversalFieldNames.CURRENT_LOCATION] = location

            description = event.get("description")
            if description:
                mapped_event[UniversalFieldNames.DESCRIPTION] = description

            if mapped_event:
                mapped_history.append(mapped_event)

        return mapped_history

    def map_carrier_schema(self, carrier_schema: Dict[str, Any]) -> UniversalCarrierFormat:
        """
        Maps the carrier-specific schema to the UniversalCarrierFormat dataclass.

        Args:
            carrier_schema (Dict[str, Any]): Carrier schema dictionary.

        Returns:
            UniversalCarrierFormat: Mapped universal carrier format object.
        """
        mapped_dict = self.map_tracking_response(carrier_schema)
        return UniversalCarrierFormat(**mapped_dict)  # type: ignore