# 🦞 ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**See your agent think.** Real-time observability for **29 AI agent runtimes**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex & 25 more. One dashboard for your whole agent fleet.

> 🌐 **Read this in:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [more →](docs/i18n/)

One command. Zero config. Auto-detects everything.

```bash
pip install clawmetry && clawmetry
```

Opens at **http://localhost:8900**. Zero config: it finds the agent runtimes
you already have, reads them read-only, and changes nothing about how they run.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## Works with 29 agent runtimes

**Free in the open source app:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**On a paid plan:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

Every runtime gets the same dashboard. Run several at once and the header
switcher re-scopes every tab to one of them.

Built your own agent on an SDK instead? The interceptor tracks its LLM calls
too. See [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## What you get

- **Sessions & transcripts**: what each agent did, turn by turn, with replay
- **Cost & tokens**: per runtime, model, session and day, with anomaly flags
- **Flow**: live diagram of messages moving through channels, models and tools
- **Brain**: the reasoning and tool-call event stream as it happens
- **Context blowout**: window utilization sized per provider, compaction vs forced overflow, plus a per-runtime map of what we *can't* see ([how](docs/CONTEXT_BLOWOUT.md))
- **Memory & skills**: the files and skills each runtime actually loaded
- **Health & logs**: disk, memory, error rates, rate limits, live log stream
- **Alerts**: budget caps, error spikes, agent-offline, routed to Slack, Discord, PagerDuty, Telegram, Email
- **Approvals**: pause risky tool calls *before* they run and approve from your phone ([how](docs/APPROVALS.md))

## Context blowout, and what watching costs

Two questions worth answering before you trust any agent-comparison tool.

**How does it handle context-window blowout across runtimes?**

A utilization percentage is only as honest as what it divides by. ClawMetry
sizes the window per provider from [a table you can read and
PR](clawmetry/context_windows.py), covering Anthropic, OpenAI, Google, xAI,
DeepSeek, Kimi, Qwen, Mistral, Llama and GLM. It does not measure all 26
runtimes with one vendor's ruler. That matters: a 300K GPT-5 turn scored
against Anthropic's 200K reads ">100%, blown" when it is really at 75% of
GPT-5's 400K. The same ruler hides a genuinely overflowed 130K DeepSeek turn
as a comfortable 65%.

Every window ships with its provenance: `model_table`, `explicit_marker`,
`observed_floor`, or an honest `default` when we don't know the model. A
gauge built on a guess never renders with the same authority as one built on
a lookup.

ClawMetry can only see compaction events on some runtimes. So
`GET /api/context-coverage` reports, per runtime, whether a **zero means
"ran clean" or "we're blind"**. A `0` that actually means blind says so.
[Full detail](docs/CONTEXT_BLOWOUT.md)

**What does the instrumentation cost?**

| Path | Added to your agent | Default? |
|---|---|---|
| Session-file tailing (all 29 runtimes) | **0**. Separate process, no ClawMetry code in your agent | on |
| HTTP interceptor (`CLAWMETRY_INTERCEPT=1`) | **+0.44 ms** per LLM call, or 0.009% of a 5s call | off |
| Pre-tool hook gate (warm cache) | **+44 ms** per gated tool call, over a 36 ms interpreter floor | off |
| Enforcement proxy | **+9.7 ms** per LLM call | off |

Daemon host cost: **2,762 events/sec** ingest, **710 bytes/event** on disk
(67.7 MB per 100k events), and **~12% of one core** sustained on a busy
install. That last number is over our own stated 5-10% budget, so it is
published as a bug to chase rather than left off the page.

Measured on an Apple M2 Pro with `benchmarks/overhead.py`. The harness runs
each condition in a separate process, alternates their order, and **refuses
to print a number when the rounds disagree on its sign**. Run it on your own
machine in a minute:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

Every path is measured, including the hook gates and the enforcement proxy,
and the harness runs on Linux, macOS and Windows in CI. Two results worth
knowing: the proxy costs about seven times more on Windows than on Linux, and
the daemon currently sustains about 12% of one core, over our own 5-10%
budget. The raw JSON, the method, and what is still unmeasured are in
[docs/OVERHEAD.md](docs/OVERHEAD.md).

## Pricing

| Plan | What it covers | Price |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose, full dashboard, local only | $0 |
| **Starter** | Every other runtime above, fleet view, cloud sync | $9 per node / month |
| **Pro** | Starter + control and evaluation: approvals, tool-risk policies, evals, anomaly detection, cost optimizer, OTel export, tamper-evident audit log | $19 per node / month |

Annual plans, Enterprise and the current numbers live at
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. Self-hosted license
keys work without the cloud (`clawmetry license`). The exact free/paid split is
in [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## Your data stays on your machine

ClawMetry reads local session files and logs. **No session data leaves your box
unless you run `clawmetry connect`** — no prompts, replies, tool arguments, file
contents or log lines. When you do connect, the snapshot is end-to-end encrypted
with a key that never leaves your machine, and decrypted in your browser. If a
node has no key, the upload is skipped rather than sent in the clear, and no
server response can turn that off.

Two things do run by default before you connect, both opt-out and neither
carrying session data: an anonymous install ping and a version check against
PyPI. A default install also looks up your public IP once for a startup banner
line. Every destination, what it carries and how to switch it off is listed in
[docs/EGRESS.md](docs/EGRESS.md); self-hosted, repointed and air-gapped installs
make no discretionary outbound calls at all.

The decryption happens in your browser, in code we serve you. That used to be
a promise; it is now something you can check. Every line that touches your key
lives in one readable file, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js),
which ships inside the wheel and is served verbatim, pinned with a Subresource
Integrity hash. To confirm the browser runs what we published:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

What that does not prove: we serve the page that loads the file, so we could
serve a different page. Integrity hashes protect you from a compromised CDN,
not from the vendor. What you gain is that any substitution has to be
deliberate, visible in the page source, and different from an artifact on PyPI
that anyone can fetch. Self-hosting or staying local-only removes the
dependency entirely.

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
| [Context blowout](docs/CONTEXT_BLOWOUT.md) | Per-provider windows, compaction vs overflow, per-runtime coverage |
| [Overhead](docs/OVERHEAD.md) | What instrumentation costs, measured, with the harness to reproduce it |
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

**It shows you where the money went, in every window.**
$252.47 today, $513.15 this week, $1,312.92 this month, each with the tokens
behind it and how much of it your subscription already covers. Below that,
about $1,128/mo itemised as recoverable and $17,256/mo already saved by
cache reuse.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**It draws how a message becomes an answer.**
The live flow diagram: you, the channel it arrived on, the gateway, the model
answering right now, and every tool it reached for. Nodes light up as work
moves through them.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**Every agent on the machine, in one table.**
What it runs, what it costs in the last 24 hours and over its lifetime, when
it was last seen, who owns it, and whether a subscription is covering the
bill. 14 agents here, 3 sessions working, 13 quiet.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**It shows where a turn's time and money went, tool by tool.**
One turn of a real session: 11 tools in 11.2 minutes for $1.16. Every Bash
call and model call gets its own bar on the timeline, so the command that ran
for 4.1 minutes and the one that ran for 226ms are told apart at a glance.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**It grades the work, not just the spend.**
An A this week: 54 tasks came back clean, 2 rough ones cost $48.57, and the
runs with too little activity to judge are left out of the grade instead of
being counted as wins. Each rough run links to its trace.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**It shows why the context window keeps filling up.**
715K of a 1M-token window on the latest turn, an 83.3% peak, 4 compactions
that all fired proactively rather than on an overflow, and the utilisation of
every turn behind it.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**Detection runs without you configuring anything.**
The built-in detectors are on from install: agent went quiet, telemetry feed
stopped, cost spike, token burst, errors climbing, error spike, budget
threshold, threat signature matched, security tool finding, security posture
changed. Your own rules are optional on top.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**Holding a risky call is opt-in, and ships off.**
Recursive deletes, force pushes, sudo, secrets, package installs and outbound
calls each get a rule you can turn on. Until you do, ClawMetry watches and
changes nothing. Once one is on, matching calls wait here (or on your phone)
for an approve or a deny.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

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
