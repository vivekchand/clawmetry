/**
 * Behavioural tests for the header trial pill + upgrade modal
 * (clawmetry/static/js/trial-pill.js).
 *
 * Why this exists: this component is the only thing standing between a
 * trialing customer and silent expiry, and every failure mode is SILENT --
 * a pill that renders on a paying account, a countdown off by a day, a
 * checkout button that opens a tab to nowhere. None of those throw, so
 * none of them show up in a smoke test.
 *
 * The two that would cost real money:
 *   * showing a countdown to somebody who already paid (reads as a billing
 *     bug, and the "Upgrade" button invites a double purchase), and
 *   * navigating to a URL the server did not hand us when checkout fails.
 *
 * The IIFE is extracted from the shipped source and run against a minimal
 * DOM/window stub -- no jsdom dependency, and the extraction fails loudly if
 * the shipped file is restructured.
 */
'use strict';

const fs = require('fs');
const path = require('path');
const vm = require('vm');

const SRC = path.join(__dirname, '..', 'clawmetry', 'static', 'js', 'trial-pill.js');
const source = fs.readFileSync(SRC, 'utf8');

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
function includes(hay, needle, msg) {
  if (String(hay).indexOf(needle) === -1) {
    throw new Error((msg || 'missing substring') + ': ' + JSON.stringify(needle)
      + ' not in ' + JSON.stringify(String(hay).slice(0, 400)));
  }
}

// ── a very small DOM ────────────────────────────────────────────────────────
function makeEl(tag) {
  const el = {
    tagName: String(tag || 'div').toUpperCase(),
    id: '',
    className: '',
    style: {},
    dataset: {},
    children: [],
    parentNode: null,
    _html: '',
    _attrs: {},
    _listeners: {},
    _text: '',
    get innerHTML() { return this._html; },
    set innerHTML(v) { this._html = String(v); this.children = parseChildren(this._html); },
    get textContent() { return this._text; },
    set textContent(v) { this._text = String(v); },
    setAttribute: function (k, v) { this._attrs[k] = String(v); },
    getAttribute: function (k) { return Object.prototype.hasOwnProperty.call(this._attrs, k) ? this._attrs[k] : null; },
    removeAttribute: function (k) { delete this._attrs[k]; },
    appendChild: function (c) { c.parentNode = this; this.children.push(c); return c; },
    remove: function () {
      if (!this.parentNode) return;
      const i = this.parentNode.children.indexOf(this);
      if (i >= 0) this.parentNode.children.splice(i, 1);
      this.parentNode = null;
    },
    addEventListener: function (t, fn) { (this._listeners[t] = this._listeners[t] || []).push(fn); },
    removeEventListener: function () {},
    focus: function () {},
    click: function (ev) { (this._listeners.click || []).forEach(function (f) { f(ev || {}); }); },
    querySelector: function (sel) { return this.querySelectorAll(sel)[0] || null; },
    querySelectorAll: function (sel) { return queryIn(this, sel); },
  };
  return el;
}

// The component builds its DOM by assigning innerHTML, so the stub needs to
// answer querySelector against that markup.
//
// This parses NESTING, not just a flat tag list. An earlier flat version made
// ".cm-up-seg button" match every button on the card -- so the interval
// handler got bound to the tier buttons and the CTA, and a click on "Continue
// to Stripe" silently flipped the billing interval. The stub reported a green
// suite while doing it. Ancestry has to be real for a descendant selector to
// mean anything.
const VOID_TAGS = { br: 1, hr: 1, img: 1, input: 1, link: 1, meta: 1 };

