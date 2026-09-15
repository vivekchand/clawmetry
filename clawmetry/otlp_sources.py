"""Which source records a tool call reported over OTLP (REQ-OBS-OTG-001).

AC-OBS-OTG-001.3 and AC-OBS-OTG-001.8. A runtime can describe one tool call
three ways: the daemon reads it from the transcript on disk, the runtime
exports it as a log record (``/v1/logs``), and it exports it as a trace span
(``/v1/traces``). Counting more than one copy doubles every trajectory
threshold and pages twice for one action, so exactly one is recorded, by a
fixed precedence:

    machine observation  >  trace span  >  log record

* **Machine observation.** A session the daemon already observes drops OTLP
  copies of ``tool_call`` / ``tool_result`` / ``llm_call`` (the transcript is
  strictly richer). Other OTLP facts still attach to it.
* **A call both signals identify.** When a tool event carries a call id
  (:data:`CALL_ID_KEYS`), its event id is derived from the session and that
  id (:func:`call_event_id`), so the log copy and the span copy name the same
  row. The span wins whichever arrives first: a log copy arriving after it is
  skipped, and a span arriving after the log copy replaces that row's
  payload. Identity, time and chain position are kept, because the
  tamper-evident chain hashes those and not the payload.
* **A call only one signal reports** is always recorded.
* **A call with no call id** cannot be matched call by call, so the first
  signal to report that session's tool calls keeps the session and the other
  signal's copies are skipped. This is the one case that depends on arrival
  order.

The whole event half of an OTLP batch runs under :data:`BATCH_LOCK`, so two
exports arriving together are decided in turn rather than both passing the
check. ``LocalStore.put_otlp_batch`` delegates to :func:`write_events`.
"""
from __future__ import annotations

import hashlib
import json
import logging
import threading
from typing import Any, Iterable, Optional

log = logging.getLogger("clawmetry.otlp_sources")

CALL_EVENT_ID_PREFIX = "otlp:call:"
TRACE_SPAN_ID_PREFIX = "otlp:span:"
TOOL_EVENT_TYPES = ("tool_call", "tool_result")
# Event types the daemon's transcript read also produces.
DAEMON_DUPLICATE_TYPES = frozenset({"tool_call", "tool_result", "llm_call"})
SIGNAL_RANK = {"log": 1, "trace": 2}

# The GenAI semconv name first, then the spellings runtimes ship
# (``call_id`` on Codex log records, ``tool_use_id`` on Anthropic shapes).
CALL_ID_KEYS = (
    "gen_ai.tool.call.id", "tool.call.id", "tool_call_id", "call_id",
    "tool_use_id",
)

BATCH_LOCK = threading.RLock()


def call_id_from(attrs: Any) -> Optional[str]:
    """The call id an OTLP record or span carries, or None."""
    if not isinstance(attrs, dict):
        return None
    for key in CALL_ID_KEYS:
        value = attrs.get(key)
        if value not in (None, ""):
            text = str(value).strip()
            if text:
                return text[:256]
    return None


def call_event_id(session_id: Any, call_id: str, phase: str) -> str:
    """The event id both signals use for one call: ``otlp:call:<d>:<phase>``.

    ``phase`` is ``call`` or ``result``. The digest keeps an exporter-chosen
    call id out of the primary key's shape and scopes it to its session.
    """
    digest = hashlib.sha256(
        (str(session_id) + "\x00" + str(call_id)).encode("utf-8", "replace")
    ).hexdigest()[:32]
    return "%s%s:%s" % (CALL_EVENT_ID_PREFIX, digest, phase)


def _data(ev: dict) -> dict:
    data = ev.get("data")
    if isinstance(data, (bytes, bytearray, memoryview)):
        data = bytes(data).decode("utf-8", "replace")
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except (ValueError, TypeError):
            data = {}
    return data if isinstance(data, dict) else {}


def signal_of(ev: dict) -> str:
    """``trace`` or ``log``: the stamp first, the id shape for older rows."""
    sig = str(_data(ev).get("_otlp_signal") or "")
    if sig in SIGNAL_RANK:
        return sig
    return "trace" if str(ev.get("id") or "").startswith(TRACE_SPAN_ID_PREFIX) else "log"


