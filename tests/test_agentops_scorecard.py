"""AgentOps scorecard gaps (clawmetry.com/blog/agentops-metrics-scorecard).

The scorecard graded ClawMetry against IBM's AgentOps checklist: 3 metrics
alerted, 7 were only shown, 5 were missing. This file guards what closed the
gap:

* latency SLOs (p95 session duration, p95 tool latency) and rates
  (escalation, guardrail violation, handoff failure, review accuracy,
  ground-truth accuracy, first-pass) as alert rule types;
* each quality rule reading the window IT asked for (it used to read the
  widest window any rule asked for);
* the figures themselves, computed on a real DuckDB store;
* the ground-truth endpoint, SLA breach firing, percentage review sampling,
  and the prompt fingerprint as a cohort key.

The class guards at the bottom auto-discover every AgentOps rule type from
``alert_evaluator.AGENTOPS_RULES``, so a type added there without an
evaluator mapping, a route, a UI button or a computed figure fails here.
"""

from __future__ import annotations

import importlib
import json
import os
import re
import sys
import time
from datetime import datetime, timedelta, timezone

import pytest
from flask import Flask

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

from clawmetry import alert_evaluator as ae  # noqa: E402


def _rule(rid, **cond):
    return {"id": rid, "name": f"rule {rid}", "enabled": True,
            "condition_json": cond}


def _iso(ts):
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


# ── Evaluator ──────────────────────────────────────────────────────────────


def test_latency_p95_fires_in_minutes_above_threshold():
    q = {"session_duration_p95_sec": 552.0, "timed_sessions": 3}
    hit = ae.evaluate([_rule("r", alert_type="latency_p95_above", threshold_value=5)],
                      [], {}, quality=q)
    assert len(hit) == 1
    md = hit[0]["metadata"]
    assert md["value"] == pytest.approx(9.2) and md["unit"] == "min"
    assert "p95 session duration" in hit[0]["summary"]
    assert ae.evaluate([_rule("r", alert_type="latency_p95_above", threshold_value=10)],
                       [], {}, quality=q) == []


def test_min_sample_floor_keeps_a_thin_window_quiet():
    q = {"session_duration_p95_sec": 9999.0, "timed_sessions": 2}
    assert ae.evaluate([_rule("r", alert_type="latency_p95_above", threshold_value=1)],
                       [], {}, quality=q) == []
    # An explicit floor lowers it.
    assert len(ae.evaluate([_rule("r", alert_type="latency_p95_above",
                                  threshold_value=1, min_sessions=2)],
                           [], {}, quality=q)) == 1


def test_unmeasured_figure_never_fires():
    for t in ae.AGENTOPS_RULES:
        spec = ae.AGENTOPS_RULES[t]
        q = {spec["value"]: None, spec["sample"]: 1000}
        assert ae.evaluate([_rule("r", alert_type=t, threshold_value=1)], [], {},
                           quality=q) == [], t


def test_tool_latency_can_watch_one_tool():
    q = {"tool_latency_p95_ms": 1000.0, "timed_tool_calls": 500,
         "tool_latency_by_tool": [
             {"name": "Bash", "p95_ms": 40000.0, "timed_calls": 30},
             {"name": "Read", "p95_ms": 500.0, "timed_calls": 30}]}
    node = _rule("r", alert_type="tool_latency_p95_above", threshold_value=10)
    assert ae.evaluate([node], [], {}, quality=q) == []
    bash = _rule("r", alert_type="tool_latency_p95_above", threshold_value=10,
                 tool_name="Bash")
    hit = ae.evaluate([bash], [], {}, quality=q)
    assert hit and hit[0]["metadata"]["tool_name"] == "Bash"
    assert "for Bash" in hit[0]["summary"]
    missing = _rule("r", alert_type="tool_latency_p95_above", threshold_value=10,
                    tool_name="Nope")
    assert ae.evaluate([missing], [], {}, quality=q) == []


