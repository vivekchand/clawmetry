// Runtime pixel-logo helper for the LOCAL (OSS) dashboard.
//
// Mirrors the hosted dashboard (cloud PR #1642): a sprite atlas of
// <symbol id="rt-<id>"> (+ rt-<id>-chip hue-tinted variants + a neutral
// rt-generic fallback), keyed STRICTLY off the runtime id from
// GET /api/runtimes. The atlas ships as a version-controlled static asset
// (clawmetry/static/runtime-logos/sprite.svg) and is fetched + inlined ONCE
// as a hidden <svg>, so an SVG <use href="#rt-<id>"> resolves live once the
// symbol is in the DOM (render order does not matter).
//
// Public API (kept identical to cloud so render code is portable):
//   window.cmRuntimeIcon(id, sizePx, opts) -> "<svg><use href='#rt-<id>'></svg>"
//       unknown id falls back to rt-generic; NEVER throws.
//       opts: {chip:true, cls:'extra', title:'tip'}
//   window.cmRuntimeIconEl(id, sizePx, opts) -> a detached DOM node
//   window.cmRuntimeBrand(id) -> brand hex (from manifest.json)
//   window.cmRuntimeKnown(id) -> bool
//
// Guard: tests/test_runtime_logos_oss.py asserts known/unknown behaviour and
// that the shipped sprite carries a <symbol> for every runtime id in the
// entitlements runtime catalog. tests/test_appjs_units.js also exercises the
// helper if the JS unit harness is present.
(function () {
  if (window.cmRuntimeIcon) return;

  // Brand hexes baked from runtime-logos/manifest.json. Kept in sync with the
  // sprite; the daemon catalog can grow (paid runtimes) and any id absent here
  // resolves to the neutral fallback hue, never throwing.
  var BRAND = {
    "openclaw": "#ff5a3c",
    "nemoclaw": "#76b900",
    "picoclaw": "#2bd4c4",
    "nanoclaw": "#9d6bff",
    "claude_code": "#d97757",
    "codex": "#cfd3da",
    "cursor": "#8a8f99",
    "aider": "#1bd96a",
    "goose": "#e8e2d6",
    "hermes": "#f4b41a",
    "opencode": "#f59e0b",
    "qwen_code": "#6d5cff"
  };
  var FALLBACK_HUE = "#8b97ad";

  function known(id) {
    return Object.prototype.hasOwnProperty.call(BRAND, String(id || "").toLowerCase());
  }

  window.cmRuntimeBrand = function (id) {
    return BRAND[String(id || "").toLowerCase()] || FALLBACK_HUE;
  };
  window.cmRuntimeKnown = function (id) { return known(id); };

  window.cmRuntimeIcon = function (id, sizePx, opts) {
    opts = opts || {};
    var rid = String(id || "").toLowerCase();
    var sym = known(rid) ? ("rt-" + rid + (opts.chip ? "-chip" : "")) : "rt-generic";
    var s = Math.max(8, Number(sizePx) || 16);
    var cls = "cm-rt-ic" + (opts.cls ? (" " + String(opts.cls)) : "");
    var t = opts.title ? ("<title>" + String(opts.title).replace(/[<&>]/g, "") + "</title>") : "";
    return '<svg class="' + cls + '" width="' + s + '" height="' + s +
      '" viewBox="0 0 16 16" aria-hidden="true" style="display:inline-block;vertical-align:middle;flex:none">' +
      t + '<use href="#' + sym + '" xlink:href="#' + sym + '"></use></svg>';
  };

  window.cmRuntimeIconEl = function (id, sizePx, opts) {
    var w = document.createElement("span");
    w.style.cssText = "display:inline-flex;align-items:center";
    w.innerHTML = window.cmRuntimeIcon(id, sizePx, opts);
    return w.firstChild;
  };

  // Inject the sprite atlas ONCE. Fetch the version-controlled static asset and
  // inline it as a hidden <svg>; <use> references resolve live afterward, so the
  // render functions can run before this completes. Idempotent + best-effort
  // (never throws — a failed fetch just leaves icons as empty <use>, which is a
  // harmless no-op rather than a crash).
  function injectSprite() {
    if (document.getElementById("cm-rt-sprite-host")) return;
    var host = document.createElement("div");
    host.id = "cm-rt-sprite-host";
    host.setAttribute("aria-hidden", "true");
    host.style.cssText = "position:absolute;width:0;height:0;overflow:hidden";
    // Resolve the URL relative to this script so a sub-path mount still works.
    var url = "/static/runtime-logos/sprite.svg";
    try {
      var cur = document.currentScript;
      if (cur && cur.src) {
        var base = cur.src.split("/static/")[0];
        if (base) url = base + "/static/runtime-logos/sprite.svg";
      }
    } catch (e) {}
    fetch(url).then(function (r) { return r.ok ? r.text() : ""; }).then(function (svg) {
      if (!svg) return;
      host.innerHTML = svg;
      // Re-decorate any element rendered before the sprite landed.
      try { if (typeof window.cmDecorateRuntimeLogos === "function") window.cmDecorateRuntimeLogos(); } catch (e) {}
    }).catch(function () {});
    (document.body || document.documentElement).appendChild(host);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", injectSprite);
  } else {
    injectSprite();
  }
})();
