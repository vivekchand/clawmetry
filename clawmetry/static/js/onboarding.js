// onboarding.js — first-run onboarding gate (hard gate, no skip).
//
// Shows templates/partials/onboarding-modal.html when
// GET /api/onboarding/state says {required:true}. Three ways out, each
// recorded via POST /api/onboarding/complete (or the combined
// activate-license endpoint):
//   managed          — existing cloud modal (OTP / Google / GitHub), we
//                      poll /api/cloud-cta/status until connected
//   selfhost_trial   — email + 6-digit code, the flow /api/trial/activate
//                      already implements (same as the gw-setup teaser)
//   selfhost_license — CLAW1 key via /api/onboarding/activate-license
//
// Never runs on the hosted cloud dashboard (window.CLOUD_MODE) and defers
// to the mandatory gateway-setup overlay when that is on screen.

(function () {
  'use strict';

  var _pollTimer = null;
  var _trialEmail = '';

  function $(id) { return document.getElementById(id); }

  function _overlay() { return $('onboarding-gate-overlay'); }

  function _show() {
    var o = _overlay();
    if (o) o.style.display = 'flex';
  }

  function _hide() {
    var o = _overlay();
    if (o) o.style.display = 'none';
    if (_pollTimer) { clearInterval(_pollTimer); _pollTimer = null; }
  }

  function _err(id, msg) {
    var e = $(id);
    if (e) { e.textContent = msg || ''; e.style.display = msg ? 'block' : 'none'; }
  }

  function _gwSetupMandatoryVisible() {
    var gw = $('gw-setup-overlay');
    return !!(gw && gw.style.display && gw.style.display !== 'none'
      && gw.dataset && gw.dataset.mandatory === 'true');
  }

  function _complete(choice, onFail) {
    fetch('/api/onboarding/complete', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ choice: choice }),
    }).then(function (r) { return r.json(); }).then(function (d) {
      if (d && d.ok) {
        _hide();
        location.reload();
      } else if (onFail) {
        onFail((d && d.error) || 'Could not save your choice. Try again.');
      }
    }).catch(function () {
      if (onFail) onFail('Network error. Try again.');
    });
  }

  // ── Managed cloud branch ─────────────────────────────────────────────
  function _startManaged() {
    _err('obg-managed-err', '');
    if (typeof openCloudModal !== 'function') {
      _err('obg-managed-err', 'Cloud sign-in is unavailable in this build.');
      return;
    }
    openCloudModal();
    if (_pollTimer) clearInterval(_pollTimer);
    _pollTimer = setInterval(function () {
      fetch('/api/cloud-cta/status').then(function (r) { return r.json(); })
        .then(function (d) {
          if (d && d.connected) {
            clearInterval(_pollTimer); _pollTimer = null;
            _complete('managed', function (msg) { _err('obg-managed-err', msg); });
          }
        }).catch(function () {});
    }, 2000);
  }

  // ── Self-host: free trial (email → code → activate) ─────────────────
  function _trialEmailStep() {
    var body = $('obg-selfhost-body');
    if (!body) return;
    body.innerHTML =
      '<input class="obg-input" id="obg-trial-email" type="email" placeholder="you@company.com" autocomplete="email">' +
      '<div class="obg-err" id="obg-trial-err"></div>' +
      '<button class="obg-btn obg-btn-quiet" id="obg-trial-send" type="button">Email me a code</button>' +
      '<a class="obg-alt" href="#" id="obg-trial-back">Back</a>';
    $('obg-trial-send').addEventListener('click', _trialSendCode);
    $('obg-trial-email').addEventListener('keydown', function (ev) {
      if (ev.key === 'Enter') _trialSendCode();
    });
    $('obg-trial-back').addEventListener('click', function (ev) {
      ev.preventDefault(); _selfhostHome();
    });
    setTimeout(function () { var el = $('obg-trial-email'); if (el) el.focus(); }, 50);
  }

  function _trialSendCode() {
    var email = (($('obg-trial-email') || {}).value || '').trim();
    if (!email || email.indexOf('@') < 0) {
      _err('obg-trial-err', 'Enter a valid email.');
      return;
    }
    _trialEmail = email;
    _err('obg-trial-err', '');
    var btn = $('obg-trial-send');
    if (btn) { btn.textContent = 'Sending code'; btn.disabled = true; }
    fetch('/api/cloud-cta/send-otp', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: email }),
    }).then(function (r) { return r.json(); }).then(function (d) {
      if (d && d.ok === false) {
        _err('obg-trial-err', d.error || 'Could not send the code. Try again.');
        if (btn) { btn.textContent = 'Email me a code'; btn.disabled = false; }
        return;
      }
      _trialCodeStep();
    }).catch(function () {
      _err('obg-trial-err', 'Network error. Try again.');
      if (btn) { btn.textContent = 'Email me a code'; btn.disabled = false; }
    });
  }

  function _trialCodeStep() {
    var body = $('obg-selfhost-body');
    if (!body) return;
    body.innerHTML =
      '<p style="color:#94a3b8;font-size:12px;margin:0 0 8px;">We emailed a 6-digit code to <b style="color:#e2e8f0;">' +
        _trialEmail.replace(/&/g, '&amp;').replace(/</g, '&lt;') + '</b>.</p>' +
      '<input class="obg-input" id="obg-trial-code" type="text" inputmode="numeric" maxlength="6" placeholder="123456" style="letter-spacing:6px;text-align:center;font-family:monospace;font-size:16px;">' +
      '<div class="obg-err" id="obg-trial-err"></div>' +
      '<button class="obg-btn obg-btn-quiet" id="obg-trial-activate" type="button">Activate trial</button>' +
      '<a class="obg-alt" href="#" id="obg-trial-redo">Use a different email</a>';
    $('obg-trial-activate').addEventListener('click', _trialActivate);
    $('obg-trial-code').addEventListener('keydown', function (ev) {
      if (ev.key === 'Enter') _trialActivate();
    });
    $('obg-trial-redo').addEventListener('click', function (ev) {
      ev.preventDefault(); _trialEmailStep();
    });
    setTimeout(function () { var el = $('obg-trial-code'); if (el) el.focus(); }, 50);
  }

  function _trialActivate() {
    var code = ((($('obg-trial-code') || {}).value) || '').replace(/\s/g, '');
    if (code.length !== 6) {
      _err('obg-trial-err', 'Enter the 6-digit code from your email.');
      return;
    }
    _err('obg-trial-err', '');
    var btn = $('obg-trial-activate');
    if (btn) { btn.textContent = 'Activating'; btn.disabled = true; }
    fetch('/api/trial/activate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: _trialEmail, code: code }),
    }).then(function (r) { return r.json(); }).then(function (d) {
      if (!d || !d.ok) {
        _err('obg-trial-err', (d && d.error) || 'Activation failed. Try again.');
        if (btn) { btn.textContent = 'Activate trial'; btn.disabled = false; }
        return;
      }
      _complete('selfhost_trial', function (msg) {
        _err('obg-trial-err', msg);
        if (btn) { btn.textContent = 'Activate trial'; btn.disabled = false; }
      });
    }).catch(function () {
      _err('obg-trial-err', 'Network error. Try again.');
      if (btn) { btn.textContent = 'Activate trial'; btn.disabled = false; }
    });
  }

  // ── Self-host: license key ───────────────────────────────────────────
  function _licenseStep() {
    var body = $('obg-selfhost-body');
    if (!body) return;
    body.innerHTML =
      '<input class="obg-input" id="obg-license-key" type="text" placeholder="CLAW1.xxxx.xxxx" autocomplete="off" spellcheck="false">' +
      '<div class="obg-err" id="obg-license-err"></div>' +
      '<button class="obg-btn obg-btn-quiet" id="obg-license-activate" type="button">Activate license</button>' +
      '<a class="obg-alt" href="#" id="obg-license-back">Back</a>';
    $('obg-license-activate').addEventListener('click', _licenseActivate);
    $('obg-license-key').addEventListener('keydown', function (ev) {
      if (ev.key === 'Enter') _licenseActivate();
    });
    $('obg-license-back').addEventListener('click', function (ev) {
      ev.preventDefault(); _selfhostHome();
    });
    setTimeout(function () { var el = $('obg-license-key'); if (el) el.focus(); }, 50);
  }

  function _licenseActivate() {
    var key = ((($('obg-license-key') || {}).value) || '').trim();
    if (!key) { _err('obg-license-err', 'Paste your license key.'); return; }
    _err('obg-license-err', '');
    var btn = $('obg-license-activate');
    if (btn) { btn.textContent = 'Activating'; btn.disabled = true; }
    fetch('/api/onboarding/activate-license', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ key: key }),
    }).then(function (r) { return r.json(); }).then(function (d) {
      if (!d || !d.ok) {
        _err('obg-license-err', (d && d.error) || 'Activation failed. Try again.');
        if (btn) { btn.textContent = 'Activate license'; btn.disabled = false; }
        return;
      }
      _hide();
      location.reload();
    }).catch(function () {
      _err('obg-license-err', 'Network error. Try again.');
      if (btn) { btn.textContent = 'Activate license'; btn.disabled = false; }
    });
  }

  function _selfhostHome() {
    var body = $('obg-selfhost-body');
    if (!body) return;
    body.innerHTML =
      '<button class="obg-btn obg-btn-quiet" id="obg-trial-btn" type="button">Start free 7-day trial</button>' +
      '<a class="obg-alt" href="#" id="obg-license-link">I have a license key</a>';
    _wireSelfhostHome();
  }

  function _wireSelfhostHome() {
    var t = $('obg-trial-btn');
    if (t) t.addEventListener('click', _trialEmailStep);
    var l = $('obg-license-link');
    if (l) l.addEventListener('click', function (ev) { ev.preventDefault(); _licenseStep(); });
  }

  // ── Greeting: lead with what ClawMetry can already see ───────────────
  function _fillDetection() {
    fetch('/api/entitlement/runtime-detection')
      .then(function (r) { return r.json(); })
      .then(function (d) {
        var found = ((d && d.probes) || []).filter(function (p) { return p.found; });
        if (!found.length) return;
        var names = found.slice(0, 3).map(function (p) { return p.label || p.id; });
        var extra = found.length - names.length;
        var el = $('obg-detect');
        if (!el) return;
        el.innerHTML = 'We found <b>' + names.map(function (n) {
          return String(n).replace(/&/g, '&amp;').replace(/</g, '&lt;');
        }).join('</b>, <b>') + '</b>' +
          (extra > 0 ? ' and ' + extra + ' more runtime' + (extra > 1 ? 's' : '') : '') +
          ' on this machine. One quick choice and your dashboard is ready.';
      }).catch(function () {});
  }

  function _boot() {
    if (window.CLOUD_MODE) return;
    if (!_overlay()) return;
    fetch('/api/onboarding/state')
      .then(function (r) { return r.json(); })
      .then(function (d) {
        if (!d || !d.required) return;
        // The gateway-setup overlay (no auth configured) is more
        // fundamental; let it win this page load — we gate the next one.
        if (_gwSetupMandatoryVisible()) return;
        var m = $('obg-managed-btn');
        if (m) m.addEventListener('click', _startManaged);
        _wireSelfhostHome();
        _fillDetection();
        _show();
      })
      .catch(function () {});
  }

  if (document.readyState === 'loading') {
    // Run after gw-setup's own DOMContentLoaded check so the mandatory
    // gateway overlay is already visible when we look for it.
    document.addEventListener('DOMContentLoaded', function () {
      setTimeout(_boot, 400);
    });
  } else {
    setTimeout(_boot, 400);
  }
})();
