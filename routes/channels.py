"""
routes/channels.py — Per-channel adapter endpoints.

Extracted from dashboard.py as Phase 5.7 of the incremental modularisation.
Owns the 21 routes registered on ``bp_channels`` (Telegram, iMessage, WhatsApp,
Signal, Discord, Slack, IRC, WebChat, Google Chat, BlueBubbles, MS Teams,
Matrix, Mattermost, LINE, Nostr, Twitch, Feishu, Zalo, Tlon, Synology Chat,
Nextcloud Talk).

Module-level helpers (``_get_log_dirs``, ``_grep_log_file``,
``_generic_channel_data``) stay in dashboard.py and are reached via late
``import dashboard as _d``. Pure mechanical move — zero behaviour change.
"""

import glob
import json
import logging
import os
import sys
from datetime import datetime

from flask import Blueprint, jsonify, request

from clawmetry.config import is_local_store_read_enabled

bp_channels = Blueprint('channels', __name__)

_log = logging.getLogger("clawmetry.routes.channels")


# ── Epic #1032 Phase 5: channel-config fast-path (DuckDB) ──────────────────
# When the local-store fast path is enabled (default since 0.12.174) the
# per-channel status endpoint serves the non-secret status summary straight
# from the local DuckDB instead of hitting the gateway / parsing YAML on
# every request. The ciphertext blob stays on this node; cloud never sees
# plaintext.

def _local_store_read_enabled() -> bool:
    """Backward-compat shim — delegates to ``clawmetry.config``.

    Kept so existing call sites (``_channel_config_status_*`` below) don't
    need to touch the import line. The single source of truth for the
    feature gate now lives in ``clawmetry/config.py``.
    """
    return is_local_store_read_enabled()


