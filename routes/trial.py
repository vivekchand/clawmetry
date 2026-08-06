"""
routes/trial.py — Local free-trial activation.

Owns the routes registered on ``bp_trial``:

  POST /api/trial/activate — verify an email OTP with the cloud, receive a
                             signed 7-day trial license key, and activate it
                             on THIS install. The user never leaves the
                             local dashboard.

Why this exists: the paid runtimes (Claude Code, Codex, Cursor, ...) need a
Trial/Pro entitlement, but until now the only path to a trial ran through
the full cloud sign-up (account page in a new tab, node registration, then
waiting for a daemon heartbeat to cache the plan). For someone who just
installed ClawMetry locally that is a funnel cliff. The flow here keeps the
account-creation requirement (email, verified by OTP; the cloud endpoint
also accepts its OAuth session) but completes everything else locally:

  browser modal -> POST /api/cloud-cta/send-otp   (existing proxy, sends code)
  browser modal -> POST /api/trial/activate       (this module)
                     -> cloud POST /api/license/trial  {email, code}
                     <- signed Ed25519 key, tier="trial", 7 days
                     -> clawmetry.license.activate(key)
                          writes ~/.clawmetry/license.key (0600)
                          invalidates the entitlement cache
                          best-effort installs the clawmetry-pro wheel

The signed key is the entitlement (verified offline by clawmetry.license),
so after this call the trial keeps working with no cloud session, no cm_
key, and no network.
"""

import json
import os
import subprocess
import sys
import urllib.error
import urllib.request

from flask import Blueprint, jsonify, request

bp_trial = Blueprint("trial", __name__)


def _ensure_local_daemon() -> None:
    """Best-effort: spawn the sync daemon detached so ingestion starts now.

    Safe to call when a daemon is already running — run_daemon() checks the
    pid lock and exits immediately. Detach semantics mirror the CLI's
    _start_subprocess: POSIX gets start_new_session, Windows gets
    DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP so the daemon survives the
    dashboard (and its console) exiting. Never raises.
    """
    if os.environ.get("PYTEST_CURRENT_TEST"):
        # Tests assert the spawn via monkeypatched Popen; never launch a
        # real daemon out of the test runner's sandbox.
        return
    try:
        # A daemon spawned without a config crash-loops: run_daemon() ->
        # load_config() raises FileNotFoundError, so the trial activates but
        # the DuckDB store is never created and every family runtime stays
        # invisible (live-hit 2026-08-01). Bootstrap a local-only config
        # first; no-op when one already exists.
        try:
            from clawmetry.sync import ensure_local_config
            ensure_local_config()
        except Exception:
            pass
        log_dir = os.path.expanduser("~/.clawmetry")
        try:
            os.makedirs(log_dir, exist_ok=True)
        except Exception:
            pass
        log_fh = open(os.path.join(log_dir, "sync.log"), "a")
        kwargs = {"stdin": subprocess.DEVNULL, "stdout": log_fh,
                  "stderr": subprocess.STDOUT, "close_fds": True,
                  # `python -m clawmetry.sync` puts the CWD on sys.path. When
                  # the dashboard was launched from a clawmetry source
                  # checkout, the spawned daemon silently ran the (possibly
                  # stale) repo copy instead of the installed wheel — pin the
                  # CWD to a neutral directory so imports resolve normally.
                  "cwd": os.path.expanduser("~")}
        if os.name == "nt":
            kwargs["creationflags"] = (
                subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
            )
        else:
            kwargs["start_new_session"] = True
        subprocess.Popen([sys.executable, "-m", "clawmetry.sync"], **kwargs)
        try:
            log_fh.close()
        except Exception:
            pass
    except Exception:
        # A missed spawn must never fail the activation; the daemon also
        # starts on the next `clawmetry` launch / connect.
        pass

# The trial-mint endpoint lives on the license server (same app that hosts
# /api/license/activate). clawmetry.license._cloud_base honours
# CLAWMETRY_LICENSE_SERVER / CLAWMETRY_INGEST_URL for self-hosted setups.
_TRIAL_PATH = "/api/license/trial"


