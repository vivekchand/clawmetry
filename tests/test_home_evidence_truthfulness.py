"""Exercise the rendered Home claims, including runtime-switch races."""
import json
from pathlib import Path
import re
import subprocess

import pytest


APP = Path(__file__).resolve().parents[1] / "clawmetry/static/js/app.js"


def run_js(names, setup, action):
    source = APP.read_text()
    functions = []
    for name in names:
        match = re.search(r"^(?:async )?function " + name + r"\b[\s\S]*?^\}", source, re.M)
        assert match, name
        functions.append(match.group())
    script = "\n".join(functions) + "\n" + setup + "\n" + action
    result = subprocess.run(["node", "-e", script], capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


ACTIVITY_SETUP = """
var current = 'claude_code', calls = [], stream = {innerHTML: ''};
var window = {_cmLastAgentSay: {text: 'old Codex reply', rt: 'codex'}};
var document = {getElementById: () => stream};
function _cmRuntimeFilter(){return current;}
function _cmRuntimeOf(row){return row.id.split(':')[0];}
function escHtml(value){return String(value);}
function t(key, args, fallback){return fallback;}
function _renderOverviewHero(){}
function _renderWasteSummary(){}
function _renderOutLoopSources(){}
"""


def test_activity_uses_selected_runtime_even_if_list_is_node_wide():
    result = run_js(["loadActivityStream"], ACTIVITY_SETUP + """
async function fetchJsonWithTimeout(url){
  calls.push(url);
  if(url.startsWith('/api/transcripts')) return {transcripts: [
    {id: 'codex:newest'}, {id: 'claude_code:chosen'}]};
  return {messages: [{role:'assistant', content:'Claude reply', timestamp:'2026-10-03'}]};
}
""", """
(async()=>{await loadActivityStream(); console.log(JSON.stringify({calls, say:window._cmLastAgentSay}));})();
""")
    assert result["calls"] == ["/api/transcripts?runtime=claude_code", "/api/transcript/claude_code%3Achosen"]
    assert result["say"]["rt"] == "claude_code"
    assert result["say"]["text"] == "Claude reply"


@pytest.mark.parametrize("switch_during_fetch", [False, True])
def test_empty_or_late_activity_cannot_reuse_another_runtimes_reply(switch_during_fetch):
    result = run_js(["loadActivityStream"], ACTIVITY_SETUP + """
async function fetchJsonWithTimeout(url){
  if (SWITCH) current='codex';
  return {transcripts: []};
}
""".replace("SWITCH", json.dumps(switch_during_fetch)), """
(async()=>{await loadActivityStream(); console.log(JSON.stringify({say:window._cmLastAgentSay, html:stream.innerHTML}));})();
""")
    assert not result["say"] or result["say"].get("rt") != "claude_code"
    assert "AI agent initialized" not in result["html"]
    if not switch_during_fetch:
        assert result["say"] is None
        assert "No recent activity" in result["html"]


def test_waste_summary_labels_scope_and_does_not_claim_an_invoice_or_proven_savings():
    result = run_js(["_renderWasteSummary"], """
var rendered = '', document={getElementById: id=>id==='page-overview' ? {
  insertAdjacentHTML: (where,html)=>{rendered=html;}
} : null};
function escHtml(v){return String(v);}
var data={reasoning_cost_usd:40, reasoning_pct_of_cost:40,total_cost_usd:100,
  flagged_session_count:3,session_count:7,compaction_heavy_sessions:2,
  compressible_sessions:1,compressible_usd:5,low_cache_sessions:1};
function fetch(){return Promise.resolve({json:()=>Promise.resolve(data)});}
function _cmIsOverviewTab(){return true;}
function _cmFetchHomeSummary(url){return fetch(url).then(r=>r.json());}
""", """
(async()=>{_renderWasteSummary(); await new Promise(r=>setImmediate(r)); console.log(JSON.stringify(rendered));})();
""")
    assert "All runtimes on this node" in result
    assert "Reasoning can be useful" in result
    assert "estimates at published rates" in result
    for claim in ["billed, no deliverable", "Recoverable spend", "without changing answers", "keep sessions warm"]:
        assert claim not in result


def test_home_summaries_share_inflight_cache_success_and_retry_errors():
    result = run_js(["_cmFetchHomeSummary"], """
var _cmHomeSummaryCache={}, now=1000, requests=[], resolvers=[];
Date.now=()=>now;
function fetchJsonWithTimeout(url){requests.push(url); return new Promise((resolve,reject)=>resolvers.push({resolve,reject}));}
""", """
(async()=>{
  var a=_cmFetchHomeSummary('/summary'), b=_cmFetchHomeSummary('/summary');
  var shared=a===b;
  resolvers[0].resolve({count:3}); await a;
  now=60999; var cached=await _cmFetchHomeSummary('/summary');
  now=61000; var refresh=_cmFetchHomeSummary('/summary');
  resolvers[1].reject(new Error('offline')); await refresh.catch(()=>{});
  var retry=_cmFetchHomeSummary('/summary'); resolvers[2].resolve({count:4}); await retry;
  console.log(JSON.stringify({shared,cached,requests}));
})();
""")
    assert result == {"shared": True, "cached": {"count": 3}, "requests": ["/summary"] * 3}


def test_home_refresh_keeps_live_status_fast_without_repeating_full_fanout():
    result = run_js(["startOverviewRefresh"], """
var window={}, timers=[], active=true, now=11000, full=0, live=0;
var _overviewRefreshRunning=false, _loadAllLastSucceededMs=1000;
Date.now=()=>now;
function clearInterval(){}
function visibilitySetInterval(fn,ms){timers.push({fn,ms});return timers.length;}
function _cmIsOverviewTab(){return active;}
function loadMainActivity(){}
function _renderOverviewHero(){live++;}
async function loadAll(){full++; _loadAllLastSucceededMs=now;}
""", """
(async()=>{
  startOverviewRefresh(); await timers[0].fn();
  var fast={full,live};
  now=61000; await timers[0].fn(); var minute={full,live};
  now=71000; await timers[0].fn();
  _loadAllLastSucceededMs=0; await timers[0].fn(); var retry={full,live};
  active=false; now=200000; await timers[0].fn();
  console.log(JSON.stringify({fast,minute,retry,offTab:{full,live},intervals:timers.map(t=>t.ms)}));
})();
""")
    assert result["fast"] == {"full": 0, "live": 1}
    assert result["minute"] == {"full": 1, "live": 1}
    assert result["retry"] == {"full": 2, "live": 2}
    assert result["offTab"] == result["retry"]
    assert result["intervals"] == [10000, 5000]


def test_home_summary_renderers_do_not_fetch_off_tab():
    result = run_js(["_renderWasteSummary", "_renderOutLoopSources"], """
var document={getElementById:()=>({})}, calls=0;
function _cmIsOverviewTab(){return false;}
function _cmFetchHomeSummary(){calls++; return Promise.resolve({});}
""", """
_renderWasteSummary(); _renderOutLoopSources(); console.log(JSON.stringify(calls));
""")
    assert result == 0


def test_scoped_usage_keeps_day_week_month_distinct_even_when_week_equals_month():
    result = run_js(["_cmScopedOverviewUsage"], "", """
console.log(JSON.stringify(_cmScopedOverviewUsage('claude_code', 12, {sessions:12, primary_model:'claude'}, {
  day:{runtime:'claude_code',total_cost:2,total_tokens:10,sessions_count:1},
  week:{runtime:'claude_code',total_cost:9},
  month:{runtime:'claude_code',total_cost:9,total_tokens:100,sessions_count:7}
})));
""")
    assert (result["cost"], result["costWeek"], result["costMonth"]) == (2, 9, 9)
    assert result["periodSplit"] is True
    assert result["sessions"] == 12


@pytest.mark.parametrize("periods", [None, {
    "day": {"runtime": "claude_code", "total_cost": 2},
    "week": {"runtime": "codex", "total_cost": 9},
    "month": {"runtime": "claude_code", "total_cost": 20},
}])
def test_lifetime_or_mismatched_usage_is_not_reported_as_todays_usage(periods):
    result = run_js(["_cmScopedOverviewUsage"], "", "console.log(JSON.stringify(" +
        "_cmScopedOverviewUsage('claude_code', 12, {sessions:12,cost_usd:999,tokens:50000}," +
        json.dumps(periods) + ")));")
    assert result["sessions"] == 12
    assert result["cost"] is None
    assert result["costWeek"] is None
    assert result["costMonth"] is None
    assert result["tokensToday"] is None
    assert result["periodSplit"] is False


@pytest.mark.parametrize("reply_runtime", ["codex", "claude_code"])
def test_hero_only_uses_evidence_for_current_runtime(reply_runtime):
    setup = """
var hero={style:{},innerHTML:''};
var document={getElementById:id=>id==='overview-hero'?hero:(id==='cm-hero-kf'?{}:null)};
var window={_cmOverview:{model:'node-model',sessionCount:500},_cmAgentBusy:false,
  _cmRtAct:{ts:Date.now()},_cmRuntimeScope:{runtime:'codex',sessions:999,cost:999,model:'wrong-model'},
  _cmLive:{rt:'codex',ts:Date.now(),available:true,counts:{working:9}},
  _cmLastAgentSay:{rt:REPLY_RUNTIME,text:'A recorded reply'},_cmEff:{rt:'claude_code',data:{},ts:Date.now()}};
var _CM_LIVE_TTL_MS=10000;
function _cmRuntimeFilter(){return 'claude_code';}
function _cmRtRecentlyActive(){return false;}
function _cmLoadLiveSessions(){}
function _cmLiveRowsHtml(){return '';}
function _cmEffChipHtml(){return '';}
function escHtml(v){return String(v);}
function t(k,a,f){return f;}
function _cmHeroCostChip(){return 'WRONG COST';}
""".replace("REPLY_RUNTIME", json.dumps(reply_runtime))
    result = run_js(["_renderOverviewHero"], setup,
                    "_renderOverviewHero(); console.log(JSON.stringify(hero.innerHTML));")
    for claim in ["9 sessions are working", "999", "wrong-model", "node-model", "WRONG COST", "🧠 running"]:
        assert claim not in result
    assert ("A recorded reply" in result) == (reply_runtime == "claude_code")


@pytest.mark.parametrize("cloud", [False, True])
@pytest.mark.parametrize("summary_fails", [False, True])
def test_real_home_widget_renderer_uses_period_data_and_matching_provenance(cloud, summary_fails):
    setup = """
var els={}, current='claude_code';
var document={getElementById:id=>els[id]||(els[id]={style:{},textContent:'',innerHTML:''})};
var window={CLOUD_MODE:__CLOUD__, _cmGlobalRtCounts:{claude_code:12}, cmProv:{
  of:(d,k)=>({basis:'derived',window:k}), isUnknown:()=>false,
  badge:()=> 'published rates', money:(d,k)=>String(d[k]),
  figure:(v,e)=>String(v)+' ['+(e.window||'scoped')+']'
}};
function _cmRuntimeFilter(){return current;}
function t(k,a,f){return f;}
function loadToolActivity(){}
function applyBillingHintToFlow(){}
function loadEvalSummary(){}
function loadEvalRegressionSummary(){}
function loadEvaluators(){}
function fetchJsonWithTimeout(){return __FAIL__ ? Promise.reject(new Error('unavailable')) : Promise.resolve({runtimes:{claude_code:{sessions:12,cost_usd:999,primary_model:'claude'}}});}
async function fetch(url){
 var d = url.endsWith('period=day')?{total_cost:2,total_tokens:10}:
   (url.endsWith('period=week')?{total_cost:9}:{total_cost:9,total_tokens:100});
 d.runtime='claude_code'; return {ok:true,json:async()=>({data:d})};
}
var usage={_source:'local_store',coverage:{runtime:'claude_code',status:'ok'},
  todayCost:2,weekCost:9,monthCost:9,today:10,week:50,month:100};
""".replace("__CLOUD__", json.dumps(cloud)).replace("__FAIL__", json.dumps(summary_fails))
    result = run_js(["_cmScopedOverviewUsage", "_cmLocalOverviewPeriods", "loadMiniWidgets"], setup, """
(async()=>{await loadMiniWidgets({sessionsToday:999,model:'node-model'},usage);
console.log(JSON.stringify({els,scope:window._cmRuntimeScope}));})();
""")
    if summary_fails:
        assert result["els"]["model-primary"]["textContent"] == "—"
        assert result["els"]["hot-sessions-count"]["textContent"] == 12
        if cloud:
            assert result["els"]["cost-today"]["textContent"] == "Not measured"
            assert result["els"]["tokens-today"]["textContent"] == "Not measured"
            return
        assert result["els"]["cost-today"]["innerHTML"] == "2"
        assert result["scope"]["cost"] == 2
        return
    assert result["els"]["cost-today"]["innerHTML"].startswith("2 [")
    assert result["els"]["cost-week"]["innerHTML"].startswith("9 [")
    assert result["els"]["cost-month"]["innerHTML"].startswith("9 [")
    assert result["els"]["tokens-today"]["textContent"] == "10"
    assert result["scope"]["periodSplit"] is True
    if not cloud:
        assert "todayCost" in result["els"]["cost-today"]["innerHTML"]
        assert "weekCost" in result["els"]["cost-week"]["innerHTML"]
        assert "monthCost" in result["els"]["cost-month"]["innerHTML"]


@pytest.mark.parametrize("source,runtime,status,expected", [
    ('local_store', 'claude_code', 'ok', 2),
    ('local_store', 'claude_code', 'no_activity', 2),
    ('local_store', 'claude_code', 'not_recorded', None),
    ('legacy', 'claude_code', 'ok', None),
    ('local_store', 'codex', 'ok', None),
])
def test_local_periods_require_confirmed_scope_and_recorded_usage(source, runtime, status, expected):
    usage = {"_source": source, "coverage": {"runtime": runtime, "status": status},
             "todayCost": 2, "weekCost": 9, "monthCost": 20}
    result = run_js(["_cmLocalOverviewPeriods"], "var window={};",
                    "console.log(JSON.stringify(_cmLocalOverviewPeriods('claude_code'," + json.dumps(usage) + ")));")
    if source != 'local_store' or runtime != 'claude_code':
        assert result is None
    else:
        assert result["day"]["total_cost"] == expected


def test_measured_zero_sessions_is_not_replaced_by_another_count():
    result = run_js(["_cmScopedOverviewUsage"], "", """
console.log(JSON.stringify(_cmScopedOverviewUsage('claude_code',0,{sessions:9},null)));
""")
    assert result["sessions"] == 0


def test_structured_or_malformed_message_content_cannot_become_a_fake_reply():
    result = run_js(["loadActivityStream"], ACTIVITY_SETUP + """
async function fetchJsonWithTimeout(url){
  if(url.startsWith('/api/transcripts')) return {transcripts:[{id:'claude_code:chosen'}]};
  return {messages:[{role:'assistant',content:'A valid reply'}, null,
    {role:'assistant',content:{type:'image'}}, {role:'assistant',content:[{type:'image'}]}]};
}
""", """
(async()=>{await loadActivityStream(); console.log(JSON.stringify(window._cmLastAgentSay));})();
""")
    assert result["text"] == "A valid reply"