def _ls_call(method_name, **kwargs):
    """Cross-process LocalStore call with single-process fallback.

    Mirrors ``routes.sessions._ls_call`` — every fast-path that wants to
    read from the DuckDB store goes through the daemon's HTTP proxy first
    so we work under the standard install (daemon owns the writer lock,
    dashboard's direct open raises ``IOException: Could not set lock``).
    Falls back to a direct read for single-process boots (dev mode + tests,
    where the daemon and dashboard share a process). Returns ``None`` on
    any failure so callers defer to the legacy path.
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


def _channel_config_status_from_local_store(provider: str):
    """Read the non-secret status summary for ``provider`` from DuckDB.

    Returns the row dict tagged with ``_source: "local_store"`` on hit, or
    ``None`` on store unavailable. NEVER returns the encrypted blob — HTTP
    responses must never carry ciphertext to keep the cloud surface
    plaintext-free at every layer of defense."""
    # Issue #1256 + #1265: route through daemon proxy (DuckDB process-level
    # lock blocks direct opens from the dashboard process when sync daemon
    # owns the writer).
    rows = None
    try:
        from routes.local_query import local_store_via_daemon
        rows = local_store_via_daemon("query_channel_config_status", provider=provider)
    except Exception as e:
        _log.debug("channel_config daemon proxy failed (provider=%s): %s", provider, e)
    if rows is None:
        # Single-process fallback (tests + dev mode).
        try:
            from clawmetry import local_store
            store = local_store.get_store(read_only=True)
            rows = store.query_channel_config_status(provider=provider)
        except Exception as e:
            _log.debug("channel_config direct open failed (provider=%s): %s", provider, e)
            return None
    if not rows:
        # Provider hasn't been configured yet — still serve from the local
        # store with explicit "unconfigured" status so the cloud UI renders
        # "Not configured" instead of falling back to gateway parsing.
        return {
            "provider": provider,
            "enabled": False,
            "configured": False,
            "last_test_at": None,
            "last_test_ok": None,
            "last_test_error": None,
            "updated_at": None,
            "_source": "local_store",
        }
    row = dict(rows[0])
    row["configured"] = True
    row["_source"] = "local_store"
    return row


@bp_channels.route("/api/channels/<provider>/status")
def api_channel_status(provider: str):
    """Per-channel adapter status — fast-path on DuckDB when the local-store
    read flag is on (epic #1032 Phase 5).

    Returns:
        {provider, enabled, configured, last_test_at, last_test_ok,
         last_test_error, updated_at, _source: "local_store"}

    Never includes the encrypted config blob. The cloud read path serves
    the same shape from Redis after a heartbeat cache_push."""
    provider = (provider or "").lower().strip()
    if not provider:
        return jsonify({"error": "provider required"}), 400
    if _local_store_read_enabled():
        row = _channel_config_status_from_local_store(provider)
        if row is not None:
            return jsonify(row)
    # Fallback when the flag is off OR the local-store import is unavailable
    # (defensive — should never happen in practice). Returns an "unknown"
    # status so the UI can degrade gracefully.
    return jsonify({
        "provider": provider,
        "enabled": False,
        "configured": False,
        "last_test_at": None,
        "last_test_ok": None,
        "last_test_error": None,
        "updated_at": None,
        "_source": "fallback",
    })


@bp_channels.route("/api/channels/status")
def api_channels_status_all():
    """All-providers status summary — same shape as ``/api/channels/<p>/status``
    but returns a list. Used by the cloud UI's channels overview tab."""
    if not _local_store_read_enabled():
        return jsonify({"channels": [], "_source": "fallback"})
    try:
        from clawmetry import local_store
    except Exception:
        return jsonify({"channels": [], "_source": "fallback"})
    # Issue #1265 + #1256: route through daemon proxy (DuckDB process lock
    # blocks direct opens) and treat an empty result as a successful hit
    # rather than a miss-that-falls-through.
    rows = None
    try:
        from routes.local_query import local_store_via_daemon
        rows = local_store_via_daemon("query_channel_config_status")
    except Exception as e:
        _log.debug("channels/status daemon proxy failed: %s", e)
    if rows is None:
        # Single-process fallback (tests + dev mode).
        try:
            store = local_store.get_store(read_only=True)
            rows = store.query_channel_config_status()
        except Exception as e:
            _log.debug("channels/status direct open failed: %s", e)
            return jsonify({"channels": [], "_source": "fallback"})
    out = []
    for r in (rows or []):
        d = dict(r); d["configured"] = True; out.append(d)
    return jsonify({"channels": out, "_source": "local_store"})


# ── Issue #1088 Phase 4: channel-message foundation (DuckDB fast-paths) ─────
#
# Three POC endpoints over the new ``channel_messages`` table. They are the
# canonical "list messages" / "list threads" / "cross-provider summary"
# shapes — every per-provider route in this file (Telegram, iMessage,
# Signal, …) will eventually delegate to one of these so the schema lives
# in one place. This PR ships only the three; the remaining 18 land in
# follow-up PRs once the schema proves out (see issue #1088).

def _try_local_store_channel_messages(provider, since, limit):
    """Fast path for ``/api/channels/<provider>/messages``. Returns ``None``
    on miss so the caller can fall through to the legacy log-grep path."""
    rows = _ls_call(
        "query_channel_messages",
        provider=provider,
        since=since or None,
        limit=limit,
    )
    if not rows:
        return None
    messages = []
    for r in rows:
        messages.append({
            "id":          r.get("id"),
            "timestamp":   r.get("ts"),
            "direction":   r.get("direction"),
            "sender":      r.get("sender_name") or r.get("sender_id") or "",
            "senderId":    r.get("sender_id") or "",
            "channelId":   r.get("channel_id") or "",
            "text":        r.get("body") or "",
            "sessionId":   r.get("session_key") or "",
        })
    return {
        "messages":  messages,
        "total":     len(messages),
        "provider":  provider,
        "_source":   "local_store",
    }


def _try_local_store_channel_threads(provider, limit):
    """Fast path for ``/api/channels/<provider>/threads``."""
    rows = _ls_call(
        "query_channel_threads",
        provider=provider,
        limit=limit,
    )
    if not rows:
        return None
    threads = []
    for r in rows:
        threads.append({
            "channelId":   r.get("channel_id") or "",
            "lastTs":      r.get("last_ts") or "",
            "lastSender":  r.get("last_sender") or "",
            "lastSnippet": r.get("last_body") or "",
            "lastDirection": r.get("last_direction") or "",
            "sessionId":   r.get("session_key") or "",
            "msgIn":       int(r.get("msg_in") or 0),
            "msgOut":      int(r.get("msg_out") or 0),
            "total":       int(r.get("total") or 0),
        })
    return {
        "threads":  threads,
        "total":    len(threads),
        "provider": provider,
        "_source":  "local_store",
    }


def _try_local_store_channel_summary():
    """Fast path for ``/api/channels/summary``."""
    rows = _ls_call("query_channel_summary")
    if rows is None:
        return None
    by_provider = []
    grand_in = 0
    grand_out = 0
    for r in rows:
        by_provider.append({
            "provider":         r.get("provider"),
            "msgIn":            int(r.get("msg_in") or 0),
            "msgOut":           int(r.get("msg_out") or 0),
            "total":            int(r.get("total") or 0),
            "distinctChannels": int(r.get("distinct_channels") or 0),
            "lastTs":           r.get("last_ts") or "",
        })
        grand_in  += int(r.get("msg_in")  or 0)
        grand_out += int(r.get("msg_out") or 0)
    return {
        "providers": by_provider,
        "totals":    {
            "msgIn":  grand_in,
            "msgOut": grand_out,
            "total":  grand_in + grand_out,
        },
        "_source":   "local_store",
    }


# ── Issue #1088 Phase 5: per-provider channel fast-paths (DuckDB) ──────────
#
# The 19 per-provider routes below (Telegram, Signal, WhatsApp, Discord,
# Slack, IRC, WebChat, Google Chat, MS Teams, Matrix, Mattermost, LINE,
# Nostr, Twitch, Feishu, Zalo, Tlon, Synology Chat, Nextcloud Talk) all
# share the same legacy "scrape gateway logs + session JSONLs" pattern.
# Now that ``channel_messages`` is the single source of truth, every one
# of them gets a tiny ``_try_local_store_provider_<name>`` early-return
# that pulls the per-provider rows from DuckDB and reshapes them into the
# legacy {messages, total, todayIn, todayOut, …extras} envelope so the
# embedded UI doesn't need to change.
#
# Three legacy routes are intentionally NOT migrated and still hit their
# original sources because the data isn't in ``channel_messages``:
#   * ``/api/channel/imessage`` — reads ``~/Library/Messages/chat.db`` (Apple
#     SQLite). The OpenClaw gateway never sees these messages so the table
#     would be permanently empty for iMessage. Migrating would break the
#     macOS-native experience.
#   * ``/api/channel/tui`` — reads ``openclaw-tui``-tagged user messages
#     directly from session JSONLs. These aren't channel adapter messages
#     (no "messageChannel=tui" log line, no ``~/.openclaw/tui/`` dir in
#     ``sync._CHANNEL_DIRS``) so the chokepoint never picks them up.
#     A future TUI-aware ingest path would lift this; until then the
#     route stays JSONL-bound on purpose. (Tier-1 audit #1565,
#     2026-05-17.)
#
# Migrated in PR #1585 (Telegram, Signal) and this PR (BlueBubbles):
# bluebubbles IS in ``sync._CHANNEL_DIRS`` — the daemon ingests its
# JSONLs into ``channel_messages`` + ``events`` exactly like Telegram,
# so the same two-tier fast path applies. The legacy REST-API + log-
# grep path now runs only as a last-resort backstop.

def _format_local_store_provider_messages(
    provider,
    rows,
    limit,
    extras=None,
):
    """Reshape ``query_channel_messages`` rows into the legacy envelope.

    Caller passes the raw row list (already provider-filtered, newest-first
    — ``query_channel_messages`` does the ORDER BY ts DESC) plus any
    provider-specific ``extras`` (e.g. ``{"workspaces": [...]}``). Returns
    the dict the route handler will JSON-ify, tagged with
    ``_source: "local_store"``.

    Today counters use the local-time ``YYYY-MM-DD`` prefix the same way
    the legacy paths do — DuckDB stores ts as ISO-8601 strings so a simple
    ``today in ts`` substring match is consistent across the board.
    """
    today = datetime.now().strftime("%Y-%m-%d")
    messages: list[dict] = []
    today_in = 0
    today_out = 0
    for r in rows:
        ts = r.get("ts") or ""
        direction = r.get("direction") or ""
        sender = r.get("sender_name") or r.get("sender_id") or (
            "User" if direction == "in" else "Clawd"
        )
        body = r.get("body") or ""
        # Cap each body at 300 chars — matches the legacy per-provider
        # pages which truncate the same way to keep the table compact.
        if isinstance(body, str) and len(body) > 300:
            body = body[:300]
        messages.append({
            "timestamp":  ts,
            "direction":  direction,
            "sender":     sender,
            "text":       body,
            "chatId":     r.get("channel_id") or "",
            "sessionId":  r.get("session_key") or "",
        })
        if today and today in str(ts):
            if direction == "in":
                today_in += 1
            elif direction == "out":
                today_out += 1
    out = {
        "messages":  messages[:limit],
        "total":     len(messages),
        "todayIn":   today_in,
        "todayOut":  today_out,
        "_source":   "local_store",
    }
    if extras:
        out.update(extras)
    return out


def _try_local_store_provider_messages(
    provider,
    limit,
    extras_extractor=None,
):
    """Generic per-provider fast-path. Returns ``None`` on miss so the
    caller falls through to the legacy log-grep path.

    ``extras_extractor`` is an optional callable invoked with the raw row
    list; it returns a dict that gets merged into the response envelope
    (used by Slack/Discord/IRC/etc. to surface workspace / guild / channel
    lists parsed out of message bodies — same regexes the legacy paths
    apply, just over the DuckDB body column instead of log lines)."""
    rows = _ls_call(
        "query_channel_messages",
        provider=provider,
        # Pull a generous window so today-counters + extras extraction stay
        # accurate even when the caller asked for a tiny page. 1000 is the
        # ``query_channel_messages`` upper bound.
        limit=1000,
    )
    if not rows:
        return None
    extras = extras_extractor(rows) if extras_extractor else None
    return _format_local_store_provider_messages(provider, rows, limit, extras)


# ── Tier-1 #1565: v3 events-table fallback for channel messages ────────────
#
# Background: ``_try_local_store_provider_messages`` above reads from the
# specialized ``channel_messages`` table (Phase 5). That table can be empty
# even when the daemon has already captured channel turns into the unified
# ``events`` table — there are real ingest paths where the chokepoint
# wrote the ``events`` projection but the ``channel_messages`` UPSERT was
# skipped (e.g. PRIMARY KEY conflicts on re-ingest after a daemon
# restart, or a legacy ``ingest`` caller that wrote only the events row).
#
# Without this fallback every Telegram / Signal poll would silently fall
# through to the legacy gateway.log grep + JSONL walker — exactly the
# silent-zero bug class memory `feedback_synthetic_tests_missed_real_event_shape.md`
# warns about: synthetic tests pass on the specialised table while real
# v3 data only lands in ``events``.
#
# The chokepoint contract (``LocalStore.ingest_channel_event`` — see PR
# #1220) stamps EACH channel turn with ``event_type='channel.in'`` or
# ``'channel.out'`` and embeds the provider tag under ``data.provider``,
# so we can serve telegram/signal/etc. from a single events query.

# Newest-first window we scan when the dedicated channel_messages table
# came back empty. Matches ``query_channel_messages``' default page-size
# upper bound so the today-counters stay accurate.
_CHANNEL_EVENTS_FAST_PATH_LIMIT = 1000


def _format_channel_event_row(ev):
    """Project one ``events`` row (event_type='channel.in'|'channel.out')
    into the legacy ``{timestamp, direction, sender, text, chatId,
    sessionId}`` envelope the per-channel routes return.

    Mirrors ``routes/brain.py`` channel-event enrichment so the field
    extraction follows a single shared shape. Returns ``None`` if the row
    is unusable (no data dict / no body anywhere)."""
    data = ev.get("data") if isinstance(ev.get("data"), dict) else {}
    if not isinstance(data, dict):
        return None
    direction = "out" if str(ev.get("event_type") or "").endswith(".out") else "in"
    # Body lookup order matches the chokepoint write rules
    # (``ingest_channel_event``): the JSONL/WS path leaves the full payload
    # under data and the gateway-log path stamps a small breadcrumb.
    body = (
        data.get("body")
        or data.get("text")
        or data.get("message")
        or ""
    )
    if isinstance(body, dict):
        body = body.get("text") or body.get("body") or ""
    body = str(body)[:300]
    # sender: prefer flat sender_name, fall back to the from/user blocks
    # the WS-tap path emits (mirrors routes/brain.py logic).
    sender = data.get("sender_name") or data.get("sender") or ""
    if not sender:
        for blk_key in ("from", "user"):
            blk = data.get(blk_key)
            if isinstance(blk, dict):
                sender = (
                    blk.get("username")
                    or blk.get("first_name")
                    or blk.get("name")
                    or ""
                )
                if sender:
                    break
    if not sender:
        sender = "User" if direction == "in" else "Clawd"
    chat_id = data.get("channel_id") or data.get("chat_id") or ""
    if not chat_id and isinstance(data.get("chat"), dict):
        chat_id = data["chat"].get("id") or ""
    return {
        "timestamp":  ev.get("ts") or "",
        "direction":  direction,
        "sender":     str(sender)[:80],
        "text":       body,
        "chatId":     str(chat_id)[:80] if chat_id else "",
        "sessionId":  ev.get("session_id") or "",
    }


def _try_local_store_channel_events(provider, limit):
    """Tier-1 #1565 v3 events-table fallback for per-provider channel
    routes. Used by ``api_channel_telegram`` + ``api_channel_signal``
    (and ready for the other 6 chat channels) AFTER the
    ``channel_messages`` fast path returns None.

    Why a second helper instead of just one query:
    ``_try_local_store_provider_messages`` reads the specialised
    ``channel_messages`` table, which is the canonical projection but
    can lag the ``events`` table when an ingest path took the ``ingest``
    side-door instead of the ``ingest_channel_event`` chokepoint (PR
    #1220 closed the known gaps but a row can still be in ``events`` and
    not in ``channel_messages`` on rare schema-drift / re-ingest paths).
    Without this fallback the route silently falls through to the
    gateway.log grep + JSONL walker — the same silent-zero hazard memory
    `feedback_synthetic_tests_missed_real_event_shape.md` warns about.

    Queries both ``channel.in`` and ``channel.out`` events, filters by
    ``data.provider`` in Python (DuckDB JSON predicate would need an
    extra ``LocalStore`` helper — keeping the daemon-proxy contract
    surface minimal), reshapes via ``_format_channel_event_row``, and
    returns the legacy envelope tagged ``_source: 'local_store_v3'`` so
    the audit canary can distinguish the events-table path from the
    specialised-table path.

    Returns ``None`` when ``events`` also has nothing for this provider
    so callers fall through to the legacy log-grep walker."""
    provider_key = (provider or "").lower().strip()
    if not provider_key:
        return None
    # ``query_events`` takes a single event_type filter; we make two calls
    # (cheap — both rows ORDER BY ts DESC + LIMIT N) and merge.
    rows_in = _ls_call(
        "query_events",
        event_type="channel.in",
        limit=_CHANNEL_EVENTS_FAST_PATH_LIMIT,
    ) or []
    rows_out = _ls_call(
        "query_events",
        event_type="channel.out",
        limit=_CHANNEL_EVENTS_FAST_PATH_LIMIT,
    ) or []
    matched = []
    for ev in list(rows_in) + list(rows_out):
        data = ev.get("data") if isinstance(ev.get("data"), dict) else {}
        if not isinstance(data, dict):
            continue
        # Provider tag is stamped by ``ingest_channel_event``'s data
        # projection (see clawmetry/local_store.py:1233-1248). Case-fold
        # to defend against legacy producers that wrote mixed case.
        ev_provider = str(data.get("provider") or "").lower().strip()
        if ev_provider != provider_key:
            continue
        row = _format_channel_event_row(ev)
        if row is not None:
            matched.append(row)
    if not matched:
        return None
    # Newest-first across the union of the two event_type pulls.
    matched.sort(key=lambda r: r.get("timestamp") or "", reverse=True)
    today = datetime.now().strftime("%Y-%m-%d")
    today_in = sum(
        1 for r in matched if r["direction"] == "in" and today in str(r["timestamp"])
    )
    today_out = sum(
        1 for r in matched if r["direction"] == "out" and today in str(r["timestamp"])
    )
    return {
        "messages":  matched[:limit],
        "total":     len(matched),
        "todayIn":   today_in,
        "todayOut":  today_out,
        "_source":   "local_store_v3",
    }


# ── Issue #1656: DuckDB fast path for /api/channel/tui ─────────────────────
#
# Unlike Telegram / Signal / BlueBubbles, the OpenClaw TUI does NOT have a
# dedicated channel adapter directory under ``~/.openclaw/`` — it writes
# directly into the active session JSONL with a ``Sender (untrusted
# metadata)`` JSON preamble tagged ``openclaw-tui``. That means there is
# no ``channel.in`` / ``channel.out`` event for TUI turns, so
# ``_try_local_store_channel_events`` cannot serve them.
#
# However the daemon's v3 mapper (``sync._parse_v3_event``) ALREADY
# normalises every session-JSONL ``message`` line into ``prompt.submitted``
# (user role) and ``model.completed`` (assistant role), preserving the
# raw ``finalPromptText`` verbatim — Sender block included. So the TUI
# marker survives the ingest and we can query DuckDB for the same rows
# the legacy JSONL walker reconstructs from disk, just without the
# O(sessions) directory scan.
#
# This is the MOAT-first read path for #1656: try DuckDB first, fall
# back to the legacy session-JSONL walker when the daemon hasn't
# ingested anything yet (fresh install / read flag OFF / daemon down).

_TUI_MARKER = "openclaw-tui"


def _strip_tui_sender_block(text: str) -> str:
    """Remove the ```json {...}``` Sender preamble from a TUI prompt body
    so the bubble shows the user's real message. Mirrors the legacy
    ``_strip_sender_block`` inside ``api_channel_tui``."""
    import re as _re
    if not isinstance(text, str):
        return text
    m = _re.search(r"```json\s*\{[^`]*?\}\s*```\s*", text, _re.DOTALL)
    return (text[m.end():] if m else text).strip()


def _try_local_store_channel_tui(limit):
    """Issue #1656 DuckDB fast path for the TUI channel.

    Reads ``prompt.submitted`` events whose ``data.finalPromptText`` carries
    the ``openclaw-tui`` marker (the same Sender-block preamble the JSONL
    walker matched on at routes/channels.py:2318) and pairs each one with
    the next ``model.completed`` event in the same ``session_id`` as the
    outbound reply.

    Same dual-tier contract memory ``feedback_synthetic_tests_missed_real_event_shape.md``
    warns about: read against the REAL OpenClaw v3 event shape
    (``prompt.submitted`` / ``model.completed``) — not a synthetic
    ``channel.*`` row that production never writes for TUI.

    Returns ``None`` when DuckDB has no TUI-tagged prompts so the route
    falls through to the legacy JSONL walker."""
    prompts = _ls_call(
        "query_events",
        event_type="prompt.submitted",
        limit=_CHANNEL_EVENTS_FAST_PATH_LIMIT,
    ) or []
    # Filter to TUI-tagged prompts in Python (DuckDB JSON predicate would
    # need an extra LocalStore helper — keep the daemon-proxy surface
    # minimal, same pattern as ``_try_local_store_channel_events``).
    tui_prompts = []
    sessions_with_tui = set()
    for ev in prompts:
        data = ev.get("data") if isinstance(ev.get("data"), dict) else {}
        if not isinstance(data, dict):
            continue
        # ``finalPromptText`` lives at either ``data.finalPromptText`` or
        # ``data.data.finalPromptText`` — ``_parse_v3_event`` dual-writes
        # so either lookup works, but check both for resilience against
        # future shape drift.
        text = data.get("finalPromptText") or ""
        if not text:
            inner = data.get("data") if isinstance(data.get("data"), dict) else {}
            text = inner.get("finalPromptText") or ""
        if not isinstance(text, str) or _TUI_MARKER not in text:
            continue
        tui_prompts.append((ev, text))
        sid = ev.get("session_id") or ""
        if sid:
            sessions_with_tui.add(sid)

    if not tui_prompts:
        return None

    # Pull completions for the sessions we have TUI prompts in so we can
    # pair each prompt with the next assistant reply by timestamp.
    completions_by_session: dict[str, list[dict]] = {}
    if sessions_with_tui:
        # ``query_events`` doesn't take a session-IN filter; pull a
        # generous global window and bucket in Python. Cheap because
        # _CHANNEL_EVENTS_FAST_PATH_LIMIT caps both pulls at 1000 each.
        completions = _ls_call(
            "query_events",
            event_type="model.completed",
            limit=_CHANNEL_EVENTS_FAST_PATH_LIMIT,
        ) or []
        for ev in completions:
            sid = ev.get("session_id") or ""
            if sid in sessions_with_tui:
                completions_by_session.setdefault(sid, []).append(ev)
        # Sort each session's completions OLDEST-FIRST so the pairing loop
        # can pop the first one strictly after each TUI prompt's ts.
        for sid in completions_by_session:
            completions_by_session[sid].sort(key=lambda e: e.get("ts") or "")

    messages = []
    today = datetime.now().strftime("%Y-%m-%d")
    today_in = 0
    today_out = 0
    used_completion_ids: set[str] = set()

    for ev, text in tui_prompts:
        ts = ev.get("ts") or ""
        body = _strip_tui_sender_block(text)
        messages.append({
            "timestamp": ts,
            "direction": "in",
            "sender":    "User",
            "text":      body,
        })
        if today and today in str(ts):
            today_in += 1

        sid = ev.get("session_id") or ""
        for c_ev in completions_by_session.get(sid, []):
            c_id = c_ev.get("id") or ""
            if c_id in used_completion_ids:
                continue
            c_ts = c_ev.get("ts") or ""
            if c_ts <= ts:
                # ISO strings sort lexicographically; skip completions
                # that came BEFORE this prompt.
                continue
            c_data = c_ev.get("data") if isinstance(c_ev.get("data"), dict) else {}
            reply = ""
            if isinstance(c_data, dict):
                reply = c_data.get("completionText") or ""
                if not reply:
                    inner = c_data.get("data") if isinstance(c_data.get("data"), dict) else {}
                    reply = inner.get("completionText") or ""
            if not reply:
                # Empty completion (tool-only turn). Mark consumed so we
                # don't re-pair it with a later TUI prompt, then move on.
                used_completion_ids.add(c_id)
                continue
            messages.append({
                "timestamp": c_ts,
                "direction": "out",
                "sender":    "Clawd",
                "text":      str(reply),
            })
            if today and today in str(c_ts):
                today_out += 1
            used_completion_ids.add(c_id)
            break

    # Newest-first, cap to ``limit``.
    messages.sort(key=lambda m: m.get("timestamp") or "", reverse=True)
    capped = messages[:limit]

    return {
        "messages": capped,
        "total":    len(messages),
        "todayIn":  today_in,
        "todayOut": today_out,
        "status":   "local_store_v3",
        "_source":  "local_store_v3",
    }


@bp_channels.route("/api/channels/<provider>/messages")
def api_channel_messages(provider: str):
    """List recent messages for one provider — DuckDB fast path
    (issue #1088 Phase 4).

    Params:
      since (ISO ts, optional): only messages with ``ts >= since``.
      limit (int, default 50, max 1000): page size.

    Falls through to a legacy ``/api/channel/<provider>`` redirect when the
    DuckDB has no rows yet (fresh install, daemon hasn't ingested any
    inbound channel messages). The cloud UI treats that as "no messages
    yet" rather than an error."""
    provider = (provider or "").lower().strip()
    if not provider:
        return jsonify({"error": "provider required"}), 400
    try:
        limit = max(1, min(int(request.args.get("limit", 50)), 1000))
    except (TypeError, ValueError):
        limit = 50
    since = (request.args.get("since") or "").strip() or None
    fast = _try_local_store_channel_messages(provider, since, limit)
    if fast is not None:
        return jsonify(fast)
    # Empty-but-tagged response so the cloud UI distinguishes "schema is
    # live but no rows yet" from "endpoint missing". Per-provider legacy
    # routes (e.g. /api/channel/telegram) still work for callers that need
    # the log-grep fallback during the schema's bake-in window.
    return jsonify({
        "messages": [],
        "total":    0,
        "provider": provider,
        "_source":  "local_store_empty",
    })


@bp_channels.route("/api/channels/<provider>/threads")
def api_channel_threads(provider: str):
    """List recent chat threads (per ``channel_id``) for one provider —
    DuckDB fast path (issue #1088 Phase 4).

    Params:
      limit (int, default 50, max 500): max threads to return.
    """
    provider = (provider or "").lower().strip()
    if not provider:
        return jsonify({"error": "provider required"}), 400
    try:
        limit = max(1, min(int(request.args.get("limit", 50)), 500))
    except (TypeError, ValueError):
        limit = 50
    fast = _try_local_store_channel_threads(provider, limit)
    if fast is not None:
        return jsonify(fast)
    return jsonify({
        "threads":  [],
        "total":    0,
        "provider": provider,
        "_source":  "local_store_empty",
    })


@bp_channels.route("/api/channels/summary")
def api_channels_summary():
    """Cross-provider message counts — DuckDB fast path (issue #1088
    Phase 4). One row per provider with inbound / outbound counts and the
    most-recent activity timestamp."""
    fast = _try_local_store_channel_summary()
    if fast is not None:
        return jsonify(fast)
    return jsonify({
        "providers": [],
        "totals":    {"msgIn": 0, "msgOut": 0, "total": 0},
        "_source":   "local_store_empty",
    })


@bp_channels.route("/api/channel-delivery-health")
def api_channel_delivery_health():
    """Aggregate outbound message delivery integrity across all channels.

    DuckDB fast-path (issue #1757): tries ``query_channel_delivery_health``
    first. Falls back to log-file scanning when DuckDB has no delivery events
    yet (i.e. before adapter instrumentation ships).

    Returns per-channel counts:
    - ``intents``     — run-starts (agent began handling a channel msg)
    - ``ok``          — confirmed outbound deliveries
    - ``failed``      — explicit send failures
    - ``unconfirmed`` — intents with no matching ok/failed entry
    - ``success_rate`` — ok / (ok + failed), null when no sends recorded

    Addresses issue #978: channel delivery failures were logged per-adapter
    but never surfaced in an aggregate view.
    """
    # ── DuckDB fast-path ──────────────────────────────────────────────────
    store_rows = _ls_call("query_channel_delivery_health", since_hours=48)
    if store_rows:
        return jsonify({
            "channels":          store_rows,
            "log_files_scanned": 0,
            "_source":           "local_store",
            "ts":                datetime.now().isoformat(),
        })

    # ── DEPRECATED FALLBACK — delete after adapters emit delivery events ──
    import re
    import dashboard as _d

    _CH_TAG      = re.compile(r"messageChannel=([\w-]+)", re.IGNORECASE)
    _TG_OK       = re.compile(r"sendMessage\s+ok", re.IGNORECASE)
    _TG_FAIL     = re.compile(r"sendMessage.*?fail|telegram message failed", re.IGNORECASE)
    _DELIVER_FAIL = re.compile(r"deliver.*?fail|fail.*?deliver", re.IGNORECASE)
    _DELIVER_OK  = re.compile(r"\bdeliver\b", re.IGNORECASE)
    _RUN_START   = re.compile(r"\brun start\b", re.IGNORECASE)

    log_dirs   = _d._get_log_dirs()
    log_files: list = []
    for ld in log_dirs:
        if os.path.isdir(ld):
            for f in sorted(glob.glob(os.path.join(ld, "*.log")), reverse=True)[:3]:
                log_files.append(f)

    counts: dict = {}

    def _bucket(ch: str) -> dict:
        if ch not in counts:
            counts[ch] = {"intents": 0, "ok": 0, "failed": 0}
        return counts[ch]

    for lf in log_files:
        try:
            lines = _d._grep_log_file(lf, r"sendMessage\|messageChannel\|deliver")
            for raw in lines:
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    obj = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                msg = obj.get("1", "") or obj.get("0", "") or ""
                if not msg:
                    continue

                # Telegram logs sendMessage ok/failed without a messageChannel= tag
                if _TG_OK.search(msg):
                    _bucket("telegram")["ok"] += 1
                    continue
                if _TG_FAIL.search(msg):
                    _bucket("telegram")["failed"] += 1
                    continue

                ch_m = _CH_TAG.search(msg)
                if not ch_m:
                    continue
                ch = ch_m.group(1).lower()

                if _DELIVER_FAIL.search(msg):
                    _bucket(ch)["failed"] += 1
                elif _DELIVER_OK.search(msg):
                    _bucket(ch)["ok"] += 1
                elif _RUN_START.search(msg):
                    _bucket(ch)["intents"] += 1
        except Exception:
            pass

    result = []
    for ch, c in sorted(counts.items()):
        total_sends = c["ok"] + c["failed"]
        result.append({
            "channel":      ch,
            "intents":      c["intents"],
            "ok":           c["ok"],
            "failed":       c["failed"],
            "unconfirmed":  max(0, c["intents"] - total_sends),
            "success_rate": round(c["ok"] / total_sends, 3) if total_sends else None,
        })

    return jsonify({
        "channels":          result,
        "log_files_scanned": len(log_files),
        "ts":                datetime.now().isoformat(),
    })


@bp_channels.route("/api/channel/telegram")
def api_channel_telegram():
    """Parse logs and session transcripts for Telegram message activity.

    Issue #1088 Phase 5 fast-path: when ``CLAWMETRY_LOCAL_STORE_READ=1`` and
    the DuckDB ``channel_messages`` table has Telegram rows, serve from
    there. Falls through to the legacy log-grep path on miss / read flag
    off so the behaviour is bit-identical for existing users."""
    import dashboard as _d
    import re

    limit = request.args.get("limit", 50, type=int)
    offset = request.args.get("offset", 0, type=int)

    if _local_store_read_enabled():
        fast = _try_local_store_provider_messages("telegram", limit + offset)
        if fast is not None:
            # Honour the legacy ``offset`` paginator the Telegram tab uses
            # for "load more". The other per-provider routes don't expose
            # offset so the shared helper doesn't bake it in.
            msgs = fast.get("messages") or []
            fast["messages"] = msgs[offset : offset + limit]
            return jsonify(fast)
        # Tier-1 #1565: v3 events-table fallback when the specialised
        # ``channel_messages`` table is empty but ``events`` carries the
        # channel.in / channel.out turns the daemon already captured. See
        # ``_try_local_store_channel_events`` docstring for the silent-zero
        # bug-class this guards against.
        fast = _try_local_store_channel_events("telegram", limit + offset)
        if fast is not None:
            msgs = fast.get("messages") or []
            fast["messages"] = msgs[offset : offset + limit]
            return jsonify(fast)

    messages = []
    today = datetime.now().strftime("%Y-%m-%d")

    # 1. Parse log files for telegram events using grep for speed
    log_dirs = _d._get_log_dirs()
    log_files = []
    for ld in log_dirs:
        if os.path.isdir(ld):
            for f in sorted(glob.glob(os.path.join(ld, "*.log")), reverse=True):
                log_files.append(f)
    log_files = log_files[:2]  # Only today + yesterday

    run_sessions = {}
    for lf in log_files:
        try:
            # Pre-filter: outbound = "sendMessage ok", inbound via JSONL
            _grep_lines = _d._grep_log_file(
                lf, r"sendMessage ok\|sendMessage failed\|telegram message failed"
            )
            for line in _grep_lines:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                msg1 = obj.get("1", "") or ""
                ts = obj.get("time", "") or (obj.get("_meta", {}) or {}).get("date", "")

                # Outbound: "telegram sendMessage ok chat=1532693273 message=5961"
                if "sendmessage ok" in msg1.lower():
                    chat_match = re.search(r"chat=(-?\d+)", msg1)
                    msg_match = re.search(r"message=(\d+)", msg1)
                    chat_id = chat_match.group(1) if chat_match else ""
                    messages.append(
                        {
                            "timestamp": ts,
                            "direction": "out",
                            "sender": "Bot",
                            "text": f"(sent message {msg_match.group(1) if msg_match else ''})",
                            "chatId": chat_id,
                            "sessionId": "",
                        }
                    )
                elif "sendmessage" in msg1.lower() and "failed" in msg1.lower():
                    messages.append(
                        {
                            "timestamp": ts,
                            "direction": "out",
                            "sender": "Bot",
                            "text": "(delivery failed)",
                            "chatId": "",
                            "sessionId": "",
                        }
                    )
        except Exception:
            pass

    # 2. Parse session JSONL files for inbound messages (user role = incoming Telegram)
    sessions_dir = os.path.expanduser("~/.openclaw/agents/main/sessions")
    for msg in messages:
        if msg["direction"] == "in" and msg["sessionId"] and not msg["text"]:
            sf = os.path.join(sessions_dir, msg["sessionId"] + ".jsonl")
            if os.path.exists(sf):
                try:
                    with open(sf, "r", errors="replace") as f:
                        for sline in f:
                            sline = sline.strip()
                            if not sline:
                                continue
                            try:
                                sd = json.loads(sline)
                            except json.JSONDecodeError:
                                continue
                            sm = sd.get("message", {})
                            if sm.get("role") == "user":
                                content = sm.get("content", "")
                                if isinstance(content, list):
                                    for c in content:
                                        if (
                                            isinstance(c, dict)
                                            and c.get("type") == "text"
                                        ):
                                            txt = c.get("text", "")
                                            # Skip system/heartbeat messages
                                            if (
                                                txt
                                                and not txt.startswith("System:")
                                                and "HEARTBEAT" not in txt
                                            ):
                                                msg["text"] = txt[:300]
                                                # Extract real sender from [Telegram Name id:...] pattern
                                                tg_name = re.search(
                                                    r"\[Telegram\s+(.+?)\s+id:", txt
                                                )
                                                if tg_name:
                                                    msg["sender"] = tg_name.group(1)
                                                break
                                elif isinstance(content, str) and content:
                                    if (
                                        not content.startswith("System:")
                                        and "HEARTBEAT" not in content
                                    ):
                                        msg["text"] = content[:300]
                                        tg_name = re.search(
                                            r"\[Telegram\s+(.+?)\s+id:", content
                                        )
                                        if tg_name:
                                            msg["sender"] = tg_name.group(1)
                                if msg["text"]:
                                    break
                except Exception:
                    pass

    # 3. Also scan telegram session files for recent messages
    try:
        with open(os.path.join(sessions_dir, "sessions.json"), "r") as f:
            sess_data = json.load(f)
        tg_sessions = [
            (sid, s)
            for sid, s in sess_data.items()
            if "telegram" in sid and "sessionId" in s
        ]
        tg_sessions.sort(key=lambda x: x[1].get("updatedAt", 0), reverse=True)

        seen_sids = {m["sessionId"] for m in messages if m["sessionId"]}
        for sid_key, sinfo in tg_sessions[:5]:
            uuid = sinfo["sessionId"]
            if uuid in seen_sids:
                continue
            sf = os.path.join(sessions_dir, uuid + ".jsonl")
            if not os.path.exists(sf):
                continue
            try:
                chat_match = re.search(r":(-?\d+)$", sid_key)
                chat_id = chat_match.group(1) if chat_match else ""
                # Read only last 64KB of session file for performance
                fsize = os.path.getsize(sf)
                with open(sf, "r", errors="replace") as f:
                    if fsize > 65536:
                        f.seek(fsize - 65536)
                        f.readline()  # skip partial line
                    for sline in f:
                        sline = sline.strip()
                        if not sline:
                            continue
                        try:
                            sd = json.loads(sline)
                        except json.JSONDecodeError:
                            continue
                        sm = sd.get("message", {})
                        ts = sd.get("timestamp", "")
                        role = sm.get("role", "")
                        if role not in ("user", "assistant"):
                            continue
                        content = sm.get("content", "")
                        txt = ""
                        if isinstance(content, list):
                            for c in content:
                                if isinstance(c, dict) and c.get("type") == "text":
                                    txt = c.get("text", "")
                                    break
                        elif isinstance(content, str):
                            txt = content
                        if not txt or txt.startswith("System:") or "HEARTBEAT" in txt:
                            continue
                        direction = "in" if role == "user" else "out"
                        sender = "User" if role == "user" else "Clawd"
                        if direction == "in":
                            tg_name = re.search(r"\[Telegram\s+(.+?)\s+id:", txt)
                            if tg_name:
                                sender = tg_name.group(1)
                        messages.append(
                            {
                                "timestamp": ts,
                                "direction": direction,
                                "sender": sender,
                                "text": txt[:300],
                                "chatId": chat_id,
                                "sessionId": uuid,
                            }
                        )
            except Exception:
                pass
    except Exception:
        pass

    # Deduplicate by timestamp+direction, sort newest first
    seen = set()
    unique = []
    for m in messages:
        key = (m["timestamp"], m["direction"], m["text"][:50])
        if key not in seen:
            seen.add(key)
            unique.append(m)
    unique.sort(key=lambda x: x["timestamp"], reverse=True)

    # Stats
    today_in = sum(
        1 for m in unique if m["direction"] == "in" and today in m.get("timestamp", "")
    )
    today_out = sum(
        1 for m in unique if m["direction"] == "out" and today in m.get("timestamp", "")
    )

    total = len(unique)
    page = unique[offset : offset + limit]
    return jsonify(
        {"messages": page, "total": total, "todayIn": today_in, "todayOut": today_out}
    )


@bp_channels.route("/api/channel/imessage")
def api_channel_imessage():
    """Read iMessage history from ~/Library/Messages/chat.db."""
    import dashboard as _d

    if sys.platform != "darwin":
        return jsonify(
            {
                "messages": [],
                "todayIn": 0,
                "todayOut": 0,
                "note": "iMessage is only available on macOS",
            }
        )
    import sqlite3

    limit = request.args.get("limit", 50, type=int)

    messages = []
    today = datetime.now().strftime("%Y-%m-%d")
    # Apple epoch starts 2001-01-01; convert to Unix
    APPLE_EPOCH_OFFSET = 978307200

    db_path = os.path.expanduser("~/Library/Messages/chat.db")
    db_ok = False

    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=5)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            # Get recent messages with handle info
            cur.execute(
                """
                SELECT m.ROWID, m.text, m.is_from_me,
                       m.date / 1000000000 AS date_sec,
                       h.id AS handle_id,
                       h.uncanonicalized_id
                FROM message m
                LEFT JOIN handle h ON m.handle_id = h.ROWID
                WHERE m.text IS NOT NULL AND m.text != ''
                ORDER BY m.date DESC
                LIMIT ?
            """,
                (limit,),
            )
            rows = cur.fetchall()
            conn.close()
            for row in rows:
                direction = "out" if row["is_from_me"] else "in"
                # Convert Apple epoch (nanoseconds) to ISO timestamp
                unix_ts = (row["date_sec"] or 0) + APPLE_EPOCH_OFFSET
                ts = (
                    datetime.utcfromtimestamp(unix_ts).strftime("%Y-%m-%dT%H:%M:%SZ")
                    if unix_ts > APPLE_EPOCH_OFFSET
                    else ""
                )
                contact = row["uncanonicalized_id"] or row["handle_id"] or "Unknown"
                sender = "Me" if direction == "out" else contact
                messages.append(
                    {
                        "timestamp": ts,
                        "direction": direction,
                        "sender": sender,
                        "text": (row["text"] or "")[:300],
                        "chatId": contact,
                        "sessionId": "",
                    }
                )
            db_ok = True
        except Exception:
            pass

    # Fallback: scan OpenClaw logs for imessage delivery events
    if not db_ok or len(messages) == 0:
        log_dirs = _d._get_log_dirs()
        for ld in log_dirs:
            if not os.path.isdir(ld):
                continue
            for lf in sorted(glob.glob(os.path.join(ld, "*.log")), reverse=True)[:2]:
                try:
                    _grep_lines = _d._grep_log_file(
                        lf, "imessage\\|iMessage\\|messageChannel=imessage"
                    )
                    for line in _grep_lines:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            obj = json.loads(line)
                        except Exception:
                            continue
                        ts = obj.get("time", "") or (obj.get("_meta", {}) or {}).get(
                            "date", ""
                        )
                        msg1 = obj.get("1", "") or obj.get("0", "")
                        direction = "out" if "deliver" in msg1.lower() else "in"
                        messages.append(
                            {
                                "timestamp": ts,
                                "direction": direction,
                                "sender": "Me" if direction == "out" else "Contact",
                                "text": msg1[:300],
                                "chatId": "",
                                "sessionId": "",
                            }
                        )
                except Exception:
                    pass

    # Deduplicate and sort newest first
    seen = set()
    unique = []
    for m in messages:
        key = (m["timestamp"], m["direction"], m["text"][:50])
        if key not in seen:
            seen.add(key)
            unique.append(m)
    unique.sort(key=lambda x: x["timestamp"], reverse=True)

    today_in = sum(
        1 for m in unique if m["direction"] == "in" and today in m.get("timestamp", "")
    )
    today_out = sum(
        1 for m in unique if m["direction"] == "out" and today in m.get("timestamp", "")
    )

    total = len(unique)
    page = unique[:limit]
    return jsonify(
        {"messages": page, "total": total, "todayIn": today_in, "todayOut": today_out}
    )


