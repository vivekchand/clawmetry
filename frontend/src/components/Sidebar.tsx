// Sidebar — 200px wide, paper bg, 1px right border.
//
// Ports DashSidebar from design_handoff_clawmetry_v3/boards-dashboards.jsx
// (lines ~7-60). Differences from the spec:
//   - Items are <NavLink> from react-router (active state comes from the URL,
//     not a prop)
//   - Grouped with section headers (LIVE / HISTORY / FLEET)
//   - Bottom row includes the 3-button theme picker (light / mid / dark)
//
// All colors via var(--*) so theme switching just works.

import { NavLink } from "react-router-dom";
import { Clawbert, ClawMark } from "../mascot";
import { NAV_ITEMS, SECTION_LABELS, type NavItem, type NavSection } from "./nav";
import type { Theme } from "../hooks/useTheme";

interface SidebarProps {
  theme: Theme;
  setTheme: (t: Theme) => void;
}

export function Sidebar({ theme, setTheme }: SidebarProps) {
  const sections: NavSection[] = ["live", "history", "fleet"];

  return (
    <aside
      style={{
        width: 200,
        flex: "0 0 200px",
        borderRight: "1px solid var(--line)",
        background: "var(--paper)",
        display: "flex",
        flexDirection: "column",
        minHeight: "100vh",
      }}
    >
      {/* Header — mascot + wordmark + version chip */}
      <div
        style={{
          padding: "16px 16px 8px",
          display: "flex",
          alignItems: "center",
          gap: 8,
        }}
      >
        <ClawMark size={28} />
        <div
          className="display"
          style={{
            fontSize: 22,
            lineHeight: 1,
            letterSpacing: "-0.01em",
          }}
        >
          clawmetry
        </div>
      </div>
      <div style={{ padding: "0 16px 10px" }}>
        <span
          className="cm-tag"
          style={{ fontSize: 9, padding: "2px 6px" }}
          title="ClawMetry v2 preview build"
        >
          v0.9 · OSS
        </span>
      </div>

      {/* Workspace selector — static chip for now, menu lands in week 2 */}
      <div style={{ padding: "0 12px 6px" }}>
        <div
          className="cm-card"
          style={{
            padding: "6px 8px",
            display: "flex",
            alignItems: "center",
            gap: 6,
            background: "var(--panel-2)",
            borderRadius: 8,
          }}
          title="Workspace selector (menu lands in week 2)"
        >
          <span
            className="mono"
            style={{ fontSize: 10, color: "var(--ink-3)", flex: 1 }}
          >
            default · local
          </span>
          <span style={{ color: "var(--ink-4)", fontSize: 10 }}>▾</span>
        </div>
      </div>

      {/* Grouped nav */}
      <nav
        style={{
          padding: "8px 8px 0",
          display: "flex",
          flexDirection: "column",
          gap: 12,
          flex: 1,
          overflowY: "auto",
        }}
      >
        {sections.map((section) => {
          const items = NAV_ITEMS.filter((it) => it.section === section);
          if (items.length === 0) return null;
          return (
            <div key={section}>
              <div
                className="caps"
                style={{
                  color: "var(--ink-4)",
                  padding: "4px 10px 6px",
                  fontSize: 9,
                }}
              >
                {SECTION_LABELS[section]}
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
                {items.map((it) => (
                  <NavItemLink key={it.id} item={it} />
                ))}
              </div>
            </div>
          );
        })}
      </nav>

      {/* Bottom — mascot + status + theme picker */}
      <div
        style={{
          padding: 12,
          borderTop: "1px dashed var(--line)",
          display: "flex",
          flexDirection: "column",
          gap: 10,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <Clawbert size={22} mood="happy" tool={null} />
          <div style={{ minWidth: 0 }}>
            <div style={{ fontSize: 11, color: "var(--ink-2)" }}>ClawMetry</div>
            <div
              className="mono"
              style={{
                fontSize: 9,
                color: "var(--ink-4)",
                whiteSpace: "nowrap",
                overflow: "hidden",
                textOverflow: "ellipsis",
              }}
            >
              watching · all clear
            </div>
          </div>
        </div>
        <ThemePicker theme={theme} setTheme={setTheme} />
      </div>
    </aside>
  );
}

function NavItemLink({ item }: { item: NavItem }) {
  return (
    <NavLink
      to={`/${item.id}`}
      style={({ isActive }) => ({
        display: "flex",
        alignItems: "center",
        gap: 8,
        padding: "7px 10px",
        borderRadius: 6,
        textDecoration: "none",
        background: isActive ? "var(--paper-deep)" : "transparent",
        color: isActive ? "var(--ink)" : "var(--ink-3)",
        fontSize: 13,
        fontWeight: isActive ? 500 : 400,
        cursor: "pointer",
        transition: "background 120ms ease-out, color 120ms ease-out",
      })}
    >
      {({ isActive }) => (
        <>
          <span
            style={{
              width: 16,
              fontFamily: "var(--f-mono)",
              fontSize: 12,
              color: isActive ? "var(--claw-red)" : "var(--ink-4)",
              textAlign: "center",
            }}
            aria-hidden="true"
          >
            {item.icon}
          </span>
          <span style={{ flex: 1 }}>{item.label}</span>
          {item.badge && (
            <span
              className="cm-tag"
              style={{
                padding: "0 5px",
                fontSize: 9,
                background:
                  item.badge === "PRO" ? "var(--plum-soft)" : "var(--panel)",
                color:
                  item.badge === "PRO" ? "var(--plum)" : "var(--ink-3)",
                borderColor:
                  item.badge === "PRO" ? "var(--plum)" : "var(--line)",
              }}
            >
              {item.badge}
            </span>
          )}
        </>
      )}
    </NavLink>
  );
}

// Three-button theme toggle. CSS variables in styles.css do all the heavy
// lifting; we just flip <html data-theme="...">.
function ThemePicker({ theme, setTheme }: { theme: Theme; setTheme: (t: Theme) => void }) {
  const opts: { id: Theme; label: string; title: string }[] = [
    { id: "light", label: "Light", title: "Light theme (paper)" },
    { id: "mid", label: "Mid", title: "Mid theme (shop floor)" },
    { id: "dark", label: "Dark", title: "Dark theme (engine room)" },
  ];
  return (
    <div
      role="radiogroup"
      aria-label="Theme picker"
      style={{
        display: "flex",
        background: "var(--panel-2)",
        border: "1px solid var(--line)",
        borderRadius: 999,
        padding: 2,
        gap: 0,
      }}
    >
      {opts.map((o) => {
        const active = theme === o.id;
        return (
          <button
            key={o.id}
            type="button"
            role="radio"
            aria-checked={active}
            title={o.title}
            onClick={() => setTheme(o.id)}
            style={{
              flex: 1,
              padding: "4px 0",
              fontFamily: "var(--f-sans)",
              fontSize: 10,
              fontWeight: active ? 600 : 400,
              color: active ? "#FFF8EE" : "var(--ink-3)",
              background: active ? "var(--claw-red)" : "transparent",
              border: "none",
              borderRadius: 999,
              cursor: "pointer",
              transition: "background 120ms ease-out, color 120ms ease-out",
            }}
          >
            {o.label}
          </button>
        );
      })}
    </div>
  );
}
