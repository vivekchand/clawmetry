"""Guard: ``rollup_session.runtime`` is the runtime, not ``openclaw`` for all.

Family sessions (Claude Code, Codex, Cursor, …) are written to the ``sessions``
table with ``agent_type='openclaw'`` **by construction** — that column predates
multi-runtime and several readers still filter on it, so the family ingest path
in ``sync`` sets it literally. The runtime lives authoritatively in the
``<runtime>:<uuid>`` session-id prefix, which is what ``query_model_rollup``,
``query_recent_sessions_by_runtime`` and ``_runtime_session_id_clause`` all key
on.

``_mirror_session_rollups_locked`` wrote ``rollup_session.runtime`` from
``agent_type`` instead. Measured on a real node before this fix:

    rollup_session   188 rows, runtime='openclaw'  188   (every other: 0)
    sessions         161 rows, agent_type='openclaw' 161
                     session-id prefixes: claude_code 61, cursor 21,
                     copilot 13, opencode 12, goose 11, codex 10, pi 9, …

Two consequences, both silent:

* ``query_rollup_sessions(runtime="codex")`` returns nothing — the per-runtime
  read of the materialized table cannot see a single paid-runtime session.
* ``query_usage_by_team`` joins ``tm.key_value = rs.runtime``, so a mapping of
  ``claude_code -> Eng Team`` never matches and all spend lands under one
  ``openclaw`` label. Per-team cost attribution (#3000) is wrong for every
  paid runtime.

Nothing caught it because every other surface derives the runtime from the id
prefix, so only this table disagreed.
"""
from __future__ import annotations

import importlib

import pytest


def _fresh_store_module(tmp_path, monkeypatch, name="rollup.duckdb"):
    """Reload clawmetry.local_store against an isolated scratch DuckDB."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / name))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "999")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "1000")
    import clawmetry.local_store as ls
    importlib.reload(ls)
    return ls


@pytest.fixture
def store(tmp_path, monkeypatch):
    ls = _fresh_store_module(tmp_path, monkeypatch)
    s = ls.LocalStore()
    yield s
    s.stop(flush=True)


def _family_session(runtime: str, uid: str, **over):
    """A family session row exactly as ``sync`` writes it: the runtime is in the
    id prefix and ``agent_type`` is the literal 'openclaw'."""
    row = {
        "agent_type": "openclaw",
        "session_id": f"{runtime}:{uid}",
        "node_id": "node-a",
        "agent_id": "main",
        "title": f"{runtime} session",
        "started_at": "2026-09-01T10:00:00Z",
        "last_active_at": "2026-09-01T11:00:00Z",
        "status": "ended",
        "total_tokens": 1000,
        "cost_usd": 1.25,
        "message_count": 4,
    }
    row.update(over)
    return row


_RUNTIMES = ["claude_code", "codex", "cursor", "goose", "opencode"]


def test_family_session_is_filed_under_its_own_runtime(store):
    for i, rt in enumerate(_RUNTIMES):
        store.ingest_session(_family_session(rt, f"uuid-{i}"))

    for rt in _RUNTIMES:
        rows = store.query_rollup_sessions(runtime=rt, limit=100)
        assert rows, (
            f"rollup_session has no rows for runtime={rt!r}. Family sessions "
            f"carry agent_type='openclaw' by construction, so deriving the "
            f"rollup runtime from that column files every paid runtime under "
            f"'openclaw' and the per-runtime read returns nothing."
        )
        assert {r["runtime"] for r in rows} == {rt}


def test_openclaw_sessions_stay_openclaw(store):
    """A genuine OpenClaw session has no runtime prefix and must not be
    reattributed. A colon in the id is not by itself a runtime prefix."""
    store.ingest_session(_family_session("", "plain", session_id="plain-uuid"))
    store.ingest_session(
        _family_session("", "colon", session_id="not_a_runtime:xyz")
    )
    rows = store.query_rollup_sessions(runtime="openclaw", limit=100)
    got = {r["session_id"] for r in rows}
    assert got == {"plain-uuid", "not_a_runtime:xyz"}, (
        f"OpenClaw sessions were reattributed: {got}"
    )


def test_per_team_rollup_can_map_a_paid_runtime(store):
    """The user-visible consequence: team mapping joins on
    ``rollup_session.runtime``, so a claude_code -> team mapping must match."""
    store.ingest_session(_family_session("claude_code", "team-uuid"))
    store.upsert_team_mapping("runtime", "claude_code", "Eng Team")

    rows = store.query_usage_by_team(window_days=3650)
    labels = {r["label"] for r in rows}
    assert "Eng Team" in labels, (
        f"team mapping runtime=claude_code did not match any rollup_session "
        f"row; labels were {labels}. The join is "
        f"tm.key_value = rs.runtime, so a runtime column stuck on 'openclaw' "
        f"silently drops every per-team attribution."
    )
