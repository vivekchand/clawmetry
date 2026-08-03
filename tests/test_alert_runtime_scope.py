"""Runtime-scoped alert rules + approvals filtering (founder 2026-08-03:
"each alert / approval should be runtime-wise by default, with a node-wide
option").

Three surfaces, all covered here:
  * ``clawmetry.alert_evaluator`` — a rule carrying ``runtime`` (row column
    or ``condition_json.runtime``) only sees that runtime's events (session-id
    prefix), and quality-type rules read the per-runtime slice from
    ``quality_by_runtime`` — NEVER the node aggregate.
  * ``routes/alerts.py`` CRUD — ``runtime`` persists on create, updates on
    PUT, defaults to node-wide ('all') for legacy callers, and unknown
    runtime ids are rejected (never silently widened to node-wide).
  * ``routes/policy.py`` — ``?runtime=`` scopes the approvals queue + audit
    by the requesting session's prefix.

Pure-unit for the evaluator; Flask test client + tmp fleet DB for the routes.
"""
from __future__ import annotations

import os
import sys

import pytest

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from clawmetry import alert_evaluator  # noqa: E402


def _rule(rid, runtime=None, **cond):
    row = {
        "id": rid,
        "name": f"rule {rid}",
        "enabled": True,
        "condition_json": cond,
    }
    if runtime is not None:
        row["runtime"] = runtime
    return row


def _evt(i, session_id, et="error", ts="2026-08-03T01:00:00+00:00"):
    return {"id": f"e{i}", "event_type": et, "ts": ts,
            "session_id": session_id, "data": {}}


# ── evaluator: event-stream rules ─────────────────────────────────────────


def test_scoped_rule_only_sees_its_runtime_events():
    rule = _rule("r1", runtime="copilot", type="count_over_threshold",
                 event_type="error", threshold=2, window_sec=3600,
                 cooldown_sec=0)
    events = [
        _evt(1, "copilot:aaa"), _evt(2, "copilot:bbb"),
        _evt(3, "claude_code:ccc"), _evt(4, "bare-uuid-openclaw"),
    ]
    matches = alert_evaluator.evaluate([rule], events, {})
    assert len(matches) == 1  # 2 copilot errors >= threshold 2

    rule_hi = _rule("r2", runtime="copilot", type="count_over_threshold",
                    event_type="error", threshold=3, window_sec=3600,
                    cooldown_sec=0)
    assert alert_evaluator.evaluate([rule_hi], events, {}) == []
    # ...while an unscoped rule at the same threshold fires on all 4.
    rule_all = _rule("r3", type="count_over_threshold", event_type="error",
                     threshold=3, window_sec=3600, cooldown_sec=0)
    assert len(alert_evaluator.evaluate([rule_all], events, {})) == 1


def test_scope_via_condition_json_matches_row_column():
    events = [_evt(1, "copilot:aaa"), _evt(2, "copilot:bbb")]
    via_cond = _rule("rc", type="count_over_threshold", event_type="error",
                     threshold=2, window_sec=3600, cooldown_sec=0,
                     runtime="copilot")
    assert len(alert_evaluator.evaluate([via_cond], events, {})) == 1


def test_openclaw_scope_means_no_family_prefix():
    rule = _rule("r4", runtime="openclaw", type="count_over_threshold",
                 event_type="error", threshold=1, window_sec=3600,
                 cooldown_sec=0)
    matches = alert_evaluator.evaluate(
        [rule], [_evt(1, "copilot:aaa"), _evt(2, "bare-uuid")], {})
    assert len(matches) == 1
    assert matches[0]["event"]["session_id"] == "bare-uuid"


def test_scoped_quality_rule_never_reads_node_aggregate():
    rule = _rule("q1", runtime="copilot", alert_type="eval_score_below",
                 threshold=3, cooldown_sec=0)
    node_quality = {"eval_count": 10, "eval_avg": 1.0,
                    "outcome_classified": 0, "outcome_failed": 0,
                    "window_minutes": 60}
    # Node aggregate is WAY below threshold, but no per-runtime slice was
    # provided -> the scoped rule must NOT fire on the node number.
    assert alert_evaluator.evaluate([rule], [], {}, node_quality) == []
    # With a per-runtime slice, it evaluates that slice.
    per_rt = {"copilot": node_quality}
    fired = alert_evaluator.evaluate(
        [rule], [], {}, node_quality, quality_by_runtime=per_rt)
    assert len(fired) == 1


