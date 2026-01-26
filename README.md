# Universal Carrier Formatter

**Proof of Concept: Transforming messy carrier responses into universal, e-commerce-ready JSON.**

## The Proof of Concept

This PoC demonstrates three core capabilities:

### 1. Input: Messy, Non-Standard Carrier Response

Real-world carrier APIs return inconsistent, messy data. For example, an old DHL API might return:
```json
{
  "trk_num": "1234567890",
  "stat": "IN_TRANSIT",
  "loc": {
    "city": "London",
    "postcode": "SW1A 1AA"
  },
  "est_del": "2026-01-30"
}
```

### 2. Logic: Python/Pydantic Validation & Cleaning Engine

Our validation engine transforms this messy data:
- Validates against Universal Carrier Format schema
- Maps inconsistent field names (`trk_num` → `tracking_number`)
- Normalizes data formats (`stat` → standardized status enum)
- Cleans and validates nested structures
- Handles missing fields and edge cases

### 3. Output: Perfect Universal JSON

The result is a clean, standardized JSON that any e-commerce checkout can use:
```json
{
  "tracking_number": "1234567890",
  "status": "in_transit",
  "current_location": {
    "city": "London",
    "postal_code": "SW1A 1AA",
    "country": "GB"
  },
  "estimated_delivery": "2026-01-30T00:00:00Z"
}
```

## The Problem: The "PDF Gatekeeper"

Most global shipping carriers provide their integration specs in massive, inconsistently formatted PDF documents. Even after parsing those PDFs, you still face inconsistent API responses.

**The Manual Way:** A human engineer reads the PDF, manually identifies the API endpoints, maps the field names (e.g., is it `postal_code`, `postcode`, or `zip`?), and writes the validation logic. This takes **weeks**.

**The Autonomous Way:** An AI reads the PDF, extracts the logic, and generates the code. Then our validation engine ensures all responses conform to a universal standard.

## What This System Does

**Universal Carrier Formatter** is a Proof of Concept that demonstrates transforming messy, non-standard carrier API responses into perfect, universal JSON that any e-commerce checkout can use.

### The Solution

This PoC showcases a complete pipeline:

1. **Document Parser** (PDF → Structured JSON) - Extracts API schemas from PDFs using LLMs
2. **Core Schema** - Universal format all carriers map to (`core/schema.py`)
3. **Validation Engine** - Python/Pydantic engine that validates and cleans data (`core/validator.py`)
4. **Mappers** - Transform carrier-specific responses to universal format (`mappers/`)
5. **Blueprints** - Carrier configuration and integration logic (`blueprints/`)

### How It Works

```
Messy Carrier Response (DHL API)
         ↓
    Mapper (dpd_mapper.py, royal_mail.py)
         ↓
Validation Engine (core/validator.py)
         ↓
Perfect Universal JSON (ready for e-commerce checkout)
```

**Example Flow:**
```
Old DHL API Response → DpdMapper → CarrierValidator → Universal Format
```

**Basic Usage:**
```bash
# Parse a carrier PDF
python -m src.formatter --input examples/dhl_express_api_docs.pdf --output schema.json

# Or test the PDF parser directly
docker-compose exec app python -c "from src.pdf_parser import PdfParserService; p = PdfParserService(); print(p.extract_metadata('examples/dhl_express_api_docs.pdf'))"
```

**Output:** Standardized JSON containing API endpoints, authentication methods, request/response schemas, rate limits, and metadata that can be used to automatically generate integration code.

📖 **For detailed information**, see [docs/SYSTEM_OVERVIEW.md](docs/SYSTEM_OVERVIEW.md) - includes complete workflow, use cases, error handling, and technical architecture.

## Project Structure

