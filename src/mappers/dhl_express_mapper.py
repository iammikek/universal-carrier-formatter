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
        "ServiceType": UniversalFieldNames.SERVICE_NAME,
        "ShipmentIdentificationNumber": UniversalFieldNames.SHIPMENT_NUMBER,
        "LabelImage": UniversalFieldNames.LABEL_BASE64,
        "LabelImageFormat": "label_image_format",
        "GraphicImage": "label_graphic_image",
        "DeliveryDateCode": "delivery_date_code",
        "DeliveryTimeCode": "delivery_time_code",
        "VolumetricWeight": UniversalFieldNames.WEIGHT,
        "Currency": UniversalFieldNames.CURRENCY,
        "Amount": UniversalFieldNames.COST,
        "ChargeType": "charge_type",
        "ChargeAmount": "charge_amount",
        "ChargeName": "charge_name",
        "ChargeCurrencyCode": "charge_currency_code",
        "PickupTimestamp": "pickup_timestamp",
        "DispatchConfirmationNumber": "dispatch_confirmation_number",
        "MessageReference": "message_reference",
        "ServiceInvocationID": "service_invocation_id",
        "Notification": "notification",
        "Warning": "warning",
        "PackagesResult": "packages_result",
        "PackageResult": "package_result",
        "TrackingNumber": UniversalFieldNames.TRACKING_NUMBER,
        "EventCode": "event_code",
        "Description": UniversalFieldNames.EVENT_DESCRIPTION,
        "Date": "event_date",
        "Time": "event_time",
        "GMTOffset": "gmt_offset",
        "Signatory": UniversalFieldNames.SIGNED_BY,
        "PieceNumber": "piece_number",
        "PieceContents": "piece_contents",
        "PickupWindowEarliestTime": "pickup_window_earliest_time",
        "PickupWindowLatestTime": "pickup_window_latest_time",
        "NextBusinessDayInd": "next_business_day_ind",
        "CutoffTime": "cutoff_time",
        "CutoffTimeOffset": "cutoff_time_offset",
        "TotalTransitDays": "total_transit_days",
        "PickupDayOfWeek": "pickup_day_of_week",
        "DestinationDayOfWeek": "destination_day_of_week",
        "FacilityCode": "facility_code",
        "ServiceAreaCode": "service_area_code",
        "OutboundSortCode": "outbound_sort_code",
        "InboundSortCode": "inbound_sort_code",
        "ReferenceID": "reference_id",
        "ReferenceType": "reference_type",
        "ShipmentReference": "shipment_reference",
        "ShipmentDate": "shipment_date",
        "Pieces": "pieces",
        "Weight": UniversalFieldNames.WEIGHT,
        "WeightUnit": "weight_unit",
        "EstimatedDeliveryDate": UniversalFieldNames.ESTIMATED_DELIVERY,
        "OriginServiceArea": "origin_service_area",
        "DestinationServiceArea": "destination_service_area",
        "CustomerAgreementInd": "customer_agreement_ind",
        "LocalServiceType": "local_service_type",
        "LocalServiceCountryCode": "local_service_country_code",
        "NetworkTypeCode": "network_type_code",
        "PickupAdditionalDays": "pickup_additional_days",
        "DeliveryAdditionalDays": "delivery_additional_days",
        "QuotedWeight": "quoted_weight",
        "UnitOfMeasurement": "unit_of_measurement",
        "PiecesEnabled": "pieces_enabled",
        "LevelOfDetails": "level_of_details",
        "LanguageCode": "language_code",
        "LanguageScriptCode": "language_script_code",
        "LanguageCountryCode": "language_country_code",
        "AWBInfo": "awb_info",
        "ArrayOfAWBInfoItem": "array_of_awb_info_item",
        "PieceInfo": "piece_info",
        "ArrayOfPieceInfoItem": "array_of_piece_info_item",
        "PieceEvent": "piece_event",
        "ArrayOfPieceEventItem": "array_of_piece_event_item",
        "ServiceEvent": "service_event",
        "ServiceArea": "service_area",
        "ShipperReference": "shipper_reference",
        "ReferenceID": "reference_id",
        "ReferenceType": "reference_type",
        "ShipmentReferences": "shipment_references",
        "ShipmentReferenceType": "shipment_reference_type",
        "ShipmentReferenceValue": "shipment_reference_value",
        "ShipmentInfo": "shipment_info",
        "Shipper": "shipper",
        "Recipient": "recipient",
        "Contact": "contact",
        "PersonName": "person_name",
        "CompanyName": "company_name",
        "PhoneNumber": "phone_number",
        "EmailAddress": "email_address",
        "MobilePhoneNumber": "mobile_phone_number",
        "Address": "address",
        "StreetLines": UniversalFieldNames.ADDRESS_LINE_1,
        "StreetLines2": UniversalFieldNames.ADDRESS_LINE_2,
        "CityDistrict": "city_district",
        "StateOrProvinceCode": UniversalFieldNames.STATE,
        "Suburb": "suburb",
        "StateOrProvinceName": "state_or_province_name",
        "CountryName": "country_name",
        "ShipmentDateRange": "shipment_date_range",
        "From": "from_date",
        "To": "to_date",
        "ShipmentNotification": "shipment_notification",
        "NotificationMethod": "notification_method",
        "BespokeMessage": "bespoke_message",
        "LanguageCode": "language_code",
        "LanguageCountryCode": "language_country_code",
        "ShipmentReferences": "shipment_references",
        "ShipmentReference": "shipment_reference",
        "Value": "value",
        "Type": "type",
        "ShipmentPickupYearAndMonth": "shipment_pickup_year_and_month",
        "DocumentTypeName": "document_type_name",
        "DocumentImageFormat": "document_image_format",
        "DocumentContent": "document_content",
        "DocumentName": "document_name",
        "DocumentFormat": "document_format",
        "DocumentImage": "document_image",
    }

    STATUS_MAPPING = {
        "Success": "delivered",
        "No Shipments Found": "not_found",
        "In Transit": "in_transit",
        "Delivered": "delivered",
        "Exception": "exception",
        "Pending": "pending",
        "Cancelled": "cancelled",
        "Info Received": "info_received",
        "Shipment Info Received": "info_received",
    }

    def map_tracking_response(self, carrier_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Maps the MYDHL tracking response to the Universal Carrier Format.

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

            # Map tracking number
            trk_num = awb_info.get("AWBNumber")
            if trk_num:
                universal[UniversalFieldNames.TRACKING_NUMBER] = trk_num

            # Map status
            status = awb_info.get("Status", {}).get("ActionStatus")
            if status:
                universal[UniversalFieldNames.STATUS] = self.STATUS_MAPPING.get(
                    status, status.lower()
                )

            # Map estimated delivery date
            est_del = awb_info.get("ShipmentInfo", {}).get("EstimatedDeliveryDate")
            if est_del:
                parsed_date = self._parse_date(est_del)
                if parsed_date:
                    universal[UniversalFieldNames.ESTIMATED_DELIVERY] = (
                        parsed_date.isoformat()
                    )

            # Map last update from latest event date/time if available
            pieces = (
                awb_info.get("Pieces", {})
                .get("PieceInfo", {})
                .get("ArrayOfPieceInfoItem", [])
            )
            latest_dt = None
            for piece in pieces:
                piece_events = piece.get("PieceEvent", {}).get(
                    "ArrayOfPieceEventItem", []
                )
                for event in piece_events:
                    dt = self._parse_event_datetime(event)
                    if dt and (latest_dt is None or dt > latest_dt):
                        latest_dt = dt
            if latest_dt:
                universal[UniversalFieldNames.LAST_UPDATE] = latest_dt.isoformat()

            # Map current location from last event's ServiceArea Description if available
            current_location = None
            if pieces:
                last_piece = pieces[-1]
                piece_events = last_piece.get("PieceEvent", {}).get(
                    "ArrayOfPieceEventItem", []
                )
                if piece_events:
                    last_event = piece_events[-1]
                    service_area = last_event.get("ServiceArea", {})
                    current_location = service_area.get("Description")
            if current_location:
                universal[UniversalFieldNames.CURRENT_LOCATION] = current_location

            # Map events history
            events = []
            for piece in pieces:
                piece_events = piece.get("PieceEvent", {}).get(
                    "ArrayOfPieceEventItem", []
                )
                for event in piece_events:
                    event_dt = self._parse_event_datetime(event)
                    if not event_dt:
                        continue
                    event_obj = {
                        UniversalFieldNames.EVENT_DATETIME: event_dt.isoformat(),
                        UniversalFieldNames.EVENT_DESCRIPTION: event.get(
                            "ServiceEvent", {}
                        ).get("Description"),
                        UniversalFieldNames.EVENT_LOCATION: event.get(
                            "ServiceArea", {}
                        ).get("Description"),
                        UniversalFieldNames.EVENT_TYPE: event.get(
                            "ServiceEvent", {}
                        ).get("EventCode"),
                    }
                    events.append(event_obj)
            if events:
                # Sort events by datetime ascending
                events.sort(key=lambda x: x[UniversalFieldNames.EVENT_DATETIME])
                universal[UniversalFieldNames.EVENTS] = events

            # Map signed by if available from last event signatory
            if pieces and pieces[-1].get("PieceEvent", {}).get(
                "ArrayOfPieceEventItem", []
            ):
                last_event = pieces[-1]["PieceEvent"]["ArrayOfPieceEventItem"][-1]
                signatory = last_event.get("Signatory")
                if signatory:
                    universal[UniversalFieldNames.SIGNED_BY] = signatory

        except Exception:
            # Fail silently and return what we have
            pass

        return universal

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """
        Parses a date string in various formats to a datetime object.

        Args:
            date_str (str): Date string.

        Returns:
            Optional[datetime]: Parsed datetime or None if parsing fails.
        """
        date_formats = [
            "%Y-%m-%d",
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%S",
            "%Y%m%d",
            "%Y%m%d%H%M%S",
            "%Y-%m-%dT%H:%M:%S.%f%z",
        ]
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except (ValueError, TypeError):
                continue
        return None

    def _parse_event_datetime(self, event: Dict[str, Any]) -> Optional[datetime]:
        """
        Parses event date and time fields into a datetime object.

        Args:
            event (Dict[str, Any]): Event dictionary containing Date, Time, and GMTOffset.

        Returns:
            Optional[datetime]: Parsed datetime or None if parsing fails.
        """
        date_str = event.get("Date")
        time_str = event.get("Time")
        gmt_offset = event.get("GMTOffset")

        if not date_str:
            return None

        try:
            # Parse date
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        except (ValueError, TypeError):
            try:
                date_obj = datetime.strptime(date_str, "%Y%m%d")
            except (ValueError, TypeError):
                return None

        if time_str:
            try:
                time_obj = datetime.strptime(time_str, "%H:%M:%S").time()
            except (ValueError, TypeError):
                try:
                    time_obj = datetime.strptime(time_str, "%H:%M").time()
                except (ValueError, TypeError):
                    time_obj = None
            if time_obj:
                date_obj = datetime.combine(date_obj.date(), time_obj)

        # Handle GMT offset if present (e.g. +0100 or +01:00)
        if gmt_offset:
            try:
                # Normalize offset string
                offset_str = gmt_offset.replace(":", "")
                if len(offset_str) == 5 and (
                    offset_str.startswith("+") or offset_str.startswith("-")
                ):
                    hours = int(offset_str[1:3])
                    minutes = int(offset_str[3:5])
                    delta_minutes = hours * 60 + minutes
                    if offset_str.startswith("-"):
                        delta_minutes = -delta_minutes
                    from datetime import timedelta, timezone

                    tzinfo = timezone(timedelta(minutes=delta_minutes))
                    date_obj = date_obj.replace(tzinfo=tzinfo)
            except Exception:
                pass

        return date_obj

    def map_carrier_schema(
        self, carrier_schema: Dict[str, Any]
    ) -> UniversalCarrierFormat:
        """
        Maps the carrier-specific schema to the UniversalCarrierFormat.

        Args:
            carrier_schema (Dict[str, Any]): Carrier-specific schema dictionary.

        Returns:
            UniversalCarrierFormat: The universal carrier format object.
        """
        # This is a placeholder implementation.
        # Actual mapping depends on carrier_schema structure and UniversalCarrierFormat definition.
        universal_data = {}

        # Example: map top-level fields if present
        for carrier_field, universal_field in self.FIELD_MAPPING.items():
            value = carrier_schema.get(carrier_field)
            if value is not None:
                universal_data[universal_field] = value

        return UniversalCarrierFormat(**universal_data)  # type: ignore
