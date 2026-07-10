"""
routes/update_check.py — Auto-update checker with changelog notification.

Provides:
  - Background thread for checking PyPI for new versions
  - Configuration storage for update check preferences
  - API endpoints for getting/setting config and update status
  - Update notification banner support

Blueprint: bp_update_check
"""
import json
import logging
import os
import sys
import threading
import time
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request

log = logging.getLogger(__name__)

bp_update_check = Blueprint("update_check", __name__)

# Module-level state
_update_check_thread = None
_update_check_stop_event = threading.Event()

# Which process this checker runs in: "dashboard" (default) or "daemon" (the
# supervised sync daemon, set via start_update_check_thread(role="daemon")).
# Default-on auto-update applies ONLY to the daemon role — the always-on,
# launchd/systemd-supervised process where a restart is safe and invisible.
# A dashboard process (often a foreground terminal) auto-installs only when
# the user EXPLICITLY opted in via the settings toggle.
_process_role = "dashboard"

CHANGELOG_URL = "https://github.com/vivekchand/clawmetry/blob/main/CHANGELOG.md"


def _env_auto_update_disabled():
    """Kill switch: ``CLAWMETRY_AUTO_UPDATE=0`` disables unattended upgrades
    regardless of the stored config (fleet operators / CI / debugging)."""
    val = os.environ.get("CLAWMETRY_AUTO_UPDATE", "").strip().lower()
    return val in ("0", "false", "no", "off")


def _auto_update_explicitly_set():
    """True when an ``auto_update`` row exists in the config table — i.e. a
    user (or the entitled-plan sync) chose a value, as opposed to the
    built-in default."""
    try:
        with _get_fleet_db_lock():
            db = _get_fleet_db()
            row = db.execute(
                "SELECT value FROM update_check_config WHERE key='auto_update'"
            ).fetchone()
            db.close()
        return row is not None
    except Exception:
        return False


def _daemon_supervised():
    """Best-effort: is the sync daemon under a supervisor that respawns it
    (launchd KeepAlive / systemd Restart=always)? When it is not, exiting to
    'restart' would just kill the daemon — so the auto-updater installs the
    new wheel but defers the restart to the next manual start."""
    try:
        from pathlib import Path
        if sys.platform == "darwin":
            return (Path.home() / "Library" / "LaunchAgents"
                    / "com.clawmetry.sync.plist").exists()
        if sys.platform.startswith("linux"):
            unit = (Path.home() / ".config" / "systemd" / "user"
                    / "clawmetry-sync.service")
            return unit.exists() or bool(os.environ.get("INVOCATION_ID"))
    except Exception:
        pass
    return False


def _live_current_version() -> str:
    """The version actually running right now (not the version recorded at the
    last PyPI check). Reading this live is what keeps the update banner honest
    immediately after an upgrade — before the next background check runs."""
    try:
        import dashboard as _d
        return str(_d.__version__)
    except Exception:
        return ""


def _version_gt(a: str, b: str) -> bool:
    """True if version ``a`` is strictly newer than ``b`` (numeric tuple
    compare; falls back to string inequality on non-numeric versions)."""
    if not a or not b:
        return False
    try:
        return [int(x) for x in a.split(".")] > [int(x) for x in b.split(".")]
    except Exception:
        return a != b


def _get_fleet_db():
    """Get fleet database connection."""
    import dashboard as _d
    return _d._fleet_db()


def _get_fleet_db_lock():
    """Get fleet database lock."""
    import dashboard as _d
    return _d._fleet_db_lock


def _init_update_check_db():
    """Initialize update check tables in the fleet database."""
    with _get_fleet_db_lock():
        db = _get_fleet_db()
        db.executescript("""
            CREATE TABLE IF NOT EXISTS update_check_config (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS update_check_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                check_at REAL NOT NULL,
                current_version TEXT NOT NULL,
                latest_version TEXT NOT NULL,
                update_available INTEGER NOT NULL,
                changelog_url TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_update_check_at
                ON update_check_history(check_at DESC);
        """)
        db.close()


