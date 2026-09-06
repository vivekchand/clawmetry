# Trial-end hard block

> **Status: OSS-side enforcement shipped default-ON as of 2026-08-06, corrected 2026-08-06 to exempt the free tier. Cloud-side email + heartbeat payload extensions land alongside. Legitimate paying customers with valid signed licenses are unaffected. A plain OSS/cloud_free install that never had a trial or license is ALSO unaffected: only a source that was actually on a paid or trial tier and has since passed its expiry hits the block.**
>
> This document is the design-note for the paywall enforcement layer added
> alongside [`clawmetry/trial_enforcement.py`](../clawmetry/trial_enforcement.py).
> Its companion, [`docs/ENTITLEMENTS.md`](./ENTITLEMENTS.md), documents the
> tier + resolver model. This file is only about what happens *when* the
> resolver reports a lapsed paid/trial install.

## What ships in OSS today

**Default ON, scoped to a lapsed paid/trial state only.** An install whose
entitlement resolves to a source that WAS on a paid or trial tier and has
now passed its `expiry` will hit the block. Explicitly set
`CLAWMETRY_HARD_BLOCK=0` (or `false` / `no` / `off`) to opt out, kept as a
support lever for the rare case of a legitimate paying customer whose
license file corrupted mid-renewal. Under default-ON, a ClawMetry install
in the expired state will:

