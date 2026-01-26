from typing import Any, Dict, Optional
from datetime import datetime
from ..core.schema import UniversalCarrierFormat
from ..core import UniversalFieldNames


class RoyalMailRestApiMapper:
    """
    Mapper class to convert Royal Mail Rest API responses into the Universal Carrier Format.
    """

    FIELD_MAPPING = {
        # Carrier field names → Universal field names (using constants for type safety)
        "mailPieceId": UniversalFieldNames.TRACKING_NUMBER,
        "status": UniversalFieldNames.STATUS,
        "lastEventDateTime": UniversalFieldNames.LAST_UPDATE,
        "destinationCountry": UniversalFieldNames.DESTINATION_COUNTRY,
        "originCountry": UniversalFieldNames.ORIGIN_COUNTRY,
        "events": UniversalFieldNames.EVENTS,
        "proofOfDelivery": UniversalFieldNames.PROOF_OF_DELIVERY,
        "manifestId": UniversalFieldNames.MANIFEST_ID,
        "label": UniversalFieldNames.LABEL_BASE64,
    }

    STATUS_MAPPING = {
        # Carrier status codes → Universal status values (strings)
        # Note: We use strings here since we don't have a TrackingStatus enum yet
        "DELIVERED": "delivered",
        "IN_TRANSIT": "in_transit",
        "OUT_FOR_DELIVERY": "out_for_delivery",
        "EXCEPTION": "exception",
        "FAILED_ATTEMPT": "failed_attempt",
        "PENDING": "pending",
        "UNKNOWN": "unknown",
    }

    def map_tracking_response(self, carrier_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Maps a Royal Mail tracking API response to the Universal Carrier Format.

        Args:
            carrier_response (Dict[str, Any]): The raw response from Royal Mail API.

        Returns:
            Dict[str, Any]: A dictionary conforming to UniversalCarrierFormat.
        """
        universal: Dict[str, Any] = {}

        # Map tracking number
        tracking_number = carrier_response.get("mailPieceId") or carrier_response.get("trackingNumber")
        if tracking_number:
            universal[UniversalFieldNames.TRACKING_NUMBER] = str(tracking_number)
        else:
            universal[UniversalFieldNames.TRACKING_NUMBER] = None

        # Map status with fallback to UNKNOWN
        raw_status = carrier_response.get("status", "UNKNOWN")
        universal[UniversalFieldNames.STATUS] = self.STATUS_MAPPING.get(raw_status.upper(), "unknown")

        # Map last update date/time
        last_update_raw = carrier_response.get("lastEventDateTime")
        universal[UniversalFieldNames.LAST_UPDATE] = self._parse_datetime(last_update_raw)

        # Map origin and destination countries
        origin_country = carrier_response.get("originCountry")
        universal[UniversalFieldNames.ORIGIN_COUNTRY] = self._normalize_country(origin_country)

        destination_country = carrier_response.get("destinationCountry")
        universal[UniversalFieldNames.DESTINATION_COUNTRY] = self._normalize_country(destination_country)

        # Map events (tracking history)
        events_raw = carrier_response.get("events") or []
        universal[UniversalFieldNames.EVENTS] = self._map_events(events_raw)

        # Map proof of delivery if present
        pod = carrier_response.get("proofOfDelivery")
        if pod:
            universal[UniversalFieldNames.PROOF_OF_DELIVERY] = pod
        else:
            universal[UniversalFieldNames.PROOF_OF_DELIVERY] = None

        # Map label if present (base64 encoded)
        label = carrier_response.get("label")
        universal[UniversalFieldNames.LABEL_BASE64] = label if label else None

        # Map manifest id if present
        manifest_id = carrier_response.get("manifestId")
        universal[UniversalFieldNames.MANIFEST_ID] = str(manifest_id) if manifest_id else None

        return universal

    def _map_events(self, events: Any) -> Optional[list[Dict[str, Any]]]:
        """
        Maps the carrier's event list to a list of universal event dictionaries.

        Args:
            events (Any): Raw events data from carrier.

        Returns:
            Optional[list[Dict[str, Any]]]: List of mapped events or None.
        """
        if not isinstance(events, list):
            return None

        mapped_events = []
        for event in events:
            try:
                event_code = event.get("eventCode") or event.get("code")
                event_description = event.get("description") or event.get("eventDescription")
                event_datetime_raw = event.get("eventDateTime") or event.get("dateTime")
                event_datetime = self._parse_datetime(event_datetime_raw)
                location = event.get("location") or {}

                city = location.get("city") or location.get("town") or None
                country = self._normalize_country(location.get("country"))

                mapped_event = {
                    "code": event_code,
                    "description": event_description,
                    "date_time": event_datetime,
                    "city": city,
                    "country": country,
                }
                mapped_events.append(mapped_event)
            except Exception:
                # Skip malformed event entries
                continue

        return mapped_events if mapped_events else None

    def _parse_datetime(self, date_str: Optional[str]) -> Optional[datetime]:
        """
        Parses a datetime string into a datetime object.

        Args:
            date_str (Optional[str]): The datetime string.

        Returns:
            Optional[datetime]: Parsed datetime or None if invalid.
        """
        if not date_str or not isinstance(date_str, str):
            return None
        try:
            # ISO 8601 format expected, fallback to common formats if needed
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except ValueError:
            # Try common alternative formats if needed
            for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
        return None

    def _normalize_country(self, country: Optional[str]) -> Optional[str]:
        """
        Normalizes country names or codes to ISO 3166-1 alpha-2 codes.

        Args:
            country (Optional[str]): Country name or code.

        Returns:
            Optional[str]: ISO alpha-2 country code or None.
        """
        if not country or not isinstance(country, str):
            return None

        country = country.strip().upper()

        # If already ISO alpha-2 code (2 letters), return as is
        if len(country) == 2 and country.isalpha():
            return country

        # Basic mapping for common country names to ISO alpha-2 codes
        country_map = {
            "UNITED KINGDOM": "GB",
            "GREAT BRITAIN": "GB",
            "ENGLAND": "GB",
            "SCOTLAND": "GB",
            "WALES": "GB",
            "NORTHERN IRELAND": "GB",
            "UK": "GB",
            "UNITED STATES": "US",
            "USA": "US",
            "UNITED STATES OF AMERICA": "US",
            "FRANCE": "FR",
            "GERMANY": "DE",
            "CANADA": "CA",
            "AUSTRALIA": "AU",
            "IRELAND": "IE",
        }

        return country_map.get(country, None)

    def map_carrier_schema(self, carrier_schema: Dict[str, Any]) -> UniversalCarrierFormat:
        """
        Maps the carrier-specific schema to the UniversalCarrierFormat schema.

        Args:
            carrier_schema (Dict[str, Any]): Carrier-specific schema dictionary.

        Returns:
            UniversalCarrierFormat: The mapped universal schema object.
        """
        # This is a placeholder implementation as the carrier schema details are not fully defined.
        # Typically, this would parse the carrier schema and map fields accordingly.
        # For now, return an empty UniversalCarrierFormat or raise NotImplementedError.

        raise NotImplementedError("Mapping carrier schema to UniversalCarrierFormat is not implemented.")