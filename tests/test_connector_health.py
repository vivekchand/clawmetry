"""Tests for connector-liveness detection (incident 2026-05-24).

Why this exists
---------------
A Telegram inbound long-poll wedged (network stall → aborted shutdown that
timed out) and never restarted. The agent kept SENDING (scheduled crons
fired) but silently stopped RECEIVING for ~37h, and ClawMetry showed green
the whole time. The only evidence was diagnostic lines split across
``gateway.log`` (``starting provider`` / ``health-monitor … reason:
disconnected``) and ``gateway.err.log`` (``Polling stall detected`` /
``channel stop exceeded … abort``).

This module pins:
  1. ``sync.parse_connector_health_line`` against the REAL production log
     shapes captured from the user's machine.
  2. ``ingest_connector_health`` / ``query_connector_health`` round-trip +
     idempotency on re-tail.
  3. ``routes/health.py:_connector_liveness`` verdict — especially the
     ``down`` verdict that would have caught the deaf node.
"""

from __future__ import annotations

import importlib
from datetime import datetime, timedelta, timezone

import pytest


@pytest.fixture
def store(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.delenv("CLAWMETRY_ROLE", raising=False)
    import clawmetry.local_store as ls
    importlib.reload(ls)
    # On a dev box with the daemon running, get_store() returns a proxy to the
    # LIVE DuckDB (see get_store: _daemon_registered branch). Force a local
    # writer at the tmp path so this test is hermetic — a different file means
    # no contention with the real daemon's writer lock.
    monkeypatch.setattr(ls, "_daemon_registered", lambda: False)
    s = ls.get_store()
    yield s
    try:
        s.stop(flush=True)
    except Exception:
        pass


@pytest.fixture
def parse():
    from clawmetry import sync
    return sync.parse_connector_health_line


# ── parser: real production log shapes (captured 2026-05-23/24) ──────────

@pytest.mark.parametrize("line,provider,kind", [
    (
        "2026-05-23T07:44:04.115+02:00 [health-monitor] [telegram:default] "
        "health-monitor: restarting (reason: disconnected)",
        "telegram", "disconnect",
    ),
    (
        "2026-05-24T20:50:14.548+02:00 [telegram] [default] "
        "starting provider (@diya_vivek_bot)",
        "telegram", "started",
    ),
    (
        "2026-05-23T07:44:03.631+02:00 [telegram] Polling stall detected "
        "(no completed getUpdates for 880.28s); forcing restart.",
        "telegram", "stall",
    ),
    (
        "2026-05-23T07:44:09.204+02:00 [telegram] [default] channel stop "
        "exceeded 5000ms after abort; continuing shutdown",
        "telegram", "wedged",
    ),
])
def test_parses_real_connector_health_lines(parse, line, provider, kind):
    out = parse(line)
    assert out is not None, f"expected a match for: {line!r}"
    prov, k, ts = out
    assert prov == provider
    assert k == kind
    # Timestamp is normalised to UTC (CEST +02:00 → −2h).
    assert ts.endswith("+00:00")


@pytest.mark.parametrize("line", [
    "2026-05-24T20:29:21.392+02:00 [ws] unauthorized conn=e36a client=openclaw-control-ui",
    "2026-05-24T20:50:14.401+02:00 [gateway] ready",
    "2026-05-24T20:50:14.760+02:00 [telegram] menu text exceeded the budget",  # noise
    "not a log line at all",
    "",
])
def test_ignores_non_health_lines(parse, line):
    assert parse(line) is None


# ── store round-trip + idempotency ──────────────────────────────────────

def test_ingest_and_query_roundtrip(store):
    ts = datetime.now(timezone.utc).isoformat()
    store.ingest_connector_health(
        node_id="n1", provider="telegram", kind="disconnect", ts_iso=ts,
        raw="reason: disconnected",
    )
    store.flush()
    rows = store.query_connector_health(since_hours=24)
    assert len(rows) == 1
    assert rows[0]["provider"] == "telegram"
    assert rows[0]["kind"] == "disconnect"


def test_ingest_is_idempotent_on_retail(store):
    ts = datetime.now(timezone.utc).isoformat()
    for _ in range(3):  # a log rotation rescan re-feeds the same line
        store.ingest_connector_health(
            node_id="n1", provider="telegram", kind="stall", ts_iso=ts, raw="x",
        )
    store.flush()
    assert len(store.query_connector_health(since_hours=24)) == 1


# ── classifier verdict ───────────────────────────────────────────────────

def _verdict(monkeypatch, rows):
    """Run _connector_liveness with telegram enabled + crafted signals.

    The enabled-channels reader + classifier live in clawmetry.connector_health
    (shared with the daemon snapshot builder); _connector_liveness imports them
    at call time, so patching the source module takes effect.
    """
    import routes.health as h
    import routes.local_query as lq
    import clawmetry.connector_health as ch
    monkeypatch.setattr(ch, "enabled_channels_from_config", lambda *a, **k: ["telegram"])
    monkeypatch.setattr(lq, "local_store_via_daemon", lambda method, **kw: rows)
    out = h._connector_liveness()
    return out[0] if out else {}


def _ago(mins):
    return (datetime.now(timezone.utc) - timedelta(minutes=mins)).isoformat()


def test_down_when_deaf_with_no_recovery(monkeypatch):
    """The Diya incident: most-recent signal is a wedge/disconnect 37h ago,
    no recovery since → DOWN (this is the alarm that was missing)."""
    rows = [
        {"provider": "telegram", "kind": "wedged", "ts": _ago(37 * 60), "raw": ""},
        {"provider": "telegram", "kind": "disconnect", "ts": _ago(37 * 60 + 1), "raw": ""},
    ]
    v = _verdict(monkeypatch, rows)
    assert v["state"] == "down"
    assert "receive messages" in v["reason"]


def test_ok_after_recovery(monkeypatch):
    """A fresh 'starting provider' after an old disconnect → OK."""
    rows = [
        {"provider": "telegram", "kind": "started", "ts": _ago(3), "raw": ""},
        {"provider": "telegram", "kind": "disconnect", "ts": _ago(40), "raw": ""},
    ]
    assert _verdict(monkeypatch, rows)["state"] == "ok"


def test_degraded_when_flapping(monkeypatch):
    rows = [
        {"provider": "telegram", "kind": "started", "ts": _ago(2), "raw": ""},
        {"provider": "telegram", "kind": "disconnect", "ts": _ago(10), "raw": ""},
        {"provider": "telegram", "kind": "disconnect", "ts": _ago(25), "raw": ""},
        {"provider": "telegram", "kind": "disconnect", "ts": _ago(40), "raw": ""},
    ]
    assert _verdict(monkeypatch, rows)["state"] == "degraded"


def test_unknown_when_no_signals(monkeypatch):
    assert _verdict(monkeypatch, [])["state"] == "unknown"
