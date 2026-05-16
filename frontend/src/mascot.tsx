// Clawbert — the ClawMetry mascot, ported verbatim from
// design_handoff_clawmetry_v2/mascot.jsx with TypeScript types added.
// Inline SVG so it can be tinted, posed, and reused anywhere in the system.

import type { CSSProperties, ReactNode } from "react";

export type Mood = "calm" | "happy" | "wink" | "worried";
export type Tool = "wrench" | "magnifier" | "clipboard" | null;

interface ClawbertProps {
  size?: number;
  mood?: Mood;
  tool?: Tool;
  color?: string;
  shadow?: string;
  style?: CSSProperties;
}

export function Clawbert({
  size = 120,
  mood = "happy",
  tool = "wrench",
  color = "var(--claw-red)",
  shadow = "var(--claw-red-deep)",
  style,
}: ClawbertProps) {
  const eye: ReactNode =
    mood === "wink" ? (
      <ellipse cx="-7" cy="-2" rx="3" ry="0.5" fill="#1A1816" />
    ) : mood === "worried" ? (
      <ellipse cx="-7" cy="-2" rx="2.2" ry="2.8" fill="#1A1816" />
    ) : (
      <ellipse cx="-7" cy="-2" rx="2.2" ry="2.6" fill="#1A1816" />
    );
  const eye2: ReactNode = <ellipse cx="7" cy="-2" rx="2.2" ry="2.6" fill="#1A1816" />;
  const mouth: ReactNode =
    mood === "happy" ? (
      <path d="M-4 6 Q0 9 4 6" stroke="#1A1816" strokeWidth="1.5" fill="none" strokeLinecap="round" />
    ) : mood === "worried" ? (
      <path d="M-4 8 Q0 5 4 8" stroke="#1A1816" strokeWidth="1.5" fill="none" strokeLinecap="round" />
    ) : (
      <path d="M-4 6 L4 6" stroke="#1A1816" strokeWidth="1.5" fill="none" strokeLinecap="round" />
    );

  return (
    <svg width={size} height={size} viewBox="-100 -100 200 200" style={style} aria-hidden="true">
      <defs>
        <linearGradient id="cb-body" x1="0" x2="0" y1="0" y2="1">
          <stop offset="0" stopColor={color} />
          <stop offset="1" stopColor={shadow} />
        </linearGradient>
        <linearGradient id="cb-claw" x1="0" x2="1" y1="0" y2="1">
          <stop offset="0" stopColor={color} />
          <stop offset="1" stopColor={shadow} />
        </linearGradient>
      </defs>

      {/* left claw arm */}
      <path d="M-30 10 Q-55 -10 -60 -45" stroke="url(#cb-claw)" strokeWidth="10" fill="none" strokeLinecap="round" />
      <path d="M-30 22 L-22 14 M-30 30 L-22 22" stroke={shadow} strokeWidth="2" />
      {/* right claw arm */}
      <path d="M30 10 Q55 -10 60 -45" stroke="url(#cb-claw)" strokeWidth="10" fill="none" strokeLinecap="round" />
      <path d="M30 22 L22 14 M30 30 L22 22" stroke={shadow} strokeWidth="2" />

      {/* left claw */}
      <g transform="translate(-60 -50) rotate(-15)">
        <ellipse cx="0" cy="0" rx="22" ry="26" fill="url(#cb-claw)" />
        <path d="M-15 -10 Q-8 -22 4 -18 Q12 -10 6 -2 Q0 -8 -8 -6 Z" fill="#FFF8EE" opacity="0.95" />
        <ellipse cx="0" cy="-2" rx="14" ry="18" fill="none" stroke={shadow} strokeWidth="1.5" opacity="0.5" />
      </g>
      {/* right claw */}
      <g transform="translate(60 -50) rotate(15)">
        <ellipse cx="0" cy="0" rx="22" ry="26" fill="url(#cb-claw)" />
        <path d="M15 -10 Q8 -22 -4 -18 Q-12 -10 -6 -2 Q0 -8 8 -6 Z" fill="#FFF8EE" opacity="0.95" />
        <ellipse cx="0" cy="-2" rx="14" ry="18" fill="none" stroke={shadow} strokeWidth="1.5" opacity="0.5" />
      </g>

      {/* body */}
      <ellipse cx="0" cy="10" rx="34" ry="40" fill="url(#cb-body)" />
      {/* segments */}
      <path d="M-30 24 Q0 32 30 24" stroke={shadow} strokeWidth="2.5" fill="none" strokeLinecap="round" opacity="0.7" />
      <path d="M-26 38 Q0 46 26 38" stroke={shadow} strokeWidth="2.5" fill="none" strokeLinecap="round" opacity="0.7" />
      {/* tail flare */}
      <path d="M-22 50 Q0 60 22 50 L18 56 Q0 64 -18 56 Z" fill="url(#cb-body)" />
      {/* head bump */}
      <circle cx="0" cy="-10" r="22" fill="url(#cb-body)" />
      {/* antennae */}
      <path d="M-6 -28 Q-10 -38 -8 -45" stroke={shadow} strokeWidth="1.6" fill="none" strokeLinecap="round" />
      <path d="M6 -28 Q10 -38 8 -45" stroke={shadow} strokeWidth="1.6" fill="none" strokeLinecap="round" />
      <circle cx="-8" cy="-45" r="1.8" fill={shadow} />
      <circle cx="8" cy="-45" r="1.8" fill={shadow} />

      {/* face */}
      {eye}
      {eye2}
      {mouth}
      {/* cheek highlight */}
      <ellipse cx="-10" cy="4" rx="3" ry="2" fill="#FFF8EE" opacity="0.35" />

      {/* optional tool */}
      {tool === "wrench" && (
        <g transform="translate(-66 -55) rotate(-30)">
          <rect x="-2" y="-22" width="4" height="28" fill="#4A4640" />
          <circle cx="0" cy="-26" r="6" fill="#4A4640" />
          <circle cx="0" cy="-26" r="2.5" fill="var(--paper)" />
        </g>
      )}
      {tool === "magnifier" && (
        <g transform="translate(70 -55) rotate(20)">
          <circle cx="0" cy="0" r="14" fill="rgba(183,217,225,0.4)" stroke="#4A4640" strokeWidth="3" />
          <line x1="10" y1="10" x2="22" y2="22" stroke="#4A4640" strokeWidth="4" strokeLinecap="round" />
        </g>
      )}
      {tool === "clipboard" && (
        <g transform="translate(-60 0) rotate(-12)">
          <rect x="-12" y="-16" width="24" height="32" rx="2" fill="#FFF8EE" stroke="#4A4640" strokeWidth="1.5" />
          <rect x="-6" y="-19" width="12" height="6" rx="1" fill="#4A4640" />
          <line x1="-7" y1="-6" x2="7" y2="-6" stroke="#4A4640" strokeWidth="1" />
          <line x1="-7" y1="0" x2="7" y2="0" stroke="#4A4640" strokeWidth="1" />
          <line x1="-7" y1="6" x2="3" y2="6" stroke="#4A4640" strokeWidth="1" />
        </g>
      )}
    </svg>
  );
}

