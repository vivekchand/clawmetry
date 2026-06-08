"""Regression guard: the audit log is REAL (producers actually write).

Before 2026-06-08 ``clawmetry/audit.py`` was a hollow pipe — ``record_audit``
had ZERO callers outside the module itself, so the Enterprise audit-log query
endpoint rendered nothing. This suite asserts that each governance-relevant
state-change path actually lands an audit row, mechanically, so the hollow-pipe
regression cannot silently recur.

Each test exercises a real producer code path (HITL decide, budget config,
alert-rule create, approval decision relay, cloud-mediated approval outcome)
and asserts an ``audit_log`` row appeared with the expected ``event_type``.

A separate test pins the ``/api/security/integrity`` route shape.
"""
from __future__ import annotations

import importlib
import os
import sys
import time
import types

import pytest

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)


# ── Fixtures ───────────────────────────────────────────────────────────────


@pytest.fixture
def audit(monkeypatch, tmp_path):
    """Reload clawmetry.audit against a throwaway SQLite file so producers
    write there and the real ~/.clawmetry/audit.db is never touched. Producers
    do a late ``from clawmetry import audit`` so they pick up this same module
    object out of sys.modules."""
    monkeypatch.setenv("CLAWMETRY_AUDIT_DB", str(tmp_path / "audit.db"))
    sys.modules.pop("clawmetry.audit", None)
    import clawmetry.audit as A
    importlib.reload(A)
    return A


def _types(audit):
    return {t["event_type"] for t in audit.event_types()}


# ── audit_event wrapper schema ──────────────────────────────────────────────


def test_audit_event_wrapper_schema(audit):
    audit.audit_event(
        "approval.decision",
        actor="cloud",
        target="Bash",
        result="denied",
        source="approvals",
        metadata={"policy": "rm-guard"},
    )
    rows = audit.read_audit_log(limit=5)
    assert len(rows) == 1
    r = rows[0]
    assert r["event_type"] == "approval.decision"
    assert r["actor"] == "cloud"
    assert r["target"] == "Bash"
    assert r["details"]["result"] == "denied"
    assert r["details"]["source"] == "approvals"
    assert r["details"]["policy"] == "rm-guard"


def test_audit_event_never_raises(audit, monkeypatch):
    # Even if record_audit blows up, audit_event must swallow it.
    monkeypatch.setattr(audit, "record_audit",
                        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom")))
    audit.audit_event("x.y")  # must not raise


# ── Producer: HITL flag + decide (routes/hitl.py) ───────────────────────────


def _hitl_client(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))  # _HITL_DIR derives from Path.home()
    from flask import Flask
    sys.modules.pop("routes.hitl", None)
    import routes.hitl as rh
    importlib.reload(rh)
    # _HITL_DIR was bound at import; repoint it at the temp HOME.
    rh._HITL_DIR = tmp_path / ".clawmetry" / "hitl"
    # Don't let the DuckDB mirror touch a real store.
    monkeypatch.setattr(rh, "_try_store_call", lambda *a, **k: None)
    app = Flask(__name__)
    app.register_blueprint(rh.bp_hitl)
    return app.test_client()


def test_hitl_flag_records_audit(audit, tmp_path, monkeypatch):
    client = _hitl_client(tmp_path, monkeypatch)
    resp = client.post("/api/hitl/flag",
                       json={"session_id": "sess-1", "operator": "alice",
                             "reason": "looks risky"})
    assert resp.status_code == 200, resp.data
    rows = audit.read_audit_log()
    assert any(r["event_type"] == "hitl.pause" and r["actor"] == "alice"
               and r["target"] == "sess-1" for r in rows)


def test_hitl_decide_records_audit(audit, tmp_path, monkeypatch):
    client = _hitl_client(tmp_path, monkeypatch)
    client.post("/api/hitl/flag", json={"session_id": "sess-2", "operator": "bob"})
    resp = client.post("/api/hitl/decide",
                       json={"session_id": "sess-2", "decision": "approve",
                             "operator": "bob"})
    assert resp.status_code == 200, resp.data
    rows = audit.read_audit_log()
    # approve -> hitl.resume with result "resumed"
    assert any(r["event_type"] == "hitl.resume"
               and r["details"].get("result") == "resumed"
               and r["target"] == "sess-2" for r in rows)


