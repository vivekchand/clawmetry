"""Guard: the rest of the dollar figures say what kind of money they are.

vivekchand/clawmetry#5937, REQ-OBS-CEA-025. #5975 labelled the Overview spend
tile, the Usage period cards and the Flow brain panel. An audit on 2026-09-14
found the Overview hero chip, most Usage cards and the Sessions transcript
cost chips still printing bare dollar amounts. These tests hold the payloads
(local routes and the hosted snapshot slices built from the same code) and the
shipped renderers, run under node out of ``app.js`` and ``provenance.js``.

Criteria declared here:

* AC-OBS-CEA-025.8 -- the hero chip, the remaining Usage cards and the
  transcript chips carry a financial basis, in payload and on screen:
  ``test_the_efficiency_slice_labels_every_cost_figure``,
  ``test_every_spend_flow_scope_labels_its_costs``,
  ``test_the_usage_card_payloads_label_their_costs``,
  ``test_the_snapshot_usage_slices_carry_the_basis``,
  ``test_the_transcript_payload_labels_message_cost``,
  ``test_the_snapshot_transcripts_carry_the_basis``,
  ``test_the_hero_chip_shows_the_tile_figure_with_its_basis``,
  ``test_the_spend_flow_chart_captions_its_basis``,
  ``test_the_plugin_legend_labels_its_costs``,
  ``test_the_skill_leaderboard_prints_real_costs_with_a_basis``,
  ``test_the_team_and_cache_cards_label_their_costs``,
  ``test_the_transcript_turn_and_tool_chips_carry_the_basis``.
* AC-OBS-CEA-025.9 -- counterfactuals are estimates at published rates, and
  usage value is never called actual spend:
  ``test_counterfactual_figures_are_estimates_at_published_rates``,
  ``test_the_cost_comparison_never_calls_usage_actual_spend``.
"""
import datetime as _dt
import json
import os
import re
import shutil
import subprocess
import sys

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "tests"))

from clawmetry import cost_basis, provenance  # noqa: E402

try:  # absent before this change; each test then fails on its own
    from clawmetry import cost_basis_surfaces  # noqa: E402
except ImportError:  # pragma: no cover - only on a tree without the fix
    cost_basis_surfaces = None

APP_JS = os.path.join(REPO, "clawmetry", "static", "js", "app.js")
PROV_JS = os.path.join(REPO, "clawmetry", "static", "js", "provenance.js")

BILL_SHAPED = (cost_basis.CONTRACT, cost_basis.ALLOCATED_ACTUAL)


def _money_entries(payload):
    out = []

    def walk(node):
        if isinstance(node, dict):
            prov = node.get("provenance")
            if isinstance(prov, dict):
                for key, entry in prov.items():
                    leaf = key.split(".")[-1].split("[]")[-1] or key
                    if (provenance.figure_kind(leaf) == "money"
                            or "_usd" in leaf or leaf.endswith("_cost")):
                        out.append((key, entry))
            for k, v in node.items():
                if k != "provenance":
                    walk(v)
        elif isinstance(node, list):
            for item in node[:50]:
                walk(item)
    walk(payload)
    return out


def _assert_cost_labelled(payload, where, *, not_costs=("monthly_budget_usd",)):
    # Money only: a score beside the costs (the efficiency grade) is another
    # requirement's figure.
    gaps = [g for g in provenance.audit_payload(payload) if g["kind"] == "money"]
    assert not gaps, "%s renders unlabelled money: %r" % (where, gaps)
    entries = [(k, e) for k, e in _money_entries(payload) if k not in not_costs]
    assert entries, "%s carries no cost provenance at all" % where
    for key, entry in entries:
        cb = entry.get("cost_basis")
        assert cb in cost_basis.COST_BASES, (
            "%s: %s has no financial basis (%r)" % (where, key, entry))
        assert cb not in BILL_SHAPED, "%s: %s claims %s" % (where, key, cb)
        assert entry.get("cost_basis_label") == cost_basis.COST_BASIS_LABEL[cb]


def _entry(payload, key):
    e = provenance.entry_for(payload, key)
    assert e, "%s has no entry for %s" % (sorted(payload), key)
    return e


def _is_estimate_at_published_rates(entry):
    return (entry.get("cost_basis") == cost_basis.PUBLISHED_RATE
            and entry.get("basis") == provenance.ESTIMATED)


