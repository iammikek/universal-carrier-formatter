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
