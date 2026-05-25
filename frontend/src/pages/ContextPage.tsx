import { useState, useEffect } from "react";

interface Segment {
  name: string;
  tokens: number;
  color: string;
  note: string;
}

interface HistoryPoint {
  ts: string;
  used: number;
  event?: string;
}

interface MemoryFile {
  path: string;
  size_bytes: number;
  preview: string;
}

interface ContextData {
  tokens: { used: number; total: number; compaction_threshold: number };
  segments: Segment[];
  history: HistoryPoint[];
  memory_files: MemoryFile[];
}

function colorVar(c: string): string {
  return `var(--${c})`;
}

export function ContextPage() {
  const [data, setData] = useState<ContextData | null>(null);

  useEffect(() => {
    fetch("/api/v2/context")
      .then((r) => r.json())
      .then(setData)
      .catch(console.error);
  }, []);

  if (!data) {
    return (
      <div style={{ padding: 40, color: "var(--ink-4)" }} className="mono">
        Loading context…
      </div>
    );
  }

  const { tokens, segments, history, memory_files } = data;
  const used = tokens.used;
  const budget = tokens.total;
  const compactionAt = tokens.compaction_threshold;
  const pctUsed = Math.round((used / budget) * 100);
  const maxSegment = Math.max(...segments.map((s) => s.tokens));

  return (
    <div style={{ flex: 1, display: "flex", flexDirection: "column", minWidth: 0 }}>
      <div style={{ flex: 1, padding: 22, overflow: "auto", display: "flex", flexDirection: "column", gap: 16 }}>

        {/* ── Token gauge ── */}
        <div className="cm-card" style={{ padding: 22, background: "var(--paper)" }}>
          <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", marginBottom: 14 }}>
            <div>
              <div className="caps" style={{ color: "var(--ink-4)" }}>Context window · live</div>
              <div className="display" style={{ fontSize: 56, lineHeight: 1, marginTop: 4 }}>
                {used.toFixed(1)}<span style={{ color: "var(--ink-4)", fontSize: 32 }}>K</span>
                <span style={{ fontFamily: "var(--f-sans)", fontSize: 16, color: "var(--ink-4)", marginLeft: 10, fontWeight: 400 }}>
                  of {budget}K tokens
                </span>
              </div>
              <div className="mono" style={{ fontSize: 11, color: "var(--ink-3)", marginTop: 4 }}>
                {pctUsed}% used · compaction at {compactionAt}K · headroom {(budget - used).toFixed(1)}K
              </div>
            </div>
            <div style={{ textAlign: "right" }}>
              <div className="cm-tag" style={{ color: used < compactionAt ? "var(--moss)" : "var(--claw-red)", borderColor: used < compactionAt ? "var(--moss)" : "var(--claw-red)" }}>
                {used < compactionAt ? "healthy" : "near limit"}
              </div>
              <div className="mono" style={{ fontSize: 10, color: "var(--ink-4)", marginTop: 4 }}>last compaction · 12m ago</div>
            </div>
          </div>

          {/* stacked bar */}
          <div style={{ position: "relative", height: 56, background: "var(--panel-2)", borderRadius: 10, overflow: "hidden", border: "1px solid var(--line)" }}>
            {(() => {
              let offset = 0;
              return segments.map((s, i) => {
                const w = (s.tokens / budget) * 100;
                const left = offset;
                offset += w;
                return (
                  <div key={i} style={{
                    position: "absolute", left: `${left}%`, top: 0, bottom: 0, width: `${w}%`,
                    background: colorVar(s.color), opacity: 0.85,
                    borderRight: "1px solid rgba(255,255,255,0.5)",
                    display: "flex", alignItems: "center", justifyContent: "center",
                    color: "#FFF8EE", fontFamily: "var(--f-mono)", fontSize: 9,
                    overflow: "hidden", whiteSpace: "nowrap",
                  }}>
                    {w > 4 && `${s.tokens}K`}
                  </div>
                );
              });
            })()}
            {/* compaction marker */}
            <div style={{ position: "absolute", left: `${(compactionAt / budget) * 100}%`, top: -6, bottom: -6, width: 2, background: "var(--claw-red)" }}>
              <div style={{ position: "absolute", top: -18, left: -38, fontFamily: "var(--f-mono)", fontSize: 9, color: "var(--claw-red)", whiteSpace: "nowrap" }}>
                ↓ compact at {compactionAt}K
              </div>
            </div>
            {/* scale ticks */}
            {[0, 50, 100, 150, 200].map((t) => (
              <div key={t} style={{ position: "absolute", left: `${(t / budget) * 100}%`, bottom: -20, fontFamily: "var(--f-mono)", fontSize: 9, color: "var(--ink-4)", transform: "translateX(-50%)" }}>
                {t}K
              </div>
            ))}
          </div>

          {/* legend */}
          <div style={{ display: "flex", flexWrap: "wrap", gap: 10, marginTop: 32 }}>
            {segments.map((s) => (
              <div key={s.name} style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 11 }}>
                <span style={{ width: 10, height: 10, background: colorVar(s.color), borderRadius: 2 }} />
                <span style={{ color: "var(--ink-2)" }}>{s.name}</span>
                <span className="mono" style={{ color: "var(--ink-4)" }}>{s.tokens}K</span>
              </div>
            ))}
          </div>
        </div>

        {/* ── Breakdown + Memory preview (two columns) ── */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>

          {/* Breakdown table */}
          <div className="cm-card" style={{ padding: 16 }}>
            <div className="caps" style={{ color: "var(--ink-4)", marginBottom: 10 }}>Breakdown · this turn</div>
            {segments.map((s) => (
              <div key={s.name} style={{ display: "flex", alignItems: "center", gap: 10, padding: "8px 0", borderTop: "1px dashed var(--line)", fontSize: 12 }}>
                <span style={{ width: 6, height: 24, background: colorVar(s.color), borderRadius: 3 }} />
                <div style={{ flex: 1 }}>
                  <div style={{ color: "var(--ink-2)" }}>{s.name}</div>
                  <div className="mono" style={{ fontSize: 10, color: "var(--ink-4)" }}>{s.note}</div>
                </div>
                <div style={{ width: 80, height: 6, background: "var(--panel-2)", borderRadius: 3, overflow: "hidden" }}>
                  <div style={{ width: `${(s.tokens / maxSegment) * 100}%`, height: "100%", background: colorVar(s.color) }} />
                </div>
                <span className="mono" style={{ fontSize: 11, color: "var(--ink-3)", width: 50, textAlign: "right" }}>{s.tokens}K</span>
              </div>
            ))}
          </div>

          {/* Memory file preview */}
          <div className="cm-card" style={{ padding: 16, background: "var(--panel-2)" }}>
            <div className="caps" style={{ color: "var(--ink-4)", marginBottom: 10 }}>Peek · what the model reads right now</div>
            <pre style={{
              fontFamily: "var(--f-mono)", fontSize: 11, color: "var(--ink-2)", lineHeight: 1.6,
              padding: 12, background: "var(--paper)", borderRadius: 6,
              border: "1px dashed var(--line-strong)", height: 240, overflow: "auto",
              margin: 0, whiteSpace: "pre-wrap",
            }}>
              {memory_files.map((f) => `# ${f.path}\n${f.preview}\n\n`).join("")}
              {`// tool schemas\n{ name: "exec.run", args: {...} } ×12\n\n`}
              {`// conversation · last 84 turns\nuser: deploy to prod\nasst: ... <running checks>\n... (${segments.find((s) => s.name === "Conversation history")?.tokens ?? 0}K tokens)`}
            </pre>
            <div style={{ display: "flex", gap: 6, marginTop: 10 }}>
              <button className="cm-btn tiny">⤓ download .txt</button>
              <button className="cm-btn tiny">diff vs last turn</button>
            </div>
          </div>
        </div>

        {/* ── Compaction history SVG ── */}
        <div className="cm-card" style={{ padding: 16 }}>
          <div className="caps" style={{ color: "var(--ink-4)", marginBottom: 10 }}>Compaction history · last 6 hours</div>
          <svg viewBox="0 0 800 80" style={{ width: "100%", height: 80 }}>
            <line x1="20" y1="60" x2="780" y2="60" stroke="var(--line-strong)" strokeWidth="0.5" />
            <line x1="20" y1="14" x2="780" y2="14" stroke="var(--claw-red)" strokeWidth="0.6" strokeDasharray="3 3" opacity="0.5" />
            <text x="22" y="12" fontFamily="JetBrains Mono" fontSize="8" fill="var(--claw-red)">compaction · {compactionAt}K</text>
            {(() => {
              const pts = history;
              const xScale = (i: number) => 20 + (i / (pts.length - 1)) * 760;
              const yScale = (v: number) => 60 - ((v / budget) * 46);
              const pathD = pts.map((p, i) => `${i === 0 ? "M" : "L"}${xScale(i)} ${yScale(p.used)}`).join(" ");
              return (
                <>
                  <path d={pathD} fill="none" stroke="var(--claw-red)" strokeWidth="1.6" />
                  {pts.map((p, i) =>
                    p.event === "compaction" ? (
                      <g key={i}>
                        <line x1={xScale(i)} y1="14" x2={xScale(i)} y2="60" stroke="var(--claw-red)" strokeWidth="0.6" opacity="0.4" />
                        <circle cx={xScale(i)} cy={yScale(p.used)} r="3" fill="var(--claw-red)" />
                        <text x={xScale(i) + 4} y="74" fontFamily="JetBrains Mono" fontSize="8" fill="var(--ink-3)">snip</text>
                      </g>
                    ) : null
                  )}
                  {/* "now" marker on last point */}
                  <line x1={xScale(pts.length - 1)} y1="14" x2={xScale(pts.length - 1)} y2="60" stroke="var(--moss)" strokeWidth="0.6" />
                  <circle cx={xScale(pts.length - 1)} cy={yScale(pts[pts.length - 1].used)} r="3" fill="var(--moss)" />
                  <text x={xScale(pts.length - 1) - 20} y={yScale(pts[pts.length - 1].used) + 14} fontFamily="JetBrains Mono" fontSize="8" fill="var(--moss)" textAnchor="end">
                    now · {pts[pts.length - 1].used}K
                  </text>
                </>
              );
            })()}
          </svg>
        </div>
      </div>
    </div>
  );
}