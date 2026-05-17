"""
clawmetry/eval_suite_runner.py — Phase 2 evals: golden test sets + CLI runner.

Phase 1 (PR #1623) scored real production sessions with an LLM-as-judge. Phase
2 inverts the flow: instead of waiting for production traffic to score, the
user writes a YAML test suite once and runs it against their agent on every
commit. Result: release-gating evals that catch a prompt regression before it
ships, not after a customer files a ticket.

Design constraints (composes with Phase 1):
  * Reuse the Phase 1 judge call (``eval_runner._call_judge``) and rubric
    plumbing — no new HTTP code paths, no second provider key, no duplicate
    rate limiter.
  * Suite YAML lives at ``~/.clawmetry/evals/<suite>.yaml`` so the user can
    commit them to git alongside the application code (the GitHub Action
    template copies them to ``~/.clawmetry/evals/`` before running).
  * Persist results to DuckDB (``eval_suite_runs`` table) so trend analysis
    feeds the same overview tile that Phase 1 populated.
  * CLI is exit-code clean: 0 on all-pass, 1 on any-fail. Plain text output
    so users can paste a failed run into a bug report without ANSI noise.

Public API:
    load_suite(name_or_path) -> Suite
    list_suites() -> list[str]
    run_suite(suite, *, agent_call=None, judge_call=None, store=None) -> SuiteRun
    SuiteRun.exit_code -> int  # 0 if all pass, 1 if any fail/error
"""

from __future__ import annotations

import json
import logging
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Callable

log = logging.getLogger("clawmetry.eval_suite_runner")


# ── Config ─────────────────────────────────────────────────────────────────────

# Suite directory. One YAML file per suite — users commit these to git and the
# CI step (``clawmetry eval --suite golden``) reads them at release time.
SUITES_DIR = Path(
    os.environ.get(
        "CLAWMETRY_EVALS_SUITES_DIR",
        os.path.expanduser("~/.clawmetry/evals"),
    )
)

# Outcome enum — kept tiny on purpose. Phase 3 may add ``deflected`` etc;
# for now ``success`` / ``escalated`` / ``failed`` covers the three buckets
# the PRD calls out (closed-loop, handed-off, broken).
_OUTCOMES = ("success", "escalated", "failed", "any")

# Default agent call: shell out to ``openclaw agent --once`` so users with a
# stock OpenClaw install get a working pipeline with zero extra glue. Callers
# (tests, custom harnesses) can inject their own.
_DEFAULT_AGENT_CMD = os.environ.get(
    "CLAWMETRY_EVALS_AGENT_CMD",
    "openclaw agent --once --json",
)


# ── Data classes ───────────────────────────────────────────────────────────────


@dataclass
class TestCase:
    """One row from the suite's ``tests:`` list. Names mirror the YAML keys
    so the dataclass doubles as schema documentation."""
    name: str
    input: str
    expected_tools: list[str] = field(default_factory=list)
    expected_outcome: str = "any"
    expected_min_score: float = 0.0

    # Tell pytest this is NOT a test class (the name pattern matches its
    # auto-collector otherwise; bare cosmetic warning, but ugly in CI logs).
    __test__ = False


@dataclass
class Suite:
    """Parsed YAML suite. ``source`` is the absolute path on disk so error
    messages can point the user at the offending file."""
    name: str
    judge_model: str
    tests: list[TestCase]
    source: str = ""


@dataclass
class TestResult:
    """One executed test case. ``status`` is one of ``pass`` / ``fail`` /
    ``error``. ``fail`` = ran clean but didn't meet expectations; ``error``
    = the harness itself broke (agent crashed, judge unavailable)."""
    name: str
    status: str
    score: float | None
    reason: str
    expected_outcome: str
    actual_outcome: str
    expected_tools: list[str]
    actual_tools: list[str]
    duration_ms: int

    # Suppress pytest auto-collection (see TestCase note above).
    __test__ = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SuiteRun:
    """Aggregate of a full ``run_suite`` invocation."""
    suite_name: str
    ran_at: int  # epoch millis
    sha: str
    results: list[TestResult]

    @property
    def passed(self) -> int:
        return sum(1 for r in self.results if r.status == "pass")

    @property
    def failed(self) -> int:
        return sum(1 for r in self.results if r.status in ("fail", "error"))

    @property
    def exit_code(self) -> int:
        return 0 if self.failed == 0 else 1


