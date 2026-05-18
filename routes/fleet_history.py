"""
routes/fleet_history.py — Multi-node fleet + SQLite time-series endpoints.

Extracted from dashboard.py as Phase 5.10 of the incremental modularisation.
Owns the 5 routes registered on ``bp_fleet`` plus the 7 routes registered on
``bp_history``:

  bp_fleet:
    GET  /fleet                         — fleet overview HTML page
    POST /api/nodes/register            — register or update a remote node
    POST /api/nodes/<node_id>/metrics   — receive metrics push from a node
    GET  /api/nodes                     — list all registered nodes
    GET  /api/nodes/<node_id>           — detail + 24h history for one node

  bp_history:
    GET  /api/history/metrics                     — query historical metrics
    GET  /api/history/metrics/list                — list available metric names
    GET  /api/history/sessions                    — historical session data
    GET  /api/history/crons                       — historical cron runs
    GET  /api/history/snapshot/<float:timestamp>  — snapshot nearest a timestamp
    GET  /api/history/stats                       — history DB stats
    GET  /api/history/reliability                 — cross-session reliability

Module-level helpers (``_fleet_db``, ``_fleet_db_lock``, ``_fleet_check_key``,
``_fleet_update_statuses``, ``_history_db``, ``_ext_emit``, ``FLEET_HTML``,
``AgentReliabilityScorer``) stay in ``dashboard.py`` and are reached via late
``import dashboard as _d``. Pure mechanical move — zero behaviour change.
"""

import json
import time
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request

bp_fleet = Blueprint('fleet', __name__)
bp_history = Blueprint('history', __name__)


# ── DuckDB-first source for /api/history/metrics token + cost series ───────
#
# Issue (user P0, 2026-05-18): the Replay tab's "Token Usage Over Time"
# chart was wired exclusively to the optional ``history.py`` SQLite collector
# (~/.clawmetry/history.db ``snapshots`` table). That collector is not
# installed in the default ``pip install clawmetry`` flow, so every user
# whose token data lives in DuckDB (via the sync daemon's
# ``query_daily_usage_splits``) saw an empty chart with a misleading
# "collector polls every 60s" status — even when /api/usage proved the
# data was sitting RIGHT THERE in DuckDB.
#
# Fix: when the requested metric is one of the three the Replay chart wires
# (``tokens_in_total``, ``tokens_out_total``, ``cost_total``), pull from
# DuckDB via ``query_daily_usage_splits`` first, reshape into the
# ``{bucket_ts, avg_val}`` rows the chart consumer expects, and fall back
# to the legacy SQLite path when DuckDB returns nothing (so existing users
# with a populated ``snapshots`` table do NOT regress).
#
# Per-day granularity is intentionally coarser than the SQLite minute/hour
# buckets — splits are computed by walking event blobs and ts→day truncation
# is built into the helper. For the 1h/6h/24h ranges the chart still draws
# a meaningful line (today's day bucket gets bigger as events accumulate);
# for 7d/30d it draws the full daily history. Deeper refactor to honour
# sub-day intervals is flagged in the PR body.

_DUCKDB_BACKED_METRICS = frozenset({
    "tokens_in_total",
    "tokens_out_total",
    "cost_total",
})


def _ts_to_iso(ts_epoch):
    """Epoch seconds → ISO-8601 UTC string the DuckDB ``since``/``until``
    columns expect. Returns ``None`` on bad input so callers can skip
    filtering."""
    try:
        return datetime.fromtimestamp(float(ts_epoch), tz=timezone.utc).isoformat()
    except (TypeError, ValueError, OSError):
        return None


