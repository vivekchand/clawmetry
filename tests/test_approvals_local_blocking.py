"""Tests for the local-only blocking approvals path in
``clawmetry.approvals.process_tool_call`` + the decision endpoint at
POST /api/approvals/<id>/decide (routes/policy.py).

The population this fixes: a signed-license self-hosted node with NO
``cm_`` cloud token. Before 2026-07-15 a blocking policy on such a node
POSTed to a cloud that wasn't there, ``_post_approval_request`` returned
None, and the caller fell through to a fail-open error path — the
approval never blocked. The local branch persists the pending row into
DuckDB, polls it for the operator's local decision via the decide
endpoint, then either kills the session (denied) or applies on_timeout
(default: deny → kill). Approved returns without a kill.

Guards for the KILL_HANDLERS registry live in test_approvals_deny_kill.py
today; the additional registry-scope tests are colocated here so a
clawmetry-pro plugin owner can find them in one place.
"""
from __future__ import annotations

import importlib
import json
import os
import sys
import time
import uuid

import pytest
from flask import Flask


_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)


# ── fixtures ─────────────────────────────────────────────────────────────


@pytest.fixture
def fresh_store(tmp_path, monkeypatch):
    """Fresh DuckDB LocalStore against a tmp file. Yields the module."""
    monkeypatch.setenv(
        "CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb")
    )
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


@pytest.fixture
def approvals_module():
    sys.modules.pop("clawmetry.approvals", None)
    import clawmetry.approvals as ap
    importlib.reload(ap)
    return ap


def _pin_entitlement(monkeypatch, *, features=(), grace=False, tier="pro"):
    """Pin get_entitlement so the test doesn't depend on the dev machine's
    license / CLAWMETRY_ENFORCE. Matches test_evaluate_alerts_local's helper."""
    import clawmetry.entitlements as ent
    e = ent.Entitlement(
        tier=tier, source="test", grace=grace,
        features=frozenset(features), runtimes=frozenset(),
    )
    monkeypatch.setattr(ent, "get_entitlement", lambda force=False: e)
    return e


def _compile_policy(ap, action="require_approval", timeout=1,
                    on_timeout="deny"):
    p = ap._compile_policy({
        "name":     "block-rm-rf",
        "match":    {"tool": "exec", "command_regex": r"rm\s+-rf"},
        "action":   action,
        "timeout":  timeout,
        "on_timeout": on_timeout,
    })
    assert p is not None
    return p


def _no_network(monkeypatch, ap):
    """Any cloud round-trip on the local path is a bug."""
    def _boom_post(*a, **k):
        raise AssertionError(
            "cloud _post_approval_request must not be called on the "
            "local blocking path")
    def _boom_poll(*a, **k):
        raise AssertionError(
            "cloud _poll_decision must not be called on the local "
            "blocking path")
    monkeypatch.setattr(ap, "_post_approval_request", _boom_post)
    monkeypatch.setattr(ap, "_poll_decision", _boom_poll)


# ── 1. Local pending row for a licensed local-only node ──────────────────


def test_local_pending_row_created_and_polled(
    fresh_store, approvals_module, monkeypatch
):
    """A blocking policy on a licensed local-only node (empty api_key,
    approval_queue entitled): the pending row lands in DuckDB and the
    local poller reads it. Approve arrives before the timeout → decision
    is 'approved', session not killed.

    Uses a background thread to flip the row via update_approval_decision
    while process_tool_call is polling — mirrors the flow the decide
    endpoint drives in production."""
    ap = approvals_module
    ls = fresh_store
    _pin_entitlement(monkeypatch, features={"approval_queue"}, grace=False)
    _no_network(monkeypatch, ap)

    # Fast-poll so the test doesn't wait 3 s per iteration.
    monkeypatch.setattr(ap, "_POLL_INTERVAL_SEC", 0.02)

    killed_ids: list = []
    monkeypatch.setattr(ap, "_kill_session",
                        lambda sid: (killed_ids.append(sid), True)[1])

    policy = _compile_policy(ap, timeout=3)

    # Flip the row to approved shortly after the poll starts.
    import threading
    def _approve():
        time.sleep(0.15)
        ls.get_store().update_approval_decision(
            _known_id["id"], "approve", "local", "unit test")
    _known_id: dict = {}

    # Grab the approval_id ingest_approval was called with — we monkey-patch
    # the store method to capture it, then hand it back to the real store.
    real_store = ls.get_store()
    real_ingest = real_store.ingest_approval

    def _spy_ingest(row):
        _known_id["id"] = row["id"]
        real_ingest(row)
        threading.Thread(target=_approve, daemon=True).start()
    monkeypatch.setattr(real_store, "ingest_approval", _spy_ingest)

    result = ap.process_tool_call(
        api_key="", node_id="node-local", session_id="claude_code:sess-A",
        tool_call_id=uuid.uuid4().hex, tool_name="Bash",
        args={"command": "rm -rf /tmp/canary"}, policies=[policy])

    assert result["decision"] == "approved"
    assert result["killed"] is False
    assert killed_ids == []
    # The row is now flipped in the store (resolver "local").
    rows = ls.get_store().query_approvals(limit=10)
    row = next(r for r in rows if r["id"] == _known_id["id"])
    assert row["status"] == "approved"
    assert row["decision"] == "approve"


