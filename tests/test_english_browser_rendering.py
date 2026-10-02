"""Rendered values and honest fallbacks with the real translation function.

AC-STE-004.1: catalog and fallback rendering retain the same observed facts.
"""
import json
from pathlib import Path
import re
import subprocess

import pytest

from scripts.english_js import translations

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / 'clawmetry/static/js/app.js').read_text()
CATALOG = json.loads((ROOT / 'clawmetry/static/locales/en.json').read_text())
I18N = (ROOT / 'clawmetry/static/js/i18n.js').read_text()
TRANSLATE = re.search(r'^  function T\(key, vars, fb\) \{[\s\S]*?^  \}', I18N, re.M).group()


@pytest.fixture(scope='session')
def server():
    yield None


def run_js(body):
    result = subprocess.run(['node', '-'], input=body, text=True, capture_output=True, timeout=15)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


@pytest.mark.parametrize('catalog_available', [False, True])
@pytest.mark.parametrize('apply_before_boot', [False, True])
def test_dom_attributes_keep_original_fallbacks_across_language_changes(catalog_available, apply_before_boot):
    """Run the complete shipped runtime, including boot and language switching."""
    body = r'''
const vm = require('vm');
const attributes = ['title', 'placeholder', 'aria-label'];
const nodes = [];
const en = {}, fr = {};
for (const kind of ['missing', 'known', 'english', 'local', 'empty']) {
  const attrs = {};
  for (const attr of attributes) {
    attrs['data-i18n-' + attr] = kind + '.' + attr;
    if (kind !== 'empty') attrs[attr] = 'Original ' + kind + ' ' + attr;
    if (kind === 'known' || kind === 'english') en[kind + '.' + attr] = 'English ' + attr;
    if (kind === 'known' || kind === 'local') fr[kind + '.' + attr] = 'French ' + attr;
  }
  nodes.push({
    attrs,
    getAttribute: name => Object.prototype.hasOwnProperty.call(attrs, name) ? attrs[name] : null,
    setAttribute: (name, value) => { attrs[name] = String(value); }
  });
}
const listeners = {};
const document = {
  currentScript: null, readyState: 'loading', cookie: '',
  documentElement: {setAttribute() {}},
  getElementById: () => null,
  addEventListener: (name, fn) => { listeners[name] = fn; },
  querySelectorAll: selector => nodes.filter(n => n.getAttribute(selector.slice(1, -1)) !== null)
};
const context = {
  document, window: {dispatchEvent() {}}, URLSearchParams,
  navigator: {languages: ['en']}, location: {hostname: 'localhost', search: ''},
  localStorage: {getItem: () => null, setItem() {}},
  fetch: async url => ({ok: true, json: async () => {
    if (url.endsWith('_meta.json')) return [{code: 'en'}, {code: 'fr'}];
    if (url.endsWith('en.json')) return __TEST_AVAILABLE__ ? en : null;
    if (url.endsWith('fr.json')) return fr;
    throw Error('Unexpected request: ' + url);
  }})
};
vm.createContext(context);
vm.runInContext(__TEST_SOURCE__, context);
const read = () => nodes.map(n => attributes.map(a => n.getAttribute(a)));
(async () => {
  if (__TEST_PREAPPLY__) context.window.i18n.apply(document);
  const before = read();
  listeners.DOMContentLoaded();
  await new Promise(setImmediate);
  const boot = read();
  await context.window.i18n.setLang('fr');
  const french = read();
  context.window.i18n.apply(document);
  context.window.i18n.apply(document);
  const repeated = read();
  await context.window.i18n.setLang('en');
  const english = read();
  await context.window.i18n.setLang('fr');
  await context.window.i18n.setLang('en');
  console.log(JSON.stringify({before, boot, french, repeated, english, again: read()}));
})().catch(e => { console.error(e); process.exitCode = 1; });
'''
    values = {'AVAILABLE': catalog_available, 'PREAPPLY': apply_before_boot, 'SOURCE': I18N}
    result = run_js(re.sub(r'__TEST_(\w+)__', lambda m: json.dumps(values[m[1]]), body))
    attributes = ['title', 'placeholder', 'aria-label']
    original = [[f'Original {kind} {attr}' for attr in attributes]
                for kind in ['missing', 'known', 'english', 'local']] + [['', '', '']]
    english = [row[:] for row in original]
    if catalog_available:
        english[1] = english[2] = [f'English {attr}' for attr in attributes]
    french = [row[:] for row in english]
    french[1] = french[3] = [f'French {attr}' for attr in attributes]
    assert result['before'] == original[:-1] + ([['', '', '']] if apply_before_boot else [[None, None, None]])
    assert result['boot'] == result['english'] == result['again'] == english
    assert result['french'] == result['repeated'] == french


