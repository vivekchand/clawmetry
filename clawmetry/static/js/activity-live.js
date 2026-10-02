/* Shared persisted activity subscriptions. One bounded reader per active scope. */
(function () {
  'use strict';
  var feeds = new Map(), MAX_FEEDS = 8;
  function active(listener) {
    return !document.hidden && (!listener.tab || !window._cmCurrentTab || listener.tab === window._cmCurrentTab);
  }
  function interested(feed) { return Array.from(feed.listeners).some(active); }
  function notify(feed, page, error) {
    feed.listeners.forEach(function (listener) {
      if (active(listener)) listener.receive(page, error);
    });
  }
  function schedule(feed, delay) {
    clearTimeout(feed.timer); feed.timer = null;
    if (interested(feed)) feed.timer = setTimeout(function () { poll(feed); }, delay);
    else if (feed.abort) feed.abort.abort();
  }
  async function poll(feed) {
    if (feed.loading || !interested(feed)) return;
    feed.loading = true;
    feed.abort = new AbortController();
    var delay = window.CLOUD_MODE ? 15000 : 2000;
    try {
      var query = new URLSearchParams(feed.scope);
      query.set('limit', '100'); if (feed.cursor) query.set('cursor', feed.cursor);
      var response = await fetch('/api/activity?' + query.toString(), {signal:feed.abort.signal});
      if (!response.ok) throw new Error('unavailable');
      var page = await response.json();
      if (!page || page.available === false) throw new Error('unavailable');
      if (page.resync_required) {
        feed.cursor = null; feed.page = null; feed.buffer.clear(); feed.brainBuffer.clear();
        notify(feed, page, null); delay = 250;
      } else {
        // Never advance a cursor past rows no active consumer received.
        if (!interested(feed)) return;
        feed.cursor = page.cursor;
        (page.removed_ids || []).forEach(function (id) { feed.buffer.delete(id); feed.brainBuffer.delete(id); });
        (page.rows || []).forEach(function (row) {
          feed.buffer.delete(row.id); feed.buffer.set(row.id, row); feed.brainBuffer.delete(row.id);
        });
        while (feed.buffer.size > 500) feed.buffer.delete(feed.buffer.keys().next().value);
        (page.brain_events || []).forEach(function (row) { if (row.eventId) feed.brainBuffer.set(row.eventId, row); });
        while (feed.brainBuffer.size > 500) feed.brainBuffer.delete(feed.brainBuffer.keys().next().value);
        feed.page = page; feed.failures = 0;
        notify(feed, page, null);
        if (page.has_more) delay = 250;
      }
    } catch (error) {
      feed.failures = Math.min((feed.failures || 0) + 1, 5);
      delay = Math.min(60000, delay * Math.pow(2, feed.failures - 1));
      notify(feed, null, error);
    } finally {
      feed.loading = false; schedule(feed, delay);
    }
  }
  window.cmWatchActivity = function (scope, receive, tab) {
    var clean = {};
    ['node_id','runtime','session_id'].forEach(function (key) {
      if (scope[key] && scope[key] !== 'all') clean[key] = scope[key];
    });
    var key = JSON.stringify(clean), feed = feeds.get(key);
    if (!feed) {
      if (feeds.size >= MAX_FEEDS) {
        var removable = Array.from(feeds.entries()).find(function (entry) { return !entry[1].listeners.size && !entry[1].loading; });
        if (removable) feeds.delete(removable[0]);
        else { receive(null, new Error('too_many_views')); return function () {}; }
      }
      feed = {scope:clean, cursor:null, listeners:new Set(), buffer:new Map(), brainBuffer:new Map(), loading:false, timer:null};
      feeds.set(key, feed);
    }
    var listener = {receive:receive, tab:tab || window._cmCurrentTab};
    feed.listeners.add(listener);
    // A new consumer receives a fresh bounded preview. Returning to a view
    // keeps the replay cursor, but does not silently miss its cached rows.
    if (feed.page && active(listener)) {
      Promise.resolve().then(function () {
        if (!feed.listeners.has(listener) || !active(listener)) return;
        receive(Object.assign({}, feed.page, {mode:'bootstrap', from_cache:true, rows:Array.from(feed.buffer.values()), brain_events:Array.from(feed.brainBuffer.values())}), null);
      });
    }
    schedule(feed, 0);
    return function () {
      feed.listeners.delete(listener);
      if (!interested(feed)) { clearTimeout(feed.timer); feed.timer = null; if (feed.abort) feed.abort.abort(); }
    };
  };
  window.cmActivityVisibilityChanged = function () {
    feeds.forEach(function (feed) { schedule(feed, 0); });
  };
  document.addEventListener('visibilitychange', window.cmActivityVisibilityChanged);

  // Compatibility facade lets Brain and Flow share the same persisted reader
  // while keeping their existing display/event callbacks.
  window.cmActivityEventSource = function (scope) {
    var handlers = {}, connected = false, closed = false;
    var stream = {readyState:0, onmessage:null, onerror:null,
      addEventListener:function (name, callback) { (handlers[name] || (handlers[name]=[])).push(callback); }};
    function emit(name, data) {
      var event = {data:JSON.stringify(data)};
      (handlers[name] || []).forEach(function (callback) { callback(event); });
    }
    var stop = window.cmWatchActivity(scope || {}, function (page, error) {
      if (closed) return;
      if (error) { connected = false; stream.readyState = 0; if (stream.onerror) stream.onerror(error); return; }
      if (page.resync_required) { emit('resync', page); return; }
      if (!connected && !page.from_cache) { connected = true; stream.readyState = 1; emit('connected', {source:'persisted'}); }
      (page.brain_events || []).forEach(function (row) {
        if (stream.onmessage) stream.onmessage({data:JSON.stringify(row)});
      });
      emit('checkpoint', {cursor:page.cursor});
    });
    stream.close = function () { closed = true; stream.readyState = 2; stop(); };
    return stream;
  };
}());
