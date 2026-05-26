// Tool policy — the governance surface: which tools can run, where they run,
// and what got approved/denied and why.
//
// Three panels:
//   1. Posture summary chips (agents, sandboxed count, strongest mode).
//   2. Sandbox-mode matrix — one expandable row per agent; click to reveal
//      that agent's effective allow/deny tool lists + config provenance.
//   3. Approval timeline — exec-approval decisions, filterable by status.
//
// Live APIs (routes/policy.py):
//   GET /api/tool-policy      → {agents:[…], summary:{…}}
//   GET /api/approvals-audit  → {decisions:[…], summary:{…}}
// Polls every 6s while visible; never crashes on empty data.

import { useState, useEffect, useRef } from "react";

interface Agent {
  agent_id: string;
  node_id?: string;
  sandbox_mode?: string;
  sandbox_scope?: string;
  workspace_access?: string;
  workspace_root?: string;
  session_is_sandboxed?: boolean | number;
  allow?: string[];
  deny?: string[];
  allow_count?: number;
  deny_count?: number;
  sources?: Record<string, unknown>;
  elevated_enabled?: boolean | number;
}

interface PolicySummary {
  agent_count: number;
  sandboxed_agents: number;
  strongest_mode?: string | null;
  total_allowed_tools: number;
  total_denied_tools: number;
}

interface Decision {
  id?: string | number;
  action?: string;
  args_preview?: string;
  status: string;
  decision?: string | null;
  decision_reason?: string | null;
  resolver?: string;
  requestor_session_id?: string;
  created_at?: string | number;
  resolved_at?: string | number;
}

interface AuditSummary {
  total: number;
  pending: number;
  approved: number;
  denied: number;
}

// Sandbox mode → [text colour, wash] — more restrictive reads "safer" (moss).
function modeColors(mode?: string): [string, string] {
  switch ((mode || "off").toLowerCase()) {
    case "all":
      return ["var(--moss)", "var(--moss-soft)"];
    case "non-main":
    case "nonmain":
      return ["var(--amber)", "var(--amber-soft)"];
    default:
      return ["var(--claw-red)", "var(--claw-red-wash)"];
  }
}

function statusColors(status: string): [string, string] {
  switch ((status || "").toLowerCase()) {
    case "approved":
    case "allow":
    case "allowed":
      return ["var(--moss)", "var(--moss-soft)"];
    case "denied":
    case "deny":
    case "blocked":
    case "rejected":
      return ["var(--claw-red)", "var(--claw-red-wash)"];
    default:
      return ["var(--amber)", "var(--amber-soft)"];
  }
}