def function(name):
    return re.search(r'^(?:async )?function ' + re.escape(name) + r'\b[\s\S]*?^\}', APP, re.M).group()


@pytest.mark.parametrize('loaded', [False, True])
@pytest.mark.parametrize('data', [
    {'ok': True, 'chain_length': 1250},
    {'ok': False, 'chain_length': 1250, 'first_break': 42},
    {'status': 'degraded', 'chain_length': 1250, 'unlinked': 7},
    {},
])
def test_integrity_rendering_retains_counts_and_uncertainty(loaded, data):
    body = '''
const vm = require('vm');
const els = {};
['integrity-label','integrity-badge','integrity-icon'].forEach(k => els[k] = {style:{},textContent:'',innerHTML:''});
const context = {
  window: {CLOUD_MODE: false}, document: {getElementById: k => els[k]},
  DICT: {}, EN: __TEST_CATALOG__, LANG: 'en',
  fetchJsonWithTimeout: async () => (__TEST_DATA__)
};
vm.createContext(context);
vm.runInContext(__TEST_SOURCE__, context);
context.loadSecurityIntegrity().then(() => console.log(JSON.stringify({label:els['integrity-label'].textContent,badge:els['integrity-badge'].textContent})));
'''
    values = {'CATALOG': CATALOG if loaded else {}, 'DATA': data,
              'SOURCE': TRANSLATE + '\nvar t=T;\n' + function('loadSecurityIntegrity')}
    body = re.sub(r'__TEST_(\w+)__', lambda match: json.dumps(values[match[1]]), body)
    result = run_js(body)
    assert not re.search(r'\{\w+\}', result['label'])
    if data.get('status') == 'degraded':
        assert '1,250' in result['label'] and '7 events' in result['label']
        assert 'incomplete' in result['label']
        assert 'nothing was altered or removed' not in result['label']
    elif data.get('ok') is True:
        assert '1,250' in result['label'] and 'passed' in result['label']
    elif data.get('ok') is False:
        assert '42' in result['label'] and 'may have changed' in result['label']
        assert result['badge'] == 'Check failed'
    else:
        assert result['badge'] == 'No data'


@pytest.mark.parametrize('loaded', [False, True])
def test_channel_fallbacks_interpolate_the_actual_channel(loaded):
    calls = [APP[c.start:c.end] for c in translations(APP, {'_sigT':2, '_cmI18nFig':1})
             if c.key == 'app.loading_channel_messages']
    values = run_js('var DICT={}, EN=' + json.dumps(CATALOG if loaded else {}) + "; var LANG='en';\n"
                    + TRANSLATE + '\nvar t=T;\nconsole.log(JSON.stringify([' + ','.join(calls) + ']));')
    assert values == ['Loading ' + name + ' messages...' for name in
                      ['TUI', 'WhatsApp', 'Signal', 'Discord', 'Slack', 'Google Chat', 'MS Teams', 'Mattermost']]


