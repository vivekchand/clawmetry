# Cloud Testing Guide

Run the OpenClaw Dashboard on a remote server and access it from anywhere.

---

## Option 1: VPS / Cloud VM (Recommended)

Any Linux VM works: DigitalOcean, Hetzner, AWS EC2, GCP Compute Engine, etc.

### 1. Install

```bash
pip install clawmetry
```

### 2. Point to your OpenClaw workspace

If OpenClaw runs on the same machine, the dashboard auto-detects everything:

```bash
clawmetry --host 0.0.0.0 --port 8900
```

If your OpenClaw workspace is on a different machine, mount or sync it, then:

```bash
clawmetry --host 0.0.0.0 --workspace /path/to/openclaw/agent
```

### 3. Secure access

**SSH tunnel (simplest):**

```bash
# From your laptop:
ssh -L 8900:localhost:8900 user@your-server
# Then open http://localhost:8900
```

**Reverse proxy (production):**

Use nginx or Caddy with HTTPS and basic auth:

```nginx
# /etc/nginx/sites-available/dashboard
server {
    listen 443 ssl;
    server_name dashboard.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/dashboard.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/dashboard.yourdomain.com/privkey.pem;

    # SSE needs long timeouts
    proxy_read_timeout 600s;
    proxy_buffering off;

    location / {
        auth_basic "Dashboard";
        auth_basic_user_file /etc/nginx/.htpasswd;
        proxy_pass http://127.0.0.1:8900;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Or with Caddy (auto-HTTPS):

```
dashboard.yourdomain.com {
    basicauth * {
        admin $2a$14$... # caddy hash-password
    }
    reverse_proxy localhost:8900
}
```

---

## Option 2: Google Cloud Run (Serverless)

Ideal if your OpenClaw metrics are sent via OTLP. Note: Cloud Run is stateless, so file-based features (logs, transcripts, memory) won't work unless you mount a volume.

### 1. Create a Dockerfile

```dockerfile
FROM python:3.12-slim
RUN pip install clawmetry[otel]
EXPOSE 8900
CMD ["clawmetry", "--host", "0.0.0.0", "--port", "8900", "--no-debug"]
```

### 2. Deploy

```bash
gcloud run deploy clawmetry \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8900 \
  --memory 512Mi
```

### 3. Send OTLP data

Point your OpenClaw config at the Cloud Run URL:

```yaml
diagnostics:
  otel:
    endpoint: https://clawmetry-xxxxx.run.app
```

The Usage tab and health checks will work. For full features, use a VM with the workspace mounted.

---

## Option 3: Docker (Anywhere)

```bash
docker run -d \
  --name clawmetry \
  -p 8900:8900 \
  -v /path/to/openclaw/agent:/workspace \
  python:3.12-slim \
  bash -c "pip install clawmetry && clawmetry --host 0.0.0.0 --workspace /workspace --no-debug"
```

For a proper image, create a Dockerfile:

```dockerfile
FROM python:3.12-slim
RUN pip install clawmetry[otel]
EXPOSE 8900
ENTRYPOINT ["clawmetry"]
CMD ["--host", "0.0.0.0", "--no-debug"]
```

```bash
docker build -t clawmetry .
docker run -d -p 8900:8900 -v ~/openclaw-agent:/workspace clawmetry --workspace /workspace
```

---

## Option 4: Railway / Render / Fly.io

These platforms support Docker or Python buildpacks.

**Railway:**
```bash
# railway.json
{
  "build": { "builder": "NIXPACKS" },
  "deploy": {
    "startCommand": "pip install clawmetry[otel] && clawmetry --host 0.0.0.0 --port $PORT --no-debug"
  }
}
```

**Fly.io:**
```bash
fly launch --image python:3.12-slim
# Then use the Dockerfile approach above
```

---

## OTLP-Only Mode (Metrics Without Workspace)

If you just want cost/token dashboards without local file access, the dashboard works in "OTLP-only" mode:

```bash
clawmetry --host 0.0.0.0 --no-debug
# No workspace needed - just send OTLP data to it
```

Configure OpenClaw to send metrics:

```yaml
diagnostics:
  otel:
    endpoint: http://your-dashboard-host:8900
```

You'll get: Usage tab (tokens, costs, model breakdown), health checks, and the Flow visualization. Tabs that need local files (Logs, Memory, Transcripts) will show empty states gracefully.

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| SSE streams disconnect | Set `proxy_read_timeout 600s` and `proxy_buffering off` in nginx |
| Empty tabs on Cloud Run | Expected - mount a volume or use OTLP-only mode |
| Port already in use | `--port 9000` or `OPENCLAW_DASHBOARD_PORT=9000` |
| High memory on long runs | Metrics auto-cap at ~10K entries per category. Use `--metrics-file` to persist across restarts |