```
universal-carrier-formatter/
├── core/                    # Universal schema and validation (the "Universal" part)
│   ├── schema.py            # Pydantic models defining Universal Carrier Format
│   └── validator.py         # Validation logic for carrier responses
├── mappers/                 # Carrier-specific response mappers
│   ├── dpd_mapper.py        # Maps DPD responses to universal format
│   └── royal_mail.py        # Maps Royal Mail responses to universal format
├── blueprints/              # Carrier configuration/logic
│   └── dhl_express.yaml     # Example blueprint for DHL Express
├── src/                     # Document parser (PDF → JSON)
│   └── pdf_parser.py        # PDF parsing service
├── tests/                   # Test files
├── examples/                # Sample PDFs and expected outputs
└── docs/                    # Documentation
```

## Quick Start

### Option 1: Docker Development (Recommended)

```bash
# Build and start containers
docker-compose up -d

# Run tests
make docker-test-tests

# Parse a carrier PDF
docker-compose exec app python -m src.formatter --input examples/sample.pdf --output output.json
```

### Option 2: Local Virtual Environment

```bash
# Create virtual environment
make setup

# Copy environment variables template
cp .env.example .env
# Edit .env and add your API keys

# Daily development
source .venv/bin/activate
make test
make format
make lint
```

## System Components

### 1. Document Parser (PDF → JSON)
Extracts structured API documentation from messy PDFs using LLMs. This is the **first part** of the system.

### 2. Core Schema
The universal format that all carriers map to. Defined in `core/schema.py` using Pydantic models.

### 3. Mappers
Transform carrier-specific API responses to the universal format. Each carrier has its own mapper (e.g., `dpd_mapper.py`, `royal_mail.py`).

### 4. Blueprints
YAML configuration files that define carrier-specific integration logic and endpoints.

## Proof of Concept Scenarios

The PoC demonstrates three core capabilities through concrete scenarios:

### Scenario 1: Automated Schema Mapping

**Problem:** Carrier PDF says "Sender Address Line 1 (required, max 50 chars)" but API uses `s_addr_1`. Manual mapping takes hours.

**PoC Solution:** Parser automatically generates mapping file in minutes:
```json
{
  "universal_field": "sender_address_line_1",
  "carrier_field": "s_addr_1",
  "required": true,
  "max_length": 50,
  "type": "string"
}
```

### Scenario 2: Constraint Extraction

**Problem:** Hidden business rules like "Weight must be in grams for Germany, kilograms for UK" are easy to miss.

**PoC Solution:** Parser extracts constraints and generates Pydantic validation logic automatically:
```python
@validator('weight')
def validate_weight(cls, v, values):
    if values.get('destination_country') == 'DE':
        return v * 1000 if values.get('unit') == 'kg' else v
    elif values.get('destination_country') == 'GB':
        return v / 1000 if values.get('unit') == 'g' else v
    return v
```

### Scenario 3: Edge Case Discovery

**Problem:** 200-page shipping guide contains route-specific requirements. Human engineers miss these until parcels get stuck.

**PoC Solution:** Parser scans entire document and flags all edge cases:
```json
{
  "edge_cases": [
    {
      "type": "customs_requirement",
      "route": "EU → Canary Islands",
      "requirement": "Customs declaration required",
      "documentation": "Section 4.2.3, page 87"
    }
  ]
}
```

### Scenario 4: Complete Transformation (E-Commerce Integration)

**Problem:** E-commerce checkout needs consistent data, but carriers return different formats.

**PoC Solution:** Complete transformation pipeline:
```
Messy DHL Response → Mapper → Validator → Universal JSON → Checkout Ready
```

**Example:**
```json
// Input (messy)
{"trk_num": "1234567890", "stat": "IN_TRANSIT", "loc": {"city": "London"}}

// Output (universal)
{
  "tracking_number": "1234567890",
  "status": "in_transit",
  "current_location": {
    "city": "London",
    "postal_code": "SW1A 1AA",
    "country": "GB"
  }
}
```

📖 **See [docs/SYSTEM_OVERVIEW.md](docs/SYSTEM_OVERVIEW.md) for detailed PoC scenarios with complete examples.**

## Universal Carrier Format

The project uses a standardized JSON schema to represent carrier API documentation. See `examples/expected_output.json` for a complete example.

