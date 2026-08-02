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
