# Backend Dockerfile for eCademy FastAPI app
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code with correct ownership
COPY --chown=appuser:appuser app/ ./app/
COPY --chown=appuser:appuser config/ ./config/
COPY --chown=appuser:appuser scripts/ ./scripts/
COPY --chown=appuser:appuser static/ ./static/
COPY --chown=appuser:appuser web/dist/ ./web/dist/

# Switch to non-root user
USER appuser

# Expose port for FastAPI
EXPOSE 8000

# Run uvicorn server (production mode, multiple workers)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