@bp_channels.route("/api/channel/whatsapp")
def api_channel_whatsapp():
    """Parse logs and session transcripts for WhatsApp message activity.

    Issue #1088 Phase 5 fast-path on ``channel_messages`` — see telegram
    handler for the gating + fall-through pattern."""
    import dashboard as _d
    import re

    limit = request.args.get("limit", 50, type=int)

    if _local_store_read_enabled():
        fast = _try_local_store_provider_messages("whatsapp", limit)
        if fast is not None:
            return jsonify(fast)
        # Tier-2 #1565 v3 events-table fallback (2026-05-18 coverage audit).
        # WhatsApp is in ``sync._CHANNEL_DIRS`` so the daemon ingests
        # ``~/.openclaw/whatsapp/*.jsonl`` through ``ingest_channel_event``,
        # but a daemon restart between the ``channel_messages`` projection
        # write and the ``events`` chokepoint can leave ``channel_messages``
        # empty while ``events`` carries the ``channel.in`` / ``channel.out``
        # rows — same silent-zero hazard memory
        # ``feedback_synthetic_tests_missed_real_event_shape.md`` warns
        # about and Telegram / Signal / BlueBubbles already guard for.
        fast = _try_local_store_channel_events("whatsapp", limit)
        if fast is not None:
            return jsonify(fast)

    messages = []
    today = datetime.now().strftime("%Y-%m-%d")

    log_dirs = _d._get_log_dirs()
    log_files = []
    for ld in log_dirs:
        if os.path.isdir(ld):
            for f in sorted(glob.glob(os.path.join(ld, "*.log")), reverse=True)[:2]:
                log_files.append(f)

    sessions_dir = os.path.expanduser("~/.openclaw/agents/main/sessions")

    for lf in log_files:
        try:
            _grep_lines = _d._grep_log_file(
                lf, "messageChannel=whatsapp\\|whatsapp.*deliver"
            )
            for line in _grep_lines:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                msg1 = obj.get("1", "") or obj.get("0", "")
                msg0 = obj.get("0", "")
                ts = obj.get("time", "") or (obj.get("_meta", {}) or {}).get("date", "")

                if "messageChannel=whatsapp" in msg1 and "run start" in msg1:
                    sid_match = re.search(r"sessionId=([a-f0-9-]+)", msg1)
                    sid = sid_match.group(1) if sid_match else ""
                    text = ""
                    if sid:
                        sf = os.path.join(sessions_dir, sid + ".jsonl")
                        if os.path.exists(sf):
                            try:
                                with open(sf, "r", errors="replace") as f:
                                    for sline in f:
                                        try:
                                            sd = json.loads(sline.strip())
                                        except Exception:
                                            continue
                                        sm = sd.get("message", {})
                                        if sm.get("role") == "user":
                                            content = sm.get("content", "")
                                            if isinstance(content, list):
                                                for c in content:
                                                    if (
                                                        isinstance(c, dict)
                                                        and c.get("type") == "text"
                                                    ):
                                                        txt = c.get("text", "")
                                                        if (
                                                            txt
                                                            and "HEARTBEAT" not in txt
                                                        ):
                                                            text = txt[:300]
                                                            break
                                            elif (
                                                isinstance(content, str)
                                                and "HEARTBEAT" not in content
                                            ):
                                                text = content[:300]
                                            if text:
                                                break
                            except Exception:
                                pass
                    messages.append(
                        {
                            "timestamp": ts,
                            "direction": "in",
                            "sender": "User",
                            "text": text,
                            "sessionId": sid,
                        }
                    )

                if "whatsapp" in msg0.lower() and "deliver" in msg0.lower():
                    messages.append(
                        {
                            "timestamp": ts,
                            "direction": "out",
                            "sender": "Clawd",
                            "text": "(message sent)",
                            "sessionId": "",
                        }
                    )
        except Exception:
            pass

    # Deduplicate and sort
    seen = set()
    unique = []
    for m in messages:
        key = (m["timestamp"], m["direction"], m["text"][:50])
        if key not in seen:
            seen.add(key)
            unique.append(m)
    unique.sort(key=lambda x: x["timestamp"], reverse=True)

    today_in = sum(
        1 for m in unique if m["direction"] == "in" and today in m.get("timestamp", "")
    )
    today_out = sum(
        1 for m in unique if m["direction"] == "out" and today in m.get("timestamp", "")
    )
    total = len(unique)
    return jsonify(
        {
            "messages": unique[:limit],
            "total": total,
            "todayIn": today_in,
            "todayOut": today_out,
        }
    )


