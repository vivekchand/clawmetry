// Single source of truth for v2 sidebar nav.
// Each item maps to a /v2/<path> route and a placeholder "Coming soon" page
// pointing at the GitHub issue tracking that tab's port.
//
// The id is the slug used in the URL. Section drives the grouping in the
// sidebar. Tabs from the design handoff README §"Phase 2 · Dashboard restyle".
export type NavSection = "live" | "history" | "fleet";

export interface NavItem {
  id: string;
  label: string;
  icon: string;
  section: NavSection;
  badge?: string | null;
  issue: number; // GitHub issue tracking the port
}

// Issue numbers are placeholders; sub-issues land in #1492 EPIC.
export const NAV_ITEMS: NavItem[] = [
  // LIVE — the "right now" pane
  { id: "trace", label: "Live trace", icon: "◐", section: "live", issue: 1505 },
  { id: "brain", label: "Brain", icon: "✦", section: "live", issue: 1506 },
  { id: "context", label: "Context", icon: "▤", section: "live", issue: 1507 },
  { id: "approvals", label: "Approvals", icon: "✋", section: "live", badge: "PRO", issue: 1508 },

  // HISTORY — looking back
  { id: "cost", label: "Cost", icon: "$", section: "history", issue: 1509 },
  { id: "subagents", label: "Sub agents", icon: "⇲", section: "history", issue: 1510 },
  { id: "skills", label: "Skills", icon: "✎", section: "history", issue: 1511 },

  // FLEET — multi-node + governance
  // (Fleet sonar removed 2026-05-19, issue #1716 — surface never rendered
  // anything useful; users get multi-node observability via the Fleet view
  // backed by /api/nodes and the system-health stream.)
  { id: "ops", label: "Ops", icon: "◍", section: "fleet", issue: 1512 },
  { id: "rules", label: "Rules", icon: "⚙", section: "fleet", badge: "PRO", issue: 1514 },
  { id: "settings", label: "Settings", icon: "⌥", section: "fleet", issue: 1515 },
];

export const SECTION_LABELS: Record<NavSection, string> = {
  live: "LIVE",
  history: "HISTORY",
  fleet: "FLEET",
};

export function getNavItemBySlug(slug: string): NavItem | undefined {
  return NAV_ITEMS.find((it) => it.id === slug);
}
