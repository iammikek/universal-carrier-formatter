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
python -m src.formatter --input carrier_docs.pdf --output formatted.json
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

## Proof of Concept Use Cases

### Primary Use Case: E-Commerce Checkout Integration

**The Problem:** Every carrier returns data in different formats. An e-commerce checkout needs consistent data.

**The Solution:** Our PoC demonstrates how to transform any carrier response into universal JSON.

### Example Workflow

```
1. Receive messy DHL API response:
   {
     "trk_num": "1234567890",
     "stat": "IN_TRANSIT",
     "loc": {"city": "London", "postcode": "SW1A 1AA"}
   }
   ↓
2. Mapper transforms field names and structure
   ↓
3. Validation engine cleans and validates
   ↓
4. Output perfect universal JSON:
   {
     "tracking_number": "1234567890",
     "status": "in_transit",
     "current_location": {
       "city": "London",
       "postal_code": "SW1A 1AA",
       "country": "GB"
     }
   }
   ↓
5. E-commerce checkout can use this JSON directly
```

### What This PoC Demonstrates

✅ **Input Handling** - Accepts messy, non-standard carrier responses  
✅ **Validation Logic** - Python/Pydantic engine validates and cleans data  
✅ **Universal Output** - Produces perfect JSON for any e-commerce checkout  
✅ **Extensibility** - Easy to add new carriers via mappers and blueprints

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

## Development Pipeline

See [docs/SYSTEM_OVERVIEW.md](docs/SYSTEM_OVERVIEW.md) for complete system documentation.

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
2. ⏳ **LLM Integration** - Next: Set up LangChain and design prompts
3. ⏳ **CLI Interface** - Next: Create `src/formatter.py` entry point
4. ⏳ **Extraction Pipeline** - Next: Combine PDF parser + LLM + validation
5. ⏳ **Mapper Implementation** - Next: Implement carrier-specific mappers
6. ⏳ **Blueprint System** - Next: Build blueprint loader and processor
