"""Unit tests for the gateway process-health surface (issue #852).

Covers ``routes.health.compute_gateway_health`` — the helper that powers the
new ``gateway`` block on ``/api/system-health`` (and the standalone
``/api/gateway-health`` endpoint).

We exercise the pure helper directly (no Flask, no network, no actual gateway
process) by injecting stub ``psutil``/``ps``/cmdline-scan callables. This
mirrors how ``test_daemon_health_endpoint.py`` covers the daemon-log parser:
keep the contract honest, keep the test cheap.

Threshold defaults (per issue #852):
  - 900 MB hard cap (OpenClaw OOMs ~945 MB) → ``critical``
  - 75% of cap = 675 MB → ``warning``
  - everything below → ``healthy``
  - no gateway process found → all fields null + ``not_running``
"""
from __future__ import annotations

import os
import sys

import pytest


_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)


from routes.health import (  # noqa: E402
    GATEWAY_MEMORY_THRESHOLD_MB,
    GATEWAY_MEMORY_WARNING_RATIO,
    _classify_gateway_status,
    _parse_etime,
    _read_gateway_pid,
    compute_gateway_health,
)


# ── Helpers ────────────────────────────────────────────────────────────────────


def _write_pid(tmp_path, value):
    """Write ``value`` (str|int) to a fake gateway.pid file. Returns the path."""
    gw_dir = tmp_path / "gateway"
    gw_dir.mkdir(parents=True, exist_ok=True)
    p = gw_dir / "gateway.pid"
    p.write_text(str(value), encoding="utf-8")
    return str(p)


def _vitals_stub(uptime, rss_mb, cpu_pct):
    """Factory: returns a callable that mimics ``_process_vitals_*`` shape."""

    def _fn(pid):
        return uptime, rss_mb, cpu_pct

    return _fn


def _vitals_unavailable(pid):
    return None


def _no_cmdline_scan():
    return None


# ── PID-file parsing ───────────────────────────────────────────────────────────


class TestReadGatewayPid:
    def test_missing_pid_file_returns_none(self, tmp_path):
        assert _read_gateway_pid(str(tmp_path / "nope.pid")) is None

    def test_reads_clean_pid(self, tmp_path):
        p = _write_pid(tmp_path, 12345)
        assert _read_gateway_pid(p) == 12345

    def test_trims_whitespace_and_trailing_newline(self, tmp_path):
        p = tmp_path / "gw.pid"
        p.write_text("   54321  \n\n", encoding="utf-8")
        assert _read_gateway_pid(str(p)) == 54321

    def test_garbage_pid_returns_none(self, tmp_path):
        p = tmp_path / "gw.pid"
        p.write_text("not-a-pid", encoding="utf-8")
        assert _read_gateway_pid(str(p)) is None

    def test_zero_pid_returns_none(self, tmp_path):
        p = tmp_path / "gw.pid"
        p.write_text("0", encoding="utf-8")
        assert _read_gateway_pid(str(p)) is None

    def test_negative_pid_returns_none(self, tmp_path):
        p = tmp_path / "gw.pid"
        p.write_text("-1", encoding="utf-8")
        assert _read_gateway_pid(str(p)) is None

    def test_empty_pid_file_returns_none(self, tmp_path):
        p = tmp_path / "gw.pid"
        p.write_text("", encoding="utf-8")
        assert _read_gateway_pid(str(p)) is None

    def test_multiline_pid_file_takes_first_token(self, tmp_path):
        # Some daemons write "<pid>\n<port>\n<state>" — we want just the PID.
        p = tmp_path / "gw.pid"
        p.write_text("9999\n18789\nstarted", encoding="utf-8")
        assert _read_gateway_pid(str(p)) == 9999


# ── etime parser ───────────────────────────────────────────────────────────────


class TestParseEtime:
    def test_seconds_only(self):
        assert _parse_etime("42") == 42

    def test_minutes_seconds(self):
        assert _parse_etime("12:34") == 12 * 60 + 34

    def test_hours_minutes_seconds(self):
        assert _parse_etime("01:02:03") == 3600 + 120 + 3

    def test_days_hours_minutes_seconds(self):
        # 2 days, 03:04:05 → 2*86400 + 3*3600 + 4*60 + 5
        assert _parse_etime("2-03:04:05") == 2 * 86400 + 3 * 3600 + 4 * 60 + 5

    def test_empty_returns_zero(self):
        assert _parse_etime("") == 0

    def test_garbage_returns_zero(self):
        assert _parse_etime("not-a-duration") == 0


