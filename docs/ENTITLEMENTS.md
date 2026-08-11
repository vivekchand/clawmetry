# Entitlements — what's free, what's paid, how gating works

ClawMetry is open-core. This OSS package is the **free** layer; a
closed-source companion package (`clawmetry-pro`) delivers the paid layer
and is fetched only when a valid license key or a cloud entitlement is
present. This document explains what the split is, how the resolver
decides, what "GRACE" means today, and what the `/api/entitlement` surface
and `clawmetry license` CLI actually return.

Everything below is grounded in code you can read: the resolver and its
constants live in [`clawmetry/entitlements.py`](../clawmetry/entitlements.py),
the offline key verifier in [`clawmetry/license.py`](../clawmetry/license.py),
and the HTTP surface in [`routes/entitlement.py`](../routes/entitlement.py).

> **TL;DR.** Nothing is enforced yet. The resolver runs in **grace mode**
> until a future release flips the default, so every check currently
> answers "allowed" no matter which tier resolved. Wiring the gate in now
> is a no-op by design — it lets the UI render the right locks/CTAs and
> lets the daemon report an accurate plan without changing behaviour for
> any current user.

---

## The open-core split

### FREE — always available in this OSS package

The FREE layer needs no key, no network call, and no account.

**Runtimes** (from `entitlements.FREE_RUNTIMES`):

- `openclaw` — OpenClaw agents
- `nemoclaw` — NVIDIA NemoClaw agents

`nemo_governance` (policy enforcement layered on top of any runtime) is a
separate **free feature**, not a runtime — see the feature list below.

**Chat-channel adapters** (all 23 are free; `entitlements.ALL_CHANNELS`):

Telegram, Signal, WhatsApp, Discord, Slack, IRC, iMessage, WebChat,
Google Chat, Microsoft Teams, BlueBubbles, Matrix, Mattermost, LINE,
Nostr, Twitch, Feishu, Zalo, Tlon, Synology Chat, Nextcloud Talk,
ClickClack, Buzz.

There is **no paid-channel tier** — every adapter unlocks on every plan.
What tiers govern is how many channels can be *active concurrently*
(see the capacity table below).

**Features** (`entitlements.FREE_FEATURES`):

`sessions`, `transcripts`, `usage`, `brain`, `flow`, `tracing`, `health`,
`logs`, `crons`, `channels`, `nemo_governance`, `overview`.

These map to the tabs and API surface listed in `README.md` and
`ARCHITECTURE.md`. If you can see it in `pip install clawmetry` on its
own, it's free.

### PAID — shipped in the `clawmetry-pro` package

The paid layer is not in this repository. It downloads separately when
either a self-hosted license key or a cloud plan resolves. The lists
below live here so the free UI can render locked rows with an accurate
"what would this unlock" preview.

**Additional runtimes** (`entitlements.PAID_RUNTIMES`):

`claude_code`, `codex`, `cursor`, `aider`, `goose`, `opencode`,
`qwen_code`, `hermes`, `picoclaw`, `nanoclaw`, `pi`, `deepagents`,
`n8n`, `antigravity`, `copilot`, `grok`, `qm`.

**Additional features**, split across three tiers:

| Bucket | Constant | Features |
|---|---|---|
| Starter | `STARTER_FEATURES` | `multi_runtime`, `fleet`, `cloud_sync`, `all_channels`, `approval_queue`, `budget_limits`, `per_runtime_health_timeline` |
| Pro-only | `PRO_ONLY_FEATURES` | `per_run_waste_flags`, `per_run_compare`, `error_triage`, `self_evolve`, `asset_registry`, `eval_suite`, `tool_policy`, `otel_export`, `custom_webhooks`, `custom_runtime_ingest`, `custom_alerts`, `alert_webhooks`, `anomaly_detection`, `cost_optimizer`, `compliance_pack` |
| Enterprise | `ENTERPRISE_FEATURES` | `siem_export`, `sso`, `audit_logs`, `rbac`, `air_gapped_license`, `custom_data_residency` |

Display labels for every feature live in `entitlements.FEATURE_LABELS`.

---

## Tiers

Tier identifiers (`entitlements.TIER_*`):

