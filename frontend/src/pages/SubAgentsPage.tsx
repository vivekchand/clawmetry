// Sub-Agents — OpenClaw run-ledger view.
//
// `runtime` IS the OpenClaw queue lane (cli / cron / subagent), so the lane
// rollup doubles as a live queue/concurrency monitor. Three panels:
//   1. Queue lanes — saturation bar (ok / running / queued / failed) + the
//      OpenClaw default concurrency cap (subagent=8, main=4; cli/cron uncapped).
//   2. Recent runs — status pill, lane chip, label, duration.
//   3. Sub-agent fan-out tree — runs grouped by requesting session, nested.
//
// Mirrors v1 loadRunLedger() (clawmetry/static/js/app.js) on the live
// /api/run-ledger + /api/run-ledger/tree endpoints (routes/scheduler.py).
// Polls every 5s while the tab is visible; never crashes on empty data.

import { useState, useEffect, useRef } from "react";

// OpenClaw default per-lane concurrency caps. cli/cron have no fixed cap in
// the queue, so we only show their running count.
const LANE_CAPS: Record<string, number> = { subagent: 8, main: 4 };

const LANE_COLORS: Record<string, string> = {
  subagent: "var(--plum)",
  cron: "var(--ocean, #3b82f6)",
  cli: "var(--moss)",
};

interface Lane {
  lane: string;
  total: number;
  running: number;
  queued: number;
  succeeded: number;
  failed: number;
  last_event_at?: number | null;
}

interface Run {
  task_id?: string;
  run_id?: string;
  runtime?: string;
  status?: string;
  label?: string;
  task?: string;
  delivery_status?: string;
  terminal_outcome?: string;
  created_at?: number | null;
  started_at?: number | null;
  ended_at?: number | null;
}

interface LedgerData {
  lanes: Lane[];
  runs: Run[];
}

interface TreeNode {
  task_id?: string;
  run_id?: string;
  label?: string;
  task?: string;
  status?: string;
  delivery_status?: string;
  terminal_outcome?: string;
  child_session_key?: string | null;
  agent_id?: string | null;
  created_at?: number | null;
  started_at?: number | null;
  ended_at?: number | null;
  error?: string | null;
  children?: TreeNode[];
}

interface TreeGroup {
  session_key: string;
  runs: TreeNode[];
}

interface TreeData {
  tree: TreeGroup[];
  count: number;
}

function laneColor(lane: string): string {
  return LANE_COLORS[lane] ?? "var(--ink-4)";
}

// status -> [text color, wash background]
function statusColors(status: string | undefined): [string, string] {
  switch ((status || "").toLowerCase()) {
    case "succeeded":
    case "success":
      return ["var(--moss)", "var(--moss-soft)"];
    case "running":
      return ["var(--ocean, #3b82f6)", "rgba(59,130,246,0.12)"];
    case "failed":
    case "timeout":
    case "error":
      return ["var(--claw-red)", "var(--claw-red-wash)"];
    case "queued":
    case "pending":
      return ["var(--amber)", "var(--amber-soft)"];
    default:
      return ["var(--ink-4)", "var(--panel-2)"];
  }
}

