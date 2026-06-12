"""clawmetry/detectors.py — research-backed, judge-free, CPU-cheap trajectory
anomaly detectors over a session's recent event sequence (issue #2999).

Design basis (the agent-observability deep-research memo + TrajAD / TRAIL /
MAST taxonomies): zero-shot LLM judges are near-useless at localizing the bad
step and 17-27x slower; naive embedding-outlier heuristics dilute the single
anomalous step. What is load-bearing is *sequence structure*. So this module is
a set of small, explainable, bounded heuristics over the ordered tool/result
stream — NOT an expensive judge. Each detector is pure (no I/O, no store, no
clock dependence beyond what the caller passes), operates on the last ``W``
events, never crashes on malformed events, and returns a structured incident.

The four detectors map to the honest failure classes the landing page promises:

1. ``stuck_loop``       — TrajAD Type II (circular loops / repeated identical
                          tool calls): K consecutive identical
                          ``(tool, args-hash)`` calls OR a short repeating
                          n-gram cycle of tool names.
2. ``no_progress``      — busy-but-not-advancing: >= N tool calls in the window
                          with zero file writes/edits and no completion marker.
3. ``repeated_tool_failure`` — the SAME tool errors >= M times in the window.
4. ``action_discrepancy``    — TRAIL tool-related hallucination, NARROW form: a
                          failed tool result immediately followed by the agent
                          continuing (another tool call / a completion) WITHOUT
                          a retry of the same tool or an acknowledgement of the
                          error. Lower precision -> lower severity, honest
                          wording ("agent continued after a failed command").

Each detector returns an incident dict (or ``None``):

    {
      "kind":          "stuck_loop" | "no_progress" | "repeated_tool_failure"
                       | "action_discrepancy",
      "session_id":    str,
      "runtime":       str,
      "severity":      "warning" | "info",
      "title":         plain-words headline ("codex looping: 38 tool calls, ..."),
      "detail":        one-sentence explanation incl. the Stop/Pause hint,
      "evidence":      small dict of the numbers behind the call,
      "first_bad_step": int | None,   # 0-based index into ``events`` of the
                                       # first event implicated (for localization
                                       # -> proxy pause/rollback later).
    }

``run_all`` runs every enabled detector and returns the incidents found, ordered
by severity (warning before info). Thresholds are module constants overridable
by env so the daemon can tune them without a code change.
"""
from __future__ import annotations

import hashlib
import json
import os
from typing import Any, Iterable, Optional

# ── Tunable thresholds (env-overridable) ─────────────────────────────────────
# How many newest events any detector will look at. Bounds CPU per session.
DETECT_EVENT_WINDOW = int(os.environ.get("CLAWMETRY_DETECT_WINDOW", "200"))

# stuck_loop: K consecutive identical (tool, args-hash) calls trips it.
STUCK_LOOP_IDENTICAL_K = int(os.environ.get("CLAWMETRY_LOOP_IDENTICAL_K", "3"))
# stuck_loop: a repeating tool-name n-gram cycle (cycle length<=this) that
# repeats at least STUCK_LOOP_CYCLE_REPEATS times also trips it.
STUCK_LOOP_MAX_CYCLE = int(os.environ.get("CLAWMETRY_LOOP_MAX_CYCLE", "4"))
STUCK_LOOP_CYCLE_REPEATS = int(os.environ.get("CLAWMETRY_LOOP_CYCLE_REPEATS", "3"))

# no_progress: >= N tool calls with zero writes/edits and no completion.
NO_PROGRESS_TOOL_CALLS = int(os.environ.get("CLAWMETRY_NOPROG_TOOLS", "20"))

# repeated_tool_failure: same tool errors >= M times in the window.
REPEATED_FAILURE_M = int(os.environ.get("CLAWMETRY_REPEAT_FAIL_M", "3"))

# action_discrepancy: how many *non-acknowledging* continuation steps after a
# failed result we require before flagging (>=1 = a single plow-ahead).
ACTION_DISCREPANCY_MIN = int(os.environ.get("CLAWMETRY_ACTION_DISCREPANCY_MIN", "1"))

