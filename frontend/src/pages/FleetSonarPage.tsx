import { useState, useEffect } from "react";
import { ProPaywallModal } from "../components/ProPaywallModal";

interface FleetNode {
  id: string;
  label: string;
  status: "live" | "await" | "alert";
  r: number;
  theta: number;
  last_seen_ts: number;
}

interface FleetData {
  nodes: FleetNode[];
  is_single_node: boolean;
}

// Radar geometry
const R = 155;
const CX = 180;
const CY = 180;

function nodeColor(status: string): string {
  if (status === "live") return "var(--moss)";
  if (status === "await") return "var(--amber)";
  return "var(--claw-red)";
}

function nodeX(n: FleetNode): number {
  return CX + n.r * R * Math.cos(n.theta - Math.PI / 2);
}

function nodeY(n: FleetNode): number {
  return CY + n.r * R * Math.sin(n.theta - Math.PI / 2);
}

function tsAgo(ts: number): string {
  if (!ts) return "—";
  const delta = Math.floor(Date.now() / 1000 - ts);
  if (delta < 60) return `${delta}s ago`;
  if (delta < 3600) return `${Math.floor(delta / 60)}m ago`;
  return `${Math.floor(delta / 3600)}h ago`;
}

// Sweep glow wedge endpoint (20° arc ahead of the beam)
const GLOW_ANGLE = 0.35; // radians
const sweepGlowX = CX + R * Math.sin(GLOW_ANGLE);
const sweepGlowY = CY - R * Math.cos(GLOW_ANGLE);

