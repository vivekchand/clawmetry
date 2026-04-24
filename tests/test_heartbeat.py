"""
Unit tests for routes/heartbeat.py — heartbeat liveness panel (#686).

Tests the ``_compute_heartbeat_data`` helper in isolation (no server needed)
by writing synthetic JSONL session files to a temp directory.

Run with:
    python3 -m pytest tests/test_heartbeat.py -v
"""

import json
import os
import time

import pytest

from routes.heartbeat import _compute_heartbeat_data, _parse_iso_ts


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_session(tmpdir, fname, assistant_replies):
    """Write a minimal heartbeat session JSONL file.

    ``assistant_replies`` is a list of (iso_ts_str, reply_text) tuples.
    """
    path = os.path.join(tmpdir, fname)
    with open(path, "w") as fh:
        for ts_str, reply_text in assistant_replies:
            ev = {
                "type": "message",
                "timestamp": ts_str,
                "message": {
                    "role": "assistant",
                    "content": [{"type": "text", "text": reply_text}],
                },
            }
            fh.write(json.dumps(ev) + "\n")


def _iso(offset_seconds=0):
    """Return an ISO-8601 UTC timestamp offset from now."""
    t = time.time() + offset_seconds
    from datetime import datetime, timezone
    return datetime.fromtimestamp(t, tz=timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# _parse_iso_ts
# ---------------------------------------------------------------------------


class TestParseIsoTs:
    def test_valid_utc_z(self):
        ts = _parse_iso_ts("2025-01-15T10:30:00Z")
        assert ts > 0

    def test_valid_with_offset(self):
        ts = _parse_iso_ts("2025-01-15T10:30:00+00:00")
        assert ts > 0

    def test_empty_string(self):
        assert _parse_iso_ts("") == 0.0

    def test_none(self):
        assert _parse_iso_ts(None) == 0.0

    def test_invalid_string(self):
        assert _parse_iso_ts("not-a-date") == 0.0

    def test_numeric_input(self):
        assert _parse_iso_ts(12345) == 0.0


# ---------------------------------------------------------------------------
# _compute_heartbeat_data — empty / missing directory
# ---------------------------------------------------------------------------


class TestComputeHeartbeatDataEmpty:
    def test_missing_dir_returns_zero_state(self, tmp_path):
        data = _compute_heartbeat_data(str(tmp_path / "nonexistent"))
        assert data["last_heartbeat_ts"] == 0.0
        assert data["recent_beats"] == []
        assert data["ok_count"] == 0
        assert data["action_count"] == 0

    def test_empty_dir_returns_zero_state(self, tmp_path):
        data = _compute_heartbeat_data(str(tmp_path))
        assert data["last_heartbeat_ts"] == 0.0
        assert data["recent_beats"] == []

    def test_non_heartbeat_files_ignored(self, tmp_path):
        """Files not named *heartbeat* are skipped."""
        _write_session(str(tmp_path), "main-session.jsonl", [(_iso(-60), "HEARTBEAT_OK")])
        data = _compute_heartbeat_data(str(tmp_path))
        assert data["last_heartbeat_ts"] == 0.0


# ---------------------------------------------------------------------------
# _compute_heartbeat_data — single heartbeat session
# ---------------------------------------------------------------------------


class TestComputeSingleSession:
    def test_single_ok_beat(self, tmp_path):
        ts = _iso(-600)  # 10 minutes ago
        _write_session(str(tmp_path), "heartbeat-daily.jsonl", [(ts, "HEARTBEAT_OK")])
        data = _compute_heartbeat_data(str(tmp_path))
        assert data["last_heartbeat_ts"] > 0
        assert data["ok_count"] == 1
        assert data["action_count"] == 0
        assert data["ok_ratio"] == 1.0

    def test_single_action_beat(self, tmp_path):
        ts = _iso(-300)  # 5 minutes ago
        _write_session(str(tmp_path), "heartbeat-checker.jsonl", [(ts, "Found 3 new emails, replied to Alice.")])
        data = _compute_heartbeat_data(str(tmp_path))
        assert data["ok_count"] == 0
        assert data["action_count"] == 1
        assert data["ok_ratio"] == 0.0

    def test_session_classified_action_if_any_turn_is_action(self, tmp_path):
        """A session with mixed ok/action replies counts as 'action'."""
        ts1 = _iso(-7200)
        ts2 = _iso(-3600)
        _write_session(
            str(tmp_path),
            "heartbeat-mixed.jsonl",
            [(ts1, "HEARTBEAT_OK"), (ts2, "Found something to do!")],
        )
        data = _compute_heartbeat_data(str(tmp_path))
        assert data["action_count"] == 1
        assert data["ok_count"] == 0

    def test_last_heartbeat_ts_is_most_recent(self, tmp_path):
        """last_heartbeat_ts reflects the most recent session."""
        older_ts = _iso(-3600)
        newer_ts = _iso(-600)
        _write_session(str(tmp_path), "heartbeat-old.jsonl", [(older_ts, "HEARTBEAT_OK")])
        _write_session(str(tmp_path), "heartbeat-new.jsonl", [(newer_ts, "HEARTBEAT_OK")])
        data = _compute_heartbeat_data(str(tmp_path))
        # last_heartbeat_ts should be close to newer_ts
        expected_ts = _parse_iso_ts(newer_ts)
        assert abs(data["last_heartbeat_ts"] - expected_ts) < 5

    def test_recent_beats_ordered_oldest_first(self, tmp_path):
        """recent_beats list is ordered oldest-to-newest (chronological)."""
        beats_written = []
        for i in range(5, 0, -1):
            ts = _iso(-i * 1800)  # 5 sessions, spaced 30 min apart
            fname = f"heartbeat-s{i}.jsonl"
            reply = "HEARTBEAT_OK" if i % 2 == 0 else "Did some work"
            _write_session(str(tmp_path), fname, [(ts, reply)])
            beats_written.append(_parse_iso_ts(ts))
        data = _compute_heartbeat_data(str(tmp_path))
        tss = [b["ts"] for b in data["recent_beats"]]
        assert tss == sorted(tss), "recent_beats should be in ascending timestamp order"

    def test_recent_beats_capped_at_10(self, tmp_path):
        """At most 10 entries in recent_beats."""
        for i in range(15):
            ts = _iso(-i * 1800)
            _write_session(str(tmp_path), f"heartbeat-{i:03d}.jsonl", [(ts, "HEARTBEAT_OK")])
        data = _compute_heartbeat_data(str(tmp_path))
        assert len(data["recent_beats"]) <= 10

    def test_ok_ratio_0_when_all_action(self, tmp_path):
        for i in range(3):
            ts = _iso(-i * 1800)
            _write_session(str(tmp_path), f"heartbeat-a{i}.jsonl", [(ts, "Did work")])
        data = _compute_heartbeat_data(str(tmp_path))
        assert data["ok_ratio"] == 0.0

    def test_ok_ratio_1_when_all_ok(self, tmp_path):
        for i in range(4):
            ts = _iso(-i * 1800)
            _write_session(str(tmp_path), f"heartbeat-o{i}.jsonl", [(ts, "HEARTBEAT_OK")])
        data = _compute_heartbeat_data(str(tmp_path))
        assert data["ok_ratio"] == 1.0

    def test_ok_ratio_mixed(self, tmp_path):
        """3 ok + 1 action → ok_ratio = 0.75."""
        for i in range(3):
            ts = _iso(-(i + 1) * 1800)
            _write_session(str(tmp_path), f"heartbeat-ok{i}.jsonl", [(ts, "HEARTBEAT_OK")])
        _write_session(str(tmp_path), "heartbeat-act.jsonl", [(_iso(-7200), "Busy")])
        data = _compute_heartbeat_data(str(tmp_path))
        assert data["ok_count"] == 3
        assert data["action_count"] == 1
        assert abs(data["ok_ratio"] - 0.75) < 0.001


# ---------------------------------------------------------------------------
# _compute_heartbeat_data — 24h window filtering
# ---------------------------------------------------------------------------


class TestComputeHeartbeat24hWindow:
    def test_old_beats_excluded_from_24h(self, tmp_path):
        """Sessions older than 24h are not counted in beats_24h."""
        old_ts = _iso(-90000)   # 25 hours ago — outside window
        new_ts = _iso(-1800)    # 30 min ago — inside window
        _write_session(str(tmp_path), "heartbeat-old.jsonl", [(old_ts, "HEARTBEAT_OK")])
        _write_session(str(tmp_path), "heartbeat-new.jsonl", [(new_ts, "HEARTBEAT_OK")])
        data = _compute_heartbeat_data(str(tmp_path))
        # beats_24h should only include the new one
        assert len(data["beats_24h"]) == 1

    def test_all_in_24h(self, tmp_path):
        """All recent sessions appear in beats_24h."""
        for i in range(3):
            ts = _iso(-(i + 1) * 3600)  # 1h, 2h, 3h ago
            _write_session(str(tmp_path), f"heartbeat-r{i}.jsonl", [(ts, "HEARTBEAT_OK")])
        data = _compute_heartbeat_data(str(tmp_path))
        assert len(data["beats_24h"]) == 3


# ---------------------------------------------------------------------------
# _compute_heartbeat_data — deleted / reset files skipped
# ---------------------------------------------------------------------------


class TestComputeHeartbeatSkipsArtefacts:
    def test_deleted_files_ignored(self, tmp_path):
        ts = _iso(-600)
        _write_session(str(tmp_path), "heartbeat-old.deleted.20250101.jsonl", [(ts, "HEARTBEAT_OK")])
        data = _compute_heartbeat_data(str(tmp_path))
        assert data["last_heartbeat_ts"] == 0.0

    def test_reset_files_ignored(self, tmp_path):
        ts = _iso(-600)
        _write_session(str(tmp_path), "heartbeat-sess.reset.20250101.jsonl", [(ts, "HEARTBEAT_OK")])
        data = _compute_heartbeat_data(str(tmp_path))
        assert data["last_heartbeat_ts"] == 0.0

    def test_corrupt_json_lines_skipped(self, tmp_path):
        """A file with corrupt JSON in some lines should not raise."""
        path = os.path.join(str(tmp_path), "heartbeat-corrupt.jsonl")
        ts = _iso(-600)
        with open(path, "w") as fh:
            fh.write("this is not json\n")
            fh.write(json.dumps({"type": "message", "timestamp": ts, "message": {"role": "assistant", "content": [{"type": "text", "text": "HEARTBEAT_OK"}]}}) + "\n")
            fh.write("{broken}\n")
        data = _compute_heartbeat_data(str(tmp_path))
        assert data["ok_count"] == 1

    def test_non_message_events_ignored(self, tmp_path):
        """Non-message events (e.g. compaction) are skipped."""
        path = os.path.join(str(tmp_path), "heartbeat-events.jsonl")
        ts = _iso(-600)
        with open(path, "w") as fh:
            # compaction event — should be ignored
            fh.write(json.dumps({"type": "compaction", "timestamp": ts, "summary": "..."}) + "\n")
            # valid assistant message
            fh.write(json.dumps({"type": "message", "timestamp": ts, "message": {"role": "assistant", "content": [{"type": "text", "text": "HEARTBEAT_OK"}]}}) + "\n")
        data = _compute_heartbeat_data(str(tmp_path))
        assert data["ok_count"] == 1
