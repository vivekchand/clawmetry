"""Tests for Phase 5 of epic #1032 — channel adapter config in DuckDB.

Surface under test:
  1. Schema: ``channel_config`` table is created on store init.
  2. ingest_channel_config helper: upsert + merge semantics; status-only
     update doesn't clobber the encrypted blob.
  3. query_channel_configs returns the blob; query_channel_config_status
     omits it (cache-safe).
  4. /api/channels/<provider>/status route serves from DuckDB when the
     ``CLAWMETRY_LOCAL_STORE_READ`` flag is on and tags ``_source:
     "local_store"``.
  5. pending_queries dispatcher handles ``channel_config_upsert`` and
     ``channel_test`` action types end-to-end.
  6. _build_channel_config_status_cache_pushes produces a properly-shaped
     cache_push entry whose blob decrypts back to the status summary —
     and never contains plaintext tokens.
"""

from __future__ import annotations

import base64
import importlib
import os
import sys

import pytest
from flask import Flask


_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)


# ── Fixtures ───────────────────────────────────────────────────────────────


@pytest.fixture
def fresh_store(tmp_path, monkeypatch):
    """Fresh DuckDB store per test. Yields the (reloaded) local_store module."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "1")

    sys.modules.pop("clawmetry.local_store", None)
    import clawmetry.local_store as ls
    importlib.reload(ls)

    yield ls

    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


@pytest.fixture
def app_with_flag(tmp_path, monkeypatch):
    """Flask app with the channels blueprint and the local-store read flag on."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")

    sys.modules.pop("clawmetry.local_store", None)
    sys.modules.pop("routes.channels", None)
    import clawmetry.local_store as ls
    importlib.reload(ls)
    import routes.channels as ch
    importlib.reload(ch)

    a = Flask(__name__)
    a.register_blueprint(ch.bp_channels)
    yield a, ls, ch
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


@pytest.fixture
def sync_mod(tmp_path, monkeypatch):
    """Reload clawmetry.sync against a fresh DuckDB."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "1")

    sys.modules.pop("clawmetry.local_store", None)
    sys.modules.pop("clawmetry.sync", None)
    import clawmetry.local_store as ls
    importlib.reload(ls)
    import clawmetry.sync as s
    importlib.reload(s)

    yield s, ls

    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


# ── 1. Schema + ingest/query happy path ─────────────────────────────────────


def test_channel_config_table_exists(fresh_store):
    """Schema bootstrap creates the channel_config table."""
    ls = fresh_store
    store = ls.get_store()
    cur = store._conn.execute(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema='main' AND table_name='channel_config'"
    )
    assert cur.fetchone() is not None


def test_ingest_then_query_roundtrip(fresh_store):
    """Upsert a Telegram config + status; query both helpers return it."""
    ls = fresh_store
    store = ls.get_store()
    encrypted = b"\x00\x01\x02ENCRYPTED-TELEGRAM-TOKEN-BLOB"
    store.ingest_channel_config(
        provider="telegram",
        encrypted_blob=encrypted,
        enabled=True,
        status_meta={
            "last_test_at": "2026-05-12T10:00:00Z",
            "last_test_ok": True,
            "last_test_error": "",
        },
    )

    rows = store.query_channel_configs(provider="telegram")
    assert len(rows) == 1
    r = rows[0]
    assert r["provider"] == "telegram"
    assert r["enabled"] is True
    # Blob round-trips byte-for-byte.
    assert bytes(r["config_json_encrypted"]) == encrypted
    assert r["last_test_ok"] is True

    # Status query omits the blob — this is the cache_push-safe surface.
    status = store.query_channel_config_status(provider="telegram")
    assert len(status) == 1
    assert "config_json_encrypted" not in status[0]
    assert status[0]["last_test_ok"] is True


def test_status_only_update_preserves_blob(fresh_store):
    """A `channel_test` action shouldn't wipe the encrypted blob."""
    ls = fresh_store
    store = ls.get_store()
    blob = b"original-encrypted-blob"
    store.ingest_channel_config(
        provider="slack",
        encrypted_blob=blob,
        enabled=True,
        status_meta=None,
    )
    # Status-only follow-up (mimics channel_test path).
    store.ingest_channel_config(
        provider="slack",
        encrypted_blob=None,
        enabled=None,
        status_meta={
            "last_test_at": "2026-05-12T11:00:00Z",
            "last_test_ok": False,
            "last_test_error": "401 from auth.test",
        },
    )
    rows = store.query_channel_configs(provider="slack")
    assert len(rows) == 1
    assert bytes(rows[0]["config_json_encrypted"]) == blob, (
        "status-only update must NOT clobber the encrypted blob"
    )
    assert rows[0]["enabled"] is True  # also preserved
    assert rows[0]["last_test_ok"] is False
    assert rows[0]["last_test_error"] == "401 from auth.test"