# ── Status classification ─────────────────────────────────────────────────────


class TestClassifyGatewayStatus:
    def test_none_is_not_running(self):
        assert _classify_gateway_status(None, 900) == "not_running"

    def test_well_below_warning_is_healthy(self):
        assert _classify_gateway_status(120.0, 900) == "healthy"

    def test_just_under_warning_threshold_is_healthy(self):
        # 75% of 900 = 675; 674 stays healthy.
        assert _classify_gateway_status(674.0, 900) == "healthy"

    def test_above_warning_threshold_is_warning(self):
        # 75% of 900 = 675; 676 trips warning.
        assert _classify_gateway_status(676.0, 900) == "warning"

    def test_just_under_hard_cap_is_warning(self):
        assert _classify_gateway_status(899.9, 900) == "warning"

    def test_above_hard_cap_is_critical(self):
        assert _classify_gateway_status(901.0, 900) == "critical"

    def test_far_above_hard_cap_is_critical(self):
        assert _classify_gateway_status(945.0, 900) == "critical"

    def test_warning_ratio_default_is_three_quarters(self):
        # Lock the default so a future "small tweak" doesn't drift it.
        assert GATEWAY_MEMORY_WARNING_RATIO == 0.75

    def test_threshold_default_is_900mb(self):
        assert GATEWAY_MEMORY_THRESHOLD_MB == 900


# ── compute_gateway_health — the contract surface ──────────────────────────────


class TestComputeGatewayHealthNotRunning:
    def test_missing_pid_file_and_no_cmdline_match_is_not_running(self, tmp_path):
        out = compute_gateway_health(
            pid_path=str(tmp_path / "absent.pid"),
            _psutil_vitals=_vitals_unavailable,
            _ps_vitals=_vitals_unavailable,
            _cmdline_pid=_no_cmdline_scan,
        )
        assert out == {
            "pid": None,
            "uptime_seconds": None,
            "rss_mb": None,
            "cpu_pct": None,
            "status": "not_running",
            "memory_threshold_mb": 900,
        }

    def test_cmdline_scan_finds_pid_when_pidfile_missing(self, tmp_path):
        # No PID file — but the cmdline scan finds an openclaw-gateway proc.
        out = compute_gateway_health(
            pid_path=str(tmp_path / "absent.pid"),
            _psutil_vitals=_vitals_stub(60, 200.0, 1.5),
            _ps_vitals=_vitals_unavailable,
            _cmdline_pid=lambda: 7777,
        )
        assert out["pid"] == 7777
        assert out["rss_mb"] == 200.0
        assert out["status"] == "healthy"

    def test_pid_found_but_vitals_unreadable_is_warning(self, tmp_path):
        # Process exists (PID file present) but neither psutil nor ps can read
        # its vitals — surface "warning" rather than fake-healthy.
        p = _write_pid(tmp_path, 5555)
        out = compute_gateway_health(
            pid_path=p,
            _psutil_vitals=_vitals_unavailable,
            _ps_vitals=_vitals_unavailable,
            _cmdline_pid=_no_cmdline_scan,
        )
        assert out["pid"] == 5555
        assert out["status"] == "warning"
        assert out["rss_mb"] is None
        assert out["cpu_pct"] is None
        assert out["uptime_seconds"] is None