# ── Payloads ────────────────────────────────────────────────────────────────

_EFF_ROWS = [{"runtime": "claude_code", "model": "claude-sonnet-4-5",
              "tokens_in": 200000, "tokens_out": 60000, "cache_read": 900000,
              "cache_write": 120000, "cost_usd": 14.0, "calls": 500,
              "days_with_data": 12}]


def test_the_efficiency_slice_labels_every_cost_figure():
    from clawmetry import efficiency
    full = efficiency.build_efficiency_slice(_EFF_ROWS, days=30)
    scopes = [full] + list(full.get("byRuntime", {}).values())
    scopes.append(efficiency.build_efficiency_slice([], days=30))
    assert len(scopes) >= 3
    for scope in scopes:
        _assert_cost_labelled(scope, "efficiency slice")
    for key in ("projected_monthly_cost_usd", "cache_saved_monthly_usd",
                "left_on_table_monthly_usd", "actions[].savings_monthly_usd"):
        assert _is_estimate_at_published_rates(_entry(full, key)), key


def test_every_spend_flow_scope_labels_its_costs():
    from clawmetry import spend_flow
    empty = spend_flow.build_spend_flow_slice([], days=7)
    scope = spend_flow._scope_payload(spend_flow._new_agg(), 7)
    for payload in (empty, scope):
        populated = dict(payload)
        populated["input_categories"] = [{"id": "user_prompts", "tokens": 10,
                                          "cost_usd": 1.0, "basis": "measured"}]
        populated["runtimes"] = [{"runtime": "codex", "cost_usd": 1.0,
                                  "input_cost_usd": 1.0, "output_cost_usd": 0.0}]
        populated["links"] = [{"source": "user_prompts",
                               "target": "runtime:codex", "cost_usd": 1.0}]
        _assert_cost_labelled(populated, "spend flow scope")
    assert _entry(scope, "totals.cost_usd")["basis"] == provenance.DERIVED
    assert _is_estimate_at_published_rates(
        _entry(scope, "input_categories[].cost_usd"))


def _usage_mod():
    import routes.usage as usage_mod
    return usage_mod


def _today():
    return _dt.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def _fake_events():
    return [{"id": "e%d" % i, "session_id": "claude_code:s%d" % (i % 2),
             "ts": _today(), "event_type": "tool_call", "model": "claude-sonnet-4-5",
             "token_count": 1000 + i, "cost_usd": 0.25,
             "data": {"tool": "exec"}} for i in range(4)]


def _spend_opt_spans(usage_mod):
    tool, target = next(iter(usage_mod._SPEND_OPT_TOOL_DOWNGRADE.items()))
    tgt_ratio = usage_mod._SPEND_OPT_MODEL_RATIO.get(target, 1.0)
    for model in ("claude-opus-4-1", "claude-opus-4", "gpt-4o", "o1",
                  "claude-sonnet-4-5", "gemini-2.5-pro"):
        tier = usage_mod._spend_opt_model_tier(model)
        if usage_mod._SPEND_OPT_MODEL_RATIO.get(tier, 0) > tgt_ratio:
            return [{"tool_name": tool, "model": model, "cost_usd": 2.0}
                    for _ in range(5)]
    pytest.fail("no model in a tier dearer than %s" % target)


def _fake_ls_call(usage_mod):
    spans = _spend_opt_spans(usage_mod)

    def call(method, **_kw):
        if method == "query_cache_metrics":
            return [{"day": _today()[:10], "model": "claude-sonnet-4-5",
                     "input_tokens": 1000, "output_tokens": 300,
                     "cache_read_tokens": 4000, "cache_write_tokens": 500,
                     "input_cost": 0.3, "output_cost": 0.45,
                     "cache_read_cost": 0.12, "cache_write_cost": 0.19,
                     "total_cost": 1.06}]
        if method == "query_recent_spans":
            return spans
        if method == "query_sessions_table":
            return [{"compression_potential_pct": 80,
                     "compressible_tool_tokens": 5000,
                     "compression_recoverable_usd": 1.2,
                     "dominant_compression_type": "json"}]
        return None
    return call