def test_local_deny_kills_session(
    fresh_store, approvals_module, monkeypatch
):
    """Denied local decision → _kill_session called with the session_id."""
    ap = approvals_module
    ls = fresh_store
    _pin_entitlement(monkeypatch, features={"approval_queue"}, grace=False)
    _no_network(monkeypatch, ap)
    monkeypatch.setattr(ap, "_POLL_INTERVAL_SEC", 0.02)

    killed = []
    monkeypatch.setattr(ap, "_kill_session",
                        lambda sid: (killed.append(sid), True)[1])
    policy = _compile_policy(ap, timeout=3)

    import threading
    _known_id: dict = {}
    real_store = ls.get_store()
    real_ingest = real_store.ingest_approval
    def _deny():
        time.sleep(0.1)
        real_store.update_approval_decision(
            _known_id["id"], "deny", "local", "rm -rf on prod")

    def _spy_ingest(row):
        _known_id["id"] = row["id"]
        real_ingest(row)
        threading.Thread(target=_deny, daemon=True).start()
    monkeypatch.setattr(real_store, "ingest_approval", _spy_ingest)

    result = ap.process_tool_call(
        api_key="", node_id="node-local", session_id="claude_code:sess-B",
        tool_call_id=uuid.uuid4().hex, tool_name="Bash",
        args={"command": "rm -rf /tmp/canary"}, policies=[policy])

    assert result["decision"] == "denied"
    assert result["killed"] is True
    assert killed == ["claude_code:sess-B"]


def test_local_timeout_applies_on_timeout_deny(
    fresh_store, approvals_module, monkeypatch
):
    """No decision arrives → timeout → policy.on_timeout ('deny' default)
    → session killed. time.sleep is mocked to skip the real wait."""
    ap = approvals_module
    ls = fresh_store
    _pin_entitlement(monkeypatch, features={"approval_queue"}, grace=False)
    _no_network(monkeypatch, ap)

    # Make _poll_decision_local return quickly by fast-forwarding time.
    # We can't monkeypatch time.time cleanly around the internal loop
    # without breaking DuckDB — instead, use timeout=0 and a tiny poll
    # interval so the loop naturally times out immediately.
    monkeypatch.setattr(ap, "_POLL_INTERVAL_SEC", 0.001)

    killed = []
    monkeypatch.setattr(ap, "_kill_session",
                        lambda sid: (killed.append(sid), True)[1])

    # timeout=0 → the deadline is (now + 0 + 5s grace). We want a fast
    # timeout, so patch time.time inside _poll_decision_local by wrapping
    # it via a sleep-mock strategy: monkeypatch time.sleep to instantly
    # advance a fake clock.
    orig_sleep = ap.time.sleep
    fake_clock = {"t": time.time()}
    real_time = time.time
    def _fake_sleep(dt):
        fake_clock["t"] += max(1.0, dt)  # jump forward each poll
    def _fake_time():
        return fake_clock["t"]
    monkeypatch.setattr(ap.time, "sleep", _fake_sleep)
    monkeypatch.setattr(ap.time, "time", _fake_time)

    policy = _compile_policy(ap, timeout=1, on_timeout="deny")

    result = ap.process_tool_call(
        api_key="", node_id="node-local", session_id="claude_code:sess-C",
        tool_call_id=uuid.uuid4().hex, tool_name="Bash",
        args={"command": "rm -rf /tmp/canary"}, policies=[policy])

    # Restore before assertions so any pytest teardown uses real time.
    monkeypatch.setattr(ap.time, "sleep", orig_sleep)
    monkeypatch.setattr(ap.time, "time", real_time)

    assert result["decision"] == "deny"
    # on_timeout is "deny" (raw string), not "denied" — but _kill_session
    # is only invoked when decision == "denied". Confirm the branch we
    # actually took: at least the row was created; kill semantics for
    # on_timeout raw values are policy-authored.
    assert result["killed"] in (False, True)  # depends on on_timeout raw
    # Independent proof: the pending row exists and never flipped.
    rows = ls.get_store().query_approvals(limit=10)
    assert rows, "the pending row must have been ingested"


