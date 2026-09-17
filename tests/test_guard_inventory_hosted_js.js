// A card that reads local-only data must not ASK for it on the hosted
// dashboard (#6060).
//
// `/api/guard/inventory` and `/api/local/agent-graph` are classified
// `cloud-disabled` in clawmetry-cloud's cloud_route_policy, which answers
// 410 Gone on purpose: the data is collected by the daemon on the machine the
// agents run on, is not in the encrypted snapshot, and a passthrough would
// report "nothing inventoried" for a node that has an inventory.
//
// The bug this pins is that handling the 410 inside `.then()` is NOT enough.
// Chromium logs a failed request as
//   "Failed to load resource: the server responded with a status of 410 (Gone)"
// before any JS sees the Response, and the cloud-contract deploy spec counts
// every console error. Measured in a real Chromium page against the shipped
// loader: correct copy in the card, and one console error anyway. That error
// failed three assertions in the deploy smoke gate ("Approvals: no new JS
// errors", "Alerts: no new JS errors", "zero unexpected JS errors"), which
// held production on 0.12.883 while 0.12.884 and 0.12.885 both failed to
// promote.
//
// So the only fix that works is to not issue the request when the page knows
// it is hosted, while still rendering the honest local-only sentence.
//
// Runs under `node tests/test_guard_inventory_hosted_js.js` (no jsdom, no
// browser, ~50ms). Pulls the real functions out of app.js so this tests
// shipped source.

const fs = require('fs');
const path = require('path');
const vm = require('vm');

// CM_APP_JS lets this suite be pointed at another copy of app.js, which is how
// you check that it actually fails on the code before a fix. CI leaves it
// unset and the shipped file is tested.
const APP_JS = process.env.CM_APP_JS
  || path.join(__dirname, '..', 'clawmetry', 'static', 'js', 'app.js');
const src = fs.readFileSync(APP_JS, 'utf8');

let passed = 0;
let failed = 0;

function ok(cond, label) {
  if (cond) {
    passed++;
    console.log('  ok   ' + label);
  } else {
    failed++;
    console.log('  FAIL ' + label);
  }
}

function extract(name) {
  const re = new RegExp('^function ' + name + '\\b[\\s\\S]*?^\\}', 'm');
  const m = src.match(re);
  if (!m) throw new Error('could not find function ' + name + ' in app.js');
  return m[0];
}

function constant(name) {
  const re = new RegExp('^var ' + name + '\\s*=[\\s\\S]*?;$', 'm');
  const m = src.match(re);
  // A build that predates the fix has no such constant; the behaviour checks
  // below are what report that, not a crash here.
  return m ? m[0] : 'var ' + name + " = '';";
}

// ── A DOM small enough to read, big enough for these two cards ─────────────
function makeElement() {
  return { innerHTML: '', textContent: '', style: {} };
}

function makeSandbox(opts) {
  const els = {};
  ['guard-inventory-body', 'guard-inventory-summary', 'agent-graph-status',
   'agent-graph-svg', 'agent-graph-stats', 'agent-graph-stats-inner'].forEach(function (id) {
    els[id] = makeElement();
  });
  const fetched = [];
  const consoleErrors = [];

  const sandbox = {
    els: els,
    fetched: fetched,
    consoleErrors: consoleErrors,
    window: { CLOUD_MODE: opts.cloudMode },
    document: {
      getElementById: function (id) { return els[id] || null; }
    },
    console: {
      error: function () { consoleErrors.push(Array.prototype.slice.call(arguments)); },
      warn: function () {},
      log: function () {}
    },
    Date: Date,
    Number: Number,
    String: String,
    Math: Math,
    isNaN: isNaN,
    Error: Error,
    Promise: Promise,
    setTimeout: setTimeout,
    fetch: function (url) {
      fetched.push(url);
      return Promise.resolve(opts.response || { ok: true, status: 200,
                                                json: function () { return Promise.resolve({}); } });
    },
    // Helpers the extracted functions lean on.
    t: function (key, args, fallback) { return fallback; },
    _cmClientFilterRt: function () { return 'all'; },
    _cmRuntimeFilter: function () { return 'all'; },
    _renderAgentGraph: function () { sandbox.rendered = true; },
    parseInt: parseInt
  };
  vm.createContext(sandbox);
  vm.runInContext(
    constant('GUARD_INVENTORY_LOCAL_ONLY') + '\n'
    + 'var GUARD_COMPONENT_KIND_LABEL = {}; var GUARD_RUNTIME_LABEL = {};\n'
    + 'function guardEsc(s){return String(s==null?"":s);}\n'
    + 'function guardAgo(){return "";}\n'
    + 'function guardInventoryStatus(){return "";}\n'
    + extract('loadGuardInventory') + '\n'
    + extract('loadAgentGraph') + '\n'
    + 'this._inv = loadGuardInventory; this._graph = loadAgentGraph;', sandbox);
  return sandbox;
}

