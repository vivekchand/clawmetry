// Unit tests for the Brain density chart's time axis (_brainAxisTicks).
//
// The density chart's window is DERIVED (adaptive in Live mode, explicit in
// history mode), so without axis labels the same bars could mean "last hour"
// or "last day". _brainAxisTicks is the pure helper that decides tick
// positions, label format, and when labels must carry the date (window
// longer than ~20h or crossing midnight) so "03:00" can't be mistaken for
// today.
//
// Extraction pattern mirrors test_brain_time_range.js: pull the shipped
// function out of app.js via regex + vm so the test always tracks the real
// source, no bundler needed.

const fs = require('fs');
const path = require('path');
const vm = require('vm');

const APP_JS = path.join(__dirname, '..', 'clawmetry', 'static', 'js', 'app.js');
const src = fs.readFileSync(APP_JS, 'utf8');

let passed = 0;
let failed = 0;

function eq(actual, expected, label) {
  if (actual === expected) { passed++; console.log('  ok   ' + label); }
  else {
    failed++;
    console.log('  FAIL ' + label);
    console.log('       expected: ' + JSON.stringify(expected));
    console.log('       actual:   ' + JSON.stringify(actual));
  }
}

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

const sandbox = {};
vm.createContext(sandbox);
vm.runInContext(extractFunction('_brainAxisTicks'), sandbox);
const _brainAxisTicks = sandbox._brainAxisTicks;

// Local-time constructors keep the midnight-crossing cases deterministic in
// any TZ the CI matrix runs in (toDateString compares local days).
const noonStart = new Date(2026, 6, 10, 12, 0).getTime();

console.log('time-only window (1h, same local day)');
{
  const r = _brainAxisTicks(noonStart, noonStart + 3600000, 800);
  eq(r.withDate, false, 'same-day 1h window needs no date in labels');
  eq(r.ticks.length, 7, '800px time-only chart gets 7 ticks');
  eq(r.ticks[0].frac, 0, 'first tick sits at the window start');
  eq(r.ticks[r.ticks.length - 1].frac, 1, 'last tick sits at the window end');
  let monotonic = true;
  for (let i = 1; i < r.ticks.length; i++) {
    if (!(r.ticks[i].frac > r.ticks[i - 1].frac)) monotonic = false;
  }
  truthy(monotonic, 'tick fractions strictly increase');
  truthy(r.ticks.every(function (t) { return typeof t.label === 'string' && t.label.length > 0; }),
    'every tick carries a non-empty label');
}

console.log('date-bearing windows');
{
  const day = _brainAxisTicks(noonStart, noonStart + 86400000, 800);
  eq(day.withDate, true, '24h window puts the date in labels');
  eq(day.ticks.length, 5, 'date-bearing labels are wider: 800px gets 5 ticks');

  const midnight = new Date(2026, 6, 10, 23, 30).getTime();
  const cross = _brainAxisTicks(midnight, midnight + 3600000, 800);
  eq(cross.withDate, true, 'a 1h window crossing midnight still shows the date');
}

console.log('narrow charts and degenerate input');
{
  const narrow = _brainAxisTicks(noonStart, noonStart + 3600000, 120);
  eq(narrow.ticks.length, 2, 'a narrow chart keeps at least start + end ticks');

  eq(_brainAxisTicks(noonStart, noonStart, 800).ticks.length, 0, 'zero span yields no ticks');
  eq(_brainAxisTicks(noonStart + 10, noonStart, 800).ticks.length, 0, 'negative span yields no ticks');
  eq(_brainAxisTicks(noonStart, noonStart + 3600000, 0).ticks.length, 0, 'zero width yields no ticks');
  eq(_brainAxisTicks(NaN, noonStart, 800).ticks.length, 0, 'NaN bounds yield no ticks');
}

console.log('');
if (failed) {
  console.log('FAIL: ' + failed + ' assertion(s) failed, ' + passed + ' passed');
  process.exit(1);
}
console.log('PASS: all ' + passed + ' assertions passed');
