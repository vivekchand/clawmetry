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
    monkeypatch.setattr(approvals, "_EXEC_POLICY_BACKOFF",
                        {"fails": 0, "until": 0.0})
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


def test_failed_apply_backs_off_then_retries(monkeypatch, tmp_path):
    # A host that can't complete the CLI (live-hit 2026-07-10: node child
    # outliving the timeout on a 1-core box) must not retry every watcher
    # iteration — that was one ~200MB orphan per minute until the VM wedged.
    applied, state = _wire(monkeypatch, tmp_path)
    monkeypatch.setattr(approvals, "_apply_openclaw_exec_preset",
                        lambda preset: (applied.append(preset), False)[1])
    t = {"now": 1000.0}
    monkeypatch.setattr(approvals.time, "time", lambda: t["now"])
    approvals.sync_openclaw_exec_policy([RM])
    approvals.sync_openclaw_exec_policy([RM])  # inside backoff window
    assert applied == ["cautious"]  # second call did not shell out
    assert not state.exists()       # never written on failure
    t["now"] += approvals._EXEC_POLICY_BACKOFF_BASE_S + 1
    approvals.sync_openclaw_exec_policy([RM])  # backoff expired → retry
    assert applied == ["cautious", "cautious"]


def test_backoff_escalates_and_caps(monkeypatch, tmp_path):
    applied, _ = _wire(monkeypatch, tmp_path)
    monkeypatch.setattr(approvals, "_apply_openclaw_exec_preset",
                        lambda preset: (applied.append(preset), False)[1])
    t = {"now": 1000.0}
    monkeypatch.setattr(approvals.time, "time", lambda: t["now"])
    delays = []
    for _ in range(6):
        approvals.sync_openclaw_exec_policy([RM])
        delays.append(approvals._EXEC_POLICY_BACKOFF["until"] - t["now"])
        t["now"] = approvals._EXEC_POLICY_BACKOFF["until"] + 1
    assert delays == [300, 600, 1200, 2400, 3600, 3600]  # 2x, capped at 1h


def test_success_resets_backoff(monkeypatch, tmp_path):
    applied, state = _wire(monkeypatch, tmp_path)
    ok = {"v": False}
    monkeypatch.setattr(approvals, "_apply_openclaw_exec_preset",
                        lambda preset: (applied.append(preset), ok["v"])[1])
    t = {"now": 1000.0}
    monkeypatch.setattr(approvals.time, "time", lambda: t["now"])
    approvals.sync_openclaw_exec_policy([RM])   # fails → backoff armed
    assert approvals._EXEC_POLICY_BACKOFF["fails"] == 1
    ok["v"] = True
    t["now"] += approvals._EXEC_POLICY_BACKOFF_BASE_S + 1
    approvals.sync_openclaw_exec_policy([RM])   # succeeds
    assert state.read_text() == "cautious"
    assert approvals._EXEC_POLICY_BACKOFF == {"fails": 0, "until": 0.0}


def test_timeout_kills_whole_process_group(monkeypatch, tmp_path):
    # `openclaw` is a wrapper: on timeout the node CHILD must die too, not
    # just the wrapper (the orphan leak that wedged the VM, 2026-07-10).
    import os
    import time as _time
    child_pid_file = tmp_path / "child.pid"
    fake = tmp_path / "openclaw"
    fake.write_text("#!/bin/bash\nsleep 300 &\necho $! > %s\nwait\n"
                    % child_pid_file)
    fake.chmod(0o755)
    monkeypatch.setattr(approvals, "_openclaw_env_and_bin",
                        lambda: (str(fake), dict(os.environ)))
    monkeypatch.setattr(approvals, "_EXEC_POLICY_APPLY_TIMEOUT_S", 1)
    assert approvals._apply_openclaw_exec_preset("cautious") is False
    deadline = _time.time() + 5
    child = int(child_pid_file.read_text().strip())
    while _time.time() < deadline:
        try:
            os.kill(child, 0)
        except ProcessLookupError:
            break  # grandchild is gone — group kill worked
        _time.sleep(0.1)
    else:
        os.kill(child, 9)  # cleanup before failing
        raise AssertionError("grandchild survived the process-group kill")


def test_want_detector():
    assert approvals._policies_want_exec_gate([RM]) is True
    assert approvals._policies_want_exec_gate([SECRETS]) is True
    assert approvals._policies_want_exec_gate([]) is False
    assert approvals._policies_want_exec_gate(
        [{"action": "monitor", "tool": "exec"}]) is False  # monitor != gate
