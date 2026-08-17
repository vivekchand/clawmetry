/**
 * Behavioural tests for the global "backend unreachable" detector + overlay
 * in clawmetry/static/js/auth-bootstrap.js.
 *
 * Why this exists: on 2026-08-17 a desktop user's backend died and every tab
 * froze -- Activity showed "Failed to load: TypeError: Load failed", Cost sat
 * on "Loading..." forever, Agents claimed "No agents yet". Each panel handled
 * the failure privately, so nothing said "the backend is gone" and nothing
 * offered a way back. The user's words: there is no refresh button when it
 * gets into this state.
 *
 * The two IIFEs under test are extracted from the shipped source and run
 * against a minimal DOM/window stub -- no jsdom dependency, and it fails if
 * the shipped file stops containing them.
 */
'use strict';

const fs = require('fs');
const path = require('path');
const vm = require('vm');

const SRC = path.join(__dirname, '..', 'clawmetry', 'static', 'js', 'auth-bootstrap.js');

let failures = 0;
const pending = [];
function check(name, fn) {
  const record = function (e) {
    if (e) {
      failures++;
      console.log('  FAIL ' + name + ' -- ' + (e && e.message ? e.message : e));
    } else {
      console.log('  ok   ' + name);
    }
  };
  let out;
  try {
    out = fn();
  } catch (e) {
    record(e);
    return;
  }
  if (out && typeof out.then === 'function') {
    pending.push(out.then(function () { record(null); }, record));
  } else {
    record(null);
  }
}
function assert(cond, msg) { if (!cond) throw new Error(msg || 'assertion failed'); }
function eq(a, b, msg) {
  if (a !== b) throw new Error((msg || 'not equal') + ': ' + JSON.stringify(a) + ' !== ' + JSON.stringify(b));
}

// ── extract the two IIFEs from the shipped file ──────────────────────────────
const source = fs.readFileSync(SRC, 'utf8');

function sliceBlock(startMarker, label) {
  const at = source.indexOf(startMarker);
  assert(at !== -1, 'shipped auth-bootstrap.js no longer contains ' + label +
    ' (looked for: ' + startMarker + ')');
  // Walk forward to the IIFE that follows, then brace-match it.
  const open = source.indexOf('(function(){', at);
  assert(open !== -1, 'no IIFE after ' + label);
  let depth = 0, i = open;
  for (; i < source.length; i++) {
    const c = source[i];
    if (c === '{') depth++;
    else if (c === '}') { depth--; if (depth === 0) break; }
  }
  // i is the IIFE body's closing brace. Take through the invoking "()" --
  // stopping at the first ")" yields a function expression that is never
  // called, and every assertion then silently sees an undefined global.
  const call = source.indexOf('()', i);
  assert(call !== -1 && call - i <= 3,
    'expected "})();" to close ' + label + ', got: ' + JSON.stringify(source.slice(i, i + 8)));
  return source.slice(open, call + 2) + ';';
}

const fetchBlock = sliceBlock('// Inject auth header into all fetch calls', 'the fetch wrapper');
const overlayBlock = sliceBlock('// ── Global "backend unreachable" overlay ──', 'the outage overlay');

// ── a small DOM/window stub ──────────────────────────────────────────────────
function makeElement(tag) {
  return {
    tagName: tag, id: '', style: { cssText: '' }, textContent: '', innerHTML: '',
    type: '', disabled: false, onclick: null, children: [], parentNode: null,
    _attrs: {},
    setAttribute(k, v) { this._attrs[k] = v; },
    appendChild(c) { c.parentNode = this; this.children.push(c); return c; },
    removeChild(c) {
      const i = this.children.indexOf(c);
      if (i >= 0) this.children.splice(i, 1);
      c.parentNode = null;
    },
  };
}

function makeEnv(opts) {
  opts = opts || {};
  const body = makeElement('body');
  const byId = {};
  const listeners = {};
  const timers = [];

  function collect(el, out) {
    out.push(el);
    el.children.forEach(function (c) { collect(c, out); });
    return out;
  }

  const win = {
    localStorage: { getItem() { return null; }, setItem() {}, removeItem() {} },
    fetch: opts.fetch,
    CustomEvent: function (type, init) { this.type = type; this.detail = init && init.detail; },
    addEventListener(type, fn) { (listeners[type] = listeners[type] || []).push(fn); },
    dispatchEvent(ev) { (listeners[ev.type] || []).forEach(function (f) { f(ev); }); return true; },
    setTimeout(fn, ms) { timers.push({ fn: fn, ms: ms }); return timers.length; },
    location: { reload() { win.__reloaded = (win.__reloaded || 0) + 1; } },
    document: {
      body: body,
      documentElement: body,
      getElementById(id) {
        const all = collect(body, []);
        for (const el of all) if (el.id === id) return el;
        return byId[id] || null;
      },
      createElement: makeElement,
    },
    __timers: timers,
    __body: body,
  };
  if (opts.pywebview) win.pywebview = opts.pywebview;
  win.window = win;
  return win;
}

function run(env, blocks) {
  const ctx = vm.createContext(env);
  // The blocks reference bare `window`, `document`, `localStorage`.
  ctx.document = env.document;
  ctx.localStorage = env.localStorage;
  blocks.forEach(function (b) { vm.runInContext(b, ctx); });
  return ctx;
}

function netError() {
  const e = new TypeError('Load failed');
  return e;
}

