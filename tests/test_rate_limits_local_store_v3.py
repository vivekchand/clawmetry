"""Regression guard for /api/rate-limits DuckDB fast path (Tier-1 #1565).

``routes/health.py:_try_local_store_rate_limits`` reads cost-bearing
event rows out of DuckDB ``events`` (1h rolling window) and buckets
rolling 1m / 1h utilisation per provider. Before the fast path, the
route aggregated only the in-memory ``metrics_store`` ring buffer that
the current dashboard *process* witnessed — empty after every restart
and blind to spend that landed on sibling fleet nodes.

This file seeds DuckDB events via ``LocalStore.ingest`` (the same write
path ``clawmetry/sync.py`` uses) and asserts:

1. Populated path — anthropic + openai events ingested → fast path
   returns ``_source='local_store'``, splits into separate provider
   buckets, and computes correct rpm/tokens_in/tokens_out + 1h rollups.
2. Empty events table → handler returns the populated zero-shell
   (``_source='local_store'``, providers=[]) instead of None, so the
   panel renders "no traffic" instantly instead of waiting for the
   legacy in-memory aggregation to confirm the same empty answer.
3. v3 real-shape regression — the route MUST recognise OpenClaw v3
   ``event_type='model.completed'`` rows with ``data.assistantMessage.usage``
   (NOT the synthetic ``event_type='message'`` + ``data.message.usage``
   shape that the original synthetic tests asserted on, per
   feedback_synthetic_tests_missed_real_event_shape.md).
4. Env gate honoured — with CLAWMETRY_LOCAL_STORE_READ=0 the fast path
   helper isn't called by the route handler.
"""

from __future__ import annotations

import importlib
import time
import uuid

import pytest
from flask import Flask


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import routes.local_query as lq
    importlib.reload(lq)
    import routes.health as health_mod
    importlib.reload(health_mod)

    # Isolate from a contributor's running daemon (see Issue #1538 pattern in
    # test_subagents_local_store_v3.py): without this, ``_ls_call`` proxies
    # through ``~/.clawmetry/local_query.json`` and the daemon queries its
    # OWN production DuckDB instead of our tmp_path fixture.
    monkeypatch.setattr(lq, "_read_discovery", lambda: None)

    # Dashboard module supplies _DEFAULT_RATE_LIMITS + _infer_provider used by
    # the helper. Importing it once initialises module state used elsewhere.
    import dashboard  # noqa: F401

    a = Flask(__name__)
    a.register_blueprint(health_mod.bp_health)
    yield a, ls, health_mod
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def _now_iso():
    from datetime import datetime, timezone
    return datetime.now(tz=timezone.utc).isoformat()


def _ingest_billable_event(store, *, model, provider, input_tokens, output_tokens, cost_usd, event_type="model.completed", ts=None, use_v3_shape=True):
    """Helper to ingest a single billable event in the v3 OpenClaw shape.

    The fast path walks BOTH the legacy ``data.message.usage`` shape (Anthropic
    SDK echo) and the v3-native ``data.assistantMessage.usage`` shape — this
    helper defaults to the v3 shape so tests catch the
    feedback_synthetic_tests_missed_real_event_shape.md class of bug.
    """
    usage_key = "assistantMessage" if use_v3_shape else "message"
    payload = {
        "model": model,
        "provider": provider,
        usage_key: {"usage": {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
        }},
    }
    store.ingest({
        "id":         f"evt-{uuid.uuid4().hex[:12]}",
        "node_id":    "node-test",
        "agent_type": "openclaw",
        "agent_id":   "main",
        "session_id": "sess-test",
        "event_type": event_type,
        "ts":         ts or _now_iso(),
        "data":       payload,
        "cost_usd":   cost_usd,
        "token_count": input_tokens + output_tokens,
        "model":      model,
    })


