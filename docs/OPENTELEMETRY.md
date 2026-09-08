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

**Switch a runtime's own exporter on, one command.** Several runtimes ship an OpenTelemetry exporter of their own (Claude Code, Codex, Gemini CLI, Cursor, Copilot, OpenCode and more), each off by default and each configured differently. `clawmetry instrument <runtime>` writes that runtime's settings so its exporter reports to the local receiver, and `--uninstall` removes exactly what it wrote. The mechanics are shared: it merges into the existing settings, never overwrites a value it did not write, keeps a per-file record of its keys, refuses when managed policy pins the destination, and keeps prompt and tool content OFF unless you pass `--content`. Raw request and response bodies are never enabled.

Which runtimes are available depends on which **exporter profiles** are registered. A profile is what tells the vendor-neutral receiver a runtime's metric names, event names, span attribute spellings, session-id form and settings file. Free runtimes' profiles ship in this repo; paid runtimes' profiles ship in the `clawmetry-pro` wheel alongside their transcript adapters, and register through the same plugin entry point. `clawmetry instrument --help` lists what is registered on this install. With no profile registered, an emitter is treated as any other OpenTelemetry app: spans, ledger rows and the generic tiles, nothing runtime-specific.

Claude Code, for example: its profile (in clawmetry-pro) writes the `env` block below into `~/.claude/settings.json` (`--project` for the repo-local file). Claude Code has no default protocol, so the protocol key is required; `http/json` works on a vanilla install.

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

Restart the runtime afterwards: a running session keeps the configuration it started with. `clawmetry status` and `GET /api/otel-status` (`runtimes`) report, per profiled runtime, whether the block is in place and when its last batch arrived.

What a profiled runtime's exporter adds over its transcript: permission decisions and their source, permission-mode changes, API refusals and errors, MCP server connection health, time spent waiting on you, lines of code, commits and pull requests, and per-skill, per-agent and per-MCP-server attribution on every request, all joined to the same session the transcript adapter builds.

You get the zero-config, local-first ClawMetry dashboard **and** your data in whatever backend your team already runs — no lock-in, no second agent to install.

The scheduled push exporter (Pro) has its own page:
[OTEL_PUSH_EXPORTER.md](OTEL_PUSH_EXPORTER.md).
