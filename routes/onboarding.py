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
import platform
import threading
import time
from pathlib import Path

from flask import Blueprint, jsonify, request

bp_onboarding = Blueprint("onboarding", __name__)

log = logging.getLogger(__name__)

# The path, the postable choices and the writer all live in
# clawmetry/onboarding_state.py now, so the CLI (`connect`, `onboard`,
# `activate`) and the desktop shell record the SAME file this gate reads —
# the 2026-08-22 re-prompt bug was nothing but three writers' worth of
# missing writes. Imported defensively: the gate must still boot if the
# package half of a partial upgrade is older than the routes half.
try:
    from clawmetry import onboarding_state as _obs

    _STATE_PATH = _obs.state_path()
    _CHOICES = _obs.CHOICES
    _RECORDED_CHOICES = _obs.RECORDED_CHOICES
except Exception:  # pragma: no cover - defensive, package/routes skew only
    _obs = None
    _STATE_PATH = os.path.expanduser("~/.clawmetry/onboarding.json")
    _CHOICES = ("managed", "selfhost_license", "selfhost_trial")
    _RECORDED_CHOICES = _CHOICES + ("selfhost_free",)


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


def _desktop_shell_runtime_dir() -> Path:
    """Where the desktop shell keeps its per-user runtime state, mirroring
    ``desktop/app.py::_runtime_dir`` byte-for-byte so the two agree on the
    file to look for. Duplicated (not imported) because the ``desktop``
    package is only bundled into the .app; the pip wheel — which serves
    the dashboard everywhere — does not ship it."""
    system = platform.system()
    if system == "Darwin":
        base = Path.home() / "Library" / "Application Support" / "ClawMetry"
    elif system == "Windows":
        base = Path(os.environ.get("LOCALAPPDATA") or str(Path.home())) / "ClawMetry"
    else:
        base = Path(
            os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
        ) / "ClawMetry"
    return base / "runtime"


def _desktop_shell_stamp() -> dict:
    """Read the desktop shell's own ``onboarding-completed.json``, if any.

    Written by ``desktop/onboarding.py::mark_onboarding_completed`` after
    the user completes the shell's native onboarding pane
    (OAuth / email OTP → hosting choice). Payload:
    ``{completed, signed_in, provider, email, mode}`` — ``mode`` was added
    in #4758; pre-#4758 stamps omit it.

    Returns the parsed dict or ``{}`` on any failure (missing file, corrupt
    JSON, wrong shape). Never raises."""
    stamp = _desktop_shell_runtime_dir() / "onboarding-completed.json"
    try:
        with stamp.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _shell_stamp_choice() -> str:
    """Map the shell stamp to a value from ``_CHOICES``, or ``''`` when the
    user hasn't completed the shell pane or dismissed it without signing
    in — in which case the browser gate still owes a prompt.

    Two failure modes this closes (both live-hit 2026-08-12):

    1. **Deployment lag.** ``desktop/`` code ships only inside the .app
       bundle and reaches users on a new .dmg download; the pip wheel
       auto-updates every 6h. If we relied on the shell to also write the
       browser gate's own file (#4758), every user on any pre-#4758 .dmg
       would still see the modal re-appear after finishing shell
       onboarding — until they redownloaded. Reading the shell stamp
       here inverts that: the fix rides the pip wheel and reaches the
       whole fleet on the next update, regardless of installer age.

    2. **Silent trial-mint failures.** When the shell's ``apply_cm_key``
       runs ``clawmetry connect --key … --keep-local``, cloud may accept
       the key but reject the trial (network blip, cloud-side error).
       ``connect`` exits 0 anyway, so the shell stamps ``signed_in=True``
       but no ``license.key`` lands. Then ``_license_state()`` is empty,
       ``_cloud_connected()`` short-circuits on the nocloud marker, and
       the gate falls through to ``{required: True}``. Recognising the
       explicit user choice in the shell stamp resolves the re-prompt;
       missing entitlement then surfaces inside the dashboard where the
       user can retry, instead of trapping them in an onboarding loop.

    Mode resolution for older .dmg stamps that lack the field: infer from
    the nocloud marker, which is the same self-host intent signal
    ``_cloud_connected()`` respects."""
    stamp = _desktop_shell_stamp()
    if not stamp.get("completed"):
        return ""
    if not stamp.get("signed_in"):
        return ""
    mode = str(stamp.get("mode", "")).strip().lower()
    if mode == "selfhost":
        return "selfhost_trial"
    if mode == "cloud":
        return "managed"
    # Pre-#4758 .dmg: mode field wasn't recorded. Infer from what
    # apply_cm_key would have left behind on the machine.
    try:
        from clawmetry.config import is_cloud_disabled as _icd

        if _icd():
            return "selfhost_trial"
    except Exception:
        pass
    return "managed"


