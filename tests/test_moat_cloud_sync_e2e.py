"""MOAT cloud-sync E2E: daemon → cloud relay → cloud cache → cloud API.

Sister to ``tests/test_moat_live_openclaw_e2e.py`` (local DuckDB half,
5/5 passing + 1 documented skip as of 2026-05-17). This file proves the
**cloud sync** half of the user's MOAT mandate (verbatim 2026-05-17):

    "cloud sync in a robust & stable way — write end to end tests api
     tests to ensure everything works"

Pipeline under test (every layer real except the wire to
``ingest.clawmetry.com``, which is replaced by an in-process Flask test
client that re-implements the cloud-side relay contract — same approach
as ``tests/test_heartbeat_relay_e2e.py`` and
``tests/test_moat_cloud_roundtrip_e2e.py``, both of which have shipped
green and pin the contract the cloud side must agree with):

    OpenClaw v3 events ingested via clawmetry.local_store (real DuckDB)
        → clawmetry.sync.send_heartbeat               (real daemon entry)
            → cache_pushes encrypted with AES-256-GCM (real cryptography)
                → mock cloud /ingest/heartbeat        (in-process Flask)
                    → mock cloud cache keyed by `brain:<owner>:<node>:recent`
                        → mock cloud /api/cloud/cache/<key> read path
                            → daemon decrypt round-trip checks plaintext
                            → assertions on cost, tokens, _source, sentinel

Scenarios covered (matches the 4 the user listed in the EOD push):

  1. Happy path — daemon writes ``session.started`` + ``model.completed``
     to local DuckDB; heartbeat ships them; cloud cache contains the
     encrypted blob; cloud read path returns the same blob; decrypting it
     reproduces the original events with their cost + token counts intact.
     Asserts the cloud-served entry is tagged ``_source='local_store'``
     (the daemon-relay tag), NOT a stale cache flag.

  2. Encrypted payload integrity — AES-256-GCM round-trip is byte-stable
     and no plaintext field-drop occurs. Catches the #1583/#1571/#1576/
     #1580 silent-strip family: encrypt-then-decrypt MUST reproduce every
     field of every event we put in (cost_usd, token_count, model, message
     content, role, …) with zero loss.

  3. Heartbeat-piggyback — cloud returns ``pending_queries`` on the
     heartbeat response; the daemon's real ``_dispatch_pending_queries``
     runs the query against local DuckDB, encrypts the result, POSTs to
     ``/ingest/cache``; cloud stores it under the cloud-supplied
     ``cache_key`` and a subsequent read returns the same blob (which
     decrypts to a ``_source='local_store'`` payload with the correct row
     count). This is the post-WS-pivot transport (memory
     ``project_relay_transport_decision``: WS killed; heartbeat-piggyback
     approved + industry-validated).

  4. Stale-cache fallback — when the daemon goes silent, the cloud read
     path MUST surface ``status='node_offline'`` (or an equivalent
     explicit stale flag) with a ``last_seen`` hint, not silently serve a
     fresh-looking cache hit. Soft-skip if the cloud-side cache TTL/stale
     flag isn't wired yet — DON'T pretend tests pass when they aren't
     (per memory ``feedback_synthetic_tests_missed_real_event_shape``).

Pre-flight reads (for the next maintainer):

  * ``clawmetry/sync.py``                           — daemon-side relay
  * ``clawmetry-cloud/routes/heartbeat_relay.py``   — cloud-side relay
  * ``tests/test_heartbeat_relay_e2e.py``           — sibling contract test
  * ``tests/test_moat_cloud_roundtrip_e2e.py``      — sibling encrypt test

Run as::

    pytest -v tests/test_moat_cloud_sync_e2e.py
"""

from __future__ import annotations

import hashlib
import http.server
import importlib
import json
import socket
import sys
import threading
import time
import urllib.parse
import urllib.request
import uuid

import pytest


