"""E2E contract test: Telegram messages → DuckDB → /api/brain-history.

This file pins down the END-TO-END shape that the Telegram (and any other
chat-channel) ingest path MUST satisfy.

Pipeline under test:

    OpenClaw filesystem (per-chat .jsonl)
        →  ClawMetry sync.py (``sync_channel_messages``)
        →  Local DuckDB (``channel_messages`` table)
        →  /api/brain-history (renders chat_id/sender/body)

Why this exists:
  1. Forces a clear regression contract for the Telegram ingest path so
     future refactors can't silently break it.
  2. Catches regressions in any link of the chain (filesystem reader,
     DuckDB writer, brain-history reader, JSON shaping).
  3. Documents the expected end-to-end JSON shape for reviewers.

Hard rules followed:
  * ``monkeypatch`` for env vars (no global mutation).
  * ``tmp_path`` everywhere — never touches ``~/.openclaw`` or
    ``~/.clawmetry``.
  * No real-name strings in payloads (per project policy).
"""

from __future__ import annotations

import importlib
import json
import time

import pytest
from flask import Flask


# --------------------------------------------------------------------------- #
# Ingest-function probe
#
# The contract is: ``clawmetry.sync`` exports ``sync_channel_messages``
# (landed in #1192), which iterates ``~/.openclaw/<provider>/`` per the
# canonical ``_CHANNEL_DIRS`` list and ingests every event into the local
# DuckDB ``channel_messages`` table. We probe for it so the module still
# loads on branches that pre-date that ingest PR (skip rather than crash).
# --------------------------------------------------------------------------- #
try:  # pragma: no cover — exercised by the skipif gate
    from clawmetry.sync import sync_channel_messages  # noqa: F401 — from #1192
    _INGEST_AVAILABLE = True
except Exception:
    _INGEST_AVAILABLE = False

pytestmark = pytest.mark.skipif(
    not _INGEST_AVAILABLE,
    reason="clawmetry.sync.sync_channel_messages not available "
           "(pre-#1192 branch)",
)


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #
def _wait_flush(store, t: float = 2.0) -> None:
    """Block until the in-memory ring buffer drains to DuckDB."""
    deadline = time.monotonic() + t
    while time.monotonic() < deadline:
        try:
            if store.health()["ring_depth"] == 0:
                return
        except Exception:
            return
        time.sleep(0.02)


def _isolated_env(tmp_path, monkeypatch):
    """Point both OpenClaw and ClawMetry at tmp dirs and the local-store
    fast-path at a tmp DuckDB. Reload modules so module-level state
    (DB path, env reads) picks up the new env.

    NOTE: ``sync._get_openclaw_dir()`` reads ``CLAWMETRY_OPENCLAW_DIR``,
    not ``OPENCLAW_HOME`` — we set both for belt-and-braces."""
    openclaw_home = tmp_path / "openclaw"
    clawmetry_home = tmp_path / "clawmetry"
    openclaw_home.mkdir()
    clawmetry_home.mkdir()

    monkeypatch.setenv("OPENCLAW_HOME", str(openclaw_home))
    monkeypatch.setenv("CLAWMETRY_OPENCLAW_DIR", str(openclaw_home))
    monkeypatch.setenv("CLAWMETRY_HOME", str(clawmetry_home))
    monkeypatch.setenv(
        "CLAWMETRY_LOCAL_STORE_PATH", str(clawmetry_home / "events.duckdb")
    )
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")

    return openclaw_home, clawmetry_home


@pytest.fixture
def env(tmp_path, monkeypatch):
    """One-stop fixture: isolated dirs + reloaded local_store + brain
    blueprint mounted on a fresh Flask app."""
    openclaw_home, clawmetry_home = _isolated_env(tmp_path, monkeypatch)

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import clawmetry.sync as sync_mod
    importlib.reload(sync_mod)
    import routes.brain as br
    importlib.reload(br)

    app = Flask(__name__)
    app.register_blueprint(br.bp_brain)

    yield {
        "openclaw_home": openclaw_home,
        "clawmetry_home": clawmetry_home,
        "store": ls.get_store(),
        "ls": ls,
        "sync": sync_mod,
        "app": app,
    }

    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _seed_chat_file(
    openclaw_home,
    *,
    provider: str,
    chat_id: str,
    events: list[dict],
) -> None:
    """Write a per-chat ``.jsonl`` file in the shape the OpenClaw channel
    adapters produce on disk. One JSON object per line."""
    chan_dir = openclaw_home / provider
    chan_dir.mkdir(parents=True, exist_ok=True)
    chat_file = chan_dir / f"{chat_id}.jsonl"
    chat_file.write_text("\n".join(json.dumps(e) for e in events) + "\n")