def _paid_entitlement_state() -> str:
    """``''`` | ``'selfhost_license'`` | ``'managed'`` — derived from the
    RESOLVED entitlement, which is strictly more than the local key file
    ``_license_state()`` reads.

    Closes the founder live-hit of 2026-08-22: a machine connected with
    ``clawmetry connect`` to a paying ``cloud_pro`` account, then switched
    to local-only (``--turn-off-cloud-sync``), was shown this gate again and
    asked to sign in a second time. Every check missed it — no gate file
    (the CLI never wrote one, now fixed in ``clawmetry/onboarding_state.py``),
    no ``license.key`` (a cloud plan does not mint one), no shell stamp, and
    ``_cloud_connected()`` deliberately returns False under the self-host
    marker. Yet ``clawmetry status`` on the same box read ``cloud_pro``,
    because ``entitlements`` resolves the daemon's ``cloud_plan.json`` cache
    that ``license.load_license()`` knows nothing about.

    A PAID entitlement is proof the account finished onboarding somewhere —
    nobody pays before choosing. The free tier is deliberately not proof:
    that is exactly the "linked account, plan free, trial mint failed"
    limbo ``_cloud_connected`` documents, which must still be re-asked.

    Self-host intent still decides the *label*: a paid plan under the
    nocloud marker is someone running their own box on a cloud
    subscription, not a managed install.
    """
    try:
        from clawmetry import entitlements as _ent

        ent = _ent.get_entitlement()
        if not ent or not getattr(ent, "is_paid", False) or getattr(ent, "expired", False):
            return ""
    except Exception:
        return ""
    try:
        from clawmetry.config import is_cloud_disabled as _icd

        return "selfhost_license" if _icd() else "managed"
    except Exception:
        return "managed"


def _resolve_state() -> dict:
    """The single source of truth the gate JS renders from.

    Precedence, most-authoritative first:
      1. Explicit choice recorded in the browser gate's own file — written
         by this gate AND by every CLI/desktop onboarding path (see
         ``clawmetry/onboarding_state.py``).
      2. Active local license (trial or paid).
      3. Explicit choice recorded by the DESKTOP SHELL's onboarding pane
         (see ``_shell_stamp_choice`` — pip-wheel-side mirror of #4758,
         reaches users regardless of installer age).
      4. A paid entitlement resolved from anywhere, including the cloud
         plan cache the local key file cannot see (``_paid_entitlement_state``).
      5. Cloud token with no self-host intent recorded anywhere.

    The shell check sits BELOW the local license check on purpose: a
    live license is a stronger signal than "user clicked something in
    the shell N days ago" (they could have since let the trial expire),
    and we want ``state`` to reflect what the user can actually DO now
    when the two disagree."""
    recorded = _read_choice_file()
    choice = str(recorded.get("choice", "")).strip().lower()
    # _RECORDED_CHOICES, not _CHOICES: the CLI wizard's "no account, no
    # cloud" answer (selfhost_free) is a real choice that must close this
    # gate, even though no browser flow can POST it.
    if choice in _RECORDED_CHOICES:
        return {"required": False, "state": choice, "source": "gate"}
    lic = _license_state()
    if lic:
        return {"required": False, "state": lic, "source": "license"}
    shell_choice = _shell_stamp_choice()
    if shell_choice:
        return {"required": False, "state": shell_choice,
                "source": "desktop_shell"}
    paid = _paid_entitlement_state()
    if paid:
        return {"required": False, "state": paid, "source": "entitlement"}
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


# ── Account sign-out (switch to a different ClawMetry account) ─────────────
# Until this existed the ONLY way off a signed-in account was the CLI
# (``clawmetry disconnect`` then ``clawmetry login``) — so a user whose Pro
# licence sits on a different email hit the expired-trial modal with no way
# forward: the gate blocks the dashboard, and every button on it re-uses the
# identity already on disk (founder live-hit 2026-08-18).
#
# "Sign out" here means FORGET THE ACCOUNT ON THIS MACHINE, which is four
# separate pieces of state — miss any one and the gate either refuses to
# re-open or the daemon quietly re-installs the old account's licence on its
# next heartbeat:
#   1. ~/.clawmetry/license.key      the entitlement itself
#   2. ~/.clawmetry/config.json      the cm_ cloud key (+ sync state file)
#   3. ~/.clawmetry/onboarding.json  this gate's recorded choice
#   4. the desktop shell's onboarding-completed.json stamp (_shell_stamp_choice
#      keeps the gate closed on .app installs even with 1-3 gone)
# Ingested data in DuckDB is deliberately left alone: signing out is an
# identity operation, not a factory reset.

