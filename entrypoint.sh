#!/bin/sh
# Entrypoint script for Railway deployment
# Reads PORT from environment variable

PORT=${PORT:-8000}
echo "Starting uvicorn on port $PORT"
exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
