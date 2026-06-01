// i18n must initialise before the React tree mounts so that the language
// detector has resolved and the first render uses the correct locale.
import "./i18n";
import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import "./styles.css";

// /v2/ is the SPA root (matches vite.config.ts `base` + Flask blueprint mount).
ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter basename="/v2">
      <App />
    </BrowserRouter>
  </React.StrictMode>,
);
