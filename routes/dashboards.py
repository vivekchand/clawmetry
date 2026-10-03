"""Saved, user-authored dashboard panels.

The Dives query builder produces a validated read-only query and a chart
specification. This blueprint persists that definition in DuckDB and re-runs
it when the Home dashboard opens, so a panel survives browser restarts and
does not create a second JSON-backed data plane.
"""
from __future__ import annotations

import json
import time
import uuid

from flask import Blueprint, jsonify, request

bp_dashboards = Blueprint("dashboards", __name__)

_MAX_NAME_LEN = 120
_MAX_QUESTION_LEN = 4_000
_MAX_SQL_LEN = 20_000


def _daemon_call(method: str, **kwargs):
    """Call a LocalStore method through the daemon, with dev fallback."""
    try:
        from routes.local_query import local_store_via_daemon

        result = local_store_via_daemon(method, **kwargs)
        if result is not None:
            return result
    except Exception:
        pass

    try:
        from clawmetry import local_store

        store = local_store.get_store(read_only=True)
        return getattr(store, method)(**kwargs)
    except Exception:
        return None


def _decode_panel(row: dict) -> dict:
    out = dict(row or {})
    raw_spec = out.get("chart_spec") or "{}"
    if isinstance(raw_spec, str):
        try:
            raw_spec = json.loads(raw_spec)
        except (TypeError, ValueError):
            raw_spec = {}
    out["chart_spec"] = raw_spec if isinstance(raw_spec, dict) else {}
    out["slug"] = out.get("panel_id") or ""
    return out


def _query_panel_sql(sql: str) -> dict | None:
    """Run a saved query through the authoritative assistant SQL guard.

    Dashboard panels use the same AST/table allowlist as Assistant.  The
    older Dives lexical validator is deliberately not used here: it rejects
    valid read-only functions such as ``replace(...)`` before DuckDB can
    validate them.
    """
    result = _daemon_call(
        "query_assistant_sql", sql=sql, max_rows=100, timeout_secs=5
    )
    if not isinstance(result, dict):
        return None
    return result


def _panel_response(
    panel: dict, *, include_rows: bool = False, query_result: dict | None = None
) -> dict:
    out = _decode_panel(panel)
    if include_rows:
        result = query_result
        if result is None:
            result = _query_panel_sql(str(out.get("sql") or ""))
        if result is None:
            return out
        raw_rows = result.get("rows", [])
        out["rows"] = raw_rows if isinstance(raw_rows, list) else []
        if result.get("error"):
            out["run_error"] = result["error"]
        if result.get("truncated"):
            out["truncated"] = True
        if result.get("notice"):
            out["notice"] = result["notice"]
    return out


@bp_dashboards.route("/api/dashboard/panels")
def dashboard_panels_list():
    try:
        limit = max(1, min(200, int(request.args.get("limit", "50"))))
    except (TypeError, ValueError):
        limit = 50
    rows = _daemon_call("query_dashboard_panels", limit=limit)
    if rows is None:
        return jsonify(error="Saved panels are unavailable. Open your local dashboard to view them."), 503
    return jsonify({
        "panels": [_panel_response(row) for row in rows if isinstance(row, dict)],
        "_source": "local_store",
    })


@bp_dashboards.route("/api/dashboard/panels", methods=["POST"])
def dashboard_panels_create():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify(error="Send a panel as a JSON object."), 400
    name = str(payload.get("name") or payload.get("title") or "").strip()
    question = str(payload.get("question") or "").strip()
    sql = str(payload.get("sql") or "").strip()
    chart_spec = payload.get("chart_spec") or {}

    if not name:
        return jsonify({"error": "A panel name is required."}), 400
    if len(name) > _MAX_NAME_LEN:
        return jsonify({"error": f"Panel name is limited to {_MAX_NAME_LEN} characters."}), 400
    if not question or len(question) > _MAX_QUESTION_LEN:
        return jsonify({"error": f"A question is required and must be at most {_MAX_QUESTION_LEN:,} characters."}), 400
    if not sql or len(sql) > _MAX_SQL_LEN:
        return jsonify({"error": "A read-only query is required."}), 400
    if not isinstance(chart_spec, dict):
        return jsonify({"error": "chart_spec must be an object."}), 400

    query_result = _query_panel_sql(sql)
    if query_result is None:
        return jsonify({"error": "The local data store is unavailable; panel was not saved."}), 503
    if query_result.get("error"):
        error = str(query_result["error"])
        if not error.lower().startswith("sql rejected:"):
            error = f"SQL rejected: {error}"
        return jsonify({"error": error}), 400

    panel_id = f"panel-{uuid.uuid4().hex[:16]}"
    now = int(time.time() * 1000)
    stored = _daemon_call(
        "upsert_dashboard_panel",
        panel_id=panel_id,
        name=name,
        question=question,
        sql=sql,
        chart_spec=json.dumps(chart_spec, separators=(",", ":")),
        created_at=now,
    )
    if not stored:
        return jsonify({"error": "The local data store is unavailable; panel was not saved."}), 503
    return jsonify({"panel": _panel_response(stored, include_rows=True, query_result=query_result)}), 201


@bp_dashboards.route("/api/dashboard/panels/<panel_id>")
def dashboard_panel_get(panel_id: str):
    panel = _daemon_call("query_dashboard_panel", panel_id=panel_id)
    if panel is None:
        return jsonify({"error": "Saved panels are unavailable. Open your local dashboard to view them."}), 503
    if not isinstance(panel, dict) or not panel:
        return jsonify({"error": "Panel not found."}), 404
    query_result = _query_panel_sql(str(panel.get("sql") or ""))
    if query_result is None:
        return jsonify({"error": "The local data store is unavailable. Try again shortly."}), 503
    return jsonify(_panel_response(panel, include_rows=True, query_result=query_result))


@bp_dashboards.route("/api/dashboard/panels/<panel_id>", methods=["DELETE"])
def dashboard_panel_delete(panel_id: str):
    deleted = _daemon_call("delete_dashboard_panel", panel_id=panel_id)
    if deleted is None:
        return jsonify({"error": "The local data store is unavailable."}), 503
    if not deleted:
        return jsonify({"error": "Panel not found."}), 404
    return jsonify({"deleted": panel_id})
