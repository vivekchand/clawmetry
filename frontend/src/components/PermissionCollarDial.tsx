import { Group } from "@visx/group";
import { Arc } from "@visx/shape";
import { LinearGradient } from "@visx/gradient";
import { motion } from "framer-motion";

export type RiskLevel = "high" | "med" | "low";

const SIZE = 220;
const CX = SIZE / 2;
const CY = SIZE / 2;
const OUTER = 98;
const INNER = 84;
const NEEDLE_LEN = 72;

function gradientId(level: RiskLevel): string {
  if (level === "high") return "collar-grad-high";
  if (level === "med") return "collar-grad-med";
  return "collar-grad-low";
}

function gradientStops(level: RiskLevel): [string, string] {
  if (level === "high") return ["var(--claw-red)", "var(--claw-red-deep)"];
  if (level === "med") return ["var(--amber)", "#C48A00"];
  return ["var(--moss)", "#4A7A3A"];
}

interface PermissionCollarDialProps {
  score: number;
  median: number;
  riskLevel: RiskLevel;
}

export function PermissionCollarDial({ score, median, riskLevel }: PermissionCollarDialProps) {
  const clamped = Math.max(0, Math.min(1, score));
  const endAngle = clamped * Math.PI * 2;
  const [startColor, endColor] = gradientStops(riskLevel);
  const gid = gradientId(riskLevel);
  const needleDeg = clamped * 360 - 90;

  return (
    <div style={{ position: "relative", width: SIZE, height: SIZE }}>
      <svg viewBox={`0 0 ${SIZE} ${SIZE}`} width={SIZE} height={SIZE}>
        <LinearGradient id={gid} from={startColor} to={endColor} vertical={false} />
        <Group top={CY} left={CX}>
          <Arc
            outerRadius={OUTER}
            innerRadius={INNER}
            startAngle={0}
            endAngle={Math.PI * 2}
            fill="var(--panel-3)"
            cornerRadius={2}
          />
          {clamped > 0.005 && (
            <Arc
              outerRadius={OUTER}
              innerRadius={INNER}
              startAngle={-Math.PI / 2}
              endAngle={-Math.PI / 2 + endAngle}
              fill={`url(#${gid})`}
              cornerRadius={2}
            />
          )}
          {Array.from({ length: 24 }).map((_, i) => {
            const a = (i / 24) * Math.PI * 2 - Math.PI / 2;
            const x1 = Math.cos(a) * (OUTER - 12);
            const y1 = Math.sin(a) * (OUTER - 12);
            const x2 = Math.cos(a) * (OUTER - 20);
            const y2 = Math.sin(a) * (OUTER - 20);
            return (
              <line
                key={i}
                x1={x1}
                y1={y1}
                x2={x2}
                y2={y2}
                stroke="var(--ink-4)"
                strokeWidth={1}
                opacity={0.5}
              />
            );
          })}
          <motion.g
            animate={{ rotate: needleDeg }}
            transition={{ type: "spring", stiffness: 90, damping: 16 }}
            style={{ transformOrigin: "0px 0px" }}
          >
            <line x1={0} y1={0} x2={0} y2={-NEEDLE_LEN} stroke="var(--ink-2)" strokeWidth={2.5} strokeLinecap="round" />
            <circle cx={0} cy={0} r={5} fill="var(--ink-2)" />
          </motion.g>
        </Group>
        <text x={CX} y={CY - 10} textAnchor="middle" fontFamily="var(--f-mono)" fontSize={10} fill="var(--ink-4)">
          RISK
        </text>
        <text x={CX} y={CY + 22} textAnchor="middle" fontFamily="Instrument Serif, serif" fontSize={40} fill="var(--ink-2)">
          {clamped.toFixed(2)}
        </text>
        <text x={CX} y={CY + 38} textAnchor="middle" fontFamily="var(--f-mono)" fontSize={9} fill="var(--ink-4)">
          vs {median.toFixed(2)} median
        </text>
      </svg>
    </div>
  );
}
