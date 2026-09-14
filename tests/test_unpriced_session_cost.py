"""#5979 — a session with tokens but no priced event must render as unknown
cost on the Usage tab's "Top Sessions by Cost" table, never as a confident
$0.00.

Reproduction: on a normal (daemon-backed) install, ``/api/usage`` serves
``routes/usage.py::_ls_top_sessions_by_cost``, the ``source: "local_store"``
fast path. It reads ``query_sessions()`` rows, whose own SQL already folds
"no priced event" and "genuinely free" into the same ``cost_usd == 0.0``
(``clawmetry/local_store.py``: ``COALESCE(SUM(cost_usd), 0) AS cost_usd_d``),
then unconditionally re-coerced that to ``0.0`` again on the way out. A
session on an unrecognised/local model with real tokens showed "$0.00" next
to a non-zero token count instead of "unpriced".

The fix mirrors the heuristic ``routes/components.py::_brain_call_costs``
already uses for the same shape of problem on the Flow brain panel: tokens
with a zero recorded cost is unpriced, not free; zero tokens and zero cost is
a legitimately idle session and stays $0.00. The frontend
(``clawmetry/static/js/provenance.js::figure()``) already renders a ``null``
value as "not available" — this only needed the backend to stop discarding
the distinction.
"""
import importlib

usage = importlib.import_module("routes.usage")


def test_top_sessions_unpriced_cost_is_none_not_zero(monkeypatch):
    def fake_ls_call(method, **kw):
        if method == "query_sessions":
            return [
                # An unrecognised/local model: tokens recorded, no price —
                # query_sessions's own COALESCE(SUM(cost_usd), 0) already
                # reports this as 0.0, same shape as _brain_call_costs'
                # "tokens but no price" case in routes/components.py.
                {"session_id": "unpriced-sess", "cost_usd": 0.0,
                 "token_count": 55000},
                # No tokens and $0 cost is a legitimately idle session, not
                # an unpriced one — must still read $0.00.
                {"session_id": "idle-sess", "cost_usd": 0.0,
                 "token_count": 0},
                # The normal case: priced and non-zero.
                {"session_id": "priced-sess", "cost_usd": 4.5,
                 "token_count": 1000},
            ]
        if method == "query_events":
            return [{"model": "m"}]
        return []
    monkeypatch.setattr(usage, "_ls_call", fake_ls_call)

    rows = {r["session_id"]: r for r in usage._ls_top_sessions_by_cost(limit=20)}
    assert rows["unpriced-sess"]["total_cost_usd"] is None, rows["unpriced-sess"]
    assert rows["unpriced-sess"]["total_tokens"] == 55000
    assert rows["idle-sess"]["total_cost_usd"] == 0.0
    assert rows["priced-sess"]["total_cost_usd"] == 4.5
