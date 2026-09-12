"""routes/agentops.py — the AgentOps scorecard and the ground-truth endpoint.

IBM's AgentOps checklist names the numbers an operator should watch across
observability, evaluation and optimization. ClawMetry scored itself against
it on 2026-09-11 (clawmetry.com/blog/agentops-metrics-scorecard); this module
is where the measurable ones become one readable answer, and where the ones
only the operator's own system can judge get a place to land.

bp_agentops:
  GET  /api/agentops/scorecard  every AgentOps figure over one window
                                (``?window=<minutes>``, default 60, and
                                ``?runtime=<id>``), plus which alert rule
                                watches each figure
  POST /api/ground-truth        record the real outcome of a session, as the
                                operator's system of record sees it:
                                ``{session_id, correct, first_pass, label,
                                source, note, external_id}``
  GET  /api/ground-truth        recent reports (``?session_id=``,
                                ``?runtime=``, ``?limit=``)

Both read and write through the daemon proxy, so the dashboard never takes
the DuckDB writer lock. On a node whose store cannot be reached the answer
says so (``store_available: false``); it never paints zeros.
"""

from __future__ import annotations

from flask import Blueprint, jsonify, request

bp_agentops = Blueprint("agentops", __name__)

MAX_WINDOW_MINUTES = 90 * 24 * 60


def _ls_call(method_name, **kwargs):
    """Daemon proxy first, single-process store second (tests, dev mode)."""
    try:
        from routes.local_query import local_store_via_daemon
        result = local_store_via_daemon(method_name, **kwargs)
        if result is not None:
            return result
    except Exception:
        pass
    try:
        from clawmetry import local_store
        store = local_store.get_store(read_only=True)
        return getattr(store, method_name)(**kwargs)
    except Exception:
        return None


def _runtime_arg():
    rt = str(request.args.get("runtime") or "").strip().lower()
    return None if rt in ("", "all") else rt


def _alert_rule_map():
    """Which alert rule type watches which figure, for the UI and API users."""
    try:
        from clawmetry.alert_evaluator import AGENTOPS_RULES
    except Exception:
        return {}
    return {t: {"metric": s["value"], "sample": s["sample"],
                "direction": s["direction"],
                "unit": "percent" if s.get("rate") else s["unit"]}
            for t, s in AGENTOPS_RULES.items()}


@bp_agentops.route("/api/agentops/scorecard", methods=["GET"])
def api_agentops_scorecard():
    """Every AgentOps figure over one window, from the same slice the alert
    evaluator reads, so a number here is the number a rule fires on."""
    try:
        window = int(str(request.args.get("window") or "60").rstrip("m"))
    except (TypeError, ValueError):
        window = 60
    window = max(1, min(window, MAX_WINDOW_MINUTES))
    runtime = _runtime_arg()
    kwargs = {"window_minutes": window}
    if runtime:
        kwargs["runtime"] = runtime
    q = _ls_call("query_session_quality_window", **kwargs)
    store_available = isinstance(q, dict)
    metrics = dict(q) if store_available else {}
    metrics.pop("eval_scores", None)  # the raw score list is not a figure
    return jsonify({
        "window_minutes": window,
        "runtime": runtime or "all",
        "store_available": store_available,
        "metrics": metrics,
        "alert_rules": _alert_rule_map(),
    })


def _flag(body, key):
    """``True`` / ``False`` / ``None`` (absent); raises on anything else."""
    if key not in body or body.get(key) is None:
        return None
    v = body.get(key)
    if isinstance(v, bool):
        return v
    raise ValueError(key)


@bp_agentops.route("/api/ground-truth", methods=["POST"])
def api_ground_truth_post():
    """Record the real outcome of one session.

    ``correct`` says whether the agent's result was right by your records;
    ``first_pass`` whether it was accepted without rework (a claim approved
    the first time, a change merged without a fix-up). Send either or both;
    a later report for the same session fills in what it carries."""
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return jsonify({"error": "Send a JSON object with a session_id."}), 400
    sid = str(body.get("session_id") or "").strip()
    if not sid or len(sid) > 256:
        return jsonify({"error": "session_id is required (at most 256 characters)."}), 400
    try:
        correct = _flag(body, "correct")
        first_pass = _flag(body, "first_pass")
    except ValueError as e:
        return jsonify({"error": f"{e.args[0]} must be true or false."}), 400
    if correct is None and first_pass is None and not body.get("label"):
        return jsonify({"error": "Send at least one of correct, first_pass or label."}), 400
    record = {"session_id": sid, "correct": correct, "first_pass": first_pass}
    for k in ("label", "source", "note", "external_id"):
        if body.get(k) is not None:
            record[k] = str(body.get(k))
    result = _ls_call("ingest_ground_truth", record=record)
    if not isinstance(result, dict):
        return jsonify({
            "error": ("ClawMetry could not reach its local store to save this. "
                      "Check that the ClawMetry background service is running, "
                      "then send it again."),
            "store_available": False,
        }), 503
    return jsonify({"ok": True, **result}), 201


@bp_agentops.route("/api/ground-truth", methods=["GET"])
def api_ground_truth_list():
    """Recent ground-truth reports, newest first."""
    try:
        limit = max(1, min(int(request.args.get("limit") or 100), 1000))
    except (TypeError, ValueError):
        limit = 100
    kwargs = {"limit": limit}
    sid = str(request.args.get("session_id") or "").strip()
    if sid:
        kwargs["session_id"] = sid
    runtime = _runtime_arg()
    if runtime:
        kwargs["runtime"] = runtime
    rows = _ls_call("query_ground_truth", **kwargs)
    return jsonify({
        "reports": rows or [],
        "count": len(rows or []),
        "store_available": rows is not None,
    })
