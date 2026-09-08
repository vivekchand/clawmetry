"""A blowout count of zero must never be ambiguous.

"Compactions: 0" is two different statements wearing the same clothes: the
runtime ran clean, or we cannot see compactions on that runtime at all.
ClawMetry emits compaction events for a minority of its adapters, so for most
runtimes the second reading is the true one — and rendering it as the first
tells a user their Codex sessions never blow out when we were never going to
know either way.

These tests pin the three-verdict vocabulary, the rule that observation beats
declaration, and the end-to-end coverage query.
"""

from __future__ import annotations

import importlib

import pytest

from clawmetry import context_coverage as cc


# ── verdict vocabulary ───────────────────────────────────────────────────

def test_zero_on_a_blind_runtime_is_unsupported_not_a_clean_bill():
    """The core regression. Codex emits no compaction event, so 0 means
    blind."""
    assert cc.verdict("codex", "compaction", 0) == "unsupported"
    note = cc.explain("codex", "compaction", "unsupported")
    assert "cannot see" in note


def test_zero_on_a_capable_runtime_is_a_real_zero():
    assert cc.verdict("openclaw", "compaction", 0) == "supported_none_seen"
    assert cc.explain("openclaw", "compaction", "supported_none_seen") == ""


def test_observation_overrides_the_denylist():
    """If the data says a runtime reports compactions, it does — whatever
    this module believes. That ordering is what stops a stale denylist from
    hiding real user data."""
    assert cc.verdict("codex", "compaction", 7) == "observed"


def test_unknown_runtime_is_assumed_capable():
    """Failure lands on the cautious side: an unrecognised runtime reports an
    honest 'nothing seen' rather than claiming we are blind to it."""
    assert cc.verdict("brand-new-harness", "compaction", 0) == "supported_none_seen"


def test_runtimes_without_token_counts_cannot_report_utilization():
    """Cursor's tokens live behind a proprietary backend and picoclaw writes
    no usage envelope — documented in sync.sync_vm_usage_log."""
    for rt in ("cursor", "picoclaw"):
        assert cc.verdict(rt, "utilization", 0) == "unsupported"


def test_overflow_is_runtime_agnostic():
    """Overflow is read out of provider error text, not an adapter feature,
    so no runtime is declared blind to it."""
    for rt in ("codex", "cursor", "openclaw", "anything"):
        assert cc.verdict(rt, "overflow", 0) == "supported_none_seen"


def test_summarise_counts_partial_observability():
    rows = [
        {s: {"verdict": "observed"} for s in cc.SIGNALS} | {"runtime": "openclaw"},
        {**{s: {"verdict": "observed"} for s in cc.SIGNALS},
         "compaction": {"verdict": "unsupported"}, "runtime": "codex"},
    ]
    out = cc.summarise(rows)
    assert out["runtimes"] == 2
    assert out["fully_observable"] == 1
    assert out["partially_observable"] == 1


# ── end to end over a real store ─────────────────────────────────────────

@pytest.fixture
def store(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    import clawmetry.local_store as ls
    importlib.reload(ls)
    ls.mark_writer_owner()
    return ls.get_store()


def _turn(i, sid, model="claude-opus-4-7", tokens=150_000):
    return {
        "id": f"cov-{sid}-{i}", "node_id": "n", "agent_id": "main",
        "session_id": sid, "event_type": "assistant",
        "ts": f"2026-08-25T10:{i % 60:02d}:00.000Z",
        "data": {"type": "assistant", "message": {
            "role": "assistant", "model": model,
            "usage": {"input_tokens": tokens, "output_tokens": 10}}},
    }


def test_coverage_distinguishes_blind_from_clean(store):
    rows = [_turn(i, "codex:sess-a", model="gpt-5-codex") for i in range(4)]
    oc = "11111111-2222-3333-4444-555555555555"
    rows += [_turn(i, oc) for i in range(4, 8)]
    rows.append({
        "id": "cov-comp", "node_id": "n", "agent_id": "main", "session_id": oc,
        "event_type": "compaction", "ts": "2026-08-25T10:30:00.000Z",
        "data": {"type": "compaction", "error": "prompt is too long"},
    })
    store.ingest_many(rows)
    store.flush()

    by_rt = {r["runtime"]: r for r in store.query_context_coverage()["runtimes"]}

    # Codex reports tokens, so utilization is real...
    assert by_rt["codex"]["utilization"]["verdict"] == "observed"
    # ...but its zero compactions are a blind spot, not a clean run.
    assert by_rt["codex"]["compaction"]["verdict"] == "unsupported"
    assert by_rt["codex"]["compaction"]["count"] == 0

    # OpenClaw genuinely reported one, including its overflow marker.
    assert by_rt["openclaw"]["compaction"]["verdict"] == "observed"
    assert by_rt["openclaw"]["overflow"]["count"] == 1


def test_absent_runtimes_are_omitted_not_zero_padded(store):
    store.ingest_many([_turn(0, "codex:only")])
    store.flush()
    names = {r["runtime"] for r in store.query_context_coverage()["runtimes"]}
    assert names == {"codex"}


def test_empty_store_returns_empty_rows_without_raising(store):
    out = store.query_context_coverage()
    assert out["runtimes"] == []
    assert out["summary"]["runtimes"] == 0
