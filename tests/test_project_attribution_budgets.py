"""Project attribution and per-project budgets (REQ-OBS-PRJ-001, issue #5941).

The question: what did this project spend, against its budget? Before this,
spend grouped only by runtime, model, session or a per-runtime team label, and
there was one budget for the whole machine.

Acceptance criteria proven here (docs/acceptance_criteria.json):

* AC-OBS-PRJ-001.1 -- attributed from where the session ran, with source and
  confidence; a label inside the activity does not decide it:
  ``test_two_repositories_on_one_machine_are_two_projects``,
  ``test_a_project_named_inside_the_activity_is_ignored``
* AC-OBS-PRJ-001.2 -- same directory name, two places, two projects:
  ``test_same_directory_name_in_two_places_stays_two_projects``
* AC-OBS-PRJ-001.3 -- no working directory lands in a visible Unassigned group:
  ``test_a_session_with_no_directory_is_unassigned_not_dropped``
* AC-OBS-PRJ-001.4 -- derived when read; assignments carry period and
  provenance; a correction supersedes without erasing:
  ``test_assignment_covers_history_and_respects_its_effective_period``,
  ``test_a_correction_supersedes_without_erasing``,
  ``test_project_is_not_stored_on_session_rows``
  The collector's ``CLAWMETRY_PROJECT`` is one more operator assignment:
  ``test_env_project_tags_sessions_started_after_the_collector``,
  ``test_env_project_never_overrides_an_operator_assignment``,
  ``test_a_changed_env_project_applies_to_later_sessions_only``,
  ``test_env_project_refuses_a_name_it_cannot_store``,
  ``test_daemon_tick_tags_sessions_from_the_environment``
* AC-OBS-PRJ-001.5 -- no full local path in published figures:
  ``test_same_directory_name_in_two_places_stays_two_projects``,
  ``test_csv_export_by_project_reports_completeness``
* AC-OBS-PRJ-001.6 -- a budget declares its terms; unsupported ones are refused:
  ``test_budget_refuses_terms_it_cannot_honour``
* AC-OBS-PRJ-001.7 -- spend counts in the period it occurred, on the budget's
  timezone: ``test_a_period_boundary_splits_a_session``,
  ``test_a_late_record_alerts_for_the_period_it_belongs_to``
* AC-OBS-PRJ-001.8 -- one alert per threshold per period, delivered, and it
  says it does not stop spend: ``test_budget_alert_fires_once_at_80_percent``,
  ``test_daemon_tick_delivers_each_crossing_exactly_once``,
  ``test_a_repository_budget_keeps_counting_after_the_repository_is_assigned``,
  ``test_usage_buckets_are_reused_between_ticks``
* AC-OBS-PRJ-001.9 -- daily burn next to the budget:
  ``test_status_reports_daily_burn``
  The Usage tab draws the same payload:
  ``test_a_budget_row_shows_spend_against_the_amount_and_never_overflows``
* AC-OBS-PRJ-001.10 -- export carries assigned / unassigned / unpriced and
  completeness; tokens without a price are unpriced, not $0:
  ``test_csv_export_by_project_reports_completeness``
"""
from __future__ import annotations

import csv
import importlib
import io
import json
import os
import sys
from datetime import datetime, timezone

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

NOW = datetime(2026, 9, 2, 12, 0, tzinfo=timezone.utc).timestamp()


@pytest.fixture
def store(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "cm.duckdb"))
    monkeypatch.setenv("CLAWMETRY_AGG_CACHE_TTL", "0")
    import clawmetry.local_store as ls
    importlib.reload(ls)
    monkeypatch.setattr(ls, "_daemon_registered", lambda *a, **k: False)
    s = ls.get_store()
    yield s
    try:
        s.stop(flush=True)
    except Exception:
        pass


def _session(store, sid, cwd, started="2026-09-01T09:00:00Z", **extra):
    row = {"session_id": sid, "node_id": "box1", "started_at": started,
           "last_active_at": started, "cwd": cwd}
    row.update(extra)
    store.ingest_sessions_batch([row])


_EV = {"n": 0}


def _spend(store, sid, ts, cost, tokens=100, data=None):
    _EV["n"] += 1
    store.ingest({"id": f"ev{_EV['n']}", "node_id": "box1", "agent_id": "main",
                  "session_id": sid, "event_type": "assistant", "ts": ts,
                  "data": data or {"type": "assistant"},
                  "cost_usd": cost, "token_count": tokens})
    store.flush()


def _repo(store, root, name=""):
    """A repository the read-only git reader has already recorded."""
    store._conn.execute(
        "INSERT INTO git_repos (repo_root, name, last_scanned_at) VALUES (?, ?, 0)",
        [root, name])


def _by_label(usage):
    return {p["label"]: p for p in usage["projects"]}


def _pid(store, label):
    return _by_label(store.query_project_usage(days=30, now=NOW))[label]["project_id"]


# ── attribution ──────────────────────────────────────────────────────────


def test_two_repositories_on_one_machine_are_two_projects(store):
    """Claude Code, Codex and Copilot, two repositories, one machine."""
    _repo(store, "/work/api")
    _repo(store, "/work/web")
    _session(store, "claude_code:a1", "/work/api")
    _session(store, "codex:c1", "/work/api/src")
    _session(store, "copilot:p1", "/work/web")
    _spend(store, "claude_code:a1", "2026-09-01T10:00:00Z", 2.0)
    _spend(store, "codex:c1", "2026-09-01T11:00:00Z", 1.5)
    _spend(store, "copilot:p1", "2026-09-01T12:00:00Z", 4.0)

    usage = store.query_project_usage(days=30, now=NOW)
    projects = _by_label(usage)
    assert set(projects) == {"api", "web"}
    assert projects["api"]["cost_usd"] == pytest.approx(3.5)
    assert projects["web"]["cost_usd"] == pytest.approx(4.0)
    assert projects["api"]["sessions"] == 2
    assert (projects["api"]["source"], projects["api"]["confidence"]) == ("repository", "high")
    assert projects["api"]["project_id"] != projects["web"]["project_id"]
    assert usage["totals"]["cost_usd"] == pytest.approx(7.5)


