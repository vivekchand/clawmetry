const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const source = fs.readFileSync(path.join(__dirname, '../clawmetry/static/js/first-run.js'), 'utf8');
const pending = { available: true, initialized: false, has_data: false, phase: 'discovering' };
const ready = { available: true, initialized: true, has_data: true };
const empty = { available: true, initialized: true, has_data: false };
async function drain() { for (let n = 0; n < 40; n++) await Promise.resolve(); }

function harness(responses, cloud = false) {
  const elements = new Map(), timers = new Map(), listeners = {}, storage = new Map();
  let count = 0, snaps = 0, next = 1, refreshes = 0;
  function element(id) {
    if (!elements.has(id)) elements.set(id, {
      id, hidden: true, dataset: {}, textContent: '', inert: false, isConnected: true,
      classList: { add() {}, remove() {} },
      addEventListener(event, callback) { this[event] = callback; },
      querySelector(selector) { return element(id + selector); },
      focus() { document.activeElement = this; }
    });
    return elements.get(id);
  }
  const document = {
    hidden: false, body: element('body'), activeElement: element('before'),
    getElementById: element,
    querySelector: () => ({ id: 'page-transcripts' }),
    addEventListener: (event, fn) => { listeners[event] = fn; },
    removeEventListener: (event) => { delete listeners[event]; }
  };
  function response() {
    const data = responses.length > 1 ? responses.shift() : responses[0];
    if (data instanceof Error) return Promise.reject(data);
    return Promise.resolve(data);
  }
  const window = {
    CLOUD_MODE: cloud, location: { pathname: cloud ? '/node/test' : '/' },
    switchTab: () => { refreshes++; },
    __cmSnap: async () => { snaps++; return await response(); }
  };
  const context = {
    window, document, Promise, Date, AbortController, console,
    localStorage: { getItem: key => storage.get(key), setItem: (key, value) => storage.set(key, value) },
    setTimeout: (fn, ms) => { const id = next++; timers.set(id, { fn, ms }); return id; },
    clearTimeout: id => timers.delete(id),
    fetch: async url => { assert.equal(url, '/api/onboarding/readiness'); count++; const data = await response(); return { ok: true, json: async () => data }; }
  };
  vm.runInNewContext(source, context);
  return {
    window, document, element, timers, listeners, storage,
    count: () => count, snaps: () => snaps, refreshes: () => refreshes,
    start: async (state = { required: false, source: 'gate' }) => { window.cmFirstRun.start(state); await drain(); },
    fire: async ms => {
      const entry = [...timers].find(([, timer]) => timer.ms === ms);
      assert.ok(entry, 'expected timer ' + ms);
      timers.delete(entry[0]); entry[1].fn(); await drain();
    }
  };
}

