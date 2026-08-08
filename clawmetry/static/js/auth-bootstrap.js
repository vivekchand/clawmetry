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
// Email OTP: swap the login card into a two-step (email → code) inline flow.
// Uses /api/auth/email-otp (same endpoint `clawmetry onboard` and the
// desktop pane hit). On success the returned cm_key is saved server-side
// and the page reloads to pick up the fresh gateway token via auto-signin.
function clawmetryEmailOtpStart(){
  var err = document.getElementById('login-error');
  if(err){ err.style.display='none'; }
  var email = prompt('Email address to send a sign-in code to:');
  if(!email || email.indexOf('@') < 0){ return; }
  fetch('/api/auth/email-otp', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({action:'send', email: email.trim()}),
  })
    .then(function(r){ return r.json(); })
    .then(function(d){
      if(!d || !d.ok){
        if(err){ err.textContent = (d && d.error) || 'Could not send code.'; err.style.display='block'; }
        return;
      }
      var code = prompt('Check ' + email + ' for a 6-digit code:');
      if(!code){ return; }
      return fetch('/api/auth/email-otp', {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify({action:'verify', email: email.trim(), otp: code.trim()}),
      }).then(function(r){ return r.json(); }).then(function(v){
        if(v && v.ok){
          try { localStorage.removeItem('cm-signed-out'); } catch(e) {}
          location.reload();
        } else {
          if(err){ err.textContent = (v && v.error) || 'Invalid code.'; err.style.display='block'; }
        }
      });
    })
    .catch(function(){
      if(err){ err.textContent = 'Network error. Try again.'; err.style.display='block'; }
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
// Inject auth header into all fetch calls
(function(){
  var _origFetch=window.fetch;
  window.fetch=function(url,opts){
    var tok=localStorage.getItem('clawmetry-token');
    if(tok && typeof url==='string' && url.startsWith('/api/')){
      opts=opts||{};
      opts.headers=opts.headers||{};
      if(opts.headers instanceof Headers){opts.headers.set('Authorization','Bearer '+tok);}
      else{opts.headers['Authorization']='Bearer '+tok;}
    }
    return _origFetch.call(this,url,opts);
  };
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
