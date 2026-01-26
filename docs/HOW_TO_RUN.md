# How to Run the LLM Extraction Pipeline

## Prerequisites

1. **Docker** (recommended) or **Python 3.11+** with virtual environment
2. **OpenAI API Key** in `.env` file
3. **PDF file** with carrier API documentation

## Quick Start (Docker - Recommended)

### 1. Start Docker Container

```bash
# Build and start the container
docker-compose up -d

# Verify it's running
docker-compose ps
```

### 2. Run the Extraction

```bash
# Basic usage (uses default output location)
docker-compose exec app python -m src.formatter examples/dhl_express_api_docs.pdf

# Specify output file
docker-compose exec app python -m src.formatter examples/dhl_express_api_docs.pdf --output output/dhl_schema.json

# Use a different LLM model
docker-compose exec app python -m src.formatter examples/dhl_express_api_docs.pdf --llm-model gpt-4-turbo-preview

# Verbose output (see detailed logs)
docker-compose exec app python -m src.formatter examples/dhl_express_api_docs.pdf --verbose

# Skip table extraction (faster, but may miss important data)
docker-compose exec app python -m src.formatter examples/dhl_express_api_docs.pdf --no-tables
```

### 3. Check the Output

```bash
# View the generated JSON file
cat output/dhl_express_api_docs_schema.json

# Or pretty-print it
docker-compose exec app python -c "import json; print(json.dumps(json.load(open('output/dhl_express_api_docs_schema.json')), indent=2))"
```

## Local Development (Without Docker)

### 1. Setup Virtual Environment

```bash
# Create virtual environment
python3 -m venv .venv

# Activate it
source .venv/bin/activate  # On macOS/Linux
# OR
.venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your OpenAI API key
# OPENAI_API_KEY=sk-proj-...
```

### 3. Run the Extraction

```bash
# Basic usage
python -m src.formatter examples/dhl_express_api_docs.pdf

# With options
python -m src.formatter examples/dhl_express_api_docs.pdf --output output/my_schema.json --verbose
```

## Command Options

```
python -m src.formatter <PDF_FILE> [OPTIONS]

Arguments:
  INPUT                  Path to PDF file (required)

Options:
  --output, -o PATH      Output JSON file path
                         (default: output/{filename}_schema.json)
  
  --llm-model TEXT       LLM model to use
                         (default: gpt-4)
                         Options: gpt-4, gpt-4-turbo-preview, gpt-3.5-turbo
  
  --no-tables            Don't extract tables from PDF
                         (faster but may miss important data)
  
  --verbose, -v          Show detailed processing logs
```

## Example: Complete Workflow

```bash
# 1. Start Docker
docker-compose up -d

# 2. Extract schema from DHL PDF
docker-compose exec app python -m src.formatter \
  examples/dhl_express_api_docs.pdf \
  --output output/dhl_schema.json \
  --verbose

# Output:
# ======================================================================
# Universal Carrier Formatter
# ======================================================================
# 
# 📄 Processing: examples/dhl_express_api_docs.pdf
# 💾 Output: output/dhl_schema.json
# 
# Starting extraction pipeline for: examples/dhl_express_api_docs.pdf
# Step 1: Extracting text from PDF...
# Extracted 125,430 characters from 234 pages
# Step 2: Extracting schema using LLM...
# Sending 125430 characters to LLM
# Received LLM response: 8,234 characters
# Step 3: Extracting field mappings and constraints...
# Step 4: Saving to output/dhl_schema.json...
# 
# ======================================================================
# ✅ Extraction Complete!
# ======================================================================
# Carrier: DHL Express
# Base URL: https://api.dhl.com/
# Endpoints: 12
# Output: output/dhl_schema.json

# 3. View the output
cat output/dhl_schema.json | jq '.schema.name'
# "DHL Express"

cat output/dhl_schema.json | jq '.schema.endpoints | length'
# 12

cat output/dhl_schema.json | jq '.field_mappings[0]'
# {
#   "carrier_field": "ShipmentNumber",
#   "universal_field": "tracking_number",
#   "description": "Tracking number"
# }
```

## Troubleshooting

### Error: "OPENAI_API_KEY environment variable not set"

**Solution:** Make sure `.env` file exists and contains your API key:
```bash
# Check if .env exists
test -f .env && echo "✅ .env exists" || echo "❌ .env missing"

# Verify API key is set
grep OPENAI_API_KEY .env
```

### Error: "PDF file not found"

**Solution:** Check the PDF path:
```bash
# List available PDFs
ls -lh examples/*.pdf

# Use correct path
docker-compose exec app python -m src.formatter examples/dhl_express_api_docs.pdf
```

### Error: "ModuleNotFoundError: No module named 'pydantic'"

**Solution:** Install dependencies:
```bash
# In Docker (should already be installed)
docker-compose exec app pip install -r requirements.txt

# Locally
pip install -r requirements.txt
```

### LLM Response is Invalid JSON

**Solution:** The extraction handles this automatically, but if it fails:
- Check verbose logs: `--verbose`
- The LLM might be returning malformed JSON
- Try a different model: `--llm-model gpt-4-turbo-preview`

## Testing Without Real API Calls

You can test the PDF parser without calling the LLM:

```bash
# Just extract text from PDF
docker-compose exec app python scripts/test_pdf_parser.py examples/dhl_express_api_docs.pdf

# Save extracted text to file
docker-compose exec app python scripts/test_pdf_parser.py \
  examples/dhl_express_api_docs.pdf \
  --output output/dhl_extracted_text.txt
```

## Next Steps

After extraction:
1. **Review the schema** in `output/{carrier}_schema.json`
2. **Check field mappings** - verify carrier fields are correctly mapped
3. **Review constraints** - check business rules are extracted
4. **Generate mapper** - use the schema to create carrier mapper code
5. **Test mapper** - validate with real API responses

See `docs/ONBOARDING.md` for complete onboarding guide.
