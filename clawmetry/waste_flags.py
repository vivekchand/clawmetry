"""Per-run "waste" heuristics.

A small set of cheap, derived flags that turn an anomalous run from
"something is unusual" into "here is the lever to pull". The thresholds are
deliberately tunable; each flag has a stable ``type`` so consumers can render
distinct chips/colours, plus a plain-English ``msg`` for the dashboard.

Pure-function and dependency-free so both the daemon snapshot builder
(``clawmetry.sync``) and the request handlers can call it without a circular
import.

Flag types (round-1 set):

- ``runaway``         — too many tool steps in one run (likely a loop)
- ``cold_cache``      — cache hit rate is low and the run has enough steps to
                         have warmed up, so context is being re-paid
- ``unscoped_result`` — a single tool result is huge (probably an unscoped
                         file/snapshot read)
- ``bloated_context`` — a single step's context tokens are very large

Each input field on the signals dict is optional and ``None``-safe; flags are
emitted only when the relevant signal is present, so a partial signal set (for
runtimes that don't expose cache numbers, for example) gracefully degrades.
"""

from __future__ import annotations

import json
import os
from typing import Any, Iterable


def _env_int(name: str, default: int) -> int:
    """Read an int from env, falling back to default on any parse error."""
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return default
    try:
        return int(raw)
    except (TypeError, ValueError):
        return default


def _env_float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return default
    try:
        return float(raw)
    except (TypeError, ValueError):
        return default


# Thresholds — overridable via env (no install-time config file needed).
RUNAWAY_STEPS = _env_int("CLAWMETRY_WASTE_RUNAWAY_STEPS", 30)
COLD_CACHE_HIT_RATIO = _env_float("CLAWMETRY_WASTE_COLD_CACHE_HIT", 0.5)
COLD_CACHE_MIN_STEPS = _env_int("CLAWMETRY_WASTE_COLD_CACHE_MIN_STEPS", 5)
UNSCOPED_RESULT_BYTES = _env_int("CLAWMETRY_WASTE_UNSCOPED_RESULT_BYTES", 10_000)
BLOATED_CONTEXT_TOKENS = _env_int("CLAWMETRY_WASTE_BLOATED_CONTEXT_TOKENS", 50_000)


def _fmt_bytes(n: int) -> str:
    """Human-readable byte count used in flag messages."""
    if n < 1024:
        return f"{n} B"
    if n < 1024 * 1024:
        return f"{n / 1024:.1f} KB"
    return f"{n / (1024 * 1024):.1f} MB"


def compute_flags(signals: Any) -> list[dict]:
    """Derive waste flags from a per-run signals dict. Never raises.

    Recognised signal keys (all optional, ``None``-safe):

    - ``step_count``                   : int — number of tool-step events
    - ``cache_read_tokens``            : int — total cache-read tokens this run
    - ``input_tokens``                 : int — non-cached input tokens this run
    - ``max_tool_result_bytes``        : int — biggest tool-result body (bytes)
    - ``max_event_token_count``        : int — biggest single-event token count
    """
    out: list[dict] = []
    if not isinstance(signals, dict):
        return out

    def _int(key: str) -> int | None:
        v = signals.get(key)
        if v is None:
            return None
        try:
            return int(v)
        except (TypeError, ValueError):
            return None

    steps = _int("step_count")
    if steps is not None and steps > RUNAWAY_STEPS:
        out.append({
            "type": "runaway",
            "severity": "red",
            "msg": f"{steps} steps (likely runaway loop)",
        })

    cache_read = _int("cache_read_tokens")
    inp = _int("input_tokens")
    if (
        steps is not None and steps > COLD_CACHE_MIN_STEPS
        and cache_read is not None and inp is not None
    ):
        total = cache_read + inp
        if total > 0:
            ratio = cache_read / total
            if ratio < COLD_CACHE_HIT_RATIO:
                out.append({
                    "type": "cold_cache",
                    "severity": "yellow",
                    "msg": f"{round(ratio * 100)}% cache hit (cold start or drift)",
                })

    rb = _int("max_tool_result_bytes")
    if rb is not None and rb > UNSCOPED_RESULT_BYTES:
        out.append({
            "type": "unscoped_result",
            "severity": "yellow",
            "msg": f"Step returned {_fmt_bytes(rb)} (unscoped snapshot?)",
        })

    tc = _int("max_event_token_count")
    if tc is not None and tc > BLOATED_CONTEXT_TOKENS:
        out.append({
            "type": "bloated_context",
            "severity": "yellow",
            "msg": f"Step with {tc:,} context (bloated)",
        })

    return out


# ── Per-session signal aggregation ────────────────────────────────────────────
# Kept here (rather than in local_store) because it must work on event rows
# from any source — the SQL fast path, a snapshot iterator, or a fixture in
# a test. The shape matches ``local_store.query_events`` rows:
#   {event_type: str, data: dict|bytes|str (JSON), token_count: int|None, ...}


_TOOL_CALL_ET_HINTS = ("tool_call", "tool_use", "tool.call")
_TOOL_RESULT_ET_HINTS = ("tool_result", "tool.result", "tool_use_result")