@pytest.fixture
def usage_client(monkeypatch):
    from flask import Flask
    usage_mod = _usage_mod()
    import routes.sessions as sessions_mod
    monkeypatch.setattr(usage_mod, "_ls_call", _fake_ls_call(usage_mod))
    monkeypatch.setattr(usage_mod, "_ls_get_store", lambda: object())
    monkeypatch.setattr(usage_mod, "_scan_events_slim",
                        lambda *a, **k: _fake_events())
    monkeypatch.setattr(usage_mod, "_ls_event_skill",
                        lambda ev: "pdf" if ev.get("cost_usd") else None)
    monkeypatch.setattr(usage_mod, "_ls_call_team", lambda method, **kw: [
        {"label": "Eng", "cost_usd": 1.5, "tokens": 900, "sessions": 2,
         "runtimes": ["codex"]}])
    monkeypatch.setattr(sessions_mod, "_try_local_store_cost_breakdown", lambda: {
        "_source": "local_store", "sessions": [
            {"cache_expiry_count": 3, "cache_write_cost_usd": 0.4,
             "cache_saved_usd": 0.1, "max_idle_gap_sec": 900}]})
    app = Flask("cost-basis-remaining")
    app.register_blueprint(usage_mod.bp_usage)
    return app.test_client(), usage_mod


def test_the_usage_card_payloads_label_their_costs(usage_client):
    client, usage_mod = usage_client
    for url in ("/api/usage/cache-risk", "/api/usage/compression",
                "/api/usage/by-team"):
        body = client.get(url).get_json()
        _assert_cost_labelled(body, url)
    built = {
        "cost comparison": usage_mod._try_local_store_cost_comparison(),
        "cache trends": usage_mod._try_local_store_cache_trends(7),
        "spend optimization": usage_mod._try_local_store_spend_optimization(),
        "by plugin": usage_mod._try_local_store_usage_by_plugin(50.0),
        "skill attribution": usage_mod._try_local_store_skill_attribution(),
    }
    for where, payload in built.items():
        assert payload is not None, "%s builder deferred" % where
        _assert_cost_labelled(payload, where)
    # Forecast: the builder needs a real store, so check it uses the shared
    # entries and that those entries are right.
    import inspect
    assert "forecast_entries(" in inspect.getsource(
        usage_mod._try_local_store_usage_forecast)
    fc = cost_basis_surfaces.forecast_entries(
        spent_so_far=10.0, daily_rate=1.0, days_remaining=5)
    for key in ("projected_month_usd", "cost_this_month_usd", "daily_rate_usd"):
        assert fc[key]["cost_basis"] == cost_basis.PUBLISHED_RATE, key
    assert "cost_basis" not in fc["monthly_budget_usd"], (
        "a budget the operator typed is not usage value")


def test_counterfactual_figures_are_estimates_at_published_rates(usage_client,
                                                                  monkeypatch):
    client, usage_mod = usage_client
    opt = usage_mod._try_local_store_spend_optimization()
    cmp_ = usage_mod._try_local_store_cost_comparison()
    fc = cost_basis_surfaces.forecast_entries(
        spent_so_far=10.0, daily_rate=1.0, days_remaining=5)
    for entry in (_entry(opt, "total_projected_savings_usd_30d"),
                  _entry(opt, "recommendations[].projected_savings_usd_30d"),
                  _entry(cmp_, "alternatives[].estimated_cost"),
                  _entry(cmp_, "alternatives[].savings_usd"),
                  fc["projected_month_usd"]):
        assert _is_estimate_at_published_rates(entry), entry
    # Nothing analysed: not "you could save $0.00", and not a published-rate
    # figure either.
    monkeypatch.setattr(usage_mod, "_ls_call", lambda *a, **k: None)
    body = client.get("/api/usage/optimization-recommendations").get_json()
    assert body["total_projected_savings_usd_30d"] is None
    assert _entry(body, "total_projected_savings_usd_30d")["cost_basis"] == \
        cost_basis.UNKNOWN


def test_the_snapshot_usage_slices_carry_the_basis(usage_client):
    from clawmetry import sync
    snap = sync._build_usage_snapshot()
    for key in ("costComparison", "cacheTrends", "spendOptimization"):
        assert snap.get(key), "snapshot %s slice is empty" % key
        _assert_cost_labelled(snap[key], "snapshot " + key)


