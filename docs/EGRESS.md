# Network egress inventory

Every outbound destination ClawMetry can contact, what it sends, when, and how
to turn it off.

This exists because "does this tool send our source code anywhere?" is the
first question in any review of a tool that reads developer machines, and the
only useful answer is a complete list someone can verify on the wire. If you
find traffic to a host that is not in this table, that is a bug. Please report
it (see [SECURITY.md](../SECURITY.md)).

The tables below were rebuilt from a wire capture of clawmetry 0.12.802 on
2026-09-03, not from reading comments. The capture method is at the end so you
can repeat it in five minutes without trusting this page.

**Verify it yourself.** These commands should produce no unexpected hosts:

```bash
# Every absolute http(s) asset reference in a served page (expects: none)
python3 scripts/verify_no_external_assets.py

# Every vendored JS bundle, byte-compared to its published npm release
python3 scripts/verify_vendor.py

# The full-suppression path, exercised in tests
python3 -m pytest tests/test_egress_suppression.py tests/test_e2e_invariants.py
```

---

## The short version

| Deployment | Contacts ClawMetry servers? | Contacts any third party? |
|---|---|---|
| **Self-hosted** (`SELF_HOSTED=true`) | No | No |
| **Air-gapped** (`CLAWMETRY_OFFLINE=1`) | No | No |
| **Local only** (no `clawmetry connect`) | One install ping; nothing else | PyPI version check |
| **Managed cloud** (`clawmetry connect`) | Yes: sealed content plus plaintext metadata (table below) | PyPI version check |

No ClawMetry deployment loads a CDN, font, analytics script, error tracker or
tracking pixel. Web assets are vendored into the package and served from the
local process; CI fails on any absolute `http(s)` asset reference in a served
page.

Two optional features can contact a **model provider** with your own API key.
Both are **off** until you turn them on: transcript quality scoring
(`CLAWMETRY_EVALS_ENABLED=1`) and the Claude rate-limit probe
(`CLAWMETRY_CLAUDE_LIMIT_PROBE=1`). One is on when an `ANTHROPIC_API_KEY` is
present: the alert narrator, which sends the alert's own one-line message and
rule id, never session content (`CLAWMETRY_NARRATOR_ENABLED=0` to stop it).

Destinations belonging to *your* agents (`api.anthropic.com`, `api.openai.com`
and similar) otherwise appear in this codebase only as strings used to
attribute costs and parse pricing. ClawMetry observes those calls; it does not
make them.

---

## What the server can read, and what it cannot

After `clawmetry connect`, two kinds of data leave the machine.

**Sealed.** Encrypted on the node with AES-256-GCM (96-bit random nonce per
blob) under a key the server never receives. Large blobs are gzip-compressed
*before* encryption (about 4x smaller; ciphertext itself does not compress),
but only once the server has said every reader it serves can inflate
(heartbeat `caps.blob_gzip`); `CLAWMETRY_BLOB_GZIP=0` turns it off. The server stores the blob; the
browser decrypts it. A node with no key **skips** these uploads rather than
sending them in the clear (`content_egress_permitted` in `clawmetry/sync.py`,
enforced by `tests/test_e2e_invariants.py`).

* Prompts, replies, thinking, tool inputs and tool outputs
* Session titles (the plaintext session row carries only the session id)
* Working directory and workspace paths
* Gateway log lines and log records
* Memory and instruction files: `MEMORY.md`, `SOUL.md`, `AGENTS.md`, project
  memory notes, skills and plugin `SKILL.md` files. **Runtime config files
  (`settings.json`, `openclaw.json`, MCP manifests) are catalogued locally but
  never pushed**, sealed or not, because they tend to hold tokens
* Local IP, CPU and RAM details, the security posture scan, the audit log
* Cron prompt text, alert rule bodies, the approval queue
* Everything the cloud pulls on demand: transcript pages, traces, search results

**Plaintext.** JSON over TLS that the server parses so it can list, sort and
bill. Readable by ClawMetry and by anyone who obtains the server's data.

* Machine hostname, on almost every request, as `node_id` and the `X-Node-Id`
  header
