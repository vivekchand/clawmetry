// ─────────────────────────────────────────────────────────────────────────
// Header trial pill + in-app upgrade modal.
//
// Until this existed, a trialing install had exactly two ways to learn its
// trial was ending and one way to act on it:
//   * the "Trial · N days left" line inside the avatar dropdown (two clicks
//     away, so in practice nobody saw it), and
//   * the un-dismissable hard-block overlay, which only appears AFTER the
//     trial has already expired and the dashboard has locked.
// The one in-app path to a card form (POST /api/trial/checkout, which mints
// a per-account Stripe Checkout Session) was reachable only from that
// post-expiry overlay. Before expiry the sole "Upgrade plan" affordance
// opened clawmetry.com/pricing in a new tab and dropped the account context
// on the floor.
//
// So: a persistent pill in the header for the whole trial, with a green
// Upgrade button beside it that opens a Starter/Pro x Monthly/Annual chooser
// and takes the user straight to Stripe without leaving the dashboard.
//
// Runs on all three deployments off one component:
//   * self-hosted / desktop -> GET /api/trial/status   (routes/trial.py)
//   * hosted cloud          -> GET /api/cloud/account  (CLOUD_MODE only)
// and routes checkout to whichever billing endpoint that deployment owns.
//
// Loaded AFTER app.js so window.CM_PLANS (the single pricing ladder shared
// with the hard-block overlay and the self-host onboarding modal) is already
// published. It is never re-declared here: two hardcoded price ladders is
// how a reprice ships half-done.
// ─────────────────────────────────────────────────────────────────────────
(function initClawMetryTrialPill() {
  'use strict';

  var PILL_ID = 'cm-trial-pill';
  // NOT "cm-trial-upgrade-btn": clawmetry-cloud's dashboard.py injects a trial
  // banner into this very page using that id. Two elements sharing an id is
  // invalid HTML and makes getElementById a coin toss between two different
  // components' buttons.
  var BTN_ID = 'cm-trial-pill-btn';
  var MODAL_ID = 'cm-upgrade-modal';
  var STYLE_ID = 'cm-trial-pill-style';
  var SLOT_ID = 'cm-trial-pill-slot';

  // Poll cadence. The pill is a countdown in days, so it does not need to be
  // fresh to the second; this is a fallback for the case where app.js's
  // hard-block module is an older cached copy that does not broadcast state.
  var POLL_MS = 300000;          // 5 min
  var POLL_MS_PAYING = 10000;    // while the user is off at Stripe
  var PAYING_WINDOW_MS = 600000; // 10 min

  // Tiers that mean "already paying" — the pill and button stay hidden.
  var PAID_TIERS = ['starter', 'pro', 'cloud_pro', 'cloud_starter',
                    'selfhosted_pro', 'self_hosted_pro', 'enterprise'];

  var _state = null;
  var _checkoutClickedAt = 0;
  var _timer = null;
  // Modal selection lives in module state, not the DOM, so a background
  // refresh that repaints the pill can never reset a half-made choice.
  //
  // Pro is recommended here, with the same monthly interval as the
  // hard-block overlay's Starter default on purpose: that screen is a
  // blocked user trying to get unstuck, so it leads with the cheapest way
  // back in. This one is a proactive upsell to somebody still working, so it
  // leads with the recommended tier. Both are one click from the other.
  var _selTier = 'pro';
  var _selInterval = 'month';

  // Last thing painted into the slot, so a background refresh that reports an
  // unchanged countdown is a no-op. Without this the pill's DOM is rebuilt on
  // every poll (once a minute), which drops hover and focus mid-interaction
  // for no reason.
  var _lastPaint = null;

  function esc(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  function tr(key, vars, fallback) {
    try {
      if (typeof window.t === 'function') return window.t(key, vars, fallback);
    } catch (e) { /* i18n not loaded yet */ }
    return vars ? String(fallback).replace(/\{(\w+)\}/g, function (m, k) {
      return vars[k] != null ? vars[k] : m;
    }) : fallback;
  }

  function isCloud() {
    try { return !!window.CLOUD_MODE; } catch (e) { return false; }
  }

  // Whether this deployment should render the pill at all.
  //
  // Self-hosted and desktop: always. They have no other trial affordance.
  //
  // Hosted cloud: only when the cloud opts in with `window.CM_TRIAL_PILL`.
  // clawmetry-cloud already injects its OWN trial UI into this page -- a fixed
  // top banner (#cm-trial-bar) with a countdown and an upgrade CTA -- and
  // rendering both would give the hosted product two competing countdowns.
  // The cloud-side change is two lines (set the flag, drop the banner
  // injection), and until it lands the cloud keeps the affordance it has. The
  // cloud code path below is complete and tested, not stubbed; this gate is
  // about not shipping duplicate UI across a repo boundary.
  function pillEnabled() {
    if (!isCloud()) return true;
    try { return !!window.CM_TRIAL_PILL; } catch (e) { return false; }
  }

  function plans() {
    // window.CM_PLANS is published by app.js (the hard-block overlay owns the
    // table). If app.js failed to load we render the chooser WITHOUT prices
    // rather than inventing a ladder that Stripe would then contradict.
    try {
      if (window.CM_PLANS && window.CM_PLANS.prices) return window.CM_PLANS;
    } catch (e) { /* noop */ }
    return null;
  }

  // ── state normalisation ───────────────────────────────────────────────
  // Both backends get flattened to one shape so everything below this line
  // is deployment-agnostic:
  //   { show, expired, days, hours, tier, label }
  function normalise(raw) {
    if (!raw) return null;
    var tier = String(raw.tier || raw.plan || '').toLowerCase();
    var expired, days, hours;

    if (isCloud() && (raw.trial_active !== undefined || raw.plan !== undefined)) {
      // /api/cloud/account shape.
      expired = !!raw.expired;
      days = (typeof raw.trial_days_left === 'number') ? raw.trial_days_left : null;
      hours = (typeof raw.trial_hours_left === 'number') ? raw.trial_hours_left : null;
      var trialing = !!raw.trial_active || tier === 'trial';
      return {
        show: trialing || expired,
        expired: expired,
        days: days,
        hours: hours,
        tier: tier,
      };
    }

    // /api/trial/status shape (self-hosted + desktop).
    expired = !!raw.expired;
    days = (typeof raw.days_until_expiry === 'number') ? raw.days_until_expiry : null;
    return {
      show: (tier === 'trial') || expired,
      expired: expired,
      days: days,
      hours: null,
      tier: tier,
    };
  }

  function isPaid(st) {
    return !!st && PAID_TIERS.indexOf(st.tier) !== -1 && !st.expired;
  }

  // ── copy ──────────────────────────────────────────────────────────────
  function pillLabel(st) {
    if (st.expired) {
      // A lapsed PAID subscription is not an ended trial. The hard-block
      // overlay already draws this distinction in its reason line ("Your
      // ClawMetry trial has ended" vs "Your ClawMetry subscription has
      // expired"); telling a former Pro customer their "trial" ended is both
      // wrong and slightly insulting.
      if (st.tier && st.tier !== 'trial') {
        return tr('trial.pill_sub_expired', null, 'Subscription expired');
      }
      return tr('trial.pill_ended', null, 'Trial ended');
    }
    var d = st.days;
    if (d === null || d === undefined) {
      // No expiry known. Say so plainly rather than printing a number we
      // cannot stand behind — a wrong countdown is worse than none.
      return tr('trial.pill_generic', null, 'Pro trial');
    }
    if (d <= 0) {
      if (typeof st.hours === 'number' && st.hours > 0) {
        if (st.hours === 1) return tr('trial.pill_one_hour', null, 'Pro trial · 1 hour remaining');
        return tr('trial.pill_hours', { hours: st.hours },
          'Pro trial · {hours} hours remaining');
      }
      return tr('trial.pill_today', null, 'Pro trial · ends today');
    }
    if (d === 1) return tr('trial.pill_one_day', null, 'Pro trial · 1 day remaining');
    return tr('trial.pill_days', { days: d }, 'Pro trial · {days} days remaining');
  }

  // Urgency drives colour only — never the wording, which stays factual.
  function urgency(st) {
    if (st.expired) return 'over';
    if (st.days === null || st.days === undefined) return 'calm';
    if (st.days <= 2) return 'urgent';
    return 'calm';
  }

  // ── styles ────────────────────────────────────────────────────────────
  function injectStyles() {
    if (document.getElementById(STYLE_ID)) return;
    var st = document.createElement('style');
    st.id = STYLE_ID;
    st.textContent = [
      '#' + SLOT_ID + '{display:none;align-items:center;gap:8px;flex-shrink:0;}',
      '#' + SLOT_ID + '.cm-on{display:flex;}',
      '#' + PILL_ID + '{display:inline-flex;align-items:center;gap:6px;',
      '  padding:6px 11px;border-radius:999px;font-size:12px;font-weight:600;',
      '  white-space:nowrap;letter-spacing:0.1px;line-height:1;',
      '  border:1px solid transparent;transition:background 140ms ease;}',
      '#' + PILL_ID + '.cm-calm{background:rgba(234,179,8,0.14);color:#eab308;',
      '  border-color:rgba(234,179,8,0.34);}',
      '#' + PILL_ID + '.cm-urgent{background:rgba(249,115,22,0.16);color:#fb923c;',
      '  border-color:rgba(249,115,22,0.40);}',
      '#' + PILL_ID + '.cm-over{background:rgba(239,68,68,0.16);color:#f87171;',
      '  border-color:rgba(239,68,68,0.42);}',
      '#' + PILL_ID + ' .cm-tp-dot{width:6px;height:6px;border-radius:50%;',
      '  background:currentColor;flex-shrink:0;}',
      '#' + BTN_ID + '{display:inline-flex;align-items:center;gap:5px;',
      '  padding:6px 13px;border-radius:8px;border:1px solid #16a34a;',
      '  background:#15803d;color:#ffffff;font-size:12px;font-weight:700;',
      '  cursor:pointer;white-space:nowrap;line-height:1;font-family:inherit;',
      '  transition:background 140ms ease,border-color 140ms ease;}',
      '#' + BTN_ID + ':hover{background:#15803d;border-color:#15803d;}',
      '#' + BTN_ID + ':focus-visible{outline:2px solid #4ade80;outline-offset:2px;}',

      '@media (max-width:640px){#' + PILL_ID + '{font-size:11px;padding:5px 9px;}}',
    ].join('');
    document.head.appendChild(st);
  }

  // ── pill render ───────────────────────────────────────────────────────
  function slot() {
    var el = document.getElementById(SLOT_ID);
    if (el) return el;
    // The slot is rendered server-side in DASHBOARD_HTML. If a cached
    // template predates it, fall back to appending into the nav so the pill
    // still appears rather than silently doing nothing.
    var nav = document.querySelector('.nav');
    if (!nav) return null;
    el = document.createElement('div');
    el.id = SLOT_ID;
    nav.appendChild(el);
    return el;
  }

  function renderPill(st) {
    var host = slot();
    if (!host) return;
    if (!pillEnabled() || !st || !st.show || isPaid(st)) {
      host.className = '';
      host.innerHTML = '';
      _lastPaint = null;
      return;
    }
    injectStyles();
    var label = pillLabel(st);
    var cta = st.expired
      ? tr('trial.upgrade_now', null, 'Upgrade')
      : tr('trial.upgrade', null, 'Upgrade');
    var paint = urgency(st) + '\u0000' + label + '\u0000' + cta;
    if (paint === _lastPaint && document.getElementById(BTN_ID)) return;
    _lastPaint = paint;
    host.innerHTML = ''
      + '<span id="' + PILL_ID + '" class="cm-' + urgency(st) + '" '
      + 'title="' + esc(tr('trial.pill_title', null,
          'Your ClawMetry Pro trial. Upgrade to keep every runtime, alert, and policy after it ends.')) + '">'
      + '<span class="cm-tp-dot" aria-hidden="true"></span>' + esc(label)
      + '</span>'
      + '<button type="button" id="' + BTN_ID + '">' + esc(cta) + '</button>';
    host.className = 'cm-on';
    var btn = document.getElementById(BTN_ID);
    if (btn) btn.addEventListener('click', function () { openModal('pill'); });
  }

  // ── modal ─────────────────────────────────────────────────────────────
  function buildModal() {
    var el = document.createElement('div');
    el.id = MODAL_ID;
    el.className = 'cm-trial-offer';
    el.setAttribute('role', 'dialog');
    el.setAttribute('aria-modal', 'true');
    el.setAttribute('aria-labelledby', 'cm-up-title');

    var st = _state || {};
    var eyebrow = st.expired
      ? tr('trial.modal_eyebrow_ended', null, 'Trial ended')
      : tr('trial.modal_eyebrow', null, 'Pro trial');
    var head = st.expired
      ? tr('trial.modal_title_ended', null, 'Choose a plan to pick up where you left off')
      : tr('trial.modal_title', null, 'Choose a plan');
    var sub;
    if (st.expired) {
      sub = tr('trial.modal_sub_ended', null,
        'Your trial has ended. Pick a plan and everything unlocks again the moment checkout completes.');
    } else if (st.days === 1) {
      sub = tr('trial.modal_sub_one_day', null,
        'Your trial has 1 day left. You can upgrade during the trial. The trial still continues until its final day.');
    } else if (typeof st.days === 'number' && st.days > 0) {
      sub = tr('trial.modal_sub_days', { days: st.days },
        'Your trial has {days} days left. You can upgrade during the trial. The trial still continues until its final day.');
    } else {
      sub = tr('trial.modal_sub', null,
        'You can upgrade during the trial. The trial still continues until its final day.');
    }

    el.innerHTML = window.CMTrialOffer.html({
      prefix: 'cm-up', title: st.expired ? tr('trial.offer.continue_title', null, 'Choose how to continue') : head,
      body: st.expired ? tr('trial.offer.continue_body', null, 'Choose a plan to continue with ClawMetry.') : sub,
      tier: _selTier, interval: _selInterval, dismissible: true,
      showFree: !!st.expired,
      recoverable: !!st.expired && PAID_TIERS.indexOf(st.tier) === -1,
    });
    return el;
  }

  function repaint(el) {
    window.CMTrialOffer.repaint(el, 'cm-up', _selTier, _selInterval);
  }

  function wireTiers(el) {
    Array.prototype.forEach.call(el.querySelectorAll('.cm-up-tier'), function (b) {
      b.addEventListener('click', function () {
        _selTier = b.getAttribute('data-tier') === 'pro' ? 'pro' : 'starter';
        repaint(el);
      });
    });
  }

  function closeModal() {
    var el = document.getElementById(MODAL_ID);
    if (!el) return;
    if (el._cmEsc) {
      try { document.removeEventListener('keydown', el._cmEsc, true); } catch (e) { /* noop */ }
    }
    if (el._cmReleaseFocus) el._cmReleaseFocus();
    el.remove();
    try { document.body.style.overflow = ''; } catch (e) { /* noop */ }
  }

  // The account token, which the cloud exposes in two different places.
  //
  // The hosted dashboard is the OSS DASHBOARD_HTML rendered by the cloud with
  // an injected `window.CLOUD_TOKEN` (clawmetry-cloud dashboard.py, the
  // early_flag script). `localStorage['clawmetry-token']` is set by the
  // SEPARATE /cloud account page. Read only the latter and the pill goes
  // silently missing on the hosted dashboard -- no error, just no pill on one
  // of the three deployments this component exists to cover.
  function cloudToken() {
    try {
      if (typeof window.CLOUD_TOKEN === 'string' && window.CLOUD_TOKEN) {
        return window.CLOUD_TOKEN;
      }
    } catch (e) { /* noop */ }
    try {
      return (window.localStorage && localStorage.getItem('clawmetry-token')) || '';
    } catch (e) { return ''; }
  }

  // Resolve a Stripe URL for the current selection. The two deployments own
  // different billing endpoints; both answer with {url}.
  function requestCheckoutUrl() {
    if (isCloud()) {
      var tok = cloudToken();
      return fetch('/api/billing/checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tier: _selTier,
          plan: _selInterval === 'year' ? 'yearly' : 'monthly',
          cm_key: tok,
          token: tok,
        }),
      }).then(function (r) { return r.json().catch(function () { return {}; }); });
    }
    // Self-hosted / desktop: the node already knows its account, so the cloud
    // mints a per-account Checkout Session and the license arrives on the
    // next daemon heartbeat — no key to copy-paste.
    return fetch('/api/trial/checkout', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        tier: _selTier,
        plan: _selInterval === 'year' ? 'yearly' : 'monthly',
      }),
    }).then(function (r) { return r.json().catch(function () { return {}; }); });
  }

  function openModal(source) {
    var locked = document.getElementById('cm-hard-block-overlay');
    if (locked) { var title = locked.querySelector('h2'); if (title) title.focus(); return; }
    injectStyles();
    closeModal();
    var el = buildModal();
    document.body.appendChild(el);
    el._cmReleaseFocus = window.CMTrialOffer.trap(el, closeModal);
    try { document.body.style.overflow = 'hidden'; } catch (e) { /* noop */ }

    // Fire-and-forget funnel telemetry, same event stream the hard-block
    // overlay writes to.
    try {
      fetch('/api/paywall/event', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          event: 'upgrade_modal_view',
          source: source || 'pill',
          tier: _state && _state.tier,
          days_left: _state && _state.days,
        }),
      }).catch(function () {});
    } catch (e) { /* noop */ }

    Array.prototype.forEach.call(el.querySelectorAll('.cm-up-seg button'), function (b) {
      b.addEventListener('click', function () {
        _selInterval = b.getAttribute('data-interval') === 'year' ? 'year' : 'month';
        repaint(el);
      });
    });
    wireTiers(el);

    el.querySelector('.cm-up-close').addEventListener('click', closeModal);
    el.addEventListener('click', function (ev) { if (ev.target === el) closeModal(); });
    var statusEl = el.querySelector('.cm-up-status');
    var cta = el.querySelector('.cm-up-cta');
    cta.addEventListener('click', function () {
      _checkoutClickedAt = Date.now();
      // In a BROWSER the tab MUST be opened synchronously inside the click
      // handler — popup blockers kill window.open from inside a fetch
      // callback — and is redirected once the URL arrives.
      //
      // In the DESKTOP shell it must NOT be. desktop/app.py patches
      // window.open to hand external https URLs to the system browser over
      // the pywebview bridge, and that shim only recognises the FINAL url:
      // 'about:blank' is not https, so a pre-opened tab falls through to the
      // native webview and the buyer is left staring at a chromeless blank
      // window while the real checkout never surfaces. There is no popup
      // blocker to defeat inside the shell, so skip the pre-open and let the
      // shim route the finished URL.
      var desktop = false;
      try {
        desktop = !!(window.pywebview && window.pywebview.api
                     && window.pywebview.api.open_external);
      } catch (e) { desktop = false; }
      var payTab = null;
      if (!desktop) {
        try { payTab = window.open('about:blank', '_blank'); } catch (e) { payTab = null; }
      }
      function go(url) {
        if (payTab) { try { payTab.location = url; return; } catch (e) { /* fall through */ } }
        try { window.open(url, '_blank', 'noopener'); } catch (e) { window.location.href = url; }
      }
      function fail(msg) {
        if (payTab) { try { payTab.close(); } catch (e) { /* noop */ } }
        statusEl.className = 'cm-up-status cm-offer-status err';
        statusEl.textContent = msg;
        cta.disabled = false;
      }
      cta.disabled = true;
      statusEl.className = 'cm-up-status cm-offer-status';
      statusEl.textContent = tr('trial.opening', null, 'Opening secure checkout…');
      requestCheckoutUrl()
        .then(function (resp) {
          var url = resp && resp.url;
          if (!url) {
            // Never send the user to a page we did not get from the server.
            fail((resp && (resp.error || resp.message))
              || tr('trial.checkout_failed', null,
                   'Could not start checkout. Please try again, or contact support@clawmetry.com.'));
            return;
          }
          go(url);
          cta.disabled = false;
          statusEl.className = 'cm-up-status cm-offer-status ok';
          statusEl.textContent = tr('trial.waiting', null,
            'Waiting for payment. This dashboard updates automatically once checkout completes.');
          schedule();  // poll hard while they are off paying
        })
        .catch(function () {
          fail(tr('trial.checkout_offline', null,
            'Could not reach the billing service. Check your connection and try again.'));
        });
      try {
        fetch('/api/paywall/event', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            event: 'upgrade_checkout_click',
            tier: _selTier,
            interval: _selInterval,
            source: source || 'pill',
          }),
        }).catch(function () {});
      } catch (e) { /* noop */ }
    });

    var free = el.querySelector('.cm-up-free');
    function continueFree() {
      if (isCloud()) { closeModal(); return Promise.resolve(); }
      return fetch('/api/trial/continue-free', {method: 'POST'}).then(function (response) {
        if (!response.ok) throw new Error('free');
        var url = new URL(window.location.href);
        url.searchParams.set('runtime', 'openclaw');
        window.location.replace(url.toString());
      });
    }
    if (free) free.addEventListener('click', function () {
      continueFree().catch(function () { statusEl.textContent = tr('trial.offer.free_failed', null, 'Could not switch to free mode. Please try again.'); });
    });
    var more = el.querySelector('.cm-offer-more');
    if (more) more.addEventListener('click', function () {
      window.CMTrialOffer.recover(el, function () { window.location.reload(); }, continueFree);
    });

    // "Already have a license key?" — annual self-hosted is a one-time
    // license purchase delivered by email, so the person completing that
    // flow needs somewhere to put the key without hunting for the CLI.
    var keyLink = el.querySelector('#cm-up-havekey');
    var keyWrap = el.querySelector('#cm-up-keywrap');
    if (keyLink && keyWrap) {
      keyLink.addEventListener('click', function () {
        keyWrap.style.display = keyWrap.style.display === 'none' ? 'block' : 'none';
        keyLink.setAttribute('aria-expanded', String(keyWrap.style.display === 'block'));
        if (keyWrap.style.display === 'block') {
          var ta = el.querySelector('#cm-up-key');
          if (ta) ta.focus();
        }
      });
    }
    var activate = el.querySelector('.cm-up-activate');
    if (activate) {
      activate.addEventListener('click', function () {
        var ta = el.querySelector('#cm-up-key');
        var key = ((ta && ta.value) || '').trim();
        if (!key) {
          statusEl.className = 'cm-up-status cm-offer-status err';
          statusEl.textContent = tr('trial.paste_first', null, 'Paste a license key first.');
          return;
        }
        activate.disabled = true;
        statusEl.className = 'cm-up-status cm-offer-status';
        statusEl.textContent = tr('trial.verifying', null, 'Verifying key…');
        fetch('/api/license/activate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ key: key }),
        })
          .then(function (r) { return r.json().catch(function () { return {}; }); })
          .then(function (resp) {
            activate.disabled = false;
            if (resp && resp.ok === false) {
              statusEl.className = 'cm-up-status cm-offer-status err';
              statusEl.textContent = resp.message || resp.error
                || tr('trial.activate_failed', null, 'License activation failed.');
              return;
            }
            statusEl.className = 'cm-up-status cm-offer-status ok';
            statusEl.textContent = tr('trial.activated', null, 'The license was installed. The page will reload.');
            setTimeout(function () { try { window.location.reload(); } catch (e) { /* noop */ } }, 900);
          })
          .catch(function () {
            activate.disabled = false;
            statusEl.className = 'cm-up-status cm-offer-status err';
            statusEl.textContent = tr('trial.activate_failed', null, 'License activation failed.');
          });
      });
    }
  }

  // ── polling ───────────────────────────────────────────────────────────
  function fetchState() {
    if (isCloud()) {
      var tok = cloudToken();
      // The cloud page fetches this itself on load; reuse the result when it
      // is already there rather than issuing a second identical request.
      try {
        var paying = _checkoutClickedAt && (Date.now() - _checkoutClickedAt) < PAYING_WINDOW_MS;
        if (window._account && !paying) return Promise.resolve(window._account);
      } catch (e) { /* noop */ }
      if (!tok) return Promise.resolve(null);
      return fetch('/api/cloud/account?token=' + encodeURIComponent(tok))
        .then(function (r) { return r.ok ? r.json() : null; })
        .then(function (account) {
          if (account && account.plan) { window._account = account; window.CLOUD_PLAN = account.plan; }
          return account;
        })
        .catch(function () { return null; });
    }
    return fetch('/api/trial/status')
      .then(function (r) { return r.ok ? r.json() : null; })
      .catch(function () { return null; });
  }

  function apply(raw) {
    var st = normalise(raw);
    if (!st) return;
    var unlocked = _checkoutClickedAt && _state && !isPaid(_state) && isPaid(st);
    _state = st;
    renderPill(st);
    if (unlocked && document.getElementById(MODAL_ID)) {
      closeModal();
      window.location.reload();
    }
  }

  function schedule() {
    if (_timer) clearTimeout(_timer);
    var paying = _checkoutClickedAt && (Date.now() - _checkoutClickedAt) < PAYING_WINDOW_MS;
    _timer = setTimeout(tick, paying ? POLL_MS_PAYING : POLL_MS);
  }

  function tick() {
    fetchState().then(function (raw) {
      if (raw) apply(raw);
      schedule();
    });
  }

  // app.js's hard-block module already polls /api/trial/status. It broadcasts
  // each snapshot so the steady state costs one request, not two; our own
  // poll above is the fallback for a cached app.js that predates the event.
  try {
    window.addEventListener('cm:trial-state', function (ev) {
      // Hosted billing state comes from the account, not the cloud host's local license.
      if (ev && ev.detail && (!isCloud() || ev.detail.plan !== undefined)) apply(ev.detail);
    });
  } catch (e) { /* noop */ }

  // Public entry point. The profile menu's "Upgrade plan" item calls this so
  // there is exactly one upgrade surface in the app.
  window.cmOpenUpgradeModal = function (source) { openModal(source || 'menu'); };
  window.cmCloseUpgradeModal = closeModal;

  function boot() {
    injectStyles();
    tick();
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