def test_a_directory_with_no_known_repository_is_low_confidence(store):
    _session(store, "claude_code:d1", "/scratch/tryout")
    _spend(store, "claude_code:d1", "2026-09-01T10:00:00Z", 1.0)
    p = _by_label(store.query_project_usage(days=30, now=NOW))["tryout"]
    assert (p["source"], p["confidence"]) == ("directory", "low")


def test_same_directory_name_in_two_places_stays_two_projects(store):
    _session(store, "claude_code:x", "/clients/one/api")
    _session(store, "claude_code:y", "/clients/two/api")
    _spend(store, "claude_code:x", "2026-09-01T10:00:00Z", 1.0)
    _spend(store, "claude_code:y", "2026-09-01T10:30:00Z", 2.0)
    usage = store.query_project_usage(days=30, now=NOW)
    named = [p for p in usage["projects"] if p["label"].startswith("api")]
    assert len(named) == 2
    assert len({p["project_id"] for p in named}) == 2
    assert len({p["label"] for p in named}) == 2  # visibly apart, not two rows called "api"
    blob = json.dumps(usage)
    assert "/clients/one" not in blob and "/clients/two" not in blob


def test_home_directory_is_not_published_by_account_name(store, tmp_path):
    home = str(tmp_path / "home")
    _session(store, "claude_code:h", home)
    _spend(store, "claude_code:h", "2026-09-01T10:00:00Z", 1.0)
    labels = set(_by_label(store.query_project_usage(days=30, now=NOW)))
    assert labels == {"Home directory"}


def test_a_session_with_no_directory_is_unassigned_not_dropped(store):
    _repo(store, "/work/api")
    _session(store, "claude_code:a", "/work/api")
    _session(store, "codex:nowhere", "")
    _spend(store, "claude_code:a", "2026-09-01T10:00:00Z", 2.0)
    _spend(store, "codex:nowhere", "2026-09-01T10:05:00Z", 0.75)
    usage = store.query_project_usage(days=30, now=NOW)
    un = _by_label(usage)["Unassigned"]
    assert un["project_id"] == "unassigned"
    assert un["cost_usd"] == pytest.approx(0.75) and un["sessions"] == 1
    t = usage["totals"]
    assert t["unassigned_cost_usd"] == pytest.approx(0.75)
    assert t["derived_cost_usd"] + t["assigned_cost_usd"] + t["unassigned_cost_usd"] == pytest.approx(t["cost_usd"])
    # and the node total agrees with the existing per-day rollup
    agg = sum(r["cost_usd"] for r in store.query_aggregates(since="2026-08-03"))
    assert t["cost_usd"] == pytest.approx(agg)


def test_a_project_named_inside_the_activity_is_ignored(store):
    """A forged tenant/project claim in the agent's own output or session
    metadata must not move spend to another project."""
    _repo(store, "/work/api")
    _session(store, "claude_code:f", "/work/api",
             metadata={"project": "someone-elses-client", "tenant": "other-org"})
    _spend(store, "claude_code:f", "2026-09-01T10:00:00Z", 5.0,
           data={"type": "assistant", "project": "someone-elses-client",
                 "tenant": "other-org"})
    labels = set(_by_label(store.query_project_usage(days=30, now=NOW)))
    assert labels == {"api"}


def test_assignment_covers_history_and_respects_its_effective_period(store):
    """Membership change: the repository joins a client engagement on
    1 September. Earlier sessions stay where they were; later ones move, and
    history collected before the assignment existed is covered by it."""
    _repo(store, "/work/api")
    _session(store, "claude_code:before", "/work/api", started="2026-08-20T09:00:00Z")
    _session(store, "claude_code:after", "/work/api", started="2026-09-01T09:00:00Z")
    _spend(store, "claude_code:before", "2026-08-20T10:00:00Z", 1.0)
    _spend(store, "claude_code:after", "2026-09-01T10:00:00Z", 2.0)
    pid = _pid(store, "api")

    res = store.add_project_assignment(
        match_type="project", match_value=pid, project_name="Client Billing",
        reason="engagement kickoff", effective_from="2026-09-01T00:00:00Z", actor="lead")
    assert res["ok"], res
    usage = store.query_project_usage(days=30, now=NOW)
    projects = _by_label(usage)
    assert projects["api"]["cost_usd"] == pytest.approx(1.0)
    assert projects["Client Billing"]["cost_usd"] == pytest.approx(2.0)
    assert projects["Client Billing"]["source"] == "assigned"
    assert usage["totals"]["assigned_cost_usd"] == pytest.approx(2.0)


def test_a_named_project_cannot_be_the_target_of_an_assignment(store, client):
    """A named (prjn_) project is in the catalog, but sessions resolve through
    their derived project only: an assignment that targets it would be stored
    and move no spend, so it is refused in words."""
    from clawmetry import project_attribution as pa
    _repo(store, "/work/api")
    _session(store, "claude_code:a", "/work/api")
    _spend(store, "claude_code:a", "2026-09-01T10:00:00Z", 2.0)
    assert store.add_project_assignment(match_type="project", match_value=_pid(store, "api"),
                                        project_name="Client Billing", reason="r")["ok"]
    named = pa.assigned_project_id("Client Billing")
    assert named in store._project_catalog()
    before = len(store.query_project_assignments())
    bad = store.add_project_assignment(match_type="project", match_value=named,
                                       project_name="Client B", reason="rename")
    assert not bad["ok"] and "repository or directory" in bad["error"]
    r = client.post("/api/projects/assignments", json={
        "match_type": "project", "match_value": named,
        "project_name": "Client B", "reason": "rename"})
    assert r.status_code == 400 and "repository or directory" in r.get_json()["error"]
    assert len(store.query_project_assignments()) == before
    usage = _by_label(store.query_project_usage(days=30, now=NOW))
    assert usage["Client Billing"]["cost_usd"] == pytest.approx(2.0)


def test_assignment_needs_an_observed_target_and_a_reason(store):
    _session(store, "claude_code:a", "/work/api")
    bad = store.add_project_assignment(match_type="project", match_value="prj_0000000000000000",
                                       project_name="X", reason="r")
    assert not bad["ok"] and "unknown project" in bad["error"]
    missing = store.add_project_assignment(match_type="session", match_value="claude_code:a",
                                           project_name="X", reason="")
    assert not missing["ok"] and "reason" in missing["error"]
    ghost = store.add_project_assignment(match_type="session", match_value="nope",
                                         project_name="X", reason="r")
    assert not ghost["ok"] and ghost["error"] == "unknown session"


