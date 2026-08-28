"""Delegated usage: pricing work a runtime handed to another vendor.

The rules under test are the ones that keep this honest rather than merely
working. A Grok Bot's own spend is unmeasurable and stays that way; what is
measurable is the work it delegated to the operator's OWN Cursor cloud agents,
which Cursor meters and bills. Getting that slightly wrong produces a number
that looks like an answer and is not one, so each rule below has a test that
fails loudly rather than quietly.
"""
from __future__ import annotations

import json
import os
import stat

import pytest

from clawmetry.delegated_usage import (
    CURSOR,
    SOURCE_API,
    SOURCE_OTEL,
    DelegatedUsage,
    DelegatedUsageStore,
    is_delegated_agent_id,
    price,
)

AGENT = "bc-2056f523-bee7-4df9-b5fa-142770d4ed25"
OTHER = "bc-3d55eb90-6a62-4712-aa56-bc201843ed40"


@pytest.fixture
def store() -> DelegatedUsageStore:
    return DelegatedUsageStore()


def _usage(agent_id=AGENT, **kw) -> DelegatedUsage:
    base = dict(agent_id=agent_id, source=SOURCE_API,
                input_tokens=1000, output_tokens=500)
    base.update(kw)
    return DelegatedUsage(**base)


# ── the id shape ────────────────────────────────────────────────────────────


@pytest.mark.parametrize("bad", [
    "sess-123", "abc", "", None, 12345, "bc-", "bc-short",
    "0198f2a1-1111-7000-8000-000000000001",   # a plain uuid session id
])
def test_only_cursor_cloud_agent_ids_are_accepted(bad):
    """An OTLP conversation id can be anything at all.

    Every runtime that exports OTel sends `session.id`, so a loose check would
    file a Claude Code session's tokens as delegated Cursor spend.
    """
    assert is_delegated_agent_id(bad) is False


def test_a_real_cloud_agent_id_is_accepted():
    assert is_delegated_agent_id(AGENT) is True


# ── attribution is bounded by what we saw locally ───────────────────────────


def test_usage_for_an_unobserved_agent_is_dropped(store):
    """The bound that stops a colleague's agent landing on your session.

    Cursor's push export carries the whole team's traffic. Only agents named in
    a transcript on THIS machine may be attributed.
    """
    assert store.record(_usage()) is False
    assert store.get(AGENT) is None


def test_usage_is_kept_once_the_agent_was_observed(store):
    store.observe([AGENT])
    assert store.record(_usage()) is True
    assert store.get(AGENT) is not None


def test_observe_ignores_ids_that_are_not_agent_ids(store):
    store.observe(["not-an-agent", "", None, AGENT])
    assert store.observed() == {AGENT}


def test_pull_lane_asks_only_about_observed_agents(store, monkeypatch):
    """The connector must never enumerate the operator's Cursor account."""
    import clawmetry.cursor_connector as cc

    store.observe([AGENT])
    monkeypatch.setattr(cc, "get_store", lambda: store)
    monkeypatch.setattr(cc, "load_key", lambda: "key_test")
    monkeypatch.setattr(cc, "_MIN_INTERVAL_SECS", 0)
    asked = []

    def fake_get(path, api_key):
        asked.append(path)
        return {"inputTokens": 10, "outputTokens": 5}

    monkeypatch.setattr(cc, "_get", fake_get)
    cc.sync()
    assert asked == [f"/v1/agents/{AGENT}/usage"]
    assert not any("/v1/agents\n" in p or p == "/v1/agents" for p in asked)


# ── delegated spend is never the session's own spend ────────────────────────


def test_rollup_is_labelled_for_its_vendor_and_kept_separate(store):
    """The crux. A Grok Bot session reports cost_status="unavailable" because
    nobody can price its own reasoning. This figure sits ALONGSIDE that, named
    for the vendor. Nothing here may present itself as the session's cost.
    """
    store.observe([AGENT])
    store.record(_usage())
    roll = store.rollup([AGENT])
    assert roll["vendor"] == CURSOR
    assert "costUsd" in roll and "costStatus" in roll
    # A rollup must not masquerade as a Session: no bare 'cost'/'total' key a
    # caller could splice into a session record without noticing.
    assert "cost" not in roll
    assert "sessionId" not in roll


