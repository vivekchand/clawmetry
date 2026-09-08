"""The Cost tab's roll-up scans ship slim event rows, and the RPC is memoised.

Why this exists (2026-09-05). ``/api/usage`` and its sibling Cost endpoints
each asked the daemon for the newest 20k-50k events and aggregated them in
Python. Measured on a real 46k-row store, ONE ``query_events(limit=20000)``
marshals 37.7 MB across the daemon RPC and the SQL is only 0.9 s of it — the
rest is decode + dumps + loads. A page load fired 21 such scans. That storm
saturated the daemon's single DuckDB connection until sibling reads exceeded
``routes.local_query._PROXY_TIMEOUTS``, whose handlers then returned ``None``
and rendered a confident EMPTY tab ("No sessions have a transcript yet" over
a store holding thousands).

Two things fix it and are pinned here:

* ``query_events_slim`` returns the SAME rows as ``query_events`` minus the
  two keys that carry the bulk (``content`` 66%, ``tool_calls`` 28% of the
  decoded payload) — a denylist, so a roll-up reading any other key keeps
  its numbers exactly;
* the daemon RPC for that shape is memoised AND single-flighted, so the
  concurrent endpoints behind one page load share a single round trip
  instead of queueing N copies of an 8 MB response.

Acceptance:
    pytest tests/test_cost_scan_slim_events.py -q
"""
from __future__ import annotations

import contextlib
import importlib
import threading
import time

import pytest


def _wait_flush(store, t=3.0):
    deadline = time.monotonic() + t
    while time.monotonic() < deadline:
        if store.health()["ring_depth"] == 0:
            return
        time.sleep(0.02)


@pytest.fixture
def store(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "slim.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")
    monkeypatch.setenv("CLAWMETRY_AGG_CACHE_TTL", "0")  # every call hits SQL
    import clawmetry.local_store as ls
    importlib.reload(ls)
    ls.mark_writer_owner()
    st = ls.get_store(read_only=False)
    for i in range(24):
        st.ingest({
            "id": f"ev-{i:02d}",
            "node_id": "node-test",
            "agent_id": "main",
            "session_id": "claude_code:sess-1" if i % 2 else "sess-openclaw",
            "event_type": "assistant" if i % 2 else "tool_call",
            "ts": f"2026-05-11T12:00:{i:02d}Z",
            "data": {
                # The two heavyweights the roll-ups never read.
                "content": "x" * 4096,
                "tool_calls": [{"name": "Bash", "args": "y" * 512}],
                # Everything a roll-up DOES read must survive untouched.
                "tool_name": "Bash",
                "plugin": "shell",
                "skill": "review",
                "role": "assistant",
                "_runtime": "claude_code",
                "extra": {"k": "v"},
            },
            "cost_usd": 0.002,
            "token_count": 25,
            "model": "claude-opus-5",
        })
    _wait_flush(st)
    yield st
    with contextlib.suppress(Exception):
        st.stop(flush=False)


def test_slim_drops_only_the_bulk_keys(store):
    full = store.query_events(limit=100)
    slim = store.query_events_slim(limit=100)
    assert len(slim) == len(full) > 0
    for a, b in zip(full, slim):
        # Every column outside ``data`` is byte-identical, order included.
        assert {k: v for k, v in a.items() if k != "data"} == \
               {k: v for k, v in b.items() if k != "data"}
        assert a["data"]["content"] and a["data"]["tool_calls"]
        assert "content" not in b["data"] and "tool_calls" not in b["data"]
        # The denylist is exactly two keys — nothing else may go missing.
        assert b["data"] == {k: v for k, v in a["data"].items()
                             if k not in ("content", "tool_calls")}


def test_slim_preserves_every_key_a_rollup_reads(store):
    slim = store.query_events_slim(limit=100)
    assert slim
    for row in slim:
        d = row["data"]
        for key in ("tool_name", "plugin", "skill", "role", "_runtime", "extra"):
            assert key in d, f"roll-up key {key!r} lost from slim rows"


def test_slim_is_materially_smaller_on_the_wire(store):
    import json
    full = len(json.dumps(store.query_events(limit=100), default=str))
    slim = len(json.dumps(store.query_events_slim(limit=100), default=str))
    # The whole point: the bulk keys dominate, so the drop must be large.
    assert slim * 3 < full, f"slim {slim} vs full {full} — projection not saving bytes"


def test_slim_shape_is_allowlisted_on_the_daemon_proxy():
    from routes.local_query import _DAEMON_METHODS
    # An un-allowlisted method returns a 400 the caller swallows as "empty",
    # which is precisely the false-empty this change exists to end.
    assert "query_events_slim" in _DAEMON_METHODS


