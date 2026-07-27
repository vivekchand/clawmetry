// Gateway setup wizard
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
      if (td.ok) { updateGwStatus(true, td.url); }
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
      // Check localStorage first
      const saved = localStorage.getItem('clawmetry-gw-token');
      if (saved) {
        // Try auto-connecting with saved token
        const r2 = await fetch('/api/gw/config', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({token: saved})
        });
        const d2 = await r2.json();
        if (d2.ok) { updateGwStatus(true, d2.url); return; }
      }
      // Bug #1127: don't z-stack the gw-setup overlay on top of an already-
      // open cloud modal — the two share the same backdrop and confuse the
      // user. Defer until the cloud modal closes.
      if (_isCloudModalOpen()) return;
      await _gwApplyRuntimeDetection();
      document.getElementById('gw-setup-overlay').style.display = 'flex';
    } else {
      updateGwStatus(true, d.url);
    }
  } catch(e) {}
}

// ── Runtime-aware setup ────────────────────────────────────────────────
// ClawMetry watches 14 runtimes but this wizard used to demand an OpenClaw
// gateway token unconditionally. On a machine running only Claude Code that
// is a dead end: the user has no gateway, no token, and no way past the
// modal. Worse on Windows, where the "how to find your token" hint printed a
// POSIX pipeline that cannot run there. Detection now decides what this step
// asks for. The backend already existed at
// /api/entitlement/runtime-detection; nothing was consuming it.

function _gwIsWindows() {
  try {
    var p = (navigator.userAgentData && navigator.userAgentData.platform) || navigator.platform || '';
    if (/win/i.test(p)) return true;
    return /Windows/i.test(navigator.userAgent || '');
  } catch (e) { return false; }
}

function gwShowOpenClawBlock() {
  var b = document.getElementById('gw-openclaw-block');
  var t = document.getElementById('gw-openclaw-toggle');
  if (b) b.style.display = '';
  if (t) t.style.display = 'none';
}

function _gwRuntimeRow(p) {
  var badge = !p.allowed
    ? '<span style="font-size:10px; padding:2px 7px; border-radius:99px; background:rgba(255,180,0,0.14); color:#ffb400; white-space:nowrap;">needs ' + (p.required_tier_label || 'an upgrade') + '</span>'
    : '<span style="font-size:10px; padding:2px 7px; border-radius:99px; background:rgba(74,222,128,0.14); color:#4ade80; white-space:nowrap;">watching</span>';
  return '' +
    '<div style="display:flex; align-items:center; justify-content:space-between; gap:12px; padding:9px 12px; margin-bottom:6px; border:1px solid var(--border-primary,#333); border-radius:8px; background:var(--bg-primary,#111);">' +
      '<span style="display:flex; align-items:center; gap:8px; min-width:0;">' +
        '<span style="color:#4ade80; font-size:13px;">&#10003;</span>' +
        '<span style="color:var(--text-primary,#fff); font-size:13px; font-weight:600; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">' + (p.label || p.id) + '</span>' +
      '</span>' + badge +
    '</div>';
}

