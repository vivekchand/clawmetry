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
