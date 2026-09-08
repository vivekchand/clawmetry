"""Session-location extraction, measured against each runtime's REAL capture.

"Works across all runtimes" is a claim, and this file is the measurement. It
runs the shipped extractors over the committed real-capture fixtures, so the
per-runtime answer is a test result rather than an assumption.

It caught a real bug on first run: Codex records its working directory ONLY
as ``payload.cwd`` (on its `session_meta` and `turn_context` lines), and the
nest list did not include ``payload`` — so an entire runtime's location was
being silently dropped while every synthetic test passed.

Runtimes that genuinely record nothing are asserted as recording nothing, on
purpose. That is a real answer, and it keeps a future "why is this NULL"
investigation from starting at zero.
"""

from __future__ import annotations

import glob
import json
import pathlib

import pytest

from clawmetry.sync import _session_cwd, _session_git_branch

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _scan(pattern: str):
    """(cwd_hits, branch_hits, first_cwd) across every line of every match."""
    cwd_hits = branch_hits = 0
    first = None
    files = sorted(glob.glob(str(ROOT / pattern), recursive=True))
    for f in files:
        for line in open(f, encoding="utf-8", errors="replace"):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except Exception:
                continue
            if not isinstance(row, dict):
                continue
            c = _session_cwd(row)
            if c:
                cwd_hits += 1
                first = first or c
            if _session_git_branch(row):
                branch_hits += 1
    return cwd_hits, branch_hits, first, len(files)


# ── runtimes whose real captures DO record a working directory ──────────────

@pytest.mark.parametrize("runtime,pattern,expect_cwd", [
    ("openclaw",    "tests/fixtures/openclaw/*.jsonl",                      "/"),
    ("claude_code", "tests/fixtures/runtimes/claude_code/**/*.jsonl",       "/"),
    ("codex",       "tests/fixtures/runtimes/codex/**/*.jsonl",             "/"),
    ("qwen_code",   "tests/fixtures/runtimes/qwen_code/**/*.jsonl",         "/"),
    ("antigravity", "tests/fixtures/runtimes/antigravity/**/*.jsonl",       "/"),
])
def test_runtime_location_is_extracted(runtime, pattern, expect_cwd):
    cwd_hits, _, first, nfiles = _scan(pattern)
    if nfiles == 0:
        pytest.skip(f"no {runtime} fixtures committed")
    assert cwd_hits > 0, (
        f"{runtime}'s real capture records a working directory somewhere and "
        f"the extractor found none — check where it nests it")
    assert first.startswith(expect_cwd)


def test_codex_cwd_comes_from_payload():
    """The regression this file exists for.

    Codex puts cwd under `payload`, nowhere else. Before `payload` joined the
    nest list every Codex session had a NULL location while the synthetic
    suite stayed green.
    """
    row = {"type": "session_meta",
           "payload": {"cwd": "/workspace/codex-demo", "id": "abc"}}
    assert _session_cwd(row) == "/workspace/codex-demo"


def test_claude_code_is_the_only_branch_source_today():
    """Documents a real limitation rather than pretending to cover it.

    Only Claude Code writes a git branch into its transcript among the
    committed captures. If another runtime starts doing so, this test fails
    and someone gets to widen the claim deliberately.
    """
    _, cc_branches, _, n = _scan("tests/fixtures/runtimes/claude_code/**/*.jsonl")
    if n == 0:
        pytest.skip("no claude_code fixtures committed")
    assert cc_branches > 0

    for pattern in ("tests/fixtures/runtimes/codex/**/*.jsonl",
                    "tests/fixtures/runtimes/qwen_code/**/*.jsonl",
                    "tests/fixtures/openclaw/*.jsonl"):
        _, branches, _, nf = _scan(pattern)
        if nf:
            assert branches == 0, (
                f"{pattern} now records a git branch — good news, but the "
                "coverage claim in docs should be widened to match")


# ── runtimes that genuinely record nothing ──────────────────────────────────

@pytest.mark.parametrize("runtime,pattern", [
    ("copilot",  "tests/fixtures/runtimes/copilot/**/*.jsonl"),
    ("picoclaw", "tests/fixtures/runtimes/picoclaw/**/*.jsonl"),
])
def test_runtime_records_no_location(runtime, pattern):
    """Asserted, not assumed. These sessions will show no project name, and
    that is the runtime's doing, not a parsing bug — worth knowing before
    someone debugs it as one."""
    cwd_hits, branch_hits, _, nfiles = _scan(pattern)
    if nfiles == 0:
        pytest.skip(f"no {runtime} fixtures committed")
    assert cwd_hits == 0 and branch_hits == 0, (
        f"{runtime} now records a location — the extractor should be checked "
        "and the docs updated to say so")
