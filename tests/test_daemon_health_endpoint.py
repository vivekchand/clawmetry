"""Pure-unit tests for the daemon-log error-rate parser (PRD #1133 layer 4).

Covers ``routes.health.compute_daemon_health`` — the helper that powers the
new ``daemon`` block on ``/api/system-health``. We test the parser directly
(no Flask server, no network, no sleep) because the integration tests in
``test_api.py`` already exercise the wider endpoint surface.

Why this matters: shipped 2026-05-13 because the 0.12.179 NameError
(``ALERTS_EVAL_INTERVAL_SEC``) was logging 4×/min on every install with no
in-product surface. The user only noticed by manually tailing
``~/.clawmetry/sync.log``.
"""
from __future__ import annotations

import os
import sys
import time
from datetime import datetime

import pytest


_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)


from routes.health import (  # noqa: E402
    _DAEMON_LOG_LINE_RE,
    _parse_daemon_log_line,
    _tail_lines,
    compute_daemon_health,
)


# ── Helpers ────────────────────────────────────────────────────────────────────


def _fmt_ts(epoch):
    """Format an epoch second as ``YYYY-MM-DD HH:MM:SS,mmm`` (daemon format)."""
    return datetime.fromtimestamp(epoch).strftime("%Y-%m-%d %H:%M:%S,000")


def _err(epoch, msg="Sync cycle error: name 'ALERTS_EVAL_INTERVAL_SEC' is not defined"):
    return f"{_fmt_ts(epoch)} [clawmetry-sync] ERROR {msg}"


def _info(epoch, msg="✓ Cloud sync activated — uploads resumed."):
    return f"{_fmt_ts(epoch)} [clawmetry-sync] INFO {msg}"


def _warn(epoch, msg="pending_query dispatch failed"):
    return f"{_fmt_ts(epoch)} [clawmetry-sync] WARNING {msg}"


def _write_log(tmp_path, lines):
    p = tmp_path / "sync.log"
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return str(p)


# ── Parser-level tests ─────────────────────────────────────────────────────────


class TestLineRegex:
    def test_matches_real_error_line(self):
        line = "2026-05-13 09:33:53,864 [clawmetry-sync] ERROR Sync cycle error: name 'X' is not defined"
        m = _DAEMON_LOG_LINE_RE.match(line)
        assert m is not None
        assert m.group("level") == "ERROR"
        assert m.group("ts") == "2026-05-13 09:33:53"
        assert m.group("msg").startswith("Sync cycle error:")

    def test_matches_warning_line(self):
        line = "2026-05-13 09:33:54,014 [clawmetry-sync] WARNING pending_query dispatch failed (id=q_brain)"
        m = _DAEMON_LOG_LINE_RE.match(line)
        assert m is not None
        assert m.group("level") == "WARNING"

    def test_rejects_garbage(self):
        assert _DAEMON_LOG_LINE_RE.match("Traceback (most recent call last):") is None
        assert _DAEMON_LOG_LINE_RE.match("") is None

    def test_parse_returns_none_for_garbage(self):
        assert _parse_daemon_log_line("Traceback (most recent call last):") is None
        assert _parse_daemon_log_line("") is None

    def test_parse_returns_tuple(self):
        out = _parse_daemon_log_line(_err(time.time(), msg="boom"))
        assert out is not None
        ts_epoch, level, msg = out
        assert level == "ERROR"
        assert msg == "boom"
        assert isinstance(ts_epoch, float)


# ── Tail-reader tests ──────────────────────────────────────────────────────────


class TestTailLines:
    def test_missing_file_returns_empty(self, tmp_path):
        assert _tail_lines(str(tmp_path / "nope.log")) == []

    def test_reads_small_file(self, tmp_path):
        p = _write_log(tmp_path, ["a", "b", "c"])
        assert _tail_lines(p) == ["a", "b", "c"]

    def test_returns_last_n(self, tmp_path):
        p = _write_log(tmp_path, [f"line {i}" for i in range(5000)])
        out = _tail_lines(p, n=10)
        assert len(out) == 10
        assert out[-1] == "line 4999"


# ── compute_daemon_health() — the contract surface ────────────────────────────


