"""Security scope and ordering regressions: AC-GOV-SBG-003.1/.2/.3.

These are pure argument replays. No displayed command is executed.

AC-GOV-SBG-003.1: a single declared outside mutation is found.
AC-GOV-SBG-003.2: unresolved paths retain unknown lexical scope.
AC-GOV-SBG-003.3: security impact outranks operational spend.
"""
from __future__ import annotations

import json
import math

import pytest

from clawmetry import detectors
from clawmetry import detector_money
from routes.guard import _incident_rank


def _event(tool, args):
    return {"event_type": "tool_call", "ts": "2026-10-26T10:00:01Z",
            "data": {"tool": tool, "args": args}}


def _scope(path, cwd="/workspace", tool="Write"):
    return detectors.file_blast_radius(
        [_event(tool, {"file_path": path})], "claude_code:scope", "claude_code",
        facts={"cwd": cwd})


@pytest.mark.parametrize("cwd,path", [
    ("/workspace", "/etc/cron.d/update"),
    ("/workspace", "/workspace-other/new.py"),
    ("/workspace", "../outside.py"),
    ("/workspace", "/workspace/../outside.py"),
    ("/workspace/nested", "../../outside.py"),
    (r"C:\Workspace", r"C:\Workspace-other\new.py"),
    (r"C:\Workspace", r"C:\Workspace\..\outside.py"),
    (r"C:\Workspace", r"D:\new.py"),
    (r"C:\Workspace", r"\Windows\new.py"),
    (r"\\server\share\project", r"\\server\share\other\new.py"),
    (r"\\server\share\project", r"\\server\other\new.py"),
    ("//server/share/project", "//server/share/other/new.py"),
    (r"\\server\share", r"\\server\other\new.py"),
])
def test_one_declared_outside_mutation_is_reported(cwd, path):
    """AC-GOV-SBG-003.1: one crossing does not need a wide edit."""
    incident = _scope(path, cwd)
    assert incident is not None
    assert incident["kind"] == "file_blast_radius"
    assert incident["severity"] == "warning"
    assert incident["evidence"]["outside_workspace"] == 1
    assert incident["evidence"]["scope_basis"] == "lexical_tool_arguments"
    assert incident["evidence"]["symlinks_resolved"] is False
    assert path not in json.dumps(incident)


@pytest.mark.parametrize("cwd,path", [
    ("/workspace", "/workspace/new.py"),
    ("/workspace", "./new.py"),
    ("/workspace", "./sub/../new.py"),
    ("/", "/etc/new.py"),
    (r"C:\Workspace", r"c:\workspace\new.py"),
    (r"C:\Workspace", r"sub\..\new.py"),
    (r"C:\Workspace", r"C:new.py"),
    (r"\\server\share\project", r"\\SERVER\SHARE\PROJECT\new.py"),
])
def test_lexically_contained_mutation_is_not_a_crossing(cwd, path):
    """AC-GOV-SBG-003.1: path components and platform rules decide scope."""
    assert _scope(path, cwd) is None


@pytest.mark.parametrize("cwd,path", [
    ("", "/etc/new.py"),
    ("relative/workspace", "/etc/new.py"),
    ("/workspace", "~/new.py"),
    ("/workspace", "$TARGET/new.py"),
    (r"C:\Workspace", r"%TEMP%\new.py"),
    (r"C:\Workspace", r"D:new.py"),
])
def test_missing_context_and_unresolved_expansion_do_not_guess(cwd, path):
    """AC-GOV-SBG-003.2: unknown roots and expansions do not fabricate scope."""
    assert _scope(path, cwd) is None


def test_reading_outside_is_not_a_write_crossing():
    assert _scope("/etc/passwd", tool="Read") is None


def test_direct_file_tool_context_is_not_a_mutation_destination():
    incident = detectors.file_blast_radius(
        [_event("Write", {"file_path": "/workspace/new.py", "cwd": "/outside"})],
        "claude_code:scope", "claude_code", facts={"cwd": "/workspace"})
    assert incident is None


def test_relative_mutation_respects_the_calls_declared_working_directory():
    incident = detectors.file_blast_radius(
        [_event("Bash", {"command": "touch new.txt", "cwd": "/outside"})],
        "claude_code:scope", "claude_code", facts={"cwd": "/workspace"})
    assert incident is not None
    assert incident["evidence"]["outside_workspace"] == 1


def test_extensionless_file_target_is_still_a_declared_path():
    incident = detectors.file_blast_radius(
        [_event("Write", {"file_path": "passwd", "cwd": "/etc"})],
        "claude_code:scope", "claude_code", facts={"cwd": "/workspace"})
    assert incident is not None
    assert incident["evidence"]["outside_workspace"] == 1


def test_patch_contents_are_not_file_targets():
    incident = detectors.file_blast_radius(
        [_event("apply_patch", {"input": "*** Begin Patch\n*** Add File: /workspace/file.py\n+example = '/outside/path'\n*** End Patch"})],
        "codex:scope", "codex", facts={"cwd": "/workspace"})
    assert incident is None


def test_nested_edit_replacement_text_is_not_a_mutation_destination():
    incident = detectors.file_blast_radius(
        [_event("MultiEdit", {"edits": [{"path": "/workspace/new.py", "code": "/outside/path"}]})],
        "claude_code:scope", "claude_code", facts={"cwd": "/workspace"})
    assert incident is None


