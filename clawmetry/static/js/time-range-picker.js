/*
 * Grafana-style date/time range picker.
 *
 * A drop-in, self-contained component used by the Activity (brain) and
 * Sessions (transcripts) screens to pick a live/quick/absolute time window
 * without wrestling with the native <input type="datetime-local"> UX.
 *
 * Public API:
 *   window.cmTimeRangePicker.mount(container, {
 *     showLive: true,           // include the ● Live option
 *     initial: 'live' | seconds | {since, until},
 *     onChange: function(range){ ... }
 *   })
 *
 * Range object passed to onChange:
 *   { mode:'live' }
 *   { mode:'quick',    seconds, since, until, label }
 *   { mode:'absolute',          since, until, label }
 */
(function () {
  'use strict';

  var QUICK_RANGES = [
    { label: 'Last 5 minutes',  seconds: 5 * 60 },
    { label: 'Last 15 minutes', seconds: 15 * 60 },
    { label: 'Last 30 minutes', seconds: 30 * 60 },
    { label: 'Last 1 hour',     seconds: 60 * 60 },
    { label: 'Last 3 hours',    seconds: 3 * 3600 },
    { label: 'Last 6 hours',    seconds: 6 * 3600 },
    { label: 'Last 12 hours',   seconds: 12 * 3600 },
    { label: 'Last 24 hours',   seconds: 24 * 3600 },
    { label: 'Last 2 days',     seconds: 2 * 86400 },
    { label: 'Last 7 days',     seconds: 7 * 86400 },
    { label: 'Last 30 days',    seconds: 30 * 86400 },
    { label: 'Last 90 days',    seconds: 90 * 86400 }
  ];

  function pad(n) { return (n < 10 ? '0' : '') + n; }

  function fmtLocalDatetimeInput(d) {
    return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate()) +
           'T' + pad(d.getHours()) + ':' + pad(d.getMinutes());
  }

  function fmtHuman(d) {
    // "Aug 12, 14:37" for compact display; year only when not this year.
    var now = new Date();
    var opts = { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' };
    if (d.getFullYear() !== now.getFullYear()) opts.year = 'numeric';
    try { return d.toLocaleString(undefined, opts); }
    catch (e) { return d.toISOString(); }
  }

  function quickLabelForSeconds(s) {
    for (var i = 0; i < QUICK_RANGES.length; i++) {
      if (QUICK_RANGES[i].seconds === s) return QUICK_RANGES[i].label;
    }
    // Fall back to a human-ish duration for arbitrary seconds.
    if (s < 3600) return 'Last ' + Math.round(s / 60) + ' minutes';
    if (s < 86400) return 'Last ' + Math.round(s / 3600) + ' hours';
    return 'Last ' + Math.round(s / 86400) + ' days';
  }

  // Build the range object emitted to callers.
  function buildRange(mode, opts) {
    opts = opts || {};
    if (mode === 'live') return { mode: 'live' };
    if (mode === 'quick') {
      var now = new Date();
      var since = new Date(now.getTime() - opts.seconds * 1000);
      return {
        mode: 'quick',
        seconds: opts.seconds,
        since: since.toISOString(),
        until: now.toISOString(),
        label: quickLabelForSeconds(opts.seconds)
      };
    }
    if (mode === 'absolute') {
      var s = new Date(opts.since);
      var u = new Date(opts.until);
      return {
        mode: 'absolute',
        since: s.toISOString(),
        until: u.toISOString(),
        label: fmtHuman(s) + ' → ' + fmtHuman(u)
      };
    }
    return { mode: 'live' };
  }

  // Persist per-instance selection so revisits feel sticky.
  function keyFor(name) { return 'cm-timerange:' + (name || 'default'); }
  function saveState(name, state) {
    try { localStorage.setItem(keyFor(name), JSON.stringify(state)); } catch (e) {}
  }
  function loadState(name) {
    try {
      var raw = localStorage.getItem(keyFor(name));
      return raw ? JSON.parse(raw) : null;
    } catch (e) { return null; }
  }

  function mount(container, options) {
    options = options || {};
    var name = options.name || (container.id || 'default');
    var showLive = options.showLive !== false;
    var initial = options.initial != null ? options.initial : (showLive ? 'live' : 60 * 60);
    var onChange = options.onChange || function () {};

    // State kept on the DOM node so callers can inspect via .getRange()
    var state = { mode: 'live', seconds: null, since: null, until: null, label: 'Live' };

    // Root markup.
    container.classList.add('cm-tr');
    container.innerHTML = ''
      + '<button type="button" class="cm-tr-trigger" aria-haspopup="dialog" aria-expanded="false">'
      +   '<svg class="cm-tr-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>'
      +   '<span class="cm-tr-trigger-label">Live</span>'
      +   '<svg class="cm-tr-caret" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="6 9 12 15 18 9"/></svg>'
      + '</button>'
      + '<div class="cm-tr-pop" role="dialog" aria-label="Select time range" hidden>'
      +   '<div class="cm-tr-pop-cols">'
      +     '<div class="cm-tr-abs">'
      +       '<div class="cm-tr-h">Absolute time range</div>'
      +       '<label class="cm-tr-l">From'
      +         '<input type="datetime-local" class="cm-tr-from" step="60">'
      +       '</label>'
      +       '<label class="cm-tr-l">To'
      +         '<input type="datetime-local" class="cm-tr-to" step="60">'
      +       '</label>'
      +       '<button type="button" class="cm-tr-apply">Apply time range</button>'
      +       '<div class="cm-tr-hint">Times are in your local timezone.</div>'
      +     '</div>'
      +     '<div class="cm-tr-quick">'
      +       '<div class="cm-tr-h">Quick ranges</div>'
      +       '<div class="cm-tr-quick-list" role="listbox"></div>'
      +     '</div>'
      +   '</div>'
      + '</div>';

    var trigger = container.querySelector('.cm-tr-trigger');
    var triggerLabel = container.querySelector('.cm-tr-trigger-label');
    var pop = container.querySelector('.cm-tr-pop');
    var fromInput = container.querySelector('.cm-tr-from');
    var toInput = container.querySelector('.cm-tr-to');
    var applyBtn = container.querySelector('.cm-tr-apply');
    var quickList = container.querySelector('.cm-tr-quick-list');

    // Fill quick-ranges panel (+ Live at top if requested).
    var quickHtml = '';
    if (showLive) {
      quickHtml += '<button type="button" class="cm-tr-quick-item cm-tr-live" data-live="1">'
                +    '<span class="cm-tr-live-dot"></span>Live · streaming'
                +  '</button>'
                +  '<div class="cm-tr-quick-sep"></div>';
    }
    QUICK_RANGES.forEach(function (r) {
      quickHtml += '<button type="button" class="cm-tr-quick-item" data-secs="' + r.seconds + '">'
                +    r.label
                +  '</button>';
    });
    quickList.innerHTML = quickHtml;

    function markActiveQuick() {
      var items = quickList.querySelectorAll('.cm-tr-quick-item');
      for (var i = 0; i < items.length; i++) items[i].classList.remove('active');
      if (state.mode === 'live') {
        var liveEl = quickList.querySelector('[data-live="1"]');
        if (liveEl) liveEl.classList.add('active');
      } else if (state.mode === 'quick' && state.seconds) {
        var q = quickList.querySelector('[data-secs="' + state.seconds + '"]');
        if (q) q.classList.add('active');
      }
    }

    function updateTriggerLabel() {
      triggerLabel.textContent = state.label || 'Live';
      trigger.classList.toggle('is-live', state.mode === 'live');
      trigger.classList.toggle('is-custom', state.mode === 'absolute');
      trigger.classList.toggle('is-quick', state.mode === 'quick');
    }

    function applyState(next, persist, notify) {
      state = next;
      updateTriggerLabel();
      markActiveQuick();
      if (persist !== false) {
        saveState(name, {
          mode: state.mode, seconds: state.seconds,
          since: state.since, until: state.until
        });
      }
      if (notify !== false) onChange(state);
    }

    function selectLive() {
      applyState(Object.assign(buildRange('live'), { label: 'Live' }), true, true);
      closePop();
    }

    function selectQuick(seconds) {
      var r = buildRange('quick', { seconds: seconds });
      applyState(r, true, true);
      closePop();
    }

    function selectAbsolute() {
      if (!fromInput.value || !toInput.value) return;
      var s = new Date(fromInput.value), u = new Date(toInput.value);
      if (isNaN(s.getTime()) || isNaN(u.getTime())) return;
      if (s.getTime() > u.getTime()) { var tmp = s; s = u; u = tmp; }
      var r = buildRange('absolute', { since: s, until: u });
      applyState(r, true, true);
      closePop();
    }

    function prefillAbsoluteInputs() {
      // Seed from current state so opening the picker while in a window
      // shows that window, not a stale "an hour ago → now".
      var now = new Date();
      var to = (state.mode !== 'live' && state.until) ? new Date(state.until) : now;
      var from;
      if (state.mode !== 'live' && state.since) from = new Date(state.since);
      else from = new Date(now.getTime() - 3600 * 1000);
      fromInput.value = fmtLocalDatetimeInput(from);
      toInput.value = fmtLocalDatetimeInput(to);
    }

    function openPop() {
      prefillAbsoluteInputs();
      pop.hidden = false;
      trigger.setAttribute('aria-expanded', 'true');
      // Position: fixed so it escapes overflow parents; anchor to trigger.
      positionPop();
      // Rebind outside-click on next tick so this same click doesn't close it.
      setTimeout(function () {
        document.addEventListener('mousedown', outsideClick, true);
        document.addEventListener('keydown', escKey, true);
        window.addEventListener('resize', positionPop);
        window.addEventListener('scroll', positionPop, true);
      }, 0);
    }

    function closePop() {
      pop.hidden = true;
      trigger.setAttribute('aria-expanded', 'false');
      document.removeEventListener('mousedown', outsideClick, true);
      document.removeEventListener('keydown', escKey, true);
      window.removeEventListener('resize', positionPop);
      window.removeEventListener('scroll', positionPop, true);
    }

    function positionPop() {
      var r = trigger.getBoundingClientRect();
      // Prefer aligning right edge; fall back to left if it would clip.
      pop.style.position = 'fixed';
      pop.style.top = (r.bottom + 6) + 'px';
      // Measure after making visible.
      pop.style.left = '0px';
      pop.style.visibility = 'hidden';
      var w = pop.offsetWidth;
      var right = r.right;
      var left = right - w;
      if (left < 8) left = Math.min(r.left, window.innerWidth - w - 8);
      if (left < 8) left = 8;
      pop.style.left = left + 'px';
      pop.style.visibility = '';
      // If it overflows bottom, flip above the trigger.
      var h = pop.offsetHeight;
      if (r.bottom + 6 + h > window.innerHeight - 8) {
        var top = r.top - 6 - h;
        if (top < 8) top = 8;
        pop.style.top = top + 'px';
      }
    }

    function outsideClick(ev) {
      if (pop.contains(ev.target) || trigger.contains(ev.target)) return;
      closePop();
    }
    function escKey(ev) { if (ev.key === 'Escape') { closePop(); trigger.focus(); } }

    // Trigger + quick-list wiring.
    trigger.addEventListener('click', function () {
      pop.hidden ? openPop() : closePop();
    });
    quickList.addEventListener('click', function (ev) {
      var btn = ev.target.closest('.cm-tr-quick-item');
      if (!btn) return;
      if (btn.getAttribute('data-live') === '1') { selectLive(); return; }
      var secs = parseInt(btn.getAttribute('data-secs'), 10);
      if (secs > 0) selectQuick(secs);
    });
    applyBtn.addEventListener('click', selectAbsolute);
    // Enter inside either date field also applies.
    [fromInput, toInput].forEach(function (el) {
      el.addEventListener('keydown', function (ev) {
        if (ev.key === 'Enter') { ev.preventDefault(); selectAbsolute(); }
      });
    });

    // Restore saved state, then honor explicit `initial` if the caller gave one.
    var restored = loadState(name);
    var start;
    if (restored) {
      if (restored.mode === 'live') start = buildRange('live');
      else if (restored.mode === 'quick' && restored.seconds) start = buildRange('quick', { seconds: restored.seconds });
      else if (restored.mode === 'absolute' && restored.since && restored.until) start = buildRange('absolute', { since: restored.since, until: restored.until });
    }
    if (!start) {
      if (initial === 'live') start = buildRange('live');
      else if (typeof initial === 'number') start = buildRange('quick', { seconds: initial });
      else if (initial && initial.since && initial.until) start = buildRange('absolute', { since: initial.since, until: initial.until });
      else start = buildRange('live');
    }
    if (start.mode === 'live') start.label = 'Live';
    // Apply without notifying so callers can subscribe after mount() and
    // then read the initial value themselves via getRange().
    applyState(start, false, false);

    // Public per-instance API.
    var api = {
      getRange: function () { return state; },
      setRange: function (next, notify) {
        var built;
        if (next === 'live') built = buildRange('live');
        else if (typeof next === 'number') built = buildRange('quick', { seconds: next });
        else if (next && next.since && next.until) built = buildRange('absolute', { since: next.since, until: next.until });
        else built = buildRange('live');
        if (built.mode === 'live') built.label = 'Live';
        applyState(built, true, notify !== false);
      },
      open: openPop,
      close: closePop
    };
    container._cmTimeRange = api;
    return api;
  }

  window.cmTimeRangePicker = { mount: mount, QUICK_RANGES: QUICK_RANGES };
})();
