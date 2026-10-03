"""Opt-in capability-gap export (#5412).

ClawMetry already records when an agent asked for something it could not
get: a tool that does not exist here, a permission check that refused the
call, a rate limit or timeout, a budget boundary the enforcement proxy
closed. This module maps those recorded signals to the MIX ``E01``..``E08``
demand taxonomy and, when an operator asks for it, appends each one as a
JSONL line a local consumer can read. Nothing is sent anywhere. The export
is off unless ``CLAWMETRY_CAPGAP_EXPORT_DIR`` names a directory.

What a record carries: the taxonomy code, the session id, the runtime, the
tool name, the matched marker from the fixed lists below, an HTTP status
when the event carried one, the event id and its timestamp. What it never
carries: prompts, task text, tool arguments, result bodies, exception text,
credentials or transcript content. The marker is one of OUR strings, never a
slice of the agent's output.

Only four codes are emitted today. ``E03``, ``E04``, ``E06`` and ``E07`` are
declared so a consumer can rely on the vocabulary, and are documented as
not emitted until an event shape maps to them without guessing. A
conservative exporter that stays silent beats one that invents demand.

Everything here is pure or file-mediated. The daemon calls
:meth:`Exporter.observe_events` from its detector pass and
:meth:`Exporter.flush` once per tick; ``GET /api/capability-gaps`` runs
:func:`classify_events` over recent store rows on demand, export or not.
"""
from __future__ import annotations

import json
import logging
import os
import re
import time
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple

from clawmetry import detectors as _det

log = logging.getLogger("clawmetry.capability_gaps")

#: Environment variable that turns the JSONL export on. Its value is the
#: directory the files are written to. Unset or blank means off.
EXPORT_DIR_ENV = "CLAWMETRY_CAPGAP_EXPORT_DIR"

#: File names inside the export directory.
EXPORT_FILENAME = "capability_gaps.jsonl"
SEEN_FILENAME = "capability_gaps.seen.json"

#: Record schema version. Bumped when a field changes meaning.
RECORD_VERSION = 1

#: How many ``event_id::code`` keys the dedup memory keeps across daemon
#: restarts. The detector window is 200 events per active session, so this
#: covers many ticks of many sessions before the oldest key is forgotten.
SEEN_CAP = 5000

TAXONOMY: Dict[str, str] = {
    "E01_NO_MATCH": "The agent asked for a tool or capability that does not exist here.",
    "E02_NO_ACCESS": "An authentication or permission check refused the call.",
    "E03_NO_FIT": "The call did not fit the schema or a policy.",
    "E04_NEED_ALTERNATIVE": "The agent asked for a fallback.",
    "E05_CAPACITY_GAP": "A rate limit, timeout, context limit or capacity ceiling stopped the call.",
    "E06_RIGHTS_GAP": "A licensing or rights check refused the call.",
    "E07_EVIDENCE_GAP": "Provenance or verification was missing.",
    "E08_CAPITAL_NEED": "An explicit budget or billing boundary stopped the call.",
}

#: Codes the classifier emits. The rest are declared only.
MAPPED_CODES: Tuple[str, ...] = (
    "E01_NO_MATCH", "E02_NO_ACCESS", "E05_CAPACITY_GAP", "E08_CAPITAL_NEED",
)

#: The fixed field set of a record. Tests pin it so a new field is a
#: deliberate change, never a leak.
RECORD_FIELDS: Tuple[str, ...] = (
    "v", "code", "taxonomy", "ts", "observed_at", "session_id", "runtime",
    "tool", "source", "marker", "http_status", "event_id",
)

# ── Marker tables ────────────────────────────────────────────────────────────
# Lower-case substrings matched against the lower-cased failure text. Each
# marker is also what the record reports, so a consumer sees which rule
# fired and never the text it fired on. Order inside a tuple is the order
# of reporting when several match.

E08_MARKERS: Tuple[str, ...] = (
    "budget_exceeded", "budget exceeded", "budget reached",
    "credit balance is too low", "insufficient credits", "insufficient funds",
    "insufficient balance", "payment required", "billing_hard_limit_reached",
    "exceeded your current quota", "check your plan and billing",
)
E08_STATUSES = frozenset({402})
E08_ERROR_TYPES = frozenset({"budget_exceeded", "insufficient_funds",
                             "billing_hard_limit_reached", "payment_required"})

E05_MARKERS: Tuple[str, ...] = (
    "timed out", "timeout", "deadline exceeded", "context_length_exceeded",
    "context length", "maximum context", "prompt is too long",
    "too many tokens", "request too large", "capacity", "overloaded",
    "rate limit", "rate_limit", "too many requests", "quota exceeded",
    "resource_exhausted",
)
E05_ERROR_TYPES = frozenset({"timeout", "deadline_exceeded",
                             "context_length_exceeded", "overloaded_error",
                             "rate_limit_error", "rate_limit_exceeded",
                             "resource_exhausted", "capacity"})

