"""An unreadable local store must never render as "you have no data" (#5534).

On a real node 2026-09-05 a contended read through the daemon query proxy
timed out and every tab said the same confident thing at once: Sessions
"No Claude Code sessions have a transcript yet" under its own header
counting **61 sessions**; ``/api/model-attribution`` ``{"model_count": 0}``
over a store holding thousands of events; the Agents panel "The AI is idle."

A spinner says wait. An error says something is wrong. An empty state says
*you have no data* — a positive claim about the user's own work — and when
the truth is "I could not read it", that claim is false and is
indistinguishable from data loss to the person reading it.

The Cost and Efficiency Analytics blueprint already names the field that
carries the distinction (``store_available``) and a handful of endpoints set
it. These tests pin the mechanism that makes it universal instead of
per-endpoint, because the reason this sat unfixed is that
``local_store_via_daemon`` has ~490 call sites and none of them can be
trusted to remember:

1. only a round trip we actually attempted and lost marks the store
   unreachable (no daemon, or being the daemon, is the supported direct-open
   path and must NOT raise the flag);
2. a direct-open fallback that answers clears it;
3. ``dashboard.py`` stamps ``store_available: false`` onto any ``/api/*``
   JSON object that did not answer the question itself, plus a header the
   frontend can read without cloning multi-MB response bodies;
4. the tabs named in the issue branch on the field instead of drawing their
   empty state.
"""
from __future__ import annotations

import json
import urllib.error
from pathlib import Path

import pytest
from flask import Flask

REPO = Path(__file__).resolve().parents[1]


@pytest.fixture
def lq():
    import routes.local_query as lq
    return lq


@pytest.fixture
def ctx():
    """A request context: the flag's whole lifetime is one request."""
    app = Flask(__name__)
    with app.test_request_context("/api/anything"):
        yield app


# ── 1. what counts as unreachable ───────────────────────────────────────────


def test_a_lost_round_trip_marks_the_store_unreachable(lq, ctx, monkeypatch):
    """The exact 2026-09-05 shape: the daemon is there, the read times out."""
    monkeypatch.setattr(lq, "_cached_discovery", lambda: {"port": 1, "token": "t"})
    monkeypatch.setattr(lq, "_invalidate_daemon_cache", lambda: None)

    def _boom(req):
        raise urllib.error.URLError("timed out")

    monkeypatch.setattr(lq, "_urlopen_retry", _boom)
    assert lq.store_available() is True
    assert lq.local_store_via_daemon("query_sessions", limit=5) is None
    assert lq.store_available() is False


def test_a_daemon_that_refuses_the_shape_is_unreachable_too(lq, ctx, monkeypatch):
    """Reproduced deterministically in the issue by leaving the daemon on an
    older build: a shape mismatch, not a timeout, but the same false zeros."""
    monkeypatch.setattr(lq, "_cached_discovery", lambda: {"port": 1, "token": "t"})
    monkeypatch.setattr(lq, "_urlopen_retry", lambda req: {"error": "unknown method"})
    assert lq.local_store_via_daemon("query_brand_new_shape") is None
    assert lq.store_available() is False


def test_no_daemon_at_all_is_not_unreachability(lq, ctx, monkeypatch):
    """Single-process boots (tests, dev mode, `python3 dashboard.py`) have no
    daemon and read the store directly. Flagging them would put a permanent
    warning on a dashboard whose data is entirely fine."""
    monkeypatch.setattr(lq, "_cached_discovery", lambda: None)
    assert lq.local_store_via_daemon("query_sessions", limit=5) is None
    assert lq.store_available() is True


def test_a_direct_open_that_answers_clears_the_flag(ctx, monkeypatch):
    """The store demonstrably WAS readable from this process, so the response
    is not the false-empty this flag exists to prevent."""
    import routes.local_query as lq
    import routes.sessions as rs

    lq.note_store_unreachable()
    assert lq.store_available() is False

    class _Store:
        def query_sessions(self, **kw):
            return [{"session_id": "s1"}]

    monkeypatch.setattr(lq, "local_store_via_daemon", lambda *a, **k: None)
    import clawmetry.local_store as ls
    monkeypatch.setattr(ls, "get_store", lambda **kw: _Store())

    assert rs._ls_call("query_sessions", limit=5) == [{"session_id": "s1"}]
    assert lq.store_available() is True


def test_a_null_fallback_does_not_clear_the_flag(ctx, monkeypatch):
    """The bug the unit tests missed and a live reproduction caught.

    Under a standard install ``local_store.get_store()`` does not open DuckDB
    at all — it hands back a ``_ProxyStore`` that forwards to the SAME daemon.
    So a dead daemon reaches ``_ls_call``'s "direct-open fallback" as a silent
    ``None``, and clearing on "no exception raised" cleared the very flag the
    proxy had just set: against a SIGSTOPped daemon holding a real DuckDB,
    ``/api/transcripts`` still answered ``{"transcripts": []}`` with no flag.
    Only a non-``None`` result proves the store was readable.
    """
    import routes.local_query as lq
    import routes.sessions as rs

    lq.note_store_unreachable()

    class _DeadProxyStore:
        def query_sessions(self, **kw):
            return None

    monkeypatch.setattr(lq, "local_store_via_daemon", lambda *a, **k: None)
    import clawmetry.local_store as ls
    monkeypatch.setattr(ls, "get_store", lambda **kw: _DeadProxyStore())

    assert rs._ls_call("query_sessions", limit=5) is None
    assert lq.store_available() is False


