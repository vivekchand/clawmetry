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
import re
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

# ── Behavioural thresholds (detectors beyond the tool loop) ──────────────────
# The four detectors above read the SHAPE of the tool stream — repetition,
# failure, stalling. The four below read what those calls actually DID: which
# files they mutated, which hosts they reached, which secrets they opened,
# which privileges they changed. Same source (a read-only observer has the
# tool stream and nothing else), different question — not "is this agent
# stuck?" but "is this agent doing something it does not normally do?".
#
# HONESTY BOUND, stated once and repeated in every incident's evidence: these
# read tool-call ARGUMENTS. They are not a kernel hook. An agent that shells
# out to a program which itself opens ~/.ssh is invisible here, and every
# incident carries ``"observed": "tool_arguments"`` so nobody reads a finding
# as syscall-level truth.

# file_blast_radius: distinct files mutated in the window before we flag it.
BLAST_RADIUS_FILES = int(os.environ.get("CLAWMETRY_BLAST_FILES", "25"))
# network_egress: distinct external hosts in one window that counts as fan-out.
EGRESS_HOST_FANOUT = int(os.environ.get("CLAWMETRY_EGRESS_HOSTS", "8"))

# ── Learned baselines (thresholds that stop being constants) ─────────────────
# A cohort (runtime, or a single agent) needs this many observed sessions
# before its measured mean/stddev is allowed to move a threshold. Below it we
# use the static default: a baseline of three sessions is noise, and a
# threshold derived from noise is worse than an honest constant.
BASELINE_MIN_SESSIONS = int(os.environ.get("CLAWMETRY_BASELINE_MIN_SESSIONS", "20"))
# How many standard deviations above the cohort mean counts as "unusual".
BASELINE_SIGMA = float(os.environ.get("CLAWMETRY_BASELINE_SIGMA", "2.0"))
# A learned threshold may never fall below floor*static or rise above
# ceiling*static. A cohort that is pathological end-to-end (every session
# loops) must not be able to teach Guard that looping is normal.
BASELINE_FLOOR_RATIO = float(os.environ.get("CLAWMETRY_BASELINE_FLOOR", "0.5"))
BASELINE_CEIL_RATIO = float(os.environ.get("CLAWMETRY_BASELINE_CEIL", "5.0"))

# Spend at risk (USD) at which a warning is promoted to critical.
CRITICAL_SPEND_USD = float(os.environ.get("CLAWMETRY_GUARD_CRITICAL_USD", "5"))

# ── Per-runtime calibration ──────────────────────────────────────────────────
# One global K and N across every runtime misfires, because the runtimes do
# not speak the same tool language. The fixtures in ``tests/fixtures/runtimes/``
# show it directly: claude_code calls ``Bash``/``Edit``, codex and picoclaw
# call ``shell``/``exec``, qwen_code calls ``list_directory``/``write_file``,
# goose calls ``developer__text_editor``. A "no file writes" signal computed
# with claude_code's vocabulary is simply wrong for the others.
#
# What this table DOES encode: per-runtime write vocabulary — a fact about the
# adapter, checkable against its fixture.
# What it deliberately does NOT encode: invented per-runtime numbers. Shipping
# "codex gets K=5 because it feels chattier" would be a fabricated constant
# wearing a calibration hat. Numeric deviation comes from the measured
# baseline below, or from an operator's per-runtime env override.
RUNTIME_PROFILES: dict = {
    # Anthropic-style vocabulary; the module defaults were written for it.
    "claude_code": {"write_tools": ()},
    # Codex patches through ``apply_patch`` (in defaults) and edits through
    # ``shell`` heredocs — the shell-mutation rule below catches the latter.
    "codex": {"write_tools": ()},
    # Gemini-CLI lineage: ``write_file`` (in defaults) and ``replace``.
    "qwen_code": {"write_tools": ("replace",)},
    "gemini_cli": {"write_tools": ("replace",)},
    "antigravity": {"write_tools": ("replace",)},
    # Goose namespaces its tools by extension (``developer__text_editor``),
    # which the default ``edit`` substring already matches — listed here with
    # an empty override so the next person checks rather than assumes.
    "goose": {"write_tools": ()},
    # opencode: write/edit/patch — all in the defaults.
    "opencode": {"write_tools": ()},
    # Shell-first runtimes: every file change happens inside ``shell``/``exec``,
    # so nothing matches a write-tool name. The shell-mutation rule is what
    # makes no_progress meaningful for them.
    "picoclaw": {"write_tools": ()},
    "nanoclaw": {"write_tools": ()},
}

# Threshold key -> (module default, base env var). A per-runtime override is
# the same env var with ``__<RUNTIME>`` appended, e.g.
# ``CLAWMETRY_NOPROG_TOOLS__CODEX=40`` tunes codex alone and leaves the rest.
_THRESHOLD_ENV = {
    "identical_k": "CLAWMETRY_LOOP_IDENTICAL_K",
    "max_cycle": "CLAWMETRY_LOOP_MAX_CYCLE",
    "cycle_repeats": "CLAWMETRY_LOOP_CYCLE_REPEATS",
    "no_progress_tools": "CLAWMETRY_NOPROG_TOOLS",
    "repeat_fail_m": "CLAWMETRY_REPEAT_FAIL_M",
    "action_discrepancy_min": "CLAWMETRY_ACTION_DISCREPANCY_MIN",
    "blast_files": "CLAWMETRY_BLAST_FILES",
    "egress_hosts": "CLAWMETRY_EGRESS_HOSTS",
}


