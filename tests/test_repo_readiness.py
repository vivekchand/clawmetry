"""Guards for clawmetry/repo_readiness.py (WO-5, repo AI-readiness).

The Trap this work order shipped with: a previous scanner graded settings
nothing in the codebase ever read, so it failed on healthy machines and
taught the operator to ignore the grade. These tests pin the three rules
that prevent a repeat, and they fail on the un-fixed code:

  * every FAIL traces to a filesystem fact this module actually opened
  * an unreadable input scores ZERO weight, never a penalty
  * nothing here opens a socket or runs a subprocess
"""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from clawmetry import repo_readiness as rr  # noqa: E402


# ── fixtures ───────────────────────────────────────────────────────────────

@pytest.fixture()
def bare(tmp_path):
    """A directory with nothing in it at all."""
    d = tmp_path / "bare"
    d.mkdir()
    return str(d)


@pytest.fixture()
def furnished(tmp_path):
    """A repo that does everything an agent needs."""
    d = tmp_path / "furnished"
    (d / ".github" / "workflows").mkdir(parents=True)
    (d / ".claude" / "skills" / "deploy").mkdir(parents=True)
    (d / ".claude" / "skills" / "deploy" / "SKILL.md").write_text("# deploy\n")
    (d / ".github" / "workflows" / "ci.yml").write_text("on: push\n")
    (d / "CLAUDE.md").write_text("# how this project works\n")
    (d / "package.json").write_text(json.dumps({
        "name": "x",
        "scripts": {"test": "jest", "build": "tsc", "lint": "eslint ."},
    }))
    return str(d)


# ── the grade ──────────────────────────────────────────────────────────────

def test_furnished_repo_grades_well(furnished):
    """Acceptance criteria proven here:

    AC-OBS-007.1

    a repo that does everything an agent needs grades well.
    """
    rep = rr.score_repo(furnished)
    assert rep["status"] == "ok"
    assert rep["failed"] == 0, [c for c in rep["checks"] if c["status"] == "fail"]
    assert rep["score"] in ("A", "B")


def test_bare_repo_fails_every_gradeable_check(bare):
    """Acceptance criteria proven here:

    AC-OBS-007.1

    all six graded checks, each answered from the filesystem.
    """
    rep = rr.score_repo(bare)
    ids = {c["id"]: c["status"] for c in rep["checks"]}
    assert ids["instruction_file"] == "fail"
    assert ids["test_command"] == "fail"
    assert ids["build_command"] == "fail"
    assert ids["lint_gate"] == "fail"
    assert ids["ci_config"] == "fail"
    assert rep["score"] == "F"


def test_every_fail_names_the_thing_it_looked_for(bare):
    """Acceptance criteria proven here:

    AC-OBS-007.3

    a FAIL says what was looked for and how to fix it.
    """
    for c in rr.score_repo(bare)["checks"]:
        if c["status"] == "fail":
            assert c["remediation"], c["id"]
            assert len(c["detail"]) > 20, c["id"]


def test_every_pass_names_the_file_it_read(furnished):
    """Acceptance criteria proven here:

    AC-OBS-007.3

    a PASS carries the path that was read, so a reader can tell a measured result from a shipped constant.
    """
    for c in rr.score_repo(furnished)["checks"]:
        if c["status"] == "pass" and c["id"] != "instruction_loaded":
            assert c["evidence"], c["id"]
            # The evidence must be a path that actually exists in the repo.
            probe = os.path.join(furnished, c["evidence"].replace("/", os.sep))
            assert os.path.exists(probe), (c["id"], c["evidence"])


# ── ADR-004: unreadable means zero weight, never a penalty ─────────────────

def test_unknown_checks_carry_zero_weight(furnished):
    """Acceptance criteria proven here:

    AC-OBS-007.4
    """
    for c in rr.score_repo(furnished)["checks"]:
        if c["status"] == "unknown":
            assert c["weight"] == 0, c["id"]


def test_check_helper_forces_unknown_to_zero_weight():
    """The rule is enforced in one place so no future check can skip it."""
    c = rr._check("x", "X", rr.UNKNOWN, "d", None, 99)
    assert c["weight"] == 0


def test_unreadable_config_scores_unknown_not_fail(tmp_path):
    """Acceptance criteria proven here:

    AC-OBS-007.4

    a package.json we cannot parse must not read as "no test command". This is the exact shape of the bug ADR-004 exists to stop: the file IS there, we simply could not read it, and reporting that as a failure invents a defect.
    """
    d = tmp_path / "broken"
    d.mkdir()
    (d / "package.json").write_text("{ not json at all")
    check = rr._check_test_command(str(d))
    assert check["status"] == "unknown"
    assert check["weight"] == 0


