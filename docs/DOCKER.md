# Docker Development Guide

## Quick Start

### 1. Build and Start Containers

```bash
# Build and start the app container (like docker-compose up in PHP projects)
docker-compose up -d

# View logs
docker-compose logs -f app
```

### 2. Run Commands in Container

```bash
# Run tests (like running phpunit in Docker)
docker-compose exec app pytest

# Run specific test
docker-compose exec app pytest tests/test_basic.py

# Run with coverage
docker-compose exec app pytest --cov=src --cov-report=html

# Format code
docker-compose exec app black src/ tests/

# Lint code
docker-compose exec app flake8 src/ tests/

# Run the formatter
docker-compose exec app python -m src.formatter --input examples/sample.pdf --output output.json

# Open Python shell (like php artisan tinker)
docker-compose exec app python

# Open IPython (better REPL)
docker-compose exec app ipython
```

### 3. Using Docker Compose Profiles

```bash
# Run tests in dedicated test container
docker-compose --profile test run --rm test

# Run linter in dedicated container
docker-compose --profile lint run --rm lint

# Run tests with coverage
docker-compose --profile test run --rm test pytest --cov=src --cov-report=html
```

## Development Workflow

### Daily Workflow

```bash
# Start containers (first time or after docker-compose down)
docker-compose up -d

# Make code changes in your editor (files are mounted as volumes)

# Run tests to verify changes
docker-compose exec app pytest

# Format code
docker-compose exec app black src/ tests/

# When done, stop containers
docker-compose down
```

### Rebuilding After Dependency Changes

```bash
# If you update pyproject.toml or uv.lock, rebuild
docker compose build

# Or rebuild and restart
docker-compose up -d --build
```

## Docker vs Local Development

### Use Docker when:
- ✅ You want consistent environment across team
- ✅ You don't want to manage Python versions locally
- ✅ You're on a system where installing Python is difficult
- ✅ You want to test in isolated environment

### Use Local Virtual Environment when:
- ✅ You prefer faster iteration (no Docker overhead)
- ✅ You want to use IDE debugging features directly
- ✅ You're comfortable managing Python versions

**You can use both!** Docker for CI/CD and team consistency, local venv for daily development.

## Common Docker Commands

```bash
# Build
docker-compose build

# Start containers
docker-compose up -d

# Stop containers
docker-compose down

# View logs
docker-compose logs -f app

# Execute command in container
docker-compose exec app <command>

# Rebuild and restart
docker-compose up -d --build

# Remove containers and volumes
docker-compose down -v

# Run one-off command
docker-compose run --rm app pytest

# Check container status
docker-compose ps
```

## Environment Variables

The `.env` file is mounted as read-only volume. To update:
1. Edit `.env` file locally
2. Restart container: `docker-compose restart app`

Or set in `docker-compose.yml`:
```yaml
environment:
  - OPENAI_API_KEY=${OPENAI_API_KEY}
```

## Volume Mounts Explained

```yaml
volumes:
  - ./src:/app/src          # Your code (live editing)
  - ./tests:/app/tests      # Your tests (live editing)
  - ./examples:/app/examples # Example files
  - ./.env:/app/.env:ro     # Environment variables (read-only)
  - ./output:/app/output    # Output files persist on host
```

Changes to `src/` and `tests/` are immediately reflected in the container (no rebuild needed).

## Debugging in Docker

```bash
# Run with Python debugger
docker-compose exec app python -m pdb -m pytest tests/test_basic.py

# Run IPython debugger
docker-compose exec app ipython

# View container shell
docker-compose exec app /bin/bash

# Check Python version
docker-compose exec app python --version

# Check installed packages
docker-compose exec app pip list
```

## Troubleshooting

### Container won't start
```bash
# Check logs
docker-compose logs app

# Rebuild from scratch
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

### Changes not reflecting
- Make sure volumes are mounted correctly
- Restart container: `docker-compose restart app`

### Permission issues
```bash
# Fix ownership (if needed)
docker-compose exec app chown -R appuser:appuser /app
```

## Integration with Makefile

You can add Docker commands to Makefile:

```makefile
docker-up:
	docker-compose up -d

docker-test:
	docker-compose exec app pytest

docker-shell:
	docker-compose exec app /bin/bash
```

Then use: `make docker-test`
