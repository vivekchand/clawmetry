"""Quality signal contract tests — the gate that would have caught the
2026-08-15 audit findings before they shipped.

The bug that motivated every test here: the old cognitive-loop detector read
tool use ONLY from ``data.message.content[*].type == "tool_use"`` (the
OpenClaw/Anthropic block-list shape). Every family runtime emits tool calls as
separate ``tool_call`` events carrying ``data.tool_calls[*]``, so the parser
returned [] for all of them, the "did the agent make forward progress?" guard
never fired, and sessions with 60+ real tool calls were reported as loops.

Nothing raised. Nothing was empty. The existing tests stayed green because
they ran OpenClaw fixtures through an OpenClaw-shaped parser.

So these tests are deliberately structured around that failure mode:
  * every dialect must parse (test_dialect_*)
  * a verdict may never exist without evidence (test_evidence_*)
  * confidence must vary (test_confidence_*)
  * absent signals must degrade to not-measurable, never to a pass
    (test_capability_*)
"""
from __future__ import annotations

import pytest

from clawmetry.quality_signals import (
    SIGNALS,
    EvidenceError,
    Verdict,
    assess_session,
    normalize_events,
    probe_capabilities,
)


# ── helpers ────────────────────────────────────────────────────────────────

def _family_tool_call(ts, tool, inp, runtime="claude_code"):
    """The shape every family adapter writes (claude_code, codex, cursor, …)."""
    return {
        "event_type": "tool_call",
        "ts": ts,
        "data": {
            "role": "assistant", "content": "", "_runtime": runtime,
            "tool_calls": [{"id": "t", "name": tool, "input": inp}],
            "tool_name": tool,
        },
    }


def _family_tool_result(ts, text="ok", is_error=False, benign=False):
    d = {
        "role": "user", "content": text, "_runtime": "claude_code",
        "extra": {"isError": bool(is_error)},
    }
    if benign:
        d["benign_error"] = True
    return {"event_type": "tool_result", "ts": ts, "data": d}


def _openclaw_tool_call(ts, tool, inp):
    """OpenClaw v3's dotted vocabulary with a flat name/input payload."""
    return {
        "event_type": "tool.use", "ts": ts,
        "data": {"name": tool, "input": inp, "id": "x"},
    }


def _anthropic_block_call(ts, tool, inp):
    """The block-list shape the OLD parser could read — must still work."""
    return {
        "event_type": "message", "ts": ts,
        "data": {"message": {"role": "assistant", "content": [
            {"type": "tool_use", "name": tool, "input": inp},
        ]}},
    }


def _msg(ts, text, role="assistant"):
    return {"event_type": "message", "ts": ts,
            "data": {"role": role, "content": text, "_runtime": "claude_code"}}


# ── dialect coverage: THE regression tests ─────────────────────────────────

def test_dialect_family_tool_call_is_parsed():
    """The exact blindness that caused the audit."""
    evs = normalize_events([_family_tool_call(1000, "Bash", {"command": "ls"})])
    assert len(evs) == 1
    e = evs[0]
    assert e.kind == "tool_call"
    assert e.tool_name == "Bash", (
        "family tool_call events must be parsed; reading only the Anthropic "
        "block-list shape is what made the old detector blind"
    )
    assert e.tool_input == {"command": "ls"}


def test_dialect_openclaw_flat_tool_call_is_parsed():
    evs = normalize_events([_openclaw_tool_call(1000, "read_file",
                                                {"path": "/tmp/a"})])
    assert evs[0].kind == "tool_call"
    assert evs[0].tool_name == "read_file"
    assert evs[0].file_path == "/tmp/a"


def test_dialect_anthropic_block_list_still_parsed():
    """The one shape the old parser DID handle must not regress."""
    evs = normalize_events([_anthropic_block_call(1000, "Edit",
                                                  {"file_path": "/x.py"})])
    assert evs[0].tool_name == "Edit"
    assert evs[0].file_path == "/x.py"


