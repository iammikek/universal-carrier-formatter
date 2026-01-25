# PDF Parser Implementation Plan

## Overview
Implement a PDF parser service that extracts text content from carrier API documentation PDFs. This is the first step in the extraction pipeline.

## Steps

### Step 1: Create PDF Parser Service Class
- Create `src/pdf_parser.py`
- Define `PdfParserService` class (like Laravel service class)
- Include Laravel comparison comments
- Add type hints throughout
- Structure similar to `src/_example_service_template.py`

**Laravel Equivalent**: `app/Services/PdfParserService.php`

### Step 2: Implement Basic Text Extraction
- Choose PDF library: `pdfplumber` (better for tables) or `pymupdf` (faster)
- Implement `extract_text()` method
- Handle basic text extraction from PDF pages
- Return extracted text as string

**Key Method**: `extract_text(pdf_path: str) -> str`

### Step 3: Add Error Handling
- Handle `FileNotFoundError` for missing files
- Handle `PDFException` for corrupted/invalid PDFs
- Handle `PermissionError` for locked files
- Provide clear error messages
- Use logging for errors

**Error Types**:
- File not found
- Invalid/corrupted PDF
- Permission denied
- Empty PDF

### Step 4: Handle Different PDF Types
- **Text-based PDFs**: Direct text extraction (primary method)
- **Scanned PDFs**: Detect and warn (would need OCR - future enhancement)
- **Tables**: Extract table data if possible
- **Multi-page**: Handle all pages, combine text
- Add fallback strategies

**Features**:
- Page-by-page extraction
- Table detection and extraction
- Metadata extraction (page count, title, etc.)

### Step 5: Add Logging
- Log PDF processing start/end
- Log page count, text length
- Log errors and warnings
- Use Python's `logging` module (like Laravel's Log facade)

**Log Levels**:
- INFO: Processing started, pages extracted
- WARNING: Empty pages, potential issues
- ERROR: File errors, extraction failures

### Step 6: Write Unit Tests
- Create `tests/unit/test_pdf_parser.py`
- Mock PDF files using fixtures
- Test successful extraction
- Test error handling (missing file, corrupted PDF)
- Test different PDF types
- Use `@pytest.mark.unit` marker

**Test Cases**:
- Extract text from valid PDF
- Handle missing file
- Handle corrupted PDF
- Handle empty PDF
- Extract from multi-page PDF

### Step 7: Write Integration Tests
- Create `tests/integration/test_pdf_parser.py`
- Use real PDF files from `examples/` directory
- Test with actual carrier documentation PDFs
- Verify text extraction quality
- Use `@pytest.mark.integration` marker

**Test Cases**:
- Extract from real carrier PDF
- Verify text contains API-related keywords
- Test with different PDF formats

### Step 8: Add Example PDF
- Add sample carrier PDF to `examples/` directory
- Can be a simple mock PDF or real documentation
- Use for integration testing
- Document in README

**File**: `examples/sample_carrier.pdf` (or similar)

### Step 9: Update Documentation
- Update `CHANGELOG.md` with PDF parser implementation
- Add usage examples to README if needed
- Document PDF library choice and rationale

## Technical Decisions

### PDF Library Choice
**Recommendation**: Start with `pdfplumber`
- Better table extraction (important for API docs)
- Good text extraction
- Active maintenance
- Already in requirements.txt

**Alternative**: `pymupdf` (fitz)
- Faster performance
- Good for simple text extraction
- Can switch later if needed

### Service Structure
```python
class PdfParserService:
    def __init__(self, config: Optional[dict] = None)
    def extract_text(self, pdf_path: str) -> str
    def extract_metadata(self, pdf_path: str) -> dict
    def _validate_pdf(self, pdf_path: str) -> None
    def _extract_page(self, page) -> str
```

### Error Handling Strategy
- Raise custom exceptions (like Laravel exceptions)
- Log errors before raising
- Provide helpful error messages
- Return None vs raise exception? → Raise (fail fast)

## Success Criteria

✅ Can extract text from text-based PDFs  
✅ Handles multi-page PDFs  
✅ Provides clear error messages  
✅ Has comprehensive unit tests  
✅ Has integration tests with real PDFs  
✅ Includes Laravel comparison comments  
✅ Follows project code style  

## Estimated Time
- Service implementation: ~1-2 hours
- Tests: ~1 hour
- Documentation: ~30 minutes
- **Total**: ~2-3 hours

## Next Steps After PDF Parser
1. LLM Integration (LangChain setup)
2. Prompt Engineering (design extraction prompts)
3. Extraction Pipeline (combine PDF + LLM)
4. CLI Interface (user-facing command)
