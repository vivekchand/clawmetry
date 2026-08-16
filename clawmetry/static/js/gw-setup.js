// Gateway connection — headless only. Every manual gateway-token UI is gone:
// the auto-popping "ClawMetry Setup" wizard (v0.1-era UX from when ClawMetry
// only watched the OpenClaw gateway) and the opt-in Developer > Gateway form
// that replaced it. The product detects 21+ runtimes automatically and the
// gateway token itself is auto-detected server-side from
// ~/.openclaw/openclaw.json, so there is nothing left for a user to fill in.
// What remains keeps an already-configured connection alive: a ?token=XXX URL
// (used by remote/Docker links) and a localStorage-remembered token are still
// posted to /api/gw/config on load. First-run onboarding lives in
// onboarding.js; remote sign-in with a raw token lives in the login overlay.
async function checkGwConfig() {
  // Support ?token=XXX in URL — auto-configure and strip from address bar
  try {
    var urlParams = new URLSearchParams(window.location.search);
    var urlToken = urlParams.get('token');
    if (urlToken && urlToken.trim()) {
      urlToken = urlToken.trim();
      localStorage.setItem('clawmetry-gw-token', urlToken);
      localStorage.setItem('clawmetry-token', urlToken);
      var tr = await fetch('/api/gw/config', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({token: urlToken})
      });
      var td = await tr.json();
      // Strip token from URL (keep it out of browser history)
      urlParams.delete('token');
      var clean = window.location.pathname + (urlParams.toString() ? '?' + urlParams.toString() : '');
      window.history.replaceState({}, '', clean);
      if (td.ok) { location.reload(); return; }
    }
  } catch(e) {}
  try {
    const r = await fetch('/api/gw/config');
    const d = await r.json();
    if (!d.configured) {
      // Not configured server-side — try a token this browser remembers.
      const saved = localStorage.getItem('clawmetry-gw-token');
      if (saved) {
        await fetch('/api/gw/config', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({token: saved})
        });
      }
    }
  } catch(e) {}
}

// Check on load
document.addEventListener('DOMContentLoaded', checkGwConfig);

// ClawMetry Cloud CTA
var _cloudEmail = '';
// How the modal was reached decides the OAuth rail. 'managed' (the default:
// the "Enable Cloud Sync" CTA, the onboarding cloud card, alert sign-up CTAs)
// sends mode=managed explicitly — clicking those IS the egress opt-in.
// 'signin' (the profile menu's "Sign in / Create account") omits mode so the
// backend picks the rail from the install's recorded intent: a self-host
// machine signing back in stays local-only (founder report 2026-08-09:
// profile-menu sign-in silently enabled cloud sync on a self-host install).
var _cloudModalIntent = 'managed';
function openCloudModal(intent) {
  _cloudModalIntent = (intent === 'signin') ? 'signin' : 'managed';
  var _cmo = document.getElementById('cloud-modal-overlay');
  document.body.appendChild(_cmo);
  _cmo.style.display = 'flex';
  document.getElementById('cloud-step-email').style.display = '';
  document.getElementById('cloud-step-otp').style.display = 'none';
  document.getElementById('cloud-step-done').style.display = 'none';
  var _w = document.getElementById('cloud-step-wait'); if (_w) _w.style.display = 'none';
  document.getElementById('cloud-email-error').style.display = 'none';
  setTimeout(function(){ var el = document.getElementById('cloud-email-input'); if(el) el.focus(); }, 100);
}
function closeCloudModal() {
  _cloudStopOauthPoll();
  document.getElementById('cloud-modal-overlay').style.display = 'none';
}
document.addEventListener('keydown', function(e){ if(e.key==='Escape') closeCloudModal(); });