# ── YAML loading ───────────────────────────────────────────────────────────────


_VALID_NAME = re.compile(r"^[A-Za-z0-9_\-]+$")


def list_suites() -> list[str]:
    """Return suite names available in ``SUITES_DIR``. Empty list if the
    directory is missing (fresh install, no suites yet)."""
    if not SUITES_DIR.exists():
        return []
    out: list[str] = []
    for p in sorted(SUITES_DIR.glob("*.yaml")):
        out.append(p.stem)
    for p in sorted(SUITES_DIR.glob("*.yml")):
        if p.stem not in out:
            out.append(p.stem)
    return out


def _resolve_suite_path(name_or_path: str) -> Path:
    """Accept a bare suite name (``customer_support``) OR an absolute path
    (``/etc/golden.yaml``). The CI template uses absolute paths so users can
    commit the YAML anywhere in their repo."""
    p = Path(name_or_path).expanduser()
    if p.is_absolute() or p.exists():
        return p
    # Strip optional .yaml extension users sometimes paste.
    stem = name_or_path
    for ext in (".yaml", ".yml"):
        if stem.endswith(ext):
            stem = stem[: -len(ext)]
            break
    if not _VALID_NAME.match(stem):
        raise ValueError(
            f"suite name {name_or_path!r} contains characters outside "
            "[A-Za-z0-9_-]; use an absolute path if your filename is unusual"
        )
    for ext in (".yaml", ".yml"):
        candidate = SUITES_DIR / f"{stem}{ext}"
        if candidate.exists():
            return candidate
    return SUITES_DIR / f"{stem}.yaml"


def _parse_yaml(text: str) -> dict[str, Any]:
    """Use PyYAML when available, fall back to the eval_runner minimal
    parser so we don't add a new hard dep just for evals."""
    try:
        import yaml  # type: ignore
        loaded = yaml.safe_load(text)
        return loaded if isinstance(loaded, dict) else {}
    except ImportError:
        return _minimal_suite_yaml(text)


def _minimal_suite_yaml(text: str) -> dict[str, Any]:
    """Tiny YAML subset parser for the suite shape. Supports:
        suite: <name>
        judge_model: <name>
        tests:
          - name: <id>
            input: <str>
            expected_tools: [a, b]
            expected_outcome: <enum>
            expected_min_score: <num>

    Anything else is ignored. PyYAML is the supported path; this fallback
    just keeps a fresh ``pip install clawmetry`` working in air-gapped
    builds without yaml installed.
    """
    out: dict[str, Any] = {}
    tests: list[dict[str, Any]] = []
    cur: dict[str, Any] | None = None
    in_tests = False
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if not line.startswith(" "):
            m = re.match(r"^([A-Za-z0-9_\-]+):\s*(.*)$", line)
            if not m:
                continue
            k, v = m.group(1), m.group(2).strip()
            if k == "tests":
                in_tests = True
                continue
            in_tests = False
            out[k] = v
            continue
        if in_tests:
            stripped = line.strip()
            if stripped.startswith("- "):
                cur = {}
                tests.append(cur)
                stripped = stripped[2:]
                if ":" in stripped:
                    k, _, v = stripped.partition(":")
                    cur[k.strip()] = _coerce_yaml_value(v.strip())
                continue
            if cur is None:
                continue
            if ":" in stripped:
                k, _, v = stripped.partition(":")
                cur[k.strip()] = _coerce_yaml_value(v.strip())
    if tests:
        out["tests"] = tests
    return out


def _coerce_yaml_value(v: str) -> Any:
    """Cheap scalar coercion for the minimal parser: quoted string,
    bracketed list, int, float, or bare string."""
    if not v:
        return ""
    if v.startswith('"') and v.endswith('"'):
        return v[1:-1]
    if v.startswith("'") and v.endswith("'"):
        return v[1:-1]
    if v.startswith("[") and v.endswith("]"):
        body = v[1:-1].strip()
        if not body:
            return []
        return [_coerce_yaml_value(p.strip()) for p in body.split(",")]
    try:
        if "." in v:
            return float(v)
        return int(v)
    except ValueError:
        return v


