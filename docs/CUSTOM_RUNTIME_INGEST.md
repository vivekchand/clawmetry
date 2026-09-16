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

Three ways in. They do not replace each other — a machine can accept all
three at once, and adding one never moves an existing one.

1. **Localhost-only (default):** if `CLAWMETRY_INGEST_TOKEN` is unset,
   only loopback requests are accepted. Zero-config but local-only.
2. **Token header:** set `CLAWMETRY_INGEST_TOKEN=<secret>` on the
   dashboard; clients must send `X-ClawMetry-Token: <secret>`. The check
   is constant-time. One secret for the whole install: no rotation, no
   revocation, no way to tell two pushers apart.
3. **Ingest key (recommended for anything off this machine):** a scoped,
   named, revocable key.

   ```bash
   clawmetry key create --name ci --scope write:ingest
   ```

   Present it as `x-clawmetry-key: cmk_...` on `/v1/logs`,
   `/v1/metrics`, `/v1/traces` and the run/event endpoints below. This is
   what lets an agent in CI, a container, a serverless function or on a
   teammate's laptop be observed at all — the first two modes require the
   agent and the daemon to share a machine.

   An ingest key **can only push**. `write:ingest` grants no `q/1` read
   shape, so a key handed to a CI runner cannot read a prompt, a cost or
   a session back out; presenting one to `/api/q/1` returns `403`. It is
   also never given a CORS header and cannot be created with a browser
   origin: ingest is server-to-server.

Non-localhost without a valid credential returns `401 unauthorized`. A
valid key that lacks `write:ingest` returns `403 forbidden` — a different
answer on purpose, because "your key is wrong" and "your key is fine and
may not do this" send you to different fixes.

## Routing headers

A pushed event carries no filesystem layout to infer a runtime from, so
the pusher says which runtime it is. Both headers are optional and are
resolved once per request, then applied to every event in it.

| Header | Value | Effect |
|---|---|---|
| `x-clawmetry-runtime` | `claude_code`, `my-engine`, … | Sets the resource's `service.name`, which is what the runtime is derived from. An unrecognised name is accepted — in-house engines are a supported case. |
| `x-clawmetry-env` | `production`, `team-a.staging`, … | Sets `deployment.environment`, the one grouping axis above runtime. |

The header wins over the equivalent resource attribute. Both are set by
the same operator; the header is the one set per request.

Deliberately one grouping axis and not a dataset / collection / tag
taxonomy: that taxonomy is what a log platform needs when it has
thousands of unrelated sources, and it is not what an agent platform is.

## OTLP

`/v1/logs`, `/v1/metrics` and `/v1/traces` accept **OTLP protobuf**
(`Content-Type: application/x-protobuf`) and **OTLP/JSON**
(`application/json`), either of them gzipped
(`Content-Encoding: gzip`). Point any OTel SDK or Collector at them.

```bash
curl -X POST http://localhost:8900/v1/traces \
  -H "x-clawmetry-key: $CLAWMETRY_KEY" \
  -H 'x-clawmetry-runtime: my-engine' \
  -H 'x-clawmetry-env: production' \
  -H 'Content-Type: application/json' \
  --data-binary @spans.json
```

Bodies over 10 MB return `413` with the size and the limit, rather than
failing somewhere inside a protobuf parser.

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