def test_unknown_moves_the_grade_in_neither_direction():
    """Acceptance criteria proven here:

    AC-OBS-007.4

    two identical repos, one with an extra unknown, grade the same.
    """
    base = [
        rr._check("a", "A", rr.PASS, "d", None, 10),
        rr._check("b", "B", rr.FAIL, "d", "fix", 10),
    ]
    with_unknown = base + [rr._check("c", "C", rr.UNKNOWN, "d", None, 40)]
    assert rr._grade(base) == rr._grade(with_unknown)


def test_grade_is_not_scored_when_everything_is_unknown():
    checks = [rr._check("a", "A", rr.UNKNOWN, "d", None, 10)]
    letter, label, _color, pct = rr._grade(checks)
    assert letter == "U"
    assert pct == 0.0


def test_instruction_loaded_is_unknown_until_a_runtime_reports_it(furnished):
    """We read the file; that proves WE read it, not that the agent did.

    No runtime ClawMetry observes reports its loaded context files today, so
    this is an honest zero-weight unknown with the hook in place.
    """
    rep = rr.score_repo(furnished)
    loaded = [c for c in rep["checks"] if c["id"] == "instruction_loaded"][0]
    assert loaded["status"] == "unknown"
    assert loaded["weight"] == 0

    graded = rr.score_repo(furnished, loaded_evidence={
        "observed": True, "runtimes": ["claude_code"], "source": "hook"})
    loaded2 = [c for c in graded["checks"] if c["id"] == "instruction_loaded"][0]
    assert loaded2["status"] == "pass"
    assert loaded2["weight"] > 0


def test_inherited_default_is_warned_not_passed(tmp_path):
    """`cargo test` exists for every Cargo project. That is an inherited
    default, which counts as unmeasured, not ready."""
    d = tmp_path / "rust"
    d.mkdir()
    (d / "Cargo.toml").write_text('[package]\nname = "x"\n')
    check = rr._check_test_command(str(d))
    assert check["status"] == "warn"


# ── never crashes, never guesses ───────────────────────────────────────────

def test_missing_directory_renders_instead_of_raising():
    rep = rr.score_repo("/definitely/not/a/real/path/anywhere")
    assert rep["status"] == "not_found"
    assert rep["checks"] == []


@pytest.mark.parametrize("junk", [None, "", 0, [], {}])
def test_never_raises_on_junk_input(junk):
    rep = rr.score_repo(junk)
    assert isinstance(rep, dict)
    assert rep["status"] == "not_found"


def test_renders_for_a_repo_with_no_clawmetry_history(furnished):
    """Acceptance criteria proven here:

    AC-OBS-007.5

    the score renders for a repo ClawMetry has never seen, and says it has no history rather than reporting a clean stuck rate.
    """
    rep = rr.score_repo(furnished)
    assert rep["status"] == "ok"
    assert rep["signals"]["has_history"] is False
    # Not a fabricated 0%: "nobody worked here" and "nobody got stuck" are
    # different facts and must not render the same.
    assert rep["signals"]["stuck_rate"] is None


def test_no_network_and_no_subprocess(monkeypatch, furnished):
    """Acceptance criteria proven here:

    AC-OBS-007.7

    no network calls, and no subprocess either. We never run the build we are grading.
    """
    import socket
    import subprocess

    def boom(*a, **k):
        raise AssertionError("repo_readiness reached outside the filesystem")

    monkeypatch.setattr(socket, "socket", boom)
    monkeypatch.setattr(socket, "create_connection", boom)
    monkeypatch.setattr(subprocess, "run", boom)
    monkeypatch.setattr(subprocess, "Popen", boom)
    monkeypatch.setattr(subprocess, "check_output", boom)

    rep = rr.score_repo(furnished)
    assert rep["status"] == "ok"


def test_module_source_has_no_subprocess_or_urllib_import():
    """Acceptance criteria proven here:

    AC-OBS-007.7

    , belt and braces: the guard above only catches what a scan reaches. A future check that shells out to `make test` would be a read-only violation AND a network call; this fails the moment one is added.
    """
    src = open(rr.__file__, encoding="utf-8").read()
    for banned in ("import subprocess", "import urllib", "import requests",
                   "import httpx", "os.system", "os.popen"):
        assert banned not in src, banned


# ── per-runtime honesty ────────────────────────────────────────────────────