def load_suite(name_or_path: str) -> Suite:
    """Parse a suite YAML and return a validated ``Suite``. Raises
    ``ValueError`` on missing required fields so the CLI can render a
    one-line user-readable error instead of a stack trace.
    """
    path = _resolve_suite_path(name_or_path)
    if not path.exists():
        raise FileNotFoundError(
            f"no suite at {path} (run `clawmetry eval --list` to see "
            f"available suites)"
        )
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as e:
        raise ValueError(f"could not read {path}: {e}") from e
    data = _parse_yaml(text)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: top-level YAML must be a mapping")

    name = str(data.get("suite") or path.stem)
    judge_model = str(data.get("judge_model") or "claude-haiku-4-5")
    raw_tests = data.get("tests")
    if not isinstance(raw_tests, list) or not raw_tests:
        raise ValueError(f"{path}: `tests:` list is required and must be non-empty")

    tests: list[TestCase] = []
    seen: set[str] = set()
    for i, row in enumerate(raw_tests):
        if not isinstance(row, dict):
            raise ValueError(f"{path}: tests[{i}] must be a mapping, got {type(row).__name__}")
        tname = str(row.get("name") or "").strip()
        if not tname:
            raise ValueError(f"{path}: tests[{i}] missing required field `name`")
        if tname in seen:
            raise ValueError(f"{path}: duplicate test name {tname!r}")
        seen.add(tname)
        tinput = row.get("input")
        if not isinstance(tinput, str) or not tinput.strip():
            raise ValueError(f"{path}: tests[{i}] ({tname}) missing required field `input`")
        outcome = str(row.get("expected_outcome") or "any").strip().lower()
        if outcome not in _OUTCOMES:
            raise ValueError(
                f"{path}: tests[{i}] ({tname}) expected_outcome {outcome!r} "
                f"must be one of {_OUTCOMES}"
            )
        raw_tools = row.get("expected_tools") or []
        if not isinstance(raw_tools, list):
            raise ValueError(
                f"{path}: tests[{i}] ({tname}) expected_tools must be a list"
            )
        try:
            min_score = float(row.get("expected_min_score") or 0.0)
        except (TypeError, ValueError):
            raise ValueError(
                f"{path}: tests[{i}] ({tname}) expected_min_score must be a number"
            )
        tests.append(TestCase(
            name=tname,
            input=tinput,
            expected_tools=[str(t) for t in raw_tools],
            expected_outcome=outcome,
            expected_min_score=min_score,
        ))

    return Suite(
        name=name,
        judge_model=judge_model,
        tests=tests,
        source=str(path),
    )


# ── Agent invocation ───────────────────────────────────────────────────────────


@dataclass
class AgentResponse:
    """What the agent returned for one test input. ``text`` feeds the
    judge; ``tools_used`` is checked against ``expected_tools``; ``outcome``
    is checked against ``expected_outcome``."""
    text: str
    tools_used: list[str]
    outcome: str
    error: str | None = None


def _default_agent_call(test_input: str) -> AgentResponse:
    """Shell out to the configured agent command, pipe ``test_input`` on
    stdin, parse the first valid JSON line of stdout. Returns an error
    response (not raises) on any failure so the suite keeps running.

    Expected JSON shape (matches OpenClaw v3 ``agent --once --json``):
        {"text": "<reply>", "tools_used": ["..."], "outcome": "success"}
    """
    cmd = _DEFAULT_AGENT_CMD.split()
    if not cmd:
        return AgentResponse("", [], "failed", error="empty CLAWMETRY_EVALS_AGENT_CMD")
    try:
        proc = subprocess.run(
            cmd,
            input=test_input,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
    except FileNotFoundError:
        return AgentResponse(
            "", [], "failed",
            error=f"agent binary not found: {cmd[0]!r} (set CLAWMETRY_EVALS_AGENT_CMD)",
        )
    except subprocess.TimeoutExpired:
        return AgentResponse("", [], "failed", error="agent timed out after 120s")
    except OSError as e:
        return AgentResponse("", [], "failed", error=f"agent spawn failed: {e}")

    if proc.returncode != 0:
        return AgentResponse(
            "", [], "failed",
            error=f"agent exited {proc.returncode}: {proc.stderr.strip()[:200]}",
        )

    # Parse the LAST JSON line — agents often print log lines before the
    # final JSON envelope.
    for line in reversed(proc.stdout.splitlines()):
        line = line.strip()
        if not line or not line.startswith("{"):
            continue
        try:
            data = json.loads(line)
        except ValueError:
            continue
        return AgentResponse(
            text=str(data.get("text") or data.get("output") or ""),
            tools_used=[str(t) for t in (data.get("tools_used") or [])],
            outcome=str(data.get("outcome") or "success").lower(),
        )
    return AgentResponse(
        text=proc.stdout.strip(),
        tools_used=[],
        outcome="success",
    )


# ── Test runner ────────────────────────────────────────────────────────────────


def _current_sha() -> str:
    """Best-effort git SHA for the run, blank if not in a git tree. The
    GitHub Action sets ``GITHUB_SHA``; honour that first."""
    sha = os.environ.get("GITHUB_SHA") or os.environ.get("CLAWMETRY_EVALS_SHA")
    if sha:
        return sha[:40]
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL,
            timeout=2,
        )
        return out.decode("utf-8", errors="replace").strip()[:40]
    except (subprocess.CalledProcessError, FileNotFoundError, OSError, subprocess.TimeoutExpired):
        return ""


