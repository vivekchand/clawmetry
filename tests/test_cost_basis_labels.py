"""Guard: a cost figure says what kind of money it is (REQ-OBS-CEA-025).

vivekchand/clawmetry#5937. ``clawmetry/provenance.py`` already says how a
figure was computed. It did not say whether the figure is a bill, and the
Usage tab told subscription users "$0 billed to you" about a bill ClawMetry
has never seen. These tests hold three properties:

* every cost figure the named surfaces emit carries a financial basis, and
  none claims contract or actual spend without the evidence behind it;
* subscription-covered usage is shown as value, apart from metered usage,
  never as an extra bill and never as costing nothing, with an undetected
  route labelled undetected;
* the explanation is reachable by keyboard, not only by mouse hover.

The renderer tests run the SHIPPED functions out of ``app.js`` and
``provenance.js`` under node, not a copy of them.

Criteria declared here:

* AC-OBS-CEA-025.1 -- every cost figure on the Usage payload, the snapshot
  cost slice, the per-session cost breakdown and the Flow brain panel carries a
  financial basis: ``test_every_usage_cost_entry_names_its_financial_basis``,
  ``test_the_snapshot_cost_slice_names_its_financial_basis``,
  ``test_the_sessions_cost_breakdown_is_labelled``,
  ``test_the_flow_brain_panel_cost_is_a_labelled_number``,
  ``test_the_usage_session_cost_chart_and_table_show_their_basis``,
  ``test_the_flow_brain_call_list_cost_is_labelled``,
  ``test_the_flow_brain_call_list_renders_its_basis``.
* AC-OBS-CEA-025.2 -- contract and actual labels need evidence:
  ``test_contract_or_actual_without_evidence_is_unavailable_not_upgraded``.
* AC-OBS-CEA-025.3 -- a runtime-reported cost is a source, not actual spend:
  ``test_runtime_reported_cost_is_a_source_not_actual_spend``.
* AC-OBS-CEA-025.4 -- subscription value apart from metered usage, never a
  bill: ``test_banner_fully_included_never_claims_a_zero_bill``,
  ``test_banner_mixed_shows_metered_and_included_apart``,
  ``test_no_shipped_copy_claims_subscription_usage_is_free``.
* AC-OBS-CEA-025.5 -- an undetected route is labelled undetected:
  ``test_banner_route_not_detected_is_never_called_metered``,
  ``test_coverage_rest_is_metered_only_when_a_metered_route_was_detected``.
* AC-OBS-CEA-025.6 -- plan fee and overages not shown as zero:
  ``test_plan_fee_is_unknown_never_zero``.
* AC-OBS-CEA-025.7 -- the explanation on hover and keyboard focus:
  ``test_the_badge_is_focusable_and_carries_rate_source_and_route``,
  ``test_the_focus_explanation_is_styled``.
"""
import json
import os
import re
import shutil
import subprocess
import sys

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from clawmetry import cost_basis, provenance  # noqa: E402

APP_JS = os.path.join(REPO, "clawmetry", "static", "js", "app.js")
PROV_JS = os.path.join(REPO, "clawmetry", "static", "js", "provenance.js")
CSS = os.path.join(REPO, "clawmetry", "static", "css", "dashboard.css")

BILL_SHAPED = (cost_basis.CONTRACT, cost_basis.ALLOCATED_ACTUAL)


def _money_entries(payload):
    """Every provenance entry, at any depth, whose key names a money figure."""
    out = []

    def walk(node):
        if isinstance(node, dict):
            prov = node.get("provenance")
            if isinstance(prov, dict):
                for key, entry in prov.items():
                    leaf = key.split(".")[-1].split("[]")[-1] or key
                    if provenance.figure_kind(leaf) == "money" or key in (
                            "sessionCosts",):
                        out.append((key, entry))
            for k, v in node.items():
                if k != "provenance":
                    walk(v)
        elif isinstance(node, list):
            for item in node[:50]:
                walk(item)
    walk(payload)
    return out


