"""Tests for #3698 — NemoClaw advisor-session JSONL ingestion via openshell.

sync_sandbox_sessions_openshell() must scan agents/advisor/sessions alongside
agents/main/sessions so LLM-consuming advisor/analysis sessions (tool calls,
retry outcomes) are visible in ClawMetry.
"""
import json
from unittest.mock import MagicMock, patch

from clawmetry.sync import sync_sandbox_sessions_openshell

CONFIG = {"api_key": "ak", "encryption_key": None, "node_id": "n1"}


def _run(returncode=0, stdout=""):
    r = MagicMock()
    r.returncode = returncode
    r.stdout = stdout
    return r


def _advisor_event(session_id, event_type, extra=None):
    ev = {"id": f"{session_id}-{event_type}", "sessionId": session_id,
          "type": event_type}
    if extra:
        ev.update(extra)
    return json.dumps(ev)


def test_advisor_sessions_ingested_when_present():
    """JSONL in agents/advisor/sessions must reach _flush_session_batch."""
    sandbox_list = json.dumps([{"name": "sb"}])
    advisor_line = _advisor_event("adv-sess-1", "tool_execution_start",
                                  {"attemptNumber": 1})

    side_effects = [
        _run(0, sandbox_list),
        _run(1, ""),                   # ls agents/main/sessions (absent)
        _run(0, "adv-sess-1.jsonl\n"), # ls agents/advisor/sessions
        _run(0, advisor_line + "\n"),  # cat advisor/adv-sess-1.jsonl
    ]

    flushed = []
    with patch("clawmetry.sync._find_openshell_bin", return_value="/usr/bin/openshell"), \
         patch("subprocess.run", side_effect=side_effects), \
         patch("clawmetry.sync._flush_session_batch",
               side_effect=lambda b, *a, **k: flushed.extend(b)):
        count = sync_sandbox_sessions_openshell(CONFIG, {})

    assert count == 1
    assert len(flushed) == 1
    assert flushed[0].get("_nemo_agent_dir") == "advisor"


def test_advisor_sessions_tagged_nemoclaw():
    """Advisor sessions must land with agent_type='nemoclaw'."""
    sandbox_list = json.dumps([{"name": "sb"}])
    advisor_line = _advisor_event("adv-sess-2", "tool_execution_end",
                                  {"isError": False, "retryResponse": "success"})

    side_effects = [
        _run(0, sandbox_list),
        _run(1, ""),
        _run(0, "adv-sess-2.jsonl\n"),
        _run(0, advisor_line + "\n"),
    ]

    flush_kwargs = []
    with patch("clawmetry.sync._find_openshell_bin", return_value="/usr/bin/openshell"), \
         patch("subprocess.run", side_effect=side_effects), \
         patch("clawmetry.sync._flush_session_batch",
               side_effect=lambda b, *a, **k: flush_kwargs.append(k)):
        sync_sandbox_sessions_openshell(CONFIG, {})

    assert flush_kwargs, "flush was never called"
    assert flush_kwargs[0].get("agent_type") == "nemoclaw"


def test_advisor_cursor_namespaced_separately_from_main():
    """Cursor keys for advisor sessions must be distinct from main keys."""
    sandbox_list = json.dumps([{"name": "sb"}])
    main_line = json.dumps({"id": "m1", "type": "message"})
    adv_line = _advisor_event("adv-sess-3", "tool_execution_start")

    side_effects = [
        _run(0, sandbox_list),
        _run(0, "sess.jsonl\n"),      # ls agents/main/sessions
        _run(0, main_line + "\n"),     # cat main/sess.jsonl
        _run(0, "sess.jsonl\n"),      # ls agents/advisor/sessions (same filename)
        _run(0, adv_line + "\n"),      # cat advisor/sess.jsonl
    ]

    state = {}
    with patch("clawmetry.sync._find_openshell_bin", return_value="/usr/bin/openshell"), \
         patch("subprocess.run", side_effect=side_effects), \
         patch("clawmetry.sync._flush_session_batch"):
        sync_sandbox_sessions_openshell(CONFIG, state)

    cursors = state["sandbox_session_cursors"]
    assert "sb/main/sess.jsonl" in cursors
    assert "sb/advisor/sess.jsonl" in cursors
    assert cursors["sb/main/sess.jsonl"] == 1
    assert cursors["sb/advisor/sess.jsonl"] == 1


def test_main_events_not_stamped_with_agent_dir():
    """Regular main sessions must not gain _nemo_agent_dir."""
    sandbox_list = json.dumps([{"name": "sb"}])
    main_line = json.dumps({"id": "m2", "type": "message"})

    side_effects = [
        _run(0, sandbox_list),
        _run(0, "main.jsonl\n"),
        _run(0, main_line + "\n"),
        _run(1, ""),
    ]

    flushed = []
    with patch("clawmetry.sync._find_openshell_bin", return_value="/usr/bin/openshell"), \
         patch("subprocess.run", side_effect=side_effects), \
         patch("clawmetry.sync._flush_session_batch",
               side_effect=lambda b, *a, **k: flushed.extend(b)):
        sync_sandbox_sessions_openshell(CONFIG, {})

    assert flushed
    assert "_nemo_agent_dir" not in flushed[0]
