"""
Verifies the default-ON behaviour of ``CLAWMETRY_LOCAL_STORE_READ``.

Background — see PR ``feat/duckdb-default-on-2026-05-13``. Phase 1-5 DuckDB
fast paths shipped behind an opt-in env var that no installer set, so 100%
of installs silently fell through to the legacy gateway/JSONL paths even
though the daemon was happily writing to the local store. The flip moves
the default to ON; the gate now only matters when an operator explicitly
opts back out (e.g. for A/B comparisons or to bypass a corrupt store).

These tests pin the helper's truth table so a future tweak to the
disable-set or default value can't silently re-break the MOAT.
"""

import pytest

from clawmetry.config import is_local_store_read_enabled


def test_unset_is_enabled(monkeypatch):
    """Unset env var → fast path is ON. This is THE bug-fix assertion."""
    monkeypatch.delenv("CLAWMETRY_LOCAL_STORE_READ", raising=False)
    assert is_local_store_read_enabled() is True


@pytest.mark.parametrize("value", ["1", "true", "TRUE", "yes", "Yes", "on", "ON", "anything-else"])
def test_truthy_values_enabled(monkeypatch, value):
    """Any value not in the disable set keeps the fast path ON."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", value)
    assert is_local_store_read_enabled() is True


@pytest.mark.parametrize("value", ["0", "false", "False", "FALSE", "no", "NO", "off", "OFF", ""])
def test_disable_values_off(monkeypatch, value):
    """Explicit disable values turn the fast path OFF.

    Empty string is treated as disable so ``CLAWMETRY_LOCAL_STORE_READ=``
    behaves the same as ``=0`` (matches the helper's documented contract).
    """
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", value)
    assert is_local_store_read_enabled() is False


def test_whitespace_is_stripped(monkeypatch):
    """Leading/trailing whitespace doesn't sneak past the disable check —
    matters because shell heredocs/k8s configmaps occasionally add a
    trailing newline to env values."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "  0  ")
    assert is_local_store_read_enabled() is False
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "  1  ")
    assert is_local_store_read_enabled() is True