// epoch-ms start/end -> human duration. Empty string when we can't compute it.
function duration(started?: number | null, ended?: number | null): string {
  if (!started || !ended) return "";
  const ms = ended - started;
  if (ms < 0) return "";
  if (ms < 1000) return `${ms}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
  return `${Math.round(ms / 60000)}m`;
}

function StatusPill({ status }: { status: string | undefined }) {
  const [fg, bg] = statusColors(status);
  return (
    <span
      style={{
        fontSize: 10,
        fontWeight: 700,
        fontFamily: "var(--f-mono)",
        color: fg,
        background: bg,
        borderRadius: 4,
        padding: "1px 6px",
        whiteSpace: "nowrap",
      }}
    >
      {status || "?"}
    </span>
  );
}

function LaneRow({ lane }: { lane: Lane }) {
  const cap = LANE_CAPS[lane.lane];
  const total = lane.total || 0;
  const running = lane.running || 0;
  const ok = lane.succeeded || 0;
  const failed = lane.failed || 0;
  const queued = lane.queued || 0;
  const capLabel = cap ? `${running}/${cap}` : `${running}`;

  // Saturation segments — proportions of the lane's total runs.
  const segs: Array<[number, string]> = [
    [ok, "var(--moss)"],
    [running, "var(--ocean, #3b82f6)"],
    [queued, "var(--amber)"],
    [failed, "var(--claw-red)"],
  ];

  return (
    <div style={{ marginBottom: 14 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 13, marginBottom: 5 }}>
        <span style={{ width: 9, height: 9, borderRadius: 2, background: laneColor(lane.lane), display: "inline-block" }} />
        <span style={{ fontWeight: 700, color: "var(--ink)" }}>{lane.lane}</span>
        <span style={{ fontSize: 11, fontWeight: 600, color: running > 0 ? "var(--moss)" : "var(--ink-4)" }}>
          {running > 0 ? `● ${capLabel} running` : "idle"}
        </span>
        <span style={{ flex: 1 }} />
        <span className="mono" style={{ fontSize: 11, color: "var(--ink-4)" }}>
          {total} runs · {ok}✓{failed ? ` · ${failed}✗` : ""}
        </span>
      </div>
      <div style={{ display: "flex", height: 7, borderRadius: 4, overflow: "hidden", background: "var(--panel-2)" }}>
        {total > 0 &&
          segs.map(([n, c], i) =>
            n > 0 ? (
              <span key={i} style={{ height: "100%", width: `${(n / total) * 100}%`, background: c, display: "inline-block" }} />
            ) : null
          )}
      </div>
    </div>
  );
}

function RunRow({ run }: { run: Run }) {
  const d = duration(run.started_at, run.ended_at);
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 10,
        padding: "7px 14px",
        borderTop: "1px dashed var(--line)",
        fontSize: 12,
      }}
    >
      <StatusPill status={run.status} />
      <span
        className="mono"
        style={{
          fontSize: 10,
          color: "var(--ink-4)",
          background: "var(--panel-2)",
          borderRadius: 4,
          padding: "1px 6px",
          minWidth: 54,
          textAlign: "center",
        }}
      >
        {run.runtime || "—"}
      </span>
      <span
        style={{ flex: 1, color: "var(--ink-2)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", minWidth: 0 }}
        title={run.label || run.task || ""}
      >
        {run.label || run.task || "(untitled)"}
      </span>
      {d && <span className="mono" style={{ fontSize: 11, color: "var(--ink-4)", whiteSpace: "nowrap" }}>{d}</span>}
    </div>
  );
}

function TreeNodeRow({ node, depth }: { node: TreeNode; depth: number }) {
  const d = duration(node.started_at, node.ended_at);
  const children = node.children ?? [];
  return (
    <>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 8,
          padding: "6px 0",
          paddingLeft: 12 + depth * 18,
          fontSize: 12,
          borderTop: depth === 0 ? "1px dashed var(--line)" : "none",
        }}
      >
        <span style={{ color: "var(--ink-4)", fontFamily: "var(--f-mono)", fontSize: 11 }}>
          {depth > 0 ? "└─" : "•"}
        </span>
        <StatusPill status={node.status} />
        <span
          style={{ flex: 1, color: "var(--ink-2)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", minWidth: 0 }}
          title={node.label || node.task || ""}
        >
          {node.label || node.task || "(untitled)"}
        </span>
        {node.child_session_key && (
          <span className="mono" style={{ fontSize: 10, color: "var(--ink-4)" }} title={node.child_session_key}>
            {node.child_session_key.slice(0, 8)}
          </span>
        )}
        {d && <span className="mono" style={{ fontSize: 11, color: "var(--ink-4)", whiteSpace: "nowrap" }}>{d}</span>}
      </div>
      {children.map((kid, i) => (
        <TreeNodeRow key={kid.task_id ?? kid.run_id ?? i} node={kid} depth={depth + 1} />
      ))}
    </>
  );
}

export function SubAgentsPage() {
  const [ledger, setLedger] = useState<LedgerData | null>(null);
  const [tree, setTree] = useState<TreeData | null>(null);
  const [errored, setErrored] = useState(false);
  const timer = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      // Don't poll while the tab is hidden (matches v1 visibilitySetInterval).
      if (typeof document !== "undefined" && document.hidden) return;
      try {
        const [l, t] = await Promise.all([
          fetch("/api/run-ledger?limit=60").then((r) => r.json()),
          fetch("/api/run-ledger/tree").then((r) => r.json()),
        ]);
        if (cancelled) return;
        setLedger({ lanes: l?.lanes ?? [], runs: l?.runs ?? [] });
        setTree({ tree: t?.tree ?? [], count: t?.count ?? 0 });
        setErrored(false);
      } catch (e) {
        console.error(e);
        if (!cancelled) setErrored(true);
      }
    }

    load();
    timer.current = setInterval(load, 5000);
    return () => {
      cancelled = true;
      if (timer.current) clearInterval(timer.current);
    };
  }, []);

  if (!ledger) {
    return (
      <div style={{ padding: 40, color: "var(--ink-4)" }} className="mono">
        {errored ? "Failed to load run ledger." : "Loading sub-agents…"}
      </div>
    );
  }

  const lanes = ledger.lanes ?? [];
  const runs = ledger.runs ?? [];
  const groups = tree?.tree ?? [];
  const treeCount = tree?.count ?? 0;
  const empty = lanes.length === 0 && runs.length === 0;

  if (empty) {
    return (
      <div style={{ padding: "80px 40px", textAlign: "center" }}>
        <div style={{ fontSize: 32, marginBottom: 12 }}>⇲</div>
        <div style={{ fontSize: 15, color: "var(--ink-3)" }}>No background runs yet.</div>
        <div className="mono" style={{ fontSize: 11, color: "var(--ink-4)", marginTop: 8, lineHeight: 1.6 }}>
          Sub-agent, cron and CLI runs from OpenClaw's task ledger appear here as they execute.
        </div>
      </div>
    );
  }

  return (
    <div style={{ flex: 1, display: "flex", flexDirection: "column", minWidth: 0 }}>
      <div style={{ flex: 1, padding: 22, overflow: "auto", display: "flex", flexDirection: "column", gap: 16 }}>

        {/* ── Queue lanes ── */}
        <div className="cm-card" style={{ padding: 16 }}>
          <div className="caps" style={{ color: "var(--ink-4)", marginBottom: 12 }}>
            Queue lanes · runtime = OpenClaw queue lane
          </div>
          {lanes.length > 0 ? (
            lanes.map((l) => <LaneRow key={l.lane} lane={l} />)
          ) : (
            <div className="mono" style={{ fontSize: 11, color: "var(--ink-4)" }}>No lanes active.</div>
          )}
        </div>

        {/* ── Recent runs + fan-out tree (two columns) ── */}
        <div style={{ display: "grid", gridTemplateColumns: "1.3fr 1fr", gap: 16, minHeight: 0 }}>

          {/* Recent runs */}
          <div className="cm-card" style={{ padding: 0, overflow: "hidden", alignSelf: "start" }}>
            <div
              className="caps"
              style={{ color: "var(--ink-4)", padding: "12px 14px", borderBottom: "1px solid var(--line)" }}
            >
              Recent runs · {runs.length}
            </div>
            {runs.length > 0 ? (
              runs.slice(0, 40).map((r, i) => <RunRow key={r.task_id ?? r.run_id ?? i} run={r} />)
            ) : (
              <div className="mono" style={{ fontSize: 11, color: "var(--ink-4)", padding: 14 }}>No runs recorded.</div>
            )}
          </div>

          {/* Sub-agent fan-out tree */}
          <div className="cm-card" style={{ padding: 16, background: "var(--panel-2)", alignSelf: "start" }}>
            <div className="caps" style={{ color: "var(--ink-4)", marginBottom: 10 }}>
              Sub-agent fan-out · {treeCount} spawned
            </div>
            {groups.length > 0 ? (
              <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
                {groups.map((g, gi) => (
                  <div key={g.session_key ?? gi}>
                    <div className="mono" style={{ fontSize: 10, color: "var(--ink-4)", marginBottom: 2 }}>
                      session {(g.session_key || "unknown").slice(0, 12)} · {g.runs?.length ?? 0}
                    </div>
                    {(g.runs ?? []).map((n, ni) => (
                      <TreeNodeRow key={n.task_id ?? n.run_id ?? ni} node={n} depth={0} />
                    ))}
                  </div>
                ))}
              </div>
            ) : (
              <div className="mono" style={{ fontSize: 11, color: "var(--ink-4)" }}>
                No sub-agents spawned yet.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
