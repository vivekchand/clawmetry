"""Guard: no dollar amount and no score renders without saying how it was got.

WO-6. ClawMetry has kept this discipline internally for a while (Guard
incidents carry ``spend_basis``, thresholds carry ``threshold_source``,
context windows carry ``confidence``) and shown none of it to the person
reading the number. ``clawmetry/provenance.py`` is the one vocabulary those
collapse into; this file is what stops a new surface from skipping it.

The trap it exists to close, from ``reference_cost_windows_one_definition``:
a failed DuckDB read was published as ``$0.00`` and read as a real result. So
the load-bearing assertions here are the ones about zero:

  * an unknown figure serialises as ``None``, never ``0.0``;
  * a genuine measured ``0.0`` survives untouched and stays badged as
    measured, because a real zero is a fact and must not be hidden either;
  * nothing the badge component renders for an unknown figure contains a
    dollar sign.

The payload guard is AUTO-DISCOVERING on purpose. It does not hold a list of
figures we remembered to label; it walks the real response, recognises money
and score keys by shape, and fails on any it finds with no basis behind it. A
hand-kept list is exactly the thing that drifts.
"""
import json
import os
import re
import shutil
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from clawmetry import provenance

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ── The vocabulary ──────────────────────────────────────────────────────────

def test_four_bases_each_have_a_label_and_a_plain_words_hint():
    assert provenance.BASES == ("measured", "derived", "estimated", "unknown")
    for basis in provenance.BASES:
        assert provenance.BASIS_LABEL[basis]
        hint = provenance.BASIS_HINT[basis]
        assert hint and hint.endswith("."), basis
        # The hint is user-facing copy and the em-dash ban applies to it.
        assert "—" not in hint and "--" not in hint, basis


def test_an_entry_carries_enough_to_reconstruct_the_number():
    entry = provenance.derived(
        "tokens times the rate card", "duckdb:events.cost_usd",
        window="today", inputs={"tokens": 1200})
    assert entry["basis"] == provenance.DERIVED
    assert entry["formula"] and entry["source"]
    assert entry["window"] == "today"
    assert entry["inputs"] == {"tokens": 1200}


def test_a_typo_in_the_basis_degrades_loudly_rather_than_crashing():
    """This runs on the ingest path. A bad basis must not take a tab down,
    and must not quietly pass as a good one either."""
    entry = provenance.figure("mesured", "f", "s")
    assert entry["basis"] == provenance.UNKNOWN
    assert "mesured" in entry["note"]


# ── The zero that is not a zero ─────────────────────────────────────────────

def test_stamp_nulls_a_figure_it_labels_unknown():
    """The whole point. A renderer cannot print $0.00 for a number nobody has
    if the number is not there to print."""
    payload = {"monthCost": 0.0}
    provenance.stamp(payload, {
        "monthCost": provenance.unknown("the local store did not answer")})
    assert payload["monthCost"] is None
    assert payload["provenance"]["monthCost"]["reason"]


def test_a_real_measured_zero_is_left_alone():
    """The opposite failure. An idle day really did cost $0.00, and hiding
    that behind "not available" is its own lie."""
    payload = {"todayCost": 0.0}
    provenance.stamp(payload, {
        "todayCost": provenance.measured("sum over an empty window", "duckdb")})
    assert payload["todayCost"] == 0.0
    assert payload["provenance"]["todayCost"]["basis"] == "measured"


def test_stamp_merges_rather_than_replacing():
    payload = {"a_cost": 1.0, "b_cost": 2.0}
    provenance.stamp(payload, {"a_cost": provenance.measured("f", "s")})
    provenance.stamp(payload, {"b_cost": provenance.derived("f", "s")})
    assert set(payload["provenance"]) == {"a_cost", "b_cost"}


# ── The auto-discovering audit ──────────────────────────────────────────────

@pytest.mark.parametrize("key,kind", [
    ("todayCost", "money"), ("cost_usd", "money"), ("total_cost_usd", "money"),
    ("routing_savings_usd", "money"), ("spend_at_risk_usd", "money"),
    ("reliability_score", "score"), ("score", "score"),
    ("message_count", None), ("tokens", None), ("spend_basis", None),
    ("provenance_version", None), ("session_id", None),
])
def test_figure_keys_are_recognised_by_shape(key, kind):
    assert provenance.figure_kind(key) == kind