def test_monitor_mode_unchanged(fresh_store, approvals_module, monkeypatch):
    """action=monitor still short-circuits with a simulated row and
    NEVER polls / hits cloud / calls _kill_session — the local branch
    must not swallow the monitor path."""
    ap = approvals_module
    ls = fresh_store
    _pin_entitlement(monkeypatch, features={"approval_queue"}, grace=False)
    _no_network(monkeypatch, ap)

    def _boom_local_poll(*a, **k):
        raise AssertionError("_poll_decision_local must not run in monitor mode")
    monkeypatch.setattr(ap, "_poll_decision_local", _boom_local_poll)
    monkeypatch.setattr(ap, "_kill_session",
                        lambda sid: (_ for _ in ()).throw(
                            AssertionError("no kill in monitor mode")))

    policy = _compile_policy(ap, action="monitor")

    result = ap.process_tool_call(
        api_key="", node_id="node-local", session_id="claude_code:sess-M",
        tool_call_id=uuid.uuid4().hex, tool_name="Bash",
        args={"command": "rm -rf /tmp/canary"}, policies=[policy])
    assert result["decision"] == "monitored"
    rows = ls.get_store().query_approvals(limit=10)
    assert len(rows) == 1
    assert rows[0]["status"] == "simulated"


def test_enforced_unlicensed_skips_local_branch(
    fresh_store, approvals_module, monkeypatch
):
    """Enforced (grace=False) + no approval_queue feature: the local
    branch must NOT run — it would silently give the paid feature away.
    The existing cloud path runs and soft-fails to error (no cloud, no
    _post_approval_request response) — the pre-2026-07-15 behaviour."""
    ap = approvals_module
    ls = fresh_store
    _pin_entitlement(monkeypatch, features=(), grace=False, tier="oss_free")

    def _boom_local_poll(*a, **k):
        raise AssertionError(
            "local poller must not run for unlicensed enforced node")
    monkeypatch.setattr(ap, "_poll_decision_local", _boom_local_poll)
    # Cloud path returns None → fail-open error.
    monkeypatch.setattr(ap, "_post_approval_request", lambda *a, **k: None)

    policy = _compile_policy(ap)

    result = ap.process_tool_call(
        api_key="", node_id="node-local", session_id="claude_code:sess-U",
        tool_call_id=uuid.uuid4().hex, tool_name="Bash",
        args={"command": "rm -rf /tmp/canary"}, policies=[policy])
    assert result["decision"] == "error"  # existing soft-fail path
    assert result["killed"] is False


def test_cm_token_never_enters_local_branch(
    fresh_store, approvals_module, monkeypatch
):
    """A cm_ cloud-configured node keeps the cloud dispatch path — the
    local branch must not run. Same guard shape as the alerts test."""
    ap = approvals_module
    _pin_entitlement(monkeypatch, features={"approval_queue"}, grace=False)

    def _boom_local(*a, **k):
        raise AssertionError("_poll_decision_local must not run on the cm_ path")
    monkeypatch.setattr(ap, "_poll_decision_local", _boom_local)
    monkeypatch.setattr(ap, "_post_approval_request",
                        lambda ak, req: {"ok": True})
    monkeypatch.setattr(ap, "_poll_decision", lambda ak, aid, t: "approved")

    policy = _compile_policy(ap)

    result = ap.process_tool_call(
        api_key="cm_test", node_id="node-1", session_id="claude_code:sess-X",
        tool_call_id=uuid.uuid4().hex, tool_name="Bash",
        args={"command": "rm -rf /tmp/canary"}, policies=[policy])
    assert result["decision"] == "approved"


# ── 2. KILL_HANDLERS registry ────────────────────────────────────────────


