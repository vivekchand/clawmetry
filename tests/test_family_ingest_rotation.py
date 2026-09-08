"""Family-ingest starvation fix: the adapter walk rotates its start position
each pass (live-hit 2026-08-03: a crash-looping daemon that died mid-pass
always restarted the walk in the same fixed order, so tail adapters —
copilot, antigravity — were never reached and their sessions silently
missed ingest while early adapters kept flowing).

Pure-unit: patches _family_adapter_classes with sentinel classes whose
constructors RECORD the visit order, then asserts consecutive passes start
at successive offsets and the cursor survives in the daemon state dict
(persisted via sync-state.json in production)."""
from __future__ import annotations

import os
import sys
from unittest.mock import patch

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from clawmetry import sync  # noqa: E402


def _sentinels(n):
    visits = []

    def make(i):
        class _A:
            name = f"rt{i}"

            def __init__(self):
                visits.append(self.name)
                raise RuntimeError("stop after recording visit order")
        _A.__name__ = f"A{i}"
        return _A

    return [make(i) for i in range(n)], visits


def _run_pass(classes, state):
    with patch.object(sync, "_family_adapter_classes", return_value=classes), \
         patch.object(sync, "_sync_allowed", return_value=True), \
         patch.object(sync, "_openclaw_spawned_claude_ids", return_value=set(),
                      create=True):
        try:
            sync.sync_family_runtimes({"node_id": "n", "api_key": "k"}, state, {})
        except Exception:
            pass


def test_rotation_advances_each_pass():
    classes, visits = _sentinels(4)
    state = {}
    _run_pass(classes, state)
    first_pass = list(visits)
    assert first_pass[0] == "rt0" and len(first_pass) == 4
    visits.clear()
    _run_pass(classes, state)
    assert visits[0] == "rt1", visits  # rotated by one
    assert set(visits) == {"rt0", "rt1", "rt2", "rt3"}  # still full coverage
    visits.clear()
    _run_pass(classes, state)
    assert visits[0] == "rt2", visits
    assert state["family_adapter_rotation"] == 3


def test_rotation_cursor_survives_restart_shape():
    """A daemon restart reloads state from sync-state.json — a plain int in
    the dict. Corrupt values degrade to offset 0, never crash."""
    classes, visits = _sentinels(3)
    _run_pass(classes, {"family_adapter_rotation": "garbage"})
    assert visits[0] == "rt0"
    visits.clear()
    _run_pass(classes, {"family_adapter_rotation": 7})  # 7 % 3 == 1
    assert visits[0] == "rt1"