def _get_update_check_config():
    """Get update check configuration as dict."""
    defaults = {
        "enabled": True,
        "check_on_startup": True,
        "check_daily": True,
        # Default ON (since 0.12.494): a detected newer release is installed
        # automatically by the background worker. Since 2026-07-10 the daemon
        # checks every ~60s and tracks the ABSOLUTE latest (no age gate by
        # default; CLAWMETRY_AUTOUPDATE_MIN_AGE_HOURS restores a window).
        # Rails: only the daemon role acts on the default
        # (see _maybe_auto_update), CLAWMETRY_AUTO_UPDATE=0 is a hard kill
        # switch, failed targets back off CLAWMETRY_AUTOUPDATE_RETRY_SECS,
        # and the boot guard (clawmetry/update_guard.py) rolls back a
        # crash-looping wheel.
        # WHY default-on: 92% of active nodes were found running months-stale
        # daemons (2026-06-09 fleet audit) — every shipped fix reached almost
        # nobody, and the hosted dashboard rendered blank cards against old
        # snapshots. An observability sidecar must keep itself current.
        "auto_update": True,
        "dismissed_version": "",
        "last_check_at": 0,
    }
    try:
        with _get_fleet_db_lock():
            db = _get_fleet_db()
            rows = db.execute("SELECT key, value FROM update_check_config").fetchall()
            db.close()
        for row in rows:
            k = row["key"]
            v = row["value"]
            if k in defaults:
                if isinstance(defaults[k], bool):
                    defaults[k] = v.lower() in ("true", "1", "yes")
                else:
                    defaults[k] = v
    except Exception:
        pass
    return defaults


def _set_update_check_config(updates):
    """Update update check config keys."""
    now = time.time()
    with _get_fleet_db_lock():
        db = _get_fleet_db()
        for k, v in updates.items():
            db.execute(
                "INSERT OR REPLACE INTO update_check_config (key, value, updated_at) VALUES (?, ?, ?)",
                (k, str(v), now),
            )
        db.commit()
        db.close()


def _record_update_check(current, latest, update_available, changelog_url=""):
    """Record an update check in history."""
    now = time.time()
    with _get_fleet_db_lock():
        db = _get_fleet_db()
        db.execute(
            """INSERT INTO update_check_history
               (check_at, current_version, latest_version, update_available, changelog_url)
               VALUES (?, ?, ?, ?, ?)""",
            (now, current, latest, 1 if update_available else 0, changelog_url),
        )
        # Keep only last 30 checks
        db.execute(
            """DELETE FROM update_check_history WHERE id NOT IN
               (SELECT id FROM update_check_history ORDER BY check_at DESC LIMIT 30)"""
        )
        db.commit()
        db.close()


def _get_latest_update_check():
    """Get the most recent update check result."""
    try:
        with _get_fleet_db_lock():
            db = _get_fleet_db()
            row = db.execute(
                """SELECT current_version, latest_version, update_available, changelog_url, check_at
                   FROM update_check_history ORDER BY check_at DESC LIMIT 1"""
            ).fetchone()
            db.close()
        if row:
            latest = row["latest_version"]
            # Always report the LIVE installed version, not the version recorded
            # at check time — otherwise the banner lies right after an upgrade
            # (e.g. "you are on v0.12.306" while actually on v0.12.309) until the
            # next background check runs (which is delayed 60s on startup).
            # Recompute availability against the live version too, so a stale
            # recorded `latest` that's <= the current build never shows a banner.
            current = _live_current_version() or row["current_version"]
            update_available = _version_gt(latest, current)
            return {
                "current": current,
                "latest": latest,
                "update_available": update_available,
                "changelog_url": row["changelog_url"] or "",
                "checked_at": row["check_at"],
            }
    except Exception:
        pass
    return None


def _should_show_update_banner(config, latest_check):
    """Determine if the update banner should be shown."""
    if not config.get("enabled", True):
        return False
    if not latest_check:
        return False
    if not latest_check.get("update_available"):
        return False
    dismissed = config.get("dismissed_version", "")
    if dismissed and latest_check.get("latest") == dismissed:
        return False
    return True


