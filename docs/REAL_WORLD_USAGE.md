# Real-World Usage: How This System Works in Production

## The Problem in Real-World E-Commerce

Imagine you're building an e-commerce platform (like Shopify, WooCommerce, or a custom solution). Your customers need to:

1. **Ship products** using multiple carriers (Royal Mail, DHL, FedEx, UPS, etc.)
2. **Track shipments** across all carriers
3. **Display tracking info** in a consistent format
4. **Handle returns** from any carrier
5. **Calculate shipping costs** from different carriers

**The Challenge:** Each carrier has:
- Different API endpoints
- Different field names (`tracking_number` vs `trk_num` vs `mailPieceId`)
- Different status values (`IN_TRANSIT` vs `in_transit` vs `In Transit`)
- Different response structures
- Different authentication methods

**Without this system:** You'd need to write custom code for each carrier, maintain it separately, and handle inconsistencies manually.

## How This System Solves It

### Step 1: Onboard a New Carrier (One-Time Setup)

```bash
# 1. Get carrier's PDF documentation
# (Download from their developer portal)

# 2. Extract schema automatically
docker-compose exec app python -m src.formatter \
    examples/royal_mail_api_docs.pdf \
    --output output/royal_mail_schema.json

# 3. Generate mapper code automatically
docker-compose exec app python -m src.mapper_generator_cli \
    output/royal_mail_schema.json \
    --output src/mappers/royal_mail_mapper.py

# 4. Review and customize mapper (if needed)
# Edit src/mappers/royal_mail_mapper.py to handle edge cases
```

**Time saved:** Weeks → Minutes

### Step 2: Use in Your Application (Production)

#### Scenario A: E-Commerce Checkout - Shipping Options

```python
# Your e-commerce application
from src.mappers.royal_mail_mapper import RoyalMailRestApiMapper
from src.mappers.dhl_express_mapper import DhlExpressMapper
from src.mappers.fedex_mapper import FedExMapper
import requests

class ShippingService:
    def __init__(self):
        self.mappers = {
            "royal_mail": RoyalMailRestApiMapper(),
            "dhl": DhlExpressMapper(),
            "fedex": FedExMapper(),
        }
        self.api_clients = {
            "royal_mail": RoyalMailAPIClient(),
            "dhl": DHLAPIClient(),
            "fedex": FedExAPIClient(),
        }
    
    def get_shipping_rates(self, origin, destination, weight, carrier):
        """
        Get shipping rates from any carrier.
        All responses are normalized to the same format.
        """
        # Call carrier-specific API
        raw_response = self.api_clients[carrier].get_rates(
            origin=origin,
            destination=destination,
            weight=weight
        )
        
        # Transform to universal format
        mapper = self.mappers[carrier]
        universal_response = mapper.map_rates_response(raw_response)
        
        # Now you have consistent format regardless of carrier
        return {
            "carrier": carrier,
            "service": universal_response["service_name"],
            "cost": universal_response["cost"],
            "estimated_delivery": universal_response["estimated_delivery"],
            "tracking_available": universal_response["tracking_available"]
        }
    
    def create_shipment(self, order, carrier):
        """
        Create a shipment with any carrier.
        All requests are normalized to the same format.
        """
        # Prepare universal shipment data
        shipment_data = {
            "tracking_number": order.tracking_number,
            "origin": self._format_address(order.shipping_address),
            "destination": self._format_address(order.delivery_address),
            "weight": order.total_weight,
            "items": order.items
        }
        
        # Transform to carrier-specific format (reverse mapping)
        mapper = self.mappers[carrier]
        carrier_request = mapper.map_shipment_request(shipment_data)
        
        # Send to carrier API
        response = self.api_clients[carrier].create_shipment(carrier_request)
        
        # Transform response back to universal format
        return mapper.map_shipment_response(response)
```

#### Scenario B: Order Tracking Page

