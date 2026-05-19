"""
clawmetry/outcome_classifier.py — Auto-label every session with an outcome.

Issue #1614 (OpenClaw blog "Four Pillars" — Outcome Measurement). Without
this, ClawMetry shows tokens + cost (activity) but can't answer the question
users actually care about: *"did this agent actually work?"*.

Pure functions only. Stateless. Tested independently from DuckDB.

Outcomes (5-way):
  success         — agent finished and nothing went wrong
  failed          — last billable turn surfaced an error OR last assistant
                    message contains structured failure markers
  escalated       — a human-approval gate fired for this session
                    (cross-references the ``approvals`` table — caller passes
                    the matching rows in)
  tool_call_stuck — a tool was invoked but its terminal result event never
                    arrived after ``TOOL_CALL_STUCK_SECONDS`` (default 120s).
                    Matches OpenClaw's ``blocked_tool_call`` failure class
                    (issue #1648) but works for any provider/adapter.
  cognitive_loop  — agent emitted N>=3 near-identical assistant messages
                    inside a 10-minute window with no new tool name and no
                    new file path between them (recursive self-validation,
                    issue #1706). Fires BEFORE ``ongoing`` because a still-
                    chattering session that's not making forward progress is
                    no longer healthily ongoing.
  ongoing         — session is still active (no terminal session.ended event
                    AND last event is recent, default <5 min)

Defaults are conservative on purpose (per memory
``feedback_synthetic_tests_missed_real_event_shape``): when uncertain we
err toward ``success`` rather than mark a working session as failed. False
negatives are worse than false positives here — users notice spurious
"failed" badges, they don't notice a slightly inflated success rate.

Confidence (0.0-1.0): how sure we are. Hard signals (explicit error flag,
matching approval row, terminal session.ended) → 0.9+. Heuristic signals
(string match on assistant text) → 0.55-0.75. The dashboard tile can hide
low-confidence ``failed`` labels from the headline number without dropping
them from the drill-down list.
"""

from __future__ import annotations

import re
import time
from typing import Any

# Outcome enum (frozen strings — these land in DuckDB and the wire API).
OUTCOME_SUCCESS = "success"
OUTCOME_FAILED = "failed"
OUTCOME_ESCALATED = "escalated"
OUTCOME_COGNITIVE_LOOP = "cognitive_loop"
OUTCOME_ONGOING = "ongoing"
OUTCOME_TOOL_CALL_STUCK = "tool_call_stuck"

VALID_OUTCOMES = frozenset({
    OUTCOME_SUCCESS, OUTCOME_FAILED, OUTCOME_ESCALATED,
    OUTCOME_TOOL_CALL_STUCK, OUTCOME_COGNITIVE_LOOP, OUTCOME_ONGOING,
})

# How long after the last event we still call a session "ongoing".
# 5 min matches the brain-stream / activity heuristic used elsewhere.
ONGOING_RECENT_SECONDS = 5 * 60

# Cognitive-loop detector tunables (issue #1706). Defaults match the
# OpenClaw blog post acceptance criteria: 3+ near-identical assistant
# messages in a 10-minute window, no new tool/file invoked in between.
COGNITIVE_LOOP_WINDOW_SECONDS = 600
COGNITIVE_LOOP_SIMILARITY_THRESHOLD = 0.85
COGNITIVE_LOOP_MIN_REPEATS = 3

# How long an unanswered tool invocation must sit before we classify the
# session as ``tool_call_stuck`` (#1648). 120s matches the OpenClaw
# ``blocked_tool_call`` triage default.
TOOL_CALL_STUCK_SECONDS = 120

# Default failure-text patterns (case-insensitive substring). Override via
# CLAWMETRY_OUTCOME_FAILURE_PATTERNS=pat1|pat2|... env var if needed.
# Conservative on purpose — every entry here is something a working agent
# would NOT normally say in its final turn.
_DEFAULT_FAILURE_PATTERNS = (
    "i couldn't complete",
    "i can't complete",
    "i was unable to",
    "i'm unable to",
    "failed to",
    "i don't have permission",
    "i don't have access",
    "operation aborted",
    "task failed",
    "unable to proceed",
)


