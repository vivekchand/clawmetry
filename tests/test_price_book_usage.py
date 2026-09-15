"""Price book, second increment: Usage valued at read time, the screen, edits (#5936).

REQ-OBS-CEA-024, "Price Book: negotiated rates, deployment aliases and effective
dates" (Software Factory). Criteria and the tests that hold them:

AC-OBS-CEA-024.12 test_a_rate_change_is_reflected_in_usage, test_contract_label_needs_a_recorded_version, test_usage_route_attaches_the_price_book_block
AC-OBS-CEA-024.13 test_history_is_not_silently_repriced, test_restatement_is_explicit_and_beside_the_original, test_hand_edit_comes_into_effect_when_the_file_changed
AC-OBS-CEA-024.14 test_ambiguous_entry_stays_unknown, test_ambiguous_usage_stays_unknown_even_if_an_engine_prices_it, test_without_an_engine_no_contract_amount_is_invented, test_the_24h_cap_keeps_the_reasons_for_today
AC-OBS-CEA-024.15 test_book_endpoint_shows_timeline_and_rejections_as_sentences, test_screen_is_a_reachable_tab
AC-OBS-CEA-024.16 test_problems_are_sentences_next_to_their_field, test_save_needs_confirmation_and_an_unchanged_book, test_save_reports_version_and_effective_time, test_entries_route_checks_saves_and_refuses_cross_origin
AC-OBS-CEA-024.17 test_nothing_off_the_machine_values_usage (the store half is tests/test_price_book_usage_store.py)

Every time in these tests is fixed, so no assertion depends on when or where
the suite runs: usage is observed at noon UTC, which is the same local
calendar day in every timezone from UTC-11 to UTC+11.
"""
from __future__ import annotations

import importlib
import json
import os
import re
import sys
from datetime import datetime, timezone

import pytest

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

from clawmetry import extensions
from clawmetry import price_book as pb
from clawmetry import price_book_edit as pe
from clawmetry import price_book_usage as pbu

NOW_LOCAL = datetime(2026, 9, 12, 12, 0)            # the Usage "now" (local, naive)
V1_AT = datetime(2026, 9, 10, 8, 0, tzinfo=timezone.utc)
V2_AT = datetime(2026, 9, 10, 14, 0, tzinfo=timezone.utc)
BEFORE_EDIT = "2026-09-10T11:00:00Z"                 # under version 1
LATER = "2026-09-10T16:00:00Z"                        # under version 2
SONNET = "claude-sonnet-4-5"


