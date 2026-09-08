"""
Shared collapse for duplicate Brain-feed events.

One logical agent/user turn legitimately lands in DuckDB as SEVERAL rows:
the Claude-transcript copy (``cc-msg:*``, carries cost/tokens), the OpenClaw
v3 ``model.completed`` sibling, a tokens=0 ``delivery-mirror`` echo, and for
inbound channel messages both the gateway ``prompt.submitted`` and the
transcript ``user`` turn (the latter prefixed with a ``Conversation info
(untrusted metadata)`` JSON block the former lacks). They all carry distinct
ids, so id-level dedup can never merge them — content-window collapse is the
only honest answer.

Historically that collapse lived ONLY in ``routes/brain.py`` (the local
``/api/brain-history``), so the cloud blob built by
``sync._build_brain_events`` shipped every sibling and the hosted Brain feed
showed one reply three times (founder screenshot, 2026-07-31). This module is
the single implementation both readers call, parameterised by accessors so it
works on UI-shaped events and raw store rows alike.

Two passes, mirroring the battle-tested ``routes/brain.py`` logic:

* Pass 1 — same source, identical normalized text (>= ``MIN_DETAIL`` chars),
  120 s window: collapses assistant/model.completed/delivery-mirror siblings.
* Pass 2a — any source, identical normalized long text (>= ``MIN_DETAIL``),
  tight 10 s window: the #3924 double-ingest safety net.
* Pass 2b — same SESSION, identical normalized text of any length >=
  ``MIN_DETAIL_SHORT``, 10 s window: catches the short inbound message
  ("hello - I'm in a meeting" is 24 chars, under pass 2a's floor) that
  arrives via both the gateway tap and the transcript. Keyed per session so
  a short broadcast to several sessions is never merged.

Text keys are NORMALIZED first: leading ``<label> (untrusted metadata):``
fenced-JSON preambles are stripped and whitespace collapsed, so the
transcript copy and the raw gateway copy of the same message finally share a
key. Within a cluster the richest row wins (real message row over a
model.completed echo, then cost, then tokens).
"""
from __future__ import annotations

import datetime as _dt
import re

WINDOW_S = 120.0
CROSS_SRC_WINDOW_S = 10.0
MIN_DETAIL = 40
MIN_DETAIL_SHORT = 4

# "Conversation info (untrusted metadata):\n```json\n{...}\n```" and friends.
# Repeatedly stripped from the front so multi-block preambles normalize too.
_META_PREAMBLE_RE = re.compile(
    r"^\s*[^\n`]{0,80}\(untrusted metadata\):\s*```[a-zA-Z]*\s*.*?```\s*",
    re.DOTALL,
)

_PRIO = {
    "MESSAGE": 3, "ASSISTANT": 3, "AGENT": 3, "USER": 3, "RESULT": 3,
    "THINK": 2,
    "MODEL.COMPLETED": 1, "MODEL": 1, "PROMPT.SUBMITTED": 1,
}


def normalize_detail(text) -> str:
    """Comparison key for a brain event's text.

    Strips leading ``(untrusted metadata)`` fenced-JSON preambles (the
    transcript copy of a channel message carries one, the gateway copy does
    not) and collapses whitespace. Never raises; non-strings key as ""."""
    try:
        s = str(text or "")
        for _ in range(4):
            stripped = _META_PREAMBLE_RE.sub("", s, count=1)
            if stripped == s:
                break
            s = stripped
        return " ".join(s.split())
    except Exception:
        return ""


def type_priority(type_name) -> int:
    """Row-keeping priority for an event type (higher = richer)."""
    return _PRIO.get(str(type_name or "").upper(), 2)


def collapse_events(items, *, get_src, get_session, get_detail, get_time,
                    get_richness) -> list:
    """Return ``items`` with duplicate-content siblings collapsed.

    Accessors receive one item and return: ``get_src`` a per-source key,
    ``get_session`` a per-session key (may equal src), ``get_detail`` the
    raw text (normalized here), ``get_time`` an ISO-8601 string, and
    ``get_richness`` a sortable tuple (max wins). Order is preserved; on any
    accessor failure the item is kept. Never raises.
    """
    try:
        return _collapse(items or [], get_src, get_session, get_detail,
                         get_time, get_richness)
    except Exception:
        return list(items or [])


