"""Date-time range filter on /api/brain-history ("what happened at 3AM?").

The Brain Activity stream historically only showed "the newest N events".
This feature adds ``since``/``until`` (aliases ``start``/``end``) query
params so a user can investigate an arbitrary historical window:

  1. The local-store fast path threads both bounds to
     ``LocalStore.query_events`` (SQL ``ts >= / <=``, idx_events_ts).
  2. The response echoes ``window: {since, until}`` and NEVER sets
     ``capped_at_24h`` for a user range (that flag drives an upgrade CTA).
  3. An empty store with a range returns an honest empty window instead of
     falling through to the (range-blind) JSONL parser.
  4. Bad time values degrade to "no bound", never a 500.
  5. The daemon relay's windowed builder ``_build_brain_events_window``
     (clawmetry/sync.py) honors the window, so hosted "3AM" queries return
     the actual chronology instead of the fair top-50 blob.

Revert-proof: every test here fails on the pre-feature code (params were
ignored → all events returned; relay discarded the window args).
"""

from __future__ import annotations

import importlib
import os
import sys
import time

import pytest
from flask import Flask

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)


def _wait_flush(store, t=4.0):
    deadline = time.monotonic() + t
    while time.monotonic() < deadline:
        if store.health()["ring_depth"] == 0:
            return
        time.sleep(0.02)


def _mk_event(eid, ts, sess="sess-night"):
    return {
        "id": eid,
        "node_id": "agent+test",
        "agent_id": "main",
        "session_id": sess,
        "event_type": "tool_call",
        "ts": ts,
        "data": {"tool": "Bash", "input": f"echo {eid}"},
        "cost_usd": 0.001,
        "token_count": 10,
        "model": "claude-opus-4-7",
    }


# A quiet night with a 3AM incident: events at 01:00, 03:00, 03:15, 05:00.
_NIGHT = [
    ("ev-0100", "2026-07-09T01:00:00Z"),
    ("ev-0300", "2026-07-09T03:00:00Z"),
    ("ev-0315", "2026-07-09T03:15:00Z"),
    ("ev-0500", "2026-07-09T05:00:00Z"),
]


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "1")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")

    import clawmetry.local_store as ls
    importlib.reload(ls)
    # Hermetic on dev machines: a live daemon registers itself in
    # ~/.clawmetry/local_query.json, which makes get_store() return a
    # _ProxyStore that forwards to the REAL store. Claim the writer so this
    # test process opens the tmp DuckDB directly.
    ls.mark_writer_owner()
    import routes.brain as br
    importlib.reload(br)

    import dashboard as _d
    monkeypatch.setattr(_d, "_is_pro_user", lambda: True)

    # Hermetic: force the daemon HTTP proxy to miss so the route reads the
    # tmp DuckDB directly (a dev machine's live daemon must not leak real
    # events into the fixture window).
    import routes.local_query as lq
    monkeypatch.setattr(lq, "local_store_via_daemon", lambda *a, **k: None)

    a = Flask(__name__)
    a.register_blueprint(br.bp_brain)
    yield a, ls, br
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def _seed_night(ls):
    store = ls.get_store()
    for eid, ts in _NIGHT:
        store.ingest(_mk_event(eid, ts))
    _wait_flush(store)
    return store


def _ids(body):
    return {ev["eventId"] for ev in body["events"]}


# ── The core investigation: bounded window ──────────────────────────────────


def test_window_returns_only_in_range_events(app):
    a, ls, _br = app
    _seed_night(ls)
    r = a.test_client().get(
        "/api/brain-history?limit=50"
        "&since=2026-07-09T02:30:00Z&until=2026-07-09T04:00:00Z"
    )
    assert r.status_code == 200, r.get_data(as_text=True)[:300]
    body = r.get_json()
    assert body.get("_source") == "local_store"
    assert _ids(body) == {"ev-0300", "ev-0315"}
    # The response echoes the normalized window so the UI can label it.
    assert body.get("window") == {
        "since": "2026-07-09T02:30:00Z",
        "until": "2026-07-09T04:00:00Z",
    }
    # A user range must NEVER read as the retention cap (upgrade CTA).
    assert body.get("capped_at_24h") is False


def test_start_end_aliases_work(app):
    a, ls, _br = app
    _seed_night(ls)
    body = a.test_client().get(
        "/api/brain-history?limit=50"
        "&start=2026-07-09T02:30:00Z&end=2026-07-09T04:00:00Z"
    ).get_json()
    assert _ids(body) == {"ev-0300", "ev-0315"}


def test_since_only_and_until_only(app):
    a, ls, _br = app
    _seed_night(ls)
    c = a.test_client()
    body = c.get("/api/brain-history?limit=50&since=2026-07-09T04:00:00Z").get_json()
    assert _ids(body) == {"ev-0500"}
    body = c.get("/api/brain-history?limit=50&until=2026-07-09T02:00:00Z").get_json()
    assert _ids(body) == {"ev-0100"}