function parseChildren(html) {
  const root = { children: [] };
  const stack = [root];
  const re = /<(\/?)(\w+)([^>]*?)(\/?)>/g;
  let m;
  while ((m = re.exec(html)) !== null) {
    const closing = m[1] === '/';
    const tag = m[2].toLowerCase();
    const attrs = m[3] || '';
    const selfClosed = m[4] === '/' || VOID_TAGS[tag];
    if (closing) {
      // Never pop past the root on unbalanced markup.
      if (stack.length > 1) stack.pop();
      continue;
    }
    const el = makeEl(tag);
    const idM = /\bid="([^"]*)"/.exec(attrs);
    if (idM) el.id = idM[1];
    const clM = /\bclass="([^"]*)"/.exec(attrs);
    if (clM) el.className = clM[1];
    ['data-tier', 'data-interval', 'aria-pressed'].forEach(function (a) {
      const hit = new RegExp('\\b' + a + '="([^"]*)"').exec(attrs);
      if (hit) el._attrs[a] = hit[1];
    });
    const parent = stack[stack.length - 1];
    el.parentNode = parent === root ? null : parent;
    parent.children.push(el);
    if (!selfClosed) stack.push(el);
  }
  return root.children;
}

// True when `el` sits anywhere under an element matching `token`.
function hasAncestorMatching(el, token, root) {
  let cur = el.parentNode;
  while (cur && cur !== root) {
    if (matchSimple(cur, token)) return true;
    cur = cur.parentNode;
  }
  // The element the innerHTML was assigned to is the implicit root of the
  // parsed fragment; treat a token matching it as satisfied.
  return root ? matchSimple(root, token) : false;
}

function matchSimple(el, s) {
  if (!el) return false;
  if (s.charAt(0) === '#') return el.id === s.slice(1);
  if (s.charAt(0) === '.') return (' ' + el.className + ' ').indexOf(' ' + s.slice(1) + ' ') !== -1;
  const attr = /\[([\w-]+)="?([^\]"]*)"?\]/.exec(s);
  if (attr) return el.getAttribute && el.getAttribute(attr[1]) === attr[2];
  if (/^[a-z]+$/.test(s)) return el.tagName === s.toUpperCase();
  return false;
}

function walk(root, acc) {
  (root.children || []).forEach(function (c) { acc.push(c); walk(c, acc); });
  return acc;
}

function queryIn(root, sel) {
  const all = walk(root, []);
  return all.filter(function (el) {
    return sel.split(',').some(function (part) {
      const tokens = part.trim().split(/\s+/);
      const last = tokens[tokens.length - 1];
      if (!matchSimple(el, last)) return false;
      // Every preceding token must be satisfied by some ancestor. Without
      // this, ".cm-up-seg button" matches every button on the card.
      for (let i = tokens.length - 2; i >= 0; i--) {
        if (!hasAncestorMatching(el, tokens[i], root)) return false;
      }
      return true;
    });
  });
}

function opened(env, url) {
  // Exact membership in the list of URLs the stub was asked to open.
  // Deliberately NOT indexOf(url): CodeQL reads `indexOf(<url literal>)` as
  // incomplete URL-substring sanitization, and an exact comparison is a
  // stricter assertion anyway.
  return env.__opened.some(function (u) { return u === url; });
}