async function _gwApplyRuntimeDetection() {
  var sub = document.getElementById('gw-setup-sub');
  var block = document.getElementById('gw-detected-block');
  var list = document.getElementById('gw-detected-list');
  var cta = document.getElementById('gw-detected-cta');
  var ocBlock = document.getElementById('gw-openclaw-block');
  var ocToggle = document.getElementById('gw-openclaw-toggle');
  var overlay = document.getElementById('gw-setup-overlay');
  var closeBtn = document.getElementById('gw-setup-close');

  // Windows has no `cat`, so swap the token hint for a PowerShell one.
  if (_gwIsWindows()) {
    var hint = document.getElementById('gw-hint-local');
    if (hint) {
      hint.textContent =
        '(Get-Content ~/.openclaw/openclaw.json | ConvertFrom-Json).gateway.auth.token';
    }
  }

  var det = null;
  try {
    var r = await fetch('/api/entitlement/runtime-detection');
    det = await r.json();
  } catch (e) { return; }
  if (!det || !det.probes) return;

  var found = det.probes.filter(function (p) { return p.found; });
  var selfHosted = det.probes.filter(function (p) {
    return (p.id === 'openclaw' || p.id === 'nemoclaw') && p.found;
  });

  // OpenClaw is here: the token step is the right ask, so keep it as-is.
  if (selfHosted.length) return;

  // No OpenClaw on this machine. The token form must not be the mandatory
  // first step, and the modal must be dismissible.
  if (ocBlock) ocBlock.style.display = 'none';
  if (ocToggle) ocToggle.style.display = '';
  if (overlay) overlay.dataset.mandatory = 'false';
  if (closeBtn) closeBtn.style.display = '';

  if (!found.length) {
    // Nothing detected. Stay runtime neutral rather than naming one runtime
    // the user may never have heard of.
    if (sub) sub.textContent = 'No AI agent runtimes found on this machine yet. Start one and ClawMetry picks it up automatically.';
    return;
  }

  var names = found.map(function (p) { return p.label; });
  if (sub) {
    sub.textContent = names.length === 1
      ? 'ClawMetry found ' + names[0] + ' on this machine.'
      : 'ClawMetry found ' + names.length + ' agent runtimes on this machine.';
  }
  if (list) list.innerHTML = found.map(_gwRuntimeRow).join('');
  if (block) block.style.display = '';

  var locked = found.filter(function (p) { return !p.allowed; });
  if (cta) {
    if (locked.length) {
      var tier = det.actionable_tier_label || 'Starter';
      cta.innerHTML =
        '<p style="color:var(--text-muted,#888); font-size:12px; margin:0 0 10px; text-align:left; line-height:1.5;">' +
          'Watching ' + locked.map(function (p) { return p.label; }).join(', ') +
          ' is part of ' + tier + '. Start a free trial to turn it on now.' +
        '</p>' +
        '<button id="gw-trial-btn" onclick="gwStartTrial()" style="width:100%; padding:12px; border:none; border-radius:8px; background:var(--bg-accent,#0f6fff); color:#fff; font-size:15px; font-weight:600; cursor:pointer; font-family:Manrope,sans-serif;">Start free trial</button>';
    } else {
      cta.innerHTML =
        '<p style="color:var(--text-muted,#888); font-size:12px; margin:0; text-align:left;">' +
          'These are watched on your current plan. Data appears as your agents run.' +
        '</p>';
    }
  }
}

// ── Local trial activation ─────────────────────────────────────────────
// Email + OTP, then everything continues locally: the cloud mints a signed
// 7-day trial key, /api/trial/activate writes it to this install, and the
// entitlement flips without the user ever leaving this dashboard. Uses the
// existing /api/cloud-cta/send-otp proxy for the code email. Google/GitHub
// sign-in stays available via the existing cloud modal (accounts are
// trial-by-default there, so that path unlocks too).

function _gwTrialErr(msg) {
  var e = document.getElementById('gw-trial-error');
  if (e) { e.textContent = msg || ''; e.style.display = msg ? '' : 'none'; }
}

function gwStartTrial() {
  var cta = document.getElementById('gw-detected-cta');
  if (!cta) return;
  cta.innerHTML =
    '<div style="text-align:left;">' +
      '<p style="color:var(--text-muted,#888); font-size:12px; margin:0 0 8px; line-height:1.5;">' +
        'Enter your email to start your 7-day free trial. Your data stays on this machine.' +
      '</p>' +
      '<input id="gw-trial-email" type="email" placeholder="you@company.com" ' +
        'style="width:100%; padding:10px 12px; border:1px solid var(--border-primary,#444); border-radius:8px; background:var(--bg-primary,#111); color:var(--text-primary,#fff); font-size:13px; box-sizing:border-box; outline:none; margin-bottom:8px;" ' +
        'onkeydown="if(event.key===\'Enter\')gwTrialSendCode()">' +
      '<div id="gw-trial-error" style="display:none; color:#ff4444; font-size:12px; margin-bottom:8px;"></div>' +
      '<button id="gw-trial-send-btn" onclick="gwTrialSendCode()" style="width:100%; padding:11px; border:none; border-radius:8px; background:var(--bg-accent,#0f6fff); color:#fff; font-size:14px; font-weight:600; cursor:pointer; font-family:Manrope,sans-serif;">Email me a code</button>' +
      '<p style="color:var(--text-faint,#555); font-size:11px; margin:10px 0 0; text-align:center;">' +
        'Prefer <a href="#" onclick="if(typeof openCloudModal===\'function\'){document.getElementById(\'gw-setup-overlay\').style.display=\'none\';openCloudModal();}return false;" style="color:var(--text-muted,#888);">Google or GitHub sign-in</a>?' +
      '</p>' +
    '</div>';
  setTimeout(function () { var el = document.getElementById('gw-trial-email'); if (el) el.focus(); }, 50);
}

