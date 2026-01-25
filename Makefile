# Makefile for common development tasks
# Usage: make <command>
# Similar to composer scripts in PHP

.PHONY: help install test lint format clean run setup

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

setup: ## Initial setup: create venv and install dependencies
	python3 -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -r requirements-dev.txt
	@echo "Setup complete! Activate with: source .venv/bin/activate"

install: ## Install/update dependencies
	pip install -r requirements-dev.txt

test: ## Run all tests
	pytest

test-verbose: ## Run tests with verbose output
	pytest -v

test-coverage: ## Run tests with coverage report
	pytest --cov=src --cov-report=html --cov-report=term
	@echo "Coverage report generated in htmlcov/index.html"

lint: ## Run linter (flake8)
	flake8 src/ tests/

format: ## Format code with black
	black src/ tests/

format-check: ## Check code formatting without changing files
	black --check src/ tests/

type-check: ## Run type checker (mypy)
	mypy src/

clean: ## Clean up generated files
	rm -rf __pycache__/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -r {} +
	find . -type f -name "*.pyc" -delete

run: ## Run the formatter (example)
	python -m src.formatter --input examples/sample_carrier.pdf --output output.json

pre-commit: ## Run all checks before committing
	@echo "Running pre-commit checks..."
	black --check src/ tests/
	flake8 src/ tests/
	pytest

# Docker commands
docker-build: ## Build Docker images
	docker-compose build

docker-up: ## Start Docker containers
	docker-compose up -d

docker-down: ## Stop Docker containers
	docker-compose down

docker-logs: ## View Docker logs
	docker-compose logs -f app

docker-test: ## Run tests in Docker
	docker-compose exec app pytest

docker-test-tests: ## Run pytest tests/ directory (most common)
	docker-compose exec app pytest tests/ -v

docker-test-coverage: ## Run tests with coverage in Docker
	docker-compose exec app pytest --cov=src --cov-report=html --cov-report=term

docker-lint: ## Run linter in Docker
	docker-compose exec app flake8 src/ tests/

docker-format: ## Format code in Docker
	docker-compose exec app black src/ tests/

docker-shell: ## Open shell in Docker container
	docker-compose exec app /bin/bash

docker-python: ## Open Python shell in Docker
	docker-compose exec app python

docker-rebuild: ## Rebuild and restart Docker containers
	docker-compose down
	docker-compose build --no-cache
	docker-compose up -d

docker-clean: ## Remove Docker containers and volumes
	docker-compose down -v

# Docker Compose Scripts (like composer scripts in Laravel)
# Usage: make docker-script-<name> or docker-compose run --rm <service-name>

docker-script-test: ## Run all tests via Docker script
	docker-compose --profile scripts run --rm test-all

docker-script-test-dir: ## Run tests in tests/ directory via Docker script
	docker-compose --profile scripts run --rm pytest-tests

# Convenience alias for the most common test command
docker-test-tests: ## Run pytest tests/ (alias for docker-compose exec app pytest tests/)
	docker-compose exec app pytest tests/ -v

docker-script-coverage: ## Run tests with coverage via Docker script
	docker-compose --profile scripts run --rm test-coverage

docker-script-format: ## Format code via Docker script
	docker-compose --profile scripts run --rm format

docker-script-format-check: ## Check formatting via Docker script
	docker-compose --profile scripts run --rm format-check

docker-script-lint: ## Run linter via Docker script
	docker-compose --profile scripts run --rm lint-check

docker-script-type-check: ## Run type checker via Docker script
	docker-compose --profile scripts run --rm type-check

docker-script-validate: ## Validate schema via Docker script
	docker-compose --profile scripts run --rm validate-schema

docker-script-quality: ## Run all quality checks via Docker script
	docker-compose --profile scripts run --rm quality

docker-script-pre-commit: ## Run pre-commit checks via Docker script
	docker-compose --profile scripts run --rm pre-commit

docker-script-shell: ## Open Python shell via Docker script
	docker-compose --profile scripts run --rm shell

docker-script-ipython: ## Open IPython shell via Docker script
	docker-compose --profile scripts run --rm ipython
