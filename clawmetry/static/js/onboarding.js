// onboarding.js — first-run onboarding gate (hard gate, no skip).
//
// Shows templates/partials/onboarding-modal.html when
// GET /api/onboarding/state says {required:true}. The gate itself is just
// two cards with one button each; the details live in modals:
//   managed  — cloud modal (gw-setup.js openCloudModal: OTP / Google /
//              GitHub), we poll /api/cloud-cta/status until connected
//   selfhost — self-host modal (partials/selfhost-modal.html, the shm*
//              globals below): Google/GitHub OAuth via the mode=selfhost
//              bridge (identity + trial license, data stays local), email
//              + 6-digit code via /api/trial/activate, or a CLAW1 key via
//              /api/onboarding/activate-license
// Every way out is recorded via POST /api/onboarding/complete (or the
// combined activate-license endpoint).
//
// Never runs on the hosted cloud dashboard (window.CLOUD_MODE) — that
// account signing up WAS the onboarding choice.

(function () {
  'use strict';

  var _pollTimer = null;   // managed-connect status poll
  var _oauthTimer = null;  // self-host OAuth bridge poll
  var _email = '';

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
    if (_oauthTimer) { clearInterval(_oauthTimer); _oauthTimer = null; }
  }

  function _err(id, msg) {
    var e = $(id);
    if (e) { e.textContent = msg || ''; e.style.display = msg ? 'block' : 'none'; }
  }

  function _complete(choice, onFail) {
    fetch('/api/onboarding/complete', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ choice: choice }),
    }).then(function (r) { return r.json(); }).then(function (d) {
      if (d && d.ok) {
        window.closeSelfhostModal();
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

  // ── Self-host modal (partials/selfhost-modal.html) ───────────────────
  var _SHM_STEPS = ['home', 'otp', 'wait', 'license', 'ended'];
  var _SHM_ERRS = ['shm-home-error', 'shm-otp-error', 'shm-wait-error', 'shm-license-error'];

  function _shmStep(name) {
    _SHM_STEPS.forEach(function (s) {
      var el = $('shm-step-' + s);
      if (el) el.style.display = s === name ? 'block' : 'none';
    });
  }

  function _shmStopPoll() {
    if (_oauthTimer) { clearInterval(_oauthTimer); _oauthTimer = null; }
  }

  window.openSelfhostModal = function () {
    var o = $('selfhost-modal-overlay');
    if (!o) return;
    _SHM_ERRS.forEach(function (id) { _err(id, ''); });
    _shmStep('home');
    o.style.display = 'flex';
    setTimeout(function () { var el = $('shm-email-input'); if (el) el.focus(); }, 60);
  };

  window.closeSelfhostModal = function () {
    var o = $('selfhost-modal-overlay');
    if (o) o.style.display = 'none';
    _shmStopPoll();
  };

  window.shmBackHome = function () {
    _shmStopPoll();
    _SHM_ERRS.forEach(function (id) { _err(id, ''); });
    _shmStep('home');
  };

  window.shmShowLicense = function () {
    _shmStopPoll();
    _err('shm-license-error', '');
    _shmStep('license');
    setTimeout(function () { var el = $('shm-license-input'); if (el) el.focus(); }, 60);
  };

  // Google/GitHub → mode=selfhost bridge: identity + trial, egress stays off.
  window.shmOauth = function (provider) {
    _err('shm-home-error', '');
    fetch('/api/cloud-cta/oauth-start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ provider: provider, mode: 'selfhost' }),
    }).then(function (r) { return r.json(); }).then(function (d) {
      if (!d || !d.ok || !d.url) {
        _err('shm-home-error', (d && d.error) || 'Could not start sign-in. Try email instead.');
        return;
      }
      window.open(d.url, '_blank');
      _err('shm-wait-error', '');
      _shmStep('wait');
      var tries = 0;
      _shmStopPoll();
      _oauthTimer = setInterval(function () {
        tries += 1;
        if (tries > 150) {
          _shmStopPoll();
          _err('shm-wait-error', 'Sign-in timed out. Try again.');
          return;
        }
        fetch('/api/cloud-cta/oauth-status').then(function (r) { return r.json(); })
          .then(function (s) {
            if (!s) return;
            if (s.status === 'connected') {
              _shmStopPoll();
              if (s.trial === 'active') {
                _complete('selfhost_trial', function (msg) { _err('shm-wait-error', msg); });
              } else if (s.trial === 'expired') {
                _shmStep('ended');
              } else {
                _err('shm-wait-error',
                  "You're signed in, but we couldn't start your trial. Try again or use email.");
              }
            } else if (s.status === 'error') {
              _shmStopPoll();
              _err('shm-wait-error', s.error || 'Sign-in failed. Try email instead.');
            }
          }).catch(function () {});
      }, 2000);
    }).catch(function () {
      _err('shm-home-error', 'Network error. Try again.');
    });
  };

  // Email → 6-digit code → /api/trial/activate (same rail as the CLI).
  window.shmSendOtp = function () {
    var email = (($('shm-email-input') || {}).value || '').trim();
    if (!email || email.indexOf('@') < 0) {
      _err('shm-home-error', 'Enter a valid email.');
      return;
    }
    _email = email;
    _err('shm-home-error', '');
    var btn = $('shm-send-btn');
    if (btn) { btn.textContent = 'Sending'; btn.disabled = true; }
    fetch('/api/cloud-cta/send-otp', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: email }),
    }).then(function (r) { return r.json(); }).then(function (d) {
      if (btn) { btn.textContent = 'Get Started'; btn.disabled = false; }
      if (d && d.ok === false) {
        _err('shm-home-error', d.error || 'Could not send the code. Try again.');
        return;
      }
      var em = $('shm-otp-email');
      if (em) em.textContent = _email;
      _err('shm-otp-error', '');
      _shmStep('otp');
      setTimeout(function () { var el = $('shm-otp-input'); if (el) { el.value = ''; el.focus(); } }, 60);
    }).catch(function () {
      if (btn) { btn.textContent = 'Get Started'; btn.disabled = false; }
      _err('shm-home-error', 'Network error. Try again.');
    });
  };

  window.shmResendOtp = function () {
    if (!_email) { window.shmBackHome(); return; }
    fetch('/api/cloud-cta/send-otp', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: _email }),
    }).then(function (r) { return r.json(); }).then(function (d) {
      _err('shm-otp-error', (d && d.ok === false)
        ? (d.error || 'Could not resend the code.')
        : 'Code re-sent. Check your inbox.');
    }).catch(function () {
      _err('shm-otp-error', 'Network error. Try again.');
    });
  };

  window.shmVerifyOtp = function () {
    var code = ((($('shm-otp-input') || {}).value) || '').replace(/\s/g, '');
    if (code.length !== 6) {
      _err('shm-otp-error', 'Enter the 6-digit code from your email.');
      return;
    }
    _err('shm-otp-error', '');
    var btn = $('shm-verify-btn');
    if (btn) { btn.textContent = 'Activating'; btn.disabled = true; }
    fetch('/api/trial/activate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: _email, code: code }),
    }).then(function (r) { return r.json(); }).then(function (d) {
      if (!d || !d.ok) {
        _err('shm-otp-error', (d && d.error) || 'Activation failed. Try again.');
        if (btn) { btn.textContent = 'Activate trial'; btn.disabled = false; }
        return;
      }
      _complete('selfhost_trial', function (msg) {
        _err('shm-otp-error', msg);
        if (btn) { btn.textContent = 'Activate trial'; btn.disabled = false; }
      });
    }).catch(function () {
      _err('shm-otp-error', 'Network error. Try again.');
      if (btn) { btn.textContent = 'Activate trial'; btn.disabled = false; }
    });
  };

  window.shmActivateLicense = function () {
    var key = ((($('shm-license-input') || {}).value) || '').trim();
    if (!key) { _err('shm-license-error', 'Paste your license key.'); return; }
    _err('shm-license-error', '');
    var btn = $('shm-license-btn');
    if (btn) { btn.textContent = 'Activating'; btn.disabled = true; }
    fetch('/api/onboarding/activate-license', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ key: key }),
    }).then(function (r) { return r.json(); }).then(function (d) {
      if (!d || !d.ok) {
        _err('shm-license-error', (d && d.error) || 'Activation failed. Try again.');
        if (btn) { btn.textContent = 'Activate'; btn.disabled = false; }
        return;
      }
      window.closeSelfhostModal();
      _hide();
      location.reload();
    }).catch(function () {
      _err('shm-license-error', 'Network error. Try again.');
      if (btn) { btn.textContent = 'Activate'; btn.disabled = false; }
    });
  };

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
        var m = $('obg-managed-btn');
        if (m) m.addEventListener('click', _startManaged);
        var s = $('obg-selfhost-btn');
        if (s) s.addEventListener('click', window.openSelfhostModal);
        _fillDetection();
        _show();
      })
      .catch(function () {});
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', _boot);
  } else {
    _boot();
  }
})();
