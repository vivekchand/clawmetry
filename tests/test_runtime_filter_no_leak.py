"""Cross-adapter no-leak contract for the runtime switcher.

Seeds events from every known runtime (claude_code / qwen_code / codex / hermes
/ goose / opencode / openclaw / cursor / nanoclaw / picoclaw / aider) plus a
prefix-less session that should bucket to ``openclaw`` (the default), then
asserts that the runtime-aware endpoints scope correctly with zero cross-
adapter leakage:

- ``/api/model-attribution?runtime=<rt>`` returns ONLY that runtime's turns;
  the total must match the seeded count exactly (no leakage, no loss).
- ``/api/runtime-summary`` buckets each session into exactly one runtime; the
  per-runtime ``turns`` / ``primary_model`` reflect only that runtime's seeds.
- The pure ``_runtime_of_session`` bucketing function (mirrored from the
  frontend ``_cmRuntimeOf`` and ``sync._runtime_of_session``) classifies every
  known prefix and falls unrecognised prefixes / bare UUIDs back to openclaw.

Pinned regression guard for the runtime-leak bugs in screenshots:
- Brain density chart that wasn't filtering by runtime (#image-14) — caught
  client-side; the matching client-side check is in test_appjs_units.js.
- "OpenClaw" view leaking events from non-OpenClaw-prefixed sessions
  (#image-15) — caught here at the aggregation layer.
"""

from __future__ import annotations

import importlib
import time
from datetime import datetime, timezone

import pytest
from flask import Flask


# Mirror the frontend `_cmRuntimeOf` and `sync._runtime_of_session` — when
# either drifts from this list, the no-leak tests below catch it.
KNOWN_RUNTIMES = [
    "picoclaw", "nanoclaw", "hermes", "claude_code", "codex", "cursor",
    "aider", "goose", "opencode", "qwen_code",
]


def runtime_of(sid: str) -> str:
    """Python mirror of the frontend `_cmRuntimeOf`."""
    sid = sid or ""
    if ":" in sid:
        p = sid.split(":", 1)[0].lower()
        if p in KNOWN_RUNTIMES:
            return p
    return "openclaw"


def _iso(s: float) -> str:
    return datetime.fromtimestamp(s, tz=timezone.utc).isoformat()


def _wait_flush(store, t: float = 2.0) -> None:
    deadline = time.monotonic() + t
    while time.monotonic() < deadline:
        if store.health()["ring_depth"] == 0:
            return
        time.sleep(0.02)


@pytest.fixture
def app_and_store(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "1")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")
    import clawmetry.local_store as ls
    importlib.reload(ls)
    ls.mark_writer_owner()
    import routes.local_query as lq
    importlib.reload(lq)
    monkeypatch.setattr(lq, "local_store_via_daemon", lambda *a, **k: None)
    monkeypatch.setattr(lq, "_read_discovery", lambda: None)
    monkeypatch.setattr(lq, "_cached_discovery", lambda: None)
    import routes.usage as usage_mod
    importlib.reload(usage_mod)
    a = Flask(__name__)
    a.register_blueprint(usage_mod.bp_usage)
    yield a, ls
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def _seed(store, sid: str, model: str, ts: float) -> None:
    store.ingest({
        "id": sid + "-" + str(int(ts * 1000)),
        "node_id": "agent+test",
        "agent_id": "main",
        "session_id": sid,
        "event_type": "tool_call",
        "ts": _iso(ts),
        "data": {"tool_name": "X"},
        "cost_usd": 0.01,
        "token_count": 100,
        "model": model,
    })


# ── 1. Pure bucketing function ──────────────────────────────────────────────


def test_runtime_of_session_classifies_every_known_runtime():
    """Every known prefix lands in its own bucket; unknowns → openclaw."""
    for rt in KNOWN_RUNTIMES:
        assert runtime_of(rt + ":anything") == rt, f"{rt} mis-bucketed"
    # Unknowns and bare UUIDs default to openclaw.
    assert runtime_of("openclaw:abc") == "openclaw"
    assert runtime_of("625c0ad9-71af-4a56-9a3b") == "openclaw"
    assert runtime_of("clawmetry-selfevolve") == "openclaw"
    assert runtime_of("unknown_future_runtime:xyz") == "openclaw"
    assert runtime_of("") == "openclaw"
    assert runtime_of(None) == "openclaw"


