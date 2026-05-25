"""backfill_event_costs must price family-runtime events.

Family runtimes (claude_code, cursor, …) are ingested by sync_family_runtimes
with cost_usd=None and the token split under ``data.extra.{inputTokens,
outputTokens}`` (not ``data.usage``). The #2049 backfill only read
``data.usage``, so these events stayed $0 — a heavy Opus session showed $0
in the Tracing + Cost tabs. The fix adds ``data.extra`` as a fallback usage
source; the existing _tok() already accepts the camelCase keys.
"""
from __future__ import annotations

import importlib
import time


def _wait_flush(store, t=3.0):
    deadline = time.monotonic() + t
    while time.monotonic() < deadline:
        if store.health()["ring_depth"] == 0:
            return
        time.sleep(0.02)


def _store(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "ev.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "2")
    monkeypatch.delenv("CLAWMETRY_ROLE", raising=False)
    import clawmetry.local_store as ls
    importlib.reload(ls)
    monkeypatch.setattr(ls, "_daemon_registered", lambda: False)  # in-process writer
    return ls, ls.get_store()


def _cost(store, eid):
    rows = store._fetch("SELECT cost_usd FROM events WHERE id = ?", [eid])
    return rows[0][0] if rows else None


def test_backfill_prices_family_event_via_extra(tmp_path, monkeypatch):
    ls, store = _store(tmp_path, monkeypatch)
    try:
        store.ingest({
            "id": "claude_code:ev-1",
            "node_id": "n", "agent_id": "main",
            "session_id": "claude_code:sess-1",
            "event_type": "message",
            "ts": "2026-05-25T12:00:00Z",
            # family shape: split under data.extra (camelCase), no data.usage
            "data": {"role": "assistant", "_runtime": "claude_code",
                     "extra": {"inputTokens": 100000, "outputTokens": 20000}},
            "cost_usd": None,
            "token_count": 120000,
            "model": "claude-opus-4-7",
        })
        _wait_flush(store)
        assert (_cost(store, "claude_code:ev-1") or 0) == 0, "starts uncosted"

        n = store.backfill_event_costs(batch=100)
        assert n >= 1, "backfill must price the family event"
        c = _cost(store, "claude_code:ev-1")
        assert c and c > 0, f"family event must be priced, got {c}"
        # sanity: 100k in + 20k out Opus is a few dollars, not cents and not absurd
        assert 0.5 < c < 50, f"cost out of sane range: {c}"
    finally:
        store.stop(flush=True)


def test_backfill_skips_event_with_no_token_split(tmp_path, monkeypatch):
    """No usage and no extra split -> left uncosted (honest, not a crash)."""
    ls, store = _store(tmp_path, monkeypatch)
    try:
        store.ingest({
            "id": "cursor:ev-1",
            "node_id": "n", "agent_id": "main",
            "session_id": "cursor:sess-1",
            "event_type": "message",
            "ts": "2026-05-25T12:00:00Z",
            "data": {"role": "assistant", "_runtime": "cursor"},  # no split anywhere
            "cost_usd": None,
            "token_count": 5000,
            "model": "claude-opus-4-7",
        })
        _wait_flush(store)
        store.backfill_event_costs(batch=100)
        assert (_cost(store, "cursor:ev-1") or 0) == 0, "no split -> stays uncosted"
    finally:
        store.stop(flush=True)