@bp_channels.route("/api/channel/signal")
def api_channel_signal():
    """Parse logs and session transcripts for Signal message activity.

    Issue #1088 Phase 5 fast-path on ``channel_messages``."""
    import dashboard as _d
    import re

    limit = request.args.get("limit", 50, type=int)

    if _local_store_read_enabled():
        fast = _try_local_store_provider_messages("signal", limit)
        if fast is not None:
            return jsonify(fast)
        # Tier-1 #1565: v3 events-table fallback. Signal DOES land JSONL
        # under ``~/.openclaw/signal/*.jsonl`` so the legacy walker isn't
        # purely dead code, but on real OpenClaw v3 installs the daemon
        # ingests those JSONLs into the ``events`` table directly via the
        # ``ingest_channel_event`` chokepoint — meaning a daemon that
        # restarted between channel_messages writes can leave ``events``
        # populated but ``channel_messages`` empty. Same bug class as the
        # MOAT silent-zero memory `feedback_synthetic_tests_missed_real_event_shape.md`.
        fast = _try_local_store_channel_events("signal", limit)
        if fast is not None:
            return jsonify(fast)

    messages = []
    today = datetime.now().strftime("%Y-%m-%d")

    log_dirs = _d._get_log_dirs()
    log_files = []
    for ld in log_dirs:
        if os.path.isdir(ld):
            for f in sorted(glob.glob(os.path.join(ld, "*.log")), reverse=True)[:2]:
                log_files.append(f)

    sessions_dir = os.path.expanduser("~/.openclaw/agents/main/sessions")

    for lf in log_files:
        try:
            _grep_lines = _d._grep_log_file(lf, "messageChannel=signal\\|signal.*deliver")
            for line in _grep_lines:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                msg1 = obj.get("1", "") or obj.get("0", "")
                msg0 = obj.get("0", "")
                ts = obj.get("time", "") or (obj.get("_meta", {}) or {}).get("date", "")

                if "messageChannel=signal" in msg1 and "run start" in msg1:
                    sid_match = re.search(r"sessionId=([a-f0-9-]+)", msg1)
                    sid = sid_match.group(1) if sid_match else ""
                    text = ""
                    if sid:
                        sf = os.path.join(sessions_dir, sid + ".jsonl")
                        if os.path.exists(sf):
                            try:
                                with open(sf, "r", errors="replace") as f:
                                    for sline in f:
                                        try:
                                            sd = json.loads(sline.strip())
                                        except Exception:
                                            continue
                                        sm = sd.get("message", {})
                                        if sm.get("role") == "user":
                                            content = sm.get("content", "")
                                            if isinstance(content, list):
                                                for c in content:
                                                    if (
                                                        isinstance(c, dict)
                                                        and c.get("type") == "text"
                                                    ):
                                                        txt = c.get("text", "")
                                                        if (
                                                            txt
                                                            and "HEARTBEAT" not in txt
                                                        ):
                                                            text = txt[:300]
                                                            break
                                            elif (
                                                isinstance(content, str)
                                                and "HEARTBEAT" not in content
                                            ):
                                                text = content[:300]
                                            if text:
                                                break
                            except Exception:
                                pass
                    messages.append(
                        {
                            "timestamp": ts,
                            "direction": "in",
                            "sender": "User",
                            "text": text,
                            "sessionId": sid,
                        }
                    )

                if "signal" in msg0.lower() and "deliver" in msg0.lower():
                    messages.append(
                        {
                            "timestamp": ts,
                            "direction": "out",
                            "sender": "Clawd",
                            "text": "(message sent)",
                            "sessionId": "",
                        }
                    )
        except Exception:
            pass

    # Deduplicate and sort
    seen = set()
    unique = []
    for m in messages:
        key = (m["timestamp"], m["direction"], m["text"][:50])
        if key not in seen:
            seen.add(key)
            unique.append(m)
    unique.sort(key=lambda x: x["timestamp"], reverse=True)

    today_in = sum(
        1 for m in unique if m["direction"] == "in" and today in m.get("timestamp", "")
    )
    today_out = sum(
        1 for m in unique if m["direction"] == "out" and today in m.get("timestamp", "")
    )
    total = len(unique)
    return jsonify(
        {
            "messages": unique[:limit],
            "total": total,
            "todayIn": today_in,
            "todayOut": today_out,
        }
    )