def _autoupdate_min_age_hours() -> float:
    """Stability window (hours) a release must survive on PyPI before the
    daemon will silently install it. Env override:
    ``CLAWMETRY_AUTOUPDATE_MIN_AGE_HOURS``.

    Default 0 (founder call 2026-07-10): ClawMetry ships 20+ releases a day
    and users must never be expected to upgrade by hand, so the fleet tracks
    the ABSOLUTE latest within minutes. The safety net for a bad wheel is
    the boot rollback guard (``clawmetry/update_guard.py``), not a stale
    window — the old 48h gate meant every shipped fix took two days to
    reach anyone. Conservative operators can set the env to restore a
    window; the aged-in selection logic still honors it."""
    try:
        return float(os.environ.get("CLAWMETRY_AUTOUPDATE_MIN_AGE_HOURS", "0") or 0)
    except Exception:
        return 0.0


def _update_check_interval_secs() -> float:
    """How often the DAEMON role polls PyPI for a new release. Env override:
    ``CLAWMETRY_UPDATE_CHECK_SECS`` (default 60, clamped to [30, 86400]).

    A 60s poll of PyPI's JSON endpoint is one tiny CDN-cached GET per node
    per minute — negligible for both sides — and is what turns a release
    into a fleet-wide upgrade within minutes instead of days. The dashboard
    role keeps its gentler startup+daily banner cadence; only the daemon
    (the process that actually installs) runs this fast loop."""
    try:
        v = float(os.environ.get("CLAWMETRY_UPDATE_CHECK_SECS", "60") or 60)
    except Exception:
        v = 60.0
    return max(30.0, min(v, 86400.0))


def _autoupdate_retry_secs() -> float:
    """Backoff before re-attempting a version whose install FAILED. Without
    this, the 60s check loop would re-run pip against a broken target every
    minute. Env override: ``CLAWMETRY_AUTOUPDATE_RETRY_SECS`` (default 1800)."""
    try:
        return float(os.environ.get("CLAWMETRY_AUTOUPDATE_RETRY_SECS", "1800") or 1800)
    except Exception:
        return 1800.0


def _newest_aged_in_version(releases, current, min_age_hours):
    """Newest published version greater than ``current`` whose files have all
    been on PyPI at least ``min_age_hours`` (the stability window). Returns the
    version string, or None if nothing newer has aged in yet.

    The unattended auto-updater installs THIS, not the absolute latest. During
    an active release run (many publishes less than the window apart) the
    absolute latest is always too fresh; gating on it alone meant a node never
    saw an installable target and stayed stuck on an old build indefinitely.
    Targeting the newest aged-in release keeps the fleet at
    latest-minus-window instead of frozen. (Burned 2026-06-13: a 2-day release
    spree left every version under 48h old, so daemons never auto-updated.)
    """
    from datetime import datetime as _dt, timezone as _tz
    _now = _dt.now(_tz.utc)
    best = None
    for ver, files in (releases or {}).items():
        if not _version_gt(ver, current):
            continue
        if best is not None and not _version_gt(ver, best):
            continue  # already have a newer candidate; skip the age cost
        times = [
            f.get("upload_time_iso_8601") or f.get("upload_time")
            for f in (files or [])
            if f.get("upload_time_iso_8601") or f.get("upload_time")
        ]
        if not times:
            continue
        try:
            t0 = min(_dt.fromisoformat(str(t).replace("Z", "+00:00")) for t in times)
            if t0.tzinfo is None:
                t0 = t0.replace(tzinfo=_tz.utc)
        except Exception:
            continue
        if (_now - t0).total_seconds() / 3600.0 < min_age_hours:
            continue
        best = ver
    return best


