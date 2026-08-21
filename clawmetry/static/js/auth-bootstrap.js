(function(){
  var stored = localStorage.getItem('clawmetry-token');
  var triedZeroClick = false;
  // Explicit sign-out (profile menu → Sign out) must stick: without this
  // marker the zero-click loopback login below signs the user straight back
  // in on reload, making Sign out a no-op on the very machine it runs on.
  // The marker only bites while there is NO stored token — any token stored
  // after sign-out (manual login, the one-click /auth?token= URL) is an
  // intentional sign-in, so it self-clears.
  var signedOut = false;
  try { signedOut = localStorage.getItem('cm-signed-out') === '1'; } catch(e) {}
  if(signedOut && stored){
    try { localStorage.removeItem('cm-signed-out'); } catch(e) {}
    signedOut = false;
  }

  // Zero-click localhost auto-login: ask the server for the on-disk token
  // (only returned on loopback), persist it, and continue inline by
  // re-entering checkAuth with the fresh token. Runs on first load when no
  // token is stored, AND as a one-shot retry when a stored token turns out
  // stale (the gateway token rotated on disk) -- the manual login wall is
  // the last resort, never the first response. The server trusts loopback
  // for /api/* regardless, so walling a localhost user is pure friction.
  //
  // No location.reload() — the fetch shim below pulls the token from
  // localStorage on the next /api/* call, so subsequent fetches authenticate
  // without restarting the page. Reloading here also breaks Playwright/E2E
  // harnesses, which observe the load event before the bootstrap's async
  // fetch resolves and then crash when the navigation fires under their feet
  // ("Execution context was destroyed").
  function tryZeroClick(done){
    triedZeroClick = true;
    fetch('/api/auth/detected-token')
      .then(function(r){ return r.ok ? r.json() : null; })
      .then(function(d){
        if(d && d.token){
          localStorage.setItem('clawmetry-token', d.token);
          done(d.token);
        } else {
          done(null);
        }
      })
      .catch(function(){ done(null); });
  }

  // After an explicit sign-out the wall still offers a one-click way back
  // on the machine itself: probe the loopback-only detected-token endpoint
  // and, if it answers, reveal the "Sign back in (this machine)" button.
  // The probe never stores the token — signing back in stays a user action
  // (clawmetryLocalSignin below).
  function offerLocalSignin(){
    var btn = document.getElementById('login-local-btn');
    if(!btn) return;
    fetch('/api/auth/detected-token')
      .then(function(r){ return r.ok ? r.json() : null; })
      .then(function(d){ if(d && d.token){ btn.style.display=''; } })
      .catch(function(){});
  }

  if(signedOut){
    // Suppress BOTH zero-click paths (fresh and stale-token retry); route
    // through checkAuth(null) so needsSetup / authRequired:false still
    // resolve to their own overlays instead of the login wall.
    triedZeroClick = true;
    checkAuth(null);
  } else if(!stored){
    tryZeroClick(checkAuth);
  } else {
    checkAuth(stored);
  }

  function checkAuth(tok){
    fetch('/api/auth/check' + (tok ? '?token=' + encodeURIComponent(tok) : ''))
      .then(function(r){return r.json()})
      .then(function(d){
        if(d.needsSetup){
          // No gateway token configured. This used to force the legacy
          // "ClawMetry Setup" gateway-token wizard open on every load, even
          // for installs that only run non-OpenClaw runtimes. The dashboard
          // itself works fine with no gateway configured; the first-run
          // choice (managed cloud vs self-host) is onboarding.js's job, and
          // a real OpenClaw gateway can still be configured opt-in from the
          // Developer tab.
          document.getElementById('login-overlay').style.display='none';
          return;
        }
        if(!d.authRequired){
          document.getElementById('login-overlay').style.display='none';
          return;
        }
        if(d.valid){
          document.getElementById('login-overlay').style.display='none';
          try { localStorage.removeItem('cm-signed-out'); } catch(e) {}
          var lb=document.getElementById('logout-btn');if(lb)lb.style.display='';
          return;
        }
        localStorage.removeItem('cm-token');localStorage.removeItem('clawmetry-token');sessionStorage.removeItem('cm-token');
        if(!triedZeroClick){
          // Stored token was stale -- recover the fresh on-disk token over
          // loopback before resorting to the manual wall.
          tryZeroClick(function(fresh){
            if(fresh){ checkAuth(fresh); }
            else { document.getElementById('login-overlay').style.display='flex'; }
          });
          return;
        }
        document.getElementById('login-overlay').style.display='flex';
        if(signedOut) offerLocalSignin();
      })
      .catch(function(){document.getElementById('login-overlay').style.display='none';});
  }
})();
function clawmetryLogin(){
  var tok=document.getElementById('login-token').value.trim();
  if(!tok)return;
  fetch('/api/auth/check?token='+encodeURIComponent(tok))
    .then(function(r){return r.json()})
    .then(function(d){
      if(d.valid){
        localStorage.setItem('clawmetry-token',tok);
        try { localStorage.removeItem('cm-signed-out'); } catch(e) {}
        document.getElementById('login-overlay').style.display='none';
        var lb=document.getElementById('logout-btn');if(lb)lb.style.display='';
        location.reload();
      } else {
        document.getElementById('login-error').style.display='block';
      }
    });
}
function clawmetryLogout(){
  // Marker makes the sign-out stick: the bootstrap suppresses zero-click
  // auto-login until the user signs back in on purpose.
  try { localStorage.setItem('cm-signed-out','1'); } catch(e) {}
  localStorage.removeItem('clawmetry-token');
  location.reload();
}