E02_MARKERS: Tuple[str, ...] = (
    "permission denied", "access denied", "operation not permitted",
    "not authorized", "unauthorized", "unauthorised", "forbidden",
    "authentication failed", "authentication_error", "permission_error",
    "invalid api key", "invalid_api_key", "invalid x-api-key",
    "api key not valid", "requires authentication", "login required",
    "has been denied", "denied by user", "user denied", "user declined",
    "doesn't want to proceed", "does not want to proceed",
    "blocked by policy", "eacces",
)
E02_STATUSES = frozenset({401, 403})
E02_ERROR_TYPES = frozenset({"authentication_error", "permission_error",
                             "permission_denied", "unauthorized", "forbidden",
                             "access_denied", "invalid_api_key"})

E01_MARKERS: Tuple[str, ...] = (
    "command not found", "unknown tool", "tool not found", "no such tool",
    "not a known tool", "no such command", "unknown command",
    "is not recognized as an internal or external command",
    "no module named", "modulenotfounderror", "cannot find module",
    "could not find a version that satisfies", "executable file not found",
    "not installed", "unknown skill", "skill not found", "no such mcp server",
    "unknown mcp server", "model not found", "does not exist or you do not have access",
)
E01_ERROR_TYPES = frozenset({"tool_not_found", "unknown_tool", "invalid_tool",
                             "unknown_tool_name", "not_found_error",
                             "model_not_found", "command_not_found"})

_RULES: Tuple[Tuple[str, Tuple[str, ...], frozenset, frozenset], ...] = (
    ("E08_CAPITAL_NEED", E08_MARKERS, E08_STATUSES, E08_ERROR_TYPES),
    ("E05_CAPACITY_GAP", E05_MARKERS, frozenset(_det._RATE_LIMIT_STATUSES) | frozenset({408, 504}),
     E05_ERROR_TYPES),
    ("E02_NO_ACCESS", E02_MARKERS, E02_STATUSES, E02_ERROR_TYPES),
    ("E01_NO_MATCH", E01_MARKERS, frozenset({404}), E01_ERROR_TYPES),
)

_API_ERROR_TYPES = frozenset(_det._API_ERROR_TYPES)
_TOOL_RESULT_TYPES = frozenset(_det._TOOL_RESULT_TYPES)
_TOOL_NAME_MAX = 120
_MARKER_429 = re.compile(r"(?<![\w.])429(?![\w])")


# ── Pure helpers ─────────────────────────────────────────────────────────────

def export_dir() -> str:
    """The configured export directory, or ``""`` when the export is off."""
    return (os.environ.get(EXPORT_DIR_ENV) or "").strip()


def export_enabled() -> bool:
    return bool(export_dir())


def _error_holder(data: dict) -> dict:
    err = data.get("error")
    if isinstance(err, dict):
        return err
    msg = data.get("message")
    if isinstance(msg, dict) and isinstance(msg.get("error"), dict):
        return msg["error"]
    return {}


def _error_type(data: dict) -> str:
    err = _error_holder(data)
    for k in ("type", "code", "kind", "name"):
        v = err.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip().lower()
    v = data.get("code")
    if isinstance(v, str) and v.strip():
        return v.strip().lower()
    return ""


def _failure_text(data: dict) -> str:
    """Lower-cased text the markers are matched against. The text itself is
    never stored or returned past this module."""
    parts: List[str] = []
    try:
        err = data.get("error")
        if isinstance(err, str) and err.strip():
            parts.append(err[:2000])
        elif isinstance(err, dict):
            for k in ("type", "code", "message", "detail", "reason"):
                v = err.get(k)
                if isinstance(v, str) and v.strip():
                    parts.append(v[:1000])
        for k in ("message", "reason", "detail"):
            v = data.get(k)
            if isinstance(v, str) and v.strip():
                parts.append(v[:1000])
        base = _det._result_text(data)
        if base:
            parts.append(base)
    except Exception:  # noqa: BLE001
        pass
    return " ".join(parts)[:4000].lower()


def _tool_name(data: dict) -> str:
    for k in ("tool", "tool_name", "name"):
        v = data.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()[:_TOOL_NAME_MAX]
    msg = data.get("message")
    if isinstance(msg, dict):
        for k in ("tool", "tool_name", "name"):
            v = msg.get(k)
            if isinstance(v, str) and v.strip():
                return v.strip()[:_TOOL_NAME_MAX]
    return ""


