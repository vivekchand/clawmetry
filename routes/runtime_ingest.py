"""routes/runtime_ingest.py — custom-runtime HTTP ingest API (Pro feature).

Lets a customer-built agent runtime push events into ClawMetry without
touching the filesystem layout that the OpenClaw/Claude-Code adapters watch.
Useful for in-house frameworks, web agents, evaluation harnesses, anything
that already produces structured run/step records.

Endpoints (all gated on the ``custom_runtime_ingest`` entitlement):

  POST /api/v1/runs                       — start a run; returns ``run_id``
  POST /api/v1/runs/<run_id>/events       — append one or many events
  POST /api/v1/runs/<run_id>/end          — close the run (optional)
  GET  /api/v1/runtimes                   — list known runtimes (free)
  GET  /api/v1/runs/<run_id>              — fetch metadata for a run

Auth:
* If ``CLAWMETRY_INGEST_TOKEN`` is set, requests must present an
  ``X-ClawMetry-Token: <token>`` header (constant-time compared).
* If unset, requests are accepted only from localhost (the same trust
  surface the dashboard already runs on).

Payload shape (single event)::

    {
      "id":           "evt_…",          # required, dedupe key
      "ts":           1.234e9,          # required, epoch seconds
      "event_type":   "model.completed",# required
      "session_id":   "run_…",          # optional, defaults to run_id
      "tool_name":    "Bash",           # optional
      "model":        "claude-…",       # optional
      "role":         "assistant",      # optional
      "data":         {…}               # optional, opaque dict
    }

Bulk shape: ``{"events": [event, event, …]}``.

Everything goes through ``local_store.ingest`` so secret redaction (#2197)
and SIEM forwarding (#2199) still apply.
"""
from __future__ import annotations

import hmac
import logging
import os
import time
import uuid

from flask import Blueprint, jsonify, request

from clawmetry._gate import gate

logger = logging.getLogger("clawmetry.routes.runtime_ingest")

bp_runtime_ingest = Blueprint("runtime_ingest", __name__)


# ── auth ───────────────────────────────────────────────────────────────────────


def _is_localhost(req) -> bool:
    """True when the request's remote_addr is loopback."""
    addr = (req.remote_addr or "").strip()
    return addr in ("127.0.0.1", "::1", "localhost", "")


def _auth_ok(req) -> bool:
    """Either localhost (zero-config) or a matching ingest-token header."""
    expected = (os.environ.get("CLAWMETRY_INGEST_TOKEN") or "").strip()
    if not expected:
        return _is_localhost(req)
    presented = (req.headers.get("X-ClawMetry-Token") or "").strip()
    if not presented:
        return False
    return hmac.compare_digest(expected, presented)


def _unauthorized():
    return jsonify({
        "error": "unauthorized",
        "hint": (
            "Set CLAWMETRY_INGEST_TOKEN on the dashboard and send the same "
            "value in the X-ClawMetry-Token header, or call from localhost."
        ),
    }), 401


# ── helpers ────────────────────────────────────────────────────────────────────


def _node_id() -> str:
    """Stable node id (matches what the rest of clawmetry uses)."""
    try:
        import dashboard as _d

        node = getattr(_d, "NODE_ID", None) or os.environ.get("CLAWMETRY_NODE_ID")
        if node:
            return str(node)
    except Exception:
        pass
    return os.environ.get("HOSTNAME") or "node-local"


def _store():
    """Return the daemon's LocalStore writer (or None if not available)."""
    try:
        from clawmetry import local_store as _ls

        return _ls.get_store()
    except Exception as exc:
        logger.warning("runtime_ingest: local_store unavailable: %s", exc)
        return None


def _normalise_event(ev: dict, run_id: str, runtime: str, node_id: str) -> dict:
    """Fill required keys + default the optionals."""
    out = dict(ev) if isinstance(ev, dict) else {}
    out.setdefault("id", f"evt_{uuid.uuid4().hex[:16]}")
    out.setdefault("ts", time.time())
    out.setdefault("event_type", "event")
    out.setdefault("session_id", run_id)
    out["node_id"] = node_id
    out["agent_type"] = runtime
    # Stash the runtime label in data.extra too so existing analytics that
    # group by runtime see it.
    data = out.get("data") if isinstance(out.get("data"), dict) else {}
    extra = data.get("extra") if isinstance(data.get("extra"), dict) else {}
    extra.setdefault("runtime", runtime)
    data["extra"] = extra
    out["data"] = data
    return out


def _validate_event(ev: dict) -> tuple[bool, str]:
    """Quick shape check on a single event payload."""
    if not isinstance(ev, dict):
        return False, "event must be an object"
    et = ev.get("event_type") or ev.get("type")
    if et is not None and not isinstance(et, str):
        return False, "event_type must be a string"
    ts = ev.get("ts") or ev.get("timestamp")
    if ts is not None:
        try:
            float(ts)
        except Exception:
            return False, "ts must be a number"
    sid = ev.get("session_id")
    if sid is not None and not isinstance(sid, str):
        return False, "session_id must be a string"
    return True, ""


# ── endpoints ──────────────────────────────────────────────────────────────────


@bp_runtime_ingest.route("/api/v1/runtimes", methods=["GET"])
def list_runtimes():
    """List of runtimes we've seen events for. Free — same data the
    runtime switcher in the header already reads. Useful for client SDKs
    that want to introspect before pushing."""
    try:
        from clawmetry import entitlements as _ent

        rows = _ent.runtime_catalog() if hasattr(_ent, "runtime_catalog") else []
    except Exception as exc:
        logger.warning("runtime_ingest: runtime catalog read failed: %s", exc)
        rows = []
    return jsonify({"runtimes": rows})


