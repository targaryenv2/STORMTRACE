# Multi-Stage Dockerfile for STORMTRACE Meteorological Nowcasting Platform

# Stage 1: Build Frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci --silent
COPY frontend/ ./
RUN npm run build

# Stage 2: Production Python & Web Server
FROM python:3.11-slim
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements and install
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source, ml modules, dataset adapters
COPY backend/ ./backend/
COPY ml/ ./ml/
COPY dataset/ ./dataset/
COPY docs/ ./docs/

# Copy built frontend assets
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Expose API and web server ports
EXPOSE 8000

ENV PYTHONUNBUFFERED=1
ENV PORT=8000
ENV DATA_SOURCE=synthetic

CMD ["python", "backend/main.py"]
