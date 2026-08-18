/**
 * Behavioural tests for backend-outage detection and recovery in
 * clawmetry/static/js/auth-bootstrap.js.
 *
 * Why this exists: on 2026-08-17 a desktop user's backend died and every tab
 * froze -- Activity showed "Failed to load: TypeError: Load failed", Cost sat
 * on "Loading..." forever, Agents claimed "No agents yet". Each panel handled
 * the failure privately, so nothing said "the backend is gone" and nothing
 * offered a way back. The user's words: there is no refresh button when it
 * gets into this state.
 *
 * The sharp edge these tests pin down: a pywebview window has no browser
 * chrome, so a naive refresh that calls location.reload() against a DEAD port
 * replaces a frozen-but-readable dashboard with a blank WebKit error page
 * carrying no buttons at all. Recovery must therefore probe first, heal the
 * backend when it is down, and only then reload -- and must refuse to reload
 * when it cannot heal.
 *
 * The IIFEs are extracted from the shipped source and run against a minimal
 * DOM/window stub -- no jsdom dependency, and it fails if the shipped file
 * stops containing them.
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
  try { out = fn(); } catch (e) { record(e); return; }
  if (out && typeof out.then === 'function') pending.push(out.then(function () { record(null); }, record));
  else record(null);
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
  const open = source.indexOf('(function(){', at);
  assert(open !== -1, 'no IIFE after ' + label);
  let depth = 0, i = open;
  for (; i < source.length; i++) {
    const c = source[i];
    if (c === '{') depth++;
    else if (c === '}') { depth--; if (depth === 0) break; }
  }
  // Take through the invoking "()" -- stopping at the first ")" yields a
  // function expression that is never called, and every assertion then
  // silently sees an undefined global.
  const call = source.indexOf('()', i);
  assert(call !== -1 && call - i <= 3,
    'expected "})();" to close ' + label + ', got: ' + JSON.stringify(source.slice(i, i + 8)));
  return source.slice(open, call + 2) + ';';
}

const fetchBlock = sliceBlock('// Inject auth header into all fetch calls', 'the fetch wrapper');
const recoveryBlock = sliceBlock('// ── Backend recovery:', 'the recovery block');

// ── a small DOM/window stub ──────────────────────────────────────────────────
function makeElement(tag) {
  const el = {
    tagName: tag, id: '', style: { cssText: '' }, textContent: '', innerHTML: '',
    type: '', disabled: false, onclick: null, children: [], parentNode: null,
    _attrs: {}, _classes: new Set(),
    setAttribute(k, v) { this._attrs[k] = v; },
    getAttribute(k) { return this._attrs[k]; },
    appendChild(c) { c.parentNode = this; this.children.push(c); return c; },
    removeChild(c) {
      const i = this.children.indexOf(c);
      if (i >= 0) this.children.splice(i, 1);
      c.parentNode = null;
    },
  };
  el.classList = {
    toggle(n, on) { if (on) el._classes.add(n); else el._classes.delete(n); },
    contains(n) { return el._classes.has(n); },
    add(n) { el._classes.add(n); },
    remove(n) { el._classes.delete(n); },
  };
  return el;
}

function makeEnv(opts) {
  opts = opts || {};
  const body = makeElement('body');
  const listeners = {};
  const docListeners = {};

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
    // Real timers: the recovery path genuinely schedules retries.
    setTimeout: setTimeout, clearTimeout: clearTimeout,
    Promise: Promise, Date: Date,
    location: { reload() { win.__reloaded = (win.__reloaded || 0) + 1; } },
    document: {
      body: body,
      documentElement: body,
      getElementById(id) {
        for (const el of collect(body, [])) if (el.id === id) return el;
        return null;
      },
      createElement: makeElement,
      addEventListener(type, fn) { (docListeners[type] = docListeners[type] || []).push(fn); },
      __fire(type, ev) { (docListeners[type] || []).forEach(function (f) { f(ev); }); },
    },
    __body: body,
  };
  if (opts.pywebview) win.pywebview = opts.pywebview;
  win.window = win;
  // The header refresh button lives in the topbar; the recovery code styles
  // it by id, so the stub page carries one.
  if (opts.withButton !== false) {
    const b = makeElement('div');
    b.id = 'cm-reconnect-btn';
    body.appendChild(b);
  }
  return win;
}

function run(env) {
  const ctx = vm.createContext(env);
  ctx.document = env.document;
  ctx.localStorage = env.localStorage;
  vm.runInContext(fetchBlock, ctx);
  vm.runInContext(recoveryBlock, ctx);
  return ctx;
}

function netError() { return new TypeError('Load failed'); }
function overlay(env) { return env.document.getElementById('cm-backend-outage'); }
function reconnectBtn(env) { return env.document.getElementById('cm-reconnect-btn'); }
function overlayButton(env) {
  const el = overlay(env);
  return el && el.children.filter(function (c) { return c.tagName === 'button'; })[0];
}

// ── detection ────────────────────────────────────────────────────────────────
console.log('backend outage detection + recovery');

check('a single network failure does NOT raise the overlay', function () {
  const env = makeEnv({ fetch: function () { return Promise.reject(netError()); } });
  run(env);
  return env.fetch('/api/overview').catch(function () {}).then(function () {
    eq(overlay(env), null, 'overlay appeared on the first failure');
  });
});

check('three consecutive network failures raise the overlay', function () {
  const env = makeEnv({ fetch: function () { return Promise.reject(netError()); } });
  run(env);
  let p = Promise.resolve();
  for (let i = 0; i < 3; i++) p = p.then(function () { return env.fetch('/api/overview').catch(function () {}); });
  return p.then(function () {
    assert(overlay(env), 'overlay never appeared after 3 network failures');
    const text = JSON.stringify(overlay(env).children.map(function (c) { return c.innerHTML || c.textContent; }));
    assert(/Cannot reach the ClawMetry backend/.test(text), 'overlay does not name the problem: ' + text);
  });
});

check('an HTTP error status is NOT an outage (the server answered)', function () {
  const env = makeEnv({ fetch: function () { return Promise.resolve({ status: 500, ok: false }); } });
  run(env);
  let p = Promise.resolve();
  for (let i = 0; i < 5; i++) p = p.then(function () { return env.fetch('/api/overview'); });
  return p.then(function () { eq(overlay(env), null, '500s were mistaken for an outage'); });
});

check('recovery dismisses the overlay', function () {
  let dead = true;
  const env = makeEnv({
    fetch: function () { return dead ? Promise.reject(netError()) : Promise.resolve({ status: 200, ok: true }); },
  });
  run(env);
  let p = Promise.resolve();
  for (let i = 0; i < 3; i++) p = p.then(function () { return env.fetch('/api/overview').catch(function () {}); });
  return p.then(function () {
    assert(overlay(env), 'overlay never appeared');
    dead = false;
    return env.fetch('/api/overview');
  }).then(function () { eq(overlay(env), null, 'overlay survived the backend coming back'); });
});

check('non-/api/ requests are not counted toward an outage', function () {
  const env = makeEnv({ fetch: function () { return Promise.reject(netError()); } });
  run(env);
  let p = Promise.resolve();
  for (let i = 0; i < 5; i++) p = p.then(function () { return env.fetch('/static/js/app.js').catch(function () {}); });
  return p.then(function () { eq(overlay(env), null, 'a static-asset failure raised a backend outage'); });
});

// ── the refresh button ───────────────────────────────────────────────────────

check('cmReconnect is exposed for the header button to call', function () {
  const env = makeEnv({ fetch: function () { return Promise.resolve({ ok: true }); } });
  run(env);
  eq(typeof env.window.cmReconnect, 'function', 'window.cmReconnect missing');
});

check('a healthy backend means the button is a plain refresh', function () {
  const env = makeEnv({ fetch: function () { return Promise.resolve({ status: 200, ok: true }); } });
  run(env);
  return env.window.cmReconnect().then(function () {
    eq(env.__reloaded, 1, 'a healthy backend should just reload');
    eq(overlay(env), null, 'no outage overlay should appear when the backend is fine');
  });
});

check('a dead backend WITHOUT a bridge must NOT reload into a blank page', function () {
  const env = makeEnv({ fetch: function () { return Promise.reject(netError()); } });
  run(env);
  return env.window.cmReconnect().then(function () {
    eq(env.__reloaded, undefined, 'reloaded against a dead origin -- this blanks the window');
    assert(overlay(env), 'refused to reload but told the user nothing');
    const text = overlay(env).children.map(function (c) { return c.textContent || c.innerHTML; }).join(' ');
    assert(/quit ClawMetry and open it again/i.test(text), 'no actionable guidance: ' + text);
  });
});

check('a dead backend WITH a bridge restarts it, then reloads', function () {
  let alive = false, restarted = 0;
  const env = makeEnv({
    fetch: function () { return alive ? Promise.resolve({ ok: true }) : Promise.reject(netError()); },
    pywebview: { api: { restart_backend: function () { restarted++; alive = true; return { ok: true }; } } },
  });
  run(env);
  return env.window.cmReconnect().then(function () {
    eq(restarted, 1, 'did not ask the shell to restart the backend');
    eq(env.__reloaded, 1, 'did not reload after the backend came back');
  });
});

check('a backend that never comes back does not reload, and says so', function () {
  const env = makeEnv({
    fetch: function () { return Promise.reject(netError()); },
    pywebview: { api: { restart_backend: function () { return { ok: true }; } } },
  });
  env.__cmRestartBudgetMs = 60;
  run(env);
  return env.window.cmReconnect().then(function () {
    eq(env.__reloaded, undefined, 'reloaded even though the backend never answered');
    const text = overlay(env).children.map(function (c) { return c.textContent || c.innerHTML; }).join(' ');
    assert(/did not come back/i.test(text), 'did not report the failed restart: ' + text);
  });
});

check('the health probe does not inflate the outage counter', function () {
  const env = makeEnv({ fetch: function () { return Promise.reject(netError()); } });
  run(env);
  // Three probes would trip the threshold if they went through the wrapper.
  return env.window.cmBackendProbe(20)
    .then(function () { return env.window.cmBackendProbe(20); })
    .then(function () { return env.window.cmBackendProbe(20); })
    .then(function () { eq(env.window.cmBackendFailures(), 0, 'probes counted as app traffic'); });
});

check('the header button shows a busy state while working', function () {
  let resolveFetch;
  const env = makeEnv({ fetch: function () { return new Promise(function (r) { resolveFetch = r; }); } });
  run(env);
  const p = env.window.cmReconnect();
  assert(reconnectBtn(env).classList.contains('cm-spinning'), 'button never entered a busy state');
  resolveFetch({ ok: true });
  return p;
});

check('the header button goes amber when the backend is known down', function () {
  const env = makeEnv({ fetch: function () { return Promise.reject(netError()); } });
  run(env);
  eq(reconnectBtn(env).classList.contains('cm-attention'), false, 'button started in the alarm state');
  env.window.cmShowBackendOutage();
  eq(reconnectBtn(env).classList.contains('cm-attention'), true, 'button did not flag the outage');
  env.window.cmHideBackendOutage();
  eq(reconnectBtn(env).classList.contains('cm-attention'), false, 'button stayed amber after recovery');
});

check('the overlay button routes through the same recovery path', function () {
  const env = makeEnv({ fetch: function () { return Promise.resolve({ ok: true }); } });
  run(env);
  env.window.cmShowBackendOutage();
  const btn = overlayButton(env);
  assert(btn && typeof btn.onclick === 'function', 'overlay has no actionable button');
  btn.onclick();
  return new Promise(function (r) { setTimeout(r, 30); }).then(function () {
    eq(env.__reloaded, 1, 'overlay button did not recover');
  });
});

// ── Cmd/Ctrl+R ───────────────────────────────────────────────────────────────

check('Cmd-R is handled in the shell, where the native shortcut is swallowed', function () {
  let alive = true;
  const env = makeEnv({
    fetch: function () { return alive ? Promise.resolve({ ok: true }) : Promise.reject(netError()); },
    pywebview: { api: { restart_backend: function () { return { ok: true }; } } },
  });
  run(env);
  let prevented = 0;
  env.document.__fire('keydown', { metaKey: true, key: 'r', preventDefault: function () { prevented++; } });
  eq(prevented, 1, 'Cmd-R was not intercepted inside the desktop shell');
  return new Promise(function (r) { setTimeout(r, 30); }).then(function () {
    eq(env.__reloaded, 1, 'Cmd-R did not refresh');
  });
});

check('Cmd-R is left alone in a browser, where it already works', function () {
  const env = makeEnv({ fetch: function () { return Promise.resolve({ ok: true }); } });
  run(env);
  let prevented = 0;
  env.document.__fire('keydown', { metaKey: true, key: 'r', preventDefault: function () { prevented++; } });
  eq(prevented, 0, 'hijacked the browser native reload');
});

check('an unrelated keypress is ignored', function () {
  const env = makeEnv({
    fetch: function () { return Promise.resolve({ ok: true }); },
    pywebview: { api: { restart_backend: function () { return { ok: true }; } } },
  });
  run(env);
  let prevented = 0;
  env.document.__fire('keydown', { metaKey: true, key: 'k', preventDefault: function () { prevented++; } });
  eq(prevented, 0, 'swallowed Cmd-K');
});

Promise.all(pending).then(function () {
  if (failures) {
    console.log('\nFAIL: ' + failures + ' check(s) failed');
    process.exit(1);
  }
  console.log('\nPASS');
});