def _failure_patterns() -> tuple[str, ...]:
    """Read failure patterns from env if set, else use the defaults."""
    import os
    raw = os.environ.get("CLAWMETRY_OUTCOME_FAILURE_PATTERNS")
    if not raw:
        return _DEFAULT_FAILURE_PATTERNS
    pats = tuple(p.strip().lower() for p in raw.split("|") if p.strip())
    return pats or _DEFAULT_FAILURE_PATTERNS


_ISO_TS_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")


def _iso_to_epoch(ts: Any) -> float:
    """Best-effort ISO-8601 → epoch seconds. Returns 0.0 on parse failure."""
    if not ts:
        return 0.0
    if isinstance(ts, (int, float)):
        # Already epoch. Heuristic: ms vs s by magnitude (>1e12 == ms).
        return float(ts) / 1000.0 if ts > 1e12 else float(ts)
    if not isinstance(ts, str):
        return 0.0
    try:
        # Python 3.9 doesn't accept the trailing 'Z' shortcut.
        from datetime import datetime
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
    except Exception:
        return 0.0


def _extract_text(data: Any) -> str:
    """Pull assistant-visible text out of an event's ``data`` blob.

    Tolerant of the three v3 shapes we've seen on real OpenClaw installs
    (per memory ``reference_openclaw_v3_event_types``):

      * ``data.message.content`` — legacy ``message`` envelope
      * ``data.finalPromptText`` — daemon-normalised prompt events
      * ``data.text`` / ``data.content`` — bare assistant turn

    Returns "" if no text is found (caller treats empty as "no signal").
    """
    if not isinstance(data, dict):
        return ""
    # message envelope: {"message": {"role": "assistant", "content": "..."}}
    msg = data.get("message")
    if isinstance(msg, dict):
        c = msg.get("content")
        if isinstance(c, str):
            return c
        if isinstance(c, list):
            # OpenAI/Anthropic block-list shape — join the text blocks.
            parts: list[str] = []
            for blk in c:
                if isinstance(blk, dict):
                    t = blk.get("text")
                    if isinstance(t, str):
                        parts.append(t)
            return " ".join(parts)
    for key in ("finalPromptText", "text", "content", "output"):
        v = data.get(key)
        if isinstance(v, str) and v:
            return v
    return ""


_TOOL_INVOCATION_EVENT_TYPES = ("tool.call", "toolcall", "tool_use", "tool_call")
_TOOL_RESULT_EVENT_TYPES = ("tool.result", "toolresult", "tool_result")
_TOOL_BLOCK_TYPES = ("toolCall", "tool_use")


def _iter_invocation_tool_call_ids(event: dict[str, Any]) -> list[str]:
    """Return every tool_call_id this event INVOKES.

    Three real shapes (matching the extraction logic in
    ``clawmetry/approvals.py`` and ``clawmetry/local_store.py``):

      * top-level ``tool.call``/``toolCall``/``tool_use`` event whose
        ``data`` IS the block ({id, name, arguments|input}).
      * assistant ``message`` event whose ``data.message.content[]`` (or
        flattened ``data.content[]``) contains toolCall/tool_use blocks.
      * Both branches: the id key is ``id`` (Anthropic/OpenClaw shape).

    Returns empty list for non-invocation events. IDs are best-effort
    strings; empty/missing IDs are skipped (we cannot match them to a
    result anyway).
    """
    out: list[str] = []
    et = (event.get("event_type") or "").lower()
    data = event.get("data")
    if not isinstance(data, dict):
        return out
    # Shape A: top-level tool-invocation event (data IS the block).
    if et in _TOOL_INVOCATION_EVENT_TYPES:
        cid = str(data.get("id") or "")
        if cid:
            out.append(cid)
        # Some emitters wrap the block under "tool" / "block".
        for k in ("tool", "block"):
            blk = data.get(k)
            if isinstance(blk, dict):
                cid = str(blk.get("id") or "")
                if cid:
                    out.append(cid)
    # Shape B: assistant message event with content blocks.
    blocks: list = []
    msg = data.get("message")
    if isinstance(msg, dict) and msg.get("role") in (None, "assistant"):
        c = msg.get("content")
        if isinstance(c, list):
            blocks = c
    elif data.get("role") in (None, "assistant") and isinstance(data.get("content"), list):
        blocks = data["content"]
    for blk in blocks:
        if isinstance(blk, dict) and blk.get("type") in _TOOL_BLOCK_TYPES:
            cid = str(blk.get("id") or "")
            if cid:
                out.append(cid)
    return out


