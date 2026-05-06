"""Unit tests for routes/overview._compute_autonomy_data.

Tests run without a live server by importing the helper directly.
"""

import json
import os
import time
import pytest

from routes.overview import _compute_autonomy_data


def _write_jsonl(path, events):
    with open(path, "w") as fh:
        for ev in events:
            fh.write(json.dumps(ev) + "\n")


def _user(ts_sec):
    return {"role": "user", "content": "hello", "timestamp": ts_sec}


def _assistant(ts_sec):
    return {"role": "assistant", "content": "ok", "timestamp": ts_sec}


class TestMissingOrEmpty:
    def test_nonexistent_dir(self, tmp_path):
        result = _compute_autonomy_data(str(tmp_path / "no_such_dir"))
        assert result["sessions_analyzed"] == 0
        assert result["median_seconds_between_nudges"] == 0
        assert result["zero_nudge_ratio"] == 0.0
        assert result["trend_slope_7d"] == 0.0
        assert result["daily_medians"] == []

    def test_empty_dir(self, tmp_path):
        result = _compute_autonomy_data(str(tmp_path))
        assert result["sessions_analyzed"] == 0

    def test_non_jsonl_files_ignored(self, tmp_path):
        (tmp_path / "notes.txt").write_text("hello\n")
        (tmp_path / "data.json").write_text("{}\n")
        result = _compute_autonomy_data(str(tmp_path))
        assert result["sessions_analyzed"] == 0

    def test_deleted_files_skipped(self, tmp_path):
        _write_jsonl(
            tmp_path / "abc.deleted.jsonl",
            [_user(time.time() - 10), _user(time.time() - 5)],
        )
        result = _compute_autonomy_data(str(tmp_path))
        assert result["sessions_analyzed"] == 0

    def test_reset_files_skipped(self, tmp_path):
        _write_jsonl(
            tmp_path / "abc.reset.jsonl",
            [_user(time.time() - 10), _user(time.time() - 5)],
        )
        result = _compute_autonomy_data(str(tmp_path))
        assert result["sessions_analyzed"] == 0


class TestZeroNudgeSessions:
    def test_single_user_message_counts_as_zero_nudge(self, tmp_path):
        now = time.time()
        _write_jsonl(tmp_path / "s1.jsonl", [_user(now - 100), _assistant(now - 50)])
        result = _compute_autonomy_data(str(tmp_path))
        assert result["sessions_analyzed"] == 1
        assert result["zero_nudge_sessions"] == 1
        assert result["zero_nudge_ratio"] == 1.0

    def test_no_user_messages_not_counted_at_all(self, tmp_path):
        now = time.time()
        _write_jsonl(tmp_path / "s1.jsonl", [_assistant(now - 50)])
        result = _compute_autonomy_data(str(tmp_path))
        assert result["sessions_analyzed"] == 0


class TestNudgeGapComputation:
    def test_two_nudges_gap(self, tmp_path):
        now = time.time()
        _write_jsonl(
            tmp_path / "s1.jsonl",
            [_user(now - 200), _assistant(now - 180), _user(now - 100)],
        )
        result = _compute_autonomy_data(str(tmp_path))
        assert result["sessions_analyzed"] == 1
        assert result["zero_nudge_sessions"] == 0
        assert abs(result["median_seconds_between_nudges"] - 100.0) < 1.0

    def test_three_nudges_median(self, tmp_path):
        now = time.time()
        _write_jsonl(
            tmp_path / "s1.jsonl",
            [
                _user(now - 300),
                _user(now - 200),   # gap 100s
                _user(now - 160),   # gap 40s  → median 70s
            ],
        )
        result = _compute_autonomy_data(str(tmp_path))
        assert abs(result["median_seconds_between_nudges"] - 70.0) < 1.0

    def test_malformed_json_skipped(self, tmp_path):
        now = time.time()
        path = tmp_path / "s1.jsonl"
        with open(path, "w") as fh:
            fh.write("not json at all\n")
            fh.write(json.dumps(_user(now - 200)) + "\n")
            fh.write("{broken\n")
            fh.write(json.dumps(_user(now - 100)) + "\n")
        result = _compute_autonomy_data(str(tmp_path))
        assert result["sessions_analyzed"] == 1
        assert abs(result["median_seconds_between_nudges"] - 100.0) < 1.0

    def test_missing_timestamp_skipped(self, tmp_path):
        now = time.time()
        _write_jsonl(
            tmp_path / "s1.jsonl",
            [
                {"role": "user", "content": "hi"},          # no timestamp
                _user(now - 200),
                _user(now - 100),
            ],
        )
        result = _compute_autonomy_data(str(tmp_path))
        assert result["sessions_analyzed"] == 1
        assert abs(result["median_seconds_between_nudges"] - 100.0) < 1.0


