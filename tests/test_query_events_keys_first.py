"""``query_events`` sorts keys first when nothing narrows the scan.

The Brain feed and the Home poll ask the store for "the newest N events" with
at most ``exclude_daemon`` set, a predicate that rejects almost nothing. On
that shape DuckDB's TOP_N materialises the ``data`` BLOB for every row before
keeping N, so the call reads the whole column; on a memory-starved laptop
(2026-09-04, daemon buffer pool paged out) it measured 13-34 s live. Sorting
the narrow key columns first and fetching the N BLOBs by primary key touches
a few MB instead.

Two things must hold and are pinned here:

* the rows and their order are identical to the plain query for every
  shape, ties included (same ``ts`` resolved by ``id DESC``);
* the two-phase form is used ONLY when no selective predicate is present,
  because with one it is slower (0.01 s -> 0.16 s for a single session).

Acceptance:
    pytest tests/test_query_events_keys_first.py -q
"""
from __future__ import annotations

import contextlib
import importlib
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
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")
    monkeypatch.setenv("CLAWMETRY_AGG_CACHE_TTL", "0")  # every call hits SQL
    import clawmetry.local_store as ls
    importlib.reload(ls)
    ls.mark_writer_owner()
    st = ls.get_store(read_only=False)
    n = 0
    # Three sessions, two agents, a daemon tee, deliberate ts ties.
    for sess in ("s-a", "s-b", "s-c"):
        for i in range(12):
            n += 1
            st.ingest({
                "id": f"ev-{sess}-{i:02d}",
                "node_id": "node-test",
                "agent_id": "main" if i % 3 else "worker",
                "session_id": sess,
                "event_type": "tool_call" if i % 2 else "message",
                # i // 2 makes pairs of events share a timestamp.
                "ts": f"2026-05-11T12:00:{i // 2:02d}Z",
                "data": {"tool": "Bash", "input": f"x-{sess}-{i}"},
                "cost_usd": 0.001,
                "token_count": 10,
                "model": "m",
            })
    for i in range(4):
        st.ingest({
            "id": f"ev-daemon-{i}",
            "node_id": "node-test",
            "agent_id": "clawmetry-daemon",
            "session_id": "daemon",
            "event_type": "daemon.error",
            "ts": "2026-05-11T12:00:09Z",
            "data": {"msg": "noise"},
        })
    _wait_flush(st)
    yield st
    with contextlib.suppress(Exception):
        st.stop(flush=False)


_COLS = ("id, agent_type, node_id, agent_id, session_id, workspace_id, "
         "event_type, ts, data, cost_usd, token_count, model")


def _plain(store, where, params, limit):
    """The reference answer: the single-statement form on the same store."""
    sql = f"SELECT id FROM events {where} ORDER BY ts DESC, id DESC LIMIT ?"
    return [r[0] for r in store._fetch(sql, params + [limit])]


@pytest.mark.parametrize("limit", [1, 5, 13, 40, 500])
def test_unfiltered_shape_matches_plain_query(store, limit):
    got = [e["id"] for e in store.query_events(limit=limit)]
    assert got == _plain(store, "", [], limit)
    assert len(got) == min(limit, 40)


@pytest.mark.parametrize("limit", [1, 7, 36, 500])
def test_exclude_daemon_shape_matches_plain_query(store, limit):
    got = [e["id"] for e in store.query_events(limit=limit, exclude_daemon=True)]
    where = ("WHERE (agent_id IS DISTINCT FROM 'clawmetry-daemon') "
             "AND (event_type IS NULL OR event_type NOT LIKE 'daemon.%')")
    assert got == _plain(store, where, [], limit)
    assert not any(i.startswith("ev-daemon") for i in got)


def test_filtered_shapes_unchanged(store):
    got = [e["id"] for e in store.query_events(session_id="s-b", limit=500)]
    assert got == _plain(store, "WHERE session_id = ?", ["s-b"], 500)
    got = [e["id"] for e in store.query_events(agent_id="worker", limit=6)]
    assert got == _plain(store, "WHERE agent_id = ?", ["worker"], 6)
    got = [e["id"] for e in store.query_events(since="2026-05-11T12:00:04Z", limit=500)]
    assert got == _plain(store, "WHERE ts >= ?", ["2026-05-11T12:00:04Z"], 500)


def test_rows_carry_full_payload(store):
    rows = store.query_events(limit=3, exclude_daemon=True)
    assert rows and all(isinstance(r["data"], dict) and r["data"].get("tool") == "Bash" for r in rows)
    assert all(r["session_id"] and r["ts"] for r in rows)


def test_two_phase_only_when_no_selective_predicate(store, monkeypatch):
    seen: list[str] = []
    real = store._fetch

    def spy(sql, params):
        seen.append(" ".join(sql.split()))
        return real(sql, params)

    monkeypatch.setattr(store, "_fetch", spy)
    store.query_events(limit=10, exclude_daemon=True)
    store.query_events(limit=10)
    store.query_events(limit=10, session_id="s-a")
    store.query_events(limit=10, since="2026-05-11T12:00:00Z")
    assert len(seen) == 4
    assert "WHERE id IN ( SELECT id FROM events" in seen[0], seen[0]
    assert "WHERE id IN ( SELECT id FROM events" in seen[1], seen[1]
    assert "WHERE id IN" not in seen[2], seen[2]
    assert "WHERE id IN" not in seen[3], seen[3]
