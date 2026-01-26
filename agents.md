# AI Agents Guide

Quick reference for AI agents working on this project. See `docs/` for detailed guides.

## Project Context

**Universal Carrier Formatter** - Python tool that extracts structured API documentation from messy carrier PDFs using LLMs (LangChain).

**Tech Stack**: Python 3.11+, Pydantic, LangChain, pytest, Docker

## Key Patterns

1. **Laravel Comparisons**: Always include Laravel → Python comparisons in code comments
2. **One Class Per File**: Tests follow Laravel convention (one test class per file)
3. **Docker-First**: Primary dev environment uses Docker
4. **Type Hints**: Always use Python type hints

## Project Structure

```
core/                # Universal schema and validation (the "Universal" part)
│   ├── schema.py    # Pydantic models defining Universal Carrier Format
│   └── validator.py # Validation logic for carrier responses
mappers/             # Carrier-specific response mappers
│   ├── dpd_mapper.py
│   └── royal_mail.py
blueprints/          # Carrier configuration/logic (YAML)
│   └── dhl_express.yaml
src/                 # Document parser (PDF → JSON)
│   └── pdf_parser.py
tests/unit/          # Unit tests (like tests/Unit/)
tests/integration/   # Integration tests (like tests/Feature/)
docs/                # Detailed documentation
```

## Quick Commands

```bash
make docker-test-tests    # Run tests
make docker-format        # Format code
pytest -m unit           # Run unit tests only
```

## Key Files

- `core/schema.py` - Universal Carrier Format schema (Pydantic models)
- `core/validator.py` - Validation logic for carrier responses
- `mappers/dpd_mapper.py` - Example mapper (DPD → Universal Format)
- `blueprints/dhl_express.yaml` - Example blueprint configuration
- `src/pdf_parser.py` - PDF parsing service (document parser)
- `docs/SYSTEM_OVERVIEW.md` - Complete system documentation
- `docs/LARAVEL_COMPARISON.md` - Laravel → Python guide
- `CHANGELOG.md` - Project status and changes

## Code Style

- **Services**: Include Laravel equivalent in docstring
- **Tests**: Use `@pytest.mark.unit` or `@pytest.mark.integration`
- **Type Hints**: Always include (e.g., `def method(self, param: str) -> dict:`)

## When Adding Code

1. Include Laravel comparisons in comments
2. Add type hints
3. Write tests in `tests/unit/` or `tests/integration/`
4. Update `CHANGELOG.md` with changes

## Quick Reference

| Laravel | This Project |
|---------|--------------|
| `tests/Unit/` | `tests/unit/` |
| `@group unit` | `@pytest.mark.unit` |
| `setUp()` | `conftest.py` fixtures |
| `app/Services/` | `src/` (parsers), `mappers/` |
| `app/Models/` | `core/` (schema) |
| `config/` | `blueprints/` (YAML configs) |

**See `docs/LARAVEL_COMPARISON.md` for detailed patterns and examples.**
