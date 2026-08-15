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
`n8n`, `antigravity`, `copilot`, `grok`, `qm`, `deepseek_harness`.

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
'at-tier' / rollup (`has-all`, `missing-all`, `missing-all-at`) /
row-detail complement (`missing-features`, `missing-runtimes`) /
multi-bundle boolean-fold (`has-features-bundle-batch`,
`has-runtimes-bundle-batch`) endpoints that let a UI answer questions
like "what does tier X look like at N channels", "which tiers are
affordable at this node count", "what does the path from tier A to tier B
unlock at each step", "does the resolved install grant this whole bundle
in one boolean fold" and "what's blocking the upgrade off ONE per-axis
denial payload". They all read the same in-memory tier matrix and never
mutate state. See `routes/entitlement.py` for the full list.

### Boolean-fold bundle-batch endpoints

`POST /api/entitlement/has-features-bundle-batch` and `POST
/api/entitlement/has-runtimes-bundle-batch` fold N caller-supplied
feature/runtime bundles to N `has_*` booleans in one round-trip — the
boolean-fold sibling of `/min-tier-for-features-batch` /
`/min-tier-for-runtimes-batch` on the same bundle axis.

**Request body** (byte-identical to the `min-tier-for-*-batch` siblings):

```json
{"bundles": [["fleet", "sso"], ["otel_export"], []]}
```

A bare list-of-strings is treated as one bundle (single-bundle shorthand).
400 on missing / non-list / empty `bundles` key.

**Response envelope** (6 keys):

```json
{
  "bundles":          [...],
  "count":            3,
  "current_tier":     "oss",
  "current_tier_rank": 0,
  "grace":            true,
  "enforced":         false
}
```