@pytest.mark.parametrize("runtime", [
    "claude_code", "codex", "cursor", "aider", "goose", "opencode",
    "qwen_code", "copilot", "antigravity", "n8n", "picoclaw", "nanoclaw",
    "hermes", "grok", "qm", "deepseek_harness", "exo", "pi", "deepagents",
])
def test_dialect_every_family_runtime_parses(runtime):
    """Every family runtime shares one envelope. If a new adapter lands with a
    different shape, this fails loudly instead of silently grading it blind."""
    evs = normalize_events([
        _family_tool_call(1000, "Bash", {"command": "x"}, runtime=runtime),
    ])
    assert evs[0].tool_name == "Bash", f"{runtime} tool call not parsed"


def test_error_flag_absent_is_not_success():
    """A runtime that reports nothing about a result must read as UNKNOWN.

    Treating silence as success is how a blind signal turns into a clean bill
    of health.
    """
    evs = normalize_events([
        {"event_type": "tool_result", "ts": 1, "data": {"content": "done"}},
    ])
    assert evs[0].is_error is None, "no error flag must be None, not False"


# ── the evidence invariant ─────────────────────────────────────────────────

def test_evidence_verdict_without_exhibits_is_refused():
    """The core contract. A claim with no evidence must not be constructible."""
    with pytest.raises(EvidenceError):
        Verdict(
            name="tool_failures", runtime="claude_code", confidence=0.9,
            signal="tool_error_rate", observed={}, threshold={}, window={},
            exhibits=[],
        )


def test_evidence_every_emitted_verdict_carries_exhibits():
    """Whatever a detector emits on real-ish input, it must be inspectable."""
    events = []
    t = 1000
    for i in range(14):
        events.append(_family_tool_call(t, "Bash", {"command": "flaky"}))
        events.append(_family_tool_result(t + 1, "boom", is_error=True))
        t += 10
    a = assess_session(events, runtime="claude_code", session_id="s1",
                       thresholds={"tool_error_pct": 8.0})
    assert a.verdicts, "a session failing every tool call must produce a verdict"
    for v in a.verdicts:
        d = v.as_dict()
        assert d["evidence"]["exhibits"], f"{v.name} shipped without exhibits"
        assert d["evidence"]["threshold"], f"{v.name} shipped without a threshold"
        assert d["evidence"]["observed"], f"{v.name} shipped without observations"


# ── false-positive regression: the 8 sessions from the audit ───────────────

def test_busy_session_with_varied_tools_is_clean():
    """An agent doing real work must NOT be flagged.

    This is the audit's headline false positive in miniature: repetitive
    assistant narration ("standing by", "waiting on that merge") alongside
    steady, varied, successful tool use. The old detector called this a loop
    because it could not see the tool calls at all.
    """
    events = []
    t = 1000
    narration = [
        "Relaying to the owner. Standing by for their signal.",
        "Relaying to the owner. Waiting on that merge.",
        "Relaying to the owner. Waiting for their fix + merge.",
        "Relaying to the owner. Standing by for the green light.",
    ]
    for i in range(24):
        events.append(_family_tool_call(
            t, ["Bash", "Read", "Edit", "Grep"][i % 4],
            {"file_path": f"/repo/file_{i}.py"}))
        events.append(_family_tool_result(t + 1, "ok", is_error=False))
        events.append(_msg(t + 2, narration[i % len(narration)]))
        t += 20
    a = assess_session(events, runtime="claude_code", session_id="busy",
                       thresholds={"tool_error_pct": 8.0})
    assert a.measurable
    assert not a.verdicts, (
        f"a productive session was flagged: {[v.name for v in a.verdicts]}"
    )


def test_real_thrash_is_still_caught():
    """The signal must not be defanged into uselessness by the fix."""
    events = []
    t = 1000
    for _ in range(8):
        events.append(_family_tool_call(t, "Edit", {"file_path": "/a.py",
                                                    "old": "x", "new": "y"}))
        events.append(_family_tool_result(t + 1, "failed to apply",
                                          is_error=True))
        t += 15
    a = assess_session(events, runtime="claude_code", session_id="thrash",
                       thresholds={"tool_error_pct": 8.0, "thrash_repeats": 4})
    names = {v.name for v in a.verdicts}
    assert "tool_thrash" in names, f"real thrash missed; got {names}"