@pytest.mark.parametrize("threshold", [20, 0.2])
def test_rates_accept_percent_or_fraction(threshold):
    q = {"escalation_rate": 0.25, "classified_total": 40}
    assert len(ae.evaluate([_rule("r", alert_type="escalation_rate_above",
                                  threshold_value=threshold)], [], {}, quality=q)) == 1
    q["escalation_rate"] = 0.2  # equal is not above
    assert ae.evaluate([_rule("r", alert_type="escalation_rate_above",
                              threshold_value=threshold)], [], {}, quality=q) == []


def test_below_rules_fire_when_the_figure_drops():
    q = {"review_accuracy": 0.75, "reviews": 5,
         "first_pass_rate": 0.95, "first_pass_known": 10}
    rules = [_rule("a", alert_type="review_accuracy_below", threshold_value=90),
             _rule("b", alert_type="first_pass_rate_below", threshold_value=90)]
    hit = ae.evaluate(rules, [], {}, quality=q)
    assert [h["rule"]["id"] for h in hit] == ["a"]
    assert hit[0]["metadata"]["direction"] == "below"


def test_each_quality_rule_reads_its_own_window():
    """The bug this fixes: one slice at the widest window served every rule,
    so an hour-long failure-rate rule was judged over a week."""
    calls = []
    slices = {
        60: {"classified_total": 10, "failed_count": 5, "failure_rate": 0.5},
        10080: {"classified_total": 1000, "failed_count": 5, "failure_rate": 0.005,
                "review_accuracy": 0.5, "reviews": 20},
    }

    def quality_for(window, runtime):
        calls.append((window, runtime))
        return slices[window]

    rules = [_rule("fail", alert_type="outcome_failure_rate", threshold_value=20),
             _rule("rev", alert_type="review_accuracy_below", threshold_value=90),
             _rule("fail2", alert_type="outcome_failure_rate", threshold_value=30)]
    hit = ae.evaluate(rules, [], {}, quality=slices[10080], quality_for=quality_for)
    assert sorted(h["rule"]["id"] for h in hit) == ["fail", "fail2", "rev"]
    # Memoised: two 60-minute rules, one fetch.
    assert sorted(calls) == [(60, None), (10080, None)]


def test_runtime_scoped_rule_asks_for_its_runtime():
    seen = []

    def quality_for(window, runtime):
        seen.append(runtime)
        return {"escalation_rate": 0.9, "classified_total": 9}

    r = _rule("r", alert_type="escalation_rate_above", threshold_value=10,
              runtime="codex")
    assert ae.evaluate([r], [], {}, quality_for=quality_for)
    assert seen == ["codex"]


# ── Figures on a real store ────────────────────────────────────────────────


@pytest.fixture
def store(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "s.duckdb"))
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.local_store as ls
    importlib.reload(ls)
    st = ls.LocalStore()
    yield st
    try:
        st.close()
    except Exception:
        pass


def _exec(st, sql, params):
    with st._write_lock:
        st._conn.execute(sql, params)