def _transcript_rows(sid):
    # The store hands the builder ``data`` already decoded.
    ts = "2026-09-14T10:00:0%dZ"
    return [
        {"id": "u1", "node_id": "n", "agent_id": "main", "session_id": sid,
         "event_type": "message", "ts": ts % 1, "token_count": 0,
         "cost_usd": 0.0,
         "data": {"role": "user", "content": "do it", "timestamp": ts % 1}},
        {"id": "a1", "node_id": "n", "agent_id": "main", "session_id": sid,
         "event_type": "message", "ts": ts % 2, "token_count": 120,
         "cost_usd": 0.02,
         "data": {"role": "assistant", "content": "done", "timestamp": ts % 2}},
    ]


def test_the_transcript_payload_labels_message_cost(monkeypatch):
    import routes.sessions as sessions_mod
    monkeypatch.setattr(sessions_mod, "_fetch_session_intent", lambda sid: {})
    sid = "claude_code:t1"
    rows = list(reversed(_transcript_rows(sid)))  # query_events is DESC
    t = sessions_mod._try_local_store_transcript(sid, _events=rows)
    assert t and any(m.get("cost_usd") == 0.02 for m in t["messages"]), t
    _assert_cost_labelled(t, "/api/transcript")
    assert _entry(t, "messages[].cost_usd")["basis"] == provenance.DERIVED

    from flask import Flask
    import routes.local_query as lq
    monkeypatch.setattr(lq, "_dispatch", lambda name, args: {
        "rows": rows, "has_more": False, "next_before_ts": None})
    app = Flask("transcript-page")
    app.register_blueprint(sessions_mod.bp_sessions)
    page = app.test_client().get("/api/transcript-page/" + sid).get_json()
    assert page["messages"], page
    _assert_cost_labelled(page, "/api/transcript-page")


def test_the_snapshot_transcripts_carry_the_basis(monkeypatch):
    from unittest.mock import patch
    from clawmetry import sync
    import routes.sessions as sessions_mod
    sid = "claude_code:t2"
    rows = list(reversed(_transcript_rows(sid)))

    class _Store:
        def query_events(self, session_id=None, limit=None):
            if session_id is None:
                return [{"session_id": sid, "ts": rows[0]["ts"], "id": "a1"}]
            return rows

        def query_recent_sessions_by_runtime(self, per_runtime=2, **_kw):
            return []

    monkeypatch.setattr(sessions_mod, "_fetch_session_intent", lambda s: {})
    sync._TRANSCRIPT_SNAP_CACHE.clear()
    with patch("clawmetry.local_store.get_store", return_value=_Store()):
        out = sync._build_transcripts()
    assert sid in out, out
    _assert_cost_labelled(out[sid], "snapshot transcripts")


# ── The shipped renderers ───────────────────────────────────────────────────

def _node():
    node = shutil.which("node")
    if not node:
        pytest.skip("node is not installed")
    return node


def _app():
    return open(APP_JS, encoding="utf-8").read()


def _fn(src, name):
    m = re.search(r"^(?:async )?function %s\(" % re.escape(name), src, re.M)
    assert m, "%s is gone from app.js" % name
    nxt = re.search(r"^(?:async )?function [\w$]+\(", src[m.end():], re.M)
    end = m.end() + nxt.start() if nxt else len(src)
    return src[m.start():end]


_PRELUDE = "\n".join([
    "var window = globalThis;",
    "function t(k, v, fb) { return fb; }",
    "function escHtml(s) { return String(s == null ? '' : s)"
    ".replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')"
    ".replace(/\"/g,'&quot;'); }",
    "var console_error = console.error; console.error = function () {};",
])

_CTX_STUB = (
    "var _ctx = new Proxy({}, {get: function (t, k) {"
    " return (k in t) ? t[k] : function () {}; },"
    " set: function (t, k, v) { t[k] = v; return true; }});")


