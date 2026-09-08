# Docker

Want to run ClawMetry in a container? No problem! 🐳

**Quick start with Docker:**

```bash
# Build the image
docker build -t clawmetry .

# Run with default settings
docker run -p 8900:8900 clawmetry

# Or mount your agent's data dir (shown: OpenClaw's ~/.openclaw)
docker run -p 8900:8900 \
  -v ~/.openclaw:/root/.openclaw \
  -v /tmp/moltbot:/tmp/moltbot \
  clawmetry
```

**Docker Compose example:**

```yaml
version: '3.8'
services:
  clawmetry:
    build: .
    ports:
      - "8900:8900"
    volumes:
      - ~/.openclaw:/root/.openclaw:ro
      - /tmp/moltbot:/tmp/moltbot:ro
    restart: unless-stopped
```

> **Note:** When running in Docker, mount your agent's data + log directories (e.g. `~/.openclaw`, `~/.claude`, `~/.codex`) so ClawMetry can auto-detect your setup.

Requirements and CLI options: [DEVELOPMENT.md](DEVELOPMENT.md).
