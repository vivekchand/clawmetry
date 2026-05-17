// Theme management hook — light / mid / dark.
//
// Reading order on mount:
//   1. localStorage["clawmetry-theme"] if set to "light" | "mid" | "dark"
//   2. prefers-color-scheme media query (dark → "dark", otherwise "light")
//   3. Default "light"
//
// "mid" is never auto-detected — it's only chosen explicitly. Per the design
// handoff README, it's the "shop floor" middle option for users who want a
// less-bright light theme.
//
// Toggling writes localStorage AND updates the <html data-theme="..."> attr,
// which the verbatim styles.css cascades through every component variable.

import { useCallback, useEffect, useState } from "react";

export type Theme = "light" | "mid" | "dark";

const STORAGE_KEY = "clawmetry-theme";
const ALL_THEMES: Theme[] = ["light", "mid", "dark"];

function readStoredTheme(): Theme | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw && (ALL_THEMES as string[]).includes(raw)) return raw as Theme;
  } catch {
    // SSR / privacy mode — fall through to OS preference.
  }
  return null;
}

function detectInitialTheme(): Theme {
  const stored = readStoredTheme();
  if (stored) return stored;
  if (typeof window !== "undefined" && window.matchMedia) {
    if (window.matchMedia("(prefers-color-scheme: dark)").matches) return "dark";
  }
  return "light";
}

function applyTheme(theme: Theme) {
  if (typeof document === "undefined") return;
  document.documentElement.setAttribute("data-theme", theme);
}

export function useTheme(): {
  theme: Theme;
  setTheme: (t: Theme) => void;
} {
  const [theme, setThemeState] = useState<Theme>(() => detectInitialTheme());

  // Apply on mount + on every change.
  useEffect(() => {
    applyTheme(theme);
  }, [theme]);

  // Follow OS preference changes UNLESS the user has explicitly chosen one.
  useEffect(() => {
    if (typeof window === "undefined" || !window.matchMedia) return;
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    const onChange = (ev: MediaQueryListEvent) => {
      if (readStoredTheme()) return; // user override wins
      setThemeState(ev.matches ? "dark" : "light");
    };
    // Older Safari uses addListener / removeListener.
    if (mq.addEventListener) {
      mq.addEventListener("change", onChange);
      return () => mq.removeEventListener("change", onChange);
    }
    mq.addListener(onChange);
    return () => mq.removeListener(onChange);
  }, []);

  const setTheme = useCallback((t: Theme) => {
    try {
      localStorage.setItem(STORAGE_KEY, t);
    } catch {
      // ignore — picker still works for the session
    }
    setThemeState(t);
  }, []);

  return { theme, setTheme };
}
