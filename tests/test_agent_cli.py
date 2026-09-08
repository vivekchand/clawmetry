"""Agent CLI Phase 1 (docs/CLI.md) regression tests.

Covers:
  * the family-adapter ``data.tool_calls[*]`` extractor fix in
    clawmetry/local_store.py (the `clawmetry waste` == 0 bug: family
    Read calls were invisible to all three ``_iter_*`` tool extractors)
  * the CLI exit-code contract (0 ok / 3 no source / 4 entitlement /
    6 not found) and the --json output shapes
  * the --follow NDJSON frame contract (_meta first, _end last, resume
    cursor)

Hermetic: a FakeStore stands in for the daemon proxy — no DuckDB, no
server. The extractor tests import clawmetry.local_store directly (pure
functions).
"""
from __future__ import annotations

import json

import pytest

from clawmetry.cli_cmds import dispatch
from clawmetry.cli_cmds import _common
from clawmetry.local_store import (
    _iter_read_tool_paths,
    _iter_tool_file_paths,
    _iter_tool_invocation_names,
)


# ── The family tool_calls[*] shape (claude_code / codex / cursor …) ────────

FAMILY_TOOL_CALL_EVENT = {
    "_runtime": "claude_code",
    "content": "",
    "role": "assistant",
    "tool_name": "Read",
    "tool_calls": [
        {
            "id": "toolu_01",
            "name": "Read",
            "input": {"file_path": "/repo/routes/sessions.py"},
        },
        {
            "id": "toolu_02",
            "name": "Bash",
            "input": {"command": "ls"},
        },
    ],
}


def test_read_paths_extracted_from_family_tool_calls():
    # Un-fixed code yields [] here (shape-1 set lacked 'tool_call' and nobody
    # walked data.tool_calls) — the `clawmetry waste` == 0 regression.
    paths = list(_iter_read_tool_paths("tool_call", FAMILY_TOOL_CALL_EVENT))
    assert paths == ["/repo/routes/sessions.py"]


def test_tool_file_paths_extracted_from_family_tool_calls():
    paths = list(_iter_tool_file_paths("tool_call", FAMILY_TOOL_CALL_EVENT))
    assert "/repo/routes/sessions.py" in paths


def test_invocation_names_count_every_family_block():
    names = list(_iter_tool_invocation_names("tool_call", FAMILY_TOOL_CALL_EVENT))
    # tool_name names the first block; the Bash block must ALSO count.
    assert "Read" in names and "Bash" in names


def test_legacy_shapes_still_extract():
    # Guard the pre-existing shapes against regression by the family fix.
    top_level = {"name": "Read", "input": {"file_path": "/a.py"}}
    assert list(_iter_read_tool_paths("tool.call", top_level)) == ["/a.py"]
    metas = {"toolMetas": [{"name": "read_file", "input": {"path": "/b.py"}}]}
    assert list(_iter_read_tool_paths("assistant", metas)) == ["/b.py"]


# ── CLI harness ─────────────────────────────────────────────────────────────

class FakeStore:
    """Read-only stand-in for the daemon proxy store."""

    def __init__(self):
        self.sessions = [
            {
                "session_id": "claude_code:abc123",
                "agent_type": "openclaw",
                "status": "active",
                "title": "fix the tests",
                "total_tokens": 1000,
                "cost_usd": 0.5,
                "last_active_at": "2099-01-01T00:00:00Z",
            },
            {
                "session_id": "openclaw-uuid-1",
                "agent_type": "openclaw",
                "status": "ended",
                "title": "telegram chat",
                "total_tokens": 200,
                "cost_usd": 0.1,
                "last_active_at": "2099-01-01T00:00:00Z",
            },
        ]

    def query_sessions_table(self, *, limit=200, **kw):
        return self.sessions[:limit]

    def query_events(self, **kw):
        return []

    def query_recent_read_tool_calls(self, **kw):
        return [
            {"ts": "t1", "session_id": "claude_code:abc123", "file_path": "/x.py"},
            {"ts": "t2", "session_id": "claude_code:abc123", "file_path": "/x.py"},
            {"ts": "t3", "session_id": "claude_code:abc123", "file_path": "/y.py"},
        ]

    def query_forward_progress(self, **kw):
        return [{"session_id": "claude_code:abc123", "tokens": 5000,
                 "state_deltas": 1, "ratio": 5000.0}]

    def query_recent_loop_signals(self, **kw):
        return []

    def query_aggregates(self, **kw):
        return [{"day": "2099-01-01", "token_count": 42, "cost_usd": 1.5,
                 "event_count": 7, "agent_id": "main"}]


@pytest.fixture
def fake_store(monkeypatch):
    store = FakeStore()
    monkeypatch.setattr(_common, "get_read_store", lambda: (store, "daemon"))
    return store


def run_cli(argv, capsys):
    code = dispatch(argv)
    out = capsys.readouterr()
    return code, out.out, out.err


# ── Exit codes + shapes ─────────────────────────────────────────────────────

