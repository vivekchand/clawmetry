"""Tests for the snapshot ``sessionTitles`` slice (clawmetry/sync.py).

A session title is CONTENT: where a runtime adapter supplies none, the family
ingest falls back to the session's first user message verbatim. It must
therefore travel inside the E2E-encrypted snapshot and never on the plaintext
``/ingest/sessions`` upload.

Pins the daemon half of the contract (its cloud-side twin is AC-CLOUD-TS-000.1
in the Team Sessions requirement):

* AC-OBS-RSO-032.1 -- a title is never transmitted in a form the service reads.
* AC-OBS-RSO-032.2 -- titles ride the encrypted path, keyed to their session.
* AC-OBS-RSO-032.3 -- no title of its own means carry nothing, not an id.
* AC-OBS-RSO-032.4 -- a title failure degrades to no titles, never a dead
  snapshot.

Context: clawmetry-cloud#2118 — 2,093 rows across 24 accounts were found
holding free-text titles in Cloud SQL in the clear.
"""

from __future__ import annotations

import importlib

import pytest


@pytest.fixture
def sync_with_store(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")

    import clawmetry.local_store as ls
    importlib.reload(ls)
    ls.mark_writer_owner()

    import clawmetry.sync as sync
    importlib.reload(sync)
    yield sync, ls
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def _ingest(store, session_id, title, agent_type="claude_code"):
    store.ingest_session({
        "session_id": session_id,
        "agent_type": agent_type,
        "title": title,
        "status": "ended",
        "started_at": "2026-08-25T09:00:00+00:00",
        "last_active_at": "2026-08-25T10:00:00+00:00",
    })


def test_empty_store_returns_empty_map(sync_with_store):
    sync, _ls = sync_with_store
    assert sync._build_session_titles_snapshot() == {}


def test_title_is_keyed_by_full_session_id(sync_with_store):
    """The cloud joins this onto rows keyed by the FULL namespaced id.

    AC-OBS-RSO-032.2 -- keyed so a title can be matched to its session.

    Keying by the bare id (what the desk-device slice does, for its own
    consumer) would silently fail to join and the cloud would render nothing.
    """
    sync, ls = sync_with_store
    store = ls.get_store()
    _ingest(store, "claude_code:11111111-2222-3333-4444-555555555555",
            "how needed is the network drive mounting here?")
    store.flush()

    titles = sync._build_session_titles_snapshot()
    assert titles == {
        "claude_code:11111111-2222-3333-4444-555555555555":
            "how needed is the network drive mounting here?",
    }


def test_bare_identifier_is_not_carried_as_a_title(sync_with_store):
    """An identifier is not a title.

    AC-OBS-RSO-032.3 -- 89.6% of production rows carry an id as their 'title'.

    Carrying those here would duplicate the plaintext row for no gain and
    inflate a snapshot every dashboard poll downloads.
    """
    sync, ls = sync_with_store
    store = ls.get_store()
    sid = "codex:aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    _ingest(store, sid, sid)                      # title == full id
    _ingest(store, "codex:ffffffff-1111-2222-3333-444444444444",
            "ffffffff-1111-2222-3333-444444444444")   # title == bare id
    store.flush()

    assert sync._build_session_titles_snapshot() == {}


def test_title_is_truncated_so_the_snapshot_stays_small(sync_with_store):
    sync, ls = sync_with_store
    store = ls.get_store()
    _ingest(store, "cursor:99999999-8888-7777-6666-555555555555", "x" * 500)
    store.flush()

    titles = sync._build_session_titles_snapshot()
    assert len(next(iter(titles.values()))) == 120


def test_a_broken_store_yields_an_empty_slice_not_a_crash(sync_with_store,
                                                          monkeypatch):
    """A broken store costs the titles, not the snapshot.

    AC-OBS-RSO-032.4 -- every other tab on the hosted dashboard rides this
    same payload, so one bad slice must not take them all down.
    """
    sync, ls = sync_with_store

    def _boom(*_a, **_kw):
        raise RuntimeError("duckdb invalidated")

    monkeypatch.setattr(ls.get_store(), "query_sessions_table", _boom)
    assert sync._build_session_titles_snapshot() == {}