def _seed(st, now):
    ms = lambda t: int(t * 1000)  # noqa: E731
    # Three finished top-level Claude Code sessions (60 s, 120 s, 600 s),
    # one escalated; one classified two hours ago (outside a 60-minute
    # window); one sub-agent session (a handoff, not a session latency).
    for sid, dur, outcome, age in (("claude_code:s1", 60, "success", 300),
                                   ("claude_code:s2", 120, "success", 300),
                                   ("claude_code:s3", 600, "escalated", 300),
                                   ("claude_code:old", 30, "success", 7200),
                                   ("claude_code:child", 5000, "success", 300),
                                   ("oc1", 10, "success", 300)):
        end = now - age
        _exec(st, "INSERT INTO sessions (agent_type, session_id, started_at, ended_at,"
                  " last_active_at, updated_at, outcome, outcome_classified_at)"
                  " VALUES ('openclaw', ?, ?, ?, ?, ?, ?, ?)",
              [sid, _iso(end - dur), _iso(end), _iso(end), ms(now), outcome, ms(end)])
    # Handoffs from s1: one came back, one failed, one still running.
    for sub, status, spawned, ended in (("claude_code:child", "completed", now - 900, now - 600),
                                        ("claude_code:s1::b", "failed", now - 800, now - 790),
                                        ("claude_code:s1::c", "running", now - 100, None)):
        _exec(st, "INSERT INTO subagents (agent_type, subagent_id, parent_session_id,"
                  " spawned_at, ended_at, status, updated_at) VALUES ('openclaw', ?, ?, ?, ?, ?, ?)",
              [sub, "claude_code:s1", _iso(spawned), _iso(ended) if ended else None,
               status, ms(now)])
    # Tools: Bash 1 s and 3 s, Read 0.5 s and errored.
    n = 0
    for tool, tid, dur, err in (("Bash", "t1", 1.0, False), ("Bash", "t2", 3.0, False),
                                ("Read", "t3", 0.5, True)):
        start = now - 200 + n
        n += 10
        for et, ts, data in (
            ("tool_call", start, {"tool_name": tool, "tool_calls": [{"id": tid, "name": tool}]}),
            ("tool_result", start + dur, {"role": "tool", "extra": {"toolUseId": tid, "isError": err}}),
        ):
            _exec(st, "INSERT INTO events (id, node_id, session_id, event_type, ts, data, created_at)"
                      " VALUES (?, 'n', 'claude_code:s1', ?, ?, ?, ?)",
                  [f"{tid}-{et}", et, _iso(ts), json.dumps(data).encode(), ms(ts)])
    # Guardrails: a policy match on s1, a denied approval on s2, an allowed
    # guardrail verdict on s3 (not a violation), a blocking one on oc1.
    _exec(st, "INSERT INTO policy_actions (session_id, policy_id, step_index, action,"
              " created_at) VALUES ('claude_code:s1', 'p', 0, 'monitor', ?)", [ms(now - 60)])
    _exec(st, "INSERT INTO approvals (id, requestor_session_id, status, decision, created_at,"
              " resolved_at) VALUES ('a1', 'claude_code:s2', 'denied', 'denied', ?, ?)",
          [_iso(now - 60), _iso(now - 50)])
    _exec(st, "INSERT INTO approvals (id, requestor_session_id, status, decision, created_at)"
              " VALUES ('a2', 'claude_code:s3', 'timeout', 'timeout', ?)", [_iso(now - 60)])
    for gid, sid, verdict in (("g1", "claude_code:s3", "no_override"), ("g2", "oc1", "deny")):
        _exec(st, "INSERT INTO guardrail_events (id, ts, verdict, session_id) VALUES (?, ?, ?, ?)",
              [gid, _iso(now - 30), verdict, sid])
    # Review: 3 correct, 1 wrong, 1 borderline, 1 still pending.
    for i, status in enumerate(("reviewed_correct",) * 3 + ("reviewed_wrong",
                               "reviewed_borderline", "pending")):
        _exec(st, "INSERT INTO review_queue (session_id, sampled_at, status, reviewed_at)"
                  " VALUES (?, ?, ?, ?)",
              [f"claude_code:r{i}", _iso(now - 500), status,
               None if status == "pending" else _iso(now - 100)])


