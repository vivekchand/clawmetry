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
import threading
import time
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request

log = logging.getLogger(__name__)

bp_update_check = Blueprint("update_check", __name__)

# Module-level state
_update_check_thread = None
_update_check_stop_event = threading.Event()

CHANGELOG_URL = "https://github.com/vivekchand/clawmetry/blob/main/CHANGELOG.md"


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
            return {
                "current": row["current_version"],
                "latest": row["latest_version"],
                "update_available": bool(row["update_available"]),
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

    # Compare version tuples
    if latest != current:
        try:
            cur_parts = [int(x) for x in current.split(".")]
            lat_parts = [int(x) for x in latest.split(".")]
            update_available = lat_parts > cur_parts
        except Exception:
            update_available = True

    _record_update_check(current, latest, update_available, CHANGELOG_URL)

    return {
        "current": current,
        "latest": latest,
        "update_available": update_available,
        "changelog_url": CHANGELOG_URL,
    }


def _update_check_worker(stop_event):
    """Background worker thread for periodic update checks."""
    # Initial check on startup (after 60s delay)
    time.sleep(60)

    config = _get_update_check_config()
    if config.get("check_on_startup", True):
        _check_for_update()

    # Daily checks
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


def start_update_check_thread():
    """Start the background update check thread."""
    global _update_check_thread, _update_check_stop_event

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


def stop_update_check_thread():
    """Stop the background update check thread."""
    global _update_check_thread, _update_check_stop_event
    if _update_check_stop_event:
        _update_check_stop_event.set()
    if _update_check_thread:
        _update_check_thread.join(timeout=5)


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
    allowed_keys = ["enabled", "check_on_startup", "check_daily", "dismissed_version"]
    updates = {k: v for k, v in data.items() if k in allowed_keys}
    _set_update_check_config(updates)
    return jsonify({"ok": True})


@bp_update_check.route("/api/update-check/status", methods=["GET"])
def api_update_check_status():
    """Get the current update check status."""
    config = _get_update_check_config()
    latest = _get_latest_update_check()

    result = {
        "config": config,
        "latest_check": latest,
        "show_banner": _should_show_update_banner(config, latest),
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
