"""Session working-directory + git-branch capture.

Every runtime that writes a transcript records the directory the session ran
in (Claude Code stamps ``cwd`` / ``gitBranch`` on nearly every line), but no
session row ever carried them, so the sessions list read as a wall of UUIDs.

Covers:
  1. ingest_sessions_batch persists cwd / git_branch and query_sessions_table
     reads them back.
  2. Latest-non-NULL-wins — a re-ingest that omits the fields keeps what we
     already knew; one that carries new values moves the row (an agent that
     cd's or switches branch mid-session).
  3. update_session_location() sets ONLY those two columns. This is the
     regression that matters: the ingest upsert assigns status / ended_at /
     token / cost columns straight from ``excluded.*``, so doing this with a
     sparse ingest_session() would blank a live session's status and zero
     its cost.
  4. The runtime-agnostic alias extractors in sync.py, since each runtime
     spells the same two facts differently.
  5. The API exposes cwd / git_branch / project, with project being the
     human-facing label a first-time user actually reads.
"""

from __future__ import annotations

import importlib

import pytest


@pytest.fixture()
def store(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")
    import clawmetry.local_store as ls
    importlib.reload(ls)
    # Claim the writer, else get_store() hands back a _ProxyStore that
    # forwards to whatever daemon happens to be running on the dev machine —
    # the test would then write to the developer's real DuckDB and read back
    # nothing.
    ls.mark_writer_owner()
    return ls.get_store()


def _row(store, sid, agent_type="claude_code"):
    for r in store.query_sessions_table(limit=50):
        if r.get("session_id") == sid and r.get("agent_type") == agent_type:
            return r
    return None


# ── 1. round trip ───────────────────────────────────────────────────────────

def test_cwd_and_branch_round_trip(store):
    store.ingest_sessions_batch([{
        "agent_type": "claude_code",
        "session_id": "s-round-trip",
        "status": "active",
        "cwd": "/Users/dev/projects/clawmetry",
        "git_branch": "add-pro-readme",
    }])
    r = _row(store, "s-round-trip")
    assert r is not None
    assert r["cwd"] == "/Users/dev/projects/clawmetry"
    assert r["git_branch"] == "add-pro-readme"


def test_absent_location_is_none_not_empty_string(store):
    """None and '' must not both appear — the COALESCE contract depends on
    'not reported' being NULL, so a later real value can win."""
    store.ingest_sessions_batch([{
        "agent_type": "claude_code", "session_id": "s-none", "status": "active",
    }])
    r = _row(store, "s-none")
    assert r["cwd"] is None
    assert r["git_branch"] is None


def test_blank_string_is_stored_as_none(store):
    """A runtime that reports an empty cwd must not clobber a known value."""
    store.ingest_sessions_batch([{
        "agent_type": "claude_code", "session_id": "s-blank",
        "cwd": "/real/path", "git_branch": "main",
    }])
    store.ingest_sessions_batch([{
        "agent_type": "claude_code", "session_id": "s-blank",
        "cwd": "   ", "git_branch": "",
    }])
    r = _row(store, "s-blank")
    assert r["cwd"] == "/real/path"
    assert r["git_branch"] == "main"


# ── 2. latest-non-NULL-wins ─────────────────────────────────────────────────

def test_reingest_without_location_preserves_it(store):
    store.ingest_sessions_batch([{
        "agent_type": "claude_code", "session_id": "s-keep",
        "cwd": "/Users/dev/projects/api", "git_branch": "main",
    }])
    store.ingest_sessions_batch([{
        "agent_type": "claude_code", "session_id": "s-keep",
        "status": "ended", "total_tokens": 500,
    }])
    r = _row(store, "s-keep")
    assert r["cwd"] == "/Users/dev/projects/api"
    assert r["git_branch"] == "main"
    assert r["status"] == "ended"


def test_agent_that_switches_branch_moves_the_row(store):
    store.ingest_sessions_batch([{
        "agent_type": "claude_code", "session_id": "s-move",
        "cwd": "/p/one", "git_branch": "main",
    }])
    store.ingest_sessions_batch([{
        "agent_type": "claude_code", "session_id": "s-move",
        "cwd": "/p/two", "git_branch": "feature",
    }])
    r = _row(store, "s-move")
    assert r["cwd"] == "/p/two"
    assert r["git_branch"] == "feature"


# ── 3. the narrow update must not blank anything else ───────────────────────

def test_update_session_location_preserves_status_and_cost(store):
    """The regression this method exists to prevent."""
    store.ingest_sessions_batch([{
        "agent_type": "claude_code", "session_id": "s-live",
        "title": "Live work", "status": "active",
        "total_tokens": 12345, "cost_usd": 4.56, "message_count": 20,
    }])
    ok = store.update_session_location(
        "s-live", agent_type="claude_code",
        cwd="/Users/dev/projects/clawmetry", git_branch="main",
    )
    assert ok is True
    r = _row(store, "s-live")
    assert r["cwd"] == "/Users/dev/projects/clawmetry"
    assert r["git_branch"] == "main"
    # Nothing else moved.
    assert r["status"] == "active"
    assert r["title"] == "Live work"
    assert r["total_tokens"] == 12345
    assert r["cost_usd"] == pytest.approx(4.56)
    assert r["message_count"] == 20
    assert r["ended_at"] is None


def test_update_only_branch_leaves_cwd_alone(store):
    store.ingest_sessions_batch([{
        "agent_type": "claude_code", "session_id": "s-partial",
        "cwd": "/keep/me", "git_branch": "old",
    }])
    store.update_session_location(
        "s-partial", agent_type="claude_code", git_branch="new")
    r = _row(store, "s-partial")
    assert r["cwd"] == "/keep/me"
    assert r["git_branch"] == "new"


def test_update_is_noop_without_values(store):
    assert store.update_session_location("s-x", agent_type="claude_code") is False


def test_update_missing_session_does_not_raise(store):
    """Ingest loops must never die on a row that isn't there yet."""
    assert store.update_session_location(
        "no-such-session", agent_type="claude_code", cwd="/tmp") is True


def test_long_path_is_bounded(store):
    store.ingest_sessions_batch([{
        "agent_type": "claude_code", "session_id": "s-long",
        "cwd": "/" + ("a" * 5000),
    }])
    assert len(_row(store, "s-long")["cwd"]) <= 512


# ── 4. per-runtime alias extraction ─────────────────────────────────────────

@pytest.mark.parametrize("row,expected", [
    ({"cwd": "/a/b"},                          "/a/b"),   # Claude Code, Codex
    ({"workingDirectory": "/a/b"},             "/a/b"),
    ({"working_directory": "/a/b"},            "/a/b"),
    ({"workspace": "/a/b"},                    "/a/b"),
    ({"project_path": "/a/b"},                 "/a/b"),
    ({"metadata": {"cwd": "/a/b"}},            "/a/b"),   # nested one level
    ({"extra": {"workspace": "/a/b"}},         "/a/b"),
    ({},                                       None),
    ({"cwd": ""},                              None),
    ({"cwd": None},                            None),
    ({"cwd": {"not": "a string"}},             None),
])
def test_cwd_aliases(row, expected):
    from clawmetry.sync import _session_cwd
    assert _session_cwd(row) == expected


@pytest.mark.parametrize("row,expected", [
    ({"gitBranch": "main"},                    "main"),   # Claude Code
    ({"git_branch": "main"},                   "main"),
    ({"branch": "main"},                       "main"),
    ({"metadata": {"gitBranch": "main"}},      "main"),
    ({},                                       None),
    ({"gitBranch": ""},                        None),     # detached HEAD
])
def test_git_branch_aliases(row, expected):
    from clawmetry.sync import _session_git_branch
    assert _session_git_branch(row) == expected


def test_alias_extractors_tolerate_garbage():
    """Never crash on bad input — these run inside the ingest loop."""
    from clawmetry.sync import _session_cwd, _session_git_branch
    for junk in (None, [], "string", 42, {"metadata": "not-a-dict"}):
        assert _session_cwd(junk) is None
        assert _session_git_branch(junk) is None


# ── 5. the human-facing label ───────────────────────────────────────────────

@pytest.mark.parametrize("cwd,expected", [
    ("/Users/dev/projects/clawmetry",  "clawmetry"),
    ("/Users/dev/projects/clawmetry/", "clawmetry"),
    ("C:\\Users\\dev\\projects\\api",  "api"),
    ("/",                              ""),
    ("",                               ""),
    (None,                             ""),
])
def test_project_name(cwd, expected):
    from routes.sessions import _project_name
    assert _project_name(cwd) == expected
