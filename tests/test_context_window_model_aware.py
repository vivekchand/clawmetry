"""Model-aware context window sizing (surfaced 2026-05-25).

currentContextTokens (the live prompt size) was rendered against a
hardcoded 200K window everywhere. A Claude Code turn on the 1M Opus
variant has ≈323K of live context, so the LLM Context Inspector gauge
read ">100%". ``context_window_for_model`` sizes the denominator from the
turn's model string and, defensively, from the observed token count (a
measured prompt can never exceed the model's window).
"""

from __future__ import annotations

import importlib

import pytest


@pytest.fixture
def ls():
    import clawmetry.local_store as _ls
    importlib.reload(_ls)
    return _ls


def test_default_window_is_200k(ls):
    assert ls.context_window_for_model("claude-opus-4-7") == 200_000
    assert ls.context_window_for_model("claude-sonnet-4-6") == 200_000
    assert ls.context_window_for_model("") == 200_000
    assert ls.context_window_for_model(None) == 200_000


def test_1m_marker_gives_1m_window(ls):
    assert ls.context_window_for_model("claude-opus-4-7[1m]") == 1_000_000
    assert ls.context_window_for_model("claude-opus-4-7-1m") == 1_000_000
    assert ls.context_window_for_model("CLAUDE-OPUS-4-7[1M]") == 1_000_000


def test_observed_over_base_bumps_to_1m(ls):
    # No 1m marker in the string, but the measured prompt exceeds 200K →
    # the session must be on a larger-window variant. Bump so the gauge
    # never reads >100%. This is the exact 323K Claude Code case.
    assert ls.context_window_for_model("claude-opus-4-7", 323_485) == 1_000_000


def test_observed_under_base_keeps_200k(ls):
    # The user's normal OpenClaw agent: 200K window, compacts at 160K.
    assert ls.context_window_for_model("claude-opus-4-7", 150_000) == 200_000


def test_observed_over_1m_rounds_up(ls):
    assert ls.context_window_for_model("claude-opus-4-7", 1_300_000) == 2_000_000


def test_peek_returns_model_aware_window(ls, tmp_path, monkeypatch):
    """End-to-end: a 1M-context turn (≈323K live) yields context_window=1M
    in the peek result, not the hardcoded 200K."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    importlib.reload(ls)
    ls.mark_writer_owner()
    store = ls.get_store()
    store.ingest({
        "id": "ctxwin-1",
        "node_id": "agent+Macbook-Pro-2-local",
        "agent_id": "main",
        "session_id": "625c0ad9-71af-4a56-9a3b-cab396860a85",
        "event_type": "assistant",
        "ts": "2026-05-25T18:50:51.723Z",
        "data": {
            "type": "assistant", "version": 3,
            "message": {
                "role": "assistant", "model": "claude-opus-4-7",
                "usage": {
                    "input_tokens": 2,
                    "output_tokens": 140,
                    "cache_read_input_tokens": 320_000,
                    "cache_creation_input_tokens": 3_483,
                },
            },
        },
        "model": "claude-opus-4-7",
    })
    # flush
    import time
    deadline = time.monotonic() + 2
    while time.monotonic() < deadline and store.health().get("ring_depth", 0):
        time.sleep(0.02)

    peek = store.query_context_window_peek(scan_sessions=5)
    assert peek["input_tokens"] == 2 + 320_000 + 3_483  # 323485
    assert peek["context_window"] == 1_000_000, (
        f"window not model/observed-aware; got {peek.get('context_window')}"
    )
    try:
        store.stop(flush=True)
    except Exception:
        pass