The schema includes:
- **Endpoints**: API paths, methods, request/response schemas
- **Authentication**: API keys, OAuth, Bearer tokens, etc.
- **Parameters**: Query strings, path params, headers, body schemas
- **Rate Limits**: Request limits and periods
- **Metadata**: Carrier name, base URL, version, documentation links

Models are defined using Pydantic (similar to Laravel Eloquent models with validation).

## Testing

Tests use `pytest` (similar to PHPUnit in PHP):

```bash
# Run tests in tests/ directory (recommended)
make docker-test-tests

# Run with coverage
make docker-test-coverage

# Validate schema models (quick check)
docker-compose exec app python scripts/validate_schema.py
```

See [docs/TESTING.md](docs/TESTING.md) for complete testing guide.

## Try the Demo

See the PoC in action with a working mapper demo:

```bash
# Run the mapper demo (shows messy → universal transformation)
python scripts/demo_mapper.py

# Or in Docker
docker-compose exec app python scripts/demo_mapper.py
```

**What it demonstrates:**
- 📥 Input: Messy DPD response (`trk_num`, `stat`, `loc`, `est_del`)
- 🔄 Transformation: Field mapping, status normalization, date formatting
- ✅ Validation: Data cleaning and structure validation
- 📤 Output: Perfect universal JSON ready for e-commerce checkout

## Onboarding New Carriers

To onboard a new carrier:

1. **Parse Documentation** (if PDF available):
   ```bash
   python -m src.formatter --input carrier_docs.pdf --output schema.json
   ```

2. **Create Mapper** - Transform carrier responses to universal format:
   ```python
   # mappers/new_carrier.py
   from core.schema import UniversalCarrierFormat
   
   class NewCarrierMapper:
       def map(self, carrier_response):
           # Transform messy response to universal format
           return UniversalCarrierFormat(...)
   ```

3. **Create Blueprint** - Define carrier configuration:
   ```yaml
   # blueprints/new_carrier.yaml
   carrier:
     name: "New Carrier"
     base_url: "https://api.newcarrier.com"
   ```

4. **Test & Validate**:
   ```python
   mapper = NewCarrierMapper()
   universal_format = mapper.map(messy_response)
   validator = CarrierValidator()
   validated = validator.validate(universal_format.dict())
   ```

📖 **See [docs/ONBOARDING.md](docs/ONBOARDING.md) for complete onboarding guide.**

## Development Pipeline

See [docs/SYSTEM_OVERVIEW.md](docs/SYSTEM_OVERVIEW.md) for complete system documentation.

See [docs/ONBOARDING.md](docs/ONBOARDING.md) for guide on onboarding new carriers.

See [docs/DEVELOPMENT_PIPELINE.md](docs/DEVELOPMENT_PIPELINE.md) for detailed guide on:
- PHP → Python concepts mapping
- Testing workflow
- Project structure
- Common commands

See [docs/DOCKER.md](docs/DOCKER.md) for Docker development guide.

See [docs/LARAVEL_COMPARISON.md](docs/LARAVEL_COMPARISON.md) for Laravel → Python comparisons.

## Pre-commit Checks

A pre-commit Git hook automatically formats and checks your code before committing:

**Automatic (recommended):**
```bash
git commit -m "Your message"
# Files are auto-formatted and auto-staged
```

**Manual check:**
```bash
make docker-pre-commit
```

**Important Notes:**
- Formatting checks are non-blocking (warnings only) - CI will catch any issues
- Flake8 linting is blocking - real code issues will prevent commits
- Each developer needs to ensure the hook is executable: `chmod +x .git/hooks/pre-commit`

## Next Steps

1. ✅ **PDF Parser** - Complete (extracts text from PDFs)
2. ✅ **Mapper Demo** - Complete (DPD mapper with working transformation)
3. ⏳ **LLM Integration** - Next: Set up LangChain and design prompts
4. ⏳ **CLI Interface** - Next: Create `src/formatter.py` entry point
5. ⏳ **Extraction Pipeline** - Next: Combine PDF parser + LLM + validation
6. ⏳ **More Mappers** - Next: Implement additional carrier mappers
7. ⏳ **Blueprint System** - Next: Build blueprint loader and processor
