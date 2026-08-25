"""Git outcome join — REQ-OBS-CEA-022.

Covers AC-OBS-CEA-022.1 through .9.

These tests build a REAL git repository in a temp directory and run the real
plumbing against it. A mocked ``subprocess.run`` would test that this module
calls git, which is not the thing that can be wrong: what can be wrong is what
git's output means. The repository is four commits and takes about a second to
build, and it is the only way the line-survival arithmetic below is worth
anything.

The fixture repository, and why each piece is there:

    base                 30 lines in a.py          -- something to blame against
    agent adds ten       +10 lines in a.py         -- merged agent work
    human rewrites       3 of those 10 rewritten   -- the rework signal
    agent on a branch    +1 line in b.py, unmerged -- the not-shipped case

So ``agent adds ten`` must measure 10 added, 7 surviving, and the branch commit
must be reported as not merged and must NOT be counted as rework.
"""
from __future__ import annotations

import importlib
import os
import subprocess
import sys
import time

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from clawmetry import git_outcomes as gitout  # noqa: E402


# ── fixtures ───────────────────────────────────────────────────────────────

def _sh(repo, *args):
    subprocess.run(args, cwd=repo, check=True, capture_output=True)


@pytest.fixture(scope="module")
def repo(tmp_path_factory):
    """A four-commit repository with a known rework story."""
    path = str(tmp_path_factory.mktemp("gitjoin-repo"))
    _sh(path, "git", "init", "-q", "-b", "main")
    _sh(path, "git", "config", "user.email", "agent@example.invalid")
    _sh(path, "git", "config", "user.name", "Test Agent")
    _sh(path, "git", "config", "commit.gpgsign", "false")

    a = os.path.join(path, "a.py")
    with open(a, "w") as fh:
        fh.write("\n".join(f"line{i}" for i in range(30)) + "\n")
    _sh(path, "git", "add", "-A")
    _sh(path, "git", "commit", "-q", "-m", "base")

    with open(a, "a") as fh:
        fh.write("\n".join(f"agent{i}" for i in range(10)) + "\n")
    _sh(path, "git", "add", "-A")
    _sh(path, "git", "commit", "-q", "-m", "agent adds ten lines")

    with open(a) as fh:
        body = fh.read()
    for n in (3, 4, 5):
        body = body.replace(f"agent{n}\n", f"HUMAN{n}\n")
    with open(a, "w") as fh:
        fh.write(body)
    _sh(path, "git", "add", "-A")
    _sh(path, "git", "commit", "-q", "-m", "human rewrites three of them")

    _sh(path, "git", "checkout", "-q", "-b", "feat/x")
    with open(os.path.join(path, "b.py"), "w") as fh:
        fh.write("x = 1\n")
    _sh(path, "git", "add", "-A")
    _sh(path, "git", "commit", "-q", "-m", "agent on a branch")
    _sh(path, "git", "checkout", "-q", "main")
    return path


@pytest.fixture(scope="module")
def scan(repo):
    now = int(time.time())
    sessions = [
        {"session_id": "claude_code:on-main", "cwd": repo, "git_branch": "main",
         "started_epoch": now - 600, "last_active_epoch": now},
        {"session_id": "claude_code:on-branch", "cwd": repo,
         "git_branch": "feat/x",
         "started_epoch": now - 600, "last_active_epoch": now},
    ]
    return gitout.scan_repo(repo, sessions, since_epoch=now - 86400)


@pytest.fixture
def store(tmp_path, monkeypatch, scan, repo):
    """A LocalStore on a temp DuckDB file, loaded with the fixture scan.

    ``CLAWMETRY_LOCAL_STORE_PATH`` is set BEFORE the module reload so nothing
    here can touch the operator's real ``~/.clawmetry`` store — a test suite
    has taken this machine out of local-only mode before.
    """
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "t.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")
    import clawmetry.local_store as ls
    importlib.reload(ls)
    st = ls.get_store()
    stamp = time.strftime("%Y-%m-%dT%H:%M:%S+00:00")
    st.ingest_session({
        "agent_type": "openclaw", "session_id": "claude_code:on-main",
        "cwd": repo, "git_branch": "main", "cost_usd": 4.0,
        "started_at": stamp, "last_active_at": stamp, "metadata": {},
    })
    st.ingest_session({
        "agent_type": "openclaw", "session_id": "claude_code:on-branch",
        "cwd": repo, "git_branch": "feat/x", "cost_usd": 1.0,
        "started_at": stamp, "last_active_at": stamp,
        "metadata": {"end_reason": "completed"},
    })
    # A session that ended, spent money, and never went near a repository.
    st.ingest_session({
        "agent_type": "openclaw", "session_id": "codex:nowhere",
        "cost_usd": 2.5, "started_at": stamp, "last_active_at": stamp,
        "metadata": {"end_reason": "completed"},
    })
    st.ingest_git_scan(scan)
    yield st
    try:
        st.stop(flush=True)
    except Exception:
        pass


