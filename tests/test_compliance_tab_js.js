// Node tests for clawmetry/static/js/compliance.js, run by
// tests/test_compliance_tab_shell.py::test_compliance_tab_js_suite.
//
// REQ-COMP-FWM-004 (Factory requirement 2b319261-73a2-4f64-b497-3dd80b99a72e).
// These fail when the tab would present a fabricated control state as met.
'use strict';

const assert = require('assert');
const path = require('path');
const C = require(path.join(__dirname, '..', 'clawmetry', 'static', 'js', 'compliance.js'));

let passed = 0;
function test(name, fn) {
  fn();
  passed += 1;
  console.log('PASS ' + name);
}

function guardReport(controls) {
  return {
    framework: { id: 'mitre-atlas', name: 'MITRE ATLAS', edition: '2026.08',
      evaluation: 'guard_contract', mapping_version: '2026-09-14.1' },
    period: { from: '2026-07-01T00:00:00+00:00', to: '2026-07-31T23:59:59+00:00' },
    scope_note: 'Coverage, not compliance. This report is supporting evidence for review, not a certification.',
    summary: {},
    scenario_traceability: { available: true, suite_version: '2026-09-14.2', tier: 'fixture_replay',
      tier_note: 'Fixture replay: no agent ran.', atlas: { edition: '2026.08' },
      variants: ['cold_start', 'learned_baseline'] },
    controls: controls,
  };
}

const exercised = { id: 'AML.T0086', text: 'Exfiltration via AI Agent Tool Invocation', status: 'exercised',
  coverage_mode: 'detect', pre_action_control: false, finding_kinds: ['network_egress'],
  evidence: { findings: 2, sessions: 1, runtimes: ['claude_code'], first_evidence_at: 'a', last_evidence_at: 'b',
    policy_decisions: { configured: 0, exercised: 0, failed: 0 } },
  scenarios: { links: [{ case: 'AML.CS0049', case_name: 'Poisoned skill', scenario: 'cs0049-poisoned-skill', stage: 'S09-S10',
    decisive: true, title: 't', steps: [{ step: 'S09', technique: 'AML.T0074', technique_name: 'Masquerading' }],
    match: ['finding_kind:network_egress'],
    variants: { cold_start: { outcome: 'observed', class: 'missed', finding_kinds: [] },
      learned_baseline: { outcome: 'detected', class: 'passing', finding_kinds: ['network_egress'] } } }],
    benign: [{ scenario: 'control-openclaw-ordinary-day', stage: 'day', variants: {} }],
    fail_modes: [], summary: { false_positives: 0 } } };

test('AC-COMP-FWM-004.5 effective is not a recognised state for any framework', function () {
  assert.strictEqual(C.stateInfo('effective').known, false);
  assert.strictEqual(C.stateInfo('effective', C.GUARD_ORDER).known, false);
  assert.strictEqual(C.stateInfo('effective', C.MAP_ORDER).known, false);
  assert.ok(C.GUARD_ORDER.indexOf('effective') < 0 && C.MAP_ORDER.indexOf('effective') < 0);
  // A state from the other evaluator is not borrowed either.
  assert.strictEqual(C.stateInfo('operating', C.GUARD_ORDER).known, false);
});

test('AC-COMP-FWM-004.5 a fabricated effective control is shown unrecognised and not counted', function () {
  const fake = Object.assign({}, exercised, { id: 'AML.T0055', status: 'effective' });
  const report = guardReport([exercised, fake]);
  const counts = C.summaryCounts(report);
  assert.strictEqual(counts.exercised, 1);
  assert.strictEqual(counts.unrecognised, 1);
  assert.strictEqual(counts.total, 2);
  const html = C.renderReport(report);
  // The forged control is the last card, so its block runs to the end.
  const block = html.slice(html.indexOf('data-control="AML.T0055"'));
  assert.ok(block.indexOf('Unrecognised state: effective') >= 0);
  assert.ok(block.indexOf('cm-comp-state-unrecognised') >= 0);
  assert.strictEqual(block.indexOf('cm-comp-state-exercised'), -1);
  assert.ok(block.indexOf('does not assign this state') >= 0);
  assert.ok(html.indexOf('data-state="unrecognised"') >= 0);
});

