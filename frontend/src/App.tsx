import { Routes, Route } from "react-router-dom";
import { Layout } from "./components/Layout";
import { WelcomePage } from "./pages/WelcomePage";
import { StubPage } from "./pages/StubPage";
import { NAV_ITEMS } from "./components/nav";

// All v2 routes live inside <Layout>, which renders the sidebar + topbar
// chrome and an <Outlet /> for route content. Every NAV_ITEMS entry maps
// to a /v2/<slug> route → <StubPage> for now ("Coming soon · see issue #N").
// When a real tab lands, swap that route's element for the real component.
export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<WelcomePage />} />
        {NAV_ITEMS.map((it) => (
          <Route key={it.id} path={it.id} element={<StubPage slug={it.id} />} />
        ))}
        {/* SPA catch-all — unknown deep links land on the welcome page rather
            than a 404 wall, keeping the chrome visible. */}
        <Route path="*" element={<WelcomePage />} />
      </Route>
    </Routes>
  );
}