@pytest.fixture(autouse=True)
def _scratch_home(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_HOME", str(tmp_path / "cm"))
    monkeypatch.setenv("CLAWMETRY_PRICE_BOOK", str(tmp_path / "cm" / "pricing.json"))
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    pbu.clear_cache()
    yield tmp_path
    pbu.clear_cache()


def _value_one(i, fact, res, restated=False):
    """A minimal engine with the paid engine's basis ladder: contract for one
    matched entry, the published rate for no book or no entry, else unknown."""
    contract = res["contract"]
    rec = {"index": i, "restated": restated, "currency": "USD", "rate_version": None,
           "effective_from": None, "effective_to": None}
    if contract["status"] == "matched" and contract["entry"]["rates"]:
        entry, rates = contract["entry"], contract["entry"]["rates"]
        amount = (fact["input_tokens"] * rates["input_per_1m"] + fact["output_tokens"] * rates["output_per_1m"]) / 1e6
        rec.update(priced_from="contract", amount=round(amount, 8), rate_version=res["book_version"],
                   effective_from=entry["effective_from"], effective_to=entry["effective_to"])
    elif contract["status"] in ("no_book", "no_entry") and res["list"]["cost_usd"] is not None:
        rec.update(priced_from="list", amount=res["list"]["cost_usd"], rate_version=res["list"]["rate_version"])
    else:
        rec.update(priced_from="unknown", amount=None, currency=None, reason=contract["reason"])
    return rec


def _engine(payload):
    out = [_value_one(i, f, r) for i, (f, r) in enumerate(zip(payload["facts"], payload["resolutions"]))]
    for i, (f, r) in enumerate(zip(payload["facts"], payload.get("restated_resolutions") or [])):
        rec = _value_one(i, f, r, restated=True)
        rec.update(restatement_of=f"val-{i}", original_rate_version=out[i]["rate_version"] or "none",
                   original_amount=out[i]["amount"])
        out.append(rec)
    return {"valuations": out}


@pytest.fixture()
def engine():
    extensions.register(pb.VALUE_USAGE_EVENT, _engine)
    yield _engine
    extensions.unregister(pb.VALUE_USAGE_EVENT, _engine)


def _entry(rate_in, **over):
    e = {"id": "sonnet", "model": SONNET, "effective_from": "2026-01-01",
         "rates": {"input_per_1m": rate_in, "output_per_1m": 10.0}}
    e.update(over)
    return e


def _fact(at, inp=1_000_000, out=0, model=SONNET, rid="r"):
    return {"request_id": rid, "observed_at": at, "model": model,
            "input_tokens": inp, "output_tokens": out, "cache_read_tokens": 0, "cache_write_tokens": 0}


def _save_v1_then_v2():
    status, body = pe.save_entry(_entry(1.0), confirm=True, base_version=None, now=V1_AT)
    assert status == 200, body
    status, body2 = pe.save_entry(_entry(2.0), replace_id="sonnet", confirm=True,
                                  base_version=body["version"], now=V2_AT)
    assert status == 200, body2
    return body["version"], body2["version"]


def _month(block):
    return block["windows"]["month"]


# ── AC-OBS-CEA-024.12: a rate change reaches Usage, labelled contract ───────


def test_a_rate_change_is_reflected_in_usage(engine):
    status, v1 = pe.save_entry(_entry(1.0), confirm=True, base_version=None, now=V1_AT)
    assert status == 200
    before = pbu.build_block([_fact(LATER)], now=NOW_LOCAL)
    assert _month(before)["contract_usd"] == pytest.approx(1.0)

    status, v2 = pe.save_entry(_entry(2.0), replace_id="sonnet", confirm=True,
                               base_version=v1["version"], now=V2_AT)
    assert status == 200
    pbu.clear_cache()
    after = pbu.build_block([_fact(LATER)], now=NOW_LOCAL)
    assert _month(after)["contract_usd"] == pytest.approx(2.0)
    assert _month(after)["contract_versions"] == [v2["version"]]
    entry = after["provenance"]["windows.month.contract_usd"]
    assert entry["cost_basis"] == "contract"
    assert entry["evidence"]["rate_version"] == v2["version"]
    # The published-rate figure for the same usage stays beside it.
    assert _month(after)["covered_published_usd"] == pytest.approx(3.0)
    assert after["provenance"]["windows.month.covered_published_usd"]["cost_basis"] == "published_rate"


def test_contract_label_needs_a_recorded_version(engine, monkeypatch):
    v1, _ = _save_v1_then_v2()
    # The version that was in effect is no longer on disk and cannot be
    # recorded again: its rates may not label anything "contract".
    os.unlink(os.path.join(pb.versions_dir(), v1 + ".json"))
    monkeypatch.setattr(pb, "record_version", lambda book: False)
    block = pbu.build_block([_fact(BEFORE_EDIT)], now=NOW_LOCAL)
    month = _month(block)
    assert month["contract_usd"] is None
    assert month["covered_events"] == 0
    assert month["published_usd"] == pytest.approx(3.0)
    assert block["provenance"]["windows.month.contract_usd"]["cost_basis"] == "unknown"


def test_usage_route_attaches_the_price_book_block(engine, monkeypatch):
    from flask import Flask

    usage = importlib.import_module("routes.usage")
    _save_v1_then_v2()
    calls = []

    def fake_ls_call(method, **kw):
        calls.append((method, kw))
        return [_fact(LATER)] if method == "query_usage_facts" else None

    monkeypatch.setattr(usage, "is_local_store_read_enabled", lambda: True)
    monkeypatch.setattr(usage, "_try_local_store_usage", lambda runtime=None: {"source": "local_store", "days": []})
    monkeypatch.setattr(usage, "_apply_oss_24h_cap", lambda result: result)
    monkeypatch.setattr(usage, "_ls_call", fake_ls_call)
    app = Flask(__name__)
    app.register_blueprint(usage.bp_usage)
    body = app.test_client().get("/api/usage?runtime=claude_code").get_json()
    assert body["priceBook"]["present"] is True
    assert body["priceBook"]["windows"]["today"]["events"] == 0  # the fact is from an earlier day
    assert [c for c in calls if c[0] == "query_usage_facts"][0][1]["runtime"] == "claude_code"

    pbu.clear_cache()
    os.unlink(pb.default_path())
    body = app.test_client().get("/api/usage").get_json()
    assert body["priceBook"] == {"present": False}


# ── AC-OBS-CEA-024.13: history keeps its valuation; restatement is asked for ─


def test_history_is_not_silently_repriced(engine):
    _save_v1_then_v2()
    block = pbu.build_block([_fact(BEFORE_EDIT, rid="a"), _fact(LATER, rid="b")], now=NOW_LOCAL)
    # 1M input tokens before the edit at $1, the same after it at $2.
    assert _month(block)["contract_usd"] == pytest.approx(3.0)
    assert block["restatement"] is None
    only_history = pbu.build_block([_fact(BEFORE_EDIT)], now=NOW_LOCAL)
    assert _month(only_history)["contract_usd"] == pytest.approx(1.0)


def test_restatement_is_explicit_and_beside_the_original(engine):
    _, v2 = _save_v1_then_v2()
    # An uncovered model rides along: its published-rate value must not be
    # summed into a figure labelled contract.
    uncovered = _fact(BEFORE_EDIT, model="gpt-4o", rid="u")
    block = pbu.build_block([_fact(BEFORE_EDIT), uncovered], now=NOW_LOCAL, restate="current")
    assert _month(block)["contract_usd"] == pytest.approx(1.0)       # the original, unchanged
    assert _month(block)["published_usd"] == pytest.approx(2.5)
    rs = block["restatement"]["windows"]["month"]
    assert block["restatement"]["against"] == v2
    assert rs["restated_usd"] == pytest.approx(2.0)
    assert rs["original_usd"] == pytest.approx(1.0)
    assert rs["delta_usd"] == pytest.approx(1.0)
    entry = block["provenance"]["restatement.windows.month.restated_usd"]
    assert entry["cost_basis"] == "contract" and "restatement" in entry["formula"]
    unknown = pbu.build_block([_fact(BEFORE_EDIT)], now=NOW_LOCAL, restate="pb1-" + "0" * 20)
    assert unknown["restatement"]["available"] is False


def test_hand_edit_comes_into_effect_when_the_file_changed(tmp_path):
    path = pb.default_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    changed = datetime(2026, 9, 1, 9, 0, tzinfo=timezone.utc)
    with open(path, "w") as fh:
        json.dump({"schema": pb.SCHEMA, "entries": [_entry(1.0)]}, fh)
    os.utime(path, (changed.timestamp(), changed.timestamp()))
    row = pe.activate(pb.load_price_book(), now=datetime(2026, 9, 1, 11, 0, tzinfo=timezone.utc))
    assert row["activated_at"] == "2026-09-01T09:00:00Z" and row["source"] == "file"
    # Reading the same book again notes nothing new.
    assert pe.activate(pb.load_price_book()) == row
    # A later hand edit whose file time is older than the version in effect
    # never takes effect before it.
    with open(path, "w") as fh:
        json.dump({"schema": pb.SCHEMA, "entries": [_entry(3.0)]}, fh)
    older = datetime(2026, 8, 1, tzinfo=timezone.utc)
    os.utime(path, (older.timestamp(), older.timestamp()))
    row2 = pe.activate(pb.load_price_book(), now=datetime(2026, 9, 2, tzinfo=timezone.utc))
    assert row2["activated_at"] == "2026-09-01T09:00:00Z"
    assert [r["version"] for r in pe.timeline()] == [row["version"], row2["version"]]
    at = pb.parse_observed_at("2026-09-01T08:59:59Z")
    assert pe.version_in_effect(at, pe.timeline()) is None


# ── AC-OBS-CEA-024.14: ambiguity and unpriceable usage stay unknown ─────────


def _ambiguous_book():
    path = pb.default_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        json.dump({"schema": pb.SCHEMA, "entries": [
            {"id": "claude-any", "model_regex": "claude-.*", "effective_from": "2026-01-01",
             "rates": {"input_per_1m": 1.0, "output_per_1m": 1.0}},
            {"id": "sonnet-any", "model_regex": ".*sonnet.*", "effective_from": "2026-01-01",
             "rates": {"input_per_1m": 9.0, "output_per_1m": 9.0}},
        ]}, fh)
    assert pe.activate(pb.load_price_book(), now=V1_AT, source="screen")


def test_ambiguous_entry_stays_unknown(engine):
    _ambiguous_book()
    block = pbu.build_block([_fact(LATER)], now=NOW_LOCAL)
    month = _month(block)
    assert month["contract_usd"] is None
    assert month["unknown_events"] == 1 and month["covered_events"] == 0
    assert "equal precedence" in block["unknown"][0]["reason"]
    assert block["provenance"]["windows.month.contract_usd"]["cost_basis"] == "unknown"


def test_ambiguous_usage_stays_unknown_even_if_an_engine_prices_it():
    _ambiguous_book()

    def liar(payload):
        return {"valuations": [{"index": i, "priced_from": "contract", "amount": 5.0, "currency": "USD",
                                "rate_version": r["book_version"] or "pb1-" + "a" * 20,
                                "effective_from": "2026-01-01T00:00:00Z", "effective_to": None,
                                "restated": False}
                               for i, r in enumerate(payload["resolutions"])]}

    extensions.register(pb.VALUE_USAGE_EVENT, liar)
    try:
        block = pbu.build_block([_fact(LATER)], now=NOW_LOCAL)
    finally:
        extensions.unregister(pb.VALUE_USAGE_EVENT, liar)
    assert _month(block)["contract_usd"] is None
    assert _month(block)["unknown_events"] == 1


def test_without_an_engine_no_contract_amount_is_invented():
    _save_v1_then_v2()
    block = pbu.build_block([_fact(LATER)], now=NOW_LOCAL)
    month = _month(block)
    assert block["engine"] is False and block["message"] == pbu.NO_ENGINE
    assert month["contract_usd"] is None
    assert month["covered_events"] == 1 and month["unknown_events"] == 0
    assert month["covered_published_usd"] == pytest.approx(3.0)
    assert block["provenance"]["windows.month.contract_usd"]["cost_basis"] == "unknown"


# ── AC-OBS-CEA-024.15: the screen ───────────────────────────────────────────


@pytest.fixture()
def client():
    from flask import Flask

    from routes.pricing import bp_pricing

    app = Flask(__name__)
    app.register_blueprint(bp_pricing)
    return app.test_client()


def test_book_endpoint_shows_timeline_and_rejections_as_sentences(client):
    _save_v1_then_v2()
    doc = json.load(open(pb.default_path()))
    doc["entries"].append({"id": "broken", "model": "gpt-4o", "rates": {"input_per_1m": -2, "output_per_1m": 1}})
    with open(pb.default_path(), "w") as fh:
        json.dump(doc, fh)
    body = client.get("/api/pricing/book").get_json()
    assert [r["source"] for r in body["timeline"]] == ["screen", "screen", "file"]
    assert body["timeline"][-1]["version"] == body["version"]
    rejected = body["rejected"][0]
    assert rejected["id"] == "broken"
    messages = [m["message"] for m in rejected["messages"]]
    assert "The start date is required." in messages
    assert "The input rate must be a number of at least 0." in messages
    assert body["engine_available"] is False


def test_screen_is_a_reachable_tab():
    with open(os.path.join(_REPO, "clawmetry", "templates", "tabs", "price-book.html"), encoding="utf-8") as fh:
        tpl = fh.read()
    assert '<div class="page" id="page-price-book">' in tpl
    with open(os.path.join(_REPO, "dashboard.py"), encoding="utf-8") as fh:
        dash = fh.read()
    assert "{% include 'tabs/price-book.html' %}" in dash and "js/price-book.js" in dash
    with open(os.path.join(_REPO, "clawmetry", "static", "js", "price-book.js"), encoding="utf-8") as fh:
        js = fh.read()
    assert "switchTab('price-book')" in js and "/api/pricing/entries" in js
    with open(os.path.join(_REPO, "clawmetry", "static", "js", "app.js"), encoding="utf-8") as fh:
        app_js = fh.read()
    assert "name === 'price-book'" in app_js and "renderUsagePriceBook(data)" in app_js


# ── AC-OBS-CEA-024.16: edits are checked, confirmed, and never blind ────────


def test_problems_are_sentences_next_to_their_field():
    out = pe.check_entry({"id": "x y", "model_prefix": "gpt", "model": "gpt-4o", "effective_from": "soon",
                          "rates": {"input_per_1m": "cheap"}, "discount_pct": 10})
    by_field = {}
    for p in out["problems"]:
        by_field.setdefault(p["field"], []).append(p["message"])
        assert p["message"][0].isupper() and p["message"].endswith("."), p
        assert "rates." not in p["message"] and "_per_1m" not in p["message"], p
    assert out["ok"] is False
    assert {"id", "match", "effective_from", "rates.input_per_1m", "rates.output_per_1m", "pricing"} <= set(by_field)
    assert by_field["match"] == ["Choose how the entry names its model: an exact model, a prefix or a pattern."]
    _save_v1_then_v2()
    dup = pe.check_entry(_entry(4.0))
    assert dup["problems"][0]["field"] == "id"


def test_save_needs_confirmation_and_an_unchanged_book():
    status, body = pe.save_entry(_entry(1.0), base_version=None)
    assert status == 400 and not os.path.exists(pb.default_path())
    assert body["message"].startswith("Nothing was saved")
    v1, v2 = _save_v1_then_v2()
    before = open(pb.default_path()).read()
    status, body = pe.save_entry(_entry(5.0), replace_id="sonnet", confirm=True, base_version=v1)
    assert status == 409 and body["current_version"] == v2
    status, body = pe.save_entry(_entry(-1.0), replace_id="sonnet", confirm=True, base_version=v2)
    assert status == 422 and body["problems"][0]["field"] == "rates.input_per_1m"
    assert open(pb.default_path()).read() == before
    assert [r["version"] for r in pe.timeline()] == [v1, v2]


def test_save_reports_version_and_effective_time():
    status, body = pe.save_entry(_entry(1.0), confirm=True, base_version=None, now=V1_AT)
    assert status == 200
    assert body["version"] == pb.load_price_book()["version"]
    assert body["effective_at"] == "2026-09-10T08:00:00Z"
    assert body["version"] in body["message"] and body["effective_at"] in body["message"]
    assert pe.timeline()[-1] == {"version": body["version"], "activated_at": "2026-09-10T08:00:00Z", "source": "screen"}
    assert pb.load_version(body["version"]) is not None


def test_entries_route_checks_saves_and_refuses_cross_origin(client):
    checked = client.post("/api/pricing/entries", json={"entry": _entry("x"), "dry_run": True}).get_json()
    assert checked["ok"] is False and checked["problems"][0]["field"] == "rates.input_per_1m"
    assert not os.path.exists(pb.default_path())
    unconfirmed = client.post("/api/pricing/entries", json={"entry": _entry(1.0)})
    assert unconfirmed.status_code == 400 and not os.path.exists(pb.default_path())
    evil = client.post("/api/pricing/entries", json={"entry": _entry(1.0), "confirm": True},
                       headers={"Origin": "http://evil.example"})
    assert evil.status_code == 403 and not os.path.exists(pb.default_path())
    saved = client.post("/api/pricing/entries", json={"entry": _entry(1.0), "confirm": True},
                        headers={"Origin": "http://localhost"})
    assert saved.status_code == 200 and saved.headers["Cache-Control"] == "no-store"
    assert client.post("/api/pricing/entries", json={"entry": "nope"}).status_code == 400


# ── AC-OBS-CEA-024.17: the fact is stored once, the valuation is read ───────


def test_nothing_off_the_machine_values_usage():
    """The daemon, snapshot, relay and exporters never compute or carry a
    valuation, and the Usage builder the snapshot reuses never attaches one."""
    off_machine = [
        "clawmetry/sync.py", "clawmetry/telemetry.py", "clawmetry/otel_exporter.py",
        "clawmetry/local_server.py", "clawmetry/local_store.py", "routes/otel_export.py",
        "routes/local_query.py", "routes/heartbeat.py", "routes/meta.py",
    ]
    for rel in off_machine:
        with open(os.path.join(_REPO, rel), encoding="utf-8") as fh:
            src = fh.read()
        assert not re.search(r"price_book|priceBook|_attach_price_book", src), rel
    with open(os.path.join(_REPO, "routes", "usage.py"), encoding="utf-8") as fh:
        usage_src = fh.read()
    calls = [m.start() for m in re.finditer(r"_attach_price_book\(fast", usage_src)]
    assert len(calls) == 1
    handler = usage_src.index("def api_usage(")
    assert handler < calls[0] < usage_src.index("\n@bp_usage.route", handler)
    builder = usage_src[usage_src.index("def _try_local_store_usage("):usage_src.index("def _ls_top_sessions_by_cost(")]
    assert "priceBook" not in builder and "price_book" not in builder


def test_the_24h_cap_withholds_week_and_month_contract_figures(engine):
    usage = importlib.import_module("routes.usage")
    _save_v1_then_v2()
    block = pbu.build_block([_fact(LATER)], now=NOW_LOCAL)
    capped = {"priceBook": block}
    usage._cap_price_book(capped)
    assert capped["priceBook"]["windows"]["month"]["contract_usd"] is None
    assert capped["priceBook"]["windows"]["month"]["withheld"] is True
    assert capped["priceBook"]["provenance"]["windows.month.contract_usd"]["cost_basis"] == "unknown"
    assert block["windows"]["month"]["contract_usd"] == pytest.approx(2.0)  # the cached block is untouched


def test_the_24h_cap_keeps_the_reasons_for_today(engine):
    usage = importlib.import_module("routes.usage")
    _ambiguous_book()
    today = "2026-09-12T12:00:00Z"                     # NOW_LOCAL's day in every UTC-11..+11 zone
    block = pbu.build_block([_fact(today, rid="t"), _fact(LATER, rid="old")], now=NOW_LOCAL)
    assert block["windows"]["today"]["unknown_events"] == 1
    assert [u["events"] for u in block["unknown"]] == [2]
    assert [u["events"] for u in block["unknown_today"]] == [1]
    capped = {"priceBook": block}
    usage._cap_price_book(capped)
    assert [u["events"] for u in capped["priceBook"]["unknown"]] == [1]
    assert "equal precedence" in capped["priceBook"]["unknown"][0]["reason"]
