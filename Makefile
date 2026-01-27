# Makefile for common development tasks
# Usage: make <command>
# Python runs in Docker by default (app service uses python:3.11).

.PHONY: help build test test-coverage lint format format-check type-check clean run setup pre-commit

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

build: ## Build Docker image (run once, or after Dockerfile/requirements change)
	docker-compose build app

test: ## Run tests in Docker (no local Python required)
	docker-compose run --rm app pytest tests/ -v

test-coverage: ## Run tests with coverage in Docker (writes htmlcov/ locally)
	docker-compose run --rm app pytest tests/ --cov=src --cov-report=html --cov-report=term
	@echo "Coverage: open htmlcov/index.html"

lint: ## Run linter in Docker
	docker-compose run --rm app flake8 src/ tests/ --ignore=E501,W503,E203

format: ## Format code in Docker
	docker-compose run --rm app black src/ tests/ scripts/

format-check: ## Check code formatting in Docker (CI)
	docker-compose run --rm app black --check src/ tests/ scripts/

type-check: ## Run type checker in Docker
	docker-compose run --rm app mypy src/

clean: ## Clean up generated files
	rm -rf __pycache__/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -r {} +
	find . -type f -name "*.pyc" -delete

run: ## Run formatter in Docker (example PDF → schema)
	docker-compose run --rm app python -m src.formatter --input examples/dhl_express_api_docs.pdf --output output/schema.json

setup: ## One-time: build Docker image; copy .env.example to .env if missing
	docker-compose build app
	@test -f .env || (cp -n .env.example .env 2>/dev/null || true; echo "Add API keys to .env if using LLM/formatter.")

pre-commit: ## Run format, lint, tests in Docker (matches CI)
	docker-compose run --rm app sh -c "black src/ tests/ scripts/ && flake8 src/ tests/ scripts/ --ignore=E501,W503,E203 && pytest tests/ -v"
	@echo "✅ Pre-commit checks passed!"

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

docker-pre-commit: ## Run all pre-commit checks in Docker (matches CI pipeline)
	@echo "Running pre-commit checks in Docker (matching CI pipeline)..."
	@echo ""
	@echo "Formatting with isort and black..."
	@docker-compose exec app isort src/ tests/ scripts/
	@docker-compose exec app black src/ tests/ scripts/
	@echo "✓ Code formatted"
	@echo ""
	@echo "Checking black formatting..."
	@docker-compose exec app black --check src/ tests/ scripts/ || (echo "❌ Black check failed. Run: docker-compose exec app black src/ tests/ scripts/" && exit 1)
	@echo "✓ Black formatting OK"
	@echo ""
	@echo "Checking isort import sorting..."
	@docker-compose exec app isort --check-only src/ tests/ scripts/ || (echo "❌ isort check failed. Run: docker-compose exec app isort src/ tests/ scripts/" && exit 1)
	@echo "✓ isort import sorting OK"
	@echo ""
	@echo "Running flake8 linting..."
	@docker-compose exec app flake8 src/ tests/ scripts/ --ignore=E501,W503,E203 || (echo "❌ flake8 check failed" && exit 1)
	@echo "✓ flake8 linting OK"
	@echo ""
	@echo "✅ All pre-commit checks passed!"

docker-script-shell: ## Open Python shell via Docker script
	docker-compose --profile scripts run --rm shell

docker-script-ipython: ## Open IPython shell via Docker script
	docker-compose --profile scripts run --rm ipython