def _is_failure(et: str, data: dict) -> Tuple[bool, str]:
    """``(is_failure, source)`` for one event. Only tool results that failed
    and API or runtime error rows are candidates; a successful tool result
    that happens to mention a 429 in its output is not a gap."""
    if et in _TOOL_RESULT_TYPES:
        sflag = _det._structured_is_error(data)
        if sflag is False:
            return False, ""
        if sflag or _det._text_looks_failed(_det._result_text(data)):
            return True, "tool_result"
        return False, ""
    if et in _API_ERROR_TYPES or isinstance(data.get("error"), (dict, str)):
        if data.get("error") in (None, "", False) and et not in _API_ERROR_TYPES:
            return False, ""
        return True, "api_error"
    return False, ""


def classify_failure(data: dict, et: str = "") -> Optional[Tuple[str, str, Optional[int]]]:
    """``(code, marker, http_status)`` for a failed event's data, or ``None``
    when no mapped rule fires. Pure. Never raises."""
    try:
        status = _det._status_code(data)
        etype = _error_type(data)
        text = _failure_text(data)
        for code, markers, statuses, etypes in _RULES:
            if status is not None and status in statuses:
                return code, "status:%d" % status, status
            if etype and (etype in etypes or any(etype == m for m in markers)):
                return code, "error_type:%s" % etype, status
            for m in markers:
                if m in text:
                    return code, m, status
            if code == "E05_CAPACITY_GAP" and text and _MARKER_429.search(text):
                return code, "429", status
    except Exception:  # noqa: BLE001
        return None
    return None


def _event_ts(ev: dict) -> str:
    ts = ev.get("ts")
    if isinstance(ts, str):
        return ts
    if isinstance(ts, datetime):
        return ts.isoformat()
    return str(ts or "")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def make_record(code: str, *, session_id: str, runtime: str, tool: str,
                source: str, marker: str, http_status: Optional[int],
                event_id: str, ts: str) -> dict:
    return {
        "v": RECORD_VERSION,
        "code": code,
        "taxonomy": "MIX-E01-E08",
        "ts": ts,
        "observed_at": _now_iso(),
        "session_id": str(session_id or ""),
        "runtime": str(runtime or ""),
        "tool": str(tool or "")[:_TOOL_NAME_MAX],
        "source": source,
        "marker": marker,
        "http_status": http_status,
        "event_id": str(event_id or ""),
    }


def classify_events(events: Iterable[dict], *, session_id: str = "",
                    runtime: str = "") -> List[dict]:
    """Map store event rows (any order) to gap records. Rows that are not a
    failed tool result or an error row are skipped. Never raises."""
    out: List[dict] = []
    try:
        rows = [e for e in events if isinstance(e, dict)]
    except Exception:  # noqa: BLE001
        return out
    for ev in rows:
        try:
            et = str(ev.get("event_type") or "").strip().lower()
            data = _det._coerce_dict(ev.get("data"))
            failed, source = _is_failure(et, data)
            if not failed:
                continue
            hit = classify_failure(data, et)
            if hit is None:
                continue
            code, marker, status = hit
            sid = str(ev.get("session_id") or session_id or "")
            rt = runtime or str(ev.get("runtime_kind") or ev.get("agent_type") or "")
            out.append(make_record(
                code, session_id=sid, runtime=rt, tool=_tool_name(data),
                source=source, marker=marker, http_status=status,
                event_id=str(ev.get("id") or ""), ts=_event_ts(ev)))
        except Exception:  # noqa: BLE001
            continue
    return out


def classify_approvals(rows: Iterable[dict]) -> List[dict]:
    """A denied approval is a permission the operator refused: ``E02``. Only
    rows whose decision or status reads ``denied`` qualify."""
    out: List[dict] = []
    try:
        rows = [r for r in rows if isinstance(r, dict)]
    except Exception:  # noqa: BLE001
        return out
    for r in rows:
        try:
            decision = str(r.get("decision") or r.get("status") or "").lower()
            if decision != "denied":
                continue
            out.append(make_record(
                "E02_NO_ACCESS",
                session_id=str(r.get("requestor_session_id") or r.get("session_id") or ""),
                runtime=str(r.get("runtime") or r.get("agent_type") or ""),
                tool=str(r.get("action") or ""),
                source="approval", marker="approval:denied", http_status=None,
                event_id=str(r.get("id") or ""),
                ts=_event_ts({"ts": r.get("resolved_at") or r.get("created_at")})))
        except Exception:  # noqa: BLE001
            continue
    return out


# ── Exporter ─────────────────────────────────────────────────────────────────

