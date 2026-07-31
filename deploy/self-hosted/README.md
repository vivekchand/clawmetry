# ClawMetry Enterprise, self-hosted deployment

Single-tenant ClawMetry inside your VPC or on-prem box. One container serves
the dashboard UI **and** the ingest API your node daemons push to. Data never
leaves the deployment (see "What leaves the box" below).

## Requirements

- Docker + Docker Compose v2 (`docker compose`)
- 1 vCPU / 1 GB RAM is plenty for tens of nodes; disk sized to your event
  retention (events are small JSON rows; budget ~1 GB per 5M events)
- A TLS-terminating reverse proxy (nginx/Caddy/ALB) in front of port 8900 if
  nodes connect across the network, the container itself speaks plain HTTP

## One-command start

```bash
cd deploy/self-hosted
cat > .env <<'EOF'
CLAWMETRY_API_TOKENS=cm_generate_a_long_random_token_here
CLAWMETRY_ADMIN_USER=admin
CLAWMETRY_ADMIN_PASSWORD=generate_a_long_random_password
EOF
docker compose up -d
```

Verify:

```bash
curl -u admin:...password... http://localhost:8900/api/selfhosted/status
```

## Connect nodes

On each machine running agents:

```bash
pip install clawmetry
CLAWMETRY_ENDPOINT=https://clawmetry.internal.example \
  clawmetry connect --key cm_generate_a_long_random_token_here
```

`CLAWMETRY_ENDPOINT` can also be persisted as the `"endpoint"` key in
`~/.clawmetry/config.json` on the node. Resolution order everywhere:
`CLAWMETRY_ENDPOINT` env > `CLAWMETRY_INGEST_URL` env (legacy) > config
`endpoint` > managed cloud default.

Tokens must start with `cm_` (the CLI enforces the prefix). Multiple tokens
are comma-separated in `CLAWMETRY_API_TOKENS`; rotate by adding the new token,
re-connecting nodes, then removing the old one and restarting the server.

Each node keeps its own full local dashboard at `localhost:8900` as usual.
The self-hosted server records every node's heartbeats, sessions, and events
(SQLite) and serves a fleet overview page at `/selfhosted` (admin login:
node roster, daemon versions, liveness) plus fleet APIs:
`/api/selfhosted/nodes`, `/api/selfhosted/status`, `/api/export/events`.

## E2E encryption trade-off

By default the server answers `/auth` with `"e2e": false`, so nodes send
events in plaintext **inside your deployment**, that is what makes
server-side audit export and fleet queries meaningful. Set
`CLAWMETRY_SELF_HOSTED_E2E=1` to keep client-side AES-256-GCM blob
encryption instead; the server then stores opaque ciphertext and audit
export contains only envelope metadata (node ids, timestamps, paths).

## What leaves the box

Outbound calls from a self-hosted deployment: **none**, with one optional
exception. If you set `CLAWMETRY_LICENSE_PING=1`, the server POSTs once per
24h to `https://app.clawmetry.com/api/license/ping` exactly this payload:

```json
{"kind": "selfhosted_ping", "version": "<package version>",
 "license": "<license 'sub' claim or empty>", "tier": "<license tier or empty>",
 "ts": "<ISO-8601>"}
```

No hostnames, node ids, counts, event data, or metrics, ever. The ping is
off by default. Node daemons pointed at your endpoint make no calls to
clawmetry.com either (install telemetry and anonymous analytics
short-circuit when a custom endpoint is configured).

## Audit export

```bash
# JSONL (one event per line)
curl -u admin:... "http://localhost:8900/api/export/events?from=2026-07-01&to=2026-07-31" \
  > events.jsonl

# Or from any workstation with the CLI:
CLAWMETRY_ENDPOINT=https://clawmetry.internal.example \
CLAWMETRY_API_KEY=cm_... \
  clawmetry export --from 2026-07-01 --to 2026-07-31 --format csv --out events.csv
```

The export reads the append-only event log (`ingest_log` + `events` tables);
rows are never updated or deleted by the server.

## Upgrade path

```bash
cd deploy/self-hosted
git pull                      # or check out the release tag you validated
docker compose build --pull
docker compose up -d          # recreates the container; the volume persists
```

Schema migrations are additive (`CREATE TABLE IF NOT EXISTS`); downgrades are
not supported, snapshot the volume before upgrading (see Backups).

## Backups

All state lives on the `clawmetry-data` volume (`/root/.clawmetry` in the
container): `selfhosted.db` (SQLite ingest/audit store), `events.duckdb`
(local event store), `config.json`. SQLite in WAL mode is safe to back up
with:

```bash
docker compose exec clawmetry \
  sqlite3 /root/.clawmetry/selfhosted.db ".backup /root/.clawmetry/backup.db"
docker cp "$(docker compose ps -q clawmetry)":/root/.clawmetry/backup.db ./
```

or stop the container and snapshot the whole volume. Test restores by
mounting the volume into a scratch compose project.

## Scope notes (v1)

- The fleet-level UI is intentionally minimal (JSON APIs); each node's own
  dashboard remains the rich per-node UI. Full multi-node dashboard parity
  with ClawMetry Cloud is on the Enterprise roadmap.
- No Kubernetes/Helm yet, this compose file is the supported deployment.