class TestCutoffWindow:
    def test_old_files_excluded(self, tmp_path):
        now = time.time()
        old_path = tmp_path / "old.jsonl"
        _write_jsonl(old_path, [_user(now - 9 * 86400), _user(now - 8 * 86400)])
        # back-date mtime to 8 days ago
        old_ts = now - 8 * 86400
        os.utime(old_path, (old_ts, old_ts))
        result = _compute_autonomy_data(str(tmp_path))
        assert result["sessions_analyzed"] == 0

    def test_recent_files_included(self, tmp_path):
        now = time.time()
        _write_jsonl(
            tmp_path / "recent.jsonl",
            [_user(now - 3600), _user(now - 1800)],
        )
        result = _compute_autonomy_data(str(tmp_path))
        assert result["sessions_analyzed"] == 1


class TestMixedSessions:
    def test_zero_nudge_ratio_mixed(self, tmp_path):
        now = time.time()
        # Session 1: 2 user messages → has nudge
        _write_jsonl(
            tmp_path / "s1.jsonl",
            [_user(now - 300), _user(now - 100)],
        )
        # Session 2: 1 user message → zero nudge
        _write_jsonl(
            tmp_path / "s2.jsonl",
            [_user(now - 200)],
        )
        result = _compute_autonomy_data(str(tmp_path))
        assert result["sessions_analyzed"] == 2
        assert result["zero_nudge_sessions"] == 1
        assert abs(result["zero_nudge_ratio"] - 0.5) < 0.01

    def test_custom_cutoff(self, tmp_path):
        now = time.time()
        cutoff = now - 3600  # 1 hour window
        _write_jsonl(tmp_path / "inside.jsonl", [_user(now - 300), _user(now - 100)])
        old = tmp_path / "outside.jsonl"
        _write_jsonl(old, [_user(now - 7200), _user(now - 6000)])
        os.utime(old, (now - 7200, now - 7200))
        result = _compute_autonomy_data(str(tmp_path), cutoff_ts=cutoff)
        assert result["sessions_analyzed"] == 1


class TestReturnShape:
    def test_all_keys_present_when_empty(self, tmp_path):
        result = _compute_autonomy_data(str(tmp_path))
        for key in (
            "median_seconds_between_nudges",
            "zero_nudge_ratio",
            "trend_slope_7d",
            "sessions_analyzed",
            "zero_nudge_sessions",
            "daily_medians",
        ):
            assert key in result, f"missing key: {key}"

    def test_all_keys_present_with_data(self, tmp_path):
        now = time.time()
        _write_jsonl(tmp_path / "s1.jsonl", [_user(now - 300), _user(now - 100)])
        result = _compute_autonomy_data(str(tmp_path))
        for key in (
            "median_seconds_between_nudges",
            "zero_nudge_ratio",
            "trend_slope_7d",
            "sessions_analyzed",
            "zero_nudge_sessions",
            "daily_medians",
        ):
            assert key in result, f"missing key: {key}"
        assert isinstance(result["daily_medians"], list)
        if result["daily_medians"]:
            dm = result["daily_medians"][0]
            assert "day_offset" in dm
            assert "median_gap_seconds" in dm

    def test_ratio_bounded_0_to_1(self, tmp_path):
        now = time.time()
        _write_jsonl(tmp_path / "s1.jsonl", [_user(now - 200)])
        result = _compute_autonomy_data(str(tmp_path))
        assert 0.0 <= result["zero_nudge_ratio"] <= 1.0
