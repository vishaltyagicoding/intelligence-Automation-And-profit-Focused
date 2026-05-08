FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    postgresql-client \
    libpq-dev \
    build-essential \
    curl \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt && \
    rm -rf ~/.cache/pip

# Copy project files
COPY . .

# Create necessary directories
RUN mkdir -p logs staticfiles media models/production models/backups

# Make scripts executable
RUN chmod +x /app/scripts/*.sh && \
    chmod +x /app/scripts/start_server.sh

# Collect static files (ignore errors if not ready)
RUN python manage.py collectstatic --noinput 2>/dev/null || true

# Create necessary directories with proper permissions
RUN mkdir -p /app/logs /app/staticfiles /app/media /app/models/production /app/models/backups && \
    chmod -R 755 /app

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

CMD ["bash", "/app/scripts/start_server.sh"]
