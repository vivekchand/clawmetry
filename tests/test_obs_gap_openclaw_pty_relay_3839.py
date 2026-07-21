"""Regression tests for issue #3839.

OpenClaw PR #107335 ('macOS paired-node terminals') and PR #107086 ('Control UI
catalog terminals') add PTY relay state, a validated resume command, a
viewer-vs-terminal preference, and a paired-node identity to gateway session
records.  Before this fix, OpenClawAdapter.list_sessions() dropped all four
fields so they never appeared in the unified Session shape.
"""

import clawmetry.adapters.openclaw as ocmod
from clawmetry.adapters.openclaw import OpenClawAdapter


class _FakeDash:
    def __init__(self, extra_fields=None):
        self._fields = extra_fields or {}

    def _get_sessions(self):
        record = {"sessionId": "sess-pty"}
        record.update(self._fields)
        return [record]


def test_list_sessions_captures_pty_relay_state(monkeypatch):
    monkeypatch.setattr(ocmod, "_d", lambda: _FakeDash({"ptyRelayState": "active"}))
    sessions = OpenClawAdapter().list_sessions(limit=10)
    assert sessions[0].extra.get("ptyRelayState") == "active", (
        "list_sessions() must surface ptyRelayState in extra"
    )


def test_list_sessions_captures_pty_relay_alias(monkeypatch):
    monkeypatch.setattr(ocmod, "_d", lambda: _FakeDash({"ptyRelay": "inactive"}))
    sessions = OpenClawAdapter().list_sessions(limit=10)
    assert sessions[0].extra.get("ptyRelayState") == "inactive", (
        "list_sessions() must accept the ptyRelay alias"
    )


def test_list_sessions_captures_resume_command(monkeypatch):
    monkeypatch.setattr(
        ocmod, "_d",
        lambda: _FakeDash({"resumeCommand": "openclaw attach sess-pty"}),
    )
    sessions = OpenClawAdapter().list_sessions(limit=10)
    assert sessions[0].extra.get("resumeCommand") == "openclaw attach sess-pty", (
        "list_sessions() must surface resumeCommand in extra"
    )


def test_list_sessions_captures_resume_cmd_alias(monkeypatch):
    monkeypatch.setattr(
        ocmod, "_d",
        lambda: _FakeDash({"resumeCmd": "openclaw attach sess-pty"}),
    )
    sessions = OpenClawAdapter().list_sessions(limit=10)
    assert sessions[0].extra.get("resumeCommand") == "openclaw attach sess-pty", (
        "list_sessions() must accept the resumeCmd alias"
    )


def test_list_sessions_captures_viewer_preference(monkeypatch):
    monkeypatch.setattr(ocmod, "_d", lambda: _FakeDash({"viewerPreference": "terminal"}))
    sessions = OpenClawAdapter().list_sessions(limit=10)
    assert sessions[0].extra.get("viewerPreference") == "terminal", (
        "list_sessions() must surface viewerPreference in extra"
    )


def test_list_sessions_captures_terminal_preference_alias(monkeypatch):
    monkeypatch.setattr(ocmod, "_d", lambda: _FakeDash({"terminalPreference": "viewer"}))
    sessions = OpenClawAdapter().list_sessions(limit=10)
    assert sessions[0].extra.get("viewerPreference") == "viewer", (
        "list_sessions() must accept the terminalPreference alias"
    )


def test_list_sessions_captures_paired_node_id(monkeypatch):
    monkeypatch.setattr(ocmod, "_d", lambda: _FakeDash({"pairedNodeId": "node-42"}))
    sessions = OpenClawAdapter().list_sessions(limit=10)
    assert sessions[0].extra.get("pairedNodeId") == "node-42", (
        "list_sessions() must surface pairedNodeId in extra"
    )


def test_list_sessions_captures_pair_node_id_alias(monkeypatch):
    monkeypatch.setattr(ocmod, "_d", lambda: _FakeDash({"pairNodeId": "node-99"}))
    sessions = OpenClawAdapter().list_sessions(limit=10)
    assert sessions[0].extra.get("pairedNodeId") == "node-99", (
        "list_sessions() must accept the pairNodeId alias"
    )


def test_list_sessions_omits_pty_fields_for_ordinary_session(monkeypatch):
    monkeypatch.setattr(ocmod, "_d", lambda: _FakeDash({"kind": "direct"}))
    sessions = OpenClawAdapter().list_sessions(limit=10)
    assert "ptyRelayState" not in sessions[0].extra, (
        "ptyRelayState must not appear in extra for ordinary direct sessions"
    )
    assert "resumeCommand" not in sessions[0].extra, (
        "resumeCommand must not appear in extra for ordinary direct sessions"
    )
    assert "pairedNodeId" not in sessions[0].extra, (
        "pairedNodeId must not appear in extra for ordinary direct sessions"
    )
