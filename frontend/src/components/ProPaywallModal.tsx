interface ProPaywallModalProps {
  open: boolean;
  onClose: () => void;
  feature?: string;
}

export function ProPaywallModal({ open, onClose, feature = "auto-promote rules" }: ProPaywallModalProps) {
  if (!open) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="pro-paywall-title"
      onClick={onClose}
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 1000,
        background: "rgba(26, 24, 22, 0.45)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: 24,
      }}
    >
      <div
        className="cm-card"
        onClick={(e) => e.stopPropagation()}
        style={{ maxWidth: 420, width: "100%", padding: 24, background: "var(--paper)" }}
      >
        <div className="caps" style={{ color: "var(--plum)", marginBottom: 8 }}>
          Cloud Pro
        </div>
        <h2 id="pro-paywall-title" style={{ margin: "0 0 10px", fontSize: 20, fontWeight: 500, color: "var(--ink)" }}>
          {feature} is a Pro feature
        </h2>
        <p style={{ margin: "0 0 18px", fontSize: 13, color: "var(--ink-3)", lineHeight: 1.5 }}>
          On OSS/Free, you can review and approve actions manually. Cloud Pro unlocks auto-promote rules,
          notification dispatch, and one-click rule creation from the approval inbox.
        </p>
        <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>
          <button type="button" className="cm-btn" onClick={onClose}>
            Not now
          </button>
          <a
            href="https://app.clawmetry.com/upgrade?source=v2-approvals"
            target="_blank"
            rel="noopener noreferrer"
            className="cm-btn primary"
            style={{ textDecoration: "none" }}
          >
            Start free trial
          </a>
        </div>
      </div>
    </div>
  );
}
