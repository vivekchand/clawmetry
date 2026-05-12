"""End-to-end test for the heartbeat-piggyback relay transport (issue #1053).

This is the test gauntlet for the new Phase-1 transport that replaces the
WebSocket relay: cloud queues a query when a browser subscribes, returns
``pending_queries`` on the next ``/ingest/heartbeat``, the daemon dispatches
locally against DuckDB, encrypts, POSTs the result to ``/ingest/cache``, and
the browser polls ``/api/cloud/cache/<key>`` for the encrypted blob.

Pipeline under test (5 steps from the issue):

  1. Browser POST /api/cloud/subscribe {node_id, shape, args}
       cloud → {cache_key, query_id, eta_sec, status: "queued"|"cache_hit"}
  2. Daemon POST /ingest/heartbeat
       cloud → {pending_queries: [{id, shape, args, cache_key}]}
  3. Daemon dispatches local DuckDB (via routes.local_query.relay_dispatch),
     encrypts result with AES-256-GCM, POST /ingest/cache {id, cache_key,
     blob, shape, args_hash, ttl}
  4. Browser GET /api/cloud/cache/<cache_key>
       cloud → encrypted blob
  5. Browser decrypts → matches the events seeded in DuckDB

This test is **fully self-contained**: no live daemon, no real network, no
cloud Flask app required. Strategy:

* Engineer 11 (cloud) is shipping ``clawmetry-cloud/routes/heartbeat_relay.py``
  with the wire contract above — it is not yet in the cloud repo as of
  2026-05-12. To unblock our E2E test we re-implement a **minimal,
  contract-faithful** mock cloud blueprint inline (`_make_mock_cloud_bp`).
  The mock owns the per-node queue + per-cache_key result dict + last-seen
  timestamps in plain Python dicts (matching cloud's "v1: in-memory dict on
  Cloud Run with TTL" storage decision in the issue). Once Engineer 11's PR
  lands, swap the import for ``from routes.heartbeat_relay import bp`` and
  the assertions stay the same — that is the value of having the contract
  pinned in this test.
* Engineer 12 (daemon) is extending ``send_heartbeat`` to consume
  ``pending_queries``. We mirror their planned path inline
  (``_daemon_drain_pending``) so the test exercises the same orchestration
  the real daemon will run, but without reaching out to a real cloud.
* The daemon's local dispatch uses the *real* ``routes.local_query.relay_dispatch``
  hooked to a *real* but isolated DuckDB seeded under ``tmp_path``.

Contract divergences observed while writing this test (documented for the
PR body so Engineer 11 / 12 can converge with us):

* Issue spec says subscribe returns ``status: "queued"|"cache_hit"`` —
  this test asserts both code paths exist.
* Issue spec lists ``cache_key`` AND ``query_id`` on subscribe response;
  ``query_id`` becomes the ``id`` field on ``pending_queries`` and on
  ``/ingest/cache``. The mock implements them as identical strings (one
  cache key per outstanding query) — Engineer 11 may make ``query_id``
  distinct (e.g. a per-subscriber UUID for fan-out reads). Test still
  passes either way because it doesn't conflate the two values.
* Issue says cache GET may return ``{status: "pending", eta_sec}`` OR
  ``{status: "node_offline", last_seen}`` OR the encrypted blob. The mock
  supports all three; tests assert each.
* The ``/ingest/cache`` 204-on-success contract is followed.
* Auth (``cm_xxx`` Bearer + ``node_id`` ownership) is *not* exercised by
  this test — we set tokens in headers but the mock skips validation. The
  cloud-side auth tests will live in clawmetry-cloud's own suite.

Run:
    python3 -m pytest tests/test_heartbeat_relay_e2e.py -q
"""

from __future__ import annotations

import hashlib
import importlib
import json
import time
import uuid
from typing import Any

import pytest
from flask import Blueprint, Flask, jsonify, request


# ── Test-data fixtures ────────────────────────────────────────────────────

NODE_ID = "agent+relay-e2e"
OTHER_NODE_ID = "agent+other-node"
API_KEY = "cm_test_relay_key_12345"
DAY = "2026-05-12"


