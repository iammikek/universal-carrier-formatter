# AI Agents Guide

Quick reference for AI agents working on this project. See `docs/` for detailed guides.

## Project Context

**Universal Carrier Formatter** - Python tool that extracts structured API documentation from messy carrier PDFs using LLMs (LangChain).

**Tech Stack**: Python 3.11+, Pydantic, LangChain, pytest, Docker

## LLM Model Selection

**⚠️ IMPORTANT: Cost Constraint**

When selecting OpenAI models for LLM extraction, **DO NOT use models priced over $2.5 per million input tokens**.

**Allowed models** (as of 2026), sorted by cost:
- `gpt-4.1-nano` - $0.20 / 1M tokens ✅ **CHEAPEST** (~$0.06 per extraction)
- `gpt-5-mini` - $0.250 / 1M tokens ✅ (~$0.09 per extraction)
- `gpt-4.1-mini` - $0.80 / 1M tokens ✅ (~$0.25 per extraction) **DEFAULT**
- `gpt-5.2` - $1.750 / 1M tokens ✅ (~$0.61 per extraction)

**Prohibited models** (too expensive):
- `gpt-4.1` - $3.00 / 1M tokens ❌
- `gpt-5.2-pro` - $21.00 / 1M tokens ❌

**Default model:** `gpt-4.1-mini` (good balance of cost and quality)

**Cheapest option:** `gpt-4.1-nano` - Use for maximum cost savings, but may have lower accuracy for complex schemas.

**Cost comparison** (for 1M character PDF ≈ 268K input tokens):
- `gpt-4.1-nano`: ~$0.06 per extraction (75% cheaper than default)
- `gpt-4.1-mini`: ~$0.25 per extraction (default)

**Why:** PDF extraction can send 1M+ characters per document. Using expensive models would result in very high costs.

**Where this applies:**
- `src/llm_extractor.py` - Default model selection
- `src/extraction_pipeline.py` - Model parameter
- `src/formatter.py` - CLI model option

## Key Patterns

1. **One Class Per File**: Tests use one test class per file
2. **Docker-First**: Primary dev environment uses Docker
3. **Type Hints**: Always use Python type hints

## Project Structure

```
core/                # Universal schema and validation (the "Universal" part)
│   ├── schema.py    # Pydantic models defining Universal Carrier Format
│   └── validator.py # Validation logic for carrier responses
mappers/             # Carrier-specific response mappers
│   ├── example_mapper.py
│   └── example_template_mapper.py  # Example/template mapper
blueprints/          # Carrier configuration/logic (YAML)
│   └── dhl_express.yaml
src/                 # Document parser (PDF → JSON)
│   └── pdf_parser.py
tests/unit/          # Unit tests
tests/integration/   # Integration tests
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
- `mappers/example_mapper.py` - Example/reference mapper (carrier → Universal Format)
- `blueprints/dhl_express.yaml` - Example blueprint configuration
- `src/pdf_parser.py` - PDF parsing service (document parser)
- `docs/SYSTEM_OVERVIEW.md` - Complete system documentation
- `docs/ARCHITECTURE.md` - Component diagram and flow
- `CHANGELOG.md` - Project status and changes

## Code Style

- **Services**: Clear docstrings; no framework comparisons
- **Tests**: Use `@pytest.mark.unit` or `@pytest.mark.integration`
- **Type Hints**: Always include (e.g., `def method(self, param: str) -> dict:`)

## When Adding Code

1. Add type hints
2. Write tests in `tests/unit/` or `tests/integration/`
3. Update `CHANGELOG.md` with changes

## Quick Reference

| Concept | This project |
|---------|--------------|
| Unit tests | `tests/unit/` |
| Markers | `@pytest.mark.unit`, `@pytest.mark.integration` |
| Fixtures | `conftest.py` |
| Services | `src/` (parsers), `mappers/` |
| Schema | `src/core/` (schema) |
| Config | `blueprints/` (YAML), `.env` |

**See `docs/ARCHITECTURE.md` for component diagram and flow.**
