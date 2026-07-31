# ClawMetry Enterprise

Self-hosting, endpoint configuration, OpenTelemetry export, and audit export: the features that let ClawMetry run inside an enterprise boundary without
touching the managed cloud.

## Endpoint configuration

Every daemon/CLI/dashboard call to ClawMetry Cloud resolves its base URL
through `clawmetry/endpoints.py`. Resolution order (first non-empty wins):

1. `CLAWMETRY_ENDPOINT` (env)
2. `CLAWMETRY_INGEST_URL` (env, legacy, still honored)
3. `"endpoint"` key in `~/.clawmetry/config.json`
4. `https://ingest.clawmetry.com` (managed cloud default)

App-side traffic (OAuth pages, account lookups, dashboard links) follows a
custom endpoint too, a self-hosted server is one host. `CLAWMETRY_APP_BASE`
remains an explicit override for split deployments;
`CLAWMETRY_LICENSE_SERVER` still overrides the license/pro-wheel server
specifically.

```jsonc
// ~/.clawmetry/config.json, only ADDS keys, existing format unchanged
{
  "api_key": "cm_...",
  "node_id": "build-box-3",
  "endpoint": "https://clawmetry.internal.example",  // NEW (optional)
  "otlp_endpoint": "http://otel-collector:4318/v1/traces", // NEW (optional)
  "otlp_headers": {"X-API-Key": "..."},                    // NEW (optional)
  "otlp_export_interval": 60                                // NEW (optional)
}
```

Endpoint values are snapshotted at process start (module constants): restart the daemon/dashboard after changing them.

When a custom endpoint is configured, the cloud-only phone-homes
short-circuit: install telemetry and anonymous funnel analytics are skipped
entirely (see `clawmetry/telemetry.py`, `routes/meta.py:_anon_forward_cloud`).

## Self-hosted deployment (ClawMetry Enterprise)

Single-tenant server for a customer VPC or on-prem box. See
[`deploy/self-hosted/README.md`](../deploy/self-hosted/README.md) for the
runbook; short version:

```bash
cd deploy/self-hosted
# set CLAWMETRY_API_TOKENS / CLAWMETRY_ADMIN_USER / CLAWMETRY_ADMIN_PASSWORD in .env
docker compose up -d
# on each node:
CLAWMETRY_ENDPOINT=https://clawmetry.internal.example clawmetry connect --key cm_...
```

`SELF_HOSTED=true` makes the dashboard process additionally register
`routes/selfhosted_ingest.py`, the server side of the daemon's sync
protocol (`/auth`, `/ingest/heartbeat`, `/ingest/events`, `/ingest/cache`,
relay read-back, approvals) backed by an append-only SQLite store, plus
the `/selfhosted` fleet overview page (admin-gated HTML: node roster,
daemon versions, liveness), fleet endpoints (`/api/selfhosted/nodes`,
`/api/selfhosted/status`), and the audit export API. Auth is deliberately simple and single-tenant: node
tokens (`CLAWMETRY_API_TOKENS`) + one admin Basic-auth user
(`CLAWMETRY_ADMIN_USER`/`CLAWMETRY_ADMIN_PASSWORD`). Open self-registration
(`/api/register`) is disabled; heartbeats always answer `plan:
"enterprise"` (no billing, no trials).

E2E encryption is optional in self-hosted mode (`CLAWMETRY_SELF_HOSTED_E2E`,
default off → plaintext inside the deployment, which enables server-side
fleet queries and meaningful audit export).

## OpenTelemetry export

Two complementary OTLP surfaces, both **in addition to** ClawMetry's own
ingest protocol, so a customer's Datadog/Grafana/Honeycomb sees agent
activity without replacing the ClawMetry dashboard:

* **Traces push** (`clawmetry/otel_exporter.py`), agent sessions as GenAI
  `invoke_agent` spans (`gen_ai.system`, `gen_ai.agent.name`,
  `gen_ai.request.model`, `gen_ai.usage.input_tokens`,
  `clawmetry.cost_usd`) with `execute_tool` child spans per tool call
  (`gen_ai.tool.name`). Deterministic trace/span ids per session. Activate
  with the `otlp_endpoint` config key (daemon-hosted, headless-safe) or the
  `CLAWMETRY_OTEL_EXPORT_ENDPOINT` env var (dashboard-hosted, the
  historical path). The scopes are disjoint so both processes never
  double-export.
* **Logs push / pull**, existing Pro feature: OTLP `logRecords` push
  (`CLAWMETRY_OTLP_ENDPOINT`, see `docs/OTEL_PUSH_EXPORTER.md`) and the
  `GET /api/otel/export` pull endpoint.

## Audit export

```bash
clawmetry export --from 2026-07-01 --to 2026-07-31 --format jsonl > events.jsonl
clawmetry export --from 2026-07-01 --to 2026-07-31 --format csv --out events.csv
```

Dumps the immutable event log for a time range from the configured endpoint
(cloud or self-hosted) using the configured credentials (`CLAWMETRY_API_KEY`
env or config `api_key`). The wire contract is
`GET <endpoint>/api/export/events?from=&to=` returning JSONL; CSV conversion
is client-side. Self-hosted servers implement it natively; the export reads
append-only tables that the server never updates or deletes.

## Data flow

**Managed cloud mode**, the sync daemon on each node ingests runtime
artifacts (session JSONL, gateway WebSocket, optional OTLP) into local
DuckDB, then pushes to `ingest.clawmetry.com` over HTTPS: plaintext
heartbeat metadata (node id, versions, counters, cache keys) plus
AES-256-GCM-encrypted blobs (events, logs, memory, snapshots) whose key
never leaves the node, the browser decrypts client-side. Optional
outbound extras: install telemetry ping (opt-out), OTLP export to a
collector you configure.

**Self-hosted mode**, identical daemon, but every byte goes to *your*
endpoint instead: `CLAWMETRY_ENDPOINT` → your server → SQLite/DuckDB on
your volume. Nothing is sent to clawmetry.com: telemetry and analytics
short-circuit on a custom endpoint, and the only optional exception is the
off-by-default daily license/version ping (`CLAWMETRY_LICENSE_PING=1`),
whose exact 5-field payload (version, license id, tier, timestamp, kind) is
documented in `clawmetry/selfhosted.py` and the deploy README. OTLP export,
when configured, goes to the collector endpoint you set, also inside your
boundary if you choose.

```
node (agents) ──daemon──► DuckDB (local dashboard :8900)
     │                        │
     │  HTTPS X-Api-Key       └─optional──► OTLP collector (your Datadog/Grafana)
     ▼
CLOUD MODE:  ingest.clawmetry.com (E2E-encrypted blobs; browser decrypts)
SELF-HOSTED: your server (deploy/self-hosted, SQLite, plaintext by default)
                 └──► /api/export/events (audit JSONL/CSV)
```

## Tests

`tests/test_enterprise_endpoint.py` (resolution order),
`tests/test_selfhosted_mode.py` (flag, auth, ingest protocol, export,
phone-home gating), `tests/test_otel_exporter_spans.py` (span shape against
an in-memory collector).
