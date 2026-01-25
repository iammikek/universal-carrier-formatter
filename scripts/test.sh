#!/bin/bash
# test.sh - Run pytest tests in Docker container
# Usage: ./scripts/test.sh [pytest-args...]

set -e

# Change to project root directory
cd "$(dirname "$0")/.."

# Run pytest in Docker container
# Pass any additional arguments to pytest
docker-compose exec app pytest tests/ -v "$@"
