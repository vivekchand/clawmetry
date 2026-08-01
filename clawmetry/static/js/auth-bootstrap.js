(function(){
  var stored = localStorage.getItem('clawmetry-token');
  var triedZeroClick = false;

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

  if(!stored){
    tryZeroClick(checkAuth);
  } else {
    checkAuth(stored);
  }

  function checkAuth(tok){
    fetch('/api/auth/check' + (tok ? '?token=' + encodeURIComponent(tok) : ''))
      .then(function(r){return r.json()})
      .then(function(d){
        if(d.needsSetup){
          // No gateway token configured -- show the setup wizard. It starts
          // mandatory, but gw-setup.js relaxes it (dismissible, token form
          // hidden) when runtime detection finds no OpenClaw on the machine.
          document.getElementById('login-overlay').style.display='none';
          var overlay=document.getElementById('gw-setup-overlay');
          overlay.dataset.mandatory='true';
          document.getElementById('gw-setup-close').style.display='none';
          overlay.style.display='flex';
          return;
        }
        if(!d.authRequired){
          document.getElementById('login-overlay').style.display='none';
          return;
        }
        if(d.valid){
          document.getElementById('login-overlay').style.display='none';
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
        document.getElementById('login-overlay').style.display='none';
        var lb=document.getElementById('logout-btn');if(lb)lb.style.display='';
        location.reload();
      } else {
        document.getElementById('login-error').style.display='block';
      }
    });
}
function clawmetryLogout(){
  localStorage.removeItem('clawmetry-token');
  location.reload();
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
