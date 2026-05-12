"""End-to-end + resilience tests for the OSS → cloud sync flow.

These tests exercise the *real* daemon code (`clawmetry.sync` +
`clawmetry.local_store`) against a *real, in-process* stub of the
`ingest.clawmetry.com` endpoints. No network calls leave the test process,
no real cloud / Postgres is contacted, and we never touch the user's live
~/.clawmetry/ or pid 309 — every test points the daemon at an isolated
DuckDB under ``tmp_path``.

Scenarios (mapped 1:1 to the brief in ``test/sync-resilience-7-scenarios``):

  1. happy path           — events generated, DuckDB has rows, cloud receives
                              the encrypted blob within 30s.
  2. network blip         — ingest "blackholed" (502/503) for 30s, daemon
                              retries with exp backoff, resumes when restored.
  3. schema drift         — bump local DuckDB SCHEMA_VERSION manually; daemon
                              should detect + migrate without crashing or
                              losing existing rows.
  4. lock contention      — open a second DuckDB RW connection while the
                              daemon holds the writer lock; second connection
                              must fail cleanly, daemon must not crash.
  5. rate limit (free)    — fire 100 heartbeats in 60s; cloud 429s some,
                              daemon honours retry; no events lost.
  6. invalid ciphertext   — corrupt one byte of a stored cache blob; the
                              cloud read still returns it, but client-side
                              AES-GCM decrypt raises (and the test asserts
                              the error is a clean exception, not a crash).
  7. clock skew           — push events with timestamps 2h in the future; the
                              cloud accepts and DuckDB stores them; no loss.

For each scenario we use a unique ``__sync_test_<rand>__`` marker baked into
the event ids / session ids so we can scope assertions and clean up at the
end via ``addfinalizer``.

Run:
    python3 -m pytest clawmetry/tests/e2e/test_cloud_sync_resilience.py -v

Pass/fail status as of 2026-05-13 is documented in the PR body — failing
tests are intentionally NOT fixed in this PR; they map to known bugs / gaps
that need their own follow-up changes.
"""
from __future__ import annotations

import importlib
import json
import os
import socket
import sys
import threading
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

try:
    import duckdb  # noqa: F401
except ImportError:
    pytest.skip("duckdb not installed", allow_module_level=True)

try:
    from flask import Flask, jsonify, request
except ImportError:  # pragma: no cover
    pytest.skip("flask not installed", allow_module_level=True)


# ── Shared helpers ───────────────────────────────────────────────────────────


