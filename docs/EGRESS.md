# Network egress inventory

Every outbound destination ClawMetry can contact, what it sends, when, and how
to turn it off.

This exists because "does this tool send our source code anywhere?" is the
first question in any review of a tool that reads developer machines, and the
only useful answer is a complete list someone can verify with `tcpdump`. If you
find traffic to a host that is not in this table, that is a bug — please report
it (see [SECURITY.md](../SECURITY.md)).

**Verify it yourself.** These commands should produce no unexpected hosts:

```bash
# Every absolute http(s) asset reference in a served page (expects: none)
python3 scripts/verify_no_external_assets.py

# Every vendored JS bundle, byte-compared to its published npm release
python3 scripts/verify_vendor.py

# The full-suppression path, exercised in tests
python3 -m pytest tests/test_egress_suppression.py
```

---

## The short version

| Deployment | Contacts ClawMetry servers? | Contacts any third party? |
|---|---|---|
| **Self-hosted** (`SELF_HOSTED=true`) | No | No |
| **Air-gapped** (`CLAWMETRY_OFFLINE=1`) | No | No |
| **Local only** (no `clawmetry connect`) | Update check only | No |
| **Managed cloud** (`clawmetry connect`) | Yes — encrypted snapshots | No |

**No ClawMetry deployment contacts a third-party host for any reason.** Not a
CDN, not a font provider, not an analytics vendor, not an error tracker. There
is no Google Analytics, no Segment, no Sentry, no PostHog, no advertising or
tracking pixel anywhere in the product. Web assets are vendored into the
package and served from the local process; CI fails on any absolute `http(s)`
asset reference in a served page.

Destinations belonging to *your* agents (`api.anthropic.com`, `api.openai.com`
and similar) appear in this codebase only as strings used to attribute costs
and parse pricing. ClawMetry observes those calls; it does not make them.

---

## Deployment modes in detail

### Self-hosted (ClawMetry Enterprise)

Set `SELF_HOSTED=true` on the server. Node daemons point at it with
`CLAWMETRY_ENDPOINT=https://clawmetry.your-company.internal`.

**Outbound calls: none.** Node daemons talk only to your server. The server
talks to nothing. Telemetry, funnel analytics, public-IP lookup and update
checks are all suppressed — see the suppression gate below.

One optional exception, **off by default**: setting `CLAWMETRY_LICENSE_PING=1`
starts a daily POST to `https://app.clawmetry.com/api/license/ping` carrying
exactly this and nothing else:

```json
{"kind": "selfhosted_ping", "version": "0.12.727", "license": "<sub claim>", "tier": "pro", "ts": "..."}
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
The only outbound call is the PyPI version check described below.

### Managed cloud (after `clawmetry connect`)

The daemon pushes snapshots to `ingest.clawmetry.com`. Payloads are encrypted
client-side with AES-256-GCM; **the key never leaves your machine** and is not
recoverable by ClawMetry — the browser decrypts for display. See
[ARCHITECTURE.md](../ARCHITECTURE.md).

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

"Discretionary" excludes the deployment's own configured ingest endpoint — that
push is the product, and repointing it is what self-hosting means.

The gate **fails closed**: if the check itself raises (partial install, older
package), the call is suppressed rather than allowed. Covered by
`tests/test_egress_suppression.py`.

---

## Full destination table

### ClawMetry-operated

| Host | Purpose | When | Sends | Disable |
|---|---|---|---|---|
| `ingest.clawmetry.com` | Encrypted snapshot upload | After `clawmetry connect`, managed cloud only | AES-256-GCM ciphertext; key never transmitted. A node with no key skips the upload — content is never sent in the clear | Don't connect, or set `CLAWMETRY_ENDPOINT` |
| `ingest.clawmetry.com/ingest/heartbeat` | Node liveness + the fleet card's machine identity | Every few seconds after `clawmetry connect` | **Not encrypted**, by design — the cloud needs it to find the machine: hostname, OS name and version, CPU/RAM class, ClawMetry version, whether a key is configured. No prompts, replies, tool arguments or file contents | Don't connect, or set `CLAWMETRY_ENDPOINT` |
| `ingest.clawmetry.com/ingest/sessions` | Session rows for the cloud sessions list | After `clawmetry connect` | Structural fields in cleartext (ids, timestamps, token counts, cost, model, runtime) so the server can query them. The session **title** is content and travels encrypted alongside them | Don't connect, or set `CLAWMETRY_ENDPOINT` |
| `app.clawmetry.com` | OAuth/device claim, entitlement + tier resolution, pro wheel download | Managed cloud only | Account identifiers, license subject, version | `CLAWMETRY_ENDPOINT`, `SELF_HOSTED`, or `CLAWMETRY_OFFLINE` |
| `app.clawmetry.com/api/install` | First-run install counter | Once per version, managed cloud only | Anonymous install ID, version, OS, Python version, CI flag | `DO_NOT_TRACK=1`, `CLAWMETRY_NO_TELEMETRY=1`, `~/.clawmetry/notelemetry`, or any suppression condition |
| `app.clawmetry.com/api/admin/anon-event` | Anonymous funnel analytics | Managed cloud only | Anonymous event names | Any suppression condition |
| `app.clawmetry.com/api/license/ping` | Self-hosted license revocation + update check | **Off unless** `CLAWMETRY_LICENSE_PING=1` | Version, license subject, tier, timestamp | Leave unset (the default) |

### Third-party

| Host | Purpose | When | Disable |
|---|---|---|---|
| `pypi.org` | Version/update check against the public package index | Periodic, `CLAWMETRY_UPDATE_CHECK_SECS`. **Not contacted** by self-hosted, air-gapped or repointed installs — upgrades there go through your own change process | `CLAWMETRY_AUTO_UPDATE=0`, or any suppression condition |
| `api.ipify.org` | Public IP for one cosmetic startup banner line | Startup, managed cloud only | Any suppression condition |

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

* **The encryption key.** Generated locally, stored at `~/.clawmetry/`, never
  transmitted. Cloud snapshots are opaque to ClawMetry.
* **Your source code.** ClawMetry reads agent *transcripts and metadata*, not
  your repository.
* **Gateway and provider API keys.** Read to talk to your local gateway; never
  uploaded.
* **The DuckDB store** at `~/.clawmetry/clawmetry.duckdb`, unless you enable
  cloud sync — and then only as ciphertext.

---

## Reporting a discrepancy

Traffic to a host not listed here is a bug and is treated as a security issue.
See [SECURITY.md](../SECURITY.md) for how to report it privately.