def test_patch_move_header_is_a_mutation_destination():
    incident = detectors.file_blast_radius(
        [_event("apply_patch", {"input": "*** Begin Patch\n*** Update File: /workspace/file.py\n*** Move to: /outside/file.py\n*** End Patch"})],
        "codex:scope", "codex", facts={"cwd": "/workspace"})
    assert incident is not None
    assert incident["evidence"]["outside_workspace"] == 1


@pytest.mark.parametrize("command", [
    "cp /outside/source.txt /workspace/copy.txt",
    "cat /outside/source.txt > /workspace/copy.txt",
    "printf '/outside/source.txt' > /workspace/copy.txt",
    "printf '>' /outside/source.txt",
    "pip install /outside/package",
])
def test_shell_read_sources_are_not_reported_as_mutation_targets(command):
    incident = detectors.file_blast_radius(
        [_event("Bash", {"command": command})], "claude_code:scope", "claude_code",
        facts={"cwd": "/workspace"})
    assert incident is None


@pytest.mark.parametrize("command", [
    "cp /workspace/source.txt /outside/copy.txt",
    "printf hello > '/outside/new file.txt'",
    "touch ../outside.txt",
    "cp -t /outside /workspace/source.txt",
])
def test_shell_mutation_destinations_are_reported(command):
    incident = detectors.file_blast_radius(
        [_event("Bash", {"command": command})], "claude_code:scope", "claude_code",
        facts={"cwd": "/workspace"})
    assert incident is not None
    assert incident["evidence"]["outside_workspace"] == 1


def test_boundary_evidence_does_not_resolve_symlinks(monkeypatch):
    """AC-GOV-SBG-003.2: lexical scope never claims actual path resolution."""
    import os.path
    monkeypatch.setattr(os.path, "realpath", lambda *a, **kw: pytest.fail("filesystem resolution"))
    assert _scope("/workspace/symlink/new.py") is None
    assert _scope("/outside/new.py")["evidence"]["symlinks_resolved"] is False


def _incident(kind, severity, spend):
    return {"kind": kind, "severity": severity,
            "spend_at_risk_usd": spend, "evidence": {}}


@pytest.mark.parametrize("kind", [
    "credential_access", "privilege_change", "file_blast_radius",
    "prompt_injection", "repo_config_exec", "security_threat",
])
def test_security_priority_does_not_depend_on_llm_spend(kind):
    """AC-GOV-SBG-003.3: critical security precedes costly operations."""
    security = _incident(kind, "critical", 0)
    costly_loop = _incident("stuck_loop", "critical", 10000)
    assert detectors.sort_incidents([costly_loop, security])[0] is security
    assert _incident_rank(security) > _incident_rank(costly_loop)


def test_operational_order_stays_cost_based():
    """AC-GOV-SBG-003.3: cost still orders operational incidents."""
    cheap = _incident("stuck_loop", "warning", 1)
    costly = _incident("action_discrepancy", "info", 100)
    assert detectors.sort_incidents([cheap, costly]) == [costly, cheap]


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), -float("inf"), -1, "bad", {}, []])
def test_invalid_cost_cannot_dominate_security_or_operational_order(bad):
    """AC-GOV-SBG-003.3: malformed and nonfinite costs are unknown."""
    invalid = _incident("stuck_loop", "warning", bad)
    valid = _incident("no_progress", "warning", 1)
    assert detectors.sort_incidents([invalid, valid])[0] is valid
    assert _incident_rank(invalid) == detector_money.incident_rank(invalid)
    assert all(not isinstance(value, float) or math.isfinite(value)
               for value in detector_money.incident_rank(invalid))


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), -float("inf")])
def test_nonfinite_measurements_never_fabricate_spend_or_promote(bad):
    """AC-GOV-SBG-003.3: ranking and annotation keep finite evidence."""
    incidents = [_incident("stuck_loop", "warning", 0)]
    output = detectors.annotate_spend(
        incidents, cost_usd=bad, session_seconds=60, bad_for_seconds=60)
    assert output[0]["spend_at_risk_usd"] == 0
    assert output[0]["severity"] == "warning"
    assert all(math.isfinite(output[0][key]) for key in (
        "spend_at_risk_usd", "burn_rate_usd_per_min", "session_cost_usd"))


@pytest.mark.parametrize("kind", ["credential_access", "network_egress", "prompt_injection", "security_threat"])
def test_model_spend_does_not_escalate_security_impact(kind):
    """AC-GOV-SBG-003.3: security labels describe security evidence."""
    output = detectors.annotate_spend(
        [_incident(kind, "warning", 0)], cost_usd=600,
        session_seconds=60, bad_for_seconds=60)
    assert output[0]["severity"] == "warning"
    assert output[0]["spend_at_risk_usd"] == 600


def test_unc_share_root_is_known_and_drive_relative_targets_need_matching_base():
    from clawmetry.workspace_scope import path_scope
    assert path_scope(r"\\server\share\new.py", r"\\server\share") == "inside"
    assert path_scope(r"C:new.py", r"C:\workspace", relative_base=r"D:\other") == "unknown"