def _static_thresholds() -> dict:
    """The module-constant defaults, read fresh so an env change after import
    (tests do this) is picked up."""
    return {
        "identical_k": STUCK_LOOP_IDENTICAL_K,
        "max_cycle": STUCK_LOOP_MAX_CYCLE,
        "cycle_repeats": STUCK_LOOP_CYCLE_REPEATS,
        "no_progress_tools": NO_PROGRESS_TOOL_CALLS,
        "repeat_fail_m": REPEATED_FAILURE_M,
        "action_discrepancy_min": ACTION_DISCREPANCY_MIN,
        "blast_files": BLAST_RADIUS_FILES,
        "egress_hosts": EGRESS_HOST_FANOUT,
    }


def _env_key(runtime: str) -> str:
    """``claude_code`` -> ``CLAUDE_CODE``; anything non-alphanumeric folds to
    ``_`` so a runtime label can never produce an unreachable env var name."""
    return "".join(c if c.isalnum() else "_" for c in str(runtime or "")).upper()


def _clamp_learned(learned: float, static: float) -> int:
    """Keep a learned threshold inside a band around the static default.

    Without this a cohort whose every session loops would raise its own
    threshold until Guard went blind, and a cohort of three trivial sessions
    would drop it until Guard screamed at everything."""
    lo = max(1.0, static * BASELINE_FLOOR_RATIO)
    hi = max(lo, static * BASELINE_CEIL_RATIO)
    return int(round(min(hi, max(lo, learned))))


def _numeric_baseline(baseline: Optional[dict], metric: str) -> Optional[dict]:
    """Pull one numeric metric out of a baseline dict, or None when it is
    absent / too thin to trust."""
    if not isinstance(baseline, dict):
        return None
    stats = baseline.get(metric)
    if not isinstance(stats, dict):
        return None
    try:
        n = int(stats.get("n") or 0)
        mean = float(stats.get("mean") or 0.0)
        stddev = float(stats.get("stddev") or 0.0)
    except (TypeError, ValueError):
        return None
    if n < BASELINE_MIN_SESSIONS or mean <= 0:
        return None
    return {"n": n, "mean": mean, "stddev": stddev}


def resolve_thresholds(runtime: Optional[str] = None,
                       baseline: Optional[dict] = None) -> dict:
    """Thresholds for one runtime, in four layers (each overrides the last):

    1. module defaults (the global env vars — unchanged, still honoured)
    2. the runtime profile (write vocabulary; a fact about the adapter)
    3. the learned baseline, when the cohort has enough observed sessions
    4. a per-runtime env override, which always wins — an operator who has
       tuned a runtime by hand outranks anything we inferred.

    The returned dict carries ``sources``: which layer set each numeric
    threshold. That is not decoration — an incident that fires on a learned
    threshold has to be able to say so, or nobody can tell a tuned detector
    from a lucky one.
    """
    rt = str(runtime or "").strip().lower()
    th = _static_thresholds()
    sources = {k: "static" for k in th}

    profile = RUNTIME_PROFILES.get(rt) or {}
    write_tools = tuple(WRITE_TOOL_SUBSTRINGS) + tuple(
        str(s).lower() for s in (profile.get("write_tools") or ()))
    for key in _THRESHOLD_ENV:
        if key in profile:
            try:
                th[key] = int(profile[key])
                sources[key] = "runtime_profile"
            except (TypeError, ValueError):
                pass

    # Layer 3: learned. tool calls per session drives no_progress; distinct
    # files mutated per session drives the blast radius.
    learned = {}
    tc = _numeric_baseline(baseline, "tool_calls")
    if tc:
        th["no_progress_tools"] = _clamp_learned(
            tc["mean"] + BASELINE_SIGMA * tc["stddev"], NO_PROGRESS_TOOL_CALLS)
        sources["no_progress_tools"] = "baseline"
        learned["tool_calls"] = tc
    wf = _numeric_baseline(baseline, "write_files")
    if wf:
        th["blast_files"] = _clamp_learned(
            wf["mean"] + BASELINE_SIGMA * wf["stddev"], BLAST_RADIUS_FILES)
        sources["blast_files"] = "baseline"
        learned["write_files"] = wf

    # A cohort that has NEVER recorded a file write across a real sample is
    # telling us its writes are invisible to us (the runtime edits files
    # without a tool call we can see), not that its agents never write. In
    # that case "zero writes" carries no information and no_progress must not
    # fire on it — the alternative is flagging every session that runtime runs.
    no_progress_enabled = True
    if isinstance(baseline, dict):
        try:
            sessions = int(baseline.get("sessions") or 0)
            write_sessions = int(baseline.get("write_sessions") or 0)
        except (TypeError, ValueError):
            sessions = write_sessions = 0
        if sessions >= BASELINE_MIN_SESSIONS and write_sessions == 0:
            no_progress_enabled = False

    # Layer 4: per-runtime env override wins over everything.
    if rt:
        suffix = "__" + _env_key(rt)
        for key, base in _THRESHOLD_ENV.items():
            raw = os.environ.get(base + suffix)
            if raw is None:
                continue
            try:
                th[key] = int(raw)
                sources[key] = "env_runtime"
            except (TypeError, ValueError):
                continue

    th["runtime"] = rt
    th["write_tools"] = write_tools
    th["no_progress_enabled"] = no_progress_enabled
    th["sources"] = sources
    th["baseline"] = learned
    th["known_hosts"] = frozenset(
        str(h).lower() for h in (baseline or {}).get("hosts") or ()
        if isinstance(h, str) and h.strip()
    )
    return th


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


