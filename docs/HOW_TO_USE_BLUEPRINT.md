# How to Use Blueprints

## Current Status: Blueprint Loader Not Built Yet ⚠️

**Important:** The blueprint loader/processor is **not yet implemented**. This document shows:
1. How it **will** work once built
2. What you can do **right now** with blueprints
3. What needs to be built

## What We Have Now

✅ **Blueprint files** - YAML files like `blueprints/dhl_express.yaml`  
✅ **Blueprint structure** - Documented in `docs/BLUEPRINT_STRUCTURE.md`  
❌ **Blueprint loader** - Code to read and process blueprints  
❌ **Blueprint converter** - Code to convert YAML → Universal Carrier Format  

## How It Will Work (Once Built)

### Step 1: Load Blueprint

```python
from src.blueprints.loader import BlueprintLoader

# Load a blueprint file
loader = BlueprintLoader()
blueprint = loader.load("blueprints/dhl_express.yaml")
```

### Step 2: Convert to Universal Carrier Format

```python
from src.blueprints.processor import BlueprintProcessor

# Convert blueprint to Universal Carrier Format
processor = BlueprintProcessor()
universal_format = processor.convert(blueprint)

# Now you have a UniversalCarrierFormat object
print(universal_format.name)  # "DHL Express"
print(universal_format.base_url)  # "https://api.dhl.com"
print(len(universal_format.endpoints))  # Number of endpoints
```

### Step 3: Use the Universal Format

```python
# Validate it
from src.core.validator import CarrierValidator

validator = CarrierValidator()
validated = validator.validate(universal_format.dict())

# Save to JSON
universal_format.to_json_file("output/dhl_from_blueprint.json")

# Use for mapper generation (future)
# Use for integration initialization
```

## Complete Example (Future)

```python
from src.blueprints.loader import BlueprintLoader
from src.blueprints.processor import BlueprintProcessor
from src.core.validator import CarrierValidator

# 1. Load blueprint
loader = BlueprintLoader()
blueprint = loader.load("blueprints/dhl_express.yaml")

# 2. Convert to Universal Carrier Format
processor = BlueprintProcessor()
universal_format = processor.convert(blueprint)

# 3. Validate
validator = CarrierValidator()
validated = validator.validate(universal_format.dict())

# 4. Save
universal_format.to_json_file("output/dhl_schema.json")

print("✅ Blueprint converted and validated!")
```

## CLI Usage (Future)

```bash
# Convert blueprint to Universal Carrier Format JSON
python -m src.blueprints.cli blueprints/dhl_express.yaml --output output/dhl_schema.json

# Or with validation
python -m src.blueprints.cli blueprints/dhl_express.yaml --output output/dhl_schema.json --validate
```

## What You Can Do Right Now

### 1. Create Blueprint Files

You can manually create blueprint YAML files:

```bash
# Create a new blueprint
vim blueprints/fedex.yaml
# ... fill in the structure
```

### 2. Use as Reference Documentation

Blueprints serve as human-readable documentation of carrier APIs:

```bash
# Read a blueprint
cat blueprints/dhl_express.yaml
```

### 3. Compare with Extracted Schemas

If you extract from PDF, you can manually compare:

```bash
# Extract from PDF
python -m src.formatter examples/dhl_express_api_docs.pdf --output output/dhl_extracted.json

# Manually compare with blueprint
cat blueprints/dhl_express.yaml
cat output/dhl_extracted.json
```

### 4. Use as Template

Copy an existing blueprint as a template for new carriers:

```bash
cp blueprints/dhl_express.yaml blueprints/new_carrier.yaml
# Edit new_carrier.yaml with new carrier's info
```

## What Needs to Be Built

To make blueprints usable, we need:

### 1. `src/blueprints/loader.py`
- Read YAML files
- Parse YAML structure
- Handle errors (file not found, invalid YAML)

### 2. `src/blueprints/validator.py`
- Validate blueprint structure
- Check required fields
- Validate URLs, paths, etc.

### 3. `src/blueprints/converter.py`
- Convert blueprint YAML → UniversalCarrierFormat
- Handle differences (carrier.code, nested structure, auth format)
- Map all fields correctly

### 4. `src/blueprints/processor.py`
- Orchestrate: load → validate → convert
- Main entry point for blueprint processing

### 5. `src/blueprints/cli.py` (Optional)
- CLI command to process blueprints
- `python -m src.blueprints.cli blueprint.yaml --output schema.json`

### 6. Tests
- Unit tests for loader, validator, converter
- Integration tests for full pipeline

## Blueprint Workflow (Once Built)

```
Blueprint YAML File
    ↓
BlueprintLoader.load()
    ↓
Blueprint Object (validated structure)
    ↓
BlueprintProcessor.convert()
    ↓
UniversalCarrierFormat (Pydantic model)
    ↓
CarrierValidator.validate()
    ↓
Validated Universal Carrier Format JSON
    ↓
Use for:
  - Mapper generation
  - Integration initialization
  - Schema validation
  - Documentation
```

## Comparison: PDF vs Blueprint Usage

| Aspect | PDF Extraction | Blueprint |
|--------|----------------|-----------|
| **Input** | PDF file | YAML file |
| **Command** | `python -m src.formatter pdf --output json` | `python -m src.blueprints.cli yaml --output json` |
| **Status** | ✅ Working | ❌ Not built yet |
| **Output** | Universal Carrier Format JSON | Universal Carrier Format JSON |
| **Same Result?** | Yes - both produce same format | Yes - both produce same format |

## Next Steps

To make blueprints usable:

1. **Build the loader** - Read and parse YAML files
2. **Build the converter** - Convert YAML → UniversalCarrierFormat
3. **Build the processor** - Orchestrate the pipeline
4. **Add tests** - Ensure it works correctly
5. **Add CLI** - Make it easy to use

Once built, blueprints will be a full alternative to PDF extraction for carriers without PDFs.