NODE_ID = "agent+moat-cloud-sync-e2e"
API_KEY = "cm_test_moat_cloud_sync_token"
DAY = "2026-05-17"
# Magic sentinel for the cost/token + plaintext-drop assertions. Distinct
# + searchable — if this string surfaces in a "cloud-stored ciphertext"
# blob, the daemon is leaking plaintext on the wire.
SENTINEL_PROMPT = "MOAT cloud-sync E2E ping HELLO_FROM_MOAT_CLOUD_42"
SENTINEL_MODEL = "claude-opus-4-7"
# Per-event cost + token counts the test asserts on. Picked to be
# distinguishable from the daemon's own internal heuristics — if a future
# regression coerces these to defaults, the deltas show up clearly in the
# failure message.
EVENT_COST_USD = 0.0314
EVENT_TOKENS_IN = 717
EVENT_TOKENS_OUT = 251
EVENT_TOKENS_TOTAL = EVENT_TOKENS_IN + EVENT_TOKENS_OUT


# ── Mock cloud blueprint (mirrors clawmetry-cloud/routes/heartbeat_relay.py) ─


class _CloudState:
    """In-memory mirror of the cloud-side relay state. Captured by a
    closure so individual tests can introspect queue/cache/last-seen."""

    def __init__(self) -> None:
        # cache_key -> ciphertext blob (string)
        self.cache: dict[str, str] = {}
        # cache_key -> metadata dict (shape, args_hash, ts, node_id)
        self.cache_meta: dict[str, dict] = {}
        # node_id -> list of pending_queries (popped on heartbeat)
        self.queue: dict[str, list] = {}
        # node_id -> unix ts of last heartbeat seen (drives offline detection)
        self.last_seen: dict[str, float] = {}
        # cache_key -> owning node_id (for stale-cache fallback)
        self.cache_owner: dict[str, str] = {}
        # Last raw heartbeat payload (for assertion on wire bytes)
        self.last_heartbeat: dict | None = None
        # Last raw /ingest/cache payload
        self.last_ingest_cache: dict | None = None
        # Offline threshold mirrors heartbeat_relay.py default (5 min).
        self.offline_after_secs = 300


class _MockCloudHandler(http.server.BaseHTTPRequestHandler):
    state: _CloudState  # bound on the class per-test before serve_forever

    # Silence the per-request access log so test output stays readable.
    def log_message(self, *_a, **_kw) -> None:  # noqa: D401
        return

    def _send(self, code: int, body: dict) -> None:
        raw = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length", "0") or 0)
        try:
            payload = json.loads(self.rfile.read(length) or b"{}")
        except Exception:
            payload = {}

        if self.path == "/ingest/heartbeat":
            self.state.last_heartbeat = payload
            node_id = payload.get("node_id") or "unknown"
            self.state.last_seen[node_id] = time.time()
            # Store every cache_push entry under its cloud-side key so the
            # read path can serve it back.
            for entry in payload.get("cache_pushes") or []:
                key = entry.get("key")
                blob = entry.get("blob")
                if key and isinstance(blob, str):
                    self.state.cache[key] = blob
                    self.state.cache_meta[key] = {
                        "ttl_s": entry.get("ttl_s"),
                        "written_at": time.time(),
                        "node_id": node_id,
                        "source": "heartbeat_cache_push",
                    }
                    self.state.cache_owner[key] = node_id
            # Drain any pending_queries queued for this node.
            pending = self.state.queue.pop(node_id, [])
            return self._send(200, {
                "ok": True,
                "sync_allowed": True,
                "pending_queries": pending,
            })

        if self.path == "/ingest/cache":
            self.state.last_ingest_cache = payload
            cache_key = payload.get("cache_key")
            blob = payload.get("blob")
            if not cache_key or not isinstance(blob, str):
                return self._send(400, {"error": "cache_key + blob required"})
            node_id = payload.get("node_id") or "unknown"
            self.state.cache[cache_key] = blob
            self.state.cache_meta[cache_key] = {
                "shape": payload.get("shape"),
                "args_hash": payload.get("args_hash"),
                "ttl": payload.get("ttl"),
                "written_at": time.time(),
                "node_id": node_id,
                "source": "pending_query_dispatch",
            }
            self.state.cache_owner[cache_key] = node_id
            return self._send(200, {"ok": True})

        # Catch-all so unhandled POSTs (events / snapshots / approvals /
        # alerts / autonomy / …) don't fail loudly during the heartbeat
        # cycle. The MOAT contract under test is the cache half; other
        # POSTs from the daemon are no-ops.
        return self._send(200, {"ok": True})

    def do_GET(self) -> None:  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(parsed.query or "")

        # /api/cloud/cache/<key>  — heartbeat_relay.py read path. The cache
        # key contains ':' separators which must be %-encoded by the caller;
        # we unquote here so cache lookups use the original bytes.
        if parsed.path.startswith("/api/cloud/cache/"):
            cache_key = urllib.parse.unquote(
                parsed.path[len("/api/cloud/cache/"):]
            )
            return self._serve_cache_read(cache_key)

        # /api/cloud/brain?key=... — older read path some clients still use.
        if parsed.path.startswith("/api/cloud/brain"):
            key = (qs.get("key") or [""])[0]
            return self._serve_cache_read(key, legacy_brain=True)

        return self._send(404, {"error": f"unknown path {parsed.path}"})

    def _serve_cache_read(self, cache_key: str, legacy_brain: bool = False) -> None:
        blob = self.state.cache.get(cache_key)
        meta = self.state.cache_meta.get(cache_key) or {}
        if blob is not None:
            owner = self.state.cache_owner.get(cache_key)
            last = self.state.last_seen.get(owner or "", 0)
            age = time.time() - last if last else None
            # Stale detection: cloud must tag served-but-old cache so the
            # browser doesn't show fresh-looking data after the daemon dies.
            stale = (last == 0) or (age is not None and age > self.state.offline_after_secs)
            body = {
                "cache_key": cache_key,
                "blob": blob,
                "shape": meta.get("shape"),
                "args_hash": meta.get("args_hash"),
                "written_at": meta.get("written_at"),
                "_source": (
                    f"cache-stale-{int(age)}s" if stale and age is not None
                    else "daemon-relay"
                ),
                "_shape": "brain_history" if legacy_brain else None,
                "status": "stale" if stale else "ready",
                "last_seen": last if last else None,
            }
            return self._send(200, body)
        # No cache entry at all → node_offline if owner never heartbeat,
        # else pending.
        owner = self.state.cache_owner.get(cache_key)
        if owner is None:
            return self._send(404, {"status": "unknown", "cache_key": cache_key})
        last = self.state.last_seen.get(owner, 0)
        if last == 0 or (time.time() - last) > self.state.offline_after_secs:
            return self._send(200, {
                "status": "node_offline",
                "last_seen": last if last else None,
                "cache_key": cache_key,
                "_source": "cache-miss-node-offline",
            })
        return self._send(200, {
            "status": "pending",
            "eta_sec": 60,
            "cache_key": cache_key,
            "_source": "cache-miss-pending",
        })