def _evaluate_one(
    test: TestCase,
    suite: Suite,
    *,
    agent_call: Callable[[str], AgentResponse],
    judge_call: Callable[..., str] | None,
) -> TestResult:
    """Run ``agent_call`` then ``judge_call``, compare to ``test``'s
    expectations, return a ``TestResult``. Pure function modulo the
    callables — testable end-to-end without DuckDB or HTTP."""
    started = time.monotonic()

    try:
        response = agent_call(test.input)
    except Exception as e:
        return TestResult(
            name=test.name,
            status="error",
            score=None,
            reason=f"agent crashed: {type(e).__name__}: {e}",
            expected_outcome=test.expected_outcome,
            actual_outcome="failed",
            expected_tools=list(test.expected_tools),
            actual_tools=[],
            duration_ms=int((time.monotonic() - started) * 1000),
        )

    if response.error:
        return TestResult(
            name=test.name,
            status="error",
            score=None,
            reason=response.error,
            expected_outcome=test.expected_outcome,
            actual_outcome=response.outcome or "failed",
            expected_tools=list(test.expected_tools),
            actual_tools=list(response.tools_used),
            duration_ms=int((time.monotonic() - started) * 1000),
        )

    # Score with the Phase 1 judge. Import lazy so the suite runner is
    # importable in environments where httpx isn't installed (tests).
    score: float | None = None
    reason = ""
    if judge_call is None:
        from clawmetry.eval_runner import _call_judge as judge_call  # type: ignore
    try:
        from clawmetry.eval_runner import DEFAULT_RUBRIC, parse_score
        prompt = (
            str(DEFAULT_RUBRIC["prompt"])
            + "\n\n---\nTRANSCRIPT:\nUSER: "
            + test.input.strip()
            + "\n\nASSISTANT: "
            + response.text.strip()
            + "\n---"
        )
        reply = judge_call(suite.judge_model, prompt, timeout=30.0)
        score, parsed_reason = parse_score(reply)
        if parsed_reason:
            reason = parsed_reason
    except Exception as e:
        return TestResult(
            name=test.name,
            status="error",
            score=None,
            reason=f"judge unavailable: {type(e).__name__}: {e}",
            expected_outcome=test.expected_outcome,
            actual_outcome=response.outcome or "success",
            expected_tools=list(test.expected_tools),
            actual_tools=list(response.tools_used),
            duration_ms=int((time.monotonic() - started) * 1000),
        )

    # Comparison rules — all three must hold for a pass.
    failures: list[str] = []
    if test.expected_outcome != "any" and response.outcome != test.expected_outcome:
        failures.append(
            f"outcome={response.outcome!r}, expected {test.expected_outcome!r}"
        )
    missing = [t for t in test.expected_tools if t not in response.tools_used]
    if missing:
        failures.append(f"missing tools: {missing}")
    if test.expected_min_score > 0:
        if score is None:
            failures.append(f"no score (expected >= {test.expected_min_score})")
        elif score < test.expected_min_score:
            failures.append(f"score {score} < required {test.expected_min_score}")

    status = "pass" if not failures else "fail"
    final_reason = reason if status == "pass" else "; ".join(failures)
    return TestResult(
        name=test.name,
        status=status,
        score=score,
        reason=final_reason,
        expected_outcome=test.expected_outcome,
        actual_outcome=response.outcome,
        expected_tools=list(test.expected_tools),
        actual_tools=list(response.tools_used),
        duration_ms=int((time.monotonic() - started) * 1000),
    )