def test_figures_on_a_real_store(store):
    from clawmetry import agentops_metrics as am
    now = time.time()
    _seed(store, now)
    m = am.compute_window_extras(store, 60, now=now)

    assert m["timed_sessions"] == 4  # s1, s2, s3, oc1; not old, not child
    # sorted 10, 60, 120, 600: p95 at rank 2.85 -> 120 + 0.85 * 480
    assert m["session_duration_p95_sec"] == pytest.approx(528.0, abs=0.5)

    assert (m["tool_calls"], m["tool_errors"], m["timed_tool_calls"]) == (3, 1, 3)
    assert m["tool_latency_p95_ms"] == pytest.approx(2800, abs=1)
    bash = next(t for t in m["tool_latency_by_tool"] if t["name"] == "Bash")
    assert bash["calls"] == 2 and bash["timed_calls"] == 2

    assert (m["handoffs"], m["handoffs_finished"], m["handoff_failed"]) == (3, 2, 1)
    assert m["handoff_failure_rate"] == 0.5
    assert m["handoff_p95_sec"] == pytest.approx(285.5, abs=0.5)

    assert m["guardrail_violating_sessions"] == 3  # s1, s2, oc1
    assert m["guardrail_events_by_source"] == {
        "policy": 1, "approval_denied": 1, "guardrail_block": 1}
    assert m["guardrail_violation_rate"] == pytest.approx(3 / m["guardrail_sessions"], abs=1e-4)

    assert (m["reviews"], m["review_accuracy"]) == (4, 0.75)
    assert m["ground_truth_reported"] == 0 and m["ground_truth_accuracy"] is None


def test_figures_scope_to_a_runtime(store):
    from clawmetry import agentops_metrics as am
    now = time.time()
    _seed(store, now)
    cc = am.compute_window_extras(store, 60, "claude_code", now=now)
    oc = am.compute_window_extras(store, 60, "openclaw", now=now)
    assert cc["timed_sessions"] == 3 and oc["timed_sessions"] == 1
    assert cc["guardrail_violating_sessions"] == 2  # s1, s2
    assert oc["guardrail_violating_sessions"] == 1  # oc1
    assert oc["handoffs"] == 0 and cc["handoffs"] == 3
    assert oc["tool_calls"] == 0


def test_quality_window_carries_escalation_and_every_rule_figure(store):
    now = time.time()
    _seed(store, now)
    q = store.query_session_quality_window(window_minutes=60)
    assert q["escalated_count"] == 1
    assert q["escalation_rate"] == pytest.approx(1 / q["classified_total"])
    # Class guard: every AgentOps rule reads keys the slice actually has, so
    # renaming a figure cannot leave a rule silently never firing.
    for t, spec in ae.AGENTOPS_RULES.items():
        assert spec["value"] in q, (t, spec["value"])
        assert spec["sample"] in q, (t, spec["sample"])


def test_ground_truth_resolves_bare_ids_and_merges_reports(store):
    from clawmetry import agentops_metrics as am
    now = time.time()
    _seed(store, now)
    r = store.ingest_ground_truth({"session_id": "s3", "correct": True})
    assert r == {"session_id": "claude_code:s3", "session_known": True,
                 "created": True, "reports": 1}
    r = store.ingest_ground_truth({"session_id": "claude_code:s3", "first_pass": False,
                                   "source": "payer"})
    assert r["reports"] == 2 and not r["created"]
    row = store.query_ground_truth(session_id="s3")[0]
    assert (row["correct"], row["first_pass"], row["source"]) == (True, False, "payer")
    unknown = store.ingest_ground_truth({"session_id": "later", "correct": False})
    assert unknown["session_known"] is False
    m = am.compute_window_extras(store, 60, now=time.time() + 1)
    assert (m["ground_truth_judged"], m["ground_truth_accuracy"]) == (2, 0.5)
    assert (m["first_pass_known"], m["first_pass_rate"]) == (1, 0.0)
    with pytest.raises(ValueError):
        store.ingest_ground_truth({"correct": True})


# ── Routes ─────────────────────────────────────────────────────────────────


def _agentops_app(monkeypatch, fake):
    import routes.agentops as ra
    monkeypatch.setattr(ra, "_ls_call", fake)
    app = Flask(__name__)
    app.register_blueprint(ra.bp_agentops)
    return app.test_client()


