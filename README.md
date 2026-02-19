# 🦞 ClawMetry

[![PyPI](https://img.shields.io/pypi/v/clawmetry)](https://pypi.org/project/clawmetry/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry)](https://github.com/vivekchand/clawmetry/stargazers)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**See your agent think.** Real-time observability for [OpenClaw](https://github.com/openclaw/openclaw) AI agents.

One command. Zero config. Auto-detects everything.

```bash
pip install clawmetry && clawmetry
```

Opens at **http://localhost:8900** and you're done.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## What You Get

- **Flow** — Live animated diagram showing messages flowing through channels, brain, tools, and back
- **Overview** — Health checks, activity heatmap, session counts, model info
- **Usage** — Token and cost tracking with daily/weekly/monthly breakdowns
- **Sessions** — Active agent sessions with model, tokens, last activity
- **Crons** — Scheduled jobs with status, next run, duration
- **Logs** — Color-coded real-time log streaming
- **Memory** — Browse SOUL.md, MEMORY.md, AGENTS.md, daily notes
- **Transcripts** — Chat-bubble UI for reading session histories

## Screenshots

| Flow | Overview | Sub-Agent |
|------|----------|-----------|
| ![Flow](https://clawmetry.com/screenshots/flow.png) | ![Overview](https://clawmetry.com/screenshots/overview.png) | ![Sub-Agent](https://clawmetry.com/screenshots/subagent.png) |

| Summary | Crons | Memory |
|---------|-------|--------|
| ![Summary](https://clawmetry.com/screenshots/summary.png) | ![Crons](https://clawmetry.com/screenshots/crons.png) | ![Memory](https://clawmetry.com/screenshots/memory.png) |

## Install

**pip (recommended):**
```bash
pip install clawmetry
clawmetry
```

**One-liner:**
```bash
curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash
```

**From source:**
```bash
git clone https://github.com/vivekchand/clawmetry.git
cd clawmetry && pip install flask && python3 dashboard.py
```

## Configuration

Most people don't need any config. ClawMetry auto-detects your workspace, logs, sessions, and crons.

If you do need to customize:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

All options: `clawmetry --help`

## Requirements

- Python 3.8+
- Flask (installed automatically via pip)
- OpenClaw running on the same machine
- Linux or macOS

## Cloud Deployment

See the **[Cloud Testing Guide](docs/CLOUD_TESTING.md)** for SSH tunnels, reverse proxy, and Docker.

## License

MIT

---

<p align="center">
  <strong>🦞 See your agent think</strong><br>
  <sub>Built by <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · Part of the <a href="https://github.com/openclaw/openclaw">OpenClaw</a> ecosystem</sub>
</p>