def test_rate_limits_local_store_tags_source_and_splits_providers(app):
    """Multi-provider population: anthropic + openai events seeded → fast
    path returns ``_source='local_store'`` and buckets each provider
    separately with correct 1m + 1h numbers."""
    a, ls, _health = app
    store = ls.get_store()

    # 3 recent Anthropic turns (all within the 1m window).
    for i in range(3):
        _ingest_billable_event(
            store,
            model="claude-opus-4-7",
            provider="anthropic",
            input_tokens=1000,
            output_tokens=500,
            cost_usd=0.045,
        )
    # 2 OpenAI turns (within 1m).
    for i in range(2):
        _ingest_billable_event(
            store,
            model="gpt-4o",
            provider="openai",
            input_tokens=2000,
            output_tokens=400,
            cost_usd=0.06,
        )
    # Public sync flush drains ring → DuckDB but keeps the singleton open
    # so the subsequent ``_ls_call`` path can query the same handle.
    store.flush()
    assert len(store.query_events(limit=100)) == 5

    r = a.test_client().get("/api/rate-limits")
    assert r.status_code == 200, r.get_data(as_text=True)
    body = r.get_json()
    assert body.get("_source") == "local_store", (
        f"_source must be local_store; got {body.get('_source')!r}"
    )
    providers = {p["provider"]: p for p in body.get("providers") or []}
    assert set(providers.keys()) == {"anthropic", "openai"}, (
        f"expected separate buckets for each provider; got {set(providers.keys())!r}"
    )

    ant = providers["anthropic"]
    assert ant["rpm"]["current"] == 3
    assert ant["tpm_input"]["current"] == 3000   # 3 × 1000
    assert ant["tpm_output"]["current"] == 1500  # 3 × 500
    assert ant["hour"]["requests"] == 3
    assert ant["hour"]["tokens_in"] == 3000
    assert ant["hour"]["tokens_out"] == 1500
    # Cost should be the sum across the 3 turns.
    assert ant["hour"]["cost_usd"] == pytest.approx(0.135, abs=1e-6)

    oai = providers["openai"]
    assert oai["rpm"]["current"] == 2
    assert oai["tpm_input"]["current"] == 4000   # 2 × 2000
    assert oai["tpm_output"]["current"] == 800   # 2 × 400

    # status colour ladder honours utilisation pct (green/amber/red).
    for p in providers.values():
        assert p["status"] in {"green", "amber", "red"}


def test_rate_limits_local_store_empty_returns_zero_shell(app):
    """Empty events table → fast path returns a populated zero-shell
    (``_source='local_store'``, providers=[]) rather than None, so the
    panel renders instantly instead of waiting for the slow legacy
    fallback to confirm the same empty answer (feedback_daemon_proxy
    pattern, mistake #2 — "Empty result is NOT a miss")."""
    a, ls, health_mod = app
    # Sanity: no events ingested.
    assert ls.get_store().query_events(limit=10) == []

    fast = health_mod._try_local_store_rate_limits()
    assert fast is not None, (
        "empty store must still tag _source=local_store to skip the slow legacy path"
    )
    assert fast.get("_source") == "local_store"
    assert fast.get("providers") == []
    assert "timestamp" in fast


