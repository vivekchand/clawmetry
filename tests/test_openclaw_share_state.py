"""OpenClaw public-share state (#5746).

The shapes asserted here are taken from ``openclaw@2026.9.3``, not invented:

* ``publicShare`` is in ``PRIVATE_SESSION_ENTRY_KEYS`` and is stripped by
  ``stripPrivateSessionEntryFields()``, so no session-list response carries
  it; ``session.members.list`` is the read method that does.
* ``SessionPublicShareSchema = {token: ^v1\\.[A-Za-z0-9_-]+$, createdAt: int}``.

The token is a live read capability for the user's conversation — OpenClaw
builds the public URL straight from it — so several tests below exist purely
to prove it never reaches anything we persist or serve.
"""
from __future__ import annotations

from types import SimpleNamespace

from clawmetry.adapters import openclaw_share as share

#: A realistic upstream object, token shaped like the real pattern.
LIVE_SHARE = {"token": "v1.tOkEn-SECRET_do_not_store", "createdAt": 1720000000000}


# --------------------------------------------------------------- share_fields

def test_share_fields_keeps_the_verdict_and_drops_the_token():
    fields = share.share_fields(LIVE_SHARE)
    assert fields["shared"] is True
    assert fields["share_created_at"] == 1720000000.0
    assert "token" not in fields
    assert "SECRET" not in repr(fields)


def test_share_fields_reports_an_unshared_session_as_false():
    # The RPC answered; there is simply no publication. That is a real
    # verdict, distinct from "we never asked".
    assert share.share_fields(None) == {"shared": False}
    assert share.share_fields({}) == {"shared": True}  # present-but-empty == published


def test_created_at_accepts_seconds_and_milliseconds():
    # Upstream types createdAt as a bare Integer, so the unit is not stated.
    assert share.share_fields({"createdAt": 1720000000000})["share_created_at"] == 1720000000.0
    assert share.share_fields({"createdAt": 1720000000})["share_created_at"] == 1720000000.0


def test_created_at_garbage_is_dropped_not_guessed():
    for bad in ("", "nope", -1, 0, None, True):
        assert "share_created_at" not in share.share_fields({"createdAt": bad})


# ---------------------------------------------------------- fetch_share_state

def test_fetch_uses_the_per_session_members_list_rpc():
    calls = []

    def rpc(method, params):
        calls.append((method, params))
        return {"sessionKey": params["sessionKey"], "publicShare": LIVE_SHARE}

    state = share.fetch_share_state(["sess-a", "sess-b"], rpc=rpc)

    assert [c[0] for c in calls] == ["session.members.list"] * 2
    assert [c[1]["sessionKey"] for c in calls] == ["sess-a", "sess-b"]
    assert state["sess-a"]["shared"] is True
    assert "token" not in state["sess-a"]


def test_fetch_omits_sessions_the_rpc_could_not_answer():
    # None is what the gateway helper returns on error/timeout/unknown method.
    # Recording False here would tell Guard a published session is private.
    def rpc(method, params):
        return None if params["sessionKey"] == "sess-b" else {"publicShare": None}

    state = share.fetch_share_state(["sess-a", "sess-b"], rpc=rpc)

    assert state["sess-a"] == {"shared": False}
    assert "sess-b" not in state


def test_fetch_survives_a_raising_rpc():
    def rpc(method, params):
        if params["sessionKey"] == "boom":
            raise RuntimeError("socket wedged")
        return {"publicShare": None}

    state = share.fetch_share_state(["boom", "ok"], rpc=rpc)
    assert "boom" not in state
    assert state["ok"] == {"shared": False}


def test_fetch_is_capped(monkeypatch):
    monkeypatch.setenv("CLAWMETRY_OPENCLAW_SHARE_MAX", "2")
    seen = []

    def rpc(method, params):
        seen.append(params["sessionKey"])
        return {"publicShare": None}

    state = share.fetch_share_state([f"s{i}" for i in range(10)], rpc=rpc)
    assert len(seen) == 2
    # Capped-out sessions are unknown, not false.
    assert len(state) == 2


def test_fetch_passes_agent_id_when_given():
    got = {}

    def rpc(method, params):
        got.update(params)
        return {"publicShare": None}

    share.fetch_share_state(["s1"], rpc=rpc, agent_id="main")
    assert got["agentId"] == "main"


def test_a_gateway_that_answers_nothing_says_so_once(monkeypatch, caplog):
    # The v4 scope gap (raw token -> no operator.read) makes every probe come
    # back None. An empty share column must be explained, not silent.
    monkeypatch.setattr(share, "_warned_no_answer", False)
    with caplog.at_level("WARNING"):
        state = share.fetch_share_state(["a", "b"], rpc=lambda m, p: None)
    assert state == {}
    assert "session.members.list" in caplog.text
    assert "UNKNOWN" in caplog.text


# ----------------------------------------------------------------- share_extra

def test_share_extra_omits_everything_when_there_is_no_verdict():
    # The daemon never probed this session (no gateway, cloud container,
    # capped out). The UI must not be handed a confident "not shared".
    assert share.share_extra({}) == {}
    assert share.share_extra(None) == {}
    assert share.share_extra({"model": "x"}) == {}


