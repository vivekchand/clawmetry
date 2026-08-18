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

OTLP/JSON traces and logs work on a plain `pip install clawmetry`, no extras. Protobuf ingest (and OTLP/JSON metrics) needs `pip install clawmetry[otel]`. An app that sets its own `service.name` shows up as its own agent in the runtime switcher, with its cost and tokens.

You get the zero-config, local-first ClawMetry dashboard **and** your data in whatever backend your team already runs — no lock-in, no second agent to install.

The scheduled push exporter (Pro) has its own page:
[OTEL_PUSH_EXPORTER.md](OTEL_PUSH_EXPORTER.md).
