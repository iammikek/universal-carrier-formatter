# Universal Carrier Formatter

A Python tool that extracts structured API documentation from messy carrier PDFs using LLMs.

## Quick Start

### Option 1: Docker Development (Recommended)

```bash
# Build and start containers
docker-compose up -d

# Run tests
make docker-test-tests
# or: docker-compose exec app pytest tests/ -v

# Run formatter
docker-compose exec app python -m src.formatter --input examples/sample.pdf --output output.json

# See DOCKER.md for complete Docker guide
```

### Option 2: Local Virtual Environment

```bash
# Create virtual environment (like composer install)
make setup

# Or manually:
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

# Copy environment variables template
cp .env.example .env
# Edit .env and add your API keys

# Daily development
source .venv/bin/activate
make test
make format
make lint
```

## Pre-commit Checks

Before committing, ensure your code passes all linting checks. A pre-commit Git hook is set up to automatically format and check your code:

**Automatic (recommended):**
```bash
# The pre-commit hook runs automatically when you commit
git commit -m "Your message"
# Files are auto-formatted with isort then black, then checked
```

**Manual check before committing:**
```bash
# Option 1: Using Makefile (recommended)
make docker-pre-commit

# Option 2: Direct Docker commands
docker-compose exec app isort src/ tests/ scripts/
docker-compose exec app black src/ tests/ scripts/
docker-compose exec app flake8 src/ tests/ scripts/ --ignore=E501,W503,E203
```

**Important Notes:**
- The pre-commit hook is local to your repository (not tracked in git)
- The hook auto-formats files with `isort` then `black` before checking
- If checks fail, the commit is blocked with helpful error messages
- The hook matches the GitHub Actions CI pipeline exactly
- Each developer needs to ensure the hook is executable: `chmod +x .git/hooks/pre-commit`

## Development Pipeline

See [docs/DEVELOPMENT_PIPELINE.md](docs/DEVELOPMENT_PIPELINE.md) for detailed guide on:
- PHP → Python concepts mapping
- Testing workflow
- Project structure
- Common commands

See [docs/DOCKER.md](docs/DOCKER.md) for Docker development guide:
- Docker setup and usage
- Container commands
- Volume mounts and live editing
- Debugging in Docker

See [docs/DOCKER_SCRIPTS.md](docs/DOCKER_SCRIPTS.md) for Docker Compose scripts:
- Available scripts (like composer scripts in Laravel)
- Testing, formatting, linting shortcuts
- Quality checks and pre-commit hooks

See [docs/LARAVEL_COMPARISON.md](docs/LARAVEL_COMPARISON.md) for Laravel → Python comparisons:
- Service classes, models, controllers
- Dependency injection patterns
- Testing approaches
- CLI commands
- LangChain vs Laravel HTTP patterns

## Project Structure

```
universal-carrier-formatter/
├── src/                    # Main source code
│   ├── models/            # Universal Carrier Format models (Pydantic)
│   └── ...
├── tests/                 # Test files
├── examples/              # Sample PDFs and expected outputs
│   └── expected_output.json  # Example Universal Carrier Format JSON
├── docs/                  # Documentation
├── scripts/               # Utility scripts
├── requirements.txt       # Production dependencies
└── requirements-dev.txt   # Development dependencies
```

## Available Commands

Run `make help` to see all available commands, or check the Makefile.

## Universal Carrier Format

The project uses a standardized JSON schema to represent carrier API documentation. See `examples/expected_output.json` for a complete example.

The schema includes:
- **Endpoints**: API paths, methods, request/response schemas
- **Authentication**: API keys, OAuth, Bearer tokens, etc.
- **Parameters**: Query strings, path params, headers, body schemas
- **Rate Limits**: Request limits and periods
- **Metadata**: Carrier name, base URL, version, documentation links

Models are defined using Pydantic (similar to Laravel Eloquent models with validation).

## Testing

Tests use `pytest` (similar to PHPUnit in PHP):

```bash
# Run tests in tests/ directory (recommended)
make docker-test-tests
# or: ./scripts/test.sh
# or: docker-compose exec app pytest tests/ -v

# Run all tests
make docker-test
# or: docker-compose exec app pytest

# Run with coverage
make docker-test-coverage
# or: docker-compose exec app pytest --cov=src --cov-report=html

# Validate schema models (quick check)
docker-compose exec app python scripts/validate_schema.py
```

See [docs/TESTING.md](docs/TESTING.md) for complete testing guide.

## Next Steps

1. Define Universal Carrier Format schema
2. Implement PDF parser
3. Set up LLM integration
4. Build extraction pipeline