def test_identical_but_successful_repeats_are_not_thrash():
    """Polling or re-running a formatter is repetition, not failure."""
    events = []
    t = 1000
    for _ in range(9):
        events.append(_family_tool_call(t, "Bash", {"command": "make fmt"}))
        events.append(_family_tool_result(t + 1, "ok", is_error=False))
        t += 15
    a = assess_session(events, runtime="claude_code", session_id="poll",
                       thresholds={"tool_error_pct": 8.0, "thrash_repeats": 4})
    assert "tool_thrash" not in {v.name for v in a.verdicts}


def test_benign_errors_do_not_count_against_the_agent():
    """A read-guard retry is recoverable and must not inflate the rate."""
    events = []
    t = 1000
    for _ in range(20):
        events.append(_family_tool_call(t, "Write", {"file_path": "/a.py"}))
        events.append(_family_tool_result(
            t + 1, "<tool_use_error>File has not been read yet.</tool_use_error>",
            is_error=True, benign=True))
        t += 10
    a = assess_session(events, runtime="claude_code", session_id="benign",
                       thresholds={"tool_error_pct": 8.0})
    assert "tool_failures" not in {v.name for v in a.verdicts}


def test_edit_then_verify_is_not_flagged():
    """Edit → run tests → edit is the normal loop, not a stuck one."""
    events = []
    t = 1000
    for _ in range(9):
        events.append(_family_tool_call(t, "Edit", {"file_path": "/a.py"}))
        events.append(_family_tool_result(t + 1, "ok"))
        events.append(_family_tool_call(t + 2, "Bash", {"command": "pytest"}))
        events.append(_family_tool_result(t + 3, "ok"))
        t += 20
    a = assess_session(events, runtime="claude_code", session_id="iter",
                       thresholds={"edit_repeats": 5, "tool_error_pct": 8.0})
    assert "no_forward_progress" not in {v.name for v in a.verdicts}


def test_edit_without_verify_is_flagged():
    events = []
    t = 1000
    for _ in range(9):
        events.append(_family_tool_call(t, "Edit", {"file_path": "/a.py"}))
        events.append(_family_tool_result(t + 1, "ok"))
        t += 20
    a = assess_session(events, runtime="claude_code", session_id="spin",
                       thresholds={"edit_repeats": 5, "tool_error_pct": 8.0})
    assert "no_forward_progress" in {v.name for v in a.verdicts}


# ── confidence must be derived, not constant ───────────────────────────────

def test_confidence_varies_with_sample_size():
    """The old classifier returned 0.8 for every single flagged session."""
    def _run(n):
        evs = []
        t = 1000
        for _ in range(n):
            evs.append(_family_tool_call(t, "Bash", {"command": "x"}))
            evs.append(_family_tool_result(t + 1, "boom", is_error=True))
            t += 10
        a = assess_session(evs, runtime="claude_code", session_id="c",
                           thresholds={"tool_error_pct": 8.0})
        vs = [v for v in a.verdicts if v.name == "tool_failures"]
        return vs[0].confidence if vs else None

    small, large = _run(6), _run(60)
    assert small is not None and large is not None
    assert large > small, (
        f"confidence must grow with evidence (got {small} then {large}); "
        "a constant confidence is not a confidence"
    )


def test_confidence_is_never_a_hardcoded_constant():
    """Guards against a regression to literal confidences."""
    seen = set()
    for n in (6, 12, 40, 120):
        evs = []
        t = 1000
        for _ in range(n):
            evs.append(_family_tool_call(t, "Bash", {"command": "x"}))
            evs.append(_family_tool_result(t + 1, "boom", is_error=True))
            t += 10
        a = assess_session(evs, runtime="claude_code", session_id="c",
                           thresholds={"tool_error_pct": 8.0})
        for v in a.verdicts:
            if v.name == "tool_failures":
                seen.add(round(v.confidence, 3))
    assert len(seen) > 1, f"confidence never varied across sample sizes: {seen}"


# ── capability honesty ─────────────────────────────────────────────────────

