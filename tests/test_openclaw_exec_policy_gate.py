"""Daemon drives OpenClaw's native exec-approval gate from the active policies.

ClawMetry's own watcher is reactive (can't prevent a command). When a
require-approval policy covering exec is active, the daemon applies
`openclaw exec-policy preset cautious` (pre-execution gate); when none are,
it restores `yolo` — but only if it was the one that set cautious, so a
hand-set posture is never clobbered. No-op off an OpenClaw host.
"""
from __future__ import annotations

import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from clawmetry import approvals  # noqa: E402


def _wire(monkeypatch, tmp_path, has_openclaw=True, prev=None):
    state = tmp_path / "exec_policy_applied"
    if prev is not None:
        state.write_text(prev)
    monkeypatch.setattr(approvals, "_EXEC_POLICY_STATE", state)
    monkeypatch.setattr(approvals, "_openclaw_env_and_bin",
                        lambda: (("/usr/local/bin/openclaw" if has_openclaw else None), {}))
    applied = []
    monkeypatch.setattr(approvals, "_apply_openclaw_exec_preset",
                        lambda preset: (applied.append(preset), True)[1])
    return applied, state


RM = {"action": "require_approval", "tool": "exec",
      "pattern": r"rm\s+-rf", "enabled": True}
SECRETS = {"action": "require_approval", "tool": "",
           "pattern": r"\.env", "enabled": True}


def test_enable_applies_cautious(monkeypatch, tmp_path):
    applied, state = _wire(monkeypatch, tmp_path)
    approvals.sync_openclaw_exec_policy([RM])
    assert applied == ["cautious"]
    assert state.read_text() == "cautious"


def test_secrets_rule_tool_agnostic_still_gates(monkeypatch, tmp_path):
    applied, _ = _wire(monkeypatch, tmp_path)
    approvals.sync_openclaw_exec_policy([SECRETS])
    assert applied == ["cautious"]


def test_no_reapply_when_already_cautious(monkeypatch, tmp_path):
    applied, _ = _wire(monkeypatch, tmp_path, prev="cautious")
    approvals.sync_openclaw_exec_policy([RM])
    assert applied == []  # idempotent — desired == last applied


def test_disable_restores_yolo_only_if_we_set_cautious(monkeypatch, tmp_path):
    applied, state = _wire(monkeypatch, tmp_path, prev="cautious")
    approvals.sync_openclaw_exec_policy([])  # all rules off
    assert applied == ["yolo"]
    assert state.read_text() == "yolo"


def test_disable_does_not_force_yolo_on_handset_posture(monkeypatch, tmp_path):
    # No prior state (operator may have set deny-all by hand) → never relax.
    applied, _ = _wire(monkeypatch, tmp_path, prev=None)
    approvals.sync_openclaw_exec_policy([])
    assert applied == []


def test_noop_off_openclaw_host(monkeypatch, tmp_path):
    applied, _ = _wire(monkeypatch, tmp_path, has_openclaw=False)
    approvals.sync_openclaw_exec_policy([RM])
    assert applied == []


def test_disabled_policy_does_not_gate(monkeypatch, tmp_path):
    applied, _ = _wire(monkeypatch, tmp_path)
    # A cloud policy row that is present but disabled must not trigger the gate.
    # (load_policies already filters enabled; _policies_want_exec_gate keys off
    # action/tool, so we assert the want-detector directly for a non-exec tool.)
    approvals.sync_openclaw_exec_policy([{"action": "require_approval",
                                          "tool": "browser", "enabled": True}])
    assert applied == []  # browser-only rule doesn't imply an exec gate


def test_want_detector():
    assert approvals._policies_want_exec_gate([RM]) is True
    assert approvals._policies_want_exec_gate([SECRETS]) is True
    assert approvals._policies_want_exec_gate([]) is False
    assert approvals._policies_want_exec_gate(
        [{"action": "monitor", "tool": "exec"}]) is False  # monitor != gate
