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
import datetime
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


@bp_v2.route("/api/v2/cost", methods=["GET"])
def get_cost():
    """/api/v2/cost — real per-day cost/tokens, per-agent breakdown,
    spike log and a single-node leaderboard, all read from the local DuckDB
    store via the daemon proxy (same pattern as ``get_context``/``get_brain``).

    Falls back to empty arrays when the daemon/local store is unreachable;
    the CostPage frontend renders the empty state gracefully. No fabricated
    numbers — every figure here comes from the user's own events.

    Wire shape: {by_integration: [{name, tokens_7d, cost_usd_7d}],
                 daily: [{date, tokens, cost_usd}],
                 spikes: [{date, delta_pct, note}],
                 leaderboard: [{node_id, label, cost_usd_7d}]}
    """
    today = datetime.date.today()
    window = [(today - datetime.timedelta(days=6 - i)).isoformat() for i in range(7)]
    window_set = set(window)

    # query_aggregates is the same per-(agent_id, day) cost/token source the v1
    # Usage tab trusts (matches /api/usage/cost-comparison). We base every figure
    # on it so the daily table, integration bars and leaderboard stay internally
    # consistent. (query_daily_usage_splits exists too but its cost column is
    # cache-weighted and disagrees with the v1 cost-of-record.)
    aggregates = []
    try:
        from routes.local_query import local_store_via_daemon as _lsd
        aggregates = _lsd("query_aggregates") or []
    except Exception:
        pass  # leave empty -> graceful empty UI

    rows7 = [r for r in aggregates if str(r.get("day") or "") in window_set]

    # ── Daily cost/tokens (7 days, zero-filled, summed across agents per day) ──
    by_day: dict = {}
    for row in rows7:
        day = str(row.get("day") or "")
        slot = by_day.setdefault(day, {"date": day, "tokens": 0, "cost_usd": 0.0})
        slot["tokens"] += int(row.get("token_count") or 0)
        slot["cost_usd"] += float(row.get("cost_usd") or 0.0)
    daily = [by_day.get(d, {"date": d, "tokens": 0, "cost_usd": 0.0}) for d in window]
    for d in daily:
        d["cost_usd"] = round(d["cost_usd"], 2)

    # ── Spike log: day-over-day cost jumps > 50% above a $0.50 floor ──
    spikes = []
    for prev, cur in zip(daily, daily[1:]):
        pc, cc = prev["cost_usd"], cur["cost_usd"]
        if cc >= 0.50 and pc > 0 and cc > pc * 1.5:
            delta = round((cc / pc - 1.0) * 100)
            spikes.append({
                "date": cur["date"],
                "delta_pct": delta,
                "note": f"cost up {delta}% vs prior day",
            })

    # ── Per-agent breakdown (7d) — the real grouping the store exposes ──
    by_agent: dict = {}
    for row in rows7:
        name = str(row.get("agent_id") or "main")
        slot = by_agent.setdefault(name, {"name": name, "tokens_7d": 0, "cost_usd_7d": 0.0})
        slot["tokens_7d"] += int(row.get("token_count") or 0)
        slot["cost_usd_7d"] += float(row.get("cost_usd") or 0.0)
    by_integration = sorted(by_agent.values(), key=lambda r: -r["cost_usd_7d"])
    for r in by_integration:
        r["cost_usd_7d"] = round(r["cost_usd_7d"], 2)

    # ── Leaderboard: this node's real 7d total (multi-node fleet is Stage B) ──
    total_cost_7d = round(sum(d["cost_usd"] for d in daily), 2)
    leaderboard = (
        [{"node_id": "main", "label": "this node", "cost_usd_7d": total_cost_7d}]
        if total_cost_7d > 0 else []
    )

    return jsonify({
        "by_integration": by_integration,
        "daily": daily,
        "spikes": spikes,
        "leaderboard": leaderboard,
    })


# ── Approvals API ─────────────────────────────────────────────────────────

def _approvals_is_pro() -> bool:
    try:
        import dashboard as _d
        return bool(_d._is_pro_user())
    except Exception:
        return False


