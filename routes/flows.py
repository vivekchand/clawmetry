"""
routes/flows.py — Flow-runs dashboard API endpoint (#611).

Blueprint: bp_flows
Endpoints:
  GET /api/flows         — list all flow runs (newest first)
  GET /api/flows/<id>    — single flow detail with linked tasks
"""

import os
import sqlite3

from flask import Blueprint, jsonify

bp_flows = Blueprint("flows", __name__)


def _get_data_dir():
    """Derive the OpenClaw data directory from SESSIONS_DIR or auto-detect."""
    import dashboard as _d

    # SESSIONS_DIR is typically {data_dir}/agents/main/sessions
    sessions_dir = _d.SESSIONS_DIR or ""
    if sessions_dir:
        # Walk up from .../agents/main/sessions to the data root
        candidate = os.path.dirname(sessions_dir)  # .../agents/main
        candidate = os.path.dirname(candidate)       # .../agents
        candidate = os.path.dirname(candidate)       # .../<data_dir>
        if os.path.isdir(candidate):
            return candidate

    # Fallback: use WORKSPACE or auto-detect
    workspace = getattr(_d, "WORKSPACE", None)
    if workspace and os.path.isdir(workspace):
        return workspace

    return _d._auto_detect_data_dir()


def _connect_ro(db_path):
    """Open a read-only SQLite connection; returns None if the file is missing."""
    if not os.path.isfile(db_path):
        return None
    return sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)


@bp_flows.route("/api/flows")
def api_flows():
    """List all flow runs, newest first.

    Response:
      { "flows": [ { id, goal, status, current_step, blocked_summary,
                      duration_ms, created_at, updated_at } ] }
    """
    data_dir = _get_data_dir()
    if not data_dir:
        return jsonify({"flows": []})

    db_path = os.path.join(data_dir, "flows", "registry.sqlite")
    conn = _connect_ro(db_path)
    if conn is None:
        return jsonify({"flows": []})

    try:
        conn.row_factory = sqlite3.Row
        cur = conn.execute(
            "SELECT flow_id, goal, status, current_step, blocked_summary, "
            "       created_at, updated_at, ended_at "
            "FROM flow_runs ORDER BY created_at DESC"
        )
        rows = cur.fetchall()
    except Exception:
        conn.close()
        return jsonify({"flows": []})

    flows = []
    for r in rows:
        created = r["created_at"] or 0
        ended = r["ended_at"] or 0
        duration_ms = (ended - created) if (ended and created) else None
        flows.append({
            "id": r["flow_id"],
            "goal": r["goal"] or "",
            "status": r["status"] or "unknown",
            "current_step": r["current_step"] or "",
            "blocked_summary": r["blocked_summary"] or "",
            "duration_ms": duration_ms,
            "created_at": created,
            "updated_at": r["updated_at"] or 0,
        })

    conn.close()
    return jsonify({"flows": flows})


@bp_flows.route("/api/flows/<flow_id>")
def api_flow_detail(flow_id):
    """Single flow detail with linked tasks from task_runs.

    Response:
      { "flow": { ... all fields ... }, "tasks": [ ... ] }
    """
    data_dir = _get_data_dir()
    if not data_dir:
        return jsonify({"error": "data directory not found"}), 404

    # ---- flow record ----
    db_path = os.path.join(data_dir, "flows", "registry.sqlite")
    conn = _connect_ro(db_path)
    if conn is None:
        return jsonify({"error": "flows database not found"}), 404

    try:
        conn.row_factory = sqlite3.Row
        cur = conn.execute("SELECT * FROM flow_runs WHERE flow_id = ?", (flow_id,))
        row = cur.fetchone()
    except Exception:
        conn.close()
        return jsonify({"error": "database error"}), 500

    conn.close()

    if not row:
        return jsonify({"error": "flow not found"}), 404

    created = row["created_at"] or 0
    ended = row["ended_at"] or 0
    duration_ms = (ended - created) if (ended and created) else None

    flow = {
        "id": row["flow_id"],
        "shape": row["shape"] or "",
        "sync_mode": row["sync_mode"] or "",
        "owner_key": row["owner_key"] or "",
        "controller_id": row["controller_id"] or "",
        "revision": row["revision"],
        "status": row["status"] or "unknown",
        "goal": row["goal"] or "",
        "current_step": row["current_step"] or "",
        "blocked_task_id": row["blocked_task_id"] or "",
        "blocked_summary": row["blocked_summary"] or "",
        "duration_ms": duration_ms,
        "created_at": created,
        "updated_at": row["updated_at"] or 0,
        "ended_at": ended,
    }

    # ---- linked tasks ----
    tasks = []
    tasks_db_path = os.path.join(data_dir, "tasks", "runs.sqlite")
    tasks_conn = _connect_ro(tasks_db_path)
    if tasks_conn is not None:
        try:
            tasks_conn.row_factory = sqlite3.Row
            cur = tasks_conn.execute(
                "SELECT task_id, runtime, label, status, terminal_outcome, "
                "       created_at, ended_at, error, progress_summary, terminal_summary "
                "FROM task_runs WHERE parent_flow_id = ? ORDER BY created_at ASC",
                (flow_id,),
            )
            for tr in cur.fetchall():
                t_created = tr["created_at"] or 0
                t_ended = tr["ended_at"] or 0
                t_duration_ms = (t_ended - t_created) if (t_ended and t_created) else None
                tasks.append({
                    "task_id": tr["task_id"],
                    "runtime": tr["runtime"] or "",
                    "label": tr["label"] or "",
                    "status": tr["status"] or "unknown",
                    "terminal_outcome": tr["terminal_outcome"] or "",
                    "created_at": t_created,
                    "ended_at": t_ended,
                    "duration_ms": t_duration_ms,
                    "error": tr["error"] or "",
                    "progress_summary": tr["progress_summary"] or "",
                    "terminal_summary": tr["terminal_summary"] or "",
                })
        except Exception:
            pass
        tasks_conn.close()

    return jsonify({"flow": flow, "tasks": tasks})
