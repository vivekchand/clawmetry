"""clawmetry/detectors.py: research-backed, judge-free, CPU-cheap anomaly
detectors over a session's recent event sequence (issue #2999, extended #5168).

Design basis (the agent-observability deep-research memo + TrajAD / TRAIL /
MAST taxonomies): zero-shot LLM judges are near-useless at localizing the bad
step and 17-27x slower; naive embedding-outlier heuristics dilute the single
anomalous step. What is load-bearing is *sequence structure*. So this module is
a set of small, explainable, bounded heuristics over the ordered tool/result
stream, NOT an expensive judge. Each detector is pure (no I/O, no store, no
clock dependence beyond what the caller passes), operates on the last ``W``
events, never crashes on malformed events, and returns a structured incident.

EIGHT detectors, in two families that ask different questions.

**Trajectory: is this agent stuck?** (the shape of the tool stream)

1. ``stuck_loop``       TrajAD Type II (circular loops / repeated identical
                        tool calls): K consecutive identical
                        ``(tool, args-hash)`` calls OR a short repeating
                        n-gram cycle of tool names.
2. ``no_progress``      busy-but-not-advancing: >= N tool calls in the window
                        with zero file mutations and no completion marker.
3. ``repeated_tool_failure``  the SAME tool errors >= M times in the window.
4. ``action_discrepancy``     TRAIL tool-related hallucination, NARROW form: a
                        failed tool result immediately followed by the agent
                        continuing (another tool call / a completion) WITHOUT
                        a retry of the same tool or an acknowledgement of the
                        error. Lower precision -> lower severity, honest
                        wording ("agent continued after a failed command").

**Behaviour: is this agent doing something it does not normally do?** (what the
calls actually DID, read from their arguments)

5. ``file_blast_radius``  more distinct files mutated than the cohort's normal,
                        or a destructive command (recursive delete at a home or
                        system root, hard reset, force push, mirror delete).
6. ``credential_access``  an ssh key, cloud credential, ``.env``, certificate or
                        stored token file is opened, or the environment dumped.
7. ``network_egress``   a host absent from the cohort's learned host set,
                        fan-out across many hosts, or a bare IP literal.
8. ``privilege_change`` sudo, an edited sudoers file, a setuid bit,
                        world-writable permissions, a disabled protection.

THE HONESTY BOUND on family two, repeated in every incident as
``evidence.observed = "tool_arguments"``: these read tool-call ARGUMENTS, not
syscalls. An agent that shells out to a program which itself opens ``~/.ssh``
is invisible here. Two rules keep that bound from becoming noise: heredoc
bodies are stripped before matching (a script that merely CONTAINS the text
``csrutil disable`` is not an escalation) and privilege patterns are ignored
inside inspect-only commands such as ``grep`` or ``git log``.

Each detector returns an incident dict (or ``None``):

    {
      "kind":          one of DETECTOR_KINDS,
      "session_id":    str,
      "runtime":       str,
      "severity":      "info" | "warning" | "critical",
      "title":         plain-words headline ("codex looping: 38 tool calls..."),
      "detail":        one-sentence explanation incl. the Stop/Pause hint,
      "evidence":      small dict of the numbers behind the call, including
                       the threshold crossed and where that threshold came
                       from; REDACTED (categories not paths, program not
                       command line) because this travels to the cloud,
      "first_bad_step": int | None,   # 0-based index into ``events``
      # attached by annotate_spend:
      "spend_at_risk_usd":    float,  # cost of the FLAGGED STRETCH, estimated
      "spend_basis":          "burn_rate" | "window_fraction" | "unknown",
      "burn_rate_usd_per_min": float,
      "session_cost_usd":      float,
    }

``run_all(events, session_id, runtime, facts=, baseline=, thresholds=, steps=)``
normalizes ONCE, shares the parse with every detector, and returns the
incidents ordered by what ignoring them costs.

**Thresholds are resolved, not hard-coded.** ``resolve_thresholds`` layers four
sources, each overriding the last: module defaults, then the runtime profile
(write-tool vocabulary, a checkable fact about the adapter), then the cohort's
learned baseline, then a per-runtime env override
(``CLAWMETRY_NOPROG_TOOLS__CODEX=40``). It reports which layer set each value.

**Money decides the order.** ``annotate_spend`` prices the flagged stretch and
says on what basis. Only a measured ``burn_rate`` may promote a warning to
``critical``; a ``window_fraction`` apportionment is context only, and where
nothing is known the figure is 0.0 with basis ``unknown``, never invented.
"""

from __future__ import annotations

from typing import Iterable, Optional

# The floor these detectors stand on, and the two questions that are not
# detection: what counts as too much (calibration) and what a finding costs
# (money). Re-exported below so ``clawmetry.detectors`` remains the single
# import every caller already uses.
from clawmetry.detector_calibration import (  # noqa: F401
    ACTION_DISCREPANCY_MIN,
    BASELINE_CEIL_RATIO,
    BASELINE_FLOOR_RATIO,
    BASELINE_MIN_SESSIONS,
    BASELINE_SIGMA,
    BLAST_RADIUS_FILES,
    DETECT_EVENT_WINDOW,
    EGRESS_HOST_FANOUT,
    NO_PROGRESS_TOOL_CALLS,
    REPEATED_FAILURE_M,
    RUNTIME_PROFILES,
    STUCK_LOOP_CYCLE_REPEATS,
    STUCK_LOOP_IDENTICAL_K,
    STUCK_LOOP_MAX_CYCLE,
    WRITE_TOOL_SUBSTRINGS,
    resolve_thresholds,
)
from clawmetry.detector_core import (  # noqa: F401
    _action_surface,
    _cmd_sketch,
    _hosts_from_text,
    _incident,
    _is_inspect_only,
    _is_write_tool,
    _prepare,
    _redact_path,
    _runtime_of,
    _step_mutates,
    _stop_hint,
    _strip_heredocs,
    _text_looks_failed,
    normalize_events,
)
from clawmetry.detector_money import (  # noqa: F401
    CRITICAL_SPEND_USD,
    _SEVERITY_RANK,
    _severity_promote,
    annotate_spend,
    incident_rank,
    sort_incidents,
)
from clawmetry.detector_behaviour import (  # noqa: F401
    credential_access,
    file_blast_radius,
    network_egress,
    privilege_change,
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
)


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