def _approvals_seed() -> dict:
    """In-memory mock queue for Stage B — resets on process restart."""
    return {
        "items": [
            {"id": "apr-vega", "agent": "vega-04", "tool": "post_tweet", "risk": "med", "age": "2m ago"},
            {"id": "apr-leo", "agent": "leo-04", "tool": "git_branch.delete", "risk": "low", "age": "5m ago"},
            {"id": "apr-kepler", "agent": "kepler-1f", "tool": "send_email", "risk": "high", "age": "8m ago"},
            {"id": "apr-orion", "agent": "orion-1a", "tool": "stripe.refund", "risk": "high", "age": "auto · 12m ago", "done": "ok"},
            {"id": "apr-ursa", "agent": "ursa-09", "tool": "db.drop_table", "risk": "high", "age": "blocked · 22m ago", "done": "blocked"},
            {"id": "apr-draco", "agent": "draco-08", "tool": "open_door", "risk": "med", "age": "auto · 31m ago", "done": "ok"},
        ],
        "details": {
            "apr-vega": {
                "risk_score": 0.55,
                "median_score": 0.18,
                "risk_level": "med",
                "title": "Tweet — agent wants to post publicly",
                "agent": "agent-vega-04",
                "session": "0x4F2A",
                "age": "2m ago",
                "action": {
                    "method": "POST /tweet",
                    "account": "@acme_ai",
                    "body": "Whales sing 30-min songs across ocean basins, and the tune changes each season.",
                    "reach": 42300,
                },
                "reasons": [
                    {"label": "first time this account posts a tool-generated tweet", "weight": 0.30},
                    {"label": "audience > 10k", "weight": 0.18},
                    {"label": "contains an outbound link", "weight": 0.07},
                ],
                "rule_suggestion": "auto-approve post_tweet when risk ≤ 0.20 and reach ≤ 5k",
            },
            "apr-leo": {
                "risk_score": 0.22,
                "median_score": 0.18,
                "risk_level": "low",
                "title": "Delete branch — cleanup after merge",
                "agent": "agent-leo-04",
                "session": "0x8B1C",
                "age": "5m ago",
                "action": {
                    "method": "DELETE /git/branch",
                    "account": "github.com/acme/backend",
                    "body": "feature/old-experiment",
                    "reach": 0,
                },
                "reasons": [
                    {"label": "branch already merged to main", "weight": 0.12},
                    {"label": "agent deleted this branch pattern before", "weight": 0.10},
                ],
                "rule_suggestion": "auto-approve git_branch.delete when risk ≤ 0.25 and branch is merged",
            },
            "apr-kepler": {
                "risk_score": 0.78,
                "median_score": 0.18,
                "risk_level": "high",
                "title": "Email — agent wants to contact external recipient",
                "agent": "agent-kepler-1f",
                "session": "0x3D9E",
                "age": "8m ago",
                "action": {
                    "method": "POST /email/send",
                    "account": "noreply@acme.ai",
                    "body": "Quarterly metrics summary attached — please review before EOD.",
                    "reach": 1,
                },
                "reasons": [
                    {"label": "first outbound email to this domain", "weight": 0.35},
                    {"label": "contains attachment", "weight": 0.22},
                    {"label": "recipient outside org allowlist", "weight": 0.21},
                ],
                "rule_suggestion": "auto-approve send_email when risk ≤ 0.30 and recipient is internal",
            },
            "apr-orion": {
                "risk_score": 0.82,
                "median_score": 0.18,
                "risk_level": "high",
                "title": "Refund — auto-approved by rule",
                "agent": "agent-orion-1a",
                "session": "0x1A04",
                "age": "auto · 12m ago",
                "action": {"method": "POST /stripe/refund", "account": "cus_8x2k", "body": "$12.00 · duplicate charge", "reach": 1},
                "reasons": [{"label": "matched auto-approve rule", "weight": 1.0}],
                "rule_suggestion": "",
            },
            "apr-ursa": {
                "risk_score": 0.95,
                "median_score": 0.18,
                "risk_level": "high",
                "title": "Drop table — blocked by policy",
                "agent": "agent-ursa-09",
                "session": "0xFF00",
                "age": "blocked · 22m ago",
                "action": {"method": "DROP TABLE sessions_staging", "account": "postgres://local", "body": "CASCADE", "reach": 0},
                "reasons": [{"label": "destructive DDL always blocked", "weight": 1.0}],
                "rule_suggestion": "",
            },
            "apr-draco": {
                "risk_score": 0.48,
                "median_score": 0.18,
                "risk_level": "med",
                "title": "Open door — auto-approved by rule",
                "agent": "agent-draco-08",
                "session": "0x2C11",
                "age": "auto · 31m ago",
                "action": {"method": "POST /iot/door/unlock", "account": "front-lobby", "body": "visitor badge #4421", "reach": 1},
                "reasons": [{"label": "matched auto-approve rule", "weight": 1.0}],
                "rule_suggestion": "",
            },
        },
    }


_APPROVALS_STORE: dict | None = None


def _approvals_store() -> dict:
    global _APPROVALS_STORE
    if _APPROVALS_STORE is None:
        _APPROVALS_STORE = _approvals_seed()
    return _APPROVALS_STORE


