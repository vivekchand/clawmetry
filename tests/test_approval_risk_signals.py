"""Tests for inline risk signals on the live/audit approval queues.

Context: a Register/Wiz write-up (2026-08-06, "humans in the loop miss a
third of dangerous AI coding agent requests") analysed ~409k human
approve/deny decisions on simulated AI-agent tool calls and found reviewers
approve roughly 1 in 3 malicious ones — worst on commands that *look*
familiar (npm run scripts) or where the shown target hides the real one
(a related GhostApproval write-up on the same theme). The report's
prescription is layered technical defenses, not more reliance on human
judgment alone.

ClawMetry already had two disconnected pieces relevant to this: a
retrospective threat-signature scanner (dashboard._THREAT_SIGNATURES /
_scan_events_for_threats, Security tab) and a live human-approval queue
(routes/policy.py + routes/hooks.py's PreToolUse gate). This closes the
gap by scoring each pending/decided approval row against the SAME
signature table and attaching the hit as ``risk_signals`` — so the warning
reaches a reviewer at the moment they're about to click Approve, not only
after the fact in a separate tab.

These are hermetic unit tests: no DuckDB, no daemon. ``_ls_call`` is
monkeypatched to return synthetic rows, mirroring the pattern in
``tests/test_tool_policy_route_gate.py``.
"""
from __future__ import annotations

import importlib
import os
import sys

import pytest
from flask import Flask

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)


# ── fixtures ─────────────────────────────────────────────────────────────


@pytest.fixture
def grace(monkeypatch, tmp_path):
    """Default grace mode — approval_queue (a Starter feature) passes
    through so the handler body actually runs."""
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    yield e
    e.invalidate()


def _make_app():
    from routes.policy import bp_policy

    app = Flask(__name__)
    app.register_blueprint(bp_policy)
    return app


# ── _arg_preview: nested tool_input lookup ─────────────────────────────────


def test_arg_preview_reads_top_level_command():
    from routes.policy import _arg_preview

    assert _arg_preview({"command": "rm -rf /etc/nginx"}) == "rm -rf /etc/nginx"


def test_arg_preview_reads_nested_tool_input_command():
    """The PreToolUse hook (routes/hooks.py) stores the actual command one
    level down, under ``tool_input`` — without this the preview silently
    fell back to a raw JSON dump of the whole args blob for every
    Claude-Code-originated approval row."""
    from routes.policy import _arg_preview

    args = {
        "source": "pretooluse-hook",
        "runtime": "claude_code",
        "tool_name": "Bash",
        "tool_input": {"command": "npm run analyze"},
        "cwd": "/home/dev/project",
    }
    assert _arg_preview(args) == "npm run analyze"


def test_arg_preview_nested_file_path():
    from routes.policy import _arg_preview

    args = {"tool_input": {"file_path": "/home/dev/.ssh/authorized_keys"}}
    assert _arg_preview(args) == "/home/dev/.ssh/authorized_keys"


def test_arg_preview_falls_back_to_json_when_nothing_matches():
    from routes.policy import _arg_preview

    assert _arg_preview({"foo": "bar"}) == '{"foo":"bar"}'


def test_arg_preview_none_and_non_dict():
    from routes.policy import _arg_preview

    assert _arg_preview(None) == ""
    assert _arg_preview("raw string") == "raw string"


# ── _risk_signals: delegates to dashboard's threat-signature engine ───────


def test_risk_signals_flags_known_pattern():
    from routes.policy import _risk_signals

    signals = _risk_signals("npm run deploy")
    assert signals and signals[0]["rule_id"] == "SEC-017"


def test_risk_signals_empty_for_clean_command():
    from routes.policy import _risk_signals

    assert _risk_signals("echo hello") == []


def test_risk_signals_empty_text_never_raises():
    from routes.policy import _risk_signals

    assert _risk_signals("") == []
    assert _risk_signals(None) == []