def _run(body, *, fns=(), els=None, fetch_json=None):
    app = _app()
    prog = "\n".join([
        _PRELUDE,
        open(PROV_JS, encoding="utf-8").read(),
        _CTX_STUB,
        "var els = %s;" % json.dumps(els or {}),
        "Object.keys(els).forEach(function (k) { els[k].style = {};"
        " els[k].getContext = function () { return _ctx; }; });",
        "var document = {getElementById: function (id) { return els[id] || null; },"
        " body: {}, createElement: function () { var o = {innerHTML: ''};"
        " Object.defineProperty(o, 'textContent', {set: function (v) {"
        " o.innerHTML = escHtml(v); }}); return o; }};",
        "function getComputedStyle() { return {getPropertyValue: function () { return ''; }}; }",
        "function fetch() { return Promise.resolve({ok: true, status: 200,"
        " json: function () { return Promise.resolve(%s); }}); }"
        % json.dumps(fetch_json),
    ] + [_fn(app, f) for f in fns] + [body])
    out = subprocess.run([_node(), "-e", prog], capture_output=True, text=True,
                         timeout=30)
    assert out.returncode == 0, out.stderr[-2000:]
    return json.loads(out.stdout.strip().splitlines()[-1])


def _pub_entry(**kw):
    return cost_basis.published_rate("tokens times rate", "duckdb", **kw)


def _badges(html):
    return re.findall(r'<span class="cm-prov[^"]*"[^>]*>([^<]*)</span>', html)


def test_the_hero_chip_shows_the_tile_figure_with_its_basis():
    entry = _pub_entry(window="today")
    got = _run(
        "console.log(JSON.stringify({"
        " priced: _cmHeroCostChip(8.49, %s, false),"
        " plan: _cmHeroCostChip(8.49, %s, true),"
        " zeroPlan: _cmHeroCostChip(0, %s, true),"
        " old: _cmHeroCostChip(8.49, null, false)}));"
        % ((json.dumps(entry),) * 3), fns=("_cmHeroCostChip",))
    assert "$8.49" in got["priced"]
    assert _badges(got["priced"]) == ["published rates"]
    assert "not an extra bill" in got["plan"]
    assert "not an extra bill" not in got["zeroPlan"]
    assert "$8.49" in got["old"] and not _badges(got["old"])
    hero = _fn(_app(), "_renderOverviewHero")
    assert "_cmHeroCostChip(" in hero
    assert "_txt('cost-today')" not in hero, (
        "the hero reads the tile's text back instead of its number and entry")


def test_no_function_calls_a_formatter_that_only_another_function_defines():
    """The runtime-scoped Spending tile called ``fmtCost`` inside
    loadMiniWidgets, where no fmtCost exists. The ReferenceError was swallowed,
    the tile kept node-wide figures, and the hero chip printed the runtime's:
    two different numbers for one thing on one screen."""
    import test_provenance_render_coverage as cov
    lines = cov._lines()
    funcs = cov._functions(lines)
    fmts = cov._formatters(lines)
    top_level = set(funcs)
    src = "\n".join(lines)
    offenders = []
    for name in sorted(fmts - top_level):
        if re.search(r"^(?:var|let|const) %s\b" % re.escape(name), src, re.M):
            continue
        call = re.compile(r"(?<![\w.$])%s\s*\(" % re.escape(name))
        define = re.compile(r"(?:function\s+%s\s*\(|(?:var|let|const)\s+%s\s*=)"
                            % (re.escape(name), re.escape(name)))
        for fn, spans in funcs.items():
            for a, b in spans:
                body = "\n".join(lines[a:b])
                if call.search(body) and not define.search(body):
                    offenders.append("%s() calls %s()" % (fn, name))
    assert not offenders, "\n".join(offenders)


def _spend_flow_payload():
    data = {
        "schema": 1, "window_days": 7, "insufficient_data": False,
        "totals": {"calls": 9, "cost_usd": 3.0, "input_cost_usd": 2.0,
                   "output_cost_usd": 1.0, "prompt_tokens": 100,
                   "output_tokens": 50},
        "input_categories": [{"id": "user_prompts", "tokens": 100,
                              "cost_usd": 2.0, "pct_of_side_cost": 100.0,
                              "basis": "measured"}],
        "output_categories": [{"id": "thinking", "tokens": 50,
                               "cost_usd": 1.0, "pct_of_side_cost": 100.0,
                               "basis": "measured"}],
        "runtimes": [{"runtime": "codex", "cost_usd": 3.0,
                      "input_cost_usd": 2.0, "output_cost_usd": 1.0}],
        "links": [{"source": "user_prompts", "target": "runtime:codex",
                   "cost_usd": 2.0, "tokens": 100},
                  {"source": "runtime:codex", "target": "thinking",
                   "cost_usd": 1.0, "tokens": 50}],
    }
    return provenance.stamp(data, cost_basis_surfaces.spend_flow_entries(7))