def test_rollup_of_nothing_is_unavailable_not_zero(store):
    """$0.00 reads as "this was free". Absence must not."""
    roll = store.rollup([AGENT])
    assert roll["costUsd"] is None
    assert roll["costStatus"] == "unavailable"
    assert roll["totalTokens"] == 0


def test_rollup_flags_a_floor_when_some_agents_are_unpriced(store):
    store.observe([AGENT, OTHER])
    store.record(_usage())
    unpriced = _usage(OTHER, input_tokens=0, output_tokens=0)
    unpriced.cost_usd = None
    store._by_agent[OTHER] = unpriced          # a recorded-but-unpriceable row
    roll = store.rollup([AGENT, OTHER])
    assert roll["agentsSeen"] == 2
    assert roll["agentsPriced"] == 1
    assert roll["isFloor"] is True


# ── cost carries the label its source earns ─────────────────────────────────


def test_a_known_model_is_derived():
    u = price(_usage(model="claude-sonnet-4"))
    assert u.cost_usd is not None and u.cost_usd > 0
    assert u.cost_status == "derived"


def test_an_unknown_model_is_estimated_not_derived():
    """Cursor returns tokens per agent but NOT the model, so this is the common
    case. Labelling a fallback rate as 'derived' would overstate it.
    """
    u = price(_usage(model=""))
    assert u.cost_status == "estimated"


def test_zero_tokens_price_to_unavailable_not_zero():
    u = price(_usage(input_tokens=0, output_tokens=0))
    assert u.cost_usd is None
    assert u.cost_status == "unavailable"


def test_cache_reads_do_not_bill_as_fresh_input():
    """A long-running cloud agent re-reads the same repo constantly. Charging
    cache reads at the input rate would overstate exactly the shape of work
    this feature exists to report.
    """
    cheap = price(_usage(input_tokens=1000, output_tokens=0, cache_read_tokens=9000))
    dear = price(_usage(input_tokens=10000, output_tokens=0))
    assert cheap.total_tokens == dear.total_tokens
    assert cheap.cost_usd < dear.cost_usd


# ── the credential ──────────────────────────────────────────────────────────


def test_connector_is_off_until_a_key_is_supplied(monkeypatch, tmp_path):
    import clawmetry.cursor_connector as cc

    monkeypatch.delenv("CLAWMETRY_CURSOR_API_KEY", raising=False)
    monkeypatch.setenv("CLAWMETRY_CURSOR_KEY_PATH", str(tmp_path / "cursor.json"))
    assert cc.load_key() == ""
    assert cc.is_enabled() is False


def test_no_outbound_call_without_a_key(monkeypatch, tmp_path):
    """Opt-in means opt-in: absent a key nothing may reach the network."""
    import clawmetry.cursor_connector as cc

    monkeypatch.delenv("CLAWMETRY_CURSOR_API_KEY", raising=False)
    monkeypatch.setenv("CLAWMETRY_CURSOR_KEY_PATH", str(tmp_path / "cursor.json"))
    called = []
    monkeypatch.setattr(cc, "_get", lambda *a, **k: called.append(a) or {})
    out = cc.sync()
    assert out == {"enabled": False, "fetched": 0, "skipped": 0,
                   "reason": "no_api_key"}
    assert called == []
    assert cc.fetch_agent_usage(AGENT) is None
    assert called == []


def test_saved_key_is_owner_only(monkeypatch, tmp_path):
    import clawmetry.cursor_connector as cc

    path = tmp_path / "cursor.json"
    monkeypatch.setenv("CLAWMETRY_CURSOR_KEY_PATH", str(path))
    masked = cc.save_key("key_abcdefghijklmnop")
    mode = stat.S_IMODE(os.stat(path).st_mode)
    assert mode == 0o600, f"key file is {oct(mode)}, must be 0600"
    assert masked == "…mnop"
    assert json.loads(path.read_text())["apiKey"] == "key_abcdefghijklmnop"


def test_only_the_masked_key_is_ever_returned():
    import clawmetry.cursor_connector as cc

    secret = "key_supersecretvalue"
    assert secret not in cc.mask(secret)
    assert cc.mask(secret) == "…alue"


def test_sync_summary_never_contains_the_raw_key(monkeypatch, tmp_path):
    """The summary is logged and displayed, so it must be safe by construction."""
    import clawmetry.cursor_connector as cc

    secret = "key_supersecretvalue"
    monkeypatch.setenv("CLAWMETRY_CURSOR_API_KEY", secret)
    monkeypatch.setattr(cc, "_MIN_INTERVAL_SECS", 0)
    monkeypatch.setattr(cc, "_get", lambda *a, **k: None)
    out = cc.sync()
    assert secret not in json.dumps(out)
    assert out["key"] == "…alue"