# ── AC-OBS-CEA-022.2: never writes to a user repository ────────────────────

@pytest.mark.parametrize("args", [
    ("fetch",), ("pull",), ("checkout", "main"), ("gc",), ("clean", "-fd"),
    ("reset", "--hard"), ("commit", "-m", "x"), ("push",), ("stash",),
    ("config", "user.name", "hacked"), ("remote", "add", "evil", "url"),
])
def test_write_commands_are_refused(args):
    """The read-only guard rejects anything that could write.

    * AC-OBS-CEA-022.2 -- covered by this test.
    """
    with pytest.raises(gitout.UnsafeGitCommand):
        gitout._assert_read_only(args)


@pytest.mark.parametrize("args", [
    ("log", "--all"), ("rev-parse", "--show-toplevel"), ("rev-list", "main"),
    ("blame", "--incremental", "main", "--", "a.py"),
    ("config", "--get", "user.name"), ("remote", "get-url", "origin"),
])
def test_read_commands_are_permitted(args):
    """The reads the feature actually needs still pass.

    * AC-OBS-CEA-022.2 -- covered by this test.
    """
    gitout._assert_read_only(args)


def test_scan_leaves_the_repository_untouched(repo, scan):
    """A full scan changes no state in the repository.

    * AC-OBS-CEA-022.2 -- covered by this test.
    """
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo,
                          capture_output=True, text=True).stdout.strip()
    branch = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"],
                            cwd=repo, capture_output=True, text=True).stdout.strip()
    status = subprocess.run(["git", "status", "--porcelain"], cwd=repo,
                            capture_output=True, text=True).stdout
    gitout.scan_repo(repo, [], since_epoch=int(time.time()) - 86400)
    assert subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo,
                          capture_output=True, text=True).stdout.strip() == head
    assert subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=repo,
                          capture_output=True, text=True).stdout.strip() == branch
    assert subprocess.run(["git", "status", "--porcelain"], cwd=repo,
                          capture_output=True, text=True).stdout == status


# ── AC-OBS-CEA-022.1: merged / branch-only / neither ───────────────────────

def test_merge_state_distinguishes_shipped_from_branch_only(scan):
    """AC-OBS-CEA-022.1: reaching the default branch and reaching a branch
    
    * AC-OBS-CEA-022.1 -- covered by this test.
    only are reported as different outcomes."""
    by_subject = {c["subject"]: c for c in scan["commits"]}
    assert by_subject["agent adds ten lines"]["merged"] is True
    assert by_subject["agent on a branch"]["merged"] is False


def test_outcome_metrics_report_shipped_spend_and_its_denominator(store):
    """AC-OBS-CEA-022.1: the cost of shipped work is reported with the count
    
    * AC-OBS-CEA-022.1 -- covered by this test.
    of merged units it was divided by."""
    out = store.query_git_outcomes()
    m = out["metrics"]["cost_per_merged_change"]
    assert m["available"] is True
    assert m["denominator"] >= 1
    assert m["numerator_usd"] > 0
    # 4-decimal rounding on the stored figure; the identity still has to hold.
    assert m["value"] == pytest.approx(
        m["numerator_usd"] / m["denominator"], abs=1e-4)


# ── AC-OBS-CEA-022.3: degrade when the code host is unavailable ────────────

def test_no_remote_reports_pull_request_state_unavailable(scan):
    """AC-OBS-CEA-022.3: a repository with no code host reports that fact and
    
    * AC-OBS-CEA-022.3 -- covered by this test.
    still produces every local figure."""
    assert scan["pull_requests"] is None
    assert scan["pr_basis"] == "no_code_host_remote"
    assert scan["commits"], "local commit facts must survive a missing host"


def test_missing_gh_is_reported_not_raised(repo, monkeypatch):
    """AC-OBS-CEA-022.3: no ``gh`` on PATH degrades, it does not fail."""
    monkeypatch.setattr(gitout.shutil, "which", lambda _n: None)
    prs, basis = gitout.read_pull_requests(repo)
    assert prs is None
    assert basis == "gh_not_installed"


