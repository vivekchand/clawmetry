"""Tests for sync_channel_messages — OpenClaw chat-channel ingest.

Bug pinned by these tests
-------------------------

ClawMetry's sync daemon used to watch ONLY
``~/.openclaw/agents/main/sessions/*.jsonl``. OpenClaw's chat-channel adapters
(Telegram, Signal, WhatsApp, Discord, Slack, IRC, iMessage, …) persist their
inbound + outbound messages to a sibling per-provider directory:
``~/.openclaw/<channel>/<chat_id>.jsonl``. None of those rows reached DuckDB,
so the Brain tab and ``channel_messages`` table missed every chat-channel
turn — the user reported "I message Diya on Telegram and ClawMetry shows
nothing".

What we cover
-------------
1. A Telegram-shaped jsonl file lands in BOTH the ``events`` table (so the
   Brain timeline paints) AND the ``channel_messages`` table (so the
   per-provider routes in ``routes/channels.py`` paint).
2. Outbound (``role: assistant``) messages get ``direction='out'``.
3. Sibling channel directories (``signal/``, ``slack/``, …) are picked up
   off the same code path with no extra config.
4. Per-adapter bookkeeping files (e.g. ``update-offset-default.json``) are
   skipped — we don't try to parse them as transcripts.
5. Re-running sync against an unchanged file is a no-op (offset persisted).
6. Re-running sync after the file grew tails JUST the new lines.

DuckDB-first hard rule (``feedback_duckdb_first_rule``): every chat-channel
event MUST land in DuckDB. JSONL re-reads at request time are violations.
"""

from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest


@pytest.fixture
def store_env(tmp_path, monkeypatch):
    """Per-test DuckDB + a fake OPENCLAW_HOME we control."""
    duck = tmp_path / "events.duckdb"
    oc_home = tmp_path / "openclaw"
    oc_home.mkdir()

    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(duck))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_OPENCLAW_DIR", str(oc_home))

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import clawmetry.sync as sync_mod
    importlib.reload(sync_mod)

    store = ls.get_store()
    yield {
        "store": store,
        "ls": ls,
        "sync": sync_mod,
        "oc_home": oc_home,
        "duck": duck,
    }
    try:
        store.stop(flush=True)
    except Exception:
        pass


def _seed_telegram_chat(oc_home: Path, chat_id: str, lines: list[dict]) -> Path:
    """Write a Telegram-shaped jsonl (one event per line) to
    ``<oc_home>/telegram/<chat_id>.jsonl``."""
    d = oc_home / "telegram"
    d.mkdir(exist_ok=True)
    p = d / f"{chat_id}.jsonl"
    p.write_text("\n".join(json.dumps(line) for line in lines) + "\n")
    return p


def _stub_config_state_paths(oc_home: Path) -> tuple[dict, dict, dict]:
    """Minimal config/state/paths a sync_* function needs. ``paths`` is
    only consulted for ``sessions_dir``/``log_dir`` by other helpers — the
    channel sync derives its watch root from ``_get_openclaw_dir()``, which
    we already pinned via the CLAWMETRY_OPENCLAW_DIR env."""
    return (
        {"api_key": "test-key", "node_id": "test-node"},
        {},
        {"sessions_dir": str(oc_home), "log_dir": str(oc_home)},
    )


def _flush(store) -> None:
    """Force the local store's background flusher to drain the ring."""
    store._flush_now()


def test_telegram_inbound_lands_in_events_and_channel_messages(store_env):
    """A user→bot Telegram message lands in BOTH ``events`` and
    ``channel_messages``, with channel='telegram' and direction='in'."""
    store = store_env["store"]
    sync_mod = store_env["sync"]
    oc_home = store_env["oc_home"]

    _seed_telegram_chat(oc_home, "1532693273", [
        {
            "id": 8463,
            "ts": "2026-05-13T22:00:00Z",
            "direction": "in",
            "from": {"id": 1532693273, "username": "vivek", "first_name": "Vivek"},
            "text": "hey diya — what's the deploy status?",
        },
    ])

    cfg, state, paths = _stub_config_state_paths(oc_home)
    n = sync_mod.sync_channel_messages(cfg, state, paths)
    _flush(store)
    assert n == 1, f"expected 1 ingested row, got {n}"

    # ── events table ─────────────────────────────────────────────────────
    evs = store.query_events(event_type="channel.in", limit=10)
    assert len(evs) == 1, evs
    e = evs[0]
    assert e["agent_id"] == "main"
    assert e["event_type"] == "channel.in"
    assert e["ts"] == "2026-05-13T22:00:00Z"
    assert e["node_id"] == "test-node"

    # ── channel_messages table ───────────────────────────────────────────
    rows = store._fetch(
        "SELECT provider, channel_id, sender_id, sender_name, body, "
        "direction FROM channel_messages WHERE provider = ?",
        ["telegram"],
    )
    assert len(rows) == 1
    provider, chan_id, sid, sname, body, direction = rows[0]
    assert provider == "telegram"
    assert chan_id == "1532693273"
    assert sid == "1532693273"
    assert sname in ("vivek", "Vivek")  # username preferred but first_name OK
    assert "deploy status" in body
    assert direction == "in"