def _assert_cost_labelled(payload, where):
    entries = _money_entries(payload)
    assert entries, "%s carries no cost provenance at all" % where
    for key, entry in entries:
        cb = entry.get("cost_basis")
        assert cb in cost_basis.COST_BASES, (
            "%s: %s has no financial basis (%r)" % (where, key, entry))
        assert cb not in BILL_SHAPED, (
            "%s: %s claims %s, and nothing on this surface records the "
            "evidence for a bill" % (where, key, cb))
        assert entry.get("cost_basis_label") == cost_basis.COST_BASIS_LABEL[cb]


# ── The vocabulary ──────────────────────────────────────────────────────────

def test_every_financial_basis_and_route_has_words():
    for b in cost_basis.COST_BASES:
        assert cost_basis.COST_BASIS_LABEL[b]
        assert cost_basis.COST_BASIS_HINT[b]
    for r in cost_basis.BILLING_ROUTES:
        assert cost_basis.BILLING_ROUTE_LABEL[r]
    assert "not an invoice" in cost_basis.COST_BASIS_HINT[
        cost_basis.PUBLISHED_RATE]


def test_contract_or_actual_without_evidence_is_unavailable_not_upgraded():
    base = provenance.derived("tokens times rate", "duckdb:events")
    for b, need in cost_basis.REQUIRED_EVIDENCE.items():
        got = cost_basis.label(base, b)
        assert got["cost_basis"] == cost_basis.UNKNOWN, b
        assert got["basis"] == provenance.UNKNOWN, b
        assert need in got["reason"], got
        # Stamped, the unevidenced figure cannot reach a screen as a number.
        payload = provenance.stamp({"monthCost": 812.5}, {"monthCost": got})
        assert payload["monthCost"] is None
        # With the evidence recorded, the label stands and carries it.
        ok = cost_basis.label(base, b, evidence={need: "pb1-abc"})
        assert ok["cost_basis"] == b
        assert ok["evidence"] == {need: "pb1-abc"}
    typo = cost_basis.label(base, "invoiced")
    assert typo["cost_basis"] == cost_basis.UNKNOWN


def test_runtime_reported_cost_is_a_source_not_actual_spend():
    import routes.usage as usage_mod
    entries = usage_mod._usage_provenance("duckdb")
    for key in ("todayCost", "weekCost", "monthCost",
                "sessions[].total_cost_usd"):
        e = entries[key]
        assert e["cost_basis"] == cost_basis.PUBLISHED_RATE, key
        assert "runtime's own" in e["rate_source"], key
        assert "published" in e["rate_source"], key


# ── The surfaces ────────────────────────────────────────────────────────────

def _fake_ls(method, **kw):
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
    return None


def test_every_usage_cost_entry_names_its_financial_basis(monkeypatch):
    import routes.usage as usage_mod
    monkeypatch.setattr(usage_mod, "_ls_call", _fake_ls)
    payload = usage_mod._try_local_store_usage()
    assert payload is not None
    provenance.assert_labelled(payload, "/api/usage")
    _assert_cost_labelled(payload, "/api/usage")


def test_the_snapshot_cost_slice_names_its_financial_basis():
    from clawmetry import sync
    payload = sync._stamp_daily_usage({
        "days": [{"day": "2026-08-25", "tokens": 10, "cost_usd": 1.0}],
        "today": 10, "week": 10, "month": 10,
        "todayCost": 1.0, "weekCost": 1.0, "monthCost": 1.0,
    })
    _assert_cost_labelled(payload, "snapshot dailyUsage")
    for spending in (
            sync._resolve_spending(
                {"todayCost": 1.0, "weekCost": 2.0, "monthCost": 3.0}, {}),
            sync._resolve_spending({}, {"today": 1.0, "week": 2.0,
                                        "month": 3.0})):
        for k in ("today", "week", "month"):
            e = provenance.entry_for(spending, k)
            assert e["cost_basis"] == cost_basis.PUBLISHED_RATE, (k, e)


