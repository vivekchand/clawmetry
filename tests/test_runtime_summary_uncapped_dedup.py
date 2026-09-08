"""Guard: /api/runtime-summary must read the deduped, uncapped rollup.

The route's own docstring says it "mirrors the daemon ``runtimeSummary``
snapshot slice". It did not. ``sync._build_runtime_summary`` reads
``query_model_rollup()``; this route re-implemented the aggregate as a raw
``_scan_events_slim(limit=20000)`` loop, which is wrong twice:

* **Capped.** The 20k budget is global and most-recent-first, so once one
  runtime passes it the quieter runtimes are starved out of the response and
  the loud one is itself undercounted.
* **Double-counted.** OpenClaw v3 emits BOTH an ``assistant``/``message`` row
  and a sibling ``model.completed`` row per turn, each stamped with the same
  cost. Summing raw events bills that turn twice. Every other aggregator
  (``query_aggregates``, ``query_model_rollup``, ``query_sessions_table``)
  reads through the shared envelope-dedup CTE; this route did not.

These tests pin the contract at the route level: given a store whose raw
events double-count and whose rollup does not, the route must report the
rollup's number.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import routes.usage as usage  # noqa: E402


# One turn, emitted as the v3 twin: same cost on both rows. A raw sum bills
# $2.00; the deduped rollup bills $1.00.
_TWIN_EVENTS = [
    {"session_id": "codex:abc", "ts": "2026-09-08T10:00:00Z", "model": "gpt-5",
     "token_count": 100, "cost_usd": 1.0, "event_type": "assistant"},
    {"session_id": "codex:abc", "ts": "2026-09-08T10:00:00Z", "model": "gpt-5",
     "token_count": 100, "cost_usd": 1.0, "event_type": "model.completed"},
]

_ROLLUP = {
    "by_runtime": {
        "codex": {"sessions": 1, "tokens": 100, "cost_usd": 1.0,
                  "last_activity_ms": 1757325600000},
        # A quiet runtime that a most-recent-20k global scan would starve out
        # entirely once codex is loud.
        "goose": {"sessions": 3, "tokens": 4200, "cost_usd": 7.5,
                  "last_activity_ms": 1757325500000},
    },
    "by_runtime_model": [
        {"runtime": "codex", "model": "gpt-5", "turns": 1, "tokens": 100,
         "cost_usd": 1.0, "sessions": 1},
        {"runtime": "goose", "model": "claude-sonnet-5", "turns": 9,
         "tokens": 4200, "cost_usd": 7.5, "sessions": 3},
    ],
}


def _install(monkeypatch, rollup, events):
    """Point the route at a fake store: `rollup` from the proxy, `events` raw."""
    monkeypatch.setattr(usage, "is_local_store_read_enabled", lambda: True)
    monkeypatch.setattr(usage, "_ls_get_store", lambda: object())
    monkeypatch.setattr(
        usage, "_ls_call",
        lambda method, **kw: rollup if method == "query_model_rollup" else None,
    )
    monkeypatch.setattr(usage, "_scan_events_slim", lambda **kw: list(events))


def _call_route():
    """Invoke the view and return its decoded JSON body."""
    from flask import Flask
    app = Flask(__name__)
    with app.test_request_context("/api/runtime-summary"):
        resp = usage.api_runtime_summary()
    return resp.get_json()


def test_cost_is_not_double_counted(monkeypatch):
    _install(monkeypatch, _ROLLUP, _TWIN_EVENTS)
    rts = _call_route()["runtimes"]
    assert rts["codex"]["cost_usd"] == 1.0, (
        "the v3 assistant/model.completed twin was billed twice — the route is "
        "summing raw events instead of the envelope-deduped rollup"
    )
    assert rts["codex"]["tokens"] == 100
    assert rts["codex"]["turns"] == 1


def test_quiet_runtime_is_not_starved_by_the_scan_cap(monkeypatch):
    # The raw-event view contains ONLY codex, exactly as a most-recent-20k
    # global scan would look on a node where codex is loud. goose must still
    # appear, because the rollup is uncapped.
    _install(monkeypatch, _ROLLUP, _TWIN_EVENTS)
    rts = _call_route()["runtimes"]
    assert "goose" in rts, (
        "a runtime absent from the capped event scan vanished from the "
        "response — the route is not reading the uncapped rollup"
    )
    assert rts["goose"]["cost_usd"] == 7.5
    assert rts["goose"]["sessions"] == 3
    assert rts["goose"]["primary_model"] == "claude-sonnet-5"


def test_falls_back_to_the_scan_when_the_daemon_lacks_the_rollup(monkeypatch):
    # Upgrade skew: dashboard restarted, daemon has not. The proxy answers
    # None for the newer method. Stale numbers beat a confident empty page.
    _install(monkeypatch, None, _TWIN_EVENTS)
    rts = _call_route()["runtimes"]
    assert "codex" in rts, (
        "an older daemon that cannot answer query_model_rollup must degrade "
        "to the legacy scan, not to an empty Overview"
    )


def test_empty_store_yields_empty_not_none(monkeypatch):
    _install(monkeypatch, {"by_runtime": {}, "by_runtime_model": []}, [])
    body = _call_route()
    assert body["runtimes"] == {}
    assert body["_source"] == "local_store"