def test_forget_key_removes_it(monkeypatch, tmp_path):
    import clawmetry.cursor_connector as cc

    path = tmp_path / "cursor.json"
    monkeypatch.setenv("CLAWMETRY_CURSOR_KEY_PATH", str(path))
    monkeypatch.delenv("CLAWMETRY_CURSOR_API_KEY", raising=False)
    cc.save_key("key_abcdefghijklmnop")
    assert cc.forget_key() is True
    assert cc.load_key() == ""


# ── the push lane ───────────────────────────────────────────────────────────


def test_otlp_join_recognises_the_cursor_conversation_id():
    import dashboard as d

    assert d._delegated_is_agent_id(AGENT) is True
    assert d._delegated_is_agent_id("some-claude-session") is False


def test_otlp_record_needs_the_agent_observed_first(monkeypatch):
    """A team export carries every agent on the Cursor team."""
    import dashboard as d
    from clawmetry.delegated_usage import DelegatedUsageStore

    st = DelegatedUsageStore()
    monkeypatch.setattr("clawmetry.delegated_usage._STORE", st)
    assert d._delegated_record_otel(AGENT, 100, 50, 0, 0) is False
    st.observe([AGENT])
    assert d._delegated_record_otel(AGENT, 100, 50, 0, 0) is True
    assert st.get(AGENT).source == SOURCE_OTEL


def test_otlp_record_with_no_tokens_records_nothing(monkeypatch):
    """A missed attribute name must yield silence, never a zero row.

    Cursor's per-log token attribute names are not published, so this path
    reads a candidate list. This is the test that makes a wrong guess safe.
    """
    import dashboard as d
    from clawmetry.delegated_usage import DelegatedUsageStore

    st = DelegatedUsageStore()
    monkeypatch.setattr("clawmetry.delegated_usage._STORE", st)
    st.observe([AGENT])
    assert d._delegated_record_otel(AGENT, None, None, None, None) is False
    assert st.get(AGENT) is None


# ── the harvest that feeds the bound ────────────────────────────────────────


def test_harvest_reads_agent_ids_off_a_transcript(monkeypatch):
    import clawmetry.sync as sync
    from types import SimpleNamespace
    from clawmetry.delegated_usage import DelegatedUsageStore

    st = DelegatedUsageStore()
    monkeypatch.setattr("clawmetry.delegated_usage._STORE", st)
    events = [
        SimpleNamespace(extra={"customType": "cursor_agent_handoff",
                               "backgroundAgentId": AGENT}),
        SimpleNamespace(extra={}),
        SimpleNamespace(extra={"backgroundAgentId": "junk"}),
        SimpleNamespace(extra=None),
        SimpleNamespace(extra={"backgroundAgentId": AGENT}),      # duplicate
    ]
    got = sync._harvest_delegated_agent_ids(events)
    assert got == [AGENT], "ids must be de-duplicated and validated"
    assert st.is_observed(AGENT)


def test_harvest_never_raises_on_a_bad_event():
    import clawmetry.sync as sync

    assert sync._harvest_delegated_agent_ids(None) == []
    assert sync._harvest_delegated_agent_ids([object()]) == []


# ── the CLI must never hold the raw credential ──────────────────────────────


def test_cli_never_binds_the_raw_key():
    """CodeQL flagged the first version of this, and it was right.

    The CLI used to read the key file itself, which put the credential in a
    local variable one print/traceback away from a terminal and a shell
    history. Reading, storing and masking now happen inside the connector and
    only a masked form comes back, so this is a structural guarantee rather
    than a promise to be careful.
    """
    import inspect
    import clawmetry.cli as cli

    src = inspect.getsource(cli._cmd_cursor)
    assert "load_key()" not in src, "the CLI must not read the raw key"
    assert "save_key(" not in src, "the CLI must not pass a raw key around"
    for leaky in ("{key}", "{api_key}", "{exc}"):
        assert leaky not in src, f"{leaky} in a credential path is a leak channel"


def test_connect_has_no_positional_key_argument():
    """A secret on the command line lands in shell history."""
    import clawmetry.cli as cli

    src = inspect.getsource(cli) if False else open(cli.__file__, encoding="utf-8").read()
    assert '"cursor_key"' not in src, (
        "the positional key argument was removed on purpose: --file or the "
        "env var only"
    )


