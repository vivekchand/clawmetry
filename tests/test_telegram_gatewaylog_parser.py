"""Tests for ``sync.parse_telegram_outbound_line`` and the daemon
``sync_telegram_from_gateway_log`` helper.

Why this exists
---------------
OpenClaw stores Telegram direct chats entirely in memory — no JSONL is
ever written for them (memory ``reference_openclaw_telegram_inmemory.md``).
The only on-disk evidence is ``[telegram] sendMessage ok ...`` ACK lines
in ``~/.openclaw/logs/gateway.log``. This module pins the parser so the
real production log shapes (captured 2026-05-13 from the user's machine)
keep round-tripping into DuckDB after future refactors.
"""

from __future__ import annotations

import importlib

import pytest


@pytest.fixture
def store(tmp_path, monkeypatch):
    """Fresh per-test DuckDB so ``ingest_channel_message`` PRIMARY-KEY
    semantics are isolated from neighbours."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    import clawmetry.local_store as ls
    importlib.reload(ls)
    s = ls.get_store()
    yield s
    try:
        s.stop(flush=True)
    except Exception:
        pass


@pytest.fixture
def parser():
    """Return ``parse_telegram_outbound_line`` from a freshly-imported
    ``clawmetry.sync``. The lazy regex compile is module-global, so we
    don't reload here — every test calls into the same precompiled
    handle, which is exactly the production code path."""
    from clawmetry import sync
    return sync.parse_telegram_outbound_line


# ── parse_telegram_outbound_line — happy path on real log shapes ───────


def test_parses_real_sendmessage_line(parser):
    """The exact production line shape from gateway.log on 2026-05-13."""
    line = (
        "2026-05-13T22:54:19.865+02:00 [telegram] sendMessage ok "
        "chat=1532693273 message=8491"
    )
    row = parser(line)
    assert row is not None
    assert row["id"] == "telegram:1532693273:8491"
    assert row["provider"] == "telegram"
    assert row["channel_id"] == "telegram:1532693273"
    assert row["direction"] == "out"
    # Body MUST be None (the log only carries the ACK, not the message
    # text). A placeholder string would mislead the renderer.
    assert row["body"] is None
    assert row["ts"] == "2026-05-13T22:54:19.865+02:00"
    assert row["raw_blob"]["method"] == "sendMessage"
    assert row["raw_blob"]["body_capture"] == "ack_only"
    assert row["raw_blob"]["source"] == "gateway.log"


def test_parses_sendphoto_sendaudio_senddocument(parser):
    """Other media APIs follow the same pattern. Pinning these prevents
    a regex tightening from silently dropping non-text media."""
    cases = [
        ("sendPhoto", 8480),
        ("sendAudio", 9001),
        ("sendDocument", 9002),
        ("sendVideo", 9003),
        ("sendVoice", 9004),
        ("sendSticker", 9005),
        ("sendAnimation", 9006),
        ("sendLocation", 9007),
    ]
    for method, msg_id in cases:
        line = (
            f"2026-05-13T06:00:56.332+02:00 [telegram] {method} ok "
            f"chat=1532693273 message={msg_id}"
        )
        row = parser(line)
        assert row is not None, f"Failed to parse {method}"
        assert row["raw_blob"]["method"] == method
        assert row["id"] == f"telegram:1532693273:{msg_id}"
        assert row["direction"] == "out"


def test_parses_negative_chat_id_for_groups(parser):
    """Telegram group chat IDs are negative integers. Must round-trip."""
    line = (
        "2026-05-13T10:00:00.000+02:00 [telegram] sendMessage ok "
        "chat=-1001234567890 message=42"
    )
    row = parser(line)
    assert row is not None
    assert row["id"] == "telegram:-1001234567890:42"
    assert row["channel_id"] == "telegram:-1001234567890"


def test_parses_z_suffix_timestamp(parser):
    """Some gateway builds emit ``Z`` instead of ``+HH:MM``. Both work."""
    line = (
        "2026-05-13T22:54:19Z [telegram] sendMessage ok "
        "chat=1532693273 message=8491"
    )
    row = parser(line)
    assert row is not None
    assert row["ts"] == "2026-05-13T22:54:19Z"


# ── parse_telegram_outbound_line — non-matches ─────────────────────────


@pytest.mark.parametrize("line", [
    "",
    "not a log line at all",
    # Inbound diagnostic — no message ACK, must NOT be ingested as a fake
    # outbound row.
    "2026-05-11T17:59:03.570+02:00 [telegram] Polling stall detected (no completed getUpdates for 120.08s)",
    # Provider startup — same shape but nothing to record.
    "2026-05-09T12:00:23.582+02:00 [telegram] [default] starting provider (@diya_vivek_bot)",
    # Menu-shortening warning — common production noise.
    "2026-05-09T12:00:23.781+02:00 [telegram] menu text exceeded the conservative 5700-character payload budget",
    # Different channel — must not match.
    "2026-05-13T10:00:00.000+02:00 [signal] sendMessage ok chat=1 message=2",
    # Failed call (no `ok` token) — we only ingest acknowledged sends.
    "2026-05-13T10:00:00.000+02:00 [telegram] sendMessage failed chat=1 message=2",
])
def test_rejects_non_outbound_lines(parser, line):
    assert parser(line) is None


# ── sync_telegram_from_gateway_log — daemon helper integration ─────────


def _write_log(path, lines):
    with open(path, "w", encoding="utf-8") as f:
        for ln in lines:
            f.write(ln + "\n")


def _make_state():
    return {"last_event_ids": {}, "last_log_offsets": {}, "last_sync": None}


SAMPLE_LINES = [
    "2026-05-13T22:54:19.865+02:00 [telegram] sendMessage ok chat=1532693273 message=8491",
    "2026-05-13T19:54:35.123+02:00 [telegram] sendMessage ok chat=1532693273 message=8489",
    "2026-05-13T06:00:56.332+02:00 [telegram] sendPhoto ok chat=1532693273 message=8480",
    # Noise that must be skipped:
    "2026-05-13T07:00:00.000+02:00 [telegram] menu text exceeded the conservative 5700-character payload budget",
    "2026-05-13T08:00:00.000+02:00 [signal] sendMessage ok chat=1 message=2",
]


def test_ingests_outbound_messages_from_log(store, tmp_path, monkeypatch):
    """Full path: write a gateway.log, run the daemon helper once, query
    the DuckDB and assert the three outbound ACK rows are present."""
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    log_path = logs_dir / "gateway.log"
    _write_log(log_path, SAMPLE_LINES)

    monkeypatch.setenv("CLAWMETRY_OPENCLAW_DIR", str(tmp_path))
    from clawmetry import sync
    importlib.reload(sync)

    state = _make_state()
    n = sync.sync_telegram_from_gateway_log(config=None, state=state)
    assert n == 3

    # Round-trip through ingest_channel_message → query the table.
    rows = store._conn.execute(
        "SELECT id, provider, direction, channel_id, ts, body "
        "FROM channel_messages ORDER BY ts"
    ).fetchall()
    ids = [r[0] for r in rows]
    assert "telegram:1532693273:8480" in ids
    assert "telegram:1532693273:8489" in ids
    assert "telegram:1532693273:8491" in ids
    assert all(r[1] == "telegram" for r in rows)
    assert all(r[2] == "out" for r in rows)
    assert all(r[3] == "telegram:1532693273" for r in rows)
    assert all(r[5] is None for r in rows)  # body uncaptured


def test_tail_and_resume_does_not_reingest(store, tmp_path, monkeypatch):
    """Second cycle on an unchanged log returns 0 — the byte offset in
    state must skip already-read content."""
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    log_path = logs_dir / "gateway.log"
    _write_log(log_path, SAMPLE_LINES)

    monkeypatch.setenv("CLAWMETRY_OPENCLAW_DIR", str(tmp_path))
    from clawmetry import sync
    importlib.reload(sync)

    state = _make_state()
    n1 = sync.sync_telegram_from_gateway_log(config=None, state=state)
    n2 = sync.sync_telegram_from_gateway_log(config=None, state=state)
    assert n1 == 3
    assert n2 == 0

    # New ACK appended → only the new line is ingested.
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(
            "2026-05-14T08:00:00.000+02:00 [telegram] sendMessage ok "
            "chat=1532693273 message=8500\n"
        )
    n3 = sync.sync_telegram_from_gateway_log(config=None, state=state)
    assert n3 == 1


def test_handles_log_truncation_by_rescanning(store, tmp_path, monkeypatch):
    """If the file shrinks below the stored offset (rotation /
    truncation) we re-scan from byte 0. PRIMARY KEY makes the re-ingest
    a no-op for already-seen rows but new content is captured."""
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    log_path = logs_dir / "gateway.log"
    _write_log(log_path, SAMPLE_LINES)

    monkeypatch.setenv("CLAWMETRY_OPENCLAW_DIR", str(tmp_path))
    from clawmetry import sync
    importlib.reload(sync)

    state = _make_state()
    sync.sync_telegram_from_gateway_log(config=None, state=state)

    # Truncate to a SHORTER set of entries (simulating logrotate copy-
    # truncate; the new file is smaller than our stored offset).
    _write_log(log_path, [
        "2026-05-14T08:00:00.000+02:00 [telegram] sendMessage ok "
        "chat=1532693273 message=8501",
    ])
    n = sync.sync_telegram_from_gateway_log(config=None, state=state)
    # One brand-new row is ingested; the offset reset is logged.
    assert n == 1
    rows = store._conn.execute(
        "SELECT id FROM channel_messages WHERE id='telegram:1532693273:8501'"
    ).fetchall()
    assert len(rows) == 1


def test_handles_partial_trailing_line(store, tmp_path, monkeypatch):
    """A line still being written (no trailing newline) must be left for
    the next cycle, NOT half-parsed and ingested."""
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    log_path = logs_dir / "gateway.log"
    # Two complete lines + one partial (no \n at end).
    with open(log_path, "w", encoding="utf-8") as f:
        f.write(
            "2026-05-13T22:54:19.865+02:00 [telegram] sendMessage ok "
            "chat=1532693273 message=8491\n"
        )
        f.write(
            "2026-05-13T22:54:20.000+02:00 [telegram] sendMessage ok "
            "chat=1532693273 message=8492\n"
        )
        f.write(
            "2026-05-13T22:54:21.000+02:00 [telegram] sendMess"
        )

    monkeypatch.setenv("CLAWMETRY_OPENCLAW_DIR", str(tmp_path))
    from clawmetry import sync
    importlib.reload(sync)

    state = _make_state()
    n1 = sync.sync_telegram_from_gateway_log(config=None, state=state)
    assert n1 == 2  # only the two complete lines

    # Complete the partial line + add a third ACK.
    with open(log_path, "a", encoding="utf-8") as f:
        f.write("age ok chat=1532693273 message=8493\n")
        f.write(
            "2026-05-13T22:54:22.000+02:00 [telegram] sendMessage ok "
            "chat=1532693273 message=8494\n"
        )
    n2 = sync.sync_telegram_from_gateway_log(config=None, state=state)
    assert n2 == 2  # the previously-partial line + the new one


def test_missing_log_file_is_noop(store, tmp_path, monkeypatch):
    """A workspace with no gateway.log (fresh install / OpenClaw not
    started yet) must return 0 silently."""
    monkeypatch.setenv("CLAWMETRY_OPENCLAW_DIR", str(tmp_path))
    from clawmetry import sync
    importlib.reload(sync)
    state = _make_state()
    assert sync.sync_telegram_from_gateway_log(config=None, state=state) == 0


def test_ingest_is_idempotent_on_state_loss(store, tmp_path, monkeypatch):
    """Re-ingesting the same log with a fresh state dict (simulating
    ``~/.clawmetry/sync-state.json`` deletion) does not duplicate
    rows — the channel_messages PRIMARY KEY is the safety net behind
    the byte-offset bookkeeping."""
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    log_path = logs_dir / "gateway.log"
    _write_log(log_path, SAMPLE_LINES)

    monkeypatch.setenv("CLAWMETRY_OPENCLAW_DIR", str(tmp_path))
    from clawmetry import sync
    importlib.reload(sync)

    sync.sync_telegram_from_gateway_log(config=None, state=_make_state())
    sync.sync_telegram_from_gateway_log(config=None, state=_make_state())

    n = store._conn.execute(
        "SELECT COUNT(*) FROM channel_messages WHERE provider='telegram'"
    ).fetchone()[0]
    assert n == 3  # not 6