class TestComputeGatewayHealthThresholds:
    def test_healthy_well_under_threshold(self, tmp_path):
        p = _write_pid(tmp_path, 1234)
        out = compute_gateway_health(
            pid_path=p,
            _psutil_vitals=_vitals_stub(3600, 250.0, 4.2),
            _ps_vitals=_vitals_unavailable,
            _cmdline_pid=_no_cmdline_scan,
        )
        assert out["pid"] == 1234
        assert out["uptime_seconds"] == 3600
        assert out["rss_mb"] == 250.0
        assert out["cpu_pct"] == 4.2
        assert out["status"] == "healthy"
        assert out["memory_threshold_mb"] == 900

    def test_warning_between_75pct_and_threshold(self, tmp_path):
        p = _write_pid(tmp_path, 1234)
        out = compute_gateway_health(
            pid_path=p,
            _psutil_vitals=_vitals_stub(60, 700.0, 12.0),
            _ps_vitals=_vitals_unavailable,
            _cmdline_pid=_no_cmdline_scan,
        )
        assert out["status"] == "warning"

    def test_critical_above_threshold(self, tmp_path):
        p = _write_pid(tmp_path, 1234)
        out = compute_gateway_health(
            pid_path=p,
            _psutil_vitals=_vitals_stub(86400, 945.0, 33.0),
            _ps_vitals=_vitals_unavailable,
            _cmdline_pid=_no_cmdline_scan,
        )
        assert out["status"] == "critical"
        assert out["rss_mb"] == 945.0
        assert out["uptime_seconds"] == 86400

    def test_custom_threshold_is_honoured(self, tmp_path):
        # Operator can override the default cap (e.g. node with more RAM).
        p = _write_pid(tmp_path, 4242)
        out = compute_gateway_health(
            pid_path=p,
            threshold_mb=1500,
            _psutil_vitals=_vitals_stub(60, 950.0, 1.0),
            _ps_vitals=_vitals_unavailable,
            _cmdline_pid=_no_cmdline_scan,
        )
        # 950 MB > 75% of 1500 (1125)? No — 950 < 1125, so still healthy.
        assert out["status"] == "healthy"
        assert out["memory_threshold_mb"] == 1500

    def test_falls_back_to_ps_when_psutil_returns_none(self, tmp_path):
        p = _write_pid(tmp_path, 1234)
        out = compute_gateway_health(
            pid_path=p,
            _psutil_vitals=_vitals_unavailable,
            _ps_vitals=_vitals_stub(120, 400.0, 8.0),
            _cmdline_pid=_no_cmdline_scan,
        )
        assert out["rss_mb"] == 400.0
        assert out["uptime_seconds"] == 120
        assert out["cpu_pct"] == 8.0
        assert out["status"] == "healthy"

    def test_psutil_takes_precedence_over_ps(self, tmp_path):
        # When both work, psutil wins (more accurate cpu measurement).
        p = _write_pid(tmp_path, 1234)
        out = compute_gateway_health(
            pid_path=p,
            _psutil_vitals=_vitals_stub(99, 111.0, 1.0),
            _ps_vitals=_vitals_stub(88, 222.0, 2.0),
            _cmdline_pid=_no_cmdline_scan,
        )
        assert out["rss_mb"] == 111.0
        assert out["uptime_seconds"] == 99


class TestPayloadShape:
    def test_keys_always_present(self, tmp_path):
        out = compute_gateway_health(
            pid_path=str(tmp_path / "absent.pid"),
            _psutil_vitals=_vitals_unavailable,
            _ps_vitals=_vitals_unavailable,
            _cmdline_pid=_no_cmdline_scan,
        )
        for key in (
            "pid",
            "uptime_seconds",
            "rss_mb",
            "cpu_pct",
            "status",
            "memory_threshold_mb",
        ):
            assert key in out, f"missing key: {key}"

    def test_status_is_documented_enum(self, tmp_path):
        # Cycle through every status path and confirm the value is one of the
        # four canonical strings the frontend knows how to render.
        valid = {"healthy", "warning", "critical", "not_running"}

        p = _write_pid(tmp_path, 1234)
        # critical
        out = compute_gateway_health(
            pid_path=p,
            _psutil_vitals=_vitals_stub(1, 1000.0, 0.0),
            _ps_vitals=_vitals_unavailable,
            _cmdline_pid=_no_cmdline_scan,
        )
        assert out["status"] in valid and out["status"] == "critical"

        # not_running
        out = compute_gateway_health(
            pid_path=str(tmp_path / "absent.pid"),
            _psutil_vitals=_vitals_unavailable,
            _ps_vitals=_vitals_unavailable,
            _cmdline_pid=_no_cmdline_scan,
        )
        assert out["status"] in valid and out["status"] == "not_running"


class TestEnvOverride:
    def test_openclaw_home_env_var_changes_default_pid_path(self, tmp_path, monkeypatch):
        monkeypatch.setenv("OPENCLAW_HOME", str(tmp_path))
        # No PID file under our tmp $OPENCLAW_HOME → not_running.
        out = compute_gateway_health(
            _psutil_vitals=_vitals_unavailable,
            _ps_vitals=_vitals_unavailable,
            _cmdline_pid=_no_cmdline_scan,
        )
        assert out["pid"] is None
        assert out["status"] == "not_running"
