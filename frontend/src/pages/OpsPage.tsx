import { useState, useEffect } from "react";

interface Service {
  name: string;
  status: "ok" | "warn" | "fail";
  uptime: string;
  bpm: number;
  latency: string;
}

interface CronJob {
  id: string;
  name: string;
  schedule: string;
  last_run: string;
  next_run: string;
  status: "ok" | "miss" | "fail";
  miss_count: number;
}

interface Incident {
  service: string;
  summary: string;
  detail: string;
  severity: "warn" | "critical";
}

interface OpsData {
  services: Service[];
  crons: CronJob[];
  incidents: Incident[];
}

const ECG_PATH =
  "M0 14 L20 14 L24 6 L28 22 L32 14 L60 14 L64 8 L68 20 L72 14 L100 14 L104 4 L108 24 L112 14 L120 14";

const UPCOMING = [
  { t: "+11m", l: "embed-docs", c: "var(--moss)" },
  { t: "+26m", l: "embed-docs", c: "var(--moss)" },
  { t: "+1h 41m", l: "embed-docs", c: "var(--moss)" },
  { t: "+3h 22m", l: "purge-old-sessions · retry", c: "var(--amber)" },
  { t: "+5h 18m", l: "morning-digest", c: "var(--moss)" },
];

function statusColor(s: string): string {
  if (s === "ok") return "var(--moss)";
  if (s === "warn" || s === "miss") return "var(--amber)";
  return "var(--claw-red)";
}

export function OpsPage() {
  const [data, setData] = useState<OpsData | null>(null);

  useEffect(() => {
    fetch("/api/v2/ops")
      .then((r) => r.json())
      .then(setData)
      .catch(console.error);
  }, []);

  if (!data) {
    return (
      <div style={{ padding: 40, color: "var(--ink-4)" }} className="mono">
        Loading ops…
      </div>
    );
  }

  return (
    <div style={{ flex: 1, display: "flex", flexDirection: "column", minHeight: 0 }}>
      <div style={{ flex: 1, display: "grid", gridTemplateRows: "auto 1fr", minHeight: 0 }}>

        {/* ── Heartbeats — top row ── */}
        <div style={{ padding: "20px 22px", borderBottom: "1px dashed var(--line)" }}>
          <div className="caps" style={{ color: "var(--ink-4)", marginBottom: 10 }}>
            Heartbeats · live · 1.4s sweep
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12 }}>
            {data.services.map((s, i) => {
              const c = statusColor(s.status);
              return (
                <div
                  key={i}
                  className="cm-card"
                  style={{ padding: 12, borderLeftWidth: 3, borderLeftStyle: "solid", borderLeftColor: c }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
                    <span style={{ fontSize: 12, fontWeight: 500, color: "var(--ink-2)" }}>{s.name}</span>
                    <span className="cm-tag" style={{ color: c, borderColor: c, fontSize: 9 }}>
                      {s.status.toUpperCase()}
                    </span>
                  </div>
                  <svg className="cm-ecg" viewBox="0 0 120 28" style={{ width: "100%", height: 28, marginTop: 6 }}>
                    <path d={ECG_PATH} fill="none" stroke={c} strokeWidth="1.4" />
                  </svg>
                  <div
                    className="mono"
                    style={{ fontSize: 10, color: "var(--ink-4)", display: "flex", justifyContent: "space-between", marginTop: 4 }}
                  >
                    <span>up {s.uptime}</span>
                    <span>{s.bpm} bpm · {s.latency}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* ── Cron board — bottom row, two columns ── */}
        <div style={{ display: "grid", gridTemplateColumns: "1.4fr 1fr", minHeight: 0 }}>

          {/* Left: Cron registry table */}
          <div style={{ padding: 22, overflow: "auto" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 12 }}>
              <div className="caps" style={{ color: "var(--ink-4)" }}>
                Cron registry · {data.crons.length} jobs
              </div>
              <button className="cm-btn tiny">+ schedule</button>
            </div>
            <div className="cm-card" style={{ padding: 0, overflow: "hidden" }}>
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "1.4fr 1fr 1.4fr 1fr 60px",
                  padding: "8px 14px",
                  background: "var(--panel-2)",
                  fontFamily: "var(--f-mono)",
                  fontSize: 9,
                  color: "var(--ink-4)",
                  textTransform: "uppercase",
                  letterSpacing: "0.06em",
                }}
              >
                <span>name</span>
                <span>cron</span>
                <span>last run</span>
                <span>next</span>
                <span />
              </div>
              {data.crons.map((cr) => {
                const c = statusColor(cr.status);
                return (
                  <div
                    key={cr.id}
                    style={{
                      display: "grid",
                      gridTemplateColumns: "1.4fr 1fr 1.4fr 1fr 60px",
                      padding: "10px 14px",
                      borderTop: "1px dashed var(--line)",
                      fontSize: 12,
                      alignItems: "center",
                      background: cr.status !== "ok" ? "var(--panel-2)" : "transparent",
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      <span style={{ width: 6, height: 6, borderRadius: "50%", background: c }} />
                      <span style={{ color: "var(--ink-2)" }}>{cr.name}</span>
                    </div>
                    <span className="mono" style={{ fontSize: 11, color: "var(--ink-3)" }}>{cr.schedule}</span>
                    <span className="mono" style={{ fontSize: 11, color: c }}>{cr.last_run}</span>
                    <span className="mono" style={{ fontSize: 11, color: "var(--ink-3)" }}>{cr.next_run}</span>
                    <button className="cm-btn tiny" style={{ padding: "2px 8px" }}>run</button>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Right: Incident watch + upcoming + SSE stub */}
          <div
            style={{
              borderLeft: "1px solid var(--line)",
              padding: 22,
              background: "var(--paper-deep)",
              overflow: "auto",
              display: "flex",
              flexDirection: "column",
              gap: 12,
            }}
          >
            {data.incidents.map((inc, i) => (
              <div key={i} className="cm-card" style={{ padding: 14, borderColor: statusColor(inc.severity) }}>
                <div className="caps" style={{ color: statusColor(inc.severity) }}>
                  Watch · {inc.service}
                </div>
                <div style={{ fontSize: 13, fontWeight: 500, marginTop: 2 }}>{inc.summary}</div>
                <div className="mono" style={{ fontSize: 11, color: "var(--ink-3)", marginTop: 6, lineHeight: 1.5 }}>
                  {inc.detail.split("\n").map((line, j) => (
                    <span key={j}>
                      {line}
                      {j < inc.detail.split("\n").length - 1 && <br />}
                    </span>
                  ))}
                </div>
                <button className="cm-btn tiny" style={{ marginTop: 10 }}>open runbook →</button>
              </div>
            ))}

            <div className="cm-card" style={{ padding: 14 }}>
              <div className="caps" style={{ color: "var(--ink-4)", marginBottom: 8 }}>
                Upcoming · next 6h
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                {UPCOMING.map((u, i) => (
                  <div key={i} style={{ display: "flex", alignItems: "center", gap: 10, padding: "4px 0", fontSize: 11 }}>
                    <span className="mono" style={{ width: 60, color: "var(--ink-4)" }}>{u.t}</span>
                    <span style={{ width: 6, height: 6, borderRadius: "50%", background: u.c }} />
                    <span style={{ color: "var(--ink-2)" }}>{u.l}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="cm-card" style={{ padding: 14, background: "var(--panel-2)" }}>
              <div className="mono" style={{ fontSize: 11, color: "var(--ink-3)" }}>
                Live logs — connecting...
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}