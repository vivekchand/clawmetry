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

from flask import Blueprint, jsonify, request

from clawmetry.adapters import registry

bp_agents = Blueprint("agents", __name__)


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
    adapter = registry.get(name)
    if adapter is None:
        return jsonify({"error": f"Unknown agent: {name}"}), 404
    try:
        limit = max(1, min(1000, int(request.args.get("limit", 100))))
    except (TypeError, ValueError):
        limit = 100
    try:
        sessions = adapter.list_sessions(limit=limit)
    except Exception as exc:
        return jsonify({"error": f"list_sessions() failed: {exc}"}), 500
    return jsonify({"sessions": [s.to_dict() for s in sessions]})
