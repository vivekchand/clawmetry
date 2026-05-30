"""
routes/sla.py — SLA policy CRUD + compliance-status endpoints.

bp_sla:
  GET/POST /api/sla/policies       — list or create SLA policies
  DELETE   /api/sla/policies/<id>  — remove a policy
  GET      /api/sla/status         — per-policy compliance (green/red/unknown)
"""

import time
import uuid
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request

bp_sla = Blueprint("sla", __name__)

_VALID_METRICS = ("p95_completion_sec", "error_rate_pct", "cost_per_session_usd")


def _ensure_sla_table(db):
    """Create sla_policies in the fleet SQLite if it doesn't exist yet."""
    db.execute("""
        CREATE TABLE IF NOT EXISTS sla_policies (
            id         TEXT PRIMARY KEY,
            name       TEXT NOT NULL,
            metric     TEXT NOT NULL,
            threshold  REAL NOT NULL,
            window_sec INTEGER NOT NULL DEFAULT 3600,
            agent_id   TEXT,
            enabled    INTEGER NOT NULL DEFAULT 1,
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL
        )
    """)


@bp_sla.route("/api/sla/policies", methods=["GET", "POST"])
def api_sla_policies():
    """List or create SLA policies."""
    import dashboard as _d
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        metric = data.get("metric", "")
        if metric not in _VALID_METRICS:
            return jsonify({"error": f"metric must be one of: {', '.join(_VALID_METRICS)}"}), 400
        threshold = data.get("threshold")
        try:
            threshold = float(threshold)
            if threshold <= 0:
                raise ValueError
        except (TypeError, ValueError):
            return jsonify({"error": "threshold must be a positive number"}), 400
        policy_id = str(uuid.uuid4())[:8]
        now = time.time()
        with _d._fleet_db_lock:
            db = _d._fleet_db()
            _ensure_sla_table(db)
            db.execute(
                "INSERT INTO sla_policies"
                " (id, name, metric, threshold, window_sec, agent_id, enabled, created_at, updated_at)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    policy_id,
                    data.get("name") or metric,
                    metric,
                    threshold,
                    max(60, int(data.get("window_sec") or 3600)),
                    data.get("agent_id") or None,
                    1 if data.get("enabled", True) else 0,
                    now,
                    now,
                ),
            )
            db.commit()
            db.close()
        return jsonify({"ok": True, "id": policy_id}), 201
    with _d._fleet_db_lock:
        db = _d._fleet_db()
        _ensure_sla_table(db)
        rows = db.execute(
            "SELECT id, name, metric, threshold, window_sec, agent_id, enabled,"
            " created_at, updated_at FROM sla_policies ORDER BY created_at ASC"
        ).fetchall()
        db.close()
    return jsonify({"policies": [dict(r) for r in rows]})


@bp_sla.route("/api/sla/policies/<policy_id>", methods=["DELETE"])
def api_sla_policy_delete(policy_id):
    """Delete an SLA policy by id."""
    import dashboard as _d
    with _d._fleet_db_lock:
        db = _d._fleet_db()
        _ensure_sla_table(db)
        if not db.execute("SELECT 1 FROM sla_policies WHERE id = ?", (policy_id,)).fetchone():
            db.close()
            return jsonify({"error": "not found"}), 404
        db.execute("DELETE FROM sla_policies WHERE id = ?", (policy_id,))
        db.commit()
        db.close()
    return jsonify({"ok": True})


def _compute_metric(metric, window_sec, agent_id):
    """Query DuckDB for the current metric value; returns float or None on failure."""
    cutoff = datetime.fromtimestamp(
        time.time() - window_sec, tz=timezone.utc
    ).strftime("%Y-%m-%dT%H:%M:%S")
    try:
        from clawmetry import local_store
        store = local_store.get_store(read_only=True)
        conn = store._conn
        af = " AND agent_type = ?" if agent_id else ""
        p = [cutoff] + ([agent_id] if agent_id else [])
        if metric == "p95_completion_sec":
            row = conn.execute(
                f"""
                SELECT PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY dur)
                FROM (
                    SELECT DATEDIFF('second',
                        TRY_CAST(started_at AS TIMESTAMP),
                        TRY_CAST(ended_at   AS TIMESTAMP)) AS dur
                    FROM sessions
                    WHERE ended_at IS NOT NULL AND started_at > ?{af}
                ) t WHERE dur IS NOT NULL AND dur > 0
                """,
                p,
            ).fetchone()
        elif metric == "error_rate_pct":
            row = conn.execute(
                f"""
                SELECT CAST(
                    COUNT(*) FILTER (
                        WHERE CAST(data AS VARCHAR) LIKE '%"isError":true%'
                           OR CAST(data AS VARCHAR) LIKE '%"error":%'
                    ) AS REAL
                ) / NULLIF(COUNT(*), 0) * 100
                FROM events
                WHERE event_type IN ('tool_result', 'tool_call') AND ts > ?{af}
                """,
                p,
            ).fetchone()
        elif metric == "cost_per_session_usd":
            row = conn.execute(
                f"""
                SELECT AVG(cost_usd) FROM sessions
                WHERE cost_usd IS NOT NULL AND cost_usd > 0 AND started_at > ?{af}
                """,
                p,
            ).fetchone()
        else:
            return None
        return float(row[0]) if row and row[0] is not None else None
    except Exception:
        return None


@bp_sla.route("/api/sla/status")
def api_sla_status():
    """Return per-policy SLA compliance: green / red / unknown."""
    import dashboard as _d
    with _d._fleet_db_lock:
        db = _d._fleet_db()
        _ensure_sla_table(db)
        policies = [dict(r) for r in db.execute(
            "SELECT id, name, metric, threshold, window_sec, agent_id"
            " FROM sla_policies WHERE enabled = 1 ORDER BY created_at ASC"
        ).fetchall()]
        db.close()
    statuses = []
    for p in policies:
        actual = _compute_metric(p["metric"], p.get("window_sec", 3600), p.get("agent_id"))
        colour = "unknown" if actual is None else (
            "green" if actual <= p["threshold"] else "red"
        )
        statuses.append({
            "id": p["id"],
            "name": p["name"],
            "metric": p["metric"],
            "threshold": p["threshold"],
            "actual": round(actual, 4) if actual is not None else None,
            "colour": colour,
        })
    return jsonify({"statuses": statuses})
