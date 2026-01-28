# Development Dockerfile
# Multi-stage build for Python development

FROM python:3.11-slim as base

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better caching)
COPY requirements.txt requirements-dev.txt ./

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements-dev.txt

# Copy application code
COPY . .

# Development stage
FROM base as development

# Install pytest and test deps (for running tests in container)
RUN pip install pytest pytest-cov pytest-mock

# Install development tools
RUN pip install ipython ipdb

# Set default command (can be overridden)
CMD ["pytest"]

# Production stage (for future use)
FROM base as production

# Only install production dependencies
RUN pip install -r requirements.txt

# Run as non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

CMD ["python", "-m", "src.formatter"]
