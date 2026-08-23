# 🦞 ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**See your agent think.** Real-time observability for **26 AI agent runtimes**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex & 22 more. One dashboard for your whole agent fleet.

> 🌐 **Read this in:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [more →](docs/i18n/)

One command. Zero config. Auto-detects everything.

```bash
pip install clawmetry && clawmetry
```

Opens at **http://localhost:8900**. Zero config: it finds the agent runtimes
you already have, reads them read-only, and changes nothing about how they run.

![ClawMetry catching a spending anomaly and a stalled agent live](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

## Works with 26 agent runtimes

**Free in the open source app:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**On a paid plan:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok](https://clawmetry.com/runtimes/grok)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

Every runtime gets the same dashboard. Run several at once and the header
switcher re-scopes every tab to one of them.

Built your own agent on an SDK instead? The interceptor tracks its LLM calls
too. See [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## What you get

- **Sessions & transcripts**: what each agent did, turn by turn, with replay
- **Cost & tokens**: per runtime, model, session and day, with anomaly flags
- **Flow**: live diagram of messages moving through channels, models and tools
- **Brain**: the reasoning and tool-call event stream as it happens
- **Memory & skills**: the files and skills each runtime actually loaded
- **Health & logs**: disk, memory, error rates, rate limits, live log stream
- **Alerts**: budget caps, error spikes, agent-offline, routed to Slack, Discord, PagerDuty, Telegram, Email
- **Approvals**: pause risky tool calls *before* they run and approve from your phone ([how](docs/APPROVALS.md))

## Pricing

| Plan | What it covers | Price |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose, full dashboard, local only | $0 |
| **Starter** | Every other runtime above, fleet view, cloud sync | $9 per node / month |
| **Pro** | Starter + governance: approvals, tool-risk policies, evals, anomaly detection, cost optimizer, OTel export | $19 per node / month |

Annual plans, Enterprise and the current numbers live at
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. Self-hosted license
keys work without the cloud (`clawmetry license`). The exact free/paid split is
in [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## Your data stays on your machine

ClawMetry reads local session files and logs. Nothing leaves your box unless
you run `clawmetry connect`. Even then the snapshot is end-to-end encrypted
with a key that never leaves your machine, and decrypted in your browser.

## Install

```bash
pip install clawmetry     # then: clawmetry
```

Or the one-liner: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

Needs Python 3.8+ on macOS, Linux or Windows, and at least one agent runtime on
the same machine. Docker instructions: [docs/DOCKER.md](docs/DOCKER.md).

## Docs

| | |
|---|---|
| [Runtime compatibility](docs/compatibility.md) | What each adapter reads, and how to add a runtime |
| [Entitlements](docs/ENTITLEMENTS.md) | Free vs paid, tier matrix, license CLI |
| [Approvals & policies](docs/APPROVALS.md) | Pre-execution gating, risk scoring, phone approvals |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | Export traces anywhere, ingest OTLP from anything |
| [SDK tracking](docs/SDK_TRACKING.md) | Cost attribution for agents you built yourself |
| [Chat channels](docs/CHANNELS.md) | The chat adapters shown in Flow |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Sandboxed NVIDIA NemoClaw setups |
| [Docker](docs/DOCKER.md) | Image, compose, volume mounts |
| [Architecture](ARCHITECTURE.md) · [Development](docs/DEVELOPMENT.md) | How it works inside; running from source |
| [Telemetry](docs/TELEMETRY.md) | The anonymous install and desktop-open pings, and how to turn them off |

## Screenshots

Every number below is from one real machine, read-only, with nothing seeded.

**It tells you when something is wrong, not just what happened.**
Two anomaly banners at the top: spend running 7x the daily average, and a
4.2x cost spike. Below them, 324 of 667 recent sessions carrying a waste
signal, itemised by cause.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**It shows you the money you can get back.**
$4,058.92 spent this month, about $3,668/mo of it itemised as recoverable
(trim long conversations, route short tasks to a smaller model, trim
thinking), and $35,572/mo already saved by cache reuse.

![Cost: efficiency grade B with itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**It shows every step, across every runtime.**
Messages, reasoning, tool calls and their results, streaming live, filterable
by runtime and by event type.

![Activity: live unified event stream across runtimes](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

**Detection runs without you configuring anything.**
The built-in detectors are on from install: agent went quiet, telemetry feed
stopped, cost spike, stalled session, repeated tool failure. Your own rules
are optional on top.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

More, per runtime: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## Star History

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## License

MIT · Built by [@vivekchand](https://github.com/vivekchand) · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
