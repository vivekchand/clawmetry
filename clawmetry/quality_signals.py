"""
clawmetry/quality_signals.py — evidence-bearing quality signals.

THE RULE THIS MODULE EXISTS TO ENFORCE:

    A verdict is a claim with evidence. No exhibits, no verdict.

Background (audit 2026-08-15). The previous Quality surface graded sessions
from a single string-similarity heuristic whose only false-positive guard read
tool use from ``data.message.content[*].type == "tool_use"`` — the OpenClaw /
Anthropic block-list shape. Every family runtime (claude_code, codex, cursor,
…) emits tool calls as SEPARATE ``tool_call`` events carrying
``data.tool_calls[*]``, so the guard parsed nothing, never fired, and the
detector flagged sessions that had made 39–63 real tool calls inside the very
window it examined. It also stamped every row's runtime from a loop variable.
Both bugs were silent: no exception, no empty result, just a confident wrong
answer. Tests stayed green because they ran OpenClaw fixtures through an
OpenClaw-shaped parser.

The defences, in order:

  1. **Two dialects, one reader.** ``normalize_events`` collapses the family
     vocabulary (``tool_call`` / ``tool_result`` / ``message`` / ``thinking`` /
     ``compaction`` / ``error``) AND the OpenClaw dotted vocabulary
     (``tool.use`` / ``tool.result`` / ``message`` / ``model.completed``) into
     one ``NormalizedEvent``. Signals never touch a raw payload again, so a new
     runtime shape is one reader change, not N silent blind spots.
  2. **Capabilities are declared and checked.** Every signal names the fields
     it needs. ``probe_capabilities`` reports what a runtime ACTUALLY emitted.
     A signal whose inputs are absent returns ``not_measurable`` — never a
     clean bill of health. That is the exact failure the audit found.
  3. **Exhibits or nothing.** ``Verdict.__post_init__`` refuses to construct a
     verdict with an empty exhibit list. The invariant is enforced at the type
     boundary, so no caller can route around it.
  4. **Confidence is derived.** From sample size and margin over threshold —
     never a literal. The old classifier returned a hardcoded 0.8 for every
     flagged session and 0.85 for every success, which made the surface
     unfalsifiable.

Public surface:
    normalize_events(rows)                 -> list[NormalizedEvent]
    probe_capabilities(events)             -> RuntimeCapabilities
    extract_signals(events, *, thresholds) -> list[Verdict]
    SIGNALS                                -> the declared signal registry
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Iterable

# ── event-type dialects ────────────────────────────────────────────────────
#
# The family adapters normalise to the first column; OpenClaw's v3 parser
# emits the second. Anything not listed here is carried through as "other"
# rather than dropped, so a new event type shows up in capability probes
# instead of vanishing.

_KIND_BY_TYPE: dict[str, str] = {
    # family (normalised adapter envelope)
    "message":        "message",
    "tool_call":      "tool_call",
    "tool_result":    "tool_result",
    "thinking":       "thinking",
    "compaction":     "compaction",
    "error":          "error",
    "model_change":   "model_change",
    # OpenClaw v3 (dotted)
    "tool.use":       "tool_call",
    "tool.call":      "tool_call",
    "tool.result":    "tool_result",
    "model.completed": "message",
    "model.changed":  "model_change",
    "assistant":      "message",
    "user":           "message",
    "session.started": "session_start",
    "session.ended":  "session_end",
}

# Roles that mean "the agent spoke", across dialects.
_ASSISTANT_ROLES = frozenset({"assistant", "model", "ai"})


@dataclass
class NormalizedEvent:
    """One event, dialect-independent. Signals read ONLY this."""

    kind: str                      # message | tool_call | tool_result | ...
    ts: float | None               # epoch seconds, None when unparseable
    role: str = ""
    text: str = ""
    tool_name: str = ""
    tool_input: dict[str, Any] = field(default_factory=dict)
    is_error: bool | None = None   # None = the runtime told us nothing
    benign_error: bool = False
    raw_type: str = ""
    session_id: str = ""

    @property
    def is_assistant(self) -> bool:
        return self.role in _ASSISTANT_ROLES

    @property
    def file_path(self) -> str:
        """The file a tool acted on, when the input names one."""
        for k in ("file_path", "path", "filename", "filepath", "notebook_path"):
            v = self.tool_input.get(k)
            if isinstance(v, str) and v:
                return v
        return ""

    @property
    def input_digest(self) -> str:
        """Stable short digest of the tool input, for repeat detection.

        Deliberately content-based, NOT identity-based: two Edit calls on the
        same file with the same payload must collide, while an Edit on a
        different file must not.
        """
        if not self.tool_input:
            return self.tool_name
        try:
            import hashlib
            import json
            blob = json.dumps(self.tool_input, sort_keys=True, default=str)[:4000]
            h = hashlib.sha256(blob.encode("utf-8")).hexdigest()[:10]
        except Exception:
            h = str(len(str(self.tool_input)))
        return f"{self.tool_name}:{h}"


def _epoch(ts: Any) -> float | None:
    """ISO / epoch-ms / epoch-s → epoch seconds. None when unparseable."""
    if ts is None:
        return None
    if isinstance(ts, (int, float)):
        v = float(ts)
        # Heuristic: anything past year ~2001 in ms is a millisecond stamp.
        return v / 1000.0 if v > 1e11 else v
    s = str(ts).strip()
    if not s:
        return None
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        # A naive stamp is UTC by convention everywhere in the store; without
        # this the epoch shifts by the local offset and every duration is wrong.
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.timestamp()
    except (ValueError, TypeError):
        pass
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


def _text_of(data: dict[str, Any]) -> str:
    """Assistant-visible text across every shape we have observed.

    Family adapters put a plain string in ``content``. OpenClaw v3 uses a
    ``message`` envelope whose ``content`` may be a string or an Anthropic
    block list. ``finalPromptText`` / ``completionText`` / ``output`` cover the
    daemon-normalised v3 rows.
    """
    if not isinstance(data, dict):
        return ""
    c = data.get("content")
    if isinstance(c, str) and c:
        return c
    if isinstance(c, list):
        parts = [b.get("text") for b in c
                 if isinstance(b, dict) and isinstance(b.get("text"), str)]
        if parts:
            return " ".join(parts)
    msg = data.get("message")
    if isinstance(msg, dict):
        mc = msg.get("content")
        if isinstance(mc, str) and mc:
            return mc
        if isinstance(mc, list):
            parts = [b.get("text") for b in mc
                     if isinstance(b, dict) and isinstance(b.get("text"), str)]
            if parts:
                return " ".join(parts)
    for k in ("finalPromptText", "completionText", "text", "output", "result"):
        v = data.get(k)
        if isinstance(v, str) and v:
            return v
    return ""


def _tool_calls_of(data: dict[str, Any]) -> list[tuple[str, dict]]:
    """[(tool_name, input), ...] across BOTH dialects.

    This is the function whose family-shape blindness caused the audit. It now
    reads, in order: the family ``data.tool_calls[]`` list, the family
    ``data.tool_name`` scalar, the OpenClaw v3 flat ``data.name`` + ``input``,
    and the Anthropic block list under ``data.message.content[]``.
    """
    out: list[tuple[str, dict]] = []
    if not isinstance(data, dict):
        return out

    # family: {"tool_calls": [{"name": "Bash", "input": {...}}], ...}
    #
    # The argument key is NOT uniform: Claude Code / Copilot / Antigravity use
    # ``input``, while goose / opencode / qwen_code / n8n use ``arguments``.
    # Reading only one of them recovers the tool NAME but silently drops every
    # argument, which leaves thrash and forward-progress detection permanently
    # dead for those runtimes while the capability probe still looks healthy.
    # Caught by tests/test_quality_runtime_conformance.py; keep both keys.
    tcs = data.get("tool_calls")
    if isinstance(tcs, list):
        for tc in tcs:
            if isinstance(tc, dict):
                name = str(tc.get("name") or "").strip()
                ipt = tc.get("input")
                if not isinstance(ipt, dict):
                    ipt = tc.get("arguments")
                out.append((name, ipt if isinstance(ipt, dict) else {}))
    if out:
        return out

    # OpenClaw v3 flat: {"name": "read_file", "input": {...}}
    name = data.get("name")
    if isinstance(name, str) and name:
        ipt = data.get("input")
        if not isinstance(ipt, dict):
            ipt = data.get("arguments")
        return [(name.strip(), ipt if isinstance(ipt, dict) else {})]

    # family scalar fallback
    tn = data.get("tool_name")
    if isinstance(tn, str) and tn:
        return [(tn.strip(), {})]

    # Anthropic block list
    msg = data.get("message")
    if isinstance(msg, dict) and isinstance(msg.get("content"), list):
        for blk in msg["content"]:
            if isinstance(blk, dict) and blk.get("type") == "tool_use":
                ipt = blk.get("input")
                out.append((str(blk.get("name") or "").strip(),
                            ipt if isinstance(ipt, dict) else {}))
    return out


def _error_of(data: dict[str, Any]) -> tuple[bool | None, bool]:
    """(is_error, benign) from either dialect.

    Returns ``(None, ...)`` when the runtime reported NOTHING about success —
    which is materially different from "reported success". Signals must not
    treat silence as a pass; that distinction is what makes
    ``not_measurable`` possible instead of a false clean bill of health.
    """
    if not isinstance(data, dict):
        return (None, False)
    benign = bool(data.get("benign_error"))
    extra = data.get("extra")
    if isinstance(extra, dict):
        for k in ("isError", "is_error"):
            if k in extra:
                return (bool(extra[k]), benign)
    for k in ("is_error", "isError"):
        if k in data:
            return (bool(data[k]), benign)
    return (None, benign)


def normalize_events(rows: Iterable[dict[str, Any]] | None) -> list[NormalizedEvent]:
    """Raw DuckDB event rows → dialect-independent events, oldest first.

    ``data`` may arrive as a dict or as a JSON blob/bytes (DuckDB BLOB
    column); both are handled. Never raises — a row that cannot be parsed is
    skipped rather than poisoning the whole session.
    """
    out: list[NormalizedEvent] = []
    for r in rows or []:
        if not isinstance(r, dict):
            continue
        data = r.get("data")
        if isinstance(data, (bytes, bytearray)):
            try:
                import json
                data = json.loads(data.decode("utf-8", "replace"))
            except Exception:
                data = {}
        elif isinstance(data, str):
            try:
                import json
                data = json.loads(data)
            except Exception:
                data = {}
        if not isinstance(data, dict):
            data = {}

        raw_type = str(r.get("event_type") or "").strip()
        kind = _KIND_BY_TYPE.get(raw_type.lower(), "other")
        is_err, benign = _error_of(data)

        # Tool use is not always carried by a tool-typed event. OpenClaw and
        # any Anthropic-style transcript put ``tool_use`` blocks INSIDE an
        # assistant message, so a message event can be a tool call. Parse
        # first, classify second — keying off the event type alone is exactly
        # the assumption that made the previous detector blind, and skipping
        # this promotion would rebuild the same blind spot facing the other
        # dialect.
        calls: list[tuple[str, dict]] = []
        if kind in ("tool_call", "message"):
            calls = _tool_calls_of(data)
            if calls and calls[0][0] and kind == "message":
                kind = "tool_call"
        name, ipt = calls[0] if calls else ("", {})
        if kind == "tool_result" and not name:
            name = str(data.get("tool_name") or "").strip()

        out.append(NormalizedEvent(
            kind=kind,
            ts=_epoch(r.get("ts")),
            role=str(data.get("role") or "").strip().lower(),
            text=_text_of(data),
            tool_name=name,
            tool_input=ipt,
            is_error=is_err,
            benign_error=benign,
            raw_type=raw_type,
            session_id=str(r.get("session_id") or ""),
        ))
    out.sort(key=lambda e: (e.ts is None, e.ts or 0.0))
    return out


# ── capability probing ─────────────────────────────────────────────────────

@dataclass
class RuntimeCapabilities:
    """What a runtime ACTUALLY emitted — observed, never assumed.

    ``unknown`` is a first-class state. A runtime we have not seen data from
    does not get an optimistic default; its signals report not_measurable and
    the UI says so, rather than implying health we cannot observe.
    """

    runtime: str = ""
    event_kinds: set[str] = field(default_factory=set)
    has_tool_calls: bool = False
    has_tool_inputs: bool = False       # tool_call carries a parseable input
    has_file_paths: bool = False        # tool input names a file
    has_error_flags: bool = False       # tool_result carries isError
    has_timestamps: bool = False
    sample_events: int = 0

    def supports(self, signal_name: str) -> bool:
        sig = SIGNALS.get(signal_name)
        return bool(sig and sig.requires(self))

    def as_dict(self) -> dict[str, Any]:
        return {
            "runtime":         self.runtime,
            "event_kinds":     sorted(self.event_kinds),
            "has_tool_calls":  self.has_tool_calls,
            "has_tool_inputs": self.has_tool_inputs,
            "has_file_paths":  self.has_file_paths,
            "has_error_flags": self.has_error_flags,
            "has_timestamps":  self.has_timestamps,
            "sample_events":   self.sample_events,
            "supported_signals": sorted(
                n for n in SIGNALS if self.supports(n)
            ),
        }


def probe_capabilities(
    events: list[NormalizedEvent],
    *,
    runtime: str = "",
) -> RuntimeCapabilities:
    """Observe what this runtime emits. Pure; never raises."""
    caps = RuntimeCapabilities(runtime=runtime, sample_events=len(events))
    for e in events:
        caps.event_kinds.add(e.kind)
        if e.kind == "tool_call":
            if e.tool_name:
                caps.has_tool_calls = True
            if e.tool_input:
                caps.has_tool_inputs = True
            if e.file_path:
                caps.has_file_paths = True
        if e.kind == "tool_result" and e.is_error is not None:
            caps.has_error_flags = True
        if e.ts is not None:
            caps.has_timestamps = True
    return caps


# ── the verdict contract ───────────────────────────────────────────────────

class EvidenceError(ValueError):
    """Raised when a verdict is constructed without exhibits.

    This is deliberately a hard failure rather than a silent downgrade: a
    verdict with no evidence is the exact defect this module exists to
    prevent, and swallowing it would reintroduce it.
    """


@dataclass
class Verdict:
    """A quality claim, inseparable from the evidence for it."""

    name: str
    runtime: str
    confidence: float
    signal: str
    observed: dict[str, Any]
    threshold: dict[str, Any]
    window: dict[str, Any]
    exhibits: list[dict[str, Any]]
    session_id: str = ""
    severity: str = "rough"           # rough | note

    def __post_init__(self) -> None:
        if not self.exhibits:
            raise EvidenceError(
                f"verdict {self.name!r} has no exhibits; "
                "a claim without evidence must not exist"
            )
        self.confidence = max(0.0, min(1.0, float(self.confidence)))

    def as_dict(self) -> dict[str, Any]:
        return {
            "verdict":    self.name,
            "runtime":    self.runtime,
            "confidence": round(self.confidence, 3),
            "severity":   self.severity,
            "session_id": self.session_id,
            "evidence": {
                "signal":    self.signal,
                "observed":  self.observed,
                "threshold": self.threshold,
                "window":    self.window,
                "exhibits":  self.exhibits[:12],
                "exhibit_count": len(self.exhibits),
            },
        }


def _confidence(sample: int, observed: float, threshold: float,
                *, min_sample: int) -> float:
    """Derived confidence — never a literal.

    Two independent terms, multiplied so a weakness in either drags the result
    down:

      * sample term  — how much evidence we have, saturating at 4x the signal's
        declared minimum. Four tool calls cannot yield high confidence no
        matter how extreme the rate.
      * margin term  — how far past the threshold the observation sits,
        saturating at 3x. Scraping the line is a weak claim.

    Floored at 0.25 so a real, exhibit-backed finding is never reported as
    near-zero, and capped at 0.95 because a deterministic signal on a bounded
    event window is not certainty.
    """
    if sample <= 0 or threshold <= 0:
        return 0.25
    sample_term = min(1.0, sample / float(max(1, min_sample) * 4))
    margin_term = min(1.0, max(0.0, (observed - threshold) / (threshold * 2)))
    raw = 0.35 + 0.65 * (0.5 * sample_term + 0.5 * margin_term)
    return max(0.25, min(0.95, raw))


# ── signal registry ────────────────────────────────────────────────────────

@dataclass
class Signal:
    """A declared quality signal: what it needs, and how it decides."""

    name: str
    label: str                                   # plain English, user-facing
    requires: Callable[[RuntimeCapabilities], bool]
    detect: Callable[..., Verdict | None]
    min_sample: int = 5


def _sig_tool_error_rate(events, *, runtime, thresholds, session_id) -> Verdict | None:
    """Real (non-benign) tool failure rate above this runtime's own normal.

    The signal the old classifier ignored while guessing from message text —
    ``extra.isError`` is ground truth the runtime itself reported.
    """
    results = [e for e in events if e.kind == "tool_result" and e.is_error is not None]
    if len(results) < 5:
        return None
    errors = [e for e in results if e.is_error and not e.benign_error]
    pct = 100.0 * len(errors) / len(results)
    limit = float(thresholds.get("tool_error_pct", 8.0))
    if pct <= limit:
        return None
    exhibits = [{
        "ts":    e.ts,
        "tool":  e.tool_name,   # may be "" — some runtimes don't name results
        "error": (e.text or "")[:240],
    } for e in errors[:12]]
    if not exhibits:
        return None
    return Verdict(
        name="tool_failures",
        runtime=runtime,
        confidence=_confidence(len(results), pct, limit, min_sample=5),
        signal="tool_error_rate",
        observed={"tool_results": len(results), "tool_errors": len(errors),
                  "pct": round(pct, 1)},
        threshold={"pct": round(limit, 1),
                   "source": thresholds.get("_source", "cold-start default")},
        window={"events_examined": len(events)},
        exhibits=exhibits,
        session_id=session_id,
    )


def _sig_tool_thrash(events, *, runtime, thresholds, session_id) -> Verdict | None:
    """The same tool called with the same input, repeatedly, failing.

    This is what "stuck in a loop" actually looks like in the data — identical
    invocations that keep erroring. It replaces the text-similarity guess with
    an observation, and it CANNOT fire on an agent that is making progress,
    because a changed input changes the digest.
    """
    calls = [e for e in events if e.kind == "tool_call" and e.tool_name]
    if len(calls) < 3:
        return None
    limit = int(thresholds.get("thrash_repeats", 4))

    # Pair each call with the result that follows it, so "repeated AND failing"
    # is provable rather than assumed. Binary search over the sorted result
    # timestamps: a linear rescan per call is O(calls x results), which on a
    # long session is tens of thousands of comparisons inside the ingest pass.
    import bisect
    results = [e for e in events if e.kind == "tool_result" and e.ts is not None]
    result_ts = [r.ts for r in results]

    def _next_result(after_ts):
        if after_ts is None or not results:
            return None
        i = bisect.bisect_left(result_ts, after_ts)
        return results[i] if i < len(results) else None

    by_digest: dict[str, list[NormalizedEvent]] = {}
    for c in calls:
        by_digest.setdefault(c.input_digest, []).append(c)

    worst_key, worst = "", []
    for k, group in by_digest.items():
        if len(group) > len(worst):
            worst_key, worst = k, group
    if len(worst) < limit:
        return None

    # Count failures across EVERY repeat, but build exhibits from the first
    # dozen. Counting only the exhibit slice would put `failed` and
    # `identical_calls` on different denominators inside one evidence block —
    # and the whole point of this surface is that its numbers survive being
    # looked at.
    failing = 0
    exhibits: list[dict[str, Any]] = []
    for i, c in enumerate(worst):
        res = _next_result(c.ts)
        errored = bool(res and res.is_error and not res.benign_error)
        if errored:
            failing += 1
        if i < 12:
            exhibits.append({
                "ts":      c.ts,
                "tool":    c.tool_name,
                "file":    c.file_path,
                "errored": errored,
            })
    # Identical repeats that all SUCCEED are not thrash (a poll loop, a
    # formatter run). Require that the repetition is actually going wrong.
    if failing < 2:
        return None
    return Verdict(
        name="tool_thrash",
        runtime=runtime,
        confidence=_confidence(len(worst), float(len(worst)), float(limit),
                               min_sample=limit),
        signal="tool_thrash",
        observed={"tool": worst[0].tool_name, "identical_calls": len(worst),
                  "failed": failing, "digest": worst_key},
        threshold={"repeats": limit,
                   "source": thresholds.get("_source", "cold-start default")},
        window={"events_examined": len(events), "tool_calls": len(calls)},
        exhibits=exhibits,
        session_id=session_id,
    )


def _sig_no_forward_progress(events, *, runtime, thresholds, session_id) -> Verdict | None:
    """Repeated edits to one file with no verification between them.

    The honest version of the old "cognitive loop": it requires an observable
    edit-without-check pattern on a named file, not merely that the agent's
    prose rhymed. Runtimes that do not expose file paths cannot produce this
    verdict at all.
    """
    edits = [e for e in events
             if e.kind == "tool_call" and e.file_path
             and any(w in e.tool_name.lower()
                     for w in ("edit", "write", "replace", "patch", "apply"))]
    if len(edits) < 3:
        return None
    limit = int(thresholds.get("edit_repeats", 5))

    verify_words = ("test", "bash", "run", "exec", "shell", "lint",
                    "check", "pytest", "build", "compile")
    by_file: dict[str, list[NormalizedEvent]] = {}
    for e in edits:
        by_file.setdefault(e.file_path, []).append(e)

    target, group = "", []
    for f, g in by_file.items():
        if len(g) > len(group):
            target, group = f, g
    if len(group) < limit:
        return None

    # Was anything verified from the first edit onward — INCLUDING after the
    # last one? "Edit a dozen times, then run the tests once" is a completely
    # normal way to work. Only looking between the first and last edit would
    # flag it, which is precisely the false-positive class this rebuild
    # exists to remove; the pathological case is editing and never checking
    # AT ALL.
    lo = min((e.ts for e in group if e.ts is not None), default=None)
    verified = 0
    if lo is not None:
        for e in events:
            if (e.kind == "tool_call" and e.ts is not None
                    and e.ts >= lo
                    and any(w in e.tool_name.lower() for w in verify_words)):
                verified += 1
    if verified > 0:
        # It edited, then checked its work. That is a normal iteration cycle.
        return None
    exhibits = [{"ts": e.ts, "tool": e.tool_name, "file": e.file_path}
                for e in group[:12]]
    return Verdict(
        name="no_forward_progress",
        runtime=runtime,
        confidence=_confidence(len(group), float(len(group)), float(limit),
                               min_sample=limit),
        signal="no_forward_progress",
        observed={"file": target, "edits": len(group),
                  "checks_after_first_edit": verified},
        threshold={"edits": limit,
                   "source": thresholds.get("_source", "cold-start default")},
        window={"events_examined": len(events)},
        exhibits=exhibits,
        session_id=session_id,
    )


def _sig_hard_failure(events, *, runtime, thresholds, session_id) -> Verdict | None:
    """The runtime itself reported an error event, or ended on a failed tool."""
    errs = [e for e in events if e.kind == "error"]
    tail_fail = [e for e in events[-3:]
                 if e.kind == "tool_result" and e.is_error and not e.benign_error]
    hits = errs + [e for e in tail_fail if e not in errs]
    if not hits:
        return None
    exhibits = [{"ts": e.ts, "tool": e.tool_name or "(runtime)",
                 "error": (e.text or "")[:240]} for e in hits[:12]]
    return Verdict(
        name="hard_failure",
        runtime=runtime,
        confidence=min(0.95, 0.6 + 0.1 * len(hits)),
        signal="hard_failure",
        observed={"error_events": len(errs),
                  "failed_at_end": len(tail_fail)},
        threshold={"any": 1, "source": "runtime-reported"},
        window={"events_examined": len(events)},
        exhibits=exhibits,
        session_id=session_id,
    )


SIGNALS: dict[str, Signal] = {
    "tool_error_rate": Signal(
        name="tool_error_rate",
        label="Tools kept failing",
        requires=lambda c: c.has_error_flags,
        detect=_sig_tool_error_rate,
        min_sample=5,
    ),
    "tool_thrash": Signal(
        name="tool_thrash",
        label="Called the same thing over and over",
        requires=lambda c: c.has_tool_calls and c.has_tool_inputs,
        detect=_sig_tool_thrash,
        min_sample=4,
    ),
    "no_forward_progress": Signal(
        name="no_forward_progress",
        label="Edited the same file without ever checking it",
        requires=lambda c: c.has_file_paths,
        detect=_sig_no_forward_progress,
        min_sample=5,
    ),
    "hard_failure": Signal(
        name="hard_failure",
        label="Ended on an error",
        requires=lambda c: "error" in c.event_kinds or c.has_error_flags,
        detect=_sig_hard_failure,
        min_sample=1,
    ),
}


@dataclass
class SessionAssessment:
    """The full, honest read on one session."""

    session_id: str
    runtime: str
    verdicts: list[Verdict]
    capabilities: RuntimeCapabilities
    measurable: bool
    not_measurable_reason: str = ""

    @property
    def is_rough(self) -> bool:
        return any(v.severity == "rough" for v in self.verdicts)

    def as_dict(self) -> dict[str, Any]:
        return {
            "session_id":      self.session_id,
            "runtime":         self.runtime,
            "measurable":      self.measurable,
            "reason":          self.not_measurable_reason,
            "verdicts":        [v.as_dict() for v in self.verdicts],
            "capabilities":    self.capabilities.as_dict(),
        }


# A session needs at least this much signal before we will grade it at all.
# Below it, the honest answer is "we could not tell", not "success" — the old
# classifier's fallthrough handed a free pass to 12 of 62 sessions in the
# audit window, most of them pure research chats with zero tool calls.
MIN_GRADEABLE_EVENTS = 8
MIN_GRADEABLE_TOOL_RESULTS = 3


def assess_session(
    rows: Iterable[dict[str, Any]] | None,
    *,
    runtime: str,
    session_id: str = "",
    thresholds: dict[str, Any] | None = None,
) -> SessionAssessment:
    """Normalize → probe → run every supported signal. Never raises.

    A signal that the runtime cannot support is SKIPPED, not failed — and the
    capability record travels with the assessment so the UI can say "we cannot
    measure this here" instead of implying a clean result.
    """
    events = normalize_events(rows)
    caps = probe_capabilities(events, runtime=runtime)
    thresholds = dict(thresholds or {})

    tool_results = sum(1 for e in events if e.kind == "tool_result")
    if len(events) < MIN_GRADEABLE_EVENTS and tool_results < MIN_GRADEABLE_TOOL_RESULTS:
        return SessionAssessment(
            session_id=session_id, runtime=runtime, verdicts=[],
            capabilities=caps, measurable=False,
            not_measurable_reason=(
                "Too little activity to judge — "
                f"{len(events)} events, {tool_results} tool results."
            ),
        )

    supported = [s for s in SIGNALS.values() if s.requires(caps)]
    if not supported:
        return SessionAssessment(
            session_id=session_id, runtime=runtime, verdicts=[],
            capabilities=caps, measurable=False,
            not_measurable_reason=(
                f"This runtime does not report the signals we grade on "
                f"(saw: {', '.join(sorted(caps.event_kinds)) or 'nothing'})."
            ),
        )

    verdicts: list[Verdict] = []
    for sig in supported:
        try:
            v = sig.detect(events, runtime=runtime, thresholds=thresholds,
                           session_id=session_id)
        except EvidenceError:
            # A detector tried to emit a verdict with no exhibits. That is a
            # bug in the detector, and the contract correctly refused it —
            # drop the claim rather than weaken the invariant.
            continue
        except Exception:
            continue
        if v is not None:
            verdicts.append(v)

    verdicts.sort(key=lambda v: -v.confidence)
    return SessionAssessment(
        session_id=session_id, runtime=runtime, verdicts=verdicts,
        capabilities=caps, measurable=True,
    )