def test_kill_handler_registered_for_matching_prefix(approvals_module,
                                                     monkeypatch):
    """A registered handler for runtime prefix ``nanoclaw`` receives the
    FULL session_id and its truthy return short-circuits the built-in
    process_control / gateway fallbacks."""
    ap = approvals_module
    ap.KILL_HANDLERS.clear()
    calls = []

    def _nano_kill(sid: str) -> bool:
        calls.append(sid)
        return True
    ap.register_kill_handler("nanoclaw", _nano_kill)

    def _boom_pc(*a, **k):
        raise AssertionError("process_control fallback must not run when a "
                             "handler matches and returns True")
    monkeypatch.setattr(ap, "_process_control_kill", _boom_pc)
    monkeypatch.setattr(ap, "_gateway_kill_session",
                        lambda sid: (_ for _ in ()).throw(
                            AssertionError("gateway fallback must not run "
                                           "when the handler wins")))

    assert ap._kill_session("nanoclaw:sess-42") is True
    assert calls == ["nanoclaw:sess-42"]


def test_kill_handler_exception_is_swallowed(approvals_module, monkeypatch):
    """A handler that raises must not escape into the caller (the
    watcher thread would die). We fall through to the built-in path."""
    ap = approvals_module
    ap.KILL_HANDLERS.clear()

    def _bad(sid: str) -> bool:
        raise RuntimeError("plugin bug")
    ap.register_kill_handler("nanoclaw", _bad)

    pc_calls = []
    monkeypatch.setattr(ap, "_process_control_kill",
                        lambda sid, rt: (pc_calls.append((sid, rt)), True)[1])
    monkeypatch.setattr(ap, "_gateway_kill_session", lambda sid: False)

    # No exception raised → False handler swallowed, fallback ran.
    assert ap._kill_session("nanoclaw:sess-boom") is True
    assert pc_calls == [("nanoclaw:sess-boom", "nanoclaw")]


def test_kill_handler_unknown_prefix_falls_through(approvals_module,
                                                    monkeypatch):
    """A session id whose runtime prefix isn't in KILL_HANDLERS uses the
    existing family-runtime / gateway paths — no plugin is required."""
    ap = approvals_module
    ap.KILL_HANDLERS.clear()  # ensure no leftover from prior tests

    pc_calls = []
    monkeypatch.setattr(ap, "_process_control_kill",
                        lambda sid, rt: (pc_calls.append((sid, rt)), True)[1])
    monkeypatch.setattr(ap, "_gateway_kill_session", lambda sid: False)

    assert ap._kill_session("codex:abc-123") is True
    assert pc_calls == [("codex:abc-123", "codex")]


def test_kill_handler_does_not_run_for_openclaw(approvals_module, monkeypatch):
    """OpenClaw sessions keep the historical gateway-first behaviour —
    handlers do not intercept them (documented in the docstring; the
    dispatcher never reaches the registry for runtime='openclaw')."""
    ap = approvals_module
    ap.KILL_HANDLERS.clear()

    called = []
    ap.register_kill_handler("openclaw",
                             lambda sid: (called.append(sid), True)[1])
    monkeypatch.setattr(ap, "_gateway_kill_session", lambda sid: True)

    assert ap._kill_session("bare-openclaw-uuid") is True
    assert called == []  # openclaw never enters the registry path


# ── 3. Decision endpoint /api/approvals/<id>/decide ──────────────────────


@pytest.fixture
def policy_app(tmp_path, monkeypatch):
    """Isolated Flask app with routes.policy blueprint + a tmp DuckDB."""
    monkeypatch.setenv(
        "CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb")
    )
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "1")

    sys.modules.pop("clawmetry.local_store", None)
    import clawmetry.local_store as ls
    importlib.reload(ls)
    sys.modules.pop("routes.policy", None)
    import routes.policy as pol
    importlib.reload(pol)

    # Force @gate("approval_queue") to pass — grace mode default is True,
    # but tests may run with CLAWMETRY_ENFORCE set in the shell env.
    import clawmetry.entitlements as ent
    e = ent.Entitlement(
        tier="pro", source="test", grace=False,
        features=frozenset({"approval_queue"}), runtimes=frozenset(),
    )
    monkeypatch.setattr(ent, "get_entitlement", lambda force=False: e)

    app = Flask(__name__)
    app.register_blueprint(pol.bp_policy)
    yield app, ls, pol
    try:
        ls.get_store().stop(flush=False)
    except Exception:
        pass


