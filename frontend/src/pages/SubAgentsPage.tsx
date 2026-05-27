import { useState, useEffect } from "react";

interface SubAgentRun {
  x: number;
  w: number;
  label: string;
  failed?: boolean;
  active?: boolean;
}

interface Lane {
  name: string;
  color: string;
  runs: SubAgentRun[];
}

interface FailedRun {
  agent: string;
  label: string;
  time: string;
  exit_code: number;
  log: string[];
}

interface LeaderboardEntry {
  name: string;
  runs: number;
}

interface Summary {
  total_runs: number;
  failed: number;
  agent_count: number;
  tokens_spawned: string;
}

interface SubAgentsData {
  summary: Summary;
  lanes: Lane[];
  failed_run: FailedRun | null;
  leaderboard: LeaderboardEntry[];
}

const DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

function toVar(token: string): string {
  return `var(--${token})`;
}

export function SubAgentsPage() {
  const [data, setData] = useState<SubAgentsData | null>(null);

  useEffect(() => {
    fetch("/api/v2/subagents")
      .then((r) => r.json())
      .then(setData)
      .catch(console.error);
  }, []);

  if (!data) {
    return (
      <div style={{ padding: 40, color: "var(--ink-4)" }} className="mono">
        Loading sub-agents…
      </div>
    );
  }

  const { lanes, failed_run, leaderboard } = data;

  if (lanes.length === 0) {
    return (
      <div style={{ padding: "80px 40px", textAlign: "center" }}>
        <div style={{ fontSize: 32, marginBottom: 12 }}>⇲</div>
        <div style={{ fontSize: 15, color: "var(--ink-3)" }}>
          No sub-agents in this workspace yet.
        </div>
      </div>
    );
  }

  const maxRuns = leaderboard.length > 0 ? leaderboard[0].runs : 1;

  return (
    <div style={{ flex: 1, display: "flex", flexDirection: "column", minWidth: 0 }}>
      <div style={{ flex: 1, display: "grid", gridTemplateColumns: "1fr 320px", minHeight: 0 }}>

        {/* ── Swimlanes (left) ── */}
        <div style={{ padding: 22, overflow: "auto" }}>

          {/* Day axis */}
          <div
            style={{
              display: "flex",
              paddingLeft: 150,
              marginBottom: 8,
              fontFamily: "var(--f-mono)",
              fontSize: 10,
              color: "var(--ink-4)",
            }}
          >
            {DAYS.map((d) => (
              <div key={d} style={{ flex: 1 }}>{d}</div>
            ))}
          </div>

          {/* Lane rows */}
          <div style={{ background: "var(--paper-deep)", borderRadius: 10, padding: 10 }}>
            {lanes.map((lane, i) => {
              const color = toVar(lane.color);
              return (
                <div
                  key={i}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    padding: "8px 0",
                    borderBottom: i < lanes.length - 1 ? "1px dashed var(--line)" : "none",
                  }}
                >
                  {/* Agent name */}
                  <div style={{ width: 140, paddingRight: 10, display: "flex", alignItems: "center", gap: 6 }}>
                    <span style={{ width: 6, height: 26, background: color, borderRadius: 3 }} />
                    <span
                      className="mono"
                      style={{ fontSize: 11, color: "var(--ink-2)", flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}
                    >
                      {lane.name}
                    </span>
                  </div>

                  {/* Timeline bar */}
                  <div
                    style={{
                      flex: 1,
                      position: "relative",
                      height: 28,
                      background: "var(--paper)",
                      borderRadius: 4,
                      border: "1px solid var(--line)",
                    }}
                  >
                    {/* Day separator lines */}
                    {[1, 2, 3, 4, 5, 6].map((d) => (
                      <div
                        key={d}
                        style={{
                          position: "absolute",
                          left: `${(d / 7) * 100}%`,
                          top: 0,
                          bottom: 0,
                          width: 1,
                          background: "var(--line)",
                        }}
                      />
                    ))}

                    {/* Run blocks */}
                    {lane.runs.map((r, j) => (
                      <div
                        key={j}
                        title={r.label}
                        style={{
                          position: "absolute",
                          left: `${r.x}%`,
                          top: 4,
                          bottom: 4,
                          width: `${r.w}%`,
                          background: r.failed ? "var(--claw-red)" : color,
                          opacity: r.failed ? 1 : 0.85,
                          borderRadius: 3,
                          padding: "0 6px",
                          display: "flex",
                          alignItems: "center",
                          color: "#FFF8EE",
                          fontFamily: "var(--f-mono)",
                          fontSize: 9,
                          whiteSpace: "nowrap",
                          overflow: "hidden",
                          border: r.active ? "1.5px solid var(--ink)" : "none",
                          cursor: "pointer",
                        }}
                      >
                        {r.label}
                        {r.failed && " \u2715"}
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>

          {/* ── Aggregate strip ── */}
          <div className="cm-card" style={{ marginTop: 14, padding: 14 }}>
            <div className="caps" style={{ color: "var(--ink-4)", marginBottom: 8 }}>
              Runs / hour · all subs
            </div>
            <svg viewBox="0 0 700 50" style={{ width: "100%", height: 50 }}>
              {Array.from({ length: 168 }).map((_, i) => {
                const h = 6 + ((i * 13 + (i % 7) * 4) % 32);
                const c = i === 38 ? "var(--claw-red)" : "var(--claw-red-soft)";
                return (
                  <rect key={i} x={i * 4} y={48 - h} width="3" height={h} fill={c} />
                );
              })}
            </svg>
          </div>
        </div>

        {/* ── Right sidebar ── */}
        <div
          style={{
            borderLeft: "1px solid var(--line)",
            padding: 18,
            background: "var(--paper-deep)",
            display: "flex",
            flexDirection: "column",
            gap: 12,
            overflow: "auto",
          }}
        >
          {/* Failed run card */}
          {failed_run && (
            <div className="cm-card" style={{ padding: 14, borderColor: "var(--claw-red)" }}>
              <div className="caps" style={{ color: "var(--claw-red)", marginBottom: 6 }}>
                Failed run
              </div>
              <div style={{ fontSize: 13, fontWeight: 500 }}>
                {failed_run.agent} · {failed_run.label}
              </div>
              <div
                className="mono"
                style={{ fontSize: 10, color: "var(--ink-4)", marginTop: 2 }}
              >
                {failed_run.time} · exit code {failed_run.exit_code}
              </div>
              <div style={{ borderTop: "1px dashed var(--line)", margin: "10px 0" }} />
              <div
                className="mono"
                style={{
                  fontSize: 11,
                  color: "var(--ink-2)",
                  background: "var(--panel-2)",
                  padding: 10,
                  borderRadius: 6,
                  lineHeight: 1.6,
                }}
              >
                {failed_run.log.map((line, k) => {
                  const isError = line.startsWith("!");
                  const isDim =
                    line.startsWith("exceeded") || line.startsWith("slack");
                  return (
                    <div
                      key={k}
                      style={{
                        color: isError
                          ? "var(--claw-red)"
                          : isDim
                            ? "var(--ink-4)"
                            : undefined,
                      }}
                    >
                      {line}
                    </div>
                  );
                })}
              </div>
              <button className="cm-btn tiny" style={{ marginTop: 10 }}>
                open trace →
              </button>
            </div>
          )}

          {/* Leaderboard */}
          <div className="cm-card" style={{ padding: 14 }}>
            <div className="caps" style={{ color: "var(--ink-4)", marginBottom: 8 }}>
              Sub agent leaderboard · 7d
            </div>
            {leaderboard.map((s) => (
              <div
                key={s.name}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 8,
                  padding: "3px 0",
                  fontSize: 11,
                }}
              >
                <span
                  className="mono"
                  style={{ width: 120, color: "var(--ink-2)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}
                >
                  {s.name}
                </span>
                <div
                  style={{
                    flex: 1,
                    height: 6,
                    background: "var(--panel-2)",
                    borderRadius: 3,
                    overflow: "hidden",
                  }}
                >
                  <div
                    style={{
                      width: `${(s.runs / maxRuns) * 100}%`,
                      height: "100%",
                      background: "var(--claw-red)",
                    }}
                  />
                </div>
                <span
                  className="mono"
                  style={{ width: 26, textAlign: "right", color: "var(--ink-4)" }}
                >
                  {s.runs}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
