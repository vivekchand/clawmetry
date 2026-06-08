"""Guard: turn anatomy now carries per-span and per-turn cost.

Before #web-accuracy (2026-06-08) ``routes/turn_anatomy._build_turns`` emitted
only duration/tokens — there was NO cost field anywhere (span, turn, or
response), so the Turn-anatomy waterfall could never show which span was
expensive even though every event is daemon-stamped with ``cost_usd`` at
ingest. These tests pin that cost is read off the events and rolled up.
"""

from __future__ import annotations

from datetime import datetime, timezone

import routes.turn_anatomy as ta


def _ev(et, ts, *, cost=0.0, tokens=0, model="", role="", **data):
    d = {"role": role} if role else {}
    d.update(data)
    return {
        "event_type": et,
        "ts": datetime.fromtimestamp(ts, tz=timezone.utc).isoformat(),
        "cost_usd": cost,
        "token_count": tokens,
        "model": model,
        "data": d,
    }


def test_turn_cost_rolls_up_from_events():
    rows = [
        _ev("prompt.submitted", 1000, role="user", text="hello"),
        _ev("model.completed", 1002, cost=12.0, tokens=20000, model="claude-opus-4-8"),
        _ev("model.completed", 1004, cost=7.86, tokens=12760, model="claude-opus-4-8"),
    ]
    turns = ta._build_turns(rows)
    assert len(turns) == 1
    t = turns[0]
    # Turn-level cost = sum of span costs.
    assert round(t["total_cost"], 2) == 19.86
    assert t["total_tokens"] == 32760
    # The expensive span carries its own cost so the UI can highlight it.
    model_spans = [s for s in t["spans"] if s["kind"] in ("model", "reply")]
    assert any(round(s.get("cost") or 0, 2) == 12.0 for s in model_spans)


def test_zero_cost_turn_reports_zero_not_missing():
    rows = [
        _ev("prompt.submitted", 1000, role="user", text="hi"),
        _ev("model.completed", 1001, cost=0.0, tokens=5, model="llama3.2"),
    ]
    turns = ta._build_turns(rows)
    assert turns[0]["total_cost"] == 0.0  # present, not absent