def test_metrics_fall_back_to_branch_state_without_pull_requests(store):
    """AC-OBS-CEA-022.3: without pull-request data the denominator is merged
    
    * AC-OBS-CEA-022.3 -- covered by this test.
    commits, and the response says so rather than pretending otherwise."""
    out = store.query_git_outcomes()
    m = out["metrics"]["cost_per_merged_change"]
    assert m["basis"] == "branch_reachability"
    assert m["denominator_kind"] == "merged_commits"


# ── AC-OBS-CEA-022.4: every figure carries its basis; uncertainty shows ────

def test_every_metric_carries_a_basis(store):
    """AC-OBS-CEA-022.4: no figure is reported without what it rests on."""
    out = store.query_git_outcomes()
    for name, metric in out["metrics"].items():
        assert metric.get("basis"), f"{name} has no basis"
        assert "available" in metric


def test_correlation_confidence_is_recorded_and_distinguishable(scan):
    """AC-OBS-CEA-022.4: a link backed by an agreeing branch is not reported
    
    * AC-OBS-CEA-022.4 -- covered by this test.
    as the same strength as one backed by time alone."""
    confs = {ln["confidence"] for ln in scan["links"]}
    assert "high" in confs
    by = {(ln["session_id"], ln["sha"]): ln for ln in scan["links"]}
    branch_sha = [c["sha"] for c in scan["commits"]
                  if c["subject"] == "agent on a branch"][0]
    assert by[("claude_code:on-branch", branch_sha)]["confidence"] == "high"
    assert by[("claude_code:on-main", branch_sha)]["confidence"] == "low"


def test_weak_links_are_excluded_and_counted_not_hidden(store):
    """AC-OBS-CEA-022.4: links below the requested confidence are reported as
    
    * AC-OBS-CEA-022.4 -- covered by this test.
    an exclusion count rather than silently dropped or silently mixed in."""
    out = store.query_git_outcomes(min_confidence="high")
    cov = out["coverage"]
    assert cov["min_confidence"] == "high"
    assert cov["links_excluded"] > 0
    assert sum(cov["links_by_confidence"].values()) > cov["links_excluded"]


def test_a_real_zero_is_not_reported_as_missing():
    """AC-OBS-CEA-022.4: ``available`` follows ``value is not None``.

    ``or`` on a float has already turned a genuine 0.0 into a false "stale
    data" state in this codebase. A rework rate of 0.0 is the best possible
    answer and must not render as "no data".
    
    * AC-OBS-CEA-022.4 -- covered by this test.
    """
    from clawmetry.local_store import _git_metric
    zero = _git_metric(value=0.0, basis="line_survival", unit="ratio")
    assert zero["available"] is True
    assert zero["value"] == 0.0
    absent = _git_metric(value=None, basis="line_survival", unit="ratio",
                         reason="no_lines_measured")
    assert absent["available"] is False
    assert absent["reason"] == "no_lines_measured"


# ── AC-OBS-CEA-022.5: abandoned needs an end signal, never silence ─────────

def test_line_survival_measures_rework_exactly(scan):
    """AC-OBS-CEA-022.5 companion: 10 lines added, 3 rewritten, 7 survive."""
    ten = [c for c in scan["commits"]
           if c["subject"] == "agent adds ten lines"][0]
    assert ten["insertions"] == 10
    assert scan["survival"].get(ten["sha"]) == 7


def test_unmerged_work_is_not_counted_as_rework(scan):
    """AC-OBS-CEA-022.5 companion: a commit that has not landed has no lines
    
    * AC-OBS-CEA-022.5 -- covered by this test.
    at the tip because it has not landed, not because anyone rewrote them."""
    branch_commit = [c for c in scan["commits"]
                     if c["subject"] == "agent on a branch"][0]
    assert branch_commit["sha"] not in scan["survival"]


def test_a_quiet_session_is_not_called_abandoned(store):
    """AC-OBS-CEA-022.5: only a session whose runtime reported an end counts.

    ``claude_code:on-main`` has no end signal and produced no *unmerged* work;
    it must not appear in the abandoned figure on the strength of silence.
    
    * AC-OBS-CEA-022.5 -- covered by this test.
    """
    out = store.query_git_outcomes()
    m = out["metrics"]["abandoned_session_spend"]
    assert m["basis"] == "end_reason"
    assert m["sessions_with_end_signal"] == out["coverage"]["sessions_with_end_signal"]
    # The only in-repo session with an end signal produced commits, so nothing
    # is abandoned — and the figure is a real 0.0, not an absence.
    assert m["available"] is True
    assert m["value"] == pytest.approx(0.0)