@bp_trial.route("/api/trial/activate", methods=["POST"])
def api_trial_activate():
    """Exchange a verified email OTP for a trial license and activate it."""
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    code = (data.get("code") or "").strip()
    if not email or "@" not in email:
        return jsonify({"ok": False, "error": "Enter a valid email."}), 400
    if not code or not code.isdigit() or len(code) != 6:
        return jsonify({"ok": False, "error": "Enter the 6-digit code from your email."}), 400

    from clawmetry import license as _lic

    base = _lic._cloud_base().rstrip("/")
    body = json.dumps({"email": email, "code": code}).encode("utf-8")
    req = urllib.request.Request(
        base + _TRIAL_PATH,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            payload = json.loads(resp.read().decode("utf-8", errors="replace"))
    except urllib.error.HTTPError as exc:
        # The cloud replies with a JSON error body on 4xx (wrong code, trial
        # already used). Surface its message rather than a generic failure.
        try:
            payload = json.loads(exc.read().decode("utf-8", errors="replace"))
        except Exception:
            payload = {}
        msg = payload.get("error") or f"Trial request failed ({exc.code})."
        return jsonify({"ok": False, "error": msg}), 400
    except Exception:
        return jsonify({
            "ok": False,
            "error": "Could not reach the license server. Check your connection and try again.",
        }), 502

    key = (payload.get("key") or "").strip()
    if not payload.get("ok") or not key:
        return jsonify({
            "ok": False,
            "error": payload.get("error") or "The license server did not return a key.",
        }), 502

    # activate() verifies the signature offline, writes the key 0600,
    # invalidates the entitlement cache, and best-effort installs the
    # clawmetry-pro wheel. Never raises.
    ok, msg = _lic.activate(key, actor="local-trial")
    if not ok:
        return jsonify({"ok": False, "error": msg}), 502

    # The trial is only real to the user when their runtime's data actually
    # shows up. Ingestion is the sync daemon's job, and a local-only install
    # has never started one — so activation without this spawn left the
    # Activity tab empty ("we don't seem to have started trial of pro",
    # founder live-hit 2026-07-28, 3 detected Claude Code sessions, zero
    # ingested). run_daemon() itself exits if another instance already holds
    # the pid lock, so the spawn is idempotent.
    _ensure_local_daemon()

    try:
        from clawmetry import entitlements as _ent

        ent = _ent.get_entitlement(force=True)
        tier = ent.tier
        tier_label = _ent.tier_label(ent.tier)
        expiry = getattr(ent, "expiry", None)
    except Exception:
        tier, tier_label, expiry = "trial", "Trial", None

    return jsonify({
        "ok": True,
        "tier": tier,
        "tier_label": tier_label,
        "expiry": expiry,
        "message": msg,
    })


# ── Trial-end hard-block surface ───────────────────────────────────────────
# The three routes below back the un-dismissable overlay in
# ``clawmetry/static/js/app.js`` (top-of-file IIFE
# ``initClawMetryHardBlockOverlay``). See ``docs/TRIAL_ENFORCEMENT.md`` and
# ``clawmetry/trial_enforcement.py`` for the full policy.
#
#   GET  /api/trial/status           — snapshot { hard_blocked, tier, source,
#                                                 expired, expiry,
#                                                 days_until_expiry, reason,
#                                                 upgrade_url, ... }
#   POST /api/trial/refresh-license  — invalidate entitlement cache so a
#                                     freshly-installed license lands NOW
#   POST /api/trial/mark-warned      — daemon-fired bookkeeping so a duplicate
#                                     "trial ending" toast doesn't double-fire
#
# All three are defensive — a resolver failure returns the safe not-blocked
# shape rather than 500-ing, so the overlay never has to handle a mid-flight
# resolver bug by locking the user out on its own.

import logging as _hb_logging
import time as _hb_time

_hb_log = _hb_logging.getLogger("clawmetry.routes.trial")
_HB_WARNINGS_PATH = os.path.expanduser("~/.clawmetry/trial_warnings.json")


def _hb_snapshot() -> dict:
    """Build the ``/api/trial/status`` payload. Never raises."""
    try:
        from clawmetry import trial_enforcement as _te
        from clawmetry import entitlements as _ent

        ent = _ent.get_entitlement()
        blocked = _te.is_hard_blocked(ent)
        payload = _te.block_payload(ent)
        payload["hard_blocked"] = bool(blocked)
        payload["hard_block_enabled"] = bool(_te.hard_block_enabled())
        payload["warning_window_days"] = int(_te.warning_window_days())
        return payload
    except Exception as exc:
        _hb_log.warning("trial.status: resolver failed: %s", exc)
        return {
            "hard_blocked": False,
            "hard_block_enabled": False,
            "warning_window_days": 2,
            "tier": "oss",
            "reason": "",
            "upgrade_url": "https://app.clawmetry.com/upgrade",
            "activation_endpoint": "/api/license/activate",
            "refresh_endpoint": "/api/trial/refresh-license",
            "status_endpoint": "/api/trial/status",
        }


@bp_trial.route("/api/trial/status", methods=["GET"])
def api_trial_status():
    """Read the current hard-block state."""
    return jsonify(_hb_snapshot())


@bp_trial.route("/api/trial/refresh-license", methods=["POST"])
def api_trial_refresh_license():
    """Invalidate the entitlement cache so a freshly-arrived license file
    gets picked up immediately. Returns the post-refresh snapshot."""
    try:
        from clawmetry import entitlements as _ent
        _ent.invalidate()
    except Exception as exc:
        _hb_log.warning("trial.refresh: invalidate failed: %s", exc)
    return jsonify(_hb_snapshot())


@bp_trial.route("/api/trial/mark-warned", methods=["POST"])
def api_trial_mark_warned():
    """Record that the user has been notified of imminent expiry today.
    Payload: ``{"days_left": <int>}``. Best-effort; never raises."""
    try:
        body = request.get_json(silent=True) or {}
    except Exception:
        body = {}
    try:
        days_left = int(body.get("days_left", -1))
    except Exception:
        days_left = -1
    try:
        os.makedirs(os.path.dirname(_HB_WARNINGS_PATH), exist_ok=True)
        today = _hb_time.strftime("%Y-%m-%d", _hb_time.gmtime())
        existing: dict = {}
        if os.path.isfile(_HB_WARNINGS_PATH):
            try:
                with open(_HB_WARNINGS_PATH, encoding="utf-8") as fh:
                    existing = json.load(fh) or {}
            except Exception:
                existing = {}
        existing[today] = days_left
        tmp = _HB_WARNINGS_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(existing, fh)
        os.replace(tmp, _HB_WARNINGS_PATH)
        return jsonify({"ok": True, "recorded": today, "days_left": days_left})
    except Exception as exc:
        _hb_log.warning("trial.mark_warned: %s", exc)
        return jsonify({"ok": False, "error": str(exc)}), 200