// ── Cloud-sync toggle chip (header, right of alerts bell) ──
// Cloud sync is included in every ClawMetry plan (Self-Hosted through
// Enterprise), so pausing it is a one-click UX toggle rather than a
// billing decision. State reads from /api/cloud-cta/status (already
// polled by other surfaces); writes go through /api/sync/toggle which
// flips the ~/.clawmetry/nocloud marker the daemon polls each iteration.
function _cmRenderSyncChip(state){
  var el = document.getElementById('sync-toggle-btn');
  if (!el) return;
  var label = document.getElementById('sync-toggle-label');
  var icon = document.getElementById('sync-toggle-icon');
  // Show the chip only when the machine has an account linked. On a
  // truly anonymous local-only install (never signed in), there is
  // nothing to sync TO — showing an inert chip would be a lie.
  if (!state || !state.account_linked) {
    el.style.display = 'none';
    return;
  }
  el.style.display = 'flex';
  if (state.local_only) {
    label.textContent = 'Local only';
    el.style.color = 'var(--text-muted, #94a3b8)';
    el.title = 'Cloud sync paused. Click to resume.';
  } else if (state.connected) {
    label.textContent = 'Synced';
    el.style.color = 'var(--accent, #4ade80)';
    el.title = 'Cloud sync active. Click to pause.';
  } else {
    // Account linked but not connected (e.g. transient) — still show
    // as clickable, and let the toggle-endpoint's error message steer
    // the user to the right recovery flow.
    label.textContent = 'Sync';
    el.style.color = 'var(--text-tertiary, #cbd5e1)';
    el.title = 'Cloud sync status.';
  }
}
function _cmRefreshSyncChip(){
  fetch('/api/cloud-cta/status')
    .then(function(r){ return r.ok ? r.json() : null; })
    .then(_cmRenderSyncChip)
    .catch(function(){ /* offline — leave chip as-is */ });
}
function clawmetryToggleSync(){
  var el = document.getElementById('sync-toggle-btn');
  if (el) el.style.pointerEvents = 'none';
  fetch('/api/sync/toggle', {method:'POST'})
    .then(function(r){
      // 409 == no_account or env_locked — surface a small toast instead
      // of silently failing. Fall through to refresh either way.
      if (r.status === 409) {
        return r.json().then(function(d){
          try { alert(d && d.detail ? d.detail : 'Cloud sync toggle not available.'); } catch(e) {}
          return null;
        });
      }
      return r.ok ? r.json() : null;
    })
    .then(function(_res){ _cmRefreshSyncChip(); })
    .catch(function(){ _cmRefreshSyncChip(); })
    .finally(function(){
      var e = document.getElementById('sync-toggle-btn');
      if (e) e.style.pointerEvents = '';
    });
}
// Poll on load + on tab focus (so returning from a sign-in tab
// picks up the new account-linked state).
document.addEventListener('DOMContentLoaded', function(){
  setTimeout(_cmRefreshSyncChip, 400);
});
window.addEventListener('focus', function(){
  _cmRefreshSyncChip();
});
// ── Cloud sign-in from the dashboard login overlay ──
// Matches `clawmetry onboard` and the desktop first-launch pane so users
// see one auth story across every surface. Uses the existing
// /api/cloud-cta/oauth-start endpoint (which spins up a loopback bridge
// and returns the cloud OAuth start URL). We open the URL in the SAME tab
// so the return round-trip is invisible; on success the loopback bridge
// stashes the cm_ key server-side, then this dashboard's next load picks
// up the fresh gateway token via /api/auth/detected-token.
function clawmetryOauthLogin(provider){
  var err = document.getElementById('login-error');
  if(err){ err.style.display='none'; }
  // Adaptive mode: on a self-hosted machine (nocloud marker present),
  // the trial license flow is what /connect wants — mode=selfhost. On a
  // fresh machine or one already using cloud sync, mode=managed registers
  // the node and starts the sync daemon. Same choice `clawmetry onboard`
  // and the desktop first-launch pane make. Probes /api/cloud-cta/status
  // first so the OAuth start URL matches the machine's disposition.
  fetch('/api/cloud-cta/status')
    .then(function(r){ return r.ok ? r.json() : {local_only: false}; })
    .catch(function(){ return {local_only: false}; })
    .then(function(status){
      var mode = (status && status.local_only) ? 'selfhost' : 'managed';
      return fetch('/api/cloud-cta/oauth-start', {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify({provider: provider, mode: mode}),
      });
    })
    .then(function(r){ return r.ok ? r.json() : null; })
    .then(function(d){
      if(d && d.url){
        // Clear the signed-out marker so the next page load auto-signs in
        // once the cloud round-trip completes and the token lands on disk.
        try { localStorage.removeItem('cm-signed-out'); } catch(e) {}
        window.location.href = d.url;
      } else {
        if(err){ err.textContent = (d && d.error) || 'Sign-in unavailable. Try email or a gateway token.'; err.style.display='block'; }
      }
    })
    .catch(function(){
      if(err){ err.textContent = 'Network error. Try again in a moment.'; err.style.display='block'; }
    });
}
// Email OTP: a two-step (email → code) flow rendered INSIDE the login card.
//
// Routes through the LOCAL proxy pair /api/cloud-cta/send-otp and
// /api/cloud-cta/verify-otp — the same seam the cloud modal uses. They
// forward to app.clawmetry.com and, on verify, pair this machine by
// persisting the returned cm_ key. verify-otp also picks a rail: on a
// local-only install we send mode=selfhost so signing in cannot switch
// cloud egress on behind the operator's back.
//
// This used to POST /api/auth/email-otp, which is a CLOUD-only route: the
// CLI and the desktop pane hit it on https://ingest.clawmetry.com, but the
// relative URL here resolved against the local dashboard, which has no such
// route. Flask answered 404 with an HTML body, r.json() threw, and the
// catch below painted "Network error. Try again." on every attempt — the
// email button was dead on every install (founder report 2026-08-19).
//
// The steps are card-inline rather than window.prompt() for two reasons: a
// prompt blocks the entire webview in the desktop shell, which has no
// browser chrome to recover with, and a raw JS dialog is not something we
// ask a first-time user to trust with their email address.
var _cmOtpEmail = '';