# ── 2. Route fast-path + _source tagging ────────────────────────────────────


def test_status_route_serves_from_local_store(app_with_flag):
    """GET /api/channels/<provider>/status returns the DuckDB row tagged
    _source='local_store' when the flag is on."""
    app, ls, _ch = app_with_flag
    store = ls.get_store()
    store.ingest_channel_config(
        provider="telegram",
        encrypted_blob=b"X",
        enabled=True,
        status_meta={"last_test_at": "2026-05-12T10:00:00Z", "last_test_ok": True},
    )
    client = app.test_client()
    r = client.get("/api/channels/telegram/status")
    assert r.status_code == 200
    body = r.get_json()
    assert body["_source"] == "local_store"
    assert body["provider"] == "telegram"
    assert body["enabled"] is True
    assert body["configured"] is True
    assert body["last_test_ok"] is True
    # The encrypted blob must NEVER appear in the HTTP response.
    assert "config_json_encrypted" not in body


def test_status_route_unconfigured_provider(app_with_flag):
    """Unknown provider still returns a local_store-tagged "not configured"
    summary so the cloud UI renders a stable shape."""
    app, _ls, _ch = app_with_flag
    client = app.test_client()
    r = client.get("/api/channels/discord/status")
    assert r.status_code == 200
    body = r.get_json()
    assert body["_source"] == "local_store"
    assert body["configured"] is False
    assert body["enabled"] is False