// One-click cloud sign-up + node connect via GitHub/Google OAuth.
// The local dashboard opens the cloud OAuth flow with a loopback bridge (cli_port);
// when the user authorizes, the cloud redirects the freshly-minted cm_ key back to
// a one-shot 127.0.0.1 listener the daemon started, which registers the node and
// starts the sync daemon. The key never leaves this machine over the network.
var _cloudOauthTimer = null;
function _cloudStopOauthPoll() { if (_cloudOauthTimer) { clearInterval(_cloudOauthTimer); _cloudOauthTimer = null; } }
function cloudOauth(provider) {
  var payload = {provider: provider};
  if (_cloudModalIntent !== 'signin') payload.mode = 'managed';
  fetch('/api/cloud-cta/oauth-start', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)})
    .then(function(r){ return r.json(); })
    .then(function(d){
      if (d.ok && d.url) {
        window.open(d.url, '_blank');
        document.getElementById('cloud-step-email').style.display = 'none';
        document.getElementById('cloud-step-otp').style.display = 'none';
        document.getElementById('cloud-step-done').style.display = 'none';
        var w = document.getElementById('cloud-step-wait'); if (w) w.style.display = '';
        var we = document.getElementById('cloud-wait-error'); if (we) we.style.display = 'none';
        _cloudPollOauth();
      } else {
        var err = document.getElementById('cloud-email-error');
        err.textContent = d.error || 'Sign-in is unavailable right now. Use email instead.';
        err.style.display = '';
      }
    })
    .catch(function(){ var err = document.getElementById('cloud-email-error'); err.textContent = 'Network error. Try again.'; err.style.display = ''; });
}
function _cloudPollOauth() {
  _cloudStopOauthPoll();
  var tries = 0;
  _cloudOauthTimer = setInterval(function(){
    tries++;
    fetch('/api/cloud-cta/oauth-status').then(function(r){ return r.json(); }).then(function(d){
      if (d.status === 'connected') {
        _cloudStopOauthPoll();
        _cloudShowConnected(d.enc_key || '');
        _updateCloudStatus();
      } else if (d.status === 'error') {
        _cloudStopOauthPoll();
        var we = document.getElementById('cloud-wait-error');
        if (we) { we.textContent = d.error || 'Sign-in did not complete. Please try again.'; we.style.display = ''; }
      } else if (tries > 150) {  // ~5 min at 2s
        _cloudStopOauthPoll();
        var we2 = document.getElementById('cloud-wait-error');
        if (we2) { we2.textContent = 'Timed out waiting for sign-in. Please try again.'; we2.style.display = ''; }
      }
    }).catch(function(){});
  }, 2000);
}
function _cloudShowConnected(encKey) {
  document.getElementById('cloud-step-email').style.display = 'none';
  document.getElementById('cloud-step-otp').style.display = 'none';
  var w = document.getElementById('cloud-step-wait'); if (w) w.style.display = 'none';
  document.getElementById('cloud-step-done').style.display = '';
  if (encKey) {
    var box = document.getElementById('cloud-done-enckey');
    var msg = document.getElementById('cloud-done-msg');
    if (msg) msg.textContent = 'Your node is now syncing to ClawMetry Cloud.';
    var code = document.getElementById('cloud-enc-key');
    if (code) code.textContent = encKey;
    if (box) box.style.display = '';
  }
}
function cloudCopyEncKey() {
  var code = document.getElementById('cloud-enc-key');
  if (!code) return;
  var txt = code.textContent || '';
  try {
    navigator.clipboard.writeText(txt);
  } catch (e) {
    var r = document.createRange(); r.selectNode(code);
    var sel = window.getSelection(); sel.removeAllRanges(); sel.addRange(r);
    try { document.execCommand('copy'); } catch (e2) {}
    sel.removeAllRanges();
  }
}
function cloudSendOtp() {
  var email = document.getElementById('cloud-email-input').value.trim();
  if (!email || !email.includes('@')) {
    var err = document.getElementById('cloud-email-error');
    err.textContent = 'Please enter a valid email.';
    err.style.display = '';
    return;
  }
  _cloudEmail = email;
  document.getElementById('cloud-email-error').style.display = 'none';
  fetch('https://app.clawmetry.com/api/otp/send', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({email: email})})
    .then(function(r){ return r.json(); })
    .then(function(d){
      if (d.ok) {
        document.getElementById('cloud-step-email').style.display = 'none';
        document.getElementById('cloud-step-otp').style.display = '';
        setTimeout(function(){ var el = document.getElementById('cloud-otp-input'); if(el) el.focus(); }, 100);
      } else {
        var err = document.getElementById('cloud-email-error');
        err.textContent = d.error || 'Could not send code. Try again.';
        err.style.display = '';
      }
    })
    .catch(function(){ var err = document.getElementById('cloud-email-error'); err.textContent = 'Network error. Try again.'; err.style.display = ''; });
}
function cloudResendOtp() { cloudSendOtp(); }
function cloudVerifyOtp() {
  var code = document.getElementById('cloud-otp-input').value.replace(/\s/g,'');
  if (code.length !== 6) {
    var err = document.getElementById('cloud-otp-error');
    err.textContent = 'Enter the 6-digit code from your email.';
    err.style.display = '';
    return;
  }
  // Route through the LOCAL dashboard endpoint (not app.clawmetry.com
  // directly): /api/cloud-cta/verify-otp proxies to cloud AND persists the
  // returned cm_ key via _write_cloud_token(). Bypassing this seam — as the
  // previous direct fetch to https://app.clawmetry.com/api/otp/verify did —
  // set the browser cookie but left the local machine with no token, so
  // /api/cloud-cta/status kept reporting connected=false, the onboarding
  // gate stayed required=true, and the modal reappeared on every launch
  // (founder report 2026-08-12).
  fetch('/api/cloud-cta/verify-otp', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({email: _cloudEmail, code: code}),
  })
    .then(function(r){ return r.json(); })
    .then(function(d){
      if (d.ok && d.token) {
        // Record the choice in the dashboard's onboarding gate so the
        // hard-gate modal never re-fires. _apply_marker_semantics() there
        // also runs enable_cloud() + registers a persistent daemon.
        fetch('/api/onboarding/complete', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({choice: 'managed'}),
        }).catch(function(){ /* best-effort — the token write above is what actually pairs */ });
        document.getElementById('cloud-step-otp').style.display = 'none';
        document.getElementById('cloud-step-done').style.display = '';
        setTimeout(function(){
          try { window.open('https://app.clawmetry.com/auth?token=' + encodeURIComponent(d.token), '_blank'); } catch (e) {}
          closeCloudModal();
          _updateCloudStatus();
          // Reload so /api/onboarding/state re-reads the freshly written
          // gate file and the dashboard boots without the modal.
          try { location.reload(); } catch (e) {}
        }, 1800);
      } else {
        var err = document.getElementById('cloud-otp-error');
        err.textContent = d.error || 'Invalid code. Try again.';
        err.style.display = '';
      }
    })
    .catch(function(){ var err = document.getElementById('cloud-otp-error'); err.textContent = 'Network error. Try again.'; err.style.display = ''; });
}
// ── E2E encryption key modal (Settings) ─────────────────────────────────────
// Local dashboard only — the /api/local/e2e-key route this reads does not
// exist on the hosted cloud dashboard (see dashboard.py for why).
var _e2eKeyValue = '';
var _e2eKeyRevealed = false;