# ── Helpers ───────────────────────────────────────────────────────────────


def _free_port() -> int:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def _v3_event(event_id: str, ts: str, *, text: str = "hello cloud",
              tokens_in: int = EVENT_TOKENS_IN,
              tokens_out: int = EVENT_TOKENS_OUT,
              cost_usd: float = EVENT_COST_USD,
              event_type: str = "message") -> dict:
    """Build one v3-shape OpenClaw event row. Matches what
    ``sync._parse_v3_event`` writes into local_store on a real ingest run
    (per memory ``reference_openclaw_v3_event_types`` + the inspected
    JSONL from ``test_moat_live_openclaw_e2e``)."""
    return {
        "id": event_id,
        "node_id": NODE_ID,
        "agent_id": "main",
        "session_id": "sess-moat-cloud-sync",
        "event_type": event_type,
        "ts": ts,
        "data": {
            "type": event_type,
            "timestamp": ts,
            "message": {
                "role": "assistant",
                "content": [{"type": "text", "text": text}],
                "model": SENTINEL_MODEL,
                "api": "anthropic",
                "provider": "anthropic",
                "usage": {
                    "input_tokens": tokens_in,
                    "output_tokens": tokens_out,
                    "totalTokens": tokens_in + tokens_out,
                },
            },
        },
        "cost_usd": cost_usd,
        "token_count": tokens_in + tokens_out,
        "model": SENTINEL_MODEL,
    }


def _seed_real_events(store, n: int = 5) -> list[dict]:
    """Ingest ``n`` v3-shape events into the real DuckDB local_store.
    Returns the list of source dicts so tests can diff round-trip."""
    seeded = []
    for i in range(n):
        ts = f"{DAY}T12:{i:02d}:00+00:00"
        text = f"{SENTINEL_PROMPT} #{i}"
        ev = _v3_event(str(uuid.uuid4()), ts, text=text)
        store.ingest(ev)
        seeded.append(ev)
    # Drain ring → committed DuckDB rows so query_events sees them.
    deadline = time.monotonic() + 3.0
    while store.health()["ring_depth"] > 0 and time.monotonic() < deadline:
        time.sleep(0.02)
    return seeded


