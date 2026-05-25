import { create } from "zustand";

type Theme = "light" | "mid" | "dark";
type Density = "compact" | "regular" | "comfy";

interface ThemeState {
  theme: Theme;
  density: Density;
  setTheme: (t: Theme) => void;
  setDensity: (d: Density) => void;
  hydrate: () => Promise<void>;
}

const applyToDOM = (theme: Theme, density: Density) => {
  document.documentElement.setAttribute("data-theme", theme);
  document.documentElement.setAttribute("data-density", density);
};

const persist = (theme: Theme, density: Density) => {
  fetch("/api/v2/preferences", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ theme, density }),
  }).catch(() => {});
};

export const useThemeStore = create<ThemeState>((set, get) => ({
  theme: "light",
  density: "regular",

  setTheme: (theme) => {
    set({ theme });
    applyToDOM(theme, get().density);
    persist(theme, get().density);
  },

  setDensity: (density) => {
    set({ density });
    applyToDOM(get().theme, density);
    persist(get().theme, density);
  },

  hydrate: async () => {
    try {
      const res = await fetch("/api/v2/preferences");
      if (res.ok) {
        const prefs = await res.json();
        const theme = prefs.theme ?? "light";
        const density = prefs.density ?? "regular";
        set({ theme, density });
        applyToDOM(theme, density);
      }
    } catch {
      applyToDOM(get().theme, get().density);
    }
  },
}));