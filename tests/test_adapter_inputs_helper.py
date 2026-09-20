"""Contract tests for clawmetry/adapters/inputs.py.

``clawmetry.adapters.inputs`` is the OSS twin of
``clawmetry_pro.adapters._inputs`` — the helper every runtime adapter uses to
emit the ``context.compiled`` event (what the agent was GIVEN). It moved into
the open package on 2026-09-20 because the bundled Qwen Code reader needs it,
the same way ``clawmetry/adapters/cost.py`` moved for Goose.

CI cannot see clawmetry-pro, so this cannot diff the two copies. What it CAN
do is pin the contract both copies must satisfy — the export surface, the
event shape, and the id-stability rule the OSS store dedupes on. A pro-side
change that breaks any of these breaks ingest, and this is the statement of
what "in lockstep" means.
"""
from __future__ import annotations

from clawmetry.adapters.base import Capability, Event
from clawmetry.adapters.inputs import (
    CAP_INPUTS,
    EVENT_TYPE,
    context_event,
    prepend_context,
    with_inputs,
)


def _ev(ts: float, type_: str = "message") -> Event:
    return Event(agent="qwen_code", session_id="s1", id=f"e{ts}", type=type_,
                 ts=ts, role="user", content="hi", extra={})


def test_export_surface_is_what_adapters_import():
    """The names the adapters import must all exist and be callable."""
    assert EVENT_TYPE == "context.compiled"
    assert CAP_INPUTS is Capability.INPUTS
    for fn in (context_event, prepend_context, with_inputs):
        assert callable(fn)


def test_returns_none_when_there_is_nothing_to_say():
    """HONESTY: no facts on disk means no event, never a placeholder one."""
    assert context_event("qwen_code", "s1", 1.0) is None
    assert context_event("qwen_code", "s1", 1.0, prompt="   ", tools=[],
                         runtime_meta={"cwd": "", "model": None}) is None


def test_empty_fields_are_dropped_not_emitted_blank():
    ev = context_event("qwen_code", "s1", 5.0, prompt="do a thing",
                       system_prompt="  ", tools=["ls", "ls", " "],
                       runtime_meta={"cwd": "/tmp", "model": "", "mcpServers": []},
                       source="message.parts")
    assert ev is not None
    assert ev.type == EVENT_TYPE
    assert ev.extra["prompt"] == "do a thing"
    assert "systemPrompt" not in ev.extra      # whitespace-only is absent, not ""
    assert ev.extra["tools"] == ["ls"]         # deduped, blanks dropped
    assert ev.extra["runtimeMeta"] == {"cwd": "/tmp"}   # "" and [] dropped
    assert ev.extra["source"] == "message.parts"


def test_event_id_is_stable_per_payload_so_rereads_do_not_multiply_rows():
    """The OSS store dedupes ``events`` on id. Two reads of an unchanged
    session must produce the same id, and a changed payload a different one."""
    a = context_event("qwen_code", "s1", 1.0, prompt="p", runtime_meta={"cwd": "/a"})
    b = context_event("qwen_code", "s1", 9.0, prompt="p", runtime_meta={"cwd": "/a"})
    c = context_event("qwen_code", "s1", 1.0, prompt="p", runtime_meta={"cwd": "/b"})
    assert a.id == b.id, "same payload at a different ts must keep one row"
    assert a.id != c.id, "a changed payload must be a new row"
    assert a.id.startswith("ctx:s1:")


def test_source_is_not_part_of_the_fingerprint():
    """``source`` is provenance, not a fact about the session: adding or
    rewording it must not orphan the existing row."""
    a = context_event("qwen_code", "s1", 1.0, prompt="p")
    b = context_event("qwen_code", "s1", 1.0, prompt="p", source="message.parts[0]")
    assert a.id == b.id


def test_prepend_context_puts_it_first_and_never_after_the_first_event():
    ctx = context_event("qwen_code", "s1", 999.0, prompt="p")
    out = prepend_context([_ev(10.0), _ev(20.0)], ctx)
    assert out[0] is ctx
    assert out[0].ts == 10.0, "context must not sort after what it produced"
    assert [e.ts for e in out] == [10.0, 10.0, 20.0]


def test_prepend_context_is_a_noop_without_a_context_event():
    evs = [_ev(1.0)]
    assert prepend_context(evs, None) is evs


def test_with_inputs_adds_the_capability():
    assert Capability.INPUTS in with_inputs({Capability.SESSIONS})