def _collapse(items, get_src, get_session, get_detail, get_time, get_richness):
    def _parse(it):
        try:
            ts = get_time(it) or ""
            return _dt.datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
        except Exception:
            return None

    def _safe(fn, it, default=""):
        try:
            return fn(it)
        except Exception:
            return default

    def _collapse_groups(groups, window_s, drop):
        for evs in groups.values():
            if len(evs) < 2:
                continue
            ordered = sorted(evs, key=lambda e: (_parse(e) or _dt.datetime.min))
            cluster = [ordered[0]]
            clusters = [cluster]
            for prev, cur in zip(ordered, ordered[1:]):
                tp, tc = _parse(prev), _parse(cur)
                if tp is None or tc is None or \
                        abs((tc - tp).total_seconds()) <= window_s:
                    cluster.append(cur)
                else:
                    cluster = [cur]
                    clusters.append(cluster)
            for cl in clusters:
                if len(cl) < 2:
                    continue
                best = max(cl, key=lambda e: _safe(get_richness, e, (0,)))
                for e in cl:
                    if e is not best:
                        drop.add(id(e))

    norm = {}
    for ev in items:
        norm[id(ev)] = normalize_detail(_safe(get_detail, ev))

    # Pass 1: same-source, substantial text, 120 s window.
    groups: dict = {}
    for ev in items:
        detail = norm[id(ev)]
        if len(detail) < MIN_DETAIL:
            continue
        groups.setdefault((_safe(get_src, ev), detail), []).append(ev)
    drop: set = set()
    _collapse_groups(groups, WINDOW_S, drop)

    # Pass 2a: cross-source, substantial text, tight 10 s window (#3924).
    cross: dict = {}
    for ev in items:
        if id(ev) in drop:
            continue
        detail = norm[id(ev)]
        if len(detail) < MIN_DETAIL:
            continue
        cross.setdefault(detail, []).append(ev)
    _collapse_groups(cross, CROSS_SRC_WINDOW_S, drop)

    # Pass 2b: same-SESSION short text, 10 s window — the gateway
    # prompt.submitted + transcript user copy of one inbound message.
    # Session-scoped so identical short texts in different sessions
    # (a broadcast "Done!") are never merged.
    short: dict = {}
    for ev in items:
        if id(ev) in drop:
            continue
        detail = norm[id(ev)]
        if not (MIN_DETAIL_SHORT <= len(detail) < MIN_DETAIL):
            continue
        sess = str(_safe(get_session, ev) or "")
        if not sess:
            continue
        short.setdefault((sess, detail), []).append(ev)
    _collapse_groups(short, CROSS_SRC_WINDOW_S, drop)

    if not drop:
        return list(items)
    return [ev for ev in items if id(ev) not in drop]


# ── Store-row adapter (used by sync._build_brain_events) ─────────────────────

def row_text(row) -> str:
    """Best-effort human text of a raw DuckDB event row, for keying only.

    Mirrors what the cloud's ``transformEvents`` / ``_v3_chat_message`` will
    eventually render: v3 completion/prompt text, Claude-transcript message
    content (string or text blocks), or a plain string payload."""
    try:
        data = row.get("data")
        if isinstance(data, str):
            return data
        if not isinstance(data, dict):
            return ""
        for key in ("completionText", "finalPromptText"):
            v = data.get(key)
            if isinstance(v, str) and v.strip():
                return v
        at = data.get("assistantTexts")
        if isinstance(at, list) and at and isinstance(at[0], str):
            return at[0]
        inner = data.get("data")
        if isinstance(inner, dict):
            for key in ("completionText", "finalPromptText"):
                v = inner.get(key)
                if isinstance(v, str) and v.strip():
                    return v
            iat = inner.get("assistantTexts")
            if isinstance(iat, list) and iat and isinstance(iat[0], str):
                return iat[0]
        msg = data.get("message")
        if isinstance(msg, dict):
            content = msg.get("content")
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                parts = [b.get("text") for b in content
                         if isinstance(b, dict) and b.get("type") == "text"
                         and isinstance(b.get("text"), str)]
                if parts:
                    return "\n".join(parts)
        content = data.get("content")
        if isinstance(content, str):
            return content
        return ""
    except Exception:
        return ""


def _bare_session(sid) -> str:
    """Canonical per-session key: drop any ``runtime:`` namespace prefix."""
    s = str(sid or "")
    return s.rsplit(":", 1)[-1]


def row_richness(row) -> tuple:
    """Keep-priority of a store row: message-class beats model.completed
    beats the tokens=0 delivery-mirror echo; then real cost wins (the
    Claude-transcript copy carries it, the gateway copies do not)."""
    try:
        data = row.get("data") if isinstance(row.get("data"), dict) else {}
        etype = str(row.get("event_type") or data.get("type") or "")
        prio = type_priority(etype)
        inner = data.get("data") if isinstance(data.get("data"), dict) else {}
        model = ""
        for d in (data, inner):
            m = d.get("modelId") or d.get("model")
            if isinstance(m, str) and m:
                model = m
                break
        if "delivery-mirror" in model:
            prio = 0
        cost = row.get("cost_usd") or 0.0
        try:
            cost = float(cost)
        except Exception:
            cost = 0.0
        return (prio, cost)
    except Exception:
        return (0, 0.0)


def collapse_duplicate_brain_rows(rows) -> list:
    """Collapse duplicate-content siblings in raw store rows (blob builder)."""
    return collapse_events(
        rows,
        get_src=lambda r: _bare_session(r.get("session_id")),
        get_session=lambda r: _bare_session(r.get("session_id")),
        get_detail=row_text,
        get_time=lambda r: r.get("ts") or "",
        get_richness=row_richness,
    )
