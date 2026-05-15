(function(){
  var stored = localStorage.getItem('clawmetry-token');

  // Zero-click localhost auto-login: if no token in localStorage, ask the
  // server for the on-disk token (only returned on loopback). If we get one,
  // persist it and continue inline by re-entering checkAuth with the token.
  // Falls back to the manual login overlay on any error / 403 / 404 (endpoint
  // may not be deployed yet, or the request isn't from localhost).
  //
  // No location.reload() — the fetch shim below pulls the token from
  // localStorage on the next /api/* call, so subsequent fetches authenticate
  // without restarting the page. Reloading here also breaks Playwright/E2E
  // harnesses, which observe the load event before the bootstrap's async
  // fetch resolves and then crash when the navigation fires under their feet
  // ("Execution context was destroyed").
  if(!stored){
    fetch('/api/auth/detected-token')
      .then(function(r){ return r.ok ? r.json() : null; })
      .then(function(d){
        if(d && d.token){
          localStorage.setItem('clawmetry-token', d.token);
          checkAuth(d.token);
        } else {
          checkAuth(null);
        }
      })
      .catch(function(){ checkAuth(null); });
  } else {
    checkAuth(stored);
  }

  function checkAuth(tok){
    fetch('/api/auth/check' + (tok ? '?token=' + encodeURIComponent(tok) : ''))
      .then(function(r){return r.json()})
      .then(function(d){
        if(d.needsSetup){
          // No gateway token configured -- show mandatory gateway setup wizard
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
        localStorage.removeItem('cm-token');localStorage.removeItem('clawmetry-token');sessionStorage.removeItem('cm-token');document.getElementById('login-overlay').style.display='flex';
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