function _cmLoginErr(msg){
  var err = document.getElementById('login-error');
  if(!err) return;
  if(msg){ err.textContent = msg; err.style.display = 'block'; }
  else { err.style.display = 'none'; }
}
function _cmShow(id, on){
  var el = document.getElementById(id);
  if(el) el.style.display = on ? '' : 'none';
}
// The local-recovery button owns its own visibility rule (revealed only when
// the loopback probe answers), so remember whether it was up before hiding it.
var _cmLocalBtnWasShown = false;

function clawmetryEmailOtpStart(){
  _cmLoginErr('');
  var lb = document.getElementById('login-local-btn');
  _cmLocalBtnWasShown = !!(lb && lb.style.display !== 'none');
  if(lb) lb.style.display = 'none';
  _cmShow('login-choices', false);
  _cmShow('login-email-step', true);
  _cmShow('login-email-back', true);
  var el = document.getElementById('login-email-input');
  if(el) el.focus();
}

function clawmetryEmailOtpCancel(){
  _cmLoginErr('');
  _cmShow('login-email-step', false);
  _cmShow('login-otp-step', false);
  _cmShow('login-email-back', false);
  _cmShow('login-choices', true);
  var lb = document.getElementById('login-local-btn');
  if(lb && _cmLocalBtnWasShown) lb.style.display = '';
}

