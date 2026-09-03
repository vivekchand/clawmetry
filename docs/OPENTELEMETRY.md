# OpenTelemetry

ClawMetry speaks **OpenTelemetry** in both directions, using the **GenAI semantic conventions**, so your agent traces are never locked into one tool.

**Export** every session — LLM calls, tools, sub-agents, tokens, cost — as OTLP/HTTP GenAI spans to any collector (Datadog, Grafana, Honeycomb, or your own OTel Collector):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Auth headers and poll interval are optional env vars:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**Ingest** — the built-in OTLP receiver accepts traces, logs, and metrics from anything else at `/v1/traces`, `/v1/logs`, and `/v1/metrics`. Point any OpenTelemetry-instrumented app at it:

```bash
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:8900 OTEL_EXPORTER_OTLP_PROTOCOL=http/json your-app
```

OTLP/JSON traces, logs **and metrics** work on a plain `pip install clawmetry`, no extras. Protobuf ingest needs `pip install clawmetry[otel]`. An app that sets its own `service.name` shows up as its own agent in the runtime switcher, with its cost and tokens.

**Claude Code, one command.** Claude Code ships its own OpenTelemetry exporter, off by default and with no default protocol. `clawmetry instrument claude` turns it on and points it at the local receiver by writing this `env` block into `~/.claude/settings.json` (add `--project` for the repo-local `.claude/settings.json`):

```json
{
  "env": {
    "CLAUDE_CODE_ENABLE_TELEMETRY": "1",
    "OTEL_LOGS_EXPORTER": "otlp",
    "OTEL_METRICS_EXPORTER": "otlp",
    "OTEL_TRACES_EXPORTER": "otlp",
    "CLAUDE_CODE_ENHANCED_TELEMETRY_BETA": "1",
    "OTEL_EXPORTER_OTLP_PROTOCOL": "http/json",
    "OTEL_EXPORTER_OTLP_ENDPOINT": "http://127.0.0.1:4318",
    "OTEL_EXPORTER_OTLP_METRICS_TEMPORALITY_PREFERENCE": "delta"
  }
}
```

The endpoint is whichever local receiver is listening when you run the command (the 4318 compatibility listener, otherwise the dashboard port). Prompt text and tool output stay OFF unless you pass `--content` (`OTEL_LOG_USER_PROMPTS`, `OTEL_LOG_TOOL_DETAILS`, `OTEL_LOG_TOOL_CONTENT`); raw API bodies are never enabled. The command merges into an existing `env` object, never overwrites a key it did not write, and `--uninstall` removes only its own keys. Restart Claude Code afterwards: a running session keeps the configuration it started with. `clawmetry instrument claude --status` and `GET /api/otel-status` report whether the block is in place and when the last Claude Code batch arrived.

Claude Code is a paid runtime. The receiver accepts its batches on every plan, but the Claude Code specific parts (this command, the join to the transcript session, the typed permission / refusal / MCP events, cache tokens by type, waiting-on-you time) follow the runtime entitlement, like the transcript adapter does. During the grace rollout they are on for everyone; in enforce mode a free install keeps the generic ledger and span rows only, and `clawmetry instrument claude` says so instead of writing the block.

What arrives that the transcript does not carry: permission decisions and their source, permission-mode changes, API refusals and errors, MCP server connection health, time spent waiting on you (`claude_code.tool.blocked_on_user` spans), lines of code, commits and pull requests, and `skill.name` / `agent.name` / `mcp_server.name` attribution on every request.

You get the zero-config, local-first ClawMetry dashboard **and** your data in whatever backend your team already runs — no lock-in, no second agent to install.

The scheduled push exporter (Pro) has its own page:
[OTEL_PUSH_EXPORTER.md](OTEL_PUSH_EXPORTER.md).
