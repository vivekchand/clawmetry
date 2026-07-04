// Guard for the "Cost tab stuck on Loading…" regression (founder report
// 2026-07-02, cloud + localhost).
//
// /api/usage returns trend:{} when there is not enough history yet. The old
// guard `if (!trend || trend.trend === 'insufficient_data')` let an empty {}
// through (it is truthy, and trend.trend is undefined), so the next line
// `trend.trend.charAt(0)` threw. Because displayTrendAnalysis runs EARLY inside
// loadUsage's try block, the throw aborted every Cost card after it and they all
// stayed on "Loading…".
//
// We pull displayTrendAnalysis out of the shipped app.js via brace-matching +
// vm (same approach as test_brain_sse_reconnect.js) and assert it never throws
// on an empty/partial/null trend, and still renders a real trend.

const fs = require('fs');
const path = require('path');
const vm = require('vm');

const APP_JS = path.join(__dirname, '..', 'clawmetry', 'static', 'js', 'app.js');
const src = fs.readFileSync(APP_JS, 'utf8');

// Extract `function displayTrendAnalysis(...) { ... }` by matching braces.
const start = src.indexOf('function displayTrendAnalysis');
if (start === -1) { console.error('FAIL: displayTrendAnalysis not found in app.js'); process.exit(1); }
let i = src.indexOf('{', start);
let depth = 0, end = -1;
for (; i < src.length; i++) {
  if (src[i] === '{') depth++;
  else if (src[i] === '}') { depth--; if (depth === 0) { end = i + 1; break; } }
}
const fnSrc = src.slice(start, end);

// Minimal DOM stub: getElementById returns a fake element with a style object
// and a settable textContent so the function can run headlessly.
function makeEl() { return { style: {}, textContent: '', innerHTML: '' }; }
const els = {};
const sandbox = {
  document: { getElementById: function (id) { return (els[id] = els[id] || makeEl()); } },
  console: console,
};
vm.createContext(sandbox);
vm.runInContext(fnSrc + '\nthis.displayTrendAnalysis = displayTrendAnalysis;', sandbox);

let passed = 0, failed = 0;
function ok(name, fn) {
  try { fn(); passed++; console.log('  ok - ' + name); }
  catch (e) { failed++; console.error('  FAIL - ' + name + ': ' + e.message); }
}

ok('empty trend {} does not throw (the regression)', function () {
  sandbox.displayTrendAnalysis({}, { month: 100, monthCost: 1 });
});
ok('empty trend {} hides the trend card', function () {
  els['trend-card'] = makeEl();
  sandbox.displayTrendAnalysis({}, {});
  if (els['trend-card'].style.display !== 'none') throw new Error('card not hidden');
});
ok('null trend does not throw', function () {
  sandbox.displayTrendAnalysis(null, {});
});
ok('insufficient_data hides the card', function () {
  els['trend-card'] = makeEl();
  sandbox.displayTrendAnalysis({ trend: 'insufficient_data' }, {});
  if (els['trend-card'].style.display !== 'none') throw new Error('card not hidden');
});
ok('a real trend still renders a direction', function () {
  els['trend-card'] = makeEl(); els['trend-direction'] = makeEl(); els['trend-prediction'] = makeEl();
  sandbox.displayTrendAnalysis({ trend: 'increasing', dailyAvg: 1000, monthlyPrediction: 30000 },
                               { month: 30000, monthCost: 3 });
  if (!/Increasing/.test(els['trend-direction'].textContent)) throw new Error('direction not rendered');
});

console.log('\n' + passed + ' passed, ' + failed + ' failed');
process.exit(failed ? 1 : 0);
