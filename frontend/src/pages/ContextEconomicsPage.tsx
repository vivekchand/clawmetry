// Context economics — the cost of the context window itself.
//
// Three panels:
//   1. Summary chips (compactions, overflow vs proactive, tokens reclaimed,
//      peak window %).
//   2. Utilization gauge-over-time — an SVG line of context-window % per
//      assistant turn, with compaction markers dropped on the timeline.
//   3. Compaction log — expandable rows; click for before/after token counts,
//      reclaimed, trigger and the summary text.
//   Plus a session picker (chips) that scopes the gauge to one conversation,
//   and an overflow-thrash callout for sessions hammering the wall.
//
// Live API (routes/context_economics.py):
//   GET /api/context-economics?session_id=…
//     → {utilization, compactions, overflow_sessions, session_chips, summary}
// Polls every 6s while visible; never crashes on empty data.

import { useState, useEffect, useRef } from "react";

interface UtilPoint {
  session_id?: string;
  ts: string;
  tokens: number;
  window: number;
  model?: string;
  pct: number;
}

interface Compaction {
  session_id?: string;
  ts: string;
  trigger: string;
  tokens_before: number;
  tokens_after: number;
  reclaimed: number;
  from_hook?: boolean;
  summary?: string;
}

interface OverflowSession {
  session_id: string;
  compaction_count: number;
  overflow_count: number;
}

interface SessionChip {
  session_id: string;
  peak_pct: number;
  ts: string;
}

interface EconSummary {
  compaction_count: number;
  overflow_count: number;
  proactive_count: number;
  total_reclaimed: number;
  peak_pct: number;
  overflow_sessions: number;
  utilization_points: number;
}

interface EconData {
  utilization: UtilPoint[];
  compactions: Compaction[];
  overflow_sessions: OverflowSession[];
  session_chips: SessionChip[];
  summary: EconSummary;
}

function pctColor(pct: number): string {
  if (pct >= 90) return "var(--claw-red)";
  if (pct >= 70) return "var(--amber)";
  return "var(--moss)";
}