# Tool names that indicate real progress (a file mutation). Lower-cased,
# substring-matched against the tool name so "Edit"/"str_replace_editor"/
# "apply_patch"/"write_file" all count. Tunable via env (comma-separated).
_DEFAULT_WRITE_TOOLS = (
    "write,edit,apply_patch,applypatch,str_replace,create_file,"
    "multiedit,notebookedit,patch_file,write_file,save_file"
)
WRITE_TOOL_SUBSTRINGS = tuple(
    s.strip().lower()
    for s in os.environ.get("CLAWMETRY_WRITE_TOOLS", _DEFAULT_WRITE_TOOLS).split(",")
    if s.strip()
)

# Substrings in tool-result text that, on their own, mark a failure even when no
# structured ``is_error`` flag is present (TRAIL System-Execution signals).
_FAILURE_TEXT_MARKERS = (
    "command not found", "no such file", "no such file or directory",
    "permission denied", "fatal:", "traceback (most recent call last)",
    "exit code 1", "exit status 1", "non-zero exit", "errno",
    "exception:", "segmentation fault", "connection refused", "timed out",
)

# ── Normalized event shape ───────────────────────────────────────────────────
# A detector never reasons over raw store rows directly. ``normalize_events``
# flattens the heterogenous on-the-wire shapes (top-level tool_call, OpenClaw v3
# model.completed+toolMetas, Claude-Code assistant+content blocks, family
# data.tool_calls arrays, tool_result/tool.result rows) into a flat, ordered
# list of NormStep dicts the heuristics scan:
#
#   {"i": int,              # index into the *original* event list (localization)
#    "kind": "tool_call" | "tool_result" | "text" | "user" | "end" | "other",
#    "tool": str,           # tool name (tool_call/tool_result), else ""
#    "args_hash": str,      # stable hash of normalized args (tool_call), else ""
#    "is_error": bool,      # tool_result only
#    "result_text": str,    # tool_result only (lower-cased, truncated)
#    "has_text": bool,      # text turn carrying a real reply (progress marker)
#   }

_TOPLEVEL_TOOL_CALL_TYPES = frozenset(
    {"tool_call", "tool_use", "toolcall", "tool.call", "tool.invoked"}
)
_TOOL_RESULT_TYPES = frozenset(
    {"tool_result", "tool-result", "tool.result", "tool.completed",
     "tool_use_result"}
)
_ASSISTANT_TYPES = frozenset(
    {"assistant", "message", "model.completed", "subagent:assistant"}
)
_USER_TYPES = frozenset({"user", "prompt.submitted", "subagent:user"})
_END_TYPES = frozenset(
    {"session.ended", "session.end", "session.completed",
     "session.stopped", "compaction"}
)


def _coerce_dict(data: Any) -> dict:
    """Best-effort dict from an event ``data`` field (dict, JSON string, junk).
    Never raises; returns ``{}`` when nothing usable."""
    if isinstance(data, dict):
        return data
    if isinstance(data, str):
        try:
            parsed = json.loads(data)
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            return {}
    return {}


def _args_hash(args: Any) -> str:
    """Stable short hash of a tool call's arguments. Order-insensitive for
    dicts (sorted keys) so logically-identical calls hash the same. Never
    raises — falls back to ``str`` then to an empty hash."""
    try:
        norm = json.dumps(args, sort_keys=True, separators=(",", ":"),
                          default=str)
    except Exception:
        try:
            norm = str(args)
        except Exception:
            return ""
    return hashlib.sha1(norm.encode("utf-8", "replace")).hexdigest()[:16]