// A tiny minimal mark — claw shape only, for favicon / tight spaces.
interface ClawMarkProps {
  size?: number;
  color?: string;
}
export function ClawMark({ size = 32, color = "var(--claw-red)" }: ClawMarkProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" aria-hidden="true">
      <path d="M16 4 L23 8 L23 15 Q23 22 16 26 Q9 22 9 15 L9 8 Z" fill={color} />
      <path d="M14 10 L18 10 L18 14 L14 14 Z" fill="#FFF8EE" />
      <circle cx="12" cy="18" r="1.6" fill="#FFF8EE" />
      <circle cx="20" cy="18" r="1.6" fill="#FFF8EE" />
    </svg>
  );
}

// Wordmark — Clawbert mark next to the word "clawmetry".
interface WordmarkProps {
  size?: number;
  color?: string;
  mark?: string;
}
export function Wordmark({
  size = 1,
  color = "var(--ink)",
  mark = "var(--claw-red)",
}: WordmarkProps) {
  return (
    <div
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 8 * size,
        fontFamily: "var(--f-display)",
        fontSize: 28 * size,
        color,
        letterSpacing: "-0.01em",
        lineHeight: 1,
      }}
    >
      <ClawMark size={28 * size} color={mark} />
      <span>clawmetry</span>
    </div>
  );
}
