"""Golden-fixture tests for the q/1 query contract (issue #2987).

A deterministic seed corpus is written into a fresh temp DuckDB via the
real ``LocalStore`` API, every LIVE contract method is run through
``routes.local_query._dispatch`` (the same shape->store bridge the HTTP
API and the cloud relay share), and the normalized JSON output is
compared against committed goldens in ``tests/fixtures/query_contract/``.

Volatile fields (``_elapsed_ms``, ``_via``, store-health size/paths) are
replaced with the placeholder ``"<volatile>"`` so key PRESENCE is still
pinned while values that legitimately churn are not.

Regenerating goldens (deliberate contract evolution only):

    CLAWMETRY_REGEN_GOLDENS=1 python3 -m pytest tests/test_query_contract_goldens.py

then review + commit the diff under tests/fixtures/query_contract/.
"""

from __future__ import annotations

import copy
import importlib
import json
import os
import pathlib
import time

import pytest

GOLDEN_DIR = pathlib.Path(__file__).parent / "fixtures" / "query_contract"
REGEN = os.environ.get("CLAWMETRY_REGEN_GOLDENS") == "1"

# Fixed args per live method (deterministic dispatch inputs).
DISPATCH_ARGS = {
    "events": {},
    "sessions": {},
    "aggregates": {},
    "health": {},
    "transcript": {"session_id": "sess-a"},
    "spans": {},
    "traces": {},
    "external_calls": {},
    "search": {"q": "alpha"},
    # #2988 (Query Spine P2): materialized-rollup backed methods.
    "models": {},
    "runtimes": {},
    "rollup_sessions": {},
    # #1012: cross-session agent spawn topology (plaintext-classed stats only).
    "agent_graph": {},
}

# health() fields that legitimately vary run-to-run / machine-to-machine.
_HEALTH_VOLATILE = {
    "db_path", "size_bytes", "size_mb", "size_cap_bytes", "cap_exceeded",
    "auto_vacuum_enabled", "ring_depth", "ring_max", "ring_dropped_total",
    "schema_version", "last_flush_ago_s", "sync_dlq_depth",
}


