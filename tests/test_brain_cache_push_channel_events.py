"""Tests for channel-event enrichment in the heartbeat-piggyback brain
cache push (extends epic #1032 Phase 2).

Bug pinned by these tests
-------------------------

Once aca53ec8's PR #1191 (commit 2dff811) added
``sync_channel_messages()``, every Telegram/Signal/WhatsApp/Discord turn
landed in DuckDB with ``event_type='channel.in'``/``'channel.out'``. The
heartbeat-piggyback brain cache push (``_build_brain_cache_pushes``)
already pulled them via ``query_events(limit=50)`` — but the cloud Brain
renderer had no way to display "Telegram: Vivek Chand: hello, how are
you?" because the OSS daemon shipped the rows without provider /
chat_id / sender attached at the top level. The cloud's "Conversation
info (untrusted metadata)" panel needs those fields per row.

What we cover
-------------
1. A ``channel.in`` row from ``~/.openclaw/telegram/<chat_id>.jsonl``
   (the shape PR #1191 writes to ``events.data``) round-trips through
   ``_build_brain_cache_pushes`` → encrypted blob → ``decrypt_payload``
   and the decrypted event carries provider='telegram', chat_id matching
   the file stem, sender / sender_id from the ``from`` block,
   direction='in'.
2. ``channel.out`` (assistant) rows mark direction='out' and still
   surface chat_id (so the cloud can group inbound + outbound under one
   conversation).
3. Sibling providers (signal, slack, whatsapp) are enriched the same
   way — the enrichment is provider-agnostic.
4. Non-channel rows (the existing session ``message`` / ``user`` /
   ``assistant`` types) are NOT enriched — the keys must NOT appear so
   we don't pollute the OpenClaw transcript shape ``transformEvents``
   already understands.
5. The encrypted blob still does not leak plaintext (chat ids, sender
   names) — same E2E invariant as the Phase 2 happy-path test.

DuckDB-first hard rule (``feedback_duckdb_first_rule``): the channel
events MUST come from the local DuckDB store — no JSONL re-tail at
heartbeat time. Test seeds DuckDB directly via ``store.ingest`` using
the same column shape ``sync_channel_messages`` writes.
"""
from __future__ import annotations

import importlib
import os
import sys

import pytest


_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)


@pytest.fixture
def sync_with_channel_events(tmp_path, monkeypatch):
    """Reload sync + local_store against a fresh DuckDB seeded with a
    realistic mix of channel.in / channel.out / regular session rows."""
    monkeypatch.setenv(
        "CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb")
    )
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "1")

    sys.modules.pop("clawmetry.local_store", None)
    sys.modules.pop("clawmetry.sync", None)

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import clawmetry.sync as s
    importlib.reload(s)

    store = ls.get_store()

    # ── Telegram inbound (mirrors what sync_channel_messages writes when
    # ~/.openclaw/telegram/1532693273.jsonl gets a new line). The id is
    # the canonical "{provider}:{channel_id}:{raw_id}" shape PR #1191
    # produces.
    store.ingest({
        "id":           "telegram:1532693273:8463",
        "node_id":      "node-test",
        "agent_id":     "main",
        "session_id":   None,
        "event_type":   "channel.in",
        "ts":           "2026-05-13T22:00:00Z",
        "data":         {
            "id": 8463,
            "ts": "2026-05-13T22:00:00Z",
            "direction": "in",
            "from": {
                "id": 1532693273,
                "username": "vivekchand",
                "first_name": "Vivek",
            },
            "text": "hey diya — how are you doing?",
        },
        "cost_usd":     None,
        "token_count":  None,
        "model":        None,
    })

    # ── Telegram outbound (assistant reply).
    store.ingest({
        "id":           "telegram:1532693273:8464",
        "node_id":      "node-test",
        "agent_id":     "main",
        "session_id":   None,
        "event_type":   "channel.out",
        "ts":           "2026-05-13T22:00:30Z",
        "data":         {
            "message_id": 8464,
            "ts": "2026-05-13T22:00:30Z",
            "role": "assistant",
            "text": "doing well — what's up?",
        },
        "cost_usd":     None,
        "token_count":  None,
        "model":        None,
    })

    # ── Sibling provider: signal.
    store.ingest({
        "id":           "signal:+14155551212:abc-1",
        "node_id":      "node-test",
        "agent_id":     "main",
        "session_id":   None,
        "event_type":   "channel.in",
        "ts":           "2026-05-13T22:01:00Z",
        "data":         {
            "id": "abc-1",
            "ts": "2026-05-13T22:01:00Z",
            "direction": "in",
            "sender": {"id": "+14155551212", "name": "Alice"},
            "text": "ping from signal",
        },
        "cost_usd":     None,
        "token_count":  None,
        "model":        None,
    })

    # ── A regular session message (must NOT get channel enrichment).
    store.ingest({
        "id":           "session-evt-1",
        "node_id":      "node-test",
        "agent_id":     "main",
        "session_id":   "sess-cli",
        "event_type":   "message",
        "ts":           "2026-05-13T22:02:00Z",
        "data":         {"text": "ordinary CLI session turn"},
        "cost_usd":     0.001,
        "token_count":  10,
        "model":        "claude-opus-4-7",
    })

    # Wait for the background flusher to drain the ring.
    import time
    for _ in range(80):
        if store.health()["ring_depth"] == 0:
            break
        time.sleep(0.05)

    config = {
        "node_id":         "node-test",
        "api_key":         "cm_test_token_xyz",
        "encryption_key":  s.generate_encryption_key(),
    }
    yield s, config

    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def _decrypt_pushes(s, config, pushes):
    assert len(pushes) == 1, pushes
    decoded = s.decrypt_payload(pushes[0]["blob"], config["encryption_key"])
    assert isinstance(decoded, dict)
    assert decoded["_shape"] == "brain_history"
    return decoded