def _iter_result_tool_call_ids(event: dict[str, Any]) -> list[str]:
    """Return every tool_call_id this event RESULT-CLOSES.

    Tolerant of the three v3 shapes seen on real installs:

      * top-level ``tool.result`` event with ``data.tool_call_id``
        (Anthropic/OpenClaw v3) or ``data.toolCallId`` (camelCase).
      * top-level ``tool.result`` event whose ``data.id`` IS the
        invocation id (some adapters reuse the field).
      * ``message`` event whose ``data.message.content[]`` has
        ``tool_result`` blocks carrying ``tool_use_id`` (Anthropic SDK).

    Empty result-id strings are dropped (we cannot match them).
    """
    out: list[str] = []
    et = (event.get("event_type") or "").lower()
    data = event.get("data")
    if not isinstance(data, dict):
        return out
    if et in _TOOL_RESULT_EVENT_TYPES:
        for key in ("tool_call_id", "toolCallId", "tool_use_id", "id"):
            v = data.get(key)
            if isinstance(v, str) and v:
                out.append(v)
                break
    # message-envelope shape: assistant or user message carrying tool_result
    # blocks (Anthropic Messages — tool_result blocks land in user turn).
    blocks: list = []
    msg = data.get("message")
    if isinstance(msg, dict):
        c = msg.get("content")
        if isinstance(c, list):
            blocks = c
    elif isinstance(data.get("content"), list):
        blocks = data["content"]
    for blk in blocks:
        if isinstance(blk, dict) and blk.get("type") in ("tool_result", "toolResult"):
            for key in ("tool_use_id", "tool_call_id", "toolCallId", "id"):
                v = blk.get(key)
                if isinstance(v, str) and v:
                    out.append(v)
                    break
    return out


def find_stuck_tool_calls(
    events: list[dict[str, Any]] | None,
    *,
    now: float | None = None,
    threshold_seconds: float = TOOL_CALL_STUCK_SECONDS,
) -> list[tuple[str, float]]:
    """Return ``[(tool_call_id, age_seconds), …]`` for invocations with no
    matching terminal result older than ``threshold_seconds``.

    Pure function; safe to call from any context. Tool calls without a
    parseable id are skipped (we cannot tell whether they got a result).
    Sorted by ``age_seconds`` descending — the stalest call first.
    """
    if now is None:
        now = time.time()
    invoked_ts: dict[str, float] = {}
    closed: set[str] = set()
    for ev in events or []:
        ev_ts = _iso_to_epoch(ev.get("ts"))
        for cid in _iter_invocation_tool_call_ids(ev):
            # Keep the EARLIEST invocation ts (a call only counts as stuck
            # from when it was first seen; duplicate emits don't reset it).
            prev = invoked_ts.get(cid)
            if prev is None or (ev_ts > 0 and ev_ts < prev):
                invoked_ts[cid] = ev_ts if ev_ts > 0 else (prev or 0.0)
        for cid in _iter_result_tool_call_ids(ev):
            closed.add(cid)
    stuck: list[tuple[str, float]] = []
    for cid, ts in invoked_ts.items():
        if cid in closed:
            continue
        if ts <= 0:
            # No parseable timestamp — cannot judge staleness. Skip.
            continue
        age = max(0.0, now - ts)
        if age >= threshold_seconds:
            stuck.append((cid, age))
    stuck.sort(key=lambda x: x[1], reverse=True)
    return stuck