def test_capability_probe_reports_what_was_seen():
    events = normalize_events([
        _family_tool_call(1, "Edit", {"file_path": "/a.py"}),
        _family_tool_result(2, "ok", is_error=False),
    ])
    caps = probe_capabilities(events, runtime="claude_code")
    assert caps.has_tool_calls and caps.has_tool_inputs
    assert caps.has_file_paths and caps.has_error_flags
    assert caps.supports("tool_error_rate")


def test_capability_missing_error_flags_disables_that_signal():
    """A runtime that never reports isError cannot be graded on error rate —
    and must not be reported as healthy instead."""
    events = normalize_events([
        {"event_type": "tool_call", "ts": i,
         "data": {"tool_calls": [{"name": "Run", "input": {}}]}}
        for i in range(10)
    ])
    caps = probe_capabilities(events, runtime="mystery_runtime")
    assert not caps.has_error_flags
    assert not caps.supports("tool_error_rate")


def test_thin_session_is_not_measurable_rather_than_success():
    """A research chat with no tool use must be EXCLUDED, not passed.

    18 of 62 sessions in the audit window were exactly this, and every one was
    collecting a free "success" from the old fallthrough default.
    """
    events = [_msg(1, "hello"), _msg(2, "here is an answer")]
    a = assess_session(events, runtime="claude_code", session_id="chat")
    assert a.measurable is False
    assert a.verdicts == []
    assert a.not_measurable_reason


def test_unknown_runtime_with_no_signals_is_not_measurable():
    events = [{"event_type": "custom_thing", "ts": i, "data": {"x": 1}}
              for i in range(20)]
    a = assess_session(events, runtime="brand_new_runtime", session_id="u")
    assert a.measurable is False
    assert "does not report" in a.not_measurable_reason


# ── registry sanity ────────────────────────────────────────────────────────

def test_every_signal_declares_its_requirements():
    for name, sig in SIGNALS.items():
        assert callable(sig.requires), f"{name} has no capability declaration"
        assert callable(sig.detect)
        assert sig.label and not sig.label.endswith("."), (
            f"{name}: label is user-facing copy, keep it a short phrase"
        )


def test_assess_never_raises_on_garbage():
    for junk in (None, [], [{}], [{"event_type": None, "ts": None, "data": None}],
                 [{"data": "not json"}], [{"data": b"\xff\xfe"}]):
        a = assess_session(junk, runtime="claude_code", session_id="junk")
        assert a.verdicts == []


# ── the fabricated label must stop reaching OTHER surfaces too ─────────────

def test_cognitive_loop_requires_corroborating_evidence():
    """Text repetition alone can no longer produce a failure label.

    ``sessions.outcome`` is read by /api/outcomes (the Overview tile), evals,
    and the cloud snapshot — not just the Quality tab. Fixing only the tab
    would have left the same fabricated failures on other screens.
    """
    from clawmetry.outcome_classifier import classify_session

    # Repetitive narration, but steady varied successful tool use underneath:
    # the audit's headline false positive.
    events, t = [], 1_780_000_000
    lines = ["Relaying to the owner. Standing by for their signal.",
             "Relaying to the owner. Waiting on that merge.",
             "Relaying to the owner. Waiting for their fix + merge.",
             "Relaying to the owner. Standing by for the green light."]
    for i in range(20):
        events.append(_family_tool_call(t, ["Bash", "Read", "Edit", "Grep"][i % 4],
                                        {"file_path": "/repo/f%d.py" % i}))
        events.append(_family_tool_result(t + 1, "ok"))
        events.append(_msg(t + 2, lines[i % len(lines)]))
        t += 20
    outcome, _conf = classify_session(events, {"status": "ended"})
    assert outcome != "cognitive_loop", (
        "repetitive narration over real, varied tool use must not be a loop"
    )


def test_cognitive_loop_still_fires_with_corroboration():
    """The guard must not defang the label into uselessness."""
    from clawmetry.outcome_classifier import classify_session

    events, t = [], 1_780_000_000
    for _ in range(9):
        events.append(_family_tool_call(t, "Edit", {"file_path": "/a.py",
                                                    "old": "x", "new": "y"}))
        events.append(_family_tool_result(t + 1, "failed to apply", is_error=True))
        events.append(_msg(t + 2, "Retrying the same edit on the same file now."))
        t += 15
    outcome, conf = classify_session(events, {"status": "ended"})
    assert outcome == "cognitive_loop", (
        "a genuine stuck session must still be labelled; got %r" % outcome
    )
    assert conf > 0


