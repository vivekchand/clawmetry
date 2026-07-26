// renderBrainTypeChips must count only the selected runtime's events.
//
// The Brain LIST (renderBrainStream) and CHART (renderBrainChart) scope to
// the header's runtime switcher, but the type-count chips counted the whole
// node-wide event array. On a ?runtime=cursor tab whose window held mostly
// Claude Code events, the user saw "AGENT (84)" chips above a 1-row stream
// (live-hit 2026-07-25) — counts that contradict the list they label.
//
// Extraction pattern mirrors test_brain_time_range.js: pull the shipped
// function out of app.js via regex + vm so the test tracks the real source.

const fs = require('fs');
const path = require('path');
const vm = require('vm');

const APP_JS = path.join(__dirname, '..', 'clawmetry', 'static', 'js', 'app.js');
const src = fs.readFileSync(APP_JS, 'utf8');

let passed = 0;
let failed = 0;

function truthy(v, label) {
  if (v) { passed++; console.log('  ok   ' + label); }
  else { failed++; console.log('  FAIL ' + label + ' (got falsy)'); }
}

function extractFunction(name) {
  const re = new RegExp('^function ' + name + '\\b[\\s\\S]*?^\\}', 'm');
  const m = src.match(re);
  if (!m) throw new Error('could not find function ' + name + ' in app.js');
  return m[0];
}

function chipsHtmlFor(runtimeFilter, events) {
  const container = { innerHTML: '' };
  const sandbox = {
    document: { getElementById: (id) => (id === 'brain-type-chips' ? container : null) },
    _brainTypeFilter: 'all',
    // Header switcher state + the same helpers the list/chart use.
    _cmRuntimeFilter: () => runtimeFilter,
    _cmClientFilterRt: (rt) => rt,
    _cmRuntimeOf: (ev) => ev.runtime || 'openclaw',
    console,
  };
  vm.createContext(sandbox);
  vm.runInContext(extractFunction('renderBrainTypeChips'), sandbox);
  vm.runInContext(
    'renderBrainTypeChips(' + JSON.stringify(events) + ')', sandbox);
  return container.innerHTML;
}

const MIXED = [
  { type: 'AGENT', runtime: 'claude_code' },
  { type: 'AGENT', runtime: 'claude_code' },
  { type: 'EXEC',  runtime: 'claude_code' },
  { type: 'USER',  runtime: 'cursor' },
  { type: 'AGENT', runtime: 'cursor' },
];

{
  const html = chipsHtmlFor('cursor', MIXED);
  truthy(html.indexOf('USER (1)') >= 0,
         'cursor scope: USER counts only cursor events');
  truthy(html.indexOf('AGENT (1)') >= 0,
         'cursor scope: AGENT count excludes claude_code AGENT rows');
  truthy(html.indexOf('EXEC') < 0,
         'cursor scope: other-runtime-only types disappear');
}

{
  const html = chipsHtmlFor('all', MIXED);
  truthy(html.indexOf('AGENT (3)') >= 0, 'all scope: node-wide AGENT count kept');
  truthy(html.indexOf('EXEC (1)') >= 0, 'all scope: EXEC chip present');
}

{
  // Helpers absent (old embeds, race at parse time): degrade to node-wide.
  const container = { innerHTML: '' };
  const sandbox = {
    document: { getElementById: () => container },
    _brainTypeFilter: 'all',
    console,
  };
  vm.createContext(sandbox);
  vm.runInContext(extractFunction('renderBrainTypeChips'), sandbox);
  vm.runInContext('renderBrainTypeChips(' + JSON.stringify(MIXED) + ')', sandbox);
  truthy(container.innerHTML.indexOf('AGENT (3)') >= 0,
         'no helpers: falls back to unscoped counts, never throws');
}

console.log('');
console.log('PASS ' + passed + ' / FAIL ' + failed);
process.exit(failed === 0 ? 0 : 1);
