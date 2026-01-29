from datetime import datetime
from typing import Any, Dict, Optional

from ..core import UniversalFieldNames
from ..core.schema import UniversalCarrierFormat
from .base import CarrierMapperBase
from .registry import register_carrier


@register_carrier("mydhl")
class MydhlMapper(CarrierMapperBase):
    """
    Mapper class for MYDHL carrier API responses to Universal Carrier Format.
    """

    FIELD_MAPPING = {
        "AWBNumber": UniversalFieldNames.TRACKING_NUMBER,
        "ActionStatus": UniversalFieldNames.STATUS,
        "MessageTime": UniversalFieldNames.LAST_UPDATE,
        "City": UniversalFieldNames.CITY,
        "PostalCode": UniversalFieldNames.POSTAL_CODE,
        "CountryCode": UniversalFieldNames.COUNTRY,
        "ServiceType": UniversalFieldNames.CARRIER_SERVICE,
        "ShipmentIdentificationNumber": UniversalFieldNames.SHIPMENT_NUMBER,
        "LabelImage": UniversalFieldNames.LABEL_BASE64,
        "GraphicImage": UniversalFieldNames.LABEL_BASE64,
        "DocumentImage": UniversalFieldNames.PROOF_OF_DELIVERY,
        "DeliveryDateCode": UniversalFieldNames.ESTIMATED_DELIVERY,
        "ChargeAmount": UniversalFieldNames.COST,
        "Currency": UniversalFieldNames.CURRENCY,
        "PersonName": UniversalFieldNames.SIGNED_BY,
        "EventCode": UniversalFieldNames.EVENT_TYPE,
        "Description": UniversalFieldNames.EVENT_DESCRIPTION,
        "Date": UniversalFieldNames.EVENT_DATETIME,
        "Time": UniversalFieldNames.EVENT_DATETIME,
        "FacilityCode": UniversalFieldNames.CURRENT_LOCATION,
        "ServiceAreaCode": UniversalFieldNames.CURRENT_LOCATION,
        "TrackingNumber": UniversalFieldNames.TRACKING_NUMBER,
    }

    STATUS_MAPPING = {
        "Success": "delivered",
        "No Shipments Found": "not_found",
        "In Transit": "in_transit",
        "Delivered": "delivered",
        "Exception": "exception",
        "Pending": "pending",
    }

    def map_tracking_response(self, carrier_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Maps MYDHL tracking response to universal tracking format.

        Args:
            carrier_response (Dict[str, Any]): Carrier-specific tracking response.

        Returns:
            Dict[str, Any]: Universal tracking response dictionary.
        """
        universal: Dict[str, Any] = {}

        try:
            tracking_info = carrier_response.get("TrackingResponse", {})
            awb_info_list = tracking_info.get("AWBInfo", {}).get(
                "ArrayOfAWBInfoItem", []
            )
            if not awb_info_list:
                return universal

            # Process first AWBInfo item (assuming single tracking number)
            awb_info = awb_info_list[0]

            # Tracking Number
            trk_num = awb_info.get("AWBNumber")
            if trk_num:
                universal[UniversalFieldNames.TRACKING_NUMBER] = trk_num

            # Status
            status_info = awb_info.get("Status", {})
            action_status = status_info.get("ActionStatus")
            if action_status:
                universal[UniversalFieldNames.STATUS] = self.STATUS_MAPPING.get(
                    action_status, action_status.lower()
                )

            # Last Update - use latest event datetime if available
            last_update = None
            pieces = (
                awb_info.get("Pieces", {})
                .get("PieceInfo", {})
                .get("ArrayOfPieceInfoItem", [])
            )
            if pieces:
                last_event_dt = None
                for piece in pieces:
                    piece_events = piece.get("PieceEvent", {}).get(
                        "ArrayOfPieceEventItem", []
                    )
                    for event in piece_events:
                        dt = self._parse_event_datetime(event)
                        if dt and (last_event_dt is None or dt > last_event_dt):
                            last_event_dt = dt
                if last_event_dt:
                    last_update = last_event_dt.isoformat()
            if not last_update:
                # fallback to ShipmentInfo EstimatedDeliveryDate or None
                shipment_info = awb_info.get("ShipmentInfo", {})
                est_del = shipment_info.get("EstimatedDeliveryDate")
                if est_del:
                    last_update = self._parse_date(est_del)
            if last_update:
                universal[UniversalFieldNames.LAST_UPDATE] = last_update

            # Current Location - use last event's ServiceArea Description or FacilityCode
            current_location = None
            if pieces:
                last_event = None
                last_event_dt = None
                for piece in pieces:
                    piece_events = piece.get("PieceEvent", {}).get(
                        "ArrayOfPieceEventItem", []
                    )
                    for event in piece_events:
                        dt = self._parse_event_datetime(event)
                        if dt and (last_event_dt is None or dt > last_event_dt):
                            last_event_dt = dt
                            last_event = event
                if last_event:
                    service_area = last_event.get("ServiceArea", {})
                    desc = service_area.get("Description")
                    code = service_area.get("ServiceAreaCode")
                    if desc:
                        current_location = desc
                    elif code:
                        current_location = code
            if current_location:
                universal[UniversalFieldNames.CURRENT_LOCATION] = current_location

            # Events - map all piece events to universal events list
            events = []
            for piece in pieces:
                piece_events = piece.get("PieceEvent", {}).get(
                    "ArrayOfPieceEventItem", []
                )
                for event in piece_events:
                    ev = self._map_event(event)
                    if ev:
                        events.append(ev)
            if events:
                # Sort events by datetime ascending
                events.sort(
                    key=lambda e: e.get(UniversalFieldNames.EVENT_DATETIME) or ""
                )
                universal[UniversalFieldNames.EVENTS] = events

            # Estimated Delivery
            est_del = awb_info.get("ShipmentInfo", {}).get("EstimatedDeliveryDate")
            if est_del:
                est_del_parsed = self._parse_date(est_del)
                if est_del_parsed:
                    universal[UniversalFieldNames.ESTIMATED_DELIVERY] = est_del_parsed

            # Origin and Destination Country
            shipment_info = awb_info.get("ShipmentInfo", {})
            origin_area = shipment_info.get("OriginServiceArea", {})
            dest_area = shipment_info.get("DestinationServiceArea", {})
            origin_country = origin_area.get("ServiceAreaCode")
            dest_country = dest_area.get("ServiceAreaCode")
            if origin_country:
                universal[UniversalFieldNames.ORIGIN_COUNTRY] = origin_country
            if dest_country:
                universal[UniversalFieldNames.DESTINATION_COUNTRY] = dest_country

        except Exception:
            # Fail silently and return what we have
            pass

        return universal

    def _parse_date(self, date_str: Optional[str]) -> Optional[str]:
        """
        Parses a date string in YYYY-MM-DD or YYYYMMDD format to ISO 8601 string.

        Args:
            date_str (Optional[str]): Date string.

        Returns:
            Optional[str]: ISO 8601 date string or None if parsing fails.
        """
        if not date_str:
            return None
        for fmt in ("%Y-%m-%d", "%Y%m%d", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S"):
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.isoformat()
            except (ValueError, TypeError):
                continue
        return None

    def _parse_event_datetime(self, event: Dict[str, Any]) -> Optional[datetime]:
        """
        Parses event date and time with optional GMT offset into datetime object.

        Args:
            event (Dict[str, Any]): Event dictionary containing Date, Time, GMTOffset.

        Returns:
            Optional[datetime]: Parsed datetime or None.
        """
        date_str = event.get("Date")
        time_str = event.get("Time")
        gmt_offset = event.get("GMTOffset")

        if not date_str:
            return None

        dt_str = date_str
        if time_str:
            dt_str += "T" + time_str
        if gmt_offset:
            # Normalize GMT offset format if needed
            offset = gmt_offset.strip()
            if offset.startswith("+") or offset.startswith("-"):
                dt_str += offset
            else:
                dt_str += "+" + offset

        # Try parsing with timezone
        for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
            try:
                return datetime.strptime(dt_str, fmt)
            except (ValueError, TypeError):
                continue
        return None

    def _map_event(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Maps a single piece event to universal event format.

        Args:
            event (Dict[str, Any]): Carrier event dictionary.

        Returns:
            Optional[Dict[str, Any]]: Universal event dictionary or None.
        """
        if not event:
            return None

        ev: Dict[str, Any] = {}

        # Event datetime
        dt = self._parse_event_datetime(event)
        if dt:
            ev[UniversalFieldNames.EVENT_DATETIME] = dt.isoformat()

        # Event type and description
        service_event = event.get("ServiceEvent", {})
        event_code = service_event.get("EventCode")
        description = service_event.get("Description")
        if event_code:
            ev[UniversalFieldNames.EVENT_TYPE] = event_code
        if description:
            ev[UniversalFieldNames.EVENT_DESCRIPTION] = description

        # Event location
        service_area = event.get("ServiceArea", {})
        location_desc = service_area.get("Description")
        location_code = service_area.get("ServiceAreaCode")
        if location_desc:
            ev[UniversalFieldNames.EVENT_LOCATION] = location_desc
        elif location_code:
            ev[UniversalFieldNames.EVENT_LOCATION] = location_code

        return ev

    def map_carrier_schema(
        self, carrier_schema: Dict[str, Any]
    ) -> UniversalCarrierFormat:
        """
        Maps the carrier-specific schema to the UniversalCarrierFormat.

        Args:
            carrier_schema (Dict[str, Any]): Carrier-specific schema dictionary.

        Returns:
            UniversalCarrierFormat: Mapped universal carrier format object.
        """
        # This is a placeholder implementation.
        # Actual mapping depends on carrier_schema structure and UniversalCarrierFormat constructor.
        # For now, return an empty UniversalCarrierFormat.
        return UniversalCarrierFormat()