export function FleetSonarPage() {
  const [data, setData] = useState<FleetData | null>(null);
  const [paywallOpen, setPaywallOpen] = useState(false);

  useEffect(() => {
    fetch("/api/v2/fleet")
      .then((r) => r.json())
      .then(setData)
      .catch(console.error);
  }, []);

  return (
    <div
      style={{
        flex: 1,
        padding: "20px 22px",
        display: "flex",
        flexDirection: "column",
        minHeight: 0,
        overflowY: "auto",
      }}
    >
      {/* Header */}
      <div
        style={{
          display: "flex",
          alignItems: "baseline",
          gap: 10,
          marginBottom: 20,
        }}
      >
        <span className="caps" style={{ color: "var(--ink-4)" }}>
          Fleet sonar
        </span>
        {data && (
          <span style={{ fontSize: 11, color: "var(--ink-4)" }}>
            {data.nodes.length} node{data.nodes.length !== 1 ? "s" : ""}
          </span>
        )}
      </div>

      <div
        style={{
          display: "flex",
          gap: 28,
          alignItems: "flex-start",
          flexWrap: "wrap",
        }}
      >
        {/* ── Radar ─────────────────────────────────────────────────── */}
        <svg
          width={CX * 2}
          height={CY * 2}
          style={{ flexShrink: 0, display: "block" }}
          aria-label="Fleet radar"
        >
          {/* Rings */}
          <circle
            cx={CX}
            cy={CY}
            r={R}
            fill="none"
            stroke="var(--line)"
            strokeWidth={1}
          />
          {[0.5, 0.75].map((f) => (
            <circle
              key={f}
              cx={CX}
              cy={CY}
              r={f * R}
              fill="none"
              stroke="var(--line)"
              strokeWidth={1}
              strokeDasharray="3 6"
            />
          ))}

          {/* Cross-hairs */}
          <line
            x1={CX}
            y1={CY - R}
            x2={CX}
            y2={CY + R}
            stroke="var(--line)"
            strokeWidth={1}
          />
          <line
            x1={CX - R}
            y1={CY}
            x2={CX + R}
            y2={CY}
            stroke="var(--line)"
            strokeWidth={1}
          />

          {/* Sweep beam — 4s linear via CSS cm-sweep keyframe */}
          <g
            style={{
              transformOrigin: `${CX}px ${CY}px`,
              animation: "cm-sweep 4s linear infinite",
            }}
          >
            {/* Glow wedge ahead of beam */}
            <path
              d={`M ${CX} ${CY} L ${CX} ${CY - R} A ${R} ${R} 0 0 1 ${sweepGlowX} ${sweepGlowY} Z`}
              fill="var(--moss)"
              opacity={0.06}
            />
            {/* Beam line */}
            <line
              x1={CX}
              y1={CY}
              x2={CX}
              y2={CY - R}
              stroke="var(--moss)"
              strokeWidth={2}
              opacity={0.9}
            />
          </g>

          {/* Node pins */}
          {(data?.nodes ?? []).map((node) => {
            const nx = nodeX(node);
            const ny = nodeY(node);
            const col = nodeColor(node.status);
            return (
              <g
                key={node.id}
                style={{ cursor: "pointer" }}
                onClick={() => setPaywallOpen(true)}
                role="button"
                aria-label={`Node ${node.label}`}
              >
                {/* Pulse ring — 1.4s heartbeat */}
                <circle
                  cx={nx}
                  cy={ny}
                  r={9}
                  fill="none"
                  stroke={col}
                  strokeWidth={1}
                  style={{ animation: "pin-pulse 1.4s ease-in-out infinite" }}
                />
                {/* Core dot */}
                <circle
                  cx={nx}
                  cy={ny}
                  r={5}
                  fill={col}
                  stroke="var(--paper)"
                  strokeWidth={1.5}
                />
                {/* Label */}
                <text
                  x={nx + 10}
                  y={ny + 4}
                  fontSize={11}
                  fill="var(--ink-3)"
                  style={{ fontFamily: "inherit", userSelect: "none" }}
                >
                  {node.label}
                </text>
              </g>
            );
          })}
        </svg>

        {/* ── Right panel ───────────────────────────────────────────── */}
        <div
          style={{ flex: 1, minWidth: 220, display: "flex", flexDirection: "column", gap: 10 }}
        >
          {/* Node status rows */}
          {(data?.nodes ?? []).map((node) => {
            const col = nodeColor(node.status);
            return (
              <div
                key={node.id}
                className="cm-card"
                style={{
                  padding: "10px 14px",
                  display: "flex",
                  alignItems: "center",
                  gap: 10,
                }}
              >
                <div
                  style={{
                    width: 8,
                    height: 8,
                    borderRadius: "50%",
                    background: col,
                    flexShrink: 0,
                  }}
                />
                <span
                  style={{ flex: 1, fontSize: 13, color: "var(--ink)" }}
                >
                  {node.label}
                </span>
                <span
                  className="mono"
                  style={{ fontSize: 11, color: "var(--ink-4)" }}
                >
                  {tsAgo(node.last_seen_ts)}
                </span>
              </div>
            );
          })}

          {/* Upgrade CTA for single-node OSS */}
          {data?.is_single_node && (
            <div
              className="cm-card"
              style={{
                padding: "16px",
                borderColor: "var(--line)",
                marginTop: 6,
              }}
            >
              <div
                className="caps"
                style={{ color: "var(--claw-red)", marginBottom: 6 }}
              >
                Fleet · Cloud Pro
              </div>
              <p
                style={{
                  margin: "0 0 12px",
                  fontSize: 13,
                  color: "var(--ink-3)",
                  lineHeight: 1.5,
                }}
              >
                You are running a single node. Connect additional machines to
                see your full fleet on this radar.
              </p>
              <button
                type="button"
                className="cm-btn primary"
                onClick={() => setPaywallOpen(true)}
              >
                Add nodes via Cloud
              </button>
            </div>
          )}
        </div>
      </div>

      <ProPaywallModal
        open={paywallOpen}
        onClose={() => setPaywallOpen(false)}
        feature="Fleet sonar"
      />

      <style>{`
        @keyframes cm-sweep {
          from { transform: rotate(0deg); }
          to   { transform: rotate(360deg); }
        }
        @keyframes pin-pulse {
          0%, 100% { opacity: 0.45; r: 9px; }
          50%       { opacity: 0.08; r: 14px; }
        }
      `}</style>
    </div>
  );
}