# ── Action surface: what a tool call actually touched ────────────────────────
# The loop detectors only need (tool, args_hash). The behavioural ones need the
# nouns: paths, commands, hosts. We extract them ONCE during normalization,
# bounded in size, so eight detectors do not each re-parse the same arguments.

# Argument keys that carry a filesystem path across the runtimes we ingest.
_PATH_ARG_KEYS = (
    "path", "file_path", "filepath", "file", "filename", "file_name",
    "notebook_path", "target_file", "old_path", "new_path", "dst",
    "destination", "src", "source", "dir", "directory", "cwd",
    "paths", "files", "file_paths", "edits",
)
# Argument keys that carry a shell command / script body.
_CMD_ARG_KEYS = (
    "command", "cmd", "commands", "script", "shell_command", "code",
    "bash_command", "input", "argv", "args",
)
# Tools whose single string argument IS a command rather than a path.
_SHELL_TOOL_SUBSTRINGS = ("bash", "shell", "exec", "terminal", "run_command",
                          "process", "console", "sh")

_URL_RE = re.compile(r"\b[a-z][a-z0-9+.\-]{1,15}://([^/\s'\"<>|)]+)", re.I)
# scp/ssh/rsync style ``user@host:path`` targets — egress without a URL.
_SSH_HOST_RE = re.compile(
    r"(?:^|\s)[\w.\-]+@([a-z0-9][a-z0-9.\-]*\.[a-z]{2,63})(?=[:\s]|$)", re.I)
# A redirect that writes a REAL file. ``2>/dev/null`` and ``>/dev/null`` are so
# common in normal work that counting them as progress would silence
# no_progress for every shell-first runtime, so they are excluded explicitly.
_REDIRECT_WRITE_RE = re.compile(r">>?\s*(?!/dev/null)([\w./~\-]+)")
# Commands that mutate the filesystem. Progress for no_progress, and the write
# side of the blast radius for shell-first runtimes.
_MUTATING_CMD_RE = re.compile(
    r"(?:^|[;&|]\s*|\s)(?:cp|mv|rm|mkdir|rmdir|touch|tee|patch|truncate|ln|"
    r"install|unzip|tar|dd)\s|"
    r"\bsed\s+-i|\bgit\s+(?:apply|commit|checkout|restore|stash|clean|reset)\b|"
    r"\bnpm\s+(?:install|i)\b|\bpip\s+install\b", re.I)
# Hosts that are not egress: the machine talking to itself.
_LOCAL_HOSTS = frozenset({
    "localhost", "127.0.0.1", "0.0.0.0", "::1", "[::1]", "host.docker.internal",
    "169.254.169.254",  # the metadata endpoint IS interesting -> see below
})
_IPV4_RE = re.compile(r"^\d{1,3}(?:\.\d{1,3}){3}$")

_MAX_SURFACE_ITEMS = 24          # per step; bounds CPU and evidence size
_MAX_CMD_CHARS = 2000


def _looks_like_path(value: str) -> bool:
    v = value.strip()
    if not v or len(v) > 400 or "\n" in v:
        return False
    if "://" in v:
        return False   # a URL is egress, not a file the agent mutated
    if v.startswith(("/", "./", "../", "~/")) or "\\" in v[:3]:
        return True
    return "/" in v and " " not in v


def _iter_str_values(value, depth: int = 0):
    """Yield the string leaves of an argument value, one level of nesting deep.
    Bounded so a huge ``edits`` array cannot make normalization expensive."""
    if isinstance(value, str):
        yield value
    elif isinstance(value, (list, tuple)) and depth < 2:
        for v in value[:_MAX_SURFACE_ITEMS]:
            for s in _iter_str_values(v, depth + 1):
                yield s
    elif isinstance(value, dict) and depth < 2:
        for k, v in list(value.items())[:_MAX_SURFACE_ITEMS]:
            if k in _PATH_ARG_KEYS or k in _CMD_ARG_KEYS:
                for s in _iter_str_values(v, depth + 1):
                    yield s


def _is_shell_tool(tool: str) -> bool:
    t = (tool or "").lower()
    return any(sub in t for sub in _SHELL_TOOL_SUBSTRINGS)


def _hosts_from_text(text: str) -> list:
    """External hostnames a command or argument reaches out to. Local names are
    dropped — a request to 127.0.0.1 is not egress."""
    out = []
    if not text:
        return out
    try:
        for m in _URL_RE.finditer(text[:_MAX_CMD_CHARS]):
            netloc = m.group(1)
            host = netloc.rsplit("@", 1)[-1]          # strip user:pass@
            host = host.split("/", 1)[0]
            if host.startswith("["):                   # [::1]:8080
                host = host[:host.find("]") + 1]
            else:
                host = host.rsplit(":", 1)[0] if host.count(":") == 1 else host
            host = host.strip().lower().rstrip(".")
            if host and host not in _LOCAL_HOSTS and not host.endswith(".local"):
                out.append(host)
        for m in _SSH_HOST_RE.finditer(text[:_MAX_CMD_CHARS]):
            host = m.group(1).strip().lower().rstrip(".")
            if host and host not in _LOCAL_HOSTS and "." in host:
                out.append(host)
    except Exception:
        return out
    return out[:_MAX_SURFACE_ITEMS]