def test_masked_key_is_the_only_key_derived_value_exposed(monkeypatch, tmp_path):
    import clawmetry.cursor_connector as cc

    secret = "key_supersecretvalue"
    path = tmp_path / "cursor.json"
    monkeypatch.setenv("CLAWMETRY_CURSOR_KEY_PATH", str(path))
    monkeypatch.delenv("CLAWMETRY_CURSOR_API_KEY", raising=False)
    path.write_text(json.dumps({"apiKey": secret}))
    out = cc.masked_key()
    assert secret not in out
    assert out == "…alue"
    assert cc.is_connected() is True


def test_save_from_file_returns_only_the_mask(monkeypatch, tmp_path):
    import clawmetry.cursor_connector as cc

    secret = "key_supersecretvalue"
    src = tmp_path / "k.txt"
    src.write_text(secret + "\n")
    monkeypatch.setenv("CLAWMETRY_CURSOR_KEY_PATH", str(tmp_path / "cursor.json"))
    out = cc.save_key_from_file(str(src))
    assert out == "…alue" and secret not in out


import inspect  # noqa: E402  (used by the guards above)


# ── the UI surface ──────────────────────────────────────────────────────────


@pytest.fixture
def client(monkeypatch, tmp_path):
    import dashboard as d

    monkeypatch.setenv("CLAWMETRY_CURSOR_KEY_PATH", str(tmp_path / "cursor.json"))
    monkeypatch.delenv("CLAWMETRY_CURSOR_API_KEY", raising=False)
    try:
        d.detect_config()
    except Exception:
        pass
    return d.app.test_client()


def test_status_never_returns_the_key(client):
    """Write-only over HTTP: a page that can read this API learns four chars."""
    from clawmetry import cursor_connector as cc

    secret = "key_supersecretvalue"
    cc.save_key(secret)
    r = client.get("/api/cursor/status")
    # Raw bytes, not the parsed body: JSON-escaping must not be what hides it.
    assert secret not in r.get_data(as_text=True)
    assert r.get_json()["maskedKey"] == "…alue"


def test_connect_stores_without_echoing(client):
    secret = "key_anothersecretvalue"
    r = client.post("/api/cursor/connect", json={"apiKey": secret})
    assert r.status_code == 200
    assert r.get_json()["connected"] is True
    assert secret not in r.get_data(as_text=True)


def test_connect_rejects_an_empty_key(client):
    r = client.post("/api/cursor/connect", json={})
    assert r.status_code == 400
    assert r.get_json()["error"] == "missing_api_key"


def test_connect_is_post_only(client):
    """A GET would put the key in a URL, and URLs land in logs and history."""
    assert client.get("/api/cursor/connect").status_code == 405


def test_delegated_usage_endpoint_is_bounded(client):
    """An agent id no local transcript named rolls up to nothing."""
    body = client.get(f"/api/delegated-usage?agents={AGENT}").get_json()
    assert body["costUsd"] is None
    assert body["costStatus"] == "unavailable"


def test_connect_handler_never_binds_the_raw_key():
    """CodeQL flagged the first version of this handler, and it was right.

    The handler must not extract the raw key into a local variable — same
    structural guarantee as the CLI (test_cli_never_binds_the_raw_key).
    Reading, storing and masking all happen inside save_key_from_body; only a
    masked form reaches the handler.
    """
    import inspect
    from routes import delegated

    src = inspect.getsource(delegated.api_cursor_connect)
    assert "save_key(" not in src, (
        "connect handler must use save_key_from_body, not pass a raw key to save_key"
    )
    for leaky in ("api_key =", "= api_key", "{api_key}"):
        assert leaky not in src, (
            f"{leaky!r} in the connect handler is a credential leak channel"
        )


def test_banner_is_scoped_to_the_two_runtimes_and_hides_the_key():
    """The panel must not appear on unrelated runtime views, and the field must
    never be a plain text input that a screenshot or a password manager reads.
    """
    import os

    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    html = open(
        os.path.join(here, "clawmetry", "templates", "partials", "banners.html"),
        encoding="utf-8",
    ).read()
    assert "{ cursor: 1, grok_bot: 1 }" in html
    assert 'id="cm-cursor-key" type="password"' in html
    # The key is POSTed in a body; a query string would leak it to logs.
    assert "apiKey=" not in html