**Per-bundle row** (5 keys; `has_features` / `has_runtimes` mirrors the
singular scalar's return-slot name):

```json
{
  "features":     ["fleet", "sso"],
  "unknown":      [],
  "kind":         "features",
  "count":        2,
  "has_features": true
}
```

The `features`/`runtimes`, `unknown`, `kind`, and `count` keys are
byte-identical to the corresponding `/min-tier-for-*-batch` rows so a UI
can render "granted right now?" and "cheapest tier that grants it?"
side-by-side per bundle from two calls.

**Behaviour notes:**

- An unknown token anywhere in a bundle collapses that row's `has_*` to
  `false` (matches the singular `has_features` / `has_runtimes`
  typo-at-callsite posture — a typo surfaces via `unknown[]` instead of
  silently appearing granted).
- Empty, all-unknown, `None`, and non-iterable bundles surface as a stable
  row with `has_*: false`.
- Runtime aliases are canonicalised per-bundle before the membership check
  (`claude-code` → `claude_code`); unknown ids echo raw into `unknown[]`.
- Never raises: per-bundle failures short-circuit to the empty row shape so
  the batch keeps building.
- Ships in GRACE mode — `has_*` reads the live grant via the same resolver
  as the singular scalar. A paid feature returns `true` in grace; FREE
  runtimes return `true` on the live install regardless of rollout state.

Every endpoint is defensive: a resolver failure falls back to the OSS-
free snapshot (identical shape) rather than 500-ing, so a UI can rely
on the response shape being stable.

### Row-detail batch endpoint: `missing-all-at-batch`

`GET /api/entitlement/missing-all-at-batch?tiers=oss,cloud_pro,...&features=a,b&runtimes=x,y&channels=N&retention_days=N&nodes=N`

Batch what-if row-detail complement of `has-all-at-batch`. Fixes ONE
5-axis mixed bundle and sweeps across N caller-supplied `perspective_tiers`,
returning per-axis denial detail for each tier in one round-trip. Answers
"out of {fleet, sso, claude_code, 100 channels, 90d retention, 100 nodes},
which axes are still blocked at OSS vs Cloud Starter vs Cloud Pro vs
Enterprise?" for a paywall diagnostics matrix without N separate calls to
`missing_all_at()`.

**Grace-independent by construction**: reads static per-tier grant tables
via `_hypothetical_entitlement` on the feature/runtime axes and
`_TIER_CHANNEL_LIMIT` / `_TIER_RETENTION_DAYS` / `_TIER_NODE_LIMIT` on the
capacity axes — so the answer is byte-identical under grace vs enforce for
the same inputs. This differs from the LIVE `missing-all` endpoint (which
reads the resolver's grace pass-through).

**Per-tier row:** mirrors `has_all_at_batch` on the axis-echo slots with a
per-axis `missing` sub-dict instead of a single `has_all_at` bool:

```json
{
  "tier":           "oss",
  "tier_label":     "OSS",
  "tier_rank":      0,
  "missing": {
    "features":       ["fleet"],
    "runtimes":       ["claude_code"],
    "channels":       100,
    "retention_days": 90,
    "nodes":          100
  }
}
```

The scalar is `clawmetry.entitlements.missing_all_at_batch(perspective_tiers, *, features, runtimes, channels, retention_days, nodes)`.


### Path-walk endpoint: `has-all-at-path`

`GET /api/entitlement/has-all-at-path?from=<id>&to=<id>&features=a,b&runtimes=x,y&channels=N&retention_days=N&nodes=N`

Aggregate mixed-axis path-shaped boolean-fold. Fixes ONE 5-axis bundle
and sweeps across every purchasable rung between `from` and `to`, returning
one row per rung with the aggregate `has_all_at` fold at that rung. Answers
"at which tier does this whole 5-axis bundle unlock?" in one round-trip.

Per-rung `has_all_at` byte-equals `has_all_at()` for the same (rung, bundle)
pair. **Grace-independent by construction**: reads static per-tier grant
tables via `_hypothetical_entitlement` on the feature/runtime axes and
`_TIER_CHANNEL_LIMIT` / `_TIER_RETENTION_DAYS` / `_TIER_NODE_LIMIT` on the
capacity axes — so the answer is byte-identical under grace vs enforce for
the same inputs.

**Per-rung row:** `{ tier, tier_label, tier_rank, has_all_at }`.

**Envelope keys:** `from`, `from_label`, `from_rank`, `to`, `to_label`,
`to_rank`, `direction` (`upgrade` | `downgrade` | `lateral` | `identity` |
`unknown`), `features`, `runtimes`, `channels`, `retention_days`, `nodes`,
`unknown_features`, `unknown_runtimes`, `supplied_axes`, `supplied_count`,
`path`, `path_length`, `allowed_count`, `all_allowed`, `any_allowed`,
`required_tier`, `required_tier_label`, `required_tier_rank`, plus the
standard resolver envelope (`current_tier`, `current_tier_rank`, `grace`,
`enforced`).

Unknown or missing endpoints return 200 with `path=[]` and
`direction="unknown"` (never 4xxs or 5xxs). Ships in GRACE mode.

The scalar is `clawmetry.entitlements.has_all_at_path(from_tier, to_tier, *, features, runtimes, channels, retention_days, nodes)`.

### Row-detail path-walk endpoint: `missing-all-at-path`

`GET /api/entitlement/missing-all-at-path?from=<id>&to=<id>&features=a,b&runtimes=x,y&channels=N&retention_days=N&nodes=N`

Aggregate mixed-axis path-shaped row-detail complement of `has-all-at-path`.
Fixes ONE 5-axis bundle and sweeps across every purchasable rung between
`from` and `to`, returning per-axis denial detail at each rung in one
round-trip. Answers "at which rung does each per-axis slot in this 5-axis
bundle clear?" for an upgrade-walkthrough tooltip without first calling
`/tier-path` for the rung list and then N calls to `missing_all_at()`.

**Grace-independent by construction**: reads static per-tier grant tables
via `_hypothetical_entitlement` on the feature/runtime axes and
`_TIER_CHANNEL_LIMIT` / `_TIER_RETENTION_DAYS` / `_TIER_NODE_LIMIT` on the
capacity axes — so the answer is byte-identical under grace vs enforce for
the same inputs.

**Per-rung row:**

```json
{
  "tier":       "cloud_starter",
  "tier_label": "Starter",
  "tier_rank":  2,
  "missing": {
    "features":       ["sso"],
    "runtimes":       [],
    "channels":       null,
    "retention_days": null,
    "nodes":          null
  }
}
```

Complement invariant with `has-all-at-path`: `any(row["missing"].values())`
byte-equals `not row["has_all_at"]` on the paired boolean-fold row for
every fully-parseable bundle.

Unknown or missing endpoints return 200 with `path=[]` (never 4xxs or 5xxs).
Ships in GRACE mode.

The scalar is `clawmetry.entitlements.missing_all_at_path(from_tier, to_tier, *, features, runtimes, channels, retention_days, nodes)`.

### Bundle path-walk boolean-fold endpoint: `has-all-bundle-at-path`

`POST /api/entitlement/has-all-bundle-at-path?from=<id>&to=<id>`

Path-shaped bundle sibling of `has-all-bundle-at` (singular perspective)
and bundle-shaped counterpart of `has-all-at-path` (kwargs-shaped path
walker). Fixes ONE 5-axis bundle and sweeps across every purchasable
rung between `from` and `to`, returning per-rung aggregate boolean-fold
in one round-trip. Answers "at which rung does this WHOLE 5-axis bundle
unlock?" straight from the bundle dict without first normalising it by
hand and calling `/has-all-at-path`, or first calling `/tier-path` and
then N calls to `/has-all-bundle-at`.

**Grace-independent by construction**: reads static per-tier grant
tables via `_hypothetical_entitlement` on the feature/runtime axes and
`_TIER_CHANNEL_LIMIT` / `_TIER_RETENTION_DAYS` / `_TIER_NODE_LIMIT` on
the capacity axes — so the answer is byte-identical under grace vs
enforce for the same inputs.

**Request body** (byte-identical to `has-all-bundle-at` — wrapped or
bare-dict shorthand):

```json
{"bundle": {"features": ["fleet"], "runtimes": ["claude_code"],
            "channels": 5, "retention_days": 30, "nodes": 2}}
```

**Per-rung row:**

```json
{
  "tier":           "cloud_pro",
  "tier_label":     "Cloud Pro",
  "tier_rank":      3,
  "features":       ["fleet"],
  "runtimes":       ["claude_code"],
  "channels":       5,
  "retention_days": 30,
  "nodes":          2,
  "has_all_at":     true
}
```

400 on missing / non-object `bundle`. Unknown or missing endpoints
return 200 with `path=[]` (never 4xxs or 5xxs). Ships in GRACE mode.

The scalar is `clawmetry.entitlements.has_all_bundle_at_path(from_tier, to_tier, bundle)`.

### Bundle path-walk row-detail endpoint: `missing-all-bundle-at-path`

`POST /api/entitlement/missing-all-bundle-at-path?from=<id>&to=<id>`

Row-detail path-shaped bundle sibling of the boolean-fold
`has-all-bundle-at-path` and bundle-shaped counterpart of
`missing-all-at-path`. Fixes ONE 5-axis bundle and sweeps across every
purchasable rung between `from` and `to`, returning per-axis denial
detail at each rung in one round-trip. Answers "at which rung does
each per-axis slot in this 5-axis bundle clear?" straight from the
bundle dict without first normalising it by hand and calling
`/missing-all-at-path`, or first calling `/tier-path` and then N calls
to the singular row-detail per-perspective seat.

**Grace-independent by construction** — same static-table read pattern
as the paired boolean-fold endpoint.

**Request body**: byte-identical to `has-all-bundle-at-path` above.

**Per-rung row:**

```json
{
  "tier":           "cloud_starter",
  "tier_label":     "Starter",
  "tier_rank":      2,
  "features":       ["fleet"],
  "runtimes":       ["claude_code"],
  "channels":       5,
  "retention_days": 30,
  "nodes":          2,
  "missing": {
    "features":       ["fleet"],
    "runtimes":       [],
    "channels":       null,
    "retention_days": null,
    "nodes":          null
  }
}
```

Complement invariant with `has-all-bundle-at-path`: per rung,
`any(row["missing"].values())` byte-equals `not row["has_all_at"]` on
the paired boolean-fold row for every fully-parseable bundle.

400 on missing / non-object `bundle`. Unknown or missing endpoints
return 200 with `path=[]` (never 4xxs or 5xxs). Ships in GRACE mode.

The scalar is `clawmetry.entitlements.missing_all_bundle_at_path(from_tier, to_tier, bundle)`.

### Batch path-walk endpoint: `has-all-at-path-batch`

`GET /api/entitlement/has-all-at-path-batch?from=<id>&to=a,b,c&features=x,y&runtimes=p,q&channels=N&retention_days=N&nodes=N`

Aggregate mixed-axis batch companion of `has-all-at-path`. Fixes ONE
5-axis bundle and sweeps across every purchasable rung between `from`
and each of the N candidate `to` tiers in ONE round-trip, returning
per-destination path lists of aggregate `has_all_at` fold rows. Answers
"from my current rung, here are 3 tiers I'm considering: for the WHOLE
5-axis bundle show me at which rung this bundle unlocks along every
candidate path" for an upgrade-comparison matrix without N calls to
`has-all-at-path` or 5·N calls to the per-axis path-batch endpoints
plus a client-side AND-chain per rung per destination.

Per-destination `path` row byte-equals `has-all-at-path`'s `.path` for
the same `(from, to, bundle)` triple. Per-destination path lengths can
legitimately differ (the rungs walked depend on the destination).
**Grace-independent by construction** — same static-table walk as the
singular endpoint applied per destination.

**Per-destination row:**

```json
{
  "to":            "pro",
  "to_label":      "Self-hosted Pro",
  "to_rank":       2,
  "direction":     "upgrade",
  "path":          [{"tier": "cloud_starter", "tier_label": "Starter", "tier_rank": 1, "has_all_at": true}],
  "path_length":   1,
  "allowed_count": 1,
  "all_allowed":   true,
  "any_allowed":   true
}
```

**Envelope keys:** `from`, `from_label`, `from_rank`, `features`,
`runtimes`, `channels`, `retention_days`, `nodes`, `unknown_features`,
`unknown_runtimes`, `unknown_tiers`, `supplied_axes`, `supplied_count`,
`tiers`, `required_tier`, `required_tier_label`, `required_tier_rank`,
plus the standard resolver envelope (`current_tier`,
`current_tier_rank`, `grace`, `enforced`).

Runtime-alias canonicalisation (`claude-code` → `claude_code`) is
applied per token upstream. Unknown feature/runtime tokens OR non-int
capacity collapse EVERY rung of EVERY destination to `has_all_at=False`
at the endpoint layer (matches the singular `has-all-at-path`
typo-`False` posture). Missing/blank/unknown `from` or an empty /
all-unknown destination CSV returns 200 with `tiers=[]` (never 4xxs or
5xxs). `trial` IS accepted as a destination via the lateral / identity
branches. Ships in GRACE mode.

The scalar is `clawmetry.entitlements.has_all_at_path_batch(from_tier, to_tiers, *, features, runtimes, channels, retention_days, nodes)`.

### Batch row-detail path-walk endpoint: `missing-all-at-path-batch`

`GET /api/entitlement/missing-all-at-path-batch?from=<id>&to=a,b,c&features=x,y&runtimes=p,q&channels=N&retention_days=N&nodes=N`

Aggregate mixed-axis batch companion of `missing-all-at-path` and
row-detail complement of `has-all-at-path-batch` at the batch-path
layer. Fixes ONE 5-axis bundle and sweeps across every purchasable rung
between `from` and each of the N candidate `to` tiers in ONE round-
trip, returning per-destination path lists of aggregate per-axis
`missing` row-detail rows. Answers "from my current rung, here are 3
tiers I'm considering: for the WHOLE 5-axis bundle show me which
per-axis slots are still locked at every rung climbed to reach each"
for an upgrade-comparison matrix without N calls to `missing-all-at-path`.

**Grace-independent by construction** — same static-table walk as the
singular endpoint applied per destination.

**Per-destination row:**

```json
{
  "to":           "pro",
  "to_label":     "Self-hosted Pro",
  "to_rank":      2,
  "direction":    "upgrade",
  "path":         [
    {"tier": "cloud_starter", "tier_label": "Starter", "tier_rank": 1,
     "missing": {"features": ["sso"], "runtimes": [], "channels": null, "retention_days": null, "nodes": null}}
  ],
  "path_length":  1,
  "denied_count": 1,
  "all_denied":   true,
  "any_denied":   true
}
```

**Envelope keys:** identical to `has-all-at-path-batch` on the
axis-echo / resolver slots; per-destination rollup slots use
`denied_count` / `all_denied` / `any_denied` instead of the
boolean-fold `allowed_count` / `all_allowed` / `any_allowed`.

Complement invariant with `has-all-at-path-batch`: per destination per
rung, `any(row["missing"].values())` byte-equals `not row["has_all_at"]`
on the paired boolean-fold row for every fully-parseable bundle.
Non-int capacity is the deliberate divergence: the row-detail slot
surfaces the raw string on every rung while the boolean-fold slot
collapses to `False`.

Missing/blank/unknown `from` or an empty / all-unknown destination CSV
returns 200 with `tiers=[]` (never 4xxs or 5xxs). Ships in GRACE mode.

The scalar is `clawmetry.entitlements.missing_all_at_path_batch(from_tier, to_tiers, *, features, runtimes, channels, retention_days, nodes)`.

### Source-batch path-walk endpoint: `has-all-from-path-batch`

`GET /api/entitlement/has-all-from-path-batch?from=a,b,c&to=<id>&features=x,y&runtimes=p,q&channels=N&retention_days=N&nodes=N`

Mirror-direction source-batch sibling of `has-all-at-path-batch`
(destination-batch): where the destination-batch fixes ONE source and
fans out over N candidate destinations, this fixes ONE destination and
fans out over N candidate sources in ONE round-trip. Answers "for each
of the tiers my fleet currently sits on, walking up to Enterprise for
the WHOLE 5-axis bundle, at which rung does this bundle unlock along
every candidate ladder?" for a source-side upgrade-comparison matrix
without N calls to `has-all-at-path` or 5·N calls to the per-axis
source-batch endpoints plus a client-side AND-chain per rung per source.

Per-source `path` row byte-equals `has-all-at-path`'s `.path` for the
same `(from, to, bundle)` triple. Per-source path lengths can
legitimately differ (the rungs walked depend on the source).
**Grace-independent by construction** — same static-table walk as the
singular endpoint applied per source.

**Per-source row:**

```json
{
  "from":          "oss",
  "from_label":    "OSS",
  "from_rank":     0,
  "direction":     "upgrade",
  "path":          [{"tier": "cloud_starter", "tier_label": "Starter", "tier_rank": 1, "has_all_at": true}],
  "path_length":   1,
  "allowed_count": 1,
  "all_allowed":   true,
  "any_allowed":   true
}
```

**Envelope keys:** `to`, `to_label`, `to_rank`, `features`, `runtimes`,
`channels`, `retention_days`, `nodes`, `unknown_features`,
`unknown_runtimes`, `unknown_tiers`, `supplied_axes`, `supplied_count`,
`tiers`, `required_tier`, `required_tier_label`, `required_tier_rank`,
plus the standard resolver envelope (`current_tier`,
`current_tier_rank`, `grace`, `enforced`).

Runtime-alias canonicalisation (`claude-code` → `claude_code`) is
applied per token upstream. Unknown feature/runtime tokens OR non-int
capacity collapse EVERY rung of EVERY source to `has_all_at=False` at
the endpoint layer (matches the singular `has-all-at-path` typo-`False`
posture). Missing/blank/unknown `to` or an empty / all-unknown source
CSV returns 200 with `tiers=[]` (never 4xxs or 5xxs). `trial` IS
accepted as a source via the lateral / identity branches. Ships in
GRACE mode.

The scalar is `clawmetry.entitlements.has_all_from_path_batch(from_tiers, to_tier, *, features, runtimes, channels, retention_days, nodes)`.

### Source-batch row-detail path-walk endpoint: `missing-all-from-path-batch`

`GET /api/entitlement/missing-all-from-path-batch?from=a,b,c&to=<id>&features=x,y&runtimes=p,q&channels=N&retention_days=N&nodes=N`

Mirror-direction source-batch sibling of `missing-all-at-path-batch`
(destination-batch) and row-detail complement of
`has-all-from-path-batch` at the source-batch path layer. Fixes ONE
destination and fans out over N candidate sources in ONE round-trip,
returning per-source path lists of aggregate per-axis `missing` row-
detail rows. Answers "for each of the tiers my fleet currently sits on,
walking toward Enterprise for the WHOLE 5-axis bundle, which per-axis
slots are still locked at every rung climbed to reach it?" for a
source-side upgrade-comparison matrix without N calls to
`missing-all-at-path`.

**Grace-independent by construction** — same static-table walk as the
singular endpoint applied per source.

**Per-source row:**

```json
{
  "from":         "oss",
  "from_label":   "OSS",
  "from_rank":    0,
  "direction":    "upgrade",
  "path":         [
    {"tier": "cloud_starter", "tier_label": "Starter", "tier_rank": 1,
     "missing": {"features": ["sso"], "runtimes": [], "channels": null, "retention_days": null, "nodes": null}}
  ],
  "path_length":  1,
  "denied_count": 1,
  "all_denied":   true,
  "any_denied":   true
}
```

**Envelope keys:** identical to `has-all-from-path-batch` on the
axis-echo / resolver slots; per-source rollup slots use `denied_count`
/ `all_denied` / `any_denied` instead of the boolean-fold
`allowed_count` / `all_allowed` / `any_allowed`.

Complement invariant with `has-all-from-path-batch`: per source per
rung, `any(row["missing"].values())` byte-equals `not row["has_all_at"]`
on the paired boolean-fold row for every fully-parseable bundle.
Non-int capacity is the deliberate divergence: the row-detail slot
surfaces the raw string on every rung while the boolean-fold slot
collapses to `False`.

Missing/blank/unknown `to` or an empty / all-unknown source CSV returns
200 with `tiers=[]` (never 4xxs or 5xxs). Ships in GRACE mode.

The scalar is `clawmetry.entitlements.missing_all_from_path_batch(from_tiers, to_tier, *, features, runtimes, channels, retention_days, nodes)`.

### Bundle-batch perspective row-detail endpoint: `missing-all-bundle-batch-at`

`POST /api/entitlement/missing-all-bundle-batch-at?tier=<perspective>`

Hypothetical-perspective row-detail sibling of `has-all-bundle-batch-at`
(boolean fold) and `missing-all-bundle-batch` (LIVE row detail). Folds N
caller-supplied 5-axis bundles to N per-axis `missing` dicts scoped by a
caller-supplied `perspective_tier` in one round-trip. Answers "which axes
of each bundle would tier `<perspective>` NOT grant?" for a pricing-matrix
walkthrough without N separate calls to `missing_all_at()`.

**Grace-independent by construction**: reads static per-tier grant tables
via `_hypothetical_entitlement` on the feature/runtime axes and
`_TIER_CHANNEL_LIMIT` / `_TIER_RETENTION_DAYS` / `_TIER_NODE_LIMIT` on the
capacity axes — so grace vs enforce yields byte-identical row bodies.
At `tier=oss`, a paid-feature bundle reports `missing.features=["fleet"]`
even in grace, whereas the LIVE `missing-all-bundle-batch` reports
`missing.features=[]` for the same bundle via grace pass-through.

**Request body** (byte-identical to `missing-all-bundle-batch` and
`has-all-bundle-batch-at`):

```json
{"bundles": [{"features": ["fleet"], "runtimes": ["claude_code"]}, {"channels": 5}]}
```

A bare dict is treated as one bundle (single-bundle shorthand).

**Response envelope** (9 keys):

```json
{
  "perspective_tier":       "cloud_pro",
  "perspective_tier_label": "Cloud Pro",
  "perspective_tier_rank":  4,
  "bundles":                [...],
  "count":                  2,
  "current_tier":           "oss",
  "current_tier_rank":      0,
  "grace":                  true,
  "enforced":               false
}
```

**Per-bundle row:** mirrors `has-all-bundle-batch-at` byte-for-byte on the
axis-echo slots (`features`, `runtimes`, `channels`, `retention_days`,
`nodes`) with the fold slot swapped from `has_all_at` bool to a per-axis
`missing` dict:

```json
{
  "features":       ["fleet"],
  "runtimes":       ["claude_code"],
  "channels":       null,
  "retention_days": null,
  "nodes":          null,
  "missing": {
    "features":       ["fleet"],
    "runtimes":       [],
    "channels":       null,
    "retention_days": null,
    "nodes":          null
  }
}
```

Complement invariant with `has-all-bundle-batch-at`: `any(row["missing"].values())`
strictly negates the paired `has_all_at` for every fully-parseable bundle
on a valid perspective.

- **400** on missing/blank `tier=`, missing/empty/non-list `bundles`
- **404** on unknown `tier=` (body carries `which=tier`)
- Never 5xxs.

Ships in GRACE mode. The scalars are
`clawmetry.entitlements.missing_all_bundle_batch_at(perspective_tier, bundles)`
and the private `_missing_all_bundle_row_at(perspective_tier, bundle)`.

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
