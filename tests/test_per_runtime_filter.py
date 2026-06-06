"""Per-runtime scoping for the Overview cards (outcome tile + activity strip).

Regression guard: query_events / query_tool_call_invocations / query_outcomes
accept a ``runtime`` filter (session_id prefix, the canonical
_runtime_session_id_clause) so the cards re-scope with the runtime switcher
instead of showing identical node-wide numbers for every runtime.
Bug: the founder saw "3 tasks / 31 tool calls" identical across all/openclaw/codex.
"""
import os, uuid, importlib, tempfile


def _store(monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", tempfile.mktemp(suffix=".duckdb"))
    monkeypatch.setenv("CLAWMETRY_DUCKDB_THREADS", "2")
    import clawmetry.local_store as ls
    ls = importlib.reload(ls)
    return ls.LocalStore(read_only=False)


def _ev(store, session_id, etype="message"):
    store.ingest({
        "id": str(uuid.uuid4()), "node_id": "agent+test", "agent_id": "a",
        "agent_type": "openclaw", "session_id": session_id, "event_type": etype,
        "ts": "2099-01-01T00:00:00Z", "token_count": 1, "cost_usd": 0.0, "data": {},
    })
    store.flush()


def test_query_events_filters_by_runtime(monkeypatch):
    st = _store(monkeypatch)
    oc = str(uuid.uuid4())                 # bare UUID => openclaw
    cx = "codex:" + str(uuid.uuid4())      # codex prefix
    _ev(st, oc); _ev(st, oc); _ev(st, cx)
    alln = len(st.query_events(event_type="message", limit=100))
    ocn  = len(st.query_events(event_type="message", runtime="openclaw", limit=100))
    cxn  = len(st.query_events(event_type="message", runtime="codex", limit=100))
    assert alln == 3, alln
    assert ocn == 2, ocn
    assert cxn == 1, cxn
    # the bug was: every runtime returned the node-wide number
    assert ocn != alln and cxn != alln


def test_unknown_runtime_returns_nothing(monkeypatch):
    st = _store(monkeypatch)
    _ev(st, str(uuid.uuid4()))
    # an unknown runtime label must not leak the unfiltered total
    assert st.query_events(event_type="message", runtime="not_a_runtime", limit=100) == []
