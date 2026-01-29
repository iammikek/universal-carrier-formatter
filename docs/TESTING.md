# Quick Reference: Running Tests

## LLM mocking (no real API calls)

**.env is not required to run tests.** CI does not set `OPENAI_API_KEY` or any LLM secrets. All tests that use LLM-backed features mock the LLM interfaces:

- **Extraction / formatter:** `LlmExtractorService` or `ExtractionPipeline` is patched (e.g. `tests/integration/test_extraction_golden.py`, `test_extraction_pipeline.py`, `test_formatter_cli.py`, `test_api.py`).
- **Mapper generator:** `ChatOpenAI` is patched and tests pass `api_key="test-key"` (e.g. `tests/unit/test_mapper_generator.py`).
- **LLM extractor unit tests:** `ChatOpenAI` is patched; the test that checks “API key required” clears `os.environ` and expects `ValueError`.

Do not add tests that call real LLM APIs. Keep mocking so CI stays fast and no secrets are needed.

## Default: Python in Docker

Tests run in Docker by default. No local Python needed.

```bash
# One-time: build image (and optionally cp .env.example .env)
make setup

# Run tests
make test
```

`make test` runs `docker-compose run --rm app pytest tests/ -v`. The image uses Python 3.11.

## Option 1: Using Shell Script (when app container is running)

```bash
# Run tests in tests/ directory
./scripts/test.sh

# Pass additional pytest arguments
./scripts/test.sh -k test_carrier
./scripts/test.sh --cov=src
```

## Option 2: Using Makefile (Recommended)

```bash
# Run tests in tests/ directory (most common)
make docker-test-tests

# This runs: docker-compose exec app pytest tests/ -v
```

## Option 3: Direct docker-compose exec

```bash
# Start containers first
docker-compose up -d

# Run tests in tests/ directory
docker-compose exec app pytest tests/ -v

# Or without verbose flag
docker-compose exec app pytest tests/
```

## Option 4: Using Docker Compose Scripts (doesn't require app container)

```bash
# Run tests in tests/ directory
docker-compose --profile scripts run --rm pytest-tests

# Or use Makefile shortcut
make docker-script-test-dir
```

## All Available Test Commands

```bash
# Shell script (easiest)
./scripts/test.sh

# Makefile shortcuts
make docker-test-tests          # Run tests/ directory (most common)
make docker-test                # Run all tests
make docker-test-coverage       # Run with coverage

# Direct docker-compose
docker-compose exec app pytest tests/ -v
docker-compose exec app pytest
docker-compose exec app pytest --cov=src --cov-report=html

# Docker Compose scripts (isolated containers)
make docker-script-test-dir     # Run tests/ via script
make docker-script-test         # Run all tests via script
make docker-script-coverage     # Run with coverage via script
```

## Comparison

| Method | Command | Requires app running? | Cleanup | Use Case |
|--------|---------|---------------------|---------|----------|
| Shell script | `./scripts/test.sh` | ✅ Yes | Manual | Daily development (easiest) |
| Makefile | `make docker-test-tests` | ✅ Yes | Manual | Daily development (recommended) |
| docker-compose exec | `docker-compose exec app pytest tests/` | ✅ Yes | Manual | Daily development |
| docker-compose script | `docker-compose --profile scripts run --rm pytest-tests` | ❌ No | Automatic (`--rm`) | CI/CD, one-off runs |

## Golden tests (extraction reproducibility)

Golden tests lock down extraction for a fixed input and mocked LLM so we can regression-test schema.json shape and extraction_metadata (LLM config, prompt_versions). See [Extraction reproducibility](EXTRACTION_REPRODUCIBILITY.md) for details.

```bash
# Run golden tests only
docker compose run --rm app pytest tests/integration/test_extraction_golden.py -v
```

Fixtures: **`tests/fixtures/golden_extracted_text.txt`** (fixed extracted text), **`tests/fixtures/golden_expected_schema.json`** (expected key invariants). Tests assert extraction_metadata and schema invariants; one test optionally compares to the golden expected JSON.

## Recommendation

For daily development, use:
```bash
make docker-test-tests
```

Or the shell script:
```bash
./scripts/test.sh
```

Both are fast since the container is already running and you can run multiple commands in the same session.