def test_a_correction_supersedes_without_erasing(store):
    _session(store, "claude_code:a", "/work/api")
    _spend(store, "claude_code:a", "2026-09-01T10:00:00Z", 1.0)
    pid = _pid(store, "api")
    first = store.add_project_assignment(match_type="project", match_value=pid,
                                         project_name="Billing", reason="initial", actor="a")
    second = store.add_project_assignment(match_type="project", match_value=pid,
                                          project_name="Payments", reason="renamed engagement",
                                          actor="b")
    assert first["ok"] and second["ok"]
    history = store.query_project_assignments()
    assert len(history) == 2
    by_id = {h["assignment_id"]: h for h in history}
    old = by_id[first["assignment"]["assignment_id"]]
    assert old["superseded_by"] == second["assignment"]["assignment_id"]
    assert (old["actor"], old["reason"]) == ("a", "initial")
    assert set(_by_label(store.query_project_usage(days=30, now=NOW))) == {"Payments"}


def test_a_session_assignment_beats_a_project_assignment(store):
    _session(store, "claude_code:a", "/work/api")
    _session(store, "claude_code:b", "/work/api")
    _spend(store, "claude_code:a", "2026-09-01T10:00:00Z", 1.0)
    _spend(store, "claude_code:b", "2026-09-01T10:10:00Z", 1.0)
    pid = _pid(store, "api")
    store.add_project_assignment(match_type="project", match_value=pid,
                                 project_name="Billing", reason="r")
    store.add_project_assignment(match_type="session", match_value="claude_code:b",
                                 project_name="Internal", reason="mis-filed run")
    projects = _by_label(store.query_project_usage(days=30, now=NOW))
    assert projects["Billing"]["cost_usd"] == pytest.approx(1.0)
    assert projects["Internal"]["cost_usd"] == pytest.approx(1.0)


# ── CLAWMETRY_PROJECT on the collector (#5941) ───────────────────────────

SINCE = "2026-09-01T08:00:00Z"


def test_env_project_tags_sessions_started_after_the_collector(store):
    _session(store, "claude_code:old", "/work/api", started="2026-08-30T09:00:00Z")
    _session(store, "claude_code:new", "/work/api", started="2026-09-01T09:00:00Z")
    _session(store, "codex:new", "", started="2026-09-01T09:30:00Z")
    store.ingest_sessions_batch([{"session_id": "codex:nostart", "node_id": "box1"}])
    for sid in ("claude_code:old", "claude_code:new", "codex:new"):
        _spend(store, sid, "2026-09-01T10:00:00Z", 1.0)

    res = store.record_env_project_assignments("Client A", since=SINCE)
    assert res["ok"] and res["assigned"] == 2
    # A second tick finds nothing left to do.
    assert store.record_env_project_assignments("Client A", since=SINCE)["assigned"] == 0

    rows = [a for a in store.query_project_assignments() if a["actor"] == "daemon:env"]
    assert sorted(a["match_value"] for a in rows) == ["claude_code:new", "codex:new"]
    assert all(a["match_type"] == "session" and a["project_name"] == "Client A"
               and "CLAWMETRY_PROJECT" in a["reason"] for a in rows)

    by = _by_label(store.query_project_usage(days=30, now=NOW))
    assert by["Client A"]["cost_usd"] == pytest.approx(2.0)
    assert by["Client A"]["source"] == "assigned"
    # History collected before the collector started keeps its derived project.
    assert by["api"]["cost_usd"] == pytest.approx(1.0)


def test_env_project_never_overrides_an_operator_assignment(store):
    _session(store, "claude_code:a", "/work/api")
    _session(store, "claude_code:b", "/work/api")
    assert store.add_project_assignment(
        "session", "claude_code:a", "Billing", reason="set by hand", actor="ana")["ok"]
    assert store.record_env_project_assignments("Client A", since=SINCE)["assigned"] == 1
    resolved = store._resolve_projects(["claude_code:a", "claude_code:b"])
    assert resolved["claude_code:a"]["label"] == "Billing"
    assert resolved["claude_code:b"]["label"] == "Client A"
    # A later correction supersedes the collector's row without erasing it.
    assert store.add_project_assignment(
        "session", "claude_code:b", "Billing", reason="wrong client", actor="ana")["ok"]
    assert store._resolve_projects(["claude_code:b"])["claude_code:b"]["label"] == "Billing"
    env = [a for a in store.query_project_assignments() if a["actor"] == "daemon:env"]
    assert len(env) == 1 and env[0]["superseded_by"]


def test_a_changed_env_project_applies_to_later_sessions_only(store):
    _session(store, "claude_code:a", "/work/api")
    assert store.record_env_project_assignments("Client A", since=SINCE)["assigned"] == 1
    _session(store, "claude_code:b", "/work/api", started="2026-09-01T11:00:00Z")
    assert store.record_env_project_assignments("Client B", since=SINCE)["assigned"] == 1
    resolved = store._resolve_projects(["claude_code:a", "claude_code:b"])
    assert resolved["claude_code:a"]["label"] == "Client A"
    assert resolved["claude_code:b"]["label"] == "Client B"


def test_env_project_refuses_a_name_it_cannot_store(store):
    _session(store, "claude_code:a", "/work/api")
    assert not store.record_env_project_assignments("   ", since=SINCE)["ok"]
    assert not store.record_env_project_assignments("x" * 121, since=SINCE)["ok"]
    assert not store.record_env_project_assignments("Client A")["ok"]
    assert store.query_project_assignments() == []


def test_daemon_tick_tags_sessions_from_the_environment(store, monkeypatch):
    from clawmetry import sync
    import clawmetry.local_store as ls
    monkeypatch.setattr(ls, "get_store", lambda *a, **k: store)
    since = datetime(2026, 9, 1, 8, 0, tzinfo=timezone.utc).timestamp()
    _session(store, "claude_code:a", "/work/api")

    monkeypatch.delenv("CLAWMETRY_PROJECT", raising=False)
    assert sync.tag_env_project_sessions(since=since) == 0
    assert store.query_project_assignments() == []

    monkeypatch.setenv("CLAWMETRY_PROJECT", "  Client A ")
    assert sync.tag_env_project_sessions(since=since) == 1
    assert sync.tag_env_project_sessions(since=since) == 0
    assert store._resolve_projects(["claude_code:a"])["claude_code:a"]["label"] == "Client A"

    # The default cut-off is this process's start, so a session from 2026-09-01
    # is history and stays untouched.
    _session(store, "claude_code:b", "/work/api")
    assert sync.tag_env_project_sessions() == 0

    # An unusable name is ignored, never raised into the loop.
    monkeypatch.setenv("CLAWMETRY_PROJECT", "x" * 121)
    assert sync.tag_env_project_sessions(since=since) == 0