def _day_to_epoch_midnight(day_str):
    """``YYYY-MM-DD`` → epoch seconds at 00:00 UTC. Used to stamp the
    ``bucket_ts`` the Replay chart's x-axis consumes. Returns ``None`` on
    parse failure (caller drops the row)."""
    try:
        dt = datetime.strptime(day_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        return int(dt.timestamp())
    except (TypeError, ValueError):
        return None


def _duckdb_history_metric(metric, from_ts, to_ts):
    """Return ``[{bucket_ts, avg_val}]`` rows for the Replay chart sourced
    from DuckDB via the daemon proxy. Returns ``None`` when DuckDB is
    unreachable or yields no rows so the caller can fall back to SQLite."""
    try:
        from routes.local_query import local_store_via_daemon
    except ImportError:
        return None
    since_iso = _ts_to_iso(from_ts)
    until_iso = _ts_to_iso(to_ts)
    kwargs = {}
    if since_iso:
        kwargs["since"] = since_iso
    if until_iso:
        kwargs["until"] = until_iso
    splits = local_store_via_daemon("query_daily_usage_splits", **kwargs)
    if not splits:
        return None
    key = {
        "tokens_in_total":  "input_tokens",
        "tokens_out_total": "output_tokens",
        "cost_total":       "cost_usd",
    }.get(metric)
    if key is None:
        return None
    out = []
    for r in splits:
        bucket_ts = _day_to_epoch_midnight(r.get("day", ""))
        if bucket_ts is None:
            continue
        try:
            val = float(r.get(key) or 0)
        except (TypeError, ValueError):
            val = 0.0
        out.append({"bucket_ts": bucket_ts, "avg_val": val})
    out.sort(key=lambda d: d["bucket_ts"])
    return out or None


# ── Fleet (multi-node) API Routes ───────────────────────────────────────


@bp_fleet.route("/fleet")
def fleet_page():
    """Fleet overview page for multi-node monitoring."""
    import dashboard as _d
    return _d.FLEET_HTML


@bp_fleet.route("/api/nodes/register", methods=["POST"])
def api_nodes_register():
    """Register or update a remote node."""
    import dashboard as _d
    if not _d._fleet_check_key(request):
        return jsonify({"error": "Invalid or missing X-Fleet-Key"}), 401

    data = request.get_json(silent=True) or {}
    node_id = data.get("node_id", "").strip()
    if not node_id:
        return jsonify({"error": "node_id is required"}), 400

    name = data.get("name", node_id)
    hostname = data.get("hostname", "")
    tags = json.dumps(data.get("tags", []))
    version = data.get("version", "")
    now = time.time()

    with _d._fleet_db_lock:
        db = _d._fleet_db()
        db.execute(
            """
            INSERT INTO nodes (node_id, name, hostname, tags, version, registered_at, last_seen_at, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'online')
            ON CONFLICT(node_id) DO UPDATE SET
                name=excluded.name, hostname=excluded.hostname, tags=excluded.tags,
                version=excluded.version, last_seen_at=excluded.last_seen_at, status='online'
        """,
            (node_id, name, hostname, tags, version, now, now),
        )
        db.commit()
        db.close()

    try:
        _d._ext_emit("fleet.node_register", {"node_id": node_id})
    except Exception:
        pass
    return jsonify({"ok": True, "node_id": node_id})


@bp_fleet.route("/api/nodes/<node_id>/metrics", methods=["POST"])
def api_nodes_push_metrics(node_id):
    """Receive metrics push from a remote node."""
    import dashboard as _d
    if not _d._fleet_check_key(request):
        return jsonify({"error": "Invalid or missing X-Fleet-Key"}), 401

    data = request.get_json(silent=True) or {}
    now = time.time()

    with _d._fleet_db_lock:
        db = _d._fleet_db()
        # Update last_seen
        db.execute(
            "UPDATE nodes SET last_seen_at = ?, status = 'online' WHERE node_id = ?",
            (now, node_id),
        )
        # Store metrics snapshot
        db.execute(
            "INSERT INTO node_metrics (node_id, timestamp, metrics_json) VALUES (?, ?, ?)",
            (node_id, now, json.dumps(data)),
        )
        db.commit()
        db.close()

    return jsonify({"ok": True, "received_at": now})


@bp_fleet.route("/api/nodes")
def api_nodes_list():
    """List all registered nodes with latest metrics."""
    import dashboard as _d
    _d._fleet_update_statuses()

    with _d._fleet_db_lock:
        db = _d._fleet_db()
        nodes = db.execute("SELECT * FROM nodes ORDER BY name").fetchall()
        result = []
        total_cost = 0
        total_sessions = 0
        online_count = 0
        offline_count = 0

        for node in nodes:
            n = dict(node)
            n["tags"] = json.loads(n.get("tags") or "[]")

            # Get latest metrics
            row = db.execute(
                "SELECT metrics_json FROM node_metrics WHERE node_id = ? ORDER BY timestamp DESC LIMIT 1",
                (n["node_id"],),
            ).fetchone()
            n["latest_metrics"] = json.loads(row["metrics_json"]) if row else {}

            # Aggregate stats
            m = n["latest_metrics"]
            if m.get("cost", {}).get("today_usd"):
                total_cost += m["cost"]["today_usd"]
            if m.get("sessions", {}).get("total_today"):
                total_sessions += m["sessions"]["total_today"]

            if n["status"] == "online":
                online_count += 1
            else:
                offline_count += 1

            # Remove internal fields
            n.pop("api_key_hash", None)
            result.append(n)

        db.close()

    return jsonify(
        {
            "nodes": result,
            "fleet_summary": {
                "total_nodes": len(result),
                "online": online_count,
                "offline": offline_count,
                "total_cost_today": round(total_cost, 2),
                "total_sessions_today": total_sessions,
            },
        }
    )


@bp_fleet.route("/api/nodes/<node_id>")
def api_node_detail(node_id):
    """Get detailed info for a single node with metric history."""
    import dashboard as _d
    with _d._fleet_db_lock:
        db = _d._fleet_db()
        node = db.execute(
            "SELECT * FROM nodes WHERE node_id = ?", (node_id,)
        ).fetchone()
        if not node:
            db.close()
            return jsonify({"error": "Node not found"}), 404

        n = dict(node)
        n["tags"] = json.loads(n.get("tags") or "[]")
        n.pop("api_key_hash", None)

        # Latest metrics
        latest_row = db.execute(
            "SELECT metrics_json FROM node_metrics WHERE node_id = ? ORDER BY timestamp DESC LIMIT 1",
            (node_id,),
        ).fetchone()
        latest = json.loads(latest_row["metrics_json"]) if latest_row else {}

        # 24h history
        cutoff = time.time() - 86400
        history_rows = db.execute(
            "SELECT timestamp, metrics_json FROM node_metrics WHERE node_id = ? AND timestamp > ? ORDER BY timestamp",
            (node_id, cutoff),
        ).fetchall()
        history = [
            {"timestamp": r["timestamp"], "metrics": json.loads(r["metrics_json"])}
            for r in history_rows
        ]

        db.close()

    return jsonify(
        {
            "node": n,
            "latest_metrics": latest,
            "history": history,
        }
    )


# ── History / Time-Series API Routes ────────────────────────────────────


@bp_history.route("/api/history/metrics")
def api_history_metrics():
    """Query historical metrics. Params: metric, from, to, interval.

    DuckDB-first (issue: Replay-tab empty chart 2026-05-18): for the three
    metrics the Replay chart wires (tokens in/out, cost), query DuckDB via
    the sync daemon's ``query_daily_usage_splits`` BEFORE touching SQLite.
    Falls back to the legacy SQLite ``snapshots``-table path when DuckDB
    returns no rows so users who DO run the ``history.py`` collector keep
    working.
    """
    metric = request.args.get("metric", "tokens_in_total")
    from_ts = request.args.get("from", type=float, default=time.time() - 3600)
    to_ts = request.args.get("to", type=float, default=time.time())
    interval = request.args.get("interval", None)

    if metric in _DUCKDB_BACKED_METRICS:
        rows = _duckdb_history_metric(metric, from_ts, to_ts)
        if rows:
            return jsonify({"data": rows, "metric": metric, "_source": "duckdb"})

    import dashboard as _d
    if not _d._history_db:
        return jsonify({"data": [], "metric": metric, "_source": "empty"}), 200
    data = _d._history_db.query_metrics(metric, from_ts, to_ts, interval)
    return jsonify({"data": data, "metric": metric, "_source": "sqlite"})


@bp_history.route("/api/history/metrics/list")
def api_history_metrics_list():
    """List available metric names."""
    import dashboard as _d
    if not _d._history_db:
        return jsonify({"metrics": []})
    return jsonify({"metrics": _d._history_db.get_available_metrics()})


@bp_history.route("/api/history/sessions")
def api_history_sessions():
    """Query historical session data."""
    import dashboard as _d
    if not _d._history_db:
        return jsonify({"data": []})
    from_ts = request.args.get("from", type=float, default=time.time() - 3600)
    to_ts = request.args.get("to", type=float, default=time.time())
    session_key = request.args.get("session", None)
    data = _d._history_db.query_sessions(from_ts, to_ts, session_key)
    return jsonify({"data": data})


@bp_history.route("/api/history/crons")
def api_history_crons():
    """Query historical cron run data."""
    import dashboard as _d
    if not _d._history_db:
        return jsonify({"data": []})
    from_ts = request.args.get("from", type=float, default=time.time() - 3600)
    to_ts = request.args.get("to", type=float, default=time.time())
    job_id = request.args.get("job_id", None)
    data = _d._history_db.query_crons(from_ts, to_ts, job_id)
    return jsonify({"data": data})


@bp_history.route("/api/history/snapshot/<float:timestamp>")
def api_history_snapshot(timestamp):
    """Get the snapshot closest to a given timestamp."""
    import dashboard as _d
    if not _d._history_db:
        return jsonify({"error": "History not available"}), 200
    snap = _d._history_db.query_snapshot(timestamp)
    if snap:
        return jsonify(snap)
    return jsonify({"error": "No snapshot found"}), 404


@bp_history.route("/api/history/stats")
def api_history_stats():
    """Get history database stats."""
    import dashboard as _d
    if not _d._history_db:
        return jsonify({"enabled": False})
    stats = _d._history_db.get_stats()
    stats["enabled"] = True
    return jsonify(stats)


@bp_history.route("/api/history/reliability")
def api_history_reliability():
    """Cross-session behavioral reliability trend."""
    import dashboard as _d
    if not _d._history_db:
        return jsonify({"error": "History DB not available"}), 503
    from history import AgentReliabilityScorer

    scorer = AgentReliabilityScorer(_d._history_db)
    window = request.args.get("window", 30, type=int)
    result = scorer.score(window_days=window)
    return jsonify(result)
