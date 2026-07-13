"""Tests for sync_sandbox_sessions_openshell (issues #3116, #3234).

No DuckDB or network required — all openshell and flush calls are mocked.
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


def test_no_openshell_returns_zero():
    with patch("clawmetry.sync._find_openshell_bin", return_value=None):
        assert sync_sandbox_sessions_openshell(CONFIG, {}) == 0


def test_happy_path_flushes_events_and_advances_cursor():
    events = [
        json.dumps({"type": "message", "id": "e1", "role": "user", "content": "hi"}),
        json.dumps({"type": "message", "id": "e2", "role": "assistant", "content": "hello"}),
    ]
    sandbox_list = json.dumps([{"name": "my-sandbox", "status": "running"}])
    ls_output = "abc123.jsonl\n"
    cat_output = "\n".join(events) + "\n"

    side_effects = [
        _run(0, sandbox_list),
        _run(0, ls_output),   # ls agents/main/sessions
        _run(0, cat_output),  # cat main/abc123.jsonl
        _run(1, ""),          # ls agents/advisor/sessions (absent — nonzero)
    ]

    state = {}
    flushed = []
    with patch("clawmetry.sync._find_openshell_bin", return_value="/usr/bin/openshell"), \
         patch("subprocess.run", side_effect=side_effects), \
         patch("clawmetry.sync._flush_session_batch",
               side_effect=lambda b, *a, **k: flushed.extend(b)):
        count = sync_sandbox_sessions_openshell(CONFIG, state)

    assert count == 2
    assert len(flushed) == 2
    # cursor key now includes agent_dir (#3698)
    assert state["sandbox_session_cursors"]["my-sandbox/main/abc123.jsonl"] == 2


def test_sidecar_files_excluded():
    sandbox_list = json.dumps([{"name": "sb"}])
    ls_output = "abc.jsonl\nabc.trajectory.jsonl\nabc.checkpoint.jsonl\nabc.deleted.jsonl\n"
    cat_output = json.dumps({"id": "e1", "type": "message"}) + "\n"

    # Only abc.jsonl should be read (1 cat call); sidecars produce no cat call
    side_effects = [
        _run(0, sandbox_list),
        _run(0, ls_output),   # ls agents/main/sessions
        _run(0, cat_output),  # cat main/abc.jsonl (only non-sidecar)
        _run(1, ""),          # ls agents/advisor/sessions (absent)
    ]
    flushed = []
    with patch("clawmetry.sync._find_openshell_bin", return_value="/usr/bin/openshell"), \
         patch("subprocess.run", side_effect=side_effects), \
         patch("clawmetry.sync._flush_session_batch",
               side_effect=lambda b, *a, **k: flushed.extend(b)):
        sync_sandbox_sessions_openshell(CONFIG, {})

    assert len(flushed) == 1


def test_sandbox_sessions_tagged_as_nemoclaw():
    """Sandbox sessions must land with agent_type='nemoclaw' so NemoClawAdapter
    list_sessions() (which filters WHERE agent_type='nemoclaw') can see them.
    Regression test for #3234."""
    events = [json.dumps({"type": "message", "id": "e1", "content": "hi"})]
    sandbox_list = json.dumps([{"name": "sb", "status": "running"}])
    ls_output = "sess.jsonl\n"
    cat_output = "\n".join(events) + "\n"

    side_effects = [
        _run(0, sandbox_list),
        _run(0, ls_output),   # ls agents/main/sessions
        _run(0, cat_output),  # cat main/sess.jsonl
        _run(1, ""),          # ls agents/advisor/sessions (absent)
    ]

    flush_kwargs = []
    with patch("clawmetry.sync._find_openshell_bin", return_value="/usr/bin/openshell"), \
         patch("subprocess.run", side_effect=side_effects), \
         patch("clawmetry.sync._flush_session_batch",
               side_effect=lambda b, *a, **k: flush_kwargs.append(k)):
        sync_sandbox_sessions_openshell(CONFIG, {})

    assert flush_kwargs, "flush was never called"
    assert flush_kwargs[0].get("agent_type") == "nemoclaw", (
        "sandbox sessions must be tagged agent_type='nemoclaw' so the "
        "NemoClawAdapter session query can find them"
    )


def test_cursor_skips_already_seen_lines_on_second_call():
    event_line = json.dumps({"id": "e1", "type": "message"})
    sandbox_list = json.dumps([{"name": "sb"}])
    ls_output = "sess.jsonl\n"
    cat_output = event_line + "\n"

    state = {}
    flushed = []

    def make_effects():
        return [
            _run(0, sandbox_list),
            _run(0, ls_output),  # ls agents/main/sessions
            _run(0, cat_output), # cat main/sess.jsonl
            _run(1, ""),         # ls agents/advisor/sessions (absent)
        ]

    with patch("clawmetry.sync._find_openshell_bin", return_value="/usr/bin/openshell"), \
         patch("subprocess.run", side_effect=make_effects()), \
         patch("clawmetry.sync._flush_session_batch",
               side_effect=lambda b, *a, **k: flushed.extend(b)):
        sync_sandbox_sessions_openshell(CONFIG, state)

    assert len(flushed) == 1
    # cursor key now includes agent_dir (#3698)
    assert state["sandbox_session_cursors"]["sb/main/sess.jsonl"] == 1

    flushed.clear()
    with patch("clawmetry.sync._find_openshell_bin", return_value="/usr/bin/openshell"), \
         patch("subprocess.run", side_effect=make_effects()), \
         patch("clawmetry.sync._flush_session_batch",
               side_effect=lambda b, *a, **k: flushed.extend(b)):
        count = sync_sandbox_sessions_openshell(CONFIG, state)

    assert count == 0
    assert len(flushed) == 0
