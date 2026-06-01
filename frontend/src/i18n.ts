/**
 * i18n.ts — i18next initialisation for the v2 SPA.
 *
 * Shares the same locale catalog as v1 (`clawmetry/static/locales/*.json`)
 * via the HTTP backend; no duplicate translation files.
 *
 * Detection order (matches v1 PRD §3.4):
 *   querystring ?lng=  →  cm-lang cookie  →  navigator.language  →  "en"
 *
 * RTL: on every language change the <html dir> attribute is updated so CSS
 * logical properties take effect without a page reload.  The RTL set is
 * pre-computed from _meta.json (ar, fa, he, ur).
 *
 * refs: issue #1986
 */

import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import LanguageDetector from "i18next-browser-languagedetector";
import Backend from "i18next-http-backend";

// Languages whose base script runs right-to-left.
// Derived from clawmetry/static/locales/_meta.json where dir === "rtl".
const RTL_LANGS = new Set(["ar", "fa", "he", "ur"]);

function applyDocumentDir(lng: string) {
  const base = lng.split("-")[0];
  document.documentElement.setAttribute(
    "dir",
    RTL_LANGS.has(base) ? "rtl" : "ltr",
  );
}

i18n
  .use(Backend)
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    fallbackLng: "en",
    // Allow any code listed in _meta.json; explicit list not needed because
    // the HTTP backend will 404 on unknown codes and fall back to "en".
    supportedLngs: false,
    load: "currentOnly",
    detection: {
      order: ["querystring", "cookie", "navigator"],
      lookupQuerystring: "lng",
      lookupCookie: "cm-lang",
      caches: ["cookie"],
      cookieOptions: { sameSite: "strict", domain: ".clawmetry.com" },
    },
    backend: {
      // Locale files served by Flask at /static/locales/<lng>.json.
      // In dev, vite.config.ts proxies /static → Flask on :8900.
      loadPath: "/static/locales/{{lng}}.json",
    },
    interpolation: {
      escapeValue: false, // React already escapes output
    },
    react: {
      useSuspense: true,
    },
  });

i18n.on("languageChanged", applyDocumentDir);

// Apply direction on init (fires after the first language is resolved).
i18n.on("initialized", () => applyDocumentDir(i18n.language));

export default i18n;
