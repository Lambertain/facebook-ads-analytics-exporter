# Multi-stage build for eCademy
# Stage 1: Build frontend
FROM node:18-alpine AS frontend-builder

WORKDIR /app/web

# Copy package files and install dependencies
COPY web/package*.json ./
RUN npm ci

# Copy frontend source and build
COPY web/ ./
RUN npm run build

# Stage 2: Python backend
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y     gcc     && rm -rf /var/lib/apt/lists/*

# Copy Python requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY app/ ./app/
COPY config/ ./config/

# Copy built frontend from stage 1
COPY --from=frontend-builder /app/web/dist ./web/dist

# Copy entrypoint script
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Create directory for database
RUN mkdir -p /app/data

# Expose port (Railway will override with $PORT)
EXPOSE 8000

# Use entrypoint script to handle PORT env var
ENTRYPOINT ["/app/entrypoint.sh"]
