"""Guard: the Fleet must only advertise runtimes with REAL sessions.

Burned 2026-06-03 (founder): the Fleet showed a "Cursor — detected here /
appears shortly / Syncing…" card that never resolved. Root cause: the lite
detector flags a runtime from directory/config presence alone — the Cursor
*IDE* being installed makes ``~/Library/Application Support/Cursor`` exist even
when the Cursor *agent* was never used — so ``_detect_runtimes_for_heartbeat``
reported it with sessions=0 and the cloud rendered a stuck phantom card.

Contract: a runtime with zero sessions is NOT reported (nothing to observe).
Runtimes with real sessions (even one) ARE reported.
"""
from __future__ import annotations

import clawmetry.sync as sync


def test_zero_session_runtime_is_dropped(monkeypatch):
    monkeypatch.setattr(sync, "_detect_runtimes_lite", lambda: [
        {"id": "claude_code", "label": "Claude Code", "sessions": 1251},
        {"id": "cursor", "label": "Cursor", "sessions": 0},      # IDE installed, agent unused
        {"id": "picoclaw", "label": "PicoClaw", "sessions": 0},  # filled in by family below
    ])
    monkeypatch.setattr(sync, "_detect_family_runtimes", lambda: [
        {"name": "picoclaw", "displayName": "PicoClaw", "sessionCount": 1},
        {"name": "goose", "displayName": "Goose", "sessionCount": 4},
    ])
    out = sync._detect_runtimes_for_heartbeat()
    ids = {r["id"] for r in out}

    assert "cursor" not in ids, "0-session cursor phantom must not be reported"
    assert ids == {"claude_code", "picoclaw", "goose"}
    assert all(int(r.get("sessions") or 0) > 0 for r in out), "no 0-session runtime may leak"
    # the family count must win where it's higher (picoclaw 0 -> 1)
    assert next(r for r in out if r["id"] == "picoclaw")["sessions"] == 1


def test_all_real_runtimes_kept(monkeypatch):
    monkeypatch.setattr(sync, "_detect_runtimes_lite", lambda: [])
    monkeypatch.setattr(sync, "_detect_family_runtimes", lambda: [
        {"name": rid, "displayName": rid, "sessionCount": n}
        for rid, n in [("claude_code", 1251), ("codex", 1), ("hermes", 2)]
    ])
    out = sync._detect_runtimes_for_heartbeat()
    assert {r["id"] for r in out} == {"claude_code", "codex", "hermes"}


def test_never_raises_on_bad_detectors(monkeypatch):
    monkeypatch.setattr(sync, "_detect_runtimes_lite", lambda: (_ for _ in ()).throw(RuntimeError("boom")))
    monkeypatch.setattr(sync, "_detect_family_runtimes", lambda: None)
    assert sync._detect_runtimes_for_heartbeat() == []