def test_end_reason_is_read_from_the_session_metadata_blob():
    """AC-OBS-CEA-022.5: the end signal is dug out of the JSON blob, and its
    
    * AC-OBS-CEA-022.5 -- covered by this test.
    absence returns empty rather than a guess."""
    from clawmetry.local_store import _session_end_reason
    assert _session_end_reason(b'{"end_reason": "completed"}') == "completed"
    assert _session_end_reason('{"endReason": "aborted"}') == "aborted"
    assert _session_end_reason({"other": 1}) == ""
    assert _session_end_reason(None) == ""
    assert _session_end_reason(b"not json") == ""


# ── AC-OBS-CEA-022.6: unattributable sessions are counted, not dropped ─────

def test_sessions_without_a_directory_are_counted_not_dropped(store):
    """A session we cannot place is reported as such, with a count.

    * AC-OBS-CEA-022.6 -- covered by this test.
    """
    cov = store.query_git_outcomes()["coverage"]
    assert cov["sessions_in_window"] == 3
    assert cov["sessions_with_cwd"] == 2
    assert cov["sessions_in_known_repo"] == 2
    assert cov["sessions_not_attributable"] == 1
    assert cov["unattributed_spend_usd"] == pytest.approx(2.5)


# ── AC-OBS-CEA-022.7: no per-person attribution ────────────────────────────

def test_no_metric_is_attributed_to_a_person(store):
    """AC-OBS-CEA-022.7: outcomes attribute to runtime, model or repository.

    The author fields exist on a commit row because that is what a commit is;
    what must not exist is a per-person figure in the reported metrics.
    
    * AC-OBS-CEA-022.7 -- covered by this test.
    """
    out = store.query_git_outcomes()
    blob = repr(out["metrics"]) + repr(out["coverage"])
    assert "agent@example.invalid" not in blob
    assert "Test Agent" not in blob
    for metric in out["metrics"].values():
        assert not any("author" in k or "person" in k or "user" in k
                       for k in metric)


# ── AC-OBS-CEA-022.8: shared windows ───────────────────────────────────────

def test_windows_come_from_the_shared_definition():
    """AC-OBS-CEA-022.8: the endpoint accepts only the shared named windows.

    A rolling-7-day option here would report a different weekly figure from
    every other cost card, both "correct" — the exact disagreement ADR-046
    exists to end.
    
    * AC-OBS-CEA-022.8 -- covered by this test.
    """
    import routes.usage as usage_mod
    assert usage_mod._OUTCOME_WINDOWS == ("today", "week", "month")
    from clawmetry.cost_windows import window_start_days
    today, week, month = window_start_days()
    assert today >= week >= month[:8] + "01"


def test_future_window_start_yields_no_sessions(store):
    """AC-OBS-CEA-022.8: the window is applied to the same day bucket the
    
    * AC-OBS-CEA-022.8 -- covered by this test.
    rest of the cost surfaces use."""
    out = store.query_git_outcomes(since_day="2999-01-01")
    assert out["coverage"]["sessions_in_window"] == 0


# ── AC-OBS-CEA-022.9: bounded and switchable ───────────────────────────────

def test_reading_is_bounded(monkeypatch):
    """AC-OBS-CEA-022.9: history, commits, files and wall clock all have
    
    * AC-OBS-CEA-022.9 -- covered by this test.
    ceilings, and each is an operator-settable dial."""
    assert gitout.LOOKBACK_DAYS > 0
    assert gitout.MAX_COMMITS > 0
    assert gitout.MAX_BLAME_FILES >= 0
    assert gitout.CMD_TIMEOUT_SECS > 0
    assert gitout.REPO_BUDGET_SECS > 0
    assert gitout.BLAME_BUDGET_SECS <= gitout.REPO_BUDGET_SECS


def test_feature_can_be_switched_off(monkeypatch):
    """AC-OBS-CEA-022.9: one environment variable disables repository reading."""
    monkeypatch.setenv("CLAWMETRY_GIT_OUTCOMES", "0")
    assert gitout.is_enabled() is False
    monkeypatch.setenv("CLAWMETRY_GIT_OUTCOMES", "1")
    assert gitout.is_enabled() is True


def test_partial_measurement_is_labelled(repo, monkeypatch):
    """AC-OBS-CEA-022.9 + .4: when a cap stops the scan early, the result says
    the measurement is incomplete instead of reporting a rate from a sample as
    
    * AC-OBS-CEA-022.9 -- covered by this test.
    though it covered everything."""
    monkeypatch.setattr(gitout, "MAX_BLAME_FILES", 0)
    now = int(time.time())
    sessions = [{"session_id": "claude_code:on-main", "cwd": repo,
                 "git_branch": "main", "started_epoch": now - 600,
                 "last_active_epoch": now}]
    partial = gitout.scan_repo(repo, sessions, since_epoch=now - 86400)
    assert partial["rework_complete"] is False
    assert partial["measured_files"] == []


