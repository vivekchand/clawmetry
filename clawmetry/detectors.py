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

Eleven detectors in three families. TRAJECTORY (is it stuck?) reads the shape
of the tool stream and lives here. BEHAVIOUR (is it doing something it does
not normally do?) reads what the calls DID and lives in ``detector_behaviour``:
``file_blast_radius``, ``credential_access``, ``network_egress``,
``privilege_change``. Those read tool ARGUMENTS rather than syscalls, and every
incident says so. SILENT FAILURE (it stopped, and nobody was told) lives here
too, defined and registered in ``_ALL_DETECTORS`` below: ``rate_limited``
(HTTP 429/529 or rate-limit / overloaded / quota text on tool results and API
error events), ``blocked_on_user`` (a pending approval for the session, or an
unanswered question / permission request with the session idle past a
threshold), ``crashed`` (>= 2 session (re)starts inside a short window,
matching the outcome classifier's ``crash-loop`` tag). Thresholds are resolved
in ``detector_calibration``; what a finding costs is computed in
``detector_money``.

The four trajectory detectors:

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

# New in this change, each in its own module so the whole of the new capability
# is readable in one place and this file keeps its shape.
from clawmetry.detector_calibration import (  # noqa: F401
    BASELINE_CEIL_RATIO, BASELINE_FLOOR_RATIO, BASELINE_MIN_SESSIONS,
    BASELINE_SIGMA, BLAST_RADIUS_FILES, EGRESS_HOST_FANOUT, RUNTIME_PROFILES,
    resolve_thresholds,
)
from clawmetry.detector_surface import (  # noqa: F401
    _MUTATING_CMD_RE, _REDIRECT_WRITE_RE, _action_surface, _cmd_sketch,
    _hosts_from_text, _is_inspect_only, _redact_path, _strip_heredocs,
)
from clawmetry.detector_money import (  # noqa: F401
    CRITICAL_SPEND_USD, _SEVERITY_RANK, _severity_promote, annotate_spend,
    incident_rank, sort_incidents,
)
from clawmetry.detector_behaviour import (  # noqa: F401
    credential_access, file_blast_radius, network_egress, privilege_change,
)

# What this module detects, declared once and up front rather than derived at
# the bottom of the file. Two reasons it is a literal:
#
#   * a reader (or a reviewer, or a tool) can learn the module's surface from
#     its head instead of executing it;
#   * it makes the registry guard real. Deriving this FROM ``_ALL_DETECTORS``
#     and then asserting the two agree is a tautology that cannot catch a
#     detector dropped from the registry. With a literal, that test compares
#     two independently maintained facts, which is the only version of it
#     worth running.
DETECTOR_KINDS = (
    # Trajectory: is this agent stuck?
    "stuck_loop",
    "no_progress",
    "repeated_tool_failure",
    "action_discrepancy",
    # Behaviour: is it doing something it does not normally do?
    "file_blast_radius",
    "credential_access",
    "network_egress",
    "privilege_change",
    # Silent failure: it stopped, and nobody was told.
    "rate_limited",
    "blocked_on_user",
    "crashed",
)


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
                tool = str(c.get("tool") or "")
                paths, cmd, hosts = _action_surface(tool, c.get("args"))
                steps.append({
                    "i": i, "kind": "tool_call",
                    "tool": tool,
                    "args_hash": _args_hash(c.get("args")),
                    "is_error": False, "result_text": "", "has_text": False,
                    # What the call touched; the behavioural detectors read these.
                    "paths": paths, "cmd": cmd, "hosts": hosts,
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


def _is_write_tool(tool: str, write_tools=None) -> bool:
    """Does this tool NAME mean a file mutation?

    ``write_tools`` is the resolved per-runtime vocabulary (the global default
    plus the runtime profile's additions). Passing None keeps the old global
    behaviour so existing callers are unaffected.
    """
    t = (tool or "").lower()
    vocab = write_tools if write_tools else WRITE_TOOL_SUBSTRINGS
    return any(sub in t for sub in vocab)

def _step_mutates(step: dict, write_tools=None) -> bool:
    """Did this step change a file — by tool name OR by shell command?

    The second half is what makes ``no_progress`` correct for shell-first
    runtimes (codex, picoclaw, nanoclaw and anything else whose edits happen
    inside ``shell``/``exec``). Before this, a codex session that wrote code
    through a heredoc looked identical to one that spun for an hour, because
    neither produced a tool call whose NAME matched a write verb.
    """
    if step.get("kind") != "tool_call":
        return False
    if _is_write_tool(step.get("tool") or "", write_tools):
        return True
    cmd = step.get("cmd") or ""
    if not cmd:
        return False
    return bool(_MUTATING_CMD_RE.search(cmd) or _REDIRECT_WRITE_RE.search(cmd))

def _prepare(events, steps, thresholds, runtime, session_id):
    """Shared detector preamble: resolve the runtime, its thresholds, and the
    normalized steps exactly once when the caller has already done the work."""
    rt = runtime or _runtime_of(session_id)
    th = thresholds if isinstance(thresholds, dict) else resolve_thresholds(rt)
    st = steps if steps is not None else normalize_events(events)
    return rt, th, st

def session_profile(steps: list, write_tools=None) -> dict:
    """Summarize one session for the cohort baseline it feeds.

    Takes already-normalized steps (the daemon has them; re-parsing 200 events
    to count them would double the tick cost for nothing) and returns the four
    numbers ``record_guard_observation`` stores: how many tool calls, how many
    distinct files mutated, whether it wrote at all, and which external hosts
    it reached.

    This is the loop that closes gap 03: today's sessions decide what counts as
    unusual tomorrow. Never raises — an empty profile just means this session
    teaches the baseline nothing.
    """
    out = {"tool_calls": 0, "write_files": 0, "wrote": False, "hosts": []}
    try:
        files = set()
        hosts = set()
        calls = 0
        for st in steps or []:
            if not isinstance(st, dict):
                continue
            for h in st.get("hosts") or ():
                hosts.add(h)
            if st.get("kind") != "tool_call" or not st.get("tool"):
                continue
            calls += 1
            if _step_mutates(st, write_tools):
                out["wrote"] = True
                for p in st.get("paths") or ():
                    files.add(p)
        out["tool_calls"] = calls
        out["write_files"] = len(files)
        out["hosts"] = sorted(hosts)[:64]
    except Exception:
        return out
    return out


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
               runtime: Optional[str] = None, *, thresholds: Optional[dict] = None,
               steps: Optional[list] = None,
               facts: Optional[dict] = None) -> Optional[dict]:
    """Flag a session that is circling: either K consecutive identical
    ``(tool, args_hash)`` calls, or a short repeating n-gram cycle of tool
    names. TrajAD Type II (process inefficiency / circular loops). Pure,
    bounded, never raises."""
    try:
        runtime, th, steps = _prepare(events, steps, thresholds, runtime, session_id)
        identical_k = int(th["identical_k"])
        calls = [s for s in steps if s["kind"] == "tool_call" and s["tool"]]
        if len(calls) < identical_k:
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
        if best_run >= identical_k:
            first_idx = calls[best_end - best_run + 1]["i"]
            tool = calls[best_end]["tool"]
            title = f"{runtime} looping: {best_run}x identical {tool} calls, no progress"
            return _incident(
                "stuck_loop", session_id, runtime, "warning", title,
                f"The agent repeated the same {tool} call {best_run} times in a row "
                f"without a different action. " + _stop_hint(),
                {"pattern": "identical", "tool": tool, "repeats": best_run,
                 "total_tool_calls": len(calls),
                 "threshold": identical_k,
                 "threshold_source": th["sources"]["identical_k"]},
                first_idx,
            )

        # (b) repeating tool-NAME n-gram cycle (e.g. A,B,A,B,A,B).
        names = [c["tool"] for c in calls]
        cyc = _find_repeating_cycle(names, int(th["max_cycle"]),
                                    int(th["cycle_repeats"]))
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
                 "total_tool_calls": len(calls),
                 "threshold": int(th["cycle_repeats"]),
                 "threshold_source": th["sources"]["cycle_repeats"]},
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
                runtime: Optional[str] = None, *, thresholds: Optional[dict] = None,
                steps: Optional[list] = None,
                facts: Optional[dict] = None) -> Optional[dict]:
    """Flag a session accruing >= N tool calls in the window with ZERO file
    writes/edits and no completion/end marker since the last user turn (busy
    but not advancing). Pure, bounded, never raises."""
    try:
        runtime, th, steps = _prepare(events, steps, thresholds, runtime, session_id)
        if not th.get("no_progress_enabled", True):
            # This cohort has never once shown us a file write across a real
            # sample of sessions, so "zero writes" is a fact about our
            # visibility, not about the agent. Firing here would flag every
            # session that runtime ever runs.
            return None
        # Only consider the tail since the most recent user turn or end marker —
        # a fresh prompt resets "progress". Walk from the end backward.
        tail: list[dict] = []
        for s in reversed(steps):
            if s["kind"] in ("user", "end"):
                break
            tail.append(s)
        tail.reverse()

        tool_calls = [s for s in tail if s["kind"] == "tool_call" and s["tool"]]
        threshold = int(th["no_progress_tools"])
        if len(tool_calls) < threshold:
            return None
        wrote = any(_step_mutates(s, th.get("write_tools")) for s in tool_calls)
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
            {"tool_calls": n, "writes": 0, "threshold": threshold,
             "threshold_source": th["sources"]["no_progress_tools"],
             "baseline": th.get("baseline", {}).get("tool_calls")},
            first_idx,
        )
    except Exception:
        return None