function clawmetryEmailOtpSend(){
  var input = document.getElementById('login-email-input');
  var email = input ? (input.value || '').trim() : '';
  if(!email || email.indexOf('@') < 0){ _cmLoginErr('Enter a valid email address.'); return; }
  _cmLoginErr('');
  var btn = document.getElementById('login-email-send');
  if(btn){ btn.disabled = true; btn.textContent = 'Sending…'; }
  fetch('/api/cloud-cta/send-otp', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({email: email}),
  })
    .then(function(r){ return r.json(); })
    .then(function(d){
      if(!d || !d.ok){ _cmLoginErr((d && d.error) || 'Could not send code.'); return; }
      _cmOtpEmail = email;
      _cmShow('login-email-step', false);
      _cmShow('login-otp-step', true);
      var sent = document.getElementById('login-otp-sent');
      if(sent) sent.textContent = 'We sent a code to ' + email;
      var code = document.getElementById('login-otp-input');
      if(code) code.focus();
    })
    .catch(function(){ _cmLoginErr('Network error. Try again.'); })
    .finally(function(){
      var b = document.getElementById('login-email-send');
      if(b){ b.disabled = false; b.textContent = 'Send code'; }
    });
}

function clawmetryEmailOtpVerify(){
  var input = document.getElementById('login-otp-input');
  var code = input ? (input.value || '').replace(/\s/g, '') : '';
  if(code.length < 4){ _cmLoginErr('Enter the code from your email.'); return; }
  _cmLoginErr('');
  var btn = document.getElementById('login-otp-verify');
  if(btn){ btn.disabled = true; btn.textContent = 'Verifying…'; }
  // Same rail probe clawmetryOauthLogin does: on a self-hosted machine
  // signing in must not flip egress on, so send mode=selfhost and let
  // verify-otp take the identity-only path.
  fetch('/api/cloud-cta/status')
    .then(function(r){ return r.ok ? r.json() : {local_only: false}; })
    .catch(function(){ return {local_only: false}; })
    .then(function(status){
      return fetch('/api/cloud-cta/verify-otp', {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify({
          email: _cmOtpEmail,
          code: code,
          mode: (status && status.local_only) ? 'selfhost' : 'managed',
        }),
      });
    })
    .then(function(r){ return r.json(); })
    .then(function(v){
      if(v && v.ok && v.token){
        // Clearing the marker re-arms zero-click auto-login, so the reload
        // picks the on-disk gateway token back up and drops the wall.
        try { localStorage.removeItem('cm-signed-out'); } catch(e) {}
        location.reload();
        return;
      }
      _cmLoginErr((v && v.error) || 'Invalid code.');
      var b = document.getElementById('login-otp-verify');
      if(b){ b.disabled = false; b.textContent = 'Verify and open dashboard'; }
    })
    .catch(function(){
      _cmLoginErr('Network error. Try again.');
      var b = document.getElementById('login-otp-verify');
      if(b){ b.disabled = false; b.textContent = 'Verify and open dashboard'; }
    });
}

