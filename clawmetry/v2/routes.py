"""ClawMetry v2 Flask blueprint.

Serves the pre-built React SPA from `clawmetry/static/v2/dist/` at `/v2`
(default) or at `/` when ``CLAWMETRY_V2_DEFAULT=1`` (``clawmetry --v2-default``).

Opt-in: `dashboard.py` only registers this blueprint when env var
`CLAWMETRY_V2=1` is set (or the user passed `--v2` / `--v2-default` to the
CLI). When the flag is off, the blueprint is never registered, so `/v2` 404s
and the v1 dashboard is unchanged — matches the "parallel rails" plan in the
design handoff README.

SPA routing: the root and all sub-paths serve `index.html`; the React
BrowserRouter handles client-side navigation. Hashed JS/CSS asset URLs are
caught by Flask's static_folder dispatch automatically.

Mode A (default): `/v2`, `/v2/`, `/v2/<path>` serve the SPA; assets at
``/v2/assets/*`` (Vite ``base: "/v2/"``).

Mode B (--v2-default): `/`, `/<path>` serve the SPA; assets at ``/assets/*``
(Vite ``base: "/"``). The v1 dashboard moves to ``/v1/``.
"""

from __future__ import annotations
import json
import os
from pathlib import Path
from flask import Blueprint, send_from_directory, abort, jsonify, request

_DIST_DIR = os.path.join(os.path.dirname(__file__), "..", "static", "v2", "dist")
_ASSETS_DIR = os.path.join(_DIST_DIR, "assets")

# Read the env var at import time (cli.py sets it before dashboard.py is
# imported, so the value is already available when Flask evaluates the routes).
_v2_default = os.environ.get("CLAWMETRY_V2_DEFAULT") == "1"

# static_url_path mirrors the Vite `base` config: "/assets" when v2 is at the
# root, "/v2/assets" when v2 is at /v2. This only matters once a bundle is
# built; the "missing bundle" 503 path is unaffected.
_static_url = "/assets" if _v2_default else "/v2/assets"

_PREFS_DIR = Path.home() / ".clawmetry"
_PREFS_FILE = _PREFS_DIR / "preferences.json"

_VALID_THEMES = {"light", "mid", "dark"}
_VALID_DENSITIES = {"compact", "regular", "comfy"}
_DEFAULT_PREFS = {"theme": "light", "density": "regular"}

bp_v2 = Blueprint(
    "v2",
    __name__,
    static_folder=_ASSETS_DIR,
    static_url_path=_static_url,
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
        base = "/" if _v2_default else "/v2/"
        return (
            "<h1>ClawMetry v2 bundle missing</h1>"
            "<p>Run <code>cd frontend && npm install && npm run build</code> "
            "to produce the static bundle at "
            f"<code>{os.path.normpath(_DIST_DIR)}</code>.</p>"
            f"<p>Build with <code>VITE_BASE={base}</code> when running in "
            f"{'root' if _v2_default else '/v2'} mode.</p>",
            503,
            {"Content-Type": "text/html; charset=utf-8"},
        )
    return send_from_directory(_DIST_DIR, "index.html")


def _catchall(path: str = ""):
    """SPA catch-all. Real asset files are served by the static_folder
    dispatcher BEFORE this view runs; this view only fires for client-side
    router paths like `/v2/trace` or (in default mode) `/trace`."""
    if path:
        asset_path = os.path.join(_DIST_DIR, path)
        if os.path.isfile(asset_path):
            return send_from_directory(_DIST_DIR, path)
        if ".." in path.split("/"):
            abort(404)
    return _serve_index()


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
    from datetime import datetime, timezone, timedelta

    # ── Token gauge ───────────────────────────────────────────────────────
    peek: dict = {}
    try:
        from routes.local_query import local_store_via_daemon
        peek = local_store_via_daemon("query_context_window_peek") or {}
    except Exception:
        pass

    input_toks = int(peek.get("input_tokens") or 0)
    # context_window is already model-aware (1M Opus, etc.) — falls back to 200K.
    context_window = int(peek.get("context_window") or 200_000)
    compaction_threshold = int(context_window * 0.8)

    # ── Compaction history (last 6 h) ─────────────────────────────────────
    history: list[dict] = []
    try:
        from routes.local_query import local_store_via_daemon as _lsd
        raw = _lsd("query_compactions", limit=100) or []
        cutoff = datetime.now(timezone.utc) - timedelta(hours=6)
        for c in raw:
            ts_str = str(c.get("timestamp") or c.get("ts") or "")
            if not ts_str:
                continue
            try:
                ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                if ts < cutoff:
                    continue
                history.append({
                    "ts": ts.strftime("%H:%M"),
                    "used": round(int(c.get("tokens_before") or 0) / 1000, 2),
                    "event": "compaction",
                })
            except Exception:
                continue
    except Exception:
        pass

    # Append current reading as the trailing data point.
    if input_toks > 0:
        history.append({
            "ts": datetime.now(timezone.utc).strftime("%H:%M"),
            "used": round(input_toks / 1000, 2),
        })

    # ── Memory files ──────────────────────────────────────────────────────
    memory_files: list[dict] = []
    try:
        from routes.local_query import local_store_via_daemon as _lsd2
        rows = _lsd2("query_memory_blobs", limit=20) or []
        seen: set[str] = set()
        for r in rows:
            path = r.get("path") or ""
            if not path or path in seen:
                continue
            seen.add(path)
            blob = r.get("blob") or ""
            preview = (blob if isinstance(blob, str) else "")[:200]
            size = r.get("size_bytes")
            if size is None:
                size = len(blob.encode("utf-8") if isinstance(blob, str) else b"")
            memory_files.append({
                "path": path,
                "size_bytes": int(size or 0),
                "preview": preview,
            })
    except Exception:
        pass

    return jsonify({
        "tokens": {
            "used": round(input_toks / 1000, 2),
            "total": context_window // 1000,
            "compaction_threshold": compaction_threshold // 1000,
        },
        "history": history,
        "memory_files": memory_files,
    })


# ── Brain API ─────────────────────────────────────────────────────────

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


# ── SPA serving ───────────────────────────────────────────────────────────
# Registered after the API routes. Flask matches by rule specificity, so the
# explicit /api/v2/* rules still win over the catch-all even in default mode.
if _v2_default:
    # Mode B: v2 owns the root. v1 moves to /v1/ (see routes/meta.py).
    bp_v2.add_url_rule("/", "v2_root", _catchall)
    bp_v2.add_url_rule("/<path:path>", "v2_catchall", _catchall)
else:
    # Mode A: v2 lives at /v2, v1 stays at /.
    bp_v2.add_url_rule("/v2", "v2_root", _serve_index)
    bp_v2.add_url_rule("/v2/", "v2_root_slash", _serve_index)
    bp_v2.add_url_rule("/v2/<path:path>", "v2_catchall", _catchall)
