"""Commit stamping for PR-trace attribution (PRD-pr-trace.md §4a).

Covers the proposed criteria AC-TRACE-001.1 (a stamped commit resolves to its
session) and AC-TRACE-001.2 (no runtime => no claim). Those ids are not yet in
``docs/acceptance_criteria.json`` -- the manifest is mirrored from 8090
Software Factory and must be refreshed with ``make ac-sync``, never hand-edited
(FLYWHEEL §1g). They are named here so the link exists the moment they land.

The behaviour that matters most is the one that is easiest to get wrong:
**stamping must never block a commit.** Every failure path returns the original
message rather than raising.
"""

from __future__ import annotations

import os
import subprocess

import pytest

from clawmetry import trace_stamp


@pytest.fixture(autouse=True)
def _clear_runtime_env(monkeypatch):
    """Tests must not inherit the session id of the agent running them."""
    for var, _ in trace_stamp._ENV_LADDER:
        monkeypatch.delenv(var, raising=False)


# ── detection ──────────────────────────────────────────────────────────────

def test_detects_claude_code_session_and_prefixes_it(monkeypatch):
    """AC-TRACE-001.1 -- the env id becomes the LocalStore key."""
    monkeypatch.setenv("CLAUDE_CODE_SESSION_ID", "36f12caf-56e7-4d1d-9db2-89808ad3d03a")
    assert trace_stamp.detect_session_id() == (
        "claude_code:36f12caf-56e7-4d1d-9db2-89808ad3d03a"
    )


def test_explicit_override_is_used_verbatim(monkeypatch):
    monkeypatch.setenv("CLAWMETRY_SESSION_ID", "openclaw:abc123")
    monkeypatch.setenv("CLAUDE_CODE_SESSION_ID", "ignored")
    assert trace_stamp.detect_session_id() == "openclaw:abc123"


def test_no_runtime_means_no_session():
    """AC-TRACE-001.2 -- a human commit makes no attribution claim."""
    assert trace_stamp.detect_session_id() is None


def test_malformed_session_id_is_ignored(monkeypatch):
    monkeypatch.setenv("CLAUDE_CODE_SESSION_ID", "has spaces and\nnewlines")
    assert trace_stamp.detect_session_id() is None


@pytest.mark.parametrize("runtime_var,prefix", [
    ("OPENCLAW_SESSION_ID", "openclaw"),
    ("CODEX_SESSION_ID", "codex"),
    ("CURSOR_SESSION_ID", "cursor"),
    ("GOOSE_SESSION_ID", "goose"),
])
def test_every_runtime_in_the_ladder_resolves(monkeypatch, runtime_var, prefix):
    monkeypatch.setenv(runtime_var, "s1")
    assert trace_stamp.detect_session_id() == f"{prefix}:s1"


# ── stamping ───────────────────────────────────────────────────────────────

def test_stamp_appends_trailer():
    out = trace_stamp.stamp("fix: a thing\n", session_id="claude_code:abc")
    assert out.rstrip("\n").endswith("Clawmetry-Session: claude_code:abc")
    assert out.startswith("fix: a thing")
    assert "\n\nClawmetry-Session:" in out, "trailer needs a blank line before it"


def test_stamp_is_idempotent():
    once = trace_stamp.stamp("fix: a thing\n", session_id="claude_code:abc")
    twice = trace_stamp.stamp(once, session_id="claude_code:abc")
    assert once == twice
    assert twice.count("Clawmetry-Session:") == 1


def test_stamp_does_not_double_when_amending_with_a_different_session():
    """An amend must not stack a second, conflicting attribution."""
    once = trace_stamp.stamp("fix: a thing\n", session_id="claude_code:abc")
    again = trace_stamp.stamp(once, session_id="claude_code:zzz")
    assert again.count("Clawmetry-Session:") == 1
    assert "claude_code:abc" in again


def test_stamp_joins_an_existing_trailer_block():
    msg = "feat: x\n\nCo-Authored-By: Someone <a@b.c>\n"
    out = trace_stamp.stamp(msg, session_id="claude_code:abc")
    lines = [ln for ln in out.split("\n") if ln.strip()]
    assert lines[-2].startswith("Co-Authored-By:")
    assert lines[-1].startswith("Clawmetry-Session:")
    assert "\n\nClawmetry-Session" not in out, "no blank line inside a trailer block"