def test_project_is_not_stored_on_session_rows(store):
    cols = {r[1] for r in store._conn.execute("PRAGMA table_info('sessions')").fetchall()}
    assert not ({"project", "project_id", "project_name"} & cols)


# ── budgets ──────────────────────────────────────────────────────────────


def _budget(store, pid, amount=10.0, period="month", tz="UTC", **kw):
    res = store.upsert_project_budget(project_id=pid, amount=amount, currency="USD",
                                      period=period, timezone_name=tz, **kw)
    assert res["ok"], res
    return res["budget"]


def test_budget_refuses_terms_it_cannot_honour(store):
    _session(store, "claude_code:a", "/work/api")
    _spend(store, "claude_code:a", "2026-09-01T10:00:00Z", 1.0)
    pid = _pid(store, "api")
    eur = store.upsert_project_budget(project_id=pid, amount=10, currency="EUR",
                                      period="month", timezone_name="UTC")
    assert not eur["ok"] and "USD only" in eur["error"]
    no_ccy = store.upsert_project_budget(project_id=pid, amount=10, currency="",
                                         period="month", timezone_name="UTC")
    assert not no_ccy["ok"] and "currency is required" in no_ccy["error"]
    tz = store.upsert_project_budget(project_id=pid, amount=10, currency="USD",
                                     period="month", timezone_name="Mars/Olympus_Mons")
    assert not tz["ok"] and "cannot be resolved" in tz["error"]
    basis = store.upsert_project_budget(project_id=pid, amount=10, currency="USD",
                                        period="month", timezone_name="UTC", basis="invoice")
    assert not basis["ok"] and "not available" in basis["error"]
    zero = store.upsert_project_budget(project_id=pid, amount=0, currency="USD",
                                       period="month", timezone_name="UTC")
    assert not zero["ok"]
    b = _budget(store, pid)
    assert (b["currency"], b["period"], b["timezone"], b["basis"]) == (
        "USD", "month", "UTC", "estimated_spend")


def test_a_period_boundary_splits_a_session(store):
    _session(store, "claude_code:long", "/work/api", started="2026-08-31T23:00:00Z")
    _spend(store, "claude_code:long", "2026-08-31T23:50:00Z", 5.0)
    _spend(store, "claude_code:long", "2026-09-01T00:10:00Z", 3.0)
    pid = _pid(store, "api")
    _budget(store, pid, amount=100.0, period="month", tz="UTC")
    b = store.project_budget_status(now=NOW)["budgets"][0]
    assert b["spent_usd"] == pytest.approx(3.0)
    assert b["previous_period"]["spent_usd"] == pytest.approx(5.0)
    assert b["period_start"].startswith("2026-09-01T00:00:00")


def test_the_budget_timezone_decides_the_period(store):
    """00:10 UTC on 1 September is still 31 August in Los Angeles."""
    from clawmetry import project_attribution as pa
    _session(store, "claude_code:la", "/work/api", started="2026-09-01T00:00:00Z")
    _spend(store, "claude_code:la", "2026-09-01T00:10:00Z", 3.0)
    pid = _pid(store, "api")
    try:
        pa.resolve_timezone("America/Los_Angeles")
    except ValueError:
        # No tz database on this interpreter: the budget must be refused,
        # never silently evaluated in UTC.
        res = store.upsert_project_budget(project_id=pid, amount=10, currency="USD",
                                          period="month", timezone_name="America/Los_Angeles")
        assert not res["ok"] and "cannot be resolved" in res["error"]
        return
    _budget(store, pid, amount=10.0, period="month", tz="America/Los_Angeles")
    b = store.project_budget_status(now=NOW)["budgets"][0]
    assert b["spent_usd"] == pytest.approx(0.0)
    assert b["previous_period"]["spent_usd"] == pytest.approx(3.0)


def test_budget_alert_fires_once_at_80_percent(store):
    _session(store, "claude_code:a", "/work/api")
    _spend(store, "claude_code:a", "2026-09-01T10:00:00Z", 4.0)
    _spend(store, "claude_code:a", "2026-09-02T09:00:00Z", 4.5)
    pid = _pid(store, "api")
    _budget(store, pid, amount=10.0)

    fired = store.evaluate_project_budgets(now=NOW)
    assert sorted(a["threshold_pct"] for a in fired) == [50, 80]
    eighty = next(a for a in fired if a["threshold_pct"] == 80)
    assert eighty["late"] is False
    assert "80%" in eighty["message"] and "do not pause, stop or reverse" in eighty["message"]
    assert store.evaluate_project_budgets(now=NOW) == []  # latched

    status = store.project_budget_status(now=NOW)["budgets"][0]
    assert status["pct_used"] == pytest.approx(85.0)
    assert status["thresholds_crossed"] == [50, 80]
    assert status["enforcement"] == "none"
    assert sorted(a["threshold_pct"] for a in status["alerts"]) == [50, 80]

    _spend(store, "claude_code:a", "2026-09-02T10:00:00Z", 2.0)
    assert [a["threshold_pct"] for a in store.evaluate_project_budgets(now=NOW)] == [100]


def test_a_late_record_alerts_for_the_period_it_belongs_to(store):
    _session(store, "claude_code:a", "/work/api", started="2026-08-10T09:00:00Z")
    _spend(store, "claude_code:a", "2026-08-10T10:00:00Z", 1.0)
    pid = _pid(store, "api")
    b = _budget(store, pid, amount=10.0)
    aug1 = int(datetime(2026, 8, 1, tzinfo=timezone.utc).timestamp() * 1000)
    store._conn.execute("UPDATE project_budgets SET created_at = ? WHERE budget_id = ?",
                        [aug1, b["budget_id"]])
    assert store.evaluate_project_budgets(now=NOW) == []
    # August usage recorded only now, after the month closed
    _spend(store, "claude_code:a", "2026-08-30T22:00:00Z", 8.0)
    fired = store.evaluate_project_budgets(now=NOW)
    assert sorted(a["threshold_pct"] for a in fired) == [50, 80]
    assert all(a["late"] and a["period_start"].startswith("2026-08-01") for a in fired)
    assert "last month" in fired[0]["message"]


