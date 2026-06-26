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
#
# Issue #2987 (Query Spine P1): the allowlist is now DERIVED from the
# declared q/1 contract registry in ``clawmetry/query_contract.py`` —
# one source of truth shared by this module, ``docs/QUERY_CONTRACT.md``
# (generated), and the drift CI test. Adding a shape means adding a
# "live" registry entry (with its arg schema + trust class) first; a
# shape with no registry entry fails ``tests/test_query_contract_drift.py``.
# The derived dict is byte-identical to the historical literal:
#   events/sessions/aggregates/transcript/spans/traces/external_calls/
#   search -> their LocalStore method names, health -> None (special:
#   ``_dispatch`` calls ``store.health()`` directly).
from clawmetry.query_contract import live_shapes as _qc_live_shapes

_SHAPES = _qc_live_shapes()


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
# The daemon's local_server is threaded, but DuckDB serializes queries on its
# single connection — so heavy reads (e.g. query_events) under a page-load
# fan-out can queue past the timeout and surface as a transient EMPTY result
# (urlopen raises → caller returns None → blank tab). Retry on TIMEOUTS only
# (contended DuckDB) with backoff + a longer per-attempt timeout; fail fast on
# connection errors (daemon down → fall through to direct open).
_PROXY_TIMEOUTS = (5.0, 9.0)  # per-attempt seconds; len() == max attempts


def _is_timeout_err(e):
    import socket as _socket
    if isinstance(e, (_socket.timeout, TimeoutError)):
        return True
    return isinstance(getattr(e, "reason", None), (_socket.timeout, TimeoutError))


def _urlopen_retry(req):
    """POST to the daemon with timeout-aware retry. Returns the parsed JSON
    body or raises the last exception. Retries only on timeouts (contended
    DuckDB), not connection errors (which mean the daemon is down)."""
    import urllib.request
    last = None
    n = len(_PROXY_TIMEOUTS)
    for i, t in enumerate(_PROXY_TIMEOUTS):
        try:
            with urllib.request.urlopen(req, timeout=t) as resp:
                return _json.loads(resp.read().decode("utf-8"))
        except Exception as e:  # noqa: BLE001 — re-raised below
            last = e
            if _is_timeout_err(e) and i < n - 1:
                time.sleep(0.2 * (i + 1))
                continue
            raise
    raise last


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
    return _urlopen_retry(req)


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
    if shape == "spans":
        return {
            "trace_id":   raw.get("trace_id"),
            "session_id": raw.get("session_id"),
            "agent_type": raw.get("agent_type"),
            "since":      raw.get("since"),
            "until":      raw.get("until"),
            "limit":      _safe_int(raw.get("limit"), default=200, lo=1, hi=2000),
        }
    if shape == "traces":
        return {
            "session_id": raw.get("session_id"),
            "agent_type": raw.get("agent_type"),
            "since":      raw.get("since"),
            "until":      raw.get("until"),
            "limit":      _safe_int(raw.get("limit"), default=100, lo=1, hi=1000),
        }
    if shape == "external_calls":
        return {
            "session_id": raw.get("session_id"),
            "since":      raw.get("since"),
            "until":      raw.get("until"),
            "limit":      _safe_int(raw.get("limit"), default=200, lo=1, hi=2000),
        }
    if shape == "models":
        return {
            "runtime": raw.get("runtime"),
            "since":   raw.get("since"),
            "until":   raw.get("until"),
            "limit":   _safe_int(raw.get("limit"), default=1000, lo=1, hi=10000),
        }
    if shape == "runtimes":
        return {
            "since": raw.get("since"),
            "until": raw.get("until"),
            "limit": _safe_int(raw.get("limit"), default=1000, lo=1, hi=10000),
        }
    if shape == "rollup_sessions":
        return {
            "runtime": raw.get("runtime"),
            "limit":   _safe_int(raw.get("limit"), default=200, lo=1, hi=2000),
        }
    if shape == "search":
        q = (raw.get("q") or "").strip()
        if not q:
            raise ValueError("search shape requires non-empty 'q' parameter")
        return {
            "q":      q,
            "model":  raw.get("model") or None,
            "status": raw.get("status") or None,
            "since":  raw.get("since"),
            "until":  raw.get("until"),
            "limit":  _safe_int(raw.get("limit"), default=50, lo=1, hi=500),
        }
    if shape == "agent_graph":
        return {
            "since": raw.get("since"),
            "until": raw.get("until"),
            "limit": _safe_int(raw.get("limit"), default=500, lo=1, hi=2000),
        }
    raise ValueError(f"unknown shape: {shape}")