def test_telegram_outbound_assistant_role_marked_out(store_env):
    """A bot→user message (role='assistant') gets direction='out'."""
    store = store_env["store"]
    sync_mod = store_env["sync"]
    oc_home = store_env["oc_home"]

    _seed_telegram_chat(oc_home, "1532693273", [
        {
            "message_id": 8464,
            "ts": "2026-05-13T22:00:30Z",
            "role": "assistant",
            "text": "Deploy is green — last release 12 minutes ago.",
        },
    ])

    cfg, state, paths = _stub_config_state_paths(oc_home)
    sync_mod.sync_channel_messages(cfg, state, paths)
    _flush(store)

    rows = store._fetch(
        "SELECT direction, body FROM channel_messages WHERE provider = ?",
        ["telegram"],
    )
    assert len(rows) == 1
    direction, body = rows[0]
    assert direction == "out"
    assert "green" in body


def test_sibling_channel_dirs_picked_up(store_env):
    """Signal + Slack + WhatsApp messages land alongside Telegram with no
    config — the daemon iterates the canonical channel-dir list."""
    store = store_env["store"]
    sync_mod = store_env["sync"]
    oc_home = store_env["oc_home"]

    # Three sibling channel dirs, one inbound message each.
    for provider, chat_id, body in (
        ("signal", "+14155551212", "hey signal user"),
        ("slack",  "C123ABC", "deploy queue is empty"),
        ("whatsapp", "447700900000", "ack from whatsapp"),
    ):
        d = oc_home / provider
        d.mkdir()
        (d / f"{chat_id}.jsonl").write_text(json.dumps({
            "id": f"{provider}-1",
            "ts": "2026-05-13T22:01:00Z",
            "direction": "in",
            "text": body,
            "sender_id": chat_id,
        }) + "\n")

    cfg, state, paths = _stub_config_state_paths(oc_home)
    n = sync_mod.sync_channel_messages(cfg, state, paths)
    _flush(store)
    assert n == 3

    rows = store._fetch(
        "SELECT provider, channel_id, body FROM channel_messages "
        "ORDER BY provider",
        [],
    )
    providers_seen = {r[0] for r in rows}
    assert providers_seen == {"signal", "slack", "whatsapp"}


def test_non_transcript_files_are_skipped(store_env):
    """``update-offset-default.json`` and friends are per-adapter bookkeeping
    — they're NOT chat transcripts and must not be parsed as one. Asserts no
    crash + no rows ingested when the directory only has bookkeeping."""
    store = store_env["store"]
    sync_mod = store_env["sync"]
    oc_home = store_env["oc_home"]

    d = oc_home / "telegram"
    d.mkdir()
    # The real OpenClaw file shape on the user's machine (2026-05-13).
    (d / "update-offset-default.json").write_text(json.dumps({
        "version": 2,
        "lastUpdateId": 440774875,
        "botId": "8253463264",
    }))

    cfg, state, paths = _stub_config_state_paths(oc_home)
    n = sync_mod.sync_channel_messages(cfg, state, paths)
    _flush(store)
    assert n == 0
    rows = store._fetch(
        "SELECT COUNT(*) FROM channel_messages WHERE provider = ?",
        ["telegram"],
    )
    assert rows[0][0] == 0


def test_offset_advances_so_resync_is_no_op(store_env):
    """Two back-to-back syncs with no file change → second pass ingests 0."""
    store = store_env["store"]
    sync_mod = store_env["sync"]
    oc_home = store_env["oc_home"]

    _seed_telegram_chat(oc_home, "1532693273", [
        {"id": 1, "ts": "2026-05-13T22:00:00Z", "direction": "in", "text": "a"},
        {"id": 2, "ts": "2026-05-13T22:00:01Z", "direction": "in", "text": "b"},
    ])
    cfg, state, paths = _stub_config_state_paths(oc_home)

    n1 = sync_mod.sync_channel_messages(cfg, state, paths)
    n2 = sync_mod.sync_channel_messages(cfg, state, paths)
    _flush(store)

    assert n1 == 2
    assert n2 == 0, "offset should have advanced past EOF"
    # Offset was persisted on the state dict the daemon hands us.
    offsets = state.get("last_channel_offsets") or {}
    assert any(k.startswith("telegram/") for k in offsets), offsets


def test_appended_lines_picked_up_on_next_cycle(store_env):
    """Appending new lines to an already-tailed file is picked up on the
    next sync cycle — only the appended bytes are read."""
    store = store_env["store"]
    sync_mod = store_env["sync"]
    oc_home = store_env["oc_home"]

    p = _seed_telegram_chat(oc_home, "1532693273", [
        {"id": 10, "ts": "2026-05-13T22:00:00Z", "direction": "in", "text": "first"},
    ])
    cfg, state, paths = _stub_config_state_paths(oc_home)

    n1 = sync_mod.sync_channel_messages(cfg, state, paths)
    assert n1 == 1

    # Append two more lines.
    with p.open("a") as f:
        f.write(json.dumps({
            "id": 11, "ts": "2026-05-13T22:00:05Z",
            "direction": "in", "text": "second",
        }) + "\n")
        f.write(json.dumps({
            "id": 12, "ts": "2026-05-13T22:00:10Z",
            "direction": "in", "text": "third",
        }) + "\n")

    n2 = sync_mod.sync_channel_messages(cfg, state, paths)
    _flush(store)

    assert n2 == 2
    rows = store._fetch(
        "SELECT body FROM channel_messages WHERE provider = ? ORDER BY ts",
        ["telegram"],
    )
    bodies = [r[0] for r in rows]
    assert bodies == ["first", "second", "third"]