def test_ground_truth_post_validates_and_reports_a_down_store(monkeypatch):
    got = {}

    def fake(method, **kw):
        got[method] = kw
        return {"session_id": kw["record"]["session_id"], "session_known": True,
                "created": True, "reports": 1}

    c = _agentops_app(monkeypatch, fake)
    assert c.post("/api/ground-truth", json={}).status_code == 400
    assert c.post("/api/ground-truth", json={"session_id": "x"}).status_code == 400
    bad = c.post("/api/ground-truth", json={"session_id": "x", "correct": "yes"})
    assert bad.status_code == 400 and "true or false" in bad.get_json()["error"]
    ok = c.post("/api/ground-truth", json={"session_id": "x", "correct": True,
                                           "first_pass": True, "source": "payer"})
    assert ok.status_code == 201 and ok.get_json()["ok"] is True
    assert got["ingest_ground_truth"]["record"]["source"] == "payer"

    down = _agentops_app(monkeypatch, lambda m, **kw: None)
    r = down.post("/api/ground-truth", json={"session_id": "x", "correct": True})
    assert r.status_code == 503 and r.get_json()["store_available"] is False
    assert "—" not in r.get_json()["error"]


def test_scorecard_is_honest_about_an_unreadable_store(monkeypatch):
    c = _agentops_app(monkeypatch, lambda m, **kw: None)
    j = c.get("/api/agentops/scorecard?window=60&runtime=codex").get_json()
    assert j["store_available"] is False and j["metrics"] == {}
    assert j["runtime"] == "codex"
    assert set(j["alert_rules"]) == set(ae.AGENTOPS_RULES)

    seen = {}

    def fake(method, **kw):
        seen.update(kw)
        return {"eval_scores": [1, 2], "timed_sessions": 4}

    j = _agentops_app(monkeypatch, fake).get("/api/agentops/scorecard?window=10080").get_json()
    assert j["store_available"] is True and "eval_scores" not in j["metrics"]
    assert seen == {"window_minutes": 10080}


def test_mirror_carries_agentops_fields(monkeypatch):
    import routes.alerts as ra
    sent = {}
    monkeypatch.setattr(ra, "_write_via_store", lambda m, **kw: sent.update(kw) or True)
    monkeypatch.setattr(ra, "_rule_in_duckdb", lambda rid: True)
    assert ra._mirror_rule_to_duckdb(
        "r1", alert_type="tool_latency_p95_above", threshold=30, runtime="all",
        channels=["banner"], cooldown_min=30, enabled=True,
        extra={"tool_name": "Bash", "window_minutes": 15})
    cond = sent["rule"]["condition_json"]
    assert (cond["tool_name"], cond["window_minutes"]) == ("Bash", 15)


# ── SLA, review sampling, cohort key ───────────────────────────────────────


def test_sla_metrics_come_from_the_quality_slice():
    from routes.sla import metric_from_slice
    q = {"session_duration_p95_sec": 42.0, "tool_error_rate": 0.05,
         "window_spend_usd": 10.0, "classified_total": 4}
    assert metric_from_slice("p95_completion_sec", q) == 42.0
    assert metric_from_slice("error_rate_pct", q) == pytest.approx(5.0)
    assert metric_from_slice("cost_per_session_usd", q) == 2.5
    assert metric_from_slice("cost_per_session_usd", {"classified_total": 0}) is None
    assert metric_from_slice("p95_completion_sec", None) is None


def test_red_sla_policy_fires_green_does_not(monkeypatch):
    import routes.sla as sla
    monkeypatch.setattr(sla, "sla_statuses", lambda: [
        {"id": "a", "name": "Fast", "metric": "p95_completion_sec", "threshold": 60,
         "window_sec": 3600, "agent_id": "codex", "actual": 90.0, "colour": "red"},
        {"id": "b", "name": "Cheap", "metric": "cost_per_session_usd", "threshold": 5,
         "window_sec": 3600, "agent_id": None, "actual": 1.0, "colour": "green"},
        {"id": "c", "name": "Unknown", "metric": "error_rate_pct", "threshold": 5,
         "window_sec": 3600, "agent_id": None, "actual": None, "colour": "unknown"},
    ])
    fired = []
    assert sla.fire_breached_policies(lambda **kw: fired.append(kw)) == 1
    assert fired[0]["rule_id"] == "sla:a" and fired[0]["alert_type"] == "sla_breach"
    msg = fired[0]["message"]
    assert "90 s" in msg and "60 s" in msg and "on codex" in msg
    assert "—" not in msg and "--" not in msg