def test_risk_signals_survives_dashboard_import_failure(monkeypatch):
    """Defensive contract matching the rest of routes/policy.py: a broken
    or missing engine degrades to no signals, never a 500."""
    import routes.policy as P

    real_import = __import__

    def _broken_import(name, *a, **kw):
        if name == "dashboard":
            raise ImportError("boom")
        return real_import(name, *a, **kw)

    monkeypatch.setattr("builtins.__import__", _broken_import)
    assert P._risk_signals("npm run deploy") == []


# ── /api/approvals-audit: risk_signals on each decision + flagged rollup ──


def test_approvals_audit_attaches_risk_signals(grace, monkeypatch):
    def _canned(name, **_kw):
        assert name == "query_approvals"
        return [
            {
                "id": "a1",
                "action": "Bash: npm run analyze",
                "args": {"tool_input": {"command": "npm run analyze"}},
                "status": "pending",
                "requestor_session_id": "claude_code:sess-1",
                "created_at": "2026-08-08T00:00:00Z",
            },
            {
                "id": "a2",
                "action": "Bash: echo hello",
                "args": {"tool_input": {"command": "echo hello"}},
                "status": "approved",
                "decision": "approve",
                "requestor_session_id": "claude_code:sess-1",
                "created_at": "2026-08-08T00:00:01Z",
            },
        ]

    import routes.policy as P
    monkeypatch.setattr(P, "_ls_call", _canned)

    app = _make_app()
    with app.test_client() as c:
        r = c.get("/api/approvals-audit")
        assert r.status_code == 200
        body = r.get_json()
        by_id = {d["id"]: d for d in body["decisions"]}
        assert by_id["a1"]["risk_signals"]
        assert by_id["a1"]["risk_signals"][0]["rule_id"] == "SEC-017"
        assert by_id["a2"]["risk_signals"] == []
        # Coarse rollup: exactly one of the two decisions carries a signal.
        assert body["summary"]["flagged"] == 1


def test_approvals_audit_flagged_zero_when_nothing_matches(grace, monkeypatch):
    def _canned(name, **_kw):
        return [{"id": "a1", "action": "Bash: echo hi",
                 "args": {"tool_input": {"command": "echo hi"}},
                 "status": "approved", "decision": "approve"}]

    import routes.policy as P
    monkeypatch.setattr(P, "_ls_call", _canned)

    app = _make_app()
    with app.test_client() as c:
        body = c.get("/api/approvals-audit").get_json()
        assert body["summary"]["flagged"] == 0


# ── /api/approvals: risk_signals on the pending queue ──────────────────────


def test_approvals_queue_attaches_risk_signals(grace, monkeypatch):
    def _canned(name, **kwargs):
        assert kwargs.get("status") == "pending"
        return [{
            "id": "a1",
            "action": "Bash: git config core.hooksPath /tmp/evil",
            "args": {"tool_input": {"command": "git config core.hooksPath /tmp/evil"}},
            "status": "pending",
            "requestor_session_id": "claude_code:sess-1",
            "created_at": "2026-08-08T00:00:00Z",
        }]

    import routes.policy as P
    monkeypatch.setattr(P, "_ls_call", _canned)

    app = _make_app()
    with app.test_client() as c:
        r = c.get("/api/approvals")
        assert r.status_code == 200
        approvals = r.get_json()["approvals"]
        assert len(approvals) == 1
        assert approvals[0]["risk_signals"][0]["rule_id"] == "SEC-018"


def test_approvals_queue_empty_risk_signals_for_clean_row(grace, monkeypatch):
    def _canned(name, **_kw):
        return [{"id": "a1", "action": "Bash: ls -la",
                 "args": {"tool_input": {"command": "ls -la"}},
                 "status": "pending"}]

    import routes.policy as P
    monkeypatch.setattr(P, "_ls_call", _canned)

    app = _make_app()
    with app.test_client() as c:
        approvals = c.get("/api/approvals").get_json()["approvals"]
        assert approvals[0]["risk_signals"] == []


