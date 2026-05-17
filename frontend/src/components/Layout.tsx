// Layout — the v2 dashboard shell.
// Three areas: 200px sidebar (left) | topbar (60px) | route content (<Outlet />).
//
// One useTheme() instance lives at the layout level so the picker in the
// sidebar shares state with the <html data-theme="..."> attribute applied
// via useEffect inside the hook.

import { Outlet } from "react-router-dom";
import { Sidebar } from "./Sidebar";
import { Topbar } from "./Topbar";
import { useTheme } from "../hooks/useTheme";

export function Layout() {
  const { theme, setTheme } = useTheme();

  return (
    <div
      className="cm"
      style={{
        display: "flex",
        minHeight: "100vh",
        background: "var(--bg)",
        color: "var(--ink)",
      }}
    >
      <Sidebar theme={theme} setTheme={setTheme} />
      <div
        style={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          minWidth: 0,
        }}
      >
        <Topbar />
        <main
          style={{
            flex: 1,
            overflow: "auto",
            background: "var(--bg)",
          }}
        >
          <Outlet />
        </main>
      </div>
    </div>
  );
}