* The account key, as the `X-Api-Key` header on every request (never in a URL)
* Per session: id, runtime and model names, status, start and last-active
  times, token counts, cost in USD, cache read/write split, cache savings,
  tool error rate, tool call count, message count, surface (terminal/editor)
* Heartbeat: names of tools used today with counts, the last tool used,
  detector one-liners such as `Bash failed 5 times` or `27 files changed in
  one stretch`, installed runtimes with session counts and last-active time,
  local Ollama model names, billing plan labels, daily activity counters, a
  random install id, the local DuckDB size, and the names of cache keys
* Cron job names, cron expressions and models (prompt text, watched command
  and last error are stripped)
* Alert rule names and counter-style summaries when a rule fires
* Trial days left and plan name, at most once a day on a trial

If the plaintext column is more than your review allows, run self-hosted or
local-only. There is no "metadata-minimal" cloud mode yet.

---

## Deployment modes in detail

### Self-hosted (ClawMetry Enterprise)

Set `SELF_HOSTED=true` on the server. Node daemons point at it with
`CLAWMETRY_ENDPOINT=https://clawmetry.your-company.internal`.

**Outbound calls: none.** Node daemons talk only to your server. The server
talks to nothing. Telemetry, funnel analytics, public-IP lookup and update
checks are all suppressed. See the suppression gate below.

One optional exception, **off by default**: setting `CLAWMETRY_LICENSE_PING=1`
starts a daily POST to `https://app.clawmetry.com/api/license/ping` carrying
exactly this and nothing else:

```json
{"kind": "selfhosted_ping", "version": "0.12.802", "license": "<sub claim>", "tier": "pro", "ts": "..."}
```

No hostnames, node IDs, counts, usage, or telemetry. It exists so a license can
be checked against revocation and so you are told about updates. Leave it unset
and the deployment is silent. Source: `clawmetry/selfhosted.py`.

### Air-gapped

`CLAWMETRY_OFFLINE=1` additionally skips the entitlement probe and the pro
wheel download, so licensing is fully local against a signed license file. Use
it together with `SELF_HOSTED=true` on a network with no route out.

### Local only (default `pip install clawmetry`)

Runs entirely on `127.0.0.1` against your own filesystem. Nothing is uploaded.
Two outbound calls remain: the one-time install ping (`DO_NOT_TRACK=1` stops
it) and the PyPI version check described below.

### Managed cloud (after `clawmetry connect`)

The daemon pushes to `ingest.clawmetry.com` on the cadence in the table below.
Content is sealed client-side; **the key never leaves your machine** and is not
recoverable by ClawMetry. The browser decrypts for display. See
[ARCHITECTURE.md](../ARCHITECTURE.md).

`CLAWMETRY_NO_CLOUD=1`, or `touch ~/.clawmetry/nocloud`, turns every upload
into a no-op without a restart. It does not gate the entitlement probe
(`CLAWMETRY_OFFLINE=1` does).

---

## The suppression gate

`clawmetry.endpoints.egress_suppressed()` is the single check every
discretionary outbound call must pass. It returns `True` when **any** of:

| Condition | Meaning |
|---|---|
| `CLAWMETRY_ENDPOINT` / `CLAWMETRY_INGEST_URL` set | traffic repointed at your server |
| `endpoint` key in `~/.clawmetry/config.json` | same, via config file |
| `SELF_HOSTED=true` / `CLAWMETRY_SELF_HOSTED=true` | this process *is* your server |
| `CLAWMETRY_OFFLINE=1` | air-gapped |

"Discretionary" excludes the deployment's own configured ingest endpoint. That
push is the product, and repointing it is what self-hosting means.

The gate **fails closed**: if the check itself raises (partial install, older
package), the call is suppressed rather than allowed. Covered by
`tests/test_egress_suppression.py`.

---

## Full destination table

### ClawMetry-operated, managed cloud only

Cadence is what the daemon did in the 2026-09-03 capture with Claude Code and
Codex sessions on the machine.