# ── Detector 3: repeated_tool_failure ────────────────────────────────────────
def repeated_tool_failure(events: Iterable[dict], session_id: str,
                          runtime: Optional[str] = None, *,
                          thresholds: Optional[dict] = None,
                          steps: Optional[list] = None,
                          facts: Optional[dict] = None) -> Optional[dict]:
    """Flag when the SAME tool returns an error >= M times in the window.
    A tool_result with no ``tool`` name is attributed to the most recent
    preceding tool_call's tool. Pure, bounded, never raises."""
    try:
        runtime, th, steps = _prepare(events, steps, thresholds, runtime, session_id)
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
        if not worst_tool or counts.get(worst_tool, 0) < int(th["repeat_fail_m"]):
            return None
        fails = counts[worst_tool]
        title = f"{worst_tool} failed {fails} times"
        return _incident(
            "repeated_tool_failure", session_id, runtime, "warning", title,
            f"The {worst_tool} tool returned an error {fails} times in this "
            f"session. The agent may be stuck on a failing step. " + _stop_hint(),
            {"tool": worst_tool, "failures": fails,
             "threshold": int(th["repeat_fail_m"]),
             "threshold_source": th["sources"]["repeat_fail_m"]},
            first_idx_by_tool.get(worst_tool),
        )
    except Exception:
        return None


