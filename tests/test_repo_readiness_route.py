"""Route + snapshot-slice guards for repo AI-readiness (WO-5).

Covers the two things a unit test of the scorer cannot: that the endpoint is
free and ungated, and that the hosted dashboard gets the same card from the
snapshot instead of a blank one (FLYWHEEL section 0a.1, cloud parity).
"""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from clawmetry import repo_readiness as rr  # noqa: E402
import routes.readiness as readiness  # noqa: E402


@pytest.fixture()
def repo(tmp_path):
    d = tmp_path / "proj"
    (d / ".git").mkdir(parents=True)
    (d / "CLAUDE.md").write_text("# project\n")
    (d / "Makefile").write_text(".PHONY: test lint\ntest:\n\tpytest\nlint:\n\truff check .\n")
    return str(d)


def _row(sid, cwd, signature=None, details=None,
         ts="2026-08-20T10:00:00+00:00"):
    return {"session_id": sid, "cwd": cwd, "signature": signature,
            "details": details, "last_active_at": ts}


# ── the endpoint ───────────────────────────────────────────────────────────

def test_payload_scores_the_requested_path(monkeypatch, repo):
    monkeypatch.setattr(readiness, "_repo_activity", lambda days: [])
    body = readiness.readiness_payload(path=repo)
    assert body["status"] == "ok"
    assert body["report"]["path"] == repo
    assert body["report"]["signals"]["has_history"] is False


def test_payload_picks_the_busiest_live_repo(monkeypatch, repo, tmp_path):
    """Acceptance criteria proven here:

    AC-OBS-007.1
    AC-OBS-007.2

    a repo discovered from session history, with the session and stuck counts for that same repo beside its grade.
    """
    quiet = tmp_path / "quiet"
    quiet.mkdir()
    rows = [_row("s1", repo), _row("s2", repo), _row("s3", str(quiet))]
    monkeypatch.setattr(readiness, "_repo_activity", lambda days: rows)
    body = readiness.readiness_payload()
    assert body["report"]["path"] == repo
    assert body["report"]["signals"]["sessions"] == 2
    assert [r["path"] for r in body["repos"]][0] == repo


def test_payload_skips_a_deleted_checkout_when_choosing(monkeypatch, repo):
    """A deleted checkout keeps its history row, but there is nothing left to
    read, so it must not be the repo we open the card on."""
    rows = [_row("s1", "/gone/a"), _row("s2", "/gone/a"), _row("s3", repo)]
    monkeypatch.setattr(readiness, "_repo_activity", lambda days: rows)
    body = readiness.readiness_payload()
    assert body["report"]["path"] == repo
    gone = [r for r in body["repos"] if r["path"] == "/gone/a"][0]
    assert gone["exists"] is False
    assert gone["signals"]["sessions"] == 2


def test_payload_is_honest_when_there_is_nothing_to_score(monkeypatch):
    monkeypatch.setattr(readiness, "_repo_activity", lambda days: [])
    monkeypatch.setattr(readiness, "_fallback_repo", lambda: None)
    body = readiness.readiness_payload()
    assert body["status"] == "no_repo"
    assert body["report"] is None
    assert body["repos"] == []


@pytest.fixture()
def client():
    """Blueprints are wired in dashboard.main(); register ours for the test
    client the same way the other route tests do."""
    import dashboard as _d
    from routes.readiness import bp_readiness

    if "readiness" not in _d.app.blueprints:
        _d.app.register_blueprint(bp_readiness)
    _d.app.config["TESTING"] = True
    return _d.app.test_client()


def test_endpoint_returns_an_honest_body_when_the_store_is_down(
        monkeypatch, client, repo):
    """A locked DuckDB must not turn into a 500 on a first-run dashboard."""
    def boom(days):
        raise RuntimeError("duckdb is locked")
    monkeypatch.setattr(readiness, "_repo_activity", boom)
    resp = client.get("/api/repo-readiness?path=" + repo)
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["status"] == "error"
    assert body["report"] is None


def test_endpoint_serves_a_scored_report(monkeypatch, client, repo):
    monkeypatch.setattr(readiness, "_repo_activity", lambda days: [])
    resp = client.get("/api/repo-readiness?path=" + repo)
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["status"] == "ok"
    assert body["report"]["path"] == repo
    assert body["report"]["score"] in list("ABCDF")


def test_the_hosted_dashboard_never_scores_its_own_checkout(monkeypatch):
    """The cloud container runs from ClawMetry's own source tree. Falling back
    to its working directory there would render a card about OUR repo and
    label it as the user's."""
    monkeypatch.setattr(readiness, "_repo_activity", lambda days: [])
    monkeypatch.setenv("CLAWMETRY_CLOUD", "1")
    body = readiness.readiness_payload()
    assert body["status"] == "no_repo"
    assert body["report"] is None
    monkeypatch.delenv("CLAWMETRY_CLOUD")
    # ...and off cloud the fallback still works, so a first-run local install
    # sees its own repo scored.
    assert readiness._fallback_repo() is not None


