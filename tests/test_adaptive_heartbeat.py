"""Tests for adaptive heartbeat cadence (epic #775 PR 2/3).

The cloud sets `viewer_active: true` on the `/ingest/heartbeat` response when a
viewer has the cloud dashboard open. The daemon flips its loop to FAST (3s) so
new Telegram / tool / brain events appear in the cloud Brain tab in ~3s
instead of waiting up to 60s. When nobody is watching we stay on SLOW (60s) to
keep idle bandwidth + Cloud Run cost flat.

Back-compat case: a cloud that hasn't deployed PR 1 of the epic yet won't set
the field, so missing → SLOW. This file pins all four branches of
`_pick_heartbeat_interval` plus the success / failure side-effects of
`send_heartbeat` against the module-level `_LAST_HEARTBEAT_RESPONSE` cache the
loop reads from.
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
def sync_mod(tmp_path, monkeypatch):
    """Reload `clawmetry.sync` against an isolated DuckDB so module state
    (esp. `_LAST_HEARTBEAT_RESPONSE`) is fresh per test."""
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

    yield s

    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


@pytest.fixture
def config(sync_mod):
    return {
        "node_id":         "node-test",
        "api_key":         "cm_test",
        "encryption_key":  sync_mod.generate_encryption_key(),
    }


# ── _pick_heartbeat_interval — pure function, all four branches ────────────────

def test_pick_interval_viewer_active_true_returns_fast(sync_mod):
    """viewer_active: true → FAST (3s)."""
    assert sync_mod._pick_heartbeat_interval({"viewer_active": True}) == \
        sync_mod.HEARTBEAT_INTERVAL_FAST
    assert sync_mod.HEARTBEAT_INTERVAL_FAST == 3


def test_pick_interval_viewer_active_false_returns_slow(sync_mod):
    """viewer_active: false → SLOW (60s)."""
    assert sync_mod._pick_heartbeat_interval({"viewer_active": False}) == \
        sync_mod.HEARTBEAT_INTERVAL_SLOW
    assert sync_mod.HEARTBEAT_INTERVAL_SLOW == 60


def test_pick_interval_missing_field_returns_slow(sync_mod):
    """Back-compat: cloud without PR 1 of #775 deployed won't set the field.
    Missing → SLOW so we don't accidentally hammer the cloud at 3s before
    the cloud-side viewer-presence tracker exists.
    """
    # Field absent entirely — the typical pre-PR-1 cloud response.
    assert sync_mod._pick_heartbeat_interval({}) == sync_mod.HEARTBEAT_INTERVAL_SLOW
    # Realistic shape: cloud only returns plan/sync_allowed today.
    assert sync_mod._pick_heartbeat_interval(
        {"plan": "free", "sync_allowed": True}
    ) == sync_mod.HEARTBEAT_INTERVAL_SLOW


def test_pick_interval_none_returns_slow(sync_mod):
    """No successful heartbeat yet (or a non-dict body) → SLOW."""
    assert sync_mod._pick_heartbeat_interval(None) == \
        sync_mod.HEARTBEAT_INTERVAL_SLOW
    # Defensive: a stray string from a misconfigured _post should not crash.
    assert sync_mod._pick_heartbeat_interval("nope") == \
        sync_mod.HEARTBEAT_INTERVAL_SLOW


# ── send_heartbeat side-effect: stash response for the loop ───────────────────

def test_send_heartbeat_active_viewer_stashes_for_fast_interval(
    sync_mod, config, monkeypatch
):
    """A successful heartbeat with viewer_active=true must leave the module
    in a state where the next `_pick_heartbeat_interval(_LAST_HEARTBEAT_RESPONSE)`
    returns FAST. This is the loop's contract.
    """
    monkeypatch.setattr(
        sync_mod, "_post",
        lambda url, payload, api_key: {"viewer_active": True, "plan": "pro"},
    )
    assert sync_mod.send_heartbeat(config) is True
    assert sync_mod._LAST_HEARTBEAT_RESPONSE == {
        "viewer_active": True, "plan": "pro",
    }
    assert (
        sync_mod._pick_heartbeat_interval(sync_mod._LAST_HEARTBEAT_RESPONSE)
        == sync_mod.HEARTBEAT_INTERVAL_FAST
    )


def test_send_heartbeat_idle_viewer_stashes_for_slow_interval(
    sync_mod, config, monkeypatch
):
    """viewer_active=false on the wire → loop derives SLOW."""
    monkeypatch.setattr(
        sync_mod, "_post",
        lambda url, payload, api_key: {"viewer_active": False},
    )
    assert sync_mod.send_heartbeat(config) is True
    assert (
        sync_mod._pick_heartbeat_interval(sync_mod._LAST_HEARTBEAT_RESPONSE)
        == sync_mod.HEARTBEAT_INTERVAL_SLOW
    )


def test_send_heartbeat_back_compat_missing_field(
    sync_mod, config, monkeypatch
):
    """Cloud hasn't deployed PR 1 of #775 yet — response lacks the field.
    The daemon must NOT regress to the fast cadence speculatively; SLOW only.
    """
    # Realistic pre-#775 cloud response shape (see comments on send_heartbeat).
    monkeypatch.setattr(
        sync_mod, "_post",
        lambda url, payload, api_key: {
            "plan": "free", "sync_allowed": True, "trial_days_left": 5,
        },
    )
    assert sync_mod.send_heartbeat(config) is True
    assert "viewer_active" not in sync_mod._LAST_HEARTBEAT_RESPONSE
    assert (
        sync_mod._pick_heartbeat_interval(sync_mod._LAST_HEARTBEAT_RESPONSE)
        == sync_mod.HEARTBEAT_INTERVAL_SLOW
    )


def test_send_heartbeat_5xx_clears_response_falls_back_to_slow(
    sync_mod, config, monkeypatch
):
    """Cloud returns 5xx → existing 3-attempt backoff path runs, returns
    False, and the stashed response is cleared so the next interval pick
    falls back to SLOW (don't burn FAST on a stale viewer flag from a
    previous successful heartbeat).
    """
    # Pre-seed a previously-active stash so we can prove it gets cleared.
    sync_mod._LAST_HEARTBEAT_RESPONSE = {"viewer_active": True}

    calls = {"n": 0}

    def _explode(url, payload, api_key):
        calls["n"] += 1
        raise RuntimeError("HTTP 503 Service Unavailable")

    monkeypatch.setattr(sync_mod, "_post", _explode)
    # Skip the real 1s/2s backoff between retries — we just need to assert
    # the path runs all 3 attempts and the stash is cleared.
    monkeypatch.setattr(sync_mod.time, "sleep", lambda *_a, **_kw: None)

    assert sync_mod.send_heartbeat(config) is False
    # Existing backoff path is preserved: 3 attempts before giving up.
    assert calls["n"] == 3
    # Stash cleared so the loop's next pick falls back to SLOW.
    assert sync_mod._LAST_HEARTBEAT_RESPONSE is None
    assert (
        sync_mod._pick_heartbeat_interval(sync_mod._LAST_HEARTBEAT_RESPONSE)
        == sync_mod.HEARTBEAT_INTERVAL_SLOW
    )
