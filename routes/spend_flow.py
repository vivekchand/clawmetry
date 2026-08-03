"""routes/spend_flow.py — node-wide AI spend flow (the "where does the
money go" Sankey).

  GET /api/spend-flow?days=7&runtime=claude_code

Returns the :func:`clawmetry.spend_flow.build_spend_flow_slice` shape:
input spend categories (user prompts / prior assistant context / tool
results / residual overhead) -> runtime -> output categories (thinking /
assistant text / built-in vs MCP tool calls), each with tokens + USD, plus
``links`` (Sankey edges) and a ``byRuntime`` map. All category math lives
in the pure engine; this route only clamps params and applies the same
OSS/Free 24h history cap policy as ``/api/usage``.

Reads go through the daemon proxy (the daemon owns the DuckDB writer lock)
with a single-process direct-read fallback — the same pattern as
``routes/context_economics.py``. NEVER 500s: an unreachable store returns
the engine's honest ``insufficient_data`` shape with ``_source: "empty"``.
"""
from __future__ import annotations

from flask import Blueprint, jsonify, request

bp_spend_flow = Blueprint("spend_flow", __name__)


def _ls_call(method_name: str, **kwargs):
    """Cross-process LocalStore call with single-process fallback."""
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


@bp_spend_flow.route("/api/spend-flow")
def api_spend_flow():
    """Spend-flow slice for the Sankey tab.

    Query params:
      * ``days`` — trailing window, clamped to 1..90 (default 7). Non-Pro
        callers are clamped to 1 day (the /api/usage 24h history cap policy)
        and the response carries ``capped_at_24h`` so the UI can render the
        upsell row instead of silently truncating.
      * ``runtime`` — optional runtime filter (session-id-prefix scoping in
        the store, so per-runtime totals reconcile with the node total).
    """
    try:
        days = max(1, min(90, int(request.args.get("days", 7))))
    except (TypeError, ValueError):
        days = 7
    runtime = (request.args.get("runtime") or "").strip() or None

    capped = False
    try:
        import dashboard as _d
        is_pro = bool(_d._is_pro_user())
    except Exception:
        is_pro = False
    if not is_pro and days > 1:
        days = 1
        capped = True

    data = _ls_call("query_spend_flow", days=days, runtime=runtime)
    if isinstance(data, dict) and "result" in data and isinstance(data["result"], dict):
        data = data["result"]
    if isinstance(data, dict) and "totals" in data:
        data = dict(data)
        data["_source"] = "local_store"
    else:
        from clawmetry.spend_flow import build_spend_flow_slice
        data = build_spend_flow_slice([], days=days)
        data["_source"] = "empty"
    data["capped_at_24h"] = capped
    if runtime:
        data["runtime"] = runtime
    return jsonify(data)
