"""Tests for AiderAdapter (clawmetry/adapters/aider.py).

Validated against a REAL ``.aider.chat.history.md`` captured by actually
installing ``aider-chat`` (v0.82.3) and running two real one-shot turns
against a local Ollama model (``ollama_chat/llama3.2``) in a throwaway git
repo. The fixture under tests/fixtures/runtimes/aider/<projhash>/ is that
real transcript (synthetic demo content, safe to commit).

Locked-in facts about the real format:
  - sessions are delimited by ``# aider chat started at <ts>`` headers
  - the model appears in a ``> Model: ollama_chat/llama3.2 ...`` line
  - user prompts are ``#### ...`` lines; assistant prose is plain text
  - per-reply tokens appear as ``> Tokens: 796 sent, 34 received.``
  - the very first header is an ABORTED "newer version available" block
    with no user/assistant turns; list_sessions() must skip it (detect()
    still counts its header, which is honest)
"""
from __future__ import annotations

import os

import pytest

from clawmetry.adapters.aider import AiderAdapter
from clawmetry.adapters.base import Capability

_FIXTURE_PROJECT_DIR = os.path.join(
    os.path.dirname(__file__),
    "fixtures",
    "runtimes",
    "aider",
    "e5ff42609174",
)


@pytest.fixture
def adapter() -> AiderAdapter:
    return AiderAdapter(roots=[_FIXTURE_PROJECT_DIR])


# -- detect ------------------------------------------------------------------


def test_detect_detected_and_counts(adapter):
    result = adapter.detect()
    assert result.detected is True
    assert result.running is False
    assert result.name == "aider"
    assert result.display_name == "Aider"
    # Three "# aider chat started at" headers in the real capture (incl. the
    # aborted upgrade block). detect() counts headers; honest, cheap.
    assert result.session_count == 3
    assert _FIXTURE_PROJECT_DIR in result.meta["roots"]
    assert result.meta["historyFiles"]


def test_detect_false_when_no_history(tmp_path):
    """detect() must not raise and reports detected=False with an empty root."""
    a = AiderAdapter(roots=[str(tmp_path / "no-such-project")])
    result = a.detect()
    assert result.detected is False
    assert result.session_count == 0


# -- list_sessions -----------------------------------------------------------


def test_list_sessions_skips_empty_block_and_orders_newest_first(adapter):
    sessions = adapter.list_sessions()
    # Two real turns; the aborted upgrade block (no user/assistant turns)
    # is skipped.
    assert len(sessions) == 2
    # Newest first: the goodbye() turn started after the hello() turn.
    assert sessions[0].title == "Now add a goodbye() function to hello.py that prints goodbye."
    assert sessions[0].started_at >= sessions[1].started_at


def test_list_sessions_model_title_and_timestamps(adapter):
    first = adapter.list_sessions()[1]  # the hello() turn (older)
    assert first.model == "ollama_chat/llama3.2"
    assert first.source == "aider"
    assert first.title.startswith("Add a Python function hello()")
    assert first.message_count == 2  # one user + one assistant
    assert first.started_at > 0
    assert first.ended_at is not None
    assert first.ended_at >= first.started_at


def test_list_sessions_tokens_parsed_from_md(adapter):
    """Aider's .md logs ``> Tokens: N sent, M received.`` — parsed honestly."""
    by_title = {s.title[:20]: s for s in adapter.list_sessions()}
    hello = by_title["Add a Python functio"]
    assert hello.input_tokens == 796
    assert hello.output_tokens == 34
    assert hello.total_tokens == 830
    goodbye = by_title["Now add a goodbye() "]
    assert goodbye.input_tokens == 763
    assert goodbye.output_tokens == 53
    assert goodbye.total_tokens == 816
    # No dollar cost on disk (local model) -> cost_usd stays unknown.
    for s in adapter.list_sessions():
        assert s.cost_usd is None
        assert s.extra["tokensPresent"] is True


def test_session_ids_are_stable_across_reads(adapter):
    ids_a = [s.id for s in adapter.list_sessions()]
    ids_b = [s.id for s in AiderAdapter(roots=[_FIXTURE_PROJECT_DIR]).list_sessions()]
    assert ids_a == ids_b


# -- list_events -------------------------------------------------------------


def test_list_events_ordered_roles(adapter):
    sessions = adapter.list_sessions()
    older = sessions[1]  # hello() turn
    events = adapter.list_events(older.id)
    types_roles = [(e.type, e.role) for e in events]
    # One user prompt then one assistant reply, in chronological order.
    assert types_roles == [("message", "user"), ("message", "assistant")]
    # The user content is the actual prompt.
    assert events[0].content.startswith("Add a Python function hello()")
    # The assistant content carries the model in extra.
    assert events[1].extra.get("modelFull") == "ollama_chat/llama3.2"
    # Chronological (non-decreasing timestamps).
    ts_list = [e.ts for e in events if e.ts]
    assert ts_list == sorted(ts_list)


def test_list_events_empty_for_unknown_session(adapter):
    assert adapter.list_events("does-not-exist") == []


# -- capabilities ------------------------------------------------------------


def test_capabilities_includes_cost_when_tokens_present(adapter):
    caps = adapter.capabilities()
    assert Capability.SESSIONS in caps
    assert Capability.EVENTS in caps
    # The real capture has ``> Tokens:`` lines, so COST is honestly claimed.
    assert Capability.COST in caps


def test_capabilities_no_cost_when_tokens_absent(tmp_path):
    """A transcript with no Tokens lines must NOT advertise COST."""
    proj = tmp_path / "proj"
    proj.mkdir()
    (proj / ".aider.chat.history.md").write_text(
        "# aider chat started at 2026-05-25 10:00:00\n\n"
        "> Model: ollama_chat/llama3.2 with whole edit format  \n\n"
        "#### just chatting, no edits  \n\n"
        "Sure, here is a reply with no token accounting.\n"
    )
    a = AiderAdapter(roots=[str(proj)])
    caps = a.capabilities()
    assert Capability.SESSIONS in caps
    assert Capability.EVENTS in caps
    assert Capability.COST not in caps
    s = a.list_sessions()[0]
    assert s.total_tokens == 0
    assert s.cost_status == "unavailable"


# -- never raises on bad input -----------------------------------------------


def test_never_raises_on_garbage_file(tmp_path):
    """A garbage / unparseable history file must be tolerated, not fatal."""
    proj = tmp_path / "garbage-proj"
    proj.mkdir()
    # Binary-ish garbage with no aider structure at all.
    (proj / ".aider.chat.history.md").write_bytes(
        b"\x00\x01\x02 not a real transcript\n#### \xff\xfe broken prompt\n"
        b"> Tokens: not-a-number sent, also-bad received.\n"
    )
    a = AiderAdapter(roots=[str(proj)])

    # detect must not raise.
    result = a.detect()
    assert result.detected is True

    # list_sessions must not raise; bad token counts coerce to 0.
    sessions = a.list_sessions()
    # The garbage still has a "####" line -> one block with a user turn.
    assert isinstance(sessions, list)
    for s in sessions:
        assert s.total_tokens == 0
        assert s.cost_usd is None

    # list_events must not raise on any returned session id.
    for s in sessions:
        assert isinstance(a.list_events(s.id), list)
    assert a.list_events("nope") == []
