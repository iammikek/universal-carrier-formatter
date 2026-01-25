# Test Organization Best Practices

## PHPUnit/Laravel Structure

```
tests/
├── Unit/                    # Unit tests (isolated, fast)
│   ├── ParameterTest.php
│   ├── EndpointTest.php
│   └── CarrierSchemaTest.php
└── Feature/                 # Feature/Integration tests (full workflows)
    ├── PdfParserTest.php
    └── FormatterPipelineTest.php
```

**PHPUnit Convention:**
- **Unit tests**: Test individual classes/methods in isolation (mocked dependencies)
- **Feature tests**: Test complete workflows, HTTP requests, database interactions

## Python/pytest Structure (Recommended)

```
tests/
├── unit/                    # Unit tests (isolated, fast)
│   ├── __init__.py
│   ├── test_parameter.py
│   ├── test_endpoint.py
│   └── test_carrier_schema.py
├── integration/            # Integration tests (full workflows)
│   ├── __init__.py
│   ├── test_pdf_parser.py
│   └── test_formatter_pipeline.py
└── conftest.py             # Shared fixtures (like PHPUnit setUp)
```

**pytest Convention:**
- **Unit tests** (`tests/unit/`): Test individual functions/classes in isolation
- **Integration tests** (`tests/integration/`): Test complete workflows, external dependencies
- **Fixtures** (`conftest.py`): Shared test setup (like PHPUnit's `setUp()`)

## Key Differences

| PHPUnit/Laravel | pytest | Purpose |
|----------------|---------|---------|
| `tests/Unit/` | `tests/unit/` | Unit tests (isolated) |
| `tests/Feature/` | `tests/integration/` | Integration/functional tests |
| `setUp()` method | `conftest.py` fixtures | Shared test setup |
| `@group unit` | `@pytest.mark.unit` | Test markers/tags |
| `@group integration` | `@pytest.mark.integration` | Test markers/tags |

## Best Practices

### 1. Directory Structure

**Option A: By Type (Recommended - matches Laravel)**
```
tests/
├── unit/              # Unit tests
├── integration/       # Integration tests
└── conftest.py        # Shared fixtures
```

**Option B: By Feature (Alternative)**
```
tests/
├── models/           # All model tests
├── services/         # All service tests
└── integration/      # Integration tests
```

### 2. Test Markers (Like PHPUnit @group)

```python
# tests/unit/test_parameter.py
import pytest

@pytest.mark.unit
class TestParameter:
    def test_creates_parameter(self):
        pass

# tests/integration/test_pipeline.py
import pytest

@pytest.mark.integration
class TestFormatterPipeline:
    def test_full_pipeline(self):
        pass
```

**Run specific test types:**
```bash
pytest -m unit              # Run only unit tests
pytest -m integration      # Run only integration tests
pytest -m "not integration" # Run everything except integration
```

### 3. Fixtures (Like PHPUnit setUp)

**PHPUnit:**
```php
class ParameterTest extends TestCase
{
    protected function setUp(): void
    {
        parent::setUp();
        $this->parameter = new Parameter();
    }
}
```

**pytest:**
```python
# tests/conftest.py
import pytest
from src.models import Parameter

@pytest.fixture
def sample_parameter():
    """Fixture (like setUp) - shared across tests"""
    return Parameter(
        name="test_param",
        type=ParameterType.STRING,
        location=ParameterLocation.PATH
    )

# tests/unit/test_parameter.py
def test_parameter(sample_parameter):  # Fixture injected automatically
    assert sample_parameter.name == "test_param"
```

### 4. Test File Naming

**PHPUnit:** `ParameterTest.php` (class name)
**pytest:** `test_parameter.py` (file name with `test_` prefix)

Both are valid, but pytest convention uses `test_` prefix.

## Recommended Structure for This Project

```
tests/
├── unit/                          # Unit tests (fast, isolated)
│   ├── __init__.py
│   ├── test_parameter.py         # Parameter model tests
│   ├── test_endpoint.py          # Endpoint model tests
│   ├── test_carrier_schema.py    # UniversalCarrierFormat tests
│   ├── test_response_schema.py   # ResponseSchema tests
│   └── test_request_schema.py    # RequestSchema tests
│
├── integration/                   # Integration tests (slower, full workflows)
│   ├── __init__.py
│   ├── test_pdf_parser.py        # PDF parsing with real files
│   ├── test_llm_extractor.py     # LLM extraction (may use real API)
│   └── test_formatter_pipeline.py # Full pipeline end-to-end
│
└── conftest.py                    # Shared fixtures
```

## Configuration

**pytest.ini** (like phpunit.xml):
```ini
[pytest]
# Test discovery
testpaths = tests
python_files = test_*.py
python_classes = Test*

# Markers (like @group in PHPUnit)
markers =
    unit: Unit tests (fast, no external dependencies)
    integration: Integration tests (slower, may use external APIs)
    slow: Slow running tests

# Run options
addopts = 
    -v
    --strict-markers
    --tb=short
```

## Running Tests

```bash
# Run all tests
pytest

# Run only unit tests (like phpunit --group unit)
pytest -m unit

# Run only integration tests (like phpunit --group integration)
pytest -m integration

# Run specific directory
pytest tests/unit/
pytest tests/integration/

# Run specific file
pytest tests/unit/test_parameter.py
```

## Comparison Summary

| Aspect | PHPUnit/Laravel | pytest |
|--------|----------------|--------|
| **Unit tests** | `tests/Unit/` | `tests/unit/` |
| **Feature tests** | `tests/Feature/` | `tests/integration/` |
| **Shared setup** | `setUp()` method | `conftest.py` fixtures |
| **Test groups** | `@group unit` | `@pytest.mark.unit` |
| **Run by group** | `phpunit --group unit` | `pytest -m unit` |
| **File naming** | `ParameterTest.php` | `test_parameter.py` |

## Migration Path

If you want to migrate current tests to this structure:

1. Create `tests/unit/` directory
2. Move model tests to `tests/unit/`
3. Add `@pytest.mark.unit` markers
4. Create `tests/integration/` for future integration tests
5. Update `pytest.ini` with markers

This matches Laravel's structure and makes tests easier to organize!
