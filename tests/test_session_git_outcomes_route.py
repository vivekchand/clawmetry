"""GET /api/sessions/<id>/git-outcomes: the per-session view of the git join.

Reads only the tables ``ingest_git_scan`` already persists (no git command
runs). Asserts the honest empties (disabled -> enabled:false with a reason;
no scan yet -> available:false), the per-commit fields (sha, subject,
authored_at, merged, PR state, confidence, basis) and the commits / prs counts
on /api/sessions rows. Temp DuckDB only.
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")
    monkeypatch.delenv("CLAWMETRY_GIT_OUTCOMES", raising=False)
    import clawmetry.local_store as ls
    importlib.reload(ls)
    import routes.sessions as sessions_mod
    importlib.reload(sessions_mod)
    a = Flask(__name__)
    a.register_blueprint(sessions_mod.bp_sessions)
    yield a, ls
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


REPO = "/work/demo-repo"
SID = "claude_code:git-sess-1"
OTHER = "claude_code:git-sess-2"


def _seed(store):
    store.ingest_session({"agent_type": "claude_code", "session_id": SID, "node_id": "n",
                          "title": "ship the fix", "cwd": REPO, "git_branch": "fix/rounding",
                          "started_at": "2026-09-01T10:00:00Z",
                          "last_active_at": "2026-09-01T10:30:00Z"})
    store.ingest_session({"agent_type": "claude_code", "session_id": OTHER, "node_id": "n",
                          "title": "nothing shipped", "cwd": REPO,
                          "started_at": "2026-09-01T11:00:00Z",
                          "last_active_at": "2026-09-01T11:10:00Z"})
    scan = {
        "repo_root": REPO, "remote_url": "git@github.com:acme/demo.git",
        "host": "github.com", "owner": "acme", "name": "demo",
        "default_branch": "main", "branch_basis": "remote_head",
        "merge_basis": "ancestry", "pr_basis": "gh_cli",
        "commits_seen": 3, "window_since": 1, "window_until": 2, "scan_secs": 0.1,
        "commits": [
            {"sha": "a" * 40, "authored_at": 1756720000, "author_name": "dev",
             "subject": "Fix invoice rounding", "insertions": 12, "deletions": 3,
             "merged": True, "branch_hint": "fix/rounding", "files": []},
            {"sha": "b" * 40, "authored_at": 1756720600, "author_name": "dev",
             "subject": "WIP experiment", "insertions": 1, "deletions": 0,
             "merged": False, "branch_hint": "fix/rounding", "files": []},
            {"sha": "c" * 40, "authored_at": 1756721200, "author_name": "dev",
             "subject": "Unrelated commit", "merged": True, "branch_hint": "main", "files": []},
        ],
        "pull_requests": [
            {"number": 42, "state": "MERGED", "title": "Fix invoice rounding",
             "url": "https://github.com/acme/demo/pull/42", "merged_at": 1756721000,
             "head_branch": "fix/rounding", "base_branch": "main", "merge_commit": "a" * 40},
        ],
        "links": [
            {"sha": "a" * 40, "session_id": SID, "confidence": "high",
             "basis": "branch+time", "matched_branch": "fix/rounding"},
            {"sha": "b" * 40, "session_id": SID, "confidence": "medium",
             "basis": "repo+time", "matched_branch": ""},
        ],
    }
    counts = store.ingest_git_scan(scan)
    assert counts["commits"] == 3 and counts["links"] == 2


def test_disabled_returns_honest_reason(app, monkeypatch):
    a, ls = app
    monkeypatch.setenv("CLAWMETRY_GIT_OUTCOMES", "0")
    body = a.test_client().get(f"/api/sessions/{SID}/git-outcomes").get_json()
    assert body["enabled"] is False
    assert body["available"] is False
    assert "disabled" in body["reason"]
    assert body["commits"] == [] and body["prs"] == []


def test_no_scan_yet_is_available_false_not_empty_success(app):
    a, ls = app
    ls.get_store().ingest_session({"agent_type": "claude_code", "session_id": SID,
                                   "node_id": "n", "started_at": "2026-09-01T10:00:00Z",
                                   "last_active_at": "2026-09-01T10:30:00Z"})
    body = a.test_client().get(f"/api/sessions/{SID}/git-outcomes").get_json()
    assert body["enabled"] is True
    assert body["available"] is False
    assert body["reason"] == "no_repositories_scanned"
    assert body["counts"]["commits"] == 0


def test_per_session_commits_with_confidence_and_pr_state(app):
    a, ls = app
    _seed(ls.get_store())
    body = a.test_client().get(f"/api/sessions/{SID}/git-outcomes").get_json()
    assert body["enabled"] is True and body["available"] is True
    assert body["session_id"] == SID
    shas = [c["sha"] for c in body["commits"]]
    assert shas == ["a" * 40, "b" * 40]          # authored order, only linked commits
    first = body["commits"][0]
    assert first["subject"] == "Fix invoice rounding"
    assert first["authored_at"] == 1756720000
    assert first["merged"] is True
    assert first["confidence"] == "high" and first["basis"] == "branch+time"
    assert first["pr_number"] == 42 and first["pr_state"] == "MERGED"
    second = body["commits"][1]
    assert second["merged"] is False and second["confidence"] == "medium"
    # The unmerged commit shares the PR's head branch, so the PR is
    # attached by branch; the PR list itself is de-duplicated.
    assert [p["number"] for p in body["prs"]] == [42]
    assert body["prs"][0]["url"].endswith("/pull/42")
    assert body["counts"] == {"commits": 2, "merged": 1, "prs": 1, "prs_merged": 1}
    assert body["repos"][0]["name"] == "demo"
    assert body["repos"][0]["merge_basis"] == "ancestry"


def test_session_without_links_is_scanned_but_empty(app):
    a, ls = app
    _seed(ls.get_store())
    body = a.test_client().get(f"/api/sessions/{OTHER}/git-outcomes").get_json()
    assert body["available"] is True          # a scan did reach this repository
    assert body["commits"] == [] and body["prs"] == []
    assert body["counts"]["commits"] == 0


def test_sessions_rows_carry_commit_and_pr_counts(app):
    a, ls = app
    _seed(ls.get_store())
    body = a.test_client().get("/api/sessions").get_json()
    rows = {r["session_id"]: r for r in body["sessions"]}
    assert rows[SID]["commits"] == 2 and rows[SID]["prs"] == 1
    assert rows[OTHER]["commits"] == 0 and rows[OTHER]["prs"] == 0
    counts = ls.get_store().query_session_git_counts()
    assert counts[SID] == {"commits": 2, "prs": 1}


def test_bad_session_id_is_400(app):
    a, _ls = app
    assert a.test_client().get("/api/sessions/%20/git-outcomes").status_code == 400


def test_new_store_methods_are_daemon_allowlisted():
    from routes.local_query import _DAEMON_METHODS
    for m in ("query_session_git_outcomes", "get_session_intent",
              "query_session_intents", "query_session_git_counts"):
        assert m in _DAEMON_METHODS, m
