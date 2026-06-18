import { useState, useEffect } from "react";
import { Clawbert } from "../mascot";

interface Skill {
  name: string;
  active: boolean;
  dead: boolean;
  header_tokens: number;
  body_fetch_count_7d: number;
  linked_file_read_count_7d: number;
  last_used_ts: number | null;
}

interface SkillsData {
  tree: Skill[];
  summary: {
    total_installed: number;
    dead_count: number;
    wasted_header_tokens: number;
  };
}

interface SkillSource {
  name: string;
  content: string;
}

function fmtLastUsed(ts: number | null): string {
  if (!ts) return "never";
  const secs = Date.now() / 1000 - ts;
  if (secs < 3600) return `${Math.round(secs / 60)}m ago`;
  if (secs < 86400) return `${Math.round(secs / 3600)}h ago`;
  return `${Math.round(secs / 86400)}d ago`;
}

function SkillRow({
  skill,
  selected,
  onSelect,
}: {
  skill: Skill;
  selected: boolean;
  onSelect: () => void;
}) {
  return (
    <div
      onClick={onSelect}
      style={{
        padding: "7px 12px",
        cursor: "pointer",
        borderLeft: selected ? "3px solid var(--claw-red)" : "3px solid transparent",
        background: selected ? "var(--panel-2)" : "transparent",
        transition: "background 80ms",
        display: "flex",
        alignItems: "center",
        gap: 8,
      }}
    >
      <span
        style={{
          fontSize: 11,
          color: skill.dead ? "var(--ink-4)" : "var(--ink-2)",
          flex: 1,
          overflow: "hidden",
          textOverflow: "ellipsis",
          whiteSpace: "nowrap",
          fontFamily: "var(--f-mono)",
        }}
      >
        {skill.name}
      </span>
      {skill.body_fetch_count_7d > 0 && (
        <span
          className="mono"
          style={{ fontSize: 9, color: "var(--moss)", flexShrink: 0 }}
        >
          {skill.body_fetch_count_7d}×
        </span>
      )}
    </div>
  );
}

