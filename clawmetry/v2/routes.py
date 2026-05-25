"""ClawMetry v2 Flask blueprint.

Serves the pre-built React SPA from `clawmetry/static/v2/dist/` at `/v2`.
Opt-in: `dashboard.py` only registers this blueprint when env var
`CLAWMETRY_V2=1` is set (or the user passed `--v2` to the CLI). When the
flag is off, the blueprint is never registered, so `/v2` 404s and the v1
dashboard is unchanged — matches the "parallel rails" plan in the design
handoff README.

SPA routing: `/v2` and `/v2/<anything>` both serve `index.html`; the
React BrowserRouter (basename="/v2") handles client-side navigation.
Hashed JS/CSS asset URLs like `/v2/assets/index-xyz.js` are caught by
Flask's static_folder dispatch automatically.
"""

from __future__ import annotations
import json
import os
from pathlib import Path
from flask import Blueprint, send_from_directory, abort, jsonify, request

_DIST_DIR = os.path.join(os.path.dirname(__file__), "..", "static", "v2", "dist")
_ASSETS_DIR = os.path.join(_DIST_DIR, "assets")

_PREFS_DIR = Path.home() / ".clawmetry"
_PREFS_FILE = _PREFS_DIR / "preferences.json"

_VALID_THEMES = {"light", "mid", "dark"}
_VALID_DENSITIES = {"compact", "regular", "comfy"}
_DEFAULT_PREFS = {"theme": "light", "density": "regular"}

bp_v2 = Blueprint(
    "v2",
    __name__,
    static_folder=_ASSETS_DIR,
    static_url_path="/v2/assets",
)


def _read_prefs() -> dict:
    try:
        if _PREFS_FILE.is_file():
            with open(_PREFS_FILE) as f:
                stored = json.load(f)
            return {
                "theme": stored.get("theme", "light") if stored.get("theme") in _VALID_THEMES else "light",
                "density": stored.get("density", "regular") if stored.get("density") in _VALID_DENSITIES else "regular",
            }
    except (json.JSONDecodeError, OSError):
        pass
    return dict(_DEFAULT_PREFS)


def _write_prefs(prefs: dict) -> None:
    _PREFS_DIR.mkdir(parents=True, exist_ok=True)
    tmp = _PREFS_FILE.with_suffix(".tmp")
    with open(tmp, "w") as f:
        json.dump(prefs, f, indent=2)
    tmp.rename(_PREFS_FILE)


def _serve_index():
    """Serve the SPA entry point."""
    index_path = os.path.join(_DIST_DIR, "index.html")
    if not os.path.isfile(index_path):
        return (
            "<h1>ClawMetry v2 bundle missing</h1>"
            "<p>Run <code>cd frontend && npm install && npm run build</code> "
            "to produce the static bundle at "
            f"<code>{os.path.normpath(_DIST_DIR)}</code>.</p>",
            503,
            {"Content-Type": "text/html; charset=utf-8"},
        )
    return send_from_directory(_DIST_DIR, "index.html")


# ── Preferences API ──────────────────────────────────────────────────────

@bp_v2.route("/api/v2/preferences", methods=["GET"])
def get_preferences():
    return jsonify(_read_prefs())


@bp_v2.route("/api/v2/preferences", methods=["POST"])
def set_preferences():
    body = request.get_json(silent=True) or {}
    prefs = _read_prefs()
    if "theme" in body and body["theme"] in _VALID_THEMES:
        prefs["theme"] = body["theme"]
    if "density" in body and body["density"] in _VALID_DENSITIES:
        prefs["density"] = body["density"]
    _write_prefs(prefs)
    return jsonify(prefs)


# ── SPA serving ──────────────────────────────────────────────────────────

@bp_v2.route("/v2")
@bp_v2.route("/v2/")
def v2_root():
    return _serve_index()


@bp_v2.route("/v2/<path:path>")
def v2_catchall(path: str):
    asset_path = os.path.join(_DIST_DIR, path)
    if os.path.isfile(asset_path):
        return send_from_directory(_DIST_DIR, path)
    if ".." in path.split("/"):
        abort(404)
    return _serve_index()


# ── Ops API ───────────────────────────────────────────────────────────

@bp_v2.route("/api/v2/ops", methods=["GET"])
def get_ops():
    return jsonify({
        "services": [
            {"name": "Gateway controller", "status": "ok", "uptime": "14d", "bpm": 84, "latency": "44ms"},
            {"name": "Session DB", "status": "ok", "uptime": "14d", "bpm": 62, "latency": "2ms"},
            {"name": "Memory store", "status": "ok", "uptime": "14d", "bpm": 71, "latency": "1ms"},
            {"name": "Telegram connector", "status": "ok", "uptime": "8d", "bpm": 92, "latency": "180ms"},
            {"name": "WhatsApp connector", "status": "warn", "uptime": "32m", "bpm": 110, "latency": "440ms"},
            {"name": "Discord connector", "status": "ok", "uptime": "8d", "bpm": 78, "latency": "92ms"},
            {"name": "Cron manager", "status": "ok", "uptime": "14d", "bpm": 68, "latency": "—"},
            {"name": "ClawMetry agent (NemoClaw)", "status": "ok", "uptime": "8d", "bpm": 56, "latency": "12ms"},
        ],
        "crons": [
            {"id": "cron-1", "name": "morning-digest", "schedule": "0 8 * * *", "last_run": "ok · today 08:00", "next_run": "tomorrow 08:00", "status": "ok", "miss_count": 0},
            {"id": "cron-2", "name": "weekly-rollup", "schedule": "0 17 * * fri", "last_run": "ok · fri 17:00", "next_run": "fri 17:00", "status": "ok", "miss_count": 0},
            {"id": "cron-3", "name": "purge-old-sessions", "schedule": "0 3 * * *", "last_run": "missed · 6h ago", "next_run": "in 18h", "status": "miss", "miss_count": 1},
            {"id": "cron-4", "name": "embed-docs", "schedule": "*/15 * * * *", "last_run": "ok · 4m ago", "next_run": "in 11m", "status": "ok", "miss_count": 0},
            {"id": "cron-5", "name": "standup-poll", "schedule": "30 9 * * 1-5", "last_run": "ok · today 09:30", "next_run": "tomorrow 09:30", "status": "ok", "miss_count": 0},
            {"id": "cron-6", "name": "billing-cron", "schedule": "0 0 1 * *", "last_run": "ok · Oct 1", "next_run": "Nov 1", "status": "ok", "miss_count": 0},
            {"id": "cron-7", "name": "memory-compact", "schedule": "0 4 * * *", "last_run": "fail · today 04:00", "next_run": "in 20h", "status": "fail", "miss_count": 0},
        ],
        "incidents": [
            {"service": "WhatsApp connector", "summary": "Reconnect storm · 7 retries in 32 min", "detail": "Last good message · 32m ago\nLikely cause · upstream rate limit", "severity": "warn"},
        ],
    })