test('AC-COMP-FWM-004.5 an unrecognised scenario result is not shown as detected', function () {
  const forged = JSON.parse(JSON.stringify(exercised));
  forged.scenarios.links[0].variants.cold_start.class = 'effective';
  const html = C.renderReport(guardReport([forged]));
  assert.ok(html.indexOf('Unrecognised result: effective') >= 0);
  assert.ok(html.indexOf('cm-comp-link-unrecognised') >= 0);
});

test('AC-COMP-FWM-004.1 AC-COMP-FWM-004.2 evidence, gap and unknown controls are all shown and counted', function () {
  const gap = { id: 'AML.X', text: 'gap item', status: 'gap', finding_kinds: [], evidence: null,
    gap_reason: 'No Guard finding kind is mapped to this item.', scenarios: { links: [], note: 'Gap: no finding kind is mapped.' } };
  const unknown = { id: 'AML.Y', text: 'unknown item', status: 'unknown', finding_kinds: ['stuck_loop'], evidence: null,
    caveats: ['evidence unavailable: guard_findings (daemon did not answer)'], scenarios: { links: [] } };
  const report = guardReport([exercised, gap, unknown]);
  const html = C.renderReport(report);
  const counts = C.summaryCounts(report);
  assert.deepStrictEqual([counts.exercised, counts.gap, counts.unknown, counts.total], [1, 1, 1, 3]);
  ['No Guard finding kind is mapped', 'evidence unavailable', 'Stored findings in period', 'claude_code',
    'Policy decisions', 'AML.CS0049', 'S09-S10 (decisive)', 'Missed', 'Detected', 'learned baseline',
    'Benign scenarios replayed: 1', 'fixture_replay'].forEach(function (needle) {
    assert.ok(html.indexOf(needle) >= 0, 'missing: ' + needle);
  });
});

test('AC-COMP-FWM-004.6 no percentage and no certification claim', function () {
  // Copy only: inline styles (width:100%) are layout, not a claim.
  const html = C.renderReport(guardReport([exercised])).replace(/style="[^"]*"/g, '');
  assert.ok(html.indexOf('%') < 0);
  const low = html.toLowerCase();
  assert.ok(low.indexOf('certified') < 0 && low.indexOf('compliant') < 0);
  assert.ok(low.indexOf('not a certification') >= 0);
});

test('AC-COMP-FWM-004.3 locked state is an upgrade prompt with no code', function () {
  const html = C.lockedHtml();
  assert.ok(html.indexOf('Compliance Pack') >= 0 && html.indexOf('pricing') >= 0);
  assert.ok(!/402|upgrade_required|error/i.test(html.replace(/https?:\/\/[^"]+/g, '')));
});

test('AC-COMP-FWM-004.4 hosted state explains local evaluation, no upgrade prompt', function () {
  const html = C.localOnlyHtml();
  assert.ok(html.indexOf('machine your agents run on') >= 0);
  assert.ok(html.indexOf('localhost') >= 0 && html.indexOf('clawmetry compliance bundle') >= 0);
  assert.ok(!/upgrade|trial|pricing|402/i.test(html));
});

test('errors never show a status or an error code', function () {
  [{}, { error: 'evaluation_failed', detail: 'boom' }, { error: 'unknown_framework' },
    { error: 'report_inconsistent', problems: ['AML.T0086: exercised with no stored finding'] }].forEach(function (b) {
    const html = C.errorHtml(b);
    assert.ok(!/\b(402|404|500)\b|evaluation_failed|report_inconsistent|unknown_framework/.test(html), html);
  });
  assert.ok(C.errorHtml({ error: 'report_inconsistent', problems: ['x'] }).indexOf('consistency check') >= 0);
});

test('values are escaped', function () {
  const evil = Object.assign({}, exercised, { text: '<img src=x onerror=alert(1)>', caveats: ['<script>x</script>'] });
  const html = C.renderReport(guardReport([evil]));
  assert.ok(html.indexOf('<img src=x') < 0 && html.indexOf('<script>') < 0);
  assert.ok(html.indexOf('&lt;img') >= 0);
});

test('the period query covers the whole last day', function () {
  assert.strictEqual(C.query('mitre-atlas', '2026-07-01', '2026-07-31'),
    'framework=mitre-atlas&from=2026-07-01&to=2026-07-31T23%3A59%3A59');
});

console.log(passed + ' tests PASS');