@pytest.mark.parametrize('loaded', [False, True, None])
def test_unreachable_list_does_not_claim_data_was_preserved(loaded):
    code = re.search(r'window\.cmStoreUnreachableHtml = function[\s\S]*?^  };', APP, re.M).group()
    prelude = 'var window={};\n'
    if loaded is not None:
        prelude += ('var DICT={},EN=' + json.dumps(CATALOG if loaded else {}) + ";var LANG='en';\n"
                    + TRANSLATE + '\nvar t=T;\n')
    text = run_js(prelude + code + '\nconsole.log(JSON.stringify(window.cmStoreUnreachableHtml("")));')
    assert 'cannot reach the collector' in text
    assert 'Nothing has been lost' not in text
    assert 'cmRetryStoreRead()' in text


@pytest.mark.parametrize('loaded', [False, True])
def test_cost_figure_keeps_html_and_amount_when_catalog_is_unavailable(loaded):
    calls = [call for call in translations(APP, {'_cmI18nFig': 1})
             if call.key == 'efficiency.save_mo' and call.fallback]
    assert len(calls) == 1
    code = ('var DICT={}, EN=' + json.dumps(CATALOG if loaded else {}) + "; var LANG='en';\n"
            + TRANSLATE + '\nvar t=T;\n'
            + 'function escHtml(s) { return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;"); }\n'
            + function('_cmI18nFig') + '\nconsole.log(JSON.stringify(_cmI18nFig('
            + json.dumps(calls[0].key) + ',' + json.dumps(calls[0].fallback)
            + ',\'<span title="Published rates">12.34 USD</span>\')));')
    rendered = run_js(code)
    assert rendered == 'save about <span title="Published rates">12.34 USD</span>/mo'
    assert '{amt}' not in rendered and '\0' not in rendered


def test_parameterized_fallbacks_are_checked_and_keep_the_same_values():
    keys = {
        'app.n_minutes', 'app.n_hours', 'app.n_days', 'alerts.feed_stopped',
        'overview.hb_banner_silent', 'overview.hb_banner_delayed',
        'needs.n_working', 'needs.n_quiet', 'needs.never_asks', 'needs.n_waiting',
        'needs.more', 'skills.never_used_verdict', 'quality.oc_scope',
        'efficiency.grade_sentence', 'usage.cost_about', 'usage.tokens_sub',
        'transcript.history_gap_count', 'inputs.seen_turns', 'inputs.tools_count',
        'inputs.not_exposed', 'profile.trial_days_left', 'profile.plan',
    }
    calls, found = [], set()
    for source in [APP, (ROOT / 'clawmetry/static/js/gw-setup.js').read_text()]:
        for call in translations(source):
            if call.key in keys:
                assert call.fallback is not None and call.pending is None, call.key
                found.add(call.key)
                calls.append(source[call.start:call.end])
    assert found == keys
    values = '''
var mins=7, hours=4, days=3, dur='4 hours', gapStr='7 minutes', intervalMin=5;
var working=2, quiet=3, rtName='Hermes', items=Array(8), unusedCount=4;
var hit=31, ctx='12k', costStr='12.34 USD', tokStr='12,345', n=9;
var item={turns:5}, names=['Read','Write'], turns=6, rt='Hermes', toolNames=['Read','Write'];
var d=3, label='Pro';
'''
    code = ("var DICT={},EN={},LANG='en';\n" + TRANSLATE + '\nvar t=T;\n' + values
            + 'function render(){return [' + ','.join(calls) + '];}\n'
            + 'var absent=render(); EN=' + json.dumps(CATALOG)
            + ';console.log(JSON.stringify([absent,render()]));')
    absent, loaded = run_js(code)
    assert absent == loaded
    assert not any(re.search(r'\{\w+\}', text) for text in absent)
    assert 'about 12.34 USD' in absent
    assert '12,345 tokens' in absent
    assert '9 earlier messages not loaded' in absent
    assert 'Trial · 3 days left' in absent


@pytest.mark.parametrize('loaded', [False, True, None])
def test_owner_fallback_is_a_label_before_the_catalog_loads(loaded):
    code = ''
    if loaded is not None:
        code = ('var DICT={},EN=' + json.dumps(CATALOG if loaded else {})
                + ";var LANG='en';\n" + TRANSLATE + '\nvar t=T;\n')
    code += function('_invOwnerLabel')
    code += '\nconsole.log(JSON.stringify([{}, {owner:" Jamie "}, {owner:" "}, {owner:0}].map(_invOwnerLabel)));'
    assert run_js(code) == ['me', 'Jamie', 'me', '0']


