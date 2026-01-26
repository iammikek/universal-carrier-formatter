from datetime import datetime
from typing import Any, Dict, List, Optional

from ..core import UniversalFieldNames
from ..core.schema import UniversalCarrierFormat


class MydhlApiMapper:
    """
    Mapper class for MYDHL API responses to Universal Carrier Format.
    """

    FIELD_MAPPING = {
        "AWBNumber": UniversalFieldNames.TRACKING_NUMBER,
        "Status.ActionStatus": UniversalFieldNames.STATUS,
        "ShipmentInfo.ShipperName": UniversalFieldNames.CURRENT_LOCATION,
        "ShipmentInfo.ShipmentDate": UniversalFieldNames.LAST_UPDATE,
        "ShipmentInfo.DestinationServiceArea.Description": UniversalFieldNames.CITY,
        "ShipmentInfo.DestinationServiceArea.ServiceAreaCode": UniversalFieldNames.POSTAL_CODE,
        "ShipmentInfo.DestinationServiceArea.CountryCode": UniversalFieldNames.DESTINATION_COUNTRY,
        "ShipmentInfo.OriginServiceArea.ServiceAreaCode": UniversalFieldNames.POSTAL_CODE,  # Origin postal code
        "ShipmentInfo.OriginServiceArea.CountryCode": UniversalFieldNames.ORIGIN_COUNTRY,
        "LabelImage.GraphicImage": UniversalFieldNames.LABEL_BASE64,
        "ShipmentIdentificationNumber": UniversalFieldNames.SHIPMENT_NUMBER,
        "Service.ServiceName": UniversalFieldNames.SERVICE_NAME,
        "TotalNet.Amount": UniversalFieldNames.COST,
        "TotalNet.Currency": UniversalFieldNames.CURRENCY,
    }

    STATUS_MAPPING = {
        "DELIVERED": "delivered",
        "IN_TRANSIT": "in_transit",
        "EXCEPTION": "exception",
        "PENDING": "pending",
        "INFO_RECEIVED": "info_received",
        "OUT_FOR_DELIVERY": "out_for_delivery",
        "FAILED_ATTEMPT": "failed_attempt",
        "CANCELLED": "cancelled",
        "RETURNED": "returned",
    }

    def map_tracking_response(self, carrier_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Maps the MYDHL API tracking response to the Universal Carrier Format.

        Args:
            carrier_response (Dict[str, Any]): The raw response from MYDHL API.

        Returns:
            Dict[str, Any]: The mapped response in Universal Carrier Format.
        """
        universal_response: Dict[str, Any] = {}

        try:
            awb_info_list = (
                carrier_response.get("TrackingResponse", {})
                .get("AWBInfo", {})
                .get("ArrayOfAWBInfoItem", [])
            )
            if not awb_info_list:
                return universal_response

            awb_info = awb_info_list[0]  # Assuming single AWB per request

            # Map tracking number
            tracking_number = awb_info.get("AWBNumber")
            if tracking_number:
                universal_response[UniversalFieldNames.TRACKING_NUMBER] = (
                    tracking_number
                )

            # Map status
            status = awb_info.get("Status", {}).get("ActionStatus")
            if status:
                universal_response[UniversalFieldNames.STATUS] = (
                    self.STATUS_MAPPING.get(status.upper(), status.lower())
                )

            # Map last update datetime from latest shipment event if available
            shipment_events = (
                awb_info.get("ShipmentInfo", {})
                .get("ShipmentEvent", {})
                .get("ArrayOfShipmentEventItem", [])
            )
            last_update = None
            if shipment_events:
                # Find the latest event by date and time
                last_event = self._get_latest_event(shipment_events)
                if last_event:
                    last_update = self._parse_event_datetime(
                        last_event.get("Date"),
                        last_event.get("Time"),
                        last_event.get("GMTOffset"),
                    )
            if last_update:
                universal_response[UniversalFieldNames.LAST_UPDATE] = last_update

            # Map current location from latest event's ServiceArea Description or ShipmentInfo DestinationServiceArea Description
            current_location = None
            if shipment_events:
                last_event = self._get_latest_event(shipment_events)
                if last_event:
                    service_area = last_event.get("ServiceArea", {})
                    current_location = service_area.get("Description")
            if not current_location:
                current_location = (
                    awb_info.get("ShipmentInfo", {})
                    .get("DestinationServiceArea", {})
                    .get("Description")
                )
            if current_location:
                universal_response[UniversalFieldNames.CURRENT_LOCATION] = (
                    current_location
                )

            # Map estimated delivery date
            est_delivery = awb_info.get("ShipmentInfo", {}).get("EstimatedDeliveryDate")
            if est_delivery:
                est_delivery_dt = self._parse_date(est_delivery)
                if est_delivery_dt:
                    universal_response[UniversalFieldNames.ESTIMATED_DELIVERY] = (
                        est_delivery_dt
                    )

            # Map events history
            events = []
            for event in shipment_events:
                event_datetime = self._parse_event_datetime(
                    event.get("Date"), event.get("Time"), event.get("GMTOffset")
                )
                event_desc = event.get("ServiceEvent", {}).get("Description")
                event_location = event.get("ServiceArea", {}).get("Description")
                event_type = event.get("ServiceEvent", {}).get("EventCode")
                if event_datetime or event_desc or event_location or event_type:
                    events.append(
                        {
                            UniversalFieldNames.EVENT_DATETIME: event_datetime,
                            UniversalFieldNames.EVENT_DESCRIPTION: event_desc,
                            UniversalFieldNames.EVENT_LOCATION: event_location,
                            UniversalFieldNames.EVENT_TYPE: event_type,
                        }
                    )
            if events:
                universal_response[UniversalFieldNames.EVENTS] = events

            # Map signed by if available (from last event's Signatory)
            if shipment_events:
                last_event = self._get_latest_event(shipment_events)
                signed_by = last_event.get("Signatory")
                if signed_by:
                    universal_response[UniversalFieldNames.SIGNED_BY] = signed_by

            # Map proof of delivery if available (base64 image from DocumentImageResponse or ePOD)
            # This requires separate call, so not mapped here.

        except Exception:
            # Fail silently and return what is mapped so far
            pass

        return universal_response

    def _get_latest_event(
        self, events: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Returns the latest event from a list of events based on Date and Time.

        Args:
            events (List[Dict[str, Any]]): List of event dictionaries.

        Returns:
            Optional[Dict[str, Any]]: The latest event dictionary or None.
        """
        latest_event = None
        latest_dt = None
        for event in events:
            dt = self._parse_event_datetime(
                event.get("Date"), event.get("Time"), event.get("GMTOffset")
            )
            if dt and (latest_dt is None or dt > latest_dt):
                latest_dt = dt
                latest_event = event
        return latest_event

    def _parse_event_datetime(
        self,
        date_str: Optional[str],
        time_str: Optional[str],
        gmt_offset: Optional[str],
    ) -> Optional[str]:
        """
        Parses event date and time strings with optional GMT offset into ISO 8601 string.

        Args:
            date_str (Optional[str]): Date string in 'YYYY-MM-DD' format.
            time_str (Optional[str]): Time string in 'HH:MM:SS' or 'HH:MM' format.
            gmt_offset (Optional[str]): GMT offset string like '+01:00' or '-05:00'.

        Returns:
            Optional[str]: ISO 8601 formatted datetime string or None if parsing fails.
        """
        if not date_str:
            return None
        try:
            if time_str:
                # Normalize time string to HH:MM:SS if needed
                if len(time_str.split(":")) == 2:
                    time_str += ":00"
                dt_str = f"{date_str} {time_str}"
                dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
            else:
                dt = datetime.strptime(date_str, "%Y-%m-%d")

            # Append GMT offset if present
            if gmt_offset:
                # Normalize offset format if needed (e.g. +0100 to +01:00)
                if len(gmt_offset) == 5 and (gmt_offset[3] != ":"):
                    gmt_offset = gmt_offset[:3] + ":" + gmt_offset[3:]
                iso_str = dt.isoformat() + gmt_offset
            else:
                iso_str = dt.isoformat()
            return iso_str
        except Exception:
            return None

    def _parse_date(self, date_str: str) -> Optional[str]:
        """
        Parses a date string in 'YYYY-MM-DD' format to ISO 8601 string.

        Args:
            date_str (str): Date string.

        Returns:
            Optional[str]: ISO 8601 date string or None if parsing fails.
        """
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            return dt.date().isoformat()
        except Exception:
            return None

    def map_carrier_schema(
        self, carrier_schema: Dict[str, Any]
    ) -> UniversalCarrierFormat:
        """
        Maps the carrier-specific schema to the UniversalCarrierFormat schema.

        Args:
            carrier_schema (Dict[str, Any]): The carrier-specific schema.

        Returns:
            UniversalCarrierFormat: The mapped universal carrier format object.
        """
        # This is a placeholder implementation as full schema mapping is complex.
        # Typically, this would convert the carrier schema JSON into the UniversalCarrierFormat dataclass.
        # For now, return an empty UniversalCarrierFormat or raise NotImplementedError.
        raise NotImplementedError(
            "Schema mapping is not implemented for MydhlApiMapper."
        )