def _by_id(events: list, marker: str) -> dict | None:
    """Find the first event whose ``text`` contains the marker — used
    because ``_rows_to_brain_events`` returns rows in newest-first order
    and we don't want to be index-fragile."""
    for ev in events:
        if marker in (ev.get("text") or ""):
            return ev
    return None


# ── 1. Telegram inbound enriched ────────────────────────────────────────────


def test_telegram_inbound_carries_provider_chatid_sender(sync_with_channel_events):
    s, config = sync_with_channel_events
    pushes = s._build_brain_cache_pushes(config)
    decoded = _decrypt_pushes(s, config, pushes)

    ev = _by_id(decoded["events"], "how are you doing?")
    assert ev is not None, "telegram inbound event missing from cache push"
    assert ev["provider"] == "telegram"
    assert ev["chat_id"] == "1532693273"
    assert ev["sender_id"] == "1532693273"
    assert ev["sender"] == "vivekchand"
    assert ev["direction"] == "in"
    # type stamp lets the cloud renderer's fallback branch label the row
    assert ev.get("type") == "channel.in"


# ── 2. Telegram outbound marked direction=out ───────────────────────────────


def test_telegram_outbound_marked_direction_out(sync_with_channel_events):
    s, config = sync_with_channel_events
    pushes = s._build_brain_cache_pushes(config)
    decoded = _decrypt_pushes(s, config, pushes)

    ev = _by_id(decoded["events"], "doing well")
    assert ev is not None
    assert ev["provider"] == "telegram"
    assert ev["chat_id"] == "1532693273"
    assert ev["direction"] == "out"
    # No sender name in the assistant payload — we fall back to chat_id
    # so the renderer always has SOMETHING to display.
    assert ev["sender_id"] == "1532693273"


# ── 3. Sibling providers enriched the same way ──────────────────────────────


def test_signal_event_enriched_with_provider_signal(sync_with_channel_events):
    s, config = sync_with_channel_events
    pushes = s._build_brain_cache_pushes(config)
    decoded = _decrypt_pushes(s, config, pushes)

    ev = _by_id(decoded["events"], "ping from signal")
    assert ev is not None
    assert ev["provider"] == "signal"
    assert ev["chat_id"] == "+14155551212"
    assert ev["sender_id"] == "+14155551212"
    assert ev["sender"] == "Alice"
    assert ev["direction"] == "in"


# ── 4. Non-channel rows are NOT enriched ────────────────────────────────────


def test_regular_session_message_has_no_channel_keys(sync_with_channel_events):
    s, config = sync_with_channel_events
    pushes = s._build_brain_cache_pushes(config)
    decoded = _decrypt_pushes(s, config, pushes)

    ev = _by_id(decoded["events"], "ordinary CLI session turn")
    assert ev is not None
    # The enrichment keys must not pollute non-channel rows — otherwise
    # the cloud's renderer would show empty "Conversation info" labels
    # on every CLI turn.
    for k in ("provider", "chat_id", "sender_id", "sender", "direction"):
        assert k not in ev, (
            f"non-channel event leaked enrichment key {k!r}: {ev!r}"
        )


# ── 5. Encrypted blob still does not leak plaintext ─────────────────────────


def test_blob_still_e2e_encrypted_no_plaintext_leak(sync_with_channel_events):
    s, config = sync_with_channel_events
    pushes = s._build_brain_cache_pushes(config)
    assert len(pushes) == 1
    blob = pushes[0]["blob"]
    assert isinstance(blob, str)
    # Plaintext sender / chat ids / message bodies must not appear in the
    # ciphertext blob — same E2E invariant the Phase 2 happy-path test
    # asserts. The cloud only ever stores ciphertext.
    assert "1532693273" not in blob
    assert "vivekchand" not in blob
    assert "how are you doing?" not in blob
    assert "ping from signal" not in blob


# ── 6. Direct unit test on the enrichment helper (no DuckDB) ────────────────


def test_channel_enrichment_helper_handles_missing_id_gracefully():
    """The helper must never raise on malformed rows — fresh installs
    have legitimately partial data and a brain cache push that 500s on
    one bad row would silently kill the cache for every other row in
    the same heartbeat."""
    import clawmetry.sync as s
    importlib.reload(s)

    # Channel row with no id at all (impossible from sync_channel_messages
    # but the helper is defensive — heartbeat must never crash).
    enrich = s._channel_enrichment_from_row({
        "event_type": "channel.in",
        "data": {"text": "hi"},
    })
    assert enrich["provider"] == ""
    assert enrich["chat_id"] == ""
    assert enrich["direction"] == "in"

    # Non-channel row → empty dict (no enrichment keys appear).
    assert s._channel_enrichment_from_row({
        "event_type": "message", "data": {}
    }) == {}

    # raw_id with embedded colons (unusual but legal — Matrix event IDs
    # contain colons). The helper must split only the first two segments.
    enrich = s._channel_enrichment_from_row({
        "event_type": "channel.in",
        "id": "matrix:!room123:matrix.org:$evt:abc",
        "data": {"text": "hi"},
    })
    assert enrich["provider"] == "matrix"
    assert enrich["chat_id"] == "!room123"
