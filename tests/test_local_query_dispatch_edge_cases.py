"""Deep edge-case coverage for the /api/local/* relay-dispatch boundary.

``routes/local_query.relay_dispatch`` (and the ``/api/local/*`` HTTP routes
that share its ``_coerce_args``) is the single query seam the dashboard, the
future WS relay, and the cloud heartbeat-piggyback ``pending_queries`` all go
through. It is a security + robustness boundary:

  * a shape ALLOWLIST (only events/sessions/aggregates/health/transcript) —
    an unknown shape must never reach a store method;
  * per-shape arg coercion that DROPS unknown kwargs — the root cause of the
    2026-05-18 "cloud shows 0 sessions" P0 was an extra ``node_id`` kwarg
    reaching a store method as a TypeError;
  * ``limit`` clamping to a safe range so a caller can't request a runaway
    scan or pass garbage.

These edge cases need no seeded data — they pin the boundary itself — so they
are fully deterministic. Hermetic store (forced direct, past any host daemon).
"""

from __future__ import annotations

import importlib

import pytest
from flask import Flask


@pytest.fixture
def lq_app(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")

    import clawmetry.local_store as ls
    importlib.reload(ls)
    monkeypatch.setattr(ls, "_daemon_registered", lambda *a, **k: False)
    monkeypatch.delenv("CLAWMETRY_ROLE", raising=False)
    import routes.local_query as lq
    importlib.reload(lq)
    # Force the read path direct (no daemon proxy) so dispatch hits the
    # in-process store; CI has no daemon so this is a no-op there.
    monkeypatch.setattr(lq, "_read_discovery", lambda: None)

    a = Flask(__name__)
    a.register_blueprint(lq.bp_local_query)
    ls.get_store()  # warm the store
    yield lq, a.test_client()
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


# ── shape allowlist (security) ──────────────────────────────────────────────


def test_unknown_shape_rejected_not_dispatched(lq_app):
    lq, _c = lq_app
    out = lq.relay_dispatch("definitely-not-a-shape", {"limit": 5})
    assert "error" in out and "unknown shape" in out["error"], (
        "an unknown shape must be rejected by the allowlist, never dispatched "
        f"to a store method; got {out!r}"
    )


def test_known_shapes_are_exactly_the_allowlist(lq_app):
    # Deliberately an EXPLICIT pin (not derived from the q/1 registry in
    # clawmetry/query_contract.py) so widening the relay-reachable query
    # surface always requires a reviewed two-place change. Registry/doc/
    # coercion cross-checks live in tests/test_query_contract_drift.py
    # (#2987). Was stale at 7 shapes (external_calls #883 + search #2860
    # landed without updating it; this file is not in the CI gate list).
    lq, _c = lq_app
    assert set(lq._SHAPES) == {"events", "sessions", "aggregates", "health",
                               "transcript", "spans", "traces",
                               "external_calls", "search",
                               # #2988 Query Spine P2: materialized-rollup
                               # backed shapes (models/runtimes plaintext
                               # aggregates; rollup_sessions e2e-classed).
                               "models", "runtimes", "rollup_sessions"}, (
        "the dispatch allowlist changed — review for new query surface before "
        "widening what the relay/cloud can ask the local store to run "
        f"(got {sorted(lq._SHAPES)})"
    )


# ── arg coercion: drop unknown kwargs (#P0 2026-05-18) ──────────────────────


def test_unknown_kwargs_dropped_no_typeerror(lq_app):
    """The cloud attaches routing metadata (e.g. node_id) the store methods
    don't accept. Coercion must DROP it so the call never TypeErrors — the
    exact regression behind 'cloud shows 0 sessions'."""
    lq, _c = lq_app
    out = lq.relay_dispatch("events", {
        "node_id": "agent+x", "bogus": 1, "session_id": "s", "limit": 3,
    })
    assert "error" not in out, f"unknown kwargs must be dropped, not error: {out!r}"
    assert out["_shape"] == "events"
    assert out["count"] == 0  # empty store, but the call succeeded


def test_coerce_drops_unknown_keys_for_every_shape(lq_app):
    lq, _c = lq_app
    for shape in ("events", "sessions", "aggregates"):
        coerced = lq._coerce_args(shape, {"evil": "x", "node_id": "n", "limit": 5})
        assert "evil" not in coerced and "node_id" not in coerced, (
            f"{shape}: coercion leaked an unknown kwarg: {coerced}"
        )


# ── limit clamping ──────────────────────────────────────────────────────────


def test_limit_clamped_high_low_and_garbage(lq_app):
    lq, _c = lq_app
    hi = lq._coerce_args("events", {"limit": 10_000_000})["limit"]
    lo = lq._coerce_args("events", {"limit": 0})["limit"]
    neg = lq._coerce_args("events", {"limit": -5})["limit"]
    garbage = lq._coerce_args("events", {"limit": "not-a-number"})["limit"]
    assert hi == 5000, f"huge limit must clamp to the events ceiling, got {hi}"
    assert lo >= 1 and neg >= 1, f"limit must clamp to >=1, got lo={lo} neg={neg}"
    assert garbage == 200, f"garbage limit must fall back to default, got {garbage}"


def test_safe_int_helper_bounds(lq_app):
    lq, _c = lq_app
    assert lq._safe_int("5", default=1, lo=1, hi=10) == 5
    assert lq._safe_int(999, default=1, lo=1, hi=10) == 10
    assert lq._safe_int(-3, default=1, lo=1, hi=10) == 1
    assert lq._safe_int(None, default=7, lo=1, hi=10) == 7
    assert lq._safe_int("abc", default=7, lo=1, hi=10) == 7


# ── required args ───────────────────────────────────────────────────────────


def test_transcript_without_session_id_raises(lq_app):
    lq, _c = lq_app
    with pytest.raises(ValueError):
        lq._coerce_args("transcript", {})


# ── HTTP surface mirrors the boundary ───────────────────────────────────────


def test_http_events_limit_garbage_is_200_not_500(lq_app):
    lq, c = lq_app
    r = c.get("/api/local/events?limit=not-a-number")
    assert r.status_code == 200, r.get_data(as_text=True)[:200]
    body = r.get_json()
    assert body["_shape"] == "events" and body["count"] == 0


def test_http_health_returns_ring_depth(lq_app):
    lq, c = lq_app
    r = c.get("/api/local/health")
    assert r.status_code == 200
    assert "ring_depth" in r.get_json()


def test_http_empty_store_endpoints_no_error(lq_app):
    lq, c = lq_app
    for path in ("/api/local/events", "/api/local/sessions", "/api/local/aggregates"):
        r = c.get(path)
        assert r.status_code == 200, f"{path}: {r.status_code} {r.get_data(as_text=True)[:150]}"
