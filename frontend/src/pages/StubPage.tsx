// "Coming soon" placeholder used for every tab whose React port hasn't
// landed yet. Resolves its label + issue number from the slug via NAV_ITEMS.

import { useParams } from "react-router-dom";
import { Clawbert } from "../mascot";
import { getNavItemBySlug } from "../components/nav";

interface StubPageProps {
  slug?: string;
}

export function StubPage({ slug: explicit }: StubPageProps) {
  const params = useParams();
  const slug = explicit ?? (params["*"] ?? "").split("/")[0] ?? "";
  const item = getNavItemBySlug(slug);
  const label = item?.label ?? "This tab";
  const issue = item?.issue ?? 1492;

  return (
    <div
      style={{
        maxWidth: 720,
        margin: "0 auto",
        padding: "80px 40px",
        textAlign: "center",
      }}
    >
      <div style={{ display: "flex", justifyContent: "center", marginBottom: 16 }}>
        <Clawbert size={120} mood="calm" tool="clipboard" />
      </div>
      <h1
        className="display"
        style={{
          fontSize: 40,
          margin: 0,
          color: "var(--ink)",
          letterSpacing: "-0.02em",
        }}
      >
        {label}, soon.
      </h1>
      <p
        style={{
          marginTop: 18,
          fontSize: 16,
          color: "var(--ink-3)",
          lineHeight: 1.5,
          maxWidth: 520,
          marginLeft: "auto",
          marginRight: "auto",
        }}
      >
        Coming in a follow-up PR. Track progress in{" "}
        <a
          href={`https://github.com/vivekchand/clawmetry/issues/${issue}`}
          target="_blank"
          rel="noopener noreferrer"
          style={{ color: "var(--claw-red)", textDecoration: "underline" }}
        >
          issue #{issue}
        </a>
        . v1 still ships everything you had before, untouched.
      </p>
      <div style={{ marginTop: 28 }}>
        <a
          href="/"
          className="cm-btn"
          style={{ textDecoration: "none" }}
        >
          ↩ open v1 dashboard
        </a>
      </div>
    </div>
  );
}
