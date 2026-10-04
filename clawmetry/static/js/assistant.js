/* ClawMetry Assistant. The module owns only this surface and exposes the two
 * integration hooks used by the host tab router. Generated content is always
 * inserted as text or rendered through Chart.js. */
(function () {
  'use strict';

  var MAX_MESSAGE = 4000;
  var MAX_PANEL_QUESTION = 1000;
  var SUGGESTIONS = [
    'Which agents were most effective today?',
    'How efficiently did agents manage their context?',
    'Could a cheaper model handle some of my work?',
    'Build a cost and effectiveness dashboard',
  ];
  var state = {
    initialized: false,
    mounted: false,
    conversationId: null,
    conversations: [],
    status: null,
    dataAvailable: null,
    dataStatusMessage: '',
    statusLoadedAt: 0,
    historyLoadedAt: 0,
    requests: [],
    chatRequest: null,
    voice: null,
    voiceActive: false,
    voiceBase: '',
    voiceFinal: '',
    voiceInterim: '',
    pendingNode: null,
    statusRequest: null,
    historyRequest: null,
    conversationRequest: null,
    checkoutRequest: null,
    navigationToken: 0,
    conversationReady: true,
    scopeIdentity: null,
    resettingScope: false,
  };

  function el(id) { return document.getElementById(id); }
  function page() { return el('page-assistant'); }
  function cloudTransportReady() {
    return !!(window._cmAssistantRelay && window._cmAssistantRelay.version === 1
      && typeof window._cmAssistantRelay.identity === 'function');
  }

  function scopeIdentity() {
    if (!window.CLOUD_MODE) return 'local';
    if (!cloudTransportReady()) return 'cloud-unavailable';
    try { return window._cmAssistantRelay.identity(); }
    catch (error) { return 'cloud-unavailable'; }
  }

  function resetScope(identity) {
    if (state.resettingScope) return;
    state.resettingScope = true;
    state.scopeIdentity = identity;
    state.navigationToken += 1;
    stopVoice();
    cancelChat('scope');
    cancelConversationRequest('scope');
    cancelAllRequests('scope');
    state.statusRequest = state.historyRequest = state.checkoutRequest = null;
    state.status = null;
    state.statusLoadedAt = state.historyLoadedAt = 0;
    state.conversationId = null;
    state.conversations = [];
    state.dataAvailable = false;
    state.dataStatusMessage = 'Checking the connection to your computer.';
    state.voiceBase = state.voiceFinal = state.voiceInterim = '';
    ['cm-assistant-api-key', 'cm-assistant-input'].forEach(function (id) {
      var input = el(id);
      if (input) input.value = '';
    });
    clearThread();
    renderHistory();
    clearRecovery();
    updateEngineOptions();
    renderManagedStatus();
    renderDataNotice({});
    renderSetupState();
    setConversationReady(false);
    setStatusPill('Checking connection', 'warning');
    setStatusMessage(state.dataStatusMessage, 'warning');
    state.resettingScope = false;
    if (state.mounted) Promise.resolve().then(function () {
      if (state.mounted && state.scopeIdentity === identity) loadAssistantPage();
    });
  }

  function isMounted() {
    if (!(state.mounted && page())) return false;
    var identity = scopeIdentity();
    if (state.scopeIdentity !== null && state.scopeIdentity !== identity) {
      resetScope(identity);
      return false;
    }
    return true;
  }

  function requestIsCurrent(request) {
    return isMounted() && request.scopeIdentity === scopeIdentity()
      && request.navigationToken === state.navigationToken;
  }

  function make(tag, className, text) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    if (text != null) node.textContent = String(text);
    return node;
  }

  function formatValue(value) {
    if (value == null) return 'Not measured';
    if (typeof value === 'number') {
      return Number.isFinite(value) ? value.toLocaleString(undefined, { maximumFractionDigits: 4 }) : 'Not measured';
    }
    if (typeof value === 'string' && /^-?(?:\d+\.\d+|\d+[eE][+-]?\d+)$/.test(value.trim())) {
      var numeric = Number(value);
      if (Number.isFinite(numeric)) return numeric.toLocaleString(undefined, { maximumFractionDigits: 4 });
    }
    if (typeof value === 'object') {
      try { return JSON.stringify(value); } catch (e) { return '[value]'; }
    }
    return String(value);
  }

  function formatCount(value) {
    var number = Number(value);
    return Number.isFinite(number) ? number.toLocaleString() : String(value == null ? 0 : value);
  }

  function displayCategory(value) {
    var raw = String(value == null ? '' : value);
    if (typeof window._cmRuntimeLabel === 'function') {
      try {
        var known = window._cmRuntimeLabel(raw);
        if (known && String(known) !== raw) return String(known);
      } catch (e) {}
    }
    if (window._CM_RT_LABEL && typeof window._CM_RT_LABEL === 'object' && window._CM_RT_LABEL[raw]) {
      return String(window._CM_RT_LABEL[raw]);
    }
    return raw.split(/[_-]+/).filter(Boolean).map(function (part) {
      return part.charAt(0).toUpperCase() + part.slice(1);
    }).join(' ') || raw;
  }

  function providerLabel(id) {
    var fallback = { auto: 'Automatic', claude_cli: 'Local harness', anthropic: 'Anthropic API key', managed: 'Managed assistant' };
    if (state.status && Array.isArray(state.status.providers)) {
      for (var i = 0; i < state.status.providers.length; i++) {
        var provider = state.status.providers[i];
        if (provider && provider.id === id) return provider.label || fallback[id] || id;
      }
    }
    return fallback[id] || id || 'Assistant engine';
  }

  function errorMessage(error, fallback) {
    if (error && error._assistantTimedOut) return 'The connection timed out. Check conversation history before retrying in case the answer was already saved.';
    if (error && error.name === 'AbortError') return 'Stop requested. Any answer already saved remains in your history.';
    var data = error && error.data;
    var status = error && error.status;
    if (data && data.error === 'no_auth') return 'No assistant engine is connected. Sign in to the local harness or add an Anthropic API key.';
    if (data && data.error === 'missing_api_key') return 'Add an Anthropic API key for this page, then try again.';
    var backendError = data && typeof data.error === 'string' ? data.error.trim() : '';
    if (backendError && backendError.length <= 600 && /\s/.test(backendError) && !/[<>\u0000-\u001f]/.test(backendError)) return backendError;
    if (status === 503 || (data && data.status === 503)) return 'The assistant is temporarily unavailable while ClawMetry reconnects to its local data store. Try again in a moment.';
    if (status === 401 || status === 403) return 'This assistant engine is not connected. Choose a local harness or add your own API key.';
    return fallback || 'The assistant could not complete that request. Try again.';
  }

  function removeRequest(request) {
    var index = state.requests.indexOf(request);
    if (index >= 0) state.requests.splice(index, 1);
  }

  function requestJson(url, options, timeoutMs, kind) {
    options = options || {};
    var controller = typeof AbortController !== 'undefined' ? new AbortController() : null;
    var request = { controller: controller, kind: kind || 'request', timedOut: false, cancelReason: null,
      scopeIdentity: scopeIdentity(), navigationToken: state.navigationToken };
    state.requests.push(request);
    var requestOptions = {};
    Object.keys(options).forEach(function (key) { requestOptions[key] = options[key]; });
    if (controller) requestOptions.signal = controller.signal;
    var timeoutReject = null;
    var timeoutPromise = controller ? null : new Promise(function (_, reject) {
      timeoutReject = reject;
    });
    var timer = setTimeout(function () {
      request.timedOut = true;
      if (controller) controller.abort();
      if (timeoutReject) {
        var timeoutError = new Error('assistant request timed out');
        timeoutError._assistantTimedOut = true;
        timeoutReject(timeoutError);
      }
    }, window.CLOUD_MODE ? 30000 : (timeoutMs || 15000));
    var fetchPromise = fetch(url, requestOptions)
      .then(function (response) {
        return response.text().then(function (body) {
          var data = {};
          try { data = body ? JSON.parse(body) : {}; } catch (e) { data = {}; }
          if (!response.ok) {
            var failure = new Error('assistant request failed');
            failure.status = response.status;
            failure.data = data;
            throw failure;
          }
          return data;
        });
      })
      .catch(function (error) {
        if (request.timedOut) error._assistantTimedOut = true;
        throw error;
      });
    var promise = (timeoutPromise ? Promise.race([fetchPromise, timeoutPromise]) : fetchPromise)
      .then(function (data) {
        clearTimeout(timer);
        removeRequest(request);
        return data;
      }, function (error) {
        clearTimeout(timer);
        removeRequest(request);
        throw error;
      });
    request.promise = promise;
    return request;
  }

  // Fetch supports POST + a request-scoped key; EventSource cannot send either.
  function requestStream(url, options, onEvent) {
    var controller = typeof AbortController !== 'undefined' ? new AbortController() : null;
    var request = { controller: controller, kind: 'chat', timedOut: false, cancelReason: null };
    state.requests.push(request);
    var reader = null;
    var timeoutReject;
    var timeoutPromise = new Promise(function (_, reject) { timeoutReject = reject; });
    var timer = setTimeout(function () {
      request.timedOut = true;
      if (controller) controller.abort();
      if (reader) reader.cancel().catch(function () {});
      var timeoutError = new Error('Assistant request timed out');
      timeoutError._assistantTimedOut = true;
      timeoutReject(timeoutError);
    }, 180000);
    options.signal = controller ? controller.signal : undefined;
    function failure(message) {
      var error = new Error(message);
      error.data = { error: message };
      return error;
    }
    request.cancelReader = function () {
      if (reader) reader.cancel().catch(function () {});
    };
    var fetchPromise = fetch(url, options).then(async function (response) {
      if (request.cancelReason || request.timedOut) {
        if (response.body && response.body.cancel) response.body.cancel().catch(function () {});
        var aborted = new Error('Aborted'); aborted.name = 'AbortError'; throw aborted;
      }
      if (!response.ok || !/text\/event-stream/i.test(response.headers.get('Content-Type') || '')) {
        var data = {};
        try { data = await response.json(); } catch (ignored) {}
        if (!response.ok) {
          var error = failure('The assistant request failed. Try again.');
          error.status = response.status;
          error.data = data;
          throw error;
        }
        // Older servers can still return their complete JSON response.
        if (typeof data.answer === 'string') return data;
        throw failure('Live replies are unavailable on this connection. Refresh and try again.');
      }
      if (!response.body || !response.body.getReader || typeof TextDecoder === 'undefined') {
        throw failure('This browser cannot receive live replies. Update your browser and try again.');
      }
      reader = response.body.getReader();
      var decoder = new TextDecoder('utf-8', { fatal: true });
      var buffer = '';
      var eventName = '';
      var lines = [];
      var totalBytes = 0;
      var result = null;
      function dispatch() {
        if (!lines.length) { eventName = ''; return; }
        var payload;
        try { payload = JSON.parse(lines.join('\n')); }
        catch (ignored) { throw failure('The live reply was interrupted. Refresh this conversation before trying again.'); }
        lines = [];
        var type = eventName || 'message';
        eventName = '';
        if (!payload || typeof payload !== 'object' || Array.isArray(payload)) {
          throw failure('The assistant sent an invalid live reply. Try again.');
        }
        if (type === 'error') {
          var streamError = failure(payload.error || 'The answer could not be completed. Try again.');
          streamError.data = payload;
          throw streamError;
        }
        if (type === 'done') {
          if (typeof payload.answer !== 'string' || !payload.conversation_id) {
            throw failure('The reply ended without a saved conversation. Try again.');
          }
          result = payload;
        } else if (type === 'status' || type === 'delta') {
          onEvent(type, payload);
        }
      }
      while (!result) {
        var chunk = await reader.read();
        if (request.cancelReason || request.timedOut) {
          var aborted = new Error('Aborted'); aborted.name = 'AbortError'; throw aborted;
        }
        if (chunk.done) break;
        totalBytes += chunk.value.byteLength;
        if (totalBytes > 2 * 1024 * 1024) throw failure('The live reply was too large. Ask a narrower question.');
        buffer += decoder.decode(chunk.value, { stream: true });
        var newline;
        while (!result && (newline = buffer.indexOf('\n')) !== -1) {
          var line = buffer.slice(0, newline).replace(/\r$/, '');
          buffer = buffer.slice(newline + 1);
          if (!line) dispatch();
          else if (line.indexOf('event:') === 0) eventName = line.slice(6).trim();
          else if (line.indexOf('data:') === 0) lines.push(line.slice(5).replace(/^ /, ''));
        }
      }
      if (!result) throw failure('The connection ended before the answer was saved. Refresh this conversation before trying again.');
      return result;
    }).finally(function () { request.cancelReader(); });
    request.promise = Promise.race([fetchPromise, timeoutPromise]).catch(function (error) {
      if (request.timedOut) error._assistantTimedOut = true;
      // The cloud decrypting reader can fail after HTTP headers arrived.
      // Preserve the same recovery contract as a non-2xx JSON response.
      if (!error.data && error.reason) error.data = {reason: error.reason, error: error.message};
      throw error;
    }).finally(function () {
      clearTimeout(timer);
      if (reader) reader.cancel().catch(function () {});
      removeRequest(request);
    });
    return request;
  }

  function cancelAllRequests(reason) {
    state.requests.slice().forEach(function (request) {
      request.cancelReason = reason || 'leave';
      if (request.controller) request.controller.abort();
    });
  }

  function setStatusMessage(message, tone) {
    var node = el('cm-assistant-status-message');
    if (!node) return;
    node.textContent = message || '';
    node.hidden = !message;
    node.className = 'cm-assistant-status-message' + (tone ? ' is-' + tone : '');
  }

  function setStatusPill(label, tone) {
    var pill = el('cm-assistant-status-pill');
    var labelNode = el('cm-assistant-status-label');
    if (labelNode) labelNode.textContent = label;
    if (pill) pill.className = 'cm-assistant-status-pill' + (tone ? ' is-' + tone : '');
  }

  function renderDataNotice(data) {
    var notice = el('cm-assistant-data-notice');
    if (!notice) return;
    var message = data && data.data_notice;
    notice.textContent = window.CLOUD_MODE && cloudTransportReady()
      ? 'Relevant query results go to your selected AI provider. Conversations and panels are available here and on your agent’s computer.'
      : (message || 'Relevant query results are sent to your selected AI provider.');
    notice.hidden = false;
  }

  function setupSuggestions() {
    var wrap = el('cm-assistant-suggestions');
    if (!wrap) return;
    while (wrap.firstChild) wrap.removeChild(wrap.firstChild);
    SUGGESTIONS.forEach(function (question) {
      var button = make('button', 'cm-assistant-suggestion', question);
      button.type = 'button';
      button.addEventListener('click', function () {
        var input = el('cm-assistant-input');
        if (!input) return;
        input.value = question;
        resizeInput();
        input.focus();
        setStatusMessage('Question ready. Review it, then press Send.', 'success');
      });
      wrap.appendChild(button);
    });
  }

  function renderSetupState() {
    var title = el('cm-assistant-setup-title');
    var description = el('cm-assistant-setup-description');
    if (!title || !description) return;
    var setup = el('cm-assistant-setup');
    if (setup) setup.classList.toggle('is-ready', !!(state.status && state.status.available && state.dataAvailable !== false));
    if (state.dataAvailable === false) {
      title.textContent = state.status && state.status.egress_suppressed ? 'External inference is disabled'
        : (window.CLOUD_MODE ? 'Connect to your computer' : 'Open your local dashboard');
      description.textContent = state.dataStatusMessage || 'This assistant needs the local data store on your agent’s computer.';
    } else if (state.status && state.status.available) {
      title.textContent = 'Good questions to start with';
      description.textContent = 'Ask for a finding or have me build a panel for Home.';
    } else {
      title.textContent = 'Connect an engine to begin';
      description.textContent = 'Use the local harness, or add an Anthropic key for this page only.';
    }
  }

  function updateEngineOptions() {
    var select = el('cm-assistant-engine');
    if (!select) return;
    var availability = {};
    if (state.status && Array.isArray(state.status.providers)) {
      state.status.providers.forEach(function (provider) {
        if (provider && provider.id) availability[provider.id] = !!provider.available;
      });
    }
    Array.prototype.forEach.call(select.options, function (option) {
      if (option.value === 'claude_cli') {
        option.disabled = state.status ? availability.claude_cli === false : false;
        option.textContent = providerLabel('claude_cli') + (option.disabled ? ' · unavailable' : '');
      }
      if (option.value === 'anthropic') {
        option.disabled = false;
        option.textContent = providerLabel('anthropic');
      }
      if (option.value === 'managed') {
        var managed = state.status && state.status.managed;
        option.disabled = !(managed && managed.available === true && availability.managed === true);
        option.textContent = providerLabel('managed') + (option.disabled ? ' · unavailable' : '');
      }
    });
    if (select.value === 'managed' && select.options[select.selectedIndex] && select.options[select.selectedIndex].disabled) {
      select.value = 'auto';
    }
    var keyRow = el('cm-assistant-key-row');
    if (keyRow) keyRow.hidden = select.value !== 'anthropic';
  }

  function isHttpsUrl(value) {
    var raw = String(value || '').trim();
    if (!/^https:\/\//i.test(raw)) return false;
    try {
      var parsed = new URL(raw);
      return parsed.protocol === 'https:' && !!parsed.hostname;
    } catch (e) {
      return false;
    }
  }

  function managedIsAvailable() {
    var managed = state.status && state.status.managed;
    if (!managed || managed.available !== true || !Array.isArray(state.status.providers)) return false;
    return state.status.providers.some(function (provider) {
      return provider && provider.id === 'managed' && provider.available === true;
    });
  }

  function formatCents(value) {
    var cents = Number(value);
    if (!Number.isFinite(cents) || cents < 0) return '';
    return '$' + (cents / 100).toFixed(2);
  }

  function renderManagedStatus() {
    var copy = el('cm-assistant-managed-copy');
    var link = el('cm-assistant-managed-link');
    var meta = el('cm-assistant-managed-meta');
    var balance = el('cm-assistant-managed-balance');
    var starter = el('cm-assistant-managed-starter');
    var topup = el('cm-assistant-managed-topup');
    if (!copy || !link || !meta || !balance || !starter || !topup) return;
    var managed = state.status && state.status.managed;
    var available = managedIsAvailable();
    if (available) {
      copy.textContent = managed.message || 'Managed assistant access is connected for this workspace.';
      link.textContent = 'Open managed assistant';
    } else {
      copy.textContent = (managed && managed.message) || 'Managed assistant access is not connected here yet. Use a local harness or your own API key.';
      link.textContent = 'Learn about managed access';
    }
    var url = managed && managed.url && isHttpsUrl(managed.url) ? String(managed.url) : 'https://build.clawmetry.com/';
    link.href = url;

    var balanceText = formatCents(managed && managed.balance_cents);
    var starterText = formatCents(managed && managed.starter_allowance_cents);
    meta.hidden = !available || !balanceText;
    balance.textContent = balanceText ? 'Verified balance ' + balanceText : '';
    starter.hidden = !available || !starterText;
    starter.textContent = starterText ? 'Starter allowance ' + starterText : '';
    topup.hidden = !available || managed.checkout_available !== true;
    topup.disabled = !available || managed.checkout_available !== true || !!state.checkoutRequest;
  }

  function startManagedCheckout() {
    if (!managedIsAvailable()) {
      setStatusMessage('Managed assistant access is not available yet. Choose another engine or learn about managed access.', 'warning');
      return;
    }
    var managed = state.status && state.status.managed;
    if (!managed || managed.checkout_available !== true || state.checkoutRequest) return;
    var topup = el('cm-assistant-managed-topup');
    if (topup) {
      topup.disabled = true;
      topup.textContent = 'Opening checkout...';
    }
    setStatusMessage('Preparing secure checkout for $5.00...', 'success');
    var request = requestJson('/api/assistant/credits/checkout', {
      method: 'POST',
      credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ amount_cents: 500 }),
    }, 20000, 'managed-checkout');
    state.checkoutRequest = request;
    request.promise.then(function (data) {
      if (state.checkoutRequest !== request || !requestIsCurrent(request)) return;
      state.checkoutRequest = null;
      var url = data && data.url;
      if (!isHttpsUrl(url)) {
        if (topup) { topup.disabled = false; topup.textContent = 'Add $5 credit'; }
        setStatusMessage('Checkout could not open because the backend did not return a secure HTTPS URL.', 'error');
        return;
      }
      window.location.assign(String(url));
    }).catch(function (error) {
      if (state.checkoutRequest !== request || !requestIsCurrent(request)) return;
      state.checkoutRequest = null;
      if (topup) { topup.disabled = false; topup.textContent = 'Add $5 credit'; }
      if (!isMounted()) return;
      setStatusMessage(errorMessage(error, 'Checkout could not be started. Try again.'), 'error');
    });
  }

  function loadStatus() {
    if (state.statusRequest) return;
    if (window.CLOUD_MODE && !cloudTransportReady()) {
      state.status = { available: false, data_available: false };
      state.dataAvailable = false;
      state.dataStatusMessage = 'The cloud connection to your computer is unavailable. Refresh this page to reconnect Assistant.';
      state.statusLoadedAt = Date.now();
      setConversationReady(false);
      setStatusPill('Connection unavailable', 'warning');
      setStatusMessage(state.dataStatusMessage, 'warning');
      renderDataNotice({});
      renderSetupState();
      ['cm-assistant-input', 'cm-assistant-engine', 'cm-assistant-voice', 'cm-assistant-new-chat'].forEach(function (id) {
        var control = el(id);
        if (control) control.disabled = true;
      });
      var billing = el('cm-assistant-managed-note');
      if (billing) billing.hidden = true;
      renderRecovery({});
      return;
    }
    ['cm-assistant-input', 'cm-assistant-engine', 'cm-assistant-voice', 'cm-assistant-new-chat'].forEach(function (id) {
      var control = el(id);
      if (control) control.disabled = false;
    });
    var billing = el('cm-assistant-managed-note');
    if (billing) billing.hidden = false;
    if (window.CLOUD_MODE && !state.statusLoadedAt) {
      state.dataAvailable = false;
      setConversationReady(false);
      setStatusPill('Connecting to your computer');
    }
    var request = requestJson('/api/assistant/status', { credentials: 'same-origin' }, 12000, 'status');
    state.statusRequest = request;
    request.promise.then(function (data) {
      // Status belongs to the node, not the selected conversation. Starting a
      // new chat while connecting must not discard its readiness response.
      if (state.statusRequest !== request || !isMounted() || request.scopeIdentity !== scopeIdentity()) return;
      state.statusRequest = null;
      state.status = data || {};
      state.dataAvailable = state.status.data_available !== false && !state.status.egress_suppressed;
      state.dataStatusMessage = state.status.message || '';
      setConversationReady(!state.conversationRequest);
      state.statusLoadedAt = Date.now();
      var ready = !!state.status.available;
      var provider = state.status.provider ? providerLabel(state.status.provider) : '';
      if (state.dataAvailable === false) {
        setStatusPill(state.status.egress_suppressed ? 'External inference disabled'
          : (window.CLOUD_MODE ? 'Connection needs attention' : 'Local data unavailable'), 'warning');
        setStatusMessage(state.dataStatusMessage || 'Local ClawMetry data is unavailable. Reconnect the local store before asking the assistant.', 'warning');
      } else {
        setStatusPill(ready ? 'Ready' + (provider ? ' · ' + provider : '') : 'Connect an engine', ready ? '' : 'warning');
      }
      var scope = el('cm-assistant-scope');
      if (scope) scope.textContent = state.status.scope || 'All runtimes on this node';
      renderDataNotice(state.status);
      renderSetupState();
      updateEngineOptions();
      renderManagedStatus();
      if (state.dataAvailable === false) renderRecovery(state.status);
      else clearRecovery();
    }).catch(function (error) {
      if (state.statusRequest !== request || !isMounted() || request.scopeIdentity !== scopeIdentity()) return;
      state.statusRequest = null;
      if (error && error.name === 'AbortError' && request.cancelReason) return;
      state.statusLoadedAt = 0;
      if (window.CLOUD_MODE) {
        state.dataAvailable = false;
        state.dataStatusMessage = errorMessage(error, 'Could not connect to your computer. Try again.');
        setConversationReady(false);
      }
      setStatusPill('Status unavailable', 'warning');
      renderDataNotice({});
      renderSetupState();
      setStatusMessage(errorMessage(error, 'Assistant status is temporarily unavailable. You can still try a request.'), 'error');
      renderRecovery(error && error.data);
    });
  }

  function clearRecovery() {
    var recovery = el('cm-assistant-recovery');
    if (!recovery) return;
    while (recovery.firstChild) recovery.firstChild.remove();
    recovery.hidden = true;
  }

  function renderRecovery(data) {
    var recovery = el('cm-assistant-recovery');
    if (!recovery) return;
    clearRecovery();
    recovery.hidden = false;
    var identity = scopeIdentity();
    var navigationToken = state.navigationToken;
    function retry() {
      if (!isMounted() || navigationToken !== state.navigationToken || identity !== scopeIdentity()) return;
      state.statusLoadedAt = state.historyLoadedAt = 0;
      loadStatus();
      loadHistory(true);
    }
    if (window.CLOUD_MODE && data && (data.reason === 'missing_key' || data.reason === 'decrypt_failed')
        && typeof window._cmRenderKeyPrompt === 'function') {
      var unlock = make('div');
      recovery.appendChild(unlock);
      window._cmRenderKeyPrompt(unlock, { title: 'Unlock Assistant', onUnlock: function () {
        if (!state.mounted || navigationToken !== state.navigationToken) return;
        var current = scopeIdentity();
        if (current !== state.scopeIdentity) resetScope(current);
        else retry();
      } });
    }
    var button = make('button', 'cm-assistant-panel-button', 'Retry connection');
    button.type = 'button';
    button.addEventListener('click', retry);
    recovery.appendChild(button);
  }

  function renderChatRecovery(error, request) {
    if (!requestIsCurrent(request)) return;
    var data = error && error.data;
    if (window.CLOUD_MODE && data && (data.reason === 'missing_key' || data.reason === 'decrypt_failed')) {
      state.dataAvailable = false;
      state.statusLoadedAt = 0;
      setConversationReady(false);
      setStatusPill('Unlock Assistant', 'warning');
      renderRecovery(data);
      return;
    }
    var recovery = el('cm-assistant-recovery');
    if (!recovery) return;
    clearRecovery();
    recovery.hidden = false;
    recovery.appendChild(make('p', '', 'An answer may already have been saved. Check history before sending the question again.'));
    var refresh = make('button', 'cm-assistant-panel-button', 'Refresh conversation history');
    refresh.type = 'button';
    refresh.addEventListener('click', function () {
      if (!requestIsCurrent(request) || state.chatRequest) return;
      loadHistory(true);
    });
    recovery.appendChild(refresh);
    if (request.conversationId) {
      var reopen = make('button', 'cm-assistant-panel-button', 'Open saved conversation');
      reopen.type = 'button';
      reopen.addEventListener('click', function () {
        if (!requestIsCurrent(request) || state.chatRequest) return;
        loadConversation(request.conversationId);
      });
      recovery.appendChild(reopen);
    }
  }

  function relativeDate(value) {
    if (!value) return '';
    var date = new Date(value);
    if (isNaN(date.getTime())) {
      var numeric = Number(value);
      if (Number.isFinite(numeric)) date = new Date(numeric < 100000000000 ? numeric * 1000 : numeric);
    }
    if (isNaN(date.getTime())) return '';
    var seconds = Math.max(0, Math.floor((Date.now() - date.getTime()) / 1000));
    if (seconds < 60) return 'just now';
    if (seconds < 3600) return Math.floor(seconds / 60) + 'm ago';
    if (seconds < 86400) return Math.floor(seconds / 3600) + 'h ago';
    if (seconds < 604800) return Math.floor(seconds / 86400) + 'd ago';
    return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
  }

  function renderHistory() {
    var list = el('cm-assistant-history-list');
    if (!list) return;
    while (list.firstChild) list.removeChild(list.firstChild);
    if (!state.conversations.length) {
      list.appendChild(make('div', 'cm-assistant-history-empty', 'Your saved conversations will appear here.'));
      return;
    }
    state.conversations.forEach(function (conversation) {
      var button = make('button', 'cm-assistant-history-item');
      button.type = 'button';
      if (conversation.id === state.conversationId) button.classList.add('is-active');
      button.appendChild(make('span', 'cm-assistant-history-title', conversation.title || 'Untitled conversation'));
      button.appendChild(make('span', 'cm-assistant-history-date', relativeDate(conversation.updated_at)));
      button.addEventListener('click', function () { loadConversation(conversation.id); });
      list.appendChild(button);
    });
  }

  function loadHistory(force) {
    if (window.CLOUD_MODE && !cloudTransportReady()) {
      var history = el('cm-assistant-history-list');
      if (history) history.textContent = 'Reconnect to your computer to load saved conversations.';
      return;
    }
    if (state.historyRequest) return;
    if (!force && state.historyLoadedAt && Date.now() - state.historyLoadedAt < 30000) {
      renderHistory();
      return;
    }
    var request = requestJson('/api/assistant/conversations', { credentials: 'same-origin' }, 15000, 'history');
    state.historyRequest = request;
    request.promise.then(function (data) {
      if (state.historyRequest !== request || !isMounted() || request.scopeIdentity !== scopeIdentity()) return;
      state.historyRequest = null;
      state.conversations = Array.isArray(data && data.conversations) ? data.conversations : [];
      state.historyLoadedAt = Date.now();
      renderHistory();
    }).catch(function (error) {
      if (state.historyRequest !== request || !isMounted() || request.scopeIdentity !== scopeIdentity()) return;
      state.historyRequest = null;
      if (error && error.name === 'AbortError' && request.cancelReason) return;
      var list = el('cm-assistant-history-list');
      if (!list) return;
      while (list.firstChild) list.removeChild(list.firstChild);
      list.appendChild(make('div', 'cm-assistant-history-empty', 'Conversation history is unavailable right now.'));
    });
  }

  function destroyCharts() {
    destroyChartsIn(el('cm-assistant-thread'));
  }

  function destroyChartsIn(container) {
    if (!container) return;
    var charts = container.querySelectorAll('.cm-assistant-chart-wrap canvas');
    Array.prototype.forEach.call(charts, function (canvas) {
      try {
        var chart = canvas._cmAssistantChart || (window.Chart && window.Chart.getChart ? window.Chart.getChart(canvas) : null);
        if (chart) chart.destroy();
        canvas._cmAssistantChart = null;
      } catch (e) {}
    });
  }

  function clearThread() {
    destroyCharts();
    var thread = el('cm-assistant-thread');
    var main = page() && page().querySelector('.cm-assistant-main');
    if (main) main.classList.remove('has-messages');
    var title = el('cm-assistant-title');
    if (title) title.textContent = 'How can I help?';
    if (!thread) return;
    while (thread.firstChild) thread.removeChild(thread.firstChild);
  }

  function showWelcome() {
    // The heading and composer are the single opening state.
    var main = page() && page().querySelector('.cm-assistant-main');
    if (main) main.classList.remove('has-messages');
  }

  function setAnswerText(container, content) {
    // Render only emphasis and inline code. Model output never becomes HTML.
    container.textContent = '';
    var source = String(content || '');
    var pattern = /\*\*([^\n*]+)\*\*|`([^\n`]+)`/g;
    var offset = 0;
    var match;
    while ((match = pattern.exec(source))) {
      container.appendChild(make('span', '', source.slice(offset, match.index)));
      container.appendChild(make(match[1] !== undefined ? 'strong' : 'code', '', match[1] !== undefined ? match[1] : match[2]));
      offset = pattern.lastIndex;
    }
    container.appendChild(make('span', '', source.slice(offset)));
  }

  function addMessage(role, content) {
    var thread = el('cm-assistant-thread');
    var main = page() && page().querySelector('.cm-assistant-main');
    if (!thread) return null;
    var welcome = el('cm-assistant-welcome');
    if (welcome) welcome.remove();
    if (thread.querySelectorAll) {
      Array.prototype.forEach.call(thread.querySelectorAll('.cm-assistant-welcome'), function (node) { node.remove(); });
    }
    if (main) main.classList.add('has-messages');
    var title = el('cm-assistant-title');
    if (title) title.textContent = 'ClawMetry assistant';
    resizeInput();
    var article = make('article', 'cm-assistant-message ' + (role === 'user' ? 'is-user' : 'is-assistant'));
    var avatar = make('div', 'cm-assistant-avatar', role === 'user' ? 'You' : '✦');
    avatar.setAttribute('aria-hidden', 'true');
    var body = make('div', 'cm-assistant-message-body');
    body.appendChild(make('div', 'cm-assistant-message-label' + (role === 'user' ? ' cm-assistant-sr-only' : ''), role === 'user' ? 'You' : 'ClawMetry'));
    var text = make('div', 'cm-assistant-message-content', content || '');
    if (role !== 'user') setAnswerText(text, content);
    body.appendChild(text);
    article.appendChild(avatar);
    article.appendChild(body);
    thread.appendChild(article);
    return { article: article, body: body, content: text };
  }

  function appendTable(container, rows, limit) {
    if (!Array.isArray(rows) || !rows.length) {
      container.appendChild(make('div', 'cm-assistant-empty-data', 'No matching data was available for this panel. That does not prove that nothing happened.'));
      return;
    }
    var normalized = rows.map(function (row) {
      return row && typeof row === 'object' && !Array.isArray(row) ? row : { value: row };
    });
    var columns = [];
    normalized.forEach(function (row) {
      Object.keys(row).forEach(function (key) {
        if (columns.indexOf(key) < 0 && columns.length < 16) columns.push(key);
      });
    });
    var runtimeIndex = columns.findIndex(function (column) { return column.toLowerCase() === 'runtime'; });
    if (runtimeIndex > 0) columns.unshift(columns.splice(runtimeIndex, 1)[0]);
    var wrap = make('div', 'cm-assistant-table-wrap');
    var table = make('table', 'cm-assistant-table');
    var head = make('thead');
    var headRow = make('tr');
    columns.forEach(function (column) { headRow.appendChild(make('th', '', displayCategory(column))); });
    head.appendChild(headRow);
    table.appendChild(head);
    var body = make('tbody');
    normalized.slice(0, limit || 100).forEach(function (row) {
      var tr = make('tr');
      columns.forEach(function (column) { tr.appendChild(make('td', '', column.toLowerCase() === 'runtime' && row[column] != null ? displayCategory(row[column]) : formatValue(row[column]))); });
      body.appendChild(tr);
    });
    table.appendChild(body);
    wrap.appendChild(table);
    container.appendChild(wrap);
    if (normalized.length > (limit || 100)) {
      container.appendChild(make('div', 'cm-assistant-panel-description', 'Showing the first ' + (limit || 100) + ' rows.'));
    }
  }

  function numericRows(rows, key) {
    return rows.every(function (row) {
      var value = row && typeof row === 'object' ? row[key] : row;
      return value !== '' && value != null && Number.isFinite(Number(value));
    });
  }

  function renderChart(container, spec, rows, panel) {
    var chartType = String(spec.chart_type || 'table').toLowerCase();
    if (chartType === 'number') {
      var numberRow = rows[0] && typeof rows[0] === 'object' ? rows[0] : { value: rows[0] };
      var numberKey = spec.y || Object.keys(numberRow)[0];
      container.appendChild(make('div', 'cm-assistant-number', numberRow[numberKey] == null || numberRow[numberKey] === '' ? 'Not measured' : formatValue(numberRow[numberKey])));
      container.appendChild(make('div', 'cm-assistant-number-label', numberKey || 'value'));
      return;
    }
    if (chartType === 'table' || !rows.length || typeof window.Chart !== 'function') {
      appendTable(container, rows);
      if (panel && chartType !== 'table' && typeof window.Chart !== 'function') panel._renderError = true;
      if (rows.length && chartType !== 'table' && typeof window.Chart !== 'function') {
        container.appendChild(make('div', 'cm-assistant-panel-description', 'Chart rendering is unavailable, so the data is shown as a table.'));
      }
      return;
    }
    if (['bar', 'line', 'pie'].indexOf(chartType) < 0) {
      appendTable(container, rows);
      if (panel) panel._renderError = true;
      return;
    }
    var first = rows[0] && typeof rows[0] === 'object' ? rows[0] : {};
    var xKey = spec.x || Object.keys(first)[0];
    var yKey = spec.y || Object.keys(first)[1] || Object.keys(first)[0];
    if (!xKey || !yKey || !numericRows(rows, yKey)) {
      appendTable(container, rows);
      if (panel) panel._renderError = true;
      container.appendChild(make('div', 'cm-assistant-panel-description', 'The returned values are not chartable, so the complete result is shown as a table.'));
      return;
    }
    var chartWrap = make('div', 'cm-assistant-chart-wrap');
    var canvas = document.createElement('canvas');
    canvas.setAttribute('role', 'img');
    canvas.setAttribute('aria-label', spec.title || 'Assistant chart');
    chartWrap.appendChild(canvas);
    container.appendChild(chartWrap);
    var limited = rows.slice(0, 80);
    var labels = limited.map(function (row) { return displayCategory(row[xKey]); });
    var values = limited.map(function (row) { return Number(row[yKey]); });
    var isPie = chartType === 'pie';
    var horizontal = chartType === 'bar' && (labels.length > 10 || labels.some(function (label) { return label.length > 16; }));
    var showAllLabels = labels.length <= 20;
    if (horizontal) chartWrap.style.height = Math.max(220, labels.length * 26) + 'px';
    var colors = ['#3b82f6', '#22c55e', '#f59e0b', '#f87171', '#06b6d4', '#a78bfa', '#ec4899'];
    var palette = getComputedStyle(page());
    var chartText = palette.getPropertyValue('--text-tertiary').trim();
    var chartGrid = palette.getPropertyValue('--border-secondary').trim();
    var chartAccent = palette.getPropertyValue('--bg-accent').trim();
    try {
      canvas._cmAssistantChart = new window.Chart(canvas, {
        type: chartType,
        data: {
          labels: labels,
          datasets: [{
            label: yKey,
            data: values,
            backgroundColor: isPie ? labels.map(function (_, index) { return colors[index % colors.length]; }) : chartAccent,
            borderColor: isPie ? colors : chartAccent,
            borderWidth: isPie ? 1 : 2,
            borderRadius: chartType === 'bar' ? 5 : 0,
            fill: chartType === 'line',
            tension: .28,
          }],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          indexAxis: horizontal ? 'y' : 'x',
          plugins: {
            legend: { display: isPie, labels: { color: chartText, padding: 14, usePointStyle: true } },
            tooltip: { bodyColor: '#f6f7fb', titleColor: '#f6f7fb', backgroundColor: '#19191d', borderColor: 'rgba(255,255,255,.12)', borderWidth: 1 },
          },
          scales: isPie ? {} : {
            x: { ticks: { color: chartText, autoSkip: horizontal ? false : !showAllLabels, maxTicksLimit: showAllLabels ? labels.length : 12, maxRotation: horizontal ? 0 : 45, minRotation: horizontal ? 0 : (labels.length > 10 ? 45 : 0) }, grid: { color: chartGrid } },
            y: { ticks: { color: chartText, autoSkip: horizontal ? false : !showAllLabels, maxTicksLimit: showAllLabels ? labels.length : 12 }, grid: { color: chartGrid } },
          },
        },
      });
    } catch (e) {
      if (panel) panel._renderError = true;
      while (container.firstChild) container.removeChild(container.firstChild);
      appendTable(container, rows);
      container.appendChild(make('div', 'cm-assistant-panel-description', 'The chart could not render, so the complete result is shown as a table.'));
    }
  }

  function panelType(spec) {
    var type = String(spec && spec.chart_type || 'table').toLowerCase();
    return ['bar', 'line', 'pie', 'table', 'number'].indexOf(type) >= 0 ? type : 'table';
  }

  function safeChartSpec(spec) {
    spec = spec && typeof spec === 'object' ? spec : {};
    var safe = { chart_type: panelType(spec) };
    ['x', 'y', 'title', 'description'].forEach(function (key) {
      if (spec[key] != null) safe[key] = String(spec[key]).slice(0, 500);
    });
    return safe;
  }

  function saveDashboardPanel(panel, question, name, confirm, feedback, row, trigger) {
    name = String(name || '').trim();
    if (!name) {
      feedback.textContent = 'Give this panel a name first.';
      feedback.className = 'cm-assistant-save-feedback is-error';
      return;
    }
    confirm.disabled = true;
    feedback.textContent = 'Saving to Home...';
    feedback.className = 'cm-assistant-save-feedback';
    var body = {
      name: name.slice(0, 120),
      question: String(question || '').slice(0, MAX_PANEL_QUESTION),
      sql: String(panel.sql || ''),
      chart_spec: safeChartSpec(panel.chart_spec),
    };
    var request = requestJson('/api/dashboard/panels', {
      method: 'POST',
      credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }, 20000, 'save-panel');
    request.promise.then(function () {
      if (!requestIsCurrent(request)) return;
      confirm.disabled = false;
      row.hidden = true;
      trigger.hidden = false;
      trigger.textContent = 'Saved to dashboard';
      trigger.disabled = true;
      feedback.textContent = 'Saved to Home dashboard.';
      feedback.className = 'cm-assistant-save-feedback is-success';
      var home = make('button', 'cm-assistant-panel-button', 'Open Home');
      home.type = 'button';
      home.addEventListener('click', function () {
        if (typeof window.switchTab === 'function') window.switchTab('overview');
      });
      feedback.parentNode.appendChild(home);
    }).catch(function (error) {
      if (!requestIsCurrent(request)) return;
      confirm.disabled = false;
      if (!isMounted()) return;
      feedback.textContent = errorMessage(error, 'The panel could not be saved. Try again.');
      feedback.className = 'cm-assistant-save-feedback is-error';
    });
  }

  function renderPanel(panel, question) {
    panel = panel || {};
    var spec = panel.chart_spec && typeof panel.chart_spec === 'object' ? panel.chart_spec : {};
    var rows = Array.isArray(panel.rows) ? panel.rows : [];
    var type = panelType(spec);
    var panelQuestion = panel.question || question || '';
    var article = make('article', 'cm-assistant-panel');
    var head = make('div', 'cm-assistant-panel-head');
    var titleWrap = make('div');
    titleWrap.appendChild(make('h3', 'cm-assistant-panel-title', spec.title || panel.title || 'Assistant panel'));
    if (spec.description) titleWrap.appendChild(make('p', 'cm-assistant-panel-description', spec.description));
    head.appendChild(titleWrap);
    head.appendChild(make('span', 'cm-assistant-panel-type', type));
    article.appendChild(head);
    var body = make('div', 'cm-assistant-panel-body');
    if (panel.error) body.appendChild(make('div', 'cm-assistant-panel-error', 'This panel could not be completed: ' + String(panel.error)));
    else if (!rows.length) body.appendChild(make('div', 'cm-assistant-empty-data', 'No recorded data matches this question.'));
    else renderChart(body, spec, rows, panel);
    article.appendChild(body);

    if (panel.sql) {
      var queryDetails = make('details', 'cm-assistant-query-details');
      queryDetails.appendChild(make('summary', '', 'Query used'));
      queryDetails.appendChild(make('pre', 'cm-assistant-query', String(panel.sql)));
      article.appendChild(queryDetails);
    }

    var footer = make('div', 'cm-assistant-panel-footer');
    var actions = make('div', 'cm-assistant-panel-actions');
    var chartButton = make('button', 'cm-assistant-panel-button', type === 'number' ? 'Number' : 'Chart');
    var tableButton = make('button', 'cm-assistant-panel-button', 'Table');
    chartButton.type = 'button';
    tableButton.type = 'button';
    chartButton.disabled = type === 'table' || !!panel.error || !rows.length || !!panel._renderError;
    tableButton.disabled = !!panel.error || !rows.length || !!panel._renderError;
    chartButton.setAttribute('aria-pressed', type !== 'table' && !panel.error && rows.length && !panel._renderError ? 'true' : 'false');
    tableButton.setAttribute('aria-pressed', type === 'table' && !panel.error && rows.length && !panel._renderError ? 'true' : 'false');
    actions.appendChild(chartButton);
    actions.appendChild(tableButton);
    var saveButton = make('button', 'cm-assistant-panel-button is-primary', 'Save to dashboard');
    saveButton.type = 'button';
    saveButton.disabled = !!panel.error || !rows.length || !!panel._renderError;
    actions.appendChild(saveButton);
    footer.appendChild(actions);
    var feedback = make('span', 'cm-assistant-save-feedback', panel._renderError ? 'Save is unavailable because this result could not render safely.' : (panel.truncated ? 'Showing a limited result. Narrow the question to see more detail.' : ''));
    footer.appendChild(feedback);
    article.appendChild(footer);

    var saveRow = make('div', 'cm-assistant-save-row');
    saveRow.hidden = true;
    var nameInput = document.createElement('input');
    nameInput.type = 'text';
    nameInput.maxLength = 120;
    nameInput.value = String(spec.title || panel.title || panelQuestion || 'Assistant panel').slice(0, 120);
    nameInput.setAttribute('aria-label', 'Dashboard panel name');
    var confirm = make('button', 'cm-assistant-panel-button is-primary', 'Save');
    var cancel = make('button', 'cm-assistant-panel-button', 'Cancel');
    confirm.type = 'button';
    cancel.type = 'button';
    saveRow.appendChild(nameInput);
    saveRow.appendChild(confirm);
    saveRow.appendChild(cancel);
    footer.appendChild(saveRow);

    function refreshView(view) {
      if (panel.error || !rows.length) return;
      destroyChartsIn(body);
      while (body.firstChild) body.removeChild(body.firstChild);
      if (view === 'table') appendTable(body, rows);
      else renderChart(body, spec, rows, panel);
      if (panel._renderError) {
        saveButton.disabled = true;
        feedback.textContent = 'Save is unavailable because this result could not render safely.';
        feedback.className = 'cm-assistant-save-feedback is-error';
      }
      chartButton.setAttribute('aria-pressed', view === 'chart' && !panel._renderError ? 'true' : 'false');
      tableButton.setAttribute('aria-pressed', view === 'table' && !panel._renderError ? 'true' : 'false');
    }
    chartButton.addEventListener('click', function () { refreshView('chart'); });
    tableButton.addEventListener('click', function () { refreshView('table'); });
    saveButton.addEventListener('click', function () {
      saveRow.hidden = false;
      saveButton.hidden = true;
      nameInput.focus();
      nameInput.select();
    });
    cancel.addEventListener('click', function () { saveRow.hidden = true; saveButton.hidden = false; });
    confirm.addEventListener('click', function () { saveDashboardPanel(panel, panelQuestion, nameInput.value, confirm, feedback, saveRow, saveButton); });
    nameInput.addEventListener('keydown', function (event) {
      if (event.key === 'Enter') { event.preventDefault(); confirm.click(); }
      if (event.key === 'Escape') cancel.click();
    });
    return article;
  }

  function appendSources(parent, sources) {
    if (!Array.isArray(sources) || !sources.length) return;
    var wrap = make('div', 'cm-assistant-sources');
    wrap.appendChild(make('div', 'cm-assistant-message-label', 'Sources used'));
    sources.forEach(function (source) {
      if (!source) return;
      var details = make('details', 'cm-assistant-source-details');
      var summary = make('summary');
      var summaryRow = make('span', 'cm-assistant-source-summary');
      summaryRow.appendChild(make('span', '', source.label || 'Local observability data'));
      var rows = source.rows;
      var rowCount = Array.isArray(rows) ? rows.length : (Number(rows) || 0);
      var previewCount = Array.isArray(source.preview) ? source.preview.length : 0;
      var analyzedCount = Number(source.preview_rows);
      var countLabel = formatCount(rowCount) + ' rows';
      if (previewCount && Number.isFinite(analyzedCount) && analyzedCount > previewCount) {
        countLabel += ' · preview ' + formatCount(previewCount) + ' of ' + formatCount(analyzedCount);
      }
      summaryRow.appendChild(make('span', 'cm-assistant-source-count', countLabel));
      summary.appendChild(summaryRow);
      details.appendChild(summary);
      var sourceBody = make('div', 'cm-assistant-source-body');
      if (source.error) sourceBody.appendChild(make('div', 'cm-assistant-panel-error', 'This source could not be read: ' + String(source.error)));
      if (Array.isArray(source.preview) && source.preview.length) {
        appendTable(sourceBody, source.preview, 20);
        if (Number.isFinite(analyzedCount) && analyzedCount > source.preview.length) {
          sourceBody.appendChild(make('div', 'cm-assistant-panel-description', 'Showing a redacted preview of ' + formatCount(analyzedCount) + ' rows. The full result count is ' + formatCount(rowCount) + '.'));
        }
      } else if (Array.isArray(rows) && rows.length) {
        appendTable(sourceBody, rows, 12);
      } else if (typeof rows === 'number') {
        sourceBody.appendChild(make('div', 'cm-assistant-panel-description', formatCount(rows) + ' rows were used by the assistant. No row-level preview was returned.'));
      } else {
        sourceBody.appendChild(make('div', 'cm-assistant-panel-description', 'The assistant did not receive row-level source data for this source.'));
      }
      if (source.sql) {
        var sqlDetails = make('details', 'cm-assistant-query-details');
        sqlDetails.appendChild(make('summary', '', 'Source query'));
        sqlDetails.appendChild(make('pre', 'cm-assistant-query', String(source.sql)));
        sourceBody.appendChild(sqlDetails);
      }
      details.appendChild(sourceBody);
      wrap.appendChild(details);
    });
    parent.appendChild(wrap);
  }

  function appendResult(messageNode, data, question) {
    var response = data || {};
    var content = response.answer || (Array.isArray(response.panels) && response.panels.length ? 'I found these views from the available evidence.' : 'The assistant returned no answer.');
    setAnswerText(messageNode.content, content);
    var stack = make('div', 'cm-assistant-result-stack');
    (Array.isArray(response.panels) ? response.panels : []).forEach(function (panel) {
      stack.appendChild(renderPanel(panel, question));
    });
    appendSources(stack, response.sources);
    if (stack.childElementCount) messageNode.body.appendChild(stack);
  }

  function renderConversationMessage(message) {
    message = message || {};
    var node = addMessage(message.role === 'user' ? 'user' : 'assistant', message.content || '');
    if (!node || message.role === 'user') return;
    var stack = make('div', 'cm-assistant-result-stack');
    (Array.isArray(message.panels) ? message.panels : []).forEach(function (panel) {
      stack.appendChild(renderPanel(panel, message.content || ''));
    });
    appendSources(stack, message.sources);
    if (stack.childElementCount) node.body.appendChild(stack);
  }

  function cancelChat(reason) {
    var request = state.chatRequest;
    if (!request) return false;
    request.cancelReason = reason || 'user';
    if (request.controller) request.controller.abort();
    if (request.cancelReader) request.cancelReader();
    if (request.pendingNode && request.pendingNode.article) {
      request.pendingNode.article.classList.remove('is-streaming');
      if (request.answerText) {
        request.pendingNode.progress.textContent = 'Stopped. This answer is incomplete.';
      } else request.pendingNode.article.remove();
    }
    state.pendingNode = null;
    state.chatRequest = null;
    setComposerBusy(false);
    return true;
  }

  function cancelConversationRequest(reason) {
    var request = state.conversationRequest;
    if (!request) return false;
    request.cancelReason = reason || 'navigation';
    if (request.controller) request.controller.abort();
    state.conversationRequest = null;
    return true;
  }

  function loadConversation(id) {
    if (!id) return;
    var hadChat = cancelChat('conversation');
    var hadConversation = cancelConversationRequest('conversation');
    var hadWaiting = hadChat || hadConversation;
    state.navigationToken += 1;
    var navigationToken = state.navigationToken;
    clearRecovery();
    state.conversationId = id;
    setConversationReady(false);
    renderHistory();
    clearThread();
    addMessage('assistant', 'Loading this conversation...');
    setStatusMessage(hadWaiting
      ? 'Stop requested. Any answer already saved remains in your history. Loading saved conversation.'
      : 'Loading saved conversation...', 'success');
    var request = requestJson('/api/assistant/conversations/' + encodeURIComponent(id), { credentials: 'same-origin' }, 15000, 'conversation');
    request.navigationToken = navigationToken;
    state.conversationRequest = request;
    request.promise.then(function (data) {
      if (state.conversationRequest === request) state.conversationRequest = null;
      if (!requestIsCurrent(request)) return;
      setConversationReady(true);
      clearThread();
      state.conversationId = data && data.id ? data.id : id;
      var messages = Array.isArray(data && data.messages) ? data.messages : [];
      if (!messages.length) showWelcome();
      messages.forEach(renderConversationMessage);
      renderHistory();
      setStatusMessage('');
    }).catch(function (error) {
      if (state.conversationRequest === request) state.conversationRequest = null;
      if (!isMounted() || navigationToken !== state.navigationToken || (error && error.name === 'AbortError' && request.cancelReason)) return;
      setConversationReady(true);
      clearThread();
      addMessage('assistant', errorMessage(error, 'This conversation could not be loaded. Try again.'));
      setStatusMessage(errorMessage(error), 'error');
    });
  }

  function newConversation() {
    var hadChat = cancelChat('new-chat');
    var hadConversation = cancelConversationRequest('new-chat');
    var hadWaiting = hadChat || hadConversation;
    state.navigationToken += 1;
    clearRecovery();
    state.conversationId = null;
    setConversationReady(true);
    renderHistory();
    clearThread();
    showWelcome();
    setStatusMessage(hadWaiting
      ? 'Stop requested. Any answer already saved remains in your history. New conversation ready.'
      : 'New conversation ready.', 'success');
    var input = el('cm-assistant-input');
    if (input) { input.value = ''; resizeInput(); input.focus(); }
  }

  function setComposerBusy(busy) {
    var send = el('cm-assistant-send');
    var input = el('cm-assistant-input');
    if (!send) return;
    send.disabled = !!(!busy && (!state.conversationReady || state.dataAvailable === false));
    send.classList.toggle('is-cancel', !!busy);
    var label = send.querySelector('span');
    if (label) label.textContent = busy ? 'Stop' : 'Send';
    var arrow = send.querySelector('.cm-assistant-send-arrow');
    if (arrow) arrow.textContent = busy ? '×' : '↗';
    if (input) input.setAttribute('aria-busy', busy ? 'true' : 'false');
  }

  function setConversationReady(ready) {
    state.conversationReady = !!ready;
    var send = el('cm-assistant-send');
    if (send && !state.chatRequest) send.disabled = !state.conversationReady || state.dataAvailable === false;
  }

  function sendMessage() {
    if (!isMounted()) return;
    if (state.chatRequest) {
      var stoppedRequest = state.chatRequest;
      cancelChat('user');
      setStatusMessage('Stop requested. Any answer already saved remains in your history.', 'success');
      renderChatRecovery(null, stoppedRequest);
      return;
    }
    if (!state.conversationReady) {
      setStatusMessage('Wait for the conversation to finish loading before sending a new question.', 'warning');
      return;
    }
    if (state.dataAvailable === false) {
      setStatusMessage(state.dataStatusMessage || 'Local ClawMetry data is unavailable. Reconnect the local store before asking the assistant.', 'warning');
      return;
    }
    var input = el('cm-assistant-input');
    if (!input) return;
    var message = String(input.value || '').trim().slice(0, MAX_MESSAGE);
    if (!message) {
      setStatusMessage('Write a question first.', 'warning');
      input.focus();
      return;
    }
    var engine = el('cm-assistant-engine');
    var provider = engine ? engine.value : 'auto';
    var keyInput = el('cm-assistant-api-key');
    var apiKey = keyInput ? String(keyInput.value || '').trim() : '';
    if (provider === 'anthropic' && !apiKey) {
      setStatusMessage('Add an Anthropic API key for this page, or choose another engine.', 'warning');
      if (keyInput) keyInput.focus();
      return;
    }
    if (provider === 'claude_cli' && state.status && Array.isArray(state.status.providers)) {
      var local = state.status.providers.filter(function (item) { return item && item.id === 'claude_cli'; })[0];
      if (local && local.available === false) {
        setStatusMessage('The local harness is not available. Choose Automatic or add an Anthropic API key.', 'warning');
        return;
      }
    }
    if (provider === 'managed' && !managedIsAvailable()) {
      setStatusMessage('Managed assistant access is not available yet. Choose another engine or learn about managed access.', 'warning');
      return;
    }
    var question = message;
    // Invalidate detached recovery actions from an earlier attempt.
    state.navigationToken += 1;
    clearRecovery();
    addMessage('user', message);
    input.value = '';
    resizeInput();
    var pending = addMessage('assistant', '');
    pending.progress = make('div', 'cm-assistant-stream-status', 'Checking your question...');
    pending.progress.setAttribute('role', 'status');
    pending.body.appendChild(pending.progress);
    pending.article.classList.add('is-streaming');
    var answerText = '';
    var payload = { message: message, provider: provider, stream: true };
    if (state.conversationId) payload.conversation_id = state.conversationId;
    if (provider === 'anthropic' && apiKey) payload.api_key = apiKey;
    setComposerBusy(true);
    setStatusMessage('');
    var request = requestStream('/api/assistant/chat', {
      method: 'POST',
      credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }, function (type, data) {
      if (state.chatRequest !== request || !requestIsCurrent(request)) return;
      if (type === 'status' && typeof data.message === 'string') {
        pending.progress.textContent = data.message;
      } else if (type === 'delta' && typeof data.text === 'string') {
        answerText += data.text;
        if (answerText.length > 24000) {
          cancelChat('user');
          setStatusMessage('The answer was too long. Ask a narrower question.', 'warning');
          return;
        }
        request.answerText = answerText;
        updateComposerClearance();
        var bounds = pending.article.getBoundingClientRect();
        var composerTop = el('cm-assistant-composer').getBoundingClientRect().top;
        var follow = bounds.bottom > 0 && bounds.bottom < Math.min(window.innerHeight, composerTop) + 160;
        setAnswerText(pending.content, answerText);
        pending.progress.textContent = 'Writing answer...';
        if (follow) pending.article.scrollIntoView({ block: 'end' });
      }
    });
    request.scopeIdentity = scopeIdentity();
    request.navigationToken = state.navigationToken;
    request.conversationId = state.conversationId;
    request.pendingNode = pending;
    state.chatRequest = request;
    if (pending.article.scrollIntoView) pending.article.scrollIntoView({ block: 'end' });
    request.promise.then(function (data) {
      if (state.chatRequest !== request || !requestIsCurrent(request)) return;
      if (state.chatRequest === request) state.chatRequest = null;
      setComposerBusy(false);
      pending.article.classList.remove('is-streaming');
      pending.progress.remove();
      state.pendingNode = null;
      if (data && data.conversation_id) state.conversationId = data.conversation_id;
      renderDataNotice(data);
      appendResult(pending, data, question);
      setStatusMessage('Answer ready. Review the sources before saving a panel.', 'success');
      loadHistory(true);
    }).catch(function (error) {
      var reason = request.cancelReason;
      if (state.chatRequest !== request || !requestIsCurrent(request)) return;
      state.chatRequest = null;
      setComposerBusy(false);
      pending.article.classList.remove('is-streaming');
      state.pendingNode = null;
      if (!isMounted() || reason === 'leave' || reason === 'conversation' || reason === 'new-chat') return;
      if (reason === 'user' || (error && error.name === 'AbortError')) {
        setStatusMessage('Stop requested. Any answer already saved remains in your history.', 'success');
        return;
      }
      var messageText = errorMessage(error);
      setStatusMessage(messageText, 'error');
      pending.progress.textContent = answerText ? 'Incomplete answer. ' + messageText : messageText;
      pending.progress.classList.add('is-error');
      renderChatRecovery(error, request);
    });
  }

  function resizeInput() {
    var input = el('cm-assistant-input');
    if (!input) return;
    input.style.height = 'auto';
    input.style.height = Math.min(input.scrollHeight, 160) + 'px';
    updateComposerClearance();
  }

  function updateComposerClearance() {
    var composer = el('cm-assistant-composer');
    var thread = el('cm-assistant-thread');
    if (composer && composer.getBoundingClientRect && thread && thread.style.setProperty) {
      thread.style.setProperty('--cm-composer-clearance', (composer.getBoundingClientRect().height + 24) + 'px');
    }
  }

  function setVoiceUi(active) {
    var button = el('cm-assistant-voice');
    if (!button) return;
    button.classList.toggle('is-listening', !!active);
    button.setAttribute('aria-pressed', active ? 'true' : 'false');
    button.setAttribute('aria-label', active ? 'Stop voice input' : 'Start voice input');
    button.title = active ? 'Stop listening' : 'Voice input';
  }

  function stopVoice() {
    if (state.voice && state.voiceActive) {
      try { state.voice.stop(); } catch (e) {}
    }
    state.voiceActive = false;
    state.voiceInterim = '';
    setVoiceUi(false);
  }

  function startVoice() {
    var Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!Recognition) {
      setStatusMessage('Voice input is not supported by this browser. You can still type your question.', 'warning');
      return;
    }
    if (state.voiceActive) { stopVoice(); return; }
    var input = el('cm-assistant-input');
    if (!input) return;
    var recognition = new Recognition();
    var voiceScope = scopeIdentity();
    var voiceNavigation = state.navigationToken;
    function voiceIsCurrent() {
      return isMounted() && state.voice === recognition && voiceScope === scopeIdentity()
        && voiceNavigation === state.navigationToken;
    }
    state.voice = recognition;
    state.voiceActive = true;
    state.voiceBase = String(input.value || '').trim();
    state.voiceFinal = '';
    state.voiceInterim = '';
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = navigator.language || 'en-US';
    recognition.onstart = function () {
      if (!voiceIsCurrent()) return;
      setVoiceUi(true);
      setStatusMessage('Listening. Review the transcript before sending.', 'success');
    };
    recognition.onresult = function (event) {
      if (!voiceIsCurrent()) return;
      var interim = '';
      for (var i = event.resultIndex; i < event.results.length; i++) {
        var text = event.results[i][0].transcript || '';
        if (event.results[i].isFinal) state.voiceFinal += text;
        else interim += text;
      }
      state.voiceInterim = interim;
      input.value = [state.voiceBase, state.voiceFinal].filter(Boolean).join(state.voiceBase && state.voiceFinal ? ' ' : '');
      resizeInput();
      if (interim) setStatusMessage('Listening: ' + interim + ' · review before sending.', 'success');
    };
    recognition.onerror = function (event) {
      if (!voiceIsCurrent()) return;
      state.voiceActive = false;
      setVoiceUi(false);
      if (!isMounted()) return;
      setStatusMessage(event && event.error === 'not-allowed'
        ? 'Microphone access was denied. You can enable it in browser settings or type your question.'
        : 'Voice input could not start. You can still type your question.', 'warning');
    };
    recognition.onend = function () {
      if (!voiceIsCurrent()) return;
      state.voiceActive = false;
      state.voiceInterim = '';
      setVoiceUi(false);
      if (isMounted() && state.voiceFinal) setStatusMessage('Transcript ready. Review it before sending.', 'success');
    };
    try { recognition.start(); } catch (e) {
      state.voiceActive = false;
      setVoiceUi(false);
      setStatusMessage('Voice input could not start. You can still type your question.', 'warning');
    }
  }

  function bind() {
    setupSuggestions();
    renderDataNotice({});
    var composer = el('cm-assistant-composer');
    if (composer) composer.addEventListener('submit', function (event) { event.preventDefault(); sendMessage(); });
    var input = el('cm-assistant-input');
    if (input) {
      input.addEventListener('input', resizeInput);
      input.addEventListener('keydown', function (event) {
        if (event.key === 'Enter' && !event.shiftKey) {
          event.preventDefault();
          sendMessage();
        }
      });
    }
    var voice = el('cm-assistant-voice');
    if (voice) voice.addEventListener('click', startVoice);
    var newChat = el('cm-assistant-new-chat');
    if (newChat) newChat.addEventListener('click', newConversation);
    var engine = el('cm-assistant-engine');
    if (engine) engine.addEventListener('change', function () {
      var keyRow = el('cm-assistant-key-row');
      if (keyRow) keyRow.hidden = engine.value !== 'anthropic';
      if (engine.value === 'anthropic') setStatusMessage('Your key stays in memory for this page only and is sent only with your request.', 'success');
      if (engine.value === 'managed' && !managedIsAvailable()) {
        engine.value = 'auto';
        setStatusMessage('Managed assistant access is not available yet. Choose another engine or learn about managed access.', 'warning');
      }
    });
    var topup = el('cm-assistant-managed-topup');
    if (topup) topup.addEventListener('click', startManagedCheckout);
    resizeInput();
    setConversationReady(true);
  }

  function initialize() {
    if (state.initialized || !page()) return;
    state.initialized = true;
    bind();
  }

  function loadAssistantPage() {
    initialize();
    if (!page()) return;
    state.mounted = true;
    var identity = scopeIdentity();
    if (state.scopeIdentity !== null && state.scopeIdentity !== identity) {
      resetScope(identity);
      return;
    }
    state.scopeIdentity = identity;
    if (!el('cm-assistant-thread').childElementCount) showWelcome();
    if (!state.statusLoadedAt || Date.now() - state.statusLoadedAt > 30000) loadStatus();
    if (!state.historyLoadedAt || Date.now() - state.historyLoadedAt > 30000) loadHistory(false);
    updateEngineOptions();
    renderManagedStatus();
  }

  function assistantLeave() {
    state.mounted = false;
    state.navigationToken += 1;
    clearRecovery();
    stopVoice();
    cancelChat('leave');
    cancelConversationRequest('leave');
    if (state.statusRequest) state.statusRequest.cancelReason = 'leave';
    if (state.historyRequest) state.historyRequest.cancelReason = 'leave';
    if (state.checkoutRequest) state.checkoutRequest.cancelReason = 'leave';
    cancelAllRequests('leave');
    state.statusRequest = null;
    state.historyRequest = null;
    state.checkoutRequest = null;
    var key = el('cm-assistant-api-key');
    if (key) key.value = '';
  }

  window.loadAssistantPage = loadAssistantPage;
  window.assistantLeave = assistantLeave;

  if (typeof window.addEventListener === 'function') window.addEventListener('cm-assistant-scope-changed', function () {
    if (!window.CLOUD_MODE || !state.initialized) return;
    var identity = scopeIdentity();
    if (state.scopeIdentity !== identity) resetScope(identity);
  });

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', initialize);
  else initialize();
}());