class TestComputeDaemonHealth:
    def test_missing_log_is_healthy(self, tmp_path):
        path = str(tmp_path / "absent.log")
        out = compute_daemon_health(log_path=path)
        assert out["log_present"] is False
        assert out["errors_last_5min"] == 0
        assert out["errors_last_1h"] == 0
        assert out["last_error_message"] is None
        assert out["last_error_ts"] is None
        assert out["status"] == "healthy"
        assert out["log_path"] == path

    def test_empty_log_is_healthy(self, tmp_path):
        p = _write_log(tmp_path, [])
        out = compute_daemon_health(log_path=p)
        assert out["log_present"] is True
        assert out["errors_last_5min"] == 0
        assert out["status"] == "healthy"
        assert out["last_error_message"] is None

    def test_only_info_lines_is_healthy(self, tmp_path):
        now = time.time()
        p = _write_log(tmp_path, [_info(now - i) for i in range(20)])
        out = compute_daemon_health(log_path=p, now=now)
        assert out["errors_last_5min"] == 0
        assert out["errors_last_1h"] == 0
        assert out["status"] == "healthy"

    def test_warnings_dont_count_as_errors(self, tmp_path):
        now = time.time()
        p = _write_log(tmp_path, [_warn(now - i * 5) for i in range(10)])
        out = compute_daemon_health(log_path=p, now=now)
        assert out["errors_last_5min"] == 0
        assert out["status"] == "healthy"

    def test_few_recent_errors_is_degraded(self, tmp_path):
        # 3 errors in the last 5 min — above 0, well below 30.
        now = time.time()
        lines = [_err(now - 30, msg="boom one"), _err(now - 60, msg="boom two"),
                 _err(now - 90, msg="boom three")]
        p = _write_log(tmp_path, lines)
        out = compute_daemon_health(log_path=p, now=now)
        assert out["errors_last_5min"] == 3
        assert out["errors_last_1h"] == 3
        assert out["status"] == "degraded"
        assert out["last_error_ts"] is not None
        # Most recent line's message wins.
        assert out["last_error_message"] == "boom one"

    def test_50_recent_errors_is_broken(self, tmp_path):
        # 50 errors all within the last 5 min — exceeds the 30 threshold.
        now = time.time()
        lines = [_err(now - i, msg=f"boom {i}") for i in range(50)]
        p = _write_log(tmp_path, lines)
        out = compute_daemon_health(log_path=p, now=now)
        assert out["errors_last_5min"] == 50
        assert out["errors_last_1h"] == 50
        assert out["status"] == "broken"
        assert out["last_error_message"] == "boom 0"

    def test_old_errors_outside_1h_dont_count(self, tmp_path):
        # 5 errors from 2 hours ago — neither window picks them up.
        now = time.time()
        lines = [_err(now - 7200 - i, msg=f"ancient {i}") for i in range(5)]
        p = _write_log(tmp_path, lines)
        out = compute_daemon_health(log_path=p, now=now)
        assert out["errors_last_5min"] == 0
        assert out["errors_last_1h"] == 0
        assert out["status"] == "healthy"
        # The most-recent ERROR line still surfaces in last_error_message
        # (the user wants to know the daemon DID have errors at some point).
        assert out["last_error_message"] is not None
        assert out["last_error_message"].startswith("ancient")

    def test_mixed_window_buckets(self, tmp_path):
        # 2 errors in the last 5 min, 8 more between 5-60 min, 4 more older.
        now = time.time()
        lines = []
        lines += [_err(now - 30, msg="recent A"), _err(now - 200, msg="recent B")]
        lines += [_err(now - 600 - i * 60, msg=f"mid {i}") for i in range(8)]
        lines += [_err(now - 7200 - i, msg=f"old {i}") for i in range(4)]
        # Throw in some non-error noise to make sure it's filtered.
        lines += [_info(now - 10), _warn(now - 20)]
        p = _write_log(tmp_path, lines)
        out = compute_daemon_health(log_path=p, now=now)
        assert out["errors_last_5min"] == 2
        assert out["errors_last_1h"] == 10  # 2 recent + 8 mid
        assert out["status"] == "degraded"
        assert out["last_error_message"] == "recent A"

    def test_truncates_very_long_message(self, tmp_path):
        now = time.time()
        big = "x" * 5000
        p = _write_log(tmp_path, [_err(now - 10, msg=big)])
        out = compute_daemon_health(log_path=p, now=now)
        assert out["last_error_message"] is not None
        assert len(out["last_error_message"]) <= 500

    def test_iso_timestamp_is_utc(self, tmp_path):
        now = time.time()
        p = _write_log(tmp_path, [_err(now - 5, msg="probe")])
        out = compute_daemon_health(log_path=p, now=now)
        assert out["last_error_ts"] is not None
        # ISO-8601 with explicit timezone offset.
        assert "T" in out["last_error_ts"]
        assert out["last_error_ts"].endswith("+00:00") or "Z" in out["last_error_ts"]

    def test_garbage_lines_dont_crash(self, tmp_path):
        now = time.time()
        lines = [
            "Traceback (most recent call last):",
            '  File "/foo/bar.py", line 12, in <module>',
            "    raise SystemExit(1)",
            _err(now - 30, msg="real error"),
            "",
            "garbage \x00 line",
        ]
        p = _write_log(tmp_path, lines)
        out = compute_daemon_health(log_path=p, now=now)
        # Only the one ERROR line counts; garbage is silently dropped.
        assert out["errors_last_5min"] == 1
        assert out["last_error_message"] == "real error"


class TestEnvOverride:
    def test_clawmetry_home_env_var_changes_default_path(self, tmp_path, monkeypatch):
        monkeypatch.setenv("CLAWMETRY_HOME", str(tmp_path))
        # No log written — should be log_present=False but pointed at our tmp.
        out = compute_daemon_health()
        assert out["log_path"] == str(tmp_path / "sync.log")
        assert out["log_present"] is False
        assert out["status"] == "healthy"