def test_audit_names_an_unlabelled_figure_and_where_it_is():
    gaps = provenance.audit_payload({"card": {"weekCost": 12.5}})
    assert [g["path"] for g in gaps] == ["card.weekCost"]


def test_audit_accepts_a_collection_labelled_once():
    """Forty rows priced the same way get one label, not forty."""
    payload = {"sessions": [{"cost_usd": 1.0}, {"cost_usd": 2.0}]}
    provenance.stamp(payload, {
        "sessions[].cost_usd": provenance.derived("f", "s")})
    assert provenance.audit_payload(payload) == []


def test_audit_ignores_a_bool_that_happens_to_end_in_cost():
    assert provenance.audit_payload({"has_cost": True}) == []


def test_assert_labelled_names_every_gap_in_one_message():
    with pytest.raises(AssertionError) as exc:
        provenance.assert_labelled({"aCost": 1.0, "bCost": 2.0}, "demo")
    assert "aCost" in str(exc.value) and "bCost" in str(exc.value)


# ── The vocabularies that came first, mapped exhaustively ───────────────────
#
# These read the CURRENT source rather than a copy of it, so a new source
# value added to the calibrator (or a new spend basis in Guard) fails here
# instead of silently rendering as "no basis".

def _string_literals_assigned_to(path, pattern):
    text = open(os.path.join(REPO, path), encoding="utf-8").read()
    return set(re.findall(pattern, text))


def test_every_guard_spend_basis_maps_to_a_provenance_basis():
    found = _string_literals_assigned_to(
        "clawmetry/detector_money.py", r'basis = "([a-z_]+)"')
    assert found, "detector_money stopped assigning a basis; update this guard"
    for basis in found:
        assert basis in provenance.SPEND_BASIS_TO_PROVENANCE, basis


def test_every_threshold_source_maps_to_a_provenance_basis():
    found = _string_literals_assigned_to(
        "clawmetry/detector_calibration.py", r'sources\[[^\]]+\] = "([a-z_]+)"')
    found |= _string_literals_assigned_to(
        "clawmetry/detector_calibration.py", r'sources = \{k: "([a-z_]+)"')
    assert found, "resolve_thresholds stopped stamping sources"
    for src in found:
        assert src in provenance.THRESHOLD_SOURCE_TO_PROVENANCE, src


def test_every_context_window_confidence_maps_to_a_provenance_basis():
    from clawmetry import context_windows
    for model in ("claude-sonnet-4-5", "gpt-5", "not-a-real-model-xyz"):
        got = context_windows.resolve_context_window(model)
        assert got.confidence in provenance.CONTEXT_CONFIDENCE_TO_PROVENANCE


def test_an_unpriceable_incident_is_unknown_not_free():
    entry = provenance.from_spend_basis("unknown")
    assert entry["basis"] == provenance.UNKNOWN
    assert entry["reason"]


def test_the_rough_spend_basis_is_labelled_estimated_not_measured():
    """``window_fraction`` assumes spend is even across the window, which on
    real sessions attributed most of a $100 session to four failed greps. It
    is context, and the badge has to say so."""
    assert provenance.from_spend_basis("window_fraction")["basis"] == "estimated"
    assert provenance.from_spend_basis("burn_rate")["basis"] == "measured"


# ── The surfaces ────────────────────────────────────────────────────────────
#
# One test per payload builder that renders money. Each asserts the SAME
# thing: walk the real response, and find no figure without a basis.