@bp_runtime_ingest.route("/api/v1/runs", methods=["POST"])
@gate("custom_runtime_ingest")
def start_run():
    """Open a new run. Returns ``run_id`` the client uses for subsequent
    /events + /end calls. Accepts a client-supplied id if you'd rather
    keep your own scheme; the server will accept and trust it.

    Body (all optional)::

        {
          "run_id":   "client-provided id",
          "runtime":  "my_engine",      # default "custom"
          "metadata": {...}             # opaque, stored on the session
        }
    """
    if not _auth_ok(request):
        return _unauthorized()
    body = request.get_json(silent=True) or {}
    run_id = (body.get("run_id") or f"run_{uuid.uuid4().hex[:16]}").strip()
    runtime = (body.get("runtime") or "custom").strip() or "custom"
    metadata = body.get("metadata") if isinstance(body.get("metadata"), dict) else {}

    store = _store()
    if store is None:
        return jsonify({"error": "daemon_unavailable"}), 503
    node_id = _node_id()
    try:
        store.ingest_session({
            "session_id": run_id,
            "agent_type": runtime,
            "node_id": node_id,
            "metadata": metadata,
            "started_at_ms": int(time.time() * 1000),
        })
    except Exception as exc:
        logger.exception("runtime_ingest: ingest_session failed: %s", exc)
        return jsonify({"error": "ingest_failed", "detail": str(exc)}), 500
    return jsonify({"ok": True, "run_id": run_id, "runtime": runtime})


@bp_runtime_ingest.route("/api/v1/runs/<run_id>/events", methods=["POST"])
@gate("custom_runtime_ingest")
def append_events(run_id: str):
    """Append one or many events to a run.

    Body either ``{"event": {...}}``, ``{"events": [...]}``, or a bare
    event object. Returns ``accepted`` (the count) and the assigned ids
    so the client can dedupe its own retry path.
    """
    if not _auth_ok(request):
        return _unauthorized()
    body = request.get_json(silent=True) or {}
    if isinstance(body, dict) and "events" in body:
        events = body.get("events") or []
    elif isinstance(body, dict) and "event" in body:
        events = [body["event"]]
    elif isinstance(body, dict):
        # Bare event object (id/ts/event_type at the top level).
        events = [body]
    else:
        return jsonify({"error": "bad_request", "detail": "expected JSON object"}), 400
    if not isinstance(events, list):
        return jsonify({"error": "bad_request", "detail": "events must be an array"}), 400
    if not events:
        return jsonify({"ok": True, "accepted": 0, "ids": []})
    if len(events) > 1000:
        return jsonify({
            "error": "bad_request",
            "detail": "batch is capped at 1000 events; split and retry",
        }), 400

    store = _store()
    if store is None:
        return jsonify({"error": "daemon_unavailable"}), 503
    node_id = _node_id()
    runtime = (request.args.get("runtime") or "custom").strip() or "custom"
    ids: list[str] = []
    for raw in events:
        ok, msg = _validate_event(raw)
        if not ok:
            return jsonify({"error": "bad_request", "detail": msg}), 400
        norm = _normalise_event(raw, run_id=run_id, runtime=runtime, node_id=node_id)
        try:
            store.ingest(norm)
            ids.append(norm["id"])
        except Exception as exc:
            logger.exception("runtime_ingest: ingest failed for %s: %s", norm.get("id"), exc)
            return jsonify({
                "error": "ingest_failed",
                "accepted": len(ids),
                "ids": ids,
                "detail": str(exc),
            }), 500
    return jsonify({"ok": True, "accepted": len(ids), "ids": ids})


@bp_runtime_ingest.route("/api/v1/runs/<run_id>/end", methods=["POST"])
@gate("custom_runtime_ingest")
def end_run(run_id: str):
    """Mark a run as ended. Optional — long-lived runs work fine without
    this; calling it just stamps ``ended_at_ms`` on the session row so
    the Overview surfaces the right "active vs done" count."""
    if not _auth_ok(request):
        return _unauthorized()
    body = request.get_json(silent=True) or {}
    store = _store()
    if store is None:
        return jsonify({"error": "daemon_unavailable"}), 503
    try:
        # Use ingest_session as an upsert: pass session_id + ended_at_ms.
        # local_store stamps the field on top of whatever started_at_ms /
        # metadata is already there.
        store.ingest_session({
            "session_id": run_id,
            "ended_at_ms": int(time.time() * 1000),
            "metadata": body.get("metadata") if isinstance(body.get("metadata"), dict) else None,
        })
    except Exception as exc:
        logger.exception("runtime_ingest: end_run failed: %s", exc)
        return jsonify({"error": "ingest_failed", "detail": str(exc)}), 500
    return jsonify({"ok": True, "run_id": run_id})


@bp_runtime_ingest.route("/api/v1/runs/<run_id>", methods=["GET"])
@gate("custom_runtime_ingest")
def get_run(run_id: str):
    """Read-back the run + its event count. Useful for clients that want
    to confirm the daemon has persisted what they pushed."""
    if not _auth_ok(request):
        return _unauthorized()
    try:
        from routes.local_query import _dispatch

        sessions = _dispatch("sessions", {"session_id": run_id}) or {}
        events = _dispatch("events", {"session_id": run_id, "limit": 1}) or {}
    except Exception as exc:
        logger.warning("runtime_ingest: get_run dispatch failed: %s", exc)
        return jsonify({"error": "read_failed", "detail": str(exc)}), 500
    rows = sessions.get("sessions") if isinstance(sessions, dict) else None
    return jsonify({
        "run_id": run_id,
        "session": (rows or [None])[0],
        "has_events": bool(events.get("events") if isinstance(events, dict) else False),
    })
