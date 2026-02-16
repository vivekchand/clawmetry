# 🦞 ClawMetry

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry)](https://pypi.org/project/clawmetry/)
[![GitHub issues](https://img.shields.io/github/issues/vivekchand/openclaw-dashboard)](https://github.com/vivekchand/openclaw-dashboard/issues)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/openclaw-dashboard)](https://github.com/vivekchand/openclaw-dashboard/stargazers)

**See your agent think.** The Grafana for your personal AI agent.

Real-time observability dashboard for [OpenClaw](https://github.com/openclaw/openclaw) AI agents. One file. Zero config. Just run it.

> *Previously published as `openclaw-dashboard` — same project, better name.*

![Flow Visualization](https://raw.githubusercontent.com/vivekchand/openclaw-dashboard/main/screenshots/flow.png)

## 🎬 Demo

<video src="https://raw.githubusercontent.com/vivekchand/openclaw-dashboard/main/clawmetry-landing/videos/clawmetry.webm" controls muted loop playsinline width="100%"></video>

[▶ Watch video directly](https://raw.githubusercontent.com/vivekchand/openclaw-dashboard/main/clawmetry-landing/videos/clawmetry.webm)

> 🌟 **[Star this repo](https://github.com/vivekchand/openclaw-dashboard)** if you find it useful!

---

## ⚡ Quick Start (30 seconds)

```bash
pip install clawmetry
clawmetry
```

🎉 Opens at **http://localhost:8900** — auto-detects your OpenClaw workspace.

### Alternative: run from source

```bash
curl -O https://raw.githubusercontent.com/vivekchand/openclaw-dashboard/main/dashboard.py
pip install flask
python3 dashboard.py
```

---

## 📸 Screenshots

| Overview | Flow | Usage |
|----------|------|-------|
| ![Overview](screenshots/overview.png) | ![Flow](screenshots/flow.png) | ![Usage](screenshots/usage.png) |

| Sessions | Logs | Memory |
|----------|------|--------|
| ![Sessions](screenshots/sessions.png) | ![Logs](screenshots/logs.png) | ![Memory](screenshots/memory.png) |

| Crons | Transcripts |
|-------|-------------|
| ![Crons](screenshots/crons.png) | ![Transcripts](screenshots/transcripts.png) |

---

## ✨ Features

| Tab | What it shows |
|-----|--------------|
| **🌊 Flow** | **Real-time animated SVG** — data flow from You → Channels → Gateway → Brain → Tools → Infrastructure |
| **Overview** | Model, sessions, crons, tokens, memory, **❤️ health checks** (auto-refresh via SSE), **🔥 activity heatmap** (GitHub-style) |
| **📊 Usage** | **Token/cost tracking** — bar charts, daily/weekly/monthly totals, model breakdown. With OTLP: real token counts & actual cost |
| **Sessions** | Active agent sessions with model, channel, token usage, last activity |
| **Crons** | Scheduled jobs with status, schedule, last/next run, duration |
| **Logs** | Color-coded JSON logs with **real-time SSE streaming** |
| **Memory** | Clickable file browser for SOUL.md, MEMORY.md, AGENTS.md, daily notes |
| **📜 Transcripts** | Session transcript viewer — chat-bubble UI with color-coded roles |

### 🌊 Flow Visualization

The star feature — a live animated architecture diagram that lights up as your agent processes messages:

- 🟣 **Purple** — your message entering through a channel
- 🔵 **Blue** — request flowing to the brain
- 🟡 **Yellow** — tool calls (exec, browser, search, cron, tts, memory)
- 🟢 **Green** — response flowing back
- 🔴 **Red** — errors
- 🔵 **Cyan** — infrastructure activity

### 📡 Built-in OpenTelemetry Collector

No Grafana or Prometheus needed. Point OpenClaw at the dashboard:

```yaml
diagnostics:
  otel:
    endpoint: http://localhost:8900
```

Install OTLP support: `pip install clawmetry[otel]`

---

## 🤔 Why ClawMetry?

| | ClawMetry | Langfuse | AgentOps |
|---|---|---|---|
| **Install** | `pip install clawmetry` | Docker + Postgres | SDK + cloud account |
| **Config** | Zero. Auto-detects everything. | Database URLs, API keys | API keys, SDK init |
| **Focus** | Personal AI agent | Enterprise LLM apps | Enterprise agent monitoring |
| **Memory browser** | ✅ SOUL.md, MEMORY.md, daily notes | ❌ | ❌ |
| **Single file** | ✅ One Python file | ❌ Multi-service | ❌ Cloud service |
| **Built-in OTel** | ✅ OTLP/HTTP receiver | ❌ | ❌ |

---

## ⚙️ Configuration

### CLI

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --log-dir /var/log       # Custom log directory
clawmetry --sessions-dir ~/data    # Custom sessions directory
clawmetry --metrics-file ~/m.json  # Custom metrics persistence path
clawmetry --name "Alice"           # Your name in Flow visualization
clawmetry --no-debug               # Disable auto-reload
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENCLAW_HOME` | Agent workspace directory | Auto-detected |
| `OPENCLAW_WORKSPACE` | Alternative to OPENCLAW_HOME | Auto-detected |
| `OPENCLAW_SESSIONS_DIR` | Sessions directory (.jsonl transcripts) | Auto-detected |
| `OPENCLAW_LOG_DIR` | Log directory | `/tmp/moltbot` |
| `OPENCLAW_METRICS_FILE` | Metrics persistence file path | `{workspace}/.openclaw-dashboard-metrics.json` |
| `OPENCLAW_USER` | Your name in Flow tab | `You` |
| `OPENCLAW_SSE_MAX_SECONDS` | Max duration per SSE stream | `300` |

### Auto-Detection

No config needed — the dashboard searches for your workspace, logs, sessions, and crons automatically.

---

## 📦 Installation

### pip (recommended)
```bash
pip install clawmetry
clawmetry
```

### From source
```bash
git clone https://github.com/vivekchand/openclaw-dashboard.git
cd openclaw-dashboard
pip install -r requirements.txt
python3 dashboard.py
```

### One-liner
```bash
curl -sSL https://raw.githubusercontent.com/vivekchand/openclaw-dashboard/main/install.sh | bash
```

---

## 🔧 Requirements

- **Python 3.8+**
- **Flask** (only required dependency)
- **opentelemetry-proto + protobuf** (optional — `pip install clawmetry[otel]`)
- **OpenClaw/Moltbot** running on the same machine
- Linux/macOS

---

## ☁️ Cloud Deployment

See the **[Cloud Testing Guide](docs/CLOUD_TESTING.md)** for SSH tunnels, reverse proxy, Docker, and OTLP-only mode.

---

## 📄 License

MIT

---

<p align="center">
  <strong>🦞 See your agent think</strong><br>
  <sub>Built by <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://linkedin.com/in/vivekchand">LinkedIn</a> · Part of the <a href="https://github.com/openclaw/openclaw">OpenClaw</a> ecosystem</sub>
</p>