def test_rpc_memo_single_flights_concurrent_identical_scans(monkeypatch):
    import routes.local_query as lq
    lq.invalidate_rpc_memo()
    monkeypatch.setattr(lq, "_RPC_MEMO_TTL", 30.0)
    calls = []

    def fake_uncached(method_name, **kwargs):
        calls.append(method_name)
        time.sleep(0.15)          # hold the "round trip" open
        return [{"id": "row"}]

    monkeypatch.setattr(lq, "_local_store_call_via_daemon_uncached", fake_uncached)
    results, threads = [], []
    for _ in range(8):
        threads.append(threading.Thread(
            target=lambda: results.append(
                lq.local_store_call_via_daemon("query_events_slim", limit=20000))))
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(results) == 8 and all(r == [{"id": "row"}] for r in results)
    # Eight concurrent callers, ONE round trip — the page-load fan-out.
    assert len(calls) == 1, f"expected single-flight, got {len(calls)} RPCs"
    lq.invalidate_rpc_memo()


def test_rpc_memo_never_caches_the_unavailable_sentinel(monkeypatch):
    import routes.local_query as lq
    lq.invalidate_rpc_memo()
    monkeypatch.setattr(lq, "_RPC_MEMO_TTL", 30.0)
    calls = []

    def flaky(method_name, **kwargs):
        calls.append(method_name)
        # Daemon down for the first call, healthy afterwards.
        return lq.PROXY_UNAVAILABLE if len(calls) == 1 else [{"id": "row"}]

    monkeypatch.setattr(lq, "_local_store_call_via_daemon_uncached", flaky)
    first = lq.local_store_call_via_daemon("query_events_slim", limit=5000)
    second = lq.local_store_call_via_daemon("query_events_slim", limit=5000)
    assert first is lq.PROXY_UNAVAILABLE
    # A momentary outage must not blind the next call for the whole TTL.
    assert second == [{"id": "row"}] and len(calls) == 2
    lq.invalidate_rpc_memo()


def test_rpc_memo_ignores_shapes_that_did_not_opt_in(monkeypatch):
    import routes.local_query as lq
    lq.invalidate_rpc_memo()
    monkeypatch.setattr(lq, "_RPC_MEMO_TTL", 30.0)
    calls = []
    monkeypatch.setattr(lq, "_local_store_call_via_daemon_uncached",
                        lambda m, **k: (calls.append(m), [{"id": "row"}])[1])
    for _ in range(3):
        lq.local_store_call_via_daemon("query_sessions", limit=10)
    # Only ``_RPC_MEMO_METHODS`` may be served from cache; everything else
    # keeps its exact previous semantics.
    assert len(calls) == 3
    lq.invalidate_rpc_memo()


def test_scan_falls_back_to_full_shape_when_daemon_lacks_slim(monkeypatch):
    """An upgraded dashboard against a not-yet-restarted daemon must not
    empty the Cost tab.

    The dashboard and the sync daemon are separate processes that restart
    independently, so during an upgrade the dashboard can ask a daemon whose
    allowlist predates ``query_events_slim`` for that shape. The proxy answers
    400, ``_ls_call`` yields None, and without a fallback every Cost roll-up
    renders a confident empty. Reproduced live 2026-09-05: with only the
    dashboard restarted, /api/model-attribution went from 4 models to 0 and
    /api/usage/by-plugin from 84%-thinking to [].
    """
    import routes.usage as U
    seen = []

    def fake_ls_call(method_name, **kwargs):
        seen.append(method_name)
        # Old daemon: slim is not allowlisted, proxy fails -> None.
        if method_name == "query_events_slim":
            return None
        return [{"id": "ev-1", "data": {"tool": "Bash"}}]

    monkeypatch.setattr(U, "_ls_call", fake_ls_call)
    rows = U._scan_events_slim(limit=20000)
    assert rows == [{"id": "ev-1", "data": {"tool": "Bash"}}], \
        "version skew must cost bytes, not correctness"
    assert seen == ["query_events_slim", "query_events"]


def test_scan_does_not_refetch_when_slim_returns_empty(monkeypatch):
    """An genuinely empty store returns ``[]``, not ``None`` — and ``[]`` is a
    real answer, so it must NOT trigger the heavyweight fallback."""
    import routes.usage as U
    seen = []
    monkeypatch.setattr(U, "_ls_call",
                        lambda m, **k: (seen.append(m), [])[1])
    assert U._scan_events_slim(limit=20000) == []
    assert seen == ["query_events_slim"], "empty is an answer, not a failure"
