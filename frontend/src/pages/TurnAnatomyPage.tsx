// Turn anatomy — per-turn horizontal waterfall of one session's spans.
//
// Each turn is partitioned on a prompt boundary; its spans (prompt / model /
// tool_call / tool_result / compaction / reply) are laid out as a waterfall
// where bar width ∝ duration_ms and bar offset ∝ (started_ms - turn_start).
// Click a span to expand its detail; pick a session from the left rail; the
// "stalled" feed (long-running mid-turn sessions) sits in its own card and
// each stalled row jumps you to that session.
//
// Live APIs (routes/turn_anatomy.py):
//   GET /api/turn-anatomy?session_id=…   → {available, turns:[{spans:[…]}]}
//   GET /api/turn-anatomy/stalled        → {stalled:[…], threshold_min}
//   GET /api/sessions                    → {sessions:[…]} (the picker)
// Polls every 5s while the tab is visible; never crashes on empty data.

import { useState, useEffect, useRef } from "react";

type SpanKind =
  | "prompt"
  | "model"
  | "tool"
  | "tool_call"
  | "tool_result"
  | "compaction"
  | "reply";

interface Span {
  kind: SpanKind;
  label: string;
  started_ms: number;
  ended_ms: number;
  duration_ms: number;
  status?: string;
  tokens?: number | null;
  model?: string | null;
}

interface Turn {
  turn: number;
  started_ms: number;
  ended_ms: number;
  duration_ms: number;
  prompt?: string;
  tool_count?: number;
  total_tokens?: number;
  span_count?: number;
  status?: string;
  spans: Span[];
}

interface AnatomyData {
  available: boolean;
  session_id: string;
  turns: Turn[];
  turn_count?: number;
}

interface Stalled {
  session_id: string;
  idle_min: number;
  last_kind: string;
  pending_tool: boolean;
  event_count: number;
}

interface SessionRow {
  session_id: string;
  title?: string;
  updated_at?: string;
  total_tokens?: number;
  message_count?: number;
  status?: string;
}

// Span kind → bar colour. tool_call / tool_result fold into the tool colour.
const KIND_COLOR: Record<string, string> = {
  prompt: "var(--ocean, #3b82f6)",
  model: "var(--plum)",
  reply: "var(--moss)",
  tool: "var(--amber)",
  tool_call: "var(--amber)",
  tool_result: "var(--amber)",
  compaction: "var(--claw-red)",
};

function spanColor(s: Span): string {
  if (s.status === "error") return "var(--claw-red)";
  return KIND_COLOR[s.kind] ?? "var(--ink-4)";
}