def test_a_new_budget_does_not_alert_on_a_period_before_it_existed(store):
    _session(store, "claude_code:a", "/work/api", started="2026-08-10T09:00:00Z")
    _spend(store, "claude_code:a", "2026-08-10T10:00:00Z", 50.0)
    _budget(store, _pid(store, "api"), amount=10.0)
    assert store.evaluate_project_budgets(now=NOW) == []


def test_status_reports_daily_burn(store):
    _session(store, "claude_code:a", "/work/api")
    _spend(store, "claude_code:a", "2026-09-02T08:00:00Z", 1.25)
    _budget(store, _pid(store, "api"), amount=10.0)
    burn = store.project_budget_status(now=NOW)["budgets"][0]["burn"]
    assert burn == [{"day": "2026-09-01", "spent_usd": 0.0},
                    {"day": "2026-09-02", "spent_usd": 1.25}]


def test_daemon_tick_delivers_each_crossing_exactly_once(store, monkeypatch):
    from clawmetry import sync
    import clawmetry.local_store as ls
    _session(store, "claude_code:a", "/work/api")
    _spend(store, "claude_code:a", "2026-09-01T10:00:00Z", 9.0)
    _budget(store, _pid(store, "api"), amount=10.0)
    real = store.evaluate_project_budgets
    monkeypatch.setattr(store, "evaluate_project_budgets", lambda: real(now=NOW))
    monkeypatch.setattr(ls, "get_store", lambda *a, **k: store)
    delivered = []
    monkeypatch.setattr(sync, "_persist_local_alert_banner",
                        lambda m: delivered.append(m) or True)
    assert sync.evaluate_project_budget_alerts({}) == 2
    assert sync.evaluate_project_budget_alerts({}) == 0
    assert len(delivered) == 2
    assert all("do not pause, stop or reverse" in m["summary"] for m in delivered)
    assert len({m["rule"]["id"] for m in delivered}) == 2


def test_a_repository_budget_keeps_counting_after_the_repository_is_assigned(store):
    """Budget the repository, then file it under a named engagement. The
    repository still spent the money: its budget must not fall to $0 and go
    silent. It says which named project its spend is now reported under."""
    _repo(store, "/work/api")
    _session(store, "claude_code:a", "/work/api")
    _spend(store, "claude_code:a", "2026-09-01T10:00:00Z", 9.0)
    pid = _pid(store, "api")
    _budget(store, pid, amount=10.0)
    assert store.project_budget_status(now=NOW)["budgets"][0]["spent_usd"] == pytest.approx(9.0)

    res = store.add_project_assignment(match_type="project", match_value=pid,
                                       project_name="Billing", reason="engagement")
    assert res["ok"], res
    assert set(_by_label(store.query_project_usage(days=30, now=NOW))) == {"Billing"}

    b = store.project_budget_status(now=NOW)["budgets"][0]
    assert b["available"] is True
    assert b["label"] == "api"
    assert b["spent_usd"] == pytest.approx(9.0)
    assert b["pct_used"] == pytest.approx(90.0)
    assert b["reported_under"] == ["Billing"]
    assert sorted(a["threshold_pct"] for a in store.evaluate_project_budgets(now=NOW)) == [50, 80]

    # A budget on the named project counts the same sessions once, not twice.
    named = _budget(store, _pid(store, "Billing"), amount=100.0)
    by_id = {x["budget_id"]: x for x in store.project_budget_status(now=NOW)["budgets"]}
    assert by_id[named["budget_id"]]["spent_usd"] == pytest.approx(9.0)
    assert by_id[named["budget_id"]]["reported_under"] == []


def test_usage_buckets_are_reused_between_ticks(store, monkeypatch):
    """The daemon asks every 60s with a new ``now``; the cache key must not
    change every second, or each tick rescans the whole period."""
    import clawmetry.local_store_projects as lsp
    monkeypatch.setenv("CLAWMETRY_AGG_CACHE_TTL", "20")
    monkeypatch.setattr(lsp, "_BUCKET_CACHE", {})
    _session(store, "claude_code:a", "/work/api")
    _spend(store, "claude_code:a", "2026-09-01T10:00:00Z", 1.0)
    first = store._project_usage_buckets(NOW - 86400 * 30, NOW + 1)
    second = store._project_usage_buckets(NOW - 86400 * 30 + 1, NOW + 2)
    assert len(lsp._BUCKET_CACHE) == 1
    assert first == second


# ── HTTP ─────────────────────────────────────────────────────────────────


@pytest.fixture
def client(store, monkeypatch):
    from flask import Flask
    import routes.projects as rp
    import routes.usage as ru
    monkeypatch.setattr(rp, "is_local_store_read_enabled", lambda: True)
    monkeypatch.setattr(ru, "is_local_store_read_enabled", lambda: True)

    def call(method, **kw):
        if method == "query_project_usage":
            kw.setdefault("now", NOW)
        if method == "project_budget_status":
            kw.setdefault("now", NOW)
        return getattr(store, method)(**kw)
    monkeypatch.setattr(rp, "_store_call", call)
    app = Flask(__name__)
    app.register_blueprint(rp.bp_projects)
    app.register_blueprint(ru.bp_usage)
    return app.test_client()