def _safe_int(v: Any, *, default: int, lo: int, hi: int) -> int:
    try:
        n = int(v)
    except (TypeError, ValueError):
        return default
    return max(lo, min(hi, n))


def _apply_24h_cap(args: dict) -> bool:
    """OSS / Cloud-Free retention cap for raw event reads (issue #1448).

    Mutates ``args`` in-place: when the caller is not a Pro user we clamp
    ``since`` to ``now - 24h``. Returns True when the cap was enforced so
    the response can surface the upgrade CTA. Pro users (validated via
    ``dashboard._is_pro_user``) bypass the cap entirely. Any failure
    fail-closes to non-Pro — we never leak unlimited history on a missing
    signal.
    """
    try:
        import dashboard as _d
        is_pro = bool(_d._is_pro_user())
    except Exception:
        is_pro = False
    if is_pro:
        return False
    from datetime import datetime, timedelta, timezone
    cap_iso = (
        datetime.now(timezone.utc) - timedelta(hours=24)
    ).strftime("%Y-%m-%dT%H:%M:%SZ")
    since = args.get("since") or ""
    if not since or since < cap_iso:
        args["since"] = cap_iso
        return True
    return False


def _dispatch(shape: str, args: dict) -> dict:
    """Single-source-of-truth shape→method bridge. Both the HTTP and (future)
    WS transports call this. Returns a JSON-friendly dict ready to ship.

    Routing order:
      1. If a daemon local_server discovery file is present + alive,
         proxy through it (the daemon is the only process that can read
         the DuckDB while it owns the writer lock).
      2. Else fall back to opening the DuckDB directly (single-process
         mode, or daemon temporarily down).

    Arg coercion: callers are NOT required to pre-filter ``args``. Cloud-side
    callers (heartbeat-piggyback ``pending_queries`` from
    ``clawmetry-cloud/routes/cloud.py``) sometimes attach metadata like
    ``node_id`` for cloud-side routing that the local DuckDB-backed
    ``LocalStore`` methods don't accept. Without coercion that surfaced as
    a TypeError per heartbeat (one of the root causes behind the 2026-05-18
    "cloud shows 0 sessions" P0). ``_coerce_args`` runs the per-shape
    allowlist so unknown kwargs are dropped before the store call.
    """
    started = time.monotonic()
    try:
        args = _coerce_args(shape, args or {})
    except ValueError:
        # ``_coerce_args`` raises for required-arg violations (e.g. transcript
        # missing session_id). Let the caller see the original ValueError so
        # the cloud dispatcher logs a meaningful message.
        raise
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
    elif shape == "agent_graph":
        # agent_graph returns a dict directly (nodes/edges/count), not a list,
        # so pass it through like health rather than wrapping in {"rows": ...}.
        body = getattr(store, _SHAPES[shape])(**args)
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
        # Issue #1448 surface 4 — OSS / Cloud-Free users get capped to
        # the last 24h of raw events. Pro users bypass entirely. Mirrors
        # the pattern PR #1445 set on /api/flow/runs.
        capped_at_24h = _apply_24h_cap(args)
        body = _dispatch("events", args)
        body["capped_at_24h"] = capped_at_24h
        return jsonify(body)
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