# ── Detector 4: action_discrepancy (NARROW, honest hallucination signal) ──────
def action_discrepancy(events: Iterable[dict], session_id: str,
                       runtime: Optional[str] = None, *,
                       thresholds: Optional[dict] = None,
                       steps: Optional[list] = None,
                       facts: Optional[dict] = None) -> Optional[dict]:
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
        runtime, th, steps = _prepare(events, steps, thresholds, runtime, session_id)
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

# ── Silent-failure detectors ─────────────────────────────────────────────────
# The three ways an agent stops without telling anyone: the provider refused
# it (rate limited), it is waiting on a human who does not know (blocked on
# user), or it died and came back (crashed). None of these are stuck loops, so
# the trajectory detectors above stay quiet on all three. Runtime-neutral:
# they read the store's event stream and the facts the daemon already has,
# never a runtime-specific hook.

_RATE_LIMIT_MARKERS = (
    "rate limit", "rate_limit", "ratelimit", "too many requests",
    "overloaded", "overloaded_error", "quota exceeded", "quota_exceeded",
    "insufficient_quota", "resource_exhausted", "resource has been exhausted",
    "429",
)
_RATE_LIMIT_STATUSES = frozenset({429, 529})
_API_ERROR_TYPES = frozenset({
    "error", "api.error", "api_error", "model.error", "model_error",
    "llm.error", "llm_error", "request.error", "request_failed",
    "provider.error", "agent.error", "session.error",
})
_BLOCKED_EVENT_TYPES = frozenset({
    "approval.requested", "approval_requested", "approval.pending",
    "permission.request", "permission_request", "permissionrequest",
    "tool.blocked_on_user", "blocked_on_user", "hitl.pending",
    "ask_user", "askuserquestion", "ask_user_question", "user_input_requested",
    "elicitation", "notification",
})
_BLOCKED_TOOL_NAMES = frozenset({
    "askuserquestion", "ask_user_question", "ask_user", "request_permission",
    "elicit", "elicitation",
})
_RESTART_TYPES = frozenset({"session.started", "session.restarted",
                            "session.reset"})


