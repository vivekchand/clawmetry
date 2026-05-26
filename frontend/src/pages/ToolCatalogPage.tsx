// Tool catalog — every tool the agent can call, grouped by provenance
// (builtin / mcp / plugin) with call volume + p50/p95 latency + error rate.
//
// Click a tool row to drill into its recent individual calls (lazily fetched
// from /api/tool-catalog/<name>/calls): a per-call latency strip + status +
// the session each call belongs to. Sortable by calls / p95 / error rate /
// name; filterable by provenance.
//
// Live APIs (routes/tool_catalog.py):
//   GET /api/tool-catalog                  → {tools:[…], groups, totals}
//   GET /api/tool-catalog/<name>/calls     → {calls:[…]}
// Polls every 7s while visible; never crashes on empty data.

import { useState, useEffect, useRef } from "react";

interface Tool {
  name: string;
  provenance: string;
  provider?: string | null;
  calls: number;
  p50_ms: number | null;
  p95_ms: number | null;
  error_rate: number;
  errors?: number;
  timed_calls?: number;
}

interface CatalogData {
  tools: Tool[];
  groups: { builtin: number; mcp: number; plugin: number };
  totals: { tool_count: number; total_calls: number; builtin_universe: number };
}

interface Call {
  ts_ms: number | null;
  duration_ms: number | null;
  status: string;
  session_id?: string | null;
}

type SortKey = "calls" | "p95_ms" | "error_rate" | "name";

const PROV_COLOR: Record<string, string> = {
  builtin: "var(--moss)",
  mcp: "var(--plum)",
  plugin: "var(--amber)",
};

function provColor(p: string): string {
  return PROV_COLOR[p] ?? "var(--ink-4)";
}

