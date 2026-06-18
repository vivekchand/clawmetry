// Live Trace — Stage A: reads /api/flow snapshot, polls every 3 s.
// Two-pane layout: event feed (left) | activity summary (right).
// Hover-scrub waterfall is Stage B (needs boards-dashboards.jsx reference).

import { useState, useEffect, useRef } from "react";

interface FlowEvent {
  type: "msg_in" | "msg_out" | "tool_call" | "tool_result" | string;
  channel?: string;
  tool?: string;
  ts?: string;
  session_id?: string;
}

interface FlowResponse {
  ok: boolean;
  events: FlowEvent[];
  _source?: string;
}

const TYPE_ICON: Record<string, string> = {
  msg_in:      "→",
  msg_out:     "←",
  tool_call:   "⚡",
  tool_result: "✓",
};

const TYPE_COLOR: Record<string, string> = {
  msg_in:      "var(--ocean, #3b82f6)",
  msg_out:     "var(--moss)",
  tool_call:   "var(--amber)",
  tool_result: "var(--ink-3)",
};

function formatTs(ts: string | undefined): string {
  if (!ts) return "—";
  const d = new Date(ts);
  if (isNaN(d.getTime())) return ts.slice(11, 19) || ts.slice(0, 8);
  return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

function EventRow({ ev, index }: { ev: FlowEvent; index: number }) {
  const color = TYPE_COLOR[ev.type] ?? "var(--ink-3)";
  const icon  = TYPE_ICON[ev.type]  ?? "·";
  const label = ev.channel ?? ev.tool ?? ev.type;

  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "20px 80px 1fr 90px",
        gap: 8,
        alignItems: "center",
        padding: "5px 14px",
        borderTop: index === 0 ? "none" : "1px dashed var(--line)",
      }}
    >
      <span style={{ color, fontSize: 12, fontWeight: 700, textAlign: "center" }}>{icon}</span>
      <span
        style={{
          fontSize: 10,
          fontFamily: "var(--f-mono)",
          padding: "1px 6px",
          borderRadius: 4,
          border: `1px solid ${color}`,
          color,
          textAlign: "center",
          whiteSpace: "nowrap",
          overflow: "hidden",
          textOverflow: "ellipsis",
        }}
      >
        {ev.type.replace(/_/g, " ")}
      </span>
      <span
        style={{
          fontSize: 12,
          color: "var(--ink-2)",
          overflow: "hidden",
          textOverflow: "ellipsis",
          whiteSpace: "nowrap",
        }}
      >
        {label}
      </span>
      <span
        style={{
          fontSize: 10,
          color: "var(--ink-4)",
          fontFamily: "var(--f-mono)",
          textAlign: "right",
        }}
      >
        {formatTs(ev.ts)}
      </span>
    </div>
  );
}

function ActivitySummary({ events }: { events: FlowEvent[] }) {
  const counts = {
    msg_in:      events.filter(e => e.type === "msg_in").length,
    msg_out:     events.filter(e => e.type === "msg_out").length,
    tool_call:   events.filter(e => e.type === "tool_call").length,
    tool_result: events.filter(e => e.type === "tool_result").length,
  };

  const activeTool = events.filter(e => e.type === "tool_call").length;
  const mood  = activeTool > 10 ? "◉" : activeTool > 0 ? "◎" : "○";
  const moodC = activeTool > 10 ? "var(--amber)" : activeTool > 0 ? "var(--moss)" : "var(--ink-4)";

  return (
    <div style={{ padding: 16, display: "flex", flexDirection: "column", gap: 14 }}>
      <div
        style={{
          fontSize: 11,
          color: "var(--ink-4)",
          textTransform: "uppercase",
          letterSpacing: "0.08em",
        }}
      >
        Activity
      </div>

      <div style={{ textAlign: "center", fontSize: 32, color: moodC, lineHeight: 1 }}>{mood}</div>

      <div style={{ display: "flex", flexDirection: "column", gap: 7 }}>
        {(
          [
            ["User msgs",  counts.msg_in,      TYPE_COLOR.msg_in],
            ["Replies",    counts.msg_out,     TYPE_COLOR.msg_out],
            ["Tool calls", counts.tool_call,   TYPE_COLOR.tool_call],
            ["Results",    counts.tool_result, TYPE_COLOR.tool_result],
          ] as [string, number, string][]
        ).map(([label, count, color]) => (
          <div
            key={label}
            style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}
          >
            <span style={{ fontSize: 11, color: "var(--ink-3)" }}>{label}</span>
            <span
              style={{
                fontSize: 11,
                color,
                fontFamily: "var(--f-mono)",
                fontWeight: 700,
              }}
            >
              {count}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

export function FlowTracePage() {
  const [data,  setData]  = useState<FlowResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const timer = useRef<ReturnType<typeof setInterval> | null>(null);

  function load() {
    fetch("/api/flow", { headers: { Accept: "application/json" } })
      .then(r => r.json())
      .then((d: FlowResponse) => { setData(d); setError(null); })
      .catch(e => setError(String(e)));
  }

  useEffect(() => {
    load();
    timer.current = setInterval(load, 3000);
    return () => { if (timer.current) clearInterval(timer.current); };
  }, []);

  if (error) {
    return (
      <div style={{ padding: 40, color: "var(--claw-red)" }} className="mono">
        {error}
      </div>
    );
  }

  if (!data) {
    return (
      <div style={{ padding: 40, color: "var(--ink-4)" }} className="mono">
        Loading trace…
      </div>
    );
  }

  const events  = data.events ?? [];
  const recent  = [...events].reverse().slice(0, 60);

  if (events.length === 0) {
    return (
      <div style={{ padding: "80px 40px", textAlign: "center" }}>
        <div style={{ fontSize: 32, marginBottom: 12 }}>◐</div>
        <div style={{ fontSize: 15, color: "var(--ink-3)" }}>All quiet. No live traces.</div>
        <div style={{ fontSize: 12, color: "var(--ink-4)", marginTop: 8 }}>
          Waiting for OpenClaw activity…
        </div>
      </div>
    );
  }

  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "1fr 160px",
        height: "100%",
        overflow: "hidden",
      }}
    >
      {/* Left: chronological event feed */}
      <div style={{ overflowY: "auto", borderRight: "1px solid var(--line)" }}>
        <div
          style={{
            padding: "7px 14px 5px",
            borderBottom: "1px solid var(--line)",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <span
            style={{
              fontSize: 11,
              color: "var(--ink-4)",
              textTransform: "uppercase",
              letterSpacing: "0.08em",
            }}
          >
            Live events · {events.length} total
          </span>
          {data._source && (
            <span style={{ fontSize: 10, color: "var(--ink-4)", fontFamily: "var(--f-mono)" }}>
              {data._source}
            </span>
          )}
        </div>
        {recent.map((ev, i) => (
          <EventRow key={i} ev={ev} index={i} />
        ))}
      </div>

      {/* Right: activity summary */}
      <div style={{ overflowY: "auto" }}>
        <ActivitySummary events={events} />
      </div>
    </div>
  );
}