def _parse_ts(value: Any) -> Optional[float]:
    """Epoch seconds for the store's ISO ``ts`` strings; None when unparsable."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value) / (1000.0 if value > 1e11 else 1.0)
    txt = str(value).strip()
    if not txt:
        return None
    try:
        from datetime import datetime, timezone
        if txt.endswith("Z") or txt.endswith("z"):
            txt = txt[:-1] + "+00:00"
        dt = datetime.fromisoformat(txt)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.timestamp()
    except Exception:
        return None


def _status_code(data: dict) -> Optional[int]:
    """An HTTP-ish status carried on the event, if any."""
    for holder in (data, data.get("error") if isinstance(data.get("error"), dict) else {},
                   data.get("response") if isinstance(data.get("response"), dict) else {}):
        if not isinstance(holder, dict):
            continue
        for k in ("status", "status_code", "statusCode", "http_status", "code"):
            v = holder.get(k)
            if isinstance(v, bool):
                continue
            try:
                n = int(v)
            except (TypeError, ValueError):
                continue
            if 100 <= n <= 599:
                return n
    return None


def _chronological(events: Iterable[dict]) -> list[dict]:
    evlist = [e for e in events if isinstance(e, dict)][:DETECT_EVENT_WINDOW]
    return list(reversed(evlist))


def _looks_rate_limited(data: dict, text: str) -> bool:
    code = _status_code(data)
    if code in _RATE_LIMIT_STATUSES:
        return True
    err = data.get("error")
    if isinstance(err, dict):
        etype = str(err.get("type") or err.get("code") or "").lower()
        if any(m in etype for m in ("rate_limit", "overloaded", "quota",
                                     "resource_exhausted")):
            return True
    t = (text or "").lower()
    if not t:
        return False
    # "429" alone matches version strings and byte counts; require a word
    # boundary-ish context so "b429" or "1429" do not count.
    for m in _RATE_LIMIT_MARKERS:
        if m == "429":
            import re
            if re.search(r"(?<![\w.])429(?![\w])", t):
                return True
            continue
        if m in t:
            return True
    return False


# ── Detector 9: rate_limited ─────────────────────────────────────────────────
def rate_limited(events: Iterable[dict], session_id: str,
                 runtime: Optional[str] = None, *,
                 thresholds: Optional[dict] = None,
                 steps: Optional[list] = None,
                 facts: Optional[dict] = None) -> Optional[dict]:
    """Flag when the provider or a tool refused the agent >= N times for
    capacity reasons: HTTP 429/529, or result text saying rate limit,
    overloaded, quota, too many requests. Reads tool results AND explicit
    API-error events, because a model refusal is not a tool result. Pure,
    bounded, never raises."""
    try:
        runtime, th, steps = _prepare(events, steps, thresholds, runtime, session_id)
        evlist = _chronological(events)
        hits: list[int] = []
        sample = ""
        seen_idx: set = set()
        # (a) tool results the normalizer already read.
        for s in steps:
            if s.get("kind") != "tool_result":
                continue
            i = s.get("i")
            data = _coerce_dict((evlist[i] or {}).get("data")) if isinstance(i, int) and 0 <= i < len(evlist) else {}
            if _looks_rate_limited(data, s.get("result_text") or ""):
                hits.append(i)
                seen_idx.add(i)
                if not sample:
                    sample = (s.get("result_text") or "")[:120]
        # (b) explicit API / model error events (not tool results).
        for i, ev in enumerate(evlist):
            if i in seen_idx:
                continue
            et = str(ev.get("event_type") or "").strip().lower()
            data = _coerce_dict(ev.get("data"))
            is_err_type = et in _API_ERROR_TYPES or et.endswith(".error") or et.endswith("_error")
            if not is_err_type and _status_code(data) not in _RATE_LIMIT_STATUSES:
                continue
            txt = _result_text(data)
            if not txt and isinstance(data.get("error"), dict):
                txt = str(data["error"].get("message") or "").lower()
            if _looks_rate_limited(data, txt):
                hits.append(i)
                if not sample:
                    sample = txt[:120]
        need = int(th.get("rate_limit_min") or 2)
        if len(hits) < need:
            return None
        hits.sort()
        rt_label = runtime or "agent"
        title = f"{rt_label} is being rate limited ({len(hits)} refusals)"
        return _incident(
            "rate_limited", session_id, runtime, "warning", title,
            f"The model provider or a tool refused {len(hits)} requests for "
            f"capacity reasons (429, overloaded, quota). The agent may be "
            f"retrying quietly or has stopped making progress. Check the "
            f"provider's status page and your plan limits. " + _stop_hint(),
            {"refusals": len(hits), "threshold": need,
             "threshold_source": th["sources"].get("rate_limit_min", "static"),
             "observed": "HTTP 429/529 status or rate-limit text on tool "
                         "results and API error events",
             "sample": sample},
            hits[0],
        )
    except Exception:
        return None


# ── Detector 10: blocked_on_user ─────────────────────────────────────────────
def blocked_on_user(events: Iterable[dict], session_id: str,
                    runtime: Optional[str] = None, *,
                    thresholds: Optional[dict] = None,
                    steps: Optional[list] = None,
                    facts: Optional[dict] = None) -> Optional[dict]:
    """Flag when the agent is waiting on a human who may not know.

    Two honest sources, either is enough:
      * ``facts["pending_approvals"]`` > 0: an approval for this session sits
        in ClawMetry's approvals table (any runtime that routes approvals
        through us, including OpenClaw's HITL and the Claude Code mirror);
      * the LAST meaningful event is a question or permission request (an
        AskUserQuestion-style tool call or a blocked/permission event type)
        with no user reply after it, and the session has been idle for at
        least ``blocked_wait_sec`` (``facts["idle_seconds"]``).

    A prompt answered within two minutes is a conversation, not an incident,
    so without an idle measurement this detector only fires on the approvals
    table. Never guesses. Pure, never raises."""
    try:
        runtime, th, steps = _prepare(events, steps, thresholds, runtime, session_id)
        f = facts if isinstance(facts, dict) else {}
        wait_need = int(th.get("blocked_wait_sec") or 120)
        try:
            pending = int(f.get("pending_approvals") or 0)
        except (TypeError, ValueError):
            pending = 0
        try:
            idle = float(f.get("idle_seconds") or 0.0)
        except (TypeError, ValueError):
            idle = 0.0
        rt_label = runtime or "agent"

        if pending > 0:
            title = f"{rt_label} is waiting for your approval"
            return _incident(
                "blocked_on_user", session_id, runtime, "warning", title,
                f"{pending} approval request(s) for this session are pending "
                f"in the ClawMetry approvals queue. The agent cannot continue "
                f"until someone answers. Open the Approvals tab to respond.",
                {"pending_approvals": pending, "idle_seconds": int(idle),
                 "threshold": 1, "threshold_source": "static",
                 "observed": "pending rows in the approvals table for this session"},
                None,
            )

        # Runtime event path: find the last question / permission request and
        # make sure nothing from the user followed it.
        evlist = _chronological(events)
        ask_idx = None
        ask_what = ""
        for i, ev in enumerate(evlist):
            et = str(ev.get("event_type") or "").strip().lower()
            data = _coerce_dict(ev.get("data"))
            if et in _USER_TYPES or _event_role(data) == "user":
                ask_idx = None  # a human answered; nothing pending before here
                continue
            if et in _BLOCKED_EVENT_TYPES:
                # Claude Code "notification" hooks carry many messages; only
                # the ones that are a request for input count.
                if et == "notification":
                    ntype = str(data.get("notification_type")
                                or data.get("type") or "").lower()
                    msg = str(data.get("message") or "").lower()
                    if not ("permission" in ntype or "idle" in ntype
                            or "waiting for" in msg or "permission" in msg):
                        continue
                ask_idx, ask_what = i, et
                continue
            for c in _iter_tool_calls_from_data(et, data):
                if str(c.get("tool") or "").strip().lower() in _BLOCKED_TOOL_NAMES:
                    ask_idx, ask_what = i, str(c.get("tool") or "")
        if ask_idx is None:
            return None
        # Anything after the ask that is a tool result or an assistant reply
        # means the agent moved on (the question was answered out of band).
        for s in steps:
            if isinstance(s.get("i"), int) and s["i"] > ask_idx and s.get("kind") in ("tool_result", "text", "tool_call"):
                if s.get("kind") == "tool_call" and str(s.get("tool") or "").lower() in _BLOCKED_TOOL_NAMES:
                    continue
                return None
        if idle < wait_need:
            return None
        mins = int(idle // 60)
        title = f"{rt_label} is waiting for you ({mins} min)"
        return _incident(
            "blocked_on_user", session_id, runtime, "warning", title,
            f"The agent asked a question or requested permission "
            f"({ask_what}) and has been waiting about {mins} minute(s) with "
            f"no reply. Nothing will happen until someone answers it in the "
            f"terminal or the runtime's UI.",
            {"pending_approvals": 0, "idle_seconds": int(idle),
             "threshold": wait_need,
             "threshold_source": th["sources"].get("blocked_wait_sec", "static"),
             "observed": f"last event is a {ask_what} request with no user reply after it",
             "asked_via": ask_what},
            ask_idx,
        )
    except Exception:
        return None


# ── Detector 11: crashed ─────────────────────────────────────────────────────
def crashed(events: Iterable[dict], session_id: str,
            runtime: Optional[str] = None, *,
            thresholds: Optional[dict] = None,
            steps: Optional[list] = None,
            facts: Optional[dict] = None) -> Optional[dict]:
    """Flag when a session (re)started >= N times inside a short window: the
    process died and came back, or is crash-looping. Mirrors the outcome
    classifier's ``crash-loop`` impact tag (two restarts) so the two views
    agree. With unparsable timestamps the count over the event window is
    used and the evidence says so. Pure, never raises."""
    try:
        runtime, th, steps = _prepare(events, steps, thresholds, runtime, session_id)
        evlist = _chronological(events)
        restarts: list[tuple[int, Optional[float]]] = []
        for i, ev in enumerate(evlist):
            et = str(ev.get("event_type") or "").strip().lower()
            if et in _RESTART_TYPES:
                restarts.append((i, _parse_ts(ev.get("ts"))))
        need = int(th.get("crash_restarts") or 2)
        window = int(th.get("crash_window_sec") or 900)
        if len(restarts) < need:
            return None
        # Best run of >= need restarts inside ``window`` seconds. If any ts is
        # missing we fall back to the raw count and say so.
        timed = [(i, t) for i, t in restarts if t is not None]
        basis = "timestamps"
        first_idx = restarts[0][0]
        count = 0
        span = None
        if len(timed) == len(restarts):
            best = 0
            for a in range(len(timed)):
                b = a
                while b + 1 < len(timed) and timed[b + 1][1] - timed[a][1] <= window:
                    b += 1
                run = b - a + 1
                if run > best:
                    best = run
                    first_idx = timed[a][0]
                    span = timed[b][1] - timed[a][1]
            count = best
            if count < need:
                return None
        else:
            basis = "event_window"
            count = len(restarts)
        rt_label = runtime or "agent"
        if span is not None:
            when = f"in {max(1, int(round(span / 60.0)))} min"
        else:
            when = f"in the last {len(evlist)} events"
        title = f"{rt_label} restarted {count} times {when}"
        return _incident(
            "crashed", session_id, runtime, "warning", title,
            f"This session started over {count} times {when}. That usually "
            f"means the agent process crashed and was relaunched, or is "
            f"stuck in a restart loop. Check the runtime's own logs for the "
            f"exit reason. " + _stop_hint(),
            {"restarts": count, "threshold": need, "window_sec": window,
             "threshold_source": th["sources"].get("crash_restarts", "static"),
             "observed": f"session.started/restarted events counted by {basis}",
             "span_sec": int(span) if span is not None else None},
            first_idx,
        )
    except Exception:
        return None


_ALL_DETECTORS = (
    # Trajectory shape: is this agent stuck?
    stuck_loop,
    no_progress,
    repeated_tool_failure,
    action_discrepancy,
    # Behaviour: is this agent doing something it does not normally do?
    file_blast_radius,
    credential_access,
    network_egress,
    privilege_change,
    # Silent failure: it stopped, and nobody was told.
    rate_limited,
    blocked_on_user,
    crashed,
)

def run_all(events: Iterable[dict], session_id: str,
            runtime: Optional[str] = None, *,
            facts: Optional[dict] = None,
            baseline: Optional[dict] = None,
            thresholds: Optional[dict] = None,
            steps: Optional[list] = None) -> list[dict]:
    """Run every detector over a session's recent events and return the
    incidents found, most expensive to ignore first.

    ``events`` is the store's newest-first ``query_events`` output.
    ``facts`` carries what the detectors cannot see for themselves —
    ``cost_usd``, ``bad_for_seconds``, ``session_seconds``, ``cwd``.
    ``baseline`` is this cohort's learned normal (see
    ``local_store.query_guard_baseline``); absent, static thresholds apply.

    Normalization happens ONCE here and is shared with every detector, so
    adding detectors five through eight did not multiply the per-tick cost by
    two — the parse was always the expensive part.

    Never raises.
    """
    try:
        evlist = list(events)
    except Exception:
        return []
    rt = runtime or _runtime_of(session_id)
    th = thresholds if isinstance(thresholds, dict) else resolve_thresholds(rt, baseline)
    if steps is None:
        try:
            steps = normalize_events(evlist)
        except Exception:
            steps = []
    f = facts if isinstance(facts, dict) else {}

    out: list[dict] = []
    for det in _ALL_DETECTORS:
        try:
            inc = det(evlist, session_id, rt, thresholds=th, steps=steps, facts=f)
        except Exception:
            inc = None
        if inc:
            out.append(inc)

    return annotate_spend(
        out,
        cost_usd=f.get("cost_usd") or 0.0,
        bad_for_seconds=f.get("bad_for_seconds") or 0.0,
        session_seconds=f.get("session_seconds") or 0.0,
        window_steps=len(steps),
    )


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
