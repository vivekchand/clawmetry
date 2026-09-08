"""
Brain-feed duplicate collapse (clawmetry/brain_dedupe.py).

Guards the 2026-07-31 founder screenshot: the hosted Brain feed showed one
agent reply THREE times (assistant transcript row + v3 model.completed +
delivery-mirror echo — the cloud blob builder applied no collapse) and one
inbound Telegram message TWICE (gateway prompt.submitted + transcript user
copy, whose "(untrusted metadata)" preamble defeated the exact-string key).

Fixtures below are the REAL DuckDB rows from that incident (slimmed), not
synthetic shapes — synthetic tests have missed real event shapes before.
"""
import copy

from clawmetry.brain_dedupe import (
    collapse_duplicate_brain_rows,
    collapse_events,
    normalize_detail,
    row_text,
)

_SID = "62030919-c8b1-4963-acc4-69465f00c3d1"
_REPLY = "Hey. Go do your meeting. I'm here when you're out."
_USER_PREAMBLED = (
    "Conversation info (untrusted metadata):\n```json\n{\n"
    '  "chat_id": "telegram:1532693273",\n  "message_id": "42",\n'
    '  "sender": {\n    "id": "1532693273",\n    "name": "Vivek Chand",\n'
    '    "username": "vivekchand19",\n    "is_bot": false\n  },\n'
    '  "timestamp": "Fri 2026-07-31 21:18:37 GMT+5:30",\n'
    '  "inbound_event_kind": "user_request",\n'
    '  "explicitly_mentioned_bot": false\n}\n```\n\n'
    "hello - I'm in a meeting"
)


def _v3_reply_row(rid, ts, model):
    return {
        "id": rid, "session_id": _SID, "ts": ts,
        "event_type": "model.completed", "cost_usd": 0.0,
        "data": {
            "type": "model.completed", "_v3_type": "message",
            "completionText": _REPLY, "assistantTexts": [_REPLY],
            "modelId": model, "timestamp": ts,
            "data": {"completionText": _REPLY, "assistantTexts": [_REPLY],
                     "modelId": model},
        },
    }


def _real_rows():
    """The five renderable rows of the real incident, newest first."""
    return [
        _v3_reply_row("1abd6d8b-36cd-471a-a6c7-f9a5616f3c62",
                      "2026-07-31T15:48:42.786Z", "delivery-mirror"),
        _v3_reply_row("745de276-6a7a-46a2-96f2-1e2fa4f87275",
                      "2026-07-31T15:48:42.752Z", "claude-opus-4-8"),
        {
            "id": "cc-msg:23bba84e-615c-48ff-8acc-b58a97c2135b",
            "session_id": _SID, "ts": "2026-07-31T15:48:41.657Z",
            "event_type": "assistant", "cost_usd": 0.0342745,
            "data": {
                "type": "assistant", "timestamp": "2026-07-31T15:48:41.657Z",
                "message": {"role": "assistant",
                            "content": [{"text": _REPLY, "type": "text"}],
                            "model": "claude-opus-4-8"},
            },
        },
        {
            "id": "cc-msg:baccb25c-75f7-46d1-bede-c96c6de0705b",
            "session_id": _SID, "ts": "2026-07-31T15:48:39.551Z",
            "event_type": "user", "cost_usd": None,
            "data": {
                "type": "user", "timestamp": "2026-07-31T15:48:39.551Z",
                "message": {"role": "user", "content": _USER_PREAMBLED},
            },
        },
        {
            "id": "1e7cc85f-dc2d-4a18-aeec-41e550a32fbd",
            "session_id": _SID, "ts": "2026-07-31T15:48:37.906Z",
            "event_type": "prompt.submitted", "cost_usd": None,
            "data": {
                "type": "prompt.submitted", "_v3_type": "message",
                "finalPromptText": "hello - I'm in a meeting",
                "timestamp": "2026-07-31T15:48:37.906Z",
                "data": {"finalPromptText": "hello - I'm in a meeting"},
            },
        },
    ]


# ── normalize_detail ─────────────────────────────────────────────────────────

def test_normalize_strips_untrusted_metadata_preamble():
    assert normalize_detail(_USER_PREAMBLED) == "hello - I'm in a meeting"


def test_normalize_plain_text_only_collapses_whitespace():
    assert normalize_detail("  hello \n world ") == "hello world"
    assert normalize_detail(None) == ""


# ── row_text extraction (real shapes) ────────────────────────────────────────

def test_row_text_all_real_shapes():
    rows = _real_rows()
    assert row_text(rows[0]) == _REPLY            # v3 completionText
    assert row_text(rows[2]) == _REPLY            # transcript text blocks
    assert row_text(rows[3]) == _USER_PREAMBLED   # string content
    assert row_text(rows[4]) == "hello - I'm in a meeting"  # finalPromptText


# ── the incident: 5 visible rows must collapse to 2 ──────────────────────────