def _ingest(env_) -> int:
    """Trigger the ingest path under test.

    ``sync_channel_messages`` iterates every provider in the canonical
    ``_CHANNEL_DIRS`` tuple, so a single call drains all seeded channels
    in one go. Returns the number of newly ingested rows."""
    cfg = {"api_key": "test-key", "node_id": "test-node"}
    state: dict = {}
    paths = {
        "sessions_dir": str(env_["openclaw_home"]),
        "log_dir": str(env_["openclaw_home"]),
    }
    n = env_["sync"].sync_channel_messages(cfg, state, paths)
    _wait_flush(env_["store"])
    return n


# --------------------------------------------------------------------------- #
# Primary contract
# --------------------------------------------------------------------------- #
def test_telegram_message_flows_end_to_end(env):
    """Headline assertion: a single Telegram event seeded on disk shows up
    in ``/api/brain-history`` with chat_id, sender, and body intact."""
    chat_id = "1532693273"
    sample_event = {
        "ts": "2026-05-13T22:54:00Z",
        "chat_id": f"telegram:{chat_id}",
        "sender_name": "tester-one",
        "sender_id": chat_id,
        "text": "hello, how are you doing?",
        "provider": "telegram",
        "direction": "in",  # in = inbound from user, out = outbound from agent
    }
    _seed_chat_file(
        env["openclaw_home"],
        provider="telegram",
        chat_id=chat_id,
        events=[sample_event],
    )

    _ingest(env)

    # 4. Verify the row landed in DuckDB via the typed query helper.
    rows = env["store"].query_channel_messages(provider="telegram", limit=10)
    assert len(rows) == 1, f"expected 1 channel_messages row, got {len(rows)}"
    row = rows[0]
    assert row["provider"] == "telegram"
    assert row["sender_name"] == "tester-one"
    assert row["direction"] == "in"
    assert row["body"] is not None and "hello" in row["body"].lower()

    # 5. Verify /api/brain-history returns it with the expected shape.
    resp = env["app"].test_client().get("/api/brain-history?limit=20")
    assert resp.status_code == 200
    body = resp.get_json() or {}
    events = body.get("events", [])

    tg = [
        e for e in events
        if (e.get("channel") or "").lower() == "telegram"
        or (e.get("source") or "").lower().startswith("telegram")
    ]
    assert len(tg) >= 1, (
        f"no telegram-channel event in brain-history; got: "
        f"{[e.get('channel') for e in events]}"
    )
    ev = tg[0]
    # Regression for #1190: detail must not be empty when body was present.
    assert ev.get("detail"), (
        "brain-history event has empty detail; "
        "regression on the bug fixed in #1190"
    )
    assert (ev.get("channel") or "").lower() == "telegram"
    assert ev.get("sender") == "tester-one" or ev.get("sender_name") == "tester-one"


# --------------------------------------------------------------------------- #
# Bonus: outbound (agent → user) message
# --------------------------------------------------------------------------- #
def test_outbound_message_renders_as_agent(env):
    """A ``direction: "out"`` event represents the agent replying to the
    user. The brain-history row must reflect that — either an explicit
    ``direction`` field, an ``actor``/``role`` of ``agent``, or the legacy
    ``type`` containing the word ``agent``. We accept any of those so this
    test isn't over-specified, but it MUST distinguish from inbound."""
    chat_id = "9000000001"
    _seed_chat_file(
        env["openclaw_home"],
        provider="telegram",
        chat_id=chat_id,
        events=[{
            "ts": "2026-05-13T23:00:00Z",
            "chat_id": f"telegram:{chat_id}",
            "sender_name": "agent-bot",
            "sender_id": "bot",
            "text": "Sure, here is the result.",
            "provider": "telegram",
            "direction": "out",
        }],
    )

    _ingest(env)

    rows = env["store"].query_channel_messages(provider="telegram", limit=10)
    assert any(r["direction"] == "out" for r in rows), (
        "outbound message did not land with direction='out' in DuckDB"
    )

    body = env["app"].test_client().get("/api/brain-history?limit=20").get_json()
    events = body.get("events", [])
    tg_out = [
        e for e in events
        if (e.get("channel") or "").lower() == "telegram"
        and (
            e.get("direction") == "out"
            or "agent" in (e.get("actor") or e.get("role") or e.get("type") or "").lower()
        )
    ]
    assert tg_out, "outbound telegram event not classified as agent in brain-history"


