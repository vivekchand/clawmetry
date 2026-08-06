"""
routes/onboarding.py — the first-run onboarding gate state machine.

Owns ``bp_onboarding``:

  GET  /api/onboarding/state            — does this install still owe an
                                          onboarding choice, and what is it?
  POST /api/onboarding/complete         — record the choice after its flow
                                          finished (managed cloud connect,
                                          trial activation, license key)
  POST /api/onboarding/activate-license — activate a CLAW1 key and record
                                          the selfhost_license choice in one
                                          call (the gate's license branch)

Why a gate: ``pip install clawmetry && clawmetry`` used to land straight on
the dashboard with no identity and no explicit choice, so the funnel had no
idea whether an install ever chose anything (founder decision 2026-07-31:
hard gate, everyone chooses managed cloud or self-host; self-host offers a
license key or the free 7-day Pro trial).

State resolution — an install is already onboarded when ANY of:
  1. ``~/.clawmetry/onboarding.json`` records an explicit choice (this gate).
  2. A local license key is activated (self-host, license or trial: the CLI
     ``clawmetry activate`` / ``clawmetry onboard`` path predates the gate).
  3. A cloud token exists (managed: ``clawmetry connect`` / the cloud CTA).
Derived states (2)/(3) mean existing installs that already chose through
the CLI are never re-prompted; installs with no choice on record are gated
regardless of age.

The gate is UX, not security: this is the user's own machine and an open
package, so "hard" means no path in the UI, not tamper-proofing. The
hosted cloud dashboard (CLOUD_MODE) never gates — accounts there already
chose managed by signing up.
"""

import json
import logging
import os
import threading
import time

from flask import Blueprint, jsonify, request

bp_onboarding = Blueprint("onboarding", __name__)

log = logging.getLogger(__name__)

_STATE_PATH = os.path.expanduser("~/.clawmetry/onboarding.json")

_CHOICES = ("managed", "selfhost_license", "selfhost_trial")


