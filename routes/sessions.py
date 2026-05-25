"""
routes/sessions.py — Session / transcript / sub-agent API endpoints.

Extracted from dashboard.py as the first step of an incremental modularisation.
This Blueprint owns the 13 HTTP routes that power the Sessions tab, the
transcript viewer, the sub-agent tree, the cost-split view, OTLP export,
and emergency session-stop.

All module-level helpers (``_get_sessions``, ``_augment_sessions_with_burn``,
``_gw_invoke``, ``_compute_transcript_analytics``, ``SESSIONS_DIR`` etc.) remain
in ``dashboard.py``. Each route handler does a late ``import dashboard as _d``
so we avoid a circular import at module-load time, matching the convention
used by ``clawmetry-cloud/routes/cloud.py``.

Pure mechanical move — zero behaviour change from the previous in-file
definitions.
"""

import json
import os
import re
import re as _re
import sys
import time
from datetime import datetime

import csv
from datetime import timezone
from flask import Blueprint, jsonify, request, Response
from clawmetry.config import is_local_store_read_enabled, hide_clawmetry_session
from routes._dedupe import build_sibling_bucket_max, is_sibling_dup

bp_sessions = Blueprint('sessions', __name__)

_SUBAGENTS_CACHE = {"ts": 0.0, "data": None}
_SUBAGENTS_CACHE_TTL_SECONDS = 10
_SUBAGENTS_SCAN_MAX_FILES = int(os.environ.get("CLAWMETRY_SUBAGENTS_SCAN_MAX_FILES", "120"))
_SUBAGENTS_SCAN_TAIL_BYTES = int(os.environ.get("CLAWMETRY_SUBAGENTS_SCAN_TAIL_BYTES", str(512 * 1024)))

# Channels that don't identify a user-initiated session (generic/internal)
_GENERIC_CHANNELS = frozenset({"unknown", "direct", "", "main", "internal"})


def _ls_call(method_name, **kwargs):
    """Cross-process LocalStore call with single-process fallback.

    Issue #1088: every direct ``get_store().query_*`` call is dead code in
    the standard install (daemon owns the writer lock, dashboard's open
    raises ``IOException: Could not set lock``). This wrapper hits the
    daemon's HTTP proxy first, then falls back to direct open for
    single-process boots (tests + dev mode). Returns ``None`` on miss so
    callers can defer to the legacy fallback path.
    """
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


def _infer_session_type(session):
    """Classify a session into one of: main / heartbeat / user / sub-agent.

    Priority:
      1. display name / session id contains "heartbeat"  → heartbeat
      2. gateway kind == "subagent" or name contains it  → sub-agent
      3. channel is set and non-generic                  → user
      4. fallback                                        → main
    """
    name = (session.get("displayName") or session.get("sessionId") or "").lower()
    kind = (session.get("kind") or "").lower()
    channel = (session.get("channel") or "").lower().strip()

    if "heartbeat" in name:
        return "heartbeat"
    if kind == "subagent" or "subagent" in name:
        return "sub-agent"
    if channel and channel not in _GENERIC_CHANNELS:
        return "user"
    return "main"


def _get_channel_context_map(session_ids=None):
    """Return ``{session_id: {channel, chat_type, subject, origin_label}}``
    from the local DuckDB ``openclaw_channels`` table.

    The table is the canonical, typed source for OpenClaw channel attribution
    (Telegram/Slack/Signal/etc.) — populated by the gateway adapter via
    ``LocalStore.ingest_channel()``. Today the legacy path infers channel
    from a free-form ``metadata`` blob; this helper lets the local-store fast
    path enrich session rows with the cleaner table when it has data.

    Args:
      session_ids: Optional iterable to scope the lookup. ``None`` returns
        all rows (cheap — table is one row per session, capped well under
        the default ``query_channels(limit=500)``).

    Returns ``{}`` (no decoration) on any failure — the local-store module
    not being importable, the table being empty, or any DuckDB error. The
    caller treats an empty dict as "nothing to merge", which preserves the
    pre-existing metadata-blob channel inference unchanged.
    """
    # Issue #1277: route through daemon HTTP proxy. Direct
    # local_store.get_store() raises IOException on multi-process installs
    # (DuckDB process-level file lock), and even when the exception is
    # caught the singleton ends up in a degraded state — surfaces as the
    # 3–10 s cumulative latency on /api/sessions despite the underlying
    # DuckDB query being 6 ms. Same root cause as the #1256 endpoint family.
    #
    # Plus: even on the happy path, query_channels(session_id=X) was
    # invoked N times in a loop. Switch to a single full-table fetch (the
    # in-line dict-build below scopes the result to the requested ids
    # client-side). Channels table is always small (one row per channel
    # per session — capped well under the 2000 limit), so a full scan is
    # cheaper than N proxy round-trips even at small N.
    rows = None
    try:
        from routes.local_query import local_store_via_daemon
        rows = local_store_via_daemon("query_channels", limit=2000)
    except Exception:
        rows = None
    if rows is None:
        # Single-process fallback (tests + dev mode).
        try:
            from clawmetry import local_store
            store = local_store.get_store(read_only=True)
            rows = store.query_channels(limit=2000)
        except Exception:
            return {}
    # Scope the full-table result to requested session_ids client-side.
    wanted = None
    if session_ids is not None:
        wanted = {s for s in session_ids if s}
        if not wanted:
            return {}
    out = {}
    for r in (rows or []):
        sid = r.get("session_id")
        if not sid:
            continue
        if wanted is not None and sid not in wanted:
            continue
        out[sid] = {
            "channel":      r.get("channel") or "",
            "chat_type":    r.get("chat_type") or "",
            "subject":      r.get("subject") or "",
            "origin_label": r.get("origin_label") or "",
        }
    return out


def _decorate_with_channel_context(sessions):
    """Mutate ``sessions`` in place, overriding empty channel/chat_type/subject
    fields with values from the ``openclaw_channels`` table when present.

    No-op when the table has no matching rows for any session in the list —
    keeps existing values (typically inferred from the metadata blob)
    unchanged. The override is one-way: only blank-on-the-row fields get
    filled in, so a metadata-blob channel from the legacy path survives if
    the channels table has nothing for that session.
    """
    if not sessions:
        return sessions
    ids = [s.get("session_id") or s.get("sessionId") for s in sessions]
    ctx_map = _get_channel_context_map(ids)
    if not ctx_map:
        return sessions
    for s in sessions:
        sid = s.get("session_id") or s.get("sessionId")
        ctx = ctx_map.get(sid)
        if not ctx:
            continue
        # Prefer the typed table value over an empty/blank existing field.
        if ctx["channel"] and not s.get("channel"):
            s["channel"] = ctx["channel"]
        if ctx["chat_type"] and not s.get("chat_type"):
            s["chat_type"] = ctx["chat_type"]
        if ctx["subject"] and not s.get("subject"):
            s["subject"] = ctx["subject"]
        if ctx["origin_label"] and not s.get("origin_label"):
            s["origin_label"] = ctx["origin_label"]
    return sessions


def _session_last_active_epoch(s: dict):
    """Extract a unix-second timestamp for a session row, tolerant of the
    many shapes the gateway / local-store / JSONL paths produce.

    Returns ``None`` when no usable timestamp is present (in which case
    the row stays visible — we never drop on missing data, only on data
    that *proves* the session is older than the cap).
    """
    # epoch-millis fields (gateway, unregistered-JSONL backfill)
    for k in ("updatedAt", "lastActivityAt", "last_active_at_ms"):
        v = s.get(k)
        if isinstance(v, (int, float)) and v > 0:
            return float(v) / 1000.0 if v > 1e12 else float(v)
    # ISO-8601 fields (local-store path)
    for k in ("last_active_at", "updated_at", "started_at"):
        v = s.get(k)
        if isinstance(v, str) and v:
            try:
                iso = v.replace("Z", "+00:00")
                return datetime.fromisoformat(iso).timestamp()
            except (ValueError, TypeError):
                continue
    return None


def _apply_24h_retention_cap(sessions: list) -> bool:
    """Drop sessions older than 24h for OSS / Cloud-Free callers (issue #1448).

    Cloud-Pro users (validated by ``dashboard._is_pro_user``) bypass the cap.
    Mutates ``sessions`` in place. Returns ``True`` when the cap kicked in
    (i.e. caller was non-Pro) so the UI can render the upgrade CTA.

    Mirrors the gating pattern introduced for /api/flow/runs in PR #1445.
    """
    try:
        import dashboard as _d
        is_pro = bool(_d._is_pro_user())
    except Exception:
        is_pro = False
    if is_pro:
        return False
    cap_floor = time.time() - 24 * 3600
    kept = []
    for s in sessions:
        ts = _session_last_active_epoch(s)
        if ts is None or ts >= cap_floor:
            kept.append(s)
    sessions[:] = kept
    return True


@bp_sessions.route("/api/sessions")
def api_sessions():
    import dashboard as _d
    # Epic #964 PR 3: opt-in local-store fast path. When
    # CLAWMETRY_LOCAL_STORE_READ=1 AND the local sessions table has rows,
    # serve directly from DuckDB. Falls through to gateway/JSONL otherwise
    # (so a fresh install with no local store, or a non-OpenClaw user, sees
    # the same data as before — zero-change default).
    if is_local_store_read_enabled():
        fast = _try_local_store_sessions()
        if fast is not None:
            _merge_unregistered_jsonls(fast["sessions"])
            capped = _apply_24h_retention_cap(fast["sessions"])
            fast["capped_at_24h"] = capped
            # Issue #1773: honest envelope marker. The fast path tags itself
            # local_store, but _merge_unregistered_jsonls may have appended
            # filesystem_unregistered rows. Recompute from the row markers so
            # operators see the actual data path (vs. a misleading
            # "local_store" envelope that hides an ingest outage).
            fast["_source"] = _derive_envelope_source(
                fast["sessions"], fallback="local_store"
            )
            fast["sessions"] = _filter_internal_sessions(fast["sessions"])
            return jsonify(fast)
    gw_data = _d._gw_invoke("sessions_list", {"limit": 20, "messageLimit": 0})
    if gw_data and "sessions" in gw_data:
        sessions = _d._augment_sessions_with_burn(gw_data["sessions"])
    else:
        sessions = _d._augment_sessions_with_burn(_d._get_sessions())
    # Same env-gate as the fast path: when the user has opted into local-store
    # reads, decorate gateway/JSONL session rows with channel context from the
    # typed openclaw_channels table. Lets a partially-migrated install (sessions
    # still from gateway, channels already in DuckDB) get typed channel/chat_type/
    # subject without waiting for the full session-table cutover.
    if is_local_store_read_enabled():
        _decorate_with_channel_context(sessions)
    for s in sessions:
        if "session_type" not in s:
            s["session_type"] = _infer_session_type(s)
    # Backfill: union with raw JSONL files on disk. The gateway / sessions.json
    # index can lag behind the filesystem (a brand-new session writes its
    # JSONL immediately but only registers in sessions.json once OpenClaw's
    # registrar runs). Without this merge those sessions stay invisible until
    # the registrar catches up — see MOAT_E2E_REPORT_2026-05-13 root-cause #3.
    _merge_unregistered_jsonls(sessions)
    sessions = _filter_internal_sessions(sessions)
    capped = _apply_24h_retention_cap(sessions)
    return jsonify({"sessions": sessions, "capped_at_24h": capped})


def _filter_internal_sessions(rows: list) -> list:
    """Drop ClawMetry's own helper sessions (clawmetry-fix / -selfevolve /
    -mem-probe …) from a session-row list so our plumbing doesn't mix with the
    user's agent activity. Honors CLAWMETRY_SHOW_INTERNAL_SESSIONS=1."""
    out = []
    for s in rows or []:
        if not isinstance(s, dict):
            out.append(s)
            continue
        sid = (
            s.get("sessionId") or s.get("id") or s.get("session_id") or s.get("key")
        )
        if hide_clawmetry_session(sid):
            continue
        out.append(s)
    return out


def _derive_envelope_source(rows: list, fallback: str = "local_store") -> str:
    """Compute an honest envelope ``_source`` from per-row markers.

    Issue #1773: ``/api/sessions`` (and any other route that unions multiple
    backends) used to hard-code ``_source: "local_store"`` at the envelope
    while individual rows might carry a different per-row marker
    (e.g. ``filesystem_unregistered`` from the JSONL fallback). That misled
    operators into thinking DuckDB was the source of truth when an ingest
    outage had silently demoted the response to a filesystem scan.

    Returns:
      - ``fallback`` when ``rows`` is empty (nothing to derive from).
      - The single source string when every row agrees.
      - ``"mixed:a,b,..."`` (sources sorted alphabetically) when rows disagree.

    Rows without a ``_source`` key are treated as ``fallback`` so we don't
    over-claim purity for rows that simply forgot to tag themselves.
    """
    if not rows:
        return fallback
    sources = set()
    for r in rows:
        if not isinstance(r, dict):
            continue
        src = r.get("_source") or fallback
        sources.add(src)
    if not sources:
        return fallback
    if len(sources) == 1:
        return next(iter(sources))
    return "mixed:" + ",".join(sorted(sources))


def _merge_unregistered_jsonls(sessions: list) -> None:
    """Append a minimal record for any ``<uuid>.jsonl`` in the sessions dir
    that isn't already represented in ``sessions``. Mutates the list in place.

    These rows carry ``displayName='(unregistered)'`` and ``session_type='main'``
    so the UI can flag them. We deliberately don't re-scan the full transcript
    here (cheap mtime/size only) — once the registrar catches up, the next
    request returns the proper row.
    """
    import dashboard as _d
    try:
        base = _d._get_sessions_dir()
    except Exception:
        return
    if not base or not os.path.isdir(base):
        return
    known: set = set()
    for s in sessions:
        for k in ("sessionId", "session_id", "key"):
            v = s.get(k)
            if isinstance(v, str) and v and "..." not in v:
                known.add(v)
    try:
        entries = os.listdir(base)
    except OSError:
        return
    for fname in entries:
        if not fname.endswith(".jsonl") or "deleted" in fname or ".trajectory." in fname:
            continue
        sid = fname[:-len(".jsonl")]
        if sid in known:
            continue
        fpath = os.path.join(base, fname)
        try:
            mtime = os.path.getmtime(fpath)
        except OSError:
            continue
        sessions.append({
            "sessionId":     sid,
            "session_id":    sid,
            "key":           sid[:12] + "...",
            "displayName":   "(unregistered)",
            "title":         "(unregistered)",
            "updatedAt":     int(mtime * 1000),
            "last_active_at": datetime.fromtimestamp(mtime, tz=timezone.utc).isoformat(),
            "model":         "unknown",
            "channel":       "unknown",
            "totalTokens":   0,
            "total_tokens":  0,
            "total_cost":    0.0,
            "message_count": 0,
            "session_type":  "main",
            "_source":       "filesystem_unregistered",
        })


def _fetch_sessions_table_rows(limit: int = 200):
    """Cross-process fetch from the typed ``sessions`` DuckDB table.

    Returns a list of dict rows (with ``metadata`` already JSON-decoded), or
    ``None`` to defer. Tries the daemon HTTP proxy FIRST (issue #1088 — the
    standard install runs daemon + dashboard as separate processes and
    DuckDB's exclusive lock blocks direct opens), then falls back to a
    direct ``get_store()`` open for single-process boots (tests + dev mode).
    """
    # 1. Cross-process: ask the daemon over HTTP.
    try:
        from routes.local_query import local_store_via_daemon
        rows = local_store_via_daemon("query_sessions_table", limit=limit)
        if rows is not None:
            return rows
    except Exception:
        pass
    # 2. Single-process fallback: open the DuckDB ourselves. Only works
    #    when no other process holds the writer lock. Issue #1240: open
    #    read-only so we don't pay DuckDB's ~2.5s writer-lock-retry budget
    #    when the daemon does own the writer lock (the daemon proxy attempt
    #    above will have already failed in that case, so we get here, and
    #    the RO open shares the writer's connection cleanly).
    try:
        from clawmetry import local_store
        return local_store.get_store(read_only=True).query_sessions_table(limit=limit)
    except Exception:
        return None


def _try_local_store_sessions():
    """Read sessions directly from the local DuckDB. Returns the same
    response shape as the legacy gateway-backed endpoint (`{"sessions":
    [...]}`). Returns ``None`` to defer to the JSONL/gateway fallback if:
      - the local_store module isn't importable / daemon unreachable
      - the sessions table is empty
      - any unexpected error happens (we'd rather degrade than 500)
    """
    rows = _fetch_sessions_table_rows(limit=200)
    if not rows:
        return None
    out = []
    for r in rows:
        meta = r.get("metadata") or {}
        title = r.get("title") or ""
        out.append({
            "agent_type":     r.get("agent_type"),
            "session_id":     r.get("session_id"),
            "agent_id":       r.get("agent_id"),
            "title":          title,
            "started_at":     r.get("started_at") or "",
            "updated_at":     r.get("last_active_at") or "",
            "ended_at":       r.get("ended_at") or "",
            "status":         r.get("status") or "",
            "total_tokens":   int(r.get("total_tokens") or 0),
            "total_cost":     float(r.get("cost_usd") or 0.0),
            "message_count":  int(r.get("message_count") or 0),
            "channel":        meta.get("channel", ""),
            "chat_type":      meta.get("chat_type", ""),
            "subject":        title or meta.get("subject", ""),
            "session_type":   meta.get("session_type", "main"),
            "_source":        "local_store",
        })
    # Decorate with channel context from the typed openclaw_channels table.
    # No-op when the table is empty; overrides only blank fields when present.
    _decorate_with_channel_context(out)
    return {"sessions": out, "_source": "local_store"}


@bp_sessions.route("/api/sessions/by-type")
def api_sessions_by_type():
    """Return sessions grouped by type with per-type counts.

    Response:
      {
        "counts": {"main": N, "heartbeat": N, "user": N, "sub-agent": N, "total": N},
        "sessions": [<session objects with session_type field>]
      }

    Optional query param ?type=<heartbeat|user|sub-agent|main> to filter the
    returned session list (counts always cover all sessions).
    """
    import dashboard as _d
    type_filter = request.args.get("type", "").strip()

    # Epic #964: opt-in local-store fast path. Mirrors /api/sessions — when
    # CLAWMETRY_LOCAL_STORE_READ=1 AND the local sessions table has rows,
    # serve directly from DuckDB. Falls through to gateway/JSONL otherwise.
    if is_local_store_read_enabled():
        fast = _try_local_store_sessions_by_type(type_filter)
        if fast is not None:
            return jsonify(fast)

    gw_data = _d._gw_invoke("sessions_list", {"limit": 50, "messageLimit": 0})
    if gw_data and "sessions" in gw_data:
        sessions = _d._augment_sessions_with_burn(gw_data["sessions"])
    else:
        sessions = _d._augment_sessions_with_burn(_d._get_sessions())

    for s in sessions:
        if "session_type" not in s:
            s["session_type"] = _infer_session_type(s)

    counts = {"main": 0, "heartbeat": 0, "user": 0, "sub-agent": 0}
    for s in sessions:
        t = s.get("session_type", "main")
        counts[t] = counts.get(t, 0) + 1
    counts["total"] = len(sessions)

    filtered = [
        s for s in sessions
        if not type_filter or s.get("session_type") == type_filter
    ]
    return jsonify({"counts": counts, "sessions": filtered})


def _try_local_store_sessions_by_type(type_filter: str = ""):
    """By-type variant of :func:`_try_local_store_sessions`.

    Reads sessions from the local DuckDB and computes the same
    ``{"counts": {...}, "sessions": [...]}`` shape the legacy gateway/JSONL
    path returns. ``type_filter`` (``main``/``heartbeat``/``user``/``sub-agent``
    or empty for all) only narrows the ``sessions`` list — ``counts`` always
    covers every row in the local store.

    Returns ``None`` to defer to the legacy fallback if:
      - the ``local_store`` module isn't importable
      - the sessions table is empty (fresh install / non-OpenClaw user)
      - any unexpected error happens (we'd rather degrade than 500)
    """
    # Issue #1282 (final callsite): replace the inline raw ``_fetch`` SELECT —
    # which forced a writable ``get_store()`` open and raced the sync daemon's
    # exclusive DuckDB writer lock — with ``query_sessions_table`` via the
    # daemon HTTP proxy. ``query_sessions_table`` already in
    # ``_DAEMON_METHODS`` allowlist; returns dict-shaped rows with metadata
    # JSON-decoded so we can drop the manual tuple-indexing + bytes-decode.
    rows = None
    try:
        from routes.local_query import local_store_via_daemon
        rows = local_store_via_daemon("query_sessions_table", limit=200)
    except Exception:
        rows = None
    if rows is None:
        try:
            from clawmetry import local_store
            store = local_store.get_store(read_only=True)
            rows = store.query_sessions_table(limit=200)
        except Exception:
            return None
    if not rows:
        return None

    sessions = []
    explicit_types: dict[str, str] = {}
    for r in rows:
        meta = r.get("metadata") if isinstance(r.get("metadata"), dict) else {}
        s = {
            "agent_type":     r.get("agent_type"),
            "session_id":     r.get("session_id"),
            "agent_id":       r.get("agent_id"),
            "title":          r.get("title") or "",
            "started_at":     r.get("started_at") or "",
            "updated_at":     r.get("last_active_at") or "",
            "ended_at":       r.get("ended_at") or "",
            "status":         r.get("status") or "",
            "total_tokens":   int(r.get("total_tokens") or 0),
            "total_cost":     float(r.get("cost_usd") or 0.0),
            "message_count":  int(r.get("message_count") or 0),
            "channel":        meta.get("channel", ""),
            "chat_type":      meta.get("chat_type", ""),
            "subject":        r.get("title") or meta.get("subject", ""),
            "displayName":    r.get("title") or "",
            "kind":           meta.get("kind", ""),
            "_source":        "local_store",
        }
        if meta.get("session_type"):
            explicit_types[s["session_id"]] = meta["session_type"]
        sessions.append(s)
    # Decorate channel context BEFORE _infer_session_type so a session with
    # channel=telegram (typed table) classifies as "user" even if the metadata
    # blob never carried a channel field.
    _decorate_with_channel_context(sessions)
    for s in sessions:
        # Honour explicit metadata.session_type when present; otherwise
        # classify with the same _infer_session_type() the legacy path uses.
        s["session_type"] = explicit_types.get(s["session_id"]) or _infer_session_type(s)

    counts = {"main": 0, "heartbeat": 0, "user": 0, "sub-agent": 0}
    for s in sessions:
        t = s.get("session_type", "main")
        counts[t] = counts.get(t, 0) + 1
    counts["total"] = len(sessions)

    filtered = [
        s for s in sessions
        if not type_filter or s.get("session_type") == type_filter
    ]
    return {"counts": counts, "sessions": filtered, "_source": "local_store"}


def _try_local_store_compactions(wanted_sid: str, summary_chars: int, full_summary: bool):
    """Fast path for /api/compactions. Reads compaction events from DuckDB
    via :meth:`LocalStore.query_compactions` and projects them into the
    same shape the JSONL scanner returns.

    Issue #1088 phase 3. Returns ``None`` when the events table has no
    ``compaction`` rows so the route falls through to the JSONL scan."""
    rows = _ls_call(
        "query_compactions",
        session_id=wanted_sid or None,
        limit=1000,
    )
    if not rows:
        return None
    compactions: list = []
    total_tokens = 0
    for r in rows:
        ts = r.get("timestamp") or ""
        ts_ms = 0
        if isinstance(ts, str) and ts:
            try:
                ts_ms = int(
                    datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp() * 1000
                )
            except Exception:
                ts_ms = 0
        summary = r.get("summary") or ""
        tokens_before = int(r.get("tokens_before") or 0)
        total_tokens += tokens_before
        entry = {
            "session_id":          r.get("session_id") or "",
            "timestamp":           ts,
            "ts_ms":               ts_ms,
            "tokens_before":       tokens_before,
            "first_kept_entry_id": r.get("first_kept_entry_id") or "",
            "from_hook":           bool(r.get("from_hook")),
        }
        if full_summary or len(summary) <= summary_chars:
            entry["summary"] = summary
        else:
            entry["summary"] = summary[:summary_chars]
            entry["summary_truncated"] = True
        compactions.append(entry)
    compactions.sort(key=lambda c: c.get("ts_ms", 0), reverse=True)
    return {
        "compactions":            compactions,
        "total_compactions":      len(compactions),
        "total_tokens_compacted": total_tokens,
        "_source":                "local_store",
    }


@bp_sessions.route("/api/compactions")
def api_compactions():
    """Return OpenClaw session-compaction events.

    OpenClaw compacts long sessions: when context fills up, it summarises
    earlier messages into a markdown `summary` and drops the originals.
    The compaction summary is often the single best "what did my agent do"
    artifact for a long session — we weren't surfacing any of it.

    Params:
      session_id (optional): filter to one session; returns full summary text.
      summary_chars (optional, default=500 when no session_id): truncate
        `summary` to this many chars to keep list responses compact.
    """
    import dashboard as _d
    wanted_sid = request.args.get("session_id", "").strip()
    try:
        summary_chars = max(100, min(int(request.args.get("summary_chars", "500")), 50000))
    except ValueError:
        summary_chars = 500
    full_summary = bool(wanted_sid)

    if is_local_store_read_enabled():
        fast = _try_local_store_compactions(wanted_sid, summary_chars, full_summary)
        if fast is not None:
            return jsonify(fast)

    sessions_dir = _d.SESSIONS_DIR or os.path.expanduser(
        "~/.openclaw/agents/main/sessions"
    )
    if not os.path.isdir(sessions_dir):
        return jsonify({
            "compactions": [],
            "total_compactions": 0,
            "total_tokens_compacted": 0,
            "note": "sessions dir not found",
        })

    try:
        all_files = [
            f
            for f in os.listdir(sessions_dir)
            if f.endswith(".jsonl") and ".deleted." not in f and ".reset." not in f
        ]
    except OSError:
        all_files = []

    if wanted_sid:
        files = [f for f in all_files if f.startswith(wanted_sid)]
    else:
        files = sorted(
            all_files,
            key=lambda f: os.path.getmtime(os.path.join(sessions_dir, f)),
            reverse=True,
        )[:100]

    compactions: list = []
    total_tokens = 0
    for fname in files:
        fpath = os.path.join(sessions_dir, fname)
        sid = fname[:-len(".jsonl")] if fname.endswith(".jsonl") else fname
        try:
            with open(fpath, "r", errors="replace") as fh:
                for raw in fh:
                    raw = raw.strip()
                    if not raw or '"compaction"' not in raw:
                        continue
                    try:
                        ev = json.loads(raw)
                    except Exception:
                        continue
                    if ev.get("type") != "compaction":
                        continue
                    ts = ev.get("timestamp", "")
                    ts_ms = 0
                    if isinstance(ts, str) and ts:
                        try:
                            from datetime import datetime as _dt
                            ts_ms = int(
                                _dt.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
                                * 1000
                            )
                        except Exception:
                            ts_ms = 0
                    summary = ev.get("summary", "") or ""
                    tokens_before = int(ev.get("tokensBefore", 0) or 0)
                    total_tokens += tokens_before
                    entry = {
                        "session_id": sid,
                        "timestamp": ts,
                        "ts_ms": ts_ms,
                        "tokens_before": tokens_before,
                        "first_kept_entry_id": ev.get("firstKeptEntryId", "") or "",
                        "from_hook": bool(ev.get("fromHook", False)),
                    }
                    if full_summary or len(summary) <= summary_chars:
                        entry["summary"] = summary
                    else:
                        entry["summary"] = summary[:summary_chars]
                        entry["summary_truncated"] = True
                    compactions.append(entry)
        except Exception:
            continue

    compactions.sort(key=lambda c: c.get("ts_ms", 0), reverse=True)
    return jsonify({
        "compactions": compactions,
        "total_compactions": len(compactions),
        "total_tokens_compacted": total_tokens,
    })


