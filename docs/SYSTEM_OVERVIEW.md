# System Overview

## What This System Does

**Universal Carrier Formatter** is a Python tool that automatically extracts structured API documentation from messy, unstructured PDF files provided by shipping carriers (like regional couriers, logistics companies, etc.).

### The Problem

Carrier API documentation often comes as:
- Messy PDF files with inconsistent formatting
- Scattered information across multiple pages
- No standardized structure
- Hard to parse programmatically

### The Solution

This tool uses **LLMs (via LangChain)** to intelligently parse these PDFs and extract structured information into a standardized **Universal Carrier Format** JSON schema.

---

## User Interaction

### Command-Line Interface (CLI)

Users interact with the system through a simple command-line tool:

```bash
# Basic usage
python -m src.formatter --input carrier_docs.pdf --output formatted.json

# With Docker (recommended)
docker-compose exec app python -m src.formatter \
    --input examples/sample.pdf \
    --output output.json

# Using Makefile shortcut
make run
```

### Command Options

```bash
python -m src.formatter \
    --input <pdf_file>          # Required: Path to carrier PDF documentation
    --output <json_file>        # Optional: Output file path (default: output.json)
    --llm-model <model>         # Optional: LLM model to use (default: gpt-4)
    --verbose                   # Optional: Show detailed processing logs
```

**Laravel Equivalent**: Like `php artisan carrier:format input.pdf --output=output.json`

---

## System Workflow

### Step-by-Step Process

```
1. User provides PDF file
   ↓
2. PDF Parser extracts raw text/content
   ↓
3. LLM analyzes text and extracts structured data
   ↓
4. Data is validated against Universal Carrier Format schema
   ↓
5. Structured JSON is written to output file
```

### Detailed Pipeline

1. **Input Validation**
   - Check PDF file exists and is readable
   - Validate file format
   - Extract basic metadata (page count, file size)

2. **PDF Text Extraction**
   - Extract text from all pages
   - Extract tables (important for API docs)
   - Extract metadata (title, author, etc.)
   - Handle multi-page documents

3. **LLM Processing**
   - Send extracted text to LLM (via LangChain)
   - Use structured prompts to identify:
     - API endpoints (paths, methods)
     - Authentication methods
     - Request/response schemas
     - Parameters (query, path, headers, body)
     - Rate limits
     - Base URLs and versions

4. **Schema Validation**
   - Validate extracted data against Pydantic models
   - Ensure all required fields are present
   - Type-check all values
   - Provide clear error messages if validation fails

5. **Output Generation**
   - Format as JSON matching Universal Carrier Format
   - Write to specified output file
   - Provide success/error feedback to user

---

## Input Format

### What Users Provide

- **Input**: A PDF file containing carrier API documentation
  - Can be text-based or scanned (scanned PDFs may need OCR - future enhancement)
  - Typically contains endpoint descriptions, authentication info, examples
  - May have inconsistent formatting, tables, diagrams

**Example Input**: `examples/sample_carrier.pdf`

---

## Output Format

### Universal Carrier Format JSON

The system outputs a standardized JSON schema that includes:

- **Metadata**: Carrier name, base URL, API version, description
- **Endpoints**: All API endpoints with:
  - Path and HTTP method
  - Request parameters (query, path, headers, body)
  - Response schemas (status codes, content types, body structure)
  - Authentication requirements
  - Tags/categories
- **Authentication**: Supported auth methods (API keys, OAuth, Bearer tokens)
- **Rate Limits**: Request limits and time periods
- **Documentation Links**: References to original docs

**Example Output**: See `examples/expected_output.json`

### Output Structure

```json
{
  "name": "Carrier Name",
  "base_url": "https://api.carrier.com",
  "version": "v1",
  "description": "...",
  "endpoints": [
    {
      "path": "/api/v1/track/{id}",
      "method": "GET",
      "summary": "...",
      "request": { ... },
      "responses": [ ... ]
    }
  ],
  "authentication": [ ... ],
  "rate_limits": [ ... ]
}
```

