"""The Quality tab's marks line — snapshot slice + live template.

Two gates from FLYWHEEL that this card would otherwise fail silently:

§0a.1 (cloud parity) — the hosted dashboard has no local DuckDB, so a card
that only fetches ``/api/outcomes/trend`` renders blank there. The daemon has
to bake an ``outcomesTrend`` slice into the snapshot for a cloud interceptor
to serve. If that slice ever stops being emitted, this test says so.

§0a.4 (no dead UI) — ``dashboard.py`` defines ``DASHBOARD_HTML`` twice and
only the second one renders. Markup is proven by an actual Jinja render, not
assumed, so an element that only exists in the dead block can't pass review.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest


def _iso(days_ago: float) -> str:
    return (
        datetime.now(timezone.utc) - timedelta(days=days_ago)
    ).isoformat().replace("+00:00", "Z")


class _StubStore:
    """Stands in for the daemon's writer-locked DuckDB handle."""

    def __init__(self, rows):
        self._rows = rows
        self.calls = []

    def query_outcomes(self, **kwargs):
        self.calls.append(kwargs)
        return self._rows


@pytest.fixture
def sync_mod():
    return pytest.importorskip("clawmetry.sync")


# ── the snapshot slice ──────────────────────────────────────────────────────


def test_trend_slice_splits_the_fourteen_day_read_into_two_weeks(
    sync_mod, monkeypatch
):
    rows = (
        [{"session_id": f"a{i}", "outcome": "success", "cost_usd": 1.0,
          "last_active_at": _iso(2)} for i in range(9)]
        + [{"session_id": "a9", "outcome": "failed", "cost_usd": 1.0,
            "last_active_at": _iso(2)}]
        + [{"session_id": f"b{i}", "outcome": "success", "cost_usd": 2.0,
            "last_active_at": _iso(10)} for i in range(5)]
        + [{"session_id": f"c{i}", "outcome": "failed", "cost_usd": 2.0,
            "last_active_at": _iso(10)} for i in range(5)]
    )
    store = _StubStore(rows)
    monkeypatch.setattr("clawmetry.local_store.get_store", lambda *a, **k: store)

    slice_ = sync_mod._outcomes_trend_slice_for_snapshot()

    assert slice_["store_available"] is True
    assert slice_["window"] == "7d"
    assert slice_["current"]["finished"] == 10
    assert slice_["previous"]["finished"] == 10
    assert slice_["current"]["success_rate"] == 0.9
    assert slice_["previous"]["success_rate"] == 0.5
    assert slice_["direction"] == "improving"
    # ONE read for both periods, not two.
    assert len(store.calls) == 1


def test_trend_slice_scopes_to_a_runtime(sync_mod, monkeypatch):
    """Per-runtime honesty (§0a.2): the switcher must not silently serve
    node-wide numbers."""
    store = _StubStore([])
    monkeypatch.setattr("clawmetry.local_store.get_store", lambda *a, **k: store)

    slice_ = sync_mod._outcomes_trend_slice_for_snapshot(runtime="claude_code")

    assert store.calls[0]["runtime"] == "claude_code"
    assert slice_["runtime"] == "claude_code"


def test_trend_slice_never_breaks_the_snapshot(sync_mod, monkeypatch):
    """A slice that raises must not take the whole encrypted snapshot down
    with it — every other slice in the payload still has to ship."""
    def _boom(*a, **k):
        raise RuntimeError("duckdb is busy")

    monkeypatch.setattr("clawmetry.local_store.get_store", _boom)
    assert sync_mod._outcomes_trend_slice_for_snapshot() == {}


def test_snapshot_payload_carries_the_trend_keys(sync_mod):
    """The slice is only worth building if it is actually attached. Pins the
    key names the cloud interceptor will read."""
    import inspect

    src = inspect.getsource(sync_mod)
    assert '"outcomesTrend": _outcomes_trend_slice_for_snapshot()' in src
    assert '"outcomesTrendByRuntime": _outcomes_trend_by_rt' in src


# ── the live template ───────────────────────────────────────────────────────


def _render_evals_tab():
    from jinja2 import Environment, FileSystemLoader

    env = Environment(loader=FileSystemLoader("clawmetry/templates"))
    return env.get_template("tabs/evals.html").render()


def test_marks_line_exists_in_the_rendered_tab():
    html = _render_evals_tab()
    for marker in ('id="q-outcomes"', 'id="q-oc-cells"', 'id="q-oc-note"'):
        assert marker in html, f"{marker} missing from the live Quality tab"


def test_marks_line_starts_hidden():
    """It reveals itself only once there is a finished task to report, so a
    fresh install sees the report card rather than a row of dashes."""
    html = _render_evals_tab()
    section = html[html.index('id="q-outcomes"'):]
    assert "hidden" in section[: section.index(">")]


def test_export_endpoint_is_findable_on_the_tab():
    """"Export instead of compete": if a buyer already runs an evaluation
    platform, the way to send them these runs has to be visible in the
    product, not only in the docs."""
    html = _render_evals_tab()
    assert "/api/otel/export?shape=sessions" in html
    assert "qCopyExportUrl" in html


def test_export_line_is_outside_the_judge_footer():
    """The judge nudge hides once a key is set (``_qRenderFooter``). The
    export line must not be inside it, or it disappears for exactly the
    users most likely to want it."""
    html = _render_evals_tab()
    footer_end = html.index("</footer>")
    assert html.index('class="q-export"') > footer_end
