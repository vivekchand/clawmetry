#!/usr/bin/env python3
"""
ClawMetry - See your agent think 🦞

Real-time observability dashboard for OpenClaw AI agents.
Single-file Flask app with zero config - auto-detects your setup.

Usage:
    clawmetry                             # Auto-detect everything
    clawmetry --port 9000                 # Custom port
    clawmetry --workspace ~/bot           # Custom workspace
    OPENCLAW_HOME=~/bot clawmetry

https://github.com/vivekchand/clawmetry
MIT License
"""

import os
import sys

# When run as `python dashboard.py`, this module is registered as `__main__`,
# not `dashboard`. Route blueprints in routes/ do `import dashboard as _d` at
# call time — without this alias, that import re-executes all 33k lines as a
# second `dashboard` module on first request, causing 10s+ timeouts on Windows
# CI (issue surfaced by the bp_sessions refactor).
sys.modules.setdefault("dashboard", sys.modules[__name__])

# Force UTF-8 output on Windows (emoji in BANNER would crash with cp1252)
if sys.platform == "win32":
    import io

    try:
        sys.stdout = io.TextIOWrapper(
            sys.stdout.buffer, encoding="utf-8", errors="replace"
        )
        sys.stderr = io.TextIOWrapper(
            sys.stderr.buffer, encoding="utf-8", errors="replace"
        )
    except Exception:
        pass

import glob
import json
import socket
from collections import deque, defaultdict

# In-process ring-buffer for quick action history (last 50 entries)
_quick_action_log = deque(maxlen=50)

import argparse
import subprocess
import time
import threading
import select
from datetime import datetime, timezone, timedelta
from flask import (
    Flask,
    render_template_string,
    request,
    jsonify,
    Response,
    make_response,
)

# Route blueprints extracted from this file (Phase 5 modularisation).
# Late-imports inside each handler keep dashboard.py as the single source of
# truth for module-level helpers — see routes/sessions.py for the pattern.
from routes.sessions import bp_sessions
from routes.brain import bp_brain
from routes.advisor import bp_advisor
from routes.selfevolve import bp_selfevolve

# Module-level helpers extracted to helpers/*.py (Phase 6 modularisation).
# Re-exported here so existing `_d.<name>` references in routes/*.py keep
# working without code changes. Over time, route modules will import from
# helpers/ directly and these re-exports will be retired.
from helpers.pricing import (  # noqa: F401 — re-export for routes/
    _provider_from_model,
    _infer_provider_from_model,
)
from helpers.logs import (  # noqa: F401 — re-export for routes/
    _grep_log_file,
    _tail_lines,
    _get_log_dirs,
    _find_log_file,
)
from helpers.streams import (  # noqa: F401 — re-export for routes/
    SSE_MAX_SECONDS,
    _acquire_stream_slot,
    _release_stream_slot,
)
from helpers.hardware import _detect_host_hardware  # noqa: F401 — re-export for routes/
from helpers.gateway import (  # noqa: F401 — re-export for routes/
    _gw_invoke,
    _gw_invoke_docker,
    _gw_ws_rpc,
)
from routes.usage import bp_usage
from routes.crons import bp_crons
from routes.health import bp_health
from routes.alerts import bp_alerts, bp_budget
from routes.channels import bp_channels
from routes.overview import bp_overview
from routes.components import bp_components
from routes.fleet_history import bp_fleet, bp_history
from routes.infra import bp_logs, bp_memory, bp_security, bp_config
from routes.meta import bp_auth, bp_gateway, bp_otel, bp_version, bp_version_impact, bp_clusters
from routes.nemoclaw import bp_nemoclaw
from routes.skills import bp_skills
from routes.heartbeat import bp_heartbeat
from routes.autonomy import bp_autonomy
from routes.selfconfig import bp_selfconfig
from helpers.openapi import bp_openapi

# History / time-series module
try:
    from history import HistoryDB, HistoryCollector, AgentReliabilityScorer

    _HAS_HISTORY = True
except ImportError:
    _HAS_HISTORY = False
    HistoryDB = None
    HistoryCollector = None
    AgentReliabilityScorer = None

_history_db = None
_history_collector = None

# Optional: OpenTelemetry protobuf support for OTLP receiver
_HAS_OTEL_PROTO = False
try:
    from opentelemetry.proto.collector.metrics.v1 import metrics_service_pb2
    from opentelemetry.proto.collector.trace.v1 import trace_service_pb2

    _HAS_OTEL_PROTO = True
except ImportError:
    metrics_service_pb2 = None
    trace_service_pb2 = None

__version__ = "0.12.141"

# Extensions (Phase 2) — load plugins at import time; safe no-op if package not installed
try:
    from clawmetry.extensions import emit as _ext_emit, load_plugins as _ext_load

    _ext_load()
except ImportError:

    def _ext_emit(event, payload=None):
        pass  # noqa


app = Flask(
    __name__,
    static_folder=os.path.join(os.path.dirname(__file__), 'clawmetry', 'static'),
    template_folder=os.path.join(os.path.dirname(__file__), 'clawmetry', 'templates'),
)

# ── Cross-platform helpers ──────────────────────────────────────────────
import re as _re
import tempfile as _tempfile
import platform as _platform


# _grep_log_file, _tail_lines, _get_log_dirs moved to helpers/logs.py (re-exported above)


# _detect_host_hardware moved to helpers/hardware.py (re-exported above)


_CURRENT_PLATFORM = _platform.system().lower()
# ── End cross-platform helpers ──────────────────────────────────────────

# ── Configuration (auto-detected, overridable via CLI/env) ──────────────
MC_URL = os.environ.get("MC_URL", "")  # Optional Mission Control URL, empty = disabled
WORKSPACE = None
MEMORY_DIR = None
LOG_DIR = None
SESSIONS_DIR = None
USER_NAME = None
GATEWAY_URL = None  # e.g. http://localhost:18789
GATEWAY_TOKEN = None  # Bearer token for /tools/invoke
CET = timezone(timedelta(hours=1))
# SSE_MAX_SECONDS moved to helpers/streams.py (re-exported above)
# Stream-slot caps + state moved to helpers/streams.py (re-exported above)
# _active_brain_stream_clients moved to helpers/streams.py
EXTRA_SERVICES = []  # List of {'name': str, 'port': int} from --monitor-service flags

# ── Multi-Node Fleet Configuration ─────────────────────────────────────
FLEET_API_KEY = os.environ.get("CLAWMETRY_FLEET_KEY", "")
FLEET_DB_PATH = None  # Set via CLI or auto-detected
FLEET_NODE_TIMEOUT = 300  # seconds before node is considered offline

# ── Budget & Alert Configuration ───────────────────────────────────────
_budget_paused = False
_budget_paused_at = 0
_budget_paused_reason = ""
_budget_alert_cooldowns = {}  # rule_id -> last_fired_timestamp
_AGENT_DOWN_SECONDS = 300  # 5 min with no OTLP data = agent down alert
_ALERTS_CONFIG_FILE = os.path.expanduser("~/.openclaw/clawmetry-alerts.json")
_security_posture_hash = ""
_ALERTS_CONFIG_FILE = os.path.expanduser("~/.openclaw/clawmetry-alerts.json")
_security_posture_hash = ""
# Token velocity alert thresholds (GH#313)
_VELOCITY_TOKENS_PER_2MIN = 10000  # tokens in any 2-minute window
_VELOCITY_CONSECUTIVE_TOOLS = 20  # consecutive tool calls without human turn
_VELOCITY_COST_PER_MIN = 0.10  # USD/min cost rate

# ── OTLP Metrics Store ─────────────────────────────────────────────────
METRICS_FILE = None  # Set via CLI/env, defaults to {WORKSPACE}/.clawmetry-metrics.json
_metrics_lock = threading.Lock()
_otel_last_received = 0  # timestamp of last OTLP data received

metrics_store = {
    "tokens": [],  # [{timestamp, input, output, total, model, channel, provider}]
    "cost": [],  # [{timestamp, usd, model, channel, provider}]
    "runs": [],  # [{timestamp, duration_ms, model, channel}]
    "messages": [],  # [{timestamp, channel, outcome, duration_ms}]
    "webhooks": [],  # [{timestamp, channel, type}]
    "queues": [],  # [{timestamp, channel, depth}]
}
MAX_STORE_ENTRIES = 10_000
STORE_RETENTION_DAYS = 14


def _metrics_file_path():
    """Get the path to the metrics persistence file."""
    if METRICS_FILE:
        return METRICS_FILE
    if WORKSPACE:
        return os.path.join(WORKSPACE, ".clawmetry-metrics.json")
    return os.path.expanduser("~/.clawmetry-metrics.json")


def _load_metrics_from_disk():
    """Load persisted metrics on startup."""
    global metrics_store, _otel_last_received
    path = _metrics_file_path()
    if not os.path.exists(path):
        return
    try:
        with open(path, "r") as f:
            data = json.load(f)
        if isinstance(data, dict):
            for key in metrics_store:
                if key in data and isinstance(data[key], list):
                    metrics_store[key] = data[key][-MAX_STORE_ENTRIES:]
            _otel_last_received = data.get("_last_received", 0)
        _expire_old_entries()
    except json.JSONDecodeError as e:
        print(f"[warn]  Warning: Failed to parse metrics file {path}: {e}")
        # Create backup of corrupted file
        backup_path = f"{path}.corrupted.{int(time.time())}"
        try:
            os.rename(path, backup_path)
            print(f"💾 Corrupted file backed up to {backup_path}")
        except OSError:
            pass
    except (IOError, OSError) as e:
        print(f"[warn]  Warning: Failed to read metrics file {path}: {e}")
    except Exception as e:
        print(f"[warn]  Warning: Unexpected error loading metrics: {e}")


def _save_metrics_to_disk():
    """Persist metrics store to JSON file."""
    path = _metrics_file_path()
    try:
        d = os.path.dirname(path)
        if d:
            os.makedirs(d, exist_ok=True)
        data = {}
        with _metrics_lock:
            for k in metrics_store:
                data[k] = list(metrics_store[k])
        data["_last_received"] = _otel_last_received
        data["_saved_at"] = time.time()
        tmp = path + ".tmp"
        with open(tmp, "w") as f:
            json.dump(data, f)
        os.replace(tmp, path)
    except OSError as e:
        print(f"[warn]  Warning: Failed to save metrics to {path}: {e}")
        if "No space left on device" in str(e):
            print("💾 Disk full! Consider cleaning up old files or expanding storage.")
    except json.JSONEncodeError as e:
        print(f"[warn]  Warning: Failed to serialize metrics data: {e}")
    except Exception as e:
        print(f"[warn]  Warning: Unexpected error saving metrics: {e}")


def _expire_old_entries():
    """Remove entries older than STORE_RETENTION_DAYS."""
    cutoff = time.time() - (STORE_RETENTION_DAYS * 86400)
    with _metrics_lock:
        for key in metrics_store:
            metrics_store[key] = [
                e for e in metrics_store[key] if e.get("timestamp", 0) > cutoff
            ][-MAX_STORE_ENTRIES:]


def _add_metric(category, entry):
    """Add an entry to the metrics store (thread-safe)."""
    global _otel_last_received
    with _metrics_lock:
        metrics_store[category].append(entry)
        if len(metrics_store[category]) > MAX_STORE_ENTRIES:
            metrics_store[category] = metrics_store[category][-MAX_STORE_ENTRIES:]
        _otel_last_received = time.time()
    # Check budget on cost entries
    if category == "cost":
        try:
            _budget_check()
        except Exception:
            pass


def _metrics_flush_loop():
    """Background thread: save metrics to disk every 60 seconds."""
    while True:
        time.sleep(60)
        try:
            _expire_old_entries()
            _save_metrics_to_disk()
        except KeyboardInterrupt:
            print("📊 Metrics flush loop shutting down...")
            break
        except Exception as e:
            print(f"[warn]  Warning: Error in metrics flush loop: {e}")
            # Continue running despite errors


def _start_metrics_flush_thread():
    """Start the background metrics flush thread."""
    t = threading.Thread(target=_metrics_flush_loop, daemon=True)
    t.start()


def _has_otel_data():
    """Check if we have any OTLP metrics data."""
    return any(len(metrics_store[k]) > 0 for k in metrics_store)


# ── Multi-Node Fleet Database ───────────────────────────────────────────
import sqlite3 as _sqlite3

_fleet_db_lock = threading.Lock()


def _fleet_db_path():
    """Get path to the fleet SQLite database.

    Always uses ~/.clawmetry/fleet.db, creating the directory if needed.
    The curl installer creates ~/.clawmetry/ but we must not rely on that --
    this function is the authoritative path and ensures the dir exists.

    Falls back to a workspace-relative path when WORKSPACE is set (dev mode).
    """
    if FLEET_DB_PATH:
        return FLEET_DB_PATH
    if WORKSPACE:
        return os.path.join(WORKSPACE, ".clawmetry-fleet.db")
    # Always use ~/.clawmetry/fleet.db -- create the dir if the installer
    # has not run yet or this is a fresh pip install without curl | bash.
    preferred_dir = os.path.expanduser("~/.clawmetry")
    try:
        os.makedirs(preferred_dir, exist_ok=True)
    except OSError:
        pass  # makedirs failed (permissions?), fall through to legacy path
    if os.path.isdir(preferred_dir):
        return os.path.join(preferred_dir, "fleet.db")
    # Last resort: legacy flat file in home dir (pre-installer environments)
    return os.path.expanduser("~/.clawmetry-fleet.db")


def _fleet_db():
    """Get a SQLite connection to the fleet database."""
    path = _fleet_db_path()
    # Ensure parent directory exists (defence-in-depth: guards against callers
    # that bypass _fleet_init_db, and older code paths that skipped makedirs).
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    db = _sqlite3.connect(path, timeout=10)
    db.row_factory = _sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    return db


def _fleet_init_db():
    """Initialize fleet database tables."""
    path = _fleet_db_path()
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    db = _fleet_db()
    db.executescript("""
        CREATE TABLE IF NOT EXISTS nodes (
            node_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            hostname TEXT,
            tags TEXT,
            api_key_hash TEXT,
            version TEXT,
            registered_at REAL,
            last_seen_at REAL,
            status TEXT DEFAULT 'unknown'
        );
        CREATE TABLE IF NOT EXISTS node_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            node_id TEXT NOT NULL,
            timestamp REAL NOT NULL,
            metrics_json TEXT NOT NULL,
            FOREIGN KEY (node_id) REFERENCES nodes(node_id)
        );
        CREATE INDEX IF NOT EXISTS idx_node_metrics_node_ts
            ON node_metrics(node_id, timestamp DESC);
    """)
    db.close()


def _fleet_check_key(req):
    """Validate fleet API key from request header. Returns True if valid."""
    if not FLEET_API_KEY:
        return True  # No key configured = open (for dev/testing)
    key = req.headers.get("X-Fleet-Key", "")
    return key == FLEET_API_KEY


def _fleet_update_statuses():
    """Update node statuses based on last_seen_at."""
    cutoff = time.time() - FLEET_NODE_TIMEOUT
    with _fleet_db_lock:
        db = _fleet_db()
        db.execute(
            "UPDATE nodes SET status = 'offline' WHERE last_seen_at < ? AND status != 'offline'",
            (cutoff,),
        )
        db.commit()
        db.close()


def _fleet_prune_metrics():
    """Remove metrics older than 7 days."""
    cutoff = time.time() - (7 * 86400)
    with _fleet_db_lock:
        db = _fleet_db()
        db.execute("DELETE FROM node_metrics WHERE timestamp < ?", (cutoff,))
        db.commit()
        db.close()


def _fleet_maintenance_loop():
    """Background thread: update statuses and prune old metrics."""
    while True:
        time.sleep(300)  # every 5 minutes
        try:
            _fleet_update_statuses()
            _fleet_prune_metrics()
        except Exception as e:
            print(f"Warning: Fleet maintenance error: {e}")


def _start_fleet_maintenance_thread():
    """Start the background fleet maintenance thread."""
    t = threading.Thread(target=_fleet_maintenance_loop, daemon=True)
    t.start()


# ── Budget & Alert Database ────────────────────────────────────────────


def _budget_init_db():
    """Initialize budget and alert tables in the fleet database."""
    db = _fleet_db()
    db.executescript("""
        CREATE TABLE IF NOT EXISTS budget_config (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS alert_rules (
            id TEXT PRIMARY KEY,
            type TEXT NOT NULL,
            threshold REAL NOT NULL,
            channels TEXT NOT NULL,
            cooldown_min INTEGER DEFAULT 30,
            enabled INTEGER DEFAULT 1,
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS alert_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rule_id TEXT,
            type TEXT NOT NULL,
            message TEXT NOT NULL,
            channel TEXT NOT NULL,
            fired_at REAL NOT NULL,
            acknowledged INTEGER DEFAULT 0,
            ack_at REAL,
            FOREIGN KEY (rule_id) REFERENCES alert_rules(id)
        );
        CREATE INDEX IF NOT EXISTS idx_alert_history_fired
            ON alert_history(fired_at DESC);
        CREATE INDEX IF NOT EXISTS idx_alert_history_rule
            ON alert_history(rule_id, fired_at DESC);
    """)
    db.close()


def _get_budget_config():
    """Get all budget config as a dict."""
    defaults = {
        "daily_limit": 0,
        "weekly_limit": 0,
        "monthly_limit": 0,
        "auto_pause_enabled": False,
        "auto_pause_threshold_pct": 100,
        "auto_pause_threshold_usd": 0,
        "auto_pause_action": "pause",
        "warning_threshold_pct": 80,
        "telegram_bot_token": "",
        "telegram_chat_id": "",
    }
    try:
        with _fleet_db_lock:
            db = _fleet_db()
            rows = db.execute("SELECT key, value FROM budget_config").fetchall()
            db.close()
        for row in rows:
            k = row["key"]
            v = row["value"]
            if k in defaults:
                if isinstance(defaults[k], bool):
                    defaults[k] = v.lower() in ("true", "1", "yes")
                elif isinstance(defaults[k], (int, float)):
                    try:
                        defaults[k] = float(v)
                    except ValueError:
                        pass
                else:
                    defaults[k] = v
    except Exception:
        pass
    return defaults


def _set_budget_config(updates):
    """Update budget config keys."""
    now = time.time()
    with _fleet_db_lock:
        db = _fleet_db()
        for k, v in updates.items():
            db.execute(
                "INSERT OR REPLACE INTO budget_config (key, value, updated_at) VALUES (?, ?, ?)",
                (k, str(v), now),
            )
        db.commit()
        db.close()


def _default_alerts_webhook_config():
    return {
        "webhook_url": "",
        "slack_webhook_url": "",
        "discord_webhook_url": "",
        "cost_spike_alerts": True,
        "agent_error_rate_alerts": True,
        "security_posture_changes": True,
    }


def _load_alerts_webhook_config():
    cfg = _default_alerts_webhook_config()
    try:
        if os.path.exists(_ALERTS_CONFIG_FILE):
            with open(_ALERTS_CONFIG_FILE, "r") as f:
                data = json.load(f)
            if isinstance(data, dict):
                for k in cfg:
                    if k in data:
                        cfg[k] = data[k]
    except Exception:
        pass
    return cfg


def _save_alerts_webhook_config(updates):
    cfg = _load_alerts_webhook_config()
    for k in cfg:
        if k in updates:
            cfg[k] = updates[k]
    try:
        os.makedirs(os.path.dirname(_ALERTS_CONFIG_FILE), exist_ok=True)
        with open(_ALERTS_CONFIG_FILE, "w") as f:
            json.dump(cfg, f, indent=2)
    except Exception:
        pass
    return cfg


def _should_send_webhook_for_type(alert_type):
    cfg = _load_alerts_webhook_config()
    if alert_type in (
        "cost_spike",
        "daily_threshold_breached",
        "weekly_threshold_breached",
    ):
        return bool(cfg.get("cost_spike_alerts", True))
    if alert_type == "agent_error_rate":
        return bool(cfg.get("agent_error_rate_alerts", True))
    if alert_type == "security_posture_change":
        return bool(cfg.get("security_posture_changes", True))
    return True


def _dispatch_configured_webhooks(alert_type, payload):
    if not _should_send_webhook_for_type(alert_type):
        return
    cfg = _load_alerts_webhook_config()
    generic_url = str(cfg.get("webhook_url", "")).strip()
    slack_url = str(cfg.get("slack_webhook_url", "")).strip()
    discord_url = str(cfg.get("discord_webhook_url", "")).strip()
    if generic_url:
        _send_webhook_alert(generic_url, payload, payload_type="generic")
    if slack_url:
        _send_webhook_alert(slack_url, payload, payload_type="slack")
    if discord_url:
        _send_webhook_alert(discord_url, payload, payload_type="discord")


def _get_budget_status():
    """Calculate current spending vs budget limits."""
    global _budget_paused, _budget_paused_at, _budget_paused_reason
    config = _get_budget_config()
    now = time.time()
    today_start = (
        datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
    )
    week_start = (
        (datetime.now() - timedelta(days=datetime.now().weekday()))
        .replace(hour=0, minute=0, second=0, microsecond=0)
        .timestamp()
    )
    month_start = (
        datetime.now()
        .replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        .timestamp()
    )

    daily_spent = 0.0
    weekly_spent = 0.0
    monthly_spent = 0.0

    with _metrics_lock:
        for entry in metrics_store["cost"]:
            ts = entry.get("timestamp", 0)
            usd = entry.get("usd", 0)
            if ts >= month_start:
                monthly_spent += usd
                if ts >= week_start:
                    weekly_spent += usd
                    if ts >= today_start:
                        daily_spent += usd

    daily_limit = config.get("daily_limit", 0)
    weekly_limit = config.get("weekly_limit", 0)
    monthly_limit = config.get("monthly_limit", 0)

    return {
        "daily_spent": round(daily_spent, 4),
        "weekly_spent": round(weekly_spent, 4),
        "monthly_spent": round(monthly_spent, 4),
        "daily_limit": daily_limit,
        "weekly_limit": weekly_limit,
        "monthly_limit": monthly_limit,
        "daily_pct": round(
            (daily_spent / daily_limit * 100) if daily_limit > 0 else 0, 1
        ),
        "weekly_pct": round(
            (weekly_spent / weekly_limit * 100) if weekly_limit > 0 else 0, 1
        ),
        "monthly_pct": round(
            (monthly_spent / monthly_limit * 100) if monthly_limit > 0 else 0, 1
        ),
        "paused": _budget_paused,
        "paused_at": _budget_paused_at,
        "paused_reason": _budget_paused_reason,
        "auto_pause_enabled": config.get("auto_pause_enabled", False),
        "auto_pause_threshold_usd": config.get("auto_pause_threshold_usd", 0),
        "auto_pause_action": config.get("auto_pause_action", "pause"),
        "warning_threshold_pct": config.get("warning_threshold_pct", 80),
    }


def _budget_check():
    """Check budget limits and fire alerts/auto-pause if needed."""
    global _budget_paused, _budget_paused_at, _budget_paused_reason
    if _budget_paused:
        return
    now = time.time()
    config = _get_budget_config()
    status = _get_budget_status()
    warning_pct = config.get("warning_threshold_pct", 80)
    pause_pct = config.get("auto_pause_threshold_pct", 100)

    # Check each period
    for period in ["daily", "weekly", "monthly"]:
        limit = config.get(f"{period}_limit", 0)
        if limit <= 0:
            continue
        spent = status[f"{period}_spent"]
        pct = (spent / limit * 100) if limit > 0 else 0

        if period in ("daily", "weekly") and spent >= limit:
            rule_id = f"webhook_{period}_threshold_breached"
            last_fired = _budget_alert_cooldowns.get(rule_id, 0)
            if now - last_fired >= 900:
                _budget_alert_cooldowns[rule_id] = now
                _dispatch_configured_webhooks(
                    f"{period}_threshold_breached",
                    {
                        "type": f"{period}_threshold_breached",
                        "agent": "main",
                        "cost_usd": round(spent, 4),
                        "threshold": round(limit, 4),
                        "timestamp": now,
                        "message": f"{period.capitalize()} cost threshold breached: ${spent:.2f} / ${limit:.2f}",
                    },
                )

        # Warning alert
        if pct >= warning_pct and pct < pause_pct:
            _fire_alert(
                rule_id=f"budget_{period}_warning",
                alert_type="threshold",
                message=f"Budget warning: {period} spending ${spent:.2f} is {pct:.0f}% of ${limit:.2f} limit",
                channels=["banner", "telegram"],
            )

        # Auto-pause
        if pct >= pause_pct and config.get("auto_pause_enabled", False):
            _budget_paused = True
            _budget_paused_at = time.time()
            _budget_paused_reason = (
                f"{period.capitalize()} budget exceeded: ${spent:.2f} / ${limit:.2f}"
            )
            _fire_alert(
                rule_id=f"budget_{period}_exceeded",
                alert_type="threshold",
                message=f"BUDGET EXCEEDED: {period} spending ${spent:.2f} exceeds ${limit:.2f} limit. Gateway paused.",
                channels=["banner", "telegram"],
            )
            _pause_gateway()
            return


def _pause_gateway():
    """Attempt to pause the OpenClaw gateway."""
    # Try gateway stop command
    try:
        subprocess.run(["openclaw", "gateway", "stop"], timeout=10, capture_output=True)
        return
    except (FileNotFoundError, subprocess.TimeoutExpired, subprocess.SubprocessError):
        pass
    # Fallback: SIGTERM to gateway process (Unix only)
    # Note: SIGSTOP (19) freezes process indefinitely with TCP held open.
    if sys.platform != 'win32':
        try:
            result = subprocess.run(
                ["pgrep", "-f", "openclaw-gatewa"],
                capture_output=True,
                text=True,
                timeout=3,
            )
            for pid in result.stdout.strip().split("\n"):
                pid = pid.strip()
                if pid:
                    os.kill(int(pid), 15)  # SIGTERM
                    return
        except (FileNotFoundError, ProcessLookupError, PermissionError, ValueError):
            pass  # process gone or can't access


def _resume_gateway():
    """Resume the OpenClaw gateway after budget pause."""
    global _budget_paused, _budget_paused_at, _budget_paused_reason
    # Try gateway start command
    try:
        subprocess.run(
            ["openclaw", "gateway", "start"], timeout=10, capture_output=True
        )
    except (FileNotFoundError, subprocess.TimeoutExpired, subprocess.SubprocessError):
        pass
    # Also try SIGCONT (Unix only)
    if sys.platform != "win32":
        try:
            result = subprocess.run(
                ["pgrep", "-f", "openclaw-gatewa"],
                capture_output=True,
                text=True,
                timeout=3,
            )
            for pid in result.stdout.strip().split("\n"):
                pid = pid.strip()
                if pid:
                    os.kill(int(pid), 18)  # SIGCONT
        except Exception:
            pass
    _budget_paused = False
    _budget_paused_at = 0
    _budget_paused_reason = ""


def _fire_alert(rule_id, alert_type, message, channels=None):
    """Fire an alert with cooldown check."""
    global _budget_alert_cooldowns
    now = time.time()

    # Check cooldown (default 30 min for budget alerts)
    cooldown_sec = 1800
    last_fired = _budget_alert_cooldowns.get(rule_id, 0)
    if now - last_fired < cooldown_sec:
        return

    _budget_alert_cooldowns[rule_id] = now

    # Save to alert history
    if channels is None:
        channels = ["banner"]
    try:
        with _fleet_db_lock:
            db = _fleet_db()
            for ch in channels:
                db.execute(
                    "INSERT INTO alert_history (rule_id, type, message, channel, fired_at) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (rule_id, alert_type, message, ch, now),
                )
            db.commit()
            db.close()
    except Exception as e:
        print(f"Warning: Failed to save alert history: {e}")

    # Send to channels
    for ch in channels:
        if ch == "telegram":
            _send_telegram_alert(message)
        elif ch == "webhook":
            pass  # webhook sending handled by custom alert rules


def _send_telegram_alert(message):
    """Send alert via direct Telegram API (preferred) or gateway fallback."""
    # Try direct Telegram API first (using budget config)
    try:
        cfg = _get_budget_config()
        token = str(cfg.get("telegram_bot_token", "")).strip()
        chat_id = str(cfg.get("telegram_chat_id", "")).strip()
        if token and chat_id:
            import urllib.request

            url = f"https://api.telegram.org/bot{token}/sendMessage"
            payload = json.dumps(
                {
                    "chat_id": chat_id,
                    "text": f"[ClawMetry Alert] {message}",
                    "parse_mode": "Markdown",
                }
            ).encode()
            req = urllib.request.Request(
                url,
                data=payload,
                headers={"Content-Type": "application/json"},
            )
            urllib.request.urlopen(req, timeout=10)
            return
    except Exception as e:
        print(f"Warning: Direct Telegram alert failed: {e}")
    # Fallback: send through gateway
    try:
        _gw_invoke(
            "message",
            {
                "action": "send",
                "message": f"[ClawMetry Alert] {message}",
            },
        )
    except Exception:
        pass


def _send_webhook_alert(url, alert_data, payload_type="generic"):
    """Send alert to a webhook URL (generic JSON, Slack, or Discord)."""
    try:
        import urllib.request as _ur

        if payload_type == "discord":
            content = (
                alert_data.get("message")
                or f"[{alert_data.get('type', 'alert')}] cost=${alert_data.get('cost_usd', 0)} threshold=${alert_data.get('threshold', 0)}"
            )
            body = {"content": content}
        elif payload_type == "slack":
            text = (
                alert_data.get("message")
                or f"[{alert_data.get('type', 'alert')}] cost=${alert_data.get('cost_usd', 0)} threshold=${alert_data.get('threshold', 0)}"
            )
            body = {"text": text}
        else:
            body = alert_data
        payload = json.dumps(body).encode()
        req = _ur.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        _ur.urlopen(req, timeout=10)
    except Exception:
        pass


def _get_alert_rules():
    """Get all alert rules."""
    try:
        with _fleet_db_lock:
            db = _fleet_db()
            rows = db.execute(
                "SELECT * FROM alert_rules ORDER BY created_at DESC"
            ).fetchall()
            db.close()
        return [dict(r) for r in rows]
    except Exception:
        return []


def _get_alert_history(limit=50):
    """Get recent alert history."""
    try:
        with _fleet_db_lock:
            db = _fleet_db()
            rows = db.execute(
                "SELECT * FROM alert_history ORDER BY fired_at DESC LIMIT ?", (limit,)
            ).fetchall()
            db.close()
        return [dict(r) for r in rows]
    except Exception:
        return []


def _get_active_alerts():
    """Get unacknowledged alerts from last 24h."""
    cutoff = time.time() - 86400
    try:
        with _fleet_db_lock:
            db = _fleet_db()
            rows = db.execute(
                "SELECT * FROM alert_history WHERE acknowledged = 0 AND fired_at > ? "
                "ORDER BY fired_at DESC LIMIT 20",
                (cutoff,),
            ).fetchall()
            db.close()
        return [dict(r) for r in rows]
    except Exception:
        return []


_velocity_cache = {"ts": 0, "result": None, "mtimes": {}}

def _compute_velocity_status():
    """Compute real-time token velocity across all active sessions.

    Returns a dict with:
      - active: bool (True if any threshold exceeded)
      - tokensIn2Min: total tokens in last 2 minutes across all sessions
      - costPerMin: estimated USD/min cost rate
      - maxConsecutiveTools: highest consecutive-tool-call chain found
      - triggeringSession: session ID with highest burn rate (if any)
      - reasons: list of human-readable trigger reasons
    """
    now = time.time()
    # Cache for 30 seconds to avoid re-reading files
    if _velocity_cache["result"] and (now - _velocity_cache["ts"]) < 30:
        return _velocity_cache["result"]
    window_2min = now - 120

    sessions_dir = SESSIONS_DIR or os.path.expanduser(
        "~/.openclaw/agents/main/sessions"
    )
    total_tokens_2min = 0.0
    max_consecutive_tools = 0
    triggering_session = None
    highest_tpm = 0.0

    try:
        if os.path.isdir(sessions_dir):
            candidates = sorted(
                [
                    f
                    for f in os.listdir(sessions_dir)
                    if f.endswith(".jsonl") and "deleted" not in f
                ],
                key=lambda f: os.path.getmtime(os.path.join(sessions_dir, f)),
                reverse=True,
            )[:20]  # check 20 most recent sessions
            for fname in candidates:
                fpath = os.path.join(sessions_dir, fname)
                try:
                    mtime = os.path.getmtime(fpath)
                    if now - mtime > 300:  # skip sessions inactive > 5 min
                        continue
                    tokens_2min = 0.0
                    consecutive_tools = 0
                    max_consecutive_in_session = 0
                    with open(fpath, "r", errors="replace") as f:
                        lines = list(deque(f, maxlen=2000))
                    for line in lines:
                        try:
                            obj = json.loads(line.strip())
                        except Exception:
                            continue
                        ts = _json_ts_to_epoch(
                            obj.get("timestamp")
                            or obj.get("time")
                            or obj.get("created_at")
                        )
                        if not ts:
                            continue
                        # Count consecutive tool calls (any tool_use role)
                        msg = (
                            obj.get("message", {})
                            if isinstance(obj.get("message"), dict)
                            else {}
                        )
                        role = msg.get("role", "") or obj.get("role", "")
                        content = msg.get("content", [])
                        is_tool_call = False
                        if isinstance(content, list):
                            for blk in content:
                                if (
                                    isinstance(blk, dict)
                                    and blk.get("type") == "tool_use"
                                ):
                                    is_tool_call = True
                                    break
                        if role == "user" and not is_tool_call:
                            consecutive_tools = 0  # human turn resets counter
                        elif is_tool_call or role == "assistant":
                            consecutive_tools += 1
                            max_consecutive_in_session = max(
                                max_consecutive_in_session, consecutive_tools
                            )
                        # Sum tokens in last 2 minutes
                        if ts >= window_2min:
                            usage = (
                                msg.get("usage", {})
                                if isinstance(msg.get("usage"), dict)
                                else {}
                            )
                            tok = float(
                                usage.get("total_tokens")
                                or usage.get("totalTokens")
                                or (
                                    usage.get("input_tokens", 0)
                                    + usage.get("output_tokens", 0)
                                )
                                or 0
                            )
                            tokens_2min += tok
                    total_tokens_2min += tokens_2min
                    if max_consecutive_in_session > max_consecutive_tools:
                        max_consecutive_tools = max_consecutive_in_session
                    # Track highest burn session
                    burn = _session_burn_stats(fname.replace(".jsonl", ""))
                    tpm = burn.get("tokensPerMin", 0)
                    if tpm > highest_tpm:
                        highest_tpm = tpm
                        triggering_session = fname.replace(".jsonl", "")
                except Exception:
                    continue
    except Exception:
        pass

    usd_per_token = _estimate_usd_per_token()
    cost_per_min = highest_tpm * usd_per_token

    reasons = []
    active = False

    if total_tokens_2min >= _VELOCITY_TOKENS_PER_2MIN:
        active = True
        reasons.append(
            f"Token velocity: {int(total_tokens_2min):,} tokens in 2 min "
            f"(threshold: {_VELOCITY_TOKENS_PER_2MIN:,})"
        )
    if cost_per_min >= _VELOCITY_COST_PER_MIN:
        active = True
        reasons.append(
            f"Cost rate: ${cost_per_min:.3f}/min "
            f"(threshold: ${_VELOCITY_COST_PER_MIN:.2f}/min)"
        )
    if max_consecutive_tools >= _VELOCITY_CONSECUTIVE_TOOLS:
        active = True
        reasons.append(
            f"Consecutive tool calls: {max_consecutive_tools} "
            f"(threshold: {_VELOCITY_CONSECUTIVE_TOOLS})"
        )

    return {
        "active": active,
        "tokensIn2Min": round(total_tokens_2min, 1),
        "costPerMin": round(cost_per_min, 5),
        "maxConsecutiveTools": max_consecutive_tools,
        "triggeringSession": triggering_session,
        "reasons": reasons,
        "thresholds": {
            "tokensIn2Min": _VELOCITY_TOKENS_PER_2MIN,
            "costPerMin": _VELOCITY_COST_PER_MIN,
            "consecutiveTools": _VELOCITY_CONSECUTIVE_TOOLS,
        },
    }


def _budget_monitor_loop():
    """Background thread: check for anomalies, agent-down, and custom alert rules."""
    global _budget_alert_cooldowns, _security_posture_hash
    while True:
        time.sleep(60)
        try:
            now = time.time()

            # Agent-down check
            if (
                _otel_last_received > 0
                and (now - _otel_last_received) > _AGENT_DOWN_SECONDS
            ):
                _fire_alert(
                    rule_id="agent_down",
                    alert_type="agent_down",
                    message=f"Agent appears down: no OTLP data for {int((now - _otel_last_received) / 60)} minutes",
                    channels=["banner", "telegram"],
                )

            # Anomaly check: today's cost > 2x 7-day average
            status = _get_budget_status()
            daily_spent = status["daily_spent"]
            if daily_spent > 0:
                week_avg = (
                    status["weekly_spent"] / 7 if status["weekly_spent"] > 0 else 0
                )
                if week_avg > 0 and daily_spent > week_avg * 2:
                    ratio = daily_spent / week_avg
                    _fire_alert(
                        rule_id="anomaly_daily",
                        alert_type="anomaly",
                        message=f"Spending anomaly: today ${daily_spent:.2f} is {ratio:.1f}x the 7-day average (${week_avg:.2f}/day)",
                        channels=["banner", "telegram"],
                    )
                    _dispatch_configured_webhooks(
                        "cost_spike",
                        {
                            "type": "cost_spike",
                            "agent": "main",
                            "cost_usd": round(daily_spent, 4),
                            "threshold": round(week_avg * 2, 4),
                            "timestamp": now,
                            "message": f"Cost spike detected: {ratio:.1f}x daily average",
                        },
                    )

            # Token velocity alert (GH#313): detect runaway agent loops
            try:
                vel = _compute_velocity_status()
                if vel["active"]:
                    reasons_str = "; ".join(vel["reasons"])
                    sid_hint = (
                        f" (session: {vel['triggeringSession'][:12]}...)"
                        if vel.get("triggeringSession")
                        else ""
                    )
                    msg = f"\u26a1 Runaway loop detected{sid_hint}: {reasons_str}"
                    _fire_alert(
                        rule_id="token_velocity",
                        alert_type="token_velocity",
                        message=msg,
                        channels=["banner", "telegram"],
                    )
            except Exception as _vel_err:
                print(f"Warning: velocity check failed: {_vel_err}")

            # Agent error-rate check from webhook channel metrics (last 60 minutes)
            window_start = now - 3600
            total_wh = 0
            error_wh = 0
            with _metrics_lock:
                for e in metrics_store.get("webhooks", []):
                    ts = e.get("timestamp", 0)
                    if ts < window_start:
                        continue
                    total_wh += 1
                    et = str(e.get("type", "")).lower()
                    if et.endswith(".error") or "error" in et:
                        error_wh += 1
            if total_wh >= 10:
                error_rate = (error_wh / total_wh) * 100.0
                if error_rate >= 20.0:
                    rule_id = "agent_error_rate_high"
                    last_fired = _budget_alert_cooldowns.get(rule_id, 0)
                    if now - last_fired >= 1800:
                        _budget_alert_cooldowns[rule_id] = now
                        msg = f"Agent error rate high: {error_rate:.1f}% ({error_wh}/{total_wh}) in the last hour"
                        _fire_alert(
                            rule_id=rule_id,
                            alert_type="agent_error_rate",
                            message=msg,
                            channels=["banner", "telegram"],
                        )
                        _dispatch_configured_webhooks(
                            "agent_error_rate",
                            {
                                "type": "agent_error_rate",
                                "agent": "main",
                                "cost_usd": round(status.get("daily_spent", 0), 4),
                                "threshold": 20.0,
                                "timestamp": now,
                                "message": msg,
                            },
                        )

            # Security posture change check
            posture = _detect_security_metadata() or {}
            posture_hash = json.dumps(posture, sort_keys=True)
            if not _security_posture_hash:
                _security_posture_hash = posture_hash
            elif posture_hash != _security_posture_hash:
                _security_posture_hash = posture_hash
                msg = "Security posture changed (sandbox/auth/network settings updated)"
                _fire_alert(
                    rule_id="security_posture_change",
                    alert_type="security",
                    message=msg,
                    channels=["banner", "telegram"],
                )
                _dispatch_configured_webhooks(
                    "security_posture_change",
                    {
                        "type": "security_posture_change",
                        "agent": "main",
                        "cost_usd": round(status.get("daily_spent", 0), 4),
                        "threshold": 0,
                        "timestamp": now,
                        "message": msg,
                    },
                )

            # Custom alert rules
            rules = _get_alert_rules()
            for rule in rules:
                if not rule.get("enabled"):
                    continue
                rule_id = rule["id"]
                rtype = rule["type"]
                threshold = rule["threshold"]
                channels = json.loads(rule.get("channels", '["banner"]'))
                cooldown = rule.get("cooldown_min", 30) * 60

                last_fired = _budget_alert_cooldowns.get(rule_id, 0)
                if now - last_fired < cooldown:
                    continue

                fired = False
                msg = ""

                if rtype == "threshold":
                    if status["daily_spent"] >= threshold:
                        msg = f"Daily spending ${status['daily_spent']:.2f} exceeded threshold ${threshold:.2f}"
                        fired = True
                elif rtype == "spike":
                    # Spike: cost in last hour > threshold x average hourly rate
                    hour_ago = now - 3600
                    hour_cost = 0
                    with _metrics_lock:
                        for e in metrics_store["cost"]:
                            if e.get("timestamp", 0) >= hour_ago:
                                hour_cost += e.get("usd", 0)
                    avg_hourly = status["daily_spent"] / max(
                        1,
                        (
                            now
                            - datetime.now()
                            .replace(hour=0, minute=0, second=0, microsecond=0)
                            .timestamp()
                        )
                        / 3600,
                    )
                    if avg_hourly > 0 and hour_cost > avg_hourly * threshold:
                        msg = f"Spending spike: ${hour_cost:.2f} in last hour ({(hour_cost / avg_hourly):.1f}x average)"
                        fired = True

                if fired:
                    _budget_alert_cooldowns[rule_id] = now
                    try:
                        with _fleet_db_lock:
                            db = _fleet_db()
                            for ch in channels:
                                db.execute(
                                    "INSERT INTO alert_history (rule_id, type, message, channel, fired_at) "
                                    "VALUES (?, ?, ?, ?, ?)",
                                    (rule_id, rtype, msg, ch, now),
                                )
                            db.commit()
                            db.close()
                    except Exception:
                        pass
                    for ch in channels:
                        if ch == "telegram":
                            _send_telegram_alert(msg)
                        elif ch == "webhook":
                            webhook_url = rule.get("webhook_url", "")
                            if webhook_url:
                                _send_webhook_alert(
                                    webhook_url,
                                    {"type": rtype, "message": msg, "timestamp": now},
                                )

        except Exception as e:
            print(f"Warning: Budget monitor error: {e}")


def _start_budget_monitor_thread():
    """Start the background budget monitor thread."""
    t = threading.Thread(target=_budget_monitor_loop, daemon=True)
    t.start()


# ── OTLP Protobuf Helpers ──────────────────────────────────────────────


def _otel_attr_value(val):
    """Convert an OTel AnyValue to a Python value."""
    if val.HasField("string_value"):
        return val.string_value
    if val.HasField("int_value"):
        return val.int_value
    if val.HasField("double_value"):
        return val.double_value
    if val.HasField("bool_value"):
        return val.bool_value
    return str(val)


def _get_data_points(metric):
    """Extract data points from a metric regardless of type."""
    if metric.HasField("sum"):
        return metric.sum.data_points
    elif metric.HasField("gauge"):
        return metric.gauge.data_points
    elif metric.HasField("histogram"):
        return metric.histogram.data_points
    elif metric.HasField("summary"):
        return metric.summary.data_points
    return []


def _get_dp_value(dp):
    """Extract the numeric value from a data point."""
    if hasattr(dp, "as_double") and dp.as_double:
        return dp.as_double
    if hasattr(dp, "as_int") and dp.as_int:
        return dp.as_int
    if hasattr(dp, "sum") and dp.sum:
        return dp.sum
    if hasattr(dp, "count") and dp.count:
        return dp.count
    return 0


def _get_dp_attrs(dp):
    """Extract attributes from a data point."""
    attrs = {}
    for attr in dp.attributes:
        attrs[attr.key] = _otel_attr_value(attr.value)
    return attrs


def _process_otlp_metrics(pb_data):
    """Decode OTLP metrics protobuf and store relevant data."""
    req = metrics_service_pb2.ExportMetricsServiceRequest()
    req.ParseFromString(pb_data)

    for resource_metrics in req.resource_metrics:
        resource_attrs = {}
        if resource_metrics.resource:
            for attr in resource_metrics.resource.attributes:
                resource_attrs[attr.key] = _otel_attr_value(attr.value)

        for scope_metrics in resource_metrics.scope_metrics:
            for metric in scope_metrics.metrics:
                name = metric.name
                ts = time.time()

                if name == "openclaw.tokens":
                    for dp in _get_data_points(metric):
                        attrs = _get_dp_attrs(dp)
                        _add_metric(
                            "tokens",
                            {
                                "timestamp": ts,
                                "input": attrs.get("input_tokens", 0),
                                "output": attrs.get("output_tokens", 0),
                                "total": _get_dp_value(dp),
                                "model": attrs.get(
                                    "model", resource_attrs.get("model", "")
                                ),
                                "channel": attrs.get(
                                    "channel", resource_attrs.get("channel", "")
                                ),
                                "provider": attrs.get(
                                    "provider", resource_attrs.get("provider", "")
                                ),
                            },
                        )
                elif name == "openclaw.cost.usd":
                    for dp in _get_data_points(metric):
                        attrs = _get_dp_attrs(dp)
                        _add_metric(
                            "cost",
                            {
                                "timestamp": ts,
                                "usd": _get_dp_value(dp),
                                "model": attrs.get(
                                    "model", resource_attrs.get("model", "")
                                ),
                                "channel": attrs.get(
                                    "channel", resource_attrs.get("channel", "")
                                ),
                                "provider": attrs.get(
                                    "provider", resource_attrs.get("provider", "")
                                ),
                            },
                        )
                elif name == "openclaw.run.duration_ms":
                    for dp in _get_data_points(metric):
                        attrs = _get_dp_attrs(dp)
                        _add_metric(
                            "runs",
                            {
                                "timestamp": ts,
                                "duration_ms": _get_dp_value(dp),
                                "model": attrs.get(
                                    "model", resource_attrs.get("model", "")
                                ),
                                "channel": attrs.get(
                                    "channel", resource_attrs.get("channel", "")
                                ),
                            },
                        )
                elif name == "openclaw.context.tokens":
                    for dp in _get_data_points(metric):
                        attrs = _get_dp_attrs(dp)
                        _add_metric(
                            "tokens",
                            {
                                "timestamp": ts,
                                "input": _get_dp_value(dp),
                                "output": 0,
                                "total": _get_dp_value(dp),
                                "model": attrs.get(
                                    "model", resource_attrs.get("model", "")
                                ),
                                "channel": attrs.get(
                                    "channel", resource_attrs.get("channel", "")
                                ),
                                "provider": attrs.get(
                                    "provider", resource_attrs.get("provider", "")
                                ),
                            },
                        )
                elif name in (
                    "openclaw.message.processed",
                    "openclaw.message.queued",
                    "openclaw.message.duration_ms",
                ):
                    for dp in _get_data_points(metric):
                        attrs = _get_dp_attrs(dp)
                        outcome = (
                            "processed"
                            if "processed" in name
                            else ("queued" if "queued" in name else "duration")
                        )
                        _add_metric(
                            "messages",
                            {
                                "timestamp": ts,
                                "channel": attrs.get(
                                    "channel", resource_attrs.get("channel", "")
                                ),
                                "outcome": outcome,
                                "duration_ms": _get_dp_value(dp)
                                if "duration" in name
                                else 0,
                            },
                        )
                elif name in (
                    "openclaw.webhook.received",
                    "openclaw.webhook.error",
                    "openclaw.webhook.duration_ms",
                ):
                    for dp in _get_data_points(metric):
                        attrs = _get_dp_attrs(dp)
                        wtype = (
                            "received"
                            if "received" in name
                            else ("error" if "error" in name else "duration")
                        )
                        _add_metric(
                            "webhooks",
                            {
                                "timestamp": ts,
                                "channel": attrs.get(
                                    "channel", resource_attrs.get("channel", "")
                                ),
                                "type": wtype,
                            },
                        )


def _process_otlp_traces(pb_data):
    """Decode OTLP traces protobuf and extract relevant span data."""
    req = trace_service_pb2.ExportTraceServiceRequest()
    req.ParseFromString(pb_data)

    for resource_spans in req.resource_spans:
        resource_attrs = {}
        if resource_spans.resource:
            for attr in resource_spans.resource.attributes:
                resource_attrs[attr.key] = _otel_attr_value(attr.value)

        for scope_spans in resource_spans.scope_spans:
            for span in scope_spans.spans:
                attrs = {}
                for attr in span.attributes:
                    attrs[attr.key] = _otel_attr_value(attr.value)

                ts = time.time()
                duration_ns = span.end_time_unix_nano - span.start_time_unix_nano
                duration_ms = duration_ns / 1_000_000

                span_name = span.name.lower()
                if "run" in span_name or "completion" in span_name:
                    _add_metric(
                        "runs",
                        {
                            "timestamp": ts,
                            "duration_ms": duration_ms,
                            "model": attrs.get(
                                "model", resource_attrs.get("model", "")
                            ),
                            "channel": attrs.get(
                                "channel", resource_attrs.get("channel", "")
                            ),
                        },
                    )
                elif "message" in span_name:
                    _add_metric(
                        "messages",
                        {
                            "timestamp": ts,
                            "channel": attrs.get(
                                "channel", resource_attrs.get("channel", "")
                            ),
                            "outcome": "processed",
                            "duration_ms": duration_ms,
                        },
                    )


def _get_otel_usage_data():
    """Aggregate OTLP metrics into usage data for the Usage tab."""
    today = datetime.now()
    today_start = today.replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
    week_start = (
        (today - timedelta(days=today.weekday()))
        .replace(hour=0, minute=0, second=0, microsecond=0)
        .timestamp()
    )
    month_start = today.replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    ).timestamp()

    daily_tokens = {}
    daily_cost = {}
    model_usage = {}

    with _metrics_lock:
        for entry in metrics_store["tokens"]:
            ts = entry.get("timestamp", 0)
            day = datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
            total = entry.get("total", 0)
            daily_tokens[day] = daily_tokens.get(day, 0) + total
            model = entry.get("model", "unknown") or "unknown"
            model_usage[model] = model_usage.get(model, 0) + total

        for entry in metrics_store["cost"]:
            ts = entry.get("timestamp", 0)
            day = datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
            daily_cost[day] = daily_cost.get(day, 0) + entry.get("usd", 0)

    days = []
    for i in range(13, -1, -1):
        d = today - timedelta(days=i)
        ds = d.strftime("%Y-%m-%d")
        days.append(
            {
                "date": ds,
                "tokens": daily_tokens.get(ds, 0),
                "cost": daily_cost.get(ds, 0),
            }
        )

    today_str = today.strftime("%Y-%m-%d")
    today_tok = daily_tokens.get(today_str, 0)
    week_tok = sum(v for k, v in daily_tokens.items() if _safe_date_ts(k) >= week_start)
    month_tok = sum(
        v for k, v in daily_tokens.items() if _safe_date_ts(k) >= month_start
    )
    today_cost_val = daily_cost.get(today_str, 0)
    week_cost_val = sum(
        v for k, v in daily_cost.items() if _safe_date_ts(k) >= week_start
    )
    month_cost_val = sum(
        v for k, v in daily_cost.items() if _safe_date_ts(k) >= month_start
    )

    run_durations = []
    with _metrics_lock:
        for entry in metrics_store["runs"]:
            run_durations.append(entry.get("duration_ms", 0))
    avg_run_ms = sum(run_durations) / len(run_durations) if run_durations else 0

    msg_count = len(metrics_store["messages"])

    # Enhanced cost tracking for OTLP data
    trend_data = _analyze_usage_trends(daily_tokens)
    model_billing, billing_summary = _build_model_billing(model_usage)
    warnings = _generate_cost_warnings(
        today_cost_val,
        week_cost_val,
        month_cost_val,
        trend_data,
        month_tok,
        billing_summary,
    )

    return {
        "source": "otlp",
        "days": days,
        "today": today_tok,
        "week": week_tok,
        "month": month_tok,
        "todayCost": round(today_cost_val, 4),
        "weekCost": round(week_cost_val, 4),
        "monthCost": round(month_cost_val, 4),
        "avgRunMs": round(avg_run_ms, 1),
        "messageCount": msg_count,
        "modelBreakdown": [
            {"model": k, "tokens": v}
            for k, v in sorted(model_usage.items(), key=lambda x: -x[1])
        ],
        "modelBilling": model_billing,
        "billingSummary": billing_summary,
        "trend": trend_data,
        "warnings": warnings,
    }


def _safe_date_ts(date_str):
    """Parse a YYYY-MM-DD date string to a timestamp, returning 0 on failure."""
    if not date_str or not isinstance(date_str, str):
        return 0
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").timestamp()
    except ValueError:
        # Invalid date format - expected but handled gracefully
        return 0
    except Exception as e:
        print(f"[warn]  Warning: Unexpected error parsing date '{date_str}': {e}")
        return 0


def validate_configuration():
    """Validate the detected configuration and provide helpful feedback for new users."""
    warnings = []
    tips = []

    # Check if workspace looks like a real OpenClaw setup
    workspace_files = ["SOUL.md", "AGENTS.md", "MEMORY.md", "memory"]
    found_files = []
    for f in workspace_files:
        path = os.path.join(WORKSPACE, f)
        if os.path.exists(path):
            found_files.append(f)

    if not found_files:
        warnings.append(f"[warn]  No OpenClaw workspace files found in {WORKSPACE}")
        tips.append(
            "[tip] Create SOUL.md, AGENTS.md, or MEMORY.md to set up your agent workspace"
        )

    # Check if log directory exists and has recent logs
    if not os.path.exists(LOG_DIR):
        warnings.append(f"[warn]  Log directory doesn't exist: {LOG_DIR}")
        tips.append("[tip] Make sure OpenClaw/Moltbot is running to generate logs")
    else:
        # Check for recent log files
        log_pattern = os.path.join(LOG_DIR, "*claw*.log")
        recent_logs = [
            f
            for f in glob.glob(log_pattern)
            if os.path.getmtime(f) > time.time() - 86400
        ]  # Last 24h
        if not recent_logs:
            warnings.append(f"[warn]  No recent log files found in {LOG_DIR}")
            tips.append("[tip] Start your OpenClaw agent to see real-time data")

    # Check if sessions directory exists
    if not SESSIONS_DIR or not os.path.exists(SESSIONS_DIR):
        warnings.append(f"[warn]  Sessions directory not found: {SESSIONS_DIR}")
        tips.append("[tip] Sessions will appear when your agent starts conversations")

    # Check if OpenClaw binary is available
    try:
        subprocess.run(["openclaw", "--version"], capture_output=True, timeout=10)
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
        warnings.append("[warn]  OpenClaw binary not found in PATH")
        tips.append("[tip] Install OpenClaw: https://github.com/openclaw/openclaw")

    return warnings, tips


def _auto_detect_data_dir():
    """Auto-detect OpenClaw data directory, including Docker volume mounts."""
    # Standard locations
    candidates = [
        os.path.expanduser("~/.openclaw"),
        os.path.expanduser("~/.clawdbot"),
    ]
    # Docker volume mounts (Hostinger pattern: /docker/*/data/.openclaw)
    try:
        import glob as _glob

        for pattern in [
            "/docker/*/data/.openclaw",
            "/docker/*/.openclaw",
            "/var/lib/docker/volumes/*/_data/.openclaw",
        ]:
            candidates.extend(_glob.glob(pattern))
    except Exception:
        pass
    # Check Docker inspect for mount points
    try:
        import subprocess as _sp

        container_ids = (
            _sp.check_output(
                ["docker", "ps", "-q", "--filter", "ancestor=*openclaw*"],
                timeout=3,
                stderr=_sp.DEVNULL,
            )
            .decode()
            .strip()
            .split()
        )
        if not container_ids:
            # Try all containers
            container_ids = (
                _sp.check_output(["docker", "ps", "-q"], timeout=3, stderr=_sp.DEVNULL)
                .decode()
                .strip()
                .split()
            )
        for cid in container_ids[:3]:
            try:
                mounts = (
                    _sp.check_output(
                        [
                            "docker",
                            "inspect",
                            cid,
                            "--format",
                            "{{range .Mounts}}{{.Source}}:{{.Destination}} {{end}}",
                        ],
                        timeout=3,
                        stderr=_sp.DEVNULL,
                    )
                    .decode()
                    .strip()
                    .split()
                )
                for mount in mounts:
                    parts = mount.split(":")
                    if len(parts) >= 1:
                        src = parts[0]
                        oc_path = os.path.join(src, ".openclaw")
                        if os.path.isdir(oc_path) and oc_path not in candidates:
                            candidates.insert(0, oc_path)
                        # Also check if the mount itself is the .openclaw dir
                        if src.endswith(".openclaw") and os.path.isdir(src):
                            candidates.insert(0, src)
            except Exception:
                pass
    except Exception:
        pass
    for c in candidates:
        if (
            c
            and os.path.isdir(c)
            and (
                os.path.isdir(os.path.join(c, "agents"))
                or os.path.isdir(os.path.join(c, "workspace"))
                or os.path.exists(os.path.join(c, "cron", "jobs.json"))
            )
        ):
            return c
    return None


def detect_config(args=None):
    """Auto-detect OpenClaw/Moltbot paths, with CLI and env overrides."""
    global WORKSPACE, MEMORY_DIR, LOG_DIR, SESSIONS_DIR, USER_NAME

    # 0a. --openclaw-dir: set OpenClaw config directory (Issue #322 - Docker config bleed)
    if args and getattr(args, "openclaw_dir", None):
        os.environ["CLAWMETRY_OPENCLAW_DIR"] = os.path.expanduser(args.openclaw_dir)

    # 0. --data-dir: set defaults from OpenClaw data directory (e.g. /path/.openclaw)
    data_dir = None
    if args and getattr(args, "data_dir", None):
        data_dir = os.path.expanduser(args.data_dir)
    elif os.environ.get("OPENCLAW_DATA_DIR"):
        data_dir = os.path.expanduser(os.environ["OPENCLAW_DATA_DIR"])
    else:
        # Auto-detect: check common locations including Docker volumes
        data_dir = _auto_detect_data_dir()

    if data_dir and os.path.isdir(data_dir):
        # Auto-set workspace, sessions, crons from data dir
        ws = os.path.join(data_dir, "workspace")
        if os.path.isdir(ws) and not (args and args.workspace):
            if not args:
                import argparse

                args = argparse.Namespace()
            args.workspace = ws
        sess = os.path.join(data_dir, "agents", "main", "sessions")
        if os.path.isdir(sess) and not (args and getattr(args, "sessions_dir", None)):
            args.sessions_dir = sess

    # 1. Workspace - where agent files live (SOUL.md, MEMORY.md, memory/, etc.)
    if args and args.workspace:
        WORKSPACE = os.path.expanduser(args.workspace)
    elif os.environ.get("OPENCLAW_HOME"):
        WORKSPACE = os.path.expanduser(os.environ["OPENCLAW_HOME"])
    elif os.environ.get("OPENCLAW_WORKSPACE"):
        WORKSPACE = os.path.expanduser(os.environ["OPENCLAW_WORKSPACE"])
    else:
        # Auto-detect: check common locations
        candidates = [
            _detect_workspace_from_config(),
            os.path.expanduser("~/.openclaw/workspace"),
            os.path.expanduser("~/.clawdbot/workspace"),
            os.path.expanduser("~/clawd"),
            os.path.expanduser("~/openclaw"),
            os.getcwd(),
        ]
        for c in candidates:
            if (
                c
                and os.path.isdir(c)
                and (
                    os.path.exists(os.path.join(c, "SOUL.md"))
                    or os.path.exists(os.path.join(c, "AGENTS.md"))
                    or os.path.exists(os.path.join(c, "MEMORY.md"))
                    or os.path.isdir(os.path.join(c, "memory"))
                )
            ):
                WORKSPACE = c
                break
        if not WORKSPACE:
            WORKSPACE = os.getcwd()

    MEMORY_DIR = os.path.join(WORKSPACE, "memory")

    # 2. Log directory
    if args and args.log_dir:
        LOG_DIR = os.path.expanduser(args.log_dir)
    elif os.environ.get("OPENCLAW_LOG_DIR"):
        LOG_DIR = os.path.expanduser(os.environ["OPENCLAW_LOG_DIR"])
    else:
        candidates = _get_log_dirs() + [os.path.expanduser("~/.clawdbot/logs")]
        LOG_DIR = next((d for d in candidates if os.path.isdir(d)), _get_log_dirs()[0])

    # 3. Sessions directory (transcript .jsonl files)
    if args and getattr(args, "sessions_dir", None):
        SESSIONS_DIR = os.path.expanduser(args.sessions_dir)
    elif os.environ.get("OPENCLAW_SESSIONS_DIR"):
        SESSIONS_DIR = os.path.expanduser(os.environ["OPENCLAW_SESSIONS_DIR"])
    else:
        candidates = [
            os.path.expanduser("~/.openclaw/agents/main/sessions"),
            os.path.expanduser("~/.clawdbot/agents/main/sessions"),
            os.path.join(WORKSPACE, "sessions") if WORKSPACE else None,
            os.path.expanduser("~/.openclaw/sessions"),
            os.path.expanduser("~/.clawdbot/sessions"),
        ]
        # Also scan agents dirs
        for agents_base in [
            os.path.expanduser("~/.openclaw/agents"),
            os.path.expanduser("~/.clawdbot/agents"),
        ]:
            if os.path.isdir(agents_base):
                for agent in os.listdir(agents_base):
                    p = os.path.join(agents_base, agent, "sessions")
                    if p not in candidates:
                        candidates.append(p)
        SESSIONS_DIR = next(
            (d for d in candidates if d and os.path.isdir(d)),
            candidates[0] if candidates else None,
        )

    # 4. User name (shown in Flow visualization)
    if args and args.name:
        USER_NAME = args.name
    elif os.environ.get("OPENCLAW_USER"):
        USER_NAME = os.environ["OPENCLAW_USER"]
    else:
        USER_NAME = "You"

    # Phase 3: initialize DataProvider with detected paths
    try:
        _init_data_provider()
    except Exception:
        pass


def _detect_workspace_from_config():
    """Try to read workspace from Moltbot/OpenClaw agent config."""
    config_paths = [
        os.path.expanduser("~/.clawdbot/agents/main/config.json"),
        os.path.expanduser("~/.clawdbot/config.json"),
    ]
    for cp in config_paths:
        try:
            with open(cp) as f:
                data = json.load(f)
                ws = data.get("workspace") or data.get("workspaceDir")
                if ws:
                    return os.path.expanduser(ws)
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            pass
    return None


def _detect_gateway_port():
    """Detect the OpenClaw gateway port from config files or environment."""
    # Check environment variable first
    env_port = os.environ.get("OPENCLAW_GATEWAY_PORT", "").strip()
    if env_port:
        try:
            return int(env_port)
        except ValueError:
            pass
    # Try reading from gateway config
    # Try JSON configs first (openclaw.json / moltbot.json / clawdbot.json)
    _oc_dir = _get_openclaw_dir()
    json_paths = [
        os.path.join(_oc_dir, "openclaw.json"),
        os.path.join(_oc_dir, "moltbot.json"),
        os.path.join(_oc_dir, "clawdbot.json"),
        os.path.expanduser("~/.clawdbot/clawdbot.json"),
    ]
    for jp in json_paths:
        try:
            import json as _json

            with open(jp) as f:
                cfg = _json.load(f)
            gw = cfg.get("gateway", {})
            if isinstance(gw, dict) and "port" in gw:
                return int(gw["port"])
        except (FileNotFoundError, ValueError, KeyError, TypeError):
            pass
    # Try YAML configs
    yaml_paths = [
        os.path.expanduser("~/.openclaw/gateway.yaml"),
        os.path.expanduser("~/.openclaw/gateway.yml"),
        os.path.expanduser("~/.clawdbot/gateway.yaml"),
        os.path.expanduser("~/.clawdbot/gateway.yml"),
    ]
    for cp in yaml_paths:
        try:
            with open(cp) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("port:"):
                        port_val = line.split(":", 1)[1].strip()
                        return int(port_val)
        except (FileNotFoundError, ValueError, IndexError):
            pass
    return 18789  # Default OpenClaw gateway port


def _detect_gateway_token():
    """Detect the OpenClaw gateway auth token from env, config files, or running process."""
    # 1. Environment variable (most reliable - matches running gateway)
    env_token = os.environ.get("OPENCLAW_GATEWAY_TOKEN", "").strip()
    if env_token:
        return env_token
    # 2. Try reading from running gateway process env (Linux only)
    try:
        import subprocess as _sp

        result = _sp.run(
            ["pgrep", "-f", "openclaw-gatewa"],
            capture_output=True,
            text=True,
            timeout=3,
        )
        for pid in result.stdout.strip().split("\n"):
            pid = pid.strip()
            if pid:
                try:
                    with open(f"/proc/{pid}/environ", "r") as f:
                        env_data = f.read()
                    for entry in env_data.split("\0"):
                        if entry.startswith("OPENCLAW_GATEWAY_TOKEN="):
                            return entry.split("=", 1)[1]
                except (PermissionError, FileNotFoundError):
                    pass
    except Exception:
        pass
    # 3. Config files
    _oc_dir = _get_openclaw_dir()
    json_paths = [
        os.path.join(_oc_dir, "openclaw.json"),
        os.path.join(_oc_dir, "moltbot.json"),
        os.path.join(_oc_dir, "clawdbot.json"),
        os.path.expanduser("~/.clawdbot/clawdbot.json"),
    ]
    for jp in json_paths:
        try:
            import json as _json

            with open(jp) as f:
                cfg = _json.load(f)
            gw = cfg.get("gateway", {})
            auth = gw.get("auth", {})
            if isinstance(auth, dict) and "token" in auth:
                return auth["token"]
        except (FileNotFoundError, ValueError, KeyError, TypeError):
            pass
    return None


def _detect_disk_mounts():
    """Detect mounted filesystems to monitor (root + any large data drives)."""
    mounts = ["/"]
    try:
        with open("/proc/mounts") as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 2:
                    mount_point = parts[1]
                    fs_type = parts[2] if len(parts) > 2 else ""
                    # Include additional data mounts (skip virtual/special filesystems)
                    if (
                        mount_point.startswith("/mnt/")
                        or mount_point.startswith("/data")
                    ) and fs_type not in (
                        "tmpfs",
                        "devtmpfs",
                        "proc",
                        "sysfs",
                        "cgroup",
                        "cgroup2",
                    ):
                        mounts.append(mount_point)
    except (IOError, OSError):
        pass
    return mounts


def get_public_ip():
    """Get the machine's public IP address (useful for cloud/VPS users)."""
    try:
        import urllib.request

        return (
            urllib.request.urlopen("https://api.ipify.org", timeout=2)
            .read()
            .decode()
            .strip()
        )
    except Exception:
        return None


def get_local_ip():
    """Get the machine's LAN IP address."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.2)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except (socket.error, OSError):
        # Network unavailable or socket error - common in offline/restricted environments
        return "127.0.0.1"
    except Exception as e:
        print(f"[warn]  Warning: Unexpected error getting local IP: {e}")
        return "127.0.0.1"


# ── HTML Template ───────────────────────────────────────────────────────

DASHBOARD_HTML = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ClawMetry</title>
<link rel="icon" href="/favicon.ico" type="image/x-icon">
<link rel="icon" href="/static/img/logo.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
  :root {
    /* Light theme (default) */
    --bg-primary: #f5f7fb;
    --bg-secondary: #ffffff;
    --bg-tertiary: #ffffff;
    --bg-hover: #f3f5f8;
    --bg-accent: #0f6fff;
    --border-primary: #e4e8ee;
    --border-secondary: #edf1f5;
    --text-primary: #101828;
    --text-secondary: #344054;
    --text-tertiary: #475467;
    --text-muted: #667085;
    --text-faint: #98a2b3;
    --text-accent: #0f6fff;
    --text-link: #0f6fff;
    --text-success: #15803d;
    --text-warning: #b45309;
    --text-error: #b42318;
    --bg-success: #ecfdf3;
    --bg-warning: #fffaeb;
    --bg-error: #fef3f2;
    --log-bg: #f7f9fc;
    --file-viewer-bg: #ffffff;
    --button-bg: #f3f5f8;
    --button-hover: #e9eef5;
    --card-shadow: 0 1px 2px rgba(16, 24, 40, 0.05), 0 1px 3px rgba(16, 24, 40, 0.1);
    --card-shadow-hover: 0 10px 18px rgba(16, 24, 40, 0.08), 0 2px 6px rgba(16, 24, 40, 0.06);
  }

  [data-theme="dark"] {
    /* Dark theme */
    --bg-primary: #0b0f14;
    --bg-secondary: #121820;
    --bg-tertiary: #151d28;
    --bg-hover: #1b2430;
    --bg-accent: #3b82f6;
    --border-primary: #273243;
    --border-secondary: #1f2937;
    --text-primary: #e6edf5;
    --text-secondary: #c1cad6;
    --text-tertiary: #98a2b3;
    --text-muted: #7c8a9d;
    --text-faint: #667085;
    --text-accent: #60a5fa;
    --text-link: #7dd3fc;
    --text-success: #4ade80;
    --text-warning: #fbbf24;
    --text-error: #f87171;
    --bg-success: #10291c;
    --bg-warning: #2a2314;
    --bg-error: #341717;
    --log-bg: #0f141c;
    --file-viewer-bg: #111722;
    --button-bg: #1d2632;
    --button-hover: #263344;
    --card-shadow: 0 1px 3px rgba(0,0,0,0.4);
    --card-shadow-hover: 0 8px 18px rgba(0,0,0,0.45);
  }

  * { box-sizing: border-box; margin: 0; padding: 0; transition: background-color 0.3s ease, color 0.3s ease, border-color 0.3s ease, box-shadow 0.3s ease; }
  body { font-family: 'Manrope', -apple-system, BlinkMacSystemFont, 'SF Pro Text', 'Segoe UI', Roboto, sans-serif; background: radial-gradient(1200px 600px at 70% -20%, rgba(15,111,255,0.06), transparent 55%), var(--bg-primary); color: var(--text-primary); min-height: 100vh; font-size: 14px; font-weight: 500; line-height: 1.5; -webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale; }

  .nav { background: color-mix(in srgb, var(--bg-secondary) 90%, transparent); border-bottom: 1px solid var(--border-primary); padding: 8px 16px; display: flex; align-items: center; gap: 12px; overflow: visible; box-shadow: 0 1px 2px rgba(16,24,40,0.06); position: sticky; top: 0; z-index: 10; backdrop-filter: blur(8px); }
  .nav h1 { font-size: 18px; font-weight: 700; color: var(--text-primary); white-space: nowrap; letter-spacing: -0.3px; }
  .nav h1 span { color: var(--text-accent); }
  .version-badge { font-size: 11px; color: var(--text-secondary); background: var(--bg-secondary); border: 1px solid var(--border-primary); border-radius: 6px; padding: 2px 8px; white-space: nowrap; cursor: default; transition: all 0.2s; user-select: none; }
  .version-badge.update-available { color: #22c55e; border-color: rgba(34,197,94,0.4); cursor: pointer; }
  .version-badge.update-available:hover { background: rgba(34,197,94,0.1); }
  .version-badge.updating { color: #f59e0b; border-color: rgba(245,158,11,0.4); cursor: wait; }
  .theme-toggle { background: var(--button-bg); border: none; border-radius: 8px; padding: 8px 12px; color: var(--text-tertiary); cursor: pointer; font-size: 16px; margin-left: 12px; transition: all 0.15s; box-shadow: var(--card-shadow); }
  .theme-toggle:hover { background: var(--button-hover); color: var(--text-secondary); }
  .theme-toggle:active { transform: scale(0.98); }
  
  /* === Zoom Controls === */
  .zoom-controls { display: flex; align-items: center; gap: 4px; margin-left: 12px; }
  .zoom-btn { background: var(--button-bg); border: 1px solid var(--border-primary); border-radius: 6px; width: 28px; height: 28px; color: var(--text-tertiary); cursor: pointer; font-size: 16px; font-weight: 700; display: flex; align-items: center; justify-content: center; transition: all 0.15s; }
  .zoom-btn:hover { background: var(--button-hover); color: var(--text-secondary); }
  .zoom-level { font-size: 11px; color: var(--text-muted); font-weight: 600; min-width: 36px; text-align: center; }
  .nav-tabs { display: flex; gap: 4px; margin-left: auto; position: relative; }
  /* Brain tab */
  .brain-event { display:flex; align-items:flex-start; gap:10px; padding:5px 0; border-bottom:1px solid var(--border); font-size:12px; font-family:monospace; flex-wrap:nowrap; cursor:pointer; transition:background 0.15s; }
  .brain-event:hover { background:rgba(255,255,255,0.02); }
  .brain-event.expanded { flex-wrap:wrap; }
  .brain-event.expanded .brain-detail { white-space:pre-wrap; overflow:visible; text-overflow:unset; }
  .brain-meta { display:contents; } /* Desktop: render children directly in brain-event flex row */
  .brain-time { color:var(--text-muted); min-width:70px; }
  .brain-source { min-width:120px; max-width:200px; font-weight:600; word-break:break-all; flex-shrink:0; }
  .brain-type { padding:1px 6px; border-radius:3px; font-size:10px; font-weight:700; min-width:60px; text-align:center; display:inline-block; }
  .badge-spawn { background:rgba(168,85,247,0.2); color:#a855f7; }
  .badge-shell { background:rgba(234,179,8,0.2); color:#eab308; }
  .badge-read { background:rgba(59,130,246,0.2); color:#3b82f6; }
  .badge-write { background:rgba(249,115,22,0.2); color:#f97316; }
  .badge-browser { background:rgba(6,182,212,0.2); color:#06b6d4; }
  .badge-msg { background:rgba(236,72,153,0.2); color:#ec4899; }
  .badge-search { background:rgba(20,184,166,0.2); color:#14b8a6; }
  .badge-done { background:rgba(34,197,94,0.2); color:#22c55e; }
  .badge-error { background:rgba(239,68,68,0.2); color:#ef4444; }
  .badge-tool { background:rgba(148,163,184,0.2); color:#94a3b8; }
  .brain-detail { color:var(--text-secondary); flex:1; min-width:0; white-space:pre-wrap; word-break:break-word; overflow-wrap:anywhere; }
  .brain-view-toggle { display:flex; gap:6px; margin-bottom:12px; }
  .brain-view-btn { padding:4px 12px; border-radius:10px; border:1px solid var(--border); background:transparent; color:var(--text-muted); font-size:11px; font-weight:600; cursor:pointer; }
  .brain-view-btn.active { border-color:#a855f7; background:rgba(168,85,247,0.2); color:#a855f7; }
  .brain-graph-container { width:100%; height:500px; background:var(--bg-secondary); border-radius:8px; border:1px solid var(--border); overflow:hidden; }
  #brain-graph-canvas { width:100%; height:500px; display:block; }
    .nav-tab { padding: 8px 16px; border-radius: 8px; background: transparent; border: 1px solid transparent; color: var(--text-tertiary); cursor: pointer; font-size: 13px; font-weight: 600; white-space: nowrap; transition: all 0.2s ease; position: relative; }
    .nav-tab-more { position: relative; }
    .advanced-tabs-dropdown { position: absolute; top: 100%; right: 0; background: var(--bg-primary); border: 1px solid var(--border-primary); border-radius: 8px; padding: 4px; z-index: 100; box-shadow: 0 4px 12px rgba(0,0,0,0.3); min-width: 140px; margin-top: 4px; display: flex; flex-direction: column; }
    .advanced-tabs-dropdown .nav-tab { display: block; width: 100%; text-align: left; border-radius: 6px; margin: 2px 0; }
  .nav-tab:hover { background: var(--bg-hover); color: var(--text-secondary); }
  .nav-tab.active { background: var(--bg-accent); color: #ffffff; border-color: var(--bg-accent); }
  .nav-tab:active { transform: scale(0.98); }
  .time-btn { padding: 4px 12px; border-radius: 6px; background: var(--bg-secondary); border: 1px solid var(--border-primary); color: var(--text-tertiary); cursor: pointer; font-size: 12px; font-weight: 600; transition: all 0.2s; }
  .time-btn:hover { background: var(--bg-hover); color: var(--text-secondary); }
  .time-btn.active { background: var(--bg-accent); color: #fff; border-color: var(--bg-accent); }

  .page { display: none; padding: 16px 20px; max-width: 1200px; margin: 0 auto; }
  #page-flow { padding: 0; max-width: 100%; }
  #page-overview { max-width: 1600px; padding: 8px 12px; }
  .page.active { display: block; }
  body.booting #zoom-wrapper { opacity: 0; pointer-events: none; transform: translateY(4px); }
  #zoom-wrapper { opacity: 1; transition: opacity 0.28s ease, transform 0.28s ease; }
  .boot-overlay {
    position: fixed;
    inset: 0;
    z-index: 9999;
    display: flex;
    align-items: center;
    justify-content: center;
    background: radial-gradient(1000px 540px at 70% -20%, rgba(15,111,255,0.18), transparent 60%), var(--bg-primary);
    transition: opacity 0.28s ease;
  }
  .boot-overlay.hide { opacity: 0; pointer-events: none; }
  .boot-card {
    width: min(540px, calc(100vw - 32px));
    border-radius: 14px;
    background: color-mix(in srgb, var(--bg-secondary) 92%, transparent);
    border: 1px solid var(--border-primary);
    box-shadow: var(--card-shadow-hover);
    padding: 18px 18px 14px;
  }
  .boot-title { font-size: 20px; font-weight: 800; color: var(--text-primary); margin-bottom: 4px; }
  .boot-sub { font-size: 12px; color: var(--text-muted); margin-bottom: 14px; }
  .boot-spinner {
    width: 28px; height: 28px; border-radius: 50%;
    border: 2px solid var(--border-primary); border-top-color: var(--bg-accent);
    animation: spin 0.8s linear infinite; margin-bottom: 10px;
  }
  .boot-steps { display: grid; gap: 8px; }
  .boot-step {
    display: flex; align-items: center; gap: 8px; padding: 8px 10px;
    border: 1px solid var(--border-secondary); border-radius: 10px; background: var(--bg-tertiary);
    font-size: 12px; color: var(--text-secondary);
  }
  .boot-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--text-faint); flex-shrink: 0; }
  .boot-step.loading .boot-dot { background: #f59e0b; box-shadow: 0 0 0 4px rgba(245,158,11,0.18); }
  .boot-step.done .boot-dot { background: #22c55e; box-shadow: 0 0 0 4px rgba(34,197,94,0.16); }
  .boot-step.fail .boot-dot { background: #ef4444; box-shadow: 0 0 0 4px rgba(239,68,68,0.16); }
  @keyframes spin { to { transform: rotate(360deg); } }

  .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 16px; margin-bottom: 16px; }
  .card { background: var(--bg-tertiary); border: 1px solid var(--border-primary); border-radius: 12px; padding: 20px; box-shadow: var(--card-shadow); transition: transform 0.2s ease, box-shadow 0.2s ease; }
  .card-title { font-size: 12px; text-transform: uppercase; color: var(--text-muted); letter-spacing: 1px; margin-bottom: 12px; display: flex; align-items: center; gap: 8px; }
  .card-title .icon { font-size: 16px; }
  .card-value { font-size: 32px; font-weight: 700; color: var(--text-primary); letter-spacing: -0.5px; }
  .card-sub { font-size: 12px; color: var(--text-faint); margin-top: 4px; }

  .stat-row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid var(--border-secondary); }
  .stat-row:last-child { border-bottom: none; }
  .stat-label { color: var(--text-tertiary); font-size: 13px; }
  .stat-val { color: var(--text-primary); font-size: 13px; font-weight: 600; }
  .stat-val.green { color: var(--text-success); }
  .stat-val.yellow { color: var(--text-warning); }
  .stat-val.red { color: var(--text-error); }

  .session-item { padding: 12px; border-bottom: 1px solid var(--border-secondary); }
  .session-item:last-child { border-bottom: none; }
  .session-name { font-weight: 600; font-size: 14px; color: var(--text-primary); }
  .session-meta { font-size: 12px; color: var(--text-muted); margin-top: 4px; display: flex; gap: 12px; flex-wrap: wrap; }
  .session-meta span { display: flex; align-items: center; gap: 4px; }
  .session-anomaly { color: #f59e0b; font-size: 14px; margin-left: 6px; cursor: help; }

  .cron-item { padding: 12px; border-bottom: 1px solid var(--border-secondary); }
  .cron-item:last-child { border-bottom: none; }
  .cron-name { font-weight: 600; font-size: 14px; color: var(--text-primary); }
  .cron-schedule { font-size: 12px; color: var(--text-accent); margin-top: 2px; font-family: 'SF Mono', 'Fira Code', monospace; }
  .cron-meta { font-size: 12px; color: var(--text-muted); margin-top: 4px; }
  .cron-status { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }
  .cron-status.ok { background: var(--bg-success); color: var(--text-success); }
  .cron-status.error { background: var(--bg-error); color: var(--text-error); }
  .cron-status.pending { background: var(--bg-warning); color: var(--text-warning); }

  /* Cron error info & fix */
  .cron-error-actions { display: inline-flex; align-items: center; gap: 6px; margin-left: 8px; vertical-align: middle; }
  .cron-info-icon { cursor: pointer; font-size: 14px; color: var(--text-muted); transition: color 0.15s; user-select: none; }
  .cron-info-icon:hover { color: var(--text-accent); }
  .cron-fix-btn { background: #f59e0b; color: #fff; border: none; border-radius: 6px; padding: 2px 10px; font-size: 11px; font-weight: 600; cursor: pointer; transition: background 0.15s; white-space: nowrap; }
  .cron-fix-btn:hover { background: #d97706; }
  .cron-error-popover { position: fixed; z-index: 1000; background: #1a1a2e; color: #e0e0e0; border: 1px solid #333; border-radius: 10px; padding: 14px 18px; max-width: 400px; font-size: 12px; line-height: 1.6; box-shadow: 0 8px 30px rgba(0,0,0,0.5); pointer-events: auto; }
  .cron-error-popover .ep-label { font-size: 10px; text-transform: uppercase; letter-spacing: 1px; color: #888; margin-bottom: 2px; }
  .cron-error-popover .ep-value { color: #fca5a5; margin-bottom: 10px; word-break: break-word; }
  .cron-error-popover .ep-value.ts { color: #93c5fd; }
  .cron-error-popover .ep-close { position: absolute; top: 8px; right: 12px; cursor: pointer; color: #888; font-size: 16px; }
  .cron-error-popover .ep-close:hover { color: #fff; }
  .cron-toast { position: fixed; bottom: 24px; left: 50%; transform: translateX(-50%); background: #16a34a; color: #fff; padding: 10px 24px; border-radius: 8px; font-size: 13px; font-weight: 600; z-index: 2000; box-shadow: 0 4px 16px rgba(0,0,0,0.3); transition: opacity 0.3s; }
  .cron-confirm-modal { position: fixed; inset: 0; z-index: 1500; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; }
  .cron-confirm-box { background: var(--bg-tertiary); border: 1px solid var(--border-primary); border-radius: 12px; padding: 24px; max-width: 360px; text-align: center; box-shadow: 0 8px 30px rgba(0,0,0,0.4); }
  .cron-confirm-box p { margin-bottom: 16px; font-size: 14px; color: var(--text-primary); }
  .cron-confirm-box button { padding: 8px 20px; border-radius: 8px; border: none; font-size: 13px; font-weight: 600; cursor: pointer; margin: 0 6px; }
  .cron-confirm-box .confirm-yes { background: #f59e0b; color: #fff; }
  .cron-confirm-box .confirm-yes:hover { background: #d97706; }
  .cron-confirm-box .confirm-no { background: var(--button-bg); color: var(--text-secondary); }
  .cron-confirm-box .confirm-no:hover { background: var(--button-hover); }
  .cron-actions { display: flex; gap: 6px; margin-top: 8px; }
  .cron-actions button { padding: 4px 12px; border-radius: 6px; border: none; font-size: 11px; font-weight: 600; cursor: pointer; transition: background 0.15s; }
  .cron-btn-run { background: #10b981; color: #fff; }
  .cron-btn-run:hover { background: #059669; }
  .cron-btn-toggle { background: #6366f1; color: #fff; }
  .cron-btn-toggle:hover { background: #4f46e5; }
  .cron-btn-edit { background: #3b82f6; color: #fff; }
  .cron-btn-edit:hover { background: #2563eb; }
  .cron-btn-delete { background: #ef4444; color: #fff; }
  .cron-btn-delete:hover { background: #dc2626; }
  .cron-disabled { opacity: 0.5; }
  .cron-expand { margin-top: 10px; padding-top: 10px; border-top: 1px solid var(--border-secondary); font-size: 12px; color: var(--text-muted); }
  .cron-expand .run-entry { padding: 4px 0; display: flex; justify-content: space-between; border-bottom: 1px solid rgba(255,255,255,0.05); }
  .cron-expand .run-status-ok { color: var(--text-success); }
  .cron-expand .run-status-error { color: var(--text-error); }
  .cron-item { cursor: pointer; }
  .cron-config-detail { margin-top: 8px; padding: 8px; background: var(--bg-secondary); border-radius: 6px; font-family: 'SF Mono','Fira Code',monospace; font-size: 11px; white-space: pre-wrap; word-break: break-all; }

  .log-viewer { background: var(--log-bg); border: 1px solid var(--border-primary); border-radius: 8px; font-family: 'SF Mono', 'Fira Code', 'JetBrains Mono', monospace; font-size: 12px; line-height: 1.6; padding: 12px; max-height: 500px; overflow-y: auto; -webkit-overflow-scrolling: touch; white-space: pre-wrap; word-break: break-all; }
  .log-line { padding: 1px 0; }
  .log-line .ts { color: var(--text-muted); }
  .log-line .info { color: var(--text-link); }
  .log-line .warn { color: var(--text-warning); }
  .log-line .err { color: var(--text-error); }
  .log-line .msg { color: var(--text-secondary); }

  .memory-item { padding: 10px 12px; border-bottom: 1px solid var(--border-secondary); display: flex; justify-content: space-between; align-items: center; cursor: pointer; transition: background 0.15s; }
  .memory-item:hover { background: var(--bg-hover); }
  .memory-item:last-child { border-bottom: none; }
  .file-viewer { background: var(--file-viewer-bg); border: 1px solid var(--border-primary); border-radius: 12px; padding: 16px; margin-top: 16px; display: none; }
  .file-viewer-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
  .file-viewer-title { font-size: 14px; font-weight: 600; color: var(--text-accent); }
  .file-viewer-close { background: var(--button-bg); border: none; color: var(--text-secondary); padding: 4px 12px; border-radius: 6px; cursor: pointer; font-size: 13px; }
  .file-viewer-close:hover { background: var(--button-hover); }
  .file-viewer-content { font-family: 'SF Mono', 'Fira Code', monospace; font-size: 12px; color: var(--text-secondary); white-space: pre-wrap; word-break: break-word; max-height: 60vh; overflow-y: auto; line-height: 1.5; }
  .memory-name { font-weight: 600; font-size: 14px; color: var(--text-link); cursor: pointer; }
  .memory-name:hover { text-decoration: underline; }
  .memory-size { font-size: 12px; color: var(--text-faint); }

  .refresh-bar { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
  .refresh-btn { padding: 8px 16px; background: var(--button-bg); border: 1px solid var(--border-primary); border-radius: 8px; color: var(--text-primary); cursor: pointer; font-size: 13px; font-weight: 500; transition: all 0.15s ease; }
  .refresh-btn:hover { background: var(--button-hover); }
  .refresh-btn:active { transform: scale(0.98); }
  .refresh-time { font-size: 12px; color: var(--text-muted); }
  .pulse { display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: #16a34a; animation: pulse 1.5s infinite; }
  @keyframes pulse { 0%,100% { opacity: 1; box-shadow: 0 0 4px #16a34a; } 50% { opacity: 0.3; box-shadow: none; } }
  .live-badge { display: inline-block; padding: 2px 8px; border-radius: 4px; background: var(--bg-success); color: var(--text-success); font-size: 11px; font-weight: 700; letter-spacing: 1px; text-transform: uppercase; animation: pulse 1.5s infinite; }

  .badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }
  .badge.model { background: var(--bg-hover); color: var(--text-accent); }
  .badge.channel { background: var(--bg-hover); color: #7c3aed; }
  .badge.tokens { background: var(--bg-success); color: var(--text-success); }

  /* Cost Optimizer Styles */
  .cost-optimizer-summary { margin-bottom: 20px; }
  .cost-stat-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 12px; }
  .cost-stat { background: var(--bg-hover); border-radius: 8px; padding: 12px; text-align: center; border: 1px solid var(--border-primary); }
  .cost-label { font-size: 11px; text-transform: uppercase; color: var(--text-muted); letter-spacing: 1px; margin-bottom: 4px; }
  .cost-value { font-size: 20px; font-weight: 700; color: var(--text-primary); }
  .local-status-good { padding: 8px 12px; background: var(--bg-success); color: var(--text-success); border-radius: 6px; font-size: 13px; font-weight: 600; }
  .local-status-warning { padding: 8px 12px; background: var(--bg-warning); color: var(--text-warning); border-radius: 6px; font-size: 13px; font-weight: 600; }
  .model-list { display: flex; flex-wrap: wrap; gap: 6px; }
  .model-badge { background: var(--bg-accent); color: #ffffff; padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }
  .recommendation { border-left: 3px solid var(--text-accent); }

  /* Cost Optimizer Enhanced Cards */
  .co-section { margin-top: 20px; }
  .co-section h3 { color: var(--text-accent); margin-bottom: 12px; font-size: 15px; font-weight: 700; }
  .co-model-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px; }
  .co-model-card { background: var(--bg-tertiary); border: 1px solid var(--border-primary); border-radius: 10px; padding: 14px; transition: border-color 0.2s, transform 0.15s; cursor: default; }
  .co-model-card:hover { border-color: var(--text-accent); transform: translateY(-2px); }
  .co-model-name { font-weight: 700; font-size: 13px; color: var(--text-primary); margin-bottom: 6px; word-break: break-all; }
  .co-model-provider { font-size: 11px; color: var(--text-muted); margin-bottom: 8px; }
  .co-badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px; }
  .co-badge.chat { background: #1e3a5f; color: #60a5fa; }
  .co-badge.coding { background: #14532d; color: #4ade80; }
  .co-model-stats { font-size: 12px; color: var(--text-secondary); margin-bottom: 8px; display: flex; flex-direction: column; gap: 2px; }
  .co-model-stat { display: flex; justify-content: space-between; }
  .co-model-stat span:last-child { font-weight: 600; color: var(--text-primary); }
  .co-speed-note { font-size: 10px; color: #4ade80; margin-top: 4px; }
  .co-action-btn { display: inline-block; margin-top: 8px; padding: 4px 10px; background: var(--bg-accent); color: #fff; border: none; border-radius: 5px; font-size: 11px; font-weight: 600; cursor: pointer; width: 100%; text-align: center; transition: opacity 0.15s; }
  .co-action-btn:hover { opacity: 0.8; }
  .co-action-btn.secondary { background: var(--bg-hover); color: var(--text-primary); border: 1px solid var(--border-primary); }
  .co-savings-row { display: flex; flex-direction: column; gap: 3px; padding: 10px 12px; background: var(--bg-hover); border-radius: 8px; border-left: 3px solid #fbbf24; margin-bottom: 8px; }
  .co-savings-title { font-weight: 600; font-size: 13px; color: var(--text-primary); }
  .co-savings-detail { font-size: 12px; color: var(--text-secondary); }
  .co-savings-amount { font-size: 12px; color: #4ade80; font-weight: 600; }
  .co-sys-info { background: var(--bg-tertiary); border: 1px solid var(--border-primary); border-radius: 8px; padding: 10px 14px; font-size: 12px; color: var(--text-secondary); margin-bottom: 12px; display: flex; gap: 16px; flex-wrap: wrap; }
  .co-sys-item { display: flex; align-items: center; gap: 5px; }
  .co-sys-item strong { color: var(--text-primary); }
  .co-ollama-prompt { background: #1c1c2e; border: 1px dashed #7c3aed; border-radius: 8px; padding: 12px 14px; margin-bottom: 12px; }
  .co-ollama-cmd { font-family: monospace; font-size: 12px; background: var(--bg-tertiary); padding: 6px 10px; border-radius: 5px; margin-top: 6px; color: #a78bfa; }

  /* Cost Optimizer v2 -- llmfit-powered */
  .cost-overview { background: linear-gradient(135deg, #1a2a1a, #1a1a2a); border: 1px solid #2d4a2d; border-radius: 12px; padding: 16px 20px; margin-bottom: 16px; }
  .cost-overview-header { font-size: 14px; font-weight: 700; color: #4ade80; margin-bottom: 10px; letter-spacing: 0.3px; }
  .cost-overview-row { display: flex; gap: 20px; flex-wrap: wrap; align-items: center; margin-bottom: 6px; }
  .cost-overview-item { display: flex; flex-direction: column; }
  .cost-overview-label { font-size: 10px; text-transform: uppercase; letter-spacing: 1px; color: #6b7280; margin-bottom: 2px; }
  .cost-overview-value { font-size: 20px; font-weight: 700; color: #fbbf24; }
  .cost-overview-value.green { color: #4ade80; }
  .savings-highlight { background: #0f2d0f; border: 1px solid #14532d; border-radius: 8px; padding: 8px 12px; font-size: 12px; color: #4ade80; font-weight: 600; margin-top: 8px; }
  .hw-card { background: var(--bg-tertiary); border: 1px solid #2d3748; border-radius: 10px; padding: 12px 16px; margin-bottom: 16px; display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
  .hw-card-chip { background: #1e3a5f; border-radius: 6px; padding: 4px 10px; font-size: 12px; font-weight: 600; color: #60a5fa; }
  .hw-card-chip.green { background: #14532d; color: #4ade80; }
  .hw-card-chip.amber { background: #451a03; color: #fbbf24; }
  .hw-metal-notice { background: #1c1500; border: 1px solid #92400e; border-radius: 8px; padding: 8px 12px; font-size: 11px; color: #fbbf24; margin-bottom: 12px; }
  .model-card { background: var(--bg-tertiary); border: 1px solid var(--border-primary); border-radius: 10px; padding: 14px; margin-bottom: 10px; transition: border-color 0.2s, transform 0.15s; }
  .model-card:hover { border-color: #4ade80; transform: translateY(-1px); }
  .model-card-header { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 8px; gap: 8px; }
  .model-card-name { font-weight: 700; font-size: 13px; color: var(--text-primary); }
  .model-badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; flex-shrink: 0; }
  .model-badge.coding { background: #14532d; color: #4ade80; }
  .model-badge.chat { background: #1e3a5f; color: #60a5fa; }
  .model-card-stats { display: flex; gap: 12px; flex-wrap: wrap; font-size: 11px; color: var(--text-muted); margin-bottom: 8px; }
  .model-card-stat { display: flex; flex-direction: column; }
  .model-card-stat-label { font-size: 9px; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 1px; }
  .model-card-stat-value { font-weight: 600; color: var(--text-primary); }
  .model-install-cmd { background: #0d1117; border: 1px solid #30363d; border-radius: 6px; padding: 6px 10px; font-family: monospace; font-size: 11px; color: #e6edf3; margin-top: 6px; cursor: pointer; display: flex; justify-content: space-between; align-items: center; }
  .model-install-cmd:hover { border-color: #4ade80; }
  .task-rec { background: var(--bg-hover); border-left: 3px solid #fbbf24; border-radius: 0 8px 8px 0; padding: 10px 14px; margin-bottom: 8px; display: grid; grid-template-columns: 1fr auto; gap: 4px 12px; align-items: start; }
  .task-rec-title { font-weight: 600; font-size: 13px; color: var(--text-primary); }
  .task-rec-savings { font-size: 12px; font-weight: 700; color: #4ade80; white-space: nowrap; }
  .task-rec-arrow { font-size: 11px; color: var(--text-muted); grid-column: 1; }
  .task-rec-reason { font-size: 11px; color: var(--text-muted); grid-column: 1 / -1; }

  .full-width { grid-column: 1 / -1; }
  .section-title { font-size: 16px; font-weight: 700; color: var(--text-primary); margin: 24px 0 12px; display: flex; align-items: center; gap: 8px; }

  /* === Flow Visualization === */
  .flow-container { width: 100%; overflow: visible; position: relative; }
  .flow-stats { display: flex; gap: 12px; margin-bottom: 12px; flex-wrap: wrap; }
  .flow-stat { background: var(--bg-tertiary); border: 1px solid var(--border-primary); border-radius: 8px; padding: 8px 14px; flex: 1; min-width: 100px; box-shadow: var(--card-shadow); }
  .flow-stat-label { font-size: 10px; text-transform: uppercase; color: var(--text-muted); letter-spacing: 1px; display: block; }
  .flow-stat-value { font-size: 20px; font-weight: 700; color: var(--text-primary); display: block; margin-top: 2px; }
  #flow-svg { width: 100%; height: calc(100vh - 155px); min-height: 400px; display: block; overflow: visible; }
  #flow-svg text { font-family: 'Manrope', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; font-size: 14px; font-weight: 700; text-anchor: middle; dominant-baseline: central; pointer-events: none; letter-spacing: -0.1px; }
  .flow-node-channel text, .flow-node-gateway text, .flow-node-session text, .flow-node-tool text { fill: #ffffff !important; }
  .flow-node-optimizer text { fill: #ffffff !important; }
  .flow-node-infra > text { fill: #ffffff !important; }
  /* Refined palette: lower saturation, clearer hierarchy */
  [id$="node-human"] circle:first-child { fill: #6d5ce8 !important; stroke: #5b4bd4 !important; }
  [id$="node-human"] text { fill: #6d5ce8 !important; }
  [id$="node-telegram"] rect { fill: #2f6feb !important; stroke: #1f4fb8 !important; }
  [id$="node-signal"] rect { fill: #0f766e !important; stroke: #115e59 !important; }
  [id$="node-whatsapp"] rect { fill: #2f9e44 !important; stroke: #237738 !important; }
  [id$="node-imessage"] rect { fill: #34C759 !important; stroke: #248A3D !important; }
  [id$="node-discord"] rect { fill: #5865F2 !important; stroke: #4752C4 !important; }
  [id$="node-slack"] rect { fill: #4A154B !important; stroke: #350e36 !important; }
  [id$="node-irc"] rect { fill: #6B7280 !important; stroke: #4B5563 !important; }
  [id$="node-webchat"] rect { fill: #0EA5E9 !important; stroke: #0369A1 !important; }
  [id$="node-googlechat"] rect { fill: #1A73E8 !important; stroke: #1557B0 !important; }
  [id$="node-bluebubbles"] rect { fill: #1C6EF3 !important; stroke: #1558C0 !important; }
  [id$="node-msteams"] rect { fill: #6264A7 !important; stroke: #464775 !important; }
  [id$="node-matrix"] rect { fill: #0DBD8B !important; stroke: #0A9E74 !important; }
  [id$="node-mattermost"] rect { fill: #0058CC !important; stroke: #0047A3 !important; }
  [id$="node-line"] rect { fill: #00B900 !important; stroke: #009900 !important; }
  [id$="node-nostr"] rect { fill: #8B5CF6 !important; stroke: #6D28D9 !important; }
  [id$="node-twitch"] rect { fill: #9146FF !important; stroke: #772CE8 !important; }
  [id$="node-feishu"] rect { fill: #3370FF !important; stroke: #2050CC !important; }
  [id$="node-zalo"] rect { fill: #0068FF !important; stroke: #0050CC !important; }
  [id$="node-gateway"] rect { fill: #334155 !important; stroke: #1f2937 !important; }
  [id$="node-brain"] rect { fill: #312e81 !important; stroke: #1e1b4b !important; }
  [id$="brain-model-label"] { fill: #e0e7ff !important; }
  [id$="brain-model-text"] { fill: #c7d2fe !important; }
  [id$="node-session"] rect { fill: #3158d4 !important; stroke: #2648b6 !important; }
  [id$="node-exec"] rect { fill: #d97706 !important; stroke: #b45309 !important; }
  [id$="node-browser"] rect { fill: #5b39c6 !important; stroke: #4629a1 !important; }
  [id$="node-search"] rect { fill: #0f766e !important; stroke: #115e59 !important; }
  [id$="node-cron"] rect { fill: #4b5563 !important; stroke: #374151 !important; }
  [id$="node-tts"] rect { fill: #a16207 !important; stroke: #854d0e !important; }
  [id$="node-memory"] rect { fill: #1e3a8a !important; stroke: #172554 !important; }
  [id$="node-cost-optimizer"] rect { fill: #166534 !important; stroke: #14532d !important; }
  [id$="node-automation-advisor"] rect { fill: #4338ca !important; stroke: #3730a3 !important; }
  [id$="node-runtime"] rect { fill: #334155 !important; stroke: #475569 !important; }
  [id$="node-machine"] rect { fill: #424b57 !important; stroke: #2f3945 !important; }
  [id$="node-storage"] rect { fill: #52525b !important; stroke: #3f3f46 !important; }
  [id$="node-network"] rect { fill: #0f766e !important; stroke: #115e59 !important; }
  .flow-node-clickable { cursor: pointer; }
  .flow-node-clickable:hover rect, .flow-node-clickable:hover circle { filter: brightness(1.08); }
  .flow-node rect { rx: 12; ry: 12; stroke-width: 1.6; transition: all 0.25s ease; }
  .flow-node-brain rect { stroke-width: 2.5; }
  @keyframes pulse-dot { 0%,100% { opacity:1; box-shadow:0 0 4px #2ecc71; } 50% { opacity:0.4; box-shadow:none; } }
  @keyframes dashFlow { to { stroke-dashoffset: -24; } }
  .flow-path { stroke-dasharray: 8 4; animation: dashFlow 1.2s linear infinite; }
  .flow-path.flow-path-infra { stroke-dasharray: 6 3; animation: dashFlow 2s linear infinite; }
  .flow-node-channel.active rect { filter: drop-shadow(0 0 8px rgba(59,130,246,0.38)); stroke-width: 2.2; }
  .flow-node-gateway.active rect { filter: drop-shadow(0 0 8px rgba(71,85,105,0.38)); stroke-width: 2.2; }
  .flow-node-session.active rect { filter: drop-shadow(0 0 8px rgba(49,88,212,0.35)); stroke-width: 2.2; }
  .flow-node-tool.active rect { filter: drop-shadow(0 0 7px rgba(217,119,6,0.32)); stroke-width: 2.2; }
  .flow-node-optimizer.active rect { filter: drop-shadow(0 0 7px rgba(22,101,52,0.35)); stroke-width: 2.2; }
  .flow-path { fill: none; stroke: var(--text-muted); stroke-width: 1.8; stroke-linecap: round; transition: stroke 0.35s, opacity 0.35s; opacity: 0.45; }
  .flow-path.glow-blue { stroke: #4080e0; filter: drop-shadow(0 0 6px rgba(64,128,224,0.6)); }
  .flow-path.glow-yellow { stroke: #f0c040; filter: drop-shadow(0 0 6px rgba(240,192,64,0.6)); }
  .flow-path.glow-green { stroke: #50e080; filter: drop-shadow(0 0 6px rgba(80,224,128,0.6)); }
  .flow-path.glow-red { stroke: #e04040; filter: drop-shadow(0 0 6px rgba(224,64,64,0.6)); }
  @keyframes brainPulse { 0%,100% { filter: drop-shadow(0 0 6px rgba(129,140,248,0.18)); } 50% { filter: drop-shadow(0 0 18px rgba(129,140,248,0.45)); } }
  .brain-group { animation: brainPulse 2.2s ease-in-out infinite; }
  .tool-indicator { opacity: 0.2; transition: opacity 0.3s ease; }
  .tool-indicator.active { opacity: 1; }
  .flow-label { font-size: 10px !important; fill: var(--text-muted) !important; font-weight: 500 !important; }
  .flow-node-human circle { transition: all 0.3s ease; }
  .flow-node-human.active circle { filter: drop-shadow(0 0 12px rgba(176,128,255,0.7)); }
  @keyframes humanGlow { 0%,100% { filter: drop-shadow(0 0 3px rgba(160,112,224,0.15)); } 50% { filter: drop-shadow(0 0 10px rgba(160,112,224,0.45)); } }
  .flow-node-human { animation: humanGlow 3.5s ease-in-out infinite; }
  .flow-ground { stroke: var(--border-primary); stroke-width: 1; stroke-dasharray: 8 4; }
  .flow-ground-label { font-size: 10px !important; fill: var(--text-muted) !important; font-weight: 700 !important; letter-spacing: 3px; }
  .flow-node-infra rect { rx: 6; ry: 6; stroke-width: 2; stroke-dasharray: 5 2; transition: all 0.3s ease; }
  .flow-node-infra text { font-size: 12px !important; }
  .flow-node-infra .infra-sub { font-size: 8px !important; fill: var(--text-muted) !important; font-weight: 500 !important; opacity: 0.9; }
  .flow-node-runtime rect { stroke: #4a7090; }
  .flow-node-machine rect { stroke: #606880; }
  .flow-node-storage rect { stroke: #806a30; }
  .flow-node-network rect { stroke: #308080; }
  [data-theme="dark"] .flow-node-runtime rect { fill: #10182a; }
  [data-theme="dark"] .flow-node-machine rect { fill: #141420; }
  [data-theme="dark"] .flow-node-storage rect { fill: #1a1810; }
  [data-theme="dark"] .flow-node-network rect { fill: #0e1c20; }
  .flow-node-runtime.active rect { filter: drop-shadow(0 0 10px rgba(74,112,144,0.7)); stroke-dasharray: none; stroke-width: 2.5; }
  .flow-node-machine.active rect { filter: drop-shadow(0 0 10px rgba(96,104,128,0.7)); stroke-dasharray: none; stroke-width: 2.5; }
  .flow-node-storage.active rect { filter: drop-shadow(0 0 10px rgba(128,106,48,0.7)); stroke-dasharray: none; stroke-width: 2.5; }
  .flow-node-network.active rect { filter: drop-shadow(0 0 10px rgba(48,128,128,0.7)); stroke-dasharray: none; stroke-width: 2.5; }
  .flow-path-infra { stroke-dasharray: 6 3; opacity: 0.3; }
  .flow-path.glow-cyan { stroke: #40a0b0; filter: drop-shadow(0 0 6px rgba(64,160,176,0.6)); stroke-dasharray: none; opacity: 1; }
  .flow-path.glow-purple { stroke: #b080ff; filter: drop-shadow(0 0 6px rgba(176,128,255,0.6)); }

  /* === Activity Heatmap === */
  .heatmap-wrap { overflow-x: auto; padding: 8px 0; }
  .heatmap-grid { display: grid; grid-template-columns: 60px repeat(24, 1fr); gap: 2px; min-width: 650px; }
  .heatmap-label { font-size: 11px; color: #666; display: flex; align-items: center; padding-right: 8px; justify-content: flex-end; }
  .heatmap-hour-label { font-size: 10px; color: #555; text-align: center; padding-bottom: 4px; }
  .heatmap-cell { aspect-ratio: 1; border-radius: 3px; min-height: 16px; transition: all 0.15s; cursor: default; position: relative; }
  .heatmap-cell:hover { transform: scale(1.3); z-index: 2; outline: 1px solid #f0c040; }
  .heatmap-cell[title]:hover::after { content: attr(title); position: absolute; bottom: 120%; left: 50%; transform: translateX(-50%); background: #222; color: #eee; padding: 3px 8px; border-radius: 4px; font-size: 10px; white-space: nowrap; z-index: 10; pointer-events: none; }
  .heatmap-legend { display: flex; align-items: center; gap: 6px; margin-top: 10px; font-size: 11px; color: #666; }
  .heatmap-legend-cell { width: 14px; height: 14px; border-radius: 3px; }

  /* === Health Checks === */
  .health-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; }
  .health-item { background: var(--bg-tertiary); border: 1px solid var(--border-primary); border-radius: 10px; padding: 14px 16px; display: flex; align-items: center; gap: 12px; transition: border-color 0.3s; box-shadow: var(--card-shadow); }
  .health-item.healthy { border-left: 3px solid #16a34a; }
  .health-item.warning { border-left: 3px solid #d97706; }
  .health-item.critical { border-left: 3px solid #dc2626; }
  .health-dot { width: 12px; height: 12px; border-radius: 50%; flex-shrink: 0; }
  .health-dot.green { background: #16a34a; box-shadow: 0 0 8px rgba(22,163,74,0.5); }
  .health-dot.yellow { background: #d97706; box-shadow: 0 0 8px rgba(217,119,6,0.5); }
  .health-dot.red { background: #dc2626; box-shadow: 0 0 8px rgba(220,38,38,0.5); }
  .health-info { flex: 1; }
  .health-name { font-size: 13px; font-weight: 600; color: var(--text-primary); }
  .health-detail { font-size: 11px; color: var(--text-muted); margin-top: 2px; }

  /* === Usage/Token Charts === */
  .usage-chart { display: flex; align-items: flex-end; gap: 6px; height: 200px; padding: 16px 8px 32px; position: relative; }
  .usage-bar-wrap { flex: 1; display: flex; flex-direction: column; align-items: center; height: 100%; justify-content: flex-end; position: relative; }
  .usage-bar { width: 100%; min-width: 20px; max-width: 48px; border-radius: 6px 6px 0 0; background: linear-gradient(180deg, var(--bg-accent), #1d4ed8); transition: height 0.4s ease; position: relative; cursor: default; }
  .usage-bar:hover { filter: brightness(1.25); }
  .usage-bar-label { font-size: 9px; color: var(--text-muted); margin-top: 6px; text-align: center; white-space: nowrap; }
  .usage-bar-value { font-size: 9px; color: var(--text-tertiary); text-align: center; position: absolute; top: -16px; width: 100%; white-space: nowrap; }
  .usage-grid-line { position: absolute; left: 0; right: 0; border-top: 1px dashed var(--border-secondary); }
  .usage-grid-label { position: absolute; right: 100%; padding-right: 8px; font-size: 10px; color: var(--text-muted); white-space: nowrap; }
  .usage-table { width: 100%; border-collapse: collapse; }
  .usage-table th { text-align: left; font-size: 12px; color: var(--text-muted); padding: 8px 12px; border-bottom: 1px solid var(--border-primary); font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }
  .usage-table td { padding: 8px 12px; font-size: 13px; color: var(--text-secondary); border-bottom: 1px solid var(--border-secondary); }
  .usage-table tr:last-child td { border-bottom: none; font-weight: 700; color: var(--text-accent); }
  
  /* === Cost Warnings === */
  .cost-warning { padding: 12px 16px; border-radius: 8px; margin-bottom: 8px; display: flex; align-items: center; gap: 10px; font-size: 13px; }
  /* === Markdown Rendered Content === */
  .md-rendered h1,.md-rendered h2,.md-rendered h3,.md-rendered h4 { margin: 8px 0 4px; color: var(--text-primary); }
  .md-rendered h1 { font-size: 18px; } .md-rendered h2 { font-size: 16px; } .md-rendered h3 { font-size: 14px; }
  .md-rendered p { margin: 4px 0; }
  .md-rendered code { background: var(--bg-secondary); padding: 1px 5px; border-radius: 4px; font-size: 12px; font-family: 'SF Mono','JetBrains Mono',monospace; }
  .md-rendered pre { background: var(--bg-secondary); border: 1px solid var(--border-primary); border-radius: 8px; padding: 10px 14px; overflow-x: auto; margin: 6px 0; }
  .md-rendered pre code { background: none; padding: 0; }
  .md-rendered ul,.md-rendered ol { padding-left: 20px; margin: 4px 0; }
  .md-rendered blockquote { border-left: 3px solid var(--text-accent); padding-left: 12px; margin: 6px 0; color: var(--text-secondary); }
  .md-rendered strong { color: var(--text-primary); }
  .md-rendered a { color: var(--text-link); }
  .md-rendered table { border-collapse: collapse; margin: 6px 0; }
  .md-rendered th,.md-rendered td { border: 1px solid var(--border-primary); padding: 4px 8px; font-size: 12px; }

  .cost-warning.error { background: var(--bg-error); border: 1px solid var(--text-error); color: var(--text-error); }
  .cost-warning.warning { background: var(--bg-warning); border: 1px solid var(--text-warning); color: var(--text-warning); }
  .cost-warning-icon { font-size: 16px; }
  .cost-warning-message { flex: 1; }

  /* === Transcript Viewer === */
  .transcript-item { padding: 12px 16px; border-bottom: 1px solid var(--border-secondary); cursor: pointer; transition: background 0.15s; display: flex; justify-content: space-between; align-items: center; }
  .transcript-item:hover { background: var(--bg-hover); }
  .transcript-item:last-child { border-bottom: none; }
  .transcript-name { font-weight: 600; font-size: 14px; color: var(--text-link); }
  .transcript-meta-row { font-size: 12px; color: var(--text-muted); margin-top: 4px; display: flex; gap: 12px; flex-wrap: wrap; }
  .transcript-viewer-meta { background: var(--bg-secondary); border: 1px solid var(--border-primary); border-radius: 12px; padding: 16px; margin-bottom: 16px; }
  .transcript-viewer-meta .stat-row { padding: 6px 0; }
  .chat-messages { display: flex; flex-direction: column; gap: 10px; padding: 8px 0; }
  .chat-msg { max-width: 85%; padding: 12px 16px; border-radius: 16px; font-size: 13px; line-height: 1.5; word-wrap: break-word; position: relative; }
  .chat-msg.user { background: #1a2a4a; border: 1px solid #2a4a7a; color: #c0d8ff; align-self: flex-end; border-bottom-right-radius: 4px; }
  .chat-msg.assistant { background: #1a3a2a; border: 1px solid #2a5a3a; color: #c0ffc0; align-self: flex-start; border-bottom-left-radius: 4px; }
  .chat-msg.system { background: #2a2a1a; border: 1px solid #4a4a2a; color: #f0e0a0; align-self: center; font-size: 12px; font-style: italic; max-width: 90%; }
  .chat-msg.tool { background: #1a1a24; border: 1px solid #2a2a3a; color: #a0a0b0; align-self: flex-start; font-family: 'SF Mono', monospace; font-size: 12px; border-left: 3px solid #555; }
  .chat-role { font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px; opacity: 0.7; }
  .chat-ts { font-size: 10px; color: #555; margin-top: 6px; text-align: right; }
  .chat-expand { display: inline-block; color: #f0c040; font-size: 11px; cursor: pointer; margin-top: 4px; }
  .chat-expand:hover { text-decoration: underline; }
  .chat-content-truncated { max-height: 200px; overflow: hidden; position: relative; }
  .chat-content-truncated::after { content: ''; position: absolute; bottom: 0; left: 0; right: 0; height: 40px; background: linear-gradient(transparent, rgba(26,42,74,0.9)); pointer-events: none; }
  .chat-msg.assistant .chat-content-truncated::after { background: linear-gradient(transparent, rgba(26,58,42,0.9)); }
  .chat-msg.tool .chat-content-truncated::after { background: linear-gradient(transparent, rgba(26,26,36,0.9)); }

  /* === Mini Dashboard Widgets === */
  .tool-spark { font-size: 11px; color: var(--text-muted); padding: 3px 8px; background: var(--bg-secondary); border-radius: 6px; border: 1px solid var(--border-secondary); }
  .tool-spark span { color: var(--text-accent); font-weight: 600; }
  .card:hover { transform: translateY(-1px); box-shadow: var(--card-shadow-hover); }
  .card[onclick] { cursor: pointer; }

  /* === Sub-Agent Worker Bees === */
  .subagent-item { display: flex; align-items: center; gap: 6px; padding: 2px 0; font-size: 10px; }
  .subagent-status { width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0; }
  .subagent-status.active { background: #16a34a; box-shadow: 0 0 4px rgba(22,163,74,0.5); }
  .subagent-status.idle { background: #d97706; box-shadow: 0 0 4px rgba(217,119,6,0.5); }
  .subagent-status.stale { background: #dc2626; box-shadow: 0 0 4px rgba(220,38,38,0.5); }
  .subagent-name { font-weight: 600; color: var(--text-secondary); }
  .subagent-task { color: var(--text-muted); font-size: 9px; }
  .subagent-runtime { color: var(--text-faint); font-size: 9px; margin-left: auto; }

  /* === Sub-Agent Detailed View === */
  .subagent-row { padding: 12px 16px; border-bottom: 1px solid var(--border-secondary); display: flex; align-items: center; gap: 12px; }
  .subagent-row:last-child { border-bottom: none; }
  .subagent-row:hover { background: var(--bg-hover); }
  .subagent-indicator { width: 12px; height: 12px; border-radius: 50%; flex-shrink: 0; }
  .subagent-indicator.active { background: #16a34a; box-shadow: 0 0 8px rgba(22,163,74,0.6); animation: pulse 2s infinite; }
  .subagent-indicator.idle { background: #d97706; box-shadow: 0 0 8px rgba(217,119,6,0.6); }
  .subagent-indicator.stale { background: #dc2626; box-shadow: 0 0 8px rgba(220,38,38,0.6); opacity: 0.7; }
  .subagent-info { flex: 1; }
  .subagent-header { display: flex; justify-content: between; align-items: center; margin-bottom: 4px; }
  .subagent-id { font-weight: 600; font-size: 14px; color: var(--text-primary); }
  .subagent-runtime-badge { background: var(--bg-accent); color: var(--bg-primary); padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: 600; }
  .subagent-meta { font-size: 12px; color: var(--text-muted); display: flex; gap: 16px; flex-wrap: wrap; }
  .subagent-meta span { display: flex; align-items: center; gap: 4px; }
  .subagent-description { font-size: 13px; color: var(--text-secondary); margin-top: 4px; }
  @keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.5; } }

  /* === Active Tasks Cards === */
  .task-card { background: var(--bg-tertiary); border: 1px solid var(--border-primary); border-radius: 12px; padding: 16px; box-shadow: var(--card-shadow); position: relative; overflow: hidden; }
  .task-card.running { border-left: 4px solid #16a34a; }
  .task-card.complete { border-left: 4px solid #2563eb; opacity: 0.7; }
  .task-card.failed { border-left: 4px solid #dc2626; }
  .task-card-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px; }
  .task-card-name { font-weight: 700; font-size: 14px; color: var(--text-primary); line-height: 1.3; }
  .task-card-badge { padding: 2px 10px; border-radius: 12px; font-size: 11px; font-weight: 700; white-space: nowrap; }
  .task-card-badge.running { background: #dcfce7; color: #166534; }
  .task-card-badge.complete { background: #dbeafe; color: #1e40af; }
  .task-card-badge.failed { background: #fef2f2; color: #991b1b; }
  [data-theme="dark"] .task-card-badge.running { background: #14532d; color: #86efac; }
  [data-theme="dark"] .task-card-badge.complete { background: #1e3a5f; color: #93c5fd; }
  [data-theme="dark"] .task-card-badge.failed { background: #450a0a; color: #fca5a5; }
  .task-card-duration { font-size: 12px; color: var(--text-muted); margin-bottom: 6px; }
  .task-card-action { font-size: 12px; color: var(--text-secondary); font-family: 'JetBrains Mono', monospace; background: var(--bg-secondary); padding: 6px 10px; border-radius: 6px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .task-card-pulse { position: absolute; top: 12px; right: 12px; width: 10px; height: 10px; border-radius: 50%; background: #22c55e; }
  .task-card-pulse.active { animation: taskPulse 1.5s ease-in-out infinite; }
  @keyframes taskPulse { 0%,100% { box-shadow: 0 0 0 0 rgba(34,197,94,0.4); } 50% { box-shadow: 0 0 0 8px rgba(34,197,94,0); } }

  /* === Enhanced Active Tasks Panel === */
  .tasks-panel-scroll { max-height: 70vh; overflow-y: auto; overflow-x: hidden; scrollbar-width: thin; scrollbar-color: var(--border-primary) transparent; }
  .tasks-panel-scroll::-webkit-scrollbar { width: 6px; }
  .tasks-panel-scroll::-webkit-scrollbar-track { background: transparent; }
  .tasks-panel-scroll::-webkit-scrollbar-thumb { background: var(--border-primary); border-radius: 3px; }
  .task-group-header { font-size: 13px; font-weight: 700; color: var(--text-secondary); padding: 8px 4px 6px; margin-top: 4px; letter-spacing: 0.3px; }
  .task-group-header:first-child { margin-top: 0; }
  @keyframes idleBreathe { 0%,100% { opacity: 0.5; transform: scale(1); } 50% { opacity: 1; transform: scale(1.05); } }
  .tasks-empty-icon { animation: idleBreathe 3s ease-in-out infinite; display: inline-block; }
  @keyframes statusPulseGreen { 0%,100% { box-shadow: 0 0 0 0 rgba(34,197,94,0.5); } 50% { box-shadow: 0 0 0 6px rgba(34,197,94,0); } }
  .status-dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; flex-shrink: 0; }
  .status-dot.running { background: #22c55e; animation: statusPulseGreen 1.5s ease-in-out infinite; }
  .status-dot.complete { background: #3b82f6; }
  .status-dot.failed { background: #ef4444; }

  /* === Zoom Wrapper === */
  .zoom-wrapper { transform-origin: top left; transition: transform 0.3s ease; }

  /* === Split-Screen Overview === */
  .overview-split { display: grid; grid-template-columns: 60fr 1px 40fr; gap: 0; margin-bottom: 0; height: calc(100vh - 175px); }
  .overview-flow-pane { position: relative; border: 1px solid var(--border-primary); border-radius: 8px 0 0 8px; overflow: hidden; background: var(--bg-secondary); padding: 4px; }
  .overview-flow-pane .flow-container { height: 100%; }
  .overview-flow-pane svg { width: 100%; height: 100%; min-width: 0 !important; }
  .overview-divider { background: var(--border-primary); width: 1px; }
  .overview-tasks-pane { overflow-y: auto; border: 1px solid var(--border-primary); border-left: none; border-radius: 0 8px 8px 0; padding: 10px 12px; }
  /* Scanline overlay */
  .scanline-overlay { pointer-events: none; position: absolute; inset: 0; z-index: 2; background: repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,255,65,0.015) 2px, rgba(0,255,65,0.015) 4px); }
  .grid-overlay { pointer-events: none; position: absolute; inset: 0; z-index: 1; background-image: linear-gradient(var(--border-secondary) 1px, transparent 1px), linear-gradient(90deg, var(--border-secondary) 1px, transparent 1px); background-size: 40px 40px; opacity: 0.3; }
  /* Task cards in overview */
  .ov-task-card { background: var(--bg-tertiary); border: 1px solid var(--border-primary); border-radius: 10px; padding: 14px 16px; margin-bottom: 10px; box-shadow: var(--card-shadow); position: relative; transition: box-shadow 0.2s; }
  .ov-task-card:hover { box-shadow: var(--card-shadow-hover); }
  .ov-task-card.running { border-left: 4px solid #16a34a; }
  .ov-task-card.complete { border-left: 4px solid #2563eb; opacity: 0.75; }
  .ov-task-card.failed { border-left: 4px solid #dc2626; }
  .ov-task-pulse { width: 10px; height: 10px; border-radius: 50%; background: #22c55e; display: inline-block; animation: taskPulse 1.5s ease-in-out infinite; }
  .ov-details { display: none; margin-top: 10px; padding: 10px; background: var(--bg-secondary); border: 1px solid var(--border-secondary); border-radius: 8px; font-family: 'JetBrains Mono', 'SF Mono', monospace; font-size: 11px; line-height: 1.7; color: var(--text-tertiary); }
  .ov-details.open { display: block; }
  .ov-toggle-btn { background: none; border: 1px solid var(--border-primary); border-radius: 6px; padding: 3px 10px; font-size: 11px; color: var(--text-tertiary); cursor: pointer; transition: all 0.15s; }
  .ov-toggle-btn:hover { background: var(--bg-hover); color: var(--text-secondary); }

  /* === Task Detail Modal === */
  .modal-overlay { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.5); z-index: 1000; justify-content: center; align-items: center; }
  .modal-overlay.open { display: flex; }
  .modal-card { background: var(--bg-primary); border: 1px solid var(--border-primary); border-radius: 16px; width: 95%; max-width: 900px; max-height: 80vh; display: flex; flex-direction: column; box-shadow: 0 25px 50px rgba(0,0,0,0.25); }
  .modal-header { display: flex; align-items: center; justify-content: space-between; padding: 16px 20px; border-bottom: 1px solid var(--border-primary); flex-shrink: 0; }
  .modal-header-left { flex: 1; min-width: 0; }
  .modal-title { font-size: 16px; font-weight: 700; color: var(--text-primary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .modal-session-key { font-size: 11px; color: var(--text-muted); font-family: monospace; margin-top: 2px; }
  .modal-header-right { display: flex; align-items: center; gap: 10px; flex-shrink: 0; }
  .modal-auto-refresh { display: flex; align-items: center; gap: 6px; font-size: 12px; color: var(--text-tertiary); cursor: pointer; }
  .modal-auto-refresh input { cursor: pointer; }
  .modal-close { background: var(--button-bg); border: 1px solid var(--border-primary); border-radius: 8px; width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; cursor: pointer; font-size: 18px; color: var(--text-tertiary); transition: all 0.15s; }
  .modal-close:hover { background: var(--bg-error); color: var(--text-error); }
  .modal-tabs { display: flex; gap: 0; border-bottom: 1px solid var(--border-primary); padding: 0 20px; flex-shrink: 0; }
  .modal-tab { padding: 10px 18px; font-size: 13px; font-weight: 600; color: var(--text-muted); cursor: pointer; border-bottom: 2px solid transparent; transition: all 0.15s; }
  .modal-tab:hover { color: var(--text-secondary); }
  .modal-tab.active { color: var(--text-accent); border-bottom-color: var(--text-accent); }
  .modal-content { flex: 1; overflow-y: auto; padding: 20px; -webkit-overflow-scrolling: touch; }
  .modal-footer { border-top: 1px solid var(--border-primary); padding: 10px 20px; display: flex; gap: 16px; font-size: 12px; color: var(--text-muted); flex-shrink: 0; }
  /* Modal event items */
  .evt-item { border: 1px solid var(--border-secondary); border-radius: 8px; margin-bottom: 8px; overflow: hidden; }
  .evt-header { display: flex; align-items: center; gap: 8px; padding: 10px 14px; cursor: pointer; transition: background 0.15s; }
  .evt-header:hover { background: var(--bg-hover); }
  .evt-icon { font-size: 16px; flex-shrink: 0; }
  .evt-summary { flex: 1; font-size: 13px; color: var(--text-secondary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .evt-summary strong { color: var(--text-primary); }
  .evt-ts { font-size: 11px; color: var(--text-muted); flex-shrink: 0; font-family: monospace; }
  .evt-body { display: none; padding: 0 14px 12px; font-family: 'JetBrains Mono', 'SF Mono', monospace; font-size: 12px; line-height: 1.6; color: var(--text-tertiary); white-space: pre-wrap; word-break: break-word; max-height: 400px; overflow-y: auto; }
  .evt-body.open { display: block; }
  .evt-item.type-agent { border-left: 3px solid #3b82f6; }
  .evt-item.type-exec { border-left: 3px solid #16a34a; }
  .evt-item.type-read { border-left: 3px solid #8b5cf6; }
  .evt-item.type-result { border-left: 3px solid #ea580c; }
  .evt-item.type-thinking { border-left: 3px solid #6b7280; }
  .evt-item.type-user { border-left: 3px solid #7c3aed; }
  /* === Component Detail Modal === */
  .comp-modal-overlay { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.5); z-index: 1100; justify-content: center; align-items: center; }
  .comp-modal-overlay.open { display: flex; }
  .comp-modal-card { background: var(--bg-primary); border: 1px solid var(--border-primary); border-radius: 16px; width: 90%; max-width: 560px; display: flex; flex-direction: column; box-shadow: 0 25px 50px rgba(0,0,0,0.25); max-height: 90vh; }
  .comp-modal-header { display: flex; align-items: center; justify-content: space-between; padding: 16px 20px; border-bottom: 1px solid var(--border-primary); }
  .comp-modal-title { font-size: 18px; font-weight: 700; color: var(--text-primary); }
  .comp-modal-close { background: var(--button-bg); border: 1px solid var(--border-primary); border-radius: 8px; width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; cursor: pointer; font-size: 18px; color: var(--text-tertiary); transition: all 0.15s; }
  .comp-modal-close:hover { background: var(--bg-error); color: var(--text-error); }
  
  /* Time Travel Controls */
  .time-travel-bar { display: none; padding: 12px 20px; border-bottom: 1px solid var(--border-primary); background: var(--bg-secondary); }
  .time-travel-bar.active { display: block; }
  .time-travel-controls { display: flex; align-items: center; gap: 12px; }
  .time-travel-toggle { background: var(--button-bg); border: 1px solid var(--border-primary); border-radius: 6px; padding: 4px 8px; color: var(--text-tertiary); cursor: pointer; font-size: 12px; transition: all 0.15s; }
  .time-travel-toggle:hover { background: var(--button-hover); }
  .time-travel-toggle.active { background: var(--bg-accent); color: white; }
  .time-scrubber { flex: 1; display: flex; align-items: center; gap: 8px; }
  .time-slider { flex: 1; height: 4px; background: var(--border-primary); border-radius: 2px; cursor: pointer; position: relative; }
  .time-slider-thumb { width: 16px; height: 16px; background: var(--bg-accent); border-radius: 50%; position: absolute; top: -6px; margin-left: -8px; box-shadow: var(--card-shadow); transition: all 0.15s; }
  .time-slider-thumb:hover { transform: scale(1.2); }
  .time-display { font-size: 12px; color: var(--text-secondary); font-weight: 600; min-width: 120px; }
  .time-nav-btn { background: var(--button-bg); border: 1px solid var(--border-primary); border-radius: 4px; width: 24px; height: 24px; display: flex; align-items: center; justify-content: center; cursor: pointer; font-size: 12px; color: var(--text-tertiary); }
  .time-nav-btn:hover { background: var(--button-hover); }
  .time-nav-btn:disabled { opacity: 0.5; cursor: not-allowed; }
  .comp-modal-body { padding: 24px 20px; font-size: 14px; color: var(--text-secondary); line-height: 1.6; max-height: 70vh; overflow-y: auto; }

  /* Telegram Chat Bubbles */
  .tg-stats { display: flex; gap: 16px; padding: 10px 14px; background: var(--bg-secondary); border-radius: 8px; margin-bottom: 12px; font-size: 13px; font-weight: 600; }
  .tg-stats .in { color: #3b82f6; } .tg-stats .out { color: #22c55e; }
  .tg-chat { display: flex; flex-direction: column; gap: 8px; }
  .tg-bubble { max-width: 85%; padding: 10px 14px; border-radius: 16px; font-size: 13px; line-height: 1.5; word-wrap: break-word; position: relative; }
  .tg-bubble.in { background: #1e3a5f; border: 1px solid #2a5a8a; color: #c0d8ff; align-self: flex-start; border-bottom-left-radius: 4px; }
  .tg-bubble.out { background: #1a3a2a; border: 1px solid #2a5a3a; color: #c0ffc0; align-self: flex-end; border-bottom-right-radius: 4px; }
  [data-theme="light"] .tg-bubble.in { background: #dbeafe; border-color: #93c5fd; color: #1e3a5f; }
  [data-theme="light"] .tg-bubble.out { background: #dcfce7; border-color: #86efac; color: #14532d; }
  .tg-bubble .tg-sender { font-size: 11px; font-weight: 700; margin-bottom: 2px; opacity: 0.7; }
  .tg-bubble .tg-time { font-size: 10px; color: var(--text-muted); margin-top: 4px; text-align: right; }
  .tg-bubble .tg-text { white-space: pre-wrap; }
  .tg-load-more { text-align: center; padding: 10px; }
  /* iMessage styles */
  .imsg-stats { display: flex; gap: 16px; padding: 10px 14px; background: var(--bg-secondary); border-radius: 8px; margin-bottom: 12px; font-size: 13px; font-weight: 600; }
  .imsg-stats .in { color: #007AFF; } .imsg-stats .out { color: #34C759; }
  .imsg-chat { display: flex; flex-direction: column; gap: 8px; }
  .imsg-bubble { max-width: 85%; padding: 10px 14px; border-radius: 18px; font-size: 13px; line-height: 1.5; word-wrap: break-word; position: relative; }
  .imsg-bubble.in { background: #1e2a3f; border: 1px solid #2a4a7a; color: #b0d0ff; align-self: flex-start; border-bottom-left-radius: 4px; }
  .imsg-bubble.out { background: #1a3a2a; border: 1px solid #2a6a3a; color: #b0ffb0; align-self: flex-end; border-bottom-right-radius: 4px; }
  [data-theme="light"] .imsg-bubble.in { background: #e1e8f5; border-color: #93c5fd; color: #1e3a5f; }
  [data-theme="light"] .imsg-bubble.out { background: #d4f5d4; border-color: #86efac; color: #14532d; }
  .imsg-bubble .imsg-sender { font-size: 11px; font-weight: 700; margin-bottom: 2px; opacity: 0.7; }
  .imsg-bubble .imsg-time { font-size: 10px; color: var(--text-muted); margin-top: 4px; text-align: right; }
  .imsg-bubble .imsg-text { white-space: pre-wrap; }
  /* WebChat styles - neutral/white browser-style bubbles */
  .wc-stats { display: flex; align-items: center; gap: 12px; padding: 10px 14px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; margin-bottom: 12px; font-size: 13px; font-weight: 600; }
  [data-theme="dark"] .wc-stats { background: #1e2533; border-color: #2d3748; }
  .wc-stat-item { color: #374151; }
  [data-theme="dark"] .wc-stat-item { color: #9ca3af; }
  .wc-messages { display: flex; flex-direction: column; gap: 6px; padding: 4px 0; }
  .wc-msg-row { display: flex; }
  .wc-msg-row.wc-row-out { justify-content: flex-end; }
  .wc-bubble { max-width: 80%; padding: 9px 13px; border-radius: 16px; font-size: 13px; line-height: 1.5; word-wrap: break-word; box-shadow: 0 1px 2px rgba(0,0,0,0.08); }
  .wc-bubble.wc-msg-in { background: #f1f5f9; color: #1e293b; border-bottom-left-radius: 4px; border: 1px solid #e2e8f0; }
  .wc-bubble.wc-msg-out { background: #0ea5e9; color: #fff; border-bottom-right-radius: 4px; }
  [data-theme="dark"] .wc-bubble.wc-msg-in { background: #1e2a3f; color: #cbd5e1; border-color: #2d3748; }
  [data-theme="dark"] .wc-bubble.wc-msg-out { background: #0369a1; color: #e0f2fe; }
  .wc-bubble-text { white-space: pre-wrap; }
  .wc-bubble-time { font-size: 10px; margin-top: 3px; text-align: right; opacity: 0.65; }
  /* IRC styles - dark terminal theme */
  .irc-loading { background: #1a1a2e; color: #9ca3af; font-family: 'Courier New', monospace; padding: 40px; text-align: center; font-size: 13px; }
  .irc-header { display: flex; align-items: center; gap: 10px; padding: 8px 12px; background: #0f0f1a; border-bottom: 1px solid #2d2d4a; font-family: 'Courier New', monospace; font-size: 12px; flex-wrap: wrap; }
  .irc-stat { color: #6b7280; }
  .irc-channels { color: #60a5fa; font-weight: 700; }
  .irc-nick { color: #a78bfa; margin-left: auto; }
  .irc-log { background: #0d0d1a; padding: 10px 12px; display: flex; flex-direction: column; gap: 2px; font-family: 'Courier New', monospace; font-size: 12px; overflow-y: auto; max-height: 500px; }
  .irc-line { line-height: 1.6; word-wrap: break-word; }
  .irc-ts { color: #4b5563; }
  .irc-nick-tag { color: #60a5fa; font-weight: 600; }
  .irc-text { color: #d1d5db; }
  /* BlueBubbles styles - Apple green */
  .bb-stats { display: flex; align-items: center; gap: 12px; padding: 10px 14px; background: #0a1f0a; border: 1px solid #166534; border-radius: 8px; margin-bottom: 12px; font-size: 13px; font-weight: 600; }
  [data-theme="light"] .bb-stats { background: #f0fdf4; border-color: #bbf7d0; }
  .bb-stat-item { color: #4ade80; }
  [data-theme="light"] .bb-stat-item { color: #166534; }
  .bb-messages { display: flex; flex-direction: column; gap: 6px; padding: 4px 0; }
  .bb-msg-row { display: flex; }
  .bb-msg-row.bb-row-out { justify-content: flex-end; }
  .bb-bubble { max-width: 80%; padding: 9px 13px; border-radius: 18px; font-size: 13px; line-height: 1.5; word-wrap: break-word; }
  .bb-bubble.bb-msg-in { background: #1a2a1a; color: #86efac; border-bottom-left-radius: 4px; border: 1px solid #166534; }
  .bb-bubble.bb-msg-out { background: #34C759; color: #fff; border-bottom-right-radius: 4px; }
  [data-theme="light"] .bb-bubble.bb-msg-in { background: #dcfce7; color: #14532d; border-color: #86efac; }
  [data-theme="light"] .bb-bubble.bb-msg-out { background: #34C759; color: #fff; }
  .bb-bubble-text { white-space: pre-wrap; }
  .bb-bubble-time { font-size: 10px; margin-top: 3px; text-align: right; opacity: 0.65; }
  /* Google Chat styles */
  .gc-stats { display: flex; gap: 16px; padding: 10px 14px; background: var(--bg-secondary); border-radius: 8px; margin-bottom: 12px; font-size: 13px; font-weight: 600; }
  .gc-stats .in { color: #1a73e8; } .gc-stats .out { color: #34a853; }
  .gc-chat { display: flex; flex-direction: column; gap: 8px; }
  .gc-bubble { max-width: 85%; padding: 10px 14px; border-radius: 8px; font-size: 13px; line-height: 1.5; word-wrap: break-word; position: relative; }
  .gc-bubble.in { background: #1a2a4a; border: 1px solid #1a73e8; color: #c0d8ff; align-self: flex-start; border-bottom-left-radius: 2px; }
  .gc-bubble.out { background: #1a3a2a; border: 1px solid #34a853; color: #c0ffc0; align-self: flex-end; border-bottom-right-radius: 2px; }
  [data-theme="light"] .gc-bubble.in { background: #e8f0fe; border-color: #1a73e8; color: #1a237e; }
  [data-theme="light"] .gc-bubble.out { background: #e6f4ea; border-color: #34a853; color: #1b5e20; }
  .gc-bubble .gc-sender { font-size: 11px; font-weight: 700; margin-bottom: 2px; color: #1a73e8; }
  .gc-bubble .gc-time { font-size: 10px; color: var(--text-muted); margin-top: 4px; text-align: right; }
  .gc-bubble .gc-text { white-space: pre-wrap; }
  /* MS Teams styles */
  .mst-stats { display: flex; gap: 16px; padding: 10px 14px; background: var(--bg-secondary); border-radius: 8px; margin-bottom: 12px; font-size: 13px; font-weight: 600; }
  .mst-stats .in { color: #6264A7; } .mst-stats .out { color: #33b55b; }
  .mst-chat { display: flex; flex-direction: column; gap: 8px; }
  .mst-bubble { max-width: 85%; padding: 10px 14px; border-radius: 6px; font-size: 13px; line-height: 1.5; word-wrap: break-word; position: relative; }
  .mst-bubble.in { background: #1e1e3a; border: 1px solid #6264A7; color: #c8c8ff; align-self: flex-start; border-bottom-left-radius: 2px; }
  .mst-bubble.out { background: #1a3a2a; border: 1px solid #33b55b; color: #c0ffc0; align-self: flex-end; border-bottom-right-radius: 2px; }
  [data-theme="light"] .mst-bubble.in { background: #f0f0ff; border-color: #6264A7; color: #2d2d7a; }
  [data-theme="light"] .mst-bubble.out { background: #e6f4ea; border-color: #33b55b; color: #1b5e20; }
  .mst-bubble .mst-sender { font-size: 11px; font-weight: 700; margin-bottom: 2px; color: #6264A7; }
  .mst-bubble .mst-time { font-size: 10px; color: var(--text-muted); margin-top: 4px; text-align: right; }
  .mst-bubble .mst-text { white-space: pre-wrap; }
  /* Mattermost styles */
  .mm-stats { display: flex; gap: 16px; padding: 10px 14px; background: var(--bg-secondary); border-radius: 8px; margin-bottom: 12px; font-size: 13px; font-weight: 600; }
  .mm-stats .in { color: #0058CC; } .mm-stats .out { color: #3db887; }
  .mm-chat { display: flex; flex-direction: column; gap: 8px; }
  .mm-bubble { max-width: 85%; padding: 10px 14px; border-radius: 4px; font-size: 13px; line-height: 1.5; word-wrap: break-word; position: relative; }
  .mm-bubble.in { background: #0a1a3a; border-left: 3px solid #0058CC; color: #b0ccff; align-self: flex-start; }
  .mm-bubble.out { background: #0a2a1a; border-left: 3px solid #3db887; color: #b0ffe0; align-self: flex-end; }
  [data-theme="light"] .mm-bubble.in { background: #e8f0ff; border-color: #0058CC; color: #003399; }
  [data-theme="light"] .mm-bubble.out { background: #e6faf3; border-color: #3db887; color: #005a3c; }
  .mm-bubble .mm-sender { font-size: 11px; font-weight: 700; margin-bottom: 2px; color: #0058CC; }
  .mm-bubble .mm-time { font-size: 10px; color: var(--text-muted); margin-top: 4px; text-align: right; }
  .mm-bubble .mm-text { white-space: pre-wrap; }

  /* === WhatsApp Channel === */
  .wa-stats { display: flex; gap: 16px; padding: 10px 14px; background: var(--bg-secondary); border-radius: 8px; margin-bottom: 12px; font-size: 13px; font-weight: 600; }
  .wa-stats .in { color: #25D366; } .wa-stats .out { color: #128C7E; }
  .wa-chat { display: flex; flex-direction: column; gap: 8px; }
  .wa-bubble { max-width: 85%; padding: 10px 14px; border-radius: 12px; font-size: 13px; line-height: 1.5; word-wrap: break-word; position: relative; }
  .wa-bubble.in { background: #1a2f1a; border: 1px solid #25D366; color: #b0ffc0; align-self: flex-start; border-bottom-left-radius: 4px; }
  .wa-bubble.out { background: #0d2b1f; border: 1px solid #128C7E; color: #90e8d0; align-self: flex-end; border-bottom-right-radius: 4px; }
  [data-theme="light"] .wa-bubble.in { background: #dcfce7; border-color: #25D366; color: #14532d; }
  [data-theme="light"] .wa-bubble.out { background: #d1faf0; border-color: #128C7E; color: #0d4a36; }
  .wa-bubble .wa-sender { font-size: 11px; font-weight: 700; margin-bottom: 2px; opacity: 0.7; }
  .wa-bubble .wa-time { font-size: 10px; color: var(--text-muted); margin-top: 4px; text-align: right; }
  .wa-bubble .wa-text { white-space: pre-wrap; }

  /* === Signal Channel === */
  .sig-stats { display: flex; gap: 16px; padding: 10px 14px; background: var(--bg-secondary); border-radius: 8px; margin-bottom: 12px; font-size: 13px; font-weight: 600; }
  .sig-stats .in { color: #3A76F0; } .sig-stats .out { color: #5b4fe8; }
  .sig-chat { display: flex; flex-direction: column; gap: 8px; }
  .sig-bubble { max-width: 85%; padding: 10px 14px; border-radius: 18px; font-size: 13px; line-height: 1.5; word-wrap: break-word; position: relative; }
  .sig-bubble.in { background: #1a2040; border: 1px solid #3A76F0; color: #b0ccff; align-self: flex-start; border-bottom-left-radius: 4px; }
  .sig-bubble.out { background: #1e1a40; border: 1px solid #5b4fe8; color: #d0c8ff; align-self: flex-end; border-bottom-right-radius: 4px; }
  [data-theme="light"] .sig-bubble.in { background: #dbeafe; border-color: #3A76F0; color: #1e3a5f; }
  [data-theme="light"] .sig-bubble.out { background: #ede9fe; border-color: #5b4fe8; color: #3b0764; }
  .sig-bubble .sig-sender { font-size: 11px; font-weight: 700; margin-bottom: 2px; opacity: 0.7; }
  .sig-bubble .sig-time { font-size: 10px; color: var(--text-muted); margin-top: 4px; text-align: right; }
  .sig-bubble .sig-text { white-space: pre-wrap; }

  /* === Discord Channel === */
  .discord-stats { display: flex; gap: 16px; padding: 10px 14px; background: #2f3136; border-radius: 8px; margin-bottom: 12px; font-size: 13px; font-weight: 600; }
  .discord-stats .in { color: #5865F2; } .discord-stats .out { color: #57F287; }
  .discord-server-info { display: flex; align-items: center; gap: 8px; padding: 6px 10px; background: #36393f; border-radius: 6px; margin-bottom: 10px; font-size: 12px; color: #b9bbbe; }
  .discord-server-info .guild-name { color: #5865F2; font-weight: 700; } .discord-server-info .ch-name { color: #8a8f95; }
  .discord-chat { display: flex; flex-direction: column; gap: 8px; }
  .discord-bubble { max-width: 85%; padding: 10px 14px; border-radius: 8px; font-size: 13px; line-height: 1.5; word-wrap: break-word; position: relative; }
  .discord-bubble.in { background: #36393f; border: 1px solid #5865F2; color: #dcddde; align-self: flex-start; border-bottom-left-radius: 2px; }
  .discord-bubble.out { background: #2f3136; border: 1px solid #57F287; color: #c0ffc0; align-self: flex-end; border-bottom-right-radius: 2px; }
  [data-theme="light"] .discord-bubble.in { background: #eef0ff; border-color: #5865F2; color: #2c2f33; }
  [data-theme="light"] .discord-bubble.out { background: #f0fff4; border-color: #3ba55d; color: #1a3a24; }
  .discord-bubble .discord-sender { font-size: 11px; font-weight: 700; margin-bottom: 2px; color: #5865F2; }
  .discord-bubble.out .discord-sender { color: #57F287; }
  .discord-bubble .discord-time { font-size: 10px; color: var(--text-muted); margin-top: 4px; text-align: right; }
  .discord-bubble .discord-text { white-space: pre-wrap; }

  /* === Slack Channel === */
  .slack-stats { display: flex; gap: 16px; padding: 10px 14px; background: var(--bg-secondary); border-radius: 8px; margin-bottom: 12px; font-size: 13px; font-weight: 600; }
  .slack-stats .in { color: #E01E5A; } .slack-stats .out { color: #2EB67D; }
  .slack-workspace-info { display: flex; align-items: center; gap: 8px; padding: 6px 10px; background: #4A154B; border-radius: 6px; margin-bottom: 10px; font-size: 12px; color: #cfc3cf; }
  .slack-workspace-info .ws-name { color: #ECB22E; font-weight: 700; } .slack-workspace-info .ch-name { color: #36C5F0; }
  .slack-chat { display: flex; flex-direction: column; gap: 8px; }
  .slack-bubble { max-width: 85%; padding: 10px 14px; border-radius: 6px; font-size: 13px; line-height: 1.5; word-wrap: break-word; position: relative; }
  .slack-bubble.in { background: #1a1a2e; border: 1px solid #E01E5A; color: #f0c0d0; align-self: flex-start; border-bottom-left-radius: 2px; }
  .slack-bubble.out { background: #0d1f18; border: 1px solid #2EB67D; color: #b0f0d8; align-self: flex-end; border-bottom-right-radius: 2px; }
  [data-theme="light"] .slack-bubble.in { background: #fce8f0; border-color: #E01E5A; color: #4A154B; }
  [data-theme="light"] .slack-bubble.out { background: #e8f8f0; border-color: #2EB67D; color: #0a3a25; }
  .slack-bubble .slack-sender { font-size: 11px; font-weight: 700; margin-bottom: 2px; color: #E01E5A; }
  .slack-bubble.out .slack-sender { color: #2EB67D; }
  .slack-bubble .slack-time { font-size: 10px; color: var(--text-muted); margin-top: 4px; text-align: right; }
  .slack-bubble .slack-text { white-space: pre-wrap; }

  .tg-load-more button { background: var(--button-bg); border: 1px solid var(--border-primary); border-radius: 8px; padding: 6px 20px; color: var(--text-secondary); cursor: pointer; font-size: 13px; }
  .tg-load-more button:hover { background: var(--button-hover); }
  .comp-modal-footer { border-top: 1px solid var(--border-primary); padding: 10px 20px; font-size: 11px; color: var(--text-muted); }
  /* === Compact Stats Footer Bar === */
  .stats-footer { display: flex; gap: 0; border: 1px solid var(--border-primary); border-radius: 8px; margin-bottom: 6px; background: var(--bg-tertiary); overflow: hidden; }
  .stats-footer-item { flex: 1; padding: 6px 12px; display: flex; align-items: center; gap: 8px; border-right: 1px solid var(--border-primary); cursor: pointer; transition: background 0.15s; }
  .stats-footer-item:last-child { border-right: none; }
  .stats-footer-item:hover { background: var(--bg-hover); }
  .stats-footer-icon { font-size: 14px; }
  .stats-footer-label { font-size: 10px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px; }
  .tooltip-info-icon {
    display:inline-flex;
    align-items:center;
    justify-content:center;
    width:14px;
    height:14px;
    margin-left:6px;
    border-radius:999px;
    border:1px solid var(--border-primary);
    color:var(--text-muted);
    font-size:10px;
    font-weight:700;
    line-height:1;
    cursor:help;
    opacity:0.9;
    vertical-align:middle;
  }
  .tooltip-info-icon:hover { color: var(--text-primary); border-color: var(--text-accent); }
  .stats-footer-value { font-size: 14px; font-weight: 700; color: var(--text-primary); }
  .stats-footer-sub { font-size: 10px; color: var(--text-faint); }
  @media (max-width: 1024px) {
    .stats-footer { flex-wrap: wrap; }
    .stats-footer-item { flex: 1 1 45%; min-width: 0; }
  }

  /* Narrative view */
  .narrative-item { padding: 10px 0; border-bottom: 1px solid var(--border-secondary); font-size: 13px; line-height: 1.6; color: var(--text-secondary); }
  .narrative-item:last-child { border-bottom: none; }
  .narrative-item .narr-icon { margin-right: 8px; }
  .narrative-item code { background: var(--bg-secondary); padding: 1px 6px; border-radius: 4px; font-family: 'JetBrains Mono', monospace; font-size: 12px; }
  /* Summary view */
  .summary-section { margin-bottom: 16px; }
  .summary-label { font-size: 11px; text-transform: uppercase; letter-spacing: 1px; color: var(--text-muted); margin-bottom: 6px; }
  .summary-text { font-size: 14px; color: var(--text-secondary); line-height: 1.6; white-space: pre-wrap; }

  @media (max-width: 1024px) {
    .overview-split { grid-template-columns: 1fr; height: auto; }
    .overview-flow-pane { height: 40vh; min-height: 250px; border-radius: 8px 8px 0 0; }
    .overview-divider { width: auto; height: 1px; }
    .overview-tasks-pane { height: 60vh; border-radius: 0 0 8px 8px; border-left: 1px solid var(--border-primary); border-top: none; }
  }

  @media (max-width: 768px) {
    .nav { padding: 10px 12px; gap: 8px; }
    .nav h1 { font-size: 16px; }
    .nav-tab { padding: 6px 12px; font-size: 12px; }
    .page { padding: 12px; }
    #page-flow { padding: 0; }
    .grid { grid-template-columns: 1fr; gap: 12px; }
    .card-value { font-size: 22px; }
    .flow-stats { gap: 8px; }
    .flow-stat { min-width: 70px; padding: 6px 10px; }
    .flow-stat-value { font-size: 16px; }
    #flow-svg { min-width: 0; }
    .heatmap-grid { min-width: 500px; }
    .chat-msg { max-width: 95%; }
    .usage-chart { height: 150px; }
    
    /* Enhanced Flow mobile optimizations */
    .flow-container { 
      padding-bottom: 20px; 
      overflow: visible; 
    }
    #flow-svg text { font-size: 11px !important; }
    .flow-label { font-size: 7px !important; }
    .flow-node rect { stroke-width: 1 !important; }
    .flow-node.active rect { stroke-width: 1.5 !important; }
    .brain-group { animation-duration: 1.8s; } /* Faster on mobile */
    
    /* Mobile zoom controls */
    .zoom-controls { margin-left: 8px; gap: 2px; }
    .zoom-btn { width: 24px; height: 24px; font-size: 14px; }
    .zoom-level { min-width: 32px; font-size: 10px; }

    /* Nav: logo+icons row, tabs scroll row below */
    .nav { flex-wrap: wrap; padding: 6px 10px; gap: 6px; }
    .nav h1 { order: 1; font-size: 15px; }
    .theme-toggle { order: 2; }
    .zoom-controls { order: 3; margin-left: auto; }
    .nav-tabs {
      order: 4; width: 100%; margin-left: 0;
      overflow-x: auto; flex-wrap: nowrap;
      padding-bottom: 2px; gap: 2px;
      scrollbar-width: none;
    }
    .nav-tabs::-webkit-scrollbar { display: none; }
    .nav-tab { padding: 5px 10px; font-size: 11px; white-space: nowrap; }

    /* Brain event stream: stack rows on mobile */
    .brain-event { flex-direction: column; gap: 2px; padding: 6px 0; align-items: flex-start; }
    .brain-meta { display: flex !important; align-items: center; gap: 5px; flex-shrink: 0; width: 100%; }
    .brain-time { min-width: unset; font-size: 10px; flex-shrink: 0; }
    .brain-source { min-width: unset; max-width: 140px; font-size: 10px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .brain-type { min-width: 42px; font-size: 9px; padding: 1px 3px; flex-shrink: 0; }
    .brain-detail { font-size: 11px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; width: 100%; white-space: normal; }
    .brain-event.expanded .brain-detail { -webkit-line-clamp: unset; overflow: visible; }

    /* Filter chips: single scrollable row, no wrap */
    #brain-filter-chips { flex-wrap: nowrap !important; overflow-x: auto; scrollbar-width: none; padding-bottom: 2px; }
    #brain-filter-chips::-webkit-scrollbar { display: none; }
    #brain-type-chips { flex-wrap: nowrap !important; overflow-x: auto; scrollbar-width: none; padding-bottom: 2px; }
    #brain-type-chips::-webkit-scrollbar { display: none; }

    /* Cards */
    .card { padding: 12px 14px; }
    .card-label { font-size: 10px; }
    .card-value { font-size: 20px; }
    
    /* Overview grid already 1-col, just tighten gap */
    .grid { gap: 8px; }

    /* Memory / cron tables */
    .mem-file-row { flex-direction: column; gap: 4px; }
    .cron-job { flex-wrap: wrap; gap: 6px; }
  }
</style>

<script>
window.toggleAdvancedTabs = function(e) {
  e.stopPropagation();
  var dd = e.target.closest('.nav-tab-more').querySelector('.advanced-tabs-dropdown');
  if (!dd) return;
  var vis = dd.style.display === 'none' || !dd.style.display;
  document.querySelectorAll('.advanced-tabs-dropdown').forEach(function(d){ d.style.display = 'none'; });
  if (vis) dd.style.display = 'block';
};
window.hideAdvDropdown = function() {
  document.querySelectorAll('.advanced-tabs-dropdown').forEach(function(d){ d.style.display = 'none'; });
};
document.addEventListener('click', function(e) {
  if (!e.target.closest('.nav-tab-more') && !e.target.closest('.advanced-tabs-dropdown')) {
    hideAdvDropdown();
  }
});
</script>

<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chartjs-adapter-date-fns@3.0.0/dist/chartjs-adapter-date-fns.bundle.min.js"></script>
</head>
<body data-theme="dark" class="booting">
<!-- Login overlay -->
<div id="login-overlay" style="display:none;position:fixed;inset:0;z-index:99999;background:var(--bg-primary,#0f172a);align-items:center;justify-content:center;flex-direction:column;">
  <div style="background:var(--card-bg,#1e293b);border-radius:16px;padding:40px;max-width:400px;width:90%;box-shadow:0 8px 32px rgba(0,0,0,0.4);text-align:center;">
    <img src="/static/img/logo.svg" style="width:64px;height:64px;margin-bottom:16px;display:block;margin-left:auto;margin-right:auto;" alt="ClawMetry">
    <h2 style="color:#e2e8f0;margin:0 0 8px;">ClawMetry</h2>
    <p style="color:#94a3b8;margin:0 0 24px;font-size:14px;">Enter your OpenClaw Gateway Token</p>
    <input id="login-token" type="password" placeholder="Gateway token..." style="width:100%;box-sizing:border-box;padding:12px 16px;border-radius:8px;border:1px solid #334155;background:#0f172a;color:#e2e8f0;font-size:15px;margin-bottom:16px;outline:none;" onkeydown="if(event.key==='Enter')clawmetryLogin()">
    <button onclick="clawmetryLogin()" style="width:100%;padding:12px;border-radius:8px;border:none;background:#3b82f6;color:#fff;font-size:15px;font-weight:600;cursor:pointer;">Login</button>
    <p id="login-error" style="color:#f87171;margin:12px 0 0;font-size:13px;display:none;">Invalid token</p>
  </div>
</div>
<script>
(function(){
  var stored = localStorage.getItem('clawmetry-token');
  fetch('/api/auth/check' + (stored ? '?token=' + encodeURIComponent(stored) : ''))
    .then(function(r){return r.json()})
    .then(function(d){
      if(d.needsSetup){
        // No gateway token configured -- show mandatory gateway setup wizard
        document.getElementById('login-overlay').style.display='none';
        var overlay=document.getElementById('gw-setup-overlay');
        overlay.dataset.mandatory='true';
        document.getElementById('gw-setup-close').style.display='none';
        overlay.style.display='flex';
        return;
      }
      if(!d.authRequired){
        document.getElementById('login-overlay').style.display='none';
        return;
      }
      if(d.valid){
        document.getElementById('login-overlay').style.display='none';
        var lb=document.getElementById('logout-btn');if(lb)lb.style.display='';
        return;
      }
      localStorage.removeItem('cm-token');localStorage.removeItem('clawmetry-token');sessionStorage.removeItem('cm-token');document.getElementById('login-overlay').style.display='flex';
    })
    .catch(function(){document.getElementById('login-overlay').style.display='none';});
})();
function clawmetryLogin(){
  var tok=document.getElementById('login-token').value.trim();
  if(!tok)return;
  fetch('/api/auth/check?token='+encodeURIComponent(tok))
    .then(function(r){return r.json()})
    .then(function(d){
      if(d.valid){
        localStorage.setItem('clawmetry-token',tok);
        document.getElementById('login-overlay').style.display='none';
        var lb=document.getElementById('logout-btn');if(lb)lb.style.display='';
        location.reload();
      } else {
        document.getElementById('login-error').style.display='block';
      }
    });
}
function clawmetryLogout(){
  localStorage.removeItem('clawmetry-token');
  location.reload();
}
// Inject auth header into all fetch calls
(function(){
  var _origFetch=window.fetch;
  window.fetch=function(url,opts){
    var tok=localStorage.getItem('clawmetry-token');
    if(tok && typeof url==='string' && url.startsWith('/api/')){
      opts=opts||{};
      opts.headers=opts.headers||{};
      if(opts.headers instanceof Headers){opts.headers.set('Authorization','Bearer '+tok);}
      else{opts.headers['Authorization']='Bearer '+tok;}
    }
    return _origFetch.call(this,url,opts);
  };
})();

// ── Version badge + one-click update ──
(function(){
  function checkVersion(){
    fetch('/api/version').then(function(r){return r.json();}).then(function(d){
      var badges=document.querySelectorAll('.version-badge');
      badges.forEach(function(badge){
        if(d.update_available){
          badge.textContent='v'+d.current+' -> v'+d.latest+' \u2B06';
          badge.className='version-badge update-available';
          badge.title='Click to update ClawMetry to v'+d.latest;
          badge.onclick=function(){triggerUpdate(d.latest,badges);};
        }else{
          badge.textContent='v'+d.current;
        }
      });
    }).catch(function(){});
  }
  function triggerUpdate(latest,badges){
    if(!confirm('Update ClawMetry to v'+latest+'? Dashboard will restart.'))return;
    badges.forEach(function(b){b.textContent='Updating...';b.className='version-badge updating';b.onclick=null;});
    fetch('/api/update',{method:'POST'}).then(function(r){return r.json();}).then(function(d){
      if(d.ok){
        badges.forEach(function(b){b.textContent='Restarting...';});
        setTimeout(function(){window.location.reload();},5000);
      }else{
        badges.forEach(function(b){b.textContent='Update failed';b.className='version-badge';});
      }
    }).catch(function(){
      badges.forEach(function(b){b.textContent='Update failed';b.className='version-badge';});
    });
  }
  checkVersion();
})();
</script>
<div class="boot-overlay" id="boot-overlay">
  <div class="boot-card">
    <div class="boot-spinner"></div>
    <div class="boot-title">Initializing ClawMetry</div>
    <div class="boot-sub" id="boot-sub">Loading model, tasks, system health, and live streams…</div>
    <div class="boot-steps">
      <div class="boot-step loading" id="boot-step-overview"><span class="boot-dot"></span><span>Loading overview + model context</span></div>
      <div class="boot-step" id="boot-step-tasks"><span class="boot-dot"></span><span>Loading active tasks</span></div>
      <div class="boot-step" id="boot-step-health"><span class="boot-dot"></span><span>Loading system health</span></div>
      <div class="boot-step" id="boot-step-streams"><span class="boot-dot"></span><span>Connecting live streams</span></div>
    </div>
  </div>
</div>
<div class="zoom-wrapper" id="zoom-wrapper">
<div class="nav">
  <h1><a href="https://clawmetry.com" style="display:flex;align-items:center;gap:7px;text-decoration:none;color:inherit"><img src="/static/img/logo.svg" width="22" height="22" style="border-radius:4px;vertical-align:middle;flex-shrink:0" alt="ClawMetry"><span><span style="color:#ffffff">Claw</span><span style="color:#E5443A">Metry</span></span></a></h1>
  <span id="version-badge" class="version-badge" title="ClawMetry version">v{{ version }}</span>
  <div class="theme-toggle" onclick="var o=document.getElementById('gw-setup-overlay');o.dataset.mandatory='false';document.getElementById('gw-setup-close').style.display='';o.style.display='flex'" title="Gateway settings" style="cursor:pointer;"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg></div>
  <!-- Budget & Alerts hidden until mature -->
  <!-- <div class="theme-toggle" onclick="openBudgetModal()" title="Budget & Alerts" style="cursor:pointer;">&#128176;</div> -->

  <div class="theme-toggle" id="logout-btn" onclick="clawmetryLogout()" title="Logout" style="display:none;cursor:pointer;"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg></div>
  <div class="zoom-controls">
    <button class="zoom-btn" onclick="zoomOut()" title="Zoom out (Ctrl/Cmd + -)">−</button>
    <span class="zoom-level" id="zoom-level" title="Current zoom level. Ctrl/Cmd + 0 to reset">100%</span>
    <button class="zoom-btn" onclick="zoomIn()" title="Zoom in (Ctrl/Cmd + +)">+</button>
  </div>
  <div class="nav-tabs">
    <div class="nav-tab" onclick="switchTab('flow')">Flow</div>
    <div class="nav-tab" onclick="switchTab('brain')">Brain</div>
    <div class="nav-tab active" onclick="switchTab('overview')">Overview</div>
    <div class="nav-tab" onclick="switchTab('approvals')" title="Cloud-mediated approval queue">Approvals <span id="nav-approvals-badge" style="display:none;background:#ef4444;color:#fff;border-radius:10px;padding:1px 6px;font-size:10px;font-weight:700;margin-left:4px;">0</span></div>
    <div class="nav-tab" onclick="switchTab('alerts')" title="Get notified when something goes wrong (Pro)">Alerts <span class="pro-chip">Pro</span></div>
    <div class="nav-tab" onclick="switchTab('notifications')" title="Slack / Email / PagerDuty / Telegram channels">Notifications</div>
    <div class="nav-tab" onclick="switchTab('context')" title="See what context the LLM receives each turn">Context</div>
    <div class="nav-tab" onclick="switchTab('usage')">Tokens</div>
    <div class="nav-tab" id="crons-tab" onclick="switchTab('crons')" style="display:none;">Crons</div>
    <div class="nav-tab" onclick="switchTab('memory')">Memory</div>
    <div class="nav-tab" onclick="switchTab('security')">Security</div>
    <div class="nav-tab" id="nemoclaw-tab" onclick="switchTab('nemoclaw')" style="display:none;">NemoClaw</div>
    <!-- History tab hidden until mature -->
    <!-- <div class="nav-tab" onclick="switchTab('history')">History</div> -->
  </div>
</div>

<!-- Alert Banner -->
<div id="alert-banner" style="display:none;padding:10px 16px;background:var(--bg-error);border-bottom:2px solid var(--text-error);color:var(--text-error);font-size:13px;font-weight:600;display:none;align-items:center;gap:10px;">
  <span style="font-size:18px;">&#9888;&#65039;</span>
  <span id="alert-banner-msg" style="flex:1;"></span>
  <button onclick="ackAllAlerts()" style="background:var(--text-error);color:#fff;border:none;border-radius:6px;padding:4px 12px;font-size:12px;cursor:pointer;font-weight:600;">Dismiss</button>
  <button id="alert-resume-btn" onclick="resumeGateway()" style="display:none;background:#16a34a;color:#fff;border:none;border-radius:6px;padding:4px 12px;font-size:12px;cursor:pointer;font-weight:600;">Resume Gateway</button>
</div>

<!-- Upgrade Impact Banner -->
<div id="upgrade-banner" style="display:none;padding:10px 16px;background:linear-gradient(90deg,#1e3a5f 0%,#1a1a2e 100%);border-bottom:2px solid #3b82f6;color:#93c5fd;font-size:13px;font-weight:500;align-items:center;gap:10px;">
  <span style="font-size:16px;">&#128640;</span>
  <span id="upgrade-banner-msg" style="flex:1;"></span>
  <button onclick="switchTab('version-impact')" style="background:#3b82f6;color:#fff;border:none;border-radius:6px;padding:4px 12px;font-size:12px;cursor:pointer;font-weight:600;">View Details</button>
  <button onclick="dismissUpgradeBanner()" style="background:transparent;color:#93c5fd;border:1px solid #3b82f680;border-radius:6px;padding:4px 10px;font-size:11px;cursor:pointer;">Dismiss</button>
</div>

<!-- Budget Settings Modal -->
<div id="budget-modal" style="display:none;position:fixed;inset:0;z-index:1200;background:rgba(0,0,0,0.5);align-items:center;justify-content:center;">
  <div style="background:var(--bg-primary);border:1px solid var(--border-primary);border-radius:16px;width:90%;max-width:560px;padding:24px;box-shadow:0 25px 50px rgba(0,0,0,0.25);">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;">
      <h3 style="font-size:18px;font-weight:700;color:var(--text-primary);">&#128176; Budget & Alerts</h3>
      <button onclick="document.getElementById('budget-modal').style.display='none'" style="background:var(--button-bg);border:1px solid var(--border-primary);border-radius:8px;width:32px;height:32px;cursor:pointer;font-size:18px;color:var(--text-tertiary);">&times;</button>
    </div>
    <div id="budget-modal-tabs" style="display:flex;gap:0;border-bottom:1px solid var(--border-primary);margin-bottom:16px;">
      <div class="modal-tab active" onclick="switchBudgetTab('limits',this)">Budget Limits</div>
      <div class="modal-tab" onclick="switchBudgetTab('alerts',this)">Alert Rules</div>
      <div class="modal-tab" onclick="switchBudgetTab('telegram',this)">Telegram</div>
      <div class="modal-tab" onclick="switchBudgetTab('history',this)">History</div>
    </div>
    <!-- Budget Limits Tab -->
    <div id="budget-tab-limits">
      <div style="display:grid;gap:12px;">
        <div>
          <label style="font-size:12px;color:var(--text-muted);display:block;margin-bottom:4px;">Daily Limit (USD, 0 = no limit)</label>
          <input id="budget-daily" type="number" step="0.01" min="0" style="width:100%;padding:8px 12px;border:1px solid var(--border-primary);border-radius:8px;background:var(--bg-secondary);color:var(--text-primary);font-size:14px;">
        </div>
        <div>
          <label style="font-size:12px;color:var(--text-muted);display:block;margin-bottom:4px;">Weekly Limit (USD)</label>
          <input id="budget-weekly" type="number" step="0.01" min="0" style="width:100%;padding:8px 12px;border:1px solid var(--border-primary);border-radius:8px;background:var(--bg-secondary);color:var(--text-primary);font-size:14px;">
        </div>
        <div>
          <label style="font-size:12px;color:var(--text-muted);display:block;margin-bottom:4px;">Monthly Limit (USD)</label>
          <input id="budget-monthly" type="number" step="0.01" min="0" style="width:100%;padding:8px 12px;border:1px solid var(--border-primary);border-radius:8px;background:var(--bg-secondary);color:var(--text-primary);font-size:14px;">
        </div>
        <div>
          <label style="font-size:12px;color:var(--text-muted);display:block;margin-bottom:4px;">Warning at (%)</label>
          <input id="budget-warn-pct" type="number" step="1" min="1" max="100" value="80" style="width:100%;padding:8px 12px;border:1px solid var(--border-primary);border-radius:8px;background:var(--bg-secondary);color:var(--text-primary);font-size:14px;">
        </div>
        <div style="display:flex;align-items:center;gap:8px;">
          <input id="budget-autopause" type="checkbox" style="cursor:pointer;">
          <label for="budget-autopause" style="font-size:13px;color:var(--text-secondary);cursor:pointer;">Auto-pause gateway when budget exceeded</label>
        </div>
        <button onclick="saveBudgetConfig()" style="background:var(--bg-accent);color:#fff;border:none;border-radius:8px;padding:10px;font-size:14px;font-weight:600;cursor:pointer;">Save Budget Settings</button>
      </div>
      <div id="budget-status-display" style="margin-top:16px;padding:12px;background:var(--bg-secondary);border:1px solid var(--border-primary);border-radius:8px;">
        <div style="font-size:12px;color:var(--text-muted);margin-bottom:8px;">Current Spending</div>
        <div id="budget-status-content" style="font-size:13px;color:var(--text-secondary);">Loading...</div>
      </div>
    </div>
    <!-- Alert Rules Tab -->
    <div id="budget-tab-alerts" style="display:none;">
      <div style="margin-bottom:12px;">
        <button onclick="showAddAlertForm()" style="background:var(--bg-accent);color:#fff;border:none;border-radius:8px;padding:8px 16px;font-size:13px;font-weight:600;cursor:pointer;">+ Add Alert Rule</button>
      </div>
      <div id="add-alert-form" style="display:none;padding:12px;background:var(--bg-secondary);border:1px solid var(--border-primary);border-radius:8px;margin-bottom:12px;">
        <div style="display:grid;gap:8px;">
          <select id="alert-type" style="padding:8px;border:1px solid var(--border-primary);border-radius:6px;background:var(--bg-tertiary);color:var(--text-primary);">
            <option value="threshold">Threshold (daily $ amount)</option>
            <option value="spike">Spike (hourly rate multiplier)</option>
          </select>
          <input id="alert-threshold" type="number" step="0.01" min="0" placeholder="Threshold value" style="padding:8px;border:1px solid var(--border-primary);border-radius:6px;background:var(--bg-tertiary);color:var(--text-primary);">
          <div style="display:flex;gap:8px;flex-wrap:wrap;">
            <label style="font-size:12px;display:flex;align-items:center;gap:4px;"><input type="checkbox" id="alert-ch-banner" checked> Banner</label>
            <label style="font-size:12px;display:flex;align-items:center;gap:4px;"><input type="checkbox" id="alert-ch-telegram"> Telegram</label>
          </div>
          <input id="alert-cooldown" type="number" value="30" min="1" placeholder="Cooldown (min)" style="padding:8px;border:1px solid var(--border-primary);border-radius:6px;background:var(--bg-tertiary);color:var(--text-primary);">
          <div style="display:flex;gap:8px;">
            <button onclick="createAlertRule()" style="background:#16a34a;color:#fff;border:none;border-radius:6px;padding:6px 16px;font-size:13px;cursor:pointer;">Create</button>
            <button onclick="document.getElementById('add-alert-form').style.display='none'" style="background:var(--button-bg);color:var(--text-secondary);border:none;border-radius:6px;padding:6px 16px;font-size:13px;cursor:pointer;">Cancel</button>
          </div>
        </div>
      </div>
      <div style="padding:12px;background:var(--bg-secondary);border:1px solid var(--border-primary);border-radius:8px;margin-bottom:12px;">
        <div style="font-size:13px;font-weight:700;color:var(--text-primary);margin-bottom:10px;">Alert Channels (Webhooks)</div>
        <div style="display:grid;gap:8px;">
          <div style="display:flex;gap:6px;align-items:center;">
            <input id="alert-webhook-url" type="text" placeholder="Generic webhook URL (JSON payload)" style="flex:1;padding:8px;border:1px solid var(--border-primary);border-radius:6px;background:var(--bg-tertiary);color:var(--text-primary);">
            <button onclick="testWebhookConfig('generic')" style="background:#374151;color:#fff;border:none;border-radius:6px;padding:6px 10px;font-size:11px;cursor:pointer;white-space:nowrap;">Test</button>
          </div>
          <div style="display:flex;gap:6px;align-items:center;">
            <input id="alert-slack-url" type="text" placeholder="Slack incoming webhook URL" style="flex:1;padding:8px;border:1px solid var(--border-primary);border-radius:6px;background:var(--bg-tertiary);color:var(--text-primary);">
            <button onclick="testWebhookConfig('slack')" style="background:#4a154b;color:#fff;border:none;border-radius:6px;padding:6px 10px;font-size:11px;cursor:pointer;white-space:nowrap;">Test</button>
          </div>
          <div style="display:flex;gap:6px;align-items:center;">
            <input id="alert-discord-url" type="text" placeholder="Discord webhook URL" style="flex:1;padding:8px;border:1px solid var(--border-primary);border-radius:6px;background:var(--bg-tertiary);color:var(--text-primary);">
            <button onclick="testWebhookConfig('discord')" style="background:#5865f2;color:#fff;border:none;border-radius:6px;padding:6px 10px;font-size:11px;cursor:pointer;white-space:nowrap;">Test</button>
          </div>
          <div style="display:flex;gap:12px;flex-wrap:wrap;align-items:center;">
            <label style="font-size:12px;display:flex;align-items:center;gap:4px;"><input type="checkbox" id="alert-toggle-cost-spike"> Cost spike alerts</label>
            <label style="font-size:12px;display:flex;align-items:center;gap:4px;"><input type="checkbox" id="alert-toggle-agent-error"> Agent error rate alerts</label>
            <label style="font-size:12px;display:flex;align-items:center;gap:4px;"><input type="checkbox" id="alert-toggle-security"> Security posture changes</label>
          </div>
          <div style="display:flex;gap:12px;align-items:center;flex-wrap:wrap;">
            <label style="font-size:12px;color:var(--text-muted);">Min severity:</label>
            <select id="alert-min-severity" style="padding:4px 8px;border:1px solid var(--border-primary);border-radius:6px;background:var(--bg-tertiary);color:var(--text-primary);font-size:12px;">
              <option value="info">Info (all alerts)</option>
              <option value="warning" selected>Warning+</option>
              <option value="critical">Critical only</option>
            </select>
          </div>
          <div style="display:flex;gap:8px;">
            <button onclick="saveWebhookConfig()" style="background:var(--bg-accent);color:#fff;border:none;border-radius:6px;padding:6px 14px;font-size:12px;cursor:pointer;">Save</button>
            <button onclick="testWebhookConfig('all')" style="background:#16a34a;color:#fff;border:none;border-radius:6px;padding:6px 14px;font-size:12px;cursor:pointer;">Test All</button>
            <span id="alert-webhook-status" style="font-size:12px;color:var(--text-muted);display:flex;align-items:center;"></span>
          </div>
        </div>
      </div>
      <div id="alert-rules-list" style="font-size:13px;color:var(--text-secondary);">Loading...</div>
    </div>
    <!-- Telegram Tab -->
    <div id="budget-tab-telegram" style="display:none;">
      <div style="display:grid;gap:12px;">
        <div style="font-size:12px;color:var(--text-muted);line-height:1.5;">
          Configure direct Telegram notifications for budget alerts. Create a bot via <a href="https://t.me/BotFather" target="_blank" style="color:var(--text-accent);">@BotFather</a> and get your chat ID.
        </div>
        <div>
          <label style="font-size:12px;color:var(--text-muted);display:block;margin-bottom:4px;">Bot Token</label>
          <input id="tg-bot-token" type="password" placeholder="123456:ABC-DEF..." style="width:100%;padding:8px 12px;border:1px solid var(--border-primary);border-radius:8px;background:var(--bg-secondary);color:var(--text-primary);font-size:14px;">
        </div>
        <div>
          <label style="font-size:12px;color:var(--text-muted);display:block;margin-bottom:4px;">Chat ID</label>
          <input id="tg-chat-id" type="text" placeholder="-100123456789" style="width:100%;padding:8px 12px;border:1px solid var(--border-primary);border-radius:8px;background:var(--bg-secondary);color:var(--text-primary);font-size:14px;">
        </div>
        <div style="display:flex;gap:8px;">
          <button onclick="saveTelegramConfig()" style="background:var(--bg-accent);color:#fff;border:none;border-radius:8px;padding:10px 16px;font-size:14px;font-weight:600;cursor:pointer;">Save</button>
          <button onclick="testTelegram()" style="background:#16a34a;color:#fff;border:none;border-radius:8px;padding:10px 16px;font-size:14px;font-weight:600;cursor:pointer;">Send Test</button>
        </div>
        <div id="tg-status" style="font-size:12px;color:var(--text-muted);"></div>
      </div>
    </div>
    <!-- History Tab -->
    <div id="budget-tab-history" style="display:none;">
      <div id="alert-history-list" style="font-size:13px;color:var(--text-secondary);max-height:400px;overflow-y:auto;">Loading...</div>
    </div>
  </div>
</div>

<!-- OVERVIEW (Split-Screen Hacker Dashboard) -->
<div class="page active" id="page-overview">

  <!-- PRIMARY KPI: Autonomy Score (#688) -->
  <div id="autonomy-card" style="
    background:var(--bg-secondary);
    border:2px solid var(--border-primary);
    border-radius:12px;
    padding:18px 22px;
    margin-bottom:14px;
    box-shadow:var(--card-shadow);
    display:grid;
    grid-template-columns:1fr 1fr;
    gap:16px;
    align-items:start;
  ">
    <!-- Left: big number + subtitle -->
    <div>
      <div style="font-size:13px;font-weight:700;color:var(--text-muted);text-transform:uppercase;letter-spacing:1.5px;margin-bottom:6px;">&#127919; Autonomy Score</div>
      <div style="display:flex;align-items:baseline;gap:12px;flex-wrap:wrap;">
        <span id="autonomy-score-value" style="font-size:48px;font-weight:800;line-height:1;color:var(--text-primary);">--</span>
        <span id="autonomy-trend-badge" style="font-size:13px;font-weight:600;padding:3px 8px;border-radius:20px;"></span>
      </div>
      <div id="autonomy-median-gap" style="font-size:13px;color:var(--text-muted);margin-top:6px;">Median time between nudges: --</div>
      <div id="autonomy-trend-pct" style="font-size:12px;color:var(--text-muted);margin-top:2px;"></div>
      <div style="font-size:10px;color:var(--text-muted);margin-top:10px;font-style:italic;line-height:1.4;max-width:420px;">
        Alex&#8217;s definition: &#8220;Success = human nudges space out exponentially&#8221;
      </div>
    </div>
    <!-- Right: sparkline -->
    <div style="display:flex;flex-direction:column;align-items:flex-end;justify-content:center;">
      <div style="font-size:11px;color:var(--text-muted);margin-bottom:6px;text-align:right;">7-day autonomy ratio</div>
      <svg id="autonomy-sparkline" width="160" height="48" viewBox="0 0 160 48" style="overflow:visible;">
        <text x="80" y="28" text-anchor="middle" fill="var(--text-muted)" font-size="10">No data yet</text>
      </svg>
      <div id="autonomy-samples" style="font-size:10px;color:var(--text-muted);margin-top:4px;text-align:right;"></div>
    </div>
  </div>

  <div class="refresh-bar" style="margin-bottom:6px;">
    <button class="refresh-btn" onclick="loadAll()" style="padding:4px 12px;font-size:12px;">↻</button>
    <span class="pulse"></span>
    <span class="live-badge">LIVE</span>
    <span class="refresh-time" id="refresh-time" style="font-size:11px;">Loading...</span>
  </div>

  <!-- Token Velocity Alert Banner (GH #313) -->
  <div id="velocity-alert-banner" style="display:none;margin-bottom:8px;border-radius:8px;padding:10px 16px;font-size:13px;font-weight:600;">
    <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;">
      <span id="velocity-alert-msg"></span>
      <span style="font-size:11px;font-weight:400;color:inherit;opacity:0.8;">auto-refreshes every 30s</span>
    </div>
    <div id="velocity-flagged-list" style="margin-top:8px;display:flex;flex-wrap:wrap;gap:8px;"></div>
  </div>

  <!-- Stats Bar (top) -->
  <div class="stats-footer">
    <div class="stats-footer-item">
      <span class="stats-footer-icon">💰</span>
      <div>
        <div class="stats-footer-label">Spending <span id="cost-info-icon" class="tooltip-info-icon" style="display:none;">i</span></div>
        <div class="stats-footer-value" id="cost-today">$0.00</div>
        <div class="stats-footer-sub" id="cost-billing-badge" style="margin-top:2px;display:none;"></div>
      </div>
      <div style="margin-left:auto;text-align:right;">
        <div class="stats-footer-sub">wk: <span id="cost-week">--</span></div>
        <div class="stats-footer-sub">mo: <span id="cost-month">--</span></div>
      </div>
      <span id="cost-trend" style="display:none;">Estimated from usage -- may be $0 billed with OAuth auth</span>
    </div>
    <div class="stats-footer-item">
      <span class="stats-footer-icon">🤖</span>
      <div>
        <div class="stats-footer-label">Model</div>
        <div class="stats-footer-value" id="model-primary">--</div>
      </div>
      <div id="model-breakdown" style="display:none;">Loading...</div>
    </div>
    <div class="stats-footer-item">
      <span class="stats-footer-icon">📊</span>
      <div>
        <div class="stats-footer-label">Tokens</div>
        <div class="stats-footer-value" id="token-rate">--</div>
      </div>
      <span class="stats-footer-sub" style="margin-left:auto;">today: <span id="tokens-today" style="color:var(--text-success);font-weight:600;">--</span></span>
    </div>
    <div class="stats-footer-item">
      <span class="stats-footer-icon">💬</span>
      <div>
        <div class="stats-footer-label">Sessions</div>
        <div class="stats-footer-value" id="hot-sessions-count">--</div>
      </div>
      <div id="hot-sessions-list" style="display:none;">Loading...</div>
    </div>
    <div class="stats-footer-item" id="reliability-card">
      <span class="stats-footer-icon" id="reliability-icon">🔄</span>
      <div>
        <div class="stats-footer-label">Reliability</div>
        <div class="stats-footer-value" id="reliability-direction">--</div>
      </div>
      <span class="stats-footer-sub" style="margin-left:auto;" id="reliability-detail"></span>
    </div>
  </div>

  <!-- Split Screen: Flow Left | Tasks Right -->
  <div class="overview-split">
    <!-- LEFT: Flow + System Health stacked -->
    <div style="display:flex;flex-direction:column;">
      <div class="overview-flow-pane" style="border-radius:8px 0 0 0;flex:3;min-height:0;">
        <div class="grid-overlay"></div>
        <div class="scanline-overlay"></div>
        <div class="flow-container" id="overview-flow-container">
          <!-- Flow SVG cloned here by JS -->
          <div style="display:flex;align-items:center;justify-content:center;height:100%;color:var(--text-muted);font-size:13px;">Loading flow...</div>
        </div>
      </div>

      <!-- System Health Panel (below flow SVG) -->
      <div id="system-health-panel" style="background:var(--bg-secondary);border:1px solid var(--border-primary);border-top:none;padding:16px;box-shadow:var(--card-shadow);">
        <div style="font-size:14px;font-weight:700;color:var(--text-primary);margin-bottom:12px;">🏥 System Health</div>
        <div style="font-size:11px;text-transform:uppercase;letter-spacing:1.5px;color:var(--text-muted);font-weight:600;margin-bottom:6px;">Services</div>
        <div id="sh-services" style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:14px;"></div>
        <div id="sh-channels-wrap"><div style="font-size:11px;text-transform:uppercase;letter-spacing:1.5px;color:var(--text-muted);font-weight:600;margin-bottom:6px;">Channels</div>
        <div id="sh-channels" style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:14px;"></div></div>
        <div style="font-size:11px;text-transform:uppercase;letter-spacing:1.5px;color:var(--text-muted);font-weight:600;margin-bottom:6px;">Disk Usage</div>
        <div id="sh-disks" style="margin-bottom:14px;"></div>
        <div style="font-size:11px;text-transform:uppercase;letter-spacing:1.5px;color:var(--text-muted);font-weight:600;margin-bottom:6px;">Cron Jobs</div>
        <div id="sh-crons" style="margin-bottom:14px;"></div>
        <div style="font-size:11px;text-transform:uppercase;letter-spacing:1.5px;color:var(--text-muted);font-weight:600;margin-bottom:6px;">Sub-Agents (24h)</div>
        <div id="sh-subagents" style="margin-bottom:14px;"></div>
        <div id="delegation-chains-panel" style="margin-bottom:14px;"></div>
        <div id="sh-heartbeat-wrap" style="display:none;"><div style="font-size:11px;text-transform:uppercase;letter-spacing:1.5px;color:var(--text-muted);font-weight:600;margin-bottom:6px;">Heartbeat</div>
        <div id="sh-heartbeat" style="margin-bottom:14px;"></div></div>
        <div id="sh-sandbox-wrap" style="display:none;"><div style="font-size:11px;text-transform:uppercase;letter-spacing:1.5px;color:var(--text-muted);font-weight:600;margin-bottom:6px;">🔒 Sandbox</div>
        <div id="sh-sandbox" style="margin-bottom:14px;"></div></div>
        <div id="sh-inference-wrap" style="display:none;"><div style="font-size:11px;text-transform:uppercase;letter-spacing:1.5px;color:var(--text-muted);font-weight:600;margin-bottom:6px;">🤖 Inference Provider</div>
        <div id="sh-inference" style="margin-bottom:14px;"></div></div>
        <div id="sh-security-wrap" style="display:none;"><div style="font-size:11px;text-transform:uppercase;letter-spacing:1.5px;color:var(--text-muted);font-weight:600;margin-bottom:6px;">🛡️ Security Posture</div>
        <div id="sh-security" style="margin-bottom:14px;"></div></div>
        <div id="sh-reliability-wrap" style="display:none;"><div style="font-size:11px;text-transform:uppercase;letter-spacing:1.5px;color:var(--text-muted);font-weight:600;margin-bottom:6px;">📊 Agent Reliability</div>
        <div id="sh-reliability" style="margin-bottom:14px;"></div></div>
        <!-- 🔍 Diagnostics Panel (GH#28) -->
        <div id="sh-diagnostics-wrap">
          <div style="display:flex;align-items:center;justify-content:space-between;cursor:pointer;padding:4px 0;" onclick="var b=document.getElementById(\'sh-diagnostics-body\');b.style.display=b.style.display===\'none\'?\'block\':\'none\';this.querySelector(\'.diag-chevron\').textContent=b.style.display===\'none\'?\'▶\':\'▼\';">
            <div style="font-size:11px;text-transform:uppercase;letter-spacing:1.5px;color:var(--text-muted);font-weight:600;">🔍 Configuration Diagnostics</div>
            <div style="display:flex;align-items:center;gap:8px;">
              <button id="sh-diagnostics-copy" onclick="event.stopPropagation();copyDiagnostics();" style="font-size:10px;padding:2px 8px;background:var(--bg-secondary);border:1px solid var(--border-secondary);border-radius:4px;color:var(--text-muted);cursor:pointer;">📋 Copy</button>
              <span class="diag-chevron" style="font-size:10px;color:var(--text-muted);">▼</span>
            </div>
          </div>
          <div id="sh-diagnostics-body" style="margin-bottom:14px;">
            <div id="sh-diagnostics" style="font-family:\'JetBrains Mono\',monospace;font-size:12px;background:var(--bg-primary);border:1px solid var(--border-secondary);border-radius:6px;padding:10px 12px;line-height:1.9;">
              <div style="color:var(--text-muted);">Loading diagnostics...</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- DIVIDER -->
    <div class="overview-divider"></div>

    <!-- RIGHT: Active Tasks + Brain stacked -->
    <div class="overview-tasks-pane">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;">
        <div style="display:flex;align-items:center;gap:8px;">
          <span style="font-size:15px;font-weight:700;color:var(--text-primary);">🐝 Active Tasks</span>
          <span id="overview-tasks-count-badge" style="font-size:11px;color:var(--text-muted);"></span>
        </div>
        <span style="font-size:10px;color:var(--text-faint);letter-spacing:0.5px;">⟳ 30s</span>
      </div>
      <div class="tasks-panel-scroll" id="overview-tasks-list">
        <div style="text-align:center;padding:32px;color:var(--text-muted);">
          <div style="font-size:28px;margin-bottom:8px;" class="tasks-empty-icon">🐝</div>
          <div style="font-size:13px;">Loading tasks...</div>
        </div>
      </div>
      <!-- 🧠 Brain Panel: Main Agent Activity (below Active Tasks) -->
      <div id="main-activity-panel" style="background:linear-gradient(180deg, var(--bg-secondary) 0%, #12121a 100%);border:1px solid var(--border-primary);border-radius:12px;padding:10px 14px 8px;min-height:80px;margin-top:14px;display:flex;flex-direction:column;overflow:hidden;">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;">
          <div style="display:flex;align-items:center;gap:6px;">
            <span id="main-activity-dot" style="width:8px;height:8px;border-radius:50%;background:#888;display:inline-block;"></span>
            <span style="font-size:13px;font-weight:700;color:var(--text-primary);">🧠 <span id="main-activity-model">Claude Opus</span></span>
            <span id="main-activity-status" style="font-size:10px;color:var(--text-muted);">
              <span id="main-activity-label">...</span>
            </span>
          </div>
        </div>
        <div id="main-activity-list" style="overflow-y:auto;flex:1;font-size:11px;font-family:'JetBrains Mono','Fira Code',monospace;line-height:1.6;">
          <div style="text-align:center;padding:8px;color:var(--text-muted);font-size:11px;">Waiting for activity...</div>
        </div>
      </div>
    </div>
  </div>

  <!-- Hidden elements referenced by existing JS -->
  <div style="display:none;">
    <span id="tokens-peak">--</span>
    <span id="subagents-count">--</span>
    <span id="subagents-status">--</span>
    <span id="subagents-preview"></span>
    <span id="tools-active">--</span>
    <span id="tools-recent">--</span>
    <div id="tools-sparklines"><div class="tool-spark"><span>--</span></div><div class="tool-spark"><span>--</span></div><div class="tool-spark"><span>--</span></div></div>
    <div id="active-tasks-grid"></div>
    <div id="activity-stream"></div>
  </div>

  <!-- old system health removed, now inside tasks pane -->

  <!-- ❤️ Heartbeat Liveness Panel (#686) -->
  <div id="heartbeat-panel" style="margin-top:16px;background:var(--bg-secondary);border:1px solid var(--border-primary);border-radius:10px;padding:14px 18px;box-shadow:var(--card-shadow);">
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;">
      <span style="font-size:14px;font-weight:700;color:var(--text-primary);">&#x2764;&#xfe0f; Heartbeat</span>
      <span id="hb-status-badge" style="font-size:11px;font-weight:600;padding:2px 8px;border-radius:10px;background:rgba(107,114,128,0.2);color:var(--text-muted);">...</span>
    </div>
    <div style="display:flex;align-items:center;gap:20px;flex-wrap:wrap;">
      <!-- Pulse indicator -->
      <div style="display:flex;flex-direction:column;align-items:center;gap:4px;min-width:48px;">
        <div id="hb-pulse-dot" style="width:20px;height:20px;border-radius:50%;background:#6b7280;animation:none;"></div>
        <span id="hb-pulse-label" style="font-size:10px;color:var(--text-muted);">no data</span>
      </div>
      <!-- Stats -->
      <div style="flex:1;display:flex;flex-direction:column;gap:5px;min-width:200px;">
        <div style="font-size:12px;color:var(--text-primary);">Last beat: <span id="hb-last-beat" style="font-weight:600;color:var(--text-success);">--</span></div>
        <div style="font-size:12px;color:var(--text-primary);">Cadence (24h): <span id="hb-cadence" style="font-weight:600;">-- / --</span> expected</div>
        <div style="font-size:12px;color:var(--text-primary);">Idle replies: <span id="hb-ok-ratio" style="font-weight:600;color:var(--text-success);">--%</span> &middot; Action taken: <span id="hb-action-ratio" style="font-weight:600;">--%</span></div>
      </div>
      <!-- Recent beats sparkline -->
      <div style="display:flex;flex-direction:column;gap:4px;align-items:center;">
        <div style="font-size:10px;color:var(--text-muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:2px;">Last 10 beats</div>
        <div id="hb-sparkline" style="display:flex;align-items:center;gap:4px;height:20px;">
          <span style="font-size:11px;color:var(--text-muted);">--</span>
        </div>
      </div>
    </div>
  </div>
  <style>
    @keyframes hb-pulse-healthy { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:.6;transform:scale(1.15)} }
    @keyframes hb-pulse-drifting { 0%,100%{opacity:1} 50%{opacity:.4} }
    @keyframes hb-pulse-missed { 0%,100%{opacity:1;box-shadow:0 0 0 0 rgba(239,68,68,.4)} 70%{opacity:.8;box-shadow:0 0 0 8px rgba(239,68,68,0)} }
  </style>
</div>

<!-- USAGE -->
<div class="page" id="page-usage">
  <div class="refresh-bar">
    <button class="refresh-btn" onclick="loadUsage()">↻ Refresh</button>
    <button class="refresh-btn" onclick="exportUsageData()" style="margin-left: 8px;">📥 Export CSV</button>
  </div>
  
  <!-- Cost Warnings -->
  <div id="cost-warnings" style="display:none; margin-bottom: 16px;"></div>
  
  <!-- Main Usage Stats -->
  <div class="grid">
    <div class="card">
      <div class="card-title"><span class="icon">📊</span> Today</div>
      <div class="card-value" id="usage-today">--</div>
      <div class="card-sub" id="usage-today-cost"></div>
    </div>
    <div class="card">
      <div class="card-title"><span class="icon">📅</span> This Week</div>
      <div class="card-value" id="usage-week">--</div>
      <div class="card-sub" id="usage-week-cost"></div>
    </div>
    <div class="card">
      <div class="card-title"><span class="icon">📆</span> This Month</div>
      <div class="card-value" id="usage-month">--</div>
      <div class="card-sub" id="usage-month-cost"></div>
    </div>
    <div class="card" id="trend-card" style="display:none;">
      <div class="card-title"><span class="icon">📈</span> Trend</div>
      <div class="card-value" id="trend-direction">--</div>
      <div class="card-sub" id="trend-prediction"></div>
    </div>
  </div>
  <div class="section-title">📊 Token Usage (14 days)</div>
  <div class="card">
    <div class="usage-chart" id="usage-chart">Loading...</div>
  </div>
  <div class="section-title">💰 Cost Breakdown <span id="usage-cost-info-icon" class="tooltip-info-icon" style="display:none;">i</span></div>
  <div class="card"><table class="usage-table" id="usage-cost-table"><tbody><tr><td colspan="3" style="color:#666;">Loading...</td></tr></tbody></table></div>
  <div id="otel-extra-sections" style="display:none;">
    <div class="grid" style="margin-top:16px;">
      <div class="card">
        <div class="card-title"><span class="icon">⏱️</span> Avg Run Duration</div>
        <div class="card-value" id="usage-avg-run">--</div>
        <div class="card-sub">from OTLP openclaw.run.duration_ms</div>
      </div>
      <div class="card">
        <div class="card-title"><span class="icon">💬</span> Messages Processed</div>
        <div class="card-value" id="usage-msg-count">--</div>
        <div class="card-sub">from OTLP openclaw.message.processed</div>
      </div>
    </div>
    <div class="section-title">🤖 Model Breakdown</div>
    <div class="card"><table class="usage-table" id="usage-model-table"><tbody><tr><td colspan="2" style="color:#666;">No model data</td></tr></tbody></table></div>
    <div style="margin-top:12px;padding:8px 12px;background:#1a3a2a;border:1px solid #2a5a3a;border-radius:8px;font-size:12px;color:#60ff80;">📡 Data source: OpenTelemetry OTLP - real-time metrics from OpenClaw</div>
  </div>
  <!-- Cost Comparison Panel (GH#554) -->
  <div class="section-title" id="cost-comparison-section" style="display:flex;align-items:center;">💱 Cost Comparison <span style="font-size:11px;font-weight:400;color:var(--text-muted);margin-left:8px;">what same workload costs elsewhere · 30 days</span></div>
  <div class="card" id="cost-comparison-card" style="display:none;">
    <div id="cost-comparison-content" style="min-height:60px;color:var(--text-muted);">Loading...</div>
  </div>
    <div class="section-title">🔮 Trace Clusters <span style="font-size:11px;font-weight:400;color:var(--text-muted);margin-left:8px;">auto-group sessions by behavior pattern</span></div>
  <div class="card">
    <div id="trace-clusters-content" style="min-height:60px;color:var(--text-muted);">Loading...</div>
  </div>
  <div class="section-title" style="display:flex;align-items:center;">📅 Activity Heatmap <span style="font-size:11px;font-weight:400;color:var(--text-muted);margin-left:8px;">hourly usage intensity</span>
    <span style="margin-left:auto;display:flex;gap:6px;">
      <button id="heatmap-btn-7d" class="time-btn active" onclick="loadHeatmap(7)" style="font-size:11px;padding:2px 8px;">7d</button>
      <button id="heatmap-btn-30d" class="time-btn" onclick="loadHeatmap(30)" style="font-size:11px;padding:2px 8px;">30d</button>
    </span>
  </div>
  <div class="card">
    <div class="heatmap-wrap"><div id="heatmap-grid" class="heatmap-grid">Loading...</div></div>
    <div id="heatmap-legend" class="heatmap-legend"></div>
  </div>
</div>

<!-- CRONS -->
<div class="page" id="page-crons">
  <div class="refresh-bar" style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
    <button class="refresh-btn" onclick="loadCrons()">&#x21bb; Refresh</button>
    <button class="refresh-btn cron-action-btn" onclick="cronCreateNew()" style="background:#6366f1;color:#fff;border-color:#6366f1;display:none;">+ New Job</button>
    <button class="refresh-btn cron-action-btn" id="cron-kill-all-btn" onclick="cronKillAll()" style="background:#dc2626;color:#fff;border-color:#dc2626;display:none;">&#x1F6D1; Emergency Stop All</button>
    <label class="modal-auto-refresh" style="margin-left:auto;">
      <input type="checkbox" id="cron-auto-refresh" onchange="toggleCronAutoRefresh()" checked> Auto-refresh (30s)
    </label>
  </div>
  <div id="cron-health-panel" style="margin-bottom:12px;"></div>
  <div id="crons-multi-node" style="display:none;margin-bottom:12px;"></div>
  <div class="card" id="crons-list">Loading...</div>
  <!-- Cron Health Monitor (GH #302) -->
  <div id="cron-health-anomaly-banner" style="display:none;margin-top:14px;padding:10px 14px;background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.4);border-radius:8px;color:#ef4444;font-size:13px;font-weight:600;">&#x26A0;&#xFE0F; Anomalies detected in cron jobs — review health table below</div>
  <div style="margin-top:16px;">
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">
      <span style="font-size:14px;font-weight:700;color:var(--text-primary);">&#x1F4CA; Cron Health Monitor</span>
      <span style="font-size:11px;color:var(--text-muted);">Click row to expand run history</span>
    </div>
    <div id="cron-health-table" style="overflow-x:auto;">
      <div style="color:var(--text-muted);font-size:13px;">Loading health data...</div>
    </div>
  </div>
</div>

<!-- Cron Edit/Create Modal -->
<div id="cron-edit-modal" style="display:none;position:fixed;inset:0;z-index:1500;background:rgba(0,0,0,0.5);align-items:center;justify-content:center;backdrop-filter:blur(4px);">
  <div style="background:var(--bg-tertiary);border:1px solid var(--border-primary);border-radius:12px;padding:24px;width:480px;max-width:90vw;box-shadow:0 8px 30px rgba(0,0,0,0.4);max-height:80vh;overflow-y:auto;margin:auto;">
    <h3 id="cron-modal-title" style="margin:0 0 16px;color:var(--text-primary);font-size:16px;">Edit Cron Job</h3>
    <input type="hidden" id="cron-edit-id">
    <input type="hidden" id="cron-edit-mode" value="edit">
    <div style="margin-bottom:12px;">
      <label style="display:block;font-size:12px;color:var(--text-muted);margin-bottom:4px;">Name</label>
      <input id="cron-edit-name" style="width:100%;padding:8px 12px;background:var(--bg-secondary);border:1px solid var(--border-secondary);border-radius:8px;color:var(--text-primary);font-size:13px;box-sizing:border-box;" placeholder="my-health-check">
    </div>
    <div style="margin-bottom:12px;">
      <label style="display:block;font-size:12px;color:var(--text-muted);margin-bottom:4px;">Schedule (cron expression or interval like "every 30min")</label>
      <input id="cron-edit-schedule" style="width:100%;padding:8px 12px;background:var(--bg-secondary);border:1px solid var(--border-secondary);border-radius:8px;color:var(--text-primary);font-size:13px;font-family:'SF Mono','Fira Code',monospace;box-sizing:border-box;" placeholder="*/30 * * * *  or  every 30min">
    </div>
    <div style="margin-bottom:12px;">
      <label style="display:block;font-size:12px;color:var(--text-muted);margin-bottom:4px;">Timezone (for cron expressions)</label>
      <input id="cron-edit-tz" style="width:100%;padding:8px 12px;background:var(--bg-secondary);border:1px solid var(--border-secondary);border-radius:8px;color:var(--text-primary);font-size:13px;box-sizing:border-box;" placeholder="e.g. Europe/Amsterdam">
    </div>
    <div id="cron-edit-prompt-section" style="margin-bottom:12px;">
      <label style="display:block;font-size:12px;color:var(--text-muted);margin-bottom:4px;">Prompt / Message</label>
      <textarea id="cron-edit-prompt" rows="3" style="width:100%;padding:8px 12px;background:var(--bg-secondary);border:1px solid var(--border-secondary);border-radius:8px;color:var(--text-primary);font-size:13px;box-sizing:border-box;resize:vertical;font-family:inherit;" placeholder="What should the agent do when this cron fires?"></textarea>
    </div>
    <div id="cron-edit-channel-section" style="margin-bottom:12px;">
      <label style="display:block;font-size:12px;color:var(--text-muted);margin-bottom:4px;">Channel (optional)</label>
      <input id="cron-edit-channel" style="width:100%;padding:8px 12px;background:var(--bg-secondary);border:1px solid var(--border-secondary);border-radius:8px;color:var(--text-primary);font-size:13px;box-sizing:border-box;" placeholder="e.g. discord, telegram">
    </div>
    <div id="cron-edit-model-section" style="margin-bottom:12px;">
      <label style="display:block;font-size:12px;color:var(--text-muted);margin-bottom:4px;">Model (optional)</label>
      <input id="cron-edit-model" style="width:100%;padding:8px 12px;background:var(--bg-secondary);border:1px solid var(--border-secondary);border-radius:8px;color:var(--text-primary);font-size:13px;box-sizing:border-box;" placeholder="e.g. anthropic/claude-sonnet-4-20250514">
    </div>
    <div style="margin-bottom:16px;display:flex;align-items:center;gap:8px;">
      <input type="checkbox" id="cron-edit-enabled" style="accent-color:#6366f1;" checked>
      <label for="cron-edit-enabled" style="font-size:13px;color:var(--text-primary);">Enabled</label>
    </div>
    <div style="display:flex;gap:8px;justify-content:flex-end;">
      <button onclick="closeCronEditModal()" style="padding:8px 20px;border-radius:8px;border:none;font-size:13px;font-weight:600;cursor:pointer;background:var(--button-bg);color:var(--text-secondary);">Cancel</button>
      <button onclick="saveCronEdit()" id="cron-save-btn" style="padding:8px 20px;border-radius:8px;border:none;font-size:13px;font-weight:600;cursor:pointer;background:#6366f1;color:#fff;">Save</button>
    </div>
  </div>
</div>

<!-- MEMORY -->
<div class="page" id="page-memory">
  <div class="refresh-bar">
    <button class="refresh-btn" onclick="loadMemory()">↻ Refresh</button>
  </div>
  <div id="memory-analytics-panel" style="margin-bottom:12px"></div>
  <div class="card" id="memory-list">Loading...</div>
  <div class="file-viewer" id="file-viewer">
    <div class="file-viewer-header">
      <span class="file-viewer-title" id="file-viewer-title"></span>
      <button class="file-viewer-close" onclick="closeFileViewer()">✕ Close</button>
    </div>
    <div class="file-viewer-content" id="file-viewer-content"></div>
  </div>
</div>

<!-- TRANSCRIPTS -->
<div class="page" id="page-transcripts">
  <div class="refresh-bar">
    <button class="refresh-btn" onclick="loadTranscripts()">↻ Refresh</button>
    <button class="refresh-btn" id="transcript-back-btn" style="display:none" onclick="showTranscriptList()">← Back to list</button>
  </div>
  <div class="card" id="transcript-list">Loading...</div>
  <div id="transcript-viewer" style="display:none">
    <div class="transcript-viewer-meta" id="transcript-meta"></div>
    <div class="chat-messages" id="transcript-messages"></div>
  </div>
</div>


<!-- UPGRADE IMPACT -->
<div class="page" id="page-version-impact">
  <div class="refresh-bar">
    <h2 style="font-size:16px;font-weight:700;color:var(--text-primary);margin:0;flex:1;">&#128200; Upgrade Impact</h2>
    <button class="refresh-btn" onclick="loadVersionImpact()">&#8635; Refresh</button>
  </div>
  <div id="version-impact-content" style="padding:8px 0;">
    <div style="color:var(--text-muted);font-size:13px;">Loading...</div>
  </div>
</div>

<!-- SESSION CLUSTERS -->
<div class="page" id="page-clusters">
  <div class="refresh-bar">
    <h2 style="font-size:16px;font-weight:700;color:var(--text-primary);margin:0;flex:1;">&#129492; Session Clusters</h2>
    <button class="refresh-btn" onclick="loadClusters()">&#8635; Refresh</button>
  </div>
  <div id="clusters-content" style="padding:8px 0;">
    <div style="color:var(--text-muted);font-size:13px;">Loading...</div>
  </div>
</div>

<!-- HISTORY -->

<!-- RATE LIMITS -->
<div class="page" id="page-limits">
  <div class="refresh-bar">
    <h2 style="font-size:16px;font-weight:700;color:var(--text-primary);margin:0;flex:1;">&#9889; API Rate Limit Monitor</h2>
    <button class="refresh-btn" onclick="loadRateLimits()">&#8635; Refresh</button>
  </div>
  <p style="font-size:12px;color:var(--text-muted);margin:0 0 14px 0;">Rolling 1-minute window utilisation per provider. Red = &ge;90%, amber = &ge;70%. Data sourced from OTLP metrics.</p>
  <div id="rate-limits-content">
    <div class="card" style="padding:24px;text-align:center;color:var(--text-muted);">Loading rate limit data...</div>
  </div>
  <div id="rate-limits-hourly" style="margin-top:16px;"></div>
</div>

<div class="page" id="page-history">
  <div style="display:flex;align-items:center;gap:16px;margin-bottom:16px;flex-wrap:wrap;">
    <h2 style="font-size:18px;font-weight:700;color:var(--text-primary);margin:0;">&#128202; History</h2>
    <div style="display:flex;gap:4px;flex-wrap:wrap;" id="time-range-picker">
      <button class="time-btn active" onclick="setTimeRange(3600,this)">1h</button>
      <button class="time-btn" onclick="setTimeRange(21600,this)">6h</button>
      <button class="time-btn" onclick="setTimeRange(86400,this)">24h</button>
      <button class="time-btn" onclick="setTimeRange(604800,this)">7d</button>
      <button class="time-btn" onclick="setTimeRange(2592000,this)">30d</button>
      <button class="time-btn" onclick="showCustomRange()">Custom</button>
    </div>
    <div id="custom-range-picker" style="display:none;gap:8px;align-items:center;">
      <input type="datetime-local" id="history-from" style="padding:4px 8px;border:1px solid var(--border-primary);border-radius:6px;background:var(--bg-secondary);color:var(--text-primary);font-size:12px;">
      <span style="color:var(--text-muted);">to</span>
      <input type="datetime-local" id="history-to" style="padding:4px 8px;border:1px solid var(--border-primary);border-radius:6px;background:var(--bg-secondary);color:var(--text-primary);font-size:12px;">
      <button class="time-btn" onclick="applyCustomRange()">Apply</button>
    </div>
    <div id="history-status" style="font-size:12px;color:var(--text-muted);margin-left:auto;"></div>
  </div>

  <!-- Token Usage Chart -->
  <div class="card" style="margin-bottom:16px;padding:16px;">
    <h3 style="font-size:14px;font-weight:600;color:var(--text-primary);margin:0 0 12px 0;">Token Usage Over Time</h3>
    <canvas id="history-tokens-chart" height="200"></canvas>
  </div>

  <!-- Cost Chart -->
  <div class="card" style="margin-bottom:16px;padding:16px;">
    <h3 style="font-size:14px;font-weight:600;color:var(--text-primary);margin:0 0 12px 0;">Cost Over Time</h3>
    <canvas id="history-cost-chart" height="180"></canvas>
  </div>

  <!-- Sessions & Crons side by side -->
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:16px;">
    <div class="card" style="padding:16px;">
      <h3 style="font-size:14px;font-weight:600;color:var(--text-primary);margin:0 0 12px 0;">Active Sessions</h3>
      <canvas id="history-sessions-chart" height="160"></canvas>
    </div>
    <div class="card" style="padding:16px;">
      <h3 style="font-size:14px;font-weight:600;color:var(--text-primary);margin:0 0 12px 0;">Cron Runs</h3>
      <div id="history-cron-table" style="max-height:300px;overflow-y:auto;font-size:13px;color:var(--text-secondary);">Loading...</div>
    </div>
  </div>

  <!-- Snapshot drilldown modal -->
  <div id="snapshot-modal" style="display:none;position:fixed;inset:0;z-index:1200;background:rgba(0,0,0,0.5);align-items:center;justify-content:center;">
    <div style="background:var(--bg-primary);border:1px solid var(--border-primary);border-radius:16px;width:90%;max-width:800px;max-height:80vh;padding:24px;overflow-y:auto;box-shadow:0 25px 50px rgba(0,0,0,0.25);">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
        <h3 style="font-size:16px;font-weight:700;color:var(--text-primary);margin:0;" id="snapshot-title">Snapshot</h3>
        <button onclick="document.getElementById('snapshot-modal').style.display='none'" style="background:var(--button-bg);border:1px solid var(--border-primary);border-radius:8px;width:32px;height:32px;cursor:pointer;font-size:18px;color:var(--text-tertiary);">&times;</button>
      </div>
      <pre id="snapshot-content" style="font-size:12px;background:var(--bg-secondary);border:1px solid var(--border-primary);border-radius:8px;padding:16px;overflow-x:auto;white-space:pre-wrap;color:var(--text-secondary);max-height:60vh;"></pre>
    </div>
  </div>
</div>

<!-- FLOW -->
<div class="page" id="page-flow">
  <div class="flow-stats">
    <div class="flow-stat"><span class="flow-stat-label">Messages / min</span><span class="flow-stat-value" id="flow-msg-rate">0</span></div>
    <div class="flow-stat"><span class="flow-stat-label">Actions Taken</span><span class="flow-stat-value" id="flow-event-count">0</span></div>
    <div class="flow-stat"><span class="flow-stat-label">Active Tools</span><span class="flow-stat-value" id="flow-active-tools">&mdash;</span></div>
    <div class="flow-stat"><span class="flow-stat-label">Tokens Used</span><span class="flow-stat-value" id="flow-tokens">&mdash;</span></div>
  </div>
  <div class="flow-container">
    <svg id="flow-svg" viewBox="0 0 980 550" preserveAspectRatio="xMidYMid meet">
      <defs>
        <pattern id="flow-grid" width="40" height="40" patternUnits="userSpaceOnUse">
          <path d="M 40 0 L 0 0 0 40" fill="none" stroke="var(--border-secondary)" stroke-width="0.5"/>
        </pattern>
        <filter id="dropShadow" x="-10%" y="-10%" width="130%" height="130%">
          <feDropShadow dx="0" dy="2" stdDeviation="3" flood-color="rgba(0,0,0,0.25)" flood-opacity="0.4"/>
        </filter>
        <filter id="dropShadowLight" x="-10%" y="-10%" width="130%" height="130%">
          <feDropShadow dx="0" dy="1" stdDeviation="2" flood-color="rgba(0,0,0,0.15)" flood-opacity="0.3"/>
        </filter>
      </defs>
      <rect width="980" height="550" fill="var(--bg-primary)" rx="12"/>
      <rect width="980" height="550" fill="url(#flow-grid)"/>

      <!-- Human -> Channel paths -->
      <path class="flow-path" id="path-human-tg"  d="M 60 56 C 60 70, 65 85, 75 100"/>
      <path class="flow-path" id="path-human-sig" d="M 60 56 C 55 90, 60 140, 75 170"/>
      <path class="flow-path" id="path-human-wa"  d="M 60 56 C 50 110, 55 200, 75 240"/>

      <!-- Channel -> Gateway paths -->
      <path class="flow-path" id="path-tg-gw"  d="M 130 120 C 150 120, 160 165, 180 170"/>
      <path class="flow-path" id="path-sig-gw" d="M 130 190 C 150 190, 160 185, 180 183"/>
      <path class="flow-path" id="path-wa-gw"  d="M 130 260 C 150 260, 160 200, 180 195"/>

      <!-- Gateway -> Brain -->
      <path class="flow-path" id="path-gw-brain" d="M 290 183 C 305 183, 315 175, 330 175"/>

      <!-- Brain -> Tools -->
      <path class="flow-path" id="path-brain-session" d="M 510 155 C 530 130, 545 95, 560 89"/>
      <path class="flow-path" id="path-brain-exec"    d="M 510 160 C 530 150, 545 143, 560 139"/>
      <path class="flow-path" id="path-brain-browser" d="M 510 175 C 530 175, 545 189, 560 189"/>
      <path class="flow-path" id="path-brain-search"  d="M 510 185 C 530 200, 545 230, 560 239"/>
      <path class="flow-path" id="path-brain-cron"    d="M 510 195 C 530 230, 545 275, 560 289"/>
      <path class="flow-path" id="path-brain-tts"     d="M 510 205 C 530 260, 545 325, 560 339"/>
      <path class="flow-path" id="path-brain-memory"  d="M 510 215 C 530 290, 545 370, 560 389"/>

      <!-- Infrastructure paths (dashed) -->
      <path class="flow-path flow-path-infra" id="path-gw-network"    d="M 235 205 C 235 350, 500 400, 590 450"/>
      <path class="flow-path flow-path-infra" id="path-brain-runtime" d="M 380 220 C 300 350, 150 400, 95 450"/>
      <path class="flow-path flow-path-infra" id="path-brain-machine" d="M 420 220 C 380 350, 300 400, 260 450"/>
      <path class="flow-path flow-path-infra" id="path-memory-storage" d="M 615 408 C 550 420, 470 435, 425 450"/>

      <!-- Human Origin -->
      <g class="flow-node flow-node-human" id="node-human">
        <circle cx="60" cy="30" r="22" fill="#7c3aed" stroke="#6a2ec0" stroke-width="2" filter="url(#dropShadow)"/>
        <circle cx="60" cy="24" r="5" fill="#ffffff" opacity="0.6"/>
        <path d="M 50 38 Q 50 45 60 45 Q 70 45 70 38" fill="#ffffff" opacity="0.4"/>
        <text x="60" y="68" style="font-size:13px;fill:#7c3aed;font-weight:800;text-anchor:middle;" id="flow-human-name">You</text>
      </g>

      <!-- Channel Nodes -->
      <g class="flow-node flow-node-channel" id="node-tui" style="display:none;">
        <rect x="20" y="100" width="110" height="40" rx="10" ry="10" fill="#1f2937" stroke="#374151" stroke-width="2" filter="url(#dropShadow)"/>
        <text x="75" y="125" style="font-size:13px;font-weight:700;fill:#ffffff;text-anchor:middle;">⌨️ TUI</text>
      </g>
      <g class="flow-node flow-node-channel" id="node-telegram">
        <rect x="20" y="100" width="110" height="40" rx="10" ry="10" fill="#2196F3" stroke="#1565C0" stroke-width="2" filter="url(#dropShadow)"/>
        <text x="75" y="125" style="font-size:13px;font-weight:700;fill:#ffffff;text-anchor:middle;">📱 TG</text>
      </g>
      <g class="flow-node flow-node-channel" id="node-signal">
        <rect x="20" y="170" width="110" height="40" rx="10" ry="10" fill="#2E8B7A" stroke="#1B6B5A" stroke-width="2" filter="url(#dropShadow)"/>
        <text x="75" y="195" style="font-size:13px;font-weight:700;fill:#ffffff;text-anchor:middle;">📡 Signal</text>
      </g>
      <g class="flow-node flow-node-channel" id="node-imessage" style="display:none;">
        <rect x="20" y="170" width="110" height="40" rx="10" ry="10" fill="#34C759" stroke="#248A3D" stroke-width="2" filter="url(#dropShadow)"/>
        <text x="75" y="195" style="font-size:13px;font-weight:700;fill:#ffffff;text-anchor:middle;">💬 iMessage</text>
      </g>
      <g class="flow-node flow-node-channel" id="node-whatsapp">
        <rect x="20" y="240" width="110" height="40" rx="10" ry="10" fill="#43A047" stroke="#2E7D32" stroke-width="2" filter="url(#dropShadow)"/>
        <text x="75" y="265" style="font-size:13px;font-weight:700;fill:#ffffff;text-anchor:middle;">💬 WA</text>
      </g>
      <g class="flow-node flow-node-channel" id="node-discord" style="display:none;">
        <rect x="20" y="170" width="110" height="40" rx="10" ry="10" fill="#5865F2" stroke="#4752C4" stroke-width="2" filter="url(#dropShadow)"/>
        <text x="75" y="195" style="font-size:13px;font-weight:700;fill:#ffffff;text-anchor:middle;">🎮 Discord</text>
      </g>
      <g class="flow-node flow-node-channel" id="node-slack" style="display:none;">
        <rect x="20" y="170" width="110" height="40" rx="10" ry="10" fill="#4A154B" stroke="#350e36" stroke-width="2" filter="url(#dropShadow)"/>
        <text x="75" y="195" style="font-size:13px;font-weight:700;fill:#ffffff;text-anchor:middle;">💼 Slack</text>
      </g>
      <g class="flow-node flow-node-channel" id="node-irc" style="display:none;">
        <rect x="20" y="170" width="110" height="40" rx="10" ry="10" fill="#6B7280" stroke="#4B5563" stroke-width="2" filter="url(#dropShadow)"/>
        <text x="75" y="195" style="font-size:13px;font-weight:700;fill:#ffffff;text-anchor:middle;"># IRC</text>
      </g>
      <g class="flow-node flow-node-channel" id="node-webchat" style="display:none;">
        <rect x="20" y="170" width="110" height="40" rx="10" ry="10" fill="#0EA5E9" stroke="#0369A1" stroke-width="2" filter="url(#dropShadow)"/>
        <text x="75" y="195" style="font-size:13px;font-weight:700;fill:#ffffff;text-anchor:middle;">🌐 WebChat</text>
      </g>
      <g class="flow-node flow-node-channel" id="node-googlechat" style="display:none;">
        <rect x="20" y="170" width="110" height="40" rx="10" ry="10" fill="#1A73E8" stroke="#1557B0" stroke-width="2" filter="url(#dropShadow)"/>
        <text x="75" y="195" style="font-size:13px;font-weight:700;fill:#ffffff;text-anchor:middle;">💬 GChat</text>
      </g>
      <g class="flow-node flow-node-channel" id="node-bluebubbles" style="display:none;">
        <rect x="20" y="170" width="110" height="40" rx="10" ry="10" fill="#1C6EF3" stroke="#1558C0" stroke-width="2" filter="url(#dropShadow)"/>
        <text x="75" y="195" style="font-size:13px;font-weight:700;fill:#ffffff;text-anchor:middle;">🍎 BB</text>
      </g>
      <g class="flow-node flow-node-channel" id="node-msteams" style="display:none;">
        <rect x="20" y="170" width="110" height="40" rx="10" ry="10" fill="#6264A7" stroke="#464775" stroke-width="2" filter="url(#dropShadow)"/>
        <text x="75" y="195" style="font-size:13px;font-weight:700;fill:#ffffff;text-anchor:middle;">👔 Teams</text>
      </g>
      <g class="flow-node flow-node-channel" id="node-matrix" style="display:none;">
        <rect x="20" y="170" width="110" height="40" rx="10" ry="10" fill="#0DBD8B" stroke="#0A9E74" stroke-width="2" filter="url(#dropShadow)"/>
        <text x="75" y="195" style="font-size:13px;font-weight:700;fill:#ffffff;text-anchor:middle;">[M] Matrix</text>
      </g>
      <g class="flow-node flow-node-channel" id="node-mattermost" style="display:none;">
        <rect x="20" y="170" width="110" height="40" rx="10" ry="10" fill="#0058CC" stroke="#0047A3" stroke-width="2" filter="url(#dropShadow)"/>
        <text x="75" y="195" style="font-size:13px;font-weight:700;fill:#ffffff;text-anchor:middle;">⚓ MM</text>
      </g>
      <g class="flow-node flow-node-channel" id="node-line" style="display:none;">
        <rect x="20" y="170" width="110" height="40" rx="10" ry="10" fill="#00B900" stroke="#009900" stroke-width="2" filter="url(#dropShadow)"/>
        <text x="75" y="195" style="font-size:13px;font-weight:700;fill:#ffffff;text-anchor:middle;">💚 LINE</text>
      </g>
      <g class="flow-node flow-node-channel" id="node-nostr" style="display:none;">
        <rect x="20" y="170" width="110" height="40" rx="10" ry="10" fill="#8B5CF6" stroke="#6D28D9" stroke-width="2" filter="url(#dropShadow)"/>
        <text x="75" y="195" style="font-size:13px;font-weight:700;fill:#ffffff;text-anchor:middle;">⚡ Nostr</text>
      </g>
      <g class="flow-node flow-node-channel" id="node-twitch" style="display:none;">
        <rect x="20" y="170" width="110" height="40" rx="10" ry="10" fill="#9146FF" stroke="#772CE8" stroke-width="2" filter="url(#dropShadow)"/>
        <text x="75" y="195" style="font-size:13px;font-weight:700;fill:#ffffff;text-anchor:middle;">🎮 Twitch</text>
      </g>
      <g class="flow-node flow-node-channel" id="node-feishu" style="display:none;">
        <rect x="20" y="170" width="110" height="40" rx="10" ry="10" fill="#3370FF" stroke="#2050CC" stroke-width="2" filter="url(#dropShadow)"/>
        <text x="75" y="195" style="font-size:13px;font-weight:700;fill:#ffffff;text-anchor:middle;">🌸 Feishu</text>
      </g>
      <g class="flow-node flow-node-channel" id="node-zalo" style="display:none;">
        <rect x="20" y="170" width="110" height="40" rx="10" ry="10" fill="#0068FF" stroke="#0050CC" stroke-width="2" filter="url(#dropShadow)"/>
        <text x="75" y="195" style="font-size:13px;font-weight:700;fill:#ffffff;text-anchor:middle;">💬 Zalo</text>
      </g>

      <!-- Gateway -->
      <g class="flow-node flow-node-gateway" id="node-gateway">
        <rect x="180" y="160" width="110" height="45" rx="10" ry="10" fill="#37474F" stroke="#263238" stroke-width="2" filter="url(#dropShadow)"/>
        <text x="235" y="188" style="font-size:13px;font-weight:700;fill:#ffffff;text-anchor:middle;">🔀 Gateway</text>
      </g>

      <!-- Brain -->
      <g class="flow-node flow-node-brain brain-group" id="node-brain">
        <rect x="330" y="130" width="180" height="90" rx="12" ry="12" fill="#C62828" stroke="#B71C1C" stroke-width="3" filter="url(#dropShadow)"/>
        <text x="420" y="162" style="font-size:24px;text-anchor:middle;">&#x1F9E0;</text>
        <text x="420" y="186" style="font-size:18px;font-weight:800;fill:#FFD54F;text-anchor:middle;" id="brain-model-label">AI Model</text>
        <text x="420" y="203" style="font-size:10px;fill:#c7d2fe;text-anchor:middle;" id="brain-model-text">unknown</text>
        <text x="420" y="214" style="font-size:8px;fill:#a5b4fc;text-anchor:middle;" id="brain-billing-text">Auth: unknown</text>
        <circle cx="420" cy="225" r="4" fill="#FF8A65">
          <animate attributeName="r" values="3;5;3" dur="1.1s" repeatCount="indefinite"/>
          <animate attributeName="opacity" values="0.5;1;0.5" dur="1.1s" repeatCount="indefinite"/>
        </circle>
      </g>

      <!-- Tool Nodes -->
      <g class="flow-node flow-node-session" id="node-session">
        <rect x="560" y="70" width="110" height="38" rx="10" ry="10" fill="#1565C0" stroke="#0D47A1" stroke-width="2" filter="url(#dropShadow)"/>
        <text x="615" y="94" style="font-size:13px;font-weight:700;fill:#ffffff;text-anchor:middle;">📋 Sessions</text>
        <circle class="tool-indicator" id="ind-session" cx="665" cy="78" r="5" fill="#42A5F5"/>
      </g>
      <g class="flow-node flow-node-tool" id="node-exec">
        <rect x="560" y="120" width="110" height="38" rx="10" ry="10" fill="#E65100" stroke="#BF360C" stroke-width="2" filter="url(#dropShadow)"/>
        <text x="615" y="144" style="font-size:13px;font-weight:700;fill:#ffffff;text-anchor:middle;">⚡ Exec</text>
        <circle class="tool-indicator" id="ind-exec" cx="665" cy="128" r="5" fill="#FF6E40"/>
      </g>
      <g class="flow-node flow-node-tool" id="node-browser">
        <rect x="560" y="170" width="110" height="38" rx="10" ry="10" fill="#6A1B9A" stroke="#4A148C" stroke-width="2" filter="url(#dropShadow)"/>
        <text x="615" y="194" style="font-size:13px;font-weight:700;fill:#ffffff;text-anchor:middle;">🌐 Web</text>
        <circle class="tool-indicator" id="ind-browser" cx="665" cy="178" r="5" fill="#CE93D8"/>
      </g>
      <g class="flow-node flow-node-tool" id="node-search">
        <rect x="560" y="220" width="110" height="38" rx="10" ry="10" fill="#00695C" stroke="#004D40" stroke-width="2" filter="url(#dropShadow)"/>
        <text x="615" y="244" style="font-size:13px;font-weight:700;fill:#ffffff;text-anchor:middle;">&#x1F50D; Search</text>
        <circle class="tool-indicator" id="ind-search" cx="665" cy="228" r="5" fill="#4DB6AC"/>
      </g>
      <g class="flow-node flow-node-tool" id="node-cron">
        <rect x="560" y="270" width="110" height="38" rx="10" ry="10" fill="#546E7A" stroke="#37474F" stroke-width="2" filter="url(#dropShadow)"/>
        <text x="615" y="294" style="font-size:13px;font-weight:700;fill:#ffffff;text-anchor:middle;">📅 Cron</text>
        <circle class="tool-indicator" id="ind-cron" cx="665" cy="278" r="5" fill="#90A4AE"/>
      </g>
      <g class="flow-node flow-node-tool" id="node-tts">
        <rect x="560" y="320" width="110" height="38" rx="10" ry="10" fill="#F9A825" stroke="#F57F17" stroke-width="2" filter="url(#dropShadow)"/>
        <text x="615" y="344" style="font-size:13px;font-weight:700;fill:#ffffff;text-anchor:middle;">&#x1F5E3;&#xFE0F; TTS</text>
        <circle class="tool-indicator" id="ind-tts" cx="665" cy="328" r="5" fill="#FFF176"/>
      </g>
      <g class="flow-node flow-node-tool" id="node-memory">
        <rect x="560" y="370" width="110" height="38" rx="10" ry="10" fill="#283593" stroke="#1A237E" stroke-width="2" filter="url(#dropShadow)"/>
        <text x="615" y="394" style="font-size:13px;font-weight:700;fill:#ffffff;text-anchor:middle;">&#x1F4BE; Memory</text>
        <circle class="tool-indicator" id="ind-memory" cx="665" cy="378" r="5" fill="#7986CB"/>
      </g>

      <!-- Cost Optimizer -->
      <g class="flow-node flow-node-optimizer" id="node-cost-optimizer">
        <rect x="680" y="370" width="145" height="44" rx="12" ry="12" fill="#2E7D32" stroke="#1B5E20" stroke-width="2" filter="url(#dropShadow)"/>
        <text x="752" y="389" style="font-size:12px;font-weight:700;fill:#ffffff;text-anchor:middle;">
          <tspan x="752" dy="-5">&#x1F4B0; Cost</tspan>
          <tspan x="752" dy="13">Optimizer</tspan>
        </text>
        <circle class="tool-indicator" id="ind-cost-optimizer" cx="817" cy="378" r="5" fill="#66BB6A"/>
      </g>

      <!-- Automation Advisor -->
      <g class="flow-node flow-node-advisor" id="node-automation-advisor">
        <rect x="835" y="370" width="145" height="44" rx="12" ry="12" fill="#7B1FA2" stroke="#4A148C" stroke-width="2" filter="url(#dropShadow)"/>
        <text x="907" y="389" style="font-size:12px;font-weight:700;fill:#ffffff;text-anchor:middle;">
          <tspan x="907" dy="-5">&#x1F9E0; Automation</tspan>
          <tspan x="907" dy="13">Advisor</tspan>
        </text>
        <circle class="tool-indicator" id="ind-automation-advisor" cx="972" cy="378" r="5" fill="#BA68C8"/>
      </g>

      <!-- Infrastructure Layer -->
      <line class="flow-ground" x1="20" y1="440" x2="970" y2="440"/>
      <text class="flow-ground-label" x="400" y="438" style="text-anchor:middle;font-size:10px;">I N F R A S T R U C T U R E</text>

      <g class="flow-node flow-node-infra flow-node-runtime" id="node-runtime">
        <rect x="30" y="450" width="130" height="40" rx="8" ry="8" fill="#455A64" stroke="#37474F" filter="url(#dropShadowLight)"/>
        <text x="95" y="466" style="font-size:13px;fill:#ffffff;font-weight:700;text-anchor:middle;">&#x2699;&#xFE0F; Runtime</text>
        <text class="infra-sub" x="95" y="480" style="fill:#B0BEC5;font-size:8px;text-anchor:middle;" id="infra-runtime-text">Node.js - Linux</text>
      </g>
      <g class="flow-node flow-node-infra flow-node-machine" id="node-machine">
        <rect x="195" y="450" width="130" height="40" rx="8" ry="8" fill="#4E342E" stroke="#3E2723" filter="url(#dropShadowLight)"/>
        <text x="260" y="466" style="font-size:13px;fill:#ffffff;font-weight:700;text-anchor:middle;">&#x1F5A5;&#xFE0F; Machine</text>
        <text class="infra-sub" x="260" y="480" style="fill:#BCAAA4;font-size:8px;text-anchor:middle;" id="infra-machine-text">Host</text>
      </g>
      <g class="flow-node flow-node-infra flow-node-storage" id="node-storage">
        <rect x="360" y="450" width="130" height="40" rx="8" ry="8" fill="#5D4037" stroke="#4E342E" filter="url(#dropShadowLight)"/>
        <text x="425" y="466" style="font-size:13px;fill:#ffffff;font-weight:700;text-anchor:middle;">&#x1F4BF; Storage</text>
        <text class="infra-sub" x="425" y="480" style="fill:#BCAAA4;font-size:8px;text-anchor:middle;" id="infra-storage-text">Disk</text>
      </g>
      <g class="flow-node flow-node-infra flow-node-network" id="node-network">
        <rect x="525" y="450" width="130" height="40" rx="8" ry="8" fill="#004D40" stroke="#00332E" filter="url(#dropShadowLight)"/>
        <text x="590" y="466" style="font-size:13px;fill:#ffffff;font-weight:700;text-anchor:middle;">&#x1F310; Network</text>
        <text class="infra-sub" x="590" y="480" style="fill:#80CBC4;font-size:8px;text-anchor:middle;" id="infra-network-text">LAN</text>
      </g>

      <!-- Legend -->
      <g transform="translate(140, 510)">
        <rect x="0" y="0" width="700" height="28" rx="14" ry="14" fill="var(--bg-tertiary)" stroke="var(--border-primary)" stroke-width="1" opacity="0.9"/>
        <text x="350" y="18" style="font-size:12px;font-weight:600;fill:var(--text-secondary);letter-spacing:1px;text-anchor:middle;">&#x1F4E8; Channels  &#x27A1;&#xFE0F;  🔀 Gateway  &#x27A1;&#xFE0F;  &#x1F9E0; AI Brain  &#x27A1;&#xFE0F;  &#x1F6E0;&#xFE0F; Tools</text>
      </g>

      <!-- Flow direction labels -->
      <text class="flow-label" x="120" y="155" style="font-size:9px;">messages in</text>
      <text class="flow-label" x="300" y="155" style="font-size:9px;">routes to AI</text>
      <text class="flow-label" x="520" y="155" style="font-size:9px;">uses tools</text>
    </svg>
  </div>

  <!-- Live Tool Call Stream -->
  <div style="margin-top:12px;background:var(--bg-secondary,#111128);border:1px solid var(--border-secondary,#2a2a4a);border-radius:10px;padding:12px 16px;">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;flex-wrap:wrap;gap:8px;">
      <span style="font-size:13px;font-weight:600;color:#aaa;">&#128295; Live Tool Call Stream</span>
      <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
        <input id="tool-stream-filter" type="text" placeholder="Filter by tool&hellip;" oninput="applyToolStreamFilter()" style="font-size:11px;padding:3px 8px;border:1px solid var(--border-secondary,#2a2a4a);border-radius:6px;background:var(--bg-primary,#0a0a1a);color:#aaa;width:130px;outline:none;">
        <button id="tool-stream-pause-btn" onclick="toggleToolStreamPause()" style="font-size:11px;padding:3px 10px;border:1px solid var(--border-secondary,#2a2a4a);border-radius:6px;background:var(--bg-primary,#0a0a1a);color:#aaa;cursor:pointer;">&#9646;&#9646; Pause</button>
        <button onclick="clearToolStream()" style="font-size:11px;padding:3px 10px;border:1px solid var(--border-secondary,#2a2a4a);border-radius:6px;background:var(--bg-primary,#0a0a1a);color:#aaa;cursor:pointer;">&#10005; Clear</button>
        <span style="font-size:10px;color:#555;" id="flow-feed-count">0 events</span>
      </div>
    </div>
    <div id="flow-live-feed" style="max-height:350px;overflow-y:auto;font-family:'SF Mono',monospace;font-size:11px;line-height:1.6;color:#777;">
      <div style="color:#555;">Waiting for activity...</div>
    </div>
  </div>
</div><!-- end page-flow -->

<!-- BRAIN -->
<div class="page" id="page-brain">
  <div style="padding:12px 0 8px 0;">
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;">
      <span style="font-size:14px;font-weight:700;color:var(--text-primary);">🧠 Brain -- Unified Activity Stream</span>
      <button class="refresh-btn" onclick="loadBrainPage()">↻ Refresh</button>
    </div>
    <!-- Activity density chart -->
    <div style="background:var(--bg-secondary);border:1px solid var(--border);border-radius:8px;padding:10px 14px;margin-bottom:12px;">
      <div style="font-size:11px;color:var(--text-muted);margin-bottom:6px;">Activity density -- last 60 min (30s buckets)</div>
      <canvas id="brain-density-chart" height="60" style="width:100%;display:block;"></canvas>
    </div>
    <div class="brain-view-toggle">
      
    </div>
    <!-- Source filter chips -->
    <div id="brain-filter-chips" style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:6px;">
      <button class="brain-chip active" data-source="all" onclick="setBrainFilter('all',this)" style="padding:3px 10px;border-radius:12px;border:1px solid #a855f7;background:rgba(168,85,247,0.2);color:#a855f7;font-size:11px;cursor:pointer;font-weight:600;">All</button>
    </div>
    <!-- Type filter chips (separate container to prevent duplication) -->
    <div id="brain-type-chips" style="display:flex;flex-wrap:wrap;gap:5px;margin-bottom:10px;"></div>
    <!-- Event stream -->
    <div id="brain-feed" style="background:var(--bg-secondary);border:1px solid var(--border);border-radius:8px;padding:10px 14px;">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
        <span style="font-size:11px;color:var(--text-muted);">Live event stream (newest first)</span>
        <span id="brain-new-pill" style="display:none;background:#a855f7;color:#fff;border-radius:10px;padding:1px 8px;font-size:10px;font-weight:700;cursor:pointer;" onclick="scrollBrainToTop()">↑ new events</span>
      </div>
      <div id="brain-stream" style="max-height:calc(100vh - 320px);overflow-y:auto;">
        <div style="color:var(--text-muted);padding:20px">Loading...</div>
      </div>
    </div>
    <div id="brain-graph-wrap" class="brain-graph-container" style="display:none;">
      <canvas id="brain-graph-canvas"></canvas>
    </div>
  </div>
</div><!-- end page-brain -->

<!-- SECURITY -->
<div class="page" id="page-security">
  <div style="padding:12px 0 8px 0;">
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;">
      <span style="font-size:14px;font-weight:700;color:var(--text-primary);">&#128737;&#65039; Security</span>
      <div style="display:flex;gap:8px;align-items:center;">
        <span id="security-scan-time" style="font-size:11px;color:var(--text-muted);"></span>
        <button class="refresh-btn" onclick="loadSecurityPage();loadSecurityPosture();">&#8635; Scan</button>
      </div>
    </div>
    <!-- Security Posture Score -->
    <div id="security-posture-panel" style="background:var(--bg-secondary);border:1px solid var(--border);border-radius:8px;padding:16px;margin-bottom:14px;">
      <div style="display:flex;align-items:center;gap:16px;margin-bottom:12px;">
        <div id="posture-score-badge" style="width:64px;height:64px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:28px;font-weight:800;color:#fff;background:#64748b;flex-shrink:0;">?</div>
        <div style="flex:1;">
          <div style="font-size:13px;font-weight:700;color:var(--text-primary);">Security Posture</div>
          <div id="posture-score-label" style="font-size:11px;color:var(--text-muted);margin-top:2px;">Scanning configuration...</div>
          <div style="margin-top:6px;background:var(--bg-primary);border-radius:4px;height:6px;overflow:hidden;">
            <div id="posture-score-bar" style="height:100%;width:0%;background:#64748b;border-radius:4px;transition:width 0.5s ease;"></div>
          </div>
        </div>
        <div style="display:flex;gap:12px;flex-shrink:0;">
          <div style="text-align:center;"><div id="posture-passed" style="font-size:18px;font-weight:700;color:#22c55e;">-</div><div style="font-size:10px;color:var(--text-muted);">Passed</div></div>
          <div style="text-align:center;"><div id="posture-warnings" style="font-size:18px;font-weight:700;color:#f59e0b;">-</div><div style="font-size:10px;color:var(--text-muted);">Warnings</div></div>
          <div style="text-align:center;"><div id="posture-failed" style="font-size:18px;font-weight:700;color:#ef4444;">-</div><div style="font-size:10px;color:var(--text-muted);">Failed</div></div>
        </div>
      </div>
      <div id="posture-checks-list" style="display:grid;gap:6px;"></div>
    </div>
    <!-- Threat Detection -->
    <div style="font-size:13px;font-weight:700;color:var(--text-primary);margin-bottom:10px;">Threat Detection &amp; Anomaly Alerts</div>
    <div id="security-summary" style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:14px;">
      <div style="background:var(--bg-secondary);border:1px solid var(--border);border-radius:8px;padding:12px;text-align:center;">
        <div style="font-size:24px;font-weight:700;color:#ef4444;" id="sec-critical-count">0</div>
        <div style="font-size:11px;color:var(--text-muted);">Critical</div>
      </div>
      <div style="background:var(--bg-secondary);border:1px solid var(--border);border-radius:8px;padding:12px;text-align:center;">
        <div style="font-size:24px;font-weight:700;color:#f59e0b;" id="sec-high-count">0</div>
        <div style="font-size:11px;color:var(--text-muted);">High</div>
      </div>
      <div style="background:var(--bg-secondary);border:1px solid var(--border);border-radius:8px;padding:12px;text-align:center;">
        <div style="font-size:24px;font-weight:700;color:#3b82f6;" id="sec-medium-count">0</div>
        <div style="font-size:11px;color:var(--text-muted);">Medium</div>
      </div>
      <div style="background:var(--bg-secondary);border:1px solid var(--border);border-radius:8px;padding:12px;text-align:center;">
        <div style="font-size:24px;font-weight:700;color:#22c55e;" id="sec-clean-count">0</div>
        <div style="font-size:11px;color:var(--text-muted);">Clean Sessions</div>
      </div>
    </div>
    <div id="security-filter-pills" style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:10px;">
      <button class="brain-chip active" data-severity="all" onclick="setSecurityFilter('all',this)" style="padding:3px 10px;border-radius:12px;border:1px solid #a855f7;background:rgba(168,85,247,0.2);color:#a855f7;font-size:11px;cursor:pointer;font-weight:600;">All</button>
      <button class="brain-chip" data-severity="critical" onclick="setSecurityFilter('critical',this)" style="padding:3px 10px;border-radius:12px;border:1px solid #ef4444;background:transparent;color:#ef4444;font-size:11px;cursor:pointer;font-weight:600;">Critical</button>
      <button class="brain-chip" data-severity="high" onclick="setSecurityFilter('high',this)" style="padding:3px 10px;border-radius:12px;border:1px solid #f59e0b;background:transparent;color:#f59e0b;font-size:11px;cursor:pointer;font-weight:600;">High</button>
      <button class="brain-chip" data-severity="medium" onclick="setSecurityFilter('medium',this)" style="padding:3px 10px;border-radius:12px;border:1px solid #3b82f6;background:transparent;color:#3b82f6;font-size:11px;cursor:pointer;font-weight:600;">Medium</button>
      <button class="brain-chip" data-severity="low" onclick="setSecurityFilter('low',this)" style="padding:3px 10px;border-radius:12px;border:1px solid #64748b;background:transparent;color:#64748b;font-size:11px;cursor:pointer;font-weight:600;">Low</button>
    </div>
    <div style="background:var(--bg-secondary);border:1px solid var(--border);border-radius:8px;padding:10px 14px;">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
        <span style="font-size:11px;color:var(--text-muted);">Threat timeline (newest first)</span>
        <span id="sec-total-label" style="font-size:11px;color:var(--text-muted);"></span>
      </div>
      <div id="security-threat-list" style="max-height:600px;overflow-y:auto;">
        <div style="color:var(--text-muted);padding:20px">Scanning...</div>
      </div>
    </div>
    <div style="margin-top:14px;background:var(--bg-secondary);border:1px solid var(--border);border-radius:8px;padding:10px 14px;">
      <div style="font-size:12px;font-weight:700;color:var(--text-primary);margin-bottom:8px;cursor:pointer;" onclick="toggleSecCatalog()">&#128203; Signature Catalog <span id="sec-catalog-arrow" style="font-size:10px;">&#9654;</span></div>
      <div id="sec-catalog" style="display:none;"></div>
    </div>
  </div>
</div><!-- end page-security -->

<!-- MODEL ATTRIBUTION -->
<div class="page" id="page-models">
  <div class="refresh-bar">
    <button class="refresh-btn" onclick="loadModelAttribution()">&#x21bb; Refresh</button>
  </div>
  <div class="grid" id="model-stats-grid">
    <div class="card">
      <div class="card-title"><span class="icon">🤖</span> Primary Model</div>
      <div class="card-value" id="model-primary">--</div>
      <div class="card-sub" id="model-primary-pct"></div>
    </div>
    <div class="card">
      <div class="card-title"><span class="icon">🔄</span> Model Diversity</div>
      <div class="card-value" id="model-count">--</div>
      <div class="card-sub">distinct models used</div>
    </div>
    <div class="card">
      <div class="card-title"><span class="icon">⚡</span> Fallback Rate</div>
      <div class="card-value" id="model-fallback-rate">--</div>
      <div class="card-sub" id="model-fallback-detail"></div>
    </div>
    <div class="card">
      <div class="card-title"><span class="icon">💬</span> Total Turns</div>
      <div class="card-value" id="model-total-turns">--</div>
      <div class="card-sub">assistant responses tracked</div>
    </div>
  </div>
  <div class="section-title">🤖 Model Mix</div>
  <div class="card" id="model-mix-card">
    <div id="model-mix-chart" style="padding:8px 0;">Loading...</div>
  </div>
  <div class="section-title">📊 Per-Session Breakdown</div>
  <div class="card">
    <table class="usage-table" id="model-sessions-table" style="width:100%;">
      <thead><tr>
        <th style="text-align:left;padding:6px 8px;color:var(--text-secondary);font-size:12px;">Model</th>
        <th style="text-align:right;padding:6px 8px;color:var(--text-secondary);font-size:12px;">Sessions</th>
        <th style="text-align:right;padding:6px 8px;color:var(--text-secondary);font-size:12px;">Turns</th>
        <th style="text-align:right;padding:6px 8px;color:var(--text-secondary);font-size:12px;">Share</th>
      </tr></thead>
      <tbody><tr><td colspan="4" style="color:#666;padding:8px;">Loading...</td></tr></tbody>
    </table>
  </div>
  <div id="model-switches-section" style="display:none;">
    <div class="section-title">🔀 Model Switches <span id="model-switches-count" style="font-size:13px;color:var(--text-muted);font-weight:400;"></span></div>
    <div class="card">
      <table class="usage-table" id="model-switches-table" style="width:100%;">
        <thead><tr>
          <th style="text-align:left;padding:6px 8px;color:var(--text-secondary);font-size:12px;">Session</th>
          <th style="text-align:left;padding:6px 8px;color:var(--text-secondary);font-size:12px;">From</th>
          <th style="text-align:left;padding:6px 8px;color:var(--text-secondary);font-size:12px;">To</th>
        </tr></thead>
        <tbody><tr><td colspan="3" style="color:#666;padding:8px;">Loading...</td></tr></tbody>
      </table>
    </div>
  </div>
</div><!-- end page-models -->

<!-- NEMOCLAW GOVERNANCE -->
<div class="page" id="page-nemoclaw">
  <div style="padding:12px 0 8px 0;">
    <!-- Header row -->
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:14px;">
      <div style="display:flex;align-items:center;gap:10px;">
        <span id="nc-status-dot" style="font-size:18px;">🟢</span>
        <span style="font-size:14px;font-weight:700;color:#76b900;">NemoClaw</span>
        <span id="nc-sandbox-name" style="font-size:12px;background:rgba(118,185,0,0.15);color:#76b900;border:1px solid rgba(118,185,0,0.3);border-radius:12px;padding:2px 10px;font-weight:600;"></span>
        <span id="nc-blueprint-ver" style="font-size:12px;background:var(--bg-secondary);color:var(--text-muted);border:1px solid var(--border);border-radius:12px;padding:2px 10px;"></span>
      </div>
      <button class="refresh-btn" onclick="loadNemoClaw()">&#8635; Refresh</button>
    </div>
    <!-- Two-column info grid -->
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px;">
      <!-- Sandbox panel -->
      <div style="background:var(--bg-secondary);border:1px solid var(--border);border-radius:8px;padding:14px;">
        <div style="font-size:11px;font-weight:700;color:#76b900;letter-spacing:1px;margin-bottom:10px;">SANDBOX</div>
        <table style="width:100%;border-collapse:collapse;font-size:12px;">
          <tr><td style="color:var(--text-muted);padding:3px 0;width:45%;">Status</td><td id="nc-sandbox-status" style="color:var(--text-primary);font-family:\'JetBrains Mono\',monospace;">&#8212;</td></tr>
          <tr><td style="color:var(--text-muted);padding:3px 0;">Blueprint</td><td id="nc-blueprint-ver2" style="color:var(--text-primary);font-family:\'JetBrains Mono\',monospace;">&#8212;</td></tr>
          <tr><td style="color:var(--text-muted);padding:3px 0;">Last action</td><td id="nc-last-action" style="color:var(--text-primary);font-family:\'JetBrains Mono\',monospace;max-width:160px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">&#8212;</td></tr>
          <tr><td style="color:var(--text-muted);padding:3px 0;">Run ID</td><td id="nc-run-id" style="color:var(--text-tertiary);font-family:\'JetBrains Mono\',monospace;font-size:11px;">&#8212;</td></tr>
        </table>
      </div>
      <!-- Inference panel -->
      <div style="background:var(--bg-secondary);border:1px solid var(--border);border-radius:8px;padding:14px;">
        <div style="font-size:11px;font-weight:700;color:#76b900;letter-spacing:1px;margin-bottom:10px;">INFERENCE</div>
        <table style="width:100%;border-collapse:collapse;font-size:12px;">
          <tr><td style="color:var(--text-muted);padding:3px 0;width:45%;">Provider</td><td id="nc-provider" style="color:var(--text-primary);font-family:\'JetBrains Mono\',monospace;">&#8212;</td></tr>
          <tr><td style="color:var(--text-muted);padding:3px 0;">Model</td><td id="nc-model" style="color:var(--text-primary);font-family:\'JetBrains Mono\',monospace;max-width:160px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">&#8212;</td></tr>
          <tr><td style="color:var(--text-muted);padding:3px 0;">Endpoint</td><td id="nc-endpoint" style="color:var(--text-tertiary);font-family:\'JetBrains Mono\',monospace;font-size:11px;max-width:160px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">&#8212;</td></tr>
          <tr><td style="color:var(--text-muted);padding:3px 0;">Onboarded</td><td id="nc-onboarded" style="color:var(--text-tertiary);font-family:\'JetBrains Mono\',monospace;font-size:11px;">&#8212;</td></tr>
        </table>
      </div>
    </div>
    <!-- Active Policy -->
    <div style="background:var(--bg-secondary);border:1px solid var(--border);border-radius:8px;padding:14px;margin-bottom:12px;">
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">
        <span style="font-size:11px;font-weight:700;color:#76b900;letter-spacing:1px;">ACTIVE POLICY</span>
        <span id="nc-policy-hash" style="font-size:11px;color:var(--text-muted);font-family:\'JetBrains Mono\',monospace;background:var(--bg-primary);border:1px solid var(--border-secondary);border-radius:4px;padding:1px 6px;"></span>
        <span id="nc-drift-badge" style="font-size:11px;font-weight:600;"></span>
      </div>
      <!-- Drift alert -->
      <div id="nc-drift-alert" style="display:none;background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.3);border-radius:6px;padding:10px;margin-bottom:10px;">
        <div style="font-size:12px;font-weight:700;color:#ef4444;">&#9888;&#65039; Policy drift detected</div>
        <div id="nc-drift-detail" style="font-size:11px;color:var(--text-muted);margin-top:4px;font-family:\'JetBrains Mono\',monospace;"></div>
      </div>
      <!-- Network policies table -->
      <div id="nc-policy-table" style="font-family:\'JetBrains Mono\',\'SF Mono\',monospace;font-size:12px;line-height:1.8;">
        <div style="color:var(--text-muted);padding:8px 0;">Loading policy...</div>
      </div>
    </div>
    <!-- Applied Presets -->
    <div style="background:var(--bg-secondary);border:1px solid var(--border);border-radius:8px;padding:14px;margin-bottom:12px;">
      <div style="font-size:11px;font-weight:700;color:#76b900;letter-spacing:1px;margin-bottom:10px;">APPLIED PRESETS</div>
      <div id="nc-presets" style="display:flex;flex-wrap:wrap;gap:6px;">
        <span style="color:var(--text-muted);font-size:12px;">None detected</span>
      </div>
    </div>
    <!-- Egress Approvals Panel -->
    <div style="background:var(--bg-secondary);border:1px solid rgba(118,185,0,0.35);border-radius:8px;padding:14px;" id="nc-approvals-panel">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;">
        <div style="display:flex;align-items:center;gap:8px;">
          <span style="font-size:11px;font-weight:700;color:#76b900;letter-spacing:1px;">PENDING EGRESS APPROVALS</span>
          <span id="nc-approvals-count" style="display:none;font-size:11px;font-weight:700;background:rgba(239,68,68,0.15);color:#ef4444;border:1px solid rgba(239,68,68,0.3);border-radius:10px;padding:1px 8px;"></span>
        </div>
        <button class="refresh-btn" onclick="loadNemoClawApprovals()" style="font-size:11px;">&#8635; Refresh</button>
      </div>
      <div id="nc-approvals-list">
        <div style="color:var(--text-muted);font-size:12px;padding:8px 0;">Loading...</div>
      </div>
    </div>
  </div>
</div><!-- end page-nemoclaw -->

<!-- SELF-CONFIG DIFF VIEWER -->
<div class="page" id="page-selfconfig">
  <div style="padding:12px 0 8px 0;">
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:14px;">
      <div style="display:flex;align-items:center;gap:10px;">
        <span style="font-size:14px;font-weight:700;color:var(--text-primary);">Self-Configuration History</span>
        <span style="font-size:11px;color:var(--text-muted);background:var(--bg-secondary);border:1px solid var(--border);border-radius:12px;padding:2px 10px;">agent-managed files</span>
      </div>
      <button class="refresh-btn" onclick="loadSelfConfig()">&#8635; Refresh</button>
    </div>
    <!-- Two-column layout: file list + detail pane -->
    <div style="display:grid;grid-template-columns:220px 1fr;gap:12px;min-height:400px;">
      <!-- File list (left) -->
      <div id="selfconfig-file-list" style="background:var(--bg-secondary);border:1px solid var(--border);border-radius:8px;padding:10px;">
        <div style="font-size:11px;font-weight:700;color:var(--text-muted);letter-spacing:1px;margin-bottom:8px;">TRACKED FILES</div>
        <div id="selfconfig-files-inner" style="color:var(--text-muted);font-size:12px;">Loading...</div>
      </div>
      <!-- Detail pane (right) -->
      <div id="selfconfig-detail-pane" style="background:var(--bg-secondary);border:1px solid var(--border);border-radius:8px;padding:14px;">
        <div id="selfconfig-empty-state" style="color:var(--text-muted);font-size:13px;padding:24px 0;text-align:center;">
          Select a file on the left to view its revision history.
        </div>
        <div id="selfconfig-revisions-panel" style="display:none;">
          <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;">
            <div style="font-size:13px;font-weight:700;color:var(--text-primary);" id="selfconfig-filename-heading"></div>
            <div id="selfconfig-values-badge" style="display:none;background:rgba(251,146,60,0.15);color:#fb923c;border:1px solid rgba(251,146,60,0.4);border-radius:10px;padding:2px 10px;font-size:11px;font-weight:700;">&#9888; VALUES FILE</div>
          </div>
          <div id="selfconfig-revisions-list" style="font-size:12px;"></div>
        </div>
        <div id="selfconfig-diff-panel" style="display:none;">
          <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">
            <button onclick="selfconfigBackToRevisions()" style="background:var(--bg-primary);border:1px solid var(--border);border-radius:6px;padding:4px 10px;font-size:11px;cursor:pointer;color:var(--text-secondary);">&#8592; Back</button>
            <span style="font-size:12px;font-weight:700;color:var(--text-primary);" id="selfconfig-diff-heading"></span>
            <span id="selfconfig-diff-stats" style="font-size:11px;color:var(--text-muted);"></span>
          </div>
          <div id="selfconfig-diff-content" style="font-family:\'JetBrains Mono\',\'SF Mono\',monospace;font-size:12px;line-height:1.6;overflow-x:auto;"></div>
        </div>
      </div>
    </div>
    <!-- Empty state when no edits ever detected -->
    <div id="selfconfig-no-history-msg" style="display:none;margin-top:16px;background:var(--bg-secondary);border:1px solid var(--border);border-radius:8px;padding:20px;text-align:center;">
      <div style="font-size:13px;color:var(--text-muted);">No self-configuration edits yet. ClawMetry snapshots these files and shows diffs when your agent updates them.</div>
    </div>
  </div>
</div><!-- end page-selfconfig -->

<!-- SUB-AGENT TREE -->
<div class="page" id="page-subagents">
  <div class="refresh-bar">
    <h2 style="font-size:16px;font-weight:700;color:var(--text-primary);margin:0;flex:1;">&#129313; Sub-Agent Tree</h2>
    <button class="refresh-btn" onclick="loadSubagents()">&#8635; Refresh</button>
  </div>
  <div id="subagents-list"><div style="color:var(--text-muted);font-size:13px;padding:16px;">Loading...</div></div>
</div><!-- end page-subagents -->

<div class="page" id="page-skills">
  <div class="refresh-bar">
    <h2 style="font-size:16px;font-weight:700;color:var(--text-primary);margin:0;flex:1;">&#127381; Skills Fidelity</h2>
    <button class="refresh-btn" onclick="loadSkills()">&#8635; Refresh</button>
  </div>
  <div id="skills-summary-row" style="display:flex;gap:12px;flex-wrap:wrap;margin-bottom:16px;"></div>
  <div id="skills-list"><div style="color:var(--text-muted);font-size:13px;padding:16px;">Loading...</div></div>
</div><!-- end page-skills -->


<script>

// ═══ QUICK ACTIONS ═══════════════════════════════════════════════════════════
var _qaCurrentAction = null;

function qaConfirmAction(actionKey, title, body) {
  _qaCurrentAction = actionKey;
  document.getElementById('qa-confirm-title').textContent = title;
  document.getElementById('qa-confirm-body').textContent = body;
  var overlay = document.getElementById('qa-confirm-overlay');
  overlay.style.display = 'flex';
  document.getElementById('qa-confirm-ok').onclick = function() {
    qaCloseConfirm();
    qaRunAction(actionKey);
  };
}

function qaCloseConfirm() {
  var overlay = document.getElementById('qa-confirm-overlay');
  if (overlay) overlay.style.display = 'none';
  _qaCurrentAction = null;
}

async function qaRunAction(actionKey) {
  var banner = document.getElementById('qa-result-banner');
  if (banner) {
    banner.style.display = 'block';
    banner.style.background = 'rgba(96,165,250,0.1)';
    banner.style.borderColor = 'rgba(96,165,250,0.3)';
    banner.style.color = '#60a5fa';
    banner.textContent = 'Running ' + actionKey + '...';
  }
  try {
    var resp = await fetch('/api/actions/run', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({action: actionKey})
    });
    var data = await resp.json();
    if (banner) {
      if (data.ok) {
        banner.style.background = 'rgba(34,197,94,0.1)';
        banner.style.borderColor = 'rgba(34,197,94,0.3)';
        banner.style.color = '#22c55e';
        banner.textContent = '✓ ' + (data.output || actionKey + ' completed') + ' (' + (data.duration_ms || 0) + 'ms)';
      } else {
        banner.style.background = 'rgba(239,68,68,0.1)';
        banner.style.borderColor = 'rgba(239,68,68,0.3)';
        banner.style.color = '#ef4444';
        banner.textContent = '✗ ' + (data.output || data.error || 'Action failed');
      }
    }
    loadQAHistory();
  } catch(e) {
    if (banner) {
      banner.style.background = 'rgba(239,68,68,0.1)';
      banner.style.borderColor = 'rgba(239,68,68,0.3)';
      banner.style.color = '#ef4444';
      banner.textContent = '✗ ' + e.message;
    }
  }
}

async function loadQAHistory() {
  var el = document.getElementById('qa-history-list');
  if (!el) return;
  try {
    var resp = await fetch('/api/actions/history');
    var data = await resp.json();
    var actions = data.actions || [];
    if (!actions.length) {
      el.textContent = 'No actions run yet.';
      return;
    }
    var html = '<table style="width:100%;border-collapse:collapse;">';
    actions.slice().reverse().forEach(function(a) {
      var color = a.ok ? '#22c55e' : '#ef4444';
      var label = a.ok ? '✓' : '✗';
      html += '<tr style="border-bottom:1px solid var(--border-color);">';
      html += '<td style="padding:6px 8px;color:' + color + ';width:24px;">' + label + '</td>';
      html += '<td style="padding:6px 8px;color:var(--text-secondary);width:130px;font-weight:600;">' + (a.action || '') + '</td>';
      html += '<td style="padding:6px 8px;color:var(--text-muted);">' + (a.output || '').slice(0, 120) + '</td>';
      html += '<td style="padding:6px 8px;color:var(--text-muted);text-align:right;width:65px;">' + (a.duration_ms || 0) + 'ms</td>';
      html += '</tr>';
    });
    html += '</table>';
    el.innerHTML = html;
  } catch(e) {
    el.textContent = 'Could not load action history.';
  }
}
// ═══ END QUICK ACTIONS ═══════════════════════════════════════════════════════

// === Budget & Alert Functions ===
function openBudgetModal() {
  document.getElementById('budget-modal').style.display = 'flex';
  loadBudgetConfig();
  loadBudgetStatus();
}

function switchBudgetTab(tab, el) {
  document.querySelectorAll('#budget-modal-tabs .modal-tab').forEach(function(t){t.classList.remove('active');});
  if(el) el.classList.add('active');
  ['limits','alerts','telegram','history'].forEach(function(t){
    var d = document.getElementById('budget-tab-'+t);
    if(d) d.style.display = t===tab ? 'block' : 'none';
  });
  if(tab==='alerts') { loadAlertRules(); loadWebhookConfig(); }
  if(tab==='telegram') loadTelegramConfig();
  if(tab==='history') loadAlertHistory();
}

async function loadBudgetConfig() {
  try {
    var cfg = await fetch('/api/budget/config').then(function(r){return r.json();});
    document.getElementById('budget-daily').value = cfg.daily_limit || 0;
    document.getElementById('budget-weekly').value = cfg.weekly_limit || 0;
    document.getElementById('budget-monthly').value = cfg.monthly_limit || 0;
    document.getElementById('budget-warn-pct').value = cfg.warning_threshold_pct || 80;
    document.getElementById('budget-autopause').checked = cfg.auto_pause_enabled || false;
  } catch(e) {}
}

async function loadBudgetStatus() {
  try {
    var s = await fetch('/api/budget/status').then(function(r){return r.json();});
    var html = '';
    function row(label, spent, limit, pct) {
      var color = pct > 90 ? 'var(--text-error)' : pct > 70 ? 'var(--text-warning)' : 'var(--text-success)';
      html += '<div style="display:flex;justify-content:space-between;padding:4px 0;">';
      html += '<span>' + label + '</span>';
      html += '<span style="font-weight:600;color:' + color + ';">$' + spent.toFixed(2);
      if(limit > 0) html += ' / $' + limit.toFixed(2) + ' (' + pct.toFixed(0) + '%)';
      html += '</span></div>';
    }
    row('Today', s.daily_spent, s.daily_limit, s.daily_pct);
    row('This Week', s.weekly_spent, s.weekly_limit, s.weekly_pct);
    row('This Month', s.monthly_spent, s.monthly_limit, s.monthly_pct);
    if(s.paused) {
      html += '<div style="margin-top:8px;padding:8px;background:var(--bg-error);border-radius:6px;color:var(--text-error);font-weight:600;">&#9888;&#65039; Gateway PAUSED: ' + escHtml(s.paused_reason) + '</div>';
    }
    document.getElementById('budget-status-content').innerHTML = html;
  } catch(e) {
    document.getElementById('budget-status-content').textContent = 'Failed to load';
  }
}

async function saveBudgetConfig() {
  var data = {
    daily_limit: parseFloat(document.getElementById('budget-daily').value) || 0,
    weekly_limit: parseFloat(document.getElementById('budget-weekly').value) || 0,
    monthly_limit: parseFloat(document.getElementById('budget-monthly').value) || 0,
    warning_threshold_pct: parseInt(document.getElementById('budget-warn-pct').value) || 80,
    auto_pause_enabled: document.getElementById('budget-autopause').checked,
  };
  await fetch('/api/budget/config', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(data)});
  loadBudgetStatus();
}

async function resumeGateway() {
  await fetch('/api/budget/resume', {method:'POST'});
  document.getElementById('alert-banner').style.display = 'none';
  document.getElementById('alert-resume-btn').style.display = 'none';
  loadBudgetStatus();
}

function showAddAlertForm() {
  document.getElementById('add-alert-form').style.display = 'block';
}

async function createAlertRule() {
  var channels = [];
  if(document.getElementById('alert-ch-banner').checked) channels.push('banner');
  if(document.getElementById('alert-ch-telegram').checked) channels.push('telegram');
  var data = {
    type: document.getElementById('alert-type').value,
    threshold: parseFloat(document.getElementById('alert-threshold').value) || 0,
    channels: channels,
    cooldown_min: parseInt(document.getElementById('alert-cooldown').value) || 30,
  };
  await fetch('/api/alerts/rules', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(data)});
  document.getElementById('add-alert-form').style.display = 'none';
  loadAlertRules();
}

async function loadAlertRules() {
  try {
    var data = await fetch('/api/alerts/rules').then(function(r){return r.json();});
    var rules = data.rules || [];
    if(rules.length === 0) {
      document.getElementById('alert-rules-list').innerHTML = '<div style="padding:20px;text-align:center;color:var(--text-muted);">No alert rules configured</div>';
      return;
    }
    var html = '';
    rules.forEach(function(r) {
      var channels = [];
      try { channels = JSON.parse(r.channels); } catch(e) { channels = [r.channels]; }
      html += '<div style="padding:10px;border-bottom:1px solid var(--border-secondary);display:flex;align-items:center;gap:8px;">';
      html += '<span style="font-weight:600;">' + escHtml(r.type) + '</span>';
      html += '<span style="color:var(--text-accent);">' + (r.type==='spike' ? r.threshold+'x' : '$'+r.threshold) + '</span>';
      html += '<span style="color:var(--text-muted);font-size:11px;">' + channels.join(', ') + '</span>';
      html += '<span style="color:var(--text-muted);font-size:11px;">' + r.cooldown_min + 'min cooldown</span>';
      html += '<span style="margin-left:auto;cursor:pointer;color:var(--text-error);font-size:16px;" data-rule-id="'+r.id+'" onclick="deleteAlertRule(this.dataset.ruleId)" title="Delete">&#x1f5d1;</span>';
      html += '</div>';
    });
    document.getElementById('alert-rules-list').innerHTML = html;
  } catch(e) {
    document.getElementById('alert-rules-list').textContent = 'Failed to load';
  }
}

async function deleteAlertRule(id) {
  await fetch('/api/alerts/rules/'+id, {method:'DELETE'});
  loadAlertRules();
}

async function loadWebhookConfig() {
  try {
    var cfg = await fetch('/api/alert-channels').then(function(r){return r.json();});
    document.getElementById('alert-webhook-url').value = cfg.webhook_url || '';
    document.getElementById('alert-slack-url').value = cfg.slack_webhook_url || '';
    document.getElementById('alert-discord-url').value = cfg.discord_webhook_url || '';
    document.getElementById('alert-toggle-cost-spike').checked = cfg.cost_spike_alerts !== false;
    document.getElementById('alert-toggle-agent-error').checked = cfg.agent_error_rate_alerts !== false;
    document.getElementById('alert-toggle-security').checked = cfg.security_posture_changes !== false;
    var minSevEl = document.getElementById('alert-min-severity');
    if (minSevEl) minSevEl.value = cfg.min_severity || 'warning';
    document.getElementById('alert-webhook-status').textContent = '';
  } catch(e) {}
}

async function saveWebhookConfig() {
  var status = document.getElementById('alert-webhook-status');
  status.textContent = 'Saving...';
  var minSevEl = document.getElementById('alert-min-severity');
  var payload = {
    webhook_url: document.getElementById('alert-webhook-url').value.trim(),
    slack_webhook_url: document.getElementById('alert-slack-url').value.trim(),
    discord_webhook_url: document.getElementById('alert-discord-url').value.trim(),
    cost_spike_alerts: document.getElementById('alert-toggle-cost-spike').checked,
    agent_error_rate_alerts: document.getElementById('alert-toggle-agent-error').checked,
    security_posture_changes: document.getElementById('alert-toggle-security').checked,
    min_severity: minSevEl ? minSevEl.value : 'warning',
  };
  try {
    var r = await fetch('/api/alert-channels', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify(payload)
    });
    if (!r.ok) throw new Error('Save failed');
    status.style.color = 'var(--text-success)';
    status.textContent = 'Saved';
  } catch(e) {
    status.style.color = 'var(--text-error)';
    status.textContent = 'Save failed';
  }
}

async function testWebhookConfig(target) {
  var status = document.getElementById('alert-webhook-status');
  status.style.color = 'var(--text-muted)';
  status.textContent = 'Sending test...';
  try {
    var r = await fetch('/api/alert-channels/test', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({target: target || 'all', severity: 'warning'})
    });
    var data = await r.json();
    if(data.ok) {
      status.style.color = 'var(--text-success)';
      status.textContent = 'Test sent to: ' + (data.sent || []).join(', ');
    } else {
      status.style.color = 'var(--text-error)';
      status.textContent = data.error || 'No URL configured for ' + (target || 'all');
    }
  } catch(e) {
    status.style.color = 'var(--text-error)';
    status.textContent = 'Test failed';
  }
}

async function loadAlertHistory() {
  try {
    var data = await fetch('/api/alerts/history?limit=50').then(function(r){return r.json();});
    var alerts = data.alerts || [];
    if(alerts.length === 0) {
      document.getElementById('alert-history-list').innerHTML = '<div style="padding:20px;text-align:center;color:var(--text-muted);">No alerts fired yet</div>';
      return;
    }
    var html = '';
    alerts.forEach(function(a) {
      var ts = new Date(a.fired_at * 1000).toLocaleString();
      var ack = a.acknowledged ? '<span style="color:var(--text-success);">&#10003;</span>' : '<span style="color:var(--text-warning);">&#x25cf;</span>';
      html += '<div style="padding:8px;border-bottom:1px solid var(--border-secondary);font-size:12px;">';
      html += ack + ' <span style="color:var(--text-muted);">' + ts + '</span> ';
      html += '<span style="font-weight:600;">[' + escHtml(a.type) + ']</span> ';
      html += escHtml(a.message);
      html += '</div>';
    });
    document.getElementById('alert-history-list').innerHTML = html;
  } catch(e) {
    document.getElementById('alert-history-list').textContent = 'Failed to load';
  }
}

async function checkActiveAlerts() {
  try {
    var data = await fetch('/api/alerts/active').then(function(r){return r.json();});
    var alerts = data.alerts || [];
    var banner = document.getElementById('alert-banner');
    if(alerts.length === 0) {
      banner.style.display = 'none';
      return;
    }
    // Show most recent alert
    var latest = alerts[0];
    document.getElementById('alert-banner-msg').textContent = latest.message;
    banner.style.display = 'flex';
    // Show resume button if gateway is paused
    var status = await fetch('/api/budget/status').then(function(r){return r.json();});
    document.getElementById('alert-resume-btn').style.display = status.paused ? '' : 'none';
  } catch(e) {}
}

async function ackAllAlerts() {
  try {
    var data = await fetch('/api/alerts/active').then(function(r){return r.json();});
    var alerts = data.alerts || [];
    for(var i=0; i<alerts.length; i++) {
      await fetch('/api/alerts/history/'+alerts[i].id+'/ack', {method:'POST'});
    }
    document.getElementById('alert-banner').style.display = 'none';
  } catch(e) {}
}

// Check alerts every 30s
setInterval(checkActiveAlerts, 30000);
setTimeout(checkActiveAlerts, 3000);

// === Telegram Config Functions ===
async function loadTelegramConfig() {
  try {
    var cfg = await fetch('/api/budget/config').then(function(r){return r.json();});
    var tokenEl = document.getElementById('tg-bot-token');
    var chatEl = document.getElementById('tg-chat-id');
    if(cfg.telegram_bot_token) tokenEl.value = cfg.telegram_bot_token;
    if(cfg.telegram_chat_id) chatEl.value = cfg.telegram_chat_id;
    var statusEl = document.getElementById('tg-status');
    if(cfg.telegram_bot_token && cfg.telegram_chat_id) {
      statusEl.innerHTML = '<span style="color:var(--text-success);">Configured</span>';
    } else {
      statusEl.innerHTML = '<span style="color:var(--text-muted);">Not configured</span>';
    }
  } catch(e) {}
}

async function saveTelegramConfig() {
  var token = document.getElementById('tg-bot-token').value.trim();
  var chatId = document.getElementById('tg-chat-id').value.trim();
  await fetch('/api/budget/config', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({telegram_bot_token: token, telegram_chat_id: chatId})
  });
  document.getElementById('tg-status').innerHTML = '<span style="color:var(--text-success);">Saved!</span>';
}

async function testTelegram() {
  var statusEl = document.getElementById('tg-status');
  statusEl.innerHTML = '<span style="color:var(--text-muted);">Sending...</span>';
  try {
    var r = await fetch('/api/budget/test-telegram', {method: 'POST'});
    var data = await r.json();
    if(data.ok) {
      statusEl.innerHTML = '<span style="color:var(--text-success);">Test sent!</span>';
    } else {
      statusEl.innerHTML = '<span style="color:var(--text-error);">' + escHtml(data.error || 'Failed') + '</span>';
    }
  } catch(e) {
    statusEl.innerHTML = '<span style="color:var(--text-error);">Request failed</span>';
  }
}

function switchTab(name) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
  var page = document.getElementById('page-' + name);
  if (page) page.classList.add('active');
  var tabs = document.querySelectorAll('.nav-tab');
  tabs.forEach(function(t) { if (t.getAttribute('onclick') && t.getAttribute('onclick').indexOf("'" + name + "'") !== -1) t.classList.add('active'); });
  if (!document.querySelector('.nav-tab.active') && typeof event !== 'undefined' && event && event.target) event.target.classList.add('active');
  // Stop cron auto-refresh when leaving crons tab
  if (name !== 'crons' && _cronAutoRefreshTimer) { clearInterval(_cronAutoRefreshTimer); _cronAutoRefreshTimer = null; }
  if (name === 'overview') loadAll();
  if (name === 'overview') { if (typeof _velocityPollTimer !== 'undefined' && _velocityPollTimer) clearInterval(_velocityPollTimer); if (typeof loadTokenVelocity === 'function') _velocityPollTimer = setInterval(loadTokenVelocity, 30000); }
  if (name === 'usage') loadUsage();
  if (name === 'skills') loadSkills();
  if (name === 'crons') loadCrons();
  if (name === 'memory') loadMemory();
  if (name === 'transcripts') loadTranscripts();
  if (name === 'version-impact') loadVersionImpact();
  if (name === 'clusters') loadClusters();
  if (name === 'limits') loadRateLimits();
  if (name === 'flow') initFlow();
  if (name === 'history') loadHistory();
  if (name === 'brain') loadBrainPage();
  if (name === 'security') { loadSecurityPage(); loadSecurityPosture(); }
  if (name === 'actions') loadQAHistory();
  if (name === 'logs') { if (!logStream || logStream.readyState === EventSource.CLOSED) startLogStream(); loadLogs(); }
  if (name === 'models') loadModelAttribution();
  if (name === 'nemoclaw') { loadNemoClaw(); _startNcApprovalsAutoRefresh(); }
  if (name !== 'nemoclaw') _stopNcApprovalsAutoRefresh();
  if (name === 'subagents') { loadSubagents(); if (!_subagentsTimer) _subagentsTimer = setInterval(loadSubagents, 5000); }
  if (name !== 'subagents' && _subagentsTimer) { clearInterval(_subagentsTimer); _subagentsTimer = null; }
  if (name === 'selfconfig') loadSelfConfig();
}

function exportUsageData() {
  window.location.href = '/api/usage/export';
}

async function loadSkills() {
  var summaryEl = document.getElementById('skills-summary-row');
  var listEl = document.getElementById('skills-list');
  if (!summaryEl || !listEl) return;
  listEl.innerHTML = '<div style="color:var(--text-muted);font-size:13px;padding:16px;">Loading...</div>';
  try {
    var data = await fetch('/api/skills').then(function(r){return r.json();});
    var skills = data.skills || [];
    var summary = data.summary || {};
    var wastePct = summary.total_header_tokens > 0
      ? Math.round(summary.wasted_header_tokens / summary.total_header_tokens * 100) : 0;
    summaryEl.innerHTML =
      '<div style="background:var(--bg-secondary);border:1px solid var(--border-primary);border-radius:8px;padding:10px 16px;font-size:13px;color:var(--text-primary);">' +
        '<strong>' + (summary.total_installed||0) + '</strong> skills installed' +
      '</div>' +
      '<div style="background:var(--bg-secondary);border:1px solid var(--border-primary);border-radius:8px;padding:10px 16px;font-size:13px;color:#ef4444;">' +
        '<strong>' + (summary.dead_count||0) + '</strong> dead' +
      '</div>' +
      '<div style="background:var(--bg-secondary);border:1px solid var(--border-primary);border-radius:8px;padding:10px 16px;font-size:13px;color:#f59e0b;">' +
        '<strong>' + (summary.stuck_count||0) + '</strong> stuck' +
      '</div>' +
      '<div style="background:var(--bg-secondary);border:1px solid var(--border-primary);border-radius:8px;padding:10px 16px;font-size:13px;color:var(--text-muted);">' +
        '<strong>' + (summary.wasted_header_tokens||0) + '</strong> tokens wasted on dead skills (' + wastePct + '%)' +
      '</div>';
    if (skills.length === 0) {
      listEl.innerHTML = '<div style="color:var(--text-muted);font-size:13px;padding:16px;">No skills installed.</div>';
      return;
    }
    var _statusColor = {healthy:'#22c55e', unused:'#94a3b8', dead:'#ef4444', stuck:'#f59e0b'};
    var html = '<table style="width:100%;border-collapse:collapse;font-size:13px;">' +
      '<thead><tr style="color:var(--text-muted);text-align:left;border-bottom:1px solid var(--border-primary);">' +
        '<th style="padding:8px 10px;">Name</th>' +
        '<th style="padding:8px 10px;">Description</th>' +
        '<th style="padding:8px 10px;">Status</th>' +
        '<th style="padding:8px 10px;text-align:right;">Header Tokens</th>' +
        '<th style="padding:8px 10px;text-align:right;">Body Fetches (7d)</th>' +
        '<th style="padding:8px 10px;text-align:right;">Linked Reads (7d)</th>' +
        '<th style="padding:8px 10px;">Last Used</th>' +
      '</tr></thead><tbody>';
    skills.forEach(function(sk, idx) {
      var desc = (sk.description||'').length > 60 ? sk.description.slice(0,57)+'...' : (sk.description||'—');
      var sc = _statusColor[sk.status] || '#94a3b8';
      var badge = '<span style="background:' + sc + '22;color:' + sc + ';border:1px solid ' + sc + '44;border-radius:10px;padding:2px 8px;font-size:11px;font-weight:600;">' + (sk.status||'?') + '</span>';
      var lastUsed = sk.last_used_ts ? new Date(sk.last_used_ts * 1000).toLocaleDateString() : '—';
      var rowBg = idx % 2 === 0 ? 'var(--bg-primary)' : 'var(--bg-secondary)';
      var detailId = 'skill-detail-' + idx;
      html += '<tr style="background:' + rowBg + ';cursor:pointer;border-bottom:1px solid var(--border-primary);" onclick="var d=document.getElementById(\'' + detailId + '\');d.style.display=d.style.display===\'none\'?\'table-row\':\'none\'">' +
        '<td style="padding:8px 10px;font-weight:600;color:var(--text-primary);">' + escHtml(sk.name) + '</td>' +
        '<td style="padding:8px 10px;color:var(--text-muted);">' + escHtml(desc) + '</td>' +
        '<td style="padding:8px 10px;">' + badge + '</td>' +
        '<td style="padding:8px 10px;text-align:right;color:var(--text-muted);">' + (sk.header_tokens||0) + '</td>' +
        '<td style="padding:8px 10px;text-align:right;color:var(--text-muted);">' + (sk.body_fetch_count_7d||0) + '</td>' +
        '<td style="padding:8px 10px;text-align:right;color:var(--text-muted);">' + (sk.linked_file_read_count_7d||0) + '</td>' +
        '<td style="padding:8px 10px;color:var(--text-muted);">' + lastUsed + '</td>' +
      '</tr>' +
      '<tr id="' + detailId + '" style="display:none;background:var(--bg-tertiary);">' +
        '<td colspan="7" style="padding:12px 20px;color:var(--text-muted);font-size:12px;">' +
          '<strong>Description:</strong> ' + escHtml(sk.description||'(none)') + '<br>' +
          '<strong>Has body:</strong> ' + (sk.has_body?'yes':'no') + ' &nbsp;|&nbsp; ' +
          '<strong>Has linked files:</strong> ' + (sk.has_linked_files?'yes':'no') +
        '</td>' +
      '</tr>';
    });
    html += '</tbody></table>';
    listEl.innerHTML = html;
  } catch(e) {
    if (listEl) listEl.innerHTML = '<div style="color:#ef4444;font-size:13px;padding:16px;">Failed to load skills: ' + e + '</div>';
  }
}

// ═══ SELF-CONFIG DIFF VIEWER ═════════════════════════════════════════════════

var _selfconfigCurrentFile = null;
var _selfconfigRevisions = [];

async function loadSelfConfig() {
  var inner = document.getElementById('selfconfig-files-inner');
  if (!inner) return;
  inner.innerHTML = '<span style="color:var(--text-muted);">Loading...</span>';
  // Reset detail pane
  var detailEmpty = document.getElementById('selfconfig-empty-state');
  var detailRevs = document.getElementById('selfconfig-revisions-panel');
  var detailDiff = document.getElementById('selfconfig-diff-panel');
  if (detailEmpty) { detailEmpty.style.display = 'block'; }
  if (detailRevs) { detailRevs.style.display = 'none'; }
  if (detailDiff) { detailDiff.style.display = 'none'; }
  try {
    var d = await fetchJsonWithTimeout('/api/selfconfig', 5000);
    var files = d.files || [];
    var hasAnyRevisions = files.some(function(f) { return f.revision_count > 0; });
    var noHistMsg = document.getElementById('selfconfig-no-history-msg');
    if (noHistMsg) noHistMsg.style.display = hasAnyRevisions ? 'none' : 'block';
    if (!files.length) {
      inner.innerHTML = '<span style="color:var(--text-muted);font-size:12px;">No tracked files found.</span>';
      return;
    }
    inner.innerHTML = files.map(function(f) {
      var badge = f.is_values_file
        ? ' <span style="background:rgba(251,146,60,0.15);color:#fb923c;border:1px solid rgba(251,146,60,0.4);border-radius:8px;padding:1px 6px;font-size:10px;font-weight:700;">VALUES</span>'
        : '';
      var revCount = f.revision_count > 0
        ? ' <span style="color:var(--text-muted);font-size:10px;">(' + f.revision_count + ' rev' + (f.revision_count !== 1 ? 's' : '') + ')</span>'
        : ' <span style="color:var(--text-muted);font-size:10px;">(no edits)</span>';
      var existStyle = f.exists ? '' : 'opacity:0.5;';
      return '<div onclick="loadSelfConfigHistory(\'' + f.name + '\')" style="cursor:pointer;padding:7px 8px;border-radius:6px;margin-bottom:4px;' + existStyle + 'border:1px solid transparent;transition:all 0.15s;" onmouseover="this.style.background=\'var(--bg-hover)\'" onmouseout="this.style.background=\'transparent\'">'
        + '<div style="font-size:12px;font-weight:600;color:var(--text-primary);">' + f.name + badge + '</div>'
        + '<div style="font-size:11px;margin-top:2px;">' + revCount + '</div>'
        + '</div>';
    }).join('');
  } catch(e) {
    inner.innerHTML = '<span style="color:var(--text-muted);font-size:12px;">Error loading files.</span>';
  }
}

async function loadSelfConfigHistory(filename) {
  _selfconfigCurrentFile = filename;
  var emptyEl = document.getElementById('selfconfig-empty-state');
  var revsPanel = document.getElementById('selfconfig-revisions-panel');
  var diffPanel = document.getElementById('selfconfig-diff-panel');
  if (emptyEl) emptyEl.style.display = 'none';
  if (diffPanel) diffPanel.style.display = 'none';
  if (revsPanel) revsPanel.style.display = 'block';
  var headEl = document.getElementById('selfconfig-filename-heading');
  var badgeEl = document.getElementById('selfconfig-values-badge');
  var listEl = document.getElementById('selfconfig-revisions-list');
  if (headEl) headEl.textContent = filename;
  if (listEl) listEl.innerHTML = '<span style="color:var(--text-muted);">Loading...</span>';
  try {
    var d = await fetchJsonWithTimeout('/api/selfconfig/' + encodeURIComponent(filename), 5000);
    if (badgeEl) badgeEl.style.display = d.is_values_file ? 'block' : 'none';
    _selfconfigRevisions = d.revisions || [];
    if (!_selfconfigRevisions.length) {
      listEl.innerHTML = '<div style="color:var(--text-muted);font-size:12px;padding:8px 0;">No revisions recorded yet. Edits will appear here automatically.</div>';
      return;
    }
    listEl.innerHTML = _selfconfigRevisions.map(function(rev, idx) {
      var dt = new Date(rev.ts * 1000).toLocaleString();
      var delta = '';
      if (idx < _selfconfigRevisions.length - 1) {
        var prevSize = _selfconfigRevisions[idx + 1].size;
        var diff = rev.size - prevSize;
        delta = diff > 0
          ? '<span style="color:#22c55e;font-weight:600;">+' + diff + '</span>'
          : diff < 0
            ? '<span style="color:#ef4444;font-weight:600;">' + diff + '</span>'
            : '<span style="color:var(--text-muted);">±0</span>';
      } else {
        delta = '<span style="color:var(--text-muted);font-size:10px;">initial</span>';
      }
      var prevTs = idx < _selfconfigRevisions.length - 1 ? _selfconfigRevisions[idx + 1].ts : null;
      var diffBtn = prevTs !== null
        ? '<button onclick="loadSelfConfigDiff(\'' + filename + '\',' + prevTs + ',' + rev.ts + ')" style="background:var(--bg-primary);border:1px solid var(--border);border-radius:5px;padding:2px 8px;font-size:10px;cursor:pointer;color:var(--text-secondary);margin-left:8px;">View diff</button>'
        : '';
      return '<div style="display:flex;align-items:center;justify-content:space-between;padding:8px;border-radius:6px;margin-bottom:4px;background:var(--bg-primary);border:1px solid var(--border-secondary);">'
        + '<div>'
        + '<div style="font-size:12px;font-weight:600;color:var(--text-primary);">' + dt + '</div>'
        + '<div style="font-size:11px;color:var(--text-muted);margin-top:2px;">' + rev.size.toLocaleString() + ' bytes &nbsp; ' + delta + '</div>'
        + '</div>'
        + diffBtn
        + '</div>';
    }).join('');
  } catch(e) {
    if (listEl) listEl.innerHTML = '<span style="color:var(--text-muted);font-size:12px;">Error loading history.</span>';
  }
}

async function loadSelfConfigDiff(filename, fromTs, toTs) {
  var diffPanel = document.getElementById('selfconfig-diff-panel');
  var revsPanel = document.getElementById('selfconfig-revisions-panel');
  var emptyEl   = document.getElementById('selfconfig-empty-state');
  if (emptyEl) emptyEl.style.display = 'none';
  if (revsPanel) revsPanel.style.display = 'none';
  if (diffPanel) diffPanel.style.display = 'block';
  var headEl    = document.getElementById('selfconfig-diff-heading');
  var statsEl   = document.getElementById('selfconfig-diff-stats');
  var contentEl = document.getElementById('selfconfig-diff-content');
  if (headEl) headEl.textContent = filename + ' diff';
  if (contentEl) contentEl.innerHTML = '<span style="color:var(--text-muted);">Loading diff...</span>';
  try {
    var url = '/api/selfconfig/' + encodeURIComponent(filename) + '/diff?from=' + fromTs + '&to=' + toTs;
    var d = await fetchJsonWithTimeout(url, 8000);
    if (statsEl) {
      statsEl.innerHTML = '<span style="color:#22c55e;">+' + d.added_chars + '</span> / <span style="color:#ef4444;">-' + d.removed_chars + '</span> chars'
        + (d.truncated ? ' <span style="color:#f59e0b;">(truncated)</span>' : '');
    }
    var lines = d.diff_lines || [];
    if (!lines.length) {
      contentEl.innerHTML = '<div style="color:var(--text-muted);font-size:12px;padding:8px 0;">No changes detected between these two versions.</div>';
      return;
    }
    contentEl.innerHTML = lines.map(function(line) {
      var txt = (line.text || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
      if (line.type === 'added') {
        return '<div style="background:rgba(34,197,94,0.12);color:#86efac;padding:1px 6px;white-space:pre;">' + txt + '</div>';
      } else if (line.type === 'removed') {
        return '<div style="background:rgba(239,68,68,0.12);color:#fca5a5;padding:1px 6px;white-space:pre;">' + txt + '</div>';
      } else if (line.type === 'meta') {
        return '<div style="color:var(--text-muted);padding:1px 6px;white-space:pre;font-size:11px;">' + txt + '</div>';
      } else {
        return '<div style="color:var(--text-secondary);padding:1px 6px;white-space:pre;">' + txt + '</div>';
      }
    }).join('');
  } catch(e) {
    if (contentEl) contentEl.innerHTML = '<span style="color:var(--text-muted);font-size:12px;">Error loading diff.</span>';
  }
}

function selfconfigBackToRevisions() {
  var diffPanel = document.getElementById('selfconfig-diff-panel');
  var revsPanel = document.getElementById('selfconfig-revisions-panel');
  if (diffPanel) diffPanel.style.display = 'none';
  if (revsPanel && _selfconfigCurrentFile) {
    revsPanel.style.display = 'block';
  }
}

// ═════════════════════════════════════════════════════════════════════════════

var _sunSVG = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>';
var _moonSVG = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>';

function toggleTheme() {
  const body = document.body;
  const toggle = document.getElementById('theme-toggle-btn');
  const isLight = !body.hasAttribute('data-theme') || body.getAttribute('data-theme') !== 'dark';
  
  if (isLight) {
    body.setAttribute('data-theme', 'dark');
    toggle.innerHTML = _sunSVG;
    toggle.title = 'Switch to light theme';
    localStorage.setItem('openclaw-theme', 'dark');
  } else {
    body.removeAttribute('data-theme');
    toggle.innerHTML = _moonSVG;
    toggle.title = 'Switch to dark theme';
    localStorage.setItem('openclaw-theme', 'light');
  }
}

function initTheme() {
  const savedTheme = 'dark'; localStorage.setItem('openclaw-theme', 'dark');
  const body = document.body;
  const toggle = document.getElementById('theme-toggle-btn');
  
  if (savedTheme === 'dark') {
    body.setAttribute('data-theme', 'dark');
    if (toggle) { toggle.innerHTML = _sunSVG; toggle.title = 'Switch to light theme'; }
  } else {
    body.removeAttribute('data-theme');
    if (toggle) { toggle.innerHTML = _moonSVG; toggle.title = 'Switch to dark theme'; }
  }
}

// === Zoom Controls ===
let currentZoom = 1.0;
const MIN_ZOOM = 0.5;
const MAX_ZOOM = 2.0;
const ZOOM_STEP = 0.1;

function initZoom() {
  const savedZoom = localStorage.getItem('openclaw-zoom');
  if (savedZoom) {
    currentZoom = parseFloat(savedZoom);
  }
  applyZoom();
}

function applyZoom() {
  const wrapper = document.getElementById('zoom-wrapper');
  const levelDisplay = document.getElementById('zoom-level');
  
  if (wrapper) {
    wrapper.style.transform = `scale(${currentZoom})`;
  }
  if (levelDisplay) {
    levelDisplay.textContent = Math.round(currentZoom * 100) + '%';
  }
  
  // Save to localStorage
  localStorage.setItem('openclaw-zoom', currentZoom.toString());
}

function zoomIn() {
  if (currentZoom < MAX_ZOOM) {
    currentZoom = Math.min(MAX_ZOOM, currentZoom + ZOOM_STEP);
    applyZoom();
  }
}

function zoomOut() {
  if (currentZoom > MIN_ZOOM) {
    currentZoom = Math.max(MIN_ZOOM, currentZoom - ZOOM_STEP);
    applyZoom();
  }
}

function resetZoom() {
  currentZoom = 1.0;
  applyZoom();
}

// Keyboard shortcuts for zoom
document.addEventListener('keydown', function(e) {
  if ((e.ctrlKey || e.metaKey) && !e.shiftKey && !e.altKey) {
    if (e.key === '=' || e.key === '+') {
      e.preventDefault();
      zoomIn();
    } else if (e.key === '-') {
      e.preventDefault();
      zoomOut();
    } else if (e.key === '0') {
      e.preventDefault();
      resetZoom();
    }
  }
});

function timeAgo(ms) {
  if (!ms) return 'never';
  var diff = Date.now() - ms;
  if (diff < 60000) return Math.floor(diff/1000) + 's ago';
  if (diff < 3600000) return Math.floor(diff/60000) + 'm ago';
  if (diff < 86400000) return Math.floor(diff/3600000) + 'h ago';
  return Math.floor(diff/86400000) + 'd ago';
}

function formatTime(ms) {
  if (!ms) return '--';
  return new Date(ms).toLocaleString('en-GB', {hour:'2-digit',minute:'2-digit',day:'numeric',month:'short'});
}

async function fetchJsonWithTimeout(url, timeoutMs) {
  var ctrl = new AbortController();
  var to = setTimeout(function() { ctrl.abort('timeout'); }, timeoutMs);
  try {
    var r = await fetch(url, {signal: ctrl.signal});
    if (!r.ok) throw new Error('HTTP ' + r.status);
    return await r.json();
  } finally {
    clearTimeout(to);
  }
}

async function resolvePrimaryModelFallback() {
  try {
    var data = await fetchJsonWithTimeout('/api/component/brain?limit=25', 4000);
    var model = (((data || {}).stats || {}).model || '').trim();
    return model || 'unknown';
  } catch (e) {
    return 'unknown';
  }
}

function applyBrainModelToAll(modelName) {
  if (!modelName) return;
  var modelText = fitFlowLabel(modelName, 20);
  document.querySelectorAll('[id$="brain-model-text"]').forEach(function(el) {
    el.textContent = modelText;
  });
  document.querySelectorAll('[id$="brain-model-label"]').forEach(function(label) {
    var short = modelName.split('/').pop().split('-').slice(0, 2).join(' ');
    if (!short) short = 'AI Model';
    label.textContent = fitFlowLabel(short.charAt(0).toUpperCase() + short.slice(1), 14);
  });
}

function fitFlowLabel(text, maxLen) {
  var s = String(text || '').trim();
  if (!s) return '';
  if (s.length <= maxLen) return s;
  return s.substring(0, Math.max(1, maxLen - 1)) + '…';
}

function applyBillingHintToFlow(billingSummary) {
  var hint = 'Auth: ?';
  if (billingSummary === 'likely_api_key') hint = 'Auth: API';
  else if (billingSummary === 'likely_oauth_or_included') hint = 'Auth: OAuth';
  else if (billingSummary === 'mixed') hint = 'Auth: mixed';

  document.querySelectorAll('[id$="brain-billing-text"]').forEach(function(el) {
    el.textContent = fitFlowLabel(hint, 14);
  });
}

function setFlowTextAll(idSuffix, text, maxLen) {
  var fitted = fitFlowLabel(text, maxLen);
  document.querySelectorAll('[id$="' + idSuffix + '"]').forEach(function(el) {
    el.textContent = fitted;
  });
}


var _velocityPollTimer = null;

async function loadTokenVelocity() {
  try {
    var d = await fetchJsonWithTimeout('/api/token-velocity', 5000);
    var banner = document.getElementById('velocity-alert-banner');
    var msgEl  = document.getElementById('velocity-alert-msg');
    var listEl = document.getElementById('velocity-flagged-list');
    if (!banner) return;

    if (!d.alert || d.level === 'ok') {
      banner.style.display = 'none';
      return;
    }

    var vel = d.velocity_2min ? d.velocity_2min.toLocaleString() : '0';
    var cpm = d.cost_per_min ? '$' + d.cost_per_min.toFixed(3) + '/min' : '';
    msgEl.textContent = '\u26a0\ufe0f High token velocity \u2014 ' + vel + ' tokens/2min' + (cpm ? '  (' + cpm + ')' : '');

    if (d.level === 'critical') {
      banner.style.background = 'rgba(220,38,38,0.18)';
      banner.style.border     = '1px solid rgba(239,68,68,0.5)';
      banner.style.color      = '#fca5a5';
    } else {
      banner.style.background = 'rgba(217,119,6,0.18)';
      banner.style.border     = '1px solid rgba(245,158,11,0.5)';
      banner.style.color      = '#fcd34d';
    }

    // Render flagged sessions with Kill buttons
    if (listEl && d.flagged_sessions && d.flagged_sessions.length > 0) {
      listEl.innerHTML = d.flagged_sessions.map(function(s) {
        var info = s.tokens_2min ? s.tokens_2min.toLocaleString() + ' tok/2min' : '';
        if (s.tool_chain_len >= 20) info += (info ? ', ' : '') + s.tool_chain_len + ' tool chain';
        return '<span style="display:inline-flex;align-items:center;gap:6px;background:rgba(0,0,0,0.3);border-radius:6px;padding:3px 8px;font-size:11px;font-weight:400;">'
          + '<code style="font-size:10px;color:inherit;opacity:0.8;">' + s.id + '</code>'
          + '<span style="opacity:0.7;">' + info + '</span>'
          + '<button onclick="killSession(\'' + s.id + '\')" style="background:#dc2626;color:#fff;border:none;border-radius:4px;padding:1px 6px;font-size:10px;cursor:pointer;font-weight:600;">Kill</button>'
          + '</span>';
      }).join('');
    } else if (listEl) {
      listEl.innerHTML = '';
    }

    banner.style.display = 'block';
  } catch(e) {
    console.warn('token velocity check failed', e);
  }
}

async function killSession(sessionId) {
  if (!confirm('Stop session ' + sessionId + '?')) return;
  try {
    var resp = await fetch('/api/sessions/' + encodeURIComponent(sessionId) + '/stop', {method: 'POST'});
    if (resp.ok) { alert('Session stopped.'); loadTokenVelocity(); }
    else alert('Failed to stop session: ' + resp.status);
  } catch(e) { alert('Error: ' + e.message); }
}

// ---------------------------------------------------------------------------
// Autonomy Score loader (#688)
// ---------------------------------------------------------------------------
async function loadAutonomy() {
  var scoreEl = document.getElementById('autonomy-score-value');
  var badgeEl = document.getElementById('autonomy-trend-badge');
  var gapEl   = document.getElementById('autonomy-median-gap');
  var trendEl = document.getElementById('autonomy-trend-pct');
  var svgEl   = document.getElementById('autonomy-sparkline');
  var sampEl  = document.getElementById('autonomy-samples');
  if (!scoreEl) return;
  try {
    var d = await fetchJsonWithTimeout('/api/autonomy', 5000);

    // Score
    if (d.score == null) {
      scoreEl.textContent = '--';
      if (gapEl) gapEl.textContent = 'No data yet \u2014 start using your agent to track autonomy';
      if (badgeEl) { badgeEl.textContent = ''; badgeEl.style.background = ''; }
      if (trendEl) trendEl.textContent = '';
      if (sampEl) sampEl.textContent = '';
      return;
    }
    scoreEl.textContent = d.score.toFixed(2);

    // Median gap
    if (gapEl && d.median_gap_seconds_7d != null) {
      var secs = Math.round(d.median_gap_seconds_7d);
      var hrs = Math.floor(secs / 3600);
      var mins = Math.floor((secs % 3600) / 60);
      var s = secs % 60;
      var parts = [];
      if (hrs > 0) parts.push(hrs + 'h');
      if (mins > 0) parts.push(mins + 'm');
      parts.push(s + 's');
      gapEl.textContent = 'Median time between nudges: ' + parts.join(' ');
    } else if (gapEl) {
      gapEl.textContent = 'Median time between nudges: --';
    }

    // Trend badge
    if (badgeEl) {
      var dir = d.trend_direction || 'flat';
      if (dir === 'improving') {
        badgeEl.textContent = '\u2191 improving';
        badgeEl.style.background = 'rgba(16,185,129,0.18)';
        badgeEl.style.color = '#10b981';
        badgeEl.style.border = '1px solid rgba(16,185,129,0.35)';
      } else if (dir === 'declining') {
        badgeEl.textContent = '\u2193 declining';
        badgeEl.style.background = 'rgba(239,68,68,0.18)';
        badgeEl.style.color = '#ef4444';
        badgeEl.style.border = '1px solid rgba(239,68,68,0.35)';
      } else {
        badgeEl.textContent = '\u2015 steady';
        badgeEl.style.background = 'rgba(100,116,139,0.18)';
        badgeEl.style.color = 'var(--text-muted)';
        badgeEl.style.border = '1px solid var(--border-primary)';
      }
    }

    // Trend pct from slope
    if (trendEl && d.trend_slope_7d != null) {
      var pct = Math.round(d.trend_slope_7d * 100);
      if (pct > 0) trendEl.textContent = '+' + pct + '% this week';
      else if (pct < 0) trendEl.textContent = pct + '% this week';
      else trendEl.textContent = '';
    }

    // Samples
    if (sampEl && d.samples_7d != null) {
      sampEl.textContent = d.samples_7d + ' user msg' + (d.samples_7d !== 1 ? 's' : '') + ' in 7d';
    }

    // Sparkline — inline SVG of daily autonomy_ratio
    if (svgEl && d.series_daily && d.series_daily.length > 0) {
      var ratios = d.series_daily.map(function(e){ return e.autonomy_ratio; });
      var valid = ratios.filter(function(v){ return v != null; });
      if (valid.length >= 2) {
        var W = 160, H = 48, pad = 4;
        var minV = 0, maxV = 1;
        var n = ratios.length;
        var step = (W - pad * 2) / Math.max(n - 1, 1);
        var pts = ratios.map(function(v, i) {
          var x = pad + i * step;
          var y = v == null ? null : H - pad - (v - minV) / (maxV - minV) * (H - pad * 2);
          return {x: x, y: y, v: v};
        });
        // Build polyline from non-null points
        var pathD = '';
        pts.forEach(function(p, i) {
          if (p.y == null) return;
          if (!pathD || pts.slice(0, i).every(function(q){ return q.y == null; })) {
            pathD += 'M' + p.x.toFixed(1) + ',' + p.y.toFixed(1);
          } else {
            pathD += ' L' + p.x.toFixed(1) + ',' + p.y.toFixed(1);
          }
        });
        var svgContent = '';
        // Area fill
        var firstP = pts.find(function(p){ return p.y != null; });
        var lastP = null; pts.forEach(function(p){ if(p.y != null) lastP = p; });
        if (firstP && lastP && pathD) {
          var fillD = pathD + ' L' + lastP.x.toFixed(1) + ',' + (H - pad) + ' L' + firstP.x.toFixed(1) + ',' + (H - pad) + ' Z';
          svgContent += '<path d="' + fillD + '" fill="rgba(99,102,241,0.15)" stroke="none"/>';
          svgContent += '<path d="' + pathD + '" fill="none" stroke="#6366f1" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>';
        }
        // Dots
        pts.forEach(function(p) {
          if (p.y == null) return;
          svgContent += '<circle cx="' + p.x.toFixed(1) + '" cy="' + p.y.toFixed(1) + '" r="2.5" fill="#6366f1"/>';
        });
        svgEl.innerHTML = svgContent;
      } else {
        svgEl.innerHTML = '<text x="80" y="28" text-anchor="middle" fill="var(--text-muted)" font-size="10">Not enough data</text>';
      }
    }
  } catch(e) {
    console.warn('autonomy load failed', e);
    if (scoreEl) scoreEl.textContent = '--';
    if (gapEl) gapEl.textContent = 'No data yet \u2014 start using your agent to track autonomy';
  }
}

async function loadAll() {
  try {
    // Render overview quickly; do not block on heavy usage aggregation.
    var overview = await fetchJsonWithTimeout('/api/overview', 3000);

    // Start secondary panels immediately.
    startActiveTasksRefresh();
    loadAutonomy().catch(function(e){console.warn('autonomy failed',e)});
    loadActivityStream().catch(function(e){console.warn('activity stream failed',e)});
    loadHealth().catch(function(e){console.warn('health failed',e)});
    loadMCTasks().catch(function(e){console.warn('mctasks failed',e)});
    if (typeof loadReliabilityCard === 'function') loadReliabilityCard().catch(function(e){console.warn('reliability card failed',e)});
    if (typeof loadAnomalyPanel === 'function') loadAnomalyPanel().catch(function(e){console.warn('anomaly panel failed',e)});
    if (typeof loadTokenVelocity === 'function') loadTokenVelocity().catch(function(e){console.warn('velocity check failed',e)});
    if (typeof loadDiagnostics === 'function') loadDiagnostics().catch(function(e){console.warn('diagnostics failed',e)});
    if (typeof loadHeartbeat === 'function') loadHeartbeat().catch(function(e){console.warn('heartbeat panel failed',e)});
    document.getElementById('refresh-time').textContent = 'Updated ' + new Date().toLocaleTimeString();

    if (overview.infra) {
      var i = overview.infra;
      if (i.runtime) setFlowTextAll('infra-runtime-text', i.runtime, 18);
      if (i.machine) setFlowTextAll('infra-machine-text', i.machine, 18);
      if (i.storage) setFlowTextAll('infra-storage-text', i.storage, 16);
      if (i.network) setFlowTextAll('infra-network-text', 'LAN ' + i.network, 18);
      if (i.userName) setFlowTextAll('flow-human-name', i.userName, 10);
    }

    // If overview cannot determine model yet, use brain endpoint fallback immediately.
    if (!overview.model || overview.model === 'unknown') {
      var fallbackModel = await resolvePrimaryModelFallback();
      if (fallbackModel && fallbackModel !== 'unknown') {
        overview.model = fallbackModel;
      }
    }
    if (overview.model && overview.model !== 'unknown') {
      applyBrainModelToAll(overview.model);
    }

    // Usage may be slow on first run; keep trying in background with timeout.
    try {
      var usage = await fetchJsonWithTimeout('/api/usage', 5000);
      loadMiniWidgets(overview, usage);
    } catch (e) {
      // Keep UI responsive with placeholder values until next refresh.
      loadMiniWidgets(overview, {todayCost:0, weekCost:0, monthCost:0, month:0, today:0});
    }
    return true;
  } catch (e) {
    console.error('Initial load failed', e);
    document.getElementById('refresh-time').textContent = 'Load failed - retrying...';
    return false;
  }
}

async function loadReliabilityCard() {
  try {
    var r = await fetchJsonWithTimeout('/api/history/reliability', 5000);
    var icons = {improving:'📈',degrading:'⚠️',stable:'✅',insufficient_data:'🔄'};
    var icon = icons[r.direction] || '🔄';
    var label = r.direction === 'insufficient_data' ? 'No data' : r.direction.charAt(0).toUpperCase() + r.direction.slice(1);
    var el = document.getElementById('reliability-icon');
    if (el) el.textContent = icon;
    el = document.getElementById('reliability-direction');
    if (el) el.textContent = label;
    el = document.getElementById('reliability-detail');
    if (el) el.textContent = r.session_count + ' sessions / ' + r.window_days + 'd';
    el = document.getElementById('reliability-icon-lt');
    if (el) el.textContent = icon;
    el = document.getElementById('reliability-direction-lt');
    if (el) el.textContent = label;
    el = document.getElementById('reliability-detail-lt');
    if (el) el.textContent = r.session_count + ' sessions / ' + r.window_days + 'd';
  } catch(e) { console.warn('reliability card load failed', e); }
}

async function loadHeartbeat() {
  try {
    var d = await fetchJsonWithTimeout('/api/heartbeat', 5000);
    var dot = document.getElementById('hb-pulse-dot');
    var label = document.getElementById('hb-pulse-label');
    var badge = document.getElementById('hb-status-badge');
    var lastBeat = document.getElementById('hb-last-beat');
    var cadenceEl = document.getElementById('hb-cadence');
    var okRatioEl = document.getElementById('hb-ok-ratio');
    var actionRatioEl = document.getElementById('hb-action-ratio');
    var sparkEl = document.getElementById('hb-sparkline');

    if (!dot) return;

    var status = d.status || 'never';
    var colors = { healthy: '#22c55e', drifting: '#f59e0b', missed: '#ef4444', never: '#6b7280' };
    var anims = {
      healthy: 'hb-pulse-healthy 2s ease-in-out infinite',
      drifting: 'hb-pulse-drifting 1.5s ease-in-out infinite',
      missed: 'hb-pulse-missed 1.2s ease-in-out infinite',
      never: 'none'
    };
    var badgeColors = {
      healthy: { bg: 'rgba(34,197,94,0.15)', color: '#4ade80' },
      drifting: { bg: 'rgba(245,158,11,0.15)', color: '#fbbf24' },
      missed: { bg: 'rgba(239,68,68,0.15)', color: '#f87171' },
      never: { bg: 'rgba(107,114,128,0.15)', color: '#9ca3af' }
    };

    dot.style.background = colors[status] || colors.never;
    dot.style.animation = anims[status] || 'none';
    if (label) label.textContent = status;

    if (badge) {
      var bc = badgeColors[status] || badgeColors.never;
      badge.style.background = bc.bg;
      badge.style.color = bc.color;
      badge.textContent = status.charAt(0).toUpperCase() + status.slice(1);
    }

    // Last beat age
    if (lastBeat) {
      if (d.last_heartbeat_age_seconds !== null && d.last_heartbeat_age_seconds !== undefined) {
        var age = d.last_heartbeat_age_seconds;
        var ageStr;
        if (age < 60) ageStr = age + 's ago';
        else if (age < 3600) ageStr = Math.floor(age / 60) + ' min ago';
        else if (age < 86400) ageStr = Math.floor(age / 3600) + 'h ago';
        else ageStr = Math.floor(age / 86400) + 'd ago';
        lastBeat.textContent = ageStr;
        lastBeat.style.color = colors[status] || '#9ca3af';
      } else {
        lastBeat.textContent = 'never';
        lastBeat.style.color = '#9ca3af';
      }
    }

    // Cadence
    if (cadenceEl && d.cadence_24h) {
      var c = d.cadence_24h;
      var pct = c.expected_beats > 0 ? Math.round(c.on_time_ratio * 100) : 0;
      cadenceEl.textContent = c.actual_beats + ' / ' + c.expected_beats + ' expected (' + pct + '%)';
    }

    // OK vs Action ratios
    if (okRatioEl && d.ok_vs_action_24h) {
      var oa = d.ok_vs_action_24h;
      okRatioEl.textContent = Math.round(oa.ok_ratio * 100) + '%';
      if (actionRatioEl) {
        var actionPct = Math.round((1 - oa.ok_ratio) * 100);
        actionRatioEl.textContent = actionPct + '%';
        actionRatioEl.style.color = actionPct > 20 ? '#f87171' : '#fbbf24';
      }
    }

    // Sparkline of last 10 beats
    if (sparkEl && d.recent_beats && d.recent_beats.length > 0) {
      sparkEl.innerHTML = d.recent_beats.map(function(b) {
        var c = b.outcome === 'ok' ? '#22c55e' : '#f59e0b';
        var title = b.outcome === 'ok' ? 'HEARTBEAT_OK' : 'Action taken';
        return '<span title="' + title + '" style="display:inline-block;width:10px;height:10px;border-radius:50%;background:' + c + ';"></span>';
      }).join('');
    } else if (sparkEl) {
      sparkEl.innerHTML = '<span style="font-size:11px;color:var(--text-muted);">no beats yet</span>';
    }
  } catch(e) { console.warn('heartbeat panel load failed', e); }
}

async function loadMiniWidgets(overview, usage) {
  // 💰 Cost Ticker 
  function fmtCost(c) { return c >= 0.01 ? '$' + c.toFixed(2) : c > 0 ? '<$0.01' : '$0.00'; }
  document.getElementById('cost-today').textContent = fmtCost(usage.todayCost || 0);
  document.getElementById('cost-week').textContent = fmtCost(usage.weekCost || 0);
  document.getElementById('cost-month').textContent = fmtCost(usage.monthCost || 0);
  
  var trend = '';
  if (usage.trend && usage.trend.trend) {
    var trendIcon = usage.trend.trend === 'increasing' ? '📈' : usage.trend.trend === 'decreasing' ? '📉' : '➡️';
    trend = trendIcon + ' ' + usage.trend.trend;
  }
  var isOauthLikely = (usage.billingSummary === 'likely_oauth_or_included');
  var isMixed = (usage.billingSummary === 'mixed');
  var trendEl = document.getElementById('cost-trend');
  var badgeEl = document.getElementById('cost-billing-badge');
  var infoIcon = document.getElementById('cost-info-icon');

  if (isOauthLikely) {
    if (badgeEl) {
      badgeEl.style.display = '';
      badgeEl.textContent = 'est. equivalent if billed - OAuth likely';
    }
    trendEl.style.display = 'none';
  } else {
    if (badgeEl) {
      badgeEl.style.display = 'none';
      badgeEl.textContent = '';
    }
    trendEl.textContent = trend || 'Today\'s running total';
    trendEl.style.display = trend ? '' : 'none';
  }

  if (infoIcon) {
    if (isOauthLikely || isMixed) {
      infoIcon.style.display = '';
      infoIcon.title = 'Equivalent if billed from token usage. OAuth/included models may be billed $0 at provider level.';
    } else {
      infoIcon.style.display = 'none';
      infoIcon.title = '';
    }
  }

  applyBillingHintToFlow(usage.billingSummary || 'unknown');

  // Budget enforcement widget: hard-cap banner + burn rate + projected monthly cost.
  try {
    var status = await fetch('/api/budget/status').then(function(r){ return r.json(); });
    var now = new Date();
    var elapsedHours = now.getHours() + (now.getMinutes() / 60.0) + (now.getSeconds() / 3600.0);
    elapsedHours = elapsedHours > 0 ? elapsedHours : 1 / 60.0;
    var burnTokensHr = (usage.today || 0) / elapsedHours;
    var burnCostHr = (usage.todayCost || 0) / elapsedHours;
    var daysInMonth = new Date(now.getFullYear(), now.getMonth() + 1, 0).getDate();
    var projectedMonthlyCost = burnCostHr * 24 * daysInMonth;

    var burnEl = document.getElementById('budget-burn-rate');
    var projEl = document.getElementById('budget-projected-month');
    if (burnEl) burnEl.textContent = Math.round(burnTokensHr).toLocaleString() + ' tok/h';
    if (projEl) projEl.textContent = fmtCost(projectedMonthlyCost);

    var banner = document.getElementById('budget-cap-banner');
    var bannerMsg = document.getElementById('budget-cap-banner-msg');
    var dailyLimit = Number(status.daily_limit || 0);
    var dailySpent = Number(status.daily_spent || 0);
    if (banner && bannerMsg) {
      if (dailyLimit > 0 && dailySpent > dailyLimit) {
        bannerMsg.textContent = 'Daily hard cap exceeded: ' + fmtCost(dailySpent) + ' / ' + fmtCost(dailyLimit);
        banner.style.display = 'flex';
      } else {
        banner.style.display = 'none';
      }
    }
  } catch (e) {
    var burnFallback = document.getElementById('budget-burn-rate');
    var projFallback = document.getElementById('budget-projected-month');
    if (burnFallback) burnFallback.textContent = '--';
    if (projFallback) projFallback.textContent = '--';
  }
  
  // ⚡ Tool Activity (load from logs)
  loadToolActivity();
  
  // 📊 Token Burn Rate
  function fmtTokens(n) { return n >= 1000000 ? (n/1000000).toFixed(1) + 'M' : n >= 1000 ? (n/1000).toFixed(0) + 'K' : String(n); }
  document.getElementById('token-rate').textContent = fmtTokens(usage.month || 0);
  document.getElementById('tokens-today').textContent = fmtTokens(usage.today || 0);
  
  // 🔥 Hot Sessions -- use /api/sessions for consistency with modal
  fetch('/api/sessions').then(function(r){return r.json()}).then(function(sd) {
    var sl = sd.sessions || sd || [];
    if (!Array.isArray(sl)) sl = [];
    document.getElementById('hot-sessions-count').textContent = sl.length;
  }).catch(function() {
    document.getElementById('hot-sessions-count').textContent = overview.sessionCount || 0;
  });
  
  // 📈 Model Mix
  document.getElementById('model-primary').textContent = overview.model || 'unknown';
  var modelLabel = document.getElementById('main-activity-model');
  if (modelLabel && overview.model) {
    var m = overview.model;
    if (m.indexOf('/') !== -1) m = m.split('/').pop();
    m = m.replace(/-/g, ' ').replace(/\b\w/g, function(c){return c.toUpperCase();});
    modelLabel.textContent = m;
  }
  var modelBreakdown = '';
  if (usage.modelBreakdown && usage.modelBreakdown.length > 0) {
    var primary = usage.modelBreakdown[0];
    var others = usage.modelBreakdown.slice(1, 3);
    modelBreakdown = fmtTokens(primary.tokens) + ' tokens';
    if (others.length > 0) {
      modelBreakdown += ' (+' + others.length + ' others)';
    }
  } else {
    modelBreakdown = 'Primary model';
  }
  document.getElementById('model-breakdown').textContent = modelBreakdown;
  
  // 🐝 Worker Bees (Sub-Agents)
  loadSubAgents();
  
}

async function loadSubAgents() {
  try {
    var data = await fetch('/api/subagents').then(r => r.json());
    var counts = data.counts;
    var subagents = data.subagents;
    
    // Update main counter
    document.getElementById('subagents-count').textContent = counts.total;
    
    // Update status text
    var statusText = '';
    if (counts.active > 0) {
      statusText = counts.active + ' active';
      if (counts.idle > 0) statusText += ', ' + counts.idle + ' idle';
      if (counts.stale > 0) statusText += ', ' + counts.stale + ' stale';
    } else if (counts.total === 0) {
      statusText = 'No sub-agents spawned';
    } else {
      statusText = 'All idle/stale';
    }
    document.getElementById('subagents-status').textContent = statusText;
    
    // Update preview with top sub-agents (human-readable)
    var previewHtml = '';
    if (subagents.length === 0) {
      previewHtml = '<div style="font-size:11px;color:#666;">No active tasks</div>';
    } else {
      // Show active ones first
      var activeFirst = subagents.filter(function(a){return a.status==='active';}).concat(subagents.filter(function(a){return a.status!=='active';}));
      var topAgents = activeFirst.slice(0, 3);
      topAgents.forEach(function(agent) {
        var icon = agent.status === 'active' ? '🔄' : agent.status === 'idle' ? '[ok]' : '⬜';
        var name = cleanTaskName(agent.displayName);
        if (name.length > 40) name = name.substring(0, 37) + '…';
        previewHtml += '<div class="subagent-item">';
        previewHtml += '<span style="font-size:10px;">' + icon + '</span>';
        previewHtml += '<span class="subagent-name" style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">' + escHtml(name) + '</span>';
        previewHtml += '<span class="subagent-runtime">' + agent.runtime + '</span>';
        previewHtml += '</div>';
      });
      
      if (subagents.length > 3) {
        previewHtml += '<div style="font-size:9px;color:#555;margin-top:4px;">+' + (subagents.length - 3) + ' more</div>';
      }
    }
    
    document.getElementById('subagents-preview').innerHTML = previewHtml;
    
  } catch(e) {
    document.getElementById('subagents-count').textContent = '?';
    document.getElementById('subagents-status').textContent = 'Error loading sub-agents';
    document.getElementById('subagents-preview').innerHTML = '<div style="color:#e74c3c;font-size:11px;">Failed to load workforce</div>';
  }
}

// === Active Tasks for Overview ===
var _activeTasksTimer = null;
function cleanTaskName(raw) {
  // Strip timestamp prefixes like "[Sun 2026-02-08 18:22 GMT+1] "
  var name = (raw || '').replace(/^\[.*?\]\s*/, '');
  // Truncate to first sentence or 80 chars
  var dot = name.indexOf('. ');
  if (dot > 10 && dot < 80) name = name.substring(0, dot + 1);
  if (name.length > 80) name = name.substring(0, 77) + '…';
  return name || 'Background task';
}

function detectProjectBadge(text) {
  var projects = {
    'mockround': { label: 'MockRound', color: '#7c3aed' },
    'vedicvoice': { label: 'VedicVoice', color: '#d97706' },
    'openclaw': { label: 'OpenClaw', color: '#2563eb' },
    'dashboard': { label: 'Dashboard', color: '#0891b2' },
    'shopify': { label: 'Shopify', color: '#16a34a' },
    'sanskrit': { label: 'Sanskrit', color: '#ea580c' },
    'telegram': { label: 'Telegram', color: '#0088cc' },
    'discord': { label: 'Discord', color: '#5865f2' },
  };
  var lower = (text || '').toLowerCase();
  for (var key in projects) {
    if (lower.includes(key)) return projects[key];
  }
  return null;
}

function humanTime(runtimeMs) {
  if (!runtimeMs || runtimeMs === Infinity) return '';
  var sec = Math.floor(runtimeMs / 1000);
  if (sec < 60) return 'Started ' + sec + 's ago';
  var min = Math.floor(sec / 60);
  if (min < 60) return 'Started ' + min + ' min ago';
  var hr = Math.floor(min / 60);
  if (hr < 24) return 'Started ' + hr + 'h ago';
  return 'Started ' + Math.floor(hr / 24) + 'd ago';
}

function humanTimeDone(runtimeMs) {
  if (!runtimeMs || runtimeMs === Infinity) return '';
  var sec = Math.floor(runtimeMs / 1000);
  if (sec < 60) return 'Finished ' + sec + 's ago';
  var min = Math.floor(sec / 60);
  if (min < 60) return 'Finished ' + min + ' min ago';
  var hr = Math.floor(min / 60);
  if (hr < 24) return 'Finished ' + hr + 'h ago';
  return 'Finished ' + Math.floor(hr / 24) + 'd ago';
}

async function loadActiveTasks() {
  try {
    var grid = document.getElementById('overview-tasks-list') || document.getElementById('active-tasks-grid');
    if (!grid) return;

    // Fetch active sub-agents
    var saData = await fetch('/api/subagents').then(r => r.json()).catch(function() { return {subagents:[]}; });

    var agents = (saData.subagents || []).filter(function(a) {
      return a.status === 'active';
    });

    if (agents.length === 0) {
      grid.innerHTML = '<div class="card" style="text-align:center;padding:24px;color:var(--text-muted);grid-column:1/-1;">'
        + '<div style="font-size:24px;margin-bottom:8px;">✨</div>'
        + '<div style="font-size:13px;">No active tasks - all quiet</div></div>';
      var badge = document.getElementById('overview-tasks-count-badge');
      if (badge) badge.textContent = '';
      return;
    }

    var html = '';
    var badge = document.getElementById('overview-tasks-count-badge');
    if (badge) badge.textContent = agents.length + ' active';

    // Render active sub-agents
    agents.forEach(function(agent) {
      var taskName = cleanTaskName(agent.displayName);
      var badge2 = detectProjectBadge(agent.displayName);
      var mins = Math.max(1, Math.floor((agent.runtimeMs || 0) / 60000));

      html += '<div class="task-card running" style="cursor:pointer;" onclick="openTaskModal(\'' + escHtml(agent.sessionId).replace(/'/g,"\\'") + '\',\'' + escHtml(taskName).replace(/'/g,"\\'") + '\',\'' + escHtml(agent.key || agent.sessionId).replace(/'/g,"\\'") + '\')">';
      html += '<div class="task-card-pulse active"></div>';
      html += '<div class="task-card-header">';
      html += '<div class="task-card-name">' + escHtml(taskName) + '</div>';
      html += '<span class="task-card-badge running" style="font-size:10px;">🤖 ' + mins + ' min</span>';
      html += '</div>';
      html += '<div style="display:flex;align-items:center;gap:8px;">';
      if (badge2) {
        html += '<span style="display:inline-block;padding:1px 8px;border-radius:10px;font-size:10px;font-weight:700;background:' + badge2.color + '22;color:' + badge2.color + ';border:1px solid ' + badge2.color + '44;">' + badge2.label + '</span>';
      }
      html += '<span style="font-size:11px;color:var(--text-muted);">' + escHtml(humanTime(agent.runtimeMs)) + '</span>';
      html += '</div>';
      html += '</div>';
    });

    grid.innerHTML = html;
  } catch(e) {
    // silently fail
  }
}
// Auto-refresh active tasks every 30s
function startActiveTasksRefresh() {
  loadActiveTasks();
  if (_activeTasksTimer) clearInterval(_activeTasksTimer);
  _activeTasksTimer = setInterval(loadActiveTasks, 30000);
}

async function loadToolActivity() {
  try {
    var logs = await fetch('/api/logs?lines=100').then(r => r.json());
    var toolCounts = { exec: 0, browser: 0, search: 0, other: 0 };
    var recentTools = [];
    
    logs.lines.forEach(function(line) {
      var msg = line.toLowerCase();
      if (msg.includes('tool') || msg.includes('invoke')) {
        if (msg.includes('exec') || msg.includes('shell')) { 
          toolCounts.exec++; recentTools.push('exec'); 
        } else if (msg.includes('browser') || msg.includes('screenshot')) { 
          toolCounts.browser++; recentTools.push('browser'); 
        } else if (msg.includes('web_search') || msg.includes('web_fetch')) { 
          toolCounts.search++; recentTools.push('search'); 
        } else {
          toolCounts.other++;
        }
      }
    });
    
    document.getElementById('tools-active').textContent = recentTools.slice(0, 3).join(', ') || 'Idle';
    document.getElementById('tools-recent').textContent = 'Last ' + Math.min(logs.lines.length, 100) + ' log entries';
    
    var sparks = document.querySelectorAll('.tool-spark span');
    sparks[0].textContent = toolCounts.exec;
    sparks[1].textContent = toolCounts.browser;  
    sparks[2].textContent = toolCounts.search;
  } catch(e) {
    document.getElementById('tools-active').textContent = '--';
  }
}

async function loadActivityStream() {
  try {
    var transcripts = await fetchJsonWithTimeout('/api/transcripts', 4000);
    var activities = [];
    
    // Get the most recent transcript to parse for activity
    if (transcripts.transcripts && transcripts.transcripts.length > 0) {
      var recent = transcripts.transcripts[0];
      try {
        var transcript = await fetchJsonWithTimeout('/api/transcript/' + recent.id, 4000);
        var recentMessages = transcript.messages.slice(-10); // Last 10 messages
        
        recentMessages.forEach(function(msg) {
          if (msg.role === 'assistant' && msg.content) {
            var content = msg.content.toLowerCase();
            var activity = '';
            var time = new Date(msg.timestamp || Date.now()).toLocaleTimeString();
            
            if (content.includes('searching') || content.includes('search')) {
              activity = time + ' [check] Searching web for information';
            } else if (content.includes('reading') || content.includes('file')) {
              activity = time + ' 📖 Reading files';
            } else if (content.includes('writing') || content.includes('edit')) {
              activity = time + ' ✏️ Editing files'; 
            } else if (content.includes('exec') || content.includes('command')) {
              activity = time + ' ⚡ Running commands';
            } else if (content.includes('browser') || content.includes('screenshot')) {
              activity = time + ' 🌐 Browser automation';
            } else if (msg.content.length > 50) {
              var preview = msg.content.substring(0, 80).replace(/[^\w\s]/g, ' ').trim();
              activity = time + ' 💭 ' + preview + '...';
            }
            
            if (activity) activities.push(activity);
          }
        });
      } catch(e) {}
    }
    
    if (activities.length === 0) {
      activities = [
        new Date().toLocaleTimeString() + ' 🤖 AI agent initialized',
        new Date().toLocaleTimeString() + ' 📡 Monitoring for activity...'
      ];
    }
    
    var html = activities.slice(-8).map(function(a) {
      return '<div style="padding:4px 0; border-bottom:1px solid #1a1a30; color:#ccc;">' + escHtml(a) + '</div>';
    }).join('');
    
    document.getElementById('activity-stream').innerHTML = html;
  } catch(e) {
    document.getElementById('activity-stream').innerHTML = '<div style="color:#666;">Error loading activity stream</div>';
  }
}


// ── Brain tab
// ── Brain tab ─────────────────────────────────────────────────────────
var _brainRefreshTimer = null;
var _brainSourceColors = {};
var _brainColorPalette = ['#2dd4bf','#f97316','#eab308','#ec4899','#3b82f6','#a78bfa','#f43f5e','#10b981'];
var _brainColorIdx = 0;

function brainSourceColor(source) {
  if (source === 'main') return '#a855f7';
  if (!_brainSourceColors[source]) {
    _brainSourceColors[source] = _brainColorPalette[_brainColorIdx % _brainColorPalette.length];
    _brainColorIdx++;
  }
  return _brainSourceColors[source];
}

function formatBrainTime(isoStr) {
  try {
    var d = new Date(isoStr);
    var now = new Date();
    var sameDay = d.getFullYear()===now.getFullYear() && d.getMonth()===now.getMonth() && d.getDate()===now.getDate();
    var time = d.toLocaleTimeString('en-GB', {hour:'2-digit',minute:'2-digit',second:'2-digit'});
    var prefix = sameDay ? 'Today' : d.toLocaleDateString('en-GB', {day:'numeric',month:'short'});
    return '<span style="opacity:0.45;font-size:10px;margin-right:3px;">' + prefix + '</span>' + time;
  } catch(e) { return isoStr || ''; }
}

function renderBrainDetail(detail) {
  if (!detail) return '';
  var s = detail.trim();
  // Try JSON rendering
  var jsonMatch = s.match(/^```json\s*([\s\S]*?)```$/) || s.match(/^(\{[\s\S]*\}|\[[\s\S]*\])$/);
  if (jsonMatch) {
    try {
      var obj = JSON.parse(jsonMatch[1] || jsonMatch[0]);
      var pretty = JSON.stringify(obj, null, 2);
      return '<pre style="background:var(--bg-tertiary,#1a1a2e);border:1px solid var(--border-primary,#333);border-radius:6px;padding:8px 10px;margin:4px 0 0;font-size:11px;color:var(--text-secondary);overflow-x:auto;white-space:pre-wrap;word-break:break-all;max-height:180px;">' + escHtml(pretty) + '</pre>';
    } catch(e) {}
  }
  // Inline markdown: **bold**, `code`, ```block```
  var html = escHtml(s);
  // Code blocks
  html = html.replace(/```([\s\S]*?)```/g, '<pre style="background:var(--bg-tertiary,#1a1a2e);border:1px solid var(--border-primary,#333);border-radius:6px;padding:6px 10px;margin:4px 0 0;font-size:11px;overflow-x:auto;white-space:pre-wrap;max-height:180px;">$1</pre>');
  // Inline code
  html = html.replace(/`([^`]+)`/g, '<code style="background:var(--bg-tertiary,#1a1a2e);padding:1px 5px;border-radius:3px;font-size:11px;">$1</code>');
  // Bold
  html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
  return '<span style="white-space:pre-wrap;word-break:break-word;">' + html + '</span>';
}

var _brainFilter = 'all';
var _brainTypeFilter = 'all';
var _brainAllEvents = [];
var _brainViewMode = 'list';
var _brainGraph = {
  canvas: null,
  ctx: null,
  width: 0,
  height: 500,
  dpr: 1,
  lastTs: 0,
  rafId: 0,
  animating: false,
  agents: {},
  agentOrder: [],
  events: [],
  lastPulseAt: 0
};
var _brainGraphResizeBound = false;

function _brainGraphHash(str) {
  var h = 2166136261;
  str = String(str || '');
  for (var i = 0; i < str.length; i++) {
    h ^= str.charCodeAt(i);
    h += (h << 1) + (h << 4) + (h << 7) + (h << 8) + (h << 24);
  }
  return h >>> 0;
}

function _brainGraphEnsureCanvas() {
  var canvas = document.getElementById('brain-graph-canvas');
  if (!canvas) return false;
  if (!_brainGraph.canvas) {
    _brainGraph.canvas = canvas;
    _brainGraph.ctx = canvas.getContext('2d');
  }
  var rect = canvas.getBoundingClientRect();
  var dpr = Math.max(1, window.devicePixelRatio || 1);
  var w = Math.max(320, Math.floor(rect.width || canvas.clientWidth || 800));
  var h = 500;
  if (canvas.width !== Math.floor(w * dpr) || canvas.height !== Math.floor(h * dpr)) {
    canvas.width = Math.floor(w * dpr);
    canvas.height = Math.floor(h * dpr);
  }
  _brainGraph.dpr = dpr;
  _brainGraph.width = w;
  _brainGraph.height = h;
  return true;
}

function setBrainViewMode(mode, btn) {
  _brainViewMode = 'list';
}

function syncBrainGraph(events) {
  events = Array.isArray(events) ? events : [];
  var oldAgents = _brainGraph.agents || {};
  var oldEvents = {};
  (_brainGraph.events || []).forEach(function(node) { oldEvents[node.id] = node; });
  var now = Date.now();
  var centerX = (_brainGraph.width || 900) / 2;
  var centerY = (_brainGraph.height || 500) / 2;
  var recent = events.slice(0, 200);
  var agentMap = {};
  recent.forEach(function(ev) {
    var source = ev && ev.source ? ev.source : 'main';
    if (!agentMap[source]) {
      agentMap[source] = {
        id: source,
        label: ev && ev.sourceLabel ? ev.sourceLabel : source,
        lastSeen: 0,
        count: 0
      };
    }
    var ts = ev && ev.time ? (new Date(ev.time).getTime() || 0) : 0;
    if (ts > agentMap[source].lastSeen) agentMap[source].lastSeen = ts;
    agentMap[source].count++;
  });
  if (!agentMap.main && recent.length) {
    agentMap.main = {id: 'main', label: 'main', lastSeen: now, count: 1};
  }
  var agentIds = Object.keys(agentMap).sort(function(a, b) {
    var da = agentMap[a], db = agentMap[b];
    if (db.lastSeen !== da.lastSeen) return db.lastSeen - da.lastSeen;
    return db.count - da.count;
  }).slice(0, 20);
  var chosen = {};
  agentIds.forEach(function(id) { chosen[id] = true; });
  var nextAgents = {};
  var ringR = Math.max(90, Math.min(180, Math.min(centerX, centerY) - 40));
  agentIds.forEach(function(id, i) {
    var baseAngle = (Math.PI * 2 * i) / Math.max(1, agentIds.length);
    var prev = oldAgents[id];
    nextAgents[id] = {
      id: id,
      label: agentMap[id].label || id,
      lastSeen: agentMap[id].lastSeen || 0,
      x: prev ? prev.x : centerX + Math.cos(baseAngle) * ringR,
      y: prev ? prev.y : centerY + Math.sin(baseAngle) * ringR,
      vx: prev ? prev.vx : 0,
      vy: prev ? prev.vy : 0,
      r: 14
    };
  });
  var nextEvents = [];
  for (var ei = 0; ei < events.length && nextEvents.length < 50; ei++) {
    var ev = events[ei];
    var source = ev && ev.source ? ev.source : 'main';
    if (!chosen[source]) continue;
    var key = (ev.time || '') + '|' + source + '|' + (ev.type || '') + '|' + (ev.detail || '');
    var id = 'ev:' + _brainGraphHash(key).toString(16);
    var prevNode = oldEvents[id];
    var agent = nextAgents[source];
    var seed = _brainGraphHash(id);
    var angle = ((seed % 6283) / 1000);
    nextEvents.push({
      id: id,
      source: source,
      type: ev.type || 'TOOL',
      color: ev.color || brainSourceColor(source),
      x: prevNode ? prevNode.x : (agent.x + Math.cos(angle) * 42),
      y: prevNode ? prevNode.y : (agent.y + Math.sin(angle) * 42),
      vx: prevNode ? prevNode.vx : 0,
      vy: prevNode ? prevNode.vy : 0,
      orbitR: 34 + (seed % 24),
      orbitSpeed: 0.00025 + ((seed % 100) / 500000),
      orbitPhase: angle,
      r: 4
    });
  }
  _brainGraph.agents = nextAgents;
  _brainGraph.agentOrder = agentIds;
  _brainGraph.events = nextEvents;
}

function _startBrainGraphLoop() {
  if (_brainGraph.animating) return;
  _brainGraph.animating = true;
  _brainGraph.lastTs = 0;
  _brainGraph.rafId = requestAnimationFrame(_brainGraphTick);
}

function _brainGraphTick(ts) {
  _brainGraph.rafId = requestAnimationFrame(_brainGraphTick);
  if (_brainViewMode !== 'graph') return;
  if (!document.getElementById('page-brain') || !document.getElementById('page-brain').classList.contains('active')) return;
  if (!_brainGraphEnsureCanvas()) return;
  var dt = _brainGraph.lastTs ? Math.min(33, ts - _brainGraph.lastTs) / 16.67 : 1;
  _brainGraph.lastTs = ts;
  var now = Date.now();
  var agents = _brainGraph.agentOrder.map(function(id) { return _brainGraph.agents[id]; }).filter(Boolean);
  var events = _brainGraph.events;
  var W = _brainGraph.width;
  var H = _brainGraph.height;
  var cx = W / 2;
  var cy = H / 2;
  agents.forEach(function(a) {
    var dx = cx - a.x;
    var dy = cy - a.y;
    a.vx += dx * 0.0007 * dt;
    a.vy += dy * 0.0007 * dt;
  });
  for (var i = 0; i < agents.length; i++) {
    for (var j = i + 1; j < agents.length; j++) {
      var a = agents[i], b = agents[j];
      var dx = b.x - a.x, dy = b.y - a.y;
      var d2 = dx * dx + dy * dy + 0.01;
      var d = Math.sqrt(d2);
      var force = Math.min(6, 900 / d2);
      var fx = (dx / d) * force;
      var fy = (dy / d) * force;
      a.vx -= fx * dt; a.vy -= fy * dt;
      b.vx += fx * dt; b.vy += fy * dt;
    }
  }
  if (ts - _brainGraph.lastPulseAt > 2000) {
    agents.forEach(function(a) {
      if (now - a.lastSeen < 90000) {
        if (!a.pulses) a.pulses = [];
        a.pulses.push({start: ts});
      }
    });
    _brainGraph.lastPulseAt = ts;
  }
  agents.forEach(function(a) {
    a.vx *= 0.9; a.vy *= 0.9;
    a.x += a.vx * dt;
    a.y += a.vy * dt;
    a.x = Math.max(24, Math.min(W - 24, a.x));
    a.y = Math.max(24, Math.min(H - 24, a.y));
  });
  events.forEach(function(ev, idx) {
    var agent = _brainGraph.agents[ev.source];
    if (!agent) return;
    var orbitA = ev.orbitPhase + ts * ev.orbitSpeed;
    var tx = agent.x + Math.cos(orbitA) * ev.orbitR;
    var ty = agent.y + Math.sin(orbitA) * ev.orbitR;
    ev.vx += (tx - ev.x) * 0.04 * dt;
    ev.vy += (ty - ev.y) * 0.04 * dt;
    for (var k = idx + 1; k < events.length; k++) {
      var other = events[k];
      if (other.source !== ev.source) continue;
      var rx = other.x - ev.x;
      var ry = other.y - ev.y;
      var rd2 = rx * rx + ry * ry + 0.01;
      if (rd2 > 1200) continue;
      var rf = 20 / rd2;
      ev.vx -= rx * rf * dt;
      ev.vy -= ry * rf * dt;
      other.vx += rx * rf * dt;
      other.vy += ry * rf * dt;
    }
    ev.vx *= 0.88; ev.vy *= 0.88;
    ev.x += ev.vx * dt;
    ev.y += ev.vy * dt;
    ev.x = Math.max(8, Math.min(W - 8, ev.x));
    ev.y = Math.max(8, Math.min(H - 8, ev.y));
  });
  _drawBrainGraph(ts, now);
}

function _drawBrainGraph(ts, now) {
  var ctx = _brainGraph.ctx;
  if (!ctx) return;
  var dpr = _brainGraph.dpr || 1;
  var W = _brainGraph.width;
  var H = _brainGraph.height;
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, W, H);
  ctx.fillStyle = 'rgba(20,23,34,0.35)';
  ctx.fillRect(0, 0, W, H);
  _brainGraph.events.forEach(function(ev) {
    var a = _brainGraph.agents[ev.source];
    if (!a) return;
    ctx.strokeStyle = 'rgba(148,163,184,0.22)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(a.x, a.y);
    ctx.lineTo(ev.x, ev.y);
    ctx.stroke();
  });
  _brainGraph.events.forEach(function(ev) {
    ctx.shadowBlur = 8;
    ctx.shadowColor = ev.color || '#60a5fa';
    ctx.fillStyle = ev.color || '#60a5fa';
    ctx.beginPath();
    ctx.arc(ev.x, ev.y, ev.r, 0, Math.PI * 2);
    ctx.fill();
  });
  _brainGraph.agentOrder.forEach(function(id) {
    var a = _brainGraph.agents[id];
    if (!a) return;
    var active = now - a.lastSeen < 90000;
    var color = active ? '#a855f7' : '#f59e0b';
    if (!a.pulses) a.pulses = [];
    a.pulses = a.pulses.filter(function(p) { return ts - p.start < 1200; });
    a.pulses.forEach(function(p) {
      var age = ts - p.start;
      var t = age / 1200;
      var radius = a.r + (44 * t);
      var alpha = Math.max(0, 0.35 * (1 - t));
      ctx.strokeStyle = active ? 'rgba(168,85,247,' + alpha + ')' : 'rgba(245,158,11,' + alpha + ')';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(a.x, a.y, radius, 0, Math.PI * 2);
      ctx.stroke();
    });
    ctx.shadowBlur = 20;
    ctx.shadowColor = color;
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc(a.x, a.y, a.r, 0, Math.PI * 2);
    ctx.fill();
    ctx.shadowBlur = 0;
    ctx.fillStyle = 'rgba(230,234,244,0.92)';
    ctx.font = '11px monospace';
    ctx.textAlign = 'center';
    ctx.fillText((a.label || a.id || 'agent').slice(0, 20), a.x, a.y + 28);
  });
  ctx.shadowBlur = 0;
}

var _brainTypeIcons = {
  'EXEC': '⚙️', 'SHELL': '⚙️', 'READ': '📖', 'WRITE': '✏️',
  'BROWSER': '🌐', 'MSG': '📨', 'SEARCH': '🔍', 'SPAWN': '🚀',
  'DONE': '✅', 'ERROR': '❌', 'TOOL': '🔧',
  'USER': '💬', 'THINK': '🧠', 'AGENT': '🤖'
};


function setBrainTypeFilter(type, btn) {
  _brainTypeFilter = type;
  document.querySelectorAll('.brain-type-chip').forEach(function(b) {
    var isActive = b.dataset.type === type;
    b.style.background = isActive ? 'rgba(168,85,247,0.2)' : 'transparent';
    b.style.fontWeight = isActive ? '600' : '400';
  });
  renderBrainFeed();
}
function setBrainFilter(source, btn) {
  _brainFilter = source;
  // Reset all pills
  document.querySelectorAll('.brain-chip').forEach(function(b) {
    b.classList.remove('active');
    b.style.background = 'transparent';
    b.style.fontWeight = '400';
    b.style.boxShadow = 'none';
    b.style.opacity = '0.45';
  });
  // Highlight selected pill with fill + glow
  btn.classList.add('active');
  var col = btn.style.color || '#a855f7';
  btn.style.background = col;
  btn.style.color = '#0d1117';
  btn.style.fontWeight = '700';
  btn.style.boxShadow = '0 0 8px ' + col;
  btn.style.opacity = '1';
  // Fade others slightly but keep visible
  document.querySelectorAll('.brain-chip:not(.active)').forEach(function(b) {
    b.style.opacity = '0.4';
  });
  var streamEl = document.getElementById('brain-stream');
  var chartEl = document.getElementById('brain-density-chart');
  if (streamEl) streamEl.innerHTML = '<div style="padding:40px;text-align:center;color:#a855f7;font-size:14px;font-weight:500;">● Filtering...</div>';
  if (chartEl) { var ctx2=chartEl.getContext('2d'); ctx2.clearRect(0,0,chartEl.width,chartEl.height); }
  setTimeout(function() {
    renderBrainChart(_brainAllEvents);
    renderBrainStream(_brainAllEvents);
  }, 80);
}

function scrollBrainToTop() {
  var el = document.getElementById('brain-stream');
  if (el) el.scrollTop = 0;
  var pill = document.getElementById('brain-new-pill');
  if (pill) pill.style.display = 'none';
}

function renderBrainFilterChips(sources) {
  var container = document.getElementById('brain-filter-chips');
  if (!container || !sources) return;
  var html = '<button class="brain-chip' + (_brainFilter === 'all' ? ' active' : '') + '" data-source="all" onclick="setBrainFilter(&apos;all&apos;,this)" style="padding:3px 10px;border-radius:12px;border:1px solid #a855f7;background:' + (_brainFilter === 'all' ? 'rgba(168,85,247,0.2)' : 'transparent') + ';color:#a855f7;font-size:11px;cursor:pointer;font-weight:' + (_brainFilter === 'all' ? '600' : '400') + ';">All</button>';
    clawmetry --workspace ~/bot           # Custom workspace
    OPENCLAW_HOME=~/bot clawmetry

https://github.com/vivekchand/clawmetry
MIT License
"""

import os
import sys

# Force UTF-8 output on Windows (emoji in BANNER would crash with cp1252)
if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import threading
from datetime import timezone, timedelta
from flask import (
    Flask,
)

# History / time-series module
try:
    from history import HistoryDB, HistoryCollector, AgentReliabilityScorer

    _HAS_HISTORY = True
except ImportError:
    _HAS_HISTORY = False
    HistoryDB = None
    HistoryCollector = None
    AgentReliabilityScorer = None

_history_db = None
_history_collector = None

# Optional: OpenTelemetry protobuf support for OTLP receiver
_HAS_OTEL_PROTO = False
try:
    from opentelemetry.proto.collector.metrics.v1 import metrics_service_pb2
    from opentelemetry.proto.collector.trace.v1 import trace_service_pb2

    _HAS_OTEL_PROTO = True
except ImportError:
    metrics_service_pb2 = None
    trace_service_pb2 = None


app = Flask(
    __name__,
    static_folder=os.path.join(os.path.dirname(__file__), 'clawmetry', 'static'),
    template_folder=os.path.join(os.path.dirname(__file__), 'clawmetry', 'templates'),
)

# ── Cross-platform helpers ──────────────────────────────────────────────
import platform as _platform


# _grep_log_file, _tail_lines, _get_log_dirs moved to helpers/logs.py (re-exported above)


# _detect_host_hardware moved to helpers/hardware.py (re-exported above)


_CURRENT_PLATFORM = _platform.system().lower()
# ── End cross-platform helpers ──────────────────────────────────────────

# ── Configuration (auto-detected, overridable via CLI/env) ──────────────
MC_URL = os.environ.get("MC_URL", "")  # Optional Mission Control URL, empty = disabled
WORKSPACE = None
MEMORY_DIR = None
LOG_DIR = None
SESSIONS_DIR = None
USER_NAME = None
GATEWAY_URL = None  # e.g. http://localhost:18789
GATEWAY_TOKEN = None  # Bearer token for /tools/invoke
CET = timezone(timedelta(hours=1))
# SSE_MAX_SECONDS moved to helpers/streams.py (re-exported above)
# Stream-slot caps + state moved to helpers/streams.py (re-exported above)
EXTRA_SERVICES = []  # List of {'name': str, 'port': int} from --monitor-service flags
# _active_brain_stream_clients moved to helpers/streams.py

# ── Multi-Node Fleet Configuration ─────────────────────────────────────
FLEET_API_KEY = os.environ.get("CLAWMETRY_FLEET_KEY", "")
FLEET_DB_PATH = None  # Set via CLI or auto-detected
FLEET_NODE_TIMEOUT = 300  # seconds before node is considered offline

# ── Budget & Alert Configuration ───────────────────────────────────────
_budget_paused = False
_budget_paused_at = 0
_budget_paused_reason = ""
_budget_alert_cooldowns = {}  # rule_id -> last_fired_timestamp
_AGENT_DOWN_SECONDS = 300  # 5 min with no OTLP data = agent down alert

# ── Heartbeat Gap Alerting ─────────────────────────────────────────────
_last_heartbeat_ts = 0  # timestamp of last detected heartbeat event
_heartbeat_interval_sec = 1800  # default 30 min, auto-detected from config
_heartbeat_silent_since = 0  # when silence was first detected (0 = not silent)


def _detect_heartbeat_interval():
    """Read heartbeat interval from OpenClaw config."""
    global _heartbeat_interval_sec
    for cf in [
        os.path.expanduser("~/.clawdbot/openclaw.json"),
        os.path.expanduser("~/.openclaw/openclaw.json"),
    ]:
        try:
            with open(cf) as f:
                cfg = json.load(f)
            hb = cfg.get("agents", {}).get("defaults", {}).get("heartbeat", {})
            every = hb.get("every", "")
            if every:
                import re as _re_hb

                m = _re_hb.match(
                    r"^(\d+)\s*(m|min|h|hr|s|sec)?$", str(every).strip().lower()
                )
                if m:
                    val = int(m.group(1))
                    unit = m.group(2) or "m"
                    if unit.startswith("h"):
                        _heartbeat_interval_sec = val * 3600
                    elif unit.startswith("s"):
                        _heartbeat_interval_sec = val
                    else:
                        _heartbeat_interval_sec = val * 60
                    return
        except Exception:
            continue


def _record_heartbeat():
    """Record that a heartbeat event was observed."""
    global _last_heartbeat_ts, _heartbeat_silent_since
    _last_heartbeat_ts = time.time()
    _heartbeat_silent_since = 0  # reset silence tracker


def _detect_sandbox_metadata():
    """Detect sandbox environment metadata. Returns dict or None."""
    sandbox = {}
    # Check environment variables (set by container wrappers like NemoClaw, Docker, etc.)
    name = os.environ.get("SANDBOX_NAME") or os.environ.get("CONTAINER_NAME")
    stype = os.environ.get("SANDBOX_TYPE") or os.environ.get("CONTAINER_TYPE")
    status = os.environ.get("SANDBOX_STATUS", "running")
    # Check if running inside Docker
    in_docker = os.path.exists("/.dockerenv")
    if not in_docker:
        try:
            with open("/proc/1/cgroup", "r") as f:
                in_docker = "docker" in f.read() or "containerd" in f.read()
        except Exception:
            pass
    # Check openclaw.json for sandbox config
    cfg = _load_gw_config()
    sandbox_cfg = cfg.get("sandbox", {}) if isinstance(cfg, dict) else {}
    if isinstance(sandbox_cfg, dict) and sandbox_cfg:
        name = name or sandbox_cfg.get("name")
        stype = stype or sandbox_cfg.get("type")
        status = sandbox_cfg.get("status", status)
    if name or stype or in_docker:
        sandbox["name"] = name or ("Docker Container" if in_docker else "Unknown")
        sandbox["type"] = stype or ("docker" if in_docker else "unknown")
        sandbox["status"] = status
        return sandbox
    return None


def _detect_inference_metadata():
    """Detect inference provider metadata. Returns dict or None."""
    provider = os.environ.get("INFERENCE_PROVIDER")
    model = os.environ.get("INFERENCE_MODEL")
    # Check openclaw.json
    cfg = _load_gw_config()
    if isinstance(cfg, dict):
        inf_cfg = cfg.get("inference", {})
        if isinstance(inf_cfg, dict) and inf_cfg:
            provider = provider or inf_cfg.get("provider")
            model = model or inf_cfg.get("model")
        # Also check default model from standard config
        if not model:
            model = cfg.get("model") or cfg.get("default_model")
        if not provider and model:
            # Infer provider from model name
            m = (model or "").lower()
            if "claude" in m or "anthropic" in m:
                provider = "Anthropic"
            elif "gpt" in m or "o1" in m or "o3" in m or "o4" in m:
                provider = "OpenAI"
            elif "gemini" in m:
                provider = "Google"
            elif "llama" in m or "mistral" in m or "mixtral" in m:
                provider = "Local/Ollama"
    if provider or model:
        return {"provider": provider, "model": model}
    return None


def _detect_security_metadata():
    """Detect security posture metadata. Returns dict or None."""
    security = {}
    cfg = _load_gw_config()
    if isinstance(cfg, dict):
        sec_cfg = cfg.get("security", {})
        if isinstance(sec_cfg, dict):
            if "sandbox_enabled" in sec_cfg:
                security["sandbox_enabled"] = sec_cfg["sandbox_enabled"]
            if "network_policy" in sec_cfg:
                security["network_policy"] = sec_cfg["network_policy"]
        # Check exec security mode
        exec_cfg = cfg.get("exec", {})
        if isinstance(exec_cfg, dict) and exec_cfg.get("security"):
            security["exec_security"] = exec_cfg["security"]
        # Check if auth is configured
        if cfg.get("auth") or cfg.get("token"):
            security["auth_enabled"] = True
        # Check bind address
        bind = cfg.get("bind") or cfg.get("host")
        if bind:
            security["bind_address"] = bind
            security["localhost_only"] = bind in ("127.0.0.1", "localhost", "::1")
    # Check Docker sandbox
    if os.path.exists("/.dockerenv"):
        security["sandbox_enabled"] = True
        security["sandbox_type"] = "docker"
    if security:
        return security
    return None


def _get_heartbeat_status():
    """Return heartbeat gap status for the API."""
    now = time.time()
    interval = _heartbeat_interval_sec
    threshold = interval * 1.5
    gap_sec = (now - _last_heartbeat_ts) if _last_heartbeat_ts > 0 else 0
    status = "unknown"
    if _last_heartbeat_ts == 0:
        status = "unknown"
    elif gap_sec <= interval:
        status = "ok"
    elif gap_sec <= threshold:
        status = "warning"
    else:
        status = "silent"
    return {
        "status": status,
        "last_heartbeat_ts": _last_heartbeat_ts,
        "gap_seconds": int(gap_sec) if _last_heartbeat_ts > 0 else None,
        "interval_seconds": interval,
        "threshold_seconds": int(threshold),
        "silent_since": _heartbeat_silent_since
        if _heartbeat_silent_since > 0
        else None,
    }


# ── OTLP Metrics Store ─────────────────────────────────────────────────
METRICS_FILE = None  # Set via CLI/env, defaults to {WORKSPACE}/.clawmetry-metrics.json
_metrics_lock = threading.Lock()
_otel_last_received = 0  # timestamp of last OTLP data received

metrics_store = {
    "tokens": [],  # [{timestamp, input, output, total, model, channel, provider}]
    "cost": [],  # [{timestamp, usd, model, channel, provider}]
    "runs": [],  # [{timestamp, duration_ms, model, channel}]
    "messages": [],  # [{timestamp, channel, outcome, duration_ms}]
    "webhooks": [],  # [{timestamp, channel, type}]
    "queues": [],  # [{timestamp, channel, depth}]
}
MAX_STORE_ENTRIES = 10_000
STORE_RETENTION_DAYS = 14


def _metrics_file_path():
    """Get the path to the metrics persistence file."""
    if METRICS_FILE:
        return METRICS_FILE
    if WORKSPACE:
        return os.path.join(WORKSPACE, ".clawmetry-metrics.json")
    return os.path.expanduser("~/.clawmetry-metrics.json")


def _load_metrics_from_disk():
    """Load persisted metrics on startup."""
    global metrics_store, _otel_last_received
    path = _metrics_file_path()
    if not os.path.exists(path):
        return
    try:
        with open(path, "r") as f:
            data = json.load(f)
        if isinstance(data, dict):
            for key in metrics_store:
                if key in data and isinstance(data[key], list):
                    metrics_store[key] = data[key][-MAX_STORE_ENTRIES:]
            _otel_last_received = data.get("_last_received", 0)
        _expire_old_entries()
    except json.JSONDecodeError as e:
        print(f"[warn]  Warning: Failed to parse metrics file {path}: {e}")
        # Create backup of corrupted file
        backup_path = f"{path}.corrupted.{int(time.time())}"
        try:
            os.rename(path, backup_path)
            print(f"💾 Corrupted file backed up to {backup_path}")
        except OSError:
            pass
    except (IOError, OSError) as e:
        print(f"[warn]  Warning: Failed to read metrics file {path}: {e}")
    except Exception as e:
        print(f"[warn]  Warning: Unexpected error loading metrics: {e}")


def _save_metrics_to_disk():
    """Persist metrics store to JSON file."""
    path = _metrics_file_path()
    try:
        d = os.path.dirname(path)
        if d:
            os.makedirs(d, exist_ok=True)
        data = {}
        with _metrics_lock:
            for k in metrics_store:
                data[k] = list(metrics_store[k])
        data["_last_received"] = _otel_last_received
        data["_saved_at"] = time.time()
        tmp = path + ".tmp"
        with open(tmp, "w") as f:
            json.dump(data, f)
        os.replace(tmp, path)
    except OSError as e:
        print(f"[warn]  Warning: Failed to save metrics to {path}: {e}")
        if "No space left on device" in str(e):
            print("💾 Disk full! Consider cleaning up old files or expanding storage.")
    except json.JSONEncodeError as e:
        print(f"[warn]  Warning: Failed to serialize metrics data: {e}")
    except Exception as e:
        print(f"[warn]  Warning: Unexpected error saving metrics: {e}")


def _expire_old_entries():
    """Remove entries older than STORE_RETENTION_DAYS."""
    cutoff = time.time() - (STORE_RETENTION_DAYS * 86400)
    with _metrics_lock:
        for key in metrics_store:
            metrics_store[key] = [
                e for e in metrics_store[key] if e.get("timestamp", 0) > cutoff
            ][-MAX_STORE_ENTRIES:]


def _add_metric(category, entry):
    """Add an entry to the metrics store (thread-safe)."""
    global _otel_last_received
    with _metrics_lock:
        metrics_store[category].append(entry)
        if len(metrics_store[category]) > MAX_STORE_ENTRIES:
            metrics_store[category] = metrics_store[category][-MAX_STORE_ENTRIES:]
        _otel_last_received = time.time()
    # Check budget on cost entries
    if category == "cost":
        try:
            _budget_check()
        except Exception:
            pass


def _metrics_flush_loop():
    """Background thread: save metrics to disk every 60 seconds."""
    while True:
        time.sleep(60)
        try:
            _expire_old_entries()
            _save_metrics_to_disk()
        except KeyboardInterrupt:
            print("📊 Metrics flush loop shutting down...")
            break
        except Exception as e:
            print(f"[warn]  Warning: Error in metrics flush loop: {e}")
            # Continue running despite errors


def _start_metrics_flush_thread():
    """Start the background metrics flush thread."""
    t = threading.Thread(target=_metrics_flush_loop, daemon=True)
    t.start()


def _has_otel_data():
    """Check if we have any OTLP metrics data."""
    return any(len(metrics_store[k]) > 0 for k in metrics_store)


# ── Multi-Node Fleet Database ───────────────────────────────────────────

_fleet_db_lock = threading.Lock()


def _fleet_db_path():
    """Get path to the fleet SQLite database.

    Always uses ~/.clawmetry/fleet.db, creating the directory if needed.
    The curl installer creates ~/.clawmetry/ but we must not rely on that --
    this function is the authoritative path and ensures the dir exists.

    Falls back to a workspace-relative path when WORKSPACE is set (dev mode).
    """
    if FLEET_DB_PATH:
        return FLEET_DB_PATH
    if WORKSPACE:
        return os.path.join(WORKSPACE, ".clawmetry-fleet.db")
    # Always use ~/.clawmetry/fleet.db -- create the dir if the installer
    # has not run yet or this is a fresh pip install without curl | bash.
    preferred_dir = os.path.expanduser("~/.clawmetry")
    try:
        os.makedirs(preferred_dir, exist_ok=True)
    except OSError:
        pass  # makedirs failed (permissions?), fall through to legacy path
    if os.path.isdir(preferred_dir):
        return os.path.join(preferred_dir, "fleet.db")
    # Last resort: legacy flat file in home dir (pre-installer environments)
    return os.path.expanduser("~/.clawmetry-fleet.db")


def _fleet_db():
    """Get a SQLite connection to the fleet database."""
    path = _fleet_db_path()
    # Ensure parent directory exists (defence-in-depth: guards against callers
    # that bypass _fleet_init_db, and older code paths that skipped makedirs).
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    db = _sqlite3.connect(path, timeout=10)
    db.row_factory = _sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    return db


def _fleet_init_db():
    """Initialize fleet database tables."""
    path = _fleet_db_path()
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    db = _fleet_db()
    db.executescript("""
        CREATE TABLE IF NOT EXISTS nodes (
            node_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            hostname TEXT,
            tags TEXT,
            api_key_hash TEXT,
            version TEXT,
            registered_at REAL,
            last_seen_at REAL,
            status TEXT DEFAULT 'unknown'
        );
        CREATE TABLE IF NOT EXISTS node_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            node_id TEXT NOT NULL,
            timestamp REAL NOT NULL,
            metrics_json TEXT NOT NULL,
            FOREIGN KEY (node_id) REFERENCES nodes(node_id)
        );
        CREATE INDEX IF NOT EXISTS idx_node_metrics_node_ts
            ON node_metrics(node_id, timestamp DESC);
    """)
    db.close()


def _fleet_check_key(req):
    """Validate fleet API key from request header. Returns True if valid."""
    if not FLEET_API_KEY:
        return True  # No key configured = open (for dev/testing)
    key = req.headers.get("X-Fleet-Key", "")
    return key == FLEET_API_KEY


def _fleet_update_statuses():
    """Update node statuses based on last_seen_at."""
    cutoff = time.time() - FLEET_NODE_TIMEOUT
    with _fleet_db_lock:
        db = _fleet_db()
        db.execute(
            "UPDATE nodes SET status = 'offline' WHERE last_seen_at < ? AND status != 'offline'",
            (cutoff,),
        )
        db.commit()
        db.close()


def _fleet_prune_metrics():
    """Remove metrics older than 7 days."""
    cutoff = time.time() - (7 * 86400)
    with _fleet_db_lock:
        db = _fleet_db()
        db.execute("DELETE FROM node_metrics WHERE timestamp < ?", (cutoff,))
        db.commit()
        db.close()


def _fleet_maintenance_loop():
    """Background thread: update statuses and prune old metrics."""
    while True:
        time.sleep(300)  # every 5 minutes
        try:
            _fleet_update_statuses()
            _fleet_prune_metrics()
        except Exception as e:
            print(f"Warning: Fleet maintenance error: {e}")


def _start_fleet_maintenance_thread():
    """Start the background fleet maintenance thread."""
    t = threading.Thread(target=_fleet_maintenance_loop, daemon=True)
    t.start()


# ── Budget & Alert Database ────────────────────────────────────────────


def _budget_init_db():
    """Initialize budget and alert tables in the fleet database."""
    db = _fleet_db()
    db.executescript("""
        CREATE TABLE IF NOT EXISTS budget_config (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS alert_rules (
            id TEXT PRIMARY KEY,
            type TEXT NOT NULL,
            threshold REAL NOT NULL,
            channels TEXT NOT NULL,
            cooldown_min INTEGER DEFAULT 30,
            enabled INTEGER DEFAULT 1,
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS alert_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rule_id TEXT,
            type TEXT NOT NULL,
            message TEXT NOT NULL,
            channel TEXT NOT NULL,
            fired_at REAL NOT NULL,
            acknowledged INTEGER DEFAULT 0,
            ack_at REAL,
            FOREIGN KEY (rule_id) REFERENCES alert_rules(id)
        );
        CREATE INDEX IF NOT EXISTS idx_alert_history_fired
            ON alert_history(fired_at DESC);
        CREATE INDEX IF NOT EXISTS idx_alert_history_rule
            ON alert_history(rule_id, fired_at DESC);
    """)
    db.close()


def _get_budget_config():
    """Get all budget config as a dict."""
    defaults = {
        "daily_limit": 0,
        "weekly_limit": 0,
        "monthly_limit": 0,
        "auto_pause_enabled": False,
        "auto_pause_threshold_pct": 100,
        "auto_pause_threshold_usd": 0,
        "auto_pause_action": "pause",
        "warning_threshold_pct": 80,
        "telegram_bot_token": "",
        "telegram_chat_id": "",
    }
    try:
        with _fleet_db_lock:
            db = _fleet_db()
            rows = db.execute("SELECT key, value FROM budget_config").fetchall()
            db.close()
        for row in rows:
            k = row["key"]
            v = row["value"]
            if k in defaults:
                if isinstance(defaults[k], bool):
                    defaults[k] = v.lower() in ("true", "1", "yes")
                elif isinstance(defaults[k], (int, float)):
                    try:
                        defaults[k] = float(v)
                    except ValueError:
                        pass
                else:
                    defaults[k] = v
    except Exception:
        pass
    return defaults


def _set_budget_config(updates):
    """Update budget config keys."""
    now = time.time()
    with _fleet_db_lock:
        db = _fleet_db()
        for k, v in updates.items():
            db.execute(
                "INSERT OR REPLACE INTO budget_config (key, value, updated_at) VALUES (?, ?, ?)",
                (k, str(v), now),
            )
        db.commit()
        db.close()


_SEVERITY_LEVELS = {"info": 0, "warning": 1, "critical": 2}
_SEVERITY_COLORS_SLACK = {"info": "#36a64f", "warning": "#f59e0b", "critical": "#ef4444"}
_SEVERITY_COLORS_DISCORD = {"info": 3581519, "warning": 16023040, "critical": 15680580}


def _default_alerts_webhook_config():
    return {
        "webhook_url": "",
        "slack_webhook_url": "",
        "discord_webhook_url": "",
        "cost_spike_alerts": True,
        "agent_error_rate_alerts": True,
        "security_posture_changes": True,
        "min_severity": "warning",
    }


def _load_alerts_webhook_config():
    cfg = _default_alerts_webhook_config()
    try:
        if os.path.exists(_ALERTS_CONFIG_FILE):
            with open(_ALERTS_CONFIG_FILE, "r") as f:
                data = json.load(f)
            if isinstance(data, dict):
                for k in cfg:
                    if k in data:
                        cfg[k] = data[k]
                if "min_severity" in data:
                    cfg["min_severity"] = data["min_severity"]
    except Exception:
        pass
    return cfg


def _save_alerts_webhook_config(updates):
    cfg = _load_alerts_webhook_config()
    allowed = {
        "webhook_url", "slack_webhook_url", "discord_webhook_url",
        "cost_spike_alerts", "agent_error_rate_alerts", "security_posture_changes",
        "min_severity",
    }
    for k in allowed:
        if k in updates:
            cfg[k] = updates[k]
    try:
        os.makedirs(os.path.dirname(_ALERTS_CONFIG_FILE), exist_ok=True)
        with open(_ALERTS_CONFIG_FILE, "w") as f:
            json.dump(cfg, f, indent=2)
    except Exception:
        pass
    return cfg


def _should_send_webhook_for_type(alert_type):
    cfg = _load_alerts_webhook_config()
    if alert_type in (
        "cost_spike",
        "daily_threshold_breached",
        "weekly_threshold_breached",
    ):
        return bool(cfg.get("cost_spike_alerts", True))
    if alert_type == "agent_error_rate":
        return bool(cfg.get("agent_error_rate_alerts", True))
    if alert_type == "security_posture_change":
        return bool(cfg.get("security_posture_changes", True))
    return True


def _severity_passes_filter(severity):
    """Return True if the given severity meets the configured minimum threshold."""
    cfg = _load_alerts_webhook_config()
    min_sev = str(cfg.get("min_severity", "warning")).lower()
    min_level = _SEVERITY_LEVELS.get(min_sev, 1)
    sev_level = _SEVERITY_LEVELS.get(str(severity).lower(), 1)
    return sev_level >= min_level


def _send_slack_alert(message, severity="warning", title="ClawMetry Alert"):
    """Send a Slack-formatted attachment alert using the configured Slack webhook URL."""
    cfg = _load_alerts_webhook_config()
    url = str(cfg.get("slack_webhook_url", "")).strip()
    if not url:
        return
    color = _SEVERITY_COLORS_SLACK.get(str(severity).lower(), "#f59e0b")
    payload = {
        "attachments": [
            {
                "color": color,
                "title": title,
                "text": message,
                "footer": "ClawMetry",
                "ts": int(time.time()),
                "fields": [
                    {"title": "Severity", "value": severity.upper(), "short": True},
                ],
            }
        ]
    }
    _send_webhook_alert(url, payload, payload_type="generic")


def _send_discord_alert(message, severity="warning", title="ClawMetry Alert"):
    """Send a Discord embed alert using the configured Discord webhook URL."""
    cfg = _load_alerts_webhook_config()
    url = str(cfg.get("discord_webhook_url", "")).strip()
    if not url:
        return
    color = _SEVERITY_COLORS_DISCORD.get(str(severity).lower(), 16023040)
    payload = {
        "embeds": [
            {
                "title": title,
                "description": message,
                "color": color,
                "fields": [
                    {"name": "Severity", "value": severity.upper(), "inline": True},
                ],
                "footer": {"text": "ClawMetry"},
                "timestamp": datetime.utcfromtimestamp(time.time()).strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                ),
            }
        ]
    }
    _send_webhook_alert(url, payload, payload_type="generic")


def _dispatch_alert(title, message, severity="warning", alert_type=None):
    """Dispatch an alert to all configured channels (Slack, Discord, generic webhook).

    Respects the global min_severity filter and per-type toggles.
    Called automatically from _fire_alert() so all alerts reach webhook channels.
    """
    if not _severity_passes_filter(severity):
        return
    if alert_type and not _should_send_webhook_for_type(alert_type):
        return
    cfg = _load_alerts_webhook_config()
    generic_url = str(cfg.get("webhook_url", "")).strip()
    slack_url = str(cfg.get("slack_webhook_url", "")).strip()
    discord_url = str(cfg.get("discord_webhook_url", "")).strip()

    if generic_url:
        payload = {
            "type": alert_type or "alert",
            "title": title,
            "message": message,
            "severity": severity,
            "timestamp": time.time(),
        }
        _send_webhook_alert(generic_url, payload, payload_type="generic")
    if slack_url:
        _send_slack_alert(message, severity=severity, title=title)
    if discord_url:
        _send_discord_alert(message, severity=severity, title=title)


def _dispatch_configured_webhooks(alert_type, payload):
    if not _should_send_webhook_for_type(alert_type):
        return
    cfg = _load_alerts_webhook_config()
    generic_url = str(cfg.get("webhook_url", "")).strip()
    slack_url = str(cfg.get("slack_webhook_url", "")).strip()
    discord_url = str(cfg.get("discord_webhook_url", "")).strip()
    if generic_url:
        _send_webhook_alert(generic_url, payload, payload_type="generic")
    if slack_url:
        _send_webhook_alert(slack_url, payload, payload_type="slack")
    if discord_url:
        _send_webhook_alert(discord_url, payload, payload_type="discord")


def _fire_alert(rule_id, alert_type, message, channels=None, severity="warning"):
    """Fire an alert with cooldown check and dispatch to configured webhook channels."""
    global _budget_alert_cooldowns
    now = time.time()

    # Check cooldown (default 30 min for budget alerts)
    cooldown_sec = 1800
    last_fired = _budget_alert_cooldowns.get(rule_id, 0)
    if now - last_fired < cooldown_sec:
        return

    _budget_alert_cooldowns[rule_id] = now

    # Save to alert history
    if channels is None:
        channels = ["banner"]
    try:
        with _fleet_db_lock:
            db = _fleet_db()
            for ch in channels:
                db.execute(
                    "INSERT INTO alert_history (rule_id, type, message, channel, fired_at) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (rule_id, alert_type, message, ch, now),
                )
            db.commit()
            db.close()
    except Exception as e:
        print(f"Warning: Failed to save alert history: {e}")

    # Send to explicit channels (telegram, banner, webhook)
    for ch in channels:
        if ch == "telegram":
            _send_telegram_alert(message)
        elif ch == "webhook":
            pass  # legacy: webhook dispatch now handled below via _dispatch_alert

    # Always dispatch to configured alert channels (Slack / Discord / generic webhook)
    _dispatch_alert(
        title=f"ClawMetry Alert [{alert_type}]",
        message=message,
        severity=severity,
        alert_type=alert_type,
    )


def _send_telegram_alert(message):
    """Send alert via direct Telegram API (preferred) or gateway fallback."""
    try:
        cfg = _get_budget_config()
        token = str(cfg.get("telegram_bot_token", "")).strip()
        chat_id = str(cfg.get("telegram_chat_id", "")).strip()
        if token and chat_id:
            import urllib.request

            url = f"https://api.telegram.org/bot{token}/sendMessage"
            payload = json.dumps(
                {
                    "chat_id": chat_id,
                    "text": f"[ClawMetry Alert] {message}",
                    "parse_mode": "Markdown",
                }
            ).encode()
            req = urllib.request.Request(
                url,
                data=payload,
                headers={"Content-Type": "application/json"},
            )
            urllib.request.urlopen(req, timeout=10)
            return
    except Exception as e:
        print(f"Warning: Direct Telegram alert failed: {e}")
    try:
        _gw_invoke(
            "message",
            {
                "action": "send",
                "message": f"[ClawMetry Alert] {message}",
            },
        )
    except Exception:
        pass


def _send_webhook_alert(url, alert_data, payload_type="generic"):
    """Send alert to a webhook URL (generic JSON, Slack attachment, or Discord embed)."""
    try:
        import urllib.request as _ur

        if payload_type == "discord":
            message_text = (
                alert_data.get("message")
                or "[{t}] cost=${c} threshold=${th}".format(
                    t=alert_data.get("type", "alert"),
                    c=alert_data.get("cost_usd", 0),
                    th=alert_data.get("threshold", 0),
                )
            )
            severity = str(alert_data.get("severity", "warning")).lower()
            color = _SEVERITY_COLORS_DISCORD.get(severity, 16023040)
            body = {
                "embeds": [
                    {
                        "title": alert_data.get("title", "ClawMetry Alert"),
                        "description": message_text,
                        "color": color,
                        "fields": [
                            {"name": "Severity", "value": severity.upper(), "inline": True},
                            {"name": "Type", "value": str(alert_data.get("type", "alert")), "inline": True},
                        ],
                        "footer": {"text": "ClawMetry"},
                        "timestamp": datetime.utcfromtimestamp(time.time()).strftime(
                            "%Y-%m-%dT%H:%M:%SZ"
                        ),
                    }
                ]
            }
        elif payload_type == "slack":
            message_text = (
                alert_data.get("message")
                or "[{t}] cost=${c} threshold=${th}".format(
                    t=alert_data.get("type", "alert"),
                    c=alert_data.get("cost_usd", 0),
                    th=alert_data.get("threshold", 0),
                )
            )
            severity = str(alert_data.get("severity", "warning")).lower()
            color = _SEVERITY_COLORS_SLACK.get(severity, "#f59e0b")
            body = {
                "attachments": [
                    {
                        "color": color,
                        "title": alert_data.get("title", "ClawMetry Alert"),
                        "text": message_text,
                        "footer": "ClawMetry",
                        "ts": int(time.time()),
                        "fields": [
                            {"title": "Severity", "value": severity.upper(), "short": True},
                            {"title": "Type", "value": str(alert_data.get("type", "alert")), "short": True},
                        ],
                    }
                ]
            }
        else:
            body = alert_data
        data = json.dumps(body).encode()
        req = _ur.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        _ur.urlopen(req, timeout=10)
    except Exception:
        pass

def _get_alert_rules():
    """Get all alert rules."""
    try:
        with _fleet_db_lock:
            db = _fleet_db()
            rows = db.execute(
                "SELECT * FROM alert_rules ORDER BY created_at DESC"
            ).fetchall()
            db.close()
        return [dict(r) for r in rows]
    except Exception:
        return []


def _get_alert_history(limit=50):
    """Get recent alert history."""
    try:
        with _fleet_db_lock:
            db = _fleet_db()
            rows = db.execute(
                "SELECT * FROM alert_history ORDER BY fired_at DESC LIMIT ?", (limit,)
            ).fetchall()
            db.close()
        return [dict(r) for r in rows]
    except Exception:
        return []


def _get_active_alerts():
    """Get unacknowledged alerts from last 24h."""
    cutoff = time.time() - 86400
    try:
        with _fleet_db_lock:
            db = _fleet_db()
            rows = db.execute(
                "SELECT * FROM alert_history WHERE acknowledged = 0 AND fired_at > ? "
                "ORDER BY fired_at DESC LIMIT 20",
                (cutoff,),
            ).fetchall()
            db.close()
        return [dict(r) for r in rows]
    except Exception:
        return []


def _budget_monitor_loop():
    """Background thread: check for anomalies, agent-down, and custom alert rules."""
    global \
        _budget_alert_cooldowns, \
        _security_posture_hash, \
        _budget_paused, \
        _budget_paused_at, \
        _budget_paused_reason
    while True:
        time.sleep(60)
        try:
            now = time.time()

            # Agent-down check
            if (
                _otel_last_received > 0
                and (now - _otel_last_received) > _AGENT_DOWN_SECONDS
            ):
                _fire_alert(
                    rule_id="agent_down",
                    alert_type="agent_down",
                    message=f"Agent appears down: no OTLP data for {int((now - _otel_last_received) / 60)} minutes",
                    channels=["banner", "telegram"],
                )

            # Heartbeat gap check
            if _last_heartbeat_ts > 0:
                hb_gap = now - _last_heartbeat_ts
                hb_threshold = _heartbeat_interval_sec * 1.5
                if hb_gap > hb_threshold:
                    if _heartbeat_silent_since == 0:
                        globals()["_heartbeat_silent_since"] = now
                    gap_min = int(hb_gap / 60)
                    _fire_alert(
                        rule_id="heartbeat_gap",
                        alert_type="heartbeat_silent",
                        message=f"Agent heartbeat silent for {gap_min} minutes (expected every {int(_heartbeat_interval_sec / 60)}m)",
                        channels=["banner", "telegram"],
                    )

            # Anomaly check: today's cost > 2x 7-day average
            status = _get_budget_status()
            daily_spent = status["daily_spent"]
            if daily_spent > 0:
                week_avg = (
                    status["weekly_spent"] / 7 if status["weekly_spent"] > 0 else 0
                )
                if week_avg > 0 and daily_spent > week_avg * 2:
                    ratio = daily_spent / week_avg
                    _fire_alert(
                        rule_id="anomaly_daily",
                        alert_type="anomaly",
                        message=f"Spending anomaly: today ${daily_spent:.2f} is {ratio:.1f}x the 7-day average (${week_avg:.2f}/day)",
                        channels=["banner", "telegram"],
                    )
                    _dispatch_configured_webhooks(
                        "cost_spike",
                        {
                            "type": "cost_spike",
                            "agent": "main",
                            "cost_usd": round(daily_spent, 4),
                            "threshold": round(week_avg * 2, 4),
                            "timestamp": now,
                            "message": f"Cost spike detected: {ratio:.1f}x daily average",
                        },
                    )

            # Token velocity alert (GH#313): detect runaway agent loops
            try:
                vel = _compute_velocity_status()
                if vel["active"]:
                    reasons_str = "; ".join(vel["reasons"])
                    sid_hint = (
                        f" (session: {vel['triggeringSession'][:12]}...)"
                        if vel.get("triggeringSession")
                        else ""
                    )
                    msg = f"\u26a1 Runaway loop detected{sid_hint}: {reasons_str}"
                    _fire_alert(
                        rule_id="token_velocity",
                        alert_type="token_velocity",
                        message=msg,
                        channels=["banner", "telegram"],
                    )
            except Exception as _vel_err:
                print(f"Warning: velocity check failed: {_vel_err}")

            # Agent error-rate check from webhook channel metrics (last 60 minutes)
            window_start = now - 3600
            total_wh = 0
            error_wh = 0
            with _metrics_lock:
                for e in metrics_store.get("webhooks", []):
                    ts = e.get("timestamp", 0)
                    if ts < window_start:
                        continue
                    total_wh += 1
                    et = str(e.get("type", "")).lower()
                    if et.endswith(".error") or "error" in et:
                        error_wh += 1
            if total_wh >= 10:
                error_rate = (error_wh / total_wh) * 100.0
                if error_rate >= 20.0:
                    rule_id = "agent_error_rate_high"
                    last_fired = _budget_alert_cooldowns.get(rule_id, 0)
                    if now - last_fired >= 1800:
                        _budget_alert_cooldowns[rule_id] = now
                        msg = f"Agent error rate high: {error_rate:.1f}% ({error_wh}/{total_wh}) in the last hour"
                        _fire_alert(
                            rule_id=rule_id,
                            alert_type="agent_error_rate",
                            message=msg,
                            channels=["banner", "telegram"],
                        )
                        _dispatch_configured_webhooks(
                            "agent_error_rate",
                            {
                                "type": "agent_error_rate",
                                "agent": "main",
                                "cost_usd": round(status.get("daily_spent", 0), 4),
                                "threshold": 20.0,
                                "timestamp": now,
                                "message": msg,
                            },
                        )

            # Security posture change check
            posture = _detect_security_metadata() or {}
            posture_hash = json.dumps(posture, sort_keys=True)
            if not _security_posture_hash:
                _security_posture_hash = posture_hash
            elif posture_hash != _security_posture_hash:
                _security_posture_hash = posture_hash
                msg = "Security posture changed (sandbox/auth/network settings updated)"
                _fire_alert(
                    rule_id="security_posture_change",
                    alert_type="security",
                    message=msg,
                    channels=["banner", "telegram"],
                )
                _dispatch_configured_webhooks(
                    "security_posture_change",
                    {
                        "type": "security_posture_change",
                        "agent": "main",
                        "cost_usd": round(status.get("daily_spent", 0), 4),
                        "threshold": 0,
                        "timestamp": now,
                        "message": msg,
                    },
                )

            # Daily threshold auto-pause/alert (absolute USD)
            cfg = _get_budget_config()
            auto_thr = float(cfg.get("auto_pause_threshold_usd", 0) or 0)
            auto_action = str(cfg.get("auto_pause_action", "pause") or "pause").lower()
            if auto_thr > 0 and status.get("daily_spent", 0) >= auto_thr:
                if auto_action == "pause" and not _budget_paused:
                    _budget_paused = True
                    _budget_paused_at = now
                    _budget_paused_reason = f"Auto-pause threshold exceeded: ${status['daily_spent']:.2f} / ${auto_thr:.2f}"
                    _fire_alert(
                        rule_id="auto_pause_daily_usd",
                        alert_type="threshold",
                        message=f"AUTO-PAUSE: daily spend ${status['daily_spent']:.2f} exceeded ${auto_thr:.2f}",
                        channels=["banner", "telegram"],
                    )
                    _dispatch_configured_webhooks(
                        "daily_threshold_breached",
                        {
                            "type": "daily_threshold_breached",
                            "agent": "main",
                            "cost_usd": round(status.get("daily_spent", 0), 4),
                            "threshold": round(auto_thr, 4),
                            "timestamp": now,
                            "message": _budget_paused_reason,
                        },
                    )
                    _pause_gateway()
                elif auto_action == "alert":
                    rule_id = "auto_pause_daily_alert_only"
                    last_fired = _budget_alert_cooldowns.get(rule_id, 0)
                    if now - last_fired >= 1800:
                        _budget_alert_cooldowns[rule_id] = now
                        msg = f"Daily spend alert threshold exceeded: ${status['daily_spent']:.2f} / ${auto_thr:.2f}"
                        _fire_alert(
                            rule_id=rule_id,
                            alert_type="threshold",
                            message=msg,
                            channels=["banner", "telegram"],
                        )
                        _dispatch_configured_webhooks(
                            "daily_threshold_breached",
                            {
                                "type": "daily_threshold_breached",
                                "agent": "main",
                                "cost_usd": round(status.get("daily_spent", 0), 4),
                                "threshold": round(auto_thr, 4),
                                "timestamp": now,
                                "message": msg,
                            },
                        )

            # Custom alert rules
            rules = _get_alert_rules()
            for rule in rules:
                if not rule.get("enabled"):
                    continue
                rule_id = rule["id"]
                rtype = rule["type"]
                threshold = rule["threshold"]
                channels = json.loads(rule.get("channels", '["banner"]'))
                cooldown = rule.get("cooldown_min", 30) * 60

                last_fired = _budget_alert_cooldowns.get(rule_id, 0)
                if now - last_fired < cooldown:
                    continue

                fired = False
                msg = ""

                if rtype == "threshold":
                    if status["daily_spent"] >= threshold:
                        msg = f"Daily spending ${status['daily_spent']:.2f} exceeded threshold ${threshold:.2f}"
                        fired = True
                elif rtype == "spike":
                    # Spike: cost in last hour > threshold x average hourly rate
                    hour_ago = now - 3600
                    hour_cost = 0
                    with _metrics_lock:
                        for e in metrics_store["cost"]:
                            if e.get("timestamp", 0) >= hour_ago:
                                hour_cost += e.get("usd", 0)
                    avg_hourly = status["daily_spent"] / max(
                        1,
                        (
                            now
                            - datetime.now()
                            .replace(hour=0, minute=0, second=0, microsecond=0)
                            .timestamp()
                        )
                        / 3600,
                    )
                    if avg_hourly > 0 and hour_cost > avg_hourly * threshold:
                        msg = f"Spending spike: ${hour_cost:.2f} in last hour ({(hour_cost / avg_hourly):.1f}x average)"
                        fired = True

                if fired:
                    _budget_alert_cooldowns[rule_id] = now
                    try:
                        with _fleet_db_lock:
                            db = _fleet_db()
                            for ch in channels:
                                db.execute(
                                    "INSERT INTO alert_history (rule_id, type, message, channel, fired_at) "
                                    "VALUES (?, ?, ?, ?, ?)",
                                    (rule_id, rtype, msg, ch, now),
                                )
                            db.commit()
                            db.close()
                    except Exception:
                        pass
                    for ch in channels:
                        if ch == "telegram":
                            _send_telegram_alert(msg)
                        elif ch == "webhook":
                            webhook_url = rule.get("webhook_url", "")
                            if webhook_url:
                                _send_webhook_alert(
                                    webhook_url,
                                    {"type": rtype, "message": msg, "timestamp": now},
                                )

        except Exception as e:
            print(f"Warning: Budget monitor error: {e}")


def _start_budget_monitor_thread():
    """Start the background budget monitor thread."""
    t = threading.Thread(target=_budget_monitor_loop, daemon=True)
    t.start()


# ── OTLP Protobuf Helpers ──────────────────────────────────────────────


def _otel_attr_value(val):
    """Convert an OTel AnyValue to a Python value."""
    if val.HasField("string_value"):
        return val.string_value
    if val.HasField("int_value"):
        return val.int_value
    if val.HasField("double_value"):
        return val.double_value
    if val.HasField("bool_value"):
        return val.bool_value
    return str(val)


def _get_data_points(metric):
    """Extract data points from a metric regardless of type."""
    if metric.HasField("sum"):
        return metric.sum.data_points
    elif metric.HasField("gauge"):
        return metric.gauge.data_points
    elif metric.HasField("histogram"):
        return metric.histogram.data_points
    elif metric.HasField("summary"):
        return metric.summary.data_points
    return []


def _get_dp_value(dp):
    """Extract the numeric value from a data point."""
    if hasattr(dp, "as_double") and dp.as_double:
        return dp.as_double
    if hasattr(dp, "as_int") and dp.as_int:
        return dp.as_int
    if hasattr(dp, "sum") and dp.sum:
        return dp.sum
    if hasattr(dp, "count") and dp.count:
        return dp.count
    return 0


def _get_dp_attrs(dp):
    """Extract attributes from a data point."""
    attrs = {}
    for attr in dp.attributes:
        attrs[attr.key] = _otel_attr_value(attr.value)
    return attrs


def _process_otlp_metrics(pb_data):
    """Decode OTLP metrics protobuf and store relevant data."""
    req = metrics_service_pb2.ExportMetricsServiceRequest()
    req.ParseFromString(pb_data)

    for resource_metrics in req.resource_metrics:
        resource_attrs = {}
        if resource_metrics.resource:
            for attr in resource_metrics.resource.attributes:
                resource_attrs[attr.key] = _otel_attr_value(attr.value)

        for scope_metrics in resource_metrics.scope_metrics:
            for metric in scope_metrics.metrics:
                name = metric.name
                ts = time.time()

                if name == "openclaw.tokens":
                    for dp in _get_data_points(metric):
                        attrs = _get_dp_attrs(dp)
                        _add_metric(
                            "tokens",
                            {
                                "timestamp": ts,
                                "input": attrs.get("input_tokens", 0),
                                "output": attrs.get("output_tokens", 0),
                                "total": _get_dp_value(dp),
                                "model": attrs.get(
                                    "model", resource_attrs.get("model", "")
                                ),
                                "channel": attrs.get(
                                    "channel", resource_attrs.get("channel", "")
                                ),
                                "provider": attrs.get(
                                    "provider", resource_attrs.get("provider", "")
                                ),
                            },
                        )
                elif name == "openclaw.cost.usd":
                    for dp in _get_data_points(metric):
                        attrs = _get_dp_attrs(dp)
                        _add_metric(
                            "cost",
                            {
                                "timestamp": ts,
                                "usd": _get_dp_value(dp),
                                "model": attrs.get(
                                    "model", resource_attrs.get("model", "")
                                ),
                                "channel": attrs.get(
                                    "channel", resource_attrs.get("channel", "")
                                ),
                                "provider": attrs.get(
                                    "provider", resource_attrs.get("provider", "")
                                ),
                            },
                        )
                elif name == "openclaw.run.duration_ms":
                    for dp in _get_data_points(metric):
                        attrs = _get_dp_attrs(dp)
                        _add_metric(
                            "runs",
                            {
                                "timestamp": ts,
                                "duration_ms": _get_dp_value(dp),
                                "model": attrs.get(
                                    "model", resource_attrs.get("model", "")
                                ),
                                "channel": attrs.get(
                                    "channel", resource_attrs.get("channel", "")
                                ),
                            },
                        )
                elif name == "openclaw.context.tokens":
                    for dp in _get_data_points(metric):
                        attrs = _get_dp_attrs(dp)
                        _add_metric(
                            "tokens",
                            {
                                "timestamp": ts,
                                "input": _get_dp_value(dp),
                                "output": 0,
                                "total": _get_dp_value(dp),
                                "model": attrs.get(
                                    "model", resource_attrs.get("model", "")
                                ),
                                "channel": attrs.get(
                                    "channel", resource_attrs.get("channel", "")
                                ),
                                "provider": attrs.get(
                                    "provider", resource_attrs.get("provider", "")
                                ),
                            },
                        )
                elif name in (
                    "openclaw.message.processed",
                    "openclaw.message.queued",
                    "openclaw.message.duration_ms",
                ):
                    for dp in _get_data_points(metric):
                        attrs = _get_dp_attrs(dp)
                        outcome = (
                            "processed"
                            if "processed" in name
                            else ("queued" if "queued" in name else "duration")
                        )
                        _add_metric(
                            "messages",
                            {
                                "timestamp": ts,
                                "channel": attrs.get(
                                    "channel", resource_attrs.get("channel", "")
                                ),
                                "outcome": outcome,
                                "duration_ms": _get_dp_value(dp)
                                if "duration" in name
                                else 0,
                            },
                        )
                elif name in (
                    "openclaw.webhook.received",
                    "openclaw.webhook.error",
                    "openclaw.webhook.duration_ms",
                ):
                    for dp in _get_data_points(metric):
                        attrs = _get_dp_attrs(dp)
                        wtype = (
                            "received"
                            if "received" in name
                            else ("error" if "error" in name else "duration")
                        )
                        _add_metric(
                            "webhooks",
                            {
                                "timestamp": ts,
                                "channel": attrs.get(
                                    "channel", resource_attrs.get("channel", "")
                                ),
                                "type": wtype,
                            },
                        )


def _process_otlp_traces(pb_data):
    """Decode OTLP traces protobuf and extract relevant span data."""
    req = trace_service_pb2.ExportTraceServiceRequest()
    req.ParseFromString(pb_data)

    for resource_spans in req.resource_spans:
        resource_attrs = {}
        if resource_spans.resource:
            for attr in resource_spans.resource.attributes:
                resource_attrs[attr.key] = _otel_attr_value(attr.value)

        for scope_spans in resource_spans.scope_spans:
            for span in scope_spans.spans:
                attrs = {}
                for attr in span.attributes:
                    attrs[attr.key] = _otel_attr_value(attr.value)

                ts = time.time()
                duration_ns = span.end_time_unix_nano - span.start_time_unix_nano
                duration_ms = duration_ns / 1_000_000

                span_name = span.name.lower()
                if "run" in span_name or "completion" in span_name:
                    _add_metric(
                        "runs",
                        {
                            "timestamp": ts,
                            "duration_ms": duration_ms,
                            "model": attrs.get(
                                "model", resource_attrs.get("model", "")
                            ),
                            "channel": attrs.get(
                                "channel", resource_attrs.get("channel", "")
                            ),
                        },
                    )
                elif "message" in span_name:
                    _add_metric(
                        "messages",
                        {
                            "timestamp": ts,
                            "channel": attrs.get(
                                "channel", resource_attrs.get("channel", "")
                            ),
                            "outcome": "processed",
                            "duration_ms": duration_ms,
                        },
                    )


def _get_otel_usage_data():
    """Aggregate OTLP metrics into usage data for the Usage tab."""
    today = datetime.now()
    today_start = today.replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
    week_start = (
        (today - timedelta(days=today.weekday()))
        .replace(hour=0, minute=0, second=0, microsecond=0)
        .timestamp()
    )
    month_start = today.replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    ).timestamp()

    daily_tokens = {}
    daily_cost = {}
    model_usage = {}

    with _metrics_lock:
        for entry in metrics_store["tokens"]:
            ts = entry.get("timestamp", 0)
            day = datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
            total = entry.get("total", 0)
            daily_tokens[day] = daily_tokens.get(day, 0) + total
            model = entry.get("model", "unknown") or "unknown"
            model_usage[model] = model_usage.get(model, 0) + total

        for entry in metrics_store["cost"]:
            ts = entry.get("timestamp", 0)
            day = datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
            daily_cost[day] = daily_cost.get(day, 0) + entry.get("usd", 0)

    days = []
    for i in range(13, -1, -1):
        d = today - timedelta(days=i)
        ds = d.strftime("%Y-%m-%d")
        days.append(
            {
                "date": ds,
                "tokens": daily_tokens.get(ds, 0),
                "cost": daily_cost.get(ds, 0),
            }
        )

    today_str = today.strftime("%Y-%m-%d")
    today_tok = daily_tokens.get(today_str, 0)
    week_tok = sum(v for k, v in daily_tokens.items() if _safe_date_ts(k) >= week_start)
    month_tok = sum(
        v for k, v in daily_tokens.items() if _safe_date_ts(k) >= month_start
    )
    today_cost_val = daily_cost.get(today_str, 0)
    week_cost_val = sum(
        v for k, v in daily_cost.items() if _safe_date_ts(k) >= week_start
    )
    month_cost_val = sum(
        v for k, v in daily_cost.items() if _safe_date_ts(k) >= month_start
    )

    run_durations = []
    with _metrics_lock:
        for entry in metrics_store["runs"]:
            run_durations.append(entry.get("duration_ms", 0))
    avg_run_ms = sum(run_durations) / len(run_durations) if run_durations else 0

    msg_count = len(metrics_store["messages"])

    # Enhanced cost tracking for OTLP data
    trend_data = _analyze_usage_trends(daily_tokens)
    model_billing, billing_summary = _build_model_billing(model_usage)
    warnings = _generate_cost_warnings(
        today_cost_val,
        week_cost_val,
        month_cost_val,
        trend_data,
        month_tok,
        billing_summary,
    )

    return {
        "source": "otlp",
        "days": days,
        "today": today_tok,
        "week": week_tok,
        "month": month_tok,
        "todayCost": round(today_cost_val, 4),
        "weekCost": round(week_cost_val, 4),
        "monthCost": round(month_cost_val, 4),
        "avgRunMs": round(avg_run_ms, 1),
        "messageCount": msg_count,
        "modelBreakdown": [
            {"model": k, "tokens": v}
            for k, v in sorted(model_usage.items(), key=lambda x: -x[1])
        ],
        "modelBilling": model_billing,
        "billingSummary": billing_summary,
        "trend": trend_data,
        "warnings": warnings,
    }


def _safe_date_ts(date_str):
    """Parse a YYYY-MM-DD date string to a timestamp, returning 0 on failure."""
    if not date_str or not isinstance(date_str, str):
        return 0
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").timestamp()
    except ValueError:
        # Invalid date format - expected but handled gracefully
        return 0
    except Exception as e:
        print(f"[warn]  Warning: Unexpected error parsing date '{date_str}': {e}")
        return 0


def validate_configuration():
    """Validate the detected configuration and provide helpful feedback for new users."""
    warnings = []
    tips = []
    
    # Check if workspace looks like a real OpenClaw setup
    workspace_files = ['SOUL.md', 'AGENTS.md', 'MEMORY.md', 'memory']
    found_files = []
    for f in workspace_files:
        path = os.path.join(WORKSPACE, f)
        if os.path.exists(path):
            found_files.append(f)
    
    if not found_files:
        warnings.append(f"[warn]  No OpenClaw workspace files found in {WORKSPACE}")
        tips.append("[tip] Create SOUL.md, AGENTS.md, or MEMORY.md to set up your agent workspace")
    
    # Check if log directory exists and has recent logs
    if not os.path.exists(LOG_DIR):
        warnings.append(f"[warn]  Log directory doesn't exist: {LOG_DIR}")
        tips.append("[tip] Make sure OpenClaw/Moltbot is running to generate logs")
    else:
        # Check for recent log files
        log_pattern = os.path.join(LOG_DIR, "*claw*.log")
        recent_logs = [f for f in glob.glob(log_pattern) 
                      if os.path.getmtime(f) > time.time() - 86400]  # Last 24h
        if not recent_logs:
            warnings.append(f"[warn]  No recent log files found in {LOG_DIR}")
            tips.append("[tip] Start your OpenClaw agent to see real-time data")
    
    # Check if sessions directory exists
    if not SESSIONS_DIR or not os.path.exists(SESSIONS_DIR):
        warnings.append(f"[warn]  Sessions directory not found: {SESSIONS_DIR}")
        tips.append("[tip] Sessions will appear when your agent starts conversations")
    
    # Check if OpenClaw binary is available
    try:
        subprocess.run(['openclaw', '--version'], capture_output=True, timeout=10)
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
        warnings.append("[warn]  OpenClaw binary not found in PATH")
        tips.append("[tip] Install OpenClaw: https://github.com/openclaw/openclaw")
    
    return warnings, tips


def _auto_detect_data_dir():
    """Auto-detect OpenClaw data directory, including Docker volume mounts."""
    # Standard locations
    candidates = [
        os.path.expanduser('~/.openclaw'),
        os.path.expanduser('~/.clawdbot'),
    ]
    # Docker volume mounts (Hostinger pattern: /docker/*/data/.openclaw)
    try:
        import glob as _glob
        for pattern in ['/docker/*/data/.openclaw', '/docker/*/.openclaw',
                        '/var/lib/docker/volumes/*/_data/.openclaw']:
            candidates.extend(_glob.glob(pattern))
    except Exception:
        pass
    # Check Docker inspect for mount points
    try:
        import subprocess as _sp
        container_ids = _sp.check_output(
            ['docker', 'ps', '-q', '--filter', 'ancestor=*openclaw*'],
            timeout=3, stderr=_sp.DEVNULL
        ).decode().strip().split()
        if not container_ids:
            # Try all containers
            container_ids = _sp.check_output(
                ['docker', 'ps', '-q'], timeout=3, stderr=_sp.DEVNULL
            ).decode().strip().split()
        for cid in container_ids[:3]:
            try:
                mounts = _sp.check_output(
                    ['docker', 'inspect', cid, '--format',
                     '{{range .Mounts}}{{.Source}}:{{.Destination}} {{end}}'],
                    timeout=3, stderr=_sp.DEVNULL
                ).decode().strip().split()
                for mount in mounts:
                    parts = mount.split(':')
                    if len(parts) >= 1:
                        src = parts[0]
                        oc_path = os.path.join(src, '.openclaw')
                        if os.path.isdir(oc_path) and oc_path not in candidates:
                            candidates.insert(0, oc_path)
                        # Also check if the mount itself is the .openclaw dir
                        if src.endswith('.openclaw') and os.path.isdir(src):
                            candidates.insert(0, src)
            except Exception:
                pass
    except Exception:
        pass
    for c in candidates:
        if c and os.path.isdir(c) and (
            os.path.isdir(os.path.join(c, 'agents')) or
            os.path.isdir(os.path.join(c, 'workspace')) or
            os.path.exists(os.path.join(c, 'cron', 'jobs.json'))
        ):
            return c
    return None

def detect_config(args=None):
    """Auto-detect OpenClaw/Moltbot paths, with CLI and env overrides."""
    global WORKSPACE, MEMORY_DIR, LOG_DIR, SESSIONS_DIR, USER_NAME

    # 0a. --openclaw-dir: set OpenClaw config directory (Issue #322 - Docker config bleed)
    if args and getattr(args, 'openclaw_dir', None):
        os.environ['CLAWMETRY_OPENCLAW_DIR'] = os.path.expanduser(args.openclaw_dir)

    # 0. --data-dir: set defaults from OpenClaw data directory (e.g. /path/.openclaw)
    data_dir = None
    if args and getattr(args, 'data_dir', None):
        data_dir = os.path.expanduser(args.data_dir)
    elif os.environ.get("OPENCLAW_DATA_DIR"):
        data_dir = os.path.expanduser(os.environ["OPENCLAW_DATA_DIR"])
    else:
        # Auto-detect: check common locations including Docker volumes
        data_dir = _auto_detect_data_dir()
    
    if data_dir and os.path.isdir(data_dir):
        # Auto-set workspace, sessions, crons from data dir
        ws = os.path.join(data_dir, 'workspace')
        if os.path.isdir(ws) and not (args and args.workspace):
            if not args:
                import argparse; args = argparse.Namespace()
            args.workspace = ws
        sess = os.path.join(data_dir, 'agents', 'main', 'sessions')
        if os.path.isdir(sess) and not (args and getattr(args, 'sessions_dir', None)):
            args.sessions_dir = sess

    # 1. Workspace - where agent files live (SOUL.md, MEMORY.md, memory/, etc.)
    if args and args.workspace:
        WORKSPACE = os.path.expanduser(args.workspace)
    elif os.environ.get("OPENCLAW_HOME"):
        WORKSPACE = os.path.expanduser(os.environ["OPENCLAW_HOME"])
    elif os.environ.get("OPENCLAW_WORKSPACE"):
        WORKSPACE = os.path.expanduser(os.environ["OPENCLAW_WORKSPACE"])
    else:
        # Auto-detect: check common locations
        candidates = [
            _detect_workspace_from_config(),
            os.path.expanduser("~/.openclaw/workspace"),
            os.path.expanduser("~/.clawdbot/workspace"),
            os.path.expanduser("~/clawd"),
            os.path.expanduser("~/openclaw"),
            os.getcwd(),
        ]
        for c in candidates:
            if c and os.path.isdir(c) and (
                os.path.exists(os.path.join(c, "SOUL.md")) or
                os.path.exists(os.path.join(c, "AGENTS.md")) or
                os.path.exists(os.path.join(c, "MEMORY.md")) or
                os.path.isdir(os.path.join(c, "memory"))
            ):
                WORKSPACE = c
                break
        if not WORKSPACE:
            WORKSPACE = os.getcwd()

    MEMORY_DIR = os.path.join(WORKSPACE, "memory")

    # 2. Log directory
    if args and args.log_dir:
        LOG_DIR = os.path.expanduser(args.log_dir)
    elif os.environ.get("OPENCLAW_LOG_DIR"):
        LOG_DIR = os.path.expanduser(os.environ["OPENCLAW_LOG_DIR"])
    else:
        candidates = _get_log_dirs() + [os.path.expanduser("~/.clawdbot/logs")]
        LOG_DIR = next((d for d in candidates if os.path.isdir(d)), _get_log_dirs()[0])

    # 3. Sessions directory (transcript .jsonl files)
    if args and getattr(args, 'sessions_dir', None):
        SESSIONS_DIR = os.path.expanduser(args.sessions_dir)
    elif os.environ.get("OPENCLAW_SESSIONS_DIR"):
        SESSIONS_DIR = os.path.expanduser(os.environ["OPENCLAW_SESSIONS_DIR"])
    else:
        candidates = [
            os.path.expanduser('~/.openclaw/agents/main/sessions'),
            os.path.expanduser('~/.clawdbot/agents/main/sessions'),
            os.path.join(WORKSPACE, 'sessions') if WORKSPACE else None,
            os.path.expanduser('~/.openclaw/sessions'),
            os.path.expanduser('~/.clawdbot/sessions'),
        ]
        # Also scan agents dirs
        for agents_base in [os.path.expanduser('~/.openclaw/agents'), os.path.expanduser('~/.clawdbot/agents')]:
            if os.path.isdir(agents_base):
                for agent in os.listdir(agents_base):
                    p = os.path.join(agents_base, agent, 'sessions')
                    if p not in candidates:
                        candidates.append(p)
        SESSIONS_DIR = next((d for d in candidates if d and os.path.isdir(d)), candidates[0] if candidates else None)

    # 4. User name (shown in Flow visualization)
    if args and args.name:
        USER_NAME = args.name
    elif os.environ.get("OPENCLAW_USER"):
        USER_NAME = os.environ["OPENCLAW_USER"]
    else:
        USER_NAME = "You"

    # ── Register blueprints (Phase 4) ───────────────────────────────────────
    app.register_blueprint(bp_advisor)
    app.register_blueprint(bp_selfevolve)
    app.register_blueprint(bp_alerts)
    app.register_blueprint(bp_autonomy)
    app.register_blueprint(bp_auth)
    app.register_blueprint(bp_brain)
    app.register_blueprint(bp_budget)
    app.register_blueprint(bp_channels)
    app.register_blueprint(bp_components)
    app.register_blueprint(bp_config)
    app.register_blueprint(bp_crons)
    app.register_blueprint(bp_fleet)
    app.register_blueprint(bp_gateway)
    app.register_blueprint(bp_health)
    app.register_blueprint(bp_history)
    app.register_blueprint(bp_logs)
    app.register_blueprint(bp_memory)
    app.register_blueprint(bp_otel)
    app.register_blueprint(bp_overview)
    app.register_blueprint(bp_security)
    app.register_blueprint(bp_sessions)
    app.register_blueprint(bp_usage)
    app.register_blueprint(bp_version)
    app.register_blueprint(bp_version_impact)
    app.register_blueprint(bp_clusters)
    app.register_blueprint(bp_nemoclaw)
    app.register_blueprint(bp_skills)
    app.register_blueprint(bp_heartbeat)
    app.register_blueprint(bp_selfconfig)
    app.register_blueprint(bp_openapi)

    # Local-OSS shims for cloud-only endpoints. Return empty arrays so the
    # Approvals tab renders cleanly without cloud sync.
    _oss_note = ("OSS install — connect to ClawMetry Cloud "
                 "(`clawmetry connect`) to enable cloud-mediated approvals.")
    @app.route("/api/cloud/approvals", endpoint="oss_approvals_shim")
    def _oss_approvals_shim():
        from flask import jsonify as _jsonify
        return _jsonify({"approvals": [], "count": 0, "note": _oss_note})

    @app.route("/api/cloud/policies", endpoint="oss_policies_shim",
               methods=["GET", "POST"])
    def _oss_policies_shim():
        from flask import jsonify as _jsonify, request as _req
        if _req.method == "POST":
            return _jsonify({"error": "Connect to ClawMetry Cloud to save "
                             "policies from the UI.", "note": _oss_note}), 402
        return _jsonify({"policies": [], "count": 0, "note": _oss_note})

    @app.route("/api/cloud/integrations", endpoint="oss_integrations_shim",
               methods=["GET", "POST"])
    def _oss_integrations_shim():
        from flask import jsonify as _jsonify, request as _req
        if _req.method == "POST":
            return _jsonify({"error": "Connect to ClawMetry Cloud to save "
                             "integrations.", "note": _oss_note}), 402
        return _jsonify({"integrations": [], "count": 0, "note": _oss_note})
    # ────────────────────────────────────────────────────────────────────────



def _detect_workspace_from_config():
    """Try to read workspace from Moltbot/OpenClaw agent config."""
    config_paths = [
        os.path.expanduser("~/.clawdbot/agents/main/config.json"),
        os.path.expanduser("~/.clawdbot/config.json"),
    ]
    for cp in config_paths:
        try:
            with open(cp) as f:
                data = json.load(f)
                ws = data.get("workspace") or data.get("workspaceDir")
                if ws:
                    return os.path.expanduser(ws)
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            pass
    return None


def _detect_gateway_port():
    """Detect the OpenClaw gateway port from config files or environment."""
    # Check environment variable first
    env_port = os.environ.get('OPENCLAW_GATEWAY_PORT', '').strip()
    if env_port:
        try:
            return int(env_port)
        except ValueError:
            pass
    # Try reading from gateway config
    # Try JSON configs first (openclaw.json / moltbot.json / clawdbot.json)
    _oc_dir = _get_openclaw_dir()
    json_paths = [
        os.path.join(_oc_dir, 'openclaw.json'),
        os.path.join(_oc_dir, 'moltbot.json'),
        os.path.join(_oc_dir, 'clawdbot.json'),
        os.path.expanduser('~/.clawdbot/clawdbot.json'),
    ]
    for jp in json_paths:
        try:
            import json as _json
            with open(jp) as f:
                cfg = _json.load(f)
            gw = cfg.get('gateway', {})
            if isinstance(gw, dict) and 'port' in gw:
                return int(gw['port'])
        except (FileNotFoundError, ValueError, KeyError, TypeError):
            pass
    # Try YAML configs
    yaml_paths = [
        os.path.expanduser('~/.openclaw/gateway.yaml'),
        os.path.expanduser('~/.openclaw/gateway.yml'),
        os.path.expanduser('~/.clawdbot/gateway.yaml'),
        os.path.expanduser('~/.clawdbot/gateway.yml'),
    ]
    for cp in yaml_paths:
        try:
            with open(cp) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('port:'):
                        port_val = line.split(':', 1)[1].strip()
                        return int(port_val)
        except (FileNotFoundError, ValueError, IndexError):
            pass
    return 18789  # Default OpenClaw gateway port


def _detect_gateway_token():
    """Detect the OpenClaw gateway auth token from env, config files, or running process."""
    # 1. Environment variable (most reliable - matches running gateway)
    env_token = os.environ.get('OPENCLAW_GATEWAY_TOKEN', '').strip()
    if env_token:
        return env_token
    # 2. Try reading from running gateway process env (Linux only)
    try:
        import subprocess as _sp
        result = _sp.run(['pgrep', '-f', 'openclaw-gatewa'], capture_output=True, text=True, timeout=3)
        for pid in result.stdout.strip().split('\n'):
            pid = pid.strip()
            if pid:
                try:
                    with open(f'/proc/{pid}/environ', 'r') as f:
                        env_data = f.read()
                    for entry in env_data.split('\0'):
                        if entry.startswith('OPENCLAW_GATEWAY_TOKEN='):
                            return entry.split('=', 1)[1]
                except (PermissionError, FileNotFoundError):
                    pass
    except Exception:
        pass
    # 3. Config files
    _oc_dir = _get_openclaw_dir()
    json_paths = [
        os.path.join(_oc_dir, 'openclaw.json'),
        os.path.join(_oc_dir, 'moltbot.json'),
        os.path.join(_oc_dir, 'clawdbot.json'),
        os.path.expanduser('~/.clawdbot/clawdbot.json'),
    ]
    for jp in json_paths:
        try:
            import json as _json
            with open(jp) as f:
                cfg = _json.load(f)
            gw = cfg.get('gateway', {})
            auth = gw.get('auth', {})
            if isinstance(auth, dict) and 'token' in auth:
                return auth['token']
        except (FileNotFoundError, ValueError, KeyError, TypeError):
            pass
    return None


def _detect_disk_mounts():
    """Detect mounted filesystems to monitor (root + any large data drives)."""
    mounts = ['/']
    try:
        with open('/proc/mounts') as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 2:
                    mount_point = parts[1]
                    fs_type = parts[2] if len(parts) > 2 else ''
                    # Include additional data mounts (skip virtual/special filesystems)
                    if (mount_point.startswith('/mnt/') or mount_point.startswith('/data')) and \
                       fs_type not in ('tmpfs', 'devtmpfs', 'proc', 'sysfs', 'cgroup', 'cgroup2'):
                        mounts.append(mount_point)
    except (IOError, OSError):
        pass
    return mounts


def get_public_ip():
    """Get the machine's public IP address (useful for cloud/VPS users)."""
    try:
        import urllib.request
        return urllib.request.urlopen("https://api.ipify.org", timeout=2).read().decode().strip()
    except Exception:
        return None


def get_local_ip():
    """Get the machine's LAN IP address."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.2)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except (socket.error, OSError) as e:
        # Network unavailable or socket error - common in offline/restricted environments
        return "127.0.0.1"
    except Exception as e:
        print(f"[warn]  Warning: Unexpected error getting local IP: {e}")
        return "127.0.0.1"


# ── HTML Template ───────────────────────────────────────────────────────

DASHBOARD_HTML = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ClawMetry</title>
<link rel="icon" href="/favicon.ico" type="image/x-icon">
<link rel="icon" href="/static/img/logo.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{{ url_for('static', filename='css/dashboard.css') }}">
<script src="{{ url_for('static', filename='js/nav-dropdown.js') }}"></script>
<script src="{{ url_for('static', filename='js/alerts.js') }}" defer></script>
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chartjs-adapter-date-fns@3.0.0/dist/chartjs-adapter-date-fns.bundle.min.js"></script>
</head>
<body data-theme="dark" class="booting">
{% include 'partials/overlays.html' %}
<div class="zoom-wrapper" id="zoom-wrapper">
<div class="nav">
  <h1><a href="https://clawmetry.com" style="display:flex;align-items:center;gap:7px;text-decoration:none;color:inherit"><img src="/static/img/logo.svg" width="22" height="22" style="border-radius:4px;vertical-align:middle;flex-shrink:0" alt="ClawMetry"><span><span style="color:#ffffff">Claw</span><span style="color:#E5443A">Metry</span></span></a></h1>
  <span id="version-badge" class="version-badge" title="ClawMetry version">v{{ version }}</span>
  <div class="theme-toggle" onclick="var o=document.getElementById('gw-setup-overlay');o.dataset.mandatory='false';document.getElementById('gw-setup-close').style.display='';o.style.display='flex'" title="Gateway settings" style="cursor:pointer;"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg></div>
  <!-- Budget & Alerts hidden until mature -->
  <!-- <div class="theme-toggle" onclick="openBudgetModal()" title="Budget & Alerts" style="cursor:pointer;">&#128176;</div> -->

  <div class="theme-toggle" id="logout-btn" onclick="clawmetryLogout()" title="Logout" style="display:none;cursor:pointer;"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg></div>
  <div class="zoom-controls">
    <button class="zoom-btn" onclick="zoomOut()" title="Zoom out (Ctrl/Cmd + -)">−</button>
    <span class="zoom-level" id="zoom-level" title="Current zoom level. Ctrl/Cmd + 0 to reset">100%</span>
    <button class="zoom-btn" onclick="zoomIn()" title="Zoom in (Ctrl/Cmd + +)">+</button>
  </div>
  <div class="nav-tabs">
    <div class="nav-tab" onclick="switchTab('flow')">Flow</div>
    <div class="nav-tab" onclick="switchTab('brain')">Brain</div>
    <div class="nav-tab active" onclick="switchTab('overview')">Overview</div>
    <div class="nav-tab" onclick="switchTab('approvals')" title="Cloud-mediated approval queue">Approvals <span id="nav-approvals-badge" style="display:none;background:#ef4444;color:#fff;border-radius:10px;padding:1px 6px;font-size:10px;font-weight:700;margin-left:4px;">0</span></div>
    <div class="nav-tab" onclick="switchTab('alerts')" title="Get notified when something goes wrong (Pro)">Alerts <span class="pro-chip">Pro</span></div>
    <div class="nav-tab" onclick="switchTab('notifications')" title="Slack / Email / PagerDuty / Telegram channels">Notifications</div>
    <div class="nav-tab" onclick="switchTab('context')" title="See what context the LLM receives each turn">Context</div>
    <div class="nav-tab" onclick="switchTab('usage')">Tokens</div>
    <div class="nav-tab" id="crons-tab" onclick="switchTab('crons')" style="display:none;">Crons</div>
    <div class="nav-tab" onclick="switchTab('memory')">Memory</div>
    <div class="nav-tab" onclick="switchTab('security')">Security</div>
    <div class="nav-tab" id="nemoclaw-tab" onclick="switchTab('nemoclaw')" style="display:none;">NemoClaw</div>
    <!-- History tab hidden until mature -->
    <!-- <div class="nav-tab" onclick="switchTab('history')">History</div> -->
  <div id="cloud-cta-btn" onclick="openCloudModal()" style="display:none;margin-left:8px;cursor:pointer;padding:6px 12px;border:1px solid rgba(96,165,250,0.5);border-radius:8px;font-size:12px;font-weight:600;color:#60a5fa;white-space:nowrap;transition:all 0.2s;user-select:none;" onmouseover="this.style.background='rgba(96,165,250,0.1)'" onmouseout="this.style.background='transparent'"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="display:inline;vertical-align:middle;margin-right:4px"><polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>Enable Cloud Sync</div>
  <div id="cloud-connected-badge" onclick="window.open('https://app.clawmetry.com','_blank')" style="display:none;margin-left:8px;cursor:pointer;padding:6px 12px;border:1px solid rgba(34,197,94,0.4);border-radius:8px;font-size:12px;font-weight:600;color:#22c55e;white-space:nowrap;transition:all 0.2s;user-select:none;" onmouseover="this.style.background='rgba(34,197,94,0.08)'" onmouseout="this.style.background='transparent'">&#9679; Cloud Connected</div>
  </div>
</div>
{% include 'partials/cloud-modal.html' %}


{% include 'partials/banners.html' %}

{% include 'partials/budget-modal.html' %}

<!-- OVERVIEW (Split-Screen Hacker Dashboard) -->
{% include 'tabs/overview.html' %}

<!-- ALERTS (Cloud-Pro feature) -->
{% include 'tabs/alerts.html' %}

<!-- USAGE -->
{% include 'tabs/usage.html' %}

<!-- CRONS -->
{% include 'tabs/crons.html' %}

<!-- MEMORY -->
{% include 'tabs/memory.html' %}

<!-- TRANSCRIPTS -->
{% include 'tabs/transcripts.html' %}


<!-- UPGRADE IMPACT -->
{% include 'tabs/version-impact.html' %}

<!-- SESSION CLUSTERS -->
{% include 'tabs/clusters.html' %}

<!-- HISTORY -->

<!-- RATE LIMITS -->
{% include 'tabs/limits.html' %}

{% include 'tabs/history.html' %}

<!-- FLOW -->
{% include 'tabs/flow.html' %}

<!-- BRAIN -->
{% include 'tabs/brain.html' %}

<!-- SELF-EVOLVE -->
{% include 'tabs/selfevolve.html' %}

<!-- NOTIFICATIONS -->
{% include 'tabs/notifications.html' %}

<!-- CONTEXT INSPECTOR -->
{% include 'tabs/context.html' %}

<!-- SECURITY -->
{% include 'tabs/security.html' %}

<!-- APPROVALS — cloud-mediated approval queue (#667) -->
{% include 'tabs/approvals.html' %}

<!-- MODEL ATTRIBUTION (theme 2) -->
{% include 'tabs/models.html' %}

<!-- NEMOCLAW GOVERNANCE -->
{% include 'tabs/nemoclaw.html' %}

<!-- SUB-AGENT TREE (theme 2) -->
{% include 'tabs/subagents.html' %}

<!-- SKILLS FIDELITY (#687) -->
{% include 'tabs/skills.html' %}

{% include 'tabs/logs.html' %}

<script src="{{ url_for('static', filename='js/app.js') }}"></script>
</div> <!-- end zoom-wrapper -->

<!-- Component Detail Modal -->
<div class="comp-modal-overlay" id="comp-modal-overlay" onclick="if(event.target===this)closeCompModal()">
  <div class="comp-modal-card">
    <div class="comp-modal-header">
      <div class="comp-modal-title" id="comp-modal-title">Component</div>
      <div style="display: flex; align-items: center; gap: 10px;">
        <div class="time-travel-toggle" id="time-travel-toggle" onclick="toggleTimeTravelMode()" title="Enable time travel">🕰️</div>
        <div class="comp-modal-close" onclick="closeCompModal()">&times;</div>
      </div>
    </div>
    <div class="time-travel-bar" id="time-travel-bar">
      <div class="time-travel-controls">
        <div class="time-nav-btn" onclick="timeTravel('prev-day')" title="Previous day">‹</div>
        <div class="time-scrubber">
          <div class="time-slider" id="time-slider" onclick="onTimeSliderClick(event)">
            <div class="time-slider-thumb" id="time-slider-thumb"></div>
          </div>
          <div class="time-display" id="time-display">Loading...</div>
        </div>
        <div class="time-nav-btn" onclick="timeTravel('next-day')" title="Next day">›</div>
        <div class="time-nav-btn" onclick="timeTravel('now')" title="Back to now">⏹</div>
      </div>
    </div>
    <div class="comp-modal-body" id="comp-modal-body">Loading...</div>
    <div class="comp-modal-footer" id="comp-modal-footer">Last updated: --</div>
  </div>
</div>

<!-- Task Detail Modal -->
<div class="modal-overlay" id="task-modal-overlay" onclick="if(event.target===this)closeTaskModal()">
  <div class="modal-card">
    <div class="modal-header">
      <div class="modal-header-left">
        <div class="modal-title" id="modal-title">Task Name</div>
        <div class="modal-session-key" id="modal-session-key">session-id</div>
      </div>
      <div class="modal-header-right">
        <label class="modal-auto-refresh"><input type="checkbox" id="modal-auto-refresh-cb" checked onchange="toggleModalAutoRefresh()"> Auto-refresh</label>
        <div class="modal-close" onclick="closeTaskModal()">&times;</div>
      </div>
    </div>
    <div class="modal-tabs">
      <div class="modal-tab active" onclick="switchModalTab('summary')">Summary</div>
      <div class="modal-tab" onclick="switchModalTab('narrative')">Narrative</div>
      <div class="modal-tab" onclick="switchModalTab('full')">Full Logs</div>
    </div>
    <div class="modal-content" id="modal-content">Loading...</div>
    <div class="modal-footer">
      <span id="modal-event-count">--</span>
      <span id="modal-msg-count">--</span>
    </div>
  </div>
</div>

<!-- Gateway Setup Wizard -->
<div id="gw-setup-overlay" data-mandatory="false" onclick="if(event.target===this && this.dataset.mandatory!=='true'){this.style.display='none'}" style="display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.85); z-index:10000; align-items:center; justify-content:center; font-family:Manrope,sans-serif;">
  <div style="background:var(--bg-secondary, #1a1a2e); border:1px solid var(--border-primary, #333); border-radius:16px; padding:40px; max-width:440px; width:90%; text-align:center; box-shadow:0 20px 60px rgba(0,0,0,0.5); position:relative;">
    <button id="gw-setup-close" onclick="document.getElementById('gw-setup-overlay').style.display='none'" style="display:none; position:absolute; top:12px; right:16px; background:none; border:none; color:var(--text-muted, #888); font-size:22px; cursor:pointer; padding:4px 8px; line-height:1;">✕</button>
    <img src="/static/img/logo.svg" style="width:64px;height:64px;margin-bottom:16px;display:block;margin-left:auto;margin-right:auto;" alt="ClawMetry">
    <h2 style="color:var(--text-primary, #fff); margin:0 0 8px; font-size:24px; font-weight:700;">ClawMetry Setup</h2>
    <p style="color:var(--text-muted, #888); margin:0 0 24px; font-size:14px;">Enter your OpenClaw gateway token to connect.</p>
    <input id="gw-token-input" type="password" placeholder="Paste your gateway token" 
      style="width:100%; padding:12px 16px; border:1px solid var(--border-primary, #444); border-radius:8px; background:var(--bg-primary, #111); color:var(--text-primary, #fff); font-size:14px; font-family:monospace; box-sizing:border-box; outline:none; margin-bottom:8px;"
      onkeydown="if(event.key==='Enter')gwSetupConnect()">
    <p id="gw-setup-hint" style="color:var(--text-muted, #888); font-size:12px; margin:0 0 4px; text-align:left;">Find it: <code style="color:var(--text-accent, #0af); background:rgba(0,170,255,0.1); padding:2px 6px; border-radius:4px;">docker exec $(docker ps -q) env | grep TOKEN</code> or <code style="color:var(--text-accent, #0af); background:rgba(0,170,255,0.1); padding:2px 6px; border-radius:4px;">gateway.auth.token</code></p>
    <p id="gw-url-hint" style="color:var(--text-muted, #666); font-size:11px; margin:0 0 16px; text-align:left;">Optional: <input id="gw-url-input" type="text" placeholder="http://localhost:18789 (auto-detected)" style="width:70%; padding:4px 8px; border:1px solid var(--border-primary, #444); border-radius:4px; background:var(--bg-primary, #111); color:var(--text-primary, #fff); font-size:11px; font-family:monospace;"></p>
    <div id="gw-setup-error" style="color:#ff4444; font-size:13px; margin-bottom:12px; display:none;"></div>
    <div id="gw-setup-status" style="color:var(--text-accent, #0af); font-size:13px; margin-bottom:12px; display:none;"></div>
    <button onclick="gwSetupConnect()" id="gw-connect-btn"
      style="width:100%; padding:12px; border:none; border-radius:8px; background:var(--bg-accent, #0f6fff); color:#fff; font-size:15px; font-weight:600; cursor:pointer; font-family:Manrope,sans-serif;">
      Connect
    </button>
    <p style="color:var(--text-faint, #555); font-size:11px; margin:16px 0 0;">Token is stored locally on this ClawMetry instance.</p>
  </div>
</div>

<script src="{{ url_for('static', filename='js/gw-setup.js') }}"></script>

</body>
</html>
"""


# ── API Routes ──────────────────────────────────────────────────────────


# _acquire_stream_slot / _release_stream_slot moved to helpers/streams.py (re-exported above)


# ── Gateway API proxy (WebSocket JSON-RPC + HTTP fallback) ──────────────
import urllib.request as _urllib_req
import uuid as _uuid

_GW_CONFIG_FILE = os.path.expanduser("~/.clawmetry-gateway.json")


def _get_openclaw_dir():
    """Return the OpenClaw config directory, respecting CLAWMETRY_OPENCLAW_DIR env var and --openclaw-dir CLI flag."""
    return os.environ.get("CLAWMETRY_OPENCLAW_DIR", os.path.expanduser("~/.openclaw"))


# _ws_client / _ws_lock / _ws_connected moved to helpers/gateway.py (re-exported above)
# _gw_ws_connect / _gw_ws_rpc moved to helpers/gateway.py


def _load_gw_config():
    """Load gateway config from globals, env, or file.

    Token resolution order (Issue #321 - avoid stale cached tokens):
      1. Environment variable (OPENCLAW_GATEWAY_TOKEN)
      2. Live OpenClaw config (openclaw.json -> gateway.auth.token)
      3. Running gateway process /proc env
      4. CLI/env globals already set
      5. Cached ~/.clawmetry-gateway.json (backward compat fallback)
    """
    global GATEWAY_URL, GATEWAY_TOKEN
    # 1. Auto-detect from live OpenClaw config (most authoritative - reads directly)
    token = _detect_gateway_token()
    port = _detect_gateway_port()
    if token:
        GATEWAY_TOKEN = token
        if not GATEWAY_URL:
            GATEWAY_URL = f"http://127.0.0.1:{port}"
        # Update cache file with fresh token (backward compat, not used for reads)
        try:
            cache = {}
            try:
                with open(_GW_CONFIG_FILE) as f:
                    cache = json.load(f)
            except Exception:
                pass
            cache["token"] = token
            cache["url"] = GATEWAY_URL or f"http://127.0.0.1:{port}"
            with open(_GW_CONFIG_FILE, "w") as f:
                json.dump(cache, f)
            os.chmod(_GW_CONFIG_FILE, 0o600)
        except Exception:
            pass
        return {"url": GATEWAY_URL, "token": GATEWAY_TOKEN}
    # 2. Already set via CLI/env
    if GATEWAY_URL and GATEWAY_TOKEN:
        return {"url": GATEWAY_URL, "token": GATEWAY_TOKEN}
    # 3. Fallback to cache file (only if live config unavailable)
    try:
        with open(_GW_CONFIG_FILE) as f:
            cfg = json.load(f)
            GATEWAY_URL = cfg.get("url", GATEWAY_URL)
            GATEWAY_TOKEN = cfg.get("token", GATEWAY_TOKEN)
            return cfg
    except Exception:
        pass
    return {}


# _gw_invoke / _gw_invoke_docker moved to helpers/gateway.py (re-exported above)


# ── Flask Blueprints (Phase 4) ────────────────────────────────────────────────
from flask import Blueprint as _Blueprint
# bp_alerts moved to routes/alerts.py
# bp_auth moved to routes/meta.py
# bp_brain moved to routes/brain.py
# bp_budget moved to routes/alerts.py
# bp_channels moved to routes/channels.py
# bp_components moved to routes/components.py
# bp_config moved to routes/infra.py
# bp_crons moved to routes/crons.py
# bp_fleet moved to routes/fleet_history.py
# bp_gateway moved to routes/meta.py
# bp_health moved to routes/health.py
# bp_history moved to routes/fleet_history.py
# bp_logs moved to routes/infra.py
# bp_memory moved to routes/infra.py
# bp_otel moved to routes/meta.py
# bp_overview moved to routes/overview.py
# bp_sessions moved to routes/sessions.py
# bp_security moved to routes/infra.py
# bp_usage moved to routes/usage.py
# bp_version moved to routes/meta.py
# bp_version_impact moved to routes/meta.py
# bp_clusters moved to routes/meta.py
# bp_nemoclaw moved to routes/nemoclaw.py
# ─────────────────────────────────────────────────────────────────────────────

# ── NemoClaw Governance ───────────────────────────────────────────────────────
_nemoclaw_policy_hash = None  # Module-level: tracks last-seen policy hash for drift detection
_nemoclaw_drift_info = {}     # Stores drift metadata (old hash, new hash, timestamp)


def _detect_nemoclaw():
    """Returns dict with nemoclaw info, or None if not installed."""
    import shutil as _shutil
    from pathlib import Path as _Path
    if not _shutil.which("nemoclaw"):
        return None
    home = _Path.home()
    result = {"installed": True}
    # Load config
    cfg_path = home / ".nemoclaw" / "config.json"
    if cfg_path.exists():
        try:
            result["config"] = json.loads(cfg_path.read_text())
        except Exception:
            pass
    # Load state
    state_path = home / ".nemoclaw" / "state" / "nemoclaw.json"
    if state_path.exists():
        try:
            result["state"] = json.loads(state_path.read_text())
        except Exception:
            pass
    # Load policy
    policy_path = home / ".nemoclaw" / "source" / "nemoclaw-blueprint" / "policies" / "openclaw-sandbox.yaml"
    if policy_path.exists():
        try:
            result["policy_yaml"] = policy_path.read_text()
            result["policy_hash"] = __import__("hashlib").sha256(policy_path.read_bytes()).hexdigest()[:12]
        except Exception:
            pass
    # Load presets
    presets_dir = home / ".nemoclaw" / "source" / "nemoclaw-blueprint" / "policies" / "presets"
    if presets_dir.exists():
        try:
            result["presets"] = [p.stem for p in presets_dir.glob("*.yaml")]
        except Exception:
            pass
    # Get sandbox list
    try:
        import subprocess as _sp
        r = _sp.run(["nemoclaw", "list"], capture_output=True, text=True, timeout=5)
        result["sandbox_list_raw"] = r.stdout
    except Exception:
        pass
    return result


def _parse_network_policies(yaml_text):
    """Parse network_policies section from openclaw-sandbox.yaml.
    Returns list of {name, hosts} dicts without requiring PyYAML."""
    policies = []
    try:
        import yaml as _yaml
        data = _yaml.safe_load(yaml_text)
        if isinstance(data, dict):
            net = data.get("network_policies") or data.get("networkPolicies") or {}
            if isinstance(net, dict):
                for name, hosts in net.items():
                    if isinstance(hosts, list):
                        policies.append({"name": name, "hosts": hosts})
                    elif isinstance(hosts, str):
                        policies.append({"name": name, "hosts": [hosts]})
        return policies
    except ImportError:
        pass
    # Fallback: simple line-based parser for network_policies block
    in_block = False
    current_name = None
    current_hosts = []
    for line in yaml_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("network_policies:"):
            in_block = True
            continue
        if in_block:
            if not line.startswith(" ") and not line.startswith("\t") and stripped and not stripped.startswith("#"):
                if current_name:
                    policies.append({"name": current_name, "hosts": current_hosts})
                in_block = False
                break
            if stripped.endswith(":") and not stripped.startswith("-"):
                if current_name:
                    policies.append({"name": current_name, "hosts": current_hosts})
                current_name = stripped[:-1]
                current_hosts = []
            elif stripped.startswith("- ") and current_name:
                current_hosts.append(stripped[2:].strip())
            elif current_name and ":" in stripped and not stripped.startswith("-"):
                # key: value host format
                parts = stripped.split(":", 1)
                if len(parts) == 2:
                    current_hosts.append(stripped.strip())
    if current_name:
        policies.append({"name": current_name, "hosts": current_hosts})
    return policies

# (bp_nemoclaw handlers moved to routes/nemoclaw.py: /api/nemoclaw/governance,
#  /api/nemoclaw/governance/acknowledge-drift)


# ── Version check & self-update routes ────────────────────────────────────────
# State for /api/version PyPI lookup cache, used by routes/meta.py.
_pypi_cache = {"ts": 0, "version": None}


# (bp_version handlers moved to routes/meta.py: /api/version, /api/update)


# ──────────────────────────────────────────────────────────────────────────────


# (bp_gateway handlers moved to routes/meta.py: /api/gw/config,
#  /api/gw/invoke, /api/gw/rpc)


def _auto_discover_gateway(token):
    """Scan common ports to find an OpenClaw gateway."""
    common_ports = [18789, 56089]
    # Also check env and config files
    env_port = os.environ.get("OPENCLAW_GATEWAY_PORT")
    if env_port:
        try:
            common_ports.insert(0, int(env_port))
        except ValueError:
            pass
    # Add ports from config files
    for cfg_name in ["moltbot.json", "clawdbot.json", "openclaw.json"]:
        for base in [
            os.path.expanduser("~/.openclaw"),
            os.path.expanduser("~/.clawdbot"),
        ]:
            try:
                with open(os.path.join(base, cfg_name)) as f:
                    c = json.load(f)
                    p = c.get("gateway", {}).get("port")
                    if p and p not in common_ports:
                        common_ports.insert(0, int(p))
            except Exception:
                pass
    # Scan for additional ports
    for port_offset in range(0, 100):
        p = 18700 + port_offset
        if p not in common_ports:
            common_ports.append(p)

    for port in common_ports[:20]:  # Cap at 20 ports to scan
        # Try WebSocket first, then HTTP
        url = f"http://127.0.0.1:{port}"
        ws_url = f"ws://127.0.0.1:{port}"
        try:
            import websocket

            ws = websocket.create_connection(f"{ws_url}/", timeout=2)
            ws.recv()  # challenge
            connect_msg = {
                "type": "req",
                "id": "discover",
                "method": "connect",
                "params": {
                    "minProtocol": 3,
                    "maxProtocol": 3,
                    "client": {
                        "id": "cli",
                        "version": __version__,
                        "platform": _CURRENT_PLATFORM,
                        "mode": "cli",
                        "instanceId": "clawmetry-discover",
                    },
                    "role": "operator",
                    "scopes": ["operator.admin"],
                    "auth": {"token": token},
                },
            }
            ws.send(json.dumps(connect_msg))
            for _ in range(5):
                r = json.loads(ws.recv())
                if r.get("type") == "res" and r.get("id") == "discover":
                    ws.close()
                    if r.get("ok"):
                        return url
                    break
            try:
                ws.close()
            except Exception:
                pass
        except Exception:
            pass
        # HTTP fallback
        try:
            payload = json.dumps({"tool": "session_status", "args": {}}).encode()
            req = _urllib_req.Request(
                f"{url}/tools/invoke",
                data=payload,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            with _urllib_req.urlopen(req, timeout=2) as resp:
                result = json.loads(resp.read())
                if result.get("ok"):
                    return url
        except Exception:
            continue

    # Last resort: try docker exec
    try:
        result = _gw_invoke_docker("session_status", {}, token)
        if result:
            return "docker://localhost:18789"  # sentinel value indicating docker mode
    except Exception:
        pass
    return None


# (bp_auth handlers moved to routes/meta.py: /api/auth/check, /auth, /)


@app.before_request
def _check_auth():
    """Require valid gateway token for all /api/* routes when GATEWAY_TOKEN is set."""
    if request.path == "/api/auth/check":
        return  # Auth check endpoint is always accessible
    if request.path == "/api/gw/config":
        return  # Gateway setup must work before auth is configured
    if request.path.startswith("/api/nodes"):
        return  # Fleet API uses its own X-Fleet-Key authentication
    if not request.path.startswith("/api/"):
        return  # HTML, static, etc. are fine
    # Trust localhost — the dashboard is a local tool; auth protects remote access only
    remote = request.remote_addr or ""
    if remote in ("127.0.0.1", "::1", "localhost"):
        return
    if not GATEWAY_TOKEN:
        return jsonify(
            {
                "error": "Gateway token not configured. Please set up your gateway token first.",
                "needsSetup": True,
            }
        ), 401
    token = request.headers.get("Authorization", "").replace("Bearer ", "").strip()
    if not token:
        token = request.args.get("token", "").strip()
    if token == GATEWAY_TOKEN:
        return
    return jsonify({"error": "Unauthorized", "authRequired": True}), 401


# (moved to routes/overview.py)


# (moved to routes/overview.py)


# (moved to routes/overview.py)


# (moved to routes/sessions.py)


# (moved to routes/sessions.py)


# (moved to routes/sessions.py)


# (moved to routes/sessions.py)


# (moved to routes/sessions.py)


# (moved to routes/sessions.py)


# (moved to routes/sessions.py)


# (moved to routes/sessions.py)


# (moved to routes/sessions.py)


# (moved to routes/sessions.py)


# (8 route handlers moved to routes/crons.py: /api/crons, /api/cron/fix,
#  /api/cron/run, /api/cron/toggle, /api/cron/delete, /api/cron/update,
#  /api/cron/create, /api/cron/<job_id>/runs)


def _enrich_cron_runs(job_id, runs):
    """Add p50/p95 duration and cost stats to a list of cron run records."""
    if not runs:
        return {"jobId": job_id, "runs": [], "stats": {}}

    durations = sorted([r.get("durationMs", 0) for r in runs if r.get("durationMs")])
    costs = [
        r.get("costUsd", 0.0) or r.get("cost_usd", 0.0)
        for r in runs
        if (r.get("costUsd") or r.get("cost_usd"))
    ]
    ok_count = sum(1 for r in runs if r.get("status") in ("ok", "success", "completed"))
    err_count = sum(
        1 for r in runs if r.get("status") in ("error", "failed", "failure")
    )

    def _pct(lst, p):
        if not lst:
            return 0
        idx = int(len(lst) * p / 100)
        return lst[min(idx, len(lst) - 1)]

    stats = {
        "totalRuns": len(runs),
        "successCount": ok_count,
        "errorCount": err_count,
        "successRate": round(ok_count / len(runs) * 100, 1) if runs else 0,
        "avgDurationMs": int(sum(durations) / len(durations)) if durations else 0,
        "p50DurationMs": _pct(durations, 50),
        "p95DurationMs": _pct(durations, 95),
        "avgCostUsd": round(sum(costs) / len(costs), 6) if costs else 0.0,
        "totalCostUsd": round(sum(costs), 6),
    }
    return {"jobId": job_id, "runs": runs[:50], "stats": stats}


def _cron_runs_from_transcripts(job_id):
    """Derive synthetic cron run records from JSONL session analytics."""
    analytics = _compute_transcript_analytics()
    sessions = analytics.get("sessions", [])
    jobs = _get_crons()
    target_job = next(
        (j for j in jobs if isinstance(j, dict) and j.get("id") == job_id), None
    )

    runs = []
    for sess in sessions:
        if not sess.get("is_cron_candidate"):
            continue
        # Check if this session is attributed to the target job
        score = (
            _score_cron_match(sess, target_job or {"id": job_id}) if target_job else 0
        )
        explicit = job_id in (sess.get("explicit_cron_refs") or set())
        if score < 20 and not explicit:
            continue

        start_ts = sess.get("start_ts", 0)
        end_ts = sess.get("end_ts", 0)
        dur_ms = int((end_ts - start_ts) * 1000) if end_ts > start_ts else 0
        runs.append(
            {
                "sessionId": sess.get("session_id", ""),
                "timestamp": int(start_ts * 1000) if start_ts else 0,
                "status": "ok",
                "durationMs": dur_ms,
                "costUsd": round(float(sess.get("cost_usd", 0.0) or 0.0), 6),
                "tokens": sess.get("tokens", 0),
            }
        )

    # Most-recent first
    runs.sort(key=lambda r: r.get("timestamp", 0), reverse=True)
    return runs[:50]


# (5 route handlers moved to routes/crons.py: /api/cron/<id>/kill,
#  /api/cron-run-log, /api/cron/health-summary, /api/cron/kill-all,
#  /api/cron-health)


# _find_log_file moved to helpers/logs.py (re-exported above)


# _infer_provider_from_model moved to helpers/pricing.py (re-exported above)


# (4 route handlers moved to routes/overview.py: /api/timeline,
#  /api/cloud-cta/status, /api/cloud-cta/send-otp, /api/cloud-cta/verify-otp)


# (bp_logs routes moved to routes/infra.py: /api/logs, /api/flow-events,
#  /api/flow, /api/logs-stream)
# (bp_memory routes moved to routes/infra.py: /api/memory-files, /api/memory,
#  /api/file, /api/memory-analytics)


# (bp_otel handlers moved to routes/meta.py: /v1/metrics, /v1/traces,
#  /api/otel-status)


# ── Multi-Node Fleet API Routes ──────────────────────────────────────────

FLEET_HTML = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ClawMetry Fleet</title>
<link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: 'Manrope', sans-serif; background: #0f1117; color: #e0e0e0; padding: 24px; }
  .header { display: flex; align-items: center; gap: 16px; margin-bottom: 24px; }
  .header h1 { font-size: 28px; font-weight: 800; }
  .header h1 span { color: #0f6fff; }
  .header .back { color: #667; text-decoration: none; font-size: 14px; }
  .header .back:hover { color: #0f6fff; }
  .summary { display: flex; gap: 16px; margin-bottom: 24px; flex-wrap: wrap; }
  .stat-card { background: #1a1d27; border: 1px solid #2a2d37; border-radius: 12px; padding: 16px 20px; min-width: 150px; }
  .stat-card .label { font-size: 12px; color: #667; text-transform: uppercase; letter-spacing: 0.5px; }
  .stat-card .value { font-size: 28px; font-weight: 700; margin-top: 4px; }
  .stat-card .value.green { color: #22c55e; }
  .stat-card .value.red { color: #ef4444; }
  .stat-card .value.blue { color: #0f6fff; }
  .search { margin-bottom: 16px; }
  .search input { background: #1a1d27; border: 1px solid #2a2d37; border-radius: 8px; padding: 10px 16px; color: #e0e0e0; font-size: 14px; width: 300px; outline: none; }
  .search input:focus { border-color: #0f6fff; }
  .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 16px; }
  .node-card { background: #1a1d27; border: 1px solid #2a2d37; border-radius: 12px; padding: 20px; cursor: pointer; transition: border-color 0.2s, transform 0.1s; }
  .node-card:hover { border-color: #0f6fff; transform: translateY(-2px); }
  .node-card .top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
  .node-card .name { font-size: 16px; font-weight: 700; }
  .node-card .status { display: inline-block; padding: 2px 10px; border-radius: 12px; font-size: 11px; font-weight: 600; text-transform: uppercase; }
  .node-card .status.online { background: #16301d; color: #22c55e; }
  .node-card .status.offline { background: #2d1515; color: #ef4444; }
  .node-card .status.unknown { background: #2a2a1a; color: #eab308; }
  .node-card .meta { font-size: 12px; color: #667; margin-bottom: 12px; }
  .node-card .metrics { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
  .node-card .metric { }
  .node-card .metric .ml { font-size: 11px; color: #667; }
  .node-card .metric .mv { font-size: 15px; font-weight: 600; }
  .node-card .svc-bar { display: flex; gap: 6px; align-items: center; margin-top: 12px; padding-top: 12px; border-top: 1px solid #2a2d37; flex-wrap: wrap; }
  .svc-dot { display: flex; align-items: center; gap: 4px; font-size: 11px; color: #889; }
  .svc-dot .dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
  .svc-dot .dot.green { background: #22c55e; box-shadow: 0 0 4px rgba(34,197,94,0.5); }
  .svc-dot .dot.yellow { background: #eab308; box-shadow: 0 0 4px rgba(234,179,8,0.5); }
  .svc-dot .dot.red { background: #ef4444; box-shadow: 0 0 4px rgba(239,68,68,0.5); }
  .svc-dot .dot.gray { background: #4b5563; }
  .empty { text-align: center; padding: 60px; color: #667; }
  .empty h2 { font-size: 20px; margin-bottom: 8px; color: #888; }
  .empty code { background: #1a1d27; padding: 2px 8px; border-radius: 4px; font-size: 13px; }
</style>
</head>
<body>
<div class="header">
  <a href="/" class="back">< Dashboard</a>
  <h1><span>ClawMetry</span> Fleet</h1>
</div>
<div class="summary" id="summary"></div>
<div class="search"><input type="text" id="search" placeholder="Search nodes..." oninput="filterNodes()"></div>
<div class="grid" id="grid"></div>
<div class="empty" id="empty" style="display:none">
  <h2>No nodes registered yet</h2>
  <p>Register a node by sending a POST request:</p>
  <p style="margin-top:12px"><code>curl -X POST -H "X-Fleet-Key: YOUR_KEY" -H "Content-Type: application/json" \<br>
  -d '{"node_id":"my-node","name":"My Agent"}' http://THIS_HOST/api/nodes/register</code></p>
</div>
<script>
window.onerror = function(msg, src, line, col, err) {
  if(window._jsErrSent) return;
  window._jsErrSent = true;
  var nid = (localStorage.getItem('cm_node_id') || '');
  fetch('/api/js-error', {method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({message:msg, source:src, lineno:line, colno:col, stack:err?err.stack:'', url:location.href, node_id:nid})
  }).catch(function(){});
};
window.addEventListener('unhandledrejection', function(e){
  if(window._jsErrSent) return;
  window._jsErrSent = true;
  fetch('/api/js-error', {method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({message: e.reason ? String(e.reason) : 'unhandledrejection', source:'promise', lineno:0, colno:0, stack:'', url:location.href, node_id:(localStorage.getItem('cm_node_id')||'')})
  }).catch(function(){});
});
let allNodes = [];
async function load() {
  const r = await fetch('/api/nodes');
  const d = await r.json();
  allNodes = d.nodes || [];
  const s = d.fleet_summary || {};
  document.getElementById('summary').innerHTML = `
    <div class="stat-card"><div class="label">Total Nodes</div><div class="value blue">${s.total_nodes||0}</div></div>
    <div class="stat-card"><div class="label">Online</div><div class="value green">${s.online||0}</div></div>
    <div class="stat-card"><div class="label">Offline</div><div class="value red">${s.offline||0}</div></div>
    <div class="stat-card"><div class="label">Cost Today</div><div class="value">$${(s.total_cost_today||0).toFixed(2)}</div></div>
    <div class="stat-card"><div class="label">Sessions Today</div><div class="value">${s.total_sessions_today||0}</div></div>
  `;
  renderNodes(allNodes);
}
function svcDot(label, colorClass) {
  return `<div class="svc-dot"><div class="dot ${colorClass}"></div>${esc(label)}</div>`;
}
function renderServiceBar(m) {
  // Build service status bar from metrics service_status field
  const ss = m.service_status || {};
  if (!ss || Object.keys(ss).length === 0) return '';
  const items = [];
  // Gateway
  if ('gateway' in ss) items.push(svcDot('GW', ss.gateway ? 'green' : 'red'));
  // Channels (array of {name, connected})
  const channels = Array.isArray(ss.channels) ? ss.channels : [];
  channels.forEach(function(ch) {
    const c = ch.connected ? 'green' : 'red';
    items.push(svcDot(esc(ch.name||'ch'), c));
  });
  // Sync daemon
  if ('sync' in ss) items.push(svcDot('sync', ss.sync ? 'green' : 'red'));
  // Resources (yellow if degraded)
  if ('resources' in ss) {
    const rc = ss.resources === 'ok' ? 'green' : (ss.resources === 'warn' ? 'yellow' : 'red');
    items.push(svcDot('res', rc));
  }
  if (!items.length) return '';
  return `<div class="svc-bar">${items.join('')}</div>`;
}
function renderNodes(nodes) {
  const grid = document.getElementById('grid');
  const empty = document.getElementById('empty');
  if (!nodes.length) { grid.innerHTML=''; empty.style.display='block'; return; }
  empty.style.display='none';
  grid.innerHTML = nodes.map(n => {
    const m = n.latest_metrics || {};
    const ago = n.last_seen_at ? timeSince(n.last_seen_at) : 'never';
    const cost = (m.cost && m.cost.today_usd) ? m.cost.today_usd.toFixed(2) : '0.00';
    const sessions = (m.sessions && m.sessions.total_today) || 0;
    const model = m.model || 'unknown';
    const disk = (m.health && m.health.disk_pct) ? m.health.disk_pct.toFixed(0)+'%' : '-';
    const svcBar = renderServiceBar(m);
    const secMeta = m.security || {};
    const sandboxedBadge = secMeta.sandbox_enabled
      ? '<span style="display:inline-block;padding:1px 7px;border-radius:10px;font-size:10px;font-weight:600;background:rgba(34,197,94,0.15);color:#22c55e;border:1px solid rgba(34,197,94,0.3);">🔒 Sandboxed</span>'
      : '';
    return `<div class="node-card" onclick="location.href='/api/nodes/${n.node_id}'">
      <div class="top"><div class="name">${esc(n.name||n.node_id)}</div><div style="display:flex;align-items:center;gap:6px;">${sandboxedBadge}<div class="status ${n.status}">${n.status}</div></div></div>
      <div class="meta">${esc(n.hostname||'')} - last seen ${ago}</div>
      <div class="metrics">
        <div class="metric"><div class="ml">Cost Today</div><div class="mv">$${cost}</div></div>
        <div class="metric"><div class="ml">Sessions</div><div class="mv">${sessions}</div></div>
        <div class="metric"><div class="ml">Model</div><div class="mv">${esc(model)}</div></div>
        <div class="metric"><div class="ml">Disk</div><div class="mv">${disk}</div></div>
      </div>
      ${svcBar}
    </div>`;
  }).join('');
}
function filterNodes() {
  const q = document.getElementById('search').value.toLowerCase();
  renderNodes(allNodes.filter(n => (n.name||'').toLowerCase().includes(q) || (n.node_id||'').includes(q) || (n.hostname||'').toLowerCase().includes(q) || JSON.stringify(n.tags||[]).toLowerCase().includes(q)));
}
function timeSince(ts) {
  const s = Math.floor(Date.now()/1000 - ts);
  if (s<60) return s+'s ago'; if (s<3600) return Math.floor(s/60)+'m ago';
  if (s<86400) return Math.floor(s/3600)+'h ago'; return Math.floor(s/86400)+'d ago';
}
function esc(s) { const d=document.createElement('div'); d.textContent=s; return d.innerHTML; }
load(); setInterval(load, 30000);
</script>
</body>
</html>
"""


# ── Fleet + History API Routes moved to routes/fleet_history.py ─────────


# ── Billing Mode Heuristics (API key vs OAuth/included) ──────────────────

_openclaw_cfg_cache = None


def _load_openclaw_config_cached():
    """Load OpenClaw config once (best effort)."""
    global _openclaw_cfg_cache
    if _openclaw_cfg_cache is not None:
        return _openclaw_cfg_cache
    for cf in [
        os.path.expanduser("~/.openclaw/openclaw.json"),
        os.path.expanduser("~/.clawdbot/openclaw.json"),
    ]:
        try:
            with open(cf) as f:
                _openclaw_cfg_cache = json.load(f)
                return _openclaw_cfg_cache
        except Exception:
            continue
    _openclaw_cfg_cache = {}
    return _openclaw_cfg_cache


# _provider_from_model moved to helpers/pricing.py (re-exported above)


def _provider_has_api_key(provider):
    provider = str(provider or "").lower()
    env_map = {
        "openai": ["OPENAI_API_KEY"],
        "anthropic": ["ANTHROPIC_API_KEY"],
        "google": ["GOOGLE_API_KEY", "GEMINI_API_KEY"],
        "openrouter": ["OPENROUTER_API_KEY"],
        "xai": ["XAI_API_KEY"],
    }

    # 1) Direct env check
    for key in env_map.get(provider, []):
        if os.environ.get(key, "").strip():
            return True

    # 2) Config-based check -- try both legacy `providers` and OpenClaw `auth.profiles`
    cfg = _load_openclaw_config_cached()

    # 2a) Legacy: top-level `providers.<name>.apiKey`
    providers = cfg.get("providers", {}) if isinstance(cfg, dict) else {}
    pconf = providers.get(provider, {}) if isinstance(providers, dict) else {}
    if isinstance(pconf, dict):
        api_key = str(pconf.get("apiKey", "")).strip()
        api_key_env = str(pconf.get("apiKeyEnv", "")).strip()
        if api_key:
            return True
        if api_key_env and os.environ.get(api_key_env, "").strip():
            return True

    # 2b) OpenClaw style: `auth.profiles.<provider:*>.mode == "token"`
    auth = cfg.get("auth", {}) if isinstance(cfg, dict) else {}
    profiles = auth.get("profiles", {}) if isinstance(auth, dict) else {}
    for profile_name, profile_cfg in (
        profiles.items() if isinstance(profiles, dict) else []
    ):
        if not isinstance(profile_cfg, dict):
            continue
        profile_provider = str(profile_cfg.get("provider", "")).lower()
        if profile_provider == provider and profile_cfg.get("mode") == "token":
            return True

    return False


def _build_model_billing(model_usage):
    """Return per-model billing heuristics + summary for UI."""
    model_billing = []
    has_api_key_model = False
    has_non_api_key_model = False

    for model, tokens in sorted(model_usage.items(), key=lambda x: -x[1]):
        provider = _provider_from_model(model)
        api_key_configured = _provider_has_api_key(provider)
        mode = "likely_api_key" if api_key_configured else "likely_oauth_or_included"
        if api_key_configured:
            has_api_key_model = True
        else:
            has_non_api_key_model = True

        model_billing.append(
            {
                "model": model,
                "provider": provider,
                "tokens": tokens,
                "apiKeyConfigured": api_key_configured,
                "billingMode": mode,
            }
        )

    if has_api_key_model and has_non_api_key_model:
        summary = "mixed"
    elif has_api_key_model:
        summary = "likely_api_key"
    else:
        summary = "likely_oauth_or_included"

    return model_billing, summary


# ── Enhanced Cost Tracking Utilities ─────────────────────────────────────


def _get_model_pricing():
    """Model-specific pricing per 1M tokens (input, output)."""
    return {
        "claude-opus": (15.0, 75.0),  # Claude 3 Opus
        "claude-sonnet": (3.0, 15.0),  # Claude 3 Sonnet
        "claude-haiku": (0.25, 1.25),  # Claude 3 Haiku
        "gpt-4": (10.0, 30.0),  # GPT-4 Turbo
        "gpt-3.5": (1.0, 2.0),  # GPT-3.5 Turbo
        "default": (15.0, 45.0),  # Conservative estimate
    }


def _calculate_enhanced_costs(daily_tokens, today_str, week_start, month_start):
    """Enhanced cost calculation with model-specific pricing."""
    pricing = _get_model_pricing()

    # For log parsing fallback, assume 60/40 input/output ratio
    input_ratio, output_ratio = 0.6, 0.4

    def calc_cost(tokens, model_key="default"):
        if tokens == 0:
            return 0.0
        in_price, out_price = pricing.get(model_key, pricing["default"])
        input_cost = (tokens * input_ratio) * (in_price / 1_000_000)
        output_cost = (tokens * output_ratio) * (out_price / 1_000_000)
        return input_cost + output_cost

    today_tok = daily_tokens.get(today_str, 0)
    week_tok = sum(v for k, v in daily_tokens.items() if k >= week_start)
    month_tok = sum(v for k, v in daily_tokens.items() if k >= month_start)

    return (
        round(calc_cost(today_tok), 4),
        round(calc_cost(week_tok), 4),
        round(calc_cost(month_tok), 4),
    )


def _analyze_usage_trends(daily_tokens):
    """Analyze usage trends for predictions."""
    if len(daily_tokens) < 3:
        return {"prediction": None, "trend": "insufficient_data"}

    # Get last 7 days of data
    recent_days = sorted(daily_tokens.items())[-7:]
    if len(recent_days) < 3:
        return {"prediction": None, "trend": "insufficient_data"}

    tokens_series = [v for k, v in recent_days]

    # Simple trend analysis
    if len(tokens_series) >= 3:
        recent_avg = sum(tokens_series[-3:]) / 3
        older_avg = (
            sum(tokens_series[:-3]) / max(1, len(tokens_series) - 3)
            if len(tokens_series) > 3
            else recent_avg
        )

        if recent_avg > older_avg * 1.2:
            trend = "increasing"
        elif recent_avg < older_avg * 0.8:
            trend = "decreasing"
        else:
            trend = "stable"

        # Monthly prediction based on recent average
        daily_avg = sum(tokens_series[-7:]) / len(tokens_series[-7:])
        monthly_prediction = daily_avg * 30

        return {
            "trend": trend,
            "dailyAvg": int(daily_avg),
            "monthlyPrediction": int(monthly_prediction),
        }

    return {"prediction": None, "trend": "stable"}


def _generate_cost_warnings(
    today_cost,
    week_cost,
    month_cost,
    trend_data,
    month_tokens=0,
    billing_summary="unknown",
):
    """Generate cost warnings based on thresholds."""
    warnings = []

    # Daily cost warnings
    if today_cost > 10.0:
        warnings.append(
            {
                "type": "high_daily_cost",
                "level": "error",
                "message": f"High daily cost: ${today_cost:.2f} (threshold: $10)",
            }
        )
    elif today_cost > 5.0:
        warnings.append(
            {
                "type": "elevated_daily_cost",
                "level": "warning",
                "message": f"Elevated daily cost: ${today_cost:.2f}",
            }
        )

    # Weekly cost warnings
    if week_cost > 50.0:
        warnings.append(
            {
                "type": "high_weekly_cost",
                "level": "error",
                "message": f"High weekly cost: ${week_cost:.2f} (threshold: $50)",
            }
        )
    elif week_cost > 25.0:
        warnings.append(
            {
                "type": "elevated_weekly_cost",
                "level": "warning",
                "message": f"Elevated weekly cost: ${week_cost:.2f}",
            }
        )

    # Monthly cost warnings
    if month_cost > 200.0:
        warnings.append(
            {
                "type": "high_monthly_cost",
                "level": "error",
                "message": f"High monthly cost: ${month_cost:.2f} (threshold: $200)",
            }
        )
    elif month_cost > 100.0:
        warnings.append(
            {
                "type": "elevated_monthly_cost",
                "level": "warning",
                "message": f"Elevated monthly cost: ${month_cost:.2f}",
            }
        )

    # Trend-based warnings (use observed effective rate, not hard-coded $/token)
    if (
        trend_data.get("trend") == "increasing"
        and trend_data.get("monthlyPrediction", 0) > 300
    ):
        # If likely OAuth/included, avoid scary projected billing alerts.
        if billing_summary != "likely_oauth_or_included":
            projected_cost = 0.0
            if month_tokens and month_cost > 0:
                effective_cost_per_token = month_cost / float(month_tokens)
                projected_cost = (
                    trend_data.get("monthlyPrediction", 0) * effective_cost_per_token
                )

            if projected_cost > 0:
                warnings.append(
                    {
                        "type": "trend_warning",
                        "level": "warning",
                        "message": f"Usage trending up - projected monthly equivalent (if billed): ${projected_cost:.2f}",
                    }
                )

    return warnings


# ── Usage cache ─────────────────────────────────────────────────────────
_usage_cache = {"data": None, "ts": 0}
_USAGE_CACHE_TTL = 60  # seconds
_sessions_cache = {"data": None, "ts": 0}
_SESSIONS_CACHE_TTL = 10  # seconds
_transcript_analytics_cache = {"data": None, "ts": 0}
_TRANSCRIPT_ANALYTICS_TTL = 60  # seconds


def _get_sessions_dir():
    base = SESSIONS_DIR or os.path.expanduser("~/.openclaw/agents/main/sessions")
    if os.path.isdir(base):
        return base
    fallback = os.path.expanduser("~/.moltbot/agents/main/sessions")
    return fallback if os.path.isdir(fallback) else base


def _parse_event_timestamp(ts_val, fallback_ts=None):
    if ts_val is None:
        return fallback_ts
    try:
        if isinstance(ts_val, (int, float)):
            return datetime.fromtimestamp(ts_val / 1000 if ts_val > 1e12 else ts_val)
        if isinstance(ts_val, str):
            return datetime.fromisoformat(ts_val.replace("Z", "+00:00"))
    except Exception:
        pass
    return fallback_ts


def _extract_usage_metrics(obj):
    """Best-effort usage extraction from mixed transcript schemas."""
    message = obj.get("message", {}) if isinstance(obj.get("message"), dict) else {}
    usage = message.get("usage")
    if not isinstance(usage, dict):
        usage = obj.get("usage")
    if not isinstance(usage, dict):
        usage = obj.get("tokens_used")
    if not isinstance(usage, dict):
        return {"tokens": 0, "cost": 0.0}

    in_toks = usage.get("input", usage.get("input_tokens", 0)) or 0
    out_toks = usage.get("output", usage.get("output_tokens", 0)) or 0
    cache_read = usage.get("cacheRead", usage.get("cache_read_tokens", 0)) or 0
    cache_write = usage.get("cacheWrite", usage.get("cache_write_tokens", 0)) or 0
    total = usage.get("totalTokens", usage.get("total_tokens", 0)) or 0
    if not total:
        total = in_toks + out_toks + cache_read + cache_write

    cost = 0.0
    cost_data = usage.get("cost", {})
    if isinstance(cost_data, dict):
        raw = cost_data.get("total", cost_data.get("usd", 0))
        try:
            cost = float(raw or 0)
        except Exception:
            cost = 0.0
    elif isinstance(cost_data, (int, float)):
        cost = float(cost_data)

    return {
        "tokens": int(total or 0),
        "cost": float(cost or 0.0),
    }


def _normalize_plugin_name(tool_name):
    name = str(tool_name or "").strip().lower()
    if not name:
        return ""
    for sep in ("/", ":", "."):
        if sep in name:
            name = name.split(sep, 1)[0]
            break
    return name[:64]


def _extract_tool_plugins(obj):
    """Extract plugin/tool names from known tool call locations."""
    plugins = []
    message = obj.get("message", {}) if isinstance(obj.get("message"), dict) else {}

    # Newer format: message.content[{type:'toolCall', name:'...'}]
    for part in message.get("content") or []:
        if not isinstance(part, dict):
            continue
        if part.get("type") == "toolCall":
            p = _normalize_plugin_name(part.get("name", ""))
            if p:
                plugins.append(p)

    # OpenAI-like tool call array
    for tc in obj.get("tool_calls") or []:
        if not isinstance(tc, dict):
            continue
        p = _normalize_plugin_name(
            tc.get("name") or (tc.get("function") or {}).get("name", "")
        )
        if p:
            plugins.append(p)

    # Alternate key
    for tc in obj.get("tool_use") or []:
        if not isinstance(tc, dict):
            continue
        p = _normalize_plugin_name(tc.get("name", ""))
        if p:
            plugins.append(p)

    return plugins


def _collect_cron_refs(obj, out_refs):
    """Recursively collect explicit cron/job IDs from transcript event objects."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            lk = str(k).lower()
            if lk in (
                "cronid",
                "cron_id",
                "cronjobid",
                "cron_job_id",
                "jobid",
                "job_id",
                "scheduleid",
                "schedule_id",
            ):
                if isinstance(v, (str, int, float)):
                    sv = str(v).strip().lower()
                    if sv:
                        out_refs.add(sv)
            _collect_cron_refs(v, out_refs)
    elif isinstance(obj, list):
        for it in obj:
            _collect_cron_refs(it, out_refs)


def _score_cron_match(session, job):
    """Heuristic score for mapping a session to a cron job."""
    refs = session.get("explicit_cron_refs", set())
    text = session.get("search_text", "")
    score = 0

    jid = str(job.get("id", "")).strip().lower()
    jname = str(job.get("name", job.get("label", ""))).strip().lower()

    if jid and jid in refs:
        score += 100
    if jname and jname in refs:
        score += 80
    if jid and jid in text:
        score += 30
    if jname and len(jname) >= 4 and jname in text:
        score += 20

    payload = job.get("payload") or job.get("config") or {}
    if isinstance(payload, dict):
        prompt = (
            str(
                payload.get("prompt")
                or payload.get("text")
                or payload.get("message")
                or ""
            )
            .strip()
            .lower()
        )
        if prompt:
            for w in [w for w in _re.split(r"[^a-z0-9_]+", prompt) if len(w) >= 5][:8]:
                if w in text:
                    score += 1
    return score


def _compute_transcript_analytics():
    """Parse transcript files once for usage, anomalies, cron attribution, and plugin breakdown."""
    now = time.time()
    if (
        _transcript_analytics_cache["data"] is not None
        and (now - _transcript_analytics_cache["ts"]) < _TRANSCRIPT_ANALYTICS_TTL
    ):
        return _transcript_analytics_cache["data"]

    sessions_dir = _get_sessions_dir()
    summaries = []
    plugin_stats = defaultdict(lambda: {"tokens": 0.0, "cost": 0.0, "calls": 0})
    daily_tokens = {}
    daily_cost = {}
    model_usage = {}

    if os.path.isdir(sessions_dir):
        for fname in os.listdir(sessions_dir):
            # Accept both live `.jsonl` and archived `.jsonl.reset.<ts>` files.
            if not (fname.endswith(".jsonl") or ".jsonl.reset." in fname):
                continue
            sid = fname.split(".jsonl", 1)[0]
            fpath = os.path.join(sessions_dir, fname)
            fallback_dt = datetime.fromtimestamp(os.path.getmtime(fpath))

            s_tokens = 0
            s_cost = 0.0
            s_model = "unknown"
            s_start = None
            s_end = None
            search_parts = []
            explicit_cron_refs = set()

            try:
                with open(fpath, "r") as f:
                    for line in f:
                        try:
                            obj = json.loads(line.strip())
                        except Exception:
                            continue

                        ts = _parse_event_timestamp(
                            obj.get("timestamp")
                            or obj.get("time")
                            or obj.get("created_at"),
                            fallback_dt,
                        )
                        if ts:
                            if s_start is None or ts < s_start:
                                s_start = ts
                            if s_end is None or ts > s_end:
                                s_end = ts

                        # Collect cron hints from metadata and known custom session-info events
                        _collect_cron_refs(obj, explicit_cron_refs)
                        if obj.get("customType") == "openclaw.session-info":
                            search_parts.append(
                                json.dumps(obj.get("data", {}), default=str).lower()
                            )

                        message = (
                            obj.get("message", {})
                            if isinstance(obj.get("message"), dict)
                            else {}
                        )
                        model = message.get("model") or obj.get("model")
                        if model:
                            s_model = model

                        usage_metrics = _extract_usage_metrics(obj)
                        tokens = usage_metrics["tokens"]
                        cost = usage_metrics["cost"]

                        if tokens > 0:
                            s_tokens += tokens
                            if cost > 0:
                                s_cost += cost

                            # Bucket to this event's actual date, not the
                            # session start date. Fixes the bug where a
                            # long-running session's entire token total
                            # piled onto the day the session started.
                            _ev_date = (ts or fallback_dt).strftime("%Y-%m-%d")
                            daily_tokens[_ev_date] = daily_tokens.get(_ev_date, 0) + tokens
                            daily_cost[_ev_date] = daily_cost.get(_ev_date, 0.0) + cost

                            plugins = _extract_tool_plugins(obj)
                            if plugins:
                                share_tokens = float(tokens) / float(len(plugins))
                                share_cost = (
                                    float(cost) / float(len(plugins))
                                    if cost > 0
                                    else 0.0
                                )
                                for p in plugins:
                                    plugin_stats[p]["tokens"] += share_tokens
                                    plugin_stats[p]["cost"] += share_cost
                                    plugin_stats[p]["calls"] += 1

                        # Textual hints for cron matching
                        if isinstance(message.get("content"), list):
                            for part in message.get("content", []):
                                if isinstance(part, dict):
                                    txt = part.get("text")
                                    if isinstance(txt, str) and txt:
                                        search_parts.append(txt.lower())
                        if obj.get("type") == "custom":
                            try:
                                search_parts.append(
                                    json.dumps(obj, default=str).lower()
                                )
                            except Exception:
                                pass

                if s_start is None:
                    s_start = fallback_dt
                if s_end is None:
                    s_end = fallback_dt

                # daily_tokens/daily_cost are now populated per-event above
                # (bucketed by each event's timestamp, not the session start).
                # Only model_usage still aggregates per-session.
                model_usage[s_model] = model_usage.get(s_model, 0) + s_tokens

                search_text = " ".join(search_parts)
                if len(search_text) > 12000:
                    search_text = search_text[:12000]

                summaries.append(
                    {
                        "session_id": sid,
                        "tokens": s_tokens,
                        "cost_usd": s_cost,
                        "model": s_model,
                        "start_ts": s_start.timestamp() if s_start else 0,
                        "end_ts": s_end.timestamp() if s_end else 0,
                        "day": s_start.strftime("%Y-%m-%d") if s_start else fallback_dt.strftime("%Y-%m-%d"),
                        "search_text": search_text,
                        "explicit_cron_refs": explicit_cron_refs,
                        "is_cron_candidate": ("cron" in search_text)
                        or bool(explicit_cron_refs),
                    }
                )
            except Exception:
                continue

    summaries.sort(key=lambda s: s.get("start_ts", 0))
    result = {
        "sessions": summaries,
        "plugin_stats": plugin_stats,
        "daily_tokens": daily_tokens,
        "daily_cost": daily_cost,
        "model_usage": model_usage,
    }
    _transcript_analytics_cache["data"] = result
    _transcript_analytics_cache["ts"] = now
    return result


_transcript_analytics_cache = {"data": None, "ts": 0}
_TRANSCRIPT_ANALYTICS_TTL = 60  # seconds


def _get_sessions_dir():
    base = SESSIONS_DIR or os.path.expanduser("~/.openclaw/agents/main/sessions")
    if os.path.isdir(base):
        return base
    fallback = os.path.expanduser("~/.moltbot/agents/main/sessions")
    return fallback if os.path.isdir(fallback) else base


def _parse_event_timestamp(ts_val, fallback_ts=None):
    if ts_val is None:
        return fallback_ts
    try:
        if isinstance(ts_val, (int, float)):
            return datetime.fromtimestamp(ts_val / 1000 if ts_val > 1e12 else ts_val)
        if isinstance(ts_val, str):
            return datetime.fromisoformat(ts_val.replace("Z", "+00:00"))
    except Exception:
        pass
    return fallback_ts


def _extract_usage_metrics(obj):
    """Best-effort usage extraction from mixed transcript schemas."""
    message = obj.get("message", {}) if isinstance(obj.get("message"), dict) else {}
    usage = message.get("usage")
    if not isinstance(usage, dict):
        usage = obj.get("usage")
    if not isinstance(usage, dict):
        usage = obj.get("tokens_used")
    if not isinstance(usage, dict):
        return {"tokens": 0, "cost": 0.0}

    in_toks = usage.get("input", usage.get("input_tokens", 0)) or 0
    out_toks = usage.get("output", usage.get("output_tokens", 0)) or 0
    cache_read = usage.get("cacheRead", usage.get("cache_read_tokens", 0)) or 0
    cache_write = usage.get("cacheWrite", usage.get("cache_write_tokens", 0)) or 0
    total = usage.get("totalTokens", usage.get("total_tokens", 0)) or 0
    if not total:
        total = in_toks + out_toks + cache_read + cache_write

    cost = 0.0
    cost_data = usage.get("cost", {})
    if isinstance(cost_data, dict):
        raw = cost_data.get("total", cost_data.get("usd", 0))
        try:
            cost = float(raw or 0)
        except Exception:
            cost = 0.0
    elif isinstance(cost_data, (int, float)):
        cost = float(cost_data)

    return {
        "tokens": int(total or 0),
        "cost": float(cost or 0.0),
    }


def _normalize_plugin_name(tool_name):
    name = str(tool_name or "").strip().lower()
    if not name:
        return ""
    for sep in ("/", ":", "."):
        if sep in name:
            name = name.split(sep, 1)[0]
            break
    return name[:64]


def _extract_tool_plugins(obj):
    """Extract plugin/tool names from known tool call locations."""
    plugins = []
    message = obj.get("message", {}) if isinstance(obj.get("message"), dict) else {}

    # Newer format: message.content[{type:'toolCall', name:'...'}]
    for part in message.get("content") or []:
        if not isinstance(part, dict):
            continue
        if part.get("type") == "toolCall":
            p = _normalize_plugin_name(part.get("name", ""))
            if p:
                plugins.append(p)

    # OpenAI-like tool call array
    for tc in obj.get("tool_calls") or []:
        if not isinstance(tc, dict):
            continue
        p = _normalize_plugin_name(
            tc.get("name") or (tc.get("function") or {}).get("name", "")
        )
        if p:
            plugins.append(p)

    # Alternate key
    for tc in obj.get("tool_use") or []:
        if not isinstance(tc, dict):
            continue
        p = _normalize_plugin_name(tc.get("name", ""))
        if p:
            plugins.append(p)

    return plugins


def _collect_cron_refs(obj, out_refs):
    """Recursively collect explicit cron/job IDs from transcript event objects."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            lk = str(k).lower()
            if lk in (
                "cronid",
                "cron_id",
                "cronjobid",
                "cron_job_id",
                "jobid",
                "job_id",
                "scheduleid",
                "schedule_id",
            ):
                if isinstance(v, (str, int, float)):
                    sv = str(v).strip().lower()
                    if sv:
                        out_refs.add(sv)
            _collect_cron_refs(v, out_refs)
    elif isinstance(obj, list):
        for it in obj:
            _collect_cron_refs(it, out_refs)


def _score_cron_match(session, job):
    """Heuristic score for mapping a session to a cron job."""
    refs = session.get("explicit_cron_refs", set())
    text = session.get("search_text", "")
    score = 0

    jid = str(job.get("id", "")).strip().lower()
    jname = str(job.get("name", job.get("label", ""))).strip().lower()

    if jid and jid in refs:
        score += 100
    if jname and jname in refs:
        score += 80
    if jid and jid in text:
        score += 30
    if jname and len(jname) >= 4 and jname in text:
        score += 20

    payload = job.get("payload") or job.get("config") or {}
    if isinstance(payload, dict):
        prompt = (
            str(
                payload.get("prompt")
                or payload.get("text")
                or payload.get("message")
                or ""
            )
            .strip()
            .lower()
        )
        if prompt:
            for w in [w for w in _re.split(r"[^a-z0-9_]+", prompt) if len(w) >= 5][:8]:
                if w in text:
                    score += 1
    return score


def _compute_transcript_analytics():
    """Parse transcript files once for usage, anomalies, cron attribution, and plugin breakdown."""
    now = time.time()
    if (
        _transcript_analytics_cache["data"] is not None
        and (now - _transcript_analytics_cache["ts"]) < _TRANSCRIPT_ANALYTICS_TTL
    ):
        return _transcript_analytics_cache["data"]

    sessions_dir = _get_sessions_dir()
    summaries = []
    plugin_stats = defaultdict(lambda: {"tokens": 0.0, "cost": 0.0, "calls": 0})
    plugin_daily_stats: dict = {}  # day -> plugin -> {tokens, cost, calls} (GH#201 trend)
    daily_tokens = {}
    daily_cost = {}
    model_usage = {}

    if os.path.isdir(sessions_dir):
        for fname in os.listdir(sessions_dir):
            # Accept both live `.jsonl` and archived `.jsonl.reset.<ts>` files.
            # Reset archives carry real historical token usage from earlier
            # days; skipping them was making the 14-day chart pile every
            # past-day total onto today.
            if not (fname.endswith(".jsonl") or ".jsonl.reset." in fname):
                continue
            sid = fname.split(".jsonl", 1)[0]
            fpath = os.path.join(sessions_dir, fname)
            fallback_dt = datetime.fromtimestamp(os.path.getmtime(fpath))

            s_tokens = 0
            s_cost = 0.0
            s_model = "unknown"
            s_start = None
            s_end = None
            search_parts = []
            explicit_cron_refs = set()

            try:
                with open(fpath, "r") as f:
                    for line in f:
                        try:
                            obj = json.loads(line.strip())
                        except Exception:
                            continue

                        ts = _parse_event_timestamp(
                            obj.get("timestamp")
                            or obj.get("time")
                            or obj.get("created_at"),
                            fallback_dt,
                        )
                        if ts:
                            if s_start is None or ts < s_start:
                                s_start = ts
                            if s_end is None or ts > s_end:
                                s_end = ts

                        # Collect cron hints from metadata and known custom session-info events
                        _collect_cron_refs(obj, explicit_cron_refs)
                        if obj.get("customType") == "openclaw.session-info":
                            search_parts.append(
                                json.dumps(obj.get("data", {}), default=str).lower()
                            )

                        message = (
                            obj.get("message", {})
                            if isinstance(obj.get("message"), dict)
                            else {}
                        )
                        model = message.get("model") or obj.get("model")
                        if model:
                            s_model = model

                        usage_metrics = _extract_usage_metrics(obj)
                        tokens = usage_metrics["tokens"]
                        cost = usage_metrics["cost"]

                        if tokens > 0:
                            s_tokens += tokens
                            if cost > 0:
                                s_cost += cost

                            # Bucket to this event's actual date, not the
                            # session start date. Fixes the bug where a
                            # long-running session's entire token total
                            # piled onto the day the session started.
                            _ev_date = (ts or fallback_dt).strftime("%Y-%m-%d")
                            daily_tokens[_ev_date] = daily_tokens.get(_ev_date, 0) + tokens
                            daily_cost[_ev_date] = daily_cost.get(_ev_date, 0.0) + cost

                            plugins = _extract_tool_plugins(obj)
                            if plugins:
                                share_tokens = float(tokens) / float(len(plugins))
                                share_cost = (
                                    float(cost) / float(len(plugins))
                                    if cost > 0
                                    else 0.0
                                )
                                # Track daily breakdown for trend analysis (GH#201)
                                # use the event's actual day so trend lines
                                # match the headline 14-day chart.
                                _ev_day = (ts or fallback_dt).strftime("%Y-%m-%d")
                                for p in plugins:
                                    plugin_stats[p]["tokens"] += share_tokens
                                    plugin_stats[p]["cost"] += share_cost
                                    plugin_stats[p]["calls"] += 1
                                    if _ev_day not in plugin_daily_stats:
                                        plugin_daily_stats[_ev_day] = {}
                                    if p not in plugin_daily_stats[_ev_day]:
                                        plugin_daily_stats[_ev_day][p] = {"tokens": 0.0, "cost": 0.0, "calls": 0}
                                    plugin_daily_stats[_ev_day][p]["tokens"] += share_tokens
                                    plugin_daily_stats[_ev_day][p]["cost"] += share_cost
                                    plugin_daily_stats[_ev_day][p]["calls"] += 1

                        # Textual hints for cron matching
                        if isinstance(message.get("content"), list):
                            for part in message.get("content", []):
                                if isinstance(part, dict):
                                    txt = part.get("text")
                                    if isinstance(txt, str) and txt:
                                        search_parts.append(txt.lower())
                        if obj.get("type") == "custom":
                            try:
                                search_parts.append(
                                    json.dumps(obj, default=str).lower()
                                )
                            except Exception:
                                pass

                if s_start is None:
                    s_start = fallback_dt
                if s_end is None:
                    s_end = fallback_dt

                # daily_tokens/daily_cost are now populated per-event above
                # (bucketed by each event's timestamp, not the session start).
                # Only model_usage still aggregates per-session.
                model_usage[s_model] = model_usage.get(s_model, 0) + s_tokens

                search_text = " ".join(search_parts)
                if len(search_text) > 12000:
                    search_text = search_text[:12000]

                summaries.append(
                    {
                        "session_id": sid,
                        "tokens": s_tokens,
                        "cost_usd": s_cost,
                        "model": s_model,
                        "start_ts": s_start.timestamp() if s_start else 0,
                        "end_ts": s_end.timestamp() if s_end else 0,
                        "day": s_start.strftime("%Y-%m-%d") if s_start else fallback_dt.strftime("%Y-%m-%d"),
                        "search_text": search_text,
                        "explicit_cron_refs": explicit_cron_refs,
                        "is_cron_candidate": ("cron" in search_text)
                        or bool(explicit_cron_refs),
                    }
                )
            except Exception:
                continue

    summaries.sort(key=lambda s: s.get("start_ts", 0))
    result = {
        "sessions": summaries,
        "plugin_stats": plugin_stats,
        "plugin_daily_stats": plugin_daily_stats,
        "daily_tokens": daily_tokens,
        "daily_cost": daily_cost,
        "model_usage": model_usage,
    }
    _transcript_analytics_cache["data"] = result
    _transcript_analytics_cache["ts"] = now
    return result


def _compute_session_cost_anomalies(session_summaries):
    """Flag sessions with cost >2x their rolling 7-day session-cost average."""
    now_ts = time.time()
    day_ago = now_ts - 86400
    anomalies = []

    for i, sess in enumerate(session_summaries):
        ts = sess.get("start_ts", 0) or 0
        if ts < day_ago:
            continue
        cost = float(sess.get("cost_usd", 0.0) or 0.0)
        if cost <= 0:
            continue

        window_start = ts - (7 * 86400)
        window_costs = []
        for prev in session_summaries[:i]:
            pts = prev.get("start_ts", 0) or 0
            pc = float(prev.get("cost_usd", 0.0) or 0.0)
            if pts >= window_start and pts < ts and pc > 0:
                window_costs.append(pc)

        if not window_costs:
            continue
        avg = sum(window_costs) / float(len(window_costs))
        if avg <= 0:
            continue
        if cost > (2.0 * avg):
            anomalies.append(
                {
                    "session_id": sess.get("session_id"),
                    "cost_usd": round(cost, 6),
                    "rolling_avg_usd": round(avg, 6),
                    "ratio": round(cost / avg, 3),
                    "timestamp": int(ts * 1000),
                }
            )

    anomalies.sort(key=lambda a: a.get("ratio", 0), reverse=True)
    return anomalies


# ── New Feature APIs ────────────────────────────────────────────────────


# (bp_usage routes moved to routes/usage.py)


# ─────────────────────────────────────────────────────────────────────────────
# Anomaly Detection Engine (GH #301)
# Rolling-baseline anomaly detector using local SQLite storage.
# Detects cost spikes (>2x), token spikes (>2x), error rate spikes (>3x)
# against a 7-day rolling baseline derived from session transcripts.
# ─────────────────────────────────────────────────────────────────────────────

_ANOMALY_DB_PATH = os.path.expanduser("~/.openclaw/clawmetry.db")
_anomaly_db_conn = None
_anomaly_db_lock = threading.Lock()


def _get_anomaly_db():
    """Return a thread-safe SQLite connection for anomaly storage.

    Uses ~/.openclaw/clawmetry.db (creates if absent). The schema is
    append-only so it is safe to call from any thread with the lock held.
    """
    global _anomaly_db_conn
    with _anomaly_db_lock:
        if _anomaly_db_conn is None:
            db_dir = os.path.dirname(_ANOMALY_DB_PATH)
            os.makedirs(db_dir, exist_ok=True)
            _anomaly_db_conn = sqlite3.connect(
                _ANOMALY_DB_PATH, check_same_thread=False
            )
            _anomaly_db_conn.row_factory = sqlite3.Row
            _anomaly_db_conn.execute("PRAGMA journal_mode=WAL")
            _anomaly_db_conn.execute("PRAGMA synchronous=NORMAL")
            _anomaly_db_conn.executescript("""
                CREATE TABLE IF NOT EXISTS anomalies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    detected_at REAL NOT NULL,
                    session_key TEXT NOT NULL,
                    metric TEXT NOT NULL,
                    value REAL NOT NULL,
                    baseline REAL NOT NULL,
                    ratio REAL NOT NULL,
                    severity TEXT NOT NULL,
                    acknowledged INTEGER DEFAULT 0
                );
                CREATE INDEX IF NOT EXISTS idx_anomalies_ts ON anomalies(detected_at);
                CREATE INDEX IF NOT EXISTS idx_anomalies_session ON anomalies(session_key);
                CREATE INDEX IF NOT EXISTS idx_anomalies_metric ON anomalies(metric);
            """)
            _anomaly_db_conn.commit()
        return _anomaly_db_conn


def _detect_and_store_anomalies():
    """Compute rolling-baseline anomalies and persist new ones to SQLite.

    Runs on every call to /api/anomalies (with a short in-memory TTL to
    avoid re-scanning transcripts too frequently).

    Detects:
    - cost_spike:        session cost > 2x 7-day rolling average
    - token_spike:       session tokens > 2x 7-day rolling average
    - error_rate_spike:  rolling 24h error rate > 3x 7-day baseline

    Returns list of anomaly dicts (both freshly detected and stored).
    """

    analytics = _compute_transcript_analytics()
    sessions = analytics.get("sessions", [])
    now_ts = time.time()
    window_7d = 7 * 86400
    window_24h = 86400

    # ── Build 7-day baseline ──────────────────────────────────────────────────
    baseline_window_start = now_ts - window_7d
    baseline_sessions = [
        s for s in sessions if float(s.get("start_ts", 0) or 0) >= baseline_window_start
    ]

    baseline_costs = [
        float(s.get("cost_usd", 0.0) or 0.0)
        for s in baseline_sessions
        if float(s.get("cost_usd", 0.0) or 0.0) > 0
    ]
    baseline_tokens = [
        int(s.get("tokens", 0) or 0)
        for s in baseline_sessions
        if int(s.get("tokens", 0) or 0) > 0
    ]

    avg_cost_7d = sum(baseline_costs) / len(baseline_costs) if baseline_costs else 0.0
    avg_tokens_7d = (
        sum(baseline_tokens) / len(baseline_tokens) if baseline_tokens else 0.0
    )

    # Error-rate baseline: fraction of sessions in last 7d with errors
    # (We approximate via cost=0 + tokens>0 as proxy for "errored" sessions.)
    err_baseline_count = sum(
        1
        for s in baseline_sessions
        if float(s.get("cost_usd", 0.0) or 0.0) == 0
        and int(s.get("tokens", 0) or 0) > 100
    )
    err_baseline_rate = err_baseline_count / max(len(baseline_sessions), 1)

    # 24h error rate
    recent_sessions_24h = [
        s for s in sessions if float(s.get("start_ts", 0) or 0) >= now_ts - window_24h
    ]
    recent_err_count = sum(
        1
        for s in recent_sessions_24h
        if float(s.get("cost_usd", 0.0) or 0.0) == 0
        and int(s.get("tokens", 0) or 0) > 100
    )
    recent_err_rate = recent_err_count / max(len(recent_sessions_24h), 1)

    # ── Detect anomalies in recent (last 24h) sessions ─────────────────────
    new_anomalies = []
    day_ago = now_ts - window_24h

    for sess in sessions:
        ts = float(sess.get("start_ts", 0) or 0)
        if ts < day_ago:
            continue
        sid = sess.get("session_id", "")
        cost = float(sess.get("cost_usd", 0.0) or 0.0)
        tokens = int(sess.get("tokens", 0) or 0)

        # Cost spike
        if avg_cost_7d > 0 and cost > avg_cost_7d * 2.0:
            ratio = round(cost / avg_cost_7d, 3)
            severity = "critical" if ratio > 5 else "high" if ratio > 3 else "medium"
            new_anomalies.append(
                {
                    "session_key": sid,
                    "metric": "cost_spike",
                    "value": cost,
                    "baseline": avg_cost_7d,
                    "ratio": ratio,
                    "severity": severity,
                    "detected_at": ts,
                }
            )

        # Token spike
        if avg_tokens_7d > 0 and tokens > avg_tokens_7d * 2.0:
            ratio = round(tokens / avg_tokens_7d, 3)
            severity = "critical" if ratio > 5 else "high" if ratio > 3 else "medium"
            new_anomalies.append(
                {
                    "session_key": sid,
                    "metric": "token_spike",
                    "value": tokens,
                    "baseline": avg_tokens_7d,
                    "ratio": ratio,
                    "severity": severity,
                    "detected_at": ts,
                }
            )

    # Error rate spike (aggregate — tied to a synthetic session_key)
    if err_baseline_rate > 0 and recent_err_rate > err_baseline_rate * 3.0:
        ratio = round(recent_err_rate / err_baseline_rate, 3)
        new_anomalies.append(
            {
                "session_key": "__error_rate__",
                "metric": "error_rate_spike",
                "value": round(recent_err_rate, 4),
                "baseline": round(err_baseline_rate, 4),
                "ratio": ratio,
                "severity": "high" if ratio > 5 else "medium",
                "detected_at": now_ts,
            }
        )

    # Session frequency spike: compare 24h session count vs 7-day daily average
    if len(baseline_sessions) > 0:
        days_in_window = max((now_ts - baseline_window_start) / 86400, 1.0)
        avg_sessions_per_day = len(baseline_sessions) / days_in_window
        sessions_last_24h = len(recent_sessions_24h)
        if avg_sessions_per_day >= 2 and sessions_last_24h > avg_sessions_per_day * 2.5:
            freq_ratio = round(sessions_last_24h / avg_sessions_per_day, 3)
            new_anomalies.append(
                {
                    "session_key": "__session_frequency__",
                    "metric": "session_frequency_spike",
                    "value": sessions_last_24h,
                    "baseline": round(avg_sessions_per_day, 2),
                    "ratio": freq_ratio,
                    "severity": "high" if freq_ratio > 4 else "medium",
                    "detected_at": now_ts,
                }
            )

    # ── Persist new anomalies (deduplicate by session_key + metric within 24h) ──
    try:
        db = _get_anomaly_db()
        with _anomaly_db_lock:
            for a in new_anomalies:
                existing = db.execute(
                    "SELECT id FROM anomalies WHERE session_key = ? AND metric = ? AND detected_at >= ?",
                    (a["session_key"], a["metric"], a["detected_at"] - window_24h),
                ).fetchone()
                if not existing:
                    db.execute(
                        "INSERT INTO anomalies (detected_at, session_key, metric, value, baseline, ratio, severity) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (
                            a["detected_at"],
                            a["session_key"],
                            a["metric"],
                            a["value"],
                            a["baseline"],
                            a["ratio"],
                            a["severity"],
                        ),
                    )
            db.commit()
    except Exception as _e:
        pass  # Non-critical — continue with in-memory results

    # ── Return stored anomalies from last 48h ──────────────────────────────
    try:
        db = _get_anomaly_db()
        cutoff = now_ts - (2 * window_24h)
        rows = db.execute(
            "SELECT * FROM anomalies WHERE detected_at >= ? ORDER BY detected_at DESC LIMIT 200",
            (cutoff,),
        ).fetchall()
        stored = [dict(r) for r in rows]
    except Exception:
        stored = []

    # Compute session frequency baseline for return value
    _days_in_window = max((now_ts - baseline_window_start) / 86400, 1.0)
    _avg_sessions_per_day = (
        len(baseline_sessions) / _days_in_window if len(baseline_sessions) > 0 else 0.0
    )

    return stored, {
        "baseline_cost_7d": round(avg_cost_7d, 6),
        "baseline_tokens_7d": round(avg_tokens_7d, 2),
        "baseline_error_rate_7d": round(err_baseline_rate, 4),
        "recent_error_rate_24h": round(recent_err_rate, 4),
        "baseline_sessions_per_day_7d": round(_avg_sessions_per_day, 2),
        "sessions_last_24h": len(recent_sessions_24h),
        "session_count_7d": len(baseline_sessions),
    }


_anomaly_detection_cache = {"data": None, "ts": 0}
_ANOMALY_CACHE_TTL = 60  # seconds

import sqlite3


def _compute_plugin_trend(plugin_name, plugin_daily_stats, days=14):
    """Return trend direction for a plugin: 'increasing', 'decreasing', or 'stable'.

    Compares average daily cost share of the last 7 days vs the prior 7 days.
    Closes vivekchand/clawmetry#201 (trend over time).
    """
    from datetime import date, timedelta
    today = date.today()
    recent_days = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(1, 8)]
    prior_days = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(8, 15)]

    def _avg_share(day_list):
        shares = []
        for d in day_list:
            day_data = plugin_daily_stats.get(d, {})
            day_total = sum(v.get("tokens", 0.0) for v in day_data.values()) or 1.0
            p_toks = day_data.get(plugin_name, {}).get("tokens", 0.0)
            if p_toks > 0:
                shares.append(p_toks / day_total * 100.0)
        return sum(shares) / len(shares) if shares else 0.0

    recent_avg = _avg_share(recent_days)
    prior_avg = _avg_share(prior_days)

    if prior_avg < 0.5:
        return "stable"
    delta_pct = (recent_avg - prior_avg) / prior_avg * 100.0
    if delta_pct > 20:
        return "increasing"
    if delta_pct < -20:
        return "decreasing"
    return "stable"


def _build_cost_comparison():
    """Build cost comparison data: actual spend vs alternative models."""
    # Alternative model pricing: (input $/1M, output $/1M, display name, provider)
    ALTERNATIVES = [
        ("gemini-2.0-flash",   0.10,  0.40,  "Gemini 2.0 Flash",     "Google"),
        ("gemini-1.5-flash",   0.075, 0.30,  "Gemini 1.5 Flash",     "Google"),
        ("gpt-4o-mini",        0.15,  0.60,  "GPT-4o Mini",          "OpenAI"),
        ("claude-haiku-3.5",   0.80,  4.00,  "Claude Haiku 3.5",     "Anthropic"),
        ("qwen-plus",          0.40,  1.20,  "Qwen Plus",            "Alibaba"),
        ("claude-sonnet-3.5",  3.00, 15.00,  "Claude Sonnet 3.5",    "Anthropic"),
        ("claude-opus-4",     15.00, 75.00,  "Claude Opus 4",        "Anthropic"),
    ]
    INPUT_RATIO = 0.60  # estimated 60% input, 40% output
    OUTPUT_RATIO = 0.40

    # Collect actual month tokens and cost from metrics store
    from datetime import datetime as _dt
    month_start = time.time() - 30 * 86400
    actual_tokens = 0
    actual_cost = 0.0
    actual_model = "unknown"
    model_token_map = {}  # model -> tokens

    with _metrics_lock:
        for entry in metrics_store.get("tokens", []):
            if entry.get("timestamp", 0) >= month_start:
                tok = float(entry.get("total", 0) or 0)
                actual_tokens += tok
                m = entry.get("model", "")
                if m:
                    model_token_map[m] = model_token_map.get(m, 0) + tok
        for entry in metrics_store.get("cost", []):
            if entry.get("timestamp", 0) >= month_start:
                actual_cost += float(entry.get("usd", 0) or 0)

    # If no cost data, estimate from tokens using current model pricing
    if actual_tokens > 0 and actual_cost == 0.0:
        usd_per_tok = _estimate_usd_per_token()
        actual_cost = actual_tokens * usd_per_tok

    # Determine dominant model
    if model_token_map:
        actual_model = max(model_token_map, key=lambda k: model_token_map[k])

    # Compute alternative costs for same token volume
    alternatives = []
    for alt_id, in_price, out_price, display_name, provider in ALTERNATIVES:
        if actual_tokens == 0:
            alt_cost = 0.0
        else:
            alt_cost = (
                actual_tokens * INPUT_RATIO * (in_price / 1_000_000)
                + actual_tokens * OUTPUT_RATIO * (out_price / 1_000_000)
            )
        if actual_cost > 0:
            savings_pct = round((actual_cost - alt_cost) / actual_cost * 100, 1)
            savings_usd = round(actual_cost - alt_cost, 4)
        else:
            savings_pct = 0.0
            savings_usd = 0.0
        alternatives.append({
            "model_id": alt_id,
            "display_name": display_name,
            "provider": provider,
            "estimated_cost": round(alt_cost, 4),
            "savings_usd": savings_usd,
            "savings_pct": savings_pct,
        })

    # Sort by estimated cost ascending
    alternatives.sort(key=lambda x: x["estimated_cost"])

    return {
        "actual": {
            "model": actual_model,
            "tokens": actual_tokens,
            "cost_usd": round(actual_cost, 4),
        },
        "alternatives": alternatives,
        "period": "30d",
    }


def _summarize_tool_input(name, inp):
    """Create a human-readable one-line summary of a tool call."""
    if name == "exec":
        return (inp.get("command") or str(inp))[:150]
    elif name in ("Read", "read"):
        return f"📖 {inp.get('file_path') or inp.get('path') or '?'}"
    elif name in ("Write", "write"):
        return f"✏️ {inp.get('file_path') or inp.get('path') or '?'}"
    elif name in ("Edit", "edit"):
        return f"🔧 {inp.get('file_path') or inp.get('path') or '?'}"
    elif name == "web_search":
        return f"[check] {inp.get('query', '?')}"
    elif name == "web_fetch":
        return f"🌐 {inp.get('url', '?')[:80]}"
    elif name == "browser":
        return f"🖥️ {inp.get('action', '?')}"
    elif name == "message":
        return f"💬 {inp.get('action', '?')} -> {inp.get('message', '')[:60]}"
    elif name == "tts":
        return f"🔊 {inp.get('text', '')[:60]}"
    else:
        return str(inp)[:120]


def _generic_channel_data(channel_key):
    """Generic channel data fetcher: scans session transcripts for channel metadata."""

    limit = request.args.get("limit", 50, type=int)
    today = datetime.now().strftime("%Y-%m-%d")

    messages = []
    today_in = 0
    today_out = 0

    # Scan log files for channel events
    log_dirs = _get_log_dirs()
    for ld in log_dirs:
        if not os.path.isdir(ld):
            continue
        for lf in sorted(glob.glob(os.path.join(ld, "*.log")), reverse=True)[:2]:
            try:
                _grep_lines = _grep_log_file(lf, f"messageChannel={channel_key}")
                for line in _grep_lines:
                    try:
                        obj = json.loads(line.strip())
                    except Exception:
                        continue
                    msg1 = obj.get("1", "") or obj.get("0", "")
                    ts = obj.get("time", "")
                    if f"messageChannel={channel_key}" in msg1:
                        direction = "out" if "deliver" in msg1.lower() else "in"
                        messages.append(
                            {
                                "timestamp": ts,
                                "direction": direction,
                                "sender": "User" if direction == "in" else "Clawd",
                                "text": msg1[:200],
                            }
                        )
                        if today and today in ts:
                            if direction == "in":
                                today_in += 1
                            else:
                                today_out += 1
            except Exception:
                pass

    # Also scan sessions.json for channel-tagged sessions
    for sessions_dir in [
        os.path.expanduser("~/.openclaw/agents/main/sessions"),
        os.path.expanduser("~/.clawdbot/agents/main/sessions"),
    ]:
        sessions_file = os.path.join(sessions_dir, "sessions.json")
        if not os.path.exists(sessions_file):
            continue
        try:
            with open(sessions_file) as f:
                sess_data = json.load(f)
            ch_sessions = [
                (sid, s)
                for sid, s in sess_data.items()
                if channel_key in sid.lower() and "sessionId" in s
            ]
            ch_sessions.sort(key=lambda x: x[1].get("updatedAt", 0), reverse=True)
            for sid_key, sinfo in ch_sessions[:5]:
                uuid = sinfo["sessionId"]
                sf = os.path.join(sessions_dir, uuid + ".jsonl")
                if not os.path.exists(sf):
                    continue
                try:
                    fsize = os.path.getsize(sf)
                    with open(sf, "r", errors="replace") as f:
                        if fsize > 65536:
                            f.seek(fsize - 65536)
                            f.readline()
                        for sline in f:
                            sline = sline.strip()
                            if not sline:
                                continue
                            try:
                                sd = json.loads(sline)
                            except Exception:
                                continue
                            sm = sd.get("message", {})
                            ts = sd.get("timestamp", "")
                            role = sm.get("role", "")
                            if role not in ("user", "assistant"):
                                continue
                            content = sm.get("content", "")
                            txt = ""
                            if isinstance(content, list):
                                for c in content:
                                    if isinstance(c, dict) and c.get("type") == "text":
                                        txt = c.get("text", "")
                                        break
                            elif isinstance(content, str):
                                txt = content
                            if (
                                not txt
                                or txt.startswith("System:")
                                or "HEARTBEAT" in txt
                            ):
                                continue
                            direction = "in" if role == "user" else "out"
                            messages.append(
                                {
                                    "timestamp": ts,
                                    "direction": direction,
                                    "sender": "User" if direction == "in" else "Clawd",
                                    "text": txt[:300],
                                }
                            )
                            if today and today in ts:
                                if direction == "in":
                                    today_in += 1
                                else:
                                    today_out += 1
                except Exception:
                    pass
        except Exception:
            pass

    # Deduplicate and sort
    seen = set()
    unique = []
    for m in messages:
        key = (m["timestamp"], m["direction"], m["text"][:50])
        if key not in seen:
            seen.add(key)
            unique.append(m)
    unique.sort(key=lambda x: x["timestamp"], reverse=True)

    status = "connected" if unique else "configured"
    return jsonify(
        {
            "messages": unique[:limit],
            "total": len(unique),
            "todayIn": today_in,
            "todayOut": today_out,
            "status": status,
        }
    )


# ── Security Threat Detection Engine ─────────────────────────────────────────
import re as _sec_re  # noqa: E402

# Built-in threat signatures: pattern matching on tool call details
_THREAT_SIGNATURES = [
    # Critical: Direct system compromise attempts
    {
        "id": "SEC-001",
        "severity": "critical",
        "description": "Reverse shell attempt via exec",
        "tool_types": ["EXEC"],
        "patterns": [
            r"(?:bash|sh|nc|ncat|netcat)\s.*-[ie]\s",
            r"/dev/tcp/",
            r"mkfifo\s+/tmp/",
            r"\bsocat\b.*\bexec\b",
            r"\btelnet\b.*\|.*\bsh\b",
        ],
    },
    {
        "id": "SEC-002",
        "severity": "critical",
        "description": "Credential/secret file access",
        "tool_types": ["READ", "EXEC"],
        "patterns": [
            r"(?:/etc/shadow|/etc/passwd)",
            r"\.ssh/(?:id_rsa|id_ed25519|authorized_keys)",
            r"\.aws/credentials",
            r"\.env(?:\b|$)",
            r"(?:\.kube|kubeconfig)",
            r"\.gnupg/private",
            r"\.netrc",
        ],
    },
    {
        "id": "SEC-003",
        "severity": "critical",
        "description": "Privilege escalation attempt",
        "tool_types": ["EXEC"],
        "patterns": [
            r"\bsudo\s+(?:su|bash|sh|chmod\s+[ugo]*s)",
            r"\bchmod\s+[0-7]*4[0-7]{2}\b",
            r"\bchmod\s+u\+s\b",
            r"\bpkexec\b",
            r"\bsu\s+-\s",
        ],
    },
    # High: Data exfiltration and suspicious network activity
    {
        "id": "SEC-004",
        "severity": "high",
        "description": "Potential data exfiltration via curl/wget POST",
        "tool_types": ["EXEC"],
        "patterns": [
            r"\bcurl\b.*\b-[dX]\b.*(?:POST|PUT)",
            r"\bcurl\b.*--data(?:-binary|-raw|-urlencode)?\b",
            r"\bwget\b.*--post-(?:data|file)\b",
        ],
    },
    {
        "id": "SEC-005",
        "severity": "high",
        "description": "SSH/SCP to unknown external host",
        "tool_types": ["EXEC"],
        "patterns": [
            r"\bssh\b\s+(?!localhost|127\.0\.0\.1|192\.168\.|10\.|172\.(?:1[6-9]|2[0-9]|3[01]))",
            r"\bscp\b\s+.*:",
            r"\brsync\b.*(?<!localhost):",
        ],
    },
    {
        "id": "SEC-006",
        "severity": "high",
        "description": "Cryptocurrency miner indicators",
        "tool_types": ["EXEC"],
        "patterns": [
            r"\bxmrig\b",
            r"\bstratum\+tcp\b",
            r"(?:mine|pool)\..*\.(?:com|net|org)",
            r"\bcpuminer\b",
        ],
    },
    # Medium: Suspicious but potentially legitimate
    {
        "id": "SEC-007",
        "severity": "medium",
        "description": "Destructive file operation (rm -rf on system paths)",
        "tool_types": ["EXEC"],
        "patterns": [
            r"\brm\s+(?:-[rfRv]+\s+)*(?:/(?:etc|usr|var|boot|lib|bin|sbin|opt|root)\b|/\s*$)",
            r"\brm\s+-[rfR]+\s+\*",
            r"\bdd\s+.*of=/dev/",
            r"\bmkfs\b",
        ],
    },
    {
        "id": "SEC-008",
        "severity": "medium",
        "description": "Package manager running as agent (supply chain risk)",
        "tool_types": ["EXEC"],
        "patterns": [
            r"\bpip\s+install\b.*(?:--index-url|--extra-index-url|--trusted-host)",
            r"\bnpm\s+install\b.*(?:--registry|--unsafe-perm)",
            r"\bcurl\b.*\|\s*(?:sudo\s+)?(?:bash|sh)\b",
            r"\bwget\b.*\|\s*(?:sudo\s+)?(?:bash|sh)\b",
        ],
    },
    {
        "id": "SEC-009",
        "severity": "medium",
        "description": "Firewall or security policy modification",
        "tool_types": ["EXEC"],
        "patterns": [
            r"\b(?:ufw|iptables|nftables|firewall-cmd)\b.*(?:allow|disable|delete|flush)",
            r"\bsetenforce\s+0\b",
            r"\bsystemctl\s+(?:stop|disable)\s+(?:firewalld|ufw|apparmor)",
        ],
    },
    {
        "id": "SEC-010",
        "severity": "medium",
        "description": "Cron/systemd persistence mechanism",
        "tool_types": ["EXEC", "WRITE"],
        "patterns": [
            r"\bcrontab\b",
            r"/etc/cron\.",
            r"/etc/systemd/system/.*\.service",
            r"systemctl\s+enable\b",
        ],
    },
    # Low: Informational security events
    {
        "id": "SEC-011",
        "severity": "low",
        "description": "Port scanning or network reconnaissance",
        "tool_types": ["EXEC"],
        "patterns": [
            r"\bnmap\b",
            r"\bmasscan\b",
            r"\bnetstat\s+-[tul]*p",
            r"\bss\s+-[tul]*p",
        ],
    },
    {
        "id": "SEC-012",
        "severity": "low",
        "description": "Large file download (potential payload)",
        "tool_types": ["EXEC"],
        "patterns": [
            r"\bwget\b\s+https?://(?!github\.com|pypi\.org|registry\.npmjs\.org|dl\.google\.com)",
            r"\bcurl\b\s+-[oOL]+\s+https?://(?!github\.com|pypi\.org|registry\.npmjs\.org)",
        ],
    },
    {
        "id": "SEC-013",
        "severity": "medium",
        "description": "Environment variable or API key extraction",
        "tool_types": ["EXEC", "READ"],
        "patterns": [
            r"\bprintenv\b",
            r"\benv\s*$",
            r"\bset\s*\|\s*grep\b.*(?:KEY|SECRET|TOKEN|PASS)",
            r"cat\s+.*(?:\.env|secrets|credentials)",
        ],
    },
    {
        "id": "SEC-014",
        "severity": "high",
        "description": "Process injection or debugging attachment",
        "tool_types": ["EXEC"],
        "patterns": [
            r"\bgdb\b.*-p\s*\d+",
            r"\bstrace\b.*-p\s*\d+",
            r"\bptrace\b",
            r"\bLD_PRELOAD\b",
            r"\b/proc/\d+/mem\b",
        ],
    },
    {
        "id": "SEC-015",
        "severity": "high",
        "description": "Browser tool accessing sensitive URLs",
        "tool_types": ["BROWSER", "SEARCH"],
        "patterns": [
            r"(?:bank|paypal|stripe\.com/dashboard|console\.aws|portal\.azure)",
            r"(?:admin|phpmyadmin|wp-admin|cpanel)",
            r"file:///etc/",
        ],
    },
]

# Compile patterns once
for _sig in _THREAT_SIGNATURES:
    _sig["_compiled"] = [
        _sec_re.compile(p, _sec_re.IGNORECASE) for p in _sig["patterns"]
    ]


def _scan_events_for_threats(events):
    """Scan brain-history events against threat signatures. Returns list of threat matches."""
    threats = []
    sessions_seen = set()
    sessions_with_threats = set()

    for ev in events:
        source = ev.get("source", "")
        sessions_seen.add(source)
        ev_type = ev.get("type", "")
        detail = ev.get("detail", "")
        if not detail:
            continue

        for sig in _THREAT_SIGNATURES:
            if ev_type not in sig["tool_types"]:
                continue
            for compiled in sig["_compiled"]:
                if compiled.search(detail):
                    sessions_with_threats.add(source)
                    threats.append(
                        {
                            "rule_id": sig["id"],
                            "severity": sig["severity"],
                            "description": sig["description"],
                            "detail": detail[:500],
                            "time": ev.get("time", ""),
                            "session": ev.get("sourceLabel", source),
                            "source": source,
                            "event_type": ev_type,
                        }
                    )
                    break  # One match per signature per event

    # Sort by severity then time
    sev_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    threats.sort(
        key=lambda t: (sev_order.get(t["severity"], 9), t.get("time", "") or ""),
        reverse=False,
    )
    threats.sort(key=lambda t: t.get("time", "") or "", reverse=True)

    counts = {
        "critical": sum(1 for t in threats if t["severity"] == "critical"),
        "high": sum(1 for t in threats if t["severity"] == "high"),
        "medium": sum(1 for t in threats if t["severity"] == "medium"),
        "low": sum(1 for t in threats if t["severity"] == "low"),
        "total": len(threats),
        "sessions_scanned": len(sessions_seen),
        "clean_sessions": len(sessions_seen - sessions_with_threats),
    }
    return threats, counts


# (bp_security routes /api/security/threats and /api/security/signatures
#  moved to routes/infra.py)


def _scan_security_posture():
    """Scan OpenClaw configuration for security misconfigurations.

    Returns a list of checks with pass/fail/warn status, remediation hints,
    and an overall A-F security score.

    Supports three config detection strategies:
    1. Local filesystem (native install)
    2. Docker container (reads config via docker exec/cp)
    3. Live gateway API (works for any deployment, including Hostinger/VPS Docker)
    """
    checks = []
    is_docker = False

    # --- Locate openclaw.json config ---
    config_data = None
    config_path = None

    # Strategy 1: Local filesystem
    for cf in [
        os.path.expanduser("~/.openclaw/openclaw.json"),
        os.path.expanduser("~/.clawdbot/openclaw.json"),
        os.path.expanduser("~/.clawdbot/clawdbot.json"),
    ]:
        try:
            with open(cf) as f:
                config_data = json.load(f)
                config_path = cf
                break
        except Exception:
            continue

    # Strategy 2: Docker container (if not found locally)
    if config_data is None:
        try:
            import subprocess as _sp

            # Find OpenClaw containers
            out = _sp.run(
                ["docker", "ps", "--format", "{{.ID}}\t{{.Names}}\t{{.Image}}"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if out.returncode == 0:
                for line in out.stdout.strip().splitlines():
                    parts = line.split("\t")
                    if len(parts) < 3:
                        continue
                    cid, name, image = parts[0], parts[1], parts[2]
                    if not any(
                        k in (name + image).lower()
                        for k in ["openclaw", "clawd", "claw"]
                    ):
                        continue
                    # Try to read config from inside container
                    for container_path in [
                        "/root/.openclaw/openclaw.json",
                        "/home/node/.openclaw/openclaw.json",
                        "/data/openclaw.json",
                        "/app/openclaw.json",
                    ]:
                        try:
                            cat_out = _sp.run(
                                ["docker", "exec", cid, "cat", container_path],
                                capture_output=True,
                                text=True,
                                timeout=8,
                            )
                            if cat_out.returncode == 0 and cat_out.stdout.strip():
                                config_data = json.loads(cat_out.stdout)
                                config_path = f"docker:{cid[:12]}:{container_path}"
                                is_docker = True
                                break
                        except Exception:
                            continue
                    if config_data:
                        break
        except (FileNotFoundError, Exception):
            pass  # Docker not available

    # Strategy 3: Live gateway API (works for any deployment including remote Docker)
    if config_data is None:
        try:
            gw_cfg = _load_gw_config()
            gw_url = gw_cfg.get("url", GATEWAY_URL)
            gw_token = gw_cfg.get("token", GATEWAY_TOKEN)
            if gw_url and gw_token:
                import urllib.request

                req = urllib.request.Request(
                    f"{gw_url}/api/config",
                    headers={
                        "Authorization": f"Bearer {gw_token}",
                        "Accept": "application/json",
                    },
                )
                with urllib.request.urlopen(req, timeout=8) as resp:
                    if resp.status == 200:
                        config_data = json.loads(resp.read().decode())
                        config_path = f"gateway:{gw_url}"
                        # Check if gateway reports Docker environment
                        runtime = config_data.get("runtime", {})
                        if runtime.get("container") or os.path.exists("/.dockerenv"):
                            is_docker = True
        except Exception:
            pass

    if config_data is None:
        return {
            "score": "U",
            "score_label": "Unknown",
            "score_color": "#64748b",
            "checks": [
                {
                    "id": "config_found",
                    "label": "Configuration file",
                    "status": "fail",
                    "detail": "No openclaw.json found (checked local files, Docker containers, and gateway API)",
                    "remediation": "Ensure OpenClaw is installed and configured. For Docker: verify the container is running. For remote: configure GATEWAY_URL and GATEWAY_TOKEN.",
                    "severity": "critical",
                    "weight": 20,
                }
            ],
            "passed": 0,
            "failed": 1,
            "warnings": 0,
            "total": 1,
        }

    # Config found — add pass check with source info
    source_label = (
        "local file"
        if not config_path.startswith(("docker:", "gateway:"))
        else (
            "Docker container" if config_path.startswith("docker:") else "gateway API"
        )
    )
    checks.append(
        {
            "id": "config_found",
            "label": "Configuration file",
            "status": "pass",
            "detail": f"Config loaded from {source_label} ({config_path})",
            "remediation": None,
            "severity": "critical",
            "weight": 20,
        }
    )

    # Docker-specific checks
    if is_docker:
        checks.append(
            {
                "id": "docker_isolation",
                "label": "Container isolation",
                "status": "pass",
                "detail": "OpenClaw is running inside a Docker container (network/filesystem isolation).",
                "remediation": None,
                "severity": "high",
                "weight": 5,
            }
        )

    gateway = config_data.get("gateway", {})
    plugins = config_data.get("plugins", {})

    # Check 1: Gateway auth token configured
    auth_token = (
        gateway.get("auth", {}).get("token")
        or gateway.get("authToken")
        or os.environ.get("OPENCLAW_AUTH_TOKEN")
    )
    if auth_token and len(str(auth_token)) >= 8:
        checks.append(
            {
                "id": "auth_enabled",
                "label": "Gateway authentication",
                "status": "pass",
                "detail": "Auth token is configured (length: {})".format(
                    len(str(auth_token))
                ),
                "remediation": None,
                "severity": "critical",
                "weight": 25,
            }
        )
    else:
        checks.append(
            {
                "id": "auth_enabled",
                "label": "Gateway authentication",
                "status": "fail",
                "detail": "No auth token configured. Anyone on the network can control your agent.",
                "remediation": "Set gateway.auth.token in openclaw.json to a strong random string (32+ chars).",
                "severity": "critical",
                "weight": 25,
            }
        )

    # Check 2: Auth token strength (not default/weak)
    weak_tokens = {
        "test",
        "password",
        "12345678",
        "changeme",
        "openclaw",
        "clawdbot",
        "default",
        "admin",
    }
    if auth_token:
        token_str = str(auth_token).lower()
        if token_str in weak_tokens or len(token_str) < 16:
            checks.append(
                {
                    "id": "auth_strength",
                    "label": "Auth token strength",
                    "status": "warn",
                    "detail": "Token is too short or uses a common/default value.",
                    "remediation": "Use a cryptographically random token: openssl rand -hex 32",
                    "severity": "high",
                    "weight": 15,
                }
            )
        else:
            checks.append(
                {
                    "id": "auth_strength",
                    "label": "Auth token strength",
                    "status": "pass",
                    "detail": "Token appears strong ({} chars)".format(len(token_str)),
                    "remediation": None,
                    "severity": "high",
                    "weight": 15,
                }
            )

    # Check 3: Gateway bind address (should be localhost, not 0.0.0.0)
    # In Docker, binding to 0.0.0.0 is expected (Docker manages port exposure)
    bind_host = gateway.get("host") or gateway.get("bind") or "127.0.0.1"
    if bind_host in ("0.0.0.0", "::") and is_docker:
        checks.append(
            {
                "id": "bind_address",
                "label": "Gateway bind address",
                "status": "pass",
                "detail": "Gateway binds to {} inside Docker container (Docker manages network exposure via port mapping).".format(
                    bind_host
                ),
                "remediation": None,
                "severity": "critical",
                "weight": 20,
            }
        )
    elif bind_host in ("0.0.0.0", "::"):
        checks.append(
            {
                "id": "bind_address",
                "label": "Gateway bind address",
                "status": "fail",
                "detail": "Gateway binds to {} (all interfaces). Exposed to the network.".format(
                    bind_host
                ),
                "remediation": 'Set gateway.host to "127.0.0.1" unless you need remote access. Use a reverse proxy with TLS for remote.',
                "severity": "critical",
                "weight": 20,
            }
        )
    else:
        checks.append(
            {
                "id": "bind_address",
                "label": "Gateway bind address",
                "status": "pass",
                "detail": "Gateway binds to {} (local only)".format(bind_host),
                "remediation": None,
                "severity": "critical",
                "weight": 20,
            }
        )

    # Check 4: Exec tool permissions
    tools_config = config_data.get("tools", {})
    exec_policy = tools_config.get("exec", {})
    exec_security = exec_policy.get("security") or exec_policy.get("mode") or "full"
    if exec_security == "full":
        checks.append(
            {
                "id": "exec_permissions",
                "label": "Exec tool permissions",
                "status": "warn",
                "detail": 'Exec security is "full" (unrestricted shell access).',
                "remediation": 'Consider "allowlist" mode with specific commands, or "deny" for high-risk environments.',
                "severity": "high",
                "weight": 10,
            }
        )
    elif exec_security == "deny":
        checks.append(
            {
                "id": "exec_permissions",
                "label": "Exec tool permissions",
                "status": "pass",
                "detail": "Exec tool is disabled (deny mode).",
                "remediation": None,
                "severity": "high",
                "weight": 10,
            }
        )
    else:
        checks.append(
            {
                "id": "exec_permissions",
                "label": "Exec tool permissions",
                "status": "pass",
                "detail": "Exec security mode: {}".format(exec_security),
                "remediation": None,
                "severity": "high",
                "weight": 10,
            }
        )

    # Check 5: TLS / HTTPS for gateway
    gw_port = gateway.get("port", 18789)
    gw_tls = gateway.get("tls", {})
    has_tls = bool(gw_tls.get("cert") or gw_tls.get("key") or gw_tls.get("enabled"))
    if has_tls:
        checks.append(
            {
                "id": "tls_enabled",
                "label": "TLS encryption",
                "status": "pass",
                "detail": "TLS is configured for the gateway.",
                "remediation": None,
                "severity": "high",
                "weight": 10,
            }
        )
    elif bind_host in ("0.0.0.0", "::") and is_docker:
        checks.append(
            {
                "id": "tls_enabled",
                "label": "TLS encryption",
                "status": "warn",
                "detail": "No TLS configured on gateway (Docker). TLS is typically handled by the hosting provider or reverse proxy.",
                "remediation": "Verify your hosting provider (Hostinger, etc.) or reverse proxy terminates TLS before reaching the container.",
                "severity": "high",
                "weight": 10,
            }
        )
    elif bind_host in ("0.0.0.0", "::"):
        checks.append(
            {
                "id": "tls_enabled",
                "label": "TLS encryption",
                "status": "fail",
                "detail": "No TLS configured and gateway is network-exposed. Traffic is unencrypted.",
                "remediation": "Configure gateway.tls.cert and gateway.tls.key, or use a reverse proxy (nginx/caddy) with TLS.",
                "severity": "high",
                "weight": 10,
            }
        )
    else:
        checks.append(
            {
                "id": "tls_enabled",
                "label": "TLS encryption",
                "status": "pass",
                "detail": "TLS not needed (gateway is localhost only).",
                "remediation": None,
                "severity": "high",
                "weight": 10,
            }
        )

    # Check 6: Plugin/channel security (telegram/discord tokens not in plaintext env)
    plugin_entries = plugins.get("entries", {})
    exposed_secrets = []
    for pname, pconf in plugin_entries.items():
        if isinstance(pconf, dict):
            for key in ["token", "apiKey", "api_key", "secret", "webhook_secret"]:
                val = pconf.get(key)
                if (
                    val
                    and isinstance(val, str)
                    and not val.startswith("$")
                    and not val.startswith("env:")
                ):
                    exposed_secrets.append("{}.{}".format(pname, key))
    if exposed_secrets:
        checks.append(
            {
                "id": "secrets_in_config",
                "label": "Secrets in config file",
                "status": "warn",
                "detail": "{} secret(s) stored as plaintext in config: {}".format(
                    len(exposed_secrets), ", ".join(exposed_secrets[:3])
                ),
                "remediation": 'Use environment variables instead. E.g., set TELEGRAM_TOKEN env var and reference as "$TELEGRAM_TOKEN" in config.',
                "severity": "medium",
                "weight": 5,
            }
        )
    else:
        checks.append(
            {
                "id": "secrets_in_config",
                "label": "Secrets in config file",
                "status": "pass",
                "detail": "No plaintext secrets detected in plugin config.",
                "remediation": None,
                "severity": "medium",
                "weight": 5,
            }
        )

    # Check 7: Workspace permissions (AGENTS.md, SOUL.md not world-readable)
    oc_home = os.path.expanduser("~/.openclaw")
    if os.path.isdir(oc_home):
        try:
            mode = oct(os.stat(oc_home).st_mode)[-3:]
            if mode[-1] != "0":  # world-readable
                checks.append(
                    {
                        "id": "workspace_perms",
                        "label": "Workspace permissions",
                        "status": "warn",
                        "detail": "OpenClaw home directory is world-readable (mode: {})".format(
                            mode
                        ),
                        "remediation": "Run: chmod 700 ~/.openclaw",
                        "severity": "medium",
                        "weight": 5,
                    }
                )
            else:
                checks.append(
                    {
                        "id": "workspace_perms",
                        "label": "Workspace permissions",
                        "status": "pass",
                        "detail": "Workspace directory permissions are restrictive (mode: {})".format(
                            mode
                        ),
                        "remediation": None,
                        "severity": "medium",
                        "weight": 5,
                    }
                )
        except Exception:
            checks.append(
                {
                    "id": "workspace_perms",
                    "label": "Workspace permissions",
                    "status": "warn",
                    "detail": "Could not check workspace permissions.",
                    "remediation": "Run: chmod 700 ~/.openclaw",
                    "severity": "medium",
                    "weight": 5,
                }
            )
    else:
        checks.append(
            {
                "id": "workspace_perms",
                "label": "Workspace permissions",
                "status": "pass",
                "detail": "Default workspace directory not found (custom location or containerized).",
                "remediation": None,
                "severity": "medium",
                "weight": 5,
            }
        )

    # Check 8: Node/remote access configuration
    nodes_config = config_data.get("nodes", {})
    auto_approve = nodes_config.get("autoApprove", False)
    if auto_approve:
        checks.append(
            {
                "id": "node_auto_approve",
                "label": "Node auto-approve",
                "status": "warn",
                "detail": "Nodes are auto-approved without manual review.",
                "remediation": "Set nodes.autoApprove to false so you review each device before granting access.",
                "severity": "medium",
                "weight": 5,
            }
        )
    else:
        checks.append(
            {
                "id": "node_auto_approve",
                "label": "Node auto-approve",
                "status": "pass",
                "detail": "Node pairing requires manual approval.",
                "remediation": None,
                "severity": "medium",
                "weight": 5,
            }
        )

    # Check 9: Elevated exec permissions
    elevated = tools_config.get("elevated", {}) or exec_policy.get("elevated", {})
    elevated_enabled = (
        elevated.get("enabled", False) if isinstance(elevated, dict) else bool(elevated)
    )
    if elevated_enabled:
        checks.append(
            {
                "id": "elevated_exec",
                "label": "Elevated (sudo) exec",
                "status": "warn",
                "detail": "Elevated/sudo exec is enabled. Agent can run commands as root.",
                "remediation": "Disable unless absolutely necessary. Use specific sudoers rules instead of blanket elevation.",
                "severity": "high",
                "weight": 10,
            }
        )
    else:
        checks.append(
            {
                "id": "elevated_exec",
                "label": "Elevated (sudo) exec",
                "status": "pass",
                "detail": "Elevated exec is disabled.",
                "remediation": None,
                "severity": "high",
                "weight": 10,
            }
        )

    # --- Calculate score ---
    total_weight = sum(c["weight"] for c in checks)
    earned = sum(c["weight"] for c in checks if c["status"] == "pass")
    # warnings get half credit
    earned += sum(c["weight"] * 0.5 for c in checks if c["status"] == "warn")
    pct = (earned / total_weight * 100) if total_weight > 0 else 0

    if pct >= 90:
        score, label, color = "A", "Excellent", "#22c55e"
    elif pct >= 75:
        score, label, color = "B", "Good", "#84cc16"
    elif pct >= 60:
        score, label, color = "C", "Fair", "#f59e0b"
    elif pct >= 40:
        score, label, color = "D", "Poor", "#f97316"
    else:
        score, label, color = "F", "Critical", "#ef4444"

    passed = sum(1 for c in checks if c["status"] == "pass")
    failed = sum(1 for c in checks if c["status"] == "fail")
    warnings = sum(1 for c in checks if c["status"] == "warn")

    return {
        "score": score,
        "score_label": label,
        "score_color": color,
        "score_pct": round(pct, 1),
        "checks": checks,
        "passed": passed,
        "failed": failed,
        "warnings": warnings,
        "total": len(checks),
        "config_path": config_path,
        "is_docker": is_docker,
        "scanned_at": datetime.now().isoformat(),
    }


# (bp_security /api/security/posture moved to routes/infra.py)


def _detect_channel_status():
    """Return list of configured channels with live connectivity status.

    Each entry: {'name': str, 'icon': str, 'status': 'connected'|'configured'|'unknown', 'detail': str}
    """
    CHANNEL_ICONS = {
        "telegram": "✈️",
        "discord": "🎮",
        "slack": "💬",
        "whatsapp": "📱",
        "signal": "🔒",
        "imessage": "🍎",
        "webchat": "🌐",
        "matrix": "🔢",
        "msteams": "🏢",
        "irc": "📡",
        "googlechat": "🔵",
        "mattermost": "⚡",
        "line": "💚",
        "nostr": "🟣",
        "twitch": "💜",
        "bluebubbles": "💙",
    }
    KNOWN_CHANNELS = (
        "telegram",
        "signal",
        "whatsapp",
        "discord",
        "webchat",
        "imessage",
        "irc",
        "slack",
        "googlechat",
        "bluebubbles",
        "matrix",
        "mattermost",
        "msteams",
        "line",
        "nostr",
        "twitch",
        "feishu",
        "synology-chat",
        "nextcloud-talk",
        "tlon",
        "zalo",
        "zalouser",
    )

    configured = []

    def _add(name):
        n = name.lower()
        if n in KNOWN_CHANNELS and n not in configured:
            configured.append(n)

    # Detect from gateway YAML config
    oc_dir = _get_openclaw_dir()
    yaml_candidates = [
        os.path.join(oc_dir, "gateway.yaml"),
        os.path.join(oc_dir, "gateway.yml"),
        os.path.expanduser("~/.clawdbot/gateway.yaml"),
        os.path.expanduser("~/.clawdbot/gateway.yml"),
    ]
    for yf in yaml_candidates:
        try:
            import yaml as _yaml

            with open(yf) as f:
                ydata = _yaml.safe_load(f)
            if not isinstance(ydata, dict):
                continue
            for section_key in ("channels", "plugins"):
                section = ydata.get(section_key, {})
                if isinstance(section, dict):
                    for name, conf in section.items():
                        if isinstance(conf, dict) and conf.get("enabled", True):
                            _add(name)
                        elif isinstance(conf, bool) and conf:
                            _add(name)
                elif isinstance(section, list):
                    for name in section:
                        _add(str(name))
            if configured:
                break
        except Exception:
            continue

    # Detect from JSON config files
    if not configured:
        for cf in [
            os.path.join(oc_dir, "openclaw.json"),
            os.path.expanduser("~/.clawdbot/openclaw.json"),
            os.path.expanduser("~/.clawdbot/moltbot.json"),
        ]:
            try:
                with open(cf) as f:
                    data = json.load(f)
                plugins = data.get("plugins", {}).get("entries", {})
                for name, pconf in plugins.items():
                    if isinstance(pconf, dict) and pconf.get("enabled"):
                        _add(name)
                channels = data.get("channels", {})
                if isinstance(channels, dict):
                    for name in channels:
                        _add(name)
                elif isinstance(channels, list):
                    for name in channels:
                        _add(str(name))
                if configured:
                    break
            except Exception:
                continue

    # Also check session data to infer active channels from recent activity
    if not configured:
        try:
            sessions = _get_sessions()
            for s in sessions:
                ch = s.get("channel") or s.get("channelName") or ""
                if ch:
                    _add(ch)
        except Exception:
            pass

    if not configured:
        return []

    # Filter to channels with data directories (evidence of real setup)
    DIR_EXEMPT = {
        "imessage",
        "irc",
        "googlechat",
        "slack",
        "webchat",
        "bluebubbles",
        "matrix",
        "mattermost",
        "msteams",
        "line",
        "nostr",
        "twitch",
        "feishu",
        "synology-chat",
        "nextcloud-talk",
        "tlon",
        "zalo",
        "zalouser",
    }
    cb_dir = os.path.expanduser("~/.clawdbot")
    active = []
    for ch in configured:
        if ch in DIR_EXEMPT:
            active.append(ch)
        elif any(os.path.isdir(os.path.join(d, ch)) for d in [oc_dir, cb_dir]):
            active.append(ch)
    if active:
        configured = active

    # Try to probe live connectivity for known channels
    results = []
    for ch in configured:
        icon = CHANNEL_ICONS.get(ch, "📡")
        status = "configured"
        detail = "Configured"

        if ch == "telegram":
            # Check if Telegram bot is reachable via getMe
            try:
                budget_cfg = _get_budget_config()
                tg_token = str(budget_cfg.get("telegram_bot_token", "")).strip()
                if not tg_token:
                    # Try reading directly from openclaw.json
                    for cf in [
                        os.path.join(oc_dir, "openclaw.json"),
                        os.path.expanduser("~/.clawdbot/openclaw.json"),
                    ]:
                        try:
                            with open(cf) as f:
                                d = json.load(f)
                            tg_token = str(
                                d.get("telegram", {}).get("token", "")
                                or d.get("plugins", {})
                                .get("entries", {})
                                .get("telegram", {})
                                .get("token", "")
                            ).strip()
                            if tg_token:
                                break
                        except Exception:
                            pass
                if tg_token:
                    import urllib.request as _ur

                    req = _ur.Request(
                        f"https://api.telegram.org/bot{tg_token}/getMe", method="GET"
                    )
                    req.add_header("User-Agent", "ClawMetry/1.0")
                    with _ur.urlopen(req, timeout=4) as resp:
                        data = json.loads(resp.read())
                    if data.get("ok"):
                        bot_name = data.get("result", {}).get("username", "")
                        status = "connected"
                        detail = f"@{bot_name}" if bot_name else "Connected"
                    else:
                        status = "configured"
                        detail = "Token invalid"
                else:
                    status = "configured"
                    detail = "No token configured"
            except Exception as e:
                err = str(e)
                if "timed out" in err or "timeout" in err:
                    status = "configured"
                    detail = "Timeout checking"
                else:
                    status = "configured"
                    detail = "Check failed"

        results.append(
            {
                "name": ch.capitalize(),
                "id": ch,
                "icon": icon,
                "status": status,
                "detail": detail,
            }
        )

    return results


# ── Rate Limit Monitor (GH#67) ────────────────────────────────────────────────

# Default API rate limits per provider (RPM = requests/min, TPM = tokens/min)
# Users can override these in openclaw.json under clawmetry.rate_limits
_DEFAULT_RATE_LIMITS = {
    'anthropic': {'rpm': 60,  'tpm_input': 80_000,    'tpm_output': 16_000,   'label': 'Anthropic (Claude)'},
    'google':    {'rpm': 360, 'tpm_input': 4_000_000,  'tpm_output': 400_000,  'label': 'Google (Gemini)'},
    'openai':    {'rpm': 60,  'tpm_input': 800_000,    'tpm_output': 100_000,  'label': 'OpenAI'},
    'bedrock':   {'rpm': 60,  'tpm_input': 80_000,     'tpm_output': 16_000,   'label': 'AWS Bedrock'},
    'openrouter':{'rpm': 200, 'tpm_input': 1_000_000,  'tpm_output': 200_000,  'label': 'OpenRouter'},
}


def _infer_provider(entry):
    """Infer API provider from entry metadata."""
    provider = (entry.get('provider') or '').lower()
    if provider and provider != 'unknown':
        return provider
    model = (entry.get('model') or '').lower()
    if any(k in model for k in ('claude', 'haiku', 'sonnet', 'opus')):
        return 'anthropic'
    if any(k in model for k in ('gemini', 'gemma')):
        return 'google'
    if any(k in model for k in ('gpt', 'o1-', 'o3-', 'o4-')):
        return 'openai'
    return 'other'


# (bp_config routes moved to routes/infra.py: /api/llmfit, /api/cost-optimizer,
#  /api/cost-optimization, /api/automation-analysis)


# (bp_nemoclaw handlers moved to routes/nemoclaw.py: /api/nemoclaw/status,
#  /api/nemoclaw/policy, /api/nemoclaw/approve, /api/nemoclaw/reject,
#  /api/nemoclaw/pending-approvals)


# ── Context Inspector (GH #9) ─────────────────────────────────────────


# ── Upgrade Impact Dashboard (GH #408) ────────────────────────────────────────


def _get_openclaw_version():
    """Detect current OpenClaw version from openclaw.json meta field or CLI."""
    # Try meta.lastTouchedVersion from openclaw.json
    oc_config = os.path.expanduser("~/.openclaw/openclaw.json")
    try:
        with open(oc_config) as f:
            data = json.load(f)
        v = (data.get("meta") or {}).get("lastTouchedVersion")
        if v:
            return str(v)
        # Also try wizard.lastRunVersion
        v = (data.get("wizard") or {}).get("lastRunVersion")
        if v:
            return str(v)
    except Exception:
        pass
    # Fallback: run openclaw --version
    try:
        import subprocess

        out = (
            subprocess.check_output(
                ["openclaw", "--version"], stderr=subprocess.STDOUT, timeout=5
            )
            .decode()
            .strip()
        )
        # Extract semver-like from output e.g. "openclaw/2026.3.13 ..."
        import re

        m = re.search(r"(\d{4}\.\d+\.\d+|\d+\.\d+\.\d+)", out)
        if m:
            return m.group(1)
    except Exception:
        pass
    return None


def _version_impact_db():
    """Get SQLite connection for version tracking, reusing history.db."""
    db_path = os.path.expanduser("~/.clawmetry/history.db")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    db = _sqlite3.connect(db_path, timeout=10)
    db.row_factory = _sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    db.executescript("""
        CREATE TABLE IF NOT EXISTS version_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            version TEXT NOT NULL,
            detected_at REAL NOT NULL,
            source TEXT DEFAULT 'openclaw.json'
        );
        CREATE INDEX IF NOT EXISTS idx_ve_ts ON version_events(detected_at);
    """)
    return db


def _record_version_if_changed(current_version):
    """Record a version event if the version has changed since last check."""
    if not current_version:
        return
    db = _version_impact_db()
    try:
        row = db.execute(
            "SELECT version FROM version_events ORDER BY detected_at DESC LIMIT 1"
        ).fetchone()
        if row and row["version"] == current_version:
            db.close()
            return
        db.execute(
            "INSERT INTO version_events (version, detected_at) VALUES (?, ?)",
            (current_version, time.time()),
        )
        db.commit()
    finally:
        db.close()


def _compute_session_stats_in_range(sessions_dir, start_ts, end_ts):
    """Compute aggregate session stats for sessions whose mtime falls in [start_ts, end_ts)."""
    stats = {
        "session_count": 0,
        "total_cost": 0.0,
        "total_tokens": 0,
        "error_count": 0,
        "tool_calls": 0,
        "duration_ms_total": 0,
        "duration_sessions": 0,
    }
    if not sessions_dir or not os.path.isdir(sessions_dir):
        return stats

    for fname in os.listdir(sessions_dir):
        if not fname.endswith(".jsonl"):
            continue
        fpath = os.path.join(sessions_dir, fname)
        try:
            mtime = os.path.getmtime(fpath)
            if not (start_ts <= mtime < end_ts):
                continue
        except OSError:
            continue

        stats["session_count"] += 1
        session_cost = 0.0
        session_tokens = 0
        session_errors = 0
        session_tools = 0
        first_ts = None
        last_ts = None

        try:
            with open(fpath, "r", errors="replace") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        ev = json.loads(line)
                    except Exception:
                        continue
                    ts_str = ev.get("timestamp", "")
                    if ts_str:
                        try:
                            ts_dt = datetime.fromisoformat(
                                ts_str.replace("Z", "+00:00")
                            )
                            ts_f = ts_dt.timestamp()
                            if first_ts is None or ts_f < first_ts:
                                first_ts = ts_f
                            if last_ts is None or ts_f > last_ts:
                                last_ts = ts_f
                        except Exception:
                            pass
                    ev_type = ev.get("type", "")
                    if ev_type == "message":
                        msg = ev.get("message", {})
                        role = msg.get("role", "")
                        if role == "assistant":
                            usage = msg.get("usage", {})
                            if isinstance(usage, dict):
                                cost_obj = usage.get("cost", {})
                                if isinstance(cost_obj, dict):
                                    session_cost += float(cost_obj.get("total", 0))
                                elif isinstance(cost_obj, (int, float)):
                                    session_cost += float(cost_obj)
                                tok_in = (
                                    usage.get("input", 0)
                                    or usage.get("inputTokens", 0)
                                    or 0
                                )
                                tok_out = (
                                    usage.get("output", 0)
                                    or usage.get("outputTokens", 0)
                                    or 0
                                )
                                session_tokens += int(tok_in) + int(tok_out)
                        if isinstance(msg.get("content"), list):
                            for part in msg["content"]:
                                if (
                                    isinstance(part, dict)
                                    and part.get("type") == "toolCall"
                                ):
                                    session_tools += 1
                    elif ev_type == "error":
                        session_errors += 1
        except Exception:
            pass

        stats["total_cost"] += session_cost
        stats["total_tokens"] += session_tokens
        stats["error_count"] += session_errors
        stats["tool_calls"] += session_tools
        if first_ts and last_ts and last_ts > first_ts:
            stats["duration_ms_total"] += int((last_ts - first_ts) * 1000)
            stats["duration_sessions"] += 1

    return stats


def _stats_to_summary(stats):
    n = max(stats["session_count"], 1)
    return {
        "session_count": stats["session_count"],
        "avg_cost": round(stats["total_cost"] / n, 6),
        "avg_tokens": int(stats["total_tokens"] / n),
        "avg_tool_calls": round(stats["tool_calls"] / n, 1),
        "error_rate": round(stats["error_count"] / n, 3),
        "avg_duration_ms": int(
            stats["duration_ms_total"] / max(stats["duration_sessions"], 1)
        ),
        "total_cost": round(stats["total_cost"], 6),
    }


def _compute_diff(before, after):
    """Compute percentage change between before and after summaries."""
    diff = {}
    for key in (
        "avg_cost",
        "avg_tokens",
        "avg_tool_calls",
        "error_rate",
        "avg_duration_ms",
    ):
        b = before.get(key, 0)
        a = after.get(key, 0)
        if b == 0:
            pct = None
        else:
            pct = round((a - b) / abs(b) * 100, 1)
        diff[key] = {"before": b, "after": a, "pct_change": pct}
    return diff


# (bp_version_impact handler moved to routes/meta.py: /api/version-impact)


# ── Trace Clustering (GH #406) ───────────────────────────────────────────────

_CLUSTER_TOOL_GROUPS = {
    "browsing": {"browser", "web_fetch", "web_search"},
    "coding": {"exec", "Read", "Write", "Edit", "process"},
    "messaging": {"message", "tts"},
    "pdf": {"pdf", "image"},
    "files": {"Read", "Write", "Edit"},
}

_CLUSTER_PATTERNS = [
    # (cluster_label, dominant_tools_required, min_fraction)
    ("browsing-heavy", {"browser", "web_fetch", "web_search"}, 0.4),
    ("code-heavy", {"exec", "Read", "Write", "Edit"}, 0.4),
    ("messaging", {"message", "tts"}, 0.3),
    ("doc-analysis", {"pdf", "image"}, 0.2),
    ("mixed-research", {"web_search", "exec", "Read"}, 0.15),
    ("cron-light", set(), 0.0),  # fallback for very short sessions
]


def _extract_session_fingerprint(fpath):
    """Extract tool call sequence, cost, tokens, error presence from a session JSONL file."""
    tools_seq = []
    cost = 0.0
    tokens = 0
    has_error = False
    first_ts = None
    last_ts = None

    try:
        with open(fpath, "r", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    ev = json.loads(line)
                except Exception:
                    continue

                ts_str = ev.get("timestamp", "")
                if ts_str:
                    try:
                        ts_f = datetime.fromisoformat(
                            ts_str.replace("Z", "+00:00")
                        ).timestamp()
                        if first_ts is None or ts_f < first_ts:
                            first_ts = ts_f
                        if last_ts is None or ts_f > last_ts:
                            last_ts = ts_f
                    except Exception:
                        pass

                ev_type = ev.get("type", "")
                if ev_type == "error":
                    has_error = True
                elif ev_type == "message":
                    msg = ev.get("message", {})
                    if msg.get("role") == "assistant":
                        usage = msg.get("usage", {})
                        if isinstance(usage, dict):
                            cost_obj = usage.get("cost", {})
                            if isinstance(cost_obj, dict):
                                cost += float(cost_obj.get("total", 0))
                            tok_in = (
                                usage.get("input", 0)
                                or usage.get("inputTokens", 0)
                                or 0
                            )
                            tok_out = (
                                usage.get("output", 0)
                                or usage.get("outputTokens", 0)
                                or 0
                            )
                            tokens += int(tok_in) + int(tok_out)
                        if isinstance(msg.get("content"), list):
                            for part in msg["content"]:
                                if (
                                    isinstance(part, dict)
                                    and part.get("type") == "toolCall"
                                ):
                                    tn = part.get("name", "")
                                    if tn:
                                        tools_seq.append(tn)
    except Exception:
        pass

    duration_ms = (
        int((last_ts - first_ts) * 1000)
        if (first_ts and last_ts and last_ts > first_ts)
        else 0
    )

    # Cost bucket (calibrated to typical agent session costs)
    if cost < 0.10:
        cost_bucket = "low"
    elif cost < 1.0:
        cost_bucket = "medium"
    else:
        cost_bucket = "high"

    return {
        "tools_seq": tools_seq,
        "tool_set": list(set(tools_seq)),
        "cost": round(cost, 6),
        "tokens": tokens,
        "has_error": has_error,
        "cost_bucket": cost_bucket,
        "duration_ms": duration_ms,
        "tool_count": len(tools_seq),
    }


def _assign_cluster_label(fp):
    """Assign a cluster label to a session based on its fingerprint."""
    tools = set(fp["tool_set"])
    n = fp["tool_count"]
    cost = fp["cost"]
    has_error = fp["has_error"]

    if n == 0:
        return "cron-light"

    # Score each cluster pattern by fraction of required tools present in session tool set
    best_label = "general"
    best_score = 0.0

    for label, required_tools, min_frac in _CLUSTER_PATTERNS:
        if not required_tools:
            continue
        # Fraction of required_tools that appear in the session (0..1)
        overlap = len(tools & required_tools)
        frac = overlap / len(required_tools) if required_tools else 0.0
        if frac >= min_frac and frac > best_score:
            best_score = frac
            best_label = label

    # Override only truly extreme outliers (cost > $5 or pure exec-only)
    if cost > 5.0:
        best_label = "expensive-outlier"

    # Suffix for error-heavy sessions
    if has_error and best_label not in ("expensive-outlier",):
        best_label += "+errors"

    return best_label


def _build_clusters(sessions_dir, limit=200):
    """Analyze recent sessions and return cluster groups."""
    if not sessions_dir or not os.path.isdir(sessions_dir):
        return {}

    files = sorted(
        [
            f
            for f in os.listdir(sessions_dir)
            if f.endswith(".jsonl") and "deleted" not in f
        ],
        key=lambda f: os.path.getmtime(os.path.join(sessions_dir, f)),
        reverse=True,
    )[:limit]

    clusters = {}  # label -> {sessions, total_cost, total_tokens, error_count, rep_session}

    for fname in files:
        fpath = os.path.join(sessions_dir, fname)
        sid = fname.replace(".jsonl", "")
        fp = _extract_session_fingerprint(fpath)
        label = _assign_cluster_label(fp)

        if label not in clusters:
            clusters[label] = {
                "label": label,
                "sessions": [],
                "total_cost": 0.0,
                "total_tokens": 0,
                "error_count": 0,
                "rep_session": None,
            }

        c = clusters[label]
        c["sessions"].append(
            {
                "id": sid,
                "cost": fp["cost"],
                "tokens": fp["tokens"],
                "tools": fp["tool_set"][:8],
                "has_error": fp["has_error"],
                "cost_bucket": fp["cost_bucket"],
                "duration_ms": fp["duration_ms"],
            }
        )
        c["total_cost"] += fp["cost"]
        c["total_tokens"] += fp["tokens"]
        if fp["has_error"]:
            c["error_count"] += 1
        # Representative session: highest cost/complexity
        if c["rep_session"] is None or fp["cost"] > c["rep_session"].get("cost", 0):
            c["rep_session"] = {
                "id": sid,
                "cost": fp["cost"],
                "tools": fp["tool_set"][:8],
            }

    # Compute summaries
    result = []
    for label, c in sorted(
        clusters.items(), key=lambda x: len(x[1]["sessions"]), reverse=True
    ):
        n = len(c["sessions"])
        result.append(
            {
                "label": label,
                "session_count": n,
                "avg_cost": round(c["total_cost"] / n, 6),
                "avg_tokens": int(c["total_tokens"] / n),
                "error_rate": round(c["error_count"] / n, 3),
                "rep_session": c["rep_session"],
                "sessions": c["sessions"][:20],  # cap for response size
            }
        )

    return result


# (bp_clusters handler moved to routes/meta.py: /api/clusters)


def _build_context_inspector_data():
    """Analyse workspace context files and session transcripts to produce the
    Context Inspector payload.

    Returns:
        {
          agents: [{sessionId, displayName, depth, parentId, contextFiles,
                    coverageScore, lintWarnings, spawnTaskSnippet, tokensIn}],
          lintWarnings: [{sessionId, message, severity}],
          summary: {totalAgents, avgCoverage, totalWarnings, contextFilesFound},
          contextFiles: [{name, sizeKB, exists}],
          generatedAt: ISO string,
        }
    """

    workspace = WORKSPACE or os.path.expanduser("~")
    sessions_dir = SESSIONS_DIR or os.path.expanduser(
        "~/.openclaw/agents/main/sessions"
    )

    # ── 1. Discover workspace context files ──────────────────────────────
    KNOWN_CONTEXT_FILES = [
        "SOUL.md",
        "AGENTS.md",
        "MEMORY.md",
        "USER.md",
        "IDENTITY.md",
        "HEARTBEAT.md",
        "CODING.md",
        "TOOLS.md",
    ]
    context_files_info = []
    existing_context_files = set()
    for fname in KNOWN_CONTEXT_FILES:
        fpath = os.path.join(workspace, fname)
        exists = os.path.isfile(fpath)
        size_kb = 0.0
        if exists:
            try:
                size_kb = round(os.path.getsize(fpath) / 1024, 1)
                existing_context_files.add(fname.lower())
            except OSError:
                pass
        context_files_info.append({"name": fname, "sizeKB": size_kb, "exists": exists})

    # Also check memory/ subdirectory
    mem_dir = os.path.join(workspace, "memory")
    memory_file_count = 0
    if os.path.isdir(mem_dir):
        try:
            memory_file_count = sum(1 for f in os.listdir(mem_dir) if f.endswith(".md"))
        except OSError:
            pass

    # ── 2. Parse sessions.json to build agent tree ──────────────────────
    index_path = os.path.join(sessions_dir, "sessions.json")
    sessions_raw = []
    try:
        with open(index_path) as f:
            idx = json.load(f)
            sessions_raw = list(idx.values()) if isinstance(idx, dict) else idx
    except (OSError, json.JSONDecodeError, TypeError):
        pass

    # Limit to 50 most recent to keep response fast
    sessions_raw = sorted(
        sessions_raw, key=lambda s: s.get("lastActiveMs", 0), reverse=True
    )[:50]

    # ── 3. For each session read the first few lines to extract spawn task ─
    def _extract_spawn_task(sess_id):
        """Return first user message text (truncated) — this is the task the agent got."""
        fpath = os.path.join(sessions_dir, sess_id + ".jsonl")
        if not os.path.isfile(fpath):
            return ""
        try:
            with open(fpath) as f:
                for line in f:
                    try:
                        obj = json.loads(line.strip())
                    except (json.JSONDecodeError, ValueError):
                        continue
                    if obj.get("type") == "message":
                        msg = obj.get("message", {})
                        if msg.get("role") == "user":
                            content = msg.get("content", "")
                            if isinstance(content, str):
                                return content[:300]
                            if isinstance(content, list):
                                for block in content:
                                    if (
                                        isinstance(block, dict)
                                        and block.get("type") == "text"
                                    ):
                                        return block.get("text", "")[:300]
        except OSError:
            pass
        return ""

    def _compute_coverage_score(sess, task_text):
        """Heuristic 0-100 coverage score.

        Checks:
        - Is there a task description at all?           +20
        - SOUL.md mentioned / present in workspace?     +20
        - AGENTS.md / MEMORY.md present?                +15 each
        - Task length ≥ 50 chars (enough context)?      +15
        - memory/ has recent files?                     +15
        """
        score = 0
        if task_text:
            score += 20
        txt_lower = task_text.lower()
        if "soul" in txt_lower or "soul.md" in existing_context_files:
            score += 20
        if "agents.md" in existing_context_files:
            score += 15
        if "memory.md" in existing_context_files:
            score += 15
        if len(task_text) >= 50:
            score += 15
        if memory_file_count > 0:
            score += 15
        return min(score, 100)

    def _lint_task(sess_id, sess, task_text):
        """Return list of lint warning strings for this agent's spawn context."""
        warnings = []
        txt_lower = task_text.lower()
        # Warn if task mentions user-specific data but no memory files
        user_data_hints = ["vivek", "user", "my ", "i'm", "password", "email", "phone"]
        if (
            any(h in txt_lower for h in user_data_hints)
            and "user.md" not in existing_context_files
        ):
            warnings.append(
                {
                    "severity": "warn",
                    "message": "Task references user data but USER.md not found in workspace",
                }
            )
        # Warn if sub-agent task is very short (context starvation risk)
        depth = sess.get("depth", 0) or 0
        if depth > 0 and len(task_text) < 50:
            warnings.append(
                {
                    "severity": "error",
                    "message": f"Sub-agent (depth {depth}) has a very short task — possible context starvation (<50 chars)",
                }
            )
        # Warn if no SOUL.md
        if "soul.md" not in existing_context_files:
            warnings.append(
                {
                    "severity": "warn",
                    "message": "SOUL.md not found — agent identity/persona context is missing",
                }
            )
        # Warn if no MEMORY.md
        if "memory.md" not in existing_context_files:
            warnings.append(
                {
                    "severity": "info",
                    "message": "MEMORY.md not found — long-term memory context unavailable",
                }
            )
        return warnings

    # ── 4. Build agent list ───────────────────────────────────────────────
    agents = []
    all_lint_warnings = []

    for sess in sessions_raw:
        sess_id = sess.get("sessionId") or sess.get("key", "")
        if not sess_id:
            continue

        display = sess.get("displayName") or sess_id[:16]
        depth = int(sess.get("depth", 0) or 0)
        parent_id = sess.get("spawnedBy") or sess.get("parentKey") or None
        tokens_in = sess.get("inputTokens") or sess.get("totalTokens", 0) or 0

        task_text = _extract_spawn_task(sess_id)
        coverage = _compute_coverage_score(sess, task_text)
        lint = _lint_task(sess_id, sess, task_text)

        # Collect files referenced in the task text (simple heuristic)
        referenced = [f for f in KNOWN_CONTEXT_FILES if f.lower() in task_text.lower()]
        missing = [f for f in referenced if f.lower() not in existing_context_files]

        agent_entry = {
            "sessionId": sess_id,
            "displayName": display,
            "depth": depth,
            "parentId": parent_id,
            "coverageScore": coverage,
            "lintWarnings": lint,
            "spawnTaskSnippet": task_text[:200] if task_text else "",
            "referencedContextFiles": referenced,
            "missingContextFiles": missing,
            "tokensIn": tokens_in,
            "lastActiveMs": sess.get("lastActiveMs", 0),
            "model": sess.get("model") or sess.get("modelRef", "unknown"),
        }
        agents.append(agent_entry)

        for w in lint:
            all_lint_warnings.append(
                {"sessionId": sess_id, "displayName": display, **w}
            )

    # Deduplicate global lint warnings (same message across sessions)
    seen_msgs = set()
    deduped_warnings = []
    for w in all_lint_warnings:
        key = w["message"]
        if key not in seen_msgs:
            seen_msgs.add(key)
            deduped_warnings.append(w)

    avg_coverage = (
        round(sum(a["coverageScore"] for a in agents) / len(agents), 1) if agents else 0
    )

    return {
        "agents": agents,
        "lintWarnings": deduped_warnings,
        "summary": {
            "totalAgents": len(agents),
            "avgCoverage": avg_coverage,
            "totalWarnings": len(all_lint_warnings),
            "contextFilesFound": len(existing_context_files),
            "memoryFileCount": memory_file_count,
        },
        "contextFiles": context_files_info,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
    }


# ── Data Helpers ────────────────────────────────────────────────────────


def _get_sessions():
    """Get sessions via gateway API first, file fallback."""
    now = time.time()
    if (
        _sessions_cache["data"] is not None
        and (now - _sessions_cache["ts"]) < _SESSIONS_CACHE_TTL
    ):
        return _sessions_cache["data"]

    # Try WebSocket RPC first
    api_data = _gw_ws_rpc("sessions.list")
    if api_data and "sessions" in api_data:
        sessions = []
        for s in api_data["sessions"][:30]:
            sessions.append(
                {
                    "sessionId": s.get("key", ""),
                    "key": s.get("key", "")[:12] + "...",
                    "displayName": s.get("displayName", s.get("key", "")[:20]),
                    "updatedAt": s.get("updatedAtMs", s.get("lastActiveMs", 0)),
                    "model": s.get("model", s.get("modelRef", "unknown")),
                    "channel": s.get("channel", "unknown"),
                    "totalTokens": s.get("totalTokens", 0),
                    "contextTokens": api_data.get("defaults", {}).get(
                        "contextTokens", 200000
                    ),
                    "kind": s.get("kind", "direct"),
                    "agent": s.get("agentId", "main"),
                }
            )
        _sessions_cache["data"] = sessions
        _sessions_cache["ts"] = now
        return sessions

    # File-based fallback
    return _get_sessions_from_files()


def _scan_session_aggregates(file_path):
    """Walk a session JSONL once and return (recent_model, total_tokens).

    Replaces the "file size as totalTokens" heuristic with an actual sum of
    `message.usage.totalTokens`. `recent_model` = the LAST model actually used
    in the session (from model_change / model-snapshot / message.model in
    file order), which is what the MODEL badge on Overview / Flow / Brain
    should display — those are live-activity surfaces that should reflect
    "what's running right now," not a historical aggregate.
    """
    total_tokens = 0
    last_seen_model = ""
    try:
        with open(file_path, "r", errors="replace") as fh:
            for raw in fh:
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    obj = json.loads(raw)
                except Exception:
                    continue
                t = obj.get("type", "")
                if t == "model_change":
                    m = obj.get("modelId") or obj.get("model") or ""
                    if m:
                        last_seen_model = m
                elif t == "custom" and obj.get("customType") == "model-snapshot":
                    d = obj.get("data", {}) or {}
                    m = d.get("modelId") or d.get("model") or ""
                    if m:
                        last_seen_model = m
                elif t == "message":
                    msg = obj.get("message", {}) or {}
                    if not isinstance(msg, dict):
                        continue
                    usage = msg.get("usage", {}) or {}
                    if isinstance(usage, dict):
                        total_tokens += int(usage.get("totalTokens", 0) or 0)
                    msg_model = msg.get("model") or ""
                    if msg_model:
                        last_seen_model = msg_model
    except Exception:
        pass
    return (last_seen_model or "unknown", total_tokens)


def _get_sessions_from_files():
    """Read active sessions from the session directory (file-based fallback)."""
    now = time.time()

    sessions = []
    try:
        base = SESSIONS_DIR or os.path.expanduser("~/.openclaw/agents/main/sessions")
        if not os.path.isdir(base):
            return sessions
        idx_files = sorted(
            [
                f
                for f in os.listdir(base)
                if f.endswith(".jsonl") and "deleted" not in f
            ],
            key=lambda f: os.path.getmtime(os.path.join(base, f)),
            reverse=True,
        )
        for fname in idx_files[:30]:
            fpath = os.path.join(base, fname)
            try:
                mtime = os.path.getmtime(fpath)
                with open(fpath) as f:
                    first = json.loads(f.readline())
                sid = fname.replace(".jsonl", "")
                # Single walk gets the session's most recent model + the real
                # token count. Previous code used file size as totalTokens,
                # which gave a bogus number proportional to JSONL bytes not
                # actual usage.
                model, total_tokens = _scan_session_aggregates(fpath)
                sessions.append(
                    {
                        "sessionId": sid,
                        "key": sid[:12] + "...",
                        "displayName": sid[:20],
                        "updatedAt": int(mtime * 1000),
                        "model": model,
                        "channel": "unknown",
                        "totalTokens": total_tokens,
                        "contextTokens": 200000,
                    }
                )
            except Exception:
                pass
    except Exception:
        pass
    _sessions_cache["data"] = sessions
    _sessions_cache["ts"] = now
    try:
        _ext_emit("session.snapshot", {"count": len(sessions)})
    except Exception:
        pass
    return sessions


def _safe_session_id(raw_id):
    sid = str(raw_id or "").strip()
    if not sid or "/" in sid or "\\" in sid or "\x00" in sid or ".." in sid:
        return ""
    return sid


def _resolve_session_stop_target(session_id):
    """Resolve stop target info for a session id/key."""
    sid = _safe_session_id(session_id)
    if not sid:
        return {"session_id": "", "jsonl_path": "", "stop_path": "", "pid": None}
    sessions_dir = SESSIONS_DIR or os.path.expanduser(
        "~/.openclaw/agents/main/sessions"
    )
    final_sid = sid
    pid = None

    direct_jsonl = os.path.join(sessions_dir, f"{sid}.jsonl")
    if os.path.exists(direct_jsonl):
        stop_path = os.path.join(sessions_dir, f"{sid}.stop")
        return {
            "session_id": sid,
            "jsonl_path": direct_jsonl,
            "stop_path": stop_path,
            "pid": None,
        }

    idx = os.path.join(sessions_dir, "sessions.json")
    try:
        with open(idx, "r") as f:
            mapping = json.load(f)
        if isinstance(mapping, dict):
            for key, meta in mapping.items():
                if not isinstance(meta, dict):
                    continue
                mapped_sid = str(meta.get("sessionId", "")).strip()
                if sid in (key, mapped_sid):
                    if mapped_sid:
                        final_sid = mapped_sid
                    pid_raw = meta.get("pid") or meta.get("processId")
                    try:
                        pid = int(pid_raw)
                    except Exception:
                        pid = None
                    break
    except Exception:
        pass

    jsonl_path = os.path.join(sessions_dir, f"{final_sid}.jsonl")
    stop_path = os.path.join(sessions_dir, f"{final_sid}.stop")
    return {
        "session_id": final_sid,
        "jsonl_path": jsonl_path,
        "stop_path": stop_path,
        "pid": pid,
    }


def _estimate_usd_per_token():
    """Estimate USD per token from recent metrics; fallback to conservative default."""
    now = time.time()
    start = now - 86400
    total_tokens = 0.0
    total_cost = 0.0
    with _metrics_lock:
        for t in metrics_store.get("tokens", []):
            if t.get("timestamp", 0) >= start:
                total_tokens += float(t.get("total", 0) or 0)
        for c in metrics_store.get("cost", []):
            if c.get("timestamp", 0) >= start:
                total_cost += float(c.get("usd", 0) or 0)
    if total_tokens > 0 and total_cost > 0:
        return total_cost / total_tokens
    return 3.0 / 1_000_000.0


def _json_ts_to_epoch(v):
    if not v:
        return None
    if isinstance(v, (int, float)):
        iv = float(v)
        if iv > 1e12:
            return iv / 1000.0
        return iv
    try:
        return datetime.fromisoformat(str(v).replace("Z", "+00:00")).timestamp()
    except Exception:
        return None


def _session_burn_stats(session_id):
    sid = _safe_session_id(session_id)
    if not sid:
        return {"tokensPerMin": 0, "projectedCostUsd": 0.0, "burnSeries": [0] * 10}
    sessions_dir = SESSIONS_DIR or os.path.expanduser(
        "~/.openclaw/agents/main/sessions"
    )
    fpath = os.path.join(sessions_dir, f"{sid}.jsonl")
    if not os.path.exists(fpath):
        return {"tokensPerMin": 0, "projectedCostUsd": 0.0, "burnSeries": [0] * 10}

    points = []
    try:
        with open(fpath, "r", errors="replace") as f:
            lines = list(deque(f, maxlen=1200))
        for line in lines:
            try:
                obj = json.loads(line.strip())
            except Exception:
                continue
            ts = _json_ts_to_epoch(
                obj.get("timestamp") or obj.get("time") or obj.get("created_at")
            )
            if not ts:
                continue
            tok = 0.0
            msg = obj.get("message", {}) if isinstance(obj.get("message"), dict) else {}
            usage = msg.get("usage", {}) if isinstance(msg.get("usage"), dict) else {}
            tok = float(
                usage.get("total_tokens")
                or usage.get("totalTokens")
                or usage.get("input_tokens", 0) + usage.get("output_tokens", 0)
                or 0
            )
            if tok <= 0:
                content = msg.get("content", [])
                text = ""
                if isinstance(content, str):
                    text = content
                elif isinstance(content, list):
                    parts = []
                    for b in content:
                        if isinstance(b, dict):
                            if b.get("type") == "text":
                                parts.append(str(b.get("text", "")))
                            elif b.get("type") == "thinking":
                                parts.append(str(b.get("thinking", "")))
                    text = " ".join(parts)
                if text:
                    tok = max(1.0, len(text) / 4.0)
            if tok > 0:
                points.append((ts, tok))
    except Exception:
        return {"tokensPerMin": 0, "projectedCostUsd": 0.0, "burnSeries": [0] * 10}

    if not points:
        return {"tokensPerMin": 0, "projectedCostUsd": 0.0, "burnSeries": [0] * 10}

    end_ts = max(ts for ts, _ in points)
    start_ts = end_ts - 600
    buckets = [0.0] * 10
    for ts, tok in points:
        if ts < start_ts:
            continue
        idx = int((ts - start_ts) // 60)
        if idx < 0:
            idx = 0
        if idx > 9:
            idx = 9
        buckets[idx] += tok

    recent = buckets[-5:] if len(buckets) >= 5 else buckets
    tokens_per_min = (sum(recent) / len(recent)) if recent else 0.0
    usd_per_token = _estimate_usd_per_token()
    projected_cost = tokens_per_min * 60.0 * usd_per_token
    return {
        "tokensPerMin": round(tokens_per_min, 2),
        "projectedCostUsd": round(projected_cost, 4),
        "burnSeries": [round(x, 2) for x in buckets],
    }


def _augment_sessions_with_burn(sessions):
    out = []
    for s in sessions or []:
        if not isinstance(s, dict):
            out.append(s)
            continue
        row = dict(s)
        sid = row.get("sessionId") or row.get("id") or row.get("key") or ""
        row["sessionId"] = sid
        row.update(_session_burn_stats(sid))
        out.append(row)
    return out


def _get_crons():
    """Get crons via gateway API first, file fallback."""
    # Try WebSocket RPC first
    api_data = _gw_ws_rpc("cron.list")
    if api_data and "jobs" in api_data:
        return api_data["jobs"]
    # File-based fallback
    return _get_crons_from_files()


def _get_crons_from_files():
    """Read crons from OpenClaw/moltbot state (file-based fallback)."""
    candidates = [
        os.path.expanduser("~/.openclaw/cron/jobs.json"),
        os.path.expanduser("~/.clawdbot/cron/jobs.json"),
    ]
    # Also check data dir if set via env
    data_dir = os.environ.get("OPENCLAW_DATA_DIR", "")
    if data_dir:
        candidates.insert(0, os.path.join(data_dir, "cron", "jobs.json"))
    for crons_file in candidates:
        try:
            if os.path.exists(crons_file):
                with open(crons_file) as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        return data
                    if isinstance(data, dict):
                        return data.get("jobs", list(data.values()))
        except Exception:
            pass
    return []


def _get_memory_files():
    """List workspace memory files."""
    result = []
    workspace = WORKSPACE or os.getcwd()
    memory_dir = MEMORY_DIR or os.path.join(workspace, "memory")

    for name in [
        "MEMORY.md",
        "SOUL.md",
        "IDENTITY.md",
        "USER.md",
        "AGENTS.md",
        "TOOLS.md",
        "HEARTBEAT.md",
    ]:
        path = os.path.join(workspace, name)
        if os.path.exists(path):
            result.append({"path": name, "size": os.path.getsize(path)})
    if os.path.isdir(memory_dir):
        pattern = os.path.join(memory_dir, "*.md")
        for f in sorted(glob.glob(pattern), reverse=True):
            name = "memory/" + os.path.basename(f)
            result.append({"path": name, "size": os.path.getsize(f)})
    return result


def _get_llmfit_recommendations():
    """Run llmfit to get local model recommendations for this hardware."""
    import shutil

    if not shutil.which("llmfit"):
        return {
            "available": False,
            "recommendations": [],
            "codingModels": [],
            "chatModels": [],
            "system": {},
        }

    try:
        # General recommendations
        result = subprocess.run(
            ["llmfit", "recommend", "--json", "--limit", "8"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        all_data = json.loads(result.stdout) if result.returncode == 0 else {}

        # Coding-specific
        coding_result = subprocess.run(
            ["llmfit", "recommend", "--json", "--use-case", "coding", "--limit", "5"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        coding_data = (
            json.loads(coding_result.stdout) if coding_result.returncode == 0 else {}
        )

        # Chat-specific
        chat_result = subprocess.run(
            ["llmfit", "recommend", "--json", "--use-case", "chat", "--limit", "5"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        chat_data = (
            json.loads(chat_result.stdout) if chat_result.returncode == 0 else {}
        )

        system_info = all_data.get("system", {})
        # Annotate: llmfit doesn't detect Apple Silicon GPU but Metal makes it 3-5x faster
        cpu = system_info.get("cpu_name", "")
        if (
            "apple" in cpu.lower()
            or "M1" in cpu
            or "M2" in cpu
            or "M3" in cpu
            or "M4" in cpu
        ):
            system_info["note"] = (
                "Apple Silicon -- Metal GPU available (3-5x faster than llmfit estimates)"
            )
            system_info["has_metal"] = True

        def _clean_model(m):
            # Extract short name from full HF path
            name = m.get("name", "")
            short = name.split("/")[-1] if "/" in name else name
            return {
                "name": short,
                "fullName": name,
                "provider": m.get("provider", ""),
                "category": m.get("category", ""),
                "useCase": m.get("use_case", ""),
                "estimatedTps": m.get("estimated_tps", 0),
                "memoryRequiredGb": m.get("memory_required_gb", 0),
                "parameterCount": m.get("parameter_count", ""),
                "contextLength": m.get("context_length", 0),
                "score": m.get("score", 0),
                "bestQuant": m.get("best_quant", ""),
                "fitLevel": m.get("fit_level", ""),
            }

        return {
            "available": True,
            "system": system_info,
            "recommendations": [
                _clean_model(m) for m in all_data.get("models", [])[:8]
            ],
            "codingModels": [
                _clean_model(m) for m in coding_data.get("models", [])[:5]
            ],
            "chatModels": [_clean_model(m) for m in chat_data.get("models", [])[:5]],
        }
    except Exception as e:
        return {
            "available": False,
            "error": str(e),
            "recommendations": [],
            "codingModels": [],
            "chatModels": [],
            "system": {},
        }


def _generate_savings_opportunities():
    """Identify tasks/crons that could use local models instead of expensive cloud models."""
    opportunities = []

    expensive_models = ["claude-sonnet", "claude-opus", "gpt-4", "o1", "o3"]

    # Check cron jobs
    try:
        crons = _get_crons()
        for cron in crons:
            model = cron.get("model", cron.get("modelRef", ""))
            name = cron.get("name", cron.get("label", "Unknown cron"))
            if any(m in (model or "").lower() for m in expensive_models):
                prompt = (cron.get("prompt", "") or "").lower()
                # Heuristic: heartbeat/status checks are simple tasks
                is_simple = any(
                    w in prompt
                    for w in [
                        "heartbeat",
                        "check",
                        "status",
                        "ping",
                        "monitor",
                        "health",
                    ]
                )
                if is_simple or not prompt:
                    opportunities.append(
                        {
                            "task": f"Cron: {name}",
                            "currentModel": model or "claude-sonnet-4-6",
                            "suggestedModel": "Qwen2.5-Coder-3B via Ollama",
                            "estimatedSavings": "~$1-3/month",
                            "reason": "Periodic checks and status tasks don't need frontier models",
                        }
                    )
    except Exception:
        pass

    # Always suggest heartbeat optimization
    opportunities.append(
        {
            "task": "Heartbeat cron (periodic checks)",
            "currentModel": "claude-sonnet-4-6",
            "suggestedModel": "Qwen3-4B via Ollama",
            "estimatedSavings": "~$2-5/month",
            "reason": "Simple periodic checks (email, calendar, weather) don't need frontier model",
        }
    )
    opportunities.append(
        {
            "task": "Summarization & formatting tasks",
            "currentModel": "claude-sonnet-4-6",
            "suggestedModel": "Llama-3.2-1B-Instruct via Ollama",
            "estimatedSavings": "~$1-2/month",
            "reason": "Text formatting, summarization, and simple rewrites work well locally",
        }
    )
    opportunities.append(
        {
            "task": "Sub-agent coding tasks",
            "currentModel": "claude-sonnet-4-6",
            "suggestedModel": "DeepSeek-Coder-V2-Lite via Ollama",
            "estimatedSavings": "~$3-8/month",
            "reason": "Small, well-scoped coding subtasks can run on local coding models",
        }
    )

    return opportunities[:6]


def _get_cost_summary():
    """Calculate cost summary from metrics store."""
    now = datetime.now(CET)
    today = now.strftime("%Y-%m-%d")
    week_start = (now - timedelta(days=7)).strftime("%Y-%m-%d")
    month_start = (now - timedelta(days=30)).strftime("%Y-%m-%d")

    costs = {"today": 0, "week": 0, "month": 0, "projected": 0}

    with _metrics_lock:
        for entry in metrics_store.get("cost", []):
            entry_date = datetime.fromtimestamp(
                entry.get("timestamp", 0) / 1000, CET
            ).strftime("%Y-%m-%d")
            entry_cost = entry.get("usd", 0)

            if entry_date == today:
                costs["today"] += entry_cost
            if entry_date >= week_start:
                costs["week"] += entry_cost
            if entry_date >= month_start:
                costs["month"] += entry_cost

    # Project monthly cost based on current daily average
    if costs["month"] > 0:
        days_in_period = min(
            30,
            (now - datetime.strptime(month_start, "%Y-%m-%d").replace(tzinfo=CET)).days
            + 1,
        )
        daily_avg = costs["month"] / days_in_period
        costs["projected"] = daily_avg * 30

    return costs


def _detect_ollama():
    """Detect Ollama installation using multiple strategies."""
    import shutil

    # Strategy 1: shutil.which (respects PATH)
    if shutil.which("ollama"):
        return True
    # Strategy 2: Check common installation paths
    common_paths = [
        "/opt/homebrew/bin/ollama",  # macOS Homebrew (Apple Silicon)
        "/usr/local/bin/ollama",  # macOS Homebrew (Intel) / Linux manual
        "/usr/bin/ollama",  # Linux package manager
        os.path.expanduser("~/.ollama/ollama"),  # Custom install
    ]
    # Windows paths
    if os.name == "nt":
        common_paths.extend(
            [
                os.path.expandvars(r"%LOCALAPPDATA%\Programs\Ollama\ollama.exe"),
                os.path.expandvars(r"%LOCALAPPDATA%\Ollama\ollama.exe"),
            ]
        )
    for p in common_paths:
        if os.path.isfile(p):
            return True
    # Strategy 3: Try HTTP ping (ollama might be running even if binary not in PATH)
    try:
        import urllib.request

        req = urllib.request.Request("http://localhost:11434/api/version", method="GET")
        with urllib.request.urlopen(req, timeout=2) as resp:
            if resp.status == 200:
                return True
    except Exception:
        pass
    return False


def _check_ollama_availability():
    """Check if Ollama is running and what models are available."""
    try:
        import requests

        response = requests.get("http://localhost:11434/api/tags", timeout=3)
        if response.status_code == 200:
            data = response.json()
            models = data.get("models", [])
            tool_capable_models = []

            for model in models:
                # Check if model supports tools (simplified check)
                model_name = model.get("name", "")
                # Common tool-capable models
                if any(
                    x in model_name.lower()
                    for x in ["llama3", "qwen", "gpt-oss", "mistral", "deepseek"]
                ):
                    tool_capable_models.append(model_name)

            return {
                "available": True,
                "count": len(tool_capable_models),
                "models": tool_capable_models[:10],  # Limit display
            }
    except Exception:
        pass

    # Fallback: use robust detection (binary found or HTTP reachable)
    if _detect_ollama():
        return {"available": True, "count": 0, "models": []}

    return {"available": False, "count": 0, "models": []}


def _generate_cost_recommendations(costs, local_models):
    """Generate cost optimization recommendations."""
    recommendations = []

    # High cost alerts
    if costs["today"] > 1.0:
        recommendations.append(
            {
                "title": "High Daily Cost",
                "description": f"Today's usage (${costs['today']:.3f}) is high. Consider using local models for routine tasks.",
                "priority": "high",
                "action": "Review recent expensive operations below",
            }
        )

    # Local model setup
    if not local_models["available"]:
        recommendations.append(
            {
                "title": "Install Local Models",
                "description": "Set up Ollama with local models to reduce API costs for formatting, simple lookups, and drafts.",
                "priority": "medium",
                "action": "curl -fsSL https://ollama.ai/install.sh | sh && ollama pull llama3.3",
            }
        )
    elif local_models["count"] < 2:
        recommendations.append(
            {
                "title": "Expand Local Model Selection",
                "description": "Add more local models for better task coverage and cost optimization.",
                "priority": "low",
                "action": "ollama pull qwen2.5-coder:32b",
            }
        )

    # Projected cost warning
    if costs["projected"] > 50.0:
        recommendations.append(
            {
                "title": "High Monthly Projection",
                "description": f"Projected monthly cost (${costs['projected']:.2f}) is high. Implement local model fallback urgently.",
                "priority": "high",
                "action": "Configure cost thresholds and local model routing",
            }
        )

    # Low-stakes task identification
    with _metrics_lock:
        recent_calls = metrics_store.get("tokens", [])[-100:]  # Last 100 calls
        high_cost_calls = [c for c in recent_calls if c.get("total", 0) > 10000]
        if len(high_cost_calls) > 20:
            recommendations.append(
                {
                    "title": "High Token Usage Detected",
                    "description": "Many recent calls use >10K tokens. Review if all require cloud models.",
                    "priority": "medium",
                    "action": "Implement task classification for local vs cloud routing",
                }
            )

    return recommendations


def _get_expensive_operations():
    """Get recent high-cost operations for analysis."""
    expensive_ops = []

    with _metrics_lock:
        # Combine cost and token data
        recent_tokens = metrics_store.get("tokens", [])[-50:]
        recent_costs = metrics_store.get("cost", [])[-50:]

        # Match tokens with costs by timestamp (approximate)
        for cost_entry in recent_costs:
            if cost_entry.get("usd", 0) > 0.01:  # Only show operations >$0.01
                timestamp = cost_entry.get("timestamp", 0)
                model = cost_entry.get("model", "unknown")
                cost = cost_entry.get("usd", 0)

                # Find matching token entry
                token_entry = None
                for t in recent_tokens:
                    if (
                        abs(t.get("timestamp", 0) - timestamp) < 5000
                    ):  # Within 5 seconds
                        if t.get("model", "") == model:
                            token_entry = t
                            break

                tokens = token_entry.get("total", 0) if token_entry else 0
                time_ago = datetime.fromtimestamp(timestamp / 1000, CET).strftime(
                    "%H:%M"
                )

                # Determine if this operation could be optimized
                can_optimize = False
                if tokens > 0:
                    # Simple heuristic: high token count with low complexity ratio might be local-model suitable
                    # This is a simplified check - in practice you'd analyze the actual request content
                    if (
                        tokens < 5000
                        and "gpt" not in model.lower()
                        and "simple" in model.lower()
                    ):
                        can_optimize = True

                expensive_ops.append(
                    {
                        "model": model,
                        "cost": cost,
                        "tokens": f"{tokens:,}" if tokens > 0 else "unknown",
                        "timeAgo": time_ago,
                        "canOptimize": can_optimize,
                    }
                )

    return sorted(expensive_ops, key=lambda x: x["cost"], reverse=True)[:10]


def _analyze_work_patterns():
    """Analyze recent work patterns from logs and metrics to detect repetitive tasks."""
    patterns = []

    try:
        # Analyze recent log files for repetitive patterns
        log_files = _get_recent_log_files(7)  # Last 7 days
        command_frequency = {}
        tool_frequency = {}
        error_patterns = {}

        for log_file in log_files:
            try:
                with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue

                        # Track tool usage patterns
                        if "tool_call" in line and "exec" in line:
                            try:
                                if '"command"' in line:
                                    # Extract command from tool call
                                    import re

                                    cmd_match = re.search(
                                        r'"command":\s*"([^"]+)"', line
                                    )
                                    if cmd_match:
                                        cmd = cmd_match.group(1).split()[
                                            0
                                        ]  # First word only
                                        command_frequency[cmd] = (
                                            command_frequency.get(cmd, 0) + 1
                                        )
                            except Exception:
                                pass

                        # Track tool names
                        for tool in [
                            "curl",
                            "git",
                            "npm",
                            "systemctl",
                            "grep",
                            "find",
                            "ls",
                        ]:
                            if tool in line and "tool_call" in line:
                                tool_frequency[tool] = tool_frequency.get(tool, 0) + 1

                        # Track common error patterns
                        if "error" in line.lower() or "failed" in line.lower():
                            for pattern in [
                                "connection failed",
                                "timeout",
                                "not found",
                                "permission denied",
                            ]:
                                if pattern in line.lower():
                                    error_patterns[pattern] = (
                                        error_patterns.get(pattern, 0) + 1
                                    )

            except Exception:
                continue

        # Generate pattern insights
        # High-frequency commands
        for cmd, count in command_frequency.items():
            if count >= 5:  # Used 5+ times in the past week
                confidence = min(90, count * 10)  # Higher frequency = higher confidence
                priority = "high" if count >= 15 else "medium" if count >= 10 else "low"
                patterns.append(
                    {
                        "title": f'Frequent "{cmd}" command usage',
                        "description": f'Command "{cmd}" has been used {count} times in the past week. This might be a candidate for automation.',
                        "frequency": f"{count} times/week",
                        "confidence": confidence,
                        "priority": priority,
                        "type": "command",
                        "target": cmd,
                    }
                )

        # Repeated error handling
        for error, count in error_patterns.items():
            if count >= 3:
                patterns.append(
                    {
                        "title": f"Recurring error: {error}",
                        "description": f"This error pattern has occurred {count} times. Consider adding error handling automation.",
                        "frequency": f"{count} occurrences/week",
                        "confidence": 75,
                        "priority": "medium",
                        "type": "error",
                        "target": error,
                    }
                )

        # Check for Mission Control task patterns (only if MC_URL is configured)
        if MC_URL:
            try:
                mc_response = subprocess.run(
                    ["curl", "-s", f"{MC_URL}/api/tasks"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if mc_response.returncode == 0:
                    mc_data = json.loads(mc_response.stdout)
                    if "tasks" in mc_data:
                        task_types = {}
                        for task in mc_data["tasks"]:
                            title = task.get("title", "").lower()
                            for keyword in [
                                "deploy",
                                "fix",
                                "update",
                                "build",
                                "test",
                                "backup",
                            ]:
                                if keyword in title:
                                    task_types[keyword] = task_types.get(keyword, 0) + 1
                        for task_type, count in task_types.items():
                            if count >= 3:
                                patterns.append(
                                    {
                                        "title": f"Frequent {task_type} tasks",
                                        "description": f'You have {count} tasks involving "{task_type}". This could be automated.',
                                        "frequency": f"{count} tasks",
                                        "confidence": 80,
                                        "priority": "medium",
                                        "type": "task",
                                        "target": task_type,
                                    }
                                )
            except Exception:
                pass

    except Exception as e:
        # Add a debug pattern if analysis fails
        patterns.append(
            {
                "title": "Pattern analysis limited",
                "description": f"Could not fully analyze patterns: {str(e)}",
                "frequency": "unknown",
                "confidence": 10,
                "priority": "low",
                "type": "debug",
                "target": "analysis",
            }
        )

    return sorted(
        patterns,
        key=lambda x: (
            x["priority"] == "high",
            x["priority"] == "medium",
            x["confidence"],
        ),
        reverse=True,
    )


def _generate_automation_suggestions(patterns):
    """Generate concrete automation suggestions based on detected patterns."""
    suggestions = []

    for pattern in patterns:
        if pattern["type"] == "command" and pattern["target"]:
            cmd = pattern["target"]

            # Command-specific automation suggestions
            if cmd in ["curl", "git", "systemctl"]:
                suggestions.append(
                    {
                        "title": f"Automate {cmd} monitoring",
                        "description": f"Create a cron job to monitor and auto-fix common {cmd} operations.",
                        "type": "cron",
                        "implementation": f"# Add to cron: */15 * * * * /path/to/auto-{cmd}.sh",
                        "impact": "Medium - reduces manual monitoring",
                        "effort": "Low - single script creation",
                    }
                )

            elif cmd in ["npm", "git"]:
                suggestions.append(
                    {
                        "title": f"{cmd.upper()} automation skill",
                        "description": f"Create a skill that automates common {cmd} workflows with error handling.",
                        "type": "skill",
                        "implementation": f"Skills/{cmd}-automation/SKILL.md - wrapper with retry logic",
                        "impact": "High - automates entire workflow",
                        "effort": "Medium - requires skill development",
                    }
                )

        elif pattern["type"] == "error":
            error_type = pattern["target"]
            suggestions.append(
                {
                    "title": f"Auto-recovery for {error_type}",
                    "description": f'Create monitoring that detects "{error_type}" errors and attempts automatic recovery.',
                    "type": "cron",
                    "implementation": f"*/10 * * * * /scripts/auto-recover-{error_type.replace(' ', '-')}.sh",
                    "impact": "High - prevents manual intervention",
                    "effort": "Medium - requires error detection logic",
                }
            )

        elif pattern["type"] == "task":
            task_type = pattern["target"]
            if task_type in ["deploy", "build", "update"]:
                suggestions.append(
                    {
                        "title": f"CI/CD pipeline for {task_type}",
                        "description": f"Automate {task_type} tasks with GitHub Actions or cron-based pipeline.",
                        "type": "automation",
                        "implementation": f".github/workflows/{task_type}.yml or cron-based pipeline",
                        "impact": "Very High - eliminates manual tasks",
                        "effort": "High - requires pipeline setup",
                    }
                )

    # Add some universal automation suggestions
    suggestions.extend(
        [
            {
                "title": "Health monitoring cron",
                "description": "Create a cron job that monitors system health and alerts on issues.",
                "type": "cron",
                "implementation": "0 */6 * * * /scripts/health-check.sh | logger",
                "impact": "Medium - proactive issue detection",
                "effort": "Low - single monitoring script",
            },
            {
                "title": "Log rotation automation",
                "description": "Automate log cleanup to prevent disk space issues.",
                "type": "cron",
                "implementation": '0 2 * * 0 find /var/log -type f -name "*.log" -mtime +7 -delete',
                "impact": "Medium - prevents disk space issues",
                "effort": "Very Low - single command cron",
            },
            {
                "title": "Backup verification skill",
                "description": "Create a skill that verifies backup integrity and reports status.",
                "type": "skill",
                "implementation": "Skills/backup-monitor/SKILL.md - checks backup health",
                "impact": "High - ensures backup reliability",
                "effort": "Medium - requires backup checking logic",
            },
        ]
    )

    # Remove duplicates and limit to top suggestions
    seen_titles = set()
    unique_suggestions = []
    for suggestion in suggestions:
        if suggestion["title"] not in seen_titles:
            seen_titles.add(suggestion["title"])
            unique_suggestions.append(suggestion)

    return unique_suggestions[:8]  # Limit to 8 suggestions max


def _get_recent_log_files(days=7):
    """Get list of recent log files to analyze."""
    log_files = []

    if LOG_DIR and os.path.isdir(LOG_DIR):
        # OpenClaw/Moltbot logs
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            log_file = os.path.join(LOG_DIR, f"moltbot-{date}.log")
            if os.path.isfile(log_file):
                log_files.append(log_file)

    # Also check journalctl if available
    try:
        result = subprocess.run(
            [
                "journalctl",
                "--user",
                "-u",
                "moltbot-gateway",
                "--since",
                f"{days} days ago",
                "--no-pager",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            # Create temporary file with journalctl output for analysis
            import tempfile

            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".log", delete=False
            ) as f:
                f.write(result.stdout)
                log_files.append(f.name)
    except Exception:
        pass

    return log_files


# ── CLI Entry Point ─────────────────────────────────────────────────────

BANNER = r"""
   ____ _                 __  __      _
  / ___| | __ ___      __|  \/  | ___| |_ _ __ _   _
 | |   | |/ _` \ \ /\ / /| |\/| |/ _ \ __| '__| | | |
 | |___| | (_| |\ V  V / | |  | |  __/ |_| |  | |_| |
  \____|_|\__,_| \_/\_/  |_|  |_|\___|\__|_|   \__, |
                                                |___/
                          v{version}

  [ClawMetry]  See your agent think

  Tabs: Overview ? ? Usage ? Sessions ? Crons ? Logs
        Memory ? ? Transcripts ? ? Flow
  Flow: Click nodes: ? Automation Advisor ? ? Cost Optimizer ? ?? Time Travel
"""

ARCHITECTURE_OVERVIEW = """\
🦞 ClawMetry {version} -- See your agent think.

  ┌─────────────────────┐              ┌─────────────────────┐              ┌─────────────────────┐
  │  🤖                 │  READS FILES │  🦞                 │  SHOWS YOU  │  📊                 │
  │  Your OpenClaw      │ ──────────->  │                     │ ──────────->  │                     │
  │  agents             │              │  ClawMetry          │              │  Your browser       │
  │                     │              │  Parses logs +      │              │  localhost:{port}   │
  │  Running normally.  │              │  sessions.          │              │  Live dashboard     │
  │  Nothing changes.   │              │  Serves dashboard.  │              │                     │
  └─────────────────────┘              └─────────────────────┘              └─────────────────────┘

  Runs locally on the same machine as OpenClaw. Your data never leaves your box.
  Docs: https://clawmetry.com/how-it-works
"""

HELP_TEXT = """\
🦞 ClawMetry {version} -- See your agent think.

Usage: clawmetry [command] [options]

Commands:
  start          Start ClawMetry as a background service (auto-starts on login)
  stop           Stop the background service
  restart        Restart the background service
  status         Show service status, port, and uptime
  uninstall      Remove the background service

Options:
  --port <port>        Port to listen on (default: 8900)
  --host <host>        Host to bind to (default: 127.0.0.1)
  --workspace <path>   OpenClaw workspace path (auto-detected)
  --name <name>        Your name in Flow visualization
  --no-debug           Disable Flask debug/auto-reload
  -v, --version        Show version
  -h, --help           Show this help

Examples:
  clawmetry start              Start as background service on port 8900
  clawmetry start --port 9000  Start on custom port
  clawmetry status             Check if running

Docs: https://docs.clawmetry.com
"""

PID_FILE = "/tmp/clawmetry.pid"
LAUNCHD_LABEL = "com.clawmetry.dashboard"
LAUNCHD_PLIST = os.path.expanduser(f"~/Library/LaunchAgents/{LAUNCHD_LABEL}.plist")
SYSTEMD_SERVICE = os.path.expanduser(
    "~/.config/systemd/user/clawmetry-dashboard.service"
)

# Sync daemon uses separate service names
SYNC_LAUNCHD_LABEL = "com.clawmetry.sync"
SYNC_LAUNCHD_PLIST = os.path.expanduser(
    f"~/Library/LaunchAgents/{SYNC_LAUNCHD_LABEL}.plist"
)
SYNC_SYSTEMD_SERVICE = os.path.expanduser(
    "~/.config/systemd/user/clawmetry-sync.service"
)


# ---------------------------------------------------------------------------
# Daemon helpers
# ---------------------------------------------------------------------------


def _get_script_path():
    """Return absolute path to the clawmetry executable / this script."""
    import shutil

    exe = shutil.which("clawmetry")
    if exe:
        return os.path.realpath(exe)
    return os.path.realpath(sys.argv[0])


def _write_pid(pid):
    with open(PID_FILE, "w") as f:
        f.write(str(pid))


def _read_pid():
    try:
        with open(PID_FILE) as f:
            return int(f.read().strip())
    except Exception:
        return None


def _is_pid_running(pid):
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, PermissionError):
        return False


def _is_macos():
    return sys.platform == "darwin"


def _is_linux():
    return sys.platform.startswith("linux")


def _launchd_running():
    import subprocess

    try:
        result = subprocess.run(
            ["launchctl", "list", LAUNCHD_LABEL], capture_output=True, text=True
        )
        return result.returncode == 0
    except Exception:
        return False


def _systemd_running():
    import subprocess

    try:
        result = subprocess.run(
            ["systemctl", "--user", "is-active", "--quiet", "clawmetry"],
            capture_output=True,
        )
        return result.returncode == 0
    except Exception:
        return False


def _service_running():
    if _is_macos():
        return _launchd_running()
    elif _is_linux():
        return _systemd_running()
    # Fallback: check PID file
    pid = _read_pid()
    return pid is not None and _is_pid_running(pid)


def _get_service_pid():
    """Try to get running PID from launchd/systemd/pid file."""
    if _is_macos():
        import subprocess

        try:
            result = subprocess.run(
                ["launchctl", "list", LAUNCHD_LABEL], capture_output=True, text=True
            )
            for line in result.stdout.splitlines():
                line = line.strip()
                if line and not line.startswith('"') and "\t" in line:
                    parts = line.split("\t")
                    if len(parts) >= 1:
                        try:
                            return int(parts[0])
                        except ValueError:
                            pass
        except Exception:
            pass
    elif _is_linux():
        import subprocess

        try:
            result = subprocess.run(
                ["systemctl", "--user", "show", "clawmetry", "--property=MainPID"],
                capture_output=True,
                text=True,
            )
            for line in result.stdout.splitlines():
                if line.startswith("MainPID="):
                    pid = int(line.split("=", 1)[1].strip())
                    return pid if pid > 0 else None
        except Exception:
            pass
    return _read_pid()


def _get_uptime_str(pid):
    try:
        import subprocess

        if _is_macos():
            result = subprocess.run(
                ["ps", "-o", "etime=", "-p", str(pid)], capture_output=True, text=True
            )
            return result.stdout.strip() or "?"
        else:
            result = subprocess.run(
                ["ps", "-o", "etime=", "-p", str(pid)], capture_output=True, text=True
            )
            return result.stdout.strip() or "?"
    except Exception:
        return "?"


def _read_cloud_token():
    cfg_path = os.path.expanduser("~/.openclaw/openclaw.json")
    try:
        with open(cfg_path) as f:
            data = json.load(f)
        return data.get("clawmetry", {}).get("cloudToken")
    except Exception:
        return None


def _write_cloud_token(token):
    cfg_path = os.path.expanduser("~/.openclaw/openclaw.json")
    try:
        with open(cfg_path) as f:
            data = json.load(f)
    except Exception:
        data = {}
    if "clawmetry" not in data:
        data["clawmetry"] = {}
    data["clawmetry"]["cloudToken"] = token
    os.makedirs(os.path.dirname(cfg_path), exist_ok=True)
    with open(cfg_path, "w") as f:
        json.dump(data, f, indent=2)


def _build_plist(python_exe, script_path, port, host, log_path="/tmp/clawmetry.log"):
    extra = []
    if host != "127.0.0.1":
        extra += ["<string>--host</string>", f"<string>{host}</string>"]
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{LAUNCHD_LABEL}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{python_exe}</string>
        <string>{script_path}</string>
        <string>--no-debug</string>
        <string>--port</string>
        <string>{port}</string>
        {"".join(extra)}
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>{log_path}</string>
    <key>StandardErrorPath</key>
    <string>{log_path}</string>
</dict>
</plist>
"""


def _build_systemd_unit(python_exe, script_path, port, host):
    extra = f" --host {host}" if host != "127.0.0.1" else ""
    return f"""[Unit]
Description=ClawMetry Dashboard
After=network.target

[Service]
ExecStart={python_exe} {script_path} --no-debug --port {port}{extra}
Restart=always
RestartSec=5

[Install]
WantedBy=default.target
"""


# ---------------------------------------------------------------------------
# CLI subcommands
# ---------------------------------------------------------------------------


def cmd_start(args):
    """Start ClawMetry as a background daemon."""
    import subprocess

    port = args.port
    host = args.host
    python_exe = sys.executable
    script_path = _get_script_path()

    try:
        print(ARCHITECTURE_OVERVIEW.format(version=__version__, port=port))
    except (ValueError, OSError):
        pass
    try:
        print("Starting dashboard...")
    except (ValueError, OSError):
        pass

    # Before loading daemon: if port is busy, only kill if it's our own stale process
    import socket as _socket

    _s = _socket.socket(_socket.AF_INET, _socket.SOCK_STREAM)
    _port_busy = _s.connect_ex(("127.0.0.1", port)) == 0
    _s.close()
    if _port_busy:
        _old_pid = None
        try:
            with open(PID_FILE) as _pf:
                _old_pid = int(_pf.read().strip())
        except Exception:
            pass
        if _old_pid:
            try:
                import subprocess as _sp

                _r = _sp.run(
                    ["ps", "-p", str(_old_pid), "-o", "command="],
                    capture_output=True,
                    text=True,
                )
                _cmd = _r.stdout
                if "clawmetry" in _cmd or "dashboard.py" in _cmd:
                    import signal as _signal

                    os.kill(_old_pid, _signal.SIGTERM)
                    import time as _time

                    _time.sleep(1)
                else:
                    print(
                        f"❌ Port {port} is in use by another application. Choose a different port with --port."
                    )
                    sys.exit(1)
            except Exception:
                pass
        else:
            print(
                f"❌ Port {port} is in use by another application. Choose a different port with --port."
            )
            sys.exit(1)

    if _is_macos():
        # Write plist
        plist_content = _build_plist(python_exe, script_path, port, host)
        os.makedirs(os.path.dirname(LAUNCHD_PLIST), exist_ok=True)
        with open(LAUNCHD_PLIST, "w") as f:
            f.write(plist_content)

        # Unload if already loaded (ignore errors)
        subprocess.run(["launchctl", "unload", LAUNCHD_PLIST], capture_output=True)
        result = subprocess.run(
            ["launchctl", "load", LAUNCHD_PLIST], capture_output=True, text=True
        )
        if result.returncode != 0:
            print(f"❌ Failed to load service: {result.stderr.strip()}")
            sys.exit(1)

        import time

        time.sleep(1)
        if _launchd_running():
            print(f"[ok] ClawMetry started  ->  http://localhost:{port}")
            print("   Auto-starts on login - logs: /tmp/clawmetry.log")
            print("   Stop with: clawmetry stop")
        else:
            print(
                "[warn]  Service loaded but may still be starting. Check: clawmetry status"
            )

    elif _is_linux():
        unit_content = _build_systemd_unit(python_exe, script_path, port, host)
        os.makedirs(os.path.dirname(SYSTEMD_SERVICE), exist_ok=True)
        with open(SYSTEMD_SERVICE, "w") as f:
            f.write(unit_content)

        subprocess.run(["systemctl", "--user", "daemon-reload"], capture_output=True)
        subprocess.run(
            ["systemctl", "--user", "enable", "clawmetry"], capture_output=True
        )
        result = subprocess.run(
            _systemctl_cmd("restart"), capture_output=True, text=True
        )
        if result.returncode != 0:
            print(f"❌ Failed to start service: {result.stderr.strip()}")
            sys.exit(1)

        import time

        time.sleep(1)
        if _systemd_running():
            print(f"[ok] ClawMetry started  ->  http://localhost:{port}")
            print("   Auto-starts on login - logs: journalctl --user -u clawmetry -f")
            print("   Stop with: clawmetry stop")
        else:
            print(
                "[warn]  Service started but may still be initialising. Check: clawmetry status"
            )
    else:
        print(
            "[warn]  Daemon mode not supported on this OS. Running in foreground instead."
        )
        _run_server(args)


def cmd_stop(args):
    """Stop the ClawMetry dashboard daemon (sync keeps running)."""
    import subprocess

    if _is_macos():
        if not os.path.exists(LAUNCHD_PLIST):
            # Try legacy service name
            _old = os.path.expanduser("~/Library/LaunchAgents/com.clawmetry.plist")
            if os.path.exists(_old):
                subprocess.run(["launchctl", "unload", _old], capture_output=True)
                print("[ok] Stopped legacy ClawMetry service.")
            else:
                print(
                    "ℹ️  No service file found. ClawMetry may not be installed as a service."
                )
            sys.exit(0)
        result = subprocess.run(
            ["launchctl", "unload", LAUNCHD_PLIST], capture_output=True, text=True
        )
        if result.returncode == 0:
            print("[ok] ClawMetry dashboard stopped. Cloud sync still running.")
        else:
            print(
                f"[warn]  {result.stderr.strip() or 'Service may already be stopped.'}"
            )
    elif _is_linux():
        # Stop dashboard service (new or legacy name)
        result = subprocess.run(
            _systemctl_cmd("stop", "clawmetry-dashboard"),
            capture_output=True,
            text=True,
        )
        # Also try legacy name
        subprocess.run(_systemctl_cmd("stop", "clawmetry"), capture_output=True)
        if result.returncode == 0:
            print("[ok] ClawMetry dashboard stopped. Cloud sync still running.")
        else:
            print(
                f"[warn]  {result.stderr.strip() or 'Service may already be stopped.'}"
            )
    else:
        # Fallback: kill via PID file
        pid = _read_pid()
        if pid and _is_pid_running(pid):
            os.kill(pid, 15)  # SIGTERM
            print(f"[ok] Sent SIGTERM to PID {pid}.")
        else:
            print("ℹ️  No running ClawMetry process found.")


def cmd_restart(args):
    """Restart the ClawMetry dashboard daemon (sync keeps running)."""
    import subprocess

    if _is_macos():
        if not os.path.exists(LAUNCHD_PLIST):
            print("ℹ️  No service installed. Use: clawmetry start")
            sys.exit(1)
        subprocess.run(["launchctl", "unload", LAUNCHD_PLIST], capture_output=True)
        result = subprocess.run(
            ["launchctl", "load", LAUNCHD_PLIST], capture_output=True, text=True
        )
        if result.returncode == 0:
            print("[ok] ClawMetry restarted.")
        else:
            print(f"❌ {result.stderr.strip()}")
            sys.exit(1)
    elif _is_linux():
        result = subprocess.run(
            _systemctl_cmd("restart"), capture_output=True, text=True
        )
        if result.returncode == 0:
            print("[ok] ClawMetry restarted.")
        else:
            print(f"❌ {result.stderr.strip()}")
            sys.exit(1)
    else:
        print("[warn]  Daemon mode not supported on this OS.")


def cmd_status(args):
    """Show ClawMetry service status."""
    running = _service_running()
    pid = _get_service_pid() if running else None
    uptime = _get_uptime_str(pid) if pid else "--"
    token = _read_cloud_token()
    port = args.port

    if _is_macos():
        svc_type = "launchd"
    elif _is_linux():
        svc_type = "systemd"
    else:
        svc_type = "process"

    status_icon = "[ok] Running" if running else "❌ Stopped"
    cloud_status = "[ok] Connected" if token else "❌ Not connected"

    print(f"""
🦞 ClawMetry Status

  Service:   {status_icon} ({svc_type})
  Port:      {port}
  PID:       {pid or "--"}
  Uptime:    {uptime}
  URL:       http://localhost:{port}
  Version:   {__version__}
  Cloud:     {cloud_status}
""")


def _kill_all_sync_procs():
    """Kill ALL running clawmetry sync processes (any platform)."""
    import subprocess
    import signal

    try:
        subprocess.run(
            ["pkill", "-9", "-f", "clawmetry.*sync"], capture_output=True, timeout=5
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    pid = _read_pid()
    if pid and _is_pid_running(pid):
        try:
            os.kill(pid, signal.SIGKILL)
        except OSError:
            pass


def _is_root():
    return os.geteuid() == 0 if hasattr(os, "geteuid") else False


def _systemctl_cmd(action, service="clawmetry-dashboard"):
    """Build systemctl command -- omit --user when running as root."""
    if _is_root():
        return ["systemctl", action, service] if service else ["systemctl", action]
    return (
        ["systemctl", "--user", action, service]
        if service
        else ["systemctl", "--user", action]
    )


def _start_daemon_background():
    """Start sync daemon as a background process (fallback for non-service setups)."""
    import subprocess
    import pathlib as _pl

    proc = subprocess.Popen(
        [sys.executable, "-m", "clawmetry.sync"],
        stdout=open(os.devnull, "w"),
        stderr=open(os.devnull, "w"),
        start_new_session=True,
    )
    pid_file = _pl.Path.home() / ".clawmetry" / "sync.pid"
    pid_file.parent.mkdir(parents=True, exist_ok=True)
    pid_file.write_text(str(proc.pid))
    print(f"  Sync daemon started (background, PID {proc.pid})")


def _is_sync_running():
    """Check if any clawmetry sync process is running."""
    import subprocess

    try:
        r = subprocess.run(
            ["pgrep", "-f", "clawmetry.*sync"], capture_output=True, timeout=3
        )
        return r.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _ensure_systemd_service():
    """Create systemd service file if needed (supports root and user mode)."""
    import pathlib as _pl
    import subprocess

    if _is_root():
        svc_dir = _pl.Path("/etc/systemd/system")
    else:
        svc_dir = _pl.Path.home() / ".config" / "systemd" / "user"
    svc_path = svc_dir / "clawmetry-sync.service"
    svc_dir.mkdir(parents=True, exist_ok=True)
    python_bin = sys.executable
    home = _pl.Path.home()
    target = "multi-user.target" if _is_root() else "default.target"
    svc_content = f"""[Unit]
Description=ClawMetry Sync Daemon
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart={python_bin} -m clawmetry.sync
Restart=always
RestartSec=10
Environment=HOME={home}

[Install]
WantedBy={target}
"""
    svc_path.write_text(svc_content)
    if _is_root():
        subprocess.run(["systemctl", "daemon-reload"], capture_output=True)
        subprocess.run(["systemctl", "enable", "clawmetry-sync"], capture_output=True)
    else:
        subprocess.run(["systemctl", "--user", "daemon-reload"], capture_output=True)
        subprocess.run(
            ["systemctl", "--user", "enable", "clawmetry-sync"], capture_output=True
        )


def cmd_connect(args):
    """Connect to ClawMetry Cloud."""
    import subprocess
    import pathlib

    print()
    print("ClawMetry Cloud Connect")
    print()

    # Stop existing sync processes (but leave dashboard running)
    _kill_all_sync_procs()
    if _is_macos() and os.path.exists(SYNC_LAUNCHD_PLIST):
        subprocess.run(["launchctl", "unload", SYNC_LAUNCHD_PLIST], capture_output=True)
    elif _is_linux():
        subprocess.run(_systemctl_cmd("stop", "clawmetry-sync"), capture_output=True)
    print("  Stopped existing sync daemon")

    token = getattr(args, "key", None) or ""
    if not token:
        print("  1. Go to: https://clawmetry.com/connect")
        print("  2. Sign in and copy your API key (starts with cm_)")
        print()
        try:
            token = input("  Paste your API key: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nCancelled.")
            sys.exit(0)

    if not token.startswith("cm_"):
        print("Invalid key -- must start with cm_")
        sys.exit(1)

    # Clear old sync state so new account gets full initial sync
    state_file = pathlib.Path.home() / ".clawmetry" / "sync-state.json"
    if state_file.exists():
        state_file.unlink()
        print("  Cleared previous sync state")

    _write_cloud_token(token)
    print()
    print(
        f"  Connected! View your fleet at: https://app.clawmetry.com/fleet/?token={token}"
    )
    print()

    # Install + start service
    if _is_macos():
        if os.path.exists(LAUNCHD_PLIST):
            subprocess.run(["launchctl", "load", LAUNCHD_PLIST], capture_output=True)
            subprocess.run(["launchctl", "start", LAUNCHD_LABEL], capture_output=True)
            print("  Sync daemon started (launchd)")
        else:
            try:
                cmd_start(type("Args", (), {})())
            except SystemExit:
                _start_daemon_background()
    elif _is_linux():
        _ensure_systemd_service()
        subprocess.run(_systemctl_cmd("restart", "clawmetry-sync"), capture_output=True)
        print("  Sync daemon started (systemd)")
    else:
        _start_daemon_background()

    # Verify after 3s
    import time

    time.sleep(3)
    if _is_sync_running():
        print("  Sync daemon is running -- your node will appear in ~60 seconds")
    else:
        # Last resort: start in background
        print("  Service didn't start, trying background mode...")
        _start_daemon_background()
        time.sleep(2)
        if _is_sync_running():
            print("  Sync daemon is running -- your node will appear in ~60 seconds")
        else:
            print("  Could not start daemon. Check: cat ~/.clawmetry/sync.log")


def cmd_uninstall(args):
    """Stop and remove the ClawMetry service."""
    import subprocess

    print("🗑️  Uninstalling ClawMetry service...")

    if _is_macos():
        if os.path.exists(LAUNCHD_PLIST):
            subprocess.run(["launchctl", "unload", LAUNCHD_PLIST], capture_output=True)
            os.remove(LAUNCHD_PLIST)
            print(f"  Removed: {LAUNCHD_PLIST}")
        else:
            print("  No launchd service found.")
    elif _is_linux():
        subprocess.run(_systemctl_cmd("stop"), capture_output=True)
        subprocess.run(_systemctl_cmd("disable"), capture_output=True)
        if os.path.exists(SYSTEMD_SERVICE):
            os.remove(SYSTEMD_SERVICE)
            print(f"  Removed: {SYSTEMD_SERVICE}")
        subprocess.run(["systemctl", "--user", "daemon-reload"], capture_output=True)
    else:
        print("  Daemon mode not supported on this OS.")

    # Remove PID file if present
    if os.path.exists(PID_FILE):
        os.remove(PID_FILE)

    print("[ok] ClawMetry service removed.")


def _run_server(args):
    import sys as _sys

    # Windows: guard against closed/detached stdout/stderr before Flask or
    # click try to use them.  Two scenarios cause problems:
    #
    #   1. pythonw.exe / Start-Process / GUI launchers close the standard
    #      handles at startup.  click._winconsole._is_console() calls
    #      f.fileno() on sys.stdout, which raises:
    #        ValueError: I/O operation on closed file
    #      (reported in GH#264, reproduced on Python 3.11 Windows 10/11)
    #
    #   2. Normal CMD terminal with CP1252 encoding: box-drawing chars and
    #      emoji crash with UnicodeEncodeError.
    #
    # Strategy:
    #   a) Try fileno() first — if it raises, the stream is closed/detached;
    #      replace with a devnull sink so click/Flask banners never crash.
    #   b) If the stream is open, reconfigure() to UTF-8 (Python 3.7+).
    if _sys.platform == "win32":
        import io as _io

        for _attr in ("stdout", "stderr"):
            _stream = getattr(_sys, _attr, None)
            if _stream is None:
                # Completely absent — attach a null sink
                try:
                    setattr(_sys, _attr, open(os.devnull, "w", encoding="utf-8"))
                except OSError:
                    setattr(_sys, _attr, _io.StringIO())
                continue
            try:
                _stream.fileno()  # raises ValueError/OSError when closed
            except (AttributeError, ValueError, OSError):
                # Stream is closed or has no real file descriptor.
                # Replace with devnull so click._winconsole never calls fileno().
                try:
                    setattr(_sys, _attr, open(os.devnull, "w", encoding="utf-8"))
                except OSError:
                    setattr(_sys, _attr, _io.StringIO())
                continue
            # Stream is open — reconfigure to UTF-8 to avoid CP1252 issues.
            try:
                _stream.reconfigure(encoding="utf-8", errors="replace")
            except (AttributeError, Exception):
                pass
    """Start the Flask server (foreground). Called by foreground mode and cmd_start on unsupported OS."""
    detect_config(args)
    _load_gw_config()

    # Parse --monitor-service flags
    global EXTRA_SERVICES, MC_URL
    for svc_spec in args.monitor_service:
        if ":" in svc_spec:
            name, port_str = svc_spec.rsplit(":", 1)
            try:
                EXTRA_SERVICES.append(
                    {"name": name.strip(), "port": int(port_str.strip())}
                )
            except ValueError:
                print(
                    f"[warn]  Invalid --monitor-service format: {svc_spec} (expected NAME:PORT)"
                )
        else:
            print(
                f"[warn]  Invalid --monitor-service format: {svc_spec} (expected NAME:PORT)"
            )

    if args.mc_url:
        MC_URL = args.mc_url
    elif not MC_URL:
        MC_URL = os.environ.get("MC_URL", "")

    global METRICS_FILE
    if args.metrics_file:
        METRICS_FILE = os.path.expanduser(args.metrics_file)
    elif os.environ.get("OPENCLAW_METRICS_FILE"):
        METRICS_FILE = os.path.expanduser(os.environ["OPENCLAW_METRICS_FILE"])

    global SSE_MAX_SECONDS, MAX_LOG_STREAM_CLIENTS, MAX_HEALTH_STREAM_CLIENTS
    sse_max = args.sse_max_seconds
    if sse_max is None:
        env_sse_max = os.environ.get("OPENCLAW_SSE_MAX_SECONDS", "").strip()
        if env_sse_max:
            try:
                sse_max = int(env_sse_max)
            except ValueError:
                sse_max = None
    if sse_max is not None and sse_max > 0:
        SSE_MAX_SECONDS = sse_max
    MAX_LOG_STREAM_CLIENTS = max(1, args.max_log_stream_clients)
    MAX_HEALTH_STREAM_CLIENTS = max(1, args.max_health_stream_clients)

    _load_metrics_from_disk()
    _start_metrics_flush_thread()

    global _history_db, _history_collector
    if _HAS_HISTORY:
        history_db_path = os.environ.get("CLAWMETRY_HISTORY_DB", None)
        _history_db = HistoryDB(history_db_path)
        _history_collector = HistoryCollector(_history_db, _gw_invoke)
        _history_collector.start()

    global FLEET_API_KEY, FLEET_DB_PATH
    if args.fleet_api_key:
        FLEET_API_KEY = args.fleet_api_key
    if args.fleet_db:
        FLEET_DB_PATH = os.path.expanduser(args.fleet_db)
    try:
        _fleet_init_db()
    except Exception as _fleet_exc:
        db_path = _fleet_db_path()
        print(
            f"\n[clawmetry] ERROR: Could not initialise fleet database at {db_path!r}\n"
            f"  Cause: {_fleet_exc}\n\n"
            f"  Try one of:\n"
            f"    1. Ensure the directory exists and is writable:\n"
            f"         mkdir -p ~/.clawmetry && chmod 700 ~/.clawmetry\n"
            f"    2. Specify a custom path:\n"
            f"         clawmetry --fleet-db /tmp/fleet.db\n",
            flush=True,
        )
        raise SystemExit(1) from _fleet_exc
    _budget_init_db()
    _detect_heartbeat_interval()
    _start_fleet_maintenance_thread()
    _start_budget_monitor_thread()

    try:
        print(BANNER.format(version=__version__))
        print(f"  Workspace:  {WORKSPACE}")
        print(f"  Sessions:   {SESSIONS_DIR}")
        print(f"  Logs:       {LOG_DIR}")
        print(f"  Metrics:    {_metrics_file_path()}")
        if _HAS_OTEL_PROTO:
            print("  OTLP:       [ok] Ready (opentelemetry-proto installed)")
        print(f"  User:       {USER_NAME}")
        print(
            f"  Mode:       {'[dev]  Dev (auto-reload ON)' if args.debug else '[prod] Prod (auto-reload OFF)'}"
        )
        print(
            f"  SSE Limits: {SSE_MAX_SECONDS}s max duration - logs {MAX_LOG_STREAM_CLIENTS} clients - health {MAX_HEALTH_STREAM_CLIENTS} clients"
        )
        print(f"  Fleet DB:   {_fleet_db_path()}")
        print(
            f"  Fleet Auth: {'Enabled (key set)' if FLEET_API_KEY else 'Open (no key - set --fleet-api-key for production)'}"
        )
        if _HAS_HISTORY and _history_db:
            print(f"  History DB: {_history_db.db_path}")
        else:
            print("  History:    Disabled (history.py not found)")
        print()

        warnings, tips = validate_configuration()
        if warnings or tips:
            print("[check] Configuration Check:")
            for warning in warnings:
                print(f"  {warning}")
            for tip in tips:
                print(f"  {tip}")
            print()
            if warnings:
                print(
                    "[tip] The dashboard will work with limited functionality. See tips above for full experience."
                )
                print()
    except (ValueError, OSError):
        pass  # stdout may be closed/redirected on Windows

    try:
        local_ip = get_local_ip()
        public_ip = get_public_ip()
        print(f"  -> http://localhost:{args.port}")
        if local_ip != "127.0.0.1":
            print(f"  -> http://{local_ip}:{args.port}  (LAN)")
        if public_ip and public_ip != local_ip:
            print(
                f"  -> http://{public_ip}:{args.port}  (Public - ensure port is open)"
            )
        if _HAS_OTEL_PROTO:
            print(f"  -> OTLP endpoint: http://{local_ip}:{args.port}/v1/metrics")
        print()
        # Cloud nudge — only if not already connected
        _already_connected = bool(
            os.environ.get("CLAWMETRY_API_KEY") or os.environ.get("CLAWMETRY_NODE_ID")
        )
        if not _already_connected:
            _sep = "  -" if sys.platform == "win32" else "  \u2500"
            print(_sep * 25)
            print()
            _globe = "[web]" if sys.platform == "win32" else "🌐 "
            _lock = "[enc]" if sys.platform == "win32" else "🔒 "
            print(
                f"  {_globe}  Run clawmetry connect to access your dashboard from app.clawmetry.com"
            )
            print(
                f"      {_lock}  E2E encrypted with your local key — decrypted in the dashboard on demand."
            )
            print("      Free 7-day trial · no credit card required.")
            print()

        if not args.debug:
            print("  Tip: run as background service with: clawmetry start")
            print()
    except (ValueError, OSError):
        pass  # stdout may be closed/redirected on Windows

    if args.debug:
        # Dev mode -- use Flask's reloader
        app.run(
            host=args.host, port=args.port, debug=True, use_reloader=True, threaded=True
        )
    else:
        # Prod mode -- use Waitress (no WSGI warning, multi-threaded)
        try:
            from waitress import serve

            # threads=32: each SSE stream (health, logs, flow) holds a thread
            # for its lifetime. Older 8-thread default got exhausted after 2-3
            # tab reloads, leaving new requests stuck pending. 32 gives ~10 tabs
            # of headroom before queuing.
            serve(app, host=args.host, port=args.port, threads=32, channel_timeout=120)
        except ImportError:
            # Waitress not installed -- fall back to Flask dev server.
            # On Windows with redirected stdout (e.g. Start-Process),
            # Flask/Click banner printing crashes on closed file handles.
            # Unconditionally redirect to devnull on Windows to prevent it.
            import logging

            log = logging.getLogger("werkzeug")
            log.setLevel(logging.ERROR)
            if os.name == "nt":
                sys.stdout = open(os.devnull, "w", encoding="utf-8")
                sys.stderr = open(os.devnull, "w", encoding="utf-8")
            app.run(
                host=args.host,
                port=args.port,
                debug=False,
                use_reloader=False,
                threaded=True,
            )


def _init_data_provider():
    """Phase 3: Initialize the active DataProvider after path detection."""
    try:
        from clawmetry.providers import init_providers

        return init_providers(
            sessions_dir=SESSIONS_DIR or "",
            log_dir=LOG_DIR or "",
            workspace=WORKSPACE or "",
            metrics_file=METRICS_FILE or "",
        )
    except Exception:
        return None



def main():
    # -----------------------------------------------------------------------
    # Build a shared parent parser for options that apply to all subcommands
    # (and to foreground mode when no subcommand is given).
    # -----------------------------------------------------------------------
    shared = argparse.ArgumentParser(add_help=False)
    shared.add_argument(
        "--port", "-p", type=int, default=8900, help="Port (default: 8900)"
    )
    shared.add_argument(
        "--host", "-H", type=str, default="127.0.0.1", help="Host (default: 127.0.0.1)"
    )
    shared.add_argument("--workspace", "-w", type=str, help="Agent workspace directory")
    shared.add_argument(
        "--data-dir", "-d", type=str, help="OpenClaw data directory (e.g. ~/.openclaw)."
    )
    shared.add_argument(
        "--openclaw-dir",
        type=str,
        help="OpenClaw config directory (default: ~/.openclaw). Env: CLAWMETRY_OPENCLAW_DIR",
    )
    shared.add_argument("--log-dir", "-l", type=str, help="Log directory")
    shared.add_argument(
        "--sessions-dir",
        "-s",
        type=str,
        help="Sessions directory (transcript .jsonl files)",
    )
    shared.add_argument(
        "--metrics-file", "-m", type=str, help="Path to metrics persistence JSON file"
    )
    shared.add_argument("--name", "-n", type=str, help="Your name (shown in Flow tab)")
    shared.add_argument("--debug", dest="debug", action="store_true", default=True)
    shared.add_argument(
        "--no-debug",
        dest="debug",
        action="store_false",
        help="Disable debug mode and auto-reload",
    )
    shared.add_argument("--sse-max-seconds", type=int, default=None)
    shared.add_argument("--max-log-stream-clients", type=int, default=10)
    shared.add_argument("--max-health-stream-clients", type=int, default=10)
    shared.add_argument(
        "--monitor-service", action="append", default=[], metavar="NAME:PORT"
    )
    shared.add_argument("--mc-url", type=str)
    shared.add_argument("--fleet-api-key", type=str)
    shared.add_argument("--fleet-db", type=str)

    # -----------------------------------------------------------------------
    # Top-level parser
    # -----------------------------------------------------------------------
    parser = argparse.ArgumentParser(
        prog="clawmetry",
        description=HELP_TEXT.format(version=__version__),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        parents=[shared],
    )

    class _SafeVersion(argparse.Action):
        def __call__(self, parser, namespace, values, option_string=None):
            try:
                import sys

                sys.stdout.write(f"clawmetry {__version__}\n")
                sys.stdout.flush()
            except Exception:
                pass
            parser.exit()

    parser.add_argument(
        "--version", "-v", nargs=0, action=_SafeVersion, help="Show version"
    )

    subparsers = parser.add_subparsers(dest="command", metavar="command")

    # clawmetry start
    p_start = subparsers.add_parser(
        "start",
        parents=[shared],
        add_help=True,
        help="Start ClawMetry as a background service",
    )

    # clawmetry stop
    p_stop = subparsers.add_parser(
        "stop", parents=[shared], add_help=True, help="Stop the background service"
    )

    # clawmetry restart
    p_restart = subparsers.add_parser(
        "restart",
        parents=[shared],
        add_help=True,
        help="Restart the background service",
    )

    # clawmetry status
    p_status = subparsers.add_parser(
        "status",
        parents=[shared],
        add_help=True,
        help="Show service status, port, and uptime",
    )

    # clawmetry connect
    p_connect = subparsers.add_parser(
        "connect", parents=[shared], add_help=True, help=argparse.SUPPRESS
    )

    # clawmetry uninstall
    p_uninstall = subparsers.add_parser(
        "uninstall",
        parents=[shared],
        add_help=True,
        help="Remove the background service",
    )

    # clawmetry help (alias)
    subparsers.add_parser("help", add_help=True, help="Show this help message")

    args = parser.parse_args()

    # "clawmetry help" -> print help and exit
    if args.command == "help":
        try:
            parser.print_help()
        except (ValueError, OSError):
            pass
        sys.exit(0)

    # Dispatch to subcommand handlers
    if args.command == "start":
        cmd_start(args)
    elif args.command == "stop":
        cmd_stop(args)
    elif args.command == "restart":
        cmd_restart(args)
    elif args.command == "status":
        cmd_status(args)
    elif args.command == "connect":
        cmd_connect(args)
    elif args.command == "uninstall":
        cmd_uninstall(args)
    else:
        # No subcommand -> foreground server (original behaviour)
        try:
            print(ARCHITECTURE_OVERVIEW.format(version=__version__, port=args.port))
        except (ValueError, OSError):
            pass
        try:
            print("Starting dashboard...")
            print()
        except (ValueError, OSError):
            pass
        _run_server(args)


if __name__ == "__main__":
    main()
