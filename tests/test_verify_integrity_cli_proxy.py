"""Regression coverage for the verify-integrity CLI → daemon-proxy path.

The integrity hash chain ships in 0.12.342 (#2200 / #2210). Live verification
caught a crash: ``clawmetry verify-integrity`` calls
``get_store(read_only=True)`` which returns the proxy when a daemon is running,
the proxy forwards the call through HTTP, and the HTTP dispatch allowlist did
not include ``verify_integrity`` — so the proxy returned ``None`` and the CLI
crashed on ``result["status"]``.

This file pins both halves of the fix so it cannot regress:

1. ``verify_integrity`` is in the daemon-side ``_DAEMON_METHODS`` allowlist.
2. The CLI prints a clear message and exits 2 instead of crashing when the
   proxy returns ``None`` (older daemon, daemon unreachable, etc.).
"""

from __future__ import annotations

import io
import sys

import pytest


def test_verify_integrity_is_in_daemon_method_allowlist():
    from routes.local_query import _DAEMON_METHODS
    assert "verify_integrity" in _DAEMON_METHODS, (
        "verify_integrity must be allowlisted so `clawmetry verify-integrity`"
        " works when the dashboard/CLI talks to the daemon over HTTP (the"
        " daemon holds DuckDB's process-level writer lock and any direct"
        " read-only open from another process is rejected)."
    )


def test_cli_handles_proxy_returning_none_without_crashing(monkeypatch, capsys):
    """Old-daemon scenario: ``store.verify_integrity()`` returns None
    (because the running daemon predates this fix). The CLI must not raise
    ``TypeError: 'NoneType' object is not subscriptable``."""
    from clawmetry import cli

    class _NoneStore:
        def verify_integrity(self, node_id=None):  # noqa: ARG002
            return None

    monkeypatch.setattr(cli, "_cmd_verify_integrity",
                        cli._cmd_verify_integrity)  # ensure name exists
    monkeypatch.setattr("clawmetry.local_store.get_store",
                        lambda read_only=True: _NoneStore())

    class _Args:
        node_id = None

    with pytest.raises(SystemExit) as ei:
        cli._cmd_verify_integrity(_Args())
    # Exit code 2 (specific signal for "could not verify, environment
    # problem"), not 1 (chain invalid) and not 0 (success).
    assert ei.value.code == 2
    captured = capsys.readouterr()
    assert "Could not reach" in captured.out
    assert "Restart the sync daemon" in captured.out


def test_cli_still_reports_invalid_when_real_break_detected(monkeypatch, capsys):
    """Make sure the graceful-None path didn't break the normal invalid-chain
    branch."""
    from clawmetry import cli

    class _BrokenStore:
        def verify_integrity(self, node_id=None):  # noqa: ARG002
            return {
                "status": "invalid",
                "node_id": "all",
                "checked": 3,
                "pre_chain": 0,
                "broken_at": "evt-3",
                "error": "chain break at event evt-3",
            }

    monkeypatch.setattr("clawmetry.local_store.get_store",
                        lambda read_only=True: _BrokenStore())

    class _Args:
        node_id = None

    with pytest.raises(SystemExit) as ei:
        cli._cmd_verify_integrity(_Args())
    assert ei.value.code == 1
    captured = capsys.readouterr()
    assert "INVALID" in captured.out
    assert "evt-3" in captured.out