def test_share_extra_renders_a_negative_verdict():
    assert share.share_extra({"shared": False}) == {"isShared": False}


def test_share_extra_renders_a_positive_verdict():
    extra = share.share_extra({"shared": True, "share_created_at": 1720000000.0})
    assert extra == {
        "isShared": True,
        "shareCreatedAt": 1720000000.0,
        "shareVisibility": "public-read-only",
    }


# ---------------------------------------------------------------- apply helpers

def test_payloads_keep_existing_extra_and_lose_the_private_metadata_key():
    payloads = [{
        "id": "s1",
        "extra": {"model": "test"},
        "_metadata": {"shared": True, "share_created_at": 1720000000.0},
    }]
    share.apply_share_state_to_payloads(payloads)

    assert payloads[0]["extra"]["model"] == "test"
    assert payloads[0]["extra"]["isShared"] is True
    assert "_metadata" not in payloads[0]


def test_payloads_without_a_verdict_are_left_alone():
    payloads = [{"id": "s1", "extra": {"model": "test"}, "_metadata": {"model": "t"}}]
    share.apply_share_state_to_payloads(payloads)

    assert "isShared" not in payloads[0]["extra"]
    assert "_metadata" not in payloads[0]


def test_apply_share_state_stamps_session_objects():
    sessions = [SimpleNamespace(id="s1", extra={}), SimpleNamespace(id="s2", extra={})]
    share.apply_share_state(sessions, {"s1": {"shared": True}})

    assert sessions[0].extra["isShared"] is True
    assert sessions[1].extra == {}  # no verdict -> untouched


# ------------------------------------------------------------------ daemon pass

def test_daemon_pass_stamps_rows_and_never_carries_the_token(monkeypatch):
    from clawmetry import sync

    monkeypatch.setattr(
        share, "fetch_share_state",
        lambda keys, **kw: {"key-a": share.share_fields(LIVE_SHARE)},
    )
    rows = [
        {"session_id": "a", "session_key": "key-a"},
        {"session_id": "b", "session_key": "key-b"},
    ]
    sync._annotate_public_share(rows)

    assert rows[0]["shared"] is True
    assert rows[0]["share_created_at"] == 1720000000.0
    assert "token" not in rows[0]
    assert "SECRET" not in repr(rows)
    assert "shared" not in rows[1]  # unprobed stays unknown


def test_daemon_pass_can_be_switched_off(monkeypatch):
    from clawmetry import sync

    monkeypatch.setenv("CLAWMETRY_OPENCLAW_SHARE", "0")
    monkeypatch.setattr(
        share, "fetch_share_state",
        lambda keys, **kw: {"key-a": {"shared": True}},
    )
    rows = [{"session_id": "a", "session_key": "key-a"}]
    sync._annotate_public_share(rows)
    assert "shared" not in rows[0]


# ------------------------------------------------------- store round-trip
#
# The bug this feature originally shipped with was not a wrong value: it was a
# field that never survived the plumbing, under tests that mocked the very
# layer that dropped it. These two go through the REAL DuckDB ingest so that a
# whitelist or COALESCE that quietly eats the verdict fails here.

import importlib

import pytest


@pytest.fixture
def store(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "1")
    import clawmetry.local_store as ls
    importlib.reload(ls)
    ls.mark_writer_owner()
    yield ls
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def _metadata_for(ls, session_id):
    rows = ls.get_store().query_sessions_table(agent_type="openclaw", limit=50)
    for r in rows:
        if r.get("session_id") == session_id:
            return r.get("metadata") or {}
    raise AssertionError(f"{session_id} not in the sessions table")


def test_verdict_survives_ingest_and_the_token_never_lands_in_duckdb(store):
    from clawmetry import sync

    rows = [{"session_id": "sess-a", "session_key": "key-a",
             **share.share_fields(LIVE_SHARE)}]
    sync._local_ingest_sessions_batch(rows, "node-1")

    meta = _metadata_for(store, "sess-a")
    assert share.share_extra(meta) == {
        "isShared": True,
        "shareCreatedAt": 1720000000.0,
        "shareVisibility": "public-read-only",
    }
    rows = store.get_store().query_sessions_table(limit=50)
    assert "SECRET" not in repr(rows)
    # ``total_tokens`` legitimately contains the substring, so check the key.
    for r in rows:
        assert "token" not in (r.get("metadata") or {})


def test_a_false_verdict_survives_and_an_unprobed_session_stays_unknown(store):
    from clawmetry import sync

    # ``shared: False`` is falsey, and the metadata blob is built by a
    # truthiness filter — the exact shape of bug that would silently turn a
    # real "not published" answer into "we never asked".
    sync._local_ingest_sessions_batch([
        {"session_id": "sess-f", "session_key": "key-f", "shared": False},
        {"session_id": "sess-u", "session_key": "key-u"},
    ], "node-1")

    assert share.share_extra(_metadata_for(store, "sess-f")) == {"isShared": False}
    assert share.share_extra(_metadata_for(store, "sess-u")) == {}