function makeEnv(opts) {
  opts = opts || {};
  const head = makeEl('head');
  const body = makeEl('body');
  const slot = makeEl('div');
  slot.id = 'cm-trial-pill-slot';
  const nav = makeEl('div');
  nav.className = 'nav';
  body.appendChild(nav);
  body.appendChild(slot);

  const document = {
    readyState: 'complete',
    head: head,
    body: body,
    _listeners: {},
    createElement: makeEl,
    addEventListener: function (t, fn) { (this._listeners[t] = this._listeners[t] || []).push(fn); },
    removeEventListener: function () {},
    getElementById: function (id) {
      const all = walk(body, []).concat(walk(head, []));
      for (let i = 0; i < all.length; i++) if (all[i].id === id) return all[i];
      return null;
    },
    querySelector: function (sel) {
      const all = walk(body, []);
      for (let i = 0; i < all.length; i++) {
        if (sel.charAt(0) === '.' && (' ' + all[i].className + ' ').indexOf(' ' + sel.slice(1) + ' ') !== -1) return all[i];
        if (sel.charAt(0) === '#' && all[i].id === sel.slice(1)) return all[i];
      }
      return null;
    },
  };

  const env = {
    document: document,
    __opened: [],
    __fetches: [],
    __timers: [],
    console: console,
    JSON: JSON,
    Date: Date,
    Promise: Promise,
    Array: Array,
    Object: Object,
    String: String,
    Math: Math,
    encodeURIComponent: encodeURIComponent,
  };
  env.window = env;
  env.CLOUD_MODE = opts.cloud || false;
  // Hosted cloud renders the pill only when the cloud opts in (it already
  // injects its own trial banner). Default the flag ON for cloud tests that
  // assert rendering; `cloudOptIn:false` exercises the default-off gate.
  if (opts.cloud && opts.cloudOptIn !== false) env.CM_TRIAL_PILL = true;
  env.CM_PLANS = opts.plans === null ? undefined : (opts.plans || {
    prices: { starter: { month: 9, year: 90, was: 190 }, pro: { month: 19, year: 190, was: 390 } },
    blurb: { starter: 'Starter blurb.', pro: 'Pro blurb.' },
    features: { starter: [], pro: [] },
    deviceValue: 149,
  });
  env.localStorage = { getItem: function () { return opts.token || ''; }, setItem: function () {} };
  env.addEventListener = function (t, fn) { (document._listeners[t] = document._listeners[t] || []).push(fn); };
  env.removeEventListener = function () {};
  env.setTimeout = function (fn, ms) { env.__timers.push({ fn: fn, ms: ms }); return env.__timers.length; };
  env.clearTimeout = function () {};
  env.open = function (url) {
    env.__opened.push(url);
    const tab = { location: url, closed: false, close: function () { this.closed = true; } };
    Object.defineProperty(tab, 'location', {
      get: function () { return this._loc; },
      set: function (v) { this._loc = v; env.__opened.push(v); },
    });
    tab._loc = url;
    return tab;
  };
  env.CustomEvent = function (type, init) { this.type = type; this.detail = init && init.detail; };
  env.dispatchEvent = function () {};
  env.fetch = function (url, init) {
    env.__fetches.push({ url: url, init: init });
    const r = opts.fetch ? opts.fetch(url, init) : null;
    if (r && typeof r.then === 'function') return r;
    return Promise.resolve({
      ok: true,
      json: function () { return Promise.resolve(r || {}); },
      catch: function () { return this; },
    });
  };
  env.location = { href: '', reload: function () { env.__reloaded = true; } };
  return env;
}

function run(env) {
  vm.createContext(env);
  vm.runInContext(source, env, { filename: 'trial-pill.js' });
  return env;
}

// Drain the microtask queue so a fetch().then() chain has settled.
function flush() {
  return new Promise(function (res) { setTimeout(res, 0); });
}

function slotHtml(env) {
  const s = env.document.getElementById('cm-trial-pill-slot');
  return s ? s.innerHTML : '';
}

// ── the pill ────────────────────────────────────────────────────────────────

check('renders "N days remaining" for a self-hosted trial', function () {
  const env = makeEnv({ fetch: function () { return { tier: 'trial', days_until_expiry: 2, expired: false }; } });
  run(env);
  return flush().then(function () {
    includes(slotHtml(env), '2 days remaining', 'pill did not render the countdown');
    includes(slotHtml(env), 'Upgrade', 'no upgrade button');
    includes(slotHtml(env), 'cm-urgent', '2 days left should read as urgent');
  });
});

check('singularises one day', function () {
  const env = makeEnv({ fetch: function () { return { tier: 'trial', days_until_expiry: 1 }; } });
  run(env);
  return flush().then(function () {
    includes(slotHtml(env), '1 day remaining');
    assert(slotHtml(env).indexOf('1 days') === -1, 'rendered "1 days"');
  });
});