def test_rate_limits_local_store_recognises_v3_event_shape(app):
    """v3 real-shape regression: real OpenClaw emits ``model.completed``
    rows with usage under ``data.assistantMessage.usage``. The fast path
    MUST count these — synthetic tests that filter on ``event_type='message'``
    + ``data.message.usage`` silently drop them on real installs (per
    feedback_synthetic_tests_missed_real_event_shape.md). One v3 row +
    one legacy synthetic row → both end up in the bucket."""
    a, ls, _health = app
    store = ls.get_store()
    _ingest_billable_event(
        store,
        model="claude-opus-4-7",
        provider="anthropic",
        input_tokens=1234,
        output_tokens=567,
        cost_usd=0.025,
        event_type="model.completed",
        use_v3_shape=True,  # data.assistantMessage.usage
    )
    _ingest_billable_event(
        store,
        model="claude-opus-4-7",
        provider="anthropic",
        input_tokens=100,
        output_tokens=50,
        cost_usd=0.004,
        event_type="message",   # legacy synthetic harness
        use_v3_shape=False,     # data.message.usage
    )
    store.flush()

    r = a.test_client().get("/api/rate-limits")
    assert r.status_code == 200
    body = r.get_json()
    assert body["_source"] == "local_store"
    providers = {p["provider"]: p for p in body["providers"]}
    ant = providers["anthropic"]
    assert ant["rpm"]["current"] == 2, (
        "BOTH the v3 and legacy event shapes must be counted; got "
        f"rpm_1m={ant['rpm']['current']}"
    )
    assert ant["tpm_input"]["current"] == 1334   # 1234 + 100
    assert ant["tpm_output"]["current"] == 617   # 567 + 50


def test_rate_limits_local_store_ignores_non_billable_event_types(app):
    """Tool calls / heartbeats / non-LLM events have no business in
    rate-limit utilisation. They MUST be filtered out by the
    billable-types allowlist even if they happen to carry a stray
    ``token_count`` column (e.g. tool retries)."""
    a, ls, _health = app
    store = ls.get_store()
    # Billable.
    _ingest_billable_event(
        store,
        model="claude-opus-4-7",
        provider="anthropic",
        input_tokens=1000,
        output_tokens=200,
        cost_usd=0.02,
    )
    # Non-billable noise: tool_call with a token_count column (synthetic
    # harnesses sometimes stamp this, real v3 doesn't — either way it's
    # NOT an LLM turn and must not inflate rate-limit utilisation).
    store.ingest({
        "id":         f"evt-{uuid.uuid4().hex[:12]}",
        "node_id":    "node-test",
        "event_type": "tool_call",
        "ts":         _now_iso(),
        "data":       {"tool": "Read", "args": {"file_path": "/etc/hosts"}},
        "cost_usd":   0.0,
        "token_count": 9999,
        "model":      "claude-opus-4-7",
    })
    store.flush()

    r = a.test_client().get("/api/rate-limits")
    body = r.get_json()
    assert body["_source"] == "local_store"
    ant = next(p for p in body["providers"] if p["provider"] == "anthropic")
    assert ant["rpm"]["current"] == 1, (
        "tool_call row must not be counted as an LLM request; got "
        f"rpm_1m={ant['rpm']['current']}"
    )
    assert ant["tpm_input"]["current"] == 1000
    assert ant["tpm_output"]["current"] == 200


def test_rate_limits_env_gate_off_bypasses_fast_path(tmp_path, monkeypatch):
    """With ``CLAWMETRY_LOCAL_STORE_READ=0`` the route MUST NOT call the
    fast path — even if the store has cost-bearing events available.
    Guards against accidental default-ON regressions
    (feedback_local_store_default_off_killed_moat.md, inverse direction:
    opt-OUT must work too)."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "0")

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import routes.local_query as lq
    importlib.reload(lq)
    import routes.health as health_mod
    importlib.reload(health_mod)
    monkeypatch.setattr(lq, "_read_discovery", lambda: None)

    store = ls.get_store()
    _ingest_billable_event(
        store,
        model="claude-opus-4-7",
        provider="anthropic",
        input_tokens=1000,
        output_tokens=200,
        cost_usd=0.02,
    )
    store.flush()

    import dashboard  # noqa: F401
    a = Flask(__name__)
    a.register_blueprint(health_mod.bp_health)
    r = a.test_client().get("/api/rate-limits")
    assert r.status_code == 200
    body = r.get_json()
    # Legacy path doesn't tag _source — its absence proves the gate held.
    assert "_source" not in body, (
        "env-gate OFF must NOT take the local_store fast path; got "
        f"body={body!r}"
    )
