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
        "Status.ActionStatus": UniversalFieldNames.STATUS,
        "Status.Condition.ArrayOfConditionItem": "conditions",
        "ShipmentInfo.ShipperName": "shipper_name",
        "ShipmentInfo.ConsigneeName": "consignee_name",
        "ShipmentInfo.ShipmentDate": UniversalFieldNames.CREATED_AT,
        "ShipmentInfo.Pieces": "pieces",
        "ShipmentInfo.Weight": UniversalFieldNames.WEIGHT,
        "ShipmentInfo.WeightUnit": "weight_unit",
        "ShipmentInfo.ServiceType": UniversalFieldNames.SERVICE_NAME,
        "ShipmentInfo.ShipmentDescription": "shipment_description",
        "ShipmentInfo.EstimatedDeliveryDate": UniversalFieldNames.ESTIMATED_DELIVERY,
        "ShipmentInfo.OriginServiceArea.ServiceAreaCode": "origin_service_area_code",
        "ShipmentInfo.OriginServiceArea.Description": "origin_service_area_description",
        "ShipmentInfo.OriginServiceArea.OutboundSortCode": "origin_outbound_sort_code",
        "ShipmentInfo.DestinationServiceArea.ServiceAreaCode": "destination_service_area_code",
        "ShipmentInfo.DestinationServiceArea.Description": "destination_service_area_description",
        "ShipmentInfo.DestinationServiceArea.FacilityCode": "destination_facility_code",
        "ShipmentInfo.DestinationServiceArea.InboundSortCode": "destination_inbound_sort_code",
        "ShipmentInfo.Shipper.City": UniversalFieldNames.CITY,
        "ShipmentInfo.Shipper.Suburb": UniversalFieldNames.ADDRESS_LINE_2,
        "ShipmentInfo.Shipper.StateOrProvinceCode": UniversalFieldNames.STATE,
        "ShipmentInfo.Shipper.PostalCode": UniversalFieldNames.POSTAL_CODE,
        "ShipmentInfo.Shipper.CountryCode": UniversalFieldNames.ORIGIN_COUNTRY,
        "ShipmentInfo.Consignee.City": UniversalFieldNames.CITY,
        "ShipmentInfo.Consignee.Suburb": UniversalFieldNames.ADDRESS_LINE_2,
        "ShipmentInfo.Consignee.StateOrProvinceCode": UniversalFieldNames.STATE,
        "ShipmentInfo.Consignee.PostalCode": UniversalFieldNames.POSTAL_CODE,
        "ShipmentInfo.Consignee.CountryCode": UniversalFieldNames.DESTINATION_COUNTRY,
        "Pieces.PieceInfo.ArrayOfPieceInfoItem": "pieces_info",
        "Pieces.PieceInfo.ArrayOfPieceInfoItem.PieceDetails.AWBNumber": UniversalFieldNames.TRACKING_NUMBER,
        "Pieces.PieceInfo.ArrayOfPieceInfoItem.PieceDetails.LicensePlate": "license_plate",
        "Pieces.PieceInfo.ArrayOfPieceInfoItem.PieceDetails.PieceNumber": "piece_number",
        "Pieces.PieceInfo.ArrayOfPieceInfoItem.PieceDetails.ActualWeight": UniversalFieldNames.WEIGHT,
        "Pieces.PieceInfo.ArrayOfPieceInfoItem.PieceDetails.WeightUnit": "weight_unit",
        "Pieces.PieceInfo.ArrayOfPieceInfoItem.PieceEvent.ArrayOfPieceEventItem": "piece_events",
        "Pieces.PieceInfo.ArrayOfPieceInfoItem.PieceEvent.ArrayOfPieceEventItem.Date": "event_date",
        "Pieces.PieceInfo.ArrayOfPieceInfoItem.PieceEvent.ArrayOfPieceEventItem.Time": "event_time",
        "Pieces.PieceInfo.ArrayOfPieceInfoItem.PieceEvent.ArrayOfPieceEventItem.GMTOffset": "gmt_offset",
        "Pieces.PieceInfo.ArrayOfPieceInfoItem.PieceEvent.ArrayOfPieceEventItem.Signatory": UniversalFieldNames.SIGNED_BY,
        "Pieces.PieceInfo.ArrayOfPieceInfoItem.PieceEvent.ArrayOfPieceEventItem.ServiceEvent.Description": UniversalFieldNames.EVENT_DESCRIPTION,
        "Pieces.PieceInfo.ArrayOfPieceInfoItem.PieceEvent.ArrayOfPieceEventItem.ServiceEvent.EventCode": UniversalFieldNames.EVENT_TYPE,
        "Pieces.PieceInfo.ArrayOfPieceInfoItem.PieceEvent.ArrayOfPieceEventItem.ServiceArea.ServiceAreaCode": UniversalFieldNames.EVENT_LOCATION,
        "Pieces.PieceInfo.ArrayOfPieceInfoItem.PieceEvent.ArrayOfPieceEventItem.ShipperReference.ReferenceID": "shipper_reference_id",
        "Pieces.PieceInfo.ArrayOfPieceInfoItem.PieceEvent.ArrayOfPieceEventItem.ShipperReference.ReferenceType": "shipper_reference_type",
        "LabelImage": UniversalFieldNames.LABEL_BASE64,
        "LabelImage.LabelImageFormat": "label_format",
        "LabelImage.GraphicImage": UniversalFieldNames.LABEL_BASE64,
        "LabelImage.LabelImageName": "label_name",
        "LabelImage.packageSequenceNumber": "package_sequence_number",
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
        Maps the MYDHL tracking response to the universal tracking response format.

        Args:
            carrier_response (Dict[str, Any]): The raw response from MYDHL tracking API.

        Returns:
            Dict[str, Any]: The mapped universal tracking response.
        """
        universal: Dict[str, Any] = {}

        try:
            tracking_info = carrier_response.get("TrackingResponse", {})
            awb_info_list = tracking_info.get("AWBInfo", {}).get(
                "ArrayOfAWBInfoItem", []
            )
            if not awb_info_list:
                return universal

            # For simplicity, map the first AWBInfo item
            awb_info = awb_info_list[0]

            # Tracking Number
            awb_number = awb_info.get("AWBNumber")
            if awb_number:
                universal[UniversalFieldNames.TRACKING_NUMBER] = awb_number

            # Status
            status_info = awb_info.get("Status", {})
            action_status = status_info.get("ActionStatus")
            if action_status:
                universal[UniversalFieldNames.STATUS] = self.STATUS_MAPPING.get(
                    action_status, action_status.lower()
                )

            # Last Update - derive from latest event datetime if available
            last_update = None
            pieces = (
                awb_info.get("Pieces", {})
                .get("PieceInfo", {})
                .get("ArrayOfPieceInfoItem", [])
            )
            all_events = []
            for piece in pieces:
                piece_events = piece.get("PieceEvent", {}).get(
                    "ArrayOfPieceEventItem", []
                )
                for event in piece_events:
                    dt = self._parse_event_datetime(event)
                    if dt:
                        all_events.append(dt)
            if all_events:
                last_update = max(all_events)
                universal[UniversalFieldNames.LAST_UPDATE] = last_update.isoformat()

            # Current Location - from last event's ServiceArea Description or ServiceAreaCode
            current_location = None
            if pieces:
                last_piece_events = (
                    pieces[0].get("PieceEvent", {}).get("ArrayOfPieceEventItem", [])
                )
                if last_piece_events:
                    last_event = last_piece_events[-1]
                    service_area = last_event.get("ServiceArea", {})
                    current_location = service_area.get(
                        "Description"
                    ) or service_area.get("ServiceAreaCode")
            if current_location:
                universal[UniversalFieldNames.CURRENT_LOCATION] = current_location

            # Estimated Delivery Date
            shipment_info = awb_info.get("ShipmentInfo", {})
            est_delivery = shipment_info.get("EstimatedDeliveryDate")
            if est_delivery:
                dt = self._parse_date(est_delivery)
                if dt:
                    universal[UniversalFieldNames.ESTIMATED_DELIVERY] = dt.isoformat()

            # Events - map all piece events
            events = []
            for piece in pieces:
                piece_events = piece.get("PieceEvent", {}).get(
                    "ArrayOfPieceEventItem", []
                )
                for event in piece_events:
                    mapped_event = self._map_event(event)
                    if mapped_event:
                        events.append(mapped_event)
            if events:
                universal[UniversalFieldNames.EVENTS] = events

            # Signed By and Delivered At - from last event if status is delivered
            if universal.get(UniversalFieldNames.STATUS) == "delivered" and pieces:
                last_piece_events = (
                    pieces[0].get("PieceEvent", {}).get("ArrayOfPieceEventItem", [])
                )
                if last_piece_events:
                    last_event = last_piece_events[-1]
                    signatory = last_event.get("Signatory")
                    if signatory:
                        universal[UniversalFieldNames.SIGNED_BY] = signatory
                    dt = self._parse_event_datetime(last_event)
                    if dt:
                        universal[UniversalFieldNames.DELIVERED_AT] = dt.isoformat()

        except Exception:
            # Fail silently and return what we have
            pass

        return universal

    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """
        Parses a date string in various formats to a datetime object.

        Args:
            date_str (Optional[str]): Date string.

        Returns:
            Optional[datetime]: Parsed datetime or None.
        """
        if not date_str:
            return None
        for fmt in ("%Y-%m-%d", "%Y%m%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S%z"):
            try:
                return datetime.strptime(date_str, fmt)
            except (ValueError, TypeError):
                continue
        return None

    def _parse_event_datetime(self, event: Dict[str, Any]) -> Optional[datetime]:
        """
        Parses event date and time with GMT offset into a datetime object.

        Args:
            event (Dict[str, Any]): Event dictionary.

        Returns:
            Optional[datetime]: Parsed datetime or None.
        """
        date_str = event.get("Date")
        time_str = event.get("Time")
        gmt_offset = event.get("GMTOffset")

        if not date_str or not time_str:
            return None

        try:
            dt_str = f"{date_str} {time_str}"
            dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
            # GMTOffset is a string like "+0100" or "-0500"
            if (
                gmt_offset
                and len(gmt_offset) == 5
                and (gmt_offset.startswith("+") or gmt_offset.startswith("-"))
            ):
                sign = 1 if gmt_offset[0] == "+" else -1
                hours = int(gmt_offset[1:3])
                minutes = int(gmt_offset[3:5])
                _ = sign * (
                    hours * 60 + minutes
                )  # offset_minutes; kept for future tz use
                dt = dt.replace(tzinfo=None)  # naive datetime
                # We do not convert to aware datetime to keep consistent with naive, but could be extended
            return dt
        except (ValueError, TypeError):
            return None

    def _map_event(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Maps a single piece event to universal event format.

        Args:
            event (Dict[str, Any]): Event dictionary.

        Returns:
            Optional[Dict[str, Any]]: Mapped event or None.
        """
        if not event:
            return None
        mapped_event: Dict[str, Any] = {}

        dt = self._parse_event_datetime(event)
        if dt:
            mapped_event[UniversalFieldNames.EVENT_DATETIME] = dt.isoformat()

        description = event.get("ServiceEvent", {}).get("Description")
        if description:
            mapped_event[UniversalFieldNames.EVENT_DESCRIPTION] = description

        event_type = event.get("ServiceEvent", {}).get("EventCode")
        if event_type:
            mapped_event[UniversalFieldNames.EVENT_TYPE] = event_type

        location = event.get("ServiceArea", {}).get("Description") or event.get(
            "ServiceArea", {}
        ).get("ServiceAreaCode")
        if location:
            mapped_event[UniversalFieldNames.EVENT_LOCATION] = location

        return mapped_event if mapped_event else None

    def map_carrier_schema(
        self, carrier_schema: Dict[str, Any]
    ) -> UniversalCarrierFormat:
        """
        Maps the carrier-specific schema to the UniversalCarrierFormat.

        Args:
            carrier_schema (Dict[str, Any]): Carrier-specific schema.

        Returns:
            UniversalCarrierFormat: The universal carrier format object.
        """
        # This is a placeholder implementation as the full schema mapping is complex.
        # Typically, this would convert the carrier schema dict into a UniversalCarrierFormat instance.
        # For now, return an empty UniversalCarrierFormat or raise NotImplementedError.
        raise NotImplementedError("Schema mapping is not implemented for MYDHL.")