def test_percentage_review_sampling(monkeypatch):
    import routes.review as rv
    assert rv.per_agent_quota(100, 10, 5) == 5
    assert rv.per_agent_quota(3, 10, 5) == 1        # every agent gets a row
    assert rv.per_agent_quota(100, 10, 0) == 10     # count mode unchanged
    assert rv.per_agent_quota(0, 10, 5) == 0
    monkeypatch.setattr(rv, "MAX_SAMPLE_PER_AGENT", 7)
    assert rv.per_agent_quota(1000, 10, 50) == 7

    now = datetime(2026, 9, 11, 12, tzinfo=timezone.utc)
    day = (now - timedelta(days=1)).date().isoformat()
    rows = [{"session_id": f"s{i}", "agent_id": "main", "started_at": day + "T10:00:00"}
            for i in range(40)]
    inserted = []

    def fake(method, **kw):
        if method == "query_sessions_table":
            return rows
        inserted.append(kw["sample"]["session_id"])
        return 1

    monkeypatch.setattr(rv, "_store_call", fake)
    out = rv.sample_yesterday_for_review(pct=10, now=now)
    assert out["mode"] == "percent" and out["sampled"] == 4 and len(inserted) == 4
    inserted.clear()
    assert rv.sample_yesterday_for_review(sample_size=2, now=now)["sampled"] == 2


def test_prompt_fingerprint_is_a_cohort_key():
    from clawmetry import cohort_compare as cc
    f = cc.parse_filter({"instructions": "ABC123", "bogus": "x"})
    assert f == {"instructions": "ABC123"}
    assert cc.session_matches({"instructions_hash": "abc123def456", "runtime": "x"}, f)
    assert not cc.session_matches({"instructions_hash": "fff", "runtime": "x"}, f)
    assert not cc.session_matches({"runtime": "x"}, f)
    assert "prompt ABC123" in cc.describe_filter(f)
    views = [{"cost_usd": 1.0, "tokens": 1000, "steps": None, "tool_results": None,
              "tool_errors": None, "cache_read": None, "input_tokens": None,
              "outcome": "success", "done": True, "done_basis": "outcome"}] * 2
    assert cc.cohort_stats(views)["tokens_per_done"] == 1000


# ── Class guards: every AgentOps rule type is wired end to end ─────────────


def _read(rel):
    with open(os.path.join(_REPO, rel), encoding="utf-8") as fh:
        return fh.read()


def test_every_agentops_rule_is_routed_and_offered():
    import routes.alerts as ra
    html = _read("clawmetry/templates/tabs/alerts.html")
    js = _read("clawmetry/static/js/alerts.js")
    ui_block = js.split("const AGENTOPS_RULE_UI = {", 1)[1].split("\n  };", 1)[0]
    for t in ae.AGENTOPS_RULES:
        assert ae._LEGACY_ALERT_TYPE_MAP.get(t) == t, t
        assert t in ae.QUALITY_RULE_TYPES, t
        assert t in ra._EVALUATOR_ONLY, t
        assert f'data-type="{t}"' in html, f"no picker button for {t}"
        assert re.search(rf"^\s+{t}: \{{", ui_block, re.M), f"no editor entry for {t}"


def test_new_user_facing_copy_has_no_dashes():
    js = _read("clawmetry/static/js/alerts.js")
    block = js.split("const AGENTOPS_RULE_UI = {", 1)[1].split("\n  };", 1)[0]
    assert "—" not in block and " -- " not in block