def _signout_clear_cloud_identity() -> bool:
    """Delete the cm_ key + sync state. True when something was removed."""
    removed = False
    try:
        from clawmetry.sync import CONFIG_FILE, STATE_FILE

        for path in (Path(str(CONFIG_FILE)), Path(str(STATE_FILE))):
            try:
                if path.exists():
                    path.unlink()
                    removed = True
            except Exception as exc:
                log.warning("signout: cannot remove %s: %s", path, exc)
    except Exception as exc:
        log.warning("signout: cloud identity clear failed: %s", exc)
    # A stale sync-progress file makes the dashboard banner freeze on
    # whatever phase the old account's daemon was in (same reason
    # ``clawmetry disconnect`` drops it).
    try:
        prog = Path.home() / ".clawmetry" / "sync_progress.json"
        if prog.exists():
            prog.unlink()
    except Exception:
        pass
    return removed


def _signout_clear_choice() -> bool:
    """Drop both onboarding stamps so the gate prompts again."""
    removed = False
    for path in (Path(_STATE_PATH),
                 _desktop_shell_runtime_dir() / "onboarding-completed.json"):
        try:
            if path.exists():
                path.unlink()
                removed = True
        except Exception as exc:
            log.warning("signout: cannot remove %s: %s", path, exc)
    return removed


def _signout_restart_daemon() -> None:
    """Kick the sync daemon so it drops the old account's key.

    ``run_daemon`` reads ``config.json`` ONCE at startup and keeps the key in
    memory for the whole process, so deleting the file is not enough — a
    running daemon would keep heartbeating as the signed-out account and
    ``_maybe_install_license_from_heartbeat`` would write its licence straight
    back. Restarting drops it into local-only mode (ingestion continues,
    nothing leaves the machine). Off-thread + best-effort: launchctl/systemctl
    are real latency the browser should not wait on, and a failed restart just
    means the change lands on the daemon's next natural restart.
    """
    def _run() -> None:
        try:
            import dashboard as _d

            _d._restart_sync_daemon()
        except Exception as exc:
            log.warning("signout: daemon restart failed: %s", exc)

    try:
        threading.Thread(target=_run, daemon=True).start()
    except Exception:
        _run()


@bp_onboarding.route("/api/account/signout", methods=["POST"])
def api_account_signout():
    """Forget the ClawMetry account this machine is signed in with.

    Idempotent — signing out twice is a no-op, not an error. Always returns
    HTTP 200 with what was actually cleared so the caller can reload into the
    gate regardless; the one hard failure is the hosted dashboard, where
    account state lives in the cloud session rather than on disk.
    """
    if os.environ.get("CLAWMETRY_CLOUD", "").strip():
        return jsonify({
            "ok": False,
            "error": "Sign out from your account menu on app.clawmetry.com.",
        }), 400

    cleared = {"license": False, "cloud": False, "choice": False}
    try:
        from clawmetry import license as _lic

        ok, removed = _lic.deactivate(actor="dashboard-signout")
        cleared["license"] = bool(ok and removed)
    except Exception as exc:
        log.warning("signout: license deactivate failed: %s", exc)

    cleared["cloud"] = _signout_clear_cloud_identity()
    cleared["choice"] = _signout_clear_choice()

    # No egress while nobody is signed in. Symmetric with sign-in: the
    # managed branch clears this marker via ``config.enable_cloud()`` and the
    # self-host branch re-writes it, so neither path is blocked by it.
    try:
        from clawmetry import config as _cfg

        marker = Path(str(_cfg.NOCLOUD_MARKER_PATH))
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.touch(exist_ok=True)
    except Exception as exc:
        log.warning("signout: nocloud marker failed: %s", exc)

    try:
        from clawmetry import entitlements as _ent

        _ent.invalidate()
    except Exception:
        pass

    _signout_restart_daemon()
    log.info("signout: cleared %s", cleared)
    return jsonify({"ok": True, "cleared": cleared, "state": _resolve_state()})