```python
# Your customer-facing tracking page
from src.mappers.royal_mail_mapper import RoyalMailRestApiMapper
from src.mappers.dhl_express_mapper import DhlExpressMapper

class TrackingService:
    def __init__(self):
        self.mappers = {
            "royal_mail": RoyalMailRestApiMapper(),
            "dhl": DhlExpressMapper(),
            # ... other carriers
        }
    
    def get_tracking_info(self, order):
        """
        Get tracking info for any order, regardless of carrier.
        Returns consistent format for your frontend.
        """
        carrier = order.shipping_carrier
        tracking_number = order.tracking_number
        
        # Call carrier API
        raw_response = self._call_carrier_api(carrier, tracking_number)
        
        # Transform to universal format
        mapper = self.mappers[carrier]
        universal_tracking = mapper.map_tracking_response(raw_response)
        
        # Your frontend always receives the same structure:
        return {
            "tracking_number": universal_tracking["tracking_number"],
            "status": universal_tracking["status"],  # Always: "in_transit", "delivered", etc.
            "current_location": universal_tracking["current_location"],
            "estimated_delivery": universal_tracking["estimated_delivery"],
            "events": universal_tracking["events"],  # Always same structure
            "carrier": carrier
        }
    
    def display_tracking_page(self, order):
        """
        Your frontend template only needs to handle ONE format.
        """
        tracking = self.get_tracking_info(order)
        
        # HTML template (same for all carriers!)
        return f"""
        <div class="tracking-info">
            <h2>Tracking: {tracking['tracking_number']}</h2>
            <p>Status: {tracking['status']}</p>
            <p>Location: {tracking['current_location']['city']}</p>
            <p>Estimated Delivery: {tracking['estimated_delivery']}</p>
            
            <h3>Tracking History</h3>
            <ul>
                {''.join([f"<li>{event['description']} - {event['timestamp']}</li>" 
                          for event in tracking['events']])}
            </ul>
        </div>
        """
```

#### Scenario C: Multi-Carrier Shipping Dashboard

```python
# Admin dashboard showing all shipments
class ShippingDashboard:
    def __init__(self):
        self.mappers = load_all_mappers()  # Auto-discover all mappers
    
    def get_all_shipments(self, date_range):
        """
        Get shipments from ALL carriers in one consistent format.
        """
        all_shipments = []
        
        for carrier in ["royal_mail", "dhl", "fedex", "ups"]:
            # Get raw data from each carrier
            raw_shipments = self._fetch_carrier_shipments(carrier, date_range)
            
            # Transform each to universal format
            mapper = self.mappers[carrier]
            for raw in raw_shipments:
                universal = mapper.map_shipment_response(raw)
                all_shipments.append(universal)
        
        # Now you can sort, filter, aggregate ALL carriers together
        return sorted(all_shipments, key=lambda x: x["created_at"])
    
    def display_dashboard(self):
        """
        One dashboard for all carriers - same data structure!
        """
        shipments = self.get_all_shipments(last_30_days)
        
        # Group by status (works for ALL carriers)
        by_status = {}
        for shipment in shipments:
            status = shipment["status"]  # Always same format
            by_status.setdefault(status, []).append(shipment)
        
        # Display in your admin panel
        return render_template("dashboard.html", shipments_by_status=by_status)
```

## Real-World Architecture

### Your Application Stack

```
┌─────────────────────────────────────────────────┐
│         Your E-Commerce Application            │
│  (Django, FastAPI, Node.js, etc.)              │
└─────────────────────────────────────────────────┘
                      │
                      │ Uses Universal Format
                      ▼
┌─────────────────────────────────────────────────┐
│      Universal Carrier Formatter (This PoC)     │
│  ┌──────────────┐  ┌──────────────┐           │
│  │   Mappers    │  │  Validators  │           │
│  │              │  │              │           │
│  │ Royal Mail   │  │  Schema      │           │
│  │ DHL          │  │  Validation  │           │
│  │ FedEx        │  │              │           │
│  │ UPS          │  │              │           │
│  └──────────────┘  └──────────────┘           │
└─────────────────────────────────────────────────┘
                      │
                      │ Transforms to/from
                      ▼
┌─────────────────────────────────────────────────┐
│           Carrier APIs (External)              │
│  ┌──────────────┐  ┌──────────────┐           │
│  │ Royal Mail   │  │ DHL Express  │           │
│  │ API          │  │ API          │           │
│  └──────────────┘  └──────────────┘           │
│  ┌──────────────┐  ┌──────────────┐           │
│  │ FedEx API    │  │ UPS API      │           │
│  └──────────────┘  └──────────────┘           │
└─────────────────────────────────────────────────┘
```