// One-click sign-in on the machine itself after an explicit sign-out. The
// button is hidden unless the loopback-only detected-token probe answered,
// so this is the same trust boundary as zero-click auto-login — just gated
// on a deliberate click.
function clawmetryLocalSignin(){
  fetch('/api/auth/detected-token')
    .then(function(r){ return r.ok ? r.json() : null; })
    .then(function(d){
      if(d && d.token){
        try { localStorage.removeItem('cm-signed-out'); } catch(e) {}
        localStorage.setItem('clawmetry-token', d.token);
        location.reload();
      } else {
        var err=document.getElementById('login-error');
        if(err) err.style.display='block';
      }
    })
    .catch(function(){
      var err=document.getElementById('login-error');
      if(err) err.style.display='block';
    });
}
// Inject auth header into all fetch calls, and notice when the backend
// stops answering at all.
//
// A dead local backend rejects every fetch with a network-level TypeError
// ("Load failed" in WebKit, "Failed to fetch" in Chromium) -- no status, no
// response. Each panel used to absorb that on its own, so a machine-wide
// outage rendered as a dozen unrelated "Loading..." spinners and one
// unhelpful per-panel Retry. On 2026-08-17 a desktop user sat in front of
// that for over six hours with nothing telling them the backend was gone.
// This is the one place every /api/ call passes through, so the global
// outage signal belongs here.
(function(){
  var _origFetch=window.fetch;
  var _netFail=0;
  // One transient failure means nothing (a restart, a sleep/wake, a
  // navigation racing an in-flight request). Three in a row is an outage.
  var FAIL_THRESHOLD=3;

  function _isNetworkError(e){
    // Never treat an HTTP error status as an outage -- those resolve.
    return !!e && (e.name==='TypeError' || e instanceof TypeError);
  }

  window.fetch=function(url,opts){
    var tok=localStorage.getItem('clawmetry-token');
    var isApi=(typeof url==='string' && url.startsWith('/api/'));
    if(tok && isApi){
      opts=opts||{};
      opts.headers=opts.headers||{};
      if(opts.headers instanceof Headers){opts.headers.set('Authorization','Bearer '+tok);}
      else{opts.headers['Authorization']='Bearer '+tok;}
    }
    if(!isApi) return _origFetch.call(this,url,opts);
    return _origFetch.call(this,url,opts).then(function(r){
      // Any answer at all -- even a 500 -- means the backend is reachable.
      if(_netFail!==0){
        _netFail=0;
        window.dispatchEvent(new CustomEvent('cm:backend-reachable'));
      }
      return r;
    },function(e){
      if(_isNetworkError(e)){
        _netFail++;
        if(_netFail===FAIL_THRESHOLD){
          window.dispatchEvent(new CustomEvent('cm:backend-unreachable',
            {detail:{url:String(url)}}));
        }
      }
      throw e;
    });
  };
  // The probe in the recovery block uses this so a health check that
  // fails cannot itself inflate the outage counter.
  window.__cmOrigFetch=_origFetch;
  window.cmBackendFailures=function(){return _netFail;};
})();