def test_the_sessions_cost_breakdown_is_labelled():
    import routes.sessions as sessions_mod
    row = {"session_id": "s1", "tokens": 10, "cost_usd": 1.25,
           "reasoning_cost_usd": 0.2, "cache_write_cost_usd": 0.1,
           "cache_saved_usd": 0.4, "compression_recoverable_usd": 0.05,
           "downstream_cost_usd": 0.3}
    payload = sessions_mod._stamp_cost_breakdown(
        {"sessions": [dict(row)], "top10": [dict(row)],
         "total_cost_usd": 1.25}, "duckdb:sessions")
    provenance.assert_labelled(payload, "/api/sessions/cost-breakdown")
    _assert_cost_labelled(payload, "/api/sessions/cost-breakdown")
    assert payload["provenance"]["sessions[].cost_usd"]["basis"] == \
        provenance.DERIVED
    blended = sessions_mod._stamp_cost_breakdown(
        {"sessions": [dict(row)], "top10": [], "total_cost_usd": 1.25},
        "transcripts", blended_rows=1)
    e = blended["provenance"]["sessions[].cost_usd"]
    assert e["basis"] == provenance.ESTIMATED
    assert e["inputs"]["sessions_priced_at_blended_rate"] == 1


def test_the_flow_brain_panel_cost_is_a_labelled_number():
    import routes.components as comp
    priced = comp._brain_cost_stats({"today_cost": "$2.50"}, 2.5, 0, "duckdb")
    assert priced["today_cost_usd"] == 2.5
    provenance.assert_labelled(priced, "brain panel stats")
    assert priced["provenance"]["today_cost_usd"]["cost_basis"] == \
        cost_basis.PUBLISHED_RATE
    floor = comp._brain_cost_stats({}, 2.5, 3, "duckdb")
    assert "floor" in floor["provenance"]["today_cost_usd"]["note"]
    # Tokens and no price at all: not a confident $0.00.
    blind = comp._brain_cost_stats({}, 0.0, 4, "duckdb")
    assert blind["today_cost_usd"] is None
    assert blind["provenance"]["today_cost_usd"]["cost_basis"] == \
        cost_basis.UNKNOWN


def test_coverage_rest_is_metered_only_when_a_metered_route_was_detected():
    mixed = cost_basis.coverage_entries({"any_metered": True})
    assert mixed["out_of_pocket_usd"]["billing_route"] == cost_basis.ROUTE_METERED
    undetected = cost_basis.coverage_entries({"any_metered": False})
    assert undetected["out_of_pocket_usd"]["billing_route"] == \
        cost_basis.ROUTE_UNKNOWN
    covered = undetected["covered_usd"]
    assert covered["billing_route"] == cost_basis.ROUTE_SUBSCRIPTION
    assert "not an extra bill" in covered["billing_route_label"]
    assert covered["cost_basis"] == cost_basis.PUBLISHED_RATE


def test_plan_fee_is_unknown_never_zero(monkeypatch):
    import dashboard as d
    from clawmetry import sync
    monkeypatch.setattr(sync, "_build_billing_payload", lambda cfg: {
        "account_plan": {"mode": "subscription", "label": "Claude Max"},
        "runtimes": {"claude_code": {"mode": "subscription",
                                     "label": "Claude Max"}}})
    cov = d._get_billing_coverage([], 1.0, 2.0, 3.0,
                                  fallback_all_covered_when_no_models=True)
    assert cov["plan_fee_usd"] is None
    assert cov["plan_terms_known"] is False
    entry = cost_basis.coverage_entries(cov)["plan_fee_usd"]
    assert entry["basis"] == provenance.UNKNOWN
    assert "plan fee" in entry["reason"]


# ── The shipped renderers ───────────────────────────────────────────────────

def _node():
    node = shutil.which("node")
    if not node:
        pytest.skip("node is not installed")
    return node


def _extract_function(src, name):
    m = re.search(r"^function %s\(" % re.escape(name), src, re.M)
    assert m, "%s is gone from app.js" % name
    nxt = re.search(r"^(?:async )?function \w+\(", src[m.end():], re.M)
    end = m.end() + nxt.start() if nxt else len(src)
    return src[m.start():end]