function openE2eKeyModal() {
  var overlay = document.getElementById('e2e-key-modal-overlay');
  if (!overlay) return;
  document.body.appendChild(overlay);
  overlay.style.display = 'flex';
  document.getElementById('e2e-key-empty').style.display = 'none';
  document.getElementById('e2e-key-body').style.display = 'none';
  document.getElementById('e2e-key-error').style.display = 'none';
  document.getElementById('e2e-key-regen-confirm').style.display = 'none';
  document.getElementById('e2e-key-regen-btn').style.display = '';
  _e2eKeyRevealed = false;
  fetch('/api/local/e2e-key').then(function (r) { return r.json(); }).then(function (d) {
    if (!d.configured || !d.key) {
      document.getElementById('e2e-key-empty').style.display = '';
      return;
    }
    _e2eKeyValue = d.key;
    document.getElementById('e2e-key-body').style.display = '';
    _e2eKeyRender();
  }).catch(function () {
    document.getElementById('e2e-key-empty').style.display = '';
  });
}
function closeE2eKeyModal() {
  var overlay = document.getElementById('e2e-key-modal-overlay');
  if (overlay) overlay.style.display = 'none';
}
function _e2eKeyMask(k) {
  if (!k || k.length < 10) return '••••••••';
  return k.slice(0, 6) + '…' + k.slice(-4);
}
function _e2eKeyRender() {
  var el = document.getElementById('e2e-key-value');
  if (!el) return;
  el.textContent = _e2eKeyRevealed ? _e2eKeyValue : _e2eKeyMask(_e2eKeyValue);
}
function e2eKeyToggleReveal() {
  _e2eKeyRevealed = !_e2eKeyRevealed;
  _e2eKeyRender();
}
function e2eKeyCopy() {
  if (!_e2eKeyValue) return;
  var done = function () {
    var msg = document.getElementById('e2e-key-copied');
    if (msg) { msg.style.display = ''; setTimeout(function () { msg.style.display = 'none'; }, 2000); }
  };
  try {
    navigator.clipboard.writeText(_e2eKeyValue).then(done);
  } catch (e) {
    var el = document.getElementById('e2e-key-value');
    var wasRevealed = _e2eKeyRevealed;
    _e2eKeyRevealed = true; _e2eKeyRender();
    var r = document.createRange(); r.selectNode(el);
    var sel = window.getSelection(); sel.removeAllRanges(); sel.addRange(r);
    try { document.execCommand('copy'); done(); } catch (e2) {}
    sel.removeAllRanges();
    _e2eKeyRevealed = wasRevealed; _e2eKeyRender();
  }
}
function e2eKeyRegenerate() {
  var btn = document.querySelector('#e2e-key-regen-confirm button');
  var errEl = document.getElementById('e2e-key-error');
  errEl.style.display = 'none';
  if (btn) { btn.disabled = true; btn.textContent = '…'; }
  fetch('/api/local/e2e-key/regenerate', { method: 'POST' }).then(function (r) {
    return r.json().then(function (d) { return { ok: r.ok, body: d }; });
  }).then(function (res) {
    if (!res.ok || !res.body.key) {
      errEl.textContent = (res.body && res.body.error) || 'Could not regenerate the key. Try again.';
      errEl.style.display = '';
      if (btn) { btn.disabled = false; btn.textContent = t('e2e_key.regen_yes', null, 'Yes, regenerate'); }
      return;
    }
    _e2eKeyValue = res.body.key;
    _e2eKeyRevealed = true;
    _e2eKeyRender();
    document.getElementById('e2e-key-regen-confirm').style.display = 'none';
    document.getElementById('e2e-key-regen-btn').style.display = '';
  }).catch(function () {
    errEl.textContent = 'Network error. Try again.';
    errEl.style.display = '';
    if (btn) { btn.disabled = false; btn.textContent = t('e2e_key.regen_yes', null, 'Yes, regenerate'); }
  });
}

