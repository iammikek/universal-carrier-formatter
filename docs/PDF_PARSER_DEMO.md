# PDF Parser Demo - What Gets Extracted

## What the PDF Parser Does

The PDF parser extracts three types of information from carrier API documentation PDFs:

### 1. Metadata
**What it extracts:**
- Page count
- File size
- Title, author, creation date (if available in PDF)
- PDF version

**Example output:**
```python
{
  "page_count": 234,
  "file_size": 5925000,
  "title": "DHL Express - MyDHL API - SOAP Developer Guide",
  "author": "DHL",
  "created": "2025-04-01"
}
```

### 2. Text Content
**What it extracts:**
- All text from PDF pages
- Can extract from all pages or specific page range
- Handles multi-page documents
- Preserves basic formatting (newlines, spacing)

**Example output:**
```
DHL Express API Developer Guide
Version 2.33

Table of Contents
1. Introduction
2. Authentication
   API Key Authentication
   Include your API key in the X-API-Key header
   
3. Endpoints
   GET /api/v1/track
   Track a shipment by tracking number
   Parameters:
   - tracking_number (required, string)
   - format (optional, json/xml)
   
   POST /api/v1/shipments
   Create a new shipment
   ...
```

### 3. Tables
**What it extracts:**
- Tabular data from PDF pages
- API parameter tables
- Response schema tables
- Rate limit tables

**Example output:**
```
Parameter Name    | Type    | Required | Description
------------------|---------|----------|------------
tracking_number   | string  | Yes      | DHL tracking number
format            | string  | No       | Response format (json/xml)
```

## How to Test It

Run the test script:
```bash
python scripts/test_pdf_parser.py
```

Or use the parser directly:
```python
from src.pdf_parser import PdfParserService

parser = PdfParserService()

# Extract metadata
metadata = parser.extract_metadata('examples/dhl_express_api_docs.pdf')
print(f"Pages: {metadata['page_count']}")

# Extract text (first 10 pages)
text = parser.extract_text('examples/dhl_express_api_docs.pdf', max_pages=10)
print(f"Extracted {len(text)} characters")

# Extract text with tables
text_with_tables = parser.extract_text(
    'examples/dhl_express_api_docs.pdf',
    max_pages=5,
    extract_tables=True
)
```

## What Happens Next

After extraction, the text is sent to the LLM which:
1. **Identifies API endpoints** from the text
2. **Extracts parameters** from tables and descriptions
3. **Finds authentication methods** mentioned in docs
4. **Discovers business rules** ("weight must be in grams for Germany")
5. **Generates mapper code** based on response examples
