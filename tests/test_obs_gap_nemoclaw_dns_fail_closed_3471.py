"""Tests for #3471: DNS-backed HTTPS fail-closed denial events surfaced as a
distinct security signal (egressDeniedCount per sandbox, dnsFailClosedCount /
networkEgressDenied on DetectResult.meta).
"""
import json
import shutil
import subprocess

import pytest

from clawmetry.adapters.openclaw import _sandbox_egress_denied_count


# ---------------------------------------------------------------------------
# _sandbox_egress_denied_count
# ---------------------------------------------------------------------------

def _make_run(events_by_sandbox):
    """Return a fake subprocess.run that serves OCSF events as JSON lines."""
    def fake_run(cmd, **kw):
        name = cmd[2]  # ["openshell", "logs", <name>, ...]
        if cmd[1] == "settings":
            return type("R", (), {"stdout": ""})()
        lines = "\n".join(json.dumps(e) for e in events_by_sandbox.get(name, []))
        return type("R", (), {"stdout": lines})()
    return fake_run


def test_deny_with_network_class_uid_counted(monkeypatch):
    """verdict=='deny' + network-activity class_uid (4001-4004) is counted."""
    monkeypatch.setattr(shutil, "which", lambda _: "/usr/bin/openshell")
    events = [
        {"uid": "a1", "verdict": "deny", "class_uid": 4003},
        {"uid": "a2", "verdict": "deny", "class_uid": 4001},
        {"uid": "a3", "verdict": "allow", "class_uid": 4003},
    ]
    monkeypatch.setattr(subprocess, "run", _make_run({"alpha": events}))
    result = _sandbox_egress_denied_count("alpha")
    assert result == {"egressDeniedCount": 2}


def test_deny_with_dst_endpoint_counted(monkeypatch):
    """verdict=='deny' + dst_endpoint is counted even without class_uid."""
    monkeypatch.setattr(shutil, "which", lambda _: "/usr/bin/openshell")
    events = [
        {"uid": "b1", "verdict": "deny", "dst_endpoint": {"ip": "1.2.3.4", "port": 443}},
        {"uid": "b2", "verdict": "deny", "src_endpoint": {"ip": "10.0.0.1"}},
    ]
    monkeypatch.setattr(subprocess, "run", _make_run({"beta": events}))
    result = _sandbox_egress_denied_count("beta")
    assert result == {"egressDeniedCount": 2}


def test_no_denials_returns_empty(monkeypatch):
    """All allow-verdict events yield {} (key absent, not zero)."""
    monkeypatch.setattr(shutil, "which", lambda _: "/usr/bin/openshell")
    events = [
        {"uid": "c1", "verdict": "allow", "class_uid": 4003},
        {"uid": "c2", "class_uid": 4003},
    ]
    monkeypatch.setattr(subprocess, "run", _make_run({"gamma": events}))
    result = _sandbox_egress_denied_count("gamma")
    assert result == {}


def test_non_network_deny_not_counted(monkeypatch):
    """verdict=='deny' without network class_uid or endpoint fields is skipped."""
    monkeypatch.setattr(shutil, "which", lambda _: "/usr/bin/openshell")
    events = [
        # class_uid 5001 is File System Activity — not network-egress
        {"uid": "d1", "verdict": "deny", "class_uid": 5001},
        # no class_uid, no endpoint fields
        {"uid": "d2", "verdict": "deny"},
    ]
    monkeypatch.setattr(subprocess, "run", _make_run({"delta": events}))
    result = _sandbox_egress_denied_count("delta")
    assert result == {}


def test_openshell_absent_returns_empty(monkeypatch):
    """No openshell binary -> {} without raising."""
    monkeypatch.setattr(shutil, "which", lambda _: None)
    result = _sandbox_egress_denied_count("epsilon")
    assert result == {}
