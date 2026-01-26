from typing import Any, Dict, Optional
from datetime import datetime
from ..core.schema import UniversalCarrierFormat, UniversalTrackingStatus, UniversalLocation, UniversalError

class RoyalMailGroupMapper:
    """
    Mapper class for Royal Mail Group API responses to Universal Carrier Format.
    """

    FIELD_MAPPING = {
        # As the schema does not specify response fields, this is a placeholder.
        # Actual carrier fields should be mapped here to universal fields.
        # Example:
        # "locationId": "location_id",
        # "locationName": "name",
        # "address": "address",
        # "postcode": "postal_code",
        # "countryCode": "country",
        # "status": "status",
        # "trackingNumber": "tracking_number",
    }

    STATUS_MAPPING = {
        # No tracking status info provided in schema, placeholder for future use.
        # Example:
        # "DELIVERED": UniversalTrackingStatus.DELIVERED,
        # "IN_TRANSIT": UniversalTrackingStatus.IN_TRANSIT,
        # "EXCEPTION": UniversalTrackingStatus.EXCEPTION,
    }

    def map_tracking_response(self, carrier_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Maps a Royal Mail Group tracking or location response to the Universal Carrier Format.

        Args:
            carrier_response (Dict[str, Any]): The raw response from Royal Mail Group API.

        Returns:
            Dict[str, Any]: A dictionary conforming to UniversalCarrierFormat.
        """
        universal_response: Dict[str, Any] = {}

        # Since the schema does not specify tracking response structure,
        # this method assumes a generic mapping approach for location data.

        # Attempt to map locations if present
        locations = carrier_response.get("locations") or carrier_response.get("locationList") or carrier_response.get("data")
        if locations and isinstance(locations, list):
            universal_locations = []
            for loc in locations:
                mapped_location = self._map_location(loc)
                if mapped_location:
                    universal_locations.append(mapped_location)
            universal_response["locations"] = universal_locations

        # Map errors if present
        errors = carrier_response.get("errors") or carrier_response.get("error")
        if errors:
            universal_response["errors"] = self._map_errors(errors)

        # Map tracking number if present
        tracking_number = carrier_response.get("trackingNumber") or carrier_response.get("trk_num")
        if tracking_number:
            universal_response["tracking_number"] = tracking_number

        # Map status if present
        status = carrier_response.get("status")
        if status:
            universal_response["status"] = self.STATUS_MAPPING.get(status.upper(), status.lower())

        return universal_response

    def _map_location(self, location_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Helper method to map a single location dictionary from carrier format to universal format.

        Args:
            location_data (Dict[str, Any]): Carrier location data.

        Returns:
            Optional[Dict[str, Any]]: Mapped location dictionary or None if invalid.
        """
        if not location_data or not isinstance(location_data, dict):
            return None

        # Extract fields with safe defaults
        location_id = location_data.get("locationId") or location_data.get("id")
        name = location_data.get("locationName") or location_data.get("name")
        address = location_data.get("address") or location_data.get("addressLine1")
        city = location_data.get("city")
        postal_code = location_data.get("postcode") or location_data.get("postalCode")
        country_code = location_data.get("countryCode") or location_data.get("country")
        phone = location_data.get("phoneNumber") or location_data.get("phone")
        opening_hours = location_data.get("openingHours")

        # Compose universal location dict
        universal_location = {
            "location_id": location_id,
            "name": name,
            "address": address,
            "city": city,
            "postal_code": postal_code,
            "country": self._normalize_country_code(country_code),
            "phone": phone,
            "opening_hours": opening_hours,
        }

        # Remove keys with None values
        universal_location = {k: v for k, v in universal_location.items() if v is not None}

        return universal_location if universal_location else None

    def _map_errors(self, errors: Any) -> Optional[list]:
        """
        Helper method to map error information from carrier response.

        Args:
            errors (Any): Error information from carrier response.

        Returns:
            Optional[list]: List of UniversalError dicts or None.
        """
        if not errors:
            return None

        error_list = []
        if isinstance(errors, dict):
            errors = [errors]

        for err in errors:
            code = err.get("code") or err.get("statusCode")
            message = err.get("message") or err.get("description") or err.get("error")
            error_list.append({
                "code": code,
                "message": message,
            })

        return error_list if error_list else None

    def _normalize_country_code(self, country_code: Optional[str]) -> Optional[str]:
        """
        Normalize country code to ISO 3166-1 alpha-2 uppercase format.

        Args:
            country_code (Optional[str]): Country code string.

        Returns:
            Optional[str]: Normalized country code or None.
        """
        if not country_code or not isinstance(country_code, str):
            return None
        country_code = country_code.strip().upper()
        if len(country_code) == 2:
            return country_code
        # Additional normalization logic can be added here if needed
        return None

    def _parse_date(self, date_str: Optional[str]) -> Optional[str]:
        """
        Parse date string to ISO 8601 format.

        Args:
            date_str (Optional[str]): Date string.

        Returns:
            Optional[str]: ISO 8601 formatted date string or None.
        """
        if not date_str or not isinstance(date_str, str):
            return None
        try:
            dt = datetime.fromisoformat(date_str)
            return dt.isoformat()
        except ValueError:
            # Attempt other common date formats if needed
            try:
                dt = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%fZ")
                return dt.isoformat()
            except ValueError:
                return None

    def map_carrier_schema(self, carrier_schema: Dict[str, Any]) -> UniversalCarrierFormat:
        """
        Maps the carrier's schema metadata to the UniversalCarrierFormat schema object.

        Args:
            carrier_schema (Dict[str, Any]): Carrier schema metadata.

        Returns:
            UniversalCarrierFormat: The universal carrier format schema object.
        """
        # As the schema is mostly metadata, map relevant fields
        base_url = carrier_schema.get("base_url", "")
        version = carrier_schema.get("version", "")
        name = carrier_schema.get("name", "Royal Mail Group")
        description = carrier_schema.get("description", "")
        rate_limits = carrier_schema.get("rate_limits", [])

        # Compose UniversalCarrierFormat object
        universal_schema = UniversalCarrierFormat(
            name=name,
            base_url=base_url,
            version=version,
            description=description,
            rate_limits=rate_limits,
            authentication=carrier_schema.get("authentication", []),
            endpoints=carrier_schema.get("endpoints", []),
        )
        return universal_schema