export function SkillsPage() {
  const [data, setData] = useState<SkillsData | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [source, setSource] = useState<SkillSource | null>(null);
  const [sourceLoading, setSourceLoading] = useState(false);
  const [deadOpen, setDeadOpen] = useState(false);

  useEffect(() => {
    fetch("/api/v2/skills")
      .then((r) => r.json())
      .then((d: SkillsData) => {
        setData(d);
        const first = (d.tree ?? []).find((s) => !s.dead);
        if (first) setSelected(first.name);
      })
      .catch(console.error);
  }, []);

  useEffect(() => {
    if (!selected) return;
    setSourceLoading(true);
    setSource(null);
    fetch(`/api/v2/skills/${encodeURIComponent(selected)}/source`)
      .then((r) => r.json())
      .then((d: SkillSource) => {
        setSource(d);
        setSourceLoading(false);
      })
      .catch(() => setSourceLoading(false));
  }, [selected]);

  if (!data) {
    return (
      <div style={{ padding: 40, color: "var(--ink-4)" }} className="mono">
        Loading skills…
      </div>
    );
  }

  if (data.tree.length === 0) {
    return (
      <div style={{ padding: "80px 40px", textAlign: "center" }}>
        <div style={{ display: "flex", justifyContent: "center", marginBottom: 16 }}>
          <Clawbert size={80} mood="calm" tool="clipboard" />
        </div>
        <div style={{ fontSize: 15, color: "var(--ink-3)" }}>
          No skills here yet. Drop a SKILL.md anywhere in the workspace.
        </div>
      </div>
    );
  }

  const activeSkills = data.tree.filter((s) => !s.dead);
  const deadSkills = data.tree.filter((s) => s.dead);
  const sel = selected ? data.tree.find((s) => s.name === selected) ?? null : null;

  return (
    <div style={{ flex: 1, display: "flex", minHeight: 0, overflow: "hidden" }}>
      {/* Left: skill tree */}
      <div
        style={{
          width: 220,
          flexShrink: 0,
          borderRight: "1px solid var(--line)",
          overflow: "auto",
          display: "flex",
          flexDirection: "column",
        }}
      >
        <div
          className="caps"
          style={{ color: "var(--ink-4)", padding: "10px 12px 6px", fontSize: 9 }}
        >
          Skills · {data.summary.total_installed}
        </div>
        {activeSkills.map((s) => (
          <SkillRow
            key={s.name}
            skill={s}
            selected={selected === s.name}
            onSelect={() => setSelected(s.name)}
          />
        ))}
        {deadSkills.length > 0 && (
          <div>
            <div
              onClick={() => setDeadOpen((o) => !o)}
              style={{
                padding: "7px 12px",
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                gap: 6,
              }}
            >
              <span style={{ fontSize: 9, color: "var(--ink-4)" }}>
                {deadOpen ? "▾" : "▸"}
              </span>
              <span
                className="mono"
                style={{ fontSize: 10, color: "var(--ink-4)" }}
              >
                _dead/ · {deadSkills.length}
              </span>
            </div>
            {deadOpen &&
              deadSkills.map((s) => (
                <SkillRow
                  key={s.name}
                  skill={s}
                  selected={selected === s.name}
                  onSelect={() => setSelected(s.name)}
                />
              ))}
          </div>
        )}
      </div>

      {/* Centre: SKILL.md source viewer */}
      <div
        style={{
          flex: 1,
          minWidth: 0,
          overflow: "auto",
          display: "flex",
          flexDirection: "column",
        }}
      >
        {selected ? (
          <>
            <div
              style={{
                padding: "8px 14px",
                borderBottom: "1px solid var(--line)",
                fontSize: 11,
                color: "var(--ink-3)",
                background: "var(--panel-2)",
                fontFamily: "var(--f-mono)",
                flexShrink: 0,
              }}
            >
              {selected}/SKILL.md
            </div>
            {sourceLoading ? (
              <div
                style={{ padding: 20, color: "var(--ink-4)" }}
                className="mono"
              >
                Loading…
              </div>
            ) : (
              <pre
                style={{
                  margin: 0,
                  padding: "14px 18px",
                  fontFamily: "var(--f-mono)",
                  fontSize: 12,
                  color: "var(--abs-paper)",
                  lineHeight: 1.7,
                  whiteSpace: "pre-wrap",
                  wordBreak: "break-word",
                  background: "var(--abs-ink)",
                  flex: 1,
                  overflow: "auto",
                }}
              >
                {source?.content ?? "(no content)"}
              </pre>
            )}
          </>
        ) : (
          <div
            style={{ padding: 40, color: "var(--ink-4)" }}
            className="mono"
          >
            Select a skill from the tree.
          </div>
        )}
      </div>

      {/* Right: fidelity stats */}
      <div
        style={{
          width: 192,
          flexShrink: 0,
          borderLeft: "1px solid var(--line)",
          overflow: "auto",
          padding: "12px 14px",
          display: "flex",
          flexDirection: "column",
          gap: 14,
        }}
      >
        <div className="caps" style={{ color: "var(--ink-4)", fontSize: 9 }}>
          Fidelity
        </div>
        {sel ? (
          <>
            {(
              [
                ["header tok", sel.header_tokens, "var(--ink-2)"],
                ["body 7d", sel.body_fetch_count_7d, "var(--moss)"],
                ["linked 7d", sel.linked_file_read_count_7d, "var(--sea, #3b82f6)"],
                ["last used", fmtLastUsed(sel.last_used_ts), "var(--ink-3)"],
              ] as [string, string | number, string][]
            ).map(([label, val, color]) => (
              <div key={label}>
                <div
                  className="caps"
                  style={{ color: "var(--ink-4)", fontSize: 9 }}
                >
                  {label}
                </div>
                <div
                  className="mono"
                  style={{ fontSize: 16, color, marginTop: 2 }}
                >
                  {val}
                </div>
              </div>
            ))}
            <div
              style={{
                borderTop: "1px dashed var(--line)",
                paddingTop: 10,
                display: "flex",
                flexDirection: "column",
                gap: 5,
              }}
            >
              <div className="caps" style={{ color: "var(--ink-4)", fontSize: 9 }}>
                workspace
              </div>
              {(
                [
                  ["installed", data.summary.total_installed, "var(--ink-2)"],
                  ["dead", data.summary.dead_count, "var(--claw-red)"],
                  ["wasted tok", data.summary.wasted_header_tokens, "var(--amber)"],
                ] as [string, number, string][]
              ).map(([k, v, c]) => (
                <div
                  key={k}
                  style={{ display: "flex", justifyContent: "space-between" }}
                >
                  <span
                    className="mono"
                    style={{ fontSize: 10, color: "var(--ink-4)" }}
                  >
                    {k}
                  </span>
                  <span className="mono" style={{ fontSize: 10, color: c }}>
                    {v}
                  </span>
                </div>
              ))}
            </div>
          </>
        ) : (
          <div
            className="mono"
            style={{ fontSize: 10, color: "var(--ink-4)" }}
          >
            Select a skill to see stats.
          </div>
        )}
      </div>
    </div>
  );
}