def _iter_tool_calls_from_data(et: str, data: dict) -> list[dict]:
    """Yield ``{"tool": name, "args": value}`` for every tool invocation a
    single event describes. Covers all real shapes (top-level tool_call,
    OpenClaw v3 toolMetas, Claude-Code content tool_use blocks, family
    ``data.tool_calls`` arrays). Never raises."""
    out: list[dict] = []
    try:
        # Shape 1: top-level tool call event — name + args live on data.
        if et in _TOPLEVEL_TOOL_CALL_TYPES:
            name = data.get("tool") or data.get("tool_name") or data.get("name")
            args = (data.get("args") if data.get("args") is not None
                    else data.get("arguments") if data.get("arguments") is not None
                    else data.get("input"))
            if isinstance(name, str) and name:
                out.append({"tool": name, "args": args})
            # Some top-level rows still carry a tool_calls array; fall through.

        # Shape 2: family ``data.tool_calls`` array (claude_code/codex/cursor
        # event_type='tool_call' w/ data.tool_calls — the gap fixed in #2984).
        tcs = data.get("tool_calls")
        if isinstance(tcs, list):
            for tc in tcs:
                if not isinstance(tc, dict):
                    continue
                fn = tc.get("function") if isinstance(tc.get("function"), dict) else {}
                name = (tc.get("name") or tc.get("tool")
                        or fn.get("name"))
                args = (tc.get("args") if tc.get("args") is not None
                        else tc.get("arguments") if tc.get("arguments") is not None
                        else tc.get("input") if tc.get("input") is not None
                        else fn.get("arguments"))
                if isinstance(name, str) and name:
                    out.append({"tool": name, "args": args})

        # Shape 3: OpenClaw v3 ``toolMetas`` projection.
        metas = data.get("toolMetas")
        if isinstance(metas, list):
            for m in metas:
                if not isinstance(m, dict):
                    continue
                name = m.get("name") or m.get("tool")
                args = (m.get("args") if m.get("args") is not None
                        else m.get("arguments") if m.get("arguments") is not None
                        else m.get("input"))
                if isinstance(name, str) and name:
                    out.append({"tool": name, "args": args})

        # Shape 4: assistant ``message.content`` tool_use / toolCall blocks.
        msg = data.get("message") if isinstance(data.get("message"), dict) else None
        container = msg or data
        content = container.get("content")
        if isinstance(content, list):
            for blk in content:
                if not isinstance(blk, dict):
                    continue
                if str(blk.get("type") or "").lower() not in ("tool_use", "toolcall"):
                    continue
                name = blk.get("name") or blk.get("tool")
                args = (blk.get("input") if blk.get("input") is not None
                        else blk.get("arguments") if blk.get("arguments") is not None
                        else blk.get("args"))
                if isinstance(name, str) and name:
                    out.append({"tool": name, "args": args})
    except Exception:
        return out
    return out


def _result_text(data: dict) -> str:
    """Best-effort lower-cased text of a tool result for failure-marker
    matching. Walks ``output``/``result``/``content``/``details``/``stderr``.
    Truncated. Never raises."""
    try:
        for k in ("stderr", "error", "output", "result", "details"):
            v = data.get(k)
            if isinstance(v, str) and v.strip():
                return v[:2000].lower()
        content = data.get("content")
        if isinstance(content, str) and content.strip():
            return content[:2000].lower()
        if isinstance(content, list):
            parts = []
            for blk in content:
                if isinstance(blk, dict) and isinstance(blk.get("text"), str):
                    parts.append(blk["text"])
                elif isinstance(blk, str):
                    parts.append(blk)
            if parts:
                return (" ".join(parts))[:2000].lower()
        msg = data.get("message")
        if isinstance(msg, dict):
            return _result_text(msg)
    except Exception:
        pass
    return ""


def _structured_is_error(data: dict) -> Optional[bool]:
    """Return the structured error flag if the event carries one, else None.
    Covers ``is_error``/``isError``/``error``/non-zero exit codes."""
    for k in ("is_error", "isError"):
        if k in data:
            return bool(data.get(k))
    msg = data.get("message")
    if isinstance(msg, dict):
        for k in ("is_error", "isError"):
            if k in msg:
                return bool(msg.get(k))
    err = data.get("error")
    if err not in (None, "", False):
        return True
    for k in ("exit_code", "exitCode", "returncode", "exit_status"):
        if k in data:
            try:
                return int(data.get(k)) != 0
            except (TypeError, ValueError):
                continue
    return None