| Identifier | Label | Source | How you get it |
|---|---|---|---|
| `oss` | OSS | this package | default when nothing else resolves |
| `cloud_free` | Free | cloud plan cache | signed-up cloud account, no paid plan |
| `trial` | Trial | cloud plan cache | time-limited full-feature evaluation |
| `cloud_starter` | Starter | cloud plan cache | paid cloud plan |
| `cloud_pro` | Pro | cloud plan cache | paid cloud plan |
| `pro` | Self-hosted Pro | local license key | Ed25519-signed key on disk |
| `enterprise` | Enterprise | license key or cloud | contract-level plan |

### Per-tier feature grants

| Tier | Features granted |
|---|---|
| `oss` | `FREE_FEATURES` only |
| `cloud_free` | `FREE_FEATURES` only |
| `cloud_starter` | `FREE_FEATURES ∪ STARTER_FEATURES` |
| `trial` | `FREE_FEATURES ∪ PAID_FEATURES` |
| `cloud_pro` | `FREE_FEATURES ∪ PAID_FEATURES` |
| `pro` | `FREE_FEATURES ∪ PAID_FEATURES` |
| `enterprise` | everything, including `ENTERPRISE_FEATURES` |

### Per-tier capacity caps

| Tier | Retention (days) | Concurrent channels | Nodes |
|---|---|---|---|
| `oss` | 7 | 3 | 1 |
| `cloud_free` | 7 | 3 | 1 |
| `trial` | 30 | unlimited | unlimited (license-bound) |
| `cloud_starter` | 30 | unlimited | unlimited (license-bound) |
| `cloud_pro` | 90 | unlimited | unlimited (license-bound) |
| `pro` | 90 | unlimited | unlimited (license-bound) |
| `enterprise` | unlimited | unlimited | unlimited (license-bound) |

"unlimited (license-bound)" means the actual node cap for that install
comes off the license payload or cached cloud plan, not the static tier
ceiling. Constants: `_TIER_RETENTION_DAYS`, `_TIER_CHANNEL_LIMIT`,
`_TIER_NODE_LIMIT`.

`CLAWMETRY_RETENTION_DAYS` overrides the tier default at runtime for
retention only.

---

## Resolution order

`entitlements.get_entitlement()` returns an `Entitlement` dataclass with
`tier`, `source`, `node_limit`, `expiry`, `features`, `runtimes`, and
`grace`. Sources are tried in this order — first hit wins, every miss
falls through silently:

1. **Local signed license file** — `~/.clawmetry/license.key`. Verified
   offline with Ed25519 by `clawmetry.license`; the public key ships
   embedded in this OSS package. Missing → skip. Malformed → warn and
   skip. Expired → warn and skip. Never raises.
2. **Cached cloud plan** — `~/.clawmetry/cloud_plan.json`, written by
   the sync daemon after each heartbeat that returned a plan payload.
   Same defensive rules.
3. **OSS free** — the built-in fallback (`TIER_OSS`, `FREE_FEATURES`,
   `FREE_RUNTIMES`).

The result is cached for `_CACHE_TTL_SECS` (60s). `POST
/api/entitlement/refresh` invalidates the cache and re-resolves.

---

## GRACE vs ENFORCE

Everything in the entitlement engine is currently wired but **inert**.

`Entitlement.grace` defaults to `True`, and `entitlements.is_enforced()`
reads the `CLAWMETRY_ENFORCE` environment variable — `1`, `true`, `yes`,
`on` all count as on. The default is off. While off, every `allows_*`
call returns `True` regardless of the resolved tier, so:

- Users on the OSS tier see every feature the same way they did before.
- The dashboard can still render lock icons and "would upgrade to Pro"
  hints, driven by the same resolver, without any endpoint actually
  returning 402/403.
- The daemon can still report an accurate resolved tier via
  `/api/entitlement`.

`CLAWMETRY_ENFORCE_AT` optionally carries the announced enforce-at
moment (ISO date, ISO datetime, or epoch seconds) so the UI can show
"enforced in N days" copy ahead of the flip. It has no effect on
behaviour — the flip itself happens when a future release changes the
default of `CLAWMETRY_ENFORCE`.

**Nothing in this document changes user behaviour today.** It documents
what the engine *will* enforce once the operator flips the switch.

---

## The `/api/entitlement` surface

`routes/entitlement.py` exposes the resolved entitlement and a large
family of preview/diff/batch helpers. The stable everyday endpoints are:

