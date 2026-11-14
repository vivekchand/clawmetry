// Shared, compact plan choice and explicitly requested trial recovery.
(function () {
  'use strict';
  function tr(key, vars, fallback) {
    try {
      if (typeof window.t === 'function') return window.t(key, vars, fallback);
    } catch (e) { /* translations can load after the component */ }
    return vars ? String(fallback).replace(/\{(\w+)\}/g, function (m, k) {
      return vars[k] != null ? vars[k] : m;
    }) : fallback;
  }
  function esc(value) {
    return String(value == null ? '' : value).replace(/[&<>"']/g, function (c) {
      return {'&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;'}[c];
    });
  }
  function price(tier, interval) {
    var p = window.CM_PLANS && window.CM_PLANS.prices && window.CM_PLANS.prices[tier];
    if (!p) return '';
    return '$' + (interval === 'year' ? p.year : p.month)
      + '<span class="cm-offer-per">' + esc(interval === 'year' ? ' / ' + tr('trial.per_year', null, 'node/yr') : ' / ' + tr('trial.per_month', null, 'node/mo')) + '</span>';
  }
  function row(prefix, tier, selected, interval) {
    return '<button type="button" class="' + prefix + '-tier cm-offer-tier" data-tier="' + tier + '" aria-pressed="' + (selected === tier) + '">'
      + '<span class="cm-offer-radio" aria-hidden="true"></span><span class="cm-offer-tier-main">'
      + '<span class="cm-offer-tier-top"><strong>' + esc(tier === 'pro' ? tr('trial.pro', null, 'Pro') : tr('trial.starter', null, 'Starter')) + '</strong>'
      + '<span class="cm-offer-tier-price">' + price(tier, interval) + '</span></span>'
      + '<span class="cm-offer-tier-sub">' + esc(window.CM_PLANS && window.CM_PLANS.blurb && window.CM_PLANS.blurb[tier]) + '</span></span></button>';
  }
  function html(o) {
    var p = o.prefix;
    return '<div class="' + p + '-card cm-offer-card">'
      + (o.dismissible ? '<button type="button" class="' + p + '-close cm-offer-close" aria-label="' + esc(tr("trial.close", null, "Close")) + '">&times;</button>' : '')
      + '<h2 id="' + p + '-title" tabindex="-1">' + esc(o.title) + '</h2>'
      + '<p class="cm-offer-body">' + esc(o.body) + '</p>'
      + '<div class="cm-offer-content">'
      + '<div class="' + p + '-seg cm-offer-seg" role="group" aria-label="' + esc(tr("trial.interval", null, "Billing interval")) + '">'
      + '<button type="button" data-interval="month" aria-pressed="' + (o.interval === 'month') + '">' + esc(tr("trial.monthly", null, "Monthly")) + '</button>'
      + '<button type="button" data-interval="year" aria-pressed="' + (o.interval === 'year') + '">' + esc(tr("trial.annual", null, "Annual")) + '<span>' + esc(tr("trial.two_months_free", null, "2 months free")) + '</span></button></div>'
      + '<div id="' + p + '-tiers">' + row(p, 'starter', o.tier, o.interval) + row(p, 'pro', o.tier, o.interval) + '</div>'
      + '<p class="cm-offer-device" id="' + p + '-device" style="' + (o.interval === 'year' ? '' : 'display:none;') + '">'
      + (window.CM_PLANS && window.CM_PLANS.deviceValue ? esc(tr('trial.offer.annual_device', {value:window.CM_PLANS.deviceValue}, 'Annual plans include the ${value} desk device after payment.')) : '') + '</p>'
      + (o.checkoutUrl ? '<a href="' + esc(o.checkoutUrl) + '" target="_blank" rel="noopener"' : '<button type="button"')
      + ' class="' + p + '-cta cm-offer-primary">' + esc(tr('trial.offer.continue_plan', {plan:o.tier === 'pro' ? tr('trial.pro', null, 'Pro') : tr('trial.starter', null, 'Starter')}, 'Continue with {plan}')) + (o.checkoutUrl ? '</a>' : '</button>')
      + '<p class="cm-offer-secure">' + esc(o.interval === 'year' ? tr('trial.offer.secure_annual', null, 'Secure checkout by Stripe. Billed annually.') : tr('trial.secure', null, 'Secure checkout by Stripe. Cancel anytime.')) + '</p>'
      + '<div class="' + p + '-status cm-offer-status" id="' + p + '-status" aria-live="polite"></div>'
      + (o.recoverable ? '<button type="button" class="cm-offer-more">' + esc(tr("trial.offer.not_ready_to_subscribe", null, "Not ready to subscribe?")) + '</button>' : '')
      + '<div class="cm-offer-alternatives">'
      + (o.showFree ? '<button type="button" class="' + p + '-free cm-offer-text" title="' + esc(o.freeLabel || tr("trial.offer.continue_with_the_free_plan", null, "Continue with the free plan")) + '">' + esc(tr("trial.offer.continue_free", null, "Continue free")) + '</button>' : '')
      + '<button type="button" class="cm-offer-text" id="' + p + '-havekey" aria-expanded="false" aria-controls="' + p + '-keywrap">' + esc(tr("trial.offer.use_a_license_key", null, "Use a license key")) + '</button></div>'
      + (o.showFree ? '<p class="cm-offer-free-note">' + esc(o.freeLabel ? tr('trial.offer.free_includes', {runtimes:o.freeLabel}, 'Free includes {runtimes}. Other runtimes need a subscription.') : tr('trial.offer.free_limits', null, 'Free runtimes only. Paid runtimes require a subscription.')) + '</p>' : '')
      + '<div id="' + p + '-keywrap" class="cm-offer-keywrap" style="display:none;">'
      + '<label for="' + p + '-key">' + esc(tr("trial.offer.license_key", null, "License key")) + '</label><textarea id="' + p + '-key" class="' + p + '-key" spellcheck="false" autocomplete="off" rows="2"></textarea>'
      + '<button type="button" class="' + p + '-activate cm-offer-secondary">' + esc(tr("trial.activate", null, "Activate license")) + '</button></div>'
      + '</div></div>';
  }
  function repaint(el, prefix, tier, interval) {
    el.querySelectorAll('.' + prefix + '-seg button').forEach(function (button) {
      button.setAttribute('aria-pressed', String(button.getAttribute('data-interval') === interval));
    });
    el.querySelectorAll('.' + prefix + '-tier').forEach(function (button) {
      var value = button.getAttribute('data-tier');
      button.setAttribute('aria-pressed', String(value === tier));
      button.querySelector('.cm-offer-tier-price').innerHTML = price(value, interval);
    });
    el.querySelector('.' + prefix + '-cta').textContent = tr('trial.offer.continue_plan', {plan:tier === 'pro' ? tr('trial.pro', null, 'Pro') : tr('trial.starter', null, 'Starter')}, 'Continue with {plan}');
    el.querySelector('#' + prefix + '-device').style.display = interval === 'year' ? '' : 'none';
    el.querySelector('.cm-offer-secure').textContent = interval === 'year' ? tr('trial.offer.secure_annual', null, 'Secure checkout by Stripe. Billed annually.') : tr('trial.secure', null, 'Secure checkout by Stripe. Cancel anytime.');
  }
  function trap(el, close) {
    var previous = document.activeElement;
    function visible(node) {
      return !node.disabled && !node.hidden && (!node.getClientRects || node.getClientRects().length > 0);
    }
    function keydown(event) {
      if (event.key === 'Escape') {
        event.preventDefault(); event.stopPropagation();
        if (close) close();
      }
      if (event.key !== 'Tab') return;
      var nodes = Array.prototype.filter.call(el.querySelectorAll('button,a[href],input,select,textarea,[tabindex="0"]'), visible);
      if (!nodes.length) { event.preventDefault(); el.focus(); return; }
      var first = nodes[0], last = nodes[nodes.length - 1], active = document.activeElement;
      if (event.shiftKey && (active === first || nodes.indexOf(active) < 0)) { event.preventDefault(); last.focus(); }
      else if (!event.shiftKey && (active === last || nodes.indexOf(active) < 0)) { event.preventDefault(); first.focus(); }
    }
    el.addEventListener('keydown', keydown);
    var heading = el.querySelector('h2');
    if (heading) heading.focus();
    return function () {
      el.removeEventListener('keydown', keydown);
      if (previous && previous.isConnected && previous.focus) previous.focus();
    };
  }
  function cloudToken() {
    try { return window.CLOUD_TOKEN || localStorage.getItem('clawmetry-token') || ''; } catch (e) { return ''; }
  }
  function request(method, body) {
    var cloud = !!window.CLOUD_MODE;
    var headers = {'Content-Type': 'application/json'};
    if (cloud) headers.Authorization = 'Bearer ' + cloudToken();
    var controller = typeof AbortController === 'function' ? new AbortController() : null;
    var timer = controller ? setTimeout(function () { controller.abort(); }, 18000) : null;
    return fetch(cloud ? '/api/license/trial/extension' : '/api/trial/extension', {
      method: method, credentials: 'same-origin', headers: headers,
      body: method === 'POST' ? JSON.stringify(body) : undefined,
      signal: controller ? controller.signal : undefined,
    }).then(function (response) {
      return response.json().then(function (data) {
        if (!response.ok) throw new Error(data.error || tr("trial.offer.could_not_confirm_the_extension_please_try_again", null, "Could not confirm the extension. Please try again."));
        return data;
      });
    }).finally(function () { if (timer) clearTimeout(timer); });
  }
  function recover(el, onSuccess, onFree) {
    if (el.querySelector('.cm-offer-recovery')) return;
    var card = el.querySelector('.cm-offer-card'), offer = el.querySelector('.cm-offer-content');
    var heading = el.querySelector('h2'), intro = el.querySelector('.cm-offer-body');
    var oldTitle = heading.textContent, oldBody = intro.textContent;
    var note = el.querySelector('.cm-offer-free-note');
    var freeNote = note ? '<p class="cm-offer-free-note">' + esc(note.textContent) + '</p>' : '';
    var panel = document.createElement('section');
    panel.className = 'cm-offer-recovery';
    offer.hidden = true;
    heading.textContent = tr("trial.offer.need_more_time", null, "Need more time?");
    intro.textContent = tr("trial.offer.let_us_find_the_right_next_step_for_you", null, "Let us find the right next step for you.");
    panel.innerHTML = '<p class="cm-offer-status" aria-live="polite">' + esc(tr("trial.offer.checking_your_trial_offer", null, "Checking your trial offer...")) + '</p>'
      + '<div class="cm-offer-alternatives"><button type="button" class="cm-offer-text" data-back>' + esc(tr("trial.offer.back_to_plans", null, "Back to plans")) + '</button>'
      + '<button type="button" class="cm-offer-text" data-free>' + esc(tr("trial.offer.continue_free", null, "Continue free")) + '</button></div>' + freeNote;
    card.appendChild(panel);
    var status = panel.querySelector('.cm-offer-status');
    function wireFree() {
      var button = panel.querySelector('[data-free]');
      button.addEventListener('click', function () {
        if (button.disabled) return;
        button.disabled = true;
        status.textContent = tr('trial.offer.switching_free', null, 'Switching to free mode...');
        Promise.resolve().then(onFree).catch(function () {
          status.textContent = tr('trial.offer.free_failed', null, 'Could not switch to free mode. Please try again.');
        }).finally(function () { button.disabled = false; });
      });
    }
    function back() {
      panel.remove(); offer.hidden = false; heading.textContent = oldTitle; intro.textContent = oldBody;
      el.querySelector('.cm-offer-more').focus();
    }
    panel.querySelector('[data-back]').addEventListener('click', back);
    wireFree();
    heading.focus();
    request('GET').then(function (data) {
      if (!panel.isConnected) return;
      if (!data.eligible && !data.can_resume) { status.textContent = data.message || tr("trial.offer.this_trial_offer_is_not_available_you_can_choose_a_plan_or_continue_free", null, "This trial offer is not available. You can choose a plan or continue free."); return; }
      intro.textContent = data.can_resume ? tr("trial.offer.your_extended_trial_is_ready_to_restore", null, "Your extended trial is ready to restore.") : tr("trial.offer.a_little_feedback_helps_us_make_clawmetry_more_useful", null, "A little feedback helps us make ClawMetry more useful.");
      panel.innerHTML = (data.can_resume ? '' : '<label for="cm-recovery-reason">' + esc(tr("trial.offer.what_stopped_you_upgrading", null, "What stopped you upgrading? ")) + '<span>' + esc(tr("trial.offer.optional", null, "(optional)")) + '</span></label>'
        + '<select id="cm-recovery-reason"><option value="prefer_not_to_say">' + esc(tr("trial.offer.prefer_not_to_say", null, "Prefer not to say")) + '</option><option value="more_time">' + esc(tr("trial.offer.i_need_more_time", null, "I need more time")) + '</option>'
        + '<option value="setup">' + esc(tr("trial.offer.i_had_trouble_getting_started", null, "I had trouble getting started")) + '</option><option value="missing_feature">' + esc(tr("trial.offer.a_feature_is_missing", null, "A feature is missing")) + '</option><option value="price">' + esc(tr("trial.offer.the_price", null, "The price")) + '</option>'
        + '<option value="unclear_value">' + esc(tr("trial.offer.i_have_not_seen_enough_value_yet", null, "I have not seen enough value yet")) + '</option><option value="other">' + esc(tr("trial.offer.something_else", null, "Something else")) + '</option></select>'
        + '<label for="cm-recovery-feedback">' + esc(tr("trial.offer.what_would_make_it_worth_subscribing", null, "What would make it worth subscribing? ")) + '<span>' + esc(tr("trial.offer.optional", null, "(optional)")) + '</span></label>'
        + '<textarea id="cm-recovery-feedback" rows="2" maxlength="500" placeholder="' + esc(tr("trial.offer.tell_us_what_would_help", null, "Tell us what would help.")) + '"></textarea>')
        + '<p class="cm-offer-promise">' + esc(tr('trial.offer.extension_promise', {days:Number(data.free_days)}, 'One-time {days}-day extension. No card required. No automatic charge.')) + '</p>'
        + '<button type="button" class="cm-offer-primary" data-claim>' + esc(data.can_resume ? tr("trial.offer.restore_my_extended_trial", null, "Restore my extended trial") : tr("trial.offer.extend_my_trial", null, "Extend my trial")) + '</button>'
        + '<p class="cm-offer-status" aria-live="polite"></p><div class="cm-offer-alternatives">'
        + '<button type="button" class="cm-offer-text" data-back>' + esc(tr("trial.offer.back_to_plans", null, "Back to plans")) + '</button><button type="button" class="cm-offer-text" data-free>' + esc(tr("trial.offer.continue_free", null, "Continue free")) + '</button></div>' + freeNote;
      panel.querySelector('[data-back]').addEventListener('click', back);
      wireFree();
      var claim = panel.querySelector('[data-claim]');
      status = panel.querySelector('.cm-offer-status');
      claim.addEventListener('click', function () {
        if (claim.disabled) return;
        claim.disabled = true;
        status.textContent = tr("trial.offer.confirming_your_extension", null, "Confirming your extension...");
        var reason = panel.querySelector('select'), feedback = panel.querySelector('textarea');
        request('POST', {reason: reason ? reason.value : 'prefer_not_to_say', feedback: feedback ? feedback.value : ''}).then(function (result) {
          if (!panel.isConnected) return;
          if (result.grant_state !== 'applied' || !result.trial_end) throw new Error(result.message || tr("trial.offer.could_not_confirm_the_extension_please_try_again", null, "Could not confirm the extension. Please try again."));
          var end = new Date(result.trial_end);
          if (!isFinite(end.getTime())) throw new Error(tr("trial.offer.could_not_confirm_the_end_date_please_try_again", null, "Could not confirm the end date. Please try again."));
          heading.textContent = tr("trial.offer.you_have_more_time", null, "You have more time");
          intro.textContent = tr('trial.offer.extended_through', {date:end.toLocaleDateString(undefined, {year:'numeric', month:'long', day:'numeric'})}, 'Your trial is extended through {date}.');
          panel.innerHTML = '<p class="cm-offer-promise">' + esc(tr("trial.offer.no_automatic_charge_choose_a_plan_whenever_you_are_ready", null, "No automatic charge. Choose a plan whenever you are ready.")) + '</p><button type="button" class="cm-offer-primary" data-done>' + esc(tr("trial.offer.continue_to_dashboard", null, "Continue to dashboard")) + '</button>';
          panel.querySelector('[data-done]').addEventListener('click', onSuccess);
          heading.focus();
        }).catch(function (error) {
          claim.disabled = false;
          status.textContent = error.name === 'AbortError' ? tr("trial.offer.this_took_too_long_try_again_your_offer_will_not_be_used_twice", null, "This took too long. Try again. Your offer will not be used twice.") : error.message;
        });
      });
    }).catch(function () {
      if (panel.isConnected) status.textContent = tr("trial.offer.could_not_check_your_trial_offer_go_back_to_plans_and_try_again_or_continue_free", null, "Could not check your trial offer. Go back to plans and try again, or continue free.");
    });
  }
  window.CMTrialOffer = {html: html, repaint: repaint, trap: trap, recover: recover, tr: tr};
})();
