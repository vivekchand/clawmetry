"""Agent self-diagnostics read API (WO-59).

Three read-only endpoints over the ``agent_self_reports`` table:

* ``GET /api/self-reports``           the reports themselves (session view)
* ``GET /api/self-reports/honesty``   per (runtime, model) honesty rollup
* ``GET /api/self-reports/support``   per runtime: MCP supported / registered

Every read goes through the daemon proxy (``_ls_call``), never a raw file
and never a writable store open: the daemon owns the DuckDB writer lock and
this module runs in the dashboard process. Nothing here writes; the only
writer is the MCP tool, through the daemon.
"""
from __future__ import annotations

import logging

from flask import Blueprint, jsonify, request

log = logging.getLogger("clawmetry.selfdiag")

bp_selfdiag = Blueprint("selfdiag", __name__)


def _ls_call(method_name, **kwargs):
    """Cross-process LocalStore read with single-process fallback. Mirror
    of ``routes/guard.py::_ls_call``."""
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


def _window_secs(default: int) -> int:
    from clawmetry.self_diagnostics import parse_window_secs
    return parse_window_secs(request.args.get("window"), default)


def _runtime_arg() -> str:
    rt = (request.args.get("runtime") or "").strip().lower()
    return "" if rt in ("", "all") else rt


@bp_selfdiag.route("/api/self-reports")
def api_self_reports():
    """Self-reports, newest first. ``session`` narrows to one session (the
    transcript view), ``runtime`` / ``category`` / ``window`` filter the
    list. Always HTTP 200 with an honest empty list on a store error."""
    from clawmetry import self_diagnostics as _sd
    window = _window_secs(_sd.DEFAULT_WINDOW_SECS)
    session = (request.args.get("session") or request.args.get("session_id") or "").strip()
    category = (request.args.get("category") or "").strip().lower()
    try:
        limit = max(1, min(int(request.args.get("limit", 200)), 2000))
    except (TypeError, ValueError):
        limit = 200
    rows = _ls_call(
        "query_self_reports",
        since_secs=0 if session else window,
        runtime=_runtime_arg(), category=category,
        session_id=session, limit=limit,
    )
    rows = rows if isinstance(rows, list) else []
    return jsonify({
        "reports": rows,
        "count": len(rows),
        "window_secs": window,
        "corroboration_window_secs": _sd.corroboration_window_secs(),
        "categories": list(_sd.allowed_categories()),
        # The plain-words meaning of the label, so every consumer says the
        # same thing: no independent evidence is not the same as false.
        "uncorroborated_means": (
            "No independent evidence was found for this report, which is "
            "not the same as false."
        ),
        "store_reachable": rows is not None,
    })


@bp_selfdiag.route("/api/self-reports/honesty")
def api_self_reports_honesty():
    """Per (runtime, model): the share of detector incidents the agent also
    reported, plus counts per category. Cohorts under the minimum incident
    count carry ``withheld: true`` and a reason instead of a figure."""
    from clawmetry import self_diagnostics as _sd
    window = _window_secs(_sd.DEFAULT_WINDOW_SECS)
    runtime = _runtime_arg()
    honesty = _ls_call("query_self_report_honesty", since_secs=window, runtime=runtime)
    counts = _ls_call("query_self_report_counts", since_secs=window, runtime=runtime)
    return jsonify({
        "window_secs": window,
        "runtime": runtime or "all",
        "honesty": honesty if isinstance(honesty, list) else [],
        "counts": counts if isinstance(counts, dict) else {},
        "min_incidents": _sd.min_incidents(),
        "corroboration_window_secs": _sd.corroboration_window_secs(),
    })


@bp_selfdiag.route("/api/self-reports/support")
def api_self_reports_support():
    """Per runtime: whether ClawMetry can register its MCP server there,
    and whether it is registered right now. Runtimes with no MCP client
    are named as such rather than shown as an empty row."""
    try:
        from clawmetry import mcp_install as _mi
        rows = _mi.support_matrix()
    except Exception as e:  # noqa: BLE001
        log.debug("mcp support matrix failed: %s", e)
        rows = []
    return jsonify({"runtimes": rows, "count": len(rows)})