@pytest.mark.parametrize('loaded', [False, True])
def test_duration_fallbacks_keep_counts_and_units(loaded):
    code = ('var DICT={},EN=' + json.dumps(CATALOG if loaded else {})
            + ";var LANG='en';\n" + TRANSLATE + '\nvar t=T;\n'
            + function('_cmHumanizeMinutes')
            + '\nconsole.log(JSON.stringify([1,2,60,120,2880,4320].map(_cmHumanizeMinutes)));')
    assert run_js(code) == ['1 minute', '2 minutes', '1 hour', '2 hours', '2 days', '3 days']


@pytest.mark.parametrize('loaded', [False, True, None])
@pytest.mark.parametrize('days', [1, 2, 3])
def test_trial_banner_retains_count_and_grammar_before_translation_loads(loaded, days):
    code = '''
var window={}, els={'license-expired-banner':{style:{}},'license-expired-msg':{textContent:''}};
var document={getElementById:k=>els[k]}, localStorage={getItem:()=>null};
var fetches=0;
'''
    code += ('var fetch=async()=>{fetches++;return {json:async()=>({tier:"trial",expired:false,days_until_expiry:'
             + str(days) + '})}};\n')
    if loaded is not None:
        code += ('var DICT={},EN=' + json.dumps(CATALOG if loaded else {})
                 + ";var LANG='en';\n" + TRANSLATE + '\nwindow.t=T;\n')
    code += function('checkLicenseExpiry')
    code += ('\ncheckLicenseExpiry().then(()=>console.log(JSON.stringify({text:els["license-expired-msg"].textContent,'
             'display:els["license-expired-banner"].style.display,fetches})));')
    result = run_js(code)
    unit = 'day' if days == 1 else 'days'
    assert result == {'text': f'Your trial ends in {days} {unit}. Upgrade to keep every runtime.',
                      'display': 'flex', 'fetches': 1}


def test_trial_templates_are_extracted_instead_of_remaining_dynamic():
    keys = {'trial.pill_hours', 'trial.pill_days', 'trial.modal_sub_days', 'trial.device',
            'trial.pill_one_hour', 'trial.modal_sub_one_day', 'trial.per_year', 'trial.per_month',
            'banners.trial_ending_msg', 'banners.trial_ending_one_day_msg'}
    found = set()
    for source in [APP, (ROOT / 'clawmetry/static/js/trial-pill.js').read_text()]:
        for call in translations(source, {'tr': 2}):
            if call.key in keys:
                assert call.fallback is not None and call.pending is None, call.key
                assert call.fallback == CATALOG[call.key], call.key
                found.add(call.key)
    assert found == keys


@pytest.mark.parametrize('loaded', [False, True])
@pytest.mark.parametrize('count', [1, 2])
def test_orchestration_badge_retains_counts_and_singular_labels(loaded, count):
    code = ('var DICT={},EN=' + json.dumps(CATALOG if loaded else {})
            + ";var LANG='en';\n" + TRANSLATE + '\nvar t=T;\n'
            + 'function escHtml(s){return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");}\n'
            + 'var _brainOrchSummaries={s:{workflows:{total:' + str(count)
            + ',running:1},agents:{total:5,completed:2,failed:1},subagents:{total:' + str(count)
            + '},running_now:[{nowTool:"<Read>"}]}};\n'
            + function('_brainOrchBadgeHtml')
            + '\nconsole.log(JSON.stringify(_brainOrchBadgeHtml("s")));')
    html = run_js(code)
    assert f'{count} workflow' + ('s' if count != 1 else ' (') in html
    assert f'{count} sub-agent' + ('s' if count != 1 else ' ·') in html
    assert '3/5 agents done' in html and '(1 running)' in html
    assert '&lt;Read&gt;' in html and '<Read>' not in html