def _check_for_update():
    """Check PyPI for the latest version and record the result."""
    import dashboard as _d
    import urllib.request as _ur

    current = _d.__version__
    latest = current
    update_available = False

    try:
        req = _ur.Request(
            "https://pypi.org/pypi/clawmetry/json",
            headers={"User-Agent": f"clawmetry/{current}"},
        )
        with _ur.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            latest = data.get("info", {}).get("version", current)
    except Exception as exc:
        log.debug("Update check failed: %s", exc)
        return None

    update_available = _version_gt(latest, current)

    _record_update_check(current, latest, update_available, CHANGELOG_URL)

    # Auto-update target: the NEWEST published version above `current` that has
    # aged past the stability window (see _newest_aged_in_version). NOT the
    # absolute `latest` — during an active release run the absolute latest is
    # perpetually too fresh, so gating the silent install on it alone strands
    # every node on an ancient build forever. The banner still advertises the
    # absolute `latest` (above); only the unattended install targets the aged
    # release, keeping the fleet at latest-minus-stability-window.
    if update_available:
        try:
            _target = _newest_aged_in_version(
                data.get("releases", {}), current, _autoupdate_min_age_hours()
            )
            if _target and _version_gt(_target, current):
                _maybe_auto_update(current, _target, latest)
        except Exception as exc:
            log.warning("auto-update trigger failed: %s", exc)

    return {
        "current": current,
        "latest": latest,
        "update_available": update_available,
        "changelog_url": CHANGELOG_URL,
    }


# Set once an auto-update upgrade has been kicked off (the process is about to
# restart). Prevents re-triggering pip on every subsequent check in the gap
# before the restart lands. Reset on failure so the next check can retry.
_auto_update_in_progress = False

# version -> monotonic timestamp of its last FAILED install attempt. With the
# 60s check loop a persistently-broken target would otherwise re-run pip every
# minute; failed versions wait _autoupdate_retry_secs() before a retry.
_failed_update_attempts: dict = {}


def _exec_restart_disabled() -> bool:
    """Kill switch for the unsupervised-daemon re-exec:
    ``CLAWMETRY_AUTOUPDATE_EXEC_RESTART=0``."""
    val = os.environ.get("CLAWMETRY_AUTOUPDATE_EXEC_RESTART", "").strip().lower()
    return val in ("0", "false", "no", "off")


def _schedule_exec_restart(delay_secs: float = 2.0) -> None:
    """Re-exec the current process image so an UNSUPERVISED daemon (no
    launchd/systemd to respawn it — containers, manual `python sync.py`,
    kubectl-exec wrappers) actually starts running the wheel it just
    installed instead of holding the old build in memory until someone
    restarts it by hand. ``os.execv`` keeps the pid and argv, so whatever
    started the process sees nothing change; the boot rollback guard
    (clawmetry/update_guard.py) still protects against a crash-looping
    wheel. Not used on Windows (execv semantics differ) — there the
    install stays deferred to the next manual start."""
    def _reexec():
        try:
            log.info("auto-update: re-exec restart (unsupervised daemon) "
                     "argv=%s", sys.argv)
            os.execv(sys.executable, [sys.executable] + sys.argv)
        except Exception as exc:  # pragma: no cover — post-exec unreachable
            global _auto_update_in_progress
            _auto_update_in_progress = False
            log.warning("auto-update: re-exec failed (%s); new version "
                        "applies on next manual start", exc)
    t = threading.Timer(delay_secs, _reexec)
    t.daemon = True
    t.start()


