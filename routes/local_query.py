"""routes/local_query.py — coherent local query API over the DuckDB store.

Implements phase 1A of issue #960 (epic #964). Adds an `/api/local/*` HTTP
surface over `clawmetry.local_store`. Two transports will share these
shapes:

* **Local HTTP** — what's in this file. Bound to `127.0.0.1:8900` by the
  OSS dashboard. Used by the OSS local-only browser experience and by any
  CLI/tooling that wants to introspect the local store.
* **WebSocket relay** (follow-up PR) — the daemon opens a long-lived WS to
  `wss://app.clawmetry.com/api/node/relay`; cloud-side dashboards send
  `{type:"query", shape:"events", args:{...}}` frames; the daemon dispatches
  to the same in-process functions exposed here, returns chunked rows over
  the WS. By keeping the dispatch in `_dispatch()`, both transports stay in
  sync — fix the SQL once, both surfaces benefit.

Response shapes mirror the cloud `/api/cloud/*` JSON so the dashboard can
swap backends with no client edits — see PRD #964 for the design.

Auth: none. Bound to localhost. Cloud sync of these endpoints — when it
happens — goes through the WS relay, which has its own auth (cm_ token +
node_id ownership check).
"""

from __future__ import annotations

import time
from typing import Any

from flask import Blueprint, jsonify, request

bp_local_query = Blueprint("local_query", __name__)


# ── Allowlist of query shapes (used by both HTTP + future WS relay) ────────

# A "shape" is a named query the relay is allowed to dispatch. Keeping it
# explicit (not raw SQL pass-through) means the cloud relay can never run
# arbitrary SELECT against the user's local DuckDB — only what we've
# whitelisted here.
_SHAPES = {
    "events":     "query_events",
    "sessions":   "query_sessions",
    "aggregates": "query_aggregates",
    "health":     None,                 # special: no args
    "transcript": "query_events",       # alias with session_id required
}


def _store():
    """Lazy-import. Avoids paying duckdb's import cost on Flask boot when
    the user never hits these endpoints. Always opens read-only — this
    process is a reader; the daemon process owns the writer lock. When
    daemon + dashboard share a process, ``get_store(read_only=True)``
    transparently shares the writer's connection.

    NOTE: when the daemon runs as a SEPARATE process (the launchd/systemd
    install case), DuckDB's exclusive lock blocks even RO opens. In that
    case ``_dispatch()`` proxies to the daemon's local_server first;
    this fallback only fires in single-process mode.
    """
    from clawmetry import local_store
    return local_store.get_store(read_only=True)


# ── Daemon-hosted proxy (cross-process DuckDB lock fix) ─────────────────────

import json as _json
import os as _os

_DISCOVERY_PATH = _os.path.expanduser("~/.clawmetry/local_query.json")
_PROXY_TIMEOUT_SECS = 5.0


def _read_discovery():
    """Read ``~/.clawmetry/local_query.json`` if present + still valid.
    Returns ``{port, token}`` or None."""
    try:
        with open(_DISCOVERY_PATH) as fh:
            data = _json.load(fh)
        port = int(data.get("port") or 0)
        token = data.get("token") or ""
        pid = int(data.get("pid") or 0)
        if not (port and token and pid):
            return None
        # Cheap liveness check: PID alive? Avoids the ~5s socket
        # connect-refused wait when the daemon was killed but the file
        # wasn't cleaned up (atexit doesn't fire on SIGKILL).
        try:
            _os.kill(pid, 0)
        except OSError:
            return None
        return {"port": port, "token": token}
    except (FileNotFoundError, ValueError, OSError):
        return None