def _run_banner(cov, usage):
    app = open(APP_JS, encoding="utf-8").read()
    prog = "\n".join([
        "var window = globalThis;",
        open(PROV_JS, encoding="utf-8").read(),
        "var host = {style: {}, innerHTML: ''};",
        "var document = {getElementById: function () { return host; }};",
        "function t(k, v, fb) { return fb; }",
        "function escHtml(s) { return String(s == null ? '' : s)"
        ".replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }",
        _extract_function(app, "_planLabel"),
        _extract_function(app, "renderBillingCoverageBanner"),
        "renderBillingCoverageBanner(%s, %s);" % (json.dumps(cov),
                                                   json.dumps(usage)),
        "console.log(JSON.stringify({html: host.innerHTML, "
        "shown: host.style.display !== 'none' && !!host.innerHTML}));",
    ])
    out = subprocess.run([_node(), "-e", prog], capture_output=True,
                         text=True, timeout=30)
    assert out.returncode == 0, out.stderr
    return json.loads(out.stdout.strip().splitlines()[-1])


def _usage(cov):
    payload = {"monthCost": 120.0}
    provenance.stamp(payload, {
        "monthCost": cost_basis.published_rate("tokens times rate", "duckdb",
                                               window="this month")})
    provenance.stamp(payload, cost_basis.coverage_entries(cov))
    return payload


_ZERO_BILL = re.compile(
    r"billed to you|out-of-pocket|out of pocket|costs? you nothing|"
    r"<strong>\$0</strong>|\$0 extra|free", re.I)


def test_banner_fully_included_never_claims_a_zero_bill():
    cov = {"detected": True, "any_subscription": True, "any_metered": False,
           "all_covered": True, "subscription_labels": ["Claude Max"],
           "month": {"covered_usd": 120.0, "out_of_pocket_usd": 0.0}}
    got = _run_banner(cov, _usage(cov))
    assert got["shown"]
    html = got["html"]
    assert not _ZERO_BILL.search(html), html
    assert "usage value at published rates" in html
    assert "not an extra bill" in html
    assert "plan fee" in html
    assert "$120.00" in html


def test_banner_mixed_shows_metered_and_included_apart():
    cov = {"detected": True, "any_subscription": True, "any_metered": True,
           "all_covered": False, "subscription_labels": ["Claude Max"],
           "metered_labels": ["OpenAI API"],
           "month": {"covered_usd": 90.0, "out_of_pocket_usd": 30.0}}
    got = _run_banner(cov, _usage(cov))
    html = got["html"]
    assert not _ZERO_BILL.search(html), html
    assert "Metered usage" in html and "$30.00" in html
    assert "$90.00" in html and "not an extra bill" in html
    assert html.index("$30.00") != html.index("$90.00")


def test_banner_route_not_detected_is_never_called_metered():
    cov = {"detected": True, "any_subscription": True, "any_metered": False,
           "all_covered": False, "subscription_labels": ["Claude Max"],
           "month": {"covered_usd": 70.0, "out_of_pocket_usd": 50.0}}
    got = _run_banner(cov, _usage(cov))
    assert got["shown"], "a partly included month with an undetected rest vanished"
    html = got["html"]
    assert "billing route was not detected" in html
    assert "Metered" not in html
    assert "$50.00" in html and "$70.00" in html


def test_no_shipped_copy_claims_subscription_usage_is_free():
    # Comments may quote the old copy to explain why it went; shipped strings
    # may not.
    app = "\n".join(
        line for line in open(APP_JS, encoding="utf-8").read().splitlines()
        if not line.strip().startswith(("//", "*")))
    for phrase in ("free on your plan", "billed to you", "out-of-pocket spend is",
                   "$0 out-of-pocket", "incremental cost is $0",
                   "Usage adds $0", "cost is $0.", "may be billed $0"):
        assert phrase not in app, "app.js still says %r" % phrase


def test_the_badge_is_focusable_and_carries_rate_source_and_route():
    entry = cost_basis.coverage_entries({"any_metered": True})["covered_usd"]
    prog = ("var window = globalThis;\n" + open(PROV_JS, encoding="utf-8").read()
            + "\nconsole.log(window.cmProv.badge(%s, {label: 'Included'}));"
            % json.dumps(entry))
    out = subprocess.run([_node(), "-e", prog], capture_output=True, text=True,
                         timeout=30)
    assert out.returncode == 0, out.stderr
    html = out.stdout.strip()
    assert 'tabindex="0"' in html
    assert ">published rates</span>" in html
    tip = re.search(r'data-tip="([^"]*)"', html).group(1)
    assert "Rate: " in tip and "published" in tip
    assert "Billing route: included in a subscription" in tip
    assert "not an extra bill" in re.search(r'aria-label="([^"]*)"', html).group(1)
    # JS fallback words mirror the Python vocabulary.
    words = subprocess.run(
        [_node(), "-e", "var window = globalThis;\n"
         + open(PROV_JS, encoding="utf-8").read()
         + "\nconsole.log(JSON.stringify([window.cmProv.COST_LABEL,"
           " window.cmProv.COST_HINT]));"],
        capture_output=True, text=True, timeout=30)
    labels, hints = json.loads(words.stdout.strip())
    assert labels == cost_basis.COST_BASIS_LABEL
    assert hints == cost_basis.COST_BASIS_HINT