check('a long trial is calm, not urgent', function () {
  const env = makeEnv({ fetch: function () { return { tier: 'trial', days_until_expiry: 6 }; } });
  run(env);
  return flush().then(function () {
    includes(slotHtml(env), '6 days remaining');
    includes(slotHtml(env), 'cm-calm', 'six days out should not be styled as urgent');
  });
});

check('day zero says "ends today", never "0 days"', function () {
  const env = makeEnv({ fetch: function () { return { tier: 'trial', days_until_expiry: 0 }; } });
  run(env);
  return flush().then(function () {
    includes(slotHtml(env), 'ends today');
    assert(slotHtml(env).indexOf('0 days') === -1, 'rendered a zero countdown');
  });
});

check('an expired trial says so and still offers Upgrade', function () {
  const env = makeEnv({ fetch: function () { return { tier: 'trial', expired: true, days_until_expiry: -3 }; } });
  run(env);
  return flush().then(function () {
    includes(slotHtml(env), 'Trial ended');
    includes(slotHtml(env), 'Upgrade');
    includes(slotHtml(env), 'cm-over');
    assert(slotHtml(env).indexOf('-3') === -1, 'leaked a negative countdown');
  });
});

// The expensive mistake: a countdown shown to somebody who already paid.
['starter', 'pro', 'cloud_pro', 'cloud_starter', 'enterprise'].forEach(function (tier) {
  check('stays hidden on a paid install (' + tier + ')', function () {
    const env = makeEnv({ fetch: function () { return { tier: tier, expired: false, days_until_expiry: 300 }; } });
    run(env);
    return flush().then(function () {
      eq(slotHtml(env), '', 'rendered a trial pill for a paying customer');
    });
  });
});

check('no expiry known -> no invented number', function () {
  const env = makeEnv({ fetch: function () { return { tier: 'trial', days_until_expiry: null }; } });
  run(env);
  return flush().then(function () {
    includes(slotHtml(env), 'Pro trial');
    assert(!/\d+\s+days?\s+remaining/.test(slotHtml(env)), 'invented a countdown with no expiry');
  });
});

check('cloud account shape drives the same pill', function () {
  const env = makeEnv({
    cloud: true,
    token: 'cm_test',
    fetch: function () { return { plan: 'trial', trial_active: true, trial_days_left: 2 }; },
  });
  run(env);
  return flush().then(function () {
    includes(slotHtml(env), '2 days remaining', 'cloud trial did not render');
  });
});

check('cloud reads the account the page already fetched, no second request', function () {
  const env = makeEnv({ cloud: true, token: 'cm_test' });
  env._account = { plan: 'trial', trial_active: true, trial_days_left: 4 };
  run(env);
  return flush().then(function () {
    includes(slotHtml(env), '4 days remaining');
    const acct = env.__fetches.filter(function (f) { return String(f.url).indexOf('/api/cloud/account') === 0; });
    eq(acct.length, 0, 'refetched an account already in window._account');
  });
});

check('a paid cloud plan gets no pill', function () {
  const env = makeEnv({ cloud: true, token: 'cm_test' });
  env._account = { plan: 'cloud_pro', trial_active: false };
  run(env);
  return flush().then(function () { eq(slotHtml(env), ''); });
});

check('rides the app.js broadcast instead of its own poll', function () {
  const env = makeEnv({ fetch: function () { return null; } });
  run(env);
  return flush().then(function () {
    const listeners = env.document._listeners['cm:trial-state'] || [];
    assert(listeners.length > 0, 'never subscribed to cm:trial-state');
    listeners.forEach(function (fn) {
      fn({ detail: { tier: 'trial', days_until_expiry: 5, expired: false } });
    });
    includes(slotHtml(env), '5 days remaining', 'ignored the broadcast snapshot');
  });
});

// ── the modal ───────────────────────────────────────────────────────────────

