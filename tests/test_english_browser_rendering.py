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