function overlay(env) { return env.document.getElementById('cm-backend-outage'); }

// ── tests ────────────────────────────────────────────────────────────────────
console.log('backend outage overlay');

check('a single network failure does NOT raise the overlay', function () {
  const env = makeEnv({ fetch: function () { return Promise.reject(netError()); } });
  run(env, [fetchBlock, overlayBlock]);
  return env.fetch('/api/overview').catch(function () {}).then(function () {
    eq(overlay(env), null, 'overlay appeared on the first failure');
  });
});

check('three consecutive network failures raise the overlay', function () {
  const env = makeEnv({ fetch: function () { return Promise.reject(netError()); } });
  run(env, [fetchBlock, overlayBlock]);
  let p = Promise.resolve();
  for (let i = 0; i < 3; i++) {
    p = p.then(function () { return env.fetch('/api/overview').catch(function () {}); });
  }
  return p.then(function () {
    assert(overlay(env), 'overlay never appeared after 3 network failures');
    const text = JSON.stringify(overlay(env).children.map(function (c) {
      return c.innerHTML || c.textContent;
    }));
    assert(/Cannot reach the ClawMetry backend/.test(text),
      'overlay does not name the problem: ' + text);
  });
});

check('an HTTP error status is NOT an outage (the server answered)', function () {
  const env = makeEnv({
    fetch: function () { return Promise.resolve({ status: 500, ok: false }); },
  });
  run(env, [fetchBlock, overlayBlock]);
  let p = Promise.resolve();
  for (let i = 0; i < 5; i++) p = p.then(function () { return env.fetch('/api/overview'); });
  return p.then(function () {
    eq(overlay(env), null, '500s were mistaken for an outage');
  });
});

check('recovery dismisses the overlay', function () {
  let dead = true;
  const env = makeEnv({
    fetch: function () {
      return dead ? Promise.reject(netError()) : Promise.resolve({ status: 200, ok: true });
    },
  });
  run(env, [fetchBlock, overlayBlock]);
  let p = Promise.resolve();
  for (let i = 0; i < 3; i++) {
    p = p.then(function () { return env.fetch('/api/overview').catch(function () {}); });
  }
  return p.then(function () {
    assert(overlay(env), 'overlay never appeared');
    dead = false;
    return env.fetch('/api/overview');
  }).then(function () {
    eq(overlay(env), null, 'overlay survived the backend coming back');
  });
});

check('the overlay always carries an actionable button', function () {
  const env = makeEnv({ fetch: function () { return Promise.reject(netError()); } });
  run(env, [fetchBlock, overlayBlock]);
  env.window.cmShowBackendOutage();
  const el = overlay(env);
  assert(el, 'overlay missing');
  const btn = el.children.filter(function (c) { return c.tagName === 'button'; })[0];
  assert(btn, 'no button in the outage overlay -- this is the whole point');
  assert(typeof btn.onclick === 'function', 'button has no click handler');
  eq(btn.textContent, 'Reload', 'browser fallback should offer Reload');
});

check('in a browser the button reloads the page', function () {
  const env = makeEnv({ fetch: function () { return Promise.reject(netError()); } });
  run(env, [fetchBlock, overlayBlock]);
  env.window.cmShowBackendOutage();
  const btn = overlay(env).children.filter(function (c) { return c.tagName === 'button'; })[0];
  btn.onclick();
  eq(env.__reloaded, 1, 'Reload did not reload');
});

check('in the desktop shell the button restarts the backend via the bridge', function () {
  let restarted = 0;
  const env = makeEnv({
    fetch: function () { return Promise.reject(netError()); },
    pywebview: { api: { restart_backend: function () { restarted++; return { ok: true }; } } },
  });
  run(env, [fetchBlock, overlayBlock]);
  env.window.cmShowBackendOutage();
  const el = overlay(env);
  const btn = el.children.filter(function (c) { return c.tagName === 'button'; })[0];
  eq(btn.textContent, 'Restart backend', 'desktop should offer a real restart');
  btn.onclick();
  eq(restarted, 1, 'bridge restart_backend was not called');
  eq(env.__reloaded, undefined, 'should not fall back to reload when the bridge works');
});

check('a browser outage tells the user what else to try', function () {
  const env = makeEnv({ fetch: function () { return Promise.reject(netError()); } });
  run(env, [fetchBlock, overlayBlock]);
  env.window.cmShowBackendOutage();
  const text = overlay(env).children.map(function (c) {
    return c.textContent || c.innerHTML;
  }).join(' ');
  assert(/quit ClawMetry and open it again/i.test(text),
    'no fallback guidance when the shell cannot self-heal: ' + text);
});

check('non-/api/ requests are not counted toward an outage', function () {
  const env = makeEnv({ fetch: function () { return Promise.reject(netError()); } });
  run(env, [fetchBlock, overlayBlock]);
  let p = Promise.resolve();
  for (let i = 0; i < 5; i++) {
    p = p.then(function () { return env.fetch('/static/js/app.js').catch(function () {}); });
  }
  return p.then(function () {
    eq(overlay(env), null, 'a static-asset failure raised a backend outage');
  });
});

// Several checks are async; drain them before reporting.
Promise.all(pending).then(function () {
  if (failures) {
    console.log('\nFAIL: ' + failures + ' check(s) failed');
    process.exit(1);
  }
  console.log('\nPASS');
});