function openModal(env) {
  env.cmOpenUpgradeModal('test');
  return env.document.getElementById('cm-upgrade-modal');
}

check('modal offers both tiers on both intervals, at CM_PLANS prices', function () {
  const env = makeEnv({ fetch: function () { return { tier: 'trial', days_until_expiry: 2 }; } });
  run(env);
  return flush().then(function () {
    const m = openModal(env);
    assert(m, 'modal never mounted');
    const h = m.innerHTML;
    includes(h, 'Starter'); includes(h, 'Pro');
    includes(h, 'Monthly'); includes(h, 'Annual');
    // Annual is preselected, so the annual figures are what render first.
    includes(h, '$90', 'starter annual price missing');
    includes(h, '$190', 'pro annual price missing');
  });
});

check('modal invents no prices when CM_PLANS is absent', function () {
  const env = makeEnv({ plans: null, fetch: function () { return { tier: 'trial', days_until_expiry: 2 }; } });
  env.CM_PLANS = undefined;
  run(env);
  return flush().then(function () {
    const m = openModal(env);
    const h = m.innerHTML;
    includes(h, 'Starter', 'tiers should still render');
    assert(!/\$\d/.test(h), 'printed a price with no ladder loaded: ' + h.slice(0, 300));
  });
});

check('switching to Monthly repaints monthly prices', function () {
  const env = makeEnv({ fetch: function () { return { tier: 'trial', days_until_expiry: 2 }; } });
  run(env);
  return flush().then(function () {
    const m = openModal(env);
    const monthly = m.querySelectorAll('[data-interval="month"]')[0];
    assert(monthly, 'no monthly button');
    monthly.click();
    const h = m.querySelector('#cm-up-tiers').innerHTML;
    // Exact figures, anchored. "$9" is a substring of "$90" and "$19" of
    // "$190", so a loose contains() passes on the ANNUAL render and proves
    // nothing about the switch.
    includes(h, '$9<', 'monthly starter price missing after switch');
    includes(h, '$19<', 'monthly pro price missing after switch');
    assert(h.indexOf('$90<') === -1 && h.indexOf('$190<') === -1,
      'annual prices survived the switch to monthly: ' + h.slice(0, 300));
    includes(h, 'node/mo', 'per-unit suffix did not switch to monthly');
  });
});

check('checkout POSTs the chosen tier + interval and opens the returned URL', function () {
  let body = null;
  const env = makeEnv({
    fetch: function (url, init) {
      if (String(url).indexOf('/api/trial/checkout') === 0) {
        body = JSON.parse(init.body);
        return { ok: true, url: 'https://checkout.stripe.com/c/pay/cs_test_123' };
      }
      return { tier: 'trial', days_until_expiry: 2 };
    },
  });
  run(env);
  return flush().then(function () {
    const m = openModal(env);
    m.querySelectorAll('[data-tier="pro"]')[0].click();
    m.querySelectorAll('[data-interval="month"]')[0].click();
    m.querySelector('.cm-up-cta').click();
    return flush().then(function () {
      assert(body, 'never called /api/trial/checkout');
      eq(body.tier, 'pro', 'wrong tier sent');
      eq(body.plan, 'monthly', 'wrong interval sent');
      assert(opened(env, 'https://checkout.stripe.com/c/pay/cs_test_123'),
        'never navigated to the Stripe URL: ' + JSON.stringify(env.__opened));
    });
  });
});

check('cloud checkout goes to the cloud billing endpoint with the account key', function () {
  let hit = null;
  const env = makeEnv({
    cloud: true,
    token: 'cm_live_abc',
    fetch: function (url, init) {
      if (String(url).indexOf('/api/billing/checkout') === 0) {
        hit = JSON.parse(init.body);
        return { url: 'https://checkout.stripe.com/c/pay/cs_cloud' };
      }
      return { plan: 'trial', trial_active: true, trial_days_left: 2 };
    },
  });
  run(env);
  return flush().then(function () {
    const m = openModal(env);
    m.querySelector('.cm-up-cta').click();
    return flush().then(function () {
      assert(hit, 'cloud never called /api/billing/checkout');
      eq(hit.cm_key, 'cm_live_abc', 'account key not forwarded');
      eq(hit.plan, 'yearly');
    });
  });
});