function _updateCloudStatus() {
  fetch('/api/cloud-cta/status').then(function(r){ return r.json(); }).then(function(d){
    var cta = document.getElementById('cloud-cta-btn');
    var badge = document.getElementById('cloud-connected-badge');
    if (d.connected) {
      cta.style.display = 'none';
      badge.style.display = '';
    } else if (d.local_only && d.account_linked) {
      // Signed-in Self-Hosted: honest amber "Local-only" — NOT the green
      // cloud badge, and no click-through to app.clawmetry.com (founder
      // report 2026-07-30: the node syncs nothing by choice).
      cta.style.display = 'none';
      badge.style.display = '';
      badge.innerHTML = '&#9679; Local-only';
      badge.style.color = '#f59e0b';
      badge.style.borderColor = 'rgba(245,158,11,0.4)';
      badge.title = 'Signed in; your data stays on this machine. Enable cloud sync: clawmetry connect';
      badge.onclick = null;
      badge.style.cursor = 'default';
    } else {
      cta.style.display = '';
      badge.style.display = 'none';
    }
  }).catch(function(){
    document.getElementById('cloud-cta-btn').style.display = '';
    document.getElementById('cloud-connected-badge').style.display = 'none';
  });
}
_updateCloudStatus();

// ── Account menu (top-right avatar) ─────────────────────────────────────────
// Self-hosted requires sign-in now, so the header gets the same profile
// affordance as app.clawmetry.com: who you are, plan state, billing/account
// management, and sign-out. Identity comes from the trial/paid license
// (/api/license/status: sub + tier + days_left) — the only identity a
// local-only node has; /api/cloud-cta/status distinguishes signed-out.
var _cmProfile = { state: null };