def _assistant_has_text(data: dict) -> bool:
    """True if an assistant/model turn carries a real text reply (progress
    marker, not a tool-only turn). Mirrors the stuck detector's logic."""
    msg = data.get("message") if isinstance(data.get("message"), dict) else data
    content = msg.get("content")
    if isinstance(content, str) and content.strip():
        return True
    if isinstance(content, list):
        for blk in content:
            if isinstance(blk, str) and blk.strip():
                return True
            if isinstance(blk, dict):
                bt = str(blk.get("type") or "").lower()
                if bt in ("text", "output_text") and str(blk.get("text") or "").strip():
                    return True
                if not bt and str(blk.get("text") or "").strip():
                    return True
    if isinstance(msg.get("text"), str) and msg["text"].strip():
        return True
    for k in ("completionText", "completion"):
        if isinstance(data.get(k), str) and data[k].strip():
            return True
    at = data.get("assistantTexts")
    if isinstance(at, list) and any(isinstance(t, str) and t.strip() for t in at):
        return True
    return False


def _event_role(data: dict) -> str:
    role = data.get("role")
    if not role and isinstance(data.get("message"), dict):
        role = data["message"].get("role")
    return str(role or "").strip().lower()


def normalize_events(events: Iterable[dict]) -> list[dict]:
    """Flatten heterogenous store events (newest-first OR oldest-first) into a
    flat, CHRONOLOGICAL (oldest-first) list of NormStep dicts. A single event
    can expand into multiple tool_call steps (multi-tool turns). Never raises;
    skips malformed events. Bounded by ``DETECT_EVENT_WINDOW``.

    Accepts the store's newest-first ``query_events`` output and reverses it so
    detectors reason forward in time. ``i`` on each step is the index into the
    chronological-ordered original event list (for first_bad_step localization).
    """
    evlist = [e for e in events if isinstance(e, dict)]
    # Cap to the newest window, then present oldest-first. query_events is
    # newest-first; if a caller already passes oldest-first that's fine too —
    # we sort by ts when available, else keep input order.
    evlist = evlist[:DETECT_EVENT_WINDOW]
    evlist = list(reversed(evlist))  # store gives newest-first -> chronological

    steps: list[dict] = []
    for i, ev in enumerate(evlist):
        et = str(ev.get("event_type") or "").strip().lower()
        data = _coerce_dict(ev.get("data"))
        role = _event_role(data)

        if et in _END_TYPES:
            steps.append({"i": i, "kind": "end", "tool": "", "args_hash": "",
                          "is_error": False, "result_text": "", "has_text": False})
            continue
        if et in _USER_TYPES or role == "user":
            steps.append({"i": i, "kind": "user", "tool": "", "args_hash": "",
                          "is_error": False, "result_text": "", "has_text": False})
            continue
        if et in _TOOL_RESULT_TYPES:
            txt = _result_text(data)
            sflag = _structured_is_error(data)
            # A structured True wins; otherwise (False or absent) fall back to
            # failure-text markers — adapters that set is_error=False but emit a
            # "command not found"/non-zero stderr are still real failures.
            is_err = bool(sflag) or _text_looks_failed(txt)
            tool = (data.get("tool") or data.get("tool_name") or data.get("name")
                    or "")
            steps.append({"i": i, "kind": "tool_result",
                          "tool": str(tool or ""), "args_hash": "",
                          "is_error": is_err, "result_text": txt,
                          "has_text": False})
            continue

        # Tool CALLS (top-level or hosted inside an assistant/model envelope).
        calls = _iter_tool_calls_from_data(et, data)
        if calls:
            for c in calls:
                steps.append({
                    "i": i, "kind": "tool_call",
                    "tool": str(c.get("tool") or ""),
                    "args_hash": _args_hash(c.get("args")),
                    "is_error": False, "result_text": "", "has_text": False,
                })
            continue

        # Assistant/model text turn with a real reply = a progress marker.
        if et in _ASSISTANT_TYPES or role == "assistant":
            if _assistant_has_text(data):
                steps.append({"i": i, "kind": "text", "tool": "", "args_hash": "",
                              "is_error": False, "result_text": "", "has_text": True})
                continue

        steps.append({"i": i, "kind": "other", "tool": "", "args_hash": "",
                      "is_error": False, "result_text": "", "has_text": False})
    return steps


