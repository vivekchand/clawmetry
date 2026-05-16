// Welcome page — the v2 landing inside the new chrome.
//
// Replaces the standalone HelloV2 hero from PR #1520. The cross-version
// "back to v1" link now lives in the topbar, so this page just sells the
// preview and points to the sidebar.

import { Clawbert } from "../mascot";

export function WelcomePage() {
  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "minmax(200px, 1fr) minmax(0, 2fr)",
        gap: 48,
        padding: "64px 56px",
        alignItems: "center",
        maxWidth: 1200,
        margin: "0 auto",
      }}
    >
      <div style={{ display: "flex", justifyContent: "center" }}>
        <Clawbert size={200} mood="happy" tool="wrench" />
      </div>

      <div>
        <h1
          className="display"
          style={{
            fontSize: 64,
            lineHeight: 0.95,
            letterSpacing: "-0.02em",
            margin: 0,
            color: "var(--ink)",
          }}
        >
          Pop the hood{" "}
          <span style={{ fontStyle: "italic", color: "var(--claw-red)" }}>
            on your AI agents.
          </span>
        </h1>
        <p
          style={{
            marginTop: 22,
            fontSize: 17,
            color: "var(--ink-3)",
            maxWidth: 520,
            lineHeight: 1.5,
          }}
        >
          You're looking at the v2 shell. Chrome is wired, theme switching is live,
          every tab in the sidebar lands in a follow-up PR. v1 keeps running at{" "}
          <code className="mono" style={{ fontSize: 14 }}>/</code> until v2 is
          stable enough to flip the default.
        </p>

        <div
          style={{
            marginTop: 28,
            display: "flex",
            flexWrap: "wrap",
            gap: 10,
          }}
        >
          <span className="cm-badge" style={{ color: "var(--moss)" }}>
            <span className="dot" /> Week 1 · chrome + theme
          </span>
          <span className="cm-tag">CLAWMETRY_V2=1</span>
          <span className="cm-tag">react · vite · ts</span>
        </div>

        <div style={{ marginTop: 36 }}>
          <div
            className="caps"
            style={{ color: "var(--ink-4)", marginBottom: 8 }}
          >
            What works today
          </div>
          <ul
            style={{
              listStyle: "none",
              padding: 0,
              margin: 0,
              display: "flex",
              flexDirection: "column",
              gap: 6,
              fontSize: 13,
              color: "var(--ink-2)",
            }}
          >
            <li>· Sidebar nav (LIVE / HISTORY / FLEET groups, 11 destinations)</li>
            <li>· Topbar with per-route title + status pill + back-to-v1 link</li>
            <li>· Light / Mid / Dark theme picker, instant, no reload</li>
            <li>· Mascot + design tokens straight from the handoff</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