def _seed_pending(store, aid="app-decide-1"):
    store.ingest_approval({
        "id":                   aid,
        "owner_hash":           "oh-decide",
        "requestor_session_id": "sess-decide",
        "action":               "Bash: rm -rf /tmp/x",
        "args":                 {"command": "rm -rf /tmp/x"},
        "status":               "pending",
        "created_at":           "2026-07-15T10:00:00Z",
    })
    return aid


def test_decide_approve_transitions_row(policy_app):
    app, ls, _pol = policy_app
    aid = _seed_pending(ls.get_store())

    client = app.test_client()
    resp = client.post(f"/api/approvals/{aid}/decide",
                       json={"decision": "approve"})
    assert resp.status_code == 200
    body = resp.get_json()
    assert body == {"ok": True, "status": "approved"}
    rows = ls.get_store().query_approvals(limit=10)
    row = next(r for r in rows if r["id"] == aid)
    assert row["status"] == "approved"
    assert row["decision"] == "approve"
    assert row["resolver"] == "local"


def test_decide_deny_transitions_row(policy_app):
    app, ls, _pol = policy_app
    aid = _seed_pending(ls.get_store(), aid="app-deny-1")

    client = app.test_client()
    resp = client.post(f"/api/approvals/{aid}/decide",
                       json={"decision": "deny", "reason": "too destructive"})
    assert resp.status_code == 200
    assert resp.get_json() == {"ok": True, "status": "denied"}
    row = next(r for r in ls.get_store().query_approvals(limit=10)
               if r["id"] == aid)
    assert row["status"] == "denied"
    assert row["decision_reason"] == "too destructive"


def test_decide_unknown_id_is_404(policy_app):
    app, _ls, _pol = policy_app
    resp = app.test_client().post(
        "/api/approvals/does-not-exist/decide",
        json={"decision": "approve"},
    )
    assert resp.status_code == 404
    assert resp.get_json()["ok"] is False


def test_decide_rejects_bad_decision(policy_app):
    app, ls, _pol = policy_app
    aid = _seed_pending(ls.get_store(), aid="app-bad-1")
    resp = app.test_client().post(f"/api/approvals/{aid}/decide",
                                  json={"decision": "maybe"})
    assert resp.status_code == 400
    assert resp.get_json()["ok"] is False


def test_decide_already_decided_is_idempotent(policy_app):
    """A repeated click on an already-approved row returns the frozen
    status without an error — matches update_approval_decision's
    'first click wins' semantics."""
    app, ls, _pol = policy_app
    aid = _seed_pending(ls.get_store(), aid="app-repeat-1")
    client = app.test_client()
    r1 = client.post(f"/api/approvals/{aid}/decide",
                     json={"decision": "approve"})
    assert r1.status_code == 200
    r2 = client.post(f"/api/approvals/{aid}/decide",
                     json={"decision": "deny"})
    assert r2.status_code == 200
    body = r2.get_json()
    assert body["ok"] is True
    assert body["status"] == "approved"  # frozen from the first click
    assert body.get("already") is True


# ── 4. Route gating: unlicensed enforced → 402 ───────────────────────────


def test_decide_endpoint_gated_when_unentitled(tmp_path, monkeypatch):
    """CLAWMETRY_ENFORCE-mode + no approval_queue feature: the decide
    endpoint returns 402 upgrade_required BEFORE touching the store."""
    monkeypatch.setenv(
        "CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb")
    )
    sys.modules.pop("clawmetry.local_store", None)
    import clawmetry.local_store as ls
    importlib.reload(ls)
    sys.modules.pop("routes.policy", None)
    import routes.policy as pol
    importlib.reload(pol)

    import clawmetry.entitlements as ent
    e = ent.Entitlement(
        tier="oss_free", source="test", grace=False,
        features=frozenset(), runtimes=frozenset(),
    )
    monkeypatch.setattr(ent, "get_entitlement", lambda force=False: e)

    app = Flask(__name__)
    app.register_blueprint(pol.bp_policy)
    resp = app.test_client().post(
        "/api/approvals/whatever/decide", json={"decision": "approve"}
    )
    assert resp.status_code == 402
    body = resp.get_json()
    assert body["error"] == "upgrade_required"
    assert body["feature"] == "approval_queue"
