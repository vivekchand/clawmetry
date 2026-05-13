"""Tests for /api/sessions channel-context decoration from local DuckDB.

The local DuckDB has a typed ``openclaw_channels`` table that maps
``session_id → {channel, chat_type, subject, origin_label}``. When the
``CLAWMETRY_LOCAL_STORE_READ=1`` env gate is on, ``/api/sessions`` reads
those rows and decorates the session list with channel attribution
(replacing the legacy free-form ``metadata`` blob inference).

What's covered here:
  - happy path: seed channel rows + sessions, hit /api/sessions, assert
    each returned session carries the typed channel/chat_type/subject.
  - negative path: env unset → no decoration, even with channel rows
    present in the store.
  - by-type variant: a Telegram-channelled session classifies as "user"
    in /api/sessions/by-type once the typed channel context is merged.
"""

from __future__ import annotations

import importlib

import pytest
from flask import Flask


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import routes.sessions as sessions_mod
    importlib.reload(sessions_mod)

    a = Flask(__name__)
    a.register_blueprint(sessions_mod.bp_sessions)
    yield a, ls
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def _seed_session(store, sid: str, **kwargs) -> None:
    """Default-everything-empty session row so the decoration test reflects
    what /api/sessions would see in the wild before channel attribution."""
    base = {
        "session_id": sid,
        "agent_type": "openclaw",
        "title": kwargs.get("title", ""),
        "started_at": "2026-05-12T10:00:00Z",
        "last_active_at": "2026-05-12T10:30:00Z",
        "status": "active",
        "total_tokens": 0,
        "cost_usd": 0.0,
        "message_count": 0,
        # Crucially: NO channel / chat_type in metadata. We want to prove the
        # decoration helper is what filled those fields, not the legacy blob.
        "metadata": {},
    }
    base.update(kwargs)
    store.ingest_session(base)


def test_api_sessions_decorates_with_channel_context(app):
    """Seed sessions + channel rows, hit /api/sessions, assert each returned
    session carries the typed channel/chat_type/subject."""
    a, ls = app
    store = ls.get_store()
    _seed_session(store, "sess-tg", title="Telegram convo")
    _seed_session(store, "sess-slack", title="Slack thread")
    _seed_session(store, "sess-plain", title="No channel")  # control
    store.ingest_channel({
        "session_id": "sess-tg",
        "channel": "telegram",
        "chat_type": "private",
        "subject": "@alice",
        "origin_label": "Telegram DM with alice",
    })
    store.ingest_channel({
        "session_id": "sess-slack",
        "channel": "slack",
        "chat_type": "channel",
        "subject": "#deploys",
        "origin_label": "Slack #deploys",
    })

    r = a.test_client().get("/api/sessions")
    assert r.status_code == 200
    body = r.get_json()
    assert body.get("_source") == "local_store"
    by_id = {s["session_id"]: s for s in body["sessions"]}

    assert by_id["sess-tg"]["channel"] == "telegram"
    assert by_id["sess-tg"]["chat_type"] == "private"
    assert by_id["sess-tg"]["subject"] == "Telegram convo"  # title wins over channel.subject
    assert by_id["sess-tg"]["origin_label"] == "Telegram DM with alice"

    assert by_id["sess-slack"]["channel"] == "slack"
    assert by_id["sess-slack"]["chat_type"] == "channel"
    assert by_id["sess-slack"]["origin_label"] == "Slack #deploys"

    # No channel row → fields stay blank; no error.
    assert by_id["sess-plain"]["channel"] == ""
    assert by_id["sess-plain"]["chat_type"] == ""


def test_api_sessions_no_decoration_without_env_flag(tmp_path, monkeypatch):
    """CLAWMETRY_LOCAL_STORE_READ unset → no fast path, no decoration.
    Channel rows in the store stay invisible to /api/sessions output.

    Verified by checking the response is NOT tagged ``_source: local_store``
    (the only way to reach the decoration). Without the env flag the fast
    path is skipped entirely, so neither the local sessions nor the
    decorated channel context surface in the response.
    """
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "0")  # force legacy path

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import routes.sessions as sessions_mod
    importlib.reload(sessions_mod)

    store = ls.get_store()
    _seed_session(store, "sess-noflag", title="Should not be decorated")
    store.ingest_channel({
        "session_id": "sess-noflag",
        "channel": "telegram",
        "chat_type": "private",
        "subject": "@bob",
    })

    a = Flask(__name__)
    a.register_blueprint(sessions_mod.bp_sessions)
    body = a.test_client().get("/api/sessions").get_json() or {}
    # Without the flag the fast path is bypassed; the response goes through
    # gateway/JSONL (which may 5xx in the unit-test context with no gateway).
    # Either way it must NOT be tagged local_store and must NOT carry the
    # decorated channel value.
    assert body.get("_source") != "local_store"
    for s in body.get("sessions", []):
        if s.get("session_id") == "sess-noflag":
            assert s.get("channel", "") != "telegram"
    try:
        store.stop(flush=True)
    except Exception:
        pass


def test_decoration_reclassifies_session_type_in_by_type(app):
    """A session with a Telegram channel row but no ``channel`` field on the
    session metadata should classify as ``user`` (not ``main``) in the
    /api/sessions/by-type response, because the decoration runs BEFORE the
    type-inference pass."""
    a, ls = app
    store = ls.get_store()
    _seed_session(store, "sess-user", title="From Telegram")
    store.ingest_channel({
        "session_id": "sess-user",
        "channel": "telegram",
        "chat_type": "private",
        "subject": "@carol",
    })

    body = a.test_client().get("/api/sessions/by-type").get_json()
    assert body.get("_source") == "local_store"
    by_id = {s["session_id"]: s for s in body["sessions"]}
    assert by_id["sess-user"]["channel"] == "telegram"
    assert by_id["sess-user"]["session_type"] == "user"
    assert body["counts"]["user"] >= 1


def test_decoration_is_noop_when_channels_table_empty(app):
    """No rows in openclaw_channels → sessions come back unmodified, no
    error. Important for fresh installs where the gateway hasn't pushed any
    channel attribution yet."""
    a, ls = app
    store = ls.get_store()
    _seed_session(store, "sess-only", title="Solo")
    # No ingest_channel() calls.

    body = a.test_client().get("/api/sessions").get_json()
    assert body.get("_source") == "local_store"
    by_id = {s["session_id"]: s for s in body["sessions"]}
    assert by_id["sess-only"]["channel"] == ""
    assert by_id["sess-only"]["chat_type"] == ""
