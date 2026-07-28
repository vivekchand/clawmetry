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
# Default-on auto-update applies to EVERY role since the 2026-07-28 founder
# directive (a release must reach every install on every OS within minutes);
# the roles differ only in HOW the process restarts onto the new wheel — see
# _restart_plan (supervised exit-and-respawn / POSIX in-place re-exec /
# Windows detached respawn). CLAWMETRY_AUTO_UPDATE=0 is the kill switch.
_process_role = "dashboard"

CHANGELOG_URL = "https://github.com/vivekchand/clawmetry/blob/main/CHANGELOG.md"


def _env_auto_update_disabled():
    """Kill switch: ``CLAWMETRY_AUTO_UPDATE=0`` disables unattended upgrades
    regardless of the stored config (fleet operators / CI / debugging).

    CI runners are implicitly disabled: an ephemeral runner must render the
    code it was started with, never swap itself for the newest wheel mid-job.
    The visual-diff harness proved why — whenever a [RELEASE] had just
    published, the PR-branch dashboard (versioned one release behind) saw the
    newer wheel on PyPI ~60s after boot, pip-updated, and exec-restarted in
    the middle of the screenshot sweep; every subsequent page logged
    ``base=200 head=0`` and the job failed. The failure rate tracked release
    cadence, and the flywheel releases constantly (diagnosed 2026-07-29 after
    three consecutive kills on #4181/#4182). ``CI`` is set by GitHub Actions,
    GitLab, CircleCI, Travis, and Azure; explicit ``CLAWMETRY_AUTO_UPDATE=1``
    re-arms it for anyone who genuinely wants in-CI self-update."""
    val = os.environ.get("CLAWMETRY_AUTO_UPDATE", "").strip().lower()
    if val in ("1", "true", "yes", "on"):
        return False
    if val in ("0", "false", "no", "off"):
        return True
    ci = os.environ.get("CI", "").strip().lower()
    return ci not in ("", "0", "false")


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


def _dashboard_supervised():
    """Same probe for the DASHBOARD process: is a launchd plist / systemd user
    unit present that would respawn it after an exit-to-restart? A foreground
    ``clawmetry`` in a terminal has neither, and Windows never does."""
    try:
        from pathlib import Path
        if sys.platform == "darwin":
            return (Path.home() / "Library" / "LaunchAgents"
                    / "com.clawmetry.dashboard.plist").exists()
        if sys.platform.startswith("linux"):
            unit = (Path.home() / ".config" / "systemd" / "user"
                    / "clawmetry-dashboard.service")
            return unit.exists() or bool(os.environ.get("INVOCATION_ID"))
    except Exception:
        pass
    return False


def _restart_plan(role: str, platform: str, supervised: bool) -> str:
    """Pure decision: how does THIS process get onto the new wheel?

    Returns one of:
      * ``"exit"``    — install with restart=True; the process exits and the
                        supervisor (launchd/systemd) respawns it on the new
                        wheel. Only valid when supervised.
      * ``"exec"``    — install with restart=False, then re-exec the same
                        process image in place (POSIX, unsupervised). The
                        terminal/parent sees nothing change.
      * ``"respawn"`` — install with restart=False, then hand a detached
                        helper the exact command line and exit; the helper
                        relaunches it a few seconds later (Windows, which has
                        neither a supervisor nor usable execv semantics).

    Every branch actively restarts. The old behaviour — Windows and
    unsupervised dashboards deferring "until the next manual start" — is
    exactly how a node that nobody restarts stays months stale. The env kill
    switches (CLAWMETRY_AUTO_UPDATE=0 / CLAWMETRY_NO_EXEC_RESTART=1) remain
    the opt-outs; this function only picks the mechanism.
    """
    if platform.startswith("win"):
        return "respawn"
    if supervised:
        return "exit"
    return "exec"