def run_suite(
    suite: Suite,
    *,
    agent_call: Callable[[str], AgentResponse] | None = None,
    judge_call: Callable[..., str] | None = None,
    store: Any = None,
    persist: bool = True,
) -> SuiteRun:
    """Execute every test in ``suite`` and return a ``SuiteRun``.

    All callables are injectable so tests can drive deterministic responses
    without subprocesses or HTTP. ``store`` defaults to the daemon's
    ``local_store.get_store()`` — set ``persist=False`` to skip the DuckDB
    write (used by ``--dry-run`` and unit tests).
    """
    agent_call = agent_call or _default_agent_call
    ran_at = int(time.time() * 1000)
    sha = _current_sha()
    results = [
        _evaluate_one(t, suite, agent_call=agent_call, judge_call=judge_call)
        for t in suite.tests
    ]
    run = SuiteRun(
        suite_name=suite.name,
        ran_at=ran_at,
        sha=sha,
        results=results,
    )
    if persist:
        try:
            _persist_run(run, store=store)
        except Exception as e:
            log.warning("eval_suite_runner: persist failed: %s", e)
    return run


def _persist_run(run: SuiteRun, *, store: Any = None) -> None:
    """Write each ``TestResult`` to the ``eval_suite_runs`` DuckDB table.
    Best-effort — a missing daemon or RO connection logs a warning and
    returns without crashing the CLI."""
    if store is None:
        try:
            from clawmetry import local_store
            store = local_store.get_store()
        except Exception as e:
            log.warning("eval_suite_runner: local_store unavailable: %s", e)
            return
    persister = getattr(store, "persist_eval_suite_run", None)
    if persister is None:
        log.warning("eval_suite_runner: store has no persist_eval_suite_run (older schema?)")
        return
    for r in run.results:
        try:
            persister(
                suite_name=run.suite_name,
                test_name=r.name,
                status=r.status,
                score=r.score,
                reason=r.reason or "",
                ran_at=run.ran_at,
                sha=run.sha,
            )
        except Exception as e:
            log.warning(
                "eval_suite_runner: persist row %s/%s failed: %s",
                run.suite_name, r.name, e,
            )


# ── CLI formatting ─────────────────────────────────────────────────────────────


def format_table(run: SuiteRun) -> str:
    """Render a ``SuiteRun`` as a fixed-width text table. No ANSI colour —
    keep the output paste-friendly for bug reports and CI logs."""
    rows = [("TEST", "STATUS", "SCORE", "REASON")]
    for r in run.results:
        score_s = "-" if r.score is None else f"{r.score:.1f}"
        reason = (r.reason or "")[:60]
        rows.append((r.name, r.status.upper(), score_s, reason))
    widths = [max(len(row[i]) for row in rows) for i in range(4)]
    lines = []
    for i, row in enumerate(rows):
        lines.append("  ".join(row[c].ljust(widths[c]) for c in range(4)).rstrip())
        if i == 0:
            lines.append("  ".join("-" * widths[c] for c in range(4)))
    lines.append("")
    lines.append(
        f"{run.passed} passed, {run.failed} failed of {len(run.results)} tests"
    )
    return "\n".join(lines)


# ── Watch mode ─────────────────────────────────────────────────────────────────


def watch_suite(
    name_or_path: str,
    *,
    interval_secs: float = 1.0,
    iterations: int | None = None,
    on_run: Callable[[SuiteRun], None] | None = None,
    agent_call: Callable[[str], AgentResponse] | None = None,
    judge_call: Callable[..., str] | None = None,
    persist: bool = True,
) -> None:
    """Poll the suite file for mtime changes; re-run on every change.

    Stdlib polling (no watchdog dep) — interval is the floor on detection
    latency. ``iterations`` caps the loop count so tests can drive it
    deterministically; ``None`` runs forever (Ctrl-C to exit).
    """
    path = _resolve_suite_path(name_or_path)
    last_mtime: float | None = None
    count = 0
    while iterations is None or count < iterations:
        try:
            mtime = path.stat().st_mtime
        except FileNotFoundError:
            mtime = -1.0
        if mtime != last_mtime:
            last_mtime = mtime
            if mtime > 0:
                try:
                    suite = load_suite(str(path))
                    run = run_suite(
                        suite,
                        agent_call=agent_call,
                        judge_call=judge_call,
                        persist=persist,
                    )
                    if on_run is not None:
                        on_run(run)
                except Exception as e:
                    log.warning("eval_suite_runner: watch reload failed: %s", e)
        count += 1
        if iterations is None or count < iterations:
            time.sleep(interval_secs)
