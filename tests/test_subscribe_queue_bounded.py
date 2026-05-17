"""Tests for the heartbeat-piggyback bounded subscribe queue (issue #1595).

The cloud-relay path queues query subscribes per (owner, node) for the next
daemon heartbeat to drain. Before this fix the queue was unbounded — a
viewer auto-refreshing 5 panels every 5 s for 10 minutes could stack 500+
entries, starving fresh subscribes behind dead work.

Invariants exercised:

  1. Queue under cap: every subscribe is preserved, ``queue_len`` rises
     monotonically, and the overflow metric never ticks.
  2. Queue at cap, new subscribe: the OLDEST entry is dropped (FIFO), the
     newest is accepted, ``subscribe_queue_overflow.count`` rises by 1,
     and ``last_dropped`` carries the evicted owner/node/shape.
  3. Multiple (owner, node) pairs are independent — pair A hitting its
     cap MUST NOT evict from pair B.
  4. ``queue_len`` in the response equals the post-append depth of THIS
     subscribe's queue (clients use it for backpressure).
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest
from flask import Flask

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture
def client(monkeypatch):
    """Flask app with bp_cloud_relay + a tiny QUEUE_MAX_LEN (5) so we can
    exercise overflow without enqueueing 100 entries per test.

    Reload routes.meta after setting the env var so QUEUE_MAX_LEN picks up
    the override (it's a module-level constant baked at import time).
    """
    monkeypatch.setenv("CLAWMETRY_SUBSCRIBE_QUEUE_MAX", "5")

    # Force re-evaluation of QUEUE_MAX_LEN from the env var.
    import routes.meta as meta_mod
    importlib.reload(meta_mod)
    assert meta_mod.QUEUE_MAX_LEN == 5, (
        f"QUEUE_MAX_LEN env override failed: {meta_mod.QUEUE_MAX_LEN}"
    )
    meta_mod._reset_subscribe_state()

    app = Flask(__name__)
    app.register_blueprint(meta_mod.bp_cloud_relay)
    yield {"client": app.test_client(), "mod": meta_mod}

    # Tear down so a subsequent test reload doesn't inherit stale state.
    meta_mod._reset_subscribe_state()


def _subscribe(client, *, shape="events", args=None, owner="alice",
               node_id="node-1"):
    """Helper. POSTs to /api/cloud/subscribe and returns the parsed JSON."""
    body = {
        "owner": owner,
        "node_id": node_id,
        "shape": shape,
        "args": args or {},
    }
    r = client.post(
        "/api/cloud/subscribe",
        json=body,
    )
    assert r.status_code == 200, (
        f"subscribe failed: {r.status_code} {r.data!r}"
    )
    return r.get_json()


# ── 1. Queue under cap: everything preserved ─────────────────────────────


def test_queue_under_cap_preserves_all_items(client):
    c = client["client"]
    mod = client["mod"]

    # Cap is 5 — enqueue 4 distinct subscribes. None should be dropped.
    keys = []
    for i in range(4):
        resp = _subscribe(c, args={"session_id": f"sess-{i}"})
        assert resp["status"] == "queued"
        keys.append(resp["cache_key"])

    # All 4 keys distinct, last response reports queue_len == 4, overflow
    # counter never ticked.
    assert len(set(keys)) == 4, "cache_keys must be unique per (shape, args)"
    assert resp["queue_len"] == 4
    assert mod.subscribe_queue_overflow["count"] == 0
    assert mod.subscribe_queue_overflow["last_dropped"] is None

    # And the in-memory deque really holds 4 entries for this (owner, node).
    q = mod._subscribe_queues[("alice", "node-1")]
    assert len(q) == 4
    assert [e["cache_key"] for e in q] == keys


# ── 2. Queue at cap: oldest dropped, newest accepted, metric fires ───────


def test_queue_at_cap_drops_oldest_and_fires_metric(client):
    c = client["client"]
    mod = client["mod"]

    # Fill the queue exactly to cap (5).
    fill_keys = []
    for i in range(5):
        resp = _subscribe(c, args={"session_id": f"sess-fill-{i}"})
        fill_keys.append(resp["cache_key"])
    assert resp["queue_len"] == 5
    assert mod.subscribe_queue_overflow["count"] == 0

    # One more subscribe — must evict fill_keys[0] (the oldest) and accept
    # the new one. queue_len stays at cap.
    overflow_resp = _subscribe(c, args={"session_id": "sess-newest"})
    assert overflow_resp["status"] == "queued"
    assert overflow_resp["queue_len"] == 5, (
        f"queue_len must stay at cap after eviction: {overflow_resp}"
    )

    # Overflow metric ticked exactly once, with a sample of the dropped key.
    assert mod.subscribe_queue_overflow["count"] == 1
    last = mod.subscribe_queue_overflow["last_dropped"]
    assert last is not None
    assert last["owner"] == "alice"
    assert last["node"] == "node-1"
    assert last["shape"] == "events"
    assert "args_hash" in last and last["args_hash"]
    assert "ts" in last

    # The in-memory deque now contains fill_keys[1:] + [overflow_resp.key].
    q = mod._subscribe_queues[("alice", "node-1")]
    actual_keys = [e["cache_key"] for e in q]
    expected_keys = fill_keys[1:] + [overflow_resp["cache_key"]]
    assert actual_keys == expected_keys, (
        f"FIFO eviction broken — got {actual_keys}, want {expected_keys}"
    )

    # And the dropped sess-fill-0 entry's memo was cleared, so a re-subscribe
    # for it goes through cleanly (instead of being coalesced onto a
    # cache_key the daemon will never see).
    resub = _subscribe(c, args={"session_id": "sess-fill-0"})
    assert resub["cache_key"] != fill_keys[0], (
        "memo for evicted entry must be cleared so re-subscribe gets a "
        "fresh cache_key"
    )
    # That re-subscribe itself caused another overflow (queue was at cap).
    assert mod.subscribe_queue_overflow["count"] == 2


# ── 3. Multiple (owner, node) pairs: per-key cap, not global ─────────────


def test_per_owner_node_cap_is_independent(client):
    c = client["client"]
    mod = client["mod"]

    # Fill (alice, node-1) to cap.
    for i in range(5):
        _subscribe(c, owner="alice", node_id="node-1",
                   args={"session_id": f"a-{i}"})
    assert mod.subscribe_queue_overflow["count"] == 0
    assert len(mod._subscribe_queues[("alice", "node-1")]) == 5

    # Now hammer (bob, node-2) with 4 subscribes. Even though the global
    # subscribe count is now 9 (well past 5), bob's queue is independent
    # and well under cap.
    for i in range(4):
        resp = _subscribe(c, owner="bob", node_id="node-2",
                          args={"session_id": f"b-{i}"})
    assert resp["queue_len"] == 4
    assert mod.subscribe_queue_overflow["count"] == 0, (
        "bob's queue must NOT count against alice's cap"
    )
    assert len(mod._subscribe_queues[("alice", "node-1")]) == 5
    assert len(mod._subscribe_queues[("bob", "node-2")]) == 4

    # And different node ids under the SAME owner are also independent
    # (the cap is keyed on the (owner, node) pair, not owner alone).
    for i in range(3):
        resp = _subscribe(c, owner="alice", node_id="node-other",
                          args={"session_id": f"ao-{i}"})
    assert resp["queue_len"] == 3
    assert mod.subscribe_queue_overflow["count"] == 0
    assert len(mod._subscribe_queues[("alice", "node-other")]) == 3
    # Alice's original node-1 queue is untouched.
    assert len(mod._subscribe_queues[("alice", "node-1")]) == 5


# ── 4. queue_len in response matches post-append depth ───────────────────


def test_queue_len_reflects_post_append_depth(client):
    c = client["client"]

    # Each new (shape, args) subscribe should bump queue_len by exactly 1.
    for expected_len in range(1, 6):
        resp = _subscribe(c, args={"session_id": f"sess-len-{expected_len}"})
        assert resp["queue_len"] == expected_len, (
            f"queue_len must equal post-append depth — got "
            f"{resp['queue_len']}, expected {expected_len}"
        )

    # A coalesced (duplicate) subscribe must return the EXISTING queue_len
    # without incrementing — coalesce is idempotent.
    coalesced = _subscribe(c, args={"session_id": "sess-len-1"})
    assert coalesced["queue_len"] == 5
    assert coalesced["status"] == "queued"

    # Overflow: queue_len caps at cap (5) and does not exceed it.
    over = _subscribe(c, args={"session_id": "sess-len-overflow"})
    assert over["queue_len"] == 5


# ── Bonus: invalid shape returns 400 + status=rejected ───────────────────


def test_invalid_shape_rejected_without_queueing(client):
    c = client["client"]
    mod = client["mod"]

    r = c.post(
        "/api/cloud/subscribe",
        json={
            "owner": "alice",
            "node_id": "node-1",
            "shape": "drop_table_users",
            "args": {},
        },
    )
    assert r.status_code == 400
    body = r.get_json()
    assert body["status"] == "rejected"
    assert "allowed_shapes" in body
    # Nothing should have been enqueued.
    assert ("alice", "node-1") not in mod._subscribe_queues


def test_missing_node_id_returns_400(client):
    c = client["client"]
    r = c.post(
        "/api/cloud/subscribe",
        json={"owner": "alice", "shape": "events", "args": {}},
    )
    assert r.status_code == 400