def _is_keyed(event_id: str) -> bool:
    return event_id.startswith(CALL_EVENT_ID_PREFIX)


def _chunks(items: list, size: int = 500) -> Iterable[list]:
    for off in range(0, len(items), size):
        yield items[off:off + size]


def _probe(store, sessions: list, keyed_ids: list) -> tuple:
    """What the store already holds for these sessions and call ids.

    Returns ``(owned_by_daemon, per_session, stored_signal_by_id)`` where
    ``per_session[sid] = {"log": {"any", "unkeyed"}, "trace": {...}}``.
    """
    owned: set = set()
    per_session: dict = {}
    by_id: dict = {}
    for chunk in _chunks(sessions):
        marks = ", ".join(["?"] * len(chunk))
        try:
            rows = store._fetch(
                "SELECT DISTINCT session_id FROM events "
                f"WHERE session_id IN ({marks}) AND id NOT LIKE 'otlp:%'",
                list(chunk),
            )
            owned.update(str(r[0]) for r in rows if r and r[0])
        except Exception:
            log.warning("otlp events: ownership probe failed", exc_info=True)
        try:
            rows = store._fetch(
                "SELECT session_id, id, data FROM events WHERE id LIKE 'otlp:%' "
                "AND event_type IN ('tool_call', 'tool_result') "
                f"AND session_id IN ({marks})",
                list(chunk),
            )
        except Exception:
            log.warning("otlp events: signal probe failed", exc_info=True)
            rows = []
        for sid, eid, data in rows:
            ev = {"id": eid, "data": _decode_blob(data)}
            sig = signal_of(ev)
            slot = per_session.setdefault(str(sid), {}).setdefault(
                sig, {"any": False, "unkeyed": False})
            slot["any"] = True
            if not _is_keyed(str(eid)):
                slot["unkeyed"] = True
    for chunk in _chunks(keyed_ids):
        marks = ", ".join(["?"] * len(chunk))
        try:
            for eid, data in store._fetch(
                f"SELECT id, data FROM events WHERE id IN ({marks})", list(chunk),
            ):
                by_id[str(eid)] = signal_of({"id": eid, "data": _decode_blob(data)})
        except Exception:
            log.warning("otlp events: call-id probe failed", exc_info=True)
    return owned, per_session, by_id


def _decode_blob(data: Any) -> Any:
    """``events.data`` as stored: JSON bytes, possibly compressed."""
    if not isinstance(data, (bytes, bytearray, memoryview)):
        return data
    raw = bytes(data)
    try:
        from clawmetry import ccr as _ccr
        raw = _ccr.maybe_decompress(raw)
    except Exception:
        pass
    if isinstance(raw, (bytes, bytearray)):
        return bytes(raw).decode("utf-8", "replace")
    return raw


def decide(ev: dict, owned: set, per_session: dict, by_id: dict) -> str:
    """``ingest``, ``replace`` or a ``skip_*`` reason for one event.

    Updates the probe state with the decision, so later events in the same
    batch see it.
    """
    sid = str(ev.get("session_id") or "")
    ev_type = str(ev.get("event_type") or "")
    if sid and sid in owned and ev_type in DAEMON_DUPLICATE_TYPES:
        return "skip_daemon"
    if ev_type not in TOOL_EVENT_TYPES or not sid:
        return "ingest"
    eid = str(ev.get("id") or "")
    sig = signal_of(ev)
    other = "log" if sig == "trace" else "trace"
    state = per_session.setdefault(sid, {})
    mine = state.setdefault(sig, {"any": False, "unkeyed": False})
    theirs = state.get(other) or {"any": False, "unkeyed": False}

    if _is_keyed(eid):
        # The other signal reported this session without call ids: nothing
        # can be matched call by call, so that signal keeps the session.
        if theirs["unkeyed"]:
            return "skip_other_signal"
        stored = by_id.get(eid)
        if stored is None:
            decision = "ingest"
        elif SIGNAL_RANK.get(sig, 0) > SIGNAL_RANK.get(stored, 0):
            decision = "replace"
        else:
            return "skip_duplicate"
        by_id[eid] = sig
        mine["any"] = True
        return decision

    # No call id: first signal to report the session keeps it.
    if theirs["any"]:
        return "skip_other_signal"
    mine["any"] = True
    mine["unkeyed"] = True
    return "ingest"


