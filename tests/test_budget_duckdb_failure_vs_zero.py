"""Guard: a failed DuckDB cost read is never published as $0.00.

Reported 2026-08-22 by a paying customer: the dashboard's cost numbers
"sporadically toggle" between two sets of values every few seconds.

``_get_budget_status`` makes THREE independent ``_duckdb_cost_since`` calls
(daily / weekly / monthly). Pre-fix each returned 0.0 on ANY exception, so a
transient daemon-proxy timeout or DuckDB writer-lock contention on one call
while another succeeded published a triple that mixed a real number with a
failure-zero, then flipped back on the next poll.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

import dashboard as _d


def test_failed_read_returns_none_not_zero(monkeypatch):
    """Both the proxy path and the direct path failing means UNKNOWN."""
    def _boom(*a, **k):
        raise RuntimeError("daemon proxy timeout")

    monkeypatch.setattr(
        "routes.local_query.local_store_via_daemon", _boom, raising=False
    )
    import clawmetry.local_store as _ls
    monkeypatch.setattr(_ls, "get_store", _boom, raising=False)

    assert _d._duckdb_cost_since("2026-08-22T00:00:00+00:00") is None


def test_empty_store_is_zero_not_none(monkeypatch):
    """A store that answers with no rows genuinely cost $0.00."""
    monkeypatch.setattr(
        "routes.local_query.local_store_via_daemon",
        lambda *a, **k: [],
        raising=False,
    )
    assert _d._duckdb_cost_since("2026-08-22T00:00:00+00:00") == 0.0


def _budget_with(monkeypatch, values):
    """Run _get_budget_status with _duckdb_cost_since returning `values` in
    call order (daily, weekly, monthly), and an empty OTLP ring."""
    calls = iter(values)
    monkeypatch.setattr(_d, "_duckdb_cost_since", lambda *_a, **_k: next(calls))
    monkeypatch.setattr(_d, "_otel_cost_is_fresh", lambda *_a, **_k: False)
    with _d._metrics_lock:
        _d.metrics_store["cost"] = []
    return _d._get_budget_status()


def test_partial_failure_never_publishes_a_mixed_triple(monkeypatch):
    """Daily read fails, monthly succeeds.

    Pre-fix: daily=0.0 (a failure) was published beside monthly=24.11 (a
    fact), because `duck_monthly > 0` alone promoted the whole triple.
    """
    out = _budget_with(monkeypatch, [None, 7.25, 24.11])
    assert out["daily_spent"] == 0.0
    assert out["monthly_spent"] == 0.0, (
        "a failure-zero daily was published next to a real monthly: "
        "the triple mixed fact and failure"
    )


def test_all_reads_succeed_still_promotes(monkeypatch):
    """The fix must not break the common path it was built for (#1404)."""
    out = _budget_with(monkeypatch, [1.72, 8.58, 21.26])
    assert out["daily_spent"] == 1.72
    assert out["weekly_spent"] == 8.58
    assert out["monthly_spent"] == 21.26


def test_genuinely_idle_store_reports_zero(monkeypatch):
    """All three succeed and are zero: an idle node, not a broken one."""
    out = _budget_with(monkeypatch, [0.0, 0.0, 0.0])
    assert out["daily_spent"] == 0.0
    assert out["monthly_spent"] == 0.0
