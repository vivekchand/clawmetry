"""routes/agents.py — Multi-agent adapter endpoints.

Exposes the registered adapter layer (``clawmetry.adapters.registry``)
over HTTP. The dashboard UI calls these on page load to render the
multi-agent chip bar and gate tabs by capability.

  GET  /api/agents                    — list all detected adapters
  GET  /api/agents/<name>             — single adapter detail
  GET  /api/agents/<name>/sessions    — per-agent session list (unified shape)

Zero coupling to ``dashboard.py``: this module only imports from
``clawmetry.adapters``. The adapters themselves reach into dashboard
globals where needed (OpenClawAdapter) — that indirection stays
contained inside the adapter.
"""
from __future__ import annotations

import os

from flask import Blueprint, jsonify, request

from clawmetry.adapters import registry

bp_agents = Blueprint("agents", __name__)


def _ls_call(method_name, **kwargs):
    """Cross-process LocalStore call with single-process fallback (issue #1088)."""
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


def _try_local_store_agent_sessions(name: str, limit: int):
    """Fast path for /api/agents/<name>/sessions. Reads the typed sessions
    table filtered by ``agent_type`` and returns the unified Session shape.

    Returns ``None`` to defer to the adapter when the sessions table has no
    rows for this agent_type (fresh sync, unsupported adapter, etc.).
    """
    rows = _ls_call("query_sessions_table", agent_type=name, limit=limit)
    if not rows:
        return None
    sessions = []
    for r in rows:
        meta = r.get("metadata") if isinstance(r.get("metadata"), dict) else {}
        sid = r.get("session_id") or ""

        def _ts_to_seconds(v):
            if not v:
                return 0.0
            if isinstance(v, (int, float)):
                return float(v) / 1000.0 if v > 1e12 else float(v)
            try:
                from datetime import datetime as _dt
                return _dt.fromisoformat(str(v).replace("Z", "+00:00")).timestamp()
            except Exception:
                return 0.0

        sessions.append({
            "agent": name,
            "id": sid,
            "displayName": r.get("title") or sid[:24],
            "title": r.get("title") or "",
            "model": meta.get("model") or "",
            "source": meta.get("source") or "",
            "startedAt": _ts_to_seconds(r.get("started_at")),
            "endedAt": _ts_to_seconds(r.get("ended_at")) or None,
            "parentId": meta.get("parent_id"),
            "messageCount": int(r.get("message_count") or 0),
            "totalTokens": int(r.get("total_tokens") or 0),
            "inputTokens": int(meta.get("input_tokens") or 0),
            "outputTokens": int(meta.get("output_tokens") or 0),
            "cacheReadTokens": int(meta.get("cache_read_tokens") or 0),
            "cacheWriteTokens": int(meta.get("cache_write_tokens") or 0),
            "reasoningTokens": int(meta.get("reasoning_tokens") or 0),
            "costUsd": float(r.get("cost_usd")) if r.get("cost_usd") is not None else None,
            "costStatus": meta.get("cost_status") or "",
            "endReason": meta.get("end_reason") or "",
        })
    return {"sessions": sessions, "_source": "local_store"}


@bp_agents.route("/api/agents")
def api_agents():
    results = registry.detect_all()
    return jsonify({"agents": [r.to_dict() for r in results]})


@bp_agents.route("/api/agents/<name>")
def api_agent_detail(name: str):
    adapter = registry.get(name)
    if adapter is None:
        return jsonify({"error": f"Unknown agent: {name}"}), 404
    try:
        detect = adapter.detect()
    except Exception as exc:
        return jsonify({"error": f"detect() failed: {exc}"}), 500
    return jsonify(detect.to_dict())


@bp_agents.route("/api/agents/<name>/sessions")
def api_agent_sessions(name: str):
    try:
        limit = max(1, min(1000, int(request.args.get("limit", 100))))
    except (TypeError, ValueError):
        limit = 100
    if os.environ.get("CLAWMETRY_LOCAL_STORE_READ") == "1":
        fast = _try_local_store_agent_sessions(name, limit)
        if fast is not None:
            return jsonify(fast)
    adapter = registry.get(name)
    if adapter is None:
        return jsonify({"error": f"Unknown agent: {name}"}), 404
    try:
        sessions = adapter.list_sessions(limit=limit)
    except Exception as exc:
        return jsonify({"error": f"list_sessions() failed: {exc}"}), 500
    return jsonify({"sessions": [s.to_dict() for s in sessions]})