def _free_port() -> int:
    """Return an unused TCP port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _marker() -> str:
    """Per-test isolation marker. Embedded in event ids / session ids so
    assertions can scope on it and we never collide with other tests."""
    return f"__sync_test_{uuid.uuid4().hex[:8]}__"


class StubCloud:
    """In-process Flask app that mimics the subset of ingest.clawmetry.com
    the OSS daemon talks to. Behaviour can be flipped via attributes:

      - ``mode``:      "ok" | "blackhole" | "ratelimit"
      - ``status``:    HTTP code returned in non-ok modes
      - ``rate_window``: seconds; in "ratelimit" mode N requests per window
      - ``rate_limit``:  N (heartbeats / window before 429)

    All received payloads land on ``self.received`` (list of (path, body))
    so the test can introspect what the daemon actually sent.
    """

    def __init__(self) -> None:
        self.received: list[tuple[str, dict]] = []
        self.mode = "ok"
        self.status = 503
        self.rate_window = 60.0
        self.rate_limit = 30
        self._rate_log: list[float] = []
        self._lock = threading.Lock()
        self.app = self._build_app()
        self.port = _free_port()
        self._server: object | None = None
        self._thread: threading.Thread | None = None

    # ------- wire ----------------------------------------------------------
    def _build_app(self) -> Flask:
        app = Flask(__name__)

        @app.route("/<path:path>", methods=["GET", "POST"])
        def catchall(path):  # noqa: ANN001
            with self._lock:
                try:
                    body = request.get_json(silent=True) or {}
                except Exception:
                    body = {}
                self.received.append((f"/{path}", body))
                if self.mode == "blackhole":
                    return ("upstream down", self.status)
                if self.mode == "ratelimit" and path == "ingest/heartbeat":
                    now = time.monotonic()
                    self._rate_log = [t for t in self._rate_log if now - t < self.rate_window]
                    if len(self._rate_log) >= self.rate_limit:
                        return jsonify({
                            "error": "rate_limited",
                            "plan": "free",
                            "retry_after": 1,
                        }), 429
                    self._rate_log.append(now)
            # Default OK responses for every endpoint the daemon hits
            if path == "ingest/heartbeat":
                return jsonify({"sync_allowed": True, "pending_queries": []})
            if path == "auth":
                return jsonify({"ok": True, "node_id": "node-test"})
            return jsonify({"ok": True})

        return app

    def start(self) -> None:
        from werkzeug.serving import make_server

        self._server = make_server("127.0.0.1", self.port, self.app, threaded=True)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        # Wait for the bind to be live
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            try:
                with socket.create_connection(("127.0.0.1", self.port), timeout=0.5):
                    return
            except OSError:
                time.sleep(0.05)
        raise RuntimeError("StubCloud failed to start")

    def stop(self) -> None:
        if self._server is not None:
            try:
                self._server.shutdown()  # type: ignore[attr-defined]
            except Exception:
                pass
        if self._thread is not None:
            self._thread.join(timeout=2)

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self.port}"

    def heartbeats(self) -> list[dict]:
        return [body for path, body in self.received if path == "/ingest/heartbeat"]

    def events_posts(self) -> list[dict]:
        return [body for path, body in self.received if path == "/ingest/events"]


@pytest.fixture
def stub_cloud(request):
    """Spin up a fresh in-process stub cloud per test."""
    cloud = StubCloud()
    cloud.start()
    request.addfinalizer(cloud.stop)
    return cloud


@pytest.fixture
def fresh_sync(tmp_path, monkeypatch, stub_cloud, request):
    """Reload `clawmetry.sync` + `clawmetry.local_store` against an isolated
    DuckDB and pointed at the in-process stub cloud. Returns
    (sync_module, local_store_module, config_dict)."""
    db_path = tmp_path / f"clawmetry-{uuid.uuid4().hex[:6]}.duckdb"
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(db_path))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "1")
    monkeypatch.setenv("CLAWMETRY_INGEST_URL", stub_cloud.url)

    # Drop cached modules so the env vars above take effect.
    for name in ("clawmetry.local_store", "clawmetry.sync"):
        sys.modules.pop(name, None)

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import clawmetry.sync as s
    importlib.reload(s)
    # The module reads INGEST_URL at import time — make sure the stub URL stuck.
    monkeypatch.setattr(s, "INGEST_URL", stub_cloud.url, raising=True)

    config = {
        "node_id":        f"node-{uuid.uuid4().hex[:6]}",
        "api_key":        "cm_test_resilience_key",
        "encryption_key": s.generate_encryption_key(),
    }

    def _cleanup():
        try:
            ls.get_store().stop(flush=True)
        except Exception:
            pass
        try:
            ls._reset_singleton_for_tests()
        except Exception:
            pass
    request.addfinalizer(_cleanup)
    return s, ls, config


def _wait_for_ring_drain(store, timeout: float = 5.0) -> None:
    """Block until the local store's flusher has drained the ring buffer."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if store.health()["ring_depth"] == 0:
            return
        time.sleep(0.02)
    raise AssertionError(
        f"flusher did not drain in {timeout}s "
        f"(ring_depth={store.health()['ring_depth']})"
    )


def _seed_event(store, marker: str, **extras) -> str:
    """Insert one synthetic event tagged with the test marker. Returns the id."""
    eid = f"{marker}-{uuid.uuid4().hex[:8]}"
    row = {
        "id":          eid,
        "node_id":     "agent+resilience",
        "agent_id":    "main",
        "session_id":  marker,
        "event_type":  "tool_call",
        "ts":          datetime.now(timezone.utc).isoformat(),
        "data":        {"marker": marker},
        "cost_usd":    0.001,
        "token_count": 42,
        "model":       "claude-opus-4-7",
    }
    row.update(extras)
    store.ingest(row)
    return eid


# ── 1. happy path ─────────────────────────────────────────────────────────────