// The other expensive mistake: sending somebody to a URL we did not get from
// the server. A blank tab pointed at about:blank is recoverable; a tab sent
// to a stale or guessed checkout link is not.
check('a checkout failure surfaces an error and navigates NOWHERE', function () {
  const env = makeEnv({
    fetch: function (url) {
      if (String(url).indexOf('/api/trial/checkout') === 0) return { ok: false, error: 'Billing not configured' };
      return { tier: 'trial', days_until_expiry: 2 };
    },
  });
  run(env);
  return flush().then(function () {
    const m = openModal(env);
    m.querySelector('.cm-up-cta').click();
    return flush().then(function () {
      const real = env.__opened.filter(function (u) { return u && u !== 'about:blank'; });
      eq(real.length, 0, 'navigated somewhere on a failed checkout: ' + JSON.stringify(real));
      includes(m.querySelector('.cm-up-status').textContent, 'Billing not configured',
        'did not show the server error');
    });
  });
});

check('a network failure is reported, not swallowed', function () {
  const env = makeEnv({
    fetch: function (url) {
      if (String(url).indexOf('/api/trial/checkout') === 0) return Promise.reject(new Error('offline'));
      return { tier: 'trial', days_until_expiry: 2 };
    },
  });
  run(env);
  return flush().then(function () {
    const m = openModal(env);
    m.querySelector('.cm-up-cta').click();
    return flush().then(function () {
      const real = env.__opened.filter(function (u) { return u && u !== 'about:blank'; });
      eq(real.length, 0, 'navigated on a network failure');
      const txt = m.querySelector('.cm-up-status').textContent;
      assert(txt && txt.length > 0, 'silent failure -- status line stayed empty');
    });
  });
});

check('the payment tab is opened synchronously (popup blockers)', function () {
  const env = makeEnv({
    fetch: function (url) {
      if (String(url).indexOf('/api/trial/checkout') === 0) {
        // Still pending when we assert below.
        return new Promise(function () {});
      }
      return { tier: 'trial', days_until_expiry: 2 };
    },
  });
  run(env);
  return flush().then(function () {
    const m = openModal(env);
    m.querySelector('.cm-up-cta').click();
    // No flush: the tab must already exist before the fetch settles.
    eq(env.__opened[0], 'about:blank',
      'tab was not opened inside the click handler -- popup blockers will kill it');
  });
});

// The desktop shell (pywebview) patches window.open to hand external https
// URLs to the system browser. That shim only recognises the FINAL url, so a
// pre-opened "about:blank" tab falls through to the native webview and the
// buyer gets a blank chromeless window instead of Stripe. Inside the shell
// there is no popup blocker to defeat, so the pre-open must be skipped.
check('desktop shell: no about:blank pre-open, final URL goes to the bridge', function () {
  const env = makeEnv({
    fetch: function (url) {
      if (String(url).indexOf('/api/trial/checkout') === 0) {
        return { ok: true, url: 'https://checkout.stripe.com/c/pay/cs_desktop' };
      }
      return { tier: 'trial', days_until_expiry: 2 };
    },
  });
  env.pywebview = { api: { open_external: function () { return true; } } };
  run(env);
  return flush().then(function () {
    const m = openModal(env);
    m.querySelector('.cm-up-cta').click();
    return flush().then(function () {
      assert(env.__opened.indexOf('about:blank') === -1,
        'pre-opened a blank tab inside the desktop shell: ' + JSON.stringify(env.__opened));
      assert(opened(env, 'https://checkout.stripe.com/c/pay/cs_desktop'),
        'desktop never reached the checkout URL: ' + JSON.stringify(env.__opened));
    });
  });
});