@bp_channels.route("/api/channel/discord")
def api_channel_discord():
    """Discord channel data: log-based with guild/channel extraction.

    Issue #1088 Phase 5 fast-path on ``channel_messages`` — extracts
    ``[Discord guild #channel]`` markers out of the row bodies the same
    way the legacy log-grep path does, so the UI's filter dropdowns stay
    populated."""
    import dashboard as _d
    import re

    limit = request.args.get("limit", 50, type=int)

    if _local_store_read_enabled():
        def _extras(rows):
            guilds: set[str] = set()
            channels: set[str] = set()
            for r in rows:
                body = r.get("body") or ""
                m = re.search(r"\[Discord\s+([^\]]+?)\s+#?(\S+)\]", body)
                if m:
                    guilds.add(m.group(1))
                    channels.add(m.group(2))
            return {"guilds": sorted(guilds), "channels": sorted(channels)}
        fast = _try_local_store_provider_messages("discord", limit, _extras)
        if fast is not None:
            return jsonify(fast)

    today = datetime.now().strftime("%Y-%m-%d")
    messages = []
    guilds = set()
    channels = set()
    today_in = 0
    today_out = 0

    # Scan log files for Discord events
    log_dirs = _d._get_log_dirs()
    for ld in log_dirs:
        if not os.path.isdir(ld):
            continue
        for lf in sorted(glob.glob(os.path.join(ld, "*.log")), reverse=True)[:3]:
            try:
                _grep_lines = _d._grep_log_file(
                    lf, "messageChannel=discord|discord.*deliver"
                )
                for line in _grep_lines:
                    try:
                        obj = json.loads(line.strip())
                    except Exception:
                        continue
                    msg1 = obj.get("1", "") or obj.get("0", "")
                    ts = obj.get("time", "")
                    if "messageChannel=discord" in msg1:
                        direction = "in"
                        messages.append(
                            {
                                "timestamp": ts,
                                "direction": "in",
                                "sender": "User",
                                "text": msg1[:300],
                            }
                        )
                        if today and today in ts:
                            today_in += 1
                    elif re.search(r"discord.*deliver", msg1, re.IGNORECASE):
                        messages.append(
                            {
                                "timestamp": ts,
                                "direction": "out",
                                "sender": "Bot",
                                "text": msg1[:300],
                            }
                        )
                        if today and today in ts:
                            today_out += 1
            except Exception:
                pass

    # Scan session transcripts for Discord messages and guild/channel info
    sessions_dir = os.path.expanduser("~/.openclaw/agents/main/sessions")
    sessions_file = os.path.join(sessions_dir, "sessions.json")
    if os.path.exists(sessions_file):
        try:
            with open(sessions_file) as f:
                sess_data = json.load(f)
            ch_sessions = [
                (sid, s)
                for sid, s in sess_data.items()
                if "discord" in sid.lower() and "sessionId" in s
            ]
            ch_sessions.sort(key=lambda x: x[1].get("updatedAt", 0), reverse=True)
            for sid_key, sinfo in ch_sessions[:5]:
                uuid = sinfo["sessionId"]
                sf = os.path.join(sessions_dir, uuid + ".jsonl")
                if not os.path.exists(sf):
                    continue
                try:
                    fsize = os.path.getsize(sf)
                    with open(sf, "r", errors="replace") as f:
                        if fsize > 65536:
                            f.seek(fsize - 65536)
                            f.readline()
                        for sline in f:
                            sline = sline.strip()
                            if not sline:
                                continue
                            try:
                                sd = json.loads(sline)
                            except Exception:
                                continue
                            sm = sd.get("message", {})
                            ts = sd.get("timestamp", "")
                            role = sm.get("role", "")
                            if role not in ("user", "assistant"):
                                continue
                            content = sm.get("content", "")
                            txt = ""
                            if isinstance(content, list):
                                for c in content:
                                    if isinstance(c, dict) and c.get("type") == "text":
                                        txt = c.get("text", "")
                                        break
                            elif isinstance(content, str):
                                txt = content
                            if (
                                not txt
                                or txt.startswith("System:")
                                or "HEARTBEAT" in txt
                            ):
                                continue
                            # Extract guild/channel from [Discord guildName channelName] pattern
                            m = re.search(r"\[Discord\s+([^\]]+?)\s+#?(\S+)\]", txt)
                            if m:
                                guilds.add(m.group(1))
                                channels.add(m.group(2))
                            direction = "in" if role == "user" else "out"
                            messages.append(
                                {
                                    "timestamp": ts,
                                    "direction": direction,
                                    "sender": "User" if direction == "in" else "Bot",
                                    "text": txt[:300],
                                }
                            )
                            if today and today in ts:
                                if direction == "in":
                                    today_in += 1
                                else:
                                    today_out += 1
                except Exception:
                    pass
        except Exception:
            pass

    # Deduplicate and sort
    seen = set()
    unique = []
    for m in messages:
        key = (m["timestamp"], m["direction"], m["text"][:50])
        if key not in seen:
            seen.add(key)
            unique.append(m)
    unique.sort(key=lambda x: x["timestamp"], reverse=True)

    return jsonify(
        {
            "messages": unique[:limit],
            "total": len(unique),
            "todayIn": today_in,
            "todayOut": today_out,
            "guilds": sorted(guilds),
            "channels": sorted(channels),
        }
    )