def test_csv_export_by_project_reports_completeness(store, client):
    _session(store, "claude_code:a", "/work/=cmd")
    _session(store, "codex:none", "")
    _spend(store, "claude_code:a", "2026-09-01T10:00:00Z", 2.0, tokens=1000)
    _spend(store, "claude_code:a", "2026-09-01T10:01:00Z", None, tokens=500)  # unpriced
    _spend(store, "codex:none", "2026-09-01T10:02:00Z", 1.0, tokens=100)

    r = client.get("/api/usage/export?by=project&days=30")
    assert r.status_code == 200 and r.headers["Content-Type"].startswith("text/csv")
    rows = list(csv.DictReader(io.StringIO(r.get_data(as_text=True))))
    projects = [x for x in rows if x["row_type"] == "project"]
    total = next(x for x in rows if x["row_type"] == "total")
    cmd = next(x for x in projects if x["project"].endswith("=cmd"))
    assert cmd["project"] == "'=cmd"  # a formula-shaped label cannot execute
    assert int(cmd["unpriced_tokens"]) == 500 and float(cmd["cost_usd"]) == pytest.approx(2.0)
    assert float(total["unassigned_cost_usd"]) == pytest.approx(1.0)
    assert float(total["derived_cost_usd"]) == pytest.approx(2.0)
    assert float(total["assigned_cost_usd"]) == pytest.approx(0.0)
    assert float(total["priced_token_share"]) == pytest.approx(1100 / 1600, abs=1e-4)
    assert float(total["attributed_cost_share"]) == pytest.approx(2 / 3, abs=1e-4)
    assert "/work/" not in r.get_data(as_text=True)

    assert client.get("/api/usage/export?by=user").status_code == 400
    assert client.get("/api/usage/export?by=nonsense").status_code == 400


def test_budget_routes_validate_and_report(store, client):
    _session(store, "claude_code:a", "/work/api")
    _spend(store, "claude_code:a", "2026-09-01T10:00:00Z", 9.0)
    pid = client.get("/api/projects").get_json()["projects"][0]["project_id"]
    bad = client.post("/api/projects/budgets", json={"project_id": pid, "amount": 10,
                                                     "currency": "EUR", "period": "month",
                                                     "timezone": "UTC"})
    assert bad.status_code == 400 and "USD only" in bad.get_json()["error"]
    ok = client.post("/api/projects/budgets", json={"project_id": pid, "amount": 10,
                                                    "currency": "USD", "period": "month",
                                                    "timezone": "UTC"})
    assert ok.status_code == 200 and ok.get_json()["ok"]
    status = client.get("/api/projects/budgets").get_json()
    assert status["budgets"][0]["pct_used"] == pytest.approx(90.0)
    assert status["notice"].startswith("Budget alerts are notifications")
    assign = client.post("/api/projects/assignments", json={
        "match_type": "project", "match_value": pid, "project_name": "Billing",
        "reason": "kickoff"})
    assert assign.status_code == 200 and assign.get_json()["ok"]
    assert client.get("/api/projects/assignments").get_json()["assignments"][0]["project_name"] == "Billing"
    bid = ok.get_json()["budget"]["budget_id"]
    assert client.delete(f"/api/projects/budgets/{bid}").get_json()["deleted"] == 1


def test_project_and_budget_figures_name_their_financial_basis(store, client):
    """Every dollar figure on these routes is usage value at published rates
    (REQ-OBS-CEA-025), labelled through the shared cost_basis vocabulary, and
    none claims to be a contract rate or an invoice."""
    from clawmetry import cost_basis, provenance
    _session(store, "claude_code:a", "/work/api")
    _session(store, "codex:none", "")
    _spend(store, "claude_code:a", "2026-09-01T10:00:00Z", 9.0)
    _spend(store, "codex:none", "2026-09-01T10:02:00Z", 1.0)
    projects = client.get("/api/projects").get_json()
    pid = next(p["project_id"] for p in projects["projects"] if p["label"] == "api")
    assert client.post("/api/projects/budgets", json={
        "project_id": pid, "amount": 10, "currency": "USD", "period": "month",
        "timezone": "UTC"}).get_json()["ok"]
    fired = store.evaluate_project_budgets(now=NOW)
    assert fired and all("published rates" in a["message"]
                         and "estimated spend" not in a["message"] for a in fired), fired
    budgets = client.get("/api/projects/budgets").get_json()
    alerts = client.get("/api/projects/budgets/alerts").get_json()
    assert alerts["alerts"], alerts
    for where, payload in (("/api/projects", projects), ("/api/projects/budgets", budgets),
                           ("/api/projects/budgets/alerts", alerts)):
        provenance.assert_labelled(payload, where)
        assert payload["cost_basis"] == cost_basis.PUBLISHED_RATE, where
        for key, entry in payload["provenance"].items():
            assert entry["cost_basis"] == cost_basis.PUBLISHED_RATE, (where, key)
            assert entry["cost_basis_label"] == cost_basis.COST_BASIS_LABEL[cost_basis.PUBLISHED_RATE]
    assert "published rates" in budgets["notice"]
    rows = list(csv.DictReader(io.StringIO(
        client.get("/api/usage/export?by=project&days=30").get_data(as_text=True))))
    assert {r["cost_basis"] for r in rows} == {cost_basis.PUBLISHED_RATE}


def test_without_a_local_store_routes_answer_an_honest_empty_state(monkeypatch):
    from flask import Flask
    import routes.projects as rp
    monkeypatch.setattr(rp, "is_local_store_read_enabled", lambda: False)
    app = Flask(__name__)
    app.register_blueprint(rp.bp_projects)
    c = app.test_client()
    for path in ("/api/projects", "/api/projects/assignments", "/api/projects/budgets",
                 "/api/projects/budgets/alerts"):
        r = c.get(path)
        assert r.status_code == 200, path
        assert r.get_json()["available"] is False, path


# ── The Usage tab panel (the shipped renderers, run in node) ────────────────

_PANEL_FNS = ("costCardText", "projectSourceText", "renderProjectUsage",
              "projectBudgetPeriodText", "renderProjectBudgets", "projectBudgetTimezone",
              "renderProjectBudgetForm", "projectAssignTargets", "renderProjectAssignments",
              "loadUsageByProject")
_REPO_ID = "prj_" + "a" * 16
_NAMED_ID = "prjn_" + "b" * 16


def _panel_usage():
    import routes.projects as rp
    return rp._stamp_project_usage({
        "available": True, "basis": "estimated_spend", "currency": "USD",
        "window": {"days": 30, "since": "2026-09-04T00:00:00Z", "until": "2026-10-04T00:00:00Z"},
        "projects": [
            {"project_id": _REPO_ID, "label": "<img src=x onerror=alert(1)>",
             "source": "repository", "confidence": "high", "cost_usd": 6.0,
             "sessions": 3, "runtimes": ["claude_code", "codex"]},
            {"project_id": _NAMED_ID, "label": "Billing", "source": "assigned",
             "confidence": "high", "cost_usd": 3.0, "sessions": 1, "runtimes": ["codex"]},
            {"project_id": "unassigned", "label": "Unassigned", "source": "none",
             "confidence": "none", "cost_usd": 1.0, "sessions": 2, "runtimes": []}],
        "totals": {"cost_usd": 10.0, "unassigned_cost_usd": 1.0, "unpriced_tokens": 1234,
                   "completeness": {"attributed_cost_share": 0.9}}})


