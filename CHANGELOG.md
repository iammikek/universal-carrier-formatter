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
