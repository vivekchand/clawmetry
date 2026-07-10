"""Tests for #3471 and #3616.

#3471: DNS-backed HTTPS fail-closed denial events surfaced as egressDeniedCount.
#3616: The full OCSF audit stream is now classified — allowed connections and
non-network (process/file/auth) events are no longer discarded.
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
    """Network deny events contribute egressDeniedCount; allow events add egressAllowedCount."""
    monkeypatch.setattr(shutil, "which", lambda _: "/usr/bin/openshell")
    events = [
        {"uid": "a1", "verdict": "deny", "class_uid": 4003},
        {"uid": "a2", "verdict": "deny", "class_uid": 4001},
        {"uid": "a3", "verdict": "allow", "class_uid": 4003},
    ]
    monkeypatch.setattr(subprocess, "run", _make_run({"alpha": events}))
    result = _sandbox_egress_denied_count("alpha")
    assert result == {"egressDeniedCount": 2, "egressAllowedCount": 1}


def test_deny_with_dst_endpoint_counted(monkeypatch):
    """verdict=='deny' + dst_endpoint / src_endpoint is counted as network-egress denied."""
    monkeypatch.setattr(shutil, "which", lambda _: "/usr/bin/openshell")
    events = [
        {"uid": "b1", "verdict": "deny", "dst_endpoint": {"ip": "1.2.3.4", "port": 443}},
        {"uid": "b2", "verdict": "deny", "src_endpoint": {"ip": "10.0.0.1"}},
    ]
    monkeypatch.setattr(subprocess, "run", _make_run({"beta": events}))
    result = _sandbox_egress_denied_count("beta")
    assert result == {"egressDeniedCount": 2}


def test_network_allow_surfaced_as_egress_allowed(monkeypatch):
    """Allowed network connections (previously dropped) now produce egressAllowedCount."""
    monkeypatch.setattr(shutil, "which", lambda _: "/usr/bin/openshell")
    events = [
        {"uid": "c1", "verdict": "allow", "class_uid": 4003},
        # no verdict → not counted in either network bucket
        {"uid": "c2", "class_uid": 4003},
    ]
    monkeypatch.setattr(subprocess, "run", _make_run({"gamma": events}))
    result = _sandbox_egress_denied_count("gamma")
    assert result == {"egressAllowedCount": 1}


def test_non_network_events_counted_as_process_file_auth(monkeypatch):
    """Process/file/auth OCSF events (previously discarded) populate processFileAuthAuditCount."""
    monkeypatch.setattr(shutil, "which", lambda _: "/usr/bin/openshell")
    events = [
        # class_uid 5001 is File System Activity
        {"uid": "d1", "verdict": "deny", "class_uid": 5001},
        # no class_uid, no endpoint fields → non-network
        {"uid": "d2", "verdict": "deny"},
    ]
    monkeypatch.setattr(subprocess, "run", _make_run({"delta": events}))
    result = _sandbox_egress_denied_count("delta")
    assert result == {"processFileAuthAuditCount": 2}


def test_openshell_absent_returns_empty(monkeypatch):
    """No openshell binary -> {} without raising."""
    monkeypatch.setattr(shutil, "which", lambda _: None)
    result = _sandbox_egress_denied_count("epsilon")
    assert result == {}


def test_mixed_event_stream_all_buckets(monkeypatch):
    """A realistic mixed stream populates all three counters (#3616)."""
    monkeypatch.setattr(shutil, "which", lambda _: "/usr/bin/openshell")
    events = [
        # network denies
        {"uid": "m1", "verdict": "deny",  "class_uid": 4001},
        {"uid": "m2", "verdict": "deny",  "class_uid": 4002},
        # network allow
        {"uid": "m3", "verdict": "allow", "class_uid": 4003},
        # process activity (class_uid outside network range)
        {"uid": "m4", "verdict": "allow", "class_uid": 1007, "actor": {"process": {"pid": 42}}},
        # auth event
        {"uid": "m5", "class_uid": 3001, "actor": {"user": {"name": "sandbox-agent"}}},
        # file activity deny (no endpoint → non-network)
        {"uid": "m6", "verdict": "deny",  "class_uid": 5001, "file": {"path": "/etc/passwd"}},
    ]
    monkeypatch.setattr(subprocess, "run", _make_run({"mixed": events}))
    result = _sandbox_egress_denied_count("mixed")
    assert result == {
        "egressDeniedCount": 2,
        "egressAllowedCount": 1,
        "processFileAuthAuditCount": 3,
    }


def test_only_non_network_events_no_egress_keys(monkeypatch):
    """When all events are non-network only processFileAuthAuditCount is set."""
    monkeypatch.setattr(shutil, "which", lambda _: "/usr/bin/openshell")
    events = [
        {"uid": "p1", "class_uid": 3001},
        {"uid": "p2", "class_uid": 1007},
    ]
    monkeypatch.setattr(subprocess, "run", _make_run({"proc": events}))
    result = _sandbox_egress_denied_count("proc")
    assert result == {"processFileAuthAuditCount": 2}
    assert "egressDeniedCount" not in result
    assert "egressAllowedCount" not in result