def _proxy_dispatch(shape: str, args: dict):
    """Forward the dispatch to the daemon's local_server. Returns the
    response dict on success, raises on failure."""
    # Loop-break: if local_server is running in THIS process we ARE the
    # daemon — proxying would just hit our own handler and recurse.
    try:
        from clawmetry import local_server as _ls
        if _ls.is_running():
            raise RuntimeError("dispatch is in-daemon; skipping proxy")
    except ImportError:
        pass
    disc = _read_discovery()
    if not disc:
        raise FileNotFoundError("daemon local_server not discoverable")
    import urllib.request
    payload = _json.dumps({"shape": shape, "args": args}).encode("utf-8")
    req = urllib.request.Request(
        f"http://127.0.0.1:{disc['port']}/api/local/query",
        data=payload,
        headers={
            "Authorization": f"Bearer {disc['token']}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=_PROXY_TIMEOUT_SECS) as resp:
        return _json.loads(resp.read().decode("utf-8"))


def _coerce_args(shape: str, raw: dict) -> dict:
    """Strict per-shape arg coercion. Drops anything not in the per-shape
    allowed-keys set, casts limit/since/until to safe types."""
    if shape == "events":
        return {
            "session_id": raw.get("session_id"),
            "agent_id":   raw.get("agent_id"),
            "event_type": raw.get("event_type"),
            "since":      raw.get("since"),
            "until":      raw.get("until"),
            "limit":      _safe_int(raw.get("limit"), default=200, lo=1, hi=5000),
        }
    if shape == "sessions":
        return {
            "agent_id": raw.get("agent_id"),
            "since":    raw.get("since"),
            "until":    raw.get("until"),
            "limit":    _safe_int(raw.get("limit"), default=100, lo=1, hi=2000),
        }
    if shape == "aggregates":
        return {
            "agent_id": raw.get("agent_id"),
            "since":    raw.get("since"),
            "until":    raw.get("until"),
        }
    if shape == "transcript":
        sid = raw.get("session_id")
        if not sid:
            raise ValueError("transcript shape requires session_id")
        return {
            "session_id": sid,
            "limit":      _safe_int(raw.get("limit"), default=500, lo=1, hi=5000),
        }
    if shape == "health":
        return {}
    raise ValueError(f"unknown shape: {shape}")


def _safe_int(v: Any, *, default: int, lo: int, hi: int) -> int:
    try:
        n = int(v)
    except (TypeError, ValueError):
        return default
    return max(lo, min(hi, n))


def _dispatch(shape: str, args: dict) -> dict:
    """Single-source-of-truth shape→method bridge. Both the HTTP and (future)
    WS transports call this. Returns a JSON-friendly dict ready to ship.

    Routing order:
      1. If a daemon local_server discovery file is present + alive,
         proxy through it (the daemon is the only process that can read
         the DuckDB while it owns the writer lock).
      2. Else fall back to opening the DuckDB directly (single-process
         mode, or daemon temporarily down).
    """
    started = time.monotonic()
    # Try the daemon proxy first. If it fails for ANY reason, fall
    # through to direct access — the dashboard never goes blank.
    try:
        body = _proxy_dispatch(shape, args)
        body["_via"] = "daemon_proxy"
        body["_elapsed_ms"] = int((time.monotonic() - started) * 1000)
        return body
    except Exception:
        pass
    store = _store()
    if shape == "health":
        body = store.health()
    else:
        method_name = _SHAPES[shape]
        rows = getattr(store, method_name)(**args)
        body = {"rows": rows, "count": len(rows)}
    body["_shape"] = shape
    body["_via"] = "direct"
    body["_elapsed_ms"] = int((time.monotonic() - started) * 1000)
    return body


# ── HTTP routes ────────────────────────────────────────────────────────────


@bp_local_query.route("/api/local/health", methods=["GET"])
def http_health():
    try:
        return jsonify(_dispatch("health", {}))
    except Exception as e:
        return jsonify({"error": str(e)[:300]}), 503


@bp_local_query.route("/api/local/events", methods=["GET"])
def http_events():
    try:
        args = _coerce_args("events", request.args.to_dict())
        return jsonify(_dispatch("events", args))
    except Exception as e:
        return jsonify({"error": str(e)[:300]}), 500


@bp_local_query.route("/api/local/sessions", methods=["GET"])
def http_sessions():
    try:
        args = _coerce_args("sessions", request.args.to_dict())
        return jsonify(_dispatch("sessions", args))
    except Exception as e:
        return jsonify({"error": str(e)[:300]}), 500


@bp_local_query.route("/api/local/aggregates", methods=["GET"])
def http_aggregates():
    try:
        args = _coerce_args("aggregates", request.args.to_dict())
        return jsonify(_dispatch("aggregates", args))
    except Exception as e:
        return jsonify({"error": str(e)[:300]}), 500


@bp_local_query.route("/api/local/transcript/<session_id>", methods=["GET"])
def http_transcript(session_id: str):
    try:
        args = _coerce_args("transcript", {"session_id": session_id, **request.args.to_dict()})
        return jsonify(_dispatch("transcript", args))
    except Exception as e:
        return jsonify({"error": str(e)[:300]}), 500


@bp_local_query.route("/api/local/query", methods=["POST"])
def http_query():
    """Generic shape-dispatched endpoint. Mirrors the WS relay frame format,
    so the same JSON body works over either transport.
    POST /api/local/query  {"shape": "events", "args": {...}}
    """
    body = request.get_json(silent=True) or {}
    shape = body.get("shape")
    if shape not in _SHAPES:
        return jsonify({"error": f"unknown shape: {shape!r}",
                        "allowed_shapes": sorted(_SHAPES.keys())}), 400
    try:
        args = _coerce_args(shape, body.get("args") or {})
        return jsonify(_dispatch(shape, args))
    except Exception as e:
        return jsonify({"error": str(e)[:300]}), 500


# ── Daemon proxy for individual LocalStore methods (issue #1088) ───────────
#
# Why a second endpoint distinct from ``/api/local/query``:
#   * ``/api/local/query`` is a STABLE public contract used by browsers, the
#     CLI, and the future WS relay. Its shapes are deliberately frozen.
#   * ``/__local_query__/<method>`` is an INTERNAL daemon-to-dashboard RPC.
#     It exposes a wider allowlist of LocalStore methods so the legacy
#     ``_try_local_store_*`` fast-paths in ``routes/`` can keep working
#     unchanged when the dashboard runs in a separate process from the sync
#     daemon (the launchd / systemd install case, where DuckDB's exclusive
#     writer lock blocks the dashboard from opening the file even read-only).
#   * The double-underscore prefix is a hint that the surface is private —
#     not a public API, not part of the WS relay protocol.
#
# Allowlist enforcement: every method must be named in ``_DAEMON_METHODS``.
# Returning a generic ``getattr(store, method)(**kwargs)`` would let an
# attacker who already had the bearer token call ``store._fetch("DROP …")``,
# which is a smaller foot-gun but still a foot-gun.

_DAEMON_METHODS = frozenset({
    "query_events",
    "query_sessions",
    "query_sessions_table",
    "query_aggregates",
    "query_heartbeats",
    "query_channels",
    # Issue #1256 follow-up: alert_rules + channel_config_status. PR #1258
    # routed /api/alerts/rules and /api/channels/status through the daemon
    # proxy but missed adding the methods to the allowlist — every call
    # 400'd, fell back to direct DuckDB open (lock contention), then to
    # gateway RPC (down), surfacing as the same 6 s timeout the PR was
    # supposed to fix. Adding both here closes the loop.
    "query_alert_rules",
    "query_channel_config_status",
    "query_crons",
    # Issue #605 DuckDB follow-up: per-job cron-run timeline. Read by
    # ``routes/crons.py:_cron_runs_from_duckdb`` via the daemon proxy.
    "query_cron_runs",
    "query_subagents",
    "query_memory_blobs",
    "query_system_snapshots",
    # Phase 3 (issue #1088 follow-up, 2026-05-13): per-feature aggregation
    # helpers powering the next batch of Bypass-Medium fast-paths.
    "query_compactions",
    "query_cost_split",
    "query_session_model_journey",
    # Tier-1 (2026-05-15): /api/context-anatomy session-history bucket
    # off the JSONL scanner. Returns last non-zero usage.input_tokens
    # from the most-recent active session.
    "query_context_window_peek",
    # Phase 4 (issue #1088 follow-up, 2026-05-13): channel-message
    # foundation. Three helpers proved out the schema; the remaining 18
    # per-provider channel routes follow once these go green.
    "query_channel_messages",
    "query_channel_threads",
    "query_channel_summary",
    # Issue #1282: NeMoClaw approvals fast-path was opening DuckDB writable
    # in routes/nemoclaw.py — collided with the daemon's writer lock.
    # Routed through proxy so /api/nemoclaw/pending-approvals stays fast.
    "query_approvals",
    # Issue #1364: surface clawmetry/proxy.py LoopDetector signals on the
    # dashboard. Read by routes/health.py:/api/loop-signals via the daemon
    # proxy so the dashboard process never opens DuckDB writable.
    "query_recent_loop_signals",
    # Issue #1364 (MOAT 1.b): surface OTel spans we already persist.
    # Powers /api/spans + the Brain-tab "Spans" table.
    "query_recent_spans",
    # Issue #1364 (Tier-1 2026-05-15): /api/fallbacks model/provider
    # transition aggregator. Replaces a JSONL walker that opened up to 100
    # transcript files per request — multi-second on a busy workspace.
    "query_model_fallbacks",
    # Issue #1364 (MOAT Tier-1): /api/skills fidelity counts. Replaces a
    # 7d × N-session JSONL scan (re-walks every transcript on every
    # /api/skills render). Returns Read-tool calls so the route can
    # bucket per-skill body-fetch + linked-file-read counts via the
    # in-memory skill-paths map.
    "query_recent_read_tool_calls",
    "health",
})


@bp_local_query.route("/__local_query__/<method>", methods=["POST"])
def http_local_method(method: str):
    """Dispatch a single LocalStore method call. POST body is
    ``{"kwargs": {...}}``; response is ``{"result": <jsonable>}`` on
    success, ``{"error": "..."}`` with a 4xx/5xx status on failure.
    """
    if method not in _DAEMON_METHODS:
        return jsonify({
            "error": f"method not allowed: {method!r}",
            "allowed": sorted(_DAEMON_METHODS),
        }), 400
    body = request.get_json(silent=True) or {}
    kwargs = body.get("kwargs") or {}
    if not isinstance(kwargs, dict):
        return jsonify({"error": "kwargs must be an object"}), 400
    try:
        store = _store()
        fn = getattr(store, method)
        result = fn(**kwargs)
        return jsonify({"result": result})
    except TypeError as e:
        # Most likely a kwargs-mismatch (caller passed an unsupported arg).
        return jsonify({"error": f"call failed: {str(e)[:200]}"}), 400
    except Exception as e:
        return jsonify({"error": str(e)[:300]}), 500


# ── Cross-process helper used by routes/* fast-paths ───────────────────────

# Cache the discovery so we don't read+stat the JSON file on every request.
# Invalidated when the call fails (daemon restarted → new port + token).
_DAEMON_CACHE: dict = {"disc": None, "ts": 0.0}
_DAEMON_CACHE_TTL_SECS = 30.0


def _cached_discovery():
    """Discovery file lookup with a 30s in-memory cache. The dashboard
    serves dozens of requests per page-load; reading + json-parsing the
    file every time is wasted work."""
    import time as _t
    now = _t.monotonic()
    if _DAEMON_CACHE["disc"] and (now - _DAEMON_CACHE["ts"]) < _DAEMON_CACHE_TTL_SECS:
        return _DAEMON_CACHE["disc"]
    disc = _read_discovery()
    _DAEMON_CACHE["disc"] = disc
    _DAEMON_CACHE["ts"] = now
    return disc


def _invalidate_daemon_cache():
    _DAEMON_CACHE["disc"] = None
    _DAEMON_CACHE["ts"] = 0.0


def local_store_via_daemon(method_name: str, **kwargs):
    """Cross-process LocalStore call.

    Routes a ``LocalStore.<method_name>(**kwargs)`` invocation through the
    sync daemon's ``local_server`` HTTP endpoint, which holds the DuckDB
    writer lock. Use this from any ``_try_local_store_*`` fast-path in
    ``routes/*`` so the helpers fire under the standard install (daemon +
    dashboard as separate processes) instead of silently failing the
    direct-open with an ``IOException: Could not set lock``.

    Returns the call's return value on success.

    Returns ``None`` when the daemon is unreachable / the method isn't
    allowlisted / anything else fails — the caller is expected to fall
    through to the legacy direct-open path (``get_store()`` works fine in
    single-process boots, e.g. tests + dev mode).
    """
    # Loop-break: when local_server is hosted in THIS process (the daemon)
    # the proxy hop is pointless — talk to the LocalStore directly.
    try:
        from clawmetry import local_server as _ls_srv
        if _ls_srv.is_running():
            return None
    except ImportError:
        pass
    disc = _cached_discovery()
    if not disc:
        return None
    import urllib.request
    import urllib.error
    payload = _json.dumps({"kwargs": kwargs}).encode("utf-8")
    req = urllib.request.Request(
        f"http://127.0.0.1:{disc['port']}/__local_query__/{method_name}",
        data=payload,
        headers={
            "Authorization": f"Bearer {disc['token']}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=_PROXY_TIMEOUT_SECS) as resp:
            body = _json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, OSError, ValueError):
        # Stale port / daemon restarted / network gremlin — drop the cache
        # so the next call re-reads the discovery file.
        _invalidate_daemon_cache()
        return None
    if "error" in body:
        return None
    return body.get("result")


# ── Public hook for the future WS relay (#960 phase B) ─────────────────────

def relay_dispatch(shape: str, args: dict) -> dict:
    """Same-process entry point the WS relay client will call when it
    receives a `{type:"query"}` frame from the cloud. Importing this from
    the relay module keeps the SQL/coercion logic in one place."""
    if shape not in _SHAPES:
        return {"error": f"unknown shape: {shape!r}"}
    args = _coerce_args(shape, args or {})
    return _dispatch(shape, args)
