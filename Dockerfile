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

# OTLP protobuf support, baked in rather than left to the [otel] extra.
# This image is what deploy/self-hosted/docker-compose.yml builds, and the
# daemon-free intake path (an org points OTEL_EXPORTER_OTLP_ENDPOINT here
# instead of installing anything per machine) depends on it: OTLP/JSON
# decodes with the stdlib, but the default exporter protocol is
# http/protobuf, and without these the receiver answers 501 to every POST.
# An enterprise receiver that has to be told to `pip install clawmetry[otel]`
# before it accepts data is not a receiver.
RUN pip install --no-cache-dir "opentelemetry-proto>=1.20.0" "protobuf>=4.21.0"

# Copy application code and necessary files for setup
COPY dashboard.py .
COPY history.py .
COPY setup.py .
COPY README.md . 
COPY clawmetry/ ./clawmetry/
COPY helpers/ ./helpers/
COPY routes/ ./routes/

# Install clawmetry
RUN pip install --no-cache-dir -e .

# Create directories for OpenClaw integration
RUN mkdir -p /root/.openclaw /tmp/moltbot /app/.clawmetry

# Expose port
EXPOSE 8900

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8900/api/health')" || exit 1

# Default command
CMD ["clawmetry", "--host", "0.0.0.0", "--port", "8900"]