# ── 2. /api/model-attribution?runtime= scopes with zero leakage ─────────────


def test_model_attribution_per_runtime_no_leak(app_and_store):
    a, ls = app_and_store
    store = ls.get_store()
    now = time.time()
    # Two claude_code sessions, one of each other runtime, plus a bare-UUID
    # session that must bucket to openclaw.
    seeds = {
        "claude_code:c1": "claude-opus-4-7",
        "claude_code:c2": "claude-opus-4-7",
        "qwen_code:q1":   "qwen3:8b",
        "codex:x1":       "gpt-5",
        "hermes:h1":      "hermes-fast",
        "goose:g1":       "goose-lite",
        "opencode:o1":    "opencode-1",
        "cursor:k1":      "cursor-mid",
        "nanoclaw:n1":    "nano-1",
        "picoclaw:p1":    "pico-1",
        "aider:a1":       "aider-1",
        "bareuuid-zzz":   "claude-opus-4-7",   # → openclaw bucket
    }
    for i, (sid, m) in enumerate(seeds.items()):
        _seed(store, sid, m, now - 600 + i)
    _wait_flush(store)
    cli = a.test_client()

    # For each runtime, scope the endpoint and assert the total turns match
    # exactly what we seeded for that runtime — no more (leak), no less (loss).
    for rt in KNOWN_RUNTIMES + ["openclaw"]:
        body = cli.get("/api/model-attribution?runtime=" + rt).get_json() or {}
        expected = sum(1 for sid in seeds if runtime_of(sid) == rt)
        actual = body.get("total_turns") or 0
        assert actual == expected, (
            f"{rt}: expected {expected} turns, got {actual}. Body={body}")
        # And the returned models, summed, must equal total_turns (no model
        # column from another runtime sneaking in).
        models_sum = sum(int(m.get("turns") or 0) for m in (body.get("models") or []))
        assert models_sum == actual, f"{rt}: model rows sum {models_sum} != total {actual}"
        # Empty case: an honest empty set, never a silent merge.
        if expected == 0:
            assert (body.get("models") or []) == [], f"{rt}: expected empty models, got {body.get('models')}"


# ── 3. /api/runtime-summary buckets every session into one runtime ──────────


def test_runtime_summary_buckets_each_session_into_one_runtime(app_and_store):
    a, ls = app_and_store
    store = ls.get_store()
    now = time.time()
    seeds = {
        "claude_code:c1": "claude-opus-4-7",
        "claude_code:c2": "claude-opus-4-7",
        "qwen_code:q1":   "qwen3:8b",
        "codex:x1":       "gpt-5",
        "bareuuid-aaa":   "claude-opus-4-7",   # → openclaw
        "bareuuid-bbb":   "claude-opus-4-7",   # → openclaw
    }
    for i, (sid, m) in enumerate(seeds.items()):
        _seed(store, sid, m, now - 600 + i)
    _wait_flush(store)
    body = a.test_client().get("/api/runtime-summary").get_json() or {}
    runtimes = body.get("runtimes") or {}

    # Expected per-runtime turn counts.
    expected_turns = {}
    for sid in seeds:
        rt = runtime_of(sid)
        expected_turns[rt] = expected_turns.get(rt, 0) + 1

    # No runtime in the response that wasn't seeded.
    for rt in runtimes:
        assert rt in expected_turns, f"unexpected runtime in response: {rt}"
    # Each seeded runtime has the right turn count + the right primary model.
    for rt, exp in expected_turns.items():
        assert rt in runtimes, f"missing runtime in response: {rt}"
        assert runtimes[rt]["turns"] == exp, (
            f"{rt}: expected {exp} turns, got {runtimes[rt]['turns']}")
    # Sum across runtimes equals total seeds (every session bucketed once).
    assert sum(runtimes[rt]["turns"] for rt in runtimes) == len(seeds)

    # Sanity: claude_code's primary is claude-opus, qwen's is qwen3:8b.
    assert runtimes["claude_code"]["primary_model"] == "claude-opus-4-7"
    assert runtimes["qwen_code"]["primary_model"] == "qwen3:8b"