def test_the_flag_does_not_leak_between_requests(lq):
    """It is scoped to a request, so a worker thread's next job starts clean."""
    app = Flask(__name__)
    with app.test_request_context("/api/a"):
        lq.note_store_unreachable()
        assert lq.store_available() is False
    with app.test_request_context("/api/b"):
        assert lq.store_available() is True


# ── 2. the response says so ─────────────────────────────────────────────────


def _stamp(body, path="/api/model-attribution", mimetype="application/json"):
    import dashboard as _d
    app = Flask(__name__)
    with app.test_request_context(path):
        import routes.local_query as lq
        lq.note_store_unreachable()
        resp = app.response_class(
            json.dumps(body), mimetype=mimetype,
        )
        return _d._stamp_store_available(resp)


def test_an_unreachable_read_stamps_the_json_and_a_header():
    """``{"models": []}`` from an unreadable store is the lie. It ships with
    the correction attached, so no handler has to remember to add it."""
    resp = _stamp({"models": [], "model_count": 0})
    assert resp.headers["X-CM-Store-Available"] == "false"
    assert json.loads(resp.get_data())["store_available"] is False


def test_a_handler_that_answers_for_itself_is_left_alone():
    """review/bench/quality/cohort already compute the field; the stamp must
    not overwrite a considered answer with a blanket one."""
    resp = _stamp({"queue": [], "store_available": True})
    assert json.loads(resp.get_data())["store_available"] is True


def test_a_healthy_request_is_untouched():
    """Only ever adds ``false``. Silence stays silence, so no existing
    response shape, snapshot slice or parity test moves."""
    import dashboard as _d
    app = Flask(__name__)
    with app.test_request_context("/api/model-attribution"):
        resp = _d._stamp_store_available(
            app.response_class(json.dumps({"models": []}), mimetype="application/json")
        )
    assert "X-CM-Store-Available" not in resp.headers
    assert "store_available" not in json.loads(resp.get_data())


def test_a_non_json_or_top_level_list_response_is_not_rewritten():
    """A list has nowhere to put the key and text/html is not ours to edit —
    the header still carries the fact."""
    resp = _stamp([1, 2, 3])
    assert resp.headers["X-CM-Store-Available"] == "false"
    assert json.loads(resp.get_data()) == [1, 2, 3]

    resp = _stamp({"a": 1}, mimetype="text/html")
    assert resp.headers["X-CM-Store-Available"] == "false"
    assert resp.get_data() == b'{"a": 1}'


def test_non_api_paths_are_never_touched():
    """Static assets and the HTML shell keep their bytes exactly."""
    import dashboard as _d
    app = Flask(__name__)
    with app.test_request_context("/static/js/app.js"):
        import routes.local_query as lq
        lq.note_store_unreachable()
        resp = _d._stamp_store_available(
            app.response_class(json.dumps({"a": 1}), mimetype="application/json")
        )
    assert "X-CM-Store-Available" not in resp.headers


# ── 3. the tabs branch on it ────────────────────────────────────────────────


APP_JS = REPO / "clawmetry" / "static" / "js" / "app.js"


def test_the_frontend_reads_the_header_not_the_body():
    """Cloning and re-parsing every API response — including the multi-MB
    event scans — to look for one field is the request-cost regression
    FLYWHEEL forbids. The banner reads a header instead."""
    src = APP_JS.read_text(encoding="utf-8")
    assert "X-CM-Store-Available" in src
    assert "cmStoreUnreachableHtml" in src
    assert "cmRetryStoreRead" in src


@pytest.mark.parametrize("marker", [
    # Sessions — "No Claude Code sessions have a transcript yet" under a
    # header counting 61.
    "var emptyMsg = (data && data.store_available === false)",
    # Cost — {"model_count": 0} over thousands of events.
    "if (data && data.store_available === false) {\n      ['model-primary'",
    # Brain — an empty stream over a store full of activity.
    "if (data && data.store_available === false) {\n      var _bhUnEl",
    # Agents — "The AI is idle."
    "if (data && data.store_available === false) return cmStoreUnreachableHtml(",
])
def test_each_surface_named_in_the_issue_branches_before_its_empty_state(marker):
    assert marker in APP_JS.read_text(encoding="utf-8"), marker


def test_the_banner_exists_in_the_live_template():
    """FLYWHEEL 0a.4: dashboard.py defines DASHBOARD_HTML twice and only the
    second renders, via templates/partials/*.html. UI added anywhere else
    never reaches a user."""
    partial = REPO / "clawmetry" / "templates" / "partials" / "banners.html"
    assert 'id="store-unreachable-banner"' in partial.read_text(encoding="utf-8")