class Exporter:
    """Appends gap records to ``<dir>/capability_gaps.jsonl``.

    Dedup key is ``event_id::code``; the keys are kept in memory and in
    ``capability_gaps.seen.json`` so a daemon restart does not replay the
    detector window. Both files are created ``0600``. Never raises past
    its public methods."""

    def __init__(self, directory: str):
        self.directory = directory
        self.path = os.path.join(directory, EXPORT_FILENAME)
        self.seen_path = os.path.join(directory, SEEN_FILENAME)
        self._seen: List[str] = []
        self._seen_set: set = set()
        self._pending: List[dict] = []
        self._loaded = False

    @classmethod
    def from_env(cls) -> Optional["Exporter"]:
        d = export_dir()
        return cls(d) if d else None

    # -- state --
    def _load_seen(self) -> None:
        if self._loaded:
            return
        self._loaded = True
        try:
            with open(self.seen_path, "r", encoding="utf-8") as fh:
                keys = json.load(fh)
            if isinstance(keys, list):
                self._seen = [str(k) for k in keys][-SEEN_CAP:]
                self._seen_set = set(self._seen)
        except (OSError, ValueError):
            self._seen, self._seen_set = [], set()

    def _remember(self, key: str) -> None:
        if key in self._seen_set:
            return
        self._seen.append(key)
        self._seen_set.add(key)
        if len(self._seen) > SEEN_CAP:
            drop = self._seen[:-SEEN_CAP]
            self._seen = self._seen[-SEEN_CAP:]
            self._seen_set.difference_update(drop)

    # -- observe --
    def observe(self, records: Iterable[dict]) -> int:
        """Queue every record not seen before. Returns how many were new."""
        self._load_seen()
        n = 0
        for rec in records:
            try:
                key = "%s::%s" % (rec.get("event_id") or "", rec.get("code") or "")
                if not rec.get("event_id") or key in self._seen_set:
                    continue
                self._remember(key)
                self._pending.append(rec)
                n += 1
            except Exception:  # noqa: BLE001
                continue
        return n

    def observe_events(self, session_id: str, runtime: str, events: Iterable[dict]) -> int:
        try:
            return self.observe(classify_events(events, session_id=session_id, runtime=runtime))
        except Exception as exc:  # noqa: BLE001
            log.debug("capability gaps: classify failed for %s: %s", session_id, exc)
            return 0

    def observe_approvals(self, rows: Iterable[dict]) -> int:
        try:
            return self.observe(classify_approvals(rows))
        except Exception as exc:  # noqa: BLE001
            log.debug("capability gaps: approvals skipped: %s", exc)
            return 0

    # -- write --
    def flush(self) -> int:
        """Append the queued records and persist the dedup memory. Returns
        the number of lines written. A write failure drops nothing from the
        queue, so the next tick retries."""
        if not self._pending:
            return 0
        try:
            os.makedirs(self.directory, exist_ok=True)
            lines = "".join(json.dumps(r, sort_keys=True, separators=(",", ":"),
                                       default=str) + "\n" for r in self._pending)
            fd = os.open(self.path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
            with os.fdopen(fd, "a", encoding="utf-8") as fh:
                fh.write(lines)
            n = len(self._pending)
            self._pending = []
        except OSError as exc:
            log.warning("capability gaps: export write failed: %s", exc)
            return 0
        try:
            tmp = self.seen_path + ".tmp"
            fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(self._seen, fh)
            os.replace(tmp, self.seen_path)
        except OSError as exc:
            log.debug("capability gaps: seen file not saved: %s", exc)
        return n


def describe() -> dict:
    """The contract a consumer reads before it reads records."""
    return {
        "record_version": RECORD_VERSION,
        "taxonomy": dict(TAXONOMY),
        "mapped_codes": list(MAPPED_CODES),
        "declared_only_codes": [c for c in TAXONOMY if c not in MAPPED_CODES],
        "record_fields": list(RECORD_FIELDS),
        "export": {
            "enabled": export_enabled(),
            "env": EXPORT_DIR_ENV,
            "path": os.path.join(export_dir(), EXPORT_FILENAME) if export_enabled() else None,
        },
        "limits": (
            "Only tool results that failed and error rows are classified. "
            "Four codes are emitted. The other four are declared and not emitted. "
            "Records carry fixed markers and metadata, never prompts, arguments, "
            "outputs or exception text."
        ),
    }


__all__ = [
    "EXPORT_DIR_ENV", "EXPORT_FILENAME", "SEEN_FILENAME", "RECORD_VERSION",
    "TAXONOMY", "MAPPED_CODES", "RECORD_FIELDS", "Exporter",
    "classify_events", "classify_approvals", "classify_failure",
    "describe", "export_dir", "export_enabled", "make_record",
]