check('browser: still pre-opens synchronously (no pywebview bridge)', function () {
  const env = makeEnv({
    fetch: function (url) {
      if (String(url).indexOf('/api/trial/checkout') === 0) return new Promise(function () {});
      return { tier: 'trial', days_until_expiry: 2 };
    },
  });
  run(env);
  return flush().then(function () {
    const m = openModal(env);
    m.querySelector('.cm-up-cta').click();
    eq(env.__opened[0], 'about:blank',
      'browser lost its popup-blocker-safe pre-open');
  });
});

// The hosted dashboard is the OSS DASHBOARD_HTML rendered by the cloud with an
// injected window.CLOUD_TOKEN; localStorage['clawmetry-token'] is set by the
// SEPARATE /cloud account page. Reading only localStorage left the pill
// silently missing on the hosted dashboard.
check('cloud: reads window.CLOUD_TOKEN when localStorage is empty', function () {
  let asked = '';
  const env = makeEnv({
    cloud: true,
    token: '',
    fetch: function (url) {
      if (String(url).indexOf('/api/cloud/account') === 0) {
        asked = String(url);
        return { plan: 'trial', trial_active: true, trial_days_left: 3 };
      }
      return null;
    },
  });
  env.CLOUD_TOKEN = 'cm_injected_by_cloud';
  run(env);
  return flush().then(function () {
    includes(asked, 'cm_injected_by_cloud', 'never used the injected CLOUD_TOKEN');
    includes(slotHtml(env), '3 days remaining', 'hosted dashboard rendered no pill');
  });
});

check('cloud: CLOUD_TOKEN wins over a stale localStorage token', function () {
  let asked = '';
  const env = makeEnv({
    cloud: true,
    token: 'cm_stale_from_other_account',
    fetch: function (url) {
      if (String(url).indexOf('/api/cloud/account') === 0) {
        asked = String(url);
        return { plan: 'trial', trial_active: true, trial_days_left: 3 };
      }
      return null;
    },
  });
  env.CLOUD_TOKEN = 'cm_current';
  run(env);
  return flush().then(function () {
    includes(asked, 'cm_current');
    assert(asked.indexOf('cm_stale_from_other_account') === -1,
      'used the stale localStorage token over the injected one');
  });
});

// clawmetry-cloud injects its own fixed trial banner (#cm-trial-bar) into this
// page. Rendering the pill as well would give the hosted product two competing
// countdowns, so the cloud must opt in explicitly.
check('cloud: no pill unless the cloud opts in', function () {
  const env = makeEnv({
    cloud: true,
    cloudOptIn: false,
    token: 'cm_test',
    fetch: function () { return { plan: 'trial', trial_active: true, trial_days_left: 2 }; },
  });
  run(env);
  return flush().then(function () {
    eq(slotHtml(env), '',
      'rendered a pill on the hosted cloud without CM_TRIAL_PILL -- that is a '
      + 'second countdown next to the cloud banner');
  });
});

check('self-hosted needs no opt-in flag', function () {
  const env = makeEnv({ fetch: function () { return { tier: 'trial', days_until_expiry: 2 }; } });
  assert(env.CM_TRIAL_PILL === undefined, 'test env leaked the cloud flag');
  run(env);
  return flush().then(function () {
    includes(slotHtml(env), '2 days remaining', 'self-hosted pill needs an opt-in it should not');
  });
});

function fire(env, detail) {
  (env.document._listeners['cm:trial-state'] || []).forEach(function (fn) { fn({ detail: detail }); });
}