function fmtTime(ts?: string): string {
  if (!ts) return "—";
  const ms = Date.parse(ts);
  if (Number.isNaN(ms)) return ts.slice(0, 19);
  return new Date(ms).toLocaleString(undefined, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
}

// Map a utilization series + compaction markers into an SVG path. Compactions
// are rendered as vertical drop-lines at the nearest utilization-point index.
function UtilGauge({ util, compactions }: { util: UtilPoint[]; compactions: Compaction[] }) {
  if (util.length === 0) {
    return <div className="mono" style={{ fontSize: 11, color: "var(--ink-4)", padding: "24px 0" }}>No utilization points yet.</div>;
  }
  const W = 800;
  const H = 120;
  const padL = 28;
  const padR = 12;
  const padB = 18;
  const padT = 10;
  const n = util.length;
  const xScale = (i: number) => padL + (n <= 1 ? 0 : (i / (n - 1)) * (W - padL - padR));
  const yScale = (pct: number) => padT + (1 - Math.min(100, pct) / 100) * (H - padT - padB);
  const pathD = util.map((u, i) => `${i === 0 ? "M" : "L"}${xScale(i).toFixed(1)} ${yScale(u.pct).toFixed(1)}`).join(" ");

  // Index compaction timestamps to the closest util point (by ts string sort).
  const compIdx: number[] = [];
  for (const c of compactions) {
    let best = -1;
    for (let i = 0; i < n; i++) {
      if ((util[i].ts || "") <= (c.ts || "")) best = i;
    }
    if (best >= 0) compIdx.push(best);
  }

  return (
    <svg viewBox={`0 0 ${W} ${H}`} style={{ width: "100%", height: 140 }}>
      {/* threshold guides */}
      {[70, 90].map((t) => (
        <g key={t}>
          <line x1={padL} y1={yScale(t)} x2={W - padR} y2={yScale(t)} stroke={t >= 90 ? "var(--claw-red)" : "var(--amber)"} strokeWidth="0.5" strokeDasharray="3 3" opacity="0.5" />
          <text x={2} y={yScale(t) + 3} fontFamily="var(--f-mono)" fontSize="8" fill={t >= 90 ? "var(--claw-red)" : "var(--amber)"}>{t}%</text>
        </g>
      ))}
      <line x1={padL} y1={yScale(0)} x2={W - padR} y2={yScale(0)} stroke="var(--line-strong)" strokeWidth="0.5" />
      {/* compaction drops */}
      {compIdx.map((idx, k) => (
        <line key={k} x1={xScale(idx)} y1={padT} x2={xScale(idx)} y2={H - padB} stroke="var(--claw-red)" strokeWidth="0.7" opacity="0.4" />
      ))}
      {/* utilization line */}
      <path d={pathD} fill="none" stroke="var(--plum)" strokeWidth="1.6" />
      {/* points */}
      {util.map((u, i) => (
        <circle key={i} cx={xScale(i)} cy={yScale(u.pct)} r="2" fill={pctColor(u.pct)}>
          <title>{`${u.pct}% · ${u.tokens.toLocaleString()}/${u.window.toLocaleString()} tok · ${fmtTime(u.ts)}`}</title>
        </circle>
      ))}
    </svg>
  );
}

function CompactionRow({ c }: { c: Compaction }) {
  const [open, setOpen] = useState(false);
  const overflow = c.trigger === "overflow";
  const tcolor = overflow ? "var(--claw-red)" : "var(--moss)";
  return (
    <div style={{ borderTop: "1px dashed var(--line)" }}>
      <div
        onClick={() => setOpen(!open)}
        style={{ display: "flex", alignItems: "center", gap: 10, padding: "8px 14px", cursor: "pointer", fontSize: 12 }}
      >
        <span className="mono" style={{ fontSize: 10, color: tcolor, border: `1px solid ${tcolor}`, borderRadius: 4, padding: "1px 7px", fontWeight: 700, minWidth: 70, textAlign: "center" }}>
          {c.trigger}
        </span>
        <span className="mono" style={{ flex: 1, color: "var(--ink-3)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", minWidth: 0 }}>
          {(c.session_id || "").slice(0, 18)}
        </span>
        <span className="mono" style={{ fontSize: 11, color: "var(--ink-2)" }}>
          {c.tokens_before.toLocaleString()} → {c.tokens_after.toLocaleString()}
        </span>
        <span className="mono" style={{ fontSize: 10, color: "var(--moss)", minWidth: 70, textAlign: "right" }}>
          −{c.reclaimed.toLocaleString()}
        </span>
      </div>
      {open && (
        <div style={{ padding: "4px 14px 12px 24px" }}>
          {/* before/after bar */}
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
            <span className="mono" style={{ fontSize: 9, color: "var(--ink-4)", width: 46, textAlign: "right" }}>before</span>
            <div style={{ flex: 1, height: 10, background: "var(--panel-2)", borderRadius: 3, overflow: "hidden" }}>
              <div style={{ width: "100%", height: "100%", background: "var(--claw-red)", opacity: 0.6 }} />
            </div>
            <span className="mono" style={{ fontSize: 9, color: "var(--ink-3)", width: 70 }}>{c.tokens_before.toLocaleString()}</span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
            <span className="mono" style={{ fontSize: 9, color: "var(--ink-4)", width: 46, textAlign: "right" }}>after</span>
            <div style={{ flex: 1, height: 10, background: "var(--panel-2)", borderRadius: 3, overflow: "hidden" }}>
              <div style={{ width: `${c.tokens_before ? Math.min(100, (c.tokens_after / c.tokens_before) * 100) : 0}%`, height: "100%", background: "var(--moss)" }} />
            </div>
            <span className="mono" style={{ fontSize: 9, color: "var(--ink-3)", width: 70 }}>{c.tokens_after.toLocaleString()}</span>
          </div>
          <div className="mono" style={{ fontSize: 10, color: "var(--ink-4)", lineHeight: 1.7 }}>
            <div><span style={{ color: "var(--ink-4)" }}>when</span> {fmtTime(c.ts)} · {c.from_hook ? "auto-hook" : "manual"}</div>
            {c.summary && <div style={{ marginTop: 4, color: "var(--ink-3)", whiteSpace: "pre-wrap" }}>{c.summary.slice(0, 400)}</div>}
          </div>
        </div>
      )}
    </div>
  );
}

export function ContextEconomicsPage() {
  const [data, setData] = useState<EconData | null>(null);
  const [picked, setPicked] = useState<string>("");
  const [errored, setErrored] = useState(false);
  const timer = useRef<ReturnType<typeof setInterval> | null>(null);
  const pickedRef = useRef(picked);
  pickedRef.current = picked;

  useEffect(() => {
    let cancelled = false;
    async function load() {
      if (typeof document !== "undefined" && document.hidden) return;
      try {
        const qs = pickedRef.current ? `?session_id=${encodeURIComponent(pickedRef.current)}` : "";
        const d = await fetch(`/api/context-economics${qs}`).then((r) => r.json());
        if (cancelled) return;
        setData(d);
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
  }, [picked]);

  if (!data) {
    return (
      <div style={{ padding: 40, color: "var(--ink-4)" }} className="mono">
        {errored ? "Failed to load context economics." : "Loading context economics…"}
      </div>
    );
  }

  const s = data.summary;
  const chips = data.session_chips ?? [];
  const compactions = data.compactions ?? [];
  const overflow = data.overflow_sessions ?? [];

  return (
    <div style={{ flex: 1, display: "flex", flexDirection: "column", minWidth: 0 }}>
      <div style={{ flex: 1, padding: 22, overflow: "auto", display: "flex", flexDirection: "column", gap: 16 }}>

        {/* ── Summary chips ── */}
        <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
          {[
            ["compactions", s?.compaction_count ?? 0, "var(--ink-2)"],
            ["overflow", s?.overflow_count ?? 0, "var(--claw-red)"],
            ["proactive", s?.proactive_count ?? 0, "var(--moss)"],
            ["tokens reclaimed", (s?.total_reclaimed ?? 0).toLocaleString(), "var(--moss)"],
            ["peak window", `${s?.peak_pct ?? 0}%`, pctColor(s?.peak_pct ?? 0)],
          ].map(([label, val, color]) => (
            <div key={String(label)} className="cm-card" style={{ padding: "10px 16px", minWidth: 120 }}>
              <div className="caps" style={{ color: "var(--ink-4)" }}>{label}</div>
              <div className="display" style={{ fontSize: 24, color: color as string, marginTop: 2 }}>{val}</div>
            </div>
          ))}
        </div>

        {/* ── Session picker chips ── */}
        {chips.length > 0 && (
          <div style={{ display: "flex", gap: 6, flexWrap: "wrap", alignItems: "center" }}>
            <span className="caps" style={{ color: "var(--ink-4)", marginRight: 4 }}>scope</span>
            <button
              className="cm-btn tiny"
              onClick={() => setPicked("")}
              style={{ background: picked === "" ? "var(--panel-2)" : undefined, fontWeight: picked === "" ? 700 : 400 }}
            >
              all sessions
            </button>
            {chips.slice(0, 12).map((c) => (
              <button
                key={c.session_id}
                className="cm-btn tiny"
                onClick={() => setPicked(c.session_id)}
                style={{ background: picked === c.session_id ? "var(--panel-2)" : undefined, fontWeight: picked === c.session_id ? 700 : 400 }}
                title={c.session_id}
              >
                {c.session_id.slice(0, 8)} · <span style={{ color: pctColor(c.peak_pct) }}>{Math.round(c.peak_pct)}%</span>
              </button>
            ))}
          </div>
        )}

        {/* ── Utilization gauge-over-time ── */}
        <div className="cm-card" style={{ padding: 16 }}>
          <div className="caps" style={{ color: "var(--ink-4)", marginBottom: 8 }}>
            Context-window utilization · {data.utilization.length} turns{picked ? ` · ${picked.slice(0, 12)}` : " · all sessions"}
          </div>
          <UtilGauge util={data.utilization} compactions={compactions} />
        </div>

        {/* ── Overflow thrash callout ── */}
        {overflow.length > 0 && (
          <div className="cm-card" style={{ padding: 14, borderColor: "var(--claw-red)" }}>
            <div className="caps" style={{ color: "var(--claw-red)", marginBottom: 8 }}>
              Overflow thrash · {overflow.length} session{overflow.length === 1 ? "" : "s"} hitting the wall repeatedly
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
              {overflow.map((o) => (
                <div
                  key={o.session_id}
                  onClick={() => setPicked(o.session_id)}
                  style={{ display: "flex", alignItems: "center", gap: 10, fontSize: 12, padding: "4px 0", cursor: "pointer", borderTop: "1px dashed var(--line)" }}
                >
                  <span className="mono" style={{ flex: 1, color: "var(--ink-2)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", minWidth: 0 }}>{o.session_id.slice(0, 24)}</span>
                  <span className="mono" style={{ fontSize: 10, color: "var(--claw-red)" }}>{o.overflow_count} overflow</span>
                  <span className="mono" style={{ fontSize: 10, color: "var(--ink-4)" }}>{o.compaction_count} compactions</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── Compaction log ── */}
        <div className="cm-card" style={{ padding: 0, overflow: "hidden" }}>
          <div className="caps" style={{ color: "var(--ink-4)", padding: "12px 14px", borderBottom: "1px solid var(--line)" }}>
            Compaction log · {compactions.length} · click a row for before/after
          </div>
          {compactions.length > 0 ? (
            compactions.map((c, i) => <CompactionRow key={`${c.session_id}-${c.ts}-${i}`} c={c} />)
          ) : (
            <div className="mono" style={{ fontSize: 11, color: "var(--ink-4)", padding: 14 }}>
              No compactions recorded{picked ? " for this session" : ""} — context staying under the limit.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