def _paths_from_command(cmd: str) -> list:
    """Path-looking tokens inside a shell command (bounded)."""
    out = []
    try:
        for tok in cmd[:_MAX_CMD_CHARS].split()[:60]:
            tok = tok.strip("'\"();|&")
            if _looks_like_path(tok):
                out.append(tok)
        for m in _REDIRECT_WRITE_RE.finditer(cmd[:_MAX_CMD_CHARS]):
            out.append(m.group(1))
    except Exception:
        return out
    return out[:_MAX_SURFACE_ITEMS]


def _action_surface(tool: str, args) -> tuple:
    """``(paths, cmd, hosts)`` for one tool call. Never raises."""
    paths: list = []
    cmd_parts: list = []
    try:
        if isinstance(args, str):
            if _is_shell_tool(tool):
                cmd_parts.append(args)
            elif _looks_like_path(args):
                paths.append(args)
        elif isinstance(args, dict):
            for key, val in list(args.items())[:40]:
                k = str(key).lower()
                if k in _CMD_ARG_KEYS:
                    for s in _iter_str_values(val):
                        cmd_parts.append(s)
                elif k in _PATH_ARG_KEYS:
                    for s in _iter_str_values(val):
                        if _looks_like_path(s) or ("." in s and "/" not in s
                                                   and len(s) < 120):
                            paths.append(s)
                elif isinstance(val, str) and val.startswith(("http://", "https://")):
                    cmd_parts.append(val)
        elif isinstance(args, (list, tuple)):
            joined = " ".join(str(a) for a in args[:_MAX_SURFACE_ITEMS])
            if _is_shell_tool(tool):
                cmd_parts.append(joined)
    except Exception:
        pass
    cmd = " ".join(cmd_parts)[:_MAX_CMD_CHARS]
    if cmd:
        paths.extend(_paths_from_command(cmd))
    hosts = _hosts_from_text(cmd)
    for p in list(paths):
        if "://" in p:
            hosts.extend(_hosts_from_text(p))
    # dedupe, preserve order, bound
    seen = set()
    uniq_paths = []
    for p in paths:
        if p not in seen:
            seen.add(p)
            uniq_paths.append(p)
    seen = set()
    uniq_hosts = []
    for h in hosts:
        if h not in seen:
            seen.add(h)
            uniq_hosts.append(h)
    return (tuple(uniq_paths[:_MAX_SURFACE_ITEMS]), cmd,
            tuple(uniq_hosts[:_MAX_SURFACE_ITEMS]))


# ── Redaction: what an incident is allowed to publish ────────────────────────
# Incident evidence travels: loop_signals -> the heartbeat slice -> the cloud
# device summary. A full path usually names a customer or a project, and a raw
# command line can carry a bearer token, so neither goes in whole.

def _redact_path(path: str) -> str:
    """At most the last two segments, home collapsed. ``/Users/x/acme/api/db.py``
    becomes ``.../api/db.py``."""
    try:
        p = str(path or "").strip()
        if not p:
            return ""
        parts = [seg for seg in p.replace("\\", "/").split("/") if seg]
        tail = "/".join(parts[-2:])
        return (".../" + tail) if len(parts) > 2 else tail
    except Exception:
        return ""


_SECRETY = ("=", "@", "://", "sk-", "token", "key", "secret", "password", "pw=")


def _cmd_sketch(cmd: str) -> str:
    """The program and its first flag, nothing else. ``curl -sS -H
    "Authorization: Bearer sk-…" https://x`` becomes ``curl -sS``. Anything
    that could carry a value is dropped rather than truncated, because a
    truncated secret is still a leaked prefix."""
    try:
        out = []
        for tok in str(cmd or "").split()[:2]:
            low = tok.lower()
            if any(marker in low for marker in _SECRETY):
                break
            out.append(tok[:24])
        return " ".join(out)
    except Exception:
        return ""


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
                    # Action surface (behavioural detectors read these).
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


# ── Detector 5: file_blast_radius ────────────────────────────────────────────
# Destructive shell verbs, matched on the command text. Each entry is
# (label, regex). The label — never the command — is what reaches the incident.
_DESTRUCTIVE_PATTERNS = (
    ("recursive delete", re.compile(r"\brm\s+(?:-\w+\s+)*-\w*[rR]\w*", re.I)),
    ("history rewrite", re.compile(r"\bgit\s+(?:reset\s+--hard|clean\s+-\w*[fd])", re.I)),
    ("branch force-push", re.compile(r"\bgit\s+push\s+(?:\S+\s+)*--force", re.I)),
    ("disk write", re.compile(r"\bdd\s+.*\bof=", re.I)),
    ("recursive chmod/chown", re.compile(r"\b(?:chmod|chown)\s+-\w*[rR]", re.I)),
    ("mirror delete", re.compile(r"\brsync\b[^|;]*--delete", re.I)),
    ("truncate", re.compile(r"\btruncate\s+-s\s*0", re.I)),
)
# Roots where a recursive delete is not "cleaning node_modules" — it is the
# agent removing something it was never asked to touch.
_DANGEROUS_ROOTS = ("/", "/*", "~", "~/", "$HOME", "/etc", "/usr", "/var",
                    "/System", "/Users", "/home", "C:\\", "/Library")


