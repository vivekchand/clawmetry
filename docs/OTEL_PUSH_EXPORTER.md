# OTLP/HTTP push exporter

Periodically POSTs ClawMetry events as OTLP/JSON `logRecords` to a customer
OpenTelemetry collector. Works with Datadog, Grafana Cloud, Honeycomb, or
any OTel collector that accepts OTLP/HTTP logs on a `/v1/logs` endpoint.

**Tier:** Pro (entitlement key `otel_export`).

## Why push as well as pull?

The existing `GET /api/otel/export` endpoint is the *pull* shape: a collector
polls ClawMetry. That works for in-cluster OTel collectors, but Datadog,
Grafana Cloud, and Honeycomb all read from sources rather than hosting pull
endpoints. The push exporter posts to them on a flush cadence.

It also works behind NAT or a firewall without exposing the dashboard.

## Enable

Set two env vars on the dashboard (or sync daemon) and restart:

```bash
export CLAWMETRY_OTLP_ENDPOINT="https://api.honeycomb.io/v1/logs"
export CLAWMETRY_OTLP_HEADERS="x-honeycomb-team: YOUR_KEY, x-honeycomb-dataset: clawmetry"
```

That's it. Every event that lands in DuckDB after redaction is enqueued and
flushed every 10 seconds (default).

Confirm it's running:

```bash
curl http://localhost:8900/api/otel/push/status
# -> {"running": true, "sent": 1240, "dropped": 0, "errors": 0,
#     "flushes": 31, "queue_size": 12, "endpoint": "...", "tier_allows": true}
```

To verify the endpoint + headers without waiting for the next flush:

```bash
curl -XPOST http://localhost:8900/api/otel/push/flush?limit=5
# -> {"ok": true, "sent": 5}
```

## Endpoint recipes

| Vendor | Endpoint | Headers |
|---|---|---|
| Honeycomb | `https://api.honeycomb.io/v1/logs` | `x-honeycomb-team: KEY, x-honeycomb-dataset: clawmetry` |
| Datadog | `https://http-intake.logs.datadoghq.com/api/v2/logs` | `DD-API-KEY: KEY, content-type: application/json` |
| Grafana Cloud (OTLP) | `https://otlp-gateway-prod-us-central-0.grafana.net/otlp/v1/logs` | `Authorization: Basic BASE64(user:token)` |
| Local OTel collector | `http://localhost:4318/v1/logs` | (none) |

For Datadog specifically, the OTLP-JSON envelope is accepted but you may
prefer to point at an in-cluster collector configured for the Datadog
exporter to get full feature parity.

## Tuning

| Env var | Default | Description |
|---|---|---|
| `CLAWMETRY_OTLP_BATCH_MAX` | 200 | Max events per flush |
| `CLAWMETRY_OTLP_FLUSH_SECS` | 10 | Seconds between flushes |
| `CLAWMETRY_OTLP_TIMEOUT_SECS` | 5 | HTTP request timeout |
| `CLAWMETRY_OTLP_QUEUE_MAX` | 10000 | Bounded queue size; older drop on overflow |

The exporter is bounded by design. When the queue is full or the collector
is unreachable, events are dropped and counted (`stats().dropped`) rather
than back-pressuring ingest.

## Data shape

Each event becomes one OTLP `LogRecord`:

```json
{
  "timeUnixNano": "1700000000500000000",
  "severityNumber": 9,
  "severityText": "INFO",
  "body":   {"stringValue": "model.completed"},
  "attributes": [
    {"key": "session_id", "value": {"stringValue": "sess_…"}},
    {"key": "event_type", "value": {"stringValue": "model.completed"}},
    {"key": "model",      "value": {"stringValue": "claude-3.5-sonnet"}},
    {"key": "node_id",    "value": {"stringValue": "node-1"}},
    {"key": "agent_type", "value": {"stringValue": "openclaw"}}
  ]
}
```

Wrapped in the standard `resourceLogs/scopeLogs/logRecords` envelope with
`service.name = clawmetry`.

## Security

By the time an event reaches the push exporter it has already been scrubbed
by `redact_event` (see `clawmetry/redaction.py`), so API keys, OAuth tokens,
and the other tracked patterns will not leave the box even if the collector
is hostile.