_CTX_STUB = (
    "var _ctx = new Proxy({}, {get: function (t, k) {"
    " return (k in t) ? t[k] : function () {}; },"
    " set: function (t, k, v) { t[k] = v; return true; }});")


def _run_session_cost_chart(rows, entry):
    app = open(APP_JS, encoding="utf-8").read()
    prog = "\n".join([
        "var window = globalThis;",
        open(PROV_JS, encoding="utf-8").read(),
        _CTX_STUB,
        "var els = {",
        " 'usage-session-cost-bar': {getContext: function () { return _ctx; },"
        "   parentElement: {clientWidth: 600}, style: {}},",
        " 'usage-session-cost-table': {innerHTML: ''},",
        " 'usage-session-cost-basis': {innerHTML: ''},",
        " 'session-cost-threshold': {value: '0.5'}};",
        "var document = {getElementById: function (id) { return els[id] || null; }};",
        "function t(k, v, fb) { return fb; }",
        "function escHtml(s) { return String(s == null ? '' : s)"
        ".replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }",
        "window._sessionCostData = %s;" % json.dumps(rows),
        "window._sessionCostEntry = %s;" % json.dumps(entry),
        _extract_function(app, "renderSessionCostChart"),
        "renderSessionCostChart();",
        "console.log(JSON.stringify({table: els['usage-session-cost-table'].innerHTML,"
        " caption: els['usage-session-cost-basis'].innerHTML}));",
    ])
    out = subprocess.run([_node(), "-e", prog], capture_output=True,
                         text=True, timeout=30)
    assert out.returncode == 0, out.stderr
    return json.loads(out.stdout.strip().splitlines()[-1])


def test_the_usage_session_cost_chart_and_table_show_their_basis():
    """AC-OBS-CEA-025.1: the Usage tab's session cost chart and its table
    print costs, so they print the basis. loadUsage used to keep only the
    rows and drop the provenance on the floor."""
    import routes.sessions as sessions_mod
    rows = [{"session_id": "sess-priced", "tokens": 1200, "cost_usd": 1.25,
             "model": "m", "day": "2026-09-01"},
            {"session_id": "sess-unknown", "tokens": 50, "cost_usd": None,
             "model": "m", "day": "2026-09-01"}]
    payload = sessions_mod._stamp_cost_breakdown(
        {"sessions": [], "top10": rows, "total_cost_usd": 1.25},
        "duckdb:sessions")
    entry = payload["provenance"]["top10[].cost_usd"]
    got = _run_session_cost_chart(rows, entry)
    assert ">published rates</span>" in got["caption"], got["caption"]
    head = got["table"].split("</thead>")[0]
    assert ">published rates</span>" in head, "the Cost column has no basis"
    assert "$1.2500" in got["table"]
    unknown_row = got["table"].split("sess-unknown")[1].split("</tr>")[0]
    assert "not available" in unknown_row and "$0.0000" not in unknown_row
    # With no entry (an older daemon) nothing is invented.
    bare = _run_session_cost_chart(rows[:1], None)
    assert bare["caption"] == "" and "cm-prov" not in bare["table"]
    assert "$1.2500" in bare["table"]
    app = open(APP_JS, encoding="utf-8").read()
    assert "cmProv.of(cbd, 'top10[].cost_usd')" in app, (
        "loadUsage drops the cost breakdown's basis before the chart renders")