def _destructive_hits(cmd: str) -> list:
    return [label for label, rx in _DESTRUCTIVE_PATTERNS if rx.search(cmd)]


def _deletes_a_root(cmd: str, paths) -> bool:
    """True when a recursive delete targets a home/system root rather than a
    subdirectory of the project."""
    if not _DESTRUCTIVE_PATTERNS[0][1].search(cmd):
        return False
    for p in paths:
        q = str(p).strip().rstrip("/") or "/"
        if q in ("", "/", "~", "$HOME") or q in _DANGEROUS_ROOTS:
            return True
        if q in ("/*", "~/*"):
            return True
    # ``rm -rf /`` with no token our path scanner kept still shows in the text.
    return bool(re.search(r"\brm\s+(?:-\w+\s+)*-\w*[rR]\w*\s+(?:/|~|\$HOME)\s*\*?\s*$",
                          cmd.strip(), re.I))


def file_blast_radius(events: Iterable[dict], session_id: str,
                      runtime: Optional[str] = None, *,
                      thresholds: Optional[dict] = None,
                      steps: Optional[list] = None,
                      facts: Optional[dict] = None) -> Optional[dict]:
    """Flag an unusually WIDE file footprint, or a destructive one.

    Two distinct failures share one detector because they are the same
    question asked at two scales:

    * **Wide** — the agent mutated more distinct files in this window than the
      cohort's baseline (or, with no baseline, than ``blast_files``). A
      refactor touching 200 files may be correct; it is also the shape of an
      agent that misread the task, and it is worth a human glance either way.
    * **Destructive** — a recursive delete at a home/system root, a hard
      reset, a force-push. Severity ``critical``: these are not recoverable by
      pressing Stop a minute later.

    Path-escape (writing outside the session's workspace) is reported when the
    caller passes ``facts["cwd"]``; without it we do not guess a root.
    """
    try:
        runtime, th, steps = _prepare(events, steps, thresholds, runtime, session_id)
        root = str((facts or {}).get("cwd") or "").rstrip("/")
        write_tools = th.get("write_tools")
        files: dict = {}
        outside = []
        destructive: list = []
        root_delete = False
        write_calls = 0
        first_idx = None
        for st in steps:
            if st.get("kind") != "tool_call":
                continue
            cmd = st.get("cmd") or ""
            hits = _destructive_hits(cmd) if cmd else []
            if hits:
                destructive.extend(hits)
                if first_idx is None:
                    first_idx = st.get("i")
                if _deletes_a_root(cmd, st.get("paths") or ()):
                    root_delete = True
            if not (_step_mutates(st, write_tools) or hits):
                continue
            write_calls += 1
            if first_idx is None:
                first_idx = st.get("i")
            for p in st.get("paths") or ():
                files.setdefault(p, st.get("tool") or "")
                if root and not str(p).startswith(("-", "~")) \
                        and str(p).startswith("/") and not str(p).startswith(root):
                    outside.append(p)

        limit = int(th["blast_files"])
        n_files = len(files)
        wide = n_files >= limit
        if not (wide or destructive):
            return None

        # Evidence NEVER carries a raw command or a full path: this dict is
        # written to loop_signals, folded into the heartbeat, and shipped to
        # the cloud device summary.
        evidence = {
            "distinct_files": n_files,
            "write_calls": write_calls,
            "threshold": limit,
            "threshold_source": th["sources"]["blast_files"],
            "baseline": th.get("baseline", {}).get("write_files"),
            "outside_workspace": len(set(outside)),
            "destructive": sorted(set(destructive))[:4],
            "samples": [_redact_path(p) for p in list(files)[:3]],
            "observed": "tool_arguments",
        }
        if root_delete:
            return _incident(
                "file_blast_radius", session_id, runtime, "critical",
                f"{runtime}: recursive delete at a home or system root",
                "The agent ran a recursive delete targeting a home or system "
                "root rather than a project subdirectory. " + _stop_hint(),
                evidence, first_idx)
        if destructive:
            label = sorted(set(destructive))[0]
            return _incident(
                "file_blast_radius", session_id, runtime, "warning",
                f"{runtime}: {label} across {n_files} file(s)",
                f"The agent ran a {label} command. Destructive commands are "
                f"not undone by stopping the agent afterwards. " + _stop_hint(),
                evidence, first_idx)
        return _incident(
            "file_blast_radius", session_id, runtime, "warning",
            f"{runtime}: {n_files} files changed in one stretch",
            f"The agent mutated {n_files} distinct files (threshold {limit}) "
            f"without a pause. Wide edits are sometimes right and sometimes a "
            f"misread task. " + _stop_hint(),
            evidence, first_idx)
    except Exception:
        return None


