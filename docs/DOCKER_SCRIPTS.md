# Docker Compose Scripts Guide

## Overview

Docker Compose scripts are like Laravel's `composer scripts` - convenient shortcuts for common development tasks.

**Laravel Equivalent:**
```json
// composer.json
{
  "scripts": {
    "test": "phpunit",
    "format": "php-cs-fixer fix",
    "quality": "phpunit && php-cs-fixer check"
  }
}
```

**Usage:**
```bash
# Laravel
composer test
composer format
composer quality

# This project
docker-compose --profile scripts run --rm test-all
docker-compose --profile scripts run --rm format
docker-compose --profile scripts run --rm quality
```

## Available Scripts

### Testing Scripts

```bash
# Run all tests
docker-compose --profile scripts run --rm test-all
# or: make docker-script-test

# Run tests with coverage
docker-compose --profile scripts run --rm test-coverage
# or: make docker-script-coverage

# Run specific test file
docker-compose --profile scripts run --rm test-file
```

### Code Quality Scripts

```bash
# Format code (like php-cs-fixer fix)
docker-compose --profile scripts run --rm format
# or: make docker-script-format

# Check formatting without changing files (like php-cs-fixer check)
docker-compose --profile scripts run --rm format-check
# or: make docker-script-format-check

# Run linter (like phpcs)
docker-compose --profile scripts run --rm lint-check
# or: make docker-script-lint

# Run type checker (like phpstan)
docker-compose --profile scripts run --rm type-check
# or: make docker-script-type-check
```

### Validation Scripts

```bash
# Validate schema models
docker-compose --profile scripts run --rm validate-schema
# or: make docker-script-validate
```

### Combined Scripts

```bash
# Run all quality checks (like composer test in Laravel)
docker-compose --profile scripts run --rm quality
# or: make docker-script-quality

# Pre-commit checks (run before committing)
docker-compose --profile scripts run --rm pre-commit
# or: make docker-script-pre-commit
```

### Interactive Scripts

```bash
# Open Python shell (like php artisan tinker)
docker-compose --profile scripts run --rm shell
# or: make docker-script-shell

# Open IPython shell (better REPL)
docker-compose --profile scripts run --rm ipython
# or: make docker-script-ipython
```

## Using Makefile Shortcuts

All scripts are available via Makefile for convenience:

```bash
make docker-script-test          # Run tests
make docker-script-coverage     # Tests with coverage
make docker-script-format       # Format code
make docker-script-lint         # Run linter
make docker-script-quality      # All quality checks
make docker-script-pre-commit   # Pre-commit checks
make docker-script-validate     # Validate schema
make docker-script-shell        # Python shell
make docker-script-ipython      # IPython shell
```

## How It Works

### Docker Compose Profiles

Scripts use Docker Compose **profiles** to organize services:

```yaml
services:
  test-all:
    extends: service: app
    command: pytest -v
    profiles:
      - scripts  # Only loaded when --profile scripts is used
```

**Benefits:**
- Scripts don't start automatically with `docker-compose up`
- Clean separation between app services and utility scripts
- Faster startup (only loads what you need)

### Service Extension

Scripts extend the `app` service to reuse configuration:

```yaml
test-all:
  extends:
    service: app  # Inherit volumes, environment, etc.
  command: pytest -v  # Override command
```

This is like Laravel's service inheritance or trait usage.

## Common Workflows

### Daily Development

```bash
# Start containers
docker-compose up -d

# Make code changes...

# Format code
make docker-script-format

# Run tests
make docker-script-test

# Run all checks before committing
make docker-script-pre-commit
```

### Before Committing

```bash
# Run all quality checks
make docker-script-quality

# Or just pre-commit checks
make docker-script-pre-commit
```

### Debugging

```bash
# Open Python shell to test code interactively
make docker-script-shell

# Or use IPython (better REPL)
make docker-script-ipython
```

## Comparison: Laravel vs Docker Compose Scripts

| Laravel | Docker Compose Scripts |
|---------|------------------------|
| `composer test` | `docker-compose --profile scripts run --rm test-all` |
| `composer format` | `docker-compose --profile scripts run --rm format` |
| `composer quality` | `docker-compose --profile scripts run --rm quality` |
| `php artisan tinker` | `docker-compose --profile scripts run --rm shell` |
| `composer scripts` in composer.json | `services:` in docker-compose.yml |

## Adding New Scripts

To add a new script:

1. Add service to `docker-compose.yml`:
```yaml
my-script:
  extends:
    service: app
  command: python scripts/my_script.py
  profiles:
    - scripts
```

2. Add Makefile shortcut (optional):
```makefile
docker-script-my-script: ## Run my script
	docker-compose --profile scripts run --rm my-script
```

3. Use it:
```bash
docker-compose --profile scripts run --rm my-script
# or: make docker-script-my-script
```

## Tips

- Scripts run in isolated containers (like `--rm` flag)
- All scripts have access to your mounted volumes (code, tests, etc.)
- Scripts inherit environment variables from `.env` file
- Use `--rm` flag to automatically remove container after running
- Scripts can be run even if main `app` container isn't running
