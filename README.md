# 🦞 OpenClaw Dashboard

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://img.shields.io/pypi/v/openclaw-dashboard)](https://pypi.org/project/openclaw-dashboard/)
[![GitHub issues](https://img.shields.io/github/issues/vivekchand/openclaw-dashboard)](https://github.com/vivekchand/openclaw-dashboard/issues)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/openclaw-dashboard)](https://github.com/vivekchand/openclaw-dashboard/stargazers)

**See your agent think.** The Grafana for your personal AI agent.

Real-time observability dashboard for [OpenClaw/Moltbot](https://github.com/openclaw/openclaw) AI agents. **One file. Zero config. Just run it.**

![Flow Visualization](https://raw.githubusercontent.com/vivekchand/openclaw-dashboard/main/screenshots/flow.jpg)

## 🎬 Latest Demo Video

<video src="https://raw.githubusercontent.com/vivekchand/openclaw-dashboard/main/clawmetry-landing/videos/clawmetry.webm" controls muted loop playsinline width="100%"></video>

If the embedded player does not render on your GitHub view, open the video directly:
[clawmetry-landing/videos/clawmetry.webm](https://raw.githubusercontent.com/vivekchand/openclaw-dashboard/main/clawmetry-landing/videos/clawmetry.webm)

> 🌟 **[Star this repo](https://github.com/vivekchand/openclaw-dashboard)** if you find it useful!

---

## ⚡ **Quick Start** (30 seconds)

### Install & run:
```bash
pip install openclaw-dashboard
openclaw-dashboard
```

### Or download & run:
```bash
curl -O https://raw.githubusercontent.com/vivekchand/openclaw-dashboard/main/dashboard.py
pip install flask
python3 dashboard.py
```

🎉 **Done!** Opens at **http://localhost:8900** — auto-detects your OpenClaw workspace.

---

## ✨ Features

| Tab | What it shows |
|-----|--------------|
| **🌊 Flow** | **Real-time animated SVG** showing data flow: You → Channels → Gateway → Brain → Tools → Infrastructure |
| **Overview** | Model, sessions, crons, tokens, memory, **❤️ health checks** (auto-refresh via SSE), **🔥 activity heatmap** (GitHub-style), recent logs |
| **📊 Usage** | **Token/cost tracking** — bar chart of tokens per day (14 days), today/week/month totals, cost breakdown. **With OTLP**: real token counts, actual cost, avg run duration, messages processed, model breakdown |
| **Sessions** | All active agent sessions with model, channel, token usage, last activity |
| **Crons** | Scheduled jobs with status, schedule, last run, next run, duration |
| **Logs** | Parsed JSON logs with color-coded levels, configurable line count, **real-time SSE streaming** |
| **Memory** | Clickable file browser for SOUL.md, MEMORY.md, AGENTS.md, daily memory files |
| **📜 Transcripts** | **Session transcript viewer** — browse .jsonl files, click to see chat-bubble conversation view with color-coded roles, expand/collapse |

### Flow Visualization

The Flow tab is the star — a live animated architecture diagram that lights up in real-time as your agent processes messages:

- 🟣 **Purple particles** — your message entering through a channel
- 🔵 **Blue particles** — request flowing to the brain
- 🟡 **Yellow particles** — tool calls (exec, browser, search, cron, tts, memory)
- 🟢 **Green particles** — response flowing back to you
- 🔴 **Red flash** — errors
- 🔵 **Cyan pulses** — infrastructure layer activity (network, storage, runtime)

### New in v0.2: OTLP Receiver + Full Observability

- **📡 OTLP Receiver** — Dashboard becomes a lightweight OTel collector. Point OpenClaw at it, get real metrics. No Grafana/Prometheus needed.
- **🔥 Activity Heatmap** — GitHub-style 7×24 grid showing when your agent is busiest. Pure CSS, no libraries.
- **❤️ Health Checks** — Gateway, disk, memory, uptime, OTLP status at a glance. Auto-refreshes every 30s via SSE.
- **📊 Real Token/Cost Tracking** — With OTLP: real token counts, actual cost, model breakdown, avg run duration.
- **📜 Transcript Viewer** — Read your agent's conversations in a beautiful chat-bubble UI. Color-coded roles, expand/collapse for long messages.

---

## 🤔 What Makes This Different?

| | OpenClaw Dashboard | Langfuse | AgentOps |
|---|---|---|---|
| **Install** | `pip install openclaw-dashboard` | Docker + Postgres | SDK + cloud account |
| **Config** | Zero. Auto-detects everything. | Database URLs, API keys | API keys, SDK init |
| **Focus** | Personal AI agent | Enterprise LLM apps | Enterprise agent monitoring |
| **Memory-first** | ✅ Browse SOUL.md, MEMORY.md, daily notes | ❌ | ❌ |
| **Single file** | ✅ One Python file, one dependency | ❌ Multi-service | ❌ Cloud service |
| **Transcripts** | ✅ Chat-bubble viewer built-in | ✅ (needs SDK) | ✅ (needs SDK) |
| **Cost tracking** | ✅ Zero config (OTLP or log parsing) | ✅ (needs SDK) | ✅ (needs SDK) |
| **Built-in OTel collector** | ✅ OTLP/HTTP receiver | ❌ | ❌ |

**TL;DR:** Langfuse and AgentOps are great for teams building LLM products. OpenClaw Dashboard is for the person running a personal AI agent on their own machine — zero instrumentation, zero config, memory-first. It's the **Grafana for your personal AI agent**.

---

## 📡 Real-time Metrics (OpenTelemetry)

The dashboard can act as a **lightweight OpenTelemetry collector** — no need for Grafana, Prometheus, or a separate OTel Collector. Just point OpenClaw at the dashboard.

### Setup

**1. Install OTLP support:**

```bash
pip install openclaw-dashboard[otel]
```

**2. Configure OpenClaw** — add one line to your config:

```yaml
diagnostics:
  otel:
    endpoint: http://localhost:8900
```

That's it! The dashboard now receives real-time metrics directly from OpenClaw.

### What you get

| Metric | Source | What it shows |
|--------|--------|---------------|
| **Token counts** per day | `openclaw.tokens` | Real input/output/total token usage (bar chart) |
| **Cost** per day | `openclaw.cost.usd` | Actual cost from your provider |
| **Avg run duration** | `openclaw.run.duration_ms` | How long model completions take |
| **Messages processed** | `openclaw.message.processed` | Message throughput |
| **Model breakdown** | attributes | Which models are being used and how much |
| **OTLP Connected** indicator | health check | Green when data is flowing |

### OTLP Endpoints

- `POST /v1/metrics` — receives OTLP/HTTP protobuf metric data
- `POST /v1/traces` — receives OTLP/HTTP protobuf trace data

### Without OTLP

Everything still works! The dashboard falls back to parsing session JSONL files for token estimates. OTLP just gives you **real** numbers instead of estimates.

### Persistence

Metrics are stored in-memory (capped at ~10K entries per category, 14-day retention) and auto-persisted to `{workspace}/.openclaw-dashboard-metrics.json` every 60 seconds. Override the path with `--metrics-file` or `OPENCLAW_METRICS_FILE`.

---

## ⚙️ Configuration

### CLI Arguments

```bash
openclaw-dashboard --port 9000          # Custom port (default: 8900)
openclaw-dashboard --host 127.0.0.1     # Bind to localhost only
openclaw-dashboard --workspace ~/mybot  # Custom workspace path
openclaw-dashboard --log-dir /var/log   # Custom log directory
openclaw-dashboard --sessions-dir ~/data # Custom sessions directory
openclaw-dashboard --metrics-file ~/m.json # Custom metrics persistence path
openclaw-dashboard --name "Alice"       # Your name in Flow visualization
openclaw-dashboard --no-debug           # Disable auto-reload
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

### Security

- Default bind host is `127.0.0.1` (localhost only).
- To expose beyond localhost, set `--host 0.0.0.0` and place the dashboard behind your own network/auth controls.
- Development mode auto-reload is enabled by default. Use `--no-debug` for production-style runs.

### Auto-Detection

If no paths are configured, the dashboard automatically searches for:

1. **Workspace**: Checks `~/.clawdbot/agents/main/config.json` → `~/.clawdbot/workspace` → `~/clawd` → `~/openclaw` → current directory. Looks for `SOUL.md`, `AGENTS.md`, `MEMORY.md`, or `memory/` directory.
2. **Logs**: Checks `/tmp/moltbot` → `/tmp/openclaw` → `~/.clawdbot/logs`
3. **Sessions**: Reads from `~/.clawdbot/agents/main/sessions/`
4. **Crons**: Reads from `~/.clawdbot/cron/jobs.json`

---

## 🏗️ How It Works

The dashboard is a single-file Flask app that reads directly from your OpenClaw/Moltbot data directories:

```
Your Agent (Moltbot)          OpenClaw Dashboard
┌─────────────────┐          ┌─────────────────┐
│ Writes logs to   │─────────▶│ Reads & parses   │
│ /tmp/moltbot/    │          │ JSON log lines   │
│                  │          │                  │
│ Stores sessions  │─────────▶│ Lists sessions   │
│ in ~/.clawdbot/  │          │ with metadata    │
│                  │          │                  │
│ Saves crons to   │─────────▶│ Shows schedules  │
│ cron/jobs.json   │          │ and status       │
│                  │          │                  │
│ Agent workspace  │─────────▶│ Browses memory   │
│ SOUL.md, etc.    │          │ files inline     │
└─────────────────┘          └─────────────────┘
```

**Real-time streaming** uses `tail -f` piped through Server-Sent Events (SSE) — no WebSockets, no dependencies, just works.

---

## ☁️ Cloud & Remote Deployment

Want to run the dashboard on a VPS, Cloud Run, or Docker? See the **[Cloud Testing Guide](docs/CLOUD_TESTING.md)** for SSH tunnels, reverse proxy configs, Docker setups, and OTLP-only mode.

---

## 📦 Installation

### 🚀 **Option 1: pip (recommended)**
```bash
pip install openclaw-dashboard
openclaw-dashboard
```

### 🛠️ **Option 2: from source**
```bash
git clone https://github.com/vivekchand/openclaw-dashboard.git
cd openclaw-dashboard
pip install -r requirements.txt
python3 dashboard.py
```

### ⚡ **Option 3: one-liner**
```bash
curl -sSL https://raw.githubusercontent.com/vivekchand/openclaw-dashboard/main/install.sh | bash
```

All methods open the dashboard at **http://localhost:8900** and auto-detect your OpenClaw workspace.

---

## 🔧 Requirements

- **Python 3.8+**
- **Flask** (only required dependency)
- **opentelemetry-proto + protobuf** (optional, for OTLP receiver — `pip install openclaw-dashboard[otel]`)
- **OpenClaw/Moltbot** running on the same machine (reads its logs and state files)
- Linux/macOS (uses `tail`, `df`, `free`, `/proc/loadavg`)

---

## 📄 License

MIT — do whatever you want with it.

---

## 🙏 Credits

- Built by [Vivek Chand](https://linkedin.com/in/vivekchand46) as part of the OpenClaw ecosystem
- Powered by [OpenClaw/Moltbot](https://github.com/openclaw/openclaw)
- The Flow visualization was inspired by watching an AI agent actually think

---

<p align="center">
  <strong>🦞 See your agent think</strong><br>
  <sub>Star this repo if you find it useful!</sub>
</p>