def _text_looks_failed(text: str) -> bool:
    if not text:
        return False
    return any(m in text for m in _FAILURE_TEXT_MARKERS)


def _is_write_tool(tool: str) -> bool:
    t = (tool or "").lower()
    return any(sub in t for sub in WRITE_TOOL_SUBSTRINGS)


def _runtime_of(session_id: str) -> str:
    try:
        from clawmetry import waste_flags as _wf
        return _wf.runtime_from_session_id(session_id) or "openclaw"
    except Exception:
        return "openclaw"


def _stop_hint() -> str:
    return "You can Stop or Pause this agent from the ClawMetry dashboard or device."


# ── Detector 1: stuck_loop ───────────────────────────────────────────────────
def stuck_loop(events: Iterable[dict], session_id: str,
               runtime: Optional[str] = None) -> Optional[dict]:
    """Flag a session that is circling: either K consecutive identical
    ``(tool, args_hash)`` calls, or a short repeating n-gram cycle of tool
    names. TrajAD Type II (process inefficiency / circular loops). Pure,
    bounded, never raises."""
    try:
        steps = normalize_events(events)
        runtime = runtime or _runtime_of(session_id)
        calls = [s for s in steps if s["kind"] == "tool_call" and s["tool"]]
        if len(calls) < STUCK_LOOP_IDENTICAL_K:
            return None

        # (a) K consecutive identical (tool, args_hash). Track the longest run.
        best_run = 1
        run = 1
        best_end = 0
        for j in range(1, len(calls)):
            same = (calls[j]["tool"] == calls[j - 1]["tool"]
                    and calls[j]["args_hash"] == calls[j - 1]["args_hash"])
            run = run + 1 if same else 1
            if run > best_run:
                best_run = run
                best_end = j
        if best_run >= STUCK_LOOP_IDENTICAL_K:
            first_idx = calls[best_end - best_run + 1]["i"]
            tool = calls[best_end]["tool"]
            title = f"{runtime} looping: {best_run}x identical {tool} calls, no progress"
            return _incident(
                "stuck_loop", session_id, runtime, "warning", title,
                f"The agent repeated the same {tool} call {best_run} times in a row "
                f"without a different action. " + _stop_hint(),
                {"pattern": "identical", "tool": tool, "repeats": best_run,
                 "total_tool_calls": len(calls)},
                first_idx,
            )

        # (b) repeating tool-NAME n-gram cycle (e.g. A,B,A,B,A,B).
        names = [c["tool"] for c in calls]
        cyc = _find_repeating_cycle(names, STUCK_LOOP_MAX_CYCLE,
                                    STUCK_LOOP_CYCLE_REPEATS)
        if cyc is not None:
            cycle_tools, repeats, start = cyc
            first_idx = calls[start]["i"]
            label = "->".join(cycle_tools)
            title = (f"{runtime} looping: {label} cycle repeated {repeats}x, "
                     f"no progress")
            return _incident(
                "stuck_loop", session_id, runtime, "warning", title,
                f"The agent cycled through {label} {repeats} times without "
                f"breaking out. " + _stop_hint(),
                {"pattern": "cycle", "cycle": cycle_tools, "repeats": repeats,
                 "total_tool_calls": len(calls)},
                first_idx,
            )
        return None
    except Exception:
        return None


def _find_repeating_cycle(names: list[str], max_cycle: int,
                          min_repeats: int) -> Optional[tuple]:
    """Find the longest tail run that is a repeating cycle of length 2..max_cycle
    repeating >= min_repeats times. Returns ``(cycle_tools, repeats, start_idx)``
    or None. Scans from the END so we catch the *current* loop."""
    n = len(names)
    for clen in range(2, max_cycle + 1):
        if n < clen * min_repeats:
            continue
        # Walk backward counting how many times the last ``clen`` window repeats.
        cycle = names[n - clen:n]
        repeats = 1
        pos = n - clen
        while pos - clen >= 0 and names[pos - clen:pos] == cycle:
            repeats += 1
            pos -= clen
        if repeats >= min_repeats and len(set(cycle)) > 1:
            return (cycle, repeats, pos)
    return None