function fmtMs(ms: number | null): string {
  if (ms == null) return "—";
  if (ms < 1000) return `${Math.round(ms)}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

function fmtTime(ms: number | null): string {
  if (!ms) return "—";
  return new Date(ms).toLocaleString(undefined, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

// Per-tool drill-in: a lazily-loaded latency strip of recent calls.
function ToolDetail({ name }: { name: string }) {
  const [calls, setCalls] = useState<Call[] | null>(null);
  const [errored, setErrored] = useState(false);

  useEffect(() => {
    let cancelled = false;
    fetch(`/api/tool-catalog/${encodeURIComponent(name)}/calls`)
      .then((r) => r.json())
      .then((d) => { if (!cancelled) setCalls(d?.calls ?? []); })
      .catch((e) => { console.error(e); if (!cancelled) setErrored(true); });
    return () => { cancelled = true; };
  }, [name]);

  if (calls === null) {
    return <div className="mono" style={{ fontSize: 10, color: "var(--ink-4)", padding: "8px 14px 12px 32px" }}>{errored ? "Failed to load calls." : "Loading calls…"}</div>;
  }
  if (calls.length === 0) {
    return <div className="mono" style={{ fontSize: 10, color: "var(--ink-4)", padding: "8px 14px 12px 32px" }}>No individual calls captured.</div>;
  }

  const durs = calls.map((c) => c.duration_ms ?? 0);
  const maxDur = Math.max(1, ...durs);

  return (
    <div style={{ padding: "8px 14px 14px 32px", background: "var(--panel-2)" }}>
      {/* latency strip (newest → oldest) */}
      <div className="caps" style={{ color: "var(--ink-4)", marginBottom: 6 }}>Recent calls · {calls.length} · latency strip</div>
      <div style={{ display: "flex", alignItems: "flex-end", gap: 2, height: 44, marginBottom: 10 }}>
        {calls.slice(0, 60).map((c, i) => {
          const h = Math.max(2, ((c.duration_ms ?? 0) / maxDur) * 44);
          return (
            <div
              key={i}
              title={`${fmtMs(c.duration_ms)} · ${c.status} · ${fmtTime(c.ts_ms)}`}
              style={{ flex: 1, minWidth: 2, height: h, background: c.status === "error" ? "var(--claw-red)" : "var(--ocean, #3b82f6)", borderRadius: 1, opacity: 0.85 }}
            />
          );
        })}
      </div>
      {/* call list */}
      <div style={{ maxHeight: 180, overflow: "auto" }}>
        {calls.slice(0, 40).map((c, i) => (
          <div key={i} style={{ display: "flex", alignItems: "center", gap: 10, fontSize: 11, padding: "3px 0", borderTop: "1px dashed var(--line)" }}>
            <span className="mono" style={{ width: 60, color: c.status === "error" ? "var(--claw-red)" : "var(--moss)" }}>{c.status}</span>
            <span className="mono" style={{ width: 60, color: "var(--ink-2)" }}>{fmtMs(c.duration_ms)}</span>
            <span className="mono" style={{ flex: 1, color: "var(--ink-4)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", minWidth: 0 }}>{c.session_id ? c.session_id.slice(0, 18) : "—"}</span>
            <span className="mono" style={{ color: "var(--ink-4)" }}>{fmtTime(c.ts_ms)}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function ToolRow({ tool, open, onToggle }: { tool: Tool; open: boolean; onToggle: () => void }) {
  const errPct = Math.round((tool.error_rate || 0) * 100);
  return (
    <>
      <div
        onClick={onToggle}
        style={{
          display: "grid",
          gridTemplateColumns: "16px 1.6fr 0.8fr 70px 70px 80px",
          alignItems: "center",
          gap: 8,
          padding: "9px 14px",
          borderTop: "1px dashed var(--line)",
          cursor: "pointer",
          fontSize: 12,
        }}
      >
        <span style={{ fontSize: 10, color: "var(--ink-4)" }}>{open ? "▾" : "▸"}</span>
        <span style={{ color: "var(--ink-2)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", minWidth: 0 }} title={tool.name}>
          <span style={{ width: 7, height: 7, borderRadius: 2, background: provColor(tool.provenance), display: "inline-block", marginRight: 7 }} />
          {tool.name}
        </span>
        <span className="mono" style={{ fontSize: 10, color: "var(--ink-4)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
          {tool.provider || tool.provenance}
        </span>
        <span className="mono" style={{ fontSize: 11, color: "var(--ink-2)", textAlign: "right" }}>{tool.calls.toLocaleString()}</span>
        <span className="mono" style={{ fontSize: 11, color: "var(--ink-3)", textAlign: "right" }}>{fmtMs(tool.p50_ms)}</span>
        <span className="mono" style={{ fontSize: 11, color: (tool.p95_ms ?? 0) > 5000 ? "var(--amber)" : "var(--ink-3)", textAlign: "right" }}>{fmtMs(tool.p95_ms)}</span>
      </div>
      {open && <ToolDetail name={tool.name} />}
    </>
  );
}

const PROV_FILTERS = ["", "builtin", "mcp", "plugin"] as const;

export function ToolCatalogPage() {
  const [data, setData] = useState<CatalogData | null>(null);
  const [sortKey, setSortKey] = useState<SortKey>("calls");
  const [provFilter, setProvFilter] = useState<string>("");
  const [openName, setOpenName] = useState<string | null>(null);
  const [errored, setErrored] = useState(false);
  const timer = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      if (typeof document !== "undefined" && document.hidden) return;
      try {
        const d = await fetch("/api/tool-catalog").then((r) => r.json());
        if (cancelled) return;
        setData(d);
        setErrored(false);
      } catch (e) {
        console.error(e);
        if (!cancelled) setErrored(true);
      }
    }
    load();
    timer.current = setInterval(load, 7000);
    return () => {
      cancelled = true;
      if (timer.current) clearInterval(timer.current);
    };
  }, []);

  if (!data) {
    return (
      <div style={{ padding: 40, color: "var(--ink-4)" }} className="mono">
        {errored ? "Failed to load tool catalog." : "Loading tool catalog…"}
      </div>
    );
  }

  let tools = data.tools ?? [];
  if (provFilter) tools = tools.filter((t) => t.provenance === provFilter);
  const sorted = [...tools].sort((a, b) => {
    if (sortKey === "name") return a.name.localeCompare(b.name);
    const av = (a[sortKey] as number) ?? 0;
    const bv = (b[sortKey] as number) ?? 0;
    return bv - av;
  });

  const groups = data.groups ?? { builtin: 0, mcp: 0, plugin: 0 };
  const totals = data.totals ?? { tool_count: 0, total_calls: 0, builtin_universe: 0 };

  function header(label: string, key: SortKey) {
    const active = sortKey === key;
    return (
      <span
        onClick={() => setSortKey(key)}
        style={{ cursor: "pointer", color: active ? "var(--ink-2)" : "var(--ink-4)", fontWeight: active ? 700 : 600, textAlign: key === "name" ? "left" : "right" }}
      >
        {label}{active ? " ↓" : ""}
      </span>
    );
  }

  return (
    <div style={{ flex: 1, display: "flex", flexDirection: "column", minWidth: 0 }}>
      <div style={{ flex: 1, padding: 22, overflow: "auto", display: "flex", flexDirection: "column", gap: 16 }}>

        {/* ── Provenance group chips ── */}
        <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
          {[
            ["tools", totals.tool_count, "var(--ink-2)"],
            ["total calls", totals.total_calls.toLocaleString(), "var(--ink-2)"],
            ["builtin", groups.builtin, "var(--moss)"],
            ["mcp", groups.mcp, "var(--plum)"],
            ["plugin", groups.plugin, "var(--amber)"],
          ].map(([label, val, color]) => (
            <div key={String(label)} className="cm-card" style={{ padding: "10px 16px", minWidth: 110 }}>
              <div className="caps" style={{ color: "var(--ink-4)" }}>{label}</div>
              <div className="display" style={{ fontSize: 24, color: color as string, marginTop: 2 }}>{val}</div>
            </div>
          ))}
        </div>

        {/* ── Provenance filter ── */}
        <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
          <span className="caps" style={{ color: "var(--ink-4)", marginRight: 4 }}>provenance</span>
          {PROV_FILTERS.map((f) => (
            <button
              key={f || "all"}
              className="cm-btn tiny"
              onClick={() => setProvFilter(f)}
              style={{ background: provFilter === f ? "var(--panel-2)" : undefined, fontWeight: provFilter === f ? 700 : 400 }}
            >
              {f || "all"}
            </button>
          ))}
        </div>

        {/* ── Tool table ── */}
        <div className="cm-card" style={{ padding: 0, overflow: "hidden" }}>
          <div
            className="mono"
            style={{
              display: "grid",
              gridTemplateColumns: "16px 1.6fr 0.8fr 70px 70px 80px",
              alignItems: "center",
              gap: 8,
              padding: "10px 14px",
              background: "var(--panel-2)",
              fontSize: 9,
              textTransform: "uppercase",
              letterSpacing: "0.06em",
            }}
          >
            <span />
            {header("tool", "name")}
            <span style={{ color: "var(--ink-4)" }}>provider</span>
            {header("calls", "calls")}
            <span style={{ color: "var(--ink-4)", textAlign: "right" }}>p50</span>
            {header("p95", "p95_ms")}
          </div>
          {sorted.length > 0 ? (
            sorted.map((t) => (
              <ToolRow
                key={t.name}
                tool={t}
                open={openName === t.name}
                onToggle={() => setOpenName(openName === t.name ? null : t.name)}
              />
            ))
          ) : (
            <div className="mono" style={{ fontSize: 11, color: "var(--ink-4)", padding: 14 }}>
              No tool calls recorded yet{provFilter ? ` for ${provFilter}` : ""}.
            </div>
          )}
        </div>

        {/* ── Error-rate honourable mention (sortable view) ── */}
        <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
          <span className="caps" style={{ color: "var(--ink-4)", marginRight: 4 }}>sort</span>
          {(["calls", "p95_ms", "error_rate", "name"] as SortKey[]).map((k) => (
            <button
              key={k}
              className="cm-btn tiny"
              onClick={() => setSortKey(k)}
              style={{ background: sortKey === k ? "var(--panel-2)" : undefined, fontWeight: sortKey === k ? 700 : 400 }}
            >
              {k === "p95_ms" ? "p95" : k === "error_rate" ? "errors" : k}
            </button>
          ))}
          <span className="mono" style={{ fontSize: 10, color: "var(--ink-4)", marginLeft: 8 }}>
            click a tool row to drill into its recent calls
          </span>
        </div>
      </div>
    </div>
  );
}
