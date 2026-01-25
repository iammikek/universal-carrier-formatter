# Quick Reference: Running Tests

## Option 1: Using Shell Script (Easiest)

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