def test_status_route_fallback_when_flag_off(tmp_path, monkeypatch):
    """With CLAWMETRY_LOCAL_STORE_READ unset, the route degrades to a
    "fallback" tagged response (no DuckDB read)."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.delenv("CLAWMETRY_LOCAL_STORE_READ", raising=False)

    sys.modules.pop("clawmetry.local_store", None)
    sys.modules.pop("routes.channels", None)
    import clawmetry.local_store as ls
    importlib.reload(ls)
    import routes.channels as ch
    importlib.reload(ch)

    a = Flask(__name__)
    a.register_blueprint(ch.bp_channels)
    client = a.test_client()
    r = client.get("/api/channels/telegram/status")
    assert r.status_code == 200
    assert r.get_json()["_source"] == "fallback"


# ── 3. pending_queries dispatcher: channel_config_upsert ────────────────────


def test_pending_query_channel_config_upsert(sync_mod):
    """Cloud queues a channel_config_upsert pending_query; the daemon
    persists the encrypted blob locally."""
    s, ls = sync_mod
    enc = s.generate_encryption_key()
    config = {
        "node_id": "node-test",
        "api_key": "cm_test_token_xyz",
        "encryption_key": enc,
    }
    # Cloud has already encrypted the user-side config blob; we just send
    # the ciphertext (base64url) through pending_queries.
    cipher_bytes = b"\xff\xee\xddCIPHERTEXT-BOT-TOKEN"
    cipher_b64 = base64.urlsafe_b64encode(cipher_bytes).decode().rstrip("=")
    action = {
        "type": "channel_config_upsert",
        "provider": "telegram",
        "encrypted_blob": cipher_b64,
        "enabled": True,
    }
    s._dispatch_pending_queries(config, [action])

    rows = ls.get_store(read_only=True).query_channel_configs(provider="telegram")
    assert len(rows) == 1
    assert bytes(rows[0]["config_json_encrypted"]) == cipher_bytes
    assert rows[0]["enabled"] is True


def test_pending_query_channel_test_updates_status(sync_mod):
    """channel_test action stamps last_test_* fields on the existing row."""
    s, ls = sync_mod
    config = {
        "node_id": "node-test",
        "api_key": "cm_test_token_xyz",
        "encryption_key": s.generate_encryption_key(),
    }
    # Seed a config first so the test stub has "config present" to report ok.
    ls.get_store().ingest_channel_config(
        provider="slack",
        encrypted_blob=b"some-encrypted-slack-config",
        enabled=True,
        status_meta=None,
    )
    s._dispatch_pending_queries(config, [{
        "type": "channel_test",
        "provider": "slack",
    }])
    rows = ls.get_store(read_only=True).query_channel_config_status(provider="slack")
    assert len(rows) == 1
    assert rows[0]["last_test_ok"] is True
    assert rows[0]["last_test_at"] is not None


def test_pending_query_channel_test_no_config(sync_mod):
    """channel_test on a never-configured provider records ok=False with
    a 'not configured' error."""
    s, ls = sync_mod
    config = {
        "node_id": "node-test",
        "api_key": "cm_test_token_xyz",
        "encryption_key": s.generate_encryption_key(),
    }
    s._dispatch_pending_queries(config, [{
        "type": "channel_test",
        "provider": "discord",
    }])
    rows = ls.get_store(read_only=True).query_channel_config_status(provider="discord")
    assert len(rows) == 1
    assert rows[0]["last_test_ok"] is False
    assert "not configured" in (rows[0]["last_test_error"] or "")


# ── 4. cache_push: shape + ciphertext only ──────────────────────────────────


def test_build_channel_config_status_cache_pushes(sync_mod):
    """Push entry: key='channels:{owner}:status', ttl=3600, blob decrypts
    back to the status summary; plaintext tokens NEVER appear in the blob."""
    s, ls = sync_mod
    config = {
        "node_id": "node-test",
        "api_key": "cm_test_token_xyz",
        "encryption_key": s.generate_encryption_key(),
    }
    # Seed two providers — one with a clearly-sensitive plaintext-looking
    # blob, one without.
    ls.get_store().ingest_channel_config(
        provider="telegram",
        encrypted_blob=b"PLAINTEXT-LOOKING-BOT-TOKEN-bot1234567:ABCDEF",
        enabled=True,
        status_meta={"last_test_at": "2026-05-12T10:00:00Z", "last_test_ok": True},
    )
    ls.get_store().ingest_channel_config(
        provider="slack",
        encrypted_blob=b"\x00\x01\x02",
        enabled=False,
        status_meta=None,
    )

    pushes = s._build_channel_config_status_cache_pushes(config)
    assert isinstance(pushes, list)
    assert len(pushes) == 1
    entry = pushes[0]

    expected_owner = s._owner_hash_for_token(config["api_key"])
    assert entry["key"] == f"channels:{expected_owner}:status"
    assert entry["ttl_s"] == s.CHANNEL_STATUS_CACHE_TTL_SEC == 3600
    blob = entry["blob"]
    assert isinstance(blob, str) and len(blob) > 0

    # Round-trip decrypt → status summary, no tokens.
    decoded = s.decrypt_payload(blob, config["encryption_key"])
    assert decoded["_shape"] == "channel_config_status"
    assert decoded["_source"] == "local_store"
    assert decoded["count"] == 2
    providers = {c["provider"] for c in decoded["channels"]}
    assert providers == {"telegram", "slack"}
    # The plaintext-looking marker must NOT travel — even encrypted, this
    # cache key carries STATUS only.
    for c in decoded["channels"]:
        assert "PLAINTEXT" not in str(c)
        assert "config_json_encrypted" not in c


def test_build_channel_config_status_empty_store_returns_empty(sync_mod):
    """No rows → no push (clean wire format, cloud doesn't get an empty
    cache entry)."""
    s, _ls = sync_mod
    config = {
        "node_id": "node-test",
        "api_key": "cm_test_token_xyz",
        "encryption_key": s.generate_encryption_key(),
    }
    assert s._build_channel_config_status_cache_pushes(config) == []


def test_build_channel_config_status_no_encryption_key(sync_mod):
    """Missing encryption key → no push (never send anything without E2E
    even though status is non-secret — keeps the contract uniform)."""
    s, ls = sync_mod
    ls.get_store().ingest_channel_config(
        provider="telegram",
        encrypted_blob=b"X",
        enabled=True,
        status_meta=None,
    )
    config = {
        "node_id": "node-test",
        "api_key": "cm_test_token_xyz",
        "encryption_key": None,
    }
    assert s._build_channel_config_status_cache_pushes(config) == []
