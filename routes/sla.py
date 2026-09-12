"""
routes/sla.py — SLA policy CRUD, compliance status, and breach firing.

bp_sla:
  GET/POST /api/sla/policies       — list or create SLA policies
  DELETE   /api/sla/policies/<id>  — remove a policy
  GET      /api/sla/status         — per-policy compliance (green/red/unknown)

``fire_breached_policies`` is called from the dashboard's monitor loop, so a
red policy notifies someone instead of only turning red on a screen nobody is
looking at (the AgentOps scorecard called that "flying blind", 2026-09-11).
"""

import time
import uuid

from flask import Blueprint, jsonify, request

bp_sla = Blueprint("sla", __name__)

_VALID_METRICS = ("p95_completion_sec", "error_rate_pct", "cost_per_session_usd")

# Plain words for the breach notification.
_METRIC_LABELS = {
    "p95_completion_sec":   ("p95 completion time", "s"),
    "error_rate_pct":       ("tool error rate", "%"),
    "cost_per_session_usd": ("cost per session", "USD"),
}


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


def _quality_slice(window_sec, runtime):
    """The quality window the alert evaluator reads, via the daemon proxy.

    This used to open DuckDB here and read ``store._conn``. In a normal
    install the dashboard's store handle is a proxy to the daemon, which has
    no ``_conn``, so every metric raised, was swallowed, and every policy
    reported ``unknown``. The daemon method is the one path that works in
    both a daemon-backed and a single-process install."""
    window_minutes = max(1, int(window_sec or 3600) // 60)
    kwargs = {"window_minutes": window_minutes}
    if runtime:
        kwargs["runtime"] = str(runtime).lower()
    try:
        from routes.local_query import local_store_via_daemon
        q = local_store_via_daemon("query_session_quality_window", **kwargs)
        if isinstance(q, dict):
            return q
    except Exception:
        pass
    try:
        from clawmetry import local_store
        store = local_store.get_store(read_only=True)
        q = store.query_session_quality_window(**kwargs)
        return q if isinstance(q, dict) else None
    except Exception:
        return None


def metric_from_slice(metric, q):
    """One SLA metric off a quality slice; ``None`` when not measurable."""
    if not isinstance(q, dict):
        return None
    if metric == "p95_completion_sec":
        v = q.get("session_duration_p95_sec")
        return float(v) if v is not None else None
    if metric == "error_rate_pct":
        v = q.get("tool_error_rate")
        return float(v) * 100.0 if v is not None else None
    if metric == "cost_per_session_usd":
        n = int(q.get("classified_total") or 0)
        return float(q.get("window_spend_usd") or 0.0) / n if n else None
    return None


def _compute_metric(metric, window_sec, agent_id):
    """Current value of one SLA metric; float or None when not measurable.
    ``agent_id`` scopes to a runtime (``claude_code``, ``openclaw``, ...)."""
    return metric_from_slice(metric, _quality_slice(window_sec, agent_id))


def _enabled_policies():
    import dashboard as _d
    with _d._fleet_db_lock:
        db = _d._fleet_db()
        _ensure_sla_table(db)
        policies = [dict(r) for r in db.execute(
            "SELECT id, name, metric, threshold, window_sec, agent_id"
            " FROM sla_policies WHERE enabled = 1 ORDER BY created_at ASC"
        ).fetchall()]
        db.close()
    return policies


def sla_statuses():
    """Per-policy compliance: ``green`` / ``red`` / ``unknown``."""
    statuses = []
    for p in _enabled_policies():
        actual = _compute_metric(p["metric"], p.get("window_sec", 3600), p.get("agent_id"))
        colour = "unknown" if actual is None else (
            "green" if actual <= p["threshold"] else "red"
        )
        statuses.append({
            "id": p["id"],
            "name": p["name"],
            "metric": p["metric"],
            "threshold": p["threshold"],
            "window_sec": p.get("window_sec", 3600),
            "agent_id": p.get("agent_id"),
            "actual": round(actual, 4) if actual is not None else None,
            "colour": colour,
        })
    return statuses


def breach_message(status):
    """Plain-words notification for one red policy."""
    label, unit = _METRIC_LABELS.get(status["metric"], (status["metric"], ""))
    scope = f" on {status['agent_id']}" if status.get("agent_id") else ""
    minutes = max(1, int(status.get("window_sec") or 3600) // 60)
    return (f"SLA breached: {status['name']}{scope}. {label} is "
            f"{status['actual']:g} {unit} against a target of "
            f"{status['threshold']:g} {unit} over the last {minutes} min.")


def fire_breached_policies(fire):
    """Call ``fire(rule_id=, alert_type=, message=, channels=)`` for each red
    policy. Cooldown and delivery are the caller's (``_fire_alert``).
    Returns the number of breaches found. Never raises."""
    try:
        statuses = sla_statuses()
    except Exception:
        return 0
    n = 0
    for s in statuses:
        if s["colour"] != "red":
            continue
        n += 1
        try:
            fire(rule_id=f"sla:{s['id']}", alert_type="sla_breach",
                 message=breach_message(s), channels=["banner", "telegram"])
        except Exception:
            continue
    return n


@bp_sla.route("/api/sla/status")
def api_sla_status():
    """Return per-policy SLA compliance: green / red / unknown."""
    return jsonify({"statuses": sla_statuses()})