# ── Detector 2: no_progress ──────────────────────────────────────────────────
def no_progress(events: Iterable[dict], session_id: str,
                runtime: Optional[str] = None) -> Optional[dict]:
    """Flag a session accruing >= N tool calls in the window with ZERO file
    writes/edits and no completion/end marker since the last user turn (busy
    but not advancing). Pure, bounded, never raises."""
    try:
        steps = normalize_events(events)
        runtime = runtime or _runtime_of(session_id)
        # Only consider the tail since the most recent user turn or end marker —
        # a fresh prompt resets "progress". Walk from the end backward.
        tail: list[dict] = []
        for s in reversed(steps):
            if s["kind"] in ("user", "end"):
                break
            tail.append(s)
        tail.reverse()

        tool_calls = [s for s in tail if s["kind"] == "tool_call" and s["tool"]]
        if len(tool_calls) < NO_PROGRESS_TOOL_CALLS:
            return None
        wrote = any(_is_write_tool(s["tool"]) for s in tool_calls)
        if wrote:
            return None
        # An ``end`` in the tail would have broken the loop above, so reaching
        # here means no completion marker either.
        n = len(tool_calls)
        first_idx = tool_calls[0]["i"]
        title = f"{runtime}: {n} tool calls, no file changes, not advancing"
        return _incident(
            "no_progress", session_id, runtime, "warning", title,
            f"The agent has made {n} tool calls without writing or editing any "
            f"file and without finishing. It may be busy but not making "
            f"progress. " + _stop_hint(),
            {"tool_calls": n, "writes": 0},
            first_idx,
        )
    except Exception:
        return None


# ── Detector 3: repeated_tool_failure ────────────────────────────────────────
def repeated_tool_failure(events: Iterable[dict], session_id: str,
                          runtime: Optional[str] = None) -> Optional[dict]:
    """Flag when the SAME tool returns an error >= M times in the window.
    A tool_result with no ``tool`` name is attributed to the most recent
    preceding tool_call's tool. Pure, bounded, never raises."""
    try:
        steps = normalize_events(events)
        runtime = runtime or _runtime_of(session_id)
        counts: dict[str, int] = {}
        first_idx_by_tool: dict[str, int] = {}
        last_call_tool = ""
        worst_tool = ""
        for s in steps:
            if s["kind"] == "tool_call" and s["tool"]:
                last_call_tool = s["tool"]
            elif s["kind"] == "tool_result" and s["is_error"]:
                tool = s["tool"] or last_call_tool or "tool"
                counts[tool] = counts.get(tool, 0) + 1
                first_idx_by_tool.setdefault(tool, s["i"])
                if not worst_tool or counts[tool] > counts.get(worst_tool, 0):
                    worst_tool = tool
        if not worst_tool or counts.get(worst_tool, 0) < REPEATED_FAILURE_M:
            return None
        fails = counts[worst_tool]
        title = f"{worst_tool} failed {fails} times"
        return _incident(
            "repeated_tool_failure", session_id, runtime, "warning", title,
            f"The {worst_tool} tool returned an error {fails} times in this "
            f"session. The agent may be stuck on a failing step. " + _stop_hint(),
            {"tool": worst_tool, "failures": fails},
            first_idx_by_tool.get(worst_tool),
        )
    except Exception:
        return None


