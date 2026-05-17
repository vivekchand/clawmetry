import { Clawbert, Wordmark } from "./mascot";

// Phase-0 "hello, v2" proof of life.
// Renders the lobster mascot, the Instrument-Serif hero line, and a
// "Back to v1 ↩" affordance per the design handoff README's parallel-rails
// strategy ("v2 grows around v1, then v1 falls away when nothing depends on it").
export default function HelloV2() {
  return (
    <div className="cm" style={{ minHeight: "100vh", background: "var(--bg)" }}>
      {/* Top strip — wordmark left, "back to v1" right. */}
      <header
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "20px 32px",
          borderBottom: "1px solid var(--line)",
        }}
      >
        <Wordmark />
        <a
          href="/"
          className="cm-btn ghost"
          style={{ textDecoration: "none" }}
          aria-label="Back to ClawMetry v1"
        >
          v2 preview · back to v1 ↩
        </a>
      </header>

      {/* Hero — mascot on the left, headline + subhead on the right. */}
      <main
        style={{
          display: "grid",
          gridTemplateColumns: "minmax(220px, 1fr) minmax(0, 2fr)",
          gap: 48,
          padding: "80px 64px",
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
              fontSize: 72,
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
              marginTop: 24,
              fontSize: 18,
              color: "var(--ink-3)",
              maxWidth: 520,
              lineHeight: 1.5,
            }}
          >
            You're looking at the v2 shell. Phase 0 of the React SPA rebuild — design tokens
            are live, the mascot is inline SVG, and routing is wired. Every tab lands in a
            follow-up PR. v1 keeps running at <code className="mono">/</code> until v2 is
            stable enough to flip the default.
          </p>
          <div style={{ marginTop: 28, display: "flex", gap: 12 }}>
            <span className="cm-badge" style={{ color: "var(--moss)" }}>
              <span className="dot" /> Phase 0 · scaffold
            </span>
            <span className="cm-tag">CLAWMETRY_V2=1</span>
          </div>
        </div>
      </main>
    </div>
  );
}