# ── Detector 6: credential_access ────────────────────────────────────────────
# (category label, path/command regex). The CATEGORY is what an incident
# publishes — never the path. "read an ssh private key" is the finding;
# ``/Users/dana/.ssh/id_ed25519_acme_prod`` is a leak in its own right.
_CREDENTIAL_PATTERNS = (
    ("ssh private key", re.compile(r"(?:^|/)\.ssh/(?:id_|.*_key$)|\bid_(?:rsa|ed25519|ecdsa|dsa)\b", re.I)),
    ("cloud credentials", re.compile(r"\.aws/credentials|\.aws/config|\.config/gcloud|"
                                     r"\.azure/|gcloud\s+auth|aws\s+configure|"
                                     r"\.kube/config", re.I)),
    ("environment file", re.compile(r"(?:^|[/\s])\.env(?:\.[\w-]+)?(?![\w./-])", re.I)),
    ("private certificate", re.compile(r"\.(?:pem|p12|pfx|jks)\b|private[_-]?key", re.I)),
    ("stored token file", re.compile(r"\.netrc|\.npmrc|\.pypirc|\.git-credentials|"
                                     r"\.docker/config\.json|credentials\.json", re.I)),
    ("keychain / secret store", re.compile(r"\bsecurity\s+find-(?:generic|internet)-password|"
                                           r"\bkeyring\b|\bvault\s+(?:read|kv)\b|"
                                           r"\bkubectl\s+get\s+secret", re.I)),
    ("environment dump", re.compile(r"(?:^|[;&|]\s*)(?:env|printenv|set)\s*(?:\||$)|"
                                    r"\bprintenv\b|\bos\.environ\b", re.I)),
    ("cloud metadata endpoint", re.compile(r"169\.254\.169\.254|metadata\.google\.internal", re.I)),
)
# ``.env.example`` / ``id_rsa.pub`` are templates and public halves, not secrets.
_CREDENTIAL_BENIGN = re.compile(r"\.env\.(?:example|sample|template)|\.pub\b|"
                                r"example\.pem|\.env\.d/", re.I)


def credential_access(events: Iterable[dict], session_id: str,
                      runtime: Optional[str] = None, *,
                      thresholds: Optional[dict] = None,
                      steps: Optional[list] = None,
                      facts: Optional[dict] = None) -> Optional[dict]:
    """Flag an agent reading secret-bearing files or dumping the environment.

    Reading a credential is not by itself wrong — plenty of legitimate tasks
    need ``.env``. What makes it worth surfacing is that nobody currently sees
    it happen at all, and that the same window sometimes also contains network
    egress, which is the shape of exfiltration rather than configuration.

    Severity is ``warning`` alone, ``critical`` when credential access is
    followed by egress to an external host in the same window. The critical
    wording says "reached the network after" — an observation — not
    "exfiltrated data", which we cannot see and will not claim.
    """
    try:
        runtime, th, steps = _prepare(events, steps, thresholds, runtime, session_id)
        categories: dict = {}
        first_idx = None
        first_pos = None
        for pos, st in enumerate(steps):
            if st.get("kind") != "tool_call":
                continue
            haystack = " ".join(list(st.get("paths") or ()) + [st.get("cmd") or ""])
            if not haystack.strip():
                continue
            if _CREDENTIAL_BENIGN.search(haystack):
                haystack = _CREDENTIAL_BENIGN.sub(" ", haystack)
            for label, rx in _CREDENTIAL_PATTERNS:
                if rx.search(haystack):
                    categories[label] = categories.get(label, 0) + 1
                    if first_idx is None:
                        first_idx = st.get("i")
                        first_pos = pos
        if not categories:
            return None

        # Egress AFTER the first credential touch, in the same window.
        egress_after = []
        for st in steps[(first_pos or 0) + 1:]:
            for h in st.get("hosts") or ():
                egress_after.append(h)
        egress_after = sorted(set(egress_after))

        labels = sorted(categories)
        evidence = {
            "categories": labels,
            "accesses": sum(categories.values()),
            "egress_after": egress_after[:5],
            "observed": "tool_arguments",
            # No paths, no commands. The category IS the finding.
            "redacted": "paths and commands are deliberately not recorded",
        }
        head = labels[0]
        more = f" and {len(labels) - 1} more" if len(labels) > 1 else ""
        if egress_after:
            return _incident(
                "credential_access", session_id, runtime, "critical",
                f"{runtime}: read {head}{more}, then reached {len(egress_after)} "
                f"external host(s)",
                f"The agent opened {head}{more} and afterwards contacted "
                f"{', '.join(egress_after[:3])}. That ordering is worth a look "
                f"before it continues. " + _stop_hint(),
                evidence, first_idx)
        return _incident(
            "credential_access", session_id, runtime, "warning",
            f"{runtime}: read {head}{more}",
            f"The agent opened {head}{more}. Plenty of tasks legitimately need "
            f"this; it is surfaced so the choice is yours rather than "
            f"invisible. " + _stop_hint(),
            evidence, first_idx)
    except Exception:
        return None