# ── Producer: cloud-mediated approval outcome (clawmetry/approvals.py) ───────


def test_process_tool_call_records_decision(audit, monkeypatch):
    sys.modules.pop("clawmetry.approvals", None)
    import clawmetry.approvals as ap
    importlib.reload(ap)

    policy = {
        "name": "rm-guard", "tool": "exec", "command_regex": None,
        "command_not_regex": None, "args_regex": None,
        "action": "require_approval", "timeout": 1, "on_timeout": "deny",
    }
    # Stub the cloud + store round-trips so the path runs offline.
    monkeypatch.setattr(ap, "_post_approval_request",
                        lambda api_key, req: {"id": req["id"]})
    monkeypatch.setattr(ap, "_poll_decision",
                        lambda api_key, aid, timeout: "denied")
    monkeypatch.setattr(ap, "_kill_session", lambda sid: True)
    # Neutralise the DuckDB ingest/update calls.
    fake_ls = types.SimpleNamespace(
        get_store=lambda: types.SimpleNamespace(
            ingest_approval=lambda *a, **k: None,
            update_approval_decision=lambda *a, **k: None,
        )
    )
    monkeypatch.setitem(sys.modules, "clawmetry.local_store", fake_ls)

    out = ap.process_tool_call(
        api_key="k", node_id="n", session_id="sess-9",
        tool_call_id="tc-1", tool_name="Bash", args={"command": "rm -rf /"},
        policies=[policy],
    )
    assert out["decision"] == "denied"
    rows = audit.read_audit_log()
    hit = next((r for r in rows if r["event_type"] == "approval.decision"), None)
    assert hit is not None
    assert hit["details"]["result"] == "denied"
    assert hit["details"]["policy"] == "rm-guard"
    assert hit["target"] == "Bash"


# ── Producer: cloud-relayed approval decision (clawmetry/sync.py) ────────────


def test_apply_approval_decision_records_audit(audit, monkeypatch):
    import clawmetry.sync as sync

    # update_approval_decision returns 1 (a row flipped) so the producer fires.
    fake_store = types.SimpleNamespace(
        update_approval_decision=lambda *a, **k: 1)
    fake_ls = types.SimpleNamespace(get_store=lambda: fake_store)
    monkeypatch.setitem(sys.modules, "clawmetry.local_store", fake_ls)

    sync._apply_approval_decision({
        "type": "approval_decision", "id": "appr-1",
        "decision": "approved", "resolver": "user@example.com",
    })
    rows = audit.read_audit_log()
    assert any(r["event_type"] == "approval.decision"
               and r["actor"] == "user@example.com"
               and r["target"] == "appr-1"
               and r["details"].get("result") == "approved" for r in rows)


def test_apply_approval_decision_noop_does_not_audit(audit, monkeypatch):
    import clawmetry.sync as sync
    # returns 0 (already decided / unknown) -> must NOT log a duplicate.
    fake_store = types.SimpleNamespace(
        update_approval_decision=lambda *a, **k: 0)
    fake_ls = types.SimpleNamespace(get_store=lambda: fake_store)
    monkeypatch.setitem(sys.modules, "clawmetry.local_store", fake_ls)

    sync._apply_approval_decision({
        "type": "approval_decision", "id": "appr-2", "decision": "approved",
    })
    assert all(r["target"] != "appr-2" for r in audit.read_audit_log())


# ── Producer: budget + alert-rule changes (routes/alerts.py) ────────────────


