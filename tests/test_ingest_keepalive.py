"""Ingest keepalive heartbeat (2026-07-30 Brain-window RCA).

A long synchronous ingest pass (e.g. a `runtime_backfill` raising the
claude_code depth from 50 to 465 sessions ≈ minutes of work) used to starve
the heartbeat, so the cloud relay's pending_queries (Brain time-window
fetches) sat undrained until the browser gave up with "Could not fetch this
window from your node yet". `_ingest_keepalive_heartbeat` re-sends the
heartbeat mid-loop, throttled to `_INGEST_KEEPALIVE_SEC`.
"""
from __future__ import annotations

import types

import pytest

import clawmetry.sync as sync


@pytest.fixture(autouse=True)
def _reset_keepalive_clock():
    sync._last_ingest_keepalive = 0.0
    yield
    sync._last_ingest_keepalive = 0.0


def test_keepalive_sends_heartbeat_and_throttles(monkeypatch):
    calls = []
    monkeypatch.setattr(sync, "send_heartbeat", lambda cfg: calls.append(cfg) or True)
    import clawmetry.config as cm_config
    monkeypatch.setattr(cm_config, "is_cloud_disabled", lambda: False)

    cfg = {"node_id": "n1"}
    assert sync._ingest_keepalive_heartbeat(cfg) is True
    # Immediately again: inside the throttle window — no second heartbeat.
    assert sync._ingest_keepalive_heartbeat(cfg) is False
    assert len(calls) == 1

    # Simulate the interval elapsing — fires again.
    sync._last_ingest_keepalive -= sync._INGEST_KEEPALIVE_SEC + 1
    assert sync._ingest_keepalive_heartbeat(cfg) is True
    assert len(calls) == 2


def test_keepalive_skips_when_cloud_disabled(monkeypatch):
    calls = []
    monkeypatch.setattr(sync, "send_heartbeat", lambda cfg: calls.append(cfg) or True)
    import clawmetry.config as cm_config
    monkeypatch.setattr(cm_config, "is_cloud_disabled", lambda: True)

    assert sync._ingest_keepalive_heartbeat({}) is False
    assert calls == []


def test_keepalive_never_raises(monkeypatch):
    def _boom(cfg):
        raise RuntimeError("cloud unreachable")

    monkeypatch.setattr(sync, "send_heartbeat", _boom)
    import clawmetry.config as cm_config
    monkeypatch.setattr(cm_config, "is_cloud_disabled", lambda: False)

    # Must swallow the error (the ingest pass it protects goes on).
    assert sync._ingest_keepalive_heartbeat({}) is True


def test_family_loop_calls_keepalive_per_session(monkeypatch):
    """sync_family_runtimes must tick the keepalive for EVERY session it
    walks — including ones it skips — so a deep backfill pass can never
    hold the heartbeat for minutes again."""
    session_ids = ["a", "b", "c"]

    class _FakeDetect:
        detected = True

    class _FakeAdapter:
        name = "claude_code"

        def detect(self):
            return _FakeDetect()

        def list_sessions(self, limit=None):
            for sid in session_ids:
                yield types.SimpleNamespace(id=sid)

    ticks = []
    monkeypatch.setattr(sync, "_ingest_keepalive_heartbeat",
                        lambda cfg: ticks.append(1))
    monkeypatch.setattr(sync, "_sync_allowed", lambda: True)
    monkeypatch.setattr(sync, "_family_adapter_classes", lambda: [_FakeAdapter])
    # Every session is "OpenClaw-spawned" → skipped before any store work,
    # keeping this test free of DuckDB/adapters while still walking the loop.
    monkeypatch.setattr(sync, "_openclaw_spawned_claude_ids",
                        lambda: set(session_ids))

    assert sync.sync_family_runtimes({"node_id": "n1"}, {}, {}) == 0
    assert len(ticks) == len(session_ids)