def test_sessions_json_shape(fake_store, capsys):
    code, out, _err = run_cli(["sessions", "--json"], capsys)
    assert code == 0
    payload = json.loads(out)
    assert payload["source"] == "daemon"
    assert payload["sessions"][0]["session_id"] == "claude_code:abc123"


def test_sessions_runtime_filter_uses_prefix_not_agent_type(fake_store, capsys):
    # agent_type is 'openclaw' for BOTH rows; the claude_code row must be
    # selected by its session-id prefix (the _runtime_of_session rule).
    code, out, _ = run_cli(["sessions", "--runtime", "claude_code", "--json"], capsys)
    assert code == 0
    rows = json.loads(out)["sessions"]
    assert [r["session_id"] for r in rows] == ["claude_code:abc123"]
    code, out, _ = run_cli(["sessions", "--runtime", "openclaw", "--json"], capsys)
    assert [r["session_id"] for r in json.loads(out)["sessions"]] == ["openclaw-uuid-1"]


def test_unknown_session_exits_6(fake_store, capsys):
    code, _out, err = run_cli(["sessions", "nope-such-id"], capsys)
    assert code == _common.EXIT_NOT_FOUND
    assert "not_found" in err


def test_no_data_source_exits_3(monkeypatch, capsys):
    def boom():
        raise _common.CliError("unavailable", "no store", _common.EXIT_UNAVAILABLE)
    monkeypatch.setattr(_common, "get_read_store", boom)
    code, _out, err = run_cli(["sessions"], capsys)
    assert code == _common.EXIT_UNAVAILABLE
    assert "unavailable" in err


def test_selfevolve_stub_exits_4_with_upgrade_body(monkeypatch, capsys):
    # Force the un-entitled path regardless of the dev machine's license.
    from clawmetry.cli_cmds import selfevolve as se
    monkeypatch.setattr(se, "_allowed", lambda: False)
    monkeypatch.setattr(se, "_pro_impl", lambda: None)
    monkeypatch.setattr(se, "_record_paywall_event", lambda action: None)
    code, _out, err = run_cli(["selfevolve", "fix"], capsys)
    assert code == _common.EXIT_ENTITLEMENT
    body = json.loads(err.splitlines()[-1])
    assert body["error"]["code"] == "upgrade_required"
    assert body["error"]["feature"] == "self_evolve"
    assert body["error"]["upgrade_url"].startswith("https://clawmetry.com/upgrade")


def test_waste_counts_rereads(fake_store, capsys):
    code, out, _ = run_cli(["waste", "--json"], capsys)
    assert code == 0
    payload = json.loads(out)
    assert payload["total_reads"] == 3
    assert payload["wasted_reads"] == 1  # /x.py read twice
    assert payload["top"][0]["file_path"] == "/x.py"


def test_usage_totals_use_token_count_key(fake_store, capsys):
    # Regression: query_aggregates rows carry token_count (not tokens);
    # the totals rendered 0 until the key was fixed.
    code, out, _ = run_cli(["usage", "--json"], capsys)
    assert code == 0
    payload = json.loads(out)
    assert payload["total_tokens"] == 42
    assert payload["total_cost_usd"] == 1.5


def test_progress_json(fake_store, capsys):
    code, out, _ = run_cli(["progress", "--json"], capsys)
    assert code == 0
    payload = json.loads(out)
    assert payload["sessions"][0]["ratio"] == 5000.0
    assert payload["loop_signals"] == []


def test_stdout_is_awk_safe(fake_store, capsys):
    # Human output: data on stdout, decoration on stderr.
    code, out, err = run_cli(["sessions"], capsys)
    assert code == 0
    assert "session(s)" in err and "session(s)" not in out
    header = out.splitlines()[0]
    assert header.split()[0] == "SESSION"


# ── --follow frame contract ─────────────────────────────────────────────────

def test_follow_emits_meta_and_end_frames(fake_store, monkeypatch, capsys):
    events = [{"ts": "2099-01-01T00:00:01Z", "session_id": "s", "event_type": "x",
               "data": {}}]
    monkeypatch.setattr(FakeStore, "query_events", lambda self, **kw: list(events))
    code, out, _ = run_cli(
        ["activity", "--follow", "--max-events", "1", "--idle-timeout", "5"],
        capsys,
    )
    assert code == 0
    lines = [json.loads(line) for line in out.splitlines()]
    assert lines[0]["type"] == "_meta"
    assert lines[0]["source"] == "daemon"
    assert lines[-1]["type"] == "_end"
    assert lines[-1]["reason"] == "max_events"
    assert lines[-1]["next_cursor"] == "2099-01-01T00:00:01Z"


# ── parse_when ──────────────────────────────────────────────────────────────

def test_parse_when_relative_and_iso():
    iso = _common.parse_when("2026-07-31T00:00:00Z")
    assert iso == "2026-07-31T00:00:00Z"
    rel = _common.parse_when("15m")
    assert rel.endswith("Z") and rel != iso
    with pytest.raises(_common.CliError):
        _common.parse_when("next tuesday")
