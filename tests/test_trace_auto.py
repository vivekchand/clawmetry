"""Automatic tracing: capture on push, publish where declared, comment once.

The rule under all of it: this runs from a `pre-push` hook, so nothing here
may ever prevent somebody pushing code. An observability tool that can block a
push is worse than no observability tool.
"""

from __future__ import annotations

import json
import subprocess
import sys
import types

import pytest

from clawmetry import trace_auto


def _repo(tmp_path):
    r = str(tmp_path)
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=r, check=True)
    subprocess.run(["git", "config", "user.email", "a@b.c"], cwd=r, check=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=r, check=True)
    (tmp_path / "a.txt").write_text("1")
    subprocess.run(["git", "add", "-A"], cwd=r, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "base"], cwd=r, check=True)
    return r


# ── policy ─────────────────────────────────────────────────────────────────

def test_publishing_is_off_until_the_repo_opts_in(tmp_path):
    """CLAUDE.md control plane: a write is fine when it is user-initiated or
    declared in a policy the user wrote. Nobody has written one yet."""
    assert trace_auto._flag(_repo(tmp_path), trace_auto.CFG_AUTO) is False


def test_opting_in_is_recorded_per_repository(tmp_path):
    repo = _repo(tmp_path)
    trace_auto.set_policy(repo, publish=True)
    assert trace_auto._flag(repo, trace_auto.CFG_AUTO) is True
    # per clone, not global: a second repo is unaffected
    other = _repo(tmp_path / "other") if (tmp_path / "other").mkdir() or True else None
    assert trace_auto._flag(other, trace_auto.CFG_AUTO) is False


def test_commenting_defaults_on_once_publishing_is_on(tmp_path):
    repo = _repo(tmp_path)
    assert trace_auto._flag(repo, trace_auto.CFG_COMMENT, default=True) is True


# ── the run never blocks a push ────────────────────────────────────────────

def test_run_never_raises_on_a_broken_repo():
    res = trace_auto.run("/nonexistent/repo/path")
    assert isinstance(res, dict)


def test_run_skips_silently_when_no_commits_are_agent_authored(tmp_path, monkeypatch):
    """A human's branch must not grow a bot comment announcing that no AI was
    involved. Silence is the correct output."""
    repo = _repo(tmp_path)
    monkeypatch.setattr(trace_auto.trace_capture, "infer_range", lambda r: "a..b")
    monkeypatch.setattr(trace_auto.trace_capture, "read_commits",
                        lambda r, rng: [{"sha": "x", "session_id": None,
                                         "ai_coauthored": False, "ts": 1,
                                         "subject": "s", "short_sha": "x"}])
    res = trace_auto.run(repo)
    assert res["ok"] is True and res["skipped"] == "no agent commits"


def test_run_waits_for_the_pull_request_to_exist(tmp_path, monkeypatch):
    repo = _repo(tmp_path)
    monkeypatch.setattr(trace_auto.trace_capture, "infer_range", lambda r: "a..b")
    monkeypatch.setattr(trace_auto.trace_capture, "read_commits",
                        lambda r, rng: [{"sha": "x", "session_id": "claude_code:s1",
                                         "ai_coauthored": True, "ts": 1,
                                         "subject": "s", "short_sha": "x"}])
    monkeypatch.setattr(trace_auto.trace_capture, "infer_pr", lambda r: None)
    res = trace_auto.run(repo)
    assert res["ok"] is True and "no open pull request" in res["skipped"]


# ── the comment ────────────────────────────────────────────────────────────

def _bundle(attr="exact", upper=False):
    return {"project": "o/r", "pr": "42", "attribution": attr,
            "summary": {"prompts": 4, "turns": 40, "tools": 12,
                        "cost_usd": 1.5, "tokens": 100,
                        "models": {"claude-opus-5": 40},
                        "cost_is_upper_bound": upper}}


def test_comment_carries_the_link_and_the_marker():
    body = trace_auto.render_comment(_bundle(), "https://trace.example/x")
    assert "https://trace.example/x" in body
    assert trace_auto.COMMENT_MARKER in body, "no marker means a new comment per push"


def test_comment_flags_an_upper_bound_rather_than_stating_a_figure():
    body = trace_auto.render_comment(_bundle("shared", upper=True), "u")
    assert "upper bound" in body