def test_the_cost_tab_payload_has_a_basis_for_every_figure(monkeypatch):
    import routes.usage as usage_mod

    def _fake_ls_call(method, **kw):
        if method == "query_aggregates":
            return [{"day": "2026-08-25", "token_count": 1000, "cost_usd": 4.0}]
        if method == "query_events":
            return [{"model": "claude-sonnet-4-5", "token_count": 1000,
                     "session_id": "openclaw-1"}]
        if method == "query_sessions":
            return [{"session_id": "openclaw-1", "cost_usd": 4.0,
                     "token_count": 1000, "message_count": 3,
                     "started_at": "2026-08-25T00:00:00"}]
        if method == "query_routing_savings":
            return {"total_savings_usd": 0.5, "by_pair": []}
        if method == "query_daily_usage_splits":
            return []
        return None

    monkeypatch.setattr(usage_mod, "_ls_call", _fake_ls_call)
    payload = usage_mod._try_local_store_usage()
    assert payload is not None
    provenance.assert_labelled(payload, "/api/usage (local store fast path)")


def test_the_snapshot_cost_slice_has_a_basis_for_every_figure():
    """Cloud parity. The hosted dashboard renders THIS payload, not the one
    /api/usage builds, so a badge that shipped only on localhost would be
    absent from the product a trial user is being asked to pay for."""
    from clawmetry import sync
    payload = sync._stamp_daily_usage({
        "days": [{"day": "2026-08-25", "tokens": 10, "cost_usd": 1.0}],
        "today": 10, "week": 10, "month": 10,
        "todayCost": 1.0, "weekCost": 1.0, "monthCost": 1.0,
        "byRuntime": {"openclaw": [{"day": "2026-08-25", "tokens": 10,
                                    "cost_usd": 1.0}]},
    })
    provenance.assert_labelled(payload, "snapshot dailyUsage")


def test_the_snapshot_spending_triple_has_a_basis():
    from clawmetry.sync import _resolve_spending
    live = _resolve_spending(
        {"todayCost": 1.0, "weekCost": 2.0, "monthCost": 3.0}, {})
    for key in ("today", "week", "month"):
        assert provenance.entry_for(live, key)["basis"] == provenance.DERIVED
    stale = _resolve_spending({}, {"today": 1.0, "week": 2.0, "month": 3.0})
    for key in ("today", "week", "month"):
        assert provenance.entry_for(stale, key)["basis"] == provenance.ESTIMATED


def test_withheld_history_is_not_a_run_of_free_days(monkeypatch):
    """The OSS 24h cap used to ZERO the older buckets, which rendered as
    twelve days on which the user spent nothing. Held back is not zero."""
    import routes.usage as usage_mod
    monkeypatch.setattr(usage_mod, "_prov", provenance)

    result = {"days": [{"date": "2026-08-%02d" % d, "tokens": 5, "cost": 1.0}
                       for d in range(11, 25)]}
    provenance.stamp(result, {"days[].cost": provenance.derived("f", "s")})
    import dashboard as _d
    monkeypatch.setattr(_d, "_is_pro_user", lambda: False)

    capped = usage_mod._apply_oss_24h_cap(result)
    withheld = [d for d in capped["days"] if d.get("withheld")]
    assert withheld, "nothing was capped; the fixture is wrong"
    for day in withheld:
        assert day["cost"] is None, "a withheld day still reads as $0.00"
    assert capped["days"][-1]["cost"] == 1.0, "a visible day was clobbered"
    # The un-capped payload is the long-lived cache entry and must not have
    # picked up the cap's note.
    assert "note" not in result["provenance"]["days[].cost"]
    assert "note" in capped["provenance"]["days[].cost"]


def test_the_weekly_digest_labels_what_it_cost_to_write():
    """A digest nobody paid for really did cost nothing, and that zero is a
    measurement. The estimate is the other case, and it says which two
    assumptions are inside it."""
    from clawmetry.insights import WeeklyDigest

    no_llm = WeeklyDigest("t", "a", "b", synthesized=False).to_dict()
    assert no_llm["cost_usd"] == 0.0
    assert no_llm["provenance"]["cost_usd"]["basis"] == "measured"
    assert "no model was called" in no_llm["provenance"]["cost_usd"]["formula"]

    priced = WeeklyDigest("t", "a", "b", synthesized=True,
                          tokens_used=10000, cost_usd=0.09).to_dict()
    entry = priced["provenance"]["cost_usd"]
    assert entry["basis"] == "estimated"
    assert entry["inputs"] == {"tokens_used": 10000}