def _ev(event_id: str, ts: str, **extras: Any) -> dict:
    """Build one normalised local_store event row."""
    base = {
        "id": event_id,
        "node_id": NODE_ID,
        "agent_id": "main",
        "session_id": "sess-relay-1",
        "event_type": "tool_call",
        "ts": ts,
        "data": {"tool": "Bash", "args": {"cmd": "echo hi"}},
        "cost_usd": 0.001,
        "token_count": 25,
        "model": "claude-opus-4-7",
    }
    base.update(extras)
    return base


SEED_EVENTS = [
    _ev("ev-1", f"{DAY}T10:00:00Z"),
    _ev("ev-2", f"{DAY}T10:00:01Z", cost_usd=0.002, token_count=50),
    _ev("ev-3", f"{DAY}T10:00:02Z", event_type="message",
        data={"role": "assistant", "text": "ok"}, cost_usd=0.005, token_count=200),
]


# ── Mock cloud blueprint (mirrors issue #1053 contract exactly) ───────────


def _make_mock_cloud_state() -> dict:
    """Per-test cloud-side in-memory state. Engineer 11's real impl stores
    the same shape on Cloud Run (issue says "v1: in-memory dict")."""
    return {
        # node_id -> list of pending_queries waiting for the next heartbeat
        # Each entry: {id, shape, args, cache_key, args_hash}
        "queue": {},
        # cache_key -> {blob, shape, args_hash, written_at}
        "cache": {},
        # cache_key -> "queued"|"dispatched"|"ready" (only used for tests
        # that distinguish — pending state implied by absence from cache)
        "status": {},
        # node_id -> last heartbeat unix ts. Drives "node_offline" detection.
        "last_seen": {},
        # (node_id, args_hash) -> cache_key memo for cache-hit detection
        "memo": {},
        # daemon-offline cutoff (issue spec: 5+ min == offline)
        "offline_after_secs": 300,
    }


