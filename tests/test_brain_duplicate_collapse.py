"""Guard for the duplicated Brain feed rows (founder report 2026-06-29).

One OpenClaw assistant turn lands as an ``assistant``/``message`` row PLUS one
or two ``model.completed`` siblings a second or two apart (one a tokens=0
``delivery-mirror`` echo), all with the same text. They have different
timestamps + ids, so the exact-tuple dedupe misses them and the same paragraph
renders two or three times. ``_collapse_duplicate_brain_events`` keeps the
richest row per (session, identical substantial detail) within a time window.
"""

from __future__ import annotations

from routes.brain import _collapse_duplicate_brain_events

_DETAIL = (
    "Okay, this time it's genuinely launched (run ID wf_f9706de7-56b), and I can "
    "confirm it's a real background workflow with its own transcript on disk."
)


def _ev(t, etype, tokens, model="claude-opus-4-8", src="04887442", detail=_DETAIL):
    return {"time": t, "type": etype, "tokens": tokens, "model": model,
            "src": src, "sessionId": src, "detail": detail}


def test_collapses_assistant_plus_model_completed_siblings():
    events = [
        _ev("2026-06-29T03:00:50.278Z", "ASSISTANT", 268),
        _ev("2026-06-29T03:00:51.127Z", "MODEL.COMPLETED", 4),
        _ev("2026-06-29T03:00:52.822Z", "MODEL.COMPLETED", 0, model="delivery-mirror"),
    ]
    out = _collapse_duplicate_brain_events(events)
    assert len(out) == 1, "the three siblings should collapse to one row"
    # The richest survives: the real assistant row with 268 tokens.
    assert out[0]["type"] == "ASSISTANT"
    assert out[0]["tokens"] == 268


def test_keeps_genuine_reutterance_in_a_later_turn():
    # Same text, but minutes apart -> two real turns, keep both.
    events = [
        _ev("2026-06-29T03:00:50Z", "ASSISTANT", 100),
        _ev("2026-06-29T03:30:50Z", "ASSISTANT", 100),
    ]
    assert len(_collapse_duplicate_brain_events(events)) == 2


def test_does_not_cross_sessions():
    events = [
        _ev("2026-06-29T03:00:50Z", "ASSISTANT", 100, src="sessA"),
        _ev("2026-06-29T03:00:51Z", "MODEL.COMPLETED", 0, src="sessB"),
    ]
    assert len(_collapse_duplicate_brain_events(events)) == 2


def test_short_repeated_detail_is_left_alone():
    # Short repeated phrases (e.g. "ok") must not be collapsed.
    events = [
        _ev("2026-06-29T03:00:50Z", "ASSISTANT", 1, detail="ok"),
        _ev("2026-06-29T03:00:51Z", "MODEL.COMPLETED", 0, detail="ok"),
    ]
    assert len(_collapse_duplicate_brain_events(events)) == 2


def test_distinct_content_untouched():
    events = [
        _ev("2026-06-29T03:00:50Z", "ASSISTANT", 100, detail=_DETAIL),
        _ev("2026-06-29T03:00:51Z", "ASSISTANT", 100, detail=_DETAIL + " plus more"),
    ]
    assert len(_collapse_duplicate_brain_events(events)) == 2


def test_missing_timestamps_still_collapse_same_content():
    events = [
        _ev("", "MODEL.COMPLETED", 0, model="delivery-mirror"),
        _ev("", "ASSISTANT", 268),
    ]
    out = _collapse_duplicate_brain_events(events)
    assert len(out) == 1
    assert out[0]["type"] == "ASSISTANT"