@pytest.fixture
def alerts_env(tmp_path, monkeypatch):
    """A dashboard + routes.alerts slate wired to throwaway DBs."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "1")
    sys.modules.pop("clawmetry.local_store", None)
    import clawmetry.local_store as ls
    importlib.reload(ls)
    ls.get_store()

    sys.modules.pop("dashboard", None)
    sys.modules.pop("routes.alerts", None)
    import dashboard as _d
    import routes.alerts as ra
    importlib.reload(ra)
    _d.FLEET_DB_PATH = str(tmp_path / "fleet.db")
    try:
        _d._budget_init_db()
    except Exception:
        pass
    monkeypatch.setattr(_d, "_pause_gateway", lambda: None, raising=False)

    from flask import Flask
    app = Flask(__name__)
    app.register_blueprint(ra.bp_budget)
    app.register_blueprint(ra.bp_alerts)
    yield app.test_client()


def test_budget_config_records_audit(audit, alerts_env):
    resp = alerts_env.post("/api/budget/config", json={"daily_limit": 12.5})
    assert resp.status_code == 200, resp.data
    rows = audit.read_audit_log()
    hit = next((r for r in rows if r["event_type"] == "budget.config"), None)
    assert hit is not None
    # old/new captured for the changed field.
    changed = hit["details"].get("changed", {})
    assert "daily_limit" in changed
    assert changed["daily_limit"]["new"] == 12.5


def test_alert_rule_create_records_audit(audit, alerts_env):
    resp = alerts_env.post("/api/alerts/rules",
                           json={"type": "threshold", "threshold": 5})
    assert resp.status_code == 200, resp.data
    rule_id = resp.get_json()["id"]
    rows = audit.read_audit_log()
    assert any(r["event_type"] == "alert_rule.create" and r["target"] == rule_id
               for r in rows)


def test_agent_budget_put_records_audit(audit, alerts_env):
    resp = alerts_env.put("/api/agents/agent-x/budget",
                          json={"daily_limit_usd": 3.0})
    assert resp.status_code == 200, resp.data
    rows = audit.read_audit_log()
    assert any(r["event_type"] == "budget.agent_set" and r["target"] == "agent-x"
               for r in rows)


# ── /api/security/integrity route shape ─────────────────────────────────────


def test_security_integrity_route_shape(monkeypatch):
    from flask import Flask
    sys.modules.pop("routes.infra", None)
    import routes.infra as ri
    importlib.reload(ri)

    # Stub the verifier so the test is hermetic (no DuckDB needed).
    def _fake_call(method, **kwargs):
        assert method == "verify_integrity"
        return {"status": "valid", "checked": 1240, "pre_chain": 3,
                "broken_at": None, "error": None}
    monkeypatch.setattr(
        "routes.local_query.local_store_via_daemon", _fake_call, raising=False)

    app = Flask(__name__)
    app.register_blueprint(ri.bp_security)
    client = app.test_client()
    resp = client.get("/api/security/integrity")
    assert resp.status_code == 200, resp.data
    body = resp.get_json()
    assert body["ok"] is True
    assert body["status"] == "valid"
    assert body["chain_length"] == 1240
    assert body["pre_chain"] == 3
    assert body["first_break"] is None


def test_security_integrity_route_invalid(monkeypatch):
    from flask import Flask
    sys.modules.pop("routes.infra", None)
    import routes.infra as ri
    importlib.reload(ri)
    monkeypatch.setattr(
        "routes.local_query.local_store_via_daemon",
        lambda method, **k: {"status": "invalid", "checked": 10, "pre_chain": 0,
                             "broken_at": 42, "error": "chain break at 42"},
        raising=False)
    app = Flask(__name__)
    app.register_blueprint(ri.bp_security)
    resp = app.test_client().get("/api/security/integrity")
    body = resp.get_json()
    assert body["ok"] is False
    assert body["first_break"] == 42


def test_security_audit_route_serves_rows(audit, monkeypatch):
    audit.record_audit("budget.config", actor="dash", target="budget")
    from flask import Flask
    sys.modules.pop("routes.infra", None)
    import routes.infra as ri
    importlib.reload(ri)
    app = Flask(__name__)
    app.register_blueprint(ri.bp_security)
    resp = app.test_client().get("/api/security/audit?limit=10")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["count"] >= 1
    assert any(e["event_type"] == "budget.config" for e in body["entries"])
