# Multi-stage Dockerfile for LinkedIn Agent Analytics Platform
FROM python:3.11-slim AS base

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code and scripts
COPY . .

# Set environment defaults
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV ENVIRONMENT=production

# Initialize Database and seed dimensions
RUN python scripts/init_db.py

EXPOSE 8000

# Default command: run ingestion pipeline runner
CMD ["python", "scripts/run_pipeline.py"]
