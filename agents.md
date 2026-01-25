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
src/models/          # Pydantic models (like Laravel Models)
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

- `docs/LARAVEL_COMPARISON.md` - Laravel → Python guide
- `docs/TEST_ORGANIZATION.md` - Test structure
- `CHANGELOG.md` - Project status and changes
- `src/models/carrier_schema.py` - Example code with Laravel comparisons

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
| `app/Services/` | `src/` |
| `app/Models/` | `src/models/` |

**See `docs/LARAVEL_COMPARISON.md` for detailed patterns and examples.**
