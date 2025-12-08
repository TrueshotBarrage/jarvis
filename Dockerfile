# syntax=docker/dockerfile:1

# Jarvis AI Assistant - Docker Image
# Python 3.13+ with FastAPI server

FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install system dependencies for audio processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create db directory for SQLite
RUN mkdir -p db

# Set PYTHONPATH for package imports
ENV PYTHONPATH=/app/src

# Expose the FastAPI port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/test')" || exit 1

# Run the server
CMD ["uvicorn", "jarvis.heart:app", "--host", "0.0.0.0", "--port", "8000"]