def _maybe_auto_update(current, target, latest=None):
    """Install ``target`` (the newest aged-in release, chosen by
    ``_newest_aged_in_version``) automatically when ``auto_update`` is enabled.

    The stability-window rail is applied during target SELECTION, not here, so
    by the time we are called ``target`` is already known to have survived the
    window. ``target`` is a specific version (e.g. installing 0.12.510 even
    when 0.12.518 is the absolute ``latest`` but still too fresh), so the fleet
    keeps moving forward during active releases instead of freezing on an old
    build.
    """
    global _auto_update_in_progress
    if _auto_update_in_progress:
        return
    if _env_auto_update_disabled():
        log.info("auto-update: disabled via CLAWMETRY_AUTO_UPDATE env")
        return
    cfg = _get_update_check_config()
    if not cfg.get("auto_update"):
        return
    # The default-on policy applies only to the supervised sync daemon. A
    # dashboard process (frequently a foreground terminal session) must not
    # pip-install + exit underneath the user unless they explicitly opted in.
    if _process_role != "daemon" and not _auto_update_explicitly_set():
        return
    if not target or not _version_gt(target, current):
        return
    # Failed-install backoff: with the 60s check loop, a target whose pip
    # install failed must not be retried every minute.
    _last_fail = _failed_update_attempts.get(str(target))
    if _last_fail is not None and \
            (time.monotonic() - _last_fail) < _autoupdate_retry_secs():
        return
    # An UNSUPERVISED daemon (no launchd plist / systemd unit — containers,
    # kubectl-exec wrappers, a manual `python -m clawmetry.sync`) installs
    # the wheel with restart=False, then re-execs its own process image so
    # the new build actually starts running (previously it kept the old
    # wheel in memory indefinitely — a containerized node stayed stale until
    # someone bounced the pod by hand). Windows keeps the old
    # install-and-defer behavior; the env kill switch restores it anywhere.
    restart = True
    exec_restart = False
    if _process_role == "daemon" and not _daemon_supervised():
        restart = False
        exec_restart = (not sys.platform.startswith("win")
                        and not _exec_restart_disabled())
    _auto_update_in_progress = True
    log.info("auto-update: upgrading clawmetry v%s -> v%s (latest available v%s, "
             "restart=%s, exec_restart=%s)",
             current, target, latest or target, restart, exec_restart)
    try:
        from routes.meta import perform_self_update
        payload, _status = perform_self_update(
            reason="auto", restart=restart, target_version=target)
        if not (isinstance(payload, dict) and payload.get("ok")):
            log.warning("auto-update: upgrade failed, will retry in %.0fs: %s",
                        _autoupdate_retry_secs(), payload)
            _failed_update_attempts[str(target)] = time.monotonic()
            if len(_failed_update_attempts) > 64:
                _failed_update_attempts.pop(
                    min(_failed_update_attempts, key=_failed_update_attempts.get),
                    None,
                )
            _auto_update_in_progress = False  # allow retry; no restart was scheduled
            return
        _failed_update_attempts.pop(str(target), None)
        if exec_restart:
            _schedule_exec_restart()
    except Exception as exc:
        log.warning("auto-update: error during upgrade: %s", exc)
        _failed_update_attempts[str(target)] = time.monotonic()
        _auto_update_in_progress = False


def _update_check_worker(stop_event):
    """Background worker thread for periodic update checks.

    DAEMON role: poll PyPI every ``_update_check_interval_secs()`` (default
    60s) and auto-install anything newer — ClawMetry ships 20+ releases a
    day, so a release must reach the fleet in minutes, not on a daily-9AM
    schedule (founder call 2026-07-10; the screenshot trigger was a hosted
    feature telling a user their node would update "within about two days").

    DASHBOARD role: unchanged gentle cadence — startup check + one banner
    check per day after 9AM. The dashboard only shows the banner; the
    daemon is the process that installs, and on the standard install its
    fast loop keeps the shared check-history fresh for the banner anyway.
    """
    # Initial check on startup (after a boot-settle delay; interruptible).
    if stop_event.wait(60):
        return

    config = _get_update_check_config()
    if config.get("check_on_startup", True):
        _check_for_update()

    if _process_role == "daemon":
        while not stop_event.is_set():
            if stop_event.wait(_update_check_interval_secs()):
                return
            config = _get_update_check_config()
            if config.get("enabled", True):
                _check_for_update()
        return

    # Dashboard role: daily banner checks
    last_check_day = None
    while not stop_event.is_set():
        now = datetime.now(timezone.utc)
        current_day = now.date()

        config = _get_update_check_config()
        if config.get("check_daily", True) and config.get("enabled", True):
            if last_check_day != current_day:
                # Check around 9 AM local time
                if now.hour >= 9:
                    _check_for_update()
                    last_check_day = current_day

        # Check every hour
        stop_event.wait(3600)