@bp_local_query.route("/api/local/spans/<span_id>", methods=["GET"])
def http_span_detail(span_id: str):
    """Full OTel span row including BLOB columns (input, output, attributes,
    events, links). Returns 404 for session-derived synthetic spans that do
    not live in the ``spans`` table."""
    try:
        rows = _store().query_spans(span_id=span_id, limit=1)
    except Exception as e:
        return jsonify({"available": False, "error": str(e)[:300]}), 503
    if not rows:
        return jsonify({"available": False}), 404
    return jsonify({"available": True, "span": rows[0]})


@bp_local_query.route("/api/local/spans", methods=["GET"])
def http_spans():
    """List spans. Filters: trace_id, session_id, agent_type, since, until, limit."""
    try:
        args = _coerce_args("spans", request.args.to_dict())
        return jsonify(_dispatch("spans", args))
    except Exception as e:
        return jsonify({"error": str(e)[:300]}), 500


@bp_local_query.route("/api/local/traces", methods=["GET"])
def http_traces():
    """List traces (one row per trace_id). Filters: session_id, agent_type, since, until, limit."""
    try:
        args = _coerce_args("traces", request.args.to_dict())
        return jsonify(_dispatch("traces", args))
    except Exception as e:
        return jsonify({"error": str(e)[:300]}), 500


@bp_local_query.route("/api/local/external-calls", methods=["GET"])
def http_external_calls():
    """List external (non-LLM) API calls captured by the interceptor.

    Optional query params: session_id, since (ISO), until (ISO), limit (int).
    When session_id is given, results are filtered to calls whose timestamp
    falls within that session's start/end window."""
    try:
        args = _coerce_args("external_calls", request.args.to_dict())
        return jsonify(_dispatch("external_calls", args))
    except Exception as e:
        return jsonify({"error": str(e)[:300]}), 500


@bp_local_query.route("/api/local/search", methods=["GET"])
def http_search():
    """Search sessions by title / eval-reason text.

    Required: ``q`` (search string). Optional: ``model``, ``status``,
    ``since`` (ISO), ``until`` (ISO), ``limit`` (int, default 50, max 500).
    Returns session summary rows matching the query, sorted newest-first.
    """
    try:
        args = _coerce_args("search", request.args.to_dict())
        return jsonify(_dispatch("search", args))
    except ValueError as e:
        return jsonify({"error": str(e)[:300]}), 400
    except Exception as e:
        return jsonify({"error": str(e)[:300]}), 500


@bp_local_query.route("/api/local/agent-graph", methods=["GET"])
def http_agent_graph():
    """Cross-session agent spawn graph. Optional: since, until (unix seconds), limit."""
    try:
        args = _coerce_args("agent_graph", request.args.to_dict())
        return jsonify(_dispatch("agent_graph", args))
    except Exception as e:
        return jsonify({"error": str(e)[:300]}), 500