def _respawn_cmdline() -> list:
    """The exact command line to relaunch THIS process. Console-script
    installs relaunch via the (freshly pip-rewritten) launcher exe; module
    runs relaunch via the interpreter + argv.

    Windows console-script quirk (live-hit on the FIRST otherwise-successful
    unattended update, 2026-07-28): inside a process launched via
    ``Scripts/clawmetry.exe``, ``sys.argv[0]`` is the EXTENSIONLESS
    ``...\\Scripts\\clawmetry`` — no ``.exe`` suffix — so the suffix check
    alone missed it, the fallback built ``python ...\\Scripts\\clawmetry``
    (a file that does not exist on Windows), and the relaunch died with
    Errno 2 after a perfect install. Probe ``argv0 + '.exe'`` too.
    """
    argv0 = sys.argv[0] or ""
    if argv0.lower().endswith(".exe") and os.path.exists(argv0):
        return [argv0] + sys.argv[1:]
    if os.name == "nt" and argv0 and os.path.exists(argv0 + ".exe"):
        return [argv0 + ".exe"] + sys.argv[1:]
    return [sys.executable] + sys.argv


def _schedule_windows_respawn(delay_secs: float = 5.0) -> None:
    """Windows self-update: hand everything to the OUT-OF-PROCESS helper.

    In-process pip cannot work on Windows while ANY process runs
    ``Scripts/clawmetry.exe``: pip's overwrite hits WinError 32, and —
    measured live on a Windows 10 box (2026-07-28) — even RENAMING the
    running launcher is denied, so the pre-rename trick in
    ``perform_self_update`` silently no-ops and every install attempt
    fails into backoff. The reliable order is inverted:
    exit first, THEN install. ``clawmetry.update_respawn`` (spawned
    detached, running the old wheel's copy) waits for this pid to
    terminate, runs pip, and relaunches the exact command line either
    way. Output: ``~/.clawmetry/restart.log``.

    ``delay_secs`` retained for signature compatibility (unused).
    """
    del delay_secs
    if os.environ.get("PYTEST_CURRENT_TEST"):
        log.info("auto-update: windows respawn suppressed under pytest")
        return
    def _respawn():
        try:
            import subprocess
            flags = 0x00000008 | 0x00000200  # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
            cmd = _respawn_cmdline()
            log_dir = os.path.expanduser("~/.clawmetry")
            try:
                os.makedirs(log_dir, exist_ok=True)
            except Exception:
                pass
            log_path = os.path.join(log_dir, "restart.log")
            target = _pending_update_target.get("version") or "latest"
            subprocess.Popen(
                [sys.executable, "-m", "clawmetry.update_respawn",
                 str(os.getpid()), str(target), log_path] + cmd,
                creationflags=flags, close_fds=True,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            log.info("auto-update: windows out-of-process updater armed "
                     "(target=%s) cmd=%s", target, cmd)
            os._exit(0)
        except Exception as exc:
            global _auto_update_in_progress
            _auto_update_in_progress = False
            log.warning("auto-update: windows respawn failed (%s); new version "
                        "applies on next manual start", exc)
    t = threading.Timer(2.0, _respawn)
    t.daemon = True
    t.start()


# Target the Windows helper should install, stashed by _maybe_auto_update
# right before it schedules the respawn (the helper runs pip AFTER this
# process exits, so it cannot read process state).
_pending_update_target: dict = {}


def _record_update_attempt(target, outcome: str, detail: str = "") -> None:
    """Persist the last auto-update attempt where a human can find it.

    Both prior Windows failures were INVISIBLE: the dashboard's logger has
    no stdout handler, so 'upgrade failed' warnings went nowhere and the
    node just sat in backoff while /api/update-check/status said everything
    was fine (founder: "are you doing end to end test at all??",
    2026-07-28). The attempt row rides the same config table the status
    endpoint already reads, so /api/update-check/status and `clawmetry
    status` can answer "why is this node not updating" directly. Never
    raises.
    """
    try:
        _set_update_check_config({
            "last_attempt_target": str(target),
            "last_attempt_outcome": str(outcome),
            "last_attempt_detail": str(detail)[-500:],
            "last_attempt_at": str(time.time()),
        })
    except Exception as exc:
        log.debug("update-attempt record failed: %s", exc)


# Cross-process guard: on a standard install BOTH the daemon and the dashboard
# now run the fast install loop, and two concurrent `pip install` runs in one
# environment can corrupt each other. First process to grab the lock updates;
# the other skips its cycle (its next check sees current==latest, and the
# updater's restart already bounces the sibling service where one exists).
_UPDATE_LOCK_PATH = os.path.expanduser("~/.clawmetry/update-in-progress.lock")
_UPDATE_LOCK_STALE_SECS = 900  # a crashed updater must not wedge the fleet


def _acquire_update_lock() -> bool:
    """Atomically create the lock file. False when another live update holds
    it; a stale lock (older than _UPDATE_LOCK_STALE_SECS) is broken."""
    try:
        os.makedirs(os.path.dirname(_UPDATE_LOCK_PATH), exist_ok=True)
    except Exception:
        pass
    for _attempt in (1, 2):
        try:
            fd = os.open(_UPDATE_LOCK_PATH, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            try:
                os.write(fd, f"{os.getpid()} {time.time()}".encode())
            finally:
                os.close(fd)
            return True
        except FileExistsError:
            try:
                age = time.time() - os.path.getmtime(_UPDATE_LOCK_PATH)
                if age > _UPDATE_LOCK_STALE_SECS:
                    os.remove(_UPDATE_LOCK_PATH)
                    continue  # retry the O_EXCL create once
            except OSError:
                pass
            return False
        except Exception:
            # Filesystem weirdness must never block updates entirely.
            return True
    return False


def _release_update_lock() -> None:
    try:
        os.remove(_UPDATE_LOCK_PATH)
    except Exception:
        pass


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

# version -> monotonic DEADLINE before which a FAILED install must not be
# retried. With the 60s check loop a persistently-broken target would
# otherwise re-run pip every minute. The deadline length depends on WHY the
# install failed — see _retry_backoff_for_error.
_failed_update_attempts: dict = {}

# pip stderr signatures of "the release exists but this mirror hasn't seen it
# yet" — the PyPI simple-index/CDN propagation race. The JSON API (which the
# checker polls) routinely advertises a version 1-3 minutes before pip can
# install it. Caught live 2026-07-10: the very first fast-loop update attempt
# hit this and backed off a full 30 minutes for what was a 2-minute lag.
_PROPAGATION_ERR_SIGNS = (
    "No matching distribution",
    "Could not find a version",
)


def _propagation_retry_secs() -> float:
    """Short retry for index-propagation failures. Env override:
    ``CLAWMETRY_AUTOUPDATE_PROPAGATION_RETRY_SECS`` (default 120)."""
    try:
        return float(os.environ.get(
            "CLAWMETRY_AUTOUPDATE_PROPAGATION_RETRY_SECS", "120") or 120)
    except Exception:
        return 120.0


def _retry_backoff_for_error(error_text: str) -> float:
    """Backoff for a failed install: propagation lag retries in ~2 minutes,
    anything else (a genuinely broken target / env) waits the full backoff."""
    txt = str(error_text or "")
    if any(sig in txt for sig in _PROPAGATION_ERR_SIGNS):
        return _propagation_retry_secs()
    return _autoupdate_retry_secs()


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
    if os.environ.get("PYTEST_CURRENT_TEST"):
        # A test that reaches this path must never replace the pytest
        # process image two seconds later. Tests monkeypatch this function
        # to assert scheduling; this guard is the belt for the ones that
        # forget (the pre-change code armed a REAL execv timer from
        # test_unsupervised_daemon_defers_restart).
        log.info("auto-update: exec restart suppressed under pytest")
        return
    def _reexec():
        try:
            log.info("auto-update: re-exec restart (unsupervised process) "
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
        log.info("auto-update: disabled (CLAWMETRY_AUTO_UPDATE=0 or CI env)")
        return
    cfg = _get_update_check_config()
    if not cfg.get("auto_update"):
        return
    # Default-on now covers EVERY role on EVERY OS. The old rail — only the
    # supervised daemon acts on the default — meant a local-only install
    # (dashboard, no daemon) NEVER self-updated: the founder's own Windows
    # demo box sat on 0.12.573 for a full release cycle with the banner
    # politely reporting update_available=true (2026-07-28). The safety
    # concern behind the old rail ("don't pip-install + exit underneath a
    # foreground user") is addressed by _restart_plan: unsupervised
    # processes re-exec in place (POSIX) or detach-respawn (Windows), they
    # do not exit-and-die. CLAWMETRY_AUTO_UPDATE=0 remains the kill switch.
    if not target or not _version_gt(target, current):
        return
    # Failed-install backoff: with the 60s check loop, a target whose pip
    # install failed must not be retried every minute. The stored value is
    # the DEADLINE (propagation lag ~2 min, real failures 30 min).
    _retry_at = _failed_update_attempts.get(str(target))
    if _retry_at is not None and time.monotonic() < _retry_at:
        return
    supervised = (_daemon_supervised() if _process_role == "daemon"
                  else _dashboard_supervised())
    plan = _restart_plan(_process_role, sys.platform, supervised)
    if plan == "exec" and _exec_restart_disabled():
        plan = "defer"
    restart = plan == "exit"
    # Two fast loops (daemon + dashboard) share one environment; only one may
    # pip at a time. The loser skips — its next 60s check sees current==latest.
    if not _acquire_update_lock():
        log.info("auto-update: another process is updating this install; skipping cycle")
        return
    _auto_update_in_progress = True
    log.info("auto-update: upgrading clawmetry v%s -> v%s (latest available v%s, "
             "role=%s, plan=%s)",
             current, target, latest or target, _process_role, plan)
    _record_update_attempt(target, "started", f"role={_process_role} plan={plan}")
    if plan == "respawn":
        # Windows: NO in-process pip. While any process runs Scripts/
        # clawmetry.exe, pip's overwrite fails with WinError 32 and even
        # renaming the running launcher is denied (measured live 2026-07-28;
        # the pre-rename in perform_self_update silently no-ops there, which
        # is why every prior Windows auto-update failed straight into a
        # 30-minute backoff, invisibly). The out-of-process helper
        # (clawmetry.update_respawn) installs AFTER this process exits and
        # relaunches it either way.
        _pending_update_target["version"] = str(target)
        _record_update_attempt(target, "handoff",
                               "out-of-process helper armed; process exits")
        # The lock is NOT released here: it rides through the handoff and the
        # HELPER deletes it when its pip run finishes. Releasing before the
        # handoff let the daemon's and dashboard's helpers pip CONCURRENTLY
        # (live-hit on the 0.12.580 run, 2026-07-28: one helper's uninstall
        # raced the other's install, WinError 32 + a metadata-bricked
        # site-packages with ~lawmetry corpses). The 15-minute staleness
        # window still breaks the lock if a helper dies before cleanup.
        _schedule_windows_respawn()
        return
    try:
        from routes.meta import perform_self_update
        payload, _status = perform_self_update(
            reason="auto", restart=restart, target_version=target)
        if not (isinstance(payload, dict) and payload.get("ok")):
            _err = payload.get("error", "") if isinstance(payload, dict) else ""
            _backoff = _retry_backoff_for_error(_err)
            log.warning("auto-update: upgrade failed, will retry in %.0fs: %s",
                        _backoff, payload)
            _record_update_attempt(target, "failed", _err[-400:])
            _failed_update_attempts[str(target)] = time.monotonic() + _backoff
            if len(_failed_update_attempts) > 64:
                _failed_update_attempts.pop(
                    min(_failed_update_attempts, key=_failed_update_attempts.get),
                    None,
                )
            _auto_update_in_progress = False  # allow retry; no restart was scheduled
            _release_update_lock()
            return
        _failed_update_attempts.pop(str(target), None)
        _record_update_attempt(target, "installed", f"plan={plan}")
        _release_update_lock()
        if plan == "exec":
            _schedule_exec_restart()
        elif plan == "defer":
            log.info("auto-update: installed v%s; restart deferred "
                     "(CLAWMETRY_NO_EXEC_RESTART set)", target)
    except Exception as exc:
        log.warning("auto-update: error during upgrade: %s", exc)
        _failed_update_attempts[str(target)] = (
            time.monotonic() + _autoupdate_retry_secs()
        )
        _auto_update_in_progress = False
        _release_update_lock()


def _fast_loop_active() -> bool:
    """Should this process poll PyPI on the fast (install) cadence?

    Daemon: always. Dashboard: whenever auto-update is effectively on —
    which is the default. With the kill switch (CLAWMETRY_AUTO_UPDATE=0) or
    a stored auto_update=false, the dashboard drops to the banner-only
    daily cadence."""
    if _process_role == "daemon":
        return True
    return (not _env_auto_update_disabled()
            and _get_update_check_config().get("auto_update", True))


def _update_check_worker(stop_event):
    """Background worker thread for periodic update checks.

    DAEMON role: poll PyPI every ``_update_check_interval_secs()`` (default
    60s) and auto-install anything newer — ClawMetry ships 20+ releases a
    day, so a release must reach the fleet in minutes, not on a daily-9AM
    schedule (founder call 2026-07-10; the screenshot trigger was a hosted
    feature telling a user their node would update "within about two days").

    DASHBOARD role: same fast loop whenever auto-update is effectively on.
    A local-only install (no sync daemon — every Windows box before
    `clawmetry connect`, and any `pip install clawmetry && clawmetry`) has
    no other process that could install, so the old daily-9AM banner cadence
    meant those nodes were never on the current release (the founder's
    Windows demo machine stayed a full release behind with the banner
    dutifully reporting update_available=true, 2026-07-28). The bar is: a
    release reaches EVERY install, on every OS, within minutes. When
    auto-update is off (CLAWMETRY_AUTO_UPDATE=0 or stored config), the
    dashboard keeps the gentle banner-only cadence.
    """
    # Initial check on startup (after a boot-settle delay; interruptible).
    if stop_event.wait(60):
        return

    config = _get_update_check_config()
    if config.get("check_on_startup", True):
        _check_for_update()

    last_check_day = None
    while not stop_event.is_set():
        if _fast_loop_active():
            if stop_event.wait(_update_check_interval_secs()):
                return
            config = _get_update_check_config()
            if config.get("enabled", True):
                _check_for_update()
            continue

        # Banner-only cadence (auto-update explicitly off): one check per
        # day after 9AM local, re-evaluating hourly (config can flip the
        # fast loop back on without a restart).
        now = datetime.now(timezone.utc)
        current_day = now.date()
        config = _get_update_check_config()
        if config.get("check_daily", True) and config.get("enabled", True):
            if last_check_day != current_day and now.hour >= 9:
                _check_for_update()
                last_check_day = current_day
        if stop_event.wait(3600):
            return


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

    # Last auto-update ATTEMPT (started/handoff/installed/failed + detail).
    # Read straight from the config table: these keys are written by
    # _record_update_attempt and are exactly the "why is this node not
    # updating" answer that used to be invisible.
    attempt = {}
    try:
        with _get_fleet_db_lock():
            db = _get_fleet_db()
            rows = db.execute(
                "SELECT key, value FROM update_check_config "
                "WHERE key LIKE 'last_attempt_%'"
            ).fetchall()
            db.close()
        attempt = {r["key"]: r["value"] for r in rows}
    except Exception:
        attempt = {}

    result = {
        "config": config,
        "latest_check": latest,
        "show_banner": _should_show_update_banner(config, latest),
        "last_attempt": attempt,
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


@bp_update_check.route("/api/update-check/dismiss", methods=["POST"])
def api_update_check_dismiss():
    """Dismiss the current update notification."""
    data = request.get_json(silent=True) or {}
    version = data.get("version", "")
    if version:
        _set_update_check_config({"dismissed_version": version})
    return jsonify({"ok": True})