function fmtDur(ms: number): string {
  if (!ms || ms < 0) return "0ms";
  if (ms < 1000) return `${Math.round(ms)}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
  return `${(ms / 60000).toFixed(1)}m`;
}

function TurnWaterfall({ turn }: { turn: Turn }) {
  const [openSpan, setOpenSpan] = useState<number | null>(null);
  const spans = turn.spans ?? [];
  // Waterfall scale is the turn's own span. Guard a zero-width turn so a
  // single instantaneous span still renders a visible bar.
  const t0 = turn.started_ms || (spans[0]?.started_ms ?? 0);
  const t1 = turn.ended_ms || (spans[spans.length - 1]?.ended_ms ?? t0 + 1);
  const span = Math.max(1, t1 - t0);
  const err = turn.status === "error";

  return (
    <div className="cm-card" style={{ padding: 0, overflow: "hidden" }}>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 10,
          padding: "10px 14px",
          borderBottom: "1px solid var(--line)",
          background: err ? "var(--claw-red-wash)" : "var(--panel-2)",
        }}
      >
        <span className="mono" style={{ fontSize: 11, fontWeight: 700, color: err ? "var(--claw-red)" : "var(--ink-3)" }}>
          turn {turn.turn}
        </span>
        <span style={{ flex: 1, fontSize: 12, color: "var(--ink-2)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", minWidth: 0 }} title={turn.prompt || ""}>
          {turn.prompt || "(no prompt)"}
        </span>
        <span className="mono" style={{ fontSize: 10, color: "var(--ink-4)", whiteSpace: "nowrap" }}>
          {turn.tool_count ? `${turn.tool_count}🔧 · ` : ""}
          {(turn.total_tokens ?? 0).toLocaleString()} tok · {fmtDur(turn.duration_ms)}
        </span>
      </div>

      <div style={{ padding: "8px 14px", display: "flex", flexDirection: "column", gap: 3 }}>
        {spans.length === 0 && (
          <div className="mono" style={{ fontSize: 11, color: "var(--ink-4)", padding: "6px 0" }}>No spans.</div>
        )}
        {spans.map((s, i) => {
          const left = ((s.started_ms - t0) / span) * 100;
          const w = Math.max(0.8, (Math.max(0, s.duration_ms) / span) * 100);
          const open = openSpan === i;
          return (
            <div key={i}>
              <div
                onClick={() => setOpenSpan(open ? null : i)}
                style={{ display: "flex", alignItems: "center", gap: 8, cursor: "pointer", padding: "2px 0" }}
                title={`${s.label} · ${fmtDur(s.duration_ms)}`}
              >
                <span className="mono" style={{ width: 84, fontSize: 9, color: "var(--ink-4)", textAlign: "right", flexShrink: 0 }}>
                  {s.kind === "tool" || s.kind === "tool_call" ? "tool" : s.kind}
                </span>
                <div style={{ position: "relative", flex: 1, height: 16, background: "var(--panel-2)", borderRadius: 3, minWidth: 0 }}>
                  <div
                    style={{
                      position: "absolute",
                      left: `${Math.min(99, Math.max(0, left))}%`,
                      width: `${Math.min(100 - left, w)}%`,
                      top: 0,
                      bottom: 0,
                      background: spanColor(s),
                      borderRadius: 3,
                      opacity: open ? 1 : 0.85,
                      minWidth: 2,
                    }}
                  />
                  <span
                    className="mono"
                    style={{
                      position: "absolute",
                      left: 6,
                      top: 2,
                      fontSize: 9,
                      color: "var(--ink-2)",
                      whiteSpace: "nowrap",
                      overflow: "hidden",
                      maxWidth: "90%",
                      textOverflow: "ellipsis",
                      pointerEvents: "none",
                    }}
                  >
                    {s.label}
                  </span>
                </div>
                <span className="mono" style={{ width: 52, fontSize: 9, color: "var(--ink-4)", textAlign: "right", flexShrink: 0 }}>
                  {fmtDur(s.duration_ms)}
                </span>
              </div>
              {open && (
                <div
                  className="mono"
                  style={{
                    margin: "2px 0 4px 92px",
                    padding: "8px 10px",
                    fontSize: 10,
                    color: "var(--ink-3)",
                    background: "var(--panel-2)",
                    borderRadius: 5,
                    border: "1px dashed var(--line-strong)",
                    lineHeight: 1.7,
                  }}
                >
                  <div><span style={{ color: "var(--ink-4)" }}>kind</span> {s.kind}</div>
                  <div><span style={{ color: "var(--ink-4)" }}>label</span> {s.label || "—"}</div>
                  <div><span style={{ color: "var(--ink-4)" }}>duration</span> {fmtDur(s.duration_ms)} ({Math.round(s.duration_ms)}ms)</div>
                  {s.tokens ? <div><span style={{ color: "var(--ink-4)" }}>tokens</span> {s.tokens.toLocaleString()}</div> : null}
                  {s.model ? <div><span style={{ color: "var(--ink-4)" }}>model</span> {s.model}</div> : null}
                  <div><span style={{ color: "var(--ink-4)" }}>status</span> <span style={{ color: s.status === "error" ? "var(--claw-red)" : "var(--moss)" }}>{s.status || "ok"}</span></div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

export function TurnAnatomyPage() {
  const [sessions, setSessions] = useState<SessionRow[]>([]);
  const [picked, setPicked] = useState<string>("");
  const [data, setData] = useState<AnatomyData | null>(null);
  const [stalled, setStalled] = useState<Stalled[]>([]);
  const [errored, setErrored] = useState(false);
  const timer = useRef<ReturnType<typeof setInterval> | null>(null);
  const pickedRef = useRef(picked);
  pickedRef.current = picked;

  // Session list + stalled feed (refreshed alongside the anatomy poll).
  useEffect(() => {
    let cancelled = false;
    async function loadMeta() {
      if (typeof document !== "undefined" && document.hidden) return;
      try {
        const [s, st] = await Promise.all([
          fetch("/api/sessions").then((r) => r.json()),
          fetch("/api/turn-anatomy/stalled").then((r) => r.json()),
        ]);
        if (cancelled) return;
        const rows: SessionRow[] = s?.sessions ?? [];
        setSessions(rows);
        setStalled(st?.stalled ?? []);
        // Auto-pick the most-recent session on first load.
        if (!pickedRef.current && rows.length > 0) setPicked(rows[0].session_id);
      } catch (e) {
        console.error(e);
      }
    }
    loadMeta();
    const t = setInterval(loadMeta, 8000);
    return () => {
      cancelled = true;
      clearInterval(t);
    };
  }, []);

  // Anatomy for the picked session.
  useEffect(() => {
    if (!picked) return;
    let cancelled = false;
    async function load() {
      if (typeof document !== "undefined" && document.hidden) return;
      try {
        const d = await fetch(`/api/turn-anatomy?session_id=${encodeURIComponent(picked)}`).then((r) => r.json());
        if (cancelled) return;
        setData(d);
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
  }, [picked]);

  const turns = data?.turns ?? [];

  return (
    <div style={{ flex: 1, display: "flex", minWidth: 0, minHeight: 0 }}>
      {/* ── Session rail ── */}
      <div style={{ width: 240, borderRight: "1px solid var(--line)", overflow: "auto", padding: 14, flexShrink: 0 }}>
        <div className="caps" style={{ color: "var(--ink-4)", marginBottom: 10 }}>Sessions · {sessions.length}</div>
        {sessions.length === 0 && (
          <div className="mono" style={{ fontSize: 11, color: "var(--ink-4)" }}>No sessions yet.</div>
        )}
        {sessions.map((s) => {
          const sel = s.session_id === picked;
          return (
            <div
              key={s.session_id}
              onClick={() => { setData(null); setPicked(s.session_id); }}
              style={{
                padding: "8px 10px",
                borderRadius: 6,
                marginBottom: 4,
                cursor: "pointer",
                background: sel ? "var(--panel-2)" : "transparent",
                border: sel ? "1px solid var(--line-strong)" : "1px solid transparent",
              }}
            >
              <div style={{ fontSize: 12, color: "var(--ink-2)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                {s.title || s.session_id.slice(0, 18)}
              </div>
              <div className="mono" style={{ fontSize: 9, color: "var(--ink-4)", marginTop: 2 }}>
                {(s.message_count ?? 0)} msg · {(s.total_tokens ?? 0).toLocaleString()} tok
              </div>
            </div>
          );
        })}
      </div>

      {/* ── Waterfall + stalled ── */}
      <div style={{ flex: 1, padding: 22, overflow: "auto", display: "flex", flexDirection: "column", gap: 16, minWidth: 0 }}>
        {/* Stalled feed */}
        <div className="cm-card" style={{ padding: 14 }}>
          <div className="caps" style={{ color: stalled.length ? "var(--amber)" : "var(--ink-4)", marginBottom: 8 }}>
            Stalled turns · {stalled.length}
          </div>
          {stalled.length === 0 ? (
            <div className="mono" style={{ fontSize: 11, color: "var(--ink-4)" }}>No turns appear stuck.</div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
              {stalled.slice(0, 8).map((s) => (
                <div
                  key={s.session_id}
                  onClick={() => { setData(null); setPicked(s.session_id); }}
                  style={{ display: "flex", alignItems: "center", gap: 10, fontSize: 12, padding: "4px 0", cursor: "pointer", borderTop: "1px dashed var(--line)" }}
                >
                  <span className="cm-tag" style={{ color: "var(--amber)", borderColor: "var(--amber)", fontSize: 9 }}>
                    idle {s.idle_min}m
                  </span>
                  <span className="mono" style={{ flex: 1, color: "var(--ink-2)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", minWidth: 0 }}>
                    {s.session_id.slice(0, 24)}
                  </span>
                  <span className="mono" style={{ fontSize: 10, color: "var(--ink-4)" }}>
                    {s.pending_tool ? "pending tool" : s.last_kind}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Turn waterfalls */}
        {!picked ? (
          <div className="mono" style={{ padding: 40, color: "var(--ink-4)" }}>Pick a session to inspect its turns.</div>
        ) : !data ? (
          <div className="mono" style={{ padding: 40, color: "var(--ink-4)" }}>
            {errored ? "Failed to load turn anatomy." : "Loading turns…"}
          </div>
        ) : !data.available || turns.length === 0 ? (
          <div style={{ padding: "60px 40px", textAlign: "center" }}>
            <div style={{ fontSize: 30, marginBottom: 10 }}>◐</div>
            <div style={{ fontSize: 14, color: "var(--ink-3)" }}>No turns recorded for this session yet.</div>
          </div>
        ) : (
          <>
            <div className="caps" style={{ color: "var(--ink-4)" }}>
              {turns.length} turns · waterfall (bar width ∝ duration)
            </div>
            {turns.map((t) => <TurnWaterfall key={t.turn} turn={t} />)}
          </>
        )}
      </div>
    </div>
  );
}
