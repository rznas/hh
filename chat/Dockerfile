# Multi-stage build for production deployment
FROM python:3.12-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH" \
    UV_COMPILE_BYTECODE=1

# Development stage
FROM base as development

COPY requirements-dev.txt .
RUN /root/.cargo/bin/uv pip install --system -r requirements-dev.txt

COPY . .

EXPOSE 8000

CMD ["chainlit", "run", "src/app.py", "--host", "0.0.0.0", "--port", "8000"]

# Production stage
FROM base as production

# Copy only production requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ /app/src/
COPY alembic/ /app/alembic/
COPY alembic.ini /app/
COPY .chainlit/ /app/.chainlit/

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["chainlit", "run", "src/app.py", "--host", "0.0.0.0", "--port", "8000"]