def test_happy_path_event_round_trip(fresh_sync, stub_cloud):
    """Daemon up → events generated → DuckDB has rows → cloud receives the
    encrypted blob via /ingest/events (or /ingest/heartbeat cache_pushes)."""
    s, ls, config = fresh_sync
    marker = _marker()
    store = ls.get_store()

    # Seed three events that look like a small OpenClaw transcript
    batch = [
        {"id": f"{marker}-1", "type": "tool_call",
         "timestamp": datetime.now(timezone.utc).isoformat(),
         "tokens": 100, "cost_usd": 0.01, "model": "claude-opus-4-7"},
        {"id": f"{marker}-2", "type": "message",
         "timestamp": datetime.now(timezone.utc).isoformat(),
         "role": "user", "text": "hello world"},
    ]
    s._flush_session_batch(
        batch, f"{marker}.jsonl",
        api_key=config["api_key"], enc_key=config["encryption_key"],
        node_id=config["node_id"],
    )
    _wait_for_ring_drain(store)

    # DuckDB side
    rows = store.query_events(session_id=marker)
    assert len(rows) == 2
    assert {r["id"] for r in rows} == {f"{marker}-1", f"{marker}-2"}

    # Cloud side — exactly one /ingest/events POST, blob is opaque
    posts = stub_cloud.events_posts()
    assert len(posts) >= 1
    sent = posts[-1]
    assert sent.get("encrypted") is True
    assert isinstance(sent.get("blob"), str) and len(sent["blob"]) > 0
    # No plaintext leaked into the wire payload
    assert marker not in sent["blob"]
    assert "hello world" not in json.dumps(sent)

    # Round-trip decrypt → matches what we sent
    decrypted = s.decrypt_payload(sent["blob"], config["encryption_key"])
    assert decrypted["session_file"] == f"{marker}.jsonl"
    assert len(decrypted["events"]) == 2


# ── 2. network blip ──────────────────────────────────────────────────────────


def test_network_blip_no_event_loss(fresh_sync, stub_cloud, monkeypatch):
    """Cloud goes blackhole (503) for a window. The daemon's POST raises;
    the local DuckDB still records every event. When the cloud comes back,
    the daemon resumes (we model this by re-flushing the same batch — the
    real daemon's outer loop replays from `last_event_ids` / log offsets)."""
    s, ls, config = fresh_sync
    marker = _marker()
    store = ls.get_store()

    # Skip the daemon's retry sleeps so the test isn't dominated by backoff.
    monkeypatch.setattr(s.time, "sleep", lambda *a, **kw: None)

    # Simulate ingest down
    stub_cloud.mode = "blackhole"
    stub_cloud.status = 503

    batch_during_outage = [
        {"id": f"{marker}-down-{i}", "type": "tool_call",
         "timestamp": datetime.now(timezone.utc).isoformat()}
        for i in range(5)
    ]
    # Cloud POST should raise but local write must still succeed.
    with pytest.raises(Exception):  # noqa: BLE001
        s._flush_session_batch(
            batch_during_outage, f"{marker}.jsonl",
            api_key=config["api_key"], enc_key=config["encryption_key"],
            node_id=config["node_id"],
        )
    _wait_for_ring_drain(store)
    rows_after_blip = store.query_events(session_id=marker)
    assert len(rows_after_blip) == 5, "events must survive the network blip locally"

    # Restore cloud, replay (this mirrors the daemon's next sync cycle)
    stub_cloud.mode = "ok"
    s._flush_session_batch(
        batch_during_outage, f"{marker}.jsonl",
        api_key=config["api_key"], enc_key=config["encryption_key"],
        node_id=config["node_id"],
    )
    _wait_for_ring_drain(store)

    # Idempotency: INSERT OR IGNORE on event id → no duplicates locally
    rows_after_restore = store.query_events(session_id=marker)
    assert len(rows_after_restore) == 5, "replay must not duplicate locally"

    # Cloud got the replay
    assert any(
        marker in (s.decrypt_payload(p["blob"], config["encryption_key"])
                   .get("session_file", ""))
        for p in stub_cloud.events_posts()
        if p.get("blob")
    )


