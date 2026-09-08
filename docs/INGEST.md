# ClawMetry Ingest Contract (ingest/1)

> GENERATED FILE — do not edit by hand. Source of truth:
> `clawmetry/ingest_contract.py`. Regenerate with
> `python3 scripts/gen_ingest_doc.py` (CI fails on drift).

Two surfaces accept inbound data: the **OTLP receiver** (standard
OpenTelemetry HTTP) and the **run/event ingest API** (structured
run/step records for custom runtimes). Both bind on the same port as
the dashboard (default `127.0.0.1:8900`).

## Evolution rule

Inside `ingest/1` evolution is **additive only**: new endpoints,
content-types, and attributes may be added. Removing or renaming one
requires bumping the contract to `ingest/2`.

## OTLP receiver

Point any OpenTelemetry-instrumented app at the dashboard port:
```
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:8900
OTEL_EXPORTER_OTLP_PROTOCOL=http/json
```

### Endpoints

| Method | Path | Description |
| - | - | - |
| `POST` | `/v1/metrics` | OTLP metrics. Ingests ``gen_ai.client.token.usage`` counters and ``gen_ai.client.operation.duration`` histograms into the token/cost tiles. |
| `POST` | `/v1/traces` | OTLP traces. Ingests GenAI spans (LLM calls, tool calls, sub-agent spawns) into the span tree and session timeline. |
| `POST` | `/v1/logs` | OTLP logs. Ingests the agent event stream exported by Claude Code, Codex, and other runtimes (cost/token/model per log record) into the cost and usage tiles. |

### Accepted content types

| `Content-Type` | Description |
| - | - |
| `application/x-protobuf` | Binary protobuf encoding. Requires ``pip install clawmetry[otel]`` (``opentelemetry-proto`` + ``protobuf``). Raises HTTP 501 when the extra is absent. |
| `application/json` | OTLP/JSON encoding. Works on a plain ``pip install clawmetry`` with no extras. ``ignore_unknown_fields`` is set, so forward-compat keys from newer producers do not cause a 400. |

**`Content-Encoding`:** `identity`, `gzip`.

### Size limits

Decompressed body cap: **64 MB** (override: `CLAWMETRY_OTLP_MAX_DECOMPRESSED_MB`).
Anything larger is rejected with HTTP 400 before the body is parsed.

### Response codes

| Code | Meaning |
| - | - |
| `200` | Accepted. Response body is ``{}`` (empty JSON object). |
| `400` | Malformed or undecodable body. Response body contains ``{"error": "<reason>"}``. |
| `429` | Budget limit exceeded; OTLP intake is paused. Response body contains ``{"paused": true}``. |
| `501` | Binary protobuf body received but ``opentelemetry-proto`` is not installed. Install with ``pip install clawmetry[otel]`` or switch to OTLP/JSON (``Content-Type: application/json``). |

### `gen_ai.*` attributes read

Spans and log records are mapped by `dashboard.py::_otel_to_row`. Every attribute below is tried in order; the first non-empty value wins.

| Primary attribute | Fallbacks | Description |
| - | - | - |
| `gen_ai.request.model` | `gen_ai.response.model`, `llm.model`, `model` | Model name used for the request. |
| `gen_ai.usage.input_tokens` | `llm.usage.prompt_tokens`, `input_tokens` | Input token count. |
| `gen_ai.usage.output_tokens` | `llm.usage.completion_tokens`, `output_tokens` | Output token count. |
| `gen_ai.usage.total_tokens` | `llm.usage.total_tokens`, `total_tokens` | Total token count. |
| `gen_ai.usage.cache_read.input_tokens` | `gen_ai.usage.cache_read_input_tokens`, `cache_read_input_tokens` | Cached input tokens read (Anthropic / OpenAI prompt caching). |
| `gen_ai.usage.cache_creation.input_tokens` | `gen_ai.usage.cache_creation_input_tokens`, `cache_creation_input_tokens` | Cache-write tokens (Anthropic prompt caching). |
| `gen_ai.usage.cost_usd` | `llm.usage.cost`, `cost_usd` | Pre-computed cost in USD. When absent, ClawMetry prices the tokens locally. |
| `gen_ai.provider.name` | `gen_ai.system`, `llm.provider`, `provider` | Provider string (e.g. ``anthropic``, ``openai``). |
| `gen_ai.tool.name` | `tool.name`, `code.function` | Name of the tool called (on ``execute_tool`` spans). |
| `gen_ai.conversation.id` | `session.id`, `openclaw.session_id`, `session_id` | Session or conversation identifier. |
| `gen_ai.agent.id` | `agent.id`, `openclaw.agent_id`, `agent_id` | Agent identifier. |
| `gen_ai.input.messages` | `gen_ai.prompt` | Input message list (current GenAI semconv). |
| `gen_ai.output.messages` | `gen_ai.completion` | Output message list (current GenAI semconv). |

Attributes that appear in GenAI semconv but are **not yet consumed**: `gen_ai.operation.name`, `gen_ai.agent.name`.

## Run / event ingest API

Push structured run and event records from any agent runtime. The write endpoints are a **Pro feature** (OSS returns HTTP 402). `GET /api/v1/runtimes` is free on all tiers.

### Endpoints

| Method | Path | Tier | Description |
| - | - | - | - |
| `GET` | `/api/v1/runtimes` | Free | List runtimes ClawMetry knows about. Same data the runtime switcher reads. |
| `POST` | `/api/v1/runs` | Pro | Open a run. Returns ``{ok, run_id, runtime}``. |
| `POST` | `/api/v1/runs/<run_id>/events` | Pro | Append one or many events to an open run. |
| `POST` | `/api/v1/runs/<run_id>/end` | Pro | Mark the run ended. Optional — the run also closes on inactivity. |
| `GET` | `/api/v1/runs/<run_id>` | Pro | Read-back: confirm the run was persisted and return its metadata. |

### Auth

Two modes; the dashboard picks based on environment:

1. **Localhost-only (default):** if `CLAWMETRY_INGEST_TOKEN` is unset, only loopback (`127.0.0.1` / `::1`) requests are accepted.
2. **Token header:** set `CLAWMETRY_INGEST_TOKEN=<secret>`; clients must send `X-ClawMetry-Token: <secret>`. The comparison is constant-time.

### Response codes

| Code | Meaning |
| - | - |
| `200` | Success (GET requests). |
| `201` | Accepted (POST requests). |
| `400` | Malformed request body. |
| `401` | Token required but missing or incorrect. |
| `402` | Pro plan required; OSS stub returns this on all write endpoints. |
| `429` | Rate limit or budget pause. |

### Quickstart

```bash
# Start a run
curl -s http://localhost:8900/api/v1/runs \
  -H 'content-type: application/json' \
  -d '{"runtime": "my_engine", "metadata": {"build": "abc123"}}'
# -> {"ok": true, "run_id": "run_a1b2c3d4...", "runtime": "my_engine"}

# Push an event
curl -s http://localhost:8900/api/v1/runs/run_a1b2c3d4/events \
  -H 'content-type: application/json' \
  -d '{"event": {"id": "evt_1", "event_type": "model.completed", \
    "model": "claude-sonnet-5", "data": {"input_tokens": 1240, "output_tokens": 312}}}'

# Close the run
curl -s http://localhost:8900/api/v1/runs/run_a1b2c3d4/end \
  -H 'content-type: application/json' -d '{}'
```