@bp_channels.route("/api/channel/slack")
def api_channel_slack():
    """Slack channel data: log-based with workspace/channel extraction.

    Issue #1088 Phase 5 fast-path — extracts ``[Slack workspace #channel]``
    markers + #-mentions out of DuckDB row bodies, mirroring the legacy
    regex set so the UI filters still populate."""
    import dashboard as _d
    import re

    limit = request.args.get("limit", 50, type=int)

    if _local_store_read_enabled():
        def _extras(rows):
            workspaces: set[str] = set()
            channels: set[str] = set()
            for r in rows:
                body = r.get("body") or ""
                m = re.search(r"\[Slack\s+([^\]]+?)\s+#?(\S+)\]", body)
                if m:
                    workspaces.add(m.group(1))
                    channels.add(m.group(2))
                for ch in re.findall(r"#([a-z0-9_-]+)", body[:200]):
                    channels.add(ch)
            return {
                "workspaces": sorted(workspaces),
                "channels":   sorted(channels),
            }
        fast = _try_local_store_provider_messages("slack", limit, _extras)
        if fast is not None:
            return jsonify(fast)

    today = datetime.now().strftime("%Y-%m-%d")
    messages = []
    workspaces = set()
    channels = set()
    today_in = 0
    today_out = 0

    # Scan log files for Slack events
    log_dirs = _d._get_log_dirs()
    for ld in log_dirs:
        if not os.path.isdir(ld):
            continue
        for lf in sorted(glob.glob(os.path.join(ld, "*.log")), reverse=True)[:3]:
            try:
                _grep_lines = _d._grep_log_file(lf, "messageChannel=slack|slack.*deliver")
                for line in _grep_lines:
                    try:
                        obj = json.loads(line.strip())
                    except Exception:
                        continue
                    msg1 = obj.get("1", "") or obj.get("0", "")
                    ts = obj.get("time", "")
                    if "messageChannel=slack" in msg1:
                        messages.append(
                            {
                                "timestamp": ts,
                                "direction": "in",
                                "sender": "User",
                                "text": msg1[:300],
                            }
                        )
                        if today and today in ts:
                            today_in += 1
                    elif re.search(r"slack.*deliver", msg1, re.IGNORECASE):
                        messages.append(
                            {
                                "timestamp": ts,
                                "direction": "out",
                                "sender": "Bot",
                                "text": msg1[:300],
                            }
                        )
                        if today and today in ts:
                            today_out += 1
            except Exception:
                pass

    # Scan session transcripts for Slack messages and workspace/channel info
    sessions_dir = os.path.expanduser("~/.openclaw/agents/main/sessions")
    sessions_file = os.path.join(sessions_dir, "sessions.json")
    if os.path.exists(sessions_file):
        try:
            with open(sessions_file) as f:
                sess_data = json.load(f)
            ch_sessions = [
                (sid, s)
                for sid, s in sess_data.items()
                if "slack" in sid.lower() and "sessionId" in s
            ]
            ch_sessions.sort(key=lambda x: x[1].get("updatedAt", 0), reverse=True)
            for sid_key, sinfo in ch_sessions[:5]:
                uuid = sinfo["sessionId"]
                sf = os.path.join(sessions_dir, uuid + ".jsonl")
                if not os.path.exists(sf):
                    continue
                try:
                    fsize = os.path.getsize(sf)
                    with open(sf, "r", errors="replace") as f:
                        if fsize > 65536:
                            f.seek(fsize - 65536)
                            f.readline()
                        for sline in f:
                            sline = sline.strip()
                            if not sline:
                                continue
                            try:
                                sd = json.loads(sline)
                            except Exception:
                                continue
                            sm = sd.get("message", {})
                            ts = sd.get("timestamp", "")
                            role = sm.get("role", "")
                            if role not in ("user", "assistant"):
                                continue
                            content = sm.get("content", "")
                            txt = ""
                            if isinstance(content, list):
                                for c in content:
                                    if isinstance(c, dict) and c.get("type") == "text":
                                        txt = c.get("text", "")
                                        break
                            elif isinstance(content, str):
                                txt = content
                            if (
                                not txt
                                or txt.startswith("System:")
                                or "HEARTBEAT" in txt
                            ):
                                continue
                            # Extract workspace/channel from [Slack workspace #channel] pattern
                            m = re.search(r"\[Slack\s+([^\]]+?)\s+#?(\S+)\]", txt)
                            if m:
                                workspaces.add(m.group(1))
                                channels.add(m.group(2))
                            # Also look for channel mentions like #general
                            ch_m = re.findall(r"#([a-z0-9_-]+)", txt[:200])
                            for ch in ch_m:
                                channels.add(ch)
                            direction = "in" if role == "user" else "out"
                            messages.append(
                                {
                                    "timestamp": ts,
                                    "direction": direction,
                                    "sender": "User" if direction == "in" else "Bot",
                                    "text": txt[:300],
                                }
                            )
                            if today and today in ts:
                                if direction == "in":
                                    today_in += 1
                                else:
                                    today_out += 1
                except Exception:
                    pass
        except Exception:
            pass

    # Deduplicate and sort
    seen = set()
    unique = []
    for m in messages:
        key = (m["timestamp"], m["direction"], m["text"][:50])
        if key not in seen:
            seen.add(key)
            unique.append(m)
    unique.sort(key=lambda x: x["timestamp"], reverse=True)

    return jsonify(
        {
            "messages": unique[:limit],
            "total": len(unique),
            "todayIn": today_in,
            "todayOut": today_out,
            "workspaces": sorted(workspaces),
            "channels": sorted(channels),
        }
    )


@bp_channels.route("/api/channel/irc")
def api_channel_irc():
    """IRC channel data: log-based, extracts channel names and nicks.

    Issue #1088 Phase 5 fast-path — pulls ``#channel`` and ``[IRC #ch nick]``
    markers out of DuckDB row bodies. ``status`` defaults to "connected"
    when there are rows, matching the legacy heuristic."""
    import dashboard as _d
    import re

    limit = request.args.get("limit", 50, type=int)

    if _local_store_read_enabled():
        def _extras(rows):
            channels: set[str] = set()
            nicks: set[str] = set()
            for r in rows:
                body = r.get("body") or ""
                for ch in re.findall(r"#\w+", body):
                    channels.add(ch)
                for nick in re.findall(r"nick[=:](\w+)", body, re.I):
                    nicks.add(nick)
                for ch in re.findall(r"\[IRC\s+(#\w+)", body):
                    channels.add(ch)
                for nick in re.findall(r"\[IRC\s+#\w+\s+(\w+)\]", body):
                    nicks.add(nick)
            return {
                "channels": sorted(channels),
                "nicks":    sorted(nicks),
                "status":   "connected" if rows else "configured",
            }
        fast = _try_local_store_provider_messages("irc", limit, _extras)
        if fast is not None:
            return jsonify(fast)

    today = datetime.now().strftime("%Y-%m-%d")
    base = (
        _d._generic_channel_data.__wrapped__("irc")
        if hasattr(_d._generic_channel_data, "__wrapped__")
        else None
    )

    messages = []
    today_in = 0
    today_out = 0
    channels = set()
    nicks = set()

    log_dirs = _d._get_log_dirs()
    for ld in log_dirs:
        if not os.path.isdir(ld):
            continue
        for lf in sorted(glob.glob(os.path.join(ld, "*.log")), reverse=True)[:3]:
            try:
                _grep_lines = _d._grep_log_file(lf, "messageChannel=irc")
                for line in _grep_lines:
                    try:
                        obj = json.loads(line.strip())
                    except Exception:
                        continue
                    msg1 = obj.get("1", "") or obj.get("0", "")
                    ts = obj.get("time", "")
                    direction = "out" if "deliver" in msg1.lower() else "in"
                    messages.append(
                        {
                            "timestamp": ts,
                            "direction": direction,
                            "sender": "User" if direction == "in" else "Clawd",
                            "text": msg1[:200],
                        }
                    )
                    if today and today in ts:
                        if direction == "in":
                            today_in += 1
                        else:
                            today_out += 1
                    # Extract IRC channels/nicks from log
                    for ch in re.findall(r"#\w+", msg1):
                        channels.add(ch)
                    for nick in re.findall(r"nick[=:](\w+)", msg1, re.I):
                        nicks.add(nick)
            except Exception:
                pass

    # Also scan session transcripts
    for sessions_dir in [
        os.path.expanduser("~/.openclaw/agents/main/sessions"),
        os.path.expanduser("~/.clawdbot/agents/main/sessions"),
    ]:
        sessions_file = os.path.join(sessions_dir, "sessions.json")
        if not os.path.exists(sessions_file):
            continue
        try:
            with open(sessions_file) as f:
                sess_data = json.load(f)
            ch_sessions = [
                (sid, s)
                for sid, s in sess_data.items()
                if "irc" in sid.lower() and "sessionId" in s
            ]
            ch_sessions.sort(key=lambda x: x[1].get("updatedAt", 0), reverse=True)
            for sid_key, sinfo in ch_sessions[:5]:
                uuid = sinfo["sessionId"]
                sf = os.path.join(sessions_dir, uuid + ".jsonl")
                if not os.path.exists(sf):
                    continue
                try:
                    with open(sf, "r", errors="replace") as f:
                        for sline in f:
                            sline = sline.strip()
                            if not sline:
                                continue
                            try:
                                sd = json.loads(sline)
                            except Exception:
                                continue
                            sm = sd.get("message", {})
                            ts = sd.get("timestamp", "")
                            role = sm.get("role", "")
                            if role not in ("user", "assistant"):
                                continue
                            content = sm.get("content", "")
                            txt = ""
                            if isinstance(content, list):
                                for c in content:
                                    if isinstance(c, dict) and c.get("type") == "text":
                                        txt = c.get("text", "")
                                        break
                            elif isinstance(content, str):
                                txt = content
                            if not txt or "HEARTBEAT" in txt:
                                continue
                            for ch in re.findall(r"\[IRC\s+(#\w+)", txt):
                                channels.add(ch)
                            for nick in re.findall(r"\[IRC\s+#\w+\s+(\w+)\]", txt):
                                nicks.add(nick)
                            direction = "in" if role == "user" else "out"
                            messages.append(
                                {
                                    "timestamp": ts,
                                    "direction": direction,
                                    "sender": "User" if direction == "in" else "Clawd",
                                    "text": txt[:300],
                                }
                            )
                            if today and today in ts:
                                if direction == "in":
                                    today_in += 1
                                else:
                                    today_out += 1
                except Exception:
                    pass
        except Exception:
            pass

    seen = set()
    unique = []
    for m in messages:
        key = (m["timestamp"], m["direction"], m["text"][:50])
        if key not in seen:
            seen.add(key)
            unique.append(m)
    unique.sort(key=lambda x: x["timestamp"], reverse=True)

    return jsonify(
        {
            "messages": unique[:limit],
            "total": len(unique),
            "todayIn": today_in,
            "todayOut": today_out,
            "channels": sorted(channels),
            "nicks": sorted(nicks),
            "status": "connected" if unique else "configured",
        }
    )