def _ev_is_tool_call(event_type: str) -> bool:
    et = event_type.lower()
    return any(h in et for h in _TOOL_CALL_ET_HINTS) and "result" not in et


def _ev_is_tool_result(event_type: str) -> bool:
    et = event_type.lower()
    return any(h in et for h in _TOOL_RESULT_ET_HINTS)


def _coerce_data(data: Any) -> dict:
    """Return a dict for ``data``, parsing JSON bytes/str when needed."""
    if isinstance(data, dict):
        return data
    if isinstance(data, (bytes, bytearray)):
        try:
            data = bytes(data).decode("utf-8", "replace")
        except Exception:
            return {}
    if isinstance(data, str):
        try:
            obj = json.loads(data)
        except Exception:
            return {}
        return obj if isinstance(obj, dict) else {}
    return {}


def _i(d: dict, *keys: str) -> int:
    """First parseable int from any of ``keys``, else 0."""
    for k in keys:
        v = d.get(k)
        if v is None:
            continue
        try:
            return int(v)
        except (TypeError, ValueError):
            continue
    return 0


def compute_signals_from_events(events: Iterable[dict]) -> dict:
    """Aggregate per-run waste signals from an iterable of event rows.

    Pure-function, never raises. The output shape matches the input contract
    of :func:`compute_flags` — call ``compute_flags(compute_signals_from_events(rows))``
    end to end for a single run's flags.
    """
    step_count = 0
    max_result_bytes = 0
    max_event_tokens = 0
    cache_read = 0
    input_tokens = 0

    for e in events or []:
        et = str(e.get("event_type") or "")

        if _ev_is_tool_call(et):
            step_count += 1

        try:
            tc = int(e.get("token_count") or 0)
        except (TypeError, ValueError):
            tc = 0
        if tc > max_event_tokens:
            max_event_tokens = tc

        data = _coerce_data(e.get("data"))

        if _ev_is_tool_result(et) and data:
            try:
                blob = json.dumps(data, separators=(",", ":"), default=str)
                sz = len(blob.encode("utf-8"))
            except Exception:
                sz = 0
            if sz > max_result_bytes:
                max_result_bytes = sz

        if not data:
            continue
        usage = data.get("usage") if isinstance(data.get("usage"), dict) else {}
        extra = data.get("extra") if isinstance(data.get("extra"), dict) else {}
        cache_read += _i(
            usage,
            "cacheRead", "cacheReadInputTokens",
            "cache_read_input_tokens", "cache_read_tokens",
        )
        cache_read += _i(
            extra,
            "cacheRead", "cacheReadInputTokens",
            "cache_read_input_tokens", "cache_read_tokens",
        )
        input_tokens += _i(
            usage, "input", "inputTokens", "input_tokens", "prompt_tokens",
        )
        input_tokens += _i(
            extra, "input", "inputTokens", "input_tokens", "prompt_tokens",
        )

    return {
        "step_count": step_count,
        "max_tool_result_bytes": max_result_bytes,
        "max_event_token_count": max_event_tokens,
        "cache_read_tokens": cache_read,
        "input_tokens": input_tokens,
    }


# ── Health-timeline derivation ────────────────────────────────────────────────
# Tiny derived primitives shared by the snapshot builder and the dashboard
# route, so the read path doesn't have to re-derive runtime/severity from
# scratch.


def runtime_from_session_id(session_id: Any) -> str:
    """Map a session id back to its runtime label.

    Family-runtime sessions are namespaced with a ``<runtime>:`` prefix
    (``claude_code:``, ``cursor:``, ``goose:``, …); OpenClaw sessions are raw
    UUIDs without a prefix. Returns ``"openclaw"`` as the default so the
    timeline always has *some* bucket for a session.
    """
    if not isinstance(session_id, str) or not session_id:
        return "openclaw"
    head, sep, _ = session_id.partition(":")
    if not sep or not head:
        return "openclaw"
    return head.lower()


def severity_from_counts(error_count: Any, flag_count: Any) -> str:
    """Map (errors, flags) -> a dot colour.

    - ``red``    — at least one real error (post benign-error filtering, #2202).
    - ``yellow`` — no errors but at least one waste flag (#2215).
    - ``green``  — clean run.
    """
    try:
        ec = int(error_count or 0)
    except (TypeError, ValueError):
        ec = 0
    try:
        fc = int(flag_count or 0)
    except (TypeError, ValueError):
        fc = 0
    if ec > 0:
        return "red"
    if fc > 0:
        return "yellow"
    return "green"


def event_is_real_error(event: Any) -> bool:
    """True when an event row carries the corrected error flag (after #2202).

    Reads ``data.is_error`` / ``data.isError`` and ``data.extra.isError`` — the
    union of what the snapshot's ``_err()`` predicate checks. Never raises.
    """
    if not isinstance(event, dict):
        return False
    data = _coerce_data(event.get("data"))
    if not data:
        return False
    if data.get("is_error") or data.get("isError"):
        return True
    extra = data.get("extra") if isinstance(data.get("extra"), dict) else {}
    if extra.get("isError") or extra.get("is_error"):
        return True
    return False
