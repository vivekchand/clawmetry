"""Sealing a session so a colleague can read it.

This is the only path by which one person's session becomes readable by their
colleagues, and the key choice IS the design:

* with an organisation key, the trace is sealed so every member can open it,
  and the cloud stores ciphertext it cannot read;
* WITHOUT one, nothing is uploaded. Sealing with this machine's own key would
  produce a blob no colleague could open, and the share would sit there looking
  successful forever. A share that cannot be read is worse than one that
  plainly failed.

That second case is the one worth a test: it is silent, it looks like success
from every angle the user can see, and it is exactly what a "just use whatever
key we have" implementation would do.

Cloud half: clawmetry-cloud#2127 (REQ-CLOUD-TS-003).
"""

from __future__ import annotations

import importlib

import pytest


@pytest.fixture
def sync_mod(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "e.duckdb"))
    monkeypatch.delenv("CLAWMETRY_ORG_KEY", raising=False)
    import clawmetry.sync as sync
    importlib.reload(sync)
    return sync


@pytest.fixture
def captured(sync_mod, monkeypatch):
    """Record what the daemon would POST, and feed it one fake session."""
    posts = []
    monkeypatch.setattr(sync_mod, "_post",
                        lambda path, body, key=None, **kw: posts.append((path, body)),
                        raising=False)

    def fake_dispatch(shape, args):
        assert shape == "transcript"
        return {"rows": [{"event_type": "message", "data": {"role": "user",
                                                            "content": "hello"}}],
                "count": 1}

    import routes.local_query as lq
    monkeypatch.setattr(lq, "_dispatch", fake_dispatch, raising=False)
    return posts


ORG = "b3BlbmNsYXctb3JnLWtleS0zMi1ieXRlcy1sb25nISE"  # 32 bytes, urlsafe b64


def test_a_trace_is_sealed_with_the_ORGANISATION_key(sync_mod, captured):
    from clawmetry import org_key

    cfg = {"api_key": "cm_x", "encryption_key": "NODEKEY",
           org_key.CONFIG_FIELD: ORG}
    sync_mod._seal_shared_traces(cfg, ["claude_code:aaa"])

    assert len(captured) == 1
    path, body = captured[0]
    assert path == "/ingest/shared-trace"
    assert body["session_id"] == "claude_code:aaa"
    assert body["key_fingerprint"] == org_key.fingerprint(ORG)
    # It opens with the ORGANISATION key, which is what makes it readable by a
    # colleague. If it opened with the node key, only this machine could.
    opened = sync_mod.decrypt_payload(body["blob"], ORG)
    assert opened["count"] == 1
    assert opened["rows"][0]["data"]["content"] == "hello"


def test_the_plaintext_never_appears_in_what_is_uploaded(sync_mod, captured):
    from clawmetry import org_key
    cfg = {"api_key": "cm_x", org_key.CONFIG_FIELD: ORG}
    sync_mod._seal_shared_traces(cfg, ["claude_code:aaa"])
    _path, body = captured[0]
    import json as _j
    assert "hello" not in _j.dumps(body)


def test_without_an_organisation_key_NOTHING_is_uploaded(sync_mod, captured):
    """The silent-failure case. Uploading a node-key blob would look like a
    successful share to everyone involved and be unreadable by the colleague
    it was shared with."""
    cfg = {"api_key": "cm_x", "encryption_key": "NODEKEY"}
    sync_mod._seal_shared_traces(cfg, ["claude_code:aaa"])
    assert captured == []


def test_a_session_with_no_events_is_skipped_rather_than_sealed_empty(
        sync_mod, monkeypatch, captured):
    from clawmetry import org_key
    import routes.local_query as lq
    monkeypatch.setattr(lq, "_dispatch",
                        lambda shape, args: {"rows": [], "count": 0},
                        raising=False)
    sync_mod._seal_shared_traces({"api_key": "cm_x", org_key.CONFIG_FIELD: ORG},
                                 ["claude_code:empty"])
    assert captured == []


def test_one_unreadable_session_does_not_stop_the_others(sync_mod, monkeypatch,
                                                          captured):
    """Per-session failures must never take down the heartbeat or the rest of
    the batch."""
    from clawmetry import org_key
    import routes.local_query as lq
    calls = {"n": 0}

    def flaky(shape, args):
        calls["n"] += 1
        if args.get("session_id") == "bad":
            raise RuntimeError("duckdb invalidated")
        return {"rows": [{"event_type": "message", "data": {"content": "ok"}}],
                "count": 1}

    monkeypatch.setattr(lq, "_dispatch", flaky, raising=False)
    sync_mod._seal_shared_traces({"api_key": "cm_x", org_key.CONFIG_FIELD: ORG},
                                 ["bad", "good"])
    assert [b["session_id"] for _p, b in captured] == ["good"]


def test_a_burst_of_shares_cannot_eat_a_whole_check_in(sync_mod, captured):
    from clawmetry import org_key
    sync_mod._seal_shared_traces({"api_key": "cm_x", org_key.CONFIG_FIELD: ORG},
                                 ["s%d" % i for i in range(40)])
    assert len(captured) == 5
