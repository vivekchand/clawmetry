"""Tests for _detect_heartbeat_loops in routes/heartbeat.py (issue #2009)."""
import json
from datetime import datetime, timedelta, timezone

from routes.heartbeat import _HB_LOOP_MIN, _HB_LOOP_SIM, _detect_heartbeat_loops


def _iso(offset_minutes=0):
    dt = datetime.now(tz=timezone.utc) - timedelta(minutes=offset_minutes)
    return dt.isoformat()


def _write_beat(tmp_path, name, replies, session_offset_minutes=0):
    """Create a heartbeat-named JSONL file with the given assistant replies."""
    fpath = tmp_path / f"heartbeat-{name}.jsonl"
    with open(fpath, "w") as fh:
        for i, text in enumerate(replies):
            ev = {
                "type": "message",
                "timestamp": _iso(offset_minutes=session_offset_minutes + len(replies) - i),
                "message": {
                    "role": "assistant",
                    "content": [{"type": "text", "text": text}],
                },
            }
            fh.write(json.dumps(ev) + "\n")
    return fpath


def test_similar_action_beats_flagged_as_loop(tmp_path):
    """>=3 consecutive nearly-identical action replies -> loop detected."""
    base = "Searching for the same document repeatedly: list_files --pattern '*.md'"
    for i in range(5):
        _write_beat(tmp_path, f"s{i:02d}", [f"{base} run={i}"], session_offset_minutes=5 - i)
    loops = _detect_heartbeat_loops(str(tmp_path))
    assert len(loops) >= 1
    assert loops[0]["repeat_count"] >= _HB_LOOP_MIN


def test_distinct_action_beats_not_flagged(tmp_path):
    """Completely different replies across sessions -> no loop detected."""
    distinct = [
        "Sending welcome message to the new user joining the channel.",
        "Checking database for expired API sessions and cleaning up stale tokens.",
        "Uploading nightly backup archive to object storage bucket.",
        "Generating the weekly analytics PDF report for the admin dashboard.",
        "Processing incoming Stripe payment webhook and updating subscription status.",
    ]
    for i, reply in enumerate(distinct):
        _write_beat(tmp_path, f"s{i:02d}", [reply], session_offset_minutes=5 - i)
    loops = _detect_heartbeat_loops(str(tmp_path))
    assert loops == []


def test_heartbeat_ok_sessions_not_flagged(tmp_path):
    """Sessions that only reply HEARTBEAT_OK are not treated as action beats."""
    for i in range(5):
        _write_beat(tmp_path, f"s{i:02d}", ["HEARTBEAT_OK"], session_offset_minutes=5 - i)
    loops = _detect_heartbeat_loops(str(tmp_path))
    assert loops == []


def test_non_heartbeat_files_skipped(tmp_path):
    """Files without 'heartbeat' in their name are ignored entirely."""
    base = "Doing the exact same thing over and over in a tight loop"
    for i in range(5):
        fpath = tmp_path / f"session-{i:02d}.jsonl"
        ev = {
            "type": "message",
            "timestamp": _iso(offset_minutes=5 - i),
            "message": {
                "role": "assistant",
                "content": [{"type": "text", "text": f"{base} {i}"}],
            },
        }
        fpath.write_text(json.dumps(ev) + "\n")
    loops = _detect_heartbeat_loops(str(tmp_path))
    assert loops == []


def test_missing_directory_returns_empty(tmp_path):
    """Non-existent sessions_dir returns [] without raising."""
    loops = _detect_heartbeat_loops(str(tmp_path / "does_not_exist"))
    assert loops == []


def test_constants_in_expected_range():
    """Sanity-check the exported thresholds."""
    assert 0.5 <= _HB_LOOP_SIM <= 1.0
    assert _HB_LOOP_MIN >= 2