def test_the_spend_flow_chart_captions_its_basis():
    app = _app()
    consts = "\n".join(re.search(r"^var %s = \{.*?^\};" % n, app, re.M | re.S).group(0)
                       for n in ("_CM_SF_IN", "_CM_SF_OUT"))
    payload = _spend_flow_payload()
    legacy = dict(payload)
    legacy.pop("provenance")
    got = _run(consts + "\nfunction _cmRuntimeLabel(r) { return r; }\n"
               "console.log(JSON.stringify({html: _sfRender(%s), old: _sfRender(%s)}));"
               % (json.dumps(payload), json.dumps(legacy)),
               fns=("_sfLabel", "_sfRender"))
    caption = got["html"].split("<svg")[0]
    assert _badges(caption) == ["published rates", "published rates"], caption
    assert "estimates" in caption
    table = got["html"].split("<table", 1)[1]
    assert 'class="cm-fig"' in table and "$2.00" in table
    assert "<svg" in got["old"] and not _badges(got["old"])


def test_the_cost_comparison_never_calls_usage_actual_spend():
    payload = provenance.stamp({
        "actual": {"model": "claude-sonnet-4-5", "tokens": 50000, "cost_usd": 0.5},
        "alternatives": [{"model_id": "m", "display_name": "Mini",
                          "provider": "OpenAI", "estimated_cost": 0.05,
                          "savings_usd": 0.45, "savings_pct": 90.0}],
        "period": "30d"}, cost_basis_surfaces.cost_comparison_entries("duckdb"))
    got = _run("renderCostComparison(%s);"
               "console.log(JSON.stringify({html: els['cost-comparison-content'].innerHTML}));"
               % json.dumps(payload), fns=("renderCostComparison",),
               els={"cost-comparison-content": {"innerHTML": ""}})
    html = got["html"]
    assert "actual spend" not in html.lower(), html
    assert "usage value at published rates" in html.lower()
    assert _badges(html) == ["published rates", "published rates"]
    assert "$0.50" in html and "$0.05" in html and "$0.45" in html
    shipped = "\n".join(line for line in _app().splitlines()
                        if not line.strip().startswith(("//", "*")))
    assert "Your actual spend" not in shipped


def test_the_plugin_legend_labels_its_costs():
    entry = cost_basis_surfaces.by_plugin_entries("duckdb")["plugins[].cost_usd"]
    rows = json.dumps([{"plugin": "exec", "total_tokens": 1200, "cost_usd": 0.5,
                        "pct_of_total": 100.0}])
    body = ("renderPluginPieChart(%s, false, %s);"
            "var first = els['usage-plugin-legend'].innerHTML;"
            "renderPluginPieChart(%s, false, null);"
            "console.log(JSON.stringify({html: first,"
            " old: els['usage-plugin-legend'].innerHTML}));"
            % (rows, json.dumps(entry), rows))
    got = _run(body, fns=("renderPluginPieChart",),
               els={"usage-plugin-pie": {"width": 280, "height": 280},
                    "usage-plugin-legend": {"innerHTML": ""}})
    assert _badges(got["html"]) == ["published rates"]
    assert "$0.50" in got["html"] and "$0.5000" not in got["html"]
    assert "$0.50" in got["old"] and not _badges(got["old"])


def _run_async(call, fns, els, data):
    return _run(call + ";setTimeout(function () { console.log(JSON.stringify("
                "Object.keys(els).reduce(function (o, k) { o[k] = els[k].innerHTML;"
                " return o; }, {}))); }, 50);", fns=fns, els=els, fetch_json=data)