def _try_local_store_session_tools(sid: str, args_chars: int, result_chars: int,
                                   include_unpaired: bool):
    """Fast path for /api/session-tools. Reads message events for one
    session from DuckDB and pairs ``toolCall`` / ``toolResult`` blocks into
    the same timeline shape the JSONL parser returns.

    Issue #1088 phase 3. Returns ``None`` to defer to the JSONL parser
    when the events table has no message rows for this session.

    Issue #1597: ALSO unions in events from any sub-agent session whose
    ``subagents.parent_session_id`` matches ``sid`` — without this a
    parent that delegated tool calls to a child rendered ``tool_calls=0``.
    Sub-agent events are tagged with ``data._via_subagent_id`` upstream
    so the resulting ``tools[]`` rows carry the same marker for the UI.
    """
    rows = _ls_call("query_events_with_subagents", session_id=sid, limit=10000)
    # Pre-1597 daemons (older wheel running, fresh dashboard) won't have the
    # helper allowlisted yet — fall back to the parent-only query so the
    # endpoint still works during a staged rollout. The rollup will simply
    # under-report sub-agent activity until the daemon is restarted.
    if rows is None:
        rows = _ls_call("query_events", session_id=sid, limit=10000)
    if not rows:
        return None
    rows = list(reversed(rows))  # query_events returns DESC

    def _parse_ts(ts):
        if not ts or not isinstance(ts, str):
            return 0
        try:
            return int(datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp() * 1000)
        except Exception:
            return 0

    def _truncate(val, limit):
        if limit <= 0 or val is None:
            return val
        if isinstance(val, str):
            return val if len(val) <= limit else val[:limit] + "…"
        try:
            s = json.dumps(val, separators=(",", ":"))
        except Exception:
            s = str(val)
        return s if len(s) <= limit else s[:limit] + "…"

    # v3 turn / lifecycle event types — presence of ANY of these in DuckDB
    # for the session means the daemon HAS ingested it. We must therefore
    # serve from the fast path even when there are zero tool calls, so the
    # legacy JSONL fallback is reserved for genuinely missing-from-DuckDB
    # sessions. See reference_openclaw_v3_event_types.md.
    _V3_TURN_TYPES = frozenset({
        "session.started", "prompt.submitted", "model.completed",
        "model.changed", "tool.call", "tool.result", "tool_use",
        "tool_use_result", "custom",
    })

    calls: dict = {}
    result_by_id: dict = {}
    turn_index = 0
    saw_any = False
    earliest_ts_ms = 0
    for ev in rows:
        et = ev.get("event_type")
        data = ev.get("data") if isinstance(ev.get("data"), dict) else {}
        # Issue #1597: events sourced from a child sub-agent session are
        # tagged by ``LocalStore.query_events_with_subagents`` so the
        # rollup can attribute them in the UI ("via sub-agent X").
        via_subagent_id = data.get("_via_subagent_id") if isinstance(data, dict) else None
        ev_ts_ms = _parse_ts(
            (data.get("timestamp") if isinstance(data, dict) else None)
            or ev.get("ts")
        )
        if ev_ts_ms and (earliest_ts_ms == 0 or ev_ts_ms < earliest_ts_ms):
            earliest_ts_ms = ev_ts_ms

        # Any recognised v3 lifecycle / turn event proves the daemon has
        # ingested this session. Mark saw_any so we return a populated
        # (possibly tool-empty) structure instead of falling back to JSONL.
        if et in _V3_TURN_TYPES:
            saw_any = True

        # v3 standalone tool_call row: self-contained call+result pair.
        # Accepts the legacy ``tool_call`` name AND the daemon-normalised
        # ``tool.call`` dot.separated name. Synthesize a tcid from the
        # event id so the pairing logic below treats it as an
        # immediately-resolved call.
        if et in ("tool_call", "tool.call"):
            turn_index += 1
            tcid = ev.get("id") or f"tc-{ev_ts_ms}-{len(calls)}"
            tool_name = ""
            args_val = None
            result_val = None
            is_error = False
            if isinstance(data, dict):
                tool_name = (data.get("tool") or data.get("tool_name")
                             or data.get("name") or "")
                args_val = (data.get("args") if data.get("args") is not None
                            else data.get("arguments") if data.get("arguments") is not None
                            else data.get("input"))
                result_val = data.get("result")
                is_error = bool(data.get("is_error") or data.get("isError")
                                or data.get("error"))
            calls[tcid] = {
                "tool_call_id":     tcid,
                "tool_name":        tool_name,
                "arguments":        _truncate(args_val, args_chars),
                "start_ms":         ev_ts_ms,
                "turn_index":       turn_index,
                "model":            ev.get("model") or "",
                "provider":         (data.get("provider") if isinstance(data, dict) else "") or "",
                "message_cost_usd": float(ev.get("cost_usd") or 0.0),
                "via_subagent_id":  via_subagent_id or "",
            }
            if result_val is not None or is_error:
                try:
                    rs = len(json.dumps(result_val, separators=(",", ":")))
                except Exception:
                    rs = len(str(result_val or ""))
                result_by_id[tcid] = {
                    "end_ms":         ev_ts_ms,
                    "is_error":       is_error,
                    "result_size":    rs,
                    "result_preview": _truncate(result_val, result_chars),
                }
            continue

        # v3 tool result event: pairs with a prior tool_use block by id.
        # Daemon-normalised name is ``tool.result``; ``tool_use_result``
        # is the raw v3 source type (rarely makes it through, but accept
        # both for safety).
        if et in ("tool.result", "tool_use_result"):
            tcid = (data.get("tool_use_id") or data.get("toolUseId")
                    or data.get("id") or "")
            if tcid:
                result_val = (data.get("output") if data.get("output") is not None
                              else data.get("result"))
                is_error = bool(data.get("is_error") or data.get("isError"))
                try:
                    rs = len(json.dumps(result_val, separators=(",", ":")))
                except Exception:
                    rs = len(str(result_val or ""))
                result_by_id[tcid] = {
                    "end_ms":         ev_ts_ms,
                    "is_error":       is_error,
                    "result_size":    rs,
                    "result_preview": _truncate(result_val, result_chars),
                }
            continue

        # v3 assistant turn (``model.completed``): tool invocations live as
        # Anthropic-style ``tool_use`` blocks inside ``data.toolMetas`` (the
        # ingest in clawmetry/sync.py::_v3_extract_tool_metas projects them
        # to ``{id, name, input}``) and/or inside ``data.data.toolMetas``
        # / ``data.message.content[]`` for raw envelopes. Walk all known
        # locations so we don't miss any.
        if et == "model.completed":
            turn_index += 1
            msg_model = (ev.get("model")
                         or (data.get("modelId") if isinstance(data, dict) else "")
                         or "")
            msg_provider = (data.get("provider") if isinstance(data, dict) else "") or ""
            msg_cost = float(ev.get("cost_usd") or 0.0)
            tool_metas: list = []
            inner = data.get("data") if isinstance(data.get("data"), dict) else {}
            for src in (data.get("toolMetas"), inner.get("toolMetas")):
                if isinstance(src, list):
                    tool_metas.extend(src)
            # Also walk message.content[] for raw Anthropic-shape tool_use.
            for envelope in (data.get("message"), inner.get("message")):
                if isinstance(envelope, dict):
                    content = envelope.get("content")
                    if isinstance(content, list):
                        for blk in content:
                            if isinstance(blk, dict) and blk.get("type") == "tool_use":
                                tool_metas.append({
                                    "id":    blk.get("id"),
                                    "name":  blk.get("name") or "tool",
                                    "input": blk.get("input") or {},
                                })
            seen_ids: set = set()
            for meta in tool_metas:
                if not isinstance(meta, dict):
                    continue
                tcid = meta.get("id") or ""
                if not tcid or tcid in seen_ids:
                    continue
                seen_ids.add(tcid)
                calls[tcid] = {
                    "tool_call_id":     tcid,
                    "tool_name":        meta.get("name", "") or "",
                    "arguments":        _truncate(meta.get("input"), args_chars),
                    "start_ms":         ev_ts_ms,
                    "turn_index":       turn_index,
                    "model":            msg_model,
                    "provider":         msg_provider,
                    "message_cost_usd": msg_cost,
                    "via_subagent_id":  via_subagent_id or "",
                }
            continue

        # Legacy: nested toolCall / toolResult inside ``message`` event rows
        # (pre-v3 OpenClaw envelopes — kept for backward compatibility).
        if et != "message":
            continue
        saw_any = True
        msg = data.get("message") if isinstance(data.get("message"), dict) else {}
        role = msg.get("role", "")
        if role == "assistant":
            turn_index += 1
            content = msg.get("content") or []
            if not isinstance(content, list):
                continue
            usage = msg.get("usage") if isinstance(msg.get("usage"), dict) else {}
            cost_obj = usage.get("cost") if isinstance(usage.get("cost"), dict) else {}
            msg_cost = float(cost_obj.get("total", 0) or 0)
            msg_model = msg.get("model", "")
            msg_provider = msg.get("provider", "")
            for blk in content:
                if not isinstance(blk, dict) or blk.get("type") != "toolCall":
                    continue
                tcid = blk.get("id", "")
                if not tcid:
                    continue
                calls[tcid] = {
                    "tool_call_id":     tcid,
                    "tool_name":        blk.get("name", ""),
                    "arguments":        _truncate(blk.get("arguments"), args_chars),
                    "start_ms":         ev_ts_ms,
                    "turn_index":       turn_index,
                    "model":            msg_model,
                    "provider":         msg_provider,
                    "message_cost_usd": msg_cost,
                    "via_subagent_id":  via_subagent_id or "",
                }
        elif role == "toolResult":
            tcid = msg.get("toolCallId", "")
            if not tcid:
                continue
            details = msg.get("details")
            result_by_id[tcid] = {
                "end_ms":         ev_ts_ms,
                "is_error":       bool(msg.get("isError", False)),
                "result_size":    len(json.dumps(details)) if details is not None else 0,
                "result_preview": _truncate(details, result_chars),
            }
    if not saw_any:
        return None

    tools: list = []
    tool_counts: dict = {}
    for tcid, call in calls.items():
        res = result_by_id.get(tcid)
        if not res and not include_unpaired:
            continue
        rec = dict(call)
        if res:
            rec["end_ms"] = res["end_ms"]
            rec["duration_ms"] = max(0, res["end_ms"] - call["start_ms"]) if res["end_ms"] and call["start_ms"] else 0
            rec["is_error"] = res["is_error"]
            rec["result_size"] = res["result_size"]
            rec["result_preview"] = res["result_preview"]
            rec["paired"] = True
        else:
            rec["end_ms"] = 0
            rec["duration_ms"] = 0
            rec["is_error"] = False
            rec["result_size"] = 0
            rec["result_preview"] = None
            rec["paired"] = False
        tools.append(rec)
        tn = rec["tool_name"] or "unknown"
        agg = tool_counts.setdefault(tn, {"calls": 0, "errors": 0,
                                          "total_duration_ms": 0,
                                          "total_cost_usd": 0.0})
        agg["calls"] += 1
        if rec["is_error"]:
            agg["errors"] += 1
        agg["total_duration_ms"] += rec["duration_ms"]
        agg["total_cost_usd"] += float(rec.get("message_cost_usd") or 0.0)

    tools.sort(key=lambda r: r.get("start_ms", 0))
    by_tool = [
        {"tool_name": k, **v,
         "error_rate_pct": round(v["errors"] / v["calls"] * 100, 1) if v["calls"] else 0}
        for k, v in sorted(tool_counts.items(), key=lambda kv: -kv[1]["calls"])
    ]
    first_start = min((r["start_ms"] for r in tools if r.get("start_ms")), default=0)
    last_end = max((r.get("end_ms", 0) for r in tools), default=0)
    # Tool-empty v3 sessions still need a sensible timeline anchor so the
    # UI can render a "session ran, no tools" state — fall back to the
    # earliest lifecycle event (typically session.started).
    if not first_start and earliest_ts_ms:
        first_start = earliest_ts_ms
    return {
        "session_id": sid,
        "tools": tools,
        "by_tool": by_tool,
        "stats": {
            "total_calls":     len(tools),
            "paired_calls":    sum(1 for r in tools if r.get("paired")),
            "error_calls":     sum(1 for r in tools if r.get("is_error")),
            "distinct_tools":  len(tool_counts),
            "first_start_ms":  first_start,
            "last_end_ms":     last_end,
            "span_ms":         max(0, last_end - first_start) if first_start and last_end else 0,
        },
        "_source": "local_store",
    }


@bp_sessions.route("/api/session-tools")
def api_session_tools():
    """Return the tool_call / tool_result timeline for a single session."""
    import dashboard as _d
    sid = (request.args.get("session_id", "") or "").strip()
    if not sid:
        return jsonify({"error": "session_id required"}), 400
    try:
        args_chars = max(0, min(int(request.args.get("args_chars", "400")), 10000))
    except ValueError:
        args_chars = 400
    try:
        result_chars = max(0, min(int(request.args.get("result_chars", "400")), 10000))
    except ValueError:
        result_chars = 400
    include_unpaired = str(request.args.get("include_unpaired", "")).lower() in (
        "1", "true", "yes"
    )

    if is_local_store_read_enabled():
        fast = _try_local_store_session_tools(sid, args_chars, result_chars, include_unpaired)
        if fast is not None:
            return jsonify(fast)

    sessions_dir = _d.SESSIONS_DIR or os.path.expanduser(
        "~/.openclaw/agents/main/sessions"
    )
    if not os.path.isdir(sessions_dir):
        return jsonify({"error": "sessions dir not found"}), 404
    matches = [
        f for f in os.listdir(sessions_dir)
        if f.startswith(sid) and f.endswith(".jsonl")
        and ".deleted." not in f and ".reset." not in f
    ]
    if not matches:
        return jsonify({"error": "session not found"}), 404
    fpath = os.path.join(sessions_dir, sorted(matches)[0])

    def _parse_ts(ts):
        if not ts or not isinstance(ts, str):
            return 0
        try:
            from datetime import datetime as _dt
            return int(_dt.fromisoformat(ts.replace("Z", "+00:00")).timestamp() * 1000)
        except Exception:
            return 0

    def _truncate(val, limit):
        if limit <= 0 or val is None:
            return val
        if isinstance(val, str):
            return val if len(val) <= limit else val[:limit] + "…"
        try:
            s = json.dumps(val, separators=(",", ":"))
        except Exception:
            s = str(val)
        return s if len(s) <= limit else s[:limit] + "…"

    calls: dict = {}
    result_by_id: dict = {}
    turn_index = 0
    try:
        with open(fpath, "r", errors="replace") as fh:
            for raw in fh:
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    ev = json.loads(raw)
                except Exception:
                    continue
                if ev.get("type") != "message":
                    continue
                msg = ev.get("message", {}) or {}
                role = msg.get("role", "")
                ev_ts_ms = _parse_ts(ev.get("timestamp", ""))
                if role == "assistant":
                    turn_index += 1
                    content = msg.get("content") or []
                    if not isinstance(content, list):
                        continue
                    usage = msg.get("usage", {}) or {}
                    cost_obj = usage.get("cost", {}) or {}
                    msg_cost = float(cost_obj.get("total", 0) or 0) if isinstance(cost_obj, dict) else 0.0
                    msg_model = msg.get("model", "")
                    msg_provider = msg.get("provider", "")
                    for blk in content:
                        if not isinstance(blk, dict) or blk.get("type") != "toolCall":
                            continue
                        tcid = blk.get("id", "")
                        if not tcid:
                            continue
                        calls[tcid] = {
                            "tool_call_id": tcid,
                            "tool_name": blk.get("name", ""),
                            "arguments": _truncate(blk.get("arguments"), args_chars),
                            "start_ms": ev_ts_ms,
                            "turn_index": turn_index,
                            "model": msg_model,
                            "provider": msg_provider,
                            "message_cost_usd": msg_cost,
                        }
                elif role == "toolResult":
                    tcid = msg.get("toolCallId", "")
                    if not tcid:
                        continue
                    details = msg.get("details")
                    result_by_id[tcid] = {
                        "end_ms": ev_ts_ms,
                        "is_error": bool(msg.get("isError", False)),
                        "result_size": len(json.dumps(details)) if details is not None else 0,
                        "result_preview": _truncate(details, result_chars),
                    }
    except Exception as e:
        return jsonify({"error": "parse error: " + str(e)}), 500

    tools: list = []
    tool_counts: dict = {}
    for tcid, call in calls.items():
        res = result_by_id.get(tcid)
        if not res and not include_unpaired:
            continue
        rec = dict(call)
        if res:
            rec["end_ms"] = res["end_ms"]
            rec["duration_ms"] = max(0, res["end_ms"] - call["start_ms"]) if res["end_ms"] and call["start_ms"] else 0
            rec["is_error"] = res["is_error"]
            rec["result_size"] = res["result_size"]
            rec["result_preview"] = res["result_preview"]
            rec["paired"] = True
        else:
            rec["end_ms"] = 0
            rec["duration_ms"] = 0
            rec["is_error"] = False
            rec["result_size"] = 0
            rec["result_preview"] = None
            rec["paired"] = False
        tools.append(rec)
        tn = rec["tool_name"] or "unknown"
        agg = tool_counts.setdefault(tn, {"calls": 0, "errors": 0, "total_duration_ms": 0, "total_cost_usd": 0.0})
        agg["calls"] += 1
        if rec["is_error"]:
            agg["errors"] += 1
        agg["total_duration_ms"] += rec["duration_ms"]
        agg["total_cost_usd"] += float(rec.get("message_cost_usd") or 0.0)

    tools.sort(key=lambda r: r.get("start_ms", 0))
    by_tool = [
        {"tool_name": k, **v, "error_rate_pct": round(v["errors"] / v["calls"] * 100, 1) if v["calls"] else 0}
        for k, v in sorted(tool_counts.items(), key=lambda kv: -kv[1]["calls"])
    ]
    first_start = min((r["start_ms"] for r in tools if r.get("start_ms")), default=0)
    last_end = max((r.get("end_ms", 0) for r in tools), default=0)
    return jsonify({
        "session_id": sid,
        "tools": tools,
        "by_tool": by_tool,
        "stats": {
            "total_calls": len(tools),
            "paired_calls": sum(1 for r in tools if r.get("paired")),
            "error_calls": sum(1 for r in tools if r.get("is_error")),
            "distinct_tools": len(tool_counts),
            "first_start_ms": first_start,
            "last_end_ms": last_end,
            "span_ms": max(0, last_end - first_start) if first_start and last_end else 0,
        },
    })


def _try_local_store_cost_split(wanted_sid: str, limit: int):
    """Fast path for /api/cost-split. Reads per-session token + cost
    aggregates from DuckDB via :meth:`LocalStore.query_cost_split` and
    rolls them into the same ``{sessions, totals}`` shape the JSONL
    walker returns.

    Issue #1088 phase 3. Returns ``None`` when the events table has no
    message rows so the route falls through to the JSONL walker.

    Issue #1597 class drain: when scoped to a single session
    (``wanted_sid``), uses the sub-agent-rollup variant so a parent that
    delegated cost to a Task-tool child still attributes that cost back.
    Top-N mode (no ``wanted_sid``) keeps the flat per-session listing —
    rollup is only meaningful when the caller has a target parent.
    """
    if wanted_sid:
        rows = _ls_call(
            "query_cost_split_with_subagents",
            session_id=wanted_sid,
            limit=limit,
        )
        if rows is None:
            rows = _ls_call(
                "query_cost_split",
                session_id=wanted_sid,
                limit=limit,
            )
    else:
        rows = _ls_call(
            "query_cost_split",
            session_id=None,
            limit=limit,
        )
    if not rows:
        return None
    # Compute totals (mirrors the legacy path's aggregation).
    totals = {
        "input_tokens":         sum(r["input_tokens"] for r in rows),
        "output_tokens":        sum(r["output_tokens"] for r in rows),
        "cache_read_tokens":    sum(r["cache_read_tokens"] for r in rows),
        "cache_write_tokens":   sum(r["cache_write_tokens"] for r in rows),
        "total_tokens":         sum(r["total_tokens"] for r in rows),
        "input_cost_usd":       round(sum(r["input_cost_usd"] for r in rows), 4),
        "output_cost_usd":      round(sum(r["output_cost_usd"] for r in rows), 4),
        "cache_read_cost_usd":  round(sum(r["cache_read_cost_usd"] for r in rows), 4),
        "cache_write_cost_usd": round(sum(r["cache_write_cost_usd"] for r in rows), 4),
        "total_cost_usd":       round(sum(r["total_cost_usd"] for r in rows), 4),
        "session_count":        len(rows),
    }
    tot_in_cache = totals["input_tokens"] + totals["cache_read_tokens"]
    totals["cache_hit_ratio_pct"] = (
        round(totals["cache_read_tokens"] / tot_in_cache * 100, 1)
        if tot_in_cache else 0.0
    )
    if wanted_sid:
        # Single-session lookup returns the session list as-is, no totals.
        return {"sessions": rows, "totals": {}, "_source": "local_store"}
    return {"sessions": rows, "totals": totals, "_source": "local_store"}


