// Topbar — 14px padding, paper bg, 1px bottom border.
//
// Ports DashTopbar from design_handoff_clawmetry_v3/boards-dashboards.jsx
// (lines ~62-70). Adds:
//   - Title + mono subtitle bound to the current route
//   - Ghost action buttons (export / share) as placeholders
//   - LIVE / AWAIT / ALERT status pill (defaults to LIVE)
//   - Pill-link "✨ You're on v2 (beta) · Back to v1 ↩" pointing at "/"
//     (the cross-version link required by the README "What to communicate" rule)

import { useLocation } from "react-router-dom";
import { getNavItemBySlug } from "./nav";

interface RouteMeta {
  title: string;
  subtitle: string;
}

const ROUTE_META: Record<string, RouteMeta> = {
  "": {
    title: "Welcome to v2",
    subtitle: "preview build · sidebar nav is wired, tabs land in week 2",
  },
  trace: { title: "Live trace", subtitle: "the hood, real time" },
  brain: { title: "Brain", subtitle: "per-turn reasoning chain" },
  context: { title: "Context", subtitle: "what the LLM sees this turn" },
  approvals: { title: "Approvals", subtitle: "hold the claw, needs human" },
  cost: { title: "Cost", subtitle: "tokens, dollars, anomalies" },
  subagents: { title: "Sub agents", subtitle: "7-day swimlanes" },
  skills: { title: "Skills", subtitle: "IDE for the agent's playbook" },
  ops: { title: "Ops", subtitle: "heartbeats and crons" },
  rules: { title: "Rules", subtitle: "guardrails as a graph" },
  settings: { title: "Settings", subtitle: "workspace, team, billing" },
};

function metaForPath(pathname: string): RouteMeta {
  // basename is /v2, so location.pathname comes through as "/" or "/trace" etc.
  const slug = pathname.replace(/^\/+/, "").split("/")[0] ?? "";
  return ROUTE_META[slug] ?? {
    title: getNavItemBySlug(slug)?.label ?? "ClawMetry v2",
    subtitle: "preview build",
  };
}

export function Topbar() {
  const { pathname } = useLocation();
  const meta = metaForPath(pathname);

  return (
    <header
      style={{
        padding: "14px 22px",
        borderBottom: "1px solid var(--line)",
        background: "var(--paper)",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        gap: 16,
        flex: "0 0 auto",
      }}
    >
      <div style={{ minWidth: 0 }}>
        <div
          style={{
            fontSize: 16,
            fontWeight: 500,
            color: "var(--ink)",
            lineHeight: 1.1,
          }}
        >
          {meta.title}
        </div>
        <div
          className="mono"
          style={{
            fontSize: 10,
            color: "var(--ink-4)",
            marginTop: 2,
          }}
        >
          {meta.subtitle}
        </div>
      </div>

      <div style={{ display: "flex", gap: 8, alignItems: "center", flexShrink: 0 }}>
        {/* Placeholder action buttons — real handlers land per-tab in week 2+ */}
        <button
          type="button"
          className="cm-btn ghost tiny"
          title="Export (coming soon)"
          disabled
          style={{ opacity: 0.55, cursor: "not-allowed" }}
        >
          ⤓ export
        </button>
        <button
          type="button"
          className="cm-btn ghost tiny"
          title="Share (coming soon)"
          disabled
          style={{ opacity: 0.55, cursor: "not-allowed" }}
        >
          share ↗
        </button>

        {/* Default LIVE pill — per-tab overrides land in week 2+ */}
        <span
          className="cm-badge"
          style={{ color: "var(--moss)", fontSize: 10 }}
          title="Live data stream"
        >
          <span className="dot cm-pulse" /> LIVE
        </span>

        {/* Cross-version pill-link — README §Migration strategy mandates this */}
        <a
          href="/"
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 6,
            padding: "4px 12px",
            borderRadius: 999,
            border: "1px solid var(--claw-red)",
            background: "var(--claw-red-wash)",
            color: "var(--claw-red-deep)",
            fontSize: 11,
            fontWeight: 500,
            textDecoration: "none",
            whiteSpace: "nowrap",
            transition: "background 120ms ease-out",
          }}
          onMouseEnter={(e) => {
            (e.currentTarget as HTMLAnchorElement).style.background =
              "var(--claw-red-soft)";
          }}
          onMouseLeave={(e) => {
            (e.currentTarget as HTMLAnchorElement).style.background =
              "var(--claw-red-wash)";
          }}
        >
          <span aria-hidden="true">✨</span>
          <span>You're on v2 (beta) · Back to v1 ↩</span>
        </a>
      </div>
    </header>
  );
}
