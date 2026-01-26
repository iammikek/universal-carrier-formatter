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

---

## [2026-01-26] - Build working mapper demo (PoC)

### Added
- Complete DPD mapper implementation with real transformation logic
  - Field name mapping (trk_num → tracking_number, stat → status, etc.)
  - Status value normalization (IN_TRANSIT → in_transit)
  - Location structure transformation with country derivation
  - Date format normalization (YYYY-MM-DD → ISO 8601)
- Demo script (`scripts/demo_mapper.py`) showing complete transformation flow
- Example messy DPD response (`examples/messy_dpd_response.json`)
- Comprehensive tests for DPD mapper (`tests/unit/test_dpd_mapper.py`)
- Updated README with demo usage instructions

### Changed
- DPD mapper now fully functional with complete transformation logic
- Updated Next Steps in README to reflect mapper completion

### PoC Demonstration
The mapper demo shows the three-part transformation:
1. Input: Messy DPD response (trk_num, stat, loc, est_del)
2. Logic: Mapper transforms + Validator cleans
3. Output: Perfect Universal JSON ready for e-commerce checkout

---

## [2026-01-26] - Improve PoC scenarios with concrete examples

### Changed
- Redefined PoC scenarios to be more concrete and actionable
- Added four clear scenarios demonstrating core capabilities:
  - Scenario 1: Automated Schema Mapping (with concrete input/output examples)
  - Scenario 2: Constraint Extraction (with Pydantic validation code examples)
  - Scenario 3: Edge Case Discovery (with comprehensive scanning examples)
  - Scenario 4: Complete Transformation Flow (e-commerce integration)
- Added detailed before/after examples showing transformations
- Made scenarios more practical and demonstration-focused

---

## [2026-01-26] - Add onboarding guide for new carriers

### Added
- Created comprehensive ONBOARDING.md guide with step-by-step process
- Added onboarding section to README with quick start examples
- Included code examples for creating mappers and blueprints
- Documented common mapping challenges and solutions
- Added best practices for onboarding new carriers

---

## [2026-01-26] - Refocus on Proof of Concept: Three-Part Transformation

### Changed
- Refocused documentation on PoC demonstrating: Input (messy carrier response) → Logic (validation/cleaning) → Output (universal JSON)
- Updated README with concrete example: old DHL API response → universal format
- Emphasized e-commerce checkout use case
- Added complete transformation flow examples in SYSTEM_OVERVIEW.md
- Highlighted practical demonstration of mapper + validator pipeline

### PoC Focus
- **Input**: Messy, non-standard carrier responses (e.g., old DHL API)
- **Logic**: Python/Pydantic validation and cleaning engine
- **Output**: Perfect Universal JSON that any e-commerce checkout can use

---

## [2026-01-26] - Restructure project for autonomous onboarding system

### Added
- Created new directory structure: `core/`, `mappers/`, `blueprints/`
- Added `core/schema.py` - Universal Carrier Format schema (moved from `src/models/`)
- Added `core/validator.py` - Validation logic for carrier responses
- Added `mappers/dpd_mapper.py` - Example DPD carrier mapper
- Added `mappers/royal_mail.py` - Example Royal Mail carrier mapper
- Added `blueprints/dhl_express.yaml` - Example carrier blueprint configuration
- Updated documentation with "Autonomous Onboarding" use case and ROI details

### Changed
- Moved schema models from `src/models/` to `core/` directory
- Updated all imports across codebase to use `core` instead of `src.models`
- Updated README.md with new project structure and autonomous onboarding context
- Updated SYSTEM_OVERVIEW.md with detailed use cases (Schema Mapping, Constraint Extraction, Edge Case Discovery)
- Updated agents.md with new project structure
- Removed all references to specific company names, replaced with generic "autonomous logistics systems"
- Updated docker-compose.yml to mount new directories (core/, mappers/, blueprints/)

### Architecture
- Document Parser (PDF → JSON) - First part of the system
- Core Schema - Universal format all carriers map to
- Mappers - Transform carrier-specific responses to universal format
- Blueprints - Carrier configuration and integration logic

---

## [2026-01-25] - Loosen pre-commit hook checks

### Changed
- Made formatting checks (black/isort) non-blocking in pre-commit hook - warnings only
- Pre-commit hook now auto-stages formatted files after formatting
- Flake8 linting remains blocking to catch real code issues
- Updated README to reflect that formatting checks are non-blocking (CI will enforce)

---

## [2026-01-25] - Add system overview documentation

### Added
- Created comprehensive system overview documentation (`docs/SYSTEM_OVERVIEW.md`)
- Added short overview section to README.md with link to full documentation
- Documented user interaction patterns, workflow, use cases, and technical architecture

---

## [2026-01-25] - Fix black formatting after isort

### Changed
- Fixed black formatting conflicts after isort import sorting
- Reformatted 4 files to match black's style requirements

---

## [2026-01-25] - Fix import sorting with isort

### Changed
- Fixed import sorting in all Python files using isort
- Applied isort formatting to src/, tests/, and scripts/ directories
- Fixes linting workflow failures

---

## [2026-01-25] - Fix validate_schema.py formatting for GitHub Actions

### Changed
- Format Endpoint call with proper line breaks
- Ensure trailing comma consistency

---

## [2026-01-25] - Format code with black

### Changed
- Formatted all Python files with black to fix linting workflow failures
- Applied black formatting to src/, tests/, and scripts/ directories

---

## [2026-01-25] - Fix test failure and improve coverage

### Fixed
- Fixed `test_validate_pdf_path_raises_error_for_permission_denied` test failure
  - Updated mocking approach to properly simulate file without read permission
  - Test now correctly covers PermissionError raise on line 201

### Added
- Added test for successful `_get_page_count` path (line 305)
- Added test for empty/None table handling in `_table_to_text` (line 277)

### Changed
- Coverage improved from 88% to 89%
- Remaining uncovered lines are validator ValueError raises (192, 423) which are executed but wrapped by Pydantic

---

## [2026-01-25] - Add linting and formatting workflow

### Added
- GitHub Actions workflow (`.github/workflows/lint.yml`) for code quality checks
- Automated checks for:
  - Code formatting (black --check)
  - Import sorting (isort --check-only)
  - Linting (flake8)
  - Type checking (mypy) - non-blocking
- Workflow runs on push to `main`/`develop` branches and all pull requests

---

## [2026-01-25] - Add GitHub Actions workflow for CI/CD

### Added
- GitHub Actions workflow (`.github/workflows/tests.yml`) to run tests on push and pull requests
- Automated test execution on Python 3.11
- Coverage reporting with XML output for potential Codecov integration
- Workflow runs on push to `main`/`develop` branches and all pull requests

### Changed
- Updated `.gitignore` to exclude `coverage.xml` (generated by CI)

---

## [2026-01-25] - Add tests to improve code coverage

### Added
- Additional test cases to cover missing lines:
  - Parameter name whitespace-only validation test (line 118)
  - ResponseSchema status code boundary tests (line 192)
  - Carrier name whitespace-only validation test (line 411)
  - PDF parser metadata error handling test (lines 160-162)
  - PDF parser permission error test (line 201)
  - PDF parser _get_page_count error handling test (lines 303-307)

### Changed
- Improved test coverage from 85% to target higher coverage
- Added boundary value tests for status codes (99, 100, 599, 600)

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