@bp_channels.route("/api/channel/webchat")
def api_channel_webchat():
    """Webchat channel data: parse logs + sessions, return active session info.

    Issue #1088 Phase 5 fast-path — derives ``activeSessions`` and
    ``lastActive`` from the DuckDB row set (distinct ``session_key`` and
    ``MAX(ts)`` respectively) so the cloud UI's "Live sessions" badge
    stays correct without grepping log files."""
    import dashboard as _d
    import re

    limit = request.args.get("limit", 50, type=int)

    if _local_store_read_enabled():
        def _extras(rows):
            active = {r.get("session_key") for r in rows if r.get("session_key")}
            last = max((r.get("ts") or "" for r in rows), default=None) or None
            return {
                "activeSessions": len(active),
                "lastActive":     last,
                "status":         "connected" if rows else "configured",
            }
        fast = _try_local_store_provider_messages("webchat", limit, _extras)
        if fast is not None:
            return jsonify(fast)

    today = datetime.now().strftime("%Y-%m-%d")

    messages = []
    today_in = 0
    today_out = 0
    active_sessions = set()
    last_active = None

    log_dirs = _d._get_log_dirs()
    for ld in log_dirs:
        if not os.path.isdir(ld):
            continue
        for lf in sorted(glob.glob(os.path.join(ld, "*.log")), reverse=True)[:3]:
            try:
                _grep_lines = _d._grep_log_file(lf, "messageChannel=webchat")
                for line in _grep_lines:
                    try:
                        obj = json.loads(line.strip())
                    except Exception:
                        continue
                    msg1 = obj.get("1", "") or obj.get("0", "")
                    ts = obj.get("time", "")
                    direction = "out" if "deliver" in msg1.lower() else "in"
                    messages.append(
                        {
                            "timestamp": ts,
                            "direction": direction,
                            "sender": "User" if direction == "in" else "Clawd",
                            "text": msg1[:200],
                        }
                    )
                    if today and today in ts:
                        if direction == "in":
                            today_in += 1
                        else:
                            today_out += 1
                    # Extract session IDs
                    for sid in re.findall(r"sessionId=([a-f0-9\-]+)", msg1):
                        active_sessions.add(sid)
                    if ts and (last_active is None or ts > last_active):
                        last_active = ts
            except Exception:
                pass

    # Scan sessions for webchat sessions
    for sessions_dir in [
        os.path.expanduser("~/.openclaw/agents/main/sessions"),
        os.path.expanduser("~/.clawdbot/agents/main/sessions"),
    ]:
        sessions_file = os.path.join(sessions_dir, "sessions.json")
        if not os.path.exists(sessions_file):
            continue
        try:
            with open(sessions_file) as f:
                sess_data = json.load(f)
            wc_sessions = [
                (sid, s)
                for sid, s in sess_data.items()
                if "webchat" in sid.lower() and "sessionId" in s
            ]
            wc_sessions.sort(key=lambda x: x[1].get("updatedAt", 0), reverse=True)
            for sid_key, sinfo in wc_sessions[:10]:
                active_sessions.add(sinfo["sessionId"])
                upd = sinfo.get("updatedAt", 0)
                if upd:
                    ts_str = datetime.fromtimestamp(
                        upd / 1000 if upd > 1e10 else upd
                    ).isoformat()
                    if last_active is None or ts_str > last_active:
                        last_active = ts_str
            # Load messages from recent webchat sessions
            for sid_key, sinfo in wc_sessions[:3]:
                uuid = sinfo["sessionId"]
                sf = os.path.join(sessions_dir, uuid + ".jsonl")
                if not os.path.exists(sf):
                    continue
                try:
                    fsize = os.path.getsize(sf)
                    with open(sf, "r", errors="replace") as f:
                        if fsize > 65536:
                            f.seek(fsize - 65536)
                            f.readline()
                        for sline in f:
                            sline = sline.strip()
                            if not sline:
                                continue
                            try:
                                sd = json.loads(sline)
                            except Exception:
                                continue
                            sm = sd.get("message", {})
                            ts = sd.get("timestamp", "")
                            role = sm.get("role", "")
                            if role not in ("user", "assistant"):
                                continue
                            content = sm.get("content", "")
                            txt = ""
                            if isinstance(content, list):
                                for c in content:
                                    if isinstance(c, dict) and c.get("type") == "text":
                                        txt = c.get("text", "")
                                        break
                            elif isinstance(content, str):
                                txt = content
                            if not txt or "HEARTBEAT" in txt:
                                continue
                            direction = "in" if role == "user" else "out"
                            messages.append(
                                {
                                    "timestamp": ts,
                                    "direction": direction,
                                    "sender": "User" if direction == "in" else "Clawd",
                                    "text": txt[:300],
                                }
                            )
                            if today and today in ts:
                                if direction == "in":
                                    today_in += 1
                                else:
                                    today_out += 1
                except Exception:
                    pass
        except Exception:
            pass

    # Also check ~/.openclaw/webchat/ dir
    wc_dir = os.path.expanduser("~/.openclaw/webchat")
    if os.path.isdir(wc_dir):
        for f in glob.glob(os.path.join(wc_dir, "*.json"))[:5]:
            active_sessions.add(os.path.basename(f).replace(".json", ""))

    seen = set()
    unique = []
    for m in messages:
        key = (m["timestamp"], m["direction"], m["text"][:50])
        if key not in seen:
            seen.add(key)
            unique.append(m)
    unique.sort(key=lambda x: x["timestamp"], reverse=True)

    return jsonify(
        {
            "messages": unique[:limit],
            "total": len(unique),
            "todayIn": today_in,
            "todayOut": today_out,
            "activeSessions": len(active_sessions),
            "lastActive": last_active,
            "status": "connected" if unique else "configured",
        }
    )


@bp_channels.route("/api/channel/googlechat")
def api_channel_googlechat():
    """Issue #1088 Phase 5 fast-path on ``channel_messages``. Falls through
    to the generic log-grep helper on miss. ``spaces`` stays empty —
    populated downstream once the Google Chat adapter publishes space
    metadata (tracked separately)."""
    import dashboard as _d
    if _local_store_read_enabled():
        fast = _try_local_store_provider_messages(
            "googlechat", request.args.get("limit", 50, type=int),
            extras_extractor=lambda _rows: {"spaces": []},
        )
        if fast is not None:
            return jsonify(fast)
    result = _d._generic_channel_data("googlechat")
    data = result.get_json()
    data["spaces"] = []
    return jsonify(data)


@bp_channels.route("/api/channel/bluebubbles")
def api_channel_bluebubbles():
    """BlueBubbles channel: try REST API first, fallback to logs.

    Tier-1 #1565: when ``CLAWMETRY_LOCAL_STORE_READ=1`` and the daemon
    has already ingested ``~/.openclaw/bluebubbles/*.jsonl`` turns into
    DuckDB (``bluebubbles`` is in ``sync._CHANNEL_DIRS``), serve from
    the unified ``channel_messages`` table first, then fall back to the
    ``events`` table — same dual-tier pattern PR #1585 wired for
    Telegram + Signal. The legacy BlueBubbles REST API call + log-grep
    stays as a last resort so an install with the read flag OFF, or a
    daemon that hasn't caught up yet, still sees the live counts.
    """
    import dashboard as _d

    limit = request.args.get("limit", 50, type=int)
    today = datetime.now().strftime("%Y-%m-%d")

    # Tier-1 #1565 fast paths. Run BEFORE the BlueBubbles REST probe so
    # a configured server doesn't add a 3s timeout to every poll once
    # DuckDB has the rows. ``chatCount``/``status`` get a v3-aware
    # default so the response envelope stays compatible with the UI.
    if _local_store_read_enabled():
        fast = _try_local_store_provider_messages("bluebubbles", limit)
        if fast is not None:
            fast.setdefault("chatCount", None)
            fast.setdefault("status", "local_store")
            return jsonify(fast)
        # Events-table fallback. Same silent-zero hazard as Telegram/Signal:
        # the chokepoint dual-writes but a re-ingest after a daemon restart
        # can leave ``channel_messages`` empty while ``events`` carries the
        # ``channel.in`` / ``channel.out`` rows. See memory
        # ``feedback_synthetic_tests_missed_real_event_shape.md``.
        fast = _try_local_store_channel_events("bluebubbles", limit)
        if fast is not None:
            fast.setdefault("chatCount", None)
            fast.setdefault("status", "local_store_v3")
            return jsonify(fast)

    messages = []
    today_in = 0
    today_out = 0
    chat_count = None
    bb_status = "configured"

    # Check for BlueBubbles config
    cfg_path = os.path.expanduser("~/.openclaw/openclaw.json")
    bb_url = None
    bb_pass = None
    if os.path.exists(cfg_path):
        try:
            with open(cfg_path) as f:
                cfg = json.load(f)
            bb_cfg = cfg.get("channels", {}).get("bluebubbles", {})
            bb_url = bb_cfg.get("serverUrl", "").rstrip("/")
            bb_pass = bb_cfg.get("password", "")
        except Exception:
            pass

    # Try BlueBubbles REST API
    if bb_url:
        try:
            import urllib.request

            api_url = f"{bb_url}/api/v1/chat/count"
            req = urllib.request.Request(
                api_url,
                headers={"Authorization": f"Bearer {bb_pass}"} if bb_pass else {},
            )
            with urllib.request.urlopen(req, timeout=3) as resp:
                bb_data = json.loads(resp.read().decode())
                chat_count = bb_data.get("data", {}).get(
                    "total", bb_data.get("total", 0)
                )
                bb_status = "connected"
            # Try to get recent messages
            msgs_url = f"{bb_url}/api/v1/message/count/me?limit=50"
            req2 = urllib.request.Request(
                msgs_url,
                headers={"Authorization": f"Bearer {bb_pass}"} if bb_pass else {},
            )
            with urllib.request.urlopen(req2, timeout=3) as resp2:
                pass  # just count endpoint
        except Exception:
            pass

    # Fallback: parse logs
    log_dirs = _d._get_log_dirs()
    for ld in log_dirs:
        if not os.path.isdir(ld):
            continue
        for lf in sorted(glob.glob(os.path.join(ld, "*.log")), reverse=True)[:3]:
            try:
                _grep_lines = _d._grep_log_file(lf, "messageChannel=bluebubbles")
                for line in _grep_lines:
                    try:
                        obj = json.loads(line.strip())
                    except Exception:
                        continue
                    msg1 = obj.get("1", "") or obj.get("0", "")
                    ts = obj.get("time", "")
                    direction = "out" if "deliver" in msg1.lower() else "in"
                    messages.append(
                        {
                            "timestamp": ts,
                            "direction": direction,
                            "sender": "User" if direction == "in" else "Clawd",
                            "text": msg1[:200],
                        }
                    )
                    if today and today in ts:
                        if direction == "in":
                            today_in += 1
                        else:
                            today_out += 1
                    if bb_status == "configured":
                        bb_status = "log-only"
            except Exception:
                pass

    # Scan sessions
    for sessions_dir in [
        os.path.expanduser("~/.openclaw/agents/main/sessions"),
        os.path.expanduser("~/.clawdbot/agents/main/sessions"),
    ]:
        sessions_file = os.path.join(sessions_dir, "sessions.json")
        if not os.path.exists(sessions_file):
            continue
        try:
            with open(sessions_file) as f:
                sess_data = json.load(f)
            ch_sessions = [
                (sid, s)
                for sid, s in sess_data.items()
                if "bluebubbles" in sid.lower() and "sessionId" in s
            ]
            ch_sessions.sort(key=lambda x: x[1].get("updatedAt", 0), reverse=True)
            for sid_key, sinfo in ch_sessions[:3]:
                uuid = sinfo["sessionId"]
                sf = os.path.join(sessions_dir, uuid + ".jsonl")
                if not os.path.exists(sf):
                    continue
                try:
                    with open(sf, "r", errors="replace") as f:
                        for sline in f:
                            sline = sline.strip()
                            if not sline:
                                continue
                            try:
                                sd = json.loads(sline)
                            except Exception:
                                continue
                            sm = sd.get("message", {})
                            ts = sd.get("timestamp", "")
                            role = sm.get("role", "")
                            if role not in ("user", "assistant"):
                                continue
                            content = sm.get("content", "")
                            txt = ""
                            if isinstance(content, list):
                                for c in content:
                                    if isinstance(c, dict) and c.get("type") == "text":
                                        txt = c.get("text", "")
                                        break
                            elif isinstance(content, str):
                                txt = content
                            if not txt or "HEARTBEAT" in txt:
                                continue
                            direction = "in" if role == "user" else "out"
                            messages.append(
                                {
                                    "timestamp": ts,
                                    "direction": direction,
                                    "sender": "User" if direction == "in" else "Clawd",
                                    "text": txt[:300],
                                }
                            )
                            if today and today in ts:
                                if direction == "in":
                                    today_in += 1
                                else:
                                    today_out += 1
                except Exception:
                    pass
        except Exception:
            pass

    seen = set()
    unique = []
    for m in messages:
        key = (m["timestamp"], m["direction"], m["text"][:50])
        if key not in seen:
            seen.add(key)
            unique.append(m)
    unique.sort(key=lambda x: x["timestamp"], reverse=True)

    return jsonify(
        {
            "messages": unique[:limit],
            "total": len(unique),
            "todayIn": today_in,
            "todayOut": today_out,
            "chatCount": chat_count,
            "status": bb_status,
        }
    )


