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
