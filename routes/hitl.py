"""routes/hitl.py — Human-in-the-loop (HITL) pause API.

Implements issue #878: operator-initiated session pause mechanism that works
without NemoClaw installed and without any cloud dependency.

Pause state lives in ``~/.clawmetry/hitl/pause_<session_id>`` flag files.
The proxy reads these files on every LLM API call (cheap ``Path.exists()``
check) and returns 503 while a session is paused. Decisions are also written
to the ``approvals`` DuckDB table so they appear in the audit log.

Routes:
  POST /api/hitl/flag              — flag a session for human review
  GET  /api/hitl/pending           — list currently paused sessions
  POST /api/hitl/decide            — approve or reject a flagged session
  GET  /api/hitl/status/<sid>      — check pause state for one session
"""

from __future__ import annotations

import json
import time
import logging
from pathlib import Path

from flask import Blueprint, jsonify, request

log = logging.getLogger("clawmetry-hitl")

bp_hitl = Blueprint("hitl", __name__)

_HITL_DIR = Path.home() / ".clawmetry" / "hitl"


def _flag_path(session_id: str) -> Path:
    return _HITL_DIR / f"pause_{session_id}"


def _ensure_dir() -> None:
    _HITL_DIR.mkdir(parents=True, exist_ok=True)


def _try_store_call(method_name: str, **kwargs):
    """Best-effort LocalStore call: daemon proxy first, direct open as fallback."""
    try:
        from routes.local_query import local_store_via_daemon
        result = local_store_via_daemon(method_name, **kwargs)
        if result is not None:
            return result
    except Exception:
        pass
    try:
        from clawmetry import local_store
        store = local_store.get_store(read_only=(method_name.startswith("query")))
        return getattr(store, method_name)(**kwargs)
    except Exception:
        return None


# ── Endpoints ────────────────────────────────────────────────────────────────


@bp_hitl.route("/api/hitl/flag", methods=["POST"])
def hitl_flag():
    """Flag a session for human review. Proxy will block its next LLM call."""
    data = request.get_json(force=True, silent=True) or {}
    session_id = (data.get("session_id") or "").strip()
    reason = (data.get("reason") or "").strip()
    operator = (data.get("operator") or "unknown").strip()

    if not session_id:
        return jsonify({"error": "session_id required"}), 400

    _ensure_dir()
    record = {
        "session_id": session_id,
        "reason": reason,
        "operator": operator,
        "flagged_at": time.time(),
        "status": "pending",
    }
    _flag_path(session_id).write_text(json.dumps(record))
    log.info("HITL flag: session=%s operator=%s reason=%r", session_id, operator, reason)

    # Mirror into DuckDB approvals table for audit log visibility.
    _try_store_call(
        "ingest_approval",
        approval={
            "id": f"hitl_{session_id}",
            "requestor_session_id": session_id,
            "action": "hitl_review",
            "status": "pending",
            "resolver": operator,
            "decision_reason": reason,
            "created_at": str(int(time.time() * 1000)),
        },
    )

    return jsonify({"flagged": True, "session_id": session_id, "operator": operator})


@bp_hitl.route("/api/hitl/pending", methods=["GET"])
def hitl_pending():
    """Return all sessions currently paused for HITL."""
    _ensure_dir()
    sessions: list[dict] = []
    for f in sorted(_HITL_DIR.glob("pause_*"), key=lambda p: p.stat().st_mtime):
        try:
            sessions.append(json.loads(f.read_text()))
        except Exception:
            sessions.append({"session_id": f.name.removeprefix("pause_"), "status": "pending"})
    return jsonify({"sessions": sessions, "count": len(sessions)})


@bp_hitl.route("/api/hitl/decide", methods=["POST"])
def hitl_decide():
    """Approve or reject a flagged session. Removes the pause flag so the proxy unblocks it."""
    data = request.get_json(force=True, silent=True) or {}
    session_id = (data.get("session_id") or "").strip()
    decision = (data.get("decision") or "").strip().lower()
    reason = (data.get("reason") or "").strip()
    operator = (data.get("operator") or "unknown").strip()

    if not session_id:
        return jsonify({"error": "session_id required"}), 400
    if decision not in ("approve", "reject"):
        return jsonify({"error": "decision must be 'approve' or 'reject'"}), 400

    flag = _flag_path(session_id)
    if not flag.exists():
        return jsonify({"error": "session not flagged for HITL"}), 404

    flag.unlink()
    log.info(
        "HITL decision: session=%s decision=%s operator=%s reason=%r",
        session_id, decision, operator, reason,
    )

    # Map to the approvals table vocabulary ("approve" → "approved", "reject" → "deny").
    store_decision = "approve" if decision == "approve" else "deny"
    _try_store_call(
        "update_approval_decision",
        approval_id=f"hitl_{session_id}",
        decision=store_decision,
        resolver=operator,
        reason=reason,
    )

    return jsonify({
        "decided": True,
        "session_id": session_id,
        "decision": decision,
        "operator": operator,
    })


@bp_hitl.route("/api/hitl/status/<session_id>", methods=["GET"])
def hitl_status(session_id: str):
    """Return the current pause state for a single session."""
    flag = _flag_path(session_id)
    if not flag.exists():
        return jsonify({"paused": False, "session_id": session_id})
    try:
        record = json.loads(flag.read_text())
        return jsonify({"paused": True, **record})
    except Exception:
        return jsonify({"paused": True, "session_id": session_id})
