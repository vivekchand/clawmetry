import { Routes, Route } from "react-router-dom";
import { Layout } from "./components/Layout";
import { WelcomePage } from "./pages/WelcomePage";
import { StubPage } from "./pages/StubPage";
import { NAV_ITEMS } from "./components/nav";
import { useEffect } from "react";
import { useThemeStore } from "./stores/themeStore";
import { OpsPage } from "./pages/OpsPage";
import { ContextPage } from "./pages/ContextPage";
import { BrainPage } from "./pages/BrainPage";
import { SubAgentsPage } from "./pages/SubAgentsPage";
import { TurnAnatomyPage } from "./pages/TurnAnatomyPage";
import { ToolPolicyPage } from "./pages/ToolPolicyPage";
import { ContextEconomicsPage } from "./pages/ContextEconomicsPage";
import { ToolCatalogPage } from "./pages/ToolCatalogPage";
import { CostPage } from "./pages/CostPage";

// Nav slugs that now have a real React page (so the stub fallback skips them).
const REAL_PAGES = new Set([
  "ops",
  "context",
  "brain",
  "subagents",
  "trace",
  "rules",
  "context-econ",
  "tools",
  "cost",
]);

// All v2 routes live inside <Layout>, which renders the sidebar + topbar
// chrome and an <Outlet /> for route content. Every NAV_ITEMS entry maps
// to a /v2/<slug> route → <StubPage> for now ("Coming soon · see issue #N").
// When a real tab lands, swap that route's element for the real component.
export default function App() {
  const hydrate = useThemeStore((s) => s.hydrate);
  useEffect(() => {
    hydrate();
  }, [hydrate]);

  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<WelcomePage />} />
        <Route path="ops" element={<OpsPage />} />
        <Route path="context" element={<ContextPage />} />
        <Route path="brain" element={<BrainPage />} />
        <Route path="subagents" element={<SubAgentsPage />} />
        <Route path="trace" element={<TurnAnatomyPage />} />
        <Route path="rules" element={<ToolPolicyPage />} />
        <Route path="context-econ" element={<ContextEconomicsPage />} />
        <Route path="tools" element={<ToolCatalogPage />} />
        <Route path="cost" element={<CostPage />} />
        {NAV_ITEMS.filter((it) => !REAL_PAGES.has(it.id)).map((it) => (
          <Route key={it.id} path={it.id} element={<StubPage slug={it.id} />} />
        ))}
        {/* SPA catch-all — unknown deep links land on the welcome page rather
            than a 404 wall, keeping the chrome visible. */}
        <Route path="*" element={<WelcomePage />} />
      </Route>
    </Routes>
  );
}