def test_the_skill_leaderboard_prints_real_costs_with_a_basis():
    local = provenance.stamp({
        "skills": [{"name": "pdf", "invocations": 2, "total_cost_usd": 1.25,
                    "avg_cost_usd": 0.625, "last_used": "2026-09-14T00:00:00Z",
                    "clawhub_url": "https://clawhub.dev/skills/pdf"}],
        "total_cost": 1.25, "note": "n"},
        cost_basis_surfaces.skill_attribution_entries("duckdb"))
    local["top5_week"] = list(local["skills"])
    els = {"skill-leaderboard-content": {"innerHTML": ""}}
    fns = ("_skillCostTableHtml", "loadSkillAttribution")
    got = _run_async("loadSkillAttribution()", fns, els, local)["skill-leaderboard-content"]
    assert "$1.25" in got and "$0.63" in got or "$0.62" in got, got
    head = got.split("</thead>")[0]
    assert _badges(head) == ["published rates"], head
    assert "$0.00" not in got, "the local shape printed $0.00 on every row"
    hosted = {"skills": [{"name": "pdf", "invocations": 2, "total_cost": 1.25,
                          "avg_cost": 0.625, "clawhub_url": ""}],
              "total_cost": 1.25, "note": "heuristic"}
    hosted["top5_week"] = list(hosted["skills"])
    old = _run_async("loadSkillAttribution()", fns, els, hosted)["skill-leaderboard-content"]
    assert "$1.25" in old and not _badges(old)


def test_the_team_and_cache_cards_label_their_costs():
    team = provenance.stamp({"teams": [{"label": "Eng", "cost_usd": 1.5,
                                        "tokens": 9, "sessions": 2,
                                        "runtimes": ["codex"]}],
                             "window_days": 7},
                            cost_basis_surfaces.by_team_entries(7))
    els = {"usage-by-team-title": {}, "usage-by-team-card": {},
           "usage-by-team-content": {"innerHTML": ""}}
    got = _run_async("loadUsageByTeam()",
                     ("costCardText", "_e", "loadUsageByTeam"), els, team)
    html = got["usage-by-team-content"]
    assert _badges(html.split("</thead>")[0]) == ["published rates"]
    assert "$1.50" in html
    risk = provenance.stamp({"affected_sessions": 1, "total_sessions": 3,
                             "total_expiry_count": 3,
                             "total_write_cost_usd": 0.4, "total_saved_usd": 0.1,
                             "max_idle_gap_sec": 900},
                            cost_basis_surfaces.cache_risk_entries("duckdb"))
    els = {"cache-risk-title": {}, "cache-risk-card": {},
           "cache-risk-content": {"innerHTML": ""}}
    html = _run_async("loadCacheRisk()", ("loadCacheRisk",), els, risk)["cache-risk-content"]
    assert "published rates" in _badges(html)
    assert "$0.40" in html and "$0.10" in html and "$0.30" in html
    assert "$0.400" not in html


def test_the_transcript_turn_and_tool_chips_carry_the_basis():
    entry = cost_basis_surfaces.transcript_entries("duckdb")["messages[].cost_usd"]
    turn = {"turn": 1, "anchor": {"role": "user", "content": "do it"},
            "firstTs": 0, "lastTs": 0, "toolCount": 1, "errorCount": 0,
            "tokens": 120, "cost": 0.03,
            "events": [{"role": "assistant", "type": "tool_use", "content": "",
                        "cost": 0.02, "tokens": 120, "originalIndex": 3}]}
    stubs = ("function _renderCompactionEvent() { return ''; }\n"
             "function _renderHistoryGap() { return ''; }\n"
             "function _renderRawPayload() { return ''; }\n"
             "function _renderToolDiveChip() { return ''; }\n")
    got = _run(stubs + "window._replayCostEntry = %s;"
               "var withBasis = _renderTurnChapter(%s, -1);"
               "window._replayCostEntry = null;"
               "console.log(JSON.stringify({html: withBasis, old: _renderTurnChapter(%s, -1)}));"
               % (json.dumps(entry), json.dumps(turn), json.dumps(turn)),
               fns=("_turnDurationLabel", "_turnAnchorPreview",
                    "_renderReplayEvent", "_renderTurnChapter"))
    html = got["html"]
    figs = re.findall(r'<span class="cm-fig"[^>]*title="([^"]*)"[^>]*>([^<]*)</span>', html)
    shown = {text for _tip, text in figs}
    assert {"$0.03", "$0.02"} <= shown, figs
    for tip, _text in figs:
        assert "published rates" in tip, tip
    # One badge in the transcript header, not one per chip.
    assert not _badges(html)
    assert "$0.03" in got["old"] and "$0.02" in got["old"]
    assert "cmProv.of(data, 'messages[].cost_usd')" in _app()