def _is_tool_error(event: dict[str, Any]) -> bool:
    """True if this event represents a tool-call that surfaced an error.

    Covers three real-world shapes:
      * v3 ``tool.result`` with ``data.error == True`` or ``data.isError``
      * legacy ``toolResult`` with non-empty ``data.error_message``
      * status-coded results: ``data.status`` ∈ {"error", "failure"}
    """
    et = (event.get("event_type") or "").lower()
    if et not in ("tool.result", "toolresult", "tool_result"):
        return False
    data = event.get("data")
    if not isinstance(data, dict):
        return False
    if data.get("error") is True or data.get("isError") is True:
        return True
    if data.get("is_error") is True:
        return True
    em = data.get("error_message") or data.get("errorMessage")
    if isinstance(em, str) and em.strip():
        return True
    status = (data.get("status") or "").lower()
    if status in ("error", "failure", "failed"):
        return True
    return False


def _last_assistant_text(events: list[dict[str, Any]]) -> str:
    """Walk events newest-first, return the most recent assistant turn text.

    Considers both v3 ``model.completed``/``assistant`` and legacy ``message``
    (with role=assistant) shapes.
    """
    for ev in reversed(events):
        et = (ev.get("event_type") or "").lower()
        if et in ("model.completed", "assistant"):
            txt = _extract_text(ev.get("data"))
            if txt:
                return txt
        if et == "message":
            data = ev.get("data") or {}
            msg = data.get("message") if isinstance(data, dict) else None
            if isinstance(msg, dict) and (msg.get("role") == "assistant"):
                txt = _extract_text(data)
                if txt:
                    return txt
    return ""


def _last_event_age_seconds(events: list[dict[str, Any]], now: float) -> float:
    """Age of the newest event in seconds. Returns +inf if no events / no ts."""
    for ev in reversed(events):
        ts_epoch = _iso_to_epoch(ev.get("ts"))
        if ts_epoch > 0:
            return max(0.0, now - ts_epoch)
    return float("inf")


def _has_terminal_event(events: list[dict[str, Any]]) -> bool:
    """True if any event marks the session as terminally ended."""
    for ev in events:
        et = (ev.get("event_type") or "").lower()
        if et in ("session.ended", "sessionended", "session_end"):
            return True
    return False


# ── Cognitive-loop detection helpers (issue #1706) ─────────────────────────
#
# Pure functions, no DuckDB / IO. Cheap by design: token-level Jaccard on
# normalised last-200-chars of each assistant turn. Future work: swap in a
# tiny embedding model for true semantic similarity; the public API of
# ``find_cognitive_loops`` is the LLM-swap escape hatch.

_NUM_OR_UUID_RE = re.compile(r"\b[0-9a-f]{6,}\b|\d+")
_WHITESPACE_RE = re.compile(r"\s+")


def _normalize_for_similarity(text: str) -> str:
    """Lowercase, strip digits + hex/UUID runs, collapse whitespace, tail 200.

    Goal: two assistant turns that say the same thing modulo timestamps,
    request IDs, or other numeric noise normalise to the same string so the
    Jaccard score actually fires. Last 200 chars keeps cost bounded.
    """
    s = (text or "").lower().strip()
    s = _NUM_OR_UUID_RE.sub(" ", s)
    s = _WHITESPACE_RE.sub(" ", s).strip()
    return s[-200:]


def _token_jaccard(a: str, b: str) -> float:
    """Token-level Jaccard similarity on whitespace-split tokens. 0.0..1.0."""
    ta = set(a.split())
    tb = set(b.split())
    if not ta and not tb:
        return 1.0
    if not ta or not tb:
        return 0.0
    union = len(ta | tb)
    return len(ta & tb) / union if union else 0.0