function _cmProfileEsc(s) {
  return String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function _cmProfileFetchState() {
  return Promise.all([
    fetch('/api/license/status').then(function (r) { return r.ok ? r.json() : null; }).catch(function () { return null; }),
    fetch('/api/cloud-cta/status').then(function (r) { return r.ok ? r.json() : null; }).catch(function () { return null; })
  ]).then(function (res) {
    var lic = res[0] || {};
    var cta = res[1] || {};
    var signedIn = !!(lic.valid || cta.account_linked);
    _cmProfile.state = {
      signedIn: signedIn,
      // license `sub` is the account the key was issued to (the sign-in
      // email); a cloud-OAuth account with no local license has no sub, so
      // fall back to the cloud account email resolved by the backend.
      who: lic.sub || cta.account_email || '',
      tier: (lic.tier || '').toLowerCase(),
      daysLeft: (typeof lic.days_left === 'number') ? lic.days_left : null,
      licenseValid: !!lic.valid,
      // Cloud links (billing/settings on app.clawmetry.com) only make sense
      // when this node is actually linked to a cloud account — a license-only
      // self-hosted install has no account there to manage.
      accountLinked: !!cta.account_linked
    };
    return _cmProfile.state;
  });
}

function _cmProfileApplyAvatar(st) {
  var btn = document.getElementById('cm-profile-btn');
  var initial = document.getElementById('cm-profile-initial');
  if (!btn || !initial) return;
  if (st.signedIn) {
    btn.dataset.signedIn = '1';
    initial.textContent = st.who ? st.who.charAt(0).toUpperCase() : '';
    btn.title = st.who || t('profile.signed_in', null, 'Signed in');
  } else {
    delete btn.dataset.signedIn;
    btn.title = t('profile.account', null, 'Account');
  }
}

function _cmProfilePlanLine(st) {
  if (!st.licenseValid) return '';
  if (st.tier === 'trial') {
    var d = (st.daysLeft == null) ? '?' : st.daysLeft;
    return t('profile.trial_days_left', { days: d }, 'Trial · ' + d + ' days left');
  }
  var label = st.tier ? st.tier.charAt(0).toUpperCase() + st.tier.slice(1) : '';
  return t('profile.plan', { tier: label }, label + ' plan');
}

function _cmProfileRender(st) {
  var menu = document.getElementById('cm-profile-menu');
  if (!menu) return;
  var h = '';
  // Identity header
  h += '<div style="padding:10px 10px 8px;border-bottom:1px solid var(--border-color,rgba(255,255,255,0.08));margin-bottom:4px;">';
  if (st.signedIn) {
    // Signed in but the email is unresolvable (offline, pre-claim account):
    // still say "Signed in" — a signed-in menu that opens with "Not signed
    // in" above Billing/Sign out is a contradiction (founder report
    // 2026-08-09, GitHub-OAuth node with no local license).
    var whoLine = st.who ? _cmProfileEsc(st.who) : t('profile.signed_in', null, 'Signed in');
    h += '<div style="font-size:13px;font-weight:700;color:var(--text-primary,#e2e8f0);word-break:break-all;">' + whoLine + '</div>';
    var plan = _cmProfilePlanLine(st);
    if (plan) h += '<div style="font-size:11px;color:var(--text-muted,#94a3b8);margin-top:2px;">' + _cmProfileEsc(plan) + '</div>';
  } else {
    h += '<div style="font-size:13px;font-weight:700;color:var(--text-primary,#e2e8f0);" data-i18n="profile.not_signed_in">' + t('profile.not_signed_in', null, 'Not signed in') + '</div>';
  }
  h += '</div>';
  if (st.signedIn) {
    // "Billing & plan" lives on app.clawmetry.com, so it is only offered when
    // a cloud account is actually linked; a license-only self-hosted node has
    // nothing to manage there (founder report 2026-08-04).
    if (st.accountLinked) {
      h += '<button class="cm-profile-item" onclick="cmProfileClose();window.open(\'https://app.clawmetry.com/settings?utm_source=oss-dashboard&utm_medium=profile-menu\',\'_blank\')">'
        + '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="1" y="4" width="22" height="16" rx="2"/><line x1="1" y1="10" x2="23" y2="10"/></svg>'
        + t('profile.billing', null, 'Billing & plan') + '</button>';
    }
    if (st.tier === 'trial') {
      // Self-hosted upgrades are sold on clawmetry.com/pricing (?deploy=self
      // preselects the self-hosted buy modal). The /upgrade route on the
      // cloud app is the CLOUD-account funnel — for a self-hosted trial it
      // either bounces through a login wall or silently starts a cloud trial.
      h += '<button class="cm-profile-item" onclick="cmProfileClose();window.open(\'https://clawmetry.com/pricing?deploy=self&utm_source=oss-dashboard&utm_medium=profile-menu\',\'_blank\')">'
        + '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="17 11 12 6 7 11"/><polyline points="17 18 12 13 7 18"/></svg>'
        + t('profile.upgrade', null, 'Upgrade plan') + '</button>';
    }
    // Local-only surface: reveal/regenerate the E2E key used to decrypt
    // cloud-synced data in the browser. Never rendered on the hosted cloud
    // dashboard (this whole menu only exists in the OSS local dashboard),
    // and the modal itself falls back to an "enable cloud sync" prompt when
    // no key is configured yet, so it is safe to always offer here.
    h += '<button class="cm-profile-item" onclick="cmProfileClose();openE2eKeyModal()">'
      + '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>'
      + t('profile.e2e_key', null, 'Cloud sync key') + '</button>';
  } else {
    h += '<button class="cm-profile-item" onclick="cmProfileClose();if(typeof openCloudModal===\'function\')openCloudModal(\'signin\')">'
      + '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"/><polyline points="10 17 15 12 10 7"/><line x1="15" y1="12" x2="3" y2="12"/></svg>'
      + t('profile.sign_in', null, 'Sign in / Create account') + '</button>';
  }
  // No "Gateway settings" item: the gw-setup overlay is a first-run wizard
  // for the OpenClaw gateway token, not an ongoing settings surface — it
  // auto-opens whenever the gateway is unconfigured, which is the only time
  // it has anything to offer (founder call 2026-08-04, removed everywhere).
  // Sign out clears this browser's dashboard session (the gateway token in
  // localStorage) — mirror the #logout-btn visibility contract set by
  // auth-bootstrap.js: only shown when token auth is actually active.
  var lb = document.getElementById('logout-btn');
  if (lb && lb.style.display !== 'none') {
    h += '<div style="border-top:1px solid var(--border-color,rgba(255,255,255,0.08));margin:4px 0;"></div>';
    h += '<button class="cm-profile-item cm-profile-danger" onclick="cmProfileClose();clawmetryLogout()">'
      + '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>'
      + t('profile.sign_out', null, 'Sign out') + '</button>';
  }
  menu.innerHTML = h;
}

function cmProfileClose() {
  var menu = document.getElementById('cm-profile-menu');
  var btn = document.getElementById('cm-profile-btn');
  if (menu) menu.style.display = 'none';
  if (btn) btn.setAttribute('aria-expanded', 'false');
}

function cmProfileToggle(e) {
  if (e) e.stopPropagation();
  var menu = document.getElementById('cm-profile-menu');
  var btn = document.getElementById('cm-profile-btn');
  if (!menu) return;
  if (menu.style.display !== 'none') { cmProfileClose(); return; }
  // Open immediately with the cached (or empty) state, then re-fetch so
  // plan/days-left/sign-in state is never stale.
  var open = function (st) { _cmProfileApplyAvatar(st); _cmProfileRender(st); menu.style.display = 'block'; if (btn) btn.setAttribute('aria-expanded', 'true'); };
  open(_cmProfile.state || { signedIn: false, who: '', tier: '', daysLeft: null, licenseValid: false });
  _cmProfileFetchState().then(function (st) {
    if (menu.style.display !== 'none') open(st);
  });
}

function cmProfileInit() {
  if (!document.getElementById('cm-profile-btn')) return;
  _cmProfileFetchState().then(_cmProfileApplyAvatar);
  document.addEventListener('click', function (ev) {
    if (!ev.target.closest || !ev.target.closest('#cm-profile-wrap')) cmProfileClose();
  });
  document.addEventListener('keydown', function (ev) {
    if (ev.key === 'Escape') cmProfileClose();
  });
}
cmProfileInit();