# ── SEC-019 / structural symlink-escape detection (GhostApproval) ─────────
# A Wiz write-up (2026-08, same theme as the Register game-study coverage)
# found six AI coding assistants shared a pattern: a pre-planted symlink at
# a plausible path silently redirects a Write/Edit outside the workspace
# while the approval dialog shows only the harmless literal path. The
# check lives in routes/hooks.py because it needs real filesystem access
# to the literal path at approval time; routes/policy.py's
# _combined_risk_signals merges the result into risk_signals.


def test_symlink_escape_detected_for_write_tool(tmp_path):
    from routes.hooks import _symlink_escape_signal

    workspace = tmp_path / "workspace"
    workspace.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    target = outside / "authorized_keys"
    target.write_text("ssh-rsa ...")
    link = workspace / "notes.txt"
    link.symlink_to(target)

    sig = _symlink_escape_signal("Write", {"file_path": "notes.txt"}, str(workspace))
    assert sig is not None
    assert sig["rule_id"] == "SEC-019"
    assert sig["severity"] == "critical"
    assert "notes.txt" in sig["description"]


def test_symlink_inside_workspace_is_not_flagged(tmp_path):
    from routes.hooks import _symlink_escape_signal

    workspace = tmp_path / "workspace"
    workspace.mkdir()
    real = workspace / "real.txt"
    real.write_text("x")
    alias = workspace / "alias.txt"
    alias.symlink_to(real)

    assert _symlink_escape_signal("Write", {"file_path": "alias.txt"}, str(workspace)) is None


def test_symlink_check_no_signal_when_no_symlink(tmp_path):
    from routes.hooks import _symlink_escape_signal

    workspace = tmp_path / "workspace"
    workspace.mkdir()
    assert _symlink_escape_signal(
        "Write", {"file_path": "brand_new_file.txt"}, str(workspace)
    ) is None


def test_symlink_check_ignores_non_write_tools(tmp_path):
    from routes.hooks import _symlink_escape_signal

    assert _symlink_escape_signal("Bash", {"command": "npm run analyze"}, str(tmp_path)) is None
    assert _symlink_escape_signal("Read", {"file_path": "/etc/passwd"}, str(tmp_path)) is None


def test_symlink_check_never_raises_on_missing_cwd():
    from routes.hooks import _symlink_escape_signal

    assert _symlink_escape_signal("Write", {"file_path": "x.txt"}, "") is None
    assert _symlink_escape_signal("Write", {}, "/tmp") is None
    assert _symlink_escape_signal("Write", None, "/tmp") is None


def test_combined_risk_signals_merges_structural_and_textual():
    """routes/policy.py's _combined_risk_signals must surface BOTH the
    structural symlink signal stashed by routes/hooks.py and any
    text-pattern match, structural first (real filesystem evidence, not
    just regex on a string)."""
    from routes.policy import _combined_risk_signals

    row = {
        "action": "Write: notes.txt",
        "args": {
            "tool_input": {"file_path": "notes.txt"},
            "structural_risk_signals": [
                {"rule_id": "SEC-019", "severity": "critical",
                 "description": "symlink escape"},
            ],
        },
    }
    signals = _combined_risk_signals(row)
    assert signals[0]["rule_id"] == "SEC-019"


def test_combined_risk_signals_handles_missing_structural_key():
    from routes.policy import _combined_risk_signals

    row = {"action": "Bash: echo hi", "args": {"tool_input": {"command": "echo hi"}}}
    assert _combined_risk_signals(row) == []


def test_combined_risk_signals_never_raises_on_garbage_row():
    from routes.policy import _combined_risk_signals

    assert _combined_risk_signals({}) == []
    assert _combined_risk_signals({"args": "not a dict"}) == []


