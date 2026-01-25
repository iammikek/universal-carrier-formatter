# Changelog

All notable changes to this project will be documented in this file.

**⚠️ Important**: This file should be updated with every commit. Add entries in reverse chronological order (newest first).

A git pre-commit hook will remind you to update this file if it's not included in your commit.

## Format

Each entry should follow this format:
```
## [Date] - Brief Description
- Added/Fixed/Changed: Description
- Added/Fixed/Changed: Description
```

---

## [2026-01-25] - Fix PDF parser test failures

### Fixed
- Fixed test failures in PDF parser unit tests
  - Mock `_get_page_count` to prevent double PDF opening in tests
  - Fix empty PDF test by ensuring proper mock setup
  - Replace non-existent PDFSyntaxError with generic Exception handling
  - Update source code to handle PDF errors more generically

### Changed
- Updated exception handling in `_extract_text_from_pdf` to check error message instead of specific exception type
- Improved test mocks to include `extract_tables` return value

---

## [2026-01-25] - Improve PDF parser tests with comprehensive coverage

### Added
- Test fixtures for common PDF mocks (reusable across tests)
- Table extraction tests (extract_tables=True)
- Page separator tests (combine_pages=False)
- Logging verification tests using caplog
- Edge case tests (empty pages, None values in tables)
- Performance test in integration tests
- Test review documentation (docs/TEST_REVIEW_PDF_PARSER.md)

### Changed
- Refactored unit tests to use pytest fixtures (reduced duplication)
- Replaced manual tempfile handling with pytest tmp_path fixture
- Improved test organization and maintainability
- Enhanced integration tests with additional scenarios

### Fixed
- Test cleanup issues (now handled automatically by tmp_path)
- Missing test coverage for table extraction feature
- Missing test coverage for page separator feature

---

## [2026-01-25] - Implement PDF Parser Service

### Added
- PDF parser service (`src/pdf_parser.py`)
  - Text extraction from PDF files using pdfplumber
  - Multi-page PDF support
  - Table extraction (optional)
  - Metadata extraction (page count, title, author)
  - Comprehensive error handling
  - Logging for debugging and monitoring
- Unit tests for PDF parser (`tests/unit/test_pdf_parser.py`)
  - Tests for text extraction
  - Tests for error handling (missing files, corrupted PDFs)
  - Tests for multi-page PDFs
  - Tests for metadata extraction
- Integration tests for PDF parser (`tests/integration/test_pdf_parser.py`)
  - Tests with real PDF files
  - Validation of extracted text quality

### Changed
- Updated `src/__init__.py` to export PdfParserService

---

## [2026-01-25] - Streamline agents.md to reduce token usage

### Changed
- Reduced agents.md from ~250 lines to ~60 lines
- Removed detailed examples and patterns (reference docs/ instead)
- Kept only essential quick reference information
- Fixed pre-commit hook typo

---

## [2026-01-25] - Add CHANGELOG.md and pre-commit hook reminder

### Added
- CHANGELOG.md for tracking all project changes
- Git pre-commit hook to remind about updating changelog
- Project status tracking in changelog

### Changed
- Moved project status section from agents.md to CHANGELOG.md
- Updated agents.md to reference CHANGELOG.md

---

## [2026-01-25] - Add Universal Carrier Format schema and reorganize tests

### Added
- Universal Carrier Format schema with Pydantic models
  - UniversalCarrierFormat, Endpoint, Parameter models
  - RequestSchema, ResponseSchema, AuthenticationMethod, RateLimit
  - Full validation and JSON serialization support
  - Example output JSON file
- Docker Compose scripts for common development tasks
- Test reorganization (PHPUnit-style structure)
  - `tests/unit/` directory (like `tests/Unit/` in Laravel)
  - `tests/integration/` directory (like `tests/Feature/`)
  - One test class per file (Laravel convention)
- Shared test fixtures in `conftest.py`
- Comprehensive documentation
  - Test organization guide
  - Docker scripts guide
  - Laravel comparison guide
  - AI agents guide

### Changed
- Reorganized test structure to match PHPUnit conventions
- Updated test files to use `@pytest.mark.unit` markers

### Fixed
- Pydantic alias handling for `default_value` field
- URL normalization in tests (HttpUrl adds trailing slash)

---

## [2026-01-25] - Initial project setup

### Added
- Python project structure with `src/`, `tests/`, `examples/` directories
- Docker development environment with docker-compose.yml
- Development dependencies (pytest, black, flake8, etc.)
- Makefile for common development tasks
- pytest configuration
- .gitignore and .dockerignore files
- Setup script for initial project configuration
- Basic test structure

---

## Project Status

### ✅ Completed
- Project structure and Docker setup
- Universal Carrier Format schema (Pydantic models)
- Test organization (unit/integration split)
- Documentation and Laravel comparison guides
- Docker Compose scripts and development workflow

### 🚧 In Progress / Next Steps
- PDF parser implementation
- LLM integration (LangChain)
- Prompt engineering module
- Extraction pipeline
- CLI interface

---

**Note**: Remember to update this file with each commit!