def test_stale_classification_detection():
    """Only pre-fix FAILURE labels are re-classified.

    Re-running successes would be a large read for no correction (the old
    success branch was a conservative fallthrough and cannot have invented a
    failure), and re-running post-fix rows on every read would be a request
    storm.
    """
    from clawmetry.local_store import (
        _CLASSIFIER_FIX_EPOCH_MS, _is_stale_classification,
    )
    old, new = _CLASSIFIER_FIX_EPOCH_MS - 1, _CLASSIFIER_FIX_EPOCH_MS + 1
    assert _is_stale_classification({"outcome": "cognitive_loop",
                                     "outcome_classified_at": old})
    assert not _is_stale_classification({"outcome": "cognitive_loop",
                                         "outcome_classified_at": new})
    assert not _is_stale_classification({"outcome": "success",
                                         "outcome_classified_at": old})
    assert _is_stale_classification({"outcome": "tool_call_stuck",
                                     "outcome_classified_at": None})
    assert not _is_stale_classification({"outcome": None})


def test_thrash_counts_failures_over_all_repeats_not_just_exhibits():
    """`failed` and `identical_calls` must share a denominator.

    Exhibits are capped at 12 for payload size. Counting failures only over
    that slice would report "identical_calls: 30, failed: 12" for a session
    where 25 actually failed — two numbers from different denominators inside
    one evidence block, on a surface whose whole promise is that its numbers
    survive being looked at.
    """
    events, t = [], 1_780_000_000
    for _ in range(30):
        events.append(_family_tool_call(t, "Bash", {"command": "same"}))
        events.append(_family_tool_result(t + 1, "boom", is_error=True))
        t += 15
    a = assess_session(events, runtime="claude_code", session_id="cap",
                       thresholds={"tool_error_pct": 8.0, "thrash_repeats": 4})
    thrash = [v for v in a.verdicts if v.name == "tool_thrash"]
    assert thrash, "expected thrash on 30 identical failing calls"
    obs = thrash[0].observed
    assert obs["identical_calls"] == 30, obs
    assert obs["failed"] == 30, (
        "failures must be counted across every repeat, not just the "
        "12 exhibited: %r" % obs
    )
    assert len(thrash[0].exhibits) == 12, "exhibits stay capped"


def test_edit_many_then_verify_at_the_end_is_not_flagged():
    """"Edit a dozen times, then run the tests once" is normal work.

    Only looking for verification BETWEEN the first and last edit flagged this
    healthy pattern — the same false-positive class the whole rebuild exists
    to remove. On real data this alone accounted for 2 of 10 flags.
    """
    events, t = [], 1_780_000_000
    for _ in range(12):
        events.append(_family_tool_call(t, "Edit", {"file_path": "/a.py"}))
        events.append(_family_tool_result(t + 1, "ok"))
        t += 20
    # ...then verify, once, at the very end.
    events.append(_family_tool_call(t, "Bash", {"command": "pytest -q"}))
    events.append(_family_tool_result(t + 1, "12 passed"))
    a = assess_session(events, runtime="claude_code", session_id="endverify",
                       thresholds={"edit_repeats": 5, "tool_error_pct": 8.0})
    assert "no_forward_progress" not in {v.name for v in a.verdicts}, (
        "editing then verifying at the end is a normal cycle, not a stall"
    )


def test_edit_and_never_verify_is_still_flagged():
    """The pathological case must survive the widened window."""
    events, t = [], 1_780_000_000
    for _ in range(12):
        events.append(_family_tool_call(t, "Edit", {"file_path": "/a.py"}))
        events.append(_family_tool_result(t + 1, "ok"))
        t += 20
    a = assess_session(events, runtime="claude_code", session_id="neververify",
                       thresholds={"edit_repeats": 5, "tool_error_pct": 8.0})
    assert "no_forward_progress" in {v.name for v in a.verdicts}
