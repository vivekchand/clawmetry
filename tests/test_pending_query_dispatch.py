"""Regression tests for the 2026-05-18 P0 where cloud-side ``pending_queries``
attach kwargs (e.g. ``node_id``) that ``LocalStore.query_sessions()`` doesn't
accept.

Root cause: cloud's ``/api/cloud/node/<id>/sessions`` enqueues a pending
query with ``args = {"node_id": node_id}``. The daemon's
``_dispatch_pending_queries`` forwarded the args straight into
``store.query_sessions(**args)`` and tripped::

    TypeError: LocalStore.query_sessions() got an unexpected keyword
    argument 'node_id'

Every heartbeat fired this 3x and the sessions cache on cloud never
populated -> "Embodied" tab empty, ``/api/cloud/node/<id>/sessions``
returned ``_source: relay_pending, eta_sec: 60`` indefinitely.

Fix: both transport entry points (``routes.local_query._dispatch`` and the
daemon-only ``clawmetry.sync._local_dispatch_fallback``) now filter args to
the per-shape allowlist before calling the underlying ``LocalStore``
method. These tests pin that behaviour so a future signature change can't
regress us.
"""
from __future__ import annotations

import importlib
import os
import sys

import pytest


_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)


# ── Fixtures ───────────────────────────────────────────────────────────────

@pytest.fixture
def fresh_modules(tmp_path, monkeypatch):
    """Reload sync + local_store + routes.local_query against a tmp DuckDB
    so the per-shape kwarg filter is exercised against the same on-disk
    schema the daemon would see in production."""
    monkeypatch.setenv(
        "CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb")
    )
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "1")

    sys.modules.pop("clawmetry.local_store", None)
    sys.modules.pop("clawmetry.sync", None)
    sys.modules.pop("routes.local_query", None)

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import clawmetry.sync as s
    importlib.reload(s)
    import routes.local_query as lq
    importlib.reload(lq)

    # Force-create the writer connection so read_only opens later in the
    # test won't trip "database does not exist". Mirrors what the daemon
    # does on boot.
    ls.get_store()

    yield {"sync": s, "local_store": ls, "local_query": lq}

    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


# ── 1. Fallback dispatcher drops node_id without raising ───────────────────

def test_fallback_dispatch_drops_node_id_for_sessions(fresh_modules):
    """Cloud sends ``shape=sessions, args={node_id: ...}``. The daemon's
    fallback dispatcher must NOT raise ``TypeError: unexpected keyword
    argument 'node_id'``."""
    s = fresh_modules["sync"]
    # Pre-fix: this raised TypeError. Post-fix: returns the empty-rows
    # envelope cleanly because no events have been ingested.
    result = s._local_dispatch_fallback("sessions", {"node_id": "node-XYZ"})
    assert isinstance(result, dict)
    assert result.get("_shape") == "sessions"
    assert "rows" in result and isinstance(result["rows"], list)


def test_fallback_dispatch_drops_node_id_for_events(fresh_modules):
    s = fresh_modules["sync"]
    result = s._local_dispatch_fallback(
        "events", {"node_id": "node-XYZ", "limit": 5}
    )
    assert isinstance(result, dict)
    assert result.get("_shape") == "events"
    # ``limit`` is in the allowlist; ``node_id`` should have been filtered.


def test_fallback_dispatch_drops_node_id_for_aggregates(fresh_modules):
    s = fresh_modules["sync"]
    result = s._local_dispatch_fallback(
        "aggregates", {"node_id": "node-XYZ"}
    )
    assert isinstance(result, dict)
    assert result.get("_shape") == "aggregates"


# ── 2. Primary dispatcher (routes.local_query) drops node_id too ───────────

def test_primary_dispatch_drops_node_id_for_sessions(fresh_modules):
    """``routes.local_query._dispatch`` is the path taken when the daemon
    can import the routes package (the common case). It must apply the
    same kwarg filter."""
    lq = fresh_modules["local_query"]
    # Without the fix this raised TypeError before returning.
    result = lq._dispatch("sessions", {"node_id": "node-XYZ"})
    assert isinstance(result, dict)
    assert result.get("_shape") == "sessions"


# ── 3. Allowlist is explicit + per-shape ───────────────────────────────────

def test_filter_kwargs_allowlist_per_shape(fresh_modules):
    """Lock in the per-shape kwarg allowlist so a future drift between the
    cloud + local store can't silently reintroduce the bug class."""
    s = fresh_modules["sync"]
    f = s._filter_store_kwargs

    # node_id is dropped for every known shape.
    for shape in ("events", "sessions", "aggregates", "transcript"):
        out = f(shape, {"node_id": "n", "limit": 10})
        assert "node_id" not in out, f"node_id leaked for shape={shape}"

    # Known kwargs pass through untouched.
    assert f("sessions", {"agent_id": "main", "limit": 25}) == {
        "agent_id": "main", "limit": 25,
    }
    assert f("transcript", {"session_id": "sess-A", "limit": 50}) == {
        "session_id": "sess-A", "limit": 50,
    }


# ── 4. End-to-end through send_heartbeat ───────────────────────────────────

def test_pending_query_with_node_id_completes_without_warning(
    fresh_modules, monkeypatch, caplog
):
    """Wire the full ``send_heartbeat`` pipeline with a fake ``_post`` and
    confirm the ``pending_query dispatch failed`` warning is NOT logged
    when the cloud attaches ``args={'node_id': ...}``."""
    import logging

    s = fresh_modules["sync"]
    cache_posts = []

    def fake_post(path, payload, api_key, timeout=45):
        if path == "/ingest/heartbeat":
            return {
                "sync_allowed": True,
                "pending_queries": [
                    {
                        "id": "q_node_sessions_refresh_test",
                        "shape": "sessions",
                        "args": {"node_id": "node-XYZ"},
                        "cache_key": "node:node-XYZ:sessions",
                    },
                ],
            }
        if path == "/ingest/cache":
            cache_posts.append(payload)
            return {}
        raise AssertionError(f"unexpected path {path}")

    monkeypatch.setattr(s, "_post", fake_post)
    monkeypatch.setattr(s.time, "sleep", lambda *a, **kw: None)

    config = {
        "node_id":        "node-XYZ",
        "api_key":        "cm_test",
        "encryption_key": s.generate_encryption_key(),
    }

    caplog.set_level(logging.WARNING, logger="clawmetry-sync")
    ok = s.send_heartbeat(config)

    assert ok is True
    # Cache POST should have fired - sessions list (even if empty) was dispatched.
    assert len(cache_posts) == 1
    assert cache_posts[0]["id"] == "q_node_sessions_refresh_test"
    # And critically: the regressed warning must NOT be present.
    failures = [
        r for r in caplog.records
        if "pending_query dispatch failed" in r.getMessage()
    ]
    assert not failures, f"unexpected dispatch failures: {[r.getMessage() for r in failures]}"