def _panel_budgets():
    import routes.projects as rp
    base = {"currency": "USD", "period": "month", "timezone": "Europe/Berlin",
            "available": True, "reported_under": []}
    return rp._stamp_budget_payload({"available": True, "notice": "Alerts do not stop a charge.", "budgets": [
        dict(base, budget_id="pb_" + "a" * 16, project_id=_REPO_ID, label="api <b>",
             amount=10.0, spent_usd=12.5, pct_used=125.0, reported_under=["Billing"]),
        dict(base, budget_id='pb_"x', project_id=_NAMED_ID, label="Billing",
             amount=20.0, spent_usd=17.0, pct_used=85.0, period="week"),
        dict(base, budget_id="pb_low", project_id=_NAMED_ID, label="Docs",
             amount=20.0, spent_usd=2.0, pct_used=10.0, period="day"),
        dict(base, budget_id="pb_tz", project_id=_NAMED_ID, label="Lost zone",
             amount=5.0, available=False, reason="timezone_unresolvable")]}, "budgets")


def _panel(body, **kw):
    from tests.test_cost_basis_remaining_surfaces import _run
    return _run(body, fns=_PANEL_FNS, **kw)


def test_the_usage_tab_lists_spend_per_project_with_its_basis():
    from tests.test_cost_basis_remaining_surfaces import _badges
    html = _panel("console.log(JSON.stringify({html: renderProjectUsage(%s)}));"
                  % json.dumps(_panel_usage()))["html"]
    assert "<img" not in html and "&lt;img src=x onerror=alert(1)&gt;" in html
    assert _badges(html.split("</thead>")[0]) == ["published rates"]
    body = html.split("<tbody>")[1].split("</tbody>")[0]
    rows = body.split("</tr>")[:-1]
    assert len(rows) == 3
    assert "$6.00" in rows[0] and ">60%<" in rows[0] and ">repository<" in rows[0]
    assert "claude_code, codex" in rows[0]
    assert "$3.00" in rows[1] and ">30%<" in rows[1] and ">assigned<" in rows[1]
    assert "Unassigned" in rows[2] and ">10%<" in rows[2] and ">no project<" in rows[2]
    assert "90% of this spend belongs to a project" in html
    assert "1,234 tokens have no price" in html


def test_the_project_table_says_nothing_extra_when_all_spend_is_attributed_and_priced():
    data = _panel_usage()
    data["totals"].update(unpriced_tokens=0, completeness={"attributed_cost_share": 1.0})
    html = _panel("console.log(JSON.stringify({html: renderProjectUsage(%s)}));"
                  % json.dumps(data))["html"]
    assert "belongs to a project" not in html and "no price" not in html
    assert html.rstrip().endswith("</table>")


def test_a_budget_row_shows_spend_against_the_amount_and_never_overflows():
    html = _panel("console.log(JSON.stringify({html: renderProjectBudgets(%s)}));"
                  % json.dumps(_panel_budgets()))["html"]
    from tests.test_cost_basis_remaining_surfaces import _badges
    rows = html.split('<div style="margin-top:8px;font-size:12px;">')[1:]
    assert len(rows) == 4
    assert _badges(html) == ["published rates"], "one basis badge, on the heading"
    over, near, low, lost = rows
    assert "api &lt;b&gt;" in over and "<b>" not in over
    assert "width:100%;background:#ef4444" in over, "125% must fill the bar, not overflow it"
    assert "$12.50" in over and "of $10.00" in over and "125% used" in over
    assert "per month" in over and "Europe/Berlin" in over
    assert "This spend is listed above under: Billing" in over
    assert "width:85%;background:#f59e0b" in near and "per week" in near
    assert "width:10%;background:var(--accent" in low and "per day" in low
    assert "listed above under" not in low
    # A budget id is data: it sits in an attribute, escaped, never in the handler.
    assert 'data-budget-id="pb_&quot;x"' in near
    assert html.count("removeProjectBudget(this.getAttribute('data-budget-id'))") == 4
    assert "timezone of this budget is not known" in lost and "width:" not in lost
    assert "Alerts do not stop a charge." in html


def test_no_budget_yet_is_said_in_words_and_the_form_offers_real_projects_only():
    got = _panel("console.log(JSON.stringify({"
                 " none: renderProjectBudgets({available: true, budgets: [], notice: 'N.'}),"
                 " form: renderProjectBudgetForm(%s.projects),"
                 " empty: renderProjectBudgetForm([{project_id: 'unassigned', label: 'Unassigned'}])}));"
                 % json.dumps(_panel_usage()))
    assert "No project has a budget yet." in got["none"] and "N." in got["none"]
    options = got["form"].split('id="project-budget-project"')[1].split("</select>")[0]
    assert options.count("<option") == 2
    assert 'value="%s"' % _REPO_ID in options and 'value="%s"' % _NAMED_ID in options
    assert "unassigned" not in options and "<img" not in options
    assert 'id="project-budget-amount"' in got["form"] and "saveProjectBudget()" in got["form"]
    assert got["empty"] == ""


def _panel_assignments():
    base = {"effective_from": None, "effective_to": None, "created_at": 1}
    return {"available": True, "assignments": [
        dict(base, assignment_id="pa_new", match_type="project", match_value=_REPO_ID,
             match_label="api <b>", project_name="Client <A>", reason="contract 12",
             actor="127.0.0.1", superseded_by=None),
        dict(base, assignment_id="pa_old", match_type="project", match_value=_REPO_ID,
             match_label="api <b>", project_name="Old name", reason="first try",
             actor="127.0.0.1", superseded_by="pa_new"),
        dict(base, assignment_id="pa_s1", match_type="session", match_value="s1",
             match_label=None, project_name="Client <A>", reason="env",
             actor="daemon:env", superseded_by=None)]}