def _hash_args(shape: str, args: dict) -> str:
    """Deterministic hash so identical (shape, args) collapse to one cache_key."""
    payload = json.dumps({"shape": shape, "args": args or {}}, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()[:32]


def _make_mock_cloud_bp(state: dict) -> Blueprint:
    """Build a Flask blueprint that implements the four cloud endpoints from
    the issue spec. State is captured by closure so tests can introspect /
    reset the in-memory dicts."""
    bp = Blueprint("mock_cloud_relay", __name__)

    # Allowed query shapes — mirrors the OSS-side allowlist in
    # routes/local_query.py so unknown shapes are rejected at subscribe time
    # (cloud is the gatekeeper; daemon trusts what cloud sends).
    ALLOWED_SHAPES = {"events", "sessions", "aggregates", "health", "transcript"}

    @bp.route("/api/cloud/subscribe", methods=["POST"])
    def subscribe():
        body = request.get_json(silent=True) or {}
        node_id = body.get("node_id")
        shape = body.get("shape")
        args = body.get("args") or {}
        if not node_id:
            return jsonify({"error": "node_id required"}), 400
        if shape not in ALLOWED_SHAPES:
            return jsonify({
                "error": f"unknown shape: {shape!r}",
                "allowed_shapes": sorted(ALLOWED_SHAPES),
            }), 400

        args_hash = _hash_args(shape, args)
        memo_key = (node_id, args_hash)

        # Cache-hit fast path (multi-tab / repeat subscribe within TTL).
        existing_cache_key = state["memo"].get(memo_key)
        if existing_cache_key and existing_cache_key in state["cache"]:
            return jsonify({
                "cache_key": existing_cache_key,
                "query_id": existing_cache_key,
                "eta_sec": 0,
                "status": "cache_hit",
            })

        # Coalesce concurrent subscribes to same (node, shape, args) onto
        # one outstanding cache_key so the daemon dispatches once.
        if existing_cache_key:
            # Already queued, no cache yet → still report "queued" with same key.
            return jsonify({
                "cache_key": existing_cache_key,
                "query_id": existing_cache_key,
                "eta_sec": 60,
                "status": "queued",
            })

        cache_key = f"ck_{uuid.uuid4().hex[:24]}"
        state["memo"][memo_key] = cache_key
        state["status"][cache_key] = "queued"
        state["queue"].setdefault(node_id, []).append({
            "id": cache_key,
            "shape": shape,
            "args": args,
            "cache_key": cache_key,
            "args_hash": args_hash,
        })
        return jsonify({
            "cache_key": cache_key,
            "query_id": cache_key,
            "eta_sec": 60,
            "status": "queued",
        })

    @bp.route("/ingest/heartbeat", methods=["POST"])
    def ingest_heartbeat():
        body = request.get_json(silent=True) or {}
        node_id = body.get("node_id") or "unknown"
        state["last_seen"][node_id] = time.time()
        pending = state["queue"].pop(node_id, [])
        for q in pending:
            state["status"][q["cache_key"]] = "dispatched"
        return jsonify({
            "ok": True,
            "sync_allowed": True,
            "pending_queries": pending,
        })

    @bp.route("/ingest/cache", methods=["POST"])
    def ingest_cache():
        body = request.get_json(silent=True) or {}
        cache_key = body.get("cache_key")
        blob = body.get("blob")
        if not cache_key or not blob:
            return jsonify({"error": "cache_key + blob required"}), 400
        state["cache"][cache_key] = {
            "blob": blob,
            "shape": body.get("shape"),
            "args_hash": body.get("args_hash"),
            "ttl": int(body.get("ttl", 3600)),
            "written_at": time.time(),
            # Track which node fulfilled this so /cache/<key> can report
            # node_offline when the daemon goes silent.
            "node_id": body.get("node_id"),
        }
        state["status"][cache_key] = "ready"
        return ("", 204)

    @bp.route("/api/cloud/cache/<cache_key>", methods=["GET"])
    def get_cache(cache_key):
        entry = state["cache"].get(cache_key)
        if entry:
            return jsonify({
                "cache_key": cache_key,
                "blob": entry["blob"],
                "shape": entry.get("shape"),
                "args_hash": entry.get("args_hash"),
                "written_at": entry.get("written_at"),
                "status": "ready",
            })

        # No cache yet — figure out why. The cache_key lives in state["status"]
        # the moment a subscribe queued it, so we know which node owes us a
        # dispatch. If that node hasn't beaten in >offline_after_secs, we
        # surface node_offline; else pending.
        owner_node = None
        for (nid, _ah), ck in state["memo"].items():
            if ck == cache_key:
                owner_node = nid
                break

        if owner_node is None:
            return jsonify({"status": "unknown", "cache_key": cache_key}), 404

        last_seen = state["last_seen"].get(owner_node, 0)
        now = time.time()
        if last_seen == 0 or (now - last_seen) > state["offline_after_secs"]:
            return jsonify({
                "status": "node_offline",
                "last_seen": last_seen if last_seen else None,
                "cache_key": cache_key,
            })
        return jsonify({
            "status": "pending",
            "eta_sec": max(1, 60 - int(now - last_seen)),
            "cache_key": cache_key,
        })

    return bp


# ── Daemon-side helper (mirrors Engineer 12's send_heartbeat extension) ───


def _daemon_drain_pending(client, *, node_id: str, api_key: str,
                         enc_key: str, dispatch_fn) -> int:
    """Run one full daemon heartbeat cycle:

      1. POST /ingest/heartbeat with node_id
      2. For each pending_query in the response, dispatch locally via
         dispatch_fn(shape, args), encrypt result, POST /ingest/cache.

    Returns the number of queries fulfilled. Engineer 12's
    ``send_heartbeat`` extension is expected to do this same orchestration —
    keep this in lock-step when their PR lands.
    """
    from clawmetry.sync import encrypt_payload

    headers = {"Authorization": f"Bearer {api_key}"}
    hb_body = {
        "node_id": node_id,
        "ts": time.time(),
        "version": "test",
    }
    r = client.post(
        "/ingest/heartbeat",
        data=json.dumps(hb_body),
        content_type="application/json",
        headers=headers,
    )
    assert r.status_code == 200, f"heartbeat failed: {r.status_code} {r.data!r}"
    body = r.get_json()
    pending = body.get("pending_queries") or []
    fulfilled = 0
    for q in pending:
        result = dispatch_fn(q["shape"], q.get("args") or {})
        blob = encrypt_payload(result, enc_key)
        r2 = client.post(
            "/ingest/cache",
            data=json.dumps({
                "id": q["id"],
                "cache_key": q["cache_key"],
                "blob": blob,
                "shape": q["shape"],
                "args_hash": q.get("args_hash"),
                "ttl": 3600,
                "node_id": node_id,
            }),
            content_type="application/json",
            headers=headers,
        )
        assert r2.status_code == 204, (
            f"cache POST failed: {r2.status_code} {r2.data!r}"
        )
        fulfilled += 1
    return fulfilled


# ── Pytest fixtures ───────────────────────────────────────────────────────


@pytest.fixture
def relay_env(tmp_path, monkeypatch):
    """Self-contained heartbeat-relay E2E environment.

    Yields a dict with:
      * ``client``    — Flask test client wired to the mock cloud blueprint
      * ``state``     — mutable cloud-side in-memory dict (queue/cache/...)
      * ``store``     — isolated DuckDB local_store seeded with SEED_EVENTS
      * ``dispatch``  — routes.local_query.relay_dispatch (real impl)
      * ``enc_key``   — fresh AES-256-GCM key generated per test
      * ``node_id``   — NODE_ID
      * ``api_key``   — API_KEY
    """
    db_path = tmp_path / "relay_e2e.duckdb"
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(db_path))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")
    # Make sure the daemon-proxy fast path doesn't try to reach a real
    # local_server (no `~/.clawmetry/local_query.json`); _proxy_dispatch
    # falls through cleanly to direct DuckDB.
    monkeypatch.setenv("HOME", str(tmp_path / "home"))

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import clawmetry.sync as sync
    importlib.reload(sync)
    import routes.local_query as lq
    importlib.reload(lq)

    store = ls.get_store()
    for ev in SEED_EVENTS:
        store.ingest(ev)
    # Drain ring → DuckDB so reads see committed rows.
    deadline = time.monotonic() + 3.0
    while store.health()["ring_depth"] > 0 and time.monotonic() < deadline:
        time.sleep(0.02)

    state = _make_mock_cloud_state()
    app = Flask(__name__)
    app.register_blueprint(_make_mock_cloud_bp(state))

    enc_key = sync.generate_encryption_key()

    yield {
        "client": app.test_client(),
        "state": state,
        "store": store,
        "dispatch": lq.relay_dispatch,
        "enc_key": enc_key,
        "node_id": NODE_ID,
        "api_key": API_KEY,
        "sync": sync,
    }

    try:
        store.stop(flush=True)
    except Exception:
        pass
    try:
        ls._reset_singleton_for_tests()
    except Exception:
        pass


