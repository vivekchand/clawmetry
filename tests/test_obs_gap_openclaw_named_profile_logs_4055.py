"""Tests for #4055 — named-profile gateway logs never ingested.

Verifies that _DEFAULT_LOG_RE (and therefore _gateway_log_files) accepts
named-profile log filenames (openclaw-{name}-YYYY-MM-DD.log) in addition to
the default-profile form (openclaw-YYYY-MM-DD.log).

Fingerprint: hgap-9676a71686
"""
from __future__ import annotations

import re

import pytest

from clawmetry.adapters.openclaw import _DEFAULT_LOG_RE, _gateway_log_files


# ---------------------------------------------------------------------------
# Regex unit tests — fast, no filesystem
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("filename", [
    "openclaw-2026-07-26.log",            # default profile
    "openclaw-work-2026-07-26.log",       # --profile work
    "openclaw-prod-2026-01-01.log",       # --profile prod
    "openclaw-my-profile-2025-12-31.log", # multi-word profile name with dashes
])
def test_regex_matches_valid_log_filenames(filename):
    assert _DEFAULT_LOG_RE.search(filename), f"should match: {filename}"


@pytest.mark.parametrize("filename", [
    "openclaw-debug.log",          # no date suffix
    "openclaw.log",                # no date at all
    "openclaw-work.log",           # profile name only, no date
    "openclaw-2026-07-26.log.bak", # backup file
])
def test_regex_rejects_non_log_filenames(filename):
    assert not _DEFAULT_LOG_RE.search(filename), f"should NOT match: {filename}"


# ---------------------------------------------------------------------------
# Integration: _gateway_log_files() picks up named-profile log files
# ---------------------------------------------------------------------------

def test_named_profile_log_file_is_returned(monkeypatch, tmp_path):
    """A named-profile log file is returned by _gateway_log_files()."""
    log = tmp_path / "openclaw-work-2026-07-26.log"
    log.write_text("{}\n", encoding="utf-8")

    monkeypatch.setenv("CLAWMETRY_OPENCLAW_DIR", str(tmp_path))
    monkeypatch.setattr(
        "clawmetry.adapters.openclaw.glob.glob",
        lambda pattern: [str(log)] if "openclaw-*.log" in pattern and str(tmp_path) in pattern else [],
    )

    result = _gateway_log_files()
    assert str(log) in result


def test_default_profile_log_still_returned(monkeypatch, tmp_path):
    """The original default-profile log filename is still matched after the fix."""
    log = tmp_path / "openclaw-2026-07-26.log"
    log.write_text("{}\n", encoding="utf-8")

    monkeypatch.setenv("CLAWMETRY_OPENCLAW_DIR", str(tmp_path))
    monkeypatch.setattr(
        "clawmetry.adapters.openclaw.glob.glob",
        lambda pattern: [str(log)] if "openclaw-*.log" in pattern and str(tmp_path) in pattern else [],
    )

    result = _gateway_log_files()
    assert str(log) in result


def test_both_default_and_named_profile_logs_returned(monkeypatch, tmp_path):
    """When both default and named-profile logs exist, both are candidates."""
    default_log = tmp_path / "openclaw-2026-07-25.log"
    named_log = tmp_path / "openclaw-work-2026-07-26.log"
    default_log.write_text("{}\n", encoding="utf-8")
    named_log.write_text("{}\n", encoding="utf-8")

    all_files = [str(default_log), str(named_log)]

    monkeypatch.setenv("CLAWMETRY_OPENCLAW_DIR", str(tmp_path))
    monkeypatch.setattr(
        "clawmetry.adapters.openclaw.glob.glob",
        lambda pattern: all_files if "openclaw-*.log" in pattern and str(tmp_path) in pattern else [],
    )

    result = _gateway_log_files()
    assert str(default_log) in result
    assert str(named_log) in result