def replace_payload(store, ev: dict) -> bool:
    """Overwrite one stored event's payload with ``ev``'s, keeping its row.

    Only ``data`` and the columns derived from it change. ``id``, identity,
    ``ts``, ``created_at`` and the chain columns are left alone: the chain
    hashes identity and time, so it stays valid. Redacted like any ingest.
    """
    try:
        from clawmetry import local_store as _ls
        from clawmetry import redaction as _r
        event = _r.redact_event(ev) if not _r._disabled() else ev
        row = _ls._event_to_row(event)
        # (id, agent_type, node_id, agent_id, session_id, workspace_id,
        #  event_type, ts, data, cost, tokens, model, created_at,
        #  runtime_kind, role, block_kind, tool_name, is_error)
        with store._write_lock:
            store._conn.execute(
                "UPDATE events SET data = ?, cost_usd = ?, token_count = ?, "
                "model = ?, role = ?, block_kind = ?, tool_name = ?, is_error = ? "
                "WHERE id = ?",
                [row[8], row[9], row[10], row[11], row[14], row[15], row[16],
                 row[17], row[0]],
            )
        return True
    except Exception:
        log.warning("otlp events: payload replacement failed", exc_info=True)
        return False


def write_events(store, events: Optional[list]) -> dict:
    """The event half of ``LocalStore.put_otlp_batch``. Never raises per row.

    Applies the content profile, the precedence above, ingests, replaces and
    flushes, all under :data:`BATCH_LOCK`.
    """
    counts = {
        "events": 0,
        "events_skipped_daemon_owned": 0,
        "events_skipped_other_signal": 0,
        "events_skipped_duplicate": 0,
        "events_replaced_by_trace": 0,
    }
    events = [ev for ev in (events or []) if isinstance(ev, dict)]
    if not events:
        return counts
    try:
        from clawmetry import otlp_content as _oc
        events = [_oc.minimise_event(ev) for ev in events]
    except Exception:
        log.warning("otlp events: content profile not applied", exc_info=True)

    with BATCH_LOCK:
        # Rows still in the ingest ring are invisible to the probe below.
        try:
            store._flush_now()
        except Exception:
            log.debug("otlp events: pre-probe flush failed", exc_info=True)
        sessions = sorted({str(ev.get("session_id")) for ev in events
                           if ev.get("session_id")})
        keyed = sorted({str(ev.get("id")) for ev in events
                        if _is_keyed(str(ev.get("id") or ""))})
        owned, per_session, by_id = _probe(store, sessions, keyed)
        replacements: list = []
        for ev in events:
            decision = decide(ev, owned, per_session, by_id)
            if decision == "skip_daemon":
                counts["events_skipped_daemon_owned"] += 1
            elif decision == "skip_other_signal":
                counts["events_skipped_other_signal"] += 1
            elif decision == "skip_duplicate":
                counts["events_skipped_duplicate"] += 1
            elif decision == "replace":
                replacements.append(ev)
            else:
                try:
                    store.ingest(ev)
                    counts["events"] += 1
                except Exception:
                    log.warning("otlp events: row rejected", exc_info=True)
        flush_failed = False
        if counts["events"] or replacements:
            # Flush before replacing: a span replacing a log copy that is
            # still in the ring would update nothing.
            try:
                store._flush_now()
            except Exception:
                flush_failed = True
                log.warning("otlp events: flush failed", exc_info=True)
        for ev in replacements:
            if replace_payload(store, ev):
                counts["events_replaced_by_trace"] += 1
        counts["events_flush_failed"] = flush_failed
    return counts
