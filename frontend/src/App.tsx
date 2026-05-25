import { Routes, Route } from "react-router-dom";
import { Layout } from "./components/Layout";
import { WelcomePage } from "./pages/WelcomePage";
import { StubPage } from "./pages/StubPage";
import { NAV_ITEMS } from "./components/nav";
import { useEffect } from "react";
import { useThemeStore } from "./stores/themeStore";
import { OpsPage } from "./pages/OpsPage";
import { BrainPage } from "./pages/BrainPage";

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
        <Route path="brain" element={<BrainPage />} />
        {NAV_ITEMS.filter((it) => it.id !== "ops" && it.id !== "brain").map((it) => (
          <Route key={it.id} path={it.id} element={<StubPage slug={it.id} />} />
        ))}
        {/* SPA catch-all — unknown deep links land on the welcome page rather
            than a 404 wall, keeping the chrome visible. */}
        <Route path="*" element={<WelcomePage />} />
      </Route>
    </Routes>
  );
}