def _approvals_payload() -> dict:
    store = _approvals_store()
    items = store["items"]
    pending = [i for i in items if not i.get("done")]
    awaiting = len(pending)
    is_pro = _approvals_is_pro()
    return {
        "summary": {
            "awaiting": awaiting,
            "median_response": "22s",
            "auto_approved_pct": 84,
        },
        "items": items,
        "details": store["details"],
        "pro_gated_upsell": awaiting > 0 and not is_pro,
        "is_pro": is_pro,
    }


@bp_v2.route("/api/v2/approvals", methods=["GET"])
def get_approvals():
    return jsonify(_approvals_payload())


@bp_v2.route("/api/v2/approvals/<approval_id>", methods=["POST"])
def post_approval(approval_id: str):
    store = _approvals_store()
    body = request.get_json(silent=True) or {}
    decision = (body.get("decision") or "").strip().lower()
    if decision not in ("approve", "deny", "edit"):
        return jsonify({"error": "decision must be approve, deny, or edit"}), 400

    item = next((i for i in store["items"] if i["id"] == approval_id), None)
    if item is None:
        return jsonify({"error": "approval not found"}), 404
    if item.get("done"):
        return jsonify({"error": "approval already resolved"}), 409

    if decision in ("approve", "edit"):
        item["done"] = "ok"
        item["age"] = "just now" if decision == "approve" else "edited · just now"
    else:
        item["done"] = "blocked"
        item["age"] = "blocked · just now"

    detail = store["details"].get(approval_id)
    if detail:
        detail["age"] = item["age"]

    payload = _approvals_payload()
    payload["resolved_id"] = approval_id
    payload["decision"] = decision
    if body.get("auto_apply_rule"):
        payload["rule_applied"] = bool(_approvals_is_pro())
    return jsonify(payload)


# ── Sub-Agents API ────────────────────────────────────────────────────────

@bp_v2.route("/api/v2/subagents", methods=["GET"])
def get_subagents():
    return jsonify({
        "summary": {
            "total_runs": 412,
            "failed": 1,
            "agent_count": 6,
            "tokens_spawned": "1.8M",
        },
        "lanes": [
            {"name": "sub-research-1", "color": "sea", "runs": [
                {"x": 4, "w": 6, "label": "scrape arxiv"},
                {"x": 16, "w": 10, "label": "summarize 12 papers"},
                {"x": 32, "w": 4, "label": "cite check"},
                {"x": 52, "w": 12, "label": "monthly digest", "active": True},
            ]},
            {"name": "sub-cron-cleaner", "color": "moss", "runs": [
                {"x": 6, "w": 2, "label": "purge logs"},
                {"x": 24, "w": 2, "label": "purge logs"},
                {"x": 42, "w": 2, "label": "purge logs"},
                {"x": 60, "w": 2, "label": "purge logs"},
            ]},
            {"name": "sub-incident-bot", "color": "claw-red", "runs": [
                {"x": 12, "w": 14, "label": "p1 \u00b7 db lag", "failed": True},
            ]},
            {"name": "sub-standup-writer", "color": "plum", "runs": [
                {"x": 8, "w": 4, "label": "mon digest"},
                {"x": 20, "w": 4, "label": "tue digest"},
                {"x": 32, "w": 4, "label": "wed digest"},
                {"x": 44, "w": 4, "label": "thu digest"},
                {"x": 56, "w": 4, "label": "fri digest"},
            ]},
            {"name": "sub-doc-indexer", "color": "amber", "runs": [
                {"x": 0, "w": 70, "label": "rolling index \u00b7 all repos"},
            ]},
            {"name": "sub-pr-reviewer", "color": "sea", "runs": [
                {"x": 18, "w": 3, "label": "PR #244"},
                {"x": 26, "w": 2, "label": "PR #245"},
                {"x": 38, "w": 4, "label": "PR #248"},
                {"x": 50, "w": 3, "label": "PR #251"},
            ]},
        ],
        "failed_run": {
            "agent": "sub-incident-bot",
            "label": "p1 \u00b7 db lag",
            "time": "Wed 14:22 \u2192 14:36 \u00b7 14 min",
            "exit_code": 1,
            "log": [
                "! tool timeout",
                "pg.explain('SELECT *...')",
                "exceeded 60s \u00b7 agent retried 3\u00d7",
                "! escalation never fired",
                "slack webhook returned 502",
            ],
        },
        "leaderboard": [
            {"name": "sub-doc-indexer", "runs": 168},
            {"name": "sub-research-1", "runs": 84},
            {"name": "sub-standup-writer", "runs": 65},
            {"name": "sub-pr-reviewer", "runs": 47},
            {"name": "sub-cron-cleaner", "runs": 32},
            {"name": "sub-incident-bot", "runs": 16},
        ],
    })


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