def test_incident_rows_collapse_to_one_agent_one_user():
    out = collapse_duplicate_brain_rows(_real_rows())
    ids = [r["id"] for r in out]
    assert len(out) == 2, ids
    # richest survivors: the transcript copies (cost on the reply, the
    # Telegram-card user turn), never the echoes
    assert "cc-msg:23bba84e-615c-48ff-8acc-b58a97c2135b" in ids
    assert "cc-msg:baccb25c-75f7-46d1-bede-c96c6de0705b" in ids


def test_reply_trio_keeps_the_cost_bearing_transcript_row():
    rows = _real_rows()[:3]
    out = collapse_duplicate_brain_rows(rows)
    assert len(out) == 1
    assert out[0]["cost_usd"] == 0.0342745


def test_user_pair_keeps_the_transcript_card_row():
    rows = _real_rows()[3:]
    out = collapse_duplicate_brain_rows(rows)
    assert len(out) == 1
    assert out[0]["event_type"] == "user"


# ── must-NOT-collapse guards ─────────────────────────────────────────────────

def test_distinct_texts_survive():
    rows = _real_rows()
    rows[4]["data"]["finalPromptText"] = "a totally different message"
    rows[4]["data"]["data"]["finalPromptText"] = "a totally different message"
    out = collapse_duplicate_brain_rows(rows)
    assert any(r["event_type"] == "prompt.submitted" for r in out)


def test_same_short_text_in_different_sessions_survives():
    a = copy.deepcopy(_real_rows()[4])
    b = copy.deepcopy(_real_rows()[4])
    b["id"] = "other-id"
    b["session_id"] = "ffffffff-0000-0000-0000-000000000000"
    b["ts"] = "2026-07-31T15:48:38.906Z"
    out = collapse_duplicate_brain_rows([a, b])
    assert len(out) == 2


def test_same_text_far_apart_survives():
    a = copy.deepcopy(_real_rows()[4])
    b = copy.deepcopy(_real_rows()[4])
    b["id"] = "other-id"
    b["ts"] = "2026-07-31T16:30:00.000Z"  # ~42 min later: a re-utterance
    out = collapse_duplicate_brain_rows([a, b])
    assert len(out) == 2


def test_empty_and_broken_rows_never_raise():
    assert collapse_duplicate_brain_rows([]) == []
    # rows with missing/odd fields must pass through, never raise
    out = collapse_duplicate_brain_rows([{"id": "x"}, {"data": 42}])
    assert len(out) == 2


# ── the /api/brain-history UI-shape path uses the same engine ────────────────

def test_routes_collapse_handles_preambled_user_pair():
    from routes.brain import _collapse_duplicate_brain_events
    events = [
        {"type": "USER", "src": _SID[:32], "sessionId": _SID,
         "time": "2026-07-31T15:48:39.551Z", "detail": _USER_PREAMBLED,
         "tokens": 0},
        {"type": "PROMPT.SUBMITTED", "src": _SID[:32], "sessionId": _SID,
         "time": "2026-07-31T15:48:37.906Z",
         "detail": "hello - I'm in a meeting", "tokens": 0},
    ]
    out = _collapse_duplicate_brain_events(events)
    assert len(out) == 1
    assert out[0]["type"] == "USER"


def test_routes_collapse_still_collapses_reply_trio():
    from routes.brain import _collapse_duplicate_brain_events
    def mk(t, typ, tok):
        return {"type": typ, "src": _SID[:32], "sessionId": _SID,
                "time": t, "detail": _REPLY, "tokens": tok}
    events = [
        mk("2026-07-31T15:48:42.786Z", "MODEL.COMPLETED", 0),
        mk("2026-07-31T15:48:42.752Z", "MODEL.COMPLETED", 0),
        mk("2026-07-31T15:48:41.657Z", "ASSISTANT", 25),
    ]
    out = _collapse_duplicate_brain_events(events)
    assert len(out) == 1
    assert out[0]["type"] == "ASSISTANT"


# ── generic engine sanity ────────────────────────────────────────────────────

def test_collapse_events_accessor_failure_keeps_items():
    def boom(ev):
        raise RuntimeError("boom")
    items = [{"a": 1}, {"a": 2}]
    out = collapse_events(items, get_src=boom, get_session=boom,
                          get_detail=boom, get_time=boom, get_richness=boom)
    assert out == items


# ── frontend guard: the Telegram pill must unwrap sender blocks ──────────────

def test_appjs_provenance_pill_unwraps_sender_object():
    """String(meta.sender) on a sender BLOCK rendered "[object Object]" in
    the channel pill. Assert the unwrap guard stays in _provenancePillHtml."""
    import pathlib
    js = (pathlib.Path(__file__).resolve().parents[1]
          / "clawmetry" / "static" / "js" / "app.js").read_text()
    fn = js.split("function _provenancePillHtml", 1)[1][:2500]
    assert "typeof senderVal === 'object'" in fn
    assert ".name || senderVal.username" in fn