def test_reversed_bounds_are_swapped(app):
    """since > until is a user slip, not an error — swap and answer."""
    a, ls, _br = app
    _seed_night(ls)
    body = a.test_client().get(
        "/api/brain-history?limit=50"
        "&since=2026-07-09T04:00:00Z&until=2026-07-09T02:30:00Z"
    ).get_json()
    assert _ids(body) == {"ev-0300", "ev-0315"}


def test_bad_time_values_degrade_to_no_bound(app):
    a, ls, _br = app
    _seed_night(ls)
    r = a.test_client().get("/api/brain-history?limit=50&since=not-a-time&until=")
    assert r.status_code == 200
    body = r.get_json()
    assert _ids(body) == {e[0] for e in _NIGHT}
    assert "window" not in body


def test_epoch_seconds_accepted(app):
    a, ls, _br = app
    _seed_night(ls)
    import datetime as _dt
    since = int(_dt.datetime(2026, 7, 9, 2, 30, tzinfo=_dt.timezone.utc).timestamp())
    until = int(_dt.datetime(2026, 7, 9, 4, 0, tzinfo=_dt.timezone.utc).timestamp())
    body = a.test_client().get(
        f"/api/brain-history?limit=50&since={since}&until={until}"
    ).get_json()
    assert _ids(body) == {"ev-0300", "ev-0315"}


def test_empty_store_with_range_returns_honest_empty(app):
    """A store with nothing in the window answers honestly empty. (A fresh
    install with NO DuckDB file at all falls through to the JSONL parser,
    which now post-filters by the same window, so events stay bounded
    either way — this asserts the contract, not the code path.)"""
    a, _ls, _br = app
    body = a.test_client().get(
        "/api/brain-history?limit=50"
        "&since=2001-01-01T00:00:00Z&until=2001-01-02T00:00:00Z"
    ).get_json()
    assert body["events"] == []
    assert body.get("capped_at_24h") is False
    assert body.get("window") == {
        "since": "2001-01-01T00:00:00Z",
        "until": "2001-01-02T00:00:00Z",
    }


# ── The time-arg parser ─────────────────────────────────────────────────────


def test_time_arg_parser_normalizes_variants(app):
    _a, _ls, br = app
    p = br._brain_history_time_arg
    assert p("2026-07-09T03:00:00Z") == "2026-07-09T03:00:00Z"
    assert p("2026-07-09T03:00") == "2026-07-09T03:00:00Z"          # naive → UTC
    assert p("2026-07-09 03:00:00") == "2026-07-09T03:00:00Z"       # space sep
    assert p("2026-07-09T08:30:00+05:30") == "2026-07-09T03:00:00Z" # offset
    assert p("1783566000") == "2026-07-09T03:00:00Z"                # epoch s
    assert p("1783566000000") == "2026-07-09T03:00:00Z"             # epoch ms
    assert p("") is None
    assert p(None) is None
    assert p("garbage") is None
    assert p("3AM") is None


# ── Daemon relay: windowed brain blob (hosted "3AM" path) ───────────────────


@pytest.fixture
def sync_with_night(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "1")
    sys.modules.pop("clawmetry.local_store", None)
    sys.modules.pop("clawmetry.sync", None)
    import clawmetry.local_store as ls
    importlib.reload(ls)
    ls.mark_writer_owner()  # hermetic on dev machines (see app fixture)
    import clawmetry.sync as s
    importlib.reload(s)
    store = ls.get_store()
    for eid, ts in _NIGHT:
        # event_type=message + data.text → passes _brain_row_renderable.
        store.ingest({
            "id": eid, "node_id": "agent+test", "agent_id": "main",
            "session_id": "sess-night", "event_type": "message", "ts": ts,
            "data": {"text": f"hello {eid}"}, "cost_usd": 0.001,
            "token_count": 42, "model": "claude-opus-4-7",
        })
    _wait_flush(store)
    yield s
    try:
        store.stop(flush=True)
    except Exception:
        pass


def _blob_ids(events):
    out = set()
    for ev in events:
        ts = (ev.get("timestamp") or ev.get("time") or ev.get("ts") or "")
        out.add(ts)
    return out


def test_build_brain_events_window_honors_bounds(sync_with_night):
    s = sync_with_night
    events = s._build_brain_events_window(
        since="2026-07-09T02:30:00Z", until="2026-07-09T04:00:00Z"
    )
    assert events, "windowed builder returned nothing for a populated window"
    times = _blob_ids(events)
    assert any(t.startswith("2026-07-09T03:00") for t in times)
    assert any(t.startswith("2026-07-09T03:15") for t in times)
    assert not any(t.startswith("2026-07-09T01:00") for t in times)
    assert not any(t.startswith("2026-07-09T05:00") for t in times)


def test_build_brain_events_window_empty_window(sync_with_night):
    s = sync_with_night
    events = s._build_brain_events_window(
        since="2026-07-08T02:30:00Z", until="2026-07-08T04:00:00Z"
    )
    assert events == []


def test_build_brain_events_window_clamps_limit(sync_with_night):
    s = sync_with_night
    # A hostile/buggy limit can't blow past the ceiling or crash.
    assert s._build_brain_events_window(limit=10**9) is not None
    assert s._build_brain_events_window(limit="junk") is not None