def start_update_check_thread(role=None):
    """Start the background update check thread.

    ``role="daemon"`` marks this process as the supervised sync daemon, the
    only role where default-on auto-update acts (see ``_maybe_auto_update``).
    The dashboard calls this with no argument and keeps the opt-in behaviour.
    """
    global _update_check_thread, _update_check_stop_event, _process_role

    if role:
        _process_role = str(role)

    if _update_check_thread is not None and _update_check_thread.is_alive():
        return

    _init_update_check_db()
    _update_check_stop_event = threading.Event()
    _update_check_thread = threading.Thread(
        target=_update_check_worker,
        args=(_update_check_stop_event,),
        daemon=True,
        name="update-checker",
    )
    _update_check_thread.start()
    log.info("Update check thread started")


# ── API Endpoints ─────────────────────────────────────────────────────────────


@bp_update_check.route("/api/update-check/config", methods=["GET"])
def api_update_check_config():
    """Get update check configuration."""
    config = _get_update_check_config()
    return jsonify(config)


@bp_update_check.route("/api/update-check/config", methods=["POST"])
def api_update_check_config_post():
    """Update update check configuration."""
    data = request.get_json(silent=True) or {}
    allowed_keys = ["enabled", "check_on_startup", "check_daily", "auto_update", "dismissed_version"]
    updates = {k: v for k, v in data.items() if k in allowed_keys}
    _set_update_check_config(updates)
    return jsonify({"ok": True})


@bp_update_check.route("/api/update-check/status", methods=["GET"])
def api_update_check_status():
    """Get the current update check status.

    ``updater`` describes THIS process's effective auto-update posture
    (role, cadence, age gate, kill switch) so "is this node actually on
    the fast update loop?" is answerable from the API instead of by
    reading env vars and logs on the box. Note the dashboard process
    reports role=dashboard; the installing fast loop lives in the sync
    daemon (see the same endpoint there / the sync log line).
    """
    config = _get_update_check_config()
    latest = _get_latest_update_check()

    result = {
        "config": config,
        "latest_check": latest,
        "show_banner": _should_show_update_banner(config, latest),
        "updater": {
            "role": _process_role,
            "check_interval_secs": (
                _update_check_interval_secs()
                if _process_role == "daemon" else None
            ),
            "min_age_hours": _autoupdate_min_age_hours(),
            "env_disabled": _env_auto_update_disabled(),
        },
    }

    return jsonify(result)


@bp_update_check.route("/api/update-check/check-now", methods=["POST"])
def api_update_check_now():
    """Trigger an immediate update check."""
    result = _check_for_update()
    if result is None:
        return jsonify({"ok": False, "error": "Failed to check for updates"}), 500
    return jsonify({"ok": True, "result": result})


@bp_update_check.route("/api/update-check/dismiss", methods=["POST"])
def api_update_check_dismiss():
    """Dismiss the current update notification."""
    data = request.get_json(silent=True) or {}
    version = data.get("version", "")
    if version:
        _set_update_check_config({"dismissed_version": version})
    return jsonify({"ok": True})


@bp_update_check.route("/api/update-check/history", methods=["GET"])
def api_update_check_history():
    """Get update check history."""
    limit = request.args.get("limit", 10, type=int)
    try:
        with _get_fleet_db_lock():
            db = _get_fleet_db()
            rows = db.execute(
                """SELECT current_version, latest_version, update_available,
                           changelog_url, check_at
                   FROM update_check_history
                   ORDER BY check_at DESC LIMIT ?""",
                (limit,),
            ).fetchall()
            db.close()

        history = []
        for row in rows:
            history.append({
                "current": row["current_version"],
                "latest": row["latest_version"],
                "update_available": bool(row["update_available"]),
                "changelog_url": row["changelog_url"] or "",
                "checked_at": row["check_at"],
            })
        return jsonify({"history": history})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500
