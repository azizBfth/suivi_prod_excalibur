# Dockerfile for FastAPI Production Tracking Application
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for SQL Anywhere ODBC driver
RUN apt-get update && apt-get install -y \
    unixodbc \
    unixodbc-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories for templates and static files
RUN mkdir -p templates static

# Expose port
EXPOSE 80

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:80/api/health || exit 1

# Run the application with production settings
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80", "--workers", "1"]