# ── Detector 7: network_egress ───────────────────────────────────────────────
def network_egress(events: Iterable[dict], session_id: str,
                   runtime: Optional[str] = None, *,
                   thresholds: Optional[dict] = None,
                   steps: Optional[list] = None,
                   facts: Optional[dict] = None) -> Optional[dict]:
    """Flag network destinations this agent has not used before.

    "First-time egress" only means something against a memory of what came
    before, so this detector fires on one of three grounds and says which:

    * ``first_time`` — hosts absent from the cohort's learned host set. Needs a
      baseline; without one we do not pretend every host is new.
    * ``fanout`` — more distinct external hosts in one window than
      ``egress_hosts``, which is unusual regardless of history.
    * ``raw_address`` — a bare IP literal instead of a hostname. Package
      registries and APIs have names; IPs in an agent's command line usually
      mean something hand-assembled.

    Contacting a host is not an accusation. The incident says where it went.
    """
    try:
        runtime, th, steps = _prepare(events, steps, thresholds, runtime, session_id)
        known = th.get("known_hosts") or frozenset()
        hosts: dict = {}
        first_idx = None
        for st in steps:
            for h in st.get("hosts") or ():
                if h not in hosts:
                    hosts[h] = st.get("i")
                    if first_idx is None:
                        first_idx = st.get("i")
        if not hosts:
            return None

        distinct = sorted(hosts)
        new_hosts = [h for h in distinct if h not in known] if known else []
        raw_ips = [h for h in distinct if _IPV4_RE.match(h)]
        fanout_limit = int(th["egress_hosts"])
        fanout = len(distinct) >= fanout_limit

        if new_hosts:
            ground, sev = "first_time", "warning"
        elif fanout:
            ground, sev = "fanout", "warning"
        elif raw_ips:
            ground, sev = "raw_address", "info"
        else:
            return None

        evidence = {
            "ground": ground,
            "distinct_hosts": len(distinct),
            "hosts": distinct[:8],
            "new_hosts": new_hosts[:8],
            "raw_addresses": raw_ips[:4],
            "known_host_count": len(known),
            "threshold": fanout_limit,
            "observed": "tool_arguments",
        }
        if ground == "first_time":
            shown = ", ".join(new_hosts[:3])
            return _incident(
                "network_egress", session_id, runtime, sev,
                f"{runtime}: first contact with {shown}"
                + (f" +{len(new_hosts) - 3} more" if len(new_hosts) > 3 else ""),
                f"This agent has not reached {shown} in the "
                f"{len(known)} host(s) seen from it before now. " + _stop_hint(),
                evidence, hosts.get(new_hosts[0]))
        if ground == "fanout":
            return _incident(
                "network_egress", session_id, runtime, sev,
                f"{runtime}: reached {len(distinct)} external hosts",
                f"The agent contacted {len(distinct)} distinct external hosts "
                f"in one stretch (threshold {fanout_limit}). " + _stop_hint(),
                evidence, first_idx)
        return _incident(
            "network_egress", session_id, runtime, sev,
            f"{runtime}: connected to a raw IP address",
            f"The agent connected to {raw_ips[0]} by address rather than by "
            f"name. " + _stop_hint(),
            evidence, hosts.get(raw_ips[0]))
    except Exception:
        return None


# ── Detector 8: privilege_change ─────────────────────────────────────────────
# (label, regex, critical?) — critical entries disable a protection or grant
# standing privilege; the rest are ordinary elevation worth seeing.
_PRIVILEGE_PATTERNS = (
    ("disabled a system protection",
     re.compile(r"\bcsrutil\s+disable|\bspctl\s+--master-disable|"
                r"\bsetenforce\s+0|\bufw\s+disable|"
                r"\bdefaults\s+write\s+/Library", re.I), True),
    ("edited sudoers",
     re.compile(r"\bvisudo\b|/etc/sudoers", re.I), True),
    ("piped a password into sudo",
     re.compile(r"\becho\s+[^|]*\|\s*sudo\s+-S\b|\bsudo\s+-S\b", re.I), True),
    ("world-writable permissions",
     re.compile(r"\bchmod\s+(?:-\w+\s+)*(?:777|a\+rwx|o\+w)\b", re.I), True),
    ("setuid bit",
     re.compile(r"\bchmod\s+(?:-\w+\s+)*[ug]?\+s\b|\bsetcap\b", re.I), True),
    ("ran a command as root",
     re.compile(r"(?:^|[;&|]\s*|\s)(?:sudo|doas)\s+(?!-S)|(?:^|\s)su\s+-", re.I), False),
    ("changed file ownership",
     re.compile(r"\bchown\s+(?:-\w+\s+)*root\b", re.I), False),
    ("installed a launch/system service",
     re.compile(r"\blaunchctl\s+(?:load|bootstrap)|\bsystemctl\s+(?:enable|start)|"
                r"\bcrontab\s+-", re.I), False),
)


def privilege_change(events: Iterable[dict], session_id: str,
                     runtime: Optional[str] = None, *,
                     thresholds: Optional[dict] = None,
                     steps: Optional[list] = None,
                     facts: Optional[dict] = None) -> Optional[dict]:
    """Flag an agent elevating privilege or weakening a protection.

    An agent that reaches for ``sudo`` mid-task has left the shape of work its
    operator approved, whether or not the command itself is reasonable. The
    critical tier is reserved for the ones that OUTLIVE the session: a disabled
    protection, an edited sudoers file, a setuid bit, world-writable
    permissions. Stopping the agent does not undo any of those.
    """
    try:
        runtime, th, steps = _prepare(events, steps, thresholds, runtime, session_id)
        found: dict = {}
        critical: list = []
        first_idx = None
        sketch = ""
        for st in steps:
            if st.get("kind") != "tool_call":
                continue
            cmd = st.get("cmd") or ""
            if not cmd:
                continue
            for label, rx, is_crit in _PRIVILEGE_PATTERNS:
                if rx.search(cmd):
                    found[label] = found.get(label, 0) + 1
                    if is_crit:
                        critical.append(label)
                    if first_idx is None:
                        first_idx = st.get("i")
                        sketch = _cmd_sketch(cmd)
        if not found:
            return None

        labels = sorted(found)
        evidence = {
            "patterns": labels,
            "matches": sum(found.values()),
            "irreversible": sorted(set(critical)),
            # Program + first flag only; a full command line can carry a token.
            "command_sketch": sketch,
            "observed": "tool_arguments",
        }
        if critical:
            head = sorted(set(critical))[0]
            return _incident(
                "privilege_change", session_id, runtime, "critical",
                f"{runtime}: {head}",
                f"The agent {head}. This outlives the session: stopping the "
                f"agent does not undo it. " + _stop_hint(),
                evidence, first_idx)
        head = labels[0]
        more = f" and {len(labels) - 1} more" if len(labels) > 1 else ""
        return _incident(
            "privilege_change", session_id, runtime, "warning",
            f"{runtime}: {head}{more}",
            f"The agent {head}{more}. Elevation mid-task is worth confirming "
            f"was part of the plan. " + _stop_hint(),
            evidence, first_idx)
    except Exception:
        return None