def test_stamp_keeps_git_comment_block_last():
    msg = "feat: x\n\n# Please enter the commit message\n# with '#' ignored.\n"
    out = trace_stamp.stamp(msg, session_id="claude_code:abc")
    body, comments = [], []
    for ln in out.split("\n"):
        (comments if ln.startswith("#") else body).append(ln)
    assert any("Clawmetry-Session" in ln for ln in body)
    assert out.index("Clawmetry-Session") < out.index("# Please enter")


def test_stamp_without_a_session_is_a_no_op():
    assert trace_stamp.stamp("fix: a thing\n") == "fix: a thing\n"


def test_stamp_never_raises_on_garbage():
    assert trace_stamp.stamp(None) == ""
    assert trace_stamp.stamp("") == ""


def test_existing_trailer_is_readable_back():
    out = trace_stamp.stamp("x\n", session_id="claude_code:abc")
    assert trace_stamp.existing_trailer(out) == "claude_code:abc"
    assert trace_stamp.existing_trailer("no trailer here") is None


# ── hook install ───────────────────────────────────────────────────────────

def _git_repo(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    return str(tmp_path)


def test_install_creates_an_executable_hook(tmp_path):
    repo = _git_repo(tmp_path)
    res = trace_stamp.install(repo)
    assert res["ok"] and res["status"] == "installed"
    assert os.access(res["path"], os.X_OK)
    with open(res["path"]) as fh:
        assert "clawmetry trace stamp" in fh.read()


def test_install_is_idempotent(tmp_path):
    repo = _git_repo(tmp_path)
    trace_stamp.install(repo)
    assert trace_stamp.install(repo)["status"] == "already-installed"


def test_install_refuses_to_clobber_a_foreign_hook(tmp_path):
    repo = _git_repo(tmp_path)
    hooks = os.path.join(repo, ".git", "hooks")
    os.makedirs(hooks, exist_ok=True)
    path = os.path.join(hooks, "prepare-commit-msg")
    with open(path, "w") as fh:
        fh.write("#!/bin/sh\necho someone elses hook\n")
    res = trace_stamp.install(repo)
    assert not res["ok"] and res["status"] == "foreign-hook"
    with open(path) as fh:
        assert "someone elses hook" in fh.read(), "must not overwrite"


def test_uninstall_removes_only_our_hook(tmp_path):
    repo = _git_repo(tmp_path)
    trace_stamp.install(repo)
    assert trace_stamp.uninstall(repo)["status"] == "removed"
    assert trace_stamp.uninstall(repo)["status"] == "not-installed"


def test_status_reports_installation_and_detection(tmp_path, monkeypatch):
    repo = _git_repo(tmp_path)
    assert trace_stamp.status(repo)["hook_installed"] is False
    trace_stamp.install(repo)
    monkeypatch.setenv("CLAUDE_CODE_SESSION_ID", "abc")
    st = trace_stamp.status(repo)
    assert st["hook_installed"] is True
    assert st["session_id"] == "claude_code:abc"


# ── the end-to-end shape the PRD depends on ────────────────────────────────

def test_stamp_file_round_trip(tmp_path, monkeypatch):
    """AC-TRACE-001.1 -- what git's prepare-commit-msg hook actually calls."""
    monkeypatch.setenv("CLAUDE_CODE_SESSION_ID", "36f12caf")
    msg = tmp_path / "COMMIT_EDITMSG"
    msg.write_text("feat: something\n")
    assert trace_stamp.stamp_file(str(msg)) is True
    assert "Clawmetry-Session: claude_code:36f12caf" in msg.read_text()
    # second call is a no-op, so rebases stay clean
    assert trace_stamp.stamp_file(str(msg)) is False


def test_stamp_file_on_missing_path_does_not_raise():
    assert trace_stamp.stamp_file("/nonexistent/COMMIT_EDITMSG") is False