| Path | Cadence | Plaintext the server reads | Sealed |
|---|---|---|---|
| `POST /ingest/heartbeat` | every 3 s while a viewer is open, else 60 s | node_id, platform, version, e2e flag, install_id, detected runtimes with session counts, tool names and counts today, last tool used, detector messages, Ollama model names, billing plan labels, activity counters, store size, cache-key names | `cache_pushes` blobs: last 50 brain events, memory files, cron list, alert rules, approval queue |
| `POST /ingest/sessions` | every 60 s when rows change | session_id, runtime, model, status, timestamps, total_tokens, cost_usd, token_split, cache stats, tool_error_pct, tool_call_count, message_count, surface | `title_blob` (the readable title) |
| `POST /ingest/system-snapshot` | every ~60 s; about 300 KB once the server advertises gzip (1.2 to 1.4 MB before) | node_id | 80 keys: transcripts with full message text, machine info, security posture, audit log, agent inventory with workspace paths, MCP servers, tool catalog, spending, traces, skills |
| `POST /ingest/events` | as transcripts change (OpenClaw JSONL path) | node_id | raw transcript events |
| `POST /ingest/logs` | every 60 s when the gateway log grows | node_id | gateway log records |
| `POST /ingest/stream` | every 2 s when the log tail moves | node_id | raw gateway log lines |
| `POST /ingest/memory` | on file-hash change | node_id | OpenClaw workspace memory files |
| `POST /ingest/cache` | only when the cloud asks | node_id, cache_key, shape name, args hash | on-demand query results and action outcomes |
| `POST /api/ingest` (crons) | each tick when a job changes | job_id, name, cron expression, model, run state | none |
| `POST /api/cloud/alerts/dispatch` | on rule match, checked every 60 s | rule id and name, node_id, event id, 500-char summary | none |
| `GET /ingest/wake` | long-poll held 15 s, continuous | node_id in the query, key in a header | none |
| `GET /api/cloud/policies` | every ~30 s | key in a header | none |
| `GET /api/license/entitlement` | daemon start, then every ~30 min | key in a header; an entitled node downloads and installs the pro wheel | none |
| `GET /api/cloud/account`, `GET /api/cloud/claim-status` | once per daemon start; every 5 s only while on a placeholder account | key in a header, node_id | none |
| `POST /auth` | only during `clawmetry connect` | api_key, hostname, machine_id (hash of hardware id) | none |
| `POST /api/install` | once per install, first run | random install id, version, OS, Python version, detected agent name, CI flag | none |
| `POST /api/admin/anon-event` | first dashboard load that fails auth | event name, version, browser family | none |
| `POST /ingest/trial-warning` | at most once a day on a trial | days_left, plan | none |
| `POST /api/license/ping` | self-hosted, **off unless** `CLAWMETRY_LICENSE_PING=1` | version, license subject, tier, timestamp | none |

### Inbound control channel

The heartbeat response can carry actions for the daemon: pause, stop or kill
a session, edit or disable a cron, answer an approval, run an allow-listed
DuckDB query and return the sealed result. Every relayed action is written to
`~/.clawmetry/audit.db` as it arrives, accepted or refused, so the node owner
has their own record of what the server asked.

Actions that would run a **server-supplied prompt** through a local agent
(`selfevolve_fix`, `cron_create`, `cron_fix`) are refused unless the node has
opted in with `CLAWMETRY_ALLOW_REMOTE_PROMPTS=1` or
`clawmetry config set remote_prompts true`.

### Third-party