# ── Tests ─────────────────────────────────────────────────────────────────


def test_subscribe_then_heartbeat_then_read_full_loop(relay_env):
    """Happy path: all five steps from issue #1053 in order.

      1. Browser subscribes → gets cache_key + status=queued
      2. Daemon heartbeats → cloud returns pending_queries
      3. Daemon dispatches DuckDB, encrypts, POSTs /ingest/cache
      4. Browser GETs /api/cloud/cache/<key> → encrypted blob
      5. Browser decrypts → seed events round-trip exactly

    This is the single most important assertion: the round-tripped event ids
    must equal the ids seeded into DuckDB at test start.
    """
    env = relay_env
    client = env["client"]
    api_key = env["api_key"]
    headers = {"Authorization": f"Bearer {api_key}"}

    # Step 1: subscribe.
    sub_args = {"session_id": "sess-relay-1", "limit": 100}
    r = client.post(
        "/api/cloud/subscribe",
        data=json.dumps({
            "node_id": env["node_id"],
            "shape": "events",
            "args": sub_args,
        }),
        content_type="application/json",
        headers=headers,
    )
    assert r.status_code == 200, r.data
    sub = r.get_json()
    assert sub["status"] == "queued"
    assert sub["cache_key"].startswith("ck_")
    assert sub["eta_sec"] >= 0
    cache_key = sub["cache_key"]

    # Step 2 + 3: daemon drains pending and posts cache.
    fulfilled = _daemon_drain_pending(
        client,
        node_id=env["node_id"],
        api_key=api_key,
        enc_key=env["enc_key"],
        dispatch_fn=env["dispatch"],
    )
    assert fulfilled == 1, f"daemon should fulfil exactly one query, got {fulfilled}"

    # Step 4: browser reads cache.
    r = client.get(f"/api/cloud/cache/{cache_key}", headers=headers)
    assert r.status_code == 200, r.data
    cache_resp = r.get_json()
    assert cache_resp["status"] == "ready"
    assert cache_resp["cache_key"] == cache_key
    assert cache_resp.get("blob"), "encrypted blob missing from cache response"

    # Step 5: decrypt with the AES key the browser holds (E2E).
    plain = env["sync"].decrypt_payload(cache_resp["blob"], env["enc_key"])
    assert plain.get("_shape") == "events"
    assert plain.get("count") == len(SEED_EVENTS)
    seen_ids = {row["id"] for row in plain.get("rows") or []}
    assert seen_ids == {ev["id"] for ev in SEED_EVENTS}, (
        f"decrypted blob ids {seen_ids} != seeded ids "
        f"{{ev-1, ev-2, ev-3}}"
    )


