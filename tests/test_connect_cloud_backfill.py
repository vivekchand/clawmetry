"""``clawmetry connect`` queues local-only history for cloud backfill.

Founder live-hit 2026-07-29: after running local-only (trial license, no
cloud), Enable Cloud Sync connected the account but the cloud dashboard sat
at "No machines connected yet / 0 sessions" forever. The family-runtime
high-water marks were stamped "done" during local-only ingest, so the first
cloud-connected pass skipped every session. ``_reset_family_sync_marks``
clears them at connect time; the next daemon pass re-ingests (idempotent PK
upserts) and pushes the full set to the newly connected account.
"""
from __future__ import annotations

import json

from clawmetry import cli as _cli


def _write_state(home, state):
    d = home / ".clawmetry"
    d.mkdir(parents=True, exist_ok=True)
    (d / "sync-state.json").write_text(json.dumps(state), encoding="utf-8")


def test_reset_clears_marks_and_reports_count(tmp_path, monkeypatch):
    monkeypatch.setattr(_cli.Path, "home", staticmethod(lambda: tmp_path))
    _write_state(tmp_path, {
        "family_event_high_water": {
            "claude_code:s1": "2026-07-29T00:00:00+00:00@@0",
            "cursor:s2": "2026-07-29T00:00:01+00:00@@0",
        },
        "other_state": {"keep": "me"},
    })
    assert _cli._reset_family_sync_marks() == 2
    left = json.loads(
        (tmp_path / ".clawmetry" / "sync-state.json").read_text(encoding="utf-8"))
    assert "family_event_high_water" not in left
    # Unrelated state survives untouched.
    assert left["other_state"] == {"keep": "me"}


def test_reset_is_a_noop_without_marks_or_state(tmp_path, monkeypatch):
    monkeypatch.setattr(_cli.Path, "home", staticmethod(lambda: tmp_path))
    # No state file at all.
    assert _cli._reset_family_sync_marks() == 0
    # State file without marks.
    _write_state(tmp_path, {"other": 1})
    assert _cli._reset_family_sync_marks() == 0
    left = json.loads(
        (tmp_path / ".clawmetry" / "sync-state.json").read_text(encoding="utf-8"))
    assert left == {"other": 1}


def test_connect_calls_the_backfill_reset():
    """The reset must be wired into the connect flow itself (revert trap:
    removing the call re-opens the never-backfills gap)."""
    import inspect
    src = inspect.getsource(_cli._cmd_connect)
    assert "_reset_family_sync_marks" in src
    assert "cloud backfill" in src