@pytest.fixture
def seeded(tmp_path, monkeypatch):
    """Fresh isolated LocalStore + routes.local_query with the seed corpus."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import routes.local_query as lq
    importlib.reload(lq)

    # Isolate from any running daemon on the contributor's machine
    # (same pattern as tests/test_local_query_api.py, issue #1538).
    # Also force single-process writer mode: with a real daemon running,
    # local_store.get_store() would hand back a _ProxyStore that forwards
    # to the daemon's PRODUCTION DuckDB instead of this tmp_path fixture.
    monkeypatch.setattr(lq, "_read_discovery", lambda: None)
    monkeypatch.setattr(ls, "_daemon_registered", lambda: False)
    monkeypatch.delenv("CLAWMETRY_ROLE", raising=False)

    store = ls.get_store()

    # -- seed corpus: events (ring-buffered ingest) --------------------------
    def _ev(i, **over):
        base = {
            "id": f"ev-{i:03d}",
            "node_id": "agent+golden",
            "agent_id": "main",
            "session_id": "sess-a",
            "event_type": "tool_call",
            "ts": f"2026-01-02T10:00:{i:02d}Z",
            "data": {"tool": "Bash", "seq": i},
            "cost_usd": 0.001 * (i + 1),
            "token_count": 10 * (i + 1),
            "model": "claude-opus-4-7",
        }
        base.update(over)
        return base

    store.ingest(_ev(0))
    store.ingest(_ev(1, event_type="message", data={"text": "golden alpha"}))
    store.ingest(_ev(2))
    store.ingest(_ev(3, session_id="sess-b", agent_id="worker",
                     model="claude-haiku-4-5"))

    # -- sessions table (search backing) ------------------------------------
    store.ingest_session({
        "session_id": "sess-a", "agent_type": "openclaw",
        "node_id": "agent+golden", "title": "golden alpha refactor",
        "started_at": "2026-01-02T10:00:00Z",
        "last_active_at": "2026-01-02T10:00:02Z",
        "status": "active", "total_tokens": 60, "cost_usd": 0.006,
        "message_count": 3,
    })
    store.ingest_session({
        "session_id": "sess-b", "agent_type": "openclaw",
        "node_id": "agent+golden", "title": "beta cleanup",
        "started_at": "2026-01-02T10:00:03Z",
        "last_active_at": "2026-01-02T10:00:03Z",
        "status": "ended", "total_tokens": 40, "cost_usd": 0.004,
        "message_count": 1,
    })

    # -- spans (direct write) -----------------------------------------------
    base_ts = 1767348000.0  # fixed unix seconds
    store.put_span({
        "span_id": "sp-001", "trace_id": "tr-001", "name": "llm_call",
        "session_id": "sess-a", "agent_type": "openclaw",
        "start_ts": base_ts, "end_ts": base_ts + 1.5,
        "model": "claude-opus-4-7", "cost_usd": 0.002,
        "tokens_input": 100, "tokens_output": 20, "status": "OK",
    })
    store.put_span({
        "span_id": "sp-002", "trace_id": "tr-001", "name": "tool_call",
        "parent_span_id": "sp-001", "session_id": "sess-a",
        "agent_type": "openclaw", "tool_name": "Bash",
        "start_ts": base_ts + 0.5, "end_ts": base_ts + 1.0, "status": "OK",
    })
    store.put_span({
        "span_id": "sp-003", "trace_id": "tr-002", "name": "llm_call",
        "session_id": "sess-b", "agent_type": "openclaw",
        "start_ts": base_ts + 10.0, "end_ts": base_ts + 11.0,
        "model": "claude-haiku-4-5", "cost_usd": 0.001,
        "tokens_input": 50, "tokens_output": 10, "status": "ERROR",
    })

    # -- external API calls (direct write) ----------------------------------
    store.ingest_external_call({
        "ts": "2026-01-02T10:00:01Z", "host": "api.github.com",
        "url": "https://api.github.com/repos/x/y", "method": "get",
        "status_code": 200, "latency_ms": 120.0, "library": "requests",
        "source": "interceptor",
    }, node_id="agent+golden")
    store.ingest_external_call({
        "ts": "2026-01-02T10:00:02Z", "host": "example.com",
        "url": "https://example.com/hook", "method": "post",
        "status_code": 500, "latency_ms": 45.5, "library": "httpx",
        "source": "interceptor",
    }, node_id="agent+golden")

    # Wait for the ring buffer to flush the 4 events.
    deadline = time.monotonic() + 5.0
    while time.monotonic() < deadline:
        if store.health()["ring_depth"] == 0:
            break
        time.sleep(0.02)

    yield lq
    try:
        store.stop(flush=True)
    except Exception:
        pass


def _normalize(method: str, body: dict) -> dict:
    body = copy.deepcopy(body)
    for k in ("_elapsed_ms", "_via"):
        if k in body:
            body[k] = "<volatile>"
    if method == "health":
        for k in _HEALTH_VOLATILE:
            if k in body:
                body[k] = "<volatile>"
    for row in body.get("rows") or []:
        if isinstance(row, dict):
            for k in ("created_at", "updated_at", "ingested_at"):
                if k in row:
                    row[k] = "<volatile>"
    # aggregates GROUP BYs (day, agent_id) but only ORDER BYs day, so row
    # order within a day is engine-nondeterministic. Intra-day order is not
    # part of the q/1 contract; canonicalize it for stable goldens.
    if method == "aggregates" and isinstance(body.get("rows"), list):
        body["rows"] = sorted(
            body["rows"],
            key=lambda r: json.dumps(r, sort_keys=True, default=str),
        )
    return body


def test_live_methods_match_goldens(seeded):
    from clawmetry.query_contract import QUERY_CONTRACT, STATUS_LIVE

    live = sorted(n for n, s in QUERY_CONTRACT.items()
                  if s["status"] == STATUS_LIVE)
    # Every live method must have fixed dispatch args declared here, so
    # a newly-lit method cannot ship without a golden.
    assert set(live) == set(DISPATCH_ARGS), (
        "DISPATCH_ARGS in this test must cover exactly the live contract "
        f"methods. live={live} declared={sorted(DISPATCH_ARGS)}"
    )

    GOLDEN_DIR.mkdir(parents=True, exist_ok=True)
    failures = []
    for method in live:
        body = seeded._dispatch(method, dict(DISPATCH_ARGS[method]))
        got = _normalize(method, body)
        path = GOLDEN_DIR / f"{method}.json"
        if REGEN:
            path.write_text(json.dumps(got, indent=2, sort_keys=True) + "\n")
            continue
        assert path.exists(), (
            f"missing golden {path}. Regenerate deliberately with "
            "CLAWMETRY_REGEN_GOLDENS=1 pytest tests/test_query_contract_goldens.py"
        )
        want = json.loads(path.read_text())
        if got != want:
            failures.append(method)
            print(f"\n=== golden mismatch: {method} ===")
            print("want:", json.dumps(want, indent=2, sort_keys=True)[:2000])
            print("got: ", json.dumps(got, indent=2, sort_keys=True)[:2000])
    if REGEN:
        pytest.skip("goldens regenerated; review + commit the diff")
    assert not failures, f"golden drift in methods: {failures}"


def test_goldens_are_deterministic_sanity(seeded):
    """Two dispatches over the same corpus normalize identically -- guards
    against accidentally pinning a volatile field into the goldens."""
    a = _normalize("sessions", seeded._dispatch("sessions", {}))
    b = _normalize("sessions", seeded._dispatch("sessions", {}))
    assert a == b
    ha = _normalize("health", seeded._dispatch("health", {}))
    hb = _normalize("health", seeded._dispatch("health", {}))
    assert ha == hb