# ── plumbing that has bitten before ────────────────────────────────────────

def test_store_methods_are_on_the_daemon_proxy_allowlist():
    """A store method the dashboard calls but the proxy does not allow 400s,
    and the surface silently reports nothing — which is the failure this
    feature exists to stop."""
    from routes.local_query import _DAEMON_METHODS
    for method in ("ingest_git_scan", "query_git_repos", "query_git_outcomes"):
        assert method in _DAEMON_METHODS


def test_no_repositories_scanned_is_an_honest_empty(tmp_path, monkeypatch):
    """An empty answer is an answer: no scan yet reports why, not zeroes."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "e.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")
    import clawmetry.local_store as ls
    importlib.reload(ls)
    st = ls.get_store()
    try:
        out = st.query_git_outcomes()
        assert out["available"] is False
        assert out["reason"] == "no_repositories_scanned"
        assert out["metrics"] == {}
    finally:
        try:
            st.stop(flush=True)
        except Exception:
            pass


def test_branch_names_compare_across_remote_prefixes():
    """``feat/x`` and ``origin/feat/x`` are the same branch; a string compare
    would report a mismatch and downgrade a good link."""
    assert gitout._branch_eq("feat/x", "origin/feat/x")
    assert gitout._branch_eq("main", "refs/remotes/origin/main")
    assert not gitout._branch_eq("main", "feat/x")


# ── the endpoint, end to end ───────────────────────────────────────────────

@pytest.fixture
def client(store, monkeypatch):
    """A Flask client on ``bp_usage``, with daemon discovery steered away.

    Without the discovery override a real ``com.clawmetry.sync`` running on
    the developer's machine answers the request from the operator's own store
    instead of the temp one, and the test silently asserts against live data.
    """
    from flask import Flask
    import routes.local_query as lq
    monkeypatch.setattr(lq, "_DISCOVERY_PATH", "/nonexistent-discovery.json")
    lq._invalidate_daemon_cache()
    import routes.usage as usage_mod
    importlib.reload(usage_mod)
    app = Flask(__name__)
    app.register_blueprint(usage_mod.bp_usage)
    return app.test_client()


def test_endpoint_serves_the_three_figures(client):
    """The whole chain: repository read, store join, HTTP shape.

    * AC-OBS-CEA-022.1 -- covered by this test.
    * AC-OBS-CEA-022.4 -- covered by this test.
    """
    res = client.get("/api/usage/outcomes")
    assert res.status_code == 200
    body = res.get_json()
    assert body["available"] is True
    assert body["window"] == "month"
    assert set(body["metrics"]) == {
        "cost_per_merged_change", "rework_rate", "abandoned_session_spend"}
    assert body["metrics"]["cost_per_merged_change"]["available"] is True
    # 43 lines added across the three merged commits, 40 still at the tip
    # (the human rewrote 3 of the agent's 10). The rate is the aggregate, and
    # it has to equal the identity rather than a number typed by hand.
    rework = body["metrics"]["rework_rate"]
    assert rework["lines_added_measured"] == 43
    assert rework["lines_surviving"] == 40
    assert rework["value"] == pytest.approx(
        1 - rework["lines_surviving"] / rework["lines_added_measured"], abs=1e-4)
    assert body["coverage"]["sessions_not_attributable"] == 1


def test_endpoint_refuses_a_window_it_does_not_share(client):
    """A window this surface invented would disagree with every other cost
    card, both "correct" -- the disagreement ADR-046 exists to end.

    * AC-OBS-CEA-022.8 -- covered by this test.
    """
    res = client.get("/api/usage/outcomes?window=rolling7")
    assert res.status_code == 400
    assert res.get_json()["allowed"] == ["today", "week", "month"]


def test_endpoint_reports_an_honest_empty_without_a_store(monkeypatch):
    """No store, no daemon: report why, never a 500 and never a fake zero.

    * AC-OBS-CEA-022.3 -- covered by this test.
    """
    from flask import Flask
    import routes.usage as usage_mod
    importlib.reload(usage_mod)
    monkeypatch.setattr(usage_mod, "_ls_call", lambda *a, **k: None)
    app = Flask(__name__)
    app.register_blueprint(usage_mod.bp_usage)
    body = app.test_client().get("/api/usage/outcomes").get_json()
    assert body["available"] is False
    assert body["reason"] == "local_store_unavailable"
    assert body["metrics"] == {}