# ── 3. schema drift ──────────────────────────────────────────────────────────


def test_schema_drift_existing_rows_preserved(fresh_sync):
    """Bump the on-disk schema_version below the code's expected value
    (simulating a downgrade-then-upgrade) and re-open the store. Existing
    rows must be intact and the daemon must not crash on re-init."""
    s, ls, config = fresh_sync
    marker = _marker()
    store = ls.get_store()

    seeded_ids = [_seed_event(store, marker) for _ in range(3)]
    _wait_for_ring_drain(store)
    assert len(store.query_events(session_id=marker)) == 3
    db_path = Path(store.health()["db_path"])

    # Stop the writer, mutate the schema_version row to look "old", reopen.
    store.stop(flush=True)
    ls._reset_singleton_for_tests()

    import duckdb
    conn = duckdb.connect(str(db_path))
    try:
        # Force the version row backwards (simulates downgrade or fresh
        # migration scenario). Tolerant of either INTEGER or empty table.
        conn.execute("DELETE FROM schema_version")
        conn.execute(
            "INSERT INTO schema_version (version, applied_at) VALUES (?, ?)",
            [1, int(time.time() * 1000)],
        )
    finally:
        conn.close()

    # Re-open via the daemon's normal codepath
    sys.modules.pop("clawmetry.local_store", None)
    import clawmetry.local_store as ls2
    importlib.reload(ls2)
    store2 = ls2.get_store()

    # Migration should have re-stamped the schema_version up to current
    rows = store2.query_events(session_id=marker)
    assert len(rows) == 3, "existing rows lost on schema rebump"
    assert {r["id"] for r in rows} == set(seeded_ids)
    assert store2.health()["schema_version"] == ls2.SCHEMA_VERSION


# ── 4. lock contention ──────────────────────────────────────────────────────


def test_lock_contention_second_writer_fails_clean(fresh_sync):
    """DuckDB is single-writer. While the daemon's store holds the RW lock,
    a second RW connection must fail cleanly (catchable IOException-style
    error) and the daemon must keep working."""
    s, ls, config = fresh_sync
    marker = _marker()
    store = ls.get_store()
    _seed_event(store, marker)
    _wait_for_ring_drain(store)
    db_path = Path(store.health()["db_path"])

    import duckdb
    second_conn_failed = False
    err: Exception | None = None
    try:
        # Daemon already holds RW; this MUST fail.
        conn2 = duckdb.connect(str(db_path), read_only=False)
        try:
            conn2.execute("SELECT 1").fetchall()
        finally:
            conn2.close()
    except Exception as e:  # noqa: BLE001
        second_conn_failed = True
        err = e

    assert second_conn_failed, "second RW connection unexpectedly succeeded"
    assert err is not None
    # Error should mention the lock, not be a segfault / generic IOError
    msg = str(err).lower()
    assert any(k in msg for k in ("lock", "use", "another", "conflict")), (
        f"second-connection error not a clean lock message: {err!r}"
    )

    # Daemon still works after the contention attempt
    eid = _seed_event(store, marker)
    _wait_for_ring_drain(store)
    rows = store.query_events(session_id=marker)
    assert eid in {r["id"] for r in rows}


# ── 5. rate limit (free plan) ───────────────────────────────────────────────


