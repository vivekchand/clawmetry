# Custom runtime HTTP ingest API

Push events from any agent runtime into ClawMetry without writing to the
OpenClaw / Claude Code filesystem layout. Designed for in-house agents,
eval harnesses, and web agents that already produce structured run/step
records.

**Tier:** Pro (entitlement key `custom_runtime_ingest`). Free in grace mode
until the enforce rollout flips on.

## Endpoints

| Method | Path | Description |
|---|---|---|
| `GET`  | `/api/v1/runtimes` | List runtimes ClawMetry knows about. Free. |
| `POST` | `/api/v1/runs` | Open a run; returns `run_id`. |
| `POST` | `/api/v1/runs/<id>/events` | Append one or many events. |
| `POST` | `/api/v1/runs/<id>/end` | Mark the run ended. Optional. |
| `GET`  | `/api/v1/runs/<id>` | Read-back: was the run persisted? |

## Auth

Two modes; the dashboard picks based on env:

1. **Localhost-only (default):** if `CLAWMETRY_INGEST_TOKEN` is unset,
   only loopback requests are accepted. Zero-config but local-only.
2. **Token header:** set `CLAWMETRY_INGEST_TOKEN=<secret>` on the
   dashboard; clients must send `X-ClawMetry-Token: <secret>`. The check
   is constant-time.

Non-localhost without a matching token returns `401 unauthorized`.

## Quickstart

```bash
# Start a run
curl -s http://localhost:8900/api/v1/runs \
  -H 'content-type: application/json' \
  -d '{"runtime": "my_engine", "metadata": {"build": "abc123"}}'
# -> {"ok": true, "run_id": "run_a1b2c3d4...", "runtime": "my_engine"}

# Push an event
curl -s http://localhost:8900/api/v1/runs/run_a1b2c3d4/events \
  -H 'content-type: application/json' \
  -d '{"event": {
        "id":         "evt_1",
        "ts":         '"$(date +%s.%N)"',
        "event_type": "model.completed",
        "model":      "claude-3.5-sonnet",
        "data":       {"input_tokens": 1240, "output_tokens": 312}
      }}'
# -> {"ok": true, "accepted": 1, "ids": ["evt_1"]}

# Close it
curl -s http://localhost:8900/api/v1/runs/run_a1b2c3d4/end \
  -H 'content-type: application/json' -d '{}'
```

## Event payload

| Field | Required | Notes |
|---|---|---|
| `id` | no | Dedupe key; server fills `evt_<hex>` if missing. Re-ingesting the same id is a no-op. |
| `ts` | no | Epoch seconds (float). Server uses `time.time()` if missing. |
| `event_type` | no | Free-form. Conventional values: `prompt.submitted`, `model.completed`, `tool.invoked`, `session.started`. |
| `session_id` | no | Defaults to the `run_id`. |
| `tool_name` | no | If the event represents a tool call. |
| `model` | no | LLM model id. |
| `role` | no | `user`, `assistant`, `system`, `tool`. |
| `data` | no | Opaque dict; the daemon adds `data.extra.runtime = <runtime>`. |

Batch shape: `{"events": [event, event, ...]}`. Cap is 1000 events per
request. Split larger batches and retry.

## Where the data goes

Events go through `local_store.ingest`, which means:

* Secret redaction (#2197) scrubs API-key-shaped values before they rest
  in DuckDB.
* Optional SIEM forwarding (#2199) sends to your Splunk / QRadar /
  Elastic collector if `CLAWMETRY_SIEM_HOST` is set.
* The Overview / Tracing / Brain / Usage tabs pick the run up
  automatically; the runtime switcher shows it under whatever string you
  passed in `runtime`.

## Client recipes

A minimal Python client (no extra dependencies):

```python
import os, time, uuid, requests

API = os.environ.get("CLAWMETRY_URL", "http://localhost:8900")
HEAD = {"content-type": "application/json"}
tok = os.environ.get("CLAWMETRY_INGEST_TOKEN")
if tok:
    HEAD["X-ClawMetry-Token"] = tok

def start_run(runtime="my_engine", **meta):
    r = requests.post(f"{API}/api/v1/runs", json={"runtime": runtime, "metadata": meta}, headers=HEAD)
    r.raise_for_status()
    return r.json()["run_id"]

def event(run_id, **fields):
    fields.setdefault("id", f"evt_{uuid.uuid4().hex[:16]}")
    fields.setdefault("ts", time.time())
    requests.post(f"{API}/api/v1/runs/{run_id}/events", json={"event": fields}, headers=HEAD).raise_for_status()

def end(run_id):
    requests.post(f"{API}/api/v1/runs/{run_id}/end", json={}, headers=HEAD).raise_for_status()
```

## Error responses

| Code | Body | Cause |
|---|---|---|
| 400 | `{"error":"bad_request","detail":"..."}` | Malformed event, batch >1000, ts not a number. |
| 401 | `{"error":"unauthorized","hint":"..."}` | Token header missing or wrong, non-localhost without token. |
| 402 | `{"error":"upgrade_required","feature":"custom_runtime_ingest",...}` | Enforce mode, tier doesn't unlock it. |
| 503 | `{"error":"daemon_unavailable"}` | LocalStore writer not reachable. |
| 500 | `{"error":"ingest_failed","detail":"..."}` | Anything else; bug or DuckDB error. Logged with traceback. |