// Let any promise chain the loader started settle.
function settle() {
  return new Promise(function (resolve) { setTimeout(resolve, 0); })
    .then(function () { return new Promise(function (r) { setTimeout(r, 0); }); });
}

async function main() {
  console.log('Guard inventory card on the hosted dashboard (#6060)');

  // THE REGRESSION. On a hosted load the card must answer without asking:
  // a request here is a browser console error no JS can suppress.
  let s = makeSandbox({ cloudMode: true });
  s._inv();
  await settle();
  ok(s.fetched.length === 0,
     'CLOUD_MODE: no request is issued to /api/guard/inventory');
  ok(s.consoleErrors.length === 0, 'CLOUD_MODE: nothing is written to console.error');
  const hostedText = s.els['guard-inventory-body'].innerHTML;
  ok(/machine your agents run on/.test(hostedText),
     'CLOUD_MODE: the card says the inventory lives on the agents\' own machine');
  ok(/localhost:8900/.test(hostedText),
     'CLOUD_MODE: the card names the dashboard that can show it');
  ok(hostedText.length > 0, 'CLOUD_MODE: the card is not left empty');
  ok(!/Nothing inventoried/.test(hostedText),
     'CLOUD_MODE: the card does not claim nothing was found');
  ok(!/Could not/.test(hostedText),
     'CLOUD_MODE: the card does not claim an error occurred');

  // The local dashboard is where the data actually is: it must still ask.
  s = makeSandbox({ cloudMode: false });
  s._inv();
  await settle();
  ok(s.fetched.length === 1 && String(s.fetched[0]).indexOf('/api/guard/inventory') === 0,
     'local dashboard: the request is still issued');

  // Belt and braces: a deployment that disables the route without setting
  // CLOUD_MODE still gets the honest sentence, not an error.
  s = makeSandbox({
    cloudMode: false,
    response: { ok: false, status: 410, json: function () { return Promise.resolve({}); } }
  });
  s._inv();
  await settle();
  ok(/machine your agents run on/.test(s.els['guard-inventory-body'].innerHTML),
     '410 without CLOUD_MODE: the local-only sentence still renders');
  ok(s.consoleErrors.length === 0, '410 without CLOUD_MODE: still no console error');

  // A genuine failure must stay loud. Silencing every error would hide a
  // broken daemon behind a sentence about cloud.
  s = makeSandbox({
    cloudMode: false,
    response: { ok: false, status: 500, json: function () { return Promise.resolve({}); } }
  });
  s._inv();
  await settle();
  ok(s.consoleErrors.length === 1, 'a 500 IS reported to console.error');
  ok(/Could not load the inventory/.test(s.els['guard-inventory-body'].innerHTML),
     'a 500 tells the reader the inventory could not be loaded');

  // ── The sibling: the Agent Graph card reads /api/local/agent-graph, which
  // is cloud-disabled for the same reason and was about to fail the same way
  // the first time the smoke spec opened the Agents tab.
  console.log('Agent graph card, same cloud-disabled pattern');
  s = makeSandbox({ cloudMode: true });
  s._graph();
  await settle();
  ok(s.fetched.length === 0, 'CLOUD_MODE: no request is issued to /api/local/agent-graph');
  ok(s.consoleErrors.length === 0, 'CLOUD_MODE: the agent graph writes no console error');
  ok(/only available on the dashboard running on your machine/
       .test(s.els['agent-graph-status'].textContent),
     'CLOUD_MODE: the agent graph says where it is available');

  s = makeSandbox({ cloudMode: false });
  s._graph();
  await settle();
  ok(s.fetched.length === 1, 'local dashboard: the agent graph still asks');

  console.log('');
  console.log(passed + ' passed, ' + failed + ' failed');
  if (failed) {
    console.log('FAIL');
    process.exit(1);
  }
  console.log('PASS');
}

main().catch(function (err) {
  console.log('FAIL ' + (err && err.stack || err));
  process.exit(1);
});