def test_approvals_audit_surfaces_symlink_signal_end_to_end(grace, monkeypatch):
    """The hooks.py -> policy.py wiring: a row carrying
    structural_risk_signals (as routes/hooks.py would store it) shows up
    in /api/approvals-audit's risk_signals."""
    def _canned(name, **_kw):
        return [{
            "id": "a1",
            "action": "Write: notes.txt",
            "args": {
                "tool_input": {"file_path": "notes.txt"},
                "structural_risk_signals": [
                    {"rule_id": "SEC-019", "severity": "critical",
                     "description": "Write target resolves outside the workspace"},
                ],
            },
            "status": "pending",
        }]

    import routes.policy as P
    monkeypatch.setattr(P, "_ls_call", _canned)

    app = _make_app()
    with app.test_client() as c:
        body = c.get("/api/approvals-audit").get_json()
        assert body["decisions"][0]["risk_signals"][0]["rule_id"] == "SEC-019"
        assert body["summary"]["flagged"] == 1


# ── permission-fatigue summary ──────────────────────────────────────────────


def test_fatigue_flags_rapid_decisions():
    from routes.policy import _fatigue_summary

    decisions = [
        {"status": "approved", "resolved_at": "2026-08-08T00:00:00Z"},
        {"status": "approved", "resolved_at": "2026-08-08T00:00:02Z"},
        {"status": "denied", "resolved_at": "2026-08-08T00:00:04Z"},
        {"status": "approved", "resolved_at": "2026-08-08T00:00:06Z"},
    ]
    fatigue = _fatigue_summary(decisions)
    assert fatigue["rapid"] is True
    assert fatigue["recent_count"] == 4
    assert fatigue["avg_interval_s"] == 2.0


def test_fatigue_not_flagged_for_slow_decisions():
    from routes.policy import _fatigue_summary

    decisions = [
        {"status": "approved", "resolved_at": "2026-08-08T00:00:00Z"},
        {"status": "approved", "resolved_at": "2026-08-08T00:01:00Z"},
        {"status": "approved", "resolved_at": "2026-08-08T00:02:00Z"},
    ]
    fatigue = _fatigue_summary(decisions)
    assert fatigue["rapid"] is False


def test_fatigue_needs_minimum_sample():
    from routes.policy import _fatigue_summary

    decisions = [
        {"status": "approved", "resolved_at": "2026-08-08T00:00:00Z"},
        {"status": "approved", "resolved_at": "2026-08-08T00:00:01Z"},
    ]
    fatigue = _fatigue_summary(decisions)
    assert fatigue["rapid"] is False
    assert fatigue["recent_count"] == 2
    assert fatigue["avg_interval_s"] is None


def test_fatigue_ignores_pending_rows():
    from routes.policy import _fatigue_summary

    decisions = [
        {"status": "pending", "created_at": "2026-08-08T00:00:00Z"},
        {"status": "pending", "created_at": "2026-08-08T00:00:01Z"},
        {"status": "pending", "created_at": "2026-08-08T00:00:02Z"},
    ]
    assert _fatigue_summary(decisions) == {
        "rapid": False, "recent_count": 0, "avg_interval_s": None,
    }


def test_fatigue_empty_input_never_raises():
    from routes.policy import _fatigue_summary

    assert _fatigue_summary([]) == {"rapid": False, "recent_count": 0, "avg_interval_s": None}


def test_approvals_audit_includes_fatigue_in_summary(grace, monkeypatch):
    def _canned(name, **_kw):
        return [
            {"id": f"a{i}", "action": "Bash: echo hi",
             "args": {"tool_input": {"command": "echo hi"}},
             "status": "approved", "decision": "approve",
             "resolved_at": f"2026-08-08T00:00:0{i}Z"}
            for i in range(4)
        ]

    import routes.policy as P
    monkeypatch.setattr(P, "_ls_call", _canned)

    app = _make_app()
    with app.test_client() as c:
        body = c.get("/api/approvals-audit").get_json()
        assert "fatigue" in body["summary"]
        assert body["summary"]["fatigue"]["rapid"] is True


# ── second-pair-of-eyes webhook notification on a flagged approval ─────────


