/* bug-report.js — the "Report a bug" dialog.
 *
 * One code path for both surfaces: the dialog always POSTs to
 * /api/bug-report on whatever origin it is loaded from. On localhost the
 * OSS blueprint (routes/support.py) collects diagnostics and forwards to
 * the cloud; on app.clawmetry.com the cloud blueprint handles it inline.
 * The browser cannot tell, which is the point.
 *
 * Ticket ids are minted by the server, never here: an id a user can quote
 * must not exist unless the row committed. We send a random idempotency
 * key instead, so pressing Send twice after a dropped connection files one
 * report, not two.
 *
 * The ticket list lives in localStorage (per browser) and its statuses are
 * always re-fetched from the server, so "fixed" shows up here without the
 * user doing anything. Losing localStorage loses nothing that matters: the
 * acknowledgement email carries the id and the status link.
 */
(function () {
  'use strict';

  var STORE_KEY = 'cm_bug_tickets';
  var MAX_REMEMBERED = 12;
  var _idemKey = null;
  var _consoleErrors = [];
  var _diagnostics = null;
  var _screenshot = null;      // {dataUrl, name, bytes}
  var _lastFocus = null;

  /* Capture console errors so a report can carry what the page already
     knew was wrong. Capped, and only ever sent with an explicit Send. */
  window.addEventListener('error', function (e) {
    if (_consoleErrors.length < 10 && e && e.message) {
      _consoleErrors.push(String(e.message).slice(0, 300));
    }
  });
  window.addEventListener('unhandledrejection', function (e) {
    if (_consoleErrors.length < 10 && e && e.reason) {
      _consoleErrors.push('unhandled promise: ' + String(e.reason).slice(0, 280));
    }
  });

  function $(id) { return document.getElementById(id); }

  function readTickets() {
    try {
      var raw = localStorage.getItem(STORE_KEY);
      var list = raw ? JSON.parse(raw) : [];
      return Array.isArray(list) ? list : [];
    } catch (e) { return []; }
  }

  function writeTickets(list) {
    try {
      localStorage.setItem(STORE_KEY, JSON.stringify(list.slice(0, MAX_REMEMBERED)));
    } catch (e) { /* private mode, quota, blocked storage — not fatal */ }
  }

  function rememberTicket(rec) {
    var list = readTickets().filter(function (t) { return t.ticket !== rec.ticket; });
    list.unshift(rec);
    writeTickets(list);
  }

  function newIdemKey() {
    try {
      if (window.crypto && window.crypto.randomUUID) return window.crypto.randomUUID();
      var buf = new Uint8Array(16);
      window.crypto.getRandomValues(buf);
      return Array.prototype.map.call(buf, function (b) {
        return ('0' + b.toString(16)).slice(-2);
      }).join('');
    } catch (e) {
      return 'k' + Date.now() + Math.random().toString(16).slice(2);
    }
  }

  function currentTab() {
    try {
      var active = document.querySelector('.left-nav-item.active, .nav-tab.active');
      return active ? (active.getAttribute('data-tab') || active.textContent.trim()) : '';
    } catch (e) { return ''; }
  }

  function clientContext() {
    var ctx = {
      page: String(location.pathname + location.search).slice(0, 200),
      tab: currentTab(),
      user_agent: navigator.userAgent,
      viewport: window.innerWidth + 'x' + window.innerHeight,
      locale: navigator.language || '',
      theme: document.body.getAttribute('data-theme') || ''
    };
    if (_consoleErrors.length) ctx.console_errors = _consoleErrors.slice(0, 10);
    return ctx;
  }

  /* ── open / close ─────────────────────────────────────────────────── */
  window.openBugModal = function () {
    var overlay = $('bug-overlay');
    if (!overlay) return;
    _lastFocus = document.activeElement;
    // Opening from the sidebar means "I want to report a bug", not "show me
    // the receipt from last time". The ticket is not lost: it is listed under
    // Your earlier reports, and it was emailed. Leaving the receipt up also
    // left a keyboard user with nowhere to land, because the form it would
    // focus is hidden behind it.
    var receipt = $('bug-receipt');
    if (receipt && !receipt.hidden) {
      window.resetBugForm();
    }
    _idemKey = newIdemKey();
    overlay.classList.add('open');
    renderMyReports();
    loadDiagnostics();
    // The dialog scrolls internally. Focusing the first field scrolls it into
    // view, which on a short window lands the person halfway down a form they
    // have not read yet -- so reset the scroll AFTER focusing, not before.
    var body = overlay.querySelector('.bug-content');
    var title = $('bug-title');
    setTimeout(function () {
      if (title) {
        try { title.focus({ preventScroll: true }); } catch (e) { title.focus(); }
      }
      if (body) body.scrollTop = 0;
    }, 60);
    document.addEventListener('keydown', onKeydown);
    document.addEventListener('paste', onPaste);
  };

  window.closeBugModal = function () {
    var overlay = $('bug-overlay');
    if (overlay) overlay.classList.remove('open');
    document.removeEventListener('keydown', onKeydown);
    document.removeEventListener('paste', onPaste);
    if (_lastFocus && _lastFocus.focus) { try { _lastFocus.focus(); } catch (e) {} }
  };

  function onKeydown(e) {
    if (e.key === 'Escape') window.closeBugModal();
  }

  /* ── diagnostics preview ──────────────────────────────────────────── */
  function loadDiagnostics() {
    var box = $('bug-diagnostics');
    if (!box || _diagnostics) {
      if (box && _diagnostics) box.textContent = renderDiag(_diagnostics);
      return;
    }
    fetch('/api/bug-report/diagnostics', { headers: { 'Accept': 'application/json' } })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (j) {
        _diagnostics = (j && j.diagnostics) || {};
        box.textContent = renderDiag(_diagnostics);
      })
      .catch(function () {
        _diagnostics = {};
        box.textContent = renderDiag({});
      });
  }

  function renderDiag(server) {
    var merged = {};
    Object.keys(server || {}).forEach(function (k) { merged[k] = server[k]; });
    var ctx = clientContext();
    Object.keys(ctx).forEach(function (k) { merged[k] = ctx[k]; });
    try { return JSON.stringify(merged, null, 2); } catch (e) { return '(unavailable)'; }
  }

  /* ── screenshot ───────────────────────────────────────────────────────
   * "Show us" beats "describe it" for anyone who does not have our words for
   * what they are looking at. Three ways in, because people reach for
   * different ones: drop, paste, or pick.
   *
   * The image is downscaled in the browser before it is sent. A raw retina
   * screenshot is several megabytes; nobody's bug report should depend on
   * their upstream bandwidth, and nothing here is worth storing at full size.
   */
  var MAX_EDGE = 1600;
  var MAX_BYTES = 1500 * 1024;

  function onPaste(e) {
    var overlay = $('bug-overlay');
    if (!overlay || !overlay.classList.contains('open')) return;
    var items = (e.clipboardData && e.clipboardData.items) || [];
    for (var i = 0; i < items.length; i++) {
      if (items[i].type && items[i].type.indexOf('image/') === 0) {
        var file = items[i].getAsFile();
        if (file) { e.preventDefault(); acceptImage(file); return; }
      }
    }
  }

  function acceptImage(file) {
    if (!file || !/^image\//.test(file.type || '')) {
      showError('That file is not an image. PNG, JPEG or WebP work.');
      return;
    }
    var reader = new FileReader();
    reader.onload = function () { downscale(String(reader.result), file.name || 'screenshot'); };
    reader.onerror = function () {
      showError('We could not read that image. Try saving it again, or send '
        + 'the report without it.');
    };
    reader.readAsDataURL(file);
  }

  function downscale(dataUrl, name) {
    var img = new Image();
    img.onload = function () {
      var scale = Math.min(1, MAX_EDGE / Math.max(img.width, img.height));
      var w = Math.max(1, Math.round(img.width * scale));
      var h = Math.max(1, Math.round(img.height * scale));
      var canvas = document.createElement('canvas');
      canvas.width = w; canvas.height = h;
      try {
        canvas.getContext('2d').drawImage(img, 0, 0, w, h);
      } catch (e) {
        setScreenshot(dataUrl, name); return;      // keep the original rather than lose it
      }
      var out = null;
      var qualities = [0.82, 0.65, 0.5];
      for (var i = 0; i < qualities.length; i++) {
        var candidate = canvas.toDataURL('image/webp', qualities[i]);
        if (candidate.indexOf('data:image/webp') !== 0) {
          candidate = canvas.toDataURL('image/jpeg', qualities[i]);
        }
        out = candidate;
        if (candidate.length * 0.75 <= MAX_BYTES) break;
      }
      if (out && out.length * 0.75 > MAX_BYTES) {
        showError('That image is very large even after shrinking. Try a '
          + 'screenshot of just the part that is wrong.');
        return;
      }
      setScreenshot(out || dataUrl, name);
    };
    img.onerror = function () {
      showError('We could not read that image. Try saving it again, or send '
        + 'the report without it.');
    };
    img.src = dataUrl;
  }

  function setScreenshot(dataUrl, name) {
    _screenshot = { dataUrl: dataUrl, name: String(name).slice(0, 80),
                    bytes: Math.round(dataUrl.length * 0.75) };
    var fig = $('bug-shot'), im = $('bug-shot-img'), label = $('bug-shot-name');
    if (im) im.src = dataUrl;
    if (label) {
      label.textContent = _screenshot.name + ' \u00b7 '
        + Math.max(1, Math.round(_screenshot.bytes / 1024)) + ' KB';
    }
    if (fig) fig.hidden = false;
    var drop = $('bug-drop'); if (drop) drop.hidden = true;
    var errBox = $('bug-error'); if (errBox) errBox.hidden = true;
  }

  function clearScreenshot() {
    _screenshot = null;
    var fig = $('bug-shot'); if (fig) fig.hidden = true;
    var drop = $('bug-drop'); if (drop) drop.hidden = false;
    var input = $('bug-file'); if (input) input.value = '';
  }

  function wireScreenshot() {
    var drop = $('bug-drop'), input = $('bug-file'), remove = $('bug-shot-remove');
    if (!drop || !input) return;
    var pick = function () { input.click(); };
    drop.addEventListener('click', pick);
    drop.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); pick(); }
    });
    input.addEventListener('change', function () {
      if (input.files && input.files[0]) acceptImage(input.files[0]);
    });
    ['dragenter', 'dragover'].forEach(function (evt) {
      drop.addEventListener(evt, function (e) {
        e.preventDefault(); drop.classList.add('over');
      });
    });
    ['dragleave', 'drop'].forEach(function (evt) {
      drop.addEventListener(evt, function (e) {
        e.preventDefault(); drop.classList.remove('over');
      });
    });
    drop.addEventListener('drop', function (e) {
      var files = e.dataTransfer && e.dataTransfer.files;
      if (files && files[0]) acceptImage(files[0]);
    });
    if (remove) remove.addEventListener('click', clearScreenshot);
  }

  /* ── submit ───────────────────────────────────────────────────────── */
  window.submitBugReport = function (event) {
    if (event) event.preventDefault();
    var btn = $('bug-send');
    var errBox = $('bug-error');
    var title = ($('bug-title') || {}).value || '';
    if (!title.trim()) {
      showError('Please add one line saying what went wrong.');
      return false;
    }
    var sevInput = document.querySelector('input[name="bug-severity"]:checked');
    var payload = {
      idem_key: _idemKey || (_idemKey = newIdemKey()),
      title: title.trim(),
      body: (($('bug-body') || {}).value || '').trim(),
      severity: sevInput ? sevInput.value : 'normal',
      email: (($('bug-email') || {}).value || '').trim(),
      surface: currentTab(),
      runtime: (typeof _cmRuntimeFilter === 'function' ? (_cmRuntimeFilter() || '') : ''),
      client: clientContext()
    };
    if (_screenshot) {
      payload.screenshot = _screenshot.dataUrl;
      payload.screenshot_name = _screenshot.name;
    }

    if (errBox) errBox.hidden = true;
    if (btn) { btn.disabled = true; btn.textContent = 'Sending…'; }

    fetch('/api/bug-report', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
      .then(function (r) {
        return r.json().catch(function () { return {}; }).then(function (j) {
          return { status: r.status, body: j };
        });
      })
      .then(function (res) {
        if (btn) { btn.disabled = false; btn.textContent = 'Send report'; }
        if (!res.body || !res.body.ok) {
          showError(res.body && res.body.error
            ? res.body.error
            : 'We could not send that just now, so nothing was lost. '
              + 'Press Send report again in a minute.');
          return;
        }
        showReceipt(res.body, payload);
      })
      .catch(function () {
        if (btn) { btn.disabled = false; btn.textContent = 'Send report'; }
        showError('We could not reach ClawMetry, so nothing was sent. Check '
          + 'your connection and press Send report again. Your text is still here.');
      });
    return false;
  };

  function showError(msg) {
    var box = $('bug-error');
    if (!box) return;
    box.textContent = msg;
    box.hidden = false;
  }

  function showReceipt(body, sent) {
    var ticket = body.ticket || '';
    rememberTicket({
      ticket: ticket,
      title: sent.title,
      status: body.status || 'received',
      status_label: body.status_label || 'Received',
      at: Date.now()
    });
    var el = $('bug-ticket');
    if (el) el.textContent = ticket;
    var note = $('bug-receipt-note');
    if (note) {
      note.textContent = sent.email
        ? ('We emailed ' + sent.email + ' with this id, and we email again the '
           + 'moment it is fixed.')
        : 'You did not leave an address, so this id is the only way back to '
          + 'the report. Copy it somewhere safe.';
    }
    var link = $('bug-status-link');
    if (link) link.href = body.status_url || ('https://app.clawmetry.com/bug/' + ticket);
    var form = $('bug-form'), receipt = $('bug-receipt');
    if (form) form.hidden = true;
    if (receipt) receipt.hidden = false;
    renderMyReports();
  }

  window.copyBugTicket = function () {
    var el = $('bug-ticket'), btn = $('bug-copy');
    if (!el) return;
    var done = function () {
      if (btn) {
        btn.textContent = 'Copied';
        setTimeout(function () { btn.textContent = 'Copy'; }, 1800);
      }
    };
    try {
      navigator.clipboard.writeText(el.textContent.trim()).then(done, done);
    } catch (e) { done(); }
  };

  window.resetBugForm = function () {
    var form = $('bug-form'), receipt = $('bug-receipt');
    if (form) {
      form.hidden = false;
      form.reset();
      var count = $('bug-title-count'); if (count) count.textContent = '0';
      var bcount = $('bug-body-count'); if (bcount) bcount.textContent = '0';
      syncSeverity();
    }
    if (receipt) receipt.hidden = true;
    clearScreenshot();
    var errBox = $('bug-error'); if (errBox) errBox.hidden = true;
    _idemKey = newIdemKey();
    var title = $('bug-title'); if (title) title.focus();
  };

  /* ── earlier reports from this browser ────────────────────────────── */
  function renderMyReports() {
    var wrap = $('bug-mine'), list = $('bug-mine-list');
    if (!wrap || !list) return;
    var tickets = readTickets();
    if (!tickets.length) { wrap.hidden = true; return; }
    wrap.hidden = false;
    list.innerHTML = '';
    tickets.forEach(function (t) {
      var li = document.createElement('li');
      li.className = 'bug-mine-item';
      var id = document.createElement('span');
      id.className = 'bug-mine-id';
      id.textContent = t.ticket;
      var title = document.createElement('span');
      title.className = 'bug-mine-label';
      title.textContent = t.title || '';
      var status = document.createElement('span');
      status.className = 'bug-mine-status';
      status.setAttribute('data-status', t.status || 'received');
      status.textContent = t.status_label || 'Received';
      li.appendChild(id); li.appendChild(title); li.appendChild(status);
      list.appendChild(li);
      refreshTicket(t, status);
    });
  }

  /* Re-read each remembered ticket's status so a fix that landed last week
     shows up here without the user asking. */
  function refreshTicket(rec, statusEl) {
    if (!rec || !rec.ticket) return;
    fetch('/api/bug-report/' + encodeURIComponent(rec.ticket))
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (j) {
        if (!j || !j.ok || !j.report) return;
        var rep = j.report;
        if (statusEl) {
          statusEl.textContent = rep.status_label || 'Received';
          statusEl.setAttribute('data-status', rep.status || 'received');
        }
        var list = readTickets().map(function (t) {
          if (t.ticket !== rec.ticket) return t;
          t.status = rep.status;
          t.status_label = rep.status_label;
          return t;
        });
        writeTickets(list);
      })
      .catch(function () { /* offline: the stored label stays as it was */ });
  }

  /* ── keep the nav inside the window ───────────────────────────────────
   * The sidebar is sticky at top:56px and sized 100vh-56px, but a banner
   * above the shell moves its real top without changing its height, so the
   * bottom of the nav ends up below the fold -- including the pinned Report
   * a bug entry, and the last tab in the list. Measure the real offset and
   * publish it as --cm-nav-top; the stylesheet falls back to 56px, so a
   * browser that never runs this is no worse off than before. */
  function syncNavTop() {
    var nav = document.getElementById('left-nav');
    if (!nav) return;
    var top = Math.max(0, Math.round(nav.getBoundingClientRect().top + window.scrollY));
    document.documentElement.style.setProperty('--cm-nav-top', top + 'px');
  }

  function watchNavTop() {
    syncNavTop();
    window.addEventListener('resize', syncNavTop);
    // Banners appear and are dismissed long after load.
    try {
      var shell = document.querySelector('.app-shell');
      if (shell && window.ResizeObserver) {
        new ResizeObserver(syncNavTop).observe(document.body);
      }
    } catch (e) { /* older browser: the resize listener still covers most of it */ }
  }

  /* ── severity selection ───────────────────────────────────────────── */
  function syncSeverity() {
    var rows = document.querySelectorAll('.bug-sev');
    Array.prototype.forEach.call(rows, function (row) {
      var input = row.querySelector('input[type="radio"]');
      if (input && input.checked) row.setAttribute('data-checked', '');
      else row.removeAttribute('data-checked');
    });
  }
  window._cmSyncBugSeverity = syncSeverity;

  /* ── character counters ───────────────────────────────────────────── */
  document.addEventListener('DOMContentLoaded', function () {
    watchNavTop();
    wireScreenshot();
    var sevInputs = document.querySelectorAll('input[name="bug-severity"]');
    Array.prototype.forEach.call(sevInputs, function (input) {
      input.addEventListener('change', syncSeverity);
    });
    syncSeverity();
    [['bug-title', 'bug-title-count'], ['bug-body', 'bug-body-count']]
      .forEach(function (pair) {
        var input = $(pair[0]), out = $(pair[1]);
        if (!input || !out) return;
        input.addEventListener('input', function () {
          out.textContent = String(input.value.length);
        });
      });
  });
})();
