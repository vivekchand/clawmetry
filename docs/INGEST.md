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
| `200` | Stored. Sent only after the local store confirmed the write. The body is an empty export response (``{}`` for OTLP/JSON, an empty protobuf message for protobuf). When some items were malformed (a span with no id or name, or an item carrying a value the store cannot hold, such as a token count beyond its range) the rest are stored and the body carries ``partialSuccess`` with the refused count in ``rejectedLogRecords``, ``rejectedSpans`` or ``rejectedDataPoints``. Do not retry. |
| `400` | Malformed or undecodable body. Nothing is stored. Response body contains ``{"error": "<reason>"}``. Do not retry the same body. |
| `401` | A request from another machine without a valid token (see Authentication). Refused before the body is read. Fix the credentials; retrying unchanged will be refused again. |
| `501` | Binary protobuf body received but ``opentelemetry-proto`` is not installed. Install with ``pip install clawmetry[otel]`` or switch to OTLP/JSON (``Content-Type: application/json``). |
| `503` | Not stored: the local store did not confirm the write (the daemon that owns it is restarting, busy or unreachable). Nothing in the export is acknowledged. Retry after the ``Retry-After`` delay; items that did reach the store are recognised on retry and not counted twice. |

### Acknowledgement and retry

The receiver keeps no intake queue of its own. It answers 200 only after the local store confirms the write, and 503 with ``Retry-After`` when it cannot, so a batch the store could not take stays in the exporter's own retry buffer. How long an exporter retries, and what it drops when that buffer is full, is the exporter's configuration (for the OpenTelemetry SDKs, the exporter timeout and the batch processor's queue size). A spending-limit pause on the observed agents does not pause intake: activity after a budget incident is still recorded.

`Retry-After` on a 503: **5 seconds**.

### Recognising a re-delivery

| Path | Identity |
| - | - |
| `/v1/logs` | A hash of the sender's ``service.name``, the session, the event name, the record's own ``time_unix_nano`` and ``observed_time_unix_nano``, its body and every attribute. A retried record replaces itself. Two model calls that differ in their own time or in any attribute (a request id, for example) are two records and both are counted; two that are identical in all of these are one. |
| `/v1/traces` | The span's ``span_id``. A re-delivered span replaces the stored one, so a later delivery carrying a corrected end time or status overwrites the first. The live tiles count a span once per ``trace_id`` and ``span_id``. |
| `/v1/metrics` | Runtime-profile metrics are stored keyed by a hash of the sender, the session, the metric name, the data point's own time, its attributes and its value. Other metrics count once per data point that carries its own time; a point with no time cannot be told apart from a new one. |

### Session identity when the sender names none

| Path | Session |
| - | - |
| `/v1/logs` | The first of ``session.id``, ``session_id``, ``gen_ai.conversation.id``, ``conversation.id`` and ``cursor.conversation.id``, on the record and then on the resource. A record with none of them is stored and counted in the team, repository and person rollups, but joins no session. |
| `/v1/traces` | The first of ``gen_ai.conversation.id``, ``session.id``, ``openclaw.session_id`` and ``session_id``. When a span carries none (and its runtime is not ``openclaw``), its trace becomes the session as ``<runtime>:trace:<trace_id>``, so every trace without an id adds one session. A sender that starts sending a conversation id later starts new sessions under it; the earlier trace-derived sessions are kept as they are and are not merged. |
| `/v1/metrics` | ``session.id`` on the data point, then on the resource. With neither, the stored row has no session. |

### Held only in the live view

The ``openclaw.*`` metrics and the GenAI ``gen_ai.client.token.usage`` and ``gen_ai.client.operation.duration`` metrics feed the live token, cost and run tiles only. They are held in memory, are not written to the local store and are gone after a restart; the intake status counts them as ``live_view_only``, and metrics nothing reads as ``not_read``. The live tiles remember the most recent 20,000 items when recognising a re-delivery. The spend rollup (``/api/otel/rollup``) sums received log records only: span cost is not added to it, so a sender that samples its traces does not reduce it. A group in which no record reported a cost has no spend figure rather than zero, and says how many records carried one.

### Authentication

A request from this machine (loopback) needs no credentials. A request from another machine must send the gateway token as ``Authorization: Bearer <token>`` (or ``?token=``) and is otherwise refused with 401 before its body is read, including when no gateway token is configured. ``CLAWMETRY_OTLP_ALLOW_UNAUTH=1`` accepts unauthenticated requests from the network, for a trusted LAN only.

### Intake status

``GET /api/otel-status`` carries an ``intake`` block. Per signal, ``items`` counts what arrived (``received``), what is in the store (``stored``), what was refused as malformed (``rejected``), what was already stored or repeated in the same export (``already_stored``), what is held only in the live tiles (``live_view_only``), metrics nothing reads (``not_read``), events not recorded because another source already reports that session (``skipped_other_source``) and items the sender was asked to send again (``retry_requested``). ``requests`` counts acknowledged, partially acknowledged, retry-requested, malformed, protobuf-unavailable and unauthorized requests, and requests received during a spending-limit pause. ``last_success_at``, ``last_failure_at`` and ``last_failure`` (a fixed category) close each signal. Counts start when the receiver starts. The block holds no record content, attribute value or credential.

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
| `gen_ai.conversation.id` | `traceloop.association.properties.thread_id`, `session.id`, `openclaw.session_id`, `session_id` | Session or conversation identifier. Fallbacks are read in the order listed, so a LangGraph thread (``traceloop.association.properties.thread_id``, what OpenLLMetry stamps on every span below the run's top span) outranks ``session.id`` on the span or the resource. |
| `gen_ai.agent.id` | `agent.id`, `openclaw.agent_id`, `agent_id` | Agent identifier. |
| `gen_ai.input.messages` | `gen_ai.prompt` | Input message list (current GenAI semconv). |
| `gen_ai.output.messages` | `gen_ai.completion` | Output message list (current GenAI semconv). |
| `gen_ai.operation.name` | — | Operation kind (``chat``, ``text_completion``, ``generate_content``). Read to decide whether a span counts as a run: OpenLLMetry and traceloop-sdk name LLM spans ``<vendor>.chat`` / ``<vendor>.completion`` and tag the operation here, so without it a bring-your-own-agent install records spans while the live Runs tile stays at zero. |

Attributes that appear in GenAI semconv but are **not yet consumed**: `gen_ai.agent.name`.

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