### Data Flow Example: Customer Tracks Order

```
1. Customer clicks "Track Order" on your website
   ↓
2. Your app: GET /api/tracking/{order_id}
   ↓
3. Your app looks up: order.shipping_carrier = "royal_mail"
   ↓
4. Your app calls: RoyalMailAPIClient.get_tracking(tracking_number)
   ↓
5. Royal Mail API returns:
   {
     "mailPieceId": "RM123456789GB",
     "status": "IN_TRANSIT",
     "lastEventDateTime": "2026-01-26T14:30:00Z",
     ...
   }
   ↓
6. Your app uses mapper:
   mapper = RoyalMailRestApiMapper()
   universal = mapper.map_tracking_response(royal_mail_response)
   ↓
7. Universal format:
   {
     "tracking_number": "RM123456789GB",
     "status": "in_transit",  // Normalized!
     "last_update": "2026-01-26T14:30:00Z",
     ...
   }
   ↓
8. Your frontend receives consistent format
   (Same format whether it's Royal Mail, DHL, or FedEx)
   ↓
9. Customer sees tracking info in your UI
```

## Benefits in Production

### 1. **Consistent Frontend Code**
- One tracking page template works for all carriers
- One status display component
- One location display format

### 2. **Easier Maintenance**
- Add new carrier: Just generate mapper (minutes, not weeks)
- Update carrier API: Update one mapper file
- Bug fixes: Fix in one place, works for all carriers

### 3. **Better Analytics**
- Aggregate data across all carriers
- Compare performance: "Which carrier delivers fastest?"
- Unified reporting: "Total shipments by status"

### 4. **Faster Development**
- New features work for all carriers automatically
- Testing: Test once, works everywhere
- Onboarding: New carrier in hours, not weeks

## Example: Adding a New Carrier

**Traditional Way (Without This System):**
```
1. Read 200-page PDF documentation (2-3 days)
2. Write API client code (1-2 days)
3. Write mapping logic (2-3 days)
4. Write tests (1 day)
5. Debug edge cases (2-3 days)
6. Update frontend to handle new format (1 day)
Total: 2-3 weeks
```

**With This System:**
```
1. Download PDF (5 minutes)
2. Run: python -m src.formatter carrier.pdf (2 minutes)
3. Run: python -m src.mapper_generator_cli schema.json (1 minute)
4. Review generated mapper (30 minutes)
5. Test with real API (1 hour)
Total: ~2 hours
```

## Production Deployment

### Docker Setup
```yaml
# docker-compose.yml
services:
  app:
    build: .
    volumes:
      - ./src/mappers:/app/src/mappers
      - ./output:/app/output
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
```

### CI/CD Integration
```yaml
# .github/workflows/test.yml
- name: Test Mappers
  run: |
    docker-compose exec app pytest tests/unit/test_mappers/
    
- name: Validate Schemas
  run: |
    docker-compose exec app python -m src.core.validator output/*.json
```

## Real Companies Using Similar Patterns

- **Shopify**: Unified shipping API that works with 100+ carriers
- **ShipStation**: Multi-carrier shipping platform
- **EasyPost**: Shipping API that normalizes carrier differences
- **Shippo**: Multi-carrier shipping API

They all solve the same problem: **Normalize carrier differences so developers don't have to.**

## Next Steps for Production

1. **Add More Mappers**: Generate mappers for all carriers you use
2. **Add Caching**: Cache carrier API responses
3. **Add Error Handling**: Handle carrier API failures gracefully
4. **Add Monitoring**: Track mapper performance and errors
5. **Add Tests**: Test with real carrier API responses
6. **Add Rate Limiting**: Respect carrier API rate limits
7. **Add Retry Logic**: Handle transient carrier API failures

This PoC demonstrates the core concept. In production, you'd add these operational concerns around it.