def test_runtime_scoping_is_honest(furnished):
    """Acceptance criteria proven here:

    AC-OBS-007.6

    a repo legible to Claude Code can be invisible to Cursor. A single node-wide tick would hide that.
    """
    claude = rr.score_repo(furnished, runtime="claude_code")
    cursor = rr.score_repo(furnished, runtime="cursor")
    c_instr = [c for c in claude["checks"] if c["id"] == "instruction_file"][0]
    x_instr = [c for c in cursor["checks"] if c["id"] == "instruction_file"][0]
    assert c_instr["status"] == "pass"
    assert x_instr["status"] == "fail"
    assert claude["score_pct"] > cursor["score_pct"]


def test_instruction_files_are_derived_from_the_runtime_catalog():
    """The file list must come from runtime_memory, not a second hand-kept
    copy that drifts every time a runtime is added."""
    from clawmetry import runtime_memory

    declared = {r["rel"] for r in runtime_memory.project_relative_roots(["memory"])}
    assert "CLAUDE.md" in declared
    assert "AGENTS.md" in declared
    used = {spec["rel"] for spec in rr._instruction_roots(None)}
    # Everything the catalog declares is used, minus the roots the AGENT
    # writes (its own transcript / scratch memory), which are not evidence
    # that a person documented the repo.
    assert used == declared - rr._AGENT_WRITTEN_ROOTS
    assert declared & rr._AGENT_WRITTEN_ROOTS, (
        "the denylist has drifted from the catalog: none of its entries are "
        "declared any more, so it is silently doing nothing")


def test_an_agents_own_transcript_is_not_an_instruction_file(tmp_path):
    """A repo aider has merely been RUN in is not a repo anyone documented."""
    d = tmp_path / "used"
    d.mkdir()
    (d / ".aider.input.history").write_text("fix the bug")
    (d / ".aider.chat.history.md").write_text("# chat")
    check = rr._check_instruction_file(
        str(d), None, rr.runtime_coverage(str(d), rr._instruction_roots(None)))
    assert check["status"] == "fail"


def test_the_suggested_instruction_file_is_the_most_widely_read_one(bare):
    """Suggesting `.agent/rules` because it sorts first alphabetically is
    advice nobody should follow."""
    check = rr._check_instruction_file(
        bare, None, rr.runtime_coverage(bare, rr._instruction_roots(None)))
    assert "AGENTS.md" in check["remediation"]
    assert check["detail"].index("AGENTS.md") < check["detail"].index(".agent")


def test_rel_ranking_is_derived_from_how_many_runtimes_read_the_file():
    roots = [
        {"rel": "zzz.md", "runtime": "a"},
        {"rel": "AGENTS.md", "runtime": "a"},
        {"rel": "AGENTS.md", "runtime": "b"},
        {"rel": "AGENTS.md", "runtime": "c"},
    ]
    assert rr._rank_rels(roots) == ["AGENTS.md", "zzz.md"]


def test_runtime_coverage_reports_what_it_looked_for(furnished):
    """Acceptance criteria proven here:

    AC-OBS-007.6

    per runtime, what was found and where we looked.
    """
    cov = rr.runtime_coverage(furnished)
    by_id = {r["runtime"]: r for r in cov}
    assert by_id["claude_code"]["has_instructions"] is True
    assert "CLAUDE.md" in by_id["claude_code"]["files"]
    # Even a runtime that found nothing says where it looked.
    for row in cov:
        assert row["looked_for"], row["runtime"]


# ── the pairing ────────────────────────────────────────────────────────────

def _row(sid, cwd, signature=None, details=None, ts="2026-08-20T10:00:00"):
    return {"session_id": sid, "cwd": cwd, "signature": signature,
            "details": details, "last_active_at": ts}


def test_pair_signals_counts_sessions_and_incidents():
    """Acceptance criteria proven here:

    AC-OBS-007.2

    sessions in the window, and how many got stuck.
    """
    rows = [
        _row("s1", "/r"),
        _row("s2", "/r", "daemon_detect_stuck_loop", {"kind": "stuck_loop"}),
        _row("s3", "/r", "daemon_detect_repeated_tool_failure",
             {"kind": "repeated_tool_failure"}),
    ]
    sig = rr.pair_signals(rows, window_days=30)
    assert sig["sessions"] == 3
    assert sig["stuck_sessions"] == 2
    assert sig["stuck_rate"] == pytest.approx(66.7)
    assert sig["incidents"]["stuck_loop"] == 1
    assert sig["incidents"]["repeated_tool_failure"] == 1


def test_one_session_with_two_signals_counts_once_as_stuck():
    rows = [
        _row("s1", "/r", "daemon_detect_stuck_loop", {"kind": "stuck_loop"}),
        _row("s1", "/r", "daemon_detect_no_progress", {"kind": "no_progress"}),
    ]
    sig = rr.pair_signals(rows, window_days=30)
    assert sig["sessions"] == 1
    assert sig["stuck_sessions"] == 1
    assert sig["incidents"]["stuck_loop"] == 1
    assert sig["incidents"]["no_progress"] == 1