check('an unchanged countdown does not rebuild the pill', function () {
  const env = makeEnv({ fetch: function () { return null; } });
  run(env);
  return flush().then(function () {
    fire(env, { tier: 'trial', days_until_expiry: 5, expired: false });
    const first = env.document.getElementById('cm-trial-pill-btn');
    assert(first, 'pill never rendered');
    fire(env, { tier: 'trial', days_until_expiry: 5, expired: false });
    eq(env.document.getElementById('cm-trial-pill-btn'), first,
      'rebuilt the pill DOM for an identical state -- this drops hover/focus '
      + 'every poll');
  });
});

check('a changed countdown DOES repaint', function () {
  const env = makeEnv({ fetch: function () { return null; } });
  run(env);
  return flush().then(function () {
    fire(env, { tier: 'trial', days_until_expiry: 5, expired: false });
    fire(env, { tier: 'trial', days_until_expiry: 4, expired: false });
    includes(slotHtml(env), '4 days remaining', 'countdown froze at the old value');
  });
});

// The repaint cache must be cleared when the pill hides, or a lapse back into
// trial (license expiry, account switch) would be skipped as "unchanged".
check('paid -> trial again re-renders rather than staying hidden', function () {
  const env = makeEnv({ fetch: function () { return null; } });
  run(env);
  return flush().then(function () {
    fire(env, { tier: 'trial', days_until_expiry: 3, expired: false });
    includes(slotHtml(env), '3 days remaining');
    fire(env, { tier: 'pro', days_until_expiry: 300, expired: false });
    eq(slotHtml(env), '', 'pill survived an upgrade to paid');
    fire(env, { tier: 'trial', days_until_expiry: 3, expired: false });
    includes(slotHtml(env), '3 days remaining',
      'pill stayed hidden after lapsing back to trial -- stale repaint cache');
  });
});

// A lapsed Pro subscription is not an ended trial. Telling a former paying
// customer their "trial" ended is wrong and reads as an insult.
check('a lapsed PAID subscription says "Subscription expired", not "Trial ended"', function () {
  const env = makeEnv({ fetch: function () { return { tier: 'pro', expired: true, days_until_expiry: -1 }; } });
  run(env);
  return flush().then(function () {
    includes(slotHtml(env), 'Subscription expired');
    assert(slotHtml(env).indexOf('Trial ended') === -1,
      'called a lapsed paid subscription an ended trial');
    includes(slotHtml(env), 'Upgrade', 'no way back for a lapsed subscriber');
  });
});

check('an expired TRIAL still says "Trial ended"', function () {
  const env = makeEnv({ fetch: function () { return { tier: 'trial', expired: true, days_until_expiry: -1 }; } });
  run(env);
  return flush().then(function () {
    includes(slotHtml(env), 'Trial ended');
    assert(slotHtml(env).indexOf('Subscription expired') === -1);
  });
});

check('modal exposes a global the profile menu can call', function () {
  const env = makeEnv({ fetch: function () { return { tier: 'trial', days_until_expiry: 2 }; } });
  run(env);
  eq(typeof env.cmOpenUpgradeModal, 'function', 'window.cmOpenUpgradeModal missing');
  eq(typeof env.cmCloseUpgradeModal, 'function', 'window.cmCloseUpgradeModal missing');
});

check('closing removes the modal', function () {
  const env = makeEnv({ fetch: function () { return { tier: 'trial', days_until_expiry: 2 }; } });
  run(env);
  return flush().then(function () {
    openModal(env);
    assert(env.document.getElementById('cm-upgrade-modal'), 'not mounted');
    env.cmCloseUpgradeModal();
    assert(!env.document.getElementById('cm-upgrade-modal'), 'modal survived close');
  });
});

check('a dead status endpoint leaves the header clean, not half-rendered', function () {
  const env = makeEnv({ fetch: function () { return Promise.reject(new Error('boom')); } });
  run(env);
  return flush().then(function () {
    eq(slotHtml(env), '', 'rendered something off a failed status fetch');
  });
});

Promise.all(pending).then(function () {
  if (failures) {
    console.log('\nFAIL: ' + failures + ' check(s) failed');
    process.exit(1);
  }
  console.log('\nPASS');
});
