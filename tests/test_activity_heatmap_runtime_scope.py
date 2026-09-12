"""Activity heatmap: SQL bucketing, node-local hours, per-runtime scoping.

The hosted Cost tab drew an all-zero heatmap for every user because the
cloud handler had nothing to count (see ``clawmetry-cloud`` cm-cloud-heatmap).
The daemon-side half of that fix is here: one SQL GROUP BY that buckets on
the node-local clock and can be scoped to a single runtime, plus the
per-runtime split the snapshot ships.

Pinned here:
  * a UTC-stamped event and a local-stamped one at the same instant land in
    the SAME hour (the old Python path stripped the offset instead),
  * ``?runtime=`` scopes by session-id prefix and an unknown runtime returns
    zero rather than the node-wide total (FLYWHEEL 1c),
  * the per-runtime split reconciles with the single-runtime query.
"""

from __future__ import annotations

import importlib
import time
from datetime import datetime, timedelta, timezone

import pytest


def _wait_flush(store, t: float = 2.0) -> None:
    deadline = time.monotonic() + t
    while time.monotonic() < deadline:
        if store.health()["ring_depth"] == 0:
            return
        time.sleep(0.02)


@pytest.fixture
def fresh_store(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "1")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")
    import clawmetry.local_store as ls
    importlib.reload(ls)
    yield ls
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def _seed(store):
    """Two events at the same instant, one written local, one written UTC."""
    local_noon = datetime.now().astimezone().replace(
        hour=12, minute=0, second=0, microsecond=0
    )
    store.ingest({
        "id": "ev-local", "node_id": "n", "agent_id": "main",
        "session_id": "claude_code:aaa", "event_type": "message",
        "ts": local_noon.isoformat(),
    })
    store.ingest({
        "id": "ev-utc", "node_id": "n", "agent_id": "main",
        "session_id": "codex:bbb", "event_type": "message",
        "ts": local_noon.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
    })
    _wait_flush(store)
    return local_noon


def test_utc_and_local_events_share_one_local_hour(fresh_store):
    store = fresh_store.get_store()
    noon = _seed(store)
    grid = store.activity_heatmap(days=1)
    hours = grid["days"][-1]["hours"]
    assert hours[noon.hour] == 2, hours
    assert sum(hours) == 2


def test_runtime_scopes_by_session_prefix(fresh_store):
    store = fresh_store.get_store()
    noon = _seed(store)
    cc = store.activity_heatmap(days=1, runtime="claude_code")
    cx = store.activity_heatmap(days=1, runtime="codex")
    assert cc["days"][-1]["hours"][noon.hour] == 1
    assert cx["days"][-1]["hours"][noon.hour] == 1
    # An unrecognised runtime must return zero, never the node-wide total.
    unknown = store.activity_heatmap(days=1, runtime="__nope__")
    assert unknown["max"] == 0
    assert sum(sum(d["hours"]) for d in unknown["days"]) == 0


def test_split_reconciles_with_single_runtime_query(fresh_store):
    store = fresh_store.get_store()
    _seed(store)
    split = store.activity_heatmap_by_runtime(days=1)
    assert set(split) >= {"all", "claude_code", "codex"}
    for rt in ("claude_code", "codex"):
        assert split[rt]["days"] == store.activity_heatmap(days=1, runtime=rt)["days"]
    # Node-wide row is the sum of its parts.
    assert sum(sum(d["hours"]) for d in split["all"]["days"]) == 2


def test_grid_is_a_fixed_shape(fresh_store):
    store = fresh_store.get_store()
    _seed(store)
    grid = store.activity_heatmap(days=30)
    assert len(grid["days"]) == 30
    assert all(len(d["hours"]) == 24 for d in grid["days"])
    today = datetime.now().astimezone().strftime("%Y-%m-%d")
    assert grid["days"][-1]["date"] == today
    first = (datetime.now().astimezone() - timedelta(days=29)).strftime("%Y-%m-%d")
    assert grid["days"][0]["date"] == first


def test_route_passes_runtime_through(fresh_store):
    store = fresh_store.get_store()
    _seed(store)
    import importlib as _il
    from flask import Flask
    mod = _il.import_module("routes.health")
    _il.reload(mod)
    app = Flask(__name__)
    app.register_blueprint(getattr(mod, "bp_health"))
    c = app.test_client()

    body = c.get("/api/heatmap?days=1&runtime=codex").get_json()
    assert body["_source"] == "local_store"
    assert body["runtime"] == "codex"
    assert body["max"] == 1
    # Unknown runtime: no fall-through to the node-wide file scan.
    body = c.get("/api/heatmap?days=1&runtime=__nope__").get_json()
    assert body["max"] == 0