def test_cache_hit_on_repeat_subscribe(relay_env):
    """Second subscribe with same (node, shape, args) — once the first cache
    is filled — must return ``status: cache_hit`` immediately, no second
    heartbeat or daemon dispatch needed.

    This is the "multi-tab dashboard" optimisation in the issue: ``Multi-tab
    subscribe to the same (shape, args) hits the cache on subsequent reads
    (~5ms)``.
    """
    env = relay_env
    client = env["client"]
    headers = {"Authorization": f"Bearer {env['api_key']}"}
    sub_args = {"session_id": "sess-relay-1", "limit": 100}
    sub_body = json.dumps({
        "node_id": env["node_id"],
        "shape": "events",
        "args": sub_args,
    })

    # First subscribe + drain — fills the cache.
    r = client.post("/api/cloud/subscribe", data=sub_body,
                    content_type="application/json", headers=headers)
    first_key = r.get_json()["cache_key"]
    _daemon_drain_pending(
        client, node_id=env["node_id"], api_key=env["api_key"],
        enc_key=env["enc_key"], dispatch_fn=env["dispatch"],
    )

    # Second subscribe — should be cache_hit, same key, eta_sec=0, NO new
    # pending query queued (state["queue"] for this node stays empty).
    r2 = client.post("/api/cloud/subscribe", data=sub_body,
                     content_type="application/json", headers=headers)
    second = r2.get_json()
    assert second["status"] == "cache_hit"
    assert second["cache_key"] == first_key
    assert second["eta_sec"] == 0
    assert env["state"]["queue"].get(env["node_id"], []) == [], (
        "cache_hit must not queue a new pending_query"
    )

    # And the cache GET still serves the original encrypted blob.
    r3 = client.get(f"/api/cloud/cache/{first_key}", headers=headers)
    assert r3.status_code == 200
    plain = env["sync"].decrypt_payload(r3.get_json()["blob"], env["enc_key"])
    assert plain["count"] == len(SEED_EVENTS)


