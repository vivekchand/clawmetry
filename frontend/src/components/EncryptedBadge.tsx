// EncryptedBadge — moss-green "🔒 E2E" pill.
//
// Surfaces wherever a user might wonder "is this data encrypted?" — sidebar
// workspace row, Topbar action bar, and eventually per-node fleet cards.
// All cloud sync is AES-256-GCM encrypted end-to-end by the sync daemon.

export function EncryptedBadge() {
  return (
    <span
      title="Cloud sync is AES-256-GCM end-to-end encrypted"
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 3,
        padding: "2px 6px",
        borderRadius: "var(--r-1)",
        background: "var(--moss-soft)",
        color: "var(--moss)",
        fontSize: 10,
        fontWeight: 500,
        whiteSpace: "nowrap",
        lineHeight: 1.5,
        flexShrink: 0,
      }}
    >
      🔒 E2E
    </span>
  );
}
