"""Bridge tests: stored DuckDB event rows -> EvalInput (#2862 resurrected).

The module was pruned in #4436 as "unintegrated" because its extractor only
understood the in-memory adapter ``Event`` shape, never the rows
``LocalStore.query_events`` actually returns. These tests pin the bridge on
REAL stored shapes captured from a live claude_code session on 2026-08-03
(``data`` holds the Event fields; ``tool_calls``/``extra`` arrive as
Python-repr strings, not JSON), per the no-synthetic-shapes rule.
"""
from __future__ import annotations

import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from clawmetry.deterministic_evaluators import (  # noqa: E402
    eval_input_from_events,
    eval_input_from_stored_rows,
    run_checks,
    stored_row_to_event,
)


def _real_tool_call_row(ts="2026-08-03T12:00:01+00:00"):
    # Verbatim shape observed via the daemon proxy: tool_calls is a
    # PYTHON-REPR string (single quotes), and the same call also appears
    # as data.tool_name.
    return {
        "session_id": "claude_code:7e71",
        "event_type": "tool_call",
        "ts": ts,
        "data": {
            "_runtime": "claude_code",
            "content": "",
            "role": "assistant",
            "tool_calls": "[{'id': 'toolu_01Q4', 'input': {'command': 'cat x'}, 'name': 'Bash'}]",
            "tool_name": "Bash",
        },
    }


def _real_tool_result_row(is_error=False, ts="2026-08-03T12:00:02+00:00"):
    return {
        "session_id": "claude_code:7e71",
        "event_type": "tool_result",
        "ts": ts,
        "data": {
            "_runtime": "claude_code",
            "content": '{"port": 61248}',
            "extra": "{'isError': %s, 'toolUseId': 'toolu_01Q4'}" % is_error,
            "role": "tool",
        },
    }


def _real_message_row(content, ts="2026-08-03T12:00:03+00:00"):
    return {
        "session_id": "claude_code:7e71",
        "event_type": "message",
        "ts": ts,
        "data": {
            "_runtime": "claude_code",
            "content": content,
            "extra": "{'model': 'claude-fable-5'}",
            "role": "assistant",
        },
    }


def test_stored_row_to_event_revives_repr_strings():
    ev = stored_row_to_event(_real_tool_call_row())
    assert ev["type"] == "tool_call"
    assert isinstance(ev["tool_calls"], list) and len(ev["tool_calls"]) == 1
    assert ev["tool_calls"][0]["name"] == "Bash"
    assert ev["tool_calls"][0]["input"] == {"command": "cat x"}
    assert ev["tool_name"] == "Bash"


def test_stored_rows_no_double_count_and_arguments_mapped():
    """A real tool_call row carries BOTH data.tool_calls and data.tool_name;
    counting both made every call count twice (a 181-call session reported
    362). The bridge must yield exactly one call, with arguments taken from
    the entry's ``input``."""
    inp = eval_input_from_stored_rows([_real_tool_call_row()])
    assert len(inp.tool_calls) == 1
    assert inp.tool_calls[0]["name"] == "Bash"
    assert inp.tool_calls[0]["arguments"] == {"command": "cat x"}


def test_tool_name_fallback_still_works_without_call_list():
    """Events that only carry tool_name (no tool_calls list) keep working."""
    row = _real_tool_call_row()
    row["data"].pop("tool_calls")
    inp = eval_input_from_stored_rows([row])
    assert len(inp.tool_calls) == 1
    assert inp.tool_calls[0]["name"] == "Bash"


def test_error_flag_from_repr_extra():
    ok = eval_input_from_stored_rows([_real_tool_result_row(is_error=False)])
    assert ok.had_error is False
    bad = eval_input_from_stored_rows([_real_tool_result_row(is_error=True)])
    assert bad.had_error is True


def test_output_text_is_latest_despite_newest_first_rows():
    """query_events returns newest-first; the bridge must sort by ts so the
    LAST reply wins, not the first row it sees."""
    rows = [
        _real_message_row("final answer", ts="2026-08-03T12:00:09+00:00"),
        _real_message_row("first draft", ts="2026-08-03T12:00:03+00:00"),
    ]
    inp = eval_input_from_stored_rows(rows)
    assert inp.output_text == "final answer"


def test_bridge_feeds_run_checks_end_to_end():
    rows = [
        _real_tool_call_row(),
        _real_tool_result_row(is_error=False),
        _real_message_row("done"),
    ]
    inp = eval_input_from_stored_rows(rows)
    results = run_checks(inp, [{"slug": "no-tool-errors"}])
    assert len(results) == 1
    assert results[0].passed is True and results[0].score == 1.0


def test_bridge_never_raises_on_garbage():
    garbage = [
        None,
        "not a row",
        {"event_type": "tool_call", "data": "totally }{ unparseable"},
        {"event_type": "tool_call", "data": {"tool_calls": "[unclosed"}},
        {},
    ]
    inp = eval_input_from_stored_rows(garbage)  # must not raise
    assert inp.tool_calls == []


def test_adapter_event_shape_unchanged():
    """The original adapter-Event path (dicts with top-level type/content/
    tool_calls) still extracts — the bridge is additive."""
    inp = eval_input_from_events([
        {"type": "message", "content": "hi",
         "tool_calls": [{"name": "web", "arguments": {"q": "x"}}]},
    ])
    assert inp.output_text == "hi"
    assert inp.tool_calls == [{"name": "web", "arguments": {"q": "x"}}]