var _gwTrialEmail = '';
function gwTrialSendCode() {
  var emailEl = document.getElementById('gw-trial-email');
  var email = (emailEl && emailEl.value || '').trim();
  if (!email || email.indexOf('@') < 0) { _gwTrialErr('Enter a valid email.'); return; }
  _gwTrialErr('');
  _gwTrialEmail = email;
  var btn = document.getElementById('gw-trial-send-btn');
  if (btn) { btn.textContent = 'Sending code'; btn.disabled = true; }
  fetch('/api/cloud-cta/send-otp', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email: email }),
  }).then(function (r) { return r.json(); }).then(function (d) {
    if (d.ok === false) {
      _gwTrialErr(d.error || 'Could not send the code. Try again.');
      if (btn) { btn.textContent = 'Email me a code'; btn.disabled = false; }
      return;
    }
    _gwTrialCodeStep();
  }).catch(function () {
    _gwTrialErr('Network error. Try again.');
    if (btn) { btn.textContent = 'Email me a code'; btn.disabled = false; }
  });
}

function _gwTrialCodeStep() {
  var cta = document.getElementById('gw-detected-cta');
  if (!cta) return;
  cta.innerHTML =
    '<div style="text-align:left;">' +
      '<p style="color:var(--text-muted,#888); font-size:12px; margin:0 0 8px; line-height:1.5;">' +
        'We emailed a 6-digit code to <span style="color:var(--text-primary,#fff);">' + _gwTrialEmail + '</span>.' +
      '</p>' +
      '<input id="gw-trial-code" type="text" inputmode="numeric" maxlength="6" placeholder="123456" ' +
        'style="width:100%; padding:10px 12px; border:1px solid var(--border-primary,#444); border-radius:8px; background:var(--bg-primary,#111); color:var(--text-primary,#fff); font-size:16px; letter-spacing:6px; text-align:center; font-family:monospace; box-sizing:border-box; outline:none; margin-bottom:8px;" ' +
        'onkeydown="if(event.key===\'Enter\')gwTrialActivate()">' +
      '<div id="gw-trial-error" style="display:none; color:#ff4444; font-size:12px; margin-bottom:8px;"></div>' +
      '<button id="gw-trial-activate-btn" onclick="gwTrialActivate()" style="width:100%; padding:11px; border:none; border-radius:8px; background:var(--bg-accent,#0f6fff); color:#fff; font-size:14px; font-weight:600; cursor:pointer; font-family:Manrope,sans-serif;">Activate trial</button>' +
      '<p style="color:var(--text-faint,#555); font-size:11px; margin:8px 0 0; text-align:center;">' +
        '<a href="#" onclick="gwStartTrial();return false;" style="color:var(--text-muted,#888);">Use a different email</a>' +
      '</p>' +
    '</div>';
  setTimeout(function () { var el = document.getElementById('gw-trial-code'); if (el) el.focus(); }, 50);
}

function gwTrialActivate() {
  var codeEl = document.getElementById('gw-trial-code');
  var code = (codeEl && codeEl.value || '').replace(/\s/g, '');
  if (code.length !== 6) { _gwTrialErr('Enter the 6-digit code from your email.'); return; }
  _gwTrialErr('');
  var btn = document.getElementById('gw-trial-activate-btn');
  if (btn) { btn.textContent = 'Activating'; btn.disabled = true; }
  fetch('/api/trial/activate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email: _gwTrialEmail, code: code }),
  }).then(function (r) { return r.json(); }).then(function (d) {
    if (!d.ok) {
      _gwTrialErr(d.error || 'Activation failed. Try again.');
      if (btn) { btn.textContent = 'Activate trial'; btn.disabled = false; }
      return;
    }
    var cta = document.getElementById('gw-detected-cta');
    if (cta) {
      cta.innerHTML =
        '<p style="color:#4ade80; font-size:13px; font-weight:600; margin:0 0 4px; text-align:center;">Trial active</p>' +
        '<p style="color:var(--text-muted,#888); font-size:12px; margin:0; text-align:center;">Your agent runtimes are now being watched. Reloading&hellip;</p>';
    }
    setTimeout(function () { location.reload(); }, 1200);
  }).catch(function () {
    _gwTrialErr('Network error. Try again.');
    if (btn) { btn.textContent = 'Activate trial'; btn.disabled = false; }
  });
}