@bp_local_query.route("/api/local/sandbox-logs/<sandbox_name>", methods=["GET"])
def http_sandbox_logs(sandbox_name: str):
    """Return OCSF sandbox audit log events for a NemoClaw sandbox.

    Queries ``events WHERE event_type='sandbox.audit_log' AND
    agent_id=<sandbox_name>``. Optional query param: ``limit`` (int,
    default 50, max 200).  Gap #3299.
    """
    try:
        limit = min(int(request.args.get("limit", 50)), 200)
        rows = local_store_via_daemon(
            "query_events",
            event_type="sandbox.audit_log",
            agent_id=sandbox_name,
            limit=limit,
        )
        if rows is None:
            rows = _store().query_events(
                event_type="sandbox.audit_log",
                agent_id=sandbox_name,
                limit=limit,
            )
        return jsonify({"events": rows or [], "sandbox": sandbox_name})
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
    # Issue #1394: per-day input/output/cache-read/cache-write token
    # split for the Tokens-tab daily chart. Replaces the legacy fast-path
    # that returned 0 for every split on real OpenClaw v3 installs.
    "query_daily_usage_splits",
    "query_heartbeats",
    "query_channels",
    # MOAT Tier-1 sweep (refs #1565): /api/flow/runs was opening DuckDB
    # directly via ``local_store.get_store(read_only=True)`` — fails on
    # multi-process installs because DuckDB's exclusive lock blocks even
    # read-only opens (per memory ``reference_duckdb_process_lock.md``).
    # Routed through the daemon proxy so the Flow tab "Past flow runs"
    # list serves fast on the standard launchd / systemd install.
    "query_flow_runs",
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
    # Context graph: decision-lineage tree (recursive subagent fan-out) for a session.
    "query_session_lineage",
    # Context graph: per-parent sub-agent cost rollup (true-cost-of-an-ask chip).
    "query_subagent_cost_rollup",
    # Context graph: the error->cause edge (failed spans + their parent).
    "query_session_errors",
    # OpenClaw run ledger (tasks/runs.sqlite mirror): sub-agents + crons +
    # CLI turns with status/timing/parent-child. Powers the Scheduler lane
    # monitor + sub-agent fan-out tree + cron run log off one source.
    "query_run_ledger",
    "query_run_ledger_lanes",
    # PRD P1-1 (governance): effective sandbox + tool policy per agent,
    # mirrored from `openclaw sandbox explain --json`. Powers the Tool Policy
    # tab (routes/policy.py:/api/tool-policy). Read-only; daemon owns writer.
    "query_tool_policy",
    # Issue #1597: parent session tool-timeline rollup needs to merge in
    # events from every child sub-agent session (the events table has no
    # parent_session_id column; the link lives on the subagents table). The
    # helper UNIONs parent + child query_events() results and tags child
    # rows with ``data._via_subagent_id``.
    "query_events_with_subagents",
    "query_memory_blobs",
    "query_system_snapshots",
    # Phase 3 (issue #1088 follow-up, 2026-05-13): per-feature aggregation
    # helpers powering the next batch of Bypass-Medium fast-paths.
    "query_compactions",
    "query_cost_split",
    # Issue #1597 class drain: sister helpers that UNION parent + child
    # sub-agent rows on per-session reads. Same pattern as
    # query_events_with_subagents — without these a parent that delegated
    # cost / model transitions to a Task-tool sub-agent reported zero on
    # the cost-split + session-model-journey routes.
    "query_cost_split_with_subagents",
    "query_session_model_journey",
    "query_session_model_journey_with_subagents",
    # Tier-1 (2026-05-15): /api/context-anatomy session-history bucket
    # off the JSONL scanner. Returns last non-zero usage.input_tokens
    # from the most-recent active session.
    "query_context_window_peek",
    # PRD P1-2 (Context Economics): per-turn context utilization over time +
    # compaction events tagged proactive/overflow + reclaimed tokens +
    # repeatedly-overflow-then-retry session flag. Powers the Context
    # Economics tab (routes/context_economics.py:/api/context-economics).
    "query_context_economics",
    # Phase 4 (issue #1088 follow-up, 2026-05-13): channel-message
    # foundation. Three helpers proved out the schema; the remaining 18
    # per-provider channel routes follow once these go green.
    "query_channel_messages",
    "query_channel_threads",
    "query_channel_summary",
    # Connector liveness (incident: node deaf ~37h, no alarm). health.py
    # reads connector.health signals via the proxy to classify each enabled
    # channel ok/degraded/down. Read-only; daemon owns the writer.
    "query_connector_health",
    # Issue #1282: NeMoClaw approvals fast-path was opening DuckDB writable
    # in routes/nemoclaw.py — collided with the daemon's writer lock.
    # Routed through proxy so /api/nemoclaw/pending-approvals stays fast.
    "query_approvals",
    # Accuracy-harness #1395 follow-up (approvals): drives ground truth
    # by calling LocalStore.ingest_approval / update_approval_decision via
    # the daemon proxy (the daemon owns the writer lock — same reason
    # query_approvals was added). Both methods are read-then-write under
    # the daemon's _write_lock, so concurrent dashboard / cloud-relay
    # decisions stay serialized.
    "ingest_approval",
    "update_approval_decision",
    # Issue #2201: asset registry (Self-Evolve findings → reviewable assets).
    # query_/get_ are reads; ingest_asset + update_asset_status are read-then-
    # write under the daemon's _write_lock — same pattern as approvals above.
    "query_assets",
    "get_asset",
    "ingest_asset",
    "update_asset_status",
    # Issue #1364: surface clawmetry/proxy.py LoopDetector signals on the
    # dashboard. Read by routes/health.py:/api/loop-signals via the daemon
    # proxy so the dashboard process never opens DuckDB writable.
    "query_recent_loop_signals",
    # Issue #1364 (MOAT 1.b): surface OTel spans we already persist.
    # Powers /api/spans + the Brain-tab "Spans" table.
    "query_recent_spans",
    # Issue #853: OTLP trace export. Full-filter variant used by
    # /api/export/traces when session_id / since / until are supplied.
    "query_spans",
    # Issue #1013: Trace 7 — one row per trace_id with aggregate stats.
    # Powers /api/local/traces + the cloud relay query.traces shape.
    "query_traces",
    # Foreign OTLP / OpenLLMetry apps (#2822 stamps agent_type from
    # service.name): a single GROUP BY agent_type rollup so the runtime
    # switcher + Agent Inventory surface a bring-your-own-agent app that only
    # ever sent OTLP traces. Daemon snapshot-path use; allowlisted so the
    # local Inventory route can read it through the proxy too.
    "query_otlp_app_rollup",
    # OTLP span WRITE-through. The /v1/traces receiver runs in the dashboard
    # process, which does not own the DuckDB writer; get_store() returns a
    # _ProxyStore that forwards put_span here so the daemon (the writer) does
    # the real INSERT. Without this allowlist entry the proxy 400s and the span
    # silently vanishes, so a "bring your own agent" OTLP app never persists or
    # appears in the switcher / Inventory. Same write-through-proxy pattern as
    # set_agent_meta. The handler calls put_span(span=...) by keyword (the proxy
    # only forwards kwargs).
    "put_span",
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
    # Issue #1364 (MOAT Tier-1): /api/plugins per-plugin invocation
    # counts. Replaces a 60-file × all-lines JSONL walk on every
    # Plugins-tab render. Returns one row per tool-call so the route can
    # bucket per-plugin counts via substring matching.
    "query_tool_call_invocations",
    # Issue #1707 — forward-progress signal. Tokens-per-state-delta per
    # session, computed off the events table. Powers /api/forward-progress
    # + the Brain-tab Progress badge.
    "query_forward_progress",
    # Weekly Insights Digest (feat/insights-v1): one allowlisted entry-point
    # for the 10 hand-authored canned-query templates in clawmetry/insights.py.
    # SQL goes through clawmetry/dives_sql_safety.validate_sql() inside the
    # method — SELECT/WITH only, no DDL/DML, no file/HTTP/attach functions.
    "raw_select_safe",
    # Issue #1615 — decision sampling workflow. Four review-queue methods
    # exposed through the daemon proxy so /api/review/* in the dashboard
    # process can hit the writer-locked DuckDB.
    "ingest_review_sample",
    "update_review_decision",
    "query_review_queue",
    "query_review_accuracy",
    # Issue #1614 — per-session outcome labels (success/failed/escalated/
    # ongoing) for the Overview tile + /api/outcomes endpoint. Inline-
    # classifies any unlabeled rows so the dashboard never paints "0%".
    "query_outcomes",
    "reclassify_session_outcome",
    # Issue #1619 Phase 1: LLM-as-judge eval surface. Reads + the persist
    # write all go via the daemon (writer-lock owner) so the dashboard
    # process can render scores without opening DuckDB itself.
    "query_unscored_sessions",
    "query_recent_evals",
    "query_eval_summary",
    "persist_eval_score",
    # Eval->monitor loop: per-session eval/outcome fields for the two runs in
    # /api/run-compare's quality rows. Read-only; routed through the daemon
    # proxy so the dashboard process never opens the writer-locked DuckDB.
    "query_session_quality",
    "health",
    # Issue #876 — NemoClaw guardrail enforcement events + metrics.
    # Routed through the daemon proxy so /api/nemoclaw/events and
    # /api/nemoclaw/metrics never open DuckDB writable in the dashboard
    # process (same pattern as query_approvals above).
    "query_guardrail_events",
    "ingest_guardrail_event",
    "query_nemoclaw_metrics",
    # Issue #2200 — tamper-evident hash chain verifier. `clawmetry
    # verify-integrity` calls this through the daemon proxy when a daemon
    # is running (the daemon holds DuckDB's process-level writer lock so
    # the CLI cannot open the file directly, even read-only). Without
    # this entry the proxy returns None and the CLI crashed on
    # `result["status"]`. Read-only walk over the events table.
    "verify_integrity",
    # Issue #2196 item #5 — per-event resolved-error triage. Writes need the
    # daemon's writer connection; the read returns a {event_id: {...}} map
    # used by /api/error-triage/resolved + future "exclude resolved from
    # error counts" filtering.
    "mark_error_resolved",
    "unmark_error_resolved",
    "query_resolved_errors",
    # Issue #883: external API tracing. Read-only; the daemon owns the writer
    # connection so the proxy is required for multi-process installs.
    "query_external_calls",
    # Agent Inventory tab: owner/notes labels per runtime. query_ is a read,
    # set_ is a read-then-write under the daemon's _write_lock (same pattern as
    # ingest_approval above). Without these the inventory owner read/write
    # returns None and the proxy 400s (memory feedback_cli_methods_need_daemon_allowlist).
    "query_agent_meta",
    "set_agent_meta",
    # Issue #2860: session full-text search. Read-only; routed through the
    # daemon proxy so the dashboard process never opens DuckDB writable.
    "query_search",
    # #2988 (Query Spine P2): materialized rollup reads. The daemon writes
    # the rollup tables at ingest; these are the read methods backing the
    # q/1 "models" / "runtimes" / "rollup_sessions" contract shapes.
    "query_rollup_model_daily",
    "query_rollup_runtime_daily",
    "query_rollup_sessions",
    # Issue #999 DIVES-6: log Dives query telemetry via the daemon's writer
    # connection so the dashboard process can fire-and-forget without opening
    # DuckDB writable itself.
    "ingest_dive_run",
    # Efficiency grade + measured savings (feat/efficiency-grade): trailing-
    # window per-(runtime, model) aggregate over rollup_model_daily, read by
    # routes/usage.py:/api/efficiency through the daemon proxy (read-only;
    # the daemon owns the writer lock).
    "query_efficiency_rollup",
    # Issue #2861 -- version-aware health regression. Read-only join of
    # sessions + heartbeats; routed through the daemon proxy so the
    # dashboard process never opens DuckDB writable.
    "query_version_health",
    # Issue #3302 — security threat events. ingest_ is a write (called from
    # /api/security/threats after each scan); query_ is read-only (serves
    # /api/security-threats on the Health tab). Both routed through the daemon
    # proxy so the dashboard process never opens DuckDB writable.
    "ingest_security_event",
    "query_security_events",
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
        body = _urlopen_retry(req)
    except (urllib.error.URLError, OSError, ValueError):
        # Stale port / daemon restarted / network gremlin (after retrying
        # timeouts) — drop the cache so the next call re-reads discovery.
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