def _tool_uses_in_event(event: dict[str, Any]) -> list[tuple[str, str]]:
    """Return [(tool_name, file_path_or_empty), ...] for an assistant event.

    Looks at ``data.message.content[*]`` for entries with ``type=tool_use``
    (Anthropic block-list shape). Returns [] if none — e.g. ``model.completed``
    on a non-Anthropic provider, or a pure-text turn.
    """
    out: list[tuple[str, str]] = []
    data = event.get("data") or {}
    if not isinstance(data, dict):
        return out
    msg = data.get("message")
    if not isinstance(msg, dict):
        return out
    content = msg.get("content")
    if not isinstance(content, list):
        return out
    for blk in content:
        if not isinstance(blk, dict):
            continue
        if blk.get("type") != "tool_use":
            continue
        name = str(blk.get("name") or "").strip()
        ipt = blk.get("input") or {}
        path = ""
        if isinstance(ipt, dict):
            for k in ("file_path", "path", "filename", "filepath"):
                v = ipt.get(k)
                if isinstance(v, str) and v:
                    path = v
                    break
        out.append((name, path))
    return out


def _session_has_cognitive_loop(
    sess_events: list[dict[str, Any]],
    *,
    window_seconds: int,
    similarity_threshold: float,
    min_repeats: int,
) -> bool:
    """True if this single session's assistant turns are spinning in place.

    Algorithm: for each anchor assistant message, slide forward through the
    time window collecting near-identical follow-ups. Bail the moment a new
    tool name or new file path appears (that's forward progress, not a
    loop). Fire if the anchor accumulates >= min_repeats matches.
    """
    try:
        sess_events = sorted(sess_events, key=lambda e: e.get("ts") or "")
    except Exception:
        pass
    items: list[dict[str, Any]] = []
    for ev in sess_events:
        et = (ev.get("event_type") or "").lower()
        if et not in ("assistant", "message", "model.completed"):
            continue
        txt = _extract_text(ev.get("data"))
        if not txt:
            continue
        items.append({
            "ts": _iso_to_epoch(ev.get("ts")),
            "norm": _normalize_for_similarity(txt),
            "tools": _tool_uses_in_event(ev),
        })
    if len(items) < min_repeats:
        return False
    for i, anchor in enumerate(items):
        matches = 1
        seen_tools = {n for n, _ in anchor["tools"] if n}
        seen_paths = {p for _, p in anchor["tools"] if p}
        for j in range(i + 1, len(items)):
            cand = items[j]
            if anchor["ts"] and cand["ts"] and (
                cand["ts"] - anchor["ts"] > window_seconds
            ):
                break
            cand_tools = {n for n, _ in cand["tools"] if n}
            cand_paths = {p for _, p in cand["tools"] if p}
            if (cand_tools - seen_tools) or (cand_paths - seen_paths):
                # Forward progress: a new tool or file appeared. Not stuck.
                break
            if _token_jaccard(anchor["norm"], cand["norm"]) >= similarity_threshold:
                matches += 1
                seen_tools |= cand_tools
                seen_paths |= cand_paths
                if matches >= min_repeats:
                    return True
    return False


def find_cognitive_loops(
    events: list[dict[str, Any]] | None,
    *,
    now: float | None = None,
    window_seconds: int = COGNITIVE_LOOP_WINDOW_SECONDS,
    similarity_threshold: float = COGNITIVE_LOOP_SIMILARITY_THRESHOLD,
    min_repeats: int = COGNITIVE_LOOP_MIN_REPEATS,
) -> list[str]:
    """Return session_ids that exhibit a cognitive loop.

    A cognitive loop = ``min_repeats`` near-identical assistant messages
    inside ``window_seconds`` AND no new tool name AND no new file path
    invoked between them. Caps at 200 sessions scanned per call so it
    never blows up on large DuckDB exports.

    ``now`` is accepted for API symmetry with ``classify_session`` (and
    leaves room for a future "only loops in the last N hours" filter); it
    is currently unused because the detection is purely intra-session.
    """
    del now  # reserved for future windowing
    by_session: dict[str, list[dict[str, Any]]] = {}
    for ev in events or []:
        sid = ev.get("session_id") or ""
        if not sid:
            continue
        if sid not in by_session and len(by_session) >= 200:
            continue  # cap fan-out
        by_session.setdefault(sid, []).append(ev)
    flagged: list[str] = []
    for sid, sess_events in by_session.items():
        if _session_has_cognitive_loop(
            sess_events,
            window_seconds=window_seconds,
            similarity_threshold=similarity_threshold,
            min_repeats=min_repeats,
        ):
            flagged.append(sid)
    return flagged