// ── Backend recovery: the refresh button, the outage overlay, and Cmd-R ──
// One implementation behind three entry points, because a naive "reload the
// page" button is a trap in the desktop shell. A pywebview window has no
// browser chrome, so if the backend is dead, location.reload() replaces a
// frozen-but-readable dashboard with a blank WebKit error page that has no
// buttons on it at all -- strictly worse than the freeze. So: probe first,
// heal the backend if it is down, and only then reload.
(function(){
  var BAR_ID='cm-backend-outage';
  var BTN_ID='cm-reconnect-btn';
  var busy=false;

  function _bridge(){
    try{
      return (window.pywebview && window.pywebview.api) ? window.pywebview.api : null;
    }catch(e){ return null; }
  }

  // Probe with the UNWRAPPED fetch: a health probe that fails must not count
  // toward the outage threshold that raised this overlay in the first place.
  function _probe(timeoutMs){
    return new Promise(function(resolve){
      var done=false;
      var t=setTimeout(function(){ if(!done){ done=true; resolve(false); } }, timeoutMs||4000);
      function settle(v){ if(!done){ done=true; clearTimeout(t); resolve(v); } }
      try{
        (window.__cmOrigFetch||window.fetch).call(window,'/api/health',{cache:'no-store'})
          .then(function(){ settle(true); }, function(){ settle(false); });
      }catch(e){ settle(false); }
    });
  }

  function _waitForBackend(budgetMs){
    var deadline=Date.now()+(budgetMs||45000);
    return new Promise(function(resolve){
      (function attempt(){
        _probe(2500).then(function(alive){
          if(alive) return resolve(true);
          if(Date.now()>=deadline) return resolve(false);
          setTimeout(attempt,1500);
        });
      })();
    });
  }

  function _btn(){ return document.getElementById(BTN_ID); }

  function _setBusy(on,label){
    busy=on;
    var b=_btn();
    if(b){
      b.classList.toggle('cm-spinning',!!on);
      b.setAttribute('aria-busy',on?'true':'false');
      b.title=on?(label||'Reconnecting…'):'Refresh (Cmd/Ctrl + R)';
    }
    var bar=document.getElementById(BAR_ID);
    if(bar && bar.__btn){
      bar.__btn.disabled=!!on;
      if(on) bar.__btn.textContent=label||'Restarting…';
      else   bar.__btn.textContent=bar.__label;
    }
  }

  // Mark the header button when the backend is known-unreachable, so the
  // affordance is discoverable BEFORE the user goes hunting for it.
  function _markDown(down){
    var b=_btn();
    if(b) b.classList.toggle('cm-attention',!!down);
  }

  function _dismiss(){
    var el=document.getElementById(BAR_ID);
    if(el && el.parentNode) el.parentNode.removeChild(el);
    _markDown(false);
  }

  function _show(note){
    _markDown(true);
    var existing=document.getElementById(BAR_ID);
    if(existing){
      if(note && existing.__note) existing.__note.textContent=note;
      return;
    }
    var api=_bridge();
    var el=document.createElement('div');
    el.id=BAR_ID;
    el.setAttribute('role','alert');
    el.style.cssText=[
      'position:fixed','left:50%','transform:translateX(-50%)','bottom:24px',
      'z-index:2147483000','max-width:min(640px,92vw)',
      'display:flex','align-items:center','gap:14px','flex-wrap:wrap',
      'padding:14px 18px','border-radius:12px',
      'background:#2a1215','border:1px solid #7f1d1d','color:#fecaca',
      'box-shadow:0 12px 32px rgba(0,0,0,.45)',
      'font:14px/1.45 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif'
    ].join(';');

    var msg=document.createElement('div');
    msg.style.cssText='flex:1 1 260px;min-width:220px';
    msg.innerHTML='<strong style="color:#fca5a5">Cannot reach the ClawMetry '
      +'backend on this machine.</strong><br>'
      +'<span style="color:#f3b5b5">Numbers on every tab are frozen at their '
      +'last known values.</span>';
    el.appendChild(msg);

    var btn=document.createElement('button');
    btn.type='button';
    btn.style.cssText=[
      'cursor:pointer','white-space:nowrap','padding:8px 16px',
      'border-radius:8px','border:1px solid #ef4444','background:#ef4444',
      'color:#fff','font-weight:600','font-size:13px'
    ].join(';');
    el.__label=(api&&api.restart_backend)?'Restart backend':'Reload';
    btn.textContent=el.__label;
    btn.onclick=function(){ window.cmReconnect(); };
    el.__btn=btn;
    el.appendChild(btn);

    var hint=document.createElement('div');
    hint.style.cssText='flex-basis:100%;font-size:12px;color:#e7a3a3';
    hint.textContent=note||((api&&api.restart_backend)
      ? 'This restarts the local backend and reloads the page.'
      : 'If reloading does not help, quit ClawMetry and open it again.');
    el.__note=hint;
    el.appendChild(hint);

    (document.body||document.documentElement).appendChild(el);
  }

  // The single recovery path. Safe to call whether the backend is healthy
  // (plain refresh) or dead (heal, then refresh).
  function cmReconnect(){
    if(busy) return Promise.resolve(false);
    _setBusy(true,'Checking…');
    return _probe(4000).then(function(alive){
      if(alive){ location.reload(); return true; }
      var api=_bridge();
      if(api && api.restart_backend){
        _setBusy(true,'Restarting…');
        try{ api.restart_backend(); }
        catch(e){ _setBusy(false); _show('Could not reach the app shell. Quit ClawMetry and open it again.'); return false; }
        // Budget is overridable so the test suite can exercise the
        // did-not-come-back branch without waiting three quarters of a minute.
        return _waitForBackend(window.__cmRestartBudgetMs||45000).then(function(ok){
          if(ok){ location.reload(); return true; }
          _setBusy(false);
          _show('The backend did not come back. Quit ClawMetry and open it again.');
          return false;
        });
      }
      // No bridge and no backend. Reloading here would swap the page for a
      // blank error page with no way back, so refuse and say what helps.
      _setBusy(false);
      _show('The backend is not answering, so reloading would leave a blank page. Quit ClawMetry and open it again.');
      return false;
    });
  }

  window.addEventListener('cm:backend-unreachable',function(){ _show(); });
  window.addEventListener('cm:backend-reachable',_dismiss);

  // Cmd/Ctrl+R. pywebview's Cocoa backend swallows the native shortcut, so
  // inside the shell we implement it ourselves; in a real browser the native
  // reload is already correct, so leave it alone.
  document.addEventListener('keydown',function(e){
    if(!(e.metaKey||e.ctrlKey) || e.altKey) return;
    if(e.key!=='r' && e.key!=='R') return;
    if(!_bridge()) return;
    e.preventDefault();
    cmReconnect();
  },true);

  window.cmReconnect=cmReconnect;
  window.cmShowBackendOutage=_show;
  window.cmHideBackendOutage=_dismiss;
  window.cmBackendProbe=_probe;
})();

