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
   "Continue to payment →" CTA pointing at `upgrade_url`, and a paste-in
   license-key field that hits `/api/license/activate` directly.

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
