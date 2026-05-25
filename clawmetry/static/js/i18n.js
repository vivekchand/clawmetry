/*
 * ClawMetry i18n runtime — vanilla, zero-dependency, no build step.
 *
 * One JSON catalog under /static/locales/ is the single source of truth, shared
 * with the v2 React SPA (which reads the same files via react-i18next). This
 * runtime translates `data-i18n` DOM nodes for v1, exposes window.t() for
 * JS-generated strings, formats numbers/dates/plurals via native Intl.*, and
 * keeps the chosen language consistent across pages/reloads/surfaces via a
 * `.clawmetry.com` cookie + localStorage mirror.
 *
 * Detection precedence (highest wins): ?lang= URL param > cm-lang cookie /
 * localStorage > navigator.languages > English. (Geo-IP hint is a later phase.)
 *
 * Design: never crash on bad input. Missing key -> English -> the key itself.
 * Missing locale file -> English. See docs/PRD_I18N.md.
 */
(function () {
  "use strict";

  // ---- where the catalog lives (derive /static base from this script's src) ----
  var SELF = document.currentScript ? document.currentScript.src : "";
  var QS = (SELF.split("?")[1] ? "?" + SELF.split("?")[1] : ""); // carry ?v= cache-bust
  var BASE = SELF.replace(/\/js\/i18n\.js.*$/, "") || "/static";
  function localeUrl(file) { return BASE + "/locales/" + file + QS; }

  var META = [{ code: "en", endonym: "English", short: "EN", dir: "ltr", enabled: true }];
  var EN = {};          // English catalog — always loaded, the fallback
  var DICT = {};        // active locale catalog
  var LANG = "en";
  var CALLBACKS = [];   // listeners notified after every language change

  function loadJSON(url) {
    return fetch(url).then(function (r) { return r.ok ? r.json() : null; }).catch(function () { return null; });
  }

  function isSupported(code) { return META.some(function (m) { return m.code === code; }); }

  // map an arbitrary BCP-47 tag (e.g. "ja-JP", "fr-CA") to a supported code
  function match(tag) {
    if (!tag) return null;
    if (isSupported(tag)) return tag;
    var primary = tag.split("-")[0];
    var hit = META.find(function (m) { return m.code === primary || m.code.split("-")[0] === primary; });
    return hit ? hit.code : null;
  }

  function readCookie(name) {
    var m = document.cookie.match(new RegExp("(?:^|;\\s*)" + name + "=([^;]+)"));
    return m ? decodeURIComponent(m[1]) : null;
  }

  function cookieDomain() {
    // domain-wide on production so the choice spans clawmetry.com <-> app.clawmetry.com;
    // host-only on localhost / previews (setting domain=localhost is rejected by browsers).
    return /(^|\.)clawmetry\.com$/.test(location.hostname) ? ".clawmetry.com" : null;
  }

  function detect() {
    var fromUrl = new URLSearchParams(location.search).get("lang");
    var explicit = match(fromUrl) || match(localStorageGet("cm-lang")) || match(readCookie("cm-lang"));
    if (explicit) return explicit;
    var langs = navigator.languages || [navigator.language || "en"];
    for (var i = 0; i < langs.length; i++) {
      var m = match(langs[i]);
      if (m) return m;
    }
    return "en";
  }

  function localStorageGet(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
  function localStorageSet(k, v) { try { localStorage.setItem(k, v); } catch (e) {} }

  // ---- translation lookup + interpolation + basic Intl pluralisation ----
  function T(key, vars) {
    var s = (DICT && DICT[key] != null) ? DICT[key]
          : (EN[key] != null ? EN[key] : key); // English fallback, then the key
    // plural: key + "_one"/"_other"/... selected by Intl.PluralRules on vars.count
    if (vars && vars.count != null) {
      try {
        var cat = new Intl.PluralRules(LANG).select(vars.count);
        var pk = key + "_" + cat;
        if (DICT[pk] != null || EN[pk] != null) s = (DICT[pk] != null ? DICT[pk] : EN[pk]);
      } catch (e) {}
    }
    if (vars) s = String(s).replace(/\{(\w+)\}/g, function (m, k) { return vars[k] != null ? vars[k] : m; });
    return s;
  }

  // ---- pseudolocale generator (QA: surfaces un-extracted strings + expansion) ----
  function pseudo(src) {
    var map = { a: "á", e: "é", i: "í", o: "ó", u: "ú", A: "Á", E: "É", I: "Í", O: "Ó", U: "Ú", n: "ñ", c: "ç", s: "š", y: "ý", w: "ŵ" };
    var out = {};
    for (var k in src) {
      if (!Object.prototype.hasOwnProperty.call(src, k)) continue;
      out[k] = "⟦" + String(src[k]).replace(/[a-zA-Z]/g, function (ch) { return map[ch] || ch; }) + " ⟧";
    }
    return out;
  }

  // ---- DOM application -------------------------------------------------------
  function apply(root) {
    root = root || document;
    // text nodes: stash the original key once (attribute value, else initial text),
    // so we never read it back from text we already overwrote (the stable-key rule).
    root.querySelectorAll("[data-i18n]").forEach(function (el) {
      if (el.__i18nKey == null) el.__i18nKey = (el.getAttribute("data-i18n") || el.textContent || "").trim();
      // only replace text for leaf elements; skip nodes with element children so we
      // don't wipe nested badges/icons (those children carry their own data-i18n).
      if (el.children.length === 0) el.textContent = T(el.__i18nKey);
    });
    // attributes
    root.querySelectorAll("[data-i18n-title]").forEach(function (el) { el.title = T(el.getAttribute("data-i18n-title")); });
    root.querySelectorAll("[data-i18n-placeholder]").forEach(function (el) { el.setAttribute("placeholder", T(el.getAttribute("data-i18n-placeholder"))); });
    root.querySelectorAll("[data-i18n-aria-label]").forEach(function (el) { el.setAttribute("aria-label", T(el.getAttribute("data-i18n-aria-label"))); });
  }

  // ---- switcher menu (built from _meta.json, native endonyms) ----------------
  function buildMenu() {
    var menu = document.getElementById("i18n-switcher-menu");
    if (!menu) return;
    var showDev = localStorageGet("cm-i18n-dev") === "1";
    menu.innerHTML = "";
    META.filter(function (m) { return m.enabled !== false && (!m.dev || showDev); }).forEach(function (m) {
      var item = document.createElement("div");
      item.textContent = m.endonym;
      item.setAttribute("data-lang", m.code);
      item.setAttribute("role", "menuitem");
      item.style.cssText = "padding:7px 12px;border-radius:6px;cursor:pointer;font-size:13px;white-space:nowrap;color:var(--text-primary,#e6edf3);" + (m.code === LANG ? "font-weight:700;" : "");
      item.onmouseover = function () { item.style.background = "rgba(127,127,127,0.14)"; };
      item.onmouseout = function () { item.style.background = "transparent"; };
      item.onclick = function () { setLang(m.code); closeMenu(); };
      menu.appendChild(item);
    });
  }

  function closeMenu() { var m = document.getElementById("i18n-switcher-menu"); if (m) m.style.display = "none"; }
  window.i18nToggleMenu = function (e) {
    if (e) e.stopPropagation();
    var m = document.getElementById("i18n-switcher-menu");
    if (m) m.style.display = (m.style.display === "block" ? "none" : "block");
  };
  document.addEventListener("click", function (e) {
    var sw = document.getElementById("i18n-switcher");
    if (sw && !sw.contains(e.target)) closeMenu();
  });

  // ---- the public API --------------------------------------------------------
  function setLang(code) {
    code = match(code) || "en";
    var done = function (dict) {
      DICT = dict || {};
      LANG = code;
      var meta = META.find(function (m) { return m.code === code; }) || { dir: "ltr", short: code.toUpperCase() };
      document.documentElement.setAttribute("lang", code);
      document.documentElement.setAttribute("dir", meta.dir || "ltr");
      localStorageSet("cm-lang", code);
      var dom = cookieDomain();
      document.cookie = "cm-lang=" + code + ";path=/;max-age=31536000;samesite=lax" + (dom ? ";domain=" + dom : "");
      var lbl = document.getElementById("i18n-current-label");
      if (lbl) lbl.textContent = meta.short || code.split("-")[0].toUpperCase();
      buildMenu();
      apply(document);
      CALLBACKS.forEach(function (fn) { try { fn(code); } catch (e) {} });
      try { window.dispatchEvent(new CustomEvent("i18n:changed", { detail: { lang: code } })); } catch (e) {}
    };
    if (code === "en") return Promise.resolve(done(EN));
    if (code === "en-XA") return Promise.resolve(done(pseudo(EN)));
    return loadJSON(localeUrl(code + ".json")).then(function (d) { done(d || EN); });
  }

  function fmt(n, opts) { try { return new Intl.NumberFormat(LANG, opts).format(n); } catch (e) { return String(n); } }

  window.i18n = {
    t: T,
    setLang: setLang,
    lang: function () { return LANG; },
    apply: apply,
    onChange: function (fn) { if (typeof fn === "function") CALLBACKS.push(fn); },
    meta: function () { return META; },
    num: function (n, o) { return fmt(n, o); },
    cur: function (n, ccy) { return fmt(n, { style: "currency", currency: ccy || "USD" }); },
    compact: function (n) { return fmt(n, { notation: "compact", maximumFractionDigits: 1 }); },
    date: function (d, o) { try { return new Intl.DateTimeFormat(LANG, o).format(d instanceof Date ? d : new Date(d)); } catch (e) { return String(d); } },
    rel: function (v, unit) { try { return new Intl.RelativeTimeFormat(LANG, { numeric: "auto" }).format(v, unit); } catch (e) { return String(v); } }
  };
  // convenience global so app.js can call t("...") directly (Phase 1 onward)
  window.t = T;

  // ---- boot ------------------------------------------------------------------
  function init() {
    loadJSON(localeUrl("_meta.json")).then(function (meta) {
      if (Array.isArray(meta) && meta.length) META = meta;
      return loadJSON(localeUrl("en.json"));
    }).then(function (en) {
      EN = en || {};
      buildMenu();
      return setLang(detect());
    });
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
