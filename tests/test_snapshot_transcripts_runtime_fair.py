"""The cloud snapshot must carry a transcript for EVERY runtime, not just the
loudest one (#5643).

Field bug: the hosted Sessions tab said "No Codex sessions have a transcript
yet" under a header counting 15 of them. Two different lanes feed those two
numbers -- the header comes from the uncapped ``/ingest/sessions`` push, the
list comes from the snapshot's ``transcripts`` map. That map was picked on
node-wide recency alone, so on a box with 1866 claude_code sessions and 16
codex ones, all 8 slots went to claude_code every single cycle and codex never
reached the cloud at all.

These guards fail on the pre-fix selection (global window only).
"""
from __future__ import annotations

from unittest.mock import patch

import clawmetry.sync as sync


class _FakeStore:
    """Minimal stand-in for LocalStore's transcript-selection reads."""

    def __init__(self, recent_sids, by_runtime):
        self._recent = list(recent_sids)
        self._by_runtime = list(by_runtime)
        self.per_runtime_calls = []

    def query_events(self, session_id=None, limit=None):
        if session_id is None:
            # Node-wide recency scan: one event per session, newest first.
            return [{"session_id": s, "ts": "2026-09-07T00:00:00+00:00", "id": s}
                    for s in self._recent][:limit or None]
        return [{"session_id": session_id, "ts": "2026-09-07T00:00:00+00:00",
                 "id": session_id + "-e"}]

    def query_recent_sessions_by_runtime(self, per_runtime=2, **_kw):
        self.per_runtime_calls.append(per_runtime)
        out = []
        seen: dict = {}
        for row in self._by_runtime:
            rt = row["runtime"]
            seen[rt] = seen.get(rt, 0) + 1
            if seen[rt] <= per_runtime:
                out.append(row)
        return out


def _transcript_for(sid, n_messages=200):
    return {
        "session_id": sid,
        "messages": [{"role": "user", "content": "m%d" % i, "timestamp": i}
                     for i in range(n_messages)],
    }


def _build(store, **env):
    """Run the real selection against a fake store."""
    sync._TRANSCRIPT_SNAP_CACHE.clear()
    with patch("clawmetry.local_store.get_store", return_value=store), \
         patch("routes.sessions._try_local_store_transcript",
               side_effect=lambda sid, _events=None: _transcript_for(sid)), \
         patch.dict("os.environ", env, clear=False):
        return sync._build_transcripts()


# 20 claude_code sessions monopolise the node-wide recency window ...
_LOUD = ["claude_code:cc-%02d" % i for i in range(20)]
# ... while these two runtimes are quieter but very much present.
_QUIET = [
    {"runtime": "claude_code", "session_id": _LOUD[0], "last_ms": 20},
    {"runtime": "claude_code", "session_id": _LOUD[1], "last_ms": 19},
    {"runtime": "codex", "session_id": "codex:cx-1", "last_ms": 9},
    {"runtime": "codex", "session_id": "codex:cx-2", "last_ms": 8},
    {"runtime": "codex", "session_id": "codex:cx-3", "last_ms": 7},
    {"runtime": "goose", "session_id": "goose:gs-1", "last_ms": 5},
]


def test_quiet_runtimes_reach_the_snapshot():
    out = _build(_FakeStore(_LOUD, _QUIET))
    runtimes = {t.get("runtime") for t in out.values()}
    assert "codex" in runtimes, (
        "codex was starved out of the snapshot by claude_code -- this is the "
        "#5643 field bug: header counts 15, list shows 0")
    assert "goose" in runtimes
    assert "claude_code" in runtimes


def test_reserved_slots_are_bounded_per_runtime():
    store = _FakeStore(_LOUD, _QUIET)
    out = _build(store)
    n_codex = sum(1 for t in out.values() if t.get("runtime") == "codex")
    assert n_codex == sync._snapshot_per_runtime_sessions() == 2, (
        "reserved slots must stay bounded or the encrypted snapshot bloats")
    # The dominant runtime keeps its global window and is not double-counted.
    assert sum(1 for t in out.values() if t.get("runtime") == "claude_code") == 8


def test_reserved_slots_use_the_short_message_cap():
    """Size budget: a reserved slot ships fewer messages than a global one.

    Measured on a 16-runtime box, the reserved slots cost +121 KB raw at cap
    12 versus +427 KB at cap 24, so this is the difference between a snapshot
    that stays shareable and one that does not.
    """
    out = _build(_FakeStore(_LOUD, _QUIET))
    glob = [t for t in out.values() if t.get("runtime") == "claude_code"]
    reserved = [t for t in out.values() if t.get("runtime") == "codex"]
    assert glob and reserved
    assert max(len(t["messages"]) for t in reserved) \
        < max(len(t["messages"]) for t in glob)
    assert max(len(t["messages"]) for t in reserved) \
        <= sync._snapshot_per_runtime_msg_cap()