def _brain_payload():
    import routes.components as comp
    calls = [
        {"timestamp": "2026-09-01T10:00:00", "session": "main",
         "tokens_in": 1000, "tokens_out": 200, "cost": "$0.0042",
         "cost_raw": 0.0042, "duration_ms": 900},
        {"timestamp": "2026-09-01T10:01:00", "session": "main",
         "tokens_in": 500, "tokens_out": 20, "cost": "$0.0000",
         "cost_raw": 0.0, "duration_ms": 0},
    ]
    return comp._brain_call_costs({
        "stats": comp._brain_cost_stats({"today_calls": 2}, 0.0042, 1,
                                        "duckdb"),
        "calls": calls, "total": 2}, "duckdb:events")


def test_the_flow_brain_call_list_cost_is_labelled():
    """AC-OBS-CEA-025.1: the Flow brain panel's per-call cost list, not only
    its summary card. A call with tokens and no price is unavailable, never a
    confident $0.0000."""
    payload = _brain_payload()
    provenance.assert_labelled(payload, "brain panel")
    _assert_cost_labelled(payload, "brain panel")
    assert [c["cost_usd"] for c in payload["calls"]] == [0.0042, None]
    assert payload["provenance"]["calls[].cost_usd"]["cost_basis"] == \
        cost_basis.PUBLISHED_RATE


def _run_brain_panel(data):
    app = open(APP_JS, encoding="utf-8").read()
    prog = "\n".join([
        "var window = globalThis;",
        open(PROV_JS, encoding="utf-8").read(),
        "var els = {'comp-modal-body': {innerHTML: ''},"
        " 'comp-modal-footer': {textContent: ''}};",
        "var document = {getElementById: function (id) { return els[id] || null; }};",
        "function t(k, v, fb) { return fb; }",
        "function escapeHtml(s) { return String(s == null ? '' : s)"
        ".replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }",
        "var _brainPage = 0;",
        "function isCompModalActive() { return true; }",
        "function _compModalError(a, b, e) { return 'ERR ' + e.message; }",
        "function fetchJsonWithTimeout() { return Promise.resolve(%s); }"
        % json.dumps(data),
        _extract_function(app, "loadBrainData"),
        "loadBrainData(false);",
        "setTimeout(function () {"
        " console.log(JSON.stringify({html: els['comp-modal-body'].innerHTML})); }, 50);",
    ])
    out = subprocess.run([_node(), "-e", prog], capture_output=True,
                         text=True, timeout=30)
    assert out.returncode == 0, out.stderr
    return json.loads(out.stdout.strip().splitlines()[-1])["html"]


def test_the_flow_brain_call_list_renders_its_basis():
    html = _run_brain_panel(_brain_payload())
    assert "ERR" not in html, html
    listing = html.split("Cost per call: ", 1)
    assert len(listing) == 2, "the per-call cost list carries no basis"
    assert listing[1].lstrip().startswith('<span class="cm-prov')
    assert ">published rates</span>" in listing[1].split("</div>")[0]
    assert "$0.0042" in listing[1]
    assert "$0.0000" not in listing[1] and "not available" in listing[1]
    # A legacy payload with no entry keeps its strings and invents no label.
    legacy = _brain_payload()
    legacy.pop("provenance")
    for c in legacy["calls"]:
        c.pop("cost_usd")
    old = _run_brain_panel(legacy)
    assert "Cost per call" not in old and "$0.0042" in old


def test_the_focus_explanation_is_styled():
    """The explanation lives in ONE element on <body>, not a ::after on the
    badge: inside the Overview tile a ::after was clipped to its first line
    by the card's overflow:hidden and covered the figure."""
    css = open(CSS, encoding="utf-8").read()
    js = open(PROV_JS, encoding="utf-8").read()
    assert re.search(r"#cm-prov-focus-tip\s*\{[^}]*position:\s*fixed", css), (
        "the keyboard focus explanation has no styling")
    assert re.search(r"#cm-prov-focus-tip\s*\{[^}]*white-space:\s*pre-line", css)
    assert "data-tip]:focus-visible::after" not in css, (
        "a ::after tip on the badge is clipped by overflow:hidden cards")
    assert "addEventListener('focusin'" in js and "':focus-visible'" in js
    assert "document.body.appendChild" in js, (
        "the tip must live on <body> or a card will clip it")