# ── routes: alert rule CRUD ───────────────────────────────────────────────


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Blueprint-only Flask app (the gate-test pattern) with a REAL sqlite
    fleet DB in tmp so the runtime column round-trips end to end."""
    import sqlite3
    from flask import Flask
    from routes.alerts import bp_alerts
    from routes.policy import bp_policy
    import dashboard as d

    db_path = str(tmp_path / "fleet.db")

    def _mk_db():
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        conn.execute(
            """CREATE TABLE IF NOT EXISTS alert_rules (
                id TEXT PRIMARY KEY, type TEXT NOT NULL,
                threshold REAL NOT NULL, channels TEXT NOT NULL,
                cooldown_min INTEGER DEFAULT 30, enabled INTEGER DEFAULT 1,
                runtime TEXT DEFAULT 'all',
                created_at REAL NOT NULL, updated_at REAL NOT NULL)""")
        return conn

    class _NoopLock:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    monkeypatch.setattr(d, "_fleet_db", _mk_db)
    monkeypatch.setattr(d, "_fleet_db_lock", _NoopLock())

    def _rules_from_db():
        conn = _mk_db()
        rows = [dict(r) for r in conn.execute(
            "SELECT * FROM alert_rules ORDER BY created_at DESC").fetchall()]
        conn.close()
        return rows

    monkeypatch.setattr(d, "_get_alert_rules", _rules_from_db)
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "0")

    app = Flask(__name__)
    app.register_blueprint(bp_alerts)
    app.register_blueprint(bp_policy)
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def _auth_post(client, url, json_body):
    return client.post(url, json=json_body)


def test_rule_create_persists_runtime(client):
    r = _auth_post(client, "/api/alerts/rules",
                   {"type": "threshold", "threshold": 5,
                    "runtime": "copilot"})
    assert r.status_code == 200, r.get_json()
    rid = r.get_json()["id"]
    rules = client.get("/api/alerts/rules").get_json()["rules"]
    mine = [x for x in rules if x["id"] == rid]
    assert mine and mine[0].get("runtime") == "copilot"
    # PUT can rescope to node-wide.
    r2 = client.put(f"/api/alerts/rules/{rid}", json={"runtime": "all"})
    assert r2.status_code == 200
    rules = client.get("/api/alerts/rules").get_json()["rules"]
    assert [x for x in rules if x["id"] == rid][0].get("runtime") == "all"


def test_rule_create_defaults_node_wide(client):
    r = _auth_post(client, "/api/alerts/rules",
                   {"type": "threshold", "threshold": 5})
    assert r.status_code == 200
    rid = r.get_json()["id"]
    rules = client.get("/api/alerts/rules").get_json()["rules"]
    assert [x for x in rules if x["id"] == rid][0].get("runtime") == "all"


def test_rule_create_rejects_unknown_runtime(client):
    r = _auth_post(client, "/api/alerts/rules",
                   {"type": "threshold", "threshold": 5,
                    "runtime": "notaruntime"})
    assert r.status_code == 400


# ── routes: approvals runtime filter ──────────────────────────────────────


def test_approvals_queue_scopes_by_runtime(client, monkeypatch):
    import routes.policy as pol
    rows = [
        {"id": "a1", "action": "exec", "status": "pending",
         "requestor_session_id": "copilot:xyz", "args": "{}",
         "created_at": "2026-08-03T00:00:00Z"},
        {"id": "a2", "action": "exec", "status": "pending",
         "requestor_session_id": "claude_code:abc", "args": "{}",
         "created_at": "2026-08-03T00:00:00Z"},
        {"id": "a3", "action": "exec", "status": "pending",
         "requestor_session_id": "bare-openclaw-uuid", "args": "{}",
         "created_at": "2026-08-03T00:00:00Z"},
    ]
    monkeypatch.setattr(pol, "_ls_call", lambda *a, **k: rows)

    body = client.get("/api/approvals?runtime=copilot").get_json()
    assert [a["id"] for a in body["approvals"]] == ["a1"]
    body = client.get("/api/approvals?runtime=openclaw").get_json()
    assert [a["id"] for a in body["approvals"]] == ["a3"]
    body = client.get("/api/approvals").get_json()
    assert len(body["approvals"]) == 3

    audit = client.get("/api/approvals-audit?runtime=claude_code").get_json()
    assert [d["id"] for d in audit["decisions"]] == ["a2"]
