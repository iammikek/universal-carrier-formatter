# Development Pipeline Guide

## Project Structure

See [Project Structure](../README.md#project-structure) in the README for the full directory tree. Summary: `src/` (core, mappers, blueprints, formatter, api, …), `blueprints/`, `examples/`, `output/`, `scripts/`, `tests/`, `docs/`, plus `pyproject.toml`, `uv.lock`, `Dockerfile`, `docker-compose.yml`, `Makefile`.

## Development Workflow

### Option A: Docker Development (Recommended for consistency)

```bash
# Build and start containers
docker-compose up -d

# Run tests
docker-compose exec app pytest

# Run formatter
docker-compose exec app python -m src.formatter --input examples/sample.pdf --output output.json

# See DOCKER.md for full Docker guide
```

### Option B: Local Virtual Environment

### 1. Initial Setup (One-time)

```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # On macOS/Linux
# .venv\Scripts\activate    # On Windows

# Install dependencies (from pyproject.toml + uv.lock)
uv sync --extra dev
# Or: pip install -e ".[dev]"
```

### 2. Daily Development Workflow

```bash
# Activate virtual environment (do this each time you open terminal)
source .venv/bin/activate

# Run tests
pytest

# Run tests with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_pdf_parser.py

# Run specific test
pytest tests/test_pdf_parser.py::test_extract_text

# Run linter
flake8 src/ tests/

# Format code
black src/ tests/

# Run the main script
python -m src.formatter --input examples/sample_carrier.pdf --output output.json
```

### 3. Testing Strategy

**Unit Tests**:
- Test individual functions/modules in isolation
- Mock external dependencies (LLM API, PDF parsing)
- Fast execution

**Integration Tests**:
- Test full pipeline with sample PDFs
- Use mock LLM responses or test API keys
- Verify end-to-end flow

**Test-Driven Development (TDD)**:
1. Write test first (red)
2. Write minimal code to pass (green)
3. Refactor (blue)

### 4. Development Pipeline Stages

#### Stage 1: Local Development
```bash
# Write code → Run tests → Fix issues → Repeat
pytest -v                    # Verbose test output
pytest --pdb                 # Drop into debugger on failure
```

#### Stage 2: Pre-commit Checks
```bash
# Before committing (can automate with git hooks)
pytest                       # All tests pass
flake8 src/ tests/          # Code style check
black --check src/ tests/   # Code formatting check
```

#### Stage 3: CI/CD (Future)
- GitHub Actions / GitLab CI
- Run tests on every push
- Check code quality
- Build and deploy

## Key Python Testing Concepts

### Writing Tests (pytest)

```python
# tests/test_pdf_parser.py
import pytest
from src.pdf_parser import extract_text_from_pdf

def test_extract_text_from_pdf():
    """Test PDF text extraction"""
    # Arrange
    pdf_path = "examples/sample_carrier.pdf"
    
    # Act
    result = extract_text_from_pdf(pdf_path)
    
    # Assert
    assert result is not None
    assert len(result) > 0
    assert "API" in result or "endpoint" in result.lower()
```

### Fixtures

```python
# tests/conftest.py
import pytest
import tempfile
import os

@pytest.fixture
def sample_pdf():
    """Create a temporary PDF file for testing"""
    # Setup
    pdf_content = b"PDF content here"
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as f:
        f.write(pdf_content)
        temp_path = f.name
    
    yield temp_path
    
    # Teardown
    os.unlink(temp_path)
```

### Mocking

```python
from unittest.mock import Mock, patch

def test_llm_extraction(mocker):
    """Test LLM extraction with mocked API call"""
    # Mock the LLM API call
    mock_response = {"endpoints": [{"path": "/api/v1/shipments"}]}
    
    with patch('src.llm_extractor.call_llm_api') as mock_llm:
        mock_llm.return_value = mock_response
        
        result = extract_with_llm("some text")
        
        assert result["endpoints"] is not None
        mock_llm.assert_called_once()
```

## Environment Variables

Create `.env` file:
```bash
# .env
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
LOG_LEVEL=DEBUG
```

Load with `python-dotenv`:
```python
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')
```

## Debugging

```python
# Use print statements for quick debug
print(f"Debug: {variable}")

# Use Python debugger
import pdb; pdb.set_trace()

# Use logging (better than print)
import logging
logging.debug(f"Processing PDF: {pdf_path}")
```

## Common Commands Cheat Sheet

```bash
# Virtual Environment
python3 -m venv .venv              # Create venv
source .venv/bin/activate          # Activate
deactivate                         # Deactivate

# Dependencies (pyproject.toml + uv.lock)
uv sync --extra dev                 # Install from lockfile (dev deps)
uv add package_name                 # Add package and update lock
uv lock                             # Refresh lock after editing pyproject.toml
uv pip list                         # List installed packages

# Testing
pytest                             # Run all tests
pytest -v                          # Verbose
pytest -k "test_name"              # Run specific test
pytest --cov=src                   # With coverage
pytest --pdb                       # Debug on failure

# Code Quality
flake8 src/                        # Lint
black src/                         # Format
black --check src/                 # Check formatting
isort src/                         # Sort imports
mypy src/                          # Full type check (non-blocking in CI)
mypy src/core/                     # Strict subset (blocking in CI; keep core clean)

# Running
python -m src.formatter            # Run as module
python src/formatter.py            # Run script directly
```

## Next Steps

1. Set up project structure
2. Create virtual environment
3. Install dependencies
4. Write first test
5. Implement first feature
6. Iterate: test → code → refactor
