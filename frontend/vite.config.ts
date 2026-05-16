import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "node:path";

// ClawMetry v2 — Vite build config.
//
// outDir: bundle lands inside the Python package so `pip install clawmetry`
// ships the prebuilt React app via setup.py's package_data glob.
// base: mounted at /v2/ by the Flask blueprint (clawmetry/v2/routes.py).
// server.proxy: in dev (`npm run dev`), proxy /api → Flask on :8900 so we
// can hit live endpoints without CORS plumbing.
export default defineConfig({
  plugins: [react()],
  base: "/v2/",
  build: {
    outDir: path.resolve(__dirname, "../clawmetry/static/v2/dist"),
    emptyOutDir: true,
    sourcemap: false,
  },
  server: {
    port: 5173,
    proxy: {
      "/api": "http://localhost:8900",
    },
  },
});
