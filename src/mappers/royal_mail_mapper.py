from datetime import datetime
from typing import Any, Dict, List, Optional

from ..core import UniversalFieldNames
from ..core.schema import UniversalCarrierFormat
from .base import CarrierMapperBase
from .registry import register_carrier


@register_carrier("royal_mail")
@register_carrier("royalmail")
class RoyalMailRestApiMapper(CarrierMapperBase):
    """
    Mapper class for Royal Mail Rest API responses to Universal Carrier Format.
    """

    FIELD_MAPPING = {
        "trackingNumber": UniversalFieldNames.TRACKING_NUMBER,
        "status": UniversalFieldNames.STATUS,
        "lastUpdate": UniversalFieldNames.LAST_UPDATE,
        "currentLocation": UniversalFieldNames.CURRENT_LOCATION,
        "estimatedDelivery": UniversalFieldNames.ESTIMATED_DELIVERY,
        "city": UniversalFieldNames.CITY,
        "postalCode": UniversalFieldNames.POSTAL_CODE,
        "country": UniversalFieldNames.COUNTRY,
        "addressLine1": UniversalFieldNames.ADDRESS_LINE_1,
        "addressLine2": UniversalFieldNames.ADDRESS_LINE_2,
        "state": UniversalFieldNames.STATE,
        "originCountry": UniversalFieldNames.ORIGIN_COUNTRY,
        "destinationCountry": UniversalFieldNames.DESTINATION_COUNTRY,
        UniversalFieldNames.EVENTS: UniversalFieldNames.EVENTS,
        "proofOfDelivery": UniversalFieldNames.PROOF_OF_DELIVERY,
        "deliveredAt": UniversalFieldNames.DELIVERED_AT,
        "signedBy": UniversalFieldNames.SIGNED_BY,
        "weight": UniversalFieldNames.WEIGHT,
        "dimensions": UniversalFieldNames.DIMENSIONS,
        "labelBase64": UniversalFieldNames.LABEL_BASE64,
        "label": UniversalFieldNames.LABEL,
        "manifestId": UniversalFieldNames.MANIFEST_ID,
        "manifestNumber": UniversalFieldNames.MANIFEST_NUMBER,
        "manifestLabel": UniversalFieldNames.MANIFEST_LABEL,
        "serviceName": UniversalFieldNames.SERVICE_NAME,
        "shipmentNumber": UniversalFieldNames.SHIPMENT_NUMBER,
        "history": UniversalFieldNames.HISTORY,
        "createdAt": UniversalFieldNames.CREATED_AT,
        "updatedAt": UniversalFieldNames.UPDATED_AT,
        "carrier": UniversalFieldNames.CARRIER,
        "carrierService": UniversalFieldNames.CARRIER_SERVICE,
        "cost": UniversalFieldNames.COST,
        "currency": UniversalFieldNames.CURRENCY,
    }

    STATUS_MAPPING = {
        "DELIVERED": "delivered",
        "IN_TRANSIT": "in_transit",
        "OUT_FOR_DELIVERY": "out_for_delivery",
        "EXCEPTION": "exception",
        "PENDING": "pending",
        "INFO_RECEIVED": "info_received",
        "FAILED_ATTEMPT": "failed_attempt",
        "RETURNED_TO_SENDER": "returned_to_sender",
        "CANCELLED": "cancelled",
        "UNKNOWN": "unknown",
    }

    def map_tracking_response(self, carrier_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Maps a Royal Mail tracking API response to the universal tracking response format.

        Args:
            carrier_response (Dict[str, Any]): The raw response from Royal Mail API.

        Returns:
            Dict[str, Any]: The mapped response in Universal Carrier Format.
        """
        universal_response: Dict[str, Any] = {}

        # Map simple fields using FIELD_MAPPING
        for carrier_field, universal_field in self.FIELD_MAPPING.items():
            value = carrier_response.get(carrier_field)
            if value is not None:
                if universal_field in (
                    UniversalFieldNames.LAST_UPDATE,
                    UniversalFieldNames.ESTIMATED_DELIVERY,
                    UniversalFieldNames.CREATED_AT,
                    UniversalFieldNames.UPDATED_AT,
                    UniversalFieldNames.DELIVERED_AT,
                ):
                    parsed_date = self._parse_date(value)
                    if parsed_date:
                        universal_response[universal_field] = parsed_date
                elif universal_field == UniversalFieldNames.STATUS:
                    universal_response[universal_field] = self.STATUS_MAPPING.get(
                        str(value).upper(), str(value).lower()
                    )
                elif universal_field == UniversalFieldNames.EVENTS:
                    universal_response[universal_field] = self._map_events(value)
                elif universal_field == UniversalFieldNames.PROOF_OF_DELIVERY:
                    universal_response[universal_field] = self._map_proof_of_delivery(
                        value
                    )
                else:
                    universal_response[universal_field] = value

        # Additional handling for nested or complex fields if present
        # e.g. currentLocation might be a dict with address details
        if "currentLocation" in carrier_response and isinstance(
            carrier_response["currentLocation"], dict
        ):
            loc = carrier_response["currentLocation"]
            location_str = self._format_location(loc)
            if location_str:
                universal_response[UniversalFieldNames.CURRENT_LOCATION] = location_str

        return universal_response

    def _map_events(self, events: Any) -> List[Dict[str, Any]]:
        """
        Maps the events list from carrier format to universal format.

        Args:
            events (Any): The events data from carrier response.

        Returns:
            List[Dict[str, Any]]: List of mapped event dictionaries.
        """
        if not isinstance(events, list):
            return []

        mapped_events = []
        for event in events:
            if not isinstance(event, dict):
                continue
            mapped_event = {}
            # Map event type
            event_type = event.get("eventType") or event.get("type")
            if event_type:
                mapped_event[UniversalFieldNames.EVENT_TYPE] = event_type

            # Map event datetime
            event_datetime_raw = event.get("eventDateTime") or event.get("dateTime")
            event_datetime = self._parse_date(event_datetime_raw)
            if event_datetime:
                mapped_event[UniversalFieldNames.EVENT_DATETIME] = event_datetime

            # Map event description
            description = event.get("eventDescription") or event.get("description")
            if description:
                mapped_event[UniversalFieldNames.EVENT_DESCRIPTION] = description

            # Map event location
            location = event.get("eventLocation") or event.get("location")
            if location:
                if isinstance(location, dict):
                    mapped_event[UniversalFieldNames.EVENT_LOCATION] = (
                        self._format_location(location)
                    )
                elif isinstance(location, str):
                    mapped_event[UniversalFieldNames.EVENT_LOCATION] = location

            if mapped_event:
                mapped_events.append(mapped_event)

        return mapped_events

    def _map_proof_of_delivery(self, pod_data: Any) -> Dict[str, Any]:
        """
        Maps proof of delivery data from carrier format to universal format.

        Args:
            pod_data (Any): Proof of delivery data from carrier response.

        Returns:
            Dict[str, Any]: Mapped proof of delivery dictionary.
        """
        if not isinstance(pod_data, dict):
            return {}

        pod_mapped = {}

        delivered_at_raw = pod_data.get("deliveredAt") or pod_data.get(
            "deliveryDateTime"
        )
        delivered_at = self._parse_date(delivered_at_raw)
        if delivered_at:
            pod_mapped[UniversalFieldNames.DELIVERED_AT] = delivered_at

        signed_by = pod_data.get("signedBy") or pod_data.get("recipientName")
        if signed_by:
            pod_mapped[UniversalFieldNames.SIGNED_BY] = signed_by

        # Additional POD fields can be mapped here if available

        return pod_mapped

    def _format_location(self, location: Dict[str, Any]) -> str:
        """
        Formats a location dictionary into a single string.

        Args:
            location (Dict[str, Any]): Location dictionary.

        Returns:
            str: Formatted location string.
        """
        if not location:
            return ""

        parts = []
        for key in (
            "addressLine1",
            "addressLine2",
            "city",
            "state",
            "postalCode",
            "country",
        ):
            val = location.get(key)
            if val:
                parts.append(str(val).strip())
        return ", ".join(parts)

    def _parse_date(self, date_str: Optional[str]) -> Optional[str]:
        """
        Parses a date string into ISO 8601 format.

        Args:
            date_str (Optional[str]): Date string to parse.

        Returns:
            Optional[str]: ISO 8601 formatted date string or None if parsing fails.
        """
        if not date_str or not isinstance(date_str, str):
            return None
        try:
            # Try ISO format first (most common)
            if "T" in date_str or date_str.endswith("Z"):
                dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            else:
                # Try common date formats
                for fmt in ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y", "%m/%d/%Y"]:
                    try:
                        dt = datetime.strptime(date_str, fmt)
                        break
                    except ValueError:
                        continue
                else:
                    return None
            return dt.isoformat()
        except (ValueError, TypeError):
            return None

    def map_carrier_schema(
        self, carrier_schema: Dict[str, Any]
    ) -> UniversalCarrierFormat:
        """
        Maps the carrier-specific schema to the UniversalCarrierFormat schema.

        Args:
            carrier_schema (Dict[str, Any]): Carrier-specific schema dictionary.

        Returns:
            UniversalCarrierFormat: The mapped universal carrier format object.
        """
        # This is a stub implementation as the carrier schema is not fully defined.
        # Typically, this would convert carrier schema fields to UniversalCarrierFormat fields.
        # For now, we return an empty UniversalCarrierFormat with carrier name set.

        return UniversalCarrierFormat(
            carrier_name="Royal Mail Rest API", schema=carrier_schema
        )
