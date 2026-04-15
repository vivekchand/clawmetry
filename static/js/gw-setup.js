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
      document.getElementById('gw-setup-overlay').style.display = 'flex';
    } else {
      updateGwStatus(true, d.url);
    }
  } catch(e) {}
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
  var _cmo = document.getElementById('cloud-modal-overlay');
  document.body.appendChild(_cmo);
  _cmo.style.display = 'flex';
  document.getElementById('cloud-step-email').style.display = '';
  document.getElementById('cloud-step-otp').style.display = 'none';
  document.getElementById('cloud-step-done').style.display = 'none';
  document.getElementById('cloud-email-error').style.display = 'none';
  setTimeout(function(){ var el = document.getElementById('cloud-email-input'); if(el) el.focus(); }, 100);
}
function closeCloudModal() {
  document.getElementById('cloud-modal-overlay').style.display = 'none';
}
document.addEventListener('keydown', function(e){ if(e.key==='Escape') closeCloudModal(); });
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