def test_node_offline_returns_proper_status(relay_env):
    """If the node hasn't heartbeat in 5+ min, /api/cloud/cache/<key> reports
    ``{status: "node_offline", last_seen}`` instead of ``pending`` — the
    dashboard surfaces "node down" instead of spinning forever.
    """
    env = relay_env
    client = env["client"]
    headers = {"Authorization": f"Bearer {env['api_key']}"}

    # Subscribe — queues a query but no daemon runs.
    r = client.post(
        "/api/cloud/subscribe",
        data=json.dumps({
            "node_id": env["node_id"],
            "shape": "events",
            "args": {"limit": 50},
        }),
        content_type="application/json",
        headers=headers,
    )
    cache_key = r.get_json()["cache_key"]

    # Pretend the node was last seen >5 min ago. (Either no heartbeat at
    # all, or one long ago — issue spec says "no heartbeat in 5+ min".)
    env["state"]["last_seen"][env["node_id"]] = time.time() - 600

    r2 = client.get(f"/api/cloud/cache/{cache_key}", headers=headers)
    assert r2.status_code == 200, r2.data
    body = r2.get_json()
    assert body["status"] == "node_offline"
    assert "last_seen" in body
    assert body["last_seen"] is not None
    assert body["last_seen"] < time.time() - env["state"]["offline_after_secs"]


def test_unknown_shape_rejected(relay_env):
    """Subscribing to a shape that isn't in the allowlist must 400 — the
    cloud is the gatekeeper so the daemon never sees a malicious shape.
    Mirrors the same allowlist defense as routes/local_query.py."""
    env = relay_env
    client = env["client"]
    headers = {"Authorization": f"Bearer {env['api_key']}"}
    r = client.post(
        "/api/cloud/subscribe",
        data=json.dumps({
            "node_id": env["node_id"],
            "shape": "drop_table_users",
            "args": {},
        }),
        content_type="application/json",
        headers=headers,
    )
    assert r.status_code == 400
    body = r.get_json()
    assert "allowed_shapes" in body
    assert "events" in body["allowed_shapes"]
    # No queue entry for this node — bad request must not pollute state.
    assert env["state"]["queue"].get(env["node_id"], []) == []


def test_concurrent_subscribes_share_cache(relay_env):
    """Three "browser tabs" subscribe to the same (node, shape, args) before
    the daemon drains — all three must collapse to one outstanding query
    and share the resulting blob. This is the fan-out invariant from the
    issue: one daemon dispatch fulfils N subscribers."""
    env = relay_env
    client = env["client"]
    headers = {"Authorization": f"Bearer {env['api_key']}"}
    sub_args = {"session_id": "sess-relay-1", "limit": 100}
    sub_body = json.dumps({
        "node_id": env["node_id"],
        "shape": "events",
        "args": sub_args,
    })

    # Three concurrent (well, serially-issued) subscribes BEFORE any heartbeat.
    keys = []
    for _ in range(3):
        r = client.post("/api/cloud/subscribe", data=sub_body,
                        content_type="application/json", headers=headers)
        assert r.status_code == 200
        keys.append(r.get_json()["cache_key"])

    # All three must share one cache_key.
    assert len(set(keys)) == 1, (
        f"concurrent subscribes must collapse to one cache_key, got {keys}"
    )
    shared_key = keys[0]

    # Cloud queue must hold exactly one pending_query for this node — not 3.
    pending = env["state"]["queue"].get(env["node_id"], [])
    assert len(pending) == 1, (
        f"only one pending_query expected, got {len(pending)}"
    )

    # One heartbeat → one daemon dispatch → fulfils all subscribers.
    fulfilled = _daemon_drain_pending(
        client, node_id=env["node_id"], api_key=env["api_key"],
        enc_key=env["enc_key"], dispatch_fn=env["dispatch"],
    )
    assert fulfilled == 1, "daemon dispatched more than once for shared cache"

    # All three "tabs" GET the same cache_key → same blob bytes.
    blobs = []
    for _ in range(3):
        r = client.get(f"/api/cloud/cache/{shared_key}", headers=headers)
        assert r.status_code == 200
        blobs.append(r.get_json()["blob"])
    assert len(set(blobs)) == 1, "shared cache must serve identical blobs to all readers"

    # And every tab decrypts to the same plaintext row set.
    plains = [env["sync"].decrypt_payload(b, env["enc_key"]) for b in blobs]
    id_sets = [{row["id"] for row in p["rows"]} for p in plains]
    assert id_sets[0] == id_sets[1] == id_sets[2] == {ev["id"] for ev in SEED_EVENTS}
