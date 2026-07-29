"""Tests for #4148 — cloud workspace conflict events silently dropped.

OpenClaw's Control UI emits a workspace conflict event into the session JSONL
when it detects a conflict between local and cloud workspace state. Before this
fix, ``_is_v3_event()`` didn't recognise any of the four plausible type-string
aliases (``cloud_workspace_conflict``, ``cloudWorkspaceConflict``,
``workspace_conflict``, ``workspaceConflict``), so the events were routed to
the legacy trajectory parser (which also can't handle them) — they never
reached DuckDB and the dashboard showed no conflict markers.
"""
from __future__ import annotations


def _sync():
    import clawmetry.sync as sync
    return sync


TS = "2026-07-28T10:00:00Z"
SESSION = "ws-conflict-test-session"
NODE = "openclaw+test"

_ALL_ALIASES = (
    "cloud_workspace_conflict",
    "cloudWorkspaceConflict",
    "workspace_conflict",
    "workspaceConflict",
)


def _make_event(t: str, **extra) -> dict:
    return {"type": t, "timestamp": TS, **extra}


def test_all_aliases_recognised_as_v3():
    """_is_v3_event must return True for every workspace-conflict alias."""
    sync = _sync()
    for alias in _ALL_ALIASES:
        assert sync._is_v3_event(_make_event(alias)), f"alias not recognised: {alias!r}"


def test_workspace_conflict_snake_case():
    """cloud_workspace_conflict must produce event_type='workspace.conflict'."""
    sync = _sync()
    obj = _make_event(
        "cloud_workspace_conflict",
        conflictedPaths=["/foo/bar.py", "/baz/qux.py"],
        resolution="use_remote",
        stagedRef="refs/heads/main",
    )
    row = sync._parse_v3_event(obj, session_id=SESSION, node_id=NODE)
    assert row is not None
    assert row["event_type"] == "workspace.conflict"
    assert row["data"]["conflictedPaths"] == ["/foo/bar.py", "/baz/qux.py"]
    assert row["data"]["resolution"] == "use_remote"
    assert row["data"]["stagedRef"] == "refs/heads/main"
    assert row["data"]["data"]["conflictedPaths"] == ["/foo/bar.py", "/baz/qux.py"]


def test_workspace_conflict_camel_case():
    """cloudWorkspaceConflict (camelCase) must produce event_type='workspace.conflict'."""
    sync = _sync()
    obj = _make_event(
        "cloudWorkspaceConflict",
        conflictedPaths=["src/app.py"],
        resolutionAction="stash_local",
    )
    row = sync._parse_v3_event(obj, session_id=SESSION, node_id=NODE)
    assert row is not None
    assert row["event_type"] == "workspace.conflict"
    assert row["data"]["resolution"] == "stash_local"


def test_workspace_conflict_short_snake():
    """workspace_conflict (short) must produce event_type='workspace.conflict'."""
    sync = _sync()
    obj = _make_event("workspace_conflict", paths=["README.md"])
    row = sync._parse_v3_event(obj, session_id=SESSION, node_id=NODE)
    assert row is not None
    assert row["event_type"] == "workspace.conflict"
    assert row["data"]["conflictedPaths"] == ["README.md"]


def test_workspace_conflict_short_camel():
    """workspaceConflict (short camelCase) must produce event_type='workspace.conflict'."""
    sync = _sync()
    obj = _make_event("workspaceConflict", conflicted_paths=["a.py", "b.py"])
    row = sync._parse_v3_event(obj, session_id=SESSION, node_id=NODE)
    assert row is not None
    assert row["event_type"] == "workspace.conflict"
    assert row["data"]["conflictedPaths"] == ["a.py", "b.py"]


def test_workspace_conflict_empty_paths():
    """Missing paths must not crash — fallback to empty list."""
    sync = _sync()
    obj = _make_event("cloud_workspace_conflict")
    row = sync._parse_v3_event(obj, session_id=SESSION, node_id=NODE)
    assert row is not None
    assert row["event_type"] == "workspace.conflict"
    assert row["data"]["conflictedPaths"] == []


def test_workspace_conflict_missing_timestamp_returns_none():
    """Events without a timestamp must be dropped (local store needs ts for indexing)."""
    sync = _sync()
    obj = {"type": "cloud_workspace_conflict", "conflictedPaths": ["x.py"]}
    row = sync._parse_v3_event(obj, session_id=SESSION, node_id=NODE)
    assert row is None


def test_unknown_v3_type_still_dropped():
    """Regression: unknown v3 type aliases must still return None."""
    sync = _sync()
    obj = _make_event("some_future_openclaw_event")
    # _is_v3_event won't route this to _parse_v3_event, but if it somehow did,
    # the parser must still drop it cleanly.
    # Verify _is_v3_event rejects it:
    assert sync._is_v3_event(obj) is False