def test_kill_switch_restores_global_only_selection():
    out = _build(_FakeStore(_LOUD, _QUIET),
                 CLAWMETRY_SNAPSHOT_PER_RUNTIME_SESSIONS="0")
    assert {t.get("runtime") for t in out.values()} == {"claude_code"}
    assert len(out) == 8


def test_store_read_failure_still_ships_the_global_window():
    """Never crash on bad input: a failing per-runtime read degrades to the
    old behaviour instead of emptying the Sessions tab."""
    class _Broken(_FakeStore):
        def query_recent_sessions_by_runtime(self, per_runtime=2, **_kw):
            raise RuntimeError("duckdb went away")

    out = _build(_Broken(_LOUD, _QUIET))
    assert len(out) == 8


def test_reserved_slots_skip_clawmetry_plumbing_sessions():
    rows = list(_QUIET) + [
        {"runtime": "codex", "session_id": "codex:clawmetry-helper", "last_ms": 1},
    ]
    store = _FakeStore(_LOUD, rows)
    with patch("clawmetry.config.hide_clawmetry_session",
               side_effect=lambda sid: "clawmetry-" in sid):
        out = _build(store)
    assert not any("clawmetry-helper" in sid for sid in out)


def test_freshness_cache_covers_every_slot():
    """The cache is what keeps this off the daemon's CPU budget (FLYWHEEL 1e).
    Sized below the slot count it would rebuild every transcript every cycle."""
    assert sync._TRANSCRIPT_SNAP_CACHE_MAX >= 8 + 2 * 26


def test_per_runtime_read_is_allowlisted_on_the_daemon_proxy():
    """An unlisted method is a SILENT no-op through the proxy: the dashboard
    process would get None and the reserved slots would quietly vanish."""
    import routes.local_query as lq

    names = [n for n in dir(lq) if "ALLOW" in n.upper() or "METHOD" in n.upper()]
    haystack = "".join(str(getattr(lq, n)) for n in names)
    assert "query_recent_sessions_by_runtime" in haystack, (
        "add the method to the __local_query__ allowlist in routes/local_query.py")


# ── The other half of #5643: the empty state must not contradict the header ──
#
# The header's session count and the Sessions list are fed by different lanes,
# so "No Codex sessions have a transcript yet" could sit directly under a
# header reading "Codex - 15 sessions". A first-time trial user reads that as
# a broken product. The copy now says which of the two numbers it means.

import os
import re

_APP_JS = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..",
    "clawmetry", "static", "js", "app.js")


def _app_js() -> str:
    with open(_APP_JS, encoding="utf-8") as fh:
        return fh.read()


def test_runtime_empty_state_reads_the_header_count():
    src = _app_js()
    m = re.search(r"function _cmRuntimeEmptyMsg\(rt\)\s*\{(.*?)\n\}\n", src,
                  re.S)
    assert m, "the runtime-scoped empty state must live in one named helper"
    body = m.group(1)
    assert "_cmGlobalRtCounts" in body, (
        "the empty state must consult the same count the header shows, or it "
        "can keep claiming zero under a header that says 15")
    assert "known > 0" in body


def test_runtime_empty_state_is_wired_into_the_list():
    src = _app_js()
    assert "_rtNoTx\n      ? _cmRuntimeEmptyMsg(_rtFilter)" in src, (
        "loadTranscripts must render the helper for the runtime-scoped case")
    assert "sessions have a transcript yet" not in src, (
        "the old copy contradicted the header count")


def test_runtime_empty_state_copy_has_no_ai_tells():
    """FLYWHEEL: no em-dashes or double-dashes in user-facing copy."""
    import json
    locales = os.path.join(os.path.dirname(_APP_JS), "..", "locales", "en.json")
    with open(locales, encoding="utf-8") as fh:
        cat = json.load(fh)
    keys = [k for k in cat if k.startswith("transcripts.runtime_")
            or k == "transcripts.pick_all_runtimes"]
    assert keys, "the empty-state strings must be translatable"
    for k in keys:
        assert "—" not in cat[k], k
        assert "--" not in cat[k], k


def test_runtime_empty_state_has_a_singular_form():
    """"This machine has 1 Codex sessions" is the kind of sloppiness a
    first-time user reads as "nobody looked at this screen"."""
    import json
    locales = os.path.join(os.path.dirname(_APP_JS), "..", "locales", "en.json")
    with open(locales, encoding="utf-8") as fh:
        cat = json.load(fh)
    base = "transcripts.runtime_counted_but_empty"
    assert base + "_one" in cat and base + "_other" in cat
    assert "1 {label} session," in cat[base + "_one"]