def classify_session(
    events: list[dict[str, Any]] | None,
    session_meta: dict[str, Any] | None = None,
    *,
    approvals: list[dict[str, Any]] | None = None,
    now: float | None = None,
) -> tuple[str, float]:
    """Return ``(outcome, confidence)`` for one session.

    Args:
      events: list of event dicts (oldest-first ideally — we sort if not).
        Each dict needs ``event_type`` and ``ts``; ``data`` optional.
      session_meta: typed-session row (from ``sessions`` table) — used for
        ``status``, ``ended_at``, ``last_active_at`` hints. Optional.
      approvals: rows from ``approvals`` table scoped to this session. Any
        row with status != "pending" means a human was looped in →
        ``escalated``.
      now: clock override for tests. Defaults to ``time.time()``.

    Confidence:
      * 1.0   — explicit ``status`` field on session row
      * 0.95  — escalated (approval row exists)
      * 0.9   — tool.result error on the tail
      * 0.85  — session.ended terminal marker present
      * 0.8   — tool_call_stuck (invocation older than threshold, no result)
      * 0.8   — cognitive loop detected (issue #1706)
      * 0.75  — last-turn text matched a failure pattern
      * 0.6   — ongoing (recent activity, no terminal event)
      * 0.5   — fell through to "success" default (conservative)
    """
    if now is None:
        now = time.time()
    evs = list(events or [])
    # Some callers (query_events with default ORDER BY ts DESC) hand us
    # newest-first; sort defensively so terminal-event detection + tail
    # scans work either way.
    try:
        evs.sort(key=lambda e: e.get("ts") or "")
    except Exception:
        pass

    meta = session_meta or {}

    # ── 1. Explicit terminal status on the session row ───────────────
    # Some adapters write a typed status into the sessions table directly
    # (e.g. "completed"/"errored"/"abandoned"). Trust it when present.
    raw_status = (meta.get("status") or "").lower().strip()
    if raw_status in ("errored", "error", "failed", "crashed"):
        return OUTCOME_FAILED, 1.0
    if raw_status == "abandoned":
        # Treat as failed-by-omission with medium confidence.
        return OUTCOME_FAILED, 0.7

    # ── 2. Escalated — approval row exists for this session ─────────
    # Any matching approval row (pending OR resolved) means a human was
    # required at some point. That's the "needed human" signal users care
    # about, regardless of whether they ultimately approved or denied.
    if approvals:
        for a in approvals:
            if a:  # ignore None / empty
                return OUTCOME_ESCALATED, 0.95

    # ── 2.5. Tool-call stuck — invocation has no terminal result ──────
    # Slots ABOVE cognitive_loop (issue #1706 requested this per comment).
    # Runs BEFORE the "ongoing" gate so a session that's still receiving
    # heartbeat-ish events but has a dead tool call is correctly flagged.
    # (#1648 — matches OpenClaw's ``blocked_tool_call`` triage class.)
    terminal = _has_terminal_event(evs) or bool(meta.get("ended_at"))
    if not terminal:
        stuck = find_stuck_tool_calls(evs, now=now)
        if stuck:
            return OUTCOME_TOOL_CALL_STUCK, 0.8

    # ── 3. Cognitive loop — recursive self-validation (issue #1706) ─
    # Runs BEFORE ongoing because a still-chattering session whose
    # assistant keeps emitting the same text is no longer healthy ongoing.
    if _session_has_cognitive_loop(
        evs,
        window_seconds=COGNITIVE_LOOP_WINDOW_SECONDS,
        similarity_threshold=COGNITIVE_LOOP_SIMILARITY_THRESHOLD,
        min_repeats=COGNITIVE_LOOP_MIN_REPEATS,
    ):
        return OUTCOME_COGNITIVE_LOOP, 0.8

    # ── 4. Ongoing — no terminal marker AND recent activity ─────────
    if not terminal:
        age = _last_event_age_seconds(evs, now)
        if age < ONGOING_RECENT_SECONDS:
            return OUTCOME_ONGOING, 0.6
        # If session row says it's running but events are stale, fall
        # through to outcome detection rather than mislabelling as
        # ongoing. Caller can decide whether to surface "stale" badge.

    # ── 5. Failed — last tool.result was an error ───────────────────
    # Scan from the tail back through up to 5 events; an error in the
    # very last billable step is the strongest "failed" signal.
    for ev in reversed(evs[-5:]):
        if _is_tool_error(ev):
            return OUTCOME_FAILED, 0.9

    # ── 6. Failed — last assistant text matches a failure pattern ──
    text = _last_assistant_text(evs).lower()
    if text:
        for pat in _failure_patterns():
            if pat in text:
                return OUTCOME_FAILED, 0.75

    # ── 7. Default: success ─────────────────────────────────────────
    # Conservative by design: when uncertain we say success rather than
    # plaster the dashboard with false failures. The confidence value
    # lets the UI distinguish "high-confidence success" (terminal event
    # with no errors) from "best-guess success" (heuristic fallthrough).
    if terminal:
        return OUTCOME_SUCCESS, 0.85
    return OUTCOME_SUCCESS, 0.5