# ── Detector 4: action_discrepancy (NARROW, honest hallucination signal) ──────
def action_discrepancy(events: Iterable[dict], session_id: str,
                       runtime: Optional[str] = None) -> Optional[dict]:
    """Flag the defensible "agent proceeded as if a failed tool succeeded" case
    (TRAIL tool-related hallucination branch): a tool_result indicating FAILURE
    immediately followed by the agent continuing (another tool call OR a
    completion) WITHOUT retrying the SAME tool and WITHOUT acknowledging the
    error.

    HEURISTIC AND LOWER-PRECISION by construction — a benign "continue" that
    actually does handle the error (e.g. a different recovery tool) can trip it,
    and a real acknowledgement only in prose between turns is hard to see. So
    this is severity 'info', and the wording never claims "hallucination" with
    false confidence. Pure, bounded, never raises."""
    try:
        steps = normalize_events(events)
        runtime = runtime or _runtime_of(session_id)
        n = len(steps)
        last_call_tool = ""
        last_call_hash = ""
        for idx in range(n - 1):
            s = steps[idx]
            if s["kind"] == "tool_call" and s["tool"]:
                last_call_tool = s["tool"]
                last_call_hash = s["args_hash"]
            if not (s["kind"] == "tool_result" and s["is_error"]):
                continue
            # Attribute the failed call's tool/args (result rows often omit the
            # tool name -> fall back to the most recent preceding call).
            failed_tool = s["tool"] or last_call_tool
            failed_hash = last_call_hash
            # Look at the NEXT meaningful step (skip 'other'/non-events).
            nxt = None
            for j in range(idx + 1, n):
                if steps[j]["kind"] in ("tool_call", "text", "end", "user"):
                    nxt = steps[j]
                    break
            if nxt is None:
                continue
            # A user turn means the human stepped in -> not the agent plowing on.
            if nxt["kind"] == "user":
                continue
            # A follow-up with the SAME tool = a retry / recovery attempt on the
            # same operation. Suppress (keeps precision high) regardless of args:
            # distinguishing "retry" from "different same-tool action" reliably
            # is not possible from the trajectory alone, so we err toward NOT
            # flagging. The defensible plow-ahead is a switch to a DIFFERENT tool
            # (or a completion) right after a failure with no reasoning beat.
            if (nxt["kind"] == "tool_call" and failed_tool
                    and nxt["tool"] == failed_tool):
                continue
            _ = failed_hash  # reserved for a future tighter same-tool heuristic
            # A text turn whose reply *mentions* the error/retry = acknowledged.
            if nxt["kind"] == "text":
                # We cannot see the text content in a NormStep, but a text turn
                # between the failure and the next action is itself a reasoning
                # beat — treat it as a (weak) acknowledgement and do NOT flag.
                continue
            # Otherwise: a NEW tool call or a completion right after a failure,
            # with no retry and no reasoning beat -> the narrow discrepancy.
            if nxt["kind"] in ("tool_call", "end"):
                cont = "ran another command" if nxt["kind"] == "tool_call" \
                    else "marked the task done"
                tool_label = failed_tool or "a command"
                title = "agent continued after a failed command"
                return _incident(
                    "action_discrepancy", session_id, runtime, "info", title,
                    f"After {tool_label} failed, the agent {cont} without "
                    f"retrying or acknowledging the error. This may mean it "
                    f"proceeded as if the step had succeeded. " + _stop_hint(),
                    {"failed_tool": tool_label, "continued_as": nxt["kind"]},
                    s["i"],
                )
        return None
    except Exception:
        return None


# ── Orchestration ────────────────────────────────────────────────────────────
_ALL_DETECTORS = (
    stuck_loop,
    no_progress,
    repeated_tool_failure,
    action_discrepancy,
)

_SEVERITY_RANK = {"warning": 0, "info": 1}


def run_all(events: Iterable[dict], session_id: str,
            runtime: Optional[str] = None) -> list[dict]:
    """Run every detector over a session's recent events and return the
    incidents found, ordered by severity (warning first). ``events`` is the
    store's newest-first ``query_events`` output. Materializes ``events`` once
    so the iterator is reusable across detectors. Never raises."""
    try:
        evlist = list(events)
    except Exception:
        return []
    rt = runtime or _runtime_of(session_id)
    out: list[dict] = []
    for det in _ALL_DETECTORS:
        try:
            inc = det(evlist, session_id, rt)
        except Exception:
            inc = None
        if inc:
            out.append(inc)
    out.sort(key=lambda c: _SEVERITY_RANK.get(c.get("severity"), 9))
    return out


def _incident(kind: str, session_id: str, runtime: str, severity: str,
              title: str, detail: str, evidence: dict,
              first_bad_step: Optional[int]) -> dict:
    return {
        "kind": kind,
        "session_id": session_id,
        "runtime": runtime,
        "severity": severity,
        "title": title,
        "detail": detail,
        "evidence": evidence,
        "first_bad_step": first_bad_step,
    }