# --------------------------------------------------------------------------- #
# Bonus: multi-line text
# --------------------------------------------------------------------------- #
def test_multiline_text_survives_roundtrip(env):
    """Newlines inside ``text`` must round-trip through DuckDB unchanged.
    A common regression is JSONL re-encoding that strips ``\\n`` or
    collapses to a single line."""
    chat_id = "9000000002"
    payload = "line one\nline two\nline three"
    _seed_chat_file(
        env["openclaw_home"],
        provider="telegram",
        chat_id=chat_id,
        events=[{
            "ts": "2026-05-13T23:01:00Z",
            "chat_id": f"telegram:{chat_id}",
            "sender_name": "tester-multiline",
            "sender_id": chat_id,
            "text": payload,
            "provider": "telegram",
            "direction": "in",
        }],
    )

    _ingest(env)

    rows = env["store"].query_channel_messages(provider="telegram", limit=10)
    assert rows, "multi-line message did not ingest"
    assert rows[0]["body"] == payload, (
        f"multi-line body mangled: {rows[0]['body']!r} != {payload!r}"
    )


# --------------------------------------------------------------------------- #
# Bonus: unicode / emoji
# --------------------------------------------------------------------------- #
def test_unicode_emoji_byte_identical(env):
    """Emoji + non-ASCII must survive the disk → DuckDB → query roundtrip
    byte-for-byte. UTF-8 mishandling is a classic ingest bug."""
    chat_id = "9000000003"
    payload = "wave 👋 unicode café — naïve façade"
    _seed_chat_file(
        env["openclaw_home"],
        provider="telegram",
        chat_id=chat_id,
        events=[{
            "ts": "2026-05-13T23:02:00Z",
            "chat_id": f"telegram:{chat_id}",
            "sender_name": "tester-unicode",
            "sender_id": chat_id,
            "text": payload,
            "provider": "telegram",
            "direction": "in",
        }],
    )

    _ingest(env)

    rows = env["store"].query_channel_messages(provider="telegram", limit=10)
    assert rows, "unicode message did not ingest"
    assert rows[0]["body"] == payload, (
        f"unicode body mangled: {rows[0]['body']!r} != {payload!r}"
    )


# --------------------------------------------------------------------------- #
# Bonus: missing provider directory (graceful no-op)
# --------------------------------------------------------------------------- #
def test_missing_directory_is_silent_noop(env):
    """When NO per-provider directory exists (user never set up any
    chat channel), the ingest must be a silent no-op — no exception,
    no spurious rows. This protects every call site that loops over
    all known providers via ``_CHANNEL_DIRS``."""
    missing = env["openclaw_home"] / "telegram"  # we never create it
    assert not missing.exists(), "preflight: directory should not exist"

    # Must NOT raise. Returns 0 since every provider dir is absent.
    n = _ingest(env)
    assert n == 0, f"missing dirs should ingest 0 rows, got {n}"

    rows = env["store"].query_channel_messages(provider="telegram", limit=10)
    assert rows == [], "missing dir should produce zero rows"


# --------------------------------------------------------------------------- #
# Bonus: two providers ingested independently
# --------------------------------------------------------------------------- #
def test_two_channels_at_once(env):
    """Telegram + Signal sibling directories ingest independently and
    both end up addressable via the typed ``provider`` filter."""
    _seed_chat_file(
        env["openclaw_home"],
        provider="telegram",
        chat_id="9000000004",
        events=[{
            "ts": "2026-05-13T23:03:00Z",
            "chat_id": "telegram:9000000004",
            "sender_name": "tester-tg",
            "sender_id": "9000000004",
            "text": "from telegram",
            "provider": "telegram",
            "direction": "in",
        }],
    )
    _seed_chat_file(
        env["openclaw_home"],
        provider="signal",
        chat_id="9000000005",
        events=[{
            "ts": "2026-05-13T23:04:00Z",
            "chat_id": "signal:9000000005",
            "sender_name": "tester-sg",
            "sender_id": "9000000005",
            "text": "from signal",
            "provider": "signal",
            "direction": "in",
        }],
    )

    # Single call drains every provider in _CHANNEL_DIRS.
    _ingest(env)

    tg_rows = env["store"].query_channel_messages(provider="telegram", limit=10)
    sg_rows = env["store"].query_channel_messages(provider="signal", limit=10)
    assert len(tg_rows) == 1, f"telegram count wrong: {len(tg_rows)}"
    assert len(sg_rows) == 1, f"signal count wrong: {len(sg_rows)}"
    assert tg_rows[0]["body"] == "from telegram"
    assert sg_rows[0]["body"] == "from signal"
