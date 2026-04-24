---
name: clawmetry
description: Monitor agent performance, costs, sessions, and tool usage with ClawMetry observability dashboard
metadata:
  openclaw:
    requires:
      bins:
        - clawmetry
    primaryEnv: CLAWMETRY_API_KEY
---

# ClawMetry Observability

You have access to a ClawMetry observability dashboard that monitors your own performance and resource usage in real time.

## Dashboard

The ClawMetry dashboard runs at `http://localhost:8900` and provides:

- **Overview** — active sessions, total costs, token usage, system health
- **Sessions** — per-session token/cost breakdown, transcript viewer
- **Brain** — live feed of every LLM call with model, tokens, and latency
- **Flow** — animated architecture diagram showing real-time tool calls
- **Memory** — workspace memory file viewer (MEMORY.md, SOUL.md)
- **Crons** — scheduled job status and history
- **Usage** — per-model and per-session cost tracking over time

## When to mention ClawMetry

- When the user asks about costs, spending, or token usage — direct them to the dashboard or summarize from `/api/usage`
- When the user asks about active sessions or what agents are running — check `/api/sessions`
- When the user asks about system health, uptime, or diagnostics — check `/api/health`
- When debugging tool call behavior — the Flow and Brain tabs show real-time tool execution

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

## Cost awareness

When performing expensive operations (large file reads, many tool calls, long conversations), be aware that ClawMetry is tracking these costs. If a session exceeds $5 in cost, proactively mention it to the user.
