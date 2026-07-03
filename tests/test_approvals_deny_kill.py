"""Guard tests for the 2026-07-02 deny-kill enforcement gap.

Live repro: approval ``7d202307907a4f12bd8af5aa17c62c76`` was DENIED from the
mobile app, the daemon logged ``denied, killed=False``, and the claude_code
canary KEPT RUNNING. Root cause: ``approvals._kill_session`` only attempted
the OpenClaw gateway RPC (``sessions_kill``/...), which does not know
family-runtime sessions (ids like ``claude_code:UUID``), so a deny never
enforced anything for claude_code / codex / goose / opencode / aider.

The fix routes family-runtime denies through the SAME pid-based engine the
Stop button uses (``clawmetry/process_control.kill_session``), keeping the
gateway path for OpenClaw. These tests are revert-proof: on the pre-fix
code the process_control spy is never invoked and ``killed`` stays False.
"""

from __future__ import annotations

import os
import sys
import uuid

import pytest

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

import clawmetry.approvals as ap  # noqa: E402
import clawmetry.process_control as pc  # noqa: E402


_FAMILY_SID = "claude_code:11111111-2222-3333-4444-555555555555"
_BARE_SID = "11111111-2222-3333-4444-555555555555"


@pytest.fixture
def spies(monkeypatch):
    """Spy on both kill mechanisms; neither touches a real process or the
    network. ``raising=False`` keeps the fixture importable on pre-fix code
    (which lacks ``_gateway_kill_session``) so a revert shows up as a RED
    assertion, not a fixture error."""
    calls = {"pc": [], "gw": [], "gw_ret": False, "pc_ok": True}

    def _fake_pc_kill(runtime, session_id="", cwd="", mode="kill"):
        calls["pc"].append((runtime, session_id, cwd, mode))
        if calls["pc_ok"]:
            return {"ok": True, "action": "graceful_kill", "pid": 4242,
                    "runtime": runtime, "detail": "terminated"}
        return {"ok": False, "action": "graceful_kill", "pid": None,
                "runtime": runtime, "detail": "session_not_in_claude_map"}

    def _fake_gw_kill(session_id):
        calls["gw"].append(session_id)
        return calls["gw_ret"]

    monkeypatch.setattr(pc, "kill_session", _fake_pc_kill)
    monkeypatch.setattr(ap, "_gateway_kill_session", _fake_gw_kill,
                        raising=False)
    # Keep the cwd lookup away from any real DuckDB store.
    monkeypatch.setattr(ap, "_session_cwd_hint", lambda sid: "",
                        raising=False)
    return calls


# ── unit: _kill_session routing ───────────────────────────────────────────


def test_deny_kill_family_runtime_uses_process_control(spies):
    """BUG 1 GUARD: a family-runtime session id must route to the pid-based
    process_control kill (the Stop-button engine), with the runtime prefix
    stripped for the process-map lookup. Pre-fix code only tried the gateway
    and returned False."""
    assert ap._kill_session(_FAMILY_SID) is True
    assert spies["pc"] == [("claude_code", _BARE_SID, "", "kill")]
    # process_control succeeded, so the gateway is never consulted.
    assert spies["gw"] == []


def test_deny_kill_openclaw_still_uses_gateway(spies):
    """OpenClaw sessions (no family prefix) keep the historical gateway RPC
    path and never go near process_control."""
    spies["gw_ret"] = True
    assert ap._kill_session("bare-openclaw-session-uuid") is True
    assert spies["gw"] == ["bare-openclaw-session-uuid"]
    assert spies["pc"] == []


def test_deny_kill_family_failure_falls_back_then_fails_safe(spies):
    """If the pid kill cannot resolve the session, we try the gateway as a
    last resort and return False when neither works (the caller keeps the
    existing killed=False warning behaviour)."""
    spies["pc_ok"] = False
    assert ap._kill_session(_FAMILY_SID) is False
    assert len(spies["pc"]) == 1
    assert spies["gw"] == [_FAMILY_SID]


def test_deny_kill_codex_prefix_routes_to_process_control(spies):
    """The routing is runtime-generic (prefix-driven), not claude_code
    specific."""
    assert ap._kill_session("codex:abc-123") is True
    assert spies["pc"][0][0] == "codex"
    assert spies["pc"][0][1] == "abc-123"


def test_deny_kill_empty_session_is_noop(spies):
    assert ap._kill_session(None) is False
    assert ap._kill_session("") is False
    assert spies["pc"] == [] and spies["gw"] == []


# ── end to end: a DENIED approval on a family session enforces the kill ──


def test_denied_approval_kills_family_session(monkeypatch, spies):
    """Full ``process_tool_call`` flow with the cloud round-trip mocked to
    DENY: the result must report ``killed=True`` and the process_control spy
    must have fired for the family runtime. This is the exact live-repro
    shape (deny from the phone, claude_code session)."""
    monkeypatch.setattr(ap, "_post_approval_request", lambda *a, **k: {"ok": True})
    monkeypatch.setattr(ap, "_poll_decision", lambda *a, **k: "denied")

    # Keep DuckDB + the audit producer out of the unit.
    class _StoreStub:
        def ingest_approval(self, approval):
            pass

        def update_approval_decision(self, *a, **k):
            pass

    import clawmetry.local_store as _ls
    monkeypatch.setattr(_ls, "get_store", lambda *a, **k: _StoreStub())
    import clawmetry.audit as _audit
    monkeypatch.setattr(_audit, "audit_event", lambda *a, **k: None,
                        raising=False)

    policy = ap._compile_policy({
        "name": "deny-canary",
        "match": {"tool": "exec", "command_regex": r"rm\s+-rf"},
        "timeout": 1,
    })
    assert policy is not None

    result = ap.process_tool_call(
        api_key="test-key", node_id="node-1", session_id=_FAMILY_SID,
        tool_call_id=uuid.uuid4().hex, tool_name="Bash",
        args={"command": "rm -rf /tmp/canary"}, policies=[policy])

    assert result["decision"] == "denied"
    assert result["killed"] is True, (
        "denied family-runtime approval must actually kill the session "
        "(pre-fix: gateway-only path logged killed=False and the agent "
        "kept running)")
    assert spies["pc"] and spies["pc"][0][0] == "claude_code"
    assert spies["pc"][0][1] == _BARE_SID