# ── The component that renders it ───────────────────────────────────────────

PROV_JS = os.path.join(REPO, "clawmetry", "static", "js", "provenance.js")


def _run_node(script):
    node = shutil.which("node")
    if not node:
        pytest.skip("node is not installed")
    src = open(PROV_JS, encoding="utf-8").read()
    prog = "var window = globalThis;\n" + src + "\n" + script
    out = subprocess.run([node, "-e", prog], capture_output=True, text=True,
                         timeout=30)
    assert out.returncode == 0, out.stderr
    return out.stdout.strip()


def test_the_badge_never_prints_a_dollar_amount_for_an_unknown_figure():
    html = _run_node(
        "console.log(window.cmProv.figure(0, "
        "{basis:'unknown', reason:'the store did not answer'}, "
        "{label:'Cost today'}));")
    assert "$" not in html, html
    assert "not available" in html
    assert "cm-fig-unknown" in html
    assert "the store did not answer" in html


def test_the_badge_prints_a_real_measured_zero_as_zero():
    html = _run_node(
        "console.log(window.cmProv.figure(0, {basis:'measured'}, {}));")
    assert "$0.00" in html
    assert "cm-prov-measured" in html


def test_a_null_value_renders_unknown_even_with_a_confident_basis():
    """Belt and braces: the server nulls unknown figures, and the component
    refuses to invent one back even if a basis says measured."""
    html = _run_node(
        "console.log(window.cmProv.figure(null, {basis:'measured'}, {}));")
    assert "$" not in html and "not available" in html


def test_an_unlabelled_figure_is_badged_as_unlabelled_not_silently_passed():
    html = _run_node("console.log(window.cmProv.figure(4.2, null, {}));")
    assert "$4.20" in html
    assert "unlabelled" in html


def test_the_tooltip_carries_the_formula_the_window_and_the_inputs():
    tip = _run_node(
        "console.log(JSON.stringify(window.cmProv.tip({basis:'derived',"
        "formula:'tokens times the rate card',window:'this month',"
        "inputs:{tokens:1200},source:'duckdb:events'}, 'Cost')));")
    text = json.loads(tip)
    assert "Cost" in text
    assert "tokens times the rate card" in text
    assert "this month" in text
    assert "tokens = 1200" in text
    assert "duckdb:events" in text


def test_the_js_and_python_vocabularies_say_the_same_words():
    labels = json.loads(_run_node(
        "console.log(JSON.stringify(window.cmProv.LABEL));"))
    assert labels == provenance.BASIS_LABEL
    hints = json.loads(_run_node(
        "console.log(JSON.stringify(window.cmProv.HINT));"))
    assert hints == provenance.BASIS_HINT


# ── No dead UI ──────────────────────────────────────────────────────────────

def test_the_component_is_loaded_by_the_live_dashboard_before_app_js():
    """``dashboard.py`` defines DASHBOARD_HTML twice and only the SECOND one
    renders. A script tag in the dead first block ships nothing."""
    text = open(os.path.join(REPO, "dashboard.py"), encoding="utf-8").read()
    blocks = [m.start() for m in re.finditer(r"^DASHBOARD_HTML = r\"\"\"",
                                             text, re.M)]
    assert len(blocks) == 2, "the two-DASHBOARD_HTML shape changed; re-check"
    live = text[blocks[1]:]
    prov_at = live.find("js/provenance.js")
    app_at = live.find("js/app.js', v=version")
    assert prov_at != -1, "provenance.js is not loaded by the LIVE template"
    assert app_at != -1
    assert prov_at < app_at, "provenance.js must load before app.js"


def test_the_badge_has_styling_for_every_basis():
    css = open(os.path.join(REPO, "clawmetry", "static", "css",
                            "dashboard.css"), encoding="utf-8").read()
    for basis in provenance.BASES:
        assert ".cm-prov-%s" % basis in css, basis
    # The unknown state must be styled differently from a real figure, or the
    # whole exercise is decorative.
    assert ".cm-fig-unknown" in css