function _isCloudModalOpen() {
  var cm = document.getElementById('cloud-modal-overlay');
  if (cm && cm.style.display && cm.style.display !== 'none') return true;
  // Defensive: also honour a generic .cloud-modal.active marker if present.
  if (document.querySelector && document.querySelector('.cloud-modal.active')) return true;
  return false;
}

function updateGwStatus(connected, url) {
  const dot = document.getElementById('gw-status-dot');
  if (!dot) return;
  dot.style.color = connected ? '#4ade80' : '#f87171';
  dot.title = connected ? 'Gateway: connected' + (url ? ' (' + url + ')' : '') : 'Gateway: disconnected';
}

async function gwSetupConnect() {
  const btn = document.getElementById('gw-connect-btn');
  const errEl = document.getElementById('gw-setup-error');
  const statusEl = document.getElementById('gw-setup-status');
  const token = document.getElementById('gw-token-input').value.trim();
  const url = document.getElementById('gw-url-input').value.trim();
  
  errEl.style.display = 'none';
  if (!token) { errEl.textContent = 'Please enter a token'; errEl.style.display = 'block'; return; }
  
  btn.textContent = 'Scanning for gateway...';
  btn.disabled = true;
  statusEl.textContent = 'Scanning ports to find your OpenClaw gateway...';
  statusEl.style.display = 'block';
  
  try {
    const r = await fetch('/api/gw/config', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({token, url})
    });
    const d = await r.json();
    if (d.ok) {
      statusEl.textContent = 'Connected to ' + d.url;
      btn.textContent = 'Connected!';
      localStorage.setItem('clawmetry-gw-token', token);
      localStorage.setItem('clawmetry-token', token);
      updateGwStatus(true, d.url);
      setTimeout(() => {
        document.getElementById('gw-setup-overlay').style.display = 'none';
        location.reload();
      }, 800);
    } else {
      errEl.textContent = d.error || 'Connection failed';
      errEl.style.display = 'block';
      btn.textContent = 'Connect';
      btn.disabled = false;
      statusEl.style.display = 'none';
    }
  } catch(e) {
    errEl.textContent = 'Network error: ' + e.message;
    errEl.style.display = 'block';
    btn.textContent = 'Connect';
    btn.disabled = false;
    statusEl.style.display = 'none';
  }
}

// Check on load
document.addEventListener('DOMContentLoaded', checkGwConfig);

// ClawMetry Cloud CTA
var _cloudEmail = '';
function openCloudModal() {
  // Bug #1127: suppress the gateway-setup overlay so the user doesn't see two
  // stacked modals (cloud CTA on top, gw-setup peeking behind it).
  var gw = document.getElementById('gw-setup-overlay');
  if (gw && gw.dataset.mandatory !== 'true') gw.style.display = 'none';
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
  fetch('/api/cloud-cta/oauth-start', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({provider: provider})})
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
  fetch('https://app.clawmetry.com/api/otp/verify', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({email: _cloudEmail, code: code})})
    .then(function(r){ return r.json(); })
    .then(function(d){
      if (d.ok && (d.token || d.api_key)) {
        document.getElementById('cloud-step-otp').style.display = 'none';
        document.getElementById('cloud-step-done').style.display = '';
        setTimeout(function(){ window.open('https://app.clawmetry.com/auth?token=' + encodeURIComponent(d.token || d.api_key), '_blank'); closeCloudModal(); _updateCloudStatus(); }, 1800);
      } else {
        var err = document.getElementById('cloud-otp-error');
        err.textContent = d.error || 'Invalid code. Try again.';
        err.style.display = '';
      }
    })
    .catch(function(){ var err = document.getElementById('cloud-otp-error'); err.textContent = 'Network error. Try again.'; err.style.display = ''; });
}
function _updateCloudStatus() {
  fetch('/api/cloud-cta/status').then(function(r){ return r.json(); }).then(function(d){
    document.getElementById('cloud-cta-btn').style.display = d.connected ? 'none' : '';
    document.getElementById('cloud-connected-badge').style.display = d.connected ? '' : 'none';
  }).catch(function(){
    document.getElementById('cloud-cta-btn').style.display = '';
    document.getElementById('cloud-connected-badge').style.display = 'none';
  });
}
_updateCloudStatus();
