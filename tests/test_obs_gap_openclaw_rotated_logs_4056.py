"""Tests for #4056 -- rotated log archives (.N.log) included in _gateway_log_files().

_DEFAULT_LOG_RE previously required the date to be immediately followed by
'.log', so rotation archives like openclaw-2026-07-20.1.log were silently
dropped.  The fix extends the regex with an optional '(\\.\\d+)?' group so
numbered rotation archives are included alongside the active log file.

Also covers named-profile rotation archives (openclaw-work-YYYY-MM-DD.N.log)
made possible by the combined pattern from #4055 + #4056.

Fingerprint: hgap-cd81abf74f-rotated
"""
from __future__ import annotations

import os

import pytest

from clawmetry.adapters.openclaw import _DEFAULT_LOG_RE, _gateway_log_files


# ---------------------------------------------------------------------------
# Regex unit tests
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("name", [
    "openclaw-2026-07-20.log",
    "openclaw-2026-07-20.1.log",
    "openclaw-2026-07-20.2.log",
    "openclaw-2026-07-20.5.log",
    "openclaw-2025-01-01.log",
    "openclaw-2025-01-01.3.log",
    "openclaw-work-2026-07-20.log",        # named profile (#4055)
    "openclaw-work-2026-07-20.1.log",      # named profile rotation archive
    "openclaw-prod-2026-07-20.3.log",      # named profile rotation archive
])
def test_regex_matches_valid_names(name):
    assert _DEFAULT_LOG_RE.search(name), f"{name!r} should match"


@pytest.mark.parametrize("name", [
    "openclaw-2026-07-20.log.gz",        # compressed
    "openclaw-2026-07-20.abc.log",       # non-numeric suffix
    "other-2026-07-20.log",              # wrong prefix
])
def test_regex_rejects_invalid_names(name):
    assert not _DEFAULT_LOG_RE.search(name), f"{name!r} should not match"


# ---------------------------------------------------------------------------
# _gateway_log_files() integration tests
# ---------------------------------------------------------------------------

def _populate_dir(d, filenames):
    """Create empty files in directory d; return sorted absolute paths."""
    paths = []
    for name in filenames:
        p = d / name
        p.write_text("", encoding="utf-8")
        paths.append(str(p))
    return sorted(paths)


def test_rotation_archives_included(monkeypatch, tmp_path):
    """Rotation archives appear in the result alongside the base log file."""
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    expected = _populate_dir(log_dir, [
        "openclaw-2026-07-20.log",
        "openclaw-2026-07-20.1.log",
        "openclaw-2026-07-20.2.log",
    ])

    monkeypatch.setenv("CLAWMETRY_OPENCLAW_DIR", str(tmp_path))

    result = _gateway_log_files()
    assert sorted(result) == sorted(expected)


def test_rotation_archives_capped_at_five(monkeypatch, tmp_path):
    """Result is limited to the 5 lexicographically-last files."""
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    _populate_dir(log_dir, [
        "openclaw-2026-07-19.log",
        "openclaw-2026-07-20.log",
        "openclaw-2026-07-20.1.log",
        "openclaw-2026-07-20.2.log",
        "openclaw-2026-07-20.3.log",
        "openclaw-2026-07-20.4.log",
        "openclaw-2026-07-20.5.log",
    ])

    monkeypatch.setenv("CLAWMETRY_OPENCLAW_DIR", str(tmp_path))

    result = _gateway_log_files()
    assert len(result) == 5


def test_named_profile_rotation_archives_included(monkeypatch, tmp_path):
    """Named-profile rotation archives are included along with default-profile files."""
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    _populate_dir(log_dir, [
        "openclaw-2026-07-20.log",          # default profile
        "openclaw-2026-07-20.1.log",        # rotation archive
        "openclaw-work-2026-07-20.log",     # named profile (#4055)
        "openclaw-work-2026-07-20.1.log",   # named profile rotation archive
    ])

    monkeypatch.setenv("CLAWMETRY_OPENCLAW_DIR", str(tmp_path))

    result = _gateway_log_files()
    basenames = [os.path.basename(p) for p in result]
    assert "openclaw-2026-07-20.log" in basenames
    assert "openclaw-2026-07-20.1.log" in basenames
    assert "openclaw-work-2026-07-20.log" in basenames
    assert "openclaw-work-2026-07-20.1.log" in basenames


def test_no_logs_returns_empty(monkeypatch, tmp_path):
    """Empty candidate directories give an empty list, no exception."""
    log_dir = tmp_path / "logs"
    log_dir.mkdir()

    monkeypatch.setenv("CLAWMETRY_OPENCLAW_DIR", str(tmp_path))

    result = _gateway_log_files()
    assert result == []
