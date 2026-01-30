#!/bin/bash
# setup.sh - Initial project setup script

set -e  # Exit on error

echo "🚀 Setting up Universal Carrier Formatter..."

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✓ Found Python $PYTHON_VERSION"

# Create virtual environment
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source .venv/bin/activate

# Install dependencies (single source: pyproject.toml + uv.lock)
echo "📥 Installing dependencies..."
if command -v uv &> /dev/null; then
    uv sync --extra dev
else
    (python3 -m uv sync --extra dev 2>/dev/null) || {
        echo "Installing uv (recommended) or use: pip install -e '.[dev]'"
        pip install --upgrade pip --quiet
        pip install uv --quiet && uv sync --extra dev
    }
fi

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your API keys!"
else
    echo "✓ .env file already exists"
fi

# Run initial test
echo "🧪 Running initial tests..."
pytest tests/test_basic.py -v

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Activate virtual environment: source .venv/bin/activate"
echo "  2. Edit .env and add your API keys"
echo "  3. Run tests: make test"
echo "  4. Start coding!"
echo ""