def test_the_assignment_list_shows_current_assignments_and_offers_derived_projects_only():
    other = "prj_" + "c" * 16
    projects = _panel_usage()["projects"] + [
        {"project_id": other, "label": "web", "source": "directory"}]
    got = _panel("console.log(JSON.stringify({"
                 " html: renderProjectAssignments(%s, %s),"
                 " none: renderProjectAssignments({available: true, assignments: []}, %s),"
                 " bare: renderProjectAssignments({available: true, assignments: []},"
                 "   [{project_id: 'unassigned'}, {project_id: %s}])}));"
                 % (json.dumps(_panel_assignments()), json.dumps(projects),
                    json.dumps(projects), json.dumps(_NAMED_ID)))
    html = got["html"]
    assert "api &lt;b&gt;" in html and "Client &lt;A&gt;" in html and "<b>" not in html
    assert "contract 12" in html and "127.0.0.1" in html
    assert "Old name" not in html and "first try" not in html, "a superseded row is history"
    assert "Sessions assigned to a project on their own: 1" in html
    options = html.split('id="project-assign-target"')[1].split("</select>")[0]
    # The assigned repository stays a target, so its assignment can be corrected.
    assert options.count("<option") == 2
    assert 'value="%s"' % _REPO_ID in options and 'value="%s"' % other in options
    assert _NAMED_ID not in options and "unassigned" not in options
    assert 'id="project-assign-name"' in html and 'id="project-assign-reason"' in html
    assert "saveProjectAssignment()" in html
    assert "No repository or directory is assigned" in got["none"]
    assert 'id="project-assign-target"' in got["none"]
    # Nothing to assign: only the unassigned row and a named project.
    assert "project-assign-target" not in got["bare"]


def test_saving_an_assignment_needs_a_name_and_a_reason_and_posts_the_derived_project():
    from tests.test_cost_basis_remaining_surfaces import _run
    fns = ("projectAssignStatus", "saveProjectAssignment")
    prog = ("var calls = []; var _f = fetch;"
            " fetch = function (u, o) { calls.push({url: u, opts: o || null}); return _f(u, o); };"
            " function loadUsageByProject() { calls.push({url: 'reload'}); }"
            " saveProjectAssignment().then(function () { console.log(JSON.stringify("
            "{calls: calls, status: els['project-assign-status'].textContent || ''})); });")

    def run(name, reason, answer):
        els = {"project-assign-target": {"value": _REPO_ID},
               "project-assign-name": {"value": name},
               "project-assign-reason": {"value": reason},
               "project-assign-status": {}}
        return _run(prog, fns=fns, els=els, fetch_json=answer)

    got = run("  ", "why", {"ok": True})
    assert got["calls"] == [] and got["status"] == "Enter a project name."
    got = run("Client A", " ", {"ok": True})
    assert got["calls"] == [] and "Enter a reason" in got["status"]
    got = run(" Client A ", " contract 12 ", {"ok": True})
    assert [c["url"] for c in got["calls"]] == ["/api/projects/assignments", "reload"]
    assert got["calls"][0]["opts"]["method"] == "POST"
    assert json.loads(got["calls"][0]["opts"]["body"]) == {
        "match_type": "project", "match_value": _REPO_ID,
        "project_name": "Client A", "reason": "contract 12"}
    got = run("Client A", "why", {"ok": False, "error": "unknown project"})
    assert [c["url"] for c in got["calls"]] == ["/api/projects/assignments"]
    assert got["status"] == "unknown project"


def test_an_assignment_row_names_the_repository_it_targets(store, client):
    _session(store, "claude_code:a", "/work/api")
    _spend(store, "claude_code:a", "2026-09-01T10:00:00Z", 2.0, tokens=1000)
    pid = next(p["project_id"] for p in client.get("/api/projects?days=366").get_json()["projects"]
               if p["source"] != "none")
    label = store._project_catalog()[pid]["label"]
    r = client.post("/api/projects/assignments", json={
        "match_type": "project", "match_value": pid, "project_name": "Client A",
        "reason": "contract 12"})
    assert r.status_code == 200 and r.get_json()["ok"] is True
    rows = client.get("/api/projects/assignments").get_json()["assignments"]
    assert rows[0]["match_label"] == label and rows[0]["project_name"] == "Client A"
    names = {p["label"]: p["source"] for p in client.get("/api/projects").get_json()["projects"]}
    assert names.get("Client A") == "assigned" and label not in names


def test_the_project_card_stays_hidden_until_a_session_has_a_project():
    from tests.test_cost_basis_remaining_surfaces import _run_async
    els = {"usage-by-project-title": {}, "usage-by-project-card": {},
           "usage-by-project-content": {"innerHTML": ""}}
    only_unassigned = _panel_usage()
    only_unassigned["projects"] = only_unassigned["projects"][2:]
    got = _run_async("loadUsageByProject()", _PANEL_FNS, els, only_unassigned)
    assert got["usage-by-project-content"] == ""
    got = _run_async("loadUsageByProject()", _PANEL_FNS, els,
                     {"available": False, "reason": "local_store_disabled", "projects": []})
    assert got["usage-by-project-content"] == ""
    # The harness answers every request with the same body, so the budget
    # request sees a payload with no budgets: the table, then the empty state.
    html = _run_async("loadUsageByProject()", _PANEL_FNS, els,
                      _panel_usage())["usage-by-project-content"]
    assert "Billing" in html and "No project has a budget yet." in html
    assert 'id="project-budget-project"' in html


def test_the_project_panel_is_wired_into_the_usage_tab_and_the_english_catalog():
    import re
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    app = open(os.path.join(root, "clawmetry", "static", "js", "app.js"), encoding="utf-8").read()
    page = open(os.path.join(root, "clawmetry", "templates", "tabs", "usage.html"),
                encoding="utf-8").read()
    catalog = json.load(open(os.path.join(root, "clawmetry", "static", "locales", "en.json"),
                             encoding="utf-8"))
    for el in ("usage-by-project-title", "usage-by-project-card", "usage-by-project-content"):
        assert 'id="%s"' % el in page, el
    assert re.search(r"loadUsageByTeam\(\);\s*(//[^\n]*\n\s*)?loadUsageByProject\(\);", app)
    used = set(re.findall(r"usage\.project_[a-z_]+", app + page))
    assert len(used) > 20
    assert not sorted(k for k in used if k not in catalog)