(async () => {
  let h = harness([{ ...pending }, { ...pending, phase: 'runtime_history', has_data: true }, ready]);
  await h.start();
  assert.equal(h.element('first-run').hidden, false);
  assert.equal(h.element('zoom-wrapper').inert, true);
  await h.fire(5000);
  assert.equal(h.window.cmFirstRun.active, true, 'first arriving rows must not finish setup');
  assert.equal(h.element('first-run-discover').dataset.state, 'done');
  await h.fire(5000);
  assert.equal(h.window.cmFirstRun.active, false);
  assert.equal(h.element('zoom-wrapper').inert, false);
  assert.equal(h.refreshes(), 1, 'refresh the landing screen after ingest');
  assert.equal([...h.timers.values()].filter(t => t.ms === 5000).length, 0);

  h = harness([ready]); await h.start();
  assert.equal(h.element('first-run').hidden, true, 'existing install opens immediately');
  assert.equal(h.count(), 1);
  assert.equal(h.refreshes(), 0);

  h = harness([{ ...pending }, ready]);
  let renderDone;
  h.window.loadTranscripts = () => new Promise(resolve => { renderDone = resolve; });
  await h.start(); await h.fire(5000);
  assert.equal(h.window.cmFirstRun.active, true, 'keep covering a stale empty landing list');
  renderDone(); await drain();
  assert.equal(h.window.cmFirstRun.active, false);
  assert.equal(h.refreshes(), 0, 'landing list must not be fetched a second time');

  h = harness([{ ...pending, started_at: 2 }]);
  h.storage.set('cm-first-run-opened:/:1', '1');
  await h.start();
  assert.equal(h.window.cmFirstRun.active, true, 'a reinstall gets its own preparation screen');
  h = harness([{ ...pending, started_at: 2 }]);
  h.storage.set('cm-first-run-opened:/:2', '1');
  await h.start();
  assert.equal(h.window.cmFirstRun.active, false, 'honor explicit dismissal for this installation');

  h = harness([empty]); await h.start();
  assert.equal(h.element('first-run').dataset.settled, 'empty');
  assert.match(h.element('first-run-title').textContent, /first activity/);
  assert.equal(h.element('first-run-retry').hidden, false);
  assert.equal([...h.timers.values()].filter(t => t.ms === 5000).length, 0);
  h.element('first-run-continue').click();
  assert.equal(h.window.cmFirstRun.active, false);

  h = harness([{ ...pending }]); await h.start(); await h.fire(180000);
  assert.equal(h.element('first-run').dataset.settled, 'delayed', 'bounded three-minute wait');
  assert.equal(h.element('first-run-retry').hidden, false);
  h.element('first-run-retry').click(); await drain();
  assert.equal(h.element('first-run').dataset.settled, undefined);
  assert.equal(h.count(), 2, 'retry really checks again');

  h = harness([new Error('offline')]); await h.start(); await h.fire(5000); await h.fire(5000);
  assert.equal(h.window.cmFirstRun.active, true, 'transient errors keep retrying during the first collection');
  await h.fire(180000);
  assert.equal(h.element('first-run').dataset.settled, 'delayed');
  assert.doesNotMatch(h.element('first-run-status').textContent, /offline|undefined|500/);

  h = harness([{}]); await h.start();
  assert.equal(h.window.cmFirstRun.active, true, 'unknown is never ready or empty');

  h = harness([{ ...pending }]); await h.start(); h.document.hidden = true; await h.fire(5000);
  assert.equal(h.count(), 1, 'no polling in a hidden tab');
  h.document.hidden = false; h.listeners.visibilitychange(); h.listeners.visibilitychange(); await drain();
  assert.equal(h.count(), 2, 'visibility events deduplicate in-flight probes');
  h.element('first-run-continue').click();
  assert.equal(h.listeners.visibilitychange, undefined);

  for (const state of [{ required: true }, { source: 'ci' }, { source: 'env_skip' }]) {
    h = harness([pending]); await h.start(state);
    assert.equal(h.count(), 0, 'respect onboarding / automation gates');
    assert.equal(h.window.cmFirstRun.checking, false);
  }

  h = harness([{ firstRun: { readiness: { ...pending } } }, { firstRun: { readiness: ready } }], true);
  await h.start(); await h.fire(8000);
  assert.equal(h.count(), 0, 'cloud must not call a local readiness endpoint');
  assert.equal(h.snaps(), 2);
  assert.equal(h.window.cmFirstRun.active, false);
  h = harness([{ sessionCount: 2 }], true); await h.start();
  assert.equal(h.element('first-run').hidden, true, 'older populated snapshots bypass preparation');
  for (const gate of ['_cmKeyNeeded', 'CM_SUPPORT_VIEW']) {
    h = harness([null], true); h.window[gate] = true;
    h.listeners.DOMContentLoaded(); await drain();
    assert.equal(h.snaps(), 0, 'do not poll snapshots before cloud data can be unlocked');
    assert.equal(h.window.cmFirstRun.active, false, 'never cover the secret-key prompt or support view');
    assert.equal(h.window.cmFirstRun.checking, false);
  }
  console.log('PASS: first-run readiness, polling, recovery, cloud and empty states');
})().catch(error => { console.error(error); process.exitCode = 1; });