# ── Context API ──────────────────────────────────────────────────────

@bp_v2.route("/api/v2/context", methods=["GET"])
def get_context():
    return jsonify({
        "tokens": {"used": 51.95, "total": 200, "compaction_threshold": 160},
        "segments": [
            {"name": "System prompt", "tokens": 1.2, "color": "ink-3", "note": "boilerplate · ClawMetry default"},
            {"name": "Tooling overhead", "tokens": 3.0, "color": "sea", "note": "framework scaffolding"},
            {"name": "Skill headers", "tokens": 1.5, "color": "amber", "note": "7 skills loaded"},
            {"name": "Bootstrap · SOUL.md", "tokens": 0.75, "color": "plum", "note": "agent persona"},
            {"name": "Bootstrap · MEMORY.md", "tokens": 1.0, "color": "plum", "note": "long-term memory"},
            {"name": "Tool schemas (JSON)", "tokens": 7.0, "color": "sea", "note": "12 tools, full JSON-schema"},
            {"name": "Conversation history", "tokens": 38.5, "color": "claw-red", "note": "current session · 84 turns"},
        ],
        "history": [
            {"ts": "08:00", "used": 50, "event": "compaction"},
            {"ts": "10:00", "used": 42},
            {"ts": "12:00", "used": 22, "event": "compaction"},
            {"ts": "14:00", "used": 56},
            {"ts": "16:00", "used": 30, "event": "compaction"},
            {"ts": "18:00", "used": 51.95},
        ],
        "memory_files": [
            {"path": "SOUL.md", "size_bytes": 1200, "preview": "You are agent-vega-04. You're patient,\ndirect, and never deploy on Fridays."},
            {"path": "MEMORY.md", "size_bytes": 1024, "preview": "- prod cluster: us-west-2\n- on-call: @vivek (oct rotation)\n- last incident: 2026-04-12 db lag"},
        ],
    })

@bp_v2.route("/api/v2/brain", methods=["GET"])
def get_brain():
    """Stage A: adapts /api/brain-history events to the v2 turn wire shape.
    Stage B will group events into real conversation round-trips via DuckDB.

    Wire shape: {turns: [{id, time, channel, user, steps, skill, llms,
                           tools, duration_ms, active, source, severity}],
                 total: int}
    """
    from flask import request as _req
    try:
        limit = max(1, min(200, int(_req.args.get("limit", 50))))
    except (TypeError, ValueError):
        limit = 50

    _CHANNEL_EMOJI = {
        "telegram": "📱", "signal": "📡", "whatsapp": "💬",
        "discord": "🎮", "slack": "💼", "imessage": "🍎",
        "webchat": "🌐", "matrix": "🔢", "msteams": "🏢",
        "irc": "📡", "googlechat": "🔵", "mattermost": "⚡",
        "line": "💚", "nostr": "🟣", "twitch": "💜",
        "bluebubbles": "💙", "cli": "⌨️", "tui": "⌨️",
    }

    def _channel_from_source(source: str) -> str:
        parts = (source or "").split(":")
        # agent:<id>:<provider>:… — provider is index 2
        if len(parts) >= 3 and parts[2] not in ("main", "subagent", "cron", ""):
            return parts[2].lower()
        return "cli"

    turns = []
    try:
        from routes.brain import api_brain_history
        resp = api_brain_history()
        events = (resp.get_json() or {}).get("events", [])
        for i, ev in enumerate(events[:limit]):
            ev_type = (ev.get("type") or "EVENT").upper()
            source = ev.get("source", "")
            channel = _channel_from_source(source)
            turns.append({
                "id": ev.get("id") or f"{source}-{i}",
                "time": ev.get("time", ""),
                "channel": channel,
                "channel_emoji": _CHANNEL_EMOJI.get(channel, "💬"),
                "user": (ev.get("detail") or "")[:120],
                "steps": [ev_type],
                "skill": ev.get("skill"),
                "llms": [ev["model"]] if ev.get("model") else [],
                "tools": [ev["tool"]] if ev.get("tool") else [],
                "duration_ms": ev.get("duration_ms") or 0,
                "active": bool(ev.get("active")),
                "source": ev.get("sourceLabel") or source,
                "severity": ev.get("severity"),
            })
    except Exception:
        pass  # turns stays []

    return jsonify({"turns": turns, "total": len(turns)})