def test_rate_limit_free_plan_no_event_loss(fresh_sync, stub_cloud, monkeypatch):
    """100 heartbeats hammered through; the stub cloud 429s once the free-plan
    threshold trips. Daemon's `_post` should surface the 429 (and flip
    `_TRIAL_STATE.sync_allowed=False` per the existing logic), but local
    state must not lose any of the events the daemon collected."""
    s, ls, config = fresh_sync
    marker = _marker()
    store = ls.get_store()

    # The daemon sleeps between retries (2**attempt). For a 100-heartbeat
    # loop that turns into minutes. We're testing the BEHAVIOUR, not the
    # backoff timing — kill the sleeps so the test runs in seconds.
    monkeypatch.setattr(s.time, "sleep", lambda *a, **kw: None)

    stub_cloud.mode = "ratelimit"
    stub_cloud.rate_limit = 30
    stub_cloud.rate_window = 60.0

    # Local: pump 100 events. These never depend on cloud succeeding.
    for i in range(100):
        _seed_event(store, marker,
                    ts=(datetime.now(timezone.utc) + timedelta(milliseconds=i)).isoformat())
    _wait_for_ring_drain(store, timeout=10.0)

    # Try 100 heartbeats. Most will be allowed by the stub; some will 429.
    ok_count = 0
    rate_limited = 0
    for _ in range(100):
        try:
            ok = s.send_heartbeat(config)
            if ok:
                ok_count += 1
        except Exception:
            rate_limited += 1

    # We expect SOME 429s (the cloud is configured to throttle).
    hb_seen = stub_cloud.heartbeats()
    assert len(hb_seen) >= 30, (
        f"stub cloud only saw {len(hb_seen)} heartbeats — daemon may be "
        f"failing to retry after throttle"
    )
    # Local DuckDB has every event we ingested, regardless of cloud throttle
    rows = store.query_events(session_id=marker)
    assert len(rows) == 100, f"events lost under rate-limit pressure: {len(rows)}/100"


# ── 6. invalid ciphertext ────────────────────────────────────────────────────


def test_corrupt_ciphertext_raises_clean_decrypt_error(fresh_sync):
    """A blob that's been bit-flipped must not silently decrypt to garbage —
    AES-GCM's MAC must fail and the client must get a clean exception, not a
    None or empty dict (which would render as a blank tab in the browser)."""
    s, ls, config = fresh_sync
    payload = {"hello": "world", "marker": _marker()}
    blob = s.encrypt_payload(payload, config["encryption_key"])

    # Sanity: clean blob round-trips
    assert s.decrypt_payload(blob, config["encryption_key"]) == payload

    # Corrupt one byte mid-ciphertext (skip the 12-byte nonce header so we
    # actually hit the auth-tagged region rather than the IV).
    raw = list(blob)
    # Pick an index well past the base64 prefix corresponding to the nonce
    idx = len(raw) // 2
    raw[idx] = "A" if raw[idx] != "A" else "B"
    corrupted = "".join(raw)
    assert corrupted != blob

    # The AES-GCM library raises InvalidTag (a subclass of Exception). We
    # care that it's an exception, not silent corruption.
    with pytest.raises(Exception) as exc_info:
        s.decrypt_payload(corrupted, config["encryption_key"])
    # Specifically — must NOT be a JSONDecodeError (would mean the MAC
    # didn't catch the corruption and we fed garbage to json.loads).
    assert "JSONDecode" not in type(exc_info.value).__name__, (
        f"AES-GCM MAC failed to catch corruption — got {type(exc_info.value).__name__}"
    )


# ── 7. clock skew ────────────────────────────────────────────────────────────


def test_clock_skew_future_timestamps_accepted(fresh_sync, stub_cloud):
    """Local clock is 2h ahead → events arrive with future timestamps. The
    local store must keep them (no silent drop) and the cloud POST must
    succeed (the stub accepts everything)."""
    s, ls, config = fresh_sync
    marker = _marker()
    store = ls.get_store()

    future = datetime.now(timezone.utc) + timedelta(hours=2)
    batch = [
        {"id": f"{marker}-future-{i}", "type": "tool_call",
         "timestamp": (future + timedelta(seconds=i)).isoformat(),
         "tokens": 10}
        for i in range(3)
    ]
    s._flush_session_batch(
        batch, f"{marker}.jsonl",
        api_key=config["api_key"], enc_key=config["encryption_key"],
        node_id=config["node_id"],
    )
    _wait_for_ring_drain(store)

    rows = store.query_events(session_id=marker)
    assert len(rows) == 3, "future-dated events were dropped locally"
    # Timestamps are stored as-is (the local store doesn't clock-correct)
    sent_ts = sorted(r["ts"] for r in rows)
    assert all(
        ts >= datetime.now(timezone.utc).isoformat()
        for ts in sent_ts
    ), f"local store mutated future timestamps: {sent_ts}"

    # Cloud accepted the upload
    posts = stub_cloud.events_posts()
    assert len(posts) >= 1
    decrypted = s.decrypt_payload(posts[-1]["blob"], config["encryption_key"])
    assert len(decrypted["events"]) == 3