---

## Use Cases

### Primary Use Case

**Integration Developers** who need to:
- Quickly understand a carrier's API structure
- Generate API clients automatically
- Compare APIs across multiple carriers
- Build unified shipping/logistics platforms

### Example Scenarios

1. **Onboarding New Carrier**
   ```
   Developer receives PDF docs → Runs formatter → Gets structured JSON → 
   Generates API client automatically
   ```

2. **API Comparison**
   ```
   Format multiple carrier PDFs → Compare endpoints/schemas → 
   Build unified abstraction layer
   ```

3. **Documentation Standardization**
   ```
   Convert messy PDFs → Standardized JSON → Generate consistent docs → 
   Share with team
   ```

---

## Technical Architecture

### Components

1. **PDF Parser Service** (`src/pdf_parser.py`)
   - Extracts text and tables from PDFs
   - Handles errors and edge cases
   - Provides metadata extraction

2. **LLM Integration** (to be implemented)
   - LangChain setup for LLM calls
   - Structured prompt templates
   - Response parsing and validation

3. **Schema Models** (`src/models/carrier_schema.py`)
   - Pydantic models defining Universal Carrier Format
   - Validation and type checking
   - JSON serialization

4. **CLI Interface** (to be implemented)
   - Command-line entry point
   - Argument parsing
   - User feedback and error handling

5. **Extraction Pipeline** (to be implemented)
   - Orchestrates PDF → LLM → Validation → Output
   - Error handling and logging
   - Progress reporting

---

## Configuration

### Environment Variables

Users need to configure LLM API keys:

```bash
# .env file
OPENAI_API_KEY=sk-...
# Or for other providers:
ANTHROPIC_API_KEY=...
```

**Laravel Equivalent**: Like `config/services.php` for API keys

---

## Error Handling

### Common Errors Users May Encounter

1. **File Not Found**
   ```
   Error: PDF file not found: carrier_docs.pdf
   ```

2. **Invalid PDF Format**
   ```
   Error: Unable to parse PDF. File may be corrupted or encrypted.
   ```

3. **LLM API Error**
   ```
   Error: Failed to connect to LLM API. Check your API key.
   ```

4. **Validation Error**
   ```
   Error: Extracted data doesn't match schema. Missing required field: 'base_url'
   ```

5. **Permission Error**
   ```
   Error: Cannot write to output file. Check file permissions.
   ```

---

## Success Criteria

A successful run should:
- ✅ Process PDF without errors
- ✅ Extract all major API endpoints
- ✅ Identify authentication methods
- ✅ Capture request/response schemas
- ✅ Output valid Universal Carrier Format JSON
- ✅ Provide clear feedback to user

---

## Future Enhancements

- **Batch Processing**: Process multiple PDFs at once
- **OCR Support**: Handle scanned PDFs
- **Interactive Mode**: Ask user for clarification when extraction is ambiguous
- **Web Interface**: GUI for non-technical users
- **API Mode**: REST API endpoint for programmatic access
- **Validation Reports**: Detailed reports on extraction quality
- **Incremental Updates**: Update existing JSON when carrier docs change

---

## Comparison to Laravel Patterns

| Laravel Concept | This Project |
|----------------|--------------|
| `php artisan` command | `python -m src.formatter` |
| `Command::class` | Click CLI decorators |
| `Service::class` | Service classes (`PdfParserService`) |
| `Model::class` | Pydantic models |
| `Validator::make()` | Pydantic validation |
| `Log::info()` | Python `logging` module |
| `config('services.openai')` | `.env` file + `os.getenv()` |

---

## Next Steps for Implementation

1. ✅ **PDF Parser** - Complete (extracts text from PDFs)
2. ⏳ **LLM Integration** - Next: Set up LangChain and design prompts
3. ⏳ **CLI Interface** - Next: Create `src/formatter.py` entry point
4. ⏳ **Extraction Pipeline** - Next: Combine PDF parser + LLM + validation
5. ⏳ **Error Handling** - Next: Comprehensive error messages and recovery
