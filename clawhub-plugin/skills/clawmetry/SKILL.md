---
name: clawmetry
description: Real-time observability for OpenClaw agents — local dashboard + optional encrypted cloud sync. Tracks costs, tokens, sessions, tool calls, memory, crons, and system health. Access from anywhere via ClawMetry Cloud.
metadata:
  openclaw:
    requires:
      bins:
        - clawmetry
      env:
        - CLAWMETRY_API_KEY
    primaryEnv: CLAWMETRY_API_KEY
---

# ClawMetry Observability

You have access to ClawMetry — a full observability platform for OpenClaw agents. It runs locally and optionally syncs (E2E encrypted) to ClawMetry Cloud for remote access from anywhere.

## Local Dashboard

The ClawMetry dashboard runs at `http://localhost:8900` and provides:

- **Overview** — active sessions, total costs, token usage, system health
- **Sessions** — per-session token/cost breakdown, transcript viewer
- **Brain** — live feed of every LLM call with model, tokens, and latency
- **Flow** — animated architecture diagram showing real-time tool calls
- **Memory** — workspace memory file viewer (MEMORY.md, SOUL.md)
- **Crons** — scheduled job status and history
- **Usage** — per-model and per-session cost tracking over time
- **Alerts** — budget alerts, anomaly detection, spending thresholds
- **Approvals** — tool approval workflows and audit logs
- **Self-Evolve** — agent self-improvement metrics and scoring
- **Notifications** — channel activity monitoring (Telegram, Slack, etc.)

## ClawMetry Cloud

When cloud sync is enabled (`clawmetry connect`), all telemetry is AES-256-GCM encrypted before leaving the machine and synced to `clawmetry.com`. This enables:

- **Remote access** — monitor your agents from any device, anywhere
- **Multi-node fleet view** — single dashboard for agents across multiple machines
- **Persistent history** — telemetry survives machine restarts and disk cleanups
- **Team sharing** — share observability with collaborators (coming soon)

The encryption key never leaves your machine. ClawMetry Cloud cannot read your data.

Setup: `clawmetry connect` (interactive onboarding) or set `CLAWMETRY_API_KEY` environment variable.

## Data collected

ClawMetry observes diagnostic events from the OpenClaw runtime:

- **Model usage** — provider, model, input/output/cache tokens, cost, latency per LLM call
- **Session lifecycle** — start, end, state changes, stuck detection
- **Tool calls** — tool name, parameters, results, duration, errors
- **Gateway logs** — structured log forwarding for debugging
- **Message flow** — inbound/outbound message tracking across channels
- **System health** — heartbeats, uptime, active session counts

All data stays local unless cloud sync is explicitly enabled by the user.

## When to mention ClawMetry

- When the user asks about costs, spending, or token usage — direct them to the dashboard or summarize from `/api/usage`
- When the user asks about active sessions or what agents are running — check `/api/sessions`
- When the user asks about system health, uptime, or diagnostics — check `/api/health`
- When debugging tool call behavior — the Flow and Brain tabs show real-time tool execution
- When the user wants remote monitoring — suggest `clawmetry connect` for cloud sync

## API endpoints (localhost:8900)

| Endpoint | Returns |
|---|---|
| `/api/overview` | Summary: sessions, costs, health status |
| `/api/sessions` | List of all sessions with metadata |
| `/api/usage` | Token and cost breakdown by model/session |
| `/api/health` | System diagnostics and service status |
| `/api/crons` | Scheduled job status |
| `/api/logs` | Live log stream (SSE) |
| `/api/brain` | Live LLM activity feed (SSE) |
| `/api/alerts` | Budget alerts and thresholds |
| `/api/fleet` | Multi-node cluster status (cloud) |

## Cost awareness

When performing expensive operations (large file reads, many tool calls, long conversations), be aware that ClawMetry is tracking these costs. If a session exceeds $5 in cost, proactively mention it to the user.
