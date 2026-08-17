"""Integration tests: approve-and-remember + risk chips through the real
HTTP surfaces (hook receiver, decide route, queue/audit payloads).

Covers what the kernel-only tests in test_tool_risk.py cannot:
  * decide with remember='session' writes a session-allow entry that the
    PreToolUse hook receiver then honors (no second pending row);
  * decide with remember='always' appends an ``action: approve`` policy
    row to policies.yml that survives a reload and short-circuits the
    NEXT identical call;
  * risk chips ride the queue (/api/approvals) and audit
    (/api/approvals-audit) payloads via the ``_cm_risk`` args stamp.

Same harness as tests/test_runtime_gates_and_hooks.py: fresh DuckDB store
under an isolated HOME, no daemon proxy, entitlement pinned.
"""
from __future__ import annotations

import importlib
import os
import sys
import time

import pytest
from flask import Flask

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)


@pytest.fixture
def fresh_store(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv(
        "CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "1")
    sys.modules.pop("clawmetry.local_store", None)
    import clawmetry.local_store as ls
    importlib.reload(ls)
    yield ls
    try:
        ls.get_store().stop(flush=False)
    except Exception:
        pass


def _pin_entitlement(monkeypatch, *, features=("approval_queue",)):
    import clawmetry.entitlements as ent
    e = ent.Entitlement(tier="pro", source="test", grace=False,
                        features=frozenset(features), runtimes=frozenset())
    monkeypatch.setattr(ent, "get_entitlement", lambda force=False: e)


@pytest.fixture
def harness(fresh_store, tmp_path, monkeypatch):
    _pin_entitlement(monkeypatch)
    import routes.local_query as lq
    monkeypatch.setattr(lq, "local_store_via_daemon", lambda *a, **k: None)
    import clawmetry.approvals as ap
    monkeypatch.setattr(ap, "POLICIES_PATH", tmp_path / "policies.yml")
    monkeypatch.setattr(ap, "_SESSION_ALLOW_PATH",
                        tmp_path / "approvals_session_allow.json")
    import routes.hooks as rh
    from routes.hooks import bp_hooks
    from routes.policy import bp_policy
    # Fast hook slices so pending answers return quickly in tests.
    monkeypatch.setattr(rh, "_WAIT_SLICE_S", 0.3)
    monkeypatch.setattr(rh, "_POLL_INTERVAL_S", 0.05)
    app = Flask(__name__)
    app.register_blueprint(bp_hooks)
    app.register_blueprint(bp_policy)
    return app.test_client(), fresh_store, ap


def _gate_policy(ap, **kw):
    ap.POLICIES_PATH.parent.mkdir(parents=True, exist_ok=True)
    ap.POLICIES_PATH.write_text(
        "- name: 'high risk gate'\n"
        "  min_risk: 'high'\n"
        "  action: 'require_approval'\n"
        "  timeout: 30\n"
        "  on_timeout: 'deny'\n")


def _post_hook(client, cmd, session="sess-A", tool="Bash", resume=None):
    body = {"tool_name": tool, "tool_input": {"command": cmd},
            "session_id": session, "cwd": "/tmp",
            "tool_use_id": f"tu-{abs(hash((cmd, session, resume)))}"}
    if resume:
        body["approval_id"] = resume
    return client.post("/api/hooks/claude-code/pretooluse", json=body)


def test_low_risk_call_passes_min_risk_gate(harness):
    client, ls, ap = harness
    _gate_policy(ap)
    r = _post_hook(client, "git status")
    hso = r.get_json()["hookSpecificOutput"]
    assert hso["permissionDecision"] == "allow"
    assert "no matching policy" in hso["permissionDecisionReason"]


def test_high_risk_call_parks_with_risk_chip(harness):
    client, ls, ap = harness
    _gate_policy(ap)
    r = _post_hook(client, "rm -rf /tmp/x")
    body = r.get_json()
    # Not decided within one 0.3 s slice → parked pending.
    assert body.get("status") == "pending"
    aid = body["approval_id"]
    # Queue payload carries the risk verdict.
    q = client.get("/api/approvals").get_json()
    row = next(a for a in q["approvals"] if a["id"] == aid)
    assert row["risk"]["level"] == "high"
    assert any("recursive delete" in x for x in row["risk"]["reasons"])
    # Audit payload carries it too.
    audit = client.get("/api/approvals-audit").get_json()
    dec = next(d for d in audit["decisions"] if d["id"] == aid)
    assert dec["risk"]["level"] == "high"


def test_remember_session_skips_next_prompt(harness):
    client, ls, ap = harness
    _gate_policy(ap)
    r = _post_hook(client, "rm -rf /tmp/x")
    aid = r.get_json()["approval_id"]
    # Human approves WITH remember=session.
    d = client.post(f"/api/approvals/{aid}/decide",
                    json={"decision": "approve", "remember": "session"})
    assert d.status_code == 200
    assert d.get_json()["remembered"] == "session"
    # Resume sees the approval.
    r2 = _post_hook(client, "rm -rf /tmp/x", resume=aid)
    assert r2.get_json()["hookSpecificOutput"]["permissionDecision"] == "allow"
    # The NEXT identical call in the same session sails through without a
    # new pending row.
    r3 = _post_hook(client, "rm -rf /tmp/x")
    hso = r3.get_json()["hookSpecificOutput"]
    assert hso["permissionDecision"] == "allow"
    assert "session" in hso["permissionDecisionReason"]
    # A DIFFERENT command still parks.
    r4 = _post_hook(client, "rm -rf /tmp/other")
    assert r4.get_json().get("status") == "pending"
    # A different session still parks for the SAME command.
    r5 = _post_hook(client, "rm -rf /tmp/x", session="sess-B")
    assert r5.get_json().get("status") == "pending"


def test_remember_always_appends_visible_policy(harness):
    client, ls, ap = harness
    _gate_policy(ap)
    r = _post_hook(client, "rm -rf /tmp/x")
    aid = r.get_json()["approval_id"]
    d = client.post(f"/api/approvals/{aid}/decide",
                    json={"decision": "approve", "remember": "always"})
    assert d.get_json()["remembered"] == "always"
    # The rule landed in policies.yml, visible + revocable.
    text = ap.POLICIES_PATH.read_text()
    assert "Always allow" in text and "action: 'approve'" in text
    # It round-trips through the loader and short-circuits the next call,
    # even from a DIFFERENT session (always-allow is not session-bound).
    policies = ap.load_policies()
    assert any((p.get("action") == "approve") for p in policies)
    r2 = _post_hook(client, "rm -rf /tmp/x", session="sess-C")
    hso = r2.get_json()["hookSpecificOutput"]
    assert hso["permissionDecision"] == "allow"
    assert "always-allow" in hso["permissionDecisionReason"]


def test_remember_rejects_unknown_scope(harness):
    client, ls, ap = harness
    _gate_policy(ap)
    r = _post_hook(client, "rm -rf /tmp/x")
    aid = r.get_json()["approval_id"]
    d = client.post(f"/api/approvals/{aid}/decide",
                    json={"decision": "approve", "remember": "forever"})
    assert d.status_code == 400


def test_watcher_session_allow_short_circuit(harness, monkeypatch):
    """The reactive watcher path honors the same session grant: a second
    process_tool_call for the remembered (session, tool, command) returns
    approved instantly with an auto_approved audit row."""
    client, ls, ap = harness
    _gate_policy(ap)
    policies = ap.load_policies()
    ap.add_session_allow("claude_code:sess-A", "Bash",
                         {"command": "rm -rf /tmp/x"})
    out = ap.process_tool_call(
        api_key="", node_id="n1", session_id="claude_code:sess-A",
        tool_call_id="tc-1", tool_name="Bash",
        args={"command": "rm -rf /tmp/x"}, policies=policies)
    assert out["decision"] == "approved"
    assert out.get("session_allow") is True
    rows = ls.get_store().query_approvals(limit=10)
    assert any(r.get("status") == "auto_approved" for r in rows)
    # And the auto_approved row carries the risk stamp.
    auto = next(r for r in rows if r.get("status") == "auto_approved")
    args = auto.get("args") or {}
    assert (args.get("_cm_risk") or {}).get("level") == "high"


def test_audit_classifies_legacy_rows_and_previews_hook_command():
    """Rows written before the classifier shipped still get a risk chip
    (classified at read time), and hook-receiver rows preview the COMMAND
    the human must judge, not the internal meta blob."""
    from routes.policy import _row_risk, _arg_preview
    legacy = {"id": "l", "action": "Bash: git push --force origin main",
              "args": {"command": "git push --force origin main"}}
    assert _row_risk(legacy)["level"] == "high"
    hook_args = {"source": "pretooluse-hook", "tool_name": "Bash",
                 "tool_input": {"command": "rm -rf /tmp/x"}, "cwd": "/tmp"}
    assert _arg_preview(hook_args) == "rm -rf /tmp/x"
    assert _row_risk({"id": "h", "action": "Bash: rm -rf /tmp/x",
                      "args": hook_args})["level"] == "high"
    # Nothing to classify → no chip, no crash.
    assert _row_risk({"id": "e", "action": "", "args": None}) is None
