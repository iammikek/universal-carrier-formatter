# AI Agents Guide

This document provides guidance for AI agents and assistants working on this project.

## Project Overview

**Universal Carrier Formatter** - A Python tool that extracts structured API documentation from messy carrier PDFs using LLMs (LangChain).

## Key Project Context

### Technology Stack
- **Language**: Python 3.11+
- **Framework**: Pydantic for data models, LangChain for LLM integration
- **Testing**: pytest (similar to PHPUnit in Laravel)
- **Development**: Docker Compose for local development
- **LLM**: LangChain with OpenAI/Anthropic support

### Important Patterns

1. **Laravel Comparisons**: This project includes extensive Laravel → Python comparisons throughout the codebase. Always reference Laravel equivalents when explaining concepts.

2. **One Class Per File**: Test files follow Laravel convention - one test class per file in `tests/unit/` directory.

3. **Docker-First Development**: Primary development environment uses Docker. Commands should work in Docker containers.

4. **Type Hints**: All code uses Python type hints (like PHP type hints in Laravel).

## Project Structure

```
universal-carrier-formatter/
├── src/
│   ├── models/              # Pydantic models (like Laravel Models)
│   │   └── carrier_schema.py
│   ├── pdf_parser.py       # PDF parsing (future)
│   ├── llm_extractor.py    # LLM integration (future)
│   └── formatter.py         # Main CLI entry point (future)
├── tests/
│   ├── unit/                # Unit tests (like tests/Unit/ in Laravel)
│   ├── integration/        # Integration tests (like tests/Feature/)
│   └── conftest.py          # Shared fixtures (like setUp())
├── docs/                    # Documentation
├── examples/                # Example PDFs and outputs
└── scripts/                 # Utility scripts
```

## Code Style Guidelines

### Laravel Comparisons
- Always include Laravel equivalent comments when creating new classes/methods
- Reference Laravel patterns in docstrings
- Use Laravel terminology when explaining concepts

**Example:**
```python
class PdfParserService:
    """
    PDF parsing service.
    
    Laravel Equivalent: app/Services/PdfParserService.php
    
    class PdfParserService
    {
        public function extract(string $pdfPath): string
        {
            // Implementation
        }
    }
    """
```

### Testing
- Use `@pytest.mark.unit` for unit tests
- Use `@pytest.mark.integration` for integration tests
- One test class per file (Laravel convention)
- Tests go in `tests/unit/` or `tests/integration/`

### Type Hints
- Always include type hints for function parameters and return types
- Use Pydantic models for data validation
- Example: `def extract(self, pdf_path: str) -> str:`

## Common Commands

### Docker Development
```bash
# Start containers
docker-compose up -d

# Run tests
make docker-test-tests
# or: docker-compose exec app pytest tests/unit/ -v

# Run specific test file
docker-compose exec app pytest tests/unit/test_parameter.py

# Format code
make docker-format

# Run linter
make docker-lint
```

### Testing
```bash
# Run all unit tests
pytest -m unit

# Run all integration tests
pytest -m integration

# Run specific directory
pytest tests/unit/
```

## Key Files to Reference

### Documentation
- `docs/LARAVEL_COMPARISON.md` - Comprehensive Laravel → Python guide
- `docs/TEST_ORGANIZATION.md` - Test structure and best practices
- `docs/DOCKER.md` - Docker development guide
- `docs/DOCKER_SCRIPTS.md` - Docker Compose scripts reference

### Code Examples
- `src/models/carrier_schema.py` - Example of Pydantic models with Laravel comparisons
- `tests/unit/test_parameter.py` - Example of unit test structure
- `src/_example_service_template.py` - Template for service classes

## Development Workflow

1. **Make Changes**: Edit files in `src/` or `tests/`
2. **Run Tests**: `make docker-test-tests` or `./scripts/test.sh`
3. **Format Code**: `make docker-format`
4. **Check Quality**: `make docker-script-quality`
5. **Commit**: Follow conventional commit messages

## Important Notes for AI Agents

### When Adding New Code

1. **Include Laravel Comparisons**: Always add comments comparing to Laravel patterns
2. **Add Type Hints**: Use Python type hints throughout
3. **Write Tests**: Add unit tests in `tests/unit/` with `@pytest.mark.unit`
4. **Update Documentation**: Update relevant docs if adding new features
5. **Follow Existing Patterns**: Match the style of existing code

### When Explaining Concepts

1. **Reference Laravel**: Compare Python patterns to Laravel equivalents
2. **Use Examples**: Provide code examples from the project
3. **Explain Differences**: Highlight where Python differs from PHP/Laravel
4. **Be Specific**: Reference actual files and classes in the project

### Common Patterns

**Service Classes:**
```python
class MyService:
    """
    Service description.
    
    Laravel Equivalent: app/Services/MyService.php
    """
    def __init__(self, config: Optional[dict] = None):
        self.config = config or {}
    
    def process(self, data: str) -> dict:
        """Process data. Returns dict."""
        pass
```

**Models:**
```python
class MyModel(BaseModel):
    """
    Model description.
    
    Laravel Equivalent: app/Models/MyModel.php
    """
    name: str = Field(..., min_length=1)
    value: Optional[int] = None
```

**Tests:**
```python
@pytest.mark.unit
class TestMyModel:
    """
    Test MyModel.
    
    Laravel Equivalent: tests/Unit/MyModelTest.php
    """
    def test_creates_model(self):
        model = MyModel(name="test")
        assert model.name == "test"
```

## Current Project Status

### ✅ Completed
- Project structure and Docker setup
- Universal Carrier Format schema (Pydantic models)
- Test organization (unit/integration split)
- Documentation and Laravel comparison guides

### 🚧 In Progress / Next Steps
- PDF parser implementation
- LLM integration (LangChain)
- Prompt engineering module
- Extraction pipeline
- CLI interface

## Questions to Ask

If you're an AI agent working on this project and need clarification:

1. **Check Documentation**: Review `docs/` directory first
2. **Review Examples**: Look at existing code in `src/models/` and `tests/unit/`
3. **Follow Patterns**: Match existing code style and structure
4. **Test Everything**: Always add tests for new functionality

## Resources

- **Laravel Docs**: https://laravel.com/docs (for comparison reference)
- **Pydantic Docs**: https://docs.pydantic.dev/
- **LangChain Docs**: https://python.langchain.com/
- **pytest Docs**: https://docs.pytest.org/

## Quick Reference

| Laravel | Python/This Project |
|---------|---------------------|
| `tests/Unit/` | `tests/unit/` |
| `tests/Feature/` | `tests/integration/` |
| `@group unit` | `@pytest.mark.unit` |
| `setUp()` | `conftest.py` fixtures |
| `app/Services/` | `src/` (service classes) |
| `app/Models/` | `src/models/` |
| `composer scripts` | Docker Compose scripts |

---

**Last Updated**: 2026-01-25  
**Project**: Universal Carrier Formatter  
**Language**: Python 3.11+  
**Framework**: Pydantic + LangChain