def _read_choice_file() -> dict:
    try:
        with open(_STATE_PATH, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _write_choice_file(choice: str) -> bool:
    try:
        os.makedirs(os.path.dirname(_STATE_PATH), exist_ok=True)
        with open(_STATE_PATH, "w", encoding="utf-8") as fh:
            json.dump({"choice": choice, "completed_at": int(time.time())}, fh)
        return True
    except Exception as exc:
        log.warning("onboarding: cannot persist choice: %s", exc)
        return False


def _license_state() -> str:
    """'' | 'selfhost_trial' | 'selfhost_license' from the local key."""
    try:
        from clawmetry import license as _lic

        payload = _lic.load_license()
        if not payload:
            return ""
        # load_license() returns an Entitlement object (older builds returned
        # a dict). A .get() call on the object raised AttributeError into the
        # broad except below, so an ACTIVE trial read as "no license" and
        # /api/onboarding/complete 409'd right after a successful activation.
        if isinstance(payload, dict):
            tier = payload.get("tier", "")
        else:
            tier = getattr(payload, "tier", "")
        tier = str(tier or "").strip().lower()
        if not tier or tier in ("oss", "free"):
            return ""
        return "selfhost_trial" if tier == "trial" else "selfhost_license"
    except Exception:
        return ""


def _cloud_connected() -> bool:
    """A cloud token alone means "chose managed" ONLY when self-host was
    never the intent. ``_selfhost_signin_with_key`` (dashboard.py) writes
    the SAME cloud token as the managed-connect flow purely to carry
    identity for the trial-signup call -- it touches the nocloud marker
    FIRST, before persisting that token. If the trial-signup half of that
    flow then fails (network error, cloud-side rejection, anything caught
    by its broad ``except Exception: pass``), the account is linked but no
    license/trial was ever activated -- yet this fallback used to report
    "already onboarded, state=managed" on every later page load anyway,
    because it only checked for the token's existence, not what it was
    for. That silently stranded a failed self-host trial attempt on the
    live dashboard with everything locked and no way to see the error or
    retry (live-hit 2026-08-06: linked account showed plan "free", no
    license file, but the gate never required a choice again). Self-host
    intent (the nocloud marker) takes precedence: a token minted under it
    is identity-only until an explicit choice or a license is on record,
    both of which are already checked earlier in ``_resolve_state()``.
    """
    try:
        import dashboard as _d
        from clawmetry.config import is_cloud_disabled as _icd

        if _icd():
            return False
        return bool(_d._read_cloud_token())
    except Exception:
        return False


def _resolve_state() -> dict:
    """The single source of truth the gate JS renders from."""
    recorded = _read_choice_file()
    choice = str(recorded.get("choice", "")).strip().lower()
    if choice in _CHOICES:
        return {"required": False, "state": choice, "source": "gate"}
    lic = _license_state()
    if lic:
        return {"required": False, "state": lic, "source": "license"}
    if _cloud_connected():
        return {"required": False, "state": "managed", "source": "cloud"}
    return {"required": True, "state": "none", "source": "none"}


def _ping_onboarded(choice: str) -> None:
    """Best-effort lifecycle ping (anonymous, opt-out — clawmetry/telemetry)."""
    try:
        from clawmetry import telemetry as _telemetry

        try:
            from dashboard import __version__ as _ver
        except Exception:
            _ver = "unknown"
        _telemetry.ping_event("onboarded", _ver,
                              {"onboarding_state": choice})
    except Exception:
        pass


def _apply_marker_semantics(choice: str) -> None:
    """Managed clears the local-only marker (the June '0 nodes' bug class:
    connect without enable_cloud() silently no-ops sync). Self-host writes
    it so identity/trial never turns into an unasked-for data upload."""
    try:
        import pathlib

        from clawmetry import config as _cfg

        if choice == "managed":
            _cfg.enable_cloud()
        else:
            # NOCLOUD_MARKER_PATH is a plain str; the old .parent/.touch
            # calls raised AttributeError into this except, so the marker
            # was silently never written for self-host choices.
            marker = pathlib.Path(str(_cfg.NOCLOUD_MARKER_PATH))
            marker.parent.mkdir(parents=True, exist_ok=True)
            marker.touch(exist_ok=True)
    except Exception as exc:
        log.warning("onboarding: marker update failed: %s", exc)


def _ensure_daemon_for_choice(choice: str) -> None:
    """Every choice this gate can record must end with a PERSISTENT
    background daemon, not just an in-process dashboard thread.

    Root cause this closes: before this call, ``managed``/``selfhost_*``
    completion here only touched the nocloud marker (_apply_marker_semantics)
    -- nothing started or registered a background sync daemon. The CLI paths
    (`clawmetry connect`, `clawmetry onboard` self-host) already register one
    via `_start_daemon`, but this browser gate is the DEFAULT onboarding path
    since the 2026-07-31 hard-gate rollout, and it registered nothing. The
    only thing left polling PyPI was the foreground dashboard's in-thread
    checker, which stops the moment that process exits (closed terminal,
    sleep, reboot, crash) -- silently and permanently halting auto-update
    until the user manually relaunches `clawmetry`. Best-effort: never let a
    registration failure break onboarding completion itself.

    Dispatched off the request thread on purpose (2026-08-06 CI regression):
    ``ensure_persistent_daemon`` shells out to systemctl/launchctl/schtasks,
    and even with a bounded per-call timeout that's still real, synchronous
    latency this HTTP handler's caller (the browser) is waiting on. Running
    it in a background thread means a slow or flaky OS registration can
    never delay -- let alone hang -- the onboarding-complete response the
    dashboard's init sequence is blocked on.
    """
    def _run() -> None:
        try:
            from clawmetry.daemon_registration import ensure_persistent_daemon

            ensure_persistent_daemon({"local_only": choice != "managed"})
        except Exception as exc:
            log.warning("onboarding: daemon registration failed: %s", exc)

    try:
        threading.Thread(target=_run, daemon=True).start()
    except Exception as exc:
        log.warning("onboarding: daemon registration dispatch failed: %s", exc)
        _run()


@bp_onboarding.route("/api/onboarding/state")
def api_onboarding_state():
    try:
        if os.environ.get("CLAWMETRY_CLOUD", "").strip():
            # Hosted dashboard: signing up WAS the onboarding.
            return jsonify({"required": False, "state": "managed",
                            "source": "cloud_mode"})
        # Fleet-managed / scripted installs get an explicit escape: the
        # operator made the choice for the machine, a modal can't.
        if os.environ.get("CLAWMETRY_SKIP_ONBOARDING", "").strip() \
                not in ("", "0", "false", "False"):
            return jsonify({"required": False, "state": "none",
                            "source": "env_skip"})
        # CI runs (our own E2E suites included) boot fresh dashboards with
        # no human present; a mandatory modal there only breaks automation.
        try:
            from clawmetry.telemetry import _detect_ci

            if _detect_ci()[0]:
                return jsonify({"required": False, "state": "none",
                                "source": "ci"})
        except Exception:
            pass
        return jsonify(_resolve_state())
    except Exception as exc:
        # Never let gate plumbing brick the dashboard: fail open.
        log.warning("onboarding: state resolution failed: %s", exc)
        return jsonify({"required": False, "state": "none",
                        "source": "error"})


@bp_onboarding.route("/api/onboarding/complete", methods=["POST"])
def api_onboarding_complete():
    data = request.get_json(silent=True) or {}
    choice = str(data.get("choice", "")).strip().lower()
    if choice not in _CHOICES:
        return jsonify({"ok": False, "error": "Unknown choice."}), 400
    # The choice must be backed by its finished flow — recording "managed"
    # with no cloud token (or a self-host state with no key) would strand
    # the install in a half-onboarded limbo the gate can no longer fix.
    if choice == "managed" and not _cloud_connected():
        return jsonify({"ok": False,
                        "error": "Connect to ClawMetry Cloud first."}), 409
    if choice in ("selfhost_license", "selfhost_trial") and not _license_state():
        return jsonify({"ok": False,
                        "error": "Activate a license or trial first."}), 409
    _write_choice_file(choice)
    _apply_marker_semantics(choice)
    _ensure_daemon_for_choice(choice)
    _ping_onboarded(choice)
    return jsonify({"ok": True, "state": choice})


@bp_onboarding.route("/api/onboarding/activate-license", methods=["POST"])
def api_onboarding_activate_license():
    data = request.get_json(silent=True) or {}
    key = str(data.get("key", "")).strip()
    if not key.startswith("CLAW1."):
        return jsonify({"ok": False,
                        "error": "That doesn't look like a ClawMetry key "
                                 "(they start with CLAW1)."}), 400
    try:
        from clawmetry import license as _lic

        ok, msg = _lic.activate(key, actor="onboarding-gate")
    except Exception as exc:
        log.warning("onboarding: activate failed: %s", exc)
        ok, msg = False, "Activation failed. Try again."
    if not ok:
        return jsonify({"ok": False, "error": msg}), 400
    state = _license_state() or "selfhost_license"
    _write_choice_file(state)
    _apply_marker_semantics(state)
    _ensure_daemon_for_choice(state)
    _ping_onboarded(state)
    return jsonify({"ok": True, "state": state, "message": msg})