@bp_sessions.route("/api/cost-split")
def api_cost_split():
    """Per-token-type token + cost breakdown per session.

    OpenClaw messages carry granular usage with input/output/cacheRead/
    cacheWrite tokens AND costs. ClawMetry was summing only totalTokens,
    hiding the cache-hit ratio (typically 40-70% of volume at ~10% cost).
    """
    import dashboard as _d
    wanted_sid = (request.args.get("session_id", "") or "").strip()
    try:
        limit = max(1, min(int(request.args.get("limit", "30")), 500))
    except ValueError:
        limit = 30

    if is_local_store_read_enabled():
        fast = _try_local_store_cost_split(wanted_sid, limit)
        if fast is not None:
            return jsonify(fast)

    sessions_dir = _d.SESSIONS_DIR or os.path.expanduser(
        "~/.openclaw/agents/main/sessions"
    )
    if not os.path.isdir(sessions_dir):
        return jsonify({"sessions": [], "totals": {}, "note": "sessions dir not found"})
    try:
        all_files = [
            f
            for f in os.listdir(sessions_dir)
            if f.endswith(".jsonl") and ".deleted." not in f and ".reset." not in f
        ]
    except OSError:
        all_files = []
    if wanted_sid:
        files = [f for f in all_files if f.startswith(wanted_sid)]
    else:
        files = sorted(
            all_files,
            key=lambda f: os.path.getmtime(os.path.join(sessions_dir, f)),
            reverse=True,
        )[:100]

    def _compute_for_file(fpath):
        sid = os.path.basename(fpath)
        if sid.endswith(".jsonl"):
            sid = sid[: -len(".jsonl")]
        tokens = {"input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 0}
        costs = {"input": 0.0, "output": 0.0, "cacheRead": 0.0, "cacheWrite": 0.0, "total": 0.0}
        model_tokens: dict = {}
        last_seen_model = ""
        try:
            with open(fpath, "r", errors="replace") as fh:
                for raw in fh:
                    raw = raw.strip()
                    if not raw:
                        continue
                    try:
                        ev = json.loads(raw)
                    except Exception:
                        continue
                    t = ev.get("type", "")
                    if t == "model_change":
                        m = ev.get("modelId") or ev.get("model") or ""
                        if m:
                            last_seen_model = m
                        continue
                    if t != "message":
                        continue
                    msg = ev.get("message", {}) or {}
                    if not isinstance(msg, dict):
                        continue
                    usage = msg.get("usage", {}) or {}
                    if not isinstance(usage, dict) or not usage:
                        continue
                    msg_model = msg.get("model") or last_seen_model
                    if msg_model:
                        last_seen_model = msg_model
                    for k in ("input", "output", "cacheRead", "cacheWrite"):
                        tokens[k] += int(usage.get(k, 0) or 0)
                    cost_obj = usage.get("cost", {}) or {}
                    if isinstance(cost_obj, dict):
                        for k in ("input", "output", "cacheRead", "cacheWrite", "total"):
                            costs[k] += float(cost_obj.get(k, 0) or 0)
                    mt = int(usage.get("totalTokens", 0) or 0)
                    if mt and msg_model:
                        model_tokens[msg_model] = model_tokens.get(msg_model, 0) + mt
        except Exception:
            return None
        total_tokens = sum(tokens.values())
        if total_tokens == 0 and costs["total"] == 0:
            return None
        primary_model = (
            max(model_tokens.items(), key=lambda kv: kv[1])[0]
            if model_tokens
            else last_seen_model
        )
        input_plus_cache = tokens["input"] + tokens["cacheRead"]
        cache_hit_ratio_pct = (
            round(tokens["cacheRead"] / input_plus_cache * 100, 1)
            if input_plus_cache
            else 0.0
        )
        est_fresh_input_cost = costs["cacheRead"] * 10.0
        savings = max(0.0, est_fresh_input_cost - costs["cacheRead"])
        est_savings_pct = (
            round(savings / (costs["input"] + est_fresh_input_cost) * 100, 1)
            if (costs["input"] + est_fresh_input_cost)
            else 0.0
        )
        return {
            "session_id": sid,
            "primary_model": primary_model,
            "input_tokens": tokens["input"],
            "output_tokens": tokens["output"],
            "cache_read_tokens": tokens["cacheRead"],
            "cache_write_tokens": tokens["cacheWrite"],
            "total_tokens": total_tokens,
            "input_cost_usd": round(costs["input"], 6),
            "output_cost_usd": round(costs["output"], 6),
            "cache_read_cost_usd": round(costs["cacheRead"], 6),
            "cache_write_cost_usd": round(costs["cacheWrite"], 6),
            "total_cost_usd": round(costs["total"], 6),
            "cache_hit_ratio_pct": cache_hit_ratio_pct,
            "est_cache_savings_pct": est_savings_pct,
        }

    rows = []
    for fname in files:
        r = _compute_for_file(os.path.join(sessions_dir, fname))
        if r:
            rows.append(r)
    rows.sort(key=lambda r: r.get("total_cost_usd", 0), reverse=True)
    if wanted_sid and rows:
        return jsonify({"sessions": rows, "totals": {}})
    top = rows[:limit]
    totals = {
        "input_tokens": sum(r["input_tokens"] for r in rows),
        "output_tokens": sum(r["output_tokens"] for r in rows),
        "cache_read_tokens": sum(r["cache_read_tokens"] for r in rows),
        "cache_write_tokens": sum(r["cache_write_tokens"] for r in rows),
        "total_tokens": sum(r["total_tokens"] for r in rows),
        "input_cost_usd": round(sum(r["input_cost_usd"] for r in rows), 4),
        "output_cost_usd": round(sum(r["output_cost_usd"] for r in rows), 4),
        "cache_read_cost_usd": round(sum(r["cache_read_cost_usd"] for r in rows), 4),
        "cache_write_cost_usd": round(sum(r["cache_write_cost_usd"] for r in rows), 4),
        "total_cost_usd": round(sum(r["total_cost_usd"] for r in rows), 4),
        "session_count": len(rows),
    }
    tot_in_cache = totals["input_tokens"] + totals["cache_read_tokens"]
    totals["cache_hit_ratio_pct"] = (
        round(totals["cache_read_tokens"] / tot_in_cache * 100, 1)
        if tot_in_cache
        else 0.0
    )
    return jsonify({"sessions": top, "totals": totals})


def _try_local_store_task_runs(*, limit, status_filter, parent_filter,
                               requester_filter):
    """Fast path for /api/task-runs. Reads the pre-aggregated ``subagents``
    DuckDB table — the same source PR #1569 wired into
    ``_try_local_store_subagents``. OpenClaw's ``~/.openclaw/tasks/runs.sqlite``
    and the subagents snapshot the sync daemon write-throughs from each
    system-snapshot pass (see ``clawmetry/sync.py`` ``ingest_subagent`` call
    site) carry the same lifecycle rows — the ``subagents`` table schema
    comment in ``clawmetry/local_store.py`` calls this out explicitly
    ("Shared by OpenClaw subagents + Claude Code Task tool.").

    Audit hint for #1565 was "derive from query_events task lifecycle
    types" — verified 2026-05-17 against ``sync.py::_parse_v3_event``:
    no ``task.started`` / ``task.completed`` event types exist in v3
    ingest. The canonical DuckDB source for task lifecycle IS the
    ``subagents`` table; the audit hint was directionally correct
    (DuckDB, not sqlite/JSONL) but pointed at the wrong table.

    Returns ``None`` when the table is empty so the legacy
    ``~/.openclaw/tasks/runs.sqlite`` fallback fires for installs whose
    daemon hasn't snapshotted yet. Field shape matches the legacy
    handler's output exactly so the Subagents modal (``app.js``
    ``renderModalSubagents``) — which keys on ``task_id``,
    ``parent_task_id``, ``child_session_key``, ``status``,
    ``duration_ms``, ``label``, ``task``, ``terminal_outcome`` —
    keeps working bit-for-bit.
    """
    rows = _ls_call("query_subagents", limit=max(limit, 500))
    if not rows:
        return None

    # Snapshot status (from gateway subagents list) uses a different
    # vocabulary than runs.sqlite. The UI keys on the runs.sqlite shape
    # (`running` / `succeeded` / `failed` / `pending`) for colour pills
    # and the "Failed" stat chip — normalise so the modal renders
    # consistently across data sources.
    _status_map = {
        "active":    "running",
        "running":   "running",
        "idle":      "running",
        "completed": "succeeded",
        "succeeded": "succeeded",
        "done":      "succeeded",
        "failed":    "failed",
        "error":     "failed",
        "pending":   "pending",
        "stale":     "pending",
    }

    tasks: list = []
    counts: dict = {}
    for r in rows:
        sid = r.get("subagent_id") or ""
        if not sid:
            continue
        extra = r.get("data") if isinstance(r.get("data"), dict) else {}

        # Derive the runs.sqlite field names from subagents columns + data blob.
        # ``subagent_id`` IS the task_id (one row per task spawn). The
        # ``child_session_key`` is OpenClaw's canonical key shape; the
        # parent (``requester_session_key``) is the session that issued
        # the spawn. ``parent_task_id`` is only set for nested spawns and
        # may not exist in the snapshot — fall back to extra dict.
        parent_sid = r.get("parent_session_id") or extra.get("spawnedBy") or ""
        child_key = extra.get("key") or f"agent:main:subagent:{sid}"
        requester_key = (extra.get("requester_session_key")
                         or (f"agent:main:{parent_sid}" if parent_sid else ""))

        # Apply caller filters BEFORE building the row so the response
        # honours ``status=`` / ``parent_task_id=`` / ``requester_session_key=``
        # exactly like the legacy sqlite WHERE clause.
        raw_status = (r.get("status") or "").strip().lower()
        mapped_status = _status_map.get(raw_status, raw_status or "unknown")
        if status_filter and mapped_status != status_filter and raw_status != status_filter:
            continue
        if parent_filter and (extra.get("parent_task_id") or "") != parent_filter:
            continue
        if requester_filter and requester_key != requester_filter:
            continue

        # started/ended come from the snapshot's ms timestamps (data blob)
        # when available; spawned_at/ended_at strings are best-effort
        # ISO fallbacks. duration_ms mirrors the legacy formula.
        started_ms = int(extra.get("started_at_ms")
                         or extra.get("updated_at_ms") or 0)
        ended_ms = int(extra.get("ended_at_ms") or 0)
        if not started_ms and r.get("spawned_at"):
            try:
                started_ms = int(datetime.fromisoformat(
                    str(r["spawned_at"]).replace("Z", "+00:00")
                ).timestamp() * 1000)
            except Exception:
                started_ms = 0
        if not ended_ms and r.get("ended_at"):
            try:
                ended_ms = int(datetime.fromisoformat(
                    str(r["ended_at"]).replace("Z", "+00:00")
                ).timestamp() * 1000)
            except Exception:
                ended_ms = 0
        duration_ms = max(0, ended_ms - started_ms) if started_ms and ended_ms else 0

        task_d = {
            "task_id":              sid,
            "parent_task_id":       extra.get("parent_task_id") or "",
            "child_session_key":    child_key,
            "requester_session_key": requester_key,
            "agent_id":             extra.get("agent_id") or "main",
            "run_id":               extra.get("runId") or extra.get("run_id") or "",
            "label":                extra.get("label") or extra.get("displayName") or "",
            "task":                 r.get("task") or "",
            "status":               mapped_status,
            "delivery_status":      extra.get("delivery_status") or "",
            "task_kind":            extra.get("task_kind") or "subagent",
            "parent_flow_id":       extra.get("parent_flow_id") or "",
            "created_at":           started_ms,
            "started_at":           started_ms,
            "ended_at":             ended_ms,
            "last_event_at":        int(extra.get("updated_at_ms") or 0),
            "error":                extra.get("error") or "",
            "progress_summary":     extra.get("progress_summary") or "",
            "terminal_summary":     extra.get("terminal_summary")
                                    or extra.get("completionResult") or "",
            "terminal_outcome":     extra.get("terminal_outcome")
                                    or extra.get("completionStatus") or "",
            "duration_ms":          duration_ms,
        }
        tasks.append(task_d)
        counts[mapped_status] = counts.get(mapped_status, 0) + 1
        if len(tasks) >= limit:
            break

    # Sort newest-first by started_at then created_at, matching the
    # legacy ``ORDER BY COALESCE(started_at, created_at, 0) DESC`` clause.
    tasks.sort(key=lambda t: t.get("started_at") or t.get("created_at") or 0,
               reverse=True)

    total = len(tasks)
    failed = counts.get("failed", 0)
    err_rate = round(failed / total * 100, 1) if total else 0
    return {
        "tasks":   tasks,
        "counts":  counts,
        "stats": {
            "total":          total,
            "succeeded":      counts.get("succeeded", 0),
            "failed":         failed,
            "running":        counts.get("running", 0),
            "error_rate_pct": err_rate,
        },
        "_source": "local_store",
    }


@bp_sessions.route("/api/task-runs")
def api_task_runs():
    """Subagent / task registry. Prefers the DuckDB ``subagents`` table
    fast path (populated by the sync daemon's snapshot pass); falls
    back to OpenClaw's ``~/.openclaw/tasks/runs.sqlite`` for installs
    whose daemon hasn't run yet.
    """
    import sqlite3
    try:
        limit = max(1, min(int(request.args.get("limit", "500")), 5000))
    except ValueError:
        limit = 500
    status_filter = (request.args.get("status", "") or "").strip()
    parent_filter = (request.args.get("parent_task_id", "") or "").strip()
    requester_filter = (request.args.get("requester_session_key", "") or "").strip()

    # DuckDB fast path — skips the sqlite open entirely when the daemon
    # has snapshotted at least one subagent row.
    if is_local_store_read_enabled():
        fast = _try_local_store_task_runs(
            limit=limit,
            status_filter=status_filter,
            parent_filter=parent_filter,
            requester_filter=requester_filter,
        )
        if fast is not None:
            return jsonify(fast)

    p = os.path.expanduser("~/.openclaw/tasks/runs.sqlite")
    if not os.path.isfile(p):
        return jsonify({"tasks": [], "counts": {}, "note": "runs.sqlite not found"})
    where = []
    args = []
    if status_filter:
        where.append("status = ?")
        args.append(status_filter)
    if parent_filter:
        where.append("parent_task_id = ?")
        args.append(parent_filter)
    if requester_filter:
        where.append("requester_session_key = ?")
        args.append(requester_filter)
    where_sql = ("WHERE " + " AND ".join(where)) if where else ""
    tasks: list = []
    counts: dict = {}
    try:
        conn = sqlite3.connect(p)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(
            f"""SELECT task_id, parent_task_id, child_session_key, requester_session_key,
                       agent_id, run_id, label, task, status, delivery_status,
                       task_kind, parent_flow_id,
                       created_at, started_at, ended_at, last_event_at,
                       error, progress_summary, terminal_summary, terminal_outcome
                FROM task_runs {where_sql}
                ORDER BY COALESCE(started_at, created_at, 0) DESC
                LIMIT ?""",
            args + [limit],
        )
        for r in cur.fetchall():
            d = dict(r)
            started = d.get("started_at") or 0
            ended = d.get("ended_at") or 0
            d["duration_ms"] = max(0, ended - started) if started and ended else 0
            tasks.append(d)
            st = d.get("status") or "unknown"
            counts[st] = counts.get(st, 0) + 1
        conn.close()
    except Exception as e:
        return jsonify({"tasks": [], "counts": {}, "error": str(e)}), 500
    total = len(tasks)
    failed = counts.get("failed", 0)
    err_rate = round(failed / total * 100, 1) if total else 0
    return jsonify({
        "tasks": tasks,
        "counts": counts,
        "stats": {
            "total": total,
            "succeeded": counts.get("succeeded", 0),
            "failed": failed,
            "running": counts.get("running", 0),
            "error_rate_pct": err_rate,
        },
    })


def _scan_spawn_events_from_jsonl(sessions_dir, max_files=None, tail_bytes=None):
    """Walk every session JSONL and pair SPAWN toolCall/toolResult rows.

    OpenClaw's subagent lifecycle is:
      1. Parent session's assistant turn emits a `toolCall` with name
         `subagents` (action=spawn) or legacy `sessions_spawn`. The
         `arguments` dict carries `name`/`label`, `task`, `channel`.
      2. OpenClaw fires back a `toolResult` with the SAME `toolCallId`.
         On success: `details = {childSessionKey, runId, mode, note,
         modelApplied, ...}`. On failure: `details = {status:"error",
         error:"..."}`.

    This gives us the FULL subagent history regardless of whether the
    gateway registry still knows about them (registry rolls over at 30
    min; JSONL persists until TTL cleanup). Returns a list of subagent
    dicts ready to merge into /api/subagents response.
    """
    import glob as _glob
    import re as _re
    subs = []
    if not sessions_dir or not os.path.isdir(sessions_dir):
        return subs

    _completion_re = _re.compile(
        r"<<<BEGIN_UNTRUSTED_CHILD_RESULT>>>\s*(.*?)\s*<<<END_UNTRUSTED_CHILD_RESULT>>>",
        _re.DOTALL,
    )
    _stats_re = _re.compile(
        r"Stats:\s*runtime\s+([\w.]+)\s*[•·]?\s*tokens\s+(\d+)\s*\(in\s*(\d+)\s*/\s*out\s*(\d+)\)",
        _re.IGNORECASE,
    )
    _session_key_re = _re.compile(r"session_key:\s*(agent:main:subagent:[\w-]+)")
    _task_name_re = _re.compile(r"^task:\s*(.+)$", _re.MULTILINE)
    _status_re = _re.compile(r"^status:\s*(.+)$", _re.MULTILINE)

    files = _glob.glob(os.path.join(sessions_dir, "*.jsonl"))
    try:
        files.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    except Exception:
        pass
    if max_files and max_files > 0:
        files = files[:max_files]

    for fpath in files:
        if ".deleted." in fpath:
            continue
        # Skip checkpoints - their content is duplicated into the main file
        # and they'd cause double-counting.
        if ".checkpoint." in fpath:
            continue
        parent_sid = os.path.basename(fpath).replace(".jsonl", "").split(".")[0]
        calls = {}       # toolCallId → {name, args, ts}
        results = {}     # toolCallId → {details, isError, ts, content_text}
        completions = {} # childSessionKey → {task, status, result, stats, ts}
        try:
            with open(fpath, "r", errors="replace") as fh:
                if tail_bytes and tail_bytes > 0:
                    try:
                        size = os.path.getsize(fpath)
                        if size > tail_bytes:
                            fh.seek(max(0, size - tail_bytes))
                            fh.readline()  # drop partial line after seek
                    except Exception:
                        pass
                for raw in fh:
                    raw = raw.strip()
                    if not raw:
                        continue
                    try:
                        ev = json.loads(raw)
                    except Exception:
                        continue
                    if ev.get("type") != "message":
                        continue
                    msg = ev.get("message") or {}
                    role = msg.get("role", "")
                    ts = ev.get("timestamp", "")
                    if role == "assistant":
                        for blk in msg.get("content") or []:
                            if not isinstance(blk, dict):
                                continue
                            if blk.get("type") != "toolCall":
                                continue
                            nm = (blk.get("name") or "").lower()
                            if "subagent" not in nm and "spawn" not in nm:
                                continue
                            args = blk.get("arguments") or {}
                            action = (args.get("action") or "spawn").lower()
                            if action not in ("spawn", "create"):
                                continue
                            calls[blk.get("id", "")] = {
                                "name": blk.get("name"),
                                "args": args,
                                "ts": ts,
                            }
                    elif role == "toolResult":
                        nm = (msg.get("toolName") or "").lower()
                        if "subagent" not in nm and "spawn" not in nm:
                            continue
                        tcid = msg.get("toolCallId", "")
                        if not tcid:
                            continue
                        content_text = ""
                        content = msg.get("content")
                        if isinstance(content, list) and content:
                            first = content[0]
                            if isinstance(first, dict):
                                content_text = first.get("text") or ""
                        results[tcid] = {
                            "details": msg.get("details"),
                            "isError": bool(msg.get("isError")),
                            "ts": ts,
                            "content_text": content_text[:2000],
                        }
                    elif role == "user":
                        # OpenClaw injects subagent completion events as
                        # synthetic user messages bracketed by
                        # <<<BEGIN_OPENCLAW_INTERNAL_CONTEXT>>>. Parse them
                        # so we can show the child's output even after its
                        # transcript is GC'd.
                        for blk in msg.get("content") or []:
                            if not isinstance(blk, dict):
                                continue
                            if blk.get("type") != "text":
                                continue
                            txt = blk.get("text") or ""
                            if "Internal task completion event" not in txt:
                                continue
                            if "source: subagent" not in txt:
                                continue
                            sk_m = _session_key_re.search(txt)
                            if not sk_m:
                                continue
                            child_key = sk_m.group(1)
                            res_m = _completion_re.search(txt)
                            stats_m = _stats_re.search(txt)
                            task_m = _task_name_re.search(txt)
                            status_m = _status_re.search(txt)
                            completions[child_key] = {
                                "task_label": task_m.group(1).strip() if task_m else "",
                                "status": status_m.group(1).strip() if status_m else "",
                                "result": (res_m.group(1).strip() if res_m else "")[:8000],
                                "runtime": stats_m.group(1) if stats_m else "",
                                "tokens_total": int(stats_m.group(2)) if stats_m else 0,
                                "tokens_in": int(stats_m.group(3)) if stats_m else 0,
                                "tokens_out": int(stats_m.group(4)) if stats_m else 0,
                                "ts": ts,
                            }
        except Exception:
            continue

        for tcid, call in calls.items():
            res = results.get(tcid, {})
            det = res.get("details") if isinstance(res.get("details"), dict) else {}
            error_msg = None
            child_key = None
            if det:
                if det.get("status") == "error":
                    error_msg = det.get("error")
                child_key = det.get("childSessionKey") or det.get("key")
            # Some OpenClaw error shapes return empty `details` but set
            # `isError=true` with the message in content[0].text. Fall back
            # to that so the dashboard can surface validation errors.
            if res.get("isError") and not error_msg:
                ct = res.get("content_text") or ""
                error_msg = ct.split("\n")[0][:400] if ct else "Unknown OpenClaw error"
            args = call.get("args") or {}
            name = args.get("name") or args.get("label") or "subagent"
            completion = completions.get(child_key, {}) if child_key else {}
            subs.append({
                "parentSessionId": parent_sid,
                "parentKey": f"agent:main:session:{parent_sid}",
                "childKey": child_key,
                "name": name,
                "task": (args.get("task") or "")[:500],
                "callTs": call.get("ts"),
                "resultTs": res.get("ts"),
                "error": error_msg,
                "runId": det.get("runId") if det else None,
                "mode": det.get("mode") if det else None,
                "modelApplied": det.get("modelApplied") if det else None,
                # Spawn acknowledgment text (e.g. "accepted" note) — useful when
                # the spawn succeeded but no completion event is present yet.
                "spawnAck": res.get("content_text") or "",
                # Completion payload — populated if OpenClaw emitted a
                # completion event for this child in the parent transcript.
                "completionStatus": completion.get("status") or "",
                "completionResult": completion.get("result") or "",
                "completionTs": completion.get("ts") or "",
                "runtimeFormatted": completion.get("runtime") or "",
                "tokensIn": completion.get("tokens_in") or 0,
                "tokensOut": completion.get("tokens_out") or 0,
                "tokensTotal": completion.get("tokens_total") or 0,
            })
    return subs


def _try_local_store_subagents(_rows=None):
    """Fast path for /api/subagents. Reads the pre-aggregated ``subagents``
    table that the sync daemon write-throughs from each system-snapshot
    pass (see ``clawmetry/sync.py`` ``ingest_subagent`` call site). Each
    row carries the same fields the JSONL-walking legacy path derives, so
    we can serve the dashboard's Subagent Tracker tab without re-scanning
    every session JSONL on every request.

    ``_rows`` lets a caller pass ``query_subagents`` rows it already has
    (e.g. the sync daemon building the snapshot on its OWN store handle,
    where the cross-process ``_ls_call`` proxy is the wrong tool). When
    omitted we fetch via the daemon proxy as usual.

    Returns ``None`` when the table is empty so the legacy gateway-RPC +
    JSONL fallback fires for older OpenClaw versions / installs whose
    daemon hasn't snapshotted yet. Returns a populated shell (subagents=[],
    counts zero'd) when the daemon HAS run but no subagents have been
    spawned — keeps the route off the 100-file JSONL walker for the
    common empty case.
    """
    rows = _rows if _rows is not None else _ls_call("query_subagents", limit=500)
    # Distinguish "store missing entirely" (rows is None) from "store is
    # there but no subagent rows yet" (rows == []). Both return None so
    # the legacy gateway-RPC + JSONL fallback fires — older OpenClaw
    # installs whose daemon hasn't snapshotted to the table yet still
    # surface their subagents via the JSONL spawn scan.
    if not rows:
        return None

    now_ms = time.time() * 1000
    subagents: list = []
    counts = {"total": 0, "active": 0, "idle": 0, "stale": 0, "failed": 0}

    def _parse_ts_ms(ts):
        if not ts:
            return 0
        if isinstance(ts, (int, float)):
            return int(ts)
        try:
            return int(datetime.fromisoformat(
                str(ts).replace("Z", "+00:00")
            ).timestamp() * 1000)
        except Exception:
            return 0

    for r in rows:
        sid = r.get("subagent_id") or ""
        if not sid:
            continue
        # ``data`` BLOB carries the fields not promoted to first-class
        # columns (model, label, displayName, sessionFile, updated_at_ms,
        # runtime_ms). _decode_data_blob_rows already deserialised it.
        extra = r.get("data") if isinstance(r.get("data"), dict) else {}
        updated_at_ms = (extra.get("updated_at_ms")
                         or _parse_ts_ms(r.get("updated_at"))
                         or 0)
        spawned_at_ms = _parse_ts_ms(r.get("spawned_at")) or updated_at_ms
        runtime_ms = int(extra.get("runtime_ms") or 0)
        if not runtime_ms and spawned_at_ms:
            runtime_ms = max(0, int(now_ms - spawned_at_ms))

        # Status: prefer the daemon's explicit classification verbatim
        # (it may emit ``completed`` / ``running`` / etc. that aren't in
        # the legacy bucket set — the UI handles those directly).
        # Fall back to age-derived bucket only when status is missing.
        status = (r.get("status") or "").strip().lower()
        if not status:
            age_ms = now_ms - (updated_at_ms or 0)
            if age_ms < 120000:
                status = "active"
            elif age_ms < 600000:
                status = "idle"
            else:
                status = "stale"

        token_count = int(r.get("token_count") or 0)
        # Build key in OpenClaw's canonical shape so Active-Tasks modal
        # lookups keep working when the legacy path falls back later.
        key = extra.get("key") or f"agent:main:subagent:{sid}"
        display = (extra.get("displayName") or extra.get("label")
                   or (r.get("task") or "")[:80] or sid[:20])
        model = extra.get("model") or "unknown"

        elapsed_s = runtime_ms // 1000
        if elapsed_s < 60:
            runtime = f"{elapsed_s}s"
        elif elapsed_s < 3600:
            runtime = f"{elapsed_s // 60}m"
        else:
            runtime = f"{elapsed_s // 3600}h {(elapsed_s % 3600) // 60}m"

        counts["total"] += 1
        counts[status] = counts.get(status, 0) + 1
        subagents.append({
            "sessionId":        sid,
            "key":              key,
            "displayName":      display,
            "model":            model,
            "status":           status,
            "depth":            int(extra.get("depth") or 1),
            "parent":           r.get("parent_session_id") or extra.get("spawnedBy"),
            "totalTokens":      token_count,
            "runtime":          runtime,
            "runtimeMs":        runtime_ms,
            "startedAt":        spawned_at_ms or updated_at_ms,
            "updatedAt":        updated_at_ms,
            "task":             r.get("task") or "",
            "error":            extra.get("error") or "",
            "completionResult": extra.get("completionResult") or "",
            "completionStatus": extra.get("completionStatus") or "",
            "completionTs":     extra.get("completionTs") or "",
            "runtimeFormatted": extra.get("runtimeFormatted") or runtime,
            "tokensIn":         int(extra.get("tokensIn") or 0),
            "tokensOut":        int(extra.get("tokensOut") or 0),
            "spawnAck":         extra.get("spawnAck") or "",
            "runId":            extra.get("runId") or "",
        })

    _status_rank = {"active": 0, "idle": 1, "stale": 2, "failed": 3}
    subagents.sort(key=lambda x: (_status_rank.get(x["status"], 9), x["depth"]))
    return {
        "subagents": subagents,
        "counts":    counts,
        "_source":   "local_store",
    }


@bp_sessions.route("/api/subagents")
def api_subagents():
    """Return sub-agent list with depth/parent fields for the tree view.

    Data sources merged (in priority order):

    0. DuckDB ``subagents`` table fast path (when the local store is
       enabled) — pre-aggregated by the sync daemon's snapshot pass, so
       we don't re-walk every session JSONL on every dashboard render.
    1. OpenClaw's canonical `subagents action=list` registry — live +
       last-30-min recent, with status explicitly.
    2. `sessions_list` gateway RPC filtered by key substring — catches
       subagents still in the session roster but outside the 30-min
       registry window.
    3. JSONL spawn event scan — pairs `toolCall` / `toolResult` for
       subagents-spawn across every session file on disk. Captures both
       succeeded spawns (via `details.childSessionKey`) and attempted
       spawns that errored (visible so the user knows the agent tried).
    """
    import dashboard as _d
    now_ms = time.time() * 1000
    full_scan = request.args.get("full", "").strip().lower() in ("1", "true", "yes")
    if not full_scan:
        cached = _SUBAGENTS_CACHE.get("data")
        if cached is not None and (time.time() - float(_SUBAGENTS_CACHE.get("ts") or 0)) < _SUBAGENTS_CACHE_TTL_SECONDS:
            return jsonify(cached)

    # Source 0: DuckDB fast path. Skips the JSONL spawn-scan + gateway RPC
    # entirely. ``full_scan`` still defers to the legacy path so the "force
    # a complete JSONL rescan" escape hatch keeps working.
    if not full_scan and is_local_store_read_enabled():
        fast = _try_local_store_subagents()
        if fast is not None:
            _SUBAGENTS_CACHE["data"] = fast
            _SUBAGENTS_CACHE["ts"] = time.time()
            return jsonify(fast)

    # Source 1: canonical subagent registry
    reg_active = []
    reg_recent = []
    try:
        reg = _d._gw_invoke("subagents", {"action": "list"})
        if reg and isinstance(reg, dict):
            reg_active = reg.get("active", []) or []
            reg_recent = reg.get("recent", []) or []
    except Exception:
        pass

    # Source 2: full session list for the depth/parent filter.
    # IMPORTANT: copy the list before mutating. `_d._get_sessions()` returns a
    # reference to _sessions_cache["data"]; calling `.insert()` on the return
    # value would append registry + spawn entries to the cache itself, so
    # every subsequent /api/subagents call inherits the previous call's
    # appends — subagents get duplicated exponentially (6x, 8x, 10x...).
    gw_data = _d._gw_invoke("sessions_list", {"limit": 20, "messageLimit": 0})
    if gw_data and "sessions" in gw_data:
        all_sessions = list(gw_data["sessions"])
    else:
        all_sessions = list(_d._get_sessions() or [])

    # Prepend registry entries — normalise to the same shape so the filter
    # below treats them uniformly. Registry-provided entries always pass
    # the is_subagent check (they're by definition subagents).
    seen_keys = set()
    for entry in reg_active + reg_recent:
        if not isinstance(entry, dict):
            continue
        k = entry.get("key") or entry.get("sessionKey") or ""
        if not k or k in seen_keys:
            continue
        seen_keys.add(k)
        all_sessions.insert(0, {
            "key": k,
            "sessionId": entry.get("sessionId") or k.split(":")[-1],
            "displayName": entry.get("name") or entry.get("label") or entry.get("displayName") or "",
            "status": entry.get("status") or "active",
            "updatedAt": entry.get("updatedAt") or entry.get("lastActiveMs") or now_ms,
            "startedAt": entry.get("startedAt") or entry.get("createdAt") or now_ms,
            "model": entry.get("model") or "",
            "totalTokens": entry.get("totalTokens") or 0,
            "depth": entry.get("depth") or 1,  # registry entries are subagents
            "spawnedBy": entry.get("parentKey") or entry.get("spawnedBy"),
            "_from_registry": True,
        })

    # Source 3: JSONL spawn event scan — merge into all_sessions where the
    # child isn't already covered by sources 1/2. Errored spawns also get
    # included (with status="failed") so the user sees "agent tried to
    # spawn X but it failed with Y" instead of a silently empty panel.
    sessions_dir = _d.SESSIONS_DIR or os.path.expanduser(
        "~/.openclaw/agents/main/sessions"
    )
    try:
        spawn_events = _scan_spawn_events_from_jsonl(
            sessions_dir,
            max_files=None if full_scan else _SUBAGENTS_SCAN_MAX_FILES,
            tail_bytes=None if full_scan else _SUBAGENTS_SCAN_TAIL_BYTES,
        )
    except Exception:
        spawn_events = []
    # Build a lookup by childKey so we can enrich entries from sources 1/2
    # with the spawn metadata + completion logs, even when they were already
    # present in the registry / session roster.
    spawn_by_key = {}
    for sp in spawn_events:
        ck = sp.get("childKey")
        if ck:
            spawn_by_key[ck] = sp
    for sp in spawn_events:
        k = sp.get("childKey") or f"spawn:attempt:{sp.get('parentSessionId')}:{sp.get('callTs')}"
        if k in seen_keys:
            continue
        seen_keys.add(k)
        # Parse timestamp to epoch ms
        try:
            from datetime import datetime as _dt
            ts_ms = int(_dt.fromisoformat(
                (sp.get("resultTs") or sp.get("callTs") or "").replace("Z", "+00:00")
            ).timestamp() * 1000)
        except Exception:
            ts_ms = int(now_ms)
        status = "failed" if sp.get("error") else ""  # let main filter classify active/idle/stale
        all_sessions.insert(0, {
            "key": k,
            "sessionId": (sp.get("childKey") or "").split(":")[-1] or "",
            "displayName": sp.get("name"),
            "task": sp.get("task"),
            "error": sp.get("error"),
            "runId": sp.get("runId"),
            # modelApplied in legacy OpenClaw spawn results is a bool "was a
            # model override applied?", not the model name. Coerce non-string
            # values to "" so the UI doesn't render "True" in a model slot.
            "model": sp.get("modelApplied") if isinstance(sp.get("modelApplied"), str) else "",
            "updatedAt": ts_ms,
            "startedAt": ts_ms,
            "depth": 1,
            "spawnedBy": sp.get("parentKey"),
            "_status_override": status,
            "_from_spawn_scan": True,
            "spawnAck": sp.get("spawnAck") or "",
            "completionResult": sp.get("completionResult") or "",
            "completionStatus": sp.get("completionStatus") or "",
            "completionTs": sp.get("completionTs") or "",
            "runtimeFormatted": sp.get("runtimeFormatted") or "",
            "tokensIn": sp.get("tokensIn") or 0,
            "tokensOut": sp.get("tokensOut") or 0,
        })

    subagents = []
    counts = {"total": 0, "active": 0, "idle": 0, "stale": 0, "failed": 0}
    for s in all_sessions:
        sid = s.get("sessionId") or ""
        key = s.get("key") or ""
        if not sid and not key:
            continue
        age_ms = now_ms - (s.get("updatedAt") or s.get("lastActiveMs", 0) or 0)
        override = s.get("_status_override")
        if override:
            status = override   # "failed" (errored spawn attempt)
        elif age_ms < 120000:
            status = "active"
        elif age_ms < 600000:
            status = "idle"
        else:
            status = "stale"
        depth = int(s.get("depth", 0) or 0)
        parent = s.get("spawnedBy") or s.get("parentKey") or None
        # OpenClaw keys subagents as `agent:main:subagent:<uuid>` — check the
        # KEY (not the sessionId UUID) for the substring. Previously we
        # checked sessionId, which is always a bare UUID → `subagent` match
        # never fired → subagents never appeared in Active Tasks.
        is_subagent = (
            depth > 0
            or "subagent" in key.lower()
            or bool(parent)
        )
        if not is_subagent:
            continue
        tokens = int(s.get("totalTokens") or 0)
        model = s.get("model") or s.get("modelRef") or "unknown"
        display = s.get("displayName") or s.get("label") or sid[:20]
        started = s.get("startedAt") or s.get("updatedAt") or now_ms
        elapsed_ms = max(0, int(now_ms - started))
        elapsed_s = elapsed_ms // 1000
        if elapsed_s < 60:
            runtime = f"{elapsed_s}s"
        elif elapsed_s < 3600:
            runtime = f"{elapsed_s // 60}m"
        else:
            runtime = f"{elapsed_s // 3600}h {(elapsed_s % 3600) // 60}m"
        counts["total"] += 1
        counts[status] += 1
        # Enrich from the spawn scan by childKey — this gives us the task
        # description and completion output even for subagents that only
        # showed up via the gateway registry / session roster.
        sp_match = spawn_by_key.get(key, {}) if key else {}
        task_text = s.get("task") or sp_match.get("task") or ""
        error_text = s.get("error") or sp_match.get("error") or ""
        subagents.append({
            "sessionId": sid,
            "key": key,                 # used by Active Tasks openTaskModal
            "displayName": display,
            "model": model,
            "status": status,
            "depth": depth,
            "parent": parent,
            "totalTokens": tokens,
            "runtime": runtime,         # formatted string (legacy)
            "runtimeMs": elapsed_ms,    # numeric ms — used by Active Tasks card
            "startedAt": started,
            "updatedAt": s.get("updatedAt") or s.get("lastActiveMs", 0),
            "task": task_text,
            "error": error_text,
            # Completion payload reconstructed from parent JSONL. Populated
            # for subagents whose parent emitted an Internal task completion
            # event (OpenClaw's auto-announce). Modal uses these fields to
            # render the child's output when its own transcript is GC'd.
            # Prefer the session-level fields (propagated for spawn-only
            # entries without a childKey) over the childKey-indexed lookup.
            "completionResult": s.get("completionResult") or sp_match.get("completionResult") or "",
            "completionStatus": s.get("completionStatus") or sp_match.get("completionStatus") or "",
            "completionTs":     s.get("completionTs")     or sp_match.get("completionTs") or "",
            "runtimeFormatted": s.get("runtimeFormatted") or sp_match.get("runtimeFormatted") or "",
            "tokensIn":  s.get("tokensIn")  or sp_match.get("tokensIn")  or 0,
            "tokensOut": s.get("tokensOut") or sp_match.get("tokensOut") or 0,
            "spawnAck":  s.get("spawnAck")  or sp_match.get("spawnAck")  or "",
            "runId":     s.get("runId") or sp_match.get("runId") or "",
        })

    _status_rank = {"active": 0, "idle": 1, "stale": 2, "failed": 3}
    subagents.sort(key=lambda x: (_status_rank.get(x["status"], 9), x["depth"]))
    payload = {"subagents": subagents, "counts": counts}
    if not full_scan:
        _SUBAGENTS_CACHE["data"] = payload
        _SUBAGENTS_CACHE["ts"] = time.time()
    return jsonify(payload)


def _check_duplicate_completions(sessions_dir, max_files=None):
    """Scan JSONL files for duplicate 'Internal task completion' events per child key.

    Returns list of {type, subagentKey, count, timestamps} for any child
    that received more than one completion broadcast in the parent transcript.
    """
    import glob as _glob
    import re as _re
    _session_key_re = _re.compile(r"session_key:\s*(agent:main:subagent:[\w-]+)")
    completion_counts: dict = {}  # child_key -> [ts, ...]
    if not sessions_dir or not os.path.isdir(sessions_dir):
        return []
    files = _glob.glob(os.path.join(sessions_dir, "*.jsonl"))
    try:
        files.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    except Exception:
        pass
    if max_files and max_files > 0:
        files = files[:max_files]
    for fpath in files:
        if ".deleted." in fpath or ".checkpoint." in fpath:
            continue
        try:
            with open(fpath, "r", errors="replace") as fh:
                for raw in fh:
                    raw = raw.strip()
                    if not raw or "Internal task completion event" not in raw:
                        continue
                    try:
                        ev = json.loads(raw)
                    except Exception:
                        continue
                    msg = ev.get("message") or {}
                    if msg.get("role") != "user":
                        continue
                    ts = ev.get("timestamp", "")
                    for blk in msg.get("content") or []:
                        if not isinstance(blk, dict) or blk.get("type") != "text":
                            continue
                        txt = blk.get("text") or ""
                        if "Internal task completion event" not in txt or "source: subagent" not in txt:
                            continue
                        sk_m = _session_key_re.search(txt)
                        if not sk_m:
                            continue
                        child_key = sk_m.group(1)
                        completion_counts.setdefault(child_key, []).append(ts)
        except Exception:
            continue
    return [
        {"type": "duplicate_completion", "subagentKey": ck, "count": len(ts_list), "timestamps": ts_list}
        for ck, ts_list in completion_counts.items()
        if len(ts_list) > 1
    ]


def _check_integrity(subagents):
    """Run orphan and cycle integrity checks on an assembled subagent list.

    Orphan: child references a parent key not present in the live session set,
    age-gated to 7 days to avoid false-positives for GC'd old sessions.
    Cycle: DFS detects back-edges in the parent→child adjacency graph.

    Returns list of violation dicts.
    """
    violations = []
    keys = {s["key"] for s in subagents if s.get("key")}
    seven_days_ms = 7 * 24 * 3600 * 1000
    now_ms = time.time() * 1000

    for s in subagents:
        parent = s.get("parent")
        key = s.get("key", "")
        if not parent or not key:
            continue
        # Only flag if parent looks like a subagent key (nested subagent
        # whose parent is gone). Depth-1 subagents have a main session
        # as parent — those will never appear in the subagent list and
        # should not be flagged.
        if "subagent" in parent and parent not in keys:
            started = s.get("startedAt") or 0
            if now_ms - started < seven_days_ms:
                violations.append({
                    "type": "orphan",
                    "subagentKey": key,
                    "displayName": s.get("displayName", ""),
                    "parentKey": parent,
                })

    children_map: dict = {}
    for s in subagents:
        parent = s.get("parent")
        key = s.get("key")
        if parent and key:
            children_map.setdefault(parent, []).append(key)

    visited: set = set()
    in_stack: set = set()

    def _dfs(node, path):
        if node in in_stack:
            violations.append({"type": "cycle", "path": path + [node]})
            return
        if node in visited:
            return
        visited.add(node)
        in_stack.add(node)
        for child in children_map.get(node, []):
            _dfs(child, path + [node])
        in_stack.discard(node)

    for s in subagents:
        key = s.get("key")
        if key and key not in visited:
            _dfs(key, [])

    return violations


@bp_sessions.route("/api/subagents/integrity")
def api_subagents_integrity():
    """Validate subagent state-machine: orphans, cycles, duplicate completions.

    Returns {violations, stats, checked_at}. Backend-only — no UI yet;
    the endpoint exists for the Subagents tab to consume when the badge
    is wired up.
    """
    import dashboard as _d
    sub_resp = api_subagents()
    try:
        sub_data = json.loads(sub_resp.get_data(as_text=True))
    except Exception:
        sub_data = {}
    subagents = sub_data.get("subagents") or []

    violations = _check_integrity(subagents)

    sessions_dir = getattr(_d, "SESSIONS_DIR", None) or os.path.expanduser(
        "~/.openclaw/agents/main/sessions"
    )
    try:
        violations.extend(
            _check_duplicate_completions(sessions_dir, max_files=_SUBAGENTS_SCAN_MAX_FILES)
        )
    except Exception:
        pass

    stats = {
        "orphan_count": sum(1 for v in violations if v["type"] == "orphan"),
        "cycle_count": sum(1 for v in violations if v["type"] == "cycle"),
        "duplicate_count": sum(1 for v in violations if v["type"] == "duplicate_completion"),
        "subagents_checked": len(subagents),
    }
    return jsonify({"violations": violations, "stats": stats, "checked_at": time.time()})


def _try_local_store_delegation_tree():
    """Fast path for /api/delegation-tree (Tier-1 from #1778 punch list).

    Reads the pre-aggregated ``subagents`` table (same source as
    ``_try_local_store_subagents``) and groups by ``parent_session_id``
    to produce the per-chain token + cost totals. Skips the JSONL spawn
    walker + sessions.json index read entirely — the daemon's snapshot
    pass already computed both ``cost_usd`` and ``token_count`` per
    subagent row, so chain totals are a server-side sum.

    Returns ``None`` when the ``subagents`` table is empty so the
    legacy ``sessions.json`` fallback fires for installs whose daemon
    hasn't snapshotted yet. Returns a populated empty shell only when
    the store is reachable AND no subagents have been spawned, which
    is the right answer (the legacy path would also return empty).
    """
    import dashboard as _d
    rows = _ls_call("query_subagents", limit=500)
    if rows is None:
        # Store unreachable. Defer to legacy so older installs keep working.
        return None
    if not rows:
        # Store reachable, just empty. Serve the empty shell directly so
        # we don't trigger an unnecessary sessions.json open + walk.
        return {
            "chains": [],
            "total_subagents": 0,
            "total_chain_cost_usd": 0.0,
            "_source": "local_store",
        }

    # Fall back to the OSS pricing estimator only when the row lacks a
    # daemon-computed ``cost_usd``. Cloud's dashboard.py doesn't export
    # this helper; guard with getattr so we degrade to zero rather than 500.
    _estimate_usd_per_token = getattr(_d, "_estimate_usd_per_token", None)
    usd_per_tok = _estimate_usd_per_token() if _estimate_usd_per_token else 3.0 / 1_000_000.0
    now_ms = time.time() * 1000

    chains_map: dict = {}
    parent_display_map: dict = {}

    for r in rows:
        sid = r.get("subagent_id") or ""
        if not sid:
            continue
        extra = r.get("data") if isinstance(r.get("data"), dict) else {}
        # The daemon stores parent_session_id as a bare session id; the
        # legacy route grouped by ``spawnedBy`` (a full canonical key). Prefer
        # the full key from the ``data`` blob when present so the response
        # shape stays byte-compatible with the legacy walker.
        parent_key = (extra.get("spawnedBy")
                      or r.get("parent_session_id")
                      or "unknown")
        token_count = int(r.get("token_count") or 0)
        # The daemon's cost_usd column is already deduped (issue #1460
        # sibling-pair fix landed in query_sessions); prefer it verbatim and
        # fall back to the token-based estimator only when the daemon
        # snapshotted a row without cost (older sync.py builds).
        cost_usd = r.get("cost_usd")
        if cost_usd is None or cost_usd == 0:
            cost_usd = round(token_count * usd_per_tok, 6)
        else:
            cost_usd = float(cost_usd)

        # Status: prefer daemon classification, fall back to age bucket.
        status = (r.get("status") or "").strip().lower()
        if not status:
            updated_ms = extra.get("updated_at_ms") or 0
            try:
                if not updated_ms and r.get("updated_at"):
                    updated_ms = int(datetime.fromisoformat(
                        str(r["updated_at"]).replace("Z", "+00:00")
                    ).timestamp() * 1000)
            except Exception:
                updated_ms = 0
            age_ms = now_ms - (updated_ms or 0)
            if age_ms < 120000:
                status = "active"
            elif age_ms < 600000:
                status = "idle"
            else:
                status = "stale"

        key = extra.get("key") or f"agent:main:subagent:{sid}"
        label = extra.get("label") or extra.get("displayName") or key.split(":")[-1]
        model = extra.get("model") or "unknown"
        try:
            updated_iso = r.get("updated_at")
            updated_at = (int(datetime.fromisoformat(
                str(updated_iso).replace("Z", "+00:00")
            ).timestamp() * 1000)
                          if updated_iso else (extra.get("updated_at_ms") or 0))
        except Exception:
            updated_at = extra.get("updated_at_ms") or 0

        chains_map.setdefault(parent_key, []).append({
            "key":               key,
            "label":             label,
            "model":             model,
            "prov_agent_type":   "subagent",
            "prov_session_turn": 2,
            "prov_parent_key":   parent_key,
            "prov_total_tokens": token_count,
            "input_tokens":      int(extra.get("tokensIn") or extra.get("inputTokens") or 0),
            "output_tokens":     int(extra.get("tokensOut") or extra.get("outputTokens") or 0),
            "total_tokens":      token_count,
            "cost_usd":          round(float(cost_usd), 6),
            "status":            status,
            "updated_at":        updated_at,
        })
        if "displayName" in extra or "subject" in extra:
            parent_display_map.setdefault(parent_key,
                                          extra.get("displayName") or extra.get("subject"))

    chains = []
    total_chain_cost = 0.0
    for parent_key, children in chains_map.items():
        parts = parent_key.split(":")
        channel = parts[2] if len(parts) > 2 else "unknown"
        display = parts[-1] if parts else parent_key
        chain_tokens = sum(c["total_tokens"] for c in children)
        chain_cost = round(sum(c["cost_usd"] for c in children), 6)
        total_chain_cost += chain_cost
        chains.append({
            "parent_key":      parent_key,
            "parent_display":  parent_display_map.get(parent_key) or display,
            "parent_channel":  channel,
            "children":        sorted(children, key=lambda x: x["total_tokens"], reverse=True),
            "chain_tokens":    chain_tokens,
            "chain_cost_usd":  chain_cost,
            "child_count":     len(children),
        })

    chains.sort(key=lambda x: x["chain_tokens"], reverse=True)
    return {
        "chains":               chains,
        "total_subagents":      len(rows),
        "total_chain_cost_usd": round(total_chain_cost, 4),
        "_source":              "local_store",
    }


@bp_sessions.route("/api/delegation-tree")
def api_delegation_tree():
    """Agent delegation chains -- inspired by AgentWeave provenance tracing.

    Source 0 (DuckDB fast path): groups the ``subagents`` table by
    ``parent_session_id``; per-chain token + cost totals come from the
    daemon-aggregated columns (no JSONL re-walk).

    Source 1 (legacy fallback): reads sessions.json, groups subagents
    by their ``spawnedBy`` parent key. Kept so older OpenClaw installs
    without the local store keep rendering this view.
    """
    import dashboard as _d
    # Source 0: DuckDB fast path. Skips sessions.json entirely.
    if is_local_store_read_enabled():
        fast = _try_local_store_delegation_tree()
        if fast is not None:
            return jsonify(fast)

    # Cloud's dashboard.py is a different module than OSS's; some helpers
    # (e.g. _get_sessions_dir, _estimate_usd_per_token) only exist in OSS.
    # Guard with getattr so we degrade to an empty response instead of 500.
    _get_sessions_dir = getattr(_d, "_get_sessions_dir", None)
    _estimate_usd_per_token = getattr(_d, "_estimate_usd_per_token", None)
    if _get_sessions_dir is None or _estimate_usd_per_token is None:
        return jsonify(
            {"chains": [], "total_subagents": 0, "total_chain_cost_usd": 0.0}
        )
    sessions_dir = _get_sessions_dir()
    index_path = os.path.join(sessions_dir, "sessions.json")
    try:
        with open(index_path) as f:
            all_sessions = json.load(f)
    except Exception:
        return jsonify(
            {"chains": [], "total_subagents": 0, "total_chain_cost_usd": 0.0}
        )

    usd_per_tok = _estimate_usd_per_token()
    now_ms = time.time() * 1000

    main_sessions = {}
    subagent_sessions = []
    for key, val in all_sessions.items():
        if not isinstance(val, dict):
            continue
        if ":subagent:" in key:
            subagent_sessions.append((key, val))
        else:
            main_sessions[key] = val

    chains_map = {}
    for key, sa in subagent_sessions:
        parent_key = sa.get("spawnedBy", "unknown")
        if parent_key not in chains_map:
            chains_map[parent_key] = []
        age_ms = now_ms - sa.get("updatedAt", 0)
        status = (
            "active" if age_ms < 120000 else ("idle" if age_ms < 600000 else "stale")
        )
        total_tok = int(sa.get("totalTokens") or 0)
        chains_map[parent_key].append(
            {
                "key": key,
                "label": sa.get("label") or key.split(":")[-1],
                "model": sa.get("model", "unknown"),
                "prov_agent_type": "subagent",
                "prov_session_turn": 2,
                "prov_parent_key": parent_key,
                "prov_total_tokens": total_tok,
                "input_tokens": int(sa.get("inputTokens") or 0),
                "output_tokens": int(sa.get("outputTokens") or 0),
                "total_tokens": total_tok,
                "cost_usd": round(total_tok * usd_per_tok, 6),
                "status": status,
                "updated_at": sa.get("updatedAt", 0),
            }
        )

    chains = []
    total_chain_cost = 0.0
    for parent_key, children in chains_map.items():
        parts = parent_key.split(":")
        channel = parts[2] if len(parts) > 2 else "unknown"
        display = parts[-1] if len(parts) > 0 else parent_key
        chain_tokens = sum(c["total_tokens"] for c in children)
        chain_cost = round(chain_tokens * usd_per_tok, 6)
        total_chain_cost += chain_cost
        parent_meta = main_sessions.get(parent_key, {})
        chains.append(
            {
                "parent_key": parent_key,
                "parent_display": parent_meta.get("displayName")
                or parent_meta.get("subject")
                or display,
                "parent_channel": channel,
                "children": sorted(
                    children, key=lambda x: x["total_tokens"], reverse=True
                ),
                "chain_tokens": chain_tokens,
                "chain_cost_usd": chain_cost,
                "child_count": len(children),
            }
        )

    chains.sort(key=lambda x: x["chain_tokens"], reverse=True)
    return jsonify(
        {
            "chains": chains,
            "total_subagents": len(subagent_sessions),
            "total_chain_cost_usd": round(total_chain_cost, 4),
        }
    )


@bp_sessions.route("/api/export/otlp")
def api_export_otlp():
    """Export recent sessions as OTLP ResourceSpans JSON.

    Compatible with Grafana Tempo, Jaeger, and any OTLP-capable backend.
    """
    import dashboard as _d
    import hashlib

    sessions_dir = _d._get_sessions_dir()
    index_path = os.path.join(sessions_dir, "sessions.json")
    try:
        with open(index_path) as f:
            all_sessions = json.load(f)
    except Exception:
        return jsonify({"resourceSpans": []})

    cutoff_ms = (time.time() - 86400) * 1000
    resource_spans = []
    count = 0

    for key, val in all_sessions.items():
        if not isinstance(val, dict):
            continue
        if val.get("updatedAt", 0) < cutoff_ms:
            continue
        if count >= 100:
            break
        count += 1

        is_subagent = ":subagent:" in key
        agent_type = "subagent" if is_subagent else "main"
        session_id = val.get("sessionId", key.split(":")[-1])
        trace_id = hashlib.md5(session_id.encode()).hexdigest()
        span_id = trace_id[:16]
        total_tokens = int(val.get("totalTokens") or 0)

        attrs = [
            {"key": "service.name", "value": {"stringValue": "clawmetry"}},
            {"key": "prov.agent.id", "value": {"stringValue": key}},
            {"key": "prov.agent.type", "value": {"stringValue": agent_type}},
            {
                "key": "prov.agent.model",
                "value": {"stringValue": val.get("model", "unknown")},
            },
            {"key": "prov.llm.total_tokens", "value": {"intValue": total_tokens}},
            {
                "key": "prov.session.turn",
                "value": {"intValue": 2 if is_subagent else 1},
            },
        ]
        if is_subagent and val.get("spawnedBy"):
            attrs.append(
                {
                    "key": "prov.parent.session.id",
                    "value": {"stringValue": val["spawnedBy"]},
                }
            )
        if val.get("label"):
            attrs.append(
                {"key": "prov.task.label", "value": {"stringValue": val["label"]}}
            )

        updated_ns = int(val.get("updatedAt", 0)) * 1000000

        resource_spans.append(
            {
                "resource": {
                    "attributes": [
                        {"key": "service.name", "value": {"stringValue": "clawmetry"}},
                    ]
                },
                "scopeSpans": [
                    {
                        "scope": {"name": "clawmetry.agent", "version": "1.0"},
                        "spans": [
                            {
                                "traceId": trace_id,
                                "spanId": span_id,
                                "name": "agent.turn",
                                "kind": 3,
                                "startTimeUnixNano": updated_ns - 1000000000,
                                "endTimeUnixNano": updated_ns,
                                "attributes": attrs,
                                "status": {"code": 1},
                            }
                        ],
                    }
                ],
            }
        )

    return jsonify({"resourceSpans": resource_spans})


def _try_local_store_cost_breakdown():
    """Fast path for /api/sessions/cost-breakdown. Aggregates per-session
    total cost + tokens straight out of DuckDB's ``sessions`` view.

    Issue #1088: routes through the daemon HTTP proxy first (cross-process
    safe), with a direct ``get_store()`` fallback for single-process boots.

    Returns ``None`` to defer to ``_compute_transcript_analytics`` if:
      - neither path can reach the local store
      - the sessions table is empty
      - any unexpected error happens
    """
    rows = _ls_call("query_sessions", limit=1000)
    if not rows:
        return None
    result = []
    for r in rows:
        sid = r.get("session_id") or ""
        if not sid:
            continue
        cost = float(r.get("cost_usd") or 0.0)
        tokens = int(r.get("token_count") or 0)
        # Day key from started_at (ISO ts) — best-effort.
        started_iso = r.get("started_at") or ""
        day = ""
        start_ts = 0
        try:
            dt = datetime.fromisoformat(str(started_iso).replace("Z", "+00:00"))
            day = dt.strftime("%Y-%m-%d")
            start_ts = int(dt.timestamp())
        except Exception:
            pass
        result.append({
            "session_id": sid,
            "tokens": tokens,
            "cost_usd": round(cost, 6),
            "model": "",  # not stored at session level; UI tolerates blank
            "day": day,
            "start_ts": start_ts,
        })
    result.sort(key=lambda x: x["cost_usd"], reverse=True)
    top10 = result[:10]
    total_cost = sum(r["cost_usd"] for r in result)
    return {
        "sessions": result,
        "top10": top10,
        "total_cost_usd": round(total_cost, 4),
        "_source": "local_store",
    }


@bp_sessions.route("/api/sessions/cost-breakdown")
def api_sessions_cost_breakdown():
    """Per-session cost breakdown: top sessions by total cost, sorted descending."""
    import dashboard as _d

    # Epic #964 — opt-in DuckDB fast path.
    if is_local_store_read_enabled():
        fast = _try_local_store_cost_breakdown()
        if fast is not None:
            return jsonify(fast)

    analytics = _d._compute_transcript_analytics()
    sessions = analytics.get("sessions", [])
    usd_per_token = _d._estimate_usd_per_token()
    result = []
    for s in sessions:
        cost = s.get("cost_usd", 0.0) or 0.0
        tokens = s.get("tokens", 0) or 0
        # Estimate cost from tokens if cost is zero
        if cost == 0.0 and tokens > 0:
            cost = tokens * usd_per_token
        result.append(
            {
                "session_id": s.get("session_id", ""),
                "tokens": tokens,
                "cost_usd": round(cost, 6),
                "model": s.get("model", "unknown"),
                "day": s.get("day", ""),
                "start_ts": s.get("start_ts", 0),
            }
        )
    result.sort(key=lambda x: x["cost_usd"], reverse=True)
    top10 = result[:10]
    total_cost = sum(r["cost_usd"] for r in result)
    return jsonify(
        {"sessions": result, "top10": top10, "total_cost_usd": round(total_cost, 4)}
    )


@bp_sessions.route("/api/sessions/<session_id>/stop", methods=["POST"])
def api_session_stop(session_id):
    """Emergency stop for a session: SIGTERM if pid is known and/or .stop signal file."""
    import dashboard as _d
    target = _d._resolve_session_stop_target(session_id)
    sid = target.get("session_id", "")
    if not sid:
        return jsonify({"ok": False, "error": "Invalid session id"}), 400

    did_signal = False
    did_file = False
    errors = []
    pid = target.get("pid")
    if isinstance(pid, int) and pid > 1 and sys.platform != "win32":
        try:
            os.kill(pid, 15)  # SIGTERM
            did_signal = True
        except Exception as e:
            errors.append(f"sigterm_failed:{e}")

    stop_path = target.get("stop_path", "")
    try:
        if stop_path:
            with open(stop_path, "w") as f:
                f.write(
                    json.dumps(
                        {"timestamp": time.time(), "reason": "dashboard_emergency_stop"}
                    )
                )
            did_file = True
    except Exception as e:
        errors.append(f"stop_file_failed:{e}")

    if not did_signal and not did_file:
        return jsonify(
            {"ok": False, "error": "Unable to issue stop signal", "details": errors}
        ), 500
    return jsonify(
        {
            "ok": True,
            "session_id": sid,
            "sigterm_sent": did_signal,
            "stop_file_written": did_file,
            "errors": errors,
        }
    )


# Issue #1718: event_types whose ``data`` is a transcript-renderable turn.
# Single source of truth for THREE places that must agree:
#   1. ``LocalStore.query_sessions`` ``message_count`` (SQL CASE WHEN).
#   2. ``_try_local_store_transcript`` (DuckDB detail path — early skip).
#   3. ``_count_jsonl_renderable_lines`` (legacy JSONL list fallback).
# Keep aligned with ``LocalStore._RENDERABLE_EVENT_TYPES`` in
# ``clawmetry/local_store.py``. The two lists are deliberately duplicated
# so each layer can evolve without a cross-module import cycle.
_RENDERABLE_TRANSCRIPT_EVENT_TYPES = frozenset({
    # Anthropic-style (no dotted type) → role-bearing turns.
    "message", "user", "assistant", "system", "tool", "tool_result",
    # Tool-call variants (see ``_TOOL_CALL_TOPLEVEL_EVENT_TYPES`` in
    # ``clawmetry/local_store.py``) — different ingest paths use different
    # spellings; all four are renderable.
    "tool_call", "toolCall", "tool_use", "tool-result",
    # OpenClaw v3 / dotted types — must match _expand_openclaw_event arms.
    "prompt.submitted", "trace.artifacts", "model.completed",
    "tool.call", "tool.invoked", "tool.result", "tool.completed",
    "compaction",
    # Subagent fan-out — child turns surface in the parent's transcript
    # via ``query_events_with_subagents`` (#1597).
    "subagent:assistant", "subagent:user",
})

# Issue #1718: OpenClaw event types whose JSONL line maps to a transcript
# turn — the dotted-type subset of ``_RENDERABLE_TRANSCRIPT_EVENT_TYPES``.
_RENDERABLE_JSONL_OPENCLAW_TYPES = frozenset({
    "prompt.submitted", "trace.artifacts", "model.completed",
    "tool.call", "tool.invoked", "tool.result", "tool.completed",
    "compaction",
})
_RENDERABLE_JSONL_ANTHROPIC_ROLES = frozenset({
    "user", "assistant", "system", "tool", "tool_result",
})


def _count_jsonl_renderable_lines(fpath: str) -> int:
    """Count session-JSONL lines that map to a transcript turn.

    Cheap streaming parse: each line is JSON-decoded once and matched
    against the same renderable predicate ``LocalStore.query_sessions``
    applies at the SQL layer. Lines that fail to parse, lack both a role
    and a recognised OpenClaw ``type``, or carry plumbing-only types
    (``session.*``, ``model.changed``, ``thinking_level_change``,
    ``context.compiled``, ``agent.heartbeat``, ``channel.in``/``.out``,
    ``custom``/``custom_message``) do NOT count.

    Caller catches all exceptions and falls back to 0 on a corrupt file.
    """
    count = 0
    with open(fpath) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except (json.JSONDecodeError, ValueError):
                # A non-JSON line is never renderable — skip.
                continue
            if not isinstance(obj, dict):
                continue
            role = obj.get("role")
            if isinstance(role, str) and role in _RENDERABLE_JSONL_ANTHROPIC_ROLES:
                count += 1
                continue
            # Tool-bearing assistant rows (some Anthropic shapes ship
            # ``tool_calls`` / ``tool_use`` without a top-level role).
            if obj.get("tool_calls") or obj.get("tool_use"):
                count += 1
                continue
            etype = obj.get("type")
            if isinstance(etype, str) and etype in _RENDERABLE_JSONL_OPENCLAW_TYPES:
                count += 1
    return count


def _try_local_store_transcripts():
    """Fast path for /api/transcripts. Lists distinct sessions with their
    event counts + most-recent ts, straight from DuckDB.

    Issue #1088: routes through the daemon HTTP proxy first (cross-process
    safe), with a direct ``get_store()`` fallback for single-process boots.

    Returns ``None`` to defer to the legacy filesystem listdir if:
      - neither path can reach the local store
      - the sessions table is empty
      - any unexpected error happens
    """
    rows = _ls_call("query_sessions", limit=50)
    if not rows:
        return None
    transcripts = []
    for r in rows:
        sid = r.get("session_id") or ""
        if not sid:
            continue
        # Issue #1896 follow-up: hide ClawMetry's own helper sessions
        # (clawmetry-fix / clawmetry-selfevolve / clawmetry-mem-probe …) so
        # our plumbing doesn't mix with the user's agent activity.
        if hide_clawmetry_session(sid):
            continue
        # Coerce ts (ISO string) to ms-since-epoch for parity with the
        # legacy ``int(os.path.getmtime(fpath) * 1000)`` shape.
        modified_ms = 0
        upd = r.get("updated_at")
        if upd:
            try:
                modified_ms = int(
                    datetime.fromisoformat(str(upd).replace("Z", "+00:00"))
                    .timestamp() * 1000
                )
            except Exception:
                modified_ms = 0
        # Issue #1718: prefer the SQL-filtered ``message_count`` (renderable-
        # event count, matches the detail modal) over the legacy raw
        # ``event_count``. The OR-fallback keeps callers running against
        # an older daemon that hasn't picked up the schema bump yet —
        # they still see the pre-fix inflated count, but no crash.
        msg_count = r.get("message_count")
        if msg_count is None:
            msg_count = r.get("event_count") or 0
        transcripts.append({
            "id": sid,
            "name": sid[:40],
            "messages": int(msg_count or 0),
            "size": 0,  # unknown from DuckDB; UI shows "—" when 0
            "modified": modified_ms,
        })
    return {"transcripts": transcripts, "_source": "local_store"}


@bp_sessions.route('/api/transcripts')
def api_transcripts():
    """List available session transcript .jsonl files."""
    import dashboard as _d

    # Epic #964 — opt-in DuckDB fast path.
    if is_local_store_read_enabled():
        fast = _try_local_store_transcripts()
        if fast is not None:
            return jsonify(fast)

    sessions_dir = _d.SESSIONS_DIR or os.path.expanduser(
        "~/.openclaw/agents/main/sessions"
    )
    transcripts = []
    if os.path.isdir(sessions_dir):
        for fname in sorted(
            os.listdir(sessions_dir),
            key=lambda f: os.path.getmtime(os.path.join(sessions_dir, f)),
            reverse=True,
        ):
            if not fname.endswith(".jsonl") or "deleted" in fname:
                continue
            # Hide ClawMetry's own helper sessions (see _try_local_store_transcripts).
            if hide_clawmetry_session(fname.replace(".jsonl", "")):
                continue
            fpath = os.path.join(sessions_dir, fname)
            try:
                # Issue #1718: count only the JSONL lines the transcript
                # detail view will actually render as messages — i.e. skip
                # plumbing rows like ``session.started`` / ``model.changed``
                # / ``thinking_level_change`` / ``custom`` / ``channel.*``.
                # Mirrors the SQL filter in ``LocalStore.query_sessions``
                # so the legacy JSONL fallback agrees with the DuckDB fast
                # path (and with what ``/api/transcript/<sid>`` returns).
                msg_count = _count_jsonl_renderable_lines(fpath)
                transcripts.append(
                    {
                        "id": fname.replace(".jsonl", ""),
                        "name": fname.replace(".jsonl", "")[:40],
                        "messages": msg_count,
                        "size": os.path.getsize(fpath),
                        "modified": int(os.path.getmtime(fpath) * 1000),
                    }
                )
            except Exception:
                pass
    return jsonify({"transcripts": transcripts[:50]})


def _is_openclaw_event(obj: dict) -> bool:
    """Return True if ``obj`` looks like an OpenClaw event (vs an Anthropic
    message).

    OpenClaw events carry ``{"type": "<namespace>.<action>", "data": {...}}``
    with no top-level ``role``. Anthropic-shaped messages have a top-level
    ``role`` field (``user`` / ``assistant`` / ``system``)."""
    if not isinstance(obj, dict):
        return False
    if obj.get("role"):
        return False
    t = obj.get("type")
    if not isinstance(t, str):
        return False
    # OpenClaw types are dotted: prompt.submitted, trace.artifacts, etc.
    return "." in t


def _openclaw_event_tokens(data: dict) -> int:
    """Sum tokens for one OpenClaw event from its ``promptCache.lastCallUsage``
    block. Falls back to ``input+output`` when ``total`` is missing.

    OpenClaw writes usage at ``data.promptCache.lastCallUsage`` (per call) and
    also sometimes at ``data.usage`` (aggregate). We prefer the per-call value
    so two trace events don't double-count the same call."""
    if not isinstance(data, dict):
        return 0
    pc = data.get("promptCache")
    if isinstance(pc, dict):
        lcu = pc.get("lastCallUsage")
        if isinstance(lcu, dict):
            total = lcu.get("total")
            if isinstance(total, (int, float)) and total:
                return int(total)
            inp = lcu.get("input") or 0
            out = lcu.get("output") or 0
            if inp or out:
                return int(inp) + int(out)
    usage = data.get("usage")
    if isinstance(usage, dict):
        total = usage.get("total_tokens")
        if isinstance(total, (int, float)) and total:
            return int(total)
        inp = usage.get("input_tokens") or 0
        out = usage.get("output_tokens") or 0
        if inp or out:
            return int(inp) + int(out)
    return 0


def _stringify_content(content) -> str:
    """Best-effort coerce a transcript message ``content`` field to a string."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for part in content:
            if isinstance(part, dict):
                parts.append(part.get("text", str(part)))
            else:
                parts.append(str(part))
        return "\n".join(parts)
    return str(content) if content else ""


# Issue #1895: expose the verbatim event payload so the transcript viewer can
# toggle between the beautified turn and the exact JSON OpenClaw recorded/sent
# upstream (requested by users studying OpenClaw's behavior). Capped per-message
# so attaching it to every turn never bloats the response or the cloud snapshot
# it rides into.
_RAW_PAYLOAD_CAP = 12000


def _bounded_raw_payload(obj, cap: int = _RAW_PAYLOAD_CAP):
    """Return ``obj`` for inline raw-payload display, or a small truncation
    marker when its serialized form exceeds ``cap`` bytes. Never raises."""
    try:
        serialized = json.dumps(obj, default=str)
    except Exception:
        return None
    if len(serialized) > cap:
        return {"_raw_truncated": True, "_raw_bytes": len(serialized)}
    return obj


# Issue #1911: Anthropic Messages content-block tools. Claude-Code rows nest the
# real message under ``data.message`` and record each tool as a *content block*
# (``{"type":"tool_use","name","input"}`` / ``{"type":"tool_result",
# "tool_use_id","content"}``) rather than a top-level ``tool_calls`` key. The
# flat transcript path missed these entirely, so tool-heavy sessions replayed as
# a wall of nameless "Tool call"/"Tool result" chips. We lift each block into a
# real turn carrying the tool name + input/output so the replay can deep-dive
# into what actually happened.
_TOOL_DETAIL_CAP = 4000


def _cap_text(s, cap: int = _TOOL_DETAIL_CAP) -> str:
    """Truncate a string to ``cap`` chars with a visible marker. Never raises."""
    s = s if isinstance(s, str) else str(s)
    if len(s) > cap:
        return s[:cap] + f"\n… (truncated, {len(s)} chars total)"
    return s


def _pretty_json(x, cap: int = _TOOL_DETAIL_CAP) -> str:
    """Pretty-print a tool input/output payload to a capped string for inline
    display. Falls back to ``str()`` for anything not JSON-serializable."""
    try:
        s = json.dumps(x, indent=2, default=str)
    except (TypeError, ValueError):
        s = str(x)
    return _cap_text(s, cap)


def _anthropic_tool_turns(blocks, ts_ms, name_by_id):
    """Map an Anthropic message ``content`` block list to ``(tool_turns, text)``.

    ``tool_turns`` is one turn per ``tool_use`` / ``tool_result`` block, each
    carrying a ``tool`` dict (``{kind, name, input|output}``) the replay renders
    as an expandable deep-dive. ``text`` is the joined text blocks, used only
    when the session has no v3 prose event (pure Claude Code) so we never double
    the assistant reply. ``name_by_id`` maps a ``tool_use`` id to its name so
    the matching ``tool_result`` (which only references the id) can show which
    tool it came from.
    """
    tool_turns: list[dict] = []
    texts: list[str] = []
    if not isinstance(blocks, list):
        return tool_turns, ""
    for b in blocks:
        if not isinstance(b, dict):
            continue
        bt = b.get("type")
        if bt == "text":
            t = b.get("text")
            if t:
                texts.append(t if isinstance(t, str) else str(t))
        elif bt == "tool_use":
            name = b.get("name") or "tool"
            tid = b.get("id")
            if tid:
                name_by_id[tid] = name
            tool_turns.append({
                "role": "assistant",
                "content": "",
                "timestamp": ts_ms,
                "type": "tool_use",
                "tool": {
                    "kind": "call",
                    "name": name,
                    "input": _pretty_json(b.get("input") or {}),
                },
            })
        elif bt == "tool_result":
            name = name_by_id.get(b.get("tool_use_id"), "")
            tool_turns.append({
                "role": "tool",
                "content": "",
                "timestamp": ts_ms,
                "type": "tool_use",
                "tool": {
                    "kind": "result",
                    "name": name,
                    "output": _cap_text(_stringify_content(b.get("content"))),
                    "is_error": bool(b.get("is_error")),
                },
            })
    return tool_turns, "\n".join(texts)


def _expand_openclaw_event(obj: dict, ts_ms):
    """Map one OpenClaw event into zero or more transcript turns.

    Returns a list of ``{role, content, timestamp}`` dicts. Events that are
    pure plumbing (``session.*``, ``context.compiled``, ``agent.heartbeat``)
    or carry no visible content return ``[]`` — never a turn with an empty
    body or a debug-shaped ``role``."""
    etype = obj.get("type", "")
    data = obj.get("data") if isinstance(obj.get("data"), dict) else {}
    turns: list[dict] = []

    # Plumbing events — never visible in the transcript.
    if etype in (
        "session.ended", "session.started", "session.created",
        "context.compiled", "agent.heartbeat",
    ):
        return turns

    if etype == "prompt.submitted":
        text = data.get("finalPromptText") or data.get("text") or data.get("prompt") or ""
        text = _stringify_content(text)
        if text.strip():
            turns.append({"role": "user", "content": text, "timestamp": ts_ms})
        return turns

    if etype == "trace.artifacts":
        # A trace can carry the final prompt, the assistant reply, and the
        # tool calls that fired during the turn — emit each separately.
        prompt = data.get("finalPromptText") or ""
        prompt = _stringify_content(prompt)
        if prompt.strip():
            turns.append({"role": "user", "content": prompt, "timestamp": ts_ms})

        atexts = data.get("assistantTexts")
        if isinstance(atexts, list):
            for at in atexts:
                at_s = _stringify_content(at)
                if at_s.strip():
                    turns.append({"role": "assistant", "content": at_s, "timestamp": ts_ms})
        elif isinstance(atexts, str) and atexts.strip():
            turns.append({"role": "assistant", "content": atexts, "timestamp": ts_ms})

        tool_metas = data.get("toolMetas")
        if isinstance(tool_metas, list):
            for tm in tool_metas:
                if not isinstance(tm, dict):
                    continue
                tname = tm.get("name") or tm.get("tool") or "tool"
                tinput = tm.get("input") or tm.get("arguments") or tm.get("args") or {}
                toutput = tm.get("output") or tm.get("result")
                body_parts = [f"[Tool: {tname}]"]
                try:
                    body_parts.append(json.dumps(tinput, indent=2)[:500])
                except (TypeError, ValueError):
                    body_parts.append(str(tinput)[:500])
                if toutput is not None:
                    try:
                        body_parts.append(json.dumps(toutput, indent=2)[:500])
                    except (TypeError, ValueError):
                        body_parts.append(str(toutput)[:500])
                turns.append({
                    "role": "tool",
                    "content": "\n".join(body_parts),
                    "timestamp": ts_ms,
                })
        return turns

    if etype == "model.completed":
        text = (
            data.get("completionText")
            or data.get("text")
            or data.get("assistantText")
        )
        if text is None:
            atexts = data.get("assistantTexts")
            if isinstance(atexts, list):
                text = "\n".join(_stringify_content(a) for a in atexts if a)
            elif isinstance(atexts, str):
                text = atexts
        text = _stringify_content(text) if text is not None else ""
        if text.strip():
            turns.append({"role": "assistant", "content": text, "timestamp": ts_ms})
        return turns

    if etype in ("tool.call", "tool.invoked"):
        tname = data.get("name") or data.get("tool") or "tool"
        tinput = data.get("input") or data.get("arguments") or data.get("args") or {}
        try:
            body = json.dumps(tinput, indent=2)[:500]
        except (TypeError, ValueError):
            body = str(tinput)[:500]
        turns.append({
            "role": "tool",
            "content": f"[Tool: {tname}]\n{body}",
            "timestamp": ts_ms,
        })
        return turns

    if etype in ("tool.result", "tool.completed"):
        tname = data.get("name") or data.get("tool") or "tool"
        result = data.get("output") or data.get("result") or ""
        try:
            body = json.dumps(result, indent=2)[:500] if not isinstance(result, str) else result[:500]
        except (TypeError, ValueError):
            body = str(result)[:500]
        if body.strip():
            turns.append({
                "role": "tool",
                "content": f"[Tool result: {tname}]\n{body}",
                "timestamp": ts_ms,
            })
        return turns

    # Unknown OpenClaw event — silently skip rather than emit "x.y" role trash.
    return turns


# Sampling parameter keys we surface in the "Decoding" pill. Order is the
# display order in the UI; missing keys are simply dropped.
_DECODING_KEYS = (
    "temperature",
    "top_p",
    "top_k",
    "max_tokens",
    "stop_sequences",
)

# Camel-case → snake-case aliases — adapters write either style depending on
# whether they came from Anthropic SDK (snake), OpenAI SDK (snake), or
# OpenClaw gateway (camel). We collapse them to the canonical snake form.
_DECODING_ALIASES = {
    "maxTokens": "max_tokens",
    "topP": "top_p",
    "topK": "top_k",
    "stopSequences": "stop_sequences",
    "stop": "stop_sequences",
    # OpenAI also calls it max_completion_tokens on newer models; treat the
    # same way so the UI still shows a sensible "max=" value.
    "max_completion_tokens": "max_tokens",
}


def _extract_decoding_params(obj):
    """Pull ``{temperature, top_p, top_k, max_tokens, stop_sequences}`` out of
    a parsed event, no matter which nested shape the adapter chose.

    Handles three nested-key shapes (see issue #564):

    1. ``obj["data"]["params"]``         — OpenClaw gateway model.completed
    2. ``obj["data"]["message"]["params"]`` — Claude Code adapter payload
    3. ``obj["data"]["config"]``         — generic LLM-client wrapper

    Also handles a flat fallback where the params live directly on the
    message dict (``obj["params"]`` / ``obj["config"]``) — common when the
    DuckDB writer has already unwrapped the outer envelope.

    Returns an empty dict when none of the keys are present so callers can
    cheaply test truthiness without first checking ``is not None``. Never
    raises on weird input — bad shapes return ``{}``.
    """
    if not isinstance(obj, dict):
        return {}

    # Candidate buckets, in priority order. The first non-empty bucket wins
    # for any given key; we don't try to merge across buckets to avoid
    # surfacing stale config from a sibling event.
    candidates = []
    data = obj.get("data") if isinstance(obj.get("data"), dict) else None
    if data is not None:
        # Path 1 — data.params  (e.g. model.completed gateway events)
        if isinstance(data.get("params"), dict):
            candidates.append(data["params"])
        # Path 2 — data.message.params  (Anthropic SDK request payload)
        msg = data.get("message") if isinstance(data.get("message"), dict) else None
        if msg and isinstance(msg.get("params"), dict):
            candidates.append(msg["params"])
        if msg and isinstance(msg.get("metadata"), dict):
            md = msg["metadata"]
            if isinstance(md.get("params"), dict):
                candidates.append(md["params"])
        # Path 3 — data.config  (generic wrappers, our own SDK)
        if isinstance(data.get("config"), dict):
            candidates.append(data["config"])
        # Anthropic non-streaming requests sometimes inline these on `data`
        # itself when the writer flattened the message.
        candidates.append(data)

    # Flat fallback — when the caller already passed the message dict.
    if isinstance(obj.get("params"), dict):
        candidates.append(obj["params"])
    if isinstance(obj.get("config"), dict):
        candidates.append(obj["config"])
    candidates.append(obj)

    out = {}
    for bucket in candidates:
        if not isinstance(bucket, dict):
            continue
        for raw_key, val in bucket.items():
            key = _DECODING_ALIASES.get(raw_key, raw_key)
            if key not in _DECODING_KEYS:
                continue
            if key in out:
                continue  # earlier bucket already supplied this key
            # Skip clearly junk values. We accept 0 as a valid temperature.
            if val is None:
                continue
            if key == "stop_sequences":
                if isinstance(val, str):
                    out[key] = [val]
                elif isinstance(val, list):
                    cleaned = [str(s) for s in val if s is not None]
                    if cleaned:
                        out[key] = cleaned
                continue
            if key in ("temperature", "top_p"):
                if isinstance(val, (int, float)):
                    out[key] = float(val)
                continue
            if key in ("top_k", "max_tokens"):
                if isinstance(val, (int, float)):
                    out[key] = int(val)
                continue
    return out


def _try_local_store_transcript(session_id: str, _events=None):
    """Read a session transcript directly from the DuckDB events table.

    Returns the same response shape as the JSONL parser. Returns ``None``
    to defer to the JSONL fallback if the local_store module isn't importable,
    the events table has no rows for this session, or anything raises.

    Handles two event shapes:
    * **Anthropic-style** messages — ``{role, content, usage, tool_calls}``,
      written by Claude Code adapters.
    * **OpenClaw events** — ``{type: "<ns>.<action>", data: {...}}`` — content
      lives in nested fields (``data.finalPromptText``, ``data.assistantTexts``,
      ``data.toolMetas``…), tokens in ``data.promptCache.lastCallUsage``.
    """
    # Issue #1291 cliff #4: route through daemon HTTP proxy. The previous
    # direct ``local_store.get_store()`` open collided with the sync
    # daemon's exclusive DuckDB lock under standard installs (per memory
    # `reference_duckdb_process_lock.md`), forced fall-through to the JSONL
    # walker → 5.5s p95 the latency probe (#1287) surfaced for
    # ``sessions.api_transcript``.
    rows = _events
    if rows is None:
        try:
            from routes.local_query import local_store_via_daemon
            rows = local_store_via_daemon(
                "query_events", session_id=session_id, limit=10000)
        except Exception:
            rows = None
    if rows is None:
        # Single-process fallback (tests/dev with no sync daemon).
        try:
            from clawmetry import local_store
            store = local_store.get_store(read_only=True)
            rows = store.query_events(session_id=session_id, limit=10000)
        except Exception:
            return None
    if not rows:
        # Return None so the caller falls through to the JSONL parser.
        # When DuckDB has no events for a session (broken ingest pipeline or
        # genuinely new session), the JSONL fallback will either serve the
        # real transcript from disk (#1772) or return 404 if no file exists —
        # both are correct. Returning an empty shell here blocks the fallback
        # and produces silent zeros when the pipeline is offline.
        return None
    # query_events returns DESC by ts; transcripts read forward.
    rows = list(reversed(rows))
    messages: list[dict] = []
    model = None
    total_tokens = 0
    first_ts = None
    last_ts = None
    # Anthropic ``tool_result`` blocks reference their call by id only; map
    # id→name as we see ``tool_use`` blocks so results show which tool ran.
    tool_name_by_id: dict = {}
    # When v3 (``model.completed`` / ``prompt.submitted``) events are present
    # they already supply the prose for Claude-Code sessions, so we take *tools*
    # from the raw ``message`` rows but skip their text to avoid doubling the
    # reply. Pure Claude-Code sessions (no v3 events) keep their message text.
    has_v3_messages = any(
        isinstance(r.get("data"), dict)
        and r["data"].get("_v3_type") == "message"
        for r in rows
    )
    for ev in rows:
        obj = ev.get("data")
        if not isinstance(obj, dict):
            continue
        # Issue #1718: skip plumbing event_types (``session.started``,
        # ``model.changed``, ``thinking_level_change``, ``channel.in/out``,
        # ``custom``/``custom_message``, ``queue-operation``, ``attachment``,
        # …) so the transcript modal stops rendering non-message noise as
        # ``{role: "custom_message", ...}`` chat bubbles. The list endpoint
        # (``/api/transcripts``) applies the SAME predicate at the SQL
        # layer, so list-vs-detail counts now agree.
        #
        # Discriminator order (renderable if ANY matches):
        #   1. outer ``event_type`` — production ingest stamps this from
        #      ``data.type`` (real OpenClaw v3 + Claude Code rows).
        #   2. inner ``data.type`` — some older ingest paths and a handful
        #      of test fixtures store a coarse outer type (``"brain"``)
        #      with the real type buried in ``data.type``.
        #   3. inner ``data.role`` — Anthropic-shape rows have no
        #      ``type`` field; they're identified by their top-level role
        #      (``user``/``assistant``/``system``/``tool``/…) and are
        #      always renderable.
        et = (ev.get("event_type") or "").strip()
        inner_type = obj.get("type") if isinstance(obj.get("type"), str) else ""
        inner_role = obj.get("role") if isinstance(obj.get("role"), str) else ""
        renderable = (
            (et and et in _RENDERABLE_TRANSCRIPT_EVENT_TYPES)
            or (inner_type and inner_type in _RENDERABLE_TRANSCRIPT_EVENT_TYPES)
            or (inner_role and inner_role in _RENDERABLE_JSONL_ANTHROPIC_ROLES)
            # Anthropic ``tool_calls``/``tool_use`` rows often omit the
            # top-level role but still render as tool turns.
            or bool(obj.get("tool_calls") or obj.get("tool_use"))
        )
        if not renderable:
            continue
        ts = obj.get("timestamp") or obj.get("time") or obj.get("created_at") or ev.get("ts")
        ts_ms = None
        if ts:
            if isinstance(ts, (int, float)):
                ts_ms = int(ts * 1000) if ts < 1e12 else int(ts)
            else:
                try:
                    ts_ms = int(
                        datetime.fromisoformat(str(ts).replace("Z", "+00:00")).timestamp() * 1000
                    )
                except Exception:
                    ts_ms = None
            if ts_ms:
                if not first_ts or ts_ms < first_ts:
                    first_ts = ts_ms
                if not last_ts or ts_ms > last_ts:
                    last_ts = ts_ms

        if _is_openclaw_event(obj):
            # OpenClaw shape. Pull model from the top-level (modelId preferred),
            # tokens from data.promptCache.lastCallUsage.
            if not model:
                model = obj.get("modelId") or obj.get("model") or ev.get("model")
            data = obj.get("data") if isinstance(obj.get("data"), dict) else {}
            total_tokens += _openclaw_event_tokens(data)
            # Issue #564: surface decoding params on assistant turns so the UI
            # can show the "T=… top_p=… max=…" pill inline with the reply.
            decoding = _extract_decoding_params(obj)
            raw_payload = _bounded_raw_payload(obj)
            for turn in _expand_openclaw_event(obj, ts_ms):
                if not turn.get("content", "").strip():
                    continue
                if decoding and turn.get("role") == "assistant":
                    turn["params"] = decoding
                if raw_payload is not None:
                    turn["raw"] = raw_payload
                messages.append(turn)
            continue

        # Claude-Code shape (#1911): the real Anthropic message is nested under
        # ``data.message`` and tools are content blocks, not top-level keys.
        # Lift each tool_use/tool_result block into a named, deep-divable turn;
        # emit prose only when no v3 event already covered it.
        msg_obj = obj.get("message") if isinstance(obj.get("message"), dict) else None
        if msg_obj is not None:
            raw_payload = _bounded_raw_payload(obj)
            role = msg_obj.get("role") or obj.get("type") or "assistant"
            if not model:
                model = msg_obj.get("model") or obj.get("model") or ev.get("model")
            usage = msg_obj.get("usage")
            if isinstance(usage, dict):
                total_tokens += usage.get("total_tokens", 0) or (
                    (usage.get("input_tokens", 0) or 0)
                    + (usage.get("output_tokens", 0) or 0)
                )
            tool_turns, block_text = _anthropic_tool_turns(
                msg_obj.get("content"), ts_ms, tool_name_by_id)
            for tt in tool_turns:
                if raw_payload is not None:
                    tt["raw"] = raw_payload
                messages.append(tt)
            if block_text.strip() and not has_v3_messages:
                entry = {"role": role, "content": block_text, "timestamp": ts_ms}
                decoding = _extract_decoding_params(obj)
                if decoding and role == "assistant":
                    entry["params"] = decoding
                if raw_payload is not None:
                    entry["raw"] = raw_payload
                messages.append(entry)
            continue

        # Anthropic-style fallback (existing logic).
        role = obj.get("role", obj.get("type", "unknown"))
        content = _stringify_content(obj.get("content", ""))
        raw_payload = _bounded_raw_payload(obj)
        if obj.get("tool_calls") or obj.get("tool_use"):
            tools = obj.get("tool_calls") or obj.get("tool_use") or []
            if isinstance(tools, list):
                for tc in tools:
                    tname = tc.get("name", tc.get("function", {}).get("name", "tool"))
                    messages.append({
                        "role": "tool",
                        "content": f"[Tool Call: {tname}]\n{json.dumps(tc.get('input', tc.get('arguments', {})), indent=2)[:500]}",
                        "timestamp": ts_ms,
                        "raw": _bounded_raw_payload(tc),
                    })
        if role == "tool_result":
            role = "tool"
        if not model:
            model = obj.get("model") or ev.get("model")
        usage = obj.get("usage", {})
        if isinstance(usage, dict):
            total_tokens += usage.get("total_tokens", 0) or (
                usage.get("input_tokens", 0) + usage.get("output_tokens", 0)
            )
        if content or role in ("user", "assistant", "system"):
            msg_entry = {"role": role, "content": content, "timestamp": ts_ms}
            if role == "assistant":
                decoding = _extract_decoding_params(obj)
                if decoding:
                    msg_entry["params"] = decoding
            if raw_payload is not None:
                msg_entry["raw"] = raw_payload
            messages.append(msg_entry)
    duration = None
    if first_ts and last_ts and last_ts > first_ts:
        dur_sec = (last_ts - first_ts) / 1000
        if dur_sec < 60:
            duration = f"{dur_sec:.0f}s"
        elif dur_sec < 3600:
            duration = f"{dur_sec / 60:.0f}m"
        else:
            duration = f"{dur_sec / 3600:.1f}h"
    return {
        "name": session_id[:40],
        "messageCount": len(messages),
        "model": model,
        "totalTokens": total_tokens,
        "duration": duration,
        "messages": messages[:500],
        "_source": "local_store",
    }


@bp_sessions.route("/api/transcript/<session_id>")
def api_transcript(session_id):
    """Parse and return a session transcript for the chat viewer."""
    import dashboard as _d
    if is_local_store_read_enabled():
        fast = _try_local_store_transcript(session_id)
        if fast is not None:
            return jsonify(fast)
    sessions_dir = _d.SESSIONS_DIR or os.path.expanduser(
        "~/.openclaw/agents/main/sessions"
    )
    fpath = os.path.join(sessions_dir, session_id + ".jsonl")
    # Sanitize path
    fpath = os.path.normpath(fpath)
    if not fpath.startswith(os.path.normpath(sessions_dir)):
        return jsonify({"error": "Access denied"}), 403
    if not os.path.exists(fpath):
        return jsonify({"error": "Transcript not found"}), 404

    messages = []
    model = None
    total_tokens = 0
    first_ts = None
    last_ts = None
    try:
        with open(fpath) as f:
            for line in f:
                try:
                    obj = json.loads(line.strip())
                    role = obj.get("role", obj.get("type", "unknown"))
                    content = obj.get("content", "")
                    if isinstance(content, list):
                        parts = []
                        for part in content:
                            if isinstance(part, dict):
                                parts.append(part.get("text", str(part)))
                            else:
                                parts.append(str(part))
                        content = "\n".join(parts)
                    elif not isinstance(content, str):
                        content = str(content) if content else ""
                    # Tool use handling
                    if obj.get("tool_calls") or obj.get("tool_use"):
                        tools = obj.get("tool_calls") or obj.get("tool_use") or []
                        if isinstance(tools, list):
                            for tc in tools:
                                tname = tc.get(
                                    "name", tc.get("function", {}).get("name", "tool")
                                )
                                messages.append(
                                    {
                                        "role": "tool",
                                        "content": f"[Tool Call: {tname}]\n{json.dumps(tc.get('input', tc.get('arguments', {})), indent=2)[:500]}",
                                        "timestamp": obj.get("timestamp")
                                        or obj.get("time"),
                                        "raw": _bounded_raw_payload(tc),
                                    }
                                )
                    if role == "tool_result":
                        role = "tool"
                    ts = (
                        obj.get("timestamp") or obj.get("time") or obj.get("created_at")
                    )
                    if ts:
                        if isinstance(ts, (int, float)):
                            ts_ms = int(ts * 1000) if ts < 1e12 else int(ts)
                        else:
                            try:
                                ts_ms = int(
                                    datetime.fromisoformat(
                                        str(ts).replace("Z", "+00:00")
                                    ).timestamp()
                                    * 1000
                                )
                            except Exception:
                                ts_ms = None
                        if ts_ms:
                            if not first_ts or ts_ms < first_ts:
                                first_ts = ts_ms
                            if not last_ts or ts_ms > last_ts:
                                last_ts = ts_ms
                    else:
                        ts_ms = None
                    if not model:
                        model = obj.get("model")
                    usage = obj.get("usage", {})
                    if isinstance(usage, dict):
                        total_tokens += usage.get("total_tokens", 0) or (
                            usage.get("input_tokens", 0) + usage.get("output_tokens", 0)
                        )
                    if content or role in ("user", "assistant", "system"):
                        msg_entry = {
                            "role": role,
                            "content": content,
                            "timestamp": ts_ms,
                        }
                        # Issue #564: attach decoding config (T/top_p/max…)
                        # to assistant turns so the UI can render an inline
                        # pill next to the reply.
                        if role == "assistant":
                            decoding = _extract_decoding_params(obj)
                            if decoding:
                                msg_entry["params"] = decoding
                        # Issue #1895: verbatim payload for the raw/pretty toggle.
                        raw_payload = _bounded_raw_payload(obj)
                        if raw_payload is not None:
                            msg_entry["raw"] = raw_payload
                        messages.append(msg_entry)
                except (json.JSONDecodeError, ValueError):
                    pass
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    duration = None
    if first_ts and last_ts and last_ts > first_ts:
        dur_sec = (last_ts - first_ts) / 1000
        if dur_sec < 60:
            duration = f"{dur_sec:.0f}s"
        elif dur_sec < 3600:
            duration = f"{dur_sec / 60:.0f}m"
        else:
            duration = f"{dur_sec / 3600:.1f}h"

    return jsonify(
        {
            "name": session_id[:40],
            "messageCount": len(messages),
            "model": model,
            "totalTokens": total_tokens,
            "duration": duration,
            "messages": messages[:500],  # Cap at 500 messages
        }
    )


def _try_local_store_transcript_events(session_id: str):
    """Fast path for /api/transcript-events/<id>. Reads events from DuckDB and
    re-projects them into the structured-event shape the detail modal expects.

    Issue #1088: routes through the daemon HTTP proxy first, with the standard
    direct-open fallback inside ``_ls_call``. Returns ``None`` to defer to the
    JSONL parser when the events table has no rows for this session.

    Issue #1597 class drain: UNIONs sub-agent events so the transcript modal
    on a parent session shows every model/tool turn the parent delegated to a
    Task-tool child. Falls back to the parent-only query when the daemon
    predates the helper (staged rollout).
    """
    rows = _ls_call("query_events_with_subagents", session_id=session_id, limit=10000)
    if rows is None:
        rows = _ls_call("query_events", session_id=session_id, limit=10000)
    if not rows:
        return None
    rows = list(reversed(rows))  # query_events is DESC; the modal reads forward.
    events: list[dict] = []
    msg_count = 0
    for ev in rows:
        ev_type = ev.get("event_type") or ""
        data = ev.get("data") if isinstance(ev.get("data"), dict) else {}
        ts_raw = data.get("timestamp") or data.get("time") or ev.get("ts")
        ts_val = None
        if isinstance(ts_raw, (int, float)):
            ts_val = int(ts_raw * 1000) if ts_raw < 1e12 else int(ts_raw)
        elif ts_raw:
            try:
                ts_val = int(
                    datetime.fromisoformat(str(ts_raw).replace("Z", "+00:00")).timestamp() * 1000
                )
            except Exception:
                ts_val = None

        if ev_type == "model_change":
            events.append({
                "type": "model_change",
                "modelId": data.get("modelId") or data.get("model") or "",
                "provider": data.get("provider") or "",
                "timestamp": ts_val,
            })
            continue
        if ev_type == "thinking_level_change":
            events.append({
                "type": "thinking_level_change",
                "thinkingLevel": data.get("thinkingLevel") or data.get("level") or "",
                "timestamp": ts_val,
            })
            continue

        msg = data.get("message") if isinstance(data.get("message"), dict) else None
        if not msg:
            continue
        role = msg.get("role", "")
        content = msg.get("content", "")
        msg_count += 1

        if isinstance(content, list):
            for block in content:
                if not isinstance(block, dict):
                    continue
                btype = block.get("type", "")
                if btype == "thinking":
                    events.append({
                        "type": "thinking",
                        "text": (block.get("thinking") or "")[:2000],
                        "thinking_chars": len(block.get("thinking") or ""),
                        "timestamp": ts_val,
                    })
                elif btype == "text":
                    text = block.get("text", "") or ""
                    if role == "user":
                        events.append({"type": "user", "text": text[:3000], "timestamp": ts_val})
                    elif role == "assistant":
                        events.append({"type": "agent", "text": text[:3000], "timestamp": ts_val})
                elif btype in ("toolCall", "tool_use"):
                    name = block.get("name", "?")
                    args = block.get("arguments") or block.get("input") or {}
                    args_str = json.dumps(args, indent=2)[:1000] if isinstance(args, dict) else str(args)[:1000]
                    events.append({
                        "type": "tool",
                        "toolName": name,
                        "args": args_str,
                        "timestamp": ts_val,
                    })
        elif isinstance(content, str) and content:
            if role == "user":
                events.append({"type": "user", "text": content[:3000], "timestamp": ts_val})
            elif role == "assistant":
                events.append({"type": "agent", "text": content[:3000], "timestamp": ts_val})
            elif role == "toolResult":
                events.append({"type": "result", "text": content[:2000], "timestamp": ts_val})
    return {
        "events": events[-500:],
        "messageCount": msg_count,
        "totalEvents": len(events),
        "_source": "local_store",
    }


@bp_sessions.route("/api/transcript-events/<session_id>")
def api_transcript_events(session_id):
    """Parse a session transcript JSONL into structured events for the detail modal."""
    import dashboard as _d
    if is_local_store_read_enabled():
        fast = _try_local_store_transcript_events(session_id)
        if fast is not None:
            return jsonify(fast)
    sessions_dir = _d.SESSIONS_DIR or os.path.expanduser(
        "~/.openclaw/agents/main/sessions"
    )
    fpath = os.path.join(sessions_dir, session_id + ".jsonl")
    fpath = os.path.normpath(fpath)
    if not fpath.startswith(os.path.normpath(sessions_dir)):
        return jsonify({"error": "Access denied"}), 403
    if not os.path.exists(fpath):
        return jsonify({"error": "Transcript not found"}), 404

    events = []
    msg_count = 0
    try:
        with open(fpath) as f:
            for line in f:
                try:
                    obj = json.loads(line.strip())
                except (json.JSONDecodeError, ValueError):
                    continue

                ts = obj.get("timestamp") or obj.get("time") or obj.get("created_at")
                ts_val = None
                if ts:
                    if isinstance(ts, (int, float)):
                        ts_val = int(ts * 1000) if ts < 1e12 else int(ts)
                    else:
                        try:
                            ts_val = int(
                                datetime.fromisoformat(
                                    str(ts).replace("Z", "+00:00")
                                ).timestamp()
                                * 1000
                            )
                        except Exception:
                            pass

                obj_type = obj.get("type", "")

                # Emit model_change and thinking_level_change as timeline
                # annotation events so the frontend can render visual dividers.
                if obj_type == "model_change":
                    events.append({
                        "type": "model_change",
                        "modelId": obj.get("modelId") or obj.get("model") or "",
                        "provider": obj.get("provider") or "",
                        "timestamp": ts_val,
                    })
                    continue
                if obj_type == "thinking_level_change":
                    events.append({
                        "type": "thinking_level_change",
                        "thinkingLevel": obj.get("thinkingLevel") or obj.get("level") or "",
                        "timestamp": ts_val,
                    })
                    continue

                if obj_type == "message":  # v3-shape-gate: allow (reason: JSONL on-disk walker — api_transcript_events iterates per-line obj from .jsonl)
                    msg = obj.get("message", {})
                    role = msg.get("role", "")
                    content = msg.get("content", "")
                    msg_count += 1

                    if isinstance(content, list):
                        for block in content:
                            if not isinstance(block, dict):
                                continue
                            btype = block.get("type", "")
                            if btype == "thinking":
                                events.append(
                                    {
                                        "type": "thinking",
                                        "text": block.get("thinking", "")[:2000],
                                        "thinking_chars": len(block.get("thinking", "")),
                                        "timestamp": ts_val,
                                    }
                                )
                            elif btype == "text":
                                text = block.get("text", "")
                                if role == "user":
                                    events.append(
                                        {
                                            "type": "user",
                                            "text": text[:3000],
                                            "timestamp": ts_val,
                                        }
                                    )
                                elif role == "assistant":
                                    events.append(
                                        {
                                            "type": "agent",
                                            "text": text[:3000],
                                            "timestamp": ts_val,
                                        }
                                    )
                            elif btype in ("toolCall", "tool_use"):
                                name = block.get("name", "?")
                                args = (
                                    block.get("arguments") or block.get("input") or {}
                                )
                                args_str = (
                                    json.dumps(args, indent=2)[:1000]
                                    if isinstance(args, dict)
                                    else str(args)[:1000]
                                )
                                if name == "exec":
                                    cmd = (
                                        args.get("command", "")
                                        if isinstance(args, dict)
                                        else ""
                                    )
                                    events.append(
                                        {
                                            "type": "exec",
                                            "command": cmd,
                                            "toolName": name,
                                            "args": args_str,
                                            "timestamp": ts_val,
                                        }
                                    )
                                elif name in ("Read", "read"):
                                    fp = (
                                        (
                                            args.get("file_path")
                                            or args.get("path")
                                            or ""
                                        )
                                        if isinstance(args, dict)
                                        else ""
                                    )
                                    events.append(
                                        {
                                            "type": "read",
                                            "file": fp,
                                            "toolName": name,
                                            "args": args_str,
                                            "timestamp": ts_val,
                                        }
                                    )
                                else:
                                    events.append(
                                        {
                                            "type": "tool",
                                            "toolName": name,
                                            "args": args_str,
                                            "timestamp": ts_val,
                                        }
                                    )
                    elif isinstance(content, str) and content:
                        if role == "user":
                            events.append(
                                {
                                    "type": "user",
                                    "text": content[:3000],
                                    "timestamp": ts_val,
                                }
                            )
                        elif role == "assistant":
                            events.append(
                                {
                                    "type": "agent",
                                    "text": content[:3000],
                                    "timestamp": ts_val,
                                }
                            )
                        elif role == "toolResult":
                            events.append(
                                {
                                    "type": "result",
                                    "text": content[:2000],
                                    "timestamp": ts_val,
                                }
                            )

                    if role == "toolResult" and isinstance(content, list):
                        text_parts = []
                        for block in content:
                            if isinstance(block, dict) and block.get("type") == "text":
                                text_parts.append(block.get("text", ""))
                        if text_parts:
                            events.append(
                                {
                                    "type": "result",
                                    "text": "\n".join(text_parts)[:2000],
                                    "timestamp": ts_val,
                                }
                            )

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify(
        {"events": events[-500:], "messageCount": msg_count, "totalEvents": len(events)}
    )


def _try_local_store_session_model_journey(session_id: str):
    """Fast path for /api/session-model-journey/<id>. Reads ordered
    model_change / thinking_level_change / message rows from DuckDB via
    :meth:`LocalStore.query_session_model_journey` and folds them into
    the same ``segments`` shape the JSONL walker produces.

    Issue #1088 phase 3. Returns ``None`` when the events table has no
    matching rows so the route falls through to the JSONL walker.

    Issue #1597 class drain: uses the sub-agent-rollup variant so a parent
    that delegated to a Task-tool child with a different model (e.g. Opus
    parent → Haiku worker) shows the full model journey instead of just
    the parent's initial line. Falls back to parent-only on older daemons.
    """
    rows = _ls_call(
        "query_session_model_journey_with_subagents",
        session_id=session_id,
        limit=5000,
    )
    if rows is None:
        rows = _ls_call(
            "query_session_model_journey",
            session_id=session_id,
            limit=5000,
        )
    if not rows:
        return None

    def _parse_ts(ts):
        if not ts:
            return 0
        if isinstance(ts, (int, float)):
            return int(ts * 1000) if ts < 1e12 else int(ts)
        try:
            return int(
                datetime.fromisoformat(str(ts).replace("Z", "+00:00")).timestamp() * 1000
            )
        except Exception:
            return 0

    segments: list = []
    thinking_changes: list = []
    current_model = ""
    current_provider = ""
    seg_start_ms = 0
    seg_tokens = 0
    seg_cost = 0.0
    first_ts = 0
    last_ts = 0

    for r in rows:
        ts_ms = _parse_ts(r.get("ts"))
        if ts_ms and not first_ts:
            first_ts = ts_ms
        if ts_ms:
            last_ts = ts_ms
        kind = r.get("kind")
        if kind == "model_change":
            new_model = r.get("model") or ""
            new_provider = r.get("provider") or ""
            if not new_model:
                continue
            if current_model:
                segments.append({
                    "modelId":     current_model,
                    "provider":    current_provider,
                    "start_ms":    seg_start_ms,
                    "end_ms":      ts_ms or last_ts,
                    "duration_ms": max(0, (ts_ms or last_ts) - seg_start_ms) if seg_start_ms else 0,
                    "tokens":      seg_tokens,
                    "cost_usd":    round(seg_cost, 6),
                })
            current_model = new_model
            current_provider = new_provider
            seg_start_ms = ts_ms
            seg_tokens = 0
            seg_cost = 0.0
        elif kind == "thinking_level_change":
            thinking_changes.append({
                "thinkingLevel": r.get("level") or "",
                "timestamp_ms":  ts_ms,
            })
        else:  # message
            msg_model = r.get("model") or ""
            if msg_model and not current_model:
                current_model = msg_model
                current_provider = r.get("provider") or ""
                seg_start_ms = ts_ms or first_ts
            elif msg_model and msg_model != current_model:
                if current_model:
                    segments.append({
                        "modelId":     current_model,
                        "provider":    current_provider,
                        "start_ms":    seg_start_ms,
                        "end_ms":      ts_ms or last_ts,
                        "duration_ms": max(0, (ts_ms or last_ts) - seg_start_ms) if seg_start_ms else 0,
                        "tokens":      seg_tokens,
                        "cost_usd":    round(seg_cost, 6),
                    })
                current_model = msg_model
                current_provider = r.get("provider") or ""
                seg_start_ms = ts_ms
                seg_tokens = 0
                seg_cost = 0.0
            seg_tokens += int(r.get("total_tokens") or 0)
            seg_cost += float(r.get("total_cost") or 0)

    if current_model:
        segments.append({
            "modelId":     current_model,
            "provider":    current_provider,
            "start_ms":    seg_start_ms,
            "end_ms":      last_ts,
            "duration_ms": max(0, last_ts - seg_start_ms) if seg_start_ms else 0,
            "tokens":      seg_tokens,
            "cost_usd":    round(seg_cost, 6),
        })

    total_tokens = sum(s["tokens"] for s in segments)
    total_cost = sum(s["cost_usd"] for s in segments)
    total_duration = max(0, last_ts - first_ts) if first_ts and last_ts else 0
    return {
        "session_id":       session_id,
        "segments":         segments,
        "thinking_changes": thinking_changes,
        "stats": {
            "total_models_used":  len({s["modelId"] for s in segments}),
            "total_segments":     len(segments),
            "total_tokens":       total_tokens,
            "total_cost_usd":     round(total_cost, 6),
            "total_duration_ms":  total_duration,
            "first_ts":           first_ts,
            "last_ts":            last_ts,
        },
        "_source": "local_store",
    }


@bp_sessions.route("/api/session-model-journey/<session_id>")
def api_session_model_journey(session_id):
    """Return the ordered model journey for a session.

    Walks the session JSONL and tracks every model_change and
    thinking_level_change event.  For each segment (period between two
    consecutive model changes) it computes: duration, tokens consumed,
    and estimated cost.  The result powers the "Model Journey" side panel
    in the session detail modal.
    """
    import dashboard as _d
    if is_local_store_read_enabled():
        fast = _try_local_store_session_model_journey(session_id)
        if fast is not None:
            return jsonify(fast)
    sessions_dir = _d.SESSIONS_DIR or os.path.expanduser(
        "~/.openclaw/agents/main/sessions"
    )
    fpath = os.path.join(sessions_dir, session_id + ".jsonl")
    fpath = os.path.normpath(fpath)
    if not fpath.startswith(os.path.normpath(sessions_dir)):
        return jsonify({"error": "Access denied"}), 403
    if not os.path.exists(fpath):
        return jsonify({"error": "Transcript not found"}), 404

    def _parse_ts(ts):
        if not ts:
            return 0
        if isinstance(ts, (int, float)):
            return int(ts * 1000) if ts < 1e12 else int(ts)
        try:
            return int(
                datetime.fromisoformat(str(ts).replace("Z", "+00:00")).timestamp() * 1000
            )
        except Exception:
            return 0

    segments = []
    thinking_changes = []
    current_model = ""
    current_provider = ""
    seg_start_ms = 0
    seg_tokens = 0
    seg_cost = 0.0
    first_ts = 0
    last_ts = 0

    try:
        with open(fpath, "r", errors="replace") as fh:
            for raw in fh:
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    ev = json.loads(raw)
                except Exception:
                    continue
                ts_ms = _parse_ts(ev.get("timestamp") or ev.get("time") or "")
                if ts_ms and not first_ts:
                    first_ts = ts_ms
                if ts_ms:
                    last_ts = ts_ms

                etype = ev.get("type", "")

                if etype == "model_change":
                    new_model = ev.get("modelId") or ev.get("model") or ""
                    new_provider = ev.get("provider") or ""
                    if not new_model:
                        continue
                    if current_model:
                        segments.append({
                            "modelId": current_model,
                            "provider": current_provider,
                            "start_ms": seg_start_ms,
                            "end_ms": ts_ms or last_ts,
                            "duration_ms": max(0, (ts_ms or last_ts) - seg_start_ms) if seg_start_ms else 0,
                            "tokens": seg_tokens,
                            "cost_usd": round(seg_cost, 6),
                        })
                    current_model = new_model
                    current_provider = new_provider
                    seg_start_ms = ts_ms
                    seg_tokens = 0
                    seg_cost = 0.0
                    continue

                if etype == "thinking_level_change":
                    thinking_changes.append({
                        "thinkingLevel": ev.get("thinkingLevel") or ev.get("level") or "",
                        "timestamp_ms": ts_ms,
                    })
                    continue

                if etype == "message":  # v3-shape-gate: allow (reason: JSONL on-disk walker — api_session_model_journey fallback iterates per-line obj from .jsonl)
                    msg = ev.get("message", {}) or {}
                    if not isinstance(msg, dict):
                        continue
                    msg_model = msg.get("model") or ""
                    if msg_model and not current_model:
                        current_model = msg_model
                        current_provider = msg.get("provider") or ""
                        seg_start_ms = ts_ms or first_ts
                    elif msg_model and msg_model != current_model:
                        if current_model:
                            segments.append({
                                "modelId": current_model,
                                "provider": current_provider,
                                "start_ms": seg_start_ms,
                                "end_ms": ts_ms or last_ts,
                                "duration_ms": max(0, (ts_ms or last_ts) - seg_start_ms) if seg_start_ms else 0,
                                "tokens": seg_tokens,
                                "cost_usd": round(seg_cost, 6),
                            })
                        current_model = msg_model
                        current_provider = msg.get("provider") or ""
                        seg_start_ms = ts_ms
                        seg_tokens = 0
                        seg_cost = 0.0

                    usage = msg.get("usage", {}) or {}
                    if isinstance(usage, dict) and usage:
                        seg_tokens += int(usage.get("totalTokens", 0) or 0)
                        cost_obj = usage.get("cost", {}) or {}
                        if isinstance(cost_obj, dict):
                            seg_cost += float(cost_obj.get("total", 0) or 0)
    except Exception as e:
        return jsonify({"error": "parse error: " + str(e)}), 500

    if current_model:
        segments.append({
            "modelId": current_model,
            "provider": current_provider,
            "start_ms": seg_start_ms,
            "end_ms": last_ts,
            "duration_ms": max(0, last_ts - seg_start_ms) if seg_start_ms else 0,
            "tokens": seg_tokens,
            "cost_usd": round(seg_cost, 6),
        })

    total_tokens = sum(s["tokens"] for s in segments)
    total_cost = sum(s["cost_usd"] for s in segments)
    total_duration = max(0, last_ts - first_ts) if first_ts and last_ts else 0

    return jsonify({
        "session_id": session_id,
        "segments": segments,
        "thinking_changes": thinking_changes,
        "stats": {
            "total_models_used": len(set(s["modelId"] for s in segments)),
            "total_segments": len(segments),
            "total_tokens": total_tokens,
            "total_cost_usd": round(total_cost, 6),
            "total_duration_ms": total_duration,
            "first_ts": first_ts,
            "last_ts": last_ts,
        },
    })


def _try_local_store_session_cost_breakdown(session_id: str):
    """Fast path for /api/sessions/<id>/cost-breakdown. Reads per-turn
    cost+token breakdown from DuckDB events for the given session.

    Issue #1088: routes through the daemon HTTP proxy first (cross-process
    safe), with a direct ``get_store()`` fallback for single-process boots.

    Returns ``None`` to defer to the JSONL parser if:
      - neither path can reach the local store
      - no events exist for this session_id (fresh sync, etc.)
      - data blobs aren't shaped like assistant messages
      - any unexpected error happens

    Issue #1597 class drain: UNIONs sub-agent events so the per-turn cost
    breakdown attributes Task-tool sub-agent turns back to the parent.
    Falls back to the parent-only query on older daemons.
    """
    evs = _ls_call("query_events_with_subagents", session_id=session_id, limit=5000)
    if evs is None:
        evs = _ls_call("query_events", session_id=session_id, limit=5000)
    if not evs:
        return None
    # Walk events oldest-first so turn_index is meaningful.
    evs_sorted = sorted(evs, key=lambda e: e.get("ts") or "")
    turns = []
    last_seen_model = ""
    turn_index = 0
    saw_assistant = False
    for ev in evs_sorted:
        data = ev.get("data") if isinstance(ev.get("data"), dict) else {}
        if ev.get("event_type") == "model_change":
            m = data.get("modelId") or data.get("model") or ev.get("model") or ""
            if m:
                last_seen_model = m
            continue
        # Only assistant-message events carry usage in the OpenClaw schema.
        msg = data.get("message") if isinstance(data.get("message"), dict) else None
        if not msg or msg.get("role") != "assistant":
            continue
        usage = msg.get("usage") or {}
        if not isinstance(usage, dict):
            continue
        saw_assistant = True
        turn_index += 1
        msg_model = msg.get("model") or last_seen_model or ev.get("model") or "unknown"
        if msg_model:
            last_seen_model = msg_model
        in_tok = int(usage.get("input", 0) or 0)
        out_tok = int(usage.get("output", 0) or 0)
        cr_tok = int(usage.get("cacheRead", 0) or 0)
        cw_tok = int(usage.get("cacheWrite", 0) or 0)
        cost_obj = usage.get("cost", {}) or {}
        if isinstance(cost_obj, dict):
            in_cost = float(cost_obj.get("input", 0) or 0)
            out_cost = float(cost_obj.get("output", 0) or 0)
            cr_cost = float(cost_obj.get("cacheRead", 0) or 0)
            cw_cost = float(cost_obj.get("cacheWrite", 0) or 0)
            tot_cost = float(cost_obj.get("total", 0) or 0)
        else:
            in_cost = out_cost = cr_cost = cw_cost = tot_cost = 0.0
        if tot_cost == 0.0 and (in_cost + out_cost + cr_cost + cw_cost) > 0:
            tot_cost = in_cost + out_cost + cr_cost + cw_cost
        turns.append({
            "turn_index": turn_index,
            "model": msg_model,
            "timestamp": ev.get("ts") if isinstance(ev.get("ts"), str) else None,
            "input_tokens": in_tok,
            "output_tokens": out_tok,
            "cache_read_tokens": cr_tok,
            "cache_write_tokens": cw_tok,
            "input_cost_usd": round(in_cost, 8),
            "output_cost_usd": round(out_cost, 8),
            "cache_read_cost_usd": round(cr_cost, 8),
            "cache_write_cost_usd": round(cw_cost, 8),
            "total_cost_usd": round(tot_cost, 8),
        })
    if not saw_assistant:
        return None

    def _s(field):
        return sum(t[field] for t in turns)

    tot_in = _s("input_tokens")
    tot_out = _s("output_tokens")
    tot_cr = _s("cache_read_tokens")
    tot_cw = _s("cache_write_tokens")
    tot_in_cost = _s("input_cost_usd")
    tot_out_cost = _s("output_cost_usd")
    tot_cr_cost = _s("cache_read_cost_usd")
    tot_cw_cost = _s("cache_write_cost_usd")
    tot_cost = _s("total_cost_usd")
    in_plus_cache = tot_in + tot_cr
    cache_hit_pct = round(tot_cr / in_plus_cache * 100, 1) if in_plus_cache > 0 else 0.0
    est_fresh_cost = tot_cr_cost * 10.0
    est_savings = max(0.0, est_fresh_cost - tot_cr_cost)
    est_savings_pct = (
        round(est_savings / (tot_in_cost + est_fresh_cost) * 100, 1)
        if (tot_in_cost + est_fresh_cost) > 0
        else 0.0
    )
    return {
        "session_id": session_id,
        "turns": turns,
        "totals": {
            "input_tokens": tot_in,
            "output_tokens": tot_out,
            "cache_read_tokens": tot_cr,
            "cache_write_tokens": tot_cw,
            "total_tokens": tot_in + tot_out + tot_cr + tot_cw,
            "input_cost_usd": round(tot_in_cost, 6),
            "output_cost_usd": round(tot_out_cost, 6),
            "cache_read_cost_usd": round(tot_cr_cost, 6),
            "cache_write_cost_usd": round(tot_cw_cost, 6),
            "total_cost_usd": round(tot_cost, 6),
        },
        "cache_hit_ratio_pct": cache_hit_pct,
        "est_cache_savings_usd": round(est_savings, 6),
        "est_cache_savings_pct": est_savings_pct,
        "turn_count": len(turns),
        "_source": "local_store",
    }


@bp_sessions.route("/api/sessions/<session_id>/cost-breakdown")
def api_session_cost_breakdown(session_id):
    """Per-turn token + cost breakdown for a single session (GH #604)."""
    import dashboard as _d

    # Epic #964 — opt-in DuckDB fast path.
    if is_local_store_read_enabled():
        fast = _try_local_store_session_cost_breakdown(session_id)
        if fast is not None:
            return jsonify(fast)

    sessions_dir = _d.SESSIONS_DIR or os.path.expanduser(
        "~/.openclaw/agents/main/sessions"
    )
    fpath = os.path.join(sessions_dir, session_id + ".jsonl")
    fpath = os.path.normpath(fpath)
    if not fpath.startswith(os.path.normpath(sessions_dir)):
        return jsonify({"error": "Access denied"}), 403
    if not os.path.exists(fpath):
        return jsonify({"error": "Session not found"}), 404

    turns = []
    last_seen_model = ""
    turn_index = 0

    try:
        with open(fpath, "r", errors="replace") as fh:
            for raw in fh:
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    ev = json.loads(raw)
                except Exception:
                    continue

                ev_type = ev.get("type", "")
                if ev_type == "model_change":
                    m = ev.get("modelId") or ev.get("model") or ""
                    if m:
                        last_seen_model = m
                    continue
                if ev_type != "message":
                    continue

                msg = ev.get("message", {}) or {}
                if not isinstance(msg, dict) or msg.get("role") != "assistant":
                    continue

                usage = msg.get("usage", {}) or {}
                if not isinstance(usage, dict):
                    continue

                turn_index += 1
                msg_model = msg.get("model") or last_seen_model or "unknown"
                if msg_model:
                    last_seen_model = msg_model

                in_tok = int(usage.get("input", 0) or 0)
                out_tok = int(usage.get("output", 0) or 0)
                cr_tok = int(usage.get("cacheRead", 0) or 0)
                cw_tok = int(usage.get("cacheWrite", 0) or 0)
                cost_obj = usage.get("cost", {}) or {}
                if isinstance(cost_obj, dict):
                    in_cost = float(cost_obj.get("input", 0) or 0)
                    out_cost = float(cost_obj.get("output", 0) or 0)
                    cr_cost = float(cost_obj.get("cacheRead", 0) or 0)
                    cw_cost = float(cost_obj.get("cacheWrite", 0) or 0)
                    tot_cost = float(cost_obj.get("total", 0) or 0)
                else:
                    in_cost = out_cost = cr_cost = cw_cost = tot_cost = 0.0
                if tot_cost == 0.0 and (in_cost + out_cost + cr_cost + cw_cost) > 0:
                    tot_cost = in_cost + out_cost + cr_cost + cw_cost

                ts_raw = ev.get("timestamp") or ev.get("time") or None
                turns.append({
                    "turn_index": turn_index,
                    "model": msg_model,
                    "timestamp": ts_raw if isinstance(ts_raw, str) else None,
                    "input_tokens": in_tok,
                    "output_tokens": out_tok,
                    "cache_read_tokens": cr_tok,
                    "cache_write_tokens": cw_tok,
                    "input_cost_usd": round(in_cost, 8),
                    "output_cost_usd": round(out_cost, 8),
                    "cache_read_cost_usd": round(cr_cost, 8),
                    "cache_write_cost_usd": round(cw_cost, 8),
                    "total_cost_usd": round(tot_cost, 8),
                })
    except Exception as e:
        return jsonify({"error": "parse error: " + str(e)}), 500

    def _s(field):
        return sum(t[field] for t in turns)

    tot_in = _s("input_tokens")
    tot_out = _s("output_tokens")
    tot_cr = _s("cache_read_tokens")
    tot_cw = _s("cache_write_tokens")
    tot_in_cost = _s("input_cost_usd")
    tot_out_cost = _s("output_cost_usd")
    tot_cr_cost = _s("cache_read_cost_usd")
    tot_cw_cost = _s("cache_write_cost_usd")
    tot_cost = _s("total_cost_usd")

    in_plus_cache = tot_in + tot_cr
    cache_hit_pct = round(tot_cr / in_plus_cache * 100, 1) if in_plus_cache > 0 else 0.0

    est_fresh_cost = tot_cr_cost * 10.0
    est_savings = max(0.0, est_fresh_cost - tot_cr_cost)
    est_savings_pct = (
        round(est_savings / (tot_in_cost + est_fresh_cost) * 100, 1)
        if (tot_in_cost + est_fresh_cost) > 0
        else 0.0
    )

    return jsonify({
        "session_id": session_id,
        "turns": turns,
        "totals": {
            "input_tokens": tot_in,
            "output_tokens": tot_out,
            "cache_read_tokens": tot_cr,
            "cache_write_tokens": tot_cw,
            "total_tokens": tot_in + tot_out + tot_cr + tot_cw,
            "input_cost_usd": round(tot_in_cost, 6),
            "output_cost_usd": round(tot_out_cost, 6),
            "cache_read_cost_usd": round(tot_cr_cost, 6),
            "cache_write_cost_usd": round(tot_cw_cost, 6),
            "total_cost_usd": round(tot_cost, 6),
        },
        "cache_hit_ratio_pct": cache_hit_pct,
        "est_cache_savings_usd": round(est_savings, 6),
        "est_cache_savings_pct": est_savings_pct,
        "turn_count": len(turns),
    })


def _try_local_store_session_export(session_id: str):
    """Fast path for /api/sessions/<id>/export (JSON shape).

    Reads events from DuckDB and re-projects them into the same export shape
    the JSONL parser produces. Issue #1088 — uses ``_ls_call`` so the daemon
    HTTP proxy fires under the standard install.

    v3-silent-zero fix (issue #1588): the legacy version filtered on
    ``ev_type == 'message'`` which silently matched ZERO rows on every real
    OpenClaw v3 install (daemon writes ``assistant`` / ``model.completed`` /
    ``prompt.submitted`` / ``tool.call`` / ``tool.result``). Endpoint
    returned an empty ``messages`` array and the JSONL fallback never fired.
    Same family as PR #1583 (token-attribution). This version:

    * Filters on the union of pre-v3 ('message') AND v3 names so both
      shapes hydrate the export.
    * Dedupes the v3 sibling pair (``assistant`` + slim ``model.completed``
      ~100 ms apart) via ``build_sibling_bucket_max`` so we don't emit the
      same turn twice.
    * Falls back to the daemon-stamped ``token_count`` / ``cost_usd``
      scalar columns when a standalone ``model.completed`` row has no rich
      sibling — defends against the Eng G "replace aggregate with deduped
      subset" failure mode.
    * Returns ``None`` (not an empty-messages dict) when no attributable
      rows survived, so the JSONL parser fallback fires.

    Issue #1597 class drain: the export now UNIONs sub-agent events so
    downstream re-import / audit pipelines see the full delegated work, not
    just the parent's direct turns. Falls back to parent-only on older
    daemons (pre-#1611 wheel).
    """
    rows = _ls_call("query_events_with_subagents", session_id=session_id, limit=10000)
    if rows is None:
        rows = _ls_call("query_events", session_id=session_id, limit=10000)
    if not rows:
        return None
    rows = list(reversed(rows))  # query_events is DESC; export reads forward.

    # Sibling-pair dedupe (issue #1451 family). Build the bucket map BEFORE
    # the projection loop so we can skip slim ``model.completed`` rows that
    # have a richer ``assistant`` / ``message`` sibling in the same
    # (sid, sec±1) window.
    bucket_max = build_sibling_bucket_max(rows)

    # Event-type → role mapping for v3 + legacy shapes. Tool-result rows
    # don't carry a "role" in the chat sense — they're attributed under
    # ``tool_calls`` rather than ``messages``.
    _MSG_EVENT_TYPES = {
        "message",          # pre-v3 synthetic
        "assistant",        # v3 rich envelope
        "model.completed",  # v3 slim sibling (only used when standalone)
        "prompt.submitted", # v3 user-turn
        "user",             # legacy / v3 fallback
    }
    _ROLE_BY_EVENT = {
        "message":          None,           # use msg.role from envelope
        "assistant":        "assistant",
        "model.completed":  "assistant",
        "prompt.submitted": "user",
        "user":             "user",
    }

    out = {
        "session_id": session_id,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "messages": [],
        "tool_calls": [],
        "cost_data": {
            "total_tokens": 0, "input_tokens": 0, "output_tokens": 0,
            "cache_read_tokens": 0, "cache_write_tokens": 0,
            "total_cost_usd": 0.0,
        },
        "metadata": {
            "start_time": None, "end_time": None, "model": None,
            "message_count": 0, "tool_call_count": 0,
        },
        "_source": "local_store",
    }
    model = None
    start_time = None
    end_time = None
    for ev in rows:
        ev_type = ev.get("event_type") or ""
        data = ev.get("data") if isinstance(ev.get("data"), dict) else {}
        ts_str = data.get("timestamp") or ev.get("ts")
        ts_ms = None
        if isinstance(ts_str, (int, float)):
            ts_ms = int(ts_str * 1000) if ts_str < 1e12 else int(ts_str)
        elif ts_str:
            try:
                ts_ms = int(datetime.fromisoformat(str(ts_str).replace("Z", "+00:00")).timestamp() * 1000)
            except Exception:
                ts_ms = None
        if ev_type == "model_change" or ev_type == "model.changed":
            mid = data.get("modelId") or data.get("model")
            if mid:
                model = mid
                out["metadata"]["model"] = model
        elif ev_type in _MSG_EVENT_TYPES:
            # Skip the slim sibling when a richer envelope already covers
            # this (sid, sec±1) bucket. Otherwise the same billable turn
            # would emit two ``messages[]`` entries.
            if is_sibling_dup(ev, bucket_max):
                if ts_ms:
                    if start_time is None or ts_ms < start_time:
                        start_time = ts_ms
                    if end_time is None or ts_ms > end_time:
                        end_time = ts_ms
                continue

            msg = data.get("message") if isinstance(data.get("message"), dict) else {}
            content = msg.get("content", [])
            usage = msg.get("usage") or {}
            # Role: prefer the explicit envelope role; fall back to the
            # event-type inference so v3 ``prompt.submitted`` rows still
            # render as ``user`` even when the envelope is bare.
            role = msg.get("role", "") or _ROLE_BY_EVENT.get(ev_type) or ""
            text_parts: list[str] = []
            tool_calls_in_msg: list[dict] = []
            if isinstance(content, list):
                for block in content:
                    if not isinstance(block, dict):
                        continue
                    btype = block.get("type", "")
                    if btype == "text":
                        text_parts.append(block.get("text", "") or "")
                    elif btype == "thinking":
                        text_parts.append(f"[THINKING] {block.get('thinking', '')}")
                    elif btype in ("toolCall", "tool_use"):
                        tool_calls_in_msg.append({
                            "id": block.get("id", ""),
                            "name": block.get("name", ""),
                            "arguments": block.get("arguments") or block.get("input") or {},
                        })
            elif isinstance(content, str):
                text_parts.append(content)
            # v3 ``prompt.submitted`` carries the user text in
            # ``data.finalPromptText`` (per reference_openclaw_v3_event_types.md),
            # not in a chat envelope. Surface it so the export isn't
            # silently empty for prompt rows.
            if not text_parts and isinstance(data, dict):
                fpt = data.get("finalPromptText") or data.get("promptText")
                if isinstance(fpt, str) and fpt:
                    text_parts.append(fpt)
            msg_entry = {
                "timestamp": ts_str if isinstance(ts_str, str) else None,
                "role": role,
                "content": "\n".join(text_parts) if text_parts else None,
                "model": msg.get("model") or model,
            }
            in_t = out_t = cr_t = cw_t = 0
            cost_total = 0.0
            if isinstance(usage, dict) and usage:
                in_t = int(usage.get("input", 0) or usage.get("input_tokens", 0) or 0)
                out_t = int(usage.get("output", 0) or usage.get("output_tokens", 0) or 0)
                cr_t = int(usage.get("cacheRead", 0) or usage.get("cache_read_input_tokens", 0) or 0)
                cw_t = int(usage.get("cacheWrite", 0) or usage.get("cache_creation_input_tokens", 0) or 0)
                cost_obj = usage.get("cost") or {}
                if isinstance(cost_obj, dict):
                    cost_total = float(cost_obj.get("total", 0) or 0)
            # Scalar-column fallback (defends against Eng G's
            # "blind-replace-aggregate-with-deduped-subset" failure mode):
            # if the data blob carried no usage splits, attribute the
            # daemon-stamped scalar columns so a standalone
            # ``model.completed`` row still shows up in the export.
            if in_t + out_t + cr_t + cw_t == 0:
                col_tok = int(ev.get("token_count") or 0)
                if col_tok > 0:
                    in_t = col_tok
            if cost_total <= 0:
                try:
                    col_cost = float(ev.get("cost_usd") or 0.0)
                except (TypeError, ValueError):
                    col_cost = 0.0
                if col_cost > 0:
                    cost_total = col_cost
            if in_t + out_t + cr_t + cw_t > 0 or cost_total > 0:
                msg_entry["tokens"] = {
                    "input": in_t, "output": out_t,
                    "cache_read": cr_t, "cache_write": cw_t,
                    "total": in_t + out_t + cr_t + cw_t,
                }
                msg_entry["cost_usd"] = cost_total
                out["cost_data"]["total_cost_usd"] += cost_total
                out["cost_data"]["input_tokens"] += in_t
                out["cost_data"]["output_tokens"] += out_t
                out["cost_data"]["cache_read_tokens"] += cr_t
                out["cost_data"]["cache_write_tokens"] += cw_t
                out["cost_data"]["total_tokens"] += in_t + out_t + cr_t + cw_t
            out["messages"].append(msg_entry)
            out["metadata"]["message_count"] += 1
            for tc in tool_calls_in_msg:
                out["tool_calls"].append({
                    "timestamp": ts_str if isinstance(ts_str, str) else None,
                    "tool_call_id": tc.get("id"),
                    "tool_name": tc.get("name"),
                    "arguments": tc.get("arguments"),
                    "model": msg.get("model") or model,
                })
                out["metadata"]["tool_call_count"] += 1
        elif ev_type in ("tool.call", "tool_call"):
            # v3 explicit tool-call event (outside an assistant envelope).
            tname = data.get("toolName") or data.get("name") or data.get("tool")
            if tname:
                out["tool_calls"].append({
                    "timestamp": ts_str if isinstance(ts_str, str) else None,
                    "tool_call_id": data.get("toolCallId") or data.get("id"),
                    "tool_name": tname,
                    "arguments": data.get("arguments") or data.get("input") or {},
                    "model": model,
                })
                out["metadata"]["tool_call_count"] += 1
        if ts_ms:
            if start_time is None or ts_ms < start_time:
                start_time = ts_ms
            if end_time is None or ts_ms > end_time:
                end_time = ts_ms

    # Return None (not an empty-messages shell) when no projectable rows
    # survived, so the JSONL parser fallback fires instead of mis-tagging
    # an empty answer as ``_source: 'local_store'``. This is the exact
    # mistake the 6 prior fixes (PR #1571/#1576/#1580/#1583/etc.) made.
    if not out["messages"] and not out["tool_calls"]:
        return None

    out["metadata"]["start_time_ms"] = start_time
    out["metadata"]["end_time_ms"] = end_time
    return out


@bp_sessions.route("/api/sessions/<session_id>/export")
def api_session_export(session_id):
    """Export session data as JSON or CSV for external analysis (closes #593)."""
    import dashboard as _d

    export_format = request.args.get("format", "json").lower()
    if export_format not in ("json", "csv"):
        return jsonify({"error": "Invalid format. Use 'json' or 'csv'"}), 400

    # JSON-only fast path — CSV branch falls through to the legacy parser
    # because it relies on text formatting that's not worth duplicating.
    if export_format == "json" and is_local_store_read_enabled():
        fast = _try_local_store_session_export(session_id)
        if fast is not None:
            return Response(
                json.dumps(fast, indent=2, default=str),
                mimetype="application/json",
                headers={"Content-Disposition": f'attachment; filename="{session_id}.json"'},
            )

    sessions_dir = _d.SESSIONS_DIR or os.path.expanduser(
        "~/.openclaw/agents/main/sessions"
    )
    fpath = os.path.join(sessions_dir, session_id + ".jsonl")
    fpath = os.path.normpath(fpath)
    if not fpath.startswith(os.path.normpath(sessions_dir)):
        return jsonify({"error": "Access denied"}), 403
    if not os.path.exists(fpath):
        return jsonify({"error": "Session not found"}), 404

    # Parse the session file
    session_data = {
        "session_id": session_id,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "messages": [],
        "tool_calls": [],
        "cost_data": {
            "total_tokens": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "cache_read_tokens": 0,
            "cache_write_tokens": 0,
            "total_cost_usd": 0.0,
        },
        "metadata": {
            "start_time": None,
            "end_time": None,
            "model": None,
            "message_count": 0,
            "tool_call_count": 0,
        },
    }

    messages = []
    tool_calls = []
    model = None
    start_time = None
    end_time = None

    def _parse_ts(ts):
        if not ts:
            return None
        if isinstance(ts, (int, float)):
            return int(ts * 1000) if ts < 1e12 else int(ts)
        try:
            dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
            return int(dt.timestamp() * 1000)
        except Exception:
            return None

    try:
        with open(fpath, "r", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue

                ev_type = obj.get("type", "")
                ts = _parse_ts(obj.get("timestamp"))

                if ev_type == "session":
                    session_data["metadata"]["start_time"] = obj.get("timestamp")
                elif ev_type == "model_change":
                    if obj.get("modelId"):
                        model = obj.get("modelId")
                        session_data["metadata"]["model"] = model
                elif ev_type == "message":  # v3-shape-gate: allow (reason: JSONL on-disk walker — api_session_export fallback iterates per-line obj from .jsonl)
                    msg = obj.get("message", {})
                    role = msg.get("role", "")
                    content = msg.get("content", [])
                    usage = msg.get("usage", {}) or {}

                    # Extract text content
                    text_parts = []
                    tool_calls_in_msg = []
                    
                    if isinstance(content, list):
                        for block in content:
                            if isinstance(block, dict):
                                btype = block.get("type", "")
                                if btype == "text":
                                    text_parts.append(block.get("text", ""))
                                elif btype == "thinking":
                                    text_parts.append(f"[THINKING] {block.get('thinking', '')}")
                                elif btype in ("toolCall", "tool_use"):
                                    tool_calls_in_msg.append({
                                        "id": block.get("id", ""),
                                        "name": block.get("name", ""),
                                        "arguments": block.get("arguments", {}),
                                    })
                    elif isinstance(content, str):
                        text_parts.append(content)

                    msg_entry = {
                        "timestamp": obj.get("timestamp"),
                        "role": role,
                        "content": "\n".join(text_parts) if text_parts else None,
                        "model": msg.get("model") or model,
                    }

                    # Add usage data
                    if usage:
                        msg_entry["tokens"] = {
                            "input": usage.get("input", 0),
                            "output": usage.get("output", 0),
                            "cache_read": usage.get("cacheRead", 0),
                            "cache_write": usage.get("cacheWrite", 0),
                            "total": usage.get("totalTokens", usage.get("input", 0) + usage.get("output", 0)),
                        }
                        cost_obj = usage.get("cost", {})
                        if isinstance(cost_obj, dict):
                            msg_entry["cost_usd"] = cost_obj.get("total", 0.0)
                            # Accumulate session cost data
                            session_data["cost_data"]["total_cost_usd"] += float(cost_obj.get("total", 0) or 0)
                            session_data["cost_data"]["input_tokens"] += int(usage.get("input", 0) or 0)
                            session_data["cost_data"]["output_tokens"] += int(usage.get("output", 0) or 0)
                            session_data["cost_data"]["cache_read_tokens"] += int(usage.get("cacheRead", 0) or 0)
                            session_data["cost_data"]["cache_write_tokens"] += int(usage.get("cacheWrite", 0) or 0)
                            session_data["cost_data"]["total_tokens"] += (
                                int(usage.get("input", 0) or 0) +
                                int(usage.get("output", 0) or 0) +
                                int(usage.get("cacheRead", 0) or 0) +
                                int(usage.get("cacheWrite", 0) or 0)
                            )

                    messages.append(msg_entry)
                    session_data["metadata"]["message_count"] += 1

                    if tool_calls_in_msg:
                        for tc in tool_calls_in_msg:
                            tool_call_entry = {
                                "timestamp": obj.get("timestamp"),
                                "tool_call_id": tc.get("id"),
                                "tool_name": tc.get("name"),
                                "arguments": tc.get("arguments"),
                                "model": msg.get("model") or model,
                            }
                            tool_calls.append(tool_call_entry)
                            session_data["metadata"]["tool_call_count"] += 1

                elif ev_type == "compaction":
                    session_data["compaction"] = {
                        "timestamp": obj.get("timestamp"),
                        "tokens_before": obj.get("tokensBefore"),
                        "summary": obj.get("summary", "")[:500],
                    }

                # Track start/end times
                if ts:
                    if start_time is None or ts < start_time:
                        start_time = ts
                    if end_time is None or ts > end_time:
                        end_time = ts

    except Exception as e:
        return jsonify({"error": f"Failed to parse session: {str(e)}"}), 500

    session_data["messages"] = messages
    session_data["tool_calls"] = tool_calls
    session_data["metadata"]["start_time_ms"] = start_time
    session_data["metadata"]["end_time_ms"] = end_time

    if export_format == "json":
        return Response(
            json.dumps(session_data, indent=2, default=str),
            mimetype="application/json",
            headers={
                "Content-Disposition": f'attachment; filename="{session_id}.json"'
            }
        )

    elif export_format == "csv":
        # Flatten data for CSV
        output = []
        
        # Add metadata row
        output.append(["# Session Export", session_id])
        output.append(["# Exported At", session_data["exported_at"]])
        output.append(["# Total Messages", session_data["metadata"]["message_count"]])
        output.append(["# Total Tool Calls", session_data["metadata"]["tool_call_count"]])
        output.append(["# Total Tokens", session_data["cost_data"]["total_tokens"]])
        output.append(["# Total Cost USD", round(session_data["cost_data"]["total_cost_usd"], 6)])
        output.append([])

        # Messages section
        if messages:
            output.append(["## MESSAGES"])
            output.append(["Timestamp", "Role", "Model", "Content", "Input Tokens", "Output Tokens", "Total Tokens", "Cost USD"])
            for msg in messages:
                tokens = msg.get("tokens", {})
                output.append([
                    msg.get("timestamp", ""),
                    msg.get("role", ""),
                    msg.get("model", ""),
                    (msg.get("content", "") or "")[:500],  # Truncate long content
                    tokens.get("input", 0),
                    tokens.get("output", 0),
                    tokens.get("total", 0),
                    msg.get("cost_usd", 0.0),
                ])
            output.append([])

        # Tool calls section
        if tool_calls:
            output.append(["## TOOL CALLS"])
            output.append(["Timestamp", "Tool Call ID", "Tool Name", "Model", "Arguments"])
            for tc in tool_calls:
                args_str = json.dumps(tc.get("arguments", {}))[:500] if tc.get("arguments") else ""
                output.append([
                    tc.get("timestamp", ""),
                    tc.get("tool_call_id", ""),
                    tc.get("tool_name", ""),
                    tc.get("model", ""),
                    args_str,
                ])

        # Generate CSV
        import io
        csv_buffer = io.StringIO()
        writer = csv.writer(csv_buffer)
        writer.writerows(output)
        csv_data = csv_buffer.getvalue()

        return Response(
            csv_data,
            mimetype="text/csv",
            headers={
                "Content-Disposition": f'attachment; filename="{session_id}.csv"'
            }
        )


# ── Model-transition detection ──────────────────────────────────────────────


def _detect_model_transitions(path):
    """Scan a session JSONL and return turns where model or provider changed.

    Returns a list of dicts: {turn, ts, from_model, from_provider,
    to_model, to_provider}.  Empty list when no transitions exist or the
    file cannot be read.
    """
    transitions = []
    prev_model = None
    prev_provider = None
    turn = 0
    try:
        with open(path, "r", errors="replace") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                # Support both OpenClaw envelope ({type:"message", message:{…}})
                # and raw {role, model, …} formats.
                msg = obj
                if obj.get("type") in ("message", "user", "assistant") and isinstance(
                    obj.get("message"), dict
                ):
                    msg = obj["message"]
                if msg.get("role") != "assistant":
                    continue
                turn += 1
                model = (msg.get("model") or "").strip()
                provider = (msg.get("provider") or "").strip()
                ts = (
                    obj.get("timestamp")
                    or obj.get("time")
                    or msg.get("timestamp")
                    or ""
                )
                if prev_model is not None and model and (
                    model != prev_model or provider != prev_provider
                ):
                    transitions.append(
                        {
                            "turn": turn,
                            "ts": ts,
                            "from_model": prev_model,
                            "from_provider": prev_provider,
                            "to_model": model,
                            "to_provider": provider,
                        }
                    )
                if model:
                    prev_model = model
                    prev_provider = provider
                elif prev_model is None:
                    prev_model = ""
                    prev_provider = ""
    except Exception:
        pass
    return transitions


def _try_local_store_model_transitions(sid: str):
    """Tier-1 DuckDB fast path for /api/sessions/<sid>/model-transitions
    (issue #1565). Reads ``event_type='model.changed'`` rows for one
    session out of the DuckDB ``events`` table and folds them into the
    same ``transitions`` shape the legacy JSONL walker produces.

    Real OpenClaw v3 emits an explicit ``model_change`` JSONL event for
    every model switch, which the sync daemon namespaces to
    ``model.changed`` (see ``reference_openclaw_v3_event_types.md`` +
    ``tests/test_v3_schema_parser.py::test_v3_model_change_becomes_model_changed``).
    Each row's ``data`` blob carries ``modelId`` + ``provider`` — the
    only fields the response needs. ``turn`` is the 1-based ordinal of
    the transition (i.e. position in the model.changed sequence) since
    we no longer have a cheap assistant-message counter without a
    second query.

    Returns ``None`` when no ``model.changed`` rows exist for the
    session so the legacy JSONL walker still fires for older OpenClaw
    installs (pre-v3 daemons, or sessions ingested before the namespace
    rewrite landed).
    """
    if not sid:
        return None
    rows = _ls_call(
        "query_events",
        session_id=sid,
        event_type="model.changed",
        limit=5000,
    )
    if not rows:
        return None
    # ``query_events`` returns most-recent first; transitions need chronological.
    rows = sorted(rows, key=lambda r: (r.get("ts") or "", r.get("id") or 0))

    transitions: list = []
    prev_model = None
    prev_provider = None
    turn = 0
    for r in rows:
        data = r.get("data") if isinstance(r.get("data"), dict) else {}
        model = (data.get("modelId") or data.get("model") or r.get("model") or "").strip()
        provider = (data.get("provider") or "").strip()
        if not model:
            continue
        turn += 1
        if prev_model is not None and (
            model != prev_model or provider != prev_provider
        ):
            transitions.append({
                "turn":          turn,
                "ts":            r.get("ts") or "",
                "from_model":    prev_model,
                "from_provider": prev_provider,
                "to_model":      model,
                "to_provider":   provider,
            })
        prev_model = model
        prev_provider = provider

    return {
        "sessionId":       sid,
        "transitions":     transitions,
        "count":           len(transitions),
        "has_transitions": bool(transitions),
        "_source":         "local_store",
    }


@bp_sessions.route("/api/sessions/<sid>/model-transitions")
def api_session_model_transitions(sid):
    """Return model/provider transitions detected within a single session."""
    import dashboard as _d
    if not sid or any(c in sid for c in ("/", "\\", "..")):
        return jsonify({"error": "invalid session id"}), 400
    if is_local_store_read_enabled():
        fast = _try_local_store_model_transitions(sid)
        if fast is not None:
            return jsonify(fast)
    sessions_dir = _d.SESSIONS_DIR or os.path.expanduser(
        "~/.openclaw/agents/main/sessions"
    )
    path = os.path.join(sessions_dir, sid + ".jsonl")
    if not os.path.isfile(path):
        return jsonify({"error": "session not found"}), 404
    transitions = _detect_model_transitions(path)
    return jsonify(
        {
            "sessionId": sid,
            "transitions": transitions,
            "count": len(transitions),
            "has_transitions": bool(transitions),
        }
    )


def _diff_params(p1, p2):
    """Return list of decoding-param keys that differ between p1 and p2.

    Compares temperature, top_p, top_k, and max_tokens. A missing key is
    treated as None — a key present in one dict but not the other counts as
    a change.  Floats are compared exactly (provider-switch drift is typically
    a deliberate user change, not floating-point noise).
    """
    changed = []
    for k in ("temperature", "top_p", "top_k", "max_tokens"):
        v1 = (p1 or {}).get(k)
        v2 = (p2 or {}).get(k)
        if v1 != v2 and not (v1 is None and v2 is None):
            changed.append(k)
    return changed


def _detect_config_drift_jsonl(path):
    """Scan a session JSONL for provider switches that also changed decoding params.

    A "config drift" event fires when both of these are true at the same turn:
      1. The provider field changed from the previous assistant turn.
      2. At least one of temperature / top_p / top_k / max_tokens differs.

    Returns a dict ``{has_drift, drift_count, drifts}`` where each drift entry
    is ``{turn, ts, from_provider, to_provider, from_params, to_params,
    changed_keys}``.  Always returns a result dict (never raises).
    """
    drifts = []
    prev_provider = None
    prev_params: dict = {}
    turn = 0
    try:
        with open(path, "r", errors="replace") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                msg = obj
                if obj.get("type") in ("message", "user", "assistant") and isinstance(
                    obj.get("message"), dict
                ):
                    msg = obj["message"]
                if msg.get("role") != "assistant":
                    continue
                turn += 1
                provider = (msg.get("provider") or "").strip()
                params = _extract_decoding_params(obj)
                ts = (
                    obj.get("timestamp")
                    or obj.get("time")
                    or msg.get("timestamp")
                    or ""
                )
                if (
                    prev_provider is not None
                    and provider
                    and prev_provider
                    and provider != prev_provider
                ):
                    changed = _diff_params(prev_params, params)
                    if changed:
                        drifts.append(
                            {
                                "turn": turn,
                                "ts": ts,
                                "from_provider": prev_provider,
                                "to_provider": provider,
                                "from_params": prev_params,
                                "to_params": params,
                                "changed_keys": changed,
                            }
                        )
                if provider:
                    prev_provider = provider
                    prev_params = params
                elif prev_provider is None:
                    prev_provider = ""
                    prev_params = params
    except Exception:
        pass
    return {
        "has_drift": bool(drifts),
        "drift_count": len(drifts),
        "drifts": drifts,
    }


@bp_sessions.route("/api/sessions/<sid>/config-drift")
def api_session_config_drift(sid):
    """Return provider-switch config-drift events for a session (issue #570).

    A drift fires when the provider changes between assistant turns AND at
    least one decoding param (temperature, top_p, top_k, max_tokens) also
    changes.  Different providers interpret the same temperature value
    differently, so a silent param change at a provider switch can alter
    model behaviour in ways that are hard to spot turn-by-turn.

    Response: ``{sessionId, has_drift, drift_count, drifts: [{turn, ts,
    from_provider, to_provider, from_params, to_params, changed_keys}]}``.
    """
    import dashboard as _d
    if not sid or any(c in sid for c in ("/", "\\", "..")):
        return jsonify({"error": "invalid session id"}), 400
    sessions_dir = _d.SESSIONS_DIR or os.path.expanduser(
        "~/.openclaw/agents/main/sessions"
    )
    path = os.path.join(sessions_dir, sid + ".jsonl")
    path = os.path.normpath(path)
    if not path.startswith(os.path.normpath(sessions_dir)):
        return jsonify({"error": "access denied"}), 403
    if not os.path.isfile(path):
        return jsonify({"sessionId": sid, "has_drift": False, "drift_count": 0, "drifts": []})
    result = _detect_config_drift_jsonl(path)
    result["sessionId"] = sid
    return jsonify(result)


def _try_local_store_fallbacks(limit: int, top: int):
    """Tier-1 DuckDB fast path for /api/fallbacks.

    Routes the model/provider transition aggregator through the daemon
    LocalStore proxy (``query_model_fallbacks``). Returns the response
    payload on success, ``None`` to defer to the legacy JSONL walker
    when the store is empty or unreachable.

    "Empty workspace" is intentionally a defer (None), not an empty
    payload — on first install the DuckDB has zero events but the
    legacy walker can still find rows via the on-disk JSONL files,
    which is the more useful default while the daemon backfills.
    """
    payload = _ls_call("query_model_fallbacks", session_limit=limit, top=top)
    if not isinstance(payload, dict):
        return None
    if not payload.get("scanned"):
        return None
    payload["_source"] = "local_store"
    return payload


@bp_sessions.route("/api/fallbacks")
def api_fallbacks():
    """Aggregate model/provider fallback summary across recent sessions.

    Query params:
      limit  — max sessions to scan (default 100, max 500)
      top    — how many transition pairs to return (default 10)

    Returns: {scanned, sessions_affected, top_transitions:[{from_model,
    to_model, from_provider, to_provider, count, sessions:[sid,…]}]}
    """
    import dashboard as _d
    try:
        limit = max(1, min(500, int(request.args.get("limit", 100))))
    except (TypeError, ValueError):
        limit = 100
    try:
        top = max(1, min(50, int(request.args.get("top", 10))))
    except (TypeError, ValueError):
        top = 10

    # Tier-1 DuckDB fast path — opt-in via CLAWMETRY_LOCAL_STORE_READ=1.
    # Falls through to the legacy JSONL walker when the store is empty
    # / unreachable, so first-install dashboards never go blank.
    if is_local_store_read_enabled():
        fast = _try_local_store_fallbacks(limit, top)
        if fast is not None:
            return jsonify(fast)

    sessions_dir = _d.SESSIONS_DIR or os.path.expanduser(
        "~/.openclaw/agents/main/sessions"
    )
    import glob as _glob

    files = sorted(
        (
            f
            for f in _glob.glob(os.path.join(sessions_dir, "*.jsonl"))
            if ".deleted." not in f and ".trajectory." not in f
        ),
        key=os.path.getmtime,
        reverse=True,
    )[:limit]

    pair_counts: dict = {}  # (from_model, from_provider, to_model, to_provider) → {count, sessions}
    sessions_affected = set()

    for fpath in files:
        sid = os.path.basename(fpath).replace(".jsonl", "")
        transitions = _detect_model_transitions(fpath)
        if not transitions:
            continue
        sessions_affected.add(sid)
        for t in transitions:
            key = (t["from_model"], t["from_provider"], t["to_model"], t["to_provider"])
            if key not in pair_counts:
                pair_counts[key] = {"count": 0, "sessions": []}
            pair_counts[key]["count"] += 1
            if sid not in pair_counts[key]["sessions"]:
                pair_counts[key]["sessions"].append(sid)

    ranked = sorted(pair_counts.items(), key=lambda x: x[1]["count"], reverse=True)[:top]
    top_transitions = [
        {
            "from_model": k[0],
            "from_provider": k[1],
            "to_model": k[2],
            "to_provider": k[3],
            "count": v["count"],
            "sessions": v["sessions"][:10],
        }
        for k, v in ranked
    ]

    return jsonify(
        {
            "scanned": len(files),
            "sessions_affected": len(sessions_affected),
            "top_transitions": top_transitions,
        }
    )


# ── /api/spans — surface OTel spans we already store (issue #1364) ─────────
#
# MOAT capability 1.b ("structured event capture per agent step") was
# already half-built: routes/meta.py /v1/traces ingests OTLP into the
# DuckDB ``spans`` table via dashboard._process_otlp_traces →
# clawmetry.local_store.put_span. The READ side never shipped, so the
# data sat dark. This endpoint is the smallest possible surface that
# makes those rows visible to a human — no fancy tree, just a list — so
# the next iteration can build a span-detail drawer on top of it.
#
# Daemon-proxy first, direct read fallback, empty list on total failure
# (Steve-Jobs-style: dashboard never goes blank, never 500s on missing
# OTLP data). A span-less workspace is a perfectly valid empty result.

@bp_sessions.route("/api/spans")
def api_spans():
    """Return recent OTel spans from the local DuckDB ``spans`` table.

    Query params:
      * ``limit`` — max rows (default 50, clamped 1-500)
      * ``session_id`` — optional session filter
      * ``since`` — optional unix-second floor on ``start_ts``. Issue #1374:
        OSS / Cloud-Free callers are clamped to ``now - 24h``; Cloud-Pro
        users (validated by ``dashboard._is_pro_user``) get unlimited
        history. Response carries ``capped_at_24h`` so the UI can render
        the upgrade CTA.

    Response shape::

        {
          "spans":   [ {span_id, parent_span_id, trace_id, name, kind,
                        session_id, service_name, start_time, end_time,
                        duration_ms, status, model, tool_name, cost_usd,
                        tokens_input, tokens_output}, ... ],
          "count":   <int>,
          "_source": "local_store",
          "capped_at_24h": <bool>
        }

    Graceful fallback: when the local store / daemon is unreachable we
    return ``{"spans": [], "count": 0, "_source": "unavailable",
    "capped_at_24h": <bool>}`` with HTTP 200 so the UI table renders an
    empty state instead of an error banner.
    """
    try:
        limit = int(request.args.get("limit", 50))
    except (TypeError, ValueError):
        limit = 50
    limit = max(1, min(500, limit))
    session_id = (request.args.get("session_id") or "").strip() or None

    # Optional unix-second floor (caller-supplied).
    since_raw = (request.args.get("since") or "").strip()
    since: float | None
    try:
        since = float(since_raw) if since_raw else None
    except (TypeError, ValueError):
        since = None

    # OSS retention cap (issue #1374). Cloud-Pro bypasses; everyone else
    # gets clamped to the last 24 h of ``start_ts``. Mirrors the pattern
    # used by /api/flow/runs (issue #1173).
    capped_at_24h = False
    try:
        import dashboard as _d
        is_pro = bool(_d._is_pro_user())
    except Exception:
        is_pro = False
    if not is_pro:
        cap_floor = time.time() - 24 * 3600
        if since is None or since < cap_floor:
            since = cap_floor
            capped_at_24h = True

    rows = _ls_call(
        "query_recent_spans",
        limit=limit,
        session_id=session_id,
        since=since,
    )
    if rows is None:
        return jsonify({
            "spans": [],
            "count": 0,
            "_source": "unavailable",
            "capped_at_24h": capped_at_24h,
        })
    return jsonify({
        "spans":   rows,
        "count":   len(rows),
        "_source": "local_store",
        "capped_at_24h": capped_at_24h,
    })


# ── Issue #1614 — outcome labeling ──────────────────────────────────────────
#
# Every session gets one of: success / failed / escalated / ongoing. Auto-
# detected by ``clawmetry.outcome_classifier`` from event-stream + approvals
# table + session metadata. Persisted on the sessions table so the tile
# query is a one-row roll-up, not a per-session event scan.
#
# Two endpoints:
#   GET /api/outcomes?window=1d        — totals + success-rate (Overview tile)
#   GET /api/outcomes/timeline?days=7  — per-day series for sparklines
#
# Both pre-compute via DuckDB (memory ``feedback_duckdb_first_rule``). When
# the daemon proxy is unreachable we degrade to ``{available: false}`` rather
# than 500ing — overview-tab MUST stay responsive (issue #1127 lesson).

_OUTCOME_WINDOW_TO_SECS = {
    "1h": 3600,
    "1d": 86400,
    "24h": 86400,
    "7d": 7 * 86400,
    "30d": 30 * 86400,
}


def _outcome_window_to_iso_since(window):
    """Convert a window shorthand to an ISO ``since`` timestamp.

    Returns None if the window string is invalid — caller treats that as
    "no time filter" so the tile still renders something useful.
    """
    secs = _OUTCOME_WINDOW_TO_SECS.get((window or "").lower())
    if not secs:
        return None
    from datetime import datetime, timedelta, timezone
    since_dt = datetime.now(timezone.utc) - timedelta(seconds=secs)
    return since_dt.isoformat().replace("+00:00", "Z")


@bp_sessions.route("/api/outcomes")
def api_outcomes():
    """Outcome roll-up for the Overview tile.

    Query params:
      ``window`` — one of ``1h``, ``1d`` (default), ``7d``, ``30d``.
      ``agent_type`` — default ``openclaw``.

    Returns the shape ``clawmetry.outcome_classifier.aggregate_outcomes``
    produces plus a ``window`` echo + ``_source`` tag. On total-failure
    paths (DuckDB unreachable + no fallback) we still 200 with zeros so
    the tile renders "No completed tasks yet" instead of a JS error.
    """
    from clawmetry.outcome_classifier import aggregate_outcomes
    window = (request.args.get("window") or "1d").lower()
    agent_type = request.args.get("agent_type") or "openclaw"
    since = _outcome_window_to_iso_since(window)

    rows = _ls_call(
        "query_outcomes",
        agent_type=agent_type,
        since=since,
        limit=int(request.args.get("limit") or 1000),
    )
    if rows is None:
        # Daemon proxy unreachable AND no in-process fallback succeeded.
        # Return a zeroed shell so the UI degrades gracefully.
        return jsonify({
            "window": window,
            "total": 0,
            "success": 0,
            "failed": 0,
            "escalated": 0,
            "ongoing": 0,
            "success_rate": 0.0,
            "needed_human_rate": 0.0,
            "_source": "unavailable",
        })
    agg = aggregate_outcomes(rows)
    agg["window"] = window
    agg["_source"] = "local_store"
    return jsonify(agg)


@bp_sessions.route("/api/outcomes/timeline")
def api_outcomes_timeline():
    """Per-day outcome series for the drill-down sparkline.

    Buckets every session into a YYYY-MM-DD key by ``last_active_at`` (the
    same field the Overview Tasks panel uses), then runs the aggregator
    per day. Returns up to ``days`` days, newest-first.
    """
    from clawmetry.outcome_classifier import aggregate_outcomes
    try:
        days = max(1, min(90, int(request.args.get("days") or 7)))
    except (TypeError, ValueError):
        days = 7
    agent_type = request.args.get("agent_type") or "openclaw"
    from datetime import datetime, timedelta, timezone
    since_dt = datetime.now(timezone.utc) - timedelta(days=days)
    since_iso = since_dt.isoformat().replace("+00:00", "Z")

    rows = _ls_call(
        "query_outcomes",
        agent_type=agent_type,
        since=since_iso,
        limit=5000,
    ) or []

    by_day: dict[str, list[dict]] = {}
    for r in rows:
        ts = r.get("last_active_at") or r.get("ended_at") or ""
        day = ts[:10] if len(ts) >= 10 else ""
        if not day:
            continue
        by_day.setdefault(day, []).append(r)
    series = []
    for day in sorted(by_day.keys(), reverse=True):
        agg = aggregate_outcomes(by_day[day])
        agg["day"] = day
        series.append(agg)
    return jsonify({
        "days": days,
        "series": series,
        "_source": "local_store" if rows else "empty",
    })


@bp_sessions.route("/api/outcomes/sessions")
def api_outcomes_sessions():
    """Drill-down list: which sessions failed / escalated. Powers the
    expanded view when the Overview tile is clicked.

    Query params:
      ``outcome`` — filter to one outcome (``failed`` / ``escalated`` /
        ``ongoing`` / ``success``). Default ``failed``.
      ``window`` — same shorthand as /api/outcomes (default ``1d``).
      ``limit``  — cap (default 50).
    """
    outcome = (request.args.get("outcome") or "failed").lower()
    window = (request.args.get("window") or "1d").lower()
    agent_type = request.args.get("agent_type") or "openclaw"
    try:
        limit = max(1, min(500, int(request.args.get("limit") or 50)))
    except (TypeError, ValueError):
        limit = 50
    since = _outcome_window_to_iso_since(window)
    rows = _ls_call(
        "query_outcomes",
        agent_type=agent_type,
        since=since,
        limit=2000,
    ) or []
    filtered = [r for r in rows if (r.get("outcome") or "") == outcome][:limit]
    # Slim the payload — the drill-down UI needs id/title/cost/timestamp only.
    out = [
        {
            "session_id":      r.get("session_id"),
            "title":           r.get("title"),
            "last_active_at":  r.get("last_active_at"),
            "ended_at":        r.get("ended_at"),
            "cost_usd":        r.get("cost_usd") or 0,
            "total_tokens":    r.get("total_tokens") or 0,
            "outcome":         r.get("outcome"),
            "confidence":      r.get("outcome_confidence"),
        }
        for r in filtered
    ]
    return jsonify({
        "outcome": outcome,
        "window":  window,
        "count":   len(out),
        "sessions": out,
        "_source": "local_store",
    })


@bp_sessions.route("/api/outcomes/impact")
def api_outcomes_impact():
    """Impact-taxonomy breakdown for sessions in the requested window (issue #1649).

    Classifies non-success sessions into OpenClaw's failure-mode labels:
    message-loss, session-state, crash-loop, auth-provider, security.
    A session may carry multiple tags.

    Query params:
      window     — 1h / 1d (default) / 7d / 30d
      agent_type — default openclaw
      limit      — max sessions to classify (default 50, cap 50)
    """
    from clawmetry.outcome_classifier import (
        classify_session_impact,
        aggregate_impacts,
        OUTCOME_SUCCESS,
        OUTCOME_ONGOING,
    )
    window = (request.args.get("window") or "1d").lower()
    agent_type = request.args.get("agent_type") or "openclaw"
    try:
        limit = max(1, min(50, int(request.args.get("limit") or 50)))
    except (TypeError, ValueError):
        limit = 50
    since = _outcome_window_to_iso_since(window)

    outcome_rows = _ls_call(
        "query_outcomes",
        agent_type=agent_type,
        since=since,
        limit=500,
    ) or []

    # Only classify sessions that didn't simply succeed / are still ongoing —
    # keeps the per-session event queries bounded to the interesting minority.
    candidates = [
        r for r in outcome_rows
        if (r.get("outcome") or "") not in (OUTCOME_SUCCESS, OUTCOME_ONGOING, "")
    ][:limit]

    pairs: list[tuple[str, list[str]]] = []
    for row in candidates:
        sid = row.get("session_id")
        if not sid:
            continue
        evs = _ls_call("query_events", session_id=sid, limit=200) or []
        meta = {k: row.get(k) for k in ("status", "ended_at", "last_active_at")}
        tags = classify_session_impact(evs, meta)
        pairs.append((sid, tags))

    agg = aggregate_impacts(pairs)
    agg["window"] = window
    agg["total_sessions_in_window"] = len(outcome_rows)
    agg["_source"] = "local_store" if outcome_rows else "empty"
    return jsonify(agg)


# ── Authority footprint (#880) ────────────────────────────────────────────────

# Matches absolute filesystem paths inside tool arg JSON/strings.
# Stops at whitespace and common JSON delimiters to avoid over-matching.
_AUTH_FILE_RE = re.compile(r'(?:^|[\s"\'`=,({])((?:/[^\s"\'`<>:;,)}\[\]]{2,})+)')

# Matches the host (and optional port) portion of http/https URLs.
_AUTH_URL_RE = re.compile(r'https?://([a-zA-Z0-9._%-]+(?::\d+)?)')

# Event types that carry a top-level tool invocation (all known variants).
_AUTH_TOOL_TYPES = frozenset({
    "tool_call", "tool.call", "tool_use", "toolCall",
})


def _extract_authority(events: list) -> dict:
    """Derive an authority footprint from a list of DuckDB events.

    Returns dict with keys:
      tools      — [{name, calls}] sorted by call count desc
      filesystem — [{path, via_tools}] up to 100 unique paths
      network    — [{host, via_tools}] up to 50 unique hosts
    """
    tool_counts: dict = {}
    file_paths: dict = {}   # path  -> set of tool names
    net_hosts: dict = {}    # host  -> set of tool names

    for ev in (events or []):
        if ev.get("event_type", "") not in _AUTH_TOOL_TYPES:
            continue
        data = ev.get("data") or {}
        if not isinstance(data, dict):
            continue

        name = (
            data.get("tool") or data.get("tool_name") or data.get("name") or ""
        ).lower().strip()
        if not name:
            continue

        tool_counts[name] = tool_counts.get(name, 0) + 1

        args_raw = (
            data.get("args") if data.get("args") is not None
            else data.get("arguments") if data.get("arguments") is not None
            else data.get("input")
        )
        if args_raw is None:
            continue
        if isinstance(args_raw, str):
            args_str = args_raw
        else:
            try:
                args_str = json.dumps(args_raw)
            except Exception:
                args_str = str(args_raw)

        for m in _AUTH_FILE_RE.findall(args_str):
            path = m.strip()
            # Skip noise: very short paths, kernel pseudo-filesystems
            if len(path) > 3 and not path.startswith(("/proc", "/sys", "/dev")):
                file_paths.setdefault(path, set()).add(name)

        for host in _AUTH_URL_RE.findall(args_str):
            if host:
                net_hosts.setdefault(host, set()).add(name)

    return {
        "tools": [
            {"name": n, "calls": c}
            for n, c in sorted(tool_counts.items(), key=lambda x: -x[1])
        ],
        "filesystem": [
            {"path": p, "via_tools": sorted(t)}
            for p, t in sorted(file_paths.items())
        ][:100],
        "network": [
            {"host": h, "via_tools": sorted(t)}
            for h, t in sorted(net_hosts.items())
        ][:50],
    }


@bp_sessions.route("/api/authority")
def api_authority():
    """Authority footprint for one session: tools called, files touched,
    network hosts contacted. Implements issue #880.

    Query params:
      session_id  — required
      limit       — max events to scan (default 2000, cap 10000)
    """
    session_id = (
        request.args.get("session_id") or request.args.get("session") or ""
    )
    if not session_id:
        return jsonify({"error": "session_id required"}), 400
    try:
        limit = max(1, min(10000, int(request.args.get("limit") or 2000)))
    except (TypeError, ValueError):
        limit = 2000

    events = _ls_call("query_events", session_id=session_id, limit=limit) or []
    footprint = _extract_authority(events)
    footprint["session_id"] = session_id
    footprint["scanned_events"] = len(events)
    return jsonify(footprint)
# ─────────────────────────────────────────────────────────────────────────────
# Intent vs. execution divergence detection  (issue #879)
# ─────────────────────────────────────────────────────────────────────────────

# Three rule sets: (1) claims search/read but calls write/execute,
# (2) claims read-only but calls write/execute/delete,
# (3) claims local-only but calls a network/external tool.
_INTENT_DIVERGENCE_RULES = [
    {
        "id": "INT-001",
        "description": "Claims to search/read but writes or executes",
        "severity": "medium",
        "compiled": [
            _re.compile(r, _re.IGNORECASE) for r in [
                r"\bi(?:'?ll| will| am going to)\s+(?:search|look up|browse|fetch|retrieve)\b",
                r"\blet me\s+(?:search|look|check|browse|find)\b",
                r"\bi(?:'?ll| will)\s+(?:just\s+)?(?:read|look at|check)\b",
            ]
        ],
        "mismatched_substrings": ("write", "edit", "create", "bash", "execute", "run"),
    },
    {
        "id": "INT-002",
        "description": "Claims read-only intent but calls write or execute tool",
        "severity": "high",
        "compiled": [
            _re.compile(r, _re.IGNORECASE) for r in [
                r"\bonly\s+(?:read|check|look|inspect|view)\b",
                r"\bwon'?t\s+(?:change|modify|write|execute|run)\b",
                r"\bnot\s+(?:going to\s+)?(?:change|modify|write|run|execute)\b",
                r"\bwithout\s+(?:modifying|changing|writing|executing)\b",
            ]
        ],
        "mismatched_substrings": ("write", "edit", "create", "bash", "execute", "run", "delete"),
    },
    {
        "id": "INT-003",
        "description": "Claims local-only operation but calls network or external tool",
        "severity": "medium",
        "compiled": [
            _re.compile(r, _re.IGNORECASE) for r in [
                r"\b(?:only\s+(?:\w+\s+)?local(?:ly)?|local(?:ly)?\s+only|work(?:ing)?\s+local(?:ly)?)\b",
                r"\bno\s+(?:external|network|internet|remote|online)\b",
                r"\bwithout\s+(?:connect(?:ing)?|network|internet|uploading|downloading)\b",
            ]
        ],
        "mismatched_substrings": ("web_search", "web_fetch", "http", "curl", "wget", "fetch", "download", "upload", "request"),
    },
]


def _extract_tool_names_from_obj(obj: dict) -> list:
    """Return all tool names referenced in a single JSONL event object.

    Handles legacy ``tool_calls``/``tool_use`` arrays, v3 ``tool.call`` events,
    and Anthropic-style ``tool_use`` content blocks.
    """
    names = []
    for field in ("tool_calls", "tool_use"):
        for tc in (obj.get(field) or []):
            if isinstance(tc, dict):
                n = tc.get("name") or (tc.get("function") or {}).get("name") or ""
                if n:
                    names.append(n.lower())
    data = obj.get("data") if isinstance(obj.get("data"), dict) else {}
    if obj.get("event_type") in ("tool.call", "tool_use"):
        n = data.get("tool") or data.get("toolName") or data.get("name") or ""
        if n:
            names.append(n.lower())
    for container in (obj, obj.get("message") if isinstance(obj.get("message"), dict) else {}):
        if not isinstance(container, dict):
            continue
        for blk in (container.get("content") or []):
            if isinstance(blk, dict) and blk.get("type") == "tool_use":
                n = blk.get("name") or ""
                if n:
                    names.append(n.lower())
    return names


def _extract_assistant_text(obj: dict) -> str:
    """Return the assistant's text content from a JSONL line object, or ''."""
    et = obj.get("event_type") or obj.get("type") or ""
    role = obj.get("role") or ""
    msg = obj
    if et in ("message", "user", "assistant") and isinstance(obj.get("message"), dict):
        msg = obj["message"]
    if msg.get("role") == "assistant" or role == "assistant" or et == "model.completed":
        content = msg.get("content") or obj.get("content") or ""
        if isinstance(content, str):
            return content.strip()
        if isinstance(content, list):
            return " ".join(
                blk.get("text", "") if isinstance(blk, dict) and blk.get("type") == "text" else ""
                for blk in content
            ).strip()
    return ""


def _detect_intent_divergence(path: str) -> dict:
    """Scan a session JSONL for intent vs. execution divergence (issue #879).

    Single-pass state machine: tracks the last assistant text; on each tool call
    checks whether the preceding stated intent contradicts the tool name.
    Resets on user / prompt.submitted turns.

    Returns ``{has_divergence, divergence_count, flags}`` where each flag is
    ``{turn, ts, check_id, description, severity, intent_evidence, actual_tool}``.
    Always returns a result dict — never raises.
    """
    flags: list = []
    last_text = ""
    last_ts = ""
    last_turn = 0
    turn = 0
    try:
        with open(path, "r", errors="replace") as fh:
            for raw in fh:
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    obj = json.loads(raw)
                except Exception:
                    continue
                et = obj.get("event_type") or obj.get("type") or ""
                role = obj.get("role") or ""
                ts = obj.get("ts") or obj.get("timestamp") or obj.get("time") or ""
                if role == "user" or et in ("prompt.submitted", "user"):
                    last_text = ""
                    continue
                text = _extract_assistant_text(obj)
                if text:
                    turn += 1
                    last_text = text
                    last_ts = ts
                    last_turn = turn
                if not last_text:
                    continue
                for tool_name in _extract_tool_names_from_obj(obj):
                    for rule in _INTENT_DIVERGENCE_RULES:
                        if not any(p.search(last_text) for p in rule["compiled"]):
                            continue
                        if not any(sub in tool_name for sub in rule["mismatched_substrings"]):
                            continue
                        flags.append({
                            "turn": last_turn,
                            "ts": last_ts or ts,
                            "check_id": rule["id"],
                            "description": rule["description"],
                            "severity": rule["severity"],
                            "intent_evidence": last_text[:300],
                            "actual_tool": tool_name,
                        })
    except Exception:
        pass
    return {
        "has_divergence": bool(flags),
        "divergence_count": len(flags),
        "flags": flags,
    }


@bp_sessions.route("/api/sessions/<session_id>/intent-divergence")
def api_session_intent_divergence(session_id):
    """Check for intent vs. execution divergence in a session (issue #879).

    Compares what the assistant says it will do (stated intent in text turns)
    against the tool calls that follow. Uses three heuristic rules:
    INT-001 (search/read claim + write/execute action),
    INT-002 (read-only claim + write/execute action),
    INT-003 (local-only claim + network/external action).

    Response: ``{sessionId, has_divergence, divergence_count, flags: [{turn,
    ts, check_id, description, severity, intent_evidence, actual_tool}]}``.
    """
    import dashboard as _d
    if not session_id or any(c in session_id for c in ("/", "\\", "..")):
        return jsonify({"error": "invalid session id"}), 400
    sessions_dir = _d.SESSIONS_DIR or os.path.expanduser(
        "~/.openclaw/agents/main/sessions"
    )
    path = os.path.join(sessions_dir, session_id + ".jsonl")
    path = os.path.normpath(path)
    if not path.startswith(os.path.normpath(sessions_dir)):
        return jsonify({"error": "access denied"}), 403
    if not os.path.isfile(path):
        return jsonify({
            "sessionId": session_id,
            "has_divergence": False,
            "divergence_count": 0,
            "flags": [],
        })
    result = _detect_intent_divergence(path)
    result["sessionId"] = session_id
    return jsonify(result)
