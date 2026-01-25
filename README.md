# Universal Carrier Formatter

A Python tool that extracts structured API documentation from messy carrier PDFs using LLMs.

## Quick Start

### Option 1: Docker Development (Recommended)

```bash
# Build and start containers
docker-compose up -d

# Run tests
make docker-test
# or: docker-compose exec app pytest

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

See [docs/LARAVEL_COMPARISON.md](docs/LARAVEL_COMPARISON.md) for Laravel → Python comparisons:
- Service classes, models, controllers
- Dependency injection patterns
- Testing approaches
- CLI commands
- LangChain vs Laravel HTTP patterns

## Project Structure

```
universal-carrier-formatter/
├── src/              # Main source code
├── tests/            # Test files
├── examples/         # Sample PDFs and expected outputs
├── requirements.txt  # Production dependencies
└── requirements-dev.txt  # Development dependencies
```

## Available Commands

Run `make help` to see all available commands, or check the Makefile.

## Testing

Tests use `pytest` (similar to PHPUnit in PHP):

```bash
pytest                    # Run all tests
pytest -v                 # Verbose output
pytest tests/test_basic.py  # Run specific test file
pytest --cov=src          # With coverage report
```

## Next Steps

1. Define Universal Carrier Format schema
2. Implement PDF parser
3. Set up LLM integration
4. Build extraction pipeline
