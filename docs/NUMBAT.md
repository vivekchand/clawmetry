# Numbat integration — ClawMetry as the console for Perplexity's agent-EDR

[numbat](https://github.com/perplexityai/numbat) (Perplexity, Apache-2.0) is
an endpoint detection & response tool for AI coding agents: it watches ~27
agent harnesses through hooks, on-disk session artifacts, and OTLP logs,
evaluates 50+ CEL security rules (secret exfiltration chains, permission
bypasses, persistence, privilege escalation — MITRE ATT&CK-tagged), and can
optionally block risky actions pre-execution.

numbat has **no UI, no storage, and no fleet view** — it writes NDJSON
records and leaves retention and display to you. ClawMetry fills exactly that
gap: findings land in the local DuckDB store, show up on the Security surface
and in alerts, and (on paid plans) aggregate fleet-wide in the cloud.

## Quick start

```bash
clawmetry secure enable    # downloads numbat (SHA-256 verified), installs
                           # monitor-only hooks wired to this dashboard
clawmetry secure status    # per-agent hook wiring + findings ingested
clawmetry secure disable   # removes the hooks again
```

`enable` asks for confirmation first — hook install edits each harness's own
config (that's how numbat works), which crosses ClawMetry's read-only
default. Enforce mode is never enabled. First-time setup surfaces the same
step: `clawmetry onboard` ends with a default-yes "Agent security
monitoring" offer, and that answer is the consent (no second prompt).

### Manual setup (what `clawmetry secure enable` runs for you)

1. [Install numbat](https://github.com/perplexityai/numbat/releases) (single
   static binary, macOS/Linux/Windows).
2. Install its hooks with ClawMetry as the HTTP sink *and* keep the file sink
   (the file is numbat's durable path — its HTTP sink buffers in memory only):

   ```bash
   numbat hook install --agent all --emit findings \
     --output file \
     --output http --http-url http://127.0.0.1:8900/api/numbat/ingest
   ```

3. That's it. ClawMetry picks up findings two ways, deduped by id:
   - the **sync daemon tails `~/.numbat/*.ndjson`** every cycle (primary,
     durable — works even if you skip `--output http`), and
   - the **dashboard accepts numbat's HTTP batches** on
     `POST /api/numbat/ingest` (low-latency supplement; loopback needs no
     extra auth flags).

## What lands where

| numbat record       | ClawMetry destination | Surface |
|---------------------|-----------------------|---------|
| `finding`           | `security_events` table + a `numbat_finding` events row | Security threats, alert rules |
| `enforcement`       | `guardrail_events` table | Governance / guardrail views |
| `event`             | **skipped by design** — numbat events mirror the same session activity ClawMetry already ingests from each harness's own files; storing both would double-count | — |

Critical/high findings additionally fire a banner + Telegram alert
immediately (with the standard cooldown). An opt-in seed rule
(`numbat security finding`) is available on the Alerts tab for
threshold-based alerting.

## Remote nodes

For a numbat that ships to a ClawMetry dashboard on another machine, use
numbat's bearer auth with your gateway token:

```bash
export NUMBAT_HTTP_TOKEN="<your ClawMetry gateway token>"
numbat hook install --agent all --output file \
  --output http --http-url https://your-node:8900/api/numbat/ingest \
  --http-auth bearer
```

Set `NUMBAT_DEVICE_ID` to your ClawMetry node id if you want numbat's own
records to carry the same node identity ClawMetry uses.

## Coexistence notes (read before installing both)

- **OTLP port**: numbat's `numbat collect` and ClawMetry's OTLP receiver both
  follow the `:4318 /v1/logs` convention. Run only one OTLP receiver, or bind
  them to different ports. If ClawMetry's receiver is active, point your
  agents' OTLP exporters at ClawMetry and skip `numbat collect`.
- **Do not** point numbat's HTTP sink at ClawMetry's `/v1/logs` — that
  endpoint only extracts cost/token attributes. Use `/api/numbat/ingest`.
- **OpenClaw plugins**: numbat installs a native OpenClaw plugin, and
  OpenClaw's `plugins.allow` allowlist is **exclusive**. If you use ClawMetry's
  clawhub plugin too, make sure *both* ids are in the allowlist, then verify
  with `openclaw plugins inspect numbat --runtime --json`.
- **Schema pin**: ClawMetry understands numbat wire schema `0.2.x`. Records
  from other versions are counted and skipped (the daemon logs a warning) —
  update ClawMetry if numbat bumps its schema.