@bp_channels.route("/api/channel/msteams")
def api_channel_msteams():
    """Issue #1088 Phase 5 fast-path on ``channel_messages``. ``teams``
    stays empty — populated once the MS Teams adapter publishes team
    metadata."""
    import dashboard as _d
    if _local_store_read_enabled():
        fast = _try_local_store_provider_messages(
            "msteams", request.args.get("limit", 50, type=int),
            extras_extractor=lambda _rows: {"teams": []},
        )
        if fast is not None:
            return jsonify(fast)
    result = _d._generic_channel_data("msteams")
    data = result.get_json()
    data["teams"] = []
    return jsonify(data)


@bp_channels.route("/api/channel/tui")
def api_channel_tui():
    """TUI channel: scans session JSONLs for user messages whose `Sender
    (untrusted metadata)` JSON label is `openclaw-tui`, and the
    immediately-following assistant reply as the outbound.

    Unlike Telegram/Signal/etc which have dedicated channel adapters and
    log to `gateway.log`, the OpenClaw TUI writes directly into the active
    session JSONL — so we reconstruct the conversation from there.

    Issue #1656 DuckDB fast path: when the daemon has already ingested
    the same session JSONLs into the local store (`prompt.submitted` +
    `model.completed` events tagged with the `openclaw-tui` Sender
    marker), serve from DuckDB first to avoid the O(sessions) directory
    scan on every poll. Falls through to the legacy JSONL walker on
    miss so fresh installs (daemon hasn't caught up) still work.
    """
    import dashboard as _d
    import re as _re

    limit = request.args.get("limit", 50, type=int)
    today = datetime.now().strftime("%Y-%m-%d")

    # MOAT-first read path (#1656). Mirrors the bluebubbles/telegram/signal
    # sibling pattern at routes/channels.py:2048-2063 — try the v3 events
    # table FIRST; only fall through to the legacy walker if DuckDB has no
    # TUI-tagged prompts yet.
    if _local_store_read_enabled():
        fast = _try_local_store_channel_tui(limit)
        if fast is not None:
            return jsonify(fast)

    sessions_dir = _d.SESSIONS_DIR or os.path.expanduser(
        "~/.openclaw/agents/main/sessions"
    )
    if not os.path.isdir(sessions_dir):
        return jsonify({"messages": [], "todayIn": 0, "todayOut": 0,
                        "status": "no sessions dir"})

    # Only scan the most-recent 3 sessions (by mtime) — good enough to
    # capture the active conversation without loading hours of history.
    files = sorted(
        [f for f in glob.glob(os.path.join(sessions_dir, "*.jsonl"))
         if ".deleted." not in f and os.path.getsize(f) > 0],
        key=os.path.getmtime, reverse=True,
    )[:3]

    def _strip_sender_block(text):
        """Remove the `Sender (untrusted metadata)` JSON preamble from a
        user message so the rendered bubble shows the real content."""
        if not isinstance(text, str):
            return text
        m = _re.search(r"```json\s*\{[^`]*?\}\s*```\s*", text, _re.DOTALL)
        return (text[m.end():] if m else text).strip()

    messages = []
    today_in = 0
    today_out = 0
    for fpath in files:
        try:
            with open(fpath, "r", errors="replace") as fh:
                prev_was_tui_in = False
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
                    content = msg.get("content") or []
                    ts = ev.get("timestamp", "") or ev.get("time", "")

                    # Inbound — user message tagged openclaw-tui
                    if role == "user" and isinstance(content, list) and content:
                        first = content[0]
                        text = first.get("text", "") if isinstance(first, dict) else ""
                        if "openclaw-tui" not in text:
                            prev_was_tui_in = False
                            continue
                        body = _strip_sender_block(text)
                        messages.append({
                            "timestamp": ts,
                            "direction": "in",
                            "sender": "User",
                            "text": body,
                        })
                        if today and today in str(ts):
                            today_in += 1
                        prev_was_tui_in = True
                        continue

                    # Outbound — assistant reply that immediately follows a
                    # TUI inbound (OpenClaw replies to whichever channel the
                    # last user message came from)
                    if role == "assistant" and prev_was_tui_in and isinstance(content, list):
                        reply_parts = []
                        for blk in content:
                            if isinstance(blk, dict) and blk.get("type") == "text":
                                t = blk.get("text", "")
                                if t:
                                    reply_parts.append(t)
                        if reply_parts:
                            messages.append({
                                "timestamp": ts,
                                "direction": "out",
                                "sender": "Clawd",
                                "text": " ".join(reply_parts),
                            })
                            if today and today in str(ts):
                                today_out += 1
                        prev_was_tui_in = False
                        continue

                    # toolResult / other roles don't toggle the tui flag
                    if role not in ("toolResult",):
                        prev_was_tui_in = False
        except Exception:
            continue

    # Newest first, cap to limit
    messages.sort(key=lambda m: m.get("timestamp", ""), reverse=True)
    messages = messages[:limit]

    return jsonify({
        "messages": messages,
        "todayIn": today_in,
        "todayOut": today_out,
        "total": len(messages),
        "status": "connected",
    })


@bp_channels.route("/api/channel/matrix")
def api_channel_matrix():
    """Issue #1088 Phase 5 fast-path on ``channel_messages``."""
    import dashboard as _d
    if _local_store_read_enabled():
        fast = _try_local_store_provider_messages(
            "matrix", request.args.get("limit", 50, type=int),
        )
        if fast is not None:
            return jsonify(fast)
    return _d._generic_channel_data("matrix")


@bp_channels.route("/api/channel/mattermost")
def api_channel_mattermost():
    """Issue #1088 Phase 5 fast-path on ``channel_messages``. ``channels``
    stays empty — populated once the Mattermost adapter publishes team
    /channel metadata."""
    import dashboard as _d
    if _local_store_read_enabled():
        fast = _try_local_store_provider_messages(
            "mattermost", request.args.get("limit", 50, type=int),
            extras_extractor=lambda _rows: {"channels": []},
        )
        if fast is not None:
            return jsonify(fast)
    result = _d._generic_channel_data("mattermost")
    data = result.get_json()
    data["channels"] = []
    return jsonify(data)


@bp_channels.route("/api/channel/line")
def api_channel_line():
    """Issue #1088 Phase 5 fast-path on ``channel_messages``."""
    import dashboard as _d
    if _local_store_read_enabled():
        fast = _try_local_store_provider_messages(
            "line", request.args.get("limit", 50, type=int),
        )
        if fast is not None:
            return jsonify(fast)
    return _d._generic_channel_data("line")


@bp_channels.route("/api/channel/nostr")
def api_channel_nostr():
    """Issue #1088 Phase 5 fast-path on ``channel_messages``."""
    import dashboard as _d
    if _local_store_read_enabled():
        fast = _try_local_store_provider_messages(
            "nostr", request.args.get("limit", 50, type=int),
        )
        if fast is not None:
            return jsonify(fast)
    return _d._generic_channel_data("nostr")


@bp_channels.route("/api/channel/twitch")
def api_channel_twitch():
    """Issue #1088 Phase 5 fast-path on ``channel_messages``."""
    import dashboard as _d
    if _local_store_read_enabled():
        fast = _try_local_store_provider_messages(
            "twitch", request.args.get("limit", 50, type=int),
        )
        if fast is not None:
            return jsonify(fast)
    return _d._generic_channel_data("twitch")


@bp_channels.route("/api/channel/feishu")
def api_channel_feishu():
    """Issue #1088 Phase 5 fast-path on ``channel_messages``."""
    import dashboard as _d
    if _local_store_read_enabled():
        fast = _try_local_store_provider_messages(
            "feishu", request.args.get("limit", 50, type=int),
        )
        if fast is not None:
            return jsonify(fast)
    return _d._generic_channel_data("feishu")


@bp_channels.route("/api/channel/zalo")
def api_channel_zalo():
    """Issue #1088 Phase 5 fast-path on ``channel_messages``."""
    import dashboard as _d
    if _local_store_read_enabled():
        fast = _try_local_store_provider_messages(
            "zalo", request.args.get("limit", 50, type=int),
        )
        if fast is not None:
            return jsonify(fast)
    return _d._generic_channel_data("zalo")


@bp_channels.route("/api/channel/tlon")
def api_channel_tlon():
    """Issue #1088 Phase 5 fast-path on ``channel_messages``."""
    import dashboard as _d
    if _local_store_read_enabled():
        fast = _try_local_store_provider_messages(
            "tlon", request.args.get("limit", 50, type=int),
        )
        if fast is not None:
            return jsonify(fast)
    return _d._generic_channel_data("tlon")


@bp_channels.route("/api/channel/synology-chat")
def api_channel_synology_chat():
    """Issue #1088 Phase 5 fast-path on ``channel_messages``."""
    import dashboard as _d
    if _local_store_read_enabled():
        fast = _try_local_store_provider_messages(
            "synology-chat", request.args.get("limit", 50, type=int),
        )
        if fast is not None:
            return jsonify(fast)
    return _d._generic_channel_data("synology-chat")


@bp_channels.route("/api/channel/nextcloud-talk")
def api_channel_nextcloud_talk():
    """Issue #1088 Phase 5 fast-path on ``channel_messages``."""
    import dashboard as _d
    if _local_store_read_enabled():
        fast = _try_local_store_provider_messages(
            "nextcloud-talk", request.args.get("limit", 50, type=int),
        )
        if fast is not None:
            return jsonify(fast)
    return _d._generic_channel_data("nextcloud-talk")