def test_endpoint_is_free_and_ungated():
    """Acceptance criteria proven here:

    AC-OBS-007.8

    free and ungated. A lead magnet, not a paid surface.
    """
    src = open(readiness.__file__, encoding="utf-8").read()
    assert "@gate(" not in src
    assert "allows_feature" not in src


def test_endpoint_makes_no_network_calls():
    src = open(readiness.__file__, encoding="utf-8").read()
    for banned in ("import requests", "import httpx", "urlopen", "subprocess"):
        assert banned not in src, banned


def test_window_is_clamped(monkeypatch, repo):
    monkeypatch.setattr(readiness, "_repo_activity", lambda days: [])
    assert readiness.readiness_payload(path=repo, days=99999)["window_days"] == 365
    assert readiness.readiness_payload(path=repo, days="junk")["window_days"] == 30
    assert readiness.readiness_payload(path=repo, days=-5)["window_days"] == 0


def test_a_local_scan_does_not_claim_all_runtimes(monkeypatch, repo):
    """The local endpoint re-scans per runtime, so the card must not show the
    hosted "scored against every runtime" caveat when a filter is on."""
    monkeypatch.setattr(readiness, "_repo_activity", lambda days: [])
    assert readiness.readiness_payload(
        path=repo, runtime="cursor")["scope"] == "cursor"
    assert readiness.readiness_payload(path=repo)["scope"] == "all_runtimes"


def test_runtime_filter_reaches_the_score(monkeypatch, repo):
    monkeypatch.setattr(readiness, "_repo_activity", lambda days: [])
    claude = readiness.readiness_payload(path=repo, runtime="claude_code")
    cursor = readiness.readiness_payload(path=repo, runtime="cursor")
    assert claude["report"]["score_pct"] > cursor["report"]["score_pct"]
    assert readiness.readiness_payload(path=repo, runtime="all")["runtime"] == "all"


# ── cloud parity: the daemon ships the finished card ───────────────────────

class _FakeStore:
    def __init__(self, rows):
        self._rows = rows

    def query_repo_activity(self, **kwargs):
        return self._rows


def test_snapshot_slice_carries_a_scored_report(repo):
    from clawmetry import sync

    slice_ = sync._build_repo_readiness_slice(_FakeStore([_row("s1", repo)]))
    assert slice_["repos"], "the daemon must score the repo, not just list it"
    entry = slice_["repos"][0]
    assert entry["path"] == repo
    assert entry["report"]["score"] in list("ABCDF")
    assert entry["signals"]["sessions"] == 1


def test_snapshot_slice_labels_itself_all_runtimes(repo):
    """The daemon cannot know which runtime the hosted viewer selected, so
    the slice must say so rather than letting the cloud pass node-wide data
    off as runtime-scoped."""
    from clawmetry import sync

    slice_ = sync._build_repo_readiness_slice(_FakeStore([_row("s1", repo)]))
    assert slice_["scope"] == "all_runtimes"


def test_snapshot_slice_leaves_a_deleted_checkout_unscored():
    from clawmetry import sync

    slice_ = sync._build_repo_readiness_slice(_FakeStore([_row("s1", "/gone")]))
    assert slice_["repos"][0]["report"] is None
    assert slice_["repos"][0]["signals"]["sessions"] == 1


def test_snapshot_slice_is_empty_not_broken_when_the_store_fails():
    from clawmetry import sync

    class Broken:
        def query_repo_activity(self, **kwargs):
            raise RuntimeError("no")

    assert sync._build_repo_readiness_slice(Broken()) == {}


def test_snapshot_slice_is_capped(monkeypatch, tmp_path):
    from clawmetry import sync

    rows = []
    for i in range(20):
        d = tmp_path / ("r%d" % i)
        d.mkdir()
        rows.append(_row("s%d" % i, str(d)))
    slice_ = sync._build_repo_readiness_slice(_FakeStore(rows))
    assert len(slice_["repos"]) <= sync._READINESS_SLICE_MAX


# ── the daemon proxy must know the method ──────────────────────────────────

def test_query_repo_activity_is_allowlisted():
    """A store method the dashboard reaches through the daemon proxy is a
    400 until it is named in the allowlist."""
    from routes.local_query import _DAEMON_METHODS

    assert "query_repo_activity" in _DAEMON_METHODS


def test_store_declares_query_repo_activity():
    from clawmetry.local_store import LocalStore

    assert callable(getattr(LocalStore, "query_repo_activity", None))
