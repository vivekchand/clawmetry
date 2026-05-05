# Dockerfile for ClawMetry
# Quick start: docker build -t clawmetry . && docker run -p 8900:8900 clawmetry

FROM python:3.11-slim

LABEL maintainer="ClawMetry Contributors"
LABEL description="Real-time observability dashboard for OpenClaw AI agents"

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY dashboard.py .
COPY setup.py .
COPY README.md .
COPY clawmetry/ ./clawmetry/

# Install clawmetry
RUN pip install --no-cache-dir -e .

# Create directories for OpenClaw integration
RUN mkdir -p /root/.openclaw /tmp/moltbot

# Expose port
EXPOSE 8900

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8900/api/health')" || exit 1

# Default command
CMD ["clawmetry", "--host", "0.0.0.0", "--port", "8900"]