@pytest.mark.parametrize('loaded', [False, True])
@pytest.mark.parametrize('action,stem,tab', [
    ('model_downgrade', 'model', 'models'),
    ('context_trim', 'ctx', 'context-economics'),
    ('cache_warm', 'reread', 'context-economics'),
    ('thinking_trim', 'think', 'usage'),
])
def test_efficiency_recommendation_retains_explanation_and_evidence(loaded, action, stem, tab):
    metadata = re.search(r'^var _CM_EFF_IDEAS = \{[\s\S]*?^\};', APP, re.M).group()
    code = ('var DICT={},EN=' + json.dumps(CATALOG if loaded else {})
            + ";var LANG='en';\n" + TRANSLATE + '\nvar t=T;\n'
            + 'function escHtml(s){return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");}\n'
            + metadata + '\n' + function('_cmI18nFig') + '\n' + function('_cmEffIdeaRowHtml')
            + '''
var figures=[];
var window={cmCostFigure:(amount,entry,opts)=>{
  figures.push({amount,entry,opts});
  return '<span title="Estimated at published rates">'+amount+' USD</span>';
}};
var row=_cmEffIdeaRowHtml({id:''' + json.dumps(action) + ''',model:'<Main>',
  data:{calls:17,target_model:'<Small>',thinking_pct_of_output_cost:42},savings_monthly_usd:12.6},
  {basis:'estimate'});
console.log(JSON.stringify({row,figures,unknown:_cmEffIdeaRowHtml({id:'unknown'},{})}));
''')
    result = run_js(code)
    html = result['row']
    assert CATALOG[f'efficiency.idea_{stem}_title'] in html
    assert 'How' in html and 'See the evidence' in html
    assert f"switchTab('{tab}')" in html
    assert 'save about <span title="Estimated at published rates">13 USD</span>/mo' in html
    assert not re.search(r'\{\w+\}', html)
    assert '<Main>' not in html and '<Small>' not in html
    if stem == 'model':
        assert '&lt;Main&gt; for 17 short tasks' in html and '&lt;Small&gt;' in html
    elif stem == 'think':
        assert '42%' in html
    elif stem == 'ctx':
        assert '/compact' in html
    else:
        assert 'same session' in html
    assert result['figures'] == [{'amount': 13, 'entry': {'basis': 'estimate'},
                                 'opts': {'noBadge': True, 'label': 'Estimated saving per month'}}]
    assert result['unknown'] == ''


def test_efficiency_recommendation_templates_are_checked():
    keys = {f'efficiency.idea_{stem}_{field}' for stem in ('model', 'ctx', 'reread', 'think')
            for field in ('title', 'finding', 'how')}
    calls = [call for call in translations(APP) if call.key in keys]
    assert {call.key for call in calls} == keys
    assert len(calls) == len(keys)
    for call in calls:
        assert call.pending is None
        assert call.fallback == CATALOG[call.key]


@pytest.mark.parametrize('loaded', [False, True])
def test_trace_and_spend_labels_follow_the_catalog_at_render_time(loaded):
    declarations = '\n'.join(re.search(r'^var ' + name + r' = [\s\S]*?^[}\]];', APP, re.M).group()
                             for name in ('_TRACE_KIND_COLORS', '_TRACE_LEGEND_KINDS', '_CM_SF_IN', '_CM_SF_OUT'))
    code = ('var DICT={},EN={},LANG="en";\n' + TRANSLATE + '\nvar t=T;\n'
            + declarations + '\n' + function('_traceLegendHtml') + '\n' + function('_sfLabel')
            + '\nEN=' + json.dumps(CATALOG if loaded else {}) + ';\n'
            + '''console.log(JSON.stringify({legend:_traceLegendHtml(),
              input:Object.keys(_CM_SF_IN).map(k=>_sfLabel(_CM_SF_IN,k)),
              output:Object.keys(_CM_SF_OUT).map(k=>_sfLabel(_CM_SF_OUT,k)),
              unknown:_sfLabel(_CM_SF_IN,'new_kind')}));''')
    result = run_js(code)
    for label in ('Agent', 'Prompt', 'Model call', 'Reasoning', 'Tool'):
        assert label in result['legend']
    assert result['input'] == ['Your messages', 'Earlier replies (context)', 'Tool results',
                               'System prompt and tool definitions']
    assert result['output'] == ['Thinking', 'Replies', 'Tool calls', 'MCP tool calls']
    assert result['unknown'] == 'new_kind'
    assert result['legend'].count('width:9px;height:9px') == 5