def test_notify_risky_approval_dispatches_alert_for_flagged_row(monkeypatch):
    from routes.policy import _notify_risky_approval
    import dashboard as _d

    calls = []

    def _fake_dispatch(title, message, severity="warning", alert_type=None):
        calls.append({"title": title, "message": message,
                      "severity": severity, "alert_type": alert_type})

    # Patch only _dispatch_alert on the REAL module — _notify_risky_approval
    # also calls _combined_risk_signals -> _risk_signals -> dashboard.
    # _threat_signals_for_text internally, so swapping the whole module for
    # a stub (as opposed to one attribute) would silently break risk
    # detection too and this test would pass for the wrong reason.
    monkeypatch.setattr(_d, "_dispatch_alert", _fake_dispatch)

    row = {
        "action": "Bash: npm run analyze",
        "args": {"tool_input": {"command": "npm run analyze"}},
        "requestor_session_id": "claude_code:sess-1",
    }
    _notify_risky_approval(row, "approval-123")

    assert len(calls) == 1
    assert calls[0]["alert_type"] == "risky_approval_approved"
    assert "SEC-017" in calls[0]["title"]
    assert "npm run analyze" in calls[0]["message"]


def test_notify_risky_approval_silent_for_clean_row(monkeypatch):
    from routes.policy import _notify_risky_approval
    import dashboard as _d

    calls = []
    monkeypatch.setattr(_d, "_dispatch_alert", lambda *a, **kw: calls.append((a, kw)))

    row = {"action": "Bash: echo hi", "args": {"tool_input": {"command": "echo hi"}}}
    _notify_risky_approval(row, "approval-456")
    assert calls == []


def test_notify_risky_approval_never_raises_when_dashboard_broken(monkeypatch):
    from routes.policy import _notify_risky_approval

    real_import = __import__

    def _broken_import(name, *a, **kw):
        if name == "dashboard":
            raise ImportError("boom")
        return real_import(name, *a, **kw)

    monkeypatch.setattr("builtins.__import__", _broken_import)
    row = {"action": "Bash: npm run analyze",
           "args": {"tool_input": {"command": "npm run analyze"}}}
    # Must not raise.
    _notify_risky_approval(row, "approval-789")


def test_approval_decide_fires_notification_on_risky_approve(grace, monkeypatch, tmp_path):
    """End-to-end through the route: approving a flagged pending row calls
    _notify_risky_approval exactly once; denying (or approving a clean
    row) must not."""
    import routes.policy as P

    def _canned(name, **_kw):
        if name == "query_approvals":
            return [{
                "id": "a1", "status": "pending",
                "action": "Bash: npm run analyze",
                "args": {"tool_input": {"command": "npm run analyze"}},
            }]
        return None

    monkeypatch.setattr(P, "_ls_call", _canned)
    monkeypatch.setattr("routes.local_query.local_store_via_daemon",
                        lambda *a, **kw: True, raising=False)

    notified = []
    monkeypatch.setattr(P, "_notify_risky_approval",
                        lambda row, aid: notified.append(aid))

    app = _make_app()
    with app.test_client() as c:
        r = c.post("/api/approvals/a1/decide", json={"decision": "approve"})
        assert r.status_code == 200
        assert r.get_json()["status"] == "approved"
    assert notified == ["a1"]


def test_approval_decide_no_notification_on_deny(grace, monkeypatch):
    import routes.policy as P

    def _canned(name, **_kw):
        if name == "query_approvals":
            return [{
                "id": "a1", "status": "pending",
                "action": "Bash: npm run analyze",
                "args": {"tool_input": {"command": "npm run analyze"}},
            }]
        return None

    monkeypatch.setattr(P, "_ls_call", _canned)
    monkeypatch.setattr("routes.local_query.local_store_via_daemon",
                        lambda *a, **kw: True, raising=False)

    notified = []
    monkeypatch.setattr(P, "_notify_risky_approval",
                        lambda row, aid: notified.append(aid))

    app = _make_app()
    with app.test_client() as c:
        r = c.post("/api/approvals/a1/decide", json={"decision": "deny"})
        assert r.status_code == 200
    assert notified == []