function fmtTime(t?: string | number): string {
  if (!t) return "—";
  const ms = typeof t === "number" ? (t < 1e12 ? t * 1000 : t) : Date.parse(String(t));
  if (!ms || Number.isNaN(ms)) return String(t).slice(0, 19);
  const d = new Date(ms);
  return d.toLocaleString(undefined, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
}

function ToolChips({ items, color }: { items: string[]; color: string }) {
  if (!items || items.length === 0) {
    return <span className="mono" style={{ fontSize: 10, color: "var(--ink-4)" }}>—</span>;
  }
  return (
    <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
      {items.map((t) => (
        <span
          key={t}
          className="mono"
          style={{ fontSize: 10, color, border: `1px solid ${color}`, borderRadius: 4, padding: "1px 6px", opacity: 0.9 }}
        >
          {t}
        </span>
      ))}
    </div>
  );
}

function AgentRow({ agent }: { agent: Agent }) {
  const [open, setOpen] = useState(false);
  const [fg, bg] = modeColors(agent.sandbox_mode);
  const allow = agent.allow ?? [];
  const deny = agent.deny ?? [];
  const sources = agent.sources ?? {};
  return (
    <div style={{ borderTop: "1px dashed var(--line)" }}>
      <div
        onClick={() => setOpen(!open)}
        style={{ display: "flex", alignItems: "center", gap: 10, padding: "10px 14px", cursor: "pointer", fontSize: 12 }}
      >
        <span style={{ fontSize: 10, color: "var(--ink-4)", width: 12 }}>{open ? "▾" : "▸"}</span>
        <span style={{ flex: 1, fontWeight: 600, color: "var(--ink-2)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", minWidth: 0 }}>
          {agent.agent_id || "(unknown agent)"}
        </span>
        <span className="mono" style={{ fontSize: 10, color: fg, background: bg, borderRadius: 4, padding: "1px 7px", fontWeight: 700 }}>
          sandbox: {agent.sandbox_mode || "off"}
        </span>
        <span className="mono" style={{ fontSize: 10, color: "var(--moss)" }}>{allow.length || agent.allow_count || 0} allow</span>
        <span className="mono" style={{ fontSize: 10, color: "var(--claw-red)" }}>{deny.length || agent.deny_count || 0} deny</span>
      </div>
      {open && (
        <div style={{ padding: "4px 14px 14px 36px", display: "flex", flexDirection: "column", gap: 10 }}>
          <div style={{ display: "flex", gap: 16, flexWrap: "wrap" }}>
            <div className="mono" style={{ fontSize: 10, color: "var(--ink-4)" }}>
              scope <span style={{ color: "var(--ink-2)" }}>{agent.sandbox_scope || "—"}</span>
            </div>
            <div className="mono" style={{ fontSize: 10, color: "var(--ink-4)" }}>
              workspace <span style={{ color: "var(--ink-2)" }}>{agent.workspace_access || "—"}</span>
            </div>
            <div className="mono" style={{ fontSize: 10, color: "var(--ink-4)" }}>
              elevated <span style={{ color: agent.elevated_enabled ? "var(--amber)" : "var(--ink-2)" }}>{agent.elevated_enabled ? "yes" : "no"}</span>
            </div>
            {agent.node_id && (
              <div className="mono" style={{ fontSize: 10, color: "var(--ink-4)" }}>
                node <span style={{ color: "var(--ink-2)" }}>{agent.node_id}</span>
              </div>
            )}
          </div>
          <div>
            <div className="caps" style={{ color: "var(--moss)", marginBottom: 4 }}>Allow ({allow.length})</div>
            <ToolChips items={allow} color="var(--moss)" />
          </div>
          <div>
            <div className="caps" style={{ color: "var(--claw-red)", marginBottom: 4 }}>Deny ({deny.length})</div>
            <ToolChips items={deny} color="var(--claw-red)" />
          </div>
          {Object.keys(sources).length > 0 && (
            <div>
              <div className="caps" style={{ color: "var(--ink-4)", marginBottom: 4 }}>Provenance</div>
              <pre className="mono" style={{ fontSize: 10, color: "var(--ink-3)", margin: 0, whiteSpace: "pre-wrap", background: "var(--panel-2)", padding: 8, borderRadius: 5 }}>
                {JSON.stringify(sources, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function DecisionRow({ d }: { d: Decision }) {
  const [open, setOpen] = useState(false);
  const [fg, bg] = statusColors(d.status);
  return (
    <div style={{ borderTop: "1px dashed var(--line)" }}>
      <div
        onClick={() => setOpen(!open)}
        style={{ display: "flex", alignItems: "center", gap: 10, padding: "8px 14px", cursor: "pointer", fontSize: 12 }}
      >
        <span className="mono" style={{ fontSize: 10, color: fg, background: bg, borderRadius: 4, padding: "1px 7px", fontWeight: 700, minWidth: 64, textAlign: "center" }}>
          {d.status}
        </span>
        <span style={{ flex: 1, color: "var(--ink-2)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", minWidth: 0 }} title={d.action || ""}>
          {d.action || "(action)"}{d.args_preview ? <span className="mono" style={{ color: "var(--ink-4)", marginLeft: 6, fontSize: 11 }}>{d.args_preview}</span> : null}
        </span>
        <span className="mono" style={{ fontSize: 10, color: "var(--ink-4)", whiteSpace: "nowrap" }}>{fmtTime(d.created_at)}</span>
      </div>
      {open && (
        <div className="mono" style={{ padding: "4px 14px 12px 36px", fontSize: 10, color: "var(--ink-3)", lineHeight: 1.8 }}>
          {d.decision != null && <div><span style={{ color: "var(--ink-4)" }}>decision</span> {d.decision}</div>}
          {d.decision_reason && <div><span style={{ color: "var(--ink-4)" }}>reason</span> {d.decision_reason}</div>}
          {d.resolver && <div><span style={{ color: "var(--ink-4)" }}>resolver</span> {d.resolver}</div>}
          {d.requestor_session_id && <div><span style={{ color: "var(--ink-4)" }}>session</span> {d.requestor_session_id}</div>}
          {d.resolved_at && <div><span style={{ color: "var(--ink-4)" }}>resolved</span> {fmtTime(d.resolved_at)}</div>}
          {d.args_preview && <div><span style={{ color: "var(--ink-4)" }}>args</span> {d.args_preview}</div>}
        </div>
      )}
    </div>
  );
}

const STATUS_FILTERS = ["", "pending", "approved", "denied"] as const;

export function ToolPolicyPage() {
  const [agents, setAgents] = useState<Agent[] | null>(null);
  const [policySummary, setPolicySummary] = useState<PolicySummary | null>(null);
  const [decisions, setDecisions] = useState<Decision[]>([]);
  const [auditSummary, setAuditSummary] = useState<AuditSummary | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [errored, setErrored] = useState(false);
  const timer = useRef<ReturnType<typeof setInterval> | null>(null);
  const filterRef = useRef(statusFilter);
  filterRef.current = statusFilter;

  useEffect(() => {
    let cancelled = false;
    async function load() {
      if (typeof document !== "undefined" && document.hidden) return;
      try {
        const qs = filterRef.current ? `?status=${filterRef.current}` : "";
        const [p, a] = await Promise.all([
          fetch("/api/tool-policy").then((r) => r.json()),
          fetch(`/api/approvals-audit${qs}`).then((r) => r.json()),
        ]);
        if (cancelled) return;
        setAgents(p?.agents ?? []);
        setPolicySummary(p?.summary ?? null);
        setDecisions(a?.decisions ?? []);
        setAuditSummary(a?.summary ?? null);
        setErrored(false);
      } catch (e) {
        console.error(e);
        if (!cancelled) setErrored(true);
      }
    }
    load();
    timer.current = setInterval(load, 6000);
    return () => {
      cancelled = true;
      if (timer.current) clearInterval(timer.current);
    };
  }, [statusFilter]);

  if (agents === null) {
    return (
      <div style={{ padding: 40, color: "var(--ink-4)" }} className="mono">
        {errored ? "Failed to load tool policy." : "Loading tool policy…"}
      </div>
    );
  }

  const ps = policySummary;
  const as = auditSummary;

  return (
    <div style={{ flex: 1, display: "flex", flexDirection: "column", minWidth: 0 }}>
      <div style={{ flex: 1, padding: 22, overflow: "auto", display: "flex", flexDirection: "column", gap: 16 }}>

        {/* ── Posture chips ── */}
        <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
          {[
            ["agents", ps?.agent_count ?? 0, "var(--ink-2)"],
            ["sandboxed", ps?.sandboxed_agents ?? 0, "var(--moss)"],
            ["strongest mode", ps?.strongest_mode ?? "—", modeColors(ps?.strongest_mode ?? undefined)[0]],
            ["tools allowed", ps?.total_allowed_tools ?? 0, "var(--moss)"],
            ["tools denied", ps?.total_denied_tools ?? 0, "var(--claw-red)"],
          ].map(([label, val, color]) => (
            <div key={String(label)} className="cm-card" style={{ padding: "10px 16px", minWidth: 120 }}>
              <div className="caps" style={{ color: "var(--ink-4)" }}>{label}</div>
              <div className="display" style={{ fontSize: 24, color: color as string, marginTop: 2 }}>{val}</div>
            </div>
          ))}
        </div>

        {/* ── Sandbox-mode matrix ── */}
        <div className="cm-card" style={{ padding: 0, overflow: "hidden" }}>
          <div className="caps" style={{ color: "var(--ink-4)", padding: "12px 14px", borderBottom: "1px solid var(--line)" }}>
            Sandbox-mode matrix · {agents.length} agents · click a row for allow/deny
          </div>
          {agents.length > 0 ? (
            agents.map((a, i) => <AgentRow key={a.agent_id ?? i} agent={a} />)
          ) : (
            <div className="mono" style={{ fontSize: 11, color: "var(--ink-4)", padding: 14 }}>
              No sandbox policy recorded yet. Run <code>openclaw sandbox explain</code> so the daemon can ingest it.
            </div>
          )}
        </div>

        {/* ── Approval timeline ── */}
        <div className="cm-card" style={{ padding: 0, overflow: "hidden" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10, padding: "12px 14px", borderBottom: "1px solid var(--line)" }}>
            <div className="caps" style={{ color: "var(--ink-4)", flex: 1 }}>
              Approval timeline · {as?.total ?? decisions.length} decisions
              {as ? <span style={{ marginLeft: 8 }}>
                <span style={{ color: "var(--amber)" }}>{as.pending} pending</span> ·{" "}
                <span style={{ color: "var(--moss)" }}>{as.approved} approved</span> ·{" "}
                <span style={{ color: "var(--claw-red)" }}>{as.denied} denied</span>
              </span> : null}
            </div>
            <div style={{ display: "flex", gap: 4 }}>
              {STATUS_FILTERS.map((f) => (
                <button
                  key={f || "all"}
                  className="cm-btn tiny"
                  onClick={() => setStatusFilter(f)}
                  style={{ background: statusFilter === f ? "var(--panel-2)" : undefined, fontWeight: statusFilter === f ? 700 : 400 }}
                >
                  {f || "all"}
                </button>
              ))}
            </div>
          </div>
          {decisions.length > 0 ? (
            decisions.map((d, i) => <DecisionRow key={d.id ?? i} d={d} />)
          ) : (
            <div className="mono" style={{ fontSize: 11, color: "var(--ink-4)", padding: 14 }}>
              No approval decisions recorded{statusFilter ? ` with status “${statusFilter}”` : ""}.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