| Endpoint | Purpose |
|---|---|
| `GET /api/entitlement` | Resolved entitlement for this install — the `Entitlement.to_dict()` payload (tier, tier_label, tier_rank, source, node_limit, expiry, grace, enforced, enforce_at, runtimes, features, locked_runtimes, locked_features, next-tier diff, …). |
| `POST /api/entitlement/refresh` | Invalidate the 60s cache and re-resolve. Returns the same shape. |
| `GET /api/entitlement/upgrade-diff` | What the next tier would add. |
| `GET /api/entitlement/downgrade-diff` | What the previous tier would remove. |
| `GET /api/entitlement/tier-diff?to=<tier>` | Diff between the current tier and any target. |
| `GET /api/entitlement/lock-reason?feature=<f>` | Why a specific feature is locked and the minimum tier that would unlock it. |
| `GET /api/entitlement/required-tier?feature=<f>` | Cheapest tier that includes the given feature/runtime/channel-count/etc. |

Beyond these there is a large family of preview / batch / capacity /
"at-tier" / rollup (`has-all`, `missing-all`) / row-detail
complement (`missing-features`, `missing-runtimes`) endpoints that
let a UI answer questions like "what does tier X look like at N
channels", "which tiers are affordable at this node count", "what
does the path from tier A to tier B unlock at each step", "does the
resolved install grant this whole bundle in one boolean fold" and
"what's blocking the upgrade off ONE per-axis denial payload". They
all read the same in-memory tier matrix and never mutate state. See
`routes/entitlement.py` for the full list.

Every endpoint is defensive: a resolver failure falls back to the OSS-
free snapshot (identical shape) rather than 500-ing, so a UI can rely
on the response shape being stable.

---

## The `clawmetry license` CLI

Two spellings, same effect: `clawmetry activate <KEY>` is a shortcut
for `clawmetry license activate <KEY>`. Every subcommand accepts
`--json` for scripting; the human table and the JSON envelope are
kept in step.

| Command | What it does |
|---|---|
| `clawmetry license` | Show the current plan, license validity, expiry, node cap. |
| `clawmetry license activate <KEY>` | Verify the key offline and install it at `~/.clawmetry/license.key`. Restart the daemon to load `clawmetry-pro`. |
| `clawmetry license verify <KEY>` | **Dry-run** — verify a key offline and print what it *would* unlock without writing anything to disk. Useful for support and pre-flight. |
| `clawmetry license deactivate` | Remove the license file. Next restart reverts to OSS. |
| `clawmetry license fingerprint` | Print the SHA-256 fingerprint of the embedded public key so you can compare it against the canonical value at https://clawmetry.com/security and confirm your install carries the genuine verification key. |
| `clawmetry activate <KEY>` | Shortcut. Same as `license activate`; same `--json` envelope. |

**How verification works.** `clawmetry.license` uses the `cryptography`
package (already a hard dependency of this repo — no new deps) to
verify a compact `header.payload.signature` token with a bundled
Ed25519 public key. The private key lives on the license server;
signatures are checked entirely offline on your machine. A key that
fails signature verification, has a `nbf` in the future, or an `exp`
in the past is rejected — the CLI prints a status line, the JSON
envelope reports `ok: false`, and the exit code is non-zero.

---

## What happens when a lock is hit

Once `CLAWMETRY_ENFORCE=1` is set (or once the future release flips the
default), a locked endpoint returns a JSON body describing:

- what was requested (feature, runtime, or capacity axis and value),
- the tier that resolved,
- the minimum tier that would satisfy the request, and
- the upgrade path the UI should render.

Today, with grace on, none of that fires — every endpoint responds
exactly as it did before entitlements existed. This document is here
so that when the switch is flipped, no user has to reverse-engineer
what changed.

---

## Related code

| File | What lives there |
|---|---|
| [`clawmetry/entitlements.py`](../clawmetry/entitlements.py) | Runtime/feature/tier constants, `Entitlement` dataclass, `get_entitlement()`, `is_enforced()`, capacity + tier-diff helpers. |
| [`clawmetry/license.py`](../clawmetry/license.py) | Ed25519 offline verification, `activate` / `deactivate` / `inspect_key`, `current_license_info`, `pubkey_info`. |
| [`clawmetry/extensions.py`](../clawmetry/extensions.py) | Plugin loader for `clawmetry-pro`. |
| [`routes/entitlement.py`](../routes/entitlement.py) | `bp_entitlement` — the full `/api/entitlement` HTTP surface. |
| [`clawmetry/_gate.py`](../clawmetry/_gate.py), [`clawmetry/_paywall.py`](../clawmetry/_paywall.py) | Gate decorator and paywall-event bookkeeping used by feature routes. |
