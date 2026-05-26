import { useState, useEffect } from "react";

interface Integration {
  name: string;
  tokens_7d: number;
  cost_usd_7d: number;
}

interface DailyPoint {
  date: string;
  tokens: number;
  cost_usd: number;
}

interface Spike {
  date: string;
  delta_pct: number;
  note: string;
}

interface LeaderboardEntry {
  node_id: string;
  label: string;
  cost_usd_7d: number;
}

interface CostData {
  by_integration: Integration[];
  daily: DailyPoint[];
  spikes: Spike[];
  leaderboard: LeaderboardEntry[];
}

function fmtTok(n: number): string {
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + "M";
  if (n >= 1_000) return Math.round(n / 1_000) + "K";
  return String(n);
}

function fmtUsd(n: number): string {
  return "$" + n.toFixed(2);
}

export function CostPage() {
  const [data, setData] = useState<CostData | null>(null);

  useEffect(() => {
    fetch("/api/v2/cost")
      .then((r) => r.json())
      .then(setData)
      .catch(console.error);
  }, []);

  if (!data) {
    return (
      <div style={{ padding: 40, color: "var(--ink-4)" }} className="mono">
        Loading cost data…
      </div>
    );
  }

  const totalTok = data.by_integration.reduce((s, i) => s + i.tokens_7d, 0);
  const totalUsd = data.by_integration.reduce((s, i) => s + i.cost_usd_7d, 0);
  const spikeMap = new Map(data.spikes.map((s) => [s.date, s]));

  return (
    <div style={{ flex: 1, display: "flex", flexDirection: "column", minHeight: 0, overflow: "auto" }}>

      {/* ── Integration bar breakdown — top strip ── */}
      <div style={{ padding: "20px 22px", borderBottom: "1px dashed var(--line)" }}>
        <div className="caps" style={{ color: "var(--ink-4)", marginBottom: 12 }}>
          Cost &amp; Tokens · last 7 days · {fmtTok(totalTok)} tok · {fmtUsd(totalUsd)}
        </div>
        {/* CSS-width bars (Stage A). Recharts stacked bars land in Stage B. */}
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {data.by_integration.map((intg) => {
            const pct = totalTok > 0 ? (intg.tokens_7d / totalTok) * 100 : 0;
            return (
              <div key={intg.name} style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <span style={{ width: 120, fontSize: 12, color: "var(--ink-2)", flexShrink: 0 }}>
                  {intg.name}
                </span>
                <div style={{ flex: 1, height: 10, background: "var(--panel-2)", borderRadius: 5 }}>
                  <div
                    style={{
                      width: `${pct.toFixed(1)}%`,
                      height: "100%",
                      background: "var(--claw-red)",
                      borderRadius: 5,
                      transition: "width 0.4s ease",
                    }}
                  />
                </div>
                <span className="mono" style={{ width: 52, fontSize: 11, color: "var(--ink-3)", textAlign: "right" }}>
                  {fmtTok(intg.tokens_7d)}
                </span>
                <span className="mono" style={{ width: 44, fontSize: 11, color: "var(--ink-4)", textAlign: "right" }}>
                  {fmtUsd(intg.cost_usd_7d)}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* ── Two-column body: daily table | leaderboard + spike log ── */}
      <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", flex: 1, minHeight: 0 }}>

        {/* Left: daily cost table */}
        <div style={{ padding: 22, overflow: "auto" }}>
          <div className="caps" style={{ color: "var(--ink-4)", marginBottom: 12 }}>
            Daily breakdown · 7 days
          </div>
          <div className="cm-card" style={{ padding: 0, overflow: "hidden" }}>
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "1.2fr 1fr 1fr",
                padding: "8px 14px",
                background: "var(--panel-2)",
                fontFamily: "var(--f-mono)",
                fontSize: 9,
                color: "var(--ink-4)",
                textTransform: "uppercase",
                letterSpacing: "0.06em",
              }}
            >
              <span>date</span>
              <span>tokens</span>
              <span>cost</span>
            </div>
            {data.daily.map((d) => {
              const spike = spikeMap.get(d.date);
              return (
                <div
                  key={d.date}
                  title={spike ? `+${spike.delta_pct}% anomaly — ${spike.note}` : undefined}
                  style={{
                    display: "grid",
                    gridTemplateColumns: "1.2fr 1fr 1fr",
                    padding: "9px 14px",
                    borderTop: "1px dashed var(--line)",
                    fontSize: 12,
                    alignItems: "center",
                    background: spike ? "var(--panel-2)" : "transparent",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                    {spike && (
                      <span style={{ color: "var(--claw-red)", fontSize: 11 }}>▲</span>
                    )}
                    <span className="mono" style={{ fontSize: 11, color: "var(--ink-3)" }}>{d.date}</span>
                  </div>
                  <span className="mono" style={{ fontSize: 12, color: "var(--ink-2)" }}>{fmtTok(d.tokens)}</span>
                  <span className="mono" style={{ fontSize: 12, color: spike ? "var(--claw-red)" : "var(--ink-2)" }}>
                    {fmtUsd(d.cost_usd)}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right: fleet leaderboard + spike log */}
        <div
          style={{
            borderLeft: "1px solid var(--line)",
            padding: 22,
            background: "var(--paper-deep)",
            overflow: "auto",
            display: "flex",
            flexDirection: "column",
            gap: 16,
          }}
        >
          <div>
            <div className="caps" style={{ color: "var(--ink-4)", marginBottom: 10 }}>
              Fleet leaderboard · 7d cost
            </div>
            <div className="cm-card" style={{ padding: 0, overflow: "hidden" }}>
              {data.leaderboard.map((entry, i) => (
                <div
                  key={entry.node_id}
                  style={{
                    padding: "10px 14px",
                    borderTop: i > 0 ? "1px dashed var(--line)" : undefined,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    fontSize: 12,
                  }}
                >
                  <div>
                    <div style={{ fontWeight: 500, color: "var(--ink-2)" }}>{entry.label}</div>
                    <div className="mono" style={{ fontSize: 10, color: "var(--ink-4)", marginTop: 2 }}>
                      {entry.node_id}
                    </div>
                  </div>
                  <span className="mono" style={{ fontSize: 13, color: "var(--ink)" }}>
                    {fmtUsd(entry.cost_usd_7d)}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {data.spikes.length > 0 && (
            <div>
              <div className="caps" style={{ color: "var(--ink-4)", marginBottom: 8 }}>
                Spike log
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                {data.spikes.map((sp, i) => (
                  <div key={i} className="cm-card" style={{ padding: "10px 14px", borderColor: "var(--claw-red)" }}>
                    <div className="mono" style={{ fontSize: 11, color: "var(--claw-red)" }}>
                      {sp.date} · +{sp.delta_pct}%
                    </div>
                    <div style={{ fontSize: 12, color: "var(--ink-2)", marginTop: 3 }}>{sp.note}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
