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
