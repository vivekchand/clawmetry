// WizardFrame — wraps any onboarding wizard step with a progress strip,
// optional "Skip for now" link, and a title block.
//
// All color/spacing values come from styles.css tokens — no inline magic.

import React from "react";

interface WizardFrameProps {
  title: string;
  current: number;
  total: number;
  onSkip?: () => void;
  children: React.ReactNode;
}

export function WizardFrame({ title, current, total, onSkip, children }: WizardFrameProps) {
  const progressPct = total > 0 ? Math.min(1, current / total) * 100 : 0;

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "var(--gap-3)",
        padding: "var(--pad-4)",
        borderRadius: "var(--r-3)",
        background: "var(--panel)",
        border: "1px solid var(--paper-line)",
      }}
    >
      {/* progress strip */}
      <div
        style={{
          height: 3,
          borderRadius: "var(--r-1)",
          background: "var(--paper-line)",
          overflow: "hidden",
        }}
      >
        <div
          style={{
            height: "100%",
            width: `${progressPct}%`,
            background: "var(--claw-red)",
            borderRadius: "var(--r-1)",
            transition: "width 0.3s ease",
          }}
        />
      </div>

      {/* header row */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <span
          style={{
            fontSize: 11,
            color: "var(--ink-4)",
            fontFamily: "var(--f-mono)",
            letterSpacing: "0.04em",
          }}
        >
          {current} / {total}
        </span>
        {onSkip && (
          <button
            onClick={onSkip}
            style={{
              background: "none",
              border: "none",
              padding: 0,
              cursor: "pointer",
              fontSize: 12,
              color: "var(--ink-4)",
              textDecoration: "underline",
            }}
          >
            Skip for now
          </button>
        )}
      </div>

      {/* title */}
      <h2
        style={{
          margin: 0,
          fontSize: 18,
          fontFamily: "var(--f-sans)",
          fontWeight: 600,
          color: "var(--ink)",
          lineHeight: 1.3,
        }}
      >
        {title}
      </h2>

      {/* step content */}
      <div>{children}</div>
    </div>
  );
}