def aggregate_outcomes(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Roll up a list of per-session outcome rows into the dashboard tile.

    Input row shape: ``{"outcome": "success" | "failed" | ..., ...}``.
    Output matches the ``/api/outcomes`` contract:

        {
            "total":           247,
            "success":         220,
            "failed":           18,
            "escalated":         9,
            "cognitive_loop":    0,
            "ongoing":           0,
            "tool_call_stuck":   0,
            "success_rate":   0.880,   # success / (success + failed + loop + stuck)
            "needed_human_rate": 0.036,  # escalated / total
        }

    ``success_rate`` deliberately excludes ``ongoing`` (still in flight) and
    ``escalated`` (different category — a successful human-in-the-loop run
    isn't a failure of the agent). ``cognitive_loop`` and ``tool_call_stuck``
    ARE in the denominator because both are terminal failure modes: the agent
    wasted budget without progress (loop) or a tool never returned (stuck).
    Matches industry convention for autonomous-task success metrics.
    """
    counts = {
        OUTCOME_SUCCESS: 0,
        OUTCOME_FAILED: 0,
        OUTCOME_ESCALATED: 0,
        OUTCOME_COGNITIVE_LOOP: 0,
        OUTCOME_ONGOING: 0,
        OUTCOME_TOOL_CALL_STUCK: 0,
    }
    for r in rows or []:
        o = (r or {}).get("outcome") or OUTCOME_SUCCESS
        if o in counts:
            counts[o] += 1
        else:
            counts[OUTCOME_SUCCESS] += 1
    total = sum(counts.values())
    finished = (
        counts[OUTCOME_SUCCESS]
        + counts[OUTCOME_FAILED]
        + counts[OUTCOME_COGNITIVE_LOOP]
        + counts[OUTCOME_TOOL_CALL_STUCK]
    )
    success_rate = (counts[OUTCOME_SUCCESS] / finished) if finished else 0.0
    needed_human = (counts[OUTCOME_ESCALATED] / total) if total else 0.0
    return {
        "total": total,
        "success": counts[OUTCOME_SUCCESS],
        "failed": counts[OUTCOME_FAILED],
        "escalated": counts[OUTCOME_ESCALATED],
        "cognitive_loop": counts[OUTCOME_COGNITIVE_LOOP],
        "ongoing": counts[OUTCOME_ONGOING],
        "tool_call_stuck": counts[OUTCOME_TOOL_CALL_STUCK],
        "success_rate": round(success_rate, 4),
        "needed_human_rate": round(needed_human, 4),
    }
