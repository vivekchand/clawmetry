"""How a detector decides what "too many" means, for THIS runtime and THIS team.

Split out of :mod:`clawmetry.detectors` so the question "where does this
threshold come from?" has one file to answer it, and so a reviewer can read the
calibration rules without also reading a thousand lines of event parsing.

Four layers, each overriding the last:

1. module defaults, which are the global env vars;
2. the runtime profile, which carries an adapter's write-tool vocabulary and is
   a checkable fact about that adapter rather than a number somebody guessed;
3. the cohort's learned baseline, once it has a real sample;
4. a per-runtime env override, which always wins, because an operator who has
   tuned a runtime by hand outranks anything we inferred.

``resolve_thresholds`` reports which layer set each value in ``sources``, so an
incident can say whether the threshold it crossed was measured or shipped.
"""
from __future__ import annotations

import os
from typing import Optional


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

# Silent-failure detectors (rate limited / blocked on a human / crashed).
# How many rate-limit style refusals (429 / overloaded / quota) in the window
# before the agent is called rate limited. One is normal; providers retry.
RATE_LIMIT_MIN = int(os.environ.get("CLAWMETRY_RATE_LIMIT_MIN", "2"))
# How many session (re)starts inside CRASH_WINDOW_SEC count as a crash loop.
# Two matches the outcome classifier's ``crash-loop`` impact tag.
CRASH_RESTARTS = int(os.environ.get("CLAWMETRY_CRASH_RESTARTS", "2"))
CRASH_WINDOW_SEC = int(os.environ.get("CLAWMETRY_CRASH_WINDOW_SEC", "900"))
# How long a session must have sat on a question or approval before it is
# reported as blocked on a human (seconds). Below this it is just a prompt.
BLOCKED_WAIT_SEC = int(os.environ.get("CLAWMETRY_BLOCKED_WAIT_SEC", "120"))

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
    # OpenWorker declares its own write set in ``coworker/risk.py``:
    # {write_file, replace_in_file, apply_patch, apply_unified_diff}.
    # ``write_file`` and ``apply_patch`` already match the module defaults; the
    # other two match nothing, so without this profile a session that edits
    # exclusively through them looks like it made no progress at all. It also
    # drives a shell (``run_shell``), which the shell-mutation rule covers.
    "openworker": {"write_tools": ("replace_in_file", "apply_unified_diff")},
    # Replit Agent writes through ``write``/``edit`` (both match the module
    # defaults) and shells through ``bash`` (covered by the shell-mutation
    # rule) — vocabulary verified against real in-workspace journals (pro
    # adapter fixture PROVENANCE.md). Listed with an empty override so the
    # next person checks rather than assumes.
    "replit": {"write_tools": ()},
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
    "rate_limit_min": "CLAWMETRY_RATE_LIMIT_MIN",
    "crash_restarts": "CLAWMETRY_CRASH_RESTARTS",
    "crash_window_sec": "CLAWMETRY_CRASH_WINDOW_SEC",
    "blocked_wait_sec": "CLAWMETRY_BLOCKED_WAIT_SEC",
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
        "rate_limit_min": RATE_LIMIT_MIN,
        "crash_restarts": CRASH_RESTARTS,
        "crash_window_sec": CRASH_WINDOW_SEC,
        "blocked_wait_sec": BLOCKED_WAIT_SEC,
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
