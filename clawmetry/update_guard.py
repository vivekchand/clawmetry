"""Crash-loop rollback guard for daemon self-update (firmware-OTA style).

``perform_self_update()`` (routes/meta.py) ARMS the guard right after
``pip install -U clawmetry`` succeeds, before the process restarts.
``run_daemon()`` (clawmetry/sync.py) CHECKS the guard at boot:

- Each daemon boot inside the guard window increments a boot counter.
- ``MAX_BOOTS`` rapid boots in a row (a launchd/systemd respawn loop) means
  the freshly installed wheel is crashing, so the guard pip-installs the
  PREVIOUS version and exits; the supervisor respawns on the rolled-back
  build. The rollback is recorded in ``update_rollback.json`` so the
  dashboard / heartbeat can surface it.
- A healthy run self-CONFIRMS (clears the guard) after ``CONFIRM_AFTER_S``
  seconds of uptime, mirroring the firmware OTA ``PENDING_VERIFY`` →
  ``mark_app_valid`` flow in clawmetry-hardware.

An import-time crash of ``clawmetry.sync`` is outside what this guard can
catch (the guard itself would never run); that band is covered by the PyPI
staleness rail (``CLAWMETRY_AUTOUPDATE_MIN_AGE_HOURS``, default 48h), which
keeps unattended installs off brand-new releases. Never raises: every entry
point swallows and logs.
"""
import json
import logging
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

log = logging.getLogger(__name__)

_CLAWMETRY_HOME = Path(os.path.expanduser("~/.clawmetry"))
STATE_PATH = _CLAWMETRY_HOME / "update_state.json"
ROLLBACK_MARKER = _CLAWMETRY_HOME / "update_rollback.json"

# A guard older than this is stale (the update clearly applied long ago).
WINDOW_S = 3600
# This many boots inside the window = crash loop -> roll back.
MAX_BOOTS = 3
# A run that stays up this long confirms the new version is healthy.
CONFIRM_AFTER_S = 300


def _read_state():
    try:
        with open(STATE_PATH, "r") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def _write_state(state):
    try:
        STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        tmp = STATE_PATH.with_suffix(".json.tmp")
        with open(tmp, "w") as f:
            json.dump(state, f)
        os.replace(tmp, STATE_PATH)
    except Exception as exc:
        log.warning("update guard: could not write state: %s", exc)


def _clear_state():
    try:
        STATE_PATH.unlink()
    except FileNotFoundError:
        pass
    except Exception as exc:
        log.warning("update guard: could not clear state: %s", exc)


def arm_rollback_guard(prev_version, target_version, reason="manual"):
    """Record that an upgrade ``prev -> target`` is about to restart the
    daemon. Called by ``perform_self_update`` AFTER pip succeeded. No-op when
    the versions are equal (nothing actually changed)."""
    try:
        prev_version = str(prev_version or "").strip()
        target_version = str(target_version or "").strip()
        if not prev_version or not target_version or prev_version == target_version:
            return
        _write_state({
            "prev": prev_version,
            "target": target_version,
            "reason": str(reason),
            "ts": time.time(),
            "boots": 0,
        })
        log.info("update guard armed: %s -> %s (%s)", prev_version, target_version, reason)
    except Exception as exc:
        log.warning("update guard: arm failed: %s", exc)


def confirm_update_ok():
    """Healthy-run confirmation: the new version survived; drop the guard."""
    if _read_state() is not None:
        log.info("update guard: new version confirmed healthy")
    _clear_state()


def _pip_install_version(version):
    """Best-effort ``pip install clawmetry==<version>`` in this interpreter's
    venv (ensurepip bootstrap first: the ~/.clawmetry venv may lack pip)."""
    py = sys.executable
    try:
        subprocess.run(
            [py, "-m", "ensurepip", "--upgrade", "--default-pip"],
            timeout=60, capture_output=True,
        )
    except Exception:
        pass
    try:
        proc = subprocess.run(
            [py, "-m", "pip", "install", "--no-cache-dir", "clawmetry==%s" % version],
            timeout=300, capture_output=True, text=True,
        )
        if proc.returncode != 0:
            tail = ((proc.stdout or "") + (proc.stderr or "")).strip()[-400:]
            log.error("update guard: rollback pip failed (%s): %s", proc.returncode, tail)
        return proc.returncode == 0
    except Exception as exc:
        log.error("update guard: rollback pip errored: %s", exc)
        return False


def check_boot_and_maybe_rollback(current_version, _install=None, _exit=None):
    """Call once, early in ``run_daemon``. Returns a status string (for tests
    and logs): ``idle`` / ``expired`` / ``mismatch`` / ``armed`` /
    ``rolled_back`` / ``rollback_failed``. Never raises."""
    try:
        state = _read_state()
        if not state:
            return "idle"
        if time.time() - float(state.get("ts", 0) or 0) > WINDOW_S:
            _clear_state()
            return "expired"
        if str(state.get("target", "")) != str(current_version):
            # We are not running the version the guard was armed for (the
            # update never applied, or a manual fix already happened).
            _clear_state()
            return "mismatch"

        boots = int(state.get("boots", 0) or 0) + 1
        if boots >= MAX_BOOTS:
            prev = str(state.get("prev", "") or "")
            log.error(
                "update guard: %d rapid boots on v%s — rolling back to v%s",
                boots, current_version, prev,
            )
            ok = bool(prev) and (_install or _pip_install_version)(prev)
            try:
                ROLLBACK_MARKER.parent.mkdir(parents=True, exist_ok=True)
                with open(ROLLBACK_MARKER, "w") as f:
                    json.dump({
                        "from": str(current_version),
                        "to": prev,
                        "ok": bool(ok),
                        "ts": time.time(),
                        "reason": state.get("reason", ""),
                    }, f)
            except Exception:
                pass
            _clear_state()
            if ok:
                # Exit so the supervisor (launchd KeepAlive / systemd
                # Restart=always) respawns on the rolled-back wheel.
                (_exit or os._exit)(0)
                return "rolled_back"  # only reached when _exit is a test spy
            return "rollback_failed"

        state["boots"] = boots
        _write_state(state)
        # Healthy-run confirmation: if we stay up CONFIRM_AFTER_S, the new
        # version is good and the guard clears itself.
        t = threading.Timer(CONFIRM_AFTER_S, confirm_update_ok)
        t.daemon = True
        t.start()
        return "armed"
    except Exception as exc:
        log.warning("update guard: boot check failed: %s", exc)
        return "error"
