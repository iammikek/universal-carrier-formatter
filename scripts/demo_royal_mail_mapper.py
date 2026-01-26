#!/usr/bin/env python3
"""
Demo Script: Using Royal Mail Mapper

This script demonstrates how to use the Royal Mail mapper to transform
carrier-specific API responses into Universal Carrier Format.

Usage:
    python scripts/demo_royal_mail_mapper.py
"""

import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.mappers.royal_mail_mapper import RoyalMailRestApiMapper


def main():
    """Demonstrate Royal Mail mapper usage."""
    print("=" * 70)
    print("Royal Mail Mapper - Usage Demo")
    print("=" * 70)
    print()

    # Initialize mapper
    print("📦 Step 1: Initialize mapper...")
    mapper = RoyalMailRestApiMapper()
    print("   ✅ Mapper initialized")
    print()

    # Example Royal Mail API response (simulated)
    print("📥 Step 2: Sample Royal Mail API response...")
    royal_mail_response = {
        "mailPieceId": "RM123456789GB",
        "status": "IN_TRANSIT",
        "lastEventDateTime": "2026-01-26T14:30:00Z",
        "originCountry": "GB",
        "destinationCountry": "US",
        "events": [
            {
                "eventDateTime": "2026-01-26T14:30:00Z",
                "eventType": "IN_TRANSIT",
                "location": {
                    "city": "London",
                    "postcode": "SW1A 1AA",
                    "countryCode": "GB"
                },
                "description": "Item in transit"
            }
        ],
        "proofOfDelivery": None,
        "manifestId": "MAN123456"
    }

    print("   Raw Royal Mail response:")
    print(json.dumps(royal_mail_response, indent=2))
    print()

    # Transform to universal format
    print("🔄 Step 3: Transform to Universal Carrier Format...")
    universal_response = mapper.map_tracking_response(royal_mail_response)

    print("   Field mappings applied:")
    print(f"   - mailPieceId → tracking_number: {royal_mail_response.get('mailPieceId')} → {universal_response.get('tracking_number')}")
    print(f"   - status → status: {royal_mail_response.get('status')} → {universal_response.get('status')}")
    print(f"   - lastEventDateTime → last_update: {royal_mail_response.get('lastEventDateTime')} → {universal_response.get('last_update')}")
    print()

    print("   Universal format response:")
    print(json.dumps(universal_response, indent=2, default=str))
    print()

    print("✅ Transformation complete!")
    print()
    print("Summary:")
    print(f"  • Input: Royal Mail specific format")
    print(f"  • Output: Universal Carrier Format")
    print(f"  • Field mappings: {len(mapper.FIELD_MAPPING)} fields")
    print(f"  • Status mappings: {len(mapper.STATUS_MAPPING)} statuses")
    print()
    print("This universal JSON is now ready for e-commerce integration!")


if __name__ == "__main__":
    main()