def test_comment_labels_a_guess_as_a_guess():
    body = trace_auto.render_comment(_bundle("heuristic"), "u")
    assert "`heuristic`" in body
    assert "hint, not a measurement" in body


def test_comment_is_updated_not_appended(tmp_path, monkeypatch):
    """Drift Bot's convention. A bot that comments on every push is muted."""
    calls = []
    monkeypatch.setattr(trace_auto, "_gh_available", lambda: True)

    def _fake(cmd, **kw):
        calls.append(cmd)
        if "view" in cmd:
            return types.SimpleNamespace(returncode=0, stdout=json.dumps(
                {"comments": [{"body": "old " + trace_auto.COMMENT_MARKER,
                               "url": "u"}]}), stderr="")
        return types.SimpleNamespace(returncode=0, stdout="posted", stderr="")

    monkeypatch.setattr(subprocess, "run", _fake)
    res = trace_auto.post_comment(str(tmp_path), "42", "body")
    assert res["ok"] and res["updated"] is True
    assert any("--edit-last" in c for c in calls), "must edit, not append"


def test_comment_posts_fresh_when_none_exists(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(trace_auto, "_gh_available", lambda: True)

    def _fake(cmd, **kw):
        calls.append(cmd)
        if "view" in cmd:
            return types.SimpleNamespace(returncode=0,
                                         stdout=json.dumps({"comments": []}), stderr="")
        return types.SimpleNamespace(returncode=0, stdout="posted", stderr="")

    monkeypatch.setattr(subprocess, "run", _fake)
    res = trace_auto.post_comment(str(tmp_path), "42", "body")
    assert res["ok"] and res["updated"] is False
    assert not any("--edit-last" in c for c in calls)


def test_comment_degrades_when_gh_is_absent(tmp_path, monkeypatch):
    monkeypatch.setattr(trace_auto, "_gh_available", lambda: False)
    res = trace_auto.post_comment(str(tmp_path), "42", "body")
    assert res["ok"] is False and "gh" in res["error"]


# ── the default is automatic ───────────────────────────────────────────────

def test_plain_init_turns_everything_on(tmp_path, monkeypatch):
    """`trace init` and nothing else. Requiring a second flag on top of an
    already-explicit command was the same mistake as asking for a revision
    range: a manual step the project's conventions say should not exist."""
    from clawmetry import cli, trace_stamp
    monkeypatch.setattr(trace_stamp, "hook_command_works", lambda cmd="clawmetry": True)
    repo = _repo(tmp_path)
    assert cli.trace_main(["init", "--repo", repo]) == 0
    assert trace_auto._flag(repo, trace_auto.CFG_AUTO) is True
    assert trace_auto._flag(repo, trace_auto.CFG_COMMENT) is True
    import os
    assert os.path.exists(os.path.join(repo, ".git", "hooks", "pre-push"))
    assert os.path.exists(os.path.join(repo, ".git", "hooks", "prepare-commit-msg"))


def test_no_publish_opts_out_but_still_stamps(tmp_path, monkeypatch):
    from clawmetry import cli, trace_stamp
    monkeypatch.setattr(trace_stamp, "hook_command_works", lambda cmd="clawmetry": True)
    repo = _repo(tmp_path)
    assert cli.trace_main(["init", "--no-publish", "--repo", repo]) == 0
    assert trace_auto._flag(repo, trace_auto.CFG_AUTO) is False
    import os
    assert os.path.exists(os.path.join(repo, ".git", "hooks", "prepare-commit-msg"))


def test_a_foreign_prepush_hook_is_never_clobbered(tmp_path, monkeypatch):
    """Stamping should still work even if we cannot own the push hook."""
    from clawmetry import cli, trace_stamp
    import os
    monkeypatch.setattr(trace_stamp, "hook_command_works", lambda cmd="clawmetry": True)
    repo = _repo(tmp_path)
    hooks = os.path.join(repo, ".git", "hooks")
    os.makedirs(hooks, exist_ok=True)
    with open(os.path.join(hooks, "pre-push"), "w") as fh:
        fh.write("#!/bin/sh\necho someone elses hook\n")
    assert cli.trace_main(["init", "--repo", repo]) == 0
    with open(os.path.join(hooks, "pre-push")) as fh:
        assert "someone elses hook" in fh.read()
    assert trace_auto._flag(repo, trace_auto.CFG_AUTO) is False
