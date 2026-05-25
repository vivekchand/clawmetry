import { useState, useEffect } from "react";

interface Turn {
  id: string;
  time: string;
  channel: string;
  channel_emoji: string;
  user: string;
  steps: string[];
  skill: string | null;
  llms: string[];
  tools: string[];
  duration_ms: number;
  active: boolean;
  source: string;
  severity: string | null;
}

interface BrainData {
  turns: Turn[];
  total: number;
}

const STEP_COLORS: Record<string, string> = {
  USER:    "var(--plum)",
  THINK:   "var(--moss)",
  EXEC:    "var(--amber)",
  READ:    "var(--ocean, #3b82f6)",
  AGENT:   "var(--claw-red)",
  TOOL:    "var(--amber)",
  EVENT:   "var(--ink-4)",
};

function stepColor(step: string): string {
  return STEP_COLORS[step] ?? "var(--ink-4)";
}

function StepChip({ step }: { step: string }) {
  const c = stepColor(step);
  return (
    <span
      style={{
        display: "inline-block",
        padding: "1px 7px",
        borderRadius: 999,
        border: `1px solid ${c}`,
        color: c,
        fontSize: 9,
        fontFamily: "var(--f-mono)",
        fontWeight: 600,
        letterSpacing: "0.05em",
        textTransform: "uppercase",
        lineHeight: "16px",
      }}
    >
      {step}
    </span>
  );
}

function TurnRow({ turn }: { turn: Turn }) {
  const [expanded, setExpanded] = useState(false);
  const severityColor =
    turn.severity === "critical" ? "var(--claw-red)"
    : turn.severity === "high"   ? "var(--amber)"
    : "transparent";

  return (
    <div
      style={{
        borderTop: "1px dashed var(--line)",
        borderLeft: `3px solid ${severityColor}`,
        background: expanded ? "var(--paper-deep)" : "transparent",
        cursor: "pointer",
        transition: "background 100ms ease-out",
      }}
      onClick={() => setExpanded((e) => !e)}
    >
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "80px 90px 1fr auto",
          alignItems: "center",
          gap: 12,
          padding: "9px 16px",
        }}
      >
        {/* Time */}
        <span className="mono" style={{ fontSize: 11, color: "var(--ink-4)" }}>
          {turn.time || "—"}
        </span>

        {/* Channel badge */}
        <span style={{ fontSize: 12, color: "var(--ink-3)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
          {turn.channel_emoji} {turn.channel}
        </span>

        {/* Content preview + step chips */}
        <div style={{ display: "flex", flexDirection: "column", gap: 3, minWidth: 0 }}>
          <span
            style={{
              fontSize: 12,
              color: "var(--ink-2)",
              whiteSpace: "nowrap",
              overflow: "hidden",
              textOverflow: "ellipsis",
            }}
          >
            {turn.user || "—"}
          </span>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
            {turn.steps.map((s, i) => <StepChip key={i} step={s} />)}
            {turn.llms.map((m, i) => (
              <span key={i} className="cm-tag" style={{ fontSize: 9, padding: "0 5px" }}>{m}</span>
            ))}
            {turn.tools.map((t, i) => (
              <span key={i} className="cm-tag" style={{ fontSize: 9, padding: "0 5px", color: "var(--amber)", borderColor: "var(--amber)" }}>{t}</span>
            ))}
          </div>
        </div>

        {/* Duration + active pill */}
        <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 3, flexShrink: 0 }}>
          {turn.active && (
            <span className="cm-badge" style={{ color: "var(--moss)", fontSize: 9 }}>
              <span className="dot cm-pulse" /> LIVE
            </span>
          )}
          {turn.duration_ms > 0 && (
            <span className="mono" style={{ fontSize: 10, color: "var(--ink-4)" }}>
              {turn.duration_ms < 1000 ? `${turn.duration_ms}ms` : `${(turn.duration_ms / 1000).toFixed(1)}s`}
            </span>
          )}
        </div>
      </div>

      {/* Expanded transcript bubble */}
      {expanded && turn.user && (
        <div style={{ padding: "0 16px 14px 108px" }}>
          <div
            className="cm-card"
            style={{
              padding: "10px 14px",
              background: "var(--panel-2)",
              fontFamily: "var(--f-mono)",
              fontSize: 12,
              color: "var(--ink-2)",
              lineHeight: 1.6,
              whiteSpace: "pre-wrap",
              wordBreak: "break-word",
            }}
          >
            {turn.user}
          </div>
          {turn.source && (
            <div className="mono" style={{ fontSize: 10, color: "var(--ink-4)", marginTop: 5 }}>
              session: {turn.source}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export function BrainPage() {
  const [data, setData] = useState<BrainData | null>(null);

  useEffect(() => {
    fetch("/api/v2/brain?limit=50")
      .then((r) => r.json())
      .then(setData)
      .catch(console.error);
  }, []);

  if (!data) {
    return (
      <div style={{ padding: 40, color: "var(--ink-4)" }} className="mono">
        Loading brain events…
      </div>
    );
  }

  if (data.turns.length === 0) {
    return (
      <div style={{ padding: "80px 40px", textAlign: "center" }}>
        <div style={{ fontSize: 32, marginBottom: 12 }}>✦</div>
        <div style={{ fontSize: 15, color: "var(--ink-3)" }}>All quiet. No brain events yet.</div>
        <div className="mono" style={{ fontSize: 11, color: "var(--ink-4)", marginTop: 8 }}>
          Start an OpenClaw session to see the per-turn timeline here.
        </div>
      </div>
    );
  }

  return (
    <div style={{ flex: 1, display: "flex", flexDirection: "column", minHeight: 0, overflow: "auto" }}>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "80px 90px 1fr auto",
          gap: 12,
          padding: "8px 16px",
          background: "var(--panel-2)",
          fontFamily: "var(--f-mono)",
          fontSize: 9,
          color: "var(--ink-4)",
          textTransform: "uppercase",
          letterSpacing: "0.06em",
          borderBottom: "1px solid var(--line)",
          position: "sticky",
          top: 0,
        }}
      >
        <span>time</span>
        <span>channel</span>
        <span>event</span>
        <span style={{ textAlign: "right" }}>{data.total} events</span>
      </div>
      {data.turns.map((t) => (
        <TurnRow key={t.id} turn={t} />
      ))}
    </div>
  );
}