@pytest.mark.parametrize('translator', ['absent', 'empty', 'loaded', 'throws'])
def test_trail_explanations_and_context_values_work_before_translation_loads(translator):
    trail = (ROOT / 'clawmetry/static/js/trail.js').read_text()
    helper = re.search(r'^  function T\([\s\S]*?^  \}', trail, re.M).group()
    outcomes = re.search(r'^  var OUTCOMES = \{[\s\S]*?^  \};', trail, re.M).group()
    renderer = re.search(r'^  function outcomeMeta\([\s\S]*?^  \}', trail, re.M).group()
    code = ''
    if translator in ('empty', 'loaded'):
        code = ('var DICT={},EN=' + json.dumps(CATALOG if translator == 'loaded' else {})
                + ';var LANG="en";\n' + TRANSLATE.replace('function T(', 'function realTranslate(')
                + '\nvar t=realTranslate;\n')
    elif translator == 'throws':
        code = 'var t=()=>{throw new Error("translation unavailable")};\n'
    code += helper + '\n' + outcomes + '\n' + renderer
    code += '''
console.log(JSON.stringify({outcomes:Object.fromEntries(Object.keys(OUTCOMES).map(k=>[k,outcomeMeta(k)])),
  unknown:outcomeMeta('new_kind'), normalized:outcomeMeta('SUCCESS'),
  count:T('trail.ctx_changed','Recorded {n} times during the session. Showing the last.',{n:2}),
  keys:T('trail.ctx_changed_keys','Changed during the session: {keys}. Showing the last.',{keys:'model, tools_count'})}));
'''
    result = run_js(code)
    colors = {'success': '#22c55e', 'failed': '#ef4444', 'escalated': '#f59e0b',
              'cognitive_loop': '#f97316', 'tool_call_stuck': '#f97316',
              'ongoing': '#3b82f6', 'waiting': '#8b5cf6'}
    assert set(result['outcomes']) == set(colors)
    for key, color in colors.items():
        assert result['outcomes'][key] == {'color': color, 'name': CATALOG[f'trail.outcome_{key}'],
                                            'explain': CATALOG[f'trail.outcome_{key}_why']}
    assert result['unknown'] is None
    assert result['normalized'] == result['outcomes']['success']
    assert result['count'] == 'Recorded 2 times during the session. Showing the last.'
    assert result['keys'] == 'Changed during the session: model, tools_count. Showing the last.'


def test_table_driven_labels_have_complete_checked_templates():
    keys = {f'tracing.legend_{kind}' for kind in ('agent', 'prompt', 'llm', 'reasoning', 'tool')}
    keys.update(f'usage.sf_{kind}' for kind in ('user_prompts', 'prior_assistant', 'tool_results',
                                              'overhead', 'thinking', 'text', 'builtin', 'mcp'))
    keys.update(f'trail.outcome_{kind}{suffix}' for kind in ('success', 'failed', 'escalated',
               'cognitive_loop', 'tool_call_stuck', 'ongoing', 'waiting') for suffix in ('', '_why'))
    calls = []
    for source in (APP, (ROOT / 'clawmetry/static/js/trail.js').read_text()):
        calls.extend(call for call in translations(source, {'T': 1}) if call.key in keys)
    assert {call.key for call in calls} == keys
    assert len(calls) == len(keys)
    for call in calls:
        assert call.pending is None
        assert call.fallback == CATALOG[call.key]
