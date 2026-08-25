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

Runtime gating
--------------
``/api/agents/<name>/sessions`` returns per-runtime session data and is
therefore gated with :func:`require_runtime` so a locked runtime 402s.
The two detection endpoints (``/api/agents`` and ``/api/agents/<name>``)
stay ungated so the UI can render locked runtime chips + an upgrade CTA
in context, and diagnostic endpoints like ``/api/health`` remain reachable
in enforce mode.
"""
from __future__ import annotations

import os
import time

from flask import Blueprint, jsonify, request
from clawmetry.config import is_local_store_read_enabled

from clawmetry.adapters import registry
from clawmetry.adapters import phase as _phase
from clawmetry._gate import require_runtime

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


def _durable_phases(name: str, session_ids) -> dict:
    """Durable phase rows for these sessions, keyed by BOTH id forms.

    The daemon records family sessions under a runtime-prefixed id
    (``codex:<uuid>``) and OpenClaw sessions bare, because that is how each one
    lands in the sessions table. A caller here holds the adapter's native id and
    should not have to know which, so both forms are asked for and both are
    keyed in the result.

    ``{}`` on any failure. A missing durable record is not an error: the phase
    itself still resolves from the current observation, only the transition time
    is unknown, and an unknown transition time is reported as absent rather than
    as "just now".
    """
    ids = [i for i in (session_ids or []) if i]
    if not ids:
        return {}
    wanted = []
    for sid in ids[:500]:
        wanted.append(sid)
        wanted.append(f"{name}:{sid}")
    rows = _ls_call("query_session_phases", session_ids=wanted, limit=1000)
    out = {}
    for r in (rows or []):
        if not isinstance(r, dict):
            continue
        rid = r.get("sessionId") or ""
        if not rid:
            continue
        out[rid] = r
        prefix = f"{name}:"
        if rid.startswith(prefix):
            out[rid[len(prefix):]] = r
    return out


def _apply_phase(payload: dict, durable: dict) -> dict:
    """Overlay the durable record onto one serialized session.

    Who wins what:

    * ``phaseSince``, ``initialCwd`` and ``resolvable`` come from the store and
      nowhere else. Deriving a transition time here would restart every
      duration on every page load, which is the one number this model exists to
      make trustworthy.
    * The **phase** prefers the fresher answer. This request has just read the
      session; the stored row is from the daemon's last pass, up to a tick ago.
      A session that asked for permission ten seconds ago must not be reported
      as still working because that is what the daemon last saw.
    * When the two disagree, the stored transition time is reported as
      **unknown**. It belongs to the phase the session has just left, and
      printing it would claim "waiting for 14 minutes" about a state entered
      seconds ago -- a fabricated duration, which is worse than none.
    """
    if not durable:
        return payload
    fresh = payload.get("phase")
    stored = durable.get("phase")
    if fresh and stored and fresh != stored:
        payload["phaseSince"] = None
    else:
        payload["phaseSince"] = durable.get("phaseSince")
        if stored and not fresh:
            payload["phase"] = stored
            payload["phaseBasis"] = (durable.get("phaseBasis")
                                     or payload.get("phaseBasis") or "")
            if durable.get("status"):
                payload["status"] = durable.get("status")
    if durable.get("initialCwd"):
        payload["initialCwd"] = durable.get("initialCwd")
    if durable.get("endReason") and not payload.get("endReason"):
        payload["endReason"] = durable.get("endReason")
    if durable.get("resolvable") is not None:
        payload["resolvable"] = durable.get("resolvable")
    return payload


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
    # Phase, on every row. Derived here from the stored timestamps so a store
    # that has rows but no phase record yet still answers, then overlaid with
    # the durable transition time -- which is the ONLY place ``phaseSince`` may
    # come from (recomputing it per request restarts every duration on every
    # page load).
    now = time.time()
    durable = _durable_phases(name, [s["id"] for s in sessions])
    for s in sessions:
        verdict = _phase.resolve(
            now=now,
            end_reason=s.get("endReason") or "",
            last_activity_at=s.get("endedAt") or s.get("startedAt") or None,
            started_at=s.get("startedAt") or None,
        )
        s["phase"] = verdict.phase
        s["status"] = verdict.status
        s["phaseBasis"] = verdict.basis
        s["phaseSince"] = None
        s["lastActivityAt"] = s.get("endedAt") or s.get("startedAt") or None
        s["resolvable"] = None
        s["initialCwd"] = ""
        if verdict.end_reason and not s.get("endReason"):
            s["endReason"] = verdict.end_reason
        _apply_phase(s, durable.get(s["id"]) or {})
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
    blocked = require_runtime(name)
    if blocked is not None:
        return blocked
    try:
        limit = max(1, min(1000, int(request.args.get("limit", 100))))
    except (TypeError, ValueError):
        limit = 100
    if is_local_store_read_enabled():
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
    # Every adapter's session gets a phase here, whether or not the adapter set
    # one: ``resolve_phase`` keeps an asserted phase and derives one from the
    # timestamps otherwise. An adapter that genuinely cannot say leaves it
    # ``None``, which is the honest answer and deliberately not ``idle``.
    now = time.time()
    for s in sessions:
        try:
            s.resolve_phase(now=now)
        except Exception:  # never let one odd session sink the listing
            pass
    durable = _durable_phases(name, [s.id for s in sessions])
    payload = []
    for s in sessions:
        payload.append(_apply_phase(s.to_dict(), durable.get(s.id) or {}))
    return jsonify({"sessions": payload})