| Host | Purpose | When | Default |
|---|---|---|---|
| `pypi.org` | version check; a newer release is pip-installed | every 60 s from the daemon (`CLAWMETRY_UPDATE_CHECK_SECS`). Not contacted by self-hosted, air-gapped or repointed installs | on; `CLAWMETRY_AUTO_UPDATE=0` stops installs, `CLAWMETRY_AUTOUPDATE_MIN_AGE_HOURS` adds a stability window. Every attempt is recorded locally |
| `api.anthropic.com` / `api.openai.com` | transcript quality scoring with your own key: a redacted 8 KB head-and-tail excerpt per session | after a session ends | **off**; `CLAWMETRY_EVALS_ENABLED=1` or `"evals": true` in config |
| `api.anthropic.com` | alert narration: the alert message and rule id | when an alert fires and `ANTHROPIC_API_KEY` is set | on; `CLAWMETRY_NARRATOR_ENABLED=0` |
| `api.anthropic.com` with the Claude Code OAuth token | a one-token request to read rate-limit headers | every 5 min | **off**; `CLAWMETRY_CLAUDE_LIMIT_PROBE=1` |
| `api.ipify.org` | public IP for one cosmetic startup banner line | dashboard start, managed cloud only | on; any suppression condition |

Third-party telemetry inside optional integrations is forced off rather than
merely left unconfigured. The DeepEval evaluation bridge, for example, phones
PostHog by default upstream; `clawmetry/deepeval_bridge.py` disables that
before importing it.

### Not egress, but adjacent: the local write API

The dashboard on `localhost:8900` trusts loopback callers without a token. It
rejects state-changing requests that carry an `Origin` header from another
site, so a page you happen to have open in another tab cannot drive it.
`CLAWMETRY_ALLOW_CROSS_ORIGIN_WRITES=1` removes that check for embedders that
genuinely need it.

### Configured by you, off by default

These fire only if you configure them, to a destination you choose:

| Integration | Destination |
|---|---|
| Alert webhooks | your URL |
| PagerDuty sink | `events.pagerduty.com` |
| Opsgenie sink | `api.opsgenie.com` / `api.eu.opsgenie.com` |
| Telegram notifications | `api.telegram.org` |
| OTLP export | your collector |

---

## Data that never leaves the machine

Regardless of mode:

* **The encryption key.** Generated locally by `clawmetry connect`, stored in
  `~/.clawmetry/config.json` and the OS keychain, handed to the browser in a
  URL fragment (which browsers do not send to servers). Cloud blobs are opaque
  to ClawMetry. The cloud never mints a key for a node.
* **Your source code.** ClawMetry reads agent *transcripts and metadata*, not
  your repository. Transcripts can quote code your agent read or wrote; those
  travel sealed.
* **Gateway, bot and provider API keys.** Read locally to talk to your gateway
  and to attribute billing; runtime config files are excluded from every
  upload.
* **The DuckDB store** at `~/.clawmetry/clawmetry.duckdb`, unless you enable
  cloud sync, and then only as ciphertext plus the plaintext metadata listed
  above.

---

## Repeat the capture

```bash
S=$(mktemp -d); mkdir -p $S/home/.clawmetry
# copy api_key, node_id and encryption_key from ~/.clawmetry/config.json into $S/home/.clawmetry/config.json
# symlink the agent directories you want scanned: ln -s ~/.claude $S/home/.claude   (and so on)
python3 - <<'EOF' &
import json, sys, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
class H(BaseHTTPRequestHandler):
    def _log(self):
        n = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(n) if n else b""
        print(json.dumps({"path": self.path, "headers": dict(self.headers), "body": body.decode("utf-8", "replace")}), flush=True)
        b = b'{"ok": true, "sync_allowed": true, "plan": "pro"}'
        self.send_response(200); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
    do_GET = do_POST = do_PUT = _log
    def log_message(self, *a): pass
ThreadingHTTPServer(("127.0.0.1", 8999), H).serve_forever()
EOF
env -i PATH="$PATH" HOME=$S/home CLAWMETRY_ENDPOINT=http://127.0.0.1:8999 CLAWMETRY_AUTO_UPDATE=0 \
  python3 -m clawmetry.sync
```

`CLAWMETRY_ENDPOINT` repoints both hosts, so nothing reaches the real cloud.
Every request the daemon makes prints as one JSON line. Decrypt any `blob`
with `clawmetry.sync.decrypt_payload(blob, config["encryption_key"])`. Delete
`$S` afterwards: it holds a copy of your key.

---

## Reporting a discrepancy

Traffic to a host not listed here is a bug and is treated as a security issue.
See [SECURITY.md](../SECURITY.md) for how to report it privately.