def test_no_sessions_means_no_rate_not_a_zero_rate():
    """Acceptance criteria proven here:

    AC-OBS-007.5
    """
    sig = rr.pair_signals([], window_days=30)
    assert sig["stuck_rate"] is None
    assert sig["has_history"] is False


def test_signal_kind_mirrors_the_daemon_mapping():
    """If sync.py learns a new detector signature, this catches the drift."""
    from clawmetry import sync

    for signature, kind in sync._LOOPS_KIND_BY_SIGNATURE.items():
        assert rr.signal_kind(signature, None) == kind


def test_unrecognised_signature_is_still_a_loop():
    """The proxy LoopDetector writes a request hash, not a named signature.
    Dropping it would under-report the stuck rate."""
    assert rr.signal_kind("a1b2c3d4", None) == "stuck_loop"
    assert rr.signal_kind("", None) is None
    assert rr.signal_kind(None, None) is None


def test_details_json_string_is_parsed():
    """DuckDB hands details back as a JSON string on some paths."""
    assert rr.signal_kind("x", json.dumps({"kind": "no_progress"})) == "no_progress"


# ── repo discovery ─────────────────────────────────────────────────────────

def test_sessions_are_grouped_by_git_root(tmp_path):
    repo = tmp_path / "proj"
    (repo / ".git").mkdir(parents=True)
    deep = repo / "src" / "pkg"
    deep.mkdir(parents=True)
    rows = [_row("s1", str(repo)), _row("s2", str(deep))]
    grouped = rr.group_by_repo(rows)
    assert list(grouped) == [str(repo)]
    assert len(grouped[str(repo)]) == 2


def test_a_directory_outside_any_repo_stands_on_its_own(tmp_path):
    loose = tmp_path / "loose"
    loose.mkdir()
    grouped = rr.group_by_repo([_row("s1", str(loose))])
    assert str(loose) in grouped


def test_rank_repos_puts_the_busiest_first(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    a.mkdir()
    b.mkdir()
    rows = [_row("s1", str(a)), _row("s2", str(a)), _row("s3", str(b))]
    ranked = rr.rank_repos(rows, window_days=30)
    assert ranked[0]["path"] == str(a)
    assert ranked[0]["signals"]["sessions"] == 2


def test_rows_without_a_cwd_are_dropped_not_guessed():
    """A session with no recorded directory cannot be attributed to a repo,
    and guessing one would fabricate the very correlation this shows."""
    assert rr.group_by_repo([_row("s1", None), _row("s2", "")]) == {}


def test_git_root_finds_a_worktree(tmp_path):
    """In a worktree or submodule, .git is a FILE, not a directory."""
    wt = tmp_path / "wt"
    wt.mkdir()
    (wt / ".git").write_text("gitdir: /elsewhere/.git/worktrees/wt\n")
    (wt / "sub").mkdir()
    assert rr.git_root(str(wt / "sub")) == str(wt)
    # A cwd whose subdirectory has since been deleted still maps to its repo:
    # the walk is over path segments, not over what survives on disk.
    assert rr.git_root(str(wt / "gone")) == str(wt)
    assert rr.git_root("") is None
    assert rr.git_root(None) is None


# ── probe helpers ──────────────────────────────────────────────────────────

def test_makefile_recipe_lines_are_not_targets():
    """A tab-indented recipe line containing a colon is not a target. Reading
    it as one would pass a repo with no test target at all."""
    mk = "build:\n\techo not:a:target\n\ncheck-deps: build\n\techo x\n"
    assert rr._make_targets(mk) == {"build", "check-deps"}


def test_makefile_variable_assignment_is_not_a_target():
    assert "PY" not in rr._make_targets("PY := python3\ntest:\n\tpytest\n")


def test_phony_is_not_a_target():
    assert rr._make_targets(".PHONY: test\ntest:\n\tpytest\n") == {"test"}


def test_toml_sections_is_a_literal_scan():
    text = "[build-system]\nrequires = []\n[tool.ruff]\nline-length = 100\n"
    assert rr._toml_sections(text) == {"build-system", "tool.ruff"}


def test_case_insensitive_filesystem_reports_one_makefile(tmp_path):
    """On macOS and Windows, Makefile and makefile are the SAME file. Probing
    both must not report it twice."""
    d = tmp_path / "mk"
    d.mkdir()
    (d / "Makefile").write_text("test:\n\tpytest\n")
    detail = rr._check_test_command(str(d))["detail"]
    assert detail.lower().count("makefile") == 1
