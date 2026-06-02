"""Out-loop source tagging: a production agent built on any SDK can name itself
so it becomes a first-class source in ClawMetry (clawmetry.track.set_source).

Covers the full flow the named-source feature ships across 0.12.402-405:
  1. capture    — set_source()/CLAWMETRY_SOURCE → I._get_source()
  2. event      — _build_external_event carries `source`
  3. store      — external_api_calls.source column round-trips (idempotent
                  migration applies to pre-existing tables)
  4. snapshot   — _build_external_calls keeps source-tagged calls only
"""
import importlib
import os, sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import clawmetry.interceptor as I
import clawmetry.track as T


@pytest.fixture
def fresh_store(tmp_path, monkeypatch):
    """Reload `clawmetry.local_store` against a fresh DuckDB file."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "1")
    sys.modules.pop("clawmetry.local_store", None)
    import clawmetry.local_store as ls
    importlib.reload(ls)
    # Own the writer so get_store() opens the test DB directly instead of
    # proxying to a daemon that may be running on the dev machine (CI has none).
    ls.mark_writer_owner()
    store = ls.get_store()
    yield ls, store
    try:
        store.stop(flush=False)
    except Exception:
        pass


def test_default_no_source():
    I.set_source("")
    os.environ.pop("CLAWMETRY_SOURCE", None)
    assert I._get_source() == ""


def test_set_source_tags_calls():
    T.set_source("support-agent")
    assert I._get_source() == "support-agent"
    I.set_source("")


def test_env_var_fallback():
    I.set_source("")
    os.environ["CLAWMETRY_SOURCE"] = "investment-agent"
    try:
        assert I._get_source() == "investment-agent"
    finally:
        os.environ.pop("CLAWMETRY_SOURCE", None)


def test_source_is_bounded_and_stripped():
    I.set_source("  " + "x" * 500 + "  ")
    assert len(I._get_source()) <= 120
    I.set_source("")


# ── 2. event builder carries source ─────────────────────────────────────────


def test_external_event_carries_source():
    I.set_source("support-agent")
    try:
        ev = I._build_external_event(
            url="https://api.openai.com/v1/chat", method="post",
            status_code=200, latency_ms=12.3, library="httpx",
        )
        assert ev.get("type") == "external_api_call"
        assert ev.get("source") == "support-agent"
    finally:
        I.set_source("")


def test_external_event_omits_source_when_unset():
    I.set_source("")
    os.environ.pop("CLAWMETRY_SOURCE", None)
    ev = I._build_external_event(
        url="https://api.openai.com/v1/chat", method="get",
        status_code=200, latency_ms=1.0, library="requests",
    )
    assert "source" not in ev


# ── 3. store round-trip + idempotent migration ──────────────────────────────


def _ev(ts, source=None):
    e = {
        "type": "external_api_call", "ts": ts,
        "url": "https://api.openai.com/v1/x", "host": "api.openai.com",
        "method": "post", "status_code": 200, "latency_ms": 9.0, "library": "httpx",
    }
    if source is not None:
        e["source"] = source
    return e


def test_external_call_source_round_trips(fresh_store):
    _ls, store = fresh_store
    store.ingest_external_call(_ev("2026-06-02T00:00:00Z", "support-agent"))
    store.ingest_external_call(_ev("2026-06-02T00:00:01Z"))  # untagged
    rows = store.query_external_calls(limit=10)
    assert rows, "expected external_api_calls rows"
    assert all("source" in r for r in rows), "source column must be selected"
    tagged = [r for r in rows if r.get("source") == "support-agent"]
    assert len(tagged) == 1


def test_cost_fallback_prices_models_outside_local_table():
    # The interceptor's small _PRICING table predates models like o3 / grok /
    # gemini-2.5; out-loop cost must NOT silently read $0 for them — the
    # providers_pricing fallback returns a conservative non-zero estimate.
    for m in ("o3", "grok-2", "gemini-2.5-pro", "gpt-5"):
        c = I._estimate_cost(m, 1000, 500)
        assert c and c > 0, (m, c)
    # but a call with no tokens is still None (nothing to price)
    assert I._estimate_cost("o3", 0, 0) is None


def test_external_call_cost_round_trips(fresh_store):
    # llm_call events carry cost/tokens/model — the out-loop card's per-source
    # $ spend depends on these surviving ingest+query.
    _ls, store = fresh_store
    ev = _ev("2026-06-02T00:00:05Z", "billing-agent")
    ev.update({"cost_usd": 0.0123, "input_tokens": 400, "output_tokens": 120,
               "model": "claude-opus-4-8"})
    store.ingest_external_call(ev)
    row = next((r for r in store.query_external_calls(limit=10)
                if r.get("source") == "billing-agent"), None)
    assert row is not None
    assert abs(float(row.get("cost_usd") or 0) - 0.0123) < 1e-9
    assert int(row.get("input_tokens") or 0) == 400
    assert int(row.get("output_tokens") or 0) == 120
    assert row.get("model") == "claude-opus-4-8"


def test_external_calls_migration_is_idempotent(fresh_store):
    # Re-running the migration set (as happens on every store open) must not
    # fail on the ALTER ... ADD COLUMN IF NOT EXISTS source.
    ls, store = fresh_store
    store.ingest_external_call(_ev("2026-06-02T00:00:02Z", "agent-a"))
    # second open against the same file re-applies migrations
    store2 = ls.get_store()
    rows = store2.query_external_calls(limit=10)
    assert any(r.get("source") == "agent-a" for r in rows)


# ── 4. snapshot slice keeps source-tagged calls only ────────────────────────


def test_snapshot_external_calls_slice_filters_to_tagged(fresh_store, monkeypatch):
    _ls, store = fresh_store
    store.ingest_external_call(_ev("2026-06-02T00:00:03Z", "billing-agent"))
    store.ingest_external_call(_ev("2026-06-02T00:00:04Z"))  # untagged → excluded
    sys.modules.pop("clawmetry.sync", None)
    import clawmetry.sync as S
    out = S._build_external_calls()
    assert isinstance(out, list)
    assert all(c.get("source") for c in out), "slice must keep tagged calls only"
    assert any(c.get("source") == "billing-agent" for c in out)