1. Return HTTP `402 Payment Required` with header `X-Clawmetry-Trial-Blocked: 1`
   for **every** request outside the small allowlist defined in
   [`clawmetry/trial_enforcement.py`](../clawmetry/trial_enforcement.py).
   The 402 body is stable JSON:

   ```json
   {
     "hard_blocked": true,
     "tier": "trial",
     "source": "license",
     "expired": true,
     "expiry": 1785937657.06,
     "days_until_expiry": 0,
     "reason": "Your ClawMetry trial has ended.",
     "upgrade_url": "https://app.clawmetry.com/upgrade",
     "activation_endpoint": "/api/license/activate",
     "refresh_endpoint": "/api/trial/refresh-license",
     "status_endpoint": "/api/trial/status"
   }
   ```

   A plain OSS/`cloud_free` install (`tier: "oss"`, `source: "oss"`, never
   entitled) never reaches this block: `is_hard_blocked()` returns `False`
   for it regardless of `CLAWMETRY_HARD_BLOCK`. Corrected 2026-08-06 (was
   shipped blocking this case too for a few hours; live-verified before the
   fix that a fresh `pip install clawmetry` with no license/trial never
   finished booting, since every `/api/*` call it depends on 402'd).

2. Render a **full-viewport, un-dismissable modal** (`static/js/app.js` top-
   of-file IIFE, `#cm-hard-block-overlay`) that shows the block reason, a
   "Continue to payment →" CTA, and a paste-in license-key field that hits
   `/api/license/activate` directly. The CTA does NOT just link to the
   generic `upgrade_url`: on click it POSTs `/api/trial/checkout`, which
   resolves the best payment destination for THIS install:

   1. **Live Stripe Checkout Session** — the account is already known
      locally (the node's `api_key`), so the route asks the cloud
      (`POST /api/billing/checkout-session`, `X-Api-Key` auth) to mint a
      per-account Checkout Session and sends the browser straight to the
      card form (`source: "session"`).
   2. **Heartbeat-cached `checkout_url`** when the live mint fails
      (`source: "cached"`).
   3. **Generic `upgrade_url`** as the last resort (`source: "upgrade"`).

   The endpoint always answers HTTP 200 with a usable URL — the CTA never
   dead-ends. After the click the overlay polls `/api/trial/refresh-license`
   every 5s (for up to 10 minutes) so the dashboard unlocks within seconds
   of the license landing, with no key to copy-paste.

   Cross-process plumbing: the daemon persists heartbeat
   `{upgrade_url, checkout_url}` into `~/.clawmetry/trial_state.json`
   (`sync.py::_persist_trial_state_to_disk`), which
   `trial_enforcement.persisted_trial_state()` reads from the dashboard
   process. (Before this file existed, `resolved_upgrade_url()` read
   `sync._TRIAL_STATE` in-process and only ever saw the module defaults —
   the per-account URL never reached the button.)

3. Refuse to load `clawmetry-pro` at daemon startup via
   [`clawmetry/extensions.py::load_plugins`](../clawmetry/extensions.py).

4. Auto-install a signed license the cloud attaches to the heartbeat
   response as `license_key` (via
   [`clawmetry/sync.py::_maybe_install_license_from_heartbeat`](../clawmetry/sync.py)).
   Written atomically to `~/.clawmetry/license.key`, permissioned `0600`,
   and the entitlement cache is invalidated so the dashboard picks it up
   within one 60-second cycle — no restart, no re-login.

5. Fire a "trial ends in N days" notification to the cloud once per UTC
   day when `trial_days_left <= CLAWMETRY_TRIAL_WARN_DAYS` (default 2)
   via `POST /ingest/trial-warning`. The daemon does NOT send email
   itself; the cloud owns delivery.

### Allowlist while blocked

The 402 gate skips these paths (see `_ALLOWED_PATH_*` in
`trial_enforcement.py`). Everything else 402s.

| Path                            | Why it must stay reachable                                     |
|---------------------------------|----------------------------------------------------------------|
| `/`, `/robots.txt`              | Dashboard shell renders the overlay on top of it              |
| `/static/*`, `/favicon*`        | Overlay JS/CSS must load                                       |
| `/api/trial/*`                  | Status, refresh, mark-warned (owned by `routes/trial.py`)     |
| `/api/entitlement*`             | Overlay reads resolver directly for auto-clear                |
| `/api/license/*`                | Activation + inspection surface (CLI + overlay)               |
| `/api/paywall/*`                | "User saw the block" telemetry                                 |
| `/api/version`, `/api/heartbeat`, `/api/extensions` | Diagnostics for `clawmetry status`         |

### Environment variables introduced

| Variable                          | Default   | Meaning                                                       |
|-----------------------------------|-----------|---------------------------------------------------------------|
| `CLAWMETRY_HARD_BLOCK`            | *(on)*    | Master switch — set `0` / `false` / `no` / `off` to opt out.  |
| `CLAWMETRY_HARD_BLOCK_ESCAPE`     | `0`       | Support-only escape hatch — bypass block even while enabled.  |
| `CLAWMETRY_TRIAL_WARN_DAYS`       | `2`       | Days before expiry the daemon fires the trial-ending notice.  |
| `CLAWMETRY_UPGRADE_URL`           | *(unset)* | Override the generic upgrade page URL.                        |
| `CLAWMETRY_CHECKOUT_URL`          | *(unset)* | Override the per-account signed Stripe checkout URL.          |

### Why default ON

Founder policy (2026-08-06): trial ends → non-dismissable modal →
payment → auto-unlock is a strict requirement, not an opt-in. Users who
"enjoy ClawMetry self-hosted forever by setting `CLAWMETRY_OFFLINE=1`"
are the specific loophole this closes.

Paying customers with a valid signed Ed25519 license file on disk are
NOT affected — the resolver returns `is_paid=True` + unexpired, which
short-circuits the block predicate. Only a source that WAS on a paid or
trial tier and has since passed its `expiry` (trial past deadline, or a
paid subscription that lapsed) hits the paywall. Plain OSS / `cloud_free`
(never entitled at all) is exempt: it was never the loophole this closes,
and the original shipped predicate over-applied "not currently paid" to
mean "block", instead of "was paid/trialing and lapsed, block". Corrected
the same day once the live symptom (a fresh free install stuck forever on
"Initializing ClawMetry") surfaced.

The `CLAWMETRY_HARD_BLOCK=0` opt-out exists solely as a support lever for
the rare case of a legitimate paying customer whose license file
corrupted mid-renewal — never as a documented user-facing knob.

## Cross-repo work orders still required

The loop the founder described in the goal ("email on trial end → click
pay → auto-license → dashboard resumes") requires four pieces of work in
sibling repos before the default can flip. Each is small and none is
blocked by this scaffold.

### `clawmetry-cloud` (ingest + heartbeat + email + billing)

0. **Add `POST /api/billing/checkout-session`** (`X-Api-Key` auth): resolve
   the account from the node key, create a Stripe Checkout Session for the
   Pro/Starter price (customer + email prefilled from the account), and
   return `{ok: true, url: "https://checkout.stripe.com/..."}`. On
   `checkout.session.completed`, mint the signed license and attach it as
   `license_key` on the next heartbeat (item 1 below) — that is what makes
   the OSS overlay's "pay → auto-unlock, no key to paste" loop real. The
   session's `success_url` should say "Payment received — you can close this
   tab; your dashboard unlocks automatically." OSS side is already live:
   `routes/trial.py::api_trial_checkout` calls this and falls back to
   `checkout_url`/`upgrade_url` when the endpoint 404s.
1. **Extend heartbeat response** with `license_key` when the account
   completed checkout since the last heartbeat. Payload: raw Ed25519
   `header.payload.signature` token, matching what `clawmetry license
   activate <KEY>` accepts.
2. **Add `POST /ingest/trial-warning`** endpoint that accepts
   `{days_left, plan}` + `X-Clawmetry-Key` header, resolves the account,
   and sends the "your trial ends in N days" email via the existing
   SendGrid pipeline. Idempotent per (account_id, UTC day) — the daemon
   already rate-limits but the cloud should also de-duplicate.
3. **Add `POST /ingest/trial-expired`** endpoint that fires on the first
   heartbeat after expiry, sending the "trial ended — click to resume"
   email. (Optional: the trial-warning endpoint above with `days_left=0`
   can double as this; either shape works.)
4. **Attach `upgrade_url` and `checkout_url`** to every heartbeat
   response so the overlay always shows the per-account signed Stripe
   checkout URL (rather than the generic upgrade page).

### `clawmetry-pro` (paid package)

1. **Optional — `CLAWMETRY_PRO_DELETE_ON_EXPIRY=1`**: on daemon startup,
   if the resolver reports hard-blocked, run `python -m pip uninstall -y
   clawmetry-pro` to remove the paid package from disk. Founder's stated
   ask ("delete clawmetry pro package for safety") — kept optional
   because (a) uninstalling a package while its code may be imported is
   fragile, and (b) refusing to load it via the extensions guard above
   is functionally equivalent and reversible.

### QA / verification

1. **Founder-machine E2E**: start with `CLAWMETRY_HARD_BLOCK=1` +
   entitlement resolver reporting expired trial. Confirm:
   - `/api/sessions` → 402 with correct JSON body
   - Dashboard renders overlay, cannot be dismissed
   - Paste a valid license key → activate → overlay clears
   - Delete license, restart, wait for cloud heartbeat carrying a
     `license_key` → overlay auto-clears within 60s
2. **Regression sweep**: existing paying customer with valid signed
   license on disk sees NO block whether flag is on or off.

## Paywall funnel telemetry

> Spec: REQ "Free Answer at the Gate, and a Visible Paywall"
> (`cd0b3dc3-ca5c-49ad-a4c0-dec01f122d12`), AC-FREE-002 and AC-FREE-001.


The hard-block overlay posts two beacons to `POST /api/paywall/event`:

| Beacon (app.js) | Forwarded as | Meaning |
|---|---|---|
| `hard_block_view` | `paywall_view` | the overlay was rendered to a user |
| `hard_block_checkout_click` | `paywall_checkout_click` | that user clicked through to pay |

Both were local-only until 0.12.821: `/api/paywall/event` wrote to an
in-process rolling store (`clawmetry/_paywall_events.py`, read back by
`/api/paywall/events/*`) and nothing left the machine. Cloud analytics
therefore held zero rows for either beacon, ever, and the funnel could not
separate "saw the paywall and declined" from "never reached it" — the one
question a pricing decision actually turns on.

`routes/entitlement.py::_ping_paywall_lifecycle` now mirrors exactly these
two into `clawmetry/telemetry.py`, the same anonymous lifecycle channel as
`install` / `update` / `onboarded` / `gate_shown`. That is deliberate: it
inherits the existing privacy contract with no new surface. An anonymous
install id, no account, no email, no hostname, no workspace path and no
runtime data; every opt-out already honoured (`CLAWMETRY_NO_TELEMETRY`,
`DO_NOT_TRACK`, `~/.clawmetry/notelemetry`). `ping_once` dedups on disk, so
an overlay that re-renders on every background poll still sends one row per
install. The cloud must allowlist both names in
`routes/install.py::_ALLOWED_EVENTS` or they are dropped with no insert and
no error.

The mapping is a silent-failure point: rename a beacon in `app.js` and the
telemetry stops with nothing turning red. `tests/test_paywall_funnel_telemetry.py`
asserts the forwarder still covers every `hard_block_*` beacon `app.js` posts.

## The gate's free-runtimes escape

`POST /api/onboarding/free-only` records `selfhost_free`: the user keeps
OpenClaw, NVIDIA NemoClaw and Goose (the `FREE_RUNTIMES`, free forever) and
takes no account, no cloud and no trial. It flips free-only mode on
(`trial_enforcement.set_free_only_mode`, the same marker the expired-trial
paywall writes) and writes the nocloud marker **before** recording the
choice, so the recorded state is backed by real local configuration. Undo
from Settings or `POST /api/trial/exit-free`.

This is **not** the deferred gate ("Look First, Choose Later", REQ-OGV-DG-*),
which remains unbuilt and is a different design: there, free runtimes render
with *no choice on record* and the gate is deferred to a later trigger. Here
the gate is still hard and still answered immediately — the change is only
that one of the answers no longer costs a signup. `selfhost_free` stays out
of `onboarding_state.CHOICES`, so it is not postable through the generic
`/api/onboarding/complete`; this dedicated endpoint is the only flow that
may claim it.

## Related code

| File | What lives there |
|---|---|
| [`clawmetry/trial_enforcement.py`](../clawmetry/trial_enforcement.py) | Core policy: `hard_block_enabled`, `is_hard_blocked`, `allowlisted_path`, `block_payload`, `resolved_upgrade_url`, `warning_window_days`. |
| [`clawmetry/entitlements.py`](../clawmetry/entitlements.py) | `Entitlement.to_dict()` now surfaces `hard_blocked` alongside every other resolver field. |
| [`routes/trial.py`](../routes/trial.py) | `bp_trial` — `/api/trial/status`, `/api/trial/refresh-license`, `/api/trial/mark-warned`. |
| [`dashboard.py`](../dashboard.py) | Flask `before_request` gate + `bp_trial` registration inside the `detect_config` bootstrap. |
| [`clawmetry/static/js/app.js`](../clawmetry/static/js/app.js) | Top-of-file IIFE `initClawMetryHardBlockOverlay` — non-dismissable overlay + license paste flow + auto-clear poller. |
| [`clawmetry/sync.py`](../clawmetry/sync.py) | `_maybe_install_license_from_heartbeat`, `_maybe_send_trial_warning` in the heartbeat path. |
| [`clawmetry/extensions.py`](../clawmetry/extensions.py) | `load_plugins` skips paid plugins when hard-blocked. |