// ── Version badge + one-click update ──
(function(){
  function checkVersion(){
    fetch('/api/version').then(function(r){return r.json();}).then(function(d){
      var badges=document.querySelectorAll('.version-badge');
      badges.forEach(function(badge){
        if(d.update_available){
          badge.textContent='v'+d.current+' -> v'+d.latest+' \u2B06';
          badge.className='version-badge update-available';
          badge.title='Click to update ClawMetry to v'+d.latest;
          badge.onclick=function(){triggerUpdate(d.latest,badges);};
        }else{
          badge.textContent='v'+d.current;
        }
      });
    }).catch(function(){});
  }
  function triggerUpdate(latest,badges){
    if(!confirm('Update ClawMetry to v'+latest+'? Dashboard will restart.'))return;
    badges.forEach(function(b){b.textContent='Updating...';b.className='version-badge updating';b.onclick=null;});
    fetch('/api/update',{method:'POST'}).then(function(r){return r.json();}).then(function(d){
      if(d.ok){
        badges.forEach(function(b){b.textContent='Restarting...';});
        setTimeout(function(){window.location.reload();},5000);
      }else{
        badges.forEach(function(b){b.textContent='Update failed';b.className='version-badge';});
      }
    }).catch(function(){
      badges.forEach(function(b){b.textContent='Update failed';b.className='version-badge';});
    });
  }
  checkVersion();
})();
