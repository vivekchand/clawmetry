"""Unit tests for routes/selfconfig.py session-attribution helpers (#689).

Pure-Python: exercises the helper functions directly without spinning up a
Flask server, so this file runs in CI without a live ClawMetry instance.
"""
import json
import os
import sys
import tempfile
import time

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from routes import selfconfig as sc  # noqa: E402


def _write_jsonl(path, rows):
    with open(path, "w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row) + "\n")


def _edit_event(ts_iso, file_path, tool="Edit"):
    return {
        "type": "message",
        "timestamp": ts_iso,
        "message": {
            "role": "assistant",
            "content": [
                {"type": "tool_use", "name": tool, "input": {"file_path": file_path}},
            ],
        },
    }


def test_normalise_file_path_lowercases_basename():
    assert sc._normalise_file_path("/home/vivek/clawd/SOUL.md")[-1] == "soul.md"


def test_normalise_file_path_handles_relative_path():
    tokens = sc._normalise_file_path("workspace/SOUL.md")
    assert tokens[-1] == "soul.md"


def test_normalise_file_path_empty_returns_empty_tuple():
    assert sc._normalise_file_path("") == ()
    assert sc._normalise_file_path(None) == ()


def test_path_matches_basename_match():
    needle = sc._normalise_file_path("/abc/SOUL.md")
    assert sc._path_matches(needle, "/some/other/path/SOUL.md") is True


def test_path_matches_different_file_rejected():
    needle = sc._normalise_file_path("/abc/SOUL.md")
    assert sc._path_matches(needle, "/some/other/path/USER.md") is False


def test_parse_ts_to_epoch_iso():
    epoch = sc._parse_ts_to_epoch("2026-05-10T01:00:00Z")
    assert epoch is not None
    assert 1746000000 < epoch < 1810000000


def test_parse_ts_to_epoch_millis():
    # > 1e12 means millisecond epoch — should be normalised to seconds.
    millis = 1_777_619_067_124
    seconds = sc._parse_ts_to_epoch(millis)
    assert seconds is not None
    assert 1_777_000_000 < seconds < 1_778_000_000


def test_scan_jsonl_finds_matching_edit():
    needle = sc._normalise_file_path("/ws/SOUL.md")
    with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as tf:
        path = tf.name
    try:
        _write_jsonl(path, [
            _edit_event("2026-05-10T01:00:00Z", "/ws/USER.md"),
            _edit_event("2026-05-10T01:05:00Z", "/ws/SOUL.md", tool="Write"),
            _edit_event("2026-05-10T01:10:00Z", "/ws/SOUL.md", tool="Edit"),
        ])
        since = sc._parse_ts_to_epoch("2026-05-10T00:00:00Z")
        until = sc._parse_ts_to_epoch("2026-05-10T02:00:00Z")
        result = sc._scan_jsonl_for_edit(path, needle, since, until)
        assert result is not None
        # The most recent matching edit wins.
        ev_ts, tool_name = result
        assert tool_name == "edit"
        assert ev_ts == sc._parse_ts_to_epoch("2026-05-10T01:10:00Z")
    finally:
        os.unlink(path)


def test_scan_jsonl_ignores_outside_window():
    needle = sc._normalise_file_path("/ws/SOUL.md")
    with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as tf:
        path = tf.name
    try:
        _write_jsonl(path, [
            _edit_event("2026-05-10T01:10:00Z", "/ws/SOUL.md", tool="Edit"),
        ])
        # Window before the event — must miss it.
        since = sc._parse_ts_to_epoch("2026-05-09T00:00:00Z")
        until = sc._parse_ts_to_epoch("2026-05-09T02:00:00Z")
        assert sc._scan_jsonl_for_edit(path, needle, since, until) is None
    finally:
        os.unlink(path)


def test_scan_jsonl_ignores_non_edit_tools():
    needle = sc._normalise_file_path("/ws/SOUL.md")
    with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as tf:
        path = tf.name
    try:
        _write_jsonl(path, [
            {
                "type": "message",
                "timestamp": "2026-05-10T01:00:00Z",
                "message": {
                    "role": "assistant",
                    "content": [
                        {"type": "tool_use", "name": "Read", "input": {"file_path": "/ws/SOUL.md"}},
                    ],
                },
            },
        ])
        since = sc._parse_ts_to_epoch("2026-05-10T00:00:00Z")
        until = sc._parse_ts_to_epoch("2026-05-10T02:00:00Z")
        assert sc._scan_jsonl_for_edit(path, needle, since, until) is None
    finally:
        os.unlink(path)


def test_scan_jsonl_handles_corrupt_lines():
    needle = sc._normalise_file_path("/ws/SOUL.md")
    with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as tf:
        path = tf.name
    try:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("{not json\n")
            fh.write(json.dumps(_edit_event("2026-05-10T01:10:00Z", "/ws/SOUL.md")) + "\n")
            fh.write("}}}\n")
        since = sc._parse_ts_to_epoch("2026-05-10T00:00:00Z")
        until = sc._parse_ts_to_epoch("2026-05-10T02:00:00Z")
        result = sc._scan_jsonl_for_edit(path, needle, since, until)
        assert result is not None
    finally:
        os.unlink(path)


def test_find_session_for_file_change_picks_most_recent(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        sessions_dir = os.path.join(tmp, "sessions")
        os.makedirs(sessions_dir)

        old_jsonl = os.path.join(sessions_dir, "old-session.jsonl")
        new_jsonl = os.path.join(sessions_dir, "new-session.jsonl")
        _write_jsonl(old_jsonl, [
            _edit_event("2026-05-10T01:05:00Z", "/ws/SOUL.md", tool="Edit"),
        ])
        _write_jsonl(new_jsonl, [
            _edit_event("2026-05-10T01:10:00Z", "/ws/SOUL.md", tool="Write"),
        ])
        sessions_json = {
            "agent:main:user:label-old": {"sessionId": "old-session", "displayName": "Old chat"},
            "agent:main:user:label-new": {"sessionId": "new-session", "displayName": "New chat"},
        }
        with open(os.path.join(sessions_dir, "sessions.json"), "w") as fh:
            json.dump(sessions_json, fh)

        monkeypatch.setattr(sc, "_sessions_dir", lambda: sessions_dir)

        since = sc._parse_ts_to_epoch("2026-05-10T00:00:00Z")
        until = sc._parse_ts_to_epoch("2026-05-10T02:00:00Z")
        result = sc._find_session_for_file_change("/ws/SOUL.md", since, until)
        assert result is not None
        assert result["session_id"] == "new-session"
        assert result["session_label"] == "New chat"
        assert result["tool"] == "write"


def test_find_session_for_file_change_returns_none_when_no_match(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        sessions_dir = os.path.join(tmp, "sessions")
        os.makedirs(sessions_dir)
        monkeypatch.setattr(sc, "_sessions_dir", lambda: sessions_dir)
        since = sc._parse_ts_to_epoch("2026-05-10T00:00:00Z")
        until = sc._parse_ts_to_epoch("2026-05-10T02:00:00Z")
        assert sc._find_session_for_file_change("/ws/SOUL.md", since, until) is None


def test_snapshot_records_source_in_revision(monkeypatch):
    """End-to-end: writing to a tracked file then triggering a snapshot
    records the matching session in the revision metadata."""
    with tempfile.TemporaryDirectory() as tmp:
        workspace = os.path.join(tmp, "workspace")
        os.makedirs(workspace)
        soul_path = os.path.join(workspace, "SOUL.md")
        with open(soul_path, "w") as fh:
            fh.write("# Soul\nFirst version\n")

        sessions_dir = os.path.join(tmp, "sessions")
        os.makedirs(sessions_dir)
        sess_jsonl = os.path.join(sessions_dir, "abc-1234.jsonl")
        # Edit event timestamp must fall inside the snapshot window — use
        # ‘now’ rather than a hard-coded date so we don't drift past the
        # 24-hour lookback window.
        from datetime import datetime, timezone, timedelta
        now_iso = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        _write_jsonl(sess_jsonl, [
            _edit_event(now_iso, soul_path, tool="Edit"),
        ])
        with open(os.path.join(sessions_dir, "sessions.json"), "w") as fh:
            json.dump({
                "agent:main:user:foo": {"sessionId": "abc-1234", "displayName": "Test session"},
            }, fh)

        history_root = os.path.join(tmp, "history")
        monkeypatch.setattr(sc, "_history_root", lambda: history_root)
        monkeypatch.setattr(sc, "_sessions_dir", lambda: sessions_dir)
        monkeypatch.setattr(sc, "_locate_file", lambda name: soul_path if name == "SOUL.md" else None)
        # _SNAPSHOT_INTERVAL guards re-runs; force it to 0 so the test is deterministic.
        monkeypatch.setattr(sc, "_SNAPSHOT_INTERVAL", 0)

        sc._snapshot_if_changed()
        index = sc._load_index()
        revisions = index.get("SOUL.md", {}).get("revisions", [])
        assert revisions, "snapshot must have recorded at least one revision"
        source = revisions[-1].get("source")
        assert source is not None, f"revision missing source attribution: {revisions[-1]}"
        assert source["session_id"] == "abc-1234"
        assert source["tool"] == "edit"
        assert source["session_label"] == "Test session"