# ── Severity that maps to money ──────────────────────────────────────────────
# An incident list sorted by severity puts a $0.02 info above a $170 warning.
# The number that decides what to look at first is what ignoring it costs, so
# every incident carries an ESTIMATE of the spend behind the flagged stretch.
#
# It is an estimate and the field says so. Two bases, in order of preference:
#
#   burn_rate      cost / session-minutes * minutes-flagged. Used when the
#                  caller knows how long the session has been bad. This is the
#                  honest one: it prices the stretch, not the session.
#   window_fraction cost * (steps after the first bad step / steps in window).
#                  Used with no clock. Assumes even spend across the window,
#                  which is wrong in detail and right in order of magnitude.
#
# With neither, spend_at_risk is 0.0 and ``basis`` is "unknown" — never a
# fabricated number, because a fabricated dollar figure is the one thing that
# would make this list worse than sorting by severity.

def _severity_promote(severity: str, spend_at_risk: float) -> str:
    """Money can raise a warning to critical; it never lowers a severity, and
    it never promotes an ``info`` (a low-precision signal stays low-precision
    no matter how expensive the session is)."""
    if severity == "warning" and spend_at_risk >= CRITICAL_SPEND_USD:
        return "critical"
    return severity


def annotate_spend(incidents: list, *, cost_usd: float = 0.0,
                   bad_for_seconds: float = 0.0,
                   session_seconds: float = 0.0,
                   window_steps: int = 0) -> list:
    """Attach ``spend_at_risk_usd`` / ``burn_rate_usd_per_min`` / ``basis`` to
    each incident, promote severity on cost, and return the list sorted by what
    it costs to ignore. Never raises; a bad number degrades to 0.0."""
    try:
        cost = max(0.0, float(cost_usd or 0))
    except (TypeError, ValueError):
        cost = 0.0
    try:
        bad_s = max(0.0, float(bad_for_seconds or 0))
    except (TypeError, ValueError):
        bad_s = 0.0
    try:
        sess_s = max(0.0, float(session_seconds or 0))
    except (TypeError, ValueError):
        sess_s = 0.0

    burn = (cost / (sess_s / 60.0)) if (cost > 0 and sess_s >= 60) else 0.0
    for inc in incidents or []:
        if not isinstance(inc, dict):
            continue
        risk, basis = 0.0, "unknown"
        if burn > 0 and bad_s > 0:
            risk = min(cost, burn * (bad_s / 60.0))
            basis = "burn_rate"
        elif cost > 0 and window_steps > 0:
            fbs = inc.get("first_bad_step")
            if isinstance(fbs, int) and 0 <= fbs < window_steps:
                risk = cost * ((window_steps - fbs) / float(window_steps))
                basis = "window_fraction"
        inc["spend_at_risk_usd"] = round(risk, 4)
        inc["spend_basis"] = basis
        inc["burn_rate_usd_per_min"] = round(burn, 4)
        inc["session_cost_usd"] = round(cost, 4)
        inc["severity"] = _severity_promote(str(inc.get("severity") or "warning"),
                                            risk)
    return sort_incidents(incidents or [])


def incident_rank(incident: dict) -> tuple:
    """Sort key: money first, then severity, then how much of it there is.

    Ties are everywhere in practice (a free-tier local model session costs
    nothing), so severity remains the second key and the old warning-before-
    info ordering still holds when no cost is known.
    """
    if not isinstance(incident, dict):
        return (0.0, 0, 0, "")
    try:
        spend = float(incident.get("spend_at_risk_usd") or 0)
    except (TypeError, ValueError):
        spend = 0.0
    sev = _SEVERITY_RANK.get(str(incident.get("severity") or ""), 0)
    ev = incident.get("evidence") if isinstance(incident.get("evidence"), dict) else {}
    try:
        size = int(ev.get("repeats") or ev.get("tool_calls") or ev.get("failures")
                   or ev.get("distinct_files") or ev.get("accesses") or 0)
    except (TypeError, ValueError):
        size = 0
    return (spend, sev, size, str(incident.get("kind") or ""))


def sort_incidents(incidents: list) -> list:
    """Most expensive to ignore first."""
    try:
        return sorted([i for i in incidents if isinstance(i, dict)],
                      key=lambda i: incident_rank(i), reverse=True)
    except Exception:
        return list(incidents or [])


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

# Higher is louder. ``critical`` exists because "an agent disabled SIP" and
# "an agent continued after a failed grep" both landing on `warning` made the
# top of the list meaningless.
_SEVERITY_RANK = {"info": 0, "warning": 1, "critical": 2}

# Kinds every consumer should know about (the UI labels them, the policy form
# offers them). Exported so a new detector cannot be added without the surfaces
# that render it noticing.
DETECTOR_KINDS = tuple(d.__name__ for d in _ALL_DETECTORS)


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
