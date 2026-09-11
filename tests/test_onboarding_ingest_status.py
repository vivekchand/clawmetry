"""`GET /api/onboarding/ingest-status` answers "is anything reaching us yet?" (#5680).

The onboarding strip polls this every 2 seconds while a new user wires up their
first runtime. Two properties decide whether it helps or misleads:

  * **"connected" must mean events actually arrived**, not that the store
    opened. A strip that reads connected over an empty store sends the user
    away believing setup worked;
  * **it must never raise.** It is polled from an overlay during onboarding,
    which is the worst moment to throw — the contract is a disconnected stub on
    any error, so the strip degrades silently instead of breaking the page.

ISOLATION, and why the import order below is load-bearing: ``local_store``
resolves its DB path at MODULE IMPORT from ``CLAWMETRY_LOCAL_STORE_PATH``.
Setting that inside a fixture is too late — the module is already imported and
the path already fixed, so the tests would run against the developer's real
``~/.clawmetry/clawmetry.duckdb``. And without ``mark_writer_owner()``,
``get_store()`` hands back the daemon proxy and every write silently no-ops.
Same trap `tests/test_store_invariants.py` documents.
"""
from __future__ import annotations

import os
import tempfile
import time

import pytest

duckdb = pytest.importorskip("duckdb", reason="ingest-status reads DuckDB")

# --- Environment MUST be prepared before clawmetry is imported. -------------
_TMPDIR = tempfile.mkdtemp(prefix="cm-ingest-status-")
os.environ["CLAWMETRY_LOCAL_STORE_PATH"] = os.path.join(_TMPDIR, "ingest.duckdb")

from clawmetry import local_store  # noqa: E402

local_store.mark_writer_owner()

_N = 0


def _event(agent_type: str, *, ts_epoch: float) -> dict:
    global _N
    _N += 1
    return {
        "id": "ev-%d" % _N,
        "node_id": "node-ingest-status",
        "event_type": "message",
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ts_epoch)),
        "session_id": "s-%s" % agent_type,
        "agent_id": "agent-ingest-status",
        "agent_type": agent_type,
    }


@pytest.fixture()
def store():
    st_ = local_store.LocalStore(read_only=False)
    try:
        yield st_
    finally:
        try:
            st_.stop(flush=False)
        except Exception:
            pass


def _status(st_):
    return st_.query_ingest_status()


def test_the_shape_is_stable_and_complete(store):
    """Every key the strip reads must be present even on a fresh store, or the
    overlay renders `undefined`."""
    out = _status(store)
    for key in ("connected", "events_total", "events_recent",
                "first_event_at", "last_event_at", "sources"):
        assert key in out, (key, out)
    assert isinstance(out["sources"], list)


def test_connected_tracks_whether_any_event_exists(store):
    """The load-bearing property: "connected" must mean events arrived, not
    that the store opened. A strip reading connected over an empty store sends
    the user away believing setup worked.

    Asserted as an INVARIANT rather than "a fresh store is empty", because
    ``CLAWMETRY_LOCAL_STORE_PATH`` is fixed at the first import of
    ``clawmetry.local_store``: in a multi-file run the first module to set it
    wins, so this file may share a store another suite already wrote to. An
    emptiness assumption passes alone and fails in the real CI job — which is
    exactly what it did before this was rewritten.
    """
    out = _status(store)
    assert out["connected"] is (out["events_total"] > 0), out
    if out["events_total"] == 0:
        assert out["sources"] == [], out
        assert out["first_event_at"] is None and out["last_event_at"] is None


def test_a_real_event_flips_connected(store):
    store.ingest_many([_event("claude_code", ts_epoch=time.time())])
    store.flush()
    out = _status(store)
    assert out["connected"] is True, out
    assert out["events_total"] >= 1


def test_it_never_raises_and_degrades_to_a_disconnected_stub(store):
    """Polled from the onboarding overlay every 2s, so throwing breaks the page
    at the worst moment. A broken store must read as disconnected, not crash."""
    def _boom(*a, **k):
        raise RuntimeError("store is unhappy")

    store._fetch = _boom
    out = store.query_ingest_status()
    assert out == {
        "connected": False,
        "events_total": 0,
        "events_recent": 0,
        "first_event_at": None,
        "last_event_at": None,
        "sources": [],
    }


def test_the_route_is_declared_to_the_daemon_query_surface():
    """A route may only call a store method the daemon actually serves.
    Without the dispatch entry the endpoint returns EMPTY in cloud rather than
    erroring — the silent shape, and the reason `make lint-daemon-allowlist`
    exists."""
    here = os.path.dirname(os.path.abspath(__file__))
    src = open(os.path.join(here, "..", "routes", "local_query.py"), encoding="utf-8").read()
    assert "query_ingest_status" in src


def test_the_endpoint_is_registered():
    here = os.path.dirname(os.path.abspath(__file__))
    src = open(os.path.join(here, "..", "routes", "onboarding.py"), encoding="utf-8").read()
    assert "/api/onboarding/ingest-status" in src


def test_kind_is_derived_from_the_runtime_catalogue():
    """`kind` tells the user WHERE their data came from, so it decides which
    setup instructions they are shown next. A runtime ClawMetry ships an
    adapter for is filesystem ingest; anything else arrived over OTLP or the
    HTTP ingest API. Asserted on the derivation, so adding a runtime cannot
    silently reclassify it."""
    import inspect

    src = inspect.getsource(local_store.LocalStore.query_ingest_status)
    assert "ALL_RUNTIMES" in src
    assert '"filesystem"' in src and '"otlp"' in src


def test_a_populated_store_reports_the_events_it_holds(store):
    """The regression that shipped in this PR's first draft, and the reason the
    two checks below exist.

    ``_fetch`` returns positional TUPLES and takes ``(sql, params)``. The method
    read rows as dicts and called ``_fetch`` with one argument, so BOTH passes
    raised — AttributeError and TypeError — and the blanket ``except Exception``
    turned each into the disconnected stub. The endpoint therefore reported
    "not connected" for every user, on every call, no matter how much data the
    store held: the exact failure it exists to prevent, inverted.

    Neither fault is visible from reading the happy path, and neither can fail a
    test that only checks the empty store. This one needs real rows.
    """
    now = time.time()
    store.ingest_many([
        _event("claude_code", ts_epoch=now),
        _event("claude_code", ts_epoch=now),
        _event("some-byo-service", ts_epoch=now),
    ])
    store.flush()

    out = _status(store)
    assert out["connected"] is True, out
    assert out["events_total"] >= 3, out
    assert out["events_recent"] >= 3, out
    assert out["first_event_at"] is not None and out["last_event_at"] is not None

    by_rt = {s["runtime"]: s for s in out["sources"]}
    assert "claude_code" in by_rt, out["sources"]
    assert by_rt["claude_code"]["events"] >= 2
    assert by_rt["claude_code"]["kind"] == "filesystem"
    assert by_rt["some-byo-service"]["kind"] == "otlp", by_rt


def test_the_error_stub_is_reachable_only_by_a_real_error(store):
    """The blanket ``except Exception`` is what hid two live bugs, so pin that a
    HEALTHY store never takes that branch. Without this, a later refactor that
    breaks either query silently restores "always disconnected"."""
    store.ingest_many([_event("claude_code", ts_epoch=time.time())])
    store.flush()
    out = _status(store)
    stub = {
        "connected": False, "events_total": 0, "events_recent": 0,
        "first_event_at": None, "last_event_at": None, "sources": [],
    }
    assert out != stub, "a populated store returned the error stub"