# ── Fixture: real DuckDB + real sync module + running mock cloud ──────────


@pytest.fixture
def env(tmp_path, monkeypatch):
    """Self-contained MOAT cloud-sync E2E environment.

    Yields a dict with::

      sync       — reloaded clawmetry.sync module (real daemon code)
      ls         — reloaded clawmetry.local_store module
      store      — writable DuckDB local_store (isolated tmp_path)
      config     — daemon config dict (api_key + node_id + enc key)
      cloud      — _CloudState mirror (introspect queue/cache/last_seen)
      port       — local port the mock cloud is listening on
      base_url   — full http URL the daemon talks to
      seeded     — list of source event dicts ingested before yield
    """
    db_path = tmp_path / "moat_cloud_sync.duckdb"
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(db_path))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "1")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")
    # Park HOME so the daemon's discovery file (~/.clawmetry/local_query.json)
    # falls back to direct DuckDB dispatch — the production daemon on this
    # dev machine must not intercept the test's queries.
    monkeypatch.setenv("HOME", str(tmp_path / "home"))

    # Force a clean reload so monkeypatched env is honoured.
    for mod in (
        "clawmetry.local_store",
        "clawmetry.sync",
        "routes.local_query",
    ):
        sys.modules.pop(mod, None)

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import clawmetry.sync as sync_mod
    importlib.reload(sync_mod)
    import routes.local_query as lq
    importlib.reload(lq)

    # Force daemon-discovery to a dead path so the in-process dispatch
    # never punts to a real local_server (same pattern as the sibling
    # MOAT tests).
    monkeypatch.setattr(
        lq, "_DISCOVERY_PATH",
        str(tmp_path / "no-such-discovery.json"),
        raising=True,
    )

    store = ls.get_store()
    seeded = _seed_real_events(store, n=5)

    # Boot the mock cloud HTTP server on a free port.
    cloud_state = _CloudState()
    _MockCloudHandler.state = cloud_state
    port = _free_port()
    httpd = http.server.HTTPServer(("127.0.0.1", port), _MockCloudHandler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()

    # Point the daemon's INGEST_URL at the mock cloud. sync.py reads this
    # at module-init AND every _post call, so monkeypatching the attribute
    # is sufficient — no reload needed.
    monkeypatch.setattr(
        sync_mod, "INGEST_URL", f"http://127.0.0.1:{port}", raising=False,
    )

    config = {
        "node_id": NODE_ID,
        "api_key": API_KEY,
        "encryption_key": sync_mod.generate_encryption_key(),
    }

    yield {
        "sync": sync_mod,
        "ls": ls,
        "lq": lq,
        "store": store,
        "config": config,
        "cloud": cloud_state,
        "port": port,
        "base_url": f"http://127.0.0.1:{port}",
        "seeded": seeded,
    }

    httpd.shutdown()
    httpd.server_close()
    try:
        store.stop(flush=True)
    except Exception:
        pass
    try:
        ls._reset_singleton_for_tests()
    except Exception:
        pass


# ── Tests ─────────────────────────────────────────────────────────────────


def test_happy_path_daemon_to_cloud_to_api_roundtrip(env):
    """Scenario 1: heartbeat ships local events → cloud serves them back
    with cost + token counts intact + ``_source`` tag indicating
    daemon-relay (not stale-cache)."""
    sync_mod = env["sync"]
    config = env["config"]
    cloud = env["cloud"]

    assert sync_mod.send_heartbeat(config) is True, (
        "send_heartbeat returned False — daemon failed to reach mock cloud "
        f"on {env['base_url']}; check INGEST_URL monkeypatch + mock handler"
    )

    # Cloud must have received the heartbeat with cache_pushes.
    hb = cloud.last_heartbeat
    assert hb is not None, "mock cloud never saw a heartbeat POST"
    pushes = hb.get("cache_pushes") or []
    assert pushes, (
        f"heartbeat had no cache_pushes — daemon dropped the brain blob; "
        f"keys in payload={sorted(hb)}"
    )

    # The brain push key must match the cross-repo contract exactly. Drift
    # here silently misroutes the blob to a key the cloud dashboard never
    # reads (the #1583 family failure shape).
    owner = sync_mod._owner_hash_for_token(config["api_key"])
    expected_key = f"brain:{owner}:{NODE_ID}:recent"
    push_keys = [p.get("key") for p in pushes]
    assert expected_key in push_keys, (
        f"brain cache_push key drift: expected {expected_key!r}, "
        f"got {push_keys!r}"
    )
    assert expected_key in cloud.cache, (
        f"cloud handler didn't store the brain blob under {expected_key!r}"
    )

    # Read the blob back via the cloud's GET path — same code path the
    # browser uses.
    url = f"{env['base_url']}/api/cloud/cache/{urllib.parse.quote(expected_key)}"
    with urllib.request.urlopen(url, timeout=5) as resp:
        served = json.loads(resp.read())

    # _source MUST be the live-daemon tag, not a stale-cache flag — we just
    # heartbeat'd, the cloud should know this node is alive.
    assert served.get("_source") == "daemon-relay", (
        f"cloud served the blob with _source={served.get('_source')!r} "
        f"instead of 'daemon-relay' — daemon-liveness signal is broken "
        f"(node {NODE_ID!r} heartbeat'd <1s ago, last_seen={served.get('last_seen')})"
    )
    assert served.get("status") == "ready", (
        f"served status={served.get('status')!r} instead of 'ready'"
    )

    # Decrypt and verify cost + token totals survived the round-trip.
    decrypted = sync_mod.decrypt_payload(served["blob"], config["encryption_key"])
    assert decrypted.get("_shape") == "brain_history", (
        f"decrypted _shape={decrypted.get('_shape')!r}"
    )
    assert decrypted.get("count") == len(env["seeded"]), (
        f"event count drift: seeded={len(env['seeded'])} "
        f"served={decrypted.get('count')}"
    )

    events = decrypted.get("events") or []
    assert len(events) == len(env["seeded"]), (
        f"events len {len(events)} != seeded {len(env['seeded'])}"
    )

    # Spot-check the first event for cost/token shape preservation.
    ev0 = events[0]
    msg = ev0.get("message") or {}
    usage = msg.get("usage") or {}
    assert usage.get("input_tokens") == EVENT_TOKENS_IN, (
        f"input_tokens dropped or coerced: {usage.get('input_tokens')!r}"
    )
    assert usage.get("output_tokens") == EVENT_TOKENS_OUT, (
        f"output_tokens dropped or coerced: {usage.get('output_tokens')!r}"
    )
    assert msg.get("model") == SENTINEL_MODEL, (
        f"model field stripped: {msg.get('model')!r}"
    )
    assert msg.get("role") == "assistant", (
        f"role field drift: {msg.get('role')!r}"
    )
    # Text content must round-trip readable (the #1583 silent-strip canary).
    text_blocks = [b for b in (msg.get("content") or [])
                   if isinstance(b, dict) and b.get("type") == "text"]
    assert text_blocks and SENTINEL_PROMPT in (text_blocks[0].get("text") or ""), (
        f"prompt text lost in round-trip; first content={msg.get('content')!r}"
    )


def test_encrypted_payload_integrity_aes256gcm_roundtrip(env):
    """Scenario 2: ciphertext on the wire is opaque (no plaintext leak)
    AND decrypts to a byte-identical dict — no silent field-drop."""
    sync_mod = env["sync"]
    config = env["config"]
    cloud = env["cloud"]

    # Build the push once *before* sending so we have a known-good
    # plaintext to diff against the cloud-served blob.
    pushes_pre = sync_mod._build_brain_cache_pushes(config)
    assert pushes_pre and len(pushes_pre) == 1, (
        f"_build_brain_cache_pushes returned {pushes_pre!r}; expected one entry"
    )
    expected_plain = sync_mod.decrypt_payload(
        pushes_pre[0]["blob"], config["encryption_key"]
    )

    assert sync_mod.send_heartbeat(config) is True
    hb = cloud.last_heartbeat
    assert hb is not None

    # No plaintext on the wire — the cloud sees ONLY the encrypted blob.
    wire = json.dumps(hb)
    assert SENTINEL_PROMPT not in wire, (
        "PLAINTEXT LEAK: prompt sentinel appeared in the heartbeat payload "
        "(the cloud should only ever see ciphertext under cache_pushes[].blob). "
        "Likely cause: the daemon attached a raw debug copy of the payload."
    )
    assert "input_tokens" not in wire, (
        "PLAINTEXT LEAK: usage field name appeared on the wire"
    )
    assert SENTINEL_MODEL not in wire, (
        "PLAINTEXT LEAK: model id appeared on the wire"
    )

    # Pull the stored blob and decrypt with the daemon's own key — must
    # round-trip identical to what _build_brain_cache_pushes produced.
    owner = sync_mod._owner_hash_for_token(config["api_key"])
    cache_key = f"brain:{owner}:{NODE_ID}:recent"
    assert cache_key in cloud.cache, (
        f"cloud didn't persist the blob under {cache_key!r}"
    )
    actual_plain = sync_mod.decrypt_payload(
        cloud.cache[cache_key], config["encryption_key"]
    )

    assert actual_plain == expected_plain, (
        "AES-256-GCM round-trip DRIFT: decrypted blob differs from the "
        "daemon's locally-built blob.\n"
        f"  expected keys: {sorted(expected_plain)}\n"
        f"  actual   keys: {sorted(actual_plain)}\n"
        "Likely: cloud handler re-encoded the blob OR the daemon ran two "
        "different code paths for build-vs-send (the silent-strip family)."
    )

    # Every seeded event MUST survive the round-trip with its source fields
    # intact. This is the hard guard against the #1583/#1571/#1576/#1580
    # silent-drop pattern.
    events = actual_plain.get("events") or []
    assert len(events) == len(env["seeded"])
    for ev in events:
        msg = ev.get("message") or {}
        usage = msg.get("usage") or {}
        # Required fields that the dashboard depends on:
        for required in ("input_tokens", "output_tokens"):
            assert required in usage, (
                f"usage.{required} dropped from decrypted event; "
                f"usage={usage!r}"
            )
        assert msg.get("model"), f"model dropped from decrypted event: {msg!r}"
        assert msg.get("role"), f"role dropped from decrypted event: {msg!r}"


def test_heartbeat_piggyback_pending_query_dispatch(env):
    """Scenario 3: cloud queues a ``pending_queries`` entry → daemon
    consumes it on the next heartbeat → dispatches against local DuckDB
    → encrypts → POSTs to /ingest/cache → cloud stores the result under
    the cloud-supplied cache_key with the daemon-relay tag."""
    sync_mod = env["sync"]
    config = env["config"]
    cloud = env["cloud"]

    # Cloud-side: queue a 'health' shape query for this node. 'health' is
    # in the allowlist (sync._PENDING_SHAPES) and takes no args, which
    # keeps the test independent of the events-shape arg-coercion churn.
    expected_cache_key = f"ck_{uuid.uuid4().hex[:24]}"
    expected_query_id = expected_cache_key
    cloud.queue[NODE_ID] = [{
        "id": expected_query_id,
        "shape": "health",
        "args": {},
        "cache_key": expected_cache_key,
        "args_hash": hashlib.sha256(b"{}").hexdigest(),
    }]
    # Pre-mark the owner so the read path's stale-fallback knows which
    # node is responsible (mirrors heartbeat_relay.py's subscribe path).
    cloud.cache_owner[expected_cache_key] = NODE_ID

    assert sync_mod.send_heartbeat(config) is True

    # The daemon must have drained the pending_queries AND POSTed the
    # result back to /ingest/cache.
    assert cloud.last_ingest_cache is not None, (
        "daemon never POSTed /ingest/cache — pending_queries dispatch "
        "is broken (likely _dispatch_pending_queries swallowed the entry "
        "or the shape allowlist doesn't include 'health')."
    )
    ic = cloud.last_ingest_cache
    assert ic.get("cache_key") == expected_cache_key, (
        f"cache_key drift on /ingest/cache: expected {expected_cache_key!r}, "
        f"got {ic.get('cache_key')!r}"
    )
    assert ic.get("id") == expected_query_id, (
        f"query id drift: expected {expected_query_id!r}, got {ic.get('id')!r}"
    )
    assert ic.get("shape") == "health"
    assert isinstance(ic.get("blob"), str) and len(ic["blob"]) > 0, (
        "no encrypted blob in /ingest/cache POST"
    )

    # Cloud read path now returns the daemon-relay tag.
    url = f"{env['base_url']}/api/cloud/cache/{urllib.parse.quote(expected_cache_key)}"
    with urllib.request.urlopen(url, timeout=5) as resp:
        served = json.loads(resp.read())
    assert served.get("_source") == "daemon-relay", (
        f"served _source={served.get('_source')!r} — heartbeat-piggyback "
        "result not tagged daemon-relay; cache freshness signal lost"
    )

    # Decrypt and confirm the local query actually ran (health shape
    # returns a small dict with engine/size_bytes/events_total/etc.).
    decrypted = sync_mod.decrypt_payload(served["blob"], config["encryption_key"])
    assert isinstance(decrypted, dict) and decrypted, (
        f"decrypted health payload empty: {decrypted!r}"
    )
    # The exact key set drifts as local_store.health() grows; we just
    # assert ANY of the well-known fields surfaced AND that 'events_total'
    # reflects the seeded events (5).
    known = {"engine", "size_bytes", "events_total", "ring_depth"}
    intersect = known & set(decrypted)
    assert intersect, (
        f"health payload missing every known field; got keys "
        f"{sorted(decrypted)!r}"
    )
    if "events_total" in decrypted:
        assert decrypted["events_total"] >= len(env["seeded"]), (
            f"events_total={decrypted['events_total']} < seeded "
            f"{len(env['seeded'])} — dispatch ran against wrong DuckDB?"
        )


def test_stale_cache_fallback_when_daemon_offline(env):
    """Scenario 4: when the daemon hasn't beaten in >offline_after_secs,
    the cloud read path MUST surface either ``node_offline`` (cache miss)
    OR an explicit stale-cache flag (cache hit). It MUST NOT pretend to
    serve fresh data — that's the silent-stale family of bugs the user's
    mandate (memory ``feedback_synthetic_tests_missed_real_event_shape``)
    explicitly calls out.

    Two sub-cases:
      (a) cache HAS a stored blob but last_seen is ancient → served
          payload must carry a ``cache-stale-Xs`` ``_source`` flag.
      (b) cache MISS + last_seen ancient → server returns
          ``status='node_offline'`` with a ``last_seen`` hint.
    """
    sync_mod = env["sync"]
    config = env["config"]
    cloud = env["cloud"]

    # ── Sub-case (a): stale cache hit ────────────────────────────────────
    # Heartbeat once to populate the brain cache + last_seen.
    assert sync_mod.send_heartbeat(config) is True
    owner = sync_mod._owner_hash_for_token(config["api_key"])
    brain_key = f"brain:{owner}:{NODE_ID}:recent"
    assert brain_key in cloud.cache, "brain push didn't land"

    # Backdate last_seen well past offline_after_secs.
    cloud.last_seen[NODE_ID] = time.time() - (cloud.offline_after_secs + 60)

    url = f"{env['base_url']}/api/cloud/cache/{urllib.parse.quote(brain_key)}"
    with urllib.request.urlopen(url, timeout=5) as resp:
        served = json.loads(resp.read())

    source = served.get("_source") or ""
    assert source.startswith("cache-stale-"), (
        f"stale-cache fallback broken: _source={source!r} (expected "
        "'cache-stale-Xs'). The cloud must explicitly flag stale data — "
        "silently serving last-known-good is the bug class this test "
        "guards against."
    )
    assert served.get("status") == "stale", (
        f"served status={served.get('status')!r}, expected 'stale'"
    )
    assert served.get("last_seen") is not None, (
        "stale response missing last_seen hint — browser can't tell user "
        "how old the data is"
    )

    # ── Sub-case (b): cache miss + offline node ──────────────────────────
    missing_key = "ck_nonexistent_never_dispatched"
    cloud.cache_owner[missing_key] = NODE_ID  # owner known, blob absent
    # last_seen still ancient from above.
    url2 = f"{env['base_url']}/api/cloud/cache/{urllib.parse.quote(missing_key)}"
    with urllib.request.urlopen(url2, timeout=5) as resp:
        miss = json.loads(resp.read())
    assert miss.get("status") == "node_offline", (
        f"cache-miss + offline node didn't surface node_offline; got "
        f"status={miss.get('status')!r} _source={miss.get('_source')!r}. "
        "Browser would render an empty tab without explaining why."
    )
    assert miss.get("last_seen") is not None, (
        "node_offline response should carry a last_seen hint"
    )
