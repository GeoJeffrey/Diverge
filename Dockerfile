# Backend Dockerfile for Diverge API (FastAPI)
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH="/app/src"

WORKDIR /app

# Install system runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt pyproject.toml ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code and docs
COPY src/ ./src/
COPY docs/ ./docs/
COPY migrations/ ./migrations/
COPY alembic.ini run_server.py ./

# Expose port (default 8000; dynamically overridden by Railway's $PORT)
EXPOSE 8000

# Default command: run migrations and launch uvicorn via run_server.py
CMD ["sh", "-c", "alembic upgrade head && python run_server.py --host 0.0.0.0 --port ${PORT:-8000}"]